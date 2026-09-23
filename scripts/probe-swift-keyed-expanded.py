#!/usr/bin/env python3
"""Preregistered expanded keyed-persistence controls; no fixture execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import shutil

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'evidence/swift-keyed-persistence-v1/expanded-plan-v1.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['output', 'codeql', 'packs', 'compiler', 'sdk']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    plan = read(PLAN)
    require(plan['scored_activation'] is False, 'non-scored scope')
    paths = [str(PLAN.relative_to(ROOT))]
    for field in ['control_files', 'query_files', 'vendor_files', 'runner_files']:
        for path, digest in plan[field].items():
            require(sha(ROOT / path) == digest, 'preregistered digest: ' + path)
            paths.append(path)
    subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths], cwd=ROOT, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=ROOT, check=True)
    assets = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
    require(sha(args.codeql) == assets['codeql/codeql'], 'CLI mismatch')
    require(sha(args.codeql.parent / 'swift/tools/osx64/extractor.real') == assets['codeql/swift/tools/osx64/extractor.real'], 'extractor mismatch')
    prior = read(ROOT / 'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    require(sha(args.compiler) == prior['compiler_sha256'], 'compiler mismatch')
    require(sha(args.sdk / 'SDKSettings.json') == plan['sdk_settings_sha256'], 'SDK mismatch')
    pack_rows = read(ROOT / 'evidence/swift-keyed-persistence-v1/pack-manifest-v1.json')['files']
    for row in pack_rows:
        require(sha(args.packs / row['path']) == row['sha256'], 'pack mismatch: ' + row['path'])
    out = args.output.resolve();out.mkdir(parents=True, exist_ok=False)
    record = {'scope': plan['scope'], 'plan_sha256': sha(PLAN), 'source_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'pack_files_verified': len(pack_rows),
        'compiler_sha256': sha(args.compiler), 'assets': assets, 'scored_activation': False}
    argv = [sys.executable, str(ROOT / 'scripts/probe-swift-v2-codeql.py'), '--output', str(out / 'probe'),
            '--codeql', str(args.codeql), '--packs', str(args.packs), '--compiler', str(args.compiler),
            '--sdk', str(args.sdk), '--target', 'arm64-apple-macosx26.5', '--control-directory',
            str(ROOT / 'evidence/swift-keyed-persistence-v1/expanded-control-v1'), '--query-directory',
            str(ROOT / 'evidence/swift-keyed-persistence-v1/queries-v1'), '--probe-queries', *plan['queries']]
    record['argv'] = argv
    try:
        with (out / 'runner.stdout').open('w') as stdout, (out / 'runner.stderr').open('w') as stderr:
            result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
        record['exit_status'] = result.returncode
        record['status'] = 'unqualified'
        witness = read(out / 'probe/witness.json')
        require(result.returncode == 0 and not witness.get('probe_error'), 'probe failure')
        shutil.copyfile(Path(witness['retained_scratch']) / 'db/src.zip', out / 'source.zip')
    finally:
        (out / 'run.json').write_text(json.dumps(record, indent=2) + '\n')
        (out / 'manifest.json').write_text(json.dumps({str(p.relative_to(out)): sha(p)
            for p in sorted(out.rglob('*')) if p.is_file()}, indent=2) + '\n')


if __name__ == '__main__':
    main()
