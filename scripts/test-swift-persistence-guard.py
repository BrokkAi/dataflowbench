#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-persistence-guard.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Guard(unittest.TestCase):
    def setUp(self):self.rows=v.read(v.BASE/'guard-attempt-02/probe/coverage.json')['#select']['tuples']
    def test_retained(self):v.verify()
    def test_no_scope_exclusion(self):
        self.rows=[r for r in self.rows if r[0]!=12]
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
    def test_unknown_mutation_not_clean(self):
        for r in self.rows:
            if r[0]==6:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
    def test_payload_not_clean(self):
        for r in self.rows:
            if r[0]==17:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
    def test_getter_not_ignored(self):
        self.rows=[r for r in self.rows if r[0]!=50]
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
    def test_missing_cfg_not_ignored(self):
        self.rows=[r for r in self.rows if r[0]!=0]
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
    def test_admitted_positive_required(self):
        self.rows=[r for r in self.rows if r[0]!=32]
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows,True)
if __name__=='__main__':unittest.main(verbosity=2)
