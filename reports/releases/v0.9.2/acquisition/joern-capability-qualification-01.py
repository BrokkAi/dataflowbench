#!/usr/bin/env python3
"""Replay genuine repaired-projection controls and write new qualification bindings."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path.cwd().resolve()
BASE = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/'
PENDING = BASE + 'plan-v092-02/pending-execution-plan-01.json'
FINAL = BASE + 'plan-v092-02/execution-plan.json'
CAPTURE = BASE + 'control-capture-01/run.json'
REVIEW = BASE + 'control-capture-01/diagnostic-admission-review-01.json'
RECEIPT = BASE + 'control-capture-01/qualification-receipt-01.json'
SHIM_SHA = '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f'
LEDGER_SHA = 'ca7152afb422160b30c2f38677aa539a1463b45e3b41131848b3d9e81d4a1084'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def ref(relative):
    return {'path': relative, 'sha256': sha(ROOT / relative)}

def write(relative, value):
    with (ROOT / relative).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')

def main():
    require(sha(ROOT / 'reports/releases/v0.9.2/ledger-v1.jsonl') == LEDGER_SHA, 'release ledger changed')
    exit_record = json.loads((ROOT / BASE / 'control-launch-01/exit.json').read_bytes())
    require(exit_record.get('status') == 'capture-complete-review-pending' and
            exit_record.get('run_sha256') == sha(ROOT / CAPTURE), 'fresh capture did not finish correctly')
    shim_path = ROOT / 'scripts/joern_capability_repair_v092.py'
    require(sha(shim_path) == SHIM_SHA, 'reviewed shim changed')
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('qualification_repair_shim', shim_path)
    shim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim)
    inputs = shim.validate_bootstrap_inputs(ROOT, new_plan_path=PENDING,
        expected_new_plan_sha256='b4f2d8ed15f6c9055baaad7afa71ece638da80b1d87e643aad40ca1f66a18293',
        expected_evidence_sha256='deefa524579114d6fa42271193b6f4def69e296ffd23023f1e72ae7d2ee4a005')
    runner = inputs['runner']
    shim._assert_canonical_historical_binding(ROOT)
    runner.EXECUTION_PLAN_PATH = PENDING
    plan, _, context = runner.validate_plan(ROOT, PENDING, allow_qualification_pending=True)
    run = runner.read(ROOT / CAPTURE)
    require(run.get('control_plan_sha256') == plan['qualification_control_plan']['sha256'] and
            run.get('execution_plan_projection_sha256') == inputs['projection_sha256'], 'fresh capture binding mismatch')
    import swift_common_population_v2 as common
    import joern_diagnostic_admission_v092 as diagnostic
    _, common_rows, _, cases, _ = common.load_common_population(ROOT)
    case_paths = {row['id']: ROOT / row['path'] for row in common_rows}
    observations, count = runner._replay_control_run(ROOT, plan, context['control'], run,
        cases, context['engine'], case_paths=case_paths)
    require(count == 36 and len(run['records']) == 12, 'fresh control matrix incomplete')
    require(run['assessment'] == context['engine'].assess_controls(observations), 'fresh assessment differs from replay')
    review = diagnostic.replay_admission(ROOT, plan, context['control'], run, observations, cases, case_paths)
    review.update(control_run=ref(CAPTURE), reviewer=ref('scripts/joern_diagnostic_admission_v092.py'),
                  control_plan=plan['qualification_control_plan'])
    require(review.get('status') == 'measurement-with-known-limits' and
            review.get('full_model_qualification') is False and review.get('scored_activation') is False,
            'fresh controls do not support the reviewed diagnostic boundary')
    for relative in [REVIEW, RECEIPT, FINAL]:
        require(not (ROOT / relative).exists(), 'qualification output already exists: ' + relative)
    write(REVIEW, review)
    old_receipt = runner.read(ROOT / inputs['old_plan']['fresh_qualification']['path'])
    receipt = copy.deepcopy(old_receipt)
    receipt.update(control_run=ref(CAPTURE), diagnostic_admission_review=ref(REVIEW),
                   execution_plan_projection_sha256=inputs['projection_sha256'])
    receipt['dimensions']['common108_controls'].update(control_run=ref(CAPTURE),
        phase_invocation_count=count, strict_assessment=run['assessment'])
    receipt['dimensions']['joern_diagnostic_admission'] = ref(REVIEW)
    write(RECEIPT, receipt)
    final = copy.deepcopy(plan)
    final.update(status='execution-eligible', execution_eligible=True, diagnostic_execution_eligible=True,
                 fresh_qualification=ref(RECEIPT), registered_at_unix_seconds=int(time.time()) - 1)
    write(FINAL, final)
    runner.EXECUTION_PLAN_PATH = shim.OLD_PLAN_PATH
    checked = shim.preflight(ROOT, new_plan_path=FINAL, expected_new_plan_sha256=sha(ROOT / FINAL),
                             expected_evidence_sha256=inputs['evidence_sha256'])
    require(sha(ROOT / 'reports/releases/v0.9.2/ledger-v1.jsonl') == LEDGER_SHA, 'read-only replay changed ledger')
    write(BASE + 'qualification-finalization-01.json', dict(
        status='replayed-qualification-independent-review-pending', repaired_plan=ref(FINAL),
        qualification_receipt=ref(RECEIPT), diagnostic_review=ref(REVIEW), control_run=ref(CAPTURE),
        projection_sha256=checked['projection_sha256'], ledger_sha256=LEDGER_SHA,
        analyzer_invoked=False, fresh_case_arms=12, fresh_phase_invocations=count,
        full_model_qualification=False, scored_activation=False))
    print(json.dumps({'status':'replayed-qualification-independent-review-pending','plan':ref(FINAL)}))

if __name__ == '__main__':
    main()
