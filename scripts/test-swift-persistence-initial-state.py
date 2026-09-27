#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-persistence-initial-state.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class InitialState(unittest.TestCase):
    def setUp(self):self.rows=v.read(v.BASE/'attempt-01/probe/coverage.json')['#select']['tuples']
    def test_retained(self):v.verify()
    def test_uninitialized_not_complete(self):
        for r in self.rows:
            if r[0]==7:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows)
    def test_conditional_not_complete(self):
        for r in self.rows:
            if r[0]==11:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows)
    def test_wrong_key_not_complete(self):
        for r in self.rows:
            if r[0]==16:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows)
    def test_later_write_not_complete(self):
        for r in self.rows:
            if r[0]==21:r[1]='Complete'
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows)
    def test_admitted_required(self):
        self.rows=[r for r in self.rows if r[0]!=2]
        with self.assertRaisesRegex(ValueError,'control coverage'):v.check_coverage(self.rows)
if __name__=='__main__':unittest.main(verbosity=2)
