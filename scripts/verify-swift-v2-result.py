#!/usr/bin/env python3
"""Verify independent Result observations without creating scored outcomes."""
import json
import gzip
from collections import Counter
from pathlib import Path
import re
from swift_population_v2 import ROOT, audit, require, sha
from joern_swift import normalize

BASE = ROOT / 'evidence/swift-v2-vendor-result-220'


def tuples(path):
    return json.loads(path.read_text())['#select']['tuples']


def location_line(row):
    match = re.search(r'/main\.swift:(\d+):\d+:\d+:\d+$', row[0]['label'])
    require(match is not None, 'exact BQRS fixture location')
    return int(match.group(1))


def verify(base=BASE):
    manifest = json.loads((base / 'manifest.json').read_text())
    actual = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p != base / 'manifest.json'}
    require(set(manifest) == actual, 'evidence membership')
    for name, digest in manifest.items(): require(sha(base / name) == digest, 'evidence digest: ' + name)
    diagnosis = json.loads((base / 'foundation-diagnosis/retained-log-observations.json').read_text())
    for observation in diagnosis['observations']:
        source = ROOT / observation['source']
        require(sha(source) == observation['sha256'], 'historical Foundation log digest')
        lines = gzip.decompress(source.read_bytes()).decode(errors='replace').splitlines()
        require(all(lines[row['line'] - 1] == row['text'] for row in observation['selected_lines']), 'historical Foundation excerpt')
    population, additions = audit()
    selected = {c['polarity']: (p, c) for p, c in additions if c['template_id'] == 'dfb-template-result-error-propagation'}
    for polarity, (path, case) in selected.items():
        for tool in ['codeql', 'joern']:
            directory = base / f'{tool}-result-{polarity}-attempt-01'
            require(sha(directory / 'case.json') == sha(path) and sha(directory / 'main.swift') == sha(path.parent / 'main.swift'), 'canonical input drift')
            witness = json.loads((directory / 'witness.json').read_text())
            require(witness['status'] == 'unqualified' and witness['memory_compliance'] == 'unproven', 'qualification promotion')
            require(witness['fixture_revision'] == population['fixture_revision'], 'population revision')
            require(all(r['exit_status'] == 0 and not r['timed_out'] for r in witness['phases'].values()), 'phase failed')
            if tool == 'codeql':
                require(witness['unqualified_feasibility'] and witness['extraction_phase_deadline_seconds'] == 180, 'diagnostic extraction scope')
                endpoint_rows = tuples(directory / 'endpoints.json')
                observed = {(location_line(row), row[1]) for row in endpoint_rows}
                expected = {(case['source_anchors'][0]['line_hint'], 'Benchmark source endpoint observed.'), (case['sink_anchors'][0]['line_hint'], 'Benchmark sink endpoint observed.')}
                require(observed == expected, 'exact source/sink endpoint binding')
                require(tuples(directory / 'flow.json') == [], 'retained Result observation changed')
                declarations = tuples(directory / 'declarations.json')
                require(any(row[2] == 'Swift' and row[3]['label'] == 'failure' for row in declarations), 'resolved Result failure declaration missing')
                require('--ram=512' in witness['phases']['flow']['argv'] and '--timeout=60' in witness['phases']['flow']['argv'], 'query budget drift')
            else:
                graph = json.loads((directory / 'graph.json').read_text()); config = json.loads((directory / 'config.json').read_text())
                require(normalize(graph, config) == ('not-reached', []), 'Joern retained native observation')
                require(graph['analysis_completeness']['status'] == 'unproven' and config['semantics'] == [], 'no fabricated completeness or Result summary')
                require(witness['phases']['query']['environment']['_JAVA_OPTIONS'] == '-Xmx512m' and witness['phases']['query']['deadline_seconds'] == 60, 'Joern query budget drift')
    control = json.loads((base / 'result-identity-control/control.json').read_text())
    directory = base / 'codeql-result-identity-attempt-01'
    endpoints = tuples(directory / 'endpoints.json')
    for role in ['source', 'sink']:
        actual_lines = {location_line(row) for row in endpoints if row[1] == f'Benchmark {role} endpoint observed.'}
        require(actual_lines == set(control[f'expected_{role}_lines']), 'identity decoy accepted or direct endpoint missing')
    require({location_line(row) for row in tuples(directory / 'flow.json')} == set(control['expected_flow_sink_lines']), 'direct control must flow without decoy flow')
    directory = base / 'joern-result-identity-attempt-01'
    require(normalize(json.loads((directory / 'graph.json').read_text()), json.loads((directory / 'config.json').read_text())) == ('reached', []), 'independent direct control')
    for tool in ['codeql', 'joern']:
        witness = json.loads((base / f'{tool}-result-identity-attempt-01/witness.json').read_text())
        require(witness['population'] is None and not witness['population_member'], 'control must not enlarge registry population')
    vendor = base / 'joern-vendor'
    catalog = json.loads((vendor / 'vendor-querydb.json').read_text())
    structural = json.loads((vendor / 'structural-catalog.json').read_text())
    require(len(catalog) == 58 and Counter(row['language'] for row in catalog) == Counter(structural['language_counts']), 'complete vendor catalog language census')
    require(all(row['language'].lower() != 'swift' for row in catalog), 'exact vendor bundle query surface changed')
    metadata = json.loads((vendor / 'release-asset-metadata.json').read_text())
    require(metadata['release']['tag_name'] == 'v4.0.628' and metadata['asset']['id'] == 565234087, 'exact vendor release asset')
    for row in json.loads((vendor / 'content-manifest.json').read_text())['files']:
        require(sha(vendor / row['path']) == row['sha256'], 'vendor content manifest')
    summary = json.loads((base / 'summary.json').read_text())
    require(summary['status'] == 'unqualified-observations' and summary['scored_partitions'] == [], 'no activation or scored partition')
    print('Verified independent Result observations and identity controls; no scored result or qualified correctness')


if __name__ == '__main__': verify()
