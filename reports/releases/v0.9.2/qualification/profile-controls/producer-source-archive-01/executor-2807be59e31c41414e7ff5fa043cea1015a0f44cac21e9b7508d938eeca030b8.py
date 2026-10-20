#!/usr/bin/env python3
"""Execute the reviewed, serial full-analyzer v0.9.2 release matrix.

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
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
from typing import Iterator, Mapping, Sequence


RELEASE = "v0.9.2"
SOURCE_POPULATION = "v0.9.0"
PARENT_PLAN = PurePosixPath("reports/releases/v0.9.0/plan.json")
PARENT_EXECUTION_CONTRACT = PurePosixPath("reports/releases/v0.9.0/execution-v1/contract.json")
MIN_FREE_BYTES = 125 * 1024**3
PROTECTED_FREE_BYTES = 40 * 1024**3
MAX_RETAINED_BYTES = 24 * 1024**3
LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"
EXECUTION_ROOT = PurePosixPath("execution-state/v092/groups")
CACHE_ROOT = PurePosixPath("execution-state/v092/cache")
ATTEMPTS_ROOT = PurePosixPath("reports/releases/v0.9.2/attempts")
LEDGER_PATH = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
NORMAL_ROOT = PurePosixPath("reports/releases/v0.9.2/normal")
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
    "corpus",
)
SNAPSHOT_FILES = (
    "Cargo.toml",
    "Cargo.lock",
    "reports/releases/v0.9.0/plan.json",
    "docs/v0.9.2-execution.md",
    "README.md",
    "LICENSE",
    "docs/adapters.md",
    "docs/benchmark-sources.md",
    "docs/challenge-tier.md",
    "docs/real-project-preregistration.md",
    "docs/real-project-r2-preregistration.md",
    "docs/real-project-review.md",
)
SNAPSHOT_PATHS = SNAPSHOT_DIRECTORIES + SNAPSHOT_FILES
HEAVY_PROCESS_NAMES = {
    "cargo",
    "cargo-nextest",
    "nextest",
    "rustc",
    "clippy-driver",
    "clang",
    "clang++",
    "gcc",
    "g++",
    "ld",
    "bazel",
    "swift",
    "swiftc",
    "swift-driver",
    "swift-frontend",
    "java",
    "javac",
    "codeql",
    "joern",
    "hyperfine",
    "semgrep",
    "pysemgrep",
    "semgrep-core",
    "pyre",
    "pyre.bin",
    "pyrefly",
    "infer",
    "pysa",
    "flowdroid",
    "opentaint",
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


def _assert_source_snapshot(
    root: Path,
    source_commit: str,
    runner_source_sha256: str | None = None,
    source_inputs: Sequence[dict] = (),
) -> None:
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
        "docs/v0.9.2-execution.md",
        "corpus", "README.md", "LICENSE", "docs/adapters.md",
        "reports/releases/v0.9.0/plan.json",
        "docs/benchmark-sources.md", "docs/challenge-tier.md",
        "docs/real-project-preregistration.md", "docs/real-project-r2-preregistration.md",
        "docs/real-project-review.md",
    ]
    extra_paths = [item["path"] for item in source_inputs]
    paths.extend(extra_paths)
    paths = list(dict.fromkeys(paths))
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
    if runner_source_sha256 is not None:
        expected = _bound_sha(runner_source_sha256, "runner_source_sha256")
        actual = _sha(_git_show(root, source_commit, "scripts/execute-release-v092.py"))
        if actual != expected:
            raise ReleaseError("runner source at source_commit differs from runner_source_sha256")
    for item in source_inputs:
        actual = _sha(_git_show(root, source_commit, item["path"]))
        if actual != item["sha256"]:
            raise ReleaseError(f"source input at source_commit differs from its contract digest: {item['path']}")


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
    if "build_identity" in result and not isinstance(result["build_identity"], str):
        raise ReleaseError(f"tools.{name}.build_identity must be a string")
    if "kind" in result and result["kind"] not in ("file", "runtime-tree-manifest"):
        raise ReleaseError(f"tools.{name}.kind is unsupported")
    if "archive_sha256" in result:
        _bound_sha(result["archive_sha256"], f"tools.{name}.archive_sha256")
    if "binary_sha256" in result and result["binary_sha256"] != digest:
        raise ReleaseError(f"tools.{name}.binary_sha256 must equal tools.{name}.sha256")
    return result


def _check_tool_file(binding: Mapping[str, str], description: str) -> None:
    path = Path(binding["path"])
    if not path.is_file() or path.is_symlink():
        raise ReleaseError(f"{description} is missing or not a regular file: {path}")
    raw = path.read_bytes()
    if _sha(raw) != binding["sha256"]:
        raise ReleaseError(f"{description} SHA-256 differs from the plan: {path}")
    if binding.get("kind") == "runtime-tree-manifest":
        _check_runtime_tree_manifest(raw, description)


def _check_runtime_tree_manifest(raw: bytes, description: str) -> None:
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"{description} runtime tree manifest is invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ReleaseError(f"{description} runtime tree manifest has an unsupported schema")
    root_value = manifest.get("root")
    if not isinstance(root_value, str) or not Path(root_value).is_absolute():
        raise ReleaseError(f"{description} runtime tree manifest must bind an absolute root")
    root = Path(root_value)
    if not root.is_dir() or root.is_symlink():
        raise ReleaseError(f"{description} runtime tree root is missing or symlinked: {root}")
    listed_files = manifest.get("files")
    listed_links = manifest.get("symlinks", [])
    external_files = manifest.get("external_files", [])
    if not isinstance(listed_files, list) or not isinstance(listed_links, list) or not isinstance(external_files, list):
        raise ReleaseError(f"{description} runtime tree inventory fields must be lists")
    expected_files: dict[str, dict] = {}
    for item in listed_files:
        if not isinstance(item, dict):
            raise ReleaseError(f"{description} runtime tree file entry must be an object")
        relative = _relative(item.get("path"), f"{description} runtime tree file path")
        digest = _bound_sha(item.get("sha256"), f"{description} runtime tree file SHA-256")
        if relative.as_posix() in expected_files:
            raise ReleaseError(f"{description} runtime tree has duplicate file entries")
        mode = item.get("mode")
        if mode is not None and (type(mode) is not int or not 0 <= mode <= 0o7777):
            raise ReleaseError(f"{description} runtime tree file mode is malformed")
        expected_files[relative.as_posix()] = {"sha256": digest, "mode": mode}
    expected_links: dict[str, dict] = {}
    for item in listed_links:
        if (not isinstance(item, dict) or not isinstance(item.get("target"), str) or
                not item["target"] or "\x00" in item["target"]):
            raise ReleaseError(f"{description} runtime tree symlink entry is malformed")
        relative = _relative(item.get("path"), f"{description} runtime tree symlink path")
        if relative.as_posix() in expected_files or relative.as_posix() in expected_links:
            raise ReleaseError(f"{description} runtime tree has duplicate entries")
        mode = item.get("mode")
        if mode is not None and (type(mode) is not int or not 0 <= mode <= 0o7777):
            raise ReleaseError(f"{description} runtime tree symlink mode is malformed")
        expected_links[relative.as_posix()] = {"target": item["target"], "mode": mode}
    expected_external: dict[str, dict] = {}
    for item in external_files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ReleaseError(f"{description} runtime tree external file entry is malformed")
        external_path = Path(item["path"])
        if not external_path.is_absolute():
            raise ReleaseError(f"{description} runtime tree external file path must be absolute")
        digest = _bound_sha(item.get("sha256"), f"{description} external runtime file SHA-256")
        if str(external_path) in expected_external:
            raise ReleaseError(f"{description} runtime tree has duplicate external entries")
        mode = item.get("mode")
        if mode is not None and (type(mode) is not int or not 0 <= mode <= 0o7777):
            raise ReleaseError(f"{description} external runtime file mode is malformed")
        expected_external[str(external_path)] = {"sha256": digest, "mode": mode}
    for relative, entry in expected_links.items():
        link_path = root / Path(*PurePosixPath(relative).parts)
        resolved_target = (link_path.parent / entry["target"]).resolve(strict=False)
        if not resolved_target.exists():
            raise ReleaseError(f"{description} runtime tree symlink target is missing: {link_path}")
        if resolved_target.is_dir():
            if _under(resolved_target, root):
                # Internal directory links are allowed: the target's actual
                # file bytes are already covered by the complete root inventory.
                continue
            raise ReleaseError(
                f"{description} runtime tree external directory symlink needs a separately reviewed tree manifest: {link_path}"
            )
        if not resolved_target.is_file():
            raise ReleaseError(f"{description} runtime tree symlink target is not a regular file: {link_path}")
        if not _under(resolved_target, root) and str(resolved_target) not in expected_external:
            raise ReleaseError(
                f"{description} runtime tree external symlink target lacks an exact file binding: {link_path}"
            )

    actual_files = set()
    actual_links = set()
    for current, directories, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                directories.remove(name)
                actual_links.add(relative)
                declared = expected_links.get(relative)
                if not isinstance(declared, dict) or os.readlink(path) != declared["target"]:
                    raise ReleaseError(f"{description} runtime tree symlink differs from manifest: {path}")
                if declared["mode"] is not None and stat.S_IMODE(path.lstat().st_mode) != declared["mode"]:
                    raise ReleaseError(f"{description} runtime tree symlink mode differs from manifest: {path}")
        for name in names:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                actual_links.add(relative)
                declared = expected_links.get(relative)
                if not isinstance(declared, dict) or os.readlink(path) != declared["target"]:
                    raise ReleaseError(f"{description} runtime tree symlink differs from manifest: {path}")
                if declared["mode"] is not None and stat.S_IMODE(path.lstat().st_mode) != declared["mode"]:
                    raise ReleaseError(f"{description} runtime tree symlink mode differs from manifest: {path}")
            elif path.is_file():
                actual_files.add(relative)
                declared = expected_files.get(relative)
                if not isinstance(declared, dict) or _sha(path.read_bytes()) != declared["sha256"]:
                    raise ReleaseError(f"{description} runtime tree file differs from manifest: {path}")
                if declared["mode"] is not None and stat.S_IMODE(path.stat().st_mode) != declared["mode"]:
                    raise ReleaseError(f"{description} runtime tree file mode differs from manifest: {path}")
            else:
                raise ReleaseError(f"{description} runtime tree contains a non-regular entry: {path}")
    if actual_files != set(expected_files) or actual_links != set(expected_links):
        raise ReleaseError(f"{description} runtime tree inventory differs from manifest")
    for path_text, digest in expected_external.items():
        path = Path(path_text)
        if (path.is_symlink() or not path.is_file() or
                _sha(path.read_bytes()) != digest["sha256"] or
                (digest["mode"] is not None and stat.S_IMODE(path.stat().st_mode) != digest["mode"])):
            raise ReleaseError(f"{description} external runtime component differs from manifest: {path}")


def _component_identity(name: str, binding: Mapping[str, str]) -> dict:
    identity = {"name": name, "path": binding["path"], "sha256": binding["sha256"]}
    if "kind" in binding:
        identity["kind"] = binding["kind"]
    for key in ("version", "build_identity", "archive_sha256"):
        if key in binding:
            identity[key] = binding[key]
    return identity


def _population(plan: dict, plan_path: Path) -> tuple[dict, bytes, str]:
    binding = plan.get("population")
    if not isinstance(binding, dict):
        raise ReleaseError("plan must bind a population object")
    path = _relative(binding.get("path"), "population path")
    digest = _bound_sha(binding.get("sha256"), "population.sha256")
    population_path = plan_path.resolve().parents[4] / Path(*path.parts)
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


def _qualification_gate(
    plan: dict, repo_root: Path, tools: Mapping[str, dict],
    tool_components: Mapping[str, list[str]]
) -> dict:
    """Validate exact qualification references and preserve their per-group scope."""
    qualifications = plan.get("qualifications")
    if not isinstance(qualifications, dict):
        raise ReleaseError("contract must bind per-analyzer qualifications")
    used = {group.get("tool") for group in plan.get("groups", []) if isinstance(group, dict)}
    if None in used or used - set(qualifications):
        raise ReleaseError("every analyzer used by a group must have an explicit qualification state")
    checked = {}
    for name in sorted(used):
        qualification = qualifications[name]
        if not isinstance(qualification, dict):
            raise ReleaseError(f"analyzer {name} qualification state must be an object")
        status = qualification.get("status")
        eligible = qualification.get("execution_eligible")
        if status not in ("qualified", "measurement-with-known-limits", "pending", "incomplete", "rejected"):
            raise ReleaseError(f"analyzer {name} has an unknown qualification status")
        qualified_groups = qualification.get("groups", [])
        if (not isinstance(qualified_groups, list) or
                any(not isinstance(group_id, str) for group_id in qualified_groups) or
                len(qualified_groups) != len(set(qualified_groups))):
            raise ReleaseError(f"analyzer {name} qualification groups are malformed")
        used_groups = {group["id"] for group in plan.get("groups", []) if group.get("tool") == name}
        if not set(qualified_groups) <= used_groups:
            raise ReleaseError(f"analyzer {name} qualification claims a group it does not execute")
        if status in ("pending", "incomplete", "rejected"):
            if eligible is not False or qualified_groups:
                raise ReleaseError(f"analyzer {name} non-qualified state cannot authorize groups")
            if "evidence" in qualification:
                raise ReleaseError(f"analyzer {name} cannot bind qualification evidence in status {status}")
            checked[name] = {"status": status, "execution_eligible": False, "groups": []}
            continue
        if (status not in ("qualified", "measurement-with-known-limits") or eligible is not True or
                not qualified_groups):
            raise ReleaseError(f"analyzer {name} execution_eligible contradicts its qualification status")
        binding = tools[name]
        components = [_component_identity(alias, tools[alias])
                      for alias in tool_components.get(name, [])]
        reference = qualification.get("evidence")
        if not isinstance(reference, dict):
            raise ReleaseError(f"analyzer {name} must bind one qualification evidence file")
        relative = _relative(reference.get("path"), f"qualifications.{name}.evidence.path")
        if relative.parts[:4] != PurePosixPath("reports/releases/v0.9.2/qualification").parts:
            raise ReleaseError(f"analyzer {name} qualification evidence must be under v0.9.2/qualification")
        digest = _bound_sha(reference.get("sha256"), f"qualifications.{name}.evidence.sha256")
        evidence, raw = _read_json(repo_root / Path(*relative.parts), f"{name} qualification evidence")
        if _sha(raw) != digest:
            raise ReleaseError(f"analyzer {name} qualification evidence digest mismatch")
        identity = evidence.get("tool")
        expected_identity = {
            "path": binding["path"],
            "sha256": binding["sha256"],
            "version": binding.get("version"),
        }
        for identity_field in ("build_identity", "archive_sha256", "binary_sha256"):
            if identity_field in binding:
                expected_identity[identity_field] = binding[identity_field]
        if (evidence.get("status") != status or not isinstance(identity, dict) or
                evidence.get("execution_eligible") is not eligible or
                evidence.get("groups") != qualified_groups or
                identity != expected_identity or
                evidence.get("identity_components") != components):
            raise ReleaseError(f"analyzer {name} qualification does not witness the exact bound identity")
        checked[name] = {
            "status": status,
            "execution_eligible": eligible,
            "groups": qualified_groups,
            "path": relative.as_posix(),
            "sha256": digest,
        }
    return checked


def _source_inputs(plan: dict, repo_root: Path, qualifications: Mapping[str, dict]) -> list[dict]:
    """Resolve only explicitly named acquisition/qualification files into the snapshot."""
    raw_inputs = plan.get("source_inputs", [])
    if not isinstance(raw_inputs, list):
        raise ReleaseError("source_inputs must be a list of digest-bound files")
    combined: dict[str, dict] = {}
    for item in raw_inputs:
        if not isinstance(item, dict):
            raise ReleaseError("each source_inputs entry must be an object")
        relative = _relative(item.get("path"), "source input path")
        prefixes = (
            PurePosixPath("reports/releases/v0.9.2/acquisition"),
            PurePosixPath("reports/releases/v0.9.2/qualification"),
        )
        if not any(relative.parts[:len(prefix.parts)] == prefix.parts for prefix in prefixes):
            raise ReleaseError("source input must be under the v0.9.2 acquisition or qualification directory")
        digest = _bound_sha(item.get("sha256"), f"source_inputs.{relative.as_posix()}.sha256")
        role = item.get("role", "release-input")
        if not isinstance(role, str) or not role:
            raise ReleaseError(f"source input role is invalid: {relative.as_posix()}")
        candidate = {"path": relative.as_posix(), "sha256": digest, "role": role}
        previous = combined.get(relative.as_posix())
        if previous is not None and previous["sha256"] != digest:
            raise ReleaseError(f"source input has conflicting digests: {relative.as_posix()}")
        combined[relative.as_posix()] = candidate
    for qualification in qualifications.values():
        path = qualification.get("path")
        digest = qualification.get("sha256")
        if path is None:
            continue
        previous = combined.get(path)
        if previous is not None and previous["sha256"] != digest:
            raise ReleaseError(f"qualification input conflicts with source_inputs: {path}")
        combined[path] = {"path": path, "sha256": digest, "role": "qualification-evidence"}
    result = sorted(combined.values(), key=lambda item: item["path"])
    for item in result:
        current = repo_root / Path(*PurePosixPath(item["path"]).parts)
        if not current.is_file() or current.is_symlink() or _sha(current.read_bytes()) != item["sha256"]:
            raise ReleaseError(f"source input is missing or differs from its SHA-256: {current}")
    return result


def _wall_budget(plan: dict) -> float:
    value = plan.get("total_wall_budget_seconds")
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value <= 0):
        raise ReleaseError("plan must bind a positive total_wall_budget_seconds")
    return float(value)


def _historical_plan(repo_root: Path, reference: object) -> tuple[dict, dict[str, dict]]:
    if not isinstance(reference, dict) or reference.get("path") != PARENT_PLAN.as_posix():
        raise ReleaseError(f"contract must bind immutable parent plan at {PARENT_PLAN.as_posix()}")
    digest = _bound_sha(reference.get("sha256"), "parent_plan.sha256")
    path = repo_root / Path(*PARENT_PLAN.parts)
    parent, raw = _read_json(path, "immutable v0.9.0 parent plan")
    if _sha(raw) != digest:
        raise ReleaseError("immutable parent plan bytes differ from the contract SHA-256")
    groups = parent.get("execution_groups")
    reports = parent.get("reports")
    if parent.get("release") != SOURCE_POPULATION or not isinstance(groups, list) or len(groups) != 84:
        raise ReleaseError("parent plan must be the fixed 84-group v0.9.0 plan")
    if not isinstance(reports, list) or len(reports) != 92:
        raise ReleaseError("parent plan must contain exactly 92 report partitions")
    by_id = {}
    for group in groups:
        group_id, case_ids = group.get("id"), group.get("case_ids")
        if (not isinstance(group_id, str) or not SAFE_ID.fullmatch(group_id) or
                not isinstance(case_ids, list) or not case_ids or
                any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or
                len(case_ids) != len(set(case_ids)) or group_id in by_id):
            raise ReleaseError("parent group identity or membership is malformed")
        by_id[group_id] = group
    by_report = {}
    for report in reports:
        if not isinstance(report, dict) or not isinstance(report.get("report"), str):
            raise ReleaseError("parent report partition is malformed")
        if report["report"] in by_report:
            raise ReleaseError("parent report paths are not unique")
        by_report[report["report"]] = report
    return parent, by_id


def _historical_execution_contract(repo_root: Path, reference: object) -> tuple[dict, dict[str, dict]]:
    if not isinstance(reference, dict) or reference.get("path") != PARENT_EXECUTION_CONTRACT.as_posix():
        raise ReleaseError(
            f"contract must bind immutable parent execution contract at {PARENT_EXECUTION_CONTRACT.as_posix()}"
        )
    digest = _bound_sha(reference.get("sha256"), "parent_execution_contract.sha256")
    path = repo_root / Path(*PARENT_EXECUTION_CONTRACT.parts)
    source, raw = _read_json(path, "immutable v0.9.0 execution contract")
    if _sha(raw) != digest:
        raise ReleaseError("immutable v0.9.0 execution contract bytes differ from the contract SHA-256")
    groups = source.get("groups")
    if source.get("release") != SOURCE_POPULATION or not isinstance(groups, list) or len(groups) != 84:
        raise ReleaseError("parent execution contract must be the fixed 84-group v0.9.0 contract")
    by_id = {}
    for group in groups:
        group_id = group.get("id") if isinstance(group, dict) else None
        if not isinstance(group_id, str) or not SAFE_ID.fullmatch(group_id) or group_id in by_id:
            raise ReleaseError("parent execution contract group identity is malformed")
        by_id[group_id] = group
    return source, by_id


def _validate_group_shape(
    group: object,
    population_ids: set[str],
    repo_root: Path,
    tools: Mapping[str, dict],
    tool_components: Mapping[str, list[str]],
    historical: Mapping[str, dict],
    historical_reports: Mapping[str, dict],
) -> tuple[dict, Path, list[dict]]:
    if not isinstance(group, dict):
        raise ReleaseError("each execution group must be an object")
    group_id = group.get("id")
    if not isinstance(group_id, str) or not SAFE_ID.fullmatch(group_id):
        raise ReleaseError("group id is not path-safe")
    if group_id not in historical:
        raise ReleaseError(f"{group_id}: group is not in the fixed v0.9.0 matrix")
    expected_group = historical[group_id]
    execution_root = (repo_root / Path(*EXECUTION_ROOT.parts) / group_id).resolve()
    argv = group.get("argv")
    if (not isinstance(argv, list) or not argv or
            any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv) or
            any("{" in arg or "}" in arg for arg in argv)):
        raise ReleaseError(f"{group_id}: argv must be an exact, fully resolved string list")
    tool = group.get("tool")
    if not isinstance(tool, str) or tool not in tools:
        raise ReleaseError(f"{group_id}: tool must reference an exact analyzer binding")
    family = expected_group.get("tool")
    if group.get("family", family) != family:
        raise ReleaseError(f"{group_id}: analyzer family differs from the historical matrix")
    identities = tool_components.get(tool, [])
    if family in {"codeql", "joern", "semgrep", "pysa"} and not identities:
        raise ReleaseError(f"{group_id}: {tool} must bind exact runtime components")
    case_ids = group.get("case_ids")
    if (not isinstance(case_ids, list) or not case_ids or
            any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or
            len(case_ids) != len(set(case_ids)) or not set(case_ids) <= population_ids or
            case_ids != expected_group.get("case_ids")):
        raise ReleaseError(f"{group_id}: case membership differs from the fixed population plan")
    deadline = group.get("deadline_seconds")
    if (isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or
            not math.isfinite(deadline) or deadline <= 0):
        raise ReleaseError(f"{group_id}: deadline_seconds must be positive and finite")
    output_roots = group.get("output_roots")
    if not isinstance(output_roots, list) or not output_roots:
        raise ReleaseError(f"{group_id}: output_roots must be non-empty")
    roots = []
    for value in output_roots:
        relative = _relative(value, "output root")
        roots.append((execution_root / Path(*relative.parts)).resolve(strict=False))
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
        source = _relative(report.get("source_path"), "report source path")
        source_path = (execution_root / Path(*source.parts)).resolve(strict=False)
        if not any(_under(source_path, root) for root in roots):
            raise ReleaseError(f"{group_id}: report source is outside output roots")
        report_cases = report.get("case_ids")
        if (not isinstance(report_cases, list) or any(not isinstance(case_id, str) for case_id in report_cases) or
                len(report_cases) != len(set(report_cases))):
            raise ReleaseError(f"{group_id}: report case_ids are invalid")
        old_report_path = "reports/releases/v0.9.0/normal/" + destination.name
        registered = historical_reports.get(old_report_path)
        binding = tools[tool]
        expected_report_version = binding.get("report_version", binding.get("version"))
        if (registered is None or registered.get("execution_group") != group_id or
                report_cases != registered.get("case_ids") or report.get("tool") != tool or
                report.get("tool_version") != expected_report_version):
            raise ReleaseError(f"{group_id}: report partition or witnessed tool identity differs from the parent plan")
        seen_cases.extend(report_cases)
        normalized_reports.append({
            **report,
            "path": destination.as_posix(),
            "source_path": source.as_posix(),
            "case_ids": report_cases,
        })
    if sorted(seen_cases) != sorted(case_ids) or len(seen_cases) != len(set(seen_cases)):
        raise ReleaseError(f"{group_id}: report partitions do not exactly match group case_ids")
    if [report["path"] for report in normalized_reports] != [
            path.replace("reports/releases/v0.9.0/normal/", f"{NORMAL_ROOT.as_posix()}/", 1)
            for path in expected_group.get("reports", [])]:
        raise ReleaseError(f"{group_id}: report destinations differ from the exact 92-partition mapping")
    env = group.get("environment")
    if (not isinstance(env, dict) or "PATH" not in env or
            any(not isinstance(key, str) or not isinstance(value, str) for key, value in env.items())):
        raise ReleaseError(f"{group_id}: a complete explicit child environment is required")
    if any(token in key.upper() for key in env for token in ("SECRET", "TOKEN", "PASSWORD", "CREDENTIAL")):
        raise ReleaseError(f"{group_id}: secret-bearing environment keys are not permitted")
    attempts = group.get("maximum_attempts", 1)
    if type(attempts) is not int or not 1 <= attempts <= 2:
        raise ReleaseError(f"{group_id}: maximum_attempts must be one or two")
    return {
        **group,
        "output_roots": [root.relative_to(execution_root).as_posix() for root in roots],
        "identity_components": list(identities),
    }, execution_root, normalized_reports


def _validate_swift_codeql_plan(
    group: Mapping[str, object],
    repo_root: Path,
    swift_packs_root: Path,
    swift_packs_component: str,
    swift_packs_manifest_sha256: str,
) -> tuple[str, str]:
    """Bind the Swift wrapper plan to its separately inventoried custom pack.

    The wrapper has no ``--codeql-packs`` option. Its versioned plan carries
    the absolute runtime root instead, while the normal adapter commands carry
    that root directly on their CLI.
    """
    argv = group.get("argv")
    if not isinstance(argv, list):
        raise ReleaseError(f"{group.get('id')}: Swift CodeQL argv is malformed")
    plan_flags = [index for index, item in enumerate(argv) if item == "--plan"]
    if len(plan_flags) != 1 or plan_flags[0] + 1 >= len(argv):
        raise ReleaseError(f"{group.get('id')}: Swift CodeQL command must bind one versioned --plan")
    relative = _relative(argv[plan_flags[0] + 1], "Swift CodeQL plan path")
    if relative.parts[:3] != ("adapters", "codeql", "swift-common-v2") or relative.name not in ("plan.json", "execution-plan.json"):
        raise ReleaseError(f"{group.get('id')}: Swift CodeQL plan must be a versioned adapter plan")
    path = repo_root / Path(*relative.parts)
    try:
        plan, raw = _read_json(path, "versioned Swift CodeQL plan")
    except ReleaseError as exc:
        raise ReleaseError(f"{group.get('id')}: cannot bind its Swift CodeQL plan: {exc}") from exc
    if (plan.get("schema") != "swift-common-execution-plan/v092" or
            plan.get("profile") != "v0.9.2" or plan.get("engine") != "codeql" or
            plan.get("execution_eligible") is not True):
        raise ReleaseError(f"{group.get('id')}: Swift CodeQL command must use the v0.9.2 CodeQL plan")
    codeql_component = plan.get("codeql_packs")
    declared_root = codeql_component.get("root") if isinstance(codeql_component, dict) else None
    manifest_component = codeql_component.get("runtime_tree_component") if isinstance(codeql_component, dict) else None
    manifest_sha = codeql_component.get("runtime_tree_manifest_sha256") if isinstance(codeql_component, dict) else None
    if (not isinstance(declared_root, str) or not Path(declared_root).is_absolute() or
            Path(declared_root).resolve() != swift_packs_root):
        raise ReleaseError(f"{group.get('id')}: Swift plan must bind the exact absolute v0.9.2 custom Swift pack root")
    if manifest_component != swift_packs_component:
        raise ReleaseError(f"{group.get('id')}: Swift plan must identify the dedicated custom Swift pack component")
    if manifest_sha != swift_packs_manifest_sha256:
        raise ReleaseError(f"{group.get('id')}: Swift plan custom pack manifest SHA differs from the contract")
    return relative.as_posix(), _sha(raw)


def _validate_joern_common_plan(group: Mapping[str, object], repo_root: Path) -> tuple[str, str]:
    """Bind the fresh Joern common-108 executable plan to the group attempt."""
    argv = group.get("argv")
    if not isinstance(argv, list):
        raise ReleaseError(f"{group.get('id')}: Joern argv is malformed")
    plan_flags = [index for index, item in enumerate(argv) if item == "--plan"]
    if len(plan_flags) != 1 or plan_flags[0] + 1 >= len(argv):
        raise ReleaseError(f"{group.get('id')}: Joern command must bind one versioned --plan")
    relative = _relative(argv[plan_flags[0] + 1], "Joern plan path")
    if relative.parts[:4] != ("adapters", "joern", "swift-common-v2", "plan-v092-01") or relative.name != "execution-plan.json":
        raise ReleaseError(f"{group.get('id')}: Joern plan must be the v0.9.2 executable common plan")
    path = repo_root / Path(*relative.parts)
    plan, raw = _read_json(path, "versioned Joern common plan")
    if (plan.get("schema") != "joern-common-execution-plan/v092" or
            plan.get("profile") != "v0.9.2" or plan.get("engine") != "joern" or
            plan.get("release_group_id") != "joern-swift-common108" or
            plan.get("status") != "execution-eligible" or plan.get("execution_eligible") is not True or
            plan.get("scored_activation") is not False or
            plan.get("aggregate_resource_qualification") != "unavailable"):
        raise ReleaseError(f"{group.get('id')}: Joern command must use its eligible v0.9.2 common plan")
    return relative.as_posix(), _sha(raw)


def validate_plan(plan_path: str | Path, *, repo_root: str | Path | None = None) -> dict:
    """Validate the immutable v0.9.2 execution contract without launching tools."""
    path = Path(plan_path).expanduser().resolve()
    if path.name != "contract.json" or path.parts[-5:-1] != ("reports", "releases", "v0.9.2", "execution-v1"):
        raise ReleaseError("contract must be reports/releases/v0.9.2/execution-v1/contract.json")
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else _repo_root(path.parent)
    if not _under(path, root):
        raise ReleaseError("plan must be inside the execution repository")
    plan, plan_raw = _read_json(path, "release plan")
    if plan.get("schema_version") != 1 or plan.get("release") != RELEASE:
        raise ReleaseError("plan schema or release identity mismatch")
    if type(plan.get("execution_series")) is not int or plan["execution_series"] < 1:
        raise ReleaseError("contract must bind a positive execution_series")
    if not isinstance(plan.get("execution_authorized"), bool):
        raise ReleaseError("plan must explicitly bind execution_authorized")
    source_commit = plan.get("source_commit")
    if not isinstance(source_commit, str) or not COMMIT.fullmatch(source_commit):
        raise ReleaseError("plan must bind an exact source_commit")
    population, population_raw, fixture = _population(plan, path)
    parent, historical = _historical_plan(root, plan.get("parent_plan"))
    parent_execution, source_groups = _historical_execution_contract(
        root, plan.get("parent_execution_contract")
    )
    if set(source_groups) != set(historical):
        raise ReleaseError("parent plan and execution contract group IDs differ")
    if not isinstance(plan.get("runner_source_sha256"), str) or not SHA256.fullmatch(plan["runner_source_sha256"]):
        raise ReleaseError("contract must bind the exact v0.9.2 runner source SHA-256")
    tools_raw = plan.get("tools")
    if not isinstance(tools_raw, dict) or not tools_raw:
        raise ReleaseError("contract must bind exact analyzer tools")
    tools = {name: _tool_binding(tools_raw, name) for name in tools_raw}
    components_raw = plan.get("tool_components")
    if not isinstance(components_raw, dict):
        raise ReleaseError("contract must bind exact analyzer runtime components")
    tool_components: dict[str, list[str]] = {}
    for name, aliases in components_raw.items():
        if name not in tools or not isinstance(aliases, list) or not aliases:
            raise ReleaseError(f"tool_components.{name} must name an analyzer and a non-empty component list")
        if (any(not isinstance(alias, str) or alias not in tools or alias == name for alias in aliases) or
                len(aliases) != len(set(aliases))):
            raise ReleaseError(f"tool_components.{name} contains an invalid or duplicate component alias")
        tool_components[name] = list(aliases)
    expected_families = {"bifrost", "codeql", "joern", "semgrep", "opentaint", "infer", "flowdroid", "pysa"}
    if plan.get("population", {}).get("sha256") != parent.get("population", {}).get("sha256"):
        raise ReleaseError("population identity differs from the immutable parent plan")
    if fixture != parent.get("fixture_revision"):
        raise ReleaseError("fixture revision differs from the immutable parent plan")
    population_ids = {case["id"] for case in population["cases"]}
    if len(population_ids) != 1108:
        raise ReleaseError("fixed v0.9.0 source population must contain exactly 1,108 cases")
    groups = plan.get("groups")
    if not isinstance(groups, list) or len(groups) != 84:
        raise ReleaseError("contract must contain exactly the 84 historical execution groups")
    historical_reports = {report["report"]: report for report in parent["reports"]}
    seen_groups: set[str] = set()
    validated = []
    for group in groups:
        checked, execution_root, reports = _validate_group_shape(
            group, population_ids, root, tools, tool_components, historical, historical_reports
        )
        group_id = checked["id"]
        if group_id in seen_groups:
            raise ReleaseError(f"duplicate group id: {group_id}")
        seen_groups.add(group_id)
        validated.append({**checked, "execution_root": execution_root, "reports": reports})
    all_cases = [case_id for group in groups for case_id in group["case_ids"]]
    used_families = {group.get("family", historical[group.get("id")].get("tool")) for group in groups}
    if (seen_groups != set(historical) or len({case_id for case_id in all_cases}) != 1108 or
            used_families != expected_families):
        raise ReleaseError("contract groups must preserve all 84 IDs and cover the fixed 1,108-case population")
    if sum(len(group.get("reports", [])) for group in groups) != 92:
        raise ReleaseError("contract must preserve the exact 92 report partitions")
    if {group.get("tool") for group in groups} - set(tools):
        raise ReleaseError("contract references an unbound analyzer")
    # Every executable and analyzer identity is rehashed before and after its group.
    for name, binding in tools.items():
        _check_tool_file(binding, name)
    codeql_packs = plan.get("codeql_packs")
    if not isinstance(codeql_packs, dict):
        raise ReleaseError("contract must bind the exact v0.9.2 CodeQL pack roots")
    packs_root_value = codeql_packs.get("root")
    packs_alias = codeql_packs.get("component")
    expected_packs_root = (root / "execution-state/v092/tools/codeql-packs").resolve()
    if (not isinstance(packs_root_value, str) or not Path(packs_root_value).is_absolute() or
            Path(packs_root_value).resolve() != expected_packs_root):
        raise ReleaseError("CodeQL pack root must be execution-state/v092/tools/codeql-packs")
    if (not isinstance(packs_alias, str) or packs_alias not in tools or
            tools[packs_alias].get("kind") != "runtime-tree-manifest"):
        raise ReleaseError("CodeQL pack root must have a runtime-tree-manifest component binding")
    try:
        packs_manifest = json.loads(Path(tools[packs_alias]["path"]).read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError("cannot read CodeQL pack tree manifest") from exc
    if Path(packs_manifest.get("root", "")).resolve() != expected_packs_root:
        raise ReleaseError("CodeQL pack manifest does not bind the exact v0.9.2 pack root")
    if packs_alias not in tool_components.get("codeql", []):
        raise ReleaseError("CodeQL pack manifest must be an identity component of tool codeql")
    swift_packs_root_value = codeql_packs.get("swift_root")
    swift_packs_alias = codeql_packs.get("swift_component")
    expected_swift_packs_root = (root / "execution-state/v092/tools/swift-codeql/candidate-packs").resolve()
    if (not isinstance(swift_packs_root_value, str) or not Path(swift_packs_root_value).is_absolute() or
            Path(swift_packs_root_value).resolve() != expected_swift_packs_root):
        raise ReleaseError("custom Swift pack root must be execution-state/v092/tools/swift-codeql/candidate-packs")
    if (not isinstance(swift_packs_alias, str) or swift_packs_alias not in tools or
            tools[swift_packs_alias].get("kind") != "runtime-tree-manifest"):
        raise ReleaseError("custom Swift pack root must have a runtime-tree-manifest component binding")
    try:
        swift_packs_manifest = json.loads(Path(tools[swift_packs_alias]["path"]).read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError("cannot read custom Swift pack tree manifest") from exc
    if Path(swift_packs_manifest.get("root", "")).resolve() != expected_swift_packs_root:
        raise ReleaseError("custom Swift pack manifest does not bind the exact v0.9.2 Swift pack root")
    if swift_packs_alias not in tool_components.get("codeql", []):
        raise ReleaseError("custom Swift pack manifest must be an identity component of tool codeql")
    codeql_aliases = {group.get("tool") for group in groups if group.get("family") == "codeql"}
    if codeql_aliases != {"codeql"}:
        raise ReleaseError("all CodeQL groups must use the single normalized codeql tool identity")
    for group in groups:
        if group.get("family") == "codeql":
            argv = group["argv"]
            if packs_alias not in tool_components.get(group["tool"], []):
                raise ReleaseError(f"{group['id']}: CodeQL pack manifest must be in runtime component identity")
            is_swift_wrapper = any(Path(item).name in ("run-swift-common-v2.py", "run-swift-common-v092.py") for item in argv)
            flags = [index for index, item in enumerate(argv) if item == "--codeql-packs"]
            if is_swift_wrapper:
                if flags:
                    raise ReleaseError(f"{group['id']}: Swift wrapper does not accept --codeql-packs")
                swift_path, swift_sha = _validate_swift_codeql_plan(
                    group, root, expected_swift_packs_root, swift_packs_alias,
                    tools[swift_packs_alias]["sha256"]
                )
                checked_group = next(item for item in validated if item["id"] == group["id"])
                checked_group["swift_plan"] = {"path": swift_path, "sha256": swift_sha}
            elif (len(flags) != 1 or flags[0] + 1 >= len(argv) or
                  argv[flags[0] + 1] != str(expected_packs_root)):
                raise ReleaseError(f"{group['id']}: CodeQL group must bind --codeql-packs to the exact v0.9.2 root")
        elif group.get("id") == "joern-swift-common108":
            if (group.get("family") != "joern" or
                    not any(Path(item).name == "run-joern-common-v092.py" for item in group["argv"])):
                raise ReleaseError("joern-swift-common108 must use the fresh v0.9.2 runner")
            checked_group = next(item for item in validated if item["id"] == group["id"])
            joern_path, joern_sha = _validate_joern_common_plan(group, root)
            checked_group["joern_plan"] = {"path": joern_path, "sha256": joern_sha}
    resource = plan.get("resource_budget")
    if not isinstance(resource, dict) or resource.get("serial_analyzers") != 1:
        raise ReleaseError("contract must reserve one serial analyzer slot")
    minimum_gib = resource.get("minimum_launch_free_gib")
    if type(minimum_gib) is not int or minimum_gib < 125:
        raise ReleaseError("contract must preserve the 125 GiB minimum launch reserve")
    if resource.get("protected_reserve_gib") != 40:
        raise ReleaseError("contract must preserve the 40 GiB protected reserve")
    for key in ("scratch_gib", "proposed_total_retention_ceiling_gib"):
        value = resource.get(key)
        if type(value) is not int or not 0 < value <= 24:
            raise ReleaseError(f"contract must preserve the 24 GiB {key} ceiling")
    if not isinstance(plan.get("resource_reservation"), dict):
        raise ReleaseError("contract must bind a live exclusive resource reservation")
    total_wall_budget = _wall_budget(plan)
    qualification = _qualification_gate(plan, root, tools, tool_components)
    source_inputs = _source_inputs(plan, root, qualification)
    return {
        "path": str(path),
        "bytes_sha256": _sha(plan_raw),
        "repo_root": root,
        "plan": plan,
        "plan_raw": plan_raw,
        "population_raw": population_raw,
        "fixture_revision": fixture,
        "tools": tools,
        "parent_plan": parent,
        "parent_execution_contract": parent_execution,
        "tool_components": tool_components,
        "codeql_packs": {"root": str(expected_packs_root), "component": packs_alias},
        "qualification": qualification,
        "source_inputs": source_inputs,
        "execution_authorized": plan.get("execution_authorized") is True,
        "total_wall_budget_seconds": total_wall_budget,
        "groups": validated,
    }


def _source_file(root: Path, commit: str, relative: str, expected: str) -> bytes:
    data = _git_show(root, commit, relative)
    if _sha(data) != expected:
        raise ReleaseError(f"{relative} at source_commit differs from the plan")
    return data


def _assert_contract_snapshot(validated: dict) -> str:
    """Bind the later plan commit without requiring a self-referential source commit."""
    root = validated["repo_root"]
    path = Path(validated["path"]).resolve()
    relative = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    if _sha(raw) != validated["bytes_sha256"]:
        raise ReleaseError("contract changed after validation")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if _git_show(root, commit, relative) != raw:
        raise ReleaseError("contract differs from the committed execution plan")
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--", relative], cwd=root, text=True,
    )
    if status.strip():
        raise ReleaseError("contract must be committed and clean before execution")
    return commit


def _safe_member(name: str, explicit_files: set[str] | None = None) -> PurePosixPath | None:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ReleaseError(f"unsafe member in source archive: {name}")
    value = path.as_posix()
    if path.parts and path.parts[0] in SNAPSHOT_DIRECTORIES:
        return path
    if value in SNAPSHOT_FILES:
        return path
    if explicit_files and value in explicit_files:
        return path
    return None


def _materialize_source(
    repo_root: Path,
    source_commit: str,
    destination: Path,
    explicit_files: Sequence[str] = (),
) -> None:
    """Extract only the committed source inputs required by the runner."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise ReleaseError(f"execution root already exists: {destination}")
    destination.mkdir()
    required = list(SNAPSHOT_DIRECTORIES) + ["Cargo.toml", "Cargo.lock"]
    optional = list(SNAPSHOT_FILES[2:])
    explicit = list(explicit_files)
    archive_paths = []
    for snapshot_path in list(dict.fromkeys(required + optional + explicit)):
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
                relative = _safe_member(member.name, set(explicit))
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
                target.chmod(stat.S_IMODE(member.mode))
    finally:
        stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise ReleaseError(f"git archive failed: {stderr.decode(errors='replace').strip()}")
    for required in ("src", "cases", "populations"):
        if not (destination / required).is_dir():
            raise ReleaseError(f"source snapshot lacks required {required}/ tree")


def _register_source_snapshot(repo_root: Path, source_commit: str, destination: Path) -> str:
    """Let legacy path-scoped Git checks compare against the real source commit.

    Objects remain read-only in the owning repository. Only this task-owned
    snapshot receives a new index and detached HEAD; it is not a full checkout
    of historical reports and makes no whole-worktree cleanliness claim.
    """
    metadata = destination / ".git"
    if metadata.exists():
        raise ReleaseError("snapshot Git metadata already exists")
    common = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=repo_root, text=True,
    ).strip()
    objects = (repo_root / common / "objects").resolve()
    if not objects.is_dir():
        raise ReleaseError("source object store is unavailable")
    subprocess.run(["git", "init", "--quiet", "--template="], cwd=destination, check=True)
    alternates = metadata / "objects/info/alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternates.write_text(str(objects) + "\n")
    subprocess.run(["git", "update-ref", "--no-deref", "HEAD", source_commit], cwd=destination, check=True)
    subprocess.run(["git", "read-tree", source_commit], cwd=destination, check=True)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, text=True).strip()
    if actual != source_commit:
        raise ReleaseError("snapshot HEAD differs from the canonical source commit")
    return actual


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
        if (command in HEAVY_PROCESS_NAMES or command.startswith(("bazel-", "suite_"))):
            result.append(line.strip())
            continue
        if command == "bifrost":
            if ("--mcp" in args or "--lsp" in args) and cpu < 1.0:
                continue
            result.append(line.strip())
    return result


def _check_resources(repo_root: Path, minimum_launch_bytes: int = MIN_FREE_BYTES) -> None:
    try:
        free = shutil.disk_usage(repo_root).free
    except OSError as exc:
        raise ReleaseError("cannot inspect free disk space") from exc
    if free < minimum_launch_bytes:
        raise ReleaseError(f"free disk space is below the launch requirement of {minimum_launch_bytes} bytes: {free} bytes")
    busy = _contenders(_process_table())
    if busy:
        raise ReleaseError("contending build/analyzer processes: " + "; ".join(busy))


@contextlib.contextmanager
def _exclusive_lock() -> Iterator[None]:
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(LOCK_PATH, flags, 0o600)
    except OSError as exc:
        raise ReleaseError(f"cannot open common analyzer lock: {LOCK_PATH}") from exc
    try:
        with os.fdopen(descriptor, "r+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ReleaseError("another analyzer group owns the common exclusive lock") from exc
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


def _tree_bytes(paths: Sequence[Path]) -> int:
    total = 0
    seen = set()
    for root in paths:
        if not root.exists():
            continue
        for directory, _directories, names in os.walk(root, followlinks=False):
            for name in names:
                path = Path(directory) / name
                try:
                    info = path.lstat()
                except (FileNotFoundError, NotADirectoryError):
                    # Analyzer temporary trees are deleted concurrently. An
                    # entry already gone consumes no current disk capacity.
                    continue
                identity = (info.st_dev, info.st_ino)
                if stat.S_ISREG(info.st_mode) and identity not in seen:
                    seen.add(identity)
                    total += info.st_size
    return total


def _capacity_loss(cwd: Path, retained_paths: Sequence[Path], retention_limit: int,
                   scratch_paths: Sequence[Path] = (), scratch_limit: int = MAX_RETAINED_BYTES) -> str | None:
    free = shutil.disk_usage(cwd).free
    if free < PROTECTED_FREE_BYTES:
        return f"protected disk reserve lost: {free} bytes free"
    retained = _tree_bytes(retained_paths)
    if retained > retention_limit:
        return f"retention ceiling exceeded: {retained} bytes"
    scratch = _tree_bytes(scratch_paths)
    if scratch > scratch_limit:
        return f"scratch ceiling exceeded: {scratch} bytes"
    return None


def _run_process(argv: Sequence[str], cwd: Path, env: Mapping[str, str], stdout: Path, stderr: Path,
                 timeout: float, *, retained_paths: Sequence[Path] = (),
                 retention_limit: int = MAX_RETAINED_BYTES,
                 scratch_paths: Sequence[Path] = (),
                 scratch_limit: int = MAX_RETAINED_BYTES) -> tuple[int, bool, float, str | None]:
    started = time.monotonic()
    timed_out = False
    capacity_loss = None
    with stdout.open("wb") as out, stderr.open("wb") as err:
        capacity_loss = _capacity_loss(cwd, retained_paths, retention_limit, scratch_paths, scratch_limit)
        if capacity_loss:
            return 125, False, time.monotonic() - started, capacity_loss
        process = subprocess.Popen(
            list(argv), cwd=cwd, env=dict(env), stdout=out, stderr=err,
            start_new_session=True, close_fds=True,
        )
        try:
            while process.poll() is None:
                capacity_loss = _capacity_loss(cwd, retained_paths, retention_limit, scratch_paths, scratch_limit)
                if capacity_loss:
                    _terminate_process_group(process)
                    break
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    timed_out = True
                    _terminate_process_group(process)
                    break
                try:
                    process.wait(timeout=min(2.0, remaining))
                except subprocess.TimeoutExpired:
                    continue
        except BaseException:
            _terminate_process_group(process)
            raise
        capacity_loss = capacity_loss or _capacity_loss(cwd, retained_paths, retention_limit, scratch_paths, scratch_limit)
    return (124 if timed_out else process.returncode), timed_out, time.monotonic() - started, capacity_loss


def _child_environment(group: Mapping[str, object], execution_root: Path,
                       attempt_root: Path, cache_root: Path) -> dict[str, str]:
    """Expand only the three reviewed attempt-local environment markers."""
    raw = group.get("environment")
    if not isinstance(raw, dict):
        raise ReleaseError("group environment must be an explicit object")
    substitutions = {
        "@EXECUTION_ROOT@": str(execution_root),
        "@ATTEMPT_ROOT@": str(attempt_root),
        "@CACHE_ROOT@": str(cache_root),
    }
    environment = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ReleaseError("child environment must contain only strings")
        for marker, replacement in substitutions.items():
            value = value.replace(marker, replacement)
        if "@EXECUTION_ROOT@" in value or "@ATTEMPT_ROOT@" in value or "@CACHE_ROOT@" in value:
            raise ReleaseError(f"unresolved child-environment marker in {key}")
        environment[key] = value
    # Keep mutable caches and temporary files inside this group's own attempt.
    environment["HOME"] = str(execution_root / "home")
    environment["TMPDIR"] = str(execution_root / "tmp")
    environment["DFB_CACHE_ROOT"] = str(cache_root)
    environment["BIFROST_CACHE_ROOT"] = str(cache_root)
    argv = [item for item in group.get("argv", []) if isinstance(item, str)]
    entrypoints = {Path(item).name for item in argv}
    if entrypoints & {"run-swift-common-v092.py", "run-joern-common-v092.py"}:
        environment["DATAFLOWBENCH_V092_RELEASE_EXECUTION"] = "1"
        environment["DATAFLOWBENCH_V092_GROUP_ID"] = str(group.get("id", ""))
    if (("run-swift-common-v092.py" in entrypoints and "check-queries" in argv) or
            ("run-joern-common-v092.py" in entrypoints and "controls" in argv)):
        environment["DATAFLOWBENCH_V092_QUALIFICATION"] = "1"
        environment["DATAFLOWBENCH_V092_GROUP_ID"] = str(group.get("id", ""))
    return environment


def _attempt_paths(
    repo_root: Path, group_id: str, series: int, attempt_number: int | None = None
) -> tuple[Path, Path, Path, Path]:
    if attempt_number is None:
        attempt_number = series
    attempt_id = f"{group_id}-attempt-{attempt_number:02d}-series-{series:02d}"
    attempt = repo_root / Path(*ATTEMPTS_ROOT.parts) / attempt_id
    execution = repo_root / Path(*EXECUTION_ROOT.parts) / f"series-{series:02d}" / group_id
    cache = repo_root / Path(*CACHE_ROOT.parts) / f"series-{series:02d}" / group_id
    return attempt, execution, cache, repo_root / Path(*LEDGER_PATH.parts)


def _ledger_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"ledger is unreadable: {path}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise ReleaseError("ledger contains a malformed row")
    return rows


def _verified_completed_groups(validated: dict) -> set[str]:
    """Return only groups whose durable receipt and staged reports verify."""
    ledger = validated["repo_root"] / Path(*LEDGER_PATH.parts)
    if not ledger.exists():
        return set()
    rows = _ledger_rows(ledger)
    verified = set()
    current_series = validated["plan"]["execution_series"]
    expected_groups = {item["id"]: item for item in validated["plan"]["groups"]}
    normalized_groups = {item["id"]: item for item in validated["groups"]}
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "completed":
            continue
        group_id = row.get("group_id")
        attempt_id = row.get("attempt_id")
        if (not isinstance(group_id, str) or group_id not in expected_groups or
                not isinstance(attempt_id, str) or not SAFE_ID.fullmatch(attempt_id) or
                row.get("execution_series") != current_series or
                row.get("contract_sha256") != validated["bytes_sha256"]):
            continue
        attempt = validated["repo_root"] / Path(*ATTEMPTS_ROOT.parts) / attempt_id
        completed = attempt / "completed.json"
        try:
            receipt, _ = _read_json(completed, "completed receipt")
        except ReleaseError:
            continue
        if (receipt.get("status") != "completed" or receipt.get("group_id") != group_id or
                receipt.get("attempt_id") != attempt_id or
                receipt.get("execution_series") != current_series or
                receipt.get("contract_sha256") != validated["bytes_sha256"] or
                receipt.get("source_commit") != validated["plan"]["source_commit"] or
                receipt.get("case_ids") != expected_groups[group_id]["case_ids"] or
                receipt.get("tool") != expected_groups[group_id]["tool"] or
                receipt.get("tool_binding") != validated["tools"][expected_groups[group_id]["tool"]] or
                receipt.get("identity_components") != [
                    _component_identity(alias, validated["tools"][alias])
                    for alias in normalized_groups[group_id]["identity_components"]
                ] or
                receipt.get("swift_plan") != normalized_groups[group_id].get("swift_plan")):
            continue
        reports = receipt.get("reports")
        expected_reports = normalized_groups[group_id]["reports"]
        if not isinstance(reports, list) or len(reports) != len(expected_reports):
            continue
        good = True
        for report, expected in zip(reports, expected_reports):
            if not isinstance(report, dict):
                good = False
                break
            staged = _relative(report.get("staged_path"), "completed staged report path")
            expected_staged = (NORMAL_ROOT / "attempts" / attempt_id /
                               PurePosixPath(expected["path"]).relative_to(NORMAL_ROOT))
            if (staged != expected_staged or report.get("case_ids") != expected["case_ids"] or
                    report.get("tool") != expected["tool"] or
                    report.get("tool_version") != expected["tool_version"]):
                good = False
                break
            path = validated["repo_root"] / Path(*staged.parts)
            if not path.is_file() or path.is_symlink() or _sha(path.read_bytes()) != report.get("staged_sha256"):
                good = False
                break
            original_rel = _relative(report.get("original_path"), "completed original report path")
            expected_original = ATTEMPTS_ROOT / attempt_id / "original" / PurePosixPath(expected["path"])
            original = validated["repo_root"] / Path(*original_rel.parts)
            if (original_rel != expected_original or not original.is_file() or original.is_symlink() or
                    _sha(original.read_bytes()) != report.get("original_sha256")):
                good = False
                break
            try:
                _report_identity(expected, path.read_bytes(), validated["fixture_revision"])
            except (OSError, ReleaseError):
                good = False
                break
        if good:
            verified.add(group_id)
    return verified


def _assert_fresh(repo_root: Path, group: Mapping[str, object], reports: Sequence[dict],
                  series: int) -> tuple[Path, Path, Path, Path, str]:
    group_id = str(group["id"])
    ledger = repo_root / Path(*LEDGER_PATH.parts)
    prior = [row for row in _ledger_rows(ledger) if row.get("group_id") == group_id]
    if any(row.get("execution_series") == series for row in prior):
        raise ReleaseError(f"group {group_id} already has retained evidence for this execution series")
    if len(prior) >= int(group.get("maximum_attempts", 1)):
        raise ReleaseError(f"group {group_id} exceeds its reviewed maximum_attempts")
    attempt_number = len(prior) + 1
    attempt, execution, cache, ledger = _attempt_paths(repo_root, group_id, series, attempt_number)
    if (attempt.exists() or attempt.is_symlink() or execution.exists() or execution.is_symlink()
            or cache.exists() or cache.is_symlink()):
        raise ReleaseError(f"existing v0.9.2 attempt for {group_id}; it cannot be overwritten")
    for report in reports:
        destination_rel = PurePosixPath("reports/releases/v0.9.2/normal/attempts") / attempt.name / PurePosixPath(report["path"]).relative_to(NORMAL_ROOT)
        destination = repo_root / Path(*destination_rel.parts)
        if destination.exists() or destination.is_symlink():
            raise ReleaseError(f"staged report already exists: {destination}")
    return attempt, execution, cache, ledger, attempt.name


def _require_group_qualification(validated: dict, group_id: str) -> dict:
    group = next((item for item in validated["plan"]["groups"] if item["id"] == group_id), None)
    if group is None:
        raise ReleaseError(f"unknown group: {group_id}")
    qualification = validated["qualification"].get(group["tool"], {})
    if (qualification.get("execution_eligible") is not True or
            group_id not in qualification.get("groups", [])):
        raise ReleaseError(
            f"group {group_id} is not covered by eligible qualification for {group['tool']}"
        )
    return qualification


def _report_identity(report: dict, original: bytes, fixture: str) -> dict:
    try:
        value = json.loads(original)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"normalized report is not valid JSON: {report['source_path']}") from exc
    if not isinstance(value, dict):
        raise ReleaseError("normalized report must be a JSON object")
    if value.get("fixture_revision") != fixture or value.get("tool") != report["tool"]:
        raise ReleaseError(f"report identity mismatch: {report['source_path']}")
    if value.get("tool_version") != report["tool_version"]:
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
    execution_root = execution_root.resolve()
    source_rel = _relative(report["source_path"], "normalized report source")
    source = execution_root / Path(*source_rel.parts)
    original = source.read_bytes()
    source_key = source.resolve(strict=True).relative_to(execution_root.resolve()).as_posix()
    captured_report = capture_rows.get(source_key)
    if captured_report is None or captured_report["sha256"] != _sha(original):
        raise ReleaseError(f"normalized report changed after capture: {source}")
    normalized = _report_identity(report, original, fixture)
    raw_mappings = []
    for row in normalized["results"]:
        raw_relative = _relative(row.get("raw_output"), "raw_output")
        raw_path = execution_root / Path(*raw_relative.parts)
        if raw_path.is_symlink():
            raise ReleaseError(f"raw_output is a symlink: {raw_path}")
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
    report_path = PurePosixPath(report["path"])
    staged_rel = NORMAL_ROOT / "attempts" / attempt_id / report_path.relative_to(NORMAL_ROOT)
    destination = repo_root / Path(*staged_rel.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = _json_bytes(normalized)
    with destination.open("xb") as target:
        target.write(staged)
    return {
        "source_path": report["source_path"],
        "staged_path": staged_rel.as_posix(),
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
    if plan.get("execution_authorized") is not True:
        raise ReleaseError("plan execution_authorized is not true")
    group_entry = next((item for item in validated["groups"] if item["id"] == group_id), None)
    if group_entry is None:
        raise ReleaseError(f"unknown group: {group_id}")
    qualification = _require_group_qualification(validated, group_id)
    group = next(item for item in plan["groups"] if item["id"] == group_id)
    reports = group_entry["reports"]
    with _exclusive_lock():
        plan_commit = _assert_contract_snapshot(validated)
        _assert_source_snapshot(
            repo_root, plan["source_commit"], plan["runner_source_sha256"], validated["source_inputs"]
        )
        population_binding = plan["population"]
        population_path = _relative(population_binding["path"], "population path")
        _source_file(repo_root, plan["source_commit"], population_path.as_posix(), population_binding["sha256"])
        for source_input in validated["source_inputs"]:
            _source_file(repo_root, plan["source_commit"], source_input["path"], source_input["sha256"])
        for tool_name, binding in validated["tools"].items():
            _check_tool_file(binding, tool_name)
        reservation = plan["resource_reservation"]
        if (reservation.get("exclusive_analyzer_slot") is not True or
                reservation.get("expires_at_unix_seconds", 0) <= time.time()):
            raise ReleaseError("fresh exclusive analyzer reservation is required")
        _check_resources(repo_root, plan["resource_budget"]["minimum_launch_free_gib"] * 1024**3)
        series = plan["execution_series"]
        attempt, execution_root, cache_root, ledger, attempt_id = _assert_fresh(
            repo_root, group, reports, series
        )
        attempt.mkdir(parents=True)
        start = _timestamp()
        cache_root.parent.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir()
        env = _child_environment(group, execution_root, attempt, cache_root)
        output_roots = [execution_root / Path(*_relative(value, "output root").parts)
                         for value in group["output_roots"]]
        receipt = {
            "schema_version": 1,
            "release": RELEASE,
            "execution_series": series,
            "group_id": group_id,
            "attempt_id": attempt_id,
            "status": "started",
            "start_utc": start,
            "end_utc": None,
            "source_commit": plan["source_commit"],
            "plan_commit": plan_commit,
            "contract_sha256": validated["bytes_sha256"],
            "runner_source_sha256": plan["runner_source_sha256"],
            "fixture_revision": validated["fixture_revision"],
            "population": plan["population"],
            "tool": group["tool"],
            "tool_binding": validated["tools"][group["tool"]],
            "identity_components": [
                _component_identity(alias, validated["tools"][alias])
                for alias in group_entry["identity_components"]
            ],
            "swift_plan": group_entry.get("swift_plan"),
            "joern_plan": group_entry.get("joern_plan"),
            "qualification": qualification,
            "source_inputs": validated["source_inputs"],
            "cache_root": str(cache_root),
            "argv": list(group["argv"]),
            "environment": env,
            "execution_root": str(execution_root),
            "output_roots": [path.relative_to(execution_root).as_posix() for path in output_roots],
            "case_ids": list(group["case_ids"]),
            "deadline_seconds": group["deadline_seconds"],
            "started_receipt": "started.json",
        }
        (attempt / "started.json").write_bytes(_json_bytes(receipt))
        row = dict(receipt)
        try:
            _materialize_source(
                repo_root, plan["source_commit"], execution_root,
                [item["path"] for item in validated["source_inputs"]],
            )
            if any(Path(value).name == "run-swift-common-v092.py" for value in group["argv"]):
                row["snapshot_git_head"] = _register_source_snapshot(
                    repo_root, plan["source_commit"], execution_root,
                )
            Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
            Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
            stdout = attempt / "stdout.txt"
            stderr = attempt / "stderr.txt"
            exit_code, timed_out, duration, capacity_loss = _run_process(
                group["argv"], execution_root, env, stdout, stderr, group["deadline_seconds"],
                retained_paths=[repo_root / "reports/releases/v0.9.2", *output_roots],
                retention_limit=plan["resource_budget"]["proposed_total_retention_ceiling_gib"] * 1024**3,
                scratch_paths=[Path(env["TMPDIR"]), cache_root],
                scratch_limit=plan["resource_budget"]["scratch_gib"] * 1024**3,
            )
            row.update({
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": duration,
                "capacity_loss": capacity_loss,
                "stdout": _file_receipt(stdout, "stdout.txt"),
                "stderr": _file_receipt(stderr, "stderr.txt"),
            })
            _assert_source_snapshot(
                repo_root, plan["source_commit"], plan["runner_source_sha256"], validated["source_inputs"]
            )
            for tool_name, binding in validated["tools"].items():
                _check_tool_file(binding, tool_name)
            capture_root = attempt / "capture"
            capture_rows = []
            for output_root in output_roots:
                capture_rows.extend(_copy_tree(output_root, execution_root, execution_root, capture_root))
            row["captured_files"] = sorted(capture_rows, key=lambda item: item["execution_relative"])
            capture_by_relative = {item["execution_relative"]: item for item in capture_rows}
            capacity_loss = capacity_loss or _capacity_loss(
                repo_root, [repo_root / "reports/releases/v0.9.2", *output_roots],
                plan["resource_budget"]["proposed_total_retention_ceiling_gib"] * 1024**3,
                [Path(env["TMPDIR"]), cache_root], plan["resource_budget"]["scratch_gib"] * 1024**3,
            )
            row["capacity_loss"] = capacity_loss
            if exit_code == 0 and not timed_out and capacity_loss is None:
                row["reports"] = [
                    _stage_report(repo_root, attempt, execution_root, attempt_id, report,
                                  capture_by_relative,
                                  output_roots,
                                  validated["fixture_revision"])
                    for report in reports
                ]
            else:
                row["reports"] = []
            row["status"] = ("capacity-lost" if capacity_loss else
                             "timed-out" if timed_out else ("completed" if exit_code == 0 else "failed"))
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
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--group")
    args = parser.parse_args(argv)
    validated = validate_plan(args.contract)
    groups = _selected(validated, args.group)
    if not args.execute:
        print(json.dumps({
            "mode": "plan",
            "release": RELEASE,
            "source_commit": validated["plan"]["source_commit"],
            "groups": groups,
            "group_count": len(groups),
            "execution_authorized": validated["plan"]["execution_authorized"],
        }, indent=2))
        return 0
    if validated["plan"].get("execution_authorized") is not True:
        raise ReleaseError("plan execution_authorized is not true")
    if args.group is None:
        unqualified = []
        for group_id in groups:
            try:
                _require_group_qualification(validated, group_id)
            except ReleaseError:
                unqualified.append(group_id)
        if unqualified:
            raise ReleaseError(
                "full-matrix dispatch requires eligible qualification coverage for every group; "
                f"unqualified group examples: {', '.join(unqualified[:5])}"
            )
    else:
        _require_group_qualification(validated, args.group)
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
