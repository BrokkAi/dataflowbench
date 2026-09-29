#!/usr/bin/env python3
"""Prepare and run isolated controls serially; never retry an incomplete control."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

CONTRACT = 'reports/releases/v0.9.0/execution-v1/contract.json'


def reviewed_inventory(source, plan_commit, contract_path):
    if not re.fullmatch(r'[0-9a-f]{40}', plan_commit):
        raise ValueError('exact reviewed plan commit required')
    def read(relative):
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('unsafe reviewed input path')
        return subprocess.check_output(['git', '-C', str(source), 'show', plan_commit + ':' + relative])
    raw = read(contract_path)
    contract = json.loads(raw)
    reference = contract['control_inventory']
    inventory_raw = read(reference['path'])
    if hashlib.sha256(inventory_raw).hexdigest() != reference['sha256']:
        raise ValueError('control inventory differs from reviewed commit')
    inventory = json.loads(inventory_raw)
    controls = inventory['controls']
    ids = [c['id'] for c in controls]
    if len(ids) != len(set(ids)) or set(ids) != set(contract['control_execution_roots']):
        raise ValueError('control membership and designated roots differ')
    return contract, controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--plan-commit', required=True)
    parser.add_argument('--contract', default=CONTRACT)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    contract, controls = reviewed_inventory(source, args.plan_commit, args.contract)
    if not args.execute:
        print(json.dumps({'mode': 'list-only', 'controls': [c['id'] for c in controls],
                          'execution_authorized': contract.get('execution_authorized') is True}, indent=2))
        return
    if contract.get('execution_authorized') is not True or contract.get('unresolved'):
        raise ValueError('controls have not passed final executable-plan review')
    for control in controls:
        root = Path(contract['control_execution_roots'][control['id']])
        # Any existing checkout requires explicit receipt review. Automatic
        # reconstruction could otherwise discard a failed run or reset attempts.
        if root.exists():
            raise ValueError('existing control root requires explicit resume review: ' + str(root))
        subprocess.run([sys.executable, str(source/'scripts/prepare-release-root-v090.py'),
                        '--source', str(source), '--destination', str(root),
                        '--plan-commit', args.plan_commit, '--contract', args.contract,
                        '--control', control['id']], check=True)
        subprocess.run([sys.executable, str(root/'scripts/run-release-control-v090.py'),
                        '--root', str(root), '--contract', args.contract,
                        '--control', control['id'], '--execute'], check=True)
        print(json.dumps({'completed_control': control['id']}), flush=True)


if __name__ == '__main__':
    main()
