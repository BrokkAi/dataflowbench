#!/usr/bin/env python3
"""Verify a fresh independent conversion control without scored activation."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-resolved-native-v1'
PROFILE='adapter-patched-ssa-resolved'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def check_rows(rows):
    require(rows['flow']==[[15,20,87,PROFILE],[15,35,87,PROFILE]],'positive and near-miss flow separation')
    roles=rows['roles'];require(all(r[2]==PROFILE for r in roles),'profile attribution')
    require([r for r in roles if r[3]!='sink']==[[15,15,PROFILE,'environment']],'source role')
    require({tuple(r[:2]) for r in roles if r[3]=='sink'}=={(line,col) for line in [20,25,30,35,40,42] for col in [32,87]},'sink coverage')
    real={16,17,18,19,21,22,23,24};local={26,27,28,29,31,32,33,34,36,37,38,39,41}
    ids=rows['summary-identity'];require(len(ids)==21 and {r[0] for r in ids}==real|local,'summary identity coverage')
    for r in ids:
        is_real=r[0] in real;module='Foundation' if is_real else 'DataFlowBenchTaintSwift'
        require(r[2]==module and r[3]==('Swift' if r[4]=='String' else module) and r[7] is is_real,'summary declaration provenance')
    for name,count in [('summary-ports',10),('summary-transfer',6),('summary-store',4)]:
        require(len(rows[name])==count and all(r[0] in real for r in rows[name]),'summary applicability: '+name)
    require({r[0] for r in rows['summary-ports']}==real and all(r[3]=='' for r in rows['summary-ports']),'port coverage and origin')
    require({(r[0],r[-1]) for r in rows['summary-store']}=={(16,'CollectionElement'),(21,'CollectionElement'),(19,'OptionalSome'),(24,'OptionalSome')},'content stores')
    require(rows['self-assignment']==[[11,'self',True,True,True,True],[12,'self',True,True,True,True]],'SSA return linkage')

def verify(attempt=None):
    attempt=Path(attempt) if attempt else BASE/'conversion-body-fresh-attempt-01';probe=attempt/'probe';plan_path=BASE/'conversion-body-fresh-plan-v1.json';plan=read(plan_path)
    require(plan['scored_activation'] is False and plan['aggregate_memory_compliance']==plan['semantic_completeness']=='unproven' and plan['ordinary_body_required'] is True and plan['expected_patched_sink_labels']==['POSITIVE_SINK','BODY_SINK'],'preregistration scope')
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
    source=(BASE/'conversion-body-control/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
    with zipfile.ZipFile(attempt/'source.zip') as z:
        members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
    for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
    check_rows({n:read(probe/(n+'.json'))['#select']['tuples'] for n in plan['queries']})
    print('Fresh body/near-miss and SSA controls verified; non-scored.')

if __name__=='__main__':verify()
