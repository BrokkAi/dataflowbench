#!/usr/bin/env python3
"""Actual frozen 84-group parser with in-memory candidate and synthetic build proof.

No candidate contract/receipt is written. Only engine-file hashing and retained
history replay are mocked; actual plan/population/group/qualification/input and
adapter-plan parsers run. No subprocess analyzer/build/admission is invoked.
"""
from pathlib import Path,PurePosixPath
import copy,datetime,hashlib,importlib.util,json,tempfile,unittest,subprocess
from unittest.mock import patch
from contextlib import ExitStack
ROOT=Path(__file__).resolve().parents[4];BASE=Path(__file__).resolve().parent

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load(BASE/'bifrost-v0140-frozen-bridge-08.py','actual_parser_bridge07')
r=load(BASE/'bifrost-v0140-replacement-05.py','actual_parser_replacement05')
e=load(ROOT/'scripts/execute-release-v092.py','actual_parser_executor')
INCOMING='reports/releases/v0.9.2/execution-v4/continuations/codeql-independent-pending-03-contract.json'
PLAN_POPULATION_PATH='populations/v0.9.0.json'
BASESHA='1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb'
def raw(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
class ActualParserTests(unittest.TestCase):
 def candidate(self):
  inherited=json.loads((ROOT/INCOMING).read_bytes());plan=copy.deepcopy(inherited)
  q=json.loads((ROOT/r.QUALIFICATION_REF['path']).read_bytes());binary={k:q['tool'][k] for k in ('path','sha256','version','build_identity')};binary['report_version']='bifrost 0.14.0'
  oldrunner=plan['tools']['runner']['path'];oldbinary=plan['tools']['bifrost']['path']
  runner={'path':'/private/tmp/synthetic-bf12-harness-NOT-EXECUTABLE','sha256':sha(b'synthetic-harness')}
  plan['tools']['runner']=runner;plan['tools']['bifrost']=binary;plan['execution_series']=2;plan['execution_authorized']=True;plan['replacement_schema']=r.REPLACEMENT_SCHEMA
  plan['qualifications']['bifrost'].update(evidence=r.QUALIFICATION_REF,groups=q['groups'],status=q['status'],execution_eligible=True)
  plan['resource_reservation']['expires_at_unix_seconds']=datetime.datetime.fromisoformat(r.CUTOFF).timestamp()
  for g in plan['groups']:
   if g['tool']!='bifrost':continue
   g['argv']=[runner['path'] if x==oldrunner else binary['path'] if x==oldbinary else x for x in g['argv']]
   g['maximum_attempts']=3 if g['id']=='bifrost-c-kernel' else 2
   for report in g['reports']:report['tool_version']='bifrost 0.14.0'
  env=next(g['environment'] for g in plan['groups'] if g['tool']=='bifrost');renv={'BIFROST_OPEN_PACKS_DISABLE':'1','PYTHONDONTWRITEBYTECODE':'1'}
  artifact={'schema':'v092-bifrost-runner-artifact/v1','status':'verified','automatic_retry':False,'runner':runner,'source_commit':plan['source_commit'],'runner_source_sha256':plan['runner_source_sha256'],'build':{'source_commit':plan['source_commit'],'runner_source_sha256':plan['runner_source_sha256']},'environment':renv,'executor_environment':env}
  artifactraw=raw(artifact);aref={'path':'reports/releases/v0.9.2/qualification/SYNTHETIC-NOT-PRODUCTION/runner.json','sha256':sha(artifactraw)}
  manifest={'runner':runner,'runner_artifact':aref,'runner_environment':renv,'executor_environment':env,'qualification':r.QUALIFICATION_REF,'contract_delta':{}}
  core={'source_contexts':{BASESHA:{'contract':{'path':'reports/releases/v0.9.2/execution-v4/contract.json','sha256':BASESHA},'source_commit':'a'*40,'plan_commit':'b'*40,'role':'base'}},'continuation':{'contract':{'path':INCOMING,'sha256':sha((ROOT/INCOMING).read_bytes())}}}
  return plan,manifest,core,aref,artifactraw
 def parse(self,mutation=None,qual_mutation=None,path_override=None,population_probe=None,root_override=None,population_raw_mutation=None):
  plan,manifest,core,aref,artifactraw=self.candidate()
  if mutation:mutation(plan)
  data=raw(plan);path=ROOT/'reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-13-contract.json';ref={'path':str(path.relative_to(ROOT)),'sha256':sha(data)}
  if path_override is not None:path=path_override;ref={'path':str(path.relative_to(ROOT)),'sha256':sha(data)}
  read=e._read_json;bound=r.bound;checks=[];hooks=(e.V4_CONTRACT_PATH,e._read_json,e._wall_budget,e._validate_resource_recovery,e._source_inputs,e._population)
  def reader(p,label):
   if Path(p)==path:return copy.deepcopy(plan),data
   value,source=read(p,label)
   if population_raw_mutation and Path(p)==ROOT/PLAN_POPULATION_PATH:source=population_raw_mutation(source)
   if qual_mutation and Path(p)==ROOT/r.QUALIFICATION_REF['path']:
    value=copy.deepcopy(value);qual_mutation(value)
   return value,source
  def artifact_bound(root,ref,label):return artifactraw if ref==aref else bound(root,ref,label)
  recovered={'base':{'validated':{'bytes_sha256':BASESHA,'resource_recovery':{'SYNTHETIC-REPLAY-NOT-PERFORMED':True}}}}
  try:
   with ExitStack() as st:
    st.enter_context(patch.object(e,'_read_json',side_effect=reader));st.enter_context(patch.object(e,'_check_tool_file',side_effect=lambda binding,name:checks.append(name)))
    st.enter_context(patch.object(r,'bound',side_effect=artifact_bound));st.enter_context(patch.object(b,'_incoming_recovery',return_value=recovered))
    if population_probe:
     original=e._population
     def probe_population(p,pp):
      population_probe(e,p,pp)
      return original(p,pp)
     st.enter_context(patch.object(e,'_population',side_effect=probe_population))
    value=b._validate_replacement_with_scoped_resource_boundary(ROOT if root_override is None else root_override,e,r,path,ref,data,core,manifest,plan['source_commit'],[],b'')
   self.assertEqual(value['plan'],plan);self.assertEqual(value['path'],str(path));self.assertEqual(value['bytes_sha256'],ref['sha256']);self.assertEqual(value['plan_raw'],data)
   self.assertEqual(len(value['groups']),84);self.assertEqual(sum(len(g['reports']) for g in value['groups']),92)
   self.assertEqual(value['total_wall_budget_seconds'],None);self.assertEqual(value['plan']['resource_guards']['working_set_gib'],30)
   self.assertEqual(len(checks),len(plan['tools']))
   self.assertEqual(next(g for g in value['groups'] if g['id']=='bifrost-c-kernel')['maximum_attempts'],3)
   return value
  finally:
   self.assertEqual(e.V4_CONTRACT_PATH,hooks[0]);self.assertIs(e._read_json,hooks[1]);self.assertIs(e._wall_budget,hooks[2]);self.assertIs(e._validate_resource_recovery,hooks[3]);self.assertIs(e._source_inputs,hooks[4]);self.assertIs(e._population,hooks[5])
 def test_actual_deep_contract_population_anchor(self):
  observed=[]
  def probe(executor,plan,path):observed.append(path)
  value=self.parse(population_probe=probe)
  self.assertTrue(observed)
  self.assertEqual(observed,[ROOT/'reports/releases/v0.9.2/execution-v4/contract.json'])
  self.assertEqual(value['path'],str(ROOT/'reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-13-contract.json'))
  self.assertEqual(value['population_raw'],(ROOT/PLAN_POPULATION_PATH).read_bytes())
  self.assertEqual(sha(value['population_raw']),value['plan']['population']['sha256'])
  self.assertEqual(value['fixture_revision'],json.loads(value['population_raw'])['fixture_revision'])
 def test_population_projection_rejects_noncanonical_successor_path(self):
  for path in [ROOT/'reports/releases/v0.9.2/execution-v5-bifrost-v0140/contract.json',ROOT/'reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-12-contract.json']:
   with self.assertRaisesRegex(ValueError,'exact replacement13 contract path'):self.parse(path_override=path)
 def test_population_projection_rejects_different_repository_root(self):
  with self.assertRaisesRegex(ValueError,'replacement parser path'):self.parse(root_override=ROOT/'reports')
 def test_original_population_raw_hash_guard_retained(self):
  with self.assertRaisesRegex(ValueError,'frozen validator rejected'):self.parse(population_raw_mutation=lambda raw:raw+b' ')
 def test_population_hook_restored_on_actual_population_failure(self):
  def fail(executor,plan,path):raise RuntimeError('synthetic population read failure')
  with self.assertRaisesRegex(ValueError,'frozen validator rejected'):self.parse(population_probe=fail)
 def test_population_projection_rejects_wrong_runtime_plan_and_path(self):
  def probe(executor,plan,path):
   # At original-helper entry the scoped executor hook remains installed.
   for changed,wrongpath in [(dict(plan,fixture_revision='wrong'),ROOT/'elsewhere.json'),(plan,ROOT/'reports/releases/v0.9.2/execution-v4/contract.json')]:
    with self.assertRaisesRegex(ValueError,'another plan/path/root'):executor._population(changed,wrongpath)
  self.parse(population_probe=probe)
 def test_actual_frozen_full84_positive(self):self.parse()
 def test_c_fourth_attempt_rejected(self):
  with self.assertRaisesRegex(ValueError,'C03 cap'):self.parse(lambda p:next(g for g in p['groups'] if g['id']=='bifrost-c-kernel').update(maximum_attempts=4))
 def test_non_bifrost_joern_cap_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'replacement gates'):self.parse(lambda p:next(g for g in p['groups'] if g['id']=='joern-swift-common108').update(maximum_attempts=4))
 def test_unlimited_cap_rejected(self):
  with self.assertRaises(ValueError):self.parse(lambda p:next(g for g in p['groups'] if g['id']=='bifrost-java-kernel').update(maximum_attempts=None))
 def test_wrong_report_partition_rejected(self):
  with self.assertRaises(ValueError):self.parse(lambda p:next(g for g in p['groups'] if g['id']=='bifrost-java-kernel')['reports'][0]['case_ids'].pop())
 def test_changed_qualification_read_object_rejected_even_if_raw_unchanged(self):
  with self.assertRaisesRegex(ValueError,'changed immutable bytes'):self.parse(qual_mutation=lambda q:q['tool'].update(bytes=1))
 def test_outer_floor_cannot_relax(self):
  with self.assertRaises(ValueError):self.parse(lambda p:p['resource_budget'].update(minimum_launch_free_gib=109))
 def test_noexpiry_cannot_be_reset(self):
  with self.assertRaises(ValueError):self.parse(lambda p:p.update(total_wall_budget_seconds=999999999))
 def test_actual_normalized_closure_keeps_all_inherited_paths(self):
  value=self.parse();old=json.loads((ROOT/INCOMING).read_bytes())
  self.assertEqual(set(x['path'] for x in value['source_inputs']),set(x['path'] for x in old['source_inputs'])|{r.QUALIFICATION_REF['path']})
  self.assertEqual(next(x for x in value['source_inputs'] if x['path']==r.QUALIFICATION_REF['path'])['role'],'qualification-evidence')
 def test_inherited_input_cannot_be_removed(self):
  with self.assertRaises(ValueError):self.parse(lambda p:p['source_inputs'].pop())
 def test_inherited_input_role_cannot_change(self):
  with self.assertRaises(ValueError):self.parse(lambda p:p['source_inputs'][0].update(role='rewritten'))
 def test_inherited_receipt_hash_cannot_change(self):
  with self.assertRaises(ValueError):self.parse(lambda p:next(x for x in p['source_inputs'] if x['path'].startswith('reports/releases/v0.9.2/attempts/')).update(sha256='0'*64))
 def test_new_arbitrary_path_cannot_join_inherited_exception(self):
  with self.assertRaisesRegex(ValueError,'outside frozen'):self.parse(lambda p:p['source_inputs'].append({'path':'scripts/unapproved.py','sha256':'a'*64,'role':'release-input'}))
 def test_duplicate_input_cannot_be_normalized_away(self):
  with self.assertRaises(ValueError):self.parse(lambda p:p['source_inputs'].append(copy.deepcopy(p['source_inputs'][0])))
 def test_all_typed_qualification_limits_retained(self):
  value=self.parse();self.assertEqual(value['qualification']['bifrost']['status'],'measurement-with-known-limits')
  self.assertEqual(json.loads((ROOT/r.QUALIFICATION_REF['path']).read_bytes())['limits'],list(r.QUALIFICATION_LIMITS))
 def test_unreviewed_retention_or_reserve_rejected(self):
  for key,value in [('protected_reserve_gib',39),('scratch_gib',25),('proposed_total_retention_ceiling_gib',25),('serial_analyzers',2)]:
   with self.subTest(key=key),self.assertRaises(ValueError):self.parse(lambda p:p['resource_budget'].update({key:value}))
 def test_non_bifrost_deadline_and_environment_cannot_change(self):
  for fn in [lambda g:g.update(deadline_seconds=1),lambda g:g['environment'].update(UNREVIEWED='1')]:
   with self.subTest(fn=fn),self.assertRaises(ValueError):self.parse(lambda p:fn(next(g for g in p['groups'] if g['id']=='joern-swift-common108')))
 def test_sourceguard_real_temp_git_positive_and_untracked_negative(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'scripts').mkdir();(root/'src').mkdir();(root/'src/lib.rs').write_text('fn main() {}\n');(root/'scripts/execute-release-v092.py').write_bytes(b'frozen runner\n')
   def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL).decode().strip()
   git('init');git('add','.');git('-c','commit.gpgsign=false','-c','user.name=synthetic','-c','user.email=synthetic@example.invalid','commit','-m','synthetic sourceguard fixture');commit=git('rev-parse','HEAD');runner=sha((root/'scripts/execute-release-v092.py').read_bytes())
   e._assert_source_snapshot(root,commit,runner,[])
   (root/'scripts/untracked.py').write_text('# preserve unrelated\n')
   with self.assertRaisesRegex(e.ReleaseError,'untracked inputs'):e._assert_source_snapshot(root,commit,runner,[])
 def test_canonical_alias_and_reader_restore_after_frozen_parse_failure(self):
  with patch.object(e,'_population',side_effect=e.ReleaseError('synthetic parser failure')):
   with self.assertRaisesRegex(ValueError,'frozen validator rejected'):self.parse()
 def test_unexpected_rich_qualification_component_is_not_dropped(self):
  with self.assertRaisesRegex(ValueError,'changed immutable bytes'):self.parse(qual_mutation=lambda q:q.update(identity_components=[{'unexpected':True}]))

class ActualFreshnessTests(unittest.TestCase):
 def test_c03_actual_frozen_freshness_and_fourth_rejection(self):
  supervisor=load(BASE/'bifrost-v0140-supervisor-13.py','parser_supervisor12')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);rows=[{'group_id':'bifrost-c-kernel','execution_series':1,'status':'recorder-error'},{'group_id':'bifrost-c-kernel','execution_series':1,'status':'completed'}]
   with patch.object(e,'_ledger_rows',return_value=rows):
    original=e._assert_fresh
    with supervisor._scoped_fresh_attempt(e,'bifrost-c-kernel'):
     result=e._assert_fresh(root,{'id':'bifrost-c-kernel','maximum_attempts':3},[],2)
     self.assertEqual(result[-1],'bifrost-c-kernel-attempt-03-series-02')
     with self.assertRaisesRegex(ValueError,'maximum_attempts=3'):e._assert_fresh(root,{'id':'bifrost-c-kernel','maximum_attempts':4},[],2)
     rows.append({'group_id':'bifrost-c-kernel','execution_series':2,'status':'failed'})
     with self.assertRaisesRegex(e.ReleaseError,'maximum_attempts'):e._assert_fresh(root,{'id':'bifrost-c-kernel','maximum_attempts':3},[],2)
    self.assertIs(e._assert_fresh,original)
 def test_successor_paths_are_consistent_in_all_four_modules(self):
  protocol=load(BASE/'bifrost-v0140-replacement-13.py','parser_protocol12')
  admission=load(BASE/'bifrost-v0140-admission-13.py','parser_admission12')
  supervisor=load(BASE/'bifrost-v0140-supervisor-13.py','parser_supervisor12_paths')
  packet=load(BASE/'bifrost-v0140-packet-13.py','parser_packet12')
  self.assertEqual(protocol.BRIDGE_SOURCE_PATH,admission.BRIDGE_PATH)
  self.assertEqual(protocol.BRIDGE_SOURCE_PATH,supervisor.BRIDGE_PATH)
  self.assertEqual(admission.PROTOCOL_PATH,packet.PROTOCOL_PATH)
  self.assertEqual(admission.PROTOCOL_PATH,supervisor.PROTOCOL_PATH)
  self.assertEqual(protocol.MANIFEST_PATH,admission.FINAL_MANIFEST_PATH)
  self.assertEqual(protocol.MANIFEST_PATH,supervisor.MANIFEST_PATH)
 def test_admission_loads_exact_protocol_bound_actual_parser_test(self):
  protocol=load(BASE/'bifrost-v0140-replacement-13.py','parser_protocol12_admission')
  admission=load(BASE/'bifrost-v0140-admission-13.py','parser_admission12_exact_tests')
  core={'frozen_bridge_source':{'path':protocol.BRIDGE_SOURCE_PATH,'sha256':sha((ROOT/protocol.BRIDGE_SOURCE_PATH).read_bytes())},'frozen_bridge_tests':{'path':protocol.BRIDGE_TEST_PATH,'sha256':sha((ROOT/protocol.BRIDGE_TEST_PATH).read_bytes())}}
  self.assertTrue(callable(admission._load_bridge(ROOT,core).validate_frozen_bridge))
  for wrong in ['reports/releases/v0.9.2/acquisition/test-bifrost-v0140-frozen-bridge-08.py',protocol.BRIDGE_TEST_PATH+'.extra']:
   bad=copy.deepcopy(core);bad['frozen_bridge_tests']['path']=wrong
   with self.assertRaisesRegex(ValueError,'actual-parser test08'):admission._load_bridge(ROOT,bad)

if __name__=='__main__':unittest.main(verbosity=2)
