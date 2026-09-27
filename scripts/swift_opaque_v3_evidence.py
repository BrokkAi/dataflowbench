"""Exact staged-fixture evidence binding; no caller-provided qualification flags."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs
from swift_integration_v3 import normalize

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ('adapter-controlled-model-off', 'adapter-controlled-model-on')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_closure(directory):
    manifest = read(directory/'manifest.json')
    files = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    require(set(manifest) == files - {'manifest.json'}, 'artifact closure')
    for name, digest in manifest.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'artifact path')
        require(not (directory/path).is_symlink() and sha(directory/path) == digest, 'artifact digest')


def bind_rows(case, rows):
    source = case['source_anchors'][0]['line_hint']
    sink = case['sink_anchors'][0]['line_hint']
    expected_roles = {(source, 19, p, 'source') for p in PROFILES} | {(sink, 14, p, 'sink') for p in PROFILES}
    require(len(rows['roles']) == 4 and {tuple(r) for r in rows['roles']} == expected_roles, 'exact endpoints')
    positional = case['template_id'] == 'dfb-template-model-propagator-position'
    member = 'select(_:_:)' if positional else ('carry(_:)' if case['polarity'] == 'positive' else 'block(_:)')
    arity = 2 if positional else 1
    expected_identity = [[sink, 'DataFlowBenchTaintSwift', 'Opaque', member, arity, i,
                          'Swift', 'String', 'Swift', 'String',
                          (i == 1 if positional else member == 'carry(_:)')] for i in range(arity)]
    require(sorted(rows['identity']) == sorted(expected_identity), 'resolved wrapper identity')
    expected_flow = [[source, sink, 14, PROFILES[1]]] if case['polarity'] == 'positive' else []
    require(rows['flow'] == expected_flow, 'load-bearing model-off/on separation')
    return 'reached' if expected_flow else 'not-reached'


def bind_case(root, entry, directory, plan):
    verify_closure(directory)
    probe = directory/'probe'
    verify_closure(probe)
    case_path = root/entry['case_path']; case = read(case_path)
    for name, digest in entry['files'].items():
        require(sha(root/name) == digest, 'population fixture digest')
    require((probe/'main.swift').read_bytes() == (case_path.parent/'main.swift').read_bytes(), 'retained source bytes')
    with zipfile.ZipFile(directory/'source.zip') as archive:
        members = [n for n in archive.namelist() if n.endswith('/source/main.swift')]
        require(len(members) == 1 and archive.read(members[0]) == (probe/'main.swift').read_bytes(), 'archived extracted source')
    require(inspect_logs(probe/'log/swift/extractor')['ready_for_observation'], 'extraction log integrity')
    witness = read(probe/'witness.json')
    require(not witness.get('probe_error') and not witness.get('cleanup_error'), 'probe failure')
    require(witness['compiler_sha256'] == plan['compiler_sha256'] and
            witness['extractor_sha256'] == plan['extractor_sha256'], 'runtime identity')
    require(witness['case_sha256'] == sha(directory/'input/control.json'), 'control metadata identity')
    require(witness['analysis_budget'] == {'wall_clock_seconds':60, 'peak_memory_mb':2048} and
            witness['extraction_phase_deadline_seconds'] == 150, 'diagnostic budget identity')
    phases = []
    for name in ['database-create','database-resolve','roles','roles-decode','flow','flow-decode','identity','identity-decode']:
        record = read(probe/(name+'.command.json'))
        require(type(record['exit_status']) is int and record['exit_status'] == 0 and
                record['timed_out'] is False and record['cleanup_status'] == 'tracked-processes-stopped', 'phase completion: '+name)
        phases.append(record)
    for name, digest in plan['queries'].items():
        require(sha(probe/'queries'/Path(name).name) == digest, 'executed query identity')
    rows = {name: read(probe/(name+'.json'))['#select']['tuples'] for name in ['roles','flow','identity']}
    raw = bind_rows(case, rows)
    observation = {'case_id':case['id'], 'outcome':raw, 'execution_budget':witness['analysis_budget'],
                   'endpoints_verified':True, 'extraction_complete':True, 'phases':phases,
                   'rows':rows, 'raw_evidence':str(directory.relative_to(root))}
    return normalize(case, observation)


def verify_attempt(root, directory):
    plan = read(root/'adapters/codeql/swift-opaque-v3/plan.json')
    for field in ['inputs','queries','runner_files']:
        for name, digest in plan[field].items():
            require(sha(root/name) == digest, 'preregistered input: '+name)
    verify_closure(directory)
    run = read(directory/'run.json')
    require(run['plan_sha256'] == sha(root/'adapters/codeql/swift-opaque-v3/plan.json'), 'plan binding')
    population = read(root/'populations/swift-opaque-v3.json')
    require(set(run['cases']) == {e['id'] for e in population['cases']}, 'complete selection')
    results = []
    for entry in population['cases']:
        record = run['cases'][entry['id']]
        if record['status'] != 'observed':
            case = read(root/entry['case_path'])
            results.append(normalize(case, {'case_id':case['id'], 'outcome':'runner-error', 'diagnostic':record}))
        else:
            results.append(bind_case(root, entry, directory/entry['id'], plan))
    return {'scope':'staged-opaque-exact-fixture-diagnostic', 'scored_activation':False,
            'population':'swift-opaque-v3', 'resource_qualification':'unavailable', 'results':results}
