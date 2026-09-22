#!/usr/bin/env python3
"""Retain bounded compiler identity views; never execute fixture binaries."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from swift_population_v2 import ROOT, audit, sha

spec = importlib.util.spec_from_file_location('retained_commands', ROOT / 'scripts/run-codeql-swift-case.py')
commands = importlib.util.module_from_spec(spec); spec.loader.exec_module(commands)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    manifest, additions = audit()
    compiler = subprocess.check_output(['xcrun', '--find', 'swiftc'], text=True).strip()
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    witness = {'compiler': compiler, 'compiler_sha256': sha(Path(compiler).resolve()), 'sdk': sdk,
               'population': manifest['population'], 'fixture_revision': manifest['fixture_revision'],
               'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'scope': 'non-scored compiler declarations only; no analyzer qualification'}
    (output / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    for name, argv in [('compiler-version', [compiler, '--version']), ('sdk-build', ['xcrun', '--show-sdk-build-version']), ('xcode', ['xcodebuild', '-version']), ('host', ['sw_vers'])]:
        commands.run(argv, output, name, 30)
    for path, case in additions:
        directory = output / case['id']; directory.mkdir()
        shutil.copyfile(path, directory / 'case.json')
        for name in case['fixture_files']: shutil.copyfile(path.parent / name, directory / name)
        with tempfile.TemporaryDirectory(prefix='dfb-v2-ast-') as temporary:
            argv = [compiler, '-swift-version', '6', '-typecheck', '-dump-ast', '-sdk', sdk,
                    '-target', 'arm64-apple-macosx27.0.0', '-module-name', 'DataFlowBenchTaintSwift',
                    '-module-cache-path', temporary] + [str(directory / name) for name in case['fixture_files']]
            record = commands.run(argv, directory, 'typechecked-ast', 60, measure=True)
            print(case['id'], record['exit_status'], flush=True)
    (output / 'manifest.json').write_text(json.dumps({str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}, indent=2) + '\n')


if __name__ == '__main__': main()
