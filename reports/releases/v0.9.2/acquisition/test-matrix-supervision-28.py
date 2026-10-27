#!/usr/bin/env python3
"""Static/no-process tests for supervision-28 successor bindings."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "supervision28", Path(__file__).with_name("matrix-supervision-28.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Supervision28BindingsTests(unittest.TestCase):
    def test_successor_namespaces_and_paths_are_append_only(self):
        self.assertTrue(str(MODULE.STATE).endswith("matrix-supervision-28"))
        self.assertTrue(str(MODULE.PUBLIC).endswith("supervision-28"))
        self.assertTrue(str(MODULE.MODULE).endswith("joern-capability-continuation-05.py"))
        self.assertTrue(MODULE.MANIFEST.endswith("continuation-manifest-06.json"))
        self.assertTrue(str(MODULE.REVIEW).endswith("supervision28-independent-review-01.json"))

    def test_command_is_bound_to_successor_module_and_manifest(self):
        class Args:
            manifest = MODULE.MANIFEST
            manifest_sha256 = "a" * 64
        command = MODULE.command(Args(), "preflight")
        self.assertIn(str(MODULE.MODULE), command)
        self.assertEqual(command[command.index("--manifest") + 1], MODULE.MANIFEST)
        self.assertNotIn("--retry", command)

    def test_gate_still_has_exact_identity_and_stop_timeout(self):
        self.assertIn("argv_sha256", MODULE.GATE)
        self.assertIn("end=time.monotonic()+30", MODULE.GATE)
        self.assertIn("sys.exit(125)", MODULE.GATE)
        self.assertIn("sys.exit(126)", MODULE.GATE)
        self.assertIn("os.execv", MODULE.GATE)


if __name__ == "__main__":
    unittest.main()
