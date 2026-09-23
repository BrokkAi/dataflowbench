#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-sanitizer-resolved.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ResolvedSanitizer(unittest.TestCase):
    def setUp(self):
        def load(stage):return {n:v.read(v.BASE/('sanitizer-'+stage+'-attempt-01')/(n+'.json'))['#select']['tuples'] for n in ['flow','barriers']}
        self.before=load('ssa');self.after=load('resolved')
    def test_retained(self):v.verify()
    def test_missing_plain_body(self):
        self.before['flow']=self.before['flow'][:1]
        with self.assertRaisesRegex(ValueError,'wrapper isolation'):v.check_rows(self.before,self.after)
    def test_missing_local_int(self):
        self.after['flow']=[r for r in self.after['flow'] if r[1]!=27]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.before,self.after)
    def test_real_int_false_flow(self):
        self.after['flow'].append([17,23,87,'adapter-patched-resolved-sanitizer'])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.before,self.after)
    def test_lost_real_barrier(self):
        self.after['barriers']=[r for r in self.after['barriers'] if r[:2]!=[21,33]]
        with self.assertRaisesRegex(ValueError,'real scalar'):v.check_rows(self.before,self.after)
    def test_local_barrier_reintroduced(self):
        for r in self.after['barriers']:
            if r[:2]==[25,33]:r[4]=True
        with self.assertRaisesRegex(ValueError,'local scalar'):v.check_rows(self.before,self.after)
if __name__=='__main__':unittest.main(verbosity=2)
