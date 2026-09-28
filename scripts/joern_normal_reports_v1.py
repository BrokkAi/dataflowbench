"""Joern-specific current108 export; no analyzer run or scoring activation."""
import math
from collections import Counter
from pathlib import Path
from swift_normal_reports_v1 import (ROOT, PARTITION, require, read, sha, repository_file, bound_file, integer, strings, identity, load_population, normalized, configuration_hash)


def phase_sequence(contract, name=None):
    sequence = contract.get('phase_sequence') if name is None else contract.get('phase_sequences', {}).get(name)
    require(isinstance(sequence, list) and len(sequence) >= 2, 'missing phase sequence')
    require(all(isinstance(p, dict) and isinstance(p.get('id'), str) and p['id'] for p in sequence), 'invalid phase ID')
    require(len({p['id'] for p in sequence}) == len(sequence), 'duplicate phase ID')
    require(sequence == [{'id':name,'role':'analysis'} for name in ['typecheck','frontend','query']], 'invalid Joern total-budget phase sequence')
    return sequence


def validate_phases(root, raw, sequence, outcome, diagnostics):
    phases = raw.get('commands')
    require(isinstance(phases, list) and 0 < len(phases) <= len(sequence), 'missing or excess command evidence')
    failed, exhausted, analysis_sum = False, False, 0.0
    for index, reference in enumerate(phases):
        require(not failed and not exhausted, 'commands after failed or exhausted prefix')
        phase = read(bound_file(root, reference))
        expected = sequence[index]
        require(phase.get('phase_id') == expected['id'] and phase.get('role') == expected['role'], 'phase role/order mismatch')
        require(strings(phase.get('argv'), 'phase argv'), 'missing phase command')
        require(type(phase.get('exit_status')) is int and type(phase.get('timed_out')) is bool, 'missing phase status')
        elapsed, deadline = phase.get('elapsed_seconds'), phase.get('deadline_seconds')
        require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (elapsed, deadline)) and deadline > 0, 'invalid phase duration')
        cap = 75 - analysis_sum
        require(deadline <= cap + 0.000001, 'phase deadline exceeds contract or remaining shared budget')
        if expected['role'] == 'analysis':
            analysis_sum += elapsed
        failed = phase['exit_status'] != 0 and not phase['timed_out']
        failed |= phase.get('cleanup_status') != 'tracked-processes-stopped'
        exhausted = phase['timed_out'] or elapsed > deadline
    shared = raw.get('total_elapsed_seconds')
    require(type(shared) in (int, float) and math.isfinite(shared) and shared >= 0, 'missing shared analysis duration')
    require(shared + 0.000001 >= analysis_sum, 'shared duration smaller than phase sum')
    exhausted |= shared > 75
    require(not failed or outcome == 'runner-error', 'failed invocation cannot be hidden')
    require(not exhausted or 'BudgetExhausted' in diagnostics, 'missing raw budget reason')
    require(len(phases) == len(sequence) or failed or exhausted or 'IncompleteExecution' in diagnostics, 'missing terminal phases without incomplete diagnostic')


def validate_config_invocation(root, raw, case, runtime, config_reference):
    """Bind the retained config to the invocation, including moved checkouts."""
    from joern_normal_execution_v1 import compiler_argv, frontend_argv, query_argv
    relative=Path(config_reference['path']).parent
    commands=[read(bound_file(root,r)) for r in raw['commands']]
    require(commands,'missing configuration invocation')
    cwd=Path(commands[0].get('cwd',''))
    require(cwd.is_absolute() and cwd.parts[-len(relative.parts):]==relative.parts,'configuration invocation directory mismatch')
    execution_root=cwd.parents[len(relative.parts)-1]
    expected=[compiler_argv(runtime,case,cwd),frontend_argv(runtime,cwd),query_argv(execution_root,runtime,cwd)]
    require(len(commands)<=3,'excess configuration invocations')
    for command,argv in zip(commands,expected):
        require(command.get('cwd')==str(cwd) and command.get('argv')==argv,'configuration invocation mismatch')


def export(root, plan_path, run):
    """Return separate normal reports and an audit index; write nothing."""
    root = Path(root)
    plan_file = repository_file(root, plan_path)
    plan = read(plan_file)
    population, cases, population_hash = load_population(root)
    require(plan.get('schema') == 'joern-normal-report-plan/v1', 'new prospective plan required')
    require(run.get('schema') == 'joern-normal-report-run/v1', 'new run metadata required')
    require(run.get('plan_sha256') == sha(plan_file), 'run plan binding mismatch')
    for packet in (plan, run):
        require(packet.get('population_sha256') == population_hash and packet.get('fixture_revision') == population['fixture_revision'], 'population binding mismatch')
        require(packet.get('aggregate_resource_qualification') == 'unavailable' and packet.get('scored_activation') is False, 'unqualified lane only')
    registered = integer(plan.get('registered_at_unix_seconds'), 'registration time')
    start = integer(run.get('started_at_unix_seconds'), 'run start')
    end = integer(run.get('ended_at_unix_seconds'), 'run end')
    require(registered < start <= end, 'plan must precede run')
    require(run.get('cold_or_warm') in ('cold', 'warm'), 'missing cache metadata')
    require(plan.get('partition_status') == 'resolved', 'current108 partition unresolved')
    tool = identity(run.get('identity'))
    require(tool['tool'] == 'joern' and tool['tool_version'] == '4.0.628' and tool['adapter_version'] == 'joern-normal-v1', 'Joern identity required')
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
    import re
    require(command['argv'] == [plan['runtime']['joern']], 'wrong Joern identity command')
    require(re.search(r'(?<![0-9.])4\.0\.628(?![0-9.])', bound_file(root,witness.get('stdout')).read_text()), 'wrong Joern version witness')
    contract = read(bound_file(root, plan.get('execution_contract')))
    require(contract.get('aggregate_resource_qualification') == 'unavailable' and contract.get('scored_activation') is False, 'unqualified execution contract required')
    require(contract.get('population_sha256') == population_hash and contract.get('fixture_revision') == population['fixture_revision'], 'execution contract population mismatch')
    require(contract.get('schema') == 'joern-normal-contract/v1' and contract.get('total_wall_clock_seconds') == 75, 'prospective Joern total budget required')
    require(contract.get('memory_policy') == {'fixture_peak_memory_mb':512,'aggregate_enforcement':'unavailable','jvm_heap_request_mb':512}, 'Joern memory qualification unavailable')
    if 'phase_sequences' not in contract:
        phase_sequence(contract)
    configs = plan.get('configurations')
    require(isinstance(configs, dict) and configs, 'missing configuration inventory')
    config_hashes = {}
    for key, files in configs.items():
        require(isinstance(key, str) and key and isinstance(files, list) and files, 'invalid configuration')
        names = [ref['path'] for ref in files]
        require(len(set(names)) == len(names), 'duplicate configuration path')
        config_hashes[key] = configuration_hash(root, files)
    selection = plan.get('cases')
    require(isinstance(selection, dict) and set(selection) == set(cases), 'plan membership mismatch')
    rows = run.get('results')
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), 'missing run rows')
    ids = [row.get('case_id') for row in rows]
    require(all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids)) == 108 and set(ids) == set(cases), 'run membership mismatch')
    from joern_normal_runner_v1 import verify_activation
    require(run.get('activation_receipt') == plan.get('activation_receipt') and isinstance(run.get('activation_receipt'),dict), 'activation receipt binding')
    verify_activation(root,plan)
    reports, index = {}, []
    for row in rows:
        case_id = row['case_id']
        case = cases[case_id]
        planned = selection[case_id]
        key = planned.get('configuration')
        require(key in config_hashes and row.get('configuration') == key, 'configuration routing mismatch')
        raw_path = bound_file(root, row.get('raw'))
        raw = read(raw_path)
        require(raw.get('schema') == 'joern-normal-raw/v1', 'new raw record required')
        for field, expected in [('case_id', case_id), ('plan_sha256', sha(plan_file)), ('population_sha256', population_hash), ('fixture_revision', population['fixture_revision']), ('configuration_hash', config_hashes[key]), ('identity_witness_sha256', run['identity_witness']['sha256']), ('execution_contract_sha256', plan['execution_contract']['sha256'])]:
            require(raw.get(field) == expected, 'raw binding mismatch: ' + field)
        require(raw.get('activation_receipt') == run['activation_receipt'], 'raw activation binding')
        bound_file(root,raw['activation_receipt'])
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
            require(raw.get('capability')==planned.get('capability') and isinstance(raw.get('capability'),dict),'raw capability binding')
            outputs = raw.get('native_outputs')
            require(isinstance(outputs, list) and outputs, 'missing native output evidence')
            for reference in outputs:
                bound_file(root, reference)
            from joern_normal_controls_v1 import config_for
            configs=[r for r in outputs if Path(r['path']).name=='config.json']
            require(len(configs)==1,'one bound native configuration required')
            require(read(bound_file(root,configs[0]))==config_for(root,case,planned['capability']['model_mode']),'native configuration capability mismatch')
            validate_config_invocation(root,raw,case,plan['runtime'],configs[0])
            sequence = phase_sequence(contract, planned.get('phase_sequence'))
            validate_phases(root, raw, sequence, outcome, diagnostics)
        grouping = tuple(case[field] for field in PARTITION) + (key,)
        if grouping not in reports:
            reports[grouping] = dict(schema_version=1, **tool, configuration_hash=config_hashes[key], fixture_revision=population['fixture_revision'], started_at_unix_seconds=start, ended_at_unix_seconds=end, cold_or_warm=run['cold_or_warm'], results=[])
        reports[grouping]['results'].append(dict(case_id=case_id, outcome=outcome, source_anchors=[a['marker'] for a in case['source_anchors']], sink_anchors=[a['marker'] for a in case['sink_anchors']], witness_checkpoints=checkpoints, diagnostics=sorted(set(diagnostics + ['AggregateResourceQualificationUnavailable'])), duration_ms=duration, peak_memory_mb=None, raw_output=row['raw']['path']))
        index.append(dict(case_id=case_id, raw_outcome=raw['raw_outcome'], outcome=outcome, raw_sha256=row['raw']['sha256'], partition=list(grouping)))
    for report in reports.values():
        report['results'].sort(key=lambda row: row['case_id'])
    return {'reports': reports, 'audit': {'population_sha256': population_hash, 'fixture_revision': population['fixture_revision'], 'scored_activation': False, 'profile_counts': dict(Counter(c['model_profile'] for c in cases.values())), 'results': sorted(index, key=lambda row: row['case_id'])}}
