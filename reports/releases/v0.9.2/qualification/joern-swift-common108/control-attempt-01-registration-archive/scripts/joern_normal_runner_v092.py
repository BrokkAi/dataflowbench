"""Fresh-identity Joern common-108 runner and controls for v0.9.2."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time

import swift_common_population_v2 as common
import v092_qualification as qualification_binding


ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "joern-common-execution-plan/v092"
CONTROL_PLAN_SCHEMA = "analyzer-qualification-control-plan/v092"
GROUP_ID = "joern-swift-common108"
EXECUTION_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
ADAPTER = "joern-normal-v092"
VERSION = "4.0.660"
PARENT_EXECUTION_CONTRACT = "adapters/joern/swift-common-v2/plan-v090-01/contract.json"
MIN_FREE_BYTES = 40 * 1024**3
CONTROL_SCRATCH_BYTES = 4 * 1024**3
CONTROL_TOTAL_BUDGET_SECONDS = 900
CONTROL_CASES = {
    "direct-positive": "dfb-taint-swift-direct-positive",
    "direct-negative": "dfb-taint-swift-direct-negative",
    "dfb-taint-swift-model-opaque-propagator-negative": "dfb-taint-swift-model-opaque-propagator-negative",
    "dfb-taint-swift-model-opaque-propagator-positive": "dfb-taint-swift-model-opaque-propagator-positive",
    "dfb-taint-swift-model-propagator-position-negative": "dfb-taint-swift-model-propagator-position-negative",
    "dfb-taint-swift-model-propagator-position-positive": "dfb-taint-swift-model-propagator-position-positive",
}
CONTROL_ARMS = ("off", "on")
OPAQUE_TEMPLATE_IDS = {
    "dfb-template-model-opaque-propagator",
    "dfb-template-model-propagator-position",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def reference(root: Path, path: Path) -> dict:
    path = path.resolve()
    require(path.is_file() and path.is_relative_to(root.resolve()), "evidence file escaped execution root")
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": sha(path)}


def bound_file(root: Path, ref: object) -> Path:
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact repository reference required")
    relative = Path(ref["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "unsafe evidence path")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "missing or escaped evidence file")
    require(sha(path) == ref["sha256"], "evidence file digest mismatch: " + str(relative))
    return path


def bound_capture_file(root: Path, capture_root: Path, ref: object) -> Path:
    path = bound_file(root, ref)
    captured = capture_root / ref["path"]
    require(captured.is_file() and not captured.is_symlink() and sha(captured) == ref["sha256"],
            "retained Joern evidence differs from its original capture-root copy")
    return path


def _expected_control_map(cases: dict) -> dict[str, str]:
    expected = {key: case_id for key, case_id in CONTROL_CASES.items() if key.startswith("direct-")}
    expected.update({case_id: case_id for case_id, case in cases.items() if case["template_id"] in OPAQUE_TEMPLATE_IDS})
    require(expected == CONTROL_CASES, "Joern v0.9.0 six-fixture control roster changed")
    return expected


def _engine(root: Path):
    engine = common.private_engine(root, "joern")["runner"]
    engine.VERSION = VERSION
    engine.ADAPTER = ADAPTER
    return engine


def _set_engine_query_root(engine, query_root: str) -> None:
    engine.BASE = query_root
    engine.config_for.__globals__["BASE"] = query_root
    engine.query_argv.__globals__["BASE"] = query_root


def _identity(runtime: dict) -> dict:
    return {
        "tool": "joern",
        "tool_version": VERSION,
        "tool_build_identity": (
            "joern-cli:" + VERSION + ";engine:" + runtime["engine_sha256"] +
            ";frontend:" + runtime["frontend_sha256"]
        ),
        "adapter_version": ADAPTER,
    }


def _check_runtime(root: Path, plan: dict, engine) -> None:
    runtime = plan.get("runtime")
    require(isinstance(runtime, dict), "Joern runtime inventory is missing")
    require(runtime.get("engine_sha256") and runtime.get("frontend_sha256"), "Joern exact engine identities are required")
    joern_root = Path(runtime["joern_root"])
    engine_jar = joern_root / "lib" / ("io.joern.dataflowengineoss-" + VERSION + ".jar")
    frontend_jar = joern_root / "frontends/swiftsrc2cpg/lib" / ("io.joern.swiftsrc2cpg-" + VERSION + ".jar")
    require(engine_jar.is_file() and sha(engine_jar) == runtime["engine_sha256"], "Joern engine JAR identity mismatch")
    require(frontend_jar.is_file() and sha(frontend_jar) == runtime["frontend_sha256"], "Joern Swift frontend JAR identity mismatch")
    engine.verify_runtime(root, plan)
    for name in ("joern", "frontend", "astgen", "compiler"):
        path = Path(runtime[name])
        require(path.is_file() and path.stat().st_mode & 0o111, "Joern runtime executable missing or not executable: " + name)


def _validate_control_plan(root: Path, plan: dict) -> tuple[dict, Path]:
    projection = qualification_binding.plan_projection_sha256(plan)
    require(plan.get("qualification_control_projection_sha256") == projection, "Joern control projection digest mismatch")
    control_path = bound_file(root, plan.get("qualification_control_plan"))
    control = read(control_path)
    require(control.get("schema") == CONTROL_PLAN_SCHEMA, "unknown Joern control plan schema")
    require(control.get("group_id") == GROUP_ID, "Joern control group identity mismatch")
    require(control.get("execution_plan_projection_sha256") == projection, "Joern control plan projection mismatch")
    require(control.get("identity") == plan.get("identity"), "Joern control plan identity mismatch")
    require(control.get("identity_components") == plan.get("identity_components"), "Joern control plan components mismatch")
    require(control.get("population_sha256") == plan.get("population_sha256"), "Joern control plan population mismatch")
    require(control.get("fixture_revision") == plan.get("fixture_revision"), "Joern control plan fixture mismatch")
    population, common_rows, _swift_rows, cases, digest = common.load_common_population(root)
    require(plan.get("population_sha256") == digest and plan.get("fixture_revision") == population["fixture_revision"], "Joern fixed population binding mismatch")
    require(control.get("controls") == _expected_control_map(cases), "Joern control plan must preserve six exact fixtures")
    require(control.get("arms") == list(CONTROL_ARMS), "Joern control arms must be off/on")
    require(control.get("case_arm_count") == 12, "Joern control plan must retain all twelve case-arms")
    require(control.get("maximum_phase_invocations") == 36, "Joern control invocation ceiling must remain 36")
    require(control.get("case_arm_budget_seconds") == 75 and control.get("total_budget_seconds") == 900, "Joern control time limits changed")
    require(control.get("scratch_allowance_bytes") == CONTROL_SCRATCH_BYTES, "Joern control scratch allowance changed")
    return control, control_path


def _validate_qualification(root: Path, plan: dict, cases: dict) -> dict:
    evidence, control_plan_path = qualification_binding.validate_common_receipt(
        root, plan, plan.get("fresh_qualification"), group_id=GROUP_ID
    )
    control_plan, _ = qualification_binding.read_json(control_plan_path, "Joern qualification control plan")
    require(control_plan.get("schema") == CONTROL_PLAN_SCHEMA, "unknown Joern control plan schema")
    require(control_plan.get("controls") == _expected_control_map(cases), "Joern qualification fixture roster mismatch")
    require(control_plan.get("arms") == list(CONTROL_ARMS) and control_plan.get("case_arm_count") == 12, "Joern qualification matrix must be six fixtures by two arms")
    run_ref = evidence.get("control_run")
    run_path = bound_file(root, run_ref)
    run, _ = qualification_binding.read_json(run_path, "Joern qualification control run")
    require(run.get("control_plan_sha256") == plan["qualification_control_plan"]["sha256"], "Joern control-run plan digest mismatch")
    require(run.get("execution_plan_projection_sha256") == plan["qualification_control_projection_sha256"], "Joern control-run projection mismatch")
    engine = _engine(root)
    _set_engine_query_root(engine, plan["query_root"])
    observations, invocations = _replay_control_run(root, plan, control_plan, run, cases, engine)
    dimensions = evidence.get("dimensions")
    require(isinstance(dimensions, dict), "Joern qualification dimension summary missing")
    controls = dimensions.get("common108_controls")
    require(isinstance(controls, dict), "Joern qualification did not bind fresh common108 controls")
    require(controls.get("case_count") == 6 and controls.get("case_arm_count") == 12, "Joern qualification control counts mismatch")
    require(controls.get("phase_invocation_count") == invocations, "Joern qualification invocation count mismatch")
    require(controls.get("control_run") == run_ref, "Joern qualification control run reference mismatch")
    assessment = engine.assess_controls(observations)
    require(run.get("assessment") == assessment, "Joern reviewed control interpretation differs from replayed observations")
    require(assessment.get("status") == "bounded-controls-observed", "Joern model on/off controls did not demonstrate the registered positive/negative transitions")
    return evidence


def _replay_control_run(root: Path, plan: dict, control_plan: dict, run: dict,
                        cases: dict, engine) -> tuple[dict, int]:
    """Replay six exact controls from retained graph/config/command files."""
    require(run.get("schema") == "analyzer-qualification-control-run/v092", "unknown Joern control-run schema")
    require(run.get("group_id") == GROUP_ID, "Joern control-run group mismatch")
    require(run.get("identity") == plan["identity"], "Joern control-run identity mismatch")
    require(run.get("identity_components") == plan["identity_components"], "Joern control-run component identity mismatch")
    elapsed_total = run.get("elapsed_seconds")
    require(type(elapsed_total) in (int, float) and 0 <= elapsed_total <= CONTROL_TOTAL_BUDGET_SECONDS,
            "Joern control run exceeded the 900-second total budget")
    witness_path = bound_file(root, run.get("identity_witness"))
    witness = read(witness_path)
    require(witness.get("observed") == plan["identity"], "Joern fresh version witness identity mismatch")
    witness_capture_root = witness.get("capture_root")
    witness_capture_dir = witness.get("capture_directory")
    require(isinstance(witness_capture_root, str) and Path(witness_capture_root).is_absolute() and Path(witness_capture_root).is_dir(),
            "Joern identity witness capture root is missing")
    require(isinstance(witness_capture_dir, str) and Path(witness_capture_dir).is_absolute(),
            "Joern identity witness capture directory is missing")
    witness_capture_root = Path(witness_capture_root).resolve()
    bound_capture_file(root, witness_capture_root, witness.get("command"))
    bound_capture_file(root, witness_capture_root, witness.get("stdout"))
    version_command = read(bound_file(root, witness.get("command")))
    require(version_command.get("argv") == [plan["runtime"]["joern"]], "Joern fresh identity command differs from the selected launcher")
    require(version_command.get("cwd") == str(Path(witness_capture_dir).resolve()),
            "Joern fresh version command differs from its bound capture directory")
    require(version_command.get("exit_status") == 0 and version_command.get("timed_out") is False and
            version_command.get("cleanup_status") == "tracked-processes-stopped", "Joern fresh identity command failed or cleanup is uncertain")
    require(re.search(r"(?<![0-9.])" + re.escape(VERSION) + r"(?![0-9.])", bound_file(root, witness.get("stdout")).read_text()), "Joern fresh version banner mismatch")

    expected = {(label, arm, case_id) for label, case_id in control_plan["controls"].items() for arm in CONTROL_ARMS}
    records = run.get("records")
    require(isinstance(records, list) and len(records) == len(expected), "Joern control run must retain all 12 case-arms")
    actual = set()
    observations: dict[str, dict[str, str]] = {}
    invocations = 0
    phase_ids = ["typecheck", "frontend", "query"]
    allowed = {"reached", "not-reached", "inconclusive", "unsupported", "runner-error"}
    for record in records:
        require(isinstance(record, dict), "Joern control-run row is malformed")
        control_name, arm, case_id = record.get("control"), record.get("arm"), record.get("case_id")
        actual.add((control_name, arm, case_id))
        require((control_name, arm, case_id) in expected, "Joern control-run row is outside the exact matrix")
        raw_path = bound_file(root, record.get("raw"))
        raw = read(raw_path)
        capture_root_text = raw.get("capture_root")
        capture_directory_text = raw.get("capture_directory")
        require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute() and Path(capture_root_text).is_dir(),
                "Joern raw control capture root is missing")
        require(isinstance(capture_directory_text, str) and Path(capture_directory_text).is_absolute(),
                "Joern raw control capture directory is missing")
        capture_root = Path(capture_root_text).resolve()
        capture_directory = Path(capture_directory_text).resolve()
        directory = raw_path.parent
        relative_output = directory.resolve().relative_to(root.resolve())
        require(capture_directory == (capture_root / relative_output).resolve(),
                "Joern control capture directory does not match retained evidence path")
        require(raw.get("schema") == "joern-common-control-raw/v092", "unknown Joern raw control schema")
        require(raw.get("plan_projection_sha256") == plan["qualification_control_projection_sha256"], "Joern raw control projection mismatch")
        require(raw.get("control") == control_name and raw.get("case_id") == case_id and raw.get("arm") == arm, "Joern raw control routing mismatch")
        case_path = root / cases[case_id]["path"]
        require(raw.get("fixture_hashes") == {name: sha(case_path.parent / name) for name in cases[case_id]["fixture_files"]}, "Joern control fixture bytes changed")
        require(raw.get("identity") == plan["identity"], "Joern raw control identity mismatch")
        require(raw.get("identity_components") == plan["identity_components"], "Joern raw control component identity mismatch")
        outcome = raw.get("raw_outcome")
        require(outcome in allowed and record.get("observed") == outcome, "Joern control observation is missing or invalid")
        require(raw.get("state") == engine.normalized(outcome), "Joern control typed state was flattened")
        native = raw.get("native_outputs")
        require(isinstance(native, list), "Joern raw control must bind native graph and config outputs")
        native_files = {}
        for reference_row in native:
            path = bound_capture_file(root, capture_root, reference_row)
            native_files[path.name] = path
        require("graph.json" in native_files and "config.json" in native_files, "Joern raw control lacks retained graph/config evidence")
        graph_path, config_path = native_files["graph.json"], native_files["config.json"]
        require(graph_path.parent == directory and config_path.parent == directory, "Joern native graph/config escaped the control output directory")
        observed_config = read(config_path)
        expected_config = engine.config_for(capture_root, cases[case_id], arm)
        require(observed_config == expected_config, "Joern control model arm differs from its reviewed configuration")
        observed_outcome, observed_diagnostics = engine.observe(read(graph_path), observed_config)
        require(outcome == observed_outcome and raw.get("diagnostics") == observed_diagnostics, "Joern raw control interpretation differs from graph replay")

        commands = raw.get("commands")
        require(isinstance(commands, list) and len(commands) == len(phase_ids), "Joern control must retain all three command phase records")
        phase_records = []
        for index, command_ref in enumerate(commands):
            command_path = bound_capture_file(root, capture_root, command_ref)
            command = read(command_path)
            expected_command_path = (directory / (phase_ids[index] + ".command.json")).resolve()
            require(command_path.resolve() == expected_command_path, "Joern phase reference points to a different control attempt")
            require(command.get("phase_id") == phase_ids[index] and command.get("role") == "analysis", "Joern control phase order/role mismatch")
            require(command.get("exit_status") == 0 and command.get("timed_out") is False and
                    command.get("cleanup_status") == "tracked-processes-stopped", "Joern control command failed or cleanup is uncertain")
            if phase_ids[index] == "typecheck":
                expected_argv = engine.compiler_argv(plan["runtime"], cases[case_id], capture_directory)
            elif phase_ids[index] == "frontend":
                expected_argv = engine.frontend_argv(plan["runtime"], capture_directory)
            else:
                expected_argv = engine.query_argv(capture_root, plan["runtime"], capture_directory)
            require(command.get("argv") == expected_argv and command.get("cwd") == str(capture_directory),
                    "Joern phase command/runtime identity differs from the reviewed execution plan")
            elapsed, deadline = command.get("elapsed_seconds"), command.get("deadline_seconds")
            require(type(elapsed) in (int, float) and type(deadline) in (int, float) and 0 <= elapsed <= deadline <= 75,
                    "Joern control phase exceeded its 75-second case-arm budget")
            phase_records.append(command)
        invocations += len(commands)
        case_arm_elapsed = sum(command["elapsed_seconds"] for command in phase_records)
        require(case_arm_elapsed <= 75, "Joern control case-arm exceeded its shared 75-second phase budget")
        observations.setdefault(control_name, {})[arm] = outcome
    require(actual == expected and len(actual) == 12, "Joern control run omitted or duplicated an off/on case-arm")
    require(invocations == 36 and run.get("phase_invocation_count") == invocations, "Joern qualification must retain all 36 successful phase invocations")
    return observations, invocations


def validate_plan(root: Path, plan_path: str, *, allow_qualification_pending: bool = False) -> tuple[dict, dict, dict]:
    root = Path(root).resolve()
    require(Path(plan_path).as_posix() == EXECUTION_PLAN_PATH, "Joern v0.9.2 executable plan must use plan-v092-01")
    plan_file = root / plan_path
    require(plan_file.is_file() and plan_file.resolve().is_relative_to(root), "Joern plan must be a repository file")
    plan = read(plan_file)
    require(plan.get("schema") == PLAN_SCHEMA and plan.get("profile") == "v0.9.2", "v0.9.2 Joern executable plan required")
    require(plan.get("engine") == "joern" and plan.get("release_group_id") == GROUP_ID, "wrong Joern release group")
    require(plan.get("scored_activation") is False and plan.get("aggregate_resource_qualification") == "unavailable", "Joern v0.9.2 must remain unscored and aggregate-resource-unqualified")
    require(plan.get("status") == ("qualification-pending" if allow_qualification_pending else "execution-eligible"), "Joern plan status is not eligible for this mode")
    require(plan.get("execution_eligible") is (not allow_qualification_pending), "Joern execution_eligible status mismatch")
    stamp = plan.get("registered_at_unix_seconds")
    require(type(stamp) is int and stamp < int(time.time()), "Joern v0.9.2 plan must be registered before execution")
    require(plan.get("output_root") == "reports/raw/joern-common-v2", "Joern output root must preserve the v0.9.0 common runner root")
    population, _common_rows, _swift_rows, cases, digest = common.load_common_population(root)
    require(len(_common_rows) == 1108 and len(cases) == 108, "fixed common-1108/Swift-108 denominator required")
    require(plan.get("population_sha256") == digest and plan.get("fixture_revision") == population["fixture_revision"], "Joern common population identity mismatch")
    require(set(plan.get("cases", {})) == set(cases), "Joern plan must cover exact Swift common-108 projection")
    contract_ref = plan.get("execution_contract")
    require(isinstance(contract_ref, dict) and contract_ref.get("path") == PARENT_EXECUTION_CONTRACT,
            "Joern execution contract must reuse the immutable v0.9.0 common contract")
    contract_path = bound_file(root, contract_ref)
    contract = read(contract_path)
    require(contract.get("population_sha256") == digest and contract.get("fixture_revision") == population["fixture_revision"],
            "Joern immutable execution contract population mismatch")
    require(contract.get("phase_sequence") == plan.get("phase_sequence") and
            contract.get("total_wall_clock_seconds") == 75,
            "Joern phase sequence or per-case budget differs from the immutable v0.9.0 contract")
    require(all(row.get("configuration") == "joern-current108" and
                row.get("disposition") in {"attempt", "unsupported"} and
                row.get("phase_sequence") == "joern-current108" for row in plan["cases"].values()),
            "Joern case configuration, phase sequence, or typed disposition changed")
    require(plan.get("runtime", {}).get("compiler_root") == str(Path(plan["runtime"].get("compiler", "")).parent.parent) and
            plan.get("runtime", {}).get("sdk_root") == plan.get("runtime", {}).get("sdk"),
            "Joern compiler_root/sdk_root must bind the exact runtime paths")
    require(plan.get("identity") == _identity(plan.get("runtime", {})), "Joern identity must bind exact 4.0.660 engine JARs")
    components = qualification_binding.expected_identity_components(plan)
    component_names = {row["name"] for row in components}
    require({"joern-root", "java-home", "swift-toolchain", "swift-sdk"} <= component_names, "Joern component identities must include engine, Java, Swift compiler, and SDK trees")
    query_root = plan.get("query_root")
    require(isinstance(query_root, str) and not Path(query_root).is_absolute() and ".." not in Path(query_root).parts, "repository-bound Joern query root required")
    require(Path(query_root).parts[:3] == ("adapters", "joern", "swift-common-v2"), "Joern query root must use the versioned common adapter")
    require(plan.get("codeql_packs") is None, "Joern plan cannot bind CodeQL packs")
    require(plan.get("qualification_control_projection_sha256") == qualification_binding.plan_projection_sha256(plan), "Joern execution projection digest mismatch")
    control, _control_path = _validate_control_plan(root, plan)
    engine = _engine(root)
    _set_engine_query_root(engine, query_root)
    _check_runtime(root, plan, engine)
    configs = plan.get("configurations")
    require(isinstance(configs, dict) and isinstance(configs.get("joern-current108"), list), "Joern configuration closure is missing")
    config_paths = {}
    for reference_row in configs["joern-current108"]:
        path = bound_file(root, reference_row)
        config_paths[reference_row["path"]] = reference_row["sha256"]
    require(contract_ref in configs["joern-current108"], "Joern configuration closure omits the immutable execution contract")
    historical_plan_path = "adapters/joern/swift-common-v2/plan-v090-01/plan.json"
    require(historical_plan_path in config_paths,
            "Joern configuration closure omits the immutable v0.9.0 case-disposition source")
    historical_plan = read(bound_file(root, {
        "path": historical_plan_path,
        "sha256": config_paths[historical_plan_path],
    }))
    historical_cases = historical_plan.get("cases")
    require(isinstance(historical_cases, dict) and set(historical_cases) == set(plan["cases"]),
            "Joern historical case-disposition source differs from the common-108 projection")
    require(all(
        plan["cases"][case_id].get("configuration") == historical_cases[case_id].get("configuration") and
        plan["cases"][case_id].get("disposition") == historical_cases[case_id].get("disposition")
        for case_id in plan["cases"]
    ), "Joern v0.9.2 case dispositions or configurations differ from the immutable v0.9.0 plan")
    require(sum(row["disposition"] == "unsupported" for row in plan["cases"].values()) == 12,
            "Joern common-108 unsupported roster must remain the exact twelve native cases")
    required = (
        "scripts/joern_normal_runner_v092.py",
        "scripts/run-joern-common-v092.py",
        "scripts/joern_normal_runner_v1.py",
        "scripts/joern_normal_controls_v1.py",
        "scripts/joern_normal_execution_v1.py",
        "scripts/joern_swift.py",
        "scripts/run-joern-swift-case.py",
        "scripts/swift_v2_process.py",
        "scripts/swift_artifact_closure.py",
        "scripts/swift_common_population_v2.py",
        "scripts/v092_qualification.py",
        "adapters/joern/swift/models.json",
        "populations/v0.9.0.json",
        "populations/swift-synthetic-v3.json",
        "reports/releases/v0.9.0/plan.json",
    )
    for relative in required:
        require(relative in config_paths and config_paths[relative] == sha(root / relative), "Joern plan does not bind " + relative)
    query_files = {"query.sc", "models.json"}
    require(all((root / query_root / name).is_file() for name in query_files), "Joern query/model inputs are missing")
    require(all(str(Path(query_root) / name) in config_paths for name in query_files), "Joern plan does not bind exact query/model inputs")
    if allow_qualification_pending:
        return plan, {}, {"engine": engine, "control": control, "cases": cases}
    evidence = _validate_qualification(root, plan, cases)
    return plan, evidence, {"engine": engine, "control": control, "cases": cases}


def _require_launch_guard(group_id: str, *, qualification: bool = False) -> None:
    marker = "DATAFLOWBENCH_V092_QUALIFICATION" if qualification else "DATAFLOWBENCH_V092_RELEASE_EXECUTION"
    require(os.environ.get(marker) == "1", "Joern v0.9.2 runner must be launched by the guarded release workflow")
    require(os.environ.get("DATAFLOWBENCH_V092_GROUP_ID") == group_id, "Joern release group identity mismatch")


def run_controls(root: Path, plan_path: str, output: Path) -> dict:
    root = Path(root).resolve()
    plan, _unused, context = validate_plan(root, plan_path, allow_qualification_pending=True)
    _require_launch_guard(GROUP_ID, qualification=True)
    engine = context["engine"]
    control = context["control"]
    cases = context["cases"]
    free = shutil.disk_usage(root).free
    require(free >= MIN_FREE_BYTES + CONTROL_SCRATCH_BYTES, "InsufficientLaunchCapacity")
    output = Path(output).resolve()
    require(output.is_relative_to(root / "reports/releases/v0.9.2/qualification"), "Joern qualification output must stay under the v0.9.2 qualification root")
    require(not output.exists() and not output.is_symlink(), "Joern qualification attempt output already exists")
    output.mkdir(parents=True)
    version = engine.process.run(
        [plan["runtime"]["joern"]], output, "version", 30,
        env=engine.env_for(plan["runtime"]), cwd=output,
    )
    require(version.get("exit_status") == 0 and version.get("timed_out") is False and version.get("cleanup_status") == "tracked-processes-stopped", "Joern qualification identity command failed")
    banner = (output / "version.stdout").read_text()
    require(re.search(r"(?<![0-9.])" + re.escape(VERSION) + r"(?![0-9.])", banner), "Joern qualification version witness mismatch")
    identity = plan["identity"]
    identity_path = output / "identity.json"
    identity_path.write_text(json.dumps({
        "observed": identity,
        "observed_at_unix_seconds": int(time.time()),
        "capture_root": str(root.resolve()),
        "capture_directory": str(output.resolve()),
        "command": version,
        "stdout": reference(root, output / "version.stdout"),
    }, indent=2) + "\n")
    _, common_rows, _swift_rows, _, _ = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in common_rows}
    run = {
        "schema": "analyzer-qualification-control-run/v092",
        "group_id": GROUP_ID,
        "control_plan_sha256": sha(root / plan["qualification_control_plan"]["path"]),
        "execution_plan_projection_sha256": plan["qualification_control_projection_sha256"],
        "identity": identity,
        "identity_components": plan["identity_components"],
        "identity_witness": reference(root, identity_path),
        "started_at_unix_seconds": int(time.time()),
        "records": [],
        "phase_invocation_count": 0,
        "scored_activation": False,
    }
    control_started = time.monotonic()
    for control_name, case_id in control["controls"].items():
        case = cases[case_id]
        case_path = case_paths[case_id]
        for arm in control["arms"]:
            require(time.monotonic() - control_started < CONTROL_TOTAL_BUDGET_SECONDS, "ControlTotalBudgetExhausted")
            require(shutil.disk_usage(root).free >= MIN_FREE_BYTES, "DiskReserveReached")
            used = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
            require(used < CONTROL_SCRATCH_BYTES, "ControlScratchAllowanceReached")
            leaf = output / control_name / arm
            raw, _stop = engine.run_case(root, plan, case_path, case, leaf, arm)
            raw.update({
                "schema": "joern-common-control-raw/v092",
                "case_id": case_id,
                "control": control_name,
                "arm": arm,
                "plan_projection_sha256": plan["qualification_control_projection_sha256"],
                "identity": plan["identity"],
                "identity_components": plan["identity_components"],
                "capture_root": str(root.resolve()),
                "capture_directory": str(leaf.resolve()),
                "fixture_hashes": {name: sha(case_path.parent / name) for name in case["fixture_files"]},
            })
            raw_path = leaf / "raw.json"
            raw_path.write_text(json.dumps(raw, indent=2) + "\n")
            run["phase_invocation_count"] += len(raw.get("commands", []))
            run["records"].append({
                "control": control_name,
                "case_id": case_id,
                "arm": arm,
                "raw": reference(root, raw_path),
                "observed": raw["raw_outcome"],
            })
            require(run["phase_invocation_count"] <= control["maximum_phase_invocations"], "Joern control invocation ceiling exceeded")
            run["elapsed_seconds"] = time.monotonic() - control_started
            (output / "run.json").write_text(json.dumps(run, indent=2) + "\n")
            require(run["elapsed_seconds"] <= CONTROL_TOTAL_BUDGET_SECONDS, "ControlTotalBudgetExhausted")
    expected = {(label, case_id, arm) for label, case_id in control["controls"].items() for arm in control["arms"]}
    actual = {(row["control"], row["case_id"], row["arm"]) for row in run["records"]}
    require(actual == expected and len(run["records"]) == 12, "Joern controls did not finish the exact 12 case-arm matrix")
    run["ended_at_unix_seconds"] = int(time.time())
    run["elapsed_seconds"] = time.monotonic() - control_started
    run["assessment"] = engine.assess_controls({
        label: {arm: next(row["observed"] for row in run["records"] if row["control"] == label and row["arm"] == arm)
                for arm in control["arms"]}
        for label in control["controls"]
    })
    (output / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    return run


def execute(root: Path, plan_path: str, output: Path) -> dict:
    root = Path(root).resolve()
    plan, evidence, context = validate_plan(root, plan_path)
    _require_launch_guard(GROUP_ID)
    engine = context["engine"]
    cases = context["cases"]
    output = Path(output).resolve()
    require(output.is_relative_to((root / plan["output_root"]).resolve()), "Joern output must remain below the plan's exact output root")
    require(not output.exists() and not output.is_symlink(), "Joern execution attempt output already exists")
    capacity = shutil.disk_usage(root).free
    require(capacity >= 125 * 1024**3, "InsufficientLaunchCapacity")
    output.mkdir(parents=True)
    identity_out = output / "identity"
    identity_out.mkdir()
    version = engine.process.run(
        [plan["runtime"]["joern"]], identity_out, "version", 30,
        env=engine.env_for(plan["runtime"]), cwd=identity_out,
    )
    require(version.get("exit_status") == 0 and version.get("timed_out") is False and version.get("cleanup_status") == "tracked-processes-stopped", "Joern identity command failed")
    banner = (identity_out / "version.stdout").read_text()
    require(re.search(r"(?<![0-9.])" + re.escape(VERSION) + r"(?![0-9.])", banner), "Joern 4.0.660 version witness mismatch")
    observed = plan["identity"]
    identity_path = identity_out / "identity.json"
    identity_path.write_text(json.dumps({
        "observed": observed,
        "observed_at_unix_seconds": int(time.time()),
        "command": version,
        "stdout": reference(root, identity_out / "version.stdout"),
    }, indent=2) + "\n")
    population, common_rows, _swift_rows, _, digest = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in common_rows}
    run = {
        "schema": "joern-common-run/v092",
        "plan_sha256": sha(root / plan_path),
        "qualification_sha256": plan["fresh_qualification"]["sha256"],
        "population_sha256": digest,
        "fixture_revision": population["fixture_revision"],
        "identity": observed,
        "identity_witness": reference(root, identity_path),
        "started_at_unix_seconds": int(time.time()),
        "ended_at_unix_seconds": int(time.time()),
        "scored_activation": False,
        "aggregate_resource_qualification": "unavailable",
        "results": [],
    }
    for case_id, case in cases.items():
        require(shutil.disk_usage(root).free >= 40 * 1024**3, "DiskReserveReached")
        selection = plan["cases"][case_id]
        require(selection.get("configuration") == "joern-current108", "unknown Joern configuration")
        leaf = output / case_id
        if selection.get("disposition") == "unsupported":
            decision_ref = selection.get("decision")
            decision_path = bound_file(root, decision_ref)
            decision = read(decision_path)
            require(decision.get("case_id") == case_id and decision.get("population_sha256") == digest, "Joern unsupported decision identity mismatch")
            require(decision.get("identity") == observed and decision.get("outcome") == "unsupported", "Joern unsupported decision must bind exact fresh identity")
            require(decision.get("evidence") and decision.get("reason"), "Joern unsupported decision lacks evidence or reason")
            for ref in decision["evidence"]:
                bound_file(root, ref)
            leaf.mkdir()
            raw = {
                "raw_outcome": "unsupported",
                "state": "unsupported",
                "duration_ms": 0,
                "total_elapsed_seconds": 0,
                "diagnostics": [decision["reason"]],
                "witness_checkpoints": [],
                "executed": False,
                "decision_sha256": decision_ref["sha256"],
                "commands": [],
                "native_outputs": [],
            }
        else:
            capability = selection.get("capability")
            require(isinstance(capability, dict), "Joern attempted case lacks explicit capability evidence")
            require(capability.get("model_mode") in ("off", "on"), "Joern model mode must be explicit")
            raw, _stop = engine.run_case(root, plan, case_paths[case_id], case, leaf, capability["model_mode"])
            raw["capability"] = capability
        raw.update({
            "schema": "joern-common-raw/v092",
            "case_id": case_id,
            "plan_sha256": run["plan_sha256"],
            "qualification_sha256": run["qualification_sha256"],
            "population_sha256": digest,
            "fixture_revision": population["fixture_revision"],
            "configuration": selection["configuration"],
            "identity": observed,
        })
        raw_path = leaf / "raw.json"
        raw_path.write_text(json.dumps(raw, indent=2) + "\n")
        run["results"].append({
            "case_id": case_id,
            "configuration": selection["configuration"],
            "raw": reference(root, raw_path),
        })
        run["ended_at_unix_seconds"] = int(time.time())
        (output / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    require(len(run["results"]) == 108 and {row["case_id"] for row in run["results"]} == set(cases), "Joern common-108 execution incomplete")
    return run
