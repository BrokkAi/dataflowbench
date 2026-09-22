#!/usr/bin/env python3
"""Verify retained preparation evidence without network access or execution."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-release-preparation-220/2026-09-23'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = read(BASE / 'manifest.json')
    actual = {str(p.relative_to(BASE)) for p in BASE.rglob('*')
              if p.is_file() and p.name != 'manifest.json'}
    assert actual == set(manifest['files']), 'evidence membership changed'
    for name, digest in manifest['files'].items():
        assert sha(BASE / name) == digest, name

    resources = read(BASE / 'resources.json')
    for name, digest in resources['input_hashes_sha256'].items():
        assert sha(ROOT / name) == digest, name
    duration = resources['historical_duration_seconds']
    assert abs(duration['v0_8_selected_latest_completed_per_82_report_lanes']
               + duration['swift_v1_v2_combined_seconds']
               - duration['serial_observed_sum_seconds']) < .001
    ledger = [json.loads(line) for line in
              (ROOT / 'reports/releases/v0.8.0/ledger.jsonl').read_text().splitlines()]
    latest = {row['planned_id']: row for row in ledger if row.get('end_utc')}
    old_plan = read(ROOT / 'reports/releases/v0.8.0/rerun-plan.json')
    elapsed = sum((datetime.fromisoformat(latest[row['id']]['end_utc'])
                   - datetime.fromisoformat(latest[row['id']]['start_utc'])).total_seconds()
                  for row in old_plan['reports'])
    assert abs(elapsed - duration['v0_8_selected_latest_completed_per_82_report_lanes']) < .001
    swift_ms = sum(row.get('duration_ms', 0) or 0
                   for tool in ('codeql', 'joern')
                   for suffix in ('kernel', 'modeling', 'calibration', 'v2-result')
                   for row in read(ROOT / f'reports/{tool}-swift-{suffix}.json')['results'])
    assert abs(swift_ms / 1000 - duration['swift_v1_v2_combined_seconds']) < .001

    metadata = BASE / 'pin-metadata'
    requests = [json.loads(line) for line in
                (metadata / 'requests.jsonl').read_text().splitlines()]
    assert len(requests) == 49
    for request in requests:
        for kind in ('body', 'headers'):
            assert sha(metadata / request[kind + '_path']) == request[kind + '_sha256']

    pins = read(metadata / 'next-pin-manifest.json')
    assert len(pins['targets']) == 10
    assert all(p['decision'] in ('hold-current', 'propose-bump', 'manual-review-required')
               for p in pins['targets'])
    rules = next(p for p in pins['targets'] if p['name'] == 'semgrep-rules')
    repository = read(metadata / 'raw/repo_semgrep_rules.json')
    branch = read(metadata / 'raw/semgrep_rules_default_branch_actual.json')
    assert rules['default_branch'] == repository['default_branch'] == branch['name']
    assert rules['candidate_pin'] == branch['commit']['sha']

    packs = read(BASE / 'codeql-packs.json')['roots']
    assert len(packs) == 13
    summary = read(metadata / 'SUMMARY.json')
    assert {p['name']: p['candidate'] for p in summary['codeql_pack_registry']['roots']} == {
        p['name']: p['latest_stable'] for p in packs}
    for pack in packs:
        assert not pack['runtime_qualified']
        files = read(ROOT / pack['evidence_directory'] / 'file-manifest.json')
        assert len(files) == pack['file_count']
        assert sum(f['bytes'] for f in files) == pack['bytes']
    print('Preparation evidence verified: 49 metadata requests, 13 pack roots, resource provenance')


if __name__ == '__main__':
    verify()
