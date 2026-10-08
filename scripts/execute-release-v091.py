#!/usr/bin/env python3
"""Execute the reviewed, serial Bifrost-only v0.9.1 release matrix.

The plan is deliberately the only source of group selection.  Execution uses a
fresh source-only snapshot for every group, retains the original native output,
and stages a normalized copy whose only changed field is ``raw_output``.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _datetime
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from typing import Iterator, Mapping, Sequence


RELEASE = "v0.9.1"
SOURCE_POPULATION = "v0.9.0"
BIFROST_SEMVER = "0.13.0"
BIFROST_BANNER = "bifrost 0.13.0"
BIFROST_BUILD_IDENTITY = "9426a205c6ced4d438182068995d6279f0d885fe"
BIFROST_BINARY_SHA256 = "640d0b8e4fe5fb34159c184f994e245021825b05e6144a09f2b4be9a76b129c9"
BIFROST_ARCHIVE_SHA256 = "8fb7212912cda0d6fc97e72188339b53aec4ea1ce31cc6a076765763e2273604"
MIN_FREE_BYTES = 64 * 1024**3
LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"
EXECUTION_ROOT = PurePosixPath("execution-state/v091/groups")
CACHE_ROOT = PurePosixPath("execution-state/v091/cache")
ATTEMPTS_ROOT = PurePosixPath("reports/releases/v0.9.1/attempts")
LEDGER_PATH = PurePosixPath("reports/releases/v0.9.1/ledger-v1.jsonl")
NORMAL_ROOT = PurePosixPath("reports/releases/v0.9.1/normal")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
FIXTURE = re.compile(r"sha256:[0-9a-f]{64}\Z")
SNAPSHOT_DIRECTORIES = (
    "src",
    "cases",
    "populations",
    "adapters",
    "scripts",
    "schemas",
)
SNAPSHOT_FILES = (
    "Cargo.toml",
    "Cargo.lock",
    "reports/releases/v0.9.1/acquisition/builtin-policy-catalog.json",
    "reports/releases/v0.9.1/acquisition/help.txt",
    "docs/releases/v0.9.1-native.md",
)
SNAPSHOT_PATHS = SNAPSHOT_DIRECTORIES + SNAPSHOT_FILES
HEAVY_PROCESS_NAMES = {
    "cargo",
    "rustc",
    "clippy-driver",
    "java",
    "codeql",
    "joern",
    "hyperfine",
}


class ReleaseError(RuntimeError):
    """A fail-closed plan, resource, provenance, or evidence error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _timestamp() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _read_json(path: Path, description: str) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"{description} must be a JSON object: {path}")
    return value, raw


def _relative(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReleaseError(f"{description} must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ReleaseError(f"unsafe {description}: {value!r}")
    return path


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _path_inside(path: Path, root: Path, description: str) -> Path:
    if not path.is_absolute():
        raise ReleaseError(f"{description} must be absolute: {path}")
    resolved = path.resolve(strict=False)
    if not _under(resolved, root):
        raise ReleaseError(f"{description} escapes execution root: {path}")
    current = root.resolve(strict=False)
    for part in resolved.relative_to(root.resolve(strict=False)).parts:
        current /= part
        if current.is_symlink():
            raise ReleaseError(f"symlink in {description}: {path}")
    return resolved


def _repo_root(start: Path) -> Path:
    try:
        raw = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=start, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("the executor must run inside a Git worktree") from exc
    return Path(raw).resolve()


def _git_head(root: Path) -> str:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("cannot read the execution worktree HEAD") from exc
    if not COMMIT.fullmatch(value):
        raise ReleaseError("worktree HEAD is not an exact commit")
    return value


def _git_show(root: Path, commit: str, relative: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{relative}"], cwd=root,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError(f"source commit lacks {relative}") from exc


def _assert_source_snapshot(root: Path, source_commit: str) -> None:
    """Require SOURCE to be an ancestor and all runner inputs to match it."""
    if not COMMIT.fullmatch(source_commit):
        raise ReleaseError("source_commit is not an exact commit")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
            cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("source drift: source_commit is not an ancestor of HEAD") from exc
    paths = [
        "src", "cases", "populations", "adapters", "schemas", "scripts",
        "Cargo.toml", "Cargo.lock",
        "reports/releases/v0.9.1/acquisition/builtin-policy-catalog.json",
        "reports/releases/v0.9.1/acquisition/help.txt",
        "docs/releases/v0.9.1-native.md",
    ]
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", source_commit, "--", *paths],
            cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("cannot verify source drift") from exc
    if result.returncode != 0:
        raise ReleaseError("source drift: runner or fixture inputs differ from source_commit")
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *paths],
            cwd=root, text=True, stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("cannot verify untracked source drift") from exc
    if status.strip():
        raise ReleaseError("source drift in untracked inputs:\n" + status.strip())


def _bound_sha(value: object, description: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ReleaseError(f"{description} must bind a lowercase SHA-256")
    return value


def _tool_binding(tools: object, name: str, expected_version: str | None = None) -> dict:
    if not isinstance(tools, dict) or not isinstance(tools.get(name), dict):
        raise ReleaseError(f"plan must bind tools.{name}")
    binding = tools[name]
    path = binding.get("path")
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ReleaseError(f"tools.{name}.path must be absolute")
    digest = _bound_sha(binding.get("sha256"), f"tools.{name}.sha256")
    if expected_version is not None and binding.get("version") != expected_version:
        raise ReleaseError(f"tools.{name}.version must be {expected_version}")
    result = dict(binding)
    result.update({"path": path, "sha256": digest})
    if expected_version:
        result["version"] = expected_version
    if "build_identity" in result and (not isinstance(result["build_identity"], str)
                                        or not COMMIT.fullmatch(result["build_identity"])):
        raise ReleaseError(f"tools.{name}.build_identity must be an exact commit identity")
    if "archive_sha256" in result:
        _bound_sha(result["archive_sha256"], f"tools.{name}.archive_sha256")
    if "binary_sha256" in result and result["binary_sha256"] != digest:
        raise ReleaseError(f"tools.{name}.binary_sha256 must equal tools.{name}.sha256")
    return result


def _check_tool_file(binding: Mapping[str, str], description: str) -> None:
    path = Path(binding["path"])
    if not path.is_file() or path.is_symlink():
        raise ReleaseError(f"{description} is missing or not a regular file: {path}")
    if _sha(path.read_bytes()) != binding["sha256"]:
        raise ReleaseError(f"{description} SHA-256 differs from the plan: {path}")


def _population(plan: dict, plan_path: Path) -> tuple[dict, bytes, str]:
    binding = plan.get("population")
    if not isinstance(binding, dict):
        raise ReleaseError("plan must bind a population object")
    path = _relative(binding.get("path"), "population path")
    digest = _bound_sha(binding.get("sha256"), "population.sha256")
    population_path = plan_path.parent.parent.parent.parent / Path(*path.parts)
    population, raw = _read_json(population_path, "population")
    if _sha(raw) != digest:
        raise ReleaseError("population bytes differ from the plan SHA-256")
    if population.get("population") != SOURCE_POPULATION:
        raise ReleaseError("plan must bind the v0.9.0 population")
    fixture = plan.get("fixture_revision")
    if not isinstance(fixture, str) or not FIXTURE.fullmatch(fixture):
        raise ReleaseError("plan must bind a common fixture_revision")
    if binding.get("fixture_revision") != fixture or population.get("fixture_revision") != fixture:
        raise ReleaseError("plan and population fixture revisions differ")
    cases = population.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ReleaseError("population cases must be a non-empty list")
    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(cases) or any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise ReleaseError("population cases require string ids")
    if len(ids) != len(set(ids)):
        raise ReleaseError("population contains duplicate case ids")
    return population, raw, fixture


def _qualification_gate(plan: dict, repo_root: Path) -> dict:
    binding = plan.get("qualification")
    if not isinstance(binding, dict):
        raise ReleaseError("plan must bind qualification")
    relative = _relative(binding.get("path"), "qualification summary path")
    expected_path = PurePosixPath("reports/releases/v0.9.1/qualification/review-01.json")
    if relative != expected_path:
        raise ReleaseError(f"qualification path must be {expected_path.as_posix()}")
    digest = _bound_sha(binding.get("sha256"), "qualification.sha256")
    path = repo_root / Path(*relative.parts)
    summary, raw = _read_json(path, "qualification summary")
    if _sha(raw) != digest:
        raise ReleaseError("qualification summary bytes differ from the plan SHA-256")
    tool = summary.get("tool")
    expected_tool = plan.get("tools", {}).get("bifrost", {})
    if (summary.get("schema") != "bifrost-v013-control-review/v1" or
            summary.get("measurement_contract") != "verified-with-known-limits" or
            summary.get("full_policy_qualification") is not False or not isinstance(tool, dict) or
            tool.get("version") != BIFROST_SEMVER or
            tool.get("build_identity") != expected_tool.get("build_identity") or
            tool.get("sha256") != expected_tool.get("sha256")):
        raise ReleaseError("qualification summary does not authorize the release matrix")
    # Recheck every captured byte and the exact frozen limited states, rather
    # than trusting a favorable summary flag or treating incomplete as clean.
    spec = importlib.util.spec_from_file_location(
        "v013_control_review", repo_root / "scripts/review-bifrost-v013-controls.py"
    )
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    try:
        observed = review.audit(repo_root)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        raise ReleaseError(f"retained control evidence failed review: {exc}") from exc
    if observed != summary:
        raise ReleaseError("control review differs from recomputed retained evidence")
    return {"path": relative.as_posix(), "sha256": digest}


def _wall_budget(plan: dict) -> float:
    value = plan.get("total_wall_budget_seconds")
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value <= 0):
        raise ReleaseError("plan must bind a positive total_wall_budget_seconds")
    return float(value)


def _historical_bifrost_groups(repo_root: Path) -> dict[str, tuple[str, ...]]:
    path = repo_root / "reports/releases/v0.9.0/plan.json"
    if not path.is_file():
        raise ReleaseError("historical v0.9.0 Bifrost group plan is unavailable")
    old, _ = _read_json(path, "historical v0.9.0 plan")
    groups = old.get("execution_groups")
    if not isinstance(groups, list):
        raise ReleaseError("historical v0.9.0 execution_groups is malformed")
    bifrost = [g for g in groups if isinstance(g, dict) and g.get("tool") == "bifrost"]
    if len(bifrost) != 20:
        raise ReleaseError("historical v0.9.0 plan must contain exactly 20 Bifrost groups")
    result = {}
    for group in bifrost:
        group_id = group.get("id")
        case_ids = group.get("case_ids")
        if (not isinstance(group_id, str) or not SAFE_ID.fullmatch(group_id) or
                not isinstance(case_ids, list) or not case_ids or
                any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or
                len(case_ids) != len(set(case_ids))):
            raise ReleaseError("historical v0.9.0 Bifrost group membership is malformed")
        if group_id in result:
            raise ReleaseError("historical v0.9.0 Bifrost group ids are not unique")
        result[group_id] = tuple(case_ids)
    if len(result) != 20:
        raise ReleaseError("historical v0.9.0 Bifrost group ids are not unique")
    return result


def _validate_group_shape(
    group: object,
    population_ids: set[str],
    repo_root: Path,
    runner: Mapping[str, str],
    bifrost: Mapping[str, str],
) -> tuple[dict, Path, list[dict]]:
    if not isinstance(group, dict):
        raise ReleaseError("each execution group must be an object")
    group_id = group.get("id")
    if not isinstance(group_id, str) or not SAFE_ID.fullmatch(group_id):
        raise ReleaseError("group id is not path-safe")
    execution_root = (repo_root / Path(*EXECUTION_ROOT.parts) / group_id).resolve()
    argv = group.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg for arg in argv):
        raise ReleaseError(f"{group_id}: argv must be a non-empty string list")
    if argv[0] != runner["path"] or bifrost["path"] not in argv:
        raise ReleaseError(f"{group_id}: argv must bind the reviewed runner and Bifrost paths")
    case_ids = group.get("case_ids")
    if (not isinstance(case_ids, list) or not case_ids or
            any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or
            len(case_ids) != len(set(case_ids)) or not set(case_ids) <= population_ids):
        raise ReleaseError(f"{group_id}: case membership is not an exact population subset")
    deadline = group.get("deadline_seconds")
    if (isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or
            not math.isfinite(deadline) or deadline <= 0):
        raise ReleaseError(f"{group_id}: deadline_seconds must be positive and finite")
    output_roots = group.get("output_roots")
    if not isinstance(output_roots, list) or not output_roots:
        raise ReleaseError(f"{group_id}: output_roots must be non-empty")
    roots = []
    for value in output_roots:
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ReleaseError(f"{group_id}: output roots must be absolute")
        roots.append(_path_inside(Path(value), execution_root, "output root"))
    if len(set(roots)) != len(roots) or any(root == execution_root for root in roots):
        raise ReleaseError(f"{group_id}: output roots must be distinct and narrower than the execution root")
    for index, left in enumerate(roots):
        if any(_under(left, right) or _under(right, left) for right in roots[index + 1:]):
            raise ReleaseError(f"{group_id}: output roots overlap")

    reports = group.get("reports")
    if not isinstance(reports, list) or not reports:
        raise ReleaseError(f"{group_id}: reports must be non-empty")
    seen_cases: list[str] = []
    normalized_reports = []
    for report in reports:
        if not isinstance(report, dict):
            raise ReleaseError(f"{group_id}: report binding must be an object")
        destination = _relative(report.get("path"), "normalized report path")
        if destination.parts[:4] != NORMAL_ROOT.parts or destination == NORMAL_ROOT:
            raise ReleaseError(f"{group_id}: report must stage below {NORMAL_ROOT.as_posix()}")
        source = report.get("source_path")
        if not isinstance(source, str) or not Path(source).is_absolute():
            raise ReleaseError(f"{group_id}: report source_path must be absolute")
        source_path = _path_inside(Path(source), execution_root, "report source path")
        if not any(_under(source_path, root) for root in roots):
            raise ReleaseError(f"{group_id}: report source is outside output roots")
        report_cases = report.get("case_ids")
        if (not isinstance(report_cases, list) or any(not isinstance(case_id, str) for case_id in report_cases) or
                len(report_cases) != len(set(report_cases))):
            raise ReleaseError(f"{group_id}: report case_ids are invalid")
        if report.get("tool") != "bifrost" or report.get("tool_version") != BIFROST_BANNER:
            raise ReleaseError(f"{group_id}: report must expect {BIFROST_BANNER}")
        seen_cases.extend(report_cases)
        normalized_reports.append({
            **report,
            "path": destination.as_posix(),
            "source_path": str(source_path),
            "case_ids": report_cases,
        })
    if sorted(seen_cases) != sorted(case_ids) or len(seen_cases) != len(set(seen_cases)):
        raise ReleaseError(f"{group_id}: report partitions do not exactly match group case_ids")
    return group, execution_root, normalized_reports


def validate_plan(plan_path: str | Path, *, repo_root: str | Path | None = None) -> dict:
    """Validate plan structure, population identity, tools, and exact group membership."""
    path = Path(plan_path).expanduser().resolve()
    if path.name != "plan.json" or path.parts[-4:-1] != ("reports", "releases", "v0.9.1"):
        raise ReleaseError("plan must be reports/releases/v0.9.1/plan.json")
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else _repo_root(path.parent)
    if not _under(path, root):
        raise ReleaseError("plan must be inside the execution repository")
    plan, plan_raw = _read_json(path, "release plan")
    if plan.get("schema_version") != 1 or plan.get("release") != RELEASE:
        raise ReleaseError("plan schema or release identity mismatch")
    if not isinstance(plan.get("execution_authorized"), bool):
        raise ReleaseError("plan must explicitly bind execution_authorized")
    source_commit = plan.get("source_commit")
    if not isinstance(source_commit, str) or not COMMIT.fullmatch(source_commit):
        raise ReleaseError("plan must bind an exact source_commit")
    population, population_raw, fixture = _population(plan, path)
    runner = _tool_binding(plan.get("tools"), "runner")
    bifrost = _tool_binding(plan.get("tools"), "bifrost", BIFROST_SEMVER)
    if (bifrost.get("build_identity") != BIFROST_BUILD_IDENTITY or
            bifrost.get("binary_sha256") != BIFROST_BINARY_SHA256 or
            bifrost.get("archive_sha256") != BIFROST_ARCHIVE_SHA256):
        raise ReleaseError("Bifrost binding does not match the reviewed v0.13.0 build")
    _check_tool_file(runner, "runner")
    _check_tool_file(bifrost, "Bifrost")
    groups = plan.get("groups")
    if not isinstance(groups, list) or len(groups) != 20:
        raise ReleaseError("plan must contain exactly the 20 Bifrost groups")
    population_ids = {case["id"] for case in population["cases"]}
    seen_groups: dict[str, tuple[str, ...]] = {}
    validated = []
    for group in groups:
        checked, execution_root, reports = _validate_group_shape(group, population_ids, root, runner, bifrost)
        group_id = checked["id"]
        if group_id in seen_groups:
            raise ReleaseError(f"duplicate group id: {group_id}")
        seen_groups[group_id] = tuple(checked["case_ids"])
        validated.append({"id": group_id, "execution_root": execution_root, "reports": reports})
    all_cases = [case_id for group in groups for case_id in group["case_ids"]]
    if len(all_cases) != 1116:
        raise ReleaseError("Bifrost group membership must contain exactly 1,116 rows")
    historical = _historical_bifrost_groups(root)
    if historical is None:
        raise ReleaseError("historical v0.9.0 Bifrost group plan is unavailable")
    if set(seen_groups) != set(historical):
        raise ReleaseError("v0.9.1 groups must copy the historical 20 Bifrost group ids")
    for group_id, expected in historical.items():
        if seen_groups[group_id] != expected:
            raise ReleaseError(f"{group_id}: case membership differs from v0.9.0")
    total_wall_budget = _wall_budget(plan)
    return {
        "path": str(path),
        "bytes_sha256": _sha(plan_raw),
        "repo_root": root,
        "plan": plan,
        "plan_raw": plan_raw,
        "population_raw": population_raw,
        "fixture_revision": fixture,
        "runner": runner,
        "bifrost": bifrost,
        "execution_authorized": plan.get("execution_authorized") is True,
        "total_wall_budget_seconds": total_wall_budget,
        "groups": validated,
    }


def _source_file(root: Path, commit: str, relative: str, expected: str) -> bytes:
    data = _git_show(root, commit, relative)
    if _sha(data) != expected:
        raise ReleaseError(f"{relative} at source_commit differs from the plan")
    return data


def _safe_member(name: str) -> PurePosixPath | None:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ReleaseError(f"unsafe member in source archive: {name}")
    value = path.as_posix()
    if path.parts and path.parts[0] in SNAPSHOT_DIRECTORIES:
        return path
    if value in SNAPSHOT_FILES:
        return path
    return None


def _materialize_source(repo_root: Path, source_commit: str, destination: Path) -> None:
    """Extract only the committed source inputs required by the runner."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise ReleaseError(f"execution root already exists: {destination}")
    destination.mkdir()
    required = list(SNAPSHOT_DIRECTORIES) + ["Cargo.toml", "Cargo.lock"]
    optional = list(SNAPSHOT_FILES[2:])
    archive_paths = []
    for snapshot_path in required + optional:
        try:
            subprocess.run(["git", "cat-file", "-e", f"{source_commit}:{snapshot_path}"],
                           cwd=repo_root, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            if snapshot_path in required:
                raise ReleaseError(f"source commit lacks required snapshot path: {snapshot_path}")
            continue
        except OSError as exc:
            raise ReleaseError("cannot inspect source snapshot paths") from exc
        archive_paths.append(snapshot_path)
    process = subprocess.Popen(
        ["git", "archive", "--format=tar", source_commit, "--", *archive_paths], cwd=repo_root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                relative = _safe_member(member.name)
                if relative is None:
                    continue
                target = destination / Path(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise ReleaseError(f"source snapshot contains unsupported entry: {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ReleaseError(f"cannot read source snapshot entry: {member.name}")
                target.write_bytes(source.read())
    finally:
        stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise ReleaseError(f"git archive failed: {stderr.decode(errors='replace').strip()}")
    for required in ("src", "cases", "populations"):
        if not (destination / required).is_dir():
            raise ReleaseError(f"source snapshot lacks required {required}/ tree")


def _resolve_runtime_path(execution_root: Path, value: object, description: str) -> Path:
    relative = _relative(value, description)
    return (execution_root / Path(*relative.parts)).resolve(strict=False)


def _copy_file(source: Path, target: Path) -> dict:
    if source.is_symlink() or not source.is_file():
        raise ReleaseError(f"capture source is not a regular file: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise ReleaseError(f"capture destination already exists: {target}")
    data = source.read_bytes()
    target.write_bytes(data)
    return {"sha256": _sha(data), "bytes": len(data)}


def _copy_tree(source: Path, target: Path, execution_root: Path, capture_root: Path) -> list[dict]:
    if source.is_symlink() or not source.exists():
        raise ReleaseError(f"declared output root is missing or symlinked: {source}")
    files = []
    if source.is_file():
        files = [source]
    elif source.is_dir():
        for current, directories, names in os.walk(source, topdown=True, followlinks=False):
            current_path = Path(current)
            for name in directories:
                if (current_path / name).is_symlink():
                    raise ReleaseError(f"declared output tree contains symlinked directory: {current_path / name}")
            files.extend(current_path / name for name in names)
    else:
        raise ReleaseError(f"declared output root is neither file nor directory: {source}")
    rows = []
    for item in files:
        if item.is_symlink() or not item.is_file():
            raise ReleaseError(f"declared output tree contains non-regular file: {item}")
        relative = item.resolve(strict=True).relative_to(execution_root.resolve())
        target_item = capture_root / Path(*relative.parts)
        identity = _copy_file(item, target_item)
        rows.append({
            "execution_relative": relative.as_posix(),
            "capture_path": str(target_item),
            **identity,
        })
    return rows


def _process_table() -> str:
    try:
        return subprocess.check_output(
            ["ps", "-axo", "pid=,%cpu=,comm=,args="], text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("cannot inspect process contention") from exc


def _contenders(table: str) -> list[str]:
    result = []
    for line in table.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) < 2:
            continue
        try:
            cpu = float(fields[1]) if len(fields) >= 4 else 100.0
        except ValueError:
            cpu = 100.0
        args = fields[3].lower() if len(fields) >= 4 else " ".join(fields[1:]).lower()
        # macOS truncates `comm` to a narrow column. Identify the executable
        # from argv[0], rather than matching repository names in arguments.
        command = Path(args.split()[0]).name if args else ""
        if len(fields) < 4:
            command = Path(fields[1]).name.lower()
        if command in HEAVY_PROCESS_NAMES:
            result.append(line.strip())
            continue
        if command == "bifrost":
            if "--mcp" in args and cpu < 1.0:
                continue
            result.append(line.strip())
    return result


def _check_resources(repo_root: Path) -> None:
    try:
        free = shutil.disk_usage(repo_root).free
    except OSError as exc:
        raise ReleaseError("cannot inspect free disk space") from exc
    if free < MIN_FREE_BYTES:
        raise ReleaseError(f"free disk space is below 64 GiB: {free} bytes")
    busy = _contenders(_process_table())
    if busy:
        raise ReleaseError("contending build/analyzer processes: " + "; ".join(busy))


@contextlib.contextmanager
def _exclusive_lock() -> Iterator[None]:
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(LOCK_PATH, flags, 0o600)
    except OSError as exc:
        raise ReleaseError(f"cannot open common Bifrost lock: {LOCK_PATH}") from exc
    try:
        with os.fdopen(descriptor, "r+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ReleaseError("another Bifrost group owns the common exclusive lock") from exc
            yield
            fcntl.flock(lock, fcntl.LOCK_UN)
    finally:
        # The descriptor is closed by fdopen, including all error paths.
        pass


def _terminate_process_group(process: subprocess.Popen, grace_seconds: float = 2.0) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=grace_seconds)


def _run_process(argv: Sequence[str], cwd: Path, env: Mapping[str, str], stdout: Path, stderr: Path,
                 timeout: float) -> tuple[int, bool, float]:
    started = time.monotonic()
    timed_out = False
    with stdout.open("wb") as out, stderr.open("wb") as err:
        process = subprocess.Popen(
            list(argv), cwd=cwd, env=dict(env), stdout=out, stderr=err,
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
    return (124 if timed_out else process.returncode), timed_out, time.monotonic() - started


CHILD_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "JAVA_HOME", "TMPDIR")


def _child_environment(cache_root: Path) -> dict[str, str]:
    """Construct a complete, secret-free environment for one native run."""
    environment = {key: os.environ[key] for key in CHILD_ENV_KEYS if key in os.environ}
    environment["BIFROST_CACHE_ROOT"] = str(cache_root)
    return environment


def _attempt_paths(repo_root: Path, group_id: str) -> tuple[Path, Path, Path, Path]:
    attempt_id = f"{group_id}-attempt-01"
    attempt = repo_root / Path(*ATTEMPTS_ROOT.parts) / attempt_id
    execution = repo_root / Path(*EXECUTION_ROOT.parts) / group_id
    cache = repo_root / Path(*CACHE_ROOT.parts) / group_id
    return attempt, execution, cache, repo_root / Path(*LEDGER_PATH.parts)


def _ledger_has_group(path: Path, group_id: str) -> bool:
    if not path.exists():
        return False
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"ledger is unreadable: {path}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise ReleaseError("ledger contains a malformed row")
    return any(row.get("group_id") == group_id for row in rows)


def _verified_completed_groups(validated: dict) -> set[str]:
    """Return only groups whose durable receipt and staged reports verify."""
    ledger = validated["repo_root"] / Path(*LEDGER_PATH.parts)
    if not ledger.exists():
        return set()
    try:
        rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"ledger is unreadable: {ledger}") from exc
    verified = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "completed":
            continue
        group_id = row.get("group_id")
        attempt_id = row.get("attempt_id")
        if not isinstance(group_id, str) or not isinstance(attempt_id, str):
            continue
        attempt = validated["repo_root"] / Path(*ATTEMPTS_ROOT.parts) / attempt_id
        completed = attempt / "completed.json"
        try:
            receipt, _ = _read_json(completed, "completed receipt")
        except ReleaseError:
            continue
        if receipt.get("status") != "completed" or receipt.get("group_id") != group_id:
            continue
        reports = receipt.get("reports")
        if not isinstance(reports, list):
            continue
        good = True
        for report in reports:
            if not isinstance(report, dict):
                good = False
                break
            path = validated["repo_root"] / Path(*PurePosixPath(report.get("staged_path", "")).parts)
            if not path.is_file() or _sha(path.read_bytes()) != report.get("staged_sha256"):
                good = False
                break
        if good:
            verified.add(group_id)
    return verified


def _assert_fresh(repo_root: Path, group_id: str, reports: Sequence[dict]) -> tuple[Path, Path, Path, Path]:
    attempt, execution, cache, ledger = _attempt_paths(repo_root, group_id)
    if (attempt.exists() or attempt.is_symlink() or execution.exists() or execution.is_symlink()
            or cache.exists() or cache.is_symlink()):
        raise ReleaseError(f"existing attempt for {group_id}; automatic retry is forbidden")
    if _ledger_has_group(ledger, group_id):
        raise ReleaseError(f"ledger already records an attempt for {group_id}; review is required")
    for report in reports:
        destination = repo_root / Path(*PurePosixPath(report["path"]).parts)
        if destination.exists() or destination.is_symlink():
            raise ReleaseError(f"staged report already exists: {destination}")
    return attempt, execution, cache, ledger


def _report_identity(report: dict, original: bytes, fixture: str) -> dict:
    try:
        value = json.loads(original)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"normalized report is not valid JSON: {report['source_path']}") from exc
    if not isinstance(value, dict):
        raise ReleaseError("normalized report must be a JSON object")
    if value.get("fixture_revision") != fixture or value.get("tool") != "bifrost":
        raise ReleaseError(f"report identity mismatch: {report['source_path']}")
    if value.get("tool_version") != BIFROST_BANNER:
        raise ReleaseError(f"report tool version mismatch: {report['source_path']}")
    results = value.get("results")
    if not isinstance(results, list):
        raise ReleaseError(f"report results must be a list: {report['source_path']}")
    actual = []
    for row in results:
        if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
            raise ReleaseError(f"report result identity is malformed: {report['source_path']}")
        actual.append(row["case_id"])
    if len(actual) != len(set(actual)) or sorted(actual) != sorted(report["case_ids"]):
        raise ReleaseError(f"report case membership mismatch: {report['source_path']}")
    return value


def _stage_report(
    repo_root: Path,
    attempt: Path,
    execution_root: Path,
    attempt_id: str,
    report: dict,
    capture_rows: Mapping[str, dict],
    output_roots: Sequence[Path],
    fixture: str,
) -> dict:
    source = Path(report["source_path"])
    original = source.read_bytes()
    source_key = source.resolve(strict=True).relative_to(execution_root.resolve()).as_posix()
    captured_report = capture_rows.get(source_key)
    if captured_report is None or captured_report["sha256"] != _sha(original):
        raise ReleaseError(f"normalized report changed after capture: {source}")
    normalized = _report_identity(report, original, fixture)
    raw_mappings = []
    for row in normalized["results"]:
        raw_path = _resolve_runtime_path(execution_root, row.get("raw_output"), "raw_output")
        if not any(_under(raw_path, output_root) for output_root in output_roots):
            raise ReleaseError(f"raw_output is outside declared output roots: {raw_path}")
        key = raw_path.relative_to(execution_root.resolve()).as_posix()
        captured = capture_rows.get(key)
        if captured is None:
            raise ReleaseError(f"raw_output was not captured: {raw_path}")
        if row.get("raw_sha256") is not None and row["raw_sha256"] != captured["sha256"]:
            raise ReleaseError(f"raw_output identity mismatch: {raw_path}")
        staged_raw = (ATTEMPTS_ROOT / attempt_id / "capture" / PurePosixPath(key)).as_posix()
        raw_mappings.append({
            "execution_path": str(raw_path),
            "execution_relative": key,
            "captured_path": staged_raw,
            "sha256": captured["sha256"],
            "bytes": captured["bytes"],
        })
        row["raw_output"] = staged_raw
    original_rel = PurePosixPath("original") / PurePosixPath(report["path"])
    original_path = attempt / Path(*original_rel.parts)
    original_path.parent.mkdir(parents=True, exist_ok=True)
    with original_path.open("xb") as target:
        target.write(original)
    destination = repo_root / Path(*PurePosixPath(report["path"]).parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = _json_bytes(normalized)
    with destination.open("xb") as target:
        target.write(staged)
    return {
        "source_path": report["source_path"],
        "staged_path": report["path"],
        "original_path": (ATTEMPTS_ROOT / attempt_id / original_rel).as_posix(),
        "original_sha256": _sha(original),
        "staged_sha256": _sha(staged),
        "case_ids": list(report["case_ids"]),
        "tool": report["tool"],
        "tool_version": report["tool_version"],
        "raw_output_mappings": raw_mappings,
    }


def _file_receipt(path: Path, receipt_path: str) -> dict:
    data = path.read_bytes()
    return {"path": receipt_path, "sha256": _sha(data), "bytes": len(data)}


def _append_ledger(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ledger:
        fcntl.flock(ledger, fcntl.LOCK_EX)
        ledger.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        ledger.flush()
        os.fsync(ledger.fileno())
        fcntl.flock(ledger, fcntl.LOCK_UN)


def run_group(validated: dict, group_id: str) -> dict:
    plan = validated["plan"]
    repo_root: Path = validated["repo_root"]
    group_entry = next((item for item in validated["groups"] if item["id"] == group_id), None)
    if group_entry is None:
        raise ReleaseError(f"unknown group: {group_id}")
    group = next(item for item in plan["groups"] if item["id"] == group_id)
    reports = group_entry["reports"]
    with _exclusive_lock():
        _assert_source_snapshot(repo_root, plan["source_commit"])
        population_binding = plan["population"]
        population_path = _relative(population_binding["path"], "population path")
        _source_file(repo_root, plan["source_commit"], population_path.as_posix(), population_binding["sha256"])
        _check_tool_file(validated["runner"], "runner")
        _check_tool_file(validated["bifrost"], "Bifrost")
        _check_resources(repo_root)
        attempt, execution_root, cache_root, ledger = _assert_fresh(repo_root, group_id, reports)
        attempt_id = attempt.name
        attempt.mkdir(parents=True)
        start = _timestamp()
        cache_root.parent.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir()
        env = _child_environment(cache_root)
        receipt = {
            "schema_version": 1,
            "release": RELEASE,
            "group_id": group_id,
            "attempt_id": attempt_id,
            "status": "started",
            "start_utc": start,
            "end_utc": None,
            "source_commit": plan["source_commit"],
            "fixture_revision": validated["fixture_revision"],
            "population": plan["population"],
            "runner": validated["runner"],
            "bifrost": validated["bifrost"],
            "bifrost_cache_root": str(cache_root),
            "argv": list(group["argv"]),
            "environment": env,
            "execution_root": str(execution_root),
            "output_roots": list(group["output_roots"]),
            "case_ids": list(group["case_ids"]),
            "deadline_seconds": group["deadline_seconds"],
            "started_receipt": "started.json",
        }
        (attempt / "started.json").write_bytes(_json_bytes(receipt))
        row = dict(receipt)
        try:
            _materialize_source(repo_root, plan["source_commit"], execution_root)
            stdout = attempt / "stdout.txt"
            stderr = attempt / "stderr.txt"
            exit_code, timed_out, duration = _run_process(
                group["argv"], execution_root, env, stdout, stderr, group["deadline_seconds"]
            )
            row.update({
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": duration,
                "stdout": _file_receipt(stdout, "stdout.txt"),
                "stderr": _file_receipt(stderr, "stderr.txt"),
            })
            _assert_source_snapshot(repo_root, plan["source_commit"])
            _check_tool_file(validated["runner"], "runner")
            _check_tool_file(validated["bifrost"], "Bifrost")
            capture_root = attempt / "capture"
            capture_rows = []
            for value in group["output_roots"]:
                capture_rows.extend(_copy_tree(Path(value), execution_root, execution_root, capture_root))
            row["captured_files"] = sorted(capture_rows, key=lambda item: item["execution_relative"])
            capture_by_relative = {item["execution_relative"]: item for item in capture_rows}
            if exit_code == 0 and not timed_out:
                row["reports"] = [
                    _stage_report(repo_root, attempt, execution_root, attempt_id, report,
                                  capture_by_relative,
                                  [Path(value).resolve() for value in group["output_roots"]],
                                  validated["fixture_revision"])
                    for report in reports
                ]
            else:
                row["reports"] = []
            row["status"] = "timed-out" if timed_out else ("completed" if exit_code == 0 else "failed")
        except BaseException as exc:
            row["status"] = "recorder-error"
            row["recorder_error"] = f"{type(exc).__name__}: {exc}"
            row.setdefault("captured_files", [])
        finally:
            row["end_utc"] = _timestamp()
            (attempt / "completed.json").write_bytes(_json_bytes(row))
            _append_ledger(ledger, row)
        return row


def _selected(validated: dict, group_id: str | None) -> list[str]:
    ids = [entry["id"] for entry in validated["groups"]]
    if group_id is None:
        return ids
    if group_id not in ids:
        raise ReleaseError(f"unknown group: {group_id}")
    return [group_id]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--group")
    args = parser.parse_args(argv)
    validated = validate_plan(args.plan)
    groups = _selected(validated, args.group)
    if not args.execute:
        print(json.dumps({
            "mode": "plan",
            "release": RELEASE,
            "source_commit": validated["plan"]["source_commit"],
            "groups": groups,
            "group_count": len(groups),
            "execution_authorized": False,
        }, indent=2))
        return 0
    if validated["plan"].get("execution_authorized") is not True:
        raise ReleaseError("plan execution_authorized is not true")
    _qualification_gate(validated["plan"], validated["repo_root"])
    completed = _verified_completed_groups(validated)
    known = {entry["id"] for entry in validated["groups"]}
    completed &= known
    groups = [group_id for group_id in groups if group_id not in completed]
    total_budget = validated["total_wall_budget_seconds"]
    matrix_started = time.monotonic()
    results = []
    for group_id in groups:
        elapsed = time.monotonic() - matrix_started
        deadline = next(item["deadline_seconds"] for item in validated["plan"]["groups"]
                        if item["id"] == group_id)
        if elapsed + deadline > total_budget:
            raise ReleaseError("total wall budget would be exceeded before the next group")
        result = run_group(validated, group_id)
        results.append({"group_id": group_id, "attempt_id": result["attempt_id"], "status": result["status"]})
        print(json.dumps(results[-1], sort_keys=True), flush=True)
        if result["status"] != "completed":
            return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ReleaseError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
