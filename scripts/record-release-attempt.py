#!/usr/bin/env python3
"""Record one serial release attempt, retaining changed outputs before any retry."""
import argparse,datetime,hashlib,json,os,pathlib,platform,shutil,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/releases/v0.7.1'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def state():
 return {str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'reports').rglob('*') if p.is_file() and BASE not in p.parents}
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def run(identifier,argv,settle=False):
 BASE.mkdir(parents=True,exist_ok=True);ledger=BASE/'ledger.jsonl'
 rows=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
 n=sum(r['planned_id']==identifier for r in rows)+1;aid=f'{identifier}-attempt-{n:02d}';dest=BASE/'attempts'/aid
 dest.mkdir(parents=True,exist_ok=False)
 plan=json.loads((BASE/'plan.json').read_text());before=state();samples=[]
 if settle:
  for _ in range(6):samples.append({'utc':now(),'load':os.getloadavg()});time.sleep(10)
 row={'id':aid,'planned_id':identifier,'argv':argv,'cwd':str(ROOT),'input_commits':plan['input_commits'],'execution_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'population':plan['population'],'fixture_revision':plan['fixture_revision'],'plan':ref(BASE/'plan.json'),'identities':ref(BASE/'identities.json'),'start_utc':now(),'host':{'platform':platform.platform(),'cpu_count':os.cpu_count(),'load_before':os.getloadavg()},'settle_observations':samples,'cache_posture':'isolated case workspaces; local distributions and prefetched CodeQL packs; OS page cache uncontrolled; warm only for explicit warm series','supersedes':rows[-1]['id'] if rows and rows[-1]['planned_id']==identifier else None}
 (dest/'started.json').write_text(json.dumps(row,indent=2)+'\n')
 print('START',aid,flush=True)
 with open(dest/'stdout.txt','wb') as out,open(dest/'stderr.txt','wb') as err:
  try:row['exit_code']=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err).returncode
  except OSError as e:err.write(str(e).encode());row['exit_code']=127
 row['end_utc']=now();row['host']['load_after']=os.getloadavg();row['stdout']=ref(dest/'stdout.txt');row['stderr']=ref(dest/'stderr.txt')
 after=state();row['outputs']=[]
 for p,h in after.items():
  if before.get(p)!=h:
   copy=dest/'outputs'/p;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,copy);row['outputs'].append({'original_path':p,**ref(copy)})
 row['removed_paths']=sorted(set(before)-set(after));(dest/'completed.json').write_text(json.dumps(row,indent=2)+'\n')
 with open(ledger,'a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
 print('END',aid,'exit',row['exit_code'],'outputs',len(row['outputs']),flush=True)
 return row['exit_code']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('id');p.add_argument('--settle',action='store_true');p.add_argument('argv',nargs=argparse.REMAINDER);a=p.parse_args();args=a.argv[1:] if a.argv[:1]==['--'] else a.argv
 raise SystemExit(run(a.id,args,a.settle))
