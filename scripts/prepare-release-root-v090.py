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


def prepare_control_root(source, destination, plan_commit, contract_path, control_id):
    """Prepare a fresh execution checkout for exactly one reviewed control."""
    source = Path(source).resolve()
    requested_destination = Path(destination).expanduser().absolute()
    if requested_destination.exists() or requested_destination.is_symlink():
        raise ValueError('execution destination already exists; attempts must not be reset')
    destination = requested_destination.resolve()
    if not SHA.fullmatch(plan_commit):
        raise ValueError('exact reviewed plan commit required')
    safe_relative(contract_path)
    if not contract_path.startswith('reports/releases/v0.9.0/execution-v1/'):
        raise ValueError('control contract must be an execution-v1 overlay')
    raw_contract = git(source, 'show', plan_commit + ':' + contract_path)
    contract = json.loads(raw_contract)
    harness = contract.get('harness_commit', '')
    if not SHA.fullmatch(harness):
        raise ValueError('exact merged harness commit required')
    subprocess.run(['git', '-C', str(source), 'merge-base', '--is-ancestor', harness, plan_commit], check=True)

    inventory_ref = contract.get('control_inventory')
    if not isinstance(inventory_ref, dict):
        raise ValueError('hash-bound control inventory required')
    inventory_path = safe_relative(inventory_ref.get('path', ''))
    inventory_sha = inventory_ref.get('sha256', '')
    if not re.fullmatch(r'[0-9a-f]{64}', inventory_sha):
        raise ValueError('hash-bound control inventory required')
    if inventory_path.parts[:4] != ('reports', 'releases', 'v0.9.0', 'execution-v1'):
        raise ValueError('control inventory must be an execution-v1 overlay')
    if str(inventory_path) == contract_path:
        raise ValueError('control contract and inventory must be distinct files')
    raw_inventory = git(source, 'show', plan_commit + ':' + str(inventory_path))
    if hashlib.sha256(raw_inventory).hexdigest() != inventory_sha:
        raise ValueError('control inventory digest mismatch')
    inventory = json.loads(raw_inventory)
    controls = inventory.get('controls')
    if not isinstance(controls, list) or not controls:
        raise ValueError('control inventory must contain controls')
    control_by_id = {}
    for control in controls:
        if not isinstance(control, dict) or not isinstance(control.get('id'), str) or not control['id']:
            raise ValueError('invalid control inventory entry')
        if control['id'] in control_by_id:
            raise ValueError('duplicate control inventory id: ' + control['id'])
        control_by_id[control['id']] = control
    if not isinstance(control_id, str) or control_id not in control_by_id:
        raise ValueError('control id is not in the reviewed inventory: ' + str(control_id))

    roots = contract.get('control_execution_roots')
    if not isinstance(roots, dict) or set(roots) != set(control_by_id):
        raise ValueError('every control must designate one execution root')
    normalized_roots = {}
    for identity, root in roots.items():
        if not isinstance(root, str) or not root:
            raise ValueError('invalid designated execution root for control: ' + identity)
        root_path = Path(root).expanduser()
        if not root_path.is_absolute():
            raise ValueError('designated control execution roots must be absolute')
        normalized_roots[identity] = str(root_path.resolve())
    if len(set(normalized_roots.values())) != len(normalized_roots):
        raise ValueError('control execution roots must be unique')
    root_paths = [Path(root) for root in normalized_roots.values()]
    for index, root in enumerate(root_paths):
        if any(root in other.parents or other in root.parents for other in root_paths[index + 1:]):
            raise ValueError('control execution roots must not overlap')
    if normalized_roots[control_id] != str(destination):
        raise ValueError('destination does not match the control designated execution root')

    # All plan-bound identities must match their reviewed digest. Mutable
    # overlays are restricted to execution-v1; all other inputs must be byte
    # identical to the exact harness checkout.
    identities = contract.get('input_identities')
    if not isinstance(identities, dict):
        raise ValueError('reviewed input identities required')
    overlay = {contract_path: raw_contract, str(inventory_path): raw_inventory}
    bound_paths = set(overlay)
    for relative, digest in identities.items():
        safe_relative(relative)
        data = git(source, 'show', plan_commit + ':' + relative)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('reviewed input digest mismatch: ' + relative)
        if not relative.startswith('reports/releases/v0.9.0/execution-v1/'):
            original = git(source, 'show', harness + ':' + relative)
            if original != data:
                raise ValueError('reviewed overlay changes immutable harness input: ' + relative)
        overlay[relative] = data
        bound_paths.add(relative)

    # Scripts named by the inventory are identities too. Check all registered
    # control scripts so the reviewed inventory cannot smuggle a plan-only
    # script into any isolated control run.
    for control in controls:
        script_identities = control.get('script_identity', [])
        if not isinstance(script_identities, list):
            raise ValueError('invalid control script identities: ' + control['id'])
        for identity in script_identities:
            if not isinstance(identity, dict):
                raise ValueError('invalid control script identity: ' + control['id'])
            relative = identity.get('path', '')
            safe_relative(relative)
            data = git(source, 'show', plan_commit + ':' + relative)
            if hashlib.sha256(data).hexdigest() != identity.get('sha256'):
                raise ValueError('control script digest mismatch: ' + relative)
            if git(source, 'show', harness + ':' + relative) != data:
                raise ValueError('control script differs from exact harness checkout: ' + relative)
            bound_paths.add(relative)

    selected = control_by_id[control_id]
    selected_roots = selected.get('output_roots')
    if (not isinstance(selected_roots, list) or not selected_roots
            or any(not isinstance(value, str) or not value for value in selected_roots)):
        raise ValueError('control must declare output_roots: ' + control_id)
    output_roots = sorted(set(selected_roots), key=lambda value: (-len(PurePosixPath(value).parts), value))
    for relative in output_roots:
        path = safe_relative(relative)
        if path.parts[0] != 'reports' or len(path.parts) < 2:
            raise ValueError('output must be a narrow reports path')
        for bound in bound_paths:
            other = PurePosixPath(bound)
            if path == other or path in other.parents or other in path.parents:
                raise ValueError('output overlaps registered input')

    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', '-C', str(source), 'clone', '--shared', '--no-checkout', str(source), str(destination)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', '-C', str(destination), 'checkout', '--detach', harness], check=True, stdout=subprocess.DEVNULL)

    # Inspect every path before deleting any parent output root. In particular,
    # do not let a parent output hide a symlink in a nested scratch root.
    for relative in output_roots:
        current = destination
        for part in PurePosixPath(relative).parts:
            current /= part
            if current.is_symlink():
                raise ValueError('symlink in isolated output path')
    removed = []
    for relative in output_roots:
        path = destination / relative
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(relative)
        elif path.exists():
            path.unlink()
            removed.append(relative)

    for relative, data in overlay.items():
        target = destination / relative
        if not target.resolve().is_relative_to(destination):
            raise ValueError('overlay escapes isolated root')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    receipt = {'schema': 'release-root-preparation/v1', 'source': str(source),
               'execution_root': str(destination), 'harness_commit': harness,
               'plan_commit': plan_commit, 'contract_path': contract_path,
               'contract_sha256': hashlib.sha256(raw_contract).hexdigest(),
               'control_id': control_id, 'control_inventory': str(inventory_path),
               'control_inventory_sha256': inventory_sha,
               'removed_isolated_output_roots': removed,
               'input_identities': identities,
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
    p.add_argument('--control')
    args = p.parse_args()
    if args.control:
        receipt = prepare_control_root(args.source, args.destination, args.plan_commit, args.contract, args.control)
    else:
        receipt = prepare_root(args.source, args.destination, args.plan_commit, args.contract)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
