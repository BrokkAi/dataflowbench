#!/usr/bin/env python3
"""Verify independent append identity, instantiated summary edge and separated flows."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-propagator-qualification-v1'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def check_rows(identities, transfers, roles, flows, plan):
    labels = plan['control_labels']
    wanted = {labels[k] for k in plan['expectations']['exact_append_labels']}
    rejected = {labels[k] for k in plan['expectations']['rejected_identity_labels']}
    require(len(identities) == 4 and {r[0] for r in identities} == wanted | rejected, 'nonvacuous append identities')
    for row in identities:
        if row[0] in wanted:
            require(row[1:6] == ['Swift', 'Swift', 'String', 'append(_:)', 1] and
                    row[7:] == [True, True, True], 'exact inout String append and attached manual summary')
        else:
            require(row[8:] == [False, False], 'near-miss accepted as exact append or manual transfer')
    require(len(transfers) == 2 and {r[0] for r in transfers} == wanted, 'instantiated shipped transfer at each real append')
    require(all(r[1] == r[0] == r[3] and r[5] == '' for r in transfers), 'transfer joins or invented row provenance')
    require(all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles) and
            all(r[3] in ['vendor-native', 'adapter-corrected'] for r in flows), 'unknown lane')
    sources = [r for r in roles if r[2] == 'adapter-corrected' and r[3] == 'environment']
    require(len(sources) == 1 and sources[0][0] == labels['SOURCE'], 'independent source')
    require(not [r for r in roles if r[2] == 'vendor-native' and r[3] == 'source'], 'vendor source observation')
    require(len(flows) == 1 and flows[0][0] == labels['SOURCE'] and
            flows[0][1] == labels['POSITIVE_SINK'] and flows[0][3] == 'adapter-corrected', 'independent positive and separating controls')
    sink_lines = {labels[k] for k in ['POSITIVE_SINK', 'SAFE_SINK', 'OWNER_SINK', 'ARITY_SINK']}
    for profile in ['vendor-native', 'adapter-corrected']:
        sinks = [r for r in roles if r[2] == profile and r[3] == 'sink']
        require(len(sinks) == 8 and {r[0] for r in sinks} == sink_lines, 'nonvacuous control sinks')
    require(any(r[:2] == flows[0][1:3] and r[2:] == ['adapter-corrected', 'sink'] for r in roles), 'flow/sink join')


def verify_diagnosis():
    plans = {
        'trace-attempt-01': 'trace-plan.json',
        'trace-attempt-02': 'trace-plan-v3.json',
        'heuristic-attempt-01': 'heuristic-plan.json',
    }
    for directory, plan_name in plans.items():
        path = BASE / directory; plan = read(BASE / plan_name)
        for field in ['queries', 'runner_files']:
            for name, digest in plan[field].items():
                require(sha(ROOT / name) == digest, 'diagnosis preregistration: ' + name)
        manifest = read(path / 'manifest.json')
        require(set(manifest) == {str(p.relative_to(path)) for p in path.rglob('*') if p.is_file()} - {'manifest.json'}, 'diagnosis artifact closure')
        for name, digest in manifest.items():
            require(sha(path / name) == digest, 'diagnosis artifact: ' + name)
        record = read(path / 'run.json')
        require(record['plan_sha256'] == sha(BASE / plan_name) and record['scored_activation'] is False, 'diagnosis scope')
        for name, command in record['phases'].items():
            require(command == read(path / (name + '.command.json')), 'diagnosis command join')
            require(command['deadline_seconds'] == 60 and not command['timed_out'] and
                    command['cleanup_status'] == 'tracked-processes-stopped', 'diagnosis deadline or cleanup')
            if not name.endswith('-decode'):
                require('--ram=2048' in command['argv'] and '--timeout=60' in command['argv'], 'diagnosis analysis budget')
            if directory == 'trace-attempt-01' and name == 'path':
                require(command['exit_status'] != 0 and 'edges/2' in (path / 'path.stderr').read_text(), 'retained compilation failure')
            else:
                require(command['exit_status'] == 0, 'diagnosis phase failure')
    original = read(BASE / 'trace-plan.json')['dataset_files']
    stable = {n: d for n, d in original.items() if not n.startswith('db-swift/default/cache/')}
    require(len(stable) == 414 and read(BASE / 'trace-plan-v3.json')['dataset_files'] == stable and
            read(BASE / 'heuristic-plan.json')['dataset_files'] == stable, 'unchanged source-fact fingerprint')
    rejection = read(BASE / 'trace-preflight-01.json')
    require(rejection['analyzer_invoked'] is False and rejection['all_original_noncache_files_match'] is True and
            rejection['expected_sha256'] != rejection['observed_sha256'], 'retained cache rejection')
    trace = BASE / 'trace-attempt-02'
    require(read(trace / 'summaries.json')['#select']['tuples'] == [], 'wrong-arity summary attribution')
    path = read(trace / 'path.json')
    require({(r[0], r[1], r[3], r[4]) for r in path['#select']['tuples']} ==
            {(11, 15, 23, 94), (23, 94, 23, 87)}, 'retained false-flow path')
    require(any(r[0]['label'] == '.environment' and r[1]['label'] == 'wrong' and
                r[2:] == ['provenance', 'AdditionalTaintStep'] for r in path['edges']['tuples']), 'native edge provenance')
    rows = read(BASE / 'heuristic-attempt-01/heuristic.json')['#select']['tuples']
    require(len(rows) == 4 and {r[0] for r in rows} == {13, 16, 19, 22}, 'nonvacuous additional-step witness')
    require(all(r[2:4] == ['append', ''] and r[0] == r[4] == r[6] for r in rows), 'resolved heuristic arguments')
    require({r[1] for r in rows if r[0] in {19, 22}} == {'DataFlowBenchTaintSwift'}, 'local near-miss provenance')
    pack_files = {r['path']: r['sha256'] for r in read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')}
    vendor = 'codeql/swift-all/6.8.4/codeql/swift/frameworks/Heuristic.qll'
    require(sha(BASE / 'vendor-source' / vendor) == pack_files[vendor], 'shipped heuristic source identity')


def verify(attempt=None):
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
            record['source_commit'] == witness['source_commit'] and record['exit_status'] == 0, 'run provenance')
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
    tuples = lambda name: read(probe / (name + '.json'))['#select']['tuples']
    rows = [tuples(n) for n in ['append-identity', 'append-transfer', 'roles', 'flow']]
    # Evidence integrity can pass while the original qualification gate remains failed.
    try:
        check_rows(*rows, plan)
    except ValueError as error:
        require(str(error) == 'independent positive and separating controls', 'unexpected control failure: ' + str(error))
    else:
        raise ValueError('failed near-miss was silently requalified')
    labels = plan['control_labels']
    require(len(rows[3]) == 2 and {(r[0], r[1], r[3]) for r in rows[3]} == {
        (labels['SOURCE'], labels['POSITIVE_SINK'], 'adapter-corrected'),
        (labels['SOURCE'], labels['ARITY_SINK'], 'adapter-corrected')}, 'retained false-flow evidence changed')
    require(plan['expectations']['assisted_flow_pairs'] == [['SOURCE', 'POSITIVE_SINK']], 'preregistered expectation weakened')
    structural_rows = rows[:3] + [[r for r in rows[3] if r[1] == labels['POSITIVE_SINK']]]
    check_rows(*structural_rows, plan)  # Validate all other guards while preserving the failed full set above.
    require(sha(BASE / 'control-source.zip') == read(BASE / 'trace-plan.json')['source_archive_sha256'], 'source archive provenance')
    verify_diagnosis()
    print('Evidence verified; propagator qualification BLOCKED by retained wrong-arity false flow. No canonical execution or scored activation.')
    return {'status': 'blocked', 'reason': 'wrong-arity near-miss false flow', 'scored_activation': False}



if __name__ == '__main__':
    verify()
