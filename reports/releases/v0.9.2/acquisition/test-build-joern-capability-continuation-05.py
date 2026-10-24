#!/usr/bin/env python3
"""Focused no-analyzer tests for the no-expiry continuation-05 builder."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("build-joern-capability-continuation-05.py")
SPEC = importlib.util.spec_from_file_location("joern_capability_builder_05_tested", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Builder05Tests(unittest.TestCase):
    def setUp(self):
        self.root = MODULE.ROOT
        self.base = MODULE.load_json(self.root, MODULE.OLD_CONTRACT, "predecessor contract")
        self.plan = MODULE.load_json(self.root, MODULE.FINAL_PLAN, "repaired plan")
        self.evidence = MODULE.load_json(self.root, MODULE.EVIDENCE, "capability evidence")

    def _contract(self):
        return MODULE.build_contract(
            self.root, "1" * 40, plan=self.plan, evidence=self.evidence,
            base=copy.deepcopy(self.base), delta=[]
        )

    def test_contract_uses_typed_null_window_and_finite_attempt_policy(self):
        contract = self._contract()
        self.assertIsNone(contract["total_wall_budget_seconds"])
        policy = contract["execution_window"]
        self.assertEqual(policy["schema"], MODULE.EXECUTION_WINDOW_SCHEMA)
        self.assertEqual(policy["mode"], "no-user-imposed-expiry")
        self.assertIsNone(policy["cutoff_utc"])
        self.assertIsNone(policy["total_wall_budget_seconds"])
        self.assertEqual(policy["historical_total_wall_budget_seconds"], 333360)
        self.assertEqual(policy["per_attempt_timeout_source"],
                         "registered-plan-group-deadline-seconds")
        joern = next(row for row in contract["groups"] if row["id"] == MODULE.JOERN_GROUP)
        self.assertEqual(joern["maximum_attempts"], 4)
        self.assertEqual(joern["output_roots"], [MODULE.JOERN_OUTPUT])
        self.assertEqual(contract["resource_guards"]["working_set_gib"], 30)
        self.assertEqual(contract["aggregate_source_working_cap"], MODULE.SOURCE_WORKING_CAP)
        MODULE.validate_contract_delta(self.root, contract)

    def test_non_joern_fields_and_launch_environment_are_immutable(self):
        contract = self._contract()
        codeql = next(row for row in contract["groups"] if row["id"] == MODULE.CODEQL_GROUP)
        codeql["maximum_attempts"] += 1
        with self.assertRaises(MODULE.BuildError):
            MODULE.validate_contract_delta(self.root, contract)

    def test_no_expiry_authority_and_ledger_are_exact(self):
        result = MODULE.validate_fourth_attempt_inputs(self.root)
        self.assertEqual(result["authorization"], {
            "path": MODULE.AUTHORIZATION_PATH, "sha256": MODULE.AUTHORIZATION_SHA})
        self.assertEqual(result["ledger"]["rows"], MODULE.LEDGER_ROWS)
        self.assertEqual(result["ledger"]["sha256"], MODULE.LEDGER_SHA)
        self.assertEqual(result["source_working_cap_authorization"], {
            "path": MODULE.SOURCE_WORKING_AUTHORIZATION_PATH,
            "sha256": MODULE.SOURCE_WORKING_AUTHORIZATION_SHA,
        })
        self.assertNotEqual(MODULE.AUTHORIZATION_PATH, MODULE.HISTORICAL_AUTHORIZATION_PATH)

    def test_source_delta_excludes_mutable_live_ledger(self):
        source = MODULE.Path(MODULE.CONTINUATION_SOURCE)
        self.assertTrue(source.name.endswith("continuation-05.py"))
        self.assertNotEqual(MODULE.LEDGER_PATH, MODULE.CONTINUATION_SOURCE)
        self.assertNotIn(MODULE.LEDGER_PATH, MODULE.HISTORICAL_AUTHORIZATION_PATH)

    def test_source_delta_uses_immutable_base_boundary(self):
        immutable = MODULE.load_json(self.root, MODULE.BASE_CONTRACT, "immutable base contract")
        base_inputs = {item["path"]: item["sha256"] for item in immutable["source_inputs"]}
        delta = MODULE.collect_delta(self.root, self.evidence, self.plan, base_inputs)
        paths = {item["path"] for item in delta}
        self.assertEqual(len(paths), len(delta))
        self.assertIn(MODULE.OLD_CONTRACT, paths)
        self.assertIn("reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py", paths)
        self.assertIn("reports/releases/v0.9.2/acquisition/joern-capability-continuation-04.py", paths)
        self.assertNotIn(MODULE.LEDGER_PATH, paths)


if __name__ == "__main__":
    unittest.main()
