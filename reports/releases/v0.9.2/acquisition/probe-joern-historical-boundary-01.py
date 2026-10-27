import importlib.util,json,hashlib,datetime,traceback
from pathlib import Path
root=Path.cwd(); module_path=root/'reports/releases/v0.9.2/acquisition/joern-capability-continuation-03.py'
spec=importlib.util.spec_from_file_location('boundary_production_probe',module_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
raw,rows=m._ledger(root);m._check_prefix(root,rows,raw);m._tail(rows,final=False)
e=m._load_frozen(root,'execute');before=e._validate_scoped_tail
value={'schema':'v092-historical-boundary-production-probe/v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'module_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'ledger_sha256':hashlib.sha256(raw).hexdigest(),'ledger_rows':len(rows),'analyzer_invoked':False,'admission':False,'materialization':False,'benchmark_attempt_consumed':False}
try:
 base=m._validate_base_with_historical_boundary(e,root/m.BASE_CONTRACT,root,rows,raw)
 assert e._validate_scoped_tail is before
 base['total_wall_budget_seconds']=m.TOTAL_WALL_SECONDS
 contexts=m._historical_contexts(base,rows,raw,{'validated':base,'plan_commit':m.BASE_PLAN_COMMIT},root=root,executor=e)
 assert len(base['resource_recovery']['retained_completed'])==82
 assert len(base['resource_recovery']['retained_failures'])==5
 value.update(status='passed',retained_completed=82,retained_failures=5,registered_contexts=sorted(contexts),original_frozen_validator_restored=True)
except Exception as exc:
 value.update(status='failed',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),original_frozen_validator_restored=e._validate_scoped_tail is before)
p=root/'reports/releases/v0.9.2/qualification/joern-capability-repair-01/base-boundary-production-probe-01.json'
with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(value));raise SystemExit(0 if value['status']=='passed' else 1)
