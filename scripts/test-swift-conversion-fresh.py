#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-conversion-fresh.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class FreshControls(unittest.TestCase):
    def setUp(self):
        p=v.BASE/'conversion-body-fresh-attempt-01/probe';plan=v.read(v.BASE/'conversion-body-fresh-plan-v1.json');self.rows={n:v.read(p/(n+'.json'))['#select']['tuples'] for n in plan['queries']}
    def test_retained(self):v.verify()
    def test_missing_body(self):
        self.rows['flow']=self.rows['flow'][:1]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_wrong_arity_false_flow(self):
        self.rows['flow'].append([15,42,87,v.PROFILE])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_local_summary(self):
        self.rows['summary-identity'][-1][-1]=True
        with self.assertRaisesRegex(ValueError,'declaration provenance'):v.check_rows(self.rows)
    def test_ssa_regression(self):
        self.rows['self-assignment'][-1][2]=False
        with self.assertRaisesRegex(ValueError,'SSA return'):v.check_rows(self.rows)
    def test_missing_content(self):
        self.rows['summary-store'][-1][-1]='Unknown'
        with self.assertRaisesRegex(ValueError,'content stores'):v.check_rows(self.rows)
    def test_vendor_relabel(self):
        self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile attribution'):v.check_rows(self.rows)
if __name__=='__main__':unittest.main(verbosity=2)
