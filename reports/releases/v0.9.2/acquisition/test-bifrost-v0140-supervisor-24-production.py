"""Canonical current24 packet joins. Actual supervisor bodies; no process/admission/replay.
Registry uses byte-copied actual107 fixture; process and graph acquisition are
I/O substitutes, never execution or semantic completion evidence.
"""
import ast,contextlib,copy,importlib.util,json,pathlib,sys,types,unittest,os,subprocess
from unittest.mock import patch
def _repo_root():
 candidates=[pathlib.Path(__file__).resolve(), pathlib.Path.cwd().resolve()]
 candidates.extend(pathlib.Path(__file__).resolve().parents)
 for candidate in candidates:
  root=candidate if (candidate/'reports/releases/v0.9.2/acquisition').is_dir() else candidate.parent
  if (root/'reports/releases/v0.9.2/acquisition').is_dir(): return root
 raise RuntimeError('canonical DataFlowBench repository root is unavailable')

REPO_ROOT=_repo_root();BASE=pathlib.Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

fixture_loader=load('canonical_replacement24_fixture_loader',BASE/'test-bifrost-v0140-replacement-24.py')
f=fixture_loader.load_current_fixture()
p=load('canonical_protocol24',BASE/'bifrost-v0140-replacement-24.py')
e=load('canonical_frozen_executor',REPO_ROOT/'scripts/execute-release-v092.py')
r=load('canonical_replacement05',REPO_ROOT/'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py')
s=load('canonical_supervisor24',BASE/'bifrost-v0140-supervisor-24.py')
class Joins(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  f.RealFunctions.setUpClass();cls.F=f.RealFunctions;cls.root=cls.F.root
 @classmethod
 def tearDownClass(cls):cls.F.tearDownClass()
 def setUp(self):
  self.core=copy.deepcopy(self.F.core);self.core['sidecar_namespace']='fixture-supervisor24';self.rows=copy.deepcopy(self.F.rows)
  (self.root/p.LEDGER_PATH).write_bytes(self.F.raw)
  self.contexts=copy.deepcopy(self.core['source_contexts'])
  for key,entry in self.contexts.items():
   plan=copy.deepcopy(self.F.old and json.loads((REPO_ROOT/entry['contract']['path']).read_bytes())) if key!='c'*64 else copy.deepcopy(json.loads((REPO_ROOT/self.F.old['contract']['path']).read_bytes()))
   entry['validated']={'bytes_sha256':key,'plan':plan,'groups':plan['groups']}
  self.contexts['c'*64]['validated']['plan']['source_commit']='a'*40
 def tearDown(self):
  (self.root/p.LEDGER_PATH).write_bytes(self.F.raw)
  import shutil
  shutil.rmtree(self.root/'fixture-supervisor24',ignore_errors=True)
  for g in p.DISPATCH_GROUPS:shutil.rmtree(self.root/'reports/releases/v0.9.2/attempts'/p._attempt_id(g),ignore_errors=True)
 def tail(self,g,status='completed'):
  value=copy.deepcopy(self.rows[-1]);value.update(group_id=g,attempt_id=p._attempt_id(g),contract_sha256='c'*64,source_commit='a'*40,plan_commit='b'*40,status=status,exit_code=0 if status=='completed' else 1,timed_out=False)
  return value
 def objects(self,rows):
  selected=p.select_resume_rows(self.root,self.core,{'replacement':r,'contexts':self.contexts},rows)
  nreports=nrows=0
  for row in selected.values():
   group=e._historical_group_for_replay(self.contexts[row['contract_sha256']]['validated'],row);nreports+=len(group['reports']);nrows+=sum(len(x['case_ids']) for x in group['reports'])
  summary={'status':'partial-evidence-verified','ledger_rows':len(rows),'selected_groups':len(selected),'partitions':nreports,'rows':nrows,'known_stale':0,'full_release_gate_satisfied':False}
  mixed={'root':self.root,'contract_sha256':'c'*64,'source_commit':'a'*40,'plan_commit':'b'*40,'source_delta':{},'rows':rows,'contexts':self.contexts,'prefix':rows[:89],'prefix_raw':self.F.raw.splitlines(keepends=True)[:89],'replacement':r}
  mixed['prefix_raw']=b''.join(mixed['prefix_raw'])
  return {'modules':{'executor':e,'replacement05':r},'validated':{'bytes_sha256':'c'*64},'mixed_context':mixed,'checker_summary':summary,'configuration_summary':{},'bridge_context':{'context_digest':'d'*64,'checker_summary_or_pending':summary}}
 def test_canonical_owned_functions_are_present_and_disjoint(self):
  """Canonical current24 keeps both reviewed ownership surfaces available."""
  tree=ast.parse((BASE/'bifrost-v0140-supervisor-24.py').read_text())
  names={node.name for node in tree.body if isinstance(node,ast.FunctionDef)}
  timing_owned=(
   '_bounded_reap_owned_group','_child_stage_witness_path','_normalize_analyzer_process_result',
   '_observe_terminal_and_ledger','_open_child_stage_identity_pipe','_phase_receipt',
   '_scoped_analyzer_phase_hook','_signal_owned_group','_validate_analyzer_phase',
   '_validate_child_stage_witness','_validate_child_stage_witness_ref',
   '_write_child_stage_identity','_write_child_stage_witness','_write_coordinator_timeout',
   '_write_timeout_reconciliation')
  for name in timing_owned:self.assertIn(name,names,name)
  self.assertIn('_resume_batch_summary',names)
 def test_actual_supervisor_freshness_wrapper_to_real_frozen_function(self):
  original=e._assert_fresh
  with s._scoped_fresh_attempt(e,'bifrost-smoke',root=self.root,core=self.core,protocol=p):
   self.assertEqual(e._assert_fresh(self.root,{'id':'bifrost-smoke','maximum_attempts':3},[],2)[-1],p._attempt_id('bifrost-smoke'))
  self.assertIs(e._assert_fresh,original)
  with self.assertRaises(ValueError):
   with s._scoped_fresh_attempt(e,'bifrost-c-kernel',root=self.root,core=self.core,protocol=p):pass
 def test_actual_mixed_context107_preserves89_and_rejects_foreign_tail(self):
  objects=self.objects(self.rows)
  with patch.object(s,'_actual_runtime_context',return_value=objects):
   runtime,_=s._mixed_runtime_context(self.root,{},self.core,'f'*64,{},object(),protocol=p)
   self.assertEqual(len(runtime['prefix']),89);self.assertEqual(len(runtime['rows']),107)
   objects['mixed_context']['prefix_raw']+=b' '
   with self.assertRaises(ValueError):s._mixed_runtime_context(self.root,{},self.core,'f'*64,{},object(),protocol=p)
  objects=self.objects(self.rows);bad=self.tail('bifrost-smoke');bad['source_commit']='d'*40;objects['mixed_context']['rows']+= [bad]
  with patch.object(s,'_actual_runtime_context',return_value=objects),self.assertRaises(ValueError):s._mixed_runtime_context(self.root,{},self.core,'f'*64,{},object(),protocol=p)
 def test_actual_stage_ledger_strict107_plus_index(self):
  admission=types.SimpleNamespace(_write_bytes_exclusive=lambda root,path,raw:p.write_immutable_bytes(root,path,raw))
  ref=s._stage_ledger(self.root,admission,self.core,0,protocol=p);self.assertEqual(ref['rows'],107)
  with self.assertRaises(ValueError):s._stage_ledger(self.root,admission,self.core,1,protocol=p)
  with self.assertRaises(ValueError):s._stage_ledger(self.root,admission,self.core,True,protocol=p)
 def test_actual_partial_summary83_and_no_full_configuration_claim(self):
  rows=self.rows+[self.tail(g) for g in p.DISPATCH_GROUPS];objects=self.objects(rows)
  actual=s._resume_batch_summary(self.root,self.core,p,objects)
  self.assertEqual((actual['selected_groups'],actual['partitions'],actual['rows']),(83,87,4144));self.assertFalse(actual['full_release_gate_satisfied'])
  objects['checker_summary']['full_release_gate_satisfied']=True
  with self.assertRaises(ValueError):s._resume_batch_summary(self.root,self.core,p,objects)
 def test_actual_run_groups_dispatches_only_two_and_keeps18_outcomes(self):
  core=self.core;groups=p.dispatch_groups(core);manifest={'core_identity':{'path':'fixture-core','sha256':'f'*64},'execution_admission_slots':{g:{'attempt_id':p._attempt_id(g),'admission_path':f'fixture-supervisor24/{g}/admission.json','phase_gate_path':f'fixture-supervisor24/{g}/phase.json','completion_path':f'fixture-supervisor24/{g}/completion.json'} for g in groups}}
  dispatch=[];stages=[];written=[];build_calls=[]
  def put(root,path,raw):return p.write_immutable_bytes(root,path,raw)
  def simple_ref(*args,**kwargs):return {'path':'fixture-control','sha256':'e'*64}
  bundle={'parent':simple_ref(),'groups':{g:simple_ref() for g in groups}}
  admission=types.SimpleNamespace(validate_authorization_bundle=lambda *a,**kw:bundle,admit_parent=simple_ref,admit_group=simple_ref,write_phase_gate=simple_ref,_write_bytes_exclusive=put,write_completion=lambda *a,**kw:(simple_ref(),kw['successor_stage']))
  loaders=types.SimpleNamespace(PRODUCTION_MODULE_NAMES={},scoped_runtime_loaders=lambda *a,**kw:contextlib.nullcontext())
  graph=types.SimpleNamespace(module=lambda n:loaders if n=='runtime_loaders24' else object())
  def make_stage(root,core,manifest,index,*args,**kwargs):
   rows=[json.loads(line) for line in (root/p.LEDGER_PATH).read_bytes().splitlines()];objects=self.objects(rows)
   stage=types.SimpleNamespace(identity=types.SimpleNamespace(index=index),runtime=types.SimpleNamespace(objects=objects));stages.append(index);return stage
  bridge=types.SimpleNamespace(prepare_graph=lambda *a,**kw:graph,_core_graph_inputs=lambda c:{},capture_lock=lambda *a:object(),create_parent_stage=make_stage,assert_stage_current=lambda *a:None,runtime_objects=lambda stage:stage.runtime)
  class Child:
   pid=12345
   def poll(self):return 0
   def wait(self,timeout=None):return 0
  def popen(argv,**kwargs):
   # Popen is a deliberately bounded fixture: inspect the real run_groups
   # command/descriptor contract, then avoid starting any analyzer process.
   self.assertIn('--child-stage-witness-fd',argv)
   self.assertIn('--child-stage-witness-token',argv)
   witness_fd=int(argv[argv.index('--child-stage-witness-fd')+1])
   witness_token=argv[argv.index('--child-stage-witness-token')+1]
   self.assertTrue(any(call['fd']==witness_fd and call['token']==witness_token for call in build_calls))
   self.assertIn(witness_fd,kwargs.get('pass_fds',()))
   self.assertTrue(kwargs.get('close_fds'))
   self.assertTrue(kwargs.get('start_new_session'))
   g=argv[0];dispatch.append(g);row=self.tail(g,'failed' if getattr(self,'failure_smoke',False) and g=='bifrost-smoke' else 'completed')
   with (self.root/p.LEDGER_PATH).open('ab') as out:out.write(s.canonical_json(row))
   slot=manifest['execution_admission_slots'][g];put(self.root,str(pathlib.PurePosixPath(slot['admission_path']).parent/'ledger-before.jsonl'),self.F.raw if len(dispatch)==1 else self.F.raw+s.canonical_json(self.tail(groups[0])))
   put(self.root,f'reports/releases/v0.9.2/attempts/{p._attempt_id(g)}/completed.json',s.canonical_json(row));return Child()
  lock=(self.root/'fixture-lock').open('a+b');self.addCleanup(lock.close)
  def build_command(root,m,sha,c,g,**kw):
   # This command builder is a fixture only; the actual admission-positive
   # command/schema seam is exercised by the timing-composed suite.
   fd=kw.get('child_stage_witness_fd');token=kw.get('child_stage_witness_token')
   self.assertIs(type(fd),int);self.assertGreater(fd,2)
   self.assertIsInstance(token,str);self.assertRegex(token,r'^[0-9a-f]{32}$')
   self.assertEqual(kw.get('context_path'),s._group_context_path(manifest,g))
   build_calls.append({'group':g,'fd':fd,'token':token,'context_path':kw.get('context_path')})
   return {'argv':[g,'--bridge-context',kw['context_path'],
                    '--child-stage-witness-fd',str(fd),
                    '--child-stage-witness-token',token], 'environment':{}}
  patches={'_static':lambda *a:(p,manifest,core),'_load_admission':lambda *a:admission,'_load_bridge':lambda *a:bridge,'_lock_target':lambda *a:self.root/'fixture-lock','_lock_fd':lambda *a:contextlib.nullcontext(lock),'_process':lambda *a:{'birth_identity':'fixture-birth'},'raw_permit':lambda *a,**kw:{},'_write_raw_permit':simple_ref,'_stage_receipt':simple_ref,'build_group_command':build_command,'_wait_group_child':lambda *a,**kw:0,'_terminal_continuation_safety':lambda *a,**kw:{'owned_processes_gone':True}}
  with contextlib.ExitStack() as stack:
   stack.enter_context(patch.dict(s.os.environ,{s.FIXTURE_ENV:'1'}))
   for name,value in patches.items():stack.enter_context(patch.object(s,name,value))
   stack.enter_context(patch.object(s.subprocess,'Popen',popen))
   if getattr(self,'failure_smoke',False):
    with self.assertRaisesRegex(ValueError,'stops after any non-success'):
     s.run_groups(self.root,s.MANIFEST_PATH,'f'*64,None,None,None,{},fixture_only=True,authorization_bundle_ref=simple_ref(),authorization_bundle_sha256='e'*64)
    self.assertEqual(dispatch,['bifrost-smoke']);self.assertEqual(stages,[0,1])
    stop=json.loads((self.root/'fixture-supervisor24/batch-stop-01.json').read_bytes());self.assertFalse(stop['later_groups_dispatched']);self.assertEqual(stop['outcomes'][0]['status'],'failed');return
   result=s.run_groups(self.root,s.MANIFEST_PATH,'f'*64,None,None,None,{},fixture_only=True,authorization_bundle_ref=simple_ref(),authorization_bundle_sha256='e'*64)
  self.assertEqual(dispatch,groups);self.assertEqual(stages,[0,1,2]);self.assertEqual(len(result['outcomes']),2);self.assertEqual(len(result['retained_outcomes']),18);self.assertFalse(result['full_release_gate_satisfied']);self.assertEqual(result['selected_matrix']['rows'],4144)
  self.assertEqual(len(build_calls),len(groups))
  self.assertEqual(len({call['token'] for call in build_calls}),len(groups))
  self.assertTrue(all(call['context_path']==s._group_context_path(manifest,call['group']) for call in build_calls))

 def test_lossless_acquisition_validation_then_real107_context_check(self):
  objects=self.objects(self.rows);modules=objects['modules'];modules.update(checker=object(),configuration=object())
  v=objects['validated'];v.update(plan={'execution_authorized':True},path=str(self.root/self.core['contract']['path']),repo_root=str(self.root))
  mixed=objects['mixed_context'];mixed.update(executor=e,checker=modules['checker'],configuration=modules['configuration'],validated=v)
  objects.update(schema='v092-bifrost-v0140-runtime-context/v1',lossless_runtime_objects=True,configuration_summary={'status':'configuration-pending-complete-matrix'})
  bridge=types.SimpleNamespace(load_runtime_context=lambda *a,**kw:objects)
  actual,_=s._mixed_runtime_context(self.root,{},self.core,'f'*64,{'context_digest':'d'*64},bridge,protocol=p)
  self.assertEqual(len(actual['rows']),107);self.assertEqual(len(actual['prefix']),89)
  v['repo_root']=str(self.root.parent)
  with self.assertRaisesRegex(ValueError,'canonical contract root'):
   s._mixed_runtime_context(self.root,{},self.core,'f'*64,{'context_digest':'d'*64},bridge,protocol=p)
 def test_failed_pending_group_does_not_fallback_to_historical0131(self):
  rows=self.rows+[self.tail('bifrost-smoke','failed'),self.tail('bifrost-typescript-kernel')]
  with self.assertRaises(ValueError):s._resume_batch_summary(self.root,self.core,p,self.objects(rows))
 def test_stage_writer_rejects_global02_and_foreign_terminal_ownership(self):
  admission=types.SimpleNamespace(_write_bytes_exclusive=lambda root,path,raw:p.write_immutable_bytes(root,path,raw))
  row=self.tail('bifrost-smoke');row['attempt_id']='bifrost-smoke-attempt-02-series-02'
  (self.root/p.LEDGER_PATH).write_bytes(self.F.raw+s.canonical_json(row))
  with self.assertRaises(ValueError):s._stage_ledger(self.root,admission,self.core,1,protocol=p)
  row=self.tail('bifrost-smoke');row['process_ownership']['tracked_processes']=[]
  (self.root/p.LEDGER_PATH).write_bytes(self.F.raw+s.canonical_json(row))
  with self.assertRaises(ValueError):s._stage_ledger(self.root,admission,self.core,1,protocol=p)
  self.assertFalse((self.root/'fixture-supervisor24/stages/stage-01-ledger.jsonl').exists())
 def test_retained_group_command_denied_before_runtime_use(self):
  with patch.dict(s.os.environ,{s.FIXTURE_ENV:'1'}),patch.object(s,'_static',return_value=(p,{},self.core)),patch.object(s,'_load_admission',return_value=object()),patch.object(s,'_validate_context',side_effect=AssertionError('should not reach runtime')):
   with self.assertRaisesRegex(ValueError,'retained group'):
    s.build_group_command(self.root,s.MANIFEST_PATH,'f'*64,{},'bifrost-c-kernel',fixture_only=True)

 def test_actual_loop_stops_after_failed_smoke_before_typescript(self):
  self.failure_smoke=True;self.test_actual_run_groups_dispatches_only_two_and_keeps18_outcomes()

 def test_actual_run_groups_process_identity_failure_reaps_direct_child_and_closes_pipe(self):
  """Real Popen seam: identity failure is contained before any next group dispatch.

  The child is an explicitly task-owned sleep process, never an analyzer. The
  test patches only admission/graph/receipt I/O while exercising run_groups,
  real subprocess.Popen, direct-child bounded reap, and descriptor closure.
  """
  core=self.core;groups=p.dispatch_groups(core);manifest={'core_identity':{'path':'fixture-core','sha256':'f'*64},'execution_admission_slots':{g:{'attempt_id':p._attempt_id(g),'admission_path':f'fixture-supervisor24/{g}/admission.json','phase_gate_path':f'fixture-supervisor24/{g}/phase.json','completion_path':f'fixture-supervisor24/{g}/completion.json'} for g in groups}}
  stages=[];build_calls=[];opened=[]
  def put(root,path,raw):return p.write_immutable_bytes(root,path,raw)
  def simple_ref(*args,**kwargs):return {'path':'fixture-control','sha256':'e'*64}
  bundle={'parent':simple_ref(),'groups':{g:simple_ref() for g in groups}}
  admission=types.SimpleNamespace(validate_authorization_bundle=lambda *a,**kw:bundle,admit_parent=simple_ref,admit_group=simple_ref,write_phase_gate=simple_ref,_write_bytes_exclusive=put,write_completion=lambda *a,**kw:(simple_ref(),kw['successor_stage']))
  loaders=types.SimpleNamespace(PRODUCTION_MODULE_NAMES={},scoped_runtime_loaders=lambda *a,**kw:contextlib.nullcontext())
  graph=types.SimpleNamespace(module=lambda n:loaders if n=='runtime_loaders24' else object())
  def make_stage(root,core,manifest,index,*args,**kwargs):
   rows=[json.loads(line) for line in (root/p.LEDGER_PATH).read_bytes().splitlines()];objects=self.objects(rows)
   stage=types.SimpleNamespace(identity=types.SimpleNamespace(index=index),runtime=types.SimpleNamespace(objects=objects));stages.append(index);return stage
  bridge=types.SimpleNamespace(prepare_graph=lambda *a,**kw:graph,_core_graph_inputs=lambda c:{},capture_lock=lambda *a:object(),create_parent_stage=make_stage,assert_stage_current=lambda *a:None,runtime_objects=lambda stage:stage.runtime)
  parent_pid=os.getpid();process_calls=[];child_holder=[]
  def process(pid):
   if pid==parent_pid:return {'birth_identity':'fixture-parent-birth'}
   process_calls.append(pid);raise s.Supervisor24Error('synthetic birth probe failure')
  original_open=s._open_child_stage_identity_pipe
  def open_pipe():
   value=original_open();opened.append(value);return value
  def build_command(root,m,sha,c,g,**kw):
   fd=kw['child_stage_witness_fd'];token=kw['child_stage_witness_token'];build_calls.append({'group':g,'fd':fd,'token':token,'context_path':kw['context_path']})
   argv=[sys.executable,'-c','import time; time.sleep(60)', '--bridge-context',kw['context_path'], '--child-stage-witness-fd',str(fd), '--child-stage-witness-token',token]
   return {'argv':argv,'environment':dict(os.environ)}
  lock=(self.root/'fixture-lock').open('a+b');self.addCleanup(lock.close)
  patches={'_static':lambda *a:(p,manifest,core),'_load_admission':lambda *a:admission,'_load_bridge':lambda *a:bridge,'_lock_target':lambda *a:self.root/'fixture-lock','_lock_fd':lambda *a:contextlib.nullcontext(lock),'_process':process,'raw_permit':lambda *a,**kw:{},'_write_raw_permit':simple_ref,'_stage_receipt':simple_ref,'build_group_command':build_command,'_open_child_stage_identity_pipe':open_pipe}
  with contextlib.ExitStack() as stack:
   stack.enter_context(patch.dict(s.os.environ,{s.FIXTURE_ENV:'1'}))
   for name,value in patches.items():stack.enter_context(patch.object(s,name,value))
   with self.assertRaises(s.Supervisor24Error):
    s.run_groups(self.root,s.MANIFEST_PATH,'f'*64,None,None,None,{},fixture_only=True,authorization_bundle_ref=simple_ref(),authorization_bundle_sha256='e'*64)
  self.assertEqual(len(process_calls),1)
  self.assertEqual(len(build_calls),1)
  self.assertEqual(build_calls[0]['group'],groups[0])
  self.assertEqual(stages,[0])
  self.assertEqual(len(opened),1)
  for fd in opened[0]:
   with self.assertRaises(OSError):os.fstat(fd)
  self.assertFalse((self.root/'fixture-supervisor24/batch-stop-00.json').read_bytes()==b'')
  self.assertTrue(all(not (self.root/f'reports/releases/v0.9.2/attempts/{p._attempt_id(g)}').exists() for g in groups))

 def test_actual_unidentified_reap_escalates_term_to_kill_with_direct_child_only(self):
  # Tiny task-owned child; this exercises the real Popen fallback without a
  # process-group or descendant kill when the child ignores SIGTERM.
  child=subprocess.Popen([sys.executable,'-c',
                          'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'],
                         start_new_session=True)
  try:
   __import__('time').sleep(0.1)
   result=s._bounded_reap_unidentified_child(child,term_seconds=0.05,kill_seconds=0.05)
   self.assertEqual(result['status'],'reaped')
   self.assertTrue(result['term_sent']);self.assertTrue(result['kill_sent'])
   self.assertEqual(result['signal_scope'],'popen-owned-direct-child-only')
   self.assertEqual(result['descendant_containment'],'unknown')
   self.assertIsNotNone(child.poll())
  finally:
   if child.poll() is None:child.kill();child.wait(timeout=2)


if __name__=='__main__':unittest.main()
