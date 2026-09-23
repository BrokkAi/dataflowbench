#!/usr/bin/env python3
"""Portable checks for the preregistered Darwin Objective-C runtime observation."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-opaque-objc-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def check_observation(observed):
    require(observed['observed']=={'carry':'tainted','block':'tainted','position1':'tainted','position0':'clean'},'runtime values/position')
    require(observed['identities']==[
        {'owner':'DataFlowBenchTaintSwift.Opaque','selector':'dfbRelay:','signature':['@','@',':','@']},
        {'owner':'DataFlowBenchTaintSwift.Opaque','selector':'dfbChoose:second:','signature':['@','@',':','@','@']}], 'declared selector owner/signature')
def verify():
    plan=read(BASE/'runtime-plan.json');attempt=BASE/'runtime-attempt-01';manifest=read(attempt/'manifest.json')
    require(set(manifest)=={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in manifest.items():require(sha(attempt/name)==digest,'artifact digest: '+name)
    for field in ['control_files','runner_files','vendor_files']:
        for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'preregistered input: '+name)
    record=read(attempt/'run.json');prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    require(record['plan_sha256']==sha(BASE/'runtime-plan.json') and record['status']=='runtime-observed-not-analyzer-qualified' and record['scored_activation'] is False and not record.get('error'),'run provenance/scope')
    require(record['compiler_sha256']==prior['compiler_sha256'] and record['sdk_settings_sha256']==plan['sdk_settings_sha256'],'compiler/SDK identity')
    runtime=BASE/'runtime/main.swift';control=BASE/'control/main.swift'
    shared=runtime.read_text().split('\nfunc declaredMethods')[0]
    require(shared==control.read_text().split('\n@inline')[0] and hashlib.sha256(shared.encode()).hexdigest()==record['shared_class_sha256'],'shared class source')
    require(record['runtime_sha256']==sha(runtime) and record['control_sha256']==sha(control),'source digests')
    for phase,deadline in [('compile',60),('runtime',10)]:
        result=read(attempt/(phase+'.command.json'))
        require(result['exit_status']==0 and not result['timed_out'] and result['deadline_seconds']==deadline and result['cleanup_status']=='tracked-processes-stopped' and not result.get('cleanup_error'),'phase failure/cleanup')
    compile=read(attempt/'compile.command.json')['argv'];execution=read(attempt/'runtime.command.json')['argv']
    require(compile[-3].endswith('/evidence/swift-opaque-objc-v1/runtime/main.swift') and compile[-2]=='-o' and execution==[compile[-1]],'runtime executable provenance')
    check_observation(read(attempt/'runtime.stdout'))
    print('Objective-C runtime fidelity verified; analyzer opacity and activation require separate evidence.')
if __name__=='__main__':verify()
