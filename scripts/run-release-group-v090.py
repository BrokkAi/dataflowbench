#!/usr/bin/env python3
"""Validate or run one reviewed release group; never choose a retry automatically."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from release_attempt_v090 import AttemptError, SERIAL_LOCK_PATH, run_group, validate_group


def launch_gate(root, contract, group):
    if contract.get('unresolved'):
        raise AttemptError('execution contract still has unresolved prerequisites')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if contract.get('harness_commit') != head:
        raise AttemptError('execution checkout is not the exact reviewed harness')
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', 'HEAD', '--', 'src', 'cases', 'populations',
         'adapters', 'scripts', 'Cargo.toml', 'Cargo.lock'], cwd=root, text=True)
    if changed.strip():
        raise AttemptError('execution source differs from the reviewed harness: ' + changed.strip())
    # A single designated root per group prevents a fresh checkout resetting
    # the recorder-local two-attempt bound. The separate preparer reserves it.
    designated = contract.get('execution_roots', {}).get(group['id'])
    if designated is None:
        designated = contract.get('control_execution_roots', {}).get(group['id'])
    if not designated or Path(designated).resolve() != root:
        raise AttemptError('group execution root is not explicitly designated')
    runner = contract['tools']['runner']
    if hashlib.sha256(Path(runner['path']).read_bytes()).hexdigest() != runner.get('sha256'):
        raise AttemptError('runner binary identity mismatch')
    provenance = contract.get('runner_build', {})
    if provenance.get('source_commit') != head or provenance.get('binary_sha256') != runner['sha256']:
        raise AttemptError('runner build provenance mismatch')
    from release_runtime_inventory_v090 import verify
    trees = contract.get('runtime_trees')
    if not trees:
        raise AttemptError('runtime tree identities missing')
    for reference in trees:
        raw = (root / reference['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference['sha256']:
            raise AttemptError('runtime inventory digest mismatch')
        verify(json.loads(raw))
    reservation = contract.get('resource_reservation', {})
    if reservation.get('exclusive_analyzer_slot') is not True or reservation.get('expires_at_unix_seconds', 0) <= time.time():
        raise AttemptError('fresh exclusive resource reservation required')
    budget = contract['resource_budget']
    if shutil.disk_usage(root).free < budget['minimum_launch_free_gib'] * 1024**3:
        raise AttemptError('launch capacity below reviewed floor')
    used = 0
    owned_roots = set(contract['execution_roots'].values()) | set(contract.get('control_execution_roots', {}).values())
    for owned_root in owned_roots:
        for category in ('attempts', 'control-attempts'):
            retained = Path(owned_root) / 'reports/releases/v0.9.0' / category
            if retained.exists():
                used += sum(p.stat().st_size for p in retained.rglob('*') if p.is_file())
    window_start = reservation.get('window_started_at_unix_seconds')
    if not isinstance(window_start, (int, float)) or window_start > time.time():
        raise AttemptError('recorded release window start required')
    if time.time() + group['deadline_seconds'] > window_start + contract['total_wall_budget_seconds']:
        raise AttemptError('release wall budget cannot accommodate another group')
    if used >= budget['proposed_total_retention_ceiling_gib'] * 1024**3:
        raise AttemptError('retention budget exhausted')
    processes = subprocess.check_output(['ps', '-axo', 'pid=,comm='], text=True)
    heavy = []
    for line in processes.splitlines():
        fields = line.split(None, 1)
        if len(fields) == 2 and Path(fields[1]).name in {'cargo', 'rustc', 'hyperfine', 'codeql', 'joern', 'java'}:
            heavy.append(line.strip())
    if heavy:
        raise AttemptError('contending build/analyzer processes: ' + '; '.join(heavy))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--contract', default='reports/releases/v0.9.0/execution-v1/contract.json')
    parser.add_argument('--group', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    result = validate_group(root, args.contract, args.group, require_authorized=args.execute)
    if not args.execute:
        print(json.dumps({'mode': 'validation-only', **result}, sort_keys=True))
        return 0
    contract = json.loads((root / args.contract).read_text())
    group = next(g for g in contract['groups'] if g['id'] == args.group)
    # Lock spans gate, native process lifetime, capture and ledger append.
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(SERIAL_LOCK_PATH, flags, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AttemptError('another release group owns the analyzer slot') from exc
        launch_gate(root, contract, group)
        row = run_group(root, args.contract, args.group, argv=group['argv'], env=group['environment'])
    print(json.dumps({'group_id': row['group_id'], 'attempt_id': row['attempt_id'], 'status': row['status']}, sort_keys=True))
    return 0 if row['status'] == 'completed' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AttemptError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
