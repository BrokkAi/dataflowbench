#!/usr/bin/env python3
"""Replay bounded structural facts; never grants scoring or full Swift support."""
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-entry-structural-v1'


def main():
    manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
    data = (EVIDENCE / 'portable-evidence.tar.gz').read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest['archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
        assert len({m.name for m in members}) == len(members)
        files = {m.name: archive.extractfile(m).read() for m in members}
    assert set(files) == set(manifest['files'])
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(files[name]).hexdigest() == digest, name
    read = lambda name: json.loads(files[name])
    prefix = 'structural-attempt-01/'
    plan = read(prefix + 'preregistration.json')
    source = ROOT / 'adapters/codeql/swift-entry-structural-v1'
    assert (source / 'preregistration.json').read_bytes() == files[prefix + 'preregistration.json']
    for name, digest in plan['files'].items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == digest, name
    assert [c['id'] for c in plan['controls']] == ['branch', 'throw']
    supplemental = read(prefix + 'supplemental-decode-registration.json')
    assert supplemental['not_part_of_original_75_seconds'] is True
    assert supplemental['deadline_seconds_per_decode'] == 15
    for control in plan['controls']:
        base = prefix + control['id'] + '/'
        facts = dict(read(base + 'structure.json')['#select']['tuples'])
        assert all(facts[k] == 0 for k in plan['expected_zero'])
        assert all(facts[k] == 1 for k in plan['expected_one'])
        assert all(facts[k] > 0 for k in plan['expected_positive'])
        for key in ['declarations', 'throw-statements', 'throw-cfg', 'throw-exits']:
            assert facts[key] == control['expected_' + key.replace('-', '_')]
        rows = sorted(read(base + 'identity-all.json')['#select']['tuples'], key=lambda row: row[3])
        assert [row[3] for row in rows] == list(range(control['expected_declarations']))
        assert len({row[4]['id'] for row in rows}) == len(rows)
        assert len({row[5]['id'] for row in rows}) == len(rows)
        assert len({(row[0]['id'], row[1]['id'], row[2]['id']) for row in rows}) == 1
        # Labels compare the independently retained compiler sequence; they do
        # not construct or sort the extractor's declaration order.
        assert [row[4]['url']['startLine'] for row in rows] == control['compiler_order_labels']
        phases = [('extract', control['extract'])] + [(p['name'], p['argv']) for p in control['phases']]
        elapsed = 0
        for name, argv in phases:
            command = read(base + name + '.command.json')
            assert command['argv'] == argv
            assert command['exit_status'] == 0 and not command['timed_out']
            assert command['cleanup_status'] == 'tracked-processes-stopped'
            assert command['elapsed_seconds'] <= command['deadline_seconds']
            if name == 'extract':
                assert command['deadline_seconds'] == 150
            else:
                elapsed += command['elapsed_seconds']
        assert elapsed <= 75
        extra = next(c for c in supplemental['commands'] if c['case'] == control['id'])
        assert hashlib.sha256(files[base + 'identity.bqrs']).hexdigest() == extra['bqrs_sha256']
        command = read(base + 'identity-all-decode.command.json')
        assert command['argv'] == extra['argv']
        assert command['exit_status'] == 0 and not command['timed_out']
        assert command['cleanup_status'] == 'tracked-processes-stopped'
        assert command['elapsed_seconds'] <= command['deadline_seconds'] == 15
        seal = read(base + 'sealed-closure.json')
        assert seal['delta']['status'] == 'CompleteArtifactClosure'
        assert seal['before']['entries'] == seal['after']['entries']
        delta = read(base + 'post-query-closure.json')['delta']
        assert delta['status'] == 'IncompleteArtifactClosure'
        assert all('/cache/' in row['path'] for key in ['changed', 'removed'] for row in delta[key])
        assert all('/cache/' in row['path'] or row['path'].startswith('log/') for row in delta['added'])
        print(control['id'], 'structural checks passed; query/decode', round(elapsed, 2), 'seconds; scoring unavailable')


if __name__ == '__main__':
    main()
