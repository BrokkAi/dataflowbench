#!/usr/bin/env python3
"""Replay fresh controls and create new qualification metadata, without analyzers."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import joern_normal_runner_v092_relocated as runner
import v092_relocated_qualification as qualification

BASE = Path("reports/timing/v0.9.2/preparation-20261122-joern-swift-01/qualification")
RUN = BASE / "control-attempt-01/run.json"
REVIEW = BASE / "control-attempt-01-diagnostic-admission-review.json"
RECEIPT = BASE / "control-attempt-01/qualification-receipt-01.json"


def write_new(relative: Path | str, value: dict) -> None:
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    for path in (REVIEW, RECEIPT, Path(runner.FINAL_EXECUTION_PLAN_PATH)):
        if (ROOT / path).exists() or (ROOT / path).is_symlink():
            raise RuntimeError(f"refusing to replace qualification metadata: {path}")
    pending, _evidence, _context = runner.validate_plan(
        ROOT, runner.PENDING_EXECUTION_PLAN_PATH, allow_qualification_pending=True)
    run = runner.read(ROOT / RUN)
    spec = importlib.util.spec_from_file_location(
        "relocated_qualification_cli", ROOT / "scripts/run-joern-common-v092-relocated.py")
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
    main()
