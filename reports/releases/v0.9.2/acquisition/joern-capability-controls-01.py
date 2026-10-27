#!/usr/bin/env python3
"""Single fresh qualification capture; no release-group attempt or automatic retry."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path.cwd().resolve()
BASE = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/'
LEDGER_SHA = 'ca7152afb422160b30c2f38677aa539a1463b45e3b41131848b3d9e81d4a1084'
AUTH_SHA = '8268eb27d8f9f8ef3c00b90007b729973719aa1e83f30e95d6b157d95ed33d3b'
EXECUTOR_SHA = 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'
CUTOFF = '2026-10-23T21:33:00.680937+00:00'
PENDING = BASE + 'plan-v092-02/pending-execution-plan-01.json'
CONTROL = BASE + 'plan-v092-02/control-plan-01.json'
EVIDENCE = BASE + 'capability-evidence.json'
SHIM = 'scripts/joern_capability_repair_v092.py'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(relative, digest, name):
    path = ROOT / relative
    require(sha(path) == digest, name + ' digest changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-sha256', required=True)
    args = parser.parse_args()
    review_path = ROOT / BASE / 'control-bootstrap-independent-review-01.json'
    require(sha(review_path) == args.review_sha256, 'independent controls review changed')
    review = json.loads(review_path.read_bytes())
    require(review.get('status') == 'approved-for-fresh-controls-only', 'fresh controls not approved')
    for field, relative in [('implementation_sha256', SHIM), ('pending_plan_sha256', PENDING),
                            ('control_plan_sha256', CONTROL), ('evidence_sha256', EVIDENCE)]:
        require(review.get(field) == sha(ROOT / relative), field + ' differs from review')
    require(review.get('launcher_sha256') == sha(Path(__file__)), 'controls launcher lacks exact review')
    require(sha(ROOT / BASE / 'authorization.json') == AUTH_SHA, 'human authorization changed')
    ledger = ROOT / 'reports/releases/v0.9.2/ledger-v1.jsonl'
    require(sha(ledger) == LEDGER_SHA, 'sealed86 ledger changed')
    require(time.time() + 900 + 29400 <= dt.datetime.fromisoformat(CUTOFF).timestamp(), 'controls and remaining reviewed runs no longer fit original clock')
    directory = ROOT / BASE / 'control-launch-01'
    output = BASE + 'control-capture-01'
    require(not directory.exists() and not (ROOT / output).exists(), 'controls launch/capture already consumed')
    for relative in ['execution-state/v092/groups/series-01/joern-swift-common108/attempt-03',
                     'execution-state/v092/groups/series-01/codeql-swift-common108/attempt-01']:
        require(not (ROOT / relative).exists(), 'release-group attempt already exists')
    executor = load('scripts/execute-release-v092.py', EXECUTOR_SHA, 'controls_executor_pinned')
    shim = load(SHIM, review['implementation_sha256'], 'controls_repair_pinned')
    kwargs = dict(new_plan_path=PENDING, evidence_path=EVIDENCE,
                  expected_new_plan_sha256=review['pending_plan_sha256'],
                  expected_evidence_sha256=review['evidence_sha256'])
    shim.validate_bootstrap_inputs(ROOT, **kwargs)
    old_plan = json.loads((ROOT / shim.OLD_PLAN_PATH).read_bytes())
    old_receipt = json.loads((ROOT / old_plan['fresh_qualification']['path']).read_bytes())
    old_run = json.loads((ROOT / old_receipt['control_run']['path']).read_bytes())
    raw = json.loads((ROOT / old_run['records'][0]['raw']['path']).read_bytes())
    command = json.loads((ROOT / raw['commands'][0]['path']).read_bytes())
    # This is the actual inherited PATH for the new capture, not a rewritten witness.
    os.environ['PATH'] = command['environment']['PATH']
    os.environ['DATAFLOWBENCH_V092_QUALIFICATION'] = '1'
    os.environ['DATAFLOWBENCH_V092_GROUP_ID'] = 'joern-swift-common108'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    with executor._exclusive_lock():
        executor._check_resources(ROOT, 127 * 1024**3)
        require(sha(ledger) == LEDGER_SHA, 'ledger changed during controls preflight')
        directory.mkdir()
        started = dict(schema='v092-joern-capability-controls-launch/v1',
                       started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), pid=os.getpid(),
                       birth=subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', 'lstart='], text=True).strip(),
                       review_sha256=args.review_sha256, launcher_sha256=sha(Path(__file__)),
                       source_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                       pending_plan_sha256=review['pending_plan_sha256'], output=output,
                       original_origin_utc='2026-10-20T00:57:00.680937+00:00', cutoff_utc=CUTOFF,
                       automatic_retry=False, release_group_attempt=False, ledger_sha256=LEDGER_SHA)
        write(directory / 'started.json', started)
        try:
            run = shim.controls(ROOT, output, **kwargs)
            require(len(run.get('records', [])) == 12 and run.get('phase_invocation_count') == 36, 'fresh control capture incomplete')
            require(sha(ledger) == LEDGER_SHA, 'controls modified the release ledger')
            write(directory / 'exit.json', dict(status='capture-complete-review-pending',
                  ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(), run_sha256=sha(ROOT / output / 'run.json'),
                  ledger_sha256=sha(ledger), release_group_attempt=False))
        except BaseException as exc:
            write(directory / 'exit.json', dict(status='failed-no-automatic-retry',
                  ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(), error=type(exc).__name__ + ': ' + str(exc),
                  ledger_sha256=sha(ledger)))
            raise

if __name__ == '__main__':
    main()
