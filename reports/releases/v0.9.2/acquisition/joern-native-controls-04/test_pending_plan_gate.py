"""Actual frozen pending validator, real files/runtime hashes, zero dispatch.

Positive uses actual source candidate. Negative plan bytes are an explicitly
scoped read seam; all unrelated bound reads and validator bodies stay real.
Existing lifecycle tests separately disclose their synthetic schema-gate seam.
"""
from pathlib import Path
import contextlib
import copy
import hashlib
import json
import subprocess
import sys
import time
import types
import unittest
from unittest import mock
import native_qualifier as n

ROOT=n.ROOT

class RealPendingPlanGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observer=n.load(ROOT,n.OBSERVER,'_native_schema_actual_test')
        cls.old=cls.observer.load_original(ROOT)
        cls.runner=cls.old._load_runner(ROOT)
        cls.cfg={'pending_plan':n.PLAN}
        cls.plan=n.document(ROOT,n.PLAN)

    @contextlib.contextmanager
    def no_dispatch(self):
        with mock.patch.object(subprocess,'Popen',side_effect=AssertionError('unexpected process dispatch')) as popen:
            yield popen
            self.assertEqual(popen.call_count,0)

    def test_actual_source_pending_positive_reaches_full_return_and_restores(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        import joern_normal_runner_v092 as canonical
        canonical_path=canonical.EXECUTION_PLAN_PATH
        common=self.runner.common
        prior_cache=dict(common._PRIVATE_ENGINES)
        prior_loader=common._load_private_module
        private_before={k:v for k,v in sys.modules.items() if k.startswith('_dfb_common_v2_joern_')}
        observed=set()
        def profile(frame,event,arg):
            if event=='call' and frame.f_code.co_filename.endswith('joern_normal_runner_v092.py'):
                observed.add(frame.f_code.co_name)
        before=sys.getprofile()
        try:
            sys.setprofile(profile)
            with self.no_dispatch():
                result=n.validate_pending_plan(ROOT,self.cfg,self.observer)
        finally:sys.setprofile(before)
        self.assertTrue(result['full_validator_returned'])
        self.assertEqual(result['cases'],108)
        self.assertEqual(result['status'],'qualification-pending')
        self.assertIsNone(result['fresh_qualification'])
        self.assertEqual(canonical.EXECUTION_PLAN_PATH,canonical_path)
        self.assertEqual(common._PRIVATE_ENGINES,prior_cache)
        self.assertIs(common._load_private_module,prior_loader)
        self.assertEqual({k:v for k,v in sys.modules.items() if k.startswith('_dfb_common_v2_joern_')},private_before)
        self.assertTrue({'validate_plan','_validate_control_plan','_check_runtime','_engine'} <= observed,observed)
        self.assertEqual(n.document(ROOT,n.PLAN),self.plan)

    @contextlib.contextmanager
    def altered_plan(self,change):
        candidate=copy.deepcopy(self.plan)
        change(candidate)
        actual_read=self.runner.read
        selected=ROOT/n.PLAN['path']
        def read(path):
            return candidate if Path(path)==selected else actual_read(path)
        old_path=self.runner.EXECUTION_PLAN_PATH
        self.runner.EXECUTION_PLAN_PATH=n.PLAN['path']
        try:
            with mock.patch.object(self.runner,'read',side_effect=read),self.no_dispatch():yield candidate
        finally:self.runner.EXECUTION_PLAN_PATH=old_path

    def test_actual_registration_near_misses_rejected_without_execution(self):
        for stamp in [1792947417.994006,True,'1792947417',None,int(time.time())+3600]:
            with self.subTest(stamp=stamp),self.altered_plan(lambda p:p.update(registered_at_unix_seconds=stamp)):
                with self.assertRaisesRegex(ValueError,'registered before execution'):
                    self.runner.validate_plan(ROOT,n.PLAN['path'],allow_qualification_pending=True)

    def test_actual_same_second_registration_rejects(self):
        stamp=self.plan['registered_at_unix_seconds']
        # Only the clock is a negative-fixture seam; the real strict comparison
        # must reject equality. The actual positive never substitutes time.
        with self.altered_plan(lambda p:p.update(registered_at_unix_seconds=stamp)),mock.patch.object(self.runner.time,'time',return_value=stamp):
            with self.assertRaisesRegex(ValueError,'registered before execution'):
                self.runner.validate_plan(ROOT,n.PLAN['path'],allow_qualification_pending=True)

    def test_actual_original04_float_reproduces_exact_failure(self):
        relative='reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-04/pending-execution-plan-01.json'
        old=self.runner.EXECUTION_PLAN_PATH
        try:
            self.runner.EXECUTION_PLAN_PATH=relative
            with self.no_dispatch(),self.assertRaisesRegex(ValueError,'registered before execution'):
                self.runner.validate_plan(ROOT,relative,allow_qualification_pending=True)
        finally:self.runner.EXECUTION_PLAN_PATH=old

    def test_actual_wrong_mode_and_projection_reject(self):
        for fields,error in [({'status':'execution-eligible'},'status'),({'qualification_control_projection_sha256':'0'*64},'projection')]:
            with self.subTest(fields=fields),self.altered_plan(lambda p:p.update(fields)):
                with self.assertRaisesRegex(ValueError,error):
                    self.runner.validate_plan(ROOT,n.PLAN['path'],allow_qualification_pending=True)

    def test_actual_late_query_missing_after_runtime_checks(self):
        original=Path.is_file
        selected=ROOT/self.plan['query_root']/'query.sc'
        reached=[]
        runtime=self.runner._check_runtime
        def checked(*args):
            value=runtime(*args);reached.append('runtime-complete');return value
        old=self.runner.EXECUTION_PLAN_PATH
        try:
            self.runner.EXECUTION_PLAN_PATH=n.PLAN['path']
            with self.no_dispatch(),mock.patch.object(self.runner,'_check_runtime',side_effect=checked),mock.patch.object(Path,'is_file',lambda p:False if p==selected else original(p)):
                with self.assertRaisesRegex(ValueError,'missing or escaped evidence file'):
                    self.runner.validate_plan(ROOT,n.PLAN['path'],allow_qualification_pending=True)
        finally:self.runner.EXECUTION_PLAN_PATH=old
        self.assertEqual(reached,['runtime-complete'])

    def test_actual_prelaunch_paths_reject_failed04_before_popen(self):
        ref={'path':'reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-04/pending-execution-plan-01.json',
             'sha256':'08ef4108097f399732ed84b4d81fa46fbf869edafaebb79fb156785cc4888888'}
        cfg={'pending_plan':ref,'observer':n.OBSERVER}
        # Upstream request/review authority is fixture-only here. The actual
        # bootstrap/parent body and real pending validator reject before launch.
        for function in (n.bootstrap,n.run_parent):
            with self.subTest(function=function.__name__),mock.patch.object(n,'PLAN',ref),mock.patch.object(n,'validate_request',return_value={}),mock.patch.object(n,'validate_review'),self.no_dispatch():
                with self.assertRaisesRegex(ValueError,'registered before execution'):
                    function(ROOT,cfg,{}, {})

    def test_worker_gate_precedes_controls_and_launch_gates_precede_popen(self):
        import ast
        tree=ast.parse(Path(n.__file__).read_text())
        for name in ('bootstrap','run_parent'):
            f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
            calls=[(x.lineno,ast.unparse(x.func)) for x in ast.walk(f) if isinstance(x,ast.Call)]
            gate=min(line for line,callee in calls if callee=='pending_plan_preflight')
            popen=min(line for line,callee in calls if callee in {'subprocess.Popen', 'controller.subprocess.Popen', 'spawn_owned', 'supervise'})
            self.assertLess(gate,popen)
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_run_worker_body')
        calls=[(x.lineno,ast.unparse(x.func)) for x in ast.walk(f) if isinstance(x,ast.Call)]
        self.assertLess(min(line for line,c in calls if c=='validate_pending_plan'),min(line for line,c in calls if c=='observer.controls'))

if __name__=='__main__':unittest.main()
