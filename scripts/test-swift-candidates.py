#!/usr/bin/env python3
"""Regression guards for non-scored candidate evidence interpretation."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-swift-candidates.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CandidateTests(unittest.TestCase):
    def test_failed_pack_resolution_is_not_observation_completion(self):
        result = audit.summarize_attempt(audit.BASE / 'codeql-endpoint-identity-attempt-01')
        self.assertFalse(result['observations_complete'])
        self.assertNotIn('identity_control_pass', result)
        self.assertFalse(result['scored_qualification'])

    def test_wrong_declaration_flow_fails_identity_control(self):
        original = audit.read
        def changed(path):
            value = copy.deepcopy(original(path))
            if path.name == 'flow.json':
                value['#select']['tuples'][0][0]['label'] = 'file:///control/main.swift:12:1:12:9'
            return value
        with mock.patch.object(audit, 'read', side_effect=changed):
            result = audit.summarize_attempt(audit.BASE / 'codeql-endpoint-identity-attempt-02')
        self.assertTrue(result['exact_endpoints'])
        self.assertFalse(result['identity_control_pass'])

    def test_successful_controls_do_not_promote_incomplete_results(self):
        result = audit.build()
        self.assertFalse(result['release_qualified'])
        self.assertEqual(result['opaque_choice'], 'pending')
        self.assertTrue(all(not a['scored_qualification'] for a in result['attempts']))
        joern = next(a for a in result['attempts'] if 'joern-result-positive' in a['path'])
        self.assertEqual(joern['analysis_completeness']['status'], 'unproven')
        self.assertEqual(joern['memory_compliance'], 'unproven')


if __name__ == '__main__':
    unittest.main()
