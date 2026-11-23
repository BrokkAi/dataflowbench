"""Pure reconciliation for the twelve declared Joern Swift scope diagnostics.

This module deliberately performs no I/O and imports no runner, reporter, or
analyzer code. Callers must verify the capture seal, Git blobs, and source
references before passing these detached JSON values.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any


AGGREGATE_DIAGNOSTIC = "AggregateResourceQualificationUnavailable"
SEMANTIC_FIELDS = (
    "outcome", "diagnostics", "witness_checkpoints", "source_anchors", "sink_anchors",
)
REPORT_IDENTITY_FIELDS = (
    "tool", "tool_version", "tool_build_identity", "fixture_revision", "cold_or_warm",
    "adapter_version", "schema_version",
)
NATIVE_TEMPLATE_ROLES = {
    "dfb-template-native-entrypoint": "entrypoint",
    "dfb-template-native-persistence": "persistence",
    "dfb-template-native-propagator": "propagator",
    "dfb-template-native-sanitizer": "sanitizer",
    "dfb-template-native-source-sink": "source-sink",
    "dfb-template-native-summary": "summary",
}
UNSUPPORTED_PROVENANCE_PREFIX = (
    "adapters/joern/swift-common-v2/plan-v092-03/unsupported-dispositions-02/"
)
HISTORICAL_DECLINE_REASON = (
    "Exact pinned shipped distribution lacks native endpoint catalog/resource/loader binding "
    "for this unchanged contract; caller-supplied method mappings are not native qualification."
)


class ReconciliationError(ValueError):
    """Raised when the inputs contain anything beyond the authorized wording mismatch."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


def _rows_by_case(report: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    rows = report.get("results")
    _require(isinstance(rows, list), f"{label} report results must be a list")
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        _require(isinstance(row, dict), f"{label} report contains a non-object row")
        case_id = row.get("case_id")
        _require(isinstance(case_id, str) and case_id, f"{label} report row has no case_id")
        _require(case_id not in mapped, f"{label} report repeats case {case_id}")
        mapped[case_id] = row
    return mapped


def _validate_identity_headers(
    report: dict[str, Any], frozen: dict[str, Any], identity: dict[str, Any],
    fixture_revision: str, label: str,
) -> None:
    for field in REPORT_IDENTITY_FIELDS:
        _require(field in report and field in frozen,
                 f"{label} report is missing identity field {field}")
        _require(report[field] == frozen[field],
                 f"report identity mismatch outside the prevalidated configuration transition: {field}")
    for field, value in identity.items():
        _require(report.get(field) == value and frozen.get(field) == value,
                 f"report identity differs from the bound current identity: {field}")
    _require(report.get("fixture_revision") == fixture_revision,
             f"{label} report fixture revision differs from the bound population")


def _validate_decline(
    case_id: str,
    decision: dict[str, Any],
    raw: dict[str, Any],
    scope: dict[str, Any],
    case: dict[str, Any],
    identity: dict[str, Any],
    population_sha256: str,
    fixture_revision: str,
) -> str:
    """Validate the declared-scope wording source and its captured historical reason."""
    _require(decision.get("schema") == "joern-current108-partition-decision/v1",
             f"published decline has an unexpected schema: {case_id}")
    _require(decision.get("case_id") == case_id and decision.get("outcome") == "unsupported",
             f"published decline is not the exact unsupported case: {case_id}")
    reason = decision.get("reason")
    _require(isinstance(reason, str) and reason.strip(),
             f"published decline lacks its declared-scope reason: {case_id}")
    _require(decision.get("population_sha256") == population_sha256
             and decision.get("fixture_revision") == fixture_revision,
             f"published decline population or current fixture revision differs: {case_id}")
    _require(decision.get("identity") == identity,
             f"published decline current identity differs: {case_id}")
    proof_scope = decision.get("proof_scope")
    qualification_limits = decision.get("qualification_limits")
    _require(isinstance(proof_scope, dict)
             and proof_scope.get("runtime_executed") is False
             and proof_scope.get("fresh_control_and_jvm_witness_required") is True
             and proof_scope.get("complete_external_loader_closure_claimed") is False
             and proof_scope.get("generic_flow_inability_claimed") is False
             and isinstance(qualification_limits, dict)
             and qualification_limits.get("aggregate_resource_qualification") == "unavailable"
             and qualification_limits.get("full_model_qualification") is False
             and qualification_limits.get("scored_activation") is False,
             f"published decline scope cannot support a runtime/model qualification claim: {case_id}")

    template_id = case.get("template_id")
    expected_role = NATIVE_TEMPLATE_ROLES.get(template_id)
    _require(case.get("model_profile") == "tool-native" and expected_role is not None,
             f"declined case is not a mapped native template: {case_id}")
    _require(decision.get("native_role") == expected_role,
             f"published native role does not match the case template: {case_id}")

    case_json_ref = scope.get("case_json")
    _require(isinstance(case_json_ref, dict)
             and case_json_ref.get("sha256") == decision.get("current_case_sha256"),
             f"captured scope and published decline bind different current case JSON: {case_id}")
    fixture_refs = scope.get("fixtures")
    decision_fixture_refs = decision.get("current_fixture_digests")
    _require(isinstance(fixture_refs, list) and isinstance(decision_fixture_refs, list)
             and fixture_refs == decision_fixture_refs,
             f"captured scope and published decline bind different current fixtures: {case_id}")

    _require(scope.get("schema") == "joern-v092-unsupported-disposition-provenance/v2"
             and scope.get("case_id") == case_id
             and scope.get("status") == "declared-not-executed"
             and scope.get("disposition") == "preserved-release-scope-decline"
             and scope.get("execution") == "not-executed"
             and scope.get("capability_qualification") == "none"
             and scope.get("population_sha256") == population_sha256
             and scope.get("fixture_revision") == fixture_revision
             and scope.get("current_identity") == identity
             and scope.get("scored_activation") is False
             and scope.get("publication_accepted") is False,
             f"captured v3 scope is not the exact unexecuted decline: {case_id}")
    _require(scope.get("case_row") == {
        "configuration": "joern-current108", "disposition": "unsupported",
        "phase_sequence": "joern-current108",
    } and isinstance(scope.get("historical_fixture_revision"), str),
        f"captured v3 case row or historical revision provenance changed: {case_id}")
    _require(scope.get("historical_outcome") == "unsupported"
             and scope.get("historical_reason") == HISTORICAL_DECLINE_REASON,
             f"captured v3 historical decline reason changed: {case_id}")

    old_decision = scope.get("historical_decision")
    old_case_row = scope.get("historical_case_row")
    _require(isinstance(old_decision, dict) and isinstance(old_case_row, dict)
             and old_case_row.get("disposition") == "unsupported"
             and old_case_row.get("decision") == old_decision,
             f"captured v3 historical decision binding is malformed: {case_id}")
    _require(raw.get("historical_decision_sha256") == old_decision.get("sha256"),
             f"captured raw record does not bind its historical decline decision: {case_id}")
    _require(raw.get("diagnostics") == [scope["historical_reason"]],
             f"captured raw reason is not the bound historical wording: {case_id}")

    provenance = raw.get("unsupported_provenance")
    expected_provenance_path = f"{UNSUPPORTED_PROVENANCE_PREFIX}{case_id}.json"
    _require(isinstance(provenance, dict)
             and provenance.get("case_id") == case_id
             and provenance.get("path") == expected_provenance_path
             and isinstance(provenance.get("sha256"), str)
             and len(provenance["sha256"]) == 64
             and raw.get("decision_sha256") == provenance.get("sha256")
             and raw.get("disposition_sha256") == provenance.get("sha256"),
             f"captured raw record lost its exact v3 disposition binding: {case_id}")
    _require(raw.get("case_id") == case_id
             and raw.get("population_sha256") == population_sha256
             and raw.get("fixture_revision") == fixture_revision
             and raw.get("identity") == identity
             and raw.get("state") == "unsupported"
             and raw.get("raw_outcome") == "unsupported"
             and raw.get("executed") is False
             and type(raw.get("duration_ms")) is int and raw["duration_ms"] == 0
             and isinstance(raw.get("total_elapsed_seconds"), (int, float))
             and not isinstance(raw.get("total_elapsed_seconds"), bool)
             and math.isfinite(raw["total_elapsed_seconds"])
             and raw["total_elapsed_seconds"] == 0
             and raw.get("commands") == []
             and raw.get("native_outputs") == [],
             f"captured decline has execution cost or incomplete raw binding: {case_id}")
    _require(reason != scope["historical_reason"],
             f"published wording did not correct the captured historical sentence: {case_id}")
    return reason


def reconcile_reports(
    reports: list[dict[str, Any]],
    frozen_reports: list[dict[str, Any]],
    decisions: dict[str, dict[str, Any]],
    raw_by_id: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
    cases: dict[str, dict[str, Any]],
    identity: dict[str, Any],
    population_sha256: str,
    fixture_revision: str,
) -> dict[str, Any]:
    """Return five derived projections with only the twelve approved diagnostics repaired.

    The caller is responsible for verifying every input path and digest, the full
    sealed capture inventory, the release commit, and the already-approved
    configuration-hash transition. This function accepts detached JSON objects
    and makes no filesystem or process calls.
    """
    _require(isinstance(reports, list) and len(reports) == 5
             and isinstance(frozen_reports, list) and len(frozen_reports) == 5,
             "exactly five candidate and five frozen report partitions are required")
    _require(isinstance(identity, dict) and identity
             and isinstance(population_sha256, str) and len(population_sha256) == 64
             and isinstance(fixture_revision, str) and fixture_revision.startswith("sha256:"),
             "current identity, population digest, or fixture revision is malformed")
    _require(isinstance(raw_by_id, dict) and len(raw_by_id) == 108,
             "the captured raw map must contain all 108 cases")

    candidate_maps: list[dict[str, dict[str, Any]]] = []
    frozen_maps: list[dict[str, dict[str, Any]]] = []
    all_candidate_ids: list[str] = []
    all_frozen_ids: list[str] = []
    for index, (candidate, frozen) in enumerate(zip(reports, frozen_reports)):
        _require(isinstance(candidate, dict) and isinstance(frozen, dict),
                 f"report partition {index} must be a JSON object")
        _validate_identity_headers(candidate, frozen, identity, fixture_revision, f"partition {index}")
        candidate_rows = _rows_by_case(candidate, f"candidate partition {index}")
        frozen_rows = _rows_by_case(frozen, f"frozen partition {index}")
        _require(list(candidate_rows) == list(frozen_rows),
                 f"candidate and frozen partition membership/order differs: {index}")
        candidate_maps.append(candidate_rows)
        frozen_maps.append(frozen_rows)
        all_candidate_ids.extend(candidate_rows)
        all_frozen_ids.extend(frozen_rows)

    _require(len(all_candidate_ids) == 108 and len(set(all_candidate_ids)) == 108
             and set(all_candidate_ids) == set(raw_by_id),
             "report partitions and raw records must cover the exact 108 unique cases")
    _require(all_frozen_ids == all_candidate_ids,
             "frozen report partitions do not preserve the candidate population order")

    declined_ids = {case_id for case_id, raw in raw_by_id.items()
                     if isinstance(raw, dict) and raw.get("state") == "unsupported"}
    _require(len(declined_ids) == 12 and len(raw_by_id) - len(declined_ids) == 96,
             "captured population must contain exactly 96 attempts and 12 unexecuted declines")
    _require(set(decisions) == declined_ids and set(scopes) == declined_ids
             and set(cases) == declined_ids,
             "published decisions, captured scopes, and case metadata must cover exactly the 12 declines")

    candidate_row_by_id = {case_id: row for rows in candidate_maps for case_id, row in rows.items()}
    frozen_row_by_id = {case_id: row for rows in frozen_maps for case_id, row in rows.items()}
    reasons: dict[str, str] = {}
    for case_id in sorted(declined_ids):
        reasons[case_id] = _validate_decline(
            case_id, decisions[case_id], raw_by_id[case_id], scopes[case_id], cases[case_id],
            identity, population_sha256, fixture_revision,
        )

    # Attempts remain strictly untouched; every raw attempt must be marked as executed.
    for case_id in set(raw_by_id) - declined_ids:
        raw = raw_by_id[case_id]
        _require(isinstance(raw, dict) and raw.get("case_id") == case_id
                 and raw.get("population_sha256") == population_sha256
                 and raw.get("fixture_revision") == fixture_revision
                 and raw.get("identity") == identity
                 and raw.get("executed") is True and raw.get("state") != "unsupported"
                 and isinstance(raw.get("diagnostics"), list)
                 and all(isinstance(item, str) for item in raw["diagnostics"])
                 and type(raw.get("duration_ms")) is int and raw["duration_ms"] > 0,
                 f"non-decline raw row is missing or not an executed attempt: {case_id}")
        expected_diagnostics = sorted(set(raw.get("diagnostics", []) + [AGGREGATE_DIAGNOSTIC]))
        _require(candidate_row_by_id[case_id].get("outcome") == raw.get("state")
                 and frozen_row_by_id[case_id].get("outcome") == raw.get("state")
                 and candidate_row_by_id[case_id].get("diagnostics") == expected_diagnostics,
                 f"attempt report outcome or diagnostics lost their captured raw binding: {case_id}")

    for case_id in declined_ids:
        candidate_row = candidate_row_by_id[case_id]
        frozen_row = frozen_row_by_id[case_id]
        _require(candidate_row.get("outcome") == "unsupported"
                 and frozen_row.get("outcome") == "unsupported"
                 and type(candidate_row.get("duration_ms")) is int
                 and candidate_row["duration_ms"] == 0
                 and type(frozen_row.get("duration_ms")) is int
                 and frozen_row["duration_ms"] == 0,
                 f"decline report is not the exact zero-cost unsupported disposition: {case_id}")

    derived = deepcopy(reports)
    changes: list[dict[str, Any]] = []
    for report_index, report in enumerate(derived):
        for row in report["results"]:
            case_id = row["case_id"]
            raw = raw_by_id[case_id]
            if case_id in declined_ids:
                expected_old = [AGGREGATE_DIAGNOSTIC, raw["diagnostics"][0]]
                expected_new = [AGGREGATE_DIAGNOSTIC, reasons[case_id]]
                _require(row.get("diagnostics") == expected_old,
                         f"decline projection differs from its captured raw wording: {case_id}")
                row["diagnostics"] = expected_new
                changes.append({
                    "case_id": case_id,
                    "report_partition": report_index,
                    "field": "diagnostics",
                    "old": expected_old,
                    "new": expected_new,
                })

    _require(len(changes) == 12 and {change["case_id"] for change in changes} == declined_ids,
             "reconciliation did not produce exactly twelve decline wording changes")

    # Prove the generated artifact changes no field except those diagnostics.
    for index, (original, reconciled) in enumerate(zip(reports, derived)):
        _require(original.keys() == reconciled.keys(),
                 f"reconciliation changed report-header fields: partition {index}")
        for key in original:
            if key != "results":
                _require(original[key] == reconciled[key],
                         f"reconciliation changed report field {key}: partition {index}")
        original_rows = _rows_by_case(original, f"original partition {index}")
        reconciled_rows = _rows_by_case(reconciled, f"reconciled partition {index}")
        _require(list(original_rows) == list(reconciled_rows),
                 f"reconciliation changed partition membership/order: {index}")
        for case_id, original_row in original_rows.items():
            reconciled_row = reconciled_rows[case_id]
            _require(original_row.keys() == reconciled_row.keys(),
                     f"reconciliation changed row fields: {case_id}")
            for key in original_row:
                if key != "diagnostics" or case_id not in declined_ids:
                    _require(original_row[key] == reconciled_row[key],
                             f"reconciliation changed non-wording row field {key}: {case_id}")

    # Compare every candidate outcome/diagnostic/checkpoint/anchor against the
    # immutable release projection. Any non-wording difference is a hard error.
    original_mismatches = []
    for case_id in all_candidate_ids:
        candidate = candidate_row_by_id[case_id]
        frozen = frozen_row_by_id[case_id]
        for field in SEMANTIC_FIELDS:
            _require(field in candidate and field in frozen,
                     f"semantic comparison lacks {field}: {case_id}")
            if candidate[field] != frozen[field]:
                original_mismatches.append((case_id, field))
        for field in ("outcome", "witness_checkpoints", "source_anchors", "sink_anchors"):
            _require(candidate[field] == frozen[field],
                     f"non-wording semantic mismatch cannot be reconciled: {case_id}:{field}")
        if case_id in declined_ids:
            _require(candidate["diagnostics"] != frozen["diagnostics"],
                     f"expected declared-scope wording mismatch is absent: {case_id}")
            _require(candidate["diagnostics"][0] == frozen["diagnostics"][0] == AGGREGATE_DIAGNOSTIC,
                     f"decline aggregate diagnostic differs from frozen report: {case_id}")
        else:
            _require(candidate["diagnostics"] == frozen["diagnostics"],
                     f"non-decline diagnostic mismatch cannot be reconciled: {case_id}")
        reconciled = next(report["results"] for report in derived
                          if any(row.get("case_id") == case_id for row in report["results"]))
        reconciled_row = next(row for row in reconciled if row["case_id"] == case_id)
        for field in SEMANTIC_FIELDS:
            _require(reconciled_row[field] == frozen_row_by_id[case_id][field],
                     f"reconciled report does not match frozen semantic field {field}: {case_id}")

    _require(len(original_mismatches) == 12
             and set(original_mismatches) == {(case_id, "diagnostics") for case_id in declined_ids},
             "original candidate must have exactly twelve diagnostics-only mismatches")
    return {
        "reports": derived,
        "changes": changes,
        "attempt_count": 96,
        "decline_count": 12,
    }
