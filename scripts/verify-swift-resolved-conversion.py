#!/usr/bin/env python3
"""Verify the bounded patched conversion experiment, without activating scores."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-resolved-native-v1'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def check_rows(rows):
    real = {13, 14, 15, 16, 18, 19, 20, 21}
    local = {23, 24, 25, 26}
    identities = rows['summary-identity']
    require(len(identities) == 12 and {r[0] for r in identities} == real | local, 'identity coverage')
    for row in identities:
        is_real = row[0] in real
        module = 'Foundation' if is_real else 'DataFlowBenchTaintSwift'
        require(row[2] == module and row[3] == ('Swift' if row[4] == 'String' else module), 'declaration provenance')
        require(row[7] is is_real, 'summary applicability')
    require(rows['flow'] == [[12, 17, 87, 'adapter-patched-conversion']], 'endpoint separation')
    roles = rows['roles']
    require(all(r[2] == 'adapter-patched-conversion' for r in roles), 'profile attribution')
    require([r for r in roles if r[3] != 'sink'] == [[12,15,'adapter-patched-conversion','environment']], 'source identity')
    require({tuple(r[:2]) for r in roles if r[3] == 'sink'} == {(line,col) for line in [17,22,27] for col in [32,87]}, 'sink coverage')
    for name, count in [('summary-ports',10),('summary-transfer',6),('summary-store',4)]:
        require(len(rows[name]) == count and not any(r[0] in local for r in rows[name]), 'local summary edge: '+name)
    require({r[0] for r in rows['summary-ports']} == real, 'real ports coverage')
    require(all(r[3] == '' for r in rows['summary-ports']), 'invented origin')
    require({(r[0],r[5]) for r in rows['summary-store']} == {(13,'CollectionElement'),(18,'CollectionElement'),(16,'OptionalSome'),(21,'OptionalSome')}, 'content stores')
    require(all(r[0] == r[1] == r[3] for r in rows['summary-transfer'] + rows['summary-store']), 'call-site join')


def verify():
    plan = read(BASE / 'conversion-plan-v2.json')
    for field in ['queries','runner_files']:
        for path,digest in plan[field].items():
            require(sha(ROOT/path) == digest, 'preregistered input: '+path)
    require(plan['scored_activation'] is False, 'score promotion')
    original = read(ROOT/'evidence/swift-summary-qualification-v1/store-plan.json')
    require(plan['dataset_files'] == original['dataset_files'] and plan['source_archive_sha256'] == original['source_archive_sha256'], 'retained source identity')
    attempt = BASE/'conversion-attempt-03'
    manifest = read(attempt/'manifest.json')
    require(set(manifest) == {str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()}-{'manifest.json'}, 'artifact closure')
    for path,digest in manifest.items():
        require(sha(attempt/path) == digest, 'artifact digest: '+path)
    run = read(attempt/'run.json')
    require(run['plan_sha256'] == sha(BASE/'conversion-plan-v2.json') and run['scored_activation'] is False, 'run scope')
    names = ['roles','flow','identity','summary-identity','summary-ports','summary-transfer','summary-store']
    require(set(run['phases']) == {n+s for n in names for s in ['', '-decode']}, 'phase closure')
    for name,command in run['phases'].items():
        require(command['exit_status'] == 0 and not command['timed_out'] and command['cleanup_status'] == 'tracked-processes-stopped', 'phase failure: '+name)
        require(command['deadline_seconds'] == 60, 'deadline')
        if not name.endswith('-decode'):
            require('--ram=2048' in command['argv'], 'memory request')
    for path in plan['queries']:
        require((attempt/'queries'/Path(path).name).read_bytes() == (ROOT/path).read_bytes(), 'query copy')
    paths = read(attempt/'library-path.json')['libraryPath']
    require(any(p.endswith('/swift-all/6.8.4-dfb.2') for p in paths) and not any(p.endswith('/swift-all/6.8.4') for p in paths), 'patched library selection')
    check_rows({n:read(attempt/(n+'.json'))['#select']['tuples'] for n in names})
    print('Conversion applicability control verified; broader body/heuristic qualification remains incomplete.')


if __name__ == '__main__':
    verify()
