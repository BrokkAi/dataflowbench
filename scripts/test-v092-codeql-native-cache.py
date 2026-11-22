#!/usr/bin/env python3
"""Small fixture regressions for offline CodeQL native cache preparation."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("v092_codeql_native_cache.py")
SPEC = importlib.util.spec_from_file_location("codeql_native_cache_under_test", SCRIPT)
cache = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cache)


class OfflineCodeQLCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dfb-codeql-cache-test-")
        base = Path(self.temporary.name).resolve()
        self.repo = base / "repo"
        self.repo.mkdir()
        self.source = base / "runtime" / "codeql-packs"
        self.source.mkdir(parents=True)
        self.old_root = str(base / "old-runtime" / "codeql-packs")
        self.home = base / "isolated-home"
        self.home.mkdir()
        self.receipt = self.repo / "reports" / "cache-receipt.json"
        self.original_path = self.repo / "reports" / "original-manifest.json"
        self.relocated_path = self.repo / "reports" / "relocated-manifest.json.gz"
        self.relocation_path = self.repo / "reports" / "relocation-receipt.json"
        self.acquisition_path = self.repo / "reports" / "acquisition-receipt.json"
        self.files: list[dict] = []
        self.links: list[dict] = []
        self.link_target_path = None

        for name, (version, _library) in cache.PACK_PINS.items():
            relative = f"{name}/{version}/pack.contents"
            self._write_source(relative, f"fixture {name}@{version}".encode())
        for suite in cache.NATIVE_SUITES:
            self._write_source(suite, f"suite fixture: {suite}".encode())
        self.link_target_path = cache.NATIVE_SUITES[0]
        link_relative = "codeql/java-queries/1.11.12/suite-alias.qls"
        link = self.source / link_relative
        link.symlink_to("codeql-suites/java-security-extended.qls")
        self.links.append({"path": link_relative, "target": os.readlink(link), "mode": 0o644})
        self._write_bound_inputs()

    def tearDown(self):
        self.temporary.cleanup()

    def _write_source(self, relative: str, data: bytes):
        path = self.source / Path(*Path(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
        self.files.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "mode": 0o644})

    def _write_bound_inputs(self, *, unsafe_path: bool = False, external_files=None):
        files = [dict(entry) for entry in self.files]
        links = [dict(entry) for entry in self.links]
        if unsafe_path:
            files.append({"path": "../../escape", "sha256": "0" * 64, "mode": 0o644})
        original_manifest = {
            "schema_version": 1,
            "root": self.old_root,
            "files": files,
            "symlinks": links,
            "external_files": [] if external_files is None else external_files,
        }
        original_raw = json.dumps(original_manifest, sort_keys=True, separators=(",", ":")).encode()
        self.original_path.parent.mkdir(parents=True, exist_ok=True)
        self.original_path.write_bytes(original_raw)

        relocated_manifest = dict(original_manifest)
        relocated_manifest["root"] = str(self.source)
        relocated_raw = json.dumps(relocated_manifest, sort_keys=True, separators=(",", ":")).encode()
        compressed = gzip.compress(relocated_raw, mtime=0)
        self.relocated_path.write_bytes(compressed)

        original_relative = self.original_path.relative_to(self.repo).as_posix()
        relocated_relative = self.relocated_path.relative_to(self.repo).as_posix()
        original_sha = hashlib.sha256(original_raw).hexdigest()
        compressed_sha = hashlib.sha256(compressed).hexdigest()
        relocated_sha = hashlib.sha256(relocated_raw).hexdigest()
        relocation = {
            "schema": cache.RELOCATION_SCHEMA,
            "manifests": [{
                "manifest_id": "codeql-packs",
                "source_path": original_relative,
                "source_sha256": original_sha,
                "source_root": self.old_root,
                "new_root": str(self.source),
                "changed_json_property": "root",
                "manifest_path": relocated_relative,
                "manifest_sha256": compressed_sha,
                "uncompressed_sha256": relocated_sha,
                "compressed": True,
                "uncompressed_bytes": len(relocated_raw),
                "compressed_bytes": len(compressed),
                "closure_status": "passed-static-full-tree-hash-mode-symlink-and-external-file-check",
                "source_audit_manifest_sha256": original_sha,
            }],
        }
        self.relocation_path.write_text(json.dumps(relocation, sort_keys=True))
        packs = [
            {"name": name, "version": version, "library": library, "result": "INSTALLED"}
            for name, (version, library) in cache.PACK_PINS.items()
        ]
        self.acquisition_path.write_text(json.dumps({"packDir": self.old_root, "packs": packs}, sort_keys=True))

    def _prepare(self):
        return cache.prepare_cache(
            home=self.home,
            receipt_path=self.receipt,
            repo_root=self.repo,
            relocated_manifest_path=self.relocated_path,
            original_manifest_path=self.original_path,
            relocation_receipt_path=self.relocation_path,
            acquisition_receipt_path=self.acquisition_path,
        )

    def test_materializes_exact_files_modes_links_and_unproven_receipt(self):
        result = self._prepare()
        destination = self.home / ".codeql" / "packages"
        self.assertEqual(result["file_count"], len(self.files))
        self.assertEqual(result["symlink_count"], 1)
        for entry in self.files:
            target = destination / Path(*Path(entry["path"]).parts)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), entry["sha256"])
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), entry["mode"])
        link = destination / "codeql/java-queries/1.11.12/suite-alias.qls"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "codeql-suites/java-security-extended.qls")
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt["qualification"], {
            "suite_discovery": "unproven",
            "analysis": "unproven",
            "semantic_qualification": "unproven",
            "publication_eligible": False,
        })
        verified = cache.verify_receipt(self.receipt, repo_root=self.repo)
        self.assertTrue(verified["verified"])

    def test_rejects_reused_destination_even_when_empty(self):
        destination = self.home / ".codeql" / "packages"
        destination.mkdir(parents=True)
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()

    def test_rejects_unsafe_manifest_path_before_materialization(self):
        self._write_bound_inputs(unsafe_path=True)
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()
        self.assertFalse((self.home / ".codeql").exists())

    def test_rejects_source_digest_drift(self):
        changed = self.source / Path(*Path(self.files[0]["path"]).parts)
        changed.write_bytes(b"drifted bytes")
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()
        self.assertTrue((self.home / ".codeql" / "packages").is_dir())
        self.assertEqual(json.loads(self.receipt.read_text())["status"], "failed")

    def test_rejects_source_mode_drift(self):
        changed = self.source / Path(*Path(self.files[0]["path"]).parts)
        changed.chmod(0o600)
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()
        self.assertTrue((self.home / ".codeql" / "packages").is_dir())
        self.assertEqual(json.loads(self.receipt.read_text())["status"], "failed")

    def test_rejects_source_symlink_target_drift(self):
        link = self.source / "codeql/java-queries/1.11.12/suite-alias.qls"
        link.unlink()
        link.symlink_to("pack.contents")
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()

    def test_rejects_unlisted_source_symlink(self):
        (self.source / "unexpected-link").symlink_to("codeql/java-queries/1.11.12/pack.contents")
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()

    def test_rejects_external_manifest_entries(self):
        self._write_bound_inputs(external_files=[{"path": "outside", "target": "/tmp/outside"}])
        with self.assertRaises(cache.CachePreparationError):
            self._prepare()

    def test_verify_detects_target_content_drift(self):
        self._prepare()
        target = self.home / ".codeql" / "packages" / Path(*Path(self.files[0]["path"]).parts)
        target.write_bytes(b"changed after preparation")
        with self.assertRaises(cache.CachePreparationError):
            cache.verify_receipt(self.receipt, repo_root=self.repo)

    def test_failure_retains_partial_cache_and_append_only_receipt(self):
        copy_file = cache._copy_file
        copied = 0

        def copy_then_fail_once(*args):
            nonlocal copied
            if copied == 1:
                raise cache.CachePreparationError("fixture copy failure")
            copy_file(*args)
            copied += 1

        with patch.object(cache, "_copy_file", side_effect=copy_then_fail_once):
            with self.assertRaises(cache.CachePreparationError):
                self._prepare()

        destination = self.home / ".codeql" / "packages"
        self.assertTrue(destination.is_dir())
        self.assertTrue(any(destination.rglob("pack.contents")))
        failure = json.loads(self.receipt.read_text())
        self.assertEqual(failure["status"], "failed")
        self.assertEqual(failure["source"]["manifest_sha256"], hashlib.sha256(
            self.relocated_path.read_bytes()).hexdigest())
        self.assertEqual(failure["target"]["cache_state"], "partial-retained")
        self.assertTrue(failure["failure"]["partial_cache_retained"])
        self.assertTrue(failure["failure"]["retry_requires_new_home_and_receipt_path"])
        with self.assertRaises(cache.CachePreparationError):
            cache.verify_receipt(self.receipt, repo_root=self.repo)

        retry_receipt = self.repo / "reports" / "retry-failure.json"
        with self.assertRaises(cache.CachePreparationError):
            cache.prepare_cache(
                home=self.home, receipt_path=retry_receipt, repo_root=self.repo,
                relocated_manifest_path=self.relocated_path, original_manifest_path=self.original_path,
                relocation_receipt_path=self.relocation_path, acquisition_receipt_path=self.acquisition_path,
            )
        self.assertEqual(json.loads(retry_receipt.read_text())["target"]["cache_state"],
                         "preexisting-refused")

    def test_verify_rejects_deleted_source_bound_inventory_entry(self):
        self._prepare()
        receipt = json.loads(self.receipt.read_text())
        receipt["target"]["inventory"].pop()
        self.receipt.write_text(json.dumps(receipt, sort_keys=True))
        with self.assertRaises(cache.CachePreparationError):
            cache.verify_receipt(self.receipt, repo_root=self.repo)

    def test_verify_rejects_symlinked_home_path(self):
        self._prepare()
        alias = self.repo / "home-alias"
        alias.symlink_to(self.home, target_is_directory=True)
        receipt = json.loads(self.receipt.read_text())
        receipt["target"]["home"] = str(alias)
        receipt["target"]["common_cache_root"] = str(alias / ".codeql")
        receipt["target"]["package_cache_root"] = str(alias / ".codeql" / "packages")
        self.receipt.write_text(json.dumps(receipt, sort_keys=True))
        with self.assertRaises(cache.CachePreparationError):
            cache.verify_receipt(self.receipt, repo_root=self.repo)


if __name__ == "__main__":
    unittest.main()
