#!/usr/bin/env python3
"""Validate or capture one reviewed non-report control under the shared host lock."""
from __future__ import annotations
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path

from release_attempt_v090 import AttemptError, SERIAL_LOCK_PATH


def launch_control(root, contract_path, control_id, *, execute=False):
    from release_control_attempt_v090 import run_control, validate_control
    root = Path(root).resolve()
    validate_control(root, contract_path, control_id, require_authorized=execute)
    if not execute:
        return {'mode': 'validation-only', 'control_id': control_id}
    contract = json.loads((root / contract_path).read_text())
    inventory = json.loads((root / contract['control_inventory']['path']).read_text())
    control = next(c for c in inventory['controls'] if c['id'] == control_id)
    spec = importlib.util.spec_from_file_location('release_launch_gate', root / 'scripts/run-release-group-v090.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(SERIAL_LOCK_PATH, flags, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AttemptError('another release operation owns the analyzer slot') from exc
        gate.launch_gate(root, contract, control)
        return run_control(root, contract_path, control_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--contract', default='reports/releases/v0.9.0/execution-v1/contract.json')
    parser.add_argument('--control', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    result = launch_control(args.root, args.contract, args.control, execute=args.execute)
    print(json.dumps(result, sort_keys=True))
    return 0 if not args.execute or result.get('status') == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
