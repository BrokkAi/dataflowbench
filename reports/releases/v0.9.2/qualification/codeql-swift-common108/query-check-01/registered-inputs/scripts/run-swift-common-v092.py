#!/usr/bin/env python3
"""Version-isolated entry point for the v0.9.2 common-108 CodeQL lane."""

import argparse
import json
from pathlib import Path

import swift_normal_runner_v092 as runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    verify = commands.add_parser("verify-plan")
    verify.add_argument("--plan", required=True)
    checks = commands.add_parser("check-queries")
    checks.add_argument("--plan", required=True)
    checks.add_argument("--output", type=Path, required=True)
    execute = commands.add_parser("execute")
    execute.add_argument("--plan", required=True)
    execute.add_argument("--query-receipt", required=True)
    execute.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = runner.ROOT.resolve()
    if args.mode == "verify-plan":
        plan, qualification, _ = runner.validate_plan(root, args.plan)
        print(json.dumps({
            "mode": "preflight",
            "engine": "codeql",
            "release_group_id": runner.GROUP_ID,
            "plan_sha256": runner.sha(root / args.plan),
            "qualification_status": qualification["status"],
            "case_count": len(plan["cases"]),
            "scored_activation": False,
        }, indent=2))
        return 0

    if args.mode == "check-queries":
        receipt = runner.check_queries(root, args.plan, args.output)
        print(json.dumps({"status": receipt["status"], "queries": len(receipt["queries"])}))
        return 0

    run = runner.execute(root, args.plan, args.query_receipt, args.output)
    print(json.dumps({"status": "complete" if len(run.get("results", [])) == 108 else "incomplete", "results": len(run.get("results", [])), "scored_activation": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
