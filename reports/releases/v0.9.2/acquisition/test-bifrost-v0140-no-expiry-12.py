#!/usr/bin/env python3
"""Bounded synthetic no-expiry regressions; no production execution."""
import copy
import datetime as dt
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
protocol = load('expiry08_protocol', BASE/'bifrost-v0140-replacement-12.py')
supervisor = load('expiry08_supervisor', BASE/'bifrost-v0140-supervisor-12.py')
bridge = load('expiry08_bridge', BASE/'bifrost-v0140-frozen-bridge-07.py')
checker = load('expiry08_frozenchecker', ROOT/'scripts/check-release-v092.py')

class NoExpiryTests(unittest.TestCase):
    def core(self):
        return {'original_origin_utc': protocol.ORIGIN, 'cutoff_utc': None,
                'total_wall_budget_seconds': None,
                'execution_window_authority': dict(protocol.WINDOW_AUTHORITY)}
    def test_startup_is_exact_inherited_bifrost_policy(self):
        original = load('expiry08_original07',BASE/'bifrost-v0140-replacement-07.py')
        self.assertEqual(supervisor.PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS, original.RESOURCE_POLICY['startup_seconds'])
        self.assertEqual(protocol.RESOURCE_POLICY['startup_seconds'], original.RESOURCE_POLICY['startup_seconds'])
    def test_pending_joern06_is_not_a_dependency(self):
        self.assertFalse(hasattr(bridge, 'CONTINUATION06'))
        self.assertTrue(callable(bridge._incoming_recovery))
    def test_lease_mutates_only_runtime_budget_and_expiry(self):
        before=self.validated()
        runtime=supervisor._dispatch_lease(before,'bifrost-c-kernel')
        actual=copy.deepcopy(runtime['plan'])
        actual['total_wall_budget_seconds']=before['plan']['total_wall_budget_seconds']
        actual['resource_reservation']['expires_at_unix_seconds']=before['plan']['resource_reservation']['expires_at_unix_seconds']
        self.assertEqual(actual,before['plan'])
    def test_exact_authority_after_historical_expiry(self):
        self.assertEqual(protocol.validate_execution_window(ROOT, self.core())['status'], 'human-authorized')
    def test_missing_or_numeric_window_rejected(self):
        for key, value in [('cutoff_utc',protocol.HISTORICAL_CUTOFF),
                           ('total_wall_budget_seconds',333360),
                           ('original_origin_utc','2026-10-24T00:00:00Z'),
                           ('execution_window_authority',{})]:
            core=self.core();core[key]=value
            with self.assertRaises(ValueError): protocol.validate_execution_window(ROOT,core)
    def test_authority_bytes_are_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/protocol.WINDOW_AUTHORITY['path'];path.parent.mkdir(parents=True)
            path.write_bytes(b'{}\n')
            with self.assertRaises(ValueError): protocol.validate_execution_window(Path(tmp),self.core())
    def validated(self, deadline=123):
        return {'total_wall_budget_seconds':None,'plan':{
            'total_wall_budget_seconds':None,
            'groups':[{'id':'bifrost-c-kernel','deadline_seconds':deadline}],
            'resource_guards':{'stop_free_gib':48,'working_set_gib':30},
            'resource_reservation':{'expires_at_unix_seconds':0,'scratch_gib':24,'reserve_gib':40}}}
    def test_lease_after_old_expiry_truthful_finite_and_no_mutation(self):
        value=self.validated();before=copy.deepcopy(value)
        origin=dt.datetime.fromisoformat(protocol.ORIGIN).timestamp()
        runtime=supervisor._dispatch_lease(value,'bifrost-c-kernel',now_seconds=origin+999999)
        self.assertEqual(value,before)
        self.assertEqual(runtime['total_wall_budget_seconds'],999999+723)
        self.assertEqual(runtime['execution_window_runtime']['actual_elapsed_wall_seconds'],999999)
        self.assertEqual(runtime['plan']['resource_reservation']['expires_at_unix_seconds'],origin+999999+723)
        self.assertEqual(runtime['plan']['resource_reservation']['reserve_gib'],40)
    def test_child_wait_and_runtime_share_full_startup_boundary(self):
        validated=self.validated(); deadline=validated['plan']['groups'][0]['deadline_seconds']
        runtime=supervisor._dispatch_lease(validated,'bifrost-c-kernel')
        for elapsed in [deadline+121, deadline+599, deadline+600]:
            calls=[]
            def wait(*, timeout):
                calls.append(timeout)
                if elapsed>timeout: raise TimeoutError('synthetic wait expired')
                return 0
            self.assertEqual(supervisor._wait_group_child(types.SimpleNamespace(wait=wait),validated,'bifrost-c-kernel'),0)
            self.assertEqual(calls,[runtime['execution_window_runtime']['per_attempt_lease_seconds']])
            self.assertEqual(validated['plan']['groups'][0]['deadline_seconds'],deadline)
    def test_child_exit_is_classified_after_receipt_not_retried_by_wait(self):
        calls=[]
        def wait(*,timeout):calls.append(timeout);return 1
        self.assertEqual(supervisor._wait_group_child(types.SimpleNamespace(wait=wait),self.validated(),'bifrost-c-kernel'),1)
        self.assertEqual(calls,[723.0])
        def expired(*,timeout):raise TimeoutError('synthetic beyond deadline+600')
        with self.assertRaises(TimeoutError):
            supervisor._wait_group_child(types.SimpleNamespace(wait=expired),self.validated(),'bifrost-c-kernel')
    def test_real_supervisor_dispatch_uses_reviewed_wait_helper(self):
        import ast
        tree=ast.parse((BASE/'bifrost-v0140-supervisor-12.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_groups')
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_wait_group_child' for n in ast.walk(fn)),1)
    def test_lease_requires_exact_registered_group_and_positive_integer_timeout(self):
        for deadline in [0,-1,True,None,1.5]:
            with self.assertRaises(ValueError):supervisor._dispatch_lease(self.validated(deadline),'bifrost-c-kernel')
        with self.assertRaises(ValueError):supervisor._dispatch_lease(self.validated(),'other')
    def rows(self):
        return [{'group_id':'x','attempt_id':'x1','status':'completed','exit_code':0,
                 'start_utc':'2026-10-20T00:57:00Z','end_utc':'2026-10-20T00:58:00Z'},
                {'group_id':'y','attempt_id':'y1','status':'completed','exit_code':0,
                 'start_utc':'2026-10-25T00:57:00Z','end_utc':'2026-10-25T00:58:00Z'}]
    def replay(self, rows):
        return bridge._observed_wall(checker, rows)
    def test_wall_provenance_accepts_actual_long_interval_and_restores_checker(self):
        original=checker._validate_wall_budget
        self.assertGreater(self.replay(self.rows()),333360)
        self.assertIs(checker._validate_wall_budget,original)
    def test_wall_provenance_still_rejects_overlap_reverse_and_non_utc(self):
        for field,value in [('start_utc','2026-10-20T00:57:30Z'),
                            ('end_utc','2026-10-19T00:58:00Z'),
                            ('start_utc','2026-10-25T02:57:00+02:00')]:
            rows=self.rows();rows[1][field]=value
            with self.assertRaises(ValueError):self.replay(rows)
    def test_production_missing_wall_validator_rejected(self):
        with self.assertRaises(ValueError):
            bridge._call_mixed(types.SimpleNamespace(_replay=lambda *x: {}),{'prefix':self.rows()},self.rows(),final=False)

if __name__=='__main__':unittest.main()
