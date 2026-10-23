#!/usr/bin/env python3
"""Single-launch reviewed Joern04/CodeQL01 supervision; no automatic retries."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import secrets

ROOT = Path(__file__).resolve().parents[4]
STATE = ROOT / 'execution-state/v092/matrix-supervision-25'
PUBLIC = ROOT / 'reports/releases/v0.9.2/execution-v4/supervision-25'
MODULE = ROOT / 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-02.py'
MANIFEST = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/continuation-manifest-03.json'
REVIEW = ROOT / 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/supervision25-independent-review-01.json'
GATE = ('import hashlib,json,os,pathlib,subprocess,sys,time\np=pathlib.Path(sys.argv[1]);end=time.monotonic()+30\n'
        'while not p.is_file():\n if time.monotonic()>=end:sys.exit(125)\n time.sleep(.05)\n'
        'v=json.loads(p.read_bytes())\n'
        'expected={"pid":os.getpid(),"birth":subprocess.check_output(["ps","-p",str(os.getpid()),"-o","lstart="],text=True).strip(),'
        '"token":sys.argv[2],"argv_sha256":hashlib.sha256(json.dumps(sys.argv[3:]).encode()).hexdigest()}\n'
        'if v!=expected:sys.exit(126)\n'
        'os.execv(sys.executable,[sys.executable,"-E",*sys.argv[3:]])')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def permit(path, proc, token, argv):
    write(path, {'pid': proc.pid, 'birth': birth(proc.pid), 'token': token,
                'argv_sha256': hashlib.sha256(json.dumps(argv).encode()).hexdigest()})

def birth(pid):
    return subprocess.check_output(['ps', '-p', str(pid), '-o', 'lstart='], text=True).strip()

def command(args, mode, group=None):
    result = [sys.executable, '-E', str(MODULE), mode,
              '--manifest', args.manifest, '--manifest-sha256', args.manifest_sha256]
    if group:
        result += ['--group', group]
    return result

def validate(args):
    require(ROOT == Path.cwd().resolve(), 'wrong working directory')
    require(args.manifest == MANIFEST, 'manifest path is not the reviewed final path')
    require(sha(Path(__file__)) == args.supervisor_sha256, 'supervision source changed')
    require(sha(MODULE) == args.module_sha256, 'continuation source changed')
    require(sha(REVIEW) == args.review_sha256, 'control review changed')
    review = json.loads(REVIEW.read_bytes())
    require(review.get('status') == 'approved' and review.get('automatic_retry') is False,
            'control review is not approved')
    require(review.get('bindings') == {
        'supervisor_sha256': args.supervisor_sha256,
        'continuation_sha256': args.module_sha256,
        'manifest_sha256': args.manifest_sha256,
        'manifest_path': args.manifest,
    }, 'control review bindings differ')

def supervise(args):
    validate(args)
    launcher = json.loads((PUBLIC / 'launcher.json').read_bytes())
    supervisor_permit = json.loads((STATE / 'allow-supervisor-start').read_bytes())
    require(supervisor_permit == {
        'pid': os.getpid(), 'birth': birth(os.getpid()),
        'token': launcher['supervisor_token'],
        'argv_sha256': hashlib.sha256(json.dumps(
            [str(Path(__file__).resolve()), *sys.argv[1:]]).encode()).hexdigest(),
    }, 'supervisor permit identity differs')
    require(launcher['supervisor_pid'] == os.getpid() and
            launcher['automatic_retry'] is False and
            launcher['supervisor_birth'] == birth(os.getpid()) and
            launcher['manifest_sha256'] == args.manifest_sha256 and
            launcher['manifest_path'] == args.manifest and
            launcher['module_sha256'] == args.module_sha256 and
            launcher['supervisor_sha256'] == args.supervisor_sha256 and
            launcher['review_sha256'] == args.review_sha256 and
            launcher['preflight_sha256'] == sha(PUBLIC / 'parent-preflight.json'),
            'durable launcher identity/bindings differ')
    preflight = json.loads((PUBLIC / 'parent-preflight.json').read_bytes())
    require(preflight['exit_code'] == 0 and preflight['automatic_retry'] is False and
            preflight['manifest_sha256'] == args.manifest_sha256 and
            preflight['manifest_path'] == args.manifest and
            preflight['argv'] == command(args, 'preflight'), 'preflight binding differs')
    write(PUBLIC / 'started.json', {'utc': now(), 'pid': os.getpid(),
          'birth': birth(os.getpid()), 'automatic_retry': False,
          'manifest_sha256': args.manifest_sha256})
    try:
        for group in ['joern-swift-common108', 'codeql-swift-common108']:
            validate(args)
            cmd = command(args, 'execute', group)
            ready = STATE / (group + '-allow-start')
            token = secrets.token_hex(32)
            with (STATE / (group + '-stdout.txt')).open('xb') as out, \
                    (STATE / (group + '-stderr.txt')).open('xb') as err:
                proc = subprocess.Popen([sys.executable, '-E', '-c', GATE, str(ready), token, *cmd[2:]],
                    cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err, close_fds=True)
                try:
                    write(PUBLIC / (group + '-dispatch.json'), {'utc': now(), 'pid': proc.pid,
                          'birth': birth(proc.pid), 'argv': cmd, 'automatic_retry': False})
                    permit(ready, proc, token, cmd[2:])
                finally:
                    # Before a permit the child exits itself within30seconds.
                    # After admission always reap the owned child, even if a
                    # receipt write raises; never kill or retry an analyzer.
                    code = proc.wait()
            write(PUBLIC / (group + '-exit.json'), {'utc': now(), 'exit_code': code,
                  'stdout_sha256': sha(STATE / (group + '-stdout.txt')),
                  'stderr_sha256': sha(STATE / (group + '-stderr.txt'))})
            require(code == 0, 'continuation stopped after ' + group)
        write(PUBLIC / 'exit.json', {'utc': now(), 'status': 'two-commands-finished',
              'exit_code': 0, 'automatic_retry': False})
    except BaseException as exc:
        write(PUBLIC / 'supervisor-error.json', {'utc': now(), 'error': str(exc),
              'automatic_retry': False})
        raise

def launch(args):
    validate(args)
    require(not STATE.exists() and not PUBLIC.exists(), 'control25 namespace already consumed')
    checked = subprocess.run(command(args, 'preflight'), cwd=ROOT,
                             capture_output=True, text=True, check=True)
    # The reviewed continuation itself owns live clock, source, prefix, lock,
    # disk/process/sidecar admission and the exact Joern04/CodeQL01 attempt gates.
    validate(args)
    STATE.mkdir()
    PUBLIC.mkdir()
    write(PUBLIC / 'parent-preflight.json', {'utc': now(), 'argv': command(args, 'preflight'),
          'stdout': checked.stdout, 'stderr': checked.stderr, 'exit_code': checked.returncode,
          'manifest_sha256': args.manifest_sha256, 'manifest_path': args.manifest, 'automatic_retry': False})
    ready = STATE / 'allow-supervisor-start'
    child_args = [str(Path(__file__).resolve()), *sys.argv[1:], '--supervise']
    token = secrets.token_hex(32)
    with (STATE / 'supervisor-stdout.txt').open('xb') as out, \
            (STATE / 'supervisor-stderr.txt').open('xb') as err:
        proc = subprocess.Popen([sys.executable, '-E', '-c', GATE, str(ready), token, *child_args],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            close_fds=True, start_new_session=True)
    try:
        awake = subprocess.Popen(['/usr/bin/caffeinate', '-i', '-w', str(proc.pid)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
        record = {'utc': now(), 'supervisor_pid': proc.pid, 'supervisor_birth': birth(proc.pid),
                  'supervisor_token': token,
                  'caffeinate_pid': awake.pid, 'caffeinate_birth': birth(awake.pid),
                  'manifest_path': args.manifest,
                  'manifest_sha256': args.manifest_sha256, 'module_sha256': args.module_sha256,
                  'supervisor_sha256': args.supervisor_sha256, 'review_sha256': args.review_sha256,
                  'preflight_sha256': sha(PUBLIC / 'parent-preflight.json'),
                  'automatic_retry': False}
        write(PUBLIC / 'launcher.json', record)
        permit(ready, proc, token, child_args)
    except BaseException:
        proc.wait()
        raise
    print(json.dumps(record))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['manifest', 'module', 'supervisor', 'review']:
        parser.add_argument('--' + key + '-sha256', required=True)
    parser.add_argument('--manifest', default=MANIFEST)
    parser.add_argument('--supervise', action='store_true')
    args = parser.parse_args()
    (supervise if args.supervise else launch)(args)

if __name__ == '__main__':
    main()
