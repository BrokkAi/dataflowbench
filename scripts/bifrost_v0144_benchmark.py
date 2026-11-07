#!/usr/bin/env python3
"""Prepare, execute, and independently verify the v0.9.2 Bifrost 0.14.4 target.

This is a target-specific C5 driver. It intentionally does not call the legacy
v0.9.2 canonical plan validator or the general release executor's ``run_group``.
The only executable groups are the fixed 20 Bifrost groups. ``prepare`` writes
an unapproved, hash-bound manifest and never starts an analyzer. ``verify`` is
read-only. Execution requires a committed, explicitly approved C5 manifest.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import threading
import time
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence


RELEASE = "v0.9.2"
TARGET_HELP_DESCRIPTION = __doc__
TARGET_ID = "bifrost-v0144-01"
CONTRACT_SCHEMA = "dataflowbench-v0.9.2-bifrost-target/v1"
SERIES = 3
SERIES_LABEL = "series-03"
CONTRACT_REL = "reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/contract-02.json"
PROGRESS_REL = "reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/progress.jsonl"
SUMMARY_REL = "reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/series-summary.json"
INVOCATIONS_REL = "reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/invocations"
LEDGER_REL = "reports/releases/v0.9.2/ledger-v1.jsonl"
BASE_PLAN_REL = "reports/releases/v0.9.0/plan.json"
BASE_POPULATION_REL = "populations/v0.9.0.json"
BASE_PARENT_EXECUTION_REL = "reports/releases/v0.9.0/execution-v1/contract.json"
BASE_CONTRACT_REL = "reports/releases/v0.9.2/execution-v4/contract.json"
QUALIFICATION_DEFAULT = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/bifrost-release-01.json"
CONTROL_REVIEW_DEFAULT = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/bifrost-review-03.json"
INDEPENDENT_REVIEW_DEFAULT = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/independent-review-v0144-01.json"
CONTROL_CAPTURE_DEFAULT = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/controls-attempt-01"
HUMAN_AUTHORIZATION_DEFAULT = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/human-authorization-01.json"
BIFROST_RECEIPT_DEFAULT = "reports/releases/v0.9.2/acquisition/bifrost-v0144-01/acquisition-receipt.json"
BIFROST_CONTROL_REVIEW_SCHEMA = "v092-bifrost-v0144-control-review/v1"
INDEPENDENT_REVIEW_SCHEMA = "v092-bifrost-v0144-independent-review/v1"
REVIEW_IMPLEMENTATION_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/review-bifrost-v0144-01.py"
CONTROL_COMPARISON_DIAGNOSTIC_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0144-01/control-comparison-diagnostic-01.json"
PIN_PROFILE_PATH = "adapters/pins/v0.9.2-bifrost-v0144.json"
PIN_PROFILE_NATIVE_EVIDENCE_DIRECTORY = "reports/releases/v0.9.2/qualification/bifrost-v0144-01"
SCALA_RECEIPT_DEFAULT = "reports/releases/v0.9.2/acquisition/scala-library-2.13.16-01/acquisition-receipt.json"
BIFROST_PATH_DEFAULT = "execution-state/v092/tools/bifrost0144/extracted/bifrost-v0.14.4-universal-apple-darwin/bifrost"
RUNNER_PATH_DEFAULT = "execution-state/v092/builds/bifrost0144-01-target/release/dataflowbench"
RUNNER_BUILD_RECEIPT = "reports/releases/v0.9.2/validation/bifrost-v0144-release-build-01/receipt.json"
RUNNER_BUILD_INPUTS = "reports/releases/v0.9.2/validation/bifrost-v0144-release-build-01/source-inputs.json"
RUNNER_BUILD_STDOUT = "reports/releases/v0.9.2/validation/bifrost-v0144-release-build-01/stdout"
RUNNER_BUILD_STDERR = "reports/releases/v0.9.2/validation/bifrost-v0144-release-build-01/stderr"
RUNNER_CARGO_TARGET_DIR = "execution-state/v092/builds/bifrost0144-01-target"
TARGET_DRIVER_SOURCE_REL = "scripts/bifrost_v0144_benchmark.py"
TARGET_TEST_SOURCE_REL = "scripts/test_bifrost_v0144_benchmark.py"
CORE_SOURCE_REL = None
PROFILE_SOURCE_REL = None
ATTEMPT_RECEIPT_SCHEMA = "dataflowbench-v0.9.2-bifrost-target-attempt/v1"
PROGRESS_SCHEMA = "dataflowbench-v0.9.2-bifrost-target-progress/v1"
INVOCATION_SCHEMA = "dataflowbench-v0.9.2-bifrost-target-invocation/v1"
SERIES_SUMMARY_SCHEMA = "dataflowbench-v0.9.2-bifrost-target-series-summary/v1"
RECONCILIATION_SCHEMA = "dataflowbench-v0.9.2-bifrost-target-reconciliation/v1"
SCALA_REPOSITORY_DEFAULT = "execution-state/v092/tools/scala-maven-2.13.16/repository"
ATTEMPTS_REL = "reports/releases/v0.9.2/attempts"
NORMAL_ATTEMPTS_REL = "reports/releases/v0.9.2/normal/attempts"
EXECUTION_GROUPS_REL = "execution-state/v092/groups"
CACHE_REL = "execution-state/v092/cache"

BASE_PLAN_SHA256 = "540846ca9c0a0bd1c257c51f3e64bb6186cd9d3dd47c52106483fb183636efbf"
BASE_PARENT_EXECUTION_SHA256 = "8597f343542d652e0c7063dc9e5832797e9dfd8bf19975e9bcf309181249dd3d"
BASE_POPULATION_SHA256 = "d05be4f2d9effe7b14a2ce5544238364f171e1fb763db2f79ff486526ca7c890"
BASE_C4_CONTRACT_SHA256 = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
LEDGER_PREFIX_LINES = 109
LEDGER_PREFIX_SHA256 = "2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851"
ORIGINAL_WALL_ORIGIN_UTC = "2026-10-20T00:57:00.680937+00:00"
TARGET_WALL_BUDGET_SECONDS = 13_592
FIXTURE_REVISION = "sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62"

BIFROST_VERSION = "0.14.4"
BIFROST_REPORT_VERSION = "bifrost 0.14.4"
BIFROST_BUILD_IDENTITY = "ff5cf473f4ad414751911ff93ef79e1df1d35823"
BIFROST_CATALOG_SHA256 = "f9d3b4efcf20e0ca8e8a976d6524556f114f4a4ccab3f4b0cc761f0b9248d206"
BIFROST_BINARY_SHA256 = "a3aa17a18be33e1e841c1bf317c6ca35a6aa3aaef452c607fafbb3b83aeec399"
BIFROST_ARCHIVE_SHA256 = "4107616cbd9e9377c7c1c568e9cd2082f5565a4fd9c3e27022a79acd201532ac"
BIFROST_RECEIPT_SHA256 = "c32c1b0ab396f9e0d5849fc01d4c602b0fcd27e13056944ff16ad6b7a2f16371"
SCALA_RECEIPT_SHA256 = "e3128ad0fd9aa5dacdcad5ed9772d4a8e492ac379d7c41d58c11a0f7e49377ef"
PUBLIC_BIFROST_TAG_COMMIT = "786891f9ed19d2086dfd6242ff15ca904b610620"
SOURCE_BASELINE_COMMIT = "36d93cc32abc20ff9a0573e755555f4b71f360b3"
QUALIFICATION_SHA256 = "d08717cecb73e055f7e31e03a56f9d0835b4ee3607f4529f51cee5722ac6aacb"
CONTROL_REVIEW_SHA256 = "cbd7251bcdfcf6a2d93b090422a4968481cbc8b07c6fb23216403909e24ba8e2"
INDEPENDENT_REVIEW_SHA256 = "7c0d01399ef8b0cc15315fcd6e69a6646e31e28dc8801efaee1e35c55992f927"
CAPTURE_MANIFEST_SHA256 = "d57cdb8353a47b9886621e746f2b6469be5480d920b089ae4e9a3ec14066b683"
CAPTURE_QUALIFICATION_SHA256 = "5aaad619ed7b0c6fa7fec7cf7a32b7dbd9763175544eb3f0a45eb5224d8025a4"
RUNNER_BINARY_SHA256 = "114912643aa9b467b00487b1cfaf9985f17b845936da4527dca8cadbbf9682d0"
RUNNER_BINARY_BYTES = 11_003_248
RUNNER_BUILD_RECEIPT_SHA256 = "3d0edc800838b6cf32a571996058f6f6cf7f9b58a8348659535c0986af591d46"
RUNNER_BUILD_INPUTS_SHA256 = "6a1238dfd8d097092569828e55e0a5fda9d449e1cd0851abb6d0e56cb8f940fd"
RUNNER_BUILD_STDOUT_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
RUNNER_BUILD_STDERR_SHA256 = "eede1e2dca04a377e545d0873c3d785fba98e75e4a8a7c3dd5e94cd7dc9477a2"

SCALA_FILES = {
    "scala-library-2.13.16.jar": {
        "role": "binary-jar",
        "sha256": "1ebb2b6f9e4eb4022497c19b1e1e825019c08514f962aaac197145f88ed730f1",
        "size_bytes": 5_926_340,
    },
    "scala-library-2.13.16-sources.jar": {
        "role": "sources-jar",
        "sha256": "c02edc324e7db59c52115214a6ef36e2d78d0a50dff635eda4dcee5502b1dea5",
        "size_bytes": 1_063_010,
    },
    "scala-library-2.13.16.pom": {
        "role": "upstream-pom",
        "sha256": "b25b72ba96eb30934868d86d307298d24d3ac154d362e7a4eeb37ba51ba86853",
        "size_bytes": 1_602,
    },
}

BIFROST_GROUP_IDS = (
    "bifrost-c-kernel",
    "bifrost-cpp-kernel",
    "bifrost-csharp-kernel",
    "bifrost-go-kernel",
    "bifrost-java-kernel",
    "bifrost-java-modeling",
    "bifrost-java-native",
    "bifrost-javascript-kernel",
    "bifrost-javascript-modeling",
    "bifrost-javascript-native",
    "bifrost-kotlin-kernel",
    "bifrost-php-kernel",
    "bifrost-python-kernel",
    "bifrost-python-modeling",
    "bifrost-python-native",
    "bifrost-ruby-kernel",
    "bifrost-rust-kernel",
    "bifrost-scala-kernel",
    "bifrost-smoke",
    "bifrost-typescript-kernel",
)

RESOURCE_POLICY = {
    "launch_free_floor_gib": 127,
    "continuous_free_floor_gib": 125,
    "protected_reserve_gib": 40,
    "emergency_margin_gib": 8,
    "guard_stop_floor_gib": 48,
    "scratch_ceiling_gib": 24,
    "retention_ceiling_gib": 24,
    "source_aggregate_ceiling_gib": 30,
    "source_per_attempt_ceiling_gib": 12,
    "serial_analyzer_slots": 1,
}
ATTEMPT_POLICY = {
    "series": SERIES,
    "series_label": SERIES_LABEL,
    "new_target_slots_per_group": 2,
    "attempt_numbering": "monotonic-per-group-across-all-ledgers-and-started-namespaces",
    "global_attempt_numbering": "monotonic-across-all-ledger-rows-and-started-namespaces",
    "automatic_retry": False,
    "serial_mode": "fail-stop-on-first-non-completed-attempt",
}
ALLOWED_RUNTIME_PROJECTIONS = {
    "argv": ["argv[0] = pinned optimized harness binary",
             f"the value following the single --bifrost flag = acquired v{BIFROST_VERSION} binary"],
    "report_identity": [f"tool_version changes from frozen C4 Bifrost version to {BIFROST_REPORT_VERSION}"],
    "scala_maven": ["the exact pinned binary jar, sources jar, and POM are staged into only the Scala attempt HOME"],
    "all_baseline_group_policy_case_ids_reports_paths_deadlines_and_attempt_budgets_retained": True,
}

COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
ATTEMPT_SUFFIX_RE = re.compile(r"-attempt-(\d+)-series-(\d+)\Z")
ATTEMPT_DIR_RE = re.compile(r"attempt-(\d+)\Z")
SAFE_GROUP_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


class BenchmarkError(RuntimeError):
    """A fail-closed C5 admission, execution, or reconciliation error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _pretty_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_json(path: Path, description: str) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file():
        raise BenchmarkError(f"{description} is missing, symlinked, or not a regular file: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise BenchmarkError(f"{description} must be a JSON object: {path}")
    return value, raw


def _repo_relative(root: Path, value: str, description: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise BenchmarkError(f"{description} must be a non-empty repository-relative path")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise BenchmarkError(f"{description} is not a safe repository-relative path: {value!r}")
    resolved = root.joinpath(*candidate.parts)
    try:
        resolved.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise BenchmarkError(f"{description} escapes the repository: {value!r}") from exc
    return candidate


def _accounting_source_path(root: Path, value: str, description: str) -> str:
    relative = _repo_relative(root, value, description)
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise BenchmarkError(f"{description} traverses a symlink: {current}")
        if not current.exists():
            break
    if current.exists() and not current.is_file():
        raise BenchmarkError(f"{description} is not a regular file: {current}")
    return relative.as_posix()


def _path_ref(root: Path, value: str | Path, description: str) -> tuple[PurePosixPath, Path, bytes]:
    raw_value = str(value)
    path = Path(raw_value)
    if path.is_absolute():
        try:
            relative = path.resolve(strict=False).relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise BenchmarkError(f"{description} must be inside the repository: {path}") from exc
    else:
        relative = raw_value
    rel = _repo_relative(root, relative, description)
    full = root.joinpath(*rel.parts)
    if full.is_symlink() or not full.is_file():
        raise BenchmarkError(f"{description} is missing, symlinked, or not a regular file: {full}")
    return rel, full, full.read_bytes()


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.STDOUT, text=text)
    except (OSError, subprocess.CalledProcessError) as exc:
        output = exc.output.decode(errors="replace") if isinstance(getattr(exc, "output", None), bytes) else getattr(exc, "output", "")
        raise BenchmarkError(f"git {' '.join(args)} failed: {output.strip()}") from exc


def _git_blob_sha256(root: Path, commit: str, relative: str) -> tuple[str, int]:
    """Hash committed file bytes without buffering whole source artifacts."""
    if not COMMIT_RE.fullmatch(commit):
        raise BenchmarkError("source_commit must be an exact lowercase 40-character Git commit")
    _repo_relative(root, relative, "source input path")
    process = subprocess.Popen(
        ["git", "cat-file", "blob", f"{commit}:{relative}"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    digest = hashlib.sha256()
    size = 0
    try:
        for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    finally:
        stderr = process.stderr.read() if process.stderr is not None else b""
        process.wait()
    if process.returncode != 0:
        raise BenchmarkError(f"source commit {commit} lacks {relative}: {stderr.decode(errors='replace').strip()}")
    return digest.hexdigest(), size


def _assert_ancestor(root: Path, ancestor: str, descendant: str, description: str) -> None:
    if not COMMIT_RE.fullmatch(ancestor) or not COMMIT_RE.fullmatch(descendant):
        raise BenchmarkError(f"{description} must use exact Git commit IDs")
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=root,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BenchmarkError(f"{description} is not an ancestor") from exc


def _load_core(root: Path, expected_sha256: str | None = None):
    path = root / "scripts/execute-release-v092.py"
    if path.is_symlink() or not path.is_file():
        raise BenchmarkError(f"pinned release helper is missing or unsafe: {path}")
    source_bytes = path.read_bytes()
    actual = _sha(source_bytes)
    if expected_sha256 is not None and actual != expected_sha256:
        raise BenchmarkError("execute-release-v092.py hash differs from the C5 contract")
    module_name = f"bifrost_release_core_{actual[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise BenchmarkError("cannot dynamically import the pinned v0.9.2 helper")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source_bytes, str(path), "exec"), module.__dict__)
    module.__verified_source_sha256__ = actual
    return module, actual


def _base_inputs(root: Path) -> tuple[dict, dict, dict, dict, list[str]]:
    plan, plan_raw = _read_json(root / BASE_PLAN_REL, "v0.9.0 parent plan")
    population, population_raw = _read_json(root / BASE_POPULATION_REL, "v0.9.0 population")
    parent_execution, parent_execution_raw = _read_json(root / BASE_PARENT_EXECUTION_REL, "v0.9.0 execution contract")
    base, base_raw = _read_json(root / BASE_CONTRACT_REL, "v0.9.2 C4 contract")
    actual = {
        BASE_PLAN_REL: _sha(plan_raw),
        BASE_POPULATION_REL: _sha(population_raw),
        BASE_PARENT_EXECUTION_REL: _sha(parent_execution_raw),
        BASE_CONTRACT_REL: _sha(base_raw),
    }
    expected = {
        BASE_PLAN_REL: BASE_PLAN_SHA256,
        BASE_POPULATION_REL: BASE_POPULATION_SHA256,
        BASE_PARENT_EXECUTION_REL: BASE_PARENT_EXECUTION_SHA256,
        BASE_CONTRACT_REL: BASE_C4_CONTRACT_SHA256,
    }
    for path, digest in expected.items():
        if actual[path] != digest:
            raise BenchmarkError(f"frozen parent reference changed: {path}")
    if plan.get("execution_group_count") != 84 or plan.get("expected_report_partitions") != 92 or plan.get("expected_report_rows") != 4252:
        raise BenchmarkError("v0.9.0 parent plan no longer has the frozen 84/92/4252 population")
    cases = population.get("cases")
    if not isinstance(cases, list) or len(cases) != 1108:
        raise BenchmarkError("v0.9.0 population no longer contains exactly 1,108 cases")
    if population.get("fixture_revision") != FIXTURE_REVISION:
        raise BenchmarkError("v0.9.0 population fixture revision changed")
    groups = base.get("groups")
    if not isinstance(groups, list) or len(groups) != 84:
        raise BenchmarkError("C4 baseline no longer contains exactly 84 full-population groups")
    report_count = sum(len(group.get("reports", [])) for group in groups if isinstance(group, dict))
    row_count = sum(len(report.get("case_ids", [])) for group in groups if isinstance(group, dict)
                    for report in group.get("reports", []) if isinstance(report, dict))
    if report_count != 92 or row_count != 4252:
        raise BenchmarkError("C4 baseline no longer preserves the 92 report partitions and 4,252 rows")
    if base.get("population") != {
            "fixture_revision": FIXTURE_REVISION,
            "path": BASE_POPULATION_REL,
            "sha256": BASE_POPULATION_SHA256,
    }:
        raise BenchmarkError("C4 baseline population reference changed")
    if base.get("parent_plan") != {"path": BASE_PLAN_REL, "sha256": BASE_PLAN_SHA256}:
        raise BenchmarkError("C4 baseline parent plan reference changed")
    if base.get("parent_execution_contract") != {
            "path": BASE_PARENT_EXECUTION_REL,
            "sha256": BASE_PARENT_EXECUTION_SHA256,
    }:
        raise BenchmarkError("C4 baseline parent execution reference changed")
    qualification = base.get("qualifications", {}).get("bifrost", {})
    ids = qualification.get("groups") if isinstance(qualification, dict) else None
    if ids != list(BIFROST_GROUP_IDS):
        raise BenchmarkError("C4 Bifrost qualification roster differs from the fixed 20-group target")
    bifrost = [group for group in groups if group.get("tool") == "bifrost"]
    if [group.get("id") for group in bifrost] != list(BIFROST_GROUP_IDS):
        raise BenchmarkError("C4 Bifrost group roster differs from the fixed 20-group target")
    if any(group.get("fixture_revision", FIXTURE_REVISION) != FIXTURE_REVISION for group in bifrost):
        raise BenchmarkError("C4 Bifrost groups have a different fixture revision")
    all_ids = [group.get("id") for group in groups]
    if any(not isinstance(group_id, str) for group_id in all_ids) or len(all_ids) != len(set(all_ids)):
        raise BenchmarkError("C4 full-population group IDs are malformed or duplicated")
    return plan, population, base, parent_execution, all_ids


def _group_sha256(group: dict) -> str:
    return _sha(_canonical_json(group))


def _runtime_argv(group: dict, runner_path: str, bifrost_path: str) -> list[str]:
    argv = group.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) for arg in argv):
        raise BenchmarkError(f"group {group.get('id')} has a malformed argv")
    if not Path(runner_path).is_absolute() or not Path(bifrost_path).is_absolute():
        raise BenchmarkError("runtime runner and Bifrost paths must be absolute")
    result = list(argv)
    result[0] = runner_path
    flags = [index for index, arg in enumerate(result) if arg == "--bifrost"]
    if len(flags) != 1 or flags[0] + 1 >= len(result):
        raise BenchmarkError(f"Bifrost group {group.get('id')} must have exactly one --bifrost path")
    result[flags[0] + 1] = bifrost_path
    if sum(1 for arg in result if arg == bifrost_path) != 1:
        raise BenchmarkError(f"Bifrost group {group.get('id')} runtime path substitution is ambiguous")
    return result


def project_target_groups(base_groups: Sequence[dict], runner_path: str, bifrost_path: str) -> list[dict]:
    """Copy only the fixed Bifrost roster and describe the two runtime substitutions."""
    selected = [group for group in base_groups if isinstance(group, dict) and group.get("tool") == "bifrost"]
    if [group.get("id") for group in selected] != list(BIFROST_GROUP_IDS):
        raise BenchmarkError("Bifrost target must use the exact canonical 20-group roster and order")
    projected = []
    for group in selected:
        env = group.get("environment")
        if not isinstance(env, dict) or env.get("BIFROST_OPEN_PACKS_DISABLE") != "1":
            raise BenchmarkError(f"group {group['id']} does not keep open-pack acquisition disabled")
        projected.append({
            "id": group["id"],
            "base_group_sha256": _group_sha256(group),
            "base_group": copy.deepcopy(group),
            "runtime_argv": _runtime_argv(group, runner_path, bifrost_path),
            "runtime_reports": [
                {**copy.deepcopy(report), "tool_version": BIFROST_REPORT_VERSION}
                for report in group.get("reports", [])
            ],
        })
    return projected


def validate_group_projections(projected: Sequence[dict], base_groups: Sequence[dict],
                               runner_path: str, bifrost_path: str) -> None:
    """Reject any C5 group change outside the two declared runtime path substitutions."""
    selected = [group for group in base_groups if isinstance(group, dict) and group.get("tool") == "bifrost"]
    if [group.get("id") for group in selected] != list(BIFROST_GROUP_IDS):
        raise BenchmarkError("baseline Bifrost roster is not the fixed 20-group roster")
    if not isinstance(projected, list) or len(projected) != len(BIFROST_GROUP_IDS):
        raise BenchmarkError("C5 must contain exactly 20 target group projections")
    for record, baseline in zip(projected, selected):
        if not isinstance(record, dict) or record.get("id") != baseline["id"]:
            raise BenchmarkError("C5 group membership or order differs from the baseline")
        if record.get("base_group") != baseline:
            raise BenchmarkError(f"C5 changed baseline group fields for {baseline['id']}")
        if record.get("base_group_sha256") != _group_sha256(baseline):
            raise BenchmarkError(f"C5 baseline group digest differs for {baseline['id']}")
        if record.get("runtime_argv") != _runtime_argv(baseline, runner_path, bifrost_path):
            raise BenchmarkError(f"C5 argv structure or runtime substitution differs for {baseline['id']}")
        expected_reports = [
            {**copy.deepcopy(report), "tool_version": BIFROST_REPORT_VERSION}
            for report in baseline.get("reports", [])
        ]
        if record.get("runtime_reports") != expected_reports:
            raise BenchmarkError(f"C5 report projection changed more than the Bifrost tool version for {baseline['id']}")
        if baseline.get("environment", {}).get("BIFROST_OPEN_PACKS_DISABLE") != "1":
            raise BenchmarkError(f"C5 baseline Bifrost process can acquire open packs: {baseline['id']}")
        if type(baseline.get("deadline_seconds")) is not int or baseline["deadline_seconds"] <= 0:
            raise BenchmarkError(f"C5 inherited deadline is invalid for {baseline['id']}")
        if baseline.get("maximum_attempts") != 2:
            raise BenchmarkError(f"C5 inherited per-group budget changed for {baseline['id']}")


def approval_subject_sha256(contract: dict) -> str:
    """Hash all reviewable contract content while excluding only approval fields."""
    subject = copy.deepcopy(contract)
    for field in ("approval", "execution_authorized", "approval_subject_sha256"):
        subject.pop(field, None)
    return _sha(_canonical_json(subject))


def validate_approval(contract: dict, *, required: bool) -> None:
    if not required:
        if contract.get("execution_authorized") is not False or contract.get("approval") is not None:
            raise BenchmarkError("prepared manifest must remain unapproved")
        return
    if contract.get("execution_authorized") is not True:
        raise BenchmarkError("C5 manifest is not explicitly execution-authorized")
    approval = contract.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        raise BenchmarkError("C5 manifest lacks the root-reviewed approval record")
    if approval.get("subject_sha256") != approval_subject_sha256(contract):
        raise BenchmarkError("C5 approval does not bind the current reviewable manifest content")
    if not isinstance(approval.get("approved_by"), str) or not approval["approved_by"].strip():
        raise BenchmarkError("C5 approval lacks an approver identity")
    approved_at = approval.get("approved_at_utc")
    try:
        parsed = dt.datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone missing")
    except (AttributeError, TypeError, ValueError) as exc:
        raise BenchmarkError("C5 approval timestamp must be timezone-aware UTC") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise BenchmarkError("C5 approval timestamp must use UTC")


def validate_resource_policy(policy: dict) -> None:
    if policy != RESOURCE_POLICY:
        raise BenchmarkError("C5 resource gates differ from the approved launch/continuous/reserve limits")


NATIVE_EVIDENCE_PATHS = {
    "help_stdout": "reports/releases/v0.9.2/acquisition/bifrost-v0144-01/help.stdout.txt",
    "controls_identity_version_stdout": "reports/releases/v0.9.2/qualification/bifrost-v0144-01/controls-attempt-01/stdout/identity-version.txt",
    "controls_identity_build_stdout": "reports/releases/v0.9.2/qualification/bifrost-v0144-01/controls-attempt-01/stdout/identity-build.txt",
    "controls_catalog_list_stdout": "reports/releases/v0.9.2/qualification/bifrost-v0144-01/controls-attempt-01/stdout/catalog-list-policies.txt",
    "pin_profile": PIN_PROFILE_PATH,
}
NATIVE_EVIDENCE_ROLES = tuple(NATIVE_EVIDENCE_PATHS)

# This is intentionally a closed data-only surface. Target wrappers may bind
# version identities and evidence paths/hashes in an isolated module instance;
# execution budgets, case/group rosters, resource admission, clock origins,
# qualification semantics, and attempt behavior remain code-owned.
TARGET_PROFILE_GLOBALS = (
    "TARGET_ID", "CONTRACT_SCHEMA", "SERIES", "SERIES_LABEL",
    "TARGET_HELP_DESCRIPTION",
    "CONTRACT_REL", "PROGRESS_REL", "SUMMARY_REL", "INVOCATIONS_REL",
    "QUALIFICATION_DEFAULT", "CONTROL_REVIEW_DEFAULT", "INDEPENDENT_REVIEW_DEFAULT",
    "CONTROL_CAPTURE_DEFAULT", "HUMAN_AUTHORIZATION_DEFAULT", "BIFROST_RECEIPT_DEFAULT",
    "BIFROST_PATH_DEFAULT", "RUNNER_PATH_DEFAULT", "RUNNER_BUILD_RECEIPT",
    "RUNNER_BUILD_INPUTS", "RUNNER_BUILD_STDOUT", "RUNNER_BUILD_STDERR",
    "RUNNER_CARGO_TARGET_DIR", "LEDGER_PREFIX_LINES", "LEDGER_PREFIX_SHA256",
    "BIFROST_VERSION", "BIFROST_REPORT_VERSION", "BIFROST_BUILD_IDENTITY",
    "BIFROST_CATALOG_SHA256", "BIFROST_BINARY_SHA256", "BIFROST_ARCHIVE_SHA256",
    "BIFROST_RECEIPT_SHA256", "PUBLIC_BIFROST_TAG_COMMIT", "QUALIFICATION_SHA256",
    "CONTROL_REVIEW_SHA256", "INDEPENDENT_REVIEW_SHA256", "CAPTURE_MANIFEST_SHA256",
    "CAPTURE_QUALIFICATION_SHA256", "RUNNER_BINARY_SHA256", "RUNNER_BUILD_RECEIPT_SHA256",
    "RUNNER_BINARY_BYTES", "RUNNER_BUILD_INPUTS_SHA256", "RUNNER_BUILD_STDOUT_SHA256",
    "RUNNER_BUILD_STDERR_SHA256",
    "BIFROST_CONTROL_REVIEW_SCHEMA", "INDEPENDENT_REVIEW_SCHEMA", "REVIEW_IMPLEMENTATION_PATH",
    "CONTROL_COMPARISON_DIAGNOSTIC_PATH", "PIN_PROFILE_PATH",
    "PIN_PROFILE_NATIVE_EVIDENCE_DIRECTORY", "TARGET_DRIVER_SOURCE_REL",
    "TARGET_TEST_SOURCE_REL", "CORE_SOURCE_REL", "PROFILE_SOURCE_REL",
    "ATTEMPT_RECEIPT_SCHEMA", "PROGRESS_SCHEMA", "INVOCATION_SCHEMA",
    "SERIES_SUMMARY_SCHEMA", "RECONCILIATION_SCHEMA", "NATIVE_EVIDENCE_PATHS",
)


class TargetProfile:
    """Immutable, exact target-specific evidence identities and repository paths."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, object]):
        copied = copy.deepcopy(dict(values))
        if isinstance(copied.get("NATIVE_EVIDENCE_PATHS"), dict):
            copied["NATIVE_EVIDENCE_PATHS"] = MappingProxyType(copied["NATIVE_EVIDENCE_PATHS"])
        object.__setattr__(self, "_values", MappingProxyType(copied))

    @property
    def values(self) -> Mapping[str, object]:
        return self._values

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("TargetProfile is immutable")


def current_target_profile_values() -> dict[str, object]:
    """Return the current instance's version-data defaults as a detached mapping."""
    return {name: copy.deepcopy(globals()[name]) for name in TARGET_PROFILE_GLOBALS}


def make_target_profile(overrides: Mapping[str, object]) -> TargetProfile:
    """Apply only keys in the closed target-data surface to current defaults."""
    if not isinstance(overrides, Mapping):
        raise BenchmarkError("target profile overrides must be a mapping")
    unknown = set(overrides) - set(TARGET_PROFILE_GLOBALS)
    if unknown:
        raise BenchmarkError(f"target profile contains non-data or unknown fields: {sorted(unknown)}")
    values = current_target_profile_values()
    values.update(copy.deepcopy(dict(overrides)))
    return TargetProfile(values)


def configure_target_profile(profile: TargetProfile) -> None:
    """Bind a validated profile's data into this isolated module instance."""
    if not isinstance(profile, TargetProfile) or set(profile.values) != set(TARGET_PROFILE_GLOBALS):
        raise BenchmarkError("target profile is incomplete or was not constructed by the closed profile API")
    for name in TARGET_PROFILE_GLOBALS:
        expected = globals()[name]
        value = profile.values[name]
        if name == "NATIVE_EVIDENCE_PATHS":
            if not isinstance(value, Mapping) or set(value) != set(expected):
                raise BenchmarkError("target native evidence roles differ from the fixed role set")
            if any(not isinstance(path, str) or not path for path in value.values()):
                raise BenchmarkError("target native evidence paths must be non-empty strings")
            globals()[name] = dict(value)
            continue
        if isinstance(expected, bool):
            valid_type = type(value) is bool
        elif expected is None:
            valid_type = value is None or isinstance(value, str)
        else:
            valid_type = type(value) is type(expected)
        if not valid_type:
            raise BenchmarkError(f"target profile field {name} has the wrong type")
        globals()[name] = copy.deepcopy(value)

    if (not isinstance(SERIES, int) or SERIES < 1 or SERIES_LABEL != f"series-{SERIES:02d}" or
            type(RUNNER_BINARY_BYTES) is not int or
            not 0 < RUNNER_BINARY_BYTES <= 512 * 1024**2 or
            BIFROST_REPORT_VERSION != f"bifrost {BIFROST_VERSION}" or
            not COMMIT_RE.fullmatch(BIFROST_BUILD_IDENTITY) or
            not SHA256_RE.fullmatch(BIFROST_BINARY_SHA256) or
            not SHA256_RE.fullmatch(BIFROST_ARCHIVE_SHA256) or
            not SHA256_RE.fullmatch(BIFROST_CATALOG_SHA256) or
            not SHA256_RE.fullmatch(BIFROST_RECEIPT_SHA256) or
            not SHA256_RE.fullmatch(LEDGER_PREFIX_SHA256) or LEDGER_PREFIX_LINES < 1):
        raise BenchmarkError("target profile identity, series, or ledger-prefix binding is invalid")
    for name in (
        "QUALIFICATION_SHA256", "CONTROL_REVIEW_SHA256", "INDEPENDENT_REVIEW_SHA256",
        "CAPTURE_MANIFEST_SHA256", "CAPTURE_QUALIFICATION_SHA256", "RUNNER_BINARY_SHA256",
        "RUNNER_BUILD_RECEIPT_SHA256", "RUNNER_BUILD_INPUTS_SHA256",
        "RUNNER_BUILD_STDOUT_SHA256", "RUNNER_BUILD_STDERR_SHA256",
    ):
        if not SHA256_RE.fullmatch(str(globals()[name])):
            raise BenchmarkError(f"target profile evidence hash is missing or invalid: {name}")
    if not COMMIT_RE.fullmatch(PUBLIC_BIFROST_TAG_COMMIT):
        raise BenchmarkError("target profile lacks the exact public Bifrost tag commit")
    for name in (
        "CONTRACT_REL", "PROGRESS_REL", "SUMMARY_REL", "INVOCATIONS_REL",
        "QUALIFICATION_DEFAULT", "CONTROL_REVIEW_DEFAULT", "INDEPENDENT_REVIEW_DEFAULT",
        "CONTROL_CAPTURE_DEFAULT", "HUMAN_AUTHORIZATION_DEFAULT", "BIFROST_RECEIPT_DEFAULT",
        "BIFROST_PATH_DEFAULT", "RUNNER_BUILD_RECEIPT", "RUNNER_BUILD_INPUTS",
        "RUNNER_BUILD_STDOUT", "RUNNER_BUILD_STDERR", "RUNNER_CARGO_TARGET_DIR",
        "REVIEW_IMPLEMENTATION_PATH", "CONTROL_COMPARISON_DIAGNOSTIC_PATH", "PIN_PROFILE_PATH",
        "TARGET_DRIVER_SOURCE_REL", "TARGET_TEST_SOURCE_REL",
    ):
        value = globals()[name]
        if not isinstance(value, str) or not value or PurePosixPath(value).is_absolute() or ".." in PurePosixPath(value).parts:
            raise BenchmarkError(f"target profile path is unsafe: {name}")

    global NATIVE_EVIDENCE_ROLES, ATTEMPT_POLICY, ALLOWED_RUNTIME_PROJECTIONS
    NATIVE_EVIDENCE_ROLES = tuple(NATIVE_EVIDENCE_PATHS)
    ATTEMPT_POLICY = dict(ATTEMPT_POLICY, series=SERIES, series_label=SERIES_LABEL)
    ALLOWED_RUNTIME_PROJECTIONS = {
        "argv": ["argv[0] = pinned optimized harness binary",
                 f"the value following the single --bifrost flag = acquired v{BIFROST_VERSION} binary"],
        "report_identity": [f"tool_version changes from frozen C4 Bifrost version to {BIFROST_REPORT_VERSION}"],
        "scala_maven": ["the exact pinned binary jar, sources jar, and POM are staged into only the Scala attempt HOME"],
        "all_baseline_group_policy_case_ids_reports_paths_deadlines_and_attempt_budgets_retained": True,
    }


LEGACY_TARGET_PROFILE = TargetProfile(current_target_profile_values())


def _verify_bifrost_receipt(root: Path, value: str | Path) -> tuple[dict, dict]:
    relative, path, raw = _path_ref(root, value, "Bifrost acquisition receipt")
    if relative.as_posix() != BIFROST_RECEIPT_DEFAULT:
        raise BenchmarkError(f"C5 must use the pinned {BIFROST_REPORT_VERSION} acquisition receipt path")
    if _sha(raw) != BIFROST_RECEIPT_SHA256:
        raise BenchmarkError(f"{BIFROST_REPORT_VERSION} acquisition receipt hash changed")
    receipt, _ = _read_json(path, "Bifrost acquisition receipt")
    binary = receipt.get("binary")
    if not isinstance(binary, dict):
        raise BenchmarkError("Bifrost acquisition receipt has no binary identity")
    expected_path = (root / BIFROST_PATH_DEFAULT).resolve()
    actual_path = Path(str(binary.get("path", "")))
    if not actual_path.is_absolute() or actual_path.resolve(strict=False) != expected_path:
        raise BenchmarkError("Bifrost acquisition receipt points at a different binary path")
    if (binary.get("sha256") != BIFROST_BINARY_SHA256 or
            binary.get("version_output", "").splitlines()[:1] != [BIFROST_REPORT_VERSION] or
            binary.get("build_identity_output", "").strip() != BIFROST_BUILD_IDENTITY):
        raise BenchmarkError(f"Bifrost acquisition receipt identity differs from pinned {BIFROST_REPORT_VERSION}")
    archive = receipt.get("assets", {}).get("macos_universal_archive", {})
    if archive.get("local", {}).get("sha256") != BIFROST_ARCHIVE_SHA256:
        raise BenchmarkError("Bifrost source archive identity differs from the official release asset")
    if receipt.get("source", {}).get("public_tag_commit") != PUBLIC_BIFROST_TAG_COMMIT:
        raise BenchmarkError("Bifrost public tag commit differs from the acquired release")
    if binary.get("build_identity_equals_public_tag_commit") is not False:
        raise BenchmarkError("Bifrost build identity must remain distinct from the public tag commit")
    if not expected_path.is_file() or expected_path.is_symlink() or _sha_file(expected_path) != BIFROST_BINARY_SHA256:
        raise BenchmarkError("acquired Bifrost binary is missing or differs from its pinned SHA-256")
    binding = {
        "path": str(expected_path),
        "sha256": BIFROST_BINARY_SHA256,
        "version": BIFROST_VERSION,
        "report_version": BIFROST_REPORT_VERSION,
        "build_identity": BIFROST_BUILD_IDENTITY,
        "builtin_policy_catalog_sha256": BIFROST_CATALOG_SHA256,
        "official_release_tag_commit": PUBLIC_BIFROST_TAG_COMMIT,
        "archive_sha256": BIFROST_ARCHIVE_SHA256,
        "receipt": {"path": relative.as_posix(), "sha256": _sha(raw)},
    }
    return receipt, binding


def _verify_scala_receipt(root: Path, value: str | Path) -> tuple[dict, dict]:
    relative, path, raw = _path_ref(root, value, "Scala Maven acquisition receipt")
    if relative.as_posix() != SCALA_RECEIPT_DEFAULT:
        raise BenchmarkError("C5 must use the pinned Scala 2.13.16 acquisition receipt path")
    if _sha(raw) != SCALA_RECEIPT_SHA256:
        raise BenchmarkError("Scala 2.13.16 acquisition receipt hash changed")
    receipt, _ = _read_json(path, "Scala Maven acquisition receipt")
    if receipt.get("identity") != {
            "artifactId": "scala-library",
            "groupId": "org.scala-lang",
            "packaging": "jar",
            "pom_identity_verified": True,
            "version": "2.13.16",
    }:
        raise BenchmarkError("Scala Maven receipt does not bind scala-library 2.13.16")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        raise BenchmarkError("Scala Maven receipt must bind the binary jar, sources jar, and upstream POM")
    by_name = {Path(item.get("repository_path", "")).name: item for item in artifacts if isinstance(item, dict)}
    if set(by_name) != set(SCALA_FILES):
        raise BenchmarkError("Scala Maven receipt has a different artifact set")
    repository_root = (root / SCALA_REPOSITORY_DEFAULT).resolve()
    runtime_artifacts = []
    for name, expected in SCALA_FILES.items():
        item = by_name[name]
        artifact = root / item["repository_path"]
        if not artifact.resolve(strict=False).is_relative_to(repository_root):
            raise BenchmarkError(f"Scala artifact escapes its pinned Maven repository: {name}")
        if (item.get("role") != expected["role"] or item.get("sha256") != expected["sha256"] or
                item.get("size_bytes") != expected["size_bytes"]):
            raise BenchmarkError(f"Scala Maven receipt pin differs for {name}")
        if not artifact.is_file() or artifact.is_symlink() or artifact.stat().st_size != expected["size_bytes"]:
            raise BenchmarkError(f"Scala Maven artifact is missing or has an unexpected size: {artifact}")
        if _sha_file(artifact) != expected["sha256"]:
            raise BenchmarkError(f"Scala Maven artifact SHA-256 differs: {artifact}")
        runtime_artifacts.append({
            "name": name,
            "role": expected["role"],
            "source_path": str(artifact.resolve()),
            "repository_path": item["repository_path"],
            "sha256": expected["sha256"],
            "size_bytes": expected["size_bytes"],
            "publisher_checksum": item.get("publisher_checksum"),
        })
    availability = receipt.get("source_availability")
    if not isinstance(availability, dict) or availability.get("http_status") != "200" or not availability.get("downloaded"):
        raise BenchmarkError("Scala sources jar is not recorded as downloaded from Maven Central")
    if type(availability.get("scala_source_entry_count")) is not int or availability["scala_source_entry_count"] < 1:
        raise BenchmarkError("Scala sources jar has no recorded source entries")
    return receipt, {
        "group_id": "org.scala-lang",
        "artifact_id": "scala-library",
        "version": "2.13.16",
        "repository_root": str(repository_root),
        "receipt": {"path": relative.as_posix(), "sha256": _sha(raw)},
        "artifacts": runtime_artifacts,
        "source_entry_count": availability["scala_source_entry_count"],
    }


def _verify_runner_binary_binding(root: Path, binary: object, runner_path: str | Path) -> Path:
    binary_path = root / RUNNER_PATH_DEFAULT
    if (not isinstance(binary, dict) or binary.get("path") != RUNNER_PATH_DEFAULT or
            binary.get("sha256") != RUNNER_BINARY_SHA256 or binary.get("bytes") != RUNNER_BINARY_BYTES or
            Path(runner_path).resolve(strict=False) != binary_path.resolve(strict=False)):
        raise BenchmarkError("optimized harness build receipt identifies a different executable")
    if (binary_path.is_symlink() or not binary_path.is_file() or
            binary_path.stat().st_size != RUNNER_BINARY_BYTES or _sha_file(binary_path) != RUNNER_BINARY_SHA256):
        raise BenchmarkError("optimized harness executable differs from the recorded build artifact")
    return binary_path


def _verify_runner_build(root: Path, source_commit: str, runner_path: str | Path) -> dict:
    receipt_path = root / RUNNER_BUILD_RECEIPT
    inputs_path = root / RUNNER_BUILD_INPUTS
    stdout_path = root / RUNNER_BUILD_STDOUT
    stderr_path = root / RUNNER_BUILD_STDERR
    expected = {
        RUNNER_BUILD_RECEIPT: RUNNER_BUILD_RECEIPT_SHA256,
        RUNNER_BUILD_INPUTS: RUNNER_BUILD_INPUTS_SHA256,
        RUNNER_BUILD_STDOUT: RUNNER_BUILD_STDOUT_SHA256,
        RUNNER_BUILD_STDERR: RUNNER_BUILD_STDERR_SHA256,
    }
    for relative, digest in expected.items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or _sha_file(path) != digest:
            raise BenchmarkError(f"optimized harness build evidence changed: {relative}")
    receipt, _ = _read_json(receipt_path, "optimized harness build receipt")
    try:
        source_inputs = json.loads(inputs_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("optimized harness source-input receipt is invalid JSON") from exc
    binary_path = root / RUNNER_PATH_DEFAULT
    if (receipt.get("argv", [])[1:] != ["build", "--release", "--locked"] or
            receipt.get("exit_code") != 0 or receipt.get("jobs") != 2 or
            receipt.get("source_inputs_sha256") != RUNNER_BUILD_INPUTS_SHA256 or
            receipt.get("stdout_sha256") != RUNNER_BUILD_STDOUT_SHA256 or
            receipt.get("stderr_sha256") != RUNNER_BUILD_STDERR_SHA256 or
            receipt.get("cargo_target_dir") != RUNNER_CARGO_TARGET_DIR):
        raise BenchmarkError("optimized harness build receipt does not match the reviewed release build")
    binary = receipt.get("binary")
    binary_path = _verify_runner_binary_binding(root, binary, runner_path)
    if not isinstance(source_inputs, list) or not source_inputs:
        raise BenchmarkError("optimized harness build source-input list is empty or malformed")
    build_hashes = {}
    for item in source_inputs:
        if (not isinstance(item, dict) or not isinstance(item.get("path"), str) or
                not SHA256_RE.fullmatch(str(item.get("sha256")))):
            raise BenchmarkError("optimized harness source-input entry is malformed")
        relative = _repo_relative(root, item["path"], "optimized harness source input").as_posix()
        if relative in build_hashes:
            raise BenchmarkError(f"optimized harness source input is duplicated: {relative}")
        build_hashes[relative] = item["sha256"]
    expected_names = set(_git(root, "ls-tree", "-r", "--name-only", source_commit, "--", "src").splitlines())
    expected_names.update(("Cargo.toml", "Cargo.lock"))
    if set(build_hashes) != expected_names:
        raise BenchmarkError("optimized harness build source inputs do not cover exactly SOURCE Cargo and Rust files")
    archive = subprocess.Popen(
        ["git", "archive", "--format=tar", source_commit, "--", "Cargo.toml", "Cargo.lock", "src"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert archive.stdout is not None
    archive_hashes = {}
    archive_bytes = 0
    try:
        with tarfile.open(fileobj=archive.stdout, mode="r|") as stream:
            for member in stream:
                member_path = PurePosixPath(member.name)
                if member_path.is_absolute() or any(part in ("", ".", "..") for part in member_path.parts):
                    raise BenchmarkError(f"unsafe path in SOURCE archive: {member.name}")
                if member.isdir():
                    continue
                if not member.isfile() or member_path.as_posix() not in expected_names:
                    raise BenchmarkError(f"unexpected non-file in harness SOURCE archive: {member.name}")
                archive_bytes += member.size
                if archive_bytes > 3 * 1024**3:
                    raise BenchmarkError("harness SOURCE archive exceeded the bounded 3 GiB limit")
                content = stream.extractfile(member)
                if content is None:
                    raise BenchmarkError(f"cannot read SOURCE archive member {member.name}")
                digest = hashlib.sha256()
                for chunk in iter(lambda: content.read(1024 * 1024), b""):
                    digest.update(chunk)
                archive_hashes[member_path.as_posix()] = digest.hexdigest()
    finally:
        _stdout, stderr = archive.communicate()
    if archive.returncode != 0:
        raise BenchmarkError(f"cannot archive optimized harness SOURCE: {stderr.decode(errors='replace').strip()}")
    if archive_hashes != build_hashes:
        raise BenchmarkError("optimized harness build input hashes do not match exact SOURCE Git blobs")
    return {
        "receipt": {"path": RUNNER_BUILD_RECEIPT, "sha256": RUNNER_BUILD_RECEIPT_SHA256},
        "source_inputs": {"path": RUNNER_BUILD_INPUTS, "sha256": RUNNER_BUILD_INPUTS_SHA256,
                          "count": len(build_hashes), "git_archive_matches_source_commit": True},
        "stdout": {"path": RUNNER_BUILD_STDOUT, "sha256": RUNNER_BUILD_STDOUT_SHA256},
        "stderr": {"path": RUNNER_BUILD_STDERR, "sha256": RUNNER_BUILD_STDERR_SHA256},
        "argv": receipt["argv"], "exit_code": 0, "jobs": 2,
        "binary": {"path": str(binary_path.resolve()), "sha256": RUNNER_BINARY_SHA256,
                   "bytes": RUNNER_BINARY_BYTES},
        "source_archive_bytes": archive_bytes,
    }


def _qualification_group_ids(value: object) -> list[str]:
    if isinstance(value, dict):
        return list(value)
    if not isinstance(value, list):
        raise BenchmarkError("qualification groups must be a list or object")
    ids = []
    for item in value:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict):
            group_id = item.get("id", item.get("group_id"))
            if not isinstance(group_id, str):
                raise BenchmarkError("qualification group entry lacks an id")
            ids.append(group_id)
        else:
            raise BenchmarkError("qualification groups contain an unsupported entry")
    return ids


def _verify_qualification(root: Path, value: str | Path, bifrost_binding: dict) -> tuple[dict, dict]:
    relative, path, raw = _path_ref(root, value, "Bifrost qualification")
    if relative.as_posix() != QUALIFICATION_DEFAULT:
        raise BenchmarkError(f"C5 must use the fresh {BIFROST_REPORT_VERSION} qualification path")
    if _sha(raw) != QUALIFICATION_SHA256:
        raise BenchmarkError(f"fresh {BIFROST_REPORT_VERSION} qualification hash changed")
    qualification, _ = _read_json(path, "Bifrost qualification")
    if (qualification.get("schema") != "v092-bifrost-release-qualification/v1" or
            qualification.get("status") != "measurement-with-known-limits" or
            qualification.get("execution_eligible") is not True or
            qualification.get("full_policy_qualification") is not False):
        raise BenchmarkError("Bifrost qualification must remain typed as limited measurement coverage")
    if _qualification_group_ids(qualification.get("groups")) != list(BIFROST_GROUP_IDS):
        raise BenchmarkError("Bifrost qualification does not cover exactly the 20 target groups")
    tool = qualification.get("tool")
    if not isinstance(tool, dict):
        raise BenchmarkError("Bifrost qualification has no exact tool binding")
    if (tool.get("path") != bifrost_binding["path"] or
            tool.get("sha256") != BIFROST_BINARY_SHA256 or
            tool.get("build_identity") != BIFROST_BUILD_IDENTITY or
            tool.get("version") not in (BIFROST_VERSION, BIFROST_REPORT_VERSION)):
        raise BenchmarkError(f"Bifrost qualification does not match the pinned {BIFROST_REPORT_VERSION} artifact")
    if qualification.get("identity_components") != []:
        raise BenchmarkError("Bifrost qualification has unexpected component/control coverage")
    control_ref = qualification.get("control_review")
    capture_ref = qualification.get("capture")
    auth_ref = qualification.get("authorization")
    scope_ref = qualification.get("scope_source")
    impl_ref = qualification.get("binding_implementation")
    append_ref = qualification.get("append_after_ledger")
    if not all(isinstance(item, dict) for item in
               (control_ref, capture_ref, auth_ref, scope_ref, impl_ref, append_ref)):
        raise BenchmarkError("Bifrost qualification is missing a required review/capture/authority binding")
    if control_ref.get("path") != CONTROL_REVIEW_DEFAULT or control_ref.get("sha256") != CONTROL_REVIEW_SHA256:
        raise BenchmarkError("Bifrost qualification points at an unexpected independent review")
    capture_path = CONTROL_CAPTURE_DEFAULT
    if (capture_ref.get("path") != capture_path or
            capture_ref.get("manifest_sha256") != CAPTURE_MANIFEST_SHA256 or
            capture_ref.get("qualification_sha256") != CAPTURE_QUALIFICATION_SHA256):
        raise BenchmarkError("Bifrost qualification points at an unexpected control capture")
    expected_bound_files = {
        CONTROL_REVIEW_DEFAULT: CONTROL_REVIEW_SHA256,
        f"{capture_path}/artifact-hashes.json": CAPTURE_MANIFEST_SHA256,
        f"{capture_path}/qualification.json": CAPTURE_QUALIFICATION_SHA256,
        HUMAN_AUTHORIZATION_DEFAULT: None,
        BASE_PARENT_EXECUTION_REL: BASE_PARENT_EXECUTION_SHA256,
        LEDGER_REL: None,
    }
    for relative_path, expected_sha in expected_bound_files.items():
        bound_path = root / relative_path
        if bound_path.is_symlink() or not bound_path.is_file():
            raise BenchmarkError(f"required qualification evidence is missing or unsafe: {relative_path}")
        actual_sha = _sha_file(bound_path)
        if expected_sha is not None and actual_sha != expected_sha:
            raise BenchmarkError(f"required qualification evidence changed: {relative_path}")
    if auth_ref.get("path") != HUMAN_AUTHORIZATION_DEFAULT or auth_ref.get("sha256") != _sha_file(root / HUMAN_AUTHORIZATION_DEFAULT):
        raise BenchmarkError("Bifrost qualification authority reference is inconsistent")
    if scope_ref.get("path") != BASE_PARENT_EXECUTION_REL or scope_ref.get("sha256") != BASE_PARENT_EXECUTION_SHA256:
        raise BenchmarkError("Bifrost qualification scope reference is inconsistent")
    if (append_ref.get("path") != LEDGER_REL or append_ref.get("rows") != LEDGER_PREFIX_LINES or
            append_ref.get("sha256") != LEDGER_PREFIX_SHA256):
        raise BenchmarkError("Bifrost qualification append authority no longer matches the ledger prefix")
    if not isinstance(impl_ref.get("path"), str) or not isinstance(impl_ref.get("sha256"), str):
        raise BenchmarkError("qualification binding implementation reference is malformed")
    impl_relative = _repo_relative(root, impl_ref["path"], "qualification binding implementation")
    impl_path = root.joinpath(*impl_relative.parts)
    if impl_path.is_symlink() or not impl_path.is_file() or _sha_file(impl_path) != impl_ref["sha256"]:
        raise BenchmarkError("qualification binding implementation hash differs")
    review, _review_raw = _read_json(root / CONTROL_REVIEW_DEFAULT, "fresh Bifrost control review")
    if (review.get("schema") != BIFROST_CONTROL_REVIEW_SCHEMA or
            review.get("status") != "measurement-with-known-limits" or
            review.get("execution_eligible") is not True or
            review.get("full_policy_qualification") is not False or
            review.get("invocations") != 44 or
            review.get("native", {}).get("interpretation") != "not-evaluated" or
            review.get("native", {}).get("clean") is not False or
            review.get("tool", {}).get("sha256") != BIFROST_BINARY_SHA256 or
            review.get("tool", {}).get("build_identity") != BIFROST_BUILD_IDENTITY):
        raise BenchmarkError("fresh Bifrost control review identity or coverage is invalid")
    review_refs = {
        "acquisition_receipt": (BIFROST_RECEIPT_DEFAULT, BIFROST_RECEIPT_SHA256),
        "capture_manifest": (f"{capture_path}/artifact-hashes.json", CAPTURE_MANIFEST_SHA256),
        "human_authorization": (HUMAN_AUTHORIZATION_DEFAULT, None),
        "original_qualification": (capture_path, CAPTURE_QUALIFICATION_SHA256),
    }
    for role, (expected_path, expected_sha) in review_refs.items():
        ref = review.get(role)
        if not isinstance(ref, dict) or ref.get("path") != expected_path:
            raise BenchmarkError(f"fresh Bifrost control review has an incorrect {role} reference")
        target = root / expected_path
        digest = _sha_file(target / "qualification.json") if role == "original_qualification" else _sha_file(target)
        if ref.get("sha256") != digest or (expected_sha is not None and digest != expected_sha):
            raise BenchmarkError(f"fresh Bifrost control review has a stale {role} digest")
    review_implementation = review.get("review_implementation")
    if (not isinstance(review_implementation, dict) or
            review_implementation.get("path") != REVIEW_IMPLEMENTATION_PATH):
        raise BenchmarkError("fresh Bifrost control review lacks its exact reviewer implementation reference")
    review_implementation_path = root / review_implementation["path"]
    if (review_implementation_path.is_symlink() or not review_implementation_path.is_file() or
            _sha_file(review_implementation_path) != review_implementation.get("sha256")):
        raise BenchmarkError("fresh Bifrost review implementation hash differs")
    capture_qualification, _capture_qualification_raw = _read_json(
        root / f"{capture_path}/qualification.json", "strict Bifrost control capture")
    if (capture_qualification.get("invocations") != 44 or
            capture_qualification.get("completed_invocations") != 44 or
            capture_qualification.get("failed_invocations") != 0 or
            capture_qualification.get("qualification") != "failed" or
            capture_qualification.get("tool", {}).get("sha256") != BIFROST_BINARY_SHA256 or
            capture_qualification.get("tool", {}).get("build_identity") != BIFROST_BUILD_IDENTITY):
        raise BenchmarkError("strict control capture counters or identity changed")
    commands_path = root / f"{capture_path}/commands.jsonl"
    command_rows = []
    with commands_path.open("rb") as commands:
        for raw_command in commands:
            if not raw_command.endswith(b"\n"):
                raise BenchmarkError("strict control command manifest has a truncated row")
            command_rows.append(json.loads(raw_command))
    if (len(command_rows) != 44 or
            any(row.get("status") != "completed" or row.get("exit_code") != 0 for row in command_rows)):
        raise BenchmarkError("strict control capture no longer records exactly 44 completed zero-exit commands")
    if qualification.get("strict_capture") != review.get("strict_capture"):
        raise BenchmarkError("qualification strict-capture summary differs from the independent control review")
    independent_review, _independent_raw = _read_json(root / INDEPENDENT_REVIEW_DEFAULT,
                                                        f"independent {BIFROST_REPORT_VERSION} review")
    if (independent_review.get("schema") != INDEPENDENT_REVIEW_SCHEMA or
            independent_review.get("execution_eligible") is not True or
            independent_review.get("full_policy_qualification") is not False or
            independent_review.get("summary", {}).get("report_roster") != 39 or
            independent_review.get("summary", {}).get("current_completion_counts") !=
            {"complete": 36, "inconclusive": 3}):
        raise BenchmarkError(f"independent {BIFROST_REPORT_VERSION} review does not preserve its limited 39-report result")
    if _sha_file(root / INDEPENDENT_REVIEW_DEFAULT) != INDEPENDENT_REVIEW_SHA256:
        raise BenchmarkError(f"independent {BIFROST_REPORT_VERSION} review hash changed")
    independent_refs = independent_review.get("evidence_refs", {})
    expected_independent = {
        "cli_help": (NATIVE_EVIDENCE_PATHS["help_stdout"], None),
        "comparison_diagnostic": (CONTROL_COMPARISON_DIAGNOSTIC_PATH, None),
        "current_capture_manifest": (f"{capture_path}/artifact-hashes.json", CAPTURE_MANIFEST_SHA256),
        "current_commands": (f"{capture_path}/commands.jsonl", None),
        "current_qualification_receipt": (f"{capture_path}/qualification.json", CAPTURE_QUALIFICATION_SHA256),
        "historical_capture_manifest": ("reports/releases/v0.9.2/qualification/bifrost-v0140-01/controls-attempt-01/artifact-hashes.json", None),
        "historical_review": ("reports/releases/v0.9.2/qualification/bifrost-v0140-01/control-review-01.json", None),
    }
    independent_ref_paths = []
    for role, (expected_path, expected_sha) in expected_independent.items():
        ref = independent_refs.get(role)
        if not isinstance(ref, dict) or ref.get("path") != expected_path:
            raise BenchmarkError(f"independent Bifrost review has an incorrect {role} reference")
        target = root / expected_path
        if target.is_symlink() or not target.is_file():
            raise BenchmarkError(f"independent Bifrost review evidence is missing: {expected_path}")
        digest = _sha_file(target)
        if ref.get("sha256") != digest or (expected_sha is not None and digest != expected_sha):
            raise BenchmarkError(f"independent Bifrost review evidence digest changed: {expected_path}")
        independent_ref_paths.append(expected_path)
    if (independent_refs["current_commands"].get("command_count") != 44 or
            independent_refs["current_commands"].get("all_44_exit_code_0") is not True or
            independent_refs["current_commands"].get("all_44_status_completed") is not True or
            independent_refs["current_capture_manifest"].get("all_reports_bound") is not True or
            independent_refs["current_capture_manifest"].get("listed_report_count") != 39 or
            independent_refs["current_capture_manifest"].get("actual_report_count") != 39):
        raise BenchmarkError("independent Bifrost review no longer binds all 39 reports and 44 commands")
    review_files = independent_review.get("source_review", {}).get("files")
    if (not isinstance(review_files, list) or not review_files or
            any(not isinstance(value, str) for value in review_files)):
        raise BenchmarkError("independent Bifrost source review lacks a file roster")
    refs = [relative.as_posix(), control_ref["path"], INDEPENDENT_REVIEW_DEFAULT,
            review_implementation["path"], *independent_ref_paths, *review_files,
            f"{capture_path}/artifact-hashes.json",
            f"{capture_path}/capture-context.json", f"{capture_path}/commands.jsonl",
            CONTROL_COMPARISON_DIAGNOSTIC_PATH,
            f"{capture_path}/qualification.json", auth_ref["path"], scope_ref["path"],
            impl_ref["path"]]
    return qualification, {
        "path": relative.as_posix(),
        "sha256": _sha(raw),
        "schema": qualification.get("schema"),
        "status": qualification.get("status"),
        "execution_eligible": True,
        "full_policy_qualification": qualification.get("full_policy_qualification"),
        "groups": list(BIFROST_GROUP_IDS),
        "control_review": {"path": control_ref["path"], "sha256": control_ref["sha256"]},
        "independent_review": {"path": INDEPENDENT_REVIEW_DEFAULT,
                               "sha256": INDEPENDENT_REVIEW_SHA256},
        "capture": {"path": capture_path, "manifest_sha256": capture_ref["manifest_sha256"],
                    "qualification_sha256": capture_ref["qualification_sha256"]},
        "authorization": {"path": auth_ref["path"], "sha256": auth_ref["sha256"]},
        "scope_source": {"path": scope_ref["path"], "sha256": scope_ref["sha256"]},
        "append_after_ledger": copy.deepcopy(append_ref),
        "binding_implementation": copy.deepcopy(impl_ref),
        "source_reference_paths": refs,
        "tool": {
            "path": bifrost_binding["path"],
            "sha256": BIFROST_BINARY_SHA256,
            "version": BIFROST_VERSION,
            "build_identity": BIFROST_BUILD_IDENTITY,
        },
    }


def _parse_role_ref(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise BenchmarkError("--native-evidence must use ROLE=REPOSITORY_PATH")
    role, path = raw.split("=", 1)
    if role not in NATIVE_EVIDENCE_ROLES or not path:
        raise BenchmarkError(f"unsupported native evidence role or empty path: {raw!r}")
    return role, path


def _source_input_paths(root: Path, base_contract: dict, refs: Iterable[str]) -> list[str]:
    # The C4 contract intentionally retains 1,712 historical inputs, including
    # archived raw outputs no longer present in SOURCE. Those paths remain in
    # historical working-capacity accounting, but are not current build inputs.
    # The immutable source tree is instead bound by SOURCE plus the core's
    # complete SNAPSHOT_DIRECTORIES/SNAPSHOT_FILES drift check.
    values = [
        BASE_PLAN_REL,
        BASE_POPULATION_REL,
        BASE_PARENT_EXECUTION_REL,
        BASE_CONTRACT_REL,
        TARGET_DRIVER_SOURCE_REL,
        TARGET_TEST_SOURCE_REL,
        "scripts/execute-release-v092.py",
        "scripts/v092_disk_guard.py",
        "scripts/swift_v2_scored_process.py",
        RUNNER_BUILD_RECEIPT,
        RUNNER_BUILD_INPUTS,
        RUNNER_BUILD_STDOUT,
        RUNNER_BUILD_STDERR,
    ]
    if CORE_SOURCE_REL is not None:
        values.append(CORE_SOURCE_REL)
    if PROFILE_SOURCE_REL is not None:
        values.append(PROFILE_SOURCE_REL)
    if TARGET_ID == "bifrost-v0151-01":
        # Successor publication validation executes these helpers as part of
        # the same reviewed source closure. Historical targets keep their
        # original finite roster when no versioned target profile is present.
        values.extend((
            "scripts/select-v092-publication-evidence.py",
            "scripts/test-select-v092-publication-evidence.py",
            "scripts/validate-v092-report-configurations.py",
            "scripts/test-validate-v092-report-configurations.py",
            "scripts/joern_v092_publication_projection.py",
            "scripts/joern_normal_reports_v092_projection.py",
            "scripts/test-joern-v092-publication-projection.py",
        ))
    values.extend(refs)
    unique = []
    for value in values:
        if not isinstance(value, str):
            raise BenchmarkError("baseline source_inputs contain a malformed path")
        normalized = _repo_relative(root, value, "source input path").as_posix()
        if normalized not in unique:
            unique.append(normalized)
    return unique


def _build_source_snapshot(root: Path, source_commit: str, base_contract: dict,
                           refs: Sequence[str], core_sha256: str) -> dict:
    inputs = []
    for relative in _source_input_paths(root, base_contract, refs):
        digest, size = _git_blob_sha256(root, source_commit, relative)
        inputs.append({"path": relative, "sha256": digest, "bytes": size})
    inputs_by_path = {item["path"]: item for item in inputs}
    runner_path = TARGET_DRIVER_SOURCE_REL
    test_path = TARGET_TEST_SOURCE_REL
    core_path = "scripts/execute-release-v092.py"
    disk_path = "scripts/v092_disk_guard.py"
    tracker_path = "scripts/swift_v2_scored_process.py"
    runner_sha = inputs_by_path[runner_path]["sha256"]
    test_sha = inputs_by_path[test_path]["sha256"]
    if _sha_file(root / runner_path) != runner_sha or _sha_file(root / test_path) != test_sha:
        raise BenchmarkError("new C5 runner or tests differ from the committed source snapshot")
    if inputs_by_path[core_path]["sha256"] != core_sha256:
        raise BenchmarkError("dynamic helper source differs from the exact source commit")
    core_helpers = [
        {"path": core_path, "sha256": core_sha256},
        {"path": disk_path, "sha256": inputs_by_path[disk_path]["sha256"]},
        {"path": tracker_path, "sha256": inputs_by_path[tracker_path]["sha256"]},
    ]
    if CORE_SOURCE_REL is not None:
        core_helpers.append({
            "path": CORE_SOURCE_REL,
            "sha256": inputs_by_path[CORE_SOURCE_REL]["sha256"],
        })
    return {
        "source_commit": source_commit,
        "closure_boundary": {
            "kind": "source-commit-plus-core-snapshot-paths-and-finite-current-inputs",
            "core_snapshot_paths": [
                "src", "cases", "populations", "adapters", "schemas", "scripts",
                "Cargo.toml", "Cargo.lock", "docs/v0.9.2-execution.md", "corpus",
                "README.md", "LICENSE", "docs/adapters.md",
                "reports/releases/v0.9.0/plan.json", "docs/benchmark-sources.md",
                "docs/challenge-tier.md", "docs/real-project-preregistration.md",
                "docs/real-project-r2-preregistration.md", "docs/real-project-review.md",
            ],
            "historical_c4_source_inputs_retained_for_capacity_accounting": len(base_contract.get("source_inputs", [])),
            "historical_inputs_are_not_reclassified_as_current_compile_inputs": True,
        },
        "source_inputs": inputs,
        "historical_c4_source_inputs": copy.deepcopy(base_contract.get("source_inputs", [])),
        "runner_source": {"path": runner_path, "sha256": runner_sha},
        "test_source": {"path": test_path, "sha256": test_sha},
        "core_helpers": core_helpers,
    }


def _atomic_write(path: Path, data: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}-{time.time_ns()}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise BenchmarkError(f"short durable write to {temporary}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if exclusive:
        try:
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    else:
        os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _make_manifest(root: Path, *, source_commit: str, runner_path: str | Path,
                   qualification_path: str | Path, bifrost_receipt_path: str | Path,
                   scala_receipt_path: str | Path, native_evidence: Mapping[str, str],
                   ledger_snapshot: dict, history_snapshot: dict) -> dict:
    plan, population, base, _parent_execution, _all_group_ids = _base_inputs(root)
    core, core_sha = _load_core(root)
    harness = Path(runner_path)
    if not harness.is_absolute() or harness.is_symlink() or not harness.is_file() or not os.access(harness, os.X_OK):
        raise BenchmarkError("--runner must be an absolute executable regular file")
    build_binding = _verify_runner_build(root, source_commit, harness)
    harness_sha = build_binding["binary"]["sha256"]
    _, bifrost_binding = _verify_bifrost_receipt(root, bifrost_receipt_path)
    _, scala_binding = _verify_scala_receipt(root, scala_receipt_path)
    _, qualification_binding = _verify_qualification(root, qualification_path, bifrost_binding)
    origin_main = _git(root, "rev-parse", "origin/main").strip()
    if origin_main != SOURCE_BASELINE_COMMIT:
        raise BenchmarkError("current origin/main no longer matches the reviewed C5 source baseline")
    _assert_ancestor(root, origin_main, source_commit, "current SOURCE relative to origin/main")
    if set(native_evidence) != set(NATIVE_EVIDENCE_ROLES):
        missing = sorted(set(NATIVE_EVIDENCE_ROLES) - set(native_evidence))
        extra = sorted(set(native_evidence) - set(NATIVE_EVIDENCE_ROLES))
        raise BenchmarkError(f"native configuration evidence roles are incomplete (missing={missing}, extra={extra})")
    native_refs = {}
    for role in NATIVE_EVIDENCE_ROLES:
        relative, path, raw = _path_ref(root, native_evidence[role], f"native evidence {role}")
        if relative.as_posix() != NATIVE_EVIDENCE_PATHS[role]:
            raise BenchmarkError(f"native evidence {role} must use its fixed source-bound path")
        native_refs[role] = {"path": relative.as_posix(), "sha256": _sha(raw), "bytes": len(raw)}
        if role == "help_stdout" and (BIFROST_REPORT_VERSION.encode() not in raw or b"USAGE:" not in raw):
            raise BenchmarkError("captured native help output does not identify the Bifrost CLI")
        if role == "controls_identity_version_stdout":
            expected = (BIFROST_REPORT_VERSION + "\n" +
                        "builtin-policy-catalog sha256=" + BIFROST_CATALOG_SHA256 + "\n").encode()
            if raw != expected:
                raise BenchmarkError("captured native version/catalog identity output changed")
        if role == "controls_identity_build_stdout" and raw != (BIFROST_BUILD_IDENTITY + "\n").encode():
            raise BenchmarkError("captured native build identity output changed")
        if role == "controls_catalog_list_stdout":
            try:
                catalog = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise BenchmarkError("captured native catalog listing is invalid JSON") from exc
            if catalog != {"schema_version": 2, "packs": []}:
                raise BenchmarkError("native empty catalog must remain explicitly not-evaluated")
        if role == "pin_profile":
            try:
                pin = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise BenchmarkError("Bifrost pin profile is invalid JSON") from exc
            bifrost_pin = pin.get("tools", {}).get("bifrost", {})
            if (pin.get("schema") != "dataflowbench-adapter-pin-profile/v1" or
                    pin.get("profile") != RELEASE or
                    bifrost_pin.get("version") != BIFROST_REPORT_VERSION or
                    bifrost_pin.get("build_identity") != BIFROST_BUILD_IDENTITY or
                    bifrost_pin.get("environment") != {"BIFROST_OPEN_PACKS_DISABLE": "1"} or
                    bifrost_pin.get("native_evidence") != PIN_PROFILE_NATIVE_EVIDENCE_DIRECTORY):
                raise BenchmarkError("C5 native pin profile differs from the acquired Bifrost identity")
    source_refs = [
        qualification_binding["path"],
        *qualification_binding["source_reference_paths"],
        bifrost_binding["receipt"]["path"],
        scala_binding["receipt"]["path"],
        RUNNER_BUILD_RECEIPT,
        RUNNER_BUILD_INPUTS,
        RUNNER_BUILD_STDOUT,
        RUNNER_BUILD_STDERR,
        *[entry["path"] for entry in native_refs.values()],
    ]
    source_snapshot = _build_source_snapshot(root, source_commit, base, source_refs, core_sha)
    core._assert_source_snapshot(
        root,
        source_commit,
        core_sha,
        [{"path": item["path"], "sha256": item["sha256"]} for item in source_snapshot["source_inputs"]],
    )
    old_harness_path = base["groups"][0]["argv"][0]
    if any(group["argv"][0] != old_harness_path for group in base["groups"] if group.get("tool") == "bifrost"):
        raise BenchmarkError("C4 Bifrost groups do not share the expected harness entrypoint")
    groups = project_target_groups(base["groups"], str(harness.resolve()), bifrost_binding["path"])
    validate_group_projections(groups, base["groups"], str(harness.resolve()), bifrost_binding["path"])
    target_deadlines = {entry["id"]: entry["base_group"]["deadline_seconds"] for entry in groups}
    if sum(target_deadlines.values()) != TARGET_WALL_BUDGET_SECONDS:
        raise BenchmarkError("the 20 inherited Bifrost deadlines no longer sum to 13,592 seconds")
    source_input_by_path = {item["path"]: item for item in source_snapshot["source_inputs"]}
    for role, evidence in native_refs.items():
        if source_input_by_path[evidence["path"]]["sha256"] != evidence["sha256"]:
            raise BenchmarkError(f"native evidence {role} differs from its committed source input")
    plan_raw = (root / BASE_PLAN_REL).read_bytes()
    population_raw = (root / BASE_POPULATION_REL).read_bytes()
    c4_raw = (root / BASE_CONTRACT_REL).read_bytes()
    contract = {
        "schema": CONTRACT_SCHEMA,
        "schema_version": 1,
        "target_id": TARGET_ID,
        "release": RELEASE,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "execution_authorized": False,
        "approval": None,
        "parent_population": {
            "plan": {"path": BASE_PLAN_REL, "sha256": _sha(plan_raw)},
            "execution_contract": {"path": BASE_PARENT_EXECUTION_REL, "sha256": BASE_PARENT_EXECUTION_SHA256},
            "baseline_c4_contract": {"path": BASE_CONTRACT_REL, "sha256": _sha(c4_raw)},
            "population": {"path": BASE_POPULATION_REL, "sha256": _sha(population_raw),
                           "fixture_revision": FIXTURE_REVISION, "case_count": len(population["cases"])},
            "full_counts": {"groups": len(base["groups"]), "report_partitions": 92,
                            "report_rows": 4252, "population_cases": len(population["cases"])},
            "target_bifrost_case_references": sum(len(group["base_group"]["case_ids"]) for group in groups),
            "target_bifrost_report_partitions": sum(len(group["base_group"]["reports"]) for group in groups),
            "historical_c4_source_commit": base["source_commit"],
            "historical_c4_ancestry_claim": "not-asserted-after-main-rewrite",
        },
        "source_snapshot": source_snapshot,
        "source_lineage": {
            "reviewed_origin_main": origin_main,
            "tracking_ref_name": "origin/main",
            "tracking_ref_commit": origin_main,
            "source_commit": source_commit,
            "source_is_descendant_of_reviewed_origin_main": True,
            "source_must_be_ancestor_of_later_plan_commit": True,
            "plan_contract_commit_is_recorded_at_execution": True,
        },
        "runtime": {
            "runner": {"path": str(harness.resolve()), "sha256": harness_sha,
                       "build_receipt": build_binding},
            "bifrost": bifrost_binding,
            "scala_maven": scala_binding,
            "qualification": qualification_binding,
            "native_configuration_evidence": native_refs,
            "base_harness_path": old_harness_path,
        },
        "allowed_runtime_projections": copy.deepcopy(ALLOWED_RUNTIME_PROJECTIONS),
        "groups": groups,
        "resource_policy": copy.deepcopy(RESOURCE_POLICY),
        "attempt_policy": copy.deepcopy(ATTEMPT_POLICY),
        "attempt_history": history_snapshot,
        "ledger_anchor": ledger_snapshot,
        "wall_budget": {
            "original_global_origin_utc": ORIGINAL_WALL_ORIGIN_UTC,
            "target_deadline_seconds": target_deadlines,
            "target_total_deadline_seconds": TARGET_WALL_BUDGET_SECONDS,
            "human_authority_expires": None,
            "historical_and_new_consumption_separate": True,
        },
        "target_outputs": {
            "ledger": LEDGER_REL,
            "attempts": ATTEMPTS_REL,
            "normal_reports": NORMAL_ATTEMPTS_REL,
            "progress": PROGRESS_REL,
            "summary": SUMMARY_REL,
        "invocations": INVOCATIONS_REL,
            "execution_roots": EXECUTION_GROUPS_REL + "/" + SERIES_LABEL,
            "cache_roots": CACHE_REL + "/" + SERIES_LABEL,
        },
        "authorization_origin": {
            "kind": "existing-human-authorization",
            "wall_clock_origin_utc": ORIGINAL_WALL_ORIGIN_UTC,
            "expires_at_utc": None,
            "review_required_for_execution": True,
        },
    }
    contract["approval_subject_sha256"] = approval_subject_sha256(contract)
    validate_resource_policy(contract["resource_policy"])
    validate_approval(contract, required=False)
    return contract


def _write_prepared_manifest(root: Path, contract: dict, output_rel: str | None = None) -> Path:
    if output_rel is None:
        output_rel = CONTRACT_REL
    if output_rel != CONTRACT_REL:
        raise BenchmarkError("C5 contract path is fixed and cannot be redirected")
    rel = _repo_relative(root, output_rel, "C5 contract path")
    target = root.joinpath(*rel.parts)
    if target.exists() or target.is_symlink():
        raise BenchmarkError(f"refusing to replace existing C5 contract: {target}")
    _atomic_write(target, _pretty_json(contract), exclusive=True)
    return target


def _attempt_number(group_id: str, attempt_id: str) -> tuple[int, int | None]:
    prefix = group_id + "-attempt-"
    if not attempt_id.startswith(prefix):
        raise BenchmarkError(f"attempt ID does not belong to group {group_id}: {attempt_id}")
    match = ATTEMPT_SUFFIX_RE.fullmatch(attempt_id[len(group_id):])
    if match is None:
        raise BenchmarkError(f"attempt ID has an unrecognized format: {attempt_id}")
    return int(match.group(1)), int(match.group(2))


def _record_attempt(records: dict, *, group_id: str, attempt_id: str,
                    series: int | None, status: str | None, source: str,
                    execution_root: str | None = None, ledger_recorded: bool = False) -> None:
    if not SAFE_GROUP_RE.fullmatch(group_id):
        raise BenchmarkError(f"attempt has an unsafe group ID: {group_id!r}")
    number, name_series = _attempt_number(group_id, attempt_id)
    if series is not None and name_series is not None and series != name_series:
        raise BenchmarkError(f"attempt series field conflicts with its ID: {attempt_id}")
    series = name_series if series is None else series
    key = (group_id, attempt_id)
    record = records.get(key)
    if record is None:
        record = {
            "group_id": group_id,
            "attempt_id": attempt_id,
            "attempt_number": number,
            "execution_series": series,
            "status": status,
            "ledger_recorded": ledger_recorded,
            "sources": [],
            "execution_roots": [],
        }
        records[key] = record
    else:
        if record["attempt_number"] != number or record["execution_series"] not in (None, series) and series is not None:
            raise BenchmarkError(f"attempt identity conflicts across evidence sources: {attempt_id}")
        if record["status"] is None and status is not None:
            record["status"] = status
        record["ledger_recorded"] = record["ledger_recorded"] or ledger_recorded
    if source not in record["sources"]:
        record["sources"].append(source)
    if execution_root and execution_root not in record["execution_roots"]:
        record["execution_roots"].append(execution_root)


def _parse_attempt_directory(name: str, known_group_ids: Sequence[str]) -> tuple[str, str, int | None] | None:
    for group_id in sorted(known_group_ids, key=len, reverse=True):
        if name.startswith(group_id + "-attempt-"):
            attempt_id = name
            number, series = _attempt_number(group_id, attempt_id)
            return group_id, attempt_id, series
    return None


def _safe_execution_root(root: Path, value: object) -> Path:
    if not isinstance(value, str):
        raise BenchmarkError("ledger execution_root must be an absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise BenchmarkError("ledger execution_root must be absolute")
    base = (root / EXECUTION_GROUPS_REL).resolve()
    try:
        path.resolve(strict=False).relative_to(base)
    except ValueError as exc:
        raise BenchmarkError("ledger execution_root escapes the v0.9.2 groups tree") from exc
    return path


def _scan_ledger(root: Path, all_group_ids: Sequence[str], *,
                 anchor: dict | None = None, current_contract_sha256: str | None = None) -> dict:
    """Stream the append-only ledger, retaining only compact identities and C5 rows."""
    path = root / LEDGER_REL
    if path.is_symlink() or not path.is_file():
        raise BenchmarkError(f"attempt ledger is missing or unsafe: {path}")
    all_ids = set(all_group_ids)
    full_hash = hashlib.sha256()
    protected_hash = hashlib.sha256()
    anchor_hash = hashlib.sha256()
    target_suffix_hash = hashlib.sha256()
    anchor_bytes = 0
    anchor_count = 0
    line_count = 0
    byte_count = 0
    records = {}
    target_rows = []
    target_stage_proofs = []
    capacity_paths = {
        "execution_roots": [], "output_roots": [], "cache_roots": [],
        "home_paths": [], "tmp_paths": [], "source_inputs": [],
    }
    seen_ledger_attempts = set()
    started_at = None
    with path.open("rb") as stream:
        for raw in stream:
            if not raw.endswith(b"\n"):
                raise BenchmarkError("attempt ledger has a truncated final line; refusing to append")
            line_count += 1
            byte_count += len(raw)
            full_hash.update(raw)
            if line_count <= LEDGER_PREFIX_LINES:
                protected_hash.update(raw)
            if anchor is not None and line_count <= anchor.get("line_count", 0):
                anchor_hash.update(raw)
                anchor_bytes += len(raw)
                anchor_count = line_count
            try:
                row = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise BenchmarkError(f"attempt ledger row {line_count} is invalid JSON") from exc
            if not isinstance(row, dict):
                raise BenchmarkError(f"attempt ledger row {line_count} is not an object")
            source_inputs = row.get("source_inputs")
            if not isinstance(source_inputs, list):
                raise BenchmarkError(f"attempt ledger row {line_count} lacks its source-input path inventory")
            for source_input in source_inputs:
                if not isinstance(source_input, dict) or not isinstance(source_input.get("path"), str):
                    raise BenchmarkError(f"attempt ledger row {line_count} has a malformed source-input path")
                capacity_paths["source_inputs"].append(
                    _accounting_source_path(root, source_input["path"], "ledger source-input path"))
            group_id = row.get("group_id")
            attempt_id = row.get("attempt_id")
            if group_id not in all_ids or not isinstance(attempt_id, str):
                raise BenchmarkError(f"attempt ledger row {line_count} has unknown group/attempt identity")
            ledger_identity = (group_id, attempt_id)
            if ledger_identity in seen_ledger_attempts:
                raise BenchmarkError(f"attempt ledger duplicates an attempt identity: {group_id}/{attempt_id}")
            seen_ledger_attempts.add(ledger_identity)
            series = row.get("execution_series")
            if type(series) is not int or series < 1:
                raise BenchmarkError(f"attempt ledger row {line_count} has invalid execution_series")
            try:
                attempt_number, embedded_series = _attempt_number(group_id, attempt_id)
            except BenchmarkError as exc:
                raise BenchmarkError(f"attempt ledger row {line_count} has an invalid attempt ID") from exc
            if embedded_series != series:
                raise BenchmarkError(f"attempt ledger row {line_count} series disagrees with attempt ID")
            execution_root = _safe_execution_root(root, row.get("execution_root"))
            expected_execution = (root / EXECUTION_GROUPS_REL / f"series-{series:02d}" /
                                  group_id / f"attempt-{attempt_number:02d}").resolve(strict=False)
            if execution_root.resolve(strict=False) != expected_execution:
                raise BenchmarkError(f"attempt ledger row {line_count} execution root is not its exact series/group attempt path")
            if execution_root.is_symlink():
                raise BenchmarkError(f"attempt ledger row {line_count} execution root is symlinked")
            expected_cache = (root / CACHE_REL / f"series-{series:02d}" /
                              group_id / f"attempt-{attempt_number:02d}").resolve(strict=False)
            capacity_paths["execution_roots"].append(str(execution_root))
            cache_value = row.get("cache_root")
            if (not isinstance(cache_value, str) or not Path(cache_value).is_absolute() or
                    Path(cache_value).resolve(strict=False) != expected_cache or Path(cache_value).is_symlink()):
                raise BenchmarkError(f"attempt ledger row {line_count} cache root is not its exact attempt path")
            capacity_paths["cache_roots"].append(cache_value)
            environment = row.get("environment")
            if not isinstance(environment, dict):
                raise BenchmarkError(f"attempt ledger row {line_count} has no explicit environment receipt")
            home_value = environment.get("HOME")
            tmp_value = environment.get("TMPDIR")
            if (not isinstance(home_value, str) or not Path(home_value).is_absolute() or
                    Path(home_value).resolve(strict=False) != (execution_root / "home").resolve(strict=False) or
                    Path(home_value).is_symlink()):
                raise BenchmarkError(f"attempt ledger row {line_count} HOME is not isolated to its attempt")
            expected_tmp = execution_root / "tmp"
            if group_id in {"pysa-python-kernel", "pysa-python-modeling", "pysa-python-native"}:
                identity = hashlib.sha256(str(execution_root.resolve()).encode()).hexdigest()[:20]
                expected_tmp = Path("/private/tmp") / ("dfb-v092-pysa-" + identity)
            if (not isinstance(tmp_value, str) or not Path(tmp_value).is_absolute() or
                    Path(tmp_value).resolve(strict=False) != expected_tmp.resolve(strict=False) or
                    Path(tmp_value).is_symlink()):
                raise BenchmarkError(f"attempt ledger row {line_count} TMPDIR is not isolated to its attempt")
            capacity_paths["home_paths"].append(home_value)
            capacity_paths["tmp_paths"].append(tmp_value)
            output_values = row.get("output_roots")
            if isinstance(output_values, list):
                for value in output_values:
                    if isinstance(value, str):
                        relative_output = PurePosixPath(value)
                        if relative_output.is_absolute() or any(part in ("", ".", "..") for part in relative_output.parts):
                            raise BenchmarkError("ledger output root is unsafe for retention accounting")
                        capacity_paths["output_roots"].append(str(execution_root.joinpath(*relative_output.parts)))
            is_target = row.get("target_id") == TARGET_ID
            if series == SERIES and not is_target:
                raise BenchmarkError(f"{SERIES_LABEL} contains an attempt from an unregistered target")
            if is_target:
                if group_id not in BIFROST_GROUP_IDS or series != SERIES:
                    raise BenchmarkError(f"C5 target ledger rows must belong to the fixed 20 Bifrost groups in {SERIES_LABEL}")
                if attempt_number < 1:
                    raise BenchmarkError("C5 target ledger row has an invalid attempt number")
                if current_contract_sha256 is not None and row.get("contract_sha256") != current_contract_sha256:
                    raise BenchmarkError(f"{SERIES_LABEL} ledger row refers to another C5 contract revision")
                if series != SERIES:
                    raise BenchmarkError("C5 target row uses the wrong execution series")
                stage = row.get("ledger_stage_proof")
                if (not isinstance(stage, dict) or
                        stage.get("pre_append_line_count") != line_count - 1 or
                        stage.get("pre_append_bytes") != byte_count - len(raw) or
                        stage.get(f"original_{LEDGER_PREFIX_LINES}_row_prefix_sha256") != LEDGER_PREFIX_SHA256 or
                        stage.get("target_suffix_line_count_before") != len(target_rows) or
                        stage.get("target_suffix_sha256_before") != target_suffix_hash.hexdigest()):
                    raise BenchmarkError("C5 ledger row has an invalid append-prefix stage proof")
                target_rows.append(row)
                target_suffix_hash.update(raw)
                target_stage_proofs.append({
                    "group_id": group_id, "attempt_id": attempt_id,
                    "line_count": len(target_rows), "sha256": target_suffix_hash.hexdigest(),
                })
            else:
                _record_attempt(records, group_id=group_id, attempt_id=attempt_id, series=series,
                                status=row.get("status") if isinstance(row.get("status"), str) else None,
                                source=f"ledger:{line_count}", execution_root=str(execution_root),
                                ledger_recorded=True)
            if line_count == 1:
                started_at = row.get("start_utc")
    if line_count < LEDGER_PREFIX_LINES or protected_hash.hexdigest() != LEDGER_PREFIX_SHA256:
        raise BenchmarkError(f"attempt ledger no longer preserves the pinned {LEDGER_PREFIX_LINES}-row prefix")
    if anchor is not None:
        expected_count = anchor.get("line_count")
        expected_sha = anchor.get("sha256")
        if type(expected_count) is not int or expected_count < LEDGER_PREFIX_LINES:
            raise BenchmarkError("C5 ledger anchor line count is invalid")
        if line_count < expected_count or anchor_count != expected_count or anchor_hash.hexdigest() != expected_sha:
            raise BenchmarkError("attempt ledger no longer begins with the C5-pinned prefix")
        if byte_count < anchor.get("bytes", 0):
            raise BenchmarkError("attempt ledger is shorter than its pinned byte prefix")
    if anchor is None and target_rows:
        raise BenchmarkError(f"{SERIES_LABEL} already contains C5 target ledger rows; refusing fresh preparation")
    return {
        "path": LEDGER_REL,
        "line_count": line_count,
        "bytes": byte_count,
        "sha256": full_hash.hexdigest(),
        "preserved_prefix": {"line_count": LEDGER_PREFIX_LINES, "sha256": protected_hash.hexdigest()},
        "original_first_start_utc": started_at,
        "historical_records": records,
        "target_rows": target_rows,
        "target_line_count": len(target_rows),
        "target_suffix_sha256": target_suffix_hash.hexdigest(),
        "target_suffix_state": target_suffix_hash,
        "target_stage_proofs": target_stage_proofs,
        "capacity_paths": {key: sorted(set(values)) for key, values in capacity_paths.items()},
    }


def _read_started_receipt(path: Path) -> dict | None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        return None
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _record_from_receipt(records: dict, receipt: dict, path: Path,
                         all_group_ids: Sequence[str]) -> None:
    group_id = receipt.get("group_id")
    attempt_id = receipt.get("attempt_id")
    if group_id not in set(all_group_ids) or not isinstance(attempt_id, str):
        return
    if not attempt_id.startswith(group_id + "-attempt-"):
        raise BenchmarkError(f"started-attempt receipt has an unrecognized ID: {path}")
    series = receipt.get("execution_series")
    if series is not None and (type(series) is not int or series < 1):
        raise BenchmarkError(f"started-attempt receipt has invalid series: {path}")
    _record_attempt(
        records,
        group_id=group_id,
        attempt_id=attempt_id,
        series=series,
        status=receipt.get("status") if isinstance(receipt.get("status"), str) else "started",
        source=f"receipt:{path.relative_to(path.anchor)}",
        execution_root=receipt.get("execution_root") if isinstance(receipt.get("execution_root"), str) else None,
        ledger_recorded=False,
    )


def _add_attempt_directory(records: dict, path: Path, all_group_ids: Sequence[str], *,
                           explicit_group: str | None = None, explicit_series: int | None = None) -> None:
    parsed = _parse_attempt_directory(path.name, all_group_ids)
    if parsed is not None:
        group_id, attempt_id, series = parsed
    elif explicit_group and ATTEMPT_DIR_RE.fullmatch(path.name):
        number = int(ATTEMPT_DIR_RE.fullmatch(path.name).group(1))
        if explicit_series is None:
            raise BenchmarkError(f"attempt directory lacks a series parent: {path}")
        group_id = explicit_group
        attempt_id = f"{group_id}-attempt-{number:02d}-series-{explicit_series:02d}"
        series = explicit_series
    else:
        return
    if path.is_symlink():
        raise BenchmarkError(f"attempt namespace path is symlinked: {path}")
    terminal = None
    for name in ("terminal.json", "completed.json", "failed.json", "started.json"):
        item = path / name
        if item.exists():
            terminal = _read_started_receipt(item)
            if terminal:
                break
    status = terminal.get("status") if isinstance(terminal, dict) else None
    _record_attempt(records, group_id=group_id, attempt_id=attempt_id, series=series,
                    status=status if isinstance(status, str) else "unclosed-started-namespace",
                    source=f"directory:{path.relative_to(path.anchor)}")


def _is_other_release_evidence_path(path: Path) -> bool:
    """Do not reinterpret copied v0.9.0 attempt evidence as v0.9.2 consumption."""
    parts = path.parts
    for index in range(len(parts) - 2):
        if parts[index:index + 2] == ("reports", "releases"):
            release = parts[index + 2]
            if re.fullmatch(r"v\d+\.\d+\.\d+", release) and release != RELEASE:
                return True
    return False


def _walk_namespace(root: Path, base: Path, all_group_ids: Sequence[str], records: dict,
                    *, max_depth: int, relevant_only: bool) -> None:
    if not base.exists() or base.is_symlink() or not base.is_dir():
        return
    stack = [(base, 0)]
    while stack:
        directory, depth = stack.pop()
        if _is_other_release_evidence_path(directory):
            continue
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise BenchmarkError(f"cannot enumerate attempt namespace {directory}: {exc}") from exc
        parent_name = directory.name
        series_match = re.fullmatch(r"series-(\d+)", parent_name)
        group_parent = parent_name if parent_name in set(all_group_ids) else None
        for child in children:
            if child.is_symlink():
                if _parse_attempt_directory(child.name, all_group_ids):
                    raise BenchmarkError(f"attempt namespace is symlinked: {child}")
                continue
            if not child.is_dir():
                continue
            if _is_other_release_evidence_path(child):
                continue
            _add_attempt_directory(
                records,
                child,
                all_group_ids,
                explicit_group=group_parent,
                explicit_series=int(series_match.group(1)) if series_match else None,
            )
            if depth + 1 >= max_depth:
                continue
            if relevant_only:
                lower = child.name.lower()
                if not any(token in lower for token in ("bifrost", "smoke", "attempt", "series", "controls")):
                    continue
            stack.append((child, depth + 1))
        # Small durable receipts are an alternative namespace marker when the
        # directory name itself does not expose the attempt ID.
        if depth < max_depth:
            for child in children:
                if not child.is_dir() or child.is_symlink():
                    continue
                for marker in ("started.json", "process-ownership.json", "attempt.json"):
                    receipt = _read_started_receipt(child / marker)
                    if receipt:
                        _record_from_receipt(records, receipt, child / marker, all_group_ids)


def _scan_history(root: Path, all_group_ids: Sequence[str], *,
                  ledger_anchor: dict | None = None,
                  current_contract_sha256: str | None = None,
                  preparing: bool = False, ledger_result: dict | None = None) -> dict:
    ledger = ledger_result or _scan_ledger(root, all_group_ids, anchor=ledger_anchor,
                                           current_contract_sha256=current_contract_sha256)
    records = dict(ledger["historical_records"])
    for row_number, row in enumerate(ledger["target_rows"], start=1):
        _record_attempt(records, group_id=row["group_id"], attempt_id=row["attempt_id"],
                        series=row["execution_series"],
                        status=row.get("status") if isinstance(row.get("status"), str) else None,
                        source=f"target-ledger:{row_number}",
                        execution_root=row.get("execution_root"), ledger_recorded=True)
    groups_root = root / EXECUTION_GROUPS_REL
    if groups_root.exists():
        if groups_root.is_symlink() or not groups_root.is_dir():
            raise BenchmarkError("historical execution-state groups root is unsafe")
        for series_dir in sorted(groups_root.iterdir(), key=lambda item: item.name):
            if series_dir.is_symlink():
                raise BenchmarkError(f"historical execution series path is symlinked: {series_dir}")
            series_match = re.fullmatch(r"series-(\d+)", series_dir.name)
            if not series_match or not series_dir.is_dir():
                continue
            series = int(series_match.group(1))
            for group_dir in sorted(series_dir.iterdir(), key=lambda item: item.name):
                if group_dir.is_symlink():
                    raise BenchmarkError(f"historical group path is symlinked: {group_dir}")
                if group_dir.name not in set(all_group_ids) or not group_dir.is_dir():
                    continue
                for attempt_dir in sorted(group_dir.iterdir(), key=lambda item: item.name):
                    if attempt_dir.is_dir() or attempt_dir.is_symlink():
                        _add_attempt_directory(records, attempt_dir, all_group_ids,
                                               explicit_group=group_dir.name, explicit_series=series)
    for relative in (ATTEMPTS_REL, NORMAL_ATTEMPTS_REL):
        directory = root / relative
        if not directory.exists():
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise BenchmarkError(f"historical attempt root is unsafe: {directory}")
        for attempt_dir in sorted(directory.iterdir(), key=lambda item: item.name):
            if attempt_dir.is_dir() or attempt_dir.is_symlink():
                _add_attempt_directory(records, attempt_dir, all_group_ids)

    # Some failed C4 supervisors created a started namespace before writing a
    # ledger row. Search bounded Bifrost/attempt subtrees for small start receipts.
    candidate_roots = [
        root / "execution-state/v092/tools",
        root / "execution-state/v092",
        root / "reports/releases/v0.9.2/acquisition",
        root / "reports/releases/v0.9.2/qualification",
        root / "reports/releases/v0.9.2/validation",
    ]
    excluded = {"groups", "cache", "attempts", "normal", "execution-v1", "execution-v2",
                "execution-v3", "execution-v4", "ledger-archives", ".git"}
    for candidate in candidate_roots:
        if not candidate.exists() or candidate.is_symlink():
            continue
        if candidate.name == "v092":
            try:
                children = sorted(candidate.iterdir(), key=lambda item: item.name)
            except OSError as exc:
                raise BenchmarkError(f"cannot enumerate historical execution root: {exc}") from exc
            for child in children:
                if child.name in excluded or child.name in {"tools", "groups", "cache"}:
                    continue
                if child.is_dir() and not child.is_symlink():
                    _walk_namespace(root, child, all_group_ids, records, max_depth=5, relevant_only=False)
            continue
        _walk_namespace(root, candidate, all_group_ids, records, max_depth=5, relevant_only=True)

    # Remove this target series's records only when reconciling a previously prepared C5
    # contract. During preparation, any such namespace means this target is not fresh.
    target_existing = [record for record in records.values() if record.get("execution_series") == SERIES]
    if preparing and target_existing:
        raise BenchmarkError(f"{SERIES_LABEL} already contains started attempts; refusing a fresh C5 contract")
    if preparing and ledger["target_rows"]:
        raise BenchmarkError(f"{SERIES_LABEL} already contains target ledger rows; refusing fresh preparation")
    historical = {key: value for key, value in records.items() if value.get("execution_series") != SERIES}
    ordered = sorted(historical.values(), key=lambda item: (item["group_id"], item["attempt_id"]))
    compact = [
        {"group_id": item["group_id"], "attempt_id": item["attempt_id"],
         "attempt_number": item["attempt_number"], "execution_series": item["execution_series"],
         "status": item["status"], "ledger_recorded": item["ledger_recorded"],
         "sources": sorted(item["sources"]), "execution_roots": sorted(item["execution_roots"])}
        for item in ordered
    ]
    group_counters = {}
    target_groups = [group_id for group_id in all_group_ids if group_id in BIFROST_GROUP_IDS]
    for group_id in target_groups:
        group_records = [item for item in compact if item["group_id"] == group_id]
        numbers = [item["attempt_number"] for item in group_records]
        unledgered = [item for item in group_records if not item["ledger_recorded"]]
        group_counters[group_id] = {
            "prior_consumed_count": len(group_records),
            "prior_max_attempt_number": max(numbers, default=0),
            "next_attempt_number": max(numbers, default=0) + 1,
            "new_target_slots": ATTEMPT_POLICY["new_target_slots_per_group"],
            "unledgered_started_attempts": unledgered,
        }
    snapshot = {
        "global_prior_consumed_attempt_count": len(compact),
        "historical_attempts_sha256": _sha(_canonical_json(compact)),
        "historical_group_counters": group_counters,
        "unledgered_started_attempt_count": sum(1 for item in compact if not item["ledger_recorded"]),
        "accounting_scope": "all 84 baseline groups, all ledger rows, and all discovered started-attempt namespaces",
    }
    roots = sorted({path for item in compact for path in item["execution_roots"]})
    target_records = [
        {"group_id": item["group_id"], "attempt_id": item["attempt_id"],
         "attempt_number": item["attempt_number"], "execution_series": item["execution_series"],
         "status": item["status"], "ledger_recorded": item["ledger_recorded"],
         "sources": sorted(item["sources"]), "execution_roots": sorted(item["execution_roots"])}
        for item in sorted(target_existing, key=lambda value: (value["group_id"], value["attempt_id"]))
    ]
    return {"ledger": ledger, "records": compact, "target_records": target_records,
            "snapshot": snapshot, "execution_roots": roots}


def _assert_history_unchanged(contract: dict, current: dict) -> None:
    if current["snapshot"] != contract.get("attempt_history"):
        raise BenchmarkError("historical attempt consumption changed after contract preparation; reprepare C5")


def _verify_capture_manifest(root: Path, qualification: dict) -> dict:
    capture_rel = qualification["capture"]["path"]
    manifest_rel = f"{capture_rel}/artifact-hashes.json"
    manifest, raw = _read_json(root / manifest_rel, "Bifrost controls artifact manifest")
    if _sha(raw) != CAPTURE_MANIFEST_SHA256 or manifest.get("schema") != "bifrost-v013-capture-artifacts/v1":
        raise BenchmarkError("Bifrost control artifact manifest schema or digest changed")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) < 1:
        raise BenchmarkError("Bifrost control artifact manifest has no file inventory")
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise BenchmarkError("Bifrost control artifact manifest contains a malformed file")
        relative = item.get("path")
        expected_sha = item.get("sha256")
        expected_bytes = item.get("bytes")
        if (not isinstance(relative, str) or not SHA256_RE.fullmatch(str(expected_sha)) or
                type(expected_bytes) is not int or expected_bytes < 0):
            raise BenchmarkError("Bifrost control artifact manifest file identity is malformed")
        manifest_path = _repo_relative(root, f"{capture_rel}/{relative}", "control artifact path")
        if not manifest_path.as_posix().startswith(capture_rel + "/") or manifest_path in seen:
            raise BenchmarkError("Bifrost control artifact path escapes or duplicates its capture")
        seen.add(manifest_path)
        path = root.joinpath(*manifest_path.parts)
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_bytes:
            raise BenchmarkError(f"captured control artifact is missing or changed size: {manifest_path}")
        if _sha_file(path) != expected_sha:
            raise BenchmarkError(f"captured control artifact hash changed: {manifest_path}")
    return {"path": manifest_rel, "sha256": _sha(raw), "files": len(files)}


def _validate_contract(root: Path, contract_path: str | Path, *, require_approval: bool = True,
                       require_committed: bool = True,
                       check_current_source: bool = True) -> dict:
    relative, path, raw = _path_ref(root, contract_path, "C5 execution contract")
    if relative.as_posix() != CONTRACT_REL:
        raise BenchmarkError("C5 execution contract path is fixed")
    contract, _ = _read_json(path, "C5 execution contract")
    if (contract.get("schema") != CONTRACT_SCHEMA or contract.get("schema_version") != 1 or
            contract.get("target_id") != TARGET_ID or contract.get("release") != RELEASE):
        raise BenchmarkError("C5 contract schema, target, or release identity is invalid")
    if contract.get("approval_subject_sha256") != approval_subject_sha256(contract):
        raise BenchmarkError("C5 contract approval subject hash differs")
    validate_approval(contract, required=require_approval)
    validate_resource_policy(contract.get("resource_policy"))
    if contract.get("attempt_policy") != ATTEMPT_POLICY:
        raise BenchmarkError("C5 attempt policy differs from the reviewed monotonic two-slot policy")
    if contract.get("allowed_runtime_projections") != ALLOWED_RUNTIME_PROJECTIONS:
        raise BenchmarkError("C5 runtime substitution boundary differs from the reviewed projection")
    plan, population, base, _parent, all_ids = _base_inputs(root)
    if contract.get("parent_population", {}).get("full_counts") != {
            "groups": 84, "report_partitions": 92, "report_rows": 4252, "population_cases": 1108}:
        raise BenchmarkError("C5 contract does not preserve the full 84/92/4252/1108 parent population")
    parent = contract.get("parent_population", {})
    if (parent.get("target_bifrost_report_partitions") != 20 or
            parent.get("target_bifrost_case_references") != sum(
                len(group["case_ids"]) for group in base["groups"] if group.get("tool") == "bifrost")):
        raise BenchmarkError("C5 parent population projection changed")
    lineage = contract.get("source_lineage", {})
    source_commit = contract.get("source_snapshot", {}).get("source_commit")
    if (source_commit != lineage.get("source_commit") or
            lineage.get("reviewed_origin_main") != SOURCE_BASELINE_COMMIT or
            lineage.get("tracking_ref_name") != "origin/main" or
            lineage.get("tracking_ref_commit") != SOURCE_BASELINE_COMMIT or
            lineage.get("source_is_descendant_of_reviewed_origin_main") is not True or
            lineage.get("source_must_be_ancestor_of_later_plan_commit") is not True):
        raise BenchmarkError("C5 source lineage declaration is incomplete")
    _assert_ancestor(root, SOURCE_BASELINE_COMMIT, source_commit, "C5 source relative to origin/main")
    core, core_sha = _load_core(root, contract.get("source_snapshot", {}).get("core_helpers", [{}])[0].get("sha256"))
    source_inputs = contract.get("source_snapshot", {}).get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        raise BenchmarkError("C5 source closure has no explicit current inputs")
    input_map = {}
    for item in source_inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not SHA256_RE.fullmatch(str(item.get("sha256"))):
            raise BenchmarkError("C5 current source input identity is malformed")
        if item["path"] in input_map:
            raise BenchmarkError(f"C5 current source input is duplicated: {item['path']}")
        input_map[item["path"]] = item["sha256"]
        core._source_file(root, source_commit, item["path"], item["sha256"])
    if contract["source_snapshot"].get("historical_c4_source_inputs") != base.get("source_inputs"):
        raise BenchmarkError("historical C4 source-input hashes were dropped or changed")
    if contract["source_snapshot"].get("closure_boundary", {}).get(
            "historical_c4_source_inputs_retained_for_capacity_accounting") != len(base.get("source_inputs", [])):
        raise BenchmarkError("C5 source closure misstates the historical C4 accounting boundary")
    for helper in contract["source_snapshot"].get("core_helpers", []):
        helper_path = helper.get("path") if isinstance(helper, dict) else None
        helper_sha = helper.get("sha256") if isinstance(helper, dict) else None
        if (not isinstance(helper_path, str) or not SHA256_RE.fullmatch(str(helper_sha))):
            raise BenchmarkError("frozen C5 core helper identity is malformed")
        if check_current_source:
            current_helper = root / helper_path
            if (current_helper.is_symlink() or not current_helper.is_file() or
                    _sha_file(current_helper) != helper_sha):
                raise BenchmarkError(f"frozen C5 core helper changed: {helper_path}")
        else:
            # Historical reconciliation verifies the implementation bound by
            # SOURCE, even when the working tree now contains a successor
            # driver. Dispatch remains stricter below and checks the current
            # source snapshot before launching any attempts.
            core._source_file(root, source_commit, helper_path, helper_sha)
    runtime = contract.get("runtime", {})
    runner = runtime.get("runner", {})
    runner_path = runner.get("path")
    bifrost_receipt_path = runtime.get("bifrost", {}).get("receipt", {}).get("path")
    scala_receipt_path = runtime.get("scala_maven", {}).get("receipt", {}).get("path")
    if not isinstance(runner_path, str) or not Path(runner_path).is_absolute():
        raise BenchmarkError("C5 runtime runner path is not absolute")
    runner_build = _verify_runner_build(root, source_commit, runner_path)
    if runner.get("sha256") != runner_build["binary"]["sha256"] or runner.get("build_receipt") != runner_build:
        raise BenchmarkError("pinned optimized harness binary or build provenance changed")
    _, bifrost = _verify_bifrost_receipt(root, bifrost_receipt_path)
    _, scala = _verify_scala_receipt(root, scala_receipt_path)
    _, qualification = _verify_qualification(root, runtime.get("qualification", {}).get("path"), bifrost)
    _verify_capture_manifest(root, qualification)
    if runtime.get("bifrost") != bifrost or runtime.get("scala_maven") != scala:
        raise BenchmarkError("C5 runtime artifact bindings differ from acquired pinned artifacts")
    if runtime.get("qualification") != qualification:
        raise BenchmarkError("C5 qualification binding differs from fresh reviewed evidence")
    native = runtime.get("native_configuration_evidence")
    if not isinstance(native, dict) or set(native) != set(NATIVE_EVIDENCE_ROLES):
        raise BenchmarkError("C5 native configuration evidence roster is incomplete")
    for role in NATIVE_EVIDENCE_ROLES:
        entry = native[role]
        if not isinstance(entry, dict) or entry.get("path") != NATIVE_EVIDENCE_PATHS[role]:
            raise BenchmarkError(f"C5 native evidence path changed for {role}")
        evidence_path = root / entry["path"]
        if evidence_path.is_symlink() or not evidence_path.is_file() or _sha_file(evidence_path) != entry.get("sha256"):
            raise BenchmarkError(f"C5 native evidence digest changed for {role}")
        if input_map.get(entry["path"]) != entry["sha256"]:
            raise BenchmarkError(f"C5 source closure omitted native evidence {role}")
    for build_path, build_sha in ((RUNNER_BUILD_RECEIPT, RUNNER_BUILD_RECEIPT_SHA256),
                                  (RUNNER_BUILD_INPUTS, RUNNER_BUILD_INPUTS_SHA256),
                                  (RUNNER_BUILD_STDOUT, RUNNER_BUILD_STDOUT_SHA256),
                                  (RUNNER_BUILD_STDERR, RUNNER_BUILD_STDERR_SHA256)):
        if input_map.get(build_path) != build_sha:
            raise BenchmarkError(f"C5 source closure omitted optimized harness build proof: {build_path}")
    source_hashes = [{"path": item["path"], "sha256": item["sha256"]} for item in source_inputs]
    runner_source = contract["source_snapshot"].get("runner_source", {})
    runner_source_path = runner_source.get("path") if isinstance(runner_source, dict) else None
    runner_source_sha = runner_source.get("sha256") if isinstance(runner_source, dict) else None
    if (runner_source_path != TARGET_DRIVER_SOURCE_REL or
            not isinstance(runner_source_sha, str) or not SHA256_RE.fullmatch(runner_source_sha) or
            input_map.get(runner_source_path) != runner_source_sha):
        raise BenchmarkError("C5 target driver source binding is incomplete or differs from source closure")
    if check_current_source:
        current_runner_source = root / runner_source_path
        if (current_runner_source.is_symlink() or not current_runner_source.is_file() or
                _sha_file(current_runner_source) != runner_source_sha):
            raise BenchmarkError("current C5 target driver differs from the frozen source binding")
    else:
        core._source_file(root, source_commit, runner_source_path, runner_source_sha)
    if check_current_source:
        core._assert_source_snapshot(root, source_commit, core_sha, source_hashes)
    validate_group_projections(contract.get("groups", []), base["groups"], runner_path, bifrost["path"])
    if sum(item["base_group"]["deadline_seconds"] for item in contract["groups"]) != TARGET_WALL_BUDGET_SECONDS:
        raise BenchmarkError("C5 inherited target deadlines changed")
    if contract.get("wall_budget", {}).get("original_global_origin_utc") != ORIGINAL_WALL_ORIGIN_UTC:
        raise BenchmarkError("C5 changed the frozen historical wall-clock origin")
    if contract.get("wall_budget", {}).get("target_total_deadline_seconds") != TARGET_WALL_BUDGET_SECONDS:
        raise BenchmarkError("C5 changed the target deadline sum")
    if require_committed:
        head = _git(root, "rev-parse", "HEAD").strip()
        plan_commit = _git(root, "log", "-1", "--format=%H", "--", relative.as_posix()).strip()
        if not COMMIT_RE.fullmatch(plan_commit) or plan_commit == source_commit:
            raise BenchmarkError("C5 contract has no later committed plan revision")
        _assert_ancestor(root, source_commit, plan_commit, "C5 SOURCE relative to committed plan")
        _assert_ancestor(root, plan_commit, head, "C5 committed plan relative to current HEAD")
        committed = _git(root, "show", f"{plan_commit}:{relative.as_posix()}", text=False)
        current_committed = _git(root, "show", f"{head}:{relative.as_posix()}", text=False)
        if committed != raw or current_committed != raw:
            raise BenchmarkError("C5 contract differs from its committed plan or current HEAD readback")
        status = _git(root, "status", "--porcelain=v1", "--", relative.as_posix()).strip()
        if status:
            raise BenchmarkError("C5 contract must be committed and clean before execution")
    history = _scan_history(root, all_ids, ledger_anchor=contract.get("ledger_anchor"),
                            current_contract_sha256=_sha(raw))
    ledger = history["ledger"]
    _assert_history_unchanged(contract, history)
    return {
        "contract": contract,
        "contract_sha256": _sha(raw),
        "path": path,
        "source_commit": source_commit,
        "plan_commit": plan_commit if require_committed else None,
        "runner_path": runner_path,
        "bifrost": bifrost,
        "scala": scala,
        "qualification": qualification,
        "base_groups": base["groups"],
        "all_group_ids": all_ids,
        "history": history,
        "ledger": ledger,
    }


class _ContinuousDiskGuard:
    """Enforce C5's 125 GiB continuous floor over the pinned v0.9.2 guard."""

    def __init__(self, base, floor_bytes: int, capacity_path: Path):
        self.base = base
        self.floor_bytes = floor_bytes
        self.capacity_path = capacity_path
        self.chunk_bytes = base.chunk_bytes

    @staticmethod
    def error(code: str, message: str, **metadata):
        from importlib.util import module_from_spec, spec_from_file_location
        return _strict_guard_module.DiskGuardError(code, message, **metadata)

    @staticmethod
    def logical_size(paths):
        return _strict_guard_module.DiskGuard.logical_size(paths)

    def _check_floor(self, result: Mapping[str, object], projected: int = 0) -> None:
        free = result.get("free_bytes")
        post = result.get("post_write_free_bytes", int(free or 0) - projected)
        if type(free) is not int or free < self.floor_bytes or type(post) is not int or post < self.floor_bytes:
            raise _strict_guard_module.DiskGuardError(
                "stop_floor",
                "C5 continuous free-space floor of 125 GiB would be crossed",
                phase="active",
                free_bytes=free,
                projected_bytes=projected,
                post_write_free_bytes=post,
                required_free_bytes=self.floor_bytes,
                capacity_path=str(self.capacity_path),
            )

    def check(self, **kwargs):
        result = self.base.check(**kwargs)
        self._check_floor(result, int(kwargs.get("projected_bytes", 0)))
        return result

    def check_capacity(self, *, projected_bytes: int = 0, capacity_path: Path):
        result = self.base.check_capacity(projected_bytes=projected_bytes, capacity_path=capacity_path)
        self._check_floor(result, projected_bytes)
        return result


_strict_guard_module = None


def _disk_guard(root: Path, core):
    global _strict_guard_module
    path = root / "scripts/v092_disk_guard.py"
    spec = importlib.util.spec_from_file_location("bifrost_v0144_disk_guard", path)
    if spec is None or spec.loader is None:
        raise BenchmarkError("cannot load the pinned v0.9.2 disk guard")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _strict_guard_module = module
    gib = 1024**3
    base = module.DiskGuard(
        launch_floor_bytes=127 * gib,
        protected_reserve_bytes=40 * gib,
        stop_margin_bytes=8 * gib,
        stop_floor_bytes=48 * gib,
        scratch_ceiling_bytes=24 * gib,
        retention_ceiling_bytes=24 * gib,
        working_ceiling_bytes=30 * gib,
    )
    return _ContinuousDiskGuard(base, 125 * gib, root)


def _reject_symlinks_under(path: Path) -> None:
    stack = [path]
    while stack:
        directory = stack.pop()
        if directory.is_symlink():
            raise BenchmarkError(f"auxiliary source projection contains a symlink: {directory}")
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise BenchmarkError(f"cannot inspect auxiliary source projection {directory}: {exc}") from exc
        for entry in entries:
            if entry.is_symlink():
                raise BenchmarkError(f"auxiliary source projection contains a symlink: {entry}")
            if entry.is_dir():
                stack.append(entry)


def _auxiliary_source_projection_roots(root: Path) -> list[Path]:
    """Find complete non-runtime source projections under the bounded v092 namespace."""
    repository_root = root.resolve(strict=True)
    execution_state = root / "execution-state"
    if execution_state.is_symlink():
        raise BenchmarkError("execution-state is symlinked during auxiliary source accounting")
    if not execution_state.exists():
        return []
    if not execution_state.is_dir():
        raise BenchmarkError("execution-state is not a directory during auxiliary source accounting")
    try:
        execution_state.resolve(strict=True).relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise BenchmarkError("execution-state escapes the repository during auxiliary source accounting") from exc
    base = execution_state / "v092"
    if not base.exists():
        return []
    if base.is_symlink() or not base.is_dir():
        raise BenchmarkError("execution-state/v092 root is unsafe during source-projection accounting")
    excluded = {"groups", "cache", "tools", "builds", "swift-source"}
    found: list[Path] = []
    stack = [(base, 0)]
    while stack:
        directory, depth = stack.pop()
        if depth == 1 and directory.name in excluded:
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise BenchmarkError(f"unsafe path in bounded source-projection discovery: {directory}")
        if (directory != base and depth <= 3 and
                (directory / "Cargo.toml").is_file() and not (directory / "Cargo.toml").is_symlink() and
                (directory / "src").is_dir() and not (directory / "src").is_symlink() and
                (directory / "cases").is_dir() and not (directory / "cases").is_symlink()):
            _reject_symlinks_under(directory)
            found.append(directory.resolve())
            continue
        if depth >= 3:
            continue
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise BenchmarkError(f"cannot enumerate bounded source-projection path {directory}: {exc}") from exc
        for child in children:
            if depth == 0 and child.name in excluded:
                continue
            if child.is_symlink():
                raise BenchmarkError(f"symlink in bounded source-projection discovery: {child}")
            if child.is_dir():
                stack.append((child, depth + 1))
    return sorted(found)


def _capacity_source_inventory(root: Path, core, base_contract: dict,
                               ledger_paths: Sequence[str], current_source_inputs: Sequence[dict]) -> dict:
    paths = list(core.SNAPSHOT_DIRECTORIES) + list(core.SNAPSHOT_FILES) + [".git"]
    for item in base_contract.get("source_inputs", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise BenchmarkError("C4 historical source-input reference is malformed")
        paths.append(_accounting_source_path(root, item["path"], "C4 historical source-input path"))
    for value in ledger_paths:
        if not isinstance(value, str):
            raise BenchmarkError("ledger historical source-input path is malformed")
        paths.append(_accounting_source_path(root, value, "ledger historical source-input path"))
    for item in current_source_inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise BenchmarkError("current C5 source-input reference is malformed")
        paths.append(_accounting_source_path(root, item["path"], "current C5 source-input path"))
    unique = sorted(set(paths))
    return {
        "paths": unique,
        "path_count": len(unique),
        "paths_sha256": _sha(_canonical_json(unique)),
        "present_logical_bytes": _strict_guard_module.DiskGuard.logical_size([root / value for value in unique]),
    }


def _historical_capacity_paths(root: Path, contract: dict, history: dict,
                                core, *, execution_root: Path, env: Mapping[str, str],
                                output_roots: Sequence[Path],
                                current_source_inputs: Sequence[dict]) -> tuple[list[Path], list[Path], list[Path], int, list[dict], dict]:
    base = _read_json(root / BASE_CONTRACT_REL, "C4 baseline contract")[0]
    source_inventory = _capacity_source_inventory(
        root, core, base, history["ledger"]["capacity_paths"]["source_inputs"], current_source_inputs)
    source_members = source_inventory["paths"]
    historical_sources: list[Path] = []
    source_roots = set(Path(value) for value in history["execution_roots"])
    groups_root = root / EXECUTION_GROUPS_REL
    if groups_root.exists():
        all_ids = {item["id"] for item in base["groups"]}
        for series_dir in groups_root.iterdir():
            if series_dir.is_symlink() or not series_dir.is_dir():
                raise BenchmarkError(f"historical source namespace is unsafe: {series_dir}")
            if not re.fullmatch(r"series-\d+", series_dir.name):
                continue
            for group_dir in series_dir.iterdir():
                if group_dir.is_symlink() or not group_dir.is_dir():
                    raise BenchmarkError(f"historical source namespace is unsafe: {group_dir}")
                if group_dir.name not in all_ids:
                    continue
                for attempt_dir in group_dir.iterdir():
                    if attempt_dir.is_symlink() or not attempt_dir.is_dir():
                        raise BenchmarkError(f"historical source attempt is unsafe: {attempt_dir}")
                    source_roots.add(attempt_dir)
    for source_root in sorted(source_roots):
        try:
            source_root.resolve(strict=False).relative_to((root / EXECUTION_GROUPS_REL).resolve())
        except ValueError as exc:
            raise BenchmarkError("historical source path escaped execution-state/v092/groups") from exc
        historical_sources.extend(source_root / value for value in source_members)
        per_source_bytes = _strict_guard_module.DiskGuard.logical_size(
            [source_root / value for value in source_members])
        if per_source_bytes > RESOURCE_POLICY["source_per_attempt_ceiling_gib"] * 1024**3:
            raise BenchmarkError(f"historical source snapshot exceeds the 12 GiB per-source ceiling: {source_root}")
    current_members = list(core.SNAPSHOT_DIRECTORIES) + list(core.SNAPSHOT_FILES)
    current_members.extend(_accounting_source_path(root, item["path"], "current C5 source-input path")
                           for item in current_source_inputs)
    current_paths = [execution_root / value for value in sorted(set(current_members))]
    # The current worktree's source is part of the same aggregate source budget;
    # historical C4 inputs remain counted even when absent from the new Git tree.
    repository_members = source_members
    historical_sources.extend(root / value for value in repository_members)
    if _strict_guard_module.DiskGuard.logical_size([root / value for value in repository_members]) > RESOURCE_POLICY["source_per_attempt_ceiling_gib"] * 1024**3:
        raise BenchmarkError("current repository source exceeds the 12 GiB per-source ceiling")
    auxiliary_roots = _auxiliary_source_projection_roots(root)
    auxiliary_projections = []
    for path in auxiliary_roots:
        size = _strict_guard_module.DiskGuard.logical_size([path])
        if size > RESOURCE_POLICY["source_per_attempt_ceiling_gib"] * 1024**3:
            raise BenchmarkError(f"auxiliary source projection exceeds the 12 GiB per-source ceiling: {path}")
        auxiliary_projections.append({"path": str(path), "bytes": size})
    historical_sources.extend(auxiliary_roots)
    working_baseline_bytes = _strict_guard_module.DiskGuard.logical_size(historical_sources)
    capacity = history["ledger"]["capacity_paths"]
    retained = [root / "reports/releases/v0.9.2", *output_roots]
    retained.extend(Path(value) for value in capacity["output_roots"])
    scratch = [root / CACHE_REL, Path(env["HOME"]), Path(env["TMPDIR"])]
    scratch.extend(Path(value) for value in capacity["cache_roots"])
    scratch.extend(Path(value) for value in capacity["home_paths"])
    scratch.extend(Path(value) for value in capacity["tmp_paths"])
    for value in history.get("execution_roots", []):
        previous = Path(value)
        scratch.extend((previous / "home", previous / "tmp"))
    return current_paths, retained, scratch, working_baseline_bytes, auxiliary_projections, source_inventory


def _verify_source_capacity_admission(root: Path, validated: dict, row: dict, *,
                                      require_current_roster: bool = False) -> None:
    admission = row.get("source_capacity_admission")
    contract = validated["contract"]
    if (not isinstance(admission, dict) or admission.get("resource_policy") != contract.get("resource_policy") or
            admission.get("continuous_free_space_floor_bytes") != 125 * 1024**3 or
            admission.get("launch_free_space_floor_bytes") != 127 * 1024**3 or
            admission.get("protected_reserve_bytes") != 40 * 1024**3 or
            admission.get("emergency_stop_margin_bytes") != 8 * 1024**3):
        raise BenchmarkError("C5 attempt source-capacity admission policy is missing or changed")
    projections = admission.get("auxiliary_source_projections")
    if not isinstance(projections, list):
        raise BenchmarkError("C5 auxiliary source-projection admission roster is malformed")
    repository_root = root.resolve(strict=True)
    execution_state = root / "execution-state"
    base_root = root / "execution-state/v092"
    if execution_state.is_symlink() or base_root.is_symlink() or not base_root.is_dir():
        raise BenchmarkError("C5 auxiliary source-capacity root is missing or symlinked")
    try:
        resolved_base = base_root.resolve(strict=True)
        resolved_base.relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise BenchmarkError("C5 auxiliary source-capacity root escapes the repository") from exc
    paths = []
    normalized = []
    excluded_roots = {"groups", "cache", "tools", "builds", "swift-source"}
    for item in projections:
        if (not isinstance(item, dict) or not isinstance(item.get("path"), str) or
                type(item.get("bytes")) is not int or item["bytes"] < 0):
            raise BenchmarkError("C5 auxiliary source-projection admission entry is malformed")
        path = Path(item["path"])
        try:
            relative_path = path.relative_to(base_root)
        except ValueError as exc:
            raise BenchmarkError("C5 auxiliary source-projection path is outside its fixed root") from exc
        if (not relative_path.parts or len(relative_path.parts) > 3 or
                relative_path.parts[0] in excluded_roots):
            raise BenchmarkError("C5 auxiliary source-projection path is outside its bounded discovery scope")
        cursor = base_root
        for part in relative_path.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise BenchmarkError(f"C5 auxiliary source projection traverses a symlink: {cursor}")
        try:
            path.resolve(strict=True).relative_to(resolved_base)
        except (OSError, ValueError) as exc:
            raise BenchmarkError("C5 auxiliary source projection escaped the v0.9.2 execution state") from exc
        if (path.is_symlink() or not path.is_dir() or
                any((path / name).is_symlink() for name in ("Cargo.toml", "src", "cases")) or
                not (path / "Cargo.toml").is_file() or not (path / "src").is_dir() or
                not (path / "cases").is_dir()):
            raise BenchmarkError(f"C5 auxiliary source projection is missing or unsafe: {path}")
        _reject_symlinks_under(path)
        actual = _strict_guard_module.DiskGuard.logical_size([path])
        if actual != item["bytes"]:
            raise BenchmarkError(f"C5 auxiliary source projection changed after admission: {path}")
        paths.append(path)
        normalized.append({"path": str(path.resolve()), "bytes": actual})
    if normalized != sorted(normalized, key=lambda item: item["path"]):
        raise BenchmarkError("C5 auxiliary source-projection admission roster is not canonical")
    auxiliary_bytes = _strict_guard_module.DiskGuard.logical_size(paths)
    if (admission.get("auxiliary_source_projection_bytes") != auxiliary_bytes or
            type(admission.get("working_baseline_bytes")) is not int or
            admission["working_baseline_bytes"] < 0 or
            type(admission.get("projected_source_bytes")) is not int or
            admission["projected_source_bytes"] < 0):
        raise BenchmarkError("C5 source-capacity admission byte totals are malformed")
    core, _ = _load_core(root, contract["source_snapshot"]["core_helpers"][0]["sha256"])
    base = _read_json(root / BASE_CONTRACT_REL, "C4 baseline contract")[0]
    source_inventory = _capacity_source_inventory(
        root, core, base, validated["ledger"]["capacity_paths"]["source_inputs"],
        contract["source_snapshot"]["source_inputs"])
    if (admission.get("source_input_path_count") != source_inventory["path_count"] or
            admission.get("source_input_paths_sha256") != source_inventory["paths_sha256"] or
            type(admission.get("source_input_present_logical_bytes")) is not int or
            admission["source_input_present_logical_bytes"] < 0 or
            (require_current_roster and admission["source_input_present_logical_bytes"] !=
             source_inventory["present_logical_bytes"])):
        raise BenchmarkError("C5 source-capacity historical path inventory changed")
    if require_current_roster and paths != _auxiliary_source_projection_roots(root):
        raise BenchmarkError("C5 auxiliary source-projection roster changed before analyzer launch")


def _durable_append(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise BenchmarkError(f"append-only progress path is symlinked: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o644)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        raw = _canonical_json(value) + b"\n"
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise BenchmarkError(f"short durable append to {path}")
            view = view[written:]
        os.fsync(descriptor)
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _fsync_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise BenchmarkError(f"cannot durably sync missing or unsafe file: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_parent(path: Path) -> None:
    descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_terminal(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        _atomic_write(path, _pretty_json(value))
    else:
        _atomic_write(path, _pretty_json(value), exclusive=True)


def _runtime_environment(group: dict, execution_root: Path, cache_root: Path) -> dict[str, str]:
    source = group.get("environment")
    if not isinstance(source, dict) or source.get("BIFROST_OPEN_PACKS_DISABLE") != "1":
        raise BenchmarkError(f"group {group.get('id')} can acquire open packs or lacks an environment")
    env = {}
    for key, value in source.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise BenchmarkError(f"group {group.get('id')} environment is malformed")
        env[key] = value.replace("@EXECUTION_ROOT@", str(execution_root)).replace(
            "@CACHE_ROOT@", str(cache_root))
        if "@EXECUTION_ROOT@" in env[key] or "@CACHE_ROOT@" in env[key]:
            raise BenchmarkError(f"group {group.get('id')} environment has an unresolved path marker")
    env["HOME"] = str(execution_root / "home")
    env["TMPDIR"] = str(execution_root / "tmp")
    env["DFB_CACHE_ROOT"] = str(cache_root)
    env["BIFROST_CACHE_ROOT"] = str(cache_root)
    env["BIFROST_OPEN_PACKS_DISABLE"] = "1"
    return env


def _stage_scala_maven(validated: dict, home: Path, disk_guard) -> dict:
    destination_root = home / ".m2/repository/org/scala-lang/scala-library/2.13.16"
    destination_root.mkdir(parents=True, exist_ok=False)
    staged = []
    for artifact in validated["scala"]["artifacts"]:
        source = Path(artifact["source_path"])
        name = artifact["name"]
        if source.is_symlink() or not source.is_file() or _sha_file(source) != artifact["sha256"]:
            raise BenchmarkError(f"pinned Scala artifact changed before isolated staging: {source}")
        destination = destination_root / name
        if destination.exists() or destination.is_symlink():
            raise BenchmarkError(f"Scala staging destination already exists: {destination}")
        disk_guard.check(projected_bytes=artifact["size_bytes"], category="scratch",
                         paths=[home], capacity_path=home)
        with source.open("rb") as incoming, destination.open("xb") as outgoing:
            copied = 0
            while True:
                chunk = incoming.read(1024 * 1024)
                if not chunk:
                    break
                outgoing.write(chunk)
                copied += len(chunk)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if copied != artifact["size_bytes"] or _sha_file(destination) != artifact["sha256"]:
            raise BenchmarkError(f"Scala staged artifact failed its size/SHA-256 check: {name}")
        staged.append({"path": str(destination), "sha256": artifact["sha256"], "bytes": copied,
                       "role": artifact["role"]})
    if {item.name for item in destination_root.iterdir()} != set(SCALA_FILES):
        raise BenchmarkError("isolated Scala Maven directory contains unapproved staged files")
    _fsync_parent(destination_root / "scala-library-2.13.16.jar")
    return {"repository": str(destination_root), "artifacts": staged,
            "source_entry_count": validated["scala"]["source_entry_count"]}


def _check_scala_staging(row: dict, execution_root: Path, validated: dict, *, require_postcheck: bool = False) -> dict:
    group_id = row.get("group_id")
    staging = row.get("scala_maven_staging")
    if group_id != "bifrost-scala-kernel":
        if staging is not None:
            raise BenchmarkError("Scala Maven files were staged into a non-Scala Bifrost attempt")
        if row.get("scala_maven_staging_seconds") is None:
            if row.get("scala_maven_staging_postcheck") != {"verified": False, "not_reached": True, "artifacts": []}:
                raise BenchmarkError("non-Scala preflight attempt has a malformed Maven not-reached receipt")
            return {"verified": False, "not_reached": True, "artifacts": []}
        if row.get("scala_maven_staging_seconds") != 0.0 or row.get("scala_maven_staging_postcheck") not in (None, {"verified": True, "artifacts": []}):
            raise BenchmarkError("non-Scala attempt contains a Scala Maven postcheck")
        if require_postcheck and row.get("scala_maven_staging_postcheck") != {"verified": True, "artifacts": []}:
            raise BenchmarkError("non-Scala postcheck receipt is missing or malformed")
        return {"verified": True, "artifacts": []}
    if not isinstance(staging, dict):
        if (row.get("status") != "completed" and
                row.get("process_ownership", {}).get("root_pid") is None and
                row.get("scala_maven_staging_postcheck", {}).get("not_reached") is True):
            partial = row.get("scala_maven_staging_partial", [])
            if not isinstance(partial, list):
                raise BenchmarkError("Scala partial-staging receipt is malformed")
            allowed = set(SCALA_FILES)
            home = Path(row.get("environment", {}).get("HOME", ""))
            partial_root = home / ".m2/repository/org/scala-lang/scala-library/2.13.16"
            observed = []
            for entry in partial:
                if not isinstance(entry, dict) or Path(entry.get("path", "")).name not in allowed:
                    raise BenchmarkError("Scala partial staging contains an unapproved artifact path")
                file_path = Path(entry["path"])
                if (file_path.parent != partial_root or file_path.is_symlink() or not file_path.is_file() or
                        file_path.stat().st_size != entry.get("bytes") or _sha_file(file_path) != entry.get("sha256")):
                    raise BenchmarkError("Scala partial staging evidence changed")
                observed.append({"path": str(file_path), "sha256": entry["sha256"], "bytes": entry["bytes"]})
            if len({Path(item["path"]).name for item in observed}) != len(observed):
                raise BenchmarkError("Scala partial staging repeats a file identity")
            return {"verified": False, "not_reached": True, "partial_artifacts": observed, "artifacts": []}
        raise BenchmarkError("Scala attempt lacks exact Maven staging evidence")
    expected_root = (Path(row["environment"]["HOME"]) /
                     ".m2/repository/org/scala-lang/scala-library/2.13.16")
    if (Path(row["environment"]["HOME"]) != execution_root / "home" or
            Path(staging.get("repository", "")) != expected_root or
            staging.get("source_entry_count") != validated["scala"]["source_entry_count"]):
        raise BenchmarkError("Scala staged repository or sources-jar identity differs from the C5 binding")
    entries = staging.get("artifacts")
    if not isinstance(entries, list) or len(entries) != len(SCALA_FILES):
        raise BenchmarkError("Scala attempt staging receipt does not contain exactly three Maven artifacts")
    by_name = {Path(item.get("path", "")).name: item for item in entries if isinstance(item, dict)}
    if set(by_name) != set(SCALA_FILES):
        raise BenchmarkError("Scala attempt staging receipt contains an unexpected artifact roster")
    observed = []
    for name, expected in SCALA_FILES.items():
        item = by_name[name]
        path = expected_root / name
        if (Path(item.get("path", "")) != path or item.get("sha256") != expected["sha256"] or
                item.get("bytes") != expected["size_bytes"] or item.get("role") != expected["role"] or
                path.is_symlink() or not path.is_file() or path.stat().st_size != expected["size_bytes"] or
                _sha_file(path) != expected["sha256"]):
            raise BenchmarkError(f"Scala attempt staged artifact changed: {name}")
        observed.append({"name": name, "sha256": expected["sha256"], "bytes": expected["size_bytes"]})
    if {item.name for item in expected_root.iterdir()} != set(SCALA_FILES):
        raise BenchmarkError("Scala Maven attempt repository contains an unapproved artifact")
    postcheck = row.get("scala_maven_staging_postcheck")
    if require_postcheck and (not isinstance(postcheck, dict) or postcheck.get("verified") is not True or postcheck.get("artifacts") != observed):
        raise BenchmarkError("Scala staged Maven files were not independently rehashed after execution")
    return {"verified": True, "artifacts": observed}


def _group_attempt_state(validated: dict, group_id: str) -> tuple[list[dict], int]:
    rows = [row for row in validated["ledger"]["target_rows"] if row.get("group_id") == group_id]
    records = [item for item in validated["history"].get("target_records", [])
               if item.get("group_id") == group_id]
    keyed = {(item["group_id"], item["attempt_id"]): item for item in records}
    if len(keyed) != len(records):
        raise BenchmarkError(f"C5 target namespace duplicates an attempt for {group_id}")
    if len(rows) != sum(1 for item in records if item.get("ledger_recorded")):
        raise BenchmarkError(f"C5 target ledger and started namespaces disagree for {group_id}")
    if any(not item.get("ledger_recorded") for item in records):
        raise BenchmarkError(f"C5 has an unclosed started attempt for {group_id}; automatic recovery is forbidden")
    if len(records) >= ATTEMPT_POLICY["new_target_slots_per_group"]:
        raise BenchmarkError(f"C5 target attempt budget is exhausted for {group_id}")
    for row in rows:
        if row.get("status") not in {"failed", "timed-out", "capacity-lost", "recorder-error", "completed"}:
            raise BenchmarkError(f"C5 has a non-terminal target row for {group_id}")
    if rows and rows[-1].get("status") == "completed":
        raise BenchmarkError(f"C5 group already has completed target evidence: {group_id}")
    history_counter = validated["contract"]["attempt_history"]["historical_group_counters"][group_id]
    attempt_number = history_counter["prior_max_attempt_number"] + len(records) + 1
    return rows, attempt_number


def _one_group(validated: dict, group_id: str, *, global_attempt_number: int,
               remaining_group_count: int, invocation_id: str) -> dict:
    contract = validated["contract"]
    root = validated["path"].parents[5]
    group_projection = next((item for item in contract["groups"] if item["id"] == group_id), None)
    if group_projection is None:
        raise BenchmarkError(f"group is outside the fixed C5 roster: {group_id}")
    group = group_projection["base_group"]
    prior_rows, attempt_number = _group_attempt_state(validated, group_id)
    attempt_id = f"{group_id}-attempt-{attempt_number:02d}-series-{SERIES:02d}"
    attempts = root / ATTEMPTS_REL / attempt_id
    execution_root = root / EXECUTION_GROUPS_REL / SERIES_LABEL / group_id / f"attempt-{attempt_number:02d}"
    cache_root = root / CACHE_REL / SERIES_LABEL / group_id / f"attempt-{attempt_number:02d}"
    ledger_path = root / LEDGER_REL
    for candidate in (attempts, execution_root, cache_root):
        if candidate.exists() or candidate.is_symlink():
            raise BenchmarkError(f"C5 refuses to reuse an existing attempt path: {candidate}")
    report_specs = group_projection.get("runtime_reports")
    if not isinstance(report_specs, list) or len(report_specs) != 1:
        raise BenchmarkError(f"Bifrost target group must retain exactly one report partition: {group_id}")
    report_attempt_root = root / NORMAL_ATTEMPTS_REL / attempt_id
    for report in report_specs:
        relative = PurePosixPath(report["path"])
        destination = report_attempt_root / Path(*relative.relative_to(PurePosixPath("reports/releases/v0.9.2/normal")).parts)
        if destination.exists() or destination.is_symlink():
            raise BenchmarkError(f"C5 refuses to overwrite a staged report: {destination}")

    raw_roots = [execution_root / value for value in group["output_roots"]]
    env = _runtime_environment(group, execution_root, cache_root)
    core, core_sha = _load_core(root, contract["source_snapshot"]["core_helpers"][0]["sha256"])
    if core_sha != contract["source_snapshot"]["core_helpers"][0]["sha256"]:
        raise BenchmarkError("core helper hash changed before C5 attempt admission")
    disk_guard = _disk_guard(root, core)
    current_paths, retained_paths, scratch_paths, historical_source_bytes, auxiliary_projections, source_inventory = _historical_capacity_paths(
        root, contract, validated["history"], core,
        execution_root=execution_root, env=env, output_roots=raw_roots,
        current_source_inputs=contract["source_snapshot"]["source_inputs"],
    )
    source_refs = [item["path"] for item in contract["source_snapshot"]["source_inputs"]]
    projected_source_bytes = core._materialize_source(
        root, validated["source_commit"], execution_root, source_refs,
        disk_guard=disk_guard, working_paths=current_paths,
        working_baseline_bytes=historical_source_bytes, preflight_only=True,
    )
    if type(projected_source_bytes) is not int:
        raise BenchmarkError("source materialization preflight did not report a bounded projection")
    if projected_source_bytes > RESOURCE_POLICY["source_per_attempt_ceiling_gib"] * 1024**3:
        raise BenchmarkError("single C5 source projection exceeds the 12 GiB per-attempt ceiling")
    reserve_projection = (projected_source_bytes + 1024**2) * remaining_group_count
    disk_guard.check(projected_bytes=reserve_projection,
                     additional_current_bytes=historical_source_bytes,
                     category="working", paths=current_paths, capacity_path=root,
                     phase="launch")
    disk_guard.check(projected_bytes=1024**2, category="retention", paths=retained_paths,
                     capacity_path=root, phase="launch")
    disk_guard.check(projected_bytes=1024**2, category="scratch", paths=scratch_paths,
                     capacity_path=root, phase="launch")

    attempts.mkdir(parents=True)
    execution_root.parent.mkdir(parents=True, exist_ok=True)
    cache_root.parent.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir()
    start_admission = dt.datetime.now(dt.timezone.utc).isoformat()
    started = {
        "schema_version": 1, "schema": ATTEMPT_RECEIPT_SCHEMA,
        "release": RELEASE, "target_id": TARGET_ID, "execution_series": SERIES,
        "global_attempt_number": global_attempt_number, "group_id": group_id,
        "attempt_id": attempt_id, "status": "started", "admitted_at_utc": start_admission,
        "source_commit": validated["source_commit"], "plan_commit": validated["plan_commit"],
        "contract_sha256": validated["contract_sha256"],
        "runner_source_sha256": contract["source_snapshot"]["runner_source"]["sha256"],
        "core_runner_sha256": core_sha, "fixture_revision": FIXTURE_REVISION,
        "population": contract["parent_population"]["population"],
        "tool": "bifrost", "tool_binding": validated["bifrost"],
        "qualification": validated["qualification"],
        "source_inputs": contract["source_snapshot"]["source_inputs"],
        "cache_root": str(cache_root), "argv": group_projection["runtime_argv"],
        "environment": env, "execution_root": str(execution_root),
        "output_roots": list(group["output_roots"]), "case_ids": list(group["case_ids"]),
        "deadline_seconds": group["deadline_seconds"], "started_receipt": "started.json",
        "scala_maven_staging": None, "scala_maven_staging_seconds": None,
        "scala_maven_staging_started": False, "scala_maven_staging_partial": [],
        "target_provenance": {
            "contract_path": CONTRACT_REL, "contract_sha256": validated["contract_sha256"],
            "parent_c4_contract_sha256": BASE_C4_CONTRACT_SHA256,
            "parent_population_sha256": BASE_POPULATION_SHA256,
            "source_closure_sha256": _sha(_canonical_json(contract["source_snapshot"])),
            "runner_binary_sha256": contract["runtime"]["runner"]["sha256"],
            "bifrost_version": BIFROST_VERSION, "bifrost_build_identity": BIFROST_BUILD_IDENTITY,
            "scala_maven": contract["runtime"]["scala_maven"],
        },
        "ledger_stage_proof": {
            "pre_append_line_count": validated["ledger"]["line_count"],
            "pre_append_bytes": validated["ledger"]["bytes"],
            f"original_{LEDGER_PREFIX_LINES}_row_prefix_sha256": LEDGER_PREFIX_SHA256,
            "target_suffix_line_count_before": validated["ledger"].get("target_line_count", 0),
            "target_suffix_sha256_before": validated["ledger"].get("target_suffix_sha256", _sha(b"")),
        },
        "source_capacity_admission": {
            "working_baseline_bytes": historical_source_bytes,
            "projected_source_bytes": projected_source_bytes,
            "auxiliary_source_projections": auxiliary_projections,
            "auxiliary_source_projection_bytes": _strict_guard_module.DiskGuard.logical_size(
                [Path(item["path"]) for item in auxiliary_projections]),
            "source_input_path_count": source_inventory["path_count"],
            "source_input_paths_sha256": source_inventory["paths_sha256"],
            "source_input_present_logical_bytes": source_inventory["present_logical_bytes"],
            "resource_policy": contract["resource_policy"],
            "continuous_free_space_floor_bytes": 125 * 1024**3,
            "launch_free_space_floor_bytes": 127 * 1024**3,
            "protected_reserve_bytes": 40 * 1024**3,
            "emergency_stop_margin_bytes": 8 * 1024**3,
        },
    }
    _atomic_write(attempts / "started.json", _pretty_json(started), exclusive=True)
    _durable_append(root / PROGRESS_REL, {
        "schema": PROGRESS_SCHEMA, "at_utc": start_admission,
        "target_id": TARGET_ID, "contract_sha256": validated["contract_sha256"],
        "invocation_id": invocation_id, "phase": "attempt-started",
        "global_attempt_number": global_attempt_number, "group_id": group_id, "attempt_id": attempt_id,
        "ledger_pre_append_line_count": started["ledger_stage_proof"]["pre_append_line_count"],
        "target_suffix_line_count_before": started["ledger_stage_proof"]["target_suffix_line_count_before"],
        "target_suffix_sha256_before": started["ledger_stage_proof"]["target_suffix_sha256_before"],
    })
    row = dict(started)
    analyzer_started_at = None
    try:
        source_start = time.monotonic()
        core._assert_source_snapshot(root, validated["source_commit"], core_sha,
                                     contract["source_snapshot"]["source_inputs"])
        core._materialize_source(
            root, validated["source_commit"], execution_root, source_refs,
            disk_guard=disk_guard, working_paths=current_paths,
            working_baseline_bytes=historical_source_bytes,
            expected_projected_bytes=projected_source_bytes,
        )
        row["source_materialization_seconds"] = time.monotonic() - source_start
        row["source_materialization_projected_bytes"] = projected_source_bytes
        current_source_bytes = _strict_guard_module.DiskGuard.logical_size(current_paths)
        if current_source_bytes > RESOURCE_POLICY["source_per_attempt_ceiling_gib"] * 1024**3:
            raise BenchmarkError("materialized C5 source exceeds the 12 GiB per-attempt ceiling")
        home = Path(env["HOME"])
        home.mkdir(parents=True, exist_ok=True)
        Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
        row["scala_maven_staging"] = None
        if group_id == "bifrost-scala-kernel":
            stage_start = time.monotonic()
            row["scala_maven_staging_started"] = True
            row["scala_maven_staging"] = _stage_scala_maven(validated, home, disk_guard)
            row["scala_maven_staging_seconds"] = time.monotonic() - stage_start
            row["scala_maven_staging_started"] = False
        else:
            row["scala_maven_staging_seconds"] = 0.0
        core._assert_source_snapshot(root, validated["source_commit"], core_sha,
                                     contract["source_snapshot"]["source_inputs"])
        core._check_tool_file({"path": validated["runner_path"],
                               "sha256": contract["runtime"]["runner"]["sha256"]}, "C5 optimized harness")
        if _sha_file(Path(validated["bifrost"]["path"])) != BIFROST_BINARY_SHA256:
            raise BenchmarkError("pinned Bifrost binary changed before group execution")
        for output_root in raw_roots:
            if output_root.exists() or output_root.is_symlink():
                raise BenchmarkError(f"C5 output root is not fresh: {output_root}")
        _verify_source_capacity_admission(root, validated, row, require_current_roster=True)
        core._check_resources(root, 127 * 1024**3)
        analyzer_started_at = dt.datetime.now(dt.timezone.utc).isoformat()
        row["start_utc"] = analyzer_started_at
        row["process_ownership"] = {}
        exit_code, timed_out, duration, capacity_loss = core._run_process(
            group_projection["runtime_argv"], execution_root, env,
            attempts / "stdout.txt", attempts / "stderr.txt", group["deadline_seconds"],
            ownership=row["process_ownership"], retained_paths=retained_paths,
            retention_limit=24 * 1024**3, scratch_paths=scratch_paths,
            scratch_limit=24 * 1024**3, disk_guard=disk_guard,
            working_paths=current_paths, working_baseline_bytes=historical_source_bytes,
        )
        row.update({"exit_code": exit_code, "timed_out": timed_out, "duration_seconds": duration,
                    "capacity_loss": capacity_loss,
                    "stdout": core._file_receipt(attempts / "stdout.txt", "stdout.txt"),
                    "stderr": core._file_receipt(attempts / "stderr.txt", "stderr.txt")})
        core._assert_source_snapshot(root, validated["source_commit"], core_sha,
                                     contract["source_snapshot"]["source_inputs"])
        if _sha_file(Path(validated["bifrost"]["path"])) != BIFROST_BINARY_SHA256:
            raise BenchmarkError("pinned Bifrost binary changed during group execution")
        capture_root = attempts / "capture"
        capture_rows = []
        capture_plans = [core._copy_tree(
            output_root, execution_root, execution_root, capture_root,
            disk_guard=disk_guard, disk_guard_module=_strict_guard_module,
            accounting_paths=retained_paths, preflight_only=True,
        ) for output_root in raw_roots]
        capture_projection = sum(item["bytes"] for planned in capture_plans for item in planned)
        disk_guard.check(projected_bytes=capture_projection, category="retention",
                         paths=retained_paths, capacity_path=root)
        for output_root, planned in zip(raw_roots, capture_plans):
            capture_rows.extend(core._copy_tree(
                output_root, execution_root, execution_root, capture_root,
                disk_guard=disk_guard, disk_guard_module=_strict_guard_module,
                accounting_paths=retained_paths, planned_files=planned,
            ))
        for item in capture_rows:
            _fsync_file(Path(item["capture_path"]))
        row["captured_files"] = sorted(capture_rows, key=lambda item: item["execution_relative"])
        capture_map = {item["execution_relative"]: item for item in capture_rows}
        row["reports"] = []
        if exit_code == 0 and not timed_out and capacity_loss is None:
            for report in report_specs:
                row["reports"].append(core._stage_report(
                    root, attempts, execution_root, attempt_id, report, capture_map,
                    raw_roots, FIXTURE_REVISION, disk_guard=disk_guard,
                    retained_paths=retained_paths,
                ))
            for report in row["reports"]:
                _fsync_file(root / report["original_path"])
                _fsync_file(root / report["staged_path"])
        row["status"] = ("capacity-lost" if capacity_loss else
                         "timed-out" if timed_out else "completed" if exit_code == 0 else "failed")
        row["capacity_loss"] = capacity_loss
    except BaseException as exc:
        capacity_codes = {"launch_floor", "stop_floor", "category_ceiling", "capacity_unavailable"}
        guard_error = getattr(exc, "as_dict", None)
        error_code = getattr(exc, "code", None)
        row["status"] = "capacity-lost" if error_code in capacity_codes else "recorder-error"
        if callable(guard_error):
            row["disk_guard_error"] = guard_error()
        row["recorder_error"] = f"{type(exc).__name__}: {exc}"
        row.setdefault("exit_code", 125)
        row.setdefault("timed_out", False)
        ownership = row.get("process_ownership")
        if isinstance(ownership, dict) and ownership.get("root_pid") is not None:
            row.setdefault("duration_seconds", None)
            row["analyzer_duration_complete"] = False
        else:
            row.setdefault("duration_seconds", 0.0)
            row["analyzer_duration_complete"] = True
        row.setdefault("capacity_loss", None)
        row["reports"] = []
        for field in ("stdout", "stderr"):
            stream = attempts / (field + ".txt")
            if not stream.exists():
                _atomic_write(stream, b"", exclusive=True)
            row[field] = core._file_receipt(stream, field + ".txt")
        try:
            core._preserve_recorder_failure(root, attempts, attempt_id, row)
        except BaseException as preserve_error:
            row["capture_preservation_error"] = f"{type(preserve_error).__name__}: {preserve_error}"
    finally:
        try:
            if (group_id != "bifrost-scala-kernel" and row.get("scala_maven_staging_seconds") is None):
                row["scala_maven_staging_postcheck"] = {
                    "verified": False, "not_reached": True, "artifacts": []}
            elif (group_id == "bifrost-scala-kernel" and row.get("scala_maven_staging") is None and
                    row.get("scala_maven_staging_started") is not True):
                row["scala_maven_staging_postcheck"] = {
                    "verified": False, "not_reached": True, "artifacts": []}
            elif (group_id == "bifrost-scala-kernel" and row.get("scala_maven_staging_started") is True):
                partial_root = Path(env["HOME"]) / ".m2/repository/org/scala-lang/scala-library/2.13.16"
                partial = []
                if partial_root.exists() and not partial_root.is_symlink():
                    for file_path in sorted(partial_root.iterdir(), key=lambda item: item.name):
                        if file_path.is_symlink() or not file_path.is_file():
                            raise BenchmarkError("Scala staging failed with an unsafe partial output")
                        partial.append({"path": str(file_path), "sha256": _sha_file(file_path),
                                        "bytes": file_path.stat().st_size})
                row["scala_maven_staging_partial"] = partial
                row["scala_maven_staging_postcheck"] = {
                    "verified": False, "not_reached": True, "partial_artifacts": partial, "artifacts": []}
            else:
                row["scala_maven_staging_postcheck"] = _check_scala_staging(row, execution_root, validated)
        except BaseException as staging_error:
            row["status"] = "recorder-error"
            row["reports"] = []
            row["recorder_error"] = (
                str(row.get("recorder_error", "")) +
                f"; Scala staging verification failed: {type(staging_error).__name__}: {staging_error}"
            ).strip("; ")
            try:
                core._preserve_recorder_failure(root, attempts, attempt_id, row)
            except BaseException as preserve_error:
                row["capture_preservation_error"] = f"{type(preserve_error).__name__}: {preserve_error}"
        row["end_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        row["source_and_recording_overhead_excluded_from_analyzer_time"] = True
        _atomic_write(attempts / "completed.json", _pretty_json(row), exclusive=True)
        core._append_ledger(ledger_path, row)
        row_bytes = json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        ledger_state = validated["ledger"].get("target_suffix_state")
        if ledger_state is not None:
            ledger_state.update(row_bytes)
        validated["ledger"]["line_count"] += 1
        validated["ledger"]["bytes"] += len(row_bytes)
        validated["ledger"]["target_line_count"] = validated["ledger"].get("target_line_count", 0) + 1
        validated["ledger"]["target_suffix_sha256"] = (
            ledger_state.hexdigest() if ledger_state is not None else None)
        validated["ledger"]["target_rows"].append(row)
        validated["ledger"].setdefault("target_stage_proofs", []).append({
            "group_id": group_id, "attempt_id": attempt_id,
            "line_count": validated["ledger"]["target_line_count"],
            "sha256": validated["ledger"]["target_suffix_sha256"],
        })
        validated["history"]["target_records"].append({
            "group_id": group_id, "attempt_id": attempt_id,
            "attempt_number": attempt_number, "execution_series": SERIES,
            "status": row["status"], "ledger_recorded": True,
            "sources": [f"target-ledger:{len(validated['ledger']['target_rows'])}"],
            "execution_roots": [str(execution_root)],
        })
        _durable_append(root / PROGRESS_REL, {
            "schema": PROGRESS_SCHEMA,
            "at_utc": row["end_utc"], "target_id": TARGET_ID,
            "contract_sha256": validated["contract_sha256"], "invocation_id": invocation_id,
            "phase": "attempt-terminal", "global_attempt_number": global_attempt_number,
            "group_id": group_id, "attempt_id": attempt_id, "status": row["status"],
            "ledger_line_count": validated["ledger"]["line_count"],
            "target_suffix_line_count": validated["ledger"]["target_line_count"],
            "target_suffix_sha256": validated["ledger"]["target_suffix_sha256"],
        })
    return row


def _validate_existing_target_attempts(validated: dict) -> list[dict]:
    records = validated["history"].get("target_records", [])
    rows = validated["ledger"].get("target_rows", [])
    if len(records) != len(rows) or any(not item.get("ledger_recorded") for item in records):
        raise BenchmarkError(f"{SERIES_LABEL} has an unledgered or unclosed C5 attempt; refusing resumption")
    by_key = {(row.get("group_id"), row.get("attempt_id")): row for row in rows}
    if len(by_key) != len(rows):
        raise BenchmarkError(f"{SERIES_LABEL} target ledger repeats an attempt identity")
    prior_count = validated["contract"]["attempt_history"]["global_prior_consumed_attempt_count"]
    rows_by_group = {}
    for index, row in enumerate(rows, start=1):
        expected_global = prior_count + index
        if row.get("global_attempt_number") != expected_global:
            raise BenchmarkError("C5 global attempt numbering is not strictly monotonic")
        expected_group_counter = validated["contract"]["attempt_history"]["historical_group_counters"][row["group_id"]]
        same_group = [item for item in rows[:index] if item.get("group_id") == row["group_id"]]
        expected_number = expected_group_counter["prior_max_attempt_number"] + len(same_group)
        attempt_number, series = _attempt_number(row["group_id"], row["attempt_id"])
        if attempt_number != expected_number or series != SERIES:
            raise BenchmarkError("C5 per-group attempt numbering is not monotonic across prior history")
        if (row.get("target_id") != TARGET_ID or row.get("contract_sha256") != validated["contract_sha256"] or
                row.get("source_commit") != validated["source_commit"] or
                row.get("plan_commit") != validated["plan_commit"]):
            raise BenchmarkError("C5 target ledger row provenance does not match the committed contract")
        rows_by_group.setdefault(row["group_id"], []).append(row)
    for group_id, group_rows in rows_by_group.items():
        completed = [item for item in group_rows if item.get("status") == "completed"]
        if len(completed) > 1 or (completed and group_rows[-1] is not completed[0]):
            raise BenchmarkError(f"C5 group {group_id} has a duplicate or non-terminal completed attempt")
    return rows


def _prepare(root: Path, args) -> dict:
    source_commit = args.source_commit
    if not COMMIT_RE.fullmatch(source_commit):
        raise BenchmarkError("--source-commit must be an exact lowercase Git commit")
    current_head = _git(root, "rev-parse", "HEAD").strip()
    if current_head != source_commit:
        raise BenchmarkError("prepare requires SOURCE to be the exact current committed HEAD")
    for relative in (PROGRESS_REL, SUMMARY_REL, INVOCATIONS_REL):
        path = root / relative
        if path.exists() or path.is_symlink():
            raise BenchmarkError(f"fresh C5 preparation refuses pre-existing execution output: {relative}")
    plan, population, base, _parent, all_ids = _base_inputs(root)
    ledger = _scan_ledger(root, all_ids)
    if (ledger["line_count"] != LEDGER_PREFIX_LINES or
            ledger["sha256"] != LEDGER_PREFIX_SHA256):
        raise BenchmarkError(
            f"preparation requires the exact authorized {LEDGER_PREFIX_LINES}-row append-only ledger prefix"
        )
    history = _scan_history(root, all_ids, preparing=True, ledger_result=ledger)
    core, core_sha = _load_core(root)
    native = dict(NATIVE_EVIDENCE_PATHS)
    for raw_ref in args.native_evidence:
        role, path = _parse_role_ref(raw_ref)
        if role in native and path != native[role]:
            raise BenchmarkError(f"native evidence role {role} was supplied more than once")
        native[role] = path
    runner = Path(args.runner).expanduser()
    if not runner.is_absolute():
        raise BenchmarkError("--runner must be an absolute path to the optimized harness")
    runner = runner.resolve(strict=True)
    contract = _make_manifest(
        root, source_commit=source_commit, runner_path=runner,
        qualification_path=args.qualification,
        bifrost_receipt_path=args.bifrost_receipt,
        scala_receipt_path=args.scala_receipt,
        native_evidence=native,
        ledger_snapshot={
            "path": LEDGER_REL, "line_count": ledger["line_count"],
            "bytes": ledger["bytes"], "sha256": ledger["sha256"],
            "preserved_prefix": ledger["preserved_prefix"],
        },
        history_snapshot=history["snapshot"],
    )
    # Keep preparation explicit about source helper identity even if an
    # integration process changed a helper between source closure and writing.
    if contract["source_snapshot"]["core_helpers"][0]["sha256"] != core_sha:
        raise BenchmarkError("C5 dynamic helper identity changed during preparation")
    path = _write_prepared_manifest(root, contract)
    return {"mode": "prepare", "path": str(path), "sha256": _sha_file(path),
            "execution_authorized": False, "source_commit": source_commit,
            "group_count": len(contract["groups"]), "parent_counts": contract["parent_population"]["full_counts"],
            "target_deadline_seconds": TARGET_WALL_BUDGET_SECONDS}


def _invocation_path(root: Path, invocation_id: str) -> Path:
    return root / INVOCATIONS_REL / f"{invocation_id}.json"


def _verify_invocation_history(root: Path, validated: dict) -> dict:
    progress_path = root / PROGRESS_REL
    invocation_dir = root / INVOCATIONS_REL
    if not progress_path.exists() and not invocation_dir.exists():
        return {"invocations": [], "events_by_invocation": {}, "invocation_order": []}
    if progress_path.is_symlink() or not progress_path.is_file() or invocation_dir.is_symlink() or not invocation_dir.is_dir():
        raise BenchmarkError("existing C5 progress/invocation state is incomplete or unsafe")
    invocations = {}
    for path in sorted(invocation_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise BenchmarkError(f"C5 invocation path is unsafe: {path}")
        receipt, _ = _read_json(path, "C5 invocation terminal receipt")
        if (receipt.get("schema") != INVOCATION_SCHEMA or
                receipt.get("target_id") != TARGET_ID or
                receipt.get("contract_sha256") != validated["contract_sha256"] or
                receipt.get("contract_path") != CONTRACT_REL or
                receipt.get("source_commit") != validated["source_commit"] or
                receipt.get("plan_commit") != validated["plan_commit"] or
                receipt.get("status") not in {"completed", "fail-stopped", "preflight-failed"}):
            raise BenchmarkError(f"C5 invocation terminal receipt is unclosed or misbound: {path}")
        if path.stem != receipt.get("invocation_id") or receipt["invocation_id"] in invocations:
            raise BenchmarkError(f"C5 invocation ID is duplicated or malformed: {path}")
        invocations[receipt["invocation_id"]] = receipt
    events_by_invocation = {}
    invocation_order = []
    active_invocation = None
    with progress_path.open("rb") as progress:
        for index, raw in enumerate(progress, start=1):
            if not raw.endswith(b"\n"):
                raise BenchmarkError("C5 progress journal has a truncated final record")
            try:
                event = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise BenchmarkError(f"C5 progress journal record {index} is invalid JSON") from exc
            if (not isinstance(event, dict) or event.get("schema") != PROGRESS_SCHEMA or
                    event.get("target_id") != TARGET_ID or event.get("contract_sha256") != validated["contract_sha256"] or
                    event.get("invocation_id") not in invocations):
                raise BenchmarkError(f"C5 progress journal record {index} is not bound to a terminal invocation")
            phase = event.get("phase")
            if phase not in {"invocation-started", "invocation-terminal", "attempt-started", "attempt-terminal"}:
                raise BenchmarkError(f"C5 progress journal record {index} has an unknown phase")
            event_invocation = event["invocation_id"]
            if phase == "invocation-started":
                if active_invocation is not None or event_invocation in invocation_order:
                    raise BenchmarkError("C5 progress invocation blocks overlap or repeat")
                active_invocation = event_invocation
                invocation_order.append(event_invocation)
            elif active_invocation != event_invocation:
                raise BenchmarkError("C5 progress records are outside their exclusive invocation block")
            if phase == "invocation-terminal":
                active_invocation = None
            events_by_invocation.setdefault(event["invocation_id"], []).append(event)
    if active_invocation is not None:
        raise BenchmarkError("C5 progress journal ends inside an open invocation")
    if not invocations:
        raise BenchmarkError("C5 progress exists without any terminal invocation receipt")
    for invocation_id, receipt in invocations.items():
        events = events_by_invocation.get(invocation_id, [])
        if (not events or events[0].get("phase") != "invocation-started" or
                events[-1].get("phase") != "invocation-terminal" or
                sum(event.get("phase") == "invocation-started" for event in events) != 1 or
                sum(event.get("phase") == "invocation-terminal" for event in events) != 1):
            raise BenchmarkError(f"C5 invocation progress is missing a durable start or terminal event: {invocation_id}")
        if (events[0].get("mode") != receipt.get("mode") or
                events[0].get("selected_groups") != receipt.get("selected_groups") or
                events[0].get("target_suffix_line_count_before") != receipt.get("target_suffix_line_count_before") or
                events[0].get("target_suffix_sha256_before") != receipt.get("target_suffix_sha256_before") or
                events[-1].get("attempt_count") != len(receipt.get("attempts", []))):
            raise BenchmarkError(f"C5 invocation progress does not match its terminal receipt: {invocation_id}")
        if (events[-1].get("status") != receipt.get("status") or
                events[-1].get("target_suffix_line_count") != receipt.get("target_suffix_line_count") or
                events[-1].get("target_suffix_sha256") != receipt.get("target_suffix_sha256")):
            raise BenchmarkError(f"C5 invocation terminal progress disagrees with its receipt: {invocation_id}")
    if len(invocation_order) != len(invocations) or set(invocation_order) != set(invocations):
        raise BenchmarkError("C5 terminal invocation receipts do not match progress start order")
    return {"invocations": [invocations[item] for item in invocation_order],
            "events_by_invocation": events_by_invocation,
            "invocation_order": invocation_order}


def _verify_invocation_attempt_links(validated: dict, state: dict) -> None:
    rows = validated["ledger"].get("target_rows", [])
    by_key = {(row.get("group_id"), row.get("attempt_id")): row for row in rows}
    linked = set()
    proofs = {(item["group_id"], item["attempt_id"]): item
              for item in validated["ledger"].get("target_stage_proofs", [])}
    invocation_by_id = {item["invocation_id"]: item for item in state["invocations"]}
    previous_count = 0
    previous_hash = _sha(b"")
    for invocation_id in state.get("invocation_order", []):
        invocation = invocation_by_id[invocation_id]
        if (invocation.get("target_suffix_line_count_before") != previous_count or
                invocation.get("target_suffix_sha256_before") != previous_hash):
            raise BenchmarkError("C5 invocation blocks do not form one contiguous target-ledger history")
        mode = invocation.get("mode")
        selected = invocation.get("selected_groups")
        if mode == "one":
            if not isinstance(selected, list) or len(selected) != 1 or selected[0] not in BIFROST_GROUP_IDS:
                raise BenchmarkError("one-group invocation receipt has a malformed selected roster")
        elif mode == "serial-fail-stop":
            if selected != list(BIFROST_GROUP_IDS):
                raise BenchmarkError("serial invocation receipt does not bind the exact 20-group roster")
        else:
            raise BenchmarkError("C5 invocation receipt has an unsupported execution mode")
        attempts = invocation.get("attempts")
        if not isinstance(attempts, list):
            raise BenchmarkError("C5 invocation receipt attempts field is malformed")
        attempt_keys = []
        for attempt in attempts:
            key = (attempt.get("group_id"), attempt.get("attempt_id"))
            row = by_key.get(key)
            if row is None or key in linked:
                raise BenchmarkError("C5 invocation attempt is missing from or duplicated in the target ledger")
            if (attempt.get("status") != row.get("status") or
                    attempt.get("global_attempt_number") != row.get("global_attempt_number") or
                    attempt.get("duration_seconds") != row.get("duration_seconds") or
                    attempt.get("completed_receipt") != f"{ATTEMPTS_REL}/{row['attempt_id']}/completed.json"):
                raise BenchmarkError("C5 invocation attempt identity differs from the target ledger")
            linked.add(key)
            attempt_keys.append(key)
            proof = proofs[key]
            attempt_events = state["events_by_invocation"].get(invocation["invocation_id"], [])
            starts = [event for event in attempt_events if event.get("phase") == "attempt-started" and
                      (event.get("group_id"), event.get("attempt_id")) == key]
            terminals = [event for event in attempt_events if event.get("phase") == "attempt-terminal" and
                         (event.get("group_id"), event.get("attempt_id")) == key]
            stage = row["ledger_stage_proof"]
            if (len(starts) != 1 or len(terminals) != 1 or
                    starts[0].get("global_attempt_number") != row["global_attempt_number"] or
                    starts[0].get("ledger_pre_append_line_count") != stage["pre_append_line_count"] or
                    starts[0].get("target_suffix_line_count_before") != stage["target_suffix_line_count_before"] or
                    starts[0].get("target_suffix_sha256_before") != stage["target_suffix_sha256_before"] or
                    terminals[0].get("status") != row["status"] or
                    terminals[0].get("ledger_line_count") != stage["pre_append_line_count"] + 1 or
                    terminals[0].get("target_suffix_line_count") != proof["line_count"] or
                    terminals[0].get("target_suffix_sha256") != proof["sha256"]):
                raise BenchmarkError("C5 progress attempt stages do not reconcile with the append-only ledger")
        if attempts:
            first = by_key[(attempts[0]["group_id"], attempts[0]["attempt_id"])]["ledger_stage_proof"]
            if (first.get("target_suffix_line_count_before") != invocation.get("target_suffix_line_count_before") or
                    first.get("target_suffix_sha256_before") != invocation.get("target_suffix_sha256_before")):
                raise BenchmarkError("C5 invocation start suffix differs from its first target attempt")
            for previous, current in zip(attempts, attempts[1:]):
                previous_key = (previous["group_id"], previous["attempt_id"])
                current_key = (current["group_id"], current["attempt_id"])
                previous_proof = proofs[previous_key]
                current_stage = by_key[current_key]["ledger_stage_proof"]
                if (current_stage.get("target_suffix_line_count_before") != previous_proof["line_count"] or
                        current_stage.get("target_suffix_sha256_before") != previous_proof["sha256"]):
                    raise BenchmarkError("C5 invocation attempts do not form a contiguous target-ledger suffix")
            last = by_key[(attempts[-1]["group_id"], attempts[-1]["attempt_id"])]
            last_proof = proofs[(last["group_id"], last["attempt_id"])]
            expected_terminal_count = last_proof["line_count"]
            expected_terminal_hash = last_proof["sha256"]
        else:
            expected_terminal_count = invocation.get("target_suffix_line_count_before")
            expected_terminal_hash = invocation.get("target_suffix_sha256_before")
        if (invocation.get("target_suffix_line_count") != expected_terminal_count or
                invocation.get("target_suffix_sha256") != expected_terminal_hash):
            raise BenchmarkError("C5 invocation terminal suffix does not match its appended target attempts")
        previous_count = expected_terminal_count
        previous_hash = expected_terminal_hash
        if mode == "one" and any(key[0] != selected[0] for key in attempt_keys):
            raise BenchmarkError("one-group invocation attempts outside its selected group")
        if mode == "serial-fail-stop":
            expected_prefix = selected[:len(attempt_keys)]
            if [key[0] for key in attempt_keys] != expected_prefix:
                raise BenchmarkError("serial invocation attempts are not a prefix of the exact roster")
        events = state["events_by_invocation"].get(invocation["invocation_id"], [])
        attempt_events = [event for event in events if event.get("phase") in {"attempt-started", "attempt-terminal"}]
        event_keys = [(event.get("group_id"), event.get("attempt_id")) for event in attempt_events]
        expected_event_keys = [key for key in attempt_keys for _ in range(2)]
        expected_event_phases = [phase for _ in attempt_keys for phase in ("attempt-started", "attempt-terminal")]
        if (event_keys != expected_event_keys or
                [event.get("phase") for event in attempt_events] != expected_event_phases):
            raise BenchmarkError("C5 progress attempt events are out of invocation order")
        status = invocation.get("status")
        if status == "completed":
            if mode == "one" and (len(attempts) != 1 or attempts[0].get("status") != "completed"):
                raise BenchmarkError("completed one-group invocation lacks one completed attempt")
            if mode == "serial-fail-stop" and (len(attempts) != 20 or
                    any(item.get("status") != "completed" for item in attempts)):
                raise BenchmarkError("completed serial invocation lacks all 20 completed attempts")
        elif status == "fail-stopped":
            if not attempts or (attempts[-1].get("status") == "completed" and "error" not in invocation):
                raise BenchmarkError("fail-stop invocation does not identify a failed attempt or supervisor error")
        elif status == "preflight-failed":
            if attempts:
                raise BenchmarkError("preflight-failed invocation unexpectedly contains launched attempts")
    if linked != set(by_key):
        raise BenchmarkError("target ledger contains an attempt without a durable terminal invocation reference")


def _terminal_invocation_refs(root: Path, state: dict) -> list[dict]:
    result = []
    for receipt in state["invocations"]:
        path = _invocation_path(root, receipt["invocation_id"])
        result.append({
            "invocation_id": receipt["invocation_id"],
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha_file(path),
            "status": receipt["status"],
            "attempt_count": len(receipt.get("attempts", [])),
        })
    return sorted(result, key=lambda item: item["invocation_id"])


def _target_attempt_summary_rows(rows: Sequence[dict]) -> list[dict]:
    return [{
        "group_id": row["group_id"], "attempt_id": row["attempt_id"],
        "status": row["status"], "global_attempt_number": row["global_attempt_number"],
        "duration_seconds": row.get("duration_seconds"),
        "completed_receipt": f"{ATTEMPTS_REL}/{row['attempt_id']}/completed.json",
    } for row in rows]


def _write_series_summary(root: Path, validated: dict, completion_invocation_id: str) -> dict:
    rows = validated["ledger"].get("target_rows", [])
    completed = {row["group_id"] for row in rows if row.get("status") == "completed"}
    if completed != set(BIFROST_GROUP_IDS):
        raise BenchmarkError("cannot write C5 terminal summary before all 20 groups have completed")
    if len([row for row in rows if row.get("status") == "completed"]) != len(BIFROST_GROUP_IDS):
        raise BenchmarkError("C5 terminal summary requires one completed target attempt per group")
    state = _verify_invocation_history(root, validated)
    _verify_invocation_attempt_links(validated, state)
    terminal = {item["invocation_id"]: item for item in state["invocations"]}
    if completion_invocation_id not in terminal or terminal[completion_invocation_id].get("status") != "completed":
        raise BenchmarkError("C5 terminal summary completion invocation is not durably completed")
    summary = {
        "schema": SERIES_SUMMARY_SCHEMA,
        "target_id": TARGET_ID, "contract_path": CONTRACT_REL,
        "contract_sha256": validated["contract_sha256"],
        "source_commit": validated["source_commit"], "plan_commit": validated["plan_commit"],
        "status": "completed", "completed_group_count": len(BIFROST_GROUP_IDS),
        "completed_groups": list(BIFROST_GROUP_IDS),
        "completion_invocation_id": completion_invocation_id,
        "target_attempts": _target_attempt_summary_rows(rows),
        "target_suffix_line_count": validated["ledger"].get("target_line_count", 0),
        "target_suffix_sha256": validated["ledger"].get("target_suffix_sha256"),
        "terminal_invocations": _terminal_invocation_refs(root, state),
        "ended_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    summary_path = root / SUMMARY_REL
    if summary_path.exists() or summary_path.is_symlink():
        raise BenchmarkError("C5 series summary already exists; refusing to replace terminal evidence")
    _atomic_write(summary_path, _pretty_json(summary), exclusive=True)
    return summary


def _verify_series_summary(root: Path, validated: dict, state: dict) -> dict | None:
    path = root / SUMMARY_REL
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise BenchmarkError("C5 terminal series summary path is unsafe")
    summary, _ = _read_json(path, "C5 terminal series summary")
    rows = validated["ledger"].get("target_rows", [])
    completed = {row["group_id"] for row in rows if row.get("status") == "completed"}
    if completed != set(BIFROST_GROUP_IDS) or len([row for row in rows if row.get("status") == "completed"]) != 20:
        raise BenchmarkError("C5 terminal summary exists without exactly 20 completed target groups")
    terminal_refs = _terminal_invocation_refs(root, state)
    invocation_ids = {item["invocation_id"] for item in terminal_refs}
    completion_id = summary.get("completion_invocation_id")
    completion = next((item for item in state["invocations"] if item.get("invocation_id") == completion_id), None)
    expected = {
        "schema": SERIES_SUMMARY_SCHEMA,
        "target_id": TARGET_ID, "contract_path": CONTRACT_REL,
        "contract_sha256": validated["contract_sha256"],
        "source_commit": validated["source_commit"], "plan_commit": validated["plan_commit"],
        "status": "completed", "completed_group_count": len(BIFROST_GROUP_IDS),
        "completed_groups": list(BIFROST_GROUP_IDS),
        "completion_invocation_id": completion_id,
        "target_attempts": _target_attempt_summary_rows(rows),
        "target_suffix_line_count": validated["ledger"].get("target_line_count", 0),
        "target_suffix_sha256": validated["ledger"].get("target_suffix_sha256"),
        "terminal_invocations": terminal_refs,
    }
    if (set(summary) != set(expected) | {"ended_at_utc"} or
            any(summary.get(key) != value for key, value in expected.items()) or
            completion_id not in invocation_ids or completion is None or completion.get("status") != "completed"):
        raise BenchmarkError("C5 terminal summary does not reconcile with contract, ledger, and invocations")
    try:
        ended = dt.datetime.fromisoformat(str(summary["ended_at_utc"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise BenchmarkError("C5 terminal summary has an invalid completion timestamp") from exc
    if ended.tzinfo is None:
        raise BenchmarkError("C5 terminal summary completion timestamp lacks a timezone")
    return {"path": SUMMARY_REL, "sha256": _sha_file(path), "completion_invocation_id": completion_id}


def _execute(root: Path, contract_path: str | Path, mode: str, group_id: str | None) -> dict:
    if mode not in {"one", "serial-fail-stop"}:
        raise BenchmarkError("execution mode must be one or serial-fail-stop")
    if mode == "one" and group_id not in BIFROST_GROUP_IDS:
        raise BenchmarkError("mode one requires exactly one group from the fixed Bifrost roster")
    if mode == "serial-fail-stop" and group_id is not None:
        raise BenchmarkError("serial-fail-stop runs the exact fixed 20-group roster and takes no --group")
    # Load the pinned helper once to acquire its shared analyzer lock, then do
    # all validation and process creation under that same cross-run lock.
    initial_core, _ = _load_core(root)
    with initial_core._exclusive_lock():
        validated = _validate_contract(root, contract_path, require_approval=True, require_committed=True)
        core, core_sha = _load_core(root, validated["contract"]["source_snapshot"]["core_helpers"][0]["sha256"])
        if core_sha != validated["contract"]["source_snapshot"]["core_helpers"][0]["sha256"]:
            raise BenchmarkError("pinned executor helper hash changed")
        rows = _validate_existing_target_attempts(validated)
        if mode == "serial-fail-stop" and rows:
            raise BenchmarkError(
                f"serial-fail-stop requires a fresh {SERIES_LABEL} target with no prior C5 attempt"
            )
        if any(item.get("status") not in {"completed", "failed", "timed-out", "capacity-lost", "recorder-error"}
               for item in validated["history"].get("target_records", [])):
            raise BenchmarkError("C5 has an unknown or non-terminal started namespace")
        if (root / SUMMARY_REL).exists() or (root / SUMMARY_REL).is_symlink():
            raise BenchmarkError("C5 series summary already exists; the target is terminal")
        if rows:
            for prior_row in rows:
                _verify_attempt_outputs(root, validated, prior_row)
            state = _verify_invocation_history(root, validated)
            _verify_invocation_attempt_links(validated, state)
        else:
            for relative in (PROGRESS_REL, INVOCATIONS_REL):
                existing = root / relative
                if existing.exists() or existing.is_symlink():
                    raise BenchmarkError(f"C5 target has output state without ledgered attempts: {relative}")
        if mode == "one":
            _group_attempt_state(validated, group_id)
            selected = [group_id]
        else:
            selected = list(BIFROST_GROUP_IDS)
        consumed_analyzer = 0.0
        for row in rows:
            duration = row.get("duration_seconds")
            if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0:
                raise BenchmarkError("prior C5 analyzer duration is unknown; no retry or continuation is allowed")
            consumed_analyzer += duration
        origin_count = validated["contract"]["attempt_history"]["global_prior_consumed_attempt_count"]
        next_global = origin_count + len(rows) + 1
        invocation_id = f"{SERIES_LABEL}-{mode}-{time.time_ns()}-{os.getpid()}"
        invocation_path = _invocation_path(root, invocation_id)
        if invocation_path.exists() or invocation_path.is_symlink():
            raise BenchmarkError("invocation receipt path already exists")
        _check_resources = getattr(core, "_check_resources")
        _check_resources(root, 127 * 1024**3)
        invocation = {
            "schema": INVOCATION_SCHEMA,
            "target_id": TARGET_ID, "invocation_id": invocation_id, "mode": mode,
            "status": "running", "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_commit": validated["source_commit"], "plan_commit": validated["plan_commit"],
            "contract_path": CONTRACT_REL, "contract_sha256": validated["contract_sha256"],
            "selected_groups": selected, "attempts": [],
            "target_suffix_line_count_before": validated["ledger"].get("target_line_count", 0),
            "target_suffix_sha256_before": validated["ledger"].get("target_suffix_sha256", _sha(b"")),
            "historical_attempt_count": origin_count,
            "historical_analyzer_seconds_separate": sum(
                float(row.get("duration_seconds", 0) or 0)
                for row in validated["history"]["ledger"]["historical_records"].values()
            ),
            "prior_c5_analyzer_seconds": consumed_analyzer,
            "target_deadline_budget_seconds": TARGET_WALL_BUDGET_SECONDS,
            "source_and_recording_overhead_excluded_from_analyzer_time": True,
            "original_global_wall_origin_utc": ORIGINAL_WALL_ORIGIN_UTC,
            "human_authority_expires": None,
            "automatic_retry": False,
        }
        _write_terminal(invocation_path, invocation)
        _durable_append(root / PROGRESS_REL, {
            "schema": PROGRESS_SCHEMA,
            "at_utc": invocation["started_at_utc"], "target_id": TARGET_ID,
            "contract_sha256": validated["contract_sha256"],
            "invocation_id": invocation_id, "phase": "invocation-started", "mode": mode,
            "selected_groups": selected,
            "target_suffix_line_count_before": invocation["target_suffix_line_count_before"],
            "target_suffix_sha256_before": invocation["target_suffix_sha256_before"],
        })
        terminal_status = "completed"
        try:
            for offset, selected_group in enumerate(selected):
                group_projection = next(item for item in validated["contract"]["groups"]
                                        if item["id"] == selected_group)
                deadline = group_projection["base_group"]["deadline_seconds"]
                if consumed_analyzer + deadline > TARGET_WALL_BUDGET_SECONDS:
                    raise BenchmarkError("inherited analyzer deadlines would exceed the fixed 13,592-second target budget")
                result = _one_group(
                    validated, selected_group, global_attempt_number=next_global,
                    remaining_group_count=len(selected) - offset, invocation_id=invocation_id,
                )
                invocation["attempts"].append({
                    "group_id": selected_group, "attempt_id": result["attempt_id"],
                    "global_attempt_number": next_global, "status": result["status"],
                    "duration_seconds": result.get("duration_seconds"),
                    "completed_receipt": f"{ATTEMPTS_REL}/{result['attempt_id']}/completed.json",
                })
                if isinstance(result.get("duration_seconds"), (int, float)):
                    consumed_analyzer += result["duration_seconds"]
                next_global += 1
                if result["status"] != "completed":
                    terminal_status = "fail-stopped"
                    break
        except BaseException as exc:
            terminal_status = "preflight-failed" if not invocation["attempts"] else "fail-stopped"
            invocation["error"] = f"{type(exc).__name__}: {exc}"
        invocation["status"] = terminal_status
        invocation["ended_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        invocation["analyzer_seconds_after"] = consumed_analyzer
        invocation["target_suffix_line_count"] = validated["ledger"].get("target_line_count", 0)
        invocation["target_suffix_sha256"] = validated["ledger"].get("target_suffix_sha256")
        _write_terminal(invocation_path, invocation)
        _durable_append(root / PROGRESS_REL, {
            "schema": PROGRESS_SCHEMA,
            "at_utc": invocation["ended_at_utc"], "target_id": TARGET_ID,
            "contract_sha256": validated["contract_sha256"],
            "invocation_id": invocation_id, "phase": "invocation-terminal",
            "status": terminal_status, "attempt_count": len(invocation["attempts"]),
            "target_suffix_line_count": invocation["target_suffix_line_count"],
            "target_suffix_sha256": invocation["target_suffix_sha256"],
        })
        summary = None
        if terminal_status == "completed":
            completed_groups = {item["group_id"] for item in validated["ledger"]["target_rows"]
                                if item.get("status") == "completed"}
            if completed_groups == set(BIFROST_GROUP_IDS):
                summary = _write_series_summary(root, validated, invocation_id)
        if terminal_status != "completed":
            return {"mode": mode, "status": terminal_status, "invocation_receipt": str(invocation_path),
                    "attempts": invocation["attempts"], "error": invocation.get("error")}
        return {"mode": mode, "status": "completed", "invocation_receipt": str(invocation_path),
                "attempts": invocation["attempts"], "target_suffix_sha256": invocation["target_suffix_sha256"],
                "series_summary": str(root / SUMMARY_REL) if summary is not None else None}


def _verify_attempt_outputs(root: Path, validated: dict, row: dict) -> None:
    attempt_id = row["attempt_id"]
    group_id = row["group_id"]
    attempt_number, embedded_series = _attempt_number(group_id, attempt_id)
    expected_execution_root = (root / EXECUTION_GROUPS_REL / SERIES_LABEL / group_id /
                               f"attempt-{attempt_number:02d}").resolve(strict=False)
    expected_cache_root = (root / CACHE_REL / SERIES_LABEL / group_id /
                           f"attempt-{attempt_number:02d}").resolve(strict=False)
    if (embedded_series != SERIES or Path(row.get("execution_root", "")).resolve(strict=False) != expected_execution_root or
            Path(row.get("cache_root", "")).resolve(strict=False) != expected_cache_root):
        raise BenchmarkError(f"C5 row execution/cache roots do not match its exact group attempt namespace: {attempt_id}")
    group_projection = next(item for item in validated["contract"]["groups"] if item["id"] == group_id)
    expected_env = _runtime_environment(group_projection["base_group"], expected_execution_root, expected_cache_root)
    if (row.get("argv") != group_projection["runtime_argv"] or row.get("environment") != expected_env or
            row.get("output_roots") != group_projection["base_group"]["output_roots"] or
            row.get("case_ids") != group_projection["base_group"]["case_ids"] or
            row.get("tool_binding") != validated["bifrost"] or
            row.get("qualification") != validated["qualification"]):
        raise BenchmarkError(f"C5 attempt runtime inputs differ from the fixed group projection: {attempt_id}")
    attempt_dir = root / ATTEMPTS_REL / attempt_id
    if attempt_dir.is_symlink() or not attempt_dir.is_dir():
        raise BenchmarkError(f"C5 attempt evidence directory is missing or unsafe: {attempt_dir}")
    for receipt_name in ("started.json", "completed.json"):
        receipt, _ = _read_json(attempt_dir / receipt_name, f"C5 {receipt_name} receipt")
        if (receipt.get("attempt_id") != attempt_id or receipt.get("group_id") != row["group_id"] or
                receipt.get("contract_sha256") != validated["contract_sha256"] or
                receipt.get("source_commit") != validated["source_commit"] or
                receipt.get("plan_commit") != validated["plan_commit"] or
                receipt.get("execution_root") != str(expected_execution_root) or
                receipt.get("cache_root") != str(expected_cache_root)):
            raise BenchmarkError(f"C5 {receipt_name} receipt identity differs: {attempt_id}")
        if receipt_name == "started.json" and receipt.get("status") != "started":
            raise BenchmarkError(f"C5 started receipt has a terminal status: {attempt_id}")
        if receipt_name == "started.json":
            immutable_fields = (
                "execution_series", "global_attempt_number", "runner_source_sha256", "core_runner_sha256",
                "fixture_revision", "population", "tool", "tool_binding", "qualification", "source_inputs",
                "argv", "environment", "output_roots", "case_ids", "deadline_seconds", "target_provenance",
                "source_capacity_admission",
            )
            if any(receipt.get(field) != row.get(field) for field in immutable_fields):
                raise BenchmarkError(f"C5 started receipt runtime binding differs from its terminal row: {attempt_id}")
        if receipt_name == "completed.json" and receipt != row:
            raise BenchmarkError(f"C5 terminal receipt does not exactly match its ledger row: {attempt_id}")
    for stream_name in ("stdout", "stderr"):
        reference = row.get(stream_name)
        if not isinstance(reference, dict):
            raise BenchmarkError(f"C5 ledger row lacks {stream_name} capture identity: {attempt_id}")
        stream = attempt_dir / f"{stream_name}.txt"
        if stream.is_symlink() or not stream.is_file() or stream.stat().st_size != reference.get("bytes") or _sha_file(stream) != reference.get("sha256"):
            raise BenchmarkError(f"C5 {stream_name} capture changed: {attempt_id}")
    if _strict_guard_module is None:
        core, _ = _load_core(root, validated["contract"]["source_snapshot"]["core_helpers"][0]["sha256"])
        _disk_guard(root, core)
    _verify_source_capacity_admission(root, validated, row)
    _check_scala_staging(row, expected_execution_root, validated, require_postcheck=True)
    group_projection = next(item for item in validated["contract"]["groups"] if item["id"] == row["group_id"])
    execution_root = Path(row.get("execution_root", ""))
    _safe_execution_root(root, str(execution_root))
    capture_rows = row.get("captured_files")
    if not isinstance(capture_rows, list):
        raise BenchmarkError(f"C5 captured file inventory is malformed: {attempt_id}")
    capture_by_relative = {}
    for capture in capture_rows:
        if not isinstance(capture, dict):
            raise BenchmarkError(f"C5 captured file entry is malformed: {attempt_id}")
        relative = capture.get("execution_relative")
        if not isinstance(relative, str):
            raise BenchmarkError(f"C5 capture lacks an execution-relative identity: {attempt_id}")
        safe = _repo_relative(root, relative, "captured execution-relative path")
        declared_output = any(PurePosixPath(relative).is_relative_to(PurePosixPath(value))
                             for value in group_projection["base_group"]["output_roots"])
        if not declared_output:
            raise BenchmarkError(f"C5 capture lies outside the group's declared raw output roots: {relative}")
        captured = Path(capture.get("capture_path", ""))
        expected_capture = attempt_dir / "capture" / Path(*PurePosixPath(relative).parts)
        if captured.resolve(strict=False) != expected_capture.resolve(strict=False):
            raise BenchmarkError(f"C5 capture path escapes its attempt: {relative}")
        if (captured.is_symlink() or not captured.is_file() or captured.stat().st_size != capture.get("bytes") or
                _sha_file(captured) != capture.get("sha256")):
            raise BenchmarkError(f"C5 raw capture changed: {relative}")
        execution_file = execution_root / Path(*PurePosixPath(relative).parts)
        try:
            execution_file.resolve(strict=True).relative_to(execution_root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise BenchmarkError(f"C5 execution output escapes its snapshot or is missing: {relative}") from exc
        if (execution_file.is_symlink() or not execution_file.is_file() or
                execution_file.stat().st_size != capture.get("bytes") or
                _sha_file(execution_file) != capture.get("sha256")):
            raise BenchmarkError(f"C5 execution output changed after retention capture: {relative}")
        capture_by_relative[relative] = capture
    reports = row.get("reports")
    if row.get("status") == "completed":
        expected_reports = group_projection["runtime_reports"]
        if not isinstance(reports, list) or len(reports) != len(expected_reports):
            raise BenchmarkError(f"completed C5 attempt has an incomplete report roster: {attempt_id}")
        core, _ = _load_core(root, validated["contract"]["source_snapshot"]["core_helpers"][0]["sha256"])
        for entry, spec in zip(reports, expected_reports):
            if not isinstance(entry, dict) or entry.get("case_ids") != spec.get("case_ids") or entry.get("tool_version") != BIFROST_REPORT_VERSION:
                raise BenchmarkError(f"C5 report binding differs from target report projection: {attempt_id}")
            staged = _repo_relative(root, entry.get("staged_path"), "staged report path")
            original = _repo_relative(root, entry.get("original_path"), "original report path")
            expected_staged = (PurePosixPath(NORMAL_ATTEMPTS_REL) / attempt_id /
                               PurePosixPath(spec["path"]).relative_to(PurePosixPath("reports/releases/v0.9.2/normal")))
            expected_original = (PurePosixPath(ATTEMPTS_REL) / attempt_id / "original" / PurePosixPath(spec["path"]))
            if staged != expected_staged or original != expected_original:
                raise BenchmarkError(f"C5 report staging path differs from the fixed attempt namespace: {attempt_id}")
            staged_path = root.joinpath(*staged.parts)
            original_path = root.joinpath(*original.parts)
            for file_path, expected_digest in ((staged_path, entry.get("staged_sha256")),
                                               (original_path, entry.get("original_sha256"))):
                if file_path.is_symlink() or not file_path.is_file() or _sha_file(file_path) != expected_digest:
                    raise BenchmarkError(f"C5 staged/original report changed: {file_path}")
            core._report_identity(spec, original_path.read_bytes(), FIXTURE_REVISION)
            core._report_identity(spec, staged_path.read_bytes(), FIXTURE_REVISION)
            for mapping in entry.get("raw_output_mappings", []):
                relative = mapping.get("execution_relative")
                captured = capture_by_relative.get(relative)
                expected_capture_path = (PurePosixPath(ATTEMPTS_REL) / attempt_id / "capture" / PurePosixPath(relative)) if isinstance(relative, str) else None
                if (captured is None or mapping.get("sha256") != captured.get("sha256") or
                        mapping.get("captured_path") != (expected_capture_path.as_posix() if expected_capture_path else None)):
                    raise BenchmarkError(f"C5 report raw output does not map to retained capture: {attempt_id}")
    elif reports not in ([], None):
        raise BenchmarkError(f"non-completed C5 attempt must not expose a completed report set: {attempt_id}")


def reconcile_outputs(root: Path, contract_path: str | Path) -> dict:
    """Read-only C5 reconciliation interface for independent checker clients."""
    core, _ = _load_core(root)
    with core._exclusive_lock():
        return _reconcile_outputs_locked(root, contract_path)


def _reconcile_outputs_locked(root: Path, contract_path: str | Path) -> dict:
    validated = _validate_contract(root, contract_path, require_approval=True, require_committed=True,
                                   check_current_source=False)
    rows = _validate_existing_target_attempts(validated)
    completed_by_group = {}
    attempt_ids = set()
    for row in rows:
        attempt_id = row["attempt_id"]
        if attempt_id in attempt_ids:
            raise BenchmarkError("C5 target ledger repeats an attempt ID")
        attempt_ids.add(attempt_id)
        _verify_attempt_outputs(root, validated, row)
        if row.get("status") == "completed":
            completed_by_group.setdefault(row["group_id"], []).append(row)
    if any(len(items) > 1 for items in completed_by_group.values()):
        raise BenchmarkError("C5 group has multiple completed target attempts")
    completed_groups = [group_id for group_id in BIFROST_GROUP_IDS if group_id in completed_by_group]
    missing_groups = [group_id for group_id in BIFROST_GROUP_IDS if group_id not in completed_by_group]
    invocation_state = _verify_invocation_history(root, validated)
    _verify_invocation_attempt_links(validated, invocation_state)
    summary = _verify_series_summary(root, validated, invocation_state)
    all_rows_completed = len(completed_groups) == len(BIFROST_GROUP_IDS)
    series_completed = all_rows_completed and summary is not None
    invocations = _terminal_invocation_refs(root, invocation_state)
    return {
        "schema": RECONCILIATION_SCHEMA,
        "status": "completed" if series_completed else "incomplete",
        "output_rows_complete": all_rows_completed,
        "series_summary": summary,
        "completion_state": ("series-summary-verified" if series_completed else
                             "series-summary-missing" if all_rows_completed else "groups-incomplete"),
        "target_id": TARGET_ID, "contract_path": CONTRACT_REL,
        "contract_sha256": validated["contract_sha256"],
        "source_commit": validated["source_commit"], "plan_commit": validated["plan_commit"],
        "parent_population": validated["contract"]["parent_population"]["full_counts"],
        "target_group_count": len(BIFROST_GROUP_IDS), "completed_group_count": len(completed_groups),
        "completed_groups": completed_groups, "missing_groups": missing_groups,
        "attempt_count": len(rows), "target_attempts": [
            {"group_id": row["group_id"], "attempt_id": row["attempt_id"],
             "status": row["status"], "global_attempt_number": row["global_attempt_number"],
             "duration_seconds": row.get("duration_seconds"),
             "completed_receipt": f"{ATTEMPTS_REL}/{row['attempt_id']}/completed.json"}
            for row in rows
        ],
        "ledger": {
            "path": LEDGER_REL, "line_count": validated["ledger"]["line_count"],
            "bytes": validated["ledger"]["bytes"], "sha256": validated["ledger"]["sha256"],
            f"preserved_{LEDGER_PREFIX_LINES}_row_prefix_sha256": LEDGER_PREFIX_SHA256,
            "target_suffix_line_count": validated["ledger"]["target_line_count"],
            "target_suffix_sha256": validated["ledger"]["target_suffix_sha256"],
        },
        "terminal_invocations": invocations,
        "qualification": validated["qualification"],
        "full_policy_qualification": False,
        "automatic_retry": False,
        "original_global_wall_origin_utc": ORIGINAL_WALL_ORIGIN_UTC,
        "historical_and_new_analyzer_consumption_separate": True,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=TARGET_HELP_DESCRIPTION)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="write a source-bound unapproved C5 manifest")
    prepare_parser.add_argument("--source-commit", required=True)
    prepare_parser.add_argument("--runner", required=True)
    prepare_parser.add_argument("--qualification", default=QUALIFICATION_DEFAULT)
    prepare_parser.add_argument("--bifrost-receipt", default=BIFROST_RECEIPT_DEFAULT)
    prepare_parser.add_argument("--scala-receipt", default=SCALA_RECEIPT_DEFAULT)
    prepare_parser.add_argument("--native-evidence", action="append", default=[])
    execute_parser = subparsers.add_parser("execute", help="run one group or the fixed fail-stop 20-group roster")
    execute_parser.add_argument("--contract", default=CONTRACT_REL)
    execute_parser.add_argument("--mode", required=True, choices=("one", "serial-fail-stop"))
    execute_parser.add_argument("--group")
    verify_parser = subparsers.add_parser("verify", help="read-only reconciliation of C5 outputs and receipts")
    verify_parser.add_argument("--contract", default=CONTRACT_REL)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    git_root = Path(_git(root, "rev-parse", "--show-toplevel").strip()).resolve()
    if git_root != root.resolve():
        raise BenchmarkError("C5 runner must execute from its owning dataflowbench worktree")
    if args.command == "prepare":
        result = _prepare(root, args)
    elif args.command == "execute":
        result = _execute(root, args.contract, args.mode, args.group)
    else:
        result = reconcile_outputs(root, args.contract)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("status") in (None, "completed", "incomplete") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (BenchmarkError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"C5 Bifrost {BIFROST_VERSION} target refused: {exc}")
