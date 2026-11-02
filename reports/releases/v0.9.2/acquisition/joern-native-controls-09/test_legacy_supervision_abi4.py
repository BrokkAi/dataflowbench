"""Retained supervisor cases with an exact ABI4-only fixture adapter.

The original assertions/phase helper are unchanged. Its old generic native
fixture is deliberately invalid under the new exact-provider boundary; only
query-fixture construction is replaced. No analyzer or native query runs.
"""
import importlib.util
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

legacy=load('_legacy_abi4_supervisor',BASE.parent/'joern-native-controls-07/test_reconciliation_policy.py')
fixtures=load('_abi4_supervisor_query_fixtures',BASE/'test_process_reconciliation_abi4_policy.py')


def abi4_query(native_before=None,command=None,native_after=None,**kwargs):
    if kwargs:
        raise AssertionError('unexpected legacy query fixture options')
    def convert(rows):
        return [fixtures._native_row(row['pid'],birth='100:12345') for row in rows or []]
    return fixtures._query(before=convert(native_before),command=command or [],after=convert(native_after))

legacy.query=abi4_query


class LegacyABI4SupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy.ReconciliationPolicyTests.setUpClass()

    def retained(self,name):
        instance=legacy.ReconciliationPolicyTests(name)
        getattr(instance,name)()

    def test_successful_receipt_and_one_pass(self):
        self.retained('test_supervisor_persists_successful_receipt_and_uses_one_pass')

    def test_slow_evaluation_stops(self):
        self.retained('test_slow_evaluation_past_absolute_pass_deadline_stops_before_continuation')

    def test_late_durable_receipt_stops(self):
        self.retained('test_slow_durable_receipt_past_absolute_pass_deadline_stops_before_continuation')

    def test_candidate_presence_and_receipt_failure_keep_primary_error(self):
        self.retained('test_supervisor_reappearance_stops_and_receipt_failure_keeps_primary_error')

    def test_query_exception_is_typed(self):
        self.retained('test_query_runner_exception_is_persisted_as_typed_incomplete_attempt')

    def test_evaluator_exception_retains_query(self):
        self.retained('test_evaluator_exception_keeps_query_and_typed_incomplete_evaluation')

    def test_later_raw_reappearance_cannot_inherit_absence_or_second_pass(self):
        self.retained('test_later_current_reappearance_cannot_inherit_the_absence_or_get_second_pass')


if __name__=='__main__':
    unittest.main()
