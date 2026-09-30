import datetime,hashlib,json,sys,subprocess,shutil
from pathlib import Path
sys.path.insert(0,str(Path('scripts').resolve()))
from release_runtime_inventory_v090 import verify
root=Path.cwd();p=root/'reports/releases/v0.9.0/execution-v1/final-recovery-20260930-01';c=json.loads((p/'contract.json').read_text());i=json.loads((p/'control-inventory.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schema':'release-preparation-readback/v1','benchmark_execution':False,'execution_authorized':False,'checks':[]}
def check(name,fn):
 try: result=fn();r['checks'].append({'check':name,'status':'pass','result':result})
 except Exception as e:r['checks'].append({'check':name,'status':'blocked','error':str(e)})
def inputs():
 bad=[v for v,h in c['input_identities'].items() if sha(root/v)!=h]
 if bad:raise ValueError('digest drift '+repr(bad))
 return len(c['input_identities'])
check('all-bound-input-digests',inputs)
for name,t in c['tools'].items():
 if 'sha256' not in t:continue
 def tool(t=t):
  if not t['sha256']:raise ValueError('not-built; no prospective binary digest')
  if sha(t['path'])!=t['sha256']:raise ValueError('tool digest mismatch')
  return t['path']
 check('tool:'+name,tool)
for ref in c['runtime_trees']:
 check('runtime-tree:'+ref['path'],lambda ref=ref:verify(json.loads((root/ref['path']).read_text())))
from swift_common_population_v2 import verify_plan
from swift_normal_runner_v1 import verify_runtime
for engine,ref in c['swift_plans'].items():
 check('swift-plan:'+engine,lambda engine=engine,ref=ref:bool(verify_plan(root,ref['path'],engine)))
 if engine=='codeql':check('swift-runtime:codeql',lambda ref=ref: verify_runtime(root,json.loads((root/ref['path']).read_text())) or True)
rows=[]
for kind,ops in [('control',i['controls']),('matrix',c['groups'])]:
 for op in ops:
  mapped=c['control_execution_roots' if kind=='control' else 'execution_roots'][op['id']]
  rows.append({'id':op['id'],'kind':kind,'argv_sha256':hashlib.sha256(json.dumps(op['argv'],separators=(',',':')).encode()).hexdigest(),'execution_root':mapped,'root_exists':Path(mapped).exists(),'deadline_seconds':op['deadline_seconds'],'status':'pending-exact-root-runtime-and-cross-field-preflight'})
r['operations']=rows;r['operation_count']=len(rows);r['qualified_operations']=0
r['capacity']={'free_bytes':shutil.disk_usage(root).free,'launch_floor_bytes':136*1024**3,'prebuild_floor_bytes':144*1024**3,'exclusive_slot':False}
r['remaining_gates']=c['unresolved'];(p/'preparation-readback.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['operations']},indent=2))
