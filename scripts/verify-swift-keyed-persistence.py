#!/usr/bin/env python3
"""Verify retained prototype successes and failures without semantic promotion."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-keyed-persistence-v1'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
PROFILE = 'adapter-patched-suite-state'


def require(value, message):
    if not value:
        raise ValueError(message)


def manifest(directory):
    values = read(directory / 'manifest.json')
    require(set(values) == {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()} - {'manifest.json'}, 'artifact closure')
    for name, digest in values.items():
        require(sha(directory / name) == digest, 'artifact digest: ' + name)


def rows(directory, name):
    return read(directory / (name + '.json'))['#select']['tuples']


def check_rows(data):
    require(data['flow'] == [[12, n, 87, PROFILE] for n in [13, 16, 29, 37, 43]], 'expanded positive/safe separation')
    require(all(r[2] == PROFILE for r in data['roles']), 'profile attribution')
    require([r for r in data['roles'] if r[3] != 'sink'] == [[12, 21, PROFILE, 'environment']], 'source role')
    require({tuple(r[:2]) for r in data['roles'] if r[3] == 'sink'} == {(n, c) for n in [13, 16, 18, 22, 25, 29, 32, 37, 39, 43, 47] for c in [32, 87]}, 'sink coverage')
    suite = 'DataFlowBench.Independent.Persistence'
    other = 'DataFlowBench.Other.Persistence'
    sequence = [10, 11, 14, 15, 17, 23, 24, 27, 28, 30, 31, 33, 36, 41, 42, 44, 45, 46]
    points = {(n, suite) for n in sequence} | {(35, other), (38, other)}
    require({(r[0], r[2], r[3]) for r in data['states']} == {(n, d, p) for n, d in points for p in [False, True]}, 'state identity')
    expected = {(n, False, n, True, d) for n, d in points} | {(a, True, b, False, suite) for a, b in zip(sequence, sequence[1:])} | {(35, True, 38, False, other)}
    require({tuple(r) for r in data['transitions']} == expected, 'ordered state transitions')
    stores = {10: 'payload', 11: 'other', 14: 'payload', 23: 'payload', 27: 'alias', 30: 'alias', 33: 'payload', 35: 'payload', 41: 'shared', 44: 'before', 46: 'before'}
    reads = {15: 'payload', 17: 'other', 24: 'payload', 28: 'alias', 31: 'alias', 36: 'payload', 38: 'payload', 42: 'shared', 45: 'before'}
    require({(r[0], r[2]) for r in data['clears']} == set(stores.items()), 'key-specific clears')
    require({(r[0], r[1], r[3], r[5]) for r in data['content']} == {(kind, n, n, key) for kind, values in [('store', stores), ('read', reads)] for n, key in values.items()}, 'key-specific contents')
    identities = data['persistence-identity']
    require(len(identities) == 26 and sum(r[2:5] == ['Foundation', 'Foundation', 'UserDefaults'] for r in identities) == 23, 'resolved owner coverage')
    require({r[0] for r in identities if r[2] == 'DataFlowBenchTaintSwift'} == {19, 20, 21}, 'local owner near miss')
    require(not any(r[-1] for r in identities), 'manual summary attribution')


def verify():
    stages = [
        ('attempt-01', 'plan-v1.json', ['roles', 'flow', 'persistence-identity', 'persistence-keys', 'content', 'clears'], None),
        ('suite-attempt-01', 'suite-plan-v1.json', ['roles'], 'roles'),
        ('suite-attempt-02', 'suite-plan-v2.json', ['roles', 'flow', 'persistence-identity', 'persistence-keys', 'content', 'clears', 'states', 'transitions'], None),
        ('origin-attempt-01', 'origin-plan-v1.json', ['origins', 'ssa'], 'ssa'),
        ('origin-attempt-02', 'origin-plan-v2.json', ['origins', 'ssa', 'qualifiers'], None),
        ('origin-attempt-03', 'origin-plan-v3.json', ['definitions', 'receiver-flow'], None),
        ('suite-attempt-03', 'suite-plan-v3.json', ['roles', 'flow', 'persistence-identity', 'persistence-keys', 'content', 'clears', 'states', 'transitions'], None),
    ]
    for name, plan_name, queries, failed in stages:
        directory = BASE / name
        plan_path = BASE / plan_name
        plan = read(plan_path)
        require(plan['scored_activation'] is False and plan['scope'].startswith('non-scored'), 'plan promotion')
        for field in ['queries', 'runner_files', 'inputs']:
            for path, digest in plan[field].items():
                require(sha(ROOT / path) == digest, 'preregistered digest: ' + path)
        manifest(directory)
        run = read(directory / 'run.json')
        require(run['scored_activation'] is False and run['plan_sha256'] == sha(plan_path), 'run promotion/provenance')
        phases = [q + suffix for q in queries for suffix in ([''] if q == failed else ['', '-decode'])]
        require(set(run['phases']) == set(phases), 'phase closure')
        for phase in phases:
            command = read(directory / (phase + '.command.json'))
            require(command == run['phases'][phase], 'phase projection')
            require(command['exit_status'] == (2 if phase == failed else 0) and not command['timed_out'] and command['cleanup_status'] == 'tracked-processes-stopped' and not command.get('cleanup_error'), 'phase outcome')
            require(command['deadline_seconds'] == 60 and command['memory_compliance'] == 'unproven', 'phase scope')
            if phase in queries:
                require('--ram=2048' in command['argv'] and '--timeout=60' in command['argv'], 'phase bounds')
                source = next(path for path in plan['queries'] if Path(path).name == phase + '.ql')
                require((directory / 'queries' / (phase + '.ql')).read_bytes() == (ROOT / source).read_bytes(), 'executed query')
        if failed:
            require('ERROR:' in (directory / (failed + '.stderr')).read_text(), 'retained compiler error')
    expanded = BASE / 'expanded-attempt-01'
    manifest(expanded); manifest(expanded / 'probe')
    plan = read(BASE / 'expanded-plan-v1.json')
    for field in ['control_files', 'query_files', 'vendor_files', 'runner_files']:
        for path, digest in plan[field].items():
            require(sha(ROOT / path) == digest, 'expanded preregistered digest')
    run = read(expanded / 'run.json')
    require(run['plan_sha256'] == sha(BASE / 'expanded-plan-v1.json') and run['scored_activation'] is False and run['status'] == 'unqualified' and run['exit_status'] == 0, 'expanded promotion/provenance')
    require([r[:3] for r in rows(BASE / 'attempt-01', 'flow')] == [[12, 13, 87], [12, 16, 87]], 'small control evidence')
    require([r[:3] for r in rows(expanded / 'probe', 'flow')] == [[12, 13, 87], [12, 16, 87], [12, 37, 87]], 'retained missing aliases')
    require([r[:3] for r in rows(BASE / 'suite-attempt-02', 'flow')] == [[12, 13, 87]], 'empty-origin attempt')
    require(all(rows(BASE / 'suite-attempt-02', n) == [] for n in ['states', 'transitions', 'content', 'clears']), 'empty-origin diagnostic')
    final = BASE / 'suite-attempt-03'
    check_rows({n: rows(final, n) for n in stages[-1][2]})
    print('Retained keyed/suite prototypes verified, including failures; non-scored and incomplete outside controls.')


if __name__ == '__main__':
    verify()
