#!/usr/bin/env python3
"""Fail-closed controller for the prospective, qualified v0.9.2 timing run.

This is additive to v092_timing_campaign.py.  It creates a new plan from
reviewed runtime bindings, requires a fresh quiet window before every command,
and records candidate evidence without upgrading release qualification.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
FROZEN_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
SOURCE_GROUPS = 84
FAMILIES = ("bifrost", "codeql", "flowdroid", "infer", "joern", "opentaint", "pysa", "semgrep")
SWIFT_WRAPPERS = {
    "codeql-swift-common108": "scripts/run-swift-common-v092.py",
    "joern-swift-common108": "scripts/run-joern-common-v092.py",
}
FAMILY_TOOL_FLAGS = {
    "bifrost": "--bifrost", "codeql": "--codeql", "flowdroid": "--flowdroid-jar",
    "infer": "--infer", "joern": "--joern", "opentaint": "--analyzer-jar",
    "pysa": "--pyre", "semgrep": "--semgrep",
}
HELPERS = (
    "scripts/execute-release-v092.py",
    "scripts/swift_v2_scored_process.py",
    "scripts/v092_disk_guard.py",
    "scripts/v092_timing_campaign.py",
    "scripts/v092_timing_host.py",
    "scripts/v092_timing_qualified_campaign.py",
)
CONTINUATION_HELPER = "scripts/v092_timing_checkpoint.py"
SEGMENT_CHECKPOINT_HELPER = "scripts/v092_timing_segment_checkpoint.py"
SEMANTIC_CONTINUATION_MODE = "semantic-quarantine/v1"
SEMANTIC_MISMATCH_POLICY = {
    "outcome_only": "quarantine-and-continue",
    "identity_or_membership": "fail-stop",
    "command_timeout_resource_or_provenance": "fail-stop",
    "retry": False,
}
# The retained source plan predates two already-committed fixes in the legacy
# timing helper. Bind both versions explicitly; no other helper transition is
# accepted. The active plan always records the helper bytes it will execute.
SOURCE_HELPER_TRANSITIONS = {
    "scripts/v092_timing_campaign.py": {
        "source_sha256": "4c857afdcd279b115b90bf252d92cae9a8c954bfdee9b209208c7b7941506fdf",
        "active_sha256": "dbc2b78f069b87e3b6e1707a32c3f5c1490ab0bb3debb2881b24e86f0bdb471f",
        "reason": "post-run CPU contention continuation and A24 overhead pairing fixes committed after source plan",
    },
}
CAMPAIGN_ID_PATTERN = re.compile(r"(?P<date>\d{8})-(?P<sequence>\d{2})\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
GIB = 1024**3
DEFAULT_MAX_CAMPAIGN_WALL_SECONDS = 48 * 60 * 60
PYSA_TMP_ROOT = Path("/private/tmp")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


legacy = _load_module("qualified_timing_legacy", ROOT / "scripts/v092_timing_campaign.py")


class CampaignWindowEnded(RuntimeError):
    """The bounded campaign wall window elapsed before the next dispatch."""


class FrozenComparisonError(RuntimeError):
    """A measured report did not preserve the frozen semantic identity."""

    def __init__(self, message: str, receipt: dict):
        super().__init__(message)
        self.receipt = receipt


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path(root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def _json_copy(value):
    return json.loads(json.dumps(value))


def _validate_sha(value, description: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise RuntimeError(f"{description} must be a lowercase SHA-256")
    return value


def _campaign_id(value: object) -> str:
    if not isinstance(value, str):
        raise RuntimeError("campaign_id must use YYYYMMDD-NN format")
    match = CAMPAIGN_ID_PATTERN.fullmatch(value)
    if match is None or match.group("sequence") == "00":
        raise RuntimeError("campaign_id must use YYYYMMDD-NN format with sequence 01..99")
    try:
        dt.datetime.strptime(match.group("date"), "%Y%m%d")
    except ValueError as exc:
        raise RuntimeError("campaign_id must contain a valid calendar date") from exc
    return value


def _utc(value: object, description: str) -> dt.datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"{description} must be an RFC 3339 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"{description} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{description} must include a UTC offset")
    return parsed.astimezone(dt.timezone.utc)


def _source_reference(bindings: dict) -> dict:
    canonical = bindings.get("source_plan")
    split_path = bindings.get("source_plan_path")
    split_sha = bindings.get("source_plan_sha256")
    if isinstance(canonical, dict):
        result = {"path": canonical.get("path"), "sha256": canonical.get("sha256")}
        if split_path is not None and split_path != result["path"]:
            raise RuntimeError("conflicting source_plan path bindings")
        if split_sha is not None and split_sha != result["sha256"]:
            raise RuntimeError("conflicting source_plan digest bindings")
    elif isinstance(canonical, str):
        if not isinstance(split_sha, str) or (split_path is not None and split_path != canonical):
            raise RuntimeError("split source_plan fields are ambiguous or incomplete")
        result = {"path": canonical, "sha256": split_sha}
    elif canonical is None and isinstance(split_path, str) and isinstance(split_sha, str):
        result = {"path": split_path, "sha256": split_sha}
    else:
        raise RuntimeError("bindings must include source_plan {path, sha256}")
    if not isinstance(result["path"], str) or Path(result["path"]).is_absolute():
        raise RuntimeError("source_plan.path must be repository-relative")
    if PurePosixPath(result["path"]).is_absolute() or ".." in PurePosixPath(result["path"]).parts:
        raise RuntimeError("source_plan.path must remain inside the repository")
    _validate_sha(result["sha256"], "source_plan.sha256")
    return result


def _rebindings(bindings: dict) -> dict[str, str]:
    raw = bindings.get("path_rebindings", {})
    if not isinstance(raw, dict):
        raise RuntimeError("path_rebindings must be an object")
    result = {}
    for old, new in raw.items():
        if (not isinstance(old, str) or not isinstance(new, str)
                or not Path(old).is_absolute() or not Path(new).is_absolute()):
            raise RuntimeError("path_rebindings keys and values must be absolute paths")
        if old == new:
            raise RuntimeError("path_rebindings must change a path")
        result[old.rstrip("/")] = new.rstrip("/")
    if len(result) != len(raw):
        raise RuntimeError("path_rebindings contain duplicate normalized prefixes")
    return result


def _rewrite_value(value, mappings: dict[str, str]):
    if isinstance(value, str):
        for old in sorted(mappings, key=len, reverse=True):
            if value == old or value.startswith(old + "/"):
                return mappings[old] + value[len(old):]
        return value
    if isinstance(value, list):
        return [_rewrite_value(item, mappings) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_value(item, mappings) for key, item in value.items()}
    return value


def _environment_with_reviewed_overrides(environment, overrides, mappings, group_id: str) -> dict:
    if not isinstance(environment, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in environment.items()):
        raise RuntimeError(f"group environment must contain string keys and values: {group_id}")
    if not isinstance(overrides, dict):
        raise RuntimeError(f"group override environment must be an object: {group_id}")
    allowed = {"JAVA_HOME", "PATH", "CC", "CXX", "SDKROOT", "GOTOOLCHAIN",
               "RUSTUP_TOOLCHAIN", "CARGO_NET_OFFLINE"}
    if set(overrides) - allowed:
        raise RuntimeError(f"group override changes protected environment settings: {group_id}")
    result = _rewrite_value(environment, mappings)
    if "PATH" in environment:
        # Each PATH entry is a separate path. Rewriting only the start of the
        # colon-separated string leaves later JDK/venv entries at old roots.
        result["PATH"] = os.pathsep.join(
            _rewrite_value(entry, mappings) for entry in environment["PATH"].split(os.pathsep))
    for key, value in overrides.items():
        if not isinstance(value, str):
            raise RuntimeError(f"environment override values must be strings: {group_id}/{key}")
        if key == "PATH":
            base = result.get("PATH", "").split(os.pathsep)
            supplied = value.split(os.pathsep)
            if any(not Path(entry).is_absolute() for entry in supplied):
                raise RuntimeError(f"PATH entries must be absolute: {group_id}")
            prefix = supplied[:-len(base)] if len(supplied) >= len(base) else []
            if supplied[len(prefix):] != base:
                raise RuntimeError(f"PATH must retain the rebound original entries: {group_id}")
            for entry in prefix:
                compiler_bin = {str(Path(overrides[name]).parent)
                                for name in ("CC", "CXX") if name in overrides}
                rust_bin = (overrides.get("RUSTUP_TOOLCHAIN") == "1.97.1"
                            and Path(entry).name == "bin"
                            and Path(entry).parent.name == "1.97.1-aarch64-apple-darwin")
                if entry not in compiler_bin and not rust_bin:
                    raise RuntimeError(f"PATH adds an unregistered compiler directory: {group_id}")
            result[key] = value
        elif key == "JAVA_HOME":
            if result.get(key) != value:
                raise RuntimeError(f"{key} override must equal its explicit path-rebound value: {group_id}")
        elif key in {"CC", "CXX", "SDKROOT"}:
            if not Path(value).is_absolute():
                raise RuntimeError(f"{key} override must be an absolute path: {group_id}")
            result[key] = value
        else:
            expected = {"GOTOOLCHAIN": "local", "RUSTUP_TOOLCHAIN": "1.97.1",
                        "CARGO_NET_OFFLINE": "true"}[key]
            if value != expected:
                raise RuntimeError(f"{key} override differs from its preregistered value: {group_id}")
            result[key] = value
    return result


def _normalize_source_group(source: dict, frozen: dict, overrides: dict,
                            mappings: dict[str, str], tools: dict) -> dict:
    group = _json_copy(source)
    group_id = group.get("id")
    if group_id in SWIFT_WRAPPERS:
        # The timing-only predecessor replaced argv[0] for every command.
        # Restore the exact original Python entry point from execution-v4.
        group["argv"] = _json_copy(frozen["argv"])
    group["kind"] = "cold"
    group.pop("blocker", None)
    group.pop("runtime_ids", None)
    group["status"] = "blocked"
    override = overrides
    allowed = {"argv", "environment", "status", "blocker", "runtime_ids", "setup_files"}
    unknown = set(override) - allowed
    if unknown:
        raise RuntimeError(f"unsupported group override fields for {group_id}: {sorted(unknown)}")
    canonical_argv = _json_copy(group["argv"])
    if "argv" in override and _rewrite_value(override["argv"], mappings) != _rewrite_value(canonical_argv, mappings):
        raise RuntimeError(f"cold group argv override changes frozen command semantics: {group_id}")
    environment_override = override.get("environment", {})
    canonical_environment = _environment_with_reviewed_overrides(
        group.get("environment", {}), environment_override, mappings, group_id)
    status = override.get("status", "blocked")
    if status not in {"ready", "blocked"}:
        raise RuntimeError(f"group status override must be ready or blocked: {group_id}")
    group["status"] = status
    if "runtime_ids" in override:
        group["runtime_ids"] = _json_copy(override["runtime_ids"])
    if "setup_files" in override:
        group["setup_files"] = _json_copy(override["setup_files"])
    else:
        group["setup_files"] = []
    if status == "blocked":
        blocker = override.get("blocker") or source.get("blocker")
        if not isinstance(blocker, str) or not blocker.strip():
            blocker = "No reviewed runtime and readiness override was supplied for this prospective campaign."
        group["blocker"] = blocker
    else:
        group.pop("blocker", None)
    group["argv"] = canonical_argv
    group = _rewrite_value(group, mappings)
    group["environment"] = canonical_environment
    if not isinstance(group.get("argv"), list) or not group["argv"] or not all(
            isinstance(item, str) and item for item in group["argv"]):
        raise RuntimeError(f"group argv must contain nonempty strings: {group_id}")
    if type(group.get("deadline_seconds")) not in (int, float) or not math.isfinite(group["deadline_seconds"]):
        raise RuntimeError(f"group deadline must be finite: {group_id}")
    if group["deadline_seconds"] <= 0:
        raise RuntimeError(f"group deadline must be positive: {group_id}")
    if group.get("family") not in FAMILIES:
        raise RuntimeError(f"unknown analyzer family in group {group_id}")
    if status == "ready":
        runtime_ids = group.get("runtime_ids")
        if not isinstance(runtime_ids, list) or not runtime_ids or not all(
                isinstance(item, str) and item for item in runtime_ids):
            raise RuntimeError(f"ready group must explicitly bind runtime_ids: {group_id}")
        if len(runtime_ids) != len(set(runtime_ids)):
            raise RuntimeError(f"ready group has duplicate runtime_ids: {group_id}")
        if group["family"] not in tools:
            raise RuntimeError(f"ready group has no family tool binding: {group_id}")
        if group_id in SWIFT_WRAPPERS:
            wrapper = SWIFT_WRAPPERS[group_id]
            expected_prefix = _rewrite_value(frozen["argv"][:2], mappings)
            if group["argv"][:2] != expected_prefix or group["argv"][1] != wrapper:
                raise RuntimeError(f"ready Swift common group must retain its frozen Python driver: {group_id}")
        elif group["argv"][0] != tools["runner"]["path"]:
            raise RuntimeError(f"ready native group must use the bound runner: {group_id}")
        if group_id not in SWIFT_WRAPPERS:
            flag = FAMILY_TOOL_FLAGS[group["family"]]
            positions = [index for index, argument in enumerate(group["argv"]) if argument == flag]
            if len(positions) != 1 or positions[0] + 1 >= len(group["argv"]) \
                    or group["argv"][positions[0] + 1] != tools[group["family"]]["path"]:
                raise RuntimeError(f"ready group does not use its bound family tool path: {group_id}")
    if group.get("case_ids") != frozen.get("case_ids"):
        raise RuntimeError(f"frozen case membership changed for {group_id}")
    source_reports = group.get("reports", [])
    frozen_reports = frozen.get("reports", [])
    if len(source_reports) != len(frozen_reports):
        raise RuntimeError(f"frozen report membership changed for {group_id}")
    for actual_report, frozen_report in zip(source_reports, frozen_reports):
        for key in ("case_ids", "ordinal", "path", "tool"):
            if actual_report.get(key) != frozen_report.get(key):
                raise RuntimeError(f"frozen report {key} changed for {group_id}")
        source_path = actual_report.get("source_path", "")
        if not isinstance(source_path, str) or not any(
                source_path == root or source_path.startswith(root.rstrip("/") + "/")
                for root in group.get("output_roots", [])):
            raise RuntimeError(f"group report output path differs from frozen output roots: {group_id}")
    _validate_setup_file_bindings(group.get("setup_files"), group_id)
    return group


def _validate_setup_file_bindings(items, group_id: str) -> list[dict]:
    if not isinstance(items, list):
        raise RuntimeError(f"setup_files must be a list: {group_id}")
    normalized = []
    targets = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"source", "path", "sha256", "mode"}:
            raise RuntimeError(f"setup file binding must contain source, path, sha256, and mode: {group_id}")
        source, relative = item["source"], item["path"]
        if not isinstance(source, str) or not Path(source).is_absolute():
            raise RuntimeError(f"setup file source must be an absolute path: {group_id}")
        if not isinstance(relative, str):
            raise RuntimeError(f"setup file destination must be relative: {group_id}")
        target = PurePosixPath(relative)
        if (target.is_absolute() or target.parts[:2] != ("home", ".m2")
                or any(part in {"", ".", ".."} for part in target.parts)):
            raise RuntimeError(f"setup file destination must be below home/.m2: {group_id}")
        digest = _validate_sha(item["sha256"], f"setup file {group_id} sha256")
        mode = item["mode"]
        if type(mode) is not int or not 0 <= mode <= 0o777:
            raise RuntimeError(f"setup file mode must be a POSIX permission integer: {group_id}")
        if relative in targets:
            raise RuntimeError(f"duplicate setup file destination: {group_id}")
        targets.add(relative)
        normalized.append({"source": source, "path": target.as_posix(), "sha256": digest, "mode": mode})
    return normalized


def _validate_warm_group(group: dict, tools: dict) -> None:
    family = group.get("family")
    if family not in {"joern", "semgrep"} or group.get("language") != "java":
        raise RuntimeError(f"warm auxiliary is only supported for Joern/Semgrep Java: {group.get('id')}")
    ids = group.get("warm_case_ids")
    expected_sizes = [1, 2, 4, 8, 16] if family == "joern" else [1, 2, 4, 8, 12]
    if (not isinstance(ids, list) or len(ids) < max(expected_sizes)
            or not all(isinstance(value, str) and value for value in ids)
            or len(ids) != len(set(ids)) or ids != sorted(ids)):
        raise RuntimeError(f"warm group must bind its sorted full case population: {group.get('id')}")
    sizes = group.get("warm_batch_sizes")
    if sizes != expected_sizes or max(expected_sizes) > len(ids):
        raise RuntimeError(f"warm group batch sizes differ from its static population: {group.get('id')}")
    if group.get("deadline_seconds") != 600:
        raise RuntimeError(f"warm group deadline must remain 600 seconds: {group.get('id')}")
    output = f"reports/raw/warm-latency/{family}-java-kernel"
    if group.get("output_roots") != [output]:
        raise RuntimeError(f"warm group output root differs from the registered artifact path: {group.get('id')}")
    argv = group.get("argv")
    if not isinstance(argv, list) or not argv or argv[0] != tools["runner"]["path"]:
        raise RuntimeError(f"warm group must use the bound runner: {group.get('id')}")
    binary_flag = "--joern" if family == "joern" else "--semgrep"
    expected = [tools["runner"]["path"], "--population", "v0.9.0", "measure-warm-latency",
                "--tool", family, "--language", "java", "--batch-sizes", ",".join(map(str, sizes)),
                binary_flag, tools[family]["path"]]
    if argv != expected:
        raise RuntimeError(f"warm group arguments differ from the frozen warm series: {group.get('id')}")


def _overhead_args(group: dict, tools: dict) -> tuple[str, str]:
    argv = group.get("argv")
    if not isinstance(argv, list) or not argv or argv[0] != tools["runner"]["path"]:
        raise RuntimeError(f"overhead group must use the bound runner: {group.get('id')}")
    if argv.count("estimate-invocation-overhead") != 1:
        raise RuntimeError(f"overhead command is malformed: {group.get('id')}")
    values = {}
    for flag in ("--tool", "--language"):
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise RuntimeError(f"overhead command lacks an unambiguous {flag}: {group.get('id')}")
        values[flag] = argv[argv.index(flag) + 1]
    family, language = values["--tool"], values["--language"]
    if family not in FAMILIES or family != group.get("family"):
        raise RuntimeError(f"overhead command family differs from its group: {group.get('id')}")
    flag = FAMILY_TOOL_FLAGS[family]
    positions = [index for index, argument in enumerate(argv) if argument == flag]
    if len(positions) != 1 or positions[0] + 1 >= len(argv) \
            or argv[positions[0] + 1] != tools[family]["path"]:
        raise RuntimeError(f"overhead command does not use its bound family tool path: {group.get('id')}")
    output_root = f"reports/raw/invocation-overhead/{family}-{language}"
    if group.get("output_roots") != [output_root]:
        raise RuntimeError(f"overhead output root differs from its tool/language: {group.get('id')}")
    if group.get("deadline_seconds") != 600:
        raise RuntimeError(f"overhead command deadline must remain 600 seconds: {group.get('id')}")
    return family, language


def _copy_setup_files(group: dict, source_root: Path) -> list[dict]:
    receipts = []
    for item in _validate_setup_file_bindings(group.get("setup_files", []), group["id"]):
        origin = Path(item["source"])
        if not origin.is_file() or origin.is_symlink() or sha(origin) != item["sha256"]:
            raise RuntimeError(f"setup file source is missing or has changed: {origin}")
        destination = source_root / Path(*PurePosixPath(item["path"]).parts)
        m2_root = source_root / "home/.m2"
        cursor = source_root
        for part in PurePosixPath(item["path"]).parts:
            cursor = cursor / part
            if cursor.exists() and cursor.is_symlink():
                raise RuntimeError(f"setup file target traverses a symlink: {cursor}")
        if destination.exists() or destination.is_symlink():
            raise RuntimeError(f"setup file target already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.resolve(strict=False).is_relative_to(m2_root.resolve(strict=False)):
            raise RuntimeError(f"setup file target escaped home/.m2: {destination}")
        shutil.copyfile(origin, destination)
        destination.chmod(item["mode"])
        copied_sha = sha(destination)
        if copied_sha != item["sha256"]:
            raise RuntimeError(f"copied setup file SHA-256 differs: {destination}")
        receipts.append({"source": str(origin), "path": item["path"], "destination": str(destination),
                         "sha256": copied_sha, "mode": item["mode"]})
    return receipts


def _prepare_pysa_tmp(group: dict, source_root: Path, environment: dict) -> dict | None:
    if group.get("tool") != "pysa":
        return None
    expected_name = "dfb-v092-pysa-" + hashlib.sha256(
        str(source_root.resolve()).encode()).hexdigest()[:20]
    expected = PYSA_TMP_ROOT / expected_name
    actual = Path(environment.get("TMPDIR", ""))
    if actual != expected:
        raise RuntimeError(f"Pysa scratch path differs from the reviewed source-bound path: {actual}")
    if not PYSA_TMP_ROOT.is_dir() or PYSA_TMP_ROOT.is_symlink():
        raise RuntimeError(f"Pysa scratch parent is missing or symlinked: {PYSA_TMP_ROOT}")
    if expected.exists() or expected.is_symlink():
        raise RuntimeError(f"Pysa scratch path already exists; refusing to reuse or delete it: {expected}")
    expected.mkdir(mode=0o700)
    if expected.is_symlink() or not expected.is_dir():
        raise RuntimeError(f"Pysa scratch path is not a fresh directory: {expected}")
    return {"path": str(expected), "created_fresh": True, "owner_group": group["id"],
            "source_snapshot": str(source_root)}


def _verify_setup_files(group: dict, source_root: Path) -> list[dict]:
    receipts = []
    for item in _validate_setup_file_bindings(group.get("setup_files", []), group["id"]):
        target = source_root
        for part in PurePosixPath(item["path"]).parts:
            target = target / part
            if target.is_symlink():
                raise RuntimeError(f"prepared dependency traverses a symlink: {target}")
        if (not target.is_file() or sha(target) != item["sha256"]
                or stat.S_IMODE(target.stat().st_mode) != item["mode"]):
            raise RuntimeError(f"prepared dependency changed: {target}")
        receipts.append({"path": item["path"], "sha256": item["sha256"], "mode": item["mode"]})
    return receipts


def _campaign_scratch_paths(sources: Path, ready_groups: list[dict], external_scratch: dict) -> list[Path]:
    result = []
    for group in ready_groups:
        source = sources / group["id"]
        result.extend(source / name for name in ("home", "tmp", "cache"))
        owned = external_scratch.get(group["id"])
        if owned is not None:
            result.append(Path(owned["path"]))
    return result


def _helper_bindings(root: Path, source_helpers: dict) -> dict[str, str]:
    result = {}
    for relative in HELPERS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"execution helper is missing or not a regular file: {relative}")
        digest = sha(path)
        expected_source = source_helpers.get(relative)
        if expected_source is not None and expected_source != digest:
            transition = SOURCE_HELPER_TRANSITIONS.get(relative)
            if (transition is None or expected_source != transition["source_sha256"]
                    or digest != transition["active_sha256"]):
                raise RuntimeError(f"existing timing helper differs from the source plan: {relative}")
        result[relative] = digest
    return result


def _frozen_report_blob(root: Path, report_path: str) -> tuple[str, bytes]:
    """Read the report from the exact release commit, including its publication alias."""
    try:
        return report_path, legacy.core._git_show(root, RELEASE, report_path)
    except legacy.core.ReleaseError:
        source_prefix = "reports/releases/v0.9.2/normal/"
        if not report_path.startswith(source_prefix):
            raise
        published = "reports/releases/v0.9.2/publication-v1/normal/" + report_path[len(source_prefix):]
        return published, legacy.core._git_show(root, RELEASE, published)


def _frozen_report_bindings(root: Path, groups: list[dict]) -> dict:
    result = {}
    for group in groups:
        if group.get("kind") != "cold":
            continue
        reports = []
        for descriptor in group.get("reports", []):
            report_path = descriptor.get("path")
            if not isinstance(report_path, str):
                raise RuntimeError(f"frozen report path is malformed: {group.get('id')}")
            git_path, raw = _frozen_report_blob(root, report_path)
            try:
                value = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"frozen report is invalid JSON: {git_path}") from exc
            reports.append({"contract_path": report_path, "git_path": git_path,
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "identity": {key: value.get(key) for key in (
                                "tool", "tool_version", "tool_build_identity", "configuration_hash",
                                "fixture_revision", "cold_or_warm", "adapter_version", "schema_version")}})
        result[group["id"]] = reports
    return result


def _build_plan(root: Path, bindings: dict, bindings_digest: str,
                bindings_relative_path: str | None = None) -> dict:
    if bindings.get("schema") != "v092-qualified-runtime-bindings/v1":
        raise RuntimeError("unsupported qualified runtime bindings schema")
    if bindings.get("release_commit") != RELEASE:
        raise RuntimeError("bindings release_commit differs from frozen v0.9.2")
    if bindings_relative_path is None:
        raise RuntimeError("runtime bindings must have a committed repository-relative path")
    binding_path = PurePosixPath(bindings_relative_path)
    if binding_path.is_absolute() or ".." in binding_path.parts:
        raise RuntimeError("runtime bindings path must remain repository-relative")
    _validate_sha(bindings_digest, "runtime bindings sha256")
    preregistration = bindings.get("preregistration")
    if preregistration is not None:
        if not isinstance(preregistration, dict) or set(preregistration) != {"path", "sha256"}:
            raise RuntimeError("preregistration must contain exactly path and sha256")
        prereg_path = preregistration["path"]
        prereg_sha = _validate_sha(preregistration["sha256"], "preregistration sha256")
        if (not isinstance(prereg_path, str) or Path(prereg_path).is_absolute()
                or ".." in PurePosixPath(prereg_path).parts):
            raise RuntimeError("preregistration path must remain repository-relative")
        prereg_file = root / prereg_path
        if not prereg_file.is_file() or sha(prereg_file) != prereg_sha:
            raise RuntimeError("preregistration file is missing or its SHA-256 differs")
    campaign_id = _campaign_id(bindings.get("campaign_id"))
    launch_after = _utc(bindings.get("launch_after_utc"), "launch_after_utc")
    source_ref = _source_reference(bindings)
    source_path = root / source_ref["path"]
    if not source_path.is_file() or sha(source_path) != source_ref["sha256"]:
        raise RuntimeError("source plan is missing or its SHA-256 differs")
    source = json.loads(source_path.read_text())
    if source.get("release_commit") != RELEASE:
        raise RuntimeError("source plan is not pinned to the frozen release commit")
    if source.get("schema") != "v092-timing-supplement-plan/v1":
        raise RuntimeError("source plan schema is not the retained v0.9.2 timing plan")
    frozen_path = root / FROZEN_CONTRACT
    if not frozen_path.is_file():
        raise RuntimeError("frozen execution-v4 contract is missing")
    frozen_contract = json.loads(frozen_path.read_text())
    frozen_groups = {group["id"]: group for group in frozen_contract.get("groups", [])}
    source_groups = [group for group in source.get("groups", []) if group.get("kind") == "cold"]
    if len(source_groups) != SOURCE_GROUPS or len({g.get("id") for g in source_groups}) != SOURCE_GROUPS:
        raise RuntimeError("source plan must contain exactly 84 distinct cold groups")
    source_ids = {group["id"] for group in source_groups}
    if source_ids != set(frozen_groups):
        raise RuntimeError("source plan cold-group membership differs from frozen execution-v4")
    for group in source_groups:
        frozen = frozen_groups[group["id"]]
        if group.get("case_ids") != frozen.get("case_ids"):
            raise RuntimeError(f"source plan membership differs from frozen execution-v4: {group['id']}")
        source_reports = group.get("reports", [])
        frozen_reports = frozen.get("reports", [])
        if len(source_reports) != len(frozen_reports):
            raise RuntimeError(f"source plan report membership differs from frozen execution-v4: {group['id']}")
        for source_report, frozen_report in zip(source_reports, frozen_reports):
            for key in ("case_ids", "ordinal", "path", "tool"):
                if source_report.get(key) != frozen_report.get(key):
                    raise RuntimeError(f"source plan report {key} differs from frozen execution-v4: {group['id']}")

    tools = bindings.get("tools")
    expected_tools = {"runner", *FAMILIES}
    if not isinstance(tools, dict) or set(tools) != expected_tools:
        raise RuntimeError("bindings tools must include runner and all eight analyzer families")
    normalized_tools = {}
    for name, binding in tools.items():
        if (not isinstance(binding, dict) or not isinstance(binding.get("path"), str)
                or not Path(binding["path"]).is_absolute()):
            raise RuntimeError(f"tools.{name}.path must be absolute")
        normalized_tools[name] = dict(binding)
        normalized_tools[name]["sha256"] = _validate_sha(binding.get("sha256"), f"tools.{name}.sha256")

    runtimes = bindings.get("runtimes")
    if not isinstance(runtimes, list):
        raise RuntimeError("bindings runtimes must be a list")
    runtime_ids = set()
    normalized_runtimes = []
    for item in runtimes:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise RuntimeError("each runtime binding must contain a nonempty id")
        if item["id"] in runtime_ids:
            raise RuntimeError(f"duplicate runtime binding id: {item['id']}")
        runtime_ids.add(item["id"])
        if not isinstance(item.get("path"), str):
            raise RuntimeError(f"runtime path is missing: {item['id']}")
        normalized = dict(item)
        normalized["sha256"] = _validate_sha(item.get("sha256"), f"runtime {item['id']} sha256")
        if "uncompressed_sha256" in normalized:
            normalized["uncompressed_sha256"] = _validate_sha(
                normalized["uncompressed_sha256"], f"runtime {item['id']} uncompressed_sha256")
        normalized_runtimes.append(normalized)

    mappings = _rebindings(bindings)
    overrides = bindings.get("group_overrides", {})
    if not isinstance(overrides, dict):
        raise RuntimeError("group_overrides must be an object")
    aux_groups = bindings.get("auxiliary_groups", [])
    if not isinstance(aux_groups, list):
        raise RuntimeError("auxiliary_groups must be a list")
    groups = []
    for source_group in source_groups:
        group_id = source_group["id"]
        if group_id not in overrides:
            overrides_for_group = {}
        else:
            overrides_for_group = overrides[group_id]
        if not isinstance(overrides_for_group, dict):
            raise RuntimeError(f"group override must be an object: {group_id}")
        groups.append(_normalize_source_group(
            source_group, frozen_groups[group_id], overrides_for_group, mappings, normalized_tools))
    auxiliary_ids = []
    for auxiliary in aux_groups:
        if not isinstance(auxiliary, dict) or not isinstance(auxiliary.get("id"), str):
            raise RuntimeError("auxiliary groups must be objects with ids")
        group_id = auxiliary["id"]
        if group_id in source_ids or any(group["id"] == group_id for group in groups):
            raise RuntimeError(f"duplicate auxiliary group id: {group_id}")
        auxiliary_ids.append(group_id)
        group = _json_copy(auxiliary)
        group.pop("status", None)
        group.pop("blocker", None)
        group.setdefault("setup_files", [])
        override = overrides.get(group_id, {})
        if not isinstance(override, dict):
            raise RuntimeError(f"group override must be an object: {group_id}")
        unknown = set(override) - {"argv", "environment", "status", "blocker", "runtime_ids", "setup_files"}
        if unknown:
            raise RuntimeError(f"unsupported group override fields for {group_id}: {sorted(unknown)}")
        canonical_argv = _json_copy(group.get("argv", []))
        if "argv" in override and _rewrite_value(override["argv"], mappings) != _rewrite_value(
                canonical_argv, mappings):
            raise RuntimeError(f"auxiliary group argv override changes command semantics: {group_id}")
        if "setup_files" in override:
            group["setup_files"] = _json_copy(override["setup_files"])
        canonical_environment = _environment_with_reviewed_overrides(
            group.get("environment", {}), override.get("environment", {}), mappings, group_id)
        group["runtime_ids"] = _json_copy(override.get("runtime_ids", group.get("runtime_ids", [])))
        group["argv"] = canonical_argv
        group = _rewrite_value(group, mappings)
        group["environment"] = canonical_environment
        status = override.get("status", "blocked")
        if status not in {"ready", "blocked"}:
            raise RuntimeError(f"group status override must be ready or blocked: {group_id}")
        group["status"] = status
        if status == "blocked":
            blocker = override.get("blocker") or auxiliary.get("blocker")
            group["blocker"] = blocker if isinstance(blocker, str) and blocker.strip() else (
                "No reviewed runtime and readiness override was supplied for this prospective campaign.")
        else:
            group.pop("blocker", None)
            if not group["runtime_ids"] or not all(isinstance(item, str) and item for item in group["runtime_ids"]):
                raise RuntimeError(f"ready group must explicitly bind runtime_ids: {group_id}")
            if group.get("family") not in FAMILIES:
                raise RuntimeError(f"ready auxiliary group has no family tool binding: {group_id}")
            if group.get("kind") not in {"cold", "overhead", "warm"}:
                raise RuntimeError(f"ready auxiliary group kind has no supported artifact schema: {group_id}")
            if not isinstance(group.get("argv"), list) or not group["argv"] or not all(
                    isinstance(arg, str) and arg for arg in group["argv"]):
                raise RuntimeError(f"ready auxiliary group has invalid argv: {group_id}")
            if group["argv"][0] != normalized_tools["runner"]["path"]:
                raise RuntimeError(f"ready auxiliary group must use the bound runner: {group_id}")
            if group.get("kind") == "warm":
                _validate_warm_group(group, normalized_tools)
            elif group.get("kind") == "overhead":
                legacy.validate_overhead_group(group)
                _overhead_args(group, normalized_tools)
        _validate_setup_file_bindings(group.get("setup_files", []), group_id)
        groups.append(group)

    extra_overrides = set(overrides) - {group["id"] for group in groups}
    if extra_overrides:
        raise RuntimeError(f"group_overrides reference unknown groups: {sorted(extra_overrides)}")
    known_runtime_ids = {item["id"] for item in normalized_runtimes}
    for group in groups:
        if group.get("status") == "ready":
            missing = set(group.get("runtime_ids", [])) - known_runtime_ids
            if missing:
                raise RuntimeError(f"ready group references unbound runtimes {sorted(missing)}: {group['id']}")

    group_order = bindings.get("group_order")
    all_ids = {group["id"] for group in groups}
    if (not isinstance(group_order, list) or len(group_order) != len(all_ids)
            or set(group_order) != all_ids or len(set(group_order)) != len(group_order)):
        raise RuntimeError("group_order must list every cold and auxiliary group exactly once")
    by_id = {group["id"]: group for group in groups}
    first_eight = [by_id[group_id] for group_id in group_order[:len(FAMILIES)]]
    if (len(first_eight) != len(FAMILIES)
            or any(group.get("kind") != "cold" or group.get("status") != "ready" for group in first_eight)
            or {group["family"] for group in first_eight} != set(FAMILIES)):
        raise RuntimeError("group_order must start with one ready cold group for each analyzer family")
    first_ids = {group["id"] for group in first_eight}
    remaining_cold = [group["id"] for group in groups
                      if group.get("kind") == "cold" and group["id"] not in first_ids]
    if group_order[len(FAMILIES):len(FAMILIES) + len(remaining_cold)] != remaining_cold:
        raise RuntimeError("group_order must preserve frozen order after the balanced first groups")
    if group_order[len(FAMILIES) + len(remaining_cold):] != auxiliary_ids:
        raise RuntimeError("group_order must place auxiliary groups last in their supplied order")
    groups = [by_id[group_id] for group_id in group_order]

    source_helpers = source.get("execution_helpers", {})
    if not isinstance(source_helpers, dict):
        raise RuntimeError("source plan execution_helpers must be an object")
    execution_helpers = _helper_bindings(root, source_helpers)
    frozen_report_bindings = _frozen_report_bindings(root, groups)
    auxiliary_deadlines = [group.get("deadline_seconds") for group in groups if group["kind"] != "cold"]
    if any(type(deadline) not in (int, float) or not math.isfinite(deadline) or deadline <= 0
           for deadline in auxiliary_deadlines):
        raise RuntimeError("auxiliary group deadlines must be finite and positive")
    ready = [group for group in groups if group.get("status") == "ready"]
    cold_ready = [group for group in ready if group.get("kind") == "cold"]
    max_wall = bindings.get("max_campaign_wall_seconds", DEFAULT_MAX_CAMPAIGN_WALL_SECONDS)
    if type(max_wall) is not int or max_wall <= 0:
        raise RuntimeError("max_campaign_wall_seconds must be a positive integer")
    plan = {
        "schema": "v092-qualified-timing-campaign-plan/v1",
        "campaign_id": campaign_id,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "launch_after_utc": launch_after.isoformat(),
        "max_campaign_wall_seconds": max_wall,
        "release_commit": RELEASE,
        "population": source["population"],
        "fixture_revision": source["fixture_revision"],
        "frozen_release_unchanged": True,
        "new_campaign_not_old_series_resume": True,
        "source_plan": {**source_ref, "bindings_sha256": bindings_digest},
        "runtime_bindings": {"path": binding_path.as_posix(), "sha256": bindings_digest},
        "preregistration": _json_copy(preregistration),
        "frozen_execution_contract": {
            "path": FROZEN_CONTRACT,
            "sha256": sha(frozen_path),
        },
        "source_projection": _json_copy(source["source_projection"]),
        "source_cold_group_order": [group["id"] for group in source_groups],
        "path_rebindings": mappings,
        "tools": normalized_tools,
        "runtimes": normalized_runtimes,
        "source_execution_helpers": _json_copy(source_helpers),
        "helper_transitions": _json_copy({
            relative: transition for relative, transition in SOURCE_HELPER_TRANSITIONS.items()
            if source_helpers.get(relative) != execution_helpers.get(relative)
        }),
        "execution_helpers": execution_helpers,
        "frozen_report_bindings": frozen_report_bindings,
        "group_order": list(group_order),
        "groups": groups,
        "planned_coverage": {
            "cold_groups": SOURCE_GROUPS,
            "ready_cold_groups": len(cold_ready),
            "blocked_cold_groups": SOURCE_GROUPS - len(cold_ready),
            "ready_analyzer_families": sorted({group["family"] for group in cold_ready}),
            "all_84_cold_groups_ready": len(cold_ready) == SOURCE_GROUPS,
            "full_coverage_claimed": False,
        },
        "resources": {
            "launch_free_gib": 127,
            "continuous_free_gib": 125,
            "working_source_gib": 30,
            "per_source_gib": 12,
            "scratch_gib": 24,
            "retention_gib": 24,
            "serial_analyzers": 1,
            "automatic_retry": False,
            "total_execution_budget_seconds": sum(group["deadline_seconds"] for group in ready),
        },
        "qualification": {
            "note": str(bindings.get("qualification_note", "")),
            "warm_population_correction": (
                "Joern Java retains batches 1,2,4,8,16. Semgrep Java uses 1,2,4,8,12 because the frozen "
                "static common-rule population has 12 cases; exact ordered IDs are bound per warm group. "
                "No analyzer observations selected the population."
            ),
            "evidence_status": "prospective candidate timing evidence only",
            "quiet_window": "fresh 300-second window with >=90% aggregate CPU idle and <=60-second sample gaps before every ready command",
            "quiet_predicate": "four recorded conditions: initial quiet gate passed, settle not skipped, no observed contention, no CPU observation failures",
            "contention_policy": "active CPU and post-run contention are recorded and do not abort or reorder a command queue",
            "descendant_containment": "unproven and separately reported",
            "publication_eligible": False,
            "global_resource_or_external_certification": False,
        },
    }
    if bindings.get("continuation") is not None:
        plan["continuation"] = _json_copy(bindings["continuation"])
        plan["execution_helpers"][CONTINUATION_HELPER] = sha(root / CONTINUATION_HELPER)
        if bindings.get("continuation_mode") is not None:
            if bindings["continuation_mode"] != SEMANTIC_CONTINUATION_MODE:
                raise RuntimeError("unsupported continuation mode")
            plan["continuation_mode"] = SEMANTIC_CONTINUATION_MODE
            plan["semantic_mismatch_policy"] = _json_copy(bindings.get("semantic_mismatch_policy"))
            plan["execution_authorization"] = _json_copy(bindings.get("execution_authorization"))
            plan["execution_helpers"][SEGMENT_CHECKPOINT_HELPER] = sha(root / SEGMENT_CHECKPOINT_HELPER)
        checkpoint = _continuation_checkpoint(plan, root=root, compare_plan=False)
        carried = set(checkpoint["completed_groups"]) | set(checkpoint.get("quarantined_groups", []))
        plan["resources"]["total_execution_budget_seconds"] = sum(
            group["deadline_seconds"] for group in ready if group["id"] not in carried)
        _continuation_checkpoint(plan, root=root)
    return plan


def prepare(bindings_path: Path, output_path: Path) -> dict:
    bindings_path = Path(bindings_path)
    if not bindings_path.is_file() or bindings_path.is_symlink():
        raise RuntimeError(f"bindings file is missing or not a regular file: {bindings_path}")
    raw = bindings_path.read_bytes()
    bindings_digest = hashlib.sha256(raw).hexdigest()
    bindings = json.loads(raw)
    try:
        bindings_relative_path = bindings_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("bindings file must be inside the repository so execute can verify committed bytes") from exc
    plan = _build_plan(ROOT, bindings, bindings_digest, bindings_relative_path)
    report, _ = legacy.campaign_paths(plan["campaign_id"])
    output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path = output_path.resolve(strict=False)
    if output_path.parent != report.resolve() or not output_path.name.startswith("qualified-plan") \
            or output_path.suffix != ".json" or output_path.name == "plan.json":
        raise RuntimeError("output must be a unique qualified-plan*.json inside the new campaign directory")
    if output_path.exists() or output_path.is_symlink():
        raise RuntimeError(f"refusing to overwrite a plan: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_new(output_path, plan)
    return {"plan": str(output_path), "campaign_id": plan["campaign_id"],
            "cold_groups": SOURCE_GROUPS,
            "ready_cold_groups": plan["planned_coverage"]["ready_cold_groups"],
            "blocked_cold_groups": plan["planned_coverage"]["blocked_cold_groups"],
            "ready_families": plan["planned_coverage"]["ready_analyzer_families"]}


def _manifest_bytes(binding: dict) -> tuple[bytes, str, str | None]:
    path = _path(ROOT, binding["path"])
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"runtime manifest is missing or not a regular file: {path}")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise RuntimeError(f"runtime manifest SHA-256 differs: {path}")
    uncompressed_hash = None
    if path.suffix == ".gz":
        if "uncompressed_sha256" not in binding:
            raise RuntimeError(f"compressed runtime manifest lacks uncompressed_sha256: {path}")
        try:
            unpacked = gzip.decompress(raw)
        except OSError as exc:
            raise RuntimeError(f"runtime manifest gzip is corrupt: {path}") from exc
        uncompressed_hash = hashlib.sha256(unpacked).hexdigest()
        if uncompressed_hash != binding["uncompressed_sha256"]:
            raise RuntimeError(f"runtime manifest uncompressed SHA-256 differs: {path}")
        raw = unpacked
    elif "uncompressed_sha256" in binding:
        uncompressed_hash = hashlib.sha256(raw).hexdigest()
        if uncompressed_hash != binding["uncompressed_sha256"]:
            raise RuntimeError(f"runtime manifest uncompressed SHA-256 differs: {path}")
    legacy.core._check_runtime_tree_manifest(raw, binding["id"])
    return raw, binding["sha256"], uncompressed_hash


def _check_tool(binding: dict, name: str) -> dict:
    path = _path(ROOT, binding["path"])
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"{name} tool is missing or not a regular file: {path}")
    actual = sha(path)
    if actual != binding["sha256"]:
        raise RuntimeError(f"{name} tool SHA-256 differs: {path}")
    return {"name": name, "path": str(path), "sha256": actual}


def _groups(plan: dict) -> list[dict]:
    groups = plan.get("groups")
    if not isinstance(groups, list) or not groups:
        raise RuntimeError("plan groups must be a nonempty list")
    ids = [group.get("id") for group in groups if isinstance(group, dict)]
    if len(ids) != len(groups) or len(set(ids)) != len(ids):
        raise RuntimeError("plan groups must have unique ids")
    cold = [group for group in groups if group.get("kind") == "cold"]
    if len(cold) != SOURCE_GROUPS:
        raise RuntimeError("qualified plan must retain all 84 frozen cold groups")
    return groups


def _validate_plan_shape(plan: dict) -> None:
    if plan.get("schema") != "v092-qualified-timing-campaign-plan/v1":
        raise RuntimeError("unsupported qualified timing plan schema")
    if plan.get("release_commit") != RELEASE:
        raise RuntimeError("plan release_commit differs from frozen v0.9.2")
    _campaign_id(plan.get("campaign_id"))
    _utc(plan.get("launch_after_utc"), "launch_after_utc")
    if type(plan.get("max_campaign_wall_seconds")) is not int or plan["max_campaign_wall_seconds"] <= 0:
        raise RuntimeError("plan max_campaign_wall_seconds must be a positive integer")
    binding = plan.get("runtime_bindings")
    if (not isinstance(binding, dict) or not isinstance(binding.get("path"), str)
            or Path(binding["path"]).is_absolute() or ".." in PurePosixPath(binding["path"]).parts):
        raise RuntimeError("plan runtime_bindings must pin a repository-relative path")
    _validate_sha(binding.get("sha256"), "plan runtime_bindings sha256")
    preregistration = plan.get("preregistration")
    if preregistration is not None:
        if not isinstance(preregistration, dict) or set(preregistration) != {"path", "sha256"}:
            raise RuntimeError("plan preregistration must contain path and sha256")
        if not isinstance(preregistration["path"], str) or Path(preregistration["path"]).is_absolute() \
                or ".." in PurePosixPath(preregistration["path"]).parts:
            raise RuntimeError("plan preregistration path must remain repository-relative")
        _validate_sha(preregistration["sha256"], "plan preregistration sha256")
    tools = plan.get("tools")
    if not isinstance(tools, dict) or set(tools) != {"runner", *FAMILIES}:
        raise RuntimeError("plan must bind runner and all eight analyzer tools")
    for name, binding in tools.items():
        if not isinstance(binding, dict) or not isinstance(binding.get("path"), str) \
                or not Path(binding["path"]).is_absolute():
            raise RuntimeError(f"plan tool path must be absolute: {name}")
        _validate_sha(binding.get("sha256"), f"plan tool {name} sha256")
    runtimes = plan.get("runtimes")
    if not isinstance(runtimes, list) or len({item.get("id") for item in runtimes}) != len(runtimes):
        raise RuntimeError("plan runtimes must be a list with unique ids")
    for runtime in runtimes:
        if not isinstance(runtime, dict) or not isinstance(runtime.get("id"), str) \
                or not isinstance(runtime.get("path"), str):
            raise RuntimeError("runtime bindings require id and path")
        _validate_sha(runtime.get("sha256"), f"runtime {runtime.get('id')} sha256")
        if "uncompressed_sha256" in runtime:
            _validate_sha(runtime["uncompressed_sha256"], f"runtime {runtime['id']} uncompressed_sha256")
    source_helpers = plan.get("source_execution_helpers")
    active_helpers = plan.get("execution_helpers")
    expected_source_helpers = set(HELPERS) - {"scripts/v092_timing_qualified_campaign.py"}
    if not isinstance(source_helpers, dict) or set(source_helpers) != expected_source_helpers:
        raise RuntimeError("plan must retain the source plan execution helper map")
    expected_active_helpers = set(HELPERS)
    if plan.get("continuation_mode") is not None:
        if (plan["continuation_mode"] != SEMANTIC_CONTINUATION_MODE
                or plan.get("semantic_mismatch_policy") != SEMANTIC_MISMATCH_POLICY
                or plan.get("continuation") is None):
            raise RuntimeError("invalid semantic continuation policy")
        expected_active_helpers.add(SEGMENT_CHECKPOINT_HELPER)
        authorization = plan.get("execution_authorization")
        if (not isinstance(authorization, dict) or set(authorization) != {"path", "sha256"}
                or not isinstance(authorization["path"], str)
                or PurePosixPath(authorization["path"]).is_absolute()
                or ".." in PurePosixPath(authorization["path"]).parts):
            raise RuntimeError("execution_authorization must bind a repository-relative receipt")
        _validate_sha(authorization["sha256"], "execution authorization SHA-256")
    elif "semantic_mismatch_policy" in plan or "execution_authorization" in plan:
        raise RuntimeError("semantic policy and execution authorization require the explicit continuation mode")
    if plan.get("continuation") is not None:
        expected_active_helpers.add(CONTINUATION_HELPER)
        reference = plan["continuation"]
        if (not isinstance(reference, dict) or set(reference) != {"path", "sha256"}
                or not isinstance(reference["path"], str)
                or PurePosixPath(reference["path"]).is_absolute()
                or ".." in PurePosixPath(reference["path"]).parts):
            raise RuntimeError("continuation must bind a repository-relative checkpoint and SHA-256")
        _validate_sha(reference["sha256"], "continuation checkpoint SHA-256")
    if not isinstance(active_helpers, dict) or set(active_helpers) != expected_active_helpers:
        raise RuntimeError("plan must bind every active execution helper")
    for relative, digest in source_helpers.items():
        _validate_sha(digest, f"source helper {relative} sha256")
    for relative, digest in active_helpers.items():
        _validate_sha(digest, f"active helper {relative} sha256")
    expected_transitions = {}
    for relative in expected_source_helpers:
        old_digest, active_digest = source_helpers[relative], active_helpers[relative]
        if old_digest == active_digest:
            continue
        transition = SOURCE_HELPER_TRANSITIONS.get(relative)
        if (transition is None or old_digest != transition["source_sha256"]
                or active_digest != transition["active_sha256"]):
            raise RuntimeError(f"plan has an unreviewed source-to-active helper transition: {relative}")
        expected_transitions[relative] = transition
    if plan.get("helper_transitions") != expected_transitions:
        raise RuntimeError("plan helper transition receipt differs from its pinned source and active hashes")
    groups = _groups(plan)
    group_order = plan.get("group_order")
    if not isinstance(group_order, list) or group_order != [group.get("id") for group in groups]:
        raise RuntimeError("plan group order differs from its explicit dispatch order")
    first_eight = groups[:len(FAMILIES)]
    if (len(first_eight) != len(FAMILIES)
            or any(group.get("kind") != "cold" or group.get("status") != "ready" for group in first_eight)
            or {group.get("family") for group in first_eight} != set(FAMILIES)):
        raise RuntimeError("plan must begin with one ready cold group for each analyzer family")
    cold_order = plan.get("source_cold_group_order")
    if not isinstance(cold_order, list) or len(cold_order) != SOURCE_GROUPS \
            or len(set(cold_order)) != SOURCE_GROUPS:
        raise RuntimeError("plan source cold-group order must bind all 84 frozen groups")
    first_ids = {group["id"] for group in first_eight}
    remaining_cold = [group_id for group_id in cold_order if group_id not in first_ids]
    auxiliary_ids = [group["id"] for group in groups if group.get("kind") != "cold"]
    if group_order != [*(group["id"] for group in first_eight), *remaining_cold, *auxiliary_ids]:
        raise RuntimeError("plan dispatch order changed balanced or frozen ordering rules")
    frozen_reports = plan.get("frozen_report_bindings")
    if not isinstance(frozen_reports, dict):
        raise RuntimeError("plan lacks frozen report byte bindings")
    cold_ids = {group["id"] for group in groups if group.get("kind") == "cold"}
    if set(frozen_reports) != cold_ids:
        raise RuntimeError("frozen report bindings do not cover exactly the cold groups")
    for group_id, bindings in frozen_reports.items():
        if not isinstance(bindings, list) or not bindings:
            raise RuntimeError(f"frozen report bindings are missing: {group_id}")
        for item in bindings:
            if not isinstance(item, dict) or not isinstance(item.get("git_path"), str):
                raise RuntimeError(f"frozen report byte binding is malformed: {group_id}")
            _validate_sha(item.get("sha256"), f"frozen report {group_id} sha256")
            if not isinstance(item.get("identity"), dict):
                raise RuntimeError(f"frozen report identity is missing: {group_id}")
    for group in groups:
        if group.get("kind") != "cold":
            continue
        expected = frozen_reports[group["id"]]
        descriptors = group.get("reports", [])
        if len(expected) != len(descriptors) or any(
                binding.get("contract_path") != descriptor.get("path")
                for binding, descriptor in zip(expected, descriptors)):
            raise RuntimeError(f"frozen report byte bindings differ from group reports: {group['id']}")
    for group in groups:
        if group.get("status") not in {"ready", "blocked"}:
            raise RuntimeError(f"invalid group status: {group.get('id')}")
        _validate_setup_file_bindings(group.get("setup_files", []), group.get("id", "unknown"))
        if group.get("status") == "blocked":
            if not isinstance(group.get("blocker"), str) or not group["blocker"].strip():
                raise RuntimeError(f"blocked group lacks a recorded reason: {group.get('id')}")
            continue
        if group.get("family") not in FAMILIES:
            raise RuntimeError(f"ready group has unknown analyzer family: {group.get('id')}")
        ids = group.get("runtime_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(item, str) and item for item in ids):
            raise RuntimeError(f"ready group lacks explicit runtime_ids: {group.get('id')}")
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"ready group has duplicate runtime_ids: {group.get('id')}")
        argv = group.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise RuntimeError(f"ready group has invalid argv: {group.get('id')}")
        if group["id"] in SWIFT_WRAPPERS:
            if argv[0] != "/usr/bin/python3" or argv[1] != SWIFT_WRAPPERS[group["id"]]:
                raise RuntimeError(f"Swift common group lost its original Python driver: {group['id']}")
        elif argv[0] != tools["runner"]["path"]:
            raise RuntimeError(f"ready group does not use bound runner: {group.get('id')}")
        if group.get("kind") not in {"cold", "overhead", "warm"}:
            raise RuntimeError(f"ready group kind has no supported artifact schema: {group.get('id')}")
        if group.get("kind") == "warm":
            _validate_warm_group(group, tools)
        elif group.get("kind") == "overhead":
            _overhead_args(group, tools)
        legacy.validate_overhead_group(group)


def _ready_groups(plan: dict) -> list[dict]:
    return [group for group in _groups(plan) if group.get("status") == "ready"]


def _continuation_checkpoint(plan: dict, root: Path | None = None, compare_plan: bool = True):
    if plan.get("continuation") is None:
        return None
    root = ROOT if root is None else root
    helper = _checkpoint_helper(plan)
    module = _load_module("qualified_timing_checkpoint", root / helper)
    return module.verify_checkpoint(root, plan["continuation"], plan if compare_plan else None)


def _checkpoint_helper(plan: dict) -> str:
    if plan.get("continuation_mode") == SEMANTIC_CONTINUATION_MODE:
        return SEGMENT_CHECKPOINT_HELPER
    return CONTINUATION_HELPER


def _execution_authorization_ok(plan: dict) -> bool:
    if plan.get("continuation_mode") != SEMANTIC_CONTINUATION_MODE:
        return True
    reference = plan["execution_authorization"]
    path = _path(ROOT, reference["path"])
    if not path.is_file() or path.is_symlink() or sha(path) != reference["sha256"]:
        raise RuntimeError("execution authorization receipt is missing or changed")
    value = json.loads(path.read_text())
    authorized = value.get("authorized")
    if (value.get("schema") != "v092-continuation-execution-authorization/v1"
            or value.get("campaign_id") != plan["campaign_id"]
            or type(authorized) is not bool
            or value.get("status") != ("authorized" if authorized else "pending")):
        raise RuntimeError("execution authorization receipt is malformed or belongs to another campaign")
    return authorized


def _outcome_only_quarantine_allowed(plan: dict, group: dict, receipt: dict) -> bool:
    if (plan.get("continuation_mode") != SEMANTIC_CONTINUATION_MODE
            or plan.get("semantic_mismatch_policy") != SEMANTIC_MISMATCH_POLICY
            or group.get("kind") != "cold" or receipt.get("status") != "mismatch"
            or receipt.get("group") != group["id"]):
        return False
    # The comparator stops at its first mismatching report. Multiple-report
    # groups therefore cannot prove the remaining report identities here.
    reports = receipt.get("reports", [])
    descriptors = group.get("reports", [])
    bindings = plan.get("frozen_report_bindings", {}).get(group["id"], [])
    if len(reports) != 1 or len(descriptors) != 1 or len(bindings) != 1:
        return False
    observed, descriptor, binding = reports[0], descriptors[0], bindings[0]
    identity_fields = ["tool", "tool_version", "tool_build_identity", "configuration_hash",
                       "fixture_revision", "cold_or_warm", "adapter_version", "schema_version"]
    if (observed.get("contract_path") != descriptor["path"]
            or observed.get("release_git_path") != binding["git_path"]
            or observed.get("frozen_sha256") != binding["sha256"]
            or not isinstance(observed.get("measured_sha256"), str)
            or SHA256_PATTERN.fullmatch(observed["measured_sha256"]) is None
            or observed.get("identity_fields_compared") != identity_fields
            or type(observed.get("case_outcomes_compared")) is not int
            or observed.get("case_outcomes_compared") != len(descriptor["case_ids"])):
        return False
    mismatches = observed.get("mismatches")
    outcomes = {"reached", "not-reached", "inconclusive", "unsupported", "runner-error"}
    return isinstance(mismatches, list) and bool(mismatches) and all(
        isinstance(item, dict) and item.get("field") == "outcome"
        and item.get("classification") == "mismatch"
        and item.get("case_id") in descriptor["case_ids"]
        and isinstance(item.get("expected"), str) and item["expected"] in outcomes
        and isinstance(item.get("actual"), str) and item["actual"] in outcomes
        and item["expected"] != item["actual"] for item in mismatches)


def _dispatch_groups(plan: dict) -> list[dict]:
    checkpoint = _continuation_checkpoint(plan)
    ready = _ready_groups(plan)
    if checkpoint is None:
        return ready
    remaining = checkpoint["remaining_ready_groups"]
    result = [group for group in ready if group["id"] in set(remaining)]
    if [group["id"] for group in result] != remaining:
        raise RuntimeError("continuation dispatch order differs from its bound checkpoint")
    return result


def _inherited_resource_paths(checkpoint: dict | None):
    if checkpoint is None:
        return [], [], []
    if (checkpoint.get("schema") == "v092-timing-segment-checkpoint/v1"
            and checkpoint.get("resource_campaign_ids") != ["20261115-01", "20261121-01"]):
        raise RuntimeError("semantic continuation must account for both parent resource namespaces")
    ids = checkpoint.get("resource_campaign_ids", [checkpoint["parent_campaign_id"]])
    contexts = [legacy.campaign_paths(campaign_id) for campaign_id in ids]
    source_roots = [work / "sources" for _report, work in contexts]
    retained, scratch = [], []
    for (report, _work), sources in zip(contexts, source_roots):
        if not sources.is_dir() or sources.is_symlink():
            raise RuntimeError("continuation parent source namespace is unavailable or redirected")
        children = list(sources.iterdir())
        if any(not path.is_dir() or path.is_symlink() for path in children):
            raise RuntimeError("continuation parent source directory is malformed")
        retained.extend([report, *(path / "reports" for path in children)])
        start = json.loads((report / "campaign-start.json").read_text())
        scratch.extend(Path(value) for value in start["scratch_roots"])
    for path in scratch:
        if (not path.is_absolute() or ".." in path.parts or path.resolve(strict=False) != path
                or not (any(path.is_relative_to(sources) for sources in source_roots)
                or (path.parent == PYSA_TMP_ROOT and path.name.startswith("dfb-v092-pysa-")))):
            raise RuntimeError("continuation parent scratch path leaves its registered namespace")
    return source_roots, list(dict.fromkeys(retained)), list(dict.fromkeys(scratch))


def _coverage(plan: dict) -> dict:
    ready_cold = [group for group in _ready_groups(plan) if group.get("kind") == "cold"]
    families = sorted({group["family"] for group in ready_cold})
    missing = sorted(set(FAMILIES) - set(families))
    cold = [group for group in plan["groups"] if group.get("kind") == "cold"]
    return {"planned_cold_groups": len(cold), "ready_cold_groups": len(ready_cold),
            "blocked_cold_groups": len(cold) - len(ready_cold),
            "ready_analyzer_families": families, "missing_analyzer_families": missing,
            "all_84_cold_groups_ready": len(ready_cold) == SOURCE_GROUPS,
            "full_coverage_claimed": False}


def _verify_frozen_group_membership(plan: dict, source_plan: dict, contract: dict) -> None:
    source_groups = {group["id"]: group for group in source_plan["groups"] if group.get("kind") == "cold"}
    frozen_groups = {group["id"]: group for group in contract["groups"]}
    cold_groups = [group for group in plan["groups"] if group.get("kind") == "cold"]
    mappings = _rebindings({"path_rebindings": plan.get("path_rebindings", {})})
    if ([group["id"] for group in source_plan["groups"] if group.get("kind") == "cold"]
            != plan["source_cold_group_order"]):
        raise RuntimeError("bound source cold-group order differs")
    if {group["id"] for group in cold_groups} != set(source_groups) or set(source_groups) != set(frozen_groups):
        raise RuntimeError("cold-group membership differs from the frozen contract or source plan")
    for group in cold_groups:
        source = source_groups[group["id"]]
        frozen = frozen_groups[group["id"]]
        if (group.get("family") != source.get("family") or group.get("family") != frozen.get("family")
                or group.get("case_ids") != source.get("case_ids")
                or group.get("case_ids") != frozen.get("case_ids")
                or group.get("reports") != source.get("reports")
                or group.get("output_roots") != source.get("output_roots")
                or group.get("deadline_seconds") != source.get("deadline_seconds")
                or group.get("deadline_seconds") != frozen.get("deadline_seconds")):
            raise RuntimeError(f"plan changed frozen case/report membership: {group['id']}")
        if len(group["reports"]) != len(frozen.get("reports", [])):
            raise RuntimeError(f"plan report count differs from frozen contract: {group['id']}")
        for descriptor, frozen_descriptor in zip(group["reports"], frozen["reports"]):
            for key in ("case_ids", "ordinal", "path", "tool"):
                if descriptor.get(key) != frozen_descriptor.get(key):
                    raise RuntimeError(f"plan report {key} differs from frozen contract: {group['id']}")
        canonical_argv = frozen["argv"] if group["id"] in SWIFT_WRAPPERS else source["argv"]
        if _rewrite_value(canonical_argv, mappings) != group.get("argv"):
            raise RuntimeError(f"plan changed frozen command arguments: {group['id']}")
        actual_environment = group.get("environment", {})
        if not isinstance(actual_environment, dict):
            raise RuntimeError(f"plan group environment is malformed: {group['id']}")
        reviewed_keys = {"JAVA_HOME", "PATH", "CC", "CXX", "SDKROOT", "GOTOOLCHAIN",
                         "RUSTUP_TOOLCHAIN", "CARGO_NET_OFFLINE"}
        deltas = {key: value for key, value in actual_environment.items() if key in reviewed_keys}
        expected_environment = _environment_with_reviewed_overrides(
            source.get("environment", {}), deltas, mappings, group["id"])
        if actual_environment != expected_environment:
            raise RuntimeError(f"plan changed protected environment settings: {group['id']}")


def _preparation_receipts(root: Path, plan: dict) -> list[dict]:
    binding = plan["runtime_bindings"]
    path = _path(root, binding["path"])
    if not path.is_file() or path.is_symlink() or sha(path) != binding["sha256"]:
        raise RuntimeError("bound runtime bindings file is missing or changed")
    receipts = json.loads(path.read_text()).get("preparation_receipts", [])
    if not isinstance(receipts, list):
        raise RuntimeError("preparation_receipts must be a list")
    for item in receipts:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeError("preparation receipt binding is malformed")
        relative = PurePosixPath(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("preparation receipt path must remain repository-relative")
        _validate_sha(item.get("sha256"), "preparation receipt SHA-256")
        receipt = root / Path(*relative.parts)
        if not receipt.is_file() or receipt.is_symlink() or sha(receipt) != item["sha256"]:
            raise RuntimeError(f"bound preparation receipt is missing or changed: {relative}")
    return receipts


def verify_plan(plan_path: Path, require_ready: bool = False) -> dict:
    plan_path = Path(plan_path)
    if not plan_path.is_absolute():
        plan_path = ROOT / plan_path
    if not plan_path.is_file() or plan_path.is_symlink():
        raise RuntimeError(f"plan is missing or not a regular file: {plan_path}")
    plan = json.loads(plan_path.read_text())
    _validate_plan_shape(plan)
    checkpoint = _continuation_checkpoint(plan)
    execution_authorized = _execution_authorization_ok(plan)
    report, _ = legacy.campaign_paths(plan["campaign_id"])
    if not plan_path.resolve(strict=False).is_relative_to(report.resolve()):
        raise RuntimeError("plan must be stored inside its new campaign report directory")
    source_ref = plan.get("source_plan", {})
    source_path = _path(ROOT, source_ref.get("path", ""))
    if not source_path.is_file() or sha(source_path) != source_ref.get("sha256"):
        raise RuntimeError("bound source plan file is missing or changed")
    bindings_path = _path(ROOT, plan["runtime_bindings"]["path"])
    if not bindings_path.is_file() or sha(bindings_path) != plan["runtime_bindings"]["sha256"]:
        raise RuntimeError("bound runtime bindings file is missing or changed")
    preparation_receipts = _preparation_receipts(ROOT, plan)
    preregistration = plan.get("preregistration")
    if preregistration is not None:
        prereg_path = _path(ROOT, preregistration["path"])
        if not prereg_path.is_file() or sha(prereg_path) != preregistration["sha256"]:
            raise RuntimeError("bound preregistration file is missing or changed")
    contract = plan.get("frozen_execution_contract", {})
    contract_path = _path(ROOT, contract.get("path", ""))
    if not contract_path.is_file() or sha(contract_path) != contract.get("sha256"):
        raise RuntimeError("bound frozen execution contract file is missing or changed")
    source_plan = json.loads(source_path.read_text())
    frozen_contract = json.loads(contract_path.read_text())
    _verify_frozen_group_membership(plan, source_plan, frozen_contract)
    for relative, expected in plan.get("execution_helpers", {}).items():
        helper_path = _path(ROOT, relative)
        if not helper_path.is_file() or helper_path.is_symlink() or sha(helper_path) != expected:
            raise RuntimeError(f"bound execution helper is missing or changed: {relative}")
    for group_id, reports in plan["frozen_report_bindings"].items():
        for item in reports:
            _git_path, raw = _frozen_report_blob(ROOT, item["contract_path"])
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise RuntimeError(f"frozen report bytes differ from release commit: {group_id}")
            expected_report = json.loads(raw)
            expected_identity = {key: expected_report.get(key) for key in (
                "tool", "tool_version", "tool_build_identity", "configuration_hash",
                "fixture_revision", "cold_or_warm", "adapter_version", "schema_version")}
            if item["identity"] != expected_identity or item["git_path"] != _git_path:
                raise RuntimeError(f"frozen report identity differs from its bound bytes: {group_id}")
    ready = _ready_groups(plan)
    for group in ready:
        for setup in group.get("setup_files", []):
            origin = Path(setup["source"])
            if not origin.is_file() or origin.is_symlink() or sha(origin) != setup["sha256"]:
                raise RuntimeError(f"setup file source is missing or changed: {origin}")
    coverage = _coverage(plan)
    if require_ready and coverage["missing_analyzer_families"]:
        raise RuntimeError("execute requires at least one ready cold group for every analyzer; missing: "
                           + ", ".join(coverage["missing_analyzer_families"]))
    tool_names = {"runner"}
    for group in ready:
        tool_names.add(group["family"])
        if group["family"] not in plan["tools"]:
            raise RuntimeError(f"ready group lacks tool binding {group['family']}: {group['id']}")
    tool_receipts = [_check_tool(plan["tools"][name], name) for name in sorted(tool_names)]
    runtimes_by_id = {item["id"]: item for item in plan["runtimes"]}
    required_ids = set()
    for group in ready:
        group_runtime_ids = set(group["runtime_ids"])
        unknown = group_runtime_ids - set(runtimes_by_id)
        if unknown:
            raise RuntimeError(f"ready group references missing runtime manifests {sorted(unknown)}: {group['id']}")
        required_ids |= group_runtime_ids
    runtime_receipts = []
    for runtime_id in sorted(required_ids):
        _raw, compressed_hash, uncompressed_hash = _manifest_bytes(runtimes_by_id[runtime_id])
        runtime_receipts.append({"id": runtime_id, "path": runtimes_by_id[runtime_id]["path"],
                                 "sha256": compressed_hash, "uncompressed_sha256": uncompressed_hash})
    return {"plan": str(plan_path), "campaign_id": plan["campaign_id"],
            "execution_authorized": execution_authorized,
            "ready_groups": len(ready), "blocked_groups": len(plan["groups"]) - len(ready),
            "continuation": None if checkpoint is None else {
                "parent_campaign_id": checkpoint["parent_campaign_id"],
                "inherited_candidate_groups": checkpoint["completed_groups"],
                "dispatch_groups": checkpoint["remaining_ready_groups"],
            },
            "coverage": coverage, "tools_verified": tool_receipts,
            "runtime_manifests_verified": runtime_receipts,
            "preparation_receipts_verified": preparation_receipts,
            "launch_after_utc": plan["launch_after_utc"], "require_ready": require_ready}


def _committed_bytes(root: Path, relative: str) -> bytes:
    if PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
        raise RuntimeError(f"committed input path must remain repository-relative: {relative}")
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"execution input is not present at HEAD: {relative}") from exc


def _assert_committed_inputs(root: Path, plan_path: Path, plan: dict) -> dict:
    relative_plan = plan_path.resolve().relative_to(root.resolve()).as_posix()
    expected = dict(plan.get("execution_helpers", {}))
    expected[relative_plan] = sha(plan_path)
    source_ref = plan["source_plan"]
    expected[source_ref["path"]] = source_ref["sha256"]
    bindings = plan["runtime_bindings"]
    expected[bindings["path"]] = bindings["sha256"]
    for receipt in _preparation_receipts(root, plan):
        expected[receipt["path"]] = receipt["sha256"]
    if plan.get("preregistration") is not None:
        preregistration = plan["preregistration"]
        expected[preregistration["path"]] = preregistration["sha256"]
    contract = plan["frozen_execution_contract"]
    expected[contract["path"]] = contract["sha256"]
    checkpoint = _continuation_checkpoint(plan)
    if checkpoint is not None:
        reference = plan["continuation"]
        expected[reference["path"]] = reference["sha256"]
        module = _load_module("qualified_timing_checkpoint_inputs", root / _checkpoint_helper(plan))
        for item in module.input_references(checkpoint):
            expected[item["path"]] = item["sha256"]
    if plan.get("execution_authorization") is not None:
        reference = plan["execution_authorization"]
        expected[reference["path"]] = reference["sha256"]
    for relative, digest in expected.items():
        committed = _committed_bytes(root, relative)
        actual = hashlib.sha256(committed).hexdigest()
        working = sha(root / relative)
        if actual != digest or working != digest:
            raise RuntimeError(f"execution input differs from committed and planned bytes: {relative}")
    return {"plan_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "committed_inputs": expected}


def wait_fresh_quiet(host, observer, destination: Path, deadline: float, capacity_check=None) -> dict:
    """Wait for a new full quiet window, bounded by the campaign wall window."""
    window = host.QuietWindow()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CampaignWindowEnded("campaign wall window ended while waiting for a quiet window")
        if capacity_check is not None:
            capacity_check()
        try:
            observation = observer.snapshot()
            if observation["disk_free_bytes"] < 127 * GIB:
                raise legacy.CampaignStop("launch disk floor lost")
            qualified = window.observe(observation, allowed_pids=observation["quiescent_service_pids"])
            observation["phase"] = "settle-before-group"
            observation["quiet_elapsed_seconds"] = window.elapsed_seconds
            legacy.append(destination, observation)
            if qualified:
                return observation
        except (host.HostObservationError, OSError, subprocess.SubprocessError, ValueError) as exc:
            legacy.append(destination, host.failure_record(exc))
            window.reset()
        time.sleep(min(host.SAMPLE_INTERVAL_SECONDS, max(0.0, deadline - time.monotonic())))


def _runtime_receipts(plan: dict, group: dict) -> list[dict]:
    runtimes = {item["id"]: item for item in plan["runtimes"]}
    receipts = []
    for runtime_id in group["runtime_ids"]:
        binding = runtimes.get(runtime_id)
        if binding is None:
            raise RuntimeError(f"runtime manifest is unbound for group {group['id']}: {runtime_id}")
        _raw, compressed_hash, uncompressed_hash = _manifest_bytes(binding)
        receipts.append({"id": runtime_id, "path": binding["path"], "sha256": compressed_hash,
                         "uncompressed_sha256": uncompressed_hash})
    return receipts


def compare_frozen_report_bytes(plan: dict, group: dict, source: Path) -> dict:
    """Compare analyzer/tool/configuration identity and every per-case outcome."""
    expected_bindings = plan["frozen_report_bindings"].get(group["id"], [])
    if len(expected_bindings) != len(group.get("reports", [])):
        raise FrozenComparisonError("frozen report binding count differs from group reports",
                                   {"status": "incomplete", "group": group["id"], "reports": []})
    receipts = []
    identity_fields = ("tool", "tool_version", "tool_build_identity", "configuration_hash",
                       "fixture_revision", "cold_or_warm", "adapter_version", "schema_version")
    for descriptor, binding in zip(group["reports"], expected_bindings):
        expected_git_path, expected_raw = _frozen_report_blob(ROOT, descriptor["path"])
        expected_sha = hashlib.sha256(expected_raw).hexdigest()
        if expected_git_path != binding["git_path"] or expected_sha != binding["sha256"]:
            raise FrozenComparisonError("frozen report bytes no longer match the qualified plan",
                                       {"status": "incomplete", "group": group["id"], "reports": receipts})
        expected = json.loads(expected_raw)
        actual_path = source / descriptor["source_path"]
        if not actual_path.is_file():
            raise FrozenComparisonError(f"measured report is missing: {actual_path}",
                                       {"status": "incomplete", "group": group["id"], "reports": receipts})
        actual_raw = actual_path.read_bytes()
        actual = json.loads(actual_raw)
        mismatches = []
        for field in identity_fields:
            if field not in expected or field not in actual:
                mismatches.append({"field": field, "classification": "incomplete"})
            elif actual[field] != expected[field]:
                mismatches.append({"field": field, "classification": "mismatch",
                                   "expected": expected[field], "actual": actual[field]})
        expected_rows = {row.get("case_id"): row for row in expected.get("results", [])}
        actual_rows = {row.get("case_id"): row for row in actual.get("results", [])}
        if (None in expected_rows or None in actual_rows
                or set(expected_rows) != set(actual_rows)
                or len(expected_rows) != len(expected.get("results", []))
                or len(actual_rows) != len(actual.get("results", []))):
            mismatches.append({"field": "case_population", "classification": "incomplete",
                               "expected_count": len(expected_rows), "actual_count": len(actual_rows)})
        for case_id in sorted(set(expected_rows) & set(actual_rows)):
            expected_outcome = expected_rows[case_id].get("outcome")
            actual_outcome = actual_rows[case_id].get("outcome")
            if expected_outcome is None or actual_outcome is None:
                mismatches.append({"case_id": case_id, "field": "outcome", "classification": "incomplete"})
            elif expected_outcome != actual_outcome:
                mismatches.append({"case_id": case_id, "field": "outcome", "classification": "mismatch",
                                   "expected": expected_outcome, "actual": actual_outcome})
        receipt = {"contract_path": descriptor["path"], "release_git_path": binding["git_path"],
                   "frozen_sha256": expected_sha,
                   "measured_sha256": hashlib.sha256(actual_raw).hexdigest(),
                   "identity_fields_compared": list(identity_fields),
                   "case_outcomes_compared": len(set(expected_rows) & set(actual_rows)),
                   "mismatches": mismatches}
        receipts.append(receipt)
        if mismatches:
            classifications = {item["classification"] for item in mismatches}
            state = "mismatch" if "mismatch" in classifications else "incomplete"
            full_receipt = {"status": state, "group": group["id"], "reports": receipts}
            raise FrozenComparisonError(
                f"measured report {state} against frozen v0.9.2 identity/outcomes: {descriptor['source_path']}",
                full_receipt)
    return {"status": "matched", "group": group["id"], "reports": receipts,
            "comparison_scope": "listed report identity fields and per-case outcomes; diagnostics, anchors and raw semantic evidence still require independent review",
            "timing_fields_excluded": ["started_at_unix_seconds", "ended_at_unix_seconds", "duration_ms"],
            "publication_eligible": False}


def validate_warm_artifact(plan: dict, group: dict, source: Path) -> dict:
    """Validate every planned warm batch and its retained case evidence."""
    root_relative = group["output_roots"][0]
    raw_root = source / root_relative
    artifact_path = raw_root / "warm-latency.json"
    if not artifact_path.is_file():
        raise RuntimeError(f"warm-latency artifact is missing: {artifact_path}")
    raw = artifact_path.read_bytes()
    artifact = json.loads(raw)
    family = group["family"]
    if artifact.get("schema_version") != 1:
        raise RuntimeError("warm-latency artifact schema_version differs")
    if artifact.get("evidence_kind") != "retained-warm-marginal-latency":
        raise RuntimeError("warm-latency artifact evidence_kind differs")
    if artifact.get("adapter") != family or artifact.get("language") != "java":
        raise RuntimeError("warm-latency artifact adapter or language differs")
    if artifact.get("repeats") != 2:
        raise RuntimeError("warm-latency artifact must retain exactly two repeats")
    case_ids = group["warm_case_ids"]
    if artifact.get("population_available") != len(case_ids):
        raise RuntimeError("warm-latency population size differs from its bound case IDs")
    for field in ("tool_version", "tool_build_identity", "fixture_revision"):
        if not isinstance(artifact.get(field), str) or not artifact[field]:
            raise RuntimeError(f"warm-latency artifact lacks {field}")
    family_identity = _frozen_family_identity(plan, family, "java")
    for field in ("tool_version", "tool_build_identity", "fixture_revision"):
        expected = plan["fixture_revision"] if field == "fixture_revision" else family_identity[field]
        if artifact[field] != expected:
            raise RuntimeError(f"warm-latency {field} differs from frozen {family} identity")
    runs = artifact.get("runs")
    sizes = group["warm_batch_sizes"]
    if not isinstance(runs, list) or len(runs) != 2:
        raise RuntimeError("warm-latency artifact must retain two run records")
    retained_files = 0
    for repeat, run in enumerate(runs, start=1):
        if not isinstance(run, dict) or run.get("run") != repeat:
            raise RuntimeError("warm-latency run numbering differs")
        batches = run.get("batches")
        if not isinstance(batches, list) or len(batches) != len(sizes):
            raise RuntimeError(f"warm-latency run {repeat} has incomplete batch records")
        for batch, size in zip(batches, sizes):
            if not isinstance(batch, dict) or batch.get("k") != size:
                raise RuntimeError(f"warm-latency run {repeat} batch sizes differ")
            wall = batch.get("wall_ms")
            if type(wall) is not int or wall < 0:
                raise RuntimeError(f"warm-latency run {repeat} batch wall_ms is malformed")
            if batch.get("case_ids") != case_ids[:size]:
                raise RuntimeError(f"warm-latency run {repeat} batch {size} is not the bound case prefix")
            evidence_dir = raw_root / f"run-{repeat}-batch-{size}-evidence"
            expected_names = {case_id + ".json" for case_id in case_ids[:size]}
            if not evidence_dir.is_dir() or evidence_dir.is_symlink():
                raise RuntimeError(f"warm per-case evidence directory is missing: {evidence_dir}")
            children = list(evidence_dir.iterdir())
            if any(path.is_symlink() or not path.is_file() for path in children):
                raise RuntimeError(f"warm per-case evidence contains a non-regular entry: {evidence_dir}")
            actual_names = {path.name for path in children}
            if actual_names != expected_names:
                raise RuntimeError(f"warm per-case evidence membership differs: {evidence_dir}")
            for name in sorted(expected_names):
                path = evidence_dir / name
                try:
                    evidence = json.loads(path.read_text())
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"warm per-case evidence is invalid: {path}") from exc
                if not isinstance(evidence, dict):
                    raise RuntimeError(f"warm per-case evidence must be a JSON object: {path}")
            retained_files += len(expected_names)
    return {"kind": "warm", "status": "candidate", "artifact": str(artifact_path),
            "sha256": hashlib.sha256(raw).hexdigest(), "repeats": 2,
            "batch_sizes": sizes, "case_count": len(case_ids),
            "retained_per_case_evidence_files": retained_files,
            "equivalence_pending": True,
            "equivalence_status": "pending comparison against corresponding cold evidence",
            "publication_eligible": False}


def _frozen_family_identity(plan: dict, family: str, language: str, *, overhead: bool = False) -> dict:
    by_id = {group["id"]: group for group in plan["groups"] if group.get("kind") == "cold"}
    candidates = []
    for group_id, group in by_id.items():
        if group_id != f"{family}-{language}-kernel" or group.get("family") != family:
            continue
        for report in plan["frozen_report_bindings"].get(group_id, []):
            identity = report["identity"]
            candidates.append(identity)
    if not candidates:
        raise RuntimeError(f"no frozen {family}/{language} kernel identity is bound for the auxiliary arm")
    fields = ("tool", "tool_version", "tool_build_identity", "fixture_revision")
    reference = {key: candidates[0].get(key) for key in fields}
    if any({key: value.get(key) for key in fields} != reference for value in candidates[1:]):
        raise RuntimeError(f"frozen kernel identity is inconsistent: {family}/{language}")
    if reference["tool"] != family or reference["fixture_revision"] != plan.get("fixture_revision"):
        raise RuntimeError(f"frozen family identity differs from plan fixture/tool: {family}")
    if overhead and family == "flowdroid":
        # The frozen A24 implementation calls witness_flowdroid_identity,
        # whereas cold kernels append the separately witnessed D8 translator.
        # D8 remains bound by this campaign's full runtime and explicit argv.
        base, separator, _d8 = reference["tool_build_identity"].partition("; dexed by ")
        if not separator:
            raise RuntimeError("frozen FlowDroid Java identity lacks the expected D8 materialization suffix")
        reference["tool_build_identity"] = base
        reference["identity_scope"] = "A24 analyzer/platform witness; D8 is separately runtime-bound"
    return reference


def validate_overhead_artifact(plan: dict, group: dict, source: Path) -> dict:
    family, language = _overhead_args(group, plan["tools"])
    raw_root = source / group["output_roots"][0]
    artifact_path = raw_root / "invocation-overhead.json"
    if not artifact_path.is_file():
        raise RuntimeError(f"invocation-overhead artifact is missing: {artifact_path}")
    raw = artifact_path.read_bytes()
    artifact = json.loads(raw)
    if artifact.get("schema_version") != 1:
        raise RuntimeError("invocation-overhead artifact schema_version differs")
    if artifact.get("evidence_kind") != "retained-invocation-overhead-estimate" \
            or artifact.get("amendment") != "A24":
        raise RuntimeError("invocation-overhead artifact does not carry the A24 evidence kind")
    if artifact.get("adapter") != family or artifact.get("language") != language:
        raise RuntimeError("invocation-overhead artifact adapter/language differs from its group")
    if artifact.get("repeats") != 3:
        raise RuntimeError("invocation-overhead artifact must retain exactly three repeats")
    runs = artifact.get("runs")
    if not isinstance(runs, list) or len(runs) != 3:
        raise RuntimeError("invocation-overhead artifact must retain three run records")
    for repeat, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            raise RuntimeError("invocation-overhead run record is malformed")
        wall = run.get("wall_ms")
        if run.get("repeat") != repeat or type(wall) not in (int, float) \
                or not math.isfinite(wall) or wall < 0:
            raise RuntimeError("invocation-overhead run repeat or wall_ms is malformed")
    fixture_file = artifact.get("fixture_file")
    if not isinstance(fixture_file, str):
        raise RuntimeError("invocation-overhead artifact lacks fixture_file")
    fixture_relative = PurePosixPath(fixture_file)
    if fixture_relative.is_absolute() or ".." in fixture_relative.parts:
        raise RuntimeError("invocation-overhead fixture path escapes its artifact root")
    fixture_path = raw_root / Path(*fixture_relative.parts)
    fixture_hash = _validate_sha(artifact.get("fixture_sha256"), "invocation-overhead fixture_sha256")
    if not fixture_path.is_file() or fixture_path.is_symlink() or sha(fixture_path) != fixture_hash:
        raise RuntimeError("invocation-overhead retained fixture is missing or its hash differs")
    identity = _frozen_family_identity(plan, family, language, overhead=True)
    for field in ("tool_version", "tool_build_identity"):
        if artifact.get(field) != identity[field]:
            raise RuntimeError(f"invocation-overhead {field} differs from frozen {family} reports")
    environment_path = raw_root / "run-environment.json"
    if not environment_path.is_file() or environment_path.is_symlink():
        raise RuntimeError("invocation-overhead run-environment witness is missing")
    environment = json.loads(environment_path.read_text())
    if (environment.get("schema_version") != 1
            or environment.get("evidence_kind") != "retained-run-environment"
            or environment.get("tool") != family
            or environment.get("witnessed_tool_version") != artifact.get("tool_version")
            or environment.get("witnessed_tool_build_identity") != artifact.get("tool_build_identity")):
        raise RuntimeError("invocation-overhead run-environment identity differs from its artifact")
    return {"kind": "overhead", "status": "candidate", "artifact": str(artifact_path),
            "sha256": hashlib.sha256(raw).hexdigest(), "repeats": 3, "fixture_file": str(fixture_path),
            "fixture_sha256": fixture_hash, "fixture_revision": plan["fixture_revision"],
            "frozen_family_identity": identity, "environment_identity_verified": True,
            "publication_eligible": False}


def _tool_receipts(plan: dict, group: dict) -> list[dict]:
    return [_check_tool(plan["tools"][name], name) for name in sorted({"runner", group["family"]})]


def _campaign_artifacts_absent(report: Path) -> None:
    for path in (report / "campaign-start.json", report / "campaign-terminal.json",
                 report / "progress.jsonl", report / "preparation-progress.jsonl", report / "attempts"):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"campaign output already exists; explicit review required: {path}")


def _assert_prepared_source(plan: dict, source: Path) -> dict:
    legacy.core._assert_source_snapshot(source, RELEASE)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if head != RELEASE:
        raise RuntimeError("prepared source HEAD differs from the immutable release")
    extra = plan["source_projection"].get("additional_paths", [])
    if extra:
        subprocess.run(["git", "diff", "--quiet", RELEASE, "--", *extra], cwd=source, check=True)
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *extra],
            cwd=source, text=True)
        if dirty.strip():
            raise RuntimeError("prepared qualification inputs changed")
    return {"source_commit": RELEASE, "snapshot_git_head": head, "source_and_fixture_inputs_unchanged": True}


def _execute(plan_path: Path) -> dict:
    plan_path = Path(plan_path)
    if not plan_path.is_absolute():
        plan_path = ROOT / plan_path
    if not plan_path.is_file() or plan_path.is_symlink():
        raise RuntimeError(f"plan is missing or not a regular file: {plan_path}")
    plan = json.loads(plan_path.read_text())
    _validate_plan_shape(plan)
    launch_after = _utc(plan["launch_after_utc"], "launch_after_utc")
    current = dt.datetime.now(dt.timezone.utc)
    if current < launch_after:
        raise RuntimeError(f"launch is not authorized before {launch_after.isoformat()}")
    if not _execution_authorization_ok(plan):
        raise RuntimeError("execution window has not been authorized; preparation only")
    report, work = legacy.select_campaign(plan["campaign_id"])
    if not plan_path.resolve(strict=False).is_relative_to(report.resolve()):
        raise RuntimeError("plan must be stored inside its new campaign report directory")
    _campaign_artifacts_absent(report)
    committed = _assert_committed_inputs(ROOT, plan_path, plan)
    ready = _dispatch_groups(plan)
    if not ready:
        raise RuntimeError("no ready commands are bound")
    checkpoint = _continuation_checkpoint(plan)
    inherited = [] if checkpoint is None else checkpoint["completed_groups"]
    inherited_quarantined = [] if checkpoint is None else checkpoint.get("quarantined_groups", [])

    host = _load_module("qualified_timing_host", ROOT / "scripts/v092_timing_host.py")
    observer = legacy.Observer(host)
    max_wall = plan["max_campaign_wall_seconds"]
    campaign_started = time.monotonic()
    campaign_deadline = campaign_started + max_wall
    source_guard = legacy.disk.DiskGuard(launch_floor_bytes=127 * GIB, stop_floor_bytes=125 * GIB,
                                         working_ceiling_bytes=30 * GIB)
    sources = work / "sources"
    inherited_sources, inherited_retained, inherited_scratch = _inherited_resource_paths(checkpoint)
    working_paths = [sources, *inherited_sources]
    setup_receipts = {}
    prepared_environments = {}
    external_scratch = {}
    source_projection = plan["source_projection"]
    if source_projection.get("commit") != RELEASE:
        raise RuntimeError("source projection does not name the frozen release commit")

    with legacy.core._exclusive_lock():
        verified = verify_plan(plan_path, require_ready=True)
        _campaign_artifacts_absent(report)
        for parent_sources in inherited_sources:
            for parent_source in parent_sources.iterdir():
                if legacy.core._tree_bytes([parent_source]) > 12 * GIB:
                    raise RuntimeError("inherited source exceeds the 12 GiB per-source ceiling")
        source_guard.check(category="working", paths=working_paths, capacity_path=ROOT, phase="launch")
        source_guard.check(category="retention", paths=[report, *inherited_retained], capacity_path=ROOT, phase="launch")
        source_guard.check(category="scratch", paths=inherited_scratch, capacity_path=ROOT, phase="launch")
        tracker = legacy.core._process_tracker()
        supervisor_identity = tracker._start_identity(os.getpid())
        if supervisor_identity is None:
            raise RuntimeError("supervisor process identity preflight failed")
        for group in ready:
            source = sources / group["id"]
            if source.exists() or source.is_symlink():
                raise RuntimeError(f"source snapshot already exists; reviewed continuation required: {source}")
            legacy.append(report / "preparation-progress.jsonl", {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "group": group["id"],
                "phase": "source-materialization-starting", "source": str(source),
                "target_absence_observed": True, "analyzer_dispatched": False})
            explicit = subprocess.check_output([
                "git", "ls-tree", "-r", "--name-only", RELEASE, "--",
                *source_projection["additional_paths"]], cwd=ROOT, text=True).splitlines()
            projected = legacy.core._materialize_source(
                ROOT, RELEASE, source, explicit, disk_guard=source_guard,
                working_paths=working_paths, preflight_only=True)
            if projected > 12 * GIB:
                raise RuntimeError("source projection exceeds the 12 GiB per-source ceiling")
            legacy.core._materialize_source(
                ROOT, RELEASE, source, explicit, disk_guard=source_guard,
                working_paths=working_paths, expected_projected_bytes=projected)
            legacy.core._register_source_snapshot(ROOT, RELEASE, source)
            for directory in ("home", "tmp", "cache"):
                (source / directory).mkdir(exist_ok=True)
            setup_receipts[group["id"]] = _copy_setup_files(group, source)
            attempt_root = report / "attempts" / group["id"] / "attempt-01"
            environment = legacy.core._child_environment(group, source, attempt_root, source / "cache")
            ownership = _prepare_pysa_tmp(group, source, environment)
            if ownership is not None:
                external_scratch[group["id"]] = ownership
            prepared_environments[group["id"]] = environment

        scratch_paths = [*_campaign_scratch_paths(sources, ready, external_scratch), *inherited_scratch]
        retained_paths = [report, *inherited_retained, *[path / "reports" for path in sources.iterdir()]]

        report.mkdir(parents=True, exist_ok=True)
        legacy.write_new(report / "campaign-start.json", {
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "phase": "fresh-quiet-before-each-ready-command",
            "campaign_id": plan["campaign_id"],
            "supervisor_pid": os.getpid(),
            "supervisor_start_identity": supervisor_identity,
            "plan_sha256": sha(plan_path),
            "plan_commit": committed["plan_commit"],
            "source_commit": RELEASE,
            "ready_commands": len(ready),
            "planned_ready_commands": len(_ready_groups(plan)),
            "new_dispatch_cold_groups": sum(group["kind"] == "cold" for group in ready),
            "inherited_candidate_groups": inherited,
            "inherited_quarantined_groups": inherited_quarantined,
            "semantic_mismatch_policy": plan.get("semantic_mismatch_policy"),
            "continuation_checkpoint": plan.get("continuation"),
            "cumulative_resource_scope": {"working": [str(path) for path in working_paths],
                                          "retained": [str(path) for path in retained_paths]},
            "planned_cold_groups": SOURCE_GROUPS,
            "ready_cold_groups": verified["coverage"]["ready_cold_groups"],
            "blocked_cold_groups": verified["coverage"]["blocked_cold_groups"],
            "max_campaign_wall_seconds": max_wall,
            "execution_inputs": committed["committed_inputs"],
            "tools_verified_before_start": verified["tools_verified"],
            "runtime_manifests_verified_before_start": verified["runtime_manifests_verified"],
            "external_scratch_ownership": external_scratch,
            "scratch_roots": [str(path) for path in scratch_paths],
            "qualification_status": "unqualified",
            "descendant_containment": "unproven",
        })
        completed = []
        quarantined = []
        consumed_seconds = 0.0
        stopped_group = None
        wall_ended = False
        for index, group in enumerate(ready):
            destination = report / "attempts" / group["id"] / "attempt-01"
            destination.mkdir(parents=True, exist_ok=False)
            source = sources / group["id"]
            ownership = {}
            guard = legacy.ObservedGuard(host, observer, ownership, destination / "host.jsonl", source)
            attempt_started = dt.datetime.now(dt.timezone.utc).isoformat()
            command_clock = None
            command_elapsed_accounted = False
            record = {"group": group["id"], "argv": group["argv"], "started_utc": attempt_started,
                      "attempt": 1, "automatic_retry": False}
            try:
                pre_tools = _tool_receipts(plan, group)
                pre_runtimes = _runtime_receipts(plan, group)
                _verify_setup_files(group, source)
                source_before = _assert_prepared_source(plan, source)
                if time.monotonic() >= campaign_deadline:
                    raise CampaignWindowEnded("campaign wall window ended before dispatch")
                def check_waiting_capacity():
                    guard.check(category="retention", paths=retained_paths, capacity_path=ROOT)
                    guard.check(category="scratch", paths=scratch_paths, capacity_path=ROOT)
                    guard.check(category="working", paths=working_paths, capacity_path=ROOT)
                quiet = wait_fresh_quiet(host, observer, destination / "host.jsonl", campaign_deadline,
                                         capacity_check=check_waiting_capacity)
                guard.initial_quiet_gate_passed = True
                guard.settle_skipped = False
                guard.launch_check(source)
                guard.check(category="working", paths=working_paths, capacity_path=ROOT, phase="launch")
                if time.monotonic() >= campaign_deadline:
                    raise CampaignWindowEnded("campaign wall window ended before dispatch")
                environment = dict(prepared_environments[group["id"]])
                legacy.write_new(destination / "start.json", {
                    "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "argv": group["argv"], "environment": environment,
                    "deadline_seconds": group["deadline_seconds"],
                    "quiet_observation": quiet,
                    "quiet_policy": {"required_seconds": 300, "minimum_idle_percent": 90,
                                     "maximum_sample_gap_seconds": 60},
                    "tools_verified_before_dispatch": pre_tools,
                    "runtime_manifests_verified_before_dispatch": pre_runtimes,
                    "setup_file_receipts": setup_receipts.get(group["id"], []),
                    "source_verified_before_dispatch": source_before,
                    "external_scratch_ownership": external_scratch.get(group["id"]),
                    "plan_sha256": sha(plan_path),
                })
                legacy.append(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                              "group": group["id"], "status": "started"})
                print(f"STARTED {group['id']}", flush=True)
                command_clock = time.monotonic()
                code, timed_out, elapsed, capacity = legacy.core._run_process(
                    group["argv"], source, environment, destination / "stdout.txt", destination / "stderr.txt",
                    group["deadline_seconds"], disk_guard=guard,
                    retained_paths=retained_paths,
                    scratch_paths=scratch_paths,
                    scratch_limit=plan["resources"]["scratch_gib"] * GIB,
                    working_paths=working_paths, ownership=ownership)
                consumed_seconds += elapsed
                command_elapsed_accounted = True
                record.update(exit_code=code, timed_out=timed_out, elapsed_seconds=elapsed,
                              capacity_loss=capacity, execution_budget_consumed_seconds=consumed_seconds)
                post = guard.observe_background("after-analysis")
                if post.get("contention_observed"):
                    record["post_analysis_contention"] = post.get("contention")
                if not post.get("observation_available"):
                    record["post_analysis_observation_available"] = False
                post_tools = _tool_receipts(plan, group)
                post_runtimes = _runtime_receipts(plan, group)
                record["setup_files_verified_after_analysis"] = _verify_setup_files(group, source)
                record["source_verified_after_analysis"] = _assert_prepared_source(plan, source)
                record["tools_verified_after_observation"] = post_tools
                record["runtime_manifests_verified_after_observation"] = post_runtimes
                if code == 0 and not timed_out and capacity is None:
                    status = "completed-candidate-evidence"
                    if group.get("kind") == "cold":
                        record["reconciliation"] = legacy.reconcile(group, source)
                        try:
                            record["frozen_report_comparison"] = compare_frozen_report_bytes(plan, group, source)
                        except FrozenComparisonError as exc:
                            record["frozen_report_comparison"] = exc.receipt
                            if not _outcome_only_quarantine_allowed(plan, group, exc.receipt):
                                raise
                            status = "semantic-mismatch-quarantined"
                            record["error"] = f"{type(exc).__name__}: {exc}"
                            record["acceptance_blocked"] = True
                    elif group.get("kind") == "warm":
                        record["reconciliation"] = validate_warm_artifact(plan, group, source)
                    else:
                        record["reconciliation"] = validate_overhead_artifact(plan, group, source)
                else:
                    status = "failed"
                record["quiet_certification"] = guard.quiet_certification()
                record["process_ownership"] = ownership
                record["external_scratch_ownership"] = external_scratch.get(group["id"])
                record["descendant_containment"] = ownership.get("descendant_containment", "unproven")
                record["publication_eligible"] = False
                record["timing_qualification"] = (
                    "unqualified: frozen outcome mismatch; not accepted or retried"
                    if status == "semantic-mismatch-quarantined" else "unqualified pending independent review")
            except CampaignWindowEnded as exc:
                wall_ended = True
                stopped_group = group["id"]
                record.update(status="wall-window-ended", not_dispatched=True,
                              reason=str(exc), quiet_certification=guard.quiet_certification(),
                              descendant_containment="unproven", publication_eligible=False)
                legacy.write_new(destination / "terminal.json", record)
                legacy.append(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                              "group": group["id"], "status": "wall-window-ended"})
                break
            except BaseException as exc:
                if command_elapsed_accounted:
                    elapsed = record.get("elapsed_seconds", 0.0)
                elif command_clock is not None and (destination / "start.json").exists():
                    elapsed = max(0.0, time.monotonic() - command_clock)
                    consumed_seconds += elapsed
                    command_elapsed_accounted = True
                else:
                    elapsed = 0.0
                status = "failed"
                stopped_group = group["id"]
                record.update(error=f"{type(exc).__name__}: {exc}", elapsed_seconds=elapsed,
                              execution_budget_consumed_seconds=consumed_seconds,
                              not_dispatched=ownership.get("root_pid") is None,
                              quiet_certification=guard.quiet_certification(), process_ownership=ownership,
                              descendant_containment=ownership.get("descendant_containment", "unproven"),
                              publication_eligible=False,
                              timing_qualification="unqualified pending independent review")
                if isinstance(exc, FrozenComparisonError):
                    record["frozen_report_comparison"] = exc.receipt
            record.update(status=status, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                          host_active_observations=guard.active_observations,
                          host_observations=guard.observations,
                          host_observation_attempts=guard.observation_attempts)
            legacy.write_new(destination / "terminal.json", record)
            legacy.append(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                          "group": group["id"], "status": status})
            print(f"{status.upper()} {group['id']}", flush=True)
            if status == "semantic-mismatch-quarantined":
                quarantined.append(group["id"])
                continue
            if status != "completed-candidate-evidence":
                stopped_group = group["id"]
                break
            completed.append(group["id"])

        blocked = [group["id"] for group in plan["groups"] if group.get("status") == "blocked"]
        remaining_ready = [group["id"] for group in ready
                           if group["id"] not in [*completed, *quarantined]
                           and (wall_ended or group["id"] != stopped_group)]
        all_plan_groups_ready = not blocked
        if wall_ended:
            terminal_status = "wall-window-ended"
        elif stopped_group is not None:
            terminal_status = "unqualified"
        elif quarantined or inherited_quarantined:
            terminal_status = "unqualified"
        elif not completed:
            terminal_status = "blocked"
        elif all_plan_groups_ready:
            terminal_status = "completed"
        else:
            terminal_status = "unqualified"
        legacy.write_new(report / "campaign-terminal.json", {
            "status": terminal_status,
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "execution_status": "stopped" if stopped_group else "completed-ready-frontier",
            "completed_candidate_groups": completed,
            "completed_commands": len(completed),
            "inherited_candidate_groups": inherited,
            "inherited_candidate_commands": len(inherited),
            "inherited_quarantined_groups": inherited_quarantined,
            "quarantined_groups": quarantined,
            "combined_quarantined_groups": [*inherited_quarantined, *quarantined],
            "semantic_mismatch_policy": plan.get("semantic_mismatch_policy"),
            "combined_completed_candidate_commands": len(inherited) + len(completed),
            "new_completed_candidate_cold_groups": sum(
                group["kind"] == "cold" and group["id"] in completed for group in plan["groups"]),
            "combined_completed_candidate_cold_groups": sum(
                group["kind"] == "cold" and group["id"] in [*inherited, *completed]
                for group in plan["groups"]),
            "continuation_checkpoint": plan.get("continuation"),
            "ready_groups": len(ready),
            "blocked_groups": blocked,
            "planned_cold_groups": SOURCE_GROUPS,
            "ready_cold_groups": verified["coverage"]["ready_cold_groups"],
            "blocked_cold_groups": verified["coverage"]["blocked_cold_groups"],
            "full_84_group_coverage": len(completed) == SOURCE_GROUPS,
            "full_84_group_coverage_claimed": False,
            "remaining_ready_groups": remaining_ready,
            "remaining_ready_group_status": "wall-window-ended" if wall_ended else (
                "not-dispatched-after-fail-stop" if stopped_group else None),
            "stopped_group": stopped_group,
            "reason": "campaign wall window ended before the next dispatch" if wall_ended else (
                "fail-stop; no automatic retry" if stopped_group else None),
            "execution_budget_consumed_seconds": consumed_seconds,
            "execution_budget_seconds": plan["resources"]["total_execution_budget_seconds"],
            "qualification_status": "unqualified",
            "publication_eligible": False,
            "descendant_containment": "unproven",
            "resource_scope": "per-command stop guards were enforced; no global resource or external certification",
        })
        return {"status": terminal_status, "campaign_id": plan["campaign_id"],
                "completed_commands": len(completed), "blocked_groups": len(blocked),
                "stopped_group": stopped_group}


def execute(plan_path: Path) -> dict:
    """Retain failures around admission/setup as well as individual commands."""
    try:
        return _execute(plan_path)
    except BaseException as failure:
        try:
            path = _path(ROOT, str(plan_path))
            plan = json.loads(path.read_text())
            _validate_plan_shape(plan)
            report, work = legacy.campaign_paths(plan["campaign_id"])
            authorized = (dt.datetime.now(dt.timezone.utc) >= _utc(plan["launch_after_utc"], "launch_after_utc")
                          and _execution_authorization_ok(plan))
            if authorized and path.resolve().is_relative_to(report.resolve()):
                completed = []
                quarantined = []
                started = set()
                progress = report / "progress.jsonl"
                if progress.is_file():
                    for line in progress.read_text().splitlines():
                        row = json.loads(line)
                        if row.get("status") == "completed-candidate-evidence":
                            completed.append(row["group"])
                        elif row.get("status") == "semantic-mismatch-quarantined":
                            quarantined.append(row["group"])
                        elif row.get("status") == "started":
                            started.add(row["group"])
                dispatch_proven = False
                retained_terminals = {}
                by_id = {group["id"]: group for group in _groups(plan)}
                for terminal in (report / "attempts").glob("*/attempt-01/terminal.json"):
                    value = json.loads(terminal.read_text())
                    dispatch_proven |= value.get("process_ownership", {}).get("root_pid") is not None
                    group_id = value.get("group")
                    if group_id not in by_id or group_id != terminal.parent.parent.name:
                        continue
                    retained_terminals[group_id] = value.get("status")
                    if value.get("status") == "completed-candidate-evidence":
                        completed.append(group_id)
                    elif (value.get("status") == "semantic-mismatch-quarantined"
                          and _outcome_only_quarantine_allowed(
                              plan, by_id[group_id], value.get("frozen_report_comparison", {}))):
                        quarantined.append(group_id)
                order = {group["id"]: index for index, group in enumerate(plan["groups"])}
                completed = sorted(set(completed) - set(quarantined), key=lambda key: order[key])
                quarantined = sorted(set(quarantined), key=lambda key: order[key])
                try:
                    frontier = [group["id"] for group in _dispatch_groups(plan)]
                except Exception:
                    # Admission failure must remain recordable when the checkpoint
                    # itself is unavailable or no longer verifies.
                    frontier = None
                record = {
                    "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "campaign_id": plan["campaign_id"], "plan_sha256": sha(path),
                    "error": f"{type(failure).__name__}: {failure}",
                    "campaign_start_record_exists": (report / "campaign-start.json").exists(),
                    "analyzer_dispatch_proven": dispatch_proven,
                    "completed_groups": completed, "completed_commands": len(completed),
                    "quarantined_groups": quarantined,
                    "retained_terminal_statuses": retained_terminals,
                    "started_without_terminal": sorted(started - set(retained_terminals)),
                    "remaining_ready_groups": None if frontier is None else [
                        group_id for group_id in frontier
                        if group_id not in set(completed) | set(quarantined) | started | set(retained_terminals)],
                    "continuation_frontier_verified": frontier is not None,
                    "blocked_groups": [{"id": g["id"], "reason": g["blocker"]}
                                       for g in plan["groups"] if g["status"] == "blocked"],
                    "source_namespace": str(work / "sources"),
                    "partial_setup_retained": True, "automatic_retry": False,
                    "publication_eligible": False, "qualification_status": "unqualified",
                    "descendant_containment": "unproven",
                }
                for number in range(1, 1000):
                    target = report / f"launch-failure-{number:03d}.json"
                    if not target.exists() and not target.is_symlink():
                        legacy.write_new(target, record)
                        break
                terminal = report / "campaign-terminal.json"
                if not terminal.exists() and not terminal.is_symlink():
                    legacy.write_new(terminal, {
                        **record, "status": "unqualified" if dispatch_proven else "blocked",
                        "execution_status": "stopped-with-controller-error",
                        "phase": "dispatch-preparation" if record["campaign_start_record_exists"] else "admission-or-source-setup",
                        "reason": "controller failure; partial evidence retained; explicit review required",
                    })
        except Exception as receipt_failure:
            print(f"Could not retain launch failure receipt: {receipt_failure}", file=sys.stderr)
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--bindings", required=True, type=Path)
    prepare_parser.add_argument("--output", required=True, type=Path)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--plan", required=True, type=Path)
    verify_parser.add_argument("--require-ready", action="store_true")
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.mode == "prepare":
            result = prepare(args.bindings, args.output)
        elif args.mode == "verify":
            result = verify_plan(args.plan, require_ready=args.require_ready)
        else:
            result = execute(args.plan)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
