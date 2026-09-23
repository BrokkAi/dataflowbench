#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-swift-conversion-diagnostics.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Diagnostics(unittest.TestCase):
    def test_retained(self):self.assertFalse(v.verify()['scored_activation'])
    def test_false_flow_reintroduced(self):
        rows=v.read(v.BASE/'conversion-initializer-attempt-01/flow.json')['#select']['tuples'];rows.append([15,42,87,'adapter-patched-resolved-initializer'])
        with self.assertRaisesRegex(ValueError,'comparison changed'):v.check_correction(rows)
    def test_lost_positive(self):
        rows=v.read(v.BASE/'conversion-initializer-attempt-01/flow.json')['#select']['tuples'];rows=[r for r in rows if r[3]!='adapter-patched-resolved-initializer']
        with self.assertRaisesRegex(ValueError,'comparison changed'):v.check_correction(rows)
    def test_invented_summary(self):
        rows={n:v.read(v.BASE/'conversion-body-trace-attempt-01'/(n+'.json'))['#select']['tuples'] for n in ['body-flow','body-summary','initializer-heuristic']};rows['body-summary'][-1][3]=True
        with self.assertRaisesRegex(ValueError,'summary attachment'):v.check_trace(rows)
    def test_missing_heuristic(self):
        rows={n:v.read(v.BASE/'conversion-body-trace-attempt-01'/(n+'.json'))['#select']['tuples'] for n in ['body-flow','body-summary','initializer-heuristic']};rows['initializer-heuristic']=[]
        with self.assertRaisesRegex(ValueError,'heuristic witness missing'):v.check_trace(rows)
    def test_ssa_body_positive_must_survive(self):
        before=v.read(v.BASE/'conversion-self-attempt-01/self-assignment.json')['#select']['tuples']
        after=v.read(v.BASE/'conversion-ssa-attempt-01/self-assignment.json')['#select']['tuples']
        flows=v.read(v.BASE/'conversion-ssa-attempt-01/flow.json')['#select']['tuples']
        flows=[r for r in flows if not (r[1]==35 and r[3]=='adapter-patched-ssa-resolved')]
        with self.assertRaisesRegex(ValueError,'body/near-miss'):v.check_ssa(before,after,flows)
    def test_ssa_rhs_link_must_be_present(self):
        before=v.read(v.BASE/'conversion-self-attempt-01/self-assignment.json')['#select']['tuples']
        after=v.read(v.BASE/'conversion-ssa-attempt-01/self-assignment.json')['#select']['tuples']
        after[-1][2]=False
        flows=v.read(v.BASE/'conversion-ssa-attempt-01/flow.json')['#select']['tuples']
        with self.assertRaisesRegex(ValueError,'linkage missing'):v.check_ssa(before,after,flows)
if __name__=='__main__':unittest.main(verbosity=2)
