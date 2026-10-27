"""Version-isolated CodeQL runner gates for the v0.9.2 common Swift lane.

The execution machinery is composed with the historical v1 mechanics only
after this module verifies fresh v0.9.2 identity, query, and qualification
evidence. No v0.9.0 activation or query-revalidation receipt is accepted.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import time

import swift_common_population_v2 as common
import codeql_swift_qualification_v092 as swift_qualification
import v092_qualification as qualification_binding


ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "swift-common-execution-plan/v092"
ADAPTER = "swift-normal-v092"
CLI_VERSION = "2.27.2"
CLI_BUILD = "d7b185e374bfe18c0484dac07a521a810eb9c4fb"
SWIFT_PACK_VERSION = "6.8.5-dfb.entry1"
GROUP_ID = "codeql-swift-common108"
EXECUTION_PLAN_PATH = "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json"
QUALIFICATION_PREFIX = "reports/releases/v0.9.2/qualification"
PARENT_EXECUTION_CONTRACT = "adapters/codeql/swift-common-v2/plan-v090-01/contract.json"
ENTRY_CONTROL_IDS = swift_qualification.ENTRY_IDS


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def bound_file(root: Path, reference: object) -> Path:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, "exact file reference required")
    relative = Path(reference["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "unsafe repository reference")
    target = root / relative
    require(target.is_file() and target.resolve().is_relative_to(root.resolve()), "missing or escaped repository reference")
    require(sha(target) == reference["sha256"], "repository reference digest mismatch: " + relative.as_posix())
    return target


def repository_ref(root: Path, relative: str) -> dict:
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "unsafe repository path")
    target = root / path
    require(target.is_file() and target.resolve().is_relative_to(root.resolve()), "missing repository input: " + relative)
    return {"path": path.as_posix(), "sha256": sha(target)}


def validate_pack_bindings(plan: dict) -> None:
    """Keep the legacy query-pack map and the outer runtime-tree manifest distinct.

    The frozen common runner consumes ``runtime.manifests.packs`` as a
    path-to-content-SHA map and requires its digest to equal the historical
    ``pins.packs_manifest_sha256``.  V0.9.2 separately binds the acquired
    custom Swift pack tree with ``codeql_packs.runtime_tree_manifest_sha256``.
    These are different files and must not be conflated.
    """
    runtime = plan.get("runtime")
    require(isinstance(runtime, dict), "CodeQL runtime binding is missing")
    pins = runtime.get("pins")
    manifests = runtime.get("manifests")
    pack = plan.get("codeql_packs")
    require(isinstance(pins, dict) and isinstance(manifests, dict) and isinstance(pack, dict),
            "CodeQL pack identity bindings are incomplete")
    legacy_map = manifests.get("packs")
    require(isinstance(legacy_map, dict) and set(legacy_map) == {"path", "sha256"},
            "CodeQL legacy pack inventory reference is missing")
    require(legacy_map.get("sha256") == pins.get("packs_manifest_sha256"),
            "CodeQL pack pin must bind the exact legacy file-map digest")
    runtime_packs = runtime.get("packs")
    require(isinstance(runtime_packs, str) and Path(runtime_packs).is_absolute(),
            "CodeQL custom Swift pack root must be absolute")
    require(pack.get("root") == runtime_packs, "CodeQL Swift pack roots differ")
    component_name = pack.get("runtime_tree_component")
    require(component_name == "codeql-swift-packs", "dedicated CodeQL Swift pack component name mismatch")
    outer_digest = pack.get("runtime_tree_manifest_sha256")
    require(isinstance(outer_digest, str) and re.fullmatch(r"[0-9a-f]{64}", outer_digest),
            "CodeQL outer Swift pack runtime manifest digest is malformed")
    component_rows = [row for row in plan.get("identity_components", [])
                      if isinstance(row, dict) and row.get("name") == component_name]
    require(len(component_rows) == 1 and component_rows[0].get("sha256") == outer_digest,
            "Swift pack runtime-tree digest differs from its identity component")


def _qualification(root: Path, plan: dict) -> dict:
    reference = plan.get("fresh_qualification")
    evidence, control_plan_path = qualification_binding.validate_common_receipt(
        root, plan, reference, group_id=GROUP_ID
    )
    control_plan, _ = qualification_binding.read_json(control_plan_path, "CodeQL qualification control plan")
    swift_qualification._validate_control_plan(root, plan, control_plan)
    dimensions = evidence.get("dimensions")
    require(isinstance(dimensions, dict), "CodeQL qualification dimensions are missing")
    entry = dimensions.get("entry_extractor")
    require(isinstance(entry, dict), "fresh CodeQL entry-extractor controls are missing")
    require(entry.get("status") in ("qualified", "measurement-with-known-limits"), "entry-extractor control status is ineligible")
    require(entry.get("execution_eligible") is True, "CodeQL entry extractor is not execution eligible")
    require(entry.get("control_ids") == list(ENTRY_CONTROL_IDS), "CodeQL structural control roster differs from the accepted ten-control manifest")
    require(entry.get("case_count") == 10, "CodeQL structural qualification must retain all ten controls")
    qualification_binding.bound_repository_file(root, entry.get("evidence"), "CodeQL entry-extractor evidence")

    query_dimension = dimensions.get("query_resolution_compile")
    require(isinstance(query_dimension, dict), "fresh CodeQL query-resolution/compile controls are missing")
    require(query_dimension.get("status") == "qualified", "CodeQL query-resolution/compile controls are not complete")
    query_receipt = qualification_binding.bound_repository_file(
        root, query_dimension.get("receipt"), "CodeQL query-resolution/compile receipt"
    )
    engine = common.private_engine(root, "codeql")["runner"]
    engine.BASE = plan["query_root"]
    expected_queries = {
        str(path.relative_to(root))
        for case in common.load_population(root)[1].values()
        for path in engine.query_files(case).values()
    }
    require(query_dimension.get("query_count") == len(expected_queries), "CodeQL query receipt query count mismatch")
    require(reference.get("path") and query_receipt.is_file(), "CodeQL query-resolution receipt missing")

    for name in ("model_activation", "sanitizer_activation"):
        dimension = dimensions.get(name)
        require(isinstance(dimension, dict), "fresh CodeQL " + name.replace("_", " ") + " receipt is missing")
        require(dimension.get("status") == "qualified" and dimension.get("execution_eligible") is True,
                "CodeQL " + name.replace("_", " ") + " controls are not fully qualified")
        qualification_binding.bound_repository_file(root, dimension.get("evidence"), "CodeQL " + name + " evidence")

    run_ref = evidence.get("control_run")
    run_path = qualification_binding.bound_repository_file(root, run_ref, "CodeQL qualification control run")
    run, _ = qualification_binding.read_json(run_path, "CodeQL qualification control run")
    expected_dimensions = {
        "entry_extractor": dimensions["entry_extractor"]["evidence"],
        "query_resolution_compile": dimensions["query_resolution_compile"]["receipt"],
        "model_activation": dimensions["model_activation"]["evidence"],
        "sanitizer_activation": dimensions["sanitizer_activation"]["evidence"],
    }
    require(run.get("dimensions") == expected_dimensions, "CodeQL qualification run dimension bindings differ from the receipt")
    replay = swift_qualification.replay_control_run(root, plan, control_plan, run, dimensions)
    require(entry.get("status") == replay["entry_extractor"]["status"], "CodeQL entry status differs from raw structural replay")
    require(entry.get("assessment") == replay["entry_extractor"], "CodeQL entry assessment differs from raw structural replay")
    for name in ("model_activation", "sanitizer_activation"):
        require(dimensions[name].get("assessment") == replay[name], "CodeQL " + name + " assessment differs from raw replay")
        require(dimensions[name].get("status") == replay[name]["status"], "CodeQL " + name + " status differs from raw replay")
    return evidence


def validate_plan(
    root: Path, plan_path: str, *, allow_qualification_pending: bool = False
) -> tuple[dict, dict, dict]:
    """Validate the v092 executable plan and exact common-108 denominator."""
    root = Path(root).resolve()
    require(Path(plan_path).as_posix() == EXECUTION_PLAN_PATH, "CodeQL v0.9.2 executable plan must use plan-v092-01")
    path = root / plan_path
    require(path.is_file() and path.resolve().is_relative_to(root), "execution plan must be a repository file")
    plan = read(path)
    require(plan.get("schema") == PLAN_SCHEMA and plan.get("profile") == "v0.9.2", "v0.9.2 executable plan required")
    require(plan.get("engine") == "codeql" and plan.get("release_group_id") == GROUP_ID, "wrong CodeQL release group")
    expected_status = "qualification-pending" if allow_qualification_pending else "execution-eligible"
    require(plan.get("status") == expected_status and plan.get("execution_eligible") is (not allow_qualification_pending), "CodeQL Swift plan status is not eligible for this mode")
    require(plan.get("scored_activation") is False and plan.get("aggregate_resource_qualification") == "unavailable", "unqualified execution lane required")
    stamp = plan.get("registered_at_unix_seconds")
    require(type(stamp) is int and stamp < int(time.time()), "CodeQL v0.9.2 plan must be registered before execution")
    require(plan.get("output_root") == "reports/raw/swift-common-v2", "CodeQL v0.9.2 output root must preserve the v0.9.0 common runner root")
    population, common_rows, swift_rows, cases, digest = common.load_common_population(root)
    require(len(common_rows) == 1108 and len(swift_rows) == 108, "fixed common-1108 / Swift-108 population required")
    require(plan.get("population_sha256") == digest and plan.get("fixture_revision") == population["fixture_revision"], "v0.9.0 population identity drift")
    contract_ref = plan.get("execution_contract")
    require(isinstance(contract_ref, dict) and contract_ref.get("path") == PARENT_EXECUTION_CONTRACT,
            "CodeQL execution contract must reuse the immutable v0.9.0 common contract")
    contract_path = bound_file(root, contract_ref)
    require(contract_ref.get("sha256") == sha(contract_path), "CodeQL immutable execution-contract digest mismatch")
    contract = read(contract_path)
    require(contract.get("population_sha256") == digest and contract.get("fixture_revision") == population["fixture_revision"],
            "CodeQL immutable execution contract population mismatch")
    require(contract.get("phases", {}).get("extraction", {}).get("wall_clock_seconds") == 150 and
            contract.get("phases", {}).get("analysis", {}).get("wall_clock_seconds") == 75,
            "CodeQL extraction or analysis budgets differ from the immutable v0.9.0 contract")
    require(plan.get("phase_sequences") == contract.get("phase_sequences"),
            "CodeQL phase sequences differ from the immutable v0.9.0 contract")
    expected_phase = {
        case_id: ("persistence" if cases[case_id]["template_id"] == "dfb-template-native-persistence" else "standard")
        for case_id in cases
    }
    require({case_id: row.get("phase_sequence") for case_id, row in plan.get("cases", {}).items()} == expected_phase,
            "CodeQL case phase selection differs from the registered common-108 roster")
    require(plan.get("qualification_control_projection_sha256") == qualification_binding.plan_projection_sha256(plan), "CodeQL qualification projection digest mismatch")
    selected = plan.get("cases")
    require(isinstance(selected, dict) and set(selected) == set(cases), "plan must cover the exact common-108 Swift projection")
    require(all(row.get("configuration") in plan.get("configurations", {}) and row.get("disposition") == "attempt" for row in selected.values()), "all common-108 cases must have an explicit attempted configuration")
    identity = plan.get("identity")
    require(isinstance(identity, dict) and identity.get("tool") == "codeql", "CodeQL identity required")
    require(identity.get("tool_version") == CLI_VERSION and identity.get("adapter_version") == ADAPTER, "CodeQL 2.27.2 / v092 adapter identity required")
    pins = plan.get("runtime", {}).get("pins", {})
    require(pins.get("cli_version") == CLI_VERSION and pins.get("cli_build") == CLI_BUILD, "CodeQL CLI build pin mismatch")
    require(identity.get("tool_build_identity") == (
        "codeql:" + CLI_BUILD + ";swift-extractor:" + pins.get("extractor_sha256", "") +
        ";schema:" + pins.get("schema_sha256", "") + ";packs:" + pins.get("packs_manifest_sha256", "")
    ), "CodeQL build identity must bind CLI, Swift extractor, schema, and query-pack manifest")
    pack = plan.get("codeql_packs")
    require(isinstance(pack, dict), "exact CodeQL runtime-pack binding required")
    expected_pack_root = Path(plan.get("runtime", {}).get("packs", "")).resolve()
    require(Path(pack.get("root", "")).is_absolute() and Path(pack["root"]).resolve() == expected_pack_root, "CodeQL runtime-pack root must be the dedicated custom Swift candidate pack")
    require(Path(plan["runtime"]["packs"]).is_absolute() and Path(plan["runtime"]["packs"]).resolve() == expected_pack_root, "CodeQL runtime-pack roots differ")
    require(Path(plan["runtime"]["packs"]).is_absolute(), "CodeQL pack root must be an absolute acquired runtime path")
    require(plan["runtime"].get("swift_pack_version") == SWIFT_PACK_VERSION, "Swift query pack version mismatch")
    require(Path(plan["runtime"]["packs"]) / "codeql/swift-all" / SWIFT_PACK_VERSION == Path(plan["runtime"]["swift_pack_directory"]), "Swift pack directory mismatch")
    validate_pack_bindings(plan)
    require(isinstance(plan.get("identity_components"), list) and plan["identity_components"], "exact CodeQL runtime component identities required")
    qualification_binding.expected_identity_components(plan)
    if allow_qualification_pending:
        require("fresh_qualification" not in plan, "pending CodeQL plan cannot claim a qualification receipt")
        qualification = {}
    else:
        qualification = _qualification(root, plan)
    query_root = plan.get("query_root")
    require(isinstance(query_root, str) and not Path(query_root).is_absolute() and ".." not in Path(query_root).parts, "repository-bound Swift query root required")
    require(Path(query_root).parts[:3] == ("adapters", "codeql", "v0.9.2"), "Swift query root must remain under the reviewed v0.9.2 CodeQL adapter tree")
    configuration_map = plan.get("configurations")
    require(isinstance(configuration_map, dict) and isinstance(configuration_map.get("patched-codeql"), list), "CodeQL v092 configuration closure is missing")
    references = [row for rows in configuration_map.values() for row in rows]
    configuration_paths = {}
    for reference in references:
        path = bound_file(root, reference)
        configuration_paths[reference["path"]] = reference["sha256"]
        require(sha(path) == reference["sha256"], "CodeQL configuration digest mismatch: " + reference["path"])
    required_paths = (
        "scripts/swift_normal_runner_v092.py",
        "scripts/run-swift-common-v092.py",
        "scripts/swift_common_population_v2.py",
        "scripts/v092_qualification.py",
        "scripts/codeql_swift_qualification_v092.py",
        "scripts/swift_normal_reports_v092.py",
        "scripts/swift_normal_runner_v1.py",
        "scripts/swift_normal_reports_v1.py",
        "scripts/swift_v3_runner.py",
        "scripts/swift_v2_process.py",
        "scripts/swift_extraction_integrity.py",
        "scripts/swift_persistence_coverage.py",
        "scripts/swift_artifact_closure.py",
        "populations/v0.9.0.json",
        "populations/swift-synthetic-v3.json",
        "reports/releases/v0.9.0/plan.json",
    )
    for required in required_paths:
        require(repository_ref(root, required) in references, "executable plan does not bind " + required)
    require(contract_ref in references, "executable plan configuration closure omits the immutable execution contract")
    query_tree = root / query_root / "queries"
    require(query_tree.is_dir() and not query_tree.is_symlink(), "CodeQL query root is missing or symlinked")
    actual_query_closure = {
        path.relative_to(root).as_posix()
        for path in query_tree.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    require(actual_query_closure, "CodeQL query closure is empty")
    require(actual_query_closure <= set(configuration_paths), "CodeQL plan does not bind every query/import file")
    require(all(configuration_paths[item] == sha(root / item) for item in actual_query_closure), "CodeQL query closure changed after plan registration")
    return plan, qualification, {}


def _engine(root: Path, plan: dict, plan_path: str):
    engine = common.private_engine(root, "codeql")["runner"]
    engine.BASE = plan["query_root"]
    engine.ADAPTER = ADAPTER
    engine.patched_identity = patched_identity
    engine.verify_query_receipt = lambda selected_root, selected_plan, receipt: verify_query_receipt(
        selected_root, selected_plan, receipt, plan_path
    )
    engine.verify_revalidation = reject_revalidation
    import swift_normal_reports_v092 as reports_v092
    engine.export = reports_v092.export
    return engine


def patched_identity(banner: dict, pins: dict) -> dict:
    require(banner.get("productName") == "CodeQL" and banner.get("version") == CLI_VERSION and banner.get("sha") == CLI_BUILD, "CodeQL version/build witness mismatch")
    return {
        "tool": "codeql",
        "tool_version": CLI_VERSION,
        "tool_build_identity": "codeql:" + CLI_BUILD + ";swift-extractor:" + pins["extractor_sha256"] + ";schema:" + pins["schema_sha256"] + ";packs:" + pins["packs_manifest_sha256"],
        "adapter_version": ADAPTER,
    }


def reject_revalidation(*_args, **_kwargs):
    raise ValueError("legacy query revalidation is forbidden; v0.9.2 requires a fresh receipt")


def verify_query_receipt(root: Path, plan: dict, receipt: dict, plan_path: str) -> None:
    """Verify fresh resolve/compile-only witnesses against the exact v092 plan."""
    engine = common.private_engine(root, "codeql")["runner"]
    engine.BASE = plan["query_root"]
    require(receipt.get("plan_path") == plan_path, "query receipt must name the exact v092 plan path")
    projection_sha = qualification_binding.plan_projection_sha256(plan)
    if receipt.get("execution_plan_projection_sha256") is not None:
        require(receipt["execution_plan_projection_sha256"] == projection_sha, "query receipt execution projection mismatch")
    else:
        require(receipt.get("plan_sha256") == sha(root / plan_path), "pre-qualification query receipt plan digest mismatch")
    capture_root_value = receipt.get("execution_root")
    require(isinstance(capture_root_value, str) and Path(capture_root_value).is_absolute() and Path(capture_root_value).is_dir(),
            "query receipt must bind an existing absolute capture root")
    capture_root = Path(capture_root_value).resolve()
    runtime = plan["runtime"]
    expected = {
        str(path.relative_to(root))
        for case in common.load_population(root)[1].values()
        for path in engine.query_files(case).values()
    }
    records = receipt.get("queries")
    require(isinstance(records, dict) and set(records) == expected, "query receipt membership differs from common-108 query closure")
    for query, row in records.items():
        require(row.get("query_sha256") == sha(root / query), "query source changed after qualification: " + query)
        captured_query = capture_root / query
        require(captured_query.is_file() and not captured_query.is_symlink() and sha(captured_query) == row["query_sha256"],
                "captured CodeQL query bytes differ from the versioned source: " + query)
        for kind in ("resolve", "compile"):
            command_path = qualification_binding.bound_repository_file(root, row.get(kind), "CodeQL query " + kind + " command")
            captured_command = capture_root / row[kind]["path"]
            require(captured_command.is_file() and not captured_command.is_symlink() and sha(captured_command) == row[kind]["sha256"],
                    "query-check command differs from its retained capture-root copy")
            command = read(command_path)
            if kind == "resolve":
                argv = [runtime["codeql"], "resolve", "library-path", "--query=" + str(Path(receipt["execution_root"]) / query), "--additional-packs=" + runtime["packs"], "--format=json"]
            else:
                argv = [runtime["codeql"], "query", "compile", str(Path(receipt["execution_root"]) / query), "--check-only", "--additional-packs=" + runtime["packs"], "--threads=2", "--ram=2048"]
            require(command.get("argv") == argv and command.get("cwd") == str(capture_root) and command.get("exit_status") == 0 and command.get("timed_out") is False and command.get("cleanup_status") == "tracked-processes-stopped", "fresh CodeQL query-check command failed or differs")
            elapsed, deadline = command.get("elapsed_seconds"), command.get("deadline_seconds")
            require(type(elapsed) in (int, float) and type(deadline) in (int, float) and 0 <= elapsed <= deadline <= 75, "query-check command exceeds its fresh per-command budget")
            stdout_ref = row[kind + "_stdout"]
            stdout_path = qualification_binding.bound_repository_file(root, stdout_ref, "CodeQL query " + kind + " stdout")
            captured_stdout = capture_root / stdout_ref["path"]
            require(stdout_path.is_file() and captured_stdout.is_file() and not captured_stdout.is_symlink() and
                    sha(captured_stdout) == stdout_ref["sha256"], "query-check stdout differs from its capture-root copy")
        resolution = read(bound_file(root, row["resolution_stdout"]))
        pack_directory = str(Path(runtime["swift_pack_directory"]))
        require(pack_directory in resolution.get("libraryPath", []), "query resolved without the exact v0.9.2 Swift pack")
        require(resolution.get("dbscheme") == pack_directory + "/swift.dbscheme", "query resolved a different Swift schema")
        allowed_query = str((Path(receipt["execution_root"]) / query).parent)
        require(all(value == allowed_query or Path(value).is_relative_to(Path(runtime["packs"])) for value in resolution["libraryPath"]), "query resolution escaped the reviewed query/pack roots")
        require(not any("/codeql/swift-all/" in value and value != pack_directory for value in resolution["libraryPath"]), "mixed Swift query-pack resolution")


def check_queries(root: Path, plan_path: str, output: Path) -> dict:
    """Run fresh resolve/compile-only checks against a pre-qualification plan."""
    root = Path(root).resolve()
    plan_path = Path(plan_path).as_posix()
    plan, _qualification, _ = validate_plan(root, plan_path, allow_qualification_pending=True)
    require(os.environ.get("DATAFLOWBENCH_V092_QUALIFICATION") == "1", "CodeQL query checks require the guarded qualification workflow")
    require(os.environ.get("DATAFLOWBENCH_V092_GROUP_ID") == GROUP_ID, "CodeQL qualification group identity mismatch")
    output = Path(output).resolve()
    require(output.is_relative_to(root / QUALIFICATION_PREFIX), "query-check output must remain under v0.9.2 qualification evidence")
    engine = _engine(root, plan, plan_path)
    receipt = engine.check_queries(root, plan_path, output)
    receipt["execution_plan_projection_sha256"] = qualification_binding.plan_projection_sha256(plan)
    receipt["plan_path"] = plan_path
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def execute(root: Path, plan_path: str, query_receipt_path: str, output: Path) -> dict:
    root = Path(root).resolve()
    plan_path = Path(plan_path).as_posix()
    plan, _qualification, _ = validate_plan(root, plan_path)
    require(os.environ.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION") == "1", "v092 Swift runner must be launched by the exclusive release executor")
    require(os.environ.get("DATAFLOWBENCH_V092_GROUP_ID") == GROUP_ID, "release executor group identity mismatch")
    engine = _engine(root, plan, plan_path)
    query_reference = repository_ref(root, query_receipt_path)
    receipt = read(bound_file(root, query_reference))
    verify_query_receipt(root, plan, receipt, plan_path)
    reservation = {
        "plan_sha256": sha(root / plan_path),
        "query_qualification": query_reference,
        "launch_free_bytes": engine.LAUNCH_CAPACITY,
        "exclusive_analyzer_slot": True,
    }
    return engine.execute(root, plan_path, Path(output).resolve(), reservation)

