#!/opt/homebrew/bin/python3.13
"""PREPARED ONLY. One separately approved diagnostic agent05 premain -version.

Decision JSON exact fields:
 schema="v092-agent05-standalone-probe-decision/v1", approved_probe=true,
 automatic_retry=false, publication_hold=true, script={path,sha256},
 jar_review={path,sha256}, agent_jar=JAR, build_result=BUILD,
 observer=OBSERVER, process_helper=PROCESS, java=JAVA,
 namespace=NAMESPACE, timeout_seconds=15, maximum_java_invocations=1.

All refs are exact absolute path/SHA objects. Root supplies a separate actual
JAR-review ref and this script's real SHA AFTER review. No default decision or
future review identity. Invocation (root only after review):
 /opt/homebrew/bin/python3.13 -B -E THIS --decision ACTUAL --decision-sha256 SHA
No analyzer, controls, qualification, native self-birth or containment inference.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
from typing import Any

NAMESPACE = Path('/private/tmp/joern05-agent05-standalone-probe-01')
ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
JAVA_HOME = Path('/Users/dave/.sdkman/candidates/java/21.0.8-tem')
JAVA = {'path': str(JAVA_HOME/'bin/java'), 'sha256': '0045ae168ee132bbf469a26fb17dac6d1dee431c9b7826474f3b6ee574a997c9'}
JAR = {'path': '/private/tmp/joern05-agent05-build-01/joern-startup-witness-agent-05.jar', 'sha256': '1e30a6a5c88abb0216c5f205bd337f18fc30dd91345a8aeae244398cc0803261'}
BUILD = {'path': '/private/tmp/joern05-agent05-build-01/build-result-01.json', 'sha256': '56f5f820331252d1f28275ead5e7d6ba80f2a3363ef63cd027be69a8cbc7d652'}
OBSERVER = {'path': '/private/tmp/joern05-native-control-08/joern_native_control_observer_v07.py', 'sha256': '64d93cf635cd00b7853f5f2d1bb7ee5bd5763f4b187eb0d6f59ae8fdc8e7dbfc'}
PROCESS = {'path': str(ROOT/'scripts/swift_v2_process.py'), 'sha256': '40aec2ef3e23def3d961caab709de9e636e9669d305b47bdc7b7c98ccf8a97dd'}
TIMEOUT = 15
FIELDS = {'schema','approved_probe','automatic_retry','publication_hold','script','jar_review',
          'agent_jar','build_result','observer','process_helper','java','namespace',
          'timeout_seconds','maximum_java_invocations'}


def require(value: bool, message: str) -> None:
    if not value: raise ValueError(message)


def stable(reference: dict[str, str]) -> bytes:
    require(type(reference) is dict and set(reference)=={'path','sha256'}, 'exact path/SHA ref required')
    p = Path(reference['path'])
    require(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)), 'noncanonical/symlink input')
    require(re.fullmatch('[0-9a-f]{64}',reference['sha256']) is not None,'unsealed digest')
    with p.open('rb') as stream:
        before=os.fstat(stream.fileno()); require(stat.S_ISREG(before.st_mode),'not regular input')
        data=stream.read(); after=os.fstat(stream.fileno())
    named=p.stat()
    keys=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    require(keys(before)==keys(after)==keys(named),'input changed during read')
    require(hashlib.sha256(data).hexdigest()==reference['sha256'],'input SHA changed: '+str(p))
    return data


def ref(p: Path) -> dict[str, Any]:
    require(p.is_file() and not p.is_symlink(),'output not regular: '+str(p))
    data=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def write(p: Path, data: bytes) -> None:
    with p.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def document(p: Path, value: Any) -> None:
    write(p,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())


def load(reference: dict[str,str], name: str) -> Any:
    data=stable(reference)
    spec=importlib.util.spec_from_file_location(name,reference['path'])
    require(spec is not None and spec.loader is not None,'cannot load pinned helper')
    module=importlib.util.module_from_spec(spec)
    exec(compile(data,reference['path'],'exec'),module.__dict__)
    return module


def gate(path: Path, digest: str) -> tuple[dict[str,Any],dict[str,str]]:
    request={'path':str(path),'sha256':digest}
    decision=json.loads(stable(request))
    require(type(decision) is dict and set(decision)==FIELDS,'decision schema fields changed')
    require(decision['schema']=='v092-agent05-standalone-probe-decision/v1' and
            decision['approved_probe'] is True and decision['automatic_retry'] is False and
            decision['publication_hold'] is True,'separate explicit diagnostic-only approval required')
    expected={'agent_jar':JAR,'build_result':BUILD,'observer':OBSERVER,'process_helper':PROCESS,'java':JAVA}
    for key,value in expected.items():
        require(decision[key]==value,'sealed dependency differs: '+key); stable(value)
    require(decision['script']['path']==str(Path(__file__).resolve()),'different probe script')
    stable(decision['script']); stable(decision['jar_review'])
    require(decision['namespace']==str(NAMESPACE) and type(decision['timeout_seconds']) is int and
            decision['timeout_seconds']==TIMEOUT and type(decision['maximum_java_invocations']) is int and
            decision['maximum_java_invocations']==1,'one-shot namespace/time/count changed')
    built=json.loads(stable(BUILD))
    require({k:built['agent_jar'][k] for k in ('path','sha256')}==JAR and
            built['standalone_premain_version_jvm_invocations']==0,'build provenance mismatch')
    require(not NAMESPACE.exists() and not NAMESPACE.is_symlink(),'namespace already consumed')
    return decision,request


def cleanup_owned(process: subprocess.Popen, shell_birth: str | None, proc: Any) -> dict[str,Any]:
    """Signal only our retained Popen or an exact witnessed new-session group."""
    result={'direct_child_reaped':False,'signals':[],'group_ownership_verified':False,
            'descendant_containment':'unproven'}
    if process.poll() is None:
        try:
            identity=proc.start_identity(process.pid,None)
            group=os.getpgid(process.pid)
            group_owned=(shell_birth is not None and identity==shell_birth and group==process.pid)
        except Exception: group_owned=False
        result['group_ownership_verified']=group_owned
        for sig,grace in ((signal.SIGTERM,1.0),(signal.SIGKILL,1.0)):
            if process.poll() is not None: break
            # Recheck group root identity before every group signal. If it
            # disappeared/recycled, use only the actual owned Popen object.
            safe_group=False
            if group_owned:
                try:safe_group=(proc.start_identity(process.pid,None)==shell_birth and os.getpgid(process.pid)==process.pid)
                except Exception:pass
            try:
                if safe_group: os.killpg(process.pid,sig)
                elif sig==signal.SIGTERM: process.terminate()
                else: process.kill()
                result['signals'].append({'signal':int(sig),'target':'exact-owned-session-group' if safe_group else 'owned-Popen-direct-child'})
            except ProcessLookupError: pass
            try:process.wait(timeout=grace)
            except subprocess.TimeoutExpired:pass
    try: process.wait(timeout=1.0);result['direct_child_reaped']=True
    except subprocess.TimeoutExpired:result['cleanup_error']='direct child did not reap within bound'
    return result


def run(decision: dict[str,Any], request_ref: dict[str,str]) -> dict[str,Any]:
    require(sys.platform=='darwin','this exact high-resolution probe is Darwin-bound')
    proc=load(PROCESS,'agent05_standalone_frozen_process')
    observer=load(OBSERVER,'agent05_standalone_observer08')
    host_pid=os.getpid();host_before=proc.start_identity(host_pid,None)
    require(type(host_before) is str and bool(host_before),'exact host birth unavailable')
    # mkdir is the irreversible one-shot consumption boundary, before Popen.
    NAMESPACE.mkdir(mode=0o700)
    for child in ('home','tmp','witnesses'):(NAMESPACE/child).mkdir(mode=0o700)
    home=NAMESPACE/'home';predef=home/'.scala-repl-pp.sc'
    shell=NAMESPACE/'invoke-once.sh'
    write(shell,b'#!/bin/sh\n"$@"\ncode=$?\nexit "$code"\n')
    environment={'JAVA_HOME':str(JAVA_HOME),'PATH':str(JAVA_HOME/'bin')+':/usr/bin:/bin',
                 'HOME':str(home),'TMPDIR':str(NAMESPACE/'tmp'),'LANG':'C','LC_ALL':'C',
                 'DFB_JOERN_STARTUP_WITNESS_DIR':str(NAMESPACE/'witnesses')}
    command=['/bin/sh',str(shell),JAVA['path'],'-Xmx64m','-XX:ActiveProcessorCount=2',
             '-Duser.home='+str(home),'-javaagent:'+JAR['path'],'-version']
    document(NAMESPACE/'inputs.json',{'decision':request_ref,'bindings':decision,'argv':command,
            'environment':environment,'host':{'pid':host_pid,'native_birth_before':host_before},
            'shell_source':ref(shell),'diagnostic_only':True,'maximum_java_invocations':1})
    process=None;shell_birth=None;cleanup=None;error=None;proof=None;timed_out=False
    start=time.monotonic();returncode=None;host_after=None
    try:
        for binding in (JAVA,JAR,BUILD,OBSERVER,PROCESS,decision['script'],decision['jar_review']):stable(binding)
        with (NAMESPACE/'stdout.txt').open('xb') as stdout,(NAMESPACE/'stderr.txt').open('xb') as stderr:
            process=subprocess.Popen(command,cwd=NAMESPACE,env=environment,stdout=stdout,stderr=stderr,start_new_session=True)
            shell_birth=proc.start_identity(process.pid,None)
            document(NAMESPACE/'child-started.json',{'pid':process.pid,'native_birth':shell_birth,
                     'argv':command,'popen_monotonic':start,'host_pid':host_pid})
            try:returncode=process.wait(timeout=max(0.001,TIMEOUT-(time.monotonic()-start)))
            except subprocess.TimeoutExpired:
                timed_out=True;raise ValueError('single diagnostic process exceeded15seconds')
            finally:
                stdout.flush();os.fsync(stdout.fileno());stderr.flush();os.fsync(stderr.fileno())
        require(returncode==0,'diagnostic Java/shell exited nonzero')
        host_after=proc.start_identity(host_pid,None)
        require(host_before==host_after,'host PID/native birth changed')
        files=list((NAMESPACE/'witnesses').iterdir())
        require(len(files)==1,'exactly one actual premain witness required')
        witness=files[0];require(re.fullmatch(r'jvm-[1-9][0-9]*[.]json',witness.name) is not None,'witness filename malformed')
        require(witness.is_file() and not witness.is_symlink() and witness.stat().st_size<=1024*1024,
                'witness must be regular and <=1MiB')
        payload=json.loads(witness.read_text())
        require(payload['schema']==observer.WITNESS_SCHEMA and payload['agent_version']==observer.AGENT_VERSION,'witness schema/version differs')
        require(type(payload['pid']) is int and payload['pid']>0 and witness.name=='jvm-'+str(payload['pid'])+'.json','PID/filename binding differs')
        require(payload['java_command_present'] is False and payload['java_command_b64']=='','-version command must remain absent/diagnostic')
        require(base64.b64decode(payload['user_home_b64'],validate=True).decode()==str(home),'actual user.home differs')
        require(base64.b64decode(payload['predef_path_b64'],validate=True).decode()==str(predef) and
                payload['predef_present'] is False and payload['predef_symlink'] is False and
                not predef.exists() and not predef.is_symlink(),'predef not absent')
        require(base64.b64decode(payload['witness_directory_b64'],validate=True).decode()==str(NAMESPACE/'witnesses'),'witness event directory differs')
        chain=observer._validate_ancestry(payload,witness.name)
        correlation=observer._ancestry_anchor(chain,{},host_pid,host_before,witness.name)
        require(correlation['anchor_source']=='invocation-host' and len(correlation['validated_prefix'])>=2,'probe did not exercise shell-parent ancestry gap')
        proof={'witness':ref(witness),'ancestry_correlation':correlation,'host_native_birth_after':host_after,
               'native_self_birth_verified':False,'semantic_qualification':False,'diagnostic_only':True}
    except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)}
    finally:
        if process is not None:
            try:cleanup=cleanup_owned(process,shell_birth,proc)
            except BaseException as cleanup_error:
                cleanup={'direct_child_reaped':process.poll() is not None,
                         'error':{'type':type(cleanup_error).__name__,'message':str(cleanup_error)},
                         'descendant_containment':'unproven'}
                if error is None:error={'type':'CleanupError','message':str(cleanup_error)}
            if not cleanup.get('direct_child_reaped') and error is None:
                error={'type':'CleanupError','message':'owned direct child not reaped'}
        try:
            host_after=proc.start_identity(host_pid,None)
            if host_after!=host_before and error is None:
                error={'type':'HostIdentityError','message':'host PID/native birth changed'}
        except BaseException as identity_error:
            if error is None:error={'type':type(identity_error).__name__,'message':str(identity_error)}
        outputs=[ref(p) for p in sorted(NAMESPACE.rglob('*')) if p.is_file() and not p.is_symlink()]
        receipt={'schema':'v092-agent05-standalone-premain-diagnostic/v1','status':'passed-diagnostic-only' if error is None else 'failed',
                 'decision':request_ref,'argv':command,'environment':environment,'timeout_seconds':TIMEOUT,
                 'elapsed_seconds':time.monotonic()-start,'timed_out':timed_out,'returncode':returncode,
                 'host_pid':host_pid,'host_native_birth_before':host_before,'host_native_birth_after':host_after,'proof':proof,'error':error,'cleanup':cleanup,
                 'outputs':outputs,'maximum_java_invocations':1,'actual_java_invocations':int(process is not None),
                 'automatic_retry':False,'scored_attempt_consumed':False,'semantic_qualification':False,
                 'native_control_matrix_executed':False,'publication_hold':True}
        document(NAMESPACE/'receipt.json',receipt)
    require(error is None,'diagnostic probe failed; namespace consumed; inspect immutable receipt')
    return receipt


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decision',type=Path,required=True)
    parser.add_argument('--decision-sha256',required=True)
    args=parser.parse_args()
    decision,reference=gate(args.decision,args.decision_sha256)
    result=run(decision,reference)
    print(json.dumps({'status':result['status'],'receipt':ref(NAMESPACE/'receipt.json')}))
    return 0


if __name__=='__main__':raise SystemExit(main())
