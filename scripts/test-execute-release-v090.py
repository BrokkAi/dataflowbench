#!/usr/bin/env python3
"""Resume never mistakes failed or incomplete attempts for completion."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('executor', Path(__file__).with_name('execute-release-v090.py'))
executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(executor)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'scripts').mkdir()
        (self.root/'scripts/verify-release-attempt-v090.py').write_text('def verify_attempt(*args):\n    return {}\n')
        self.base = self.root/'reports/releases/v0.9.0'
        self.base.mkdir(parents=True)

    def test_empty_matrix_is_not_completed(self):
        self.assertEqual(executor.completed_groups(self.root, 'contract.json'), set())

    def test_failed_attempt_stops_resume(self):
        (self.base/'ledger-v1.jsonl').write_text(json.dumps({'group_id':'one','status':'failed','attempt_id':'one-01'})+'\n')
        with self.assertRaisesRegex(ValueError, 'explicit review'):
            executor.completed_groups(self.root, 'contract.json')

    def test_started_only_attempt_stops_resume(self):
        (self.base/'attempts/one-01').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'lacks completion'):
            executor.completed_groups(self.root, 'contract.json')

    def test_duplicate_success_not_selected(self):
        row={'group_id':'one','status':'completed','attempt_id':'one-01'}
        (self.base/'ledger-v1.jsonl').write_text((json.dumps(row)+'\n')*2)
        with self.assertRaisesRegex(ValueError, 'multiple selected'):
            executor.completed_groups(self.root, 'contract.json')


if __name__ == '__main__':
    unittest.main()
