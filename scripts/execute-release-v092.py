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
import importlib.util
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
V1_CONTRACT_PATH = PurePosixPath("reports/releases/v0.9.2/execution-v1/contract.json")
V2_CONTRACT_PATH = PurePosixPath("reports/releases/v0.9.2/execution-v2/contract.json")
V3_CONTRACT_PATH = PurePosixPath("reports/releases/v0.9.2/execution-v3/contract.json")
ARCHIVED_FAILED_CONTRACT_PATH = PurePosixPath(
    "reports/releases/v0.9.2/acquisition/failed-contract-01.json"
)
ARCHIVED_SCOPED_CONTRACT_02_PATH = PurePosixPath(
    "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json"
)
SCOPED_RECOVERY_MANIFEST_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest.json"
)
HARNESS_BUILD_04_ROOT = PurePosixPath("reports/releases/v0.9.2/acquisition/harness-build-04")
HARNESS_V3_PATH = PurePosixPath("execution-state/v092/tools/harness-v3/dataflowbench")
C2_CONTRACT_SHA256 = "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422"
C2_SOURCE_COMMIT = "21b76b747b72363aad4bbbc358fc2ae9aee24f1c"
C2_PLAN_COMMIT = "a180c302b56f2c18a1fdfbbd1bc14489151fc54e"
SCOPED_RECOVERY_PRESERVED_EVIDENCE_COMMIT = "00207c228a55b4c1bd6373d9ff1358c0f2654393"
SCOPED_RECOVERY_PRESERVED_EVIDENCE_BLOBS = {
    "reports/releases/v0.9.2/qualification/source-snapshot-preflight-03/preflight.log":
        "66b573e967c0bdc67617b6b6d13eb6d04951a1c9",
    "reports/releases/v0.9.2/qualification/source-snapshot-preflight-03/receipt.json":
        "63f19ce9df8d8bc0336e6c2e7a634a7d26e0720f",
    "reports/releases/v0.9.2/qualification/source-snapshot-preflight-03/retry-01/preflight.log":
        "466b7cf81381e87f045a4d223d44636b4e864301",
    "reports/releases/v0.9.2/qualification/source-snapshot-preflight-03/retry-01/receipt.json":
        "841cb2e058d0c2381a8fdca21f9662cbc224357f",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/diagnosis.json":
        "ca13e48a15e8063472e021f6d53344bc66f407e0",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/diagnosis-02.md":
        "42a8a04ee1a45fac4facef19659ca08a2e731212",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/fix-02.patch":
        "895739f26024d9d52d39436adf534dc68c8e9632",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/fix.patch":
        "29c02a65843da190cd821d3f4a5886ba935ec174",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/patch-manifest-02.json":
        "47940a65b8aeea46b156d3c6d64200db04bdf472",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/patch-manifest.json":
        "ffd3ba6f5e281a46250c399caec394153c3bc282",
    "reports/releases/v0.9.2/validation/codeql-modeling-stamp-failure-01/repair-proposal/proposal.json":
        "3554b95fd399ce24eee7dc9db3837e6593c64892",
}
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


def _scoped_recovery_module():
    module_path = Path(__file__).with_name("v092_scoped_recovery.py")
    spec = importlib.util.spec_from_file_location("v092_scoped_recovery_packet", module_path)
    if spec is None or spec.loader is None:
        raise ReleaseError(f"cannot load scoped recovery validator: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _require_ancestor(root: Path, ancestor: str, descendant: str, description: str) -> None:
    if not COMMIT.fullmatch(ancestor) or not COMMIT.fullmatch(descendant):
        raise ReleaseError(f"{description} must use exact Git commits")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError(f"{description} is not an ancestor") from exc


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
        committed_extractor_provenance = (
            relative.as_posix()
            == "execution-state/v092/swift-source/patch-application/applied-patch.json"
        )
        if not committed_extractor_provenance and not any(relative.parts[:len(prefix.parts)] == prefix.parts for prefix in prefixes):
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


def _assert_successor_contract_equivalent(old_plan: dict, current_plan: dict) -> None:
    """Restrict v2 to the reviewed runner fix and exact same matrix contract."""
    old_tools = old_plan.get("tools")
    current_tools = current_plan.get("tools")
    if not isinstance(old_tools, dict) or not isinstance(current_tools, dict):
        raise ReleaseError("prior-failure contract has malformed tool bindings")
    if set(old_tools) != set(current_tools) or "runner" not in old_tools:
        raise ReleaseError("successor contract changed the bound tool alias set")
    old_runner = old_tools["runner"]
    current_runner = current_tools["runner"]
    if not isinstance(old_runner, dict) or not isinstance(current_runner, dict):
        raise ReleaseError("successor contract has malformed runner bindings")
    if (old_runner.get("path") == current_runner.get("path") or
            old_runner.get("sha256") == current_runner.get("sha256")):
        raise ReleaseError("successor contract must bind a fresh, separately retained runner binary")
    if ({key: value for key, value in old_runner.items() if key not in ("path", "sha256")} !=
            {key: value for key, value in current_runner.items() if key not in ("path", "sha256")}):
        raise ReleaseError("successor contract changed runner identity metadata beyond its fresh path and digest")
    if ({key: value for key, value in old_tools.items() if key != "runner"} !=
            {key: value for key, value in current_tools.items() if key != "runner"}):
        raise ReleaseError("successor contract changed a pinned analyzer or runtime binding")

    old_runner_path = old_runner.get("path")
    current_runner_path = current_runner.get("path")
    if not isinstance(old_runner_path, str) or not isinstance(current_runner_path, str):
        raise ReleaseError("successor contract runner paths are malformed")
    old_groups = old_plan.get("groups")
    current_groups = current_plan.get("groups")
    if (not isinstance(old_groups, list) or not isinstance(current_groups, list) or
            len(old_groups) != 84 or len(current_groups) != 84):
        raise ReleaseError("successor contract must preserve all 84 groups")
    old_by_id = {item.get("id"): item for item in old_groups if isinstance(item, dict)}
    current_by_id = {item.get("id"): item for item in current_groups if isinstance(item, dict)}
    if set(old_by_id) != set(current_by_id) or len(old_by_id) != 84:
        raise ReleaseError("successor contract changed group membership")
    wrapper_groups = {"codeql-swift-common108", "joern-swift-common108"}
    for group_id, old_group in old_by_id.items():
        current_group = current_by_id[group_id]
        old_argv = old_group.get("argv")
        current_argv = current_group.get("argv")
        if not isinstance(old_argv, list) or not isinstance(current_argv, list):
            raise ReleaseError(f"{group_id}: successor command is malformed")
        occurrences = sum(item == old_runner_path for item in old_argv)
        if group_id in wrapper_groups:
            if occurrences != 0:
                raise ReleaseError(f"{group_id}: legacy wrapper unexpectedly uses the replaced runner path")
            expected_argv = list(old_argv)
        else:
            if occurrences != 1:
                raise ReleaseError(f"{group_id}: successor must replace exactly one runner path")
            expected_argv = [current_runner_path if item == old_runner_path else item
                             for item in old_argv]
        if current_argv != expected_argv:
            raise ReleaseError(f"{group_id}: successor changed arguments beyond the runner path")
        old_without_argv = {key: value for key, value in old_group.items() if key != "argv"}
        current_without_argv = {key: value for key, value in current_group.items() if key != "argv"}
        if old_without_argv != current_without_argv:
            raise ReleaseError(f"{group_id}: successor changed group membership, environment, or budget")

    old_inputs = old_plan.get("source_inputs", [])
    current_inputs = current_plan.get("source_inputs", [])
    if not isinstance(old_inputs, list) or not isinstance(current_inputs, list):
        raise ReleaseError("successor contract source input lists are malformed")
    current_by_path = {
        item.get("path"): item.get("sha256") for item in current_inputs if isinstance(item, dict)
    }
    if any(not isinstance(item, dict) or current_by_path.get(item.get("path")) != item.get("sha256")
           for item in old_inputs):
        raise ReleaseError("successor contract does not preserve every prior source-input digest")

    old_replacements = old_plan.get("path_replacements")
    current_replacements = current_plan.get("path_replacements")
    if not isinstance(old_replacements, dict) or not isinstance(current_replacements, dict):
        raise ReleaseError("successor contract path replacement maps are malformed")
    if sum(value == old_runner_path for value in old_replacements.values()) != 1:
        raise ReleaseError("prior contract must bind the runner at exactly one replacement path")
    expected_replacements = {
        key: (current_runner_path if value == old_runner_path else value)
        for key, value in old_replacements.items()
    }
    if current_replacements != expected_replacements:
        raise ReleaseError("successor contract changed path replacements beyond the exact runner path")

    # The reservation and generated contract record are refreshed for the
    # successor commit. All other matrix, qualification, runtime, and budget
    # fields remain byte-for-byte equivalent as parsed JSON values.
    excluded = {
        "source_commit", "runner_source_sha256", "execution_authorized",
        "resource_reservation", "source_inputs", "tools", "groups",
        "generator", "prior_failed_contracts", "qualifications", "path_replacements",
    }
    old_rest = {key: value for key, value in old_plan.items() if key not in excluded}
    current_rest = {key: value for key, value in current_plan.items() if key not in excluded}
    if old_rest != current_rest:
        raise ReleaseError("successor contract changed a pinned population, qualification, or budget field")
    old_qualifications = old_plan.get("qualifications")
    current_qualifications = current_plan.get("qualifications")
    if not isinstance(old_qualifications, dict) or not isinstance(current_qualifications, dict):
        raise ReleaseError("successor contract qualifications are malformed")
    if current_plan.get("execution_authorized") is True:
        if current_qualifications != old_qualifications:
            raise ReleaseError("authorized successor changed the exact reviewed qualifications")
    else:
        pending = {
            name: {"status": "pending", "execution_eligible": False, "groups": []}
            for name in sorted(old_qualifications)
        }
        if current_qualifications != pending:
            raise ReleaseError("prospective successor qualifications must all remain pending and ineligible")
    old_generator = old_plan.get("generator")
    current_generator = current_plan.get("generator")
    if (not isinstance(old_generator, dict) or not isinstance(current_generator, dict) or
            {key: value for key, value in old_generator.items() if key != "source_sha256"} !=
            {key: value for key, value in current_generator.items() if key != "source_sha256"}):
        raise ReleaseError("successor contract changed generator provenance beyond its source digest")


def _read_prior_ledger(root: Path) -> list[tuple[dict, str]]:
    path = root / Path(*LEDGER_PATH.parts)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReleaseError(f"prior failure ledger is missing: {path}") from exc
    rows = []
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.endswith(b"\n") or line == b"\n" or line.endswith(b"\r\n"):
            raise ReleaseError(f"execution ledger line {number} is blank or non-canonical")
        try:
            row = json.loads(line[:-1])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ReleaseError(f"execution ledger line {number} is invalid JSON") from exc
        if not isinstance(row, dict):
            raise ReleaseError(f"execution ledger line {number} must be an object")
        canonical_line = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if line != canonical_line:
            raise ReleaseError(f"execution ledger line {number} is not canonical JSON")
        rows.append((row, _sha(line)))
    return rows


def _read_regular_receipt(path: Path, description: str, *, max_bytes: int = 1024 * 1024) -> tuple[dict, bytes]:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > max_bytes:
            raise ReleaseError(f"{description} is not a bounded regular file: {path}")
        data = path.read_bytes()
    except OSError as exc:
        raise ReleaseError(f"cannot read {description} {path}: {exc}") from exc
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"{description} is invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"{description} must be an object: {path}")
    return value, data


def _verify_preanalysis_bifrost_failure(
    old_validated: dict,
    old_plan_commit: str,
    attempt_id: str,
    ledger_line_sha256: str,
    ledger_rows: Sequence[tuple[dict, str]],
) -> dict:
    """Replay the one explicitly admitted pre-analysis version-gate failure."""
    group_id = "bifrost-c-kernel"
    expected_attempt_id = f"{group_id}-attempt-01-series-01"
    if attempt_id != expected_attempt_id:
        raise ReleaseError("prior failure scope admits only the first Bifrost C kernel attempt")
    matches = [(row, digest) for row, digest in ledger_rows if digest == ledger_line_sha256]
    if len(matches) != 1:
        raise ReleaseError("prior failure ledger-line digest is absent or ambiguous")
    row, actual_line_sha256 = matches[0]
    plan = old_validated["plan"]
    group = next((item for item in plan["groups"] if item.get("id") == group_id), None)
    normalized_group = next((item for item in old_validated["groups"] if item.get("id") == group_id), None)
    if group is None or normalized_group is None:
        raise ReleaseError("prior contract does not contain the admitted Bifrost C group")
    attempt = old_validated["repo_root"] / Path(*ATTEMPTS_ROOT.parts) / attempt_id
    execution = (old_validated["repo_root"] / Path(*EXECUTION_ROOT.parts) /
                 "series-01" / group_id / "attempt-01")
    cache = (old_validated["repo_root"] / Path(*CACHE_ROOT.parts) /
             "series-01" / group_id / "attempt-01")

    required = {
        "schema_version": 1,
        "release": RELEASE,
        "execution_series": 1,
        "group_id": group_id,
        "attempt_id": attempt_id,
        "status": "recorder-error",
        "source_commit": plan["source_commit"],
        "plan_commit": old_plan_commit,
        "contract_sha256": old_validated["bytes_sha256"],
        "runner_source_sha256": plan["runner_source_sha256"],
        "fixture_revision": old_validated["fixture_revision"],
        "population": plan["population"],
        "tool": "bifrost",
        "tool_binding": old_validated["tools"]["bifrost"],
        "identity_components": [
            _component_identity(alias, old_validated["tools"][alias])
            for alias in normalized_group["identity_components"]
        ],
        "qualification": old_validated["qualification"]["bifrost"],
        "source_inputs": old_validated["source_inputs"],
        "swift_plan": None,
        "joern_plan": None,
        "cache_root": str(cache),
        "argv": group["argv"],
        "environment": _child_environment(group, execution, attempt, cache),
        "execution_root": str(execution),
        "output_roots": group["output_roots"],
        "case_ids": group["case_ids"],
        "deadline_seconds": group["deadline_seconds"],
        "started_receipt": "started.json",
        "exit_code": 1,
        "timed_out": False,
        "capacity_loss": None,
        "captured_files": [],
        "failed_staging_artifacts": [],
        "reports": [],
        "recorder_error": (
            "ReleaseError: declared output root is missing or symlinked: "
            f"{execution / Path(*PurePosixPath(group['output_roots'][0]).parts)}"
        ),
    }
    for key, expected in required.items():
        if row.get(key) != expected:
            raise ReleaseError(f"prior Bifrost version-gate receipt differs from its contract: {key}")
    duration = row.get("duration_seconds")
    if (type(duration) not in (int, float) or not math.isfinite(duration) or
            duration < 0 or duration >= group["deadline_seconds"]):
        raise ReleaseError("prior Bifrost version-gate duration is invalid")
    ownership = row.get("process_ownership")
    if (not isinstance(ownership, dict) or
            set(ownership) != {"schema", "root_pid", "tracking_interval_seconds", "tracked_processes",
                               "signals_sent", "descendant_containment", "cleanup_status"} or
            ownership.get("schema") != "invocation-process-ownership/v1" or
            type(ownership.get("root_pid")) is not int or ownership["root_pid"] <= 0 or
            ownership.get("tracking_interval_seconds") != 2.0 or
            ownership.get("descendant_containment") != "unproven" or
            ownership.get("cleanup_status") != "tracked-processes-stopped" or
            ownership.get("signals_sent") != []):
        raise ReleaseError("prior Bifrost version-gate process cleanup is not terminal")
    tracked = ownership.get("tracked_processes")
    if (not isinstance(tracked, list) or len(tracked) != 1 or
            not isinstance(tracked[0], dict) or
            set(tracked[0]) != {"pid", "start_identity"} or
            tracked[0].get("pid") != ownership["root_pid"] or
            not isinstance(tracked[0].get("start_identity"), str) or
            not re.fullmatch(r"[0-9]+:[0-9]+", tracked[0]["start_identity"])):
        raise ReleaseError("prior Bifrost version-gate process ownership evidence is malformed")
    expected_row_keys = {
        "schema_version", "release", "execution_series", "group_id", "attempt_id", "status",
        "start_utc", "end_utc", "source_commit", "plan_commit", "contract_sha256",
        "runner_source_sha256", "fixture_revision", "population", "tool", "tool_binding",
        "identity_components", "swift_plan", "joern_plan", "qualification", "source_inputs",
        "cache_root", "argv", "environment", "execution_root", "output_roots", "case_ids",
        "deadline_seconds", "started_receipt", "exit_code", "timed_out", "duration_seconds",
        "capacity_loss", "stdout", "stderr", "captured_files", "failed_staging_artifacts",
        "reports", "recorder_error", "process_ownership",
    }
    if set(row) != expected_row_keys:
        raise ReleaseError("prior Bifrost version-gate receipt has unreviewed fields")
    try:
        start_time = _datetime.datetime.fromisoformat(row["start_utc"])
        end_time = _datetime.datetime.fromisoformat(row["end_utc"])
        if start_time.tzinfo is None or end_time.tzinfo is None or end_time < start_time:
            raise ValueError("invalid wall timestamps")
    except (KeyError, TypeError, ValueError) as exc:
        raise ReleaseError("prior Bifrost version-gate timestamps are invalid") from exc

    if old_validated["tools"]["bifrost"].get("version") != "0.13.1" or old_validated["tools"]["bifrost"].get("report_version") != "bifrost 0.13.1":
        raise ReleaseError("prior Bifrost version-gate witness is not the pinned 0.13.1 identity")
    stdout_expected = (
        b"validated 1108 cases\n"
        b"validated 6 real-project pin records\n"
        b"validated 219 real-project R2 frame candidates\n"
        b"validated 6 real-project R2 selections\n"
        b"validated 6 real-project R2 selected repositories\n"
        b"validated 6 real-project R2 pin records\n"
        b"validated 616 real-project R2 review-packet artifacts\n"
    )
    stderr_expected = (
        f'Error: the Bifrost binary at {old_validated["tools"]["bifrost"]["path"]} '
        'witnessed version "bifrost 0.13.1\\nbuiltin-policy-catalog '
        'sha256=f9d3b4efcf20e0ca8e8a976d6524556f114f4a4ccab3f4b0cc761f0b9248d206", '
        'but profile v0.9.2 pins bifrost 0.13.1; refusing to publish a report for another release\n'
    ).encode()
    streams = {}
    for field, expected in (("stdout", stdout_expected), ("stderr", stderr_expected)):
        reference = row.get(field)
        if not isinstance(reference, dict) or reference.get("path") != f"{field}.txt":
            raise ReleaseError(f"prior Bifrost version-gate receipt lacks exact {field} binding")
        try:
            info = (attempt / (field + ".txt")).lstat()
            actual = (attempt / (field + ".txt")).read_bytes()
        except OSError as exc:
            raise ReleaseError(f"cannot read prior Bifrost {field}: {exc}") from exc
        if (not stat.S_ISREG(info.st_mode) or actual != expected or
                reference.get("bytes") != len(actual) or reference.get("sha256") != _sha(actual)):
            raise ReleaseError(f"prior Bifrost {field} differs from the exact version-gate witness")
        streams[field] = {"sha256": _sha(actual), "bytes": len(actual)}

    started, started_raw = _read_regular_receipt(attempt / "started.json", "prior started receipt")
    if started.get("status") != "started" or started.get("end_utc") is not None:
        raise ReleaseError("prior started receipt has an invalid state")
    if any(row.get(key) != value for key, value in started.items()
           if key not in ("status", "end_utc")):
        raise ReleaseError("prior started receipt differs from its ledger completion")
    if started_raw != _json_bytes(started):
        raise ReleaseError("prior started receipt is not the exact canonical receipt file")
    completed, completed_raw = _read_regular_receipt(attempt / "completed.json", "prior completed receipt")
    if completed != row or completed_raw != _json_bytes(row):
        raise ReleaseError("prior completed receipt differs from its exact ledger row")

    # The ledger line digest binds the complete terminal row, including both
    # streams, while these file checks prove the referenced bytes still exist.
    actual_line = next((digest for candidate, digest in ledger_rows if candidate == row), None)
    if actual_line != actual_line_sha256:
        raise ReleaseError("prior ledger row changed during receipt replay")
    capture = attempt / "capture"
    if capture.exists() and (capture.is_symlink() or not capture.is_dir() or any(capture.iterdir())):
        raise ReleaseError("prior Bifrost attempt contains unrecorded analyzer capture output")
    staged = old_validated["repo_root"] / Path(*NORMAL_ROOT.parts) / "attempts" / attempt_id
    if staged.exists() and (staged.is_symlink() or not staged.is_dir() or any(staged.iterdir())):
        raise ReleaseError("prior Bifrost attempt contains unrecorded staged reports")
    report_path = execution / Path(*PurePosixPath(group["output_roots"][0]).parts)
    if report_path.exists() or report_path.is_symlink():
        raise ReleaseError("prior Bifrost version-gate attempt unexpectedly produced its report")
    raw_root = execution / Path(*PurePosixPath(group["output_roots"][1]).parts)
    if raw_root.exists() and (raw_root.is_symlink() or not raw_root.is_dir() or any(raw_root.iterdir())):
        raise ReleaseError("prior Bifrost version-gate attempt contains raw analyzer output")

    return {
        "attempt_id": attempt_id,
        "ledger_line_sha256": actual_line_sha256,
        "receipt_sha256": _sha(completed_raw),
        "receipt_bytes": len(completed_raw),
        "started_receipt_sha256": _sha(started_raw),
        "started_receipt_bytes": len(started_raw),
        "streams": streams,
        "start_utc": row["start_utc"],
    }


def _verify_preanalysis_failure_review(
    validated: dict,
    old_validated: dict,
    old_plan_commit: str,
    old_contract_sha256: str,
    attempt: dict,
) -> None:
    review_path = PurePosixPath(
        "reports/releases/v0.9.2/qualification/bifrost-preanalysis-version-gate-failure-review-01.json"
    )
    inputs = {item["path"]: item["sha256"] for item in validated["source_inputs"]}
    expected_sha = inputs.get(review_path.as_posix())
    if not isinstance(expected_sha, str):
        raise ReleaseError("successor source_inputs must bind the pre-analysis version-gate review")
    root = validated["repo_root"]
    path = root / Path(*review_path.parts)
    review, raw = _read_regular_receipt(path, "pre-analysis version-gate review")
    if _sha(raw) != expected_sha:
        raise ReleaseError("pre-analysis version-gate review differs from its source-input digest")
    if _git_show(root, validated["plan"]["source_commit"], review_path.as_posix()) != raw:
        raise ReleaseError("successor source commit does not contain the exact version-gate review")
    if (review.get("schema") != "v092-preanalysis-version-gate-failure-review/v1" or
            review.get("attempt_id") != attempt["attempt_id"] or
            review.get("status") != "recorder-error" or
            review.get("case_analysis_ran") is not False or
            review.get("ledger_line_sha256") != attempt["ledger_line_sha256"] or
            review.get("original_start_utc") != attempt["start_utc"]):
        raise ReleaseError("pre-analysis review does not replay the exact retained failure")
    contract_ref = review.get("prior_contract")
    expected_contract_ref = {
        "path": ARCHIVED_FAILED_CONTRACT_PATH.as_posix(),
        "sha256": old_contract_sha256,
        "plan_commit": old_plan_commit,
    }
    if contract_ref != expected_contract_ref:
        raise ReleaseError("pre-analysis review names a different prior contract")
    expected_files = {
        (ATTEMPTS_ROOT / attempt["attempt_id"] / "completed.json").as_posix():
            (attempt["receipt_sha256"], attempt["receipt_bytes"]),
        (ATTEMPTS_ROOT / attempt["attempt_id"] / "started.json").as_posix():
            (attempt["started_receipt_sha256"], attempt["started_receipt_bytes"]),
        (ATTEMPTS_ROOT / attempt["attempt_id"] / "stdout.txt").as_posix():
            (attempt["streams"]["stdout"]["sha256"], attempt["streams"]["stdout"]["bytes"]),
        (ATTEMPTS_ROOT / attempt["attempt_id"] / "stderr.txt").as_posix():
            (attempt["streams"]["stderr"]["sha256"], attempt["streams"]["stderr"]["bytes"]),
    }
    entries = review.get("files")
    if not isinstance(entries, list) or len(entries) != len(expected_files):
        raise ReleaseError("pre-analysis review must bind exactly the four retained receipt and stream files")
    found = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes"}:
            raise ReleaseError("pre-analysis review file entry has an unknown or missing field")
        file_path = entry["path"]
        if file_path in found:
            raise ReleaseError("pre-analysis review contains duplicate file entries")
        found[file_path] = (entry["sha256"], entry["bytes"])
    if found != expected_files:
        raise ReleaseError("pre-analysis review file digests differ from independently replayed bytes")
    constraints = review.get("constraints")
    expected_constraints = {
        "execution_series": old_validated["plan"]["execution_series"],
        "maximum_attempts_per_group": 2,
        "total_wall_budget_seconds": old_validated["total_wall_budget_seconds"],
        "wall_origin_must_be_preserved": True,
        "no_report_carry_forward": True,
        "prior_failure_counts_as_attempt": True,
    }
    if constraints != expected_constraints:
        raise ReleaseError("pre-analysis review does not preserve the original execution limits")


def _validate_prior_failed_contracts(
    validated: dict,
    historical_ledger_rows: Sequence[tuple[dict, str]] | None = None,
) -> dict[str, dict]:
    """Load and verify the immutable v1 failure admitted by the execution-v2 contract."""
    plan = validated["plan"]
    references = plan.get("prior_failed_contracts")
    if not isinstance(references, list) or len(references) != 1:
        raise ReleaseError("execution-v2 must bind exactly one prior failed contract")
    reference = references[0]
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256", "plan_commit", "attempts"}:
        raise ReleaseError("prior_failed_contracts entry has an unknown or missing field")
    if reference.get("path") != ARCHIVED_FAILED_CONTRACT_PATH.as_posix():
        raise ReleaseError("successor contract may reference only the registered failed-contract-01 archive")
    archive_sha = _bound_sha(reference.get("sha256"), "prior_failed_contracts.sha256")
    plan_commit = reference.get("plan_commit")
    if not isinstance(plan_commit, str) or not COMMIT.fullmatch(plan_commit):
        raise ReleaseError("prior failed contract must bind its exact plan commit")
    attempts = reference.get("attempts")
    if (not isinstance(attempts, list) or len(attempts) != 1 or
            not isinstance(attempts[0], dict) or
            set(attempts[0]) != {"attempt_id", "ledger_line_sha256"}):
        raise ReleaseError("prior failed contract must bind exactly one attempt and ledger-line digest")
    attempt_ref = attempts[0]
    attempt_id = attempt_ref.get("attempt_id")
    if attempt_id != "bifrost-c-kernel-attempt-01-series-01":
        raise ReleaseError("successor contract admits only the recorded first Bifrost C kernel failure")
    line_sha = _bound_sha(attempt_ref.get("ledger_line_sha256"), "prior failed ledger line SHA-256")

    root = validated["repo_root"]
    archive_path = root / Path(*ARCHIVED_FAILED_CONTRACT_PATH.parts)
    try:
        info = archive_path.lstat()
        archive_bytes = archive_path.read_bytes()
    except OSError as exc:
        raise ReleaseError(f"cannot read archived v1 contract: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or _sha(archive_bytes) != archive_sha:
        raise ReleaseError("archived v1 contract is not the exact digest-bound regular file")
    canonical_v1 = V1_CONTRACT_PATH.as_posix()
    if _git_show(root, plan_commit, canonical_v1) != archive_bytes:
        raise ReleaseError("archived v1 contract differs from its committed canonical bytes")
    _require_ancestor(root, plan_commit, plan["source_commit"],
                      "prior execution-plan commit to successor source commit")
    if _git_show(root, plan["source_commit"], ARCHIVED_FAILED_CONTRACT_PATH.as_posix()) != archive_bytes:
        raise ReleaseError("successor source commit does not contain the exact archived v1 contract")

    old_validated = validate_plan(
        archive_path,
        repo_root=root,
        _archived=True,
        _historical_ledger_rows=historical_ledger_rows,
    )
    old_plan = old_validated["plan"]
    if old_plan.get("prior_failed_contracts"):
        raise ReleaseError("archived prior contract may not itself have predecessors")
    _require_ancestor(root, old_plan["source_commit"], plan_commit,
                      "prior source commit to prior execution-plan commit")
    _require_ancestor(root, old_plan["source_commit"], plan["source_commit"],
                      "prior source commit to successor source commit")
    runner_source = _git_show(root, old_plan["source_commit"], "scripts/execute-release-v092.py")
    if _sha(runner_source) != old_plan["runner_source_sha256"]:
        raise ReleaseError("archived contract runner source differs from its own source commit")
    for source_input in old_validated["source_inputs"]:
        if _sha(_git_show(root, old_plan["source_commit"], source_input["path"])) != source_input["sha256"]:
            raise ReleaseError(f"prior source input differs at its own source commit: {source_input['path']}")
    _assert_successor_contract_equivalent(old_plan, plan)
    current_inputs = {item["path"]: item["sha256"] for item in validated["source_inputs"]}
    if any(current_inputs.get(item["path"]) != item["sha256"]
           for item in old_validated["source_inputs"]):
        raise ReleaseError("successor contract does not preserve all prior qualification and acquisition inputs")

    ledger_rows = (list(historical_ledger_rows) if historical_ledger_rows is not None
                   else _read_prior_ledger(root))
    old_digest = old_validated["bytes_sha256"]
    if not ledger_rows or ledger_rows[0][1] != line_sha:
        raise ReleaseError("admitted pre-analysis version-gate failure is not the first ledger line")
    old_rows = [(row, digest) for row, digest in ledger_rows
                if row.get("contract_sha256") == old_digest]
    if len(old_rows) != 1 or old_rows[0][1] != line_sha:
        raise ReleaseError("prior contract ledger history differs from its one declared failed attempt")
    foreign_series_rows = [row for row, _digest in ledger_rows
                           if row.get("execution_series") == plan["execution_series"] and
                           row.get("contract_sha256") not in (old_digest, validated["bytes_sha256"])]
    if foreign_series_rows:
        raise ReleaseError("execution series contains an unregistered contract revision")
    # The current revision may be resumed after new attempts. Every retained
    # prior-revision row is forbidden except the one above; its own checker
    # will validate all current-revision attempts against this contract.
    replayed = _verify_preanalysis_bifrost_failure(
        old_validated, plan_commit, attempt_id, line_sha, ledger_rows,
    )
    _verify_preanalysis_failure_review(
        validated, old_validated, plan_commit, old_digest, replayed,
    )
    return {
        old_digest: {
            "validated": old_validated,
            "plan_commit": plan_commit,
            "attempts": [replayed],
        }
    }


def _retained_attempt_paths(packet: dict) -> set[str]:
    """Return only paths named by the sealed 27-row historical prefix."""
    root = Path(packet.get("repo_root", ".")).resolve()
    paths: set[str] = set()
    manifest_by_line = {
        item["ledger_line_sha256"]: item
        for item in packet["manifest"]["retained_completed"] + packet["manifest"]["retained_failures"]
    }
    for row, line_sha in packet["prefix_rows"]:
        attempt_id = row["attempt_id"]
        item = manifest_by_line[line_sha]
        for key in ("started_receipt", "completed_receipt"):
            paths.add(item[key]["path"])
        for key in ("stdout", "stderr"):
            paths.add((ATTEMPTS_ROOT / attempt_id / f"{key}.txt").as_posix())
        for captured in row.get("captured_files", []):
            capture_path = Path(captured["capture_path"])
            absolute = (capture_path if capture_path.is_absolute() else root / capture_path).resolve()
            if not _under(absolute, root):
                raise ReleaseError(f"retained capture escapes the repository: {captured.get('capture_path')}")
            paths.add(absolute.relative_to(root).as_posix())
        for report in row.get("reports", []):
            for key in ("original_path", "staged_path"):
                value = report.get(key)
                if value:
                    paths.add(_relative(value, f"retained report {key}").as_posix())
            for mapping in report.get("raw_output_mappings", []):
                value = mapping.get("captured_path")
                if value:
                    paths.add(_relative(value, "retained raw capture path").as_posix())
    return paths


def _retained_normal_report_paths(packet: dict) -> set[str]:
    paths: set[str] = set()
    for row, _line_sha in packet["prefix_rows"]:
        for report in row.get("reports", []):
            value = report.get("staged_path")
            if value:
                paths.add(_relative(value, "retained staged report path").as_posix())
    return paths


def _build04_source_inputs() -> dict[str, str]:
    return {
        (HARNESS_BUILD_04_ROOT / name).as_posix(): ""
        for name in (
            "receipt.json", "prebuild-inputs.json", "postbuild-inputs.json",
            "build.log", "smoke-validate.log", "smoke-validate-reports.log",
        )
    }


def _build04_path(root: Path, value: object, description: str, expected: PurePosixPath) -> Path:
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ReleaseError(f"{description} must bind an absolute retained path")
    selected = Path(value).resolve()
    expected_path = (root / Path(*expected.parts)).resolve()
    if selected != expected_path:
        raise ReleaseError(f"{description} must name {expected.as_posix()}")
    return selected


def _validate_build04_input_snapshots(
    receipt: dict,
    prebuild: dict,
    postbuild: dict,
    build_commit: str,
) -> list[dict]:
    """Replay the build's recorded pre/post compile-input closure."""
    compile_inputs = receipt.get("compile_inputs")
    if (prebuild.get("schema") != "harness-release-build-preflight/v1" or
            postbuild.get("schema") != "harness-release-build-postflight/v1" or
            prebuild.get("source_commit") != build_commit or
            postbuild.get("source_commit") != build_commit or
            receipt.get("source_inputs_clean_and_unchanged") is not True or
            postbuild.get("compile_inputs_unchanged_from_prebuild") is not True or
            prebuild.get("compile_inputs") != compile_inputs or
            postbuild.get("compile_inputs") != compile_inputs or
            not isinstance(compile_inputs, list) or not compile_inputs):
        raise ReleaseError("harness build-04 compile-input snapshots do not replay")
    return compile_inputs


def _validate_harness_build_04(validated: dict, c2_source: str) -> dict:
    """Replay the exact corrected harness build and its smoke logs."""
    root = validated["repo_root"]
    build_root = root / Path(*HARNESS_BUILD_04_ROOT.parts)
    source_input_map = {item["path"]: item["sha256"] for item in validated["source_inputs"]}
    expected_inputs = _build04_source_inputs()
    loaded: dict[str, bytes] = {}
    for relative, _unused in expected_inputs.items():
        path = root / Path(*PurePosixPath(relative).parts)
        try:
            info = path.lstat()
            raw = path.read_bytes()
        except OSError as exc:
            raise ReleaseError(f"cannot read the C3 harness build proof: {path}") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ReleaseError(f"C3 harness build proof is not a regular file: {path}")
        digest = _sha(raw)
        if source_input_map.get(relative) != digest:
            raise ReleaseError(f"C3 source_inputs do not bind the exact harness build proof: {relative}")
        expected_inputs[relative] = digest
        loaded[relative] = raw

    receipt_path = root / Path(*HARNESS_BUILD_04_ROOT.parts) / "receipt.json"
    receipt, _receipt_raw = _read_json(receipt_path, "harness build-04 receipt")
    if (receipt.get("schema") != "harness-release-build-receipt/v1" or
            receipt.get("status") != "built-and-smoke-validated" or
            receipt.get("build_exit_code") != 0 or
            receipt.get("source_inputs_clean_and_unchanged") is not True):
        raise ReleaseError("harness build-04 receipt is not a complete successful build")
    build_commit = receipt.get("source_commit")
    if not isinstance(build_commit, str) or not COMMIT.fullmatch(build_commit):
        raise ReleaseError("harness build-04 receipt lacks its exact source commit")
    _require_ancestor(root, c2_source, build_commit, "C2 source to corrected harness build source")
    _require_ancestor(root, build_commit, validated["plan"]["source_commit"],
                      "corrected harness build source to C3 source")

    binary = receipt.get("binary")
    if not isinstance(binary, dict):
        raise ReleaseError("harness build-04 receipt lacks the corrected binary binding")
    copy_path = _build04_path(root, binary.get("copy_path"), "harness build-04 binary", HARNESS_V3_PATH)
    runner = validated["tools"].get("runner")
    binary_sha = _bound_sha(binary.get("sha256"), "harness build-04 binary SHA-256")
    if (not isinstance(runner, dict) or runner.get("path") != str(copy_path) or
            runner.get("sha256") != binary_sha):
        raise ReleaseError("C3 runner binding differs from the exact retained build-04 binary")
    try:
        binary_info = copy_path.lstat()
        binary_bytes = copy_path.read_bytes()
    except OSError as exc:
        raise ReleaseError("cannot read the corrected harness binary") from exc
    if (not stat.S_ISREG(binary_info.st_mode) or len(binary_bytes) != binary.get("bytes") or
            _sha(binary_bytes) != binary_sha):
        raise ReleaseError("corrected harness binary bytes differ from build-04 receipt")

    preflight_ref = receipt.get("compile_input_receipts", {}).get("prebuild")
    postflight_ref = receipt.get("compile_input_receipts", {}).get("postbuild")
    preflight_path = HARNESS_BUILD_04_ROOT / "prebuild-inputs.json"
    postflight_path = HARNESS_BUILD_04_ROOT / "postbuild-inputs.json"
    for ref, relative, label in (
        (preflight_ref, preflight_path, "prebuild inputs"),
        (postflight_ref, postflight_path, "postbuild inputs"),
    ):
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            raise ReleaseError(f"harness build-04 receipt lacks exact {label} reference")
        path = _build04_path(root, ref["path"], label, relative)
        raw = path.read_bytes()
        if _sha(raw) != ref["sha256"]:
            raise ReleaseError(f"harness build-04 {label} digest differs from receipt")
    prebuild, _ = _read_json(root / Path(*preflight_path.parts), "harness build-04 prebuild inputs")
    postbuild, _ = _read_json(root / Path(*postflight_path.parts), "harness build-04 postbuild inputs")
    compile_inputs = _validate_build04_input_snapshots(
        receipt, prebuild, postbuild, build_commit,
    )
    for item in compile_inputs:
        if (not isinstance(item, dict) or item.get("worktree_status") != "clean" or
                not isinstance(item.get("path"), str)):
            raise ReleaseError("harness build-04 contains malformed or dirty compile inputs")
        relative = _relative(item["path"], "harness compile input")
        if not relative.parts or relative.is_absolute():
            raise ReleaseError("harness compile input path is unsafe")
        git_object = _git_blob(root, build_commit, relative.as_posix())
        if git_object != item.get("git_object"):
            raise ReleaseError(f"harness build-04 Git object differs for {relative.as_posix()}")
        current_git_object = _git_blob(root, validated["plan"]["source_commit"], relative.as_posix())
        if current_git_object != git_object:
            raise ReleaseError(f"C3 source changed a compile input after the corrected harness build: {relative.as_posix()}")
        expected_file_sha = item.get("sha256")
        if expected_file_sha is not None:
            if _sha(_git_show(root, build_commit, relative.as_posix())) != expected_file_sha:
                raise ReleaseError(f"harness build-04 file digest differs for {relative.as_posix()}")

    build_log = receipt.get("build_log")
    if not isinstance(build_log, dict) or set(build_log) != {"path", "sha256", "bytes"}:
        raise ReleaseError("harness build-04 receipt lacks the exact build log")
    build_log_path = _build04_path(root, build_log["path"], "harness build log", HARNESS_BUILD_04_ROOT / "build.log")
    if len(build_log_path.read_bytes()) != build_log["bytes"] or _sha(build_log_path.read_bytes()) != build_log["sha256"]:
        raise ReleaseError("harness build log differs from its receipt")
    smoke_checks = receipt.get("smoke_checks")
    expected_smokes = {
        "validate": HARNESS_BUILD_04_ROOT / "smoke-validate.log",
        "validate-reports": HARNESS_BUILD_04_ROOT / "smoke-validate-reports.log",
    }
    if not isinstance(smoke_checks, list) or len(smoke_checks) != 2:
        raise ReleaseError("harness build-04 must include both smoke validations")
    found_smokes = set()
    for smoke in smoke_checks:
        if not isinstance(smoke, dict) or smoke.get("exit_code") != 0:
            raise ReleaseError("harness build-04 smoke validation did not pass")
        command = smoke.get("command")
        log = smoke.get("log")
        if (not isinstance(command, list) or len(command) != 2 or
                command[0] != str(copy_path) or command[1] not in expected_smokes or
                not isinstance(log, dict) or set(log) != {"path", "sha256", "bytes"}):
            raise ReleaseError("harness build-04 smoke validation command is malformed")
        smoke_name = command[1]
        if smoke_name in found_smokes:
            raise ReleaseError("harness build-04 repeats a smoke validation")
        found_smokes.add(smoke_name)
        smoke_path = _build04_path(root, log["path"], "harness smoke log", expected_smokes[smoke_name])
        raw = smoke_path.read_bytes()
        if len(raw) != log["bytes"] or _sha(raw) != log["sha256"]:
            raise ReleaseError(f"harness build-04 {smoke_name} log differs from its receipt")
    if found_smokes != set(expected_smokes):
        raise ReleaseError("harness build-04 omitted one of the exact smoke validations")

    return {"source_inputs": expected_inputs, "source_commit": build_commit, "binary_sha256": binary_sha}


def _git_changed_paths(root: Path, old_commit: str, new_commit: str) -> set[str]:
    try:
        raw = subprocess.check_output(
            ["git", "diff", "--name-only", "-z", old_commit, new_commit, "--"],
            cwd=root,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("cannot inspect the scoped-recovery source diff") from exc
    try:
        return {item.decode("utf-8") for item in raw.split(b"\0") if item}
    except UnicodeDecodeError as exc:
        raise ReleaseError("scoped-recovery source diff contains a non-UTF-8 path") from exc


def _git_blob(root: Path, commit: str, relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{relative}"],
            cwd=root,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError(f"cannot resolve historical source blob: {relative}") from exc


def _validate_scoped_preserved_evidence(root: Path, source_commit: str) -> None:
    """Keep prior C2 approval and source-preflight artifacts byte-identical."""
    _require_ancestor(
        root,
        SCOPED_RECOVERY_PRESERVED_EVIDENCE_COMMIT,
        source_commit,
        "preserved C2 approval and source-preflight evidence to C3 source",
    )
    for relative, expected_blob in SCOPED_RECOVERY_PRESERVED_EVIDENCE_BLOBS.items():
        if (_git_blob(root, SCOPED_RECOVERY_PRESERVED_EVIDENCE_COMMIT, relative) != expected_blob or
                _git_blob(root, source_commit, relative) != expected_blob):
            raise ReleaseError(f"C3 changed preserved historical approval/preflight evidence: {relative}")


def _validate_scoped_successor_equivalent(
    old_validated: dict,
    current_validated: dict,
    packet: dict,
) -> None:
    """Require C3 to preserve C2's matrix/runtime and carry only the reviewed fix."""
    old = old_validated["plan"]
    current = current_validated["plan"]
    root = current_validated["repo_root"]
    old_source = old.get("source_commit")
    new_source = current.get("source_commit")
    if old_source != C2_SOURCE_COMMIT or not isinstance(new_source, str) or not COMMIT.fullmatch(new_source):
        raise ReleaseError("C3 source must descend from the exact C2 source commit")
    _require_ancestor(root, old_source, new_source, "C2 source to C3 source")

    old_tools = old.get("tools")
    current_tools = current.get("tools")
    if not isinstance(old_tools, dict) or not isinstance(current_tools, dict) or set(old_tools) != set(current_tools):
        raise ReleaseError("C3 changed the analyzer tool alias set")
    old_runner = old_tools.get("runner")
    current_runner = current_tools.get("runner")
    if not isinstance(old_runner, dict) or not isinstance(current_runner, dict):
        raise ReleaseError("C2/C3 must bind the exact harness runner")
    old_runner_path = old_runner.get("path")
    current_runner_path = current_runner.get("path")
    if (not isinstance(old_runner_path, str) or not isinstance(current_runner_path, str) or
            not Path(old_runner_path).is_absolute() or not Path(current_runner_path).is_absolute()):
        raise ReleaseError("C2/C3 runner paths must be absolute")
    _bound_sha(old_runner.get("sha256"), "C2 runner SHA-256")
    _bound_sha(current_runner.get("sha256"), "C3 runner SHA-256")
    if old_runner["sha256"] == current_runner["sha256"]:
        raise ReleaseError("C3 must bind the corrected harness build, not reuse the C2 binary")
    if {key: value for key, value in old_runner.items() if key not in ("path", "sha256")} != {
            key: value for key, value in current_runner.items() if key not in ("path", "sha256")}:
        raise ReleaseError("C3 changed runner metadata beyond its exact path and binary digest")
    for name in old_tools:
        if name != "runner" and old_tools[name] != current_tools[name]:
            raise ReleaseError(f"C3 changed the pinned runtime or analyzer binding: {name}")

    old_groups = {group.get("id"): group for group in old.get("groups", []) if isinstance(group, dict)}
    current_groups = {group.get("id"): group for group in current.get("groups", []) if isinstance(group, dict)}
    if not old_groups or set(old_groups) != set(current_groups):
        raise ReleaseError("C3 changed execution group membership")
    for group_id, old_group in old_groups.items():
        current_group = current_groups[group_id]
        old_argv = old_group.get("argv")
        current_argv = current_group.get("argv")
        if not isinstance(old_argv, list) or not isinstance(current_argv, list):
            raise ReleaseError(f"{group_id}: C2/C3 command vectors are malformed")
        occurrences = sum(value == old_runner_path for value in old_argv)
        if occurrences > 1:
            raise ReleaseError(f"{group_id}: C2 command repeats the harness path")
        expected_argv = [current_runner_path if value == old_runner_path else value for value in old_argv]
        if current_argv != expected_argv:
            raise ReleaseError(f"{group_id}: C3 changed command arguments beyond the corrected runner path")
        old_rest = {key: value for key, value in old_group.items() if key != "argv"}
        current_rest = {key: value for key, value in current_group.items() if key != "argv"}
        if old_rest != current_rest:
            raise ReleaseError(f"{group_id}: C3 changed its reports, environment, membership, or budget")

    old_replacements = old.get("path_replacements")
    current_replacements = current.get("path_replacements")
    if not isinstance(old_replacements, dict) or not isinstance(current_replacements, dict):
        raise ReleaseError("C2/C3 path replacement maps are malformed")
    occurrences = sum(value == old_runner_path for value in old_replacements.values())
    if occurrences != 1:
        raise ReleaseError("C2 must map exactly one source runner path to its selected binary")
    expected_replacements = {
        key: (current_runner_path if value == old_runner_path else value)
        for key, value in old_replacements.items()
    }
    if current_replacements != expected_replacements:
        raise ReleaseError("C3 changed source path replacements beyond the corrected harness path")
    if old.get("group_path_replacements") != current.get("group_path_replacements"):
        raise ReleaseError("C3 changed a group-specific path replacement")

    old_inputs = old_validated["source_inputs"]
    current_inputs = current_validated["source_inputs"]
    old_by_path = {item["path"]: item["sha256"] for item in old_inputs}
    current_by_path = {item["path"]: item["sha256"] for item in current_inputs}
    if any(current_by_path.get(path) != digest for path, digest in old_by_path.items()):
        raise ReleaseError("C3 does not preserve every original C2 source-input digest")
    manifest = packet["manifest"]
    expected_new_inputs = {
        packet["manifest_path"]: packet["manifest_sha256"],
        manifest["authorization"]["path"]: packet["authorization_sha256"],
        manifest["ledger_prefix"]["path"]: manifest["ledger_prefix"]["sha256"],
        ARCHIVED_SCOPED_CONTRACT_02_PATH.as_posix(): manifest["historical_contracts"][1]["sha256"],
    }
    expected_new_inputs.update(packet["proof_digests_path_map"])
    repair_proof = json.loads(packet["proof_bytes"]["repair_proof"])
    validation = repair_proof.get("validation", {})
    repair_logs = {
        "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/fmt-02.log":
            validation.get("format_log", {}).get("sha256"),
        "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/focused-test-02.log":
            validation.get("focused_test_log", {}).get("sha256"),
    }
    for path, digest in repair_logs.items():
        expected_new_inputs[path] = _bound_sha(digest, f"repair log {path} SHA-256")

    build = _validate_harness_build_04(current_validated, old_source)
    expected_new_inputs.update(build["source_inputs"])
    packet["harness_build_04"] = build
    permitted_extra = set(expected_new_inputs)
    extra_inputs = set(current_by_path) - set(old_by_path)
    if extra_inputs != permitted_extra:
        raise ReleaseError("C3 source_inputs add or omit files beyond the sealed scoped-recovery packet")
    for path, digest in expected_new_inputs.items():
        if current_by_path.get(path) != digest:
            raise ReleaseError(f"C3 source_inputs do not bind the scoped-recovery evidence: {path}")

    if old.get("qualifications") != current.get("qualifications"):
        raise ReleaseError("C3 changed the exact qualified analyzer evidence")
    if old_validated["tool_components"] != current_validated["tool_components"]:
        raise ReleaseError("C3 changed an analyzer runtime component")
    if old.get("codeql_packs") != current.get("codeql_packs"):
        raise ReleaseError("C3 changed either exact CodeQL pack root")
    if old.get("execution_series") != current.get("execution_series") or old.get("total_wall_budget_seconds") != current.get("total_wall_budget_seconds"):
        raise ReleaseError("C3 changed the original execution series or wall-clock budget")
    if old.get("resource_budget") != current.get("resource_budget"):
        raise ReleaseError("C3 changed the original resource ceilings")
    if old.get("population") != current.get("population") or old.get("fixture_revision") != current.get("fixture_revision"):
        raise ReleaseError("C3 changed the exact population or fixture revision")

    excluded = {
        "source_commit", "runner_source_sha256", "execution_authorized", "resource_reservation",
        "source_inputs", "tools", "groups", "path_replacements", "qualifications",
        "generator", "prior_failed_contracts", "scoped_recovery",
    }
    old_rest = {key: value for key, value in old.items() if key not in excluded}
    current_rest = {key: value for key, value in current.items() if key not in excluded}
    if old_rest != current_rest:
        raise ReleaseError("C3 changed a pinned contract field outside its reviewed recovery scope")
    old_generator = old.get("generator")
    current_generator = current.get("generator")
    if (not isinstance(old_generator, dict) or not isinstance(current_generator, dict) or
            {key: value for key, value in old_generator.items() if key != "source_sha256"} !=
            {key: value for key, value in current_generator.items() if key != "source_sha256"}):
        raise ReleaseError("C3 changed generator provenance beyond its source digest")

    proof = repair_proof
    patch_manifest = proof.get("patch")
    changed = patch_manifest.get("changed_files") if isinstance(patch_manifest, dict) else None
    expected_files = {
        "src/modeling.rs": {
            "base_git_blob": "a4524333d26deba9a44a180091765d7a86e84846",
            "patched_sha256": "d2de3d05a224b797d2b67356e57063c3ea10992f59c19c89938d72da1ca2917a",
        },
        "src/tests/modeling.rs": {
            "base_git_blob": "395e656e0ef297ab941f2fe0da36244d08bfab24",
            "patched_sha256": "d5c678789c5d77324c7b428984c2bc20e37f1c2248cd104d4dad618c2d04b330",
        },
    }
    if (proof.get("schema") != "dataflowbench-temporary-fix-proof/v1" or
            proof.get("attempt_source_commit") != old_source or
            not isinstance(changed, list) or
            {item.get("path"): {key: item.get(key) for key in ("base_git_blob", "patched_sha256")}
             for item in changed if isinstance(item, dict)} != expected_files or len(changed) != 2):
        raise ReleaseError("C3 repair proof does not bind exactly the reviewed two-file Rust fix")
    if proof.get("validation", {}).get("format_log", {}).get("exit_code") != 0:
        raise ReleaseError("C3 repair proof lacks a successful formatting check")
    focused = proof.get("validation", {}).get("focused_test_log", {})
    if (focused.get("exit_code") != 0 or
            focused.get("result") != "1 passed; 0 failed; 303 filtered out"):
        raise ReleaseError("C3 repair proof lacks the exact focused regression pass")
    for source_path, expected in expected_files.items():
        if _git_blob(root, old_source, source_path) != expected["base_git_blob"]:
            raise ReleaseError(f"C2 base blob differs from the reviewed Rust patch: {source_path}")
        if _sha(_git_show(root, new_source, source_path)) != expected["patched_sha256"]:
            raise ReleaseError(f"C3 Rust source differs from the tested patch: {source_path}")

    diagnosis = json.loads(packet["proof_bytes"]["failure_diagnosis"])
    if (diagnosis.get("schema") != "v092-codeql-modeling-stamp-failure/v1" or
            diagnosis.get("attempt_id") != "codeql-java-modeling-attempt-01-series-01" or
            diagnosis.get("contract_sha256") != C2_CONTRACT_SHA256 or
            diagnosis.get("source_commit") != C2_SOURCE_COMMIT or
            diagnosis.get("plan_commit") != C2_PLAN_COMMIT or
            diagnosis.get("status") != "failed" or diagnosis.get("exit_code") != 1 or
            diagnosis.get("process_cleanup") != "tracked-processes-stopped" or
            diagnosis.get("no_selected_reports") is not True or
            diagnosis.get("all_50_capture_hashes_and_stream_hashes_verified") is not True):
        raise ReleaseError("C3 repair proof is not tied to the exact retained Java modeling failure")

    _validate_scoped_preserved_evidence(root, new_source)

    allowed_changed = {
        "src/modeling.rs", "src/tests/modeling.rs",
        V2_CONTRACT_PATH.as_posix(),
        ARCHIVED_SCOPED_CONTRACT_02_PATH.as_posix(),
        "reports/releases/v0.9.2/execution-v2/preflight-01.json",
        LEDGER_PATH.as_posix(),
        ".github/workflows/ci.yml",
    }
    allowed_changed.update(old_by_path)
    allowed_changed.update(current_by_path)
    allowed_changed.update(SCOPED_RECOVERY_PRESERVED_EVIDENCE_BLOBS)
    allowed_changed.update(_retained_attempt_paths(packet))
    allowed_changed.update(_retained_normal_report_paths(packet))
    allowed_changed.update(build["source_inputs"])
    allowed_changed.update({
        packet["manifest_path"], manifest["authorization"]["path"],
        manifest["ledger_prefix"]["path"],
        *[item["path"] for item in (manifest["repair_patch"], manifest["repair_proof"], manifest["failure_diagnosis"])],
        *repair_logs.keys(),
        "reports/releases/v0.9.2/acquisition/matrix-supervisor-03.py",
        "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest-draft-01.json",
        "reports/releases/v0.9.2/acquisition/harness-build-04/command.json",
        "reports/releases/v0.9.2/validation/scoped-recovery-rust-01/cargo-test.log",
        "reports/releases/v0.9.2/validation/scoped-recovery-rust-01/fmt.log",
        "reports/releases/v0.9.2/validation/scoped-recovery-rust-01/cargo-test-01.json",
        "reports/releases/v0.9.2/validation/scoped-recovery-rust-01/preflight.json",
        "reports/releases/v0.9.2/execution-v2/supervision-02/exit.json",
        "reports/releases/v0.9.2/execution-v2/supervision-02/launcher.json",
        "reports/releases/v0.9.2/execution-v2/supervision-02/dispatch.json",
        "reports/releases/v0.9.2/execution-v2/supervision-02/started.json",
    })
    changed_paths = _git_changed_paths(root, old_source, new_source)
    allowed_scripts = {
        "scripts/execute-release-v092.py", "scripts/test-execute-release-v092.py",
        "scripts/prepare-release-v092.py", "scripts/test-prepare-release-v092.py",
        "scripts/v092_scoped_recovery.py", "scripts/check-release-v092.py",
        "scripts/test-check-release-v092.py", "scripts/test-v092-scoped-recovery.py",
    }
    allowed_docs = {"docs/v0.9.2-execution.md"}
    disallowed = changed_paths - allowed_changed - allowed_scripts - allowed_docs
    if disallowed:
        raise ReleaseError("C3 changed source or evidence outside the exact Rust fix and outer runner/docs: " +
                           ", ".join(sorted(disallowed)))


def _historical_group_for_replay(context: dict, row: dict) -> dict:
    """Select the group representation expected by the evidence checker."""
    group_id = row.get("group_id")
    status = row.get("status")
    if not isinstance(group_id, str) or not group_id:
        raise ReleaseError("historical replay row lacks a group id")
    if status == "completed":
        groups = context.get("plan", {}).get("groups")
    elif status in {"failed", "timed-out", "capacity-lost", "recorder-error"}:
        # _verify_failed_attempt consumes the validated group, which includes
        # normalized identity_components. Successful receipt replay consumes
        # the raw plan group instead.
        groups = context.get("groups")
    else:
        raise ReleaseError("historical replay row has an unsupported status")
    if not isinstance(groups, list):
        raise ReleaseError("historical replay context has no matching group collection")
    matches = [group for group in groups if isinstance(group, dict) and group.get("id") == group_id]
    if len(matches) != 1:
        raise ReleaseError("historical replay context does not have exactly one matching group")
    return matches[0]


def _validate_scoped_recovery(validated: dict) -> dict:
    plan = validated["plan"]
    root = validated["repo_root"]
    packet_module = _scoped_recovery_module()
    try:
        packet = packet_module.validate_packet(root, plan.get("scoped_recovery"))
    except packet_module.ScopedRecoveryError as exc:
        raise ReleaseError(f"scoped recovery packet rejected: {exc}") from exc

    manifest = packet["manifest"]
    references = {
        packet["manifest_path"]: packet["manifest_sha256"],
        manifest["authorization"]["path"]: packet["authorization_sha256"],
        manifest["ledger_prefix"]["path"]: manifest["ledger_prefix"]["sha256"],
        ARCHIVED_SCOPED_CONTRACT_02_PATH.as_posix(): manifest["historical_contracts"][1]["sha256"],
    }
    proof_path_map = {}
    for key in ("repair_patch", "repair_proof", "failure_diagnosis"):
        item = manifest[key]
        proof_path_map[item["path"]] = item["sha256"]
    packet["proof_digests_path_map"] = proof_path_map
    references.update(proof_path_map)
    repair_proof = json.loads(packet["proof_bytes"]["repair_proof"])
    proof_validation = repair_proof.get("validation", {})
    repair_logs = {
        "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/fmt-02.log":
            proof_validation.get("format_log", {}).get("sha256"),
        "reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/focused-test-02.log":
            proof_validation.get("focused_test_log", {}).get("sha256"),
    }
    for relative, digest in repair_logs.items():
        digest = _bound_sha(digest, f"C3 repair log {relative} SHA-256")
        references[relative] = digest
        repair_log_path = root / Path(*PurePosixPath(relative).parts)
        try:
            repair_log_info = repair_log_path.lstat()
            repair_log_raw = repair_log_path.read_bytes()
        except OSError as exc:
            raise ReleaseError(f"cannot read the C3 repair validation log: {relative}") from exc
        if not stat.S_ISREG(repair_log_info.st_mode) or _sha(repair_log_raw) != digest:
            raise ReleaseError(f"C3 repair validation log differs from proof digest: {relative}")
        if relative.endswith("fmt-02.log") and repair_log_raw:
            raise ReleaseError("C3 formatting log differs from the reviewed silent cargo fmt success")
        if relative.endswith("focused-test-02.log"):
            required_output = (
                b"test tests::modeling::codeql_modeling_configuration_matches_v092_validator_without_changing_history ... ok",
                b"test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 303 filtered out",
            )
            if any(line not in repair_log_raw for line in required_output):
                raise ReleaseError("C3 focused-test log does not contain the exact reviewed passing regression")
    source_input_map = {item["path"]: item["sha256"] for item in validated["source_inputs"]}
    if any(source_input_map.get(path) != digest for path, digest in references.items()):
        raise ReleaseError("C3 source_inputs do not bind every scoped recovery record and historical C2 archive")
    for path, digest in references.items():
        if _sha(_git_show(root, plan["source_commit"], path)) != digest:
            raise ReleaseError(f"C3 source commit does not contain exact scoped recovery input: {path}")
    for item in validated["source_inputs"]:
        if _sha(_git_show(root, plan["source_commit"], item["path"])) != item["sha256"]:
            raise ReleaseError(f"C3 source commit differs from a bound source input: {item['path']}")

    history = manifest["historical_contracts"]
    contexts: dict[str, dict] = {}
    for item in history:
        archive_path = root / Path(*PurePosixPath(item["path"]).parts)
        try:
            info = archive_path.lstat()
            archive_raw = archive_path.read_bytes()
        except OSError as exc:
            raise ReleaseError(f"cannot read scoped recovery historical contract: {archive_path}") from exc
        if not stat.S_ISREG(info.st_mode) or _sha(archive_raw) != item["sha256"]:
            raise ReleaseError(f"scoped recovery historical contract differs from its archive digest: {item['path']}")
        if _git_show(root, item["plan_commit"], item["canonical_path"]) != archive_raw:
            raise ReleaseError(f"historical contract differs from its canonical bytes at plan commit: {item['path']}")
        _require_ancestor(root, item["source_commit"], item["plan_commit"],
                          "historical source commit to contract plan commit")
        _require_ancestor(root, item["plan_commit"], plan["source_commit"],
                          "historical contract plan commit to C3 source commit")
        _require_ancestor(root, item["source_commit"], plan["source_commit"],
                          "historical source commit to C3 source commit")

    old_c2_ref = history[1]
    old_c2_path = root / Path(*PurePosixPath(old_c2_ref["path"]).parts)
    old_c2 = validate_plan(
        old_c2_path,
        repo_root=root,
        _archived=True,
        _historical_ledger_rows=packet["prefix_rows"],
    )
    old_c2_sha = old_c2_ref["sha256"]
    if old_c2["bytes_sha256"] != old_c2_sha:
        raise ReleaseError("archived C2 validation produced a different canonical digest")
    old_c1_ref = history[0]
    old_c1_entry = old_c2["prior_failed_contracts"].get(old_c1_ref["sha256"])
    if old_c1_entry is None or old_c1_entry["plan_commit"] != old_c1_ref["plan_commit"]:
        raise ReleaseError("archived C2 did not replay the exact registered C1 failure context")
    old_c1 = old_c1_entry["validated"]
    if (old_c1["plan"]["source_commit"] != old_c1_ref["source_commit"] or
            old_c2["plan"]["source_commit"] != old_c2_ref["source_commit"]):
        raise ReleaseError("historical contract source commits differ from the sealed manifest")
    for context in (old_c1, old_c2):
        context_source = context["plan"]["source_commit"]
        for source_input in context["source_inputs"]:
            if _sha(_git_show(root, context_source, source_input["path"])) != source_input["sha256"]:
                raise ReleaseError(f"historical source input differs at its original commit: {source_input['path']}")
    contexts[old_c1_ref["sha256"]] = {
        "validated": old_c1,
        "plan_commit": old_c1_ref["plan_commit"],
    }
    contexts[old_c2_ref["sha256"]] = {
        "validated": old_c2,
        "plan_commit": old_c2_ref["plan_commit"],
    }

    _validate_scoped_successor_equivalent(old_c2, validated, packet)

    retained_completed: dict[str, dict] = {}
    retained_failures: dict[str, dict] = {}
    manifest_rows_by_line = {
        item["ledger_line_sha256"]: item
        for item in manifest["retained_completed"] + manifest["retained_failures"]
    }
    for row, line_sha in packet["prefix_rows"]:
        context_sha = row["contract_sha256"]
        context_entry = contexts.get(context_sha)
        manifest_item = manifest_rows_by_line.get(line_sha)
        if context_entry is None or manifest_item is None:
            raise ReleaseError("historical ledger row is missing its exact contract context or manifest entry")
        context = context_entry["validated"]
        group = next((item for item in context["plan"]["groups"] if item.get("id") == row.get("group_id")), None)
        if group is None:
            raise ReleaseError("historical ledger row is not a registered group in its source contract")
        attempt_number = int(row["attempt_id"].split("-attempt-")[-1].split("-series-")[0])
        record = {
            "row": row,
            "ledger_line_sha256": line_sha,
            "context_sha256": context_sha,
            "plan_commit": context_entry["plan_commit"],
            "attempt_number": attempt_number,
        }
        if row["status"] == "completed":
            if context_sha != old_c2_sha:
                raise ReleaseError("only completed C2 measurements may be retained by this recovery")
            retained_completed[row["group_id"]] = record
        else:
            retained_failures[row["attempt_id"]] = record

    if len(retained_completed) != 25 or len(retained_failures) != 2:
        raise ReleaseError("scoped recovery replay roster is not exactly 25 completed rows and two failures")
    for group_id, record in retained_completed.items():
        row = record["row"]
        if row.get("status") != "completed" or row.get("source_commit") != C2_SOURCE_COMMIT:
            raise ReleaseError(f"retained completion lost its original C2 provenance: {group_id}")

    # Deep replay uses the same receipt, report projection, process-ownership,
    # and raw-capture interpreter as the release checker. Importing lazily keeps
    # the checker/executor import relationship acyclic at module load time.
    checker_path = Path(__file__).with_name("check-release-v092.py")
    checker_spec = importlib.util.spec_from_file_location("check_release_v092_scoped_replay", checker_path)
    if checker_spec is None or checker_spec.loader is None:
        raise ReleaseError("cannot load the release evidence checker for scoped historical replay")
    checker = importlib.util.module_from_spec(checker_spec)
    checker_spec.loader.exec_module(checker)
    for record in [*retained_completed.values(), *retained_failures.values()]:
        context_entry = contexts[record["context_sha256"]]
        context = context_entry["validated"]
        row = record["row"]
        group = _historical_group_for_replay(context, row)
        try:
            if row["status"] == "completed":
                checker._verify_one_group(
                    root, context, group, row, record["plan_commit"], record["attempt_number"],
                )
            else:
                manifest_item = manifest_rows_by_line[record["ledger_line_sha256"]]
                checker._verify_failed_attempt(
                    root,
                    context,
                    group,
                    row,
                    record["plan_commit"],
                    record["attempt_number"],
                    record["ledger_line_sha256"],
                    manifest_item["completed_receipt"]["sha256"],
                )
        except checker.EvidenceError as exc:
            raise ReleaseError(f"historical attempt replay failed: {row['attempt_id']}: {exc}") from exc

    _validate_scoped_tail(validated, packet)
    return {
        **packet,
        "sealed_prefix_sha256": manifest["ledger_prefix"]["sha256"],
        "contexts": contexts,
        "retained_completed": retained_completed,
        "retained_failures": retained_failures,
        "prefix_rows": packet["prefix_rows"],
    }


def _validate_scoped_tail(validated: dict, packet: dict) -> None:
    """Reject any appended rows except attempts under the exact current C3 contract."""
    plan = validated["plan"]
    contract_sha = validated["bytes_sha256"]
    group_ids = {group["id"] for group in plan["groups"]}
    counts: dict[str, int] = {}
    for row, _line_sha in packet["prefix_rows"]:
        counts[row["group_id"]] = counts.get(row["group_id"], 0) + 1
    for row, _line_sha in packet["tail_rows"]:
        group_id = row.get("group_id")
        if (row.get("contract_sha256") != contract_sha or
                row.get("source_commit") != plan["source_commit"] or
                row.get("execution_series") != plan["execution_series"] or
                group_id not in group_ids):
            raise ReleaseError("post-prefix ledger row is not registered to the exact C3 contract")
        counts[group_id] = counts.get(group_id, 0) + 1
        if counts[group_id] > 2:
            raise ReleaseError(f"{group_id}: attempts exceed the original cross-contract maximum of two")
        attempt_id = row.get("attempt_id")
        expected_id = f"{group_id}-attempt-{counts[group_id]:02d}-series-{plan['execution_series']:02d}"
        if attempt_id != expected_id:
            raise ReleaseError(f"{group_id}: post-prefix attempt number would reset or skip history")
    completed_before_c3 = {row.get("group_id") for row, _line_sha in packet["prefix_rows"]
                           if row.get("status") == "completed"}
    if any(row.get("group_id") in completed_before_c3 for row, _line_sha in packet["tail_rows"]):
        raise ReleaseError("C3 cannot re-execute a group with a retained completed C2 measurement")


def validate_plan(
    plan_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    _archived: bool = False,
    _historical_ledger_rows: Sequence[tuple[dict, str]] | None = None,
) -> dict:
    """Validate the immutable v0.9.2 execution contract without launching tools."""
    path = Path(plan_path).expanduser().resolve()
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else _repo_root(path.parent)
    if not _under(path, root):
        raise ReleaseError("plan must be inside the execution repository")
    relative_path = path.relative_to(root).as_posix()
    if _archived:
        if relative_path not in (
            ARCHIVED_FAILED_CONTRACT_PATH.as_posix(),
            ARCHIVED_SCOPED_CONTRACT_02_PATH.as_posix(),
        ):
            raise ReleaseError("archived contract validation is limited to the registered C1/C2 contracts")
    elif relative_path not in (
        V1_CONTRACT_PATH.as_posix(), V2_CONTRACT_PATH.as_posix(), V3_CONTRACT_PATH.as_posix(),
    ):
        raise ReleaseError("contract must be the canonical execution-v1, execution-v2, or execution-v3 contract")
    plan, plan_raw = _read_json(path, "release plan")
    if plan.get("schema_version") != 1 or plan.get("release") != RELEASE:
        raise ReleaseError("plan schema or release identity mismatch")
    is_c1_archive = _archived and relative_path == ARCHIVED_FAILED_CONTRACT_PATH.as_posix()
    is_c2_archive = _archived and relative_path == ARCHIVED_SCOPED_CONTRACT_02_PATH.as_posix()
    if is_c1_archive or (not _archived and relative_path == V1_CONTRACT_PATH.as_posix()):
        if "prior_failed_contracts" in plan:
            raise ReleaseError("execution-v1 contract cannot carry predecessor history")
        if "scoped_recovery" in plan:
            raise ReleaseError("execution-v1 contract cannot carry scoped recovery")
    elif is_c2_archive or (not _archived and relative_path == V2_CONTRACT_PATH.as_posix()):
        if not isinstance(plan.get("prior_failed_contracts"), list) or len(plan["prior_failed_contracts"]) != 1:
            raise ReleaseError("execution-v2 contract must bind exactly one prior failed contract")
        if "scoped_recovery" in plan:
            raise ReleaseError("execution-v2 contract cannot carry scoped recovery")
    elif not _archived and relative_path == V3_CONTRACT_PATH.as_posix():
        if "prior_failed_contracts" in plan:
            raise ReleaseError("execution-v3 cannot carry prior_failed_contracts")
        recovery = plan.get("scoped_recovery")
        if (not isinstance(recovery, dict) or set(recovery) != {"path", "sha256"} or
                recovery.get("path") != SCOPED_RECOVERY_MANIFEST_PATH.as_posix() or
                not isinstance(recovery.get("sha256"), str) or not SHA256.fullmatch(recovery["sha256"])):
            raise ReleaseError("execution-v3 must bind the exact scoped-recovery manifest path and digest")
    else:
        raise ReleaseError("execution-v2 contract must bind exactly one prior failed contract")
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
    expected_swift_packs_root = (root / "execution-state/v092/tools/swift-codeql/candidate-packs-entry2").resolve()
    if (not isinstance(swift_packs_root_value, str) or not Path(swift_packs_root_value).is_absolute() or
            Path(swift_packs_root_value).resolve() != expected_swift_packs_root):
        raise ReleaseError("custom Swift pack root must be execution-state/v092/tools/swift-codeql/candidate-packs-entry2")
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
    result = {
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
    if is_c1_archive or (not _archived and relative_path == V1_CONTRACT_PATH.as_posix()):
        result["prior_failed_contracts"] = {}
    elif is_c2_archive or (not _archived and relative_path == V2_CONTRACT_PATH.as_posix()):
        result["prior_failed_contracts"] = _validate_prior_failed_contracts(
            result, historical_ledger_rows=_historical_ledger_rows,
        )
    else:
        result["prior_failed_contracts"] = {}
        result["scoped_recovery"] = _validate_scoped_recovery(result)
    return result


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


def _process_tracker():
    # Reuse the existing PID/start-identity checks without changing the frozen
    # Swift process helper or treating process-group membership as containment.
    path = Path(__file__).with_name("swift_v2_scored_process.py")
    spec = importlib.util.spec_from_file_location("v092_process_tracker", path)
    if spec is None or spec.loader is None:
        raise ReleaseError("process ownership tracker is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stop_owned_processes(process, tracker, tracked: dict[int, str], signals_sent: list[dict]) -> None:
    """Stop observed descendants even when they created separate sessions."""
    for sig, grace in ((signal.SIGTERM, 0.5), (signal.SIGKILL, 1.5)):
        until = time.monotonic() + grace
        while True:
            table = tracker._process_table()
            tracked.update(tracker._descendants(table, tracked))
            alive = tracker._active(table, tracked)
            if not alive:
                process.poll()
                if process.poll() is None:
                    raise ReleaseError("invocation parent is alive without its tracked start identity")
                return
            for pid in reversed(alive):
                # Never signal a recycled PID or discover through a recycled
                # ancestor. Each signal rechecks the high-resolution identity.
                current = tracker._process_table()
                if pid not in tracker._active(current, tracked):
                    continue
                try:
                    os.kill(pid, sig)
                    signals_sent.append({"pid": pid, "start_identity": tracked[pid], "signal": sig.name})
                except ProcessLookupError:
                    pass
            process.poll()
            if time.monotonic() >= until:
                break
            time.sleep(0.05)
    table = tracker._process_table()
    if tracker._active(table, tracked) or process.poll() is None:
        raise ReleaseError("tracked invocation processes remain alive after cleanup")


def _tree_bytes(paths: Sequence[Path]) -> int:
    total = 0
    seen = set()
    for root in paths:
        if not root.exists():
            continue
        walk = [(root.parent, [], [root.name])] if root.is_file() else os.walk(root, followlinks=False)
        for directory, _directories, names in walk:
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


def _matrix_capacity_paths(validated: dict, execution_root: Path,
                           env: Mapping[str, str], output_roots: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    """Account for retained originals and scratch from earlier serial attempts."""
    root = validated["repo_root"]
    retained = [root / "reports/releases/v0.9.2", *output_roots]
    scratch = [root / Path(*CACHE_ROOT.parts), Path(env["HOME"]), Path(env["TMPDIR"])]
    groups = {group["id"]: group for group in validated["plan"]["groups"]}
    for row in _ledger_rows(root / Path(*LEDGER_PATH.parts)):
        group_id = row.get("group_id")
        if group_id not in groups:
            raise ReleaseError("capacity ledger contains an unknown group")
        previous = Path(row.get("execution_root", ""))
        if not previous.is_absolute() or not _under(previous, root / Path(*EXECUTION_ROOT.parts)):
            raise ReleaseError("capacity ledger execution root escapes task outputs")
        previous_home = previous / "home"
        previous_tmp = previous / "tmp"
        if groups[group_id]["tool"] == "pysa":
            identity = hashlib.sha256(str(previous.resolve()).encode()).hexdigest()[:20]
            previous_tmp = Path("/private/tmp") / ("dfb-v092-pysa-" + identity)
        scratch.extend([previous_home, previous_tmp])
        retained.extend(previous / Path(*_relative(value, "retained output root").parts)
                        for value in groups[group_id]["output_roots"])
    return retained, scratch


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
                 scratch_limit: int = MAX_RETAINED_BYTES,
                 ownership: dict | None = None) -> tuple[int, bool, float, str | None]:
    started = time.monotonic()
    timed_out = False
    capacity_loss = None
    ownership = {} if ownership is None else ownership
    ownership.update({"schema": "invocation-process-ownership/v1", "root_pid": None,
                      "tracked_processes": [], "signals_sent": [],
                      "cleanup_status": "not-started", "descendant_containment": "unproven",
                      "tracking_interval_seconds": 2.0})
    with stdout.open("wb") as out, stderr.open("wb") as err:
        capacity_loss = _capacity_loss(cwd, retained_paths, retention_limit, scratch_paths, scratch_limit)
        if capacity_loss:
            return 125, False, time.monotonic() - started, capacity_loss
        tracker = _process_tracker()
        tracked: dict[int, str] = {}
        process = subprocess.Popen(
            list(argv), cwd=cwd, env=dict(env), stdout=out, stderr=err,
            start_new_session=True, close_fds=True,
        )
        ownership["root_pid"] = process.pid
        try:
            table = tracker._process_table()
            if process.pid not in table:
                raise ReleaseError("invocation root start identity was never captured")
            tracked[process.pid] = table[process.pid][1]
            while process.poll() is None:
                tracked.update(tracker._descendants(tracker._process_table(), tracked))
                capacity_loss = _capacity_loss(cwd, retained_paths, retention_limit, scratch_paths, scratch_limit)
                if capacity_loss:
                    break
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    timed_out = True
                    break
                try:
                    process.wait(timeout=min(2.0, remaining))
                except subprocess.TimeoutExpired:
                    continue
        except BaseException as exc:
            ownership["tracking_error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            try:
                _stop_owned_processes(process, tracker, tracked, ownership["signals_sent"])
                ownership["cleanup_status"] = (
                    "uncertain" if "tracking_error" in ownership else "tracked-processes-stopped"
                )
            except BaseException as exc:
                ownership["cleanup_status"] = "uncertain"
                ownership["cleanup_error"] = f"{type(exc).__name__}: {exc}"
                if process.poll() is None:
                    _terminate_process_group(process)
                raise
            finally:
                ownership["tracked_processes"] = [
                    {"pid": pid, "start_identity": birth} for pid, birth in sorted(tracked.items())
                ]
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
    if group.get("tool") == "pysa":
        # Explicit benchmark fixtures must not inherit the repository ignore
        # rule for execution-state from Pyrefly 1.4. Keep owned scratch separate.
        identity = hashlib.sha256(str(execution_root.resolve()).encode()).hexdigest()[:20]
        environment["TMPDIR"] = str(Path("/private/tmp") / ("dfb-v092-pysa-" + identity))
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
    execution = repo_root / Path(*EXECUTION_ROOT.parts) / f"series-{series:02d}" / group_id / f"attempt-{attempt_number:02d}"
    cache = repo_root / Path(*CACHE_ROOT.parts) / f"series-{series:02d}" / group_id / f"attempt-{attempt_number:02d}"
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


def _matrix_elapsed_wall(validated: dict, *, now_seconds: float | None = None) -> float:
    """A resumed invocation retains the original series wall-clock ceiling."""
    rows = _ledger_rows(validated["repo_root"] / Path(*LEDGER_PATH.parts))
    series = validated["plan"]["execution_series"]
    registered_contracts = {validated["bytes_sha256"]}
    registered_contracts.update(validated.get("prior_failed_contracts", {}).keys())
    scoped = validated.get("scoped_recovery")
    if isinstance(scoped, dict):
        registered_contracts.update(scoped.get("contexts", {}).keys())
    series_rows = [row for row in rows if row.get("execution_series") == series]
    if any(row.get("contract_sha256") not in registered_contracts for row in series_rows):
        raise ReleaseError("execution series has an unregistered contract revision")
    selected = [row for row in series_rows if row.get("contract_sha256") in registered_contracts]
    if not selected:
        return 0.0
    starts = []
    durations = 0.0
    for row in selected:
        try:
            start = _datetime.datetime.fromisoformat(row["start_utc"])
            if start.tzinfo is None:
                raise ValueError("timezone missing")
            starts.append(start.timestamp())
        except (KeyError, TypeError, ValueError) as exc:
            raise ReleaseError("retained attempt has no valid wall-budget start") from exc
        duration = row.get("duration_seconds", 0)
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
            raise ReleaseError("retained attempt has invalid wall-budget duration")
        durations += duration
    now = time.time() if now_seconds is None else now_seconds
    if now < min(starts):
        raise ReleaseError("wall clock predates retained attempt start")
    if isinstance(scoped, dict):
        original = scoped.get("manifest", {}).get("original_wall_origin_utc")
        try:
            original_timestamp = _datetime.datetime.fromisoformat(original).timestamp()
        except (TypeError, ValueError) as exc:
            raise ReleaseError("scoped recovery has no valid original wall-clock origin") from exc
        if min(starts) != original_timestamp:
            raise ReleaseError("retained attempt series does not begin at the exact authorized wall origin")
    return max(now - min(starts), durations)


def _verified_completed_groups(validated: dict) -> set[str]:
    """Return only groups whose durable receipt and staged reports verify."""
    ledger = validated["repo_root"] / Path(*LEDGER_PATH.parts)
    if not ledger.exists():
        return set()
    rows = _ledger_rows(ledger)
    scoped = validated.get("scoped_recovery")
    verified = set(scoped.get("retained_completed", {})) if isinstance(scoped, dict) else set()
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
    if any(row.get("execution_series") == series and row.get("status") == "completed" for row in prior):
        raise ReleaseError(f"group {group_id} already has completed evidence for this execution series")
    if any(row.get("execution_series") == series and row.get("status") not in
           {"failed", "timed-out", "capacity-lost", "recorder-error"} for row in prior):
        raise ReleaseError(f"group {group_id} has a non-terminal or unknown retained attempt")
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


def _preserve_recorder_failure(repo_root: Path, attempt: Path, attempt_id: str, row: dict) -> None:
    """Bind partial recorder writes without treating them as completed reports."""
    def files(directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        if directory.is_symlink():
            raise ReleaseError("partial recorder directory is symlinked")
        result = []
        for current, directories, names in os.walk(directory, followlinks=False):
            base = Path(current)
            if any((base / name).is_symlink() for name in directories):
                raise ReleaseError("symlink in partial recorder evidence")
            for name in names:
                path = base / name
                if path.is_symlink() or not path.is_file():
                    raise ReleaseError("non-regular partial recorder evidence")
                result.append(path)
        return sorted(result)

    # A tracker/import/Popen failure before a PID exists did not launch an
    # invocation. Preserve the recorder error and streams, not a capacity-only
    # "not-started" process receipt.
    ownership = row.get("process_ownership")
    if isinstance(ownership, dict) and ownership.get("root_pid") is None:
        row.pop("process_ownership", None)
    capture = attempt / "capture"
    row["captured_files"] = [
        {"execution_relative": path.relative_to(capture).as_posix(),
         "capture_path": str(path),
         "sha256": _sha(path.read_bytes()), "bytes": path.stat().st_size}
        for path in files(capture)
    ]
    staging = repo_root / Path(*NORMAL_ROOT.parts) / "attempts" / attempt_id
    row["failed_staging_artifacts"] = [
        _file_receipt(path, path.relative_to(repo_root).as_posix())
        for directory in (attempt / "original", staging) for path in files(directory)
    ]
    row["reports"] = []
    for field in ("stdout", "stderr"):
        path = attempt / (field + ".txt")
        if path.is_file() and not path.is_symlink():
            row[field] = _file_receipt(path, field + ".txt")


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
        if (_matrix_elapsed_wall(validated) + group["deadline_seconds"] >
                validated["total_wall_budget_seconds"]):
            raise ReleaseError("total wall budget would be exceeded before this group")
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
            scratch_path = Path(env["TMPDIR"])
            if group["tool"] == "pysa":
                scratch_path.mkdir()  # Freshness includes external task-owned scratch.
            else:
                scratch_path.mkdir(parents=True, exist_ok=True)
            retained_paths, scratch_paths = _matrix_capacity_paths(validated, execution_root, env, output_roots)
            stdout = attempt / "stdout.txt"
            stderr = attempt / "stderr.txt"
            row["process_ownership"] = {}
            exit_code, timed_out, duration, capacity_loss = _run_process(
                group["argv"], execution_root, env, stdout, stderr, group["deadline_seconds"],
                ownership=row["process_ownership"],
                retained_paths=retained_paths,
                retention_limit=plan["resource_budget"]["proposed_total_retention_ceiling_gib"] * 1024**3,
                scratch_paths=scratch_paths,
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
                repo_root, retained_paths,
                plan["resource_budget"]["proposed_total_retention_ceiling_gib"] * 1024**3,
                scratch_paths, plan["resource_budget"]["scratch_gib"] * 1024**3,
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
            _preserve_recorder_failure(repo_root, attempt, attempt_id, row)
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
        elapsed = max(time.monotonic() - matrix_started, _matrix_elapsed_wall(validated))
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
