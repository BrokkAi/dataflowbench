#!/usr/bin/env python3
"""Historical-fixture and synthetic tests for v0.15.1 capture/review gates."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
HISTORICAL_CAPTURE = HERE.parent / "bifrost-v0144-01/controls-attempt-01"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capture = load("bifrost_v0151_test_capture", "qualify-bifrost-v0151-01.py")
review = load("bifrost_v0151_test_review", "review-bifrost-v0151-01.py")
binding = load("bifrost_v0151_test_binding", "bind-bifrost-v0151-01.py")


class FrozenCaptureTests(unittest.TestCase):
    def test_only_release_identity_and_external_pack_environment_are_overridden(self):
        controls = capture.controls_for_release()
        self.assertEqual(controls.EXPECTED_VERSION, "0.15.1")
        self.assertEqual(controls.EXPECTED_BUILD_IDENTITY, "90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69")
        self.assertEqual(controls.EXPECTED_BINARY_SHA256,
                         "00b279126297d5e9f7805390799493e915eaf4a2d5940dc3e755138a577a6df9")
        self.assertEqual(controls.PUBLIC_TAG_COMMIT, "04fdd17d2606d13a7a5f13b012bfbe3ad9729d1e")
        self.assertEqual(controls.TIMEOUT_SECONDS, 30)
        self.assertEqual(controls.TOTAL_TIMEOUT_SECONDS, 600)
        environment = controls._environment(cache_root=Path("/cache"), tmpdir=Path("/tmp"))
        self.assertEqual(environment["BIFROST_OPEN_PACKS_DISABLE"], "1")
        self.assertIn("BIFROST_OPEN_PACKS_DISABLE", controls.ENVIRONMENT_ALLOWLIST)


class ReviewGateTests(unittest.TestCase):
    def test_roster_is_44_controls_with_15_unbound_and_15_sanitizer_controls(self):
        controls = review.controls_module()
        expected, vacuous, other = review.expected_controls(controls)
        self.assertEqual(len(expected), 39)
        self.assertEqual(len(vacuous), 15)
        self.assertEqual(sum(name.startswith("sanitizer-") for name in expected), 15)
        self.assertEqual(len(expected) + len(other), 44)
        self.assertEqual(expected["policy-javascript-declared-source-positive-with"], ("javascript", 1))
        self.assertEqual(expected["sanitizer-python-sanitizer-kill-negative-without"], ("python", 1))
        self.assertEqual(set(review.prior_limit_roster()), {
            "policy-javascript-declared-source-positive-with",
            "policy-javascript-declared-sink-positive-with",
            "policy-javascript-declared-sink-negative-with",
        })

    def test_schema6_validation_uses_actual_captured_positive_and_nearmiss_reports(self):
        controls = review.controls_module()
        expected, vacuous, _ = review.expected_controls(controls)
        attempt = HISTORICAL_CAPTURE
        examples = (
            ("policy-python-declared-source-positive-with",
             "e32ea8af50581ec281b0df6b958a74ca143ae8bae59eeba99705ebec7efcaea6",
             "proven-flow"),
            ("policy-python-declared-source-positive-without",
             "b1802e432c653d027ba6ea2cceabc392c210c088ea5ea9b344b0f664e0543a87",
             "unbound-endpoint"),
        )
        reports = {}
        for name, expected_sha256, interpretation in examples:
            report_path = attempt / "reports" / f"{name}.json"
            report_bytes = report_path.read_bytes()
            self.assertEqual(hashlib.sha256(report_bytes).hexdigest(), expected_sha256)
            report = controls._load_report(report_path)
            run = report["runs"][0]
            self.assertEqual(report["schema_version"], 6)
            self.assertFalse(report["diagnostics_truncated"])
            self.assertEqual(report["omitted_diagnostics_lower_bound"], 0)
            self.assertFalse(run["diagnostics_truncated"])
            self.assertNotIn("omitted_diagnostics_lower_bound", run)
            reports[name] = report
            result = review._validate_report(name, "python", expected[name][1], vacuous,
                                             report_path, controls, None)
            self.assertEqual(result["interpretation"], interpretation)

        positive_name = "policy-python-declared-source-positive-with"
        positive_path = attempt / "reports" / f"{positive_name}.json"
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "positive-with-run-counter.json"
            for counter, accepted in ((0, True), (1, False)):
                report = json.loads(json.dumps(reports[positive_name]))
                report["runs"][0]["omitted_diagnostics_lower_bound"] = counter
                report_path.write_text(json.dumps(report), encoding="utf-8")
                if accepted:
                    result = review._validate_report(positive_name, "python", 1, vacuous,
                                                     report_path, controls, None)
                    self.assertEqual(result["interpretation"], "proven-flow")
                else:
                    with self.assertRaisesRegex(review.ReviewError, "diagnostics are truncated"):
                        review._validate_report(positive_name, "python", 1, vacuous,
                                                report_path, controls, None)

    def test_historical_partial_witnesses_replay_through_the_pinned_roster_module(self):
        controls = review.controls_module()
        witnesses, reference = review._prior_partial_witnesses(controls, review.ROOT)
        self.assertEqual(set(witnesses), set(review.prior_limit_roster()))
        self.assertEqual(reference["sha256"], review.PRIOR_REVIEW_SHA256)
        self.assertIn("policy-javascript-declared-source-positive-with", witnesses)
        self.assertIn("policy-javascript-declared-sink-positive-with", witnesses)
        self.assertIn("policy-javascript-declared-sink-negative-with", witnesses)

    def test_three_captured_partials_match_prior_typed_signatures_and_remain_inconclusive(self):
        controls = review.controls_module()
        expected, vacuous, _ = review.expected_controls(controls)
        witnesses, _reference = review._prior_partial_witnesses(controls, review.ROOT)
        attempt = HISTORICAL_CAPTURE
        prior = json.loads(review.PRIOR_REVIEW.read_text(encoding="utf-8"))
        prior_rows = {row["id"]: row for row in prior["controls"]}
        for name in review.prior_limit_roster():
            report_path = attempt / "reports" / f"{name}.json"
            report = controls._load_report(report_path)
            self.assertEqual(review.signature(report), witnesses[name])
            self.assertEqual(review.normalize_signature(prior_rows[name]["current_signature"]),
                             witnesses[name])
            self.assertFalse(prior_rows[name]["clean"])
            result = review._validate_report(name, "javascript", expected[name][1], vacuous,
                                             report_path, controls, witnesses[name])
            self.assertEqual(result["interpretation"], "inconclusive")
            self.assertFalse(result["clean"])
            self.assertEqual(result["findings"], expected[name][1])
            self.assertEqual(result["completion"]["type"], "inconclusive")
            if expected[name][1] == 1:
                self.assertEqual(report["runs"][0]["findings"][0]["proof"]["state"], "proven")
            else:
                self.assertEqual(name, "policy-javascript-declared-sink-negative-with")
                self.assertEqual(report["runs"][0]["findings"], [])

    def test_altered_zero_finding_negative_partial_diagnostic_is_rejected(self):
        controls = review.controls_module()
        expected, vacuous, _ = review.expected_controls(controls)
        witnesses, _reference = review._prior_partial_witnesses(controls, review.ROOT)
        name = "policy-javascript-declared-sink-negative-with"
        source = HISTORICAL_CAPTURE / "reports" / f"{name}.json"
        altered = json.loads(source.read_text(encoding="utf-8"))
        altered["runs"][0]["diagnostics"][0]["family_count"] += 1
        with tempfile.TemporaryDirectory() as directory:
            changed_path = Path(directory) / f"{name}.json"
            changed_path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(review.ReviewError, "new or unproven incompleteness"):
                review._validate_report(name, "javascript", expected[name][1], vacuous,
                                        changed_path, controls, witnesses[name])

    def test_captured_positive_partial_still_requires_a_proven_finding(self):
        controls = review.controls_module()
        expected, vacuous, _ = review.expected_controls(controls)
        witnesses, _reference = review._prior_partial_witnesses(controls, review.ROOT)
        name = "policy-javascript-declared-source-positive-with"
        source = HISTORICAL_CAPTURE / "reports" / f"{name}.json"
        altered = json.loads(source.read_text(encoding="utf-8"))
        altered["runs"][0]["findings"][0]["proof"]["state"] = "unproven"
        with tempfile.TemporaryDirectory() as directory:
            changed_path = Path(directory) / f"{name}.json"
            changed_path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finding is not proven"):
                review._validate_report(name, "javascript", expected[name][1], vacuous,
                                        changed_path, controls, witnesses[name])

    def test_captured_command_state_is_separate_from_inconclusive_report_state(self):
        controls = review.controls_module()
        expected, _vacuous, other = review.expected_controls(controls)
        attempt = HISTORICAL_CAPTURE
        commands = [json.loads(line) for line in (attempt / "commands.jsonl").read_text().splitlines()]
        command_binary = next(row["argv"][0] for row in commands if row["id"] == "identity-version")
        review._validate_commands(attempt, commands, expected, other,
                                  command_binary, controls.EVALUATION_DATE)
        partials = {command["id"]: command for command in commands}
        for name in review.prior_limit_roster():
            report = json.loads((attempt / "reports" / f"{name}.json").read_text())
            self.assertEqual(report["runs"][0]["completion"]["type"], "inconclusive")
            self.assertEqual(partials[name]["exit_code"], 0)
            self.assertEqual(partials[name]["status"], "completed")

        changed = json.loads(json.dumps(commands))
        negative = next(row for row in changed if row["id"] == "policy-javascript-declared-sink-negative-with")
        negative["exit_code"] = 2
        negative["status"] = "failed"
        with self.assertRaisesRegex(review.ReviewError, "did not complete successfully"):
            review._validate_commands(attempt, changed, expected, other,
                                      command_binary, controls.EVALUATION_DATE)

        changed = json.loads(json.dumps(commands))
        source_positive = next(row for row in changed if row["id"] == "policy-javascript-declared-source-positive-with")
        source_positive["argv"][source_positive["argv"].index("never")] = "warning"
        with self.assertRaisesRegex(review.ReviewError, "exact v0.15.1 command vector"):
            review._validate_commands(attempt, changed, expected, other,
                                      command_binary, controls.EVALUATION_DATE)

    def test_only_exact_prior_positive_partials_can_remain_inconclusive(self):
        name = "policy-javascript-declared-source-positive-with"
        report = {
            "completion": "unused",
            "diagnostics": [],
            "runs": [{
                "completion": {"type": "inconclusive", "reasons": ["partial_discovery"],
                               "scope": {"type": "files", "files": ["Config.js"], "truncated": False}},
                "findings": [{"certainty": {"type": "definite"},
                              "proof": {"state": "proven", "reasons": [{"type": "dataflow_witness"}],
                                        "evidence_refs": []},
                              "completeness": {"type": "complete"},
                              "evidence": {"type": "taint"},
                              "primary": {"path": "Config.js"}}],
                "diagnostics": [],
                "work": {"metrics": [
                    {"name": "taint.compiled_source_endpoints", "unit": "count", "value": 1},
                    {"name": "taint.compiled_sink_endpoints", "unit": "count", "value": 1},
                ]},
            }],
        }
        witness = review.signature(report)
        self.assertTrue(review.accepted_exact_partial(name, 1, report, witness))
        self.assertTrue(review.accepted_exact_partial(
            "policy-javascript-declared-sink-positive-with", 1,
            {**report, "runs": [{**report["runs"][0], "completion": {
                "type": "inconclusive", "reasons": ["partial_discovery"],
                "scope": {"type": "files", "files": ["Audit.js"], "truncated": False},
            }}]},
            {**witness, "completion": {"type": "inconclusive", "reasons": ["partial_discovery"],
                                        "scope": {"type": "files", "files": ["Audit.js"], "truncated": False}}}))
        self.assertFalse(review.accepted_exact_partial(
            "policy-javascript-declared-sink-negative-with", 0, report, witness))
        changed = {**witness, "completion": {"type": "inconclusive", "reasons": ["budget_exhausted"]}}
        self.assertFalse(review.accepted_exact_partial(name, 1, report, changed))

    def test_obligation_truncation_is_never_admitted(self):
        self.assertTrue(review.obligations_are_closed({
            "obligations": [], "obligations_truncated": False, "omitted_obligations_lower_bound": 0,
        }))
        self.assertFalse(review.obligations_are_closed({
            "obligations": [], "obligations_truncated": True, "omitted_obligations_lower_bound": 1,
        }))

    def test_artifact_manifest_rejects_unbound_or_changed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            content = attempt / "control.txt"
            content.write_text("captured\n", encoding="utf-8")
            data = content.read_bytes()
            import hashlib
            manifest = {
                "schema": "bifrost-v013-capture-artifacts/v1",
                "files": [{"path": "control.txt", "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()}],
            }
            (attempt / "artifact-hashes.json").write_text(json.dumps(manifest), encoding="utf-8")
            review.verify_artifact_manifest(attempt)
            (attempt / "unbound.txt").write_text("extra\n", encoding="utf-8")
            with self.assertRaisesRegex(review.ReviewError, "exact file inventory"):
                review.verify_artifact_manifest(attempt)
            review.verify_artifact_manifest(attempt, require_closed=False)

    def test_strict_schema5_failure_is_admitted_only_for_reviewed_schema6_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            report = attempt / "reports/policy-java-declared-source-positive-with.json"
            report.parent.mkdir(parents=True)
            report.write_text("{}", encoding="utf-8")
            name = "policy-java-declared-source-positive-with"
            reviewed = {name: {"interpretation": "proven-flow"}}
            expected = {name: ("java", 1)}
            result = review._validate_strict_failures({
                "qualification": "failed",
                "failures": [f"{name}: report is not schema_version 5: {report}"],
            }, reviewed, expected, attempt)
            self.assertEqual(result["failure_count"], 1)
            with self.assertRaisesRegex(review.ReviewError, "unexplained failure"):
                review._validate_strict_failures({
                    "qualification": "failed", "failures": ["catalog control did not run"],
                }, reviewed, expected, attempt)


class GroupBindingTests(unittest.TestCase):
    def setUp(self):
        self.authorization = {
            "schema": "v092-new-bifrost-target-human-authorization/v1",
            "target_version": "0.15.1",
            "source_integration_acquisition_tests_qualification_and_fresh_run_authorized": True,
            "supersedes_preparation_only_hold_for_new_target_qualification_and_benchmark": True,
            "publication_approval_received_for_version": "0.15.1",
            "publication_requires_validated_merged_freeze": True,
            "scope": list(capture.GROUPS),
        }
        self.review = {
            "schema": "v092-bifrost-v0151-control-review/v1",
            "status": "measurement-with-known-limits",
            "execution_eligible": True,
            "full_policy_qualification": False,
            "invocations": 44,
            "unbound_endpoint_controls": 15,
            "sanitizer_controls": 15,
            "native": {"interpretation": "not-evaluated", "clean": False},
            "tool": {
                "version": "0.15.1",
                "build_identity": "90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69",
                "sha256": "00b279126297d5e9f7805390799493e915eaf4a2d5940dc3e755138a577a6df9",
                "public_tag_commit": "04fdd17d2606d13a7a5f13b012bfbe3ad9729d1e",
            },
            "strict_capture": {"status": "failed", "failure_count": 39, "reviewed_failures": []},
        }
        self.references = {name: {"path": name + ".json", "sha256": "a" * 64}
                           for name in ("control_review", "capture", "authorization", "scope_source",
                                        "append_after_ledger", "binding_implementation")}

    def test_binds_only_the_authorized_groups_without_full_support_claim(self):
        result = binding.approved_binding(self.review, list(capture.GROUPS), self.authorization,
                                          self.references)
        self.assertEqual(result["groups"], list(capture.GROUPS))
        self.assertTrue(result["execution_eligible"])
        self.assertFalse(result["full_policy_qualification"])
        self.assertEqual(result["strict_capture"]["status"], "failed")

    def test_rejects_full_support_claim_and_changed_group_scope(self):
        with self.assertRaisesRegex(binding.BindingError, "overstates qualification"):
            binding.approved_binding({**self.review, "full_policy_qualification": True},
                                     list(capture.GROUPS), self.authorization, self.references)
        with self.assertRaisesRegex(binding.BindingError, "scope differs"):
            binding.approved_binding(self.review, list(capture.GROUPS[:-1]),
                                     self.authorization, self.references)


if __name__ == "__main__":
    unittest.main()
