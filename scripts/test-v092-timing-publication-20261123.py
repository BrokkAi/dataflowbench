#!/usr/bin/env python3
"""Offline publication regressions: no analyzer binaries or host execution-state."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location("timing_publication", Path(__file__).with_name("v092_timing_publication_20261123.py"))
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)
ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dfb-publication-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.package = self.root / publication.PUBLICATION_REL
        shutil.copytree(ROOT / publication.PUBLICATION_REL, self.package)

    def rewrite(self, name, change):
        path = self.package / name
        value = json.loads(path.read_text())
        change(value)
        raw = publication._json_bytes(value)
        path.write_bytes(raw)
        manifest_path = self.package / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        ref = next(ref for ref in manifest["files"].values() if ref["path"] == name)
        ref.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        manifest_path.write_bytes(publication._json_bytes(manifest))

    def test_portable_replay_without_host_tree(self):
        self.assertFalse((self.root / "execution-state").exists())
        result = publication.verify(self.root)
        self.assertEqual(result["status"], "verified-portable-publication")
        self.assertEqual(result["case_rows"], 4144)
        summary = json.loads((self.package / "summary.json").read_text())
        self.assertEqual(summary["totals"]["accepted_invocation_cost_rows"], 3191)
        self.assertEqual(summary["totals"]["candidate_cold_groups"], 82)
        self.assertFalse(summary["certified_timing"])

    def test_flowdroid_modeling_preserves_declared_analyzer_phase(self):
        rows = json.loads((self.package / "cases.json").read_text())
        selected = [r for r in rows if r["group"] == "flowdroid-java-modeling" and r["invocation_cost_accepted"]]
        self.assertEqual(len(selected), 14)
        with zipfile.ZipFile(self.package / "source-evidence.zip") as archive:
            for row in selected:
                ref = next(r for r in row["source_refs"] if r["kind"] == "timing-sidecar")
                timing = json.loads(archive.read(ref["archive_path"]))
                phases = {p["phase"]: p["wall_ms"] for p in timing["phases"]}
                self.assertEqual(row["invocation_cost_ms"], phases["analyze"])
                self.assertLess(row["invocation_cost_ms"], sum(phases.values()))
                self.assertEqual(row["cost_basis"], "analyzer-phase-excluding-apk-materialization")

    def test_rehashed_cost_tampering_fails_replay(self):
        def change(rows):
            row = next(row for row in rows if row["invocation_cost_accepted"])
            row["invocation_cost_ms"] += 1
        self.rewrite("cases.json", change)
        with self.assertRaisesRegex(publication.PublicationError, "portable replay differs"):
            publication.verify(self.root)

    def test_rehashed_swift_partial_flag_tampering_fails_replay(self):
        def change(rows):
            row = next(row for row in rows if row["partial"])
            row["partial"] = False
        self.rewrite("cases.json", change)
        with self.assertRaisesRegex(publication.PublicationError, "portable replay differs"):
            publication.verify(self.root)

    def test_rehashed_source_reference_tampering_fails_replay(self):
        self.rewrite("cases.json", lambda rows: rows[0]["source_refs"][0].update(sha256="0" * 64))
        with self.assertRaisesRegex(publication.PublicationError, "portable replay differs"):
            publication.verify(self.root)

    def test_rehashed_quarantine_promotion_fails_replay(self):
        def change(rows):
            row = next(row for row in rows if row["group"] == "joern-rust-kernel")
            row["invocation_cost_accepted"] = True
        self.rewrite("cases.json", change)
        with self.assertRaisesRegex(publication.PublicationError, "portable replay differs"):
            publication.verify(self.root)

    def test_rehashed_certification_promotion_fails_replay(self):
        self.rewrite("summary.json", lambda value: value.update(certified_timing=True))
        with self.assertRaisesRegex(publication.PublicationError, "portable replay differs"):
            publication.verify(self.root)

    def test_download_hash_tampering_is_rejected(self):
        with (self.package / "cases.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(publication.PublicationError, "hash mismatch"):
            publication.verify(self.root)

    def test_staging_is_idempotent_and_preserves_conflicting_evidence(self):
        destination = self.root / "site"
        result = publication.stage_site(self.root, destination)
        self.assertEqual(result["files"], 8)
        self.assertEqual(publication.stage_site(self.root, destination), result)
        (destination / "cases.json").write_bytes(b"retained conflicting evidence")
        with self.assertRaisesRegex(publication.PublicationError, "refusing to overwrite"):
            publication.stage_site(self.root, destination)
        self.assertEqual((destination / "cases.json").read_bytes(), b"retained conflicting evidence")

    def test_staging_rejects_symlink_parent(self):
        actual = self.root / "actual"
        actual.mkdir()
        link = self.root / "linked"
        link.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(publication.PublicationError, "symlink staging"):
            publication.stage_site(self.root, link / "site")
        self.assertEqual(list(actual.iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
