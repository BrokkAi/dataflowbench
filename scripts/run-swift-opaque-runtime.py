#!/usr/bin/env python3
"""Execute only the preregistered pure-string Objective-C runtime harness."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from swift_v2_process import run
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-opaque-objc-v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['output','compiler','sdk']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();plan=read(BASE/'runtime-plan.json')
    require(plan['scored_activation'] is False and plan['population_member'] is False,'scope')
    paths=['evidence/swift-opaque-objc-v1/runtime-plan.json']
    for field in ['control_files','runner_files','vendor_files']:
        for name,digest in plan[field].items():require(sha(ROOT/name)==digest,'input digest: '+name);paths.append(name)
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
    subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=ROOT,check=True)
    prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    require(sha(args.compiler)==prior['compiler_sha256'],'compiler identity')
    require(sha(args.sdk/'SDKSettings.json')==plan['sdk_settings_sha256'],'SDK identity')
    runtime=BASE/'runtime/main.swift';control=BASE/'control/main.swift'
    runtime_class=runtime.read_text().split('\nfunc declaredMethods')[0]
    control_class=control.read_text().split('\n@inline')[0]
    require(runtime_class==control_class,'runtime/control class bytes')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    record={'scope':plan['scope'],'plan_sha256':sha(BASE/'runtime-plan.json'),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scored_activation':False,'status':'incomplete','compiler_sha256':sha(args.compiler),'sdk_settings_sha256':sha(args.sdk/'SDKSettings.json'),'runtime_sha256':sha(runtime),'control_sha256':sha(control),'shared_class_sha256':hashlib.sha256(runtime_class.encode()).hexdigest()}
    scratch=Path(tempfile.mkdtemp(prefix='dfb-opaque-runtime-'));binary=scratch/'runtime-check'
    record['retained_scratch']=str(scratch)
    try:
        command=[str(args.compiler),'-swift-version','6','-Onone','-sdk',str(args.sdk),'-target','arm64-apple-macosx26.5','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(scratch/'module-cache'),str(runtime),'-o',str(binary)]
        result=run(command,out,'compile',60,measure=True,cwd=ROOT)
        require(result['exit_status']==0 and not result['timed_out'],'runtime compile failure')
        record['binary_sha256']=sha(binary)
        result=run([str(binary)],out,'runtime',10,measure=True,cwd=ROOT)
        require(result['exit_status']==0 and not result['timed_out'],'runtime execution failure')
        observed=read(out/'runtime.stdout')
        require(observed['observed']==plan['runtime_expectations'],'runtime values')
        require({r['selector']:r['signature'] for r in observed['identities']}==plan['required_runtime_declarations'],'runtime signatures')
        require(all(r['owner']=='DataFlowBenchTaintSwift.Opaque' for r in observed['identities']),'runtime declaration owner')
        record['status']='runtime-observed-not-analyzer-qualified'
    except Exception as error:record['error']=str(error);raise
    finally:
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        (out/'manifest.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},indent=2)+'\n')
if __name__=='__main__':main()
