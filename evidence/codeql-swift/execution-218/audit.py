import collections,hashlib,json
from pathlib import Path
root=Path('.')
report_hashes={};cases={};rows={};tiers={};resource=[];native_failures=[];config=set()
for p in root.glob('cases/taint/swift/*/case.json'):
 c=json.loads(p.read_text());cases[c['id']]=(p,c)
for tier,count in [('kernel',66),('modeling',20),('calibration',4)]:
 p=Path('reports/codeql-swift-'+tier+'.json');report=json.loads(p.read_text());report_hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();config.add(report['configuration_hash'])
 assert len(report['results'])==count
 tiers[tier]=dict(collections.Counter(row['outcome'] for row in report['results']))
 for row in report['results']:
  id=row['case_id'];assert id not in rows;rows[id]=row
  case_path,case=cases[id];d=Path('reports/raw/codeql-swift-'+tier)/id
  provenance=json.loads((d/'provenance.json').read_text());execution=json.loads((d/'execution.json').read_text())
  for file,digest in provenance['fixture_sha256'].items():assert hashlib.sha256((case_path.parent/file).read_bytes()).hexdigest()==digest
  cert=json.loads(Path('adapters/codeql/swift/activation.json').read_text())
  for key in ['compiler_sha256','extractor_sha256']:assert provenance[key]==cert[key]
  assert json.loads((d/'pack-identities.json').read_text())==json.loads(Path('evidence/codeql-swift/activation-218/pack-tree-identities.json').read_text())
  native=[]
  for phase in ['database-create','database-analyze']:
   command=json.loads((d/(phase+'.command.json')).read_text());native.append({'phase':phase,'exit_status':command['exit_status'],'timed_out':command['timed_out'],'elapsed_seconds':command['elapsed_seconds']})
   if phase=='database-analyze':
    assert '--ram='+str(case['execution_budget']['peak_memory_mb']) in command['argv']
    assert '--timeout='+str(case['execution_budget']['wall_clock_seconds']) in command['argv']
  resource.append({'case_id':id,'outcome':row['outcome'],'diagnostics':row['diagnostics'],'time_maxrss_mb':execution.get('time_maxrss_mb'),'normalized_peak_memory_mb':row['peak_memory_mb'],'native_commands':native,'contemporaneous_git_head':provenance['execution_git_commit']})
  assert row['outcome'] in ['inconclusive','runner-error'] and row['peak_memory_mb'] is None
assert len(rows)==90 and set(rows)==set(cases)
assert len(config)==1
summary={'source':'retained native evidence; no qualified score or performance claim','launched_runner_source_commit':'f51cb4c9d8d716710812af26725eed83fbf1bb61','configuration_hash':config.pop(),'tiers':tiers,'total_assertions':len(rows),'report_sha256':report_hashes,'case_evidence':resource,'contention':'Core/modeling overlapped with at most two sequential CodeQL runners, each threads=2. Local tests/site checks also overlapped. All timings are descriptive.'}
summary['raw_evidence_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for tier in ['kernel','modeling','calibration'] for p in sorted(Path('reports/raw/codeql-swift-'+tier).rglob('*')) if p.is_file()}
diagnosis=Path('evidence/codeql-swift/endpoint-diagnosis-218')
for relative,digest in json.loads((diagnosis/'evidence-sha256.json').read_text()).items():
 assert hashlib.sha256((diagnosis/relative).read_bytes()).hexdigest()==digest
for path,digest in json.loads((diagnosis/'query-sha256.json').read_text()).items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
expected={
 'array-element-positive':[['dfb_source()',5,1,0,0,0],['dfb_sink(_:)',7,1,0,0,0]],
 'callback-registration-positive':[['dfb_source()',15,1,0,0,0],['dfb_sink(_:)',13,1,1,1,1]],
 'function-body-positive-control':[['dfb_source()',4,1,1,1,0],['dfb_sink(_:)',5,1,1,1,1]],
}
for name,tuples in expected.items():
 assert json.loads((diagnosis/(name+'-decode.stdout')).read_text())['#select']['tuples']==tuples
 assert json.loads((diagnosis/(name+'-query.command.json')).read_text())['exit_status']==0
print(json.dumps(summary,indent=2))
