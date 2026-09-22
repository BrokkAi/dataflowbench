#!/usr/bin/env python3
"""Publish a path-redacted copy while preserving raw local evidence untouched."""
import argparse
import hashlib
import json
from pathlib import Path


def export(source, output):
    raw = source.read_bytes()
    evidence = json.loads(raw)
    environment = evidence['execution_environment']['sanitized']
    script = evidence.get('validator', {}).get('path', '')
    # Exact raw records remain local. Placeholder substitutions retain argv
    # order, scratch suffixes, outcomes, compiler identity and source digests.
    substitutions = {}
    if script:
        substitutions[str(Path(script).parent.parent)] = '<WORKTREE>'
    for key in ['HOME', 'TMPDIR']:
        if environment.get(key):
            value = environment[key].rstrip('/')
            substitutions[value] = '<' + key + '>'
            if value.startswith('/var/'):
                substitutions['/private' + value] = '<' + key + '>'
    def redact(value):
        if isinstance(value, dict):
            return {k: '<LOCAL_PATH_WITHHELD>' if k == 'PATH' else redact(v) for k,v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        if isinstance(value, str):
            for prefix, placeholder in sorted(substitutions.items(), key=lambda kv: -len(kv[0])):
                value = value.replace(prefix, placeholder)
        return value
    result = redact(evidence)
    result['publication'] = {
        'kind': 'path-redacted-copy',
        'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'redactions': ['worktree root', 'home directory', 'temporary directory root', 'local PATH value'],
        'raw_retention': 'Original local attempt is retained unchanged; this export is not verbatim raw evidence.',
    }
    data = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if '/Users/dave' in data or '/var/folders/' in data:
        raise ValueError('unredacted local path remains')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    export(args.source, args.output)
