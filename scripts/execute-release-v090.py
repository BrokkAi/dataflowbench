#!/usr/bin/env python3
"""Run the reviewed matrix serially; resume only fully verified completed groups."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def completed_groups(root, contract_path):
    path = root/'scripts/verify-release-attempt-v090.py'
    spec = importlib.util.spec_from_file_location('attempt_verifier', path)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    ledger = root/'reports/releases/v0.9.0/ledger-v1.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    done = set()
    for row in rows:
        if row['group_id'] in done:
            raise ValueError('multiple selected attempts for group; explicit review required')
        if row.get('status') != 'completed':
            raise ValueError('retained failed/incomplete attempt requires explicit review: ' + row['attempt_id'])
        receipt = Path('reports/releases/v0.9.0/attempts')/row['attempt_id']/'completed.json'
        verifier.verify_attempt(root, receipt, contract_path)
        done.add(row['group_id'])
    started = root/'reports/releases/v0.9.0/attempts'
    if started.exists():
        for directory in started.iterdir():
            if directory.is_dir() and not (directory/'completed.json').is_file():
                raise ValueError('started attempt lacks completion: ' + directory.name)
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--contract', default='reports/releases/v0.9.0/execution-v1/contract.json')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    contract = json.loads((root/args.contract).read_text())
    if not args.execute:
        print(json.dumps({'mode': 'list-only', 'groups': [g['id'] for g in contract['groups']], 'execution_authorized': contract.get('execution_authorized') is True}, indent=2))
        return
    if contract.get('execution_authorized') is not True or contract.get('unresolved'):
        raise ValueError('matrix has not passed final executable-plan review')
    done = completed_groups(root, args.contract)
    for group in contract['groups']:
        if group['id'] in done:
            continue
        command = [sys.executable, str(root/'scripts/run-release-group-v090.py'), '--root', str(root), '--contract', args.contract, '--group', group['id'], '--execute']
        subprocess.run(command, cwd=root, check=True)
        done = completed_groups(root, args.contract)
        if group['id'] not in done:
            raise ValueError('group did not produce verified completion: ' + group['id'])
        print(json.dumps({'completed_groups': len(done), 'total_groups': len(contract['groups'])}), flush=True)


if __name__ == '__main__':
    main()
