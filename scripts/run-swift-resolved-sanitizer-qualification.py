#!/usr/bin/env python3
"""Retain a bounded, non-scored canonical native-sanitizer pair observation."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'adapters/codeql/swift-resolved-native-v1/canonical-sanitizer-plan.json'
QUERY_DIR = ROOT / 'adapters/codeql/swift-resolved-native-v1/canonical-sanitizer-queries-v1'
PROFILES = ('adapter-patched-resolved-sanitizer',)
QUERIES = ('roles', 'flow', 'identity', 'barriers', 'numeric-bases', 'conversion-identity')
spec = importlib.util.spec_from_file_location('integration', ROOT / 'scripts/verify-swift-native-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)
require = integration.require
read = integration.read


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def verify_preregistration(check_git=True):
    config = integration.verify(root=ROOT)
    plan = read(PLAN)
    require(plan['configuration_hash'] == config['configuration_hash'], 'immutable population configuration drift')
    require(plan['scope'] == 'non-scored-canonical-sanitizer-qualification' and plan['scored_activation'] is False,
            'qualification scope')
    require(plan['cases'] == ['dfb-taint-swift-native-sanitizer-positive',
                              'dfb-taint-swift-native-sanitizer-negative'], 'case selection')
    require(plan['population_entries'] == 104 and config['population_inputs'] == 104,
            'immutable 104-entry population')
    require(plan['flow_profiles'] == list(PROFILES), 'patched flow profile set')
    require(plan['runtime_scope'] == 'adapter-patched-library-not-vendor-native', 'patched runtime scope')
    require((plan['extraction_seconds'], plan['analysis_seconds'], plan['analysis_memory_mb']) == (150, 60, 2048),
            'phase policy')
    required = {'scripts/run-swift-resolved-sanitizer-qualification.py', 'scripts/probe-swift-v2-codeql.py',
                'scripts/swift_v2_process.py', 'scripts/swift_extraction_integrity.py',
                'scripts/swift_population_v2.py', 'scripts/verify-swift-native-integration.py'}
    require(set(plan['runner_files']) == required, 'runner closure')
    for name, digest in plan['runner_files'].items():
        require(sha(ROOT / name) == digest, 'runner digest: ' + name)
    for name, digest in plan['query_files'].items():
        require(sha(ROOT / name) == digest, 'query digest: ' + name)
    for name, digest in plan['input_files'].items():
        require(sha(ROOT / name) == digest, 'preregistered input digest: ' + name)
    population = read(ROOT / 'populations/swift-synthetic-v2.json')
    entries = {entry['id']: entry for entry in population['cases']}
    require(len(entries) == 104 and population['population'] == 'swift-synthetic-v2', 'population identity')
    for case_id in plan['cases']:
        entry = entries[case_id]
        case = read(ROOT / entry['path'])
        require(case['id'] == case_id and case['model_profile'] == 'tool-native' and
                case['score_tier'] == 'modeling', 'summary case identity')
        for fixture in entry['fixture_digests']:
            require(sha(ROOT / fixture['path']) == fixture['sha256'], 'case fixture digest: ' + fixture['path'])
    if check_git:
        paths = sorted(required | set(plan['query_files']) | set(plan['input_files']) |
                       {str(PLAN.relative_to(ROOT))})
        subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths], cwd=ROOT,
                       stdout=subprocess.DEVNULL, check=True)
        subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=ROOT, check=True)
    return plan, config, population


def inspect_phases(attempt, witness):
    phases = ['database-create', 'database-resolve'] + list(QUERIES) + [q + '-decode' for q in QUERIES]
    measurements = {}
    for phase in phases:
        record = read(attempt / (phase + '.command.json'))
        require(record.get('exit_status') == 0 and not record.get('timed_out') and
                record.get('cleanup_status') == 'tracked-processes-stopped' and not record.get('cleanup_error'),
                'phase failure or cleanup error: ' + phase)
        deadline = 150 if phase == 'database-create' else 60
        require(record.get('deadline_seconds') == deadline, 'phase deadline: ' + phase)
        argv = record.get('argv', [])
        if phase == 'database-create':
            require('--ram=512' in argv, 'extraction memory budget')
        elif phase in QUERIES:
            require('--ram=2048' in argv and '--timeout=60' in argv, 'analysis budget: ' + phase)
        if phase in ('database-create',) + QUERIES:
            stderr = (attempt / (phase + '.stderr')).read_text()
            rss = re.search(r'(\d+)\s+maximum resident set size', stderr)
            measurements[phase] = {'elapsed_seconds': record.get('elapsed_seconds'),
                                   'command_maxrss_bytes': int(rss[1]) if rss else None}
    require(set(witness.get('phases', {})) == {'database-create', 'database-resolve', *QUERIES},
            'witness phase closure')
    require(witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048} and
            witness['extraction_phase_deadline_seconds'] == 150, 'witness phase policy')
    return measurements


def observe(attempt, case, case_entry):
    witness = read(attempt / 'witness.json')
    require(not witness.get('probe_error') and not witness.get('cleanup_error'), 'probe failure')
    require(witness.get('population_member') is False and witness.get('scope', '').startswith('non-scored'),
            'control witness was scored')
    measurements = inspect_phases(attempt, witness)
    extraction = inspect_logs(attempt / 'log/swift/extractor')
    require(witness.get('extraction_integrity') == extraction and extraction['ready_for_observation'],
            'extractor log gate')
    source = case['source_anchors'][0]['line_hint']
    sink = case['sink_anchors'][0]['line_hint']
    roles = read(attempt / 'roles.json')['#select']['tuples']
    flows = read(attempt / 'flow.json')['#select']['tuples']
    identities = read(attempt / 'identity.json')['#select']['tuples']
    require(any(r[0] == source and r[1:5] == ['Foundation', 'Foundation', 'ProcessInfo', 'environment']
                for r in identities), 'resolved canonical environment identity missing')
    role_profiles = {r[2] for r in roles}
    flow_profiles = {r[3] for r in flows}
    require('vendor-native' not in role_profiles | flow_profiles, 'patched runtime mislabeled vendor-native')
    require(role_profiles == set(PROFILES), 'roles must emit the resolved sanitizer profile')
    require(flow_profiles <= set(PROFILES), 'unknown flow profile')
    expected = bool(case['expected_flows'])
    lanes = {}
    for profile in PROFILES:
        source_rows = [r for r in roles if r[2] == profile and r[3] != 'sink']
        sink_rows = [r for r in roles if r[2] == profile and r[3] == 'sink']
        pairs = [r for r in flows if r[3] == profile]
        require(source_rows and all(r[0] == source for r in source_rows), 'source role join: ' + profile)
        require(sink_rows and all(r[0] == sink for r in sink_rows), 'sink role join: ' + profile)
        require(all(r[0] == source and any(s[0:2] == [r[1], r[2]] for s in sink_rows) for r in pairs),
                'flow does not join source/sink roles: ' + profile)
        lanes[profile] = {'source_rows': source_rows, 'sink_rows': sink_rows, 'flow_rows': pairs,
                          'source_anchor_recognized': bool(source_rows), 'sink_anchor_recognized': bool(sink_rows),
                          'observed_anchor_flow': bool(pairs), 'matches_case_expectation': bool(pairs) == expected}
    summary = {}
    for name in ('barriers', 'numeric-bases', 'conversion-identity'):
        rows = read(attempt / (name + '.json'))['#select']['tuples']
        summary[name] = {'row_count': len(rows), 'rows': rows}
    archive = Path(witness['retained_scratch']) / 'db/src.zip'
    with zipfile.ZipFile(archive) as zipped:
        members = [name for name in zipped.namelist() if name.endswith('/source/main.swift')]
        require(len(members) == 1, 'source archive membership')
        archived = zipped.read(members[0])
    source_path = attempt / 'main.swift'
    require(archived == source_path.read_bytes(), 'archived source differs from staged canonical source')
    require(hashlib.sha256(archived).hexdigest() == case_entry['fixture_digests'][0]['sha256'],
            'archived source differs from immutable population fixture')
    return {'lanes': lanes, 'sanitizer_observations': summary, 'phase_measurements': measurements,
            'archive_sha256': sha(archive), 'archive_member': members[0],
            'source_sha256': hashlib.sha256(archived).hexdigest(), 'status': 'observed-unqualified',
            'aggregate_memory_compliance': 'unproven', 'semantic_completeness': 'unproven',
            'scored_activation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codeql', type=Path, required=True)
    parser.add_argument('--packs', type=Path, required=True, help='materialized swift-all 6.8.4-dfb.4 runtime')
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    plan, config, population = verify_preregistration()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    run = {'scope': plan['scope'], 'configuration': config, 'plan_sha256': sha(PLAN),
           'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
           'runtime_scope': plan['runtime_scope'], 'flow_profiles': list(PROFILES),
           'scored_activation': False, 'attempts': [], 'status': 'incomplete'}
    try:
        assets = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
        require(sha(args.codeql) == assets['codeql/codeql'], 'CLI asset mismatch')
        extractor = args.codeql.parent / 'swift/tools/osx64/extractor.real'
        require(sha(extractor) == assets['codeql/swift/tools/osx64/extractor.real'], 'extractor asset mismatch')
        prior = read(ROOT / 'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
        require(sha(args.compiler) == prior['compiler_sha256'], 'compiler asset mismatch')
        require(sha(args.sdk / 'SDKSettings.json') == plan['sdk_settings_sha256'], 'SDK identity mismatch')
        pack_manifest = read(ROOT / 'evidence/swift-resolved-native-v1/numeric-pack-manifest-v1.json')
        require(pack_manifest['scope'] == plan['runtime_scope'], 'patched runtime scope mismatch')
        pack_rows = pack_manifest['files']
        for row in pack_rows:
            require(sha(args.packs / row['path']) == row['sha256'], 'patched pack mismatch: ' + row['path'])
        require(any('swift-all/6.8.4-dfb.4/' in row['path'] for row in pack_rows), 'v3 Swift pack missing')
        version = subprocess.run([str(args.codeql), 'version', '--format=json'], capture_output=True,
                                 text=True, timeout=10, check=True)
        version_record = json.loads(version.stdout)
        require(version_record['sha'] == '938af3639d0709b587251e45d9f8d2bdc3505696', 'CLI build mismatch')
        write(out / 'version.json', version_record)
        write(out / 'runtime.json', {'assets': assets, 'runtime_manifest_sha256': sha(
            ROOT / 'evidence/swift-resolved-native-v1/numeric-pack-manifest-v1.json'),
            'compiler_sha256': sha(args.compiler), 'sdk_settings_sha256': sha(args.sdk / 'SDKSettings.json'),
            'pack_files_verified': len(pack_rows), 'pack_version': '6.8.4-dfb.4'})
        for case_id in plan['cases']:
            entry = next(row for row in population['cases'] if row['id'] == case_id)
            case_path = ROOT / entry['path']; case = read(case_path)
            directory = out / case_id; directory.mkdir()
            control = directory / 'control'; control.mkdir()
            shutil.copyfile(case_path, directory / 'canonical-case.json')
            shutil.copyfile(case_path.parent / 'main.swift', control / 'main.swift')
            write(control / 'control.json', {'id': 'control-' + case_id, 'scope': 'non-scored-control',
                  'fixture_files': ['main.swift'], 'execution_budget': case['execution_budget']})
            join = {'case_id': case_id, 'canonical_entry': entry, 'population': population['population'],
                    'fixture_revision': population['fixture_revision'],
                    'staged_source_sha256': sha(control / 'main.swift')}
            require(join['staged_source_sha256'] == entry['fixture_digests'][0]['sha256'], 'staging mutation')
            write(directory / 'canonical-join.json', join)
            argv = [sys.executable, str(ROOT / 'scripts/probe-swift-v2-codeql.py'), '--output',
                    str(directory / 'probe'), '--codeql', str(args.codeql), '--packs', str(args.packs),
                    '--compiler', str(args.compiler), '--sdk', str(args.sdk), '--target',
                    'arm64-apple-macosx26.5', '--control-directory', str(control), '--query-directory',
                    str(QUERY_DIR), '--probe-queries', *QUERIES]
            write(directory / 'invocation.json', {'argv': argv})
            with (directory / 'runner.stdout').open('w') as stdout, (directory / 'runner.stderr').open('w') as stderr:
                execution = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
            try:
                require(execution.returncode == 0, 'probe driver failed')
                observation = observe(directory / 'probe', case, entry)
                witness = read(directory / 'probe/witness.json')
                shutil.copyfile(Path(witness['retained_scratch']) / 'db/src.zip', directory / 'source.zip')
            except (ValueError, KeyError, OSError, zipfile.BadZipFile, StopIteration) as error:
                observation = {'status': 'inconclusive', 'reason': str(error), 'scored_activation': False}
            write(directory / 'observation.json', observation)
            run['attempts'].append({'case_id': case_id, 'status': observation['status']})
            print(case_id + ': ' + observation['status'], flush=True)
        run['status'] = 'retained-non-scored-attempts'
    except Exception as error:
        run['error'] = str(error)
    finally:
        write(out / 'run.json', run)
        write(out / 'manifest.json', {str(path.relative_to(out)): sha(path)
              for path in sorted(out.rglob('*')) if path.is_file()})
    require('error' not in run, run.get('error', ''))


if __name__ == '__main__':
    main()
