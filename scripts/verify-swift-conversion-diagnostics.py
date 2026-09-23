#!/usr/bin/env python3
"""Verify diagnostic evidence while preserving the missing-body blocker."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-resolved-native-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def package(plan_name,attempt_name,names,version="6.8.4-dfb.2"):
    plan_path=BASE/(plan_name+'.json');plan=read(plan_path);attempt=BASE/attempt_name
    for field in ['queries','runner_files']:
        for path,digest in plan[field].items():require(sha(ROOT/path)==digest,'preregistered digest: '+path)
    require(plan['scored_activation'] is False,'score promotion')
    require(sha(BASE/'conversion-body-attempt-01/source.zip')==plan['source_archive_sha256'],'source archive')
    manifest=read(attempt/'manifest.json')
    require(set(manifest)=={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for path,digest in manifest.items():require(sha(attempt/path)==digest,'artifact digest: '+path)
    run=read(attempt/'run.json')
    require(run['plan_sha256']==sha(plan_path) and run['scored_activation'] is False,'run provenance')
    require(set(run['phases'])=={n+s for n in names for s in ['','-decode']},'phase closure')
    for name,command in run['phases'].items():
        require(command['exit_status']==0 and not command['timed_out'] and command['cleanup_status']=='tracked-processes-stopped' and not command.get('cleanup_error'),'phase failure')
        require(command['deadline_seconds']==60,'deadline drift')
        if not name.endswith('-decode'):require('--ram=2048' in command['argv'] and '--timeout=60' in command['argv'],'query limits')
    for path in plan['queries']:require((attempt/'queries'/Path(path).name).read_bytes()==(ROOT/path).read_bytes(),'query identity')
    libraries=read(attempt/'library-path.json')['libraryPath']
    require(any(p.endswith('/swift-all/'+version) for p in libraries) and not any(p.endswith('/swift-all/6.8.4') for p in libraries),'library identity')
    return {n:read(attempt/(n+'.json'))['#select']['tuples'] for n in names}

def check_trace(rows):
    summaries=rows['body-summary'];real={16,17,18,19,21,22,23,24};local={26,27,28,29,31,32,33,34,36,37,38,39,41}
    require(len(summaries)==21 and {r[0] for r in summaries}==real|local,'summary coverage')
    for row in summaries:require(row[3:]==([True,True] if row[0] in real else [False,False]),'summary attachment')
    checkpoints=rows['body-flow']
    require(any(r[0]==32 and r[4]=='bodyEncoded' for r in checkpoints) and any(r[:2]==[12,65] and r[4]=='.value' for r in checkpoints),'body checkpoints missing')
    require(not any(r[0]==35 for r in checkpoints),'retained body gap changed')
    heuristic=rows['initializer-heuristic']
    require([41,'DataFlowBenchTaintSwift','init(data:encoding:unrelated:)',3,41,49,41,30] in heuristic,'initializer heuristic witness missing')

def check_correction(rows):
    require(sorted(rows)==sorted([[15,20,87,'adapter-patched-conversion'],[15,42,87,'adapter-patched-conversion'],[15,20,87,'adapter-patched-resolved-initializer']]),'correction comparison changed')
    return {'initializer_false_flow':'removed in resolved experiment','ordinary_body':'missing; qualification blocked','scored_activation':False}

def check_ssa(before, after, flows):
    require(before == [[11,'self',True,True,True,True],[12,'self',False,False,False,False]], 'original SSA gap changed')
    require(after == [[11,'self',True,True,True,True],[12,'self',True,True,True,True]], 'SSA assignment linkage missing')
    expected = [[15,line,87,profile] for profile,lines in [('adapter-patched-ssa',[20,35,42]),('adapter-patched-ssa-resolved',[20,35])] for line in lines]
    require(sorted(flows)==sorted(expected), 'SSA body/near-miss separation')

def verify():
    check_trace(package('conversion-body-trace-plan-v1','conversion-body-trace-attempt-01',['body-flow','body-summary','initializer-heuristic']))
    report=check_correction(package('conversion-initializer-plan-v1','conversion-initializer-attempt-01',['flow'])['flow'])
    before=package('conversion-self-plan-v1','conversion-self-attempt-01',['assignment-shapes','self-assignment'])
    after=package('conversion-ssa-plan-v1','conversion-ssa-attempt-01',['self-assignment','flow'],'6.8.4-dfb.3')
    check_ssa(before['self-assignment'],after['self-assignment'],after['flow'])
    report['ordinary_body_before_ssa']=report.pop('ordinary_body')
    report['ordinary_body']='restored in SSA follow-up'
    report['SSA_followup']='body flow restored; required positive and near-miss controls observed'
    report['qualification']='non-scored; fresh extraction and canonical controls still required'
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':verify()
