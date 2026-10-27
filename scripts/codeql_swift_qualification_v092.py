"""Replay the bounded CodeQL/Swift qualification evidence for v0.9.2.

The module intentionally consumes native decoded CodeQL tables and command
receipts. Summary booleans and declared assessment labels are never sufficient
to authorize the Swift lane.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shlex
import re

import swift_common_population_v2 as common
import swift_entry_observation
import v092_qualification as qualification


GROUP_ID = "codeql-swift-common108"
ENTRY_IDS = (
    "direct-positive", "direct-negative",
    "local-overwrite-positive", "local-overwrite-negative",
    "array-element-positive", "array-element-negative",
    "callback-registration-positive", "callback-registration-negative",
    "wrapped", "wrapped-negative",
)
ENTRY_EXPECTED = {
    "direct-positive": "reached", "direct-negative": "not-reached",
    "local-overwrite-positive": "reached", "local-overwrite-negative": "not-reached",
    "array-element-positive": "reached", "array-element-negative": "not-reached",
    "callback-registration-positive": "reached", "callback-registration-negative": "not-reached",
    "wrapped": "reached", "wrapped-negative": "not-reached",
}
KNOWN_SEMANTIC_LIMITS = {"array-element-negative", "callback-registration-positive"}
MODEL_EXPECTED = {
    "dfb-taint-swift-model-declared-source-positive": {"off": "not-reached", "on": "reached"},
    "dfb-taint-swift-model-declared-source-negative": {"off": "not-reached", "on": "not-reached"},
}
SANITIZER_EXPECTED = {
    "dfb-taint-swift-model-sanitizer-kill-positive": {"off": "reached", "on": "reached"},
    "dfb-taint-swift-model-sanitizer-kill-negative": {"off": "reached", "on": "not-reached"},
    "dfb-taint-swift-model-sanitizer-selectivity-positive": {"off": "reached", "on": "reached"},
    "dfb-taint-swift-model-sanitizer-selectivity-negative": {"off": "reached", "on": "not-reached"},
}
ENTRY_QUERY_ROLES = ("entry", "diagnostics", "kernel-flow")
ENTRY_PHASES = (
    "database-create", "resolve-database", "entry-query", "entry-decode",
    "diagnostics-query", "diagnostics-decode", "kernel-flow-query", "kernel-flow-decode",
)
ACTIVATION_PHASES = ("database-create", "resolve-database", "flow-query", "flow-decode")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {description} {path}: {exc}") from exc
    require(isinstance(value, dict), description + " must be a JSON object")
    return value


def bound_file(root: Path, reference: object, description: str) -> Path:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, description + " needs exact path/SHA")
    rel = Path(reference["path"])
    require(not rel.is_absolute() and ".." not in rel.parts, description + " path is unsafe")
    path = root / rel
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), description + " is missing or escaped")
    require(sha(path) == reference["sha256"], description + " digest mismatch")
    return path


def bound_capture_file(root: Path, capture_root: Path, reference: object, description: str) -> Path:
    path = bound_file(root, reference, description)
    captured = capture_root / reference["path"]
    require(captured.is_file() and not captured.is_symlink() and sha(captured) == reference["sha256"],
            description + " differs from the retained capture-root copy")
    return path


def _table_rows(root: Path, reference: object, description: str) -> list:
    output_path = bound_file(root, reference, description)
    output = read_json(output_path, description)
    selected = output.get("#select")
    require(isinstance(selected, dict) and isinstance(selected.get("tuples"), list), description + " must retain native #select.tuples")
    return selected["tuples"]


def _validate_control_plan(root: Path, plan: dict, control: dict) -> tuple[dict, dict]:
    require(control.get("schema") == "analyzer-qualification-control-plan/v092", "unknown CodeQL control-plan schema")
    require(control.get("group_id") == GROUP_ID, "CodeQL control-plan group mismatch")
    projection = qualification.plan_projection_sha256(plan)
    require(control.get("execution_plan_projection_sha256") == projection, "CodeQL control-plan projection mismatch")
    require(control.get("identity") == plan.get("identity"), "CodeQL control-plan identity mismatch")
    require(control.get("identity_components") == plan.get("identity_components"), "CodeQL control-plan component identity mismatch")
    require(control.get("population_sha256") == plan.get("population_sha256"), "CodeQL control-plan population mismatch")
    require(control.get("fixture_revision") == plan.get("fixture_revision"), "CodeQL control-plan fixture revision mismatch")
    require(control.get("case_arm_budget_seconds") == 75 and control.get("extraction_budget_seconds") == 150,
            "CodeQL control phase ceilings changed")
    require(control.get("total_budget_seconds") == 5400 and control.get("scratch_allowance_bytes") == 4 * 1024**3,
            "CodeQL total-time or scratch ceiling changed")

    manifest_path = root / "adapters/codeql/swift-entry-extractor-v1/control-manifest.json"
    manifest = read_json(manifest_path, "registered CodeQL entry control manifest")
    entries = control.get("entry_extractor")
    require(isinstance(entries, dict), "CodeQL entry controls are missing")
    require(entries.get("control_ids") == list(ENTRY_IDS), "CodeQL entry control roster must preserve the exact registered ten")
    require(entries.get("controls") == {name: "adapters/codeql/swift-entry-extractor-v1/controls/" + name + "/main.swift" for name in ENTRY_IDS},
            "CodeQL entry control paths differ from the registered ten fixtures")
    require(set(manifest.get("files", {})) == {name + "/main.swift" for name in ENTRY_IDS}, "registered entry manifest membership changed")
    for name in ENTRY_IDS:
        path = root / entries["controls"][name]
        require(path.is_file() and sha(path) == manifest["files"][name + "/main.swift"], "registered entry fixture drift: " + name)
    query_refs = entries.get("queries")
    require(isinstance(query_refs, dict) and set(query_refs) == set(ENTRY_QUERY_ROLES), "entry control queries must bind entry, diagnostics and kernel-flow")
    for role, reference in query_refs.items():
        query_path = bound_file(root, reference, "entry " + role + " query")
        require(query_path.suffix == ".ql" and "adapters/codeql/swift-entry-extractor-v1/queries" in query_path.as_posix(),
                "entry control query escaped the reviewed query package")

    population, common_rows, _swift, cases, digest = common.load_common_population(root)
    require(digest == plan.get("population_sha256"), "CodeQL controls do not use the fixed v0.9.0 population")
    case_paths = {row["id"]: row["path"] for row in common_rows}
    for case_id, case in cases.items():
        case["path"] = case_paths[case_id]
    expected_cases = {
        "model_activation": set(MODEL_EXPECTED),
        "sanitizer_activation": set(SANITIZER_EXPECTED),
    }
    query_profiles = control.get("activation_queries")
    require(isinstance(query_profiles, dict) and set(query_profiles) == {"model_activation", "sanitizer_activation"},
            "dimension-specific model/sanitizer on/off query profiles are missing")
    query_root = plan.get("query_root")
    require(isinstance(query_root, str), "versioned CodeQL common108 query root is missing")
    standard_root = Path(query_root) / "queries/standard"
    expected_activation_paths = {
        "model_activation": {
            "off": standard_root / "kernel-flow.ql",
            "on": standard_root / "modeling-flow.ql",
        },
        "sanitizer_activation": {
            "off": standard_root / "modeling-flow-sanitizer-off.ql",
            "on": standard_root / "modeling-flow.ql",
        },
    }
    for dimension, arms in query_profiles.items():
        require(isinstance(arms, dict) and set(arms) == {"off", "on"}, "CodeQL " + dimension + " must bind both off and on queries")
        for arm, reference in arms.items():
            query_path = bound_file(root, reference, "CodeQL " + dimension + " " + arm + " query")
            expected_path = root / expected_activation_paths[dimension][arm]
            require(query_path == expected_path and query_path.suffix == ".ql",
                    "CodeQL activation query differs from the production common108 on/off profile")

    counterfactual = control.get("sanitizer_counterfactual")
    require(isinstance(counterfactual, dict) and set(counterfactual) == {"production_query", "counterfactual_query", "diff"},
            "sanitizer-off counterfactual needs separately bound production, control, and diff files")
    production_ref = query_profiles["sanitizer_activation"]["on"]
    control_ref = query_profiles["sanitizer_activation"]["off"]
    require(counterfactual["production_query"] == production_ref and counterfactual["counterfactual_query"] == control_ref,
            "sanitizer counterfactual query refs differ from the registered on/off arms")
    production_path = bound_file(root, production_ref, "CodeQL production modeling-flow query")
    control_path = bound_file(root, control_ref, "CodeQL sanitizer-off counterfactual query")
    patch_path = bound_file(root, counterfactual["diff"], "CodeQL sanitizer-off unified diff")
    require(patch_path.suffix == ".patch", "sanitizer-off counterfactual diff must be a retained patch file")
    production_source = production_path.read_text()
    sanitizer_barrier = "predicate isBarrier(DataFlow::Node n) { sanitizer(n) or summaryBarrier(n) }"
    no_sanitizer_barrier = "predicate isBarrier(DataFlow::Node n) { summaryBarrier(n) }"
    require(production_source.count(sanitizer_barrier) == 1 and
            control_path.read_text() == production_source.replace(sanitizer_barrier, no_sanitizer_barrier, 1),
            "sanitizer-off query must differ only by removing the sanitizer barrier while retaining summaryBarrier")
    patch_lines = patch_path.read_text().splitlines()
    removed = [line[1:] for line in patch_lines if line.startswith("-") and not line.startswith("---")]
    added = [line[1:] for line in patch_lines if line.startswith("+") and not line.startswith("+++")]
    require(removed == [" " + sanitizer_barrier] and added == [" " + no_sanitizer_barrier],
            "sanitizer-off patch must retain the exact one-expression counterfactual diff")
    for dimension, expected_ids in expected_cases.items():
        actual = control.get(dimension)
        require(isinstance(actual, dict) and set(actual.get("case_ids", [])) == expected_ids,
                "CodeQL " + dimension + " must retain its exact positive/near-miss case set")
        for case_id in expected_ids:
            require(case_id in cases and cases[case_id].get("polarity") in ("positive", "negative"), "unknown CodeQL activation fixture")
    return manifest, cases


def _commands(root: Path, plan: dict, raw: dict, phases: tuple[str, ...], output_dir: Path,
              *, query_paths: dict[str, str], fixture_files: list[str]) -> list[dict]:
    references = raw.get("commands")
    require(isinstance(references, list) and len(references) == len(phases), "CodeQL control must retain every registered command phase")
    runtime = plan["runtime"]
    capture_root_text = raw.get("capture_root")
    capture_output_text = raw.get("capture_output_dir")
    require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute() and Path(capture_root_text).is_dir(),
            "CodeQL raw control must bind its original capture root")
    capture_root = Path(capture_root_text).resolve()
    require(isinstance(capture_output_text, str) and Path(capture_output_text).is_absolute(),
            "CodeQL raw control must bind its original output directory")
    capture_output_dir = Path(capture_output_text).resolve()
    relative_output = output_dir.resolve().relative_to(root.resolve())
    require(capture_output_dir == (capture_root / relative_output).resolve(),
            "CodeQL capture output directory does not match the retained evidence path")
    require(capture_output_dir.is_dir(), "CodeQL capture output directory is missing")
    source_dir = (capture_output_dir / "source").resolve()
    db_path = (capture_output_dir / "database").resolve()
    compile_argv = [runtime["compiler"], "-swift-version", "6", "-Onone", "-sdk", runtime["sdk"],
                    "-target", runtime.get("swift_target", "arm64-apple-macosx26.5"), "-module-name", "DataFlowBenchTaintSwift",
                    "-module-cache-path", str((capture_output_dir / "cache").resolve()),
                    *[str((source_dir / name).resolve()) for name in fixture_files], "-o", str((capture_output_dir / "never-executed").resolve())]
    expected_argv = {
        "database-create": [runtime["codeql"], "database", "create", str(db_path), "--language=swift",
                            "--search-path=" + runtime["extractor_root"], "--source-root=" + str(source_dir),
                            "--threads=2", "--ram=2048", "--command=" + shlex.join(compile_argv)],
        "resolve-database": [runtime["codeql"], "resolve", "database", "--format=json", str(db_path)],
    }
    for role, query in query_paths.items():
        bqrs = str((capture_output_dir / (role + ".bqrs")).resolve())
        decoded = str((capture_output_dir / (role + ".json")).resolve())
        expected_argv[role + "-query"] = [runtime["codeql"], "query", "run", query,
                                           "--database=" + str(db_path), "--output=" + bqrs,
                                           "--additional-packs=" + runtime["packs"], "--threads=2", "--ram=2048"]
        expected_argv[role + "-decode"] = [runtime["codeql"], "bqrs", "decode", bqrs, "--format=json", "--output=" + decoded]
    records = []
    for reference, phase in zip(references, phases):
        path = bound_capture_file(root, capture_root, reference, "CodeQL " + phase + " command")
        require(path.parent.resolve() == output_dir.resolve(), "CodeQL command receipt escaped its fresh control attempt")
        command = read_json(path, "CodeQL command")
        expected_role = "extraction" if phase == "database-create" else "analysis"
        require(command.get("phase_id") == phase and command.get("role") == expected_role, "CodeQL command phase identity mismatch")
        require(command.get("argv") == expected_argv[phase], "CodeQL command argv differs from the executable control contract: " + phase)
        require(command.get("cwd") == str(capture_root), "CodeQL command working directory differs from its bound capture root")
        require(command.get("exit_status") == 0 and command.get("timed_out") is False and
                command.get("cleanup_status") == "tracked-processes-stopped", "CodeQL control process failed or cleanup is uncertain: " + phase)
        elapsed, deadline = command.get("elapsed_seconds"), command.get("deadline_seconds")
        phase_limit = 150 if phase == "database-create" else 75
        require(type(elapsed) in (int, float) and type(deadline) in (int, float) and 0 <= elapsed <= deadline <= phase_limit,
                "CodeQL control phase exceeded its registered deadline: " + phase)
        records.append(command)
    require(sum(row["elapsed_seconds"] for row in records if row.get("role") == "analysis") <= 75,
            "CodeQL per-control analysis exceeded 75 seconds")
    return records


def _entry_observation(root: Path, raw: dict, output_dir: Path) -> dict:
    query_outputs = raw.get("query_outputs")
    require(isinstance(query_outputs, dict) and set(query_outputs) == set(ENTRY_QUERY_ROLES), "entry control lacks native decoded query outputs")
    capture_root = Path(raw["capture_root"]).resolve()
    rows = {role: _table_rows(root, reference, "CodeQL entry " + role + " output") for role, reference in query_outputs.items()}
    for role, reference in query_outputs.items():
        bound_capture_file(root, capture_root, reference, "CodeQL entry " + role + " output")
    require(raw.get("entry_rows") == rows["entry"] and raw.get("exact_endpoint_rows") == rows["diagnostics"] and
            raw.get("flow_rows") == rows["kernel-flow"], "CodeQL entry raw tables differ from retained decoded outputs")
    observation = swift_entry_observation.classify(rows["entry"], rows["diagnostics"], rows["kernel-flow"])
    require(raw.get("observation") == observation, "CodeQL entry interpretation differs from raw native tables")
    if observation.get("status") == "DIAGNOSTIC":
        capture_output = Path(raw["capture_output_dir"]).resolve()
        require(observation.get("entry_owner") == {"file": str((capture_output / "source/main.swift").resolve()), "module": "DataFlowBenchTaintSwift"},
                "CodeQL entry scope is not owned by the exact fixture source/module")
        exact = [row for row in rows["diagnostics"] if len(row) == 10 and row[3] in ("source", "sink") and row[4] == 1 and row[5] == 1]
        require(len([row for row in exact if row[3] == "source" and row[9] == "DataFlowBenchTaintSwift:dfb_source()"] ) == 1 and
                len([row for row in exact if row[3] == "sink" and row[9] == "DataFlowBenchTaintSwift:dfb_sink(_:)" ]) == 1,
                "CodeQL exact source/sink declaration identities are missing or ambiguous")
    return observation


def _fixture_hashes(root: Path, case: dict) -> dict[str, str]:
    case_path = root / case["path"]
    return {name: sha(case_path.parent / name) for name in case["fixture_files"]}


def _marker_line(root: Path, case: dict, marker: str) -> tuple[str, int]:
    matches = []
    for name in case["fixture_files"]:
        path = root / case["path"]
        fixture = path.parent / name
        for line_number, line in enumerate(fixture.read_text().splitlines(), 1):
            if marker in line:
                matches.append((name, line_number))
    require(len(matches) == 1, "CodeQL activation marker must resolve to one exact fixture line: " + marker)
    return matches[0]


def _activation_observation(root: Path, case: dict, arm: str, rows: list) -> str:
    require(arm in ("off", "on"), "unknown model activation arm")
    require(all(isinstance(row, list) and len(row) == 5 and isinstance(row[0], str) and isinstance(row[2], str) and
                all(type(row[index]) is int and row[index] > 0 for index in (1, 3, 4)) for row in rows), "malformed CodeQL activation flow rows")
    expected_pairs = case.get("expected_flows", [])
    expected_nonflows = case.get("expected_nonflows", [])
    anchors = case.get("source_anchors", [])
    sinks = case.get("sink_anchors", [])
    require(len(anchors) == 1 and len(sinks) == 1, "qualification fixture must have one anchored source and sink")
    source_file, source_line = _marker_line(root, case, anchors[0]["marker"])
    sink_file, sink_line = _marker_line(root, case, sinks[0]["marker"])
    exact = [row for row in rows if row[0] == source_file and row[1] == source_line and row[2] == sink_file and row[3] == sink_line]
    require(len(expected_pairs) + len(expected_nonflows) == 1, "qualification fixture must declare exactly one positive or near-miss flow pair")
    expected_pair = expected_pairs[0] if expected_pairs else expected_nonflows[0]
    require(expected_pair["source"] == anchors[0]["marker"] and expected_pair["sink"] == sinks[0]["marker"],
            "population flow pair differs from exact source/sink markers")
    require(len(exact) <= 1, "CodeQL activation output duplicated the exact anchored flow")
    observed = bool(exact)
    return "reached" if observed else "not-reached"


def replay_entry_controls(root: Path, plan: dict, control: dict, evidence: dict) -> dict:
    manifest, _cases = _validate_control_plan(root, plan, control)
    require(evidence.get("schema") == "codeql-entry-extractor-evidence/v092", "unknown CodeQL entry evidence schema")
    require(evidence.get("group_id") == GROUP_ID and evidence.get("identity") == plan["identity"] and
            evidence.get("identity_components") == plan["identity_components"], "CodeQL entry evidence identity mismatch")
    require(evidence.get("execution_plan_projection_sha256") == qualification.plan_projection_sha256(plan), "CodeQL entry evidence plan projection mismatch")
    records = evidence.get("controls")
    require(isinstance(records, list) and len(records) == 10, "CodeQL entry evidence must retain exactly ten controls")
    actual = set()
    observations = {}
    for record in records:
        require(isinstance(record, dict), "CodeQL entry evidence row is malformed")
        control_id = record.get("control_id")
        require(control_id in ENTRY_IDS and control_id not in actual, "CodeQL entry control is unknown or duplicated")
        actual.add(control_id)
        raw_path = bound_file(root, record.get("raw"), "CodeQL raw entry control")
        raw = read_json(raw_path, "CodeQL raw entry control")
        output_dir = raw_path.parent
        require(raw.get("schema") == "codeql-entry-control-raw/v092", "unknown CodeQL raw entry schema")
        require(raw.get("group_id") == GROUP_ID and raw.get("control_id") == control_id, "CodeQL raw entry routing mismatch")
        require(raw.get("execution_plan_projection_sha256") == qualification.plan_projection_sha256(plan), "CodeQL raw entry plan projection mismatch")
        require(raw.get("identity") == plan["identity"] and raw.get("identity_components") == plan["identity_components"], "CodeQL raw entry runtime identity mismatch")
        fixture = root / control["entry_extractor"]["controls"][control_id]
        expected_hash = manifest["files"][control_id + "/main.swift"]
        require(raw.get("fixture_sha256") == expected_hash and sha(fixture) == expected_hash, "CodeQL raw entry fixture digest mismatch")
        require(raw.get("source_files") == {"main.swift": reference_for(root, fixture)}, "CodeQL raw entry source file reference mismatch")
        capture_root = Path(raw.get("capture_root", "")).resolve()
        require(capture_root.is_dir(), "CodeQL entry raw capture root is missing")
        capture_output = Path(raw.get("capture_output_dir", "")).resolve()
        require(capture_output == (capture_root / raw_path.parent.resolve().relative_to(root.resolve())).resolve(),
                "CodeQL entry capture output directory does not match retained evidence path")
        captured_fixture = capture_output / "source/main.swift"
        require(captured_fixture.is_file() and sha(captured_fixture) == expected_hash,
                "CodeQL entry capture fixture differs from its registered source")
        query_paths = {}
        for role, reference in control["entry_extractor"]["queries"].items():
            current_query = bound_file(root, reference, "entry " + role + " query")
            captured_query = capture_root / reference["path"]
            require(captured_query.is_file() and not captured_query.is_symlink() and sha(captured_query) == sha(current_query),
                    "CodeQL entry capture query bytes differ from the reviewed query")
            query_paths[role] = str(captured_query.resolve())
        _commands(root, plan, raw, ENTRY_PHASES, output_dir,
                  query_paths={"entry": query_paths["entry"], "diagnostics": query_paths["diagnostics"], "kernel-flow": query_paths["kernel-flow"]},
                  fixture_files=["main.swift"])
        observation = _entry_observation(root, raw, output_dir)
        require(observation.get("status") == "DIAGNOSTIC", "CodeQL structural entry observation is typed incomplete: " + control_id)
        observed = observation["diagnostic"]
        require(record.get("observed") == observation, "CodeQL entry summary differs from raw replay")
        observations[control_id] = observed
    require(actual == set(ENTRY_IDS), "CodeQL entry evidence omitted one or more registered controls")
    mismatches = {control_id: {"expected": expected, "observed": observations[control_id]}
                  for control_id, expected in ENTRY_EXPECTED.items() if observations[control_id] != expected}
    structural_failures = set(mismatches) - KNOWN_SEMANTIC_LIMITS
    require(not structural_failures, "CodeQL direct/overwrite/wrapped control failed: " + json.dumps({key: mismatches[key] for key in structural_failures}, sort_keys=True))
    assessment = {
        "status": "measurement-with-known-limits" if mismatches else "qualified",
        "execution_eligible": True,
        "strict_qualified": not bool(mismatches),
        "case_count": 10,
        "observations": observations,
        "known_limit_deltas": mismatches,
        "scored_activation": False,
    }
    require(evidence.get("assessment") == assessment, "CodeQL entry reviewed assessment differs from raw evidence")
    return assessment


def reference_for(root: Path, path: Path) -> dict:
    return {"path": path.resolve().relative_to(root.resolve()).as_posix(), "sha256": sha(path)}


def replay_activation_dimension(root: Path, plan: dict, control: dict, evidence: dict, *, dimension: str) -> dict:
    expected = MODEL_EXPECTED if dimension == "model_activation" else SANITIZER_EXPECTED if dimension == "sanitizer_activation" else None
    require(expected is not None, "unknown CodeQL activation dimension")
    require(evidence.get("schema") == "codeql-activation-evidence/v092", "unknown CodeQL activation evidence schema")
    require(evidence.get("dimension") == dimension and evidence.get("group_id") == GROUP_ID, "CodeQL activation evidence routing mismatch")
    require(evidence.get("identity") == plan["identity"] and evidence.get("identity_components") == plan["identity_components"], "CodeQL activation evidence identity mismatch")
    require(evidence.get("execution_plan_projection_sha256") == qualification.plan_projection_sha256(plan), "CodeQL activation evidence projection mismatch")
    _manifest, cases = _validate_control_plan(root, plan, control)
    records = evidence.get("controls")
    require(isinstance(records, list) and len(records) == len(expected) * 2, "CodeQL activation evidence has an incomplete matrix")
    observed: dict[str, dict[str, str]] = {}
    actual = set()
    query_profile = {arm: bound_file(root, ref, "CodeQL " + dimension + " " + arm + " activation query").resolve()
                     for arm, ref in control["activation_queries"][dimension].items()}
    for record in records:
        require(isinstance(record, dict), "CodeQL activation record is malformed")
        case_id, arm = record.get("case_id"), record.get("arm")
        require(case_id in expected and arm in ("off", "on") and (case_id, arm) not in actual, "CodeQL activation control is unknown or duplicated")
        actual.add((case_id, arm))
        case = cases[case_id]
        raw_path = bound_file(root, record.get("raw"), "CodeQL raw activation control")
        raw = read_json(raw_path, "CodeQL raw activation control")
        output_dir = raw_path.parent
        capture_root_text = raw.get("capture_root")
        capture_output_text = raw.get("capture_output_dir")
        require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute() and Path(capture_root_text).is_dir(),
                "CodeQL activation raw capture root is missing")
        capture_root = Path(capture_root_text).resolve()
        require(isinstance(capture_output_text, str) and Path(capture_output_text).is_absolute(),
                "CodeQL activation raw capture output directory is missing")
        capture_output = Path(capture_output_text).resolve()
        require(capture_output == (capture_root / output_dir.resolve().relative_to(root.resolve())).resolve(),
                "CodeQL activation capture output directory does not match retained evidence path")
        require(raw.get("schema") == "codeql-activation-control-raw/v092", "unknown CodeQL activation raw schema")
        require(raw.get("dimension") == dimension and raw.get("case_id") == case_id and raw.get("arm") == arm, "CodeQL activation raw routing mismatch")
        require(raw.get("identity") == plan["identity"] and raw.get("identity_components") == plan["identity_components"], "CodeQL activation raw identity mismatch")
        require(raw.get("execution_plan_projection_sha256") == qualification.plan_projection_sha256(plan), "CodeQL activation raw projection mismatch")
        fixture_hashes = _fixture_hashes(root, case)
        require(raw.get("fixture_hashes") == fixture_hashes, "CodeQL activation fixture bytes differ from the fixed population")
        for name, digest in fixture_hashes.items():
            captured_fixture = capture_output / "source" / name
            require(captured_fixture.is_file() and sha(captured_fixture) == digest,
                    "CodeQL activation capture fixture differs from the fixed population: " + name)
        query_ref = control["activation_queries"][dimension][arm]
        current_query = query_profile[arm]
        captured_query = capture_root / query_ref["path"]
        require(captured_query.is_file() and not captured_query.is_symlink() and sha(captured_query) == sha(current_query),
                "CodeQL activation capture query bytes differ from the reviewed query")
        flow_query = str(captured_query.resolve())
        _commands(root, plan, raw, ACTIVATION_PHASES, output_dir, query_paths={"flow": flow_query}, fixture_files=case["fixture_files"])
        flow_output_ref = raw.get("query_outputs", {}).get("flow")
        bound_capture_file(root, capture_root, flow_output_ref, "CodeQL activation flow output")
        rows = _table_rows(root, flow_output_ref, "CodeQL activation flow output")
        require(raw.get("flow_rows") == rows, "CodeQL activation flow rows differ from native output")
        replayed = _activation_observation(root, case, arm, rows)
        require(raw.get("observed") == replayed and record.get("observed") == replayed, "CodeQL activation summary differs from exact anchor replay")
        observed.setdefault(case_id, {})[arm] = replayed
    require(actual == {(case_id, arm) for case_id in expected for arm in ("off", "on")}, "CodeQL activation evidence omitted an on/off arm")
    require(all(set(value) == {"off", "on"} for value in observed.values()), "CodeQL activation arm pair is incomplete")
    mismatches = [
        {"case_id": case_id, "arm": arm, "expected": wanted, "observed": observed[case_id][arm]}
        for case_id, arms in expected.items() for arm, wanted in arms.items()
        if observed[case_id][arm] != wanted
    ]
    require(not mismatches, "CodeQL " + dimension + " did not demonstrate registered positive/near-miss transitions: " + json.dumps(mismatches, sort_keys=True))
    assessment = {
        "status": "qualified",
        "execution_eligible": True,
        "strict_qualified": True,
        "case_count": len(expected),
        "case_arm_count": len(expected) * 2,
        "observations": observed,
        "scored_activation": False,
        "partition_registered": False,
    }
    require(evidence.get("assessment") == assessment, "CodeQL activation reviewed assessment differs from raw evidence")
    return assessment


def replay_control_run(root: Path, plan: dict, control: dict, run: dict, dimensions: dict) -> dict:
    """Replay every evidence file and require the digest-bound review to agree."""
    require(run.get("schema") == "analyzer-qualification-control-run/v092" and run.get("group_id") == GROUP_ID,
            "unknown CodeQL qualification control run")
    require(run.get("identity") == plan["identity"] and run.get("identity_components") == plan["identity_components"],
            "CodeQL control run identity mismatch")
    require(run.get("control_plan_sha256") == plan["qualification_control_plan"]["sha256"], "CodeQL control run plan digest mismatch")
    require(run.get("execution_plan_projection_sha256") == qualification.plan_projection_sha256(plan), "CodeQL control run projection mismatch")
    witness_ref = run.get("identity_witness")
    witness_path = bound_file(root, witness_ref, "CodeQL control runtime identity witness")
    witness = read_json(witness_path, "CodeQL control runtime identity witness")
    require(witness.get("observed") == plan["identity"], "CodeQL control runtime witness identity mismatch")
    require(witness.get("stdout") and witness.get("command"), "CodeQL control runtime witness is incomplete")
    capture_root_text = witness.get("capture_root")
    require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute() and Path(capture_root_text).is_dir(),
            "CodeQL identity witness must bind its original capture root")
    capture_root = Path(capture_root_text).resolve()
    bound_capture_file(root, capture_root, witness["stdout"], "CodeQL version stdout")
    stdout = bound_file(root, witness["stdout"], "CodeQL version stdout")
    bound_capture_file(root, capture_root, witness["command"], "CodeQL version command")
    version_command = read_json(bound_file(root, witness["command"], "CodeQL version command"), "CodeQL version command")
    require(version_command.get("argv") == [plan["runtime"]["codeql"], "version", "--format=json"] and
            version_command.get("cwd") == str(capture_root) and version_command.get("exit_status") == 0 and
            version_command.get("timed_out") is False and version_command.get("cleanup_status") == "tracked-processes-stopped",
            "CodeQL runtime identity command failed or differs from the selected CLI")
    banner = read_json(stdout, "CodeQL version banner")
    require(banner.get("productName") == "CodeQL" and banner.get("version") == plan["identity"].get("tool_version") and
            banner.get("sha") == plan["runtime"].get("pins", {}).get("cli_build"), "CodeQL runtime version/build witness mismatch")
    entry_ref = dimensions["entry_extractor"]["evidence"]
    model_ref = dimensions["model_activation"]["evidence"]
    sanitizer_ref = dimensions["sanitizer_activation"]["evidence"]
    for reference, description in ((entry_ref, "CodeQL entry evidence"), (model_ref, "CodeQL model evidence"),
                                   (sanitizer_ref, "CodeQL sanitizer evidence")):
        bound_capture_file(root, capture_root, reference, description)
    entry = read_json(bound_file(root, entry_ref, "CodeQL entry evidence"), "CodeQL entry evidence")
    model = read_json(bound_file(root, model_ref, "CodeQL model evidence"), "CodeQL model evidence")
    sanitizer = read_json(bound_file(root, sanitizer_ref, "CodeQL sanitizer evidence"), "CodeQL sanitizer evidence")
    assessment = {
        "entry_extractor": replay_entry_controls(root, plan, control, entry),
        "model_activation": replay_activation_dimension(root, plan, control, model, dimension="model_activation"),
        "sanitizer_activation": replay_activation_dimension(root, plan, control, sanitizer, dimension="sanitizer_activation"),
    }
    require(run.get("assessment") == assessment, "CodeQL control-run assessment differs from replay")
    elapsed = run.get("elapsed_seconds")
    require(type(elapsed) in (int, float) and 0 <= elapsed <= control["total_budget_seconds"],
            "CodeQL qualification capture exceeded the registered total-time budget")
    retained_phase_seconds = 0.0
    for dimension_name in ("entry_extractor", "model_activation", "sanitizer_activation"):
        evidence = read_json(bound_file(root, dimensions[dimension_name]["evidence"], "CodeQL " + dimension_name + " evidence"),
                             "CodeQL " + dimension_name + " evidence")
        for record in evidence["controls"]:
            raw = read_json(bound_file(root, record["raw"], "CodeQL retained control output"), "CodeQL retained control output")
            for command_ref in raw["commands"]:
                command = read_json(bound_file(root, command_ref, "CodeQL retained command"), "CodeQL retained command")
                retained_phase_seconds += command["elapsed_seconds"]
    retained_phase_seconds += version_command["elapsed_seconds"]
    require(elapsed + 0.05 >= retained_phase_seconds,
            "CodeQL total elapsed time is shorter than its retained serial command durations")
    return assessment
