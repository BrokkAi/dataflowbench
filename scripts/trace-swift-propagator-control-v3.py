#!/usr/bin/env python3
"""Bounded read-only diagnosis of the retained failed append near-miss."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import swift_v2_process as commands

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-propagator-qualification-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def main():
    cli, packs, out = map(Path, sys.argv[1:])
    plan = read(BASE / 'trace-plan-v3.json'); db = Path(plan['database'])
    for field in ['queries', 'runner_files']:
        for name, digest in plan[field].items():
            if sha(ROOT / name) != digest:
                raise ValueError('changed preregistered input: ' + name)
    actual = {str(p.relative_to(db)) for p in (db / 'db-swift').rglob('*') if p.is_file() and not str(p.relative_to(db)).startswith('db-swift/default/cache/')}
    if actual != set(plan['dataset_files']):
        raise ValueError('changed source-data file set')
    for name, digest in plan['dataset_files'].items():
        if sha(db / name) != digest:
            raise ValueError('changed retained dataset: ' + name)
    if sha(db / 'src.zip') != plan['source_archive_sha256']:
        raise ValueError('changed source archive')
    paths = list(plan['queries']) + list(plan['runner_files']) + [str((BASE / 'trace-plan-v3.json').relative_to(ROOT))]
    subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths], cwd=ROOT, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=ROOT, check=True)
    assets = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
    if sha(cli) != assets['codeql/codeql']:
        raise ValueError('CLI identity changed')
    for row in read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json'):
        if sha(packs / row['path']) != row['sha256']:
            raise ValueError('pack identity changed')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(BASE / 'trace-queries-v2', out / 'queries')
    record = {'scope': plan['scope'], 'plan_sha256': sha(BASE / 'trace-plan-v3.json'),
              'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'scored_activation': False, 'phases': {}}
    try:
        for name in ['summaries', 'path']:
            bqrs = out / (name + '.bqrs')
            argv = [str(cli), 'query', 'run', str(out / 'queries' / (name + '.ql')),
                    '--database=' + str(db), '--output=' + str(bqrs), '--additional-packs=' + str(packs),
                    '--threads=2', '--ram=2048', '--timeout=60']
            result = commands.run(argv, out, name, 60, measure=True)
            record['phases'][name] = result
            if result['exit_status'] != 0 or result['timed_out']:
                break
            result = commands.run([str(cli), 'bqrs', 'decode', str(bqrs), '--format=json',
                                   '--output=' + str(out / (name + '.json'))], out, name + '-decode', 60)
            record['phases'][name + '-decode'] = result
    finally:
        (out / 'run.json').write_text(json.dumps(record, indent=2) + '\n')
        (out / 'manifest.json').write_text(json.dumps({str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}, indent=2) + '\n')


if __name__ == '__main__':
    main()
