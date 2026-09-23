#!/usr/bin/env python3
"""Verify a Objective-C opaque activation control without scored activation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-opaque-objc-v1'
PROFILES=('adapter-controlled-model-off','adapter-controlled-model-on')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def check_rows(rows):
    expected={(26,27,14,p) for p in PROFILES}|{(26,n,14,PROFILES[1]) for n in [28,30]}
    require(len(rows['flow'])==4 and {tuple(r) for r in rows['flow']}==expected,'load-bearing opacity/position flow separation')
    require(len(rows['roles'])==14 and all(r[2] in PROFILES for r in rows['roles']),'role profile attribution')
    for profile in PROFILES:
        require(len([r for r in rows['roles'] if r[2]==profile and r[3]=='source' and r[0]==26])==1,'source role')
        require({r[0] for r in rows['roles'] if r[2:]==[profile,'sink']}==set(range(27,33)),'sink coverage')
    expected_identity=[]
    for line,member,arity in [(28,'carry(_:)',1),(29,'block(_:)',1),(30,'select(_:_:)',2),(31,'select(_:_:)',2),(32,'carry(_:)',1)]:
        for position in range(arity):
            modeled=member=='carry(_:)' or (member=='select(_:_:)' and position==1)
            expected_identity.append([line,'DataFlowBenchTaintSwift','Opaque',member,arity,position,'Swift','String','Swift','String',modeled])
    require(sorted(rows['identity'])==sorted(expected_identity),'resolved wrapper signature and position identity')

def verify_diagnosis():
    for name in ['analysis-attempt-01','endpoint-attempt-01','endpoint-attempt-02']:
        directory=BASE/name;manifest=read(directory/'manifest.json')
        require(set(manifest)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'diagnostic artifact closure')
        for path,digest in manifest.items():require(sha(directory/path)==digest,'diagnostic artifact digest')
    first=BASE/'analysis-attempt-01/probe'
    require(read(first/'roles.json')['#select']['tuples']==read(first/'flow.json')['#select']['tuples']==[], 'original missing endpoint observation')
    for version in [1,2]:
        plan=read(BASE/('endpoint-plan-v%d.json'%version));attempt=BASE/('endpoint-attempt-%02d'%version)
        for field in ['queries','runner_files']:
            for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'diagnostic preregistration')
        record=read(attempt/'run.json');require(record['plan_sha256']==sha(BASE/('endpoint-plan-v%d.json'%version)) and record['scored_activation'] is False,'diagnostic provenance')
        require(set(record['phases'])=={'endpoints','endpoints-decode'},'diagnostic phase closure')
        for phase,result in record['phases'].items():
            require(result['exit_status']==0 and not result['timed_out'] and result['deadline_seconds']==60 and result['cleanup_status']=='tracked-processes-stopped','diagnostic phase failure')
    rows=read(BASE/'endpoint-attempt-02/endpoints.json')['#select']['tuples']
    endpoints=[r for r in rows if r[2] in ['dfb_source()','dfb_sink(_:)']]
    require(len(endpoints)==7 and {r[0] for r in endpoints}==set(range(25,32)) and all(r[1]=='DataFlowBenchTaintSwift' and r[-3:]==[True,False,False] for r in endpoints),'top-level resolved declaration without data-flow nodes')

def verify(attempt=None):
    verify_diagnosis()
    attempt=Path(attempt) if attempt else BASE/'analysis-attempt-02';probe=attempt/'probe';plan_path=BASE/'plan-v2.json';plan=read(plan_path)
    require(plan['scored_activation'] is False and plan['population_member'] is False and plan['aggregate_memory_compliance']==plan['semantic_completeness']=='unproven','preregistration scope')
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
    source=(BASE/'control-v2/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
    with zipfile.ZipFile(attempt/'source.zip') as z:
        members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
    for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
    require(source.decode().split('\n@inline')[0]==(BASE/'runtime/main.swift').read_text().split('\nfunc declaredMethods')[0], 'runtime dispatch source join')
    check_rows({n:read(probe/(n+'.json'))['#select']['tuples'] for n in plan['queries']})
    print('Objective-C model-off/on and positional control observations verified; non-scored, not a population result.')

if __name__=='__main__':verify()
