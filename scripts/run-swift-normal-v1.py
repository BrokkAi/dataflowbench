#!/usr/bin/env python3
"""Prepare a pinned CodeQL normal-report plan or execute a reserved one."""
import argparse
from pathlib import Path
from swift_normal_runner_v1 import ROOT, prepare, execute, check_queries, read, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    create = commands.add_parser('prepare')
    create.add_argument('--directory', type=Path, required=True)
    for name in ['repair', 'codeql', 'compiler', 'sdk']:
        create.add_argument('--' + name, required=True)
    check = commands.add_parser('check-queries')
    check.add_argument('--plan', required=True)
    check.add_argument('--output', type=Path, required=True)
    run = commands.add_parser('execute')
    run.add_argument('--plan', required=True)
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--reservation', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        destination = args.directory.resolve()
        require(destination.is_relative_to(ROOT / 'adapters'), 'plan belongs under adapters')
        prepare(ROOT, destination, {key: getattr(args, key) for key in ['repair', 'codeql', 'compiler', 'sdk']})
        print('Prepared only; no processes launched and capacity remains unreserved.')
    elif args.mode == 'check-queries':
        check_queries(ROOT, args.plan, args.output.resolve())
    else:
        execute(ROOT, args.plan, args.output.resolve(), read(args.reservation))


if __name__ == '__main__':
    main()
