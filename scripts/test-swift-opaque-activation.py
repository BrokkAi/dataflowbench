#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-opaque-activation.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class OpaqueActivation(unittest.TestCase):
    def setUp(self):
        p=v.BASE/'analysis-attempt-02/probe';self.rows={n:v.read(p/(n+'.json'))['#select']['tuples'] for n in ['roles','flow','identity']}
    def test_retained(self):v.verify()
    def test_missing_direct_baseline(self):
        self.rows['flow']=[r for r in self.rows['flow'] if r[1]!=27]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_model_not_load_bearing(self):
        self.rows['flow'].append([26,28,14,v.PROFILES[0]])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_wrong_position_propagates(self):
        self.rows['flow'].append([26,31,14,v.PROFILES[1]])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_undeclared_member_propagates(self):
        self.rows['flow'].append([26,29,14,v.PROFILES[1]])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_wrong_owner(self):
        self.rows['identity'][0][2]='Lookalike'
        with self.assertRaisesRegex(ValueError,'wrapper signature'):v.check_rows(self.rows)
    def test_wrong_parameter_binding(self):
        self.rows['identity'][2][-1]=True
        with self.assertRaisesRegex(ValueError,'position identity'):v.check_rows(self.rows)
    def test_missing_endpoint(self):
        self.rows['roles'].pop()
        with self.assertRaisesRegex(ValueError,'role profile'):v.check_rows(self.rows)
    def test_vendor_attribution(self):
        self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'role profile'):v.check_rows(self.rows)
if __name__=='__main__':unittest.main(verbosity=2)
