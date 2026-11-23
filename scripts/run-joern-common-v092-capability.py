#!/usr/bin/env python3
"""Versioned v0.9.2 Joern Swift qualification and capability-bound execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joern_normal_runner_v092_capability as runner
import joern_normal_reports_v092_capability as reports


def review_controls(root: Path, plan_path: str, run_path: Path, output_path: Path) -> dict:
    """Replay a completed control capture without launching analyzer processes."""
    import joern_diagnostic_admission_v092_capability as admission
    import swift_common_population_v2 as common

    root = Path(root).resolve()
    run_path = run_path.resolve()
    output_path = output_path.resolve()
    runner.require(run_path.is_file() and run_path.resolve().is_relative_to(root),
                   "Joern control run must remain inside the repository")
    runner.require(output_path.is_relative_to(root / runner.QUALIFICATION_OUTPUT_ROOT),
                   "Joern diagnostic review must stay under the v0.9.2-03 preparation root")
    runner.require(not output_path.exists() and not output_path.is_symlink(),
                   "Joern diagnostic review output already exists")

    plan, _unused, context = runner.validate_plan(
        root, plan_path, allow_qualification_pending=True
    )
    run = runner.read(run_path)
    runner.require(
        run.get("control_plan_sha256") == plan["qualification_control_plan"]["sha256"] and
        run.get("execution_plan_projection_sha256") == plan["qualification_control_projection_sha256"],
        "Joern control run does not bind the exact v0.9.2-03 pending plan",
    )
    _population, common_rows, _swift_rows, cases, _digest = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in common_rows}
    engine = context["engine"]
    runner._set_engine_query_root(engine, plan["query_root"])
    observations, phase_count = runner._replay_control_run(
        root, plan, context["control"], run, cases, engine, case_paths=case_paths
    )
    runner.require(phase_count == 36, "Joern diagnostic review requires all 36 replayed phase invocations")
    report = admission.replay_admission(
        root, plan, context["control"], run, observations, cases, case_paths
    )
    report["control_run"] = runner.reference(root, run_path)
    reviewer_path = root / "scripts/joern_diagnostic_admission_v092_capability.py"
    report["reviewer"] = {
        "path": "scripts/joern_diagnostic_admission_v092_capability.py",
        "sha256": runner.sha(reviewer_path),
    }
    report["control_plan"] = plan["qualification_control_plan"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    verify = sub.add_parser("verify-plan")
    verify.add_argument("--plan", required=True)
    controls = sub.add_parser("controls")
    controls.add_argument("--plan", required=True)
    controls.add_argument("--output", type=Path, required=True)
    review = sub.add_parser("review-controls")
    review.add_argument("--plan", required=True)
    review.add_argument("--run", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    execute = sub.add_parser("execute")
    execute.add_argument("--plan", required=True)
    execute.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = runner.ROOT.resolve()

    if args.mode == "verify-plan":
        plan, evidence, _ = runner.validate_plan(root, args.plan)
        print(json.dumps({
            "mode": "preflight",
            "group_id": runner.GROUP_ID,
            "tool_version": runner.VERSION,
            "qualification_status": evidence["status"],
            "case_count": len(plan["cases"]),
            "scored_activation": False,
        }, indent=2))
        return 0

    if args.mode == "controls":
        run = runner.run_controls(root, args.plan, args.output)
        summary = runner.summarize_control_capture(run)
        summary["scored_activation"] = False
        print(json.dumps(summary, indent=2))
        return 0

    if args.mode == "review-controls":
        result = review_controls(root, args.plan, args.run, args.output)
        print(json.dumps({
            "status": result["status"],
            "diagnostic_execution_eligible": result["diagnostic_execution_eligible"],
            "full_model_qualification": result["full_model_qualification"],
            "scored_activation": result["scored_activation"],
            "opaque_case_arm_count": result["opaque_case_arm_count"],
        }, indent=2))
        return 0

    run = runner.execute(root, args.plan, args.output)
    output = args.output.resolve() / "normal"
    written = reports.export(root, args.plan, run, output)
    print(json.dumps({
        "status": "complete" if len(run.get("results", [])) == 108 else "incomplete",
        "results": len(run.get("results", [])),
        "report_partitions": len(written),
        "scored_activation": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
