import datetime, hashlib, json, os, pathlib, subprocess, sys
root=pathlib.Path.cwd()
state=root/'execution-state/v092/matrix-supervision-03'
public=root/'reports/releases/v0.9.2/execution-v3/supervision-03'
script=root/'execution-state/v092/supervise-matrix-03.py'
archived=root/'reports/releases/v0.9.2/acquisition/matrix-supervisor-03.py'
contract=root/'reports/releases/v0.9.2/execution-v3/contract.json'
assert script.read_bytes()==archived.read_bytes()
assert json.loads(contract.read_text())['execution_authorized'] is True
state.mkdir(exist_ok=False);public.mkdir(exist_ok=False)
with (state/'supervisor-stdout.txt').open('xb') as out,(state/'supervisor-stderr.txt').open('xb') as err:
 proc=subprocess.Popen(['/usr/bin/python3',str(script)],cwd=root,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1'},start_new_session=True,close_fds=True)
 awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(proc.pid)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
 identity=subprocess.check_output(['ps','-p',str(proc.pid),'-o','lstart='],text=True).strip()
 receipt={'schema':'v092-durable-launch/v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_pid':proc.pid,'supervisor_start_identity':identity,'caffeinate_pid':awake.pid,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'automatic_retry':False,'retained_original_wall_origin_utc':'2026-10-20T00:57:00.680937+00:00','execution_series':1}
 with (public/'launcher.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(receipt))
