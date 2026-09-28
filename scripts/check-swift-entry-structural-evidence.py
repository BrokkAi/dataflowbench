#!/usr/bin/env python3
"""Replay bounded structural facts; never grants scoring or full Swift support."""
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-entry-structural-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_facts(rows, plan, control):
    expected = set(plan['expected_zero'] + plan['expected_one'] + plan['expected_positive'])
    expected.update(['declarations', 'throw-statements', 'throw-cfg', 'throw-exits'])
    require(isinstance(rows, list), 'fact rows must be a list')
    facts = {}
    for row in rows:
        require(isinstance(row, list) and len(row) == 2, 'malformed fact row')
        key, value = row
        require(isinstance(key, str) and key in expected, 'unknown fact key')
        require(key not in facts, 'duplicate fact key: ' + key)
        require(type(value) is int and value >= 0, 'fact count must be a nonnegative integer')
        facts[key] = value
    require(set(facts) == expected, 'missing fact keys')
    require(all(facts[k] == 0 for k in plan['expected_zero']), 'nonzero forbidden fact')
    require(all(facts[k] == 1 for k in plan['expected_one']), 'required singleton fact')
    require(all(facts[k] > 0 for k in plan['expected_positive']), 'missing positive fact')
    for key in ['declarations', 'throw-statements', 'throw-cfg', 'throw-exits']:
        require(facts[key] == control['expected_' + key.replace('-', '_')], 'wrong control count: ' + key)
    return facts


def validate_identities(rows, control):
    require(isinstance(rows, list) and len(rows) == control['expected_declarations'], 'identity row count')
    for row in rows:
        require(isinstance(row, list) and len(row) == 6, 'malformed identity row')
        require(type(row[3]) is int and row[3] >= 0, 'invalid compiler index')
        for column in [0, 1, 2, 4, 5]:
            require(isinstance(row[column], dict) and type(row[column].get('id')) is int and row[column]['id'] >= 0, 'invalid entity ID')
    rows = sorted(rows, key=lambda row: row[3])
    require([row[3] for row in rows] == list(range(control['expected_declarations'])), 'non-dense or duplicate indices')
    require(len({row[4]['id'] for row in rows}) == len(rows), 'duplicate declaration entity')
    require(len({row[5]['id'] for row in rows}) == len(rows), 'duplicate body entity')
    require(len({(row[0]['id'], row[1]['id'], row[2]['id']) for row in rows}) == 1, 'mixed entry ownership')
    require([row[4]['url']['startLine'] for row in rows] == control['compiler_order_labels'], 'compiler sequence mismatch')


def validate_command(command, argv, maximum):
    require(command['argv'] == argv, 'command provenance mismatch')
    require(type(command['exit_status']) is int and command['exit_status'] == 0 and command['timed_out'] is False, 'failed command')
    require(command['cleanup_status'] == 'tracked-processes-stopped', 'incomplete cleanup')
    elapsed, deadline = command['elapsed_seconds'], command['deadline_seconds']
    require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in [elapsed, deadline]), 'invalid timing')
    require(0 < deadline <= maximum and elapsed <= deadline, 'deadline exceeded')


def validate_supplement(control, supplemental, command, bqrs):
    require(supplemental['not_part_of_original_75_seconds'] is True, 'supplement budget conflated')
    require(type(supplemental['deadline_seconds_per_decode']) is int and supplemental['deadline_seconds_per_decode'] == 15, 'supplement deadline changed')
    require([c['case'] for c in supplemental['commands']] == ['branch', 'throw'], 'supplement control set changed')
    extra = next(c for c in supplemental['commands'] if c['case'] == control['id'])
    require(hashlib.sha256(bqrs).hexdigest() == extra['bqrs_sha256'], 'supplement BQRS provenance mismatch')
    validate_command(command, extra['argv'], 15)
    require(command['deadline_seconds'] == 15, 'supplement deadline mismatch')


def main():
    manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
    data = (EVIDENCE / 'portable-evidence.tar.gz').read_bytes()
    require(hashlib.sha256(data).hexdigest() == manifest['archive_sha256'], "evidence check failed: hashlib.sha256(data).hexdigest() == manifest['archive_sha256']")
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        require(all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members), "evidence check failed: all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)")
        require(len({m.name for m in members}) == len(members), 'evidence check failed: len({m.name for m in members}) == len(members)')
        files = {m.name: archive.extractfile(m).read() for m in members}
    require(set(files) == set(manifest['files']), "evidence check failed: set(files) == set(manifest['files'])")
    for name, digest in manifest['files'].items():
        require(hashlib.sha256(files[name]).hexdigest() == digest, 'evidence check failed: hashlib.sha256(files[name]).hexdigest() == digest')
    read = lambda name: json.loads(files[name])
    prefix = 'structural-attempt-01/'
    plan = read(prefix + 'preregistration.json')
    source = ROOT / 'adapters/codeql/swift-entry-structural-v1'
    require((source / 'preregistration.json').read_bytes() == files[prefix + 'preregistration.json'], "evidence check failed: (source / 'preregistration.json').read_bytes() == files[prefix + 'preregistration.json']")
    for name, digest in plan['files'].items():
        require(hashlib.sha256((source / name).read_bytes()).hexdigest() == digest, 'evidence check failed: hashlib.sha256((source / name).read_bytes()).hexdigest() == digest')
    require([c['id'] for c in plan['controls']] == ['branch', 'throw'], "evidence check failed: [c['id'] for c in plan['controls']] == ['branch', 'throw']")
    supplemental = read(prefix + 'supplemental-decode-registration.json')
    require(supplemental['not_part_of_original_75_seconds'] is True, "evidence check failed: supplemental['not_part_of_original_75_seconds'] is True")
    require(supplemental['deadline_seconds_per_decode'] == 15, "evidence check failed: supplemental['deadline_seconds_per_decode'] == 15")
    for control in plan['controls']:
        base = prefix + control['id'] + '/'
        validate_facts(read(base + 'structure.json')['#select']['tuples'], plan, control)
        validate_identities(read(base + 'identity-all.json')['#select']['tuples'], control)
        phases = [('extract', control['extract'])] + [(p['name'], p['argv']) for p in control['phases']]
        elapsed = 0
        for name, argv in phases:
            command = read(base + name + '.command.json')
            validate_command(command, argv, 150 if name == 'extract' else 75)
            if name == 'extract':
                require(command['deadline_seconds'] == 150, "evidence check failed: command['deadline_seconds'] == 150")
            else:
                elapsed += command['elapsed_seconds']
        require(elapsed <= 75, 'evidence check failed: elapsed <= 75')
        validate_supplement(control, supplemental, read(base + 'identity-all-decode.command.json'), files[base + 'identity.bqrs'])
        seal = read(base + 'sealed-closure.json')
        require(seal['delta']['status'] == 'CompleteArtifactClosure', "evidence check failed: seal['delta']['status'] == 'CompleteArtifactClosure'")
        require(seal['before']['entries'] == seal['after']['entries'], "evidence check failed: seal['before']['entries'] == seal['after']['entries']")
        delta = read(base + 'post-query-closure.json')['delta']
        require(delta['status'] == 'IncompleteArtifactClosure', "evidence check failed: delta['status'] == 'IncompleteArtifactClosure'")
        require(all('/cache/' in row['path'] for key in ['changed', 'removed'] for row in delta[key]), "evidence check failed: all('/cache/' in row['path'] for key in ['changed', 'removed'] for row in delta[key])")
        require(all('/cache/' in row['path'] or row['path'].startswith('log/') for row in delta['added']), "evidence check failed: all('/cache/' in row['path'] or row['path'].startswith('log/') for row in delta['added'])")
        print(control['id'], 'structural checks passed; query/decode', round(elapsed, 2), 'seconds; scoring unavailable')


if __name__ == '__main__':
    main()
