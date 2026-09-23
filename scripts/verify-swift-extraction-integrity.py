#!/usr/bin/env python3
"""Check extraction integrity independently of successful database finalization."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-candidate-native-controls-220'
OUTPUT = ROOT / 'evidence/swift-extraction-integrity-220.json'


def inspect(directory):
    logs = sorted((directory / 'log/swift/extractor').glob('*.gz'))
    records = []
    for path in logs:
        lines = gzip.open(path, 'rt', errors='strict').read().splitlines()
        errors = [{'line': i, 'text': line} for i, line in enumerate(lines, 1)
                  if ' ERRO ' in line or ' ERROR ' in line]
        records.append({'path': str(path.relative_to(ROOT)),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'errors': errors})
    return {'attempt': directory.name, 'logs': records,
            'extraction_integrity': 'blocked' if not logs or any(r['errors'] for r in records) else 'no-errors-observed',
            'qualified_role_absence': False,
            'limitation': 'No logged errors alone does not prove complete extraction or native capability.'}


def build():
    return {'schema_version': 1, 'attempts': [inspect(p) for p in sorted(BASE.glob('codeql-*-attempt-02'))],
            'decision': 'blocked: extractor compiler errors invalidate absence inference despite finalized databases',
            'prior_evidence': 'Preserved unchanged. role_observation_complete in the earlier summary means query completion only, not extraction integrity.',
            'near_miss': 'Shipped sink remains an observed result in an error-bearing database; reproduce on a compatible compiler/SDK before attributing a qualified native-model defect.',
            'budget': '60 seconds / 512 MiB remains unchanged. Fix extraction compatibility before fresh preregistered qualification; 180-second retries remain diagnostic.'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, sort_keys=True) + '\n'
    if args.write:
        OUTPUT.write_text(rendered)
    else:
        assert OUTPUT.read_text() == rendered, 'stale extraction-integrity correction'
        assert len(build()['attempts']) == 3
        assert all(r['extraction_integrity'] == 'blocked' for r in build()['attempts'])
    print('Extraction errors retained; native absence and qualification remain blocked')
