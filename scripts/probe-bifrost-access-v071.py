#!/usr/bin/env python3
"""One explicitly sandboxed or elevated same-fixture Bifrost access control."""
import argparse,datetime,hashlib,json,os,pathlib,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('access',choices=['sandboxed','elevated']);p.add_argument('polarity',choices=['positive','negative']);args=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];base=root/'reports/probes/bifrost-access-v071';base.mkdir(parents=True,exist_ok=True)
ident='java-alias-'+args.polarity+'-'+args.access;dest=base/ident;dest.mkdir(exist_ok=False)
casepath=root/'cases/taint/java'/('alias-propagation-'+args.polarity)/'case.json';case=json.loads(casepath.read_text());policy=root/case['tool_model_references']['bifrost']['policy'];binary=pathlib.Path('/Users/dave/.cache/dataflowbench-tools/bifrost-v0.11.0/bifrost-v0.11.0-universal-apple-darwin/bifrost')
work=pathlib.Path('/private/tmp/dfb-v071-bifrost-access-control-653a')/case['id']
if work.exists():shutil.move(str(work),str(dest/'preexisting-workspace'))
work.mkdir(parents=True)
for name in case['fixture_files']:shutil.copy2(casepath.parent/name,work/name)
shutil.copy2(policy,work/'policy.rqlp')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
argv=[str(binary),'--root',str(work),'--policy-file','policy.rqlp','--evaluation-date','2026-08-11','--format','json','--fail-on','never','--output',str(dest/'raw.json')]
row={'id':ident,'execution_access':args.access,'population':'v0.7.0','case_id':case['id'],'argv':argv,'cwd':str(root),'binary_sha256':sha(binary),'policy_sha256':sha(policy),'fixtures':{name:sha(work/name) for name in case['fixture_files']},'environment':{k:os.environ.get(k) for k in ['PATH','JAVA_HOME','TMPDIR']},'cache_observation':'Fresh workspace before each invocation; prior workspace retained if present. Global semantic-pack and OS caches uncontrolled and may carry earlier runs. Fixed order sandbox positive,elevated positive,sandbox negative,elevated negative. Diagnostic only, no population timing parity claim.','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'load_before':os.getloadavg()}
(dest/'started.json').write_text(json.dumps(row,indent=2)+'\n');start=time.monotonic()
with (dest/'stdout.txt').open('wb') as out,(dest/'stderr.txt').open('wb') as err:row['exit_code']=subprocess.run(argv,cwd=root,stdout=out,stderr=err).returncode
row['wall_ms']=round((time.monotonic()-start)*1000);row['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();row['load_after']=os.getloadavg();row['files']={p.name:sha(p) for p in dest.iterdir() if p.is_file()}
(dest/'completed.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({'id':ident,'exit_code':row['exit_code'],'wall_ms':row['wall_ms']}))
