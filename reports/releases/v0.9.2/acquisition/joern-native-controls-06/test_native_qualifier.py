"""Harmless actual wrapper/body tests, never native controls or an analyzer.

Fixture I/O supplies source/109ledger/review/resource/process-table observations.
Real immutable writers, retained cleanup functions, phase parser/state machine,
existing flock handoff and actual DiskGuard API execute. Tiny owned Python child
commands are the only processes launched; their source is explicit below.
"""
import contextlib
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading
import types
import unittest
from unittest import mock

import native_qualifier as n

REPO=n.ROOT


def load_path(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='joern-native-qualifier-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()

    def artifact(self,path,value,raw=None):
        p=self.root/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(n.canonical(value) if raw is None else raw)
        return {'path':path,'sha256':n.sha(p.read_bytes())}

    def fixture(self):
        plan=json.loads((REPO/n.PLAN['path']).read_bytes())
        control=json.loads((REPO/plan['qualification_control_plan']['path']).read_bytes())
        control_ref=self.artifact('inputs/control.json',control)
        plan['qualification_control_plan']=control_ref
        evidence_ref=self.artifact('inputs/native-evidence.json', {'fixture': True})
        for index, case in enumerate(plan['cases'].values()):
            if 'decision' in case:
                case['decision']=self.artifact('inputs/decision-'+str(index)+'.json',{'evidence':[evidence_ref]})
        plan['configurations']={'joern-current108': [evidence_ref]}
        plan_ref=self.artifact('inputs/plan.json',plan)
        observer=self.artifact('inputs/observer.py',{},raw=b'# fixture source only\n')
        ledger=self.artifact('inputs/ledger.jsonl',{},raw=b''.join(n.canonical({'status':'completed' if i<103 else 'failed'}) for i in range(109)))
        cfg={'schema':'v092-joern-native-control-request/v1','expected_head':'1'*40,
             'ledger':ledger,'observer':observer,'pending_plan':plan_ref,'control_plan':control_ref,
             'namespace':'reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-01'}
        for key in ('evidence','agent_jar','agent_source','design','source_review','decision_review','authority'):
            cfg[key]=self.artifact('inputs/'+key+'.json',{'status':'approved','automatic_retry':False,'publication_hold':True})
        cfg['tool_refs']={k:self.artifact('inputs/'+k+'.py',{},raw=b'# fixture source\n') for k in ('wrapper','resources')}
        cfg['source_refs']=[cfg[k] for k in ('observer','pending_plan','control_plan','evidence','agent_jar','agent_source')]+list(cfg['tool_refs'].values())
        runtime=self.artifact('inputs/runtime.py', {}, raw=b'# fixture runtime only\n')
        process=self.artifact('scripts/swift_v2_process.py', {}, raw=b'# fixture process only\n')
        inherited=self.artifact('inputs/inherited.json', {'fixture': 'inherited'})
        contract=self.artifact('inputs/contract.json', {'source_inputs':[{**inherited,'role':'release-input'}]})
        self.core_ref=self.artifact('inputs/core.json', {'contract':contract, 'source_inputs':[{**inherited,'role':'release-input'}], 'runtime_module_graph':{'fixture-role-'+str(i):runtime for i in range(88)}})
        cfg['source_refs'] += [cfg[k] for k in ('design','source_review','decision_review','authority')]
        cfg['source_refs'] += [self.core_ref,contract,runtime,process,inherited,evidence_ref]
        cfg['source_refs'] += [c['decision'] for c in plan['cases'].values() if 'decision' in c]
        return cfg,plan

    @contextlib.contextmanager
    def fixture_bindings(self,cfg):
        # Only fixture root and fixture immutable reference anchors differ;
        # tests are not actual source qualification or approval evidence.
        with mock.patch.multiple(n,ROOT=self.root,OBSERVER=cfg['observer'],PLAN=cfg['pending_plan'],LEDGER=cfg['ledger'],CORE=self.core_ref):
            yield

    def test_pending_plan_positive_without_future_controls_or_eligible_plan(self):
        cfg,plan=self.fixture()
        with self.fixture_bindings(cfg):
            value=n.validate_request(self.root,cfg,check_git=False)
        self.assertEqual(value['ledger_rows'],109)
        self.assertFalse(value['plan']['execution_eligible'])
        self.assertIsNone(value['plan']['fresh_qualification'])
        self.assertNotIn('eligible_plan',cfg)

    def test_unknown_missing_schema_and_unbound_source_deny(self):
        cfg,plan=self.fixture()
        for mutate in (lambda c:c.update(extra=1),lambda c:c.pop('authority'),lambda c:c.update(schema='foreign'),lambda c:c['source_refs'].pop()):
            bad=copy.deepcopy(cfg);mutate(bad)
            with self.fixture_bindings(cfg),self.assertRaises(ValueError):n.validate_request(self.root,bad,check_git=False)

    def test_env_real_derived_guarded_markers_and_near_misses(self):
        cfg,plan=self.fixture()
        expected=n.expected_environment(self.root,cfg,plan)
        n.validate_environment(expected,expected)
        for key in ('DATAFLOWBENCH_V092_RELEASE_EXECUTION','DATAFLOWBENCH_V092_QUALIFICATION','JAVA_HOME','JAVA_OPTS','LC_ALL','CLASSPATH'):
            bad=dict(expected);bad[key]='foreign'
            with self.assertRaises(ValueError):n.validate_environment(bad,expected)
        with self.assertRaises(ValueError):n.validate_environment({**expected,'PYTHONPATH':'foreign'},expected)

    def test_exact_review_binds_request_wrapper_and_all_dependencies(self):
        cfg,plan=self.fixture();request={'path':'request.json','sha256':'2'*64}
        keys={'request_sha256':request['sha256'],'wrapper_sha256':cfg['tool_refs']['wrapper']['sha256'],'resources_sha256':cfg['tool_refs']['resources']['sha256'],'observer_sha256':cfg['observer']['sha256'],'pending_plan_sha256':cfg['pending_plan']['sha256'],'ledger_sha256':cfg['ledger']['sha256'],'source_head':cfg['expected_head']}
        review={'status':'approved-for-native-control-qualification-only','automatic_retry':False,'bindings':keys}
        ref=self.artifact('review.json',review);n.validate_review(self.root,ref,request,cfg)
        for key in keys:
            bad=copy.deepcopy(review);bad['bindings'][key]='0'*len(keys[key])
            ref=self.artifact('bad-review.json',bad)
            with self.assertRaises(ValueError):n.validate_review(self.root,ref,request,cfg)

    def test_stable_hash_symlink_and_append_only_writer(self):
        ref=self.artifact('source.json',{'a':1});n.stable(self.root,ref)
        (self.root/'source.json').write_bytes(b'changed')
        with self.assertRaises(ValueError):n.stable(self.root,ref)
        alias=self.root/'alias';alias.symlink_to(self.root/'source.json')
        with self.assertRaises(ValueError):n.stable(self.root,{'path':'alias','sha256':n.sha(b'changed')})
        p=self.root/'out.json';n.immutable(p,{'a':1})
        with self.assertRaises(FileExistsError):n.immutable(p,{'a':1})

    def test_real_lock_handoff_uses_same_descriptor_no_reacquisition_race(self):
        helper=load_path(Path(n.__file__).with_name('retained_resources.py'),'fixture_resource_lock')
        lock=self.root/'lock';lock.write_bytes(b'')
        with mock.patch.object(n,'LOCK',lock),helper.observe_existing_lock(lock) as held:
            with n.held_lock(helper,held['fd']) as received:
                self.assertEqual(received['ino'],held['ino'])
                self.assertEqual(received['fd'],held['fd'])
                os.fstat(held['fd'])
        fd=os.open(lock,os.O_RDONLY)
        try:
            with mock.patch.object(n,'LOCK',lock),self.assertRaises(ValueError):
                with n.held_lock(helper,fd):pass
        finally:os.close(fd)

    def test_bootstrap_gate_real_pipe_positive_wrongtoken_and_eof(self):
        for payload,good in (({'token':'x','request_sha256':'a'},True),({'token':'foreign','request_sha256':'a'},False),(None,False)):
            r,w=os.pipe()
            if payload is not None:os.write(w,n.canonical(payload))
            os.close(w)
            if good:n.bootstrap_gate(r,'x','a')
            else:
                with self.assertRaises(ValueError):n.bootstrap_gate(r,'x','a')
            with self.assertRaises(OSError):os.fstat(r)

    def test_phase_parser_rejects_token_birth_unknown_fields_and_future_clock(self):
        for changes in ({},{'token':'bad'},{'birth_identity':'bad'},{'extra':1},{'observed_monotonic':1000}):
            r,w=os.pipe();frame={'token':'x','pid':123,'birth_identity':'b','phase':'ready','observed_monotonic':1.0};frame.update(changes)
            os.write(w,n.canonical(frame));os.close(w)
            try:
                if not changes:self.assertEqual(n.consume_frames(r,b'',{'token':'x','pid':123,'birth_identity':'b'},observed=2)[1][0]['phase'],'ready')
                else:
                    with self.assertRaises(ValueError):n.consume_frames(r,b'',{'token':'x','pid':123,'birth_identity':'b'},observed=2)
            finally:os.close(r)

    def controller(self):
        m=load_path(REPO/'reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py','fixture_retained_supervisor_'+str(time.time_ns()))
        proc=load_path(REPO/'scripts/swift_v2_process.py','fixture_swift_process_'+str(time.time_ns()))
        # Sandbox process-table I/O seam: expose only the exact owned direct
        # child. Real native start identities and retained cleanup run.
        m._birth=lambda pid:proc.start_identity(pid,None) or (_ for _ in ()).throw(ValueError('gone'))
        m._process=lambda pid:{'pid':pid,'birth_identity':m._birth(pid)}
        proc.process_table=lambda:{p:(os.getpid(),proc.start_identity(p,None),'S') for p in self.owned if proc.start_identity(p,None) is not None}
        return m,proc

    def tiny(self,*,mode='ok',resource_error=False,birth_error=False,pgid_wrong=False):
        self.owned=[];controller,proc=self.controller()
        executor=types.SimpleNamespace(_process_table=lambda:'',_contenders=lambda t:[])
        samples=[]
        def sample(**kw):
            samples.append(kw)
            if resource_error:raise ValueError('fixture resource exhausted')
        resources=types.SimpleNamespace(sample=sample)
        r,w=os.pipe();lock=self.root/'flock';lock.write_bytes(b'');fd=os.open(lock,os.O_RDONLY)
        token='fixture-token'
        script="""import os,time,json,sys
sys.path.insert(0,sys.argv[1])
import swift_v2_process as p
fd=int(sys.argv[2]);token=sys.argv[3]
for phase in ('ready','controls-started','controls-returned'):
 os.write(fd,(json.dumps({'token':token,'pid':os.getpid(),'birth_identity':p.start_identity(os.getpid(),None),'phase':phase,'observed_monotonic':time.monotonic()})+'\\n').encode())
 time.sleep(.01)
os.close(fd)
"""
        if mode=='nonzero':script+='raise SystemExit(7)\n'
        elif mode=='sleep':script+='time.sleep(60)\n'
        argv=[sys.executable,'-B','-E','-c',script,str(REPO/'scripts'),str(w),token]
        real_popen=subprocess.Popen
        def spawn(*args,**kwargs):
            child=real_popen(*args,**kwargs);self.owned.append(child.pid);return child
        if birth_error:controller._process=lambda pid:(_ for _ in ()).throw(ValueError('fixture post-Popen birth failure'))
        with (self.root/'stdout').open('wb') as out,(self.root/'stderr').open('wb') as err,contextlib.ExitStack() as stack:
            if pgid_wrong:stack.enter_context(mock.patch.object(os,'getpgid',side_effect=ProcessLookupError))
            result=n.supervise(argv,root=self.root,env={'PATH':os.environ['PATH'],'LC_ALL':'C'},stdout=out,stderr=err,lock_fd=fd,request_sha='f'*64,controller=controller,proc=proc,resources=resources,executor=executor,namespace=self.root,token=token,read_fd=r,write_fd=w,popen=spawn)
        os.close(fd)
        for pid in self.owned:self.assertIsNone(proc.start_identity(pid,None))
        with self.assertRaises(OSError):os.fstat(r)
        return result,samples

    def test_real_tiny_child_phase_positive_and_reaped(self):
        result,samples=self.tiny()
        self.assertIsNone(result['failure'],result)
        self.assertEqual([p['phase'] for p in result['phases']],['ready','controls-started','controls-returned'])
        self.assertTrue(result['cleanup']['coordinator_reaped'])
        self.assertTrue(samples)
        self.assertFalse(result['qualification_inferred'])

    def test_real_tiny_child_nonzero_never_becomes_qualification(self):
        result,_=self.tiny(mode='nonzero')
        self.assertIsNotNone(result['failure'])
        self.assertFalse(result['qualification_inferred'])

    def test_real_tiny_child_resource_stop_reaps_only_owned(self):
        result,_=self.tiny(mode='sleep',resource_error=True)
        self.assertIn('resource exhausted',result['failure']['message'])
        self.assertTrue(result['cleanup']['coordinator_reaped'])

    def test_real_post_popen_unknown_birth_direct_cleanup(self):
        result,_=self.tiny(mode='sleep',birth_error=True)
        self.assertIn('birth failure',result['failure']['message'])
        self.assertEqual(result['cleanup']['signal_scope'],'popen-owned-direct-child-only')
        self.assertTrue(result['cleanup']['coordinator_reaped'])

    def test_real_post_popen_unknown_group_direct_cleanup(self):
        result,_=self.tiny(mode='sleep',resource_error=True,pgid_wrong=True)
        self.assertTrue(result['cleanup']['coordinator_reaped'])
        self.assertEqual(result['cleanup']['signal_scope'],'popen-owned-direct-child-only')

    def test_actual_diskguard_api_and_one_byte_over_caps(self):
        disk=load_path(REPO/'scripts/v092_disk_guard.py','fixture_actual_disk_guard')
        helper=load_path(Path(n.__file__).with_name('retained_resources.py'),'fixture_resource_paths')
        class Graph:
            def module(self,name):return self.values[name]
        graph=Graph();cfg={'namespace':'capture'};core={};contract={'source_inputs':[]}
        executor=types.SimpleNamespace(EXECUTION_ROOT=Path('groups'),SNAPSHOT_DIRECTORIES=(),SNAPSHOT_FILES=())
        authority={'authorized_change':{'after_bytes':30*n.GIB}}
        admission=types.SimpleNamespace(_live_resources=lambda root,core:{'resource_policy':{'minimum_free_gib':127}})
        protocol=types.SimpleNamespace(validate_working_cap=lambda root,core:authority,_relative=lambda value,label:Path(value))
        resource=object.__new__(n.Resources)
        resource.root=self.root;resource.cfg=cfg;resource.core=core;resource.graph=graph
        resource.admission=admission;resource.protocol=protocol;resource.executor=executor;resource.contract=contract
        resource.paths={k:[self.root/k] for k in ('working','scratch','retention')}
        resource.guard=disk.DiskGuard(launch_floor_bytes=127*n.GIB,protected_reserve_bytes=40*n.GIB,stop_margin_bytes=8*n.GIB,stop_floor_bytes=48*n.GIB,scratch_ceiling_bytes=24*n.GIB,retention_ceiling_bytes=24*n.GIB,working_ceiling_bytes=30*n.GIB)
        with mock.patch.object(disk.shutil,'disk_usage',return_value=types.SimpleNamespace(free=200*n.GIB)):
            self.assertEqual(resource.sample(launch=False)['working_cap_bytes'],30*n.GIB)
            with mock.patch.object(resource.guard,'logical_size',side_effect=lambda paths:31*n.GIB if list(paths)==resource.paths['working'] else 0):
                with self.assertRaises(disk.DiskGuardError):resource.sample(launch=False)
            with mock.patch.object(resource.guard,'_disk_usage',return_value=types.SimpleNamespace(free=125*n.GIB-1)):
                with self.assertRaises(ValueError):resource.sample(launch=False)


    def controlled_wait(self, stamps, observed, *, exit_race=False):
        r, w = os.pipe()
        lock = self.root / 'clock-lock'
        lock.write_bytes(b'')
        lock_fd = os.open(lock, os.O_RDONLY)
        frames = [{'token': 'clock-token', 'pid': 999999, 'birth_identity': 'clock-birth',
                   'phase': name, 'observed_monotonic': stamp}
                  for name, stamp in zip(('ready', 'controls-started', 'controls-returned'), stamps)]
        def publish():
            for frame in frames:
                os.write(w, n.canonical(frame))
        # Duplicate the child write descriptor just as pass_fds would preserve
        # it across the parent's close. No process is started in clock fixtures.
        child_writer = os.dup(w)
        def publish_child():
            for frame in frames:
                os.write(child_writer, n.canonical(frame))
        class Child:
            pid = 999999
            returncode = 0
            def poll(self): return 0
        if not exit_race:
            publish()
        controller = types.SimpleNamespace(
            _process=lambda pid: {'pid':pid, 'birth_identity':'clock-birth'},
            _bounded_reap_unidentified_child=lambda child: {'coordinator_reaped':True},
            _hashed_bifrost_contenders=lambda table: [])
        proc = types.SimpleNamespace(start_identity=lambda pid, fallback:'native-birth',
            process_table=lambda:{}, descendants=lambda table, tracked:tracked,
            active=lambda table, tracked:[])
        executor = types.SimpleNamespace(_process_table=lambda:'', _contenders=lambda table:[])
        clock = iter([0.0] + [float(observed)] * 20)
        resources = types.SimpleNamespace(sample=lambda **kwargs:publish_child() if exit_race else None)
        try:
            result = n.supervise(['fixture-only'], root=self.root, env={}, stdout=None, stderr=None,
                lock_fd=lock_fd, request_sha='1'*64, controller=controller, proc=proc,
                resources=resources, executor=executor, namespace=self.root,
                token='clock-token', read_fd=r, write_fd=w, popen=lambda *a,**k:Child(),
                clock=lambda:next(clock))
        finally:
            os.close(child_writer)
            os.close(lock_fd)
        return result

    def test_real_supervise_phase_deadlines_and_recording_tail(self):
        result = self.controlled_wait([1,2,3],4)
        self.assertIsNone(result['failure'], result)
        self.assertEqual(len(result['phases']),3)

    def test_real_supervise_handshake120_near_miss(self):
        self.assertIn('late or reversed',self.controlled_wait([121,122,123],124)['failure']['message'])

    def test_real_supervise_startup600_near_miss(self):
        self.assertIn('late or reversed',self.controlled_wait([1,601,602],603)['failure']['message'])

    def test_real_supervise_absolute_startup600_plus_controls900_near_miss(self):
        self.assertIn('late or reversed',self.controlled_wait([1,2,1501],1502)['failure']['message'])

    def test_real_supervise_tail240_near_miss(self):
        self.assertIn('late native',self.controlled_wait([1,2,3],244)['failure']['message'])

    def test_real_supervise_exit_race_drains_actual_pipe_all_phases(self):
        result = self.controlled_wait([1,2,3],4,exit_race=True)
        self.assertIsNone(result['failure'],result)
        self.assertEqual(len(result['phases']),3)


    def worker_fixture(self, *, bad_environment=False, actual_environment=False, import_mutation=False):
        cfg, plan = self.fixture()
        cfg['tool_refs']['wrapper'] = self.artifact('inputs/current-wrapper.py', {}, raw=Path(n.__file__).read_bytes())
        helper = load_path(Path(n.__file__).with_name('retained_resources.py'), 'worker_real_lock_helper')
        # Load retained source only. Both original guard bodies execute; the
        # controls callback is an explicit engine-I/O seam, never an analyzer.
        scripts = str(REPO / 'scripts')
        sys.path.insert(0, scripts)
        try:
            runner = load_path(REPO / 'scripts/joern_normal_runner_v092.py', 'worker_retained_runner_guard')
        finally:
            sys.path.remove(scripts)
        request = {'path':'request.json', 'sha256':'3'*64}
        lock = self.root / 'worker-lock'
        lock.write_bytes(b'')
        parent_pid = os.getppid()
        base = cfg['namespace']
        self.artifact(base + '/parent-started.json', {
            'request':request, 'review':{'path':'review.json','sha256':'4'*64}, 'source_head':cfg['expected_head'], 'ledger':cfg['ledger'],
            'process':{'pid':parent_pid,'birth_identity':'parent-fixture-birth'},
            'argv':[n.PYTHON, *sys.orig_argv[1:]],
            'interpreter_identity':n.validate_worker_argv([n.PYTHON,*sys.orig_argv[1:]],list(sys.orig_argv))})
        called=[]
        def controls(root, output, **kwargs):
            runner._require_launch_guard('joern-swift-common108', qualification=True)
            runner._require_launch_guard('joern-swift-common108')
            called.append((output, kwargs))
            return {'run':{'records':[{}]*12,'phase_invocation_count':36},
                    'startup_observation':{'qualification_safe':True}}
        old = types.SimpleNamespace(validate_bootstrap_inputs=lambda *a,**k:{'new_plan':plan})
        observer = types.SimpleNamespace(load_original=lambda root:old, controls=controls)
        controller = types.SimpleNamespace(_birth=lambda pid:'parent-fixture-birth',
            _process=lambda pid:{'pid':pid,'birth_identity':'worker-fixture-birth'})
        original_load = n.load
        def selected_load(root,ref,prefix):
            if prefix == '_native_observer06':
                if import_mutation:os.environ['FOREIGN_IMPORT_MUTATION']='1'
                return observer
            if prefix == '_native_controller':return controller
            return original_load(root,ref,prefix)
        env = n.expected_environment(self.root,cfg,plan)
        if bad_environment:env['LC_ALL']='foreign-environment'
        r,w=os.pipe()
        core={'runtime_module_graph':{'supervisor24':{'path':'fixture-controller','sha256':'0'*64}}}
        original_document=n.document
        with mock.patch.object(n,'ROOT',self.root),mock.patch.object(n,'LOCK',lock), \
             helper.observe_existing_lock(lock) as held, \
             mock.patch.object(n,'load',side_effect=selected_load), \
             mock.patch.object(n,'validate_pending_plan',return_value={'fixture_schema_gate':True}), \
             mock.patch.object(n,'document',side_effect=lambda root,ref:core if ref==n.CORE else original_document(root,ref)), \
             (contextlib.nullcontext() if actual_environment else mock.patch.dict(os.environ,env,clear=True)):
            try:
                if bad_environment:
                    with self.assertRaisesRegex(ValueError,'worker environment differs'):
                        n.run_worker(self.root,cfg,request,lock_fd=held['fd'],witness_fd=w,
                            token='worker-token',parent_pid=parent_pid,parent_birth='parent-fixture-birth')
                else:
                    result=n.run_worker(self.root,cfg,request,lock_fd=held['fd'],witness_fd=w,
                        token='worker-token',parent_pid=parent_pid,parent_birth='parent-fixture-birth')
            finally:os.close(w)
        raw=os.read(r,16384);os.close(r)
        frames=[json.loads(line) for line in raw.splitlines()]
        if bad_environment:
            self.assertEqual(frames,[])
            self.assertEqual(called,[])
            self.assertFalse((self.root/base/'worker-invocation.json').exists())
            self.assertFalse((self.root/base/'capture').exists())
            return
        observation=json.loads((self.root/base/'worker-invocation.json').read_bytes())
        self.assertEqual(observation['actual_raw_argv'],sys.orig_argv)
        self.assertEqual(observation['environment'],env)
        self.assertEqual(observation['interpreter_identity'],observation['parent_interpreter_identity'])
        self.assertEqual([f['phase'] for f in frames],['ready','controls-started','controls-returned'])
        self.assertEqual(len(called),1)
        self.assertEqual(called[0][1]['new_plan_path'],cfg['pending_plan']['path'])
        self.assertTrue((self.root/base/'control-result.json').is_file())
        self.assertEqual(result['run']['phase_invocation_count'],36)


    def test_full_guard_thread_positive_final_scan_and_fast_parent_checks(self):
        calls=[]
        class Resource:
            def sample(self, **kw):
                time.sleep(.01)
                calls.append('full')
                return {'actual-fixture-scan':True}
            def quick_sample(self):calls.append('quick')
        monitor=n.GuardMonitor(Resource())
        monitor.check()
        result=monitor.finish(time.monotonic()+1)
        self.assertGreaterEqual(result['full_scans'],2)
        self.assertIn('quick',calls)
        self.assertFalse(monitor.thread.is_alive())

    def test_full_guard_hang_cannot_block_phase_clock_or_recording_tail(self):
        release=threading.Event()
        entered=threading.Event()
        class Resource:
            def sample(self, **kw):
                entered.set()
                release.wait(1)
                return {}
            def quick_sample(self):pass
        monitor=n.GuardMonitor(Resource())
        self.assertTrue(entered.wait(1))
        started=time.monotonic()
        try:
            with self.assertRaisesRegex(ValueError,'recording tail'):
                monitor.finish(started+.02)
            self.assertLess(time.monotonic()-started,.3)
        finally:
            release.set()
            self.assertTrue(monitor.cancel(time.monotonic()+1))

    def test_full_guard_error_is_not_accepted_as_resource_compliance(self):
        entered=threading.Event()
        class Resource:
            def sample(self, **kw):
                entered.set()
                raise ValueError('fixture full inventory cap violation')
            def quick_sample(self):pass
        monitor=n.GuardMonitor(Resource())
        self.assertTrue(entered.wait(1))
        monitor.thread.join(1)
        with self.assertRaises(RuntimeError):monitor.check()
        self.assertTrue(monitor.cancel(time.monotonic()+1))

    def test_outer_combined_deadline_does_not_narrow_actual_inner900(self):
        result=self.controlled_wait([1,500,1499],1499.5)
        self.assertIsNone(result['failure'],result)
        # Actual900/75 enforcement is retained in the real runner, and exact
        # control-plan fields are checked by validate_request. This fixture
        # proves only that observer bootstrap/version overhead is not deducted
        # from that inner budget by the separate outer supervisor.


    def test_actual_bootstrap_body_preserves_lock_fd_and_releases_only_after_receipt(self):
        # Upstream request/resource/process observations are fixture I/O. The
        # actual bootstrap body, real flock, pipe, writers and FD handoff run.
        cfg,_=self.fixture()
        # fixture() already binds the retained process source
        (self.root/cfg['namespace']).parent.mkdir(parents=True)
        lock_path=self.root/'analyzer.lock';lock_path.touch()
        helper=load_path(Path(n.__file__).with_name('retained_resources.py'),'bootstrap_fixture_resources')
        processes=[];received=[]
        class Child:
            def __init__(self,pid):self.pid=pid
        def popen(argv, **kw):
            child=Child(900+len(processes));processes.append((child,argv,kw))
            if len(processes)==1:
                received.append(os.dup(kw['pass_fds'][1]))
                # The launch is serialized under the actual existing flock.
                import fcntl
                other=os.open(lock_path,os.O_RDONLY)
                try:
                    with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:os.close(other)
            return child
        controller=types.SimpleNamespace(_process=lambda pid:{'pid':pid,'birth_identity':'fixture:'+str(pid)})
        graph=types.SimpleNamespace(module=lambda role:controller if role=='supervisor24' else object())
        @contextlib.contextmanager
        def graph_scope(root, **kwargs):yield {},graph
        resources=types.SimpleNamespace(sample=lambda **kw:{'free_bytes':200*n.GIB})
        with mock.patch.multiple(n,LOCK=lock_path,modules=graph_scope), mock.patch.object(n,'pending_plan_preflight',return_value={'fixture_schema_gate':True}), mock.patch.object(n,'validate_request',return_value={'environment':{}}), mock.patch.object(n,'validate_review'), mock.patch.object(n,'stable',return_value=Path(n.__file__).read_bytes()), mock.patch.object(n,'load',side_effect=lambda root,ref,name:helper if 'resources' in name else object()), mock.patch.object(n,'Resources',return_value=resources), mock.patch.object(n,'contenders',return_value=[]), mock.patch.object(n.subprocess,'Popen',side_effect=popen):
            value=n.bootstrap(self.root,cfg,{'path':'request','sha256':'1'*64},{'path':'review','sha256':'2'*64})
        try:frame=json.loads(os.read(received[0],4096))
        finally:os.close(received[0])
        self.assertEqual(frame['request_sha256'],'1'*64)
        self.assertEqual(value['status'],'owned-parent-started')
        self.assertFalse(value['qualification_inferred'])
        self.assertTrue((self.root/(cfg['namespace']+'-supervision')/'result.json').exists())
        self.assertEqual(processes[0][2]['pass_fds'][0],int(processes[0][1][processes[0][1].index('--lock-fd')+1]))

    def test_wrapper_and_dependency_must_be_in_committed_closure(self):
        cfg,_=self.fixture()
        for key in ('wrapper','resources'):
            changed=copy.deepcopy(cfg)
            changed['source_refs']=[r for r in changed['source_refs'] if r!=changed['tool_refs'][key]]
            with self.fixture_bindings(changed),self.assertRaisesRegex(ValueError,'committed source closure'):
                n.validate_request(self.root,changed,check_git=False)


    def test_complete_derived_closure_rejects_every_omitted_or_rebound_class(self):
        cfg,_=self.fixture()
        with self.fixture_bindings(cfg):
            required=n.required_source_closure(self.root,cfg)
            n.validate_request(self.root,cfg,check_git=False)
            for ref in required:
                changed=copy.deepcopy(cfg)
                changed['source_refs']=[r for r in changed['source_refs'] if r['path']!=ref['path']]
                with self.subTest(omitted=ref['path']),self.assertRaises(ValueError):
                    n.validate_request(self.root,changed,check_git=False)
            changed=copy.deepcopy(cfg)
            changed['source_refs'].append(changed['source_refs'][0])
            with self.assertRaisesRegex(ValueError,'duplicate'):
                n.validate_request(self.root,changed,check_git=False)
            changed=copy.deepcopy(cfg)
            changed['source_refs'][0]={'path':changed['source_refs'][0]['path'],'sha256':'0'*64}
            with self.assertRaises(ValueError):n.validate_request(self.root,changed,check_git=False)

    def test_static_actual_source_dependency_closure_reaches_local_and_dynamic_helpers(self):
        cfg,_=self.fixture()
        local=self.artifact('scripts/nested_helper.py',{},raw=b'# local import fixture\n')
        dynamic=self.artifact('scripts/dynamic_helper.py',{},raw=b'# dynamic path fixture\n')
        process=self.artifact('scripts/swift_v2_process.py',{},raw=b'import nested_helper\nPATH="scripts/dynamic_helper.py"\n')
        cfg['source_refs']=[r for r in cfg['source_refs'] if r['path']!=process['path']]+[process]
        with self.fixture_bindings(cfg):
            required={r['path']:r for r in n.required_source_closure(self.root,cfg)}
            self.assertEqual(required[local['path']],local)
            self.assertEqual(required[dynamic['path']],dynamic)
            with self.assertRaisesRegex(ValueError,'closure omitted'):
                n.validate_request(self.root,cfg,check_git=False)
            cfg['source_refs'] += [local,dynamic]
            n.validate_request(self.root,cfg,check_git=False)

    def test_supervision_sibling_in_full_and_quick_accounting_actual_resource_body(self):
        cfg,_=self.fixture()
        core={'contract':self.artifact('inputs/resource-contract.json', {'source_inputs':[]})}
        disk=types.SimpleNamespace(DiskGuard=lambda **kw:types.SimpleNamespace())
        graph=types.SimpleNamespace(module=lambda role:disk if role=='disk_guard' else object())
        helper=types.SimpleNamespace(accounting_paths=lambda *a:{'working':[], 'scratch':[], 'retention':[]})
        cfg['tool_refs']['resources']['sha256']=n.sha(Path(n.__file__).with_name('retained_resources.py').read_bytes())
        with mock.patch.object(n,'load',return_value=helper):
            resources=n.Resources(self.root,cfg,core,graph)
        sibling=self.root/(cfg['namespace']+'-supervision')
        self.assertIn(sibling,resources.paths['scratch'])
        self.assertIn(sibling,resources.paths['retention'])
        calls=[]
        resources.guard=types.SimpleNamespace(_free_bytes=lambda root:200*n.GIB,logical_size=lambda paths:0,
            check=lambda **kw:calls.append(kw) or {})
        resources.quick_sample()
        self.assertEqual({c['category'] for c in calls},{'scratch','retention'})
        self.assertTrue(all(sibling in c['paths'] for c in calls))
        def overcap(**kw):
            self.assertIn(sibling,kw['paths'])
            raise ValueError('fixture supervision exceeded same category cap')
        resources.guard.check=overcap
        with self.assertRaisesRegex(ValueError,'same category cap'):resources.quick_sample()


    def test_sibling_logs_actual_diskguard_shared_cap_one_byte_near_miss(self):
        disk=load_path(REPO/'scripts/v092_disk_guard.py','sibling_actual_diskguard')
        resource=object.__new__(n.Resources)
        resource.root=self.root;resource.cfg={'namespace':'capture'}
        resource.guard=disk.DiskGuard(launch_floor_bytes=127*n.GIB,protected_reserve_bytes=40*n.GIB,
            stop_margin_bytes=8*n.GIB,stop_floor_bytes=48*n.GIB,scratch_ceiling_bytes=10,
            retention_ceiling_bytes=10,working_ceiling_bytes=30*n.GIB,
            disk_usage=lambda path:types.SimpleNamespace(free=200*n.GIB))
        sibling=self.root/'capture-supervision';sibling.mkdir()
        log=sibling/'parent.stderr';log.write_bytes(b'1234567890')
        resource.quick_sample()
        log.write_bytes(b'12345678901')
        with self.assertRaises(disk.DiskGuardError):resource.quick_sample()

    def test_control_and_plan_fixture_refs_are_derived_from_bound_population(self):
        cfg,plan=self.fixture()
        selected=list(plan['cases'])
        control=n.document(self.root,cfg['control_plan'])
        selected+=list(control['controls'].values())
        selected=list(dict.fromkeys(selected))
        case_ref=self.artifact('cases/fixture/case.json',{'fixture':True})
        source_ref=self.artifact('cases/fixture/main.swift',{},raw=b'// fixture\n')
        pop=self.artifact('populations/fixture.json',{'cases':[{**case_ref,'id':case,'fixture_digests':[source_ref]} for case in selected]})
        plan['configurations']['joern-current108'].append(pop)
        cfg['pending_plan']=self.artifact('inputs/plan.json',plan)
        cfg['source_refs']=[r for r in cfg['source_refs'] if r['path']!=cfg['pending_plan']['path']]+[cfg['pending_plan'],pop]
        with self.fixture_bindings(cfg):
            required={r['path']:r for r in n.required_source_closure(self.root,cfg)}
            self.assertEqual(required[case_ref['path']],case_ref)
            self.assertEqual(required[source_ref['path']],source_ref)
            with self.assertRaisesRegex(ValueError,'closure omitted'):
                n.validate_request(self.root,cfg,check_git=False)
            cfg['source_refs'] += [case_ref,source_ref]
            n.validate_request(self.root,cfg,check_git=False)


    def test_real_homebrew_worker_argv_alias_positive_and_exact_argument_near_misses(self):
        # Uses the actual interpreter launched with the same configured path;
        # no worker/observer/control is dispatched.
        actual=list(sys.orig_argv)
        recorded=[n.PYTHON,*actual[1:]]
        identity=n.validate_worker_argv(recorded,actual)
        self.assertEqual(identity['raw_executable'],actual[0])
        self.assertTrue(identity['all_arguments_after_argv0_exact'])
        for changed in ([actual[0],*actual[1:],'--foreign'], ['/usr/bin/python3',*actual[1:]],
                        [str(Path(n.PYTHON).resolve().parent.parent/'Resources/Foreign.app/Python'),*actual[1:]]):
            with self.subTest(argv=changed),self.assertRaises(ValueError):n.validate_worker_argv(recorded,changed)
        with self.assertRaises(ValueError):n.validate_worker_argv(['/usr/bin/python3',*actual[1:]],actual)

    def test_actual_modules_scope_cleans_late_resource_process_imports_before_frozen_close(self):
        before=dict(sys.modules)
        with n.modules(REPO) as (core,graph):
            resource=n.load(Path(n.__file__).parent,{'path':'retained_resources.py','sha256':n.sha(Path(n.__file__).with_name('retained_resources.py').read_bytes())},'_late_actual_resource')
            process_path=REPO/'scripts/swift_v2_process.py'
            process=n.load(REPO,{'path':'scripts/swift_v2_process.py','sha256':n.sha(process_path.read_bytes())},'_late_actual_process')
            names=[resource.__name__,process.__name__]
            self.assertTrue(all(sys.modules[name] is module for name,module in zip(names,(resource,process))))
        self.assertTrue(all(name not in sys.modules for name in names))
        self.assertTrue(all(sys.modules.get(name) is module for name,module in before.items()))

    def test_actual_modules_scope_preserves_foreign_entry_and_frozen_rejection(self):
        name='_native_test_foreign_unowned'
        foreign=types.ModuleType(name)
        try:
            with self.assertRaisesRegex(Exception,'non-stdlib process-global'):
                with n.modules(REPO):sys.modules[name]=foreign
            self.assertIs(sys.modules[name],foreign)
        finally:sys.modules.pop(name,None)

    def test_scoped_loader_rejects_replaced_owned_identity_but_cleans_other_owned_entries(self):
        ref=self.artifact('loader_fixture.py',{},raw=b'VALUE=1\n')
        foreign=types.ModuleType('_fixture_replacement')
        first=second=None
        try:
            with self.assertRaisesRegex(ValueError,'registry identity changed'):
                with n.owned_module_scope():
                    first=n.load(self.root,ref,'_owned_first')
                    second=n.load(self.root,ref,'_owned_second')
                    sys.modules[second.__name__]=foreign
            self.assertNotIn(first.__name__,sys.modules)
            self.assertIs(sys.modules[second.__name__],foreign)
        finally:
            if second is not None:sys.modules.pop(second.__name__,None)

    def test_actual_module_scope_error_keeps_original_failure_after_clean_teardown(self):
        with self.assertRaisesRegex(RuntimeError,'original worker failure sentinel'):
            with n.modules(REPO):
                n.load(Path(n.__file__).parent,{'path':'retained_resources.py','sha256':n.sha(Path(n.__file__).with_name('retained_resources.py').read_bytes())},'_late_failure_resource')
                raise RuntimeError('original worker failure sentinel')


    def test_tiny_actual_python_process_combines_interpreter_and_actual_graph_late_cleanup(self):
        # Actual configured Homebrew launcher + actual modules/late loads/close.
        # No worker/control/bootstrap/admission/replay API is invoked.
        script="""import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import native_qualifier as n
identity=n.validate_worker_argv([n.PYTHON,*sys.orig_argv[1:]],list(sys.orig_argv))
with n.modules(n.ROOT):
    p=Path(n.__file__).with_name('retained_resources.py')
    resource=n.load(p.parent,{'path':p.name,'sha256':n.sha(p.read_bytes())},'_tiny_late_resource')
    p=n.ROOT/'scripts/swift_v2_process.py'
    process=n.load(n.ROOT,{'path':'scripts/swift_v2_process.py','sha256':n.sha(p.read_bytes())},'_tiny_late_process')
    names=[resource.__name__,process.__name__]
assert all(name not in sys.modules for name in names)
print(json.dumps({'interpreter':identity,'owned_late_modules_removed':True,'frozen_close_passed':True}))
"""
        result=subprocess.run([n.PYTHON,'-B','-E','-c',script,str(Path(n.__file__).parent)],
            capture_output=True,text=True,timeout=20,check=True)
        proof=json.loads(result.stdout)
        self.assertTrue(proof['owned_late_modules_removed'])
        self.assertTrue(proof['frozen_close_passed'])
        self.assertEqual(proof['interpreter']['raw_executable'],sys.orig_argv[0])

    def test_cleanup_failure_is_recorded_without_masking_original_body_failure(self):
        name='_native_test_foreign_during_failure';foreign=types.ModuleType(name)
        receipt=self.root/'module-cleanup-error.json'
        try:
            with self.assertRaisesRegex(RuntimeError,'original body error') as captured:
                with n.modules(REPO,cleanup_receipt=receipt):
                    sys.modules[name]=foreign
                    raise RuntimeError('original body error')
            self.assertIs(sys.modules[name],foreign)
            self.assertTrue(captured.exception.native_module_cleanup_errors)
            detail=json.loads(receipt.read_bytes())
            self.assertEqual(detail['original_error']['message'],'original body error')
            self.assertIn('non-stdlib process-global',detail['cleanup_errors'][0]['message'])
        finally:sys.modules.pop(name,None)

    def test_actual_recorded_worker_arguments_all_remain_exact(self):
        path=REPO/'reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-01/parent-started.json'
        recorded=json.loads(path.read_bytes())['argv']
        actual=[sys.orig_argv[0],*recorded[1:]]
        n.validate_worker_argv(recorded,actual)
        for flag in ['-B','--request-sha256','--review-sha256','--witness-fd','--lock-fd','--token','--parent-birth']:
            changed=list(actual)
            index=changed.index(flag)+(0 if flag=='-B' else 1)
            changed[index]='foreign-value'
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'arguments differ'):
                n.validate_worker_argv(recorded,changed)
        with mock.patch.object(n.sys,'executable','/usr/bin/python3'),self.assertRaisesRegex(ValueError,'interpreter differs'):
            n.validate_worker_argv(recorded,actual)


    def test_actual_worker_parent_flock_environment_and_retained_runner_guard(self):
        self.worker_fixture()

    def test_actual_worker_environment_near_miss_has_no_ready_or_control_phase(self):
        self.worker_fixture(bad_environment=True)


class FailedExecutionCleanupTests(unittest.TestCase):
    def run_failed_load(self, replace):
        with tempfile.TemporaryDirectory(prefix='native-failed-load-') as directory:
            root=Path(directory).resolve()
            path=root/'failed.py'
            source='import sys, types\n'
            if replace:
                source+="sys.modules[__name__]=types.ModuleType('foreign-replacement')\n"
            source+="raise RuntimeError('original-execution-failure')\n"
            path.write_text(source)
            ref={'path':path.name,'sha256':__import__('hashlib').sha256(path.read_bytes()).hexdigest()}
            names=set(sys.modules)
            try:
                with n.owned_module_scope():
                    with self.assertRaisesRegex(RuntimeError,'original-execution-failure') as caught:
                        n.load(root,ref,'failed_execution_test')
                added=[name for name in set(sys.modules)-names if name.startswith('failed_execution_test_')]
                if replace:
                    self.assertEqual(len(added),1)
                    self.assertEqual(sys.modules[added[0]].__name__,'foreign-replacement')
                    errors=caught.exception.native_module_cleanup_errors
                    self.assertEqual(len(errors),1)
                    self.assertIn('registry identity changed',errors[0]['message'])
                else:
                    self.assertEqual(added,[])
                    self.assertFalse(hasattr(caught.exception,'native_module_cleanup_errors'))
            finally:
                for name in set(sys.modules)-names:
                    if name.startswith('failed_execution_test_'):
                        del sys.modules[name]

    def test_failed_execution_preserves_foreign_replacement_and_primary_error(self):
        self.run_failed_load(True)

    def test_failed_execution_removes_only_exact_owned_module(self):
        self.run_failed_load(False)


class FreshDarwinWorkerEnvironmentTests(unittest.TestCase):
    def run_worker_process(self, mode):
        with tempfile.TemporaryDirectory(dir='/private/tmp',prefix='native-env-worker-') as directory:
            root=Path(directory).resolve()
            fixture=NativeTests('runTest')
            fixture.root=root
            cfg,plan=fixture.fixture()
            env=n.expected_environment(root,cfg,plan)
            self.assertEqual(env['__CF_USER_TEXT_ENCODING'],'0x1F5:0x0:0x0')
            if mode=='wrong-cf':env['__CF_USER_TEXT_ENCODING']='0x1F5:0x1:0x0'
            if mode=='extra':env['FOREIGN_EXTRA']='1'
            if mode=='changed-java':env['JAVA_OPTS']='foreign'
            script=Path(__file__).resolve().with_name('fresh_worker_probe.py')
            result=subprocess.run([n.PYTHON,'-B','-E',str(script),str(root),mode],
                                  env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            proof=json.loads(result.stdout)
            self.assertEqual(proof['mode'],mode)
            self.assertEqual(proof['ready'],mode=='positive')
            return proof

    def test_actual_fresh_darwin_worker_explicit_platform_value(self):
        self.assertTrue(self.run_worker_process('positive')['worker_receipt'])

    def test_actual_fresh_worker_wrong_platform_value_rejected(self):
        self.run_worker_process('wrong-cf')

    def test_actual_fresh_worker_arbitrary_extra_rejected(self):
        self.run_worker_process('extra')

    def test_actual_fresh_worker_changed_java_option_rejected(self):
        self.run_worker_process('changed-java')

    def test_actual_fresh_worker_import_mutation_rejected(self):
        self.run_worker_process('import-mutation')


if __name__=='__main__':unittest.main()
