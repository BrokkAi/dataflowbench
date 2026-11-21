#!/usr/bin/env python3
"""Bind a paused v0.9.2 timing campaign before a prospective continuation.

The checkpoint is a read-only inventory. It does not dispatch analyzers, alter
the parent campaign, or turn timing observations into release qualification.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import subprocess


SCHEMA = "v092-timing-checkpoint/v1"
SOURCE_GROUPS = 84
EXPECTED_COMPLETED = 55
EXPECTED_REMAINING = 38
EXPECTED_BLOCKED_SWIFT = {"codeql-swift-common108", "joern-swift-common108"}
EXPECTED_FIRST_REMAINING = "joern-php-kernel"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
CAMPAIGN_ID = re.compile(r"\d{8}-(?:0[1-9]|[1-9]\d)\Z")
QUALIFIED_HELPER = "scripts/v092_timing_qualified_campaign.py"
CHECKPOINT_HELPER = "scripts/v092_timing_checkpoint.py"


def sha(path: Path) -> str:
    """Return the SHA-256 of a regular file, rejecting symlinks and special files."""
    path = Path(path)
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"evidence path is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_sha(value: object, description: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise RuntimeError(f"{description} must be a lowercase SHA-256")
    return value


def _repo_path(root: Path, value: str | Path, description: str) -> tuple[str, Path]:
    root_value = Path(root)
    root_absolute = root_value if root_value.is_absolute() else Path.cwd() / root_value
    root = root_value.resolve()
    supplied = Path(value)
    raw_candidate = supplied if supplied.is_absolute() else root_absolute / supplied
    try:
        relative = raw_candidate.relative_to(root_absolute)
    except ValueError as exc:
        raise RuntimeError(f"{description} must remain inside the repository") from exc
    posix = PurePosixPath(relative.as_posix())
    if posix.is_absolute() or not posix.parts or any(part in {"", ".", ".."} for part in posix.parts):
        raise RuntimeError(f"{description} must be a safe repository-relative path")
    candidate = root_absolute / Path(*posix.parts)
    _reject_symlink_components(root_absolute, candidate)
    return posix.as_posix(), candidate


def _reject_symlink_components(root: Path, path: Path) -> None:
    root = Path(root)
    if not root.is_absolute():
        root = Path.cwd() / root
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"path escapes repository root: {candidate}") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"symlink is not allowed in checkpoint evidence: {cursor}")


def _read_bytes(root: Path, reference: dict, description: str) -> tuple[bytes, str]:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise RuntimeError(f"{description} reference must contain path and sha256")
    relative, path = _repo_path(root, reference["path"], description)
    expected = _valid_sha(reference["sha256"], f"{description} sha256")
    if not path.is_file():
        raise RuntimeError(f"{description} is missing: {relative}")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise RuntimeError(f"{description} SHA-256 differs: {relative}")
    return raw, relative


def _read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{description} must be a JSON object: {path}")
    return value


def _file_reference(root: Path, path: Path, description: str) -> dict:
    relative, path = _repo_path(root, path, description)
    return {"path": relative, "sha256": sha(path)}


def _inventory_file(root: Path, path: Path, seen: dict[str, dict]) -> None:
    relative, path = _repo_path(root, path, "evidence file")
    if relative in seen:
        raise RuntimeError(f"duplicate checkpoint evidence path: {relative}")
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"evidence path is not a regular file: {relative}")
    seen[relative] = {"path": relative, "sha256": sha(path), "size_bytes": path.stat().st_size}


def _inventory_tree(root: Path, target: Path, seen: dict[str, dict], *, allow_missing: bool = False) -> None:
    """Inventory only an explicitly authorized report/output tree."""
    root = Path(root)
    target = Path(target)
    _reject_symlink_components(root, target)
    if not target.exists() and not target.is_symlink():
        if allow_missing:
            return
        raise RuntimeError(f"evidence output root is missing: {target}")
    mode = target.lstat().st_mode
    if stat.S_ISREG(mode):
        _inventory_file(root, target, seen)
        return
    if not stat.S_ISDIR(mode):
        raise RuntimeError(f"evidence output root is not a regular file or directory: {target}")

    def visit(directory: Path) -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            raise RuntimeError(f"cannot inventory evidence directory: {directory}") from exc
        for entry in entries:
            child = Path(entry.path)
            if entry.is_symlink():
                raise RuntimeError(f"symlink is not allowed in checkpoint evidence: {child}")
            if entry.is_dir(follow_symlinks=False):
                visit(child)
            elif entry.is_file(follow_symlinks=False):
                _inventory_file(root, child, seen)
            else:
                raise RuntimeError(f"special file is not allowed in checkpoint evidence: {child}")

    visit(target)


def _inventory_report(root: Path, report: Path) -> dict[str, dict]:
    if not report.is_dir() or report.is_symlink():
        raise RuntimeError(f"parent report directory is missing or symlinked: {report}")
    seen: dict[str, dict] = {}
    _inventory_tree(root, report, seen)
    return seen


def _campaign_id(value: object) -> str:
    if not isinstance(value, str) or CAMPAIGN_ID.fullmatch(value) is None:
        raise RuntimeError("campaign_id must use YYYYMMDD-NN format")
    try:
        dt.datetime.strptime(value[:8], "%Y%m%d")
    except ValueError as exc:
        raise RuntimeError("campaign_id must contain a valid calendar date") from exc
    return value


def _parse_utc(value: object, description: str) -> dt.datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"{description} must be an RFC 3339 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"{description} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{description} must include a UTC offset")
    return parsed.astimezone(dt.timezone.utc)


def _plan_groups(plan: dict) -> tuple[list[dict], list[dict], list[dict]]:
    groups = plan.get("groups")
    if not isinstance(groups, list) or not all(isinstance(group, dict) for group in groups):
        raise RuntimeError("parent plan groups must be a list of objects")
    ids = [group.get("id") for group in groups]
    if not all(isinstance(group_id, str) and group_id for group_id in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("parent plan groups must have unique nonempty IDs")
    if plan.get("group_order") != ids:
        raise RuntimeError("parent plan group order differs from its group list")
    cold = [group for group in groups if group.get("kind") == "cold"]
    ready = [group for group in groups if group.get("status") == "ready"]
    blocked = [group for group in groups if group.get("status") == "blocked"]
    if len(cold) != SOURCE_GROUPS or len(groups) != 95 or len(ready) != 93:
        raise RuntimeError("parent plan must retain 84 cold groups and 93 ready commands")
    blocked_cold = [group for group in cold if group.get("status") == "blocked"]
    if (len(blocked) != 2 or {group["id"] for group in blocked_cold} != EXPECTED_BLOCKED_SWIFT
            or any(group.get("kind") != "cold" for group in blocked)):
        raise RuntimeError("parent plan must retain exactly the two blocked Swift cold groups")
    if sum(group.get("kind") == "overhead" and group.get("status") == "ready" for group in groups) != 9:
        raise RuntimeError("parent plan must retain nine ready overhead commands")
    if sum(group.get("kind") == "warm" and group.get("status") == "ready" for group in groups) != 2:
        raise RuntimeError("parent plan must retain two ready warm commands")
    if any(group.get("kind") not in {"cold", "overhead", "warm"} for group in groups):
        raise RuntimeError("parent plan contains an unsupported group kind")
    return groups, ready, blocked


def _verify_parent_plan_commit(root: Path, plan_path: Path, plan: dict, start: dict) -> str:
    commit = start.get("plan_commit")
    if not isinstance(commit, str) or COMMIT.fullmatch(commit) is None:
        raise RuntimeError("campaign-start plan_commit must be a full commit SHA")
    try:
        relative = plan_path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("parent plan must be inside the repository") from exc
    try:
        committed = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot verify parent plan at its campaign-start commit") from exc
    if committed != plan_path.read_bytes():
        raise RuntimeError("parent plan bytes differ from campaign-start plan_commit")
    return commit


def _validate_start_and_pause(plan: dict, pause: dict, start: dict,
                              plan_sha256: str, progress_sha256: str,
                              ready: list[dict], completed: list[str], remaining: list[str]) -> None:
    campaign_id = _campaign_id(plan.get("campaign_id"))
    if (start.get("campaign_id") != campaign_id or start.get("plan_sha256") != plan_sha256
            or start.get("source_commit") != plan.get("release_commit")):
        raise RuntimeError("campaign-start identity differs from the parent plan")
    if (start.get("ready_commands") != len(ready)
            or start.get("planned_cold_groups") != SOURCE_GROUPS
            or start.get("ready_cold_groups") != SOURCE_GROUPS - 2
            or start.get("blocked_cold_groups") != 2
            or start.get("max_campaign_wall_seconds") != plan.get("max_campaign_wall_seconds")):
        raise RuntimeError("campaign-start coverage or wall budget differs from the parent plan")
    if pause.get("schema") != "dataflowbench-v092-user-pause/v1":
        raise RuntimeError("unsupported user-pause receipt schema")
    if (pause.get("campaign_id") != campaign_id or pause.get("status") != "paused-between-commands"
            or pause.get("plan_sha256") != plan_sha256
            or pause.get("progress_sha256") != progress_sha256):
        raise RuntimeError("pause receipt identity or bound hashes differ")
    if (pause.get("completed_command_count") != EXPECTED_COMPLETED
            or pause.get("remaining_ready_command_count") != EXPECTED_REMAINING
            or pause.get("completed_groups") != completed
            or pause.get("remaining_ready_groups") != remaining):
        raise RuntimeError("pause receipt group counts or order differ from progress")
    if (pause.get("active_analyzer_groups") != [] or pause.get("invocations_interrupted") is not False
            or pause.get("existing_evidence_unchanged") is not True
            or pause.get("automatic_resume") is not False):
        raise RuntimeError("pause receipt does not prove a clean pause between invocations")
    if (pause.get("signal") != "SIGSTOP"
            or not isinstance(pause.get("observed_process_state"), str)
            or not pause["observed_process_state"].startswith("T")
            or type(pause.get("supervisor_pid")) is not int or pause["supervisor_pid"] <= 0
            or not isinstance(pause.get("supervisor_start_identity"), str)
            or not pause["supervisor_start_identity"]):
        raise RuntimeError("pause receipt lacks the stopped supervisor identity")
    _parse_utc(pause.get("paused_utc"), "pause paused_utc")

    command = pause.get("supervisor_command")
    if not isinstance(command, str):
        raise RuntimeError("pause receipt lacks supervisor command")
    fields = shlex.split(command)
    expected_tail = ["scripts/v092_timing_qualified_campaign.py", "execute", "--plan",
                     f"reports/timing/v0.9.2/{campaign_id}/qualified-plan.json"]
    if len(fields) < 4 or fields[-4:] != expected_tail:
        raise RuntimeError("pause supervisor command differs from the bound parent plan")


def _validate_progress(raw: bytes, ready: list[dict]) -> tuple[list[str], list[str]]:
    try:
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("parent progress is not valid JSONL") from exc
    if len(rows) != EXPECTED_COMPLETED * 2:
        raise RuntimeError("parent progress must contain exactly 55 started/completed pairs")
    completed = []
    for index in range(0, len(rows), 2):
        started, finished = rows[index:index + 2]
        if not isinstance(started, dict) or not isinstance(finished, dict):
            raise RuntimeError("parent progress rows must be objects")
        group_id = ready[index // 2]["id"]
        if (started.get("group") != group_id or started.get("status") != "started"
                or finished.get("group") != group_id
                or finished.get("status") != "completed-candidate-evidence"):
            raise RuntimeError("parent progress is not the exact alternating completed ready prefix")
        if _parse_utc(started.get("utc"), "progress started utc") > _parse_utc(
                finished.get("utc"), "progress completed utc"):
            raise RuntimeError("parent progress completion precedes its start")
        completed.append(group_id)
    if len(completed) != len(set(completed)):
        raise RuntimeError("parent progress contains duplicate completed groups")
    return completed, [group["id"] for group in ready[len(completed):]]


def _validate_successful_terminal(root: Path, report: Path, work: Path, plan: dict,
                                  group: dict, plan_sha256: str) -> dict:
    group_id = group["id"]
    attempt = report / "attempts" / group_id / "attempt-01"
    _reject_symlink_components(root, attempt)
    if not attempt.is_dir():
        raise RuntimeError(f"completed group lacks attempt-01: {group_id}")
    start_path, terminal_path = attempt / "start.json", attempt / "terminal.json"
    if not start_path.is_file() or not terminal_path.is_file():
        raise RuntimeError(f"completed group lacks start or terminal receipt: {group_id}")
    start = _read_json(start_path, f"{group_id} start receipt")
    terminal = _read_json(terminal_path, f"{group_id} terminal receipt")
    if (start.get("plan_sha256") != plan_sha256 or start.get("argv") != group.get("argv")
            or start.get("deadline_seconds") != group.get("deadline_seconds")
            or start.get("quiet_policy") != {"required_seconds": 300, "minimum_idle_percent": 90,
                                               "maximum_sample_gap_seconds": 60}):
        raise RuntimeError(f"completed group start receipt differs from the qualified plan: {group_id}")
    if (terminal.get("group") != group_id or terminal.get("status") != "completed-candidate-evidence"
            or terminal.get("exit_code") != 0 or terminal.get("timed_out") is not False
            or terminal.get("capacity_loss") is not None
            or terminal.get("publication_eligible") is not False
            or terminal.get("attempt") != 1 or terminal.get("automatic_retry") is not False):
        raise RuntimeError(f"completed group terminal is not a successful unqualified command: {group_id}")
    comparison = terminal.get("frozen_report_comparison")
    reconciliation = terminal.get("reconciliation")
    if (not isinstance(comparison, dict) or comparison.get("status") != "matched"
            or comparison.get("publication_eligible") is not False
            or not isinstance(reconciliation, dict)
            or reconciliation.get("publication_eligible") is not False):
        raise RuntimeError(f"completed group lacks matched frozen report comparison: {group_id}")
    descriptors = group.get("reports")
    comparisons = comparison.get("reports")
    reconciled = reconciliation.get("reports")
    frozen = plan.get("frozen_report_bindings", {}).get(group_id)
    if (not isinstance(descriptors, list) or not descriptors
            or not isinstance(comparisons, list) or not isinstance(reconciled, list)
            or not isinstance(frozen, list) or len(descriptors) != len(comparisons)
            or len(descriptors) != len(reconciled) or len(descriptors) != len(frozen)):
        raise RuntimeError(f"completed group report comparison counts differ: {group_id}")
    source = work / "sources" / group_id
    report_files = []
    for descriptor, observed, reconciled_report, frozen_report in zip(
            descriptors, comparisons, reconciled, frozen):
        source_path_value = descriptor.get("source_path")
        if not isinstance(source_path_value, str):
            raise RuntimeError(f"completed group report lacks source_path: {group_id}")
        source_relative = PurePosixPath(source_path_value)
        if source_relative.is_absolute() or any(part in {"", ".", ".."} for part in source_relative.parts):
            raise RuntimeError(f"completed group report path escapes its source: {group_id}")
        relative, report_file = _repo_path(root, source / Path(*source_relative.parts),
                                           f"{group_id} report output")
        actual_hash = sha(report_file)
        digest = _valid_sha(actual_hash, f"{group_id} report SHA-256")
        reconciled_path_value = reconciled_report.get("path")
        if not isinstance(reconciled_path_value, str) or not Path(reconciled_path_value).is_absolute():
            raise RuntimeError(f"reconciliation report path is malformed: {group_id}")
        _reconciled_rel, reconciled_path = _repo_path(root, reconciled_path_value,
                                                      f"{group_id} reconciled report")
        if (observed.get("contract_path") != descriptor.get("path")
                or observed.get("frozen_sha256") != frozen_report.get("sha256")
                or observed.get("measured_sha256") != digest
                or reconciled_path != report_file
                or reconciled_report.get("sha256") != digest):
            raise RuntimeError(f"preserved report bytes differ from reconciliation: {group_id}/{relative}")
        report_files.append((source_relative.as_posix(), json.loads(report_file.read_text()),
                             reconciled_report.get("timing_sidecars")))
    return_refs = []
    for relative, report_value, _sidecars in report_files:
        results = report_value.get("results")
        if not isinstance(results, list):
            raise RuntimeError(f"completed group report results are malformed: {group_id}/{relative}")
        for result in results:
            if not isinstance(result, dict):
                raise RuntimeError(f"completed group result is malformed: {group_id}/{relative}")
            raw_output = result.get("raw_output")
            if raw_output is None:
                continue
            if not isinstance(raw_output, str):
                raise RuntimeError(f"raw_output reference is malformed: {group_id}/{relative}")
            raw_relative = PurePosixPath(raw_output)
            if raw_relative.is_absolute() or any(part in {"", ".", ".."} for part in raw_relative.parts):
                raise RuntimeError(f"raw_output path escapes its source: {group_id}/{relative}")
            return_refs.append(raw_relative.as_posix())
    source_root = source
    for raw_output in return_refs:
        raw_path = source_root / Path(*PurePosixPath(raw_output).parts)
        _reject_symlink_components(root, raw_path)
        if not raw_path.is_file():
            raise RuntimeError(f"referenced raw output is missing: {group_id}/{raw_output}")
    return _file_reference(root, terminal_path, f"{group_id} terminal receipt"), return_refs


def _validate_pending_attempts(root: Path, report: Path, remaining: list[str]) -> None:
    attempts_root = report / "attempts"
    allowed_parent = {"attempt-01"}
    first = remaining[0] if remaining else None
    for group_id in remaining:
        group_root = attempts_root / group_id
        _reject_symlink_components(root, group_root)
        if not group_root.exists():
            continue
        if group_id != first or not group_root.is_dir():
            raise RuntimeError(f"pending group has pre-existing attempt output: {group_id}")
        children = sorted(path.name for path in group_root.iterdir())
        if children != sorted(allowed_parent):
            raise RuntimeError(f"first pending group has unexpected attempt directories: {group_id}")
        attempt = group_root / "attempt-01"
        _reject_symlink_components(root, attempt)
        files = sorted(path.name for path in attempt.iterdir())
        if files != ["host.jsonl"] or not (attempt / "host.jsonl").is_file():
            raise RuntimeError("first pending group may retain only its quiet-window host.jsonl")


def _validate_attempt_layout(root: Path, report: Path, completed: list[str], remaining: list[str]) -> None:
    attempts_root = report / "attempts"
    if not attempts_root.is_dir() or attempts_root.is_symlink():
        raise RuntimeError("parent attempts directory is missing or symlinked")
    actual = sorted(path.name for path in attempts_root.iterdir())
    expected = set(completed)
    first_pending = remaining[0] if remaining else None
    if first_pending is not None and (attempts_root / first_pending).exists():
        expected.add(first_pending)
    if actual != sorted(expected):
        raise RuntimeError("parent attempts directory contains unknown or incomplete group output")
    for group_id in completed:
        group_root = attempts_root / group_id
        _reject_symlink_components(root, group_root)
        if (not group_root.is_dir() or sorted(path.name for path in group_root.iterdir()) != ["attempt-01"]):
            raise RuntimeError(f"completed group must have exactly one attempt-01: {group_id}")


def _expected_scratch_roots(plan: dict, start: dict, work: Path) -> list[str]:
    ready = [group for group in plan["groups"] if group.get("status") == "ready"]
    owned = start.get("external_scratch_ownership")
    if not isinstance(owned, dict):
        raise RuntimeError("campaign-start external_scratch_ownership must be an object")
    expected = []
    for group in ready:
        source = work / "sources" / group["id"]
        expected.extend(str(source / name) for name in ("home", "tmp", "cache"))
        if group["id"] in owned:
            entry = owned[group["id"]]
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) \
                    or not Path(entry["path"]).is_absolute():
                raise RuntimeError(f"external scratch path is malformed: {group['id']}")
            expected.append(entry["path"])
    actual = start.get("scratch_roots")
    if actual != expected:
        raise RuntimeError("campaign-start scratch roots differ from the plan-bound group paths")
    return expected


def _make_checkpoint(root: Path, parent_plan_path: Path, pause_path: Path) -> dict:
    root = Path(root)
    plan_rel, plan_path = _repo_path(root, parent_plan_path, "parent plan")
    pause_rel, pause_file = _repo_path(root, pause_path, "pause receipt")
    if not plan_path.is_file() or not pause_file.is_file():
        raise RuntimeError("parent plan and pause receipt must exist as regular files")
    plan_bytes = plan_path.read_bytes()
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    plan = _read_json(plan_path, "parent plan")
    campaign_id = _campaign_id(plan.get("campaign_id"))
    expected_report_rel = f"reports/timing/v0.9.2/{campaign_id}"
    report_rel, report = _repo_path(root, expected_report_rel, "parent report root")
    if not plan_path.resolve().is_relative_to(report.resolve()) or pause_file.parent.resolve() != report.resolve():
        raise RuntimeError("parent plan and pause receipt must be in the campaign report directory")
    if not plan_path.name.startswith("qualified-plan") or plan_path.suffix != ".json":
        raise RuntimeError("parent plan must be a qualified-plan JSON file")
    pause_bytes = pause_file.read_bytes()
    pause_sha256 = hashlib.sha256(pause_bytes).hexdigest()
    pause = _read_json(pause_file, "pause receipt")
    progress_path = report / "progress.jsonl"
    if not progress_path.is_file() or progress_path.is_symlink():
        raise RuntimeError("parent progress.jsonl is missing or symlinked")
    progress_bytes = progress_path.read_bytes()
    progress_sha256 = hashlib.sha256(progress_bytes).hexdigest()
    start_path = report / "campaign-start.json"
    if not start_path.is_file() or start_path.is_symlink():
        raise RuntimeError("parent campaign-start.json is missing or symlinked")
    start = _read_json(start_path, "campaign-start receipt")
    groups, ready, _blocked = _plan_groups(plan)
    completed, remaining = _validate_progress(progress_bytes, ready)
    if len(completed) != EXPECTED_COMPLETED or len(remaining) != EXPECTED_REMAINING \
            or not remaining or remaining[0] != EXPECTED_FIRST_REMAINING:
        raise RuntimeError("parent progress is not the expected 55/38 Joern PHP frontier")
    _validate_start_and_pause(plan, pause, start, plan_sha256, progress_sha256,
                              ready, completed, remaining)
    _verify_parent_plan_commit(root, plan_path, plan, start)
    _parse_utc(start.get("created_utc"), "campaign-start created_utc")
    work_rel = f"execution-state/timing-v092-{campaign_id}"
    work = root / work_rel
    if work.is_symlink():
        raise RuntimeError("parent work namespace is symlinked")
    scratch_roots = _expected_scratch_roots(plan, start, work)

    seen = _inventory_report(root, report)
    terminal_refs = []
    raw_output_refs: dict[str, list[str]] = {}
    absent_output_roots = []
    for group in ready[:len(completed)]:
        terminal_ref, raw_refs = _validate_successful_terminal(
            root, report, work, plan, group, plan_sha256)
        terminal_refs.append({"group": group["id"], **terminal_ref})
        raw_output_refs[group["id"]] = raw_refs
        source = work / "sources" / group["id"]
        _reject_symlink_components(root, source)
        if not source.is_dir():
            raise RuntimeError(f"completed group source snapshot is missing: {group['id']}")
        output_roots = group.get("output_roots")
        if not isinstance(output_roots, list) or not output_roots:
            raise RuntimeError(f"completed group lacks output_roots: {group['id']}")
        for output in output_roots:
            if not isinstance(output, str):
                raise RuntimeError(f"completed group output root is malformed: {group['id']}")
            relative = PurePosixPath(output)
            if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
                raise RuntimeError(f"completed group output root escapes its source: {group['id']}")
            output_path = source / Path(*relative.parts)
            if not output_path.exists() and not output_path.is_symlink():
                referenced = False
                for descriptor in group.get("reports", []):
                    report_path_value = descriptor.get("source_path")
                    if not isinstance(report_path_value, str):
                        continue
                    report_relative = PurePosixPath(report_path_value)
                    report_file = source / Path(*report_relative.parts)
                    if not report_file.is_file():
                        continue
                    report_value = _read_json(report_file, f"{group['id']} measured report")
                    for result in report_value.get("results", []):
                        raw_output = result.get("raw_output") if isinstance(result, dict) else None
                        if isinstance(raw_output, str):
                            raw_relative = PurePosixPath(raw_output)
                            if raw_relative == relative or relative in raw_relative.parents:
                                referenced = True
                terminal_path = report / "attempts" / group["id"] / "attempt-01" / "terminal.json"
                terminal = _read_json(terminal_path, f"{group['id']} terminal receipt")
                sidecar_counts = [item.get("timing_sidecars") for item in
                                  terminal.get("reconciliation", {}).get("reports", [])
                                  if isinstance(item, dict)]
                if referenced or not sidecar_counts or any(count != 0 for count in sidecar_counts):
                    raise RuntimeError(f"declared output root is missing without a zero-sidecar decline: {group['id']}/{output}")
                absent_output_roots.append({
                    "group": group["id"], "path": (source / Path(*relative.parts)).relative_to(root).as_posix(),
                    "reason": "unreferenced-output-root-with-zero-timing-sidecars",
                })
                continue
            _inventory_tree(root, output_path, seen)
        declared_roots = [PurePosixPath(output) for output in output_roots]
        for raw_output in raw_output_refs[group["id"]]:
            raw_relative = PurePosixPath(raw_output)
            if not any(raw_relative == declared or declared in raw_relative.parents
                       for declared in declared_roots):
                raise RuntimeError(f"raw output is outside declared output_roots: {group['id']}/{raw_output}")
            raw_repo_path = (source / Path(*raw_relative.parts)).relative_to(root).as_posix()
            if raw_repo_path not in seen:
                raise RuntimeError(f"referenced raw output is not bound in evidence inventory: {group['id']}/{raw_output}")
    _validate_attempt_layout(root, report, completed, remaining)
    _validate_pending_attempts(root, report, remaining)

    evidence_files = [seen[path] for path in sorted(seen)]
    references = {
        "parent_plan": {"path": plan_rel, "sha256": plan_sha256},
        "pause_receipt": {"path": pause_rel, "sha256": pause_sha256},
        "progress": _file_reference(root, progress_path, "parent progress"),
        "campaign_start": _file_reference(root, start_path, "campaign-start receipt"),
        "completed_terminals": terminal_refs,
    }
    return {
        "schema": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "parent_campaign_id": campaign_id,
        **references,
        "completed_groups": completed,
        "remaining_ready_groups": remaining,
        "parent_report_root": report_rel,
        "parent_work_root": work_rel,
        "parent_sources_root": f"{work_rel}/sources",
        "parent_source_roots": [f"{work_rel}/sources/{group['id']}" for group in ready],
        "parent_scratch_roots": scratch_roots,
        "absent_output_roots": absent_output_roots,
        "evidence_files": evidence_files,
    }


def create_checkpoint(root: Path, parent_plan_path: Path, pause_path: Path) -> dict:
    """Create a content-bound checkpoint from the immutable paused campaign."""
    return _make_checkpoint(root, parent_plan_path, pause_path)


def _compare_continuation_plan(parent: dict, current: dict, reference: dict,
                               checkpoint: dict) -> None:
    if current.get("continuation") != reference:
        raise RuntimeError("new plan continuation reference differs from the checkpoint reference")
    if _campaign_id(current.get("campaign_id")) == checkpoint["parent_campaign_id"]:
        raise RuntimeError("continuation plan must use a new campaign ID")
    if (current.get("created_utc") is None or current.get("launch_after_utc") is None):
        raise RuntimeError("continuation plan must bind creation and launch timestamps")
    _parse_utc(current.get("created_utc"), "continuation created_utc")
    _parse_utc(current.get("launch_after_utc"), "continuation launch_after_utc")

    variable = {"campaign_id", "created_utc", "launch_after_utc", "preregistration",
                "runtime_bindings", "continuation", "source_plan", "execution_helpers", "resources",
                "groups", "group_order"}
    if set(current) != set(parent) | {"continuation"}:
        raise RuntimeError("continuation plan has unexpected or missing top-level fields")
    for key in parent:
        if key in variable:
            continue
        if current[key] != parent[key]:
            raise RuntimeError(f"continuation plan changed parent field: {key}")
    if current.get("groups") != parent.get("groups") or current.get("group_order") != parent.get("group_order"):
        raise RuntimeError("continuation plan changed commands, environments, profiles, or group statuses")

    parent_source, current_source = parent.get("source_plan"), current.get("source_plan")
    if not isinstance(parent_source, dict) or not isinstance(current_source, dict):
        raise RuntimeError("continuation source_plan bindings are malformed")
    parent_source_without_bindings = {key: value for key, value in parent_source.items()
                                     if key != "bindings_sha256"}
    current_source_without_bindings = {key: value for key, value in current_source.items()
                                      if key != "bindings_sha256"}
    if parent_source_without_bindings != current_source_without_bindings:
        raise RuntimeError("continuation plan changed source plan identity")
    _valid_sha(current_source.get("bindings_sha256"), "continuation source plan bindings sha256")

    parent_helpers, current_helpers = parent.get("execution_helpers"), current.get("execution_helpers")
    if not isinstance(parent_helpers, dict) or not isinstance(current_helpers, dict):
        raise RuntimeError("continuation execution helper map is malformed")
    if set(current_helpers) != set(parent_helpers) | {CHECKPOINT_HELPER}:
        raise RuntimeError("continuation plan changed helper inventory unexpectedly")
    for path, digest in parent_helpers.items():
        _valid_sha(current_helpers.get(path), f"continuation execution helper {path} sha256")
        if path != QUALIFIED_HELPER and current_helpers[path] != digest:
            raise RuntimeError(f"continuation plan changed execution helper: {path}")
    _valid_sha(current_helpers[CHECKPOINT_HELPER], "checkpoint helper sha256")

    parent_resources, current_resources = parent.get("resources"), current.get("resources")
    if not isinstance(parent_resources, dict) or not isinstance(current_resources, dict) \
            or set(current_resources) != set(parent_resources):
        raise RuntimeError("continuation resources fields differ")
    expected_budget = 0
    by_id = {group["id"]: group for group in current["groups"]}
    for group_id in checkpoint["remaining_ready_groups"]:
        deadline = by_id[group_id].get("deadline_seconds")
        if type(deadline) not in (int, float) or not math.isfinite(deadline) or deadline <= 0:
            raise RuntimeError(f"continuation group deadline is malformed: {group_id}")
        expected_budget += deadline
    for key, value in parent_resources.items():
        expected = expected_budget if key == "total_execution_budget_seconds" else value
        if current_resources[key] != expected:
            raise RuntimeError(f"continuation plan changed resource setting: {key}")
    if current.get("max_campaign_wall_seconds") != parent.get("max_campaign_wall_seconds"):
        raise RuntimeError("continuation plan changed max_campaign_wall_seconds")


def verify_checkpoint(root: Path, reference: dict, plan: dict | None = None) -> dict:
    """Verify a checkpoint file, its full evidence inventory, and optional child plan."""
    root = Path(root).resolve()
    raw, relative = _read_bytes(root, reference, "continuation checkpoint")
    try:
        checkpoint = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("continuation checkpoint is not valid JSON") from exc
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported continuation checkpoint schema")
    if checkpoint.get("parent_campaign_id") != _campaign_id(checkpoint.get("parent_campaign_id")):
        raise RuntimeError("checkpoint parent campaign ID is malformed")
    if checkpoint.get("parent_report_root") != f"reports/timing/v0.9.2/{checkpoint['parent_campaign_id']}" \
            or checkpoint.get("parent_work_root") != f"execution-state/timing-v092-{checkpoint['parent_campaign_id']}" \
            or checkpoint.get("parent_sources_root") != f"{checkpoint['parent_work_root']}/sources":
        raise RuntimeError("checkpoint parent report/work roots differ from its campaign ID")
    _parse_utc(checkpoint.get("created_utc"), "checkpoint created_utc")
    if not isinstance(checkpoint.get("evidence_files"), list):
        raise RuntimeError("checkpoint evidence_files must be a list")
    listed = checkpoint["evidence_files"]
    paths = []
    for item in listed:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "size_bytes"}:
            raise RuntimeError("checkpoint evidence entry is malformed")
        path = item.get("path")
        if not isinstance(path, str):
            raise RuntimeError("checkpoint evidence path is malformed")
        _valid_sha(item.get("sha256"), "checkpoint evidence sha256")
        if type(item.get("size_bytes")) is not int or item["size_bytes"] < 0:
            raise RuntimeError("checkpoint evidence size_bytes is malformed")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise RuntimeError("checkpoint evidence inventory is not uniquely sorted")

    parent_plan_ref = checkpoint.get("parent_plan")
    pause_ref = checkpoint.get("pause_receipt")
    progress_ref = checkpoint.get("progress")
    start_ref = checkpoint.get("campaign_start")
    for name, ref in (("parent_plan", parent_plan_ref), ("pause receipt", pause_ref),
                      ("progress", progress_ref), ("campaign-start", start_ref)):
        _read_bytes(root, ref, name)
    terminals = checkpoint.get("completed_terminals")
    if not isinstance(terminals, list) or len(terminals) != EXPECTED_COMPLETED:
        raise RuntimeError("checkpoint must bind 55 completed terminal receipts")
    for item in terminals:
        if not isinstance(item, dict) or set(item) != {"group", "path", "sha256"}:
            raise RuntimeError("checkpoint terminal reference is malformed")
        _read_bytes(root, {"path": item["path"], "sha256": item["sha256"]}, "completed terminal")

    plan_path = root / parent_plan_ref["path"]
    parent = _read_json(plan_path, "parent plan")
    pause_path = root / pause_ref["path"]
    fresh = _make_checkpoint(root, plan_path, pause_path)
    for key in ("parent_campaign_id", "parent_plan", "pause_receipt", "progress", "campaign_start",
                "completed_groups", "remaining_ready_groups", "parent_report_root", "parent_work_root",
                "parent_sources_root", "parent_source_roots", "parent_scratch_roots", "absent_output_roots",
                "evidence_files",
                "completed_terminals"):
        if fresh.get(key) != checkpoint.get(key):
            raise RuntimeError(f"checkpoint no longer matches parent evidence: {key}")
    if reference != {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}:
        raise RuntimeError("checkpoint reference is not canonical")
    if plan is not None:
        _compare_continuation_plan(parent, plan, reference, checkpoint)
    return checkpoint


def input_references(checkpoint: dict) -> list[dict]:
    """Return immutable parent-plan inputs for a continuation plan binding."""
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported checkpoint object")
    refs = [checkpoint.get(name) for name in ("parent_plan", "pause_receipt", "progress", "campaign_start")]
    terminals = checkpoint.get("completed_terminals")
    if not isinstance(terminals, list):
        raise RuntimeError("checkpoint completed_terminals must be a list")
    refs.extend({"path": item.get("path"), "sha256": item.get("sha256")} for item in terminals)
    result = []
    seen = set()
    for item in refs:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise RuntimeError("checkpoint input reference is malformed")
        path = item["path"]
        digest = _valid_sha(item["sha256"], "checkpoint input sha256")
        if not isinstance(path, str) or path in seen:
            raise RuntimeError("checkpoint input paths must be unique repository-relative strings")
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise RuntimeError("checkpoint input path escapes the repository")
        seen.add(path)
        result.append({"path": path, "sha256": digest})
    return result
