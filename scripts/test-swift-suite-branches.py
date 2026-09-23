#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-suite-branches.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class BranchState(unittest.TestCase):
    def setUp(self):
        p=v.BASE/'branch-attempt-01/probe'
        self.rows={n:v.read(p/(n+'.json'))['#select']['tuples'] for n in v.read(v.BASE/'branch-plan-v1.json')['queries']}
    def test_retained(self):v.verify()
    def test_missing_one_branch_flow(self):
        self.rows['flow']=[r for r in self.rows['flow'] if r[1]!=61]
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_both_branches_false_positive(self):
        self.rows['flow'].append([12,55,87,v.PROFILE])
        with self.assertRaisesRegex(ValueError,'flow separation'):v.check_rows(self.rows)
    def test_lost_clear(self):
        self.rows['clears']=[r for r in self.rows['clears'] if r[0]!=52]
        with self.assertRaisesRegex(ValueError,'clears'):v.check_rows(self.rows)
    def test_bypass_write(self):
        self.rows['transitions'].append([48,True,54,False,'DataFlowBench.Independent.Persistence'])
        with self.assertRaisesRegex(ValueError,'transitions'):v.check_rows(self.rows)
    def test_lost_branch_path(self):
        self.rows['transitions']=[r for r in self.rows['transitions'] if r[:4]!=[56,True,60,False]]
        with self.assertRaisesRegex(ValueError,'transitions'):v.check_rows(self.rows)
    def test_forged_suite(self):
        self.rows['states'][0][2]='DataFlowBench.Other.Persistence'
        with self.assertRaisesRegex(ValueError,'state identity'):v.check_rows(self.rows)
    def test_key_confusion(self):
        self.rows['content'][0][-1]='unrelated'
        with self.assertRaisesRegex(ValueError,'content'):v.check_rows(self.rows)
    def test_missing_endpoint(self):
        self.rows['roles']=[r for r in self.rows['roles'] if r[0]!=55]
        with self.assertRaisesRegex(ValueError,'sink coverage'):v.check_rows(self.rows)
if __name__=='__main__':unittest.main(verbosity=2)
