#!/usr/bin/python3
"""Task-owned durable single-dispatch supervisor. Never retries."""
import datetime, hashlib, json, os, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[2]
state = root / 'execution-state/v092/matrix-supervision-11'
contract = root / 'reports/releases/v0.9.2/execution-v3/contract.json'
public = root / 'reports/releases/v0.9.2/execution-v3/supervision-11'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value):
    with (public/name).open('x') as f:
        json.dump(value,f,indent=2); f.write('\n'); f.flush();os.fsync(f.fileno())
base = {'schema':'dataflowbench-v092-matrix-supervisor/v1','supervisor_pid':os.getpid(),'start_utc':now(),'contract_sha256':sha(contract),'source_commit':json.loads(contract.read_text())['source_commit'],'plan_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'supervisor_script_sha256':sha(pathlib.Path(__file__)),'automatic_retry':False}
write('started.json',base)
try:
    cmd=[sys.executable,'scripts/execute-release-v092.py','--contract',str(contract),'--execute']
    with (state/'executor-stdout.txt').open('xb') as out,(state/'executor-stderr.txt').open('xb') as err:
        proc=subprocess.Popen(cmd,cwd=root,stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1'})
        write('dispatch.json',{'argv':cmd,'pid':proc.pid,'utc':now()})
        result=proc.wait()
    write('exit.json',{**base,'end_utc':now(),'exit_code':result,'stdout_sha256':sha(state/'executor-stdout.txt'),'stderr_sha256':sha(state/'executor-stderr.txt')})
except BaseException as exc:
    write('supervisor-error.json',{**base,'end_utc':now(),'error':type(exc).__name__+': '+str(exc)})
    raise
