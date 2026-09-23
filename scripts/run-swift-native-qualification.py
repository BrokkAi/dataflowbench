#!/usr/bin/env python3
"""Run only the preregistered, non-scored canonical Swift source/sink pair."""
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
PLAN = ROOT / 'adapters/codeql/swift-native-v3/qualification-plan.json'
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
    config = integration.verify()
    plan = read(PLAN)
    require(plan['configuration_hash'] == config['configuration_hash'], 'configuration drift')
    require(plan['scope'] == 'non-scored-canonical-qualification' and plan['scored_activation'] is False, 'qualification scope')
    require((plan['extraction_seconds'], plan['analysis_seconds'], plan['analysis_memory_mb']) == (150, 60, 2048), 'phase policy')
    require(plan['cases'] == read(ROOT / integration.BASE / 'partition.json')['first_qualification_cases'], 'case selection')
    required = {'scripts/run-swift-native-qualification.py', 'scripts/probe-swift-v2-codeql.py',
                'scripts/swift_v2_process.py', 'scripts/swift_extraction_integrity.py',
                'scripts/swift_population_v2.py', 'scripts/verify-swift-native-integration.py'}
    require(set(plan['runner_files']) == required, 'runner closure')
    for name, digest in plan['runner_files'].items():
        require(sha(ROOT / name) == digest, 'runner digest: ' + name)
    if check_git:
        paths = sorted(required | set(read(ROOT / integration.BASE / 'inputs.json')) |
                       {str(PLAN.relative_to(ROOT))} |
                       {integration.BASE + '/' + n for n in ['activation.json', 'partition.json', 'inputs.json']})
        subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths], cwd=ROOT, stdout=subprocess.DEVNULL, check=True)
        subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=ROOT, check=True)
    return plan, config


def observe(attempt, case):
    witness = read(attempt / 'witness.json')
    require(not witness.get('probe_error') and not witness.get('cleanup_error'), 'probe failure')
    measurements = {}
    for phase in ['database-create', 'database-resolve', 'roles', 'flow', 'identity',
                  'roles-decode', 'flow-decode', 'identity-decode']:
        record = read(attempt / (phase + '.command.json'))
        require(record['exit_status'] == 0 and not record['timed_out'] and
                record['cleanup_status'] == 'tracked-processes-stopped', 'phase failure: ' + phase)
        if phase in ['database-create', 'roles', 'flow', 'identity']:
            text = (attempt / (phase + '.stderr')).read_text()
            rss = re.search(r'(\d+)\s+maximum resident set size', text)
            measurements[phase] = {'elapsed_seconds': record.get('elapsed_seconds'),
                                   'command_maxrss_bytes': int(rss[1]) if rss else None}
    require(witness['extraction_integrity']['ready_for_observation'] and
            inspect_logs(attempt / 'log/swift/extractor')['ready_for_observation'], 'extraction errors')
    require(witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048}
            and witness['extraction_phase_deadline_seconds'] == 150, 'phase policy drift')
    source = case['source_anchors'][0]['line_hint']
    sink = case['sink_anchors'][0]['line_hint']
    roles = read(attempt / 'roles.json')['#select']['tuples']
    flows = read(attempt / 'flow.json')['#select']['tuples']
    identities = read(attempt / 'identity.json')['#select']['tuples']
    require(any(r[:5] == [source, 'Foundation', 'Foundation', 'ProcessInfo', 'environment']
                for r in identities), 'resolved canonical environment identity missing')
    require(all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles), 'unknown role profile')
    require(all(r[3] in ['vendor-native', 'adapter-corrected'] for r in flows), 'unknown flow profile')
    result = {}
    for lane, profile in [('vendor-native', 'vendor-native'), ('adapter-assisted', 'adapter-corrected')]:
        sources = [r for r in roles if r[2] == profile and r[3] != 'sink']
        sinks = [r for r in roles if r[2] == profile and r[3] == 'sink']
        pairs = [r for r in flows if r[3] == profile]
        require(all(r[0] == sink for r in sinks), 'unexpected sink location')
        require(all(r[0] == source and any(s[0:2] == r[1:3] for s in sinks) for r in pairs), 'unjoined flow')
        result[lane] = {'source_rows': sources, 'sink_rows': sinks, 'flow_rows': pairs,
                        'source_anchor_recognized': any(r[0] == source for r in sources),
                        'sink_anchor_recognized': bool(sinks), 'observed_anchor_flow': bool(pairs)}
    archive = Path(witness['retained_scratch']) / 'db/src.zip'
    with zipfile.ZipFile(archive) as z:
        members = [n for n in z.namelist() if n.endswith('/source/main.swift')]
        require(len(members) == 1, 'source archive membership')
        data = z.read(members[0])
    require(data == (attempt / 'main.swift').read_bytes(), 'archived canonical source differs')
    return {'lanes': result, 'phase_measurements': measurements, 'archive_sha256': sha(archive), 'archive_member': members[0],
            'source_sha256': hashlib.sha256(data).hexdigest(), 'status': 'observed-unqualified',
            'aggregate_memory_compliance': 'unproven', 'semantic_completeness': 'unproven',
            'scored_activation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codeql', type=Path, required=True)
    parser.add_argument('--packs', type=Path, required=True)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    plan, config = verify_preregistration()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    run = {'scope': plan['scope'], 'configuration': config, 'plan_sha256': sha(PLAN),
           'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
           'scored_activation': False, 'attempts': [], 'status': 'incomplete'}
    try:
        assets = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
        require(sha(args.codeql) == assets['codeql/codeql'], 'CLI asset mismatch')
        require(sha(args.codeql.parent / 'swift/tools/osx64/extractor.real') == assets['codeql/swift/tools/osx64/extractor.real'], 'extractor mismatch')
        prior = read(ROOT / 'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
        require(sha(args.compiler) == prior['compiler_sha256'], 'compiler mismatch')
        require(sha(args.sdk / 'SDKSettings.json') == plan['sdk_settings_sha256'], 'SDK identity mismatch')
        pack_rows = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')
        for row in pack_rows:
            require(sha(args.packs / row['path']) == row['sha256'], 'pack mismatch: ' + row['path'])
        version = subprocess.run([str(args.codeql), 'version', '--format=json'], capture_output=True, text=True, timeout=10, check=True)
        write(out / 'version.json', json.loads(version.stdout))
        require(json.loads(version.stdout)['sha'] == '938af3639d0709b587251e45d9f8d2bdc3505696', 'binary build mismatch')
        write(out / 'runtime.json', {'assets': assets, 'compiler_sha256': sha(args.compiler),
              'sdk_settings_sha256': sha(args.sdk / 'SDKSettings.json'), 'pack_files_verified': len(pack_rows)})
        population = read(ROOT / 'populations/swift-synthetic-v2.json')
        for case_id in plan['cases']:
            entry = next(c for c in population['cases'] if c['id'] == case_id)
            case_path = ROOT / entry['path']; case = read(case_path)
            directory = out / case_id; directory.mkdir()
            control = directory / 'control'; control.mkdir()
            shutil.copyfile(case_path, directory / 'canonical-case.json')
            shutil.copyfile(case_path.parent / 'main.swift', control / 'main.swift')
            write(control / 'control.json', {'id': 'control-' + case_id, 'scope': 'non-scored-control',
                  'fixture_files': ['main.swift'], 'execution_budget': case['execution_budget']})
            join = {'case_id': case_id, 'canonical_entry': entry, 'population': population['population'],
                    'fixture_revision': population['fixture_revision'], 'staged_source_sha256': sha(control / 'main.swift')}
            require(join['staged_source_sha256'] == entry['fixture_digests'][0]['sha256'], 'staging mutation')
            write(directory / 'canonical-join.json', join)
            argv = [sys.executable, str(ROOT / 'scripts/probe-swift-v2-codeql.py'), '--output', str(directory / 'probe'),
                    '--codeql', str(args.codeql), '--packs', str(args.packs), '--compiler', str(args.compiler),
                    '--sdk', str(args.sdk), '--target', 'arm64-apple-macosx26.5', '--control-directory', str(control),
                    '--query-directory', str(ROOT / 'adapters/codeql/swift-foundation-sources-v1/queries'),
                    '--probe-queries', 'roles', 'flow', 'identity']
            write(directory / 'invocation.json', {'argv': argv})
            with (directory / 'runner.stdout').open('w') as stdout, (directory / 'runner.stderr').open('w') as stderr:
                execution = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
            try:
                require(execution.returncode == 0, 'probe driver failed')
                observation = observe(directory / 'probe', case)
            except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
                observation = {'status': 'inconclusive', 'reason': str(error), 'scored_activation': False}
            write(directory / 'observation.json', observation)
            run['attempts'].append({'case_id': case_id, 'status': observation['status']})
            print(case_id + ': ' + observation['status'], flush=True)
        run['status'] = 'retained-non-scored-attempts'
    except Exception as error:
        run['error'] = str(error)
    finally:
        write(out / 'run.json', run)
        write(out / 'manifest.json', {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    require('error' not in run, run.get('error', ''))


if __name__ == '__main__':
    main()
