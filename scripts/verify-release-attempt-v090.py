#!/usr/bin/env python3
"""Read-only verification of one v0.9.0 completed release-attempt receipt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


RELEASE = "v0.9.0"
ATTEMPTS_PATH = PurePosixPath("reports/releases/v0.9.0/attempts")
LEDGER_PATH = "reports/releases/v0.9.0/ledger-v1.jsonl"
PLAN_PATH = "reports/releases/v0.9.0/plan.json"
POPULATION_PATH = "populations/v0.9.0.json"
CONTRACT_PATH = "reports/releases/v0.9.0/execution-v1/contract.json"
NORMAL_ROOT = PurePosixPath("reports/releases/v0.9.0/normal")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(ValueError):
    """A receipt or retained artifact failed a read-only integrity check."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise VerificationError(f"{label} must be a non-empty repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise VerificationError(f"unsafe {label}: {value!r}")
    return path


def _inside(path: PurePosixPath, parent: PurePosixPath) -> bool:
    return path == parent or parent in path.parents


def _path(root: Path, relative: PurePosixPath, label: str) -> Path:
    """Resolve an existing path under root and reject symlinks in its path."""
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            current.lstat()
        except FileNotFoundError as exc:
            raise VerificationError(f"missing {label}: {relative.as_posix()}") from exc
        if current.is_symlink():
            raise VerificationError(f"symlink in {label}: {relative.as_posix()}")
        if index < len(relative.parts) - 1 and not current.is_dir():
            raise VerificationError(f"non-directory ancestor in {label}: {relative.as_posix()}")
    resolved = current.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise VerificationError(f"{label} escapes verification root: {relative.as_posix()}")
    return current


def _read_json(root: Path, relative: PurePosixPath, label: str) -> tuple[Any, bytes]:
    path = _path(root, relative, label)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read {label} {relative.as_posix()}: {exc}") from exc
    return value, raw


def _digest_ref(root: Path, ref: object, expected_path: str, label: str) -> bytes:
    if not isinstance(ref, dict) or ref.get("path") != expected_path:
        raise VerificationError(f"receipt {label} path differs from the required input")
    digest = ref.get("sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        raise VerificationError(f"receipt has invalid {label} SHA-256")
    relative = _relative(expected_path, f"{label} path")
    data = _path(root, relative, label).read_bytes()
    if _sha(data) != digest:
        raise VerificationError(f"{label} digest differs from completed receipt")
    return data


def _membership_digest(case_ids: list[str]) -> str:
    encoded = (json.dumps(case_ids, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return _sha(encoded)


def _load_contract(root: Path, contract_path: str | Path) -> tuple[dict, bytes, PurePosixPath]:
    if Path(contract_path).is_absolute():
        raise VerificationError("contract_path must be relative to root")
    relative = _relative(Path(contract_path).as_posix(), "contract path")
    value, raw = _read_json(root, relative, "execution contract")
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("release") != RELEASE:
        raise VerificationError("execution contract schema or release identity mismatch")
    return value, raw, relative


def _verify_ledger(root: Path, receipt: dict) -> None:
    ledger, _ = _read_json_lines(root, PurePosixPath(LEDGER_PATH))
    matches = [row for row in ledger if row.get("attempt_id") == receipt.get("attempt_id")]
    if len(matches) != 1 or matches[0] != receipt:
        raise VerificationError("completed receipt does not match exactly one immutable ledger row")


def _read_json_lines(root: Path, relative: PurePosixPath) -> tuple[list[dict], bytes]:
    path = _path(root, relative, "attempt ledger")
    try:
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read attempt ledger {relative.as_posix()}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise VerificationError("attempt ledger contains a non-object row")
    return rows, raw


def _validate_contract_links(root: Path, contract: dict, receipt: dict,
                             contract_raw: bytes) -> tuple[dict, dict]:
    if contract.get("execution_authorized") is not True:
        raise VerificationError("execution contract does not authorize this completed attempt")
    contract_ref = receipt.get("contract")
    if not isinstance(contract_ref, dict) or contract_ref.get("sha256") != _sha(contract_raw):
        raise VerificationError("completed receipt contract digest mismatch")
    if contract_ref.get("path") is None:
        raise VerificationError("completed receipt lacks contract path")

    plan_bytes = _digest_ref(root, receipt.get("parent_plan"), PLAN_PATH, "parent plan")
    population_bytes = _digest_ref(root, receipt.get("population"), POPULATION_PATH, "population")
    plan = json.loads(plan_bytes)
    population = json.loads(population_bytes)
    for ref_name, plan_ref in (("parent_plan", contract.get("parent_plan")),
                               ("population", contract.get("population"))):
        receipt_ref = receipt.get(ref_name)
        if not isinstance(plan_ref, dict) or receipt_ref != plan_ref:
            raise VerificationError(f"completed receipt {ref_name} differs from execution contract")
    if plan.get("release") != RELEASE or population.get("population") != RELEASE:
        raise VerificationError("parent plan or population release identity mismatch")
    fixture_revision = contract.get("fixture_revision")
    if (not isinstance(fixture_revision, str) or receipt.get("fixture_revision") != fixture_revision
            or plan.get("fixture_revision") != fixture_revision
            or population.get("fixture_revision") != fixture_revision):
        raise VerificationError("receipt, contract, plan, and population fixture revisions differ")
    if receipt.get("input_commits") != contract.get("input_commits"):
        raise VerificationError("completed receipt input commits differ from execution contract")
    identities = contract.get("input_identities")
    if not isinstance(identities, dict) or receipt.get("input_identities") != identities:
        raise VerificationError("completed receipt input identities differ from execution contract")
    for identity_path, digest in identities.items():
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise VerificationError(f"invalid contract input identity digest: {identity_path}")
        data = _path(root, _relative(identity_path, "input identity path"), "input identity").read_bytes()
        if _sha(data) != digest:
            raise VerificationError(f"input identity digest mismatch: {identity_path}")
    return plan, population


def _validate_group(plan: dict, contract: dict, receipt: dict,
                    contract_group_id: str | None = None) -> tuple[dict, list[dict]]:
    group_id = receipt.get("group_id")
    if not isinstance(group_id, str) or not group_id:
        raise VerificationError("completed receipt lacks group_id")
    if contract_group_id is not None and group_id != contract_group_id:
        raise VerificationError("receipt group_id differs from requested group")
    contract_groups = [g for g in contract.get("groups", []) if isinstance(g, dict) and g.get("id") == group_id]
    plan_groups = [g for g in plan.get("execution_groups", []) if isinstance(g, dict) and g.get("id") == group_id]
    if len(contract_groups) != 1 or len(plan_groups) != 1:
        raise VerificationError("group must occur exactly once in contract and parent plan")
    group, planned_group = contract_groups[0], plan_groups[0]
    case_ids = group.get("case_ids")
    if (not isinstance(case_ids, list) or not case_ids or
            any(not isinstance(item, str) or not item for item in case_ids) or
            len(case_ids) != len(set(case_ids)) or case_ids != planned_group.get("case_ids")):
        raise VerificationError("contract and parent-plan group membership differs")
    if receipt.get("case_ids") != case_ids:
        raise VerificationError("completed receipt membership differs from contract group")
    if receipt.get("argv") != group.get("argv") or receipt.get("environment") != group.get("environment"):
        raise VerificationError("completed receipt argv or environment differs from exact contract group")
    roots = group.get("output_roots")
    if not isinstance(roots, list) or not roots or receipt.get("output_roots") != roots:
        raise VerificationError("completed receipt output roots differ from contract group")

    reports = group.get("reports")
    plan_report_paths = planned_group.get("reports")
    if (not isinstance(reports, list) or not reports or
            [r.get("path") for r in reports if isinstance(r, dict)] != plan_report_paths):
        raise VerificationError("contract reports differ from exact parent-plan group reports")
    registered = {r.get("report"): r for r in plan.get("reports", []) if isinstance(r, dict)}
    if len(registered) != len(plan.get("reports", [])):
        raise VerificationError("parent plan has duplicate or malformed report declarations")
    for report in reports:
        if not isinstance(report, dict):
            raise VerificationError("contract report declaration must be an object")
        path = report.get("path")
        planned = registered.get(path)
        if planned is None or planned.get("execution_group") != group_id:
            raise VerificationError(f"report is not assigned to this parent-plan group: {path}")
        if report.get("case_ids") != planned.get("case_ids"):
            raise VerificationError(f"report case membership differs from parent plan: {path}")
        membership = planned.get("case_membership")
        ids = planned.get("case_ids")
        if (not isinstance(ids, list) or membership != {
                "count": len(ids), "sha256": _membership_digest(ids)}):
            raise VerificationError(f"parent-plan report membership digest invalid: {path}")
        if report.get("tool") != planned.get("tool") or report.get("tool") != group.get("tool"):
            raise VerificationError(f"report tool differs from group or parent plan: {path}")
        if not isinstance(report.get("tool_version"), str) or not report["tool_version"]:
            raise VerificationError(f"contract lacks exact expected tool_version: {path}")
        if report.get("fixture_revision", receipt.get("fixture_revision")) != receipt.get("fixture_revision"):
            raise VerificationError(f"contract report fixture revision mismatch: {path}")
    if receipt.get("expected_reports") != [r["path"] for r in reports]:
        raise VerificationError("completed receipt expected_reports differs from contract")
    return group, reports


def _verify_mapping(receipt: dict, output_roots: list[str], attempt_id: str) -> list[dict]:
    mapping = receipt.get("execution_root_mapping")
    if not isinstance(mapping, dict):
        raise VerificationError("completed receipt lacks execution_root_mapping")
    if mapping.get("execution_root") != receipt.get("execution_root"):
        raise VerificationError("execution root mapping does not preserve receipt.execution_root")
    if mapping.get("raw_json_bytes_rewritten") is not False:
        raise VerificationError("receipt does not attest that captured raw JSON bytes were left untouched")
    if mapping.get("nested_raw_references_resolve_from_execution_root_namespace") is not True:
        raise VerificationError("receipt does not provide nested raw-reference replay semantics")
    capture_root = (ATTEMPTS_PATH / attempt_id / "capture").as_posix()
    if mapping.get("captured_root") != capture_root:
        raise VerificationError("execution root mapping captured_root differs from attempt capture")
    expected = [{
        "execution_root_relative": root,
        "captured_relative": (PurePosixPath(capture_root) / _relative(root, "output root")).as_posix(),
    } for root in output_roots]
    if mapping.get("mapping") != expected:
        raise VerificationError("execution root mapping differs from exact contract output roots")
    return expected


def _mapped_reference(value: str, execution_root: str,
                      output_roots: list[PurePosixPath]) -> PurePosixPath | None:
    candidate = value
    root_prefix = execution_root.rstrip("/") + "/"
    if candidate.startswith(root_prefix):
        candidate = candidate[len(root_prefix):]
    try:
        relative = _relative(candidate, "nested raw reference")
    except VerificationError:
        return None
    return relative if any(_inside(relative, output_root) for output_root in output_roots) else None


def _verify_nested_raw_references(root: Path, receipt: dict,
                                  inventory: dict[str, dict], attempt_id: str) -> int:
    """Check path-bearing nested JSON refs against the captured root mapping.

    JSON bytes are only read. Every captured file, including raw JSON, is
    independently bound by the receipt inventory; an optional adjacent SHA-256
    on a nested reference is checked against that inventory entry as well.
    """
    execution_root = receipt["execution_root"]
    output_roots = [_relative(path, "output root") for path in receipt["output_roots"]]
    capture_base = ATTEMPTS_PATH / receipt["attempt_id"] / "capture"
    checked = 0

    def visit(value: Any, *, parent: dict | None = None) -> None:
        nonlocal checked
        if isinstance(value, dict):
            sibling_digest = next((value.get(key) for key in ("sha256", "raw_sha256", "digest")
                                   if isinstance(value.get(key), str)), None)
            for key, child in value.items():
                if isinstance(child, str) and (key == "path" or key.endswith("_path") or key.endswith("_file")):
                    mapped = _mapped_reference(child, execution_root, output_roots)
                    if mapped is not None:
                        captured_rel = mapped.as_posix()
                        captured_file = _path(root, capture_base / mapped, "nested captured raw reference")
                        checked += 1
                        if sibling_digest is not None:
                            if SHA256_RE.fullmatch(sibling_digest) is None:
                                raise VerificationError(f"invalid nested raw-reference SHA-256: {child}")
                            item = inventory.get(captured_rel)
                            if item is None or item["sha256"] != sibling_digest:
                                raise VerificationError(f"nested raw-reference digest differs from capture inventory: {child}")
                            if _sha(captured_file.read_bytes()) != sibling_digest:
                                raise VerificationError(f"nested raw-reference bytes differ from declared digest: {child}")
                visit(child, parent=value)
        elif isinstance(value, list):
            for child in value:
                visit(child, parent=parent)

    for relative in inventory:
        if not relative.lower().endswith(".json"):
            continue
        data = _path(root, capture_base / _relative(relative, "captured JSON path"), "captured raw JSON").read_bytes()
        try:
            value = json.loads(data)
        except (UnicodeError, json.JSONDecodeError):
            continue
        visit(value)
    return checked


def _verify_capture(root: Path, receipt: dict, roots: list[str], attempt_id: str) -> dict[str, dict]:
    attempt_rel = ATTEMPTS_PATH / attempt_id
    capture_rel = attempt_rel / "capture"
    capture_path = _path(root, capture_rel, "attempt capture root")
    if not capture_path.is_dir():
        raise VerificationError("attempt capture root is not a directory")
    listed = receipt.get("captured_files")
    if not isinstance(listed, list):
        raise VerificationError("completed receipt lacks captured_files inventory")
    by_path: dict[str, dict] = {}
    for item in listed:
        if not isinstance(item, dict):
            raise VerificationError("captured_files inventory entries must be objects")
        relative = _relative(item.get("path"), "captured file path").as_posix()
        if relative in by_path:
            raise VerificationError(f"duplicate captured file inventory path: {relative}")
        if not any(_inside(PurePosixPath(relative), _relative(output_root, "output root")) for output_root in roots):
            raise VerificationError(f"captured file is outside declared output roots: {relative}")
        digest = item.get("sha256")
        size = item.get("bytes")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None or type(size) is not int or size < 0:
            raise VerificationError(f"invalid captured file digest or byte count: {relative}")
        captured = _path(root, capture_rel / PurePosixPath(relative), "captured file")
        if not captured.is_file():
            raise VerificationError(f"captured inventory member is not a regular file: {relative}")
        data = captured.read_bytes()
        if len(data) != size or _sha(data) != digest:
            raise VerificationError(f"captured raw-file digest or byte count mismatch: {relative}")
        by_path[relative] = item

    actual: set[str] = set()
    for current, dirs, files in __import__("os").walk(capture_path, followlinks=False):
        current_path = Path(current)
        for directory in dirs:
            if (current_path / directory).is_symlink():
                raise VerificationError("symlink directory inside captured output")
        for filename in files:
            file_path = current_path / filename
            if file_path.is_symlink() or not file_path.is_file():
                raise VerificationError("non-regular file inside captured output")
            actual.add(file_path.relative_to(capture_path).as_posix())
    if actual != set(by_path):
        extra = sorted(actual - set(by_path))
        omitted = sorted(set(by_path) - actual)
        raise VerificationError(f"captured file membership differs from receipt inventory: extra={extra}, omitted={omitted}")
    for output_root in roots:
        root_path = _path(root, capture_rel / _relative(output_root, "output root"), "captured output root")
        if not root_path.exists():
            raise VerificationError(f"declared output root missing from captured inventory: {output_root}")
    return by_path


def _verify_reports(root: Path, receipt: dict, reports: list[dict], inventory: dict[str, dict],
                    attempt_id: str, fixture_revision: str) -> list[dict]:
    receipt_reports = receipt.get("reports")
    if not isinstance(receipt_reports, list) or len(receipt_reports) != len(reports):
        raise VerificationError("completed receipt report projections differ in count from contract")
    expected_by_ordinal = {r["ordinal"]: r for r in reports}
    if len(expected_by_ordinal) != len(reports) or set(expected_by_ordinal) != set(range(len(reports))):
        raise VerificationError("contract report ordinals must cover every report exactly once")
    seen: set[int] = set()
    verified: list[dict] = []
    roots = [_relative(path, "output root") for path in receipt["output_roots"]]
    for meta in receipt_reports:
        if not isinstance(meta, dict):
            raise VerificationError("completed receipt report metadata must be an object")
        ordinal = meta.get("ordinal")
        if type(ordinal) is not int or ordinal in seen or ordinal not in expected_by_ordinal:
            raise VerificationError("completed receipt report ordinal is missing, duplicate, or unexpected")
        seen.add(ordinal)
        expected = expected_by_ordinal[ordinal]
        report_dest = _relative(expected.get("path"), "normalized report destination")
        normal_root = NORMAL_ROOT / "attempts"
        expected_staged = normal_root / attempt_id / report_dest.relative_to(NORMAL_ROOT)
        expected_original = PurePosixPath("original-normalized") / report_dest
        source_rel = _relative(expected.get("source_path"), "normalized report source")
        if (meta.get("source_path") != report_dest.as_posix()
                or meta.get("execution_output_path") != source_rel.as_posix()
                or meta.get("staged_path") != expected_staged.as_posix()
                or meta.get("original_normalized") != expected_original.as_posix()
                or meta.get("case_ids") != expected.get("case_ids")):
            raise VerificationError(f"completed receipt report mapping differs from contract: {report_dest}")
        if source_rel.as_posix() not in inventory:
            raise VerificationError(f"normalized execution report absent from captured-file inventory: {source_rel}")
        captured_original = _path(root, ATTEMPTS_PATH / attempt_id / "capture" / source_rel,
                                  "captured normalized report")
        original_rel = ATTEMPTS_PATH / attempt_id / expected_original
        retained_original = _path(root, original_rel, "original normalized report")
        original_bytes = retained_original.read_bytes()
        if original_bytes != captured_original.read_bytes():
            raise VerificationError(f"retained normalized bytes differ from captured execution output: {report_dest}")
        original_digest = meta.get("original_normalized_sha256")
        if not isinstance(original_digest, str) or _sha(original_bytes) != original_digest:
            raise VerificationError(f"original normalized report digest mismatch: {report_dest}")
        try:
            original = json.loads(original_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise VerificationError(f"original normalized report is invalid JSON: {report_dest}: {exc}") from exc
        if not isinstance(original, dict):
            raise VerificationError(f"original normalized report must be an object: {report_dest}")
        if (original.get("fixture_revision") != fixture_revision
                or original.get("tool") != expected.get("tool")
                or original.get("tool_version") != expected.get("tool_version")):
            raise VerificationError(f"normalized report fixture, tool, or tool_version mismatch: {report_dest}")
        results = original.get("results")
        expected_ids = expected.get("case_ids")
        actual_ids = [row.get("case_id") for row in results if isinstance(row, dict)] if isinstance(results, list) else None
        if (actual_ids is None or len(actual_ids) != len(results) or len(actual_ids) != len(set(actual_ids))
                or sorted(actual_ids) != sorted(expected_ids)):
            raise VerificationError(f"normalized report member IDs differ from reviewed partition: {report_dest}")

        projection = copy.deepcopy(original)
        raw_mappings = []
        for original_row, staged_row in zip(results, projection["results"]):
            raw_value = original_row.get("raw_output")
            raw_rel = _relative(raw_value, "normalized raw_output")
            matching_roots = [out_root for out_root in roots if _inside(raw_rel, out_root)]
            if len(matching_roots) != 1:
                raise VerificationError(f"raw_output does not map into exactly one captured output root: {raw_value}")
            raw_key = raw_rel.as_posix()
            if raw_key not in inventory:
                raise VerificationError(f"raw_output is absent from receipt capture inventory: {raw_key}")
            captured_rel = (ATTEMPTS_PATH / attempt_id / "capture" / raw_rel).as_posix()
            staged_row["raw_output"] = captured_rel
            raw_mappings.append({"execution_root_relative": raw_key, "captured_relative": captured_rel,
                                 "sha256": inventory[raw_key]["sha256"]})

        staged_rel = _relative(meta.get("staged_path"), "staged normalized report")
        staged_bytes = _path(root, staged_rel, "staged normalized report").read_bytes()
        if _sha(staged_bytes) != meta.get("staged_sha256"):
            raise VerificationError(f"staged normalized report digest mismatch: {staged_rel}")
        try:
            staged = json.loads(staged_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise VerificationError(f"staged normalized report is invalid JSON: {staged_rel}: {exc}") from exc
        if staged != projection:
            raise VerificationError(f"staged projection changed fields beyond row.raw_output mapping: {staged_rel}")
        verified.append({
            "ordinal": ordinal,
            "path": staged_rel.as_posix(),
            "case_ids": list(expected_ids),
            "tool": expected["tool"],
            "tool_version": expected["tool_version"],
            "raw_output_mappings": raw_mappings,
            "original_normalized_sha256": original_digest,
            "staged_sha256": meta["staged_sha256"],
        })
    return sorted(verified, key=lambda item: item["ordinal"])


def verify_attempt(root: str | Path, receipt_path: str | Path,
                   contract_path: str | Path = CONTRACT_PATH) -> dict:
    """Verify a completed v0.9.0 receipt under an artifact transport root.

    ``root`` is the local checkout/artifact tree holding the receipt, capture,
    reports, contract, plan, and population. The receipt's absolute
    ``execution_root`` is historical provenance and need not exist after
    transport. The returned execution-root mapping is sufficient to map
    preserved nested raw references into their captured trees. This function
    performs no writes.
    """
    requested_root = Path(root)
    if requested_root.is_symlink():
        raise VerificationError("verification root cannot be a symlink")
    root = requested_root.resolve(strict=True)
    if not root.is_dir():
        raise VerificationError("verification root must be a directory")
    receipt_arg = Path(receipt_path)
    if receipt_arg.is_absolute():
        try:
            receipt_rel = PurePosixPath(receipt_arg.resolve(strict=True).relative_to(root).as_posix())
        except (OSError, ValueError) as exc:
            raise VerificationError("receipt_path must be inside root") from exc
    else:
        receipt_rel = _relative(receipt_arg.as_posix(), "receipt path")
    receipt_rel = _relative(receipt_rel.as_posix(), "receipt path")
    receipt, _ = _read_json(root, receipt_rel, "completed receipt")
    if not isinstance(receipt, dict):
        raise VerificationError("completed receipt must be a JSON object")
    attempt_id = receipt.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id:
        raise VerificationError("completed receipt lacks attempt_id")
    expected_receipt = ATTEMPTS_PATH / attempt_id / "completed.json"
    if receipt_rel != expected_receipt:
        raise VerificationError("receipt path does not match its attempt_id")
    if (receipt.get("schema_version") != 1 or receipt.get("release") != RELEASE
            or receipt.get("status") != "completed" or receipt.get("exit_code") != 0
            or receipt.get("timed_out") is not False):
        raise VerificationError("receipt is not a successful completed attempt")
    if receipt.get("capture_errors") or receipt.get("recorder_error"):
        raise VerificationError("completed receipt records capture or recorder errors")
    if not isinstance(receipt.get("execution_root"), str) or not Path(receipt["execution_root"]).is_absolute():
        raise VerificationError("receipt must preserve its original absolute execution_root")

    contract, contract_raw, contract_rel = _load_contract(root, contract_path)
    if receipt.get("contract", {}).get("path") != contract_rel.as_posix():
        raise VerificationError("completed receipt names a different execution contract path")
    plan, _population = _validate_contract_links(root, contract, receipt, contract_raw)
    group, reports = _validate_group(plan, contract, receipt)
    mapping = _verify_mapping(receipt, group["output_roots"], attempt_id)
    inventory = _verify_capture(root, receipt, group["output_roots"], attempt_id)
    started_rel = ATTEMPTS_PATH / attempt_id / "started.json"
    started, _ = _read_json(root, started_rel, "started receipt")
    if not isinstance(started, dict) or started.get("status") != "started":
        raise VerificationError("attempt started receipt is missing or malformed")
    if any(receipt.get(key) != value for key, value in started.items() if key != "status"):
        raise VerificationError("completed receipt changed immutable started-receipt fields")

    for label in ("stdout", "stderr"):
        ref = receipt.get(label)
        if not isinstance(ref, dict) or ref.get("path") != f"{label}.txt":
            raise VerificationError(f"completed receipt lacks {label} capture reference")
        data = _path(root, ATTEMPTS_PATH / attempt_id / _relative(ref["path"], label), label).read_bytes()
        if not isinstance(ref.get("sha256"), str) or _sha(data) != ref["sha256"]:
            raise VerificationError(f"completed receipt {label} digest mismatch")

    verified_reports = _verify_reports(root, receipt, reports, inventory, attempt_id,
                                       receipt["fixture_revision"])
    nested_reference_count = _verify_nested_raw_references(root, receipt, inventory, attempt_id)
    _verify_ledger(root, receipt)
    return {
        "receipt": receipt,
        "attempt_id": attempt_id,
        "group_id": receipt["group_id"],
        "status": receipt["status"],
        "captured_file_count": len(inventory),
        "nested_raw_references_verified": nested_reference_count,
        "execution_root_mapping": {
            "execution_root": receipt["execution_root"],
            "captured_root": receipt["execution_root_mapping"]["captured_root"],
            "mapping": mapping,
            "raw_json_bytes_rewritten": False,
        },
        "reports": verified_reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="artifact transport root")
    parser.add_argument("receipt", help="repository-relative completed.json path")
    parser.add_argument("--contract", default=CONTRACT_PATH, help="contract path relative to root")
    args = parser.parse_args(argv)
    try:
        result = verify_attempt(args.root, args.receipt, args.contract)
    except (VerificationError, OSError, ValueError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: value for key, value in result.items() if key != "receipt"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
