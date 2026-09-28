#!/usr/bin/env python3
"""Serial non-scored endpoint diagnostics; preserve canonical and historical bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import time
import zipfile

import swift_v2_process as process
from swift_v3_runner75 import enforce_deadline
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'adapters/codeql/swift-endpoint-diagnostic-v1'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
        return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def invoke(argv, directory, name, deadline):
    record = process.run(argv, directory, name, deadline)
    enforce_deadline(record, deadline)
    require(record['exit_status'] == 0, 'CommandFailed:' + name)
    return record


def failure_stop(error):
    return ('StoppedAfterUncertainCleanup'
            if isinstance(error, (TimeoutError, process.ProcessCleanupError))
            else 'StoppedAfterDiagnosticFailure')


def main():
    from swift_artifact_closure import snapshot, compare
    from swift_endpoint_diagnostic import classify
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['codeql', 'compiler', 'sdk', 'packs', 'retained', 'output']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    registration = read(ADAPTER / 'registration.json')
    plan = read(ADAPTER / 'plan.json')
    require(registration['resources'] == {'extraction_seconds': 150, 'analysis_total_seconds': 75,
            'requested_memory_mb': 2048, 'minimum_free_gib': 40,
            'aggregate_memory_compliance': 'unproven', 'descendant_containment': 'unproven'},
            'PreregisteredResourceMismatch')
    require(len(registration['retained_case_ids']) == 3 and len(plan['controls']) <= 5, 'BoundedSelectionMismatch')
    for name, digest in registration['files'].items():
        require(sha(ROOT / name) == digest, 'PreregistrationMismatch:' + name)
    registered = [*registration['files'], str((ADAPTER / 'registration.json').relative_to(ROOT))]
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *registered], cwd=ROOT, check=True)
    subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *registered], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    pins = read(ROOT / 'adapters/codeql/swift-opaque-v3/plan.json')
    for path, key in [(args.codeql, 'cli_sha256'), (args.compiler, 'compiler_sha256'),
                      (args.codeql.parent / 'swift/tools/osx64/extractor.real', 'extractor_sha256'),
                      (args.sdk / 'SDKSettings.json', 'sdk_settings_sha256')]:
        require(sha(path) == pins[key], 'RuntimePinMismatch:' + key)
    for row in read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json'):
        require(sha(args.packs / row['path']) == row['sha256'], 'PackPinMismatch:' + row['path'])
    query = ADAPTER / 'diagnostics.ql'
    resolved = subprocess.run([str(args.codeql), 'resolve', 'library-path', '--query=' + str(query),
                              '--additional-packs=' + str(args.packs), '--format=json'],
                             capture_output=True, text=True, check=True, timeout=30)
    require(str(args.packs / 'codeql/swift-all/6.8.4') in json.loads(resolved.stdout)['libraryPath'], 'ResolvedPackMismatch')
    output = args.output.resolve()
    output.relative_to(ROOT / 'reports/raw')
    require(shutil.disk_usage(ROOT).free >= 40 * 1024**3, 'InsufficientDiskReserve')
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'launch.json', {'scope': 'endpoint-diagnostics-only', 'scored_activation': False,
          'registration_sha256': sha(ADAPTER / 'registration.json'),
          'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'paths': {k: str(v) for k, v in vars(args).items()}, 'library_path': json.loads(resolved.stdout),
          'aggregate_memory_compliance': 'unproven', 'descendant_containment': 'unproven'})
    population = {r['id']: r for r in read(ROOT / 'populations/swift-synthetic-v3.json')['cases']}
    selections = [dict(id=cid, retained=True) for cid in registration['retained_case_ids']] + plan['controls']
    results = []
    sealed = []
    retained_sealed = []
    stop = None
    for selection in selections:
        identity = selection['id']
        directory = output / identity
        directory.mkdir()
        artifacts = directory / 'artifacts'
        artifacts.mkdir()
        result = {'id': identity, 'execution_status': 'not-attempted', 'scored_activation': False}
        analysis_start = None
        try:
            if stop:
                raise RuntimeError(stop)
            require(shutil.disk_usage(ROOT).free >= 40 * 1024**3, 'DiskReserveReached')
            for prior_directory, baseline in sealed:
                delta = compare(baseline, snapshot(prior_directory / 'artifacts'))
                if delta['status'] != 'CompleteArtifactClosure':
                    write(prior_directory / 'closure-before-next.json', delta)
                    raise ValueError('IncompleteArtifactClosure:' + prior_directory.name)
            result['execution_status'] = 'attempted'
            source = artifacts / 'source'
            source.mkdir()
            db = artifacts / 'database'
            if selection.get('retained'):
                entry = population[identity]
                casepath = ROOT / entry['path']
                case = read(casepath)
                anchors = [dict(file=a['file'], line=a['line_hint'], role=role)
                           for role, key in [('source', 'source_anchors'), ('sink', 'sink_anchors')]
                           for a in case[key]]
                for name in case['fixture_files']:
                    shutil.copyfile(casepath.parent / name, source / name)
                original = args.retained / identity
                require(sha(original / 'observation.json') == registration['retained_observations'][identity], 'RetainedObservationMismatch')
                require(read(original / 'observation.json')['execution_status'] == 'completed', 'RetainedExtractionIncomplete')
                original_snapshot = snapshot(original / 'database')
                write(directory / 'original-before.json', original_snapshot)
                retained_sealed.append((identity, original / 'database', original_snapshot))
                # APFS copy-on-write clone: no native query may mutate the retained database.
                subprocess.run(['/bin/cp', '-cR', str(original / 'database'), str(db)], check=True, timeout=120)
                require(original_snapshot['entries'] == snapshot(db)['entries'], 'ClonedDatabaseMismatch')
                write(directory / 'original-after.json', snapshot(original / 'database'))
                require(compare(original_snapshot, read(directory / 'original-after.json'))['status'] == 'CompleteArtifactClosure', 'OriginalClosureChanged')
                with zipfile.ZipFile(db / 'src.zip') as archive:
                    for name in case['fixture_files']:
                        matches = [n for n in archive.namelist() if n.endswith('/source/' + name)]
                        require(len(matches) == 1 and archive.read(matches[0]) == (source / name).read_bytes(), 'CanonicalSourceMismatch')
            else:
                anchors = selection['anchors']
                for name in selection['files']:
                    shutil.copyfile(ADAPTER / name, source / Path(name).name)
            def run(argv, name, deadline):
                return invoke(argv, artifacts, name, deadline)
            if not selection.get('retained'):
                compile_argv = [str(args.compiler), '-swift-version', '6', '-Onone', '-sdk', str(args.sdk),
                                '-target', 'arm64-apple-macosx26.5', '-module-name', selection.get('module', 'DataFlowBenchTaintSwift'),
                                '-module-cache-path', str(artifacts / 'cache')]
                compile_argv += [str(p) for p in sorted(source.glob('*.swift'))]
                compile_argv += ['-o', str(artifacts / 'never-executed')]
                run([str(args.codeql), 'database', 'create', str(db), '--language=swift', '--source-root=' + str(source),
                     '--threads=2', '--ram=2048', '--command=' + shlex.join(compile_argv)], 'extract', 150)
            require('finalised: true' in (db / 'codeql-database.yml').read_text(), 'DatabaseNotFinalized')
            require(inspect_logs(db / 'log/swift/extractor')['ready_for_observation'], 'ExtractionIncomplete')
            analysis_start = time.monotonic()
            run([str(args.codeql), 'query', 'run', str(query), '--database=' + str(db),
                 '--output=' + str(artifacts / 'diagnostics.bqrs'), '--additional-packs=' + str(args.packs),
                 '--threads=2', '--ram=2048', '--timeout=75'], 'query', 75)
            remaining = 75 - (time.monotonic() - analysis_start)
            if remaining <= 0:
                raise TimeoutError('BudgetExhausted:analysis')
            run([str(args.codeql), 'bqrs', 'decode', str(artifacts / 'diagnostics.bqrs'), '--format=json',
                 '--output=' + str(artifacts / 'diagnostics.json')], 'decode', remaining)
            if time.monotonic() - analysis_start > 75:
                raise TimeoutError('BudgetExhausted:analysis')
            result['endpoints'] = classify(read(artifacts / 'diagnostics.json')['#select']['tuples'], anchors)
            if 'expected_statuses' in selection:
                require([r['status'] for r in result['endpoints']] == selection['expected_statuses'], 'ControlExpectationMismatch')
            result['execution_status'] = 'completed'
        except Exception as error:
            result['failure'] = {'kind': type(error).__name__, 'message': str(error)}
            # Discovery is explicitly incomplete: after any failure stop the selection,
            # including timeout with no observed survivors. Never infer containment.
            stop = failure_stop(error)
        finally:
            if analysis_start is not None:
                result['analysis_elapsed_seconds'] = time.monotonic() - analysis_start
            try:
                before = snapshot(artifacts)
                write(directory / 'closure-before.json', before)
                time.sleep(1)
                after = snapshot(artifacts)
                write(directory / 'closure-after.json', after)
                delta = compare(before, after)
                result['closure'] = delta
                if delta['status'] != 'CompleteArtifactClosure':
                    stop = 'IncompleteArtifactClosure'
                    result['execution_status'] = 'incomplete'
                sealed.append((directory, before))
            except Exception as error:
                result['closure'] = {'status': 'IncompleteArtifactClosure', 'reason': str(error)}
                result['execution_status'] = 'incomplete'
                stop = 'IncompleteArtifactClosure'
            result['descendant_containment'] = 'unproven'
            write(directory / 'result.json', result)
            results.append(result)
            write(output / 'results.json', {'scope': 'diagnostic-only', 'scored_activation': False, 'results': results})
        print(identity + ': ' + result['execution_status'], flush=True)
    audits = []
    for directory, baseline in sealed:
        try:
            current = snapshot(directory / 'artifacts')
            write(directory / 'closure-final.json', current)
            delta = compare(baseline, current)
        except Exception as error:
            delta = {'status': 'IncompleteArtifactClosure', 'reason': str(error)}
        audits.append({'id': directory.name, **delta})
    original_audits = []
    for identity, original, baseline in retained_sealed:
        try:
            original_delta = compare(baseline, snapshot(original))
        except Exception as error:
            original_delta = {'status': 'IncompleteArtifactClosure', 'reason': str(error)}
        original_audits.append({'id': identity, **original_delta})
    write(output / 'closure-audit.json', {'cases': audits, 'retained_originals': original_audits, 'descendant_containment': 'unproven',
                                        'stable_snapshots_prove_containment': False})
    require(not stop and all(a['status'] == 'CompleteArtifactClosure' for a in audits + original_audits), 'DiagnosticAttemptIncomplete')


if __name__ == '__main__':
    main()
