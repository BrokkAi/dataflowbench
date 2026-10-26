#!/usr/bin/env python3
"""Concise review plus lossless detail, without changing benchmark contracts.

Standard library only. See docs/compact-evidence.md for the package contract.
"""

import argparse
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from evidence_bundle import (BLOCK, _assert_no_symlink_components, _lexical_absolute,
                             check, digest, pack, read_file, require, safe_path)


SCHEMA = 'dataflowbench-compact-review/v1'
OUTCOMES = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode()


def load_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'duplicate JSON key: {key}')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f'non-finite JSON value: {value}')

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


def reference(directory, path):
    file = directory / path
    return {'path': path, 'sha256': digest(file), 'bytes': file.stat().st_size}


def csv_cell(value):
    # A review CSV may be opened by a spreadsheet. The original value stays
    # byte-exact in detail; a leading apostrophe marks unsafe display cells.
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + value
    return value


def inventory(detail):
    with gzip.open(detail / 'files.jsonl.gz', 'rt', encoding='utf-8') as stream:
        return {r['path']: r for r in map(load_json, stream)}


def make_review(root, inputs, output):
    """Project explicit inputs only; all rows and original identities remain linked."""
    output.mkdir()
    summaries = []
    with (output / 'cases.csv').open('w', newline='', encoding='utf-8') as case_file, \
         (output / 'attempts.jsonl').open('wb') as attempt_file:
        cases = csv.DictWriter(case_file, fieldnames=[
            'report', 'case_id', 'outcome', 'duration_ms', 'peak_memory_mb',
            'raw_output', 'detail_pointer', 'result_sha256'])
        cases.writeheader()
        for item in inputs:
            path = item['path']
            data = (root / path).read_bytes()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() ==
                    item['sha256'], f'review input changed: {path}')
            summary = dict(item)
            if item['kind'] == 'report':
                report = load_json(data)
                require(isinstance(report, dict) and type(report.get('schema_version')) is int
                        and report['schema_version'] == 1
                        and isinstance(report.get('tool'), str)
                        and isinstance(report.get('results'), list),
                        f'not a normalized v1 report: {path}')
                rows = report['results']
                identities = set()
                counts = collections.Counter()
                for number, row in enumerate(rows):
                    require(isinstance(row, dict) and isinstance(row.get('case_id'), str)
                            and row.get('outcome') in OUTCOMES,
                            f'invalid case row: {path} /results/{number}')
                    require(row['case_id'] not in identities, f'duplicate case ID: {path}')
                    identities.add(row['case_id'])
                    counts[row['outcome']] += 1
                    cells = {
                        'report': path, 'case_id': row['case_id'], 'outcome': row['outcome'],
                        'duration_ms': row.get('duration_ms'),
                        'peak_memory_mb': row.get('peak_memory_mb'),
                        'raw_output': row.get('raw_output'),
                        'detail_pointer': f'/results/{number}',
                        'result_sha256': hashlib.sha256(encoded(row)).hexdigest(),
                    }
                    cases.writerow({key: csv_cell(value) for key, value in cells.items()})
                summary.update(metadata={k: v for k, v in report.items() if k != 'results'},
                               result_count=len(rows),
                               outcome_counts={outcome: counts[outcome] for outcome in sorted(OUTCOMES)})
            elif item['kind'] == 'attempts':
                counts = collections.Counter()
                count = 0
                for count, line in enumerate(data.splitlines(keepends=True), 1):
                    row = load_json(line)
                    require(isinstance(row, dict), f'attempt row is not an object: {path}:{count}')
                    # Keep every scalar, including unknown statuses, failures and nulls.
                    # Nested records remain in the byte-exact line, referenced below.
                    scalars = {k: v for k, v in row.items() if not isinstance(v, (list, dict))}
                    counts[json.dumps(row.get('status'), sort_keys=True)] += 1
                    attempt_file.write(encoded({
                        'source': path, 'line_1based': count,
                        'raw_line_sha256': hashlib.sha256(line).hexdigest(),
                        'scalars': scalars,
                        'detail_fields': [k for k, v in row.items() if isinstance(v, (list, dict))],
                    }))
                summary.update(row_count=count, status_counts=dict(sorted(counts.items())))
            else:
                require(item['kind'] == 'copy', 'unknown review input kind')
                target = output / 'files' / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            summaries.append(summary)
    summary = {
        'schema': SCHEMA, 'inputs': summaries,
        'authority': 'derived review; original files and existing validators remain authoritative',
        'scope': 'explicit inputs only; counts are observed rows, not expected population or completion',
        'detail': '../detail/bundle.json',
        'case_details': 'cases.csv points into original reports; diagnostics, anchors and unknown fields remain in detail',
        'attempt_details': 'attempts.jsonl retains one row per input line; nested fields remain in detail',
        'qualification': False,
    }
    (output / 'summary.json').write_bytes(encoded(summary))
    (output / 'START-HERE.md').write_text(
        '# Evidence review\n\nRead summary.json, cases.csv and attempts.jsonl. '
        'Copied context is under files/. Counts describe only the explicitly selected inputs; '
        'they do not establish matrix completion, scoring or publication readiness.\n\n'
        'Use package-evidence.py read to inspect a complete original report, a JSON pointer '
        'from cases.csv, or a ledger line from attempts.jsonl. Use materialize for existing '
        'readers and compare for the existing Rust report comparison. See docs/compact-evidence.md.\n',
        encoding='utf-8')


def create(root, scope, output, reports=(), attempts=(), copies=(), part_bytes=40 * BLOCK):
    root, output = _lexical_absolute(root), _lexical_absolute(output)
    _assert_no_symlink_components(root)
    _assert_no_symlink_components(output.parent)
    # The bundle library also checks scope ancestry and refuses nested outputs.
    relative = safe_path(scope)
    require(not output.resolve().is_relative_to((root / relative).resolve()),
            'output must be outside evidence scope')
    requested = [(p, kind) for kind, paths in
                 [('report', reports), ('attempts', attempts), ('copy', copies)] for p in paths]
    require(len({p for p, _ in requested}) == len(requested), 'duplicate review input')
    for path, _ in requested:
        safe_path(path)
        require(Path(path).is_relative_to(Path(scope)), 'review input outside scope')
    # A failed pack/review never publishes a partially usable package.
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists() and not output.is_symlink(), 'package destination already exists')
    with tempfile.TemporaryDirectory(prefix='.evidence-', dir=output.parent) as temporary:
        staging = Path(temporary) / 'package'
        staging.mkdir()
        pack(root, scope, staging / 'detail', part_bytes)
        files = inventory(staging / 'detail')
        inputs = []
        for path, kind in requested:
            require(path in files, f'review input not in snapshot: {path}')
            inputs.append({k: files[path][k] for k in ('path', 'sha256', 'bytes')} | {'kind': kind})
        make_review(root, inputs, staging / 'review')
        manifest = {
            'schema': SCHEMA, 'inputs': inputs,
            'detail': reference(staging, 'detail/bundle.json'),
            'files': [reference(staging, p.relative_to(staging).as_posix())
                      for p in sorted((staging / 'review').rglob('*')) if p.is_file()],
        }
        (staging / 'review-manifest.json').write_bytes(encoded(manifest))
        staging.rename(output)
    return manifest


def review_manifest(package):
    manifest_path = package / 'review-manifest.json'
    require(not manifest_path.is_symlink(), 'symlink manifest refused')
    manifest = load_json(manifest_path.read_bytes())
    require(manifest['schema'] == SCHEMA, 'unknown review schema')
    require(manifest['detail']['path'] == 'detail/bundle.json', 'invalid detail reference')
    names = set()
    for item in [manifest['detail'], *manifest['files']]:
        path = safe_path(item['path'])
        require(str(path) not in names, 'duplicate review file reference')
        names.add(str(path))
        require(str(path) == 'detail/bundle.json' or path.parts[0] == 'review',
                'file outside package review')
        current = package
        for component in path.parts:
            current = current / component
            require(not current.is_symlink(), 'symlink package file refused')
        require(current.is_file() and current.stat().st_size == item['bytes']
                and digest(current) == item['sha256'], f'package digest mismatch: {path}')
    return manifest


def verify(package, restore=None, paths=None):
    manifest = review_manifest(package)
    inputs = manifest['inputs']
    require(len({i['path'] for i in inputs}) == len(inputs), 'duplicate review input')
    selected = None if paths is None else [str(safe_path(path)) for path in paths]
    require(selected is None or len(set(selected)) == len(selected), 'duplicate selected path')
    required = None if restore is not None and selected is None else sorted(
        {i['path'] for i in inputs} | set(selected or []))
    destination = None if restore is None else _lexical_absolute(restore)
    if destination is not None:
        _assert_no_symlink_components(destination.parent)
        require(not destination.exists() and not destination.is_symlink(), 'restore destination already exists')
        require(not destination.resolve().is_relative_to(package.resolve()),
                'restore output must be outside package')
        destination.parent.mkdir(parents=True, exist_ok=True)
    # One archive pass restores the review inputs and requested files together.
    # Rebuild the derivative before publishing any caller-visible destination.
    with tempfile.TemporaryDirectory(prefix='.dfb-review-',
                                     dir=None if destination is None else destination.parent) as temporary:
        root = Path(temporary)
        originals = root / 'originals'
        result = check(package / 'detail', originals, paths=required)
        make_review(root / 'originals', inputs, root / 'review')
        expected = [reference(root, p.relative_to(root).as_posix())
                    for p in sorted((root / 'review').rglob('*')) if p.is_file()]
        require(manifest['files'] == expected, 'review differs from detailed originals')
        if destination is not None:
            if selected is not None:
                keep = set(selected)
                for file in originals.rglob('*'):
                    if file.is_file() and file.relative_to(originals).as_posix() not in keep:
                        file.unlink()
                for directory in sorted(originals.rglob('*'), reverse=True):
                    if directory.is_dir() and not any(directory.iterdir()):
                        directory.rmdir()
            _assert_no_symlink_components(destination.parent)
            require(not destination.exists() and not destination.is_symlink(),
                    'restore destination appeared during verification')
            restored_count = sum(1 for file in originals.rglob('*') if file.is_file())
            originals.rename(destination)
        else:
            restored_count = 0
    return result | {'restored': destination is not None, 'restored_files': restored_count,
                     'review': 'verified', 'review_inputs': len(inputs)}


def pointer(value, selection):
    require(selection == '' or selection.startswith('/'), 'JSON pointer must begin with /')
    if selection:
        for token in selection[1:].split('/'):
            # RFC 6901 permits only ~0 and ~1 escapes.
            require('~' not in token.replace('~1', '').replace('~0', ''), 'invalid JSON pointer escape')
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                require(token.isascii() and token.isdigit() and
                        (token == '0' or not token.startswith('0')), 'invalid array index')
                value = value[int(token)]
            else:
                require(isinstance(value, dict), 'JSON pointer traverses a scalar')
                value = value[token]
    return value


def compare(baseline, current, output, binary, allow_configuration_mismatch=False):
    require(binary.is_file(), 'comparison binary does not exist')
    sources = {'baseline': baseline.resolve(), 'current': current.resolve()}
    output = _lexical_absolute(output)
    _assert_no_symlink_components(output.parent)
    require(not output.exists() and not output.is_symlink(), 'comparison destination already exists')
    output = output.resolve()
    for source in sources.values():
        require(source.exists(), f'missing comparison input: {source}')
        require(not (source.is_dir() and output.is_relative_to(source)),
                'comparison output must be outside input trees')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'dataflowbench-package-comparison/v1', 'inputs': {}}
    resolved = {}
    with tempfile.TemporaryDirectory(prefix='.dfb-compare-', dir=output.parent) as temporary:
        staging = Path(temporary) / 'comparison'
        staging.mkdir()
        for name, source in sources.items():
            if source.is_dir() and (source / 'review-manifest.json').exists():
                manifest = review_manifest(source)
                reports = [i for i in manifest['inputs'] if i['kind'] == 'report']
                require(reports, f'package contains no selected reports: {source}')
                verify(source, staging / name, paths=[i['path'] for i in reports])
                resolved[name] = output / name
                receipt['inputs'][name] = {'package': str(source), 'reports': reports,
                                          'manifest': reference(source, 'review-manifest.json')}
            else:
                resolved[name] = source
                receipt['inputs'][name] = {'original': str(source)}
        require(not output.exists() and not output.is_symlink(), 'comparison destination appeared')
        staging.rename(output)
    command = [str(binary.resolve()), 'compare-reports', '--baseline', str(resolved['baseline']),
               '--current', str(resolved['current']), '--json', str(output / 'comparison.json')]
    if allow_configuration_mismatch:
        command.append('--allow-configuration-mismatch')
    receipt['command'] = command
    result = subprocess.run(command, check=False)
    receipt['exit_code'] = result.returncode
    (output / 'package-inputs.json').write_bytes(encoded(receipt))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create_parser = sub.add_parser('pack', help='create an immutable detail snapshot and review')
    create_parser.add_argument('--root', type=Path, required=True)
    create_parser.add_argument('--scope', required=True)
    create_parser.add_argument('--output', type=Path, required=True)
    for option in ('report', 'attempts', 'copy'):
        create_parser.add_argument('--' + option, action='append', default=[])
    create_parser.add_argument('--part-mib', type=int, default=40)
    for command in ('check', 'materialize', 'read'):
        command_parser = sub.add_parser(command)
        command_parser.add_argument('package', type=Path)
        if command == 'materialize':
            command_parser.add_argument('--output', type=Path, required=True)
            command_parser.add_argument('--path', action='append')
        if command == 'read':
            command_parser.add_argument('path')
            selection = command_parser.add_mutually_exclusive_group()
            selection.add_argument('--pointer')
            selection.add_argument('--line', type=int)
    comparison = sub.add_parser('compare', help='materialize reports and call the existing Rust CLI')
    comparison.add_argument('--baseline', type=Path, required=True)
    comparison.add_argument('--current', type=Path, required=True)
    comparison.add_argument('--output', type=Path, required=True)
    comparison.add_argument('--binary', type=Path, required=True)
    comparison.add_argument('--allow-configuration-mismatch', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'pack':
            result = create(args.root, args.scope, args.output, args.report, args.attempts,
                            args.copy, args.part_mib * BLOCK)
        elif args.command == 'compare':
            return compare(args.baseline, args.current, args.output.resolve(), args.binary,
                           args.allow_configuration_mismatch)
        elif args.command == 'read':
            review_manifest(args.package)
            data = read_file(args.package / 'detail', args.path)
            if args.line is not None:
                lines = data.splitlines(keepends=True)
                require(1 <= args.line <= len(lines), 'line outside file')
                data = lines[args.line - 1]
            if args.pointer is not None:
                data = encoded(pointer(load_json(data), args.pointer))
            sys.stdout.buffer.write(data)
            return 0
        else:
            result = verify(args.package, getattr(args, 'output', None), getattr(args, 'path', None))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, IndexError, TypeError, OSError, EOFError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    sys.exit(main())
