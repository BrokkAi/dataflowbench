#!/usr/bin/env python3
"""Focused read-only tests for the Joern04 contract builder."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("build-joern-capability-continuation-03.py")
SPEC = importlib.util.spec_from_file_location("joern_capability_builder_02_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class JoernContinuationBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = MODULE.ROOT
        self.base = MODULE.load_json(self.root, MODULE.BASE_CONTRACT, "base contract")
        self.plan = MODULE.load_json(self.root, MODULE.FINAL_PLAN, "repaired plan")
        self.evidence = MODULE.load_json(self.root, MODULE.EVIDENCE, "capability evidence")

    def _contract(self) -> dict:
        return MODULE.build_contract(
            self.root, "1" * 40, plan=self.plan, evidence=self.evidence,
            base=copy.deepcopy(self.base), delta=[]
        )

    def test_contract_adds_exact_guard_markers_and_fourth_attempt(self) -> None:
        contract = self._contract()
        joern = next(group for group in contract["groups"]
                     if group.get("id") == MODULE.JOERN_GROUP)
        historical = MODULE.load_json(self.root, MODULE.OLD_CONTRACT,
                                      "historical Joern03 continuation contract")
        old_joern = next(group for group in historical["groups"]
                         if group.get("id") == MODULE.JOERN_GROUP)
        self.assertEqual(joern["maximum_attempts"], 4)
        self.assertEqual(joern["environment"], {
            **old_joern["environment"],
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
            "DATAFLOWBENCH_V092_GROUP_ID": MODULE.JOERN_GROUP,
        })
        MODULE.validate_contract_delta(self.root, contract)

    def test_contract_rejects_unreviewed_environment_change(self) -> None:
        contract = self._contract()
        joern = next(group for group in contract["groups"]
                     if group.get("id") == MODULE.JOERN_GROUP)
        joern["environment"]["UNREVIEWED_MARKER"] = "1"
        with self.assertRaises(MODULE.BuildError):
            MODULE.validate_contract_delta(self.root, contract)

    def test_non_joern_group_is_immutable(self) -> None:
        contract = self._contract()
        codeql = next(group for group in contract["groups"]
                      if group.get("id") == MODULE.CODEQL_GROUP)
        codeql["maximum_attempts"] += 1
        with self.assertRaises(MODULE.BuildError):
            MODULE.validate_contract_delta(self.root, contract)

    def test_fourth_attempt_authorization_is_exactly_bound(self) -> None:
        self.assertEqual(MODULE.AUTHORIZATION_PATH.endswith(
            "authorization-fourth-attempt-01.json"), True)
        self.assertEqual(MODULE.AUTHORIZATION_SHA,
                         "d0068fa640f953912cc0b682b0fb8b957282e174ad3f103493d38cb2c140f9d7")
        self.assertEqual(MODULE.LEDGER_ROWS, 87)
        self.assertEqual(MODULE.LEDGER_SHA,
                         "57d8265e8eb0c216c56e184a5fed36f9931bcb5b36ea1047ae3f4a0c71f0a096")
        self.assertEqual(MODULE.HISTORICAL_LEDGER_ROWS, 86)
        self.assertEqual(MODULE.HISTORICAL_LEDGER_SHA,
                         "ca7152afb422160b30c2f38677aa539a1463b45e3b41131848b3d9e81d4a1084")
        self.assertEqual(MODULE.SEALED_LEDGER_ROWS, 87)
        self.assertEqual(MODULE.SEALED_LEDGER_SHA, MODULE.LEDGER_SHA)
        self.assertEqual(MODULE.JOERN_OUTPUT,
                         "reports/raw/joern-common-v2/current108-v092-02")

    def test_source_closure_names_sealed_ledger_and_public_stop_evidence_only(self) -> None:
        source = MODULE_PATH.read_text()
        self.assertIn("SEALED_LEDGER_PATH", source)
        self.assertIn("ref(root, SEALED_LEDGER_PATH, \"sealed 87-row ledger predecessor\")", source)
        self.assertIn("LEDGER_PATH not in result", source)
        self.assertNotIn("execution-state/v092/matrix-supervision-24/joern-swift-common108-stderr.txt",
                          source)
        self.assertNotIn("execution-state/v092/matrix-supervision-24/joern-swift-common108-stdout.txt",
                          source)
        self.assertNotIn("execution-state/v092/matrix-supervision-24/supervisor-stderr.txt", source)
        self.assertNotIn("execution-state/v092/matrix-supervision-24/supervisor-stdout.txt", source)


if __name__ == "__main__":
    unittest.main()
