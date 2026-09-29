#!/usr/bin/env python3
"""Versioned common-population wrapper for the unchanged CodeQL v1 engine."""
import argparse
from pathlib import Path

import swift_common_population_v2 as common

ROOT = common.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("--directory", type=Path, required=True)
    for name in ("repair", "codeql", "compiler", "sdk"):
        create.add_argument("--" + name, required=True)
    check = commands.add_parser("check-queries")
    check.add_argument("--plan", required=True)
    check.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("execute")
    run.add_argument("--plan", required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--reservation", type=Path, required=True)
    args = parser.parse_args()

    if args.mode == "prepare":
        destination = args.directory.resolve()
        common.require(destination.is_relative_to(ROOT / "adapters"), "plan belongs under adapters")
        common.prepare(ROOT, destination, {name: getattr(args, name) for name in ("repair", "codeql", "compiler", "sdk")}, "codeql", "scripts/run-swift-common-v2.py")
        print("Prepared only; common 1108 population and exact Swift 108 projection are bound. No analyzer was launched.")
    elif args.mode == "check-queries":
        common.check_queries(ROOT, args.plan, args.output.resolve())
    else:
        common.execute(ROOT, args.plan, args.output.resolve(), common.read(args.reservation), "codeql")


if __name__ == "__main__":
    main()
