#!/usr/bin/env python3
"""Versioned common-population wrapper for the unchanged Joern v1 engine."""
import argparse
from pathlib import Path

import swift_common_population_v2 as common

ROOT = common.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("--directory", type=Path, required=True)
    for name in ("joern", "java-home", "compiler", "sdk"):
        create.add_argument("--" + name, required=True)
    for mode in ("controls", "execute"):
        run = commands.add_parser(mode)
        run.add_argument("--plan", required=True)
        run.add_argument("--output", type=Path, required=True)
        run.add_argument("--reservation", type=Path, required=True)
        if mode == "controls":
            run.add_argument("--controls", required=True)
    args = parser.parse_args()

    if args.mode == "prepare":
        destination = args.directory.resolve()
        common.require(destination.is_relative_to(ROOT / "adapters"), "plan belongs under adapters")
        common.prepare(ROOT, destination, {
            "joern": args.joern,
            "java_home": args.java_home,
            "compiler": args.compiler,
            "sdk": args.sdk,
        }, "joern", "scripts/run-joern-common-v2.py")
        print("Prepared only; common 1108 population and exact Swift 108 projection are bound. No analyzer was launched.")
    elif args.mode == "controls":
        common.controls(ROOT, args.plan, args.controls, args.output.resolve(), common.read(args.reservation))
    else:
        common.execute(ROOT, args.plan, args.output.resolve(), common.read(args.reservation), "joern")


if __name__ == "__main__":
    main()
