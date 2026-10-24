#!/usr/bin/env python3
"""Guarded append-only Joern capability repair successor-03 for v0.9.2.

This module is intentionally a narrow adapter around the retained Joern
runner.  It validates the old plan and its qualification first, checks a
strict repaired-plan delta, and requires a real qualification rebinding for
the repaired projection.  It never edits the retained plan or receipts.

The ``preflight`` command is read-only and does not start Joern.  The
``execute`` command is the only path that invokes the retained runner, and it
does so in an isolated module after all preflight checks have passed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
import sys
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OLD_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
OLD_PLAN_SHA256 = "e5cfd9d5473fd47f54de25d74a6f945c667c086ce471d5f6cdcead797bf9e3ab"
NEW_PLAN_DEFAULT = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-03/execution-plan.json"
EVIDENCE_DEFAULT = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/capability-evidence.json"
RUNNER_PATH = "scripts/joern_normal_runner_v092.py"
RUNNER_SHA256 = "683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4"
REPORTS_PATH = "scripts/joern_normal_reports_v092.py"
REPORTS_SHA256 = "75531186a9091e9e907a2c42388efea0e33d4872787a28fa9fc20b3643131db1"
EXECUTION_OUTPUT_ROOT = "reports/raw/joern-common-v2/current108-v092-04"
CONTROL_CAPTURE_ROOT = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/control-capture-03"
PROJECTION_PATH = "scripts/v092_qualification.py"
PROJECTION_SHA256 = "f673a5b5133c1101e7379fc365a83a47a7525c3daf15efa34a6eed12858e7cb5"
GROUP_ID = "joern-swift-common108"
PLAN_SCHEMA = "joern-common-execution-plan/v092"
EVIDENCE_SCHEMA = "v092-joern-capability-repair-evidence/v1"
PROPOSAL_EVIDENCE_SCHEMA = "v092-joern-capability-evidence-proposal/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PROJECTION_MODULE = "v092_qualification"
UNSUPPORTED_DECISION_SCHEMA = "joern-current108-partition-decision/v1"
UNSUPPORTED_CASE_IDS = frozenset((
    "dfb-taint-swift-native-entrypoint-negative",
    "dfb-taint-swift-native-entrypoint-positive",
    "dfb-taint-swift-native-persistence-negative",
    "dfb-taint-swift-native-persistence-positive",
    "dfb-taint-swift-native-propagator-negative",
    "dfb-taint-swift-native-propagator-positive",
    "dfb-taint-swift-native-sanitizer-negative",
    "dfb-taint-swift-native-sanitizer-positive",
    "dfb-taint-swift-native-source-sink-negative",
    "dfb-taint-swift-native-source-sink-positive",
    "dfb-taint-swift-native-summary-negative",
    "dfb-taint-swift-native-summary-positive",
))

# The runner needs model_mode.  The other two fields are deliberately
# required by the repair contract so a bare off/on guess cannot be admitted.
CAPABILITY_KEYS = frozenset(("identity_gate", "model_mode", "model_status"))
ALLOWED_TOP_LEVEL_DELTA = frozenset((
    "cases",
    "qualification_control_projection_sha256",
    "qualification_control_plan",
    "fresh_qualification",
    "registered_at_unix_seconds",
))

# The shipped Joern launcher clears ambient JVM/classpath injections and then
# supplies a fixed JAVA_OPTS value.  The successor adds one deterministic
# JAVA_TOOL_OPTIONS property for both the bridge JVM and every forked JVM.
# This object is part of every new Unsupported decision; paths are resolved
# relative to the fresh control/attempt namespace at runtime.
JVM_STARTUP_POLICY = {
    "schema": "v092-joern-jvm-startup-policy/v1",
    "java_property": "user.home",
    "option_source": "JAVA_TOOL_OPTIONS",
    "option_template": "-Duser.home={capture_home}",
    "home_relative": "jvm-home",
    "predef_relative": ".scala-repl-pp.sc",
    "predef_expectation": "absent",
    "ambient_options_cleared": [
        "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "CLASSPATH",
    ],
    "retained_java_opts": "-Xmx512m -XX:ActiveProcessorCount=2",
}


def _validate_jvm_startup_policy(value: object) -> dict[str, Any]:
    require(value == JVM_STARTUP_POLICY,
            "decision does not bind the exact reviewed JVM startup policy")
    return copy.deepcopy(JVM_STARTUP_POLICY)


class RepairError(ValueError):
    """A repair input failed a fail-closed admission check."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RepairError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    try:
        return sha_bytes(path.read_bytes())
    except OSError as exc:
        raise RepairError(f"cannot hash {path}: {exc}") from exc


def _json(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RepairError(f"cannot read {description} {path}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be a JSON object: {path}")
    return value


def _relative_path(root: Path, value: str, description: str) -> Path:
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts, f"{description} must be a safe relative path")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()), f"{description} escaped the repository")
    return resolved


def _load_bound(root: Path, reference: object, description: str) -> tuple[Path, dict[str, Any]]:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
            f"{description} must be an exact path/SHA reference")
    path_text = reference.get("path")
    digest = reference.get("sha256")
    require(isinstance(path_text, str) and isinstance(digest, str) and SHA256.fullmatch(digest),
            f"{description} has malformed path/SHA")
    path = _relative_path(root, path_text, description)
    require(path.is_file() and not path.is_symlink(), f"{description} is missing: {path_text}")
    require(sha(path) == digest, f"{description} digest mismatch: {path_text}")
    return path, _json(path, description)


def _load_runner(root: Path) -> ModuleType:
    path = _relative_path(root, RUNNER_PATH, "immutable Joern runner")
    require(path.is_file() and not path.is_symlink(), "immutable Joern runner is missing")
    require(sha(path) == RUNNER_SHA256, "immutable Joern runner digest changed")
    scripts = str(path.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("joern_normal_runner_v092_repair_pinned", path)
    require(spec is not None and spec.loader is not None, "cannot load immutable Joern runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_projection_module(root: Path) -> ModuleType:
    path = _relative_path(root, PROJECTION_PATH, "qualification projection module")
    require(path.is_file() and not path.is_symlink(), "qualification projection module is missing")
    require(sha(path) == PROJECTION_SHA256, "qualification projection module digest changed")
    scripts = str(path.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    module = sys.modules.get(PROJECTION_MODULE)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(PROJECTION_MODULE, path)
    require(spec is not None and spec.loader is not None, "cannot load qualification projection module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[PROJECTION_MODULE] = module
    spec.loader.exec_module(module)
    return module


def _require_sha_reference(root: Path, reference: object, description: str) -> Path:
    path, _ = _load_bound(root, reference, description)
    return path


def _capability(value: object, description: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{description} must be an object")
    require(set(value) == CAPABILITY_KEYS, f"{description} must contain exactly identity_gate/model_mode/model_status")
    require(isinstance(value["identity_gate"], str) and value["identity_gate"], f"{description} identity_gate is missing")
    require(value["model_mode"] in ("off", "on"), f"{description} model_mode must be explicit off/on")
    require(isinstance(value["model_status"], str) and value["model_status"], f"{description} model_status is missing")
    return copy.deepcopy(value)


def _load_reference_bytes(root: Path, reference: object, description: str) -> Path:
    """Validate a raw evidence reference without assuming it is JSON."""
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
            f"{description} must be an exact path/SHA reference")
    path_text = reference.get("path")
    digest = reference.get("sha256")
    require(isinstance(path_text, str) and isinstance(digest, str) and SHA256.fullmatch(digest),
            f"{description} has malformed path/SHA")
    path = _relative_path(root, path_text, description)
    require(path.is_file() and not path.is_symlink(), f"{description} is missing: {path_text}")
    require(sha(path) == digest, f"{description} digest mismatch: {path_text}")
    return path


def _validate_current_case_and_fixtures(root: Path, decision: dict[str, Any],
                                        evidence: list[Any], case_id: str) -> None:
    """Bind the decision to the exact current case.json and declared fixtures."""
    case_refs: list[tuple[Path, object]] = []
    for index, evidence_ref in enumerate(evidence):
        path = _load_reference_bytes(root, evidence_ref,
                                     f"unsupported decision evidence {case_id}[{index}]")
        if path.name == "case.json":
            case_refs.append((path, evidence_ref))
    require(len(case_refs) == 1,
            f"unsupported decision must bind exactly one current case.json: {case_id}")
    case_path, case_ref = case_refs[0]
    case_value = _json(case_path, f"current case for {case_id}")
    require(case_value.get("schema_version") == 2 and case_value.get("id") == case_id,
            f"unsupported decision current case identity changed: {case_id}")
    require(sha(case_path) == decision.get("current_case_sha256") and
            case_ref.get("sha256") == decision.get("current_case_sha256"),
            f"unsupported decision current case digest is not the case.json digest: {case_id}")
    fixture_files = case_value.get("fixture_files")
    require(isinstance(fixture_files, list) and fixture_files and
            all(isinstance(item, str) and item for item in fixture_files),
            f"current case fixture_files are missing: {case_id}")
    normalized_fixture_files: list[str] = []
    for fixture_name in fixture_files:
        fixture_path = PurePosixPath(fixture_name)
        require(not fixture_path.is_absolute() and ".." not in fixture_path.parts and
                fixture_path.as_posix() == fixture_name,
                f"current case fixture path is unsafe: {case_id}")
        normalized_fixture_files.append(fixture_name)
    if "fixture_files" in decision:
        require(decision.get("fixture_files") == normalized_fixture_files,
                f"unsupported decision fixture mapping changed: {case_id}")
    fixture_digests = decision.get("current_fixture_digests")
    require(isinstance(fixture_digests, list) and
            len(fixture_digests) == len(normalized_fixture_files),
            f"unsupported decision fixture mapping is incomplete: {case_id}")
    observed: list[str] = []
    for index, (fixture_name, fixture_ref) in enumerate(
            zip(normalized_fixture_files, fixture_digests)):
        fixture_path = _load_reference_bytes(
            root, fixture_ref,
            f"unsupported decision fixture {case_id}[{index}]")
        require(fixture_path.is_relative_to(case_path.parent),
                f"unsupported decision fixture is outside its case directory: {case_id}")
        relative = fixture_path.relative_to(case_path.parent).as_posix()
        require(relative == fixture_name,
                f"unsupported decision fixture mapping does not match case.json: {case_id}")
        observed.append(relative)
    require(observed == normalized_fixture_files,
            f"unsupported decision fixture ordering changed: {case_id}")


def _startup_output_path(root: Path, value: str) -> Path:
    """Resolve a fresh capture or execute output inside an authorized prefix."""
    raw = Path(value)
    require(not raw.is_absolute() and ".." not in raw.parts,
            "Joern startup output must be a safe relative path")
    lexical = root / raw
    cursor = root
    for part in raw.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(),
                "Joern startup output contains a symlinked path component")
    resolved = lexical.resolve()
    require(resolved.is_relative_to(root.resolve()),
            "Joern startup output escaped the repository")
    allowed = (root / CONTROL_CAPTURE_ROOT, root / EXECUTION_OUTPUT_ROOT)
    require(any(resolved == prefix or resolved.is_relative_to(prefix)
                for prefix in allowed),
            "Joern startup output is outside the authorized capture/execute namespaces")
    return resolved


def _validate_unsupported_decision(root: Path, reference: object, case_id: str,
                                   old_plan: dict[str, Any]) -> None:
    """Validate one fresh current-identity Unsupported decision.

    Unsupported rows are deliberately data-bound: this adapter may validate an
    independently reviewed decision, but it cannot infer one from an old
    distribution, a missing field, or a runner exception.
    """
    decision_path, decision = _load_bound(root, reference, f"unsupported decision for {case_id}")
    require(decision.get("schema") == UNSUPPORTED_DECISION_SCHEMA,
            f"unsupported decision schema is wrong: {case_id}")
    require(decision.get("case_id") == case_id,
            f"unsupported decision case identity changed: {case_id}")
    require(decision.get("population_sha256") == old_plan.get("population_sha256"),
            f"unsupported decision population changed: {case_id}")
    require(decision.get("fixture_revision") == old_plan.get("fixture_revision"),
            f"unsupported decision fixture revision changed: {case_id}")
    require(decision.get("identity") == old_plan.get("identity"),
            f"unsupported decision Joern identity changed: {case_id}")
    _validate_jvm_startup_policy(decision.get("jvm_startup_policy"))
    require(decision.get("outcome") == "unsupported",
            f"unsupported decision outcome is not explicit: {case_id}")
    require(isinstance(decision.get("reason"), str) and decision["reason"].strip(),
            f"unsupported decision reason is missing: {case_id}")
    evidence = decision.get("evidence")
    require(isinstance(evidence, list) and evidence,
            f"unsupported decision evidence is empty: {case_id}")
    for index, evidence_ref in enumerate(evidence):
        _load_reference_bytes(root, evidence_ref,
                              f"unsupported decision evidence {case_id}[{index}]")
    require(isinstance(decision.get("current_case_sha256"), str) and
            SHA256.fullmatch(decision["current_case_sha256"]),
            f"unsupported decision current case digest is missing: {case_id}")
    _validate_current_case_and_fixtures(root, decision, evidence, case_id)
    # The decision file itself must remain a regular non-symlink source input.
    require(decision_path.is_file() and not decision_path.is_symlink(),
            f"unsupported decision path is not a regular file: {case_id}")


def _evidence_cases(root: Path, evidence: dict[str, Any], old_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    attempted = {case_id for case_id, row in old_plan.get("cases", {}).items()
                 if isinstance(row, dict) and row.get("disposition") == "attempt"}
    if evidence.get("schema") == EVIDENCE_SCHEMA:
        require(evidence.get("status") in {"independently-reviewed", "approved"},
                "capability evidence is not independently reviewed")
        base = evidence.get("base_plan")
        require(isinstance(base, dict), "capability evidence must bind the retained base plan")
        require(base.get("path") == OLD_PLAN_PATH and base.get("sha256") == OLD_PLAN_SHA256,
                "capability evidence is bound to a different base plan")
        population = evidence.get("population_sha256")
        fixture = evidence.get("fixture_revision")
        rows = evidence.get("cases")
        require(isinstance(rows, dict), "capability evidence cases must be an object")
        require(population == old_plan.get("population_sha256") and fixture == old_plan.get("fixture_revision"),
                "capability evidence population or fixture identity changed")
    elif evidence.get("schema") == PROPOSAL_EVIDENCE_SCHEMA:
        # The evidence agent's proposal is accepted as a source mapping, while
        # its status remains visible to the caller.  The continuation's
        # independent review and control rebinding are still mandatory before
        # execution; this branch never promotes the proposal to qualification.
        source = evidence.get("provenance", {}).get("current_v092_execution_plan", {})
        require(source.get("path") == OLD_PLAN_PATH and source.get("sha256") == OLD_PLAN_SHA256,
                "capability proposal is bound to a different base plan")
        population = source.get("population_sha256")
        fixture = source.get("fixture_revision")
        require(population == old_plan.get("population_sha256") and fixture == old_plan.get("fixture_revision"),
                "capability proposal population or fixture identity changed")
        required = evidence.get("capability_value_provenance", {}).get("per_case_required_capability")
        raw = evidence.get("historical_raw_evidence", {}).get("case_reports")
        require(isinstance(required, dict) and isinstance(raw, dict),
                "capability proposal lacks its reviewed value or raw case mapping")
        require(evidence.get("roster_validation", {}).get("attempt_case_set_exact_match") is True and
                evidence.get("roster_validation", {}).get("unsupported_count") == 12,
                "capability proposal roster is not the reviewed 96/12 split")
        rows = {}
        for case_id, row in raw.items():
            require(isinstance(row, dict), f"capability proposal raw mapping is malformed: {case_id}")
            raw_path, raw_value = _load_bound(root, {"path": row.get("path"), "sha256": row.get("sha256")},
                                              f"historical raw capability source for {case_id}")
            require(raw_value.get("capability") == required and raw_value.get("executed") is True,
                    f"capability proposal raw evidence does not prove the reviewed value: {case_id}")
            require(raw_value.get("plan_sha256") == evidence["provenance"]["historical_case_capability_source"]["sha256"] and
                    raw_value.get("population_sha256") == population and
                    raw_value.get("fixture_revision") == fixture and
                    raw_value.get("execution_contract_sha256") == evidence["provenance"]["execution_contract"]["sha256"],
                    f"capability proposal raw evidence identity changed: {case_id}")
            rows[case_id] = {
                "capability": raw_value["capability"],
                "source_ref": {"path": raw_path.relative_to(root).as_posix(), "sha256": row["sha256"]},
                "provenance": "historical raw capability source; Joern 4.0.628 provenance retained",
            }
        require(evidence.get("capability_value_provenance", {}).get("values_are_case_copied") is True,
                "capability proposal is not explicitly case-copied")
    else:
        raise RepairError("capability evidence schema is not a supported reviewed repair schema")
    require(set(rows) == attempted, "capability evidence must cover exactly the 96 attempted cases")
    result: dict[str, dict[str, Any]] = {}
    for case_id, row in rows.items():
        require(isinstance(row, dict), f"capability evidence row is malformed: {case_id}")
        result[case_id] = _capability(row.get("capability"), f"capability evidence {case_id}")
        source_ref = row.get("source_ref")
        _require_sha_reference(root, source_ref, f"capability evidence source for {case_id}")
        provenance = row.get("provenance")
        require(isinstance(provenance, str) and provenance.strip(), f"capability evidence provenance is missing: {case_id}")
    return result


def _projection(root: Path, plan: dict[str, Any]) -> str:
    module = _load_projection_module(root)
    try:
        value = module.plan_projection_sha256(plan)
    except (ValueError, KeyError, TypeError) as exc:
        raise RepairError(f"cannot calculate repaired qualification projection: {exc}") from exc
    require(isinstance(value, str) and SHA256.fullmatch(value), "qualification projection digest is malformed")
    return value


def _strict_plan_delta(
    root: Path,
    old_plan: dict[str, Any],
    new_plan: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    *,
    allow_qualification_pending: bool = False,
) -> str:
    require(new_plan.get("schema") == PLAN_SCHEMA, "repaired Joern plan schema is wrong")
    require(new_plan.get("engine") == "joern" and new_plan.get("release_group_id") == GROUP_ID,
            "repaired Joern plan identity is wrong")
    if allow_qualification_pending:
        require(new_plan.get("status") in {"qualification-pending", "execution-eligible"},
                "repaired Joern bootstrap plan has an invalid status")
        if new_plan.get("status") == "qualification-pending":
            require(new_plan.get("execution_eligible") is False and
                    new_plan.get("diagnostic_execution_eligible") is False,
                    "qualification-pending Joern bootstrap plan has invalid eligibility")
        else:
            require(new_plan.get("execution_eligible") is True,
                    "repaired Joern plan is not execution eligible")
    else:
        require(new_plan.get("status") == "execution-eligible" and new_plan.get("execution_eligible") is True,
                "repaired Joern plan is not execution eligible")
    require(new_plan.get("scored_activation") is False and
            new_plan.get("full_model_qualification") is False and
            new_plan.get("aggregate_resource_qualification") == "unavailable",
            "repaired Joern plan changed typed qualification limits")
    require(set(new_plan) - set(old_plan) == set(), "repaired Joern plan added unreviewed top-level fields")
    changed = {key for key in set(old_plan) | set(new_plan) if old_plan.get(key) != new_plan.get(key)}
    allowed_delta = ALLOWED_TOP_LEVEL_DELTA | ({"status", "execution_eligible", "diagnostic_execution_eligible"}
                                                if allow_qualification_pending else set())
    require(changed <= allowed_delta,
            "repaired Joern plan changed fields outside capabilities/projection/requalification: " + ", ".join(sorted(changed - allowed_delta)))
    require(new_plan.get("qualification_control_plan") != old_plan.get("qualification_control_plan"),
            "repaired plan must bind a new qualification control plan")
    require(new_plan.get("fresh_qualification") != old_plan.get("fresh_qualification"),
            "repaired plan must bind a new qualification receipt")
    old_cases, new_cases = old_plan.get("cases"), new_plan.get("cases")
    require(isinstance(old_cases, dict) and isinstance(new_cases, dict) and set(old_cases) == set(new_cases),
            "repaired Joern plan changed the 108-case projection")
    require(len(new_cases) == 108, "repaired Joern plan must retain exactly 108 cases")
    for case_id, old_row in old_cases.items():
        new_row = new_cases[case_id]
        require(isinstance(old_row, dict) and isinstance(new_row, dict), f"case row is malformed: {case_id}")
        disposition = old_row.get("disposition")
        if disposition == "attempt":
            require(set(new_row) == set(old_row) | {"capability"}, f"attempt case delta is not capability-only: {case_id}")
            require(all(new_row.get(key) == value for key, value in old_row.items()),
                    f"attempt case pre-existing fields changed: {case_id}")
            require(new_row.get("capability") == evidence[case_id], f"plan capability does not match reviewed evidence: {case_id}")
        elif disposition == "unsupported":
            require(case_id in UNSUPPORTED_CASE_IDS,
                    f"unknown unsupported case roster entry: {case_id}")
            require(set(new_row) == set(old_row) | {"decision"},
                    f"unsupported case delta must add only decision: {case_id}")
            require(all(new_row.get(key) == value for key, value in old_row.items()),
                    f"unsupported case pre-existing fields changed: {case_id}")
            _validate_unsupported_decision(root, new_row.get("decision"), case_id, old_plan)
        else:
            raise RepairError(f"unknown retained case disposition: {case_id}")
    require({case_id for case_id, row in new_cases.items()
             if row.get("disposition") == "unsupported"} == UNSUPPORTED_CASE_IDS,
            "successor unsupported roster changed")
    projection = _projection(root, new_plan)
    require(new_plan.get("qualification_control_projection_sha256") == projection,
            "repaired plan projection digest is not truthful")
    require(projection != old_plan.get("qualification_control_projection_sha256"),
            "repaired plan projection did not change despite capability repair")
    return projection


def _validate_control_plan_binding(root: Path, old_plan: dict[str, Any], new_plan: dict[str, Any], projection: str) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    old_control_path, old_control = _load_bound(root, old_plan.get("qualification_control_plan"), "retained qualification control plan")
    new_control_path, new_control = _load_bound(root, new_plan.get("qualification_control_plan"), "repaired qualification control plan")
    require(new_control_path != old_control_path, "repaired qualification control plan reused the retained path")
    require(new_control.get("schema") == "analyzer-qualification-control-plan/v092" and
            new_control.get("group_id") == GROUP_ID, "repaired qualification control plan identity is wrong")
    require(new_control.get("execution_plan_projection_sha256") == projection,
            "repaired control plan does not bind the repaired projection")
    for field in ("controls", "arms", "case_arm_count", "maximum_phase_invocations", "case_arm_budget_seconds",
                  "total_budget_seconds", "scratch_allowance_bytes", "population_sha256", "fixture_revision",
                  "identity", "identity_components"):
        require(new_control.get(field) == old_control.get(field), f"control harness input changed: {field}")
    return old_control_path, old_control, new_control_path, new_control


def _validate_requalification(root: Path, old_plan: dict[str, Any], new_plan: dict[str, Any], projection: str) -> dict[str, Any]:
    old_control_path, old_control, new_control_path, new_control = _validate_control_plan_binding(root, old_plan, new_plan, projection)
    _, old_receipt = _load_bound(root, old_plan.get("fresh_qualification"), "retained qualification receipt")
    _, receipt = _load_bound(root, new_plan.get("fresh_qualification"), "repaired qualification receipt")
    require(receipt.get("schema") == "analyzer-qualification-receipt/v092" and receipt.get("group_id") == GROUP_ID,
            "repaired qualification receipt identity is wrong")
    require(receipt.get("execution_plan_projection_sha256") == projection,
            "repaired qualification receipt does not bind the repaired projection")
    require(receipt.get("control_run") is not None, "repaired qualification receipt lacks a control run")
    _, old_run = _load_bound(root, old_receipt.get("control_run"), "retained qualification control run")
    _, run = _load_bound(root, receipt.get("control_run"), "repaired qualification control run")
    require(run.get("schema") == "analyzer-qualification-control-run/v092" and run.get("group_id") == GROUP_ID,
            "repaired qualification control run identity is wrong")
    require(run.get("execution_plan_projection_sha256") == projection,
            "repaired qualification control run does not bind the repaired projection")
    require(run.get("control_plan_sha256") == new_plan["qualification_control_plan"]["sha256"],
            "repaired control run does not bind the repaired control plan")
    require(run.get("phase_invocation_count") == 36 and isinstance(run.get("records"), list) and len(run["records"]) == 12,
            "repaired control run is not the complete six-fixture off/on capture")
    _validate_control_command_equivalence(root, old_run, run)
    require(receipt.get("identity") == new_plan.get("identity") and
            receipt.get("identity_components") == new_plan.get("identity_components"),
            "repaired qualification receipt has stale runtime identity")
    return {"control_plan": new_control_path.relative_to(root).as_posix(), "projection": projection,
            "control_run": receipt["control_run"]["path"], "receipt": new_plan["fresh_qualification"]["path"]}


def _normalise_capture_path(value: object, old_capture: str, new_capture: str) -> object:
    if not isinstance(value, str):
        return value
    return value.replace(old_capture, "<control-capture>").replace(new_capture, "<control-capture>")


def _command_input_signature(command: dict[str, Any], old_capture: str, new_capture: str) -> dict[str, Any]:
    """Return only command inputs; timings, PIDs, and output witnesses are excluded."""
    return {
        "argv": [_normalise_capture_path(value, old_capture, new_capture) for value in command.get("argv", [])],
        "cwd": _normalise_capture_path(command.get("cwd"), old_capture, new_capture),
        "environment": command.get("environment"),
        "measurement_wrapper": command.get("measurement_wrapper"),
        "phase_id": command.get("phase_id"),
        "role": command.get("role"),
        "deadline_scope": command.get("deadline_scope"),
    }


def _validate_control_command_equivalence(root: Path, old_run: dict[str, Any], new_run: dict[str, Any]) -> None:
    """Prove the fresh control capture changed projection, not command inputs."""
    old_records = old_run.get("records")
    new_records = new_run.get("records")
    require(isinstance(old_records, list) and isinstance(new_records, list),
            "control runs lack command records for equivalence proof")
    def key(row: object) -> tuple[object, object, object]:
        require(isinstance(row, dict), "control run record is malformed")
        return row.get("control"), row.get("case_id"), row.get("arm")
    old_by_key = {key(row): row for row in old_records}
    new_by_key = {key(row): row for row in new_records}
    require(set(old_by_key) == set(new_by_key) and len(old_by_key) == 12,
            "repaired control run changed the twelve control arms")
    for record_key, old_record in old_by_key.items():
        new_record = new_by_key[record_key]
        old_raw_path, old_raw = _load_bound(root, old_record.get("raw"), f"retained control raw {record_key}")
        new_raw_path, new_raw = _load_bound(root, new_record.get("raw"), f"repaired control raw {record_key}")
        require(old_raw_path != new_raw_path, f"repaired control reused retained raw path: {record_key}")
        require(old_raw.get("case_id") == new_raw.get("case_id") == record_key[1] and
                old_raw.get("control") == new_raw.get("control") == record_key[0] and
                old_raw.get("arm") == new_raw.get("arm") == record_key[2],
                f"control raw identity changed: {record_key}")
        old_capture = str(old_raw.get("capture_directory", ""))
        new_capture = str(new_raw.get("capture_directory", ""))
        require(old_capture and new_capture and old_capture != new_capture,
                f"control capture roots were not fresh: {record_key}")
        old_commands = old_raw.get("commands")
        new_commands = new_raw.get("commands")
        require(isinstance(old_commands, list) and isinstance(new_commands, list) and len(old_commands) == len(new_commands),
                f"control phase count changed: {record_key}")
        for old_ref, new_ref in zip(old_commands, new_commands):
            _, old_command = _load_bound(root, old_ref, f"retained command {record_key}")
            _, new_command = _load_bound(root, new_ref, f"repaired command {record_key}")
            require(_command_input_signature(old_command, old_capture, new_capture) ==
                    _command_input_signature(new_command, old_capture, new_capture),
                    f"control command input changed: {record_key}")


def validate_repair_inputs(
    root: Path,
    *,
    new_plan_path: str = NEW_PLAN_DEFAULT,
    evidence_path: str = EVIDENCE_DEFAULT,
    expected_new_plan_sha256: str | None = None,
    expected_evidence_sha256: str | None = None,
    runner_module: ModuleType | None = None,
) -> dict[str, Any]:
    """Validate all repair inputs without launching an analyzer."""
    root = Path(root).resolve()
    old_path = _relative_path(root, OLD_PLAN_PATH, "retained Joern plan")
    require(old_path.is_file() and not old_path.is_symlink(), "retained Joern plan is missing")
    require(sha(old_path) == OLD_PLAN_SHA256, "retained Joern plan digest changed")
    runner = _load_runner(root) if runner_module is None else runner_module

    # This call deliberately precedes every repaired-plan read.  The returned
    # plan is checked against the exact bytes whose SHA was pinned above.
    try:
        old_result = runner.validate_plan(root, OLD_PLAN_PATH)
    except Exception as exc:  # runner uses ValueError; preserve a stable API
        raise RepairError(f"retained Joern plan validation failed: {exc}") from exc
    old_plan = _json(old_path, "retained Joern plan")
    require(old_result and old_result[0] == old_plan, "immutable runner validated a different retained plan")

    evidence_file = _relative_path(root, evidence_path, "capability evidence")
    require(evidence_file.is_file() and not evidence_file.is_symlink(), "capability evidence is missing")
    evidence_digest = sha(evidence_file)
    if expected_evidence_sha256 is not None:
        require(SHA256.fullmatch(expected_evidence_sha256) and evidence_digest == expected_evidence_sha256,
                "capability evidence digest does not match its contract")
    evidence = _json(evidence_file, "capability evidence")
    evidence_cases = _evidence_cases(root, evidence, old_plan)

    new_path = _relative_path(root, new_plan_path, "repaired Joern plan")
    require(new_path.is_file() and not new_path.is_symlink(), "repaired Joern plan is missing")
    require(new_path != old_path, "repaired Joern plan must be a new path")
    new_digest = sha(new_path)
    if expected_new_plan_sha256 is not None:
        require(SHA256.fullmatch(expected_new_plan_sha256) and new_digest == expected_new_plan_sha256,
                "repaired Joern plan digest does not match its contract")
    new_plan = _json(new_path, "repaired Joern plan")
    projection = _strict_plan_delta(root, old_plan, new_plan, evidence_cases)
    rebinding = _validate_requalification(root, old_plan, new_plan, projection)
    return {
        "runner": runner,
        "old_plan": old_plan,
        "old_plan_sha256": OLD_PLAN_SHA256,
        "new_plan": new_plan,
        "new_plan_path": new_path.relative_to(root).as_posix(),
        "new_plan_sha256": new_digest,
        "evidence_path": evidence_file.relative_to(root).as_posix(),
        "evidence_sha256": evidence_digest,
        "projection_sha256": projection,
        "requalification": rebinding,
    }


def validate_bootstrap_inputs(
    root: Path,
    *,
    new_plan_path: str = NEW_PLAN_DEFAULT,
    evidence_path: str = EVIDENCE_DEFAULT,
    expected_new_plan_sha256: str | None = None,
    expected_evidence_sha256: str | None = None,
    runner_module: ModuleType | None = None,
) -> dict[str, Any]:
    """Validate a qualification-pending repaired plan before fresh controls.

    The pending plan may omit ``fresh_qualification``.  It still needs the
    new projection and a complete new control-plan binding; the actual
    receipt/run are produced only by the guarded ``controls`` command.
    """
    root = Path(root).resolve()
    old_path = _relative_path(root, OLD_PLAN_PATH, "retained Joern plan")
    require(old_path.is_file() and not old_path.is_symlink(), "retained Joern plan is missing")
    require(sha(old_path) == OLD_PLAN_SHA256, "retained Joern plan digest changed")
    runner = _load_runner(root) if runner_module is None else runner_module
    try:
        old_result = runner.validate_plan(root, OLD_PLAN_PATH)
    except Exception as exc:
        raise RepairError(f"retained Joern plan validation failed: {exc}") from exc
    old_plan = _json(old_path, "retained Joern plan")
    require(old_result and old_result[0] == old_plan, "immutable runner validated a different retained plan")

    evidence_file = _relative_path(root, evidence_path, "capability evidence")
    require(evidence_file.is_file() and not evidence_file.is_symlink(), "capability evidence is missing")
    evidence_digest = sha(evidence_file)
    if expected_evidence_sha256 is not None:
        require(SHA256.fullmatch(expected_evidence_sha256) and evidence_digest == expected_evidence_sha256,
                "capability evidence digest does not match its contract")
    evidence_cases = _evidence_cases(root, _json(evidence_file, "capability evidence"), old_plan)

    new_path = _relative_path(root, new_plan_path, "repaired Joern plan")
    require(new_path.is_file() and not new_path.is_symlink() and new_path != old_path,
            "repaired Joern bootstrap plan is missing or reuses the retained path")
    new_digest = sha(new_path)
    if expected_new_plan_sha256 is not None:
        require(SHA256.fullmatch(expected_new_plan_sha256) and new_digest == expected_new_plan_sha256,
                "repaired Joern plan digest does not match its contract")
    new_plan = _json(new_path, "repaired Joern bootstrap plan")
    projection = _strict_plan_delta(root, old_plan, new_plan, evidence_cases, allow_qualification_pending=True)
    _validate_control_plan_binding(root, old_plan, new_plan, projection)
    return {
        "runner": runner,
        "old_plan": old_plan,
        "old_plan_sha256": OLD_PLAN_SHA256,
        "new_plan": new_plan,
        "new_plan_path": new_path.relative_to(root).as_posix(),
        "new_plan_sha256": new_digest,
        "evidence_path": evidence_file.relative_to(root).as_posix(),
        "evidence_sha256": evidence_digest,
        "projection_sha256": projection,
    }


def _assert_canonical_historical_binding(root: Path) -> None:
    """Keep diagnostic admission's historical archive bound to plan-v092-01."""
    scripts = str(_relative_path(root, "scripts", "script root"))
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import joern_normal_runner_v092 as canonical_runner
    require(canonical_runner.EXECUTION_PLAN_PATH == OLD_PLAN_PATH,
            "historical diagnostic admission runner was rebound to the repaired plan")


def preflight(root: Path, **kwargs: Any) -> dict[str, Any]:
    """Run repair validation only; this function never invokes Joern."""
    result = validate_repair_inputs(root, **kwargs)
    runner = result["runner"]
    _assert_canonical_historical_binding(Path(root).resolve())
    old_constant = getattr(runner, "EXECUTION_PLAN_PATH", None)
    try:
        runner.EXECUTION_PLAN_PATH = result["new_plan_path"]
        try:
            checked, _evidence, _context = runner.validate_plan(root, result["new_plan_path"])
        except Exception as exc:
            raise RepairError(f"repaired Joern plan validation failed: {exc}") from exc
        require(checked == result["new_plan"], "immutable runner returned a different repaired plan")
    finally:
        if old_constant is not None:
            runner.EXECUTION_PLAN_PATH = old_constant
    return {key: value for key, value in result.items() if key != "runner"}


def execute(root: Path, output: str, *, startup_policy: object | None = None,
            **kwargs: Any) -> dict[str, Any]:
    """Execute Joern only after validation and the reviewed JVM startup bind."""
    require(startup_policy is not None,
            "Joern execution requires the reviewed JVM startup policy")
    result = validate_repair_inputs(root, **kwargs)
    runner = result["runner"]
    _assert_canonical_historical_binding(Path(root).resolve())
    old_constant = getattr(runner, "EXECUTION_PLAN_PATH", None)
    try:
        runner.EXECUTION_PLAN_PATH = result["new_plan_path"]
        run = _run_with_startup_policy(
            root, output, startup_policy,
            lambda output_path: runner.execute(
                Path(root).resolve(), result["new_plan_path"], output_path
            ),
            runner,
        )
        reports_path = _relative_path(Path(root).resolve(), REPORTS_PATH, "immutable Joern reports exporter")
        require(reports_path.is_file() and not reports_path.is_symlink() and sha(reports_path) == REPORTS_SHA256,
                "immutable Joern reports exporter digest changed")
        scripts = str(reports_path.parent)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        spec = importlib.util.spec_from_file_location("joern_normal_reports_v092_repair_pinned", reports_path)
        require(spec is not None and spec.loader is not None, "cannot load immutable Joern reports exporter")
        reports = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reports)
        normal_output = _relative_path(Path(root).resolve(), str(Path(output) / "normal"), "Joern report output")
        reports.export(Path(root).resolve(), result["new_plan_path"], run, normal_output)
    finally:
        if old_constant is not None:
            runner.EXECUTION_PLAN_PATH = old_constant
    return run


def _startup_home(root: Path, output: Path, policy: object) -> tuple[Path, Path]:
    """Create the isolated Java home and prove the reviewed predef is absent."""
    checked = _validate_jvm_startup_policy(policy)
    output = output.resolve()
    require(output.is_relative_to(root.resolve()),
            "JVM startup output escaped the repository")
    allowed = (root / CONTROL_CAPTURE_ROOT, root / EXECUTION_OUTPUT_ROOT)
    require(any(output == prefix or output.is_relative_to(prefix)
                for prefix in allowed),
            "JVM startup home must remain in an authorized capture/execute namespace")
    home = output / checked["home_relative"]
    require(not home.is_symlink() and (not home.exists() or home.is_dir()),
            "JVM startup home is not a fresh directory")
    home.mkdir(parents=True, exist_ok=True)
    predef = home / checked["predef_relative"]
    require(not predef.exists() and not predef.is_symlink(),
            "reviewed JVM predef is present before the fresh capture")
    return home, predef


def _scoped_startup_engine_factory(original_factory: Any, root: Path, output: Path,
                                   policy: object) -> tuple[Any, Any]:
    """Wrap only the hash-bound runner engine's environment factory.

    The wrapper is installed by ``controls``/``execute`` for one call and is
    restored in ``finally``.  It is not a caller-supplied command callback: the
    exact policy above determines every value and both bridge/forked JVMs see
    the same ``JAVA_TOOL_OPTIONS`` property.
    """
    checked = _validate_jvm_startup_policy(policy)
    patched: list[tuple[Any, Any]] = []
    patched_ids: set[int] = set()

    def factory(*args: Any, **kwargs: Any) -> Any:
        bundle = original_factory(*args, **kwargs)
        require(isinstance(bundle, dict) and set(bundle) >= {"runner"},
                "pinned Joern engine factory did not return a runner bundle")
        engine = bundle["runner"]
        original_env_for = engine.env_for
        if id(engine) in patched_ids:
            return bundle

        def env_for(runtime: dict[str, Any]) -> dict[str, str]:
            environment = dict(original_env_for(runtime))
            require(environment.get("JAVA_OPTS") == checked["retained_java_opts"],
                    "pinned Joern JAVA_OPTS changed under startup policy")
            for key in checked["ambient_options_cleared"]:
                require(key not in environment or environment[key] in (None, ""),
                        f"ambient JVM/classpath injection survived for {key}")
            home, _predef = _startup_home(root, output, checked)
            environment[checked["option_source"]] = checked["option_template"].format(
                capture_home=str(home)
            )
            return environment
        engine.env_for = env_for
        patched_ids.add(id(engine))
        patched.append((engine, original_env_for))
        return bundle

    def restore() -> None:
        for engine, original_env_for in reversed(patched):
            engine.env_for = original_env_for
        patched.clear()
        patched_ids.clear()

    return factory, restore


def _write_startup_witness(root: Path, output: Path, policy: object) -> dict[str, Any]:
    """Record the deterministic startup binding after the guarded run."""
    checked = _validate_jvm_startup_policy(policy)
    home, predef = _startup_home(root, output, checked)
    # The source policy requires absence; a newly created predef is a failed
    # startup witness, never silently treated as an empty file.
    present = predef.exists() or predef.is_symlink()
    witness = {
        "schema": "v092-joern-jvm-startup-witness/v1",
        "policy": checked,
        "capture_root": output.relative_to(root).as_posix(),
        "home_relative": checked["home_relative"],
        "predef_relative": checked["predef_relative"],
        "bridge_and_forked_jvm": {
            "option_source": checked["option_source"],
            "option_template": checked["option_template"],
            "user_home_relative": checked["home_relative"],
        },
        "predef": {
            "present": present,
            "bytes": predef.stat().st_size if predef.is_file() else 0,
            "sha256": sha(predef) if predef.is_file() else None,
        },
    }
    require(not present, "reviewed JVM predef appeared during the fresh capture")
    return witness


def _run_with_startup_policy(root: Path, output: str, policy: object,
                             invoke: Any, runner: ModuleType) -> dict[str, Any]:
    root = Path(root).resolve()
    output_path = _startup_output_path(root, output)
    _validate_jvm_startup_policy(policy)
    require(not output_path.exists() and not output_path.is_symlink(),
            "Joern startup output namespace was already consumed")
    common = getattr(runner, "common", None)
    original_factory = getattr(common, "private_engine", None)
    require(callable(original_factory), "pinned Joern runner lacks its engine factory")
    factory, restore = _scoped_startup_engine_factory(
        original_factory, root, output_path, policy
    )
    common.private_engine = factory
    try:
        result = invoke(output_path)
        witness = _write_startup_witness(root, output_path, policy)
        witness_path = output_path / "jvm-startup-witness.json"
        witness_path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
        reference = {
            "path": witness_path.relative_to(root).as_posix(),
            "sha256": sha(witness_path),
        }
        result["jvm_startup_policy"] = copy.deepcopy(JVM_STARTUP_POLICY)
        result["jvm_startup_witness"] = reference
        (output_path / "run.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    finally:
        common.private_engine = original_factory
        restore()


def controls(root: Path, output: str, *, startup_policy: object | None = None,
             **kwargs: Any) -> dict[str, Any]:
    """Capture fresh controls under the exact reviewed JVM startup policy."""
    require(startup_policy is not None,
            "fresh Joern controls require the reviewed JVM startup policy")
    result = validate_bootstrap_inputs(root, **kwargs)
    runner = result["runner"]
    _assert_canonical_historical_binding(Path(root).resolve())
    old_constant = getattr(runner, "EXECUTION_PLAN_PATH", None)
    try:
        runner.EXECUTION_PLAN_PATH = result["new_plan_path"]
        return _run_with_startup_policy(
            root, output, startup_policy,
            lambda output_path: runner.run_controls(
                Path(root).resolve(), result["new_plan_path"], output_path
            ),
            runner,
        )
    finally:
        if old_constant is not None:
            runner.EXECUTION_PLAN_PATH = old_constant



def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("preflight", "controls", "execute"):
        command = sub.add_parser(mode)
        command.add_argument("--root", type=Path, default=ROOT)
        command.add_argument("--plan", default=NEW_PLAN_DEFAULT)
        command.add_argument("--evidence", default=EVIDENCE_DEFAULT)
        command.add_argument("--plan-sha256")
        command.add_argument("--evidence-sha256")
        if mode in {"controls", "execute"}:
            command.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    common = {
        "new_plan_path": args.plan,
        "evidence_path": args.evidence,
        "expected_new_plan_sha256": args.plan_sha256,
        "expected_evidence_sha256": args.evidence_sha256,
    }
    if args.mode == "preflight":
        result = preflight(args.root, **common)
        print(json.dumps({"status": "ready", **result}, indent=2, sort_keys=True))
        return 0
    if args.mode == "controls":
        run = controls(args.root, args.output, startup_policy=JVM_STARTUP_POLICY, **common)
        print(json.dumps({"status": "controls-complete", "group_id": GROUP_ID,
                          "records": len(run.get("records", []))}, indent=2))
        return 0
    run = execute(args.root, args.output, startup_policy=JVM_STARTUP_POLICY, **common)
    print(json.dumps({"status": "complete", "group_id": GROUP_ID, "results": len(run.get("results", []))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
