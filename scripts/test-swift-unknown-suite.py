#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-unknown-suite.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class UnknownSuite(unittest.TestCase):
    def setUp(self):
        p=v.BASE/'unknown-attempt-01/probe';self.rows={n:v.read(p/(n+'.json'))['#select']['tuples'] for n in v.read(v.BASE/'unknown-plan-v1.json')['queries']}
    def test_retained(self):v.verify()
    def test_missing_mixed_flow(self):
        self.rows['flow']=[r for r in self.rows['flow'] if r[1]!=70]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows,True)
    def test_same_suite_false_flow(self):
        self.rows['flow'].append([12,78,87,v.PROFILE])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows,True)
    def test_mixed_strong_clear(self):
        self.rows['clears'].append([68,5,'mixed'])
        with self.assertRaisesRegex(ValueError,'must clears'):v.check_rows(self.rows,True)
    def test_lost_same_suite_clear(self):
        self.rows['clears']=[r for r in self.rows['clears'] if r[0]!=76]
        with self.assertRaisesRegex(ValueError,'must clears'):v.check_rows(self.rows,True)
    def test_forged_must_proof(self):
        for r in self.rows['receiver-proof']:
            if r[0]==68:r[3]=True
        with self.assertRaisesRegex(ValueError,'mixed receiver proof'):v.check_rows(self.rows,True)
    def test_missing_domain(self):
        self.rows['receiver-proof']=[r for r in self.rows['receiver-proof'] if not(r[0]==68 and r[2]=='DataFlowBench.Other.Persistence')]
        with self.assertRaisesRegex(ValueError,'mixed receiver proof'):v.check_rows(self.rows,True)
    def test_unknown_strong_clear(self):
        self.rows['clears'].append([84,5,'unknown-phi'])
        with self.assertRaisesRegex(ValueError,'unknown origin strong clear'):v.check_rows(self.rows,True)
    def test_loop_incomplete_erased(self):
        for r in self.rows['receiver-proof']:
            if r[0]==94:r[4]=True
        with self.assertRaisesRegex(ValueError,'unknown origin proof'):v.check_rows(self.rows,True)
    def test_unknown_flow_missing(self):
        self.rows['flow']=[r for r in self.rows['flow'] if r[1]!=96]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows,True)
    def test_vendor_label(self):
        self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile'):v.check_rows(self.rows,True)
if __name__=='__main__':unittest.main(verbosity=2)
