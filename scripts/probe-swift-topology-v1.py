#!/usr/bin/env python3
"""Preregistered no-extraction topology query on immutable database clones."""
import argparse, hashlib, importlib.util, json, shutil, subprocess, time
from pathlib import Path
from swift_artifact_closure import snapshot, compare

ROOT=Path(__file__).resolve().parents[1]
ADAPTER=ROOT/'adapters/codeql/swift-top-level-topology-v1'
spec=importlib.util.spec_from_file_location('endpoint_probe',ROOT/'scripts/probe-swift-endpoints-v1.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
read,write,sha,require=probe.read,probe.write,probe.sha,probe.require


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['codeql','packs','retained','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();registration=read(ADAPTER/'registration.json')
    for name,digest in registration['files'].items():require(sha(ROOT/name)==digest,'PreregistrationMismatch:'+name)
    tracked=[*registration['files'],str((ADAPTER/'registration.json').relative_to(ROOT))]
    subprocess.run(['git','diff','--quiet','HEAD','--',*tracked],cwd=ROOT,check=True)
    subprocess.run(['git','ls-files','--error-unmatch','--',*tracked],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    pins=read(ROOT/'adapters/codeql/swift-opaque-v3/plan.json')
    require(sha(args.codeql)==pins['cli_sha256'],'CLIPinMismatch')
    for row in read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json'):
        require(sha(args.packs/row['path'])==row['sha256'],'PackPinMismatch')
    query=ADAPTER/'topology.ql';output=args.output.resolve();output.relative_to(ROOT/'reports/raw/swift-topology-v1')
    require(shutil.disk_usage(ROOT).free>=40*1024**3,'DiskReserveReached')
    output.mkdir(parents=True,exist_ok=False)
    write(output/'launch.json',{'scope':'topology-diagnostic-only','scored_activation':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),'registration_sha256':sha(ADAPTER/'registration.json'),'paths':{k:str(v) for k,v in vars(args).items()}})
    resolved=subprocess.run([str(args.codeql),'resolve','library-path','--query='+str(query),'--additional-packs='+str(args.packs),'--format=json'],capture_output=True,text=True,check=True,timeout=30)
    write(output/'library-path.json',json.loads(resolved.stdout))
    require(str(args.packs/'codeql/swift-all/6.8.4') in json.loads(resolved.stdout)['libraryPath'],'ResolvedPackMismatch')
    stop=None;results=[];sealed=[];originals=[]
    for cid in registration['case_ids']:
        base=output/cid;base.mkdir();artifacts=base/'artifacts';artifacts.mkdir();result={'id':cid,'status':'not-attempted','scored_activation':False}
        try:
            require(stop is None,stop or '')
            require(shutil.disk_usage(ROOT).free>=40*1024**3,'DiskReserveReached')
            for old,baseline in sealed:require(compare(baseline,snapshot(old))['status']=='CompleteArtifactClosure','LateArtifactDrift')
            original=args.retained/cid
            require(sha(original/'observation.json')==registration['observations'][cid],'OriginalObservationMismatch')
            before=snapshot(original/'database');write(base/'original-before.json',before);originals.append((original/'database',before))
            database=artifacts/'database'
            subprocess.run(['/bin/cp','-cR',str(original/'database'),str(database)],check=True,timeout=120)
            require(before['entries']==snapshot(database)['entries'],'CloneMismatch')
            result['status']='attempted';start=time.monotonic()
            probe.invoke([str(args.codeql),'query','run',str(query),'--database='+str(database),'--output='+str(artifacts/'topology.bqrs'),'--additional-packs='+str(args.packs),'--threads=2','--ram=2048','--timeout=75'],artifacts,'query',75)
            remaining=75-(time.monotonic()-start)
            if remaining<=0:raise TimeoutError('BudgetExhausted:analysis')
            probe.invoke([str(args.codeql),'bqrs','decode',str(artifacts/'topology.bqrs'),'--format=json','--output='+str(artifacts/'topology.json')],artifacts,'decode',remaining)
            result['analysis_elapsed_seconds']=time.monotonic()-start
            require(result['analysis_elapsed_seconds']<=75,'BudgetExhausted:analysis')
            result['rows']=read(artifacts/'topology.json')['#select']['tuples'];result['status']='completed'
        except Exception as error:
            result['failure']={'kind':type(error).__name__,'message':str(error)};stop=probe.failure_stop(error)
        finally:
            try:
                before=snapshot(artifacts);write(base/'closure-before.json',before);time.sleep(1)
                after=snapshot(artifacts);write(base/'closure-after.json',after)
                result['closure']=compare(before,after)
                if result['closure']['status']!='CompleteArtifactClosure':stop='IncompleteArtifactClosure'
                sealed.append((artifacts,before))
            except Exception as error:stop='IncompleteArtifactClosure';result['closure']={'status':stop,'reason':str(error)}
            write(base/'result.json',result);results.append(result);write(output/'results.json',results)
        print(cid+': '+result['status'],flush=True)
    audits=[]
    for path,before in sealed+originals:
        try:delta=compare(before,snapshot(path))
        except Exception as error:delta={'status':'IncompleteArtifactClosure','reason':str(error)}
        audits.append({'path':str(path),'delta':delta})
    write(output/'closure-audit.json',{'observations':audits,'containment':'unproven'})
    require(stop is None and all(r['delta']['status']=='CompleteArtifactClosure' for r in audits),'IncompleteTopologyAttempt')


if __name__=='__main__':main()
