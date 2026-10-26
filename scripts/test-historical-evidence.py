#!/usr/bin/env python3
"""Focused synthetic Git-bundle tests for historical_evidence.py."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import historical_evidence as evidence  # noqa: E402


class HistoricalEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pinned_main_before = evidence.PINNED_ORIGINAL_MAIN
        self.pinned_base_before = evidence.PINNED_REWRITTEN_BASE
        self.preserved_tags_before = dict(evidence.EXPECTED_PRESERVED_TAGS)
        self.addCleanup(self._restore_pinned_authority)
        self.temporary = tempfile.TemporaryDirectory(prefix="historical-evidence-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self._git(None, "init", "--quiet", "--initial-branch=main", str(self.root))
        self._git("config", "user.name", "Historical Evidence Test")
        self._git("config", "user.email", "history-test@example.invalid")
        self._write("src/app.py", b"source at release\n")
        self._write("reports/freeze.json", b'{"frozen":true}\n')
        self._write("results/index.md", b"frozen results\n")
        self._write("results/results.json", b'{"rows":[]}\n')
        self._write("reports/raw/run.log", b"raw diagnostic bytes\x00\xff\n")
        self._write("reports/releases/v0.1.0/attempts/detail.json", b'{"attempt":1}\n')
        self._write("reports/releases/v0.1.0/ledger.jsonl", b'{"ledger":true}\n')
        self._git("add", ".")
        self._git("commit", "--quiet", "-m", "release source")
        self.release_commit = self._git_output("rev-parse", "HEAD")
        self._git("tag", "-a", "v0.1.0", "-m", "v0.1.0")
        self._git("tag", "-a", "v0.0.9", self.release_commit, "-m", "v0.0.9")
        self._write("src/app.py", b"main after release\n")
        self._git("add", "src/app.py")
        self._git("commit", "--quiet", "-m", "main update")
        self.original_main = self._git_output("rev-parse", "HEAD")
        self.tag_object = self._git_output("rev-parse", "refs/tags/v0.1.0")
        self.older_tag_object = self._git_output("rev-parse", "refs/tags/v0.0.9")
        self._git("update-ref", "refs/remotes/origin/main", self.original_main)

        archive_dir = self.root / "evidence-archives/main-before-20261026"
        archive_dir.mkdir(parents=True)
        bundle_path = archive_dir / "original-history.bundle.part0000"
        generated_bundle = Path(self.temporary.name) / "original-history.bundle"
        self._git(
            "bundle",
            "create",
            str(generated_bundle),
            "refs/remotes/origin/main",
            "refs/tags/v0.1.0",
            "refs/tags/v0.0.9",
        )
        bundle_bytes = generated_bundle.read_bytes()
        bundle_path.write_bytes(bundle_bytes)
        self.manifest_path = archive_dir / "manifest.json"
        self.manifest = {
            "schema_version": 1,
            "original_main": self.original_main,
            "rewritten_base": "0" * 40,
            "original_ref": "refs/remotes/origin/main",
            "preserved_tags": {"v0.1.0": self.tag_object, "v0.0.9": self.older_tag_object},
            "removed_paths": {
                "prefixes": ["reports/raw/", "reports/releases/v0.1.0/attempts/"],
                "files": ["reports/releases/v0.1.0/ledger.jsonl"],
            },
            "bundle": {
                "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                "bytes": len(bundle_bytes),
                "parts": [
                    {
                        "path": bundle_path.name,
                        "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                        "bytes": len(bundle_bytes),
                    }
                ],
            },
        }
        self._filter_removed_paths()
        self._write_manifest()
        evidence.PINNED_ORIGINAL_MAIN = self.original_main
        evidence.PINNED_REWRITTEN_BASE = self.manifest["rewritten_base"]
        evidence.EXPECTED_PRESERVED_TAGS = dict(self.manifest["preserved_tags"])
        self.cache_dir = Path(self._git_output("rev-parse", "--absolute-git-dir")) / "historical-evidence" / self.manifest["bundle"]["sha256"]

    def _restore_pinned_authority(self) -> None:
        evidence.PINNED_ORIGINAL_MAIN = self.pinned_main_before
        evidence.PINNED_REWRITTEN_BASE = self.pinned_base_before
        evidence.EXPECTED_PRESERVED_TAGS = self.preserved_tags_before

    def _git(self, *args: str | None) -> bytes:
        argv = ["git"]
        for arg in args:
            if arg is not None:
                argv.append(arg)
        env = os.environ.copy()
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        result = subprocess.run(argv, cwd=self.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            self.fail(f"git {argv[1:]} failed: {result.stderr.decode('utf-8', 'replace')}")
        return result.stdout

    def _git_output(self, *args: str) -> str:
        return self._git("-C", str(self.root), *args).decode("ascii").strip()

    def _write(self, relative: str, content: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def _filter_removed_paths(self) -> None:
        self._git("-C", str(self.root), "rm", "-r", "--", "reports/raw", "reports/releases/v0.1.0/attempts", "reports/releases/v0.1.0/ledger.jsonl")
        self._git("-C", str(self.root), "commit", "--quiet", "-m", "filtered base")
        self.manifest["rewritten_base"] = self._git_output("rev-parse", "HEAD")

    def _write_manifest(self) -> None:
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_roundtrip_restores_only_selected_original_bytes(self) -> None:
        proof = evidence.prove_lineage(self.root, self.release_commit, "v0.1.0")
        self.assertTrue(proof["verified"])
        self.assertEqual(proof["original_main"], self.original_main)
        self.assertFalse((self.root / "reports/raw/run.log").exists())
        cli_output = io.StringIO()
        with contextlib.redirect_stdout(cli_output):
            status = evidence._main(
                [
                    "prove",
                    "--root",
                    str(self.root),
                    "--revision",
                    self.release_commit,
                    "--release",
                    "v0.1.0",
                ]
            )
        self.assertEqual(status, 0)
        cli_proof = json.loads(cli_output.getvalue())
        self.assertTrue(cli_proof["verified"])
        self.assertEqual(cli_proof["revision"], self.release_commit)
        self.assertEqual(cli_proof["release"], "v0.1.0")
        self.assertEqual(cli_proof["original_main"], self.original_main)
        self.assertEqual(cli_proof["rewritten_base"], self.manifest["rewritten_base"])

        restored = evidence.hydrate(self.root)
        self.assertEqual(restored["restored_files"], 3)
        expected_restored_bytes = sum(
            map(
                len,
                (
                    b"raw diagnostic bytes\x00\xff\n",
                    b'{"attempt":1}\n',
                    b'{"ledger":true}\n',
                ),
            )
        )
        self.assertEqual(restored["restored_bytes"], expected_restored_bytes)
        self.assertEqual((self.root / "reports/raw/run.log").read_bytes(), b"raw diagnostic bytes\x00\xff\n")
        self.assertEqual((self.root / "reports/releases/v0.1.0/attempts/detail.json").read_bytes(), b'{"attempt":1}\n')
        self.assertEqual((self.root / "reports/releases/v0.1.0/ledger.jsonl").read_bytes(), b'{"ledger":true}\n')
        second = evidence.hydrate(self.root)
        self.assertEqual(second["restored_files"], 0)
        self.assertEqual(second["already_present_files"], 3)
        self.assertEqual(second["restored_bytes"], 0)
        self.assertEqual(second["already_present_bytes"], expected_restored_bytes)

    def test_wrong_revision_and_wrong_release_fail(self) -> None:
        with self.assertRaises(evidence.EvidenceError):
            evidence.prove_lineage(self.root, "f" * 40, "v0.1.0")
        with self.assertRaises(evidence.EvidenceError):
            evidence.prove_lineage(self.root, self.original_main, "v9.9.9")
        with self.assertRaisesRegex(evidence.EvidenceError, "not an ancestor of preserved"):
            evidence.prove_lineage(self.root, self.original_main, "v0.1.0")

    def test_manifest_tag_identity_must_match_archive(self) -> None:
        self.manifest["preserved_tags"]["v0.1.0"] = self.original_main
        evidence.EXPECTED_PRESERVED_TAGS = dict(self.manifest["preserved_tags"])
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "bundle refs"):
            evidence.verify(self.root)

    def test_consistent_omitted_preserved_tag_fails_pinned_authority(self) -> None:
        self.manifest["preserved_tags"].pop("v0.0.9")
        bundle_path = Path(self.temporary.name) / "one-tag-history.bundle"
        self._git(
            "-C",
            str(self.root),
            "bundle",
            "create",
            str(bundle_path),
            "refs/remotes/origin/main",
            "refs/tags/v0.1.0",
        )
        bundle_bytes = bundle_path.read_bytes()
        part_path = self.manifest_path.parent / "original-history.bundle.part0000"
        part_path.write_bytes(bundle_bytes)
        self.manifest["bundle"] = {
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "bytes": len(bundle_bytes),
            "parts": [
                {
                    "path": part_path.name,
                    "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                    "bytes": len(bundle_bytes),
                }
            ],
        }
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "pinned tag identities"):
            evidence.verify(self.root)

    def test_consistent_substituted_original_main_fails_pinned_authority(self) -> None:
        # Change only a blob that the manifest removes, then rebuild the bundle
        # and matching manifest. The filtered tree and all tags remain
        # internally consistent, so the migration-specific authority pin must
        # be the check that rejects this alternate original history.
        self._git("-C", str(self.root), "checkout", "--quiet", self.original_main)
        self._write("reports/raw/run.log", b"alternate original history\n")
        self._git("-C", str(self.root), "add", "reports/raw/run.log")
        self._git("-C", str(self.root), "commit", "--quiet", "-m", "alternate removed evidence")
        alternate_main = self._git_output("rev-parse", "HEAD")
        self._git("-C", str(self.root), "update-ref", "refs/remotes/origin/main", alternate_main)
        bundle_path = Path(self.temporary.name) / "alternate-history.bundle"
        self._git(
            "-C",
            str(self.root),
            "bundle",
            "create",
            str(bundle_path),
            "refs/remotes/origin/main",
            "refs/tags/v0.1.0",
            "refs/tags/v0.0.9",
        )
        bundle_bytes = bundle_path.read_bytes()
        part_path = self.manifest_path.parent / "original-history.bundle.part0000"
        part_path.write_bytes(bundle_bytes)
        self.manifest["original_main"] = alternate_main
        self.manifest["bundle"] = {
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "bytes": len(bundle_bytes),
            "parts": [
                {
                    "path": part_path.name,
                    "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                    "bytes": len(bundle_bytes),
                }
            ],
        }
        self._git("-C", str(self.root), "checkout", "--quiet", self.manifest["rewritten_base"])
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "pinned source commit"):
            evidence.verify(self.root)

    def test_current_tag_identity_must_remain_unchanged(self) -> None:
        self._git("-C", str(self.root), "update-ref", "refs/tags/v0.1.0", self.original_main)
        with self.assertRaisesRegex(evidence.EvidenceError, "current tag"):
            evidence.verify(self.root)

    def test_corrupt_part_is_rejected(self) -> None:
        part = self.manifest_path.parent / self.manifest["bundle"]["parts"][0]["path"]
        content = bytearray(part.read_bytes())
        content[len(content) // 2] ^= 1
        part.write_bytes(content)
        with self.assertRaisesRegex(evidence.EvidenceError, "part .* failed"):
            evidence.verify(self.root)

    def test_corrupt_cached_bundle_is_rejected(self) -> None:
        evidence.verify(self.root)
        cached_bundle = self.cache_dir / "original-history.bundle"
        content = bytearray(cached_bundle.read_bytes())
        content[len(content) // 2] ^= 1
        cached_bundle.write_bytes(content)
        with self.assertRaisesRegex(evidence.EvidenceError, "cached bundle does not match"):
            evidence.verify(self.root)

    def test_unlisted_part_is_rejected(self) -> None:
        extra = self.manifest_path.parent / "original-history.bundle.part0001"
        extra.write_bytes(b"unlisted part")
        with self.assertRaisesRegex(evidence.EvidenceError, "unlisted bundle part"):
            evidence.verify(self.root)

    def test_mutated_cached_git_refs_are_rejected(self) -> None:
        evidence.verify(self.root)
        archive_repo = self.cache_dir / "archive.git"
        self._git("--git-dir", str(archive_repo), "update-ref", "refs/remotes/origin/main", self.release_commit)
        with self.assertRaisesRegex(evidence.EvidenceError, "cached archive Git refs"):
            evidence.verify(self.root)

    def test_cached_git_alternates_are_rejected(self) -> None:
        evidence.verify(self.root)
        alternates = self.cache_dir / "archive.git/objects/info/alternates"
        alternates.write_text("/tmp/other-objects\n", encoding="utf-8")
        with self.assertRaisesRegex(evidence.EvidenceError, "object alternates"):
            evidence.verify(self.root)

    def test_cached_git_objects_symlink_is_rejected(self) -> None:
        evidence.verify(self.root)
        archive_repo = self.cache_dir / "archive.git"
        objects = archive_repo / "objects"
        saved_objects = archive_repo / "objects.saved"
        objects.rename(saved_objects)
        objects.symlink_to(saved_objects, target_is_directory=True)
        with self.assertRaisesRegex(evidence.EvidenceError, "objects path must be a real directory"):
            evidence.verify(self.root)

    def test_corrupt_cached_git_object_is_rejected_by_full_fsck(self) -> None:
        evidence.verify(self.root)
        archive_repo = self.cache_dir / "archive.git"
        object_id = evidence._tree_entries(archive_repo, self.original_main)[b"reports/raw/run.log"][2].decode("ascii")
        loose_object = archive_repo / "objects" / object_id[:2] / object_id[2:]
        loose_object.parent.mkdir(parents=True, exist_ok=True)
        loose_object.write_bytes(b"corrupt cached object")
        with self.assertRaisesRegex(evidence.EvidenceError, "failed full fsck"):
            evidence.verify(self.root)

    def test_unmapped_new_base_tree_is_rejected(self) -> None:
        self.manifest["rewritten_base"] = self.original_main
        evidence.PINNED_REWRITTEN_BASE = self.original_main
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "rewritten_base tree differs"):
            evidence.verify(self.root)

    def test_retained_source_change_in_new_base_is_rejected(self) -> None:
        self._write("src/app.py", b"silently changed source\n")
        self._git("-C", str(self.root), "add", "src/app.py")
        self._git("-C", str(self.root), "commit", "--quiet", "-m", "bad source update")
        self.manifest["rewritten_base"] = self._git_output("rev-parse", "HEAD")
        evidence.PINNED_REWRITTEN_BASE = self.manifest["rewritten_base"]
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "rewritten_base tree differs"):
            evidence.verify(self.root)

    def test_frozen_results_change_after_base_is_rejected(self) -> None:
        self._write("results/results.json", b'{"rows":["changed"]}\n')
        self._git("-C", str(self.root), "add", "results/results.json")
        self._git("-C", str(self.root), "commit", "--quiet", "-m", "bad frozen result update")
        with self.assertRaisesRegex(evidence.EvidenceError, r"results/\*\* differs"):
            evidence.verify(self.root)

    def test_traversal_path_is_rejected(self) -> None:
        self.manifest["removed_paths"]["files"] = ["../../outside.txt"]
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "unsafe path"):
            evidence.verify(self.root)

    def test_symlink_destination_parent_is_rejected(self) -> None:
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (self.root / "reports/raw").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(evidence.EvidenceError):
            evidence.hydrate(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_different_existing_bytes_are_not_overwritten(self) -> None:
        self._write("reports/raw/run.log", b"user data\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "refusing to overwrite different bytes"):
            evidence.hydrate(self.root)
        self.assertEqual((self.root / "reports/raw/run.log").read_bytes(), b"user data\n")

    def test_existing_fifo_is_rejected_without_opening_it(self) -> None:
        raw_directory = self.root / "reports/raw"
        raw_directory.mkdir(parents=True)
        os.mkfifo(raw_directory / "run.log")
        with self.assertRaisesRegex(evidence.EvidenceError, "non-regular path"):
            evidence.hydrate(self.root)

    def test_archive_symlink_mode_is_not_hydrated(self) -> None:
        # Make a fresh archive whose selected path is a Git symlink (mode 120000).
        self._git("-C", str(self.root), "checkout", "--quiet", self.original_main)
        target = self.root / "reports/raw/link"
        target.symlink_to("../freeze.json")
        self._git("-C", str(self.root), "add", "reports/raw/link")
        self._git("-C", str(self.root), "commit", "--quiet", "-m", "add raw symlink")
        new_main = self._git_output("rev-parse", "HEAD")
        self._git("-C", str(self.root), "update-ref", "refs/remotes/origin/main", new_main)
        bundle_path = Path(self.temporary.name) / "new-history.bundle"
        self._git(
            "-C",
            str(self.root),
            "bundle",
            "create",
            str(bundle_path),
            "refs/remotes/origin/main",
            "refs/tags/v0.1.0",
            "refs/tags/v0.0.9",
        )
        bundle_bytes = bundle_path.read_bytes()
        part_path = self.manifest_path.parent / "original-history.bundle.part0000"
        part_path.write_bytes(bundle_bytes)
        self.manifest["original_main"] = new_main
        evidence.PINNED_ORIGINAL_MAIN = new_main
        self.manifest["bundle"] = {
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "bytes": len(bundle_bytes),
            "parts": [
                {
                    "path": part_path.name,
                    "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                    "bytes": len(bundle_bytes),
                }
            ],
        }
        # Restore the filtered branch tip after generating this synthetic archive.
        self._git("-C", str(self.root), "checkout", "--quiet", self.manifest["rewritten_base"])
        # The symlink is selected by the existing reports/raw/ prefix.  Its
        # archived tree entry must be rejected before any destination write.
        self._write_manifest()
        with self.assertRaisesRegex(evidence.EvidenceError, "non-regular Git entry"):
            evidence.hydrate(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
