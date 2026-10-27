#!/usr/bin/env python3
"""Append-only CodeQL Swift continuation from the sealed v0.9.2 ledger prefix.

This module is deliberately independent of the Joern continuation scheduler.
It validates the immutable 88-row prefix, admits at most one fresh CodeQL row,
and delegates source, lock, process, disk, and report checks to the frozen
executor/checker.  It does not infer a Joern completion and it never changes
the historical 82 completed-group count.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[4]
BASE_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
BASE_SHA = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
MODULE_SOURCE = "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py"
SUPERVISOR_SOURCE = "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-03.py"
CONTRACT = "reports/releases/v0.9.2/execution-v4/continuations/codeql-independent-pending-03-contract.json"
MANIFEST = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-manifest-03.json"
PROVISIONAL_MANIFEST = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-admission-03.json"
LEDGER = "reports/releases/v0.9.2/ledger-v1.jsonl"
SEALED_LEDGER = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/sealed-ledger-prefix-88.jsonl"
SEALED_LEDGER_SHA = "9ae98c51570149cc7ebe86573df518b4f469188e23dd58d7bcdc37ac93532476"
SEALED_ROWS = 88
HISTORICAL_COMPLETED = 82
CODEQL_GROUP = "codeql-swift-common108"
CODEQL_ATTEMPT = "codeql-swift-common108-attempt-01-series-01"
EXECUTION_SERIES = 1
CODEQL_MAX_ATTEMPTS = 2
CODEQL_DEADLINE_SECONDS = 13840
STARTUP_ALLOWANCE_SECONDS = 30
ORIGIN = "2026-10-20T00:57:00.680937+00:00"
FULL_REMAINING_RESERVE_SECONDS = 29400
CODEQL_REMAINING_RESERVE_SECONDS = 28032
LIVE_RESOURCE_FLOOR_BYTES = 127 * 1024**3
SOURCE_PROJECTION_MAX_BYTES = 12 * 1024**3
SOURCE_WORKING_CAP_BYTES = 30 * 1024**3
WORKING_SET_GIB = 30
STOP_FREE_GIB = 48
CODEQL_OUTPUT_ROOT = "reports/raw/swift-common-v2/current108-v092-01"
QUERY_RECEIPT = "reports/releases/v0.9.2/qualification/codeql-swift-common108/query-check-02/receipt.json"
QUERY_RECEIPT_SHA = "62b934fb5546296ebd790bb952a169a8fe8ea59c9e056ea377c839cfcf3fa468"
NO_EXPIRY_AUTH = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json"
NO_EXPIRY_AUTH_SHA = "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc"
SOURCE_CAP_AUTH = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/source-working-cap-30gib-authorization-01.json"
SOURCE_CAP_AUTH_SHA = "bcba59ae10ea1cea565641249a0dc3bddfd063c66f298e19ce2ce0b86743cdbe"
BREADTH_AUTH = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/authorization-01.json"
BREADTH_AUTH_SHA = "0f8413d52c348a9d89079c70d8cebdea3179c35a8b84a98d390c53227e6f5478"
ADMISSION_RECEIPT = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/execution-admission-codeql-03.json"
FINAL_REVIEW = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/final-codeql-independent-review-03.json"
CONTROL_REVIEW = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/control-review-codeql-03.json"
SUPERVISOR_STATE = "execution-state/v092/independent-codeql-supervision-03"
SUPERVISOR_PUBLIC = "reports/releases/v0.9.2/execution-v4/independent-codeql-supervision-03"
MATERIALIZED_SOURCE = "execution-state/v092/independent-codeql-materialized-03"
MATERIALIZED_PREFLIGHT = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/materialized-preflight-codeql-03.json"
FROZEN_EXECUTOR = ("scripts/execute-release-v092.py", "fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8")
FROZEN_CHECKER = ("scripts/check-release-v092.py", "0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928")
FROZEN_CONFIGURATION = ("scripts/validate-v092-report-configurations.py", "21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858")
FROZEN_DISK_GUARD = ("scripts/v092_disk_guard.py", "fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21")
CF_USER_TEXT_ENCODING = "0x1F5:0x0:0x0"
# Immutable contexts for the six historical non-completed rows.  These are
# replay inputs only; this CodeQL-only successor never schedules Joern.
HISTORICAL_CONTEXT_SPECS = {
    "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3": (
        "reports/releases/v0.9.2/acquisition/failed-contract-01.json",
        "c5837c0e5b3b809cae3f347a748ef2fd03e3090f",
    ),
    "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422": (
        "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json",
        "a180c302b56f2c18a1fdfbbd1bc14489151fc54e",
    ),
    BASE_SHA: (BASE_CONTRACT, BASE_PLAN_COMMIT),
    "5a9aa55014847fdedce612429c4b856213ac228d59418e95e302483a472ca827": (
        "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-04-contract.json",
        "ce3db41d69c452d65a43f9c14b56706e2876e507",
    ),
    "1014ceb38510222d32887a17780d3a612afad80c5250714b0e60dc90f3cd37c3": (
        "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-08-contract.json",
        "9b71cce939ac74d9674be189ee03dbee14b868e9",
    ),
}
# Frozen C4's packet stores only its C1/C2/C3 predecessors.  The runtime
# successor nevertheless has to register every contract revision represented
# by the sealed 88-row ledger: C1/C2/C3, C4, and the normalized Joern03/04
# contexts.  The prospective CodeQL contract is registered separately by the
# frozen elapsed-wall guard from ``successor["bytes_sha256"]``.
HISTORICAL_RESOURCE_CONTRACT_SHA = (
    "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063"
)
HISTORICAL_C1_SHA = next(
    digest for digest, spec in HISTORICAL_CONTEXT_SPECS.items()
    if spec[0].endswith("acquisition/failed-contract-01.json")
)
HISTORICAL_C2_SHA = next(
    digest for digest, spec in HISTORICAL_CONTEXT_SPECS.items()
    if spec[0].endswith("acquisition/scoped-recovery-contract-02.json")
)
EXPECTED_HISTORICAL_CONTEXT_SHAS = frozenset({
    HISTORICAL_C1_SHA, HISTORICAL_C2_SHA, HISTORICAL_RESOURCE_CONTRACT_SHA,
    BASE_SHA,
    "5a9aa55014847fdedce612429c4b856213ac228d59418e95e302483a472ca827",
    "1014ceb38510222d32887a17780d3a612afad80c5250714b0e60dc90f3cd37c3",
})
HISTORICAL_REPLAY_PREVIOUS_SOURCE = (
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py"
)
HISTORICAL_REPLAY_PREVIOUS_SOURCE_SHA = (
    "712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa"
)
HISTORICAL_REPLAY_SOURCE = (
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py"
)
HISTORICAL_REPLAY_SOURCE_SHA = (
    "848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6"
)
HISTORICAL_REPLAY_MANIFEST = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "continuation-manifest-06.json"
)
HISTORICAL_REPLAY_MANIFEST_SHA = (
    "96cc7331c6043f270b07398dc546e07688e6df99c024c1b9da48a0782cd714ce"
)
HISTORICAL_REPLAY_CONTRACT = (
    "reports/releases/v0.9.2/execution-v4/continuations/"
    "joern-capability-repair-08-contract.json"
)
HISTORICAL_REPLAY_CONTRACT_SHA = (
    "1014ceb38510222d32887a17780d3a612afad80c5250714b0e60dc90f3cd37c3"
)
HISTORICAL_REPLAY_PREVIOUS_MANIFEST = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "continuation-manifest-02.json"
)
HISTORICAL_REPLAY_PREVIOUS_MANIFEST_SHA = (
    "fa81d5f6aee3cf5099eab6aeafabcbf59c3020b9cc2cdbe88a19a56167e2b73f"
)
HISTORICAL_REPLAY_PREVIOUS_CONTRACT = (
    "reports/releases/v0.9.2/execution-v4/continuations/"
    "joern-capability-repair-04-contract.json"
)
HISTORICAL_REPLAY_PREVIOUS_CONTRACT_SHA = (
    "5a9aa55014847fdedce612429c4b856213ac228d59418e95e302483a472ca827"
)
RE_SHA = re.compile(r"[0-9a-f]{64}\Z")
RE_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
RE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class CodeQLContinuationError(ValueError):
    """An independent CodeQL continuation input failed closed validation."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise CodeQLContinuationError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    try:
        return sha_bytes(path.read_bytes())
    except OSError as exc:
        raise CodeQLContinuationError(f"cannot hash {path}: {exc}") from exc


def _git_blob(root: Path, commit: str, relative: str, description: str) -> bytes:
    require(RE_COMMIT.fullmatch(str(commit or "")),
            f"{description} commit is malformed")
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{commit}:{relative}"], cwd=root,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CodeQLContinuationError(
            f"{description} is absent from its registered commit: {relative}"
        ) from exc
    return raw


def _relative(value: object, description: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{description} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts),
            f"{description} is unsafe")
    return path


def _path(root: Path, value: object, description: str = "path") -> Path:
    path = root
    for part in _relative(value, description).parts:
        path = path / part
        require(not path.is_symlink(), f"symlink in {description}: {value}")
    return path


def _read(root: Path, value: object, description: str = "file") -> bytes:
    path = _path(root, value, description)
    require(path.is_file(), f"missing {description}: {value}")
    return path.read_bytes()


def _json(root: Path, value: object, description: str = "JSON") -> dict[str, Any]:
    try:
        result = json.loads(_read(root, value, description))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CodeQLContinuationError(f"invalid {description}: {value}") from exc
    require(isinstance(result, dict), f"{description} must be an object: {value}")
    return result


def _ref(root: Path, value: object, description: str = "binding") -> bytes:
    require(isinstance(value, dict) and set(value) == {"path", "sha256"},
            f"{description} must be an exact path/SHA binding")
    path, digest = value.get("path"), value.get("sha256")
    require(isinstance(path, str) and RE_SHA.fullmatch(str(digest or "")),
            f"{description} has malformed path/SHA")
    raw = _read(root, path, description)
    require(sha_bytes(raw) == digest, f"{description} digest changed: {path}")
    return raw


def _load_module(root: Path, relative: str, name: str) -> Any:
    path = _path(root, relative, "module")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load frozen module: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_frozen(root: Path) -> dict[str, Any]:
    # Verify bytes before executing import-time module code.
    for relative, expected in (FROZEN_EXECUTOR, FROZEN_CHECKER,
                               FROZEN_CONFIGURATION, FROZEN_DISK_GUARD):
        require(sha(_path(root, relative)) == expected,
                f"frozen source changed: {relative}")
    executor = _load_module(root, FROZEN_EXECUTOR[0], "codeql_pending_executor")
    checker = _load_module(root, FROZEN_CHECKER[0], "codeql_pending_checker")
    configuration = _load_module(root, FROZEN_CONFIGURATION[0], "codeql_pending_configuration")
    disk_guard = _load_module(root, FROZEN_DISK_GUARD[0], "codeql_pending_disk_guard")
    return {"executor": executor, "checker": checker, "configuration": configuration,
            "disk_guard": disk_guard}


def _parse_ledger(raw: bytes) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CodeQLContinuationError("ledger is not valid JSONL") from exc
    require(all(isinstance(row, dict) for row in rows), "ledger contains a non-object row")
    return rows


def _ledger(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    raw = _read(root, LEDGER, "live ledger")
    sealed = _read(root, SEALED_LEDGER, "sealed ledger prefix")
    require(sha_bytes(sealed) == SEALED_LEDGER_SHA and len(sealed.splitlines()) == SEALED_ROWS,
            "sealed ledger prefix binding changed")
    lines = raw.splitlines(keepends=True)
    require(len(lines) in {SEALED_ROWS, SEALED_ROWS + 1},
            "CodeQL continuation ledger must contain only the sealed prefix or one tail row")
    require(b"".join(lines[:SEALED_ROWS]) == sealed,
            "live ledger does not begin with the exact sealed 88-row prefix")
    rows = _parse_ledger(raw)
    require(len(rows) == len(lines), "ledger JSON rows and bytes differ")
    return raw, rows


def _check_prefix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prefix = rows[:SEALED_ROWS]
    require(len(prefix) == SEALED_ROWS and
            sum(row.get("status") == "completed" for row in prefix) == HISTORICAL_COMPLETED and
            sum(row.get("status") != "completed" for row in prefix) == 6,
            "historical CodeQL prefix completion count changed")
    require(all(row.get("execution_series") == EXECUTION_SERIES for row in prefix),
            "historical CodeQL prefix execution series changed")
    return prefix


def _attempt_number(attempt_id: object) -> int:
    match = re.fullmatch(r".+-attempt-(\d+)-series-\d+", str(attempt_id))
    require(match is not None, f"malformed attempt id: {attempt_id}")
    return int(match.group(1))


def _tail(rows: list[dict[str, Any]], *, final: bool) -> list[dict[str, Any]]:
    tail = rows[SEALED_ROWS:]
    require(len(tail) <= 1, "CodeQL-only continuation appended more than one row")
    if tail:
        row = tail[0]
        require(row.get("group_id") == CODEQL_GROUP and
                row.get("attempt_id") == CODEQL_ATTEMPT and
                row.get("execution_series") == EXECUTION_SERIES and
                _attempt_number(row.get("attempt_id")) == 1 and
                (row.get("attempt_number") is None or row.get("attempt_number") == 1),
                "CodeQL-only tail is not the exact first CodeQL attempt")
        if row.get("status") == "completed":
            require(row.get("exit_code") == 0 and row.get("timed_out") is False and
                    row.get("capacity_loss") is None,
                    "completed CodeQL tail has a non-success terminal state")
        else:
            require(row.get("status") in {"failed", "timed-out", "capacity-lost", "recorder-error"},
                    "CodeQL tail is neither successful nor a reviewed terminal failure")
    if final:
        require(len(tail) == 1, "final CodeQL continuation is incomplete")
        if tail[0].get("status") == "completed":
            require(tail[0].get("exit_code") == 0 and tail[0].get("timed_out") is False and
                    tail[0].get("capacity_loss") is None,
                    "final CodeQL continuation has a non-success terminal state")
    return tail


def selected(rows: list[dict[str, Any]], *, final: bool) -> dict[str, dict[str, Any]]:
    _check_prefix(rows)
    tail = _tail(rows, final=final)
    result = {row["group_id"]: row for row in rows[:SEALED_ROWS]
              if row.get("status") == "completed"}
    require(len(result) == HISTORICAL_COMPLETED, "historical selected group count changed")
    if final and tail and tail[0].get("status") == "completed":
        result[CODEQL_GROUP] = tail[0]
    require(len(result) == HISTORICAL_COMPLETED +
            (1 if final and tail and tail[0].get("status") == "completed" else 0),
            "CodeQL selected group count changed")
    return result


def _base_group(contract: dict[str, Any]) -> dict[str, Any]:
    groups = contract.get("groups")
    require(isinstance(groups, list), "base contract group roster is missing")
    for group in groups:
        if isinstance(group, dict) and group.get("id") == CODEQL_GROUP:
            return group
    raise CodeQLContinuationError("base contract lacks the CodeQL Swift group")


def _check_authorization(root: Path, manifest: dict[str, Any]) -> None:
    for key, path, digest in (("no_expiry_authorization", NO_EXPIRY_AUTH, NO_EXPIRY_AUTH_SHA),
                               ("source_working_cap_authorization", SOURCE_CAP_AUTH, SOURCE_CAP_AUTH_SHA),
                               ("breadth_first_authorization", BREADTH_AUTH, BREADTH_AUTH_SHA)):
        item = manifest.get(key)
        require(item == {"path": path, "sha256": digest}, f"manifest does not bind exact {key}")
        _ref(root, item, key)
    auth = _json(root, NO_EXPIRY_AUTH, "no-expiry authorization")
    require(auth.get("schema") == "v092-no-user-execution-window-authorization/v1" and
            auth.get("execution_window", {}).get("mode") == "no-user-imposed-expiry",
            "no-expiry authorization is not the reviewed policy")
    cap = _json(root, SOURCE_CAP_AUTH, "source-working authorization")
    require(cap.get("authorized_change", {}).get("after_bytes") == SOURCE_WORKING_CAP_BYTES and
            cap.get("authorized_change", {}).get("unit") == "GiB",
            "aggregate source-working authorization is not 30 GiB")
    breadth = _json(root, BREADTH_AUTH, "breadth-first authorization")
    require(breadth.get("schema") == "v092-breadth-first-reviewed-scheduling-authorization/v1" and
            breadth.get("fabricated_original84_success_forbidden") is True and
            breadth.get("aggregate_source_working_gib") == 30 and
            breadth.get("per_source_snapshot_gib") == 12,
            "breadth-first authorization is not the reviewed independent schedule")


def _check_execution_window(value: object) -> None:
    require(isinstance(value, dict) and value.get("mode") == "no-user-imposed-expiry" and
            value.get("cutoff_utc") is None and value.get("total_wall_budget_seconds") is None,
            "CodeQL contract does not preserve the reviewed no-expiry window")
    require(value.get("original_origin_utc") == ORIGIN and
            value.get("phase_remaining_reserved_seconds") == CODEQL_REMAINING_RESERVE_SECONDS and
            value.get("per_attempt_timeout_seconds") == CODEQL_DEADLINE_SECONDS and
            value.get("startup_allowance_seconds") == STARTUP_ALLOWANCE_SECONDS,
            "CodeQL no-expiry lease or phase reserve changed")


def _check_contract_delta(root: Path, base: dict[str, Any], contract: dict[str, Any], manifest: dict[str, Any]) -> None:
    require(contract.get("schema_version") == 1 and contract.get("release") == "v0.9.2" and
            contract.get("execution_series") == EXECUTION_SERIES and
            contract.get("source_commit") == manifest.get("source_commit") and
            contract.get("total_wall_budget_seconds") is None,
            "CodeQL successor contract identity or clock changed")
    _check_execution_window(contract.get("execution_window"))
    require(contract.get("aggregate_source_working_cap") == {
        "before_gib": 12, "after_gib": 30,
        "before_bytes": 12 * 1024**3, "after_bytes": SOURCE_WORKING_CAP_BYTES,
        "authorization": {"path": SOURCE_CAP_AUTH, "sha256": SOURCE_CAP_AUTH_SHA},
    }, "CodeQL aggregate source-working cap is not the reviewed delta")
    require(contract.get("breadth_first_authorization") ==
            {"path": BREADTH_AUTH, "sha256": BREADTH_AUTH_SHA},
            "CodeQL contract does not bind the exact breadth authorization")
    _ref(root, contract["breadth_first_authorization"], "CodeQL contract breadth authorization")
    base_guards, new_guards = base.get("resource_guards"), contract.get("resource_guards")
    require(isinstance(base_guards, dict) and isinstance(new_guards, dict) and
            set(base_guards) == set(new_guards) and
            base_guards.get("working_set_gib") == 12 and
            new_guards.get("working_set_gib") == WORKING_SET_GIB and
            all(new_guards.get(k) == v for k, v in base_guards.items() if k != "working_set_gib") and
            new_guards.get("stop_free_gib") == STOP_FREE_GIB,
            "CodeQL successor changed resource guards beyond aggregate working cap")
    old_groups = {g.get("id"): g for g in base.get("groups", []) if isinstance(g, dict)}
    new_groups = {g.get("id"): g for g in contract.get("groups", []) if isinstance(g, dict)}
    require(set(old_groups) == set(new_groups) and len(new_groups) == 84,
            "CodeQL successor changed the fixed group roster")
    for group_id, old in old_groups.items():
        new = new_groups[group_id]
        if group_id != CODEQL_GROUP:
            require(new == old, f"non-CodeQL group changed: {group_id}")
    old_codeql = old_groups[CODEQL_GROUP]
    new_codeql = new_groups[CODEQL_GROUP]
    old_codeql_without_environment = copy.deepcopy(old_codeql)
    new_codeql_without_environment = copy.deepcopy(new_codeql)
    old_codeql_without_environment.pop("environment", None)
    new_codeql_without_environment.pop("environment", None)
    require(new_codeql_without_environment == old_codeql_without_environment,
            "CodeQL group changed a frozen field beyond the reviewed environment witness")
    require(new_codeql.get("argv") == old_codeql.get("argv") and
            new_codeql.get("case_ids") == old_codeql.get("case_ids") and
            new_codeql.get("reports") == old_codeql.get("reports") and
            new_codeql.get("output_roots") == old_codeql.get("output_roots") and
            new_codeql.get("maximum_attempts") == CODEQL_MAX_ATTEMPTS and
            new_codeql.get("environment", {}).get("__CF_USER_TEXT_ENCODING") == CF_USER_TEXT_ENCODING,
            "CodeQL command, reports, runtime, or reviewed macOS environment changed")
    old_env = dict(old_codeql.get("environment", {}))
    new_env = dict(new_codeql.get("environment", {}))
    require(set(new_env) == set(old_env) | {"__CF_USER_TEXT_ENCODING"} and
            all(new_env.get(k) == v for k, v in old_env.items()),
            "CodeQL environment changed beyond the exact macOS startup witness")
    scope = contract.get("independent_codeql_scope")
    require(isinstance(scope, dict) and scope.get("schema") == "v092-independent-codeql-continuation/v1" and
            scope.get("sealed_prefix_rows") == SEALED_ROWS and
            scope.get("historical_completed_groups") == HISTORICAL_COMPLETED and
            scope.get("tail_rows_allowed") == 1 and scope.get("automatic_retry") is False and
            scope.get("expected_final_selected_groups") == 83 and
            scope.get("expected_final_partitions") == 87 and scope.get("expected_final_rows") == 4144,
            "CodeQL continuation scope is incomplete")
    failure_scope = scope.get("terminal_outcomes", {}).get("failure")
    require(isinstance(failure_scope, dict) and
            failure_scope.get("statuses") == ["failed", "timed-out", "capacity-lost", "recorder-error"] and
            failure_scope.get("selected_groups") == HISTORICAL_COMPLETED and
            failure_scope.get("partitions") == 82 and failure_scope.get("rows") == 4036 and
            failure_scope.get("automatic_retry") is False,
            "CodeQL terminal-failure handoff scope is incomplete")
    allowed_extra = {
        "source_commit", "source_inputs", "total_wall_budget_seconds", "resource_guards",
        "execution_window", "aggregate_source_working_cap", "independent_codeql_scope",
        "breadth_first_authorization",
    }
    require(set(contract) - set(base) <= allowed_extra,
            "CodeQL successor added an unreviewed top-level contract field")
    for key, value in base.items():
        if key in {"source_commit", "source_inputs", "total_wall_budget_seconds", "resource_guards",
                   "groups", "execution_window", "aggregate_source_working_cap",
                   "independent_codeql_scope"}:
            continue
        require(contract.get(key) == value, f"CodeQL successor changed forbidden contract field: {key}")
    base_inputs = {item.get("path"): item.get("sha256") for item in base.get("source_inputs", [])}
    new_inputs = {item.get("path"): item.get("sha256") for item in contract.get("source_inputs", [])}
    require(all(path in new_inputs and new_inputs[path] == digest for path, digest in base_inputs.items()),
            "CodeQL successor dropped or changed a frozen source input")
    require(set(new_inputs) - set(base_inputs), "CodeQL successor has no additive source closure")
    for path, digest in new_inputs.items():
        require(isinstance(path, str) and RE_SHA.fullmatch(str(digest or "")),
                f"source input is malformed: {path}")
        _relative(path, "source input")


def _project_packet(packet: dict[str, Any], rows: list[dict[str, Any]], raw: bytes) -> dict[str, Any]:
    prefix = packet.get("prefix_rows")
    tail = packet.get("tail_rows")
    require(isinstance(prefix, list) and isinstance(tail, list), "frozen C4 packet is malformed")
    actual_lines = raw.splitlines(keepends=True)
    actual = [(row, sha_bytes(line)) for row, line in zip(rows, actual_lines)]
    require(list(prefix) + list(tail) == actual, "frozen C4 packet is not the exact sealed snapshot")
    boundary = 86
    require(len(prefix) < boundary <= len(actual), "frozen C4 packet does not span the historical boundary")
    projected = copy.deepcopy(packet)
    projected["tail_rows"] = copy.deepcopy(tail[:boundary - len(prefix)])
    require(list(projected["prefix_rows"]) + list(projected["tail_rows"]) == actual[:boundary],
            "frozen C4 historical boundary projection changed rows")
    return projected


@contextlib.contextmanager
def _scoped_resource_recovery_ledger(raw: bytes) -> Iterator[None]:
    """Make the frozen C4 packet reader consume only the supplied prefix.

    ``execute-release-v092.py`` loads ``v092_resource_recovery.py`` inside
    ``_validate_resource_recovery``.  That module normally reads the mutable
    canonical ledger itself, which is correct for ordinary C4 validation but
    would make a later 89+ row look like an unexpected C4 tail while this
    successor is validating its immutable 88-row base.  The loader wrapper is
    scoped to that import and replaces only the module's read of the current
    ledger with the already-bound bytes; every manifest, prefix, roster, and
    artifact read still uses the frozen implementation unchanged.
    """
    original_factory = importlib.util.module_from_spec

    class _LoaderProxy:
        def __init__(self, loader: Any) -> None:
            self._loader = loader

        def create_module(self, spec: Any) -> Any:
            creator = getattr(self._loader, "create_module", None)
            return creator(spec) if creator is not None else None

        def exec_module(self, module: Any) -> None:
            self._loader.exec_module(module)
            original_regular = getattr(module, "_regular_bytes", None)
            original_validate = getattr(module, "validate_packet", None)
            ledger_path = getattr(getattr(module, "LEDGER_PATH", None), "as_posix", lambda: "")()
            require(callable(original_regular) and callable(original_validate) and ledger_path,
                    "frozen resource-recovery reader API changed")

            def scoped_regular(repository: Any, relative: Any, description: str,
                               *args: Any, **kwargs: Any) -> bytes:
                if relative == ledger_path and description == "current execution ledger":
                    return raw
                return original_regular(repository, relative, description, *args, **kwargs)

            def scoped_validate(repository: Any, reference: Any) -> dict[str, Any]:
                module._regular_bytes = scoped_regular
                try:
                    return original_validate(repository, reference)
                finally:
                    module._regular_bytes = original_regular

            module.validate_packet = scoped_validate

    def factory(spec: Any) -> Any:
        if getattr(spec, "name", None) == "v092_resource_recovery":
            loader = getattr(spec, "loader", None)
            require(loader is not None and callable(getattr(loader, "exec_module", None)),
                    "frozen resource-recovery loader changed")
            spec.loader = _LoaderProxy(loader)
        return original_factory(spec)

    importlib.util.module_from_spec = factory
    try:
        yield
    finally:
        importlib.util.module_from_spec = original_factory


def _validate_base(executor: Any, root: Path, rows: list[dict[str, Any]], raw: bytes) -> dict[str, Any]:
    """Use the frozen C4 validator against only the immutable 88-row prefix."""
    original = getattr(executor, "_validate_scoped_tail", None)
    require(callable(original), "frozen executor lacks scoped-tail validation")
    outer = (root / Path(*_relative(BASE_CONTRACT).parts)).resolve()
    nested = {
        ((root / Path(*_relative(path).parts)).resolve(), digest)
        for path, digest in (
            ("reports/releases/v0.9.2/acquisition/failed-contract-01.json", "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3"),
            ("reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json", "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422"),
            ("reports/releases/v0.9.2/acquisition/resource-recovery-contract-03.json", "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063"),
        )
    }
    def bounded(validated: dict[str, Any], packet: dict[str, Any]) -> None:
        identity = (Path(validated.get("path")).resolve(), validated.get("bytes_sha256"))
        if identity == (outer, BASE_SHA):
            return original(validated, _project_packet(packet, rows, raw))
        require(identity in nested, "frozen scoped-tail call names an unregistered historical contract")
        return original(validated, packet)
    executor._validate_scoped_tail = bounded
    try:
        with _scoped_resource_recovery_ledger(raw):
            return executor.validate_plan(root / Path(*_relative(BASE_CONTRACT).parts), repo_root=root)
    finally:
        executor._validate_scoped_tail = original


def _successor_context(base: dict[str, Any], contract: dict[str, Any], contract_raw: bytes,
                       root: Path) -> dict[str, Any]:
    result = copy.deepcopy(base)
    result["repo_root"] = root
    result["path"] = root / Path(*_relative(CONTRACT).parts)
    result["bytes_sha256"] = sha_bytes(contract_raw)
    result["plan_raw"] = contract_raw
    result["plan"] = contract
    result["total_wall_budget_seconds"] = None
    result["source_inputs"] = copy.deepcopy(contract["source_inputs"])
    new_codeql = _base_group(contract)
    for group in result.get("groups", []):
        if group.get("id") == CODEQL_GROUP:
            group.update(copy.deepcopy(new_codeql))
    return result


def _check_manifest(root: Path, manifest: dict[str, Any], manifest_path: str, *, final: bool,
                    terminal: bool) -> None:
    require(manifest.get("schema") == "v092-codeql-independent-continuation-manifest/v1",
            "CodeQL manifest schema differs")
    require(manifest.get("manifest_path") == manifest_path, "manifest self-path binding differs")
    require(manifest.get("base_contract") == {"path": BASE_CONTRACT, "sha256": BASE_SHA},
            "CodeQL manifest does not bind the frozen base contract")
    require(manifest.get("ledger_prefix") == {"path": SEALED_LEDGER, "sha256": SEALED_LEDGER_SHA},
            "CodeQL manifest does not bind sealed ledger88")
    require(manifest.get("source_commit") and RE_COMMIT.fullmatch(manifest["source_commit"]) and
            manifest.get("plan_commit") and RE_COMMIT.fullmatch(manifest["plan_commit"]),
            "CodeQL manifest source/plan commits are malformed")
    require(manifest.get("base_plan_commit") == BASE_PLAN_COMMIT,
            "CodeQL manifest does not bind the frozen base plan commit")
    expected_success = {
        "ledger_rows": 89, "selected_groups": 83,
        "partitions": 87, "rows": 4144, "known_stale": 0,
    }
    expected_failure = {
        "ledger_rows": 89, "selected_groups": 82,
        "partitions": 82, "rows": 4036, "known_stale": 0,
    }

    def terminal_expectations() -> dict[str, dict[str, Any]]:
        """Return the reviewed success/failure outcomes without choosing one.

        A final manifest is sealed before the one CodeQL row exists.  It may
        therefore bind both possible terminal packets instead of claiming a
        future result.  Older already-sealed fixtures may still bind one
        explicit ``expected`` result alongside a concrete terminal outcome.
        """
        pair = manifest.get("terminal_expected")
        if pair is None and "expected_after_success" in manifest and "expected_after_failure" in manifest:
            pair = {
                "success": manifest.get("expected_after_success"),
                "failure": manifest.get("expected_after_failure"),
            }
        if pair is not None:
            require(pair == {"success": expected_success, "failure": expected_failure},
                    "CodeQL terminal outcome mapping is not the reviewed pair")
            return pair
        return {"success": expected_success, "failure": expected_failure}
    require(manifest.get("joern") in (None, {"scheduled": False, "historical_only": True}),
            "CodeQL manifest contains a prospective Joern schedule")
    codeql = manifest.get("codeql")
    require(isinstance(codeql, dict) and codeql.get("group_id") == CODEQL_GROUP and
            codeql.get("attempt_id") == CODEQL_ATTEMPT and codeql.get("maximum_attempts") == CODEQL_MAX_ATTEMPTS and
            codeql.get("output_root") == CODEQL_OUTPUT_ROOT and
            codeql.get("query_receipt") == {"path": QUERY_RECEIPT, "sha256": QUERY_RECEIPT_SHA},
            "CodeQL manifest identity is incomplete")
    _check_authorization(root, manifest)
    if final:
        require(manifest.get("execution_admission") == {"path": ADMISSION_RECEIPT},
                "final CodeQL manifest does not bind the canonical admission receipt path")
        review = manifest.get("final_review")
        require(isinstance(review, dict) and review.get("path") == FINAL_REVIEW,
                "final CodeQL manifest lacks the registered independent review")
        _ref(root, review, "final CodeQL review")
        review_value = _json(root, review["path"], "final CodeQL review")
        require(review_value.get("status") == "approved" and review_value.get("automatic_retry") is False,
                "final CodeQL review is not approved fail-closed")
        if terminal:
            outcome = manifest.get("terminal_outcome", {"mode": "success"})
            require(isinstance(outcome, dict) and outcome.get("mode") in
                    {"pending", "success", "failure"},
                    "final CodeQL terminal outcome is missing or ambiguous")
            pair = terminal_expectations()
            mode = outcome.get("mode")
            if mode == "pending":
                require("expected" not in manifest,
                        "pending CodeQL manifest must not claim a future terminal result")
            else:
                require(manifest.get("expected") == pair[mode],
                        "terminal CodeQL denominator changed")
        else:
            # Final review binds the candidate before dispatch.  The terminal
            # outcome is deliberately absent/pending until the one CodeQL row
            # is durably written; requiring it here would make admission
            # impossible at the sealed 88-row prefix.
            outcome = manifest.get("terminal_outcome")
            pair_bound = ("terminal_expected" in manifest or
                          ("expected_after_success" in manifest and
                           "expected_after_failure" in manifest))
            if pair_bound:
                terminal_expectations()
                require(isinstance(outcome, dict) and outcome.get("mode") == "pending" and
                        "expected" not in manifest,
                        "pre-terminal CodeQL mapping must remain pending and unclaimed")
            else:
                require(manifest.get("expected") in (expected_success, expected_failure),
                        "pre-terminal CodeQL denominator is not a reviewed result")
                if outcome is not None:
                    require(isinstance(outcome, dict) and outcome.get("mode") in
                            {"pending", "success", "failure"},
                            "pre-terminal CodeQL outcome is ambiguous")
    elif manifest.get("expected") not in (expected_success, expected_failure):
        raise CodeQLContinuationError("CodeQL provisional denominator is not a reviewed one-tail result")
    else:
        require(manifest.get("final_review") in (None, {}), "pre-admission manifest has final review bytes")


def _runtime_lease(validated: dict[str, Any], root: Path) -> dict[str, Any]:
    now = time.time()
    origin = dt.datetime.fromisoformat(ORIGIN).timestamp()
    actual_elapsed = now - origin
    require(actual_elapsed >= 0, "wall clock precedes the immutable execution origin")
    lease = CODEQL_DEADLINE_SECONDS + STARTUP_ALLOWANCE_SECONDS
    runtime = copy.deepcopy(validated)
    runtime["total_wall_budget_seconds"] = actual_elapsed + lease
    runtime["plan"] = copy.deepcopy(validated["plan"])
    runtime["plan"]["total_wall_budget_seconds"] = actual_elapsed + lease
    runtime["plan"]["resource_reservation"] = dict(validated["plan"]["resource_reservation"])
    runtime["plan"]["resource_reservation"]["expires_at_unix_seconds"] = now + lease
    runtime["execution_window_runtime"] = {
        "mode": "no-user-imposed-expiry", "actual_elapsed_wall_seconds": actual_elapsed,
        "per_attempt_lease_seconds": lease, "group_id": CODEQL_GROUP,
        "deadline_seconds": CODEQL_DEADLINE_SECONDS,
        "startup_allowance_seconds": STARTUP_ALLOWANCE_SECONDS,
    }
    return runtime


@contextlib.contextmanager
def _scoped_source_projection_guard(executor: Any) -> Iterator[None]:
    original = getattr(executor, "_materialize_source", None)
    require(callable(original), "frozen executor lacks source materialization")
    def guarded(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("disk_guard") is not None and kwargs.get("preflight_only") is not True:
            probe = dict(kwargs)
            probe["preflight_only"] = True
            probe.pop("expected_projected_bytes", None)
            projected = original(*args, **probe)
            require(type(projected) is int and projected <= SOURCE_PROJECTION_MAX_BYTES,
                    "CodeQL materialized source projection exceeds 12 GiB")
            expected = kwargs.get("expected_projected_bytes")
            if expected is not None:
                require(expected == projected, "CodeQL source projection changed after preflight")
        projected = original(*args, **kwargs)
        if isinstance(projected, int):
            require(projected <= SOURCE_PROJECTION_MAX_BYTES,
                    "CodeQL materialized source projection exceeds 12 GiB")
        return projected
    executor._materialize_source = guarded
    try:
        yield
    finally:
        executor._materialize_source = original


def build_worker_environment(executor: Any, group: dict[str, Any], execution: Path,
                            attempt: Path, cache: Path) -> dict[str, str]:
    helper = getattr(executor, "_child_environment", None)
    require(callable(helper), "frozen executor lacks child environment expansion")
    env = helper(group, execution, attempt, cache)
    require(isinstance(env, dict), "frozen child environment is not an object")
    require(env.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION") == "1" and
            env.get("DATAFLOWBENCH_V092_GROUP_ID") == CODEQL_GROUP,
            "CodeQL child environment lacks exact release/group markers")
    require(env.get("__CF_USER_TEXT_ENCODING") == CF_USER_TEXT_ENCODING,
            "CodeQL child environment lacks the reviewed macOS text encoding witness")
    return {str(k): str(v) for k, v in env.items()}


def _codeql_disk_guard(ctx: dict[str, Any]) -> Any:
    """Construct the frozen C4 guard with only the reviewed working-cap delta."""
    plan = ctx["successor"]["plan"]
    resource = plan.get("resource_budget")
    guards = plan.get("resource_guards")
    require(isinstance(resource, dict) and isinstance(guards, dict),
            "CodeQL successor lacks the frozen resource budget")
    require(resource.get("minimum_launch_free_gib") == 110 and
            resource.get("minimum_free_after_restore_gib") == 64 and
            resource.get("protected_reserve_gib") == 40 and
            resource.get("scratch_gib") == 24 and
            resource.get("proposed_total_retention_ceiling_gib") == 24,
            "CodeQL successor changed the frozen resource budget")
    require(guards == {"stop_free_gib": STOP_FREE_GIB, "working_set_gib": WORKING_SET_GIB},
            "CodeQL successor has an unexpected resource guard shape")
    disk_guard = ctx["frozen"].get("disk_guard")
    require(disk_guard is not None and hasattr(disk_guard, "DiskGuard"),
            "frozen disk guard is unavailable")
    gib = 1024**3
    return disk_guard.DiskGuard(
        launch_floor_bytes=resource["minimum_launch_free_gib"] * gib,
        protected_reserve_bytes=resource["protected_reserve_gib"] * gib,
        stop_margin_bytes=(guards["stop_free_gib"] - resource["protected_reserve_gib"]) * gib,
        stop_floor_bytes=guards["stop_free_gib"] * gib,
        scratch_ceiling_bytes=resource["scratch_gib"] * gib,
        retention_ceiling_bytes=resource["proposed_total_retention_ceiling_gib"] * gib,
        working_ceiling_bytes=guards["working_set_gib"] * gib,
    )


def check_live_resource_floor(executor: Any, root: Path) -> None:
    """Repeat the reviewed 127 GiB and contender gate before dispatch."""
    checker = getattr(executor, "_check_resources", None)
    require(callable(checker), "frozen executor lacks its resource contender gate")
    try:
        checker(root, LIVE_RESOURCE_FLOOR_BYTES)
    except Exception as exc:
        raise CodeQLContinuationError(f"CodeQL live resource gate rejected dispatch: {exc}") from exc


@contextlib.contextmanager
def _scoped_locked_resource_floor(executor: Any, root: Path) -> Iterator[None]:
    """Raise the frozen pre-attempt resource check to 127 GiB under its lock.

    The frozen C4 runner checks only contenders on its resource-recovery path
    before calling ``_assert_fresh``.  Patching both frozen call sites keeps
    the original 110 GiB minimum and all contender logic, while adding the
    reviewed 127 GiB floor immediately before the first attempt directory can
    be created.  The patch is scoped and restored on every exit path.
    """
    original_check = getattr(executor, "_check_resources", None)
    original_fresh = getattr(executor, "_assert_fresh", None)
    original_materialize = getattr(executor, "_materialize_source", None)
    require(callable(original_check) and callable(original_fresh) and callable(original_materialize),
            "frozen executor lacks its pre-attempt resource gates")
    checked = False

    def locked_materialize(*args: Any, **kwargs: Any) -> Any:
        nonlocal checked
        if kwargs.get("preflight_only") is True and not checked:
            repo_root = args[0] if args else kwargs.get("repo_root")
            require(isinstance(repo_root, (str, Path)) and
                    Path(repo_root).resolve() == Path(root).resolve(),
                    "frozen materializer changed repository root")
            checked = True
            original_check(Path(repo_root), LIVE_RESOURCE_FLOOR_BYTES)
        return original_materialize(*args, **kwargs)

    def locked_check_with_cell(repo_root: Path, minimum: int = 0) -> Any:
        nonlocal checked
        require(Path(repo_root).resolve() == Path(root).resolve(),
                "frozen resource gate changed repository root")
        checked = True
        return original_check(repo_root, max(int(minimum), LIVE_RESOURCE_FLOOR_BYTES))

    def locked_fresh_with_cell(repo_root: Path, group: Any, reports: Any, series: int) -> Any:
        nonlocal checked
        if not checked:
            require(Path(repo_root).resolve() == Path(root).resolve(),
                    "frozen fresh-attempt gate changed repository root")
            checked = True
            original_check(repo_root, LIVE_RESOURCE_FLOOR_BYTES)
        return original_fresh(repo_root, group, reports, series)

    executor._check_resources = locked_check_with_cell
    executor._assert_fresh = locked_fresh_with_cell
    executor._materialize_source = locked_materialize
    try:
        yield
    finally:
        executor._check_resources = original_check
        executor._assert_fresh = original_fresh
        executor._materialize_source = original_materialize


def materialized_preflight(ctx: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen whole-snapshot source and capacity preflight without extraction.

    This deliberately calls the frozen archive preflight with ``preflight_only``;
    it never creates an attempt, execution root, cache, source snapshot, or
    analyzer process. The same path roster and logical-size accounting are then
    used by ``run_group`` before its first mkdir.
    """
    require(ctx.get("runtime_recovery_verified") is True,
            "CodeQL materialized preflight requires a verified retained replay")
    executor = ctx["frozen"]["executor"]
    validated = ctx["successor"]
    root = ctx["root"]
    group = _base_group(validated["plan"])
    reports = group.get("reports")
    require(isinstance(reports, list), "CodeQL group report roster is missing")
    fresh = executor._assert_fresh(root, group, reports, EXECUTION_SERIES)
    attempt, execution, cache, _ledger, attempt_id = fresh
    require(attempt_id == CODEQL_ATTEMPT, "frozen attempt path is not CodeQL attempt one")
    env = build_worker_environment(executor, group, execution, attempt, cache)
    output_roots = [execution / Path(*_relative(value, "CodeQL output root").parts)
                    for value in group.get("output_roots", [])]
    retained, scratch = executor._matrix_capacity_paths(validated, execution, env, output_roots)
    source_members = tuple(executor.SNAPSHOT_DIRECTORIES) + tuple(executor.SNAPSHOT_FILES) + tuple(
        item["path"] for item in validated["source_inputs"]
    ) + (".git",)
    source_roots = [execution]
    ledger_rows = executor._ledger_rows(root / Path(*executor.LEDGER_PATH.parts))
    for row in ledger_rows:
        previous = Path(row.get("execution_root", ""))
        require(previous.is_absolute() and executor._under(previous, root / Path(*executor.EXECUTION_ROOT.parts)),
                "capacity ledger execution root escapes the frozen execution root")
        source_roots.append(previous)
    execution_base = root / Path(*executor.EXECUTION_ROOT.parts)
    if execution_base.exists():
        for series_root in execution_base.iterdir():
            require(not series_root.is_symlink() and series_root.is_dir(),
                    "execution-state contains an unsafe series path")
            for group_root in series_root.iterdir():
                require(not group_root.is_symlink() and group_root.is_dir(),
                        "execution-state contains an unsafe group path")
                for attempt_root in group_root.iterdir():
                    require(not attempt_root.is_symlink() and attempt_root.is_dir(),
                            "execution-state contains an unsafe attempt path")
                    source_roots.append(attempt_root)
    source_roots = list(dict.fromkeys(source_roots))
    working_paths: list[Path] = []
    historical_paths: list[Path] = []
    for source_root in source_roots:
        paths = [source_root / Path(*_relative(value, "working source path").parts)
                 for value in source_members]
        (working_paths if source_root == execution else historical_paths).extend(paths)
    guard = _codeql_disk_guard(ctx)
    baseline = guard.logical_size(historical_paths)
    projected = executor._materialize_source(
        root, validated["plan"]["source_commit"], execution,
        [item["path"] for item in validated["source_inputs"]],
        disk_guard=guard, working_paths=working_paths,
        working_baseline_bytes=baseline, preflight_only=True,
    )
    require(type(projected) is int and projected <= SOURCE_PROJECTION_MAX_BYTES,
            "CodeQL materialized source projection exceeds 12 GiB")
    completed = executor._verified_completed_groups(validated)
    known = {item["id"] for item in validated["plan"]["groups"]}
    expected_completed = {
        row.get("group_id") for row in ctx["rows"][:SEALED_ROWS]
        if row.get("status") == "completed"
    }
    require(completed == expected_completed and len(completed) == HISTORICAL_COMPLETED,
            "CodeQL preflight retained completion IDs differ from the verified sealed rows")
    remaining = len(known - completed)
    require(remaining == 2, "CodeQL preflight no longer sees the sealed 82-group remainder")
    metadata_projection = 1024**2
    working = guard.check(
        projected_bytes=(projected + metadata_projection) * remaining,
        additional_current_bytes=baseline, category="working", paths=working_paths,
        capacity_path=root, phase="launch",
    )
    retention = guard.check(projected_bytes=1024**2, category="retention",
                            paths=retained, capacity_path=root, phase="launch")
    scratch_check = guard.check(projected_bytes=1024**2, category="scratch",
                                paths=scratch, capacity_path=root, phase="launch")
    return {
        "schema": "v092-codeql-materialized-source-preflight/v1",
        "attempt_id": CODEQL_ATTEMPT,
        "materialized_source": MATERIALIZED_SOURCE,
        "projected_source_bytes": projected,
        "historical_working_baseline_bytes": baseline,
        "remaining_group_count": remaining,
        "aggregate_working_cap_bytes": SOURCE_WORKING_CAP_BYTES,
        "source_projection_max_bytes": SOURCE_PROJECTION_MAX_BYTES,
        "resource_floor_bytes": LIVE_RESOURCE_FLOOR_BYTES,
        "working_check": working,
        "retention_check": retention,
        "scratch_check": scratch_check,
        "child_environment": {
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": env.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION"),
            "DATAFLOWBENCH_V092_GROUP_ID": env.get("DATAFLOWBENCH_V092_GROUP_ID"),
            "__CF_USER_TEXT_ENCODING": env.get("__CF_USER_TEXT_ENCODING"),
        },
        "execution_root": str(execution),
        "attempt_root": str(attempt),
        "cache_root": str(cache),
    }


def _validate_row_identity(ctx: dict[str, Any], row: dict[str, Any]) -> None:
    manifest = ctx["manifest"]
    group = _base_group(ctx["base_contract"])
    require(row.get("group_id") == CODEQL_GROUP and row.get("attempt_id") == CODEQL_ATTEMPT,
            "CodeQL tail group identity changed")
    require(row.get("execution_series") == EXECUTION_SERIES and
            row.get("contract_sha256") == ctx["successor"]["bytes_sha256"] and
            row.get("source_commit") == manifest["source_commit"] and
            row.get("plan_commit") == manifest["plan_commit"] and
            row.get("fixture_revision") == manifest.get("fixture_revision"),
            "CodeQL tail source/plan/contract/fixture identity changed")
    require(row.get("argv") == group.get("argv") and
            row.get("output_roots") == group.get("output_roots"),
            "CodeQL tail command or output identity changed")


def _load_pinned_helper(root: Path, relative: str, expected: str, name: str) -> Any:
    path = _path(root, relative, name)
    require(sha(path) == expected, f"{name} source changed")
    spec = importlib.util.spec_from_file_location(
        f"codeql_pending_{name.replace('-', '_').replace(' ', '_')}", path
    )
    require(spec is not None and spec.loader is not None, f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_historical_replay_helper(root: Path) -> Any:
    """Load the reviewed continuation-05 normalizer by exact source bytes."""
    module = _load_pinned_helper(root, HISTORICAL_REPLAY_SOURCE,
                                 HISTORICAL_REPLAY_SOURCE_SHA,
                                 "historical-replay-helper")
    require(getattr(module, "SEALED_ROWS", None) == 87 and
            getattr(module, "DEFAULT_MANIFEST", None) == HISTORICAL_REPLAY_MANIFEST and
            getattr(module, "DEFAULT_CONTRACT", None) == HISTORICAL_REPLAY_CONTRACT and
            getattr(module, "JOERN_ATTEMPT", None) ==
            "joern-swift-common108-attempt-04-series-01",
            "historical replay helper identity is not the pinned continuation-05 API")
    return module


def _load_historical_previous_helper(root: Path) -> Any:
    """Load the reviewed continuation-01 normalizer for Joern03 history."""
    module = _load_pinned_helper(root, HISTORICAL_REPLAY_PREVIOUS_SOURCE,
                                 HISTORICAL_REPLAY_PREVIOUS_SOURCE_SHA,
                                 "historical-previous-helper")
    require(getattr(module, "SEALED_ROWS", None) == 86 and
            getattr(module, "JOERN_ATTEMPT", None) ==
            "joern-swift-common108-attempt-03-series-01" and
            getattr(module, "DEFAULT_CONTRACT", None) ==
            HISTORICAL_REPLAY_PREVIOUS_CONTRACT,
            "historical previous helper identity is not the pinned continuation-01 API")
    return module


def _historical_replay_contexts(ctx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive normalized contexts for every retained row before CodeQL.

    Frozen C4 supplies normalized C1/C2/C3 contexts.  The two later Joern
    contracts are continuation overlays, so their raw JSON groups are not
    checker inputs.  The pinned continuation-05 helper derives those contexts
    from the normalized base groups and its exact reviewed deltas; this keeps
    identity components, expanded tools, qualifications, and report bindings
    identical to the predecessor validation path.
    """
    root = ctx["root"]
    executor = ctx["frozen"]["executor"]
    base = ctx["base"]
    helper = _load_historical_replay_helper(root)
    previous = _load_historical_previous_helper(root)
    contexts = dict(base.get("resource_recovery", {}).get("contexts", {}))
    require(isinstance(contexts, dict),
            "frozen historical replay helper returned no context map")
    # Derive Joern03 through continuation-01's reviewed context constructor.
    # This copies the frozen normalized groups and applies only that
    # continuation's validated Joern plan/report delta.
    previous_manifest_raw = _read(root, HISTORICAL_REPLAY_PREVIOUS_MANIFEST,
                                  "historical previous manifest")
    require(sha_bytes(previous_manifest_raw) == HISTORICAL_REPLAY_PREVIOUS_MANIFEST_SHA,
            "historical previous manifest changed")
    previous_manifest = json.loads(previous_manifest_raw)
    require(isinstance(previous_manifest, dict),
            "historical previous manifest is not an object")
    previous_contract_raw = _read(root, HISTORICAL_REPLAY_PREVIOUS_CONTRACT,
                                  "historical Joern03 contract")
    require(sha_bytes(previous_contract_raw) == HISTORICAL_REPLAY_PREVIOUS_CONTRACT_SHA,
            "historical Joern03 contract changed")
    previous_contract = json.loads(previous_contract_raw)
    require(isinstance(previous_contract, dict),
            "historical Joern03 contract is not an object")
    previous_plan = previous._raw_plan_delta(root, previous_manifest)
    joern03 = previous._derive_context(
        base, previous_contract, previous_contract_raw,
        previous_manifest, previous_plan, executor,
    )
    contexts[HISTORICAL_REPLAY_PREVIOUS_CONTRACT_SHA] = {
        "validated": joern03,
        "plan_commit": previous_manifest["plan_commit"],
    }
    # Derive the current predecessor (Joern04) through the same reviewed
    # continuation-05 context constructor.  It is not a raw plan copy.
    manifest_raw = _read(root, HISTORICAL_REPLAY_MANIFEST, "historical replay manifest")
    require(sha_bytes(manifest_raw) == HISTORICAL_REPLAY_MANIFEST_SHA,
            "historical replay manifest changed")
    manifest = json.loads(manifest_raw)
    require(isinstance(manifest, dict), "historical replay manifest is not an object")
    contract_raw = _read(root, HISTORICAL_REPLAY_CONTRACT,
                         "historical predecessor contract")
    require(sha_bytes(contract_raw) == HISTORICAL_REPLAY_CONTRACT_SHA,
            "historical predecessor contract changed")
    contract = json.loads(contract_raw)
    require(isinstance(contract, dict), "historical predecessor contract is not an object")
    repaired_plan = helper._raw_plan_delta(root, manifest)
    predecessor = helper._derive_context(
        base, contract, contract_raw, manifest, repaired_plan, executor,
    )
    contexts[HISTORICAL_REPLAY_CONTRACT_SHA] = {
        "validated": predecessor,
        "plan_commit": manifest["plan_commit"],
    }
    contexts[BASE_SHA] = {"validated": base, "plan_commit": ctx["base_plan_commit"]}
    for digest, entry in contexts.items():
        require(isinstance(entry, dict) and isinstance(entry.get("validated"), dict),
                f"historical context is malformed: {digest}")
        validated = entry["validated"]
        require(validated.get("bytes_sha256") == digest,
                f"historical context digest mismatch: {digest}")
        groups = validated.get("groups")
        require(isinstance(groups, list) and all(
            isinstance(group, dict) and isinstance(group.get("identity_components"), list)
            for group in groups
        ), f"historical context is not frozen-normalized: {digest}")
    return contexts


def _enrich_successor_historical_contexts(ctx: dict[str, Any]) -> dict[str, Any]:
    """Attach the complete immutable historical map to the runtime successor.

    Frozen C4's packet intentionally retains only C1/C2/C3 contexts.  The
    continuation replay derives normalized C4, Joern03, and Joern04 contexts
    separately; the runtime successor must carry those exact wrappers so the
    frozen elapsed-wall and completed-group guards can register every row in
    the sealed ledger.  The prospective CodeQL SHA is deliberately excluded
    from this map and is registered by frozen ``_matrix_elapsed_wall`` itself.
    """
    historical = ctx.get("_historical_replay_contexts")
    if historical is None:
        historical = _historical_replay_contexts(ctx)
        ctx["_historical_replay_contexts"] = historical
    require(isinstance(historical, dict),
            "historical replay did not return a context map")
    require(set(historical) == EXPECTED_HISTORICAL_CONTEXT_SHAS,
            "historical replay context roster differs from the sealed C1/C2/C3/C4/Joern03/04 roster")
    successor = ctx["successor"]
    recovery = successor.get("resource_recovery")
    require(isinstance(recovery, dict),
            "runtime successor lacks the C4 resource-recovery packet")
    inherited = recovery.get("contexts")
    require(isinstance(inherited, dict) and
            set(inherited).issubset(EXPECTED_HISTORICAL_CONTEXT_SHAS),
            "runtime successor inherited an unknown historical context")
    retained_completed = copy.deepcopy(recovery.get("retained_completed"))
    retained_failures = copy.deepcopy(recovery.get("retained_failures"))
    require(isinstance(retained_completed, dict) and isinstance(retained_failures, dict),
            "runtime successor lost frozen retained completion/failure maps")
    recovery = copy.deepcopy(recovery)
    recovery["contexts"] = copy.deepcopy(historical)
    recovery["retained_completed"] = retained_completed
    recovery["retained_failures"] = retained_failures
    successor["resource_recovery"] = recovery
    ctx["successor"] = successor
    return successor


@contextlib.contextmanager
def _scoped_elapsed_ledger(executor: Any, root: Path, raw: bytes) -> Iterator[None]:
    """Scope the frozen elapsed-wall reader to an explicitly supplied prefix.

    Bifrost recovery may inspect an immutable 89-row CodeQL prefix after the
    canonical ledger has gained later rows.  This adapter is used only for
    that read-only registration check, only for the canonical ledger path,
    and restores the frozen reader on every exit.
    """
    original = getattr(executor, "_ledger_rows", None)
    ledger_path = getattr(executor, "LEDGER_PATH", None)
    require(callable(original) and ledger_path is not None,
            "frozen elapsed-wall ledger reader API changed")
    _assert_live_ledger_prefix(root, raw)
    expected_path = (root / Path(*ledger_path.parts)).resolve()
    supplied_rows = _parse_ledger(raw)

    def scoped(path: Path) -> list[dict[str, Any]]:
        require(Path(path).resolve() == expected_path,
                "frozen elapsed-wall reader requested an unexpected ledger path")
        return copy.deepcopy(supplied_rows)

    executor._ledger_rows = scoped
    try:
        yield
    finally:
        executor._ledger_rows = original


def _validate_runtime_context_registration(ctx: dict[str, Any]) -> float:
    """Run the frozen elapsed-wall registration check before admission/execute."""
    successor = ctx["successor"]
    recovery = successor.get("resource_recovery")
    require(isinstance(recovery, dict) and
            set(recovery.get("contexts", {})) == EXPECTED_HISTORICAL_CONTEXT_SHAS,
            "runtime successor historical context registration is incomplete")
    checker = getattr(ctx["frozen"].get("executor"), "_matrix_elapsed_wall", None)
    require(callable(checker), "frozen executor does not expose its wall-clock registration guard")
    try:
        if ctx.get("ledger_raw_supplied"):
            raw = ctx.get("raw")
            require(isinstance(raw, bytes),
                    "supplied ledger registration lacks immutable raw bytes")
            with _scoped_elapsed_ledger(ctx["frozen"]["executor"], ctx["root"], raw):
                elapsed = checker(successor)
        else:
            elapsed = checker(successor)
    except Exception as exc:
        raise CodeQLContinuationError(
            f"frozen runtime historical context registration rejected: {exc}"
        ) from exc
    require(type(elapsed) in (int, float) and elapsed >= 0 and elapsed != float("inf"),
            "frozen runtime registration returned an invalid elapsed wall value")
    ctx["runtime_registration"] = {
        "schema": "v092-codeql-runtime-context-registration/v1",
        "historical_context_sha256": sorted(EXPECTED_HISTORICAL_CONTEXT_SHAS),
        "prospective_contract_sha256": successor["bytes_sha256"],
        "elapsed_wall_seconds": elapsed,
        "read_only": True,
    }
    return elapsed


def _check_replay_proof(proof: object) -> str:
    """Validate the frozen replay result shape before recovery overlay."""
    require(isinstance(proof, dict),
            "runtime recovery overlay requires a completed frozen replay")
    expected = {
        "continuation-preflight-passed": (SEALED_ROWS, HISTORICAL_COMPLETED, 82, 4036, "pending"),
        "fresh-evidence-verified": (SEALED_ROWS + 1, HISTORICAL_COMPLETED + 1, 87, 4144, "success"),
        "terminal-failure-handoff": (SEALED_ROWS + 1, HISTORICAL_COMPLETED, 82, 4036, "failure"),
    }
    status = proof.get("status")
    require(status in expected,
            "runtime recovery overlay requires an actual frozen replay status")
    ledger_rows, selected_groups, partitions, report_rows, terminal_outcome = expected[status]
    require(proof.get("ledger_rows") == ledger_rows and
            proof.get("selected_groups") == selected_groups and
            proof.get("partitions") == partitions and
            proof.get("rows") == report_rows and
            proof.get("known_stale") == 0 and
            proof.get("terminal_outcome") == terminal_outcome,
            "runtime recovery overlay replay counts are not the frozen 82/6 proof")
    expected_failure_count = 7 if status == "terminal-failure-handoff" else 6
    require(isinstance(proof.get("selected_attempts"), list) and
            len(proof["selected_attempts"]) == selected_groups and
            isinstance(proof.get("fresh_reports"), list) and
            len(proof["fresh_reports"]) == partitions and
            isinstance(proof.get("failed_attempts"), list) and
            len(proof["failed_attempts"]) == expected_failure_count,
            "runtime recovery overlay lacks the complete frozen replay proof")
    return status


def _attach_verified_runtime_recovery(ctx: dict[str, Any]) -> None:
    """Replace C4's 55/2 packet maps with the verified 88-row runtime view.

    The frozen C4 packet deliberately reports its own 55 completed groups and
    two failures.  A continuation runtime must additionally account for the
    Joern03/04 rows already verified by ``_replay_completed``; otherwise the
    frozen completed-group guard sees only 55 and reports 29 groups remaining.
    This overlay is constructed solely from rows whose receipts and normalized
    contexts have just passed the frozen checker.  The original C4 maps remain
    under explicit provenance keys and the immutable ``ctx["base"]`` object is
    never changed.
    """
    proof = ctx.get("replay")
    status = _check_replay_proof(proof)
    require(isinstance(proof, dict),
            "runtime recovery overlay requires a completed frozen replay")
    expected_proof = {
        "continuation-preflight-passed": (SEALED_ROWS, HISTORICAL_COMPLETED, 82, 4036, "pending"),
        "fresh-evidence-verified": (SEALED_ROWS + 1, HISTORICAL_COMPLETED + 1, 87, 4144, "success"),
        "terminal-failure-handoff": (SEALED_ROWS + 1, HISTORICAL_COMPLETED, 82, 4036, "failure"),
    }
    ledger_rows, selected_groups, partitions, report_rows, terminal_outcome = expected_proof[status]
    historical = ctx.get("_historical_replay_contexts")
    require(isinstance(historical, dict) and
            set(historical) == EXPECTED_HISTORICAL_CONTEXT_SHAS,
            "runtime recovery overlay lacks the exact historical context roster")
    successor = ctx["successor"]
    recovery = successor.get("resource_recovery")
    require(isinstance(recovery, dict),
            "runtime successor lacks the C4 resource-recovery packet")
    original_completed = recovery.get("retained_completed")
    original_failures = recovery.get("retained_failures")
    require(isinstance(original_completed, dict) and isinstance(original_failures, dict),
            "frozen C4 retained maps are missing")
    raw = ctx.get("raw")
    rows = ctx.get("rows")
    require(isinstance(raw, bytes) and isinstance(rows, list) and len(rows) >= SEALED_ROWS,
            "runtime recovery overlay lacks the sealed ledger bytes")
    lines = raw.splitlines(keepends=True)
    require(len(lines) >= SEALED_ROWS and len(lines) == len(rows),
            "runtime recovery overlay ledger rows and bytes differ")
    completed: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}
    terminal_statuses = {"failed", "timed-out", "capacity-lost", "recorder-error"}
    for index, row in enumerate(rows[:SEALED_ROWS]):
        require(isinstance(row, dict), "runtime recovery overlay contains a malformed row")
        digest = row.get("contract_sha256")
        entry = historical.get(digest)
        require(isinstance(entry, dict) and isinstance(entry.get("validated"), dict),
                f"runtime recovery row has no normalized context: {row.get('attempt_id')}")
        require(row.get("source_commit") == entry["validated"].get("plan", {}).get("source_commit") and
                row.get("plan_commit") == entry.get("plan_commit"),
                f"runtime recovery row identity changed: {row.get('attempt_id')}")
        attempt_id = row.get("attempt_id")
        number = _attempt_number(attempt_id)
        record = {
            "row": copy.deepcopy(row),
            "ledger_line_sha256": sha_bytes(lines[index]),
            "context_sha256": digest,
            "plan_commit": entry["plan_commit"],
            "attempt_number": number,
        }
        if row.get("status") == "completed":
            group_id = row.get("group_id")
            require(isinstance(group_id, str) and group_id not in completed,
                    f"runtime recovery has duplicate completed group: {group_id}")
            completed[group_id] = record
        else:
            require(row.get("status") in terminal_statuses and isinstance(attempt_id, str),
                    f"runtime recovery has an unknown terminal row: {attempt_id}")
            require(attempt_id not in failures,
                    f"runtime recovery has duplicate terminal attempt: {attempt_id}")
            failures[attempt_id] = record
    require(len(completed) == 82 and len(failures) == 6,
            "runtime recovery overlay did not account for the verified 82/6 sealed rows")
    recovery = copy.deepcopy(recovery)
    recovery["base_retained_completed"] = copy.deepcopy(original_completed)
    recovery["base_retained_failures"] = copy.deepcopy(original_failures)
    recovery["retained_completed"] = completed
    recovery["retained_failures"] = failures
    recovery["runtime_overlay"] = {
        "schema": "v092-codeql-runtime-recovery-overlay/v1",
        "sealed_rows": SEALED_ROWS,
        "verified_completed_groups": len(completed),
        "verified_terminal_failures": len(failures),
        "base_retained_completed": len(original_completed),
        "base_retained_failures": len(original_failures),
    }
    successor["resource_recovery"] = recovery
    ctx["successor"] = successor
    ctx["runtime_recovery_verified"] = True


def _historical_contract_context(ctx: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """Return the exact normalized context for one retained failed attempt."""
    digest = row.get("contract_sha256")
    require(isinstance(digest, str) and digest in HISTORICAL_CONTEXT_SPECS,
            f"retained failure has no registered original contract: {row.get('attempt_id')}")
    _relative(HISTORICAL_CONTEXT_SPECS[digest][0], "historical contract")
    contexts = ctx.get("_historical_replay_contexts")
    if not isinstance(contexts, dict):
        contexts = _historical_replay_contexts(ctx)
        ctx["_historical_replay_contexts"] = contexts
    entry = contexts.get(digest)
    require(isinstance(entry, dict) and isinstance(entry.get("validated"), dict),
            f"retained failure has no normalized original context: {row.get('attempt_id')}")
    require(row.get("plan_commit") == entry.get("plan_commit"),
            f"retained failure plan commit changed: {row.get('attempt_id')}")
    origin = entry["validated"]
    require(row.get("source_commit") == origin.get("plan", {}).get("source_commit"),
            f"retained failure source commit changed: {row.get('attempt_id')}")
    groups = origin.get("groups")
    require(isinstance(groups, list) and all(
        isinstance(group, dict) and isinstance(group.get("identity_components"), list)
        for group in groups
    ), f"retained failure context is not frozen-normalized: {row.get('attempt_id')}")
    return origin


def _replay_completed(ctx: dict[str, Any], *, final: bool) -> dict[str, Any]:
    """Run the frozen checker over the retained completed prefix and optional tail."""
    rows = ctx["rows"]
    selected_rows = selected(rows, final=final)
    checker = ctx["frozen"]["checker"]
    executor = ctx["frozen"]["executor"]
    historical_contexts = _historical_replay_contexts(ctx)
    ctx["_historical_replay_contexts"] = historical_contexts
    # The frozen elapsed-wall guard registers the prospective successor by its
    # own bytes_sha256.  Keep the stored historical map immutable and use a
    # local view for replay's prospective row; otherwise enrichment would
    # recursively register the successor as a historical context.
    contexts = dict(historical_contexts)
    contexts[ctx["successor"]["bytes_sha256"]] = {"validated": ctx["successor"], "plan_commit": ctx["manifest"]["plan_commit"]}
    reports: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    line_hashes = {index: sha_bytes(line)
                   for index, line in enumerate(ctx["raw"].splitlines(keepends=True))}
    tail = rows[SEALED_ROWS:] if final else []
    for index, row in enumerate(rows[:SEALED_ROWS] + tail):
        if row.get("status") != "completed":
            if row in tail:
                _validate_row_identity(ctx, row)
                failures.append(_verify_codeql_terminal_failure(
                    ctx, row, line_hashes[index],
                ))
            else:
                # Every historical terminal row is checked against its own
                # contract, started/completed receipts, and bound streams.
                # The C4 packet's 86-row projection is never a license to
                # skip the continuation-03/04 failures at rows 86/87.
                origin = _historical_contract_context(ctx, row)
                group = executor._historical_group_for_replay(origin, row)
                number = _attempt_number(row.get("attempt_id"))
                attempt_dir = ctx["root"] / Path("reports/releases/v0.9.2/attempts") / str(row["attempt_id"])
                completed_path = attempt_dir / "completed.json"
                require(completed_path.is_file() and not completed_path.is_symlink(),
                        f"retained failure completed receipt is missing: {row.get('attempt_id')}")
                try:
                    failure = checker._verify_failed_attempt(
                        ctx["root"], origin, group, row, row["plan_commit"], number,
                        line_hashes[index], sha(completed_path),
                    )
                except Exception as exc:
                    raise CodeQLContinuationError(
                        f"retained failure replay rejected: {row.get('attempt_id')}: {exc}"
                    ) from exc
                failures.append(failure)
            continue
        entry = contexts.get(row.get("contract_sha256"))
        require(isinstance(entry, dict), f"retained row has no registered context: {row.get('attempt_id')}")
        origin = entry["validated"]
        group = executor._historical_group_for_replay(origin, row)
        number = _attempt_number(row.get("attempt_id"))
        bindings, _counts = checker._verify_one_group(
            ctx["root"], origin, group, row, entry["plan_commit"], number,
        )
        if selected_rows.get(row.get("group_id"), {}).get("attempt_id") == row.get("attempt_id"):
            reports.extend(bindings)
    require(not any("stale" in str(item).lower() for item in reports),
            "CodeQL replay selected a stale report")
    successful_tail = bool(tail and tail[0].get("status") == "completed")
    expected_partitions = 87 if successful_tail else 82
    expected_rows = 4144 if successful_tail else 4036
    require(len(reports) == expected_partitions and
            sum(item.get("rows", 0) for item in reports) == expected_rows,
            "CodeQL retained replay denominator changed")
    if final:
        declared = ctx["manifest"].get("terminal_outcome", {}).get("mode")
        actual = "success" if successful_tail else "failure"
        # A sealed prospective manifest may use terminal_outcome=pending and
        # bind both reviewed denominators.  Verification derives the actual
        # mode from the immutable tail row; it never rewrites that manifest.
        require(declared in {"pending", actual},
                "CodeQL manifest terminal outcome does not match the retained tail")
        if declared == "pending":
            pair = ctx["manifest"].get("terminal_expected")
            if pair is None and "expected_after_success" in ctx["manifest"] and \
                    "expected_after_failure" in ctx["manifest"]:
                pair = {
                    "success": ctx["manifest"].get("expected_after_success"),
                    "failure": ctx["manifest"].get("expected_after_failure"),
                }
            require(pair == {
                "success": {"ledger_rows": 89, "selected_groups": 83,
                             "partitions": 87, "rows": 4144, "known_stale": 0},
                "failure": {"ledger_rows": 89, "selected_groups": 82,
                             "partitions": 82, "rows": 4036, "known_stale": 0},
            }, "pending CodeQL manifest lacks both reviewed terminal outcomes")
    status = ("fresh-evidence-verified" if successful_tail else "terminal-failure-handoff") if final \
        else "continuation-preflight-passed"
    return {"status": status,
            "ledger_rows": SEALED_ROWS + (1 if final else 0),
            "selected_groups": HISTORICAL_COMPLETED + (1 if final and successful_tail else 0),
            "partitions": len(reports), "rows": sum(item.get("rows", 0) for item in reports),
            "known_stale": 0, "selected_attempts": list(selected_rows.values()),
            "fresh_reports": reports, "failed_attempts": failures,
            "terminal_outcome": "success" if successful_tail else ("failure" if tail else "pending")}


def _validate_terminal_failure(ctx: dict[str, Any], row: dict[str, Any]) -> None:
    """Require a durable, source-bound failure handoff with no retry semantics."""
    require(row.get("status") in {"failed", "timed-out", "capacity-lost", "recorder-error"},
            "CodeQL terminal handoff has an unrecognized status")
    require(row.get("timed_out") is False or row.get("status") == "timed-out",
            "CodeQL terminal handoff timeout/status disagree")
    require(isinstance(row.get("started_receipt"), str) and row["started_receipt"] == "started.json",
            "CodeQL terminal handoff lacks its started receipt")
    attempt_dir = ctx["root"] / Path("reports/releases/v0.9.2/attempts") / str(row["attempt_id"])
    for receipt_name in ("started.json", "completed.json"):
        receipt_path = attempt_dir / receipt_name
        require(receipt_path.is_file() and not receipt_path.is_symlink(),
                f"CodeQL terminal handoff lacks durable {receipt_name}")
    for stream_name in ("stdout", "stderr"):
        stream = row.get(stream_name)
        require(isinstance(stream, dict) and isinstance(stream.get("path"), str) and
                RE_SHA.fullmatch(str(stream.get("sha256") or "")) and
                type(stream.get("bytes")) is int and stream["bytes"] >= 0,
                f"CodeQL terminal handoff lacks a bound {stream_name} stream")
        attempt_dir = ctx["root"] / Path("reports/releases/v0.9.2/attempts") / str(row["attempt_id"])
        stream_path = attempt_dir / Path(*_relative(stream["path"], f"{stream_name} path").parts)
        require(stream_path.is_file() and not stream_path.is_symlink() and
                sha(stream_path) == stream["sha256"] and stream_path.stat().st_size == stream["bytes"],
                f"CodeQL terminal {stream_name} stream is missing or changed")
    execution_root = row.get("execution_root")
    require(isinstance(execution_root, str) and Path(execution_root).is_absolute(),
            "CodeQL terminal handoff lacks an absolute execution root")
    expected_root = (ctx["root"] / "execution-state/v092/groups/series-01" / CODEQL_GROUP / "attempt-01").resolve()
    require(Path(execution_root).resolve() == expected_root,
            "CodeQL terminal handoff execution root changed")


def _verify_codeql_terminal_failure(ctx: dict[str, Any], row: dict[str, Any],
                                    ledger_line_sha256: str) -> dict[str, Any]:
    """Run the frozen failure verifier over the prospective CodeQL tail.

    Stream checks are useful diagnostics, but they are not terminal evidence.
    The immutable row, normalized successor context, started/completed
    receipts, and ledger-line hash must all pass the frozen checker before a
    failure handoff can be exposed to Bifrost recovery.
    """
    _validate_terminal_failure(ctx, row)
    executor = ctx["frozen"]["executor"]
    checker = ctx["frozen"]["checker"]
    origin = ctx["successor"]
    group = executor._historical_group_for_replay(origin, row)
    number = _attempt_number(row.get("attempt_id"))
    completed_path = ctx["root"] / Path("reports/releases/v0.9.2/attempts") / str(row["attempt_id"]) / "completed.json"
    try:
        return checker._verify_failed_attempt(
            ctx["root"], origin, group, row, row["plan_commit"], number,
            ledger_line_sha256, sha(completed_path),
        )
    except Exception as exc:
        raise CodeQLContinuationError(
            f"CodeQL terminal failure rejected by frozen checker: {row.get('attempt_id')}: {exc}"
        ) from exc


def _validated_ledger_bytes(root: Path, raw: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    """Validate a supplied immutable prefix without reading mutable tails."""
    sealed = _read(root, SEALED_LEDGER, "sealed ledger prefix")
    require(sha_bytes(sealed) == SEALED_LEDGER_SHA and len(sealed.splitlines()) == SEALED_ROWS,
            "sealed ledger prefix binding changed")
    lines = raw.splitlines(keepends=True)
    require(len(lines) in {SEALED_ROWS, SEALED_ROWS + 1} and
            b"".join(lines[:SEALED_ROWS]) == sealed,
            "supplied ledger prefix does not begin with the exact sealed 88-row prefix")
    _assert_live_ledger_prefix(root, raw)
    rows = _parse_ledger(raw)
    require(len(rows) == len(lines), "supplied ledger JSON rows and bytes differ")
    return raw, rows


def _assert_live_ledger_prefix(root: Path, raw: bytes) -> None:
    """Require supplied recovery bytes to be an exact canonical-ledger prefix."""
    supplied_lines = raw.splitlines(keepends=True)
    require(len(supplied_lines) in {SEALED_ROWS, SEALED_ROWS + 1},
            "supplied ledger prefix has an unsupported row count")
    path = _path(root, LEDGER, "live ledger")
    require(path.is_file() and not path.is_symlink(),
            "canonical live ledger is not a regular file")
    try:
        live = path.read_bytes()
    except OSError as exc:
        raise CodeQLContinuationError("canonical live ledger cannot be read") from exc
    live_lines = live.splitlines(keepends=True)
    require(len(live_lines) >= len(supplied_lines) and live.startswith(raw),
            "supplied ledger bytes are not the exact canonical ledger prefix")


def _assert_source_snapshot(ctx: dict[str, Any]) -> dict[str, Any]:
    """Run the immutable frozen source snapshot gate for this successor.

    The CodeQL02 stop was caused by three already-present untracked scripts.
    This successor binds those files as explicit contract ``source_inputs``;
    the frozen executor remains the authority and is called with the exact
    successor commit and source-input list.  The check is intentionally
    repeated by ``execute`` immediately before any fresh namespace can be
    consumed, so a source tree drift cannot become an attempt.
    """
    root = Path(ctx["root"]).resolve()
    executor = ctx["frozen"]["executor"]
    checker = getattr(executor, "_assert_source_snapshot", None)
    require(callable(checker), "frozen executor lacks _assert_source_snapshot")
    successor = ctx.get("successor")
    require(isinstance(successor, dict) and isinstance(successor.get("plan"), dict),
            "CodeQL successor context lacks its bound plan")
    source_commit = successor["plan"].get("source_commit")
    source_inputs = successor.get("source_inputs")
    require(isinstance(source_commit, str) and RE_COMMIT.fullmatch(source_commit),
            "CodeQL successor source commit is malformed")
    require(isinstance(source_inputs, list) and source_inputs,
            "CodeQL successor source closure is empty")
    try:
        checker(root, source_commit, FROZEN_EXECUTOR[1], source_inputs)
    except Exception as exc:
        raise CodeQLContinuationError(
            f"frozen CodeQL source snapshot rejected successor closure: {exc}"
        ) from exc
    result = {
        "schema": "v092-codeql-frozen-source-snapshot/v1",
        "verified": True,
        "source_commit": source_commit,
        "runner_source_sha256": FROZEN_EXECUTOR[1],
        "source_input_count": len(source_inputs),
    }
    ctx["source_snapshot"] = result
    return result


def _maybe_assert_source_snapshot(ctx: dict[str, Any], *, terminal: bool) -> None:
    """Apply the live-tree gate only to pre-attempt validation.

    Once CodeQL has completed, Bifrost recovery may run from the immutable
    CodeQL source/plan commit after later Rust source commits.  Terminal
    verification still checks the committed contract and replay evidence, but
    must not compare that historical source closure with the later live tree.
    ``execute`` calls the live gate explicitly immediately before dispatch.
    """
    if terminal is False:
        _assert_source_snapshot(ctx)


def validate(root: Path = ROOT, manifest_path: str = MANIFEST,
             manifest_sha256: str | None = None, *, final: bool = False,
             terminal: bool | None = None, replay: bool = False,
             ledger_raw: bytes | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    terminal = final if terminal is None else terminal
    require(manifest_path in {MANIFEST, PROVISIONAL_MANIFEST}, "unregistered CodeQL manifest path")
    manifest_raw = _read(root, manifest_path, "CodeQL continuation manifest")
    digest = sha_bytes(manifest_raw)
    require(manifest_sha256 == digest, "CodeQL manifest SHA differs")
    manifest = json.loads(manifest_raw)
    require(isinstance(manifest, dict), "CodeQL continuation manifest is not an object")
    _check_manifest(root, manifest, manifest_path, final=final, terminal=terminal)
    _ref(root, {"path": QUERY_RECEIPT, "sha256": QUERY_RECEIPT_SHA}, "CodeQL query receipt")
    raw, rows = _ledger(root) if ledger_raw is None else _validated_ledger_bytes(root, ledger_raw)
    _check_prefix(rows)
    _tail(rows, final=terminal)
    frozen = load_frozen(root)
    base_raw = _read(root, BASE_CONTRACT, "frozen base contract")
    require(sha_bytes(base_raw) == BASE_SHA, "frozen base contract changed")
    base_contract = json.loads(base_raw)
    successor_ref = manifest.get("continuation_contract")
    contract_raw = _ref(root, successor_ref, "CodeQL continuation contract")
    contract = json.loads(contract_raw)
    require(isinstance(contract, dict), "CodeQL continuation contract is not an object")
    committed_contract = _git_blob(
        root, manifest["plan_commit"], successor_ref["path"],
        "CodeQL continuation contract",
    )
    require(committed_contract == contract_raw,
            "CodeQL continuation contract differs from its registered plan commit")
    _check_contract_delta(root, base_contract, contract, manifest)
    # The expensive frozen base validation is intentionally the final read-only
    # gate before replay/materialization. Tests may inject a validated fixture.
    base = _validate_base(frozen["executor"], root, rows[:SEALED_ROWS], b"".join(raw.splitlines(keepends=True)[:SEALED_ROWS]))
    require(base.get("bytes_sha256") == BASE_SHA, "frozen base validator returned a changed contract")
    successor = _successor_context(base, contract, contract_raw, root)
    ctx = {"root": root, "manifest": manifest, "manifest_sha256": digest,
           "rows": rows, "raw": raw,
           "ledger_raw_supplied": ledger_raw is not None,
           "frozen": frozen, "base": base, "base_contract": base_contract,
           "base_plan_commit": manifest.get("base_plan_commit"),
           "successor": successor, "successor_contract": contract}
    _enrich_successor_historical_contexts(ctx)
    if replay:
        ctx["replay"] = _replay_completed(ctx, final=terminal)
        _attach_verified_runtime_recovery(ctx)
    else:
        ctx["runtime_recovery_verified"] = False
    # Prospective validation follows contract binding and (when requested)
    # retained replay, and precedes all fresh namespace/attempt work. Terminal
    # recovery intentionally uses the committed historical closure instead of
    # comparing it with a later live Rust tree.
    _maybe_assert_source_snapshot(ctx, terminal=terminal)
    _validate_runtime_context_registration(ctx)
    return ctx


def recover_bifrost_history(root: Path, manifest_path: str,
                            manifest_sha256: str, prefix_raw: bytes) -> dict[str, Any]:
    """Export the lossless CodeQL context expected by the Bifrost bridge.

    The bridge supplies the actual 89-row post-CodeQL prefix.  We validate
    that exact byte stream through this module, including all six historical
    terminal failures, then return only the typed base and CodeQL continuation
    contexts.  Bifrost adds its own replacement context after this function;
    no serialized context or caller-selected replacement is accepted here.
    """
    root = Path(root).resolve()
    require(manifest_path == MANIFEST, "CodeQL recovery manifest is not the final registered manifest")
    require(isinstance(prefix_raw, bytes), "CodeQL recovery prefix must be raw bytes")
    live_raw = _read(root, LEDGER, "live ledger")
    require(live_raw.startswith(prefix_raw) and len(prefix_raw.splitlines()) == SEALED_ROWS + 1,
            "CodeQL recovery prefix is not the exact leading 89-row ledger bytes")
    ctx = validate(root, manifest_path, manifest_sha256, final=True, replay=True,
                   ledger_raw=prefix_raw)
    require(ctx["raw"] == prefix_raw, "CodeQL recovery replay used different ledger bytes")
    successor = ctx["successor"]
    successor_sha = successor["bytes_sha256"]
    continuation = {
        "validated": successor,
        "plan_commit": ctx["manifest"]["plan_commit"],
        "source_commit": ctx["manifest"]["source_commit"],
        "role": "continuation",
    }
    base = {
        "validated": ctx["base"],
        "plan_commit": ctx["base_plan_commit"],
        "source_commit": ctx["base"]["plan"].get("source_commit"),
        "role": "base",
    }
    contexts: dict[str, dict[str, Any]] = {}
    recovered = _historical_replay_contexts(ctx)
    for key, value in recovered.items():
        require(isinstance(value, dict) and isinstance(value.get("validated"), dict),
                f"frozen historical context is malformed: {key}")
        contexts[key] = {**value, "source_commit": value["validated"]["plan"].get("source_commit"),
                         "role": "historical"}
    contexts[BASE_SHA] = base
    contexts[successor_sha] = continuation
    return {
        "base": base,
        "contexts": contexts,
        "repaired": continuation,
        "prefix_sha256": sha_bytes(prefix_raw),
    }


def execute(ctx: dict[str, Any]) -> dict[str, Any]:
    require(ctx.get("runtime_recovery_verified") is True,
            "CodeQL execute requires a verified retained replay")
    # Re-run the frozen immutable source gate immediately before any output,
    # attempt, or materialized namespace can be consumed.
    _assert_source_snapshot(ctx)
    require(len(ctx["rows"]) == SEALED_ROWS, "CodeQL attempt is no longer the first successor tail")
    admission = ctx["manifest"].get("execution_admission")
    require(admission == {"path": ADMISSION_RECEIPT},
            "CodeQL execution admission path is not the canonical receipt")
    admission_value = _json(ctx["root"], admission["path"], "CodeQL execution admission")
    manifest_sha256 = ctx.get("manifest_sha256")
    require(isinstance(manifest_sha256, str) and RE_SHA.fullmatch(manifest_sha256),
            "CodeQL execution context lacks the sealed manifest SHA")
    require(admission_value.get("manifest") == {
        "path": MANIFEST, "sha256": manifest_sha256,
    } and admission_value.get("manifest_sha256") == manifest_sha256,
            "CodeQL execution admission is bound to a different manifest")
    require(admission_value.get("module_sha256") == sha(
        ctx["root"] / Path(*_relative(MODULE_SOURCE).parts)),
            "CodeQL execution admission is bound to a different continuation source")
    require(admission_value.get("supervisor_sha256") == sha(
        ctx["root"] / Path(*_relative(SUPERVISOR_SOURCE).parts)),
            "CodeQL execution admission is bound to a different supervisor source")
    require(admission_value.get("ledger_prefix") == {
        "path": SEALED_LEDGER, "sha256": SEALED_LEDGER_SHA, "rows": SEALED_ROWS,
    }, "CodeQL execution admission is bound to a different sealed ledger prefix")
    require(admission_value.get("status") == "ready-to-execute" and
            admission_value.get("automatic_retry") is False,
            "CodeQL execution admission is not ready")
    output = ctx["root"] / Path(*_relative(CODEQL_OUTPUT_ROOT).parts)
    require(not output.exists() and not output.is_symlink(), "CodeQL output namespace is not fresh")
    executor = ctx["frozen"]["executor"]
    # Repeat the complete source/archive and aggregate working-capacity
    # preflight immediately before the frozen runner. The runner repeats the
    # same guard under its exclusive lock before creating the attempt root.
    ctx["materialized_preflight"] = materialized_preflight(ctx)
    runtime = _runtime_lease(ctx["successor"], ctx["root"])
    group = _base_group(ctx["successor"]["plan"])
    build_worker_environment(executor, group, Path("/codeql-execution"), Path("/codeql-attempt"), Path("/codeql-cache"))
    # run_group owns the frozen exclusive lock.  The scoped adapter raises the
    # frozen pre-attempt check to 127 GiB on both its normal and C4 recovery
    # branches, without taking a second lock or changing the frozen 110 GiB
    # minimum, contender scan, source, or process checks.
    with _scoped_locked_resource_floor(executor, ctx["root"]), \
         _scoped_source_projection_guard(executor):
        result = executor.run_group(runtime, CODEQL_GROUP)
    require(isinstance(result, dict) and result.get("group_id") == CODEQL_GROUP and
            result.get("attempt_id") == CODEQL_ATTEMPT and result.get("status") == "completed" and
            result.get("exit_code") == 0 and result.get("timed_out") is False and
            result.get("capacity_loss") is None,
            "CodeQL attempt did not complete successfully")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "validate", "verify", "execute"))
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        final = args.command in {"verify", "execute"}
        # Execute validates the final review against the sealed prefix before
        # it creates an attempt.  Only verify runs the terminal ledger gate;
        # otherwise pre-launch validation would demand a row the launch is
        # responsible for producing.
        terminal = args.command == "verify"
        ctx = validate(ROOT, args.manifest, args.manifest_sha256, final=final,
                       terminal=terminal,
                       replay=args.command in {"preflight", "verify", "execute"})
        if args.command == "execute":
            result = execute(ctx)
        elif args.command == "verify":
            result = ctx["replay"]
        else:
            result = ctx.get("replay", {"status": "validated", "ledger_rows": len(ctx["rows"])})
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    except (CodeQLContinuationError, OSError, subprocess.SubprocessError) as exc:
        print(f"codeql continuation rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
