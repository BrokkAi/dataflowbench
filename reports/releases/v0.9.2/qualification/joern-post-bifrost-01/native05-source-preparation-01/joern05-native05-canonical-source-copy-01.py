import json,hashlib,datetime,copy
from pathlib import Path
r=Path('/Users/dave/.codex/worktrees/9f01/dataflowbench');p='reports/releases/v0.9.2/';a=p+'acquisition/';q=p+'qualification/joern-post-bifrost-01/';v=p+'validation/joern-post-bifrost-01/';c=p+'qualification/joern-capability-repair-01/'
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def ref(x):return {'path':x,'sha256':sha(r/x)}
def write(x,data):
 with (r/x).open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
review=Path('/private/tmp/joern05-native05-source-integration-independent-review-01.json');assert sha(review)=='e8f5af5a8f9ac6b5a4e0842dc1ffcaa5fa7fa52ec2961a2c0cb6d64e289c411c'
z=json.loads(review.read_bytes());assert z['decision']['status']=='approved-source-copy-commit-request-preparation-only' and not z['decision']['approve_runtime_activation']
reviewrel=v+'native05-source-integration-independent-review-01.json'
with (r/reviewrel).open('xb') as f:f.write(review.read_bytes())
h=Path('/private/tmp/joern05-native-qualifier-08/implementation-handoff-08.json');assert sha(h)=='7505c7cee1ae2ef947510ea845303832de6f8de5cb7af4d62cd54c77eaccc830';handoff=json.loads(h.read_bytes())
dest=r/a/'joern-native-controls-05';assert not dest.exists();dest.mkdir()
entries=[]
for item in handoff['files']+[{'path':str(h),'sha256':sha(h),'bytes':h.stat().st_size}]:
 src=Path(item['path']);assert not src.is_symlink() and src.is_file() and sha(src)==item['sha256'] and src.stat().st_size==item['bytes'];target=dest/src.name
 with target.open('xb') as f:f.write(src.read_bytes())
 assert sha(target)==item['sha256']
 entries.append({'source':str(src),'copy':str(target.relative_to(r)),'sha256':sha(target),'bytes':target.stat().st_size})
copyrel=v+'native-qualifier08-canonical-copy-01.json'
write(copyrel,{'schema':'v092-native05-exact-source-copy/v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'copies':entries,'independent_source_review':ref(reviewrel),'source_preparation_only':True,'runtime_invoked':False,'qualification_inferred':False,'publication_hold':True})
x=copy.deepcopy(json.loads((r/q/'native-control-authority-derivation-04.json').read_bytes()))
x.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),allowed_namespace=q+'native-controls-05',preparation_parent_head='76e6121651e94be113fd0d5f027419f7d0f0859b',predecessor_authority=ref(q+'native-control-authority-derivation-04.json'),canonical_wrapper=ref(a+'joern-native-controls-05/native_qualifier.py'),canonical_resources=ref(a+'joern-native-controls-05/retained_resources.py'),observer=ref(a+'joern-native-startup-observer-07.py'),pending_plan=ref(c+'plan-v092-06/pending-execution-plan-01.json'),control_plan=ref(c+'plan-v092-06/control-plan-01.json'))
x['earlier_consumed_invocations'].append(x.pop('prior_consumed_invocation'))
x['prior_consumed_invocation']={'namespace':'native-controls-04','preserved':True,'terminal':ref(q+'native-controls-04/exit.json'),'root_stop_check':ref(v+'native-controls04-root-stop-check-01.json'),'independent_diagnosis':ref(v+'native-controls04-stop-independent-review-01.json'),'partial_arm_diagnosis':ref(q+'native-controls04-partial-arm-diagnosis-01.json'),'benchmark_attempt_consumed':False,'qualification_accepted':False,'actual_contender_identity':'unknown; rejected command rows not preserved','descendant_containment':'unknown; recorded exact births gone'}
x['source_and_copy_reviews']=[ref(reviewrel),ref(copyrel),ref(v+'native-qualifier07-independent-review-01.json'),ref(v+'startup-observer08-independent-source-review-01.json'),ref(v+'startup-observer07-sealed-independent-review-01.json'),ref(v+'startup-observer07-sealed-review-clarification-01.json'),ref(v+'startup-observer07-canonical-copy-01.json')]
x.pop('registration_successor_design',None)
x['integration_decision']=ref(q+'native-controls05-source-integration-decision-01.json')
x['repair_required']=['Preserve native04 failure; monitor commands first then fresh native identities, merge only exact-birth owned descendants, preserve rejected-row diagnostic receipt; command rows have no birth so polling is not atomic ownership or complete containment proof.','Use sealed agent05 and observer07 v5 bounded ancestry ONLY for untracked command-absent diagnostic version helpers; semantic JVMs retain native exact tracking and direct parent proof. Maximum32 sampled nodes/edges; first tracked/host mismatch rejects; no historical99171/99172 ownership inference.','Append-only12prospective decisions03 and pendingplan06/control06, preserving169 historical evidence refs each,108cases/96attempts/falseeligibility/nullfresh and allresource/time limits; inheritedv4 evidence is not v5 runtime proof.','New native-controls05 namespace/request/exact review/fresh admission only; no reuse01-04 or scored Joern05 authority.']
x['scope']='One fresh native-controls-05 qualification after independently reviewed monitor and diagnostic ancestry repairs. Derived from existing human autonomous/no-expiry/resource authority. No new human/time/scored-attempt approval, Unsupported issuance, publication or semantic completion is inferred.'
x['diagnostic_boundary']={'untracked_helper_native_self_birth_verified':False,'semantic_qualification_inferred':False,'historical_offender_identity':'unknown','complete_descendant_coverage':False,'ancestor_correlation':'bounded sampled chain to first exact trusted anchor; version-only diagnostic'}
x['source_commit_pending']=True;x['runtime_qualification_performed']=False
write(q+'native-control-authority-derivation-05.json',x)
print(json.dumps({'copy':ref(copyrel),'integration_review':ref(reviewrel),'authority':ref(q+'native-control-authority-derivation-05.json'),'copied_files':len(entries),'runtime_invoked':False}))
