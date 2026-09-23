#!/usr/bin/env python3
"""Verify a fresh independent sanitizer control without scored activation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-resolved-native-v1'
PROFILE='adapter-patched-resolved-sanitizer'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def check_rows(rows):
    spec=importlib.util.spec_from_file_location('resolved',ROOT/'scripts/verify-swift-sanitizer-resolved.py')
    resolved=importlib.util.module_from_spec(spec);spec.loader.exec_module(resolved)
    before={n:read(BASE/'sanitizer-ssa-attempt-01'/(n+'.json'))['#select']['tuples'] for n in ['flow','barriers']}
    resolved.check_rows(before,rows)
    require(all(r[2]==PROFILE for r in rows['roles']),'profile attribution')
    require([r for r in rows['roles'] if r[3]!='sink']==[[17,21,PROFILE,'environment']], 'source role')
    require({tuple(r[:2]) for r in rows['roles'] if r[3]=='sink'}=={(line,col) for line in [19,23,27,31] for col in [32,87]},'sink coverage')
    for name in ['conversion-identity','numeric-bases']:
        require(rows[name]==read(BASE/'sanitizer-resolved-attempt-01'/(name+'.json'))['#select']['tuples'],'fresh resolved declaration match')

def verify(attempt=None):
    attempt=Path(attempt) if attempt else BASE/'sanitizer-fresh-attempt-01';probe=attempt/'probe';plan_path=BASE/'sanitizer-fresh-plan-v1.json';plan=read(plan_path)
    require(plan['scored_activation'] is False and plan['aggregate_memory_compliance']==plan['semantic_completeness']=='unproven' and plan['ordinary_body_required'] is True and plan['expected_patched_sink_labels']==['POSITIVE_SINK','LOCAL_SINK','PLAIN_SINK'],'preregistration scope')
    for field in ['control_files','query_files','vendor_files','runner_files']:
        for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'preregistered digest: '+name)
    for directory in [attempt,probe]:
        manifest=read(directory/'manifest.json');require(set(manifest)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
        for name,digest in manifest.items():require(sha(directory/name)==digest,'artifact digest: '+name)
    run=read(attempt/'run.json');witness=read(probe/'witness.json');prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json');assets=read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
    require(run['plan_sha256']==sha(plan_path) and run['source_commit']==witness['source_commit'] and run['exit_status']==0 and run['scored_activation'] is False,'run provenance')
    require(run['assets']==assets and run['compiler_sha256']==witness['compiler_sha256']==prior['compiler_sha256'] and witness['extractor_sha256']==assets['codeql/swift/tools/osx64/extractor.real'] and run['pack_files_verified']==3398,'runtime provenance')
    require(witness['status']=='unqualified' and witness['population_member'] is False and not witness.get('probe_error') and not witness.get('cleanup_error') and witness['memory_compliance']=='unproven','witness scope/failure')
    require(witness['analysis_budget']=={'wall_clock_seconds':60,'peak_memory_mb':2048} and witness['extraction_phase_deadline_seconds']==150,'witness limits')
    require(inspect_logs(probe/'log/swift/extractor')['ready_for_observation'],'extractor errors')
    require(set(witness['phases'])=={'database-create','database-resolve',*plan['queries']},'phase closure')
    for name in ['database-create','database-resolve']+[n+s for n in plan['queries'] for s in ['','-decode']]:
        c=read(probe/(name+'.command.json'));require(c['exit_status']==0 and not c['timed_out'] and not c.get('cleanup_error') and c['cleanup_status']=='tracked-processes-stopped','phase failure')
        require(c['deadline_seconds']==(150 if name=='database-create' else 60),'phase deadline')
        if name in plan['queries']:require('--ram=2048' in c['argv'] and '--timeout=60' in c['argv'],'analysis bounds')
    source=(ROOT/'evidence/swift-sanitizer-qualification-v1/control/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
    with zipfile.ZipFile(attempt/'source.zip') as z:
        members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
    for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
    check_rows({n:read(probe/(n+'.json'))['#select']['tuples'] for n in plan['queries']})
    print('Fresh sanitizer positives and real scalar near-miss verified; non-scored.')

if __name__=='__main__':verify()
