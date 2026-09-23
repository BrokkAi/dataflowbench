#!/usr/bin/env python3
"""Verify non-scored resolved process-input diagnostics without rerunning CodeQL."""
import hashlib
import json
import re
from pathlib import Path
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-foundation-sources-v1'
QUERIES = ROOT / 'adapters/codeql/swift-foundation-sources-v1/queries'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_logs(directory):
    result = inspect_logs(directory)
    assert result['ready_for_observation'], result


def verify_semantics(roles, flows, plan):
    labels = plan['labels']
    sources = [(row[0], row[3]) for row in roles if row[2] == 'adapter-corrected' and row[3] != 'sink']
    assert sorted(sources) == sorted([(labels['SOURCE_ENV'], 'environment'), (labels['SOURCE_ARGV'], 'argv')])
    assert not [r for r in roles if r[2] == 'vendor-native' and r[3] == 'source']
    assert all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles)
    expected = {(labels[a], labels[b]) for a, b in plan['expected_corrected_flows']}
    actual = [(r[0], r[1]) for r in flows if r[3] == 'adapter-corrected']
    assert set(actual) == expected and len(actual) == len(expected)
    assert len(flows) == len(actual), 'Vendor or unknown-profile flow appeared'
    positive_sinks = {labels[b] for _, b in plan['expected_corrected_flows']}
    negative_sinks = {labels[name] for name in plan['negative_sink_labels']}
    for profile in ['adapter-corrected', 'vendor-native']:
        sinks = [r for r in roles if r[2] == profile and r[3] == 'sink']
        assert {r[0] for r in sinks} == positive_sinks | negative_sinks
        # Six static calls have two argument sinks; two setters have one sink each.
        assert len(sinks) == 14
        for source_line, sink_line, column, flow_profile in flows:
            if flow_profile == profile:
                assert any(r[0] == sink_line and r[1] == column for r in sinks)


def verify():
    manifest = read(EVIDENCE / 'manifest.json')['files']
    for name, expected in manifest.items():
        assert digest(EVIDENCE / name) == expected, name
    attempt = EVIDENCE / 'control-attempt-01'
    for name, expected in read(attempt / 'manifest.json').items():
        assert digest(attempt / name) == expected, name
    plan = read(EVIDENCE / 'control-plan.json')
    assert digest(EVIDENCE / 'control/main.swift') == plan['source_sha256']
    assert digest(attempt / 'main.swift') == plan['source_sha256']
    assert (QUERIES / 'FoundationIdentity.qll').read_bytes() == (ROOT / 'adapters/codeql/swift-foundation-identity-v1/queries/FoundationIdentity.qll').read_bytes()
    for name, expected in plan['query_hashes'].items():
        assert digest(QUERIES / name) == expected, name
        assert digest(attempt / 'queries' / name) == expected, name
    policy = ROOT / 'adapters/codeql/swift-extraction-v2/policy.json'
    assert (attempt / 'extraction-policy.json').read_bytes() == policy.read_bytes()
    witness = read(attempt / 'witness.json')
    assert witness['status'] == 'unqualified' and witness['memory_compliance'] == 'unproven'
    assert witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048}
    assert witness['extraction_phase_deadline_seconds'] == 150
    assert witness['extraction_policy_sha256'] == digest(policy)
    prior = read(ROOT / 'evidence/swift-native-recognition-220/near-miss-attempt-01/witness.json')
    for key in ['compiler_sha256', 'extractor_sha256', 'target']:
        assert witness[key] == prior[key], key
    assert 'Swift version 6.3.3' in witness['compiler_version']['stdout']
    assert Path(witness['sdk']).name == 'MacOSX26.5.sdk'
    assert witness['extraction_integrity']['ready_for_observation']
    verify_logs(attempt / 'log/swift/extractor')
    assert 'finalised: true' in (attempt / 'codeql-database.yml').read_text()
    for name in ['database-create', 'roles', 'flow', 'identity']:
        record = read(attempt / (name + '.command.json'))
        assert record == witness['phases'][name]
        deadline = 150 if name == 'database-create' else 60
        assert record['exit_status'] == 0 and not record['timed_out']
        assert record['deadline_seconds'] == deadline and record['elapsed_seconds'] < deadline
        assert record['cleanup_status'] == 'tracked-processes-stopped'
        if name != 'database-create':
            assert '--ram=2048' in record['argv'] and '--timeout=60' in record['argv']
            decoded = read(attempt / (name + '-decode.command.json'))
            assert decoded['exit_status'] == 0 and not decoded['timed_out']
            rss = re.search(r'(\d+)\s+maximum resident set size', (attempt / (name + '.stderr')).read_text())
            assert rss and int(rss[1]) <= 2048 * 1024 ** 2
    archive = read(EVIDENCE / 'source-archive-check.json')
    assert archive['member_sha256'] == plan['source_sha256'] and archive['matches_control']
    verify_semantics(read(attempt / 'roles.json')['#select']['tuples'], read(attempt / 'flow.json')['#select']['tuples'], plan)
    print('Verified 4 corrected environment/argv flows and recognized nonflow sinks; vendor output separate. Non-scored; aggregate memory and completeness unproven.')


if __name__ == '__main__':
    verify()
