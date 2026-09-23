#!/usr/bin/env python3
"""Verify retained blocked sanitizer evidence without qualifying the family."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-sanitizer-qualification-v1'
LOCAL = 'DataFlowBenchTaintSwift'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def manifest(root):
    rows = read(root / 'manifest.json')
    require(set(rows) == {str(p.relative_to(root)) for p in root.rglob('*')
                         if p.is_file() and p != root / 'manifest.json'}, 'artifact closure')
    for name, digest in rows.items():
        require(sha(root / name) == digest, 'artifact digest: ' + name)


def bound_files(plan, fields):
    for field in fields:
        for name, digest in plan[field].items():
            require(sha(ROOT / name) == digest, 'preregistered input: ' + name)


def check_rows(identities, barriers, bases, roles, flows, plan):
    """Original qualification gate. Expected to fail on the retained observation."""
    labels = plan['control_labels']
    require(len(identities) == 6 and {r[0] for r in identities} ==
            {labels[n] for n in plan['expectations']['resolved_conversion_labels']}, 'conversion identity coverage')
    expected = {
        labels['REAL_PARSE']: ['Swift', 'Swift', 'FixedWidthInteger', 'init(_:radix:)', 2],
        labels['REAL_RENDER']: ['Swift', 'Swift', 'String', 'init(_:radix:uppercase:)', 3],
        labels['LOCAL_PARSE']: [LOCAL, LOCAL, 'Int', 'init(_:radix:)', 2],
        labels['LOCAL_RENDER']: [LOCAL, 'Swift', 'String', 'init(_:radix:)', 2],
        labels['PLAIN_PARSE']: [LOCAL, LOCAL, 'Plain', 'init(_:radix:)', 2],
        labels['PLAIN_RENDER']: [LOCAL, 'Swift', 'String', 'init(_:radix:)', 2],
    }
    require(all(r[2:7] == expected[r[0]] for r in identities), 'resolved initializer provenance')
    require(all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles) and
            all(r[3] in ['vendor-native', 'adapter-corrected'] for r in flows), 'unknown lane')
    sources = [r for r in roles if r[3] != 'sink']
    require(len(sources) == 1 and sources[0][0] == labels['SOURCE'] and
            sources[0][2:] == ['adapter-corrected', 'environment'], 'source lane coverage')
    sink_lines = {labels[n] for n in ['POSITIVE_SINK', 'SAFE_SINK', 'LOCAL_SINK', 'PLAIN_SINK']}
    for profile in ['vendor-native', 'adapter-corrected']:
        sinks = [r for r in roles if r[2:] == [profile, 'sink']]
        require(len(sinks) == 8 and {r[0] for r in sinks} == sink_lines, 'nonvacuous sinks')
    require(all(any(r[:2] == f[1:3] and r[2:] == [f[3], 'sink'] for r in roles)
                for f in flows), 'flow/sink join')
    real = [r for r in barriers if r[0] == labels['REAL_RENDER'] and r[2:4] == ['Swift', 'Int'] and r[5] == 'DeclRefExpr']
    plain = [r for r in barriers if r[0] == labels['PLAIN_RENDER'] and r[2:4] == [LOCAL, 'Plain'] and r[5] == 'DeclRefExpr']
    local = [r for r in barriers if r[0] == labels['LOCAL_RENDER'] and r[2:4] == [LOCAL, 'Int'] and r[5] == 'DeclRefExpr']
    require(len(real) == len(local) == len(plain) == 1 and real[0][4] is True and
            plain[0][4] is False, 'nonvacuous typed barrier controls')
    require(any(r[:4] == real[0][:4] and r[4] == 'Swift' for r in bases), 'real numeric base provenance')
    require(local[0][4] is False, 'spurious local numeric barrier')
    wanted = {(labels[a], labels[b], 'adapter-corrected') for a, b in plan['expectations']['assisted_flow_pairs']}
    require(len(flows) == len(wanted) and {(r[0], r[1], r[3]) for r in flows} == wanted,
            'missing independent wrapper flows')


def verify():
    plan = read(BASE / 'control-plan.json')
    diagnosis = read(BASE / 'diagnosis-plan.json')
    bound_files(plan, ['control_files', 'query_files', 'vendor_files', 'runner_files'])
    bound_files(diagnosis, ['queries', 'runner_files'])
    require(plan['scored_activation'] is False and diagnosis['scored_activation'] is False and
            plan['aggregate_memory_compliance'] == plan['semantic_completeness'] == 'unproven', 'scope promotion')
    require(plan['expectations']['assisted_flow_pairs'] == [['SOURCE', 'POSITIVE_SINK'], ['SOURCE', 'LOCAL_SINK'], ['SOURCE', 'PLAIN_SINK']] and
            plan['expectations']['local_and_plain_value_barriers_allowed'] is False and
            plan['expectations']['real_integer_barrier_required'] is True, 'expectations weakened')
    attempt = BASE / 'control-attempt-01'; probe = attempt / 'probe'
    diag = BASE / 'diagnosis-attempt-01'
    manifest(attempt); manifest(diag)
    record = read(attempt / 'run.json'); witness = read(probe / 'witness.json')
    require(record['plan_sha256'] == sha(BASE / 'control-plan.json') and
            record['source_commit'] == witness['source_commit'] and record['scored_activation'] is False, 'control provenance')
    require(witness['status'] == 'unqualified' and witness['probe_error'] == 'query failed or timed out; stop and retain scratch' and
            not witness.get('cleanup_error'), 'retained query failure')
    require(witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048} and
            witness['extraction_phase_deadline_seconds'] == 150 and witness['memory_compliance'] == 'unproven', 'diagnostic budgets')
    require(inspect_logs(probe / 'log/swift/extractor')['ready_for_observation'], 'extraction logs')
    phases = ['database-create', 'database-resolve', 'roles', 'roles-decode', 'flow', 'flow-decode', 'identity', 'identity-decode', 'conversion-identity']
    require({p.name.removesuffix('.command.json') for p in probe.glob('*.command.json')} == set(phases), 'initial phase closure')
    for name in phases:
        command = read(probe / (name + '.command.json'))
        require(not command['timed_out'] and command['cleanup_status'] == 'tracked-processes-stopped' and
                command['deadline_seconds'] == (150 if name == 'database-create' else 60), 'control phase budget/cleanup')
        if name == 'conversion-identity':
            require(command['exit_status'] != 0 and 'empty relation' in (probe / (name + '.stderr')).read_text(), 'retained compile failure')
        else:
            require(command['exit_status'] == 0, 'unexpected initial phase failure')
    source = (BASE / 'control/main.swift').read_bytes()
    require((probe / 'main.swift').read_bytes() == source, 'staged source')
    require(sha(BASE / 'control-source.zip') == diagnosis['source_archive_sha256'], 'archive digest')
    with zipfile.ZipFile(BASE / 'control-source.zip') as archive:
        members = [n for n in archive.namelist() if n.endswith('/source/main.swift')]
        require(len(members) == 1 and archive.read(members[0]) == source, 'archived source')
    for name in plan['query_files']:
        require((probe / 'queries' / Path(name).name).read_bytes() == (ROOT / name).read_bytes(), 'original query drift')
    record = read(diag / 'run.json')
    require(record['plan_sha256'] == sha(BASE / 'diagnosis-plan.json') and record['scored_activation'] is False, 'diagnosis scope')
    require(len(diagnosis['dataset_files']) == 424 and all(not n.startswith('db-swift/default/cache/') for n in diagnosis['dataset_files']), 'source-data fingerprint')
    phases = [p for name in ['conversion-identity', 'barriers', 'numeric-bases'] for p in [name, name + '-decode']]
    require(set(record['phases']) == set(phases), 'diagnosis phase closure')
    for name in phases:
        command = read(diag / (name + '.command.json'))
        require(command == record['phases'][name] and command['exit_status'] == 0 and not command['timed_out'] and
                command['deadline_seconds'] == 60 and command['cleanup_status'] == 'tracked-processes-stopped', 'diagnosis phase failure')
        if not name.endswith('-decode'):
            require('--ram=2048' in command['argv'] and '--timeout=60' in command['argv'], 'diagnosis query budget')
    for name in diagnosis['queries']:
        require((diag / 'queries' / Path(name).name).read_bytes() == (ROOT / name).read_bytes(), 'diagnosis query drift')
    rows = [read(diag / (n + '.json'))['#select']['tuples'] for n in ['conversion-identity', 'barriers', 'numeric-bases']]
    rows += [read(probe / (n + '.json'))['#select']['tuples'] for n in ['roles', 'flow']]
    require(rows[4] == [[17, 19, 87, 'adapter-corrected']], 'retained missing flows changed')
    require({tuple(r) for r in rows[2] if r[2] == LOCAL} ==
            {(line, col, LOCAL, 'Int', LOCAL, 'Numeric') for line, col in [(6, 52), (13, 51), (25, 33)]}, 'local numeric base provenance')
    require({tuple(r) for r in rows[1] if r[2:4] == [LOCAL, 'Int']} ==
            {(line, col, LOCAL, 'Int', True, 'DeclRefExpr') for line, col in [(6, 52), (13, 51), (25, 33)]}, 'retained local barrier witnesses')
    try:
        check_rows(*rows, plan)
    except ValueError as error:
        require(str(error) == 'spurious local numeric barrier', 'unexpected qualification failure: ' + str(error))
    else:
        raise ValueError('blocked control silently qualified')
    # Independently expose the second failure without changing any retained data.
    import copy
    without_local_barrier = copy.deepcopy(rows)
    for row in without_local_barrier[1]:
        if row[2:4] == [LOCAL, 'Int']:
            row[4] = False
    try:
        check_rows(*without_local_barrier, plan)
    except ValueError as error:
        require(str(error) == 'missing independent wrapper flows', 'unexpected flow control failure')
    else:
        raise ValueError('missing wrapper flows silently accepted')
    print('Evidence verified; sanitizer qualification BLOCKED: spurious local numeric barrier and missing wrapper flows. Canonical pair unrun; non-scored.')
    return {'status': 'blocked', 'scored_activation': False}


if __name__ == '__main__':
    verify()
