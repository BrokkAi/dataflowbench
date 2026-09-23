#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-sanitizer-fresh.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class FreshSanitizer(unittest.TestCase):
    def setUp(self):
        probe=v.BASE/'sanitizer-fresh-attempt-01/probe'
        plan=v.read(v.BASE/'sanitizer-fresh-plan-v1.json')
        self.rows={name:v.read(probe/(name+'.json'))['#select']['tuples'] for name in plan['queries']}

    def test_retained(self):v.verify()

    def test_missing_local_flow(self):
        self.rows['flow']=[row for row in self.rows['flow'] if row[1]!=27]
        with self.assertRaisesRegex(ValueError,'resolved positive/safe flow separation'):v.check_rows(self.rows)

    def test_false_flow_to_safe_sink(self):
        self.rows['flow'].append([17,23,87,v.PROFILE])
        with self.assertRaisesRegex(ValueError,'resolved positive/safe flow separation'):v.check_rows(self.rows)

    def test_lost_real_scalar_barrier(self):
        self.rows['barriers']=[row for row in self.rows['barriers'] if row[:2]!=[21,33]]
        with self.assertRaisesRegex(ValueError,'real scalar barrier missing'):v.check_rows(self.rows)

    def test_local_scalar_barrier_reintroduced(self):
        for row in self.rows['barriers']:
            if row[:2]==[25,33]:row[4]=True
        with self.assertRaisesRegex(ValueError,'local scalar barrier mismatch'):v.check_rows(self.rows)

    def test_plain_wrapper_sanitized(self):
        for row in self.rows['barriers']:
            if row[:2]==[29,34]:row[4]=True
        with self.assertRaisesRegex(ValueError,'plain wrapper incorrectly sanitized'):v.check_rows(self.rows)

    def test_inconsistent_local_int_barrier(self):
        for row in self.rows['barriers']:
            if row[:2]==[13,51] and row[2:4]==['DataFlowBenchTaintSwift','Int']:row[4]=True
        with self.assertRaisesRegex(ValueError,'local barrier coverage'):v.check_rows(self.rows)

    def test_wrong_profile_attribution(self):
        self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile attribution'):v.check_rows(self.rows)

    def test_wrong_source_role(self):
        self.rows['roles'][0][3]='sink'
        with self.assertRaisesRegex(ValueError,'source role'):v.check_rows(self.rows)

    def test_missing_sink_role(self):
        self.rows['roles']=[row for row in self.rows['roles'] if row[:2]!=[31,87]]
        with self.assertRaisesRegex(ValueError,'sink coverage'):v.check_rows(self.rows)

    def test_extra_sink_role(self):
        self.rows['roles'].append([33,32,v.PROFILE,'sink'])
        with self.assertRaisesRegex(ValueError,'sink coverage'):v.check_rows(self.rows)

    def test_changed_fresh_resolved_declaration(self):
        self.rows['conversion-identity'][-1][-1]='OptionalType'
        with self.assertRaisesRegex(ValueError,'fresh resolved declaration match'):v.check_rows(self.rows)

if __name__=='__main__':unittest.main(verbosity=2)
