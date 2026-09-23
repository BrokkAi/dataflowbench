#!/usr/bin/env python3
"""Verify a fresh independent sanitizer control without scored activation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-keyed-persistence-v1'
PROFILE='adapter-patched-suite-state'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def check_rows(rows):
    require(rows['flow']==[[12,n,87,PROFILE] for n in [13,16,29,37,43,61]],'branch positive/safe flow separation')
    require(all(r[2]==PROFILE for r in rows['roles']),'profile attribution')
    require([r for r in rows['roles'] if r[3]!='sink']==[[12,21,PROFILE,'environment']],'source role')
    require({tuple(r[:2]) for r in rows['roles'] if r[3]=='sink'}=={(n,c) for n in [13,16,18,22,25,29,32,37,39,43,47,55,61] for c in [32,87]},'sink coverage')
    suite='DataFlowBench.Independent.Persistence';other='DataFlowBench.Other.Persistence'
    main=[10,11,14,15,17,23,24,27,28,30,31,33,36,41,42,44,45,46,48,50,52,54,56,58,60]
    points={(n,suite) for n in main}|{(35,other),(38,other)}
    require({(r[0],r[2],r[3]) for r in rows['states']}=={(n,d,p) for n,d in points for p in [False,True]},'state identity coverage')
    edges=list(zip(main[:19],main[1:19]))+[(48,50),(48,52),(50,54),(52,54),(54,56),(56,58),(56,60),(58,60)]
    expected={(a,True,b,False,suite) for a,b in edges}|{(35,True,38,False,other)}|{(n,False,n,True,d) for n,d in points}
    require({tuple(r) for r in rows['transitions']}==expected,'ordered branch transitions')
    stores={10:'payload',11:'other',14:'payload',23:'payload',27:'alias',30:'alias',33:'payload',35:'payload',41:'shared',44:'before',46:'before',48:'both',50:'both',52:'both',56:'one',58:'one'}
    reads={15:'payload',17:'other',24:'payload',28:'alias',31:'alias',36:'payload',38:'payload',42:'shared',45:'before',54:'both',60:'one'}
    require({(r[0],r[2]) for r in rows['clears']}==set(stores.items()),'key-specific clears')
    require({(r[0],r[1],r[3],r[5]) for r in rows['content']}=={(kind,n,n,k) for kind,m in [('store',stores),('read',reads)] for n,k in m.items()},'key-specific content')

def verify(attempt=None):
    attempt=Path(attempt) if attempt else BASE/'branch-attempt-01';probe=attempt/'probe';plan_path=BASE/'branch-plan-v1.json';plan=read(plan_path)
    require(plan['scored_activation'] is False and plan['aggregate_memory_compliance']==plan['semantic_completeness']=='unproven' and plan['expected_flow_lines']==[13,16,29,37,43,61],'preregistration scope')
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
    source=(BASE/'branch-control-v1/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
    with zipfile.ZipFile(attempt/'source.zip') as z:
        members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
    for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
    check_rows({n:read(probe/(n+'.json'))['#select']['tuples'] for n in plan['queries']})
    print('Fresh suite-state branches, alias/domain/ordering controls verified; non-scored.')

if __name__=='__main__':verify()
