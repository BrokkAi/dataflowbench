#!/usr/bin/env python3
"""Regressions for prospective result admission, without analyzer execution."""
import copy
import unittest
from swift_integration_v3 import normalize, normalize_population

class Integration(unittest.TestCase):
    def setUp(self):
        self.case = {'id': 'persistence-positive', 'template_id': 'dfb-template-native-persistence',
                     'execution_budget': {'wall_clock_seconds': 60, 'peak_memory_mb': 512}}
        self.row = {'case_id': self.case['id'], 'outcome': 'not-reached',
                    'execution_budget': copy.deepcopy(self.case['execution_budget']),
                    'expected_scopes': [3], 'coverage': [[3, 'Complete', 'AdmittedClosedScope', 3]],
                    'endpoints_verified': True, 'extraction_complete': True,
                    'phases': [{'exit_status': 0, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped'}]}

    def test_malformed_observation_is_runner_error(self):
        for row in [None, [], dict(self.row, outcome=[])]:
            self.assertEqual(normalize(self.case, row)['outcome'], 'runner-error')

    def test_successful_queries_do_not_qualify_resources(self):
        result = normalize(self.case, self.row)
        self.assertEqual(result['outcome'], 'inconclusive')
        self.assertEqual(result['raw_outcome'], 'not-reached')
        self.assertFalse(result['scored_activation'])

    def test_claimed_resource_certificate_cannot_promote(self):
        self.row.update(memory_compliance='qualified', peak_memory_mb=10, resources_qualified=True)
        self.assertEqual(normalize(self.case, self.row)['outcome'], 'inconclusive')

    def test_diagnostic_budget_is_not_canonical_budget(self):
        self.row['execution_budget']['peak_memory_mb'] = 2048
        self.assertIn('ResourceContractMismatch', normalize(self.case, self.row)['diagnostics'])

    def test_initial_state_incomplete_survives_with_findings(self):
        self.row.update(outcome='reached', findings=[{'source': 4, 'sink': 8}],
                        coverage=[[3, 'Incomplete', 'IncompleteInitialState', 8]])
        result = normalize(self.case, self.row)
        self.assertEqual(result['outcome'], 'inconclusive')
        self.assertIn('IncompleteInitialState', result['diagnostics'])
        self.assertEqual(result['observation']['findings'], self.row['findings'])

    def test_missing_scope_is_not_clean(self):
        self.row['expected_scopes'].append(9)
        self.assertIn('MissingScopeCoverage', normalize(self.case, self.row)['diagnostics'])

    def test_scope_inventory_required(self):
        self.row.pop('expected_scopes')
        self.assertIn('MissingScopeInventory', normalize(self.case, self.row)['diagnostics'])

    def test_missing_endpoint_or_failed_extraction_is_runner_error(self):
        for key in ['endpoints_verified', 'extraction_complete']:
            row = copy.deepcopy(self.row); row[key] = False
            self.assertEqual(normalize(self.case, row)['outcome'], 'runner-error')

    def test_timeout_and_cleanup_uncertainty_are_errors(self):
        for key, value in [('cleanup_status', 'uncertain'), ('exit_status', 1)]:
            row = copy.deepcopy(self.row); row['phases'][0][key] = value
            self.assertEqual(normalize(self.case, row)['outcome'], 'runner-error')

    def test_timeout_preserves_budget_exhaustion(self):
        self.row['phases'][0].update(timed_out=True, exit_status=-15)
        result = normalize(self.case, self.row)
        self.assertEqual(result['outcome'], 'inconclusive')
        self.assertIn('BudgetExhausted', result['diagnostics'])

    def test_missing_observation_retains_denominator(self):
        rows = normalize_population([self.case], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['outcome'], 'runner-error')

    def test_duplicate_and_foreign_observations_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate observation'):
            normalize_population([self.case], [self.row, self.row])
        with self.assertRaisesRegex(ValueError, 'foreign observation'):
            normalize_population([self.case], [dict(self.row, case_id='other')])

    def test_unsupported_is_not_inferred(self):
        self.row['outcome'] = 'unsupported'
        result = normalize(self.case, self.row)
        self.assertEqual(result['outcome'], 'inconclusive')
        self.assertIn('UnsupportedPartitionNotVerified', result['diagnostics'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
