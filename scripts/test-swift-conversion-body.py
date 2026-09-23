#!/usr/bin/env python3
"""Mutation checks for the bounded non-scored Swift conversion body verifier."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "verify_swift_conversion_body", Path(__file__).with_name("verify-swift-conversion-body.py"))
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class ConversionBodyVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = verify.read_json(verify.PLAN_PATH)
        cls.attempt = verify.DEFAULT_ATTEMPT
        cls.labels = cls.plan["control_labels"]

    def patched_tables(self):
        tables, missing = verify.lane_tables(self.attempt / "probe")
        self.assertEqual(missing, [])
        return copy.deepcopy(tables)

    def test_real_attempt_reports_both_blockers_without_score_promotion(self):
        result = verify.verify()
        self.assertTrue(result["patched_lane"]["positive_flow_observed"])
        # Keep the real positive independent from the body and initializer failures.
        self.assertNotIn("missing expected patched positive flow to POSITIVE_SINK",
                         result["patched_lane"]["blockers"])
        self.assertIn("missing expected patched positive flow to BODY_SINK",
                      result["patched_lane"]["blockers"])
        self.assertIn("unexpected patched flow to WRONG_ARITY_SINK",
                      result["patched_lane"]["blockers"])
        self.assertEqual(result["qualification"],
                         "not-qualified; diagnostic-only; score activation disabled")
        self.assertNotEqual(result["integrity_status"], "failed")
        self.assertIn("stock BODY_SINK reachability is not proof of local-body propagation",
                      result["limitations"])

    def test_missing_ordinary_body_flow_remains_a_blocker(self):
        tables = self.patched_tables()
        result = verify.evaluate_patched(tables, self.labels)
        self.assertIn("missing expected patched positive flow to BODY_SINK", result["blockers"])

    def test_missing_real_positive_is_not_waived_by_other_findings(self):
        tables = self.patched_tables()
        tables["flow"] = [row for row in tables["flow"] if row[1] != self.labels["POSITIVE_SINK"]]
        result = verify.evaluate_patched(tables, self.labels)
        self.assertIn("missing expected patched positive flow to POSITIVE_SINK", result["blockers"])

    def test_wrong_arity_flow_is_a_hard_blocker(self):
        tables = self.patched_tables()
        tables["flow"] = [row for row in tables["flow"] if row[1] != self.labels["WRONG_ARITY_SINK"]]
        without_initializer_flow = verify.evaluate_patched(tables, self.labels)
        self.assertNotIn("unexpected patched flow to WRONG_ARITY_SINK", without_initializer_flow["blockers"])
        tables["flow"].append([15, self.labels["WRONG_ARITY_SINK"], 87,
                               verify.PATCHED_PROFILE])
        result = verify.evaluate_patched(tables, self.labels)
        self.assertIn("unexpected patched flow to WRONG_ARITY_SINK", result["blockers"])

    def test_invented_lane_profile_is_rejected(self):
        tables = self.patched_tables()
        tables["flow"][0][3] = "adapter-patched-plus-invented"
        with self.assertRaisesRegex(verify.VerificationError, "invented or cross-lane"):
            verify.evaluate_patched(tables, self.labels)

    def test_local_body_summary_cannot_be_promoted_to_modeled(self):
        tables = self.patched_tables()
        body_call = next(row for row in tables["summary-identity"] if row[0] == 31)
        body_call[7] = True
        with self.assertRaisesRegex(verify.VerificationError, "summary identity/applicability"):
            verify.check_patched_summaries(tables)

    def test_rewritten_wrong_arity_near_miss_is_rejected(self):
        tables = self.patched_tables()
        wrong_arity = next(row for row in tables["summary-identity"] if row[0] == 41)
        wrong_arity[5] = "init(data:encoding:)"
        wrong_arity[6] = 2
        with self.assertRaisesRegex(verify.VerificationError, "summary identity/applicability"):
            verify.check_patched_summaries(tables)

    def test_compiler_and_extractor_hashes_join_to_prior_and_run(self):
        current = verify.read_json(self.attempt / "probe/witness.json")
        prior = verify.read_json(verify.ROOT /
            "evidence/swift-foundation-sources-v1/control-attempt-01/witness.json")
        run = verify.read_json(self.attempt / "run.json")
        verify.check_toolchain_joins(current, prior, run)
        changed = copy.deepcopy(current)
        changed["compiler_sha256"] = "0" * 64
        with self.assertRaisesRegex(verify.VerificationError, "compiler_sha256.*prior witness"):
            verify.check_toolchain_joins(changed, prior)
        changed = copy.deepcopy(current)
        changed["extractor_sha256"] = "0" * 64
        with self.assertRaisesRegex(verify.VerificationError, "extractor_sha256.*prior witness"):
            verify.check_toolchain_joins(changed, prior)
        changed_run = copy.deepcopy(run)
        changed_run["assets"]["codeql/swift/tools/osx64/extractor.real"] = "0" * 64
        with self.assertRaisesRegex(verify.VerificationError, "extractor hash.*probe witness"):
            verify.check_toolchain_joins(current, prior, changed_run)

    def test_retained_extractor_logs_are_inspected_and_probe_errors_rejected(self):
        witness = verify.read_json(self.attempt / "probe/witness.json")
        log_directory = self.attempt / "probe/log/swift/extractor"
        result = verify.check_extraction_gate(log_directory, witness)
        self.assertTrue(result["ready_for_observation"])
        changed = copy.deepcopy(witness)
        changed["probe_error"] = "injected probe failure"
        with self.assertRaisesRegex(verify.VerificationError, "probe_error"):
            verify.check_extraction_gate(log_directory, changed)
        changed = copy.deepcopy(witness)
        changed["cleanup_error"] = "injected cleanup failure"
        with self.assertRaisesRegex(verify.VerificationError, "cleanup_error"):
            verify.check_extraction_gate(log_directory, changed)

    def test_extractor_log_error_blocks_observation(self):
        witness = verify.read_json(self.attempt / "probe/witness.json")
        with tempfile.TemporaryDirectory() as directory:
            logs = Path(directory)
            (logs / "extractor.log.txt").write_text("ERROR: injected compiler diagnostic\n")
            with self.assertRaisesRegex(verify.VerificationError, "not ready for observation"):
                verify.check_extraction_gate(logs, witness)

    def test_stock_body_row_stays_diagnostic_and_lane_separate(self):
        tables, missing = verify.lane_tables(self.attempt / "stock")
        self.assertNotIn("flow", missing)
        result = verify.evaluate_stock(tables, self.labels, missing)
        self.assertTrue(result["body_endpoint_reached_in_stock_output"])
        self.assertEqual(result["profile"], verify.STOCK_PROFILE)
        self.assertIn("not proof of local-body propagation", result["interpretation"])

    def test_preregistration_cannot_promote_scoring_or_weaken_body_positive(self):
        promoted = copy.deepcopy(self.plan)
        promoted["scored_activation"] = True
        with self.assertRaisesRegex(verify.VerificationError, "promotes scoring"):
            verify.check_scope(promoted)
        weakened = copy.deepcopy(self.plan)
        weakened["expected_patched_sink_labels"].remove("BODY_SINK")
        with self.assertRaisesRegex(verify.VerificationError, "required patched positive"):
            verify.check_scope(weakened)

    def test_manifest_detects_raw_evidence_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            payload = package / "flow.json"
            payload.write_text('{"#select":{"tuples":[]}}\n')
            manifest = package / "manifest.json"
            manifest.write_text(json.dumps({"flow.json": verify.sha256(payload)}))
            verify.check_manifest(package)
            payload.write_text('{"#select":{"tuples":[[15,35,87,"wrong"]]}}\n')
            with self.assertRaisesRegex(verify.VerificationError, "manifest digest mismatch"):
                verify.check_manifest(package)


if __name__ == "__main__":
    unittest.main(verbosity=2)
