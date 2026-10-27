"""Replay Joern's narrowly admitted Swift endpoint-identity limitation.

This module never launches Joern. It replays the registered control commands,
raw results, graph export, small CPG binary references, and the dated admission
descriptor before it can emit a diagnostic execution-eligibility receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "joern-diagnostic-admission/v1"
REVIEW_SCHEMA = "joern-diagnostic-admission-review/v1"
GROUP_ID = "joern-swift-common108"
DECISION_ID = "joern-swift-common108-endpoint-identity-gap-2026-10-20"
DECISION_DATE = "2026-10-20"
EXPECTED_INCOMPLETE = "Incomplete:EndpointIdentity:source native endpoint missing at exact anchor"
DIRECT_EXPECTATIONS = {
    "direct-positive": {"off": "reached", "on": "reached"},
    "direct-negative": {"off": "not-reached", "on": "not-reached"},
}
OPAQUE_CASES = (
    "dfb-taint-swift-model-opaque-propagator-negative",
    "dfb-taint-swift-model-opaque-propagator-positive",
    "dfb-taint-swift-model-propagator-position-negative",
    "dfb-taint-swift-model-propagator-position-positive",
)
SOURCE_LOCAL = "main.swift:<global>.dfb_source:()->Swift.String"
SINK_LOCAL = "main.swift:<global>.dfb_sink:(_:Swift.String)->ANY"
SOURCE_EXTERNAL = "DataFlowBenchTaintSwift.dfb_source:()->Swift.String"
SINK_EXTERNAL = "DataFlowBenchTaintSwift.dfb_sink:(Swift.String)->()"
ANALYSIS_COMPLETENESS = {
    "status": "unproven",
    "exhaustion_observable": False,
    "max_call_depth": 4,
    "max_args_to_allow": 1000,
    "max_output_args_expansion": 1000,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ref(path: Path, root: Path) -> dict[str, str]:
    path = path.resolve()
    require(path.is_file() and path.is_relative_to(root.resolve()), "review evidence escaped repository")
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": sha(path)}


def admission_descriptor(plan: dict, *, reviewer_path: Path, prior_run: dict,
                         prior_archive: dict) -> dict:
    """Return the only prospective admission descriptor accepted by this code."""
    reviewer_path = reviewer_path.resolve()
    require(reviewer_path.is_file(), "diagnostic admission reviewer is missing")
    return {
        "schema": SCHEMA,
        "decision_id": DECISION_ID,
        "decision_date": DECISION_DATE,
        "state": "prospective",
        "basis": (
            "Joern 4.0.660 and the pinned Swift frontend retain exact native source/sink "
            "declarations, but call edges at the registered anchors resolve to external "
            "CPG method IDs. No edge is repaired or inferred."
        ),
        "scope": {
            "group_id": GROUP_ID,
            "population_sha256": plan["population_sha256"],
            "fixture_revision": plan["fixture_revision"],
            "control_case_count": 6,
            "control_case_arm_count": 12,
            "phase_invocation_count": 36,
            "direct_case_arm_count": 4,
            "opaque_case_ids": list(OPAQUE_CASES),
            "opaque_case_arm_count": 8,
        },
        "strict_model_qualification": {
            "status": "incomplete",
            "full_model_qualification": False,
            "failed_case_arm_count": 8,
        },
        "diagnostic_execution": {
            "status": "measurement-with-known-limits",
            "execution_eligible_if_replay_passes": True,
            "full_model_qualification": False,
            "scored_activation": False,
        },
        "direct_expected": DIRECT_EXPECTATIONS,
        "opaque_expected": {
            "raw_outcome": "inconclusive",
            "typed_state": "inconclusive",
            "diagnostics": [EXPECTED_INCOMPLETE],
            "local_source_declaration": {
                "full_name": SOURCE_LOCAL,
                "file": "main.swift",
                "line": 22,
            },
            "local_sink_declaration": {
                "full_name": SINK_LOCAL,
                "file": "main.swift",
                "line": 23,
            },
            "external_source_callee": SOURCE_EXTERNAL,
            "external_sink_callee": SINK_EXTERNAL,
            "source_call_anchor": {"file": "main.swift", "line": 26},
            "sink_call_anchor": {"file": "main.swift", "line": 27},
        },
        "resource_limits": {
            "case_arm_budget_seconds": 75,
            "total_budget_seconds": 900,
            "scratch_allowance_bytes": 4 * 1024**3,
            "protected_free_bytes": 40 * 1024**3,
        },
        "prior_control_run": prior_run,
        "prior_registration_archive": prior_archive,
        "reviewer": {
            "path": reviewer_path.relative_to(ROOT).as_posix(),
            "sha256": sha(reviewer_path),
        },
    }


def validate_control_plan_admission(root: Path, plan: dict, control: dict) -> dict:
    """Fail closed unless the dated prospective amendment is exactly registered."""
    import joern_normal_runner_v092 as runner

    root = Path(root).resolve()
    reviewer_path = root / "scripts/joern_diagnostic_admission_v092.py"
    require(reviewer_path.is_file(), "diagnostic admission reviewer is missing")
    configs = plan.get("configurations", {}).get("joern-current108", [])
    reviewer_ref = next((row for row in configs if row.get("path") == "scripts/joern_diagnostic_admission_v092.py"), None)
    require(reviewer_ref == {"path": "scripts/joern_diagnostic_admission_v092.py", "sha256": sha(reviewer_path)},
            "Joern plan does not bind the exact diagnostic admission reviewer")

    prior_run = control.get("diagnostic_admission", {}).get("prior_control_run")
    prior_archive = control.get("diagnostic_admission", {}).get("prior_registration_archive")
    prior_run_path = runner.bound_file(root, prior_run)
    prior_archive_path = runner.bound_file(root, prior_archive)
    expected = admission_descriptor(
        plan,
        reviewer_path=reviewer_path,
        prior_run=prior_run,
        prior_archive=prior_archive,
    )
    require(control.get("diagnostic_admission") == expected,
            "Joern diagnostic admission differs from the exact dated bounded decision")

    old_run = runner.read(prior_run_path)
    require(prior_run.get("path") == "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-02/run.json",
            "diagnostic admission must cite the preserved attempt02 strict control run")
    require(old_run.get("schema") == "analyzer-qualification-control-run/v092" and
            old_run.get("group_id") == GROUP_ID and
            old_run.get("identity") == plan.get("identity") and
            old_run.get("identity_components") == plan.get("identity_components") and
            old_run.get("phase_invocation_count") == 36 and
            old_run.get("assessment", {}).get("status") == "incomplete" and
            len(old_run.get("assessment", {}).get("failures", [])) == 8,
            "preserved Joern attempt02 does not prove the exact strict incomplete boundary")

    archive = runner.read(prior_archive_path)
    require(prior_archive.get("path") == "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-02-registration-archive-01/archive.json",
            "diagnostic admission must cite the preserved attempt02 registration archive")
    require(archive.get("control_plan") == {
        "path": "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-02.json",
        "sha256": runner.sha(root / "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-02.json"),
    }, "attempt02 archive no longer binds the prior control plan")
    require(any(row.get("source_path") == runner.EXECUTION_PLAN_PATH and
                row.get("archive_sha256") == archive.get("execution_plan_sha256")
                for row in archive.get("files", [])),
            "attempt02 archive does not preserve its exact executable plan")
    return expected


def _unique_method(methods: dict[str, dict], full_name: str, *, external: bool) -> dict:
    rows = [row for row in methods.values()
            if row.get("full_name") == full_name and row.get("external") is external]
    require(len(rows) == 1, "CPG declaration identity missing or ambiguous: " + full_name)
    return rows[0]


def _validate_wrapper_evidence(graph: dict, config: dict, methods: dict[str, dict]) -> list[dict]:
    wrappers = config.get("wrappers")
    evidence = graph.get("wrapper_evidence")
    require(isinstance(wrappers, list) and len(wrappers) == 3 and isinstance(evidence, list) and len(evidence) == 3,
            "all three registered opaque wrapper proofs are required")
    evidence_by_id = {row.get("method_id"): row for row in evidence if isinstance(row, dict)}
    require(len(evidence_by_id) == 3, "opaque wrapper proof identities are duplicated or malformed")
    proof_rows = []
    selected_calls = []
    sink_anchors = config.get("sink_anchors")
    require(isinstance(sink_anchors, list) and len(sink_anchors) == 1, "one exact sink call anchor is required")
    sink_anchor = sink_anchors[0]

    for spec in wrappers:
        full_name = spec.get("method")
        owner_name = spec.get("owner")
        expected_indices = spec.get("parameter_indices")
        method = _unique_method(methods, full_name, external=False)
        require(method.get("node", {}).get("label") == "METHOD" and
                method.get("node", {}).get("file") == "main.swift",
                "opaque wrapper is not a local Swift declaration")
        parameters = method.get("parameters")
        require(isinstance(parameters, list) and
                sorted(parameter.get("index") for parameter in parameters) == expected_indices,
                "opaque wrapper parameter identities differ from the registered model")
        require(all(parameter.get("type") == (owner_name if parameter["index"] == 0 else "Swift.String")
                    for parameter in parameters),
                "opaque wrapper parameter types differ from the registered model")
        proof = evidence_by_id.get(method.get("id"))
        require(proof is not None and proof.get("owner_id") and proof.get("owner_full_name") == owner_name and
                method.get("id") in proof.get("owner_ast_method_ids", []) and
                proof.get("return_types") == ["Swift.String"],
                "opaque wrapper owner/AST/return proof is missing or inconsistent")
        proof_row = {"method_id": method["id"], "full_name": full_name,
                     "owner_id": proof["owner_id"], "owner_full_name": owner_name,
                     "parameter_indices": expected_indices}

        if full_name == config.get("selected_wrapper"):
            selected_calls = [call for call in graph.get("calls", [])
                              if call.get("method_full_name") == full_name and
                              call.get("callee_ids") == [method.get("id")] and
                              call.get("node", {}).get("file") == sink_anchor.get("file") and
                              call.get("node", {}).get("line") == sink_anchor.get("line_hint")]
            require(len(selected_calls) == 1, "selected wrapper has no unique local call edge at the exact sink anchor")
            selected_call = selected_calls[0]
            selected_arguments = selected_call.get("arguments")
            require(isinstance(selected_arguments, list) and
                    sorted(argument.get("index") for argument in selected_arguments) == expected_indices and
                    len({argument.get("index") for argument in selected_arguments}) == len(selected_arguments) and
                    all(isinstance(argument.get("node"), dict) and
                        isinstance(argument["node"].get("id"), str) and argument["node"]["id"]
                        for argument in selected_arguments),
                    "selected wrapper call argument identities differ from the registered model")
            selected_node = selected_call.get("node")
            require(isinstance(selected_node, dict) and isinstance(selected_node.get("id"), str) and
                    selected_node.get("label") == "CALL" and
                    selected_node.get("file") == sink_anchor.get("file") and
                    selected_node.get("line") == sink_anchor.get("line_hint"),
                    "selected wrapper call node is not anchored at the registered sink argument")
            sink_calls = [call for call in graph.get("calls", [])
                          if call.get("method_full_name") == SINK_EXTERNAL and
                          call.get("node", {}).get("file") == sink_anchor.get("file") and
                          call.get("node", {}).get("line") == sink_anchor.get("line_hint")]
            require(len(sink_calls) == 1,
                    "registered sink call has no unique node at the selected wrapper anchor")
            sink_arguments = sink_calls[0].get("arguments")
            require(isinstance(sink_arguments, list) and
                    sorted(argument.get("index") for argument in sink_arguments) == [0, 1] and
                    len({argument.get("index") for argument in sink_arguments}) == len(sink_arguments),
                    "registered sink call argument identities differ from its native declaration")
            sink_value = next(argument for argument in sink_arguments if argument.get("index") == 1)
            sink_value_node = sink_value.get("node")
            require(isinstance(sink_value_node, dict) and
                    sink_value_node.get("id") == selected_node.get("id") and
                    sink_value_node.get("label") == "CALL" and
                    sink_value_node.get("file") == sink_anchor.get("file") and
                    sink_value_node.get("line") == sink_anchor.get("line_hint"),
                    "sink argument 1 is not the exact selected wrapper call node")
            proof_row["selected_call_node_id"] = selected_node["id"]
            proof_row["sink_argument_index"] = 1
            proof_row["sink_argument_node_id"] = sink_value_node["id"]

        proof_rows.append(proof_row)

    require(len(selected_calls) == 1, "registered selected wrapper is not among the reviewed wrappers")
    return proof_rows


def validate_opaque_endpoint_gap(graph: dict, config: dict, raw: dict, *, plan: dict,
                                 cpg_path: Path, case_id: str, arm: str) -> dict:
    """Prove exact declarations exist while registered call edges target EXTERNAL IDs."""
    require(case_id in OPAQUE_CASES and arm in ("off", "on"), "opaque endpoint gap is outside the admitted scope")
    require(cpg_path.is_file() and not cpg_path.is_symlink() and cpg_path.stat().st_size > 0,
            "digest-bound native CPG binary is missing or empty")
    require(raw.get("case_id") == case_id and raw.get("control") == case_id and raw.get("arm") == arm,
            "opaque raw row routing differs from the exact admitted case-arm")
    require(raw.get("identity") == plan.get("identity") and
            raw.get("identity_components") == plan.get("identity_components"),
            "opaque CPG evidence has the wrong pinned Joern/frontend identity")
    require(raw.get("raw_outcome") == "inconclusive" and raw.get("state") == "inconclusive" and
            raw.get("diagnostics") == [EXPECTED_INCOMPLETE],
            "opaque control did not preserve the exact EndpointIdentity incomplete state")
    require(graph.get("state") == "analyzed" and graph.get("query_completed") is True and
            graph.get("frontend") == "SWIFTSRC",
            "opaque CPG export is not a completed Swift frontend graph")
    require(graph.get("analysis_completeness") == ANALYSIS_COMPLETENESS,
            "opaque CPG changed the existing bounded-analysis uncertainty state")
    require(graph.get("source_observations") == [] and graph.get("sink_observations") == [] and
            graph.get("source_nodes") == [] and graph.get("sink_nodes") == [] and graph.get("flows") == [],
            "opaque EndpointIdentity gap was flattened into endpoint or flow evidence")

    required_identities = config.get("source_methods"), config.get("sink_methods")
    require(required_identities == ([SOURCE_LOCAL], [SINK_LOCAL]),
            "opaque control no longer binds the exact source and sink declaration identities")
    anchors = config.get("source_anchors"), config.get("sink_anchors")
    require(len(anchors[0]) == 1 and len(anchors[1]) == 1 and
            {"file": anchors[0][0].get("file"), "line": anchors[0][0].get("line_hint")} == {"file": "main.swift", "line": 26} and
            {"file": anchors[1][0].get("file"), "line": anchors[1][0].get("line_hint")} == {"file": "main.swift", "line": 27},
            "opaque endpoint anchor differs from the registered source/sink callsites")

    method_rows = graph.get("methods")
    require(isinstance(method_rows, list), "opaque graph has no native method inventory")
    methods = {row.get("id"): row for row in method_rows if isinstance(row, dict)}
    require(len(methods) == len(method_rows) and all(isinstance(key, str) and key for key in methods),
            "opaque graph method IDs are missing or duplicated")
    source = _unique_method(methods, SOURCE_LOCAL, external=False)
    sink = _unique_method(methods, SINK_LOCAL, external=False)
    require(source.get("node", {}).get("label") == "METHOD" and
            source.get("node", {}).get("file") == "main.swift" and source.get("node", {}).get("line") == 22 and
            source.get("parameters") == [],
            "native source declaration differs from the exact reviewed CPG identity")
    require(sink.get("node", {}).get("label") == "METHOD" and
            sink.get("node", {}).get("file") == "main.swift" and sink.get("node", {}).get("line") == 23 and
            [(row.get("index"), row.get("type")) for row in sink.get("parameters", [])] == [(1, "Swift.String")],
            "native sink declaration differs from the exact reviewed CPG identity")
    require(graph.get("source_method_ids") == [source["id"]] and graph.get("sink_method_ids") == [sink["id"]],
            "graph resolver method IDs do not bind the exact local endpoint declarations")

    calls = graph.get("calls")
    require(isinstance(calls, list), "opaque graph has no call inventory")
    expected = (
        ("source", anchors[0][0], SOURCE_EXTERNAL, source),
        ("sink", anchors[1][0], SINK_EXTERNAL, sink),
    )
    edge_proofs = []
    for role, anchor, external_name, local_method in expected:
        rows = [call for call in calls if call.get("node", {}).get("file") == anchor.get("file") and
                call.get("node", {}).get("line") == anchor.get("line_hint") and
                call.get("method_full_name") == external_name]
        require(len(rows) == 1, f"{role} call edge at the exact fixture anchor is missing or ambiguous")
        call = rows[0]
        callees = call.get("callee_ids")
        require(isinstance(callees, list) and len(callees) == 1 and callees[0] != local_method.get("id"),
                f"{role} call edge is not a single distinct callee identity")
        external_method = methods.get(callees[0])
        require(external_method is not None and external_method.get("external") is True and
                external_method.get("full_name") == external_name and
                external_method.get("node", {}).get("file") == "builtintypes" and
                external_method.get("node", {}).get("line") == -1,
                f"{role} call edge no longer resolves to the recorded EXTERNAL CPG identity")
        require(local_method.get("external") is False and local_method.get("id") != external_method.get("id"),
                f"{role} local native declaration was aliased to the external call target")
        edge_proofs.append({
            "role": role,
            "anchor": {"file": anchor["file"], "line": anchor["line_hint"]},
            "local_declaration_id": local_method["id"],
            "local_declaration_full_name": local_method["full_name"],
            "call_node_id": call.get("node", {}).get("id"),
            "call_method_full_name": call.get("method_full_name"),
            "callee_id": external_method["id"],
            "callee_external": True,
            "callee_full_name": external_method["full_name"],
        })

    wrapper_proofs = _validate_wrapper_evidence(graph, config, methods)
    return {
        "case_id": case_id,
        "arm": arm,
        "raw_outcome": raw["raw_outcome"],
        "typed_state": raw["state"],
        "diagnostics": raw["diagnostics"],
        "cpg_size_bytes": cpg_path.stat().st_size,
        "endpoint_edges": edge_proofs,
        "wrapper_declarations": wrapper_proofs,
        "source_observations": 0,
        "sink_observations": 0,
        "flows": 0,
        "analysis_completeness": graph["analysis_completeness"],
    }


def replay_admission(root: Path, plan: dict, control: dict, run: dict,
                     observations: dict, cases: dict[str, dict],
                     case_paths: dict[str, Path]) -> dict:
    """Validate a completed control run without changing strict control results."""
    import joern_normal_runner_v092 as runner

    root = Path(root).resolve()
    descriptor = validate_control_plan_admission(root, plan, control)
    require(run.get("scored_activation") is False, "strict Joern control run claims scored activation")
    engine = runner._engine(root)
    runner._set_engine_query_root(engine, plan["query_root"])
    assessment = engine.assess_controls(observations)
    require(assessment.get("status") == "incomplete" and
            assessment.get("scored_activation") is False and
            assessment.get("partition_registered") is False and
            assessment.get("absence_completeness") == "unproven" and
            run.get("assessment") == assessment,
            "strict Joern control assessment is not the exact preserved incomplete result")

    for control_name, expected_arms in DIRECT_EXPECTATIONS.items():
        require(observations.get(control_name) == expected_arms,
                "direct positive/negative control arms did not strictly pass")
    expected_failure_rows = {
        (case_id, arm, "inconclusive")
        for case_id in OPAQUE_CASES for arm in ("off", "on")
    }
    actual_failure_rows = {
        (row.get("control"), row.get("arm"), row.get("observed"))
        for row in assessment.get("failures", [])
    }
    require(actual_failure_rows == expected_failure_rows and len(assessment.get("failures", [])) == 8,
            "strict assessment has a timeout, unknown incomplete state, or failure outside the eight admitted opaque arms")

    records = {(row.get("control"), row.get("arm")): row for row in run.get("records", [])}
    require(len(records) == 12, "diagnostic admission requires all twelve exact control arms")
    proofs = []
    for case_id in OPAQUE_CASES:
        for arm in ("off", "on"):
            record = records.get((case_id, arm))
            require(record is not None, "diagnostic admission omitted an opaque model arm")
            raw_path = runner.bound_file(root, record.get("raw"))
            raw = runner.read(raw_path)
            native_by_name: dict[str, Path] = {}
            for reference in raw.get("native_outputs", []):
                path = runner.bound_file(root, reference)
                require(path.parent == raw_path.parent and path.name not in native_by_name,
                        "opaque native CPG output escaped or duplicated its control arm")
                native_by_name[path.name] = path
            require({"graph.json", "config.json", "cpg.bin"} <= set(native_by_name),
                    "opaque arm lacks its graph, reviewed model config, or native CPG binary")
            case_path = Path(case_paths[case_id])
            expected_config = _expected_control_config_from_capture_root(
                runner, raw, engine, cases[case_id], arm, control
            )
            config = runner.read(native_by_name["config.json"])
            require(config == expected_config,
                    "opaque control model configuration differs from exact registered endpoint/wrapper identities")
            graph = runner.read(native_by_name["graph.json"])
            proof = validate_opaque_endpoint_gap(
                graph, config, raw, plan=plan, cpg_path=native_by_name["cpg.bin"],
                case_id=case_id, arm=arm,
            )
            proof["raw"] = record["raw"]
            proof["graph"] = runner.reference(root, native_by_name["graph.json"])
            proof["cpg"] = runner.reference(root, native_by_name["cpg.bin"])
            proofs.append(proof)

    require(len(proofs) == 8, "diagnostic admission must independently replay all eight opaque CPGs")
    return {
        "schema": REVIEW_SCHEMA,
        "decision_id": descriptor["decision_id"],
        "decision_date": descriptor["decision_date"],
        "execution_plan_projection_sha256": plan["qualification_control_projection_sha256"],
        "status": "measurement-with-known-limits",
        "diagnostic_execution_eligible": True,
        "full_model_qualification": False,
        "strict_model_qualification": False,
        "scored_activation": False,
        "strict_assessment": assessment,
        "direct_case_arm_count": 4,
        "opaque_case_arm_count": len(proofs),
        "endpoint_identity_proofs": proofs,
        "limits": [
            "Joern 4.0.660 exposes local native endpoint declarations but binds their anchored calls to EXTERNAL method IDs.",
            "The eight opaque model arms remain Incomplete:EndpointIdentity and are not model-qualified.",
            "No source/sink aliases, approximate edges, scored activation, or denominator changes are admitted.",
            "Analysis absence remains unproven under the registered bounded analysis settings.",
        ],
    }


def _expected_control_config_from_capture_root(runner, raw: dict, engine,
                                               case: dict, arm: str, control: dict) -> dict:
    """Rebuild model configuration from the root recorded with the raw capture."""
    capture_root_text = raw.get("capture_root")
    require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute(),
            "opaque raw control has no absolute recorded capture root")
    return runner._control_config(engine, Path(capture_root_text).resolve(), case, arm, control)


def review_attempt(root: Path, plan_path: str, run_path: Path, output_path: Path) -> dict:
    """Replay the prospective control attempt and write one append-only review."""
    import joern_normal_runner_v092 as runner
    import swift_common_population_v2 as common

    root = Path(root).resolve()
    run_path = run_path.resolve()
    output_path = output_path.resolve()
    runner.require(not output_path.exists() and not output_path.is_symlink(),
                   "diagnostic admission review output already exists")
    plan, _evidence, context = runner.validate_plan(root, plan_path, allow_qualification_pending=True)
    require(run_path.is_file() and run_path.resolve().is_relative_to(root),
            "diagnostic admission control run must be inside the current repository root")
    control = context["control"]
    run = runner.read(run_path)
    require(run.get("control_plan_sha256") == plan["qualification_control_plan"]["sha256"] and
            run.get("execution_plan_projection_sha256") == plan["qualification_control_projection_sha256"],
            "diagnostic admission run does not bind the current prospective control plan")
    _population, common_rows, _swift_rows, cases, _digest = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in common_rows}
    engine = context["engine"]
    runner._set_engine_query_root(engine, plan["query_root"])
    observations, phase_count = runner._replay_control_run(
        root, plan, control, run, cases, engine, case_paths=case_paths
    )
    require(phase_count == 36, "diagnostic admission requires 36 successful, replayed phase invocations")
    report = replay_admission(root, plan, control, run, observations, cases, case_paths)
    report["control_run"] = runner.reference(root, run_path)
    report["reviewer"] = _ref(Path(__file__), root)
    report["control_plan"] = plan["qualification_control_plan"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def validate_receipt_review(root: Path, plan: dict, control: dict, evidence: dict,
                            run: dict, observations: dict, cases: dict[str, dict],
                            case_paths: dict[str, Path]) -> dict:
    """Replay and compare the exact review bound by a prospective receipt."""
    import joern_normal_runner_v092 as runner

    root = Path(root).resolve()
    ref = evidence.get("diagnostic_admission_review")
    review_path = runner.bound_file(root, ref)
    review = runner.read(review_path)
    expected = replay_admission(root, plan, control, run, observations, cases, case_paths)
    expected["control_run"] = runner.reference(root, runner.bound_file(root, evidence["control_run"]))
    expected["reviewer"] = {
        "path": "scripts/joern_diagnostic_admission_v092.py",
        "sha256": sha(root / "scripts/joern_diagnostic_admission_v092.py"),
    }
    expected["control_plan"] = plan["qualification_control_plan"]
    require(review == expected, "diagnostic admission review differs from independently replayed controls and CPG evidence")
    require(evidence.get("status") == "measurement-with-known-limits" and
            evidence.get("execution_eligible") is True and
            evidence.get("diagnostic_execution_eligible") is True and
            evidence.get("full_model_qualification") is False and
            evidence.get("scored_activation") is False,
            "qualification receipt flattened or overstated the diagnostic admission state")
    dimensions = evidence.get("dimensions")
    require(isinstance(dimensions, dict) and dimensions.get("joern_diagnostic_admission") == ref,
            "qualification receipt dimensions do not bind the diagnostic review artifact")
    return review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = review_attempt(ROOT, args.plan, args.run, args.output)
    print(json.dumps({
        "status": result["status"],
        "diagnostic_execution_eligible": result["diagnostic_execution_eligible"],
        "full_model_qualification": result["full_model_qualification"],
        "scored_activation": result["scored_activation"],
        "opaque_case_arm_count": result["opaque_case_arm_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
