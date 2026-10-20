#!/usr/bin/env python3
"""Recompute and verify the fresh v0.9.2 full-matrix execution evidence.

This checker validates retained execution evidence only.  It never creates a
freeze, authorizes execution, or publishes results.
"""

from __future__ import annotations

import argparse
import collections
import datetime as _datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.9.2"
RELEASE_ROOT = PurePosixPath("reports/releases/v0.9.2")
CONTRACT_PATH = RELEASE_ROOT / "execution-v1/contract.json"
LEDGER_PATH = RELEASE_ROOT / "ledger-v1.jsonl"
ATTEMPTS_ROOT = RELEASE_ROOT / "attempts"
NORMAL_ROOT = RELEASE_ROOT / "normal/attempts"
PREANALYSIS_FAILURE_REVIEW = (
    RELEASE_ROOT / "qualification/bifrost-preanalysis-version-gate-failure-review-01.json"
)
POPULATION_PATH = PurePosixPath("populations/v0.9.0.json")
EXPECTED_GROUPS = 84
EXPECTED_REPORTS = 92
EXPECTED_ROWS = 4252
EXPECTED_CASES = 1108
MAX_ATTEMPTS_PER_GROUP = 2
OUTCOMES = {"reached", "not-reached", "inconclusive", "unsupported", "runner-error"}
FAILED_STATUSES = {"failed", "timed-out", "capacity-lost", "recorder-error"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
RESOURCE_GUARD_ERROR_CODES = {
    "accounting_path_unavailable", "capacity_unavailable", "category_ceiling",
    "copy_io_failed", "copy_write_failed", "file_unavailable", "invalid_budget",
    "invalid_category", "invalid_path", "invalid_phase", "launch_floor", "missing_file",
    "not_regular_file", "source_changed", "source_grew", "source_open_failed",
    "source_plan_changed", "stop_floor", "symlink_accounting_path", "symlink_path",
    "target_exists", "target_open_failed", "target_parent_unavailable", "target_unavailable",
    "unsafe_target_parent", "unsupported_accounting_path",
}
RESOURCE_CAPACITY_ERROR_CODES = {
    "capacity_unavailable", "category_ceiling", "launch_floor", "stop_floor",
}
RESOURCE_CAPACITY_ERROR_METADATA = {
    "allowed_categories": list,
    "accounting_paths": list,
    "actual_projected_bytes": int,
    "actual_signature": list,
    "actual_size_bytes": int,
    "additional_current_bytes": int,
    "category": str,
    "category_limit_bytes": int,
    "capacity_path": str,
    "copied_bytes": int,
    "current_bytes": int,
    "expected_projected_bytes": int,
    "expected_signature": list,
    "expected_size_bytes": int,
    "field": str,
    "free_bytes": int,
    "mode": int,
    "observed_size_bytes": int,
    "partial_bytes": int,
    "path": str,
    "phase": str,
    "post_write_free_bytes": int,
    "protected_reserve_bytes": int,
    "projected_bytes": int,
    "required_free_bytes": int,
    "result_type": str,
    "role": str,
    "source_path": str,
    "stop_floor_bytes": int,
    "target_path": str,
    "total_projected_bytes": int,
    "value": (str, int),
}
D8_VERSION_WITNESS_PATH = "reports/releases/v0.9.2/acquisition/d8-version-witness-01.json"
D8_VERSION_WITNESS_SHA256 = "7aca9c89f40d14448aa11fe508e21bb6dda781595dcb7bdfa449358dea4829bb"
D8_VERSION_LINE = (
    "D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 "
    "from go/r8bot (luci-r8-custom-ci-archive-0-gths))"
)
D8_JAR_SHA256 = "4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294"
SCOPED_C1_SHA256 = "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3"
SCOPED_C1_PLAN_COMMIT = "c5837c0e5b3b809cae3f347a748ef2fd03e3090f"
SCOPED_C1_SOURCE_COMMIT = "4e7b1d9afd6bccf3e932e4222825afb44c436412"
SCOPED_C2_SHA256 = "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422"
SCOPED_C2_PLAN_COMMIT = "a180c302b56f2c18a1fdfbbd1bc14489151fc54e"
SCOPED_C2_SOURCE_COMMIT = "21b76b747b72363aad4bbbc358fc2ae9aee24f1c"
SCOPED_PREFIX_SHA256 = "48e5a5eb985fa3dde72c62dee2cfa55e6c291050c68d7c5b8b4212d970aebd29"
SCOPED_PREFIX_BYTES = 7_738_871
RESOURCE_RECOVERY_MANIFEST_PATH = (
    RELEASE_ROOT / "qualification/resource-recovery-01/manifest.json"
)
RESOURCE_RECOVERY_PREFIX_PATH = (
    RELEASE_ROOT / "qualification/resource-recovery-01/ledger-prefix.jsonl"
)
RESOURCE_C3_ARCHIVE_PATH = RELEASE_ROOT / "acquisition/resource-recovery-contract-03.json"
RESOURCE_C3_CANONICAL_PATH = RELEASE_ROOT / "execution-v3/contract.json"
RESOURCE_C1_SHA256 = SCOPED_C1_SHA256
RESOURCE_C2_SHA256 = SCOPED_C2_SHA256
RESOURCE_C3_SHA256 = "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063"
RESOURCE_C3_PLAN_COMMIT = "216bbaaf6513f334a31111983bf6cd35de6232e2"
RESOURCE_C3_SOURCE_COMMIT = "3b583cd10fd66f27977d17d43fb06afc5006f4c3"
RESOURCE_PREFIX_SHA256 = "31ea08cf5f0fa04fe07697bb8d3683e2a313140e6e12e15fe7e7963a82cdc1f2"
RESOURCE_PREFIX_BYTES = 16_086_045
RESOURCE_PREFIX_LINES = 57
CODEQL_NATIVE_PACKS = {
    "java": "1.11.12",
    "javascript": "2.4.7",
    "python": "1.8.12",
}
CODEQL_CLI_BUILD_SHA = "d7b185e374bfe18c0484dac07a521a810eb9c4fb"
EXPECTED_TOOL_VERSIONS = {
    "bifrost": "bifrost 0.13.1",
    "codeql": "2.27.2",
    "joern": "4.0.660",
    "semgrep": "1.181.0",
    "infer": "v1.3.0",
    "flowdroid": "2.15.1",
    "opentaint": "v0.4.6",
    "pysa": "0.10.0",
}
FLOWDROID_JAR_SHA256 = "51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218"
ANDROID_PLATFORM_SHA256 = "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad"
OPENTAINT_JAR_SHA256 = "2ca93b6c33462bdbc23ceccdc5375e1a900682b33371cd906e5214dc7c48f569"
OPENTAINT_MODELS_SHA256 = "20a96a50fba9ab6f6e98e8562019e5ecbe2a77de7947981eaf6e379f04065329"


class EvidenceError(ValueError):
    """The retained execution evidence is incomplete or inconsistent."""


def _load_executor():
    path = Path(__file__).with_name("execute-release-v092.py")
    spec = importlib.util.spec_from_file_location("execute_release_v092_for_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.9.2 executor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_resource_recovery_module():
    path = Path(__file__).with_name("v092_resource_recovery.py")
    spec = importlib.util.spec_from_file_location("v092_resource_recovery_for_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.9.2 resource recovery parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_scoped_recovery_module():
    path = Path(__file__).with_name("v092_scoped_recovery.py")
    spec = importlib.util.spec_from_file_location("v092_scoped_recovery_for_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.9.2 scoped recovery parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXECUTOR = _load_executor()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _verify_process_ownership(group_id: str, status: str, ownership: object,
                             *, required: bool) -> None:
    """Validate observed PID/start-identity cleanup evidence without claiming containment."""
    if ownership is None:
        _require(not required,
                 f"{group_id}: terminal attempt lacks process ownership evidence")
        return

    required_fields = {
        "schema", "root_pid", "tracked_processes", "signals_sent", "cleanup_status",
        "descendant_containment", "tracking_interval_seconds",
    }
    optional_fields = {"tracking_error", "cleanup_error"}
    _require(isinstance(ownership, dict) and required_fields <= set(ownership) and
             set(ownership) <= required_fields | optional_fields,
             f"{group_id}: process ownership has an unsupported shape")
    _require(ownership.get("schema") == "invocation-process-ownership/v1",
             f"{group_id}: process ownership schema is unknown")
    _require(ownership.get("descendant_containment") == "unproven",
             f"{group_id}: process ownership overstates descendant containment")
    interval = ownership.get("tracking_interval_seconds")
    _require(type(interval) in (int, float) and math.isfinite(interval) and interval == 2.0,
             f"{group_id}: process ownership tracking interval differs from the executor contract")

    root_pid = ownership.get("root_pid")
    _require(root_pid is None or (type(root_pid) is int and root_pid > 0),
             f"{group_id}: process ownership root PID is invalid")
    tracked_processes = ownership.get("tracked_processes")
    _require(isinstance(tracked_processes, list),
             f"{group_id}: process ownership tracked_processes must be a list")
    tracked: dict[int, str] = {}
    for index, item in enumerate(tracked_processes):
        _require(isinstance(item, dict) and set(item) == {"pid", "start_identity"},
                 f"{group_id}: tracked process {index} has an unsupported shape")
        pid = item.get("pid")
        identity = item.get("start_identity")
        _require(type(pid) is int and pid > 0 and isinstance(identity, str) and bool(identity.strip()),
                 f"{group_id}: tracked process {index} has an invalid PID or start identity")
        _require(pid not in tracked,
                 f"{group_id}: process ownership contains a duplicate tracked PID")
        tracked[pid] = identity

    signals_sent = ownership.get("signals_sent")
    _require(isinstance(signals_sent, list),
             f"{group_id}: process ownership signals_sent must be a list")
    for index, item in enumerate(signals_sent):
        _require(isinstance(item, dict) and set(item) == {"pid", "start_identity", "signal"},
                 f"{group_id}: process signal {index} has an unsupported shape")
        pid = item.get("pid")
        identity = item.get("start_identity")
        _require(type(pid) is int and pid > 0 and pid in tracked and tracked[pid] == identity,
                 f"{group_id}: process signal does not bind an exact tracked PID identity")
        signal_name = item.get("signal")
        _require(isinstance(signal_name, str) and signal_name in {"SIGTERM", "SIGKILL"},
                 f"{group_id}: process signal is unsupported")

    cleanup_status = ownership.get("cleanup_status")
    _require(isinstance(cleanup_status, str) and
             cleanup_status in {"not-started", "tracked-processes-stopped", "uncertain"},
             f"{group_id}: process ownership cleanup status is unknown")
    errors = []
    for field in optional_fields:
        if field in ownership:
            value = ownership[field]
            _require(isinstance(value, str) and bool(value.strip()),
                     f"{group_id}: process ownership {field} must be non-empty text")
            errors.append(value)

    if cleanup_status == "not-started":
        _require(status == "capacity-lost" and root_pid is None and not tracked and
                 not signals_sent and not errors,
                 f"{group_id}: not-started ownership is valid only for capacity loss before process launch")
        return
    if cleanup_status == "tracked-processes-stopped":
        _require(root_pid is not None and tracked.get(root_pid) is not None and not errors,
                 f"{group_id}: stopped process ownership lacks its tracked root or contains errors")
    else:
        _require(root_pid is not None and bool(errors),
                 f"{group_id}: uncertain process ownership lacks a launched root or cleanup error")

    if status == "completed":
        _require(cleanup_status == "tracked-processes-stopped" and root_pid is not None and
                 tracked.get(root_pid) is not None and not errors,
                 f"{group_id}: completed attempt lacks confirmed tracked-process cleanup")


def _verify_resource_guard_error(group_id: str, value: object, *, capacity_loss: bool) -> dict:
    """Validate a typed C4 disk-guard failure receipt."""
    _require(isinstance(value, dict) and {"code", "message"} <= set(value),
             f"{group_id}: C4 capacity loss lacks its typed guard code and message")
    code = value.get("code")
    message = value.get("message")
    allowed_codes = RESOURCE_CAPACITY_ERROR_CODES if capacity_loss else RESOURCE_GUARD_ERROR_CODES
    _require(isinstance(code, str) and code in allowed_codes and
             isinstance(message, str) and bool(message.strip()),
             f"{group_id}: C4 disk-guard error has an unknown code or empty message")
    _require(set(value) <= {"code", "message", *RESOURCE_CAPACITY_ERROR_METADATA},
             f"{group_id}: C4 disk-guard error contains unknown metadata")
    for key, item in value.items():
        if key in ("code", "message"):
            continue
        expected_type = RESOURCE_CAPACITY_ERROR_METADATA[key]
        if key == "value":
            valid = ((isinstance(item, str) or type(item) is int))
        elif key in {"expected_signature", "actual_signature"}:
            valid = (isinstance(item, list) and len(item) == 5 and
                     all(type(part) is int for part in item) and all(part >= 0 for part in item[:3]))
        elif expected_type is list:
            valid = isinstance(item, list) and all(isinstance(path, str) for path in item)
        else:
            valid = type(item) is expected_type and (expected_type is not str or bool(item.strip()))
        _require(valid, f"{group_id}: C4 disk-guard metadata {key} has the wrong type")

    required_metadata = {
        "launch_floor": {"phase", "free_bytes", "required_free_bytes", "projected_bytes", "capacity_path"},
        "stop_floor": {"phase", "free_bytes", "projected_bytes", "post_write_free_bytes",
                        "required_free_bytes", "protected_reserve_bytes", "capacity_path"},
        "category_ceiling": {"category", "current_bytes", "projected_bytes", "total_projected_bytes",
                             "category_limit_bytes", "accounting_paths"},
        "capacity_unavailable": {"capacity_path"},
        "source_plan_changed": {"expected_projected_bytes", "actual_projected_bytes"},
    }
    _require(required_metadata.get(code, set()) <= set(value),
             f"{group_id}: C4 disk-guard code lacks its required measurements")
    if "phase" in value:
        _require(value["phase"] in {"launch", "active"},
                 f"{group_id}: C4 disk-guard phase is invalid")
    for key, item in value.items():
        if key in RESOURCE_CAPACITY_ERROR_METADATA and key not in {"mode", "value", "post_write_free_bytes"} and type(item) is int:
            _require(item >= 0, f"{group_id}: C4 disk-guard measurement {key} is negative")
    if "post_write_free_bytes" in value:
        _require(code == "stop_floor",
                 f"{group_id}: negative post-write capacity is valid only for a stop-floor refusal")
    if code == "stop_floor":
        _require(value["post_write_free_bytes"] == value["free_bytes"] - value["projected_bytes"] and
                 value["post_write_free_bytes"] < value["required_free_bytes"],
                 f"{group_id}: C4 stop-floor projection is arithmetically inconsistent")
    elif code == "launch_floor":
        _require(value["free_bytes"] < value["required_free_bytes"],
                 f"{group_id}: C4 launch-floor measurement does not establish a refusal")
    elif code == "category_ceiling":
        _require(value["total_projected_bytes"] == value["current_bytes"] + value["projected_bytes"] and
                 value["total_projected_bytes"] > value["category_limit_bytes"] and
                 value.get("additional_current_bytes", 0) <= value["current_bytes"],
                 f"{group_id}: C4 category-ceiling projection is arithmetically inconsistent")
    return value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path, description: str) -> tuple[object, bytes]:
    _require(path.is_file() and not path.is_symlink(), f"missing or symlinked {description}: {path}")
    try:
        raw = path.read_bytes()
        return json.loads(raw), raw
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {description} {path}: {exc}") from exc


def _read_ledger_with_hashes(path: Path) -> list[tuple[dict, str]]:
    _require(path.is_file() and not path.is_symlink(), f"missing or symlinked execution ledger: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EvidenceError(f"cannot read execution ledger {path}: {exc}") from exc
    _require(bool(raw) and raw.endswith(b"\n"), "execution ledger must be non-empty and newline-terminated")
    rows = []
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        _require(line.endswith(b"\n") and line != b"\n" and not line.endswith(b"\r\n"),
                 f"execution ledger line {index} is blank or not canonical newline-terminated JSON")
        try:
            value = json.loads(line[:-1])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceError(f"execution ledger line {index} is invalid JSON") from exc
        _require(isinstance(value, dict), f"execution ledger line {index} must be an object")
        rows.append((value, _sha(line)))
    return rows


def _select_attempts(plan: dict, contract_sha256: str,
                     ledger_rows: list[tuple[dict, str]],
                     prior_failed_contracts: dict | None = None
                     ) -> tuple[str, dict[str, tuple[dict, str, int]], list[tuple]]:
    """Select current-contract completions and explicitly bound earlier failures.

    A successor contract may inherit only its single registered, pre-analysis
    Bifrost C version-gate failure. That row remains an attempt in the same
    series and consumes the group's existing retry allowance.
    """
    planned = plan.get("groups")
    _require(isinstance(planned, list), "execution plan groups are malformed")
    groups = {item.get("id"): item for item in planned if isinstance(item, dict)}
    _require(len(groups) == len(planned) == EXPECTED_GROUPS,
             "execution plan must contain exactly 84 unique groups")
    _require(0 < len(ledger_rows) <= EXPECTED_GROUPS * MAX_ATTEMPTS_PER_GROUP,
             "execution ledger has no attempts or exceeds the two-attempt bound")
    series = plan.get("execution_series")
    source_commit = plan.get("source_commit")
    _require(type(series) is int and series > 0 and isinstance(source_commit, str) and
             COMMIT.fullmatch(source_commit) is not None,
             "execution plan lacks an exact source commit or positive series")

    if prior_failed_contracts is None:
        prior_failed_contracts = {}
    _require(isinstance(prior_failed_contracts, dict) and len(prior_failed_contracts) <= 1,
             "at most one exact prior failed contract may be continued")
    _require(not prior_failed_contracts or series == 1,
             "a prior failed contract may only continue execution series 1")

    prior_contracts: dict[str, dict] = {}
    prior_attempt_refs: dict[str, tuple[str, dict, str]] = {}
    for prior_sha, prior_binding in prior_failed_contracts.items():
        _require(isinstance(prior_sha, str) and SHA256.fullmatch(prior_sha) is not None and
                 isinstance(prior_binding, dict),
                 "prior failed contract binding is malformed")
        old_validated = prior_binding.get("validated")
        old_commit = prior_binding.get("plan_commit")
        _require(isinstance(old_validated, dict) and old_validated.get("bytes_sha256") == prior_sha and
                 isinstance(old_commit, str) and COMMIT.fullmatch(old_commit) is not None,
                 "prior failed contract identity or committed plan binding is invalid")
        old_plan = old_validated.get("plan")
        old_groups_raw = old_plan.get("groups") if isinstance(old_plan, dict) else None
        old_groups = {item.get("id"): item for item in old_groups_raw if isinstance(item, dict)} \
            if isinstance(old_groups_raw, list) else {}
        old_normalized_raw = old_validated.get("groups")
        old_normalized = {item.get("id"): item for item in old_normalized_raw if isinstance(item, dict)} \
            if isinstance(old_normalized_raw, list) else {}
        _require(isinstance(old_plan, dict) and old_plan.get("execution_series") == series and
                 old_plan.get("source_commit") != source_commit and
                 set(old_groups) == set(groups) and set(old_normalized) == set(groups),
                 "prior failed contract is not a distinct-source contract for the same series and groups")
        _require(old_plan.get("total_wall_budget_seconds") == plan.get("total_wall_budget_seconds") and
                 old_plan.get("resource_budget") == plan.get("resource_budget") and
                 old_plan.get("population") == plan.get("population"),
                 "prior failed contract changes the series budgets or population")
        _require(prior_sha != contract_sha256,
                 "current contract cannot also be registered as its own predecessor")
        refs = prior_binding.get("attempts")
        _require(isinstance(refs, list) and len(refs) == 1,
                 "the prior failed contract must bind exactly one earlier failed attempt")
        for ref in refs:
            _require(isinstance(ref, dict) and isinstance(ref.get("attempt_id"), str) and
                     isinstance(ref.get("ledger_line_sha256"), str) and
                     SHA256.fullmatch(ref["ledger_line_sha256"]) is not None,
                     "prior failed attempt reference is malformed")
            attempt_id = ref["attempt_id"]
            _require(attempt_id == "bifrost-c-kernel-attempt-01-series-01" and
                     attempt_id not in prior_attempt_refs,
                     "only the registered first Bifrost C version-gate failure may be inherited")
            _require(isinstance(ref.get("receipt_sha256"), str) and
                     SHA256.fullmatch(ref["receipt_sha256"]) is not None,
                     "prior failed receipt digest is missing or malformed")
            prior_attempt_refs[attempt_id] = (prior_sha, prior_binding, ref["ledger_line_sha256"])
        prior_contracts[prior_sha] = prior_binding

    declared = plan.get("prior_failed_contracts", [])
    _require(isinstance(declared, list) and len(declared) <= 1,
             "execution plan may bind at most one prior failed contract")
    declared_by_sha = {}
    for ref in declared:
        _require(isinstance(ref, dict) and isinstance(ref.get("sha256"), str) and
                 SHA256.fullmatch(ref["sha256"]) is not None and ref["sha256"] not in declared_by_sha,
                 "execution plan prior-contract reference is malformed or duplicated")
        _require(ref.get("path") == "reports/releases/v0.9.2/acquisition/failed-contract-01.json",
                 "execution plan prior-contract path is not the registered immutable archive")
        _require(ref.get("plan_commit") == prior_contracts.get(ref["sha256"], {}).get("plan_commit"),
                 "execution plan prior-contract commit differs from the validated predecessor")
        declared_by_sha[ref["sha256"]] = ref
    _require(set(declared_by_sha) == set(prior_contracts),
             "execution plan and executor prior-contract bindings differ")
    for prior_sha, ref in declared_by_sha.items():
        prior_binding = prior_contracts[prior_sha]
        bound_attempts = prior_binding["attempts"]
        _require(ref.get("attempts") == [
            {key: item[key] for key in ("attempt_id", "ledger_line_sha256")}
            for item in bound_attempts
        ], "execution plan prior-attempt references differ from the exact validated predecessor")

    commit_values = [row.get("plan_commit") for row, _line_sha in ledger_rows
                     if row.get("contract_sha256") == contract_sha256]
    _require(all(isinstance(value, str) for value in commit_values) and
             bool(commit_values) and len(set(commit_values)) == 1,
             "current attempts were not all dispatched from one committed execution contract")
    plan_commit = commit_values[0]
    _require(COMMIT.fullmatch(plan_commit) is not None, "attempt plan_commit is not an exact Git commit")

    by_group: dict[str, list[tuple]] = collections.defaultdict(list)
    seen_prior_attempts: set[str] = set()
    for row_index, (row, line_sha) in enumerate(ledger_rows):
        group_id = row.get("group_id")
        _require(isinstance(group_id, str) and group_id in groups,
                 f"execution ledger contains unknown group id {group_id!r}")
        attempt_id = row.get("attempt_id")
        prior_ref = prior_attempt_refs.get(attempt_id) if isinstance(attempt_id, str) else None
        if prior_ref is not None:
            prior_sha, prior_binding, expected_line_sha = prior_ref
            _require(row_index == 0,
                     "the registered prior failure must be the first attempt in the shared ledger")
            _require(line_sha == expected_line_sha,
                     "prior failed attempt ledger line differs from its registered digest")
            old_validated = prior_binding["validated"]
            old_plan = old_validated["plan"]
            old_groups = {item["id"]: item for item in old_plan["groups"]}
            group = old_groups[group_id]
            origin_plan_commit = prior_binding["plan_commit"]
            origin_source_commit = old_plan["source_commit"]
            origin_contract_sha = prior_sha
            _require(group_id == "bifrost-c-kernel" and
                     attempt_id == "bifrost-c-kernel-attempt-01-series-01",
                     "prior contract contains a failure outside the exact Bifrost C first attempt")
            _require(row.get("status") == "recorder-error" and row.get("exit_code") == 1 and
                     row.get("timed_out") is False and row.get("capacity_loss") is None and
                     row.get("reports") == [] and row.get("captured_files") == [] and
                     row.get("failed_staging_artifacts", []) == [],
                     "prior contract attempt is not the report-free pre-analysis Bifrost C version-gate failure")
            seen_prior_attempts.add(attempt_id)
        else:
            origin_plan_commit = plan_commit
            origin_source_commit = source_commit
            origin_contract_sha = contract_sha256
            _require(row.get("contract_sha256") == contract_sha256,
                     "execution ledger contains an unregistered predecessor or successor contract")
            group = groups[group_id]

        maximum = group.get("maximum_attempts", 1)
        _require(type(maximum) is int and 1 <= maximum <= MAX_ATTEMPTS_PER_GROUP,
                 f"{group_id}: reviewed maximum_attempts must be one or two")
        pattern = re.compile(rf"{re.escape(group_id)}-attempt-(\d{{2}})-series-(\d{{2}})\Z")
        match = pattern.fullmatch(attempt_id) if isinstance(attempt_id, str) else None
        _require(match is not None, f"{group_id}: attempt id is malformed or belongs to another group")
        attempt_number, attempt_series = (int(value) for value in match.groups())
        _require(1 <= attempt_number <= maximum and attempt_series == series and
                 row.get("execution_series") == series,
                 f"{group_id}: attempt number or series exceeds the reviewed execution plan")
        for key, expected in (
            ("source_commit", origin_source_commit),
            ("contract_sha256", origin_contract_sha),
            ("plan_commit", origin_plan_commit),
            ("group_id", group_id),
            ("tool", group.get("tool")),
            ("case_ids", group.get("case_ids")),
        ):
            _require(row.get(key) == expected,
                     f"{group_id}: attempt {attempt_number} has mismatched {key}")
        if prior_ref is not None:
            current_group = groups[group_id]
            for key in ("tool", "family", "case_ids", "maximum_attempts", "deadline_seconds", "output_roots"):
                _require(group.get(key) == current_group.get(key),
                         f"{group_id}: predecessor and successor differ in {key}")
        status = row.get("status")
        _require(isinstance(status, str) and
                 (status == "completed" or status in FAILED_STATUSES),
                 f"{group_id}: attempt has an unknown or non-terminal status")
        if prior_ref is not None:
            _require(status != "completed", "a prior contract may contribute failures only, never completions")
        by_group[group_id].append((row, line_sha, attempt_number, origin_contract_sha,
                                   origin_plan_commit, prior_ref is not None))

    _require(seen_prior_attempts == set(prior_attempt_refs),
             "one or more declared prior failed attempts are absent from the shared ledger")

    _require(set(by_group) == set(groups), "execution ledger does not contain every planned group")
    selected: dict[str, tuple[dict, str, int]] = {}
    failures: list[tuple[dict, str, int]] = []
    for group_id, attempts in by_group.items():
        numbers = [number for _row, _line_sha, number, _origin_sha, _origin_commit, _is_prior in attempts]
        _require(numbers == list(range(1, len(attempts) + 1)),
                 f"{group_id}: attempts are duplicated, missing, or out of order")
        completed = [index for index, (row, _line_sha, _number, _origin_sha, _origin_commit, _is_prior) in enumerate(attempts)
                     if row.get("status") == "completed"]
        _require(len(completed) == 1,
                 f"{group_id}: expected exactly one completed attempt, found {len(completed)}")
        selected_index = completed[0]
        _require(selected_index == len(attempts) - 1,
                 f"{group_id}: an attempt appears after its completed attempt")
        _require(all(row.get("status") in FAILED_STATUSES
                     for row, _line_sha, _number, _origin_sha, _origin_commit, _is_prior in attempts[:selected_index]),
                 f"{group_id}: a non-failure attempt precedes its selected completion")
        selected_attempt = attempts[selected_index]
        _require(selected_attempt[3] == contract_sha256 and not selected_attempt[5],
                 f"{group_id}: selected completion must belong to the current contract")
        selected[group_id] = selected_attempt[:3]
        for row, line_sha, number, origin_sha, origin_commit, is_prior in attempts[:selected_index]:
            if is_prior:
                binding = prior_contracts[origin_sha]
                old_validated = binding["validated"]
                receipt_sha = next(item["receipt_sha256"] for item in binding["attempts"]
                                   if item["attempt_id"] == row["attempt_id"])
                failures.append((row, line_sha, number, old_validated, origin_commit,
                                 receipt_sha, origin_sha))
            else:
                failures.append((row, line_sha, number, None, origin_commit, None, origin_sha))
    return plan_commit, selected, failures


def _select_scoped_recovery_attempts(
    plan: dict,
    contract_sha256: str,
    ledger_rows: list[tuple[dict, str]],
    scoped: dict,
) -> tuple[str, dict[str, tuple], list[tuple]]:
    """Select C3 attempts while preserving the sealed C1/C2 ledger prefix.

    Historical completion rows remain bound to their original validated C2
    contract.  Only the C2 success roster in the scoped-recovery manifest may
    be retained; the two sealed historical failures remain failures.
    """
    planned = plan.get("groups")
    _require(isinstance(planned, list), "execution plan groups are malformed")
    groups = {item.get("id"): item for item in planned if isinstance(item, dict)}
    _require(len(groups) == len(planned) == EXPECTED_GROUPS,
             "execution plan must contain exactly 84 unique groups")
    _require(isinstance(scoped, dict), "executor did not return scoped-recovery validation")
    manifest = scoped.get("manifest")
    _require(isinstance(manifest, dict) and manifest.get("schema") == "v092-scoped-recovery-manifest/v1",
             "scoped-recovery manifest is missing or has an unsupported schema")
    manifest_sha = scoped.get("manifest_sha256")
    _require(isinstance(manifest_sha, str) and SHA256.fullmatch(manifest_sha) is not None,
             "scoped-recovery manifest digest is missing or malformed")
    ref = plan.get("scoped_recovery")
    _require(isinstance(ref, dict) and set(ref) == {"path", "sha256"} and
             ref.get("path") == "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest.json" and
             ref.get("sha256") == manifest_sha,
             "C3 plan does not bind the exact scoped-recovery manifest")
    _require(plan.get("execution_series") == 1 and manifest.get("execution_series") == 1 and
             plan.get("maximum_attempts_per_group", 2) == 2 and
             "prior_failed_contracts" not in plan and
             manifest.get("maximum_attempts_per_group") == 2 and
             manifest.get("total_wall_budget_seconds") == plan.get("total_wall_budget_seconds") and
             manifest.get("original_wall_origin_utc") == "2026-10-20T00:57:00.680937+00:00" and
             manifest.get("scope") == (
                 "Only current v0.9.2 C2 completed runs retain their own original source/contract "
                 "provenance; new measurements use corrected C3; all failed evidence remains non-selected."
             ),
             "scoped-recovery changed the shared execution series, retry, or wall budget")

    historical = manifest.get("historical_contracts")
    _require(isinstance(historical, list) and len(historical) == 2,
             "scoped-recovery must bind exactly the C1 and C2 historical contracts")
    expected_historical = {
        "reports/releases/v0.9.2/execution-v1/contract.json": {
            "path": "reports/releases/v0.9.2/acquisition/failed-contract-01.json",
            "sha256": SCOPED_C1_SHA256,
            "plan_commit": SCOPED_C1_PLAN_COMMIT,
            "source_commit": SCOPED_C1_SOURCE_COMMIT,
        },
        "reports/releases/v0.9.2/execution-v2/contract.json": {
            "path": "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json",
            "sha256": SCOPED_C2_SHA256,
            "plan_commit": SCOPED_C2_PLAN_COMMIT,
            "source_commit": SCOPED_C2_SOURCE_COMMIT,
        },
    }
    _require({item.get("canonical_path"): {
        key: item.get(key) for key in ("path", "sha256", "plan_commit", "source_commit")
    } for item in historical if isinstance(item, dict)} == expected_historical,
             "scoped-recovery historical contracts differ from the exact registered C1/C2 identities")
    contexts = scoped.get("contexts")
    _require(isinstance(contexts, dict) and len(contexts) == 2,
             "executor did not return both historical contract contexts")
    context_by_sha: dict[str, dict] = {}
    for item in historical:
        _require(isinstance(item, dict), "scoped-recovery historical contract entry is malformed")
        old_sha = item.get("sha256")
        context = contexts.get(old_sha)
        _require(isinstance(old_sha, str) and SHA256.fullmatch(old_sha) is not None and
                 isinstance(context, dict) and isinstance(context.get("validated"), dict),
                 "scoped-recovery historical contract context is absent")
        old_validated = context["validated"]
        old_plan = old_validated.get("plan")
        _require(old_validated.get("bytes_sha256") == old_sha and isinstance(old_plan, dict) and
                 context.get("plan_commit") == item.get("plan_commit") and
                 old_plan.get("source_commit") == item.get("source_commit") and
                 old_plan.get("execution_series") == 1,
                 "historical contract context differs from the sealed manifest")
        historical_root = old_validated.get("repo_root")
        _require(isinstance(historical_root, Path),
                 "historical contract context lacks its repository root")
        expected_archive_path = (historical_root / item["path"]).resolve()
        _require(isinstance(old_validated.get("path"), str) and
                 Path(old_validated["path"]).resolve() == expected_archive_path,
                 "historical context was not validated from its exact archived contract bytes")
        canonical = item.get("canonical_path")
        expected_canonical = {
            "reports/releases/v0.9.2/execution-v1/contract.json",
            "reports/releases/v0.9.2/execution-v2/contract.json",
        }
        _require(canonical in expected_canonical,
                 "scoped-recovery historical contract is not a canonical v1/v2 contract")
        context_by_sha[old_sha] = context
    _require(set(contexts) == set(context_by_sha),
             "executor returned an unregistered historical contract context")
    _require({item["canonical_path"] for item in historical} == {
        "reports/releases/v0.9.2/execution-v1/contract.json",
        "reports/releases/v0.9.2/execution-v2/contract.json",
    }, "scoped-recovery does not bind both canonical historical contracts")
    c1_sha = next(item["sha256"] for item in historical
                   if item["canonical_path"].endswith("execution-v1/contract.json"))
    c2_sha = next(item["sha256"] for item in historical
                   if item["canonical_path"].endswith("execution-v2/contract.json"))

    prefix_ref = manifest.get("ledger_prefix")
    _require(isinstance(prefix_ref, dict) and prefix_ref.get("lines") == 27 and
             type(prefix_ref.get("bytes")) is int and prefix_ref.get("bytes") > 0 and
             isinstance(prefix_ref.get("sha256"), str) and SHA256.fullmatch(prefix_ref["sha256"]) is not None,
             "scoped-recovery ledger prefix reference is malformed")
    _require(prefix_ref.get("path") ==
             "reports/releases/v0.9.2/qualification/scoped-recovery-01/ledger-prefix.jsonl" and
             prefix_ref.get("sha256") == SCOPED_PREFIX_SHA256 and
             prefix_ref.get("bytes") == SCOPED_PREFIX_BYTES,
             "scoped-recovery prefix differs from the exact registered historical byte seal")
    prefix_rows = scoped.get("prefix_rows")
    _require(isinstance(prefix_rows, list) and len(prefix_rows) == 27 and
             scoped.get("sealed_prefix_sha256") == prefix_ref["sha256"],
             "executor's validated prefix differs from the manifest seal")
    _require(len(ledger_rows) >= len(prefix_rows) and ledger_rows[:len(prefix_rows)] == prefix_rows,
             "current ledger does not begin with the exact sealed C1/C2 prefix")
    _require(ledger_rows and len(ledger_rows) <= EXPECTED_GROUPS * MAX_ATTEMPTS_PER_GROUP,
             "execution ledger has no attempts or exceeds the shared two-attempt bound")
    if len(ledger_rows) > len(prefix_rows):
        _require(all(row.get("contract_sha256") == contract_sha256
                     for row, _line_sha in ledger_rows[len(prefix_rows):]),
                 "ledger rows after the sealed prefix must belong only to the current C3 contract")

    retained_completed = scoped.get("retained_completed")
    retained_failures = scoped.get("retained_failures")
    completed_manifest = manifest.get("retained_completed")
    failures_manifest = manifest.get("retained_failures")
    _require(isinstance(retained_completed, dict) and len(retained_completed) == 25 and
             isinstance(completed_manifest, list) and len(completed_manifest) == 25,
             "scoped-recovery must retain exactly the 25 sealed C2 completions")
    _require(isinstance(retained_failures, dict) and len(retained_failures) == 2 and
             isinstance(failures_manifest, list) and len(failures_manifest) == 2,
             "scoped-recovery must retain exactly the two sealed failures")
    complete_by_id = {item.get("attempt_id"): item for item in completed_manifest if isinstance(item, dict)}
    failure_by_id = {item.get("attempt_id"): item for item in failures_manifest if isinstance(item, dict)}
    completed_by_attempt = {}
    for key, recovered in retained_completed.items():
        row = recovered.get("row") if isinstance(recovered, dict) else None
        _require(isinstance(row, dict) and isinstance(row.get("attempt_id"), str) and
                 key in (row.get("group_id"), row.get("attempt_id")) and
                 row["attempt_id"] not in completed_by_attempt,
                 "executor retained-completion map has a duplicate or mismatched key")
        completed_by_attempt[row["attempt_id"]] = recovered
    failures_by_attempt = {}
    for key, recovered in retained_failures.items():
        row = recovered.get("row") if isinstance(recovered, dict) else None
        _require(isinstance(row, dict) and isinstance(row.get("attempt_id"), str) and
                 key in (row.get("group_id"), row.get("attempt_id")) and
                 row["attempt_id"] not in failures_by_attempt,
                 "executor retained-failure map has a duplicate or mismatched key")
        failures_by_attempt[row["attempt_id"]] = recovered
    _require(len(complete_by_id) == 25 and len(failure_by_id) == 2 and
             set(complete_by_id) == set(completed_by_attempt) and
             set(failure_by_id) == set(failures_by_attempt),
             "executor-retained attempts differ from the exact manifest roster")

    prefix_by_id = {row.get("attempt_id"): (row, line_sha) for row, line_sha in prefix_rows}
    _require(len(prefix_by_id) == len(prefix_rows), "sealed prefix contains duplicate attempt IDs")
    _require(set(prefix_by_id) == set(complete_by_id) | set(failure_by_id),
             "sealed prefix contains an unregistered attempt or omits a manifest attempt")
    origins: dict[str, tuple[dict, str, str, bool, str | None]] = {}
    for attempt_id, manifest_item in complete_by_id.items():
        row, line_sha = prefix_by_id[attempt_id]
        recovered = completed_by_attempt[attempt_id]
        attempt_number = int(attempt_id.split("-attempt-", 1)[1][:2])
        _require(isinstance(recovered, dict) and recovered.get("row") == row and
                 recovered.get("ledger_line_sha256") == line_sha and
                 recovered.get("context_sha256") == c2_sha and
                 recovered.get("plan_commit") == manifest_item.get("plan_commit") and
                 recovered.get("attempt_number") == attempt_number,
                 f"{attempt_id}: executor completion differs from the C2 manifest roster")
        _require(manifest_item.get("status") == "completed" and row.get("status") == "completed" and
                 manifest_item.get("group_id") == row.get("group_id") and
                 manifest_item.get("contract_sha256") == c2_sha and
                 manifest_item.get("source_commit") == contexts[c2_sha]["validated"]["plan"]["source_commit"] and
                 manifest_item.get("ledger_line_sha256") == line_sha,
                 f"{attempt_id}: retained completion is not the exact C2 ledger row")
        _verify_manifest_receipt_ref(manifest_item, attempt_id, "completed")
        _verify_manifest_receipt_ref(manifest_item, attempt_id, "started")
        origins[attempt_id] = (row, line_sha, c2_sha, True,
                               manifest_item["completed_receipt"]["sha256"])

    expected_failure_ids = {"bifrost-c-kernel-attempt-01-series-01",
                            "codeql-java-modeling-attempt-01-series-01"}
    _require(set(failure_by_id) == expected_failure_ids,
             "scoped-recovery failures differ from the authorized C1/C2 pair")
    for attempt_id, manifest_item in failure_by_id.items():
        row, line_sha = prefix_by_id[attempt_id]
        recovered = failures_by_attempt[attempt_id]
        expected_context = c1_sha if attempt_id.startswith("bifrost-c-kernel-") else c2_sha
        context = contexts[expected_context]
        _require(isinstance(recovered, dict) and recovered.get("row") == row and
                 recovered.get("ledger_line_sha256") == line_sha and
                 recovered.get("context_sha256") == expected_context and
                 recovered.get("plan_commit") == manifest_item.get("plan_commit"),
                 f"{attempt_id}: executor failure differs from the historical context")
        attempt_number = int(attempt_id.split("-attempt-", 1)[1][:2])
        _require(manifest_item.get("status") == row.get("status") and
                 manifest_item.get("group_id") == row.get("group_id") and
                 manifest_item.get("contract_sha256") == expected_context and
                 manifest_item.get("source_commit") == context["validated"]["plan"]["source_commit"] and
                 manifest_item.get("plan_commit") == context["plan_commit"] and
                 manifest_item.get("ledger_line_sha256") == line_sha and
                 recovered.get("attempt_number") == attempt_number,
                 f"{attempt_id}: retained failure is not the exact historical ledger row")
        _verify_manifest_receipt_ref(manifest_item, attempt_id, "completed")
        _verify_manifest_receipt_ref(manifest_item, attempt_id, "started")
        origins[attempt_id] = (row, line_sha, expected_context, False,
                               manifest_item["completed_receipt"]["sha256"])

    _require(sum(1 for row, _sha256 in prefix_rows if row.get("status") == "completed") == 25 and
             sum(1 for row, _sha256 in prefix_rows if row.get("status") in FAILED_STATUSES) == 2,
             "sealed historical prefix has a completion/failure count outside its authorized roster")
    _require(prefix_rows[0][0].get("attempt_id") == "bifrost-c-kernel-attempt-01-series-01" and
             prefix_rows[-1][0].get("attempt_id") == "codeql-java-modeling-attempt-01-series-01",
             "sealed historical prefix does not preserve the C1 failure and final C2 failure boundaries")

    current_rows = [(row, line_sha) for row, line_sha in ledger_rows[len(prefix_rows):]]
    _require(bool(current_rows), "C3 ledger has no fresh attempts after the sealed historical prefix")
    commit_values = [row.get("plan_commit") for row, _line_sha in current_rows]
    _require(all(isinstance(value, str) and COMMIT.fullmatch(value) is not None for value in commit_values) and
             len(set(commit_values)) == 1,
             "C3 attempts were not dispatched from one exact committed contract")
    plan_commit = commit_values[0]
    source_commit = plan.get("source_commit")
    _require(isinstance(source_commit, str) and COMMIT.fullmatch(source_commit) is not None,
             "C3 execution plan lacks an exact source commit")

    by_group: dict[str, list[tuple]] = collections.defaultdict(list)
    failures: list[tuple] = []
    for index, (row, line_sha) in enumerate(ledger_rows):
        group_id = row.get("group_id")
        _require(isinstance(group_id, str) and group_id in groups,
                 f"execution ledger contains unknown group id {group_id!r}")
        attempt_id = row.get("attempt_id")
        _require(isinstance(attempt_id, str), f"{group_id}: attempt ID is missing")
        if index < len(prefix_rows):
            _require(attempt_id in origins and origins[attempt_id][0] == row and
                     origins[attempt_id][1] == line_sha,
                     f"{attempt_id}: historical row is outside the exact retained roster")
            _row, _line, origin_sha, retained, receipt_sha = origins[attempt_id]
            origin = contexts[origin_sha]
            origin_validated = origin["validated"]
            origin_plan_commit = origin["plan_commit"]
        else:
            _require(row.get("contract_sha256") == contract_sha256 and
                     row.get("plan_commit") == plan_commit and
                     row.get("source_commit") == source_commit,
                     f"{attempt_id}: post-prefix row has mismatched C3 contract, plan commit, or source")
            origin_sha = contract_sha256
            origin_validated = None
            origin_plan_commit = plan_commit
            retained = False
            receipt_sha = None
        pattern = re.compile(rf"{re.escape(group_id)}-attempt-(\d{{2}})-series-(\d{{2}})\Z")
        match = pattern.fullmatch(attempt_id)
        _require(match is not None, f"{group_id}: attempt id is malformed or belongs to another group")
        attempt_number, attempt_series = (int(value) for value in match.groups())
        current_group = groups[group_id]
        maximum = current_group.get("maximum_attempts", 1)
        _require(type(maximum) is int and 1 <= maximum <= MAX_ATTEMPTS_PER_GROUP and
                 1 <= attempt_number <= maximum and attempt_series == 1 and
                 row.get("execution_series") == 1,
                 f"{group_id}: attempt number or series exceeds the shared reviewed plan")
        row_plan = origin_validated["plan"] if origin_validated is not None else plan
        origin_groups = {item["id"]: item for item in row_plan["groups"]}
        origin_group = origin_groups.get(group_id)
        _require(isinstance(origin_group, dict), f"{group_id}: historical context lacks its planned group")
        for key, expected in (
            ("contract_sha256", origin_sha),
            ("plan_commit", origin_plan_commit),
            ("source_commit", row_plan["source_commit"]),
            ("tool", origin_group.get("tool")),
            ("case_ids", origin_group.get("case_ids")),
        ):
            _require(row.get(key) == expected, f"{group_id}: attempt {attempt_number} has mismatched {key}")
        for key in ("tool", "family", "case_ids", "maximum_attempts", "deadline_seconds", "output_roots"):
            _require(origin_group.get(key) == current_group.get(key),
                     f"{group_id}: historical and C3 plans differ in {key}")
        status = row.get("status")
        _require(status == "completed" or status in FAILED_STATUSES,
                 f"{group_id}: attempt has an unknown or non-terminal status")
        if index < len(prefix_rows):
            _require((status == "completed") == retained,
                     f"{attempt_id}: historical completion was not authorized for retention")
            if not retained:
                failures.append((row, line_sha, attempt_number, origin_validated,
                                 origin_plan_commit, receipt_sha, origin_sha))
            else:
                _require(attempt_id in complete_by_id,
                         f"{attempt_id}: historical completion is outside the exact C2 roster")
        elif status in FAILED_STATUSES:
            failures.append((row, line_sha, attempt_number, None, plan_commit, None, contract_sha256))
        by_group[group_id].append((row, line_sha, attempt_number, origin_validated,
                                   origin_plan_commit, origin_sha, retained))

    _require(set(by_group) == set(groups), "execution ledger does not contain every planned group")
    selected: dict[str, tuple] = {}
    for group_id, attempts in by_group.items():
        numbers = [item[2] for item in attempts]
        _require(numbers == list(range(1, len(attempts) + 1)) and len(attempts) <= MAX_ATTEMPTS_PER_GROUP,
                 f"{group_id}: attempts are duplicated, missing, out of order, or exceed the shared limit")
        completed_indexes = [index for index, item in enumerate(attempts) if item[0].get("status") == "completed"]
        _require(len(completed_indexes) == 1 and completed_indexes[0] == len(attempts) - 1,
                 f"{group_id}: expected one final completed attempt and no attempt after completion")
        chosen = attempts[completed_indexes[0]]
        if chosen[6]:
            _require(chosen[0]["attempt_id"] in complete_by_id,
                     f"{group_id}: historical completion is not in the authorized C2 roster")
        else:
            _require(chosen[5] == contract_sha256,
                     f"{group_id}: selected completion must belong to C3 or the exact retained C2 roster")
        _require(all(item[0].get("status") in FAILED_STATUSES for item in attempts[:completed_indexes[0]]),
                 f"{group_id}: a non-failure attempt precedes its selected completion")
        selected[group_id] = chosen
    _require(len(selected) == EXPECTED_GROUPS,
             "scoped-recovery ledger does not select exactly one completion for all 84 groups")
    return plan_commit, selected, failures


def _select_resource_recovery_attempts(
    plan: dict,
    contract_sha256: str,
    ledger_rows: list[tuple[dict, str]],
    resource: dict,
) -> tuple[str, dict[str, tuple], list[tuple]]:
    """Select C4 attempts while retaining C2/C3 rows under their original contracts."""
    planned = plan.get("groups")
    _require(isinstance(planned, list), "C4 execution plan groups are malformed")
    groups = {item.get("id"): item for item in planned if isinstance(item, dict)}
    _require(len(groups) == len(planned) == EXPECTED_GROUPS,
             "C4 execution plan must contain exactly 84 unique groups")
    _require(isinstance(resource, dict), "executor did not return resource-recovery validation")
    manifest = resource.get("manifest")
    _require(isinstance(manifest, dict) and manifest.get("schema") == "v092-resource-recovery-manifest/v1",
             "resource-recovery manifest is missing or has an unsupported schema")
    manifest_sha = resource.get("manifest_sha256")
    reference = plan.get("resource_recovery")
    _require(isinstance(manifest_sha, str) and SHA256.fullmatch(manifest_sha) is not None and
             isinstance(reference, dict) and set(reference) == {"path", "sha256"} and
             reference.get("path") == RESOURCE_RECOVERY_MANIFEST_PATH.as_posix() and
             reference.get("sha256") == manifest_sha,
             "C4 plan does not bind the exact resource-recovery manifest")
    _require(plan.get("execution_series") == 1 and
             manifest.get("execution_series") == 1 and
             plan.get("maximum_attempts_per_group", 2) == 2 and
             manifest.get("maximum_attempts_per_group") == 2 and
             manifest.get("original_wall_origin_utc") == "2026-10-20T00:57:00.680937+00:00" and
             manifest.get("deadline_utc") == "2026-10-21T05:33:00.680937+00:00" and
             manifest.get("total_wall_budget_seconds") == plan.get("total_wall_budget_seconds") == 102960,
             "resource recovery changed the original deadline, wall budget, series, or attempt cap")

    contexts = resource.get("contexts")
    _require(isinstance(contexts, dict) and set(contexts) == {
        RESOURCE_C1_SHA256, RESOURCE_C2_SHA256, RESOURCE_C3_SHA256,
    }, "resource-recovery does not expose the exact original C1/C2/C3 contexts")
    c3_validated = contexts[RESOURCE_C3_SHA256]["validated"]
    c3_plan = c3_validated["plan"]
    _require(c3_validated.get("bytes_sha256") == RESOURCE_C3_SHA256 and
             contexts[RESOURCE_C3_SHA256].get("plan_commit") == RESOURCE_C3_PLAN_COMMIT and
             c3_plan.get("source_commit") == RESOURCE_C3_SOURCE_COMMIT and
             plan.get("tools") == c3_plan.get("tools") and
             plan.get("tool_components") == c3_plan.get("tool_components") and
             plan.get("scoped_recovery") == c3_plan.get("scoped_recovery"),
             "C4 changed original C3 analyzer/runtime bindings or scoped history")
    c3_groups = {group.get("id"): group for group in c3_plan.get("groups", [])
                 if isinstance(group, dict)}
    _require(set(c3_groups) == set(groups), "original C3 group set differs from C4")
    for group_id, current_group in groups.items():
        original_group = c3_groups[group_id]
        for key in ("tool", "family", "case_ids", "maximum_attempts", "deadline_seconds",
                    "output_roots", "argv", "environment"):
            _require(current_group.get(key) == original_group.get(key),
                     f"{group_id}: resource-only C4 changed the C3 {key}")

    prefix_rows = resource.get("prefix_rows")
    retained_completed = resource.get("retained_completed")
    retained_failures = resource.get("retained_failures")
    completed_manifest = manifest.get("retained_completed")
    failures_manifest = manifest.get("retained_failures")
    _require(isinstance(prefix_rows, list) and len(prefix_rows) == RESOURCE_PREFIX_LINES and
             isinstance(retained_completed, dict) and len(retained_completed) == 55 and
             isinstance(completed_manifest, list) and len(completed_manifest) == 55,
             "resource-recovery must retain exactly 55 C2/C3 completed rows")
    _require(isinstance(retained_failures, dict) and len(retained_failures) == 2 and
             isinstance(failures_manifest, list) and len(failures_manifest) == 2,
             "resource-recovery must retain exactly its two C1/C2 failures")
    _require(ledger_rows[:RESOURCE_PREFIX_LINES] == prefix_rows and
             len(ledger_rows) <= EXPECTED_GROUPS * MAX_ATTEMPTS_PER_GROUP,
             "current ledger differs from the exact 57-row C1/C2/C3 prefix or exceeds the shared attempt cap")
    if len(ledger_rows) > RESOURCE_PREFIX_LINES:
        _require(all(row.get("contract_sha256") == contract_sha256
                     for row, _line_sha in ledger_rows[RESOURCE_PREFIX_LINES:]),
                 "ledger rows after the C1/C2/C3 prefix must belong only to the current C4 contract")

    completed_by_group = {item.get("group_id"): item for item in completed_manifest if isinstance(item, dict)}
    failures_by_id = {item.get("attempt_id"): item for item in failures_manifest if isinstance(item, dict)}
    _require(len(completed_by_group) == 55 and len(failures_by_id) == 2 and
             set(completed_by_group) == set(retained_completed) and
             set(failures_by_id) == set(retained_failures),
             "executor retained attempts differ from the exact resource-recovery roster")
    by_line = {line_sha: row for row, line_sha in prefix_rows}
    _require(len(by_line) == RESOURCE_PREFIX_LINES, "resource-recovery prefix contains duplicate rows")
    contexts_by_sha = contexts
    origins: dict[str, tuple[dict, str, str, bool, str | None]] = {}
    expected_completed_by_contract = {RESOURCE_C2_SHA256: 0, RESOURCE_C3_SHA256: 0}
    expected_failures = {
        "bifrost-c-kernel-attempt-01-series-01": RESOURCE_C1_SHA256,
        "codeql-java-modeling-attempt-01-series-01": RESOURCE_C2_SHA256,
    }
    for attempt_id, item in failures_by_id.items():
        _require(item.get("contract_sha256") == expected_failures.get(attempt_id),
                 "resource-recovery failure roster differs from the original C1/C2 failures")

    for item in completed_manifest + failures_manifest:
        line_sha = item.get("ledger_line_sha256")
        row = by_line.get(line_sha)
        _require(row is not None and all(item.get(key) == row.get(key) for key in (
            "group_id", "attempt_id", "status", "contract_sha256", "source_commit", "plan_commit",
        )), "resource-recovery roster entry is not the exact sealed ledger row")
        context_sha = row.get("contract_sha256")
        context = contexts_by_sha.get(context_sha)
        _require(isinstance(context, dict) and isinstance(context.get("validated"), dict),
                 "historical row has no matching validated C1/C2/C3 context")
        old_validated = context["validated"]
        old_plan = old_validated.get("plan", {})
        _require(old_validated.get("bytes_sha256") == context_sha and
                 context.get("plan_commit") == row.get("plan_commit") and
                 old_plan.get("source_commit") == row.get("source_commit"),
                 "historical row provenance differs from its validated original contract context")
        attempt_number = int(row["attempt_id"].split("-attempt-", 1)[1][:2])
        old_group = next((group for group in old_plan.get("groups", [])
                          if isinstance(group, dict) and group.get("id") == row.get("group_id")), None)
        _require(isinstance(old_group, dict), "historical row group is absent from its original contract")
        current_group = groups[row["group_id"]]
        for key in ("tool", "family", "case_ids", "maximum_attempts", "deadline_seconds", "output_roots"):
            _require(old_group.get(key) == current_group.get(key),
                     f"{row['group_id']}: historical and C4 plans differ in {key}")
        if row["status"] == "completed":
            _require(context_sha in expected_completed_by_contract,
                     "only C2 and C3 completed measurements may be retained")
            expected_completed_by_contract[context_sha] += 1
            recovered = retained_completed.get(row["group_id"])
            is_retained = True
            expected_receipt_sha = item.get("completed_receipt", {}).get("sha256")
        else:
            _require(row["attempt_id"] in expected_failures and context_sha == expected_failures[row["attempt_id"]],
                     "retained failure differs from the original C1/C2 failure pair")
            recovered = retained_failures.get(row["attempt_id"])
            is_retained = False
            expected_receipt_sha = item.get("completed_receipt", {}).get("sha256")
        _require(isinstance(recovered, dict) and recovered.get("row") == row and
                 recovered.get("ledger_line_sha256") == line_sha and
                 recovered.get("context_sha256") == context_sha and
                 recovered.get("plan_commit") == context["plan_commit"] and
                 recovered.get("attempt_number") == attempt_number,
                 "executor retained record differs from its exact manifest roster entry")
        origins[row["attempt_id"]] = (row, line_sha, context_sha, is_retained, expected_receipt_sha)
    _require(expected_completed_by_contract == {RESOURCE_C2_SHA256: 25, RESOURCE_C3_SHA256: 30} and
             set(origins) == {row["attempt_id"] for row, _line in prefix_rows} and
             set(completed_by_group) == {row["group_id"] for row, _line in prefix_rows
                                        if row.get("status") == "completed"},
             "resource-recovery roster is not exactly 25 C2 plus 30 C3 completions and two failures")

    c4_rows = [(row, line_sha) for row, line_sha in ledger_rows[RESOURCE_PREFIX_LINES:]]
    _require(c4_rows, "C4 ledger has no fresh attempts after the sealed historical prefix")
    plan_commits = {row.get("plan_commit") for row, _line_sha in c4_rows}
    _require(len(plan_commits) == 1 and isinstance(next(iter(plan_commits)), str) and
             COMMIT.fullmatch(next(iter(plan_commits))) is not None,
             "C4 attempts were not dispatched from one exact committed contract")
    plan_commit = next(iter(plan_commits))
    source_commit = plan.get("source_commit")
    _require(isinstance(source_commit, str) and COMMIT.fullmatch(source_commit) is not None,
             "C4 execution plan lacks an exact source commit")

    by_group: dict[str, list[tuple]] = collections.defaultdict(list)
    failures: list[tuple] = []
    counts: dict[str, int] = collections.Counter(row.get("group_id") for row, _line in prefix_rows)
    for row, line_sha in prefix_rows:
        attempt_id = row["attempt_id"]
        context_sha = row["contract_sha256"]
        context = contexts[context_sha]
        old_validated = context["validated"]
        old_plan = old_validated["plan"]
        attempt_number = int(attempt_id.split("-attempt-", 1)[1][:2])
        retained_record = origins[attempt_id]
        if row.get("status") != "completed":
            failures.append((row, line_sha, attempt_number, old_validated,
                             context["plan_commit"], retained_record[4], context_sha))
        by_group[row["group_id"]].append((row, line_sha, attempt_number, old_validated,
                                          context["plan_commit"], context_sha, retained_record[3]))

    for row, line_sha in c4_rows:
        group_id = row.get("group_id")
        _require(isinstance(group_id, str) and group_id in groups,
                 f"C4 ledger contains unknown group id {group_id!r}")
        counts[group_id] = counts.get(group_id, 0) + 1
        expected_attempt_id = f"{group_id}-attempt-{counts[group_id]:02d}-series-01"
        _require(row.get("attempt_id") == expected_attempt_id and counts[group_id] <= 2 and
                 row.get("contract_sha256") == contract_sha256 and
                 row.get("source_commit") == source_commit and
                 row.get("plan_commit") == plan_commit and
                 row.get("execution_series") == 1,
                 f"{group_id}: C4 row changed original attempt numbering or source/contract identity")
        group = groups[group_id]
        for key, expected in (("tool", group.get("tool")), ("case_ids", group.get("case_ids"))):
            _require(row.get(key) == expected, f"{group_id}: C4 row has mismatched {key}")
        status = row.get("status")
        _require(status == "completed" or status in FAILED_STATUSES,
                 f"{group_id}: C4 attempt has an unknown or non-terminal status")
        record = (row, line_sha, counts[group_id], None, plan_commit, contract_sha256, False)
        by_group[group_id].append(record)
        if status in FAILED_STATUSES:
            failures.append((row, line_sha, counts[group_id], None, plan_commit, None, contract_sha256))

    _require(set(by_group) == set(groups), "resource-recovery ledger does not contain every planned group")
    selected: dict[str, tuple] = {}
    for group_id, attempts in by_group.items():
        numbers = [item[2] for item in attempts]
        _require(numbers == list(range(1, len(attempts) + 1)) and len(attempts) <= MAX_ATTEMPTS_PER_GROUP,
                 f"{group_id}: attempts are duplicated, missing, out of order, or exceed the shared limit")
        completed_indexes = [index for index, item in enumerate(attempts)
                             if item[0].get("status") == "completed"]
        _require(len(completed_indexes) == 1 and completed_indexes[0] == len(attempts) - 1,
                 f"{group_id}: expected one final completed attempt and no attempt after completion")
        chosen = attempts[completed_indexes[0]]
        if chosen[6]:
            _require(chosen[5] in {RESOURCE_C2_SHA256, RESOURCE_C3_SHA256},
                     f"{group_id}: retained completion is not an authorized C2/C3 row")
        else:
            _require(chosen[5] == contract_sha256,
                     f"{group_id}: selected completion must belong to C4 or its retained C2/C3 roster")
        _require(all(item[0].get("status") in FAILED_STATUSES
                     for item in attempts[:completed_indexes[0]]),
                 f"{group_id}: a non-failure attempt precedes its selected completion")
        selected[group_id] = chosen
    _require(len(selected) == EXPECTED_GROUPS,
             "resource-recovery ledger does not select exactly one completion for all 84 groups")
    return plan_commit, selected, failures


def _verify_manifest_receipt_ref(item: dict, attempt_id: str, kind: str) -> None:
    key = f"{kind}_receipt"
    reference = item.get(key)
    expected_path = (ATTEMPTS_ROOT / attempt_id / ("completed.json" if kind == "completed" else "started.json")).as_posix()
    _require(isinstance(reference, dict) and reference.get("path") == expected_path and
             isinstance(reference.get("sha256"), str) and SHA256.fullmatch(reference["sha256"]) is not None,
             f"{attempt_id}: scoped-recovery manifest has an invalid {kind} receipt binding")


def _verify_scoped_recovery_bundle(root: Path, validated: dict,
                                  ledger_rows: list[tuple[dict, str]], scoped: dict) -> None:
    manifest = scoped["manifest"]
    manifest_ref = validated["plan"]["scoped_recovery"]
    manifest_path = _bound(root, manifest_ref["path"], manifest_ref["sha256"], None,
                           "scoped-recovery manifest")
    parsed_manifest, _manifest_bytes = _read_json(manifest_path, "scoped-recovery manifest")
    _require(parsed_manifest == manifest and _sha(manifest_path.read_bytes()) == scoped["manifest_sha256"],
             "executor scoped-recovery manifest differs from the committed plan reference")

    prefix_ref = manifest.get("ledger_prefix")
    prefix_path = _bound(root, prefix_ref.get("path"), prefix_ref.get("sha256"),
                         prefix_ref.get("bytes"), "sealed historical ledger prefix")
    prefix_rows = _read_ledger_with_hashes(prefix_path)
    _require(len(prefix_rows) == prefix_ref.get("lines") == 27 and
             prefix_rows == scoped.get("prefix_rows") and ledger_rows[:27] == prefix_rows,
             "current ledger differs from the independently hashed 27-line historical prefix")

    authorization_ref = manifest.get("authorization")
    _require(isinstance(authorization_ref, dict) and
             authorization_ref.get("path") ==
             "reports/releases/v0.9.2/qualification/scoped-recovery-01/authorization.json",
             "scoped-recovery authorization reference is missing or uses an unexpected path")
    authorization_path = _bound(root, authorization_ref.get("path"), authorization_ref.get("sha256"),
                                None, "scoped-recovery authorization")
    authorization, _authorization_bytes = _read_json(authorization_path, "scoped-recovery authorization")
    _require(scoped.get("authorization") == authorization and
             authorization.get("schema") == "v092-scoped-recovery-authorization/v1" and
             authorization.get("evidence_kind") == "human-chat-authorization-record",
             "scoped-recovery authorization does not contain the exact recorded human authorization")
    authorized = authorization.get("authorized_scope")
    _require(isinstance(authorized, dict) and
             authorized.get("retained_current_completed_groups") == 25 and
             authorized.get("corrected_harness_for_remaining_groups") is True and
             authorized.get("codeql_java_modeling_next_attempt") == 2 and
             authorized.get("original_wall_origin_utc") == prefix_rows[0][0].get("start_utc") and
             authorized.get("total_wall_budget_seconds") == validated["plan"].get("total_wall_budget_seconds") and
             authorized.get("max_attempts_per_group_across_contracts") == 2 and
             authorized.get("case_population") == EXPECTED_CASES and
             authorized.get("groups") == EXPECTED_GROUPS and
             authorized.get("report_partitions") == EXPECTED_REPORTS and
             authorized.get("report_rows") == EXPECTED_ROWS and
             authorized.get("minimum_launch_free_gib") == 125 and
             authorized.get("protected_reserve_gib") == 40 and
             authorized.get("scratch_retention_caps_gib") == 24 and
             manifest.get("original_wall_origin_utc") == prefix_rows[0][0].get("start_utc") and
             "Relabeling original measurements as executed under new source" in authorization.get("forbidden", []),
             "scoped-recovery authorization does not preserve the original matrix scope and limits")
    expected_proof_paths = {
        "repair_patch": "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/fix-02.patch",
        "repair_proof": "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/patch-manifest-02.json",
        "failure_diagnosis": "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/diagnosis.json",
    }
    for name, expected_path in expected_proof_paths.items():
        reference = manifest.get(name)
        _require(isinstance(reference, dict) and reference.get("path") == expected_path,
                 f"scoped-recovery {name} reference is missing or uses an unexpected path")
        _bound(root, reference.get("path"), reference.get("sha256"), None,
               f"scoped-recovery {name}")
    for item in manifest["retained_completed"] + manifest["retained_failures"]:
        for kind in ("started", "completed"):
            reference = item.get(f"{kind}_receipt")
            _require(isinstance(reference, dict),
                     f"scoped-recovery manifest lacks a {kind} receipt entry")
            _bound(root, reference["path"], reference["sha256"], None,
                   f"scoped-recovery {kind} receipt")


def _verify_resource_recovery_bundle(root: Path, validated: dict,
                                     ledger_rows: list[tuple[dict, str]], resource: dict,
                                     current_head: str) -> None:
    """Independently parse the C4 packet and bind executor contexts to it."""
    parser = _load_resource_recovery_module()
    try:
        packet = parser.validate_packet(
            root, validated["plan"].get("resource_recovery"),
        )
    except parser.ResourceRecoveryError as exc:
        raise EvidenceError(f"resource-recovery packet rejected: {exc}") from exc

    plan = validated["plan"]
    manifest = packet["manifest"]
    _require(isinstance(resource, dict) and resource.get("manifest") == manifest and
             resource.get("manifest_sha256") == packet["manifest_sha256"] and
             resource.get("prefix_rows") == packet["prefix_rows"] and
             resource.get("tail_rows") == packet["tail_rows"] and
             resource.get("sealed_prefix_sha256") == RESOURCE_PREFIX_SHA256,
             "executor resource-recovery result differs from the independently parsed packet")
    _require(len(ledger_rows) >= RESOURCE_PREFIX_LINES and
             ledger_rows[:RESOURCE_PREFIX_LINES] == packet["prefix_rows"] and
             ledger_rows[RESOURCE_PREFIX_LINES:] == packet["tail_rows"],
             "execution ledger differs from the exact resource-recovery prefix and tail")
    _require(plan.get("execution_series") == 1 and
             plan.get("maximum_attempts_per_group", 2) == MAX_ATTEMPTS_PER_GROUP and
             plan.get("total_wall_budget_seconds") == manifest["total_wall_budget_seconds"] and
             plan.get("resource_guards") == {"stop_free_gib": 48, "working_set_gib": 12},
             "C4 plan changed the original series, retry cap, deadline budget, or resource guards")
    c3_plan = packet["historical_contract"].get("resource_budget")
    current_budget = plan.get("resource_budget")
    _require(isinstance(c3_plan, dict) and isinstance(current_budget, dict) and
             current_budget == dict(c3_plan, minimum_launch_free_gib=110) and
             current_budget.get("protected_reserve_gib") == 40 and
             current_budget.get("scratch_gib") == 24 and
             current_budget.get("proposed_total_retention_ceiling_gib") == 24,
             "C4 resource budget must preserve C3 limits except for the authorized 110 GiB launch floor")
    _require(manifest.get("resource_budget") == {
        key: current_budget[key] for key in (
            "minimum_launch_free_gib", "protected_reserve_gib", "scratch_gib",
            "proposed_total_retention_ceiling_gib",
        )
    }, "resource-recovery manifest differs from the C4 plan resource budget")

    expected_source_inputs = {
        plan["resource_recovery"]["path"]: plan["resource_recovery"]["sha256"],
        manifest["authorization"]["path"]: manifest["authorization"]["sha256"],
        manifest["ledger_prefix"]["path"]: manifest["ledger_prefix"]["sha256"],
        manifest["historical_contract"]["path"]: manifest["historical_contract"]["sha256"],
    }
    source_inputs = {item.get("path"): item.get("sha256") for item in validated.get("source_inputs", [])
                     if isinstance(item, dict)}
    _require(all(source_inputs.get(path) == digest for path, digest in expected_source_inputs.items()),
             "C4 source_inputs do not bind every exact resource-recovery packet artifact")
    for relative, digest in expected_source_inputs.items():
        try:
            source_bytes = subprocess.check_output(
                ["git", "show", f"{plan['source_commit']}:{relative}"],
                cwd=root, stderr=subprocess.STDOUT,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise EvidenceError(f"C4 source commit lacks resource-recovery input: {relative}") from exc
        _require(_sha(source_bytes) == digest,
                 f"C4 source commit differs from the exact resource-recovery input: {relative}")

    c3_ref = manifest["historical_contract"]
    _require(c3_ref == {
        "path": RESOURCE_C3_ARCHIVE_PATH.as_posix(),
        "sha256": RESOURCE_C3_SHA256,
        "canonical_path": RESOURCE_C3_CANONICAL_PATH.as_posix(),
        "plan_commit": RESOURCE_C3_PLAN_COMMIT,
        "source_commit": RESOURCE_C3_SOURCE_COMMIT,
    }, "resource-recovery manifest changed the original C3 contract identity")
    archive = _bound(root, c3_ref["path"], c3_ref["sha256"], None, "archived original C3 contract")
    archive_raw = archive.read_bytes()
    _require(_sha(archive_raw) == RESOURCE_C3_SHA256 and
             packet["historical_contract"] == json.loads(archive_raw),
             "archived original C3 contract bytes differ from the independently parsed contract")
    try:
        canonical = subprocess.check_output(
            ["git", "show", f"{RESOURCE_C3_PLAN_COMMIT}:{RESOURCE_C3_CANONICAL_PATH.as_posix()}"],
            cwd=root, stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError("cannot independently read the original C3 canonical contract") from exc
    _require(canonical == archive_raw, "C3 archive differs from its original canonical contract bytes")
    _assert_ancestor(root, RESOURCE_C3_SOURCE_COMMIT, RESOURCE_C3_PLAN_COMMIT,
                     "original C3 source-to-plan commit")
    _assert_ancestor(root, RESOURCE_C3_PLAN_COMMIT, current_head, "original C3 plan commit")
    _assert_ancestor(root, RESOURCE_C3_PLAN_COMMIT, plan["source_commit"],
                     "original C3 plan to C4 source commit")
    _assert_ancestor(root, RESOURCE_C3_SOURCE_COMMIT, plan["source_commit"],
                     "original C3 source to C4 source commit")

    historical_contract = packet["historical_contract"]
    _require(plan.get("scoped_recovery") == historical_contract.get("scoped_recovery"),
             "C4 must preserve the C3 scoped-recovery reference exactly")
    contexts = resource.get("contexts")
    expected_contexts = {
        RESOURCE_C1_SHA256: (SCOPED_C1_PLAN_COMMIT, SCOPED_C1_SOURCE_COMMIT,
                             "reports/releases/v0.9.2/acquisition/failed-contract-01.json"),
        RESOURCE_C2_SHA256: (SCOPED_C2_PLAN_COMMIT, SCOPED_C2_SOURCE_COMMIT,
                             "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json"),
        RESOURCE_C3_SHA256: (RESOURCE_C3_PLAN_COMMIT, RESOURCE_C3_SOURCE_COMMIT,
                             RESOURCE_C3_ARCHIVE_PATH.as_posix()),
    }
    _require(isinstance(contexts, dict) and set(contexts) == set(expected_contexts),
             "executor resource-recovery result lacks the exact C1/C2/C3 historical contexts")
    for contract_sha, (plan_commit, source_commit, archive_path) in expected_contexts.items():
        entry = contexts.get(contract_sha)
        _require(isinstance(entry, dict) and isinstance(entry.get("validated"), dict),
                 "resource-recovery historical context is malformed")
        old = entry["validated"]
        _require(old.get("bytes_sha256") == contract_sha and
                 entry.get("plan_commit") == plan_commit and
                 old.get("plan", {}).get("source_commit") == source_commit and
                 Path(old.get("path", "")).resolve() == (root / archive_path).resolve(),
                 "resource-recovery historical context lost its original contract/source/plan identity")

    c3_context = contexts[RESOURCE_C3_SHA256]["validated"]
    c3_plan = c3_context.get("plan", {})
    c3_source_inputs = c3_context.get("source_inputs")
    _require(isinstance(c3_source_inputs, list) and c3_source_inputs,
             "archived C3 context lacks its original source-input inventory")
    _require(isinstance(c3_plan.get("runner_source_sha256"), str) and
             SHA256.fullmatch(c3_plan["runner_source_sha256"]) is not None,
             "archived C3 context lacks its original runner digest")
    try:
        c3_runner = subprocess.check_output(
            ["git", "show", f"{RESOURCE_C3_SOURCE_COMMIT}:scripts/execute-release-v092.py"],
            cwd=root, stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError("cannot independently read the original C3 runner") from exc
    _require(_sha(c3_runner) == c3_plan["runner_source_sha256"],
             "original C3 runner bytes differ from its historical receipt binding")
    for source_input in c3_source_inputs:
        _require(isinstance(source_input, dict) and isinstance(source_input.get("path"), str) and
                 isinstance(source_input.get("sha256"), str) and
                 SHA256.fullmatch(source_input["sha256"]) is not None,
                 "archived C3 source-input inventory is malformed")
        source_path = _relative(source_input["path"], "original C3 source-input path").as_posix()
        try:
            source_bytes = subprocess.check_output(
                ["git", "show", f"{RESOURCE_C3_SOURCE_COMMIT}:{source_path}"],
                cwd=root, stderr=subprocess.STDOUT,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise EvidenceError(f"original C3 source input is absent at its origin commit: {source_path}") from exc
        _require(_sha(source_bytes) == source_input["sha256"],
                 f"original C3 source input differs at its origin commit: {source_path}")
    c3_scoped = c3_context.get("scoped_recovery")
    _require(isinstance(c3_scoped, dict) and isinstance(c3_scoped.get("manifest"), dict),
             "archived C3 context lacks its original scoped-recovery validation")
    scoped_parser = _load_scoped_recovery_module()
    try:
        c3_packet = scoped_parser.validate_packet(
            root, historical_contract.get("scoped_recovery"),
        )
    except scoped_parser.ScopedRecoveryError as exc:
        raise EvidenceError(f"original C3 scoped-recovery packet rejected: {exc}") from exc
    _require(c3_scoped.get("manifest") == c3_packet["manifest"] and
             c3_scoped.get("manifest_sha256") == c3_packet["manifest_sha256"] and
             c3_scoped.get("prefix_rows") == c3_packet["prefix_rows"],
             "archived C3 executor context differs from the independently parsed scoped-recovery packet")
    _verify_scoped_recovery_bundle(
        root, c3_context, packet["prefix_rows"], c3_scoped,
    )
    _verify_historical_contract_contexts(root, c3_scoped["manifest"], c3_scoped, current_head)

    completed_manifest = manifest.get("retained_completed")
    failures_manifest = manifest.get("retained_failures")
    completed_map = resource.get("retained_completed")
    failure_map = resource.get("retained_failures")
    _require(isinstance(completed_manifest, list) and len(completed_manifest) == 55 and
             isinstance(completed_map, dict) and len(completed_map) == 55,
             "resource-recovery must retain exactly 55 validated completions")
    _require(isinstance(failures_manifest, list) and len(failures_manifest) == 2 and
             isinstance(failure_map, dict) and len(failure_map) == 2,
             "resource-recovery must retain exactly two validated historical failures")
    prefix_by_line = {line_sha: row for row, line_sha in packet["prefix_rows"]}
    for item in completed_manifest + failures_manifest:
        line_sha = item.get("ledger_line_sha256")
        row = prefix_by_line.get(line_sha)
        _require(row is not None and all(item.get(key) == row.get(key) for key in (
            "group_id", "attempt_id", "status", "contract_sha256", "source_commit", "plan_commit",
        )), "resource-recovery roster differs from an original sealed ledger row")
        context_sha = row["contract_sha256"]
        context = contexts[context_sha]
        attempt_number = int(row["attempt_id"].split("-attempt-", 1)[1][:2])
        if row["status"] == "completed":
            recovered = completed_map.get(row["group_id"])
            _require(isinstance(recovered, dict) and recovered.get("row") == row and
                     recovered.get("ledger_line_sha256") == line_sha and
                     recovered.get("context_sha256") == context_sha and
                     recovered.get("plan_commit") == context["plan_commit"] and
                     recovered.get("attempt_number") == attempt_number,
                     "executor retained-completion map differs from the sealed historical roster")
        else:
            recovered = failure_map.get(row["attempt_id"])
            _require(isinstance(recovered, dict) and recovered.get("row") == row and
                     recovered.get("ledger_line_sha256") == line_sha and
                     recovered.get("context_sha256") == context_sha and
                     recovered.get("plan_commit") == context["plan_commit"] and
                     recovered.get("attempt_number") == attempt_number,
                     "executor retained-failure map differs from the sealed historical roster")


def _verify_historical_contract_contexts(root: Path, manifest: dict, scoped: dict,
                                         current_head: str) -> None:
    """Recheck old source-input and canonical-contract bytes at their original commits."""
    contexts = scoped["contexts"]
    for item in manifest["historical_contracts"]:
        old_sha = item["sha256"]
        context = contexts[old_sha]
        old_validated = context["validated"]
        old_plan = old_validated["plan"]
        old_commit = item["plan_commit"]
        canonical = item["canonical_path"]
        archive_path = item["path"]
        _bound(root, archive_path, old_sha, None, "archived historical contract")
        try:
            canonical_bytes = subprocess.check_output(
                ["git", "show", f"{old_commit}:{canonical}"], cwd=root, stderr=subprocess.STDOUT,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise EvidenceError(f"cannot read historical canonical contract at {old_commit}") from exc
        _require(_sha(canonical_bytes) == old_sha == old_validated["bytes_sha256"],
                 "historical canonical contract bytes differ from the archived contract")
        source_commit = old_plan["source_commit"]
        _assert_ancestor(root, source_commit, old_commit, "historical source-to-contract commit")
        _assert_ancestor(root, old_commit, current_head, "historical contract commit")
        source_inputs = old_validated.get("source_inputs")
        _require(isinstance(source_inputs, list) and source_inputs,
                 "historical contract has no independently replayable source-input inventory")
        seen_paths = set()
        for source_input in source_inputs:
            _require(isinstance(source_input, dict) and isinstance(source_input.get("path"), str) and
                     isinstance(source_input.get("sha256"), str) and
                     SHA256.fullmatch(source_input["sha256"]) is not None,
                     "historical source-input entry is malformed")
            source_path = _relative(source_input["path"], "historical source-input path").as_posix()
            _require(source_path not in seen_paths, "historical source-input inventory contains duplicates")
            seen_paths.add(source_path)
            try:
                source_bytes = subprocess.check_output(
                    ["git", "show", f"{source_commit}:{source_path}"], cwd=root,
                    stderr=subprocess.STDOUT,
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                raise EvidenceError(f"historical source input is absent at {source_commit}: {source_path}") from exc
            _require(_sha(source_bytes) == source_input["sha256"],
                     f"historical source input differs at its origin commit: {source_path}")


def _verify_codeql_modeling_failure_diagnosis(root: Path, manifest: dict,
                                               failure_summary: dict) -> dict:
    reference = manifest["failure_diagnosis"]
    path = _bound(root, reference.get("path"), reference.get("sha256"), None,
                  "CodeQL Java modeling failure diagnosis")
    diagnosis, _raw = _read_json(path, "CodeQL Java modeling failure diagnosis")
    expected = {
        "schema": "v092-codeql-modeling-stamp-failure/v1",
        "attempt_id": "codeql-java-modeling-attempt-01-series-01",
        "contract_sha256": failure_summary["contract_sha256"],
        "source_commit": failure_summary["source_commit"],
        "plan_commit": failure_summary["plan_commit"],
        "completed_receipt_sha256": failure_summary["completed_receipt_sha256"],
        "status": "failed",
        "exit_code": 1,
        "all_50_capture_hashes_and_stream_hashes_verified": True,
        "no_selected_reports": True,
    }
    _require(all(diagnosis.get(key) == value for key, value in expected.items()) and
             len(failure_summary.get("captured_files", [])) == 50 and
             failure_summary.get("stdout") is not None and failure_summary.get("stderr") is not None,
             "CodeQL Java modeling diagnosis does not match the independently replayed complete failure")
    return {"path": reference["path"], "sha256": reference["sha256"]}


def _relative(value: object, description: str) -> PurePosixPath:
    try:
        return EXECUTOR._relative(value, description)
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc


def _assert_no_symlink_path(root: Path, destination: Path, description: str) -> None:
    try:
        relative = destination.relative_to(root)
    except ValueError as exc:
        raise EvidenceError(f"{description} escapes the repository root") from exc
    current = root
    for part in relative.parts:
        current /= part
        _require(not current.is_symlink(), f"symlink in {description}: {current}")


def _bound(root: Path, relative: object, digest: object, size: object | None, description: str) -> Path:
    path = _relative(relative, description)
    _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
             f"{description} must bind a lowercase SHA-256")
    destination = root / Path(*path.parts)
    current = root
    for part in path.parts:
        current /= part
        _require(not current.is_symlink(), f"symlink in {description}: {current}")
    _require(destination.is_file() and not destination.is_symlink(), f"missing or symlinked {description}: {path}")
    data = destination.read_bytes()
    _require(_sha(data) == digest, f"{description} SHA-256 mismatch: {path}")
    if size is not None:
        _require(type(size) is int and len(data) == size, f"{description} byte count mismatch: {path}")
    return destination


def _assert_ancestor(root: Path, ancestor: str, descendant: str, description: str) -> None:
    _require(COMMIT.fullmatch(ancestor) is not None and COMMIT.fullmatch(descendant) is not None,
             f"{description} must use exact Git commits")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError(f"{description} is not in the required Git ancestry") from exc


def _assert_committed_contract(root: Path, validated: dict, plan_commit: str) -> None:
    contract = Path(validated["path"]).resolve()
    relative = contract.relative_to(root.resolve()).as_posix()
    try:
        committed = subprocess.check_output(
            ["git", "show", f"{plan_commit}:{relative}"], cwd=root, stderr=subprocess.STDOUT,
        )
        current_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.STDOUT,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--", relative], cwd=root,
            text=True, stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError("cannot verify the committed v0.9.2 execution contract") from exc
    _require(_sha(committed) == validated["bytes_sha256"], "receipt plan_commit does not contain the exact execution contract")
    _require(not status.strip(), "execution contract has working-tree changes")
    _assert_ancestor(root, plan_commit, current_head, "execution-plan commit")
    _assert_ancestor(root, validated["plan"]["source_commit"], plan_commit, "source commit to execution-plan commit")


def _read_capture_manifest(root: Path, attempt_id: str, receipt: dict) -> dict[str, dict]:
    rows = receipt.get("captured_files")
    _require(isinstance(rows, list), f"{attempt_id}: captured_files must be a list")
    by_relative: dict[str, dict] = {}
    capture_root = root / Path(*ATTEMPTS_ROOT.parts) / attempt_id / "capture"
    _require(not capture_root.is_symlink(), f"{attempt_id}: capture root is symlinked")
    for row in rows:
        _require(isinstance(row, dict), f"{attempt_id}: malformed captured file")
        relative = _relative(row.get("execution_relative"), "captured execution path").as_posix()
        _require(relative not in by_relative, f"{attempt_id}: duplicate captured file {relative}")
        _require(isinstance(row.get("capture_path"), str), f"{attempt_id}: captured file lacks its capture path")
        expected_capture = (capture_root / Path(*PurePosixPath(relative).parts)).resolve()
        _require(Path(row["capture_path"]).resolve() == expected_capture,
                 f"{attempt_id}: captured file path differs from its execution-relative path")
        captured_path = (capture_root / Path(*PurePosixPath(relative).parts))
        _require(captured_path.is_file() and not captured_path.is_symlink(),
                 f"{attempt_id}: missing or symlinked captured file {relative}")
        data = captured_path.read_bytes()
        _require(_sha(data) == row.get("sha256") and type(row.get("bytes")) is int and len(data) == row["bytes"],
                 f"{attempt_id}: captured file digest or byte count differs: {relative}")
        by_relative[relative] = row

    actual = set()
    if capture_root.exists():
        for current, directories, files in os.walk(capture_root, followlinks=False):
            current_path = Path(current)
            for name in directories:
                _require(not (current_path / name).is_symlink(), f"{attempt_id}: symlink in capture tree")
            for name in files:
                path = current_path / name
                _require(path.is_file() and not path.is_symlink(), f"{attempt_id}: non-regular capture entry {path}")
                actual.add(path.relative_to(capture_root).as_posix())
    _require(actual == set(by_relative), f"{attempt_id}: capture tree differs from its file inventory")
    return by_relative


def _verify_report_projection(
    root: Path,
    attempt_id: str,
    fixture_revision: str,
    expected: dict,
    entry: dict,
    captured: dict[str, dict],
    adapter_version: str,
) -> tuple[dict, int, collections.Counter, dict[str, tuple[str, bytes]]]:
    expected_stage = NORMAL_ROOT / attempt_id / PurePosixPath(expected["path"]).relative_to("reports/releases/v0.9.2/normal")
    expected_original = ATTEMPTS_ROOT / attempt_id / "original" / PurePosixPath(expected["path"])
    _require(entry.get("source_path") == expected["source_path"], "normalized source path differs from the reviewed plan")
    _require(entry.get("staged_path") == expected_stage.as_posix(), "staged report is outside the current v0.9.2 attempt")
    _require(entry.get("original_path") == expected_original.as_posix(), "original report path differs from the current attempt")
    _require(entry.get("case_ids") == expected["case_ids"], "receipt report membership differs from the reviewed plan")
    _require(entry.get("tool") == expected["tool"] and entry.get("tool_version") == expected["tool_version"],
             "receipt report tool identity differs from the reviewed plan")

    original_path = _bound(root, entry.get("original_path"), entry.get("original_sha256"), None, "original normalized report")
    staged_path = _bound(root, entry.get("staged_path"), entry.get("staged_sha256"), None, "staged normalized report")
    source_relative = _relative(expected["source_path"], "normalized source report").as_posix()
    captured_source = captured.get(source_relative)
    _require(captured_source is not None and captured_source.get("sha256") == _sha(original_path.read_bytes()) and
             captured_source.get("bytes") == original_path.stat().st_size,
             "original normalized report is not backed by its execution capture")
    try:
        original = json.loads(original_path.read_bytes())
        staged = json.loads(staged_path.read_bytes())
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("normalized report is not valid JSON") from exc
    _require(isinstance(original, dict) and isinstance(staged, dict), "normalized reports must be JSON objects")
    _require(original.get("schema_version") == 1 and staged.get("schema_version") == 1,
             "normalized report schema version is not 1")
    try:
        EXECUTOR._report_identity(expected, original_path.read_bytes(), fixture_revision)
        EXECUTOR._report_identity(expected, staged_path.read_bytes(), fixture_revision)
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc
    _require(original.get("adapter_version") == adapter_version and staged.get("adapter_version") == adapter_version,
             "report adapter version differs from the committed adapter source")
    config_hash = original.get("configuration_hash")
    _require(isinstance(config_hash, str) and SHA256.fullmatch(config_hash) is not None,
             "report configuration_hash is missing or malformed")
    _require(staged.get("configuration_hash") == config_hash, "configuration hash changed during report staging")

    raw_mappings = entry.get("raw_output_mappings")
    rows = original.get("results")
    staged_rows = staged.get("results")
    _require(isinstance(raw_mappings, list) and isinstance(rows, list) and isinstance(staged_rows, list),
             "report raw mappings or result rows are malformed")
    _require(len(raw_mappings) == len(rows) == len(staged_rows), "raw mapping count differs from report rows")
    mapping_by_capture: dict[str, dict] = {}
    mapping_exec_paths: set[str] = set()
    for mapping in raw_mappings:
        _require(isinstance(mapping, dict), "malformed raw-output mapping")
        relative = _relative(mapping.get("execution_relative"), "raw execution-relative path").as_posix()
        captured_path = _relative(mapping.get("captured_path"), "captured raw-output path").as_posix()
        expected_capture = (ATTEMPTS_ROOT / attempt_id / "capture" / PurePosixPath(relative)).as_posix()
        _require(captured_path == expected_capture, "raw-output mapping escapes its attempt capture")
        _require(relative in captured and captured[relative].get("sha256") == mapping.get("sha256") and
                 captured[relative].get("bytes") == mapping.get("bytes"),
                 f"raw-output mapping is not backed by the capture manifest: {relative}")
        _require(relative not in mapping_exec_paths and captured_path not in mapping_by_capture,
                 "duplicate raw-output mapping")
        mapping_exec_paths.add(relative)
        mapping_by_capture[captured_path] = mapping

    restored = json.loads(json.dumps(staged))
    outcome_counts: collections.Counter = collections.Counter()
    raw_by_case: dict[str, tuple[str, bytes]] = {}
    used_raw_mappings: set[str] = set()
    for row, staged_row in zip(rows, restored["results"]):
        _require(isinstance(row, dict) and isinstance(staged_row, dict), "report contains a malformed row")
        _require(row.get("case_id") == staged_row.get("case_id"), "report row order or case identity changed")
        outcome = row.get("outcome")
        _require(outcome in OUTCOMES, f"unknown typed outcome {outcome!r}")
        outcome_counts[outcome] += 1
        staged_raw = staged_row.get("raw_output")
        mapping = mapping_by_capture.get(staged_raw)
        _require(mapping is not None, f"staged raw_output has no fresh capture mapping: {staged_raw}")
        _require(staged_raw not in used_raw_mappings,
                 f"report rows reuse one raw-output mapping: {staged_raw}")
        used_raw_mappings.add(staged_raw)
        _require(row.get("raw_output") == mapping["execution_relative"],
                 "staged raw_output does not map back to its original execution path")
        _require(row["case_id"] not in raw_by_case, "report contains duplicate case identities")
        relative = mapping["execution_relative"]
        raw_path = root / Path(*ATTEMPTS_ROOT.parts) / attempt_id / "capture" / Path(*PurePosixPath(relative).parts)
        raw_by_case[row["case_id"]] = (relative, raw_path.read_bytes())
        staged_row["raw_output"] = mapping["execution_relative"]
    _require(used_raw_mappings == set(mapping_by_capture),
             "report rows and raw-output mappings are not a bijection")
    _require(restored == original,
             "normalized staging changed report fields beyond the retained raw_output path")
    return original, len(rows), outcome_counts, raw_by_case


def _adapter_version(root: Path, plan: dict, group: dict) -> str:
    if group["id"] == "codeql-swift-common108":
        return "swift-normal-v092"
    if group["id"] == "joern-swift-common108":
        return "joern-normal-v092"
    try:
        cargo = (root / "Cargo.toml").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EvidenceError(f"cannot read Cargo.toml for the Rust adapter version: {exc}") from exc
    package_header = re.search(r"(?ms)^\[package\]\s*(.*?)(?=^\[|\Z)", cargo)
    version_match = re.search(r'(?m)^version\s*=\s*"([^"\n]+)"\s*$', package_header.group(1)) if package_header else None
    version = version_match.group(1) if version_match else None
    _require(isinstance(version, str) and version, "Cargo.toml package.version is malformed")
    return version


def _runtime_manifest(bindings: dict, alias: str, tool: str) -> tuple[Path, dict]:
    component = bindings.get(alias)
    _require(isinstance(component, dict) and component.get("kind") == "runtime-tree-manifest",
             f"{tool}: exact {alias} runtime-tree manifest binding is missing")
    digest = component.get("sha256")
    path_value = component.get("path")
    _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None and
             isinstance(path_value, str) and Path(path_value).is_absolute(),
             f"{tool}: exact {alias} runtime-tree manifest path or SHA-256 is malformed")
    path = Path(path_value)
    _require(path.is_file() and not path.is_symlink(),
             f"{tool}: {alias} runtime-tree manifest is missing or symlinked")
    raw = path.read_bytes()
    _require(_sha(raw) == digest, f"{tool}: {alias} runtime-tree manifest changed after validation")
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"{tool}: {alias} runtime-tree manifest is invalid JSON") from exc
    _require(isinstance(manifest, dict) and manifest.get("schema_version") == 1 and
             isinstance(manifest.get("root"), str) and Path(manifest["root"]).is_absolute() and
             isinstance(manifest.get("files"), list) and isinstance(manifest.get("symlinks", []), list),
             f"{tool}: {alias} runtime-tree manifest has an unsupported shape")
    root = Path(manifest["root"])
    _require(root.is_dir() and not root.is_symlink(),
             f"{tool}: {alias} runtime-tree root is missing or symlinked")
    return root.resolve(strict=True), manifest


def _runtime_manifest_file(root: Path, manifest: dict, relative: str, description: str) -> bytes:
    expected = _relative(relative, f"{description} runtime path").as_posix()
    matches = [item for item in manifest["files"]
               if isinstance(item, dict) and item.get("path") == expected]
    _require(len(matches) == 1, f"{description} is not uniquely bound in its runtime-tree manifest")
    digest = matches[0].get("sha256")
    _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
             f"{description} runtime-tree entry lacks an exact SHA-256")
    target = root
    for part in PurePosixPath(expected).parts:
        target /= part
        _require(not target.is_symlink(), f"symlink in {description} runtime path: {target}")
    _require(target.is_file(), f"{description} runtime file is missing: {target}")
    raw = target.read_bytes()
    _require(_sha(raw) == digest, f"{description} differs from its runtime-tree manifest")
    return raw


def _codeql_native_pack_version(language: str, validated: dict) -> str:
    expected_version = CODEQL_NATIVE_PACKS.get(language)
    _require(expected_version is not None, f"codeql: no native query pack is pinned for {language}")
    pack_binding = validated.get("codeql_packs")
    alias = pack_binding.get("component") if isinstance(pack_binding, dict) else None
    _require(isinstance(alias, str) and alias in validated.get("tool_components", {}).get("codeql", []),
             "codeql: native query packs are not bound to the CodeQL runtime identity")
    root, manifest = _runtime_manifest(validated["tools"], alias, "codeql")
    package_name = f"codeql/{language}-queries"
    query_packs = [item.get("path") for item in manifest["files"]
                   if isinstance(item, dict) and isinstance(item.get("path"), str) and
                   len(PurePosixPath(item["path"]).parts) == 4 and
                   PurePosixPath(item["path"]).parts[0] == "codeql" and
                   PurePosixPath(item["path"]).parts[1] == f"{language}-queries" and
                   PurePosixPath(item["path"]).parts[3] == "qlpack.yml"]
    expected_path = f"{package_name}/{expected_version}/qlpack.yml"
    _require(query_packs == [expected_path],
             f"codeql: runtime pack closure does not bind exactly {expected_path}")
    qlpack = _runtime_manifest_file(root, manifest, expected_path, "CodeQL native query pack")
    try:
        text = qlpack.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError("codeql: native query pack metadata is not UTF-8") from exc
    name_match = re.search(r"(?m)^name:\s*([^\s#]+)\s*$", text)
    version_match = re.search(r"(?m)^version:\s*([^\s#]+)\s*$", text)
    _require(name_match is not None and name_match.group(1) == f"codeql/{language}-queries" and
             version_match is not None and version_match.group(1) == expected_version,
             "codeql: bound native query-pack metadata disagrees with its pinned name or version")
    return expected_version


def _pysa_native_suite_sha256(bindings: dict, validated: dict) -> str:
    alias = "pysa-runtime"
    _require(alias in validated.get("tool_components", {}).get("pysa", []),
             "pysa: shipped taint suite is not part of the Pysa runtime identity")
    root, manifest = _runtime_manifest(bindings, alias, "pysa")
    pyre = bindings.get("pysa")
    _require(isinstance(pyre, dict) and isinstance(pyre.get("path"), str),
             "pysa: exact pyre executable binding is missing")
    pyre_path = Path(pyre["path"])
    _require(pyre_path.is_file() and not pyre_path.is_symlink() and
             pyre_path.parent.parent.resolve(strict=True) == root,
             "pysa: shipped suite runtime root differs from the bound pyre executable")

    suite_relative = PurePosixPath("lib/pyre_check/taint")
    suite = root / Path(*suite_relative.parts)
    _require(suite.is_dir() and not suite.is_symlink(), "pysa: shipped taint suite is missing or symlinked")
    suite_prefix = suite_relative.as_posix() + "/"
    symlinks = manifest.get("symlinks", [])
    _require(not any(isinstance(item, dict) and isinstance(item.get("path"), str) and
                     (item["path"] == suite_relative.as_posix() or item["path"].startswith(suite_prefix))
                     for item in symlinks), "pysa: shipped taint suite contains a runtime symlink")
    expected_files = {
        item["path"]: item for item in manifest["files"]
        if isinstance(item, dict) and isinstance(item.get("path"), str) and
        item["path"].startswith(suite_prefix)
    }
    actual_files: list[Path] = []

    def collect(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except OSError as exc:
            raise EvidenceError(f"pysa: cannot enumerate shipped taint suite: {directory}") from exc
        for entry in entries:
            _require(not entry.is_symlink(), f"pysa: shipped taint suite contains a symlink: {entry}")
            if entry.is_dir():
                collect(entry)
            elif entry.is_file():
                actual_files.append(entry)
            else:
                raise EvidenceError(f"pysa: shipped taint suite contains a non-file entry: {entry}")

    collect(suite)
    _require(bool(actual_files), "pysa: shipped taint suite has no files")
    actual_relatives = {
        (suite_relative / path.relative_to(suite)).as_posix(): path for path in actual_files
    }
    _require(set(actual_relatives) == set(expected_files),
             "pysa: shipped suite file membership differs from its runtime-tree manifest")

    digest = hashlib.sha256()
    for relative, path in actual_relatives.items():
        raw = path.read_bytes()
        expected_digest = expected_files[relative].get("sha256")
        _require(isinstance(expected_digest, str) and SHA256.fullmatch(expected_digest) is not None and
                 _sha(raw) == expected_digest,
                 f"pysa: shipped suite file differs from its runtime-tree manifest: {relative}")
        suite_path = PurePosixPath(relative).relative_to(suite_relative).as_posix()
        digest.update(suite_path.encode("utf-8"))
        digest.update(raw)
    return digest.hexdigest()


def _expected_d8_build_identity(bindings: dict, validated: dict) -> str:
    binding = bindings.get("d8")
    _require(isinstance(binding, dict), "flowdroid: exact D8 runtime binding is missing")
    digest = binding.get("sha256")
    _require(digest == D8_JAR_SHA256,
             "flowdroid: D8 JAR SHA-256 differs from the witnessed v0.9.2 release input")
    expected_identity = f"{D8_VERSION_LINE}; r8 jar sha256:{D8_JAR_SHA256}"
    _require(binding.get("build_identity") == expected_identity,
             "flowdroid: D8 build identity differs from the exact version witness and JAR digest")
    source_inputs = validated.get("source_inputs")
    witnesses = [item for item in source_inputs if isinstance(item, dict) and
                 item.get("path") == D8_VERSION_WITNESS_PATH] if isinstance(source_inputs, list) else []
    _require(len(witnesses) == 1 and witnesses[0].get("sha256") == D8_VERSION_WITNESS_SHA256,
             "flowdroid: exact D8 --version witness is not bound by the release contract")
    return expected_identity


def _native_report_build_identity(tool: str, version: str, base: str,
                                  bindings: dict, validated: dict, group: dict) -> str:
    group_id = group.get("id")
    match = re.fullmatch(r"(bifrost|codeql|flowdroid|infer|joern|opentaint|pysa|semgrep)-(java|javascript|python)-native",
                         group_id) if isinstance(group_id, str) else None
    _require(match is not None and match.group(1) == tool,
             f"{tool}: unknown tool-native report group identity {group_id!r}")
    language = match.group(2)
    if tool == "bifrost":
        _require(version == "bifrost 0.13.1" and
                 bindings[tool].get("build_identity") == "271a0bd840372a1ce6e6e11fc60a788e997ed353",
                 "bifrost: native identity is not bound to the exact v0.13.1 release build")
        activation = (
            f"{version} — standalone engine; empty shipped policy catalog; "
            "open-pack acquisition disabled; BIFROST_OPEN_PACKS_DISABLE=1"
        )
    elif tool == "codeql":
        pack_version = _codeql_native_pack_version(language, validated)
        suite = (f"codeql/{language}-queries@{pack_version}:"
                 f"codeql-suites/{language}-security-extended.qls")
        activation = f"{version} shipped suite {suite}"
    elif tool == "flowdroid":
        _require(language == "java", "flowdroid: native analyzer profile is registered for Java only")
        for alias, expected in (("flowdroid", FLOWDROID_JAR_SHA256),
                                ("android-platform", ANDROID_PLATFORM_SHA256)):
            _require(bindings.get(alias, {}).get("sha256") == expected,
                     f"flowdroid: exact {alias} digest differs from the pinned native identity")
        activation = (
            f"FlowDroid {version} shipped SourcesAndSinks.txt catalog "
            "(extracted verbatim from the pinned soot-infoflow-cmd jar) and default "
            "summariesManual taint wrapper"
        )
    elif tool == "infer":
        _require(language == "java", "infer: native analyzer profile is registered for Java only")
        activation = f"{version} shipped Pulse checker, no taint configuration"
    elif tool == "joern":
        activation = f"{version} DefaultSemantics only"
    elif tool == "opentaint":
        _require(language == "java", "opentaint: native analyzer profile is registered for Java only")
        _require(bindings.get("opentaint", {}).get("sha256") == OPENTAINT_JAR_SHA256 and
                 bindings.get("opentaint-models", {}).get("sha256") == OPENTAINT_MODELS_SHA256,
                 "opentaint: release-asset digests differ from the pinned native identity")
        activation = f"{version} shipped models archive only — no rule set"
    elif tool == "pysa":
        _require(language == "python", "pysa: native analyzer profile is registered for Python only")
        pyrefly = bindings.get("pyrefly")
        _require(isinstance(pyrefly, dict) and pyrefly.get("version") == "1.4.0",
                 "pysa: Pyrefly version differs from the exact v0.9.2 native pin")
        suite_digest = _pysa_native_suite_sha256(bindings, validated)
        activation = (
            f"Pysa (pyre-check {version} + Pyrefly {pyrefly['version']}) shipped taint model suite "
            f"lib/pyre_check/taint with --no-verify (suite-sha256:{suite_digest})"
        )
    elif tool == "semgrep":
        activation = (
            f"{version} over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules "
            f"into adapters/semgrep/native/v0.9.2/{language}"
        )
    else:
        raise EvidenceError(f"{tool}: no exact v0.9.2 native build-identity derivation is registered")
    return f"{base} — {activation}"


def _expected_report_build_identity(group: dict, report: dict, validated: dict) -> str:
    """Derive the full normalized identity from exact v0.9.2 tool bindings."""
    tool = group["tool"]
    bindings = validated["tools"]
    binding = bindings.get(tool)
    _require(isinstance(binding, dict), f"{tool}: exact analyzer tool binding is missing")

    def component_sha(alias: str) -> str:
        component = bindings.get(alias)
        _require(isinstance(component, dict), f"{tool}: exact {alias} component binding is missing")
        digest = component.get("sha256")
        _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
                 f"{tool}: exact {alias} component SHA-256 is missing")
        return digest

    version = report.get("tool_version")
    _require(isinstance(version, str) and version, f"{tool}: report tool_version is missing")
    expected_version = EXPECTED_TOOL_VERSIONS.get(tool)
    _require(version == expected_version,
             f"{tool}: report tool_version differs from the exact v0.9.2 profile pin")
    binding_version = binding.get("report_version", binding.get("version"))
    _require(binding_version == version,
             f"{tool}: report tool_version differs from its exact analyzer binding")

    if tool == "bifrost":
        identity = binding.get("build_identity")
        _require(isinstance(identity, str) and identity,
                 "bifrost: exact build identity is missing from the analyzer binding")
        base = identity
    elif tool == "codeql":
        identity = binding.get("build_identity")
        _require(identity == CODEQL_CLI_BUILD_SHA,
                 "codeql: CLI build SHA differs from the exact v0.9.2 release identity")
        base = f"codeql-cli:{identity}"
    elif tool == "joern":
        base = f"joern-cli:{version}"
    elif tool == "semgrep":
        base = f"semgrep-oss:{version}"
    elif tool == "infer":
        digest = binding.get("sha256")
        _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
                 "infer: exact analyzer binary SHA-256 is missing")
        base = f"infer:{version} bin-sha256:{digest}"
    elif tool == "flowdroid":
        _require(component_sha("flowdroid") == FLOWDROID_JAR_SHA256 and
                 component_sha("android-platform") == ANDROID_PLATFORM_SHA256,
                 "flowdroid: analyzer or Android platform digest differs from the pinned profile")
        base = (
            f"soot-infoflow-cmd-{version}-jar-with-dependencies.jar sha256:{component_sha('flowdroid')}; "
            f"android-34 platform android.jar sha256:{component_sha('android-platform')}"
        )
    elif tool == "opentaint":
        _require(component_sha("opentaint") == OPENTAINT_JAR_SHA256 and
                 component_sha("opentaint-models") == OPENTAINT_MODELS_SHA256,
                 "opentaint: release-asset digest differs from the pinned profile")
        base = (
            f"opentaint-project-analyzer.jar sha256:{component_sha('opentaint')}; "
            f"opentaint-models.tar.gz sha256:{component_sha('opentaint-models')}"
        )
    elif tool == "pysa":
        pyrefly = bindings.get("pyrefly")
        _require(isinstance(pyrefly, dict) and pyrefly.get("version") == "1.4.0",
                 "pysa: exact Pyrefly version is missing or differs from its v0.9.2 pin")
        base = (
            f"pyre-check:{version} pyre.bin-sha256:{component_sha('pyre.bin')} "
            f"pyrefly:{pyrefly['version']} pyrefly-sha256:{component_sha('pyrefly')}"
        )
    else:
        raise EvidenceError(f"{tool}: no exact v0.9.2 report build-identity derivation is registered")

    group_id = group.get("id")
    if isinstance(group_id, str) and group_id.endswith("-native"):
        return _native_report_build_identity(tool, version, base, bindings, validated, group)
    if tool == "flowdroid":
        _require("d8" in group.get("identity_components", []),
                 "flowdroid: exact D8 runtime is not included in this group identity")
        _require(group_id in {
            "flowdroid-java-kernel", "flowdroid-java-modeling", "flowdroid-kotlin-kernel",
        }, f"flowdroid: unsupported v0.9.2 report group identity {group_id!r}")
        return f"{base}; dexed by {_expected_d8_build_identity(bindings, validated)}"
    return base


def _verify_report_build_identity(group: dict, report: dict, validated: dict) -> None:
    expected = _expected_report_build_identity(group, report, validated)
    _require(report.get("tool_build_identity") == expected,
             f"{group.get('id')}: report build identity differs from its exact analyzer/runtime bindings")


def _swift_configuration_hash(root: Path, plan: dict, key: str) -> str:
    configurations = plan.get("configurations")
    references = configurations.get(key) if isinstance(configurations, dict) else None
    _require(isinstance(references, list) and references, f"Swift executable plan lacks configuration closure {key!r}")
    _require(all(isinstance(item, dict) and set(item) == {"path", "sha256"}
                 and isinstance(item.get("path"), str) for item in references),
             "Swift configuration entries must bind exactly path and SHA-256")
    seen: set[str] = set()
    digest = hashlib.sha256()
    for reference in sorted(references, key=lambda item: tuple(PurePosixPath(item["path"]).parts)):
        relative = _relative(reference["path"], "Swift configuration path").as_posix()
        _require(relative not in seen, f"duplicate Swift configuration path: {relative}")
        seen.add(relative)
        path = root / Path(*PurePosixPath(relative).parts)
        data = path.read_bytes()
        _require(_sha(data) == reference["sha256"], f"Swift configuration changed after execution: {relative}")
        digest.update(relative.encode())
        digest.update(data)
    return digest.hexdigest()


def _verify_swift_raw_provenance(root: Path, group: dict, plan_path: str,
                                 plan: dict, report: dict,
                                 raw_by_case: dict[str, tuple[str, bytes]]) -> None:
    if group["id"] == "codeql-swift-common108":
        _require(report.get("configuration_hash") == _swift_configuration_hash(root, plan, "patched-codeql"),
                 "CodeQL Swift configuration hash differs from its exact versioned plan closure")
        try:
            import sys
            sys.path.insert(0, str(root / "scripts"))
            import swift_normal_runner_v092 as swift_runner
            import swift_common_population_v2 as common
        except ImportError as exc:
            raise EvidenceError(f"cannot load the committed Swift CodeQL provenance validators: {exc}") from exc
        receipt_ref = None
        for _case_id, (_relative, raw_bytes) in raw_by_case.items():
            try:
                raw = json.loads(raw_bytes)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise EvidenceError("CodeQL Swift raw case evidence is not JSON") from exc
            _require(isinstance(raw, dict) and raw.get("schema") == "swift-normal-raw/v1",
                     "CodeQL Swift raw evidence has an unknown schema")
            reference = raw.get("query_qualification")
            _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
                     "CodeQL Swift raw evidence lacks the fresh query qualification reference")
            if receipt_ref is None:
                receipt_ref = reference
            _require(reference == receipt_ref, "CodeQL Swift rows bind different query qualification receipts")
            _require(raw.get("case_id") == _case_id, "CodeQL Swift raw case identity differs from report row")
        _require(receipt_ref is not None, "CodeQL Swift group has no raw query provenance")
        argv = group.get("argv", [])
        query_flags = [index for index, value in enumerate(argv) if value == "--query-receipt"]
        _require(len(query_flags) == 1 and query_flags[0] + 1 < len(argv) and
                 argv[query_flags[0] + 1] == receipt_ref.get("path"),
                 "CodeQL Swift raw receipt differs from the exact runner command")
        receipt_path = _bound(root, receipt_ref.get("path"), receipt_ref.get("sha256"), None,
                              "fresh CodeQL query qualification receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        _require(receipt.get("plan_path") == plan_path, "CodeQL query receipt names a different executable plan")
        try:
            swift_runner.verify_query_receipt(root, plan, receipt, plan_path)
            _population, _rows, _swift_rows, cases, _digest = common.load_common_population(root)
        except (ValueError, OSError, KeyError) as exc:
            raise EvidenceError(f"CodeQL query qualification failed independent replay: {exc}") from exc
        _require(len(cases) == 108 and set(raw_by_case) <= set(cases),
                 "CodeQL Swift report includes a case outside the exact common-108 projection")
        return

    if group["id"] == "joern-swift-common108":
        _require(report.get("configuration_hash") == _swift_configuration_hash(root, plan, "joern-current108"),
                 "Joern Swift configuration hash differs from its exact versioned plan closure")
        expected_plan_sha = _sha((root / plan_path).read_bytes())
        population = json.loads((root / POPULATION_PATH).read_text(encoding="utf-8"))
        population_sha = plan.get("population_sha256")
        _require(isinstance(population_sha, str) and SHA256.fullmatch(population_sha) is not None,
                 "Joern executable plan lacks the exact population SHA-256")
        report_outcomes = {row.get("case_id"): row.get("outcome") for row in report.get("results", [])}
        for case_id, (_relative, raw_bytes) in raw_by_case.items():
            try:
                raw = json.loads(raw_bytes)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise EvidenceError("Joern Swift raw case evidence is not JSON") from exc
            _require(isinstance(raw, dict) and raw.get("schema") == "joern-common-raw/v092",
                     "Joern Swift raw evidence has an unknown schema")
            _require(raw.get("case_id") == case_id and raw.get("plan_sha256") == expected_plan_sha and
                     raw.get("population_sha256") == population_sha and
                     raw.get("fixture_revision") == population.get("fixture_revision") and
                     raw.get("identity") == plan.get("identity") and
                     raw.get("qualification_sha256") == plan.get("fresh_qualification", {}).get("sha256"),
                     "Joern raw case provenance differs from the exact plan, runtime, or population")
            raw_outcome = raw.get("raw_outcome")
            _require(raw_outcome in OUTCOMES, "Joern raw outcome is unknown")
            normalized = raw_outcome if raw_outcome in ("runner-error", "unsupported") else "inconclusive"
            _require(raw.get("state") == normalized and report_outcomes.get(case_id) == normalized,
                     "Joern typed outcome was altered or flattened")


def _verify_one_group(root: Path, validated: dict, group: dict, receipt: dict,
                      plan_commit: str, attempt_number: int) -> tuple[list[dict], collections.Counter]:
    plan = validated["plan"]
    group_id = group["id"]
    expected_group = next(item for item in validated["groups"] if item["id"] == group_id)
    attempt_id = f"{group_id}-attempt-{attempt_number:02d}-series-{plan['execution_series']:02d}"
    expected_attempt = root / Path(*ATTEMPTS_ROOT.parts) / attempt_id
    expected_execution = (root / Path(*EXECUTOR.EXECUTION_ROOT.parts) /
                          f"series-{plan['execution_series']:02d}" / group_id /
                          f"attempt-{attempt_number:02d}")
    expected_cache = (root / Path(*EXECUTOR.CACHE_ROOT.parts) /
                      f"series-{plan['execution_series']:02d}" / group_id /
                      f"attempt-{attempt_number:02d}")
    _require(receipt.get("schema_version") == 1 and receipt.get("release") == RELEASE, f"{group_id}: receipt schema or release mismatch")
    _require(receipt.get("status") == "completed" and receipt.get("exit_code") == 0 and
             receipt.get("timed_out") is False and receipt.get("capacity_loss") is None,
             f"{group_id}: attempt did not complete successfully")
    _verify_process_ownership(group_id, "completed", receipt.get("process_ownership"), required=True)
    duration = receipt.get("duration_seconds")
    _require(type(duration) in (int, float) and math.isfinite(duration) and duration >= 0,
             f"{group_id}: invalid monotonic duration")
    attempt_fields = (
        ("execution_series", plan["execution_series"]),
        ("group_id", group_id),
        ("attempt_id", attempt_id),
        ("source_commit", plan["source_commit"]),
        ("plan_commit", plan_commit),
        ("contract_sha256", validated["bytes_sha256"]),
        ("runner_source_sha256", plan["runner_source_sha256"]),
        ("fixture_revision", validated["fixture_revision"]),
        ("population", plan["population"]),
        ("tool", group["tool"]),
        ("tool_binding", validated["tools"][group["tool"]]),
        ("identity_components", [EXECUTOR._component_identity(alias, validated["tools"][alias])
                                  for alias in expected_group["identity_components"]]),
        ("swift_plan", expected_group.get("swift_plan")),
        ("joern_plan", expected_group.get("joern_plan")),
        ("qualification", validated["qualification"][group["tool"]]),
        ("source_inputs", validated["source_inputs"]),
        ("cache_root", str(expected_cache)),
        ("argv", group["argv"]),
        ("output_roots", group["output_roots"]),
        ("case_ids", group["case_ids"]),
        ("deadline_seconds", group["deadline_seconds"]),
        ("execution_root", str(expected_execution)),
        ("started_receipt", "started.json"),
    )
    for key, expected in attempt_fields:
        _require(key in receipt and receipt[key] == expected,
                 f"{group_id}: receipt {key} differs from the committed plan")
    try:
        environment = EXECUTOR._child_environment(group, expected_execution, expected_attempt, expected_cache)
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc
    _require(receipt.get("environment") == environment, f"{group_id}: execution environment differs from the committed plan")
    _require(receipt.get("snapshot_git_head") in (None, plan["source_commit"]),
             f"{group_id}: source snapshot HEAD differs from source_commit")

    attempt = expected_attempt
    ledger_entry = receipt
    completed, _ = _read_json(attempt / "completed.json", f"{group_id} completed receipt")
    _require(completed == ledger_entry, f"{group_id}: completed receipt differs from ledger")
    started, _ = _read_json(attempt / "started.json", f"{group_id} started receipt")
    _require(isinstance(started, dict), f"{group_id}: malformed started receipt")
    _require(all(key in started and started[key] == expected for key, expected in attempt_fields),
             f"{group_id}: started receipt is missing an exact plan field")
    _require(all(receipt.get(key) == value for key, value in started.items()
                 if key not in ("status", "end_utc")), f"{group_id}: started provenance differs from completed receipt")
    _require(started.get("status") == "started" and started.get("end_utc") is None,
             f"{group_id}: started receipt has an invalid state")
    for field in ("stdout", "stderr"):
        stream = receipt.get(field)
        _require(isinstance(stream, dict) and stream.get("path") == f"{field}.txt",
                 f"{group_id}: missing exact {field} receipt")
        _bound(root, (ATTEMPTS_ROOT / attempt_id / stream["path"]).as_posix(),
               stream.get("sha256"), stream.get("bytes"), f"{group_id} {field}")

    captured = _read_capture_manifest(root, attempt_id, receipt)
    reports = receipt.get("reports")
    expected_reports = expected_group["reports"]
    _require(isinstance(reports, list) and len(reports) == len(expected_reports),
             f"{group_id}: report receipt count differs from the committed plan")
    adapter_version = _adapter_version(root, plan, group)
    bindings = []
    outcomes: collections.Counter = collections.Counter()
    swift_plan_info = expected_group.get("swift_plan") if group_id == "codeql-swift-common108" else expected_group.get("joern_plan")
    swift_plan = None
    swift_plan_path = None
    if group_id in ("codeql-swift-common108", "joern-swift-common108"):
        _require(isinstance(swift_plan_info, dict), f"{group_id}: exact v0.9.2 executable plan binding is missing")
        swift_plan_path = swift_plan_info.get("path")
        plan_file = _bound(root, swift_plan_path, swift_plan_info.get("sha256"), None,
                           f"{group_id} executable plan")
        swift_plan, _ = _read_json(plan_file, f"{group_id} executable plan")
    for expected, entry in zip(expected_reports, reports):
        _require(isinstance(entry, dict), f"{group_id}: malformed report receipt")
        report, count, report_outcomes, raw_by_case = _verify_report_projection(
            root, attempt_id, validated["fixture_revision"], expected, entry, captured, adapter_version,
        )
        tool_binding = validated["tools"][group["tool"]]
        if group_id in ("codeql-swift-common108", "joern-swift-common108"):
            _require(report.get("tool_version") == swift_plan.get("identity", {}).get("tool_version") and
                     report.get("tool_build_identity") == swift_plan.get("identity", {}).get("tool_build_identity"),
                     f"{group_id}: report runtime identity differs from its executable plan")
            _verify_swift_raw_provenance(root, group, swift_plan_path, swift_plan, report, raw_by_case)
        else:
            _verify_report_build_identity(group, report, validated)
        _require(isinstance(report.get("tool_build_identity"), str) and report["tool_build_identity"],
                 f"{group_id}: report lacks a witnessed tool build identity")
        bindings.append({
            "adapter": expected["path"],
            "staged_path": entry["staged_path"],
            "sha256": entry["staged_sha256"],
            "rows": count,
        })
        outcomes.update(report_outcomes)
    return bindings, outcomes


def _verify_failed_attempt(root: Path, validated: dict, group: dict, receipt: dict,
                           plan_commit: str, attempt_number: int,
                           ledger_line_sha256: str,
                           expected_receipt_sha256: str | None = None) -> dict:
    """Validate a non-selected terminal failure without admitting its reports."""
    plan = validated["plan"]
    group_id = group["id"]
    attempt_id = f"{group_id}-attempt-{attempt_number:02d}-series-{plan['execution_series']:02d}"
    attempt = root / Path(*ATTEMPTS_ROOT.parts) / attempt_id
    execution = (root / Path(*EXECUTOR.EXECUTION_ROOT.parts) /
                 f"series-{plan['execution_series']:02d}" / group_id /
                 f"attempt-{attempt_number:02d}")
    cache = (root / Path(*EXECUTOR.CACHE_ROOT.parts) /
             f"series-{plan['execution_series']:02d}" / group_id /
             f"attempt-{attempt_number:02d}")
    status = receipt.get("status")
    c4_attempt = ("resource_recovery" in plan and
                  receipt.get("contract_sha256") == validated.get("bytes_sha256"))
    c4_prelaunch_refusal = (
        c4_attempt and status in {"capacity-lost", "recorder-error"} and
        "process_ownership" not in receipt
    )
    c4_postprocess_capacity_failure = (
        c4_attempt and status == "capacity-lost" and
        "process_ownership" in receipt and "recorder_error" in receipt
    )
    _require(status in FAILED_STATUSES, f"{group_id}: non-selected attempt is not a terminal failure")
    _require(receipt.get("schema_version") == 1 and receipt.get("release") == RELEASE,
             f"{group_id}: failed attempt receipt schema or release mismatch")
    _require(isinstance(receipt.get("start_utc"), str) and isinstance(receipt.get("end_utc"), str),
             f"{group_id}: failed attempt lacks terminal timestamps")
    _require(receipt.get("reports", []) == [],
             f"{group_id}: failed attempt contains report receipts and cannot be excluded safely")

    expected_identity_components = [
        EXECUTOR._component_identity(alias, validated["tools"][alias])
        for alias in group["identity_components"]
    ]
    try:
        environment = EXECUTOR._child_environment(group, execution, attempt, cache)
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc
    expected_fields = {
        "execution_series": plan["execution_series"],
        "group_id": group_id,
        "attempt_id": attempt_id,
        "source_commit": plan["source_commit"],
        "plan_commit": plan_commit,
        "contract_sha256": validated["bytes_sha256"],
        "runner_source_sha256": plan["runner_source_sha256"],
        "fixture_revision": validated["fixture_revision"],
        "population": plan["population"],
        "tool": group["tool"],
        "tool_binding": validated["tools"][group["tool"]],
        "identity_components": expected_identity_components,
        "swift_plan": group.get("swift_plan"),
        "joern_plan": group.get("joern_plan"),
        "qualification": validated["qualification"][group["tool"]],
        "source_inputs": validated["source_inputs"],
        "cache_root": str(cache),
        "argv": group["argv"],
        "environment": environment,
        "execution_root": str(execution),
        "output_roots": group["output_roots"],
        "case_ids": group["case_ids"],
        "deadline_seconds": group["deadline_seconds"],
        "started_receipt": "started.json",
    }
    for key, expected in expected_fields.items():
        _require(key in receipt and receipt[key] == expected,
                 f"{group_id}: failed attempt {attempt_number} has mismatched {key}")
    allowed_receipt_fields = (set(expected_fields) | {
        "schema_version", "release", "status", "start_utc", "end_utc", "snapshot_git_head",
        "exit_code", "timed_out", "duration_seconds", "capacity_loss", "stdout", "stderr",
        "captured_files", "reports", "recorder_error", "disk_guard_error",
        "failed_staging_artifacts", "process_ownership",
    })
    _require(set(receipt) <= allowed_receipt_fields,
             f"{group_id}: failed attempt receipt contains unknown fields")
    if "disk_guard_error" in receipt:
        _require(c4_attempt and status == "recorder-error",
                 f"{group_id}: disk_guard_error is valid only on a C4 recorder-error receipt")
    if status == "recorder-error":
        _require({"recorder_error", "captured_files", "failed_staging_artifacts"} <= set(receipt),
                 f"{group_id}: recorder-error receipt is missing its error or capture inventory")
        _verify_process_ownership(group_id, status, receipt.get("process_ownership"), required=False)
        if "disk_guard_error" in receipt:
            _require(c4_attempt,
                     f"{group_id}: legacy recorder-error contains C4 disk-guard metadata")
            guard_error = _verify_resource_guard_error(
                group_id, receipt["disk_guard_error"], capacity_loss=False,
            )
            _require(receipt.get("recorder_error") ==
                     f"DiskGuardError: {guard_error['message']}",
                     f"{group_id}: C4 recorder detail differs from its disk-guard error")
    else:
        if c4_prelaunch_refusal:
            _require({"exit_code", "timed_out", "duration_seconds", "capacity_loss", "stdout", "stderr",
                      "captured_files", "reports", "recorder_error", "failed_staging_artifacts"} <= set(receipt),
                     f"{group_id}: pre-launch C4 refusal receipt is incomplete")
        elif c4_postprocess_capacity_failure:
            _verify_process_ownership(group_id, status, receipt.get("process_ownership"), required=True)
            _require({"exit_code", "timed_out", "duration_seconds", "capacity_loss", "stdout", "stderr",
                      "captured_files", "reports", "recorder_error", "failed_staging_artifacts"} <= set(receipt),
                     f"{group_id}: post-process C4 capacity receipt is incomplete")
        else:
            _verify_process_ownership(group_id, status, receipt.get("process_ownership"), required=True)
            _require("failed_staging_artifacts" not in receipt,
                     f"{group_id}: non-recorder failure contains recorder-only staging artifacts")
            _require({"exit_code", "timed_out", "duration_seconds", "capacity_loss", "stdout", "stderr",
                      "captured_files", "reports"} <= set(receipt),
                     f"{group_id}: terminal process failure receipt is incomplete")
    _require(receipt.get("snapshot_git_head") in (None, plan["source_commit"]),
             f"{group_id}: failed attempt source snapshot differs from source_commit")

    completed, completed_bytes = _read_json(attempt / "completed.json", f"{group_id} failed completed receipt")
    _require(completed == receipt, f"{group_id}: failed completed receipt differs from its ledger row")
    if expected_receipt_sha256 is not None:
        _require(_sha(completed_bytes) == expected_receipt_sha256,
                 f"{group_id}: failed completed receipt differs from its predecessor digest")
    started, _started_bytes = _read_json(attempt / "started.json", f"{group_id} failed started receipt")
    started_fields = set(expected_fields) | {"schema_version", "release", "status", "start_utc", "end_utc"}
    _require(isinstance(started, dict) and set(started) == started_fields and
             started.get("status") == "started" and
             started.get("end_utc") is None and all(started.get(key) == expected
                                                       for key, expected in expected_fields.items()),
             f"{group_id}: failed started receipt does not bind the exact attempt")
    _require(all(receipt.get(key) == value for key, value in started.items()
                 if key not in ("status", "end_utc")),
             f"{group_id}: failed start and completion provenance differ")

    exit_code = receipt.get("exit_code")
    timed_out = receipt.get("timed_out")
    capacity_loss = receipt.get("capacity_loss")
    if status == "failed":
        _require(type(exit_code) is int and exit_code != 0 and timed_out is False and capacity_loss is None,
                 f"{group_id}: failed attempt status contradicts its process result")
    elif status == "timed-out":
        _require(exit_code == 124 and timed_out is True and capacity_loss is None,
                 f"{group_id}: timed-out status contradicts its process result")
    elif status == "capacity-lost":
        if c4_attempt:
            guard_error = _verify_resource_guard_error(
                group_id, capacity_loss, capacity_loss=True,
            )
            if c4_prelaunch_refusal:
                _require(exit_code == 125 and timed_out is False and
                         type(receipt.get("duration_seconds")) in (int, float) and
                         receipt["duration_seconds"] == 0,
                         f"{group_id}: C4 pre-launch capacity sentinel claims an analyzer result")
                _require(receipt.get("recorder_error") ==
                         f"DiskGuardError: {guard_error['message']}" and
                         receipt.get("snapshot_git_head") is None,
                         f"{group_id}: C4 pre-launch capacity detail differs from its guard receipt")
                _require(receipt.get("captured_files") == [] and receipt.get("reports") == [] and
                         receipt.get("failed_staging_artifacts") == [],
                         f"{group_id}: C4 pre-launch capacity receipt contains analyzer or staging evidence")
            elif c4_postprocess_capacity_failure:
                ownership = receipt["process_ownership"]
                _require(exit_code == 0 and timed_out is False and
                         ownership.get("cleanup_status") == "tracked-processes-stopped" and
                         receipt.get("recorder_error") ==
                         f"DiskGuardError: {guard_error['message']}" and
                         receipt.get("reports") == [] and
                         isinstance(receipt.get("failed_staging_artifacts"), list),
                         f"{group_id}: C4 post-process capacity receipt contradicts completed analyzer/staging failure")
        else:
            _require(type(exit_code) is int and type(timed_out) is bool and
                     isinstance(capacity_loss, str) and bool(capacity_loss),
                     f"{group_id}: capacity-lost status lacks the measured capacity failure")
    else:
        recorder_error = receipt.get("recorder_error")
        _require(isinstance(recorder_error, str) and bool(recorder_error.strip()),
                 f"{group_id}: recorder-error status lacks its failure detail")
        if c4_prelaunch_refusal:
            _require(exit_code == 125 and timed_out is False and
                     type(receipt.get("duration_seconds")) in (int, float) and
                     receipt["duration_seconds"] == 0 and capacity_loss is None and
                     receipt.get("snapshot_git_head") is None and
                     receipt.get("captured_files") == [] and receipt.get("reports") == [] and
                     receipt.get("failed_staging_artifacts") == [],
                     f"{group_id}: C4 pre-launch recorder failure claims analyzer evidence")
    if status != "recorder-error":
        duration = receipt.get("duration_seconds")
        _require(type(duration) in (int, float) and math.isfinite(duration) and duration >= 0,
                 f"{group_id}: failed attempt has invalid monotonic duration")

    captured = _read_capture_manifest(root, attempt_id, receipt)
    stream_summaries = {}
    allowed_attempt_files = {"started.json", "completed.json"}
    for field in ("stdout", "stderr"):
        stream = receipt.get(field)
        if stream is None and status == "recorder-error":
            stream_summaries[field] = None
            continue
        _require(isinstance(stream, dict) and stream.get("path") == f"{field}.txt",
                 f"{group_id}: failed attempt lacks exact {field} receipt")
        _bound(root, (ATTEMPTS_ROOT / attempt_id / stream["path"]).as_posix(),
               stream.get("sha256"), stream.get("bytes"), f"{group_id} failed {field}")
        stream_summaries[field] = {
            "sha256": stream["sha256"],
            "bytes": stream["bytes"],
        }
        if c4_prelaunch_refusal:
            _require(stream["bytes"] == 0,
                     f"{group_id}: C4 pre-launch refusal contains analyzer {field} output")
        allowed_attempt_files.add(stream["path"])
    allowed_attempt_files.update(f"capture/{relative}" for relative in captured)

    failed_staging_artifacts = receipt.get("failed_staging_artifacts", [])
    _require(isinstance(failed_staging_artifacts, list),
             f"{group_id}: failed_staging_artifacts must be a list")
    artifact_paths = []
    for index, artifact in enumerate(failed_staging_artifacts):
        _require(isinstance(artifact, dict) and set(artifact) == {"path", "sha256", "bytes"},
                 f"{group_id}: failed staging artifact {index} has an unsupported shape")
        relative = _relative(artifact.get("path"), f"{group_id} failed staging artifact path").as_posix()
        original_prefix = f"{(ATTEMPTS_ROOT / attempt_id / 'original').as_posix()}/"
        staged_prefix = f"{(NORMAL_ROOT / attempt_id).as_posix()}/"
        _require(relative.startswith(original_prefix) or relative.startswith(staged_prefix),
                 f"{group_id}: failed staging artifact escapes its original or staged attempt namespace")
        _bound(root, relative, artifact.get("sha256"), artifact.get("bytes"),
               f"{group_id} failed staging artifact")
        artifact_paths.append(relative)
    _require(len(artifact_paths) == len(set(artifact_paths)),
             f"{group_id}: duplicate failed staging artifact path")
    _require((status == "recorder-error" or c4_postprocess_capacity_failure) or not artifact_paths,
             f"{group_id}: non-recorder failure retains staging artifacts")

    original_root = attempt / "original"
    staged_root = root / Path(*NORMAL_ROOT.parts) / attempt_id
    _assert_no_symlink_path(root, attempt, f"{group_id} failed attempt")
    _assert_no_symlink_path(root, staged_root, f"{group_id} failed staged reports")
    _assert_no_symlink_path(root, attempt / "original", f"{group_id} failed originals")
    actual_original_files = _regular_files_under(original_root, f"{group_id} failed originals")
    actual_staged_files = _regular_files_under(staged_root, f"{group_id} failed staged reports")
    expected_original_files = {
        PurePosixPath(path).relative_to(ATTEMPTS_ROOT / attempt_id / "original").as_posix()
        for path in artifact_paths
        if PurePosixPath(path).is_relative_to(ATTEMPTS_ROOT / attempt_id / "original")
    }
    expected_failed_staged_files = {
        PurePosixPath(path).relative_to(NORMAL_ROOT / attempt_id).as_posix()
        for path in artifact_paths
        if PurePosixPath(path).is_relative_to(NORMAL_ROOT / attempt_id)
    }
    _require(actual_original_files == expected_original_files,
             f"{group_id}: failed originals differ from the exact recorder inventory")
    _require(actual_staged_files == expected_failed_staged_files,
             f"{group_id}: failed staged files differ from the exact recorder inventory")
    for path in expected_original_files:
        allowed_attempt_files.add(f"original/{path}")
    actual_attempt_files = _regular_files_under(attempt, f"{group_id} failed attempt receipt")
    _require(actual_attempt_files == allowed_attempt_files,
             f"{group_id}: failed attempt contains orphaned or unbound files")

    summary = {
        "group_id": group_id,
        "attempt_id": attempt_id,
        "attempt_number": attempt_number,
        "status": status,
        "contract_sha256": validated["bytes_sha256"],
        "plan_commit": plan_commit,
        "source_commit": plan["source_commit"],
        "ledger_line_sha256": ledger_line_sha256,
        "started_receipt_sha256": _sha((attempt / "started.json").read_bytes()),
        "completed_receipt_sha256": _sha(completed_bytes),
        "stdout": stream_summaries["stdout"],
        "stderr": stream_summaries["stderr"],
        "captured_files": [
            {"execution_relative": relative, "sha256": item["sha256"], "bytes": item["bytes"]}
            for relative, item in sorted(captured.items())
        ],
        "failed_staging_artifacts": [
            {"path": path, "sha256": item["sha256"], "bytes": item["bytes"]}
            for path, item in sorted(
                ((item["path"], item) for item in failed_staging_artifacts), key=lambda pair: pair[0],
            )
        ],
    }
    if c4_prelaunch_refusal:
        summary["analyzer_started"] = False
    elif c4_postprocess_capacity_failure:
        summary["analyzer_started"] = True
    return summary


def _assert_attempt_directories(root: Path, attempt_ids: set[str]) -> None:
    attempts_root = root / Path(*ATTEMPTS_ROOT.parts)
    _assert_no_symlink_path(root, attempts_root, "fresh attempt receipt root")
    _require(attempts_root.is_dir() and not attempts_root.is_symlink(),
             "fresh attempt receipt root is missing or symlinked")
    actual = set()
    for item in attempts_root.iterdir():
        _require(item.is_dir() and not item.is_symlink(),
                 f"unexpected non-directory entry in attempt root: {item.name}")
        actual.add(item.name)
    _require(actual == attempt_ids, "attempt directory set differs from the exact ledger attempts")


def _regular_files_under(root: Path, description: str) -> set[str]:
    _require(not root.is_symlink(), f"{description} root is symlinked")
    if not root.exists():
        return set()
    _require(root.is_dir(), f"{description} root is not a directory")
    actual = set()
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directories:
            _require(not (current_path / name).is_symlink(), f"symlink in {description}: {current_path / name}")
        for name in files:
            path = current_path / name
            _require(path.is_file() and not path.is_symlink(), f"non-regular file in {description}: {path}")
            actual.add(path.relative_to(root).as_posix())
    return actual


def _expected_staged_files(selected_report_paths: set[str], failed_summaries: list[dict]) -> set[str]:
    """Include hash-bound recorder leftovers while keeping them out of selected reports."""
    expected = {
        PurePosixPath(path).relative_to(NORMAL_ROOT).as_posix()
        for path in selected_report_paths
    }
    for failure in failed_summaries:
        for artifact in failure["failed_staging_artifacts"]:
            path = PurePosixPath(artifact["path"])
            if path.is_relative_to(NORMAL_ROOT):
                relative = path.relative_to(NORMAL_ROOT).as_posix()
                _require(relative not in expected,
                         "failed staging artifacts overlap selected completed-attempt reports")
                expected.add(relative)
    return expected


def _validate_wall_budget(ledger_rows: list[tuple[dict, str]], total_budget_seconds: object) -> float:
    _require(type(total_budget_seconds) in (int, float) and math.isfinite(total_budget_seconds)
             and total_budget_seconds > 0, "execution plan total wall budget is invalid")
    intervals = []
    for index, (row, _line_sha) in enumerate(ledger_rows, 1):
        try:
            start = _datetime.datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
            end = _datetime.datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00"))
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise EvidenceError(f"execution ledger attempt {index} lacks valid UTC timestamps") from exc
        _require(start.tzinfo is not None and end.tzinfo is not None and
                 start.utcoffset() == _datetime.timedelta(0) and end.utcoffset() == _datetime.timedelta(0),
                 f"execution ledger attempt {index} timestamps must use UTC")
        _require(end >= start, f"execution ledger attempt {index} ends before it starts")
        intervals.append((start, end))
    for previous, current in zip(intervals, intervals[1:]):
        _require(current[0] >= previous[1], "execution attempts overlap or are recorded out of execution order")
    elapsed = (max(end for _start, end in intervals) - min(start for start, _end in intervals)).total_seconds()
    _require(math.isfinite(elapsed) and elapsed <= total_budget_seconds,
             "full execution interval, including pauses and failed attempts, exceeds the registered wall budget")
    return elapsed


def _verify_preanalysis_failure_review(root: Path, current_validated: dict,
                                       prior_validated: dict, prior_contract_sha256: str,
                                       prior_plan_commit: str, receipt: dict,
                                       ledger_line_sha256: str, failure_summary: dict) -> str:
    """Bind the sole inherited failure to its reviewed version-gate evidence."""
    review_relative = PREANALYSIS_FAILURE_REVIEW.as_posix()
    review_path = root / Path(*PREANALYSIS_FAILURE_REVIEW.parts)
    _assert_no_symlink_path(root, review_path, "pre-analysis failure review")
    review, review_bytes = _read_json(review_path, "pre-analysis Bifrost version-gate review")
    source_inputs = current_validated.get("source_inputs")
    _require(isinstance(source_inputs, list), "successor contract lacks its source-input inventory")
    matches = [item for item in source_inputs
               if isinstance(item, dict) and item.get("path") == review_relative]
    _require(len(matches) == 1 and matches[0].get("sha256") == _sha(review_bytes),
             "successor contract does not bind the exact pre-analysis failure review")

    old_plan = prior_validated["plan"]
    _require(isinstance(review, dict) and
             review.get("schema") == "v092-preanalysis-version-gate-failure-review/v1" and
             review.get("attempt_id") == "bifrost-c-kernel-attempt-01-series-01" and
             review.get("status") == "recorder-error" and
             review.get("case_analysis_ran") is False and
             review.get("basis") == (
                 "stderr rejects exact two-line Bifrost version witness; stdout contains only validation "
                 "messages; no analyzer case outputs/report artifacts"
             ) and
             review.get("prior_contract") == {
                 "path": "reports/releases/v0.9.2/acquisition/failed-contract-01.json",
                 "sha256": prior_contract_sha256,
                 "plan_commit": prior_plan_commit,
             } and
             review.get("ledger_line_sha256") == ledger_line_sha256 and
             review.get("original_start_utc") == receipt.get("start_utc"),
             "pre-analysis failure review does not identify the exact prior version-gate attempt")
    expected_constraints = {
        "execution_series": old_plan["execution_series"],
        "maximum_attempts_per_group": 2,
        "total_wall_budget_seconds": old_plan["total_wall_budget_seconds"],
        "wall_origin_must_be_preserved": True,
        "no_report_carry_forward": True,
        "prior_failure_counts_as_attempt": True,
    }
    _require(review.get("constraints") == expected_constraints,
             "pre-analysis failure review does not preserve the series, retry, wall-budget, and no-carry constraints")
    _require(failure_summary.get("status") == "recorder-error" and
             failure_summary.get("attempt_id") == review["attempt_id"] and
             failure_summary.get("contract_sha256") == prior_contract_sha256 and
             failure_summary.get("plan_commit") == prior_plan_commit and
             failure_summary.get("ledger_line_sha256") == ledger_line_sha256 and
             failure_summary.get("started_receipt_sha256") is not None and
             failure_summary.get("completed_receipt_sha256") is not None,
             "verified predecessor failure differs from its pre-analysis review")

    attempt_root = f"reports/releases/v0.9.2/attempts/{review['attempt_id']}"
    expected_files = {
        f"{attempt_root}/completed.json": (failure_summary["completed_receipt_sha256"], None),
        f"{attempt_root}/started.json": (failure_summary["started_receipt_sha256"], None),
    }
    for stream in ("stdout", "stderr"):
        item = failure_summary.get(stream)
        _require(isinstance(item, dict), f"reviewed prior failure lacks its {stream} evidence")
        expected_files[f"{attempt_root}/{stream}.txt"] = (item.get("sha256"), item.get("bytes"))
    review_files = review.get("files")
    _require(isinstance(review_files, list) and len(review_files) == len(expected_files),
             "pre-analysis failure review must bind exactly the four attempt evidence files")
    actual_review_files = {}
    for item in review_files:
        _require(isinstance(item, dict) and set(item) == {"path", "sha256", "bytes"} and
                 isinstance(item.get("path"), str) and item["path"] not in actual_review_files and
                 isinstance(item.get("sha256"), str) and SHA256.fullmatch(item["sha256"]) is not None and
                 type(item.get("bytes")) is int and item["bytes"] >= 0,
                 "pre-analysis failure review file entry is malformed or duplicated")
        actual_review_files[item["path"]] = item
    _require(set(actual_review_files) == set(expected_files),
             "pre-analysis failure review file roster differs from the four expected attempt files")
    for relative, (expected_sha, expected_size) in expected_files.items():
        path = root / Path(*PurePosixPath(relative).parts)
        _require(path.is_file() and not path.is_symlink(), f"missing or symlinked reviewed failure file: {relative}")
        data = path.read_bytes()
        item = actual_review_files[relative]
        _require(_sha(data) == item["sha256"] and len(data) == item["bytes"] and
                 item["sha256"] == expected_sha and
                 (expected_size is None or item["bytes"] == expected_size),
                 f"pre-analysis failure review differs from verified attempt file: {relative}")
    return _sha(review_bytes)


def verify(root: str | Path = ROOT, contract_path: str | Path | None = None) -> dict:
    root = Path(root).resolve()
    contract_input = Path(contract_path) if contract_path is not None else Path(*CONTRACT_PATH.parts)
    if not contract_input.is_absolute():
        contract_input = root / contract_input
    _require(not contract_input.is_symlink(), "execution contract must not be a symlink")
    contract = contract_input.resolve()
    try:
        validated = EXECUTOR.validate_plan(contract, repo_root=root)
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc
    plan = validated["plan"]
    _require(plan.get("execution_authorized") is True, "execution contract is not authorized")
    _require(plan.get("release") == RELEASE, "execution contract is not for v0.9.2")
    _require(not any(key in plan for key in ("carried_reports", "carry_forward", "inherited_reports")),
             "v0.9.2 contract must not carry forward reports")
    parent = validated["parent_plan"]
    groups = {item["id"]: item for item in plan["groups"]}
    _require(len(groups) == EXPECTED_GROUPS and len(validated["groups"]) == EXPECTED_GROUPS,
             "contract must bind all 84 fresh execution groups")
    _require(len(parent["reports"]) == EXPECTED_REPORTS, "immutable parent partition map changed")
    population, _ = _read_json(root / POPULATION_PATH, "v0.9.0 population")
    _require(isinstance(population, dict) and population.get("population") == "v0.9.0",
             "v0.9.0 source population is missing")
    cases = population.get("cases")
    case_ids = [case.get("id") for case in cases if isinstance(case, dict)] if isinstance(cases, list) else []
    _require(len(case_ids) == EXPECTED_CASES and len(set(case_ids)) == EXPECTED_CASES,
             "source population must contain exactly 1,108 unique cases")
    _require(plan["population"]["sha256"] == _sha((root / POPULATION_PATH).read_bytes()),
             "execution contract population digest differs from v0.9.0 population bytes")

    ledger_path = root / Path(*LEDGER_PATH.parts)
    ledger_rows = _read_ledger_with_hashes(ledger_path)
    scoped_mode = "scoped_recovery" in plan
    resource_mode = "resource_recovery" in plan
    _require(not (scoped_mode and resource_mode),
             "execution contract cannot combine C3 scoped recovery and C4 resource recovery")
    recovery_mode = scoped_mode or resource_mode
    scoped = validated.get("scoped_recovery") if scoped_mode else None
    resource = validated.get("resource_recovery") if resource_mode else None
    if resource_mode:
        try:
            current_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.STDOUT,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise EvidenceError("cannot resolve current source HEAD for resource-recovery history") from exc
        _require(isinstance(resource, dict), "C4 execution contract lacks validated resource-recovery context")
        _verify_resource_recovery_bundle(root, validated, ledger_rows, resource, current_head)
        plan_commit, selected_attempts, prior_failures = _select_resource_recovery_attempts(
            plan, validated["bytes_sha256"], ledger_rows, resource,
        )
    elif scoped_mode:
        _require(isinstance(scoped, dict), "C3 execution contract lacks validated scoped-recovery context")
        _verify_scoped_recovery_bundle(root, validated, ledger_rows, scoped)
        plan_commit, selected_attempts, prior_failures = _select_scoped_recovery_attempts(
            plan, validated["bytes_sha256"], ledger_rows, scoped,
        )
    else:
        plan_commit, selected_attempts, prior_failures = _select_attempts(
            plan, validated["bytes_sha256"], ledger_rows,
            validated.get("prior_failed_contracts", {}),
        )
    expected_ids = set(groups)
    _require(set(selected_attempts) == expected_ids,
             "ledger must select exactly one completed attempt for each of 84 groups")
    _assert_committed_contract(root, validated, plan_commit)
    if scoped_mode:
        try:
            current_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.STDOUT,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise EvidenceError("cannot resolve current source HEAD for scoped historical proof") from exc
        _verify_historical_contract_contexts(
            root, scoped["manifest"], scoped, current_head,
        )
    all_attempt_ids = {row["attempt_id"] for row, _line_sha in ledger_rows}
    _assert_attempt_directories(root, all_attempt_ids)
    try:
        EXECUTOR._assert_source_snapshot(root, plan["source_commit"], plan["runner_source_sha256"], validated["source_inputs"])
    except EXECUTOR.ReleaseError as exc:
        raise EvidenceError(str(exc)) from exc

    bound_reports = []
    outcome_counts: collections.Counter = collections.Counter()
    report_paths = set()
    staged_report_paths = set()
    row_count = 0
    selected_summaries = []
    for group_id in sorted(selected_attempts):
        selected = selected_attempts[group_id]
        if recovery_mode:
            (receipt, ledger_line_sha256, attempt_number, origin_validated,
             origin_plan_commit, origin_contract_sha256, retained) = selected
            evidence_validated = origin_validated or validated
            origin_groups = {item["id"]: item for item in evidence_validated["groups"]}
            group = origin_groups[group_id]
        else:
            receipt, ledger_line_sha256, attempt_number = selected
            origin_validated = None
            origin_plan_commit = plan_commit
            origin_contract_sha256 = validated["bytes_sha256"]
            retained = False
            evidence_validated = validated
            group = groups[group_id]
        bindings, counts = _verify_one_group(
            root, evidence_validated, group, receipt, origin_plan_commit, attempt_number,
        )
        completed_bytes = (root / Path(*ATTEMPTS_ROOT.parts) / receipt["attempt_id"] / "completed.json").read_bytes()
        if recovery_mode and retained:
            recovery_manifest = resource["manifest"] if resource_mode else scoped["manifest"]
            retained_item = next(item for item in recovery_manifest["retained_completed"]
                                 if item["attempt_id"] == receipt["attempt_id"])
            _require(_sha(completed_bytes) == retained_item["completed_receipt"]["sha256"],
                     f"{group_id}: selected historical completion differs from its manifest receipt digest")
            started_bytes = (root / Path(*ATTEMPTS_ROOT.parts) / receipt["attempt_id"] / "started.json").read_bytes()
            _require(_sha(started_bytes) == retained_item["started_receipt"]["sha256"],
                     f"{group_id}: selected historical start differs from its manifest receipt digest")
        for binding in bindings:
            _require(binding["adapter"] not in report_paths, "report partition was emitted more than once")
            report_paths.add(binding["adapter"])
            _require(binding["staged_path"] not in staged_report_paths,
                     "staged report path was emitted more than once")
            staged_report_paths.add(binding["staged_path"])
            row_count += binding["rows"]
            binding["attempt_id"] = receipt["attempt_id"]
            binding["attempt_number"] = attempt_number
            binding["evidence_contract_sha256"] = origin_contract_sha256
            bound_reports.append(binding)
        outcome_counts.update(counts)
        selected_summaries.append({
            "group_id": group_id,
            "attempt_id": receipt["attempt_id"],
            "attempt_number": attempt_number,
            "status": "completed",
            "evidence_origin": (
                ("retained-c3" if origin_contract_sha256 == RESOURCE_C3_SHA256 else "retained-c2")
                if resource_mode and retained else
                ("fresh-c4" if resource_mode else
                 ("retained-c2" if retained else ("fresh-c3" if scoped_mode else "current-contract")))
            ),
            "evidence_contract_sha256": origin_contract_sha256,
            "evidence_plan_commit": origin_plan_commit,
            "ledger_line_sha256": ledger_line_sha256,
            "started_receipt_sha256": _sha((root / Path(*ATTEMPTS_ROOT.parts) /
                                             receipt["attempt_id"] / "started.json").read_bytes()),
            "completed_receipt_sha256": _sha(completed_bytes),
        })

    failed_summaries = []
    prior_failure_summary_rows = []
    scoped_failure_summary_rows = []
    for (receipt, ledger_line_sha256, attempt_number, origin_validated,
         origin_plan_commit, expected_receipt_sha256, origin_contract_sha256) in prior_failures:
        failure_validated = origin_validated or validated
        failure_groups = {item["id"]: item for item in failure_validated["groups"]}
        group = failure_groups[receipt["group_id"]]
        failure_summary = _verify_failed_attempt(
            root, failure_validated, group, receipt, origin_plan_commit,
            attempt_number, ledger_line_sha256, expected_receipt_sha256,
        )
        failure_summary["inherited_from_prior_contract"] = origin_contract_sha256 != validated["bytes_sha256"]
        if recovery_mode:
            c1_sha = next(
                item["sha256"] for item in scoped["manifest"]["historical_contracts"]
                if item["canonical_path"].endswith("execution-v1/contract.json")
            ) if scoped_mode else RESOURCE_C1_SHA256
            if origin_contract_sha256 == c1_sha:
                failure_summary["evidence_origin"] = "retained-c1-failure"
                review_sha256 = _verify_preanalysis_failure_review(
                    root, validated, failure_validated, origin_contract_sha256,
                    origin_plan_commit, receipt, ledger_line_sha256, failure_summary,
                )
                failure_summary["version_gate_review"] = {
                    "path": PREANALYSIS_FAILURE_REVIEW.as_posix(),
                    "sha256": review_sha256,
                }
            elif failure_summary["inherited_from_prior_contract"]:
                failure_summary["evidence_origin"] = "retained-c2-failure"
                failure_summary["failure_diagnosis"] = _verify_codeql_modeling_failure_diagnosis(
                    root,
                    (scoped["manifest"] if scoped_mode else
                     resource["contexts"][RESOURCE_C3_SHA256]["validated"]["scoped_recovery"]["manifest"]),
                    failure_summary,
                )
            else:
                failure_summary["evidence_origin"] = "fresh-c4-failure" if resource_mode else "fresh-c3-failure"
            if failure_summary["inherited_from_prior_contract"]:
                scoped_failure_summary_rows.append(failure_summary)
        elif failure_summary["inherited_from_prior_contract"]:
            review_sha256 = _verify_preanalysis_failure_review(
                root, validated, failure_validated, origin_contract_sha256,
                origin_plan_commit, receipt, ledger_line_sha256, failure_summary,
            )
            failure_summary["version_gate_review"] = {
                "path": PREANALYSIS_FAILURE_REVIEW.as_posix(),
                "sha256": review_sha256,
            }
        failed_summaries.append(failure_summary)
        if failure_summary["inherited_from_prior_contract"] and not recovery_mode:
            prior_failure_summary_rows.append(failure_summary)
    _require(len(failed_summaries) == len(prior_failures),
             "one or more prior failed attempts lack verifiable non-selected provenance")
    execution_interval_seconds = _validate_wall_budget(
        ledger_rows, validated["total_wall_budget_seconds"],
    )
    normal_root = root / Path(*NORMAL_ROOT.parts)
    _assert_no_symlink_path(root, normal_root, "normalized report staging")
    all_stage_files = _regular_files_under(normal_root, "normalized report staging")
    expected_stage_files = _expected_staged_files(staged_report_paths, failed_summaries)
    _require(all_stage_files == expected_stage_files,
             "staged report files differ from the 92 selected completed-attempt reports")
    expected_paths = {
        report["report"].replace(
            "reports/releases/v0.9.0/normal/", "reports/releases/v0.9.2/normal/", 1,
        )
        for report in parent["reports"]
    }
    # Contracts use the fresh v0.9.2 staging destination but preserve every
    # immutable v0.9.0 report stem and partition membership.
    _require(len(report_paths) == EXPECTED_REPORTS and report_paths == expected_paths,
             "fresh reports do not preserve the exact 92 historical report paths")
    _require(row_count == EXPECTED_ROWS, f"fresh matrix contains {row_count} rows, expected {EXPECTED_ROWS}")
    _require(sum(outcome_counts.values()) == EXPECTED_ROWS, "typed outcomes do not cover exactly 4,252 fresh report rows")

    completed = EXECUTOR._verified_completed_groups(validated)
    _require(completed == expected_ids, "executor's durable receipt verifier rejected one or more fresh groups")
    prior_contract_summaries = []
    for contract_sha256, binding in sorted(validated.get("prior_failed_contracts", {}).items()):
        old_validated = binding["validated"]
        prior_ref = next(item for item in plan.get("prior_failed_contracts", [])
                         if item.get("sha256") == contract_sha256)
        prior_contract_summaries.append({
            "path": prior_ref["path"],
            "contract_sha256": contract_sha256,
            "plan_commit": binding["plan_commit"],
            "source_commit": old_validated["plan"]["source_commit"],
            "attempts": [
                {
                    "attempt_id": failure["attempt_id"],
                    "status": failure["status"],
                    "ledger_line_sha256": failure["ledger_line_sha256"],
                    "completed_receipt_sha256": failure["completed_receipt_sha256"],
                    "version_gate_review": failure.get("version_gate_review"),
                }
                for failure in prior_failure_summary_rows
                if failure["contract_sha256"] == contract_sha256
            ],
        })
    _require(all(item["attempts"] for item in prior_contract_summaries),
             "a registered prior contract has no independently verified failed attempt")
    scoped_summary = None
    resource_summary = None
    if scoped_mode:
        _require(len(selected_summaries) == EXPECTED_GROUPS and
                 sum(item["evidence_origin"] == "retained-c2" for item in selected_summaries) == 25 and
                 sum(item["evidence_origin"] == "fresh-c3" for item in selected_summaries) == 59,
                 "C3 selection must preserve exactly 25 C2 completions and verify 59 C3 completions")
        _require(len(scoped_failure_summary_rows) == 2 and
                 {item["evidence_origin"] for item in scoped_failure_summary_rows} ==
                 {"retained-c1-failure", "retained-c2-failure"},
                 "C3 summary does not retain exactly the authorized C1 and C2 failures")
        scoped_summary = {
            "manifest": plan["scoped_recovery"]["path"],
            "manifest_sha256": plan["scoped_recovery"]["sha256"],
            "sealed_prefix_sha256": scoped["sealed_prefix_sha256"],
            "retained_completed_groups": 25,
            "retained_failures": [
                {
                    "attempt_id": item["attempt_id"],
                    "status": item["status"],
                    "contract_sha256": item["contract_sha256"],
                    "plan_commit": item["plan_commit"],
                    "ledger_line_sha256": item["ledger_line_sha256"],
                    "evidence_origin": item["evidence_origin"],
                    "version_gate_review": item.get("version_gate_review"),
                    "failure_diagnosis": item.get("failure_diagnosis"),
                }
                for item in scoped_failure_summary_rows
            ],
        }
    if resource_mode:
        _require(len(selected_summaries) == EXPECTED_GROUPS and
                 sum(item["evidence_origin"] == "retained-c2" for item in selected_summaries) == 25 and
                 sum(item["evidence_origin"] == "retained-c3" for item in selected_summaries) == 30 and
                 sum(item["evidence_origin"] == "fresh-c4" for item in selected_summaries) == 29,
                 "C4 selection must preserve 25 C2 plus 30 C3 completions and verify 29 C4 completions")
        _require(len(scoped_failure_summary_rows) == 2 and
                 {item["evidence_origin"] for item in scoped_failure_summary_rows} ==
                 {"retained-c1-failure", "retained-c2-failure"},
                 "C4 summary does not retain the exact two original C1/C2 failures")
        resource_summary = {
            "manifest": plan["resource_recovery"]["path"],
            "manifest_sha256": plan["resource_recovery"]["sha256"],
            "sealed_prefix_sha256": resource["sealed_prefix_sha256"],
            "retained_completed_groups": 55,
            "retained_c2_completed_groups": 25,
            "retained_c3_completed_groups": 30,
            "fresh_c4_completed_groups": 29,
            "original_c3": {
                "contract_sha256": RESOURCE_C3_SHA256,
                "path": RESOURCE_C3_ARCHIVE_PATH.as_posix(),
                "plan_commit": RESOURCE_C3_PLAN_COMMIT,
                "source_commit": RESOURCE_C3_SOURCE_COMMIT,
            },
            "retained_failures": [
                {
                    "attempt_id": item["attempt_id"],
                    "status": item["status"],
                    "contract_sha256": item["contract_sha256"],
                    "plan_commit": item["plan_commit"],
                    "ledger_line_sha256": item["ledger_line_sha256"],
                    "evidence_origin": item["evidence_origin"],
                    "version_gate_review": item.get("version_gate_review"),
                    "failure_diagnosis": item.get("failure_diagnosis"),
                }
                for item in scoped_failure_summary_rows
            ],
        }
    result = {
        "schema_version": 1,
        "release": RELEASE,
        "status": "fresh-evidence-verified",
        "release_freeze_created": False,
        "published": False,
        "contract_sha256": validated["bytes_sha256"],
        "plan_commit": plan_commit,
        "source_commit": plan["source_commit"],
        "ledger_sha256": _sha(ledger_path.read_bytes()),
        "case_count": EXPECTED_CASES,
        "fresh_groups": EXPECTED_GROUPS,
        "fresh_attempts": len(ledger_rows),
        "execution_interval_seconds": execution_interval_seconds,
        "fresh_partitions": EXPECTED_REPORTS,
        "fresh_rows": EXPECTED_ROWS,
        "carried_partitions": 0,
        "carried_rows": 0,
        "selected_attempts": selected_summaries,
        "failed_attempt_count": len(failed_summaries),
        "failed_attempts": failed_summaries,
        "prior_failed_contracts": prior_contract_summaries,
        "scoped_recovery": scoped_summary,
        "resource_recovery": resource_summary,
        "typed_outcomes": dict(sorted(outcome_counts.items())),
        "fresh_reports": sorted(bound_reports, key=lambda item: item["adapter"]),
        "configuration_hash_validation": {
            "swift_common108": "exact versioned plan closure independently rehashed",
            "other_reports": (
                "source-and-harness-bound; canonical Rust revalidation required; "
                "native hashes may be NotDerivable"
            ),
            "canonical_rust_validate_reports": "required separate final-delivery gate",
        },
        "performance_claim": "none; execution timings are diagnostic",
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path(*CONTRACT_PATH.parts))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    try:
        result = verify(ROOT, args.contract)
        if args.check:
            prior, _ = _read_json(args.check, "expected evidence summary")
            _require(prior == result, "evidence summary differs from recomputed artifacts")
        if args.output:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (EvidenceError, OSError, ValueError) as exc:
        raise SystemExit(str(exc))
    print(json.dumps({key: result[key] for key in ("status", "fresh_groups", "fresh_partitions", "fresh_rows", "carried_rows")}))
