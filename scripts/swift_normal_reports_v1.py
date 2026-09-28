"""Prospective result/v1 export; no analyzer execution or scoring activation.

Consumes a new registered plan and immutable run records. Historical coverage
assemblers and their contracts are deliberately not changed or promoted.
"""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPULATION = 'populations/swift-synthetic-v3.json'
FIELDS = ('tool', 'tool_version', 'tool_build_identity', 'adapter_version')
PARTITION = ('track', 'model_profile', 'score_tier')
OUTCOMES = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_file(root, relative):
    require(isinstance(relative, str) and relative != '', 'missing artifact path')
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, 'nonrepository artifact path')
    target = root / path
    require(target.is_file() and target.resolve().is_relative_to(root.resolve()), 'missing or escaped artifact')
    return target


def bound_file(root, reference):
    require(isinstance(reference, dict), 'artifact reference required')
    target = repository_file(root, reference.get('path'))
    require(sha(target) == reference.get('sha256'), 'artifact digest mismatch')
    return target


def integer(value, label):
    require(type(value) is int and value >= 0, 'invalid ' + label)
    return value


def strings(value, label):
    require(isinstance(value, list) and all(isinstance(s, str) and s.strip() for s in value), 'invalid ' + label)
    return value


def identity(value):
    require(isinstance(value, dict), 'missing run identity')
    result = {}
    for key in FIELDS:
        text = value.get(key)
        require(isinstance(text, str) and text.strip().lower() not in ('', 'unknown', 'n/a', 'unavailable'), 'missing identity: ' + key)
        result[key] = text
    return result


def load_population(root):
    path = repository_file(root, POPULATION)
    population = read(path)
    require(population.get('population') == 'swift-synthetic-v3', 'wrong population')
    cases, paths = {}, set()
    revision = hashlib.sha256()
    for selected in sorted(population['cases'], key=lambda item: item['path']):
        path = bound_file(root, selected)
        case = read(path)
        case_id = case['id']
        require(case_id not in cases and selected['path'] not in paths, 'duplicate population member')
        require(case_id == selected['id'] and case['language'] == 'swift', 'case identity mismatch')
        for key in (*PARTITION, 'template_id', 'polarity'):
            require(case[key] == selected[key], 'population metadata mismatch: ' + key)
        fixtures = {item['path']: item for item in selected['fixture_digests']}
        require(len(fixtures) == len(selected['fixture_digests']), 'duplicate fixture')
        expected = {str(Path(selected['path']).parent / name) for name in case['fixture_files']}
        require(set(fixtures) == expected, 'fixture membership mismatch')
        revision.update(selected['path'].encode())
        revision.update(path.read_bytes())
        for name in case['fixture_files']:
            fixture = bound_file(root, fixtures[str(Path(selected['path']).parent / name)])
            revision.update(name.encode())
            revision.update(fixture.read_bytes())
        cases[case_id] = case
        paths.add(selected['path'])
    require(len(cases) == 108, 'exact 108 population required')
    require(population['fixture_revision'] == 'sha256:' + revision.hexdigest(), 'selected fixture revision mismatch')
    return population, cases, sha(root / POPULATION)


def normalized(raw_outcome):
    require(isinstance(raw_outcome, str) and raw_outcome in OUTCOMES, 'unknown raw outcome')
    return raw_outcome if raw_outcome in ('runner-error', 'unsupported') else 'inconclusive'


def export(root, plan_path, run):
    """Return separate normal reports and an audit index; write nothing."""
    root = Path(root)
    plan_file = repository_file(root, plan_path)
    plan = read(plan_file)
    population, cases, population_hash = load_population(root)
    require(plan.get('schema') == 'swift-normal-report-plan/v1', 'new prospective plan required')
    require(run.get('schema') == 'swift-normal-report-run/v1', 'new run metadata required')
    require(run.get('plan_sha256') == sha(plan_file), 'run plan binding mismatch')
    for packet in (plan, run):
        require(packet.get('population_sha256') == population_hash and packet.get('fixture_revision') == population['fixture_revision'], 'population binding mismatch')
        require(packet.get('aggregate_resource_qualification') == 'unavailable' and packet.get('scored_activation') is False, 'unqualified lane only')
    registered = integer(plan.get('registered_at_unix_seconds'), 'registration time')
    start = integer(run.get('started_at_unix_seconds'), 'run start')
    end = integer(run.get('ended_at_unix_seconds'), 'run end')
    require(registered < start <= end, 'plan must precede run')
    require(run.get('cold_or_warm') in ('cold', 'warm'), 'missing cache metadata')
    tool = identity(run.get('identity'))
    require(tool == identity(plan.get('identity')), 'identity differs from prospective plan')
    # The runner supplies a structured observation plus the original version
    # command/output. Binding is checked here; tool-specific banner parsing is
    # a runner obligation, never inferred from a version string in this exporter.
    witness = read(bound_file(root, run.get('identity_witness')))
    require(identity(witness.get('observed')) == tool, 'identity witness mismatch')
    command = witness.get('command')
    require(isinstance(command, dict) and strings(command.get('argv'), 'version argv'), 'missing version command')
    require(type(command.get('exit_status')) is int and command['exit_status'] == 0 and command.get('timed_out') is False, 'failed version witness')
    require(command.get('cleanup_status') == 'tracked-processes-stopped', 'version cleanup incomplete')
    witnessed = integer(witness.get('observed_at_unix_seconds'), 'identity observation time')
    require(start <= witnessed <= end, 'identity witness outside run')
    require(bound_file(root, witness.get('stdout')).stat().st_size > 0, 'empty identity stdout')
    contract = read(bound_file(root, plan.get('execution_contract')))
    require(contract.get('aggregate_resource_qualification') == 'unavailable' and contract.get('scored_activation') is False, 'unqualified execution contract required')
    require(contract.get('population_sha256') == population_hash and contract.get('fixture_revision') == population['fixture_revision'], 'execution contract population mismatch')
    require(contract.get('phases') == {'extraction': {'wall_clock_seconds': 150, 'peak_memory_mb': 2048}, 'analysis': {'wall_clock_seconds': 75, 'peak_memory_mb': 2048}}, 'prospective execution budgets required')
    configs = plan.get('configurations')
    require(isinstance(configs, dict) and configs, 'missing configuration inventory')
    config_hashes = {}
    for key, files in configs.items():
        require(isinstance(key, str) and key and isinstance(files, list) and files, 'invalid configuration')
        names = [ref['path'] for ref in files]
        require(len(set(names)) == len(names), 'duplicate configuration path')
        digest = hashlib.sha256()
        for ref in sorted(files, key=lambda ref: ref['path']):
            file = bound_file(root, ref)
            digest.update(ref['path'].encode())
            digest.update(file.read_bytes())
        config_hashes[key] = digest.hexdigest()
    selection = plan.get('cases')
    require(isinstance(selection, dict) and set(selection) == set(cases), 'plan membership mismatch')
    rows = run.get('results')
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), 'missing run rows')
    ids = [row.get('case_id') for row in rows]
    require(all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids)) == 108 and set(ids) == set(cases), 'run membership mismatch')
    reports, index = {}, []
    for row in rows:
        case_id = row['case_id']
        case = cases[case_id]
        planned = selection[case_id]
        key = planned.get('configuration')
        require(key in config_hashes and row.get('configuration') == key, 'configuration routing mismatch')
        raw_path = bound_file(root, row.get('raw'))
        raw = read(raw_path)
        require(raw.get('schema') == 'swift-normal-raw/v1', 'new raw record required')
        for field, expected in [('case_id', case_id), ('plan_sha256', sha(plan_file)), ('population_sha256', population_hash), ('fixture_revision', population['fixture_revision']), ('configuration_hash', config_hashes[key]), ('identity_witness_sha256', run['identity_witness']['sha256']), ('execution_contract_sha256', plan['execution_contract']['sha256'])]:
            require(raw.get(field) == expected, 'raw binding mismatch: ' + field)
        outcome = normalized(raw.get('raw_outcome'))
        require(raw.get('state') == outcome, 'raw special state must preserve normalized outcome')
        duration = integer(raw.get('duration_ms'), 'case duration')
        diagnostics = strings(raw.get('diagnostics'), 'raw diagnostics')
        checkpoints = strings(raw.get('witness_checkpoints'), 'raw checkpoints')
        disposition = planned.get('disposition')
        require(disposition in ('attempt', 'unsupported'), 'missing prospective disposition')
        if outcome == 'unsupported':
            require(disposition == 'unsupported' and raw.get('executed') is False, 'unsupported needs prospective partition')
            decision = read(bound_file(root, planned.get('decision')))
            require(decision.get('case_id') == case_id and decision.get('population_sha256') == population_hash and decision.get('configuration_hash') == config_hashes[key], 'partition binding mismatch')
            require(identity(decision.get('identity')) == tool and decision.get('outcome') == 'unsupported', 'partition identity mismatch')
            require(integer(decision.get('reviewed_at_unix_seconds'), 'partition review time') <= registered, 'retrospective partition decision')
            require(isinstance(decision.get('reason'), str) and decision['reason'].strip(), 'missing partition rationale')
            evidence = decision.get('evidence')
            require(isinstance(evidence, list) and evidence, 'missing partition evidence')
            for reference in evidence:
                bound_file(root, reference)
            require(raw.get('decision_sha256') == planned['decision']['sha256'], 'raw partition binding mismatch')
            require(duration == 0 and checkpoints == [], 'unsupported cannot claim execution')
        else:
            require(disposition == 'attempt' and raw.get('executed') is True, 'missing attempted execution')
            outputs = raw.get('native_outputs')
            require(isinstance(outputs, list) and outputs, 'missing native output evidence')
            for reference in outputs:
                bound_file(root, reference)
            phases = raw.get('commands')
            require(isinstance(phases, list) and phases, 'missing command evidence')
            failed = False
            timed_out = False
            for reference in phases:
                phase = read(bound_file(root, reference))
                require(isinstance(phase, dict) and strings(phase.get('argv'), 'phase argv'), 'missing phase command')
                require(type(phase.get('exit_status')) is int and type(phase.get('timed_out')) is bool, 'missing phase status')
                elapsed, deadline = phase.get('elapsed_seconds'), phase.get('deadline_seconds')
                require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (elapsed, deadline)) and deadline > 0, 'invalid phase duration')
                failed |= phase['exit_status'] != 0 and not phase['timed_out']
                failed |= phase.get('cleanup_status') != 'tracked-processes-stopped'
                timed_out |= phase['timed_out'] or elapsed > deadline
            require(not failed or outcome == 'runner-error', 'failed invocation cannot be hidden')
            require(not timed_out or 'BudgetExhausted' in diagnostics, 'missing raw budget reason')
        grouping = tuple(case[field] for field in PARTITION) + (key,)
        if grouping not in reports:
            reports[grouping] = dict(schema_version=1, **tool, configuration_hash=config_hashes[key], fixture_revision=population['fixture_revision'], started_at_unix_seconds=start, ended_at_unix_seconds=end, cold_or_warm=run['cold_or_warm'], results=[])
        reports[grouping]['results'].append(dict(case_id=case_id, outcome=outcome, source_anchors=[a['marker'] for a in case['source_anchors']], sink_anchors=[a['marker'] for a in case['sink_anchors']], witness_checkpoints=checkpoints, diagnostics=sorted(set(diagnostics + ['AggregateResourceQualificationUnavailable'])), duration_ms=duration, peak_memory_mb=None, raw_output=row['raw']['path']))
        index.append(dict(case_id=case_id, raw_outcome=raw['raw_outcome'], outcome=outcome, raw_sha256=row['raw']['sha256'], partition=list(grouping)))
    for report in reports.values():
        report['results'].sort(key=lambda row: row['case_id'])
    return {'reports': reports, 'audit': {'population_sha256': population_hash, 'fixture_revision': population['fixture_revision'], 'scored_activation': False, 'profile_counts': dict(Counter(c['model_profile'] for c in cases.values())), 'results': sorted(index, key=lambda row: row['case_id'])}}
