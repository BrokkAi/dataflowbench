#!/usr/bin/env python3
"""Replay fresh controls and create new qualification metadata, without analyzers."""
from __future__ import annotations

import copy
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import joern_normal_runner_v092_capability as runner
import v092_capability_qualification as qualification

BASE = Path("reports/timing/v0.9.2/preparation-20261122-joern-swift-01/capability-qualification")
RUN = BASE / "control-attempt-03/run.json"
REVIEW = BASE / "control-attempt-03-diagnostic-admission-review.json"
RECEIPT = BASE / "control-attempt-03/qualification-receipt-01.json"
SUPERVISION = Path("reports/timing/v0.9.2/preparation-20261122-joern-swift-01/capability-control-supervision-03/terminal.json")
OWNERSHIP = Path("reports/timing/v0.9.2/preparation-20261122-joern-swift-01/capability-post-control-ownership-01.json")


def write_new(relative: Path | str, value: dict) -> None:
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main(expected_ownership_sha256: str) -> None:
    for path in (REVIEW, RECEIPT, Path(runner.FINAL_EXECUTION_PLAN_PATH)):
        if (ROOT / path).exists() or (ROOT / path).is_symlink():
            raise RuntimeError(f"refusing to replace qualification metadata: {path}")
    pending, _evidence, _context = runner.validate_plan(
        ROOT, runner.PENDING_EXECUTION_PLAN_PATH, allow_qualification_pending=True)
    if (len(expected_ownership_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_ownership_sha256)
            or runner.sha(ROOT / OWNERSHIP) != expected_ownership_sha256):
        raise RuntimeError("ownership receipt differs from the independently observed successful audit")
    terminal = runner.read(ROOT / SUPERVISION)
    ownership = runner.read(ROOT / OWNERSHIP)
    elapsed = terminal.get("elapsed_seconds")
    if (terminal.get("schema") != "v092-joern-capability-controls-supervision-terminal/v1"
            or terminal.get("status") != "captured-needs-replay"
            or type(terminal.get("exit_code")) is not int or terminal["exit_code"] != 0
            or terminal.get("timed_out") is not False
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed)
            or not 0 <= elapsed <= 900
            or "capacity_loss" not in terminal or terminal["capacity_loss"] is not None
            or "changed_protected_inputs" in terminal
            or "changed_static_resource_baseline" in terminal
            or terminal.get("resource_baseline_status") != "unchanged"):
        raise RuntimeError("fresh control supervision did not pass resource and identity gates")
    if (ownership.get("schema") != "v092-joern-capability-post-control-ownership/v1"
            or ownership.get("status") != "passed"
            or type(ownership.get("command_records")) is not int or ownership["command_records"] != 37
            or type(ownership.get("recorded_process_identities")) is not int
            or ownership["recorded_process_identities"] <= 0
            or ownership.get("serial_lock_available") is not True
            or ownership.get("same_identities_still_alive") != []
            or ownership.get("signals_sent_by_audit") != []
            or ownership.get("supervision_terminal") != runner.reference(ROOT, ROOT / SUPERVISION)
            or ownership.get("control_run") != runner.reference(ROOT, ROOT / RUN)):
        raise RuntimeError("fresh control process identities have not been observed stopped")
    run = runner.read(ROOT / RUN)
    if run.get("phase_invocation_count") != 36 or len(run.get("records", [])) != 12:
        raise RuntimeError("fresh qualification requires all twelve arms and 36 phases")
    expected_commands = [runner.reference(ROOT, ROOT / BASE / "control-attempt-03/version.command.json")]
    for row in run["records"]:
        raw = runner.read(runner.bound_file(ROOT, row.get("raw")))
        commands = raw.get("commands")
        if not isinstance(commands, list) or len(commands) != 3:
            raise RuntimeError("fresh qualification arm lacks three command references")
        for ref in commands:
            runner.bound_file(ROOT, ref)
            expected_commands.append(ref)
    audited_commands = ownership.get("command_refs")
    if (not isinstance(audited_commands, list) or len(audited_commands) != 37
            or len({ref["path"] for ref in expected_commands}) != 37
            or sorted(audited_commands, key=lambda ref: ref["path"])
            != sorted(expected_commands, key=lambda ref: ref["path"])):
        raise RuntimeError("ownership audit does not cover the exact control/version commands")
    spec = importlib.util.spec_from_file_location(
        "capability_qualification_cli", ROOT / "scripts/run-joern-common-v092-capability.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    review = cli.review_controls(ROOT, runner.PENDING_EXECUTION_PLAN_PATH, ROOT / RUN, ROOT / REVIEW)
    if (review.get("status") != "measurement-with-known-limits"
            or review.get("diagnostic_execution_eligible") is not True
            or review.get("full_model_qualification") is not False
            or review.get("scored_activation") is not False):
        raise RuntimeError("fresh controls did not establish the exact diagnostic-only admission")
    run_ref = runner.reference(ROOT, ROOT / RUN)
    review_ref = runner.reference(ROOT, ROOT / REVIEW)
    receipt = {
        "schema": "analyzer-qualification-receipt/v092",
        "status": "measurement-with-known-limits",
        "execution_eligible": True,
        "diagnostic_execution_eligible": True,
        "full_model_qualification": False,
        "scored_activation": False,
        "group_id": runner.GROUP_ID,
        "groups": [runner.GROUP_ID],
        "population_sha256": pending["population_sha256"],
        "fixture_revision": pending["fixture_revision"],
        "identity": pending["identity"],
        "identity_components": qualification.expected_identity_components(pending),
        "execution_plan_projection_sha256": qualification.plan_projection_sha256(pending),
        "control_run": run_ref,
        "supervision_terminal": runner.reference(ROOT, ROOT / SUPERVISION),
        "closed_process_ownership": runner.reference(ROOT, ROOT / OWNERSHIP),
        "diagnostic_admission_review": review_ref,
        "dimensions": {
            "common108_controls": {
                "status": "measurement-with-known-limits", "case_count": 6,
                "case_arm_count": 12, "phase_invocation_count": run["phase_invocation_count"],
                "control_run": run_ref, "strict_assessment": run["assessment"],
                "full_model_qualification": False,
            },
            "joern_diagnostic_admission": review_ref,
        },
        "finalization_procedure": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    write_new(RECEIPT, receipt)
    final = copy.deepcopy(pending)
    final.update(status="execution-eligible", execution_eligible=True,
                 diagnostic_execution_eligible=True,
                 fresh_qualification=runner.reference(ROOT, ROOT / RECEIPT))
    if qualification.plan_projection_sha256(final) != qualification.plan_projection_sha256(pending):
        raise RuntimeError("final qualification changed the prospective control projection")
    # Replay the receipt before creating the final plan's fixed, exclusive path.
    _population, rows, _swift_rows, cases, _digest = runner.common.load_common_population(ROOT)
    case_paths = {row["id"]: ROOT / row["path"] for row in rows}
    runner._validate_qualification(ROOT, final, cases, case_paths)
    write_new(runner.FINAL_EXECUTION_PLAN_PATH, final)
    runner.validate_plan(ROOT, runner.FINAL_EXECUTION_PLAN_PATH)
    print(json.dumps({"status": "diagnostic-execution-eligible", "full_model_qualification": False,
                      "scored_activation": False, "plan": runner.FINAL_EXECUTION_PLAN_PATH,
                      "receipt": str(RECEIPT)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ownership-sha256", required=True)
    main(parser.parse_args().ownership_sha256)
