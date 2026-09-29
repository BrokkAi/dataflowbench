#!/usr/bin/env python3
"""Check versioned execution planning bindings; never launch an analyzer."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'reports/releases/v0.9.0/execution-v1/contract.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bound(root, reference):
    relative = Path(reference['path'])
    require(not relative.is_absolute() and '..' not in relative.parts, 'escaped reference')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()), 'escaped reference')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == reference['sha256'], 'bound input changed: ' + str(relative))
    return path


def validate(root=ROOT):
    plan = json.loads((root / CONTRACT).read_text())
    preparation = json.loads(bound(root, plan['preparation_plan']).read_text())
    require(plan.get('execution_authorized') is False, 'planning contract must not authorize execution')
    require(plan['parent_plan'] == plan['preparation_plan'], 'parent plan binding mismatch')
    require(plan['input_commits'] == preparation['input_commits'], 'input commits changed')
    require(plan['status'] == 'integration-in-progress-not-executable', 'planning checker cannot grant execution')
    require(plan['population'] == preparation['population'], 'population binding changed')
    require(plan['fixture_revision'] == preparation['fixture_revision'], 'fixture revision changed')
    expected = {g['id']: g for g in preparation['execution_groups']}
    groups = plan['groups']
    require(len(groups) == len({g['id'] for g in groups}) == 84, 'exact 84 groups required')
    require({g['id'] for g in groups} == set(expected), 'group identity mismatch')
    registered = {r['report']: r for r in preparation['reports']}
    for group in groups:
        prior = expected[group['id']]
        for key in ['tool', 'case_ids']:
            require(group[key] == prior[key], 'group ' + key + ' changed')
        require(group['maximum_attempts'] == 2 and group['deadline_seconds'] > 0, 'unbounded group')
        require([r['path'] for r in group['reports']] == prior['reports'], 'report destinations changed')
        for ordinal, mapping in enumerate(group['reports']):
            expected_report = registered[mapping['path']]
            require(mapping['ordinal'] == ordinal, 'report ordinal mismatch')
            require(mapping['case_ids'] == expected_report['case_ids'], 'report membership changed')
            require(mapping['tool'] == expected_report['tool'], 'report tool changed')
            require(mapping['tool_version'] == ('2.27.1' if group['tool'] == 'codeql' else expected_report['historical_identity']['tool_version']), 'tool version drift')
        require(group['historical_seconds'] == max(registered[r]['historical_cost']['wall_seconds'] for r in prior['reports']), 'historical deadline basis changed')
        require(group['deadline_seconds'] == max(600, math.ceil(2 * group['historical_seconds'] + 300)), 'deadline changed')
        require(isinstance(group['environment'], dict) and group['environment'].get('PATH'), 'explicit environment missing')
        argv = group.get('argv', [])
        require(argv and all(isinstance(a, str) and a and '{' not in a for a in argv), 'exact argv required')
        roots = [Path(value) for value in group['output_roots']]
        require(roots and all(not r.is_absolute() and '..' not in r.parts for r in roots), 'unsafe output root')
        require(len(roots) == len(set(roots)), 'duplicate output root')
        for mapping in group['reports']:
            source = Path(mapping['source_path'])
            require(not source.is_absolute() and '..' not in source.parts, 'unsafe report source')
            require(any(source == r or r in source.parents for r in roots), 'uncaptured report source')
        if 'swift-common108' not in group['id']:
            original = prior['command_template']
            exact = list(original)
            exact[0] = plan['tools']['runner']['path']
            if '--codeql' in exact:
                exact[exact.index('--codeql') + 1] = plan['tools']['codeql']['path']
            require(argv == exact, 'command differs beyond reviewed runner and CodeQL pin')
            require(len(group['reports']) == 1 and group['reports'][0]['source_path'] == registered[prior['reports'][0]]['historical_reference']['path'], 'legacy output mapping changed')
            require(argv[1:3] == ['--population', 'v0.9.0'], 'common population flag required')
            if '--codeql' in argv:
                require(argv[argv.index('--codeql') + 1] == plan['tools']['codeql']['path'], 'mixed CodeQL runtime')
        else:
            tool = group['tool']
            stem = 'swift' if tool == 'codeql' else 'joern'
            output = 'reports/raw/' + stem + '-common-v2/current108-v090-01'
            require(argv == ['/usr/bin/python3', 'scripts/run-' + stem + '-common-v2.py', 'execute', '--plan', 'adapters/' + tool + '/swift-common-v2/plan-v090-01/plan.json', '--output', output, '--reservation', 'reports/releases/v0.9.0/execution-v1/' + tool + '-swift-reservation.json'], 'Swift wrapper command drift')
            require(group['output_roots'] == [output], 'Swift output root drift')
            require([r['source_path'] for r in group['reports']] == [output + '/normal/report-' + str(i) + '.json' for i in range(5)], 'Swift partition mapping drift')
    for reference in [*plan['identity_evidence'], *plan['environment_implementation'], plan['codeql_compatibility']]:
        bound(root, reference)
    budget = plan['resource_budget']
    require(budget['serial_analyzers'] == 1 and budget['protected_reserve_gib'] >= 40, 'resource boundary weakened')
    require(budget['minimum_launch_free_gib'] >= sum(budget[k] for k in ['protected_reserve_gib', 'scratch_gib', 'proposed_total_retention_ceiling_gib', 'proposed_working_copy_and_staging_gib']), 'unbudgeted launch capacity')
    require(len(plan['controls']) == 30 and len({c['id'] for c in plan['controls']}) == 30, 'existing control inventory changed')
    require(plan['unresolved'], 'planning blocker list missing')
    return {'groups': len(groups), 'controls': len(plan['controls']), 'executable': False}


if __name__ == '__main__':
    print(json.dumps(validate(), sort_keys=True))
