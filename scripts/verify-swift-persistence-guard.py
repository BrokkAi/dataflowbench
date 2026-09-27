#!/usr/bin/env python3
"""Verify retained applicability evidence; no scored activation."""
import hashlib
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs
from swift_persistence_coverage import assess_coverage, CoverageStatus
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-persistence-guard-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def manifest(directory):
    values=read(directory/'manifest.json')
    require(set(values)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in values.items():require(sha(directory/name)==digest,'artifact digest: '+name)
def check_coverage(rows,global_control=False):
    expected={(6,'Incomplete','UnmodeledCallEffect',9),(12,'Incomplete','DynamicKey',14),(17,'Incomplete','UnqualifiedPayloadType',19),(22,'Incomplete','IncompleteReceiverOrigin',23),(22,'Incomplete','IncompleteReceiverOrigin',24),(26,'Incomplete','UnsupportedPreferenceOperation',29),(32,'Complete','AdmittedClosedScope',32),(38,'Incomplete','IncompleteReceiverOrigin',40),(38,'Incomplete','IncompleteReceiverOrigin',41),(50,'Incomplete','UnmodeledGetterEffect',53)}
    if global_control:expected.add((0,'Incomplete','MissingCfgCoverage',58))
    require({tuple(r) for r in rows}==expected,'applicability control coverage')
    require(assess_coverage(rows).status is CoverageStatus.INCOMPLETE,'aggregate incomplete')
    require(assess_coverage([r for r in rows if r[0]==32]).status is CoverageStatus.COMPLETE,'admitted scope')
def verify_retained():
    stages=[('diagnostic',1,['calls'],'calls'),('diagnostic',2,['calls','payloads','getters'],None),('diagnostic',3,['calls','cfg-calls'],None),('coverage',1,['coverage'],'coverage'),('coverage',2,['coverage'],None),('coverage',3,['coverage'],None)]
    for family,version,queries,failed in stages:
        plan_path=BASE/(family+'-plan-v'+str(version)+'.json');plan=read(plan_path);directory=BASE/(family+'-attempt-0'+str(version))
        require(plan['scored_activation'] is False,'diagnostic promotion')
        for field in ['queries','runner_files','inputs']:
            for path,digest in plan[field].items():require(sha(ROOT/path)==digest,'diagnostic preregistration')
        manifest(directory);run=read(directory/'run.json')
        require(run['scored_activation'] is False and run['plan_sha256']==sha(plan_path),'diagnostic run provenance')
        phases=[q+s for q in queries for s in ([''] if q==failed else ['','-decode'])]
        require(set(run['phases'])==set(phases),'diagnostic phases')
        for phase in phases:
            command=read(directory/(phase+'.command.json'))
            require(command==run['phases'][phase] and command['exit_status']==(2 if phase==failed else 0) and not command['timed_out'] and not command.get('cleanup_error') and command['cleanup_status']=='tracked-processes-stopped','diagnostic phase outcome')
            require(command['deadline_seconds']==60 and command['memory_compliance']=='unproven','diagnostic phase limits')
        if failed:require('ERROR:' in (directory/(failed+'.stderr')).read_text(),'retained diagnostic error')
    require(read(BASE/'diagnostic-attempt-02/calls.json')['#select']['tuples']==[],'retained empty call enumeration')
    require(len(read(BASE/'diagnostic-attempt-03/calls.json')['#select']['tuples'])==8,'resolved call coverage')
    require(read(BASE/'coverage-attempt-03/coverage.json')['#select']['tuples']==[[3,'Complete','AdmittedClosedScope',3]],'final canonical admission')
    require(read(BASE/'coverage-attempt-02/coverage.json')['#select']['tuples']==[[3,'Complete','AdmittedClosedScope',3]],'canonical admission')

def verify():
    verify_retained()
    for version in [1,2]:
        attempt=BASE/('guard-attempt-0'+str(version));probe=attempt/'probe';plan_path=BASE/('guard-plan-v'+str(version)+'.json');plan=read(plan_path)
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
        source=(BASE/('coverage-control-v'+str(version))/'main.swift').read_bytes();require((probe/'main.swift').read_bytes()==source,'staged source')
        with zipfile.ZipFile(attempt/'source.zip') as z:
            members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived source')
        for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query')
        check_coverage(read(probe/'coverage.json')['#select']['tuples'],version==2)
    print('Structural applicability controls verified; incomplete coverage never becomes clean.')
if __name__=='__main__':verify()
