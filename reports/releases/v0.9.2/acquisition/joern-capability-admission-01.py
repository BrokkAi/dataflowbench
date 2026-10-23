#!/usr/bin/env python3
"""Read-only retained replay/materialized-source checks and one-shot admission."""
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
MODULE = 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py'

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
    source = manifest['source_commit']
    report_path = BASE + 'retained-preflight-01.json'
    replay = subprocess.run([sys.executable, '-E', str(ROOT / MODULE), 'preflight',
        '--manifest', args.manifest, '--manifest-sha256', args.manifest_sha256],
        cwd=ROOT, capture_output=True, check=True)
    with (ROOT / report_path).open('xb') as f:
        f.write(replay.stdout)
    with (ROOT / BASE / 'retained-preflight-01-stderr.txt').open('xb') as f:
        f.write(replay.stderr)
    destination = ROOT / 'execution-state/v092/joern-capability-materialized-preflight-01'
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
        sys.path.insert(0, str(destination / 'scripts'))
        shim_spec = importlib.util.spec_from_file_location('materialized_repair',
                         destination / manifest['artifacts']['joern_shim']['path'])
        shim = importlib.util.module_from_spec(shim_spec)
        shim_spec.loader.exec_module(shim)
        checked = shim.preflight(destination,
            new_plan_path=manifest['artifacts']['repaired_plan']['path'],
            expected_new_plan_sha256=manifest['artifacts']['repaired_plan']['sha256'],
            expected_evidence_sha256=manifest['artifacts']['capability_evidence']['sha256'])
        executor._check_resources(ROOT, 127 * 1024**3)
        mod.require(time.time() + 29400 <= datetime.datetime.fromisoformat(mod.CUTOFF).timestamp(),
                    'remaining complete reservation cannot fit')
    artifacts = dict(manifest['artifacts'])
    artifacts['continuation_test'] = ref(mod.CONTINUATION_TEST)
    value = dict(schema='v092-joern-capability-continuation-admission/v1',
        status='ready-to-execute', automatic_retry=False, release_group_attempt=False,
        original_origin_utc=mod.ORIGIN, cutoff_utc=mod.CUTOFF,
        total_wall_budget_seconds=mod.TOTAL_WALL_SECONDS, authorization=manifest['authorization'],
        ledger_prefix=manifest['ledger_prefix'], source_commit=source, plan_commit=manifest['plan_commit'],
        final_review=manifest['final_review'], retained_replay_output=ref(report_path),
        artifacts=artifacts, remaining_reserved_seconds=29400,
        phase_remaining_reserved_seconds={mod.JOERN_GROUP: 29400, mod.CODEQL_GROUP: 28032},
        resource_floor_bytes=127*1024**3, resource_floor_checked=True, no_foreign_processes=True,
        exclusive_lock_checked=True, fresh_attempt_namespaces=True, fresh_sidecar_namespaces=True,
        materialized_source=str(destination), materialized_projection_sha256=checked['projection_sha256'],
        materialized_source_projected_bytes=projected,
        admission_source_sha256=sha(Path(__file__)), utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    output = BASE + 'execution-admission-01.json'
    write(ROOT / output, value)
    print(json.dumps(ref(output)))

if __name__ == '__main__':
    main()
