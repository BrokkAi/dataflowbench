"""Synthetic tests for the new wrapper boundary; no real process queries."""
import copy
import json
from pathlib import Path
import unittest
from unittest import mock
import native_qualifier as n
import test_interval_supervision as interval
interval_result = interval.interval_result
legacy = interval.legacy

ROOT = Path(__file__).resolve().parents[5]


def two_rows():
    result = interval_result()
    other = copy.deepcopy(result['historical_only_intrasnapshot_rows'][0])
    other['pid'] = 603
    result['historical_only_intrasnapshot_rows'].append(other)
    return result


class SetSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        interval.IntervalSupervisorTests.setUpClass.__func__(cls)

    supervise_candidate = interval.IntervalSupervisorTests.supervise_candidate

    def test_multiple_rows_validate_without_ownership(self):
        result = two_rows()
        before = copy.deepcopy(result)
        self.assertEqual(n.validate_interval_evaluation(result,[{'pid':601}],{500:'root-birth'}),{602,603})
        self.assertEqual(result,before)

    def test_bad_last_row_duplicate_and_bound_reject_entire_set(self):
        good = two_rows()
        for delta in ({'pid':602}, {'pid':601}, {'pid':500}, {'pid':True},
                      {'row':{}}, {'row':good['historical_only_intrasnapshot_rows'][1]['row'] | {'argv_bridge_allowed':True}}):
            bad = copy.deepcopy(good)
            bad['historical_only_intrasnapshot_rows'][-1].update(delta)
            original = copy.deepcopy(bad)
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                n.validate_interval_evaluation(bad,[{'pid':601}],{500:'root-birth'})
            self.assertEqual(bad,original)
        with self.assertRaises(ValueError):
            n.validate_interval_evaluation(good | {'historical_only_intrasnapshot_rows':[{}]*16385},[],{})
        with self.assertRaises(ValueError):
            n.validate_interval_evaluation(good | {'tracked_after':{603:'invented'}},[],{})

    def test_multiple_rows_require_durable_receipt_and_semantic_only_result(self):
        with mock.patch.object(n.process_reconciliation,'evaluate_reconciliation',return_value=two_rows()):
            result,calls,receipt,_=self.supervise_candidate(legacy.query())
        self.assertIsNone(result['failure'])
        self.assertEqual(len(calls),1)
        self.assertEqual(len(receipt['evaluation']['historical_only_intrasnapshot_rows']),2)
        self.assertTrue(result['reconciliation_attempts'][0]['supervisor_continuation_authorized'])
        for key,value in n.SEMANTIC_SCOPE.items():
            self.assertEqual(result[key],value)

    def test_last_historical_pid_reappearance_stops(self):
        with mock.patch.object(n.process_reconciliation,'evaluate_reconciliation',return_value=two_rows()):
            result,calls,_,stop=self.supervise_candidate(legacy.query(),current_reappearance=True,history_reappearance=603)
        self.assertIsNotNone(result['failure'])
        self.assertEqual(len(calls),1)
        self.assertEqual(stop['historical_absent_pid_reappearances'][0]['pid'],603)

    def test_human_binding_scope_and_limits_are_exact(self):
        policy=json.loads((ROOT/n.SNAPSHOT_POLICY['path']).read_bytes())
        self.assertEqual(n.sha((ROOT/n.SNAPSHOT_POLICY['path']).read_bytes()),n.SNAPSHOT_POLICY['sha256'])
        authority={'status':'approved','automatic_retry':False,'publication_hold':True,
                   'human_snapshot_set_policy':n.SNAPSHOT_POLICY,**n.SEMANTIC_SCOPE}
        n.validate_semantic_policy(policy,authority)
        for key in ('maximum_native_rows_per_observation_exclusive','maximum_combined_native_rows_upper_bound',
                    'maximum_existing_query_seconds','maximum_query_output_bytes'):
            with self.subTest(policy_field=key), self.assertRaises(ValueError):
                n.validate_semantic_policy(policy | {key:policy[key]+1},authority)
        for key in ('extra_queries_retries_or_time_authorized','uncontended_timing_certified',
                    'relative_performance_conclusions_authorized','automatic_retry'):
            with self.subTest(policy_field=key), self.assertRaises(ValueError):
                n.validate_semantic_policy(policy | {key:True},authority)
        for key,value in n.SEMANTIC_SCOPE.items():
            with self.subTest(authority_field=key), self.assertRaises(ValueError):
                n.validate_semantic_policy(policy,authority | {key:'performance' if type(value) is str else True})
        with self.assertRaises(ValueError):
            n.validate_semantic_policy(policy,authority | {'human_snapshot_set_policy':{'path':'old','sha256':'0'*64}})


if __name__ == '__main__':
    unittest.main()
