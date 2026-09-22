#!/usr/bin/env python3
"""Non-scored, bounded CodeQL structural probes; no fixture binary execution."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from swift_population_v2 import ROOT, audit, sha

import swift_v2_process as commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codeql', type=Path, required=True)
    parser.add_argument('--packs', type=Path, required=True)
    parser.add_argument('--case-id', required=True)
    args = parser.parse_args()
    manifest, additions = audit()
    path, case = next((p, c) for p, c in additions if c['id'] == args.case_id)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    compiler = subprocess.check_output(['xcrun', '--find', 'swiftc'], text=True).strip()
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    queries = ROOT / 'evidence/swift-v2-qualification-220/codeql-probes'
    shutil.copytree(queries, output / 'queries')
    shutil.copyfile(__file__, output / 'probe.py')
    shutil.copyfile(ROOT / 'scripts/swift_v2_process.py', output / 'process-runner.py')
    shutil.copyfile(path, output / 'case.json')
    for name in case['fixture_files']: shutil.copyfile(path.parent / name, output / name)
    witness = {'scope': 'non-scored structural observations; no flow or unsupported qualification',
               'case_id': case['id'], 'population': manifest['population'], 'fixture_revision': manifest['fixture_revision'],
               'case_sha256': sha(path), 'compiler_sha256': sha(Path(compiler).resolve()),
               'extractor_sha256': sha(args.codeql.parent / 'swift/tools/osx64/extractor.real'),
               'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'budget': case['execution_budget'], 'memory_compliance': 'unproven', 'phases': {}}
    (output / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    scratch = Path(tempfile.mkdtemp(prefix='dfb-v2-codeql-'))
    cleanup_safe = True
    try:
        source = scratch / 'source'; source.mkdir(); db = scratch / 'db'
        for name in case['fixture_files']: shutil.copyfile(path.parent / name, source / name)
        compile_argv = [compiler, '-swift-version', '6', '-Onone', '-sdk', sdk, '-target', 'arm64-apple-macosx27.0.0', '-module-name', 'DataFlowBenchTaintSwift', '-module-cache-path', str(scratch / 'cache')] + [str(source / name) for name in case['fixture_files']] + ['-o', str(scratch / 'never-executed')]
        try:
            argv = [str(args.codeql), 'database', 'create', str(db), '--language=swift', '--source-root=' + str(source), '--threads=2', '--ram=512', '--command=' + shlex.join(compile_argv)]
            record = commands.run(argv, output, 'database-create', 60, measure=True)
            witness['phases']['database-create'] = record
            if record['exit_status'] == 0 and not record['timed_out']:
                for name in ['declarations', 'catalog']:
                    bqrs = output / (name + '.bqrs')
                    argv = [str(args.codeql), 'query', 'run', str(output / 'queries' / (name + '.ql')), '--database=' + str(db), '--output=' + str(bqrs), '--additional-packs=' + str(args.packs), '--threads=2', '--ram=512', '--timeout=60']
                    result = commands.run(argv, output, name, 60, measure=True)
                    witness['phases'][name] = result
                    if result['exit_status'] == 0 and not result['timed_out']:
                        commands.run([str(args.codeql), 'bqrs', 'decode', str(bqrs), '--format=json', '--output=' + str(output / (name + '.json'))], output, name + '-decode', 60)
        finally:
            if db.exists():
                for name in ['log', 'diagnostic']:
                    if (db / name).exists(): shutil.copytree(db / name, output / name)
                if (db / 'codeql-database.yml').exists(): shutil.copyfile(db / 'codeql-database.yml', output / 'codeql-database.yml')
    except commands.ProcessCleanupError as error:
        cleanup_safe = False
        witness['cleanup_error'] = str(error)
        witness['retained_scratch'] = str(scratch)
    except Exception as error:
        witness['probe_error'] = str(error)
        cleanup_safe = False
        witness['retained_scratch'] = str(scratch)
    finally:
        if cleanup_safe:
            shutil.rmtree(scratch)
    witness['status'] = 'unqualified'
    (output / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    for log in output.rglob('*.log'):
        data = log.read_bytes(); compressed = gzip.compress(data, mtime=0)
        assert gzip.decompress(compressed) == data
        log.with_suffix('.log.txt.gz').write_bytes(compressed); log.unlink()
    (output / 'manifest.json').write_text(json.dumps({str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}, indent=2) + '\n')
    print(json.dumps({name: {'exit': r['exit_status'], 'timeout': r['timed_out'], 'rss_mb': r.get('time_maxrss_mb')} for name, r in witness['phases'].items()}), flush=True)


if __name__ == '__main__': main()
