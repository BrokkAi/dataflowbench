#!/usr/bin/env python3
"""Verify retained Swift resolved-append evidence without running CodeQL."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from swift_extraction_integrity import inspect_logs

BASE_REL = Path('evidence/swift-resolved-native-v1')
CANONICAL_PLAN_REL = Path('adapters/codeql/swift-resolved-native-v1/canonical-append-plan.json')
CANONICAL_QUERY_ROOT = Path('adapters/codeql/swift-resolved-native-v1/canonical-queries-v1')
CANONICAL_PHASES = ('database-create', 'database-resolve', 'roles', 'flow', 'identity')
APPEND_BODY_PHASES = ('database-create', 'database-resolve', 'roles', 'identity', 'append-flow')
LANES = {
    'vendor-native': 'vendor-native',
    'adapter-assisted-stock': 'adapter-corrected-stock',
    'adapter-resolved-experiment': 'adapter-resolved-experiment',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def checked(root, relative):
    root = root.resolve()
    path = (root / relative).resolve()
    require(path == root or root in path.parents, 'path escapes evidence root: ' + str(relative))
    return path


def verify_bound_inputs(root, mappings):
    for mapping in mappings:
        for name, digest in mapping.items():
            path = checked(root, name)
            require(path.is_file() and sha(path) == digest, 'preregistered input digest: ' + name)


def verify_manifest(directory):
    manifest_path = directory / 'manifest.json'
    manifest = read(manifest_path)
    require(isinstance(manifest, dict), 'manifest shape')
    actual = {str(path.relative_to(directory)) for path in directory.rglob('*')
              if path.is_file() and path != manifest_path}
    require(set(manifest) == actual, 'exact retained artifact set: ' + str(directory))
    for name, digest in manifest.items():
        path = checked(directory, name)
        require(path.is_file() and sha(path) == digest, 'retained digest: ' + name)
    return manifest


def rows(path):
    result = read(path)
    require(isinstance(result.get('#select'), dict) and
            isinstance(result['#select'].get('tuples'), list), 'query result shape: ' + str(path))
    return result['#select']['tuples']


def check_phase(record, deadline, query=False):
    require(record.get('exit_status') == 0 and record.get('timed_out') is False,
            'phase failure')
    require(record.get('cleanup_status') == 'tracked-processes-stopped' and
            record.get('cleanup_error') in (None, ''), 'phase cleanup failure')
    require(record.get('deadline_seconds') == deadline, 'phase deadline drift')
    argv = record.get('argv', [])
    if query:
        require('--ram=2048' in argv and '--timeout=60' in argv, 'query budget drift')


def check_phase_bundle(directory, witness, phases):
    records = witness.get('phases', {})
    require(set(records) == set(phases), 'phase witness set')
    for name in phases:
        record = read(directory / (name + '.command.json'))
        require(record == records[name], 'phase witness join: ' + name)
        check_phase(record, 150 if name == 'database-create' else 60,
                    name in ('roles', 'flow', 'identity', 'append-flow'))
    for name in phases:
        if name in ('database-create', 'database-resolve'):
            continue
        decode = read(directory / (name + '-decode.command.json'))
        check_phase(decode, 60)
    require(witness.get('analysis_budget') == {'wall_clock_seconds': 60,
            'peak_memory_mb': 2048} and witness.get('extraction_phase_deadline_seconds') == 150,
            'analysis/extraction budget drift')
    require(witness.get('probe_error') in (None, '') and witness.get('cleanup_error') in (None, ''),
            'probe or cleanup error')
    require(inspect_logs(directory / 'log/swift/extractor')['ready_for_observation'],
            'raw extraction gate')


def check_query_snapshots(directory, root, mapping):
    query_dir = directory / 'queries'
    expected = {Path(name).name for name in mapping}
    actual = {path.name for path in query_dir.iterdir() if path.is_file()}
    require(actual == expected, 'query snapshot file set')
    for name in mapping:
        require((query_dir / Path(name).name).read_bytes() == checked(root, name).read_bytes(),
                'query snapshot provenance: ' + name)


def verify_original_database(plan, run, require_database=False):
    database = Path(plan['database'])
    phase = run.get('phases', {}).get('append-flow', {})
    argv = phase.get('argv', [])
    require('--database=' + str(database) in argv, 'original database query join')
    if not database.is_dir():
        require(not require_database, 'retained original database unavailable')
        return False
    data_root = database / 'db-swift'
    actual = {str(path.relative_to(database)) for path in data_root.rglob('*') if path.is_file()
              and not str(path.relative_to(database)).startswith('db-swift/default/cache/')}
    require(actual == set(plan['dataset_files']), 'retained original database file set')
    for name, digest in plan['dataset_files'].items():
        require(sha(checked(database, name)) == digest, 'retained original database digest: ' + name)
    archive = database / 'src.zip'
    require(archive.is_file() and sha(archive) == plan['source_archive_sha256'],
            'retained original source archive digest')
    return True


def verify_initial_append(root, base, check_database=True, require_database=False):
    attempt = base / 'append-attempt-01'
    verify_manifest(attempt)
    plan = read(base / 'append-plan.json')
    run = read(attempt / 'run.json')
    require(plan['scope'] == 'non-scored-versioned-adapter-append-heuristic-feasibility' and
            plan['scored_activation'] is False, 'initial append plan scope')
    require(run['scope'] == plan['scope'] and run['scored_activation'] is False and
            run['plan_sha256'] == sha(base / 'append-plan.json') and 'error' not in run,
            'initial append run promotion or plan join')
    verify_bound_inputs(root, [plan['queries'], plan['runner_files']])
    query_inputs = {name: digest for name, digest in plan['queries'].items()}
    check_query_snapshots(attempt, root, query_inputs)

    phase = run.get('phases', {}).get('append-flow')
    require(isinstance(phase, dict), 'initial append phase missing')
    check_phase(phase, 60, query=True)
    require(phase.get('scratch_cleanup_authorized') is False and
            phase.get('memory_compliance') == 'unproven', 'initial append diagnostic scope')
    require(read(attempt / 'append-flow.command.json') == phase, 'initial append phase witness join')
    decode = read(attempt / 'append-flow-decode.command.json')
    check_phase(decode, 60)
    require('--database=' + str(Path(plan['database'])) in phase.get('argv', []),
            'initial append did not query retained database')
    expected = {tuple(flow + [profile]) for profile, flows in plan['expected_flows'].items()
                for flow in flows}
    actual_rows = rows(attempt / 'append-flow.json')
    require(len(actual_rows) == len({tuple(row) for row in actual_rows}) and
            {tuple(row) for row in actual_rows} == expected,
            'initial append rows or wrong-arity near miss')
    database_verified = (verify_original_database(plan, run, require_database)
                         if check_database else False)
    return {'package': 'append-attempt-01', 'original_database_hashes_verified': database_verified}


def check_archive(archive_path, expected_source):
    with zipfile.ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if name.endswith('/source/main.swift')]
        require(len(members) == 1, 'source archive membership')
        data = archive.read(members[0])
    require(data == expected_source, 'archived source differs from preregistered source')
    return members[0], hashlib.sha256(data).hexdigest()


def verify_append_body(root, base):
    attempt = base / 'append-body-attempt-01'
    probe = attempt / 'probe'
    verify_manifest(attempt)
    verify_manifest(probe)
    plan = read(base / 'append-body-plan.json')
    run = read(attempt / 'run.json')
    require(plan['scope'] == 'non-scored-resolved-append-body-preservation-control' and
            plan['scored_activation'] is False and
            plan['aggregate_memory_compliance'] == plan['semantic_completeness'] == 'unproven',
            'append-body plan scope')
    require(run['scope'] == plan['scope'] and run['scored_activation'] is False and
            run['status'] == 'unqualified' and run['exit_status'] == 0 and
            run['plan_sha256'] == sha(base / 'append-body-plan.json'),
            'append-body run promotion or plan join')
    mappings = [plan['control_files'], plan['query_files'], plan['runner_files']]
    if plan.get('vendor_files'):
        mappings.append(plan['vendor_files'])
    verify_bound_inputs(root, mappings)
    check_query_snapshots(probe, root, plan['query_files'])

    control = root / 'evidence/swift-resolved-native-v1/append-body-control'
    control_json = read(control / 'control.json')
    case = read(probe / 'case.json')
    witness = read(probe / 'witness.json')
    require(case == control_json and case['scope'] == 'non-scored-control' and
            witness['case_sha256'] == plan['control_files'][
                'evidence/swift-resolved-native-v1/append-body-control/control.json'] and
            witness['population_member'] is False and witness['unqualified_feasibility'] is False,
            'append-body control provenance or promotion')
    require(witness['extraction_policy_sha256'] == plan['runner_files'][plan['policy']],
            'append-body extraction policy identity')
    check_phase_bundle(probe, witness, APPEND_BODY_PHASES)

    source = (control / 'main.swift').read_bytes()
    require(sha(control / 'main.swift') == plan['control_files'][
            'evidence/swift-resolved-native-v1/append-body-control/main.swift'],
            'append-body control source digest')
    check_archive(base / 'append-body-source.zip', source)
    require((probe / 'main.swift').read_bytes() == source, 'append-body staged source differs')

    labels = plan['control_labels']
    sink_lines = {line for name, line in labels.items() if name.endswith('_SINK')}
    role_rows = rows(probe / 'roles.json')
    require(all(len(row) == 4 and row[2] in ('vendor-native', 'adapter-corrected') and
                row[3] in ('environment', 'source', 'sink') for row in role_rows),
            'unknown append-body role lane')
    corrected = [row for row in role_rows if row[2] == 'adapter-corrected']
    require(any(row[0] == labels['SOURCE'] and row[3] in ('environment', 'source')
                for row in corrected), 'append-body source role missing')
    require({row[0] for row in corrected if row[3] == 'sink'} == sink_lines,
            'append-body sink role set')
    identity_rows = rows(probe / 'identity.json')
    require(any(row[:5] == [labels['SOURCE'], 'Foundation', 'Foundation',
                            'ProcessInfo', 'environment'] for row in identity_rows),
            'append-body resolved source identity missing')

    expected_flows = {
        tuple([labels['SOURCE'], labels[sink], 87, profile])
        for profile, names in plan['expected_sink_labels'].items() for sink in names
    }
    flow_rows = rows(probe / 'append-flow.json')
    profiles = {'adapter-corrected-stock', 'adapter-resolved-experiment'}
    require(all(len(row) == 4 and row[3] in profiles for row in flow_rows),
            'unknown append-body flow lane')
    require(len(flow_rows) == len({tuple(row) for row in flow_rows}) and
            {tuple(row) for row in flow_rows} == expected_flows,
            'append-body flow rows, missing ordinary body flow, or rewritten near miss')
    return {'package': 'append-body-attempt-01', 'body_control_flow_rows': len(flow_rows)}


def verify_canonical(root, base):
    attempt = base / 'canonical-append-attempt-01'
    verify_manifest(attempt)
    plan = read(root / CANONICAL_PLAN_REL)
    run = read(attempt / 'run.json')
    require(plan['scope'] == 'non-scored-canonical-qualification' and
            plan['scored_activation'] is False and
            (plan['extraction_seconds'], plan['analysis_seconds'],
             plan['analysis_memory_mb']) == (150, 60, 2048), 'canonical plan scope/budget')
    require(set(plan['runner_files']) == {
            'scripts/run-swift-resolved-append-qualification.py',
            'scripts/probe-swift-v2-codeql.py', 'scripts/swift_v2_process.py',
            'scripts/swift_extraction_integrity.py', 'scripts/swift_population_v2.py',
            'scripts/verify-swift-native-integration.py'}, 'canonical runner closure')
    verify_bound_inputs(root, [plan['runner_files'], plan['query_files']])
    require(run['scope'] == plan['scope'] and run['scored_activation'] is False and
            run['status'] == 'retained-non-scored-attempts' and 'error' not in run and
            run['plan_sha256'] == sha(root / CANONICAL_PLAN_REL) and
            run['configuration']['configuration_hash'] == plan['configuration_hash'] and
            run['configuration']['scored_outcomes'] == 0,
            'canonical run promotion/plan join')
    require([item['case_id'] for item in run['attempts']] == plan['cases'] and
            all(item['status'] == 'observed-unqualified' for item in run['attempts']),
            'canonical pair incomplete or promoted')

    assets = read(root / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
    runtime = read(attempt / 'runtime.json')
    require(runtime['assets'] == assets and
            runtime['sdk_settings_sha256'] == plan['sdk_settings_sha256'] and
            runtime['pack_files_verified'] == len(read(
                root / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')),
            'canonical runtime witness')
    prior = read(root / 'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    require(runtime['compiler_sha256'] == prior['compiler_sha256'], 'canonical compiler identity')
    version = read(attempt / 'version.json')
    require(version['version'] == '2.27.1' and
            version['sha'] == '938af3639d0709b587251e45d9f8d2bdc3505696',
            'canonical CodeQL version')

    population = read(root / 'populations/swift-synthetic-v2.json')
    entries = {entry['id']: entry for entry in population['cases']}
    require(set(plan['cases']) <= set(entries), 'canonical population case missing')
    for case_id in plan['cases']:
        entry = entries[case_id]
        directory = attempt / case_id
        case_path = checked(root, entry['path'])
        case = read(case_path)
        source = (case_path.parent / 'main.swift').read_bytes()
        join = read(directory / 'canonical-join.json')
        require(join == {'case_id': case_id, 'canonical_entry': entry,
                         'population': population['population'],
                         'fixture_revision': population['fixture_revision'],
                         'staged_source_sha256': entry['fixture_digests'][0]['sha256']} and
                (directory / 'canonical-case.json').read_bytes() == case_path.read_bytes(),
                'canonical population join/metadata')
        require(hashlib.sha256(source).hexdigest() == entry['fixture_digests'][0]['sha256'],
                'canonical source fixture digest')
        probe = directory / 'probe'
        verify_manifest(probe)
        require((directory / 'control/main.swift').read_bytes() == source and
                (probe / 'main.swift').read_bytes() == source, 'canonical source changed')
        witness = read(probe / 'witness.json')
        require(witness['source_commit'] == run['source_commit'] and
                witness['status'] == 'unqualified' and witness['population_member'] is False and
                witness.get('probe_error') in (None, '') and witness.get('cleanup_error') in (None, '') and
                witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048} and
                witness['extraction_phase_deadline_seconds'] == 150 and
                witness['compiler_sha256'] == runtime['compiler_sha256'],
                'canonical probe witness scope')
        check_phase_bundle(probe, witness, CANONICAL_PHASES)
        for name in plan['query_files']:
            query = probe / 'queries' / Path(name).name
            require(query.is_file() and query.read_bytes() == checked(root, name).read_bytes(),
                    'canonical query snapshot provenance: ' + name)
        query_names = {path.name for path in (probe / 'queries').iterdir() if path.is_file()}
        require(query_names == {Path(name).name for name in plan['query_files']},
                'canonical query snapshot file set')

        observation = read(directory / 'observation.json')
        require(observation['status'] == 'observed-unqualified' and
                observation['scored_activation'] is False and
                observation['aggregate_memory_compliance'] ==
                observation['semantic_completeness'] == 'unproven',
                'canonical observation promotion')
        archive = directory / 'source.zip'
        archive_member, source_digest = check_archive(archive, source)
        require(observation['archive_member'] == archive_member and
                observation['archive_sha256'] == sha(archive) and
                observation['source_sha256'] == source_digest == join['staged_source_sha256'],
                'canonical source archive identity')

        source_line = case['source_anchors'][0]['line_hint']
        sink_line = case['sink_anchors'][0]['line_hint']
        roles = rows(probe / 'roles.json')
        flows = rows(probe / 'flow.json')
        identities = rows(probe / 'identity.json')
        require(any(row[:5] == [source_line, 'Foundation', 'Foundation',
                                'ProcessInfo', 'environment'] for row in identities),
                'canonical resolved source identity missing')
        require(all(len(row) == 4 and row[2] in LANES.values() and
                    row[3] in ('environment', 'source', 'sink') for row in roles),
            'unknown canonical role lane')
        require(all(len(row) == 4 and row[3] in LANES.values() for row in flows),
                'unknown canonical flow lane')

        projected = {}
        for lane, profile in LANES.items():
            source_rows = [row for row in roles if row[2] == profile and row[3] != 'sink']
            sink_rows = [row for row in roles if row[2] == profile and row[3] == 'sink']
            flow_rows = [row for row in flows if row[3] == profile]
            require(all(row[0] == sink_line for row in sink_rows), 'unexpected canonical sink location')
            require(all(row[0] == source_line and
                        any(sink[0:2] == row[1:3] for sink in sink_rows)
                        for row in flow_rows), 'unjoined canonical flow')
            projected[lane] = {'source_rows': source_rows, 'sink_rows': sink_rows,
                               'flow_rows': flow_rows,
                               'source_anchor_recognized': any(row[0] == source_line
                                                               for row in source_rows),
                               'sink_anchor_recognized': bool(sink_rows),
                               'observed_anchor_flow': bool(flow_rows)}
        require(observation['lanes'] == projected, 'canonical lane projection drift')
        vendor = projected['vendor-native']
        require(vendor['source_rows'] == [] and vendor['flow_rows'] == [],
                'vendor-native source/flow unexpectedly present')
        expected_flow = case['polarity'] == 'positive'
        for lane in ('adapter-assisted-stock', 'adapter-resolved-experiment'):
            require(projected[lane]['observed_anchor_flow'] is expected_flow,
                    'canonical adapter flow expectation: ' + lane + '/' + case['polarity'])

        measurements = observation['phase_measurements']
        for phase in ('database-create', 'roles', 'flow', 'identity'):
            record = witness['phases'][phase]
            text = (probe / (phase + '.stderr')).read_text()
            rss = re.search(r'(\d+)\s+maximum resident set size', text)
            require(measurements[phase] == {
                'elapsed_seconds': record.get('elapsed_seconds'),
                'command_maxrss_bytes': int(rss[1]) if rss else None},
                'canonical phase measurement join: ' + phase)
    return {'package': 'canonical-append-attempt-01', 'cases': len(plan['cases']),
            'scored_activation': False}


def verify(evidence_root=None, root=ROOT, check_original_database=True,
           require_original_database=False):
    root = Path(root).resolve()
    base = Path(evidence_root).resolve() if evidence_root else root / BASE_REL
    initial = verify_initial_append(root, base, check_original_database,
                                    require_original_database)
    body = verify_append_body(root, base)
    canonical = verify_canonical(root, base)
    return {'scope': 'non-scored diagnostic evidence', 'packages': [initial, body, canonical],
            'qualification': 'not established', 'whole_library_qualification': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path,
                        help='root containing append-plan.json and the three attempt directories')
    parser.add_argument('--require-original-database', action='store_true',
                        help='fail when the retained original database is unavailable for rehashing')
    args = parser.parse_args()
    report = verify(args.evidence_root, require_original_database=args.require_original_database)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
