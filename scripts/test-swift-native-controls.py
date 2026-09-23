#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-swift-native-controls.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NativeControlsTests(unittest.TestCase):
    def test_timeout_never_proves_role_absence(self):
        row = audit.observe(audit.BASE / 'codeql-environment-attempt-01')
        self.assertFalse(row['finalized_swift_database'])
        self.assertFalse(row['role_observation_complete'])
        self.assertNotIn('shipped_role_nodes', row)

    def test_missing_node_query_is_incomplete(self):
        original = audit.read
        def modified(path):
            value = original(path)
            if path.name == 'witness.json':
                value['phases'].pop('roleNodes', None)
            return value
        with mock.patch.object(audit, 'read', side_effect=modified):
            row = audit.observe(audit.BASE / 'codeql-environment-attempt-02')
        self.assertFalse(row['role_observation_complete'])

    def test_feasibility_does_not_qualify_scored_budget(self):
        row = audit.observe(audit.BASE / 'codeql-environment-attempt-02')
        self.assertTrue(row['finalized_swift_database'])
        self.assertFalse(row['scored_qualified'])
        self.assertEqual(row['extraction_phase_deadline_seconds'], 180)

    def test_native_lookalike_sink_blocks_admission(self):
        result = audit.build()
        self.assertEqual(result['candidate_native_admission'], 'blocked')
        self.assertTrue(any('benchmark-owned' in b['reason'] for b in result['blockers']))
        self.assertFalse(result['capability_partition_emitted'])


if __name__ == '__main__':
    unittest.main()
