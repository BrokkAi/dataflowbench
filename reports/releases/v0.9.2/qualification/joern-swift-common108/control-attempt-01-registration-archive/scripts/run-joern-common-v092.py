#!/usr/bin/env python3
"""Fresh v0.9.2 common-108 Joern qualification and execution entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joern_normal_runner_v092 as runner
import joern_normal_reports_v092 as reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    verify = sub.add_parser("verify-plan")
    verify.add_argument("--plan", required=True)
    controls = sub.add_parser("controls")
    controls.add_argument("--plan", required=True)
    controls.add_argument("--output", type=Path, required=True)
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
        print(json.dumps({
            "status": "complete" if len(run.get("records", [])) == 12 else "incomplete",
            "case_arms": len(run.get("records", [])),
            "phase_invocations": run.get("phase_invocation_count"),
            "scored_activation": False,
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
