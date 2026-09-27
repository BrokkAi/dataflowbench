#!/usr/bin/env python3
"""Verify retained applicability evidence; no scored activation."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs
from swift_persistence_coverage import assess_coverage, CoverageStatus
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-persistence-initial-state-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def manifest(directory):
    values=read(directory/'manifest.json')
    require(set(values)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in values.items():require(sha(directory/name)==digest,'artifact digest: '+name)
def check_coverage(rows):
    expected={(2,'Complete','AdmittedClosedScope',2),(7,'Incomplete','IncompleteInitialState',9),(11,'Incomplete','IncompleteInitialState',14),(16,'Incomplete','IncompleteInitialState',19),(21,'Incomplete','IncompleteInitialState',23)}
    require({tuple(r) for r in rows}==expected,'initial-state control coverage')

def verify_canonical():
    for polarity in ['positive','negative']:
        plan_path=BASE/('canonical-'+polarity+'-plan-v1.json');plan=read(plan_path);directory=BASE/('canonical-'+polarity+'-attempt-01')
        for field in ['queries','runner_files','inputs']:
            for path,digest in plan[field].items():require(sha(ROOT/path)==digest,'canonical preregistration')
        manifest(directory);run=read(directory/'run.json')
        require(run['scored_activation'] is False and run['plan_sha256']==sha(plan_path),'canonical provenance')
        require(set(run['phases'])=={'coverage','coverage-decode'},'canonical phase closure')
        for phase,command in run['phases'].items():
            require(command==read(directory/(phase+'.command.json')) and command['exit_status']==0 and not command['timed_out'] and command['deadline_seconds']==60 and command['cleanup_status']=='tracked-processes-stopped' and not command.get('cleanup_error'),'canonical phase failure')
        require(read(directory/'coverage.json')['#select']['tuples']==[[3,'Complete','AdmittedClosedScope',3]],'canonical initialized admission')

def verify():
    verify_canonical()
    for version in [1]:
        attempt=BASE/'attempt-01';probe=attempt/'probe';plan_path=BASE/'plan-v1.json';plan=read(plan_path)
        require(plan['scored_activation'] is False and plan['semantic_completeness']==plan['aggregate_memory_compliance']=='unproven','scope promotion')
        for field in ['control_files','query_files','vendor_files','runner_files']:
            for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'preregistered digest: '+name)
        manifest(attempt);manifest(probe)
        run=read(attempt/'run.json');witness=read(probe/'witness.json')
        require(run['plan_sha256']==sha(plan_path) and run['source_commit']==witness['source_commit'] and run['exit_status']==0 and run['scored_activation'] is False,'run provenance')
        assets=read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json');prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
        require(run['assets']==assets and run['compiler_sha256']==witness['compiler_sha256']==prior['compiler_sha256'] and witness['extractor_sha256']==assets['codeql/swift/tools/osx64/extractor.real'] and run['pack_files_verified']==3398,'runtime provenance')
        require(witness['analysis_budget']=={'wall_clock_seconds':60,'peak_memory_mb':2048} and witness['extraction_phase_deadline_seconds']==150,'witness limits')
        require(set(witness['phases'])=={'database-create','database-resolve',*plan['queries']},'phase closure')
        require(witness['status']=='unqualified' and witness['population_member'] is False and not witness.get('probe_error') and not witness.get('cleanup_error') and witness['memory_compliance']=='unproven','probe scope')
        require(inspect_logs(probe/'log/swift/extractor')['ready_for_observation'],'extractor errors')
        for name in ['database-create','database-resolve']+[n+s for n in plan['queries'] for s in ['','-decode']]:
            c=read(probe/(name+'.command.json'));require(c['exit_status']==0 and not c['timed_out'] and not c.get('cleanup_error') and c['cleanup_status']=='tracked-processes-stopped','phase failure')
            require(c['deadline_seconds']==(150 if name=='database-create' else 60),'phase deadline')
            if name in plan['queries']:require('--ram=2048' in c['argv'] and '--timeout=60' in c['argv'],'analysis bounds')
        source=(BASE/'control-v1/main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
        with zipfile.ZipFile(attempt/'source.zip') as z:
            members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
        for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
        check_coverage(read(probe/'coverage.json')['#select']['tuples'])
    print('Initialized-key gate verified in controls and both canonical fixtures; non-scored.')
if __name__=='__main__':verify()
