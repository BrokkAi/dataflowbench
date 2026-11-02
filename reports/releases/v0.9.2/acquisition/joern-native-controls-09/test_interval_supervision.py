"""Actual supervisor phase/receipt/deadline tests with harmless in-memory processes.

The evaluator result is a typed stub here to isolate the supervisor boundary.
Actual ABI4 eligibility and evidence validation are tested separately.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
import native_qualifier as n

LEGACY=Path(__file__).resolve().parents[1]/'joern-native-controls-07/test_reconciliation_policy.py'
spec=importlib.util.spec_from_file_location('_interval_legacy_fixtures',LEGACY)
legacy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def interval_result():
    return {'status':n.INTERVAL_STATUS,'complete':True,'fresh_contenders':[],
            'tracked_after':{500:'root-birth'},'candidate_outcomes':[
                {'pid':601,'status':'unresolved_historical_absent_at_reconciliation'}],
            'historical_only_intrasnapshot_rows':[{'pid':602,'row':{
                'status':'unresolved_historical_intrasnapshot_disappearance',
                'historical_ownership':'unknown','historical_foreignness':'unknown',
                'workload_relevance':'unknown','exact_exit_time':'unknown',
                'current_map_eligible':False,'argv_bridge_allowed':False,
                'absence_evidence':{'first_table_present':True,
                    'same_observation_second_table_absent':True,'command_snapshot_absent_by_pid':True,
                    'other_native_observation_absent_by_pid':True,'final_current_kernel_table_absent':True,
                    'continuous_absence_claim':False,'os_global_absence_claim':False}}}],
            'historical_ownership':'unknown','historical_foreignness':'unknown',
            'continuous_absence_claim':False,'os_global_absence_claim':False,
            'cleanup_authorized':False}


class IntervalSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy.ReconciliationPolicyTests.setUpClass()
        for name in ('executor_source','controller_source','process_source'):
            setattr(cls,name,getattr(legacy.ReconciliationPolicyTests,name))

    def supervise_candidate(self, fresh_query, *, fail_reconciliation_receipt=False,
                            current_reappearance=False, query_raises=False,
                            clock_value=None, advance_after_receipt=False, history_reappearance=False):
        clock_value = [0.0] if clock_value is None else clock_value
        directory = Path(tempfile.mkdtemp(prefix="monitor06-test-", dir=Path(__file__).parent))
        read_fd, write_fd = os.pipe()
        lock_path = directory / "lock"
        lock_path.write_bytes(b"")
        lock_fd = os.open(lock_path, os.O_RDONLY)
        frames = [
            {"token": "token", "pid": 500, "birth_identity": "root-birth",
             "phase": phase, "observed_monotonic": 0.0}
            for phase in ("ready", "controls-started", "controls-returned")
        ]
        for frame in frames:
            os.write(write_fd, n.canonical(frame))

        class Child:
            pid = 500
            def __init__(self):
                self.calls = 0
            def poll(self):
                self.calls += 1
                return None if self.calls == 1 else 0

        child = Child()
        controller = types.SimpleNamespace(
            _process=lambda pid: {"pid": pid, "birth_identity": "root-birth"},
            _bounded_reap_unidentified_child=lambda value: {"coordinator_reaped": True},
            _hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders,
        )
        native_states = iter([
            {500: (1, "root-birth", "S")},  # original snapshot, rejected row lacks native identity
            ({500: (1, "root-birth", "S"), (602 if history_reappearance else 601): (500, "recycled-birth", "S")}
             if current_reappearance else {500: (1, "root-birth", "S")}),
            {},                                  # cleanup verification
        ])
        command_tables = iter([
            "601 80.0 java /usr/bin/java -version",
            f"{602 if history_reappearance else 601} 80.0 java /usr/bin/java -version" if current_reappearance is True else "",
        ])
        executor = types.SimpleNamespace(
            _process_table=lambda: next(command_tables),
            _contenders=self.executor_source._contenders,
        )
        proc = types.SimpleNamespace(
            start_identity=lambda pid, fallback: "root-birth",
            process_table=lambda: next(native_states),
            descendants=self.process_source.descendants,
            active=lambda table, tracked: [],
        )
        resources = types.SimpleNamespace(sample=lambda **kwargs: None)
        query_calls = []
        def query_runner(*, boundary_deadline, clock):
            query_calls.append(boundary_deadline)
            if query_raises:
                raise RuntimeError("query runner failed before returning evidence")
            return fresh_query
        original_immutable = n.immutable
        def immutable(path, value):
            if fail_reconciliation_receipt and path.name.startswith("contention-reconciliation-"):
                raise OSError("reconciliation receipt path unavailable")
            receipt_ref = original_immutable(path, value)
            if advance_after_receipt and path.name.startswith("contention-reconciliation-"):
                clock_value[0] = 6.0
            return receipt_ref
        try:
            with mock.patch.object(n, "immutable", side_effect=immutable), \
                 mock.patch.object(n.time, "sleep", return_value=None):
                result = n.supervise(
                    ["fixture-only"], root=directory, env={}, stdout=None, stderr=None,
                    lock_fd=lock_fd, request_sha="a" * 64, controller=controller,
                    proc=proc, resources=resources, executor=executor, namespace=directory,
                    token="token", read_fd=read_fd, write_fd=write_fd,
                    popen=lambda *args, **kwargs: child, clock=lambda: clock_value[0],
                    reconciliation_query=query_runner,
                )
            receipt_path = directory / "contention-reconciliation-01.json"
            receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else None
            stop_path = directory / "contention-stop.json"
            stop_receipt = json.loads(stop_path.read_bytes()) if stop_path.exists() else None
            return result, query_calls, receipt, stop_receipt
        finally:
            os.close(lock_fd)
            for path in directory.iterdir():
                path.unlink()
            directory.rmdir()


    def test_interval_boundary_requires_exact_one_non_candidate_untracked_row(self):
        good=interval_result()
        self.assertEqual(n.validate_interval_evaluation(good,[{'pid':601}],{500:'root-birth'}),{602})
        changes=[{'historical_only_intrasnapshot_rows':[]},
                 {'historical_only_intrasnapshot_rows':[{'pid':602},{'pid':603}]},
                 {'historical_only_intrasnapshot_rows':[{'pid':True}]},
                 {'historical_only_intrasnapshot_rows':[{'pid':601}]},
                 {'historical_only_intrasnapshot_rows':[{'pid':500}]},
                 {'tracked_after':{500:'root-birth',602:'invented'}},
                 {'fresh_contenders':[{'pid':999}]}, {'historical_ownership':'owned'},
                 {'historical_foreignness':'harmless'}, {'continuous_absence_claim':True},
                 {'os_global_absence_claim':True}, {'cleanup_authorized':True}, {'complete':False}]
        for delta in changes:
            with self.subTest(delta=delta),self.assertRaises(ValueError):
                n.validate_interval_evaluation(good|delta,[{'pid':601}],{500:'root-birth'})
        with self.assertRaises(ValueError):
            n.validate_interval_evaluation(good|{'status':'historical-absence-observed-no-fresh-contender'},[{'pid':601}],{})
        for delta in ({'status':'owned'}, {'workload_relevance':'harmless'},
                      {'historical_ownership':'owned'}, {'historical_foreignness':'foreign'},
                      {'exact_exit_time':'known'}, {'current_map_eligible':True},
                      {'argv_bridge_allowed':True}):
            bad=copy.deepcopy(good);bad['historical_only_intrasnapshot_rows'][0]['row'].update(delta)
            with self.subTest(row_delta=delta),self.assertRaises(ValueError):
                n.validate_interval_evaluation(bad,[{'pid':601}],{500:'root-birth'})

    def test_each_serialized_absence_predicate_is_mandatory(self):
        good=interval_result()
        evidence=good['historical_only_intrasnapshot_rows'][0]['row']['absence_evidence']
        for key,value in evidence.items():
            for mode in ('missing','inverted'):
                bad=copy.deepcopy(good);absence=bad['historical_only_intrasnapshot_rows'][0]['row']['absence_evidence']
                if mode=='missing':absence.pop(key)
                else:absence[key]=not value
                with self.subTest(key=key,mode=mode),self.assertRaises(ValueError):
                    n.validate_interval_evaluation(bad,[{'pid':601}],{500:'root-birth'})

    def test_new_status_requires_durable_evidence_and_original_deadlines(self):
        with mock.patch.object(n.process_reconciliation,'evaluate_reconciliation',return_value=interval_result()):
            result,calls,receipt,_=self.supervise_candidate(legacy.query())
        self.assertIsNone(result['failure'])
        self.assertEqual(len(calls),1)
        self.assertEqual(receipt['status'],n.INTERVAL_STATUS)
        self.assertEqual(receipt['evaluation']['historical_only_intrasnapshot_rows'][0]['pid'],602)
        attempt=result['reconciliation_attempts'][0]
        self.assertTrue(attempt['supervisor_continuation_authorized'])
        self.assertEqual(attempt['receipt_write_state'],'durable')
        self.assertTrue(all(c['within_deadline'] for c in attempt['deadline_checks'].values()))
        self.assertNotIn(602,attempt['evaluation']['tracked_after'])

    def test_receipt_failure_or_late_receipt_rejects_new_status(self):
        for options in ({'fail_reconciliation_receipt':True},{'advance_after_receipt':True}):
            with self.subTest(options=options),mock.patch.object(n.process_reconciliation,'evaluate_reconciliation',return_value=interval_result()):
                result,calls,_,_=self.supervise_candidate(legacy.query(),**options)
            self.assertIsNotNone(result['failure'])
            self.assertFalse(result['reconciliation_attempts'][0]['supervisor_continuation_authorized'])
            self.assertEqual(len(calls),1)

    def test_historical_only_pid_reappearance_stops_even_if_newly_owned_descendant(self):
        with mock.patch.object(n.process_reconciliation,'evaluate_reconciliation',return_value=interval_result()):
            result,calls,_,stop=self.supervise_candidate(legacy.query(),current_reappearance=True,history_reappearance=True)
        self.assertIsNotNone(result['failure'])
        self.assertEqual(len(calls),1)
        self.assertTrue(stop['historical_absent_pid_reappearances'])
        self.assertEqual(stop['historical_absent_pid_reappearances'][0]['pid'],602)


if __name__=='__main__':
    unittest.main()
