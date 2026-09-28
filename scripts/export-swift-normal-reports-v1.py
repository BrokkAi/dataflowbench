#!/usr/bin/env python3
"""Export a newly registered Swift run; never execute an analyzer."""
import argparse
import json
from pathlib import Path
from swift_normal_reports_v1 import ROOT, export, read, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, help='Repository-relative new plan')
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New directory; never overwritten')
    args = parser.parse_args()
    bundle = export(ROOT, args.plan, read(args.run))
    require(not args.output.exists(), 'output already exists; preserve prior attempts')
    args.output.mkdir(parents=True, exist_ok=False)
    audit = bundle['audit']
    audit['reports'] = []
    for index, (group, report) in enumerate(sorted(bundle['reports'].items())):
        name = f'swift-normal-{index:03}.json'
        (args.output / name).write_text(json.dumps(report, indent=2) + '\n')
        audit['reports'].append({'file': name, 'partition': list(group), 'case_count': len(report['results'])})
    (args.output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(f"Exported {len(audit['results'])} coverage rows; scoring unavailable; no freeze created")


if __name__ == '__main__':
    main()
