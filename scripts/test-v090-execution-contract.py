#!/usr/bin/env python3
"""Mutations that must never turn a planning contract into executable evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract_check', ROOT/'scripts/check-v090-execution-contract.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = json.loads((ROOT/checker.CONTRACT).read_text())
        refs = [self.plan['preparation_plan'], *self.plan['identity_evidence'],
                *self.plan['environment_implementation'], self.plan['codeql_compatibility']]
        for ref in refs:
            target = self.root/ref['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT/ref['path']).read_bytes())

    def check(self):
        target = self.root/checker.CONTRACT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.plan))
        return checker.validate(self.root)

    def test_complete_planning_inventory(self):
        self.assertEqual(self.check(), {'groups': 84, 'controls': 30, 'executable': False})

    def test_cannot_self_authorize(self):
        self.plan['execution_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'must not authorize'):
            self.check()

    def test_omitted_report_case_is_rejected(self):
        self.plan['groups'][0]['reports'][0]['case_ids'].pop()
        with self.assertRaisesRegex(ValueError, 'membership changed'):
            self.check()

    def test_mixed_codeql_version_is_rejected(self):
        group = next(g for g in self.plan['groups'] if g['tool'] == 'codeql')
        group['reports'][0]['tool_version'] = '2.27.0'
        with self.assertRaisesRegex(ValueError, 'version drift'):
            self.check()

    def test_missing_swift_group_is_rejected(self):
        self.plan['groups'] = [g for g in self.plan['groups'] if g['id'] != 'codeql-swift-common108']
        with self.assertRaisesRegex(ValueError, '84 groups'):
            self.check()

    def test_changed_command_is_rejected(self):
        self.plan['groups'][0]['argv'].append('--unreviewed-option')
        with self.assertRaisesRegex(ValueError, 'command differs'):
            self.check()

    def test_swift_export_mapping_is_rejected(self):
        self.plan['groups'][-1]['reports'][0]['source_path'] = self.plan['groups'][-1]['reports'][1]['source_path']
        with self.assertRaisesRegex(ValueError, 'partition mapping drift'):
            self.check()

    def test_uncaptured_report_is_rejected(self):
        self.plan['groups'][0]['reports'][0]['source_path'] = 'reports/foreign.json'
        with self.assertRaisesRegex(ValueError, 'uncaptured report source'):
            self.check()

    def test_parent_commit_binding_is_rejected(self):
        self.plan['input_commits']['corpus'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'input commits changed'):
            self.check()

    def test_deadline_cannot_shrink(self):
        self.plan['groups'][-1]['deadline_seconds'] -= 1
        with self.assertRaisesRegex(ValueError, 'deadline changed'):
            self.check()


if __name__ == '__main__':
    unittest.main()
