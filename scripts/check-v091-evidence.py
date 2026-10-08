#!/usr/bin/env python3
"""Verify v0.9.1 evidence and compare retained outcomes; never create a freeze."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = Path('reports/releases/v0.9.1')
OUTCOMES = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def bound(path, digest, size=None):
    path = Path(path)
    check(not path.is_absolute() and '..' not in path.parts, f'unsafe path: {path}')
    check((ROOT / path).is_file() and not (ROOT / path).is_symlink(), f'missing or symlinked artifact: {path}')
    check(sha(path) == digest, f'changed bytes: {path}')
    if size is not None:
        check((ROOT / path).stat().st_size == size, f'changed byte count: {path}')


def verify():
    plan = load(RELEASE_ROOT / 'plan.json')
    check(plan['release'] == 'v0.9.1' and plan['execution_series'] == 2, 'wrong release series')
    check((plan['expected_cases'], plan['fresh_report_partitions'], plan['fresh_report_rows'], plan['carried_report_partitions'], plan['carried_report_rows'], plan['expected_report_partitions'], plan['expected_report_rows']) == (1108,20,1116,72,3136,92,4252), 'wrong registered release scope')
    bound(plan['baseline_freeze']['path'], plan['baseline_freeze']['sha256'])
    bound(plan['prior_series']['path'], plan['prior_series']['sha256'])
    failed_rows = [json.loads(line) for line in (ROOT / plan['prior_series']['ledger']).read_text().splitlines()]
    check(len(failed_rows) == 1 and failed_rows[0]['status'] == 'recorder-error' and failed_rows[0]['exit_code'] == 1, 'original pre-dispatch failure changed')
    failed_attempt = RELEASE_ROOT / 'attempts' / failed_rows[0]['attempt_id']
    check(load(failed_attempt / 'completed.json') == failed_rows[0], 'original failed receipt differs from ledger')
    for stream in ('stdout', 'stderr'):
        entry = failed_rows[0][stream]
        bound(failed_attempt / entry['path'], entry['sha256'], entry['bytes'])
    freeze = load(plan['baseline_freeze']['path'])
    bound(plan['population']['path'], plan['population']['sha256'])
    spec = importlib.util.spec_from_file_location('control_review', ROOT / 'scripts/review-bifrost-v013-controls.py')
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    check(review.audit(ROOT) == load(plan['qualification']['path']), 'control review changed')
    bound(plan['qualification']['path'], plan['qualification']['sha256'])
    check(len(freeze['cases']) == 1108, 'wrong frozen population')
    for case in freeze['cases']:
        bound(case['path'], case['sha256'])
        for fixture in case['fixture_digests']:
            bound(fixture['path'], fixture['sha256'])
    ledger_path = RELEASE_ROOT / 'ledger-v2.jsonl'
    ledger = [json.loads(line) for line in (ROOT / ledger_path).read_text().splitlines()]
    groups = {group['id']: group for group in plan['groups']}
    check(len(ledger) == 20 and len({row['group_id'] for row in ledger}) == 20, 'matrix is incomplete or duplicated')
    check({row['group_id'] for row in ledger} == set(groups), 'matrix group membership differs')
    old_reports = {entry['adapter']: entry for entry in freeze['reports']}
    report_bindings = []
    counts = collections.Counter()
    old_counts = collections.Counter()
    transitions = []
    for receipt in ledger:
        group = groups[receipt['group_id']]
        check(receipt['status'] == 'completed' and receipt['exit_code'] == 0 and not receipt['timed_out'], 'non-completed group')
        check(receipt['source_commit'] == plan['source_commit'], 'mixed execution sources')
        check(receipt['fixture_revision'] == plan['fixture_revision'], 'mixed fixture revisions')
        check(receipt['argv'] == group['argv'], 'command differs from registered plan')
        check(receipt['runner']['sha256'] == plan['tools']['runner']['sha256'] and
              receipt['bifrost']['sha256'] == plan['tools']['bifrost']['sha256'], 'substituted binary')
        check(sorted(receipt['case_ids']) == sorted(group['case_ids']), 'receipt membership differs')
        attempt = RELEASE_ROOT / 'attempts' / receipt['attempt_id']
        check(load(attempt / 'completed.json') == receipt, 'ledger differs from completed receipt')
        for stream in ('stdout', 'stderr'):
            entry = receipt[stream]
            bound(attempt / entry['path'], entry['sha256'], entry['bytes'])
        for entry in receipt['captured_files']:
            bound(attempt / 'capture' / entry['execution_relative'], entry['sha256'], entry['bytes'])
        check(len(receipt['reports']) == len(group['reports']), 'missing staged report')
        for entry, expected in zip(receipt['reports'], group['reports']):
            check(entry['staged_path'] == expected['path'], 'unexpected normalized path')
            bound(entry['original_path'], entry['original_sha256'])
            bound(entry['staged_path'], entry['staged_sha256'])
            staged = load(entry['staged_path'])
            original = load(entry['original_path'])
            check(staged['tool'] == 'bifrost' and staged['tool_version'] == 'bifrost 0.13.0', 'wrong runtime version')
            identity = staged['tool_build_identity']
            check(identity == plan['tools']['bifrost']['build_identity'] or
                  (group['id'].endswith('-native') and identity.startswith(plan['tools']['bifrost']['build_identity'] + ' — ')), 'wrong runtime build')
            check(staged['fixture_revision'] == plan['fixture_revision'], 'wrong report fixture revision')
            check(sorted(row['case_id'] for row in staged['results']) == sorted(expected['case_ids']), 'wrong report membership')
            check(len(staged['results']) == len(expected['case_ids']), 'duplicate report membership')
            if group['id'].endswith('-native'):
                check(all(row['outcome'] == 'unsupported' for row in staged['results']), 'native no-pack state was treated as evaluated coverage')
            restored = json.loads(json.dumps(staged))
            mappings = {entry['captured_path']: entry for entry in entry['raw_output_mappings']}
            check(len(mappings) == len(staged['results']), 'missing raw output mapping')
            for row in restored['results']:
                mapping = mappings[row['raw_output']]
                bound(mapping['captured_path'], mapping['sha256'], mapping['bytes'])
                row['raw_output'] = mapping['execution_relative']
            check(restored == original, 'normalized report changes fields beyond raw_output')
            baseline_entry = old_reports[group['id']]
            bound(baseline_entry['path'], baseline_entry['normalized_report_sha256'])
            baseline = load(baseline_entry['path'])
            old_rows = {row['case_id']: row for row in baseline['results']}
            check(set(old_rows) == set(expected['case_ids']), 'baseline population differs')
            if not group['id'].endswith('-native'):
                check(staged['configuration_hash'] == baseline['configuration_hash'], 'controlled configuration changed')
            for row in staged['results']:
                check(row['outcome'] in OUTCOMES, 'unknown outcome')
                before = old_rows[row['case_id']]['outcome']
                counts[row['outcome']] += 1
                old_counts[before] += 1
                if before != row['outcome']:
                    transitions.append({'adapter': group['id'], 'case_id': row['case_id'], 'before': before, 'after': row['outcome']})
            report_bindings.append({'adapter': group['id'], 'path': entry['staged_path'], 'sha256': entry['staged_sha256'], 'rows': len(staged['results'])})
    check(sum(counts.values()) == plan['fresh_report_rows'], 'wrong fresh row count')
    carried_rows = 0
    carried_counts = collections.Counter()
    raw_carried = 0
    check(len(plan['carried_reports']) == plan['carried_report_partitions'], 'wrong carry count')
    check(plan['carried_reports'] == [entry for entry in freeze['reports'] if entry['adapter'] not in groups], 'carry references changed')
    for entry in plan['carried_reports']:
        bound(entry['path'], entry['normalized_report_sha256'])
        rows = load(entry['path'])['results']
        check(sorted(row['case_id'] for row in rows) == sorted(entry['case_ids']), 'carried membership changed')
        carried_rows += len(rows)
        carried_counts.update(row['outcome'] for row in rows)
        for raw in entry['raw_evidence']:
            bound(raw['path'], raw['sha256'])
            raw_carried += 1
    check(carried_rows == plan['carried_report_rows'] and sum(counts.values()) + carried_rows == plan['expected_report_rows'], 'wrong total row count')
    return {
        'schema_version': 1, 'release': 'v0.9.1', 'status': 'evidence-verified',
        'release_freeze_created': False, 'published': False,
        'plan_sha256': sha(RELEASE_ROOT / 'plan.json'), 'ledger_sha256': sha(ledger_path),
        'execution_source_commit': plan['source_commit'], 'tool': plan['tools']['bifrost'],
        'case_count': 1108, 'fresh_partitions': 20, 'fresh_rows': 1116,
        'carried_partitions': 72, 'carried_rows': 3136, 'carried_raw_refs_verified': raw_carried,
        'total_partitions': 92, 'total_rows': 4252,
        'fresh_outcomes': dict(sorted(counts.items())), 'baseline_bifrost_outcomes': dict(sorted(old_counts.items())),
        'combined_outcomes': dict(sorted((counts + carried_counts).items())),
        'transitions': transitions, 'fresh_reports': sorted(report_bindings, key=lambda x: x['adapter']),
        'performance_claim': 'none; retained execution timings are diagnostic',
        'control_review': {'full_policy_qualification': False, 'measurement_contract': 'verified-with-known-limits'},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = verify()
    if args.check:
        check(load(args.check) == result, 'evidence summary differs from recomputed evidence')
    if args.output:
        with args.output.open('x') as output:
            output.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key:result[key] for key in ('status','fresh_partitions','fresh_rows','total_rows','fresh_outcomes')}))
