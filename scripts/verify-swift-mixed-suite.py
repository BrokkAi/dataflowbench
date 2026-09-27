#!/usr/bin/env python3
"""Verify immutable mixed receiver evidence without scored promotion."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-persistence-completeness-v1'
PROFILE='adapter-patched-suite-state'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def manifest(directory):
    values=read(directory/'manifest.json')
    require(set(values)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in values.items():require(sha(directory/name)==digest,'artifact digest: '+name)
def check_rows(rows,repaired):
    expected=[13,16,29,37,43,61]+([70] if repaired else [])
    require(rows['flow']==[[12,n,87,PROFILE] for n in expected],'mixed receiver flow separation')
    require(all(r[2]==PROFILE for r in rows['roles']),'profile attribution')
    require([r for r in rows['roles'] if r[3]!='sink']==[[12,21,PROFILE,'environment']],'source coverage')
    require({tuple(r[:2]) for r in rows['roles'] if r[3]=='sink'}=={(n,c) for n in [13,16,18,22,25,29,32,37,39,43,47,55,61,70,78] for c in [32,87]},'sink coverage')
    clear_lines={r[0] for r in rows['clears']}
    require((68 not in clear_lines if repaired else 68 in clear_lines) and 76 in clear_lines,'may versus must clears')
    if repaired:
        mixed=[r for r in rows['receiver-proof'] if r[0]==68]
        require({(r[2],r[3],r[4]) for r in mixed}=={(s,False,True) for s in ['DataFlowBench.Independent.Persistence','DataFlowBench.Other.Persistence']},'mixed receiver proof')
        same=[r for r in rows['receiver-proof'] if r[0]==76]
        require(len(same)==1 and same[0][2:]==['DataFlowBench.Independent.Persistence',True,True],'same suite receiver proof')
def verify():
    for version in [1,2]:
        attempt=BASE/('mixed-attempt-0'+str(version));probe=attempt/'probe';plan_path=BASE/('mixed-plan-v'+str(version)+'.json');plan=read(plan_path)
        require(plan['scored_activation'] is False and plan['semantic_completeness']==plan['aggregate_memory_compliance']=='unproven','scope promotion')
        for field in ['control_files','query_files','vendor_files','runner_files']:
            for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'preregistered digest: '+name)
        manifest(attempt);manifest(probe)
        run=read(attempt/'run.json');witness=read(probe/'witness.json')
        require(run['plan_sha256']==sha(plan_path) and run['source_commit']==witness['source_commit'] and run['exit_status']==0 and run['scored_activation'] is False,'run provenance')
        assets=read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json')
        prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
        require(run['assets']==assets and run['compiler_sha256']==witness['compiler_sha256']==prior['compiler_sha256'] and witness['extractor_sha256']==assets['codeql/swift/tools/osx64/extractor.real'] and run['pack_files_verified']==3398,'runtime provenance')
        require(witness['analysis_budget']=={'wall_clock_seconds':60,'peak_memory_mb':2048} and witness['extraction_phase_deadline_seconds']==150,'witness limits')
        require(set(witness['phases'])=={'database-create','database-resolve',*plan['queries']},'phase closure')
        require(witness['status']=='unqualified' and witness['population_member'] is False and not witness.get('probe_error') and not witness.get('cleanup_error') and witness['memory_compliance']=='unproven','probe scope')
        require(inspect_logs(probe/'log/swift/extractor')['ready_for_observation'],'extractor errors')
        for name in ['database-create','database-resolve']+[n+s for n in plan['queries'] for s in ['','-decode']]:
            c=read(probe/(name+'.command.json'));require(c['exit_status']==0 and not c['timed_out'] and not c.get('cleanup_error') and c['cleanup_status']=='tracked-processes-stopped','phase failure')
            require(c['deadline_seconds']==(150 if name=='database-create' else 60),'phase deadline')
            if name in plan['queries']:require('--ram=2048' in c['argv'] and '--timeout=60' in c['argv'],'analysis bounds')
        source=(BASE/'mixed-control-v1/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
        with zipfile.ZipFile(attempt/'source.zip') as z:
            members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
        for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
        check_rows({n:read(probe/(n+'.json'))['#select']['tuples'] for n in plan['queries']},version==2)
    print('Mixed receiver regression and same-suite clear verified; non-scored.')
if __name__=='__main__':verify()
