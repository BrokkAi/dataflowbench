#!/usr/bin/env python3
"""Accept unchanged diagnostic invocation costs through an offline wording audit."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
CAMPAIGN = "reports/timing/v0.9.2/20261122-08"
SOURCE = "execution-state/timing-v092-20261122-08/sources/joern-swift-common108"
INVENTORY = CAMPAIGN + "/capture-evidence-inventory-01.json"
INVENTORY_SHA = "466482c18cd38ce78e5a1562ad19470a75b139bfef4e2246b140ffce7d580f98"
PLAN_SHA = "d508f111908f2540f52085f47fc37551b553cc6fc03022c118db4bda784ebc78"
SCOPE_PLAN = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-finalization-03/attempt-07/execution-plan.json"
SCOPE_PLAN_SHA = "f4ae8f2ca3ece1bb253ce24a70368e969f0a25bc8d35dd2c8f7578d730aff4e9"
AMENDMENT = "docs/latency-v092-20261123-decline-wording.md"
AMENDMENT_SHA = "dedfee85a49f383e978c37d4dd406cc28b4375af7fc7510c6fd89dd380cd8015"
PREFIX = "reports/timing/v0.9.2/reconciliation-20261123-01"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(root, relative):
    require(isinstance(relative, str) and relative, "nonempty relative path required")
    part = PurePosixPath(relative)
    require(not part.is_absolute() and ".." not in part.parts and str(part) == relative,
            "unsafe evidence path")
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()), "evidence escaped repository")
    for parent in (path, *path.parents):
        if parent == root:
            break
        require(not parent.is_symlink(), "symlinked evidence/output path")
    return path


def reference(root, relative):
    path = safe_path(root, relative)
    require(path.is_file(), "missing evidence: " + relative)
    return {"path": relative, "sha256": digest(path.read_bytes())}


def object_json(raw):
    value = json.loads(raw)
    require(isinstance(value, dict), "JSON object required")
    return value


class Capture:
    def __init__(self, root):
        self.root = root.resolve()
        blob = safe_path(self.root, INVENTORY).read_bytes()
        require(digest(blob) == INVENTORY_SHA, "capture inventory identity changed")
        inventory = object_json(blob)
        self.files = inventory["files"]
        require(len(self.files) == inventory["file_count"] == 7559, "capture denominator changed")
        self.by_path = {row["path"]: row for row in self.files}
        require(len(self.by_path) == len(self.files), "duplicate capture inventory path")

    def verify(self):
        for item in self.files:
            path = safe_path(self.root, item["path"])
            require(path.is_file(), "sealed file missing: " + item["path"])
            info = path.stat()
            require(info.st_size == item["size_bytes"] and stat.S_IMODE(info.st_mode) == item["mode"]
                    and digest(path.read_bytes()) == item["sha256"], "sealed capture changed: " + item["path"])

    def read(self, relative, expected=None):
        require(relative in self.by_path, "input is outside the sealed capture: " + relative)
        blob = safe_path(self.root, relative).read_bytes()
        require(digest(blob) == self.by_path[relative]["sha256"], "sealed input changed")
        require(expected is None or digest(blob) == expected, "reference digest differs from capture")
        return blob

    def json(self, relative, expected=None):
        return object_json(self.read(relative, expected))

    def source_ref(self, ref):
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact source reference required")
        return self.read(SOURCE + "/" + ref["path"], ref["sha256"])


def released(root, relative, expected=None):
    safe_path(root, relative)
    raw = subprocess.check_output(["git", "show", RELEASE + ":" + relative], cwd=root)
    # A Git LFS pointer is still immutable identity; read only a locally retained
    # body with that exact OID. Never fetch tools or execute a released producer.
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", raw)
        require(match is not None, "malformed released LFS pointer")
        raw = safe_path(root, relative).read_bytes()
        require(digest(raw) == match[1].decode() and len(raw) == int(match[2]), "released LFS body unavailable")
    require(expected is None or digest(raw) == expected, "released dependency digest mismatch: " + relative)
    return raw


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def validate_report_raw_binding(row, raw, raw_ref):
    require(type(row["duration_ms"]) is int and row["duration_ms"] == raw["duration_ms"]
            and row["outcome"] == raw["state"]
            and row["witness_checkpoints"] == raw["witness_checkpoints"]
            and row["raw_output"] == raw_ref["path"] and row["raw_sha256"] == raw_ref["sha256"],
            "normalized row timing or raw-result binding differs")


def validate_historical_provenance(case_id, historical, scope, historical_plan, population):
    require(historical.get("schema") == "joern-current108-partition-decision/v1"
            and historical.get("case_id") == case_id and historical.get("outcome") == "unsupported"
            and historical.get("population_sha256") == population
            and historical.get("identity") == historical_plan["identity"]
            and historical.get("reason") == scope["historical_reason"]
            and historical.get("identity") == scope["historical_identity"]
            and historical.get("fixture_revision") == scope["historical_fixture_revision"]
            and historical.get("current_case_sha256") == scope["case_json"]["sha256"]
            and historical.get("current_fixture_digests") == scope["fixtures"]
            and historical_plan["cases"][case_id] == scope["historical_case_row"]
            and historical_plan["cases"][case_id]["decision"] == scope["historical_decision"],
            "historical reason provenance is not the exact case-bound decline")


def validate_capture(root):
    from v092_joern_swift_wording import reconcile_reports

    capture = Capture(root)
    capture.verify()
    plan = capture.json(CAMPAIGN + "/supplement-plan-01.json", PLAN_SHA)
    require(plan["release_commit"] == RELEASE and plan["case_count"] == 108, "wrong campaign release/population")
    qualified = object_json(capture.source_ref(plan["qualified_execution_plan"]))
    require(len(qualified["configurations"]["joern-current108"]) == 45, "configuration denominator changed")
    for configured_ref in qualified["configurations"]["joern-current108"]:
        capture.source_ref(configured_ref)
    run = capture.json(SOURCE + "/reports/raw/joern-common-v2/current108-v092-03/run.json")
    attempt_path = CAMPAIGN + "/attempts/joern-swift-common108/attempt-01/terminal.json"
    attempt = capture.json(attempt_path)
    terminal = capture.json(CAMPAIGN + "/campaign-terminal.json")
    require(attempt["status"] == "failed" and terminal["execution_status"] == "stopped-fail-closed",
            "original failed acceptance changed")
    require(type(attempt["exit_code"]) is int and attempt["exit_code"] == 0
            and attempt["timed_out"] is False and attempt["capacity_loss"] is None,
            "measured wrapper did not finish successfully")
    require(attempt["resource_baseline_after_dispatch"]["unchanged"] is True, "resource baseline drift")
    require(run["identity"] == qualified["identity"] and run["population_sha256"] == plan["population_sha256"]
            and run["fixture_revision"] == plan["fixture_revision"], "raw run identity drift")
    require(run["plan_sha256"] == plan["qualified_execution_plan"]["sha256"]
            and run["qualification_sha256"] == plan["fresh_qualification"]["sha256"], "raw plan/qualification drift")
    witness = object_json(capture.source_ref(run["identity_witness"]))
    version = witness["command"]
    require(witness["observed"] == qualified["identity"]
            and version["argv"] == [qualified["runtime"]["joern"]]
            and type(version["exit_status"]) is int and version["exit_status"] == 0
            and version["timed_out"] is False and version["cleanup_status"] == "tracked-processes-stopped",
            "recorded runtime identity witness differs")
    banner = capture.source_ref(witness["stdout"]).decode()
    require(re.search(r"(?<![0-9.])" + re.escape(qualified["identity"]["tool_version"]) + r"(?![0-9.])", banner),
            "recorded version banner differs")
    original_costs = capture.json(CAMPAIGN + "/case-invocation-costs-01.json")
    rows = original_costs["rows"]
    require(rows == attempt["reconciliation"]["frozen_report_comparison"]["case_timing_rows"], "retained cost rows differ")
    by_cost = {row["case_id"]: row for row in rows}
    raw_by_id = {}
    raw_refs = {}
    partial = []
    phase_count = 0
    for result in run["results"]:
        case_id = result["case_id"]
        require(case_id not in raw_by_id, "duplicate raw case")
        raw = object_json(capture.source_ref(result["raw"]))
        for artifact in raw["native_outputs"]:
            capture.source_ref(artifact)
        require(raw["case_id"] == case_id and raw["identity"] == qualified["identity"]
                and raw["plan_sha256"] == run["plan_sha256"]
                and raw["qualification_sha256"] == run["qualification_sha256"], "raw row identity drift")
        require(raw["population_sha256"] == plan["population_sha256"]
                and raw["fixture_revision"] == plan["fixture_revision"], "raw row population drift")
        cost = by_cost[case_id]
        require(type(raw["executed"]) is bool and cost["executed"] is raw["executed"]
                and cost["latency_sample_included"] is raw["executed"]
                and cost["duration_ms"] == raw["duration_ms"]
                and cost["raw_outcome"] == raw["raw_outcome"]
                and cost["normalized_outcome"] == raw["state"]
                and cost["native_outputs"] == raw["native_outputs"]
                and cost["raw_output"] == result["raw"], "cost row differs from its raw invocation")
        require(len(cost["commands"]) == len(raw["commands"]), "cost phase coverage differs")
        phases = []
        for command_ref, timing in zip(raw["commands"], cost["commands"]):
            command = object_json(capture.source_ref(command_ref))
            phase = PurePosixPath(command_ref["path"]).name.removesuffix(".command.json")
            phases.append(phase)
            require(timing["reference"] == command_ref and timing["phase_id"] == phase,
                    "timing command binding differs")
            require(type(command["exit_status"]) is int and command["exit_status"] == 0
                    and command["timed_out"] is False and command["cleanup_status"] == "tracked-processes-stopped",
                    "phase failed or cleanup uncertain")
            require(finite_number(command["elapsed_seconds"])
                    and finite_number(command["deadline_seconds"])
                    and command["elapsed_seconds"] <= command["deadline_seconds"]
                    and all(timing[key] == command[key] for key in ("exit_status", "timed_out", "elapsed_seconds")),
                    "timing values or phase deadline differ")
        phase_count += len(phases)
        if raw["executed"]:
            require(raw["state"] == "inconclusive" and phases in (["typecheck", "frontend"], ["typecheck", "frontend", "query"]),
                    "attempted outcome or phase sequence changed")
            require(type(raw["duration_ms"]) is int and raw["duration_ms"] >= 0
                    and finite_number(raw["total_elapsed_seconds"])
                    and raw["duration_ms"] == int(raw["total_elapsed_seconds"] * 1000), "case timing changed")
            if len(phases) == 2:
                require("IncompleteExecution" in raw["diagnostics"] and "Incomplete:SwiftImport" in raw["diagnostics"],
                        "partial query omission lacks retained incompleteness")
                partial.append({"case_id": case_id, "query_phase_executed": False, "raw": result["raw"]})
        raw_by_id[case_id] = raw
        raw_refs[case_id] = result["raw"]
    require(len(raw_by_id) == len(by_cost) == len(rows) == 108 and set(raw_by_id) == set(qualified["cases"]), "case roster differs")
    require(phase_count == 284 and len(partial) == 4, "recorded phase denominator changed")

    frozen_base = object_json(released(root, "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"))
    original_refs = frozen_base["configurations"]["joern-current108"]
    require(len(original_refs) == 33 and qualified["configurations"]["joern-current108"][:33] == original_refs,
            "original model/query/configuration closure changed")
    for item in original_refs:
        require(capture.source_ref(item) == released(root, item["path"], item["sha256"]), "original configuration bytes changed")
    scope_plan = object_json(released(root, SCOPE_PLAN, SCOPE_PLAN_SHA))
    decisions, scopes, cases, authorities = {}, {}, {}, {}
    for case_id, selection in qualified["cases"].items():
        if selection["disposition"] != "unsupported":
            continue
        scope_ref = qualified["unsupported_decisions"][case_id]
        scope = object_json(capture.source_ref(scope_ref))
        historical = object_json(capture.source_ref(scope["historical_decision"]))
        require(scope["capability_source_plan"] == plan["capability_binding"]["source"], "historical source plan changed")
        historical_plan = object_json(capture.source_ref(scope["capability_source_plan"]))
        validate_historical_provenance(case_id, historical, scope, historical_plan, plan["population_sha256"])
        released_selection = scope_plan["cases"][case_id]
        require({key: value for key, value in released_selection.items() if key != "decision"} == selection,
                "released declared scope differs from captured selection")
        decision_ref = released_selection["decision"]
        decision = object_json(released(root, decision_ref["path"], decision_ref["sha256"]))
        case = object_json(capture.source_ref(scope["case_json"]))
        require(scope["case_json"]["sha256"] == decision["current_case_sha256"], "current case bytes differ from release decision")
        require(scope["fixtures"] == decision["current_fixture_digests"], "current fixture mapping differs")
        for fixture in decision["current_fixture_digests"]:
            require(capture.source_ref(fixture) == released(root, fixture["path"], fixture["sha256"]), "fixture bytes differ")
        decisions[case_id], scopes[case_id], cases[case_id] = decision, scope, case
        authorities[case_id] = {"released_scope_decision": {**decision_ref, "commit": RELEASE},
                                "captured_scope_decision": scope_ref, "historical_decision": scope["historical_decision"],
                                "proof_scope_not_transferred": decision["proof_scope"],
                                "qualification_limits_preserved": decision["qualification_limits"]}

    reports, frozen_reports, report_refs = [], [], []
    descriptors = attempt["reconciliation"]["reports"]
    require(len(descriptors) == len(plan["frozen_report_bindings"]) == 5, "report partition count changed")
    for descriptor, binding in zip(descriptors, plan["frozen_report_bindings"]):
        candidate = capture.json(SOURCE + "/" + descriptor["derived_path"], descriptor["derived_sha256"])
        original = capture.json(SOURCE + "/" + descriptor["original_path"], descriptor["original_sha256"])
        frozen = object_json(released(root, binding["git_path"], binding["sha256"]))
        expected = copy.deepcopy(original)
        expected["configuration_hash"] = plan["configuration_provenance"]["candidate_configuration_hash"]
        require(candidate == expected, "existing projection changed more than configuration hash")
        require(frozen["configuration_hash"] == plan["configuration_provenance"]["historical_configuration_hash"], "frozen configuration identity drift")
        for field in ("schema_version", "tool", "tool_version", "tool_build_identity", "adapter_version", "fixture_revision", "cold_or_warm"):
            require(candidate[field] == frozen[field], "report identity mismatch: " + field)
        for row in candidate["results"]:
            case_id = row["case_id"]
            raw, raw_ref = raw_by_id[case_id], raw_refs[case_id]
            validate_report_raw_binding(row, raw, raw_ref)
        reports.append(candidate)
        frozen_reports.append(frozen)
        report_refs.append({"original_projection": {"path": SOURCE + "/" + descriptor["derived_path"], "sha256": descriptor["derived_sha256"]},
                            "frozen_report": {"commit": RELEASE, "path": binding["git_path"], "sha256": binding["sha256"]}})
    result = reconcile_reports(reports, frozen_reports, decisions, raw_by_id, scopes, cases,
                               qualified["identity"], plan["population_sha256"], plan["fixture_revision"])
    require(result["attempt_count"] == 96 and result["decline_count"] == 12 and len(result["changes"]) == 12,
            "reconciliation changed its exact permitted population")
    return {"capture": capture, "plan": plan, "attempt": attempt, "result": result, "authorities": authorities,
            "rows": rows, "partial": partial, "report_refs": report_refs, "attempt_path": attempt_path}


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def build(root, audit_number, check_only=False):
    root = root.resolve()
    require(re.fullmatch(r"[0-9]{2}", audit_number) is not None and audit_number != "00", "unused audit number 01-99 required")
    output_relative = PREFIX + "/joern-swift-audit-" + audit_number
    output = safe_path(root, output_relative)
    require(check_only or not output.exists(), "audit output already exists; use a new audit number")
    require(reference(root, AMENDMENT)["sha256"] == AMENDMENT_SHA, "A37 authorization changed")
    data = validate_capture(root)
    if check_only:
        data["capture"].verify()
        return {"status": "verified-wording-only-diagnostic-reconciliation", "attempt_cost_rows": 96,
                "declines": 12, "partial_invocations": 4, "new_analyzer_invocations": 0}
    protected = [AMENDMENT, "scripts/v092_reconcile_joern_swift_wording.py", "scripts/v092_joern_swift_wording.py",
                 "scripts/test-v092-reconcile-joern-swift-wording.py", "scripts/test-v092-joern-swift-wording-cli.py"]
    for path in protected:
        committed = subprocess.check_output(["git", "show", "HEAD:" + path], cwd=root)
        require(digest(committed) == reference(root, path)["sha256"], "reconciler input is not committed: " + path)
    output.mkdir(parents=True, exist_ok=False)
    derived = []
    for index, report in enumerate(data["result"]["reports"]):
        path = output / "normal" / f"report-{index}.json"
        write_new(path, report)
        derived.append({**data["report_refs"][index], "corrected_projection": reference(root, path.relative_to(root).as_posix())})
    mapping = [{**change, **data["authorities"][change["case_id"]]} for change in data["result"]["changes"]]
    write_new(output / "diagnostic-mapping.json", {"schema": "v092-decline-wording-mapping/v1", "retrospective": True,
                                                   "source_reference_root": SOURCE, "changes": mapping})
    limits = {"retrospective": True, "new_analyzer_invocations": 0, "certified_settled_timing": False,
              "accepted_successful_analysis_latency_rows": 0, "full_model_qualification": False,
              "scored_activation": False, "publication_eligible": False}
    write_new(output / "diagnostic-invocation-costs.json", {"schema": "v092-accepted-diagnostic-invocation-costs/v1", **limits,
              "accepted_diagnostic_invocation_cost_rows": 96, "unsupported_no_invocation_rows": 12,
              "original_costs": reference(root, CAMPAIGN + "/case-invocation-costs-01.json"),
              "raw_reference_root": SOURCE, "rows": data["rows"], "partial_invocations": data["partial"]})
    data["capture"].verify()
    receipt = {"schema": "v092-retrospective-swift-wording-acceptance/v1", **limits,
               "status": "accepted-diagnostic-invocation-costs", "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "accepted_diagnostic_invocation_cost_rows": 96, "unsupported_no_invocation_rows": 12,
               "all_108_rows_reconciled": True, "diagnostic_changes": 12, "attempted_rows_changed": 0,
               "original_controller_acceptance": "failed", "original_files_changed": False,
               "raw_timing_values_changed": False, "sealed_capture_files_verified_before_and_after": 7559,
               "original_attempt_terminal": reference(root, data["attempt_path"]),
               "original_campaign_terminal": reference(root, CAMPAIGN + "/campaign-terminal.json"),
               "capture_inventory": reference(root, INVENTORY), "campaign_plan": reference(root, CAMPAIGN + "/supplement-plan-01.json"),
               "immutable_release": RELEASE, "released_scope_plan": {"commit": RELEASE, "path": SCOPE_PLAN, "sha256": SCOPE_PLAN_SHA},
               "authorizations_and_validators": [reference(root, p) for p in protected],
               "derived_reports": derived, "diagnostic_mapping": reference(root, output_relative + "/diagnostic-mapping.json"),
               "accepted_costs": reference(root, output_relative + "/diagnostic-invocation-costs.json"),
               "full_phase_invocations": 92, "partial_invocations": data["partial"],
               "inherited_resource_accounting_limitation": data["plan"]["resource_scope"]["capability_scratch_accounting_correction"],
               "inherited_semantic_uncertainty": data["plan"]["semantic_uncertainty"],
               "original_a24_settled_qualification_eligible": False,
               "descendant_containment": data["attempt"]["process_ownership"]["descendant_containment"],
               "cold_warm_equivalence": "unqualified", "cross_release_performance_claim": False,
               "repository_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
    write_new(output / "validation-receipt.json", receipt)
    files = [reference(root, path.relative_to(root).as_posix()) for path in sorted(output.rglob("*")) if path.is_file()]
    write_new(output / "audit-inventory.json", {"schema": "v092-reconciliation-audit-inventory/v1", "files": files, "file_count": len(files),
                                                "total_bytes": sum((root / item["path"]).stat().st_size for item in files)})
    return {"status": receipt["status"], "output": output_relative, "accepted_diagnostic_invocation_cost_rows": 96,
            "certified_settled_timing": False, "new_analyzer_invocations": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-number", default="01")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(ROOT, args.audit_number, args.check_only), indent=2))
