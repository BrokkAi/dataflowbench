#!/usr/bin/env python3
"""Capture fresh, bounded CodeQL Swift structural and model controls for v0.9.2.

This entry point is separate from the scored common-108 runner. It creates one
new attempt tree and leaves partial command/database evidence in place on
failure. A successful bundle is replayed from the retained CodeQL tables before
an execution-eligible receipt is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import time

import codeql_swift_qualification_v092 as replay
import swift_common_population_v2 as common
import swift_v2_process as process
import swift_normal_runner_v092 as runner
import v092_qualification as qualification
from swift_extraction_integrity import inspect_logs


ENTRY_QUERY_ROLES = ("entry", "diagnostics", "kernel-flow")
ANALYSIS_PHASES = {
    "entry": replay.ENTRY_PHASES,
    "activation": replay.ACTIVATION_PHASES,
}
MINIMUM_FREE_BYTES = 40 * 1024**3


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def ref(root: Path, path: Path) -> dict:
    resolved = path.resolve()
    require(resolved.is_file() and resolved.is_relative_to(root.resolve()), "evidence escaped repository root")
    return {"path": resolved.relative_to(root.resolve()).as_posix(), "sha256": sha(resolved)}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "expected JSON object: " + str(path))
    return value


def _check_capacity(root: Path, output: Path, scratch_limit: int) -> None:
    require(shutil.disk_usage(root).free >= MINIMUM_FREE_BYTES + scratch_limit,
            "qualification capacity gate requires 40 GiB reserve plus 4 GiB scratch")
    retained = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    require(retained <= scratch_limit, "CodeQL control capture exceeded its declared scratch allowance")


def _run_phase(root: Path, directory: Path, phase: str, role: str, argv: list[str], deadline: float) -> dict:
    require(deadline > 0, "qualification total or phase budget exhausted")
    record = process.run(argv, directory, phase, deadline, cwd=root)
    record.update(phase_id=phase, role=role)
    write(directory / (phase + ".command.json"), record)
    require(record.get("cleanup_status") == "tracked-processes-stopped", "uncertain CodeQL process cleanup")
    require(record.get("exit_status") == 0 and record.get("timed_out") is False,
            "CodeQL qualification phase failed: " + phase)
    return record


def _partial_command_refs(root: Path, directory: Path) -> list[dict]:
    return [ref(root, path) for path in sorted(directory.glob("*.command.json"))]


def _partial_query_refs(root: Path, directory: Path, roles: tuple[str, ...]) -> dict:
    return {role: ref(root, path) for role in roles
            if (path := directory / (role + ".json")).is_file()}


def _run_queries(root: Path, plan: dict, output: Path, source: Path,
                 canonical: Path, fixture_files: list[str], query_paths: dict[str, Path],
                 *, entry: bool, total_deadline: float,
                 scratch_limit: int, capture_root: Path) -> dict:
    runtime = plan["runtime"]
    cli = runtime["codeql"]
    database = (output / "database").resolve()
    source_dir = source.resolve()
    compiler_argv = [runtime["compiler"], "-swift-version", "6", "-Onone", "-sdk", runtime["sdk"],
                     "-target", runtime.get("swift_target", "arm64-apple-macosx26.5"),
                     "-module-name", "DataFlowBenchTaintSwift",
                     "-module-cache-path", str((output / "cache").resolve()),
                     *[str((source_dir / name).resolve()) for name in fixture_files],
                     "-o", str((output / "never-executed").resolve())]
    commands = []
    analysis_deadline = None

    def phase(phase_id: str, role: str, argv: list[str], phase_limit: float) -> None:
        _check_capacity(root, capture_root, scratch_limit)
        remaining_total = total_deadline - time.monotonic()
        remaining_analysis = analysis_deadline - time.monotonic() if role == "analysis" else phase_limit
        limit = min(phase_limit, remaining_total, remaining_analysis)
        record = _run_phase(root, output, phase_id, role, argv, limit)
        commands.append(ref(root, output / (phase_id + ".command.json")))
        if role == "analysis":
            require(time.monotonic() <= analysis_deadline, "CodeQL control exceeded its shared 75-second analysis budget")

    create_argv = [cli, "database", "create", str(database), "--language=swift",
                   "--search-path=" + runtime["extractor_root"], "--source-root=" + str(source_dir),
                   "--threads=2", "--ram=2048", "--command=" + shlex.join(compiler_argv)]
    phase("database-create", "extraction", create_argv, 150)

    analysis_start = time.monotonic()
    analysis_deadline = min(analysis_start + 75, total_deadline)
    phase("resolve-database", "analysis", [cli, "resolve", "database", "--format=json", str(database)], 75)

    # Revalidate that the database is finalized, owns only the fresh control
    # fixture, uses the pinned schema, and has a complete extractor log.
    if entry:
        case = {"fixture_files": fixture_files}
    else:
        case = read_json(canonical / "case.json")
    from swift_normal_runner_v1 import validate_database
    validate_database(database, source_dir, canonical, case,
                      read_json(output / "resolve-database.stdout"),
                      plan["runtime"]["pins"]["schema_sha256"])
    integrity = inspect_logs(database / "log/swift/extractor")
    write(output / "extraction-integrity.json", integrity)
    require(integrity.get("ready_for_observation") is True, "CodeQL Swift extraction is incomplete")

    roles = list(query_paths)
    if entry:
        roles = list(ENTRY_QUERY_ROLES)
    else:
        roles = ["flow"]
    for role in roles:
        query = str(query_paths[role].resolve())
        bqrs = str((output / (role + ".bqrs")).resolve())
        query_id = role + "-query"
        phase(query_id, "analysis", [cli, "query", "run", query, "--database=" + str(database),
                                      "--output=" + bqrs, "--additional-packs=" + runtime["packs"],
                                      "--threads=2", "--ram=2048"], 75)
        phase(role + "-decode", "analysis", [cli, "bqrs", "decode", bqrs, "--format=json",
                                               "--output=" + str((output / (role + ".json")).resolve())], 75)
    require(time.monotonic() - analysis_start <= 75, "CodeQL control exceeded its shared 75-second analysis budget")

    outputs = {}
    for role in roles:
        decoded = output / (role + ".json")
        table = read_json(decoded)
        require(isinstance(table.get("#select"), dict) and isinstance(table["#select"].get("tuples"), list),
                "CodeQL failed to retain native #select.tuples for " + role)
        outputs[role] = {"reference": ref(root, decoded), "rows": table["#select"]["tuples"]}
    return {"commands": commands, "query_outputs": outputs}


def _capture_entry(root: Path, plan: dict, control: dict, control_id: str,
                   output: Path, total_deadline: float, scratch_limit: int) -> dict:
    fixture = root / control["entry_extractor"]["controls"][control_id]
    directory = output / "entry" / control_id
    directory.mkdir(parents=True, exist_ok=False)
    source = directory / "source"
    source.mkdir()
    shutil.copyfile(fixture, source / "main.swift")
    query_paths = {role: replay.bound_file(root, ref_value, "CodeQL entry query")
                   for role, ref_value in control["entry_extractor"]["queries"].items()}
    try:
        captured = _run_queries(root, plan, directory, source, fixture.parent, ["main.swift"], query_paths,
                                entry=True, total_deadline=total_deadline,
                                scratch_limit=scratch_limit, capture_root=output)
    except Exception as error:
        partial = {"schema": "codeql-entry-control-raw/v092", "group_id": replay.GROUP_ID,
                   "control_id": control_id,
                   "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
                   "identity": plan["identity"], "identity_components": plan["identity_components"],
                   "capture_root": str(root.resolve()), "capture_output_dir": str(directory.resolve()),
                   "fixture_sha256": sha(fixture),
                   "source_files": {"main.swift": replay.reference_for(root, fixture)},
                   "commands": _partial_command_refs(root, directory),
                   "query_outputs": _partial_query_refs(root, directory, ENTRY_QUERY_ROLES),
                   "capture_state": "incomplete", "failure": {"type": type(error).__name__, "message": str(error)}}
        write(directory / "raw.json", partial)
        raise
    rows = {role: value["rows"] for role, value in captured["query_outputs"].items()}
    observation = replay.swift_entry_observation.classify(rows["entry"], rows["diagnostics"], rows["kernel-flow"])
    raw = {
        "schema": "codeql-entry-control-raw/v092",
        "group_id": replay.GROUP_ID,
        "control_id": control_id,
        "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
        "identity": plan["identity"],
        "identity_components": plan["identity_components"],
        "capture_root": str(root.resolve()),
        "capture_output_dir": str(directory.resolve()),
        "fixture_sha256": sha(fixture),
        "source_files": {"main.swift": replay.reference_for(root, fixture)},
        "commands": captured["commands"],
        "query_outputs": {role: value["reference"] for role, value in captured["query_outputs"].items()},
        "entry_rows": rows["entry"],
        "exact_endpoint_rows": rows["diagnostics"],
        "flow_rows": rows["kernel-flow"],
        "observation": observation,
        "capture_state": "complete",
    }
    raw_path = directory / "raw.json"
    write(raw_path, raw)
    return {"control_id": control_id, "raw": ref(root, raw_path), "observed": observation}


def _capture_activation(root: Path, plan: dict, control: dict, dimension: str,
                        case_id: str, arm: str, case: dict, case_path: Path,
                        output: Path, total_deadline: float, scratch_limit: int) -> dict:
    directory = output / dimension / case_id / arm
    directory.mkdir(parents=True, exist_ok=False)
    source = directory / "source"
    source.mkdir()
    for name in case["fixture_files"]:
        shutil.copyfile(case_path.parent / name, source / name)
    query = replay.bound_file(root, control["activation_queries"][dimension][arm], "CodeQL activation query")
    try:
        captured = _run_queries(root, plan, directory, source, case_path.parent, case["fixture_files"],
                                {"flow": query}, entry=False,
                                total_deadline=total_deadline, scratch_limit=scratch_limit,
                                capture_root=output)
    except Exception as error:
        partial = {"schema": "codeql-activation-control-raw/v092", "group_id": replay.GROUP_ID,
                   "dimension": dimension, "case_id": case_id, "arm": arm,
                   "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
                   "identity": plan["identity"], "identity_components": plan["identity_components"],
                   "capture_root": str(root.resolve()), "capture_output_dir": str(directory.resolve()),
                   "fixture_hashes": replay._fixture_hashes(root, case),
                   "commands": _partial_command_refs(root, directory),
                   "query_outputs": _partial_query_refs(root, directory, ("flow",)),
                   "capture_state": "incomplete", "failure": {"type": type(error).__name__, "message": str(error)}}
        write(directory / "raw.json", partial)
        raise
    rows = captured["query_outputs"]["flow"]["rows"]
    observed = replay._activation_observation(root, case, arm, rows)
    raw_path = directory / "raw.json"
    raw = {
        "schema": "codeql-activation-control-raw/v092",
        "group_id": replay.GROUP_ID,
        "dimension": dimension,
        "case_id": case_id,
        "arm": arm,
        "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
        "identity": plan["identity"],
        "identity_components": plan["identity_components"],
        "capture_root": str(root.resolve()),
        "capture_output_dir": str(directory.resolve()),
        "fixture_hashes": replay._fixture_hashes(root, case),
        "commands": captured["commands"],
        "query_outputs": {"flow": captured["query_outputs"]["flow"]["reference"]},
        "flow_rows": rows,
        "observed": observed,
        "capture_state": "complete",
    }
    write(raw_path, raw)
    return {"case_id": case_id, "arm": arm, "raw": ref(root, raw_path), "observed": observed}


def capture(root: Path, plan_path: str, control_plan_ref: dict,
            query_receipt_ref: dict, output: Path) -> dict:
    root = root.resolve()
    plan, _empty, _ = runner.validate_plan(root, plan_path, allow_qualification_pending=True)
    require(os.environ.get("DATAFLOWBENCH_V092_QUALIFICATION") == "1" and
            os.environ.get("DATAFLOWBENCH_V092_GROUP_ID") == replay.GROUP_ID,
            "CodeQL Swift controls require the guarded, group-scoped qualification workflow")
    control_path = qualification.bound_repository_file(root, control_plan_ref, "CodeQL control plan")
    control = replay.read_json(control_path, "CodeQL control plan")
    replay._validate_control_plan(root, plan, control)
    require(plan.get("qualification_control_plan") == control_plan_ref,
            "selected control plan differs from the executable plan binding")
    query_path = qualification.bound_repository_file(root, query_receipt_ref, "CodeQL query resolution receipt")
    query_receipt = qualification.read_json(query_path, "CodeQL query resolution receipt")[0]
    runner.verify_query_receipt(root, plan, query_receipt, plan_path)

    output = output.resolve()
    require(output.is_relative_to(root / "reports/releases/v0.9.2/qualification"),
            "CodeQL Swift control output must remain in the v0.9.2 qualification evidence root")
    require(not output.exists() and not output.is_symlink(), "CodeQL qualification attempts are append-only and never overwritten")
    scratch_limit = control["scratch_allowance_bytes"]
    _check_capacity(root, output.parent if output.parent.exists() else root, scratch_limit)
    output.mkdir(parents=True)

    started = time.monotonic()
    total_deadline = started + control["total_budget_seconds"]
    # Capture and retain a fresh version/build witness before controls.
    identity_dir = output / "identity"
    identity_dir.mkdir()
    runtime = plan["runtime"]
    version = process.run([runtime["codeql"], "version", "--format=json"], identity_dir,
                          "version", 30, cwd=root)
    banner_path = identity_dir / "version.stdout"
    require(version.get("exit_status") == 0 and not version.get("timed_out") and
            version.get("cleanup_status") == "tracked-processes-stopped", "CodeQL runtime identity command failed")
    banner = read_json(banner_path)
    require(banner.get("productName") == "CodeQL" and banner.get("version") == plan["identity"]["tool_version"] and
            banner.get("sha") == runtime["pins"]["cli_build"], "CodeQL runtime identity differs from the exact selected CLI")
    identity_witness = identity_dir / "identity.json"
    write(identity_witness, {"observed": plan["identity"], "capture_root": str(root.resolve()),
                             "command": ref(root, identity_dir / "version.command.json"),
                             "stdout": ref(root, banner_path), "observed_at_unix_seconds": int(time.time())})

    entries = []
    model_records = []
    sanitizer_records = []
    common_population, population_rows, _swift_rows, cases, population_sha = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in population_rows}
    case_path_strings = {row["id"]: row["path"] for row in population_rows}
    for case_id, case in cases.items():
        case["path"] = case_path_strings[case_id]
    index = {"schema": "codeql-swift-control-capture-index/v092", "status": "capturing",
             "plan": {"path": plan_path, "sha256": sha(root / plan_path)},
             "control_plan": control_plan_ref, "query_receipt": query_receipt_ref,
             "started_at_unix_seconds": int(time.time()), "partial": {}}
    write(output / "capture-index.json", index)

    try:
        for control_id in replay.ENTRY_IDS:
            _check_capacity(root, output, scratch_limit)
            entries.append(_capture_entry(root, plan, control, control_id, output, total_deadline, scratch_limit))
            index["partial"]["entry_extractor"] = len(entries)
            write(output / "capture-index.json", index)

        for dimension, cases_expected, destination in (
            ("model_activation", replay.MODEL_EXPECTED, model_records),
            ("sanitizer_activation", replay.SANITIZER_EXPECTED, sanitizer_records),
        ):
            for case_id in cases_expected:
                case = cases[case_id]
                for arm in ("off", "on"):
                    _check_capacity(root, output, scratch_limit)
                    destination.append(_capture_activation(root, plan, control, dimension, case_id, arm,
                                                          case, case_paths[case_id], output, total_deadline,
                                                          scratch_limit))
                    index["partial"][dimension] = len(destination)
                    write(output / "capture-index.json", index)

        entry_assessment = {
            "status": "measurement-with-known-limits" if any(row["observed"].get("diagnostic") != replay.ENTRY_EXPECTED[row["control_id"]] for row in entries) else "qualified",
            "execution_eligible": True,
            "strict_qualified": False,
            "case_count": 10,
            "observations": {row["control_id"]: row["observed"].get("diagnostic") for row in entries},
            "known_limit_deltas": {},
            "scored_activation": False,
        }
        deltas = {control_id: {"expected": expected, "observed": entry_assessment["observations"][control_id]}
                  for control_id, expected in replay.ENTRY_EXPECTED.items()
                  if entry_assessment["observations"][control_id] != expected}
        entry_assessment["known_limit_deltas"] = deltas
        entry_assessment["strict_qualified"] = not bool(deltas)
        entry_assessment["status"] = "measurement-with-known-limits" if deltas else "qualified"
        entry_evidence_path = output / "entry-extractor-evidence.json"
        entry_evidence = {"schema": "codeql-entry-extractor-evidence/v092", "group_id": replay.GROUP_ID,
                          "identity": plan["identity"], "identity_components": plan["identity_components"],
                          "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
                          "controls": entries, "assessment": entry_assessment}
        write(entry_evidence_path, entry_evidence)

        dimension_refs = {}
        activation_assessments = {}
        for dimension, records, case_expectations in (
            ("model_activation", model_records, replay.MODEL_EXPECTED),
            ("sanitizer_activation", sanitizer_records, replay.SANITIZER_EXPECTED),
        ):
            provisional_assessment = {
                "status": "qualified", "execution_eligible": True, "strict_qualified": True,
                "case_count": len(case_expectations), "case_arm_count": len(case_expectations) * 2,
                "observations": {}, "scored_activation": False, "partition_registered": False,
            }
            for row in records:
                provisional_assessment["observations"].setdefault(row["case_id"], {})[row["arm"]] = row["observed"]
            evidence_path = output / (dimension.replace("_", "-") + "-evidence.json")
            evidence = {"schema": "codeql-activation-evidence/v092", "dimension": dimension,
                        "group_id": replay.GROUP_ID, "identity": plan["identity"],
                        "identity_components": plan["identity_components"],
                        "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
                        "controls": records, "assessment": provisional_assessment}
            write(evidence_path, evidence)
            dimension_refs[dimension] = ref(root, evidence_path)

        dimension_refs["entry_extractor"] = ref(root, entry_evidence_path)
        dimension_refs["query_resolution_compile"] = ref(root, query_path)
        control_run = {
            "schema": "analyzer-qualification-control-run/v092", "group_id": replay.GROUP_ID,
            "identity": plan["identity"], "identity_components": plan["identity_components"],
            "control_plan_sha256": control_plan_ref["sha256"],
            "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
            "identity_witness": ref(root, identity_witness), "dimensions": dimension_refs,
            "elapsed_seconds": time.monotonic() - started,
        }
        control_run["assessment"] = replay.replay_control_run(root, plan, control, control_run, {
            "entry_extractor": {"evidence": dimension_refs["entry_extractor"]},
            "model_activation": {"evidence": dimension_refs["model_activation"]},
            "sanitizer_activation": {"evidence": dimension_refs["sanitizer_activation"]},
        })
        control_run_path = output / "control-run.json"
        write(control_run_path, control_run)
        control_run_ref = ref(root, control_run_path)

        # The query-resolution/compile dimension remains a separately replayed
        # prerequisite. Its digest and completeness are bound into this receipt.
        query_count = len(query_receipt.get("queries", {}))
        require(query_count > 0 and query_receipt.get("status") == "checked-only", "query-resolution receipt is incomplete")
        entry_replayed = control_run["assessment"]["entry_extractor"]
        dimensions = {
            "entry_extractor": {"status": entry_replayed["status"], "execution_eligible": True,
                                "control_ids": list(replay.ENTRY_IDS), "case_count": 10,
                                "assessment": entry_replayed, "evidence": dimension_refs["entry_extractor"]},
            "query_resolution_compile": {"status": "qualified", "query_count": query_count,
                                          "receipt": query_receipt_ref},
            "model_activation": {"status": "qualified", "execution_eligible": True,
                                 "assessment": control_run["assessment"]["model_activation"],
                                 "evidence": dimension_refs["model_activation"]},
            "sanitizer_activation": {"status": "qualified", "execution_eligible": True,
                                     "assessment": control_run["assessment"]["sanitizer_activation"],
                                     "evidence": dimension_refs["sanitizer_activation"]},
        }
        control_run["dimensions"] = {name: value["evidence"] if name != "query_resolution_compile" else value["receipt"]
                                      for name, value in dimensions.items()}
        # Re-save only after the final immutable dimension set is established;
        # the run's assessment is unchanged by this reference-only projection.
        write(control_run_path, control_run)
        control_run_ref = ref(root, control_run_path)
        receipt = {
            "schema": "analyzer-qualification-receipt/v092",
            "status": entry_replayed["status"], "execution_eligible": True,
            "group_id": replay.GROUP_ID, "groups": [replay.GROUP_ID],
            "population_sha256": population_sha,
            "fixture_revision": common_population["fixture_revision"],
            "identity": plan["identity"], "identity_components": plan["identity_components"],
            "execution_plan_projection_sha256": qualification.plan_projection_sha256(plan),
            "control_run": control_run_ref, "dimensions": dimensions,
        }
        receipt_path = output / "qualification-receipt.json"
        write(receipt_path, receipt)
        index.update(status="complete", ended_at_unix_seconds=int(time.time()),
                     control_run=control_run_ref, qualification_receipt=ref(root, receipt_path),
                     elapsed_seconds=control_run["elapsed_seconds"])
        write(output / "capture-index.json", index)
        return receipt
    except Exception as error:
        index.update(status="incomplete", ended_at_unix_seconds=int(time.time()),
                     elapsed_seconds=time.monotonic() - started,
                     failure={"type": type(error).__name__, "message": str(error)})
        write(output / "capture-index.json", index)
        write(output / "incomplete.json", {"schema": "codeql-swift-control-capture-incomplete/v092",
                                             "status": "incomplete", "execution_eligible": False,
                                             "failure": index["failure"], "partial": index["partial"]})
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default=runner.EXECUTION_PLAN_PATH)
    parser.add_argument("--control-plan", required=True, help="repository-relative path to the preregistered control plan")
    parser.add_argument("--query-receipt", required=True, help="repository-relative path to fresh query resolve/compile receipt")
    parser.add_argument("--output", type=Path, required=True, help="a new path under reports/releases/v0.9.2/qualification")
    args = parser.parse_args(argv)
    root = runner.ROOT.resolve()
    try:
        plan = read_json(root / args.plan)
        control_ref = plan.get("qualification_control_plan")
        require(isinstance(control_ref, dict) and control_ref.get("path") == args.control_plan,
                "--control-plan must match the executable plan's digest-bound control-plan reference")
        query_path = Path(args.query_receipt)
        query_ref = {"path": query_path.as_posix(), "sha256": sha(root / query_path)}
        receipt = capture(root, args.plan, control_ref, query_ref, args.output)
        print(json.dumps({"status": receipt["status"], "execution_eligible": receipt["execution_eligible"],
                          "receipt": (args.output / "qualification-receipt.json").as_posix()}, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, process.ProcessCleanupError) as error:
        print("CodeQL v0.9.2 control capture failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
