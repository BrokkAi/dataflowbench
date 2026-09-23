#!/usr/bin/env python3
"""Verify retained UserDefaults control evidence without promoting scores."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-persistence-qualification-v1'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_integrity(attempt=None):
    attempt = attempt or BASE / 'control-attempt-01'
    plan = read(BASE / 'control-plan.json')
    for field in ['control_files', 'query_files', 'vendor_files', 'runner_files']:
        for name, digest in plan[field].items():
            require(sha(ROOT / name) == digest, 'preregistered file: ' + name)
    require(plan['scored_activation'] is False and plan['aggregate_memory_compliance'] ==
            plan['semantic_completeness'] == 'unproven', 'scope promotion')
    manifest = read(attempt / 'manifest.json')
    require(set(manifest) == {str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()} - {'manifest.json'}, 'artifact closure')
    for name, digest in manifest.items():
        require(sha(attempt / name) == digest, 'raw digest: ' + name)
    record = read(attempt / 'run.json'); probe = attempt / 'probe'; witness = read(probe / 'witness.json')
    require(record['plan_sha256'] == sha(BASE / 'control-plan.json') and
            record['source_commit'] == witness['source_commit'] and record['exit_status'] == 0 and record['scored_activation'] is False, 'run provenance')
    require(witness['status'] == 'unqualified' and not witness.get('probe_error') and not witness.get('cleanup_error'), 'probe failure')
    require(witness['analysis_budget'] == {'wall_clock_seconds':60, 'peak_memory_mb':2048} and
            witness['extraction_phase_deadline_seconds'] == 150, 'phase budgets')
    require(inspect_logs(probe / 'log/swift/extractor')['ready_for_observation'], 'extraction log gate')
    for phase in ['database-create', 'database-resolve'] + [p for name in plan['queries'] for p in [name, name + '-decode']]:
        command = read(probe / (phase + '.command.json'))
        require(command['exit_status'] == 0 and not command['timed_out'] and
                command['cleanup_status'] == 'tracked-processes-stopped', 'phase failure: ' + phase)
        require(command['deadline_seconds'] == (150 if phase == 'database-create' else 60), 'phase deadline')
    source = (BASE / 'control/main.swift').read_bytes()
    require((probe / 'main.swift').read_bytes() == source, 'staged control changed')
    with zipfile.ZipFile(BASE / 'control-source.zip') as archive:
        members = [n for n in archive.namelist() if n.endswith('/source/main.swift')]
        require(len(members) == 1 and archive.read(members[0]) == source, 'archived control changed')
    for name in plan['query_files']:
        require((probe / 'queries' / Path(name).name).read_bytes() == (ROOT / name).read_bytes(), 'executed query drift')
    return plan, probe


def check_structure(identities, keys, roles, plan):
    labels = plan['control_labels']
    names = ['REAL_INIT', 'INIT_PAYLOAD', 'INIT_OTHER', 'REAL_SET', 'SAME_READ', 'OTHER_READ', 'LOCAL_INIT', 'LOCAL_SET', 'LOCAL_READ']
    require(len(identities) == 9 and {r[0] for r in identities} == {labels[n] for n in names}, 'resolved call coverage')
    for name in names:
        row = next(r for r in identities if r[0] == labels[name])
        module = 'DataFlowBenchTaintSwift' if name.startswith('LOCAL') else 'Foundation'
        selector, arity = ('init(suiteName:)', 1) if name.endswith('_INIT') else (
            ('string(forKey:)', 1) if name.endswith('_READ') else ('set(_:forKey:)', 2))
        require(row[2:7] == [module, module, 'UserDefaults', selector, arity], 'resolved method provenance')
    expected_keys = plan['expectations']['literal_keys']
    require(len(keys) == len(expected_keys) and {r[0] for r in keys} == {labels[n] for n in expected_keys}, 'literal key coverage')
    for name, value in expected_keys.items():
        row = next(r for r in keys if r[0] == labels[name])
        target = next(r for r in identities if r[0] == row[0])
        require(row[1:3] == [target[2], target[5]] and row[3:6] == ['forKey', value, row[0]], 'native key identity/join')
    require(all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles), 'unknown lane')
    sources = [r for r in roles if r[3] != 'sink']
    require(len(sources) == 1 and sources[0][0] == labels['SOURCE'] and sources[0][2:] == ['adapter-corrected', 'environment'], 'source lanes')
    for profile in ['vendor-native', 'adapter-corrected']:
        sinks = [r for r in roles if r[2:] == [profile, 'sink']]
        require(len(sinks) == 8 and {r[0] for r in sinks} == {labels[n] for n in ['DIRECT_SINK', 'SAME_SINK', 'OTHER_SINK', 'LOCAL_SINK']}, 'nonvacuous sinks')


def check_flows(flows, roles, plan):
    labels = plan['control_labels']
    wanted = {(labels[a], labels[b], 'adapter-corrected') for a, b in plan['expectations']['assisted_flow_pairs']}
    require(len(flows) == len(wanted) and {(r[0], r[1], r[3]) for r in flows} == wanted, 'missing real same-key flow')
    require(all(any(r[:2] == f[1:3] and r[2:] == [f[3], 'sink'] for r in roles) for f in flows), 'flow/sink join')


def check_qualification(identities, keys, ports, edges, roles, flows, plan):
    check_structure(identities, keys, roles, plan)
    labels = plan['control_labels']
    required = {labels[n] for n in plan['expectations']['real_engagement_labels']}
    require(required <= {r[0] for r in identities if r[7]} and required <= {r[0] for r in ports} and
            required <= {r[0] for r in edges}, 'missing persistence model engagement')
    local = {labels[n] for n in ['LOCAL_SET', 'LOCAL_READ']}
    require(not any(r[0] in local for r in ports + edges), 'local constant-body model overreach')
    check_flows(flows, roles, plan)


def verify():
    plan, probe = verify_integrity()
    require(plan['expectations']['assisted_flow_pairs'] == [['SOURCE', 'DIRECT_SINK'], ['SOURCE', 'SAME_SINK']] and
            plan['expectations']['real_engagement_labels'] == ['REAL_SET', 'SAME_READ', 'OTHER_READ'] and
            plan['expectations']['local_manual_transfer_allowed'] is False, 'expectations weakened')
    identities, keys, ports, edges, roles, flows = [read(probe / (n + '.json'))['#select']['tuples'] for n in
        ['persistence-identity', 'persistence-keys', 'persistence-ports', 'persistence-edges', 'roles', 'flow']]
    check_structure(identities, keys, roles, plan)
    require(all(r[7] is False for r in identities) and ports == [] and edges == [], 'retained absent model engagement changed')
    require(flows == [[12, 13, 87, 'adapter-corrected']], 'retained missing positive changed')
    require(any(r[:2] == flows[0][1:3] and r[2:] == ['adapter-corrected', 'sink'] for r in roles), 'direct baseline sink join')
    for function, args, expected in [
        (check_qualification, (identities, keys, ports, edges, roles, flows, plan), 'missing persistence model engagement'),
        (check_flows, (flows, roles, plan), 'missing real same-key flow')]:
        try:
            function(*args)
        except ValueError as error:
            require(str(error) == expected, 'unexpected qualification failure')
        else:
            raise ValueError('blocked persistence control silently qualified')
    print('Evidence verified; persistence qualification BLOCKED by missing same-key positive and scoped model engagement. Canonical pair unrun; non-scored.')
    return {'status': 'blocked', 'scored_activation': False}


if __name__ == '__main__':
    verify()
