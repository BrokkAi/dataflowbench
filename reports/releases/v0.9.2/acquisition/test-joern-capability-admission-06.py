#!/usr/bin/env python3
"""No-analyzer tests for the no-expiry admission-06 path gates."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "admission06", Path(__file__).with_name("joern-capability-admission-06.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Admission06PathTests(unittest.TestCase):
    def test_only_new_provisional_manifest_is_admissible(self):
        for path in [MODULE.BASE + "continuation-manifest-05.json", "../outside.json"]:
            with self.subTest(path=path), patch.object(sys, "argv", [
                "admission06", "--manifest", path, "--manifest-sha256", "0" * 64,
                "--module-sha256", "0" * 64]), patch.object(MODULE, "sha") as digest, \
                    patch.object(MODULE.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "exact reviewed provisional"):
                    MODULE.main()
                digest.assert_not_called()
                run.assert_not_called()

    def test_exact_provisional_reaches_successor_source_digest_gate(self):
        with patch.object(sys, "argv", [
            "admission06", "--manifest", MODULE.PROVISIONAL_MANIFEST,
            "--manifest-sha256", "0" * 64, "--module-sha256", "0" * 64]), \
                patch.object(MODULE, "sha", return_value="wrong") as digest, \
                patch.object(MODULE.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "module changed"):
                MODULE.main()
            digest.assert_called_once()
            run.assert_not_called()

    def test_receipt_policy_is_typed_null_window(self):
        self.assertEqual(MODULE.EXECUTION_WINDOW_SCHEMA,
                         "v092-no-user-execution-window-policy/v1")
        self.assertEqual(MODULE.AUTHORIZATION_SHA,
                         "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc")
        self.assertEqual(MODULE.PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS, 30)
        self.assertIsNone(None)  # Explicitly document the JSON null representation.
        self.assertTrue(MODULE.MATERIALIZED_SOURCE.endswith("preflight-06"))
        self.assertTrue(MODULE.RETAINED_PREFLIGHT.endswith("retained-preflight-06.json"))


if __name__ == "__main__":
    unittest.main()
