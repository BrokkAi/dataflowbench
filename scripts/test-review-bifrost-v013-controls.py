#!/usr/bin/env python3
"""Integrity regressions against immutable captured Bifrost controls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


review = module("review", "review-bifrost-v013-controls.py")
executor = module("executor", "execute-release-v091.py")


class ReviewTests(unittest.TestCase):
    def test_actual_receipt_preserves_limits_and_does_not_qualify(self):
        result = review.audit()
        self.assertFalse(result["full_policy_qualification"])
        self.assertEqual(result["original_qualification"]["status"], "failed")
        self.assertEqual(result["inconclusive_policy_runs"], 3)
        self.assertEqual(result["unbound_endpoint_controls"], 15)
        self.assertEqual(result["sanitizer_controls"], 15)
        self.assertFalse(result["native"]["clean"])

    def test_changed_capture_is_rejected(self):
        original = review.digest
        def changed(path):
            return "0" * 64 if path.name == "policy-python-declared-source-positive-with.json" else original(path)
        with patch.object(review, "digest", changed), self.assertRaisesRegex(ValueError, "changed capture"):
            review.audit()

    def test_new_incomplete_state_is_rejected(self):
        original = review.qualifier._load_report
        def incomplete(path):
            report = copy.deepcopy(original(path))
            if path.name == "sanitizer-java-sanitizer-kill-positive-with.json":
                report["runs"][0]["completion"] = {"type": "inconclusive", "reasons": ["budget_exhausted"]}
            return report
        with patch.object(review.qualifier, "_load_report", incomplete), self.assertRaisesRegex(ValueError, "run is incomplete"):
            review.audit()

    def test_changed_known_limit_is_rejected(self):
        original = review.qualifier._load_report
        def incomplete(path):
            report = copy.deepcopy(original(path))
            if path.name == "policy-javascript-declared-source-positive-with.json":
                report["runs"][0]["completion"]["reasons"].append("budget_exhausted")
            return report
        with patch.object(review.qualifier, "_load_report", incomplete), self.assertRaisesRegex(ValueError, "known limitation changed"):
            review.audit()

    def test_novel_advisory_is_rejected(self):
        original = review.qualifier._load_report
        def advisory(path):
            report = copy.deepcopy(original(path))
            if path.name == "policy-python-declared-source-negative-with.json":
                report["runs"][0]["diagnostics"][0]["code"] = {"type": "new_unsupported_state"}
            return report
        with patch.object(review.qualifier, "_load_report", advisory), self.assertRaisesRegex(ValueError, "unexpected diagnostic"):
            review.audit()

    def test_forged_favorable_summary_cannot_authorize_execution(self):
        root = review.ROOT
        path = root / "reports/releases/v0.9.1/qualification/review-01.json"
        result = json.loads(path.read_text())
        result["inconclusive_policy_runs"] = 0
        raw = (json.dumps(result) + "\n").encode()
        plan = {"qualification": {"path": path.relative_to(root).as_posix(), "sha256": executor._sha(raw)},
                "tools": {"bifrost": result["tool"]}}
        with patch.object(executor, "_read_json", return_value=(result, raw)), \
                self.assertRaisesRegex(executor.ReleaseError, "differs from recomputed"):
            executor._qualification_gate(plan, root)


if __name__ == "__main__":
    unittest.main()
