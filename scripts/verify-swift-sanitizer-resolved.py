#!/usr/bin/env python3
"""Verify separately scoped SSA and resolved numeric-barrier observations."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-resolved-native-v1'
OLD=ROOT/'evidence/swift-sanitizer-qualification-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)

def package(stage,version):
    plan_path=BASE/('sanitizer-'+stage+'-plan-v1.json');plan=read(plan_path);attempt=BASE/('sanitizer-'+stage+'-attempt-01')
    require(plan['scored_activation'] is False and plan['expected_semantic_sink_lines']==[19,27,31] and plan['required_real_safe_sink_absent']==23,'scope/expectations')
    require(plan['aggregate_memory_compliance']==plan['semantic_completeness']=='unproven','uncertainty promotion')
    for field in ['queries','runner_files']:
        for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'preregistered digest: '+name)
    old=read(OLD/'diagnosis-plan.json');require(plan['dataset_files']==old['dataset_files'] and plan['source_archive_sha256']==old['source_archive_sha256']==sha(OLD/'control-source.zip'),'original dataset/archive identity')
    manifest=read(attempt/'manifest.json');require(set(manifest)=={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in manifest.items():require(sha(attempt/name)==digest,'artifact digest: '+name)
    run=read(attempt/'run.json');require(run['plan_sha256']==sha(plan_path) and run['scored_activation'] is False,'run identity')
    names=['flow','barriers','numeric-bases','conversion-identity'];require(set(run['phases'])=={n+s for n in names for s in ['','-decode']},'phase closure')
    for name,c in run['phases'].items():
        require(c['exit_status']==0 and not c['timed_out'] and not c.get('cleanup_error') and c['cleanup_status']=='tracked-processes-stopped','phase failure')
        require(c['deadline_seconds']==60,'phase deadline')
        if not name.endswith('-decode'):require('--ram=2048' in c['argv'] and '--timeout=60' in c['argv'],'analysis limits')
    paths=read(attempt/'library-path.json')['libraryPath'];require(any(p.endswith('/swift-all/'+version) for p in paths) and not any(p.endswith('/swift-all/6.8.4') for p in paths),'library resolution')
    for name in plan['queries']:require((attempt/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query copy')
    rows={n:read(attempt/(n+'.json'))['#select']['tuples'] for n in names}
    for name in ['numeric-bases','conversion-identity']:require(rows[name]==read(OLD/'diagnosis-attempt-01'/(name+'.json'))['#select']['tuples'],'unchanged resolved declaration evidence: '+name)
    return rows

def check_rows(before,after):
    require(before['flow']==[[17,19,87,'adapter-patched-ssa-sanitizer'],[17,31,87,'adapter-patched-ssa-sanitizer']],'SSA-only wrapper isolation')
    require(after['flow']==[[17,n,87,'adapter-patched-resolved-sanitizer'] for n in [19,27,31]],'resolved positive/safe flow separation')
    for rows,local_barrier in [(before,True),(after,False)]:
        barriers=rows['barriers']
        require([21,33,'Swift','Int',True,'DeclRefExpr'] in barriers,'real scalar barrier missing')
        require([25,33,'DataFlowBenchTaintSwift','Int',local_barrier,'DeclRefExpr'] in barriers,'local scalar barrier mismatch')
        require([29,34,'DataFlowBenchTaintSwift','Plain',False,'DeclRefExpr'] in barriers,'plain wrapper incorrectly sanitized')
        local=[r for r in barriers if r[2:4]==['DataFlowBenchTaintSwift','Int']]
        require(local and all(r[4] is local_barrier for r in local),'local barrier coverage')

def verify():
    check_rows(package('ssa','6.8.4-dfb.3'),package('resolved','6.8.4-dfb.4'))
    print('SSA restores Plain; resolved scalar barrier restores local Int; real Swift.Int remains safe. Non-scored diagnostic; fresh/canonical controls are verified separately.')
if __name__=='__main__':verify()
