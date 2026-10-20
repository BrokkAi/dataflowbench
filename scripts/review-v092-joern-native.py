#!/usr/bin/env python3
"""Replay Joern's native bundle probe while preserving missing completion proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.capture = args.capture.resolve()
    args.output = args.output.resolve()
    require(args.capture.is_relative_to(ROOT) and args.output.is_relative_to(ROOT), 'review paths escaped repository')
    require(not args.output.exists(), 'review is append-only')
    completed = args.capture / 'completed.json'
    receipt = json.loads(completed.read_bytes())
    require(receipt['control'] == 'probe-joern-scan-native' and receipt['status'] == 'completed' and receipt['exit_code'] == 0 and not receipt['timed_out'] and not receipt['capacity_loss'], 'capture is incomplete')
    require(receipt['tool_bindings']['joern']['version'] == '4.0.660', 'unexpected Joern identity')
    inputs = {row['path']: row['sha256'] for row in receipt['source_inputs']}
    require(inputs['scripts/probe-joern-scan-native.sh'] == sha(ROOT / 'scripts/probe-joern-scan-native.sh'), 'probe source changed')
    files = {}
    for row in receipt['captured_files']:
        path = Path(row['capture_path'])
        require(path.resolve().is_relative_to(args.capture.resolve()) and path.is_file() and not path.is_symlink(), 'unsafe capture')
        require(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'capture changed')
        require(path.name not in files, 'duplicate captured name')
        files[path.name] = path
    require(files['witnessed-version.txt'].read_text().strip() == 'Version: `4.0.660`', 'bundle version differs')
    provenance = files['querydb-zip-provenance.txt'].read_text()
    require('https://github.com/joernio/joern/releases/download/v4.0.660/querydb.zip' in provenance and re.search(r'sha256: [a-f0-9]{64}\n', provenance), 'unpinned query bundle')
    bundle = json.loads(files['querydb.json'].read_bytes())
    require(isinstance(bundle, list) and len(bundle) == 58 and len({row['name'] for row in bundle}) == 58, 'bundle query roster differs')
    languages = sorted({row['language'] for row in bundle})
    require('javascript' not in languages and 'python' not in languages, 'native language availability changed')
    query = next(row for row in bundle if row['name'] == 'call-to-exec')
    require(query['language'] == 'java' and 'java.lang.Runtime.exec' in query['traversalAsString'], 'sink query changed')
    binding = files['call-to-exec-binding-check.txt'].read_text()
    require('pattern `java.lang.Runtime.exec` matches methods: 0' in binding and 'method name `exec` matches methods: 1' in binding and 'calls to that method: 1' in binding, 'receiver binding observation changed')
    observations = []
    for language in ('java', 'javascript', 'python'):
        fixtures = sorted(path.name for path in (ROOT / 'cases/taint' / language).glob('native-*') if path.is_dir())
        require(len(fixtures) == 12, 'native fixture roster changed')
        for fixture in fixtures:
            stem = 'scan-' + language + '-' + fixture
            raw = files[stem + '.txt'].read_text()
            summary = json.loads(files[stem + '.json'].read_bytes())
            findings = re.findall(r'^Result: .*$', raw, re.M)
            marker = 'Pass io.joern.console.scan.ScanPass completed' in raw
            require(summary['language'] == language and summary['probe'] == fixture and summary['scan_exit_status'] == 0, 'native command failure')
            require(summary['result_count'] == len(findings) and summary['results'] == findings and summary['scan_pass_completed'] is marker, 'native projection differs')
            require('Code successfully imported.' in raw, 'fixture extraction unproven')
            observations.append({'language': language, 'fixture': fixture, 'emitted_findings': len(findings), 'scan_completion_marker': marker})
    result = {'schema': 'v092-joern-native-review/v1', 'status': 'measurement-with-known-limits', 'execution_eligible': False,
              'capture': {'path': str(completed.relative_to(ROOT)), 'sha256': sha(completed)},
              'query_bundle': {'path': str(files['querydb.json'].relative_to(ROOT)), 'sha256': sha(files['querydb.json']), 'queries': 58, 'languages': languages},
              'observations': observations, 'completion_markers': sum(row['scan_completion_marker'] for row in observations),
              'limits': ['All 36 commands returned zero and imported code; missing scan completion markers remain unproven scan completion.', 'Zero emitted findings do not prove cleanliness or source/sink coverage.', 'The bundle has no JavaScript or Python query package; its Java Runtime.exec pattern matches zero methods despite an exec method and call.'],
              'review_implementation': {'path': str(Path(__file__).relative_to(ROOT)), 'sha256': sha(Path(__file__))}}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'queries': 58, 'scans': len(observations), 'completion_markers': result['completion_markers'], 'status': result['status']}))


if __name__ == '__main__':
    main()
