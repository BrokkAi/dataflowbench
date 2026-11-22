#!/usr/bin/env python3
"""Extract retained diagnostic costs and audit the failed acceptance; no rerun."""
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import v092_closed_process_identity as closed
import v092_timing_qualified_campaign as campaign

REPORT = Path(__file__).resolve().parent
SOURCE = ROOT / "execution-state/timing-v092-20261122-08/sources/joern-swift-common108"
OUTPUT = SOURCE / "reports/raw/joern-common-v2/current108-v092-03"
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"


def read(path):
    return json.loads(path.read_text())


def ref(path):
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write_new(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main():
    audit_path = REPORT / "postcapture-audit-01.json"
    costs_path = REPORT / "case-invocation-costs-01.json"
    assert not audit_path.exists() and not costs_path.exists()
    plan = read(REPORT / "supplement-plan-01.json")
    start = read(REPORT / "campaign-start.json")
    attempt_path = REPORT / "attempts/joern-swift-common108/attempt-01/terminal.json"
    attempt = read(attempt_path)
    terminal = read(REPORT / "campaign-terminal.json")
    comparison = attempt["reconciliation"]["frozen_report_comparison"]
    assert terminal["execution_status"] == "stopped-fail-closed"
    assert type(attempt["exit_code"]) is int and attempt["exit_code"] == 0
    assert attempt["timed_out"] is False and attempt["capacity_loss"] is None
    assert attempt["resource_baseline_after_dispatch"]["unchanged"] is True
    assert comparison["status"] == "mismatch" and len(comparison["mismatches"]) == 12
    run = read(OUTPUT / "run.json")
    raw_by_id = {}
    command_refs = [ref(OUTPUT / "identity/version.command.json")]
    for row in run["results"]:
        path = SOURCE / row["raw"]["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["raw"]["sha256"]
        raw = read(path)
        raw_by_id[row["case_id"]] = raw
        for command in raw["commands"]:
            path = SOURCE / command["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == command["sha256"]
            command_refs.append(ref(path))
    mismatches = []
    checked = collections.Counter()
    for binding, descriptor in zip(plan["frozen_report_bindings"], attempt["reconciliation"]["reports"]):
        blob = subprocess.check_output(["git", "show", RELEASE + ":" + binding["git_path"]], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == binding["sha256"]
        frozen = {row["case_id"]: row for row in json.loads(blob)["results"]}
        actual = read(SOURCE / descriptor["derived_path"])
        for row in actual["results"]:
            case_id = row["case_id"]
            raw = raw_by_id[case_id]
            checked["attempted" if raw["executed"] else "declined"] += 1
            for field in ("outcome", "diagnostics", "witness_checkpoints", "source_anchors", "sink_anchors"):
                if row[field] != frozen[case_id][field]:
                    assert not raw["executed"] and raw["state"] == "unsupported" and field == "diagnostics"
                    mismatches.append({"case_id": case_id, "field": field,
                                       "expected": frozen[case_id][field], "actual": row[field]})
    assert checked == {"attempted": 96, "declined": 12} and len(mismatches) == 12
    identities = {(start["supervisor_pid"], start["supervisor_start_identity"])}
    missing_identities = []
    for command_ref in command_refs:
        command = read(ROOT / command_ref["path"])
        assert type(command["exit_status"]) is int and command["exit_status"] == 0
        assert command["timed_out"] is False and command["cleanup_status"] == "tracked-processes-stopped"
        if not command["tracked_descendants"]:
            missing_identities.append(command_ref)
        for row in command["tracked_descendants"]:
            identities.add((row["pid"], row["start_identity"]))
    for row in attempt["process_ownership"]["tracked_processes"]:
        identities.add((row["pid"], row["start_identity"]))
    with campaign.legacy.core._exclusive_lock():
        snapshot = subprocess.run(["ps", "-axo", "pid="], capture_output=True, text=True, check=True)
        tracker = campaign.legacy.core._process_tracker()
        observations = []
        for pid, birth in sorted(identities):
            observation = closed.observe_stopped(pid, birth, tracker._start_identity,
                                                 run=lambda *args, **kwargs: snapshot)
            observation.pop("raw_unfiltered_pid_table")
            observations.append(observation)
    common = {"immutable_release": RELEASE, "campaign_id": "20261122-08",
              "source_attempt_terminal": ref(attempt_path), "original_acceptance_preserved": "failed",
              "accepted_measurements": 0, "certified_measurements": 0,
              "full_model_qualification": False, "publication_eligible": False,
              "retrospective": True, "new_analyzer_invocations": 0}
    write_new(costs_path, {"schema": "v092-retained-swift-invocation-costs/v1", **common,
                           "captured_attempt_cost_rows": 96, "unsupported_no_invocation_rows": 12,
                           "rows": comparison["case_timing_rows"]})
    audit = {"schema": "v092-swift-postcapture-acceptance-audit/v1", **common,
             "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "status": "acceptance-failure-retained-diagnostic-costs-only",
             "attempted_rows_matching_all_frozen_semantic_fields": 96,
             "declined_rows_matching_outcome_checkpoints_anchors": 12,
             "diagnostic_mismatches": mismatches, "analysis_phase_commands": len(command_refs) - 1,
             "version_commands": 1, "wrapper_seconds": attempt["elapsed_seconds"],
             "recorded_process_identities": len(identities), "process_observations": observations,
             "commands_with_no_recorded_identity": missing_identities,
             "raw_unfiltered_pid_table": snapshot.stdout, "signals_sent_by_audit": [],
             "serial_lock_available": True, "descendant_containment": "unproven",
             "case_costs": ref(costs_path), "procedure": ref(Path(__file__).resolve())}
    write_new(audit_path, audit)
    print(json.dumps({"status": audit["status"], "attempt_costs": 96,
                      "declines": 12, "diagnostic_mismatches": 12,
                      "recorded_process_identities": len(identities),
                      "commands_with_no_recorded_identity": len(missing_identities)}))


if __name__ == "__main__":
    main()
