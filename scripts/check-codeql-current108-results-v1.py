#!/usr/bin/env python3
"""Replay CodeQL current108 compact evidence; never launches an analyzer.

This checker requires the full 108-row run envelope and retained decoded query
rows, command records, and report exports. It intentionally does not require or
replay the full CodeQL database bytes; database closure evidence remains the
runner's recorded inventory, so this is a compact command/source/query replay.
Aggregate resource qualification is unavailable and scoring remains disabled.
"""
from collections import Counter
from pathlib import Path
import json
import shlex

from swift_normal_reports_v1 import (
    ROOT, bound_file, configuration_hash, export, identity, load_population,
    normalized, phase_sequence, read, require, sha, validate_phases,
)
from swift_normal_runner_v1 import patched_identity, query_files
from swift_persistence_coverage import CoverageStatus, assess_coverage
from swift_v3_runner import lane, observe


PLAN = 'adapters/codeql/swift-normal-v1/plan-2026-09-28-06/plan.json'
PLAN_SHA256 = 'a91c0571b588e63977611064d649914827d1497b9988e52b4f8b8622540c7bcd'
RUN = 'reports/raw/swift-normal-v1/current108-2026-09-29-01'
OUTCOMES = {'reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error'}
UNQUALIFIED_OUTCOMES = {'inconclusive', 'unsupported', 'runner-error'}


def decoded_rows(root, raw, name, case_id):
    """Read exactly one hash-bound decoded query result from this case."""
    references = [item for item in raw.get('native_outputs', [])
                  if Path(item.get('path', '')).name == name + '.json']
    require(len(references) == 1, 'decoded evidence membership: ' + name)
    path = Path(references[0]['path'])
    require(path.parts[:5] == (*Path(RUN).parts, case_id), 'decoded evidence path: ' + name)
    require(not (root / path).is_symlink(), 'decoded evidence symlink: ' + name)
    bqrs = [item for item in raw.get('native_outputs', [])
            if Path(item.get('path', '')).name == name + '.bqrs']
    require(len(bqrs) == 1, 'BQRS evidence membership: ' + name)
    require(Path(bqrs[0]['path']).parts[:5] == (*Path(RUN).parts, case_id)
            and not (root / bqrs[0]['path']).is_symlink(),
            'BQRS evidence path: ' + name)
    bound_file(root, bqrs[0])
    packet = read(bound_file(root, references[0]))
    require(isinstance(packet, dict) and isinstance(packet.get('#select'), dict)
            and isinstance(packet['#select'].get('tuples'), list),
            'malformed decoded evidence: ' + name)
    return packet['#select']['tuples']


def rederive_outcome(root, raw, case, sequence, commands):
    """Derive the semantic result from decoded rows after a clean full run."""
    phases = [read(bound_file(root, reference)) for reference in commands]
    complete_success = len(phases) == len(sequence) and all(
        phase.get('exit_status') == 0
        and phase.get('timed_out') is False
        and phase.get('cleanup_status') == 'tracked-processes-stopped'
        and type(phase.get('elapsed_seconds')) in (int, float)
        and type(phase.get('deadline_seconds')) in (int, float)
        and phase['elapsed_seconds'] <= phase['deadline_seconds']
        for phase in phases
    )
    raw_outcome = raw.get('raw_outcome')
    require(raw_outcome in OUTCOMES, 'unknown raw outcome')
    diagnostics = raw.get('diagnostics', [])
    require(isinstance(diagnostics, list) and all(isinstance(item, str) for item in diagnostics),
            'invalid raw diagnostics')
    elapsed = raw.get('analysis_elapsed_seconds')
    require(type(elapsed) in (int, float) and elapsed >= 0,
            'invalid shared analysis duration')
    if ('IncompleteExecution' in diagnostics or 'BudgetExhausted' in diagnostics
            or elapsed > 75):
        require(raw_outcome in UNQUALIFIED_OUTCOMES,
                'incomplete/budget-exhausted execution was promoted')
        return raw_outcome, diagnostics
    if not complete_success:
        # A failed or partial prefix cannot support a semantic observation.
        # Keep the runner's typed failure/incompleteness state intact.
        require(raw_outcome in {'inconclusive', 'runner-error'},
                'partial execution promoted to semantic outcome')
        return raw_outcome, diagnostics

    try:
        roles = decoded_rows(root, raw, 'roles', case['id'])
        flows = decoded_rows(root, raw, 'flow', case['id'])
        outcome, diagnostics = observe(case, roles, flows, lane(case))
        if case['template_id'] == 'dfb-template-native-persistence':
            coverage = decoded_rows(root, raw, 'coverage', case['id'])
            scopes = decoded_rows(root, raw, 'scopes', case['id'])
            assessment = assess_coverage(coverage, [row[0] for row in scopes])
            if assessment.status is CoverageStatus.INCOMPLETE:
                outcome = 'inconclusive'
                diagnostics.extend(assessment.reasons)
        # A failed closure snapshot invalidates an otherwise complete result.
        closure_diagnostics = [item for item in raw.get('diagnostics', [])
                               if item.startswith('ArtifactClosureFailed:')]
        if raw.get('closure_status') == 'incomplete' or closure_diagnostics:
            if outcome not in {'inconclusive', 'runner-error'}:
                outcome = 'inconclusive'
            diagnostics = list(diagnostics) + closure_diagnostics
        return outcome, diagnostics
    except Exception as error:
        # The runner records decode/shape/observation exceptions as runner-error.
        require(str(error) in raw.get('diagnostics', []),
                'independent replay error missing from raw diagnostics')
        return 'runner-error', [str(error)]


def expected_command_argv(root, plan, case, case_dir, phase_id):
    """Reconstruct the runner's registered command shape from plan and case."""
    runtime = plan['runtime']
    source = case_dir / 'source'
    database = case_dir / 'database'
    cli = runtime['codeql']
    if phase_id == 'extract':
        compile_argv = [runtime['compiler'], '-swift-version', '6', '-Onone',
                        '-sdk', runtime['sdk'], '-target', 'arm64-apple-macosx26.5',
                        '-module-name', 'DataFlowBenchTaintSwift',
                        '-module-cache-path', str(case_dir / 'cache')]
        compile_argv += [str(source / name) for name in case['fixture_files']]
        compile_argv += ['-o', str(case_dir / 'never-executed')]
        return [cli, 'database', 'create', str(database), '--language=swift',
                '--search-path=' + runtime['extractor_root'],
                '--source-root=' + str(source), '--threads=2', '--ram=2048',
                '--command=' + shlex.join(compile_argv)]
    if phase_id == 'resolve-database':
        return [cli, 'resolve', 'database', '--format=json', str(database)]

    query_name = phase_id.removesuffix('-decode')
    query = root / query_files(case)[query_name].relative_to(ROOT)
    if phase_id.endswith('-decode'):
        return [cli, 'bqrs', 'decode', str(case_dir / (query_name + '.bqrs')),
                '--format=json', '--output=' + str(case_dir / (query_name + '.json'))]
    return [cli, 'query', 'run', str(query), '--database=' + str(database),
            '--output=' + str(case_dir / (phase_id + '.bqrs')),
            '--additional-packs=' + runtime['packs'], '--threads=2', '--ram=2048']


def verify(root=ROOT):
    root = Path(root)
    plan_path = root / PLAN
    require(sha(plan_path) == PLAN_SHA256, 'registered plan 06 digest mismatch')
    plan = read(plan_path)
    run_dir = root / RUN
    require(not (run_dir / 'stop.json').exists(), 'stopped run cannot qualify as current108')
    run_path = run_dir / 'run.json'
    require(run_path.is_file(), 'missing run.json')
    run = read(run_path)
    manifest = read(run_dir / 'portable-files.json')
    require(manifest.get('schema') == 'swift-codeql-compact-evidence/v1',
            'missing portable evidence inventory')
    references = manifest.get('files', [])
    names = [ref.get('path') for ref in references]
    require(references and len(names) == len(set(names)),
            'portable evidence inventory membership')
    for reference in references:
        artifact = bound_file(root, reference)
        require(artifact.is_relative_to(run_dir) and not artifact.is_symlink(),
                'portable evidence inventory escaped run')

    population, cases, population_hash = load_population(root)
    require(plan.get('schema') == 'swift-normal-report-plan/v1', 'wrong plan schema')
    require(plan.get('population_sha256') == population_hash
            and plan.get('fixture_revision') == population['fixture_revision'],
            'plan population binding')
    require(plan.get('aggregate_resource_qualification') == 'unavailable'
            and plan.get('scored_activation') is False,
            'plan must remain unqualified and unscored')
    selection = plan.get('cases')
    require(isinstance(selection, dict) and set(selection) == set(cases)
            and all(item.get('disposition') == 'attempt'
                    and item.get('configuration') == 'patched-codeql'
                    for item in selection.values()),
            'plan must register exactly 108 attempts')
    rows = run.get('results')
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows),
            'missing run rows')
    ids = [row.get('case_id') for row in rows]
    require(all(isinstance(case_id, str) for case_id in ids)
            and len(ids) == len(set(ids)) == 108 and set(ids) == set(cases),
            'exact 108 run membership required')
    require(run.get('plan_sha256') == PLAN_SHA256, 'run plan binding mismatch')
    require(run.get('population_sha256') == population_hash
            and run.get('fixture_revision') == population['fixture_revision'],
            'run population binding')
    require(run.get('aggregate_resource_qualification') == 'unavailable'
            and run.get('scored_activation') is False,
            'run must remain unqualified and unscored')
    require(type(run.get('started_at_unix_seconds')) is int
            and type(run.get('ended_at_unix_seconds')) is int
            and plan['registered_at_unix_seconds'] < run['started_at_unix_seconds']
            <= run['ended_at_unix_seconds'], 'run time envelope')

    tool = identity(run.get('identity'))
    require(tool == identity(plan.get('identity')), 'run identity differs from plan')
    witness = read(bound_file(root, run.get('identity_witness')))
    require(identity(witness.get('observed')) == tool, 'runtime identity witness mismatch')
    version = witness.get('command')
    runtime = plan['runtime']
    require(isinstance(version, dict)
            and version.get('argv') == [runtime['codeql'], 'version', '--format=json']
            and version.get('exit_status') == 0
            and version.get('timed_out') is False
            and type(version.get('elapsed_seconds')) in (int, float)
            and type(version.get('deadline_seconds')) in (int, float)
            and 0 <= version['elapsed_seconds'] <= version['deadline_seconds'] <= 30
            and version.get('cleanup_status') == 'tracked-processes-stopped',
            'CodeQL version command failed or mismatched')
    observed_at = witness.get('observed_at_unix_seconds')
    require(type(observed_at) is int
            and run['started_at_unix_seconds'] <= observed_at <= run['ended_at_unix_seconds'],
            'CodeQL identity observation time')
    banner = read(bound_file(root, witness.get('stdout')))
    require(patched_identity(banner, runtime['pins']) == tool,
            'CodeQL runtime banner does not match plan pins')

    execution_root = Path(version.get('cwd', ''))
    require(execution_root.is_absolute(), 'missing absolute execution working directory')

    contract = read(bound_file(root, plan.get('execution_contract')))
    require(contract.get('aggregate_resource_qualification') == 'unavailable'
            and contract.get('scored_activation') is False,
            'execution contract must remain unqualified and unscored')
    configuration_hashes = {
        name: configuration_hash(root, references)
        for name, references in plan['configurations'].items()
    }

    independent = {}
    for row in rows:
        case_id = row['case_id']
        case = cases[case_id]
        case_dir = run_dir / case_id
        raw_ref = row.get('raw')
        require(isinstance(raw_ref, dict)
                and raw_ref.get('path') == str(Path(RUN) / case_id / 'raw.json'),
                'case raw path mismatch: ' + case_id)
        raw = read(bound_file(root, raw_ref))
        require(raw.get('schema') == 'swift-normal-raw/v1'
                and raw.get('case_id') == case_id
                and row.get('configuration') == selection[case_id]['configuration'],
                'raw case identity/configuration mismatch: ' + case_id)
        for field, expected in (
            ('plan_sha256', PLAN_SHA256),
            ('population_sha256', population_hash),
            ('fixture_revision', population['fixture_revision']),
            ('configuration_hash', configuration_hashes['patched-codeql']),
            ('identity_witness_sha256', run['identity_witness']['sha256']),
            ('execution_contract_sha256', plan['execution_contract']['sha256']),
        ):
            require(raw.get(field) == expected, 'raw binding mismatch: ' + field)
        require(raw.get('executed') is True, 'current108 row was not attempted: ' + case_id)
        require(raw.get('state') == normalized(raw.get('raw_outcome')),
                'raw state/outcome mismatch: ' + case_id)
        commands = raw.get('commands')
        sequence = phase_sequence(contract, selection[case_id]['phase_sequence'])
        validate_phases(root, raw, sequence, raw['raw_outcome'], raw.get('diagnostics'))
        source_dir = case_dir / 'source'
        source_entries = list(source_dir.rglob('*'))
        require(all(not path.is_symlink() for path in source_entries),
                'symlink in retained fixture sources: ' + case_id)
        source_files = {str(path.relative_to(source_dir)) for path in source_entries
                        if path.is_file()}
        require(source_files == set(case['fixture_files']),
                'retained fixture source membership: ' + case_id)
        population_entry = next(item for item in population['cases'] if item['id'] == case_id)
        canonical_dir = (root / population_entry['path']).parent
        for fixture in case['fixture_files']:
            require((source_dir / fixture).read_bytes() == (canonical_dir / fixture).read_bytes(),
                    'retained fixture source differs from population: ' + case_id)
        require(len(commands) <= len(sequence), 'excess command records: ' + case_id)
        for reference, phase_spec in zip(commands, sequence):
            command_path = bound_file(root, reference)
            require(command_path.is_relative_to(case_dir) and not command_path.is_symlink(),
                    'phase command escaped case evidence: ' + case_id)
            command = read(command_path)
            require(command.get('cwd') == str(execution_root)
                    and command.get('argv') == expected_command_argv(
                        execution_root, plan, case, execution_root / RUN / case_id, phase_spec['id']),
                    'CodeQL command prefix/arguments mismatch: ' + case_id + ':' + phase_spec['id'])
        derived, derived_diagnostics = rederive_outcome(root, raw, case, sequence, commands)
        require(raw['raw_outcome'] == derived,
                'decoded evidence/raw outcome mismatch: ' + case_id)
        require(set(derived_diagnostics) <= set(raw.get('diagnostics', [])),
                'decoded evidence/raw diagnostics mismatch: ' + case_id)
        independent[case_id] = derived

    # Replay the canonical report projection, then compare every exported byte
    # structure. This is a compact report replay and does not open DB payloads.
    bundle = export(root, PLAN, run)
    normal_dir = run_dir / 'normal'
    require(normal_dir.is_dir(), 'missing exported normal reports')
    report_names = [f'report-{index}.json'
                    for index in range(len(bundle['reports']))]
    expected_files = {'audit.json', *report_names}
    actual_files = {path.name for path in normal_dir.iterdir() if path.is_file()}
    require(actual_files == expected_files, 'normal report membership')
    require(read(normal_dir / 'audit.json') == bundle['audit'], 'normal audit drift')
    require(bundle['audit'].get('scored_activation') is False,
            'score activation must remain false')
    report_outcomes = Counter()
    reports = list(bundle['reports'].values())
    for index, report in enumerate(reports):
        require(read(normal_dir / report_names[index]) == report,
                'normal report drift: ' + report_names[index])
        for result in report['results']:
            case_id = result['case_id']
            require(result['outcome'] == normalized(independent[case_id]),
                    'report outcome differs from independent replay: ' + case_id)
            require(result['outcome'] in UNQUALIFIED_OUTCOMES,
                    'unqualified run promoted a scored outcome: ' + case_id)
            require('AggregateResourceQualificationUnavailable' in result['diagnostics'],
                    'unqualified result lacks resource diagnostic: ' + case_id)
            report_outcomes[result['outcome']] += 1
    return {
        'rows': len(rows),
        'attempted': sum(read(bound_file(root, row['raw'])).get('executed') is True
                         for row in rows),
        'raw_outcomes': dict(Counter(
            read(bound_file(root, row['raw']))['raw_outcome'] for row in rows)),
        'report_outcomes': dict(report_outcomes),
        'scored_activation': False,
        'replay_scope': 'compact-command-source-query; full CodeQL database replay not required',
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
