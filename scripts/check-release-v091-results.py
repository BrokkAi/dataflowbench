#!/usr/bin/env python3
"""Check v0.9.1 evidence or its separately merged freeze/publication artifacts."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def validate_manifest(source, evidence_revision):
    manifest = json.loads((source / 'reports/freeze.json').read_text())
    plan = json.loads((source / 'reports/releases/v0.9.1/plan.json').read_text())
    if manifest.get('schema_version') != 1 or manifest.get('claim', {}).get('scope') != 'release':
        raise ValueError('v0.9.1 requires an actual release-scope freeze')
    benchmark = manifest.get('benchmark', {})
    if (benchmark.get('release') != 'v0.9.1' or benchmark.get('revision') != evidence_revision or
            benchmark.get('dirty') is not False or benchmark.get('fixture_revision') != plan['fixture_revision']):
        raise ValueError('freeze does not bind the exact merged v0.9.1 evidence revision and fixture')
    summary = json.loads((source / 'reports/releases/v0.9.1/evidence-validation.json').read_text())
    expected = {entry['path']: entry['sha256'] for entry in summary['fresh_reports']}
    expected.update({entry['path']: entry['normalized_report_sha256'] for entry in plan['carried_reports']})
    reports = manifest.get('reports', [])
    if len(reports) != 92 or {entry['path']: entry['normalized_report_sha256'] for entry in reports} != expected:
        raise ValueError('freeze does not bind exactly the 20 fresh and 72 carried reports')
    baseline = json.loads((source / plan['baseline_freeze']['path']).read_text())
    if manifest.get('cases') != baseline['cases']:
        raise ValueError('freeze population or fixture bytes differ from v0.9.0')
    return manifest


def run(source, binary, evidence_revision, generate_output=None):
    if not re.fullmatch('[0-9a-f]{40}', evidence_revision):
        raise ValueError('evidence revision must be an exact lowercase commit')
    checker = module('v091_evidence', source / 'scripts/check-v091-evidence.py')
    checker.ROOT = source
    if checker.verify() != json.loads((source / 'reports/releases/v0.9.1/evidence-validation.json').read_text()):
        raise ValueError('evidence validation summary differs from retained artifacts')
    validate_manifest(source, evidence_revision)
    # Reuse the existing official-remote, main ancestry, clean clone, temporary
    # local tag rehearsal, immutable published tag, and generation checks.
    gate = module('v091_release_mechanics', source / 'scripts/check-release-results.py')
    gate.RELEASE = 'v0.9.1'
    gate.EXPECTED_REVISION = evidence_revision
    gate.run_gate(source, binary=binary, generate_output=generate_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-revision', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--generate-output', type=Path)
    args = parser.parse_args()
    run(ROOT, args.binary, args.evidence_revision, args.generate_output)
    print('v0.9.1 release gate passed')
