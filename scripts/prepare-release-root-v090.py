#!/usr/bin/env python3
"""Prepare one isolated, shared execution checkout for the entire serial matrix.

Only declared output roots in this newly created checkout are removed. Source
history and source working files are never changed. Repeated destinations are
rejected, preserving one central attempt counter for all groups and retries.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

SHA = re.compile(r'^[0-9a-f]{40}$')


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args])


def safe_relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or str(path) != value:
        raise ValueError('unsafe repository path: ' + str(value))
    return path


def prepare_root(source, destination, plan_commit, contract_path):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if destination.exists() or destination.is_symlink():
        raise ValueError('execution destination already exists; attempts must not be reset')
    if not SHA.fullmatch(plan_commit):
        raise ValueError('exact reviewed plan commit required')
    safe_relative(contract_path)
    raw_contract = git(source, 'show', plan_commit + ':' + contract_path)
    contract = json.loads(raw_contract)
    harness = contract.get('harness_commit', '')
    if not SHA.fullmatch(harness):
        raise ValueError('exact merged harness commit required')
    subprocess.run(['git', '-C', str(source), 'merge-base', '--is-ancestor', harness, plan_commit], check=True)
    groups = contract['groups']
    roots = contract.get('execution_roots', {})
    if set(roots) != {g['id'] for g in groups} or any(Path(p).absolute() != destination for p in roots.values()):
        raise ValueError('all serial groups must designate this one central execution root')
    # Read every bound input from the explicit reviewed commit before mutation.
    overlay = {contract_path: raw_contract}
    for relative, digest in contract['input_identities'].items():
        safe_relative(relative)
        data = git(source, 'show', plan_commit + ':' + relative)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('reviewed input digest mismatch: ' + relative)
        if not relative.startswith('reports/releases/v0.9.0/execution-v1/'):
            original = git(source, 'show', harness + ':' + relative)
            if original != data:
                raise ValueError('reviewed overlay changes immutable harness input: ' + relative)
        overlay[relative] = data
    output_roots = sorted({r for group in groups for r in group['output_roots']})
    for relative in output_roots:
        path = safe_relative(relative)
        if path.parts[0] != 'reports' or len(path.parts) < 2:
            raise ValueError('output must be a narrow reports path')
        for bound in overlay:
            other = PurePosixPath(bound)
            if path == other or path in other.parents or other in path.parents:
                raise ValueError('output overlaps registered input')
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(source), str(destination)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', '-C', str(destination), 'checkout', '--detach', harness], check=True, stdout=subprocess.DEVNULL)
    removed = []
    for relative in output_roots:
        path = destination / relative
        current = destination
        for part in PurePosixPath(relative).parts:
            current /= part
            if current.is_symlink():
                raise ValueError('symlink in isolated output path')
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(relative)
        elif path.exists():
            path.unlink()
            removed.append(relative)
    for relative, data in overlay.items():
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError('overlay escapes isolated root')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    receipt = {'schema': 'release-root-preparation/v1', 'source': str(source),
               'execution_root': str(destination), 'harness_commit': harness,
               'plan_commit': plan_commit, 'contract_path': contract_path,
               'contract_sha256': hashlib.sha256(raw_contract).hexdigest(),
               'removed_isolated_output_roots': removed,
               'input_identities': contract['input_identities'],
               'source_modified': False, 'automatic_retry': False}
    target = destination/'reports/releases/v0.9.0/root-preparation.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--plan-commit', required=True)
    p.add_argument('--contract', default='reports/releases/v0.9.0/execution-v1/contract.json')
    args = p.parse_args()
    print(json.dumps(prepare_root(args.source, args.destination, args.plan_commit, args.contract), sort_keys=True))


if __name__ == '__main__':
    main()
