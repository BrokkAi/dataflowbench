#!/usr/bin/env python3
"""Focused successor-release boundary tests using the existing tiny Git fixture."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path


HELPER_SCRIPTS = Path(
    os.environ.get("DATAFLOWBENCH_HISTORICAL_EVIDENCE_SCRIPTS", Path(__file__).resolve().parent)
).resolve()
if not HELPER_SCRIPTS.is_dir():
    raise RuntimeError(f"historical helper scripts directory does not exist: {HELPER_SCRIPTS}")
sys.path.insert(0, str(HELPER_SCRIPTS))

import historical_evidence as historical
import historical_evidence_publication as publication

fixture_path = Path(
    os.environ.get("DATAFLOWBENCH_HISTORICAL_EVIDENCE_TEST", HELPER_SCRIPTS / "test-historical-evidence.py")
).resolve()
spec = importlib.util.spec_from_file_location("historical_evidence_fixture", fixture_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load existing historical evidence fixture: {fixture_path}")
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


class SuccessorPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixture_module.HistoricalEvidenceTests(
            "test_roundtrip_restores_only_selected_original_bytes"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def _blob(self, revision: str, relative: str) -> bytes:
        _, _, manifest, archive_repo, _ = historical._load_archive(self.fixture.root)
        entries = historical._tree_entries(archive_repo, revision)
        entry = entries.get(os.fsencode(relative))
        if entry is None or entry[1] != b"blob":
            self.fail(f"fixture archive lacks regular blob {relative}")
        return historical._git(archive_repo, ["cat-file", "blob", entry[2].decode("ascii")]).stdout

    def _prepare_successor(self, *, release: str = "v0.9.2") -> tuple[bytes, bytes]:
        f = self.fixture
        old_freeze = self._blob(f.original_main, "reports/freeze.json")
        old_results = self._blob(f.original_main, "results/results.json")
        f._write("reports/releases/v0.9.0/freeze.json", old_freeze)
        f._write("docs/src/data/archive/v0-9-0-results.json", old_results)
        current_freeze = {
            "schema_version": 1,
            "benchmark": {
                "release": release,
                "revision": f.original_main,
                "dirty": False,
            },
            "claim": {"scope": "release"},
        }
        f._write("reports/freeze.json", json.dumps(current_freeze, sort_keys=True).encode() + b"\n")
        f._write("results/results.json", b'{"rows":["successor"]}\n')
        f._git("add", "reports/freeze.json", "results/results.json", "reports/releases/v0.9.0/freeze.json", "docs/src/data/archive/v0-9-0-results.json")
        f._git("commit", "--quiet", "-m", "publish successor freeze")
        return old_freeze, old_results

    def test_v092_verifies_historical_base_and_retained_v090_bytes(self) -> None:
        old_freeze, old_results = self._prepare_successor()
        result = publication.verify(self.fixture.root)
        self.assertTrue(result["verified"])
        self.assertEqual(result["scope"], "historical-only")
        self.assertEqual(result["current_release_validation"], "pending-v0.9.2-release-gate")
        self.assertEqual(result["publication_qualification"], "not-evaluated")
        self.assertEqual((self.fixture.root / "reports/releases/v0.9.0/freeze.json").read_bytes(), old_freeze)
        self.assertEqual((self.fixture.root / "docs/src/data/archive/v0-9-0-results.json").read_bytes(), old_results)
        self.assertNotEqual((self.fixture.root / "reports/freeze.json").read_bytes(), old_freeze)

    def test_v092_hydrate_restores_only_selected_files_and_keeps_release_files(self) -> None:
        old_freeze, old_results = self._prepare_successor()
        current_freeze = (self.fixture.root / "reports/freeze.json").read_bytes()
        current_results = (self.fixture.root / "results/results.json").read_bytes()
        restored = publication.hydrate(self.fixture.root)
        self.assertEqual(restored["restored_files"], 3)
        self.assertEqual(restored["scope"], "historical-only")
        self.assertEqual((self.fixture.root / "reports/raw/run.log").read_bytes(), b"raw diagnostic bytes\x00\xff\n")
        self.assertEqual((self.fixture.root / "reports/releases/v0.1.0/attempts/detail.json").read_bytes(), b'{"attempt":1}\n')
        self.assertEqual((self.fixture.root / "reports/releases/v0.1.0/ledger.jsonl").read_bytes(), b'{"ledger":true}\n')
        self.assertEqual((self.fixture.root / "reports/freeze.json").read_bytes(), current_freeze)
        self.assertEqual((self.fixture.root / "results/results.json").read_bytes(), current_results)
        self.assertEqual((self.fixture.root / "reports/releases/v0.9.0/freeze.json").read_bytes(), old_freeze)
        self.assertEqual((self.fixture.root / "docs/src/data/archive/v0-9-0-results.json").read_bytes(), old_results)
        second = publication.hydrate(self.fixture.root)
        self.assertEqual(second["restored_files"], 0)
        self.assertEqual(second["already_present_files"], 3)

    def test_v090_delegates_to_frozen_helper(self) -> None:
        f = self.fixture
        original_verify = historical.verify
        original_current_release = publication._current_release
        calls: list[Path] = []

        def delegated(root: Path) -> dict[str, object]:
            calls.append(Path(root))
            return {"delegated": True}

        historical.verify = delegated
        publication._current_release = lambda root: (
            Path(root), {"benchmark": {"release": "v0.9.0"}}, "v0.9.0"
        )
        self.addCleanup(setattr, historical, "verify", original_verify)
        self.addCleanup(setattr, publication, "_current_release", original_current_release)
        result = publication.verify(f.root)
        self.assertEqual(result, {"delegated": True})
        self.assertEqual(calls, [f.root])

    def test_retained_v090_archive_drift_fails_closed(self) -> None:
        self._prepare_successor()
        path = self.fixture.root / "reports/releases/v0.9.0/freeze.json"
        path.write_bytes(b"drift\n")
        with self.assertRaisesRegex(historical.EvidenceError, "working file differs"):
            publication.verify(self.fixture.root)

    def test_incorrect_release_claim_dirty_or_revision_is_rejected(self) -> None:
        self._prepare_successor()
        freeze_path = self.fixture.root / "reports/freeze.json"
        good = json.loads(freeze_path.read_text())
        bad_values = (
            ({**good, "benchmark": {**good["benchmark"], "release": "v0.9.1"}}, "unsupported current release"),
            ({**good, "claim": {"scope": "benchmark"}}, "claim.scope must be release"),
            ({**good, "benchmark": {**good["benchmark"], "dirty": True}}, "dirty=false"),
            ({**good, "benchmark": {**good["benchmark"], "revision": "abc"}}, "full lowercase SHA-1"),
        )
        for bad, message in bad_values:
            with self.subTest(message=message):
                freeze_path.write_text(json.dumps(bad) + "\n")
                self.fixture._git("add", "reports/freeze.json")
                self.fixture._git("commit", "--quiet", "-m", "test successor freeze boundary")
                with self.assertRaisesRegex(historical.EvidenceError, message):
                    publication.verify(self.fixture.root)

    def test_preserved_tag_drift_is_rejected(self) -> None:
        self._prepare_successor()
        self.fixture._git("update-ref", "refs/tags/v0.1.0", self.fixture.original_main)
        with self.assertRaisesRegex(historical.EvidenceError, "preserved object ID"):
            publication.verify(self.fixture.root)

    def test_unrelated_head_cannot_claim_successor_history(self) -> None:
        self._prepare_successor()
        f = self.fixture
        base_tree = f._git_output("rev-parse", f"{f.manifest['rewritten_base']}^{{tree}}")
        orphan = f._git_output("commit-tree", base_tree, "-m", "unrelated history")
        f._git("checkout", "--quiet", "--detach", orphan)
        # Classification reads the on-disk current freeze; the proof must stop
        # specifically at the rewritten-base ancestry check.
        f._write(
            "reports/freeze.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "benchmark": {"release": "v0.9.2", "revision": f.original_main, "dirty": False},
                    "claim": {"scope": "release"},
                }
            ).encode() + b"\n",
        )
        f._git("add", "reports/freeze.json")
        f._git("commit", "--quiet", "-m", "unrelated successor freeze")
        with self.assertRaisesRegex(historical.EvidenceError, "not an ancestor"):
            publication.verify(f.root)

    def test_unknown_current_release_is_rejected(self) -> None:
        self._prepare_successor(release="v1.0.0")
        with self.assertRaisesRegex(historical.EvidenceError, "unsupported current release"):
            publication.verify(self.fixture.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
