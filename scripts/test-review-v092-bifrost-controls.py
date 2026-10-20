#!/usr/bin/env python3
"""Exercise qualification safety against retained real schema-6 controls."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v092_review", HERE / "review-v092-bifrost-controls.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewTests(unittest.TestCase):
    def altered(self, case_name, mutate):
        prior = review.module("v092_test_prior", "review-bifrost-v013-controls.py")
        original = prior.qualifier._load_report

        def decode(path):
            result = original(path)
            if path.name == case_name + ".json":
                result = copy.deepcopy(result)
                mutate(result)
            return result

        prior.qualifier._load_report = decode
        with patch.object(review, "module", return_value=prior):
            return review.review()

    def test_real_partial_runs_stay_inconclusive(self):
        result = review.review()
        self.assertEqual(result["status"], "measurement-with-known-limits")
        self.assertFalse(result["full_policy_qualification"])
        partial = [row for row in result["controls"] if row["interpretation"] == "inconclusive"]
        self.assertEqual(len(partial), 3)
        self.assertTrue(all(row["clean"] is False for row in partial))

    def test_unreviewed_obligation_rejects_measurement(self):
        def mutate(report):
            report["runs"][0]["obligations"] = [{"kind": "unresolved_call"}]
        with self.assertRaisesRegex(ValueError, "unreviewed schema-6 obligations"):
            self.altered("policy-java-declared-source-positive-with", mutate)

    def test_partial_scope_cannot_be_dropped(self):
        def mutate(report):
            report["runs"][0]["completion"].pop("scope")
        with self.assertRaisesRegex(ValueError, "unexpected partial scope"):
            self.altered("policy-javascript-declared-source-positive-with", mutate)

    def test_positive_proof_cannot_be_downgraded_silently(self):
        def mutate(report):
            report["runs"][0]["findings"][0]["proof"]["state"] = "unproven"
        with self.assertRaisesRegex(ValueError, "finding is not proven"):
            self.altered("policy-javascript-declared-source-positive-with", mutate)


if __name__ == "__main__":
    unittest.main()
