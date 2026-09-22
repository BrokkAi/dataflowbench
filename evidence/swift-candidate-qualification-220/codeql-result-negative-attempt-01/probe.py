#!/usr/bin/env python3
"""Non-scored, bounded CodeQL structural probes; no fixture binary execution."""
import argparse
import gzip
import json
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from swift_population_v2 import ROOT, audit, sha

import swift_v2_process as commands


def database_ready(record, metadata, resolved, database):
    """Gate query progress on successful command and finalized artifact, not containment."""
    return (record['exit_status'] == 0 and not record['timed_out']
            and record['cleanup_status'] == 'tracked-processes-stopped'
            and len(re.findall(r'^finalised: true$', metadata, re.MULTILINE)) == 1
            and not re.search(r'^inProgress:', metadata, re.MULTILINE)
            and resolved.get('languages') == ['swift']
            and Path(resolved.get('datasetFolder', '')).resolve() == (database / 'db-swift').resolve()
            and (database / 'db-swift').is_dir())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codeql', type=Path, required=True)
    parser.add_argument('--packs', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--case-id')
    selection.add_argument('--control-directory', type=Path)
    parser.add_argument('--query-directory', type=Path, default=ROOT / 'evidence/swift-v2-qualification-220/codeql-probes')
    parser.add_argument('--probe-queries', nargs='+', default=['declarations', 'catalog'])
    parser.add_argument('--extraction-timeout', type=int, default=60)
    parser.add_argument('--unqualified-feasibility', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.extraction_timeout <= 300 or (args.extraction_timeout != 60 and not args.unqualified_feasibility):
        parser.error('a non-default extraction deadline requires explicit unqualified feasibility scope (maximum300s)')
    if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', name) for name in args.probe_queries):
        parser.error('probe query names must be simple identifiers')
    manifest, additions = audit()
    if args.control_directory:
        path = args.control_directory.resolve() / 'control.json'
        case = json.loads(path.read_text())
        if case.get('scope') != 'non-scored-control' or not case['id'].startswith('control-') or case['fixture_files'] != ['main.swift'] or case['execution_budget'] != {'peak_memory_mb': 512, 'wall_clock_seconds': 60}:
            parser.error('external controls require explicit non-scored identity, one Swift input, and unchanged budgets')
    else:
        path, case = next((p, c) for p, c in additions if c['id'] == args.case_id)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    compiler = subprocess.check_output(['xcrun', '--find', 'swiftc'], text=True).strip()
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    queries = args.query_directory.resolve()
    shutil.copytree(queries, output / 'queries')
    shutil.copyfile(__file__, output / 'probe.py')
    shutil.copyfile(ROOT / 'scripts/swift_v2_process.py', output / 'process-runner.py')
    shutil.copyfile(path, output / 'case.json')
    for name in case['fixture_files']: shutil.copyfile(path.parent / name, output / name)
    witness = {'scope': 'non-scored structural observations; no flow or unsupported qualification',
               'case_id': case['id'], 'population': None if args.control_directory else manifest['population'],
               'fixture_revision': None if args.control_directory else manifest['fixture_revision'],
               'population_member': not bool(args.control_directory),
               'case_sha256': sha(path), 'compiler_sha256': sha(Path(compiler).resolve()),
               'extractor_sha256': sha(args.codeql.parent / 'swift/tools/osx64/extractor.real'),
               'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'budget': case['execution_budget'], 'extraction_phase_deadline_seconds': args.extraction_timeout,
               'unqualified_feasibility': args.unqualified_feasibility, 'query_phase_deadline_seconds': 60, 'memory_compliance': 'unproven', 'phases': {}}
    (output / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    scratch = Path(tempfile.mkdtemp(prefix='dfb-v2-codeql-'))
    witness['retained_scratch'] = str(scratch)
    try:
        source = scratch / 'source'; source.mkdir(); db = scratch / 'db'
        for name in case['fixture_files']: shutil.copyfile(path.parent / name, source / name)
        compile_argv = [compiler, '-swift-version', '6', '-Onone', '-sdk', sdk, '-target', 'arm64-apple-macosx27.0.0', '-module-name', 'DataFlowBenchTaintSwift', '-module-cache-path', str(scratch / 'cache')] + [str(source / name) for name in case['fixture_files']] + ['-o', str(scratch / 'never-executed')]
        try:
            argv = [str(args.codeql), 'database', 'create', str(db), '--language=swift', '--source-root=' + str(source), '--threads=2', '--ram=512', '--command=' + shlex.join(compile_argv)]
            record = commands.run(argv, output, 'database-create', args.extraction_timeout, measure=True)
            witness['phases']['database-create'] = record
            if record['exit_status'] != 0 or record['timed_out']:
                raise RuntimeError('extraction did not complete normally; stop and retain scratch for reconciliation')
            resolved_record = commands.run([str(args.codeql), 'resolve', 'database', '--format=json', str(db)], output, 'database-resolve', 60)
            witness['phases']['database-resolve'] = resolved_record
            if resolved_record['exit_status'] != 0 or resolved_record['timed_out']:
                raise RuntimeError('database metadata resolution failed')
            resolved = json.loads((output / 'database-resolve.stdout').read_text())
            if not database_ready(record, (db / 'codeql-database.yml').read_text(), resolved, db):
                raise RuntimeError('database is not a finalized Swift artifact from this invocation')
            witness['database_validation'] = 'finalized-swift-artifact; no containment claim'
            for name in args.probe_queries:
                bqrs = output / (name + '.bqrs')
                argv = [str(args.codeql), 'query', 'run', str(output / 'queries' / (name + '.ql')), '--database=' + str(db), '--output=' + str(bqrs), '--additional-packs=' + str(args.packs), '--threads=2', '--ram=512', '--timeout=60']
                result = commands.run(argv, output, name, 60, measure=True)
                witness['phases'][name] = result
                if result['exit_status'] != 0 or result['timed_out']:
                    raise RuntimeError('query failed or timed out; stop and retain scratch')
                if result['exit_status'] == 0 and not result['timed_out']:
                    commands.run([str(args.codeql), 'bqrs', 'decode', str(bqrs), '--format=json', '--output=' + str(output / (name + '.json'))], output, name + '-decode', 60)
        finally:
            if db.exists():
                for name in ['log', 'diagnostic']:
                    if (db / name).exists(): shutil.copytree(db / name, output / name)
                if (db / 'codeql-database.yml').exists(): shutil.copyfile(db / 'codeql-database.yml', output / 'codeql-database.yml')
    except commands.ProcessCleanupError as error:
        witness['cleanup_error'] = str(error)
        witness['retained_scratch'] = str(scratch)
    except Exception as error:
        witness['probe_error'] = str(error)
        witness['retained_scratch'] = str(scratch)
    witness['status'] = 'unqualified'
    (output / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    for log in output.rglob('*.log'):
        data = log.read_bytes(); compressed = gzip.compress(data, mtime=0)
        assert gzip.decompress(compressed) == data
        log.with_suffix('.log.txt.gz').write_bytes(compressed); log.unlink()
    (output / 'manifest.json').write_text(json.dumps({str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}, indent=2) + '\n')
    print(json.dumps({name: {'exit': r['exit_status'], 'timeout': r['timed_out'], 'rss_mb': r.get('time_maxrss_mb')} for name, r in witness['phases'].items()}), flush=True)


if __name__ == '__main__': main()
