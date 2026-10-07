#!/usr/bin/env python3
"""Focused regression checks for the no-build Swift recovery verifier."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/restore-v090-swift-runtime-20261007.py"
spec = importlib.util.spec_from_file_location("restore_v090", SCRIPT)
restore = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(restore)
REAL_ASSETS = "--real-assets" in sys.argv


class RestoreV090Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = restore.validate_plan(ROOT / "adapters/codeql/swift-normal-v1/plan-2026-09-28-06")
        cls.build = ROOT / "execution-state/v090-resume-20261007-01/extractor-build"

    def test_real_plan_uses_actual_manifest_keys_and_counts(self):
        self.assertEqual(self.plan["manifests"]["extractor_tree"]["entries"], 2277)
        self.assertEqual(self.plan["manifests"]["packs_tree"]["entries"], 3402)
        self.assertEqual(self.plan["manifests"]["extractor"]["entries"], 2277)
        self.assertEqual(self.plan["manifests"]["packs"]["entries"], 3402)

    @unittest.skipUnless(REAL_ASSETS, "pass --real-assets for the durable restored-tree check")
    def test_primary_restored_candidates_verify_in_place_without_copy(self):
        extractor = self.build / "candidate-extractor"
        packs = self.build / "repaired-packs"
        extractor_result = restore.stage_candidate(extractor, extractor, self.plan["trees"]["extractor"], "extractor")
        packs_result = restore.stage_candidate(packs, packs, self.plan["trees"]["packs"], "packs")
        self.assertEqual(extractor_result["status"], "verified-existing")
        self.assertEqual(packs_result["status"], "verified-existing")
        self.assertEqual(extractor_result["staged"]["entries"], 2277)
        self.assertEqual(packs_result["staged"]["entries"], 3402)
        qlpack = packs / "codeql/swift-all/6.8.4-dfb.entry1/qlpack.yml"
        self.assertIn("version: 6.8.4-dfb.entry1\n", qlpack.read_text())
        self.assertNotIn("buildMetadata:", qlpack.read_text())

    def test_temp_fixture_covers_tree_integrity_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            payload = source / "payload"
            payload.write_text("exact\n")
            payload.chmod(0o751)
            (source / "alias").symlink_to("payload")
            expected = restore.tree_entries(source)
            staged = root / "staged"
            result = restore.stage_candidate(source, staged, expected, "packs")
            self.assertEqual(result["status"], "staged-and-verified")
            self.assertEqual(restore.verify_tree(staged, expected, "fixture"), result["staged"])
            (staged / "payload").write_text("tampered\n")
            with self.assertRaisesRegex(restore.RecoveryError, "immutable tree manifest"):
                restore.stage_candidate(source, staged, expected, "packs")

    def test_output_names_are_single_safe_basenames(self):
        for name in ("../escape", "nested/name", "/absolute", "", ".", ".."):
            with self.subTest(name=name), self.assertRaises(restore.RecoveryError):
                restore.safe_output_name(name, "candidate")
        self.assertEqual(restore.safe_output_name("candidate-extractor", "candidate"), "candidate-extractor")

    def test_symlink_destination_is_rejected_before_resolution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            link = root / "destination"
            link.symlink_to(target, target_is_directory=True)
            with patch.object(sys, "argv", [str(SCRIPT), "--destination", str(link)]):
                with self.assertRaisesRegex(restore.RecoveryError, "symlink destination"):
                    restore.main()


if __name__ == "__main__":
    if "--real-assets" in sys.argv:
        sys.argv.remove("--real-assets")
    unittest.main()
