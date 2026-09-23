#!/usr/bin/env python3
"""Check retained Swift body-control evidence without scoring or rerunning analysis."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/swift-resolved-native-v1"
PLAN_PATH = BASE / "conversion-body-plan-v1.json"
DEFAULT_ATTEMPT = BASE / "conversion-body-attempt-01"
PATCHED_PROFILE = "adapter-patched-conversion"
STOCK_PROFILE = "adapter-assisted-stock-conversion"
QUERY_NAMES = ("roles", "flow", "identity", "summary-identity", "summary-ports",
               "summary-transfer", "summary-store")
DECODE_NAMES = tuple(name + "-decode" for name in QUERY_NAMES)
PHASE_NAMES = QUERY_NAMES + DECODE_NAMES


class VerificationError(ValueError):
    """Evidence is malformed, tampered with, or inconsistent with its preregistration."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def check_scope(plan: dict) -> None:
    require(plan.get("scope") == "non-scored-conversion-body-and-independent-initializer-control",
            "unexpected plan scope")
    require(plan.get("scored_activation") is False, "preregistration promotes scoring")
    require(plan.get("aggregate_memory_compliance") == "unproven", "memory status was promoted")
    require(plan.get("semantic_completeness") == "unproven", "semantic completeness was promoted")
    require(plan.get("ordinary_body_required") is True, "ordinary-body positive was weakened")
    require(plan.get("expected_patched_sink_labels") == ["POSITIVE_SINK", "BODY_SINK"],
            "required patched positive sinks changed")
    require(plan.get("expected_patched_unmodeled_call_prefixes") ==
            ["LOCAL", "BODY", "BODY_SAFE", "WRONG_ARITY"], "unmodeled-call controls changed")
    require(plan.get("control_labels", {}).get("POSITIVE_SINK") == 20 and
            plan.get("control_labels", {}).get("BODY_SINK") == 35 and
            plan.get("control_labels", {}).get("WRONG_ARITY_SINK") == 42,
            "control endpoint lines changed")


def check_bound_inputs(root: Path, plan: dict) -> None:
    for field in ("control_files", "query_files", "vendor_files", "runner_files"):
        for relative, expected in plan.get(field, {}).items():
            path = root / relative
            require(path.is_file() and sha256(path) == expected,
                    f"preregistered {field} digest mismatch: {relative}")

    main = root / "evidence/swift-resolved-native-v1/conversion-body-control/main.swift"
    lines = main.read_text().splitlines()
    for label, line_no in plan["control_labels"].items():
        require(line_no <= len(lines) and f"// {label}" in lines[line_no - 1],
                f"control label moved or changed: {label}")


def check_manifest(directory: Path) -> None:
    """Validate exact file closure and content hashes for a completed package manifest."""
    manifest_path = directory / "manifest.json"
    manifest = read_json(manifest_path)
    require(isinstance(manifest, dict), f"invalid manifest: {manifest_path}")
    actual = {path.relative_to(directory).as_posix()
              for path in directory.rglob("*") if path.is_file() and path != manifest_path}
    require(set(manifest) == actual, f"manifest file closure mismatch: {directory}")
    for name, expected in manifest.items():
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts,
                f"unsafe manifest path: {name}")
        path = directory.joinpath(*relative.parts)
        require(path.is_file() and sha256(path) == expected,
                f"manifest digest mismatch: {directory}/{name}")


def check_lane_query_copies(root: Path, attempt: Path, plan: dict) -> None:
    for relative, expected in plan["query_files"].items():
        source = root / relative
        lane = "stock" if "/conversion-body-stock-queries-v1/" in relative else "probe"
        copy = attempt / lane / "queries" / source.name
        if copy.exists():
            require(sha256(copy) == expected, f"query copy mismatch: {lane}/{source.name}")


def check_source_archive(attempt: Path, plan: dict) -> None:
    archive = attempt / "source.zip"
    if not archive.is_file():
        return
    source = attempt / "probe/main.swift"
    require(source.is_file(), "retained extractor source is missing")
    expected = sha256(source)
    try:
        with zipfile.ZipFile(archive) as zipped:
            members = [name for name in zipped.namelist() if name.endswith("/main.swift") or name == "main.swift"]
            require(len(members) == 1, "source archive must contain exactly one main.swift")
            require(hashlib.sha256(zipped.read(members[0])).hexdigest() == expected,
                    "source archive main.swift differs from retained control")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise VerificationError(f"invalid retained source archive: {exc}") from exc
    bound = plan["control_files"]["evidence/swift-resolved-native-v1/conversion-body-control/main.swift"]
    require(expected == bound, "extracted source differs from preregistered control")


def check_command(command: dict, name: str, lane: str) -> None:
    require(command.get("exit_status") == 0 and command.get("timed_out") is False,
            f"{lane} phase failed: {name}")
    require(command.get("cleanup_status") == "tracked-processes-stopped",
            f"{lane} cleanup incomplete: {name}")
    require(not command.get("cleanup_error"), f"{lane} cleanup error: {name}")
    expected_deadline = 150 if name == "database-create" else 60
    require(command.get("deadline_seconds") == expected_deadline,
            f"{lane} phase deadline mismatch: {name}")
    argv = command.get("argv", [])
    if name == "database-create":
        require("--ram=512" in argv, f"{lane} extraction memory request changed")
    elif name in QUERY_NAMES:
        require("--ram=2048" in argv and "--timeout=60" in argv,
                f"{lane} analysis budget changed: {name}")


def check_toolchain_joins(witness: dict, prior: dict, run=None) -> None:
    for key in ("compiler_sha256", "extractor_sha256"):
        value = witness.get(key)
        require(isinstance(value, str) and len(value) == 64 and value == prior.get(key),
                f"probe {key} does not match preregistered prior witness")
    if run is not None:
        require(run.get("compiler_sha256") == witness.get("compiler_sha256"),
                "outer run compiler hash does not match probe witness")
        assets = run.get("assets", {})
        require(assets.get("codeql/swift/tools/osx64/extractor.real") ==
                witness.get("extractor_sha256"), "outer run extractor hash does not match probe witness")


def check_extraction_gate(log_directory: Path, witness: dict, root: Path = ROOT) -> dict:
    helper_path = root / "scripts/swift_extraction_integrity.py"
    spec = importlib.util.spec_from_file_location("swift_extraction_integrity", helper_path)
    require(spec is not None and spec.loader is not None, "cannot load Swift extraction log inspector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observed = module.inspect_logs(log_directory)
    require(observed.get("ready_for_observation") is True and observed.get("logs_checked", 0) > 0,
            "Swift extractor logs are not ready for observation")
    require(not observed.get("errors"), "Swift extractor logs contain compiler errors")
    require(witness.get("extraction_integrity") == observed,
            "probe witness extraction log assessment does not match retained logs")
    require(not witness.get("probe_error"), "probe witness contains probe_error")
    require(not witness.get("cleanup_error"), "probe witness contains cleanup_error")
    return observed


def lane_tables(directory: Path) -> tuple[dict, list[str]]:
    tables = {}
    missing = []
    for name in QUERY_NAMES:
        path = directory / f"{name}.json"
        if not path.is_file():
            missing.append(name)
            continue
        value = read_json(path)
        select = value.get("#select")
        require(isinstance(select, dict) and isinstance(select.get("tuples"), list),
                f"malformed decoded query table: {directory.name}/{name}")
        tables[name] = select["tuples"]
    return tables, missing


def check_table_shapes(tables: dict, lane: str) -> None:
    widths = {"roles": 4, "flow": 4, "identity": 7, "summary-identity": 8,
              "summary-ports": 4, "summary-transfer": 5, "summary-store": 6}
    for name, rows in tables.items():
        for row in rows:
            require(isinstance(row, list) and len(row) == widths[name],
                    f"malformed {lane} row in {name}")


def check_roles_and_identity(tables: dict, profile: str, labels: dict) -> None:
    roles = tables["roles"]
    require(all(row[2] == profile for row in roles), "invented or cross-lane role profile")
    sources = [row for row in roles if row[3] == "environment"]
    require(sources == [[labels["SOURCE"], 15, profile, "environment"]],
            f"{profile} source role identity mismatch")
    sink_lines = {labels[name] for name in (
        "POSITIVE_SINK", "SAFE_SINK", "LOCAL_SINK", "BODY_SINK", "BODY_SAFE_SINK", "WRONG_ARITY_SINK")}
    role_sinks = {(row[0], row[1]) for row in roles if row[3] == "sink"}
    require({line for line, _ in role_sinks} == sink_lines, f"{profile} sink inventory mismatch")
    require(all((line, 87) in role_sinks for line in sink_lines),
            f"{profile} flow sink locations do not join to declared roles")
    require(all(row[3] in ("environment", "sink") for row in roles),
            f"{profile} contains an unknown role")

    require(tables["identity"] == [[labels["SOURCE"], "Foundation", "Foundation", "ProcessInfo",
                                    "environment", "[String : String]", "ClassType"]],
            f"{profile} source declaration identity mismatch")


def expected_patched_summary_rows() -> dict[int, list]:
    # Call-site identity is kept distinct from declaration owner and module identity.
    values = [
        [16, 17, "Foundation", "Foundation", "Data", "init(_:)", 1, True],
        [17, 19, "Foundation", "Foundation", "Data", "base64EncodedString(options:)", 1, True],
        [18, 25, "Foundation", "Foundation", "Data", "init(base64Encoded:options:)", 2, True],
        [19, 25, "Foundation", "Swift", "String", "init(data:encoding:)", 2, True],
        [21, 21, "Foundation", "Foundation", "Data", "init(_:)", 1, True],
        [22, 23, "Foundation", "Foundation", "Data", "base64EncodedString(options:)", 1, True],
        [23, 29, "Foundation", "Foundation", "Data", "init(base64Encoded:options:)", 2, True],
        [24, 29, "Foundation", "Swift", "String", "init(data:encoding:)", 2, True],
        [26, 22, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(_:)", 1, False],
        [27, 24, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "base64EncodedString(options:)", 1, False],
        [28, 30, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(base64Encoded:options:)", 2, False],
        [29, 30, "DataFlowBenchTaintSwift", "Swift", "String", "init(data:encoding:)", 2, False],
        [31, 21, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(_:)", 1, False],
        [32, 23, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "base64EncodedString(options:)", 1, False],
        [33, 29, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(base64Encoded:options:)", 2, False],
        [34, 29, "DataFlowBenchTaintSwift", "Swift", "String", "init(data:encoding:)", 2, False],
        [36, 25, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(_:)", 1, False],
        [37, 27, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "base64EncodedString(options:)", 1, False],
        [38, 33, "DataFlowBenchTaintSwift", "DataFlowBenchTaintSwift", "Data", "init(base64Encoded:options:)", 2, False],
        [39, 33, "DataFlowBenchTaintSwift", "Swift", "String", "init(data:encoding:)", 2, False],
        [41, 30, "DataFlowBenchTaintSwift", "Swift", "String", "init(data:encoding:unrelated:)", 3, False],
    ]
    return {row[0]: row for row in values}


def check_patched_summaries(tables: dict) -> dict:
    expected = expected_patched_summary_rows()
    actual_rows = tables["summary-identity"]
    by_call = {row[0]: row for row in actual_rows}
    require(len(actual_rows) == len(by_call), "duplicate call-site summary identity")
    require(by_call == expected, "patched summary identity/applicability changed")
    custom_calls = {line for line, row in expected.items() if not row[7]}
    require(len(custom_calls) == 13, "expected 13 unmodeled local calls")

    ports = tables["summary-ports"]
    require(len(ports) == 10 and {row[0] for row in ports} == {16, 17, 18, 19, 21, 22, 23, 24},
            "patched summary ports do not match resolved Foundation calls")
    require(all(row[3] == "" for row in ports), "patched summary port has invented origin")
    transfers = tables["summary-transfer"]
    require(len(transfers) == 6 and {row[0] for row in transfers} == {16, 17, 18, 21, 22, 23},
            "patched summary transfer coverage changed")
    stores = tables["summary-store"]
    require({(row[0], row[5]) for row in stores} == {
        (16, "CollectionElement"), (19, "OptionalSome"),
        (21, "CollectionElement"), (24, "OptionalSome")},
        "patched summary store identity changed")
    for row in transfers + stores:
        require(row[0] == row[1] == row[3] and row[0] in expected and expected[row[0]][7] is True,
                "summary edge is not joined to a modeled call site")
    return {"local_call_sites": len(custom_calls), "modeled_local_call_sites": 0,
            "foundation_summary_call_sites": 8}


def evaluate_patched(tables: dict, labels: dict) -> dict:
    """Return flow findings while retaining required positives and every near-miss."""
    require("roles" in tables and "flow" in tables, "patched roles/flow tables are required")
    check_table_shapes({key: value for key, value in tables.items() if key in {"roles", "flow"}}, "patched")
    check_roles_and_identity(tables, PATCHED_PROFILE, labels)
    role_sinks = {(row[0], row[1]) for row in tables["roles"] if row[3] == "sink"}
    flows = tables["flow"]
    blockers = []
    observed = set()
    for row in flows:
        source, sink, column, profile = row
        require(profile == PATCHED_PROFILE, f"invented or cross-lane flow profile: {profile}")
        require(source == labels["SOURCE"], f"unexpected patched flow source line: {source}")
        require((sink, column) in role_sinks, f"flow sink does not join to a declared sink role: {sink}:{column}")
        observed.add(sink)
    require(len(flows) == len(observed), "duplicate patched flow endpoint")

    required = {labels["POSITIVE_SINK"], labels["BODY_SINK"]}
    for line, label in ((labels["POSITIVE_SINK"], "POSITIVE_SINK"),
                        (labels["BODY_SINK"], "BODY_SINK")):
        if line not in observed:
            blockers.append(f"missing expected patched positive flow to {label}")
    for line, label in ((labels["SAFE_SINK"], "SAFE_SINK"),
                        (labels["LOCAL_SINK"], "LOCAL_SINK"),
                        (labels["BODY_SAFE_SINK"], "BODY_SAFE_SINK"),
                        (labels["WRONG_ARITY_SINK"], "WRONG_ARITY_SINK")):
        if line in observed:
            blockers.append(f"unexpected patched flow to {label}")
    unknown = observed - required - {
        labels["SAFE_SINK"], labels["LOCAL_SINK"], labels["BODY_SAFE_SINK"], labels["WRONG_ARITY_SINK"]}
    if unknown:
        blockers.append("unexpected patched flow endpoint(s): " + ",".join(map(str, sorted(unknown))))

    wrong_arity = labels["WRONG_ARITY_SINK"] in observed
    return {
        "profile": PATCHED_PROFILE,
        "flow_rows": flows,
        "observed_sink_lines": sorted(observed),
        "positive_flow_observed": labels["POSITIVE_SINK"] in observed,
        "ordinary_body_flow_observed": labels["BODY_SINK"] in observed,
        "wrong_arity_flow_observed": wrong_arity,
        "blockers": blockers,
    }


def evaluate_stock(tables: dict, labels: dict, missing: list[str]) -> dict:
    flows = tables.get("flow", [])
    roles = tables.get("roles", [])
    role_sinks = {(row[0], row[1]) for row in roles if len(row) == 4 and row[3] == "sink"}
    findings = []
    for row in flows:
        if len(row) != 4 or row[3] != STOCK_PROFILE:
            raise VerificationError("stock lane contains an invented or cross-lane profile")
        source, sink, column, _ = row
        require(source == labels["SOURCE"], "stock lane has a different source endpoint")
        require((sink, column) in role_sinks, f"stock flow sink does not join to a stock role: {sink}:{column}")
        findings.append({"source_line": source, "sink_line": sink, "sink_label":
                         next((name for name, line in labels.items() if name.endswith("SINK") and line == sink),
                              f"line-{sink}")})
    return {
        "profile": STOCK_PROFILE,
        "status": "complete" if not missing else "partial",
        "missing_queries": missing,
        "flow_rows": flows,
        "flow_findings": findings,
        "body_endpoint_reached_in_stock_output": labels["BODY_SINK"] in {row[1] for row in flows},
        "interpretation": "raw stock-lane diagnostic only; endpoint reachability may come from library summaries and is not proof of local-body propagation",
    }


def check_probe_provenance(attempt: Path, plan: dict, root: Path = ROOT) -> tuple[dict, list[str]]:
    probe = attempt / "probe"
    witness_path = probe / "witness.json"
    if not witness_path.is_file():
        return {}, ["probe/witness.json"]
    witness = read_json(witness_path)
    prior_path = root / "evidence/swift-foundation-sources-v1/control-attempt-01/witness.json"
    prior = read_json(prior_path)
    check_toolchain_joins(witness, prior)
    check_extraction_gate(probe / "log/swift/extractor", witness, root)
    require(witness.get("scope", "").startswith("non-scored"), "probe scope was promoted")
    require(witness.get("population_member") is False and witness.get("population") is None,
            "probe was represented as a scored population member")
    require(witness.get("case_sha256") == plan["control_files"][
        "evidence/swift-resolved-native-v1/conversion-body-control/control.json"], "probe case identity mismatch")
    require(witness.get("extraction_phase_deadline_seconds") == 150,
            "extraction phase budget changed")
    require(witness.get("analysis_budget") == {"wall_clock_seconds": 60, "peak_memory_mb": 2048},
            "analysis budget changed")
    require(witness.get("memory_compliance") == "unproven" and
            witness.get("unqualified_feasibility") is False, "probe completeness/feasibility was promoted")

    missing = []
    for phase in ("database-create", "database-resolve") + QUERY_NAMES:
        command = witness.get("phases", {}).get(phase)
        if not command:
            missing.append("probe phase " + phase)
        else:
            check_command(command, phase, "patched")
    for name in ("database-create", "database-resolve") + PHASE_NAMES:
        path = probe / f"{name}.command.json"
        if not path.is_file():
            missing.append("probe command " + name)
        else:
            check_command(read_json(path), name, "patched")
    if not missing and (probe / "manifest.json").is_file():
        check_manifest(probe)
    elif not (probe / "manifest.json").is_file():
        missing.append("probe/manifest.json")
    return witness, missing


def check_outer_run(attempt: Path, plan: dict, witness: dict, root: Path = ROOT) -> list[str]:
    run_path = attempt / "run.json"
    manifest_path = attempt / "manifest.json"
    missing = []
    if run_path.is_file():
        run = read_json(run_path)
        require(run.get("scope") == plan["scope"] and
                run.get("plan_sha256") == sha256(PLAN_PATH), "outer run preregistration mismatch")
        require(run.get("scored_activation") is False, "outer run promotes scoring")
        prior = read_json(root / "evidence/swift-foundation-sources-v1/control-attempt-01/witness.json")
        check_toolchain_joins(witness, prior, run)
        require(run.get("source_commit") == witness.get("source_commit"), "outer/probe source commit mismatch")
        stock_phases = run.get("stock_phases", {})
        for name in PHASE_NAMES:
            command = stock_phases.get(name)
            if command is None:
                missing.append("stock phase " + name)
            else:
                check_command(command, name, "stock")
        if run.get("exit_status") != 0:
            missing.append("outer runner exit status is not successful")
    else:
        missing.append("run.json (stock lane may still be running)")
    if manifest_path.is_file():
        check_manifest(attempt)
    else:
        missing.append("manifest.json (outer attempt package not finalized)")
    return missing


def verify(attempt: Path = DEFAULT_ATTEMPT, root: Path = ROOT) -> dict:
    plan_path = root / "evidence/swift-resolved-native-v1/conversion-body-plan-v1.json"
    plan = read_json(plan_path)
    check_scope(plan)
    check_bound_inputs(root, plan)
    check_lane_query_copies(root, attempt, plan)
    labels = plan["control_labels"]

    witness, incomplete = check_probe_provenance(attempt, plan, root)
    check_source_archive(attempt, plan)
    incomplete.extend(check_outer_run(attempt, plan, witness, root))

    patched, patched_missing = lane_tables(attempt / "probe")
    check_table_shapes(patched, "patched")
    if "roles" in patched and "identity" in patched:
        check_roles_and_identity(patched, PATCHED_PROFILE, labels)
    if "flow" in patched and "roles" in patched:
        patched_result = evaluate_patched(patched, labels)
    else:
        patched_result = {"profile": PATCHED_PROFILE, "flow_rows": patched.get("flow", []),
                          "observed_sink_lines": [], "positive_flow_observed": False,
                          "ordinary_body_flow_observed": False, "wrong_arity_flow_observed": False,
                          "blockers": ["patched roles/flow output is incomplete"]}
    if "summary-identity" in patched and "summary-ports" in patched and \
            "summary-transfer" in patched and "summary-store" in patched:
        patched_result["summary_applicability"] = check_patched_summaries(patched)
    else:
        incomplete.extend("patched query " + name for name in
                          ("summary-identity", "summary-ports", "summary-transfer", "summary-store")
                          if name not in patched)
    incomplete.extend("patched query " + name for name in patched_missing)

    stock, stock_missing = lane_tables(attempt / "stock")
    check_table_shapes(stock, "stock")
    stock_result = evaluate_stock(stock, labels, stock_missing)
    incomplete.extend("stock query " + name for name in stock_missing)

    # A missing/unfinalized stock run is reported independently from patched semantic blockers.
    all_blockers = list(patched_result["blockers"])
    integrity_status = "partial" if incomplete else "complete"
    return {
        "verifier": "swift-conversion-body-v1",
        "scope": plan["scope"],
        "plan_sha256": sha256(plan_path),
        "source_commit": witness.get("source_commit"),
        "integrity_status": integrity_status,
        "incomplete_evidence": sorted(set(incomplete)),
        "semantic_status": "blocked" if all_blockers else "positive-control-observed",
        "qualification": "not-qualified; diagnostic-only; score activation disabled",
        "patched_lane": patched_result,
        "stock_lane": stock_result,
        "limitations": [
            "stock BODY_SINK reachability is not proof of local-body propagation",
            "aggregate memory compliance and semantic completeness remain unproven",
            "no fixture execution or score activation",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    args = parser.parse_args()
    try:
        report = verify(args.attempt.resolve())
    except VerificationError as exc:
        print(json.dumps({"integrity_status": "failed", "qualification": "not-qualified",
                          "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
