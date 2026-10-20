#!/usr/bin/env python3
"""Generate an unapproved v0.9.2 contract from the immutable v0.9.0 runner plan."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = PurePosixPath("reports/releases/v0.9.0/execution-v1/contract.json")
PARENT_PLAN = PurePosixPath("reports/releases/v0.9.0/plan.json")
OUTPUT = PurePosixPath("reports/releases/v0.9.2/execution-v1/contract.json")
DEFAULT_SWIFT_PLAN = PurePosixPath("adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json")
DEFAULT_JOERN_PLAN = PurePosixPath("adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def _load_executor():
    module_path = Path(__file__).with_name("execute-release-v092.py")
    spec = importlib.util.spec_from_file_location("execute_release_v092", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.9.2 executor: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


executor = _load_executor()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_object(path: Path, description: str) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise executor.ReleaseError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise executor.ReleaseError(f"{description} must be a JSON object")
    return value, raw


def _absolute_string(value: object, description: str) -> str:
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise executor.ReleaseError(f"{description} must be an absolute path")
    return value


def _replace_paths(value: str, replacements: Mapping[str, str]) -> str:
    # Longest-first keeps an explicitly listed nested runtime path from being
    # partially rewritten by one of its parent path entries.
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(old, new)
    return value


def _validate_bindings(
    bindings: dict,
) -> tuple[dict[str, dict], dict[str, str], dict[str, dict[str, str]], dict[str, list[str]]]:
    tool_bindings = bindings.get("tool_bindings")
    if not isinstance(tool_bindings, dict) or not tool_bindings:
        raise executor.ReleaseError("bindings must contain a non-empty tool_bindings object")
    tools = {}
    for name, binding in tool_bindings.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
            raise executor.ReleaseError(f"invalid tool binding alias: {name!r}")
        if not isinstance(binding, dict):
            raise executor.ReleaseError(f"tool_bindings.{name} must be an object")
        path = _absolute_string(binding.get("path"), f"tool_bindings.{name}.path")
        digest = binding.get("sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise executor.ReleaseError(f"tool_bindings.{name}.sha256 must be lowercase SHA-256")
        for key in ("version", "report_version"):
            if key in binding and (not isinstance(binding[key], str) or not binding[key]):
                raise executor.ReleaseError(f"tool_bindings.{name}.{key} must be a non-empty string")
        tools[name] = {**binding, "path": path, "sha256": digest}

    replacements_raw = bindings.get("path_replacements")
    if not isinstance(replacements_raw, dict) or not replacements_raw:
        raise executor.ReleaseError("bindings must contain explicit path_replacements")
    replacements = {}
    for old, new in replacements_raw.items():
        old_path = _absolute_string(old, "path_replacements key")
        new_path = _absolute_string(new, f"path_replacements[{old!r}]")
        replacements[old_path] = new_path

    group_replacements_raw = bindings.get("group_path_replacements", {})
    if not isinstance(group_replacements_raw, dict):
        raise executor.ReleaseError("group_path_replacements must be an object")
    group_replacements = {}
    for group_id, mapping in group_replacements_raw.items():
        if not isinstance(group_id, str) or not isinstance(mapping, dict):
            raise executor.ReleaseError("group_path_replacements entries must map a group ID to paths")
        converted = {}
        for old, new in mapping.items():
            old_path = _absolute_string(old, f"group_path_replacements.{group_id} key")
            new_path = _absolute_string(new, f"group_path_replacements.{group_id}[{old!r}]")
            converted[old_path] = new_path
        group_replacements[group_id] = converted

    components_raw = bindings.get("tool_components")
    if not isinstance(components_raw, dict):
        raise executor.ReleaseError("bindings must contain tool_components")
    components = {}
    for name, aliases in components_raw.items():
        if name not in tools or not isinstance(aliases, list) or not aliases:
            raise executor.ReleaseError(f"tool_components.{name} must have a non-empty alias list")
        if (any(not isinstance(alias, str) or alias not in tools or alias == name for alias in aliases) or
                len(aliases) != len(set(aliases))):
            raise executor.ReleaseError(f"tool_components.{name} contains invalid aliases")
        components[name] = list(aliases)
    component_aliases = {alias for aliases in components.values() for alias in aliases}
    auxiliary = {"runner", "java", "javac", "go", "kotlinc", "kotlin-stdlib",
                 "android-platform", "d8"}
    for name, binding in tools.items():
        if ("version" not in binding or "report_version" not in binding) and name not in component_aliases | auxiliary:
            raise executor.ReleaseError(f"tool_bindings.{name} must bind version and report_version")
    return tools, replacements, group_replacements, components


def build_contract(
    bindings: dict,
    runner_source_sha256: str,
    *,
    repo_root: str | Path = ROOT,
    output_path: str | Path | None = None,
) -> dict:
    """Create a complete prospective contract without authorizing execution."""
    root = Path(repo_root).resolve()
    if not isinstance(runner_source_sha256, str) or not SHA256.fullmatch(runner_source_sha256):
        raise executor.ReleaseError("runner source SHA must be lowercase SHA-256")
    source_commit = bindings.get("source_commit")
    if not isinstance(source_commit, str) or not COMMIT.fullmatch(source_commit):
        raise executor.ReleaseError("bindings must name the exact 40-hex source_commit")
    series = bindings.get("execution_series", 1)
    if type(series) is not int or series < 1:
        raise executor.ReleaseError("execution_series must be a positive integer")
    tools, replacements, group_replacements, tool_components = _validate_bindings(bindings)
    for name, binding in tools.items():
        executor._check_tool_file(binding, name)
    group_tools = bindings.get("group_tools")
    if not isinstance(group_tools, dict):
        raise executor.ReleaseError("bindings must map every historical group in group_tools")
    parent_execution, source_bytes = _read_object(root / Path(*SOURCE_CONTRACT.parts), "v0.9.0 execution contract")
    parent_plan, parent_plan_bytes = _read_object(root / Path(*PARENT_PLAN.parts), "v0.9.0 plan")
    if (parent_execution.get("release") != "v0.9.0" or len(parent_execution.get("groups", [])) != 84 or
            parent_plan.get("release") != "v0.9.0" or len(parent_plan.get("execution_groups", [])) != 84):
        raise executor.ReleaseError("source contracts are not the immutable 84-group v0.9.0 pair")
    source_groups = {group["id"]: group for group in parent_execution["groups"]}
    historical_groups = {group["id"]: group for group in parent_plan["execution_groups"]}
    if set(source_groups) != set(historical_groups) or set(group_tools) != set(source_groups):
        raise executor.ReleaseError("group_tools must bind exactly the 84 historical group IDs")
    if any(alias not in tools for alias in group_tools.values()):
        raise executor.ReleaseError("group_tools contains an unbound tool alias")
    if set(group_replacements) - set(source_groups):
        raise executor.ReleaseError("group_path_replacements contains an unknown historical group")
    codeql_group_ids = [group_id for group_id, group in source_groups.items() if group["tool"] == "codeql"]
    if any(group_tools[group_id] != "codeql" for group_id in codeql_group_ids):
        raise executor.ReleaseError("all CodeQL groups must use the single normalized codeql tool alias")
    packs_alias = bindings.get("codeql_packs_component")
    if (not isinstance(packs_alias, str) or packs_alias not in tools or
            packs_alias not in tool_components.get("codeql", [])):
        raise executor.ReleaseError("codeql_packs_component must name a component of tool codeql")
    swift_packs_alias = bindings.get("swift_codeql_packs_component")
    if (not isinstance(swift_packs_alias, str) or swift_packs_alias not in tools or
            swift_packs_alias not in tool_components.get("codeql", [])):
        raise executor.ReleaseError("swift_codeql_packs_component must name a component of tool codeql")
    codeql_packs_root = (root / "execution-state/v092/tools/codeql-packs").resolve()
    swift_codeql_packs_root = (root / "execution-state/v092/tools/swift-codeql/candidate-packs-entry2").resolve()
    swift_plan_raw = bindings.get("swift_plan_path", DEFAULT_SWIFT_PLAN.as_posix())
    swift_plan = executor._relative(swift_plan_raw, "swift_plan_path")
    if (swift_plan.parts[:3] != ("adapters", "codeql", "swift-common-v2") or
            swift_plan.name != "execution-plan.json"):
        raise executor.ReleaseError("swift_plan_path must select a versioned Swift CodeQL plan under adapters/codeql")
    swift_plan_file = root / Path(*swift_plan.parts)
    if not swift_plan_file.is_file() or swift_plan_file.is_symlink():
        raise executor.ReleaseError(f"versioned Swift CodeQL plan is missing or symlinked: {swift_plan_file}")
    joern_plan_raw = bindings.get("joern_plan_path", DEFAULT_JOERN_PLAN.as_posix())
    joern_plan = executor._relative(joern_plan_raw, "joern_plan_path")
    if (joern_plan.parts[:3] != ("adapters", "joern", "swift-common-v2") or
            joern_plan.name != "execution-plan.json"):
        raise executor.ReleaseError("joern_plan_path must select a versioned Joern plan under adapters/joern")
    joern_plan_file = root / Path(*joern_plan.parts)
    if not joern_plan_file.is_file() or joern_plan_file.is_symlink():
        raise executor.ReleaseError(f"versioned Joern plan is missing or symlinked: {joern_plan_file}")

    groups = []
    used_tools = set()
    for group_id, old in source_groups.items():
        selected_tool = group_tools[group_id]
        family = old["tool"]
        if family in {"codeql", "joern", "semgrep", "pysa"} and selected_tool not in tool_components:
            raise executor.ReleaseError(f"{group_id} ({selected_tool}) lacks exact runtime component bindings")
        binding = tools[selected_tool]
        if selected_tool not in {"runner", "java", "javac", "go", "kotlinc", "kotlin-stdlib",
                                 "android-platform", "d8"} and not binding.get("version"):
            raise executor.ReleaseError(f"{group_id} tool binding lacks an exact version")
        used_tools.add(selected_tool)
        replacements_for_group = {**replacements, **group_replacements.get(group_id, {})}
        argv = [_replace_paths(item, replacements_for_group) for item in old.get("argv", [])]
        if not argv or any(not isinstance(item, str) for item in argv):
            raise executor.ReleaseError(f"{group_id} has malformed argv")
        if family == "codeql":
            is_swift_wrapper = any(Path(item).name in ("run-swift-common-v2.py", "run-swift-common-v092.py") for item in argv)
            if is_swift_wrapper:
                argv = ["scripts/run-swift-common-v092.py" if item == "scripts/run-swift-common-v2.py" else item for item in argv]
                plan_flags = [index for index, item in enumerate(argv) if item == "--plan"]
                if len(plan_flags) != 1 or plan_flags[0] + 1 >= len(argv):
                    raise executor.ReleaseError(f"{group_id} must bind one Swift --plan argument")
                argv[plan_flags[0] + 1] = swift_plan.as_posix()
                # The v092 wrapper takes a receipt produced by the fresh
                # compile-only query qualification stage. It is intentionally
                # a separate argument, not a legacy reservation file.
                argv = [item for item in argv if item != "--reservation"]
                if "reports/releases/v0.9.0/execution-v1/codeql-swift-reservation.json" in argv:
                    argv.remove("reports/releases/v0.9.0/execution-v1/codeql-swift-reservation.json")
                argv.extend([
                    "--query-receipt",
                    "reports/releases/v0.9.2/qualification/codeql-swift-common108/query-check-02/receipt.json",
                ])
                if "--output" not in argv or argv.index("--output") + 1 >= len(argv):
                    raise executor.ReleaseError(f"{group_id} must bind one Swift --output argument")
                swift_output = "reports/raw/swift-common-v2/current108-v092-01"
                argv[argv.index("--output") + 1] = swift_output
                old_output_roots = list(old.get("output_roots", []))
                if len(old_output_roots) != 1:
                    raise executor.ReleaseError(f"{group_id} must declare exactly one Swift output root")
                group_output_roots = [swift_output]
            else:
                pack_flags = [index for index, item in enumerate(argv) if item == "--codeql-packs"]
                if len(pack_flags) != 1 or pack_flags[0] + 1 >= len(argv):
                    raise executor.ReleaseError(f"{group_id} must preserve its explicit --codeql-packs argument")
                argv[pack_flags[0] + 1] = str(codeql_packs_root)
                group_output_roots = list(old["output_roots"])
        elif family == "joern" and any(
                Path(item).name in ("run-joern-common-v2.py", "run-joern-common-v092.py") for item in argv):
            argv = ["scripts/run-joern-common-v092.py" if item == "scripts/run-joern-common-v2.py" else item for item in argv]
            plan_flags = [index for index, item in enumerate(argv) if item == "--plan"]
            if len(plan_flags) != 1 or plan_flags[0] + 1 >= len(argv):
                raise executor.ReleaseError(f"{group_id} must bind one Joern --plan argument")
            argv[plan_flags[0] + 1] = joern_plan.as_posix()
            argv = [item for item in argv if item != "--reservation"]
            legacy_reservation = "reports/releases/v0.9.0/execution-v1/joern-swift-reservation.json"
            if legacy_reservation in argv:
                argv.remove(legacy_reservation)
            if "--output" not in argv or argv.index("--output") + 1 >= len(argv):
                raise executor.ReleaseError(f"{group_id} must bind one Joern --output argument")
            joern_output = "reports/raw/joern-common-v2/current108-v092-01"
            argv[argv.index("--output") + 1] = joern_output
            old_output_roots = list(old.get("output_roots", []))
            if len(old_output_roots) != 1:
                raise executor.ReleaseError(f"{group_id} must declare exactly one Joern output root")
            group_output_roots = [joern_output]
        else:
            group_output_roots = list(old["output_roots"])
        environment = {
            key: _replace_paths(value, replacements_for_group)
            for key, value in old.get("environment", {}).items()
            if isinstance(key, str) and isinstance(value, str)
        }
        if len(environment) != len(old.get("environment", {})):
            raise executor.ReleaseError(f"{group_id} has malformed environment")
        if family == "bifrost":
            environment["BIFROST_OPEN_PACKS_DISABLE"] = "1"
        if family == "semgrep":
            semgrep_bin = str(Path(binding["path"]).parent)
            path_entries = environment.get("PATH", "").split(os.pathsep)
            path_entries = [entry for entry in path_entries if entry and entry != semgrep_bin]
            environment["PATH"] = os.pathsep.join([semgrep_bin, *path_entries])
            if environment["PATH"].split(os.pathsep)[0] != semgrep_bin:
                raise executor.ReleaseError(f"{group_id} does not pin the selected Semgrep environment first in PATH")
        reports = []
        for old_report in old.get("reports", []):
            report_version = binding.get("report_version", binding.get("version"))
            source_path = _replace_paths(old_report["source_path"], replacements_for_group)
            if family == "codeql" and group_id == "codeql-swift-common108":
                source_path = source_path.replace("reports/raw/swift-common-v2/current108-v090-01/",
                                                  "reports/raw/swift-common-v2/current108-v092-01/", 1)
            elif family == "joern" and group_id == "joern-swift-common108":
                source_path = source_path.replace("reports/raw/joern-common-v2/current108-v090-01/",
                                                  "reports/raw/joern-common-v2/current108-v092-01/", 1)
            reports.append({
                "ordinal": old_report["ordinal"],
                "path": old_report["path"].replace(
                    "reports/releases/v0.9.0/normal/", "reports/releases/v0.9.2/normal/", 1
                ),
                "source_path": source_path,
                "case_ids": list(old_report["case_ids"]),
                "tool": selected_tool,
                "tool_version": report_version,
            })
        historical = historical_groups[group_id]
        if old.get("case_ids") != historical.get("case_ids"):
            raise executor.ReleaseError(f"{group_id} source membership differs from the immutable v0.9.0 plan")
        groups.append({
            "id": group_id,
            "family": family,
            "tool": selected_tool,
            "argv": argv,
            "environment": environment,
            "output_roots": group_output_roots,
            "deadline_seconds": old["deadline_seconds"],
            "maximum_attempts": old["maximum_attempts"],
            "case_ids": list(old["case_ids"]),
            "reports": reports,
        })
    if len(used_tools) < 8:
        raise executor.ReleaseError("full-eight-analyzer contract does not select all eight families")

    qualifications = {}
    for name in sorted(used_tools):
        qualifications[name] = {
            "status": "pending",
            "execution_eligible": False,
            "groups": [],
        }
    supplied_resource_budget = bindings.get("resource_budget")
    resource_budget = dict(parent_execution.get("resource_budget", {})) if supplied_resource_budget is None else supplied_resource_budget
    if not isinstance(resource_budget, dict):
        raise executor.ReleaseError("resource_budget must be an object preserving the registered v0.9.0 ceilings")
    resource_budget = dict(resource_budget)
    if supplied_resource_budget is None:
        resource_budget["minimum_launch_free_gib"] = 125
    resource_budget.setdefault("protected_reserve_gib", 40)
    resource_budget.setdefault("scratch_gib", 24)
    resource_budget.setdefault("proposed_total_retention_ceiling_gib", 24)
    if (type(resource_budget.get("serial_analyzers")) is not int or resource_budget["serial_analyzers"] != 1 or
            type(resource_budget.get("minimum_launch_free_gib")) is not int or resource_budget["minimum_launch_free_gib"] < 125 or
            type(resource_budget.get("protected_reserve_gib")) is not int or resource_budget["protected_reserve_gib"] < 40 or
            type(resource_budget.get("scratch_gib")) is not int or not 0 < resource_budget["scratch_gib"] <= 24 or
            type(resource_budget.get("proposed_total_retention_ceiling_gib")) not in (int, float) or
            resource_budget["proposed_total_retention_ceiling_gib"] <= 0 or
            resource_budget["proposed_total_retention_ceiling_gib"] > 24):
        raise executor.ReleaseError("resource_budget must retain one serial analyzer, 125 GiB launch, 40 GiB protected reserve, and <=24 GiB scratch/retention ceilings")
    reservation = bindings.get("resource_reservation")
    if not isinstance(reservation, dict):
        raise executor.ReleaseError("bindings must include a fresh resource_reservation")
    total_wall_budget = bindings.get("total_wall_budget_seconds")
    if isinstance(total_wall_budget, bool) or not isinstance(total_wall_budget, (int, float)) or total_wall_budget <= 0:
        raise executor.ReleaseError("bindings must include positive total_wall_budget_seconds")
    source_inputs = bindings.get("source_inputs", [])
    if not isinstance(source_inputs, list):
        raise executor.ReleaseError("source_inputs must be a list of digest-bound files")

    contract = {
        "schema_version": 1,
        "release": "v0.9.2",
        "source_commit": source_commit,
        "runner_source_sha256": runner_source_sha256,
        "execution_series": series,
        "execution_authorized": False,
        "fixture_revision": parent_execution["fixture_revision"],
        "parent_plan": {
            "path": PARENT_PLAN.as_posix(),
            "sha256": hashlib.sha256(parent_plan_bytes).hexdigest(),
        },
        "parent_execution_contract": {
            "path": SOURCE_CONTRACT.as_posix(),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
        },
        "population": {
            "path": "populations/v0.9.0.json",
            "sha256": parent_execution["population"]["sha256"],
            "fixture_revision": parent_execution["fixture_revision"],
        },
        "tools": tools,
        "tool_components": tool_components,
        "codeql_packs": {
            "root": str(codeql_packs_root),
            "component": packs_alias,
            "swift_root": str(swift_codeql_packs_root),
            "swift_component": swift_packs_alias,
        },
        "path_replacements": replacements,
        "group_path_replacements": group_replacements,
        "qualifications": qualifications,
        "source_inputs": source_inputs,
        "groups": groups,
        "resource_budget": resource_budget,
        "resource_reservation": reservation,
        "total_wall_budget_seconds": total_wall_budget,
        "generator": {
            "path": "scripts/prepare-release-v092.py",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "status": "prospective-unapproved",
        },
    }
    # Reuse the executor's fail-closed structural validation before committing
    # the generated bytes. The destination is the one canonical contract path.
    destination = Path(output_path) if output_path is not None else root / Path(*OUTPUT.parts)
    destination = destination.resolve()
    if destination != (root / Path(*OUTPUT.parts)).resolve():
        raise executor.ReleaseError(f"output must be the canonical contract path: {OUTPUT.as_posix()}")
    if destination.exists() or destination.is_symlink():
        raise executor.ReleaseError(f"contract already exists and will not be overwritten: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(contract)
    with destination.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        executor.validate_plan(destination, repo_root=root)
    except BaseException:
        try:
            if destination.is_file() and hashlib.sha256(destination.read_bytes()).digest() == hashlib.sha256(raw).digest():
                destination.unlink()
        except OSError:
            pass
        raise
    return contract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--runner-source-sha", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    bindings, _ = _read_object(args.bindings, "bindings")
    contract = build_contract(bindings, args.runner_source_sha, output_path=args.output)
    print(json.dumps({
        "path": OUTPUT.as_posix(),
        "execution_authorized": contract["execution_authorized"],
        "group_count": len(contract["groups"]),
        "report_partition_count": sum(len(group["reports"]) for group in contract["groups"]),
        "population": contract["population"],
        "selected_tools": sorted({group["tool"] for group in contract["groups"]}),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (executor.ReleaseError, OSError, ValueError) as exc:
        raise SystemExit(str(exc))
