"""Record one explicitly reviewed v0.9.0 execution group.

Call ``run_group(root, contract_path, group_id, argv=..., env=...)`` from an orchestration
layer that has already prepared ``root`` as an isolated checkout. This module
never clones a repository and never chooses work from the prospective plan.

Contract schema (version 1) is intentionally small and explicit::

    {
      "schema_version": 1, "release": "v0.9.0",
      "execution_authorized": true,
      "parent_plan": {"path": "reports/releases/v0.9.0/plan.json", "sha256": ...},
      "population": {"path": "populations/v0.9.0.json", "sha256": ...},
      "fixture_revision": "sha256:...", "input_commits": {...},
      "input_identities": {"path": "sha256..."},
      "groups": [{"id": ..., "argv": [...], "case_ids": [...],
        "output_roots": [...], "environment": {...}, "historical_seconds": 1.0,
        "maximum_attempts": 2,
        "reports": [{"ordinal": 0, "source_path": ".../0.json",
          "path": "reports/releases/v0.9.0/normal/<planned-name>.json",
          "case_ids": [...], "tool": ..., "tool_version": ...}]}]
    }

``output_roots`` are complete trees, including raw command/native evidence. They
must be absent before the run. Captured trees retain their execution-root-relative
names and bytes; JSON inside them is never rewritten. Only ``raw_output`` in a
top-level normalized report is remapped in the staged copy. The original report
bytes are retained separately, and the receipt records the root mapping needed
to replay nested paths in raw evidence.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import subprocess
import time
from typing import Mapping, Sequence


RELEASE = "v0.9.0"
PLAN_PATH = "reports/releases/v0.9.0/plan.json"
POPULATION_PATH = "populations/v0.9.0.json"
ATTEMPTS_PATH = "reports/releases/v0.9.0/attempts"
LEDGER_PATH = "reports/releases/v0.9.0/ledger-v1.jsonl"
SERIAL_LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"


class AttemptError(RuntimeError):
    """A fail-closed contract, identity, or evidence error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_json(path: Path, description: str) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AttemptError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AttemptError(f"{description} must be a JSON object: {path}")
    return value, raw


def _relative(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AttemptError(f"{description} must be a non-empty repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise AttemptError(f"unsafe {description}: {value!r}")
    return path


def _inside(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def _safe_path(root: Path, relative: PurePosixPath, *, allow_missing: bool) -> Path:
    """Resolve under root while rejecting symlinks in every existing component."""
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if not allow_missing:
                raise AttemptError(f"required path is missing: {relative.as_posix()}")
            continue
        if current.is_symlink():
            raise AttemptError(f"symlink path is not allowed: {relative.as_posix()}")
        # Existing non-directory ancestors cannot safely contain a child.
        if part != relative.parts[-1] and not current.is_dir():
            raise AttemptError(f"non-directory path ancestor: {relative.as_posix()}")
    resolved = current.resolve(strict=not allow_missing)
    if resolved != root and root not in resolved.parents:
        raise AttemptError(f"path escapes execution root: {relative.as_posix()}")
    return current


def _ref(root: Path, relative: str, expected_sha: str, description: str) -> bytes:
    path = _safe_path(root, _relative(relative, description), allow_missing=False)
    data = path.read_bytes()
    if _sha(data) != expected_sha:
        raise AttemptError(f"{description} bytes differ from reviewed SHA-256")
    return data


def _validate(root: Path, contract_path: str | Path, group_id: str,
              requested_argv: Sequence[str] | None, env: Mapping[str, str] | None,
              *, require_authorized: bool = True, require_fresh: bool = True):
    requested_root = Path(root)
    if requested_root.is_symlink():
        raise AttemptError("execution root cannot be a symlink")
    root = requested_root.resolve(strict=True)
    if not root.is_dir():
        raise AttemptError("execution root must be a pre-created directory")
    if os.name != "posix":
        raise AttemptError("process-group timeout cleanup currently requires a POSIX host")
    contract_rel = _relative(Path(contract_path).as_posix(), "contract path")
    contract_file = _safe_path(root, contract_rel, allow_missing=False)
    contract, contract_raw = _read_json(contract_file, "execution contract")
    if contract.get("schema_version") != 1 or contract.get("release") != RELEASE:
        raise AttemptError("execution contract schema or release identity mismatch")
    if not isinstance(contract.get("execution_authorized"), bool):
        raise AttemptError("execution contract must explicitly set execution_authorized true or false")
    if require_authorized and contract["execution_authorized"] is not True:
        raise AttemptError("execution contract is validation-only; execution_authorized is not true")

    plan_ref = contract.get("parent_plan")
    population_ref = contract.get("population")
    for ref, required, description in (
        (plan_ref, PLAN_PATH, "immutable parent plan"),
        (population_ref, POPULATION_PATH, "population"),
    ):
        if not isinstance(ref, dict) or ref.get("path") != required:
            raise AttemptError(f"contract must bind {description} at {required}")
        digest = ref.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise AttemptError(f"contract has invalid {description} SHA-256")
        _ref(root, required, digest, description)

    plan, _ = _read_json(root / PLAN_PATH, "immutable parent plan")
    population, _ = _read_json(root / POPULATION_PATH, "population")
    if plan.get("release") != RELEASE or population.get("population") != RELEASE:
        raise AttemptError("parent plan or population release identity mismatch")
    fixture_revision = contract.get("fixture_revision")
    if not isinstance(fixture_revision, str) or not fixture_revision:
        raise AttemptError("contract lacks fixture_revision")
    if fixture_revision != plan.get("fixture_revision") or fixture_revision != population.get("fixture_revision"):
        raise AttemptError("contract, plan, and population fixture revisions differ")
    input_commits = contract.get("input_commits")
    if not isinstance(input_commits, dict) or input_commits != plan.get("input_commits"):
        raise AttemptError("contract input commits differ from immutable parent plan")
    if population_ref.get("sha256") != plan.get("population", {}).get("sha256"):
        raise AttemptError("contract population digest differs from immutable parent plan")
    input_identities = contract.get("input_identities")
    if not isinstance(input_identities, dict) or not input_identities:
        raise AttemptError("contract must bind non-empty input_identities")
    for input_path, expected_sha in input_identities.items():
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise AttemptError(f"invalid input identity digest: {input_path}")
        _ref(root, input_path, expected_sha, "input identity")

    groups = contract.get("groups")
    if not isinstance(groups, list):
        raise AttemptError("contract groups must be a list")
    matches = [g for g in groups if isinstance(g, dict) and g.get("id") == group_id]
    if len(matches) != 1:
        raise AttemptError(f"group must occur exactly once in contract: {group_id}")
    group = matches[0]
    plan_groups = [g for g in plan.get("execution_groups", []) if g.get("id") == group_id]
    if len(plan_groups) != 1:
        raise AttemptError(f"group is not registered exactly once in parent plan: {group_id}")
    planned_group = plan_groups[0]

    planned_argv = group.get("argv")
    if (not isinstance(planned_argv, list) or not planned_argv or
            any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in planned_argv)):
        raise AttemptError("group argv must be an explicit non-empty string array")
    if any("{" in arg or "}" in arg for arg in planned_argv):
        raise AttemptError("group argv contains an unresolved template")
    if requested_argv is not None and list(requested_argv) != planned_argv:
        raise AttemptError("requested argv differs from the reviewed group's exact argv")
    case_ids = group.get("case_ids")
    if (not isinstance(case_ids, list) or not case_ids or
            any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or
            len(case_ids) != len(set(case_ids)) or case_ids != planned_group.get("case_ids")):
        raise AttemptError("group member IDs differ from exact parent-plan membership")

    planned_report_paths = planned_group.get("reports")
    reports = group.get("reports")
    if not isinstance(reports, list) or not reports or not isinstance(planned_report_paths, list):
        raise AttemptError("group must explicitly bind its normalized report partitions")
    plan_reports = {r.get("report"): r for r in plan.get("reports", []) if isinstance(r, dict)}
    if [r.get("path") for r in reports if isinstance(r, dict)] != planned_report_paths:
        raise AttemptError("contract report destinations differ from exact parent-plan group")
    ordinals = []
    source_paths = []
    destination_paths = []
    for report in reports:
        if not isinstance(report, dict):
            raise AttemptError("report declaration must be an object")
        registered = plan_reports.get(report.get("path"))
        if registered is None or registered.get("execution_group") != group_id:
            raise AttemptError("report partition is not assigned to this parent-plan group")
        if report.get("case_ids") != registered.get("case_ids"):
            raise AttemptError(f"report member IDs differ from parent plan: {report.get('path')}")
        if not isinstance(report.get("tool_version"), str) or not report["tool_version"]:
            raise AttemptError("each report must bind an exact expected tool_version")
        if report.get("tool") != registered.get("tool"):
            raise AttemptError("report tool differs from parent plan")
        destination = _relative(report.get("path"), "normalized report path")
        normal_root = PurePosixPath("reports/releases/v0.9.0/normal")
        if not _inside(destination, normal_root) or destination == normal_root:
            raise AttemptError("normalized report destination must be under the versioned normal release root")
        destination_paths.append(destination)
        _relative(report.get("source_path"), "normalized report source path")
        if type(report.get("ordinal")) is not int or report["ordinal"] < 0:
            raise AttemptError("each report requires an explicit non-negative output ordinal")
        ordinals.append(report["ordinal"])
        source_paths.append(report["source_path"])
        if report.get("fixture_revision", fixture_revision) != fixture_revision:
            raise AttemptError("report fixture_revision differs from the reviewed group")
    if (len(ordinals) != len(set(ordinals)) or len(source_paths) != len(set(source_paths)) or
            len(destination_paths) != len(set(destination_paths))):
        raise AttemptError("duplicate ordinal, normalized report source, or destination mapping")
    if sorted(ordinals) != list(range(len(reports))):
        raise AttemptError("report ordinals must map every output ordinal exactly once")
    mapped_case_ids = [case_id for report in reports for case_id in report["case_ids"]]
    if len(mapped_case_ids) != len(set(mapped_case_ids)) or sorted(mapped_case_ids) != sorted(case_ids):
        raise AttemptError("report mapping does not exactly partition group member IDs")

    maximum = group.get("maximum_attempts")
    if type(maximum) is not int or maximum < 1 or maximum > 2:
        raise AttemptError("maximum_attempts must be 1 or 2")
    historical_seconds = group.get("historical_seconds")
    if (isinstance(historical_seconds, bool) or
            not isinstance(historical_seconds, (int, float)) or
            not math.isfinite(historical_seconds) or historical_seconds < 0):
        raise AttemptError("group must bind non-negative finite historical_seconds")
    expected_env = group.get("environment")
    if (not isinstance(expected_env, dict) or
            any(not isinstance(k, str) or not isinstance(v, str) for k, v in expected_env.items())):
        raise AttemptError("group must bind an explicit string-to-string environment map")
    supplied_env = dict(expected_env if env is None else env)
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in supplied_env.items()):
        raise AttemptError("supplied child environment must contain only strings")
    if supplied_env != expected_env:
        raise AttemptError("supplied child environment differs from reviewed contract")

    output_roots_value = group.get("output_roots")
    if not isinstance(output_roots_value, list) or not output_roots_value:
        raise AttemptError("group must declare complete output_roots")
    output_roots = [_relative(path, "output root") for path in output_roots_value]
    reserved_paths = [
        PurePosixPath(ATTEMPTS_PATH),
        PurePosixPath(LEDGER_PATH),
        PurePosixPath("reports/releases/v0.9.0/normal/attempts"),
        PurePosixPath(PLAN_PATH),
        PurePosixPath(POPULATION_PATH),
        contract_rel,
    ]
    for output_root in output_roots:
        if any(_inside(output_root, reserved) or _inside(reserved, output_root)
               for reserved in reserved_paths):
            raise AttemptError(f"output root overlaps recorder-owned evidence: {output_root}")
    if len(set(output_roots)) != len(output_roots):
        raise AttemptError("duplicate declared output root")
    for i, left in enumerate(output_roots):
        if any(_inside(left, right) or _inside(right, left) for right in output_roots[i + 1:]):
            raise AttemptError("output roots must be disjoint; declare complete raw trees")
        target = _safe_path(root, left, allow_missing=True)
        if require_fresh and (target.exists() or target.is_symlink()):
            raise AttemptError(f"declared output root is not fresh: {left.as_posix()}")
    for report in reports:
        source_rel = _relative(report["source_path"], "normalized report source path")
        if not any(_inside(source_rel, output_root) for output_root in output_roots):
            raise AttemptError(f"normalized report source is outside declared output roots: {source_rel}")
    return root, contract, contract_raw, plan, population, group, output_roots


def validate_group(root, contract_path, group_id, *, require_authorized=False, require_fresh=True):
    """Validate an explicit group without launching commands or allocating attempts."""
    contract = json.loads((Path(root) / contract_path).read_text())
    matches = [g for g in contract['groups'] if g['id'] == group_id]
    if len(matches) != 1:
        raise AttemptError('group must occur exactly once')
    group = matches[0]
    _validate(Path(root), contract_path, group_id, group['argv'], group['environment'],
              require_authorized=require_authorized, require_fresh=require_fresh)
    return {'group_id': group_id, 'reports': len(group['reports']), 'execution_authorized': contract.get('execution_authorized') is True}


def _timestamp() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _attempt_dir(root: Path, group_id: str, maximum: int) -> tuple[Path, str]:
    base_rel = PurePosixPath(ATTEMPTS_PATH)
    base = _safe_path(root, base_rel, allow_missing=True)
    base.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in group_id)
    for number in range(1, maximum + 1):
        attempt_id = f"{safe_id}-attempt-{number:02d}"
        path = base / attempt_id
        try:
            path.mkdir(exist_ok=False)
            return path, attempt_id
        except FileExistsError:
            continue
    raise AttemptError(f"maximum attempts ({maximum}) already recorded for {group_id}")


def _copy_tree(root: Path, relative: PurePosixPath, destination: Path) -> list[dict]:
    source = _safe_path(root, relative, allow_missing=False)
    if source.is_symlink():
        raise AttemptError(f"declared output root became a symlink: {relative}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []
    if source.is_file():
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        copied.append({"path": relative.as_posix(), "sha256": _sha(destination.read_bytes()), "bytes": destination.stat().st_size})
        return copied
    if not source.is_dir():
        raise AttemptError(f"declared output root is neither file nor directory: {relative}")
    destination.mkdir(parents=True, exist_ok=False)
    for current, dirs, files in os.walk(source, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            item = current_path / name
            if item.is_symlink():
                raise AttemptError(f"symlink inside declared output tree: {item}")
        for name in files:
            item = current_path / name
            if item.is_symlink() or not item.is_file():
                raise AttemptError(f"non-regular file inside declared output tree: {item}")
            sub = item.relative_to(source)
            target = destination / sub
            target.parent.mkdir(parents=True, exist_ok=True)
            with item.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst)
            rel = (relative / PurePosixPath(sub.as_posix())).as_posix()
            copied.append({"path": rel, "sha256": _sha(target.read_bytes()), "bytes": target.stat().st_size})
    return sorted(copied, key=lambda row: row["path"])


def _terminate_process_group(process: subprocess.Popen, grace_seconds: float = 2.0) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    # The group leader can exit on TERM while a child ignores it. Kill the
    # group after the grace period even when wait() has already reaped leader.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def _run(argv: Sequence[str], root: Path, env: Mapping[str, str], out: Path, err: Path, timeout: float | None):
    start = time.monotonic()
    timed_out = False
    with out.open("wb") as stdout, err.open("wb") as stderr:
        process = subprocess.Popen(
            list(argv), cwd=root, env=dict(env), stdout=stdout, stderr=stderr,
            start_new_session=True, close_fds=True,
        )
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process)
        except BaseException:
            _terminate_process_group(process)
            raise
    return (124 if timed_out else process.returncode), timed_out, time.monotonic() - start


def _report_bytes(root: Path, attempt: Path, report: dict, roots: list[PurePosixPath],
                  attempt_id: str, fixture_revision: str,
                  capture_manifest: Mapping[str, str]):
    report_rel = _relative(report["path"], "report path")
    source_rel = _relative(report["source_path"], "report source path")
    source = attempt / "capture" / Path(*source_rel.parts)
    if not source.is_file() or source.is_symlink():
        raise AttemptError(f"normalized source was not captured: {source_rel}")
    original = source.read_bytes()
    try:
        normalized = json.loads(original)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AttemptError(f"normalized report is not valid JSON: {report['path']}: {exc}") from exc
    if not isinstance(normalized, dict):
        raise AttemptError(f"normalized report must be a JSON object: {report['path']}")
    if normalized.get("fixture_revision") != fixture_revision:
        raise AttemptError(f"normalized report fixture_revision mismatch: {report['path']}")
    if normalized.get("tool_version") != report["tool_version"]:
        raise AttemptError(f"normalized report tool_version mismatch: {report['path']}")
    if normalized.get("tool") != report["tool"]:
        raise AttemptError(f"normalized report tool mismatch: {report['path']}")
    results = normalized.get("results")
    expected_ids = report["case_ids"]
    actual_ids = [r.get("case_id") for r in results if isinstance(r, dict)] if isinstance(results, list) else None
    if (actual_ids is None or len(actual_ids) != len(results) or
            len(actual_ids) != len(set(actual_ids)) or sorted(actual_ids) != sorted(expected_ids)):
        raise AttemptError(f"normalized report member IDs differ from reviewed partition: {report['path']}")
    for row in results:
        raw_value = row.get("raw_output")
        raw_rel = _relative(raw_value, "normalized raw_output")
        if not any(_inside(raw_rel, out_root) for out_root in roots):
            raise AttemptError(f"raw_output is outside declared complete output roots: {raw_value}")
        captured = attempt / "capture" / Path(*raw_rel.parts)
        if not captured.is_file() or captured.is_symlink():
            raise AttemptError(f"raw_output was not retained in the attempt capture: {raw_value}")
        captured_sha = _sha(captured.read_bytes())
        if capture_manifest.get(raw_rel.as_posix()) != captured_sha:
            raise AttemptError(f"raw_output differs from immutable capture manifest: {raw_value}")
        raw_sha = row.get("raw_sha256")
        if raw_sha is not None and (not isinstance(raw_sha, str) or raw_sha != captured_sha):
            raise AttemptError(f"raw_output digest mismatch: {raw_value}")
        row["raw_output"] = (PurePosixPath(ATTEMPTS_PATH) / attempt_id / "capture" / raw_rel).as_posix()

    original_rel = PurePosixPath("original-normalized") / report_rel
    original_path = attempt / Path(*original_rel.parts)
    original_path.parent.mkdir(parents=True, exist_ok=True)
    with original_path.open("xb") as target:
        target.write(original)
    normal_root = PurePosixPath("reports/releases/v0.9.0/normal")
    staged_rel = PurePosixPath("reports/releases/v0.9.0/normal/attempts") / attempt_id / report_rel.relative_to(normal_root)
    staged = root / Path(*staged_rel.parts)
    _safe_path(root, staged_rel, allow_missing=True)
    staged.parent.mkdir(parents=True, exist_ok=True)
    with staged.open("xb") as target:
        target.write(_json_bytes(normalized))
    return {
        "source_path": report_rel.as_posix(),
        "execution_output_path": source_rel.as_posix(),
        "ordinal": report["ordinal"],
        "original_normalized": original_rel.as_posix(),
        "original_normalized_sha256": _sha(original),
        "staged_path": staged_rel.as_posix(),
        "staged_sha256": _sha(staged.read_bytes()),
        "case_ids": actual_ids,
    }


def _verify_immutable_inputs(root: Path, contract_path: str | Path,
                             contract_raw: bytes, contract: dict) -> None:
    contract_rel = _relative(Path(contract_path).as_posix(), "contract path")
    current_contract = _safe_path(root, contract_rel, allow_missing=False).read_bytes()
    if current_contract != contract_raw:
        raise AttemptError("execution contract changed during the run")
    for reference, description in (
        (contract["parent_plan"], "immutable parent plan"),
        (contract["population"], "population"),
    ):
        _ref(root, reference["path"], reference["sha256"], description)
    for input_path, expected_sha in contract["input_identities"].items():
        _ref(root, input_path, expected_sha, "input identity")


def run_group(
    root: str | Path,
    contract_path: str | Path,
    group_id: str,
    *,
    argv: Sequence[str],
    env: Mapping[str, str],
    timeout_seconds: float | None = None,
) -> dict:
    """Execute exactly one reviewed group and return its immutable receipt row.

    ``env`` is the complete child environment; it must equal the explicit map in
    the reviewed group contract. No process-global environment is read or
    inherited. A timeout kills and reaps the complete POSIX process group.
    Failed commands and post-start recorder failures retain an attempt and ledger
    entry. Validation errors happen before an attempt is allocated.
    """
    if timeout_seconds is not None and (not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0):
        raise AttemptError("timeout_seconds must be positive when provided")
    root, contract, contract_raw, plan, population, group, output_roots = _validate(
        Path(root), contract_path, group_id, argv, env
    )
    deadline_seconds = max(600, math.ceil(2 * group["historical_seconds"] + 300))
    if timeout_seconds is not None and timeout_seconds != deadline_seconds:
        raise AttemptError(
            f"timeout_seconds must equal the reviewed group deadline ({deadline_seconds})"
        )
    attempt, attempt_id = _attempt_dir(root, group_id, group["maximum_attempts"])
    start = _timestamp()
    contract_relative = _relative(Path(contract_path).as_posix(), "contract path")
    plan_raw = (root / PLAN_PATH).read_bytes()
    population_raw = (root / POPULATION_PATH).read_bytes()
    receipt = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "group_id": group_id,
        "release": RELEASE,
        "status": "started",
        "start_utc": start,
        "execution_root": str(root),
        "execution_revision": _git_revision(root),
        "contract": {"path": contract_relative.as_posix(), "sha256": _sha(contract_raw)},
        "parent_plan": {"path": PLAN_PATH, "sha256": _sha(plan_raw)},
        "population": {"path": POPULATION_PATH, "sha256": _sha(population_raw)},
        "fixture_revision": contract["fixture_revision"],
        "input_commits": contract["input_commits"],
        "input_identities": contract["input_identities"],
        "historical_seconds": group["historical_seconds"],
        "deadline_seconds": deadline_seconds,
        "argv": list(argv),
        "environment": dict(env),
        "environment_sha256": _sha(_json_bytes(dict(env))),
        "case_ids": group["case_ids"],
        "expected_reports": [r["path"] for r in group["reports"]],
        "output_roots": [r.as_posix() for r in output_roots],
        "execution_root_mapping": {
            "execution_root": str(root),
            "captured_root": (PurePosixPath(ATTEMPTS_PATH) / attempt_id / "capture").as_posix(),
            "mapping": [{"execution_root_relative": r.as_posix(), "captured_relative": (PurePosixPath(ATTEMPTS_PATH) / attempt_id / "capture" / r).as_posix()} for r in output_roots],
            "raw_json_bytes_rewritten": False,
            "nested_raw_references_resolve_from_execution_root_namespace": True,
        },
        "started_receipt": "started.json",
    }
    with (attempt / "started.json").open("xb") as started_file:
        started_file.write(_json_bytes(receipt))
    row = dict(receipt)
    try:
        row["exit_code"], row["timed_out"], row["duration_seconds"] = _run(
            argv, root, env, attempt / "stdout.txt", attempt / "stderr.txt", deadline_seconds
        )
        _verify_immutable_inputs(root, contract_path, contract_raw, contract)
        row["stdout"] = {"path": "stdout.txt", "sha256": _sha((attempt / "stdout.txt").read_bytes())}
        row["stderr"] = {"path": "stderr.txt", "sha256": _sha((attempt / "stderr.txt").read_bytes())}
        capture_rows = []
        capture_errors = []
        for output_root in output_roots:
            try:
                capture_rows.extend(_copy_tree(root, output_root, attempt / "capture" / Path(*output_root.parts)))
            except Exception as exc:
                capture_errors.append(f"{output_root}: {type(exc).__name__}: {exc}")
        row["captured_files"] = sorted(capture_rows, key=lambda item: item["path"])
        if capture_errors:
            row["capture_errors"] = capture_errors
            raise AttemptError("one or more declared output roots could not be captured")
        if row["exit_code"] == 0 and not row["timed_out"]:
            capture_manifest = {item["path"]: item["sha256"] for item in capture_rows}
            row["reports"] = [
                _report_bytes(root, attempt, report, output_roots, attempt_id,
                              contract["fixture_revision"], capture_manifest)
                for report in group["reports"]
            ]
        else:
            row["reports"] = []
        row["status"] = "timed-out" if row["timed_out"] else ("completed" if row["exit_code"] == 0 else "failed")
    except BaseException as exc:
        row["status"] = "recorder-error"
        row["recorder_error"] = f"{type(exc).__name__}: {exc}"
        # Best-effort capture is deliberately additive and never removes failed output.
        for output_root in output_roots:
            source = root.joinpath(*output_root.parts)
            target = attempt / "capture" / Path(*output_root.parts)
            if source.exists() and not target.exists():
                try:
                    _copy_tree(root, output_root, target)
                except Exception as capture_exc:
                    row.setdefault("capture_errors", []).append(f"{output_root}: {capture_exc}")
    finally:
        row["end_utc"] = _timestamp()
        with (attempt / "completed.json").open("xb") as completed_file:
            completed_file.write(_json_bytes(row))
        _append_ledger(root / LEDGER_PATH, row)
    return row


def _git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, env={"PATH": os.defpath},
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, text=True,
        )
        value = result.stdout.strip()
        return value if len(value) == 40 and all(c in "0123456789abcdefABCDEF" for c in value) else None
    except (OSError, subprocess.CalledProcessError):
        return None


def _append_ledger(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
    # flock serializes concurrent group recorders on the supported POSIX host.
    import fcntl
    with path.open("a", encoding="utf-8") as ledger:
        fcntl.flock(ledger.fileno(), fcntl.LOCK_EX)
        ledger.write(encoded)
        ledger.flush()
        os.fsync(ledger.fileno())
        fcntl.flock(ledger.fileno(), fcntl.LOCK_UN)
