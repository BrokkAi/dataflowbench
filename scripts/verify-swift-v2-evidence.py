#!/usr/bin/env python3
"""Verify the immutable compile-only native and Result control evidence."""
import json
from pathlib import Path
from swift_population_v2 import ROOT, audit, require, sha


def main():
    manifest, additions = audit()
    directory = ROOT / 'evidence/swift-v2-220/compile-control-attempt-01'
    files = json.loads((directory / 'manifest.json').read_text())
    require(set(files) == {p.name for p in directory.iterdir() if p.is_file() and p.name != 'manifest.json'}, 'evidence membership')
    for name, digest in files.items():
        require(sha(directory / name) == digest, f'evidence digest: {name}')
    evidence = json.loads((directory / 'evidence.json').read_text())
    require(evidence['status'] == 'passed', 'compiler/control completion')
    require(evidence['population']['fixture_revision'] == manifest['fixture_revision'], 'evidence population')
    require(evidence['population']['manifest_sha256'] == sha(ROOT / 'populations/swift-synthetic-v2.json'), 'evidence manifest digest')
    require(evidence['validator']['sha256'] == sha(ROOT / 'scripts/validate-swift-v2.py'), 'validator identity')
    expected = {case['id']: (path, case) for path, case in additions}
    require({r['case_id']: r['sha256'] for r in evidence['metadata_digests']} == {identifier: sha(path) for identifier, (path, _) in expected.items()}, 'metadata identity')
    for record in evidence['cases']:
        path, case = expected[record['case_id']]
        require(record['fixture_files'] == [{'path': name, 'sha256': sha(path.parent / name), 'bytes': (path.parent / name).stat().st_size} for name in case['fixture_files']], 'source identity')
    require(len(evidence['cases']) == len(expected), 'case evidence completeness')
    events = evidence['events']
    compiles = [e for e in events if e['kind'] == 'compile']
    require(len(compiles) == 18 and all(e['exit'] == 0 for e in compiles), 'all 14 inputs and four instrumented controls compile')
    require({e['case_id'] for e in compiles if not e['instrumented']} == set(expected), 'unmodified compilation set')
    native = {identifier for identifier, (_, case) in expected.items() if case['model_profile'] == 'tool-native'}
    require(not any(e['instrumented'] and e['case_id'] in native for e in compiles), 'native instrumentation forbidden')
    binaries = {e['output']: e for e in compiles}
    executions = [c for c in evidence['commands'] if c['argv'][0] in binaries]
    require(len(executions) == 4 and all(c['exit'] == 0 and binaries[c['argv'][0]]['instrumented'] and binaries[c['argv'][0]]['case_id'] not in native for c in executions), 'only four Result binary executions')
    require(all(c['exit'] == 0 for c in evidence['commands']), 'retained command completion')
    controls = {e['case_id']: e['observed'] for e in events if e['kind'] == 'control-result'}
    require(controls == {'dfb-taint-swift-result-error-propagation-positive': {'7': 7, '19': 19}, 'dfb-taint-swift-result-error-propagation-negative': {'7': 0, '19': 0}}, 'Result source dependence and near miss')
    print('Verified 14 compiled inputs, four Result controls, zero native executions; no analyzer outcomes')


if __name__ == '__main__':
    main()
