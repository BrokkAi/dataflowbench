#!/usr/bin/env python3
"""Reconcile candidate native evidence without inventing endpoint support."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-candidate-native-controls-220'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def successful(record):
    return record['exit_status'] == 0 and not record['timed_out'] and record['cleanup_status'] == 'tracked-processes-stopped'


def census():
    directory = BASE / 'joern-census'
    final = read(directory / 'final-summary.json')
    counts = {}
    jars = {}
    unique = set()
    member_jars = set()
    classes = resources = 0
    for item in final['compressed_jsonl']:
        path = directory / item['gzip']
        assert sha(path) == item['gzip_sha256'], path
        assert path.stat().st_size == item['gzip_size_bytes'], path
        digest = hashlib.sha256()
        count = size = 0
        with gzip.open(path, 'rb') as stream:
            for line in stream:
                digest.update(line)
                size += len(line)
                count += 1
                row = json.loads(line)
                if item['source'] == 'jars.jsonl':
                    jars[row['relative_path']] = row['sha256']
                elif item['source'] == 'unique-jars.jsonl':
                    unique.add(row['jar_sha256'])
                elif item['source'] == 'all-jar-members.jsonl':
                    member_jars.add(row['jar_sha256'])
                    if not row['is_directory']:
                        classes += row['member'].endswith('.class')
                        resources += not row['member'].endswith(('.class', '.tasty'))
        assert digest.hexdigest() == item['source_sha256'], path
        assert size == item['source_size_bytes'], path
        counts[item['source']] = count
    expected = final['counts']
    for name, key in [('all-files', 'extracted_files'), ('jars', 'jar_paths'),
                      ('unique-jars', 'unique_jar_sha256_contents'),
                      ('all-jar-members', 'unique_content_jar_members'),
                      ('all-jar-resources', 'unique_content_non_class_non_tasty_resources'),
                      ('first-party-classes', 'exact_first_party_package_class_rows'),
                      ('keyword-navigation-hits', 'keyword_navigation_rows')]:
        assert counts[name + '.jsonl'] == expected[key], name
    assert set(jars.values()) == unique == member_jars
    assert len(jars) - len(unique) == expected['duplicate_jar_path_mappings']
    assert classes == expected['unique_content_class_members']
    assert resources == expected['unique_content_non_class_non_tasty_resources']
    assessment = read(directory / 'integration-assessment.json')
    assert assessment['status'] == 'blocked' and not assessment['capability_partition_emitted']
    return {'counts': expected, 'assessment': assessment}


def observe(path):
    witness = read(path / 'witness.json')
    phases = witness['phases']
    result = {'path': str(path.relative_to(ROOT)), 'case_id': witness['case_id'],
              'failure': witness.get('probe_error', witness.get('cleanup_error')),
              'scored_qualified': False,
              'extraction_phase_deadline_seconds': witness['extraction_phase_deadline_seconds'],
              'phase_results': {name: {'exit_status': row['exit_status'], 'timed_out': row['timed_out'],
                                       'cleanup_status': row['cleanup_status']} for name, row in phases.items()}}
    finalized = (all(name in phases and successful(phases[name]) for name in ('database-create', 'database-resolve'))
                 and witness.get('database_validation') == 'finalized-swift-artifact; no containment claim')
    result['finalized_swift_database'] = finalized
    complete = finalized and all(name in phases and successful(phases[name]) and (path / (name + '.json')).is_file()
                                for name in ('rolesCalls', 'roleNodes'))
    result['role_observation_complete'] = complete
    if complete:
        result['declaration_rows'] = read(path / 'rolesCalls.json')['#select']['tuples']
        result['shipped_role_nodes'] = read(path / 'roleNodes.json')['#select']['tuples']
    else:
        result['capability_interpretation'] = 'blocked: no complete finalized native role observation'
    return result


def build():
    plan = read(BASE / 'plan.json')
    assert plan['opaque_choice'] == 'pending' and not plan['native_binary_execution'] and not plan['active_pin_mutation']
    for path, digest in plan['files'].items():
        assert sha(ROOT / path) == digest, path
    supplement = read(BASE / 'node-query-plan.json')
    assert sha(ROOT / supplement['query']) == supplement['sha256']
    attempts = [observe(p.parent) for p in sorted(BASE.glob('codeql-*/witness.json'))]
    assert len(attempts) == 6, 'retain three initial attempts and three bounded retries'
    latest = {name: next(r for r in attempts if r['path'].endswith(f'codeql-{name}-attempt-02'))
              for name in plan['codeql_controls']}
    blockers = []
    for name, row in latest.items():
        if not row['role_observation_complete']:
            blockers.append({'control': name, 'reason': 'incomplete finalized role observation'})
            continue
        source_line = 12 if name == 'near-misses' else 3
        if not any(n[0] == source_line and n[2] == 'shipped-source' for n in row['shipped_role_nodes']):
            blockers.append({'control': name, 'reason': 'known contentsOf positive did not acquire a shipped-source role'})
    near = latest['near-misses']
    if near['role_observation_complete']:
        lookalike = [r for r in near['declaration_rows'] if r[0] == 18 and r[2] == 'declaration'
                     and r[3] == 'DataFlowBenchTaintSwift:arguments:[String]']
        sinks = [r for r in near['shipped_role_nodes'] if r[0] == 18 and r[2] == 'shipped-sink']
        if lookalike and sinks:
            blockers.append({'control': 'near-misses', 'reason': 'shipped sink instantiated at benchmark-owned Process.arguments lookalike',
                             'declarations': lookalike, 'role_nodes': sinks})
    return {'schema_version': 1, 'scope': 'candidate-native control observations',
            'joern_census': census(),
            'codeql_attempts': attempts, 'opaque_choice': 'pending', 'active_pins_changed': False,
            'candidate_native_admission': 'blocked' if blockers else 'not-decided', 'blockers': blockers,
            'capability_partition_emitted': False,
            'limits': 'Non-scored diagnostics only. A 180s extraction is a feasibility retry, not a changed scored budget. Incomplete finalization or role queries cannot prove absence. Individual phases do not establish memory compliance or complete descendant containment.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True) + '\n'
    if args.write:
        (BASE / 'summary.json').write_text(text)
    else:
        assert (BASE / 'summary.json').read_text() == text, 'stale native control summary'
        actual = {str(p.relative_to(BASE)): sha(p) for p in BASE.rglob('*')
                  if p.is_file() and p != BASE / 'manifest.json'}
        assert actual == read(BASE / 'manifest.json')['files'], 'native control evidence changed'
    print('Native controls reconciled; pending scope and qualification boundaries preserved')


if __name__ == '__main__':
    main()
