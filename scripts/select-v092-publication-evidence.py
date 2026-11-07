#!/usr/bin/env python3
"""Select the exact v0.9.2 report evidence for later validation.

This selector joins retained preflight09 reports for the 63 non-Bifrost groups,
the verified metadata-only Joern108 projection, and a live read-only C5
reconciliation for the Bifrost 0.15.1 series. It does not execute analyzers,
score reports, freeze a release, or approve publication. The retained Joern
stage is evidence for saved reports only; its old runtime authority is never
reused.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, BinaryIO


ROOT = Path(__file__).resolve().parents[1]
PLAN_REF = {
    "path": "reports/releases/v0.9.0/plan.json",
    "sha256": "540846ca9c0a0bd1c257c51f3e64bb6186cd9d3dd47c52106483fb183636efbf",
}
POPULATION_REF = {
    "path": "populations/v0.9.0.json",
    "sha256": "d05be4f2d9effe7b14a2ce5544238364f171e1fb763db2f79ff486526ca7c890",
}
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
PREFIX_130_SHA256 = "79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84"
PREFIX_131_SHA256 = "2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199"
PREFLIGHT_STDOUT_REF = {
    "path": "execution-state/v092/recovery-20261102/joern05-stage-preflight-09/stdout.txt",
    "sha256": "2f10e4e84d7fa4625e327976321954a11dee2f23ba0912f36929441ee85d4c1a",
}
PREFLIGHT_RESULT_REF = {
    "path": "execution-state/v092/recovery-20261102/joern05-stage-preflight-09/result.json",
    "sha256": "31485dfb41494c8b68be72c4919b6237ad4519865857373b760aaa404ec2547b",
}
STAGE_RECEIPT_REF = {
    "path": "execution-state/v092/recovery-20261102/joern05-qualification-09/stage-00.json",
    "sha256": "ed7f7b96ba2a5a8cbd7712f2cb451e2901b3ff25add292a81be202a7ad1c1904",
}
JOERN_OUTPUT_REL = "execution-state/v092/publication-evidence/joern108-metadata-projection-01"
JOERN_MANIFEST_REL = JOERN_OUTPUT_REL + "/projection.json"
JOERN_ATTEMPT_ID = "joern-swift-common108-attempt-05-series-02"
JOERN_GROUP_ID = "joern-swift-common108"
EXPECTED_COMPLETION_REF = {
    "path": "reports/releases/v0.9.2/attempts/" + JOERN_ATTEMPT_ID + "/completed.json",
    "sha256": "421a261d21d8475d59bc22237bfa1ad3930aad18867acd1919a5e7a0b48de676",
}
JOERN_TYPED_OUTCOMES = {"inconclusive": 96, "unsupported": 12}
V0151_WRAPPER_REL = "scripts/bifrost_v0151_benchmark.py"
V0151_TARGET_ID = "bifrost-v0151-01"
V0151_CONTRACT_REL = "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json"
V0151_SERIES_SUMMARY_REL = "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/series-summary.json"
SUMMARY_SCHEMA = "dataflowbench-v0.9.2-publication-evidence-selection/v1"
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class SelectionError(ValueError):
    """Evidence is missing, changed, misbound, or outside the fixed selection."""


@dataclass(frozen=True)
class Counts:
    groups: int
    reports: int
    rows: int
    cases: int
    bifrost_groups: int
    joern_groups: int
    retained_groups: int


RELEASE_COUNTS = Counts(84, 92, 4252, 1108, 20, 1, 63)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SelectionError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(value: object, label: str) -> PurePosixPath:
    _require(isinstance(value, str) and bool(value) and "\\" not in value and "\x00" not in value,
             f"{label} must be a non-empty canonical relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and path.as_posix() == value and
             all(part not in ("", ".", "..") for part in path.parts),
             f"{label} is unsafe")
    return path


def _read_under(root: Path, relative: object, label: str) -> bytes:
    path = _safe_relative(relative, label)
    root = root.resolve(strict=True)
    current = root
    for part in path.parts:
        current = current / part
        _require(not current.is_symlink(), f"symlink in {label}: {current}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise SelectionError(f"{label} is missing or escapes the repository: {path}") from exc
    _require(resolved.is_file(), f"{label} is not a regular file: {path}")
    try:
        return resolved.read_bytes()
    except OSError as exc:
        raise SelectionError(f"cannot read {label}: {path}") from exc


def _read_json(data: bytes, label: str) -> dict:
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectionError(f"{label} is not valid JSON") from exc
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _bound_json(root: Path, reference: dict[str, str], label: str) -> tuple[dict, bytes]:
    data = _read_under(root, reference["path"], label)
    _require(_sha(data) == reference["sha256"], f"{label} SHA-256 differs from the fixed reference")
    return _read_json(data, label), data


def _group_and_report_plan(plan: dict, population: dict, expected: Counts) -> tuple[dict, dict, set[str]]:
    _require(plan.get("schema_version") == 1 and
             plan.get("execution_group_count") == expected.groups and
             plan.get("expected_cases") == expected.cases and
             plan.get("expected_report_partitions") == expected.reports and
             plan.get("expected_report_rows") == expected.rows,
             "frozen parent plan totals differ from the v0.9.2 release matrix")
    _require(plan.get("fixture_revision") == population.get("fixture_revision") and
             plan.get("population") == POPULATION_REF,
             "frozen parent plan does not bind the pinned population and fixture")
    cases = population.get("cases")
    _require(isinstance(cases, list) and len(cases) == expected.cases,
             "pinned population has the wrong number of cases")
    case_ids = [item.get("id") for item in cases if isinstance(item, dict)]
    _require(len(case_ids) == len(cases) and all(isinstance(x, str) and x for x in case_ids) and
             len(set(case_ids)) == expected.cases,
             "pinned population case IDs are malformed or duplicated")
    groups = plan.get("execution_groups")
    reports = plan.get("reports")
    _require(isinstance(groups, list) and isinstance(reports, list) and
             len(groups) == expected.groups and len(reports) == expected.reports,
             "frozen parent plan group or report roster is incomplete")
    group_by_id = {}
    for group in groups:
        _require(isinstance(group, dict) and isinstance(group.get("id"), str) and
                 isinstance(group.get("tool"), str) and isinstance(group.get("reports"), list),
                 "frozen parent plan contains a malformed execution group")
        _require(group["id"] not in group_by_id, "frozen parent plan repeats a group ID")
        group_by_id[group["id"]] = group
    report_by_path = {}
    report_ids = set()
    partition_rows = 0
    plan_case_ids = set()
    group_report_paths: dict[str, list[str]] = {group_id: [] for group_id in group_by_id}
    for report in reports:
        _require(isinstance(report, dict) and isinstance(report.get("id"), str) and
                 isinstance(report.get("report"), str) and
                 isinstance(report.get("execution_group"), str) and
                 isinstance(report.get("case_ids"), list),
                 "frozen parent plan contains a malformed report partition")
        path = report["report"]
        _safe_relative(path, "planned report path")
        _require(path not in report_by_path and report["id"] not in report_ids,
                 "frozen parent plan repeats a report path or ID")
        group_id = report["execution_group"]
        _require(group_id in group_by_id, f"planned report refers to an unknown group: {group_id}")
        expected_ids = report["case_ids"]
        _require(bool(expected_ids) and all(isinstance(x, str) and x for x in expected_ids) and
                 len(expected_ids) == len(set(expected_ids)) and set(expected_ids) <= set(case_ids),
                 f"planned report has invalid case membership: {path}")
        partition_rows += len(expected_ids)
        plan_case_ids.update(expected_ids)
        report_by_path[path] = report
        report_ids.add(report["id"])
        group_report_paths[group_id].append(path)
    _require(partition_rows == expected.rows and plan_case_ids == set(case_ids),
             "frozen report partitions do not cover the exact planned row and case totals")
    for group_id, group in group_by_id.items():
        group_paths = group.get("reports")
        _require(isinstance(group_paths, list) and all(isinstance(path, str) for path in group_paths),
                 f"frozen parent plan group report roster is malformed: {group_id}")
        canonical_group_paths = [_safe_relative(path, "group report path").as_posix()
                                 for path in group_paths]
        _require(len(canonical_group_paths) == len(set(canonical_group_paths)) and
                 set(canonical_group_paths) == set(group_report_paths[group_id]) and
                 all(path in report_by_path and report_by_path[path]["execution_group"] == group_id
                     for path in canonical_group_paths),
                 f"group report roster differs from its exact canonical plan partitions: {group_id}")
        ids = group.get("case_ids")
        _require(isinstance(ids, list) and bool(ids) and len(ids) == len(set(ids)) and
                 all(isinstance(x, str) and x in set(case_ids) for x in ids),
                 f"frozen parent plan has invalid group membership: {group_id}")
        _require(set(ids) == set().union(*(set(report_by_path[p]["case_ids"])
                                         for p in group_report_paths[group_id])),
                 f"planned group and report partition membership differ: {group_id}")
    _require(sum(group.get("tool") == "bifrost" for group in groups) == expected.bifrost_groups and
             sum(group.get("id") == JOERN_GROUP_ID and group.get("tool") == "joern"
                 for group in groups) == expected.joern_groups and
             sum(group.get("tool") != "bifrost" and group.get("id") != JOERN_GROUP_ID
                 for group in groups) == expected.retained_groups,
             "frozen parent plan tool-group partition differs from the release selection")
    _require(JOERN_GROUP_ID in group_by_id and group_by_id[JOERN_GROUP_ID].get("tool") == "joern",
             "frozen parent plan lacks its exact Joern108 group")
    return group_by_id, report_by_path, set(case_ids)


def _report_adapter(plan_report: dict) -> str:
    leaf = PurePosixPath(plan_report["report"]).name
    _require(leaf.endswith(".json"), "planned report filename is malformed")
    return "reports/releases/v0.9.2/normal/" + leaf


def verify_report_payload(
    binding: dict,
    report_bytes: bytes,
    expected_case_ids: list[str],
    label: str,
) -> list[str]:
    """Check one immutable normalized report payload against its planned partition."""
    _require(isinstance(binding, dict), f"{label} binding must be an object")
    expected_sha = binding.get("sha256")
    _require(isinstance(expected_sha, str) and HEX256.fullmatch(expected_sha) and
             _sha(report_bytes) == expected_sha,
             f"{label} report SHA-256 mismatch")
    report = _read_json(report_bytes, label)
    rows = report.get("results")
    _require(isinstance(rows, list) and type(binding.get("rows")) is int and
             len(rows) == binding["rows"] == len(expected_case_ids),
             f"{label} result row count differs from the exact planned partition")
    case_ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    _require(len(case_ids) == len(rows) and case_ids == expected_case_ids and
             len(set(case_ids)) == len(case_ids),
             f"{label} result case IDs differ from the exact ordered plan partition")
    return case_ids


def verify_ledger_stream(
    stream: BinaryIO,
    required_attempt_ids: set[str],
    expected_prefix_130: str = PREFIX_130_SHA256,
    expected_prefix_131: str = PREFIX_131_SHA256,
) -> dict:
    """Hash the complete ledger while retaining only explicitly selected rows."""
    full = hashlib.sha256()
    first130 = hashlib.sha256()
    first131 = hashlib.sha256()
    selected: dict[str, dict] = {}
    line_hashes: dict[str, str] = {}
    seen: set[str] = set()
    byte_count = 0
    line_count = 0
    for raw_line in stream:
        line_count += 1
        byte_count += len(raw_line)
        full.update(raw_line)
        if line_count <= 130:
            first130.update(raw_line)
        if line_count <= 131:
            first131.update(raw_line)
        _require(raw_line.endswith(b"\n") and raw_line.strip(),
                 f"ledger line {line_count} is blank or lacks its LF terminator")
        row = _read_json(raw_line, f"ledger line {line_count}")
        attempt_id = row.get("attempt_id")
        _require(isinstance(attempt_id, str) and attempt_id and attempt_id not in seen,
                 f"ledger line {line_count} has a missing or duplicated attempt ID")
        seen.add(attempt_id)
        if attempt_id in required_attempt_ids:
            selected[attempt_id] = row
            line_hashes[attempt_id] = _sha(raw_line)
    _require(line_count >= 131, "ledger is shorter than the sealed 131-row historical prefix")
    _require(first130.hexdigest() == expected_prefix_130,
             "immutable first-130-row ledger prefix SHA-256 mismatch")
    _require(first131.hexdigest() == expected_prefix_131,
             "immutable first-131-row ledger prefix SHA-256 mismatch")
    missing = required_attempt_ids - set(selected)
    _require(not missing, f"selected attempt IDs are absent from the ledger: {sorted(missing)[:3]}")
    return {
        "path": LEDGER_PATH,
        "line_count": line_count,
        "bytes": byte_count,
        "sha256": full.hexdigest(),
        "prefix_130": first130.hexdigest(),
        "prefix_131": first131.hexdigest(),
        "selected_rows": selected,
        "selected_line_sha256": line_hashes,
    }


def verify_ledger_bytes(
    raw: bytes,
    required_attempt_ids: set[str],
    expected_prefix_130: str = PREFIX_130_SHA256,
    expected_prefix_131: str = PREFIX_131_SHA256,
) -> dict:
    """Bytes adapter for focused tests; production uses streaming file input."""
    return verify_ledger_stream(io.BytesIO(raw), required_attempt_ids,
                                expected_prefix_130, expected_prefix_131)


def _verify_stage_proof(root: Path) -> tuple[dict, dict, dict]:
    result, _ = _bound_json(root, PREFLIGHT_RESULT_REF, "saved preflight09 process result")
    _require(result == {"exit_code": 0, "timed_out": False},
             "saved preflight09 process result is not the exact successful retained run")
    stdout_bytes = _read_under(root, PREFLIGHT_STDOUT_REF["path"], "saved preflight09 stdout")
    _require(_sha(stdout_bytes) == PREFLIGHT_STDOUT_REF["sha256"],
             "saved preflight09 stdout SHA-256 mismatch")
    stdout = _read_json(stdout_bytes, "saved preflight09 stdout")
    _require(stdout.get("schema") == "v092-joern05-qualification/v1" and
             stdout.get("status") == "actual-before-runtime-verified" and
             stdout.get("analyzer_dispatches") == 0 and
             stdout.get("execution_authorized") is False and
             stdout.get("runtime_authority_reusable_across_processes") is False and
             stdout.get("purpose") == "stage-qualification",
             "saved preflight09 is not retained-stage-only proof")
    _require(stdout.get("stage_receipt") == STAGE_RECEIPT_REF,
             "saved preflight09 does not bind the exact pinned stage receipt")
    receipt, receipt_bytes = _bound_json(root, STAGE_RECEIPT_REF, "retained Joern stage receipt")
    _require(receipt.get("status") == "parent-stage-verified" and
             receipt.get("stage_identity_sha256") == stdout.get("stage_identity_sha256") and
             receipt.get("ledger_rows") == 130 and receipt.get("ledger_sha256") == PREFIX_130_SHA256,
             "retained stage receipt no longer verifies its saved 130-row parent")
    for key in ("ledger_ref", "live_ledger_ref"):
        ref = receipt.get(key)
        _require(isinstance(ref, dict) and ref.get("path") == LEDGER_PATH and
                 ref.get("sha256") == PREFIX_130_SHA256,
                 f"retained stage receipt has an invalid {key} binding")
    summary = stdout.get("checker_summary")
    _require(isinstance(summary, dict) and summary.get("status") == "partial-evidence-verified" and
             summary.get("selected_groups") == 83 and summary.get("partitions") == 87 and
             summary.get("rows") == 4144 and summary.get("ledger_rows") == 130 and
             summary.get("known_stale") == 0 and
             summary.get("missing_groups") == [JOERN_GROUP_ID] and
             summary.get("full_release_gate_satisfied") is False and
             summary.get("joern108_operational_completion") is None,
             "saved checker summary differs from the known pre-Joern partial state")
    reports = summary.get("fresh_reports")
    failures = summary.get("failed_attempts")
    _require(isinstance(reports, list) and len(reports) == 87 and
             isinstance(failures, list) and len(failures) == 6,
             "saved checker summary report or failure history is incomplete")
    return stdout, summary, {
        "preflight_stdout": PREFLIGHT_STDOUT_REF,
        "preflight_result": PREFLIGHT_RESULT_REF,
        "stage_receipt": STAGE_RECEIPT_REF,
        "stage_receipt_bytes": len(receipt_bytes),
        "runtime_authority_reused": False,
        "analyzer_dispatches": 0,
        "saved_stage_status": stdout["status"],
    }


def _verify_attempt_report_raw(
    root: Path,
    attempt_id: str,
    report_receipt: dict,
    report_rows: list[dict],
) -> None:
    mappings = report_receipt.get("raw_output_mappings")
    _require(isinstance(mappings, list) and len(mappings) == len(report_rows),
             f"attempt raw-output map does not cover report rows: {attempt_id}")
    expected_prefix = f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/"
    by_path = {}
    for mapping in mappings:
        _require(isinstance(mapping, dict), f"malformed raw-output binding: {attempt_id}")
        captured = _safe_relative(mapping.get("captured_path"), "captured raw-output path").as_posix()
        relative = _safe_relative(mapping.get("execution_relative"), "raw execution-relative path").as_posix()
        digest = mapping.get("sha256")
        size = mapping.get("bytes")
        _require(captured == expected_prefix + relative and
                 isinstance(digest, str) and HEX256.fullmatch(digest) is not None and
                 type(size) is int and size >= 0 and captured not in by_path,
                 f"raw-output mapping is unsafe, duplicated, or malformed: {attempt_id}")
        raw_bytes = _read_under(root, captured, "retained raw output")
        _require(len(raw_bytes) == size and _sha(raw_bytes) == digest,
                 f"retained raw output differs from receipt: {captured}")
        by_path[captured] = mapping
    used = set()
    for row in report_rows:
        path = _safe_relative(row.get("raw_output"), "normalized raw-output reference").as_posix()
        _require(path in by_path and path not in used,
                 f"normalized result row has no unique raw-output binding: {path}")
        used.add(path)
    _require(used == set(by_path), f"attempt raw-output map is not a bijection: {attempt_id}")


def _report_receipt_for(report_rows: list[dict], staged_path: str, staged_sha: str) -> dict:
    matches = [item for item in report_rows if isinstance(item, dict) and
               item.get("staged_path") == staged_path]
    _require(len(matches) == 1, f"completed receipt does not uniquely bind staged report: {staged_path}")
    report = matches[0]
    _require(report.get("staged_sha256") == staged_sha,
             f"completed receipt report SHA differs from selected binding: {staged_path}")
    return report


def _verify_population_binding(row: dict, plan: dict, group_id: str) -> None:
    expected_population = plan.get("population")
    population = row.get("population")
    fixture = plan.get("fixture_revision")
    _require(isinstance(expected_population, dict) and isinstance(population, dict) and
             population.get("path") == expected_population.get("path") and
             population.get("sha256") == expected_population.get("sha256") and
             population.get("fixture_revision") == fixture and
             row.get("fixture_revision") == fixture,
             f"attempt population or fixture binding differs from frozen parent plan: {group_id}")


def _verify_attempt_source_refs(row: dict, group_id: str) -> None:
    _require(isinstance(row.get("contract_sha256"), str) and
             HEX256.fullmatch(row["contract_sha256"]) and
             isinstance(row.get("source_commit"), str) and HEX40.fullmatch(row["source_commit"]) and
             isinstance(row.get("plan_commit"), str) and HEX40.fullmatch(row["plan_commit"]),
             f"attempt lacks exact contract/source/plan identity refs: {group_id}")


def _verify_preflight_reports(
    root: Path,
    stage_summary: dict,
    ledger: dict,
    plan: dict,
    group_by_id: dict,
    report_by_path: dict,
) -> tuple[list[dict], list[dict], list[dict]]:
    selected_by_group: dict[str, dict] = {}
    output_bindings = []
    seen_adapter = set()
    seen_attempt_report = set()
    report_rows_total = 0
    excluded_old_bifrost_groups = set()
    for binding in stage_summary["fresh_reports"]:
        _require(isinstance(binding, dict), "saved preflight contains a malformed report binding")
        adapter = _safe_relative(binding.get("adapter"), "saved adapter report path").as_posix()
        _require(adapter.startswith("reports/releases/v0.9.2/normal/") and
                 adapter.count("/") == 4,
                 f"saved adapter report is outside the normalized report set: {adapter}")
        plan_report = next((item for item in report_by_path.values()
                            if _report_adapter(item) == adapter), None)
        _require(plan_report is not None, f"saved adapter report is absent from the frozen plan: {adapter}")
        group_id = plan_report["execution_group"]
        group = group_by_id[group_id]
        _require(group_id != JOERN_GROUP_ID,
                 f"preflight09 unexpectedly includes the Joern108 group missing from its proof: {group_id}")
        attempt_id = binding.get("attempt_id")
        _require(isinstance(attempt_id, str) and attempt_id and
                 attempt_id not in {JOERN_ATTEMPT_ID},
                 f"saved preflight report has an invalid selected attempt: {adapter}")
        staged = _safe_relative(binding.get("staged_path"), "saved staged report path").as_posix()
        expected_staged = f"reports/releases/v0.9.2/normal/attempts/{attempt_id}/{PurePosixPath(adapter).name}"
        _require(staged == expected_staged and adapter not in seen_adapter and
                 (attempt_id, adapter) not in seen_attempt_report,
                 f"saved report path, membership, or selection is duplicated: {adapter}")
        seen_adapter.add(adapter)
        seen_attempt_report.add((attempt_id, adapter))
        if group.get("tool") == "bifrost":
            excluded_old_bifrost_groups.add(group_id)
            continue
        attempt = ledger["selected_rows"].get(attempt_id)
        _require(isinstance(attempt, dict) and attempt.get("status") == "completed" and
                 attempt.get("group_id") == group_id and
                 attempt.get("contract_sha256") == binding.get("evidence_contract_sha256"),
                 f"selected ledger row differs from preflight report binding: {attempt_id}")
        _verify_population_binding(attempt, plan, group_id)
        _verify_attempt_source_refs(attempt, group_id)
        _require(attempt.get("case_ids") == group.get("case_ids"),
                 f"selected ledger group membership differs from frozen plan: {group_id}")
        receipt_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"
        receipt_bytes = _read_under(root, receipt_path, "selected completed attempt receipt")
        receipt_sha = _sha(receipt_bytes)
        receipt = _read_json(receipt_bytes, f"completed attempt receipt {attempt_id}")
        _require(receipt == attempt and receipt.get("status") == "completed" and
                 receipt.get("attempt_id") == attempt_id,
                 f"completed receipt is not identical to its selected ledger row: {attempt_id}")
        report_sha = binding.get("sha256")
        _require(isinstance(report_sha, str) and HEX256.fullmatch(report_sha) is not None,
                 f"saved report SHA is malformed: {adapter}")
        report_bytes = _read_under(root, staged, "selected normalized report")
        internal = {"attempt_id": attempt_id, "rows": binding.get("rows"), "sha256": report_sha}
        case_ids = verify_report_payload(internal, report_bytes, plan_report["case_ids"], staged)
        report_record = _report_receipt_for(receipt.get("reports", []), staged, report_sha)
        _require(report_record.get("case_ids") == case_ids,
                 f"completed receipt case membership differs from report rows: {staged}")
        _verify_attempt_report_raw(root, attempt_id, report_record, json.loads(report_bytes)["results"])
        report_rows_total += len(case_ids)
        attempt_number = binding.get("attempt_number")
        _require(type(attempt_number) is int and attempt_number > 0,
                 f"saved attempt number is malformed: {attempt_id}")
        output_bindings.append({
            "adapter": adapter, "attempt_id": attempt_id,
            "attempt_number": attempt_number, "sha256": report_sha,
            "rows": len(case_ids), "staged_path": staged,
            "_case_ids": case_ids, "_group_id": group_id,
            "_receipt_sha256": receipt_sha,
        })
        prior = selected_by_group.get(group_id)
        if prior is None:
            selected_by_group[group_id] = {
                "attempt_id": attempt_id,
                "status": "completed",
                "completed_receipt_sha256": receipt_sha,
                "group_id": group_id,
                "completed_receipt": {"path": receipt_path, "sha256": receipt_sha},
                "contract_sha256": attempt.get("contract_sha256"),
                "source_commit": attempt.get("source_commit"),
                "plan_commit": attempt.get("plan_commit"),
                "fixture_revision": attempt.get("fixture_revision"),
            }
        else:
            _require(prior["attempt_id"] == attempt_id and
                     prior["completed_receipt_sha256"] == receipt_sha,
                     f"one group has multiple selected completed attempts: {group_id}")

    expected_bifrost_groups = {group_id for group_id, group in group_by_id.items()
                               if group.get("tool") == "bifrost"}
    _require(report_rows_total == 3028 and excluded_old_bifrost_groups == expected_bifrost_groups and
             len(excluded_old_bifrost_groups) == RELEASE_COUNTS.bifrost_groups,
             "preflight09 retained non-Bifrost report rows differ from the expected 63-group subset")
    _require(len(selected_by_group) == RELEASE_COUNTS.retained_groups,
             "preflight09 did not prove exactly 63 selected non-Bifrost groups")
    expected_non_bifrost = {group_id for group_id, group in group_by_id.items()
                            if group.get("tool") != "bifrost" and group_id != JOERN_GROUP_ID}
    _require(set(selected_by_group) == expected_non_bifrost,
             "preflight09 selected non-Bifrost group set differs from the frozen plan")
    # The saved summary also binds the six failed attempts. Retain compact refs
    # and verify both their original ledger line digest and completed receipt.
    failure_refs = []
    for failure in stage_summary["failed_attempts"]:
        _require(isinstance(failure, dict), "preflight failure history is malformed")
        attempt_id = failure.get("attempt_id")
        row = ledger["selected_rows"].get(attempt_id)
        _require(isinstance(row, dict) and row.get("status") == failure.get("status") and
                 row.get("group_id") == failure.get("group_id") and
                 ledger["selected_line_sha256"].get(attempt_id) == failure.get("ledger_line_sha256"),
                 f"preflight failure reference differs from the immutable ledger row: {attempt_id}")
        receipt_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"
        receipt_bytes = _read_under(root, receipt_path, "historical failed attempt receipt")
        _require(_sha(receipt_bytes) == failure.get("completed_receipt_sha256") and
                 _read_json(receipt_bytes, "historical failed attempt receipt") == row,
                 f"historical failure receipt differs from its ledger row: {attempt_id}")
        failure_refs.append({
            "attempt_id": attempt_id, "group_id": failure["group_id"],
            "status": failure["status"], "ledger_line_sha256": failure["ledger_line_sha256"],
            "completed_receipt": {"path": receipt_path, "sha256": failure["completed_receipt_sha256"]},
        })
    _require(len(failure_refs) == 6, "preflight failure history count changed")
    return output_bindings, list(selected_by_group.values()), failure_refs


def _load_module(path: Path, name: str):
    source_bytes = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SelectionError(f"cannot load selector dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(source_bytes, str(path), "exec"), module.__dict__)
        module.__verified_source_sha256__ = _sha(source_bytes)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _run_bifrost_reconciliation(root: Path, group_by_id: dict) -> tuple[dict, dict, Any, Any, dict]:
    wrapper = _load_module(root / V0151_WRAPPER_REL, "select_v092_bifrost_v0151_wrapper")
    core = wrapper._load_core_module()
    profile = wrapper.load_target_profile(core)
    core.configure_target_profile(profile)
    _require(core.TARGET_ID == V0151_TARGET_ID and core.BIFROST_VERSION == "0.15.1" and
             core.SERIES_LABEL == "series-04" and core.LEDGER_PREFIX_LINES == 131 and
             core.LEDGER_PREFIX_SHA256 == PREFIX_131_SHA256 and
             core.CONTRACT_REL == V0151_CONTRACT_REL,
             "loaded v0.15.1 wrapper profile does not configure the exact fixed series04 target")
    reconciliation = core.reconcile_outputs(root, core.CONTRACT_REL)
    _validate_bifrost_reconciliation(reconciliation, core, group_by_id)
    contract_bytes = _read_under(root, core.CONTRACT_REL, "v0.15.1 target contract")
    _require(_sha(contract_bytes) == reconciliation.get("contract_sha256"),
             "v0.15.1 reconciliation contract SHA differs from the current target contract")
    summary_binding = reconciliation.get("series_summary")
    _require(isinstance(summary_binding, dict) and
             summary_binding.get("path") == V0151_SERIES_SUMMARY_REL,
             "v0.15.1 reconciliation lacks the exact completed series summary")
    summary_bytes = _read_under(root, V0151_SERIES_SUMMARY_REL, "v0.15.1 completed series summary")
    _require(_sha(summary_bytes) == summary_binding.get("sha256"),
             "v0.15.1 completed series summary changed after reconciliation")
    series_summary = _read_json(summary_bytes, "v0.15.1 completed series summary")
    _require(series_summary.get("status") == "completed" and
             series_summary.get("completed_group_count") == RELEASE_COUNTS.bifrost_groups and
             len(series_summary.get("completed_groups", [])) == RELEASE_COUNTS.bifrost_groups,
             "v0.15.1 series summary is not the completed exact 20-group target")
    target_sources = {
        "wrapper": {"path": V0151_WRAPPER_REL,
                    "sha256": _sha(_read_under(root, V0151_WRAPPER_REL, "v0.15.1 wrapper source"))},
        "core": {"path": core.CORE_SOURCE_REL,
                 "sha256": _sha(_read_under(root, core.CORE_SOURCE_REL, "shared C5 core source"))},
        "target_profile": {"path": wrapper.PROFILE_REL,
                           "sha256": _sha(_read_under(root, wrapper.PROFILE_REL,
                                                      "tracked v0.15.1 target profile"))},
    }
    return reconciliation, series_summary, core, wrapper, target_sources


def _validate_bifrost_reconciliation(reconciliation: object, core: Any, group_by_id: dict) -> None:
    _require(isinstance(reconciliation, dict) and
             reconciliation.get("schema") == core.RECONCILIATION_SCHEMA and
             reconciliation.get("status") == "completed" and
             reconciliation.get("target_id") == V0151_TARGET_ID and
             reconciliation.get("contract_path") == V0151_CONTRACT_REL and
             reconciliation.get("output_rows_complete") is True and
             reconciliation.get("completion_state") == "series-summary-verified" and
             reconciliation.get("target_group_count") == RELEASE_COUNTS.bifrost_groups and
             reconciliation.get("completed_group_count") == RELEASE_COUNTS.bifrost_groups and
             reconciliation.get("missing_groups") == [] and
             reconciliation.get("full_policy_qualification") is False,
             "input is not a completed core.reconcile_outputs() v0.15.1 result")
    target_groups = {group_id for group_id, group in group_by_id.items() if group.get("tool") == "bifrost"}
    attempts = reconciliation.get("target_attempts")
    _require(isinstance(attempts, list) and len(attempts) == RELEASE_COUNTS.bifrost_groups,
             "v0.15.1 reconciliation has an incomplete target attempt roster")
    seen_groups = set()
    seen_attempts = set()
    for item in attempts:
        _require(isinstance(item, dict) and item.get("status") == "completed" and
                 isinstance(item.get("group_id"), str) and isinstance(item.get("attempt_id"), str) and
                 isinstance(item.get("completed_receipt"), str),
                 "v0.15.1 reconciliation contains a non-completed or malformed target attempt")
        _require(item["group_id"] in target_groups and item["group_id"] not in seen_groups and
                 item["attempt_id"] not in seen_attempts,
                 "v0.15.1 reconciliation repeats or substitutes a target group/attempt")
        seen_groups.add(item["group_id"])
        seen_attempts.add(item["attempt_id"])
    _require(seen_groups == target_groups,
             "v0.15.1 completed groups differ from the frozen Bifrost roster")
    ledger = reconciliation.get("ledger")
    _require(isinstance(ledger, dict) and ledger.get("path") == LEDGER_PATH and
             ledger.get(f"preserved_131_row_prefix_sha256") == PREFIX_131_SHA256 and
             ledger.get("target_suffix_line_count") == RELEASE_COUNTS.bifrost_groups and
             isinstance(ledger.get("sha256"), str) and HEX256.fullmatch(ledger["sha256"]) and
             type(ledger.get("line_count")) is int and ledger["line_count"] >= 151 and
             type(ledger.get("bytes")) is int and ledger["bytes"] > 0,
             "v0.15.1 reconciliation lacks the current full ledger and immutable series04 boundary")


def _load_bifrost_reports(
    root: Path,
    reconciliation: dict,
    core: Any,
    plan: dict,
    group_by_id: dict,
    report_by_path: dict,
    ledger: dict,
) -> tuple[list[dict], list[dict]]:
    bindings = []
    selected_attempts = []
    for target in reconciliation["target_attempts"]:
        attempt_id = target["attempt_id"]
        group_id = target["group_id"]
        row = ledger["selected_rows"].get(attempt_id)
        _require(isinstance(row, dict) and row.get("status") == "completed" and
                 row.get("group_id") == group_id and row.get("execution_series") == 4,
                 f"v0.15.1 target row is absent or misbound in the real ledger: {attempt_id}")
        _verify_population_binding(row, plan, group_id)
        _verify_attempt_source_refs(row, group_id)
        _require(row.get("case_ids") == group_by_id[group_id].get("case_ids"),
                 f"v0.15.1 ledger group membership differs from frozen plan: {group_id}")
        receipt_path = _safe_relative(target["completed_receipt"], "v0.15.1 completed receipt path").as_posix()
        expected_receipt_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"
        _require(receipt_path == expected_receipt_path,
                 f"v0.15.1 target receipt path differs from its exact attempt namespace: {attempt_id}")
        receipt_bytes = _read_under(root, receipt_path, "v0.15.1 completed attempt receipt")
        receipt_sha = _sha(receipt_bytes)
        receipt = _read_json(receipt_bytes, f"v0.15.1 completed receipt {attempt_id}")
        _require(receipt == row and receipt.get("status") == "completed" and
                 receipt.get("attempt_id") == attempt_id and receipt.get("group_id") == group_id,
                 f"v0.15.1 completed receipt is not identical to its target ledger row: {attempt_id}")
        report_specs = [item for item in report_by_path.values() if item["execution_group"] == group_id]
        _require(len(receipt.get("reports", [])) == len(report_specs),
                 f"v0.15.1 receipt report count differs from the frozen group plan: {group_id}")
        selected_attempts.append({
            "attempt_id": attempt_id, "status": "completed",
            "completed_receipt_sha256": receipt_sha, "group_id": group_id,
            "completed_receipt": {"path": receipt_path, "sha256": receipt_sha},
            "contract_sha256": row.get("contract_sha256"),
            "source_commit": row.get("source_commit"),
            "plan_commit": row.get("plan_commit"),
            "fixture_revision": row.get("fixture_revision"),
        })
        entries_by_plan = []
        for spec in report_specs:
            matches = [entry for entry in receipt["reports"] if isinstance(entry, dict) and
                       entry.get("case_ids") == spec["case_ids"]]
            _require(len(matches) == 1,
                     f"v0.15.1 receipt does not uniquely bind a frozen report partition: {group_id}")
            entries_by_plan.append((spec, matches[0]))
        for plan_report, entry in entries_by_plan:
            staged = _safe_relative(entry.get("staged_path"), "v0.15.1 staged report path").as_posix()
            report_sha = entry.get("staged_sha256")
            adapter = _report_adapter(plan_report)
            expected_stage = (PurePosixPath("reports/releases/v0.9.2/normal/attempts") /
                              attempt_id / PurePosixPath(adapter).name).as_posix()
            _require(staged == expected_stage and isinstance(report_sha, str) and HEX256.fullmatch(report_sha),
                     f"v0.15.1 staged report path or SHA differs from the target contract: {staged}")
            report_bytes = _read_under(root, staged, "v0.15.1 normalized report")
            internal = {"sha256": report_sha, "rows": len(plan_report["case_ids"])}
            case_ids = verify_report_payload(internal, report_bytes, plan_report["case_ids"], staged)
            _require(entry.get("case_ids") == case_ids,
                     f"v0.15.1 receipt report membership differs from normalized rows: {staged}")
            _verify_attempt_report_raw(root, attempt_id, entry, json.loads(report_bytes)["results"])
            bindings.append({
                "adapter": adapter, "attempt_id": attempt_id,
                "attempt_number": core._attempt_number(group_id, attempt_id)[0],
                "sha256": report_sha, "rows": len(case_ids), "staged_path": staged,
                "_case_ids": case_ids, "_group_id": group_id,
                "_receipt_sha256": receipt_sha,
            })
    return bindings, selected_attempts


def _run_joern_projection(root: Path, report_by_path: dict) -> tuple[dict, list[dict], dict]:
    helper = _load_module(root / "scripts/joern_v092_publication_projection.py",
                          "select_v092_joern_publication_projection")
    manifest_path = root / JOERN_MANIFEST_REL
    try:
        if manifest_path.exists() or manifest_path.is_symlink():
            _require(manifest_path.is_file() and not manifest_path.is_symlink(),
                     "existing Joern108 projection manifest is unsafe")
            manifest_bytes = _read_under(root, JOERN_MANIFEST_REL, "Joern108 projection manifest")
            manifest_ref = {"path": JOERN_MANIFEST_REL, "sha256": _sha(manifest_bytes)}
            manifest = helper.verify_existing_projection(root, manifest_ref)
        else:
            manifest = helper.verify_and_project(root, JOERN_OUTPUT_REL)
            manifest_ref = {
                "path": JOERN_MANIFEST_REL,
                "sha256": _sha(_read_under(root, JOERN_MANIFEST_REL, "Joern108 projection manifest")),
            }
    except (helper.ProjectionError, OSError, ValueError) as exc:
        raise SelectionError(f"Joern108 metadata projection refused: {exc}") from exc
    _require(manifest.get("schema") == "v092-joern108-publication-projection/v1" and
             manifest.get("status") == "verified-derived-report-metadata" and
             manifest.get("attempt_id") == JOERN_ATTEMPT_ID and
             manifest.get("group_id") == JOERN_GROUP_ID and
             manifest.get("case_count") == 108 and manifest.get("report_count") == 5 and
             manifest.get("scored_activation") is False and
             manifest.get("configuration_ready") is False and
             manifest.get("full_release_gate_satisfied") is False and
             manifest.get("publication_approved") is False,
             "Joern108 helper returned a result outside its metadata-only boundary")
    outcomes = manifest.get("typed_outcomes")
    _require(isinstance(outcomes, dict) and
             all(outcomes.get(key) == value for key, value in JOERN_TYPED_OUTCOMES.items()) and
             sum(outcomes.values()) == 108,
             "Joern108 typed inconclusive/unsupported outcomes were changed or flattened")
    manifest_bytes = _read_under(root, JOERN_MANIFEST_REL, "Joern108 projection manifest")
    manifest_sha = _sha(manifest_bytes)
    _require(manifest_sha == manifest.get("manifest_sha256"),
             "Joern108 projection manifest file SHA differs from its verified in-memory record")
    output = []
    joern_specs = [item for item in report_by_path.values() if item["execution_group"] == JOERN_GROUP_ID]
    by_case_membership = {tuple(record.get("case_ids", [])): record for record in manifest["reports"]}
    _require(len(joern_specs) == len(manifest["reports"]) == 5,
             "Joern108 projection report set differs from the frozen parent plan")
    for spec in joern_specs:
        record = by_case_membership.get(tuple(spec["case_ids"]))
        _require(isinstance(record, dict),
                 f"Joern108 projected report has no exact frozen partition: {spec['report']}")
        adapter = _report_adapter(spec)
        binding = {
            "adapter": adapter,
            "attempt_id": JOERN_ATTEMPT_ID,
            "attempt_number": 5,
            "rows": record.get("cases"),
            "sha256": record.get("sha256"),
            "staged_path": record.get("path"),
            "original_staged": record.get("staged"),
            "metadata_projection": manifest_ref,
            "_case_ids": record.get("case_ids"),
            "_group_id": JOERN_GROUP_ID,
            "_receipt_sha256": EXPECTED_COMPLETION_REF["sha256"],
        }
        projected_bytes = _read_under(root, record.get("path"), "Joern108 projected normalized report")
        case_ids = verify_report_payload(binding, projected_bytes, spec["case_ids"], record["path"])
        _require(record.get("cases") == len(case_ids) and
                 isinstance(record.get("staged"), dict) and
                 record["staged"].get("path") and record["staged"].get("sha256"),
                 "Joern108 projection report lacks original staged evidence references")
        binding["_case_ids"] = case_ids
        output.append(binding)
    _require(manifest_ref == {"path": JOERN_MANIFEST_REL, "sha256": manifest_sha},
             "Joern108 projection manifest reference changed during verification")
    projection_ref = {"path": JOERN_MANIFEST_REL, "sha256": manifest_sha}
    return manifest, output, {"projection": projection_ref}


def _validate_join(
    plan: dict,
    report_bindings: list[dict],
    selected_attempts: list[dict],
    *,
    counts: Counts = RELEASE_COUNTS,
) -> tuple[int, int, int]:
    group_by_id = {group["id"]: group for group in plan["execution_groups"]}
    report_by_path = {report["report"]: report for report in plan["reports"]}
    expected_adapters = {_report_adapter(item): item for item in report_by_path.values()}
    _require(len(report_bindings) == counts.reports,
             "selected report count differs from exact publication matrix")
    seen_adapters = set()
    cases = set()
    row_total = 0
    reports_by_group: dict[str, list[dict]] = {}
    for binding in report_bindings:
        adapter = binding.get("adapter")
        _require(adapter in expected_adapters and adapter not in seen_adapters,
                 f"selected report is not a unique frozen plan partition: {adapter}")
        seen_adapters.add(adapter)
        expected = expected_adapters[adapter]
        group_id = expected["execution_group"]
        _require(binding.get("_group_id") == group_id,
                 f"selected report attempt group differs from frozen plan: {adapter}")
        case_ids = binding.get("_case_ids")
        _require(isinstance(case_ids, list) and case_ids == expected["case_ids"] and
                 len(case_ids) == binding.get("rows"),
                 f"selected report case membership differs from frozen plan: {adapter}")
        row_total += len(case_ids)
        cases.update(case_ids)
        reports_by_group.setdefault(group_id, []).append(binding)
    _require(seen_adapters == set(expected_adapters),
             "selected report partition set differs from exact parent plan")
    selected_by_group = {}
    selected_ids = set()
    for attempt in selected_attempts:
        _require(isinstance(attempt, dict) and attempt.get("status") == "completed" and
                 isinstance(attempt.get("group_id"), str) and
                 isinstance(attempt.get("attempt_id"), str) and
                 isinstance(attempt.get("completed_receipt_sha256"), str) and
                 HEX256.fullmatch(attempt["completed_receipt_sha256"]),
                 "selected attempt receipt binding is malformed")
        group_id = attempt["group_id"]
        _require(group_id in group_by_id and group_id not in selected_by_group and
                 attempt["attempt_id"] not in selected_ids,
                 f"selected attempt group or ID is duplicated: {group_id}")
        selected_by_group[group_id] = attempt
        selected_ids.add(attempt["attempt_id"])
    _require(set(selected_by_group) == set(group_by_id),
             "selected attempt roster differs from exact frozen group plan")
    for group_id, group in group_by_id.items():
        _require(group_id in reports_by_group and reports_by_group[group_id],
                 f"selected group has no report partitions: {group_id}")
        _require(all(binding.get("attempt_id") == selected_by_group[group_id]["attempt_id"] and
                     binding.get("_receipt_sha256") == selected_by_group[group_id]["completed_receipt_sha256"]
                     for binding in reports_by_group[group_id]),
                 f"selected report partitions do not share the exact completed receipt: {group_id}")
        plan_paths = set(group["reports"])
        selected_paths = {next(report["report"] for report in plan["reports"]
                               if _report_adapter(report) == binding["adapter"])
                          for binding in reports_by_group[group_id]}
        _require(plan_paths == selected_paths,
                 f"selected report partitions do not fully cover their group: {group_id}")
    expected_cases = set().union(*(set(group["case_ids"]) for group in plan["execution_groups"]))
    _require(len(selected_by_group) == counts.groups and row_total == counts.rows and
             len(cases) == counts.cases and cases == expected_cases,
             "joined groups, rows, or unique case membership differ from frozen publication totals")
    _require(sum(group.get("tool") == "bifrost" for group in plan["execution_groups"]) == counts.bifrost_groups and
             sum(group.get("id") == JOERN_GROUP_ID and group.get("tool") == "joern"
                 for group in plan["execution_groups"]) == counts.joern_groups and
             sum(group.get("tool") != "bifrost" and group.get("id") != JOERN_GROUP_ID
                 for group in plan["execution_groups"]) == counts.retained_groups,
             "joined tool population differs from the frozen group classification")
    return len(selected_by_group), len(seen_adapters), row_total


def build_checker_summary(
    plan: dict,
    report_bindings: list[dict],
    selected_attempts: list[dict],
    *,
    retained_stage: dict,
    ledger_binding: dict,
    joern_projection: dict,
    bifrost_reconciliation: dict,
    counts: Counts = RELEASE_COUNTS,
) -> dict:
    """Build the checker-shaped summary after all source evidence was verified."""
    _require(retained_stage.get("runtime_authority_reused") is False and
             retained_stage.get("analyzer_dispatches") == 0,
             "retained-stage proof must not be upgraded into runtime authority")
    _require(joern_projection.get("scored_activation") is False and
             joern_projection.get("configuration_ready") is False and
             joern_projection.get("full_release_gate_satisfied") is False and
             joern_projection.get("publication_approved") is False,
             "Joern metadata projection overstates scoring or publication readiness")
    outcomes = joern_projection.get("typed_outcomes")
    _require(isinstance(outcomes, dict) and
             all(outcomes.get(k) == v for k, v in JOERN_TYPED_OUTCOMES.items()),
             "Joern typed unsupported/inconclusive states must remain present")
    _require(bifrost_reconciliation.get("status") == "completed" and
             bifrost_reconciliation.get("target_id") == V0151_TARGET_ID and
             bifrost_reconciliation.get("full_policy_qualification") is False,
             "Bifrost selection lacks actual completed v0.15.1 core reconciliation")
    groups, reports, rows = _validate_join(plan, report_bindings, selected_attempts, counts=counts)
    # Strip helper-only case/receipt data. Report files and attempt receipts stay
    # reachable through these path+digest references and the canonical ledger.
    public_reports = []
    for binding in report_bindings:
        record = {key: value for key, value in binding.items() if not key.startswith("_")}
        public_reports.append(record)
    public_attempt_keys = (
        "attempt_id", "status", "completed_receipt_sha256", "group_id",
        "completed_receipt", "contract_sha256", "source_commit", "plan_commit",
        "fixture_revision",
    )
    public_attempts = [{key: attempt[key] for key in public_attempt_keys if key in attempt}
                       for attempt in selected_attempts]
    return {
        "schema": SUMMARY_SCHEMA,
        "status": "fresh-evidence-verified",
        "fresh_groups": groups,
        "fresh_partitions": reports,
        "fresh_rows": rows,
        "case_count": counts.cases,
        "carried_partitions": 0,
        "carried_rows": 0,
        "fresh_reports": public_reports,
        "selected_attempts": public_attempts,
        "configuration_hash_validation": {
            "canonical_rust_validate_reports": "required separate final-delivery gate",
            "configuration_ready": False,
        },
        "retained_stage_proof": retained_stage,
        "failure_history": retained_stage.get("failure_history", []),
        "ledger": ledger_binding,
        "frozen_parent_plan": PLAN_REF,
        "joern_metadata_projection": joern_projection["projection_ref"],
        "bifrost_v0151_reconciliation": {
            "method": "scripts/bifrost_v0151_benchmark.py -> core.reconcile_outputs",
            "status": bifrost_reconciliation["status"],
            "target_id": bifrost_reconciliation["target_id"],
            "reconciliation_sha256": bifrost_reconciliation["reconciliation_sha256"],
            "wrapper": bifrost_reconciliation["wrapper"],
            "core": bifrost_reconciliation["core"],
            "target_profile": bifrost_reconciliation["target_profile"],
            "contract": bifrost_reconciliation["contract"],
            "series_summary": bifrost_reconciliation["summary_ref"],
            "full_policy_qualification": False,
        },
        "typed_outcomes": {
            "joern_swift_common108": dict(joern_projection["typed_outcomes"]),
        },
        "scoring_enabled": False,
        "scorecard_generation_allowed": False,
        "full_release_gate_satisfied": False,
        "freeze_created": False,
        "publication_approved": False,
    }


def _verify_joern_attempt_in_ledger(root: Path, ledger: dict, plan: dict,
                                    group_by_id: dict) -> dict:
    row = ledger["selected_rows"].get(JOERN_ATTEMPT_ID)
    _require(isinstance(row, dict) and row.get("status") == "completed" and
             row.get("group_id") == JOERN_GROUP_ID and row.get("exit_code") == 0 and
             row.get("timed_out") is False and row.get("capacity_loss") is None,
             "exact Joern108 completed receipt is absent from the sealed ledger")
    _verify_population_binding(row, plan, JOERN_GROUP_ID)
    _verify_attempt_source_refs(row, JOERN_GROUP_ID)
    _require(row.get("case_ids") == group_by_id[JOERN_GROUP_ID].get("case_ids"),
             "Joern108 ledger group membership differs from the frozen parent plan")
    receipt_bytes = _read_under(root, EXPECTED_COMPLETION_REF["path"], "Joern108 completed receipt")
    _require(_sha(receipt_bytes) == EXPECTED_COMPLETION_REF["sha256"] and
             _read_json(receipt_bytes, "Joern108 completed receipt") == row,
             "Joern108 completed receipt differs from its original ledger row")
    return {
        "attempt_id": JOERN_ATTEMPT_ID, "status": "completed",
        "completed_receipt_sha256": EXPECTED_COMPLETION_REF["sha256"],
        "group_id": JOERN_GROUP_ID,
    }


def select_evidence(root: Path) -> dict:
    """Return a fully verified checker-shaped summary without writing that summary.

    The only possible write is the fixed append-only Joern metadata projection;
    an existing projection is replay-verified read-only. Bifrost qualification
    is read-only and must pass the pinned wrapper and core reconciliation.
    """
    root = Path(root).resolve(strict=True)
    _require(root == ROOT.resolve(strict=True),
             "selector must operate on its owning repository checkout")
    plan, _ = _bound_json(root, PLAN_REF, "frozen v0.9.0 parent plan")
    population, _ = _bound_json(root, POPULATION_REF, "pinned v0.9.0 population")
    group_by_id, report_by_path, population_case_ids = _group_and_report_plan(plan, population, RELEASE_COUNTS)
    preflight_stdout, stage_summary, retained_stage = _verify_stage_proof(root)
    preflight_selected_ids = set()
    adapter_to_plan = {_report_adapter(item): item for item in report_by_path.values()}
    for item in stage_summary["fresh_reports"]:
        if not isinstance(item, dict):
            raise SelectionError("saved preflight report roster is malformed")
        report = adapter_to_plan.get(item.get("adapter"))
        _require(report is not None, "saved preflight report is absent from the frozen plan")
        if group_by_id[report["execution_group"]].get("tool") != "bifrost":
            attempt_id = item.get("attempt_id")
            _require(isinstance(attempt_id, str) and attempt_id,
                     "saved preflight report has no selected attempt ID")
            preflight_selected_ids.add(attempt_id)
    preflight_failed_ids = {item.get("attempt_id") for item in stage_summary["failed_attempts"]}
    joern_projection_script = root / "scripts/joern_v092_publication_projection.py"
    _require(joern_projection_script.is_file() and not joern_projection_script.is_symlink(),
             "Joern108 metadata projection helper is missing or unsafe")
    # Validate profile and target evidence using the fixed wrapper, then call
    # the shared core's read-only reconciliation. This never accepts a
    # diagnostic summary or a caller-supplied eligibility boolean.
    reconciliation, series_summary, core, wrapper, target_sources = _run_bifrost_reconciliation(
        root, group_by_id,
    )
    target_ids = {item["attempt_id"] for item in reconciliation["target_attempts"]}
    required_ids = preflight_selected_ids | preflight_failed_ids | target_ids | {JOERN_ATTEMPT_ID}
    with (root / LEDGER_PATH).open("rb") as stream:
        ledger = verify_ledger_stream(stream, required_ids)
    reconciled_ledger = reconciliation["ledger"]
    _require(ledger["sha256"] == reconciled_ledger["sha256"] and
             ledger["line_count"] == reconciled_ledger["line_count"] and
             ledger["bytes"] == reconciled_ledger["bytes"] and
             ledger["prefix_131"] == reconciled_ledger["preserved_131_row_prefix_sha256"] and
             ledger["line_count"] == 131 + reconciled_ledger["target_suffix_line_count"],
             "current full ledger differs from the exact C5 reconciliation")
    bifrost_receipts, bifrost_attempts = _load_bifrost_reports(
        root, reconciliation, core, plan, group_by_id, report_by_path, ledger,
    )
    joern_attempt = _verify_joern_attempt_in_ledger(root, ledger, plan, group_by_id)
    joern_manifest, joern_reports, joern_meta = _run_joern_projection(root, report_by_path)
    preflight_reports, retained_attempts, failure_refs = _verify_preflight_reports(
        root, stage_summary, ledger, plan, group_by_id, report_by_path,
    )
    all_reports = preflight_reports + joern_reports + bifrost_receipts
    all_attempts = retained_attempts + [joern_attempt] + bifrost_attempts
    _require(set(population_case_ids) == set().union(*(set(item["_case_ids"]) for item in all_reports)),
             "selected report case IDs do not exactly cover the pinned v0.9.0 population")
    ledger_binding = {key: ledger[key] for key in
                      ("path", "line_count", "bytes", "sha256", "prefix_130", "prefix_131")}
    retained_stage["failure_history"] = failure_refs
    retained_stage["selected_non_bifrost_groups"] = RELEASE_COUNTS.retained_groups
    retained_stage["selected_non_bifrost_reports"] = len(preflight_reports)
    retained_stage["selected_non_bifrost_rows"] = sum(item["rows"] for item in preflight_reports)
    retained_stage["saved_partial_summary"] = {
        "status": stage_summary["status"],
        "selected_groups": stage_summary["selected_groups"],
        "partitions": stage_summary["partitions"],
        "rows": stage_summary["rows"],
        "failed_attempts": len(failure_refs),
        "missing_groups": stage_summary["missing_groups"],
    }
    joern_projection_ref = joern_meta["projection"]
    joern_projection = dict(joern_manifest)
    joern_projection["projection_ref"] = joern_projection_ref
    bifrost_summary_ref = reconciliation["series_summary"]
    bifrost_projection = {
        "status": reconciliation["status"],
        "target_id": reconciliation["target_id"],
        "full_policy_qualification": reconciliation["full_policy_qualification"],
        "summary_ref": bifrost_summary_ref,
        "reconciliation_sha256": _sha(json.dumps(reconciliation, sort_keys=True,
                                                   separators=(",", ":")).encode()),
        "contract_sha256": reconciliation["contract_sha256"],
        "contract": {"path": core.CONTRACT_REL,
                     "sha256": reconciliation["contract_sha256"]},
        **target_sources,
        "series_summary_status": series_summary["status"],
    }
    # The reference is carried as a fixed ref; actual SHA is tied to the on-disk file.
    bifrost_projection["summary_ref"] = {
        "path": V0151_SERIES_SUMMARY_REL,
        "sha256": reconciliation["series_summary"]["sha256"],
    }
    result = build_checker_summary(
        plan, all_reports, all_attempts,
        retained_stage=retained_stage,
        ledger_binding=ledger_binding,
        joern_projection=joern_projection,
        bifrost_reconciliation=bifrost_projection,
    )
    _require(result["fresh_groups"] == 84 and result["fresh_partitions"] == 92 and
             result["fresh_rows"] == 4252 and result["case_count"] == 1108,
             "final selector result differs from frozen release totals")
    return result


def select(root: Path, output_path: Path) -> dict:
    root = Path(root).resolve(strict=True)
    _exclusive_output_target(root, output_path)
    result = select_evidence(root)
    _write_exclusive(root, output_path, result)
    return result


def _write_exclusive(root: Path, output_path: Path, result: dict) -> None:
    target = _exclusive_output_target(root, output_path)
    relative = target.relative_to(root).as_posix()
    data = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    try:
        with target.open("xb") as stream:
            stream.write(data)
            stream.flush()
    except OSError as exc:
        raise SelectionError(f"cannot write exclusive selector output: {relative}") from exc


def _exclusive_output_target(root: Path, output_path: Path) -> Path:
    destination = Path(output_path)
    if destination.is_absolute():
        try:
            destination = destination.relative_to(root)
        except ValueError as exc:
            raise SelectionError("selector output must remain inside the repository") from exc
    relative = _safe_relative(destination.as_posix(), "selector output path")
    target = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        _require(not current.is_symlink(), f"symlink in selector output path: {current}")
    _require(not target.exists() and not target.is_symlink(),
             f"selector output is exclusive and already exists: {relative}")
    _require(target.parent.exists() and target.parent.is_dir() and not target.parent.is_symlink(),
             "selector output parent must already exist as a real directory")
    try:
        target.parent.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise SelectionError("selector output parent escapes the repository") from exc
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True,
                        help="new JSON path inside this repository; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        result = select(ROOT, Path(args.output))
    except (SelectionError, OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"v0.9.2 evidence selection refused: {exc}") from exc
    print(json.dumps({
        "status": result["status"],
        "output": args.output,
        "fresh_groups": result["fresh_groups"],
        "fresh_partitions": result["fresh_partitions"],
        "fresh_rows": result["fresh_rows"],
        "case_count": result["case_count"],
        "scorecard_generation_allowed": result["scorecard_generation_allowed"],
        "publication_approved": result["publication_approved"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
