#!/usr/bin/env python3
"""Replay compact native rows without executing CodeQL or changing scores."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
from swift_entry_observation import classify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-entry-extractor-v1'


def main():
    record = json.loads((EVIDENCE / 'record.json').read_text())
    data = (EVIDENCE / 'portable-evidence.tar.gz').read_bytes()
    assert hashlib.sha256(data).hexdigest() == record['archive_sha256'], 'archive hash mismatch'
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
        assert len({m.name for m in members}) == len(members), 'duplicate archive member'
        files = {m.name: archive.extractfile(m).read() for m in members}
    assert set(files) == set(record['files']), 'closure mismatch'
    for name, digest in record['files'].items():
        assert hashlib.sha256(files[name]).hexdigest() == digest, name
    expected_ids = {'direct-positive', 'direct-negative', 'local-overwrite-positive',
                    'local-overwrite-negative', 'array-element-positive', 'array-element-negative',
                    'callback-registration-positive', 'callback-registration-negative', 'wrapped', 'wrapped-negative'}
    for case in expected_ids:
        audit = json.loads(files['closure-audit/' + case + '.json'])
        assert audit['delta']['status'] == 'CompleteArtifactClosure'
        assert audit['before']['entries'] == audit['after']['entries']
    diagnosis = EVIDENCE / 'retained-diagnosis-01'
    diagnostic_manifest = json.loads((diagnosis / 'manifest.json').read_text())
    for name, digest in diagnostic_manifest['files'].items():
        assert hashlib.sha256((diagnosis / name).read_bytes()).hexdigest() == digest
    diagnostic_results = json.loads((diagnosis / 'retained-diagnosis-01/results.json').read_text())
    assert len(diagnostic_results) == 3 and all(r['status'] == 'completed' for r in diagnostic_results)
    results = []
    for name in sorted(files):
        if name.startswith('controls-attempt-01/') and name.endswith('/observation.json'):
            native = json.loads(files[name])
            case_dir = name.rsplit('/', 1)[0]
            if native['status'] == 'completed':
                assert native['extraction_integrity']['ready_for_observation'] is True
                phases = []
                for phase in ['extract', 'entry', 'entry-decode', 'diagnostics', 'diagnostics-decode', 'kernel-flow', 'kernel-flow-decode']:
                    command = json.loads(files[case_dir + '/' + phase + '.command.json'])
                    assert command['exit_status'] == 0 and command['timed_out'] is False
                    assert command['cleanup_status'] == 'tracked-processes-stopped'
                    assert command['elapsed_seconds'] <= command['deadline_seconds']
                    if phase != 'extract':
                        phases.append(command['elapsed_seconds'])
                assert sum(phases) <= 75
                for query, key in [('entry', 'entry_rows'), ('kernel-flow', 'flow_rows')]:
                    assert native[key] == json.loads(files[case_dir + '/' + query + '.json'])['#select']['tuples']
                assert native['exact_endpoints'] == [row for row in json.loads(files[case_dir + '/diagnostics.json'])['#select']['tuples'] if row[5] == 1]
                observation = classify(native['entry_rows'], native['exact_endpoints'], native['flow_rows'])
            else:
                observation = {'status': 'incomplete', 'reason': native.get('reason', 'native phase incomplete')}
            results.append({'id': native['id'], 'observation': observation})
    assert {r['id'] for r in results} == expected_ids, 'missing control observations'
    assert record['scored_activation'] is False and record['stock_results_changed'] is False
    print(json.dumps({'scope': 'patched-extractor-diagnostic-only', 'scored_activation': False, 'controls': results}, indent=2))


if __name__ == '__main__':
    main()
