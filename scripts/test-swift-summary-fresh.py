#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-swift-summary-fresh.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class CanonicalSummary(unittest.TestCase):
    def load(self,polarity='positive'):
        p=v.BASE/('canonical-summary-attempt-01/dfb-taint-swift-native-summary-'+polarity)
        self.case=v.read(p/'canonical-case.json');self.observation=v.read(p/'observation.json')
        self.rows={n:v.read(p/'probe'/(n+'.json'))['#select']['tuples'] for n in ['roles','flow','identity','summary-identity','summary-ports','summary-transfer','summary-store']}
    def test_complete_retained_pair(self):v.verify()
    def test_missing_positive_flow(self):
        self.load();self.rows['flow']=[]
        with self.assertRaisesRegex(ValueError,'expected flow'):v.check_semantics(self.rows,self.case,self.observation)
    def test_negative_false_flow(self):
        self.load('negative');self.rows['flow']=[[4,8,87,v.PROFILES[0]]]
        with self.assertRaisesRegex(ValueError,'expected flow'):v.check_semantics(self.rows,self.case,self.observation)
    def test_vendor_relabel(self):
        self.load();self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile attribution'):v.check_semantics(self.rows,self.case,self.observation)
    def test_wrong_summary_owner(self):
        self.load();self.rows['summary-identity'][0][3]='Local'
        with self.assertRaisesRegex(ValueError,'method identity'):v.check_semantics(self.rows,self.case,self.observation)
    def test_missing_optional_store(self):
        self.load();self.rows['summary-store']=[r for r in self.rows['summary-store'] if r[-1]!='OptionalSome']
        with self.assertRaisesRegex(ValueError,'transfer/store'):v.check_semantics(self.rows,self.case,self.observation)
    def test_invented_origin(self):
        self.load();self.rows['summary-ports'][0][3]='exact-row-without-proof'
        with self.assertRaisesRegex(ValueError,'ports/origin'):v.check_semantics(self.rows,self.case,self.observation)
    def test_observation_rewrite(self):
        self.load();self.observation['lanes'][v.PROFILES[0]]['matches_case_expectation']=False
        with self.assertRaisesRegex(ValueError,'projection'):v.check_semantics(self.rows,self.case,self.observation)
if __name__=='__main__':unittest.main(verbosity=2)
