#!/usr/bin/env python3
"""Negative controls for the retained semantic evidence gate."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('verify_foundation', Path(__file__).with_name('verify-swift-foundation-identity.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        attempt = module.EVIDENCE / 'control-attempt-03'
        self.roles = module.read(attempt / 'roles.json')['#select']['tuples']
        self.flows = module.read(attempt / 'flow.json')['#select']['tuples']

    def test_actual_positive_and_near_miss_evidence(self):
        module.verify_rows(self.roles, self.flows)

    def test_empty_corrected_output_cannot_pass(self):
        flows = [r for r in self.flows if r[3] != 'adapter-corrected']
        with self.assertRaises(AssertionError):
            module.verify_rows(self.roles, flows)

    def test_lookalike_false_flow_cannot_pass(self):
        flows = copy.deepcopy(self.flows) + [[13, 18, 5, 'adapter-corrected']]
        with self.assertRaises(AssertionError):
            module.verify_rows(self.roles, flows)

    def test_safe_call_false_flow_cannot_pass(self):
        flows = copy.deepcopy(self.flows) + [[13, 22, 36, 'adapter-corrected']]
        with self.assertRaises(AssertionError):
            module.verify_rows(self.roles, flows)

    def test_missing_safe_sink_invalidates_nonflow_control(self):
        roles = [r for r in self.roles if not (r[0] == 22 and r[2] == 'adapter-corrected')]
        with self.assertRaises(AssertionError):
            module.verify_rows(roles, self.flows)


if __name__ == '__main__':
    unittest.main()
