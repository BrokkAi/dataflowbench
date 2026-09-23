#!/usr/bin/env python3
"""Verify retained Data roundtrip control evidence without promoting scores."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-summary-qualification-v1'


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


def check_structure(identities, ports, transfers, stores, roles, plan):
    labels = plan['control_labels']
    real = {labels[n] for n in plan['expectations']['real_call_labels']}
    local = {labels[n] for n in plan['expectations']['local_call_labels']}
    require(len(identities) == 12 and {r[0] for r in identities} == real | local, 'resolved call coverage')
    selectors = [('BYTES', 'Data', 'init(_:)', 1), ('ENCODE', 'Data', 'base64EncodedString(options:)', 1),
                 ('DECODE', 'Data', 'init(base64Encoded:options:)', 2), ('STRING', 'String', 'init(data:encoding:)', 2)]
    for prefix in ['REAL', 'SAFE', 'LOCAL']:
        module = 'DataFlowBenchTaintSwift' if prefix == 'LOCAL' else 'Foundation'
        for suffix, owner, selector, arity in selectors:
            row = next(r for r in identities if r[0] == labels[prefix + '_' + suffix])
            require(row[2:7] == [module, 'Swift' if owner == 'String' else module, owner, selector, arity], 'resolved method provenance')
            if prefix != 'LOCAL':
                require(row[7] is True, 'real manual summary missing')
    require(all(r[3] == '' for r in ports), 'invented catalog origin')
    for prefix in ['REAL', 'SAFE']:
        for suffix in ['BYTES', 'ENCODE', 'DECODE', 'STRING']:
            line = labels[prefix + '_' + suffix]
            port = [line, 'Argument[-1]' if suffix == 'ENCODE' else 'Argument[0]',
                    'ReturnValue.OptionalSome' if suffix == 'STRING' else 'ReturnValue', '']
            require(port in ports, 'real attached port missing')
            if suffix == 'STRING':
                require(any(r[0] == line and r[5] == 'OptionalSome' for r in stores), 'real OptionalSome store missing')
            else:
                require(any(r[0] == line for r in transfers), 'real simple edge missing')
    require(all(r[0] == r[1] == r[3] for r in transfers + stores), 'instantiated call join')
    sources = [r for r in roles if r[3] != 'sink']
    require(len(sources) == 1 and sources[0][0] == labels['SOURCE'] and sources[0][2:] == ['adapter-corrected', 'environment'], 'source lanes')
    for profile in ['vendor-native', 'adapter-corrected']:
        sinks = [r for r in roles if r[2:] == [profile, 'sink']]
        require(len(sinks) == 6 and {r[0] for r in sinks} == {labels[n] for n in ['POSITIVE_SINK', 'SAFE_SINK', 'LOCAL_SINK']}, 'sink coverage')


def check_qualification(identities, ports, transfers, stores, roles, flows, plan):
    check_structure(identities, ports, transfers, stores, roles, plan)
    local = {plan['control_labels'][n] for n in plan['expectations']['local_call_labels']}
    require(not any(r[0] in local and r[7] for r in identities) and
            not any(r[0] in local for r in ports + transfers + stores), 'local constant-body summary overreach')
    check_flows(flows, roles, plan)


def check_flows(flows, roles, plan):
    require(len(flows) == 1 and flows[0][0:2] == [plan['control_labels']['SOURCE'], plan['control_labels']['POSITIVE_SINK']] and
            flows[0][3] == 'adapter-corrected', 'local near-miss false flow')
    require(any(r[:2] == flows[0][1:3] and r[2:] == ['adapter-corrected', 'sink'] for r in roles), 'flow/sink join')


def verify():
    plan, probe = verify_integrity()
    store_plan = read(BASE / 'store-plan.json'); attempt = BASE / 'store-attempt-01'
    require(plan['expectations']['assisted_flow_pairs'] == [['SOURCE', 'POSITIVE_SINK']] and
            plan['expectations']['local_constant_body_manual_transfer_allowed'] is False, 'expectations weakened')
    for field in ['queries', 'runner_files']:
        for name, digest in store_plan[field].items():
            require(sha(ROOT / name) == digest, 'store preregistration')
    require(store_plan['scored_activation'] is False and len(store_plan['dataset_files']) == 422 and
            all(not n.startswith('db-swift/default/cache/') for n in store_plan['dataset_files']), 'store scope/fingerprint')
    require(sha(BASE / 'control-source.zip') == store_plan['source_archive_sha256'], 'archive fingerprint')
    manifest = read(attempt / 'manifest.json')
    require(set(manifest) == {str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()} - {'manifest.json'}, 'store artifact closure')
    for name, digest in manifest.items():
        require(sha(attempt / name) == digest, 'store artifact digest')
    record = read(attempt / 'run.json')
    require(record['scored_activation'] is False and record['plan_sha256'] == sha(BASE / 'store-plan.json') and
            set(record['phases']) == {'summary-store', 'summary-store-decode'}, 'store run provenance')
    for name, command in record['phases'].items():
        require(command == read(attempt / (name + '.command.json')) and command['exit_status'] == 0 and not command['timed_out'] and
                command['deadline_seconds'] == 60 and command['cleanup_status'] == 'tracked-processes-stopped', 'store phase failure')
        if name == 'summary-store':
            require('--ram=2048' in command['argv'] and '--timeout=60' in command['argv'], 'store analysis budget')
    for name in store_plan['queries']:
        require((attempt / 'queries' / Path(name).name).read_bytes() == (ROOT / name).read_bytes(), 'store query drift')
    identities, ports, transfers, roles, flows = [read(probe / (n + '.json'))['#select']['tuples']
        for n in ['summary-identity', 'summary-ports', 'summary-transfer', 'roles', 'flow']]
    stores = read(attempt / 'summary-store.json')['#select']['tuples']
    check_structure(identities, ports, transfers, stores, roles, plan)
    require(flows == [[12, 17, 87, 'adapter-corrected'], [12, 27, 87, 'adapter-corrected']], 'retained false flow changed')
    require(len(ports) == 14 and len(transfers) == 9 and len(stores) == 5 and all(r[7] is True for r in identities), 'retained model evidence changed')
    require({r[0] for r in transfers} == {13, 14, 15, 18, 19, 20, 23, 24, 25} and
            {(r[0], r[5]) for r in stores} == {(13, 'CollectionElement'), (18, 'CollectionElement'), (16, 'OptionalSome'), (21, 'OptionalSome'), (26, 'OptionalSome')}, 'native edge coverage')
    require({tuple(r) for r in ports if r[0] >= 23} == {(23, 'Argument[0]', 'ReturnValue', ''),
        (24, 'Argument[-1]', 'ReturnValue', ''), (25, 'Argument[0]', 'ReturnValue', ''),
        (26, 'Argument[0]', 'ReturnValue.OptionalSome', '')}, 'local attached ports changed')
    for function, args, message in [
        (check_qualification, (identities, ports, transfers, stores, roles, flows, plan), 'local constant-body summary overreach'),
        (check_flows, (flows, roles, plan), 'local near-miss false flow')]:
        try:
            function(*args)
        except ValueError as error:
            require(str(error) == message, 'unexpected qualification failure')
        else:
            raise ValueError('blocked summary control silently qualified')
    print('Evidence verified; Data summary qualification BLOCKED by local constant-body summaries and false flow. Canonical pair unrun; non-scored.')
    return {'status': 'blocked', 'scored_activation': False}


if __name__ == '__main__':
    verify()
