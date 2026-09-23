#!/usr/bin/env python3
"""Verify retained Foundation diagnostics without claiming scored qualification."""
import hashlib
import json
import re
from pathlib import Path
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-foundation-identity-v1'


def read(path):
    return json.loads(path.read_text())


def verify_manifest(directory, nested=False):
    manifest = read(directory / 'manifest.json')
    files = manifest['files'] if nested else manifest
    for name, digest in files.items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, name


def verify_rows(roles, flows):
    expected_roles = {(15, 5), (16, 36), (16, 76), (22, 36), (22, 82)}
    expected_flows = {(13, 15, 5), (13, 16, 36), (13, 16, 76)}
    false_roles = {(18, 5), (19, 17), (19, 57), (20, 28), (20, 46)}
    for profile in ['vendor-native', 'adapter-corrected']:
        rs = [tuple(row[:2]) for row in roles if row[2] == profile]
        fs = [tuple(row[:3]) for row in flows if row[3] == profile]
        wanted_roles = expected_roles | (false_roles if profile == 'vendor-native' else set())
        wanted_flows = expected_flows | ({(13, *r) for r in false_roles} if profile == 'vendor-native' else set())
        assert set(rs) == wanted_roles and len(rs) == len(wanted_roles), profile
        assert set(fs) == wanted_flows and len(fs) == len(wanted_flows), profile
    assert len(roles) == 15 and len(flows) == 11


def verify_extraction_logs(directory):
    integrity = inspect_logs(directory)
    assert integrity['ready_for_observation'], integrity


def verify():
    verify_manifest(EVIDENCE, nested=True)
    verify_manifest(ROOT / 'evidence/swift-native-recognition-220', nested=True)
    attempt = EVIDENCE / 'control-attempt-03'
    verify_manifest(attempt)
    witness = read(attempt / 'witness.json')
    plan = read(EVIDENCE / 'control-v3-plan.json')
    assert witness['status'] == 'unqualified'
    assert witness['memory_compliance'] == 'unproven'
    assert witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048}
    assert witness['extraction_phase_deadline_seconds'] == 150
    assert witness['extraction_integrity']['ready_for_observation']
    assert not witness['extraction_integrity']['errors']
    assert 'finalised: true' in (attempt / 'codeql-database.yml').read_text()
    verify_extraction_logs(attempt / 'log/swift/extractor')
    source = (attempt / 'main.swift').read_bytes()
    assert source == (EVIDENCE / 'control-v3/main.swift').read_bytes()
    assert hashlib.sha256(source).hexdigest() == plan['source_sha256']
    archive = read(EVIDENCE / 'control-03-source-archive-check.json')
    assert archive['member_sha256'] == plan['source_sha256'] and archive['matches_retained_control']
    for name, digest in plan['query_hashes'].items():
        live = ROOT / 'adapters/codeql/swift-foundation-identity-v1/queries' / name
        assert hashlib.sha256(live.read_bytes()).hexdigest() == digest, name
        assert live.read_bytes() == (attempt / 'queries' / name).read_bytes()
    assert (attempt / 'extraction-policy.json').read_bytes() == (ROOT / 'adapters/codeql/swift-extraction-v2/policy.json').read_bytes()
    for name in ['database-create', 'roles', 'flow', 'signature']:
        phase = witness['phases'][name]
        assert phase == read(attempt / (name + '.command.json'))
        limit = 150 if name == 'database-create' else 60
        assert phase['exit_status'] == 0 and not phase['timed_out']
        assert phase['deadline_seconds'] == limit and phase['elapsed_seconds'] < limit
        assert phase['cleanup_status'] == 'tracked-processes-stopped'
        if name != 'database-create':
            assert '--ram=2048' in phase['argv'] and '--timeout=60' in phase['argv']
            rss = re.search(r'(\d+)\s+maximum resident set size', (attempt / (name + '.stderr')).read_text())
            assert rss and int(rss[1]) <= 2048 * 1024 ** 2
    verify_rows(read(attempt / 'roles.json')['#select']['tuples'], read(attempt / 'flow.json')['#select']['tuples'])
    for name in ['control-attempt-01', 'control-attempt-02']:
        assert read(EVIDENCE / name / 'roles.json')['#select']['tuples'] == []
    print('Verified Foundation diagnostic: 3 real flows preserved, 5 vendor false flows excluded; safe sink has no flow. Non-scored; aggregate memory and completeness unproven.')


if __name__ == '__main__':
    verify()
