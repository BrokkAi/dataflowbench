#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('v', Path(__file__).with_name('verify-swift-keyed-persistence.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)

class KeyedPersistence(unittest.TestCase):
    def setUp(self):
        self.data = {n: v.rows(v.BASE / 'suite-attempt-03', n) for n in ['flow', 'roles', 'states', 'transitions', 'clears', 'content', 'persistence-identity']}
    def test_retained(self):v.verify()
    def test_missing_alias(self):
        self.data['flow'] = [r for r in self.data['flow'] if r[1] != 29]
        with self.assertRaisesRegex(ValueError, 'separation'):v.check_rows(self.data)
    def test_missing_shared_suite(self):
        self.data['flow'] = [r for r in self.data['flow'] if r[1] != 43]
        with self.assertRaisesRegex(ValueError, 'separation'):v.check_rows(self.data)
    def test_overwrite_false_flow(self):
        self.data['flow'].append([12, 32, 87, v.PROFILE])
        with self.assertRaisesRegex(ValueError, 'separation'):v.check_rows(self.data)
    def test_lost_clear(self):
        self.data['clears'] = [r for r in self.data['clears'] if r[0] != 30]
        with self.assertRaisesRegex(ValueError, 'clears'):v.check_rows(self.data)
    def test_forged_suite(self):
        self.data['states'][0][2] = 'Unknown'
        with self.assertRaisesRegex(ValueError, 'state identity'):v.check_rows(self.data)
    def test_unordered_shortcut(self):
        self.data['transitions'].append([27, True, 31, False, 'DataFlowBench.Independent.Persistence'])
        with self.assertRaisesRegex(ValueError, 'transitions'):v.check_rows(self.data)
    def test_vendor_relabel(self):
        self.data['roles'][0][2] = 'vendor-native'
        with self.assertRaisesRegex(ValueError, 'profile'):v.check_rows(self.data)
    def test_local_owner_confusion(self):
        self.data['persistence-identity'][0][2] = 'DataFlowBenchTaintSwift'
        with self.assertRaisesRegex(ValueError, 'owner'):v.check_rows(self.data)
    def test_artifact_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'raw').write_text('before')
            (p/'manifest.json').write_text(v.json.dumps({'raw':v.sha(p/'raw')}))
            (p/'raw').write_text('after')
            with self.assertRaisesRegex(ValueError,'artifact digest'):v.manifest(p)
    def test_added_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'manifest.json').write_text('{}');(p/'raw').write_text('extra')
            with self.assertRaisesRegex(ValueError,'artifact closure'):v.manifest(p)

if __name__ == '__main__':unittest.main(verbosity=2)
