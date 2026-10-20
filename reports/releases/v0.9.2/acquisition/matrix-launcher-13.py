"""Task-owned, single-shot launcher; every gate runs before spawning anything."""
import datetime, hashlib, importlib.util, json, os, pathlib, subprocess
root=pathlib.Path.cwd()
state=root/'execution-state/v092/matrix-supervision-13'
public=root/'reports/releases/v0.9.2/execution-v3/supervision-13'
script=root/'execution-state/v092/supervise-matrix-13.py'
archived=root/'reports/releases/v0.9.2/acquisition/matrix-supervisor-13.py'
contract=root/'reports/releases/v0.9.2/execution-v3/contract.json'
raw=contract.read_bytes();plan=json.loads(raw)
assert hashlib.sha256(raw).hexdigest()=='9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063'
assert script.read_bytes()==archived.read_bytes()
assert plan['execution_authorized'] is True
spec=importlib.util.spec_from_file_location('matrix_launch_gate',root/'scripts/execute-release-v092.py')
executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
executor._assert_source_snapshot(root,plan['source_commit'],plan['runner_source_sha256'],executor._source_inputs(plan,root,{}))
plan_commit=executor._assert_contract_snapshot({'repo_root':root,'path':str(contract),'bytes_sha256':hashlib.sha256(raw).hexdigest()})
executor._check_resources(root,125*1024**3)
assert not state.exists() and not public.exists()
state.mkdir();public.mkdir()
with (state/'supervisor-stdout.txt').open('xb') as out,(state/'supervisor-stderr.txt').open('xb') as err:
 proc=subprocess.Popen(['/usr/bin/python3',str(script)],cwd=root,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1'},start_new_session=True,close_fds=True)
 awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(proc.pid)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
 identity=subprocess.check_output(['ps','-p',str(proc.pid),'-o','lstart='],text=True).strip()
 receipt={'schema':'v092-durable-launch/v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_pid':proc.pid,'supervisor_start_identity':identity,'caffeinate_pid':awake.pid,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'launcher_script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256(raw).hexdigest(),'source_commit':plan['source_commit'],'plan_commit':plan_commit,'source_and_contract_gate_passed':True,'launch_resource_gate_passed':True,'automatic_retry':False,'retained_original_wall_origin_utc':'2026-10-20T00:57:00.680937+00:00','execution_series':1}
 with (public/'launcher.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(receipt))
