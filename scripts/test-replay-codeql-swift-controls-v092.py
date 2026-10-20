#!/usr/bin/env python3
"""Host-bound, no-analyzer checks for the retained CodeQL attempt-02 evidence.

These integration checks require the acquired local runtime files and the
original capture root. Keep them out of hermetic CI; the release collector
and plan validator replay the same registered evidence in their own gates.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name("replay-codeql-swift-controls-v092.py")
SPEC = importlib.util.spec_from_file_location("replay_codeql_swift_controls_v092", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
recovery = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = recovery
SPEC.loader.exec_module(recovery)


class CodeQLControlReplayRecoveryTests(unittest.TestCase):
    """Exercise current eligibility against the retained, promoted plan."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ROOT
        cls.plan, cls.receipt, _context = recovery.runner.validate_plan(
            ROOT, recovery.PLAN_PATH
        )
        cls.control = recovery.read_json(
            recovery.checked_repository_reference(
                ROOT, cls.plan["qualification_control_plan"], "CodeQL control plan"
            ),
            "CodeQL control plan",
        )
        cls.control_run = recovery.read_json(
            recovery.checked_repository_reference(
                ROOT, cls.receipt["control_run"], "CodeQL control run"
            ),
            "CodeQL control run",
        )
        cls.query_receipt = recovery.read_json(
            recovery.checked_repository_reference(
                ROOT,
                cls.receipt["dimensions"]["query_resolution_compile"]["receipt"],
                "CodeQL query receipt",
            ),
            "CodeQL query receipt",
        )

    def test_current_eligible_plan_replays_retained_controls_without_analyzer(self) -> None:
        self.assertEqual(self.plan["status"], "execution-eligible")
        self.assertTrue(self.plan["execution_eligible"])
        self.assertEqual(self.receipt["status"], "measurement-with-known-limits")
        self.assertTrue(self.receipt["execution_eligible"])

        assessment = recovery.replay.replay_control_run(
            self.root,
            self.plan,
            self.control,
            self.control_run,
            self.receipt["dimensions"],
        )
        self.assertEqual(assessment, self.control_run["assessment"])
        entry = assessment["entry_extractor"]
        self.assertEqual(entry["status"], "measurement-with-known-limits")
        self.assertFalse(entry["strict_qualified"])
        self.assertEqual(entry["case_count"], 10)
        self.assertEqual(
            set(entry["known_limit_deltas"]),
            {"array-element-negative", "callback-registration-positive"},
        )
        self.assertEqual(assessment["model_activation"]["case_arm_count"], 4)
        self.assertTrue(assessment["model_activation"]["strict_qualified"])
        self.assertEqual(assessment["sanitizer_activation"]["case_arm_count"], 8)
        self.assertTrue(assessment["sanitizer_activation"]["strict_qualified"])
        self.assertFalse(assessment["entry_extractor"]["scored_activation"])

    def test_query_receipt_with_wrong_query_digest_is_rejected(self) -> None:
        recovery.runner.verify_query_receipt(
            self.root, self.plan, self.query_receipt, recovery.PLAN_PATH
        )
        altered = copy.deepcopy(self.query_receipt)
        first_query = sorted(altered["queries"])[0]
        altered["queries"][first_query]["query_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "query source changed"):
            recovery.runner.verify_query_receipt(
                self.root, self.plan, altered, recovery.PLAN_PATH
            )

    def test_false_aggregate_assessment_is_rejected_after_raw_replay(self) -> None:
        altered_run = copy.deepcopy(self.control_run)
        altered_run["assessment"]["entry_extractor"]["status"] = "qualified"
        altered_run["assessment"]["entry_extractor"]["strict_qualified"] = True
        with self.assertRaisesRegex(ValueError, "control-run assessment differs from replay"):
            recovery.replay.replay_control_run(
                self.root,
                self.plan,
                self.control,
                altered_run,
                self.receipt["dimensions"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
