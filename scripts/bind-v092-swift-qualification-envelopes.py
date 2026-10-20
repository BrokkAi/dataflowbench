#!/usr/bin/env python3
"""Bind current CodeQL and Joern Swift qualification to the executor gate.

This script replays retained qualification evidence and current configuration
checks only. It does not launch analyzer or database commands.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDINGS = Path("execution-state/v092/bindings-draft-03.json")
DEFAULT_CODEQL_OUTPUT = Path("reports/releases/v0.9.2/qualification/codeql-swift-envelope-01.json")
DEFAULT_JOERN_OUTPUT = Path("reports/releases/v0.9.2/qualification/joern-swift-envelope-01.json")
CODEQL_PLAN = Path("adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json")
JOERN_PLAN = Path("adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json")
ORDINARY_DIR = Path("reports/releases/v0.9.2/qualification/codeql-ordinary-query-checks/attempt-01")
NATIVE_REVIEW = Path("reports/releases/v0.9.2/qualification/joern-native-review-01.json")
NATIVE_CAPTURE = Path("reports/releases/v0.9.2/qualification/profile-controls/probe-joern-scan-native-attempt-01")
QUALIFICATION_ROOT = Path("reports/releases/v0.9.2/qualification")
OUTER_SCHEMA = "v092-tool-qualification-envelope/v1"
SHA256 = set("0123456789abcdef")


class BindError(RuntimeError):
    """Raised when a Swift qualification cannot be bound exactly."""


def require(value: bool, message: str) -> None:
    if not value:
        raise BindError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), f"missing or unsafe file: {path}")
    return sha_bytes(path.read_bytes())


def read_json(path: Path, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"missing or unsafe {description}: {path}")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BindError(f"cannot read {description} {path}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be an object: {path}")
    return value


def reference(root: Path, path: Path) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    require(resolved.is_file() and not resolved.is_symlink(), f"reference is not a regular file: {path}")
    require(resolved.is_relative_to(root.resolve()), f"reference escapes repository: {path}")
    return {"path": resolved.relative_to(root.resolve()).as_posix(), "sha256": sha_file(resolved)}


def bound_reference(root: Path, value: object, description: str) -> tuple[Path, dict[str, str]]:
    require(isinstance(value, dict) and set(value) == {"path", "sha256"}, f"{description} must be an exact path/SHA reference")
    path_text, digest = value["path"], value["sha256"]
    require(isinstance(path_text, str) and path_text and "\\" not in path_text, f"{description} path is malformed")
    rel = Path(path_text)
    require(not rel.is_absolute() and ".." not in rel.parts, f"{description} path is unsafe")
    require(isinstance(digest, str) and len(digest) == 64 and set(digest) <= SHA256, f"{description} SHA-256 is malformed")
    path = root / rel
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), f"{description} is missing or escaped: {path_text}")
    require(sha_file(path) == digest, f"{description} SHA-256 mismatch: {path_text}")
    return path, {"path": rel.as_posix(), "sha256": digest}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expected_groups(root: Path, tool: str) -> list[str]:
    parent = read_json(root / "reports/releases/v0.9.0/execution-v1/contract.json", "immutable v0.9.0 execution contract")
    groups = parent.get("groups")
    require(isinstance(groups, list), "immutable v0.9.0 contract has no ordered group list")
    result = [row.get("id") for row in groups if isinstance(row, dict) and row.get("tool") == tool]
    require(result and len(result) == len(set(result)) and all(isinstance(item, str) for item in result), f"invalid immutable {tool} group roster")
    return result


def expected_tool(binding: dict[str, Any]) -> dict[str, Any]:
    result = {key: binding[key] for key in ("path", "sha256", "version") if key in binding}
    for key in ("build_identity", "archive_sha256", "binary_sha256"):
        if key in binding:
            result[key] = binding[key]
    return result


def expected_components(executor: Any, bindings: dict[str, Any], tool: str) -> list[dict[str, Any]]:
    aliases = bindings.get("tool_components", {}).get(tool)
    require(isinstance(aliases, list) and aliases and len(aliases) == len(set(aliases)), f"bindings have no exact {tool} component order")
    tools = bindings.get("tool_bindings", {})
    result = []
    for alias in aliases:
        require(alias in tools, f"bindings omit {tool} component {alias}")
        row = executor._tool_binding(tools, alias)
        executor._check_tool_file(row, alias)
        result.append(executor._component_identity(alias, row))
    return result


def validate_envelope_shape(
    envelope: dict[str, Any], *, tool_name: str, groups: list[str],
    tool: dict[str, Any], components: list[dict[str, Any]],
) -> None:
    require(envelope.get("schema") == OUTER_SCHEMA, f"{tool_name} envelope schema mismatch")
    require(envelope.get("tool_name") == tool_name, f"{tool_name} envelope tool name mismatch")
    require(envelope.get("status") == "measurement-with-known-limits", f"{tool_name} Swift status must preserve known limits")
    require(envelope.get("execution_eligible") is True, f"{tool_name} Swift group eligibility must be explicit")
    require(envelope.get("groups") == groups, f"{tool_name} qualification group order/scope mismatch")
    require(envelope.get("tool") == tool, f"{tool_name} envelope tool identity differs from the current binding")
    require(envelope.get("identity_components") == components, f"{tool_name} component identity/order differs from the current binding")
    require([item.get("name") for item in components] == envelope.get("component_aliases"), f"{tool_name} component alias order mismatch")
    evidence = envelope.get("evidence")
    require(isinstance(evidence, dict), f"{tool_name} evidence summary is missing")
    if tool_name == "codeql":
        swift = evidence.get("swift")
        ordinary = evidence.get("ordinary_query_compatibility")
        require(isinstance(swift, dict) and isinstance(ordinary, dict), "CodeQL evidence summaries are incomplete")
        require(swift.get("status") == "measurement-with-known-limits" and swift.get("execution_eligible") is True,
                "CodeQL Swift controls must retain the known-limits eligible state")
        require(swift.get("control_count") == 22 and swift.get("entry_extractor_controls") == 10 and
                swift.get("model_activation_case_arms") == 4 and swift.get("sanitizer_activation_case_arms") == 8,
                "CodeQL Swift evidence must retain the exact 22-control roster")
        require(swift.get("strict_entry_extractor") is False and swift.get("scored_activation") is False,
                "CodeQL structural limits or unscored activation were overclaimed")
        require(swift.get("query_preflight_count") == 12 and swift.get("query_preflight_status") == "qualified" and
                swift.get("query_preflight_mode") == "resolve-compile-only",
                "CodeQL Swift preflight scope/status mismatch")
        require(ordinary.get("status") == "compatibility-verified" and ordinary.get("query_count") == 26 and
                ordinary.get("resolve_command_count") == 26 and ordinary.get("compile_command_count") == 26 and
                ordinary.get("compile_only") is True and ordinary.get("flow_detection_claimed") is False and
                ordinary.get("activation_qualified") is False and ordinary.get("coverage_qualified") is False and
                ordinary.get("performance_claimed") is False,
                "ordinary CodeQL validation was overclaimed or has incomplete command coverage")
    elif tool_name == "joern":
        swift = evidence.get("swift")
        native = evidence.get("native_review")
        require(isinstance(swift, dict) and isinstance(native, dict), "Joern evidence summaries are incomplete")
        require(swift.get("status") == "measurement-with-known-limits" and swift.get("execution_eligible") is True and
                swift.get("diagnostic_execution_eligible") is True and swift.get("control_case_arms") == 12 and
                swift.get("phase_invocations") == 36,
                "Joern Swift diagnostic control scope/status mismatch")
        require(swift.get("full_model_qualification") is False and swift.get("strict_model_qualification") is False and
                swift.get("scored_activation") is False and swift.get("strict_assessment_status") == "incomplete" and
                swift.get("endpoint_identity_gaps") == 8,
                "Joern Swift endpoint-identity gaps or unscored diagnostic state were overclaimed")
        require(native.get("status") == "measurement-with-known-limits" and native.get("execution_eligible") is False and
                native.get("scan_count") == 36 and native.get("completion_markers") == 0 and
                native.get("cleanliness_claimed") is False and native.get("coverage_claimed") is False,
                "Joern native review limits or missing completion markers were overclaimed")
    else:
        raise BindError(f"unsupported envelope tool: {tool_name}")


def _run_validator(root: Path, argv: list[str], description: str) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as exc:
        raise BindError(f"cannot run {description}: {exc}") from exc
    require(result.returncode == 0, f"{description} failed ({result.returncode}): {result.stderr[-2000:]}")
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BindError(f"{description} did not return JSON") from exc
    require(isinstance(parsed, dict), f"{description} output must be a JSON object")
    return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "result": parsed}


def validate_codeql_ordinary(root: Path, bindings: dict[str, Any]) -> dict[str, Any]:
    directory = root / ORDINARY_DIR
    receipt_path = directory / "receipt.json"
    review_path = directory / "review-01.json"
    receipt = read_json(receipt_path, "ordinary CodeQL query receipt")
    review = read_json(review_path, "ordinary CodeQL query review")
    tool = bindings["tool_bindings"]["codeql"]
    packs_binding = bindings["tool_bindings"]["codeql-packs"]
    packs_manifest = read_json(Path(packs_binding["path"]), "ordinary CodeQL pack-tree manifest")
    pack_root = packs_manifest.get("root")
    require(isinstance(pack_root, str) and Path(pack_root).is_absolute() and Path(pack_root).is_dir() and
            not Path(pack_root).is_symlink(), "ordinary CodeQL pack-tree manifest has no live absolute root")
    require(receipt.get("schema") == "v092-ordinary-codeql-query-checks/v1" and
            receipt.get("status") == "completed-pending-review" and receipt.get("query_count") == 26,
            "ordinary CodeQL receipt is incomplete or has another schema")
    require(receipt.get("tool", {}).get("path") == tool["path"] and receipt["tool"].get("sha256") == tool["sha256"] and
            receipt["tool"].get("version") == tool.get("version") and
            receipt["tool"].get("build_identity") == tool.get("build_identity"),
            "ordinary CodeQL receipt does not bind the current CLI identity")
    require(receipt.get("packs_component") == packs_binding, "ordinary CodeQL receipt does not bind the exact ordinary pack tree")
    checker_path = root / "scripts/check-v092-codeql-queries.py"
    require(receipt.get("implementation_sha256") == sha_file(checker_path), "ordinary CodeQL runner implementation changed")
    require(receipt.get("total_wall_budget_seconds") == 900 and receipt.get("per_command_deadline_seconds") == 120,
            "ordinary CodeQL command budgets differ from the captured run")
    query_root = root / "adapters/codeql/v0.9.2"
    queries = sorted((path.relative_to(root).as_posix() for path in query_root.rglob("*.ql")
                      if path.is_file() and path.relative_to(query_root).parts[0] != "swift"))
    require(len(queries) == 26, "ordinary CodeQL current query roster is not 26")
    rows = receipt.get("queries")
    require(isinstance(rows, list) and len(rows) == 26 and [row.get("path") for row in rows] == queries,
            "ordinary CodeQL receipt query membership/order differs from current 26-query roster")
    resolved = []
    command_count = {"resolve": 0, "compile": 0}
    command_elapsed = 0.0
    for index, (query, row) in enumerate(zip(queries, rows)):
        query_path = root / query
        require(row.get("sha256") == sha_file(query_path), f"ordinary CodeQL query changed: {query}")
        commands = row.get("commands")
        require(isinstance(commands, list) and [item.get("phase") for item in commands] == ["resolve", "compile"],
                f"ordinary CodeQL command phase roster differs: {query}")
        resolve_doc = None
        for phase, command in zip(("resolve", "compile"), commands):
            query_abs = str(query_path.resolve())
            if phase == "resolve":
                expected_argv = [tool["path"], "resolve", "library-path", "--query=" + query_abs,
                                 "--format=json", "--additional-packs=" + pack_root]
            else:
                expected_argv = [tool["path"], "query", "compile", query_abs, "--check-only", "--threads=2",
                                 "--ram=2048", "--additional-packs=" + pack_root]
            require(command.get("argv") == expected_argv and command.get("exit_code") == 0 and
                    command.get("timed_out") is False and command.get("capacity_loss") is None,
                    f"ordinary CodeQL {phase} command failed or differs: {query}")
            duration = command.get("duration_seconds")
            require(type(duration) in (int, float) and 0 <= duration <= 120,
                    f"ordinary CodeQL {phase} command exceeds its deadline: {query}")
            command_elapsed += duration
            command_count[phase] += 1
            stdout_path, stdout_ref = bound_reference(root, command.get("stdout"), f"ordinary CodeQL {phase} stdout")
            stderr_path, _ = bound_reference(root, command.get("stderr"), f"ordinary CodeQL {phase} stderr")
            require(stdout_path.parent == directory and stderr_path.parent == directory,
                    f"ordinary CodeQL {phase} streams escaped their attempt directory: {query}")
            if phase == "resolve":
                resolve_doc = read_json(stdout_path, "ordinary CodeQL resolve output")
                require(command["stdout"]["sha256"] == stdout_ref["sha256"], "ordinary CodeQL resolve stdout binding changed")
        require(isinstance(resolve_doc, dict), f"ordinary CodeQL resolve output missing: {query}")
        lib_path = resolve_doc.get("libraryPath")
        dbscheme = resolve_doc.get("dbscheme")
        qlpack = resolve_doc.get("qlPackName")
        require(isinstance(lib_path, list) and isinstance(dbscheme, str) and isinstance(qlpack, str),
                f"ordinary CodeQL resolve output is incomplete: {query}")
        pack_root_resolved = Path(pack_root).resolve()
        require(any(Path(item).is_absolute() and Path(item).resolve().is_relative_to(pack_root_resolved)
                    for item in lib_path if isinstance(item, str)),
                f"ordinary CodeQL resolution omitted the exact ordinary pack tree: {query}")
        dbscheme_path = Path(dbscheme)
        require(dbscheme_path.is_absolute() and dbscheme_path.is_file() and
                dbscheme_path.resolve().is_relative_to(Path(pack_root).resolve()),
                f"ordinary CodeQL resolution selected an unbound dbscheme: {query}")
        resolved.append({"query": query, "dbscheme": dbscheme, "qlpack": qlpack})
    require(command_count == {"resolve": 26, "compile": 26}, "ordinary CodeQL evidence omits query commands")
    require(type(receipt.get("duration_seconds")) in (int, float) and receipt["duration_seconds"] <= 900 and
            receipt["duration_seconds"] + 0.1 >= command_elapsed,
            "ordinary CodeQL capture duration is inconsistent with retained command times")
    require(review.get("schema") == "v092-ordinary-query-review/v1" and review.get("status") == "compatibility-verified" and
            review.get("query_count") == 26 and review.get("resolved_queries") == resolved,
            "ordinary CodeQL review does not match the 26 retained resolution outputs")
    require(review.get("receipt") == reference(root, receipt_path), "ordinary CodeQL review does not bind its exact receipt")
    limits = [
        "Compile-only checks establish compatibility, not flow detection or completeness.",
        "CodeQL raised the requested2048MiB RAM to its2638MiB minimum; this is not a hard aggregate memory cap.",
    ]
    require(review.get("limits") == limits, "ordinary CodeQL review lost its execution limits")
    return {
        "receipt": reference(root, receipt_path), "review": reference(root, review_path),
        "status": "compatibility-verified", "query_count": 26,
        "resolve_command_count": command_count["resolve"], "compile_command_count": command_count["compile"],
        "compile_only": True, "flow_detection_claimed": False, "activation_qualified": False,
        "coverage_qualified": False, "performance_claimed": False,
        "review_limits": limits,
    }


def validate_native_joern_review(root: Path) -> dict[str, Any]:
    current_review_path = root / NATIVE_REVIEW
    current_review = read_json(current_review_path, "Joern native review")
    replay_script = root / "scripts/review-v092-joern-native.py"
    require(current_review.get("review_implementation") == reference(root, replay_script),
            "Joern native review does not bind its current replay implementation")
    with tempfile.NamedTemporaryFile(prefix=".joern-native-review-replay-", suffix=".json",
                                     dir=root / QUALIFICATION_ROOT, delete=False) as stream:
        temporary_output = Path(stream.name)
    temporary_output.unlink()
    argv = [sys.executable, str(replay_script), "--capture", str(root / NATIVE_CAPTURE), "--output", str(temporary_output)]
    try:
        command = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        require(command.returncode == 0, f"Joern native reviewer failed ({command.returncode}): {command.stderr[-2000:]}")
        replayed = read_json(temporary_output, "replayed Joern native review")
        require(replayed == current_review, "current Joern native replay differs from the retained review-01")
    finally:
        temporary_output.unlink(missing_ok=True)
    require(current_review.get("status") == "measurement-with-known-limits" and
            current_review.get("execution_eligible") is False and len(current_review.get("observations", [])) == 36 and
            current_review.get("completion_markers") == 0,
            "Joern native review status, captured scan count, or completion-marker limitation changed")
    require(any("missing scan completion markers" in item for item in current_review.get("limits", [])) and
            any("Zero emitted findings do not prove cleanliness" in item for item in current_review.get("limits", [])),
            "Joern native review overstates completion or cleanliness")
    return {
        "review": reference(root, current_review_path), "status": current_review["status"],
        "execution_eligible": False, "scan_count": len(current_review["observations"]),
        "completion_markers": current_review["completion_markers"], "cleanliness_claimed": False,
        "coverage_claimed": False, "replay_matches_retained_review": True,
        "replay_command": {"argv": argv, "exit_code": command.returncode,
                           "stdout": command.stdout, "stderr": command.stderr},
        "reviewer": reference(root, replay_script),
    }


def build_codeql_envelope(root: Path, bindings: dict[str, Any], executor: Any) -> dict[str, Any]:
    plan_path = root / CODEQL_PLAN
    plan = read_json(plan_path, "CodeQL Swift plan")
    require(plan.get("status") == "execution-eligible" and plan.get("execution_eligible") is True and
            plan.get("scored_activation") is False, "CodeQL Swift plan is not diagnostic execution-eligible")
    current_plan_ref = reference(root, plan_path)
    validator = _run_validator(root, [sys.executable, "scripts/run-swift-common-v092.py", "verify-plan", "--plan", CODEQL_PLAN.as_posix()],
                               "current CodeQL Swift eligible-plan validator")
    result = validator["result"]
    require(result.get("engine") == "codeql" and result.get("release_group_id") == "codeql-swift-common108" and
            result.get("qualification_status") == "measurement-with-known-limits" and result.get("scored_activation") is False,
            "CodeQL Swift validator returned an unexpected qualification state")
    qualification_path, qualification_ref = bound_reference(root, plan.get("fresh_qualification"), "CodeQL Swift qualification receipt")
    qualification = read_json(qualification_path, "CodeQL Swift qualification receipt")
    require(qualification.get("schema") == "analyzer-qualification-receipt/v092" and
            qualification.get("status") == "measurement-with-known-limits" and
            qualification.get("execution_eligible") is True and
            qualification.get("groups") == ["codeql-swift-common108"],
            "CodeQL Swift qualification receipt lost its bounded eligible state")
    require(qualification.get("identity") == plan.get("identity") and
            qualification.get("identity_components") == plan.get("identity_components") and
            qualification.get("execution_plan_projection_sha256") == plan.get("qualification_control_projection_sha256"),
            "CodeQL Swift receipt does not bind the exact eligible plan identity")
    dimensions = qualification.get("dimensions", {})
    entry = dimensions.get("entry_extractor", {})
    model = dimensions.get("model_activation", {})
    sanitizer = dimensions.get("sanitizer_activation", {})
    query = dimensions.get("query_resolution_compile", {})
    require(entry.get("case_count") == 10 and entry.get("status") == "measurement-with-known-limits" and
            entry.get("execution_eligible") is True and entry.get("assessment", {}).get("strict_qualified") is False,
            "CodeQL entry controls lost their known-limit boundary")
    require(model.get("assessment", {}).get("case_arm_count") == 4 and model.get("status") == "qualified" and
            sanitizer.get("assessment", {}).get("case_arm_count") == 8 and sanitizer.get("status") == "qualified",
            "CodeQL model/sanitizer control dimensions do not match the captured 4/8 arms")
    require(query.get("status") == "qualified" and query.get("query_count") == 12,
            "CodeQL Swift plan lacks its exact 12-query preflight")
    control_ref = plan.get("qualification_control_plan")
    control_path, control_ref = bound_reference(root, control_ref, "CodeQL Swift control plan")
    control = read_json(control_path, "CodeQL Swift control plan")
    control_run_path, control_run_ref = bound_reference(root, qualification.get("control_run"), "CodeQL Swift control run")
    control_run = read_json(control_run_path, "CodeQL Swift control run")
    require(control.get("group_id") == "codeql-swift-common108" and control_run.get("group_id") == "codeql-swift-common108" and
            control_run.get("control_plan_sha256") == control_ref["sha256"],
            "CodeQL Swift control plan/run linkage mismatch")
    ordinary = validate_codeql_ordinary(root, bindings)
    tool_binding = bindings["tool_bindings"]["codeql"]
    components = expected_components(executor, bindings, "codeql")
    groups = expected_groups(root, "codeql")
    evidence = {
        "swift": {
            "plan": current_plan_ref, "control_plan": control_ref,
            "qualification_receipt": qualification_ref, "control_run": control_run_ref,
            "query_preflight_receipt": query.get("receipt"),
            "status": qualification["status"], "execution_eligible": True,
            "control_count": 22, "entry_extractor_controls": 10,
            "model_activation_case_arms": 4, "sanitizer_activation_case_arms": 8,
            "query_preflight_count": 12, "query_preflight_status": "qualified",
            "query_preflight_mode": "resolve-compile-only",
            "strict_entry_extractor": False, "scored_activation": False,
            "replay_validator": {
                "path": "scripts/run-swift-common-v092.py",
                "sha256": sha_file(root / "scripts/run-swift-common-v092.py"),
                "argv": validator["argv"], "exit_code": validator["exit_code"],
                "stdout": validator["stdout"], "stderr": validator["stderr"],
            },
        },
        "ordinary_query_compatibility": ordinary,
    }
    envelope = {
        "schema": OUTER_SCHEMA, "tool_name": "codeql",
        "status": "measurement-with-known-limits", "execution_eligible": True,
        "groups": groups, "tool": expected_tool(tool_binding),
        "identity_components": components,
        "component_aliases": list(bindings["tool_components"]["codeql"]),
        "bindings_draft": reference(root, root / DEFAULT_BINDINGS),
        "evidence": evidence,
        "binding_implementation": reference(root, root / Path(__file__).relative_to(root)),
        "limits": [
            "Swift entry extraction remains measurement-with-known-limits: two registered structural deltas remain, and activation is unscored.",
            "The Swift query preflight covers 12 resolve/compile checks only; ordinary query checks establish compatibility, not flow detection, coverage, or performance.",
            "This envelope authorizes only the listed group attempts; it does not establish completed v0.9.2 report coverage.",
        ],
    }
    validate_envelope_shape(envelope, tool_name="codeql", groups=groups,
                            tool=expected_tool(tool_binding), components=components)
    return envelope


def build_joern_envelope(root: Path, bindings: dict[str, Any], executor: Any) -> dict[str, Any]:
    plan_path = root / JOERN_PLAN
    plan = read_json(plan_path, "Joern Swift plan")
    require(plan.get("status") == "execution-eligible" and plan.get("execution_eligible") is True and
            plan.get("diagnostic_execution_eligible") is True and plan.get("full_model_qualification") is False and
            plan.get("scored_activation") is False, "Joern Swift plan does not preserve diagnostic-only eligibility")
    current_plan_ref = reference(root, plan_path)
    validator = _run_validator(root, [sys.executable, "scripts/run-joern-common-v092.py", "verify-plan", "--plan", JOERN_PLAN.as_posix()],
                               "current Joern Swift eligible-plan validator")
    result = validator["result"]
    require(result.get("group_id") == "joern-swift-common108" and
            result.get("qualification_status") == "measurement-with-known-limits" and
            result.get("scored_activation") is False and result.get("case_count") == 108,
            "Joern Swift validator returned an unexpected qualification state")
    qualification_path, qualification_ref = bound_reference(root, plan.get("fresh_qualification"), "Joern Swift qualification receipt")
    qualification = read_json(qualification_path, "Joern Swift qualification receipt")
    require(qualification.get("schema") == "analyzer-qualification-receipt/v092" and
            qualification.get("status") == "measurement-with-known-limits" and
            qualification.get("execution_eligible") is True and
            qualification.get("groups") == ["joern-swift-common108"] and
            qualification.get("diagnostic_execution_eligible") is True and
            qualification.get("full_model_qualification") is False and qualification.get("scored_activation") is False,
            "Joern Swift qualification receipt overstates its diagnostic scope")
    require(qualification.get("identity") == plan.get("identity") and
            qualification.get("identity_components") == plan.get("identity_components") and
            qualification.get("execution_plan_projection_sha256") == plan.get("qualification_control_projection_sha256"),
            "Joern Swift receipt does not bind the exact eligible plan identity")
    dimension = qualification.get("dimensions", {}).get("common108_controls", {})
    strict = dimension.get("strict_assessment", {})
    failures = strict.get("failures", [])
    require(dimension.get("case_count") == 6 and dimension.get("case_arm_count") == 12 and
            dimension.get("phase_invocation_count") == 36 and dimension.get("full_model_qualification") is False and
            dimension.get("status") == "measurement-with-known-limits" and strict.get("status") == "incomplete" and
            strict.get("absence_completeness") == "unproven" and len(failures) == 8 and
            all(row.get("observed") == "inconclusive" for row in failures),
            "Joern diagnostic receipt flattened one or more endpoint-identity gaps")
    control_ref = plan.get("qualification_control_plan")
    control_path, control_ref = bound_reference(root, control_ref, "Joern Swift control plan")
    control = read_json(control_path, "Joern Swift control plan")
    control_run_path, control_run_ref = bound_reference(root, qualification.get("control_run"), "Joern Swift control run")
    control_run = read_json(control_run_path, "Joern Swift control run")
    require(control.get("group_id") == "joern-swift-common108" and control_run.get("group_id") == "joern-swift-common108" and
            control_run.get("phase_invocation_count") == 36 and control_run.get("scored_activation") is False and
            control_run.get("control_plan_sha256") == control_ref["sha256"],
            "Joern Swift control plan/run linkage mismatch")
    native = validate_native_joern_review(root)
    tool_binding = bindings["tool_bindings"]["joern"]
    components = expected_components(executor, bindings, "joern")
    groups = expected_groups(root, "joern")
    envelope = {
        "schema": OUTER_SCHEMA, "tool_name": "joern",
        "status": "measurement-with-known-limits", "execution_eligible": True,
        "groups": groups, "tool": expected_tool(tool_binding),
        "identity_components": components,
        "component_aliases": list(bindings["tool_components"]["joern"]),
        "bindings_draft": reference(root, root / DEFAULT_BINDINGS),
        "evidence": {
            "swift": {
                "plan": current_plan_ref, "control_plan": control_ref,
                "qualification_receipt": qualification_ref, "control_run": control_run_ref,
                "diagnostic_admission_review": qualification["diagnostic_admission_review"],
                "status": qualification["status"], "execution_eligible": True,
                "diagnostic_execution_eligible": True, "control_case_arms": 12,
                "phase_invocations": 36, "full_model_qualification": False,
                "strict_model_qualification": False, "scored_activation": False,
                "strict_assessment_status": "incomplete", "endpoint_identity_gaps": 8,
                "replay_validator": {
                    "path": "scripts/run-joern-common-v092.py",
                    "sha256": sha_file(root / "scripts/run-joern-common-v092.py"),
                    "argv": validator["argv"], "exit_code": validator["exit_code"],
                    "stdout": validator["stdout"], "stderr": validator["stderr"],
                },
            },
            "native_review": native,
        },
        "binding_implementation": reference(root, root / Path(__file__).relative_to(root)),
        "limits": [
            "Joern Swift diagnostic controls retain eight Incomplete:EndpointIdentity arms; full-model qualification and scored activation remain false.",
            "The independent native review remains execution-ineligible, with zero completion markers across 36 scans; no cleanliness or coverage claim is made.",
            "This envelope authorizes only the listed group attempts; it does not establish completed v0.9.2 report coverage.",
        ],
    }
    validate_envelope_shape(envelope, tool_name="joern", groups=groups,
                            tool=expected_tool(tool_binding), components=components)
    return envelope


def self_check_executor_gate(root: Path, bindings: dict[str, Any], envelopes: dict[str, dict[str, Any]], executor: Any) -> dict[str, Any]:
    groups = []
    qualifications = {}
    for tool, envelope in envelopes.items():
        groups.extend({"id": group_id, "tool": tool} for group_id in envelope["groups"])
    tools = {name: executor._tool_binding(bindings["tool_bindings"], name)
             for name in bindings["tool_bindings"]}
    with tempfile.TemporaryDirectory(prefix=".swift-envelope-selfcheck-", dir=root / QUALIFICATION_ROOT) as temp_text:
        temp_dir = Path(temp_text)
        for tool, envelope in envelopes.items():
            payload = (json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
            temp_file = temp_dir / (tool + ".json")
            temp_file.write_bytes(payload)
            qualifications[tool] = {
                "status": envelope["status"], "execution_eligible": envelope["execution_eligible"],
                "groups": envelope["groups"],
                "evidence": {"path": temp_file.relative_to(root).as_posix(), "sha256": sha_bytes(payload)},
            }
        checked = executor._qualification_gate(
            {"groups": groups, "qualifications": qualifications}, root,
            tools, bindings["tool_components"],
        )
    require(sum(len(value["groups"]) for value in checked.values()) == 31,
            "executor gate self-check did not accept all 31 CodeQL/Joern groups")
    return {"status": "accepted", "group_count": 31, "qualification_gate_tools": sorted(checked)}


def write_append_only(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists() and not path.is_symlink(), f"qualification envelope is append-only: {path}")
    payload = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def bind(root: Path, bindings_path: Path, codeql_output: Path, joern_output: Path) -> dict[str, Any]:
    root = root.resolve()
    bindings_path = bindings_path if bindings_path.is_absolute() else root / bindings_path
    codeql_output = codeql_output if codeql_output.is_absolute() else root / codeql_output
    joern_output = joern_output if joern_output.is_absolute() else root / joern_output
    require(bindings_path == root / DEFAULT_BINDINGS, "only bindings-draft-03.json is registered for Swift envelope binding")
    require(codeql_output.is_relative_to(root) and joern_output.is_relative_to(root), "qualification output escaped repository")
    require(codeql_output != joern_output and not codeql_output.exists() and not joern_output.exists(),
            "Swift qualification envelope outputs are append-only")
    bindings = read_json(bindings_path, "v0.9.2 bindings draft")
    require(bindings.get("schema") == "v092-binding-draft/v1" and bindings.get("status") == "incomplete-not-executable",
            "expected the reviewed incomplete draft-03 bindings")
    executor = load_module("execute_release_v092_for_swift_envelopes", root / "scripts/execute-release-v092.py")
    codeql = build_codeql_envelope(root, bindings, executor)
    joern = build_joern_envelope(root, bindings, executor)
    validate_envelope_shape(codeql, tool_name="codeql", groups=expected_groups(root, "codeql"),
                            tool=expected_tool(bindings["tool_bindings"]["codeql"]),
                            components=codeql["identity_components"])
    validate_envelope_shape(joern, tool_name="joern", groups=expected_groups(root, "joern"),
                            tool=expected_tool(bindings["tool_bindings"]["joern"]),
                            components=joern["identity_components"])
    gate_result = self_check_executor_gate(root, bindings, {"codeql": codeql, "joern": joern}, executor)
    write_append_only(codeql_output, codeql)
    write_append_only(joern_output, joern)
    return {"codeql": {"path": codeql_output.relative_to(root).as_posix(), "sha256": sha_file(codeql_output), "groups": len(codeql["groups"])},
            "joern": {"path": joern_output.relative_to(root).as_posix(), "sha256": sha_file(joern_output), "groups": len(joern["groups"])},
            "executor_gate": gate_result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
    parser.add_argument("--codeql-output", type=Path, default=DEFAULT_CODEQL_OUTPUT)
    parser.add_argument("--joern-output", type=Path, default=DEFAULT_JOERN_OUTPUT)
    args = parser.parse_args(argv)
    result = bind(ROOT, args.bindings, args.codeql_output, args.joern_output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
