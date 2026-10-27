#!/usr/bin/env python3
"""Bind exact retained v0.9.0 tool controls to v0.9.2 tool identities.

This creates group-level execution eligibility receipts only. It never copies
or promotes a v0.9.0 normal report as a v0.9.2 result.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDINGS = ROOT / "execution-state/v092/bindings-draft-01.json"
DEFAULT_OUTPUT_DIR = ROOT / "reports/releases/v0.9.2/qualification/retained-v090-02"
V090_EXEC = Path("reports/releases/v0.9.0/execution-v1")
V090_RESUME = V090_EXEC / "resume-20261007-05"

TOOL_GROUPS = {
    "infer": (
        "infer-c-kernel",
        "infer-cpp-kernel",
        "infer-java-kernel",
        "infer-java-modeling",
        "infer-java-native",
    ),
    "flowdroid": (
        "flowdroid-java-kernel",
        "flowdroid-java-modeling",
        "flowdroid-java-native",
        "flowdroid-kotlin-kernel",
    ),
    "opentaint": (
        "opentaint-java-kernel",
        "opentaint-java-modeling",
        "opentaint-java-native",
        "opentaint-kotlin-kernel",
    ),
}

TOOL_CONTROLS = {
    "infer": (
        "probe-infer-modeling-partition",
        "probe-infer-native-activation",
        "probe-infer-native-silence",
    ),
    "flowdroid": (
        "probe-flowdroid-modeling-load-bearing",
        "probe-flowdroid-native-shipped-surface",
    ),
    "opentaint": (
        "probe-opentaint-modeling-surface",
        "probe-opentaint-native-activation",
        "probe-opentaint-scan-activation",
        "probe-opentaint-primitive-tracking",
        "probe-opentaint-value-kind",
    ),
}

FLAG_ALIASES = {
    "--infer": "infer",
    "--flowdroid-jar": "flowdroid",
    "--android-platform": "android-platform",
    "--d8-jar": "d8",
    "--analyzer-jar": "opentaint",
    "--models-archive": "opentaint-models",
    "--rules-archive": "opentaint-rules",
    "--java": "java",
    "--javac": "javac",
    "--kotlinc": "kotlinc",
    "--kotlin-stdlib": "kotlin-stdlib",
}

HELD_TOOL_IDS = {
    "infer": "infer",
    "flowdroid": "flowdroid",
    "android-platform": "android-platform",
    "d8": "d8",
    "opentaint": "opentaint-analyzer",
    "opentaint-models": "opentaint-models",
    "opentaint-rules": "opentaint-rules",
    "kotlin-stdlib": "kotlin-stdlib",
}


class AuditError(RuntimeError):
    """Raised when retained evidence does not bind exactly."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_json(path: Path, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"missing or unsafe {description}: {path}")
    try:
        result = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot parse {description} {path}: {exc}") from exc
    require(isinstance(result, dict), f"{description} must be an object: {path}")
    return result


def repo_path(relative: str, description: str) -> Path:
    posix = PurePosixPath(relative)
    require(not posix.is_absolute() and ".." not in posix.parts, f"unsafe {description} path: {relative}")
    result = ROOT.joinpath(*posix.parts)
    require(result.resolve().is_relative_to(ROOT.resolve()), f"escaped {description} path: {relative}")
    return result


def run_git(*argv: str) -> bytes:
    try:
        return subprocess.check_output(["git", *argv], cwd=ROOT, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        raise AuditError(f"git {' '.join(argv)} failed: {detail.decode(errors='replace')}") from exc


def import_executor():
    path = ROOT / "scripts/execute-release-v092.py"
    name = "execute_release_v092_for_retained_qualification"
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot load v0.9.2 release executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_direct_binding(executor: Any, bindings: dict[str, Any], alias: str) -> dict[str, Any]:
    require(alias in bindings, f"v0.9.2 bindings omit component {alias}")
    row = bindings[alias]
    require(isinstance(row, dict), f"component binding {alias} is not an object")
    executor._check_tool_file(row, alias)
    return row


def actual_tree(root: Path) -> dict[str, dict[str, Any]]:
    require(root.is_dir() and not root.is_symlink(), f"runtime root is missing or symlinked: {root}")
    entries: dict[str, dict[str, Any]] = {}
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                entries[relative] = {"mode": stat.S_IMODE(info.st_mode), "symlink": os.readlink(path)}
                dirs.remove(name)
            elif stat.S_ISDIR(info.st_mode):
                entries[relative] = {"mode": stat.S_IMODE(info.st_mode), "directory": True}
            else:
                raise AuditError(f"runtime tree has a non-directory entry in directory list: {path}")
        for name in files:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                entries[relative] = {"mode": stat.S_IMODE(info.st_mode), "symlink": os.readlink(path)}
            elif stat.S_ISREG(info.st_mode):
                entries[relative] = {"mode": stat.S_IMODE(info.st_mode), "sha256": sha_file(path)}
            else:
                raise AuditError(f"runtime tree contains a non-regular file: {path}")
    return entries


def verify_legacy_tree_against_current(tool: str, old_contract: dict[str, Any], bindings: dict[str, Any], executor: Any) -> dict[str, Any]:
    runtime_alias = f"{tool}-runtime"
    current_binding = verify_direct_binding(executor, bindings, runtime_alias)
    manifest_path = Path(current_binding["path"])
    current_manifest = read_json(manifest_path, f"current {tool} runtime manifest")
    require(current_manifest.get("schema_version") == 1, f"current {tool} runtime manifest schema mismatch")
    current_root = Path(current_manifest.get("root", ""))
    require(current_root.is_absolute(), f"current {tool} runtime root is not absolute")

    runtime_refs = old_contract.get("runtime_trees")
    require(isinstance(runtime_refs, list), "v0.9.0 contract lacks runtime tree references")
    old_ref = next((row for row in runtime_refs if Path(row.get("path", "")).name == f"{tool}.json"), None)
    require(isinstance(old_ref, dict), f"v0.9.0 contract does not bind {tool} runtime tree")
    old_manifest_path = repo_path(old_ref["path"], f"v0.9.0 {tool} runtime manifest")
    require(sha_file(old_manifest_path) == old_ref["sha256"], f"v0.9.0 {tool} runtime manifest digest mismatch")
    old_manifest = read_json(old_manifest_path, f"v0.9.0 {tool} runtime manifest")
    require(old_manifest.get("schema") == "release-runtime-tree/v1", f"v0.9.0 {tool} runtime manifest schema mismatch")
    require(old_manifest.get("root") == str(current_root), f"{tool} runtime root changed since v0.9.0")

    executor._check_tool_file(current_binding, runtime_alias)
    live = actual_tree(current_root)
    require(old_manifest.get("entries") == live, f"{tool} current runtime tree differs from v0.9.0 tree")
    old_external = old_manifest.get("external_files", {})
    require(old_external in ({}, []), f"unexpected {tool} external runtime files prevent exact tree comparison")

    current_files = current_manifest.get("files")
    current_links = current_manifest.get("symlinks", [])
    current_external = current_manifest.get("external_files", [])
    require(isinstance(current_files, list) and isinstance(current_links, list) and isinstance(current_external, list), f"malformed current {tool} inventory")
    require(not current_external, f"current {tool} runtime has external files outside the exact tree")
    listed: dict[str, dict[str, Any]] = {}
    for row in current_files:
        require(isinstance(row, dict) and isinstance(row.get("path"), str), f"malformed {tool} file inventory row")
        require(row["path"] not in listed, f"duplicate current {tool} inventory path: {row['path']}")
        listed[row["path"]] = {"mode": row.get("mode"), "sha256": row.get("sha256")}
    for row in current_links:
        require(isinstance(row, dict) and isinstance(row.get("path"), str), f"malformed {tool} symlink inventory row")
        require(row["path"] not in listed, f"duplicate current {tool} inventory path: {row['path']}")
        listed[row["path"]] = {"mode": row.get("mode"), "symlink": row.get("target")}
    live_leaf_entries = {path: value for path, value in live.items() if not value.get("directory")}
    require(listed == live_leaf_entries, f"current {tool} acquisition inventory does not match the live runtime tree")
    return {
        "old_manifest": {"path": old_ref["path"], "sha256": old_ref["sha256"]},
        "current_manifest": {"path": str(manifest_path), "sha256": current_binding["sha256"]},
        "root": str(current_root),
        "entry_count": len(live),
        "file_count": len(current_files),
        "symlink_count": len(current_links),
        "v090_live_entry_equality": True,
        "v092_inventory_live_equality": True,
    }


def verify_held_digests(old_contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    input_identities = old_contract.get("input_identities", {})
    require(isinstance(input_identities, dict), "v0.9.0 contract input identities are malformed")
    held_rel = "reports/releases/v0.9.0/execution-v1/held-tool-digests.json"
    dep_rel = "reports/releases/v0.9.0/execution-v1/dependency-version-witnesses.json"
    for relative in (held_rel, dep_rel):
        require(relative in input_identities, f"v0.9.0 contract omits input identity for {relative}")
        require(sha_file(ROOT / relative) == input_identities[relative], f"v0.9.0 input identity changed: {relative}")
    held = read_json(ROOT / held_rel, "v0.9.0 held tool digests")
    dependencies = read_json(ROOT / dep_rel, "v0.9.0 dependency version witnesses")
    return (
        {"path": held_rel, "sha256": input_identities[held_rel], "document": held},
        {"path": dep_rel, "sha256": input_identities[dep_rel], "document": dependencies},
    )


def validate_held_component(alias: str, binding: dict[str, Any], held: dict[str, Any]) -> Optional[dict[str, Any]]:
    held_id = HELD_TOOL_IDS.get(alias)
    if held_id is None:
        return None
    records = [row for row in held["document"].get("artifacts", []) if row.get("id") == held_id]
    require(len(records) == 1, f"v0.9.0 held tool digest is missing or ambiguous for {alias}")
    record = records[0]
    require(record.get("path") == binding.get("path"), f"{alias} path differs from held v0.9.0 identity")
    require(record.get("sha256") == binding.get("sha256") and record.get("matches_historical") is True, f"{alias} bytes differ from held v0.9.0 identity")
    return {"id": held_id, "path": record["path"], "sha256": record["sha256"]}


def java_witness(dependencies: dict[str, Any], java_root: str) -> dict[str, Any]:
    doc = dependencies["document"]
    env = doc.get("environment", {})
    require(env.get("JAVA_HOME") == java_root, "v0.9.0 JAVA_HOME differs from the current Java runtime root")
    commands = doc.get("commands", [])
    by_command = {tuple(row.get("argv", [])): row for row in commands}
    java = by_command.get(("/usr/bin/java", "-version"))
    javac = by_command.get(("/usr/bin/javac", "-version"))
    kotlinc = by_command.get(("/opt/homebrew/bin/kotlinc", "-version"))
    require(java and java.get("exit_code") == 0 and "21.0.8" in java.get("stderr", ""), "v0.9.0 Java version witness is missing")
    require(javac and javac.get("exit_code") == 0 and "21.0.8" in javac.get("stdout", ""), "v0.9.0 javac version witness is missing")
    require(kotlinc and kotlinc.get("exit_code") == 0 and "2.4.10" in kotlinc.get("stderr", ""), "v0.9.0 kotlinc version witness is missing")
    return {
        "java_home": java_root,
        "java_version_output_sha256": sha_bytes(java["stderr"].encode()),
        "javac_version_output_sha256": sha_bytes(javac["stdout"].encode()),
        "kotlinc_version_output_sha256": sha_bytes(kotlinc["stderr"].encode()),
        "whole_v090_java_tree_digest_available": False,
        "whole_v090_kotlinc_distribution_digest_available": False,
    }


def binding_arg_matches(argv: list[str], flag: str, bindings: dict[str, Any], *, resolve: bool = False) -> bool:
    indexes = [index for index, value in enumerate(argv[:-1]) if value == flag]
    require(len(indexes) <= 1, f"duplicate command-line option {flag}")
    if not indexes:
        return False
    alias = FLAG_ALIASES[flag]
    current = bindings[alias]["path"]
    actual = argv[indexes[0] + 1]
    if resolve:
        require(Path(actual).resolve() == Path(current).resolve(), f"{flag} resolved path differs from current {alias} binding")
    else:
        require(actual == current, f"{flag} differs from current {alias} binding")
    return True


def verify_group_configs(tool: str, old_contract: dict[str, Any], bindings_doc: dict[str, Any], java_root: str, population_doc: dict[str, Any]) -> tuple[list[str], dict[str, list[str]], list[dict[str, Any]]]:
    current_map = bindings_doc.get("group_tools")
    require(isinstance(current_map, dict), "v0.9.2 binding draft lacks group_tools")
    current_groups = sorted(group for group, selected_tool in current_map.items() if selected_tool == tool)
    expected_groups = sorted(TOOL_GROUPS[tool])
    require(current_groups == expected_groups, f"current {tool} group set differs from the audited scope")
    old_rows = {row.get("id"): row for row in old_contract.get("groups", []) if row.get("tool") == tool}
    require(sorted(old_rows) == expected_groups, f"v0.9.0 {tool} group set differs from the current binding draft")
    population_cases = population_doc.get("cases")
    require(isinstance(population_cases, list), "v0.9.0 population case list is malformed")
    case_paths = {row.get("id"): row.get("path") for row in population_cases if isinstance(row, dict)}
    require(len(case_paths) == len(population_cases), "v0.9.0 population has malformed or duplicate case identities")
    group_components: dict[str, list[str]] = {}
    configuration: list[dict[str, Any]] = []
    tool_languages: set[str] = set()

    for group in expected_groups:
        row = old_rows[group]
        argv = row.get("argv")
        environment = row.get("environment")
        require(isinstance(argv, list) and all(isinstance(value, str) for value in argv), f"v0.9.0 {group} argv is malformed")
        require(isinstance(environment, dict), f"v0.9.0 {group} environment is missing")
        require(environment.get("JAVA_HOME") == java_root, f"{group} JAVA_HOME differs from current Java runtime root")
        case_ids = row.get("case_ids")
        require(isinstance(case_ids, list) and case_ids, f"v0.9.0 {group} has no case roster")
        language_counts: dict[str, int] = {}
        for case_id in case_ids:
            case_path = case_paths.get(case_id)
            require(isinstance(case_path, str), f"v0.9.0 {group} references a case outside the retained population: {case_id}")
            parts = PurePosixPath(case_path).parts
            require(len(parts) >= 4, f"population case path is malformed: {case_path}")
            language = parts[2] if parts[:2] == ("cases", "taint") else ""
            if not language:
                population_case = next(row for row in population_cases if row.get("id") == case_id)
                fixtures = population_case.get("fixture_digests", [])
                require(fixtures and isinstance(fixtures[0].get("path"), str), f"{group} case has no fixture language witness: {case_id}")
                suffix = PurePosixPath(fixtures[0]["path"]).suffix.lower()
                language = {".c": "c", ".cc": "cpp", ".cpp": "cpp", ".cs": "csharp", ".go": "go", ".java": "java", ".js": "javascript", ".kt": "kotlin", ".php": "php", ".py": "python", ".rb": "ruby", ".rs": "rust", ".scala": "scala", ".swift": "swift", ".ts": "typescript"}.get(suffix, "")
                require(language, f"cannot determine fixture language for {case_id}: {suffix}")
            language_counts[language] = language_counts.get(language, 0) + 1
        tool_languages.update(language_counts)

        used = {f"{tool}-runtime"}
        # PATH/JAVA_HOME participate in all these tool invocations even when
        # the command does not carry an explicit --java argument.
        used.add("java-runtime")
        for flag, alias in FLAG_ALIASES.items():
            if binding_arg_matches(argv, flag, bindings_doc["tool_bindings"], resolve=(flag == "--kotlinc")):
                used.add(alias)

        if tool == "infer":
            require("--infer" in argv, f"{group} does not bind the current Infer executable")
        elif tool == "flowdroid":
            require("--flowdroid-jar" in argv and "--android-platform" in argv, f"{group} omits a required FlowDroid component")
        else:
            require("--analyzer-jar" in argv and "--models-archive" in argv, f"{group} omits a required OpenTaint component")

        group_components[group] = sorted(used)
        configuration.append({
            "group_id": group,
            "tool": tool,
            "case_count": len(row.get("case_ids", [])),
            "case_ids_sha256": sha_bytes(canonical_json(row.get("case_ids", []))),
            "case_language_counts": dict(sorted(language_counts.items())),
            "case_languages": sorted(language_counts),
            "argv_sha256": sha_bytes(canonical_json(argv)),
            "environment_sha256": sha_bytes(canonical_json(environment)),
            "binding_flags_verified": sorted(flag for flag in FLAG_ALIASES if flag in argv),
            "status": "historical-v090-configuration-only",
        })
    expected_languages = {"infer": {"c", "cpp", "java"}, "flowdroid": {"java", "kotlin"}, "opentaint": {"java", "kotlin"}}[tool]
    require(expected_languages <= tool_languages, f"retained {tool} group configurations omit required source languages: {sorted(expected_languages - tool_languages)}")
    return expected_groups, group_components, configuration


def verify_control(tool: str, control_id: str, bindings_doc: dict[str, Any], inventory: dict[str, Any], contract_path: Path, contract: dict[str, Any], executor: Any) -> dict[str, Any]:
    control_rel = V090_RESUME / "completion-evidence" / "controls" / control_id / "attempt-01"
    folder = ROOT / control_rel
    completed_path = folder / "completed.json"
    started_path = folder / "started.json"
    completed = read_json(completed_path, f"{control_id} completion receipt")
    started = read_json(started_path, f"{control_id} start receipt")
    require(completed.get("schema") == "release-control-attempt/v1", f"{control_id} completion schema mismatch")
    require(completed.get("control_id") == control_id and completed.get("status") == "completed", f"{control_id} is not completed")
    require(completed.get("exit_code") == 0 and completed.get("timed_out") is False, f"{control_id} failed or timed out")
    require(completed.get("missing_output_roots") == [], f"{control_id} has missing output roots")
    require(completed.get("release") == "v0.9.0" and completed.get("attempt_number") == 1, f"{control_id} is not the immutable v0.9.0 attempt-01 receipt")
    require(completed.get("argv") == started.get("argv") and completed.get("environment") == started.get("environment"), f"{control_id} start/completion configuration differs")
    require(started.get("status") == "started" and started.get("control_id") == control_id, f"{control_id} start receipt identity mismatch")
    require(completed.get("started_receipt") == "started.json", f"{control_id} has an unexpected started receipt name")
    started_sha = sha_file(started_path)
    require(completed.get("started_receipt_sha256") == started_sha, f"{control_id} started receipt digest mismatch")

    contract_ref = completed.get("contract", {})
    require(contract_ref.get("path") == contract_path.relative_to(ROOT).as_posix(), f"{control_id} references a different v0.9.0 contract")
    require(contract_ref.get("sha256") == sha_file(contract_path), f"{control_id} contract digest mismatch")
    inventory_ref = completed.get("control_inventory", {})
    inventory_path = ROOT / V090_RESUME / "control-inventory.json"
    require(inventory_ref.get("path") == inventory_path.relative_to(ROOT).as_posix(), f"{control_id} references a different control inventory")
    require(inventory_ref.get("sha256") == sha_file(inventory_path), f"{control_id} control inventory digest mismatch")
    require(completed.get("parent_plan_sha256") == contract.get("parent_plan", {}).get("sha256"), f"{control_id} parent plan digest mismatch")
    require(completed.get("population_sha256") == contract.get("population", {}).get("sha256"), f"{control_id} population digest mismatch")

    inventory_rows = [row for row in inventory.get("controls", []) if row.get("id") == control_id]
    require(len(inventory_rows) == 1, f"{control_id} control inventory row is missing or ambiguous")
    registered = inventory_rows[0]
    require(registered.get("argv") == completed.get("argv"), f"{control_id} argv differs from registered configuration")
    require(registered.get("script_identity") == completed.get("script_identity"), f"{control_id} source identity differs from registered configuration")
    require(registered.get("stage") == "script_probes", f"{control_id} is not registered as a script probe")
    script_identity = completed.get("script_identity")
    require(isinstance(script_identity, list) and len(script_identity) == 1, f"{control_id} must bind exactly one implementation script")
    script_row = script_identity[0]
    script_path = repo_path(script_row["path"], f"{control_id} implementation")
    require(sha_file(script_path) == script_row["sha256"], f"{control_id} current implementation differs from v0.9.0 receipt")
    historical_script = sha_bytes(run_git("show", f"{contract['source_commit']}:{script_row['path']}"))
    require(historical_script == script_row["sha256"], f"{control_id} script differs from v0.9.0 source commit")

    argv = completed["argv"]
    tool_alias = {"infer": "infer", "flowdroid": "flowdroid", "opentaint": "opentaint"}[tool]
    required_flags = {
        "infer": ("--infer",),
        "flowdroid": ("--flowdroid-jar", "--android-platform"),
        "opentaint": ("--analyzer-jar",),
    }[tool]
    used = {f"{tool}-runtime"}
    for flag, alias in FLAG_ALIASES.items():
        if binding_arg_matches(argv, flag, bindings_doc["tool_bindings"], resolve=(flag == "--kotlinc")):
            used.add(alias)
    for flag in required_flags:
        require(flag in argv, f"{control_id} omits required component flag {flag}")
    require(tool_alias in bindings_doc["tool_bindings"], f"v0.9.2 primary binding missing: {tool_alias}")

    captures = completed.get("captured_files")
    require(isinstance(captures, list) and captures, f"{control_id} has no captured outputs")
    capture_rows = []
    seen_capture_paths: set[str] = set()
    for row in captures:
        require(isinstance(row, dict) and isinstance(row.get("path"), str), f"{control_id} capture row is malformed")
        relative = PurePosixPath(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, f"{control_id} capture path is unsafe")
        require(row["path"] not in seen_capture_paths, f"{control_id} has duplicate capture path {row['path']}")
        seen_capture_paths.add(row["path"])
        captured = folder / "capture" / Path(*relative.parts)
        require(captured.is_file() and not captured.is_symlink(), f"{control_id} captured file missing or unsafe: {row['path']}")
        require(captured.stat().st_size == row.get("bytes") and sha_file(captured) == row.get("sha256"), f"{control_id} capture changed: {row['path']}")
        capture_rows.append({"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]})

    stream_refs = {}
    for stream_name in ("stdout", "stderr"):
        ref = completed.get(stream_name)
        require(isinstance(ref, dict) and isinstance(ref.get("path"), str), f"{control_id} lacks {stream_name} identity")
        stream_path = repo_path((control_rel / ref["path"]).as_posix(), f"{control_id} {stream_name}")
        require(stream_path.is_file() and not stream_path.is_symlink() and sha_file(stream_path) == ref.get("sha256"), f"{control_id} {stream_name} changed")
        stream_refs[stream_name] = {"path": stream_path.relative_to(ROOT).as_posix(), "sha256": ref["sha256"]}

    return {
        "id": control_id,
        "completion_receipt": {"path": completed_path.relative_to(ROOT).as_posix(), "sha256": sha_file(completed_path)},
        "started_receipt": {"path": started_path.relative_to(ROOT).as_posix(), "sha256": started_sha},
        "status": completed["status"],
        "exit_code": completed["exit_code"],
        "duration_seconds": completed.get("duration_seconds"),
        "argv_sha256": sha_bytes(canonical_json(argv)),
        "environment_sha256": completed["environment_sha256"],
        "script": {"path": script_row["path"], "sha256": script_row["sha256"]},
        "control_inventory_status": registered.get("status"),
        "capture_count": len(capture_rows),
        "capture_manifest_sha256": sha_bytes(canonical_json(capture_rows)),
        "captured_files": capture_rows,
        "streams": stream_refs,
        "component_aliases_used": sorted(used),
    }


def bound_tool_identity(binding: dict[str, Any]) -> dict[str, Any]:
    """Match the executor's exact qualification identity envelope."""
    identity = {key: binding[key] for key in ("path", "sha256", "version") if key in binding}
    for key in ("build_identity", "archive_sha256", "binary_sha256"):
        if key in binding:
            identity[key] = binding[key]
    return identity


def build_receipt(tool: str, bindings_doc: dict[str, Any], binding_path: Path, old_contract_path: Path, old_contract: dict[str, Any], population_doc: dict[str, Any], population_ref: dict[str, Any], population_tree: dict[str, Any], inventory: dict[str, Any], held: dict[str, Any], dependencies: dict[str, Any], executor: Any, current_group_map: dict[str, Any]) -> dict[str, Any]:
    tool_binding = verify_direct_binding(executor, bindings_doc["tool_bindings"], tool)
    expected_version = {"infer": "v1.3.0", "flowdroid": "2.15.1", "opentaint": "v0.4.6"}[tool]
    require(tool_binding.get("version") == expected_version, f"{tool} version binding is not the retained latest")
    require(tool_binding.get("report_version") == tool_binding.get("version"), f"{tool} report version differs from tool version")

    declared_components = bindings_doc.get("tool_components", {}).get(tool)
    require(isinstance(declared_components, list), f"v0.9.2 bindings omit {tool} component list")
    java_component = "java-runtime"
    support = set(declared_components)
    groups, group_components, group_config = verify_group_configs(
        tool,
        old_contract,
        bindings_doc,
        str(Path(read_json(Path(bindings_doc["tool_bindings"][java_component]["path"]), "Java manifest")["root"])),
        population_doc,
    )
    support.update(alias for group_aliases in group_components.values() for alias in group_aliases)
    support.add(java_component)

    for alias in sorted(support):
        verify_direct_binding(executor, bindings_doc["tool_bindings"], alias)

    held_components = {}
    for alias in sorted(support | {tool}):
        match = validate_held_component(alias, bindings_doc["tool_bindings"][alias], held)
        if match:
            held_components[alias] = match

    java_root = str(Path(read_json(Path(bindings_doc["tool_bindings"][java_component]["path"]), "Java manifest")["root"]))
    java_evidence = java_witness(dependencies, java_root)
    runtime_evidence = verify_legacy_tree_against_current(tool, old_contract, bindings_doc["tool_bindings"], executor)
    control_evidence = [
        verify_control(tool, control_id, bindings_doc, inventory, old_contract_path, old_contract, executor)
        for control_id in TOOL_CONTROLS[tool]
    ]

    return {
        "schema": "v092-retained-tool-qualification/v1",
        "release": "v0.9.2",
        "status": "measurement-with-known-limits",
        "execution_eligible": True,
        "basis": "retained-v0.9.0-controls-with-exact-tool-runtime-tree-and-command-configuration",
        "tool": bound_tool_identity(tool_binding),
        "groups": groups,
        "expanded_group_components": group_components,
        "identity_components": [
            executor._component_identity(alias, bindings_doc["tool_bindings"][alias])
            for alias in declared_components
        ],
        "v090_configuration": {
            "contract": {"path": old_contract_path.relative_to(ROOT).as_posix(), "sha256": sha_file(old_contract_path)},
            "groups": group_config,
            "population": population_ref,
            "population_fixture_tree": population_tree,
            "fixture_revision": old_contract["fixture_revision"],
            "controls": control_evidence,
        },
        "exact_identity_evidence": {
            "bindings_draft": {"path": binding_path.relative_to(ROOT).as_posix(), "sha256": sha_file(binding_path), "status": bindings_doc.get("status")},
            "runtime_tree": runtime_evidence,
            "held_v090_component_digests": held_components,
            "java_and_kotlin_version_witness": {
                "path": dependencies["path"],
                "sha256": dependencies["sha256"],
                **java_evidence,
            },
        },
        "limits": [
            "The v0.9.0 control captures are retained as qualification evidence; their normal-group reports are not copied or promoted as v0.9.2 measurements.",
            "The v0.9.0 control inventory still labels these rows registered-pending-final-executable-plan-review; this receipt independently verifies each start/completion record, command, source script, streams, and captured output hashes.",
            "The v0.9.0 record binds Temurin 21.0.8 and the same JAVA_HOME, but does not retain a full Java runtime tree digest; current v0.9.2 Java runtime inventory is verified against the live tree only.",
            "Kotlin compiler 2.4.10 is version/path-bound in v0.9.0 and the current v0.9.2 compiler file is hashed, but v0.9.0 did not retain a full Kotlin compiler distribution digest.",
            "These receipts authorize attempts for the listed groups; they do not assert v0.9.2 analyzer coverage, completeness, or group outcomes. The v0.9.2 bindings draft remains incomplete until unrelated pending components are qualified.",
        ],
        "review_implementation": {
            "path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "sha256": sha_file(Path(__file__).resolve()),
        },
    }


def verify_population_fixture_tree(old_contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    population_ref = old_contract.get("population")
    require(isinstance(population_ref, dict), "v0.9.0 contract population reference is malformed")
    population_path = repo_path(population_ref.get("path", ""), "v0.9.0 population")
    require(sha_file(population_path) == population_ref.get("sha256"), "v0.9.0 population file digest mismatch")
    population_doc = read_json(population_path, "immutable v0.9.0 population")
    require(population_doc.get("population") == "v0.9.0", "v0.9.0 population identity mismatch")
    require(population_doc.get("fixture_revision") == old_contract.get("fixture_revision"), "v0.9.0 population fixture revision mismatch")
    cases = population_doc.get("cases")
    require(isinstance(cases, list) and cases, "v0.9.0 population case list is empty or malformed")

    corpus_commit = old_contract.get("input_commits", {}).get("corpus")
    require(isinstance(corpus_commit, str) and len(corpus_commit) == 40, "v0.9.0 corpus commit is missing")
    language_counts: dict[str, int] = {}
    fixture_roots: set[str] = set()
    for case in cases:
        require(isinstance(case, dict) and isinstance(case.get("id"), str) and isinstance(case.get("path"), str), "v0.9.0 population contains a malformed case")
        case_path = PurePosixPath(case["path"])
        require(not case_path.is_absolute() and ".." not in case_path.parts and len(case_path.parts) >= 4, f"unsafe or malformed population case path: {case['path']}")
        live_case_path = ROOT.joinpath(*case_path.parts)
        require(live_case_path.is_file() and not live_case_path.is_symlink(), f"population case file is missing or unsafe: {case_path.as_posix()}")
        require(sha_file(live_case_path) == case.get("sha256"), f"population case bytes changed: {case_path.as_posix()}")
        fixture_roots.add("/".join(case_path.parts[:2]))
        language = case_path.parts[2] if case_path.parts[:2] == ("cases", "taint") else ""
        fixtures = case.get("fixture_digests", [])
        require(isinstance(fixtures, list) and fixtures, f"population case lacks fixture digests: {case_path.as_posix()}")
        for fixture in fixtures:
            require(isinstance(fixture, dict) and isinstance(fixture.get("path"), str), f"malformed fixture digest row: {case_path.as_posix()}")
            fixture_path = PurePosixPath(fixture["path"])
            require(not fixture_path.is_absolute() and ".." not in fixture_path.parts and len(fixture_path.parts) >= 4, f"unsafe fixture path: {fixture.get('path')}")
            live_fixture_path = ROOT.joinpath(*fixture_path.parts)
            require(live_fixture_path.is_file() and not live_fixture_path.is_symlink(), f"population fixture is missing or unsafe: {fixture_path.as_posix()}")
            require(sha_file(live_fixture_path) == fixture.get("sha256"), f"population fixture bytes changed: {fixture_path.as_posix()}")
            fixture_roots.add("/".join(fixture_path.parts[:2]))
            if not language:
                suffix = fixture_path.suffix.lower()
                language = {".c": "c", ".cc": "cpp", ".cpp": "cpp", ".cs": "csharp", ".go": "go", ".java": "java", ".js": "javascript", ".kt": "kotlin", ".php": "php", ".py": "python", ".rb": "ruby", ".rs": "rust", ".scala": "scala", ".swift": "swift", ".ts": "typescript"}.get(suffix, "")
        require(language, f"cannot determine fixture language for {case_path.as_posix()}")
        language_counts[language] = language_counts.get(language, 0) + 1
    root_identities = []
    for fixture_root in sorted(fixture_roots):
        diff = subprocess.run(["git", "diff", "--quiet", corpus_commit, "--", fixture_root], cwd=ROOT)
        require(diff.returncode == 0, f"current fixture tree differs from retained corpus commit: {fixture_root}")
        untracked = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all", "--", fixture_root], cwd=ROOT, text=True)
        require(not untracked.strip(), f"untracked fixture content is outside retained corpus tree: {fixture_root}")
        tree = run_git("rev-parse", f"{corpus_commit}:{fixture_root}").decode().strip()
        require(len(tree) == 40, f"retained fixture tree identity is malformed: {fixture_root}")
        tree_entries = run_git("ls-tree", "-r", "--name-only", corpus_commit, "--", fixture_root).decode().splitlines()
        require(tree_entries, f"retained corpus commit has no fixture entries: {fixture_root}")
        root_identities.append({"path": fixture_root, "git_tree_object": tree, "tracked_entry_count": len(tree_entries), "tracked_diff_clean": True, "untracked_content_absent": True})
    tree = run_git("rev-parse", f"{corpus_commit}:cases/taint").decode().strip()
    return population_doc, {
        "path": "cases/taint",
        "corpus_commit": corpus_commit,
        "git_tree_object": tree,
        "fixture_roots": root_identities,
        "population_case_count": len(cases),
        "population_case_language_counts": dict(sorted(language_counts.items())),
        "tracked_diff_clean": True,
        "untracked_content_absent": True,
    }


def run_qualification_gate_selfcheck(output_dir: Path, receipts: dict[str, dict[str, Any]], receipt_paths: dict[str, Path], bindings_doc: dict[str, Any], executor: Any) -> dict[str, Any]:
    """Exercise the real gate with one actual group per retained analyzer family."""
    selfcheck_dir = Path(tempfile.mkdtemp(prefix=".gate-selfcheck-", dir=output_dir))
    try:
        groups = []
        qualifications = {}
        evidence_refs = {}
        for tool in TOOL_GROUPS:
            receipt = receipts[tool]
            group_id = receipt["groups"][0]
            require(bindings_doc["group_tools"].get(group_id) == tool, f"self-check group {group_id} is not bound to {tool}")
            group = {"id": group_id, "tool": tool}
            groups.append(group)
            reduced_evidence = dict(receipt)
            reduced_evidence["groups"] = [group_id]
            evidence_path = selfcheck_dir / f"{tool}.json"
            evidence_path.write_bytes(json.dumps(reduced_evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n")
            relative_path = evidence_path.relative_to(ROOT).as_posix()
            reference = {"path": relative_path, "sha256": sha_file(evidence_path)}
            qualifications[tool] = {
                "status": receipt["status"],
                "execution_eligible": receipt["execution_eligible"],
                "groups": [group_id],
                "evidence": reference,
            }
            evidence_refs[tool] = {
                "source_receipt": receipt_paths[tool].relative_to(ROOT).as_posix(),
                "source_receipt_sha256": sha_file(receipt_paths[tool]),
                "selfcheck_evidence_sha256": reference["sha256"],
                "group": group_id,
            }
        checked = executor._qualification_gate(
            {"groups": groups, "qualifications": qualifications},
            ROOT,
            bindings_doc["tool_bindings"],
            bindings_doc["tool_components"],
        )
        require(set(checked) == set(TOOL_GROUPS), "executor qualification gate returned an unexpected analyzer set")
        return {
            "schema": "v092-retained-qualification-gate-selfcheck/v1",
            "status": "passed",
            "groups": groups,
            "analyzers": evidence_refs,
            "gate_checked_analyzers": sorted(checked),
            "note": "The gate was called with one actual bound group per analyzer family; temporary evidence narrowed only the receipt group list to that group's exact scope.",
        }
    finally:
        for path in selfcheck_dir.iterdir():
            path.unlink()
        selfcheck_dir.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    bindings_path = args.bindings if args.bindings.is_absolute() else ROOT / args.bindings
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    require(bindings_path.is_file() and not bindings_path.is_symlink(), "bindings draft is missing or unsafe")
    require(output_dir.resolve().is_relative_to((ROOT / "reports/releases/v0.9.2/qualification").resolve()), "output must be under v0.9.2 qualification")
    bindings_doc = read_json(bindings_path, "v0.9.2 binding draft")
    require(bindings_doc.get("schema") == "v092-binding-draft/v1", "unexpected v0.9.2 binding draft schema")

    old_contract_path = ROOT / V090_RESUME / "contract.json"
    old_contract = read_json(old_contract_path, "final v0.9.0 resume contract")
    require(old_contract.get("release") == "v0.9.0", "retained contract is not v0.9.0")
    require(old_contract.get("harness_commit") == old_contract.get("source_commit"), "v0.9.0 control harness/source commit is ambiguous")
    parent_plan_ref = old_contract.get("parent_plan", {})
    parent_plan_path = repo_path(parent_plan_ref.get("path", ""), "v0.9.0 parent plan")
    require(sha_file(parent_plan_path) == parent_plan_ref.get("sha256"), "v0.9.0 parent plan digest mismatch")

    inventory_path = ROOT / V090_RESUME / "control-inventory.json"
    inventory = read_json(inventory_path, "v0.9.0 final control inventory")
    held, dependencies = verify_held_digests(old_contract)
    executor = import_executor()

    # Bind the complete C/C++/Java/Kotlin and other-language population tree,
    # including non-Java case assets, to the immutable v0.9.0 corpus commit.
    population_doc, population_tree = verify_population_fixture_tree(old_contract)
    population_ref = old_contract["population"]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {tool: output_dir / f"{tool}.json" for tool in TOOL_GROUPS}
    selfcheck_path = output_dir / "qualification-gate-selfcheck.json"
    require(all(not path.exists() for path in output_paths.values()) and not selfcheck_path.exists(), "retained-v090-02 output already exists; refusing overwrite")
    receipts = {}
    for tool in TOOL_GROUPS:
        runtime = verify_legacy_tree_against_current(tool, old_contract, bindings_doc["tool_bindings"], executor)
        # Runtime equality is checked before creating any receipt.
        java_manifest = read_json(Path(bindings_doc["tool_bindings"]["java-runtime"]["path"]), "v0.9.2 Java runtime manifest")
        java_root = str(Path(java_manifest["root"]))
        groups, _components, _config = verify_group_configs(tool, old_contract, bindings_doc, java_root, population_doc)
        require(groups == sorted(TOOL_GROUPS[tool]), f"{tool} group scope changed")
        receipts[tool] = build_receipt(tool, bindings_doc, bindings_path, old_contract_path, old_contract, population_doc, population_ref, population_tree, inventory, held, dependencies, executor, bindings_doc["group_tools"])

    for tool, receipt in receipts.items():
        output_paths[tool].write_bytes((json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode())
    gate_selfcheck = run_qualification_gate_selfcheck(output_dir, receipts, output_paths, bindings_doc, executor)
    selfcheck_path.write_bytes((json.dumps(gate_selfcheck, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode())
    print(json.dumps({"status": "measurement-with-known-limits", "receipts": {tool: {"path": str(output_paths[tool].relative_to(ROOT)), "groups": len(receipt["groups"]), "controls": len(receipt["v090_configuration"]["controls"])} for tool, receipt in receipts.items()}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"retained qualification rejected: {exc}", file=sys.stderr)
        raise SystemExit(2)
