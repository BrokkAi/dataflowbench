#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-persistence-canonical.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class CanonicalPersistence(unittest.TestCase):
    def load(self,polarity='positive'):
        p=v.BASE/('canonical-attempt-01/dfb-taint-swift-native-persistence-'+polarity)
        self.case=v.read(p/'canonical-case.json');self.observation=v.read(p/'observation.json')
        self.rows={n:v.read(p/'probe'/(n+'.json'))['#select']['tuples'] for n in ['roles','flow','identity','persistence-identity','persistence-keys','content','clears','states','transitions']}
    def test_complete_retained_pair(self):v.verify()
    def test_missing_positive(self):
        self.load();self.rows['flow']=[]
        with self.assertRaisesRegex(ValueError,'expected flow'):v.check_semantics(self.rows,self.case,self.observation)
    def test_negative_false_flow(self):
        self.load('negative');self.rows['flow']=[[7,10,87,v.PROFILES[0]]]
        with self.assertRaisesRegex(ValueError,'expected flow'):v.check_semantics(self.rows,self.case,self.observation)
    def test_vendor_relabel(self):
        self.load();self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile attribution'):v.check_semantics(self.rows,self.case,self.observation)
    def test_wrong_persistence_owner(self):
        self.load('negative');self.rows['persistence-identity'][0][2]='Local'
        with self.assertRaisesRegex(ValueError,'persistence identity'):v.check_semantics(self.rows,self.case,self.observation)
    def test_lost_key_clear(self):
        self.load('negative');self.rows['clears']=[]
        with self.assertRaisesRegex(ValueError,'clears'):v.check_semantics(self.rows,self.case,self.observation)
    def test_wrong_read_key(self):
        self.load('negative');self.rows['persistence-keys'][-1][4]='payload'
        with self.assertRaisesRegex(ValueError,'key binding'):v.check_semantics(self.rows,self.case,self.observation)
    def test_cross_suite_state(self):
        self.load();self.rows['states'][0][2]='Unrelated'
        with self.assertRaisesRegex(ValueError,'state domains'):v.check_semantics(self.rows,self.case,self.observation)
    def test_lost_source_identity(self):
        self.load();self.rows['identity']=[]
        with self.assertRaisesRegex(ValueError,'source identity'):v.check_semantics(self.rows,self.case,self.observation)
    def test_observation_rewrite(self):
        self.load();self.observation['lanes'][v.PROFILES[0]]['matches_case_expectation']=False
        with self.assertRaisesRegex(ValueError,'projection'):v.check_semantics(self.rows,self.case,self.observation)
if __name__=='__main__':unittest.main(verbosity=2)
