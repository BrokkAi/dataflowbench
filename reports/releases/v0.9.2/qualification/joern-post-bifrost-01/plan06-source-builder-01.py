"""Append-only prospective startup-policy artifacts; no runtime or eligibility."""
from pathlib import Path
import copy, datetime, hashlib, importlib.util, json, sys, time

R = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
Q = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/'
O = Path('/private/tmp/joern05-native-control-09/joern_native_control_observer_v07.py')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path': str(p.relative_to(R)), 'sha256': sha(p)}
def read(p): return json.loads(p.read_bytes())
def write(p, value):
    with p.open('x') as f: json.dump(value, f, indent=2, sort_keys=True); f.write('\n')

assert sha(O) == '4e3998dfb3f32b5d377c8697ea644d247f147220679eb784cc64fc501f7bc199'
assert len(sys.argv) == 2
review = Path(sys.argv[1]); rv = read(review)
assert rv['approve_minimal_plan_control_decision_delta'] is True if 'approve_minimal_plan_control_decision_delta' in rv else rv['decision']['approve_minimal_plan_control_decision_delta'] is True
spec = importlib.util.spec_from_file_location('plan06_sealed_observer_source', O)
observer = importlib.util.module_from_spec(spec); spec.loader.exec_module(observer)
policy = copy.deepcopy(observer.STARTUP_POLICY_V5)
assert policy['agent_jar']['sha256'] == '1e30a6a5c88abb0216c5f205bd337f18fc30dd91345a8aeae244398cc0803261'
assert policy['ancestry']['maximum_links'] == 32
basepath = R / (Q + 'plan-v092-05/pending-execution-plan-01.json')
assert sha(basepath) == 'c79f93dca045d8fbf2b7221fbf20e042d7546d403567a821ed1594fda8411137'
base = read(basepath); plan = copy.deepcopy(base)
oldcontrolpath = R / base['qualification_control_plan']['path']
assert sha(oldcontrolpath) == base['qualification_control_plan']['sha256']
oldcontrol = read(oldcontrolpath)
decisions = R / (Q + 'unsupported-decisions-03')
destination = R / (Q + 'plan-v092-06')
assert not decisions.exists() and not destination.exists()
decisions.mkdir(); destination.mkdir()
changes = []
for caseid, row in sorted(plan['cases'].items()):
    if 'decision' not in row: continue
    oldpath = R / row['decision']['path']; assert sha(oldpath) == row['decision']['sha256']
    old = read(oldpath); new = copy.deepcopy(old)
    assert len(old['evidence']) == 169 and old['proof_scope']['prospective_only'] is True
    assert old['proof_scope']['fresh_control_and_jvm_witness_required'] is True
    new['jvm_startup_policy'] = copy.deepcopy(policy)
    assert {k:v for k,v in old.items() if k != 'jvm_startup_policy'} == {k:v for k,v in new.items() if k != 'jvm_startup_policy'}
    target = decisions / (caseid + '.json'); write(target, new)
    before = row['decision']; row['decision'] = ref(target)
    changes.append({'case_id':caseid, 'before':before, 'after':row['decision'], 'evidence_refs_preserved':169})
assert len(changes) == 12
spec = importlib.util.spec_from_file_location('plan06_frozen_projection', R/'scripts/v092_qualification.py')
qualification = importlib.util.module_from_spec(spec); spec.loader.exec_module(qualification)
projection = qualification.plan_projection_sha256(plan)
assert projection != base['qualification_control_projection_sha256']
control = copy.deepcopy(oldcontrol); control['execution_plan_projection_sha256'] = projection
assert {k:v for k,v in control.items() if k!='execution_plan_projection_sha256'} == {k:v for k,v in oldcontrol.items() if k!='execution_plan_projection_sha256'}
controlpath = destination / 'control-plan-01.json'; write(controlpath, control)
plan['qualification_control_plan'] = ref(controlpath)
plan['qualification_control_projection_sha256'] = projection
plan['registered_at_unix_seconds'] = int(time.time())
assert qualification.plan_projection_sha256(plan) == projection
allowed = {'cases','qualification_control_plan','qualification_control_projection_sha256','registered_at_unix_seconds'}
assert {k:v for k,v in plan.items() if k not in allowed} == {k:v for k,v in base.items() if k not in allowed}
for caseid, row in base['cases'].items():
    assert {k:v for k,v in row.items() if k!='decision'} == {k:v for k,v in plan['cases'][caseid].items() if k!='decision'}
assert len(plan['cases']) == 108 and sum(x['disposition']=='attempt' for x in plan['cases'].values()) == 96
assert plan['fresh_qualification'] is None and plan['execution_eligible'] is False and plan['diagnostic_execution_eligible'] is False
planpath = destination/'pending-execution-plan-01.json'; write(planpath, plan)
handoff = {'schema':'v092-plan06-prospective-source-handoff/v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_builder':{'path':str(Path(__file__)), 'sha256':sha(Path(__file__))},
 'base_plan':ref(basepath), 'base_control':ref(oldcontrolpath), 'plan':ref(planpath), 'control':ref(controlpath),
 'observer_source':{'path':str(O),'sha256':sha(O)}, 'design_review':{'path':str(review),'sha256':sha(review)},
 'projection_sha256':projection, 'decision_changes':changes, 'cases':108,'attempts':96,'prospective_unsupported':12,
 'actual_native_qualification':False,'engine_dispatched':False,'eligibility_granted':False,'publication_hold':True,'automatic_retry':False,
 'limits':'Historical169refs per decision preserved; v4 evidence is not v5 execution proof. At most32nodes/32edges; sampled diagnostic helper correlation only; no semantic ownership promotion. Actual new12arms36phases and independent review remain required.'}
out = destination/'source-handoff-01.json'; write(out,handoff)
print(json.dumps({'handoff':ref(out), 'plan':ref(planpath), 'control':ref(controlpath),'projection':projection}))
