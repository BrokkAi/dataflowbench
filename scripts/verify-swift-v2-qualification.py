#!/usr/bin/env python3
"""Verify retained preflight observations without promoting them to activation."""
import hashlib
import json
from pathlib import Path
import re
from swift_population_v2 import ROOT, audit, require, sha

BASE = ROOT / 'evidence/swift-v2-qualification-220'


def declaration_index(base):
    result = {}
    for path in sorted((base / 'compiler-attempt-01').glob('*/typechecked-ast.stdout')):
        rows = []
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if 'decl="' in line:
                attributes = dict(re.findall(r'(type|decl)="([^"]*)"', line))
                if attributes: rows.append({'ast_line': number, **attributes})
        result[path.parent.name] = rows
    return result


def verify_files(base):
    manifest = json.loads((base / 'manifest.json').read_text())
    actual = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p != base / 'manifest.json'}
    require(set(manifest) == actual, 'qualification evidence membership')
    for name, digest in manifest.items(): require(sha(base / name) == digest, f'qualification digest: {name}')


def verify(base=BASE):
    verify_files(base)
    population, additions = audit()
    summary = json.loads((base / 'summary.json').read_text())
    require(summary['status'] == 'unqualified-preflight' and summary['scored_partitions'] == [], 'no qualification or partition promotion')
    require(summary['fixture_revision'] == population['fixture_revision'], 'population revision')
    expected = {case['id']: (path, case) for path, case in additions}
    index = declaration_index(base)
    require(set(index) == set(expected), 'compiler coverage')
    require(index == json.loads((base / 'compiler-declaration-index.json').read_text()), 'compiler declaration index differs from raw AST')
    for identifier, (path, case) in expected.items():
        directory = base / 'compiler-attempt-01' / identifier
        require(sha(directory / 'case.json') == sha(path), 'retained metadata')
        for name in case['fixture_files']: require(sha(directory / name) == sha(path.parent / name), 'retained fixture')
        record = json.loads((directory / 'typechecked-ast.command.json').read_text())
        require(record['exit_status'] == 0 and not record['timed_out'], 'compiler completion')
        require('-typecheck' in record['argv'] and '-dump-ast' in record['argv'], 'compiler-only command')
        if case['model_profile'] == 'tool-native':
            require(any(row['decl'].startswith('Foundation.(file).Process extension.run(_:arguments:terminationHandler:)@') and row.get('type') == '(Process.Type) -> (URL, [String], (@Sendable (Process) -> Void)?) throws -> Process' for row in index[identifier]), 'compiler platform sink declaration')
    first = json.loads((base / 'codeql-native-source-attempt-01/database-create.command.json').read_text())
    require(first['timed_out'] and first['exit_status'] != 0, 'first extraction failure must remain visible')
    for attempt in ['codeql-native-source-attempt-01', 'codeql-native-source-attempt-02']:
        witness = json.loads((base / attempt / 'witness.json').read_text())
        require(witness['status'] == 'unqualified' and witness['memory_compliance'] == 'unproven', 'extraction qualification boundary')
    second = json.loads((base / 'codeql-native-source-attempt-02/database-create.command.json').read_text())
    require(second['timed_out'] and second['cleanup_status'] == 'verified-stopped', 'second extraction timeout and safe cleanup')
    for attempt, name, exit_status in [('codeql-probe-check-attempt-01', 'catalog', 0), ('codeql-probe-check-attempt-01', 'declarations', 2), ('codeql-probe-check-attempt-02', 'declarations', 0)]:
        record = json.loads((base / attempt / (name + '.command.json')).read_text())
        require(record['exit_status'] == exit_status and '--ram=512' in record['argv'], 'query check evidence')
        require(record['time_maxrss_mb'] > 512, 'resource excess remains unqualified')
    print('Verified compiler/catalog preflight and retained failures; zero scored partitions; no v2 activation')


if __name__ == '__main__': verify()
