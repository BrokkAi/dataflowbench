import sys,json,hashlib,shutil,time,subprocess
from pathlib import Path
r=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/dfb-220-full108-20260928/scripts');import swift_v2_process as process
from swift_artifact_closure import snapshot,compare
out=r/'retained-diagnosis-01';out.mkdir(exist_ok=False)
q=r/'diagnostic-queries/steps.ql';names=['array-element-positive','array-element-negative','callback-registration-positive'];cli='/private/tmp/dfb-full108-assets-20260928/codeql-runtime/codeql/codeql'
(out/'preregistration.json').write_text(json.dumps({'query_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'cases':names,'shared_query_decode_seconds':75,'ram_requested_mb':2048,'minimum_free_gib':40,'extraction':False,'attempts':1,'claim':'content steps and resolved dispatch counts only; no full path witness'},indent=2)+'\n')
originals=[]
for name in names:
 assert shutil.disk_usage(r).free>40*1024**3
 original=r/f'controls-attempt-01/{name}/database';before=snapshot(original);originals.append((original,before));d=out/name;d.mkdir();subprocess.run(['/bin/cp','-cR',str(original),str(d/'database')],check=True);assert snapshot(d/'database')['entries']==before['entries']
start=time.monotonic();records=[]
for name in names:
 d=out/name
 try:
  for label,args in [('query',[cli,'query','run',str(q),'--database='+str(d/'database'),'--output='+str(d/'steps.bqrs'),'--additional-packs='+str(r/'candidate-packs'),'--threads=2','--ram=2048']),('decode',[cli,'bqrs','decode',str(d/'steps.bqrs'),'--format=json','--output='+str(d/'steps.json')])]:
   remain=75-(time.monotonic()-start);assert remain>0,'BudgetExhausted'
   x=process.run(args,d,label,remain,cwd=r);assert x['exit_status']==0 and not x['timed_out'],'DiagnosticFailed:'+label
  records.append({'case':name,'status':'completed','rows':json.loads((d/'steps.json').read_text())['#select']['tuples']})
 except Exception as e:records.append({'case':name,'status':'incomplete','reason':str(e)});break
(out/'results.json').write_text(json.dumps(records,indent=2)+'\n')
(out/'original-closure.json').write_text(json.dumps([{'path':str(p),'delta':compare(b,snapshot(p))} for p,b in originals],indent=2)+'\n')
print(json.dumps(records),flush=True)
