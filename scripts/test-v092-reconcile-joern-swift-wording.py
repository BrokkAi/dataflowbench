#!/usr/bin/env python3
"""Focused tests for the pure Joern Swift wording reconciler."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).resolve().with_name("v092_joern_swift_wording.py")
spec = importlib.util.spec_from_file_location("joern_swift_wording_test_subject", SCRIPT)
assert spec is not None and spec.loader is not None
wording = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wording
spec.loader.exec_module(wording)


IDENTITY = {
    "tool": "joern",
    "tool_version": "4.0.660",
    "tool_build_identity": "joern-cli:4.0.660;engine:fixture;frontend:fixture",
    "adapter_version": "joern-normal-v092",
}
POPULATION = "a" * 64
FIXTURE_REVISION = "sha256:" + "b" * 64
ROLE_CASES = {
    "entrypoint": "dfb-taint-swift-native-entrypoint",
    "persistence": "dfb-taint-swift-native-persistence",
    "propagator": "dfb-taint-swift-native-propagator",
    "sanitizer": "dfb-taint-swift-native-sanitizer",
    "source-sink": "dfb-taint-swift-native-source-sink",
    "summary": "dfb-taint-swift-native-summary",
}


def inputs():
    declines = [f"{prefix}-{polarity}"
                for prefix in ROLE_CASES.values() for polarity in ("negative", "positive")]
    attempts = [f"attempt-{index:03d}" for index in range(96)]
    case_ids = attempts + declines
    identity = dict(IDENTITY)
    cases = {}
    decisions = {}
    scopes = {}
    raw_by_id = {}
    candidate_rows = {}
    frozen_rows = {}

    for case_id in attempts:
        raw_by_id[case_id] = {
            "case_id": case_id, "population_sha256": POPULATION,
            "fixture_revision": FIXTURE_REVISION, "identity": identity,
            "executed": True, "state": "reached", "raw_outcome": "reached",
            "duration_ms": 17, "diagnostics": [],
        }
        row = {
            "case_id": case_id, "outcome": "reached",
            "diagnostics": [wording.AGGREGATE_DIAGNOSTIC],
            "witness_checkpoints": ["source-to-sink"],
            "source_anchors": ["source-anchor"], "sink_anchors": ["sink-anchor"],
            "duration_ms": 17, "peak_memory_mb": None,
        }
        candidate_rows[case_id] = copy.deepcopy(row)
        frozen_rows[case_id] = copy.deepcopy(row)

    for role, prefix in ROLE_CASES.items():
        template = f"dfb-template-native-{role}"
        for polarity in ("negative", "positive"):
            case_id = f"{prefix}-{polarity}"
            historical_decision = {"path": f"old/{case_id}.json", "sha256": "c" * 64}
            case_ref = {"path": f"cases/{case_id}/case.json", "sha256": "d" * 64}
            fixture_refs = [{"path": f"cases/{case_id}/main.swift", "sha256": "e" * 64}]
            published_reason = f"Released declared-scope reason for {role}."
            cases[case_id] = {"model_profile": "tool-native", "template_id": template}
            decisions[case_id] = {
                "schema": "joern-current108-partition-decision/v1",
                "case_id": case_id, "outcome": "unsupported", "reason": published_reason,
                "population_sha256": POPULATION, "fixture_revision": FIXTURE_REVISION,
                "identity": identity, "native_role": role,
                "current_case_sha256": case_ref["sha256"],
                "current_fixture_digests": fixture_refs,
                "proof_scope": {
                    "runtime_executed": False,
                    "fresh_control_and_jvm_witness_required": True,
                    "complete_external_loader_closure_claimed": False,
                    "generic_flow_inability_claimed": False,
                },
                "qualification_limits": {
                    "aggregate_resource_qualification": "unavailable",
                    "full_model_qualification": False, "scored_activation": False,
                },
            }
            scopes[case_id] = {
                "schema": "joern-v092-unsupported-disposition-provenance/v2",
                "case_id": case_id, "status": "declared-not-executed",
                "disposition": "preserved-release-scope-decline",
                "execution": "not-executed", "capability_qualification": "none",
                "population_sha256": POPULATION, "fixture_revision": FIXTURE_REVISION,
                "current_identity": identity, "scored_activation": False,
                "publication_accepted": False,
                "case_row": {"configuration": "joern-current108", "disposition": "unsupported",
                             "phase_sequence": "joern-current108"},
                "case_json": case_ref, "fixtures": fixture_refs,
                "historical_fixture_revision": "sha256:" + "f" * 64,
                "historical_outcome": "unsupported",
                "historical_reason": wording.HISTORICAL_DECLINE_REASON,
                "historical_decision": historical_decision,
                "historical_case_row": {"configuration": "joern-current108",
                                         "disposition": "unsupported",
                                         "decision": historical_decision},
            }
            disposition_hash = "f" * 64
            raw_by_id[case_id] = {
                "case_id": case_id, "population_sha256": POPULATION,
                "fixture_revision": FIXTURE_REVISION, "identity": identity,
                "state": "unsupported", "raw_outcome": "unsupported",
                "duration_ms": 0, "total_elapsed_seconds": 0.0, "executed": False,
                "diagnostics": [wording.HISTORICAL_DECLINE_REASON],
                "commands": [], "native_outputs": [],
                "historical_decision_sha256": historical_decision["sha256"],
                "decision_sha256": disposition_hash,
                "disposition_sha256": disposition_hash,
                "unsupported_provenance": {
                    "path": f"{wording.UNSUPPORTED_PROVENANCE_PREFIX}{case_id}.json",
                    "sha256": disposition_hash, "case_id": case_id,
                },
            }
            candidate_rows[case_id] = {
                "case_id": case_id, "outcome": "unsupported",
                "diagnostics": [wording.AGGREGATE_DIAGNOSTIC,
                                wording.HISTORICAL_DECLINE_REASON],
                "witness_checkpoints": [], "source_anchors": ["source-anchor"],
                "sink_anchors": ["sink-anchor"], "duration_ms": 0,
                "peak_memory_mb": None,
            }
            frozen_rows[case_id] = {
                **candidate_rows[case_id],
                "diagnostics": [wording.AGGREGATE_DIAGNOSTIC, published_reason],
            }

    partitions = (66, 24, 4, 12, 2)
    candidate_reports = []
    frozen_reports = []
    cursor = 0
    for index, count in enumerate(partitions):
        ids = case_ids[cursor:cursor + count]
        cursor += count
        common = {
            "schema_version": 1, **identity, "fixture_revision": FIXTURE_REVISION,
            "cold_or_warm": "cold", "scored_activation": False,
            "aggregate_resource_qualification": "unavailable",
        }
        candidate_reports.append({
            **common, "configuration_hash": "candidate-config",
            "results": [candidate_rows[case_id] for case_id in ids],
        })
        frozen_reports.append({
            **common, "configuration_hash": "historical-config",
            "results": [frozen_rows[case_id] for case_id in ids],
        })
    return {
        "reports": candidate_reports, "frozen_reports": frozen_reports,
        "decisions": decisions, "raw_by_id": raw_by_id, "scopes": scopes,
        "cases": cases, "identity": identity, "population_sha256": POPULATION,
        "fixture_revision": FIXTURE_REVISION, "declines": declines,
    }


def reconcile(data):
    return wording.reconcile_reports(
        data["reports"], data["frozen_reports"], data["decisions"], data["raw_by_id"],
        data["scopes"], data["cases"], data["identity"], data["population_sha256"],
        data["fixture_revision"],
    )


class ReconcileWordingTests(unittest.TestCase):
    def test_reconciles_only_twelve_declared_scope_diagnostics(self):
        data = inputs()
        result = reconcile(data)
        self.assertEqual(result["attempt_count"], 96)
        self.assertEqual(result["decline_count"], 12)
        self.assertEqual(len(result["changes"]), 12)
        self.assertEqual({row["case_id"] for row in result["changes"]}, set(data["declines"]))
        self.assertEqual([len(report["results"]) for report in result["reports"]], [66, 24, 4, 12, 2])
        for original, reconciled in zip(data["reports"], result["reports"]):
            self.assertEqual({k: v for k, v in original.items() if k != "results"},
                             {k: v for k, v in reconciled.items() if k != "results"})
            before = {row["case_id"]: row for row in original["results"]}
            after = {row["case_id"]: row for row in reconciled["results"]}
            for case_id, old_row in before.items():
                self.assertEqual(set(old_row), set(after[case_id]))
                for key in old_row:
                    if key != "diagnostics" or case_id not in data["declines"]:
                        self.assertEqual(old_row[key], after[case_id][key])

    def test_non_wording_semantic_mismatch_fails_closed(self):
        data = inputs()
        data["reports"][0]["results"][0]["outcome"] = "not-reached"
        with self.assertRaisesRegex(wording.ReconciliationError, "attempt report outcome or diagnostics"):
            reconcile(data)

    def test_only_the_exact_twelve_declines_may_be_reconciled(self):
        data = inputs()
        data["decisions"].pop(next(iter(data["decisions"])))
        with self.assertRaisesRegex(wording.ReconciliationError, "exactly the 12 declines"):
            reconcile(data)

    def test_published_reason_must_bind_the_case_native_template_role(self):
        data = inputs()
        case_id = next(iter(data["decisions"]))
        data["decisions"][case_id]["native_role"] = "summary"
        with self.assertRaisesRegex(wording.ReconciliationError, "native role"):
            reconcile(data)

    def test_case_must_be_an_explicit_native_template(self):
        data = inputs()
        case_id = next(iter(data["cases"]))
        data["cases"][case_id]["template_id"] = "dfb-template-native-unknown"
        with self.assertRaisesRegex(wording.ReconciliationError, "not a mapped native template"):
            reconcile(data)

    def test_historical_reason_must_match_raw_v3_provenance(self):
        data = inputs()
        case_id = next(iter(data["scopes"]))
        data["scopes"][case_id]["historical_reason"] = "rewritten old wording"
        with self.assertRaisesRegex(wording.ReconciliationError, "historical decline reason changed"):
            reconcile(data)

    def test_unexecuted_decline_must_have_zero_cost_and_no_artifacts(self):
        data = inputs()
        case_id = next(iter(data["scopes"]))
        data["raw_by_id"][case_id]["duration_ms"] = 1
        with self.assertRaisesRegex(wording.ReconciliationError, "execution cost"):
            reconcile(data)

    def test_unexecuted_decline_rejects_nonzero_total_elapsed_time(self):
        data = inputs()
        case_id = next(iter(data["scopes"]))
        data["raw_by_id"][case_id]["total_elapsed_seconds"] = 0.01
        with self.assertRaisesRegex(wording.ReconciliationError, "execution cost"):
            reconcile(data)

    def test_decline_report_duration_must_be_typed_integer_zero(self):
        data = inputs()
        case_id = next(iter(data["scopes"]))
        row = next(row for row in data["reports"][3]["results"] if row["case_id"] == case_id)
        row["duration_ms"] = 1
        with self.assertRaisesRegex(wording.ReconciliationError, "zero-cost unsupported disposition"):
            reconcile(data)

    def test_published_scope_cannot_be_promoted_to_runtime_qualification(self):
        data = inputs()
        case_id = next(iter(data["decisions"]))
        data["decisions"][case_id]["proof_scope"]["runtime_executed"] = True
        with self.assertRaisesRegex(wording.ReconciliationError, "cannot support a runtime/model"):
            reconcile(data)

    def test_current_population_identity_and_fixture_are_exact(self):
        data = inputs()
        case_id = next(iter(data["scopes"]))
        data["scopes"][case_id]["fixture_revision"] = "sha256:historical-only"
        with self.assertRaisesRegex(wording.ReconciliationError, "exact unexecuted decline"):
            reconcile(data)

    def test_configuration_hash_transition_is_not_rewritten_by_core(self):
        data = inputs()
        before = [report["configuration_hash"] for report in data["reports"]]
        result = reconcile(data)
        self.assertEqual([report["configuration_hash"] for report in result["reports"]], before)
        self.assertTrue(all(report["configuration_hash"] == "candidate-config"
                            for report in result["reports"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
