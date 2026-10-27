#!/usr/bin/env python3
"""Read-only retained replay/materialized-source checks and one-shot no-expiry admission."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import shutil

ROOT = Path(__file__).resolve().parents[4]
BASE = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/'
MODULE = 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-04.py'
SUPERVISOR = 'reports/releases/v0.9.2/acquisition/matrix-supervision-27.py'
PROVISIONAL_MANIFEST = BASE + 'continuation-manifest-admission-09.json'
AUTHORIZATION_PATH = BASE + 'no-expiry-authorization-01.json'
AUTHORIZATION_SHA = 'acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc'
EXECUTION_WINDOW_SCHEMA = 'v092-no-user-execution-window-policy/v1'
PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS = 30
PER_ATTEMPT_STARTUP_ALLOWANCE_SOURCE = 'matrix-supervision-27.GATE.stop-wait-seconds'
RETAINED_PREFLIGHT = BASE + 'retained-preflight-06.json'
MATERIALIZED_PREFLIGHT = BASE + 'materialized-preflight-06.json'
MATERIALIZED_SOURCE = 'execution-state/v092/joern-capability-materialized-preflight-06'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')

def ref(path):
    return {'path': path, 'sha256': sha(ROOT / path)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--module-sha256', required=True)
    args = parser.parse_args()
    if args.manifest != PROVISIONAL_MANIFEST:
        raise ValueError('admission requires the exact reviewed provisional manifest path')
    if sha(ROOT / MODULE) != args.module_sha256:
        raise ValueError('module changed')
    spec = importlib.util.spec_from_file_location('admission_continuation', ROOT / MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    context = mod.validate(ROOT, args.manifest, args.manifest_sha256)
    executor = context['executor']
    validated = context['repaired']['validated']
    manifest = context['manifest']
    review = json.loads((ROOT / manifest['final_review']['path']).read_bytes())
    mod.require(review.get('admission_source') == ref(Path(__file__).resolve().relative_to(ROOT).as_posix()),
                'final review does not bind this admission helper')
    mod.require(review.get('supervisor_source') == ref(SUPERVISOR),
                'final review does not bind the reviewed supervisor')
    source = manifest['source_commit']
    report_path = RETAINED_PREFLIGHT
    replay = subprocess.run([sys.executable, '-E', str(ROOT / MODULE), 'preflight',
        '--manifest', args.manifest, '--manifest-sha256', args.manifest_sha256],
        cwd=ROOT, capture_output=True, check=True)
    with (ROOT / report_path).open('xb') as f:
        f.write(replay.stdout)
    with (ROOT / BASE / 'retained-preflight-06-stderr.txt').open('xb') as f:
        f.write(replay.stderr)
    destination = ROOT / MATERIALIZED_SOURCE
    with executor._exclusive_lock():
        executor._check_resources(ROOT, 127 * 1024**3)
        executor._assert_source_snapshot(ROOT, source, validated['plan']['runner_source_sha256'],
                                         validated['source_inputs'])
        mod.require(executor._assert_contract_snapshot(validated) == manifest['plan_commit'],
                    'contract commit differs')
        for group_id in [mod.JOERN_GROUP, mod.CODEQL_GROUP]:
            group = next(g for g in validated['plan']['groups'] if g['id'] == group_id)
            normalized = next(g for g in validated['groups'] if g['id'] == group_id)
            executor._assert_fresh(ROOT, group, normalized['reports'], validated['plan']['execution_series'])
        class Projection:
            chunk_bytes = 1024**2
            def error(self, reason, message, **kw):
                return ValueError(reason + ': ' + message)
            def check_capacity(self, *, projected_bytes=0, **kw):
                mod.require(shutil.disk_usage(ROOT).free - projected_bytes >= 127 * 1024**3,
                            'materialization would cross protected scheduling capacity')
            def check(self, **kw):
                projected = kw['projected_bytes']
                mod.require(projected <= 12 * 1024**3 and
                            shutil.disk_usage(ROOT).free - projected >= 127 * 1024**3,
                            'source projection exceeds bounded admission capacity')
        projected = executor._materialize_source(ROOT, source, destination,
            [x['path'] for x in validated['source_inputs']],
            disk_guard=Projection(), preflight_only=True)
        executor._materialize_source(ROOT, source, destination,
            [x['path'] for x in validated['source_inputs']],
            disk_guard=Projection(), expected_projected_bytes=projected)
        # A fresh interpreter is required: the validated parent process has
        # already imported frozen modules whose ROOT constants name the checkout.
        # Match the real runner's isolated materialized-script invocation.
        probe = """import json,sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root/'scripts'))
import joern_capability_repair_v092 as shim
v=shim.preflight(root,new_plan_path=sys.argv[1],expected_new_plan_sha256=sys.argv[2],expected_evidence_sha256=sys.argv[3])
import joern_normal_runner_v092 as launch_guard
launch_guard._require_launch_guard('joern-swift-common108')
v['launch_guard_checked']=True
v['launch_environment_markers']={k:__import__('os').environ.get(k) for k in ['DATAFLOWBENCH_V092_RELEASE_EXECUTION','DATAFLOWBENCH_V092_GROUP_ID']}
print(json.dumps(v,default=str))
"""
        joern_group = next(g for g in validated['plan']['groups'] if g['id'] == mod.JOERN_GROUP)
        launch_environment = executor._child_environment(joern_group, destination,
            ROOT / 'reports/releases/v0.9.2/attempts' / mod.JOERN_ATTEMPT,
            ROOT / 'execution-state/v092/cache/series-01/joern-swift-common108/attempt-04')
        isolated = subprocess.run([sys.executable, '-E', '-c', probe,
            manifest['artifacts']['repaired_plan']['path'],
            manifest['artifacts']['repaired_plan']['sha256'],
            manifest['artifacts']['capability_evidence']['sha256']],
            cwd=destination, env=launch_environment, capture_output=True, check=True)
        with (ROOT / MATERIALIZED_PREFLIGHT).open('xb') as f:
            f.write(isolated.stdout)
        with (ROOT / BASE / 'materialized-preflight-06-stderr.txt').open('xb') as f:
            f.write(isolated.stderr)
        checked = json.loads(isolated.stdout)
        mod.require(checked.get('launch_guard_checked') is True and
            checked.get('launch_environment_markers') == {
                'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1',
                'DATAFLOWBENCH_V092_GROUP_ID': mod.JOERN_GROUP},
            'actual materialized child environment failed immutable launch guard')
        executor._check_resources(ROOT, 127 * 1024**3)
        # No user-window arithmetic is performed here.  Static phase reserves
        # remain in the receipt and the successor continuation creates a finite
        # per-attempt lease under its exclusive lock.
    artifacts = dict(manifest['artifacts'])
    artifacts['continuation_test'] = ref(mod.CONTINUATION_TEST)
    value = dict(schema='v092-joern-capability-continuation-admission/v1',
        status='ready-to-execute', automatic_retry=False, release_group_attempt=False,
        original_origin_utc=mod.ORIGIN, cutoff_utc=None,
        total_wall_budget_seconds=None,
        execution_window={
            'schema': EXECUTION_WINDOW_SCHEMA,
            'mode': 'no-user-imposed-expiry',
            'original_origin_utc': mod.ORIGIN,
            'historical_cutoff_utc': mod.CUTOFF,
            'historical_total_wall_budget_seconds': mod.TOTAL_WALL_SECONDS,
            'cutoff_utc': None,
            'total_wall_budget_seconds': None,
            'per_attempt_timeout_source': 'registered-plan-group-deadline-seconds',
            'resource_reservation_source': 'per-attempt-lease-under-exclusive-lock',
            'startup_allowance_seconds': PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS,
            'startup_allowance_source': PER_ATTEMPT_STARTUP_ALLOWANCE_SOURCE,
        }, authorization=manifest['authorization'],
        ledger_prefix=manifest['ledger_prefix'], source_commit=source, plan_commit=manifest['plan_commit'],
        final_review=manifest['final_review'], retained_replay_output=ref(report_path),
        artifacts=artifacts, remaining_reserved_seconds=29400,
        phase_remaining_reserved_seconds={mod.JOERN_GROUP: 29400, mod.CODEQL_GROUP: 28032},
        resource_floor_bytes=127*1024**3, resource_floor_checked=True, no_foreign_processes=True,
        exclusive_lock_checked=True, fresh_attempt_namespaces=True, fresh_sidecar_namespaces=True,
        reserve_window_admission_removed=True,
        materialized_source=str(destination), materialized_projection_sha256=checked['projection_sha256'],
        materialized_source_projected_bytes=projected,
        materialized_launch_guard_checked=checked['launch_guard_checked'],
        materialized_launch_environment_markers=checked['launch_environment_markers'],
        materialized_preflight_output=ref(MATERIALIZED_PREFLIGHT),
        admission_source=ref(Path(__file__).resolve().relative_to(ROOT).as_posix()),
        supervisor_source=ref(SUPERVISOR),
        admission_source_sha256=sha(Path(__file__)), utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    output = BASE + 'execution-admission-06.json'
    write(ROOT / output, value)
    print(json.dumps(ref(output)))

if __name__ == '__main__':
    main()
