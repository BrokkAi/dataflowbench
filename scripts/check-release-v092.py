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
D8_VERSION_WITNESS_PATH = "reports/releases/v0.9.2/acquisition/d8-version-witness-01.json"
D8_VERSION_WITNESS_SHA256 = "7aca9c89f40d14448aa11fe508e21bb6dda781595dcb7bdfa449358dea4829bb"
D8_VERSION_LINE = (
    "D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 "
    "from go/r8bot (luci-r8-custom-ci-archive-0-gths))"
)
D8_JAR_SHA256 = "4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294"
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
        "captured_files", "reports", "recorder_error", "failed_staging_artifacts", "process_ownership",
    })
    _require(set(receipt) <= allowed_receipt_fields,
             f"{group_id}: failed attempt receipt contains unknown fields")
    if status == "recorder-error":
        _require({"recorder_error", "captured_files", "failed_staging_artifacts"} <= set(receipt),
                 f"{group_id}: recorder-error receipt is missing its error or capture inventory")
        _verify_process_ownership(group_id, status, receipt.get("process_ownership"), required=False)
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
        _require(type(exit_code) is int and type(timed_out) is bool and
                 isinstance(capacity_loss, str) and bool(capacity_loss),
                 f"{group_id}: capacity-lost status lacks the measured capacity failure")
    else:
        recorder_error = receipt.get("recorder_error")
        _require(isinstance(recorder_error, str) and bool(recorder_error.strip()),
                 f"{group_id}: recorder-error status lacks its failure detail")
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
    _require((status == "recorder-error") or not artifact_paths,
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

    return {
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
    plan_commit, selected_attempts, prior_failures = _select_attempts(
        plan, validated["bytes_sha256"], ledger_rows,
        validated.get("prior_failed_contracts", {}),
    )
    expected_ids = set(groups)
    _require(set(selected_attempts) == expected_ids,
             "ledger must select exactly one completed attempt for each of 84 groups")
    _assert_committed_contract(root, validated, plan_commit)
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
        receipt, ledger_line_sha256, attempt_number = selected_attempts[group_id]
        group = groups[group_id]
        bindings, counts = _verify_one_group(
            root, validated, group, receipt, plan_commit, attempt_number,
        )
        for binding in bindings:
            _require(binding["adapter"] not in report_paths, "report partition was emitted more than once")
            report_paths.add(binding["adapter"])
            _require(binding["staged_path"] not in staged_report_paths,
                     "staged report path was emitted more than once")
            staged_report_paths.add(binding["staged_path"])
            row_count += binding["rows"]
            binding["attempt_id"] = receipt["attempt_id"]
            binding["attempt_number"] = attempt_number
            bound_reports.append(binding)
        outcome_counts.update(counts)
        completed_bytes = (root / Path(*ATTEMPTS_ROOT.parts) / receipt["attempt_id"] / "completed.json").read_bytes()
        selected_summaries.append({
            "group_id": group_id,
            "attempt_id": receipt["attempt_id"],
            "attempt_number": attempt_number,
            "status": "completed",
            "ledger_line_sha256": ledger_line_sha256,
            "started_receipt_sha256": _sha((root / Path(*ATTEMPTS_ROOT.parts) /
                                             receipt["attempt_id"] / "started.json").read_bytes()),
            "completed_receipt_sha256": _sha(completed_bytes),
        })

    failed_summaries = []
    prior_failure_summary_rows = []
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
        if failure_summary["inherited_from_prior_contract"]:
            review_sha256 = _verify_preanalysis_failure_review(
                root, validated, failure_validated, origin_contract_sha256,
                origin_plan_commit, receipt, ledger_line_sha256, failure_summary,
            )
            failure_summary["version_gate_review"] = {
                "path": PREANALYSIS_FAILURE_REVIEW.as_posix(),
                "sha256": review_sha256,
            }
        failed_summaries.append(failure_summary)
        if failure_summary["inherited_from_prior_contract"]:
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
    return {
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
