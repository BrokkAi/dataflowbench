#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "reports/releases/v0.9.2/acquisition/build-independent-pending-codeql-01.py"


def load():
    spec = importlib.util.spec_from_file_location("build_independent_pending_codeql_tested", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CodeQLBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()
        cls.refs = cls.m.source_closure(ROOT)

    def test_draft_preserves_frozen_groups_and_adds_only_codeql_environment_witness(self):
        value = self.m.draft_contract(ROOT, "a" * 40, self.refs)
        self.m.validate_draft(ROOT, value, "a" * 40)
        codeql = next(g for g in value["groups"] if g["id"] == self.m.CODEQL_GROUP)
        self.assertEqual(codeql["environment"]["__CF_USER_TEXT_ENCODING"], self.m.CF_USER_TEXT_ENCODING)
        self.assertEqual(value["resource_guards"]["working_set_gib"], 30)
        self.assertEqual(value["execution_window"]["phase_remaining_reserved_seconds"], 28032)
        self.assertNotIn("reports/releases/v0.9.2/ledger-v1.jsonl",
                         {item["path"] for item in value["source_inputs"]})

    def test_source_closure_contains_sealed_prefix_and_not_mutable_ledger(self):
        paths = {item["path"] for item in self.refs}
        self.assertIn(self.m.SEALED_LEDGER, paths)
        self.assertIn(self.m.QUERY_RECEIPT, paths)
        self.assertIn(
            "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-08-contract.json",
            paths,
        )
        self.assertNotIn("reports/releases/v0.9.2/ledger-v1.jsonl", paths)
        base = json.loads((ROOT / Path(*self.m.BASE_CONTRACT.split("/"))).read_bytes())
        predecessor = json.loads((ROOT / Path(*self.m.HISTORICAL_REPLAY_CONTRACT.split("/"))).read_bytes())
        base_paths = {item["path"] for item in base["source_inputs"]}
        predecessor_paths = {item["path"] for item in predecessor["source_inputs"]}
        self.assertFalse(predecessor_paths - (base_paths | paths))

    def test_plan_commit_must_be_an_exact_repository_commit(self):
        with self.assertRaises(self.m.CodeQLBuildError):
            self.m.verify_exact_commit(ROOT, "a" * 40, "plan commit")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.m.verify_exact_commit(ROOT, head, "plan commit")

    def test_wrong_cap_is_rejected(self):
        value = self.m.draft_contract(ROOT, "a" * 40, self.refs)
        value["resource_guards"]["working_set_gib"] = 31
        with self.assertRaises(self.m.CodeQLBuildError):
            self.m.validate_draft(ROOT, value, "a" * 40)

    def test_non_codeql_group_mutation_is_rejected(self):
        value = self.m.draft_contract(ROOT, "a" * 40, self.refs)
        bifrost = next(g for g in value["groups"] if g["id"] != self.m.CODEQL_GROUP)
        bifrost["argv"] = list(bifrost["argv"]) + ["unexpected"]
        with self.assertRaises(self.m.CodeQLBuildError):
            self.m.validate_draft(ROOT, value, "a" * 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
