#!/usr/bin/env python3
import unittest,importlib.util
from pathlib import Path
from swift_v3_runner75 import enforce_deadline,completed_analysis_elapsed
from swift_v3_verify75 import verify_case
from swift_v3_reports75 import inputs,ROOT
spec=importlib.util.spec_from_file_location('oldtests',Path(__file__).with_name('test-swift-v3-verifier.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
class Boundaries(unittest.TestCase):
    def test_deadline_boundary_and_late_success(self):
        enforce_deadline({'timed_out':False,'elapsed_seconds':.239},.239)
        with self.assertRaises(TimeoutError):enforce_deadline({'timed_out':False,'elapsed_seconds':.345},.239)
        self.assertEqual(completed_analysis_elapsed(75),75)
        with self.assertRaises(TimeoutError):completed_analysis_elapsed(75.00001)
    def test_contract(self):
        _,contract,cases,_,_=inputs(ROOT)
        self.assertEqual(contract['phases']['analysis']['wall_clock_seconds'],75)
        self.assertEqual(contract['phases']['extraction']['wall_clock_seconds'],150)
        self.assertEqual(len(cases),108)
    def test_late_success_is_typed_timeout_not_completed(self):
        t=old.Verify('test_complete');t.setUp();self.addCleanup(t.doCleanups)
        t.raw.update(execution_status='attempted',failure_kind='timeout',outcome='inconclusive',diagnostics=['BudgetExhausted:flow-decode'],analysis_elapsed_seconds=75.1)
        rec=t.raw['commands']['flow-decode'];rec.update(elapsed_seconds=.345,deadline_seconds=.239);t.sync()
        verify_case(Path('/repo'),t.base,t.case,t.raw,t.paths)
        t.raw['execution_status']='completed'
        with self.assertRaisesRegex(ValueError,'successful phase overrun'):verify_case(Path('/repo'),t.base,t.case,t.raw,t.paths)
if __name__=='__main__':unittest.main(verbosity=2)
