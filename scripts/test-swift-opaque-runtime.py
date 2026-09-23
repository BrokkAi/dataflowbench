#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-swift-opaque-runtime.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class RuntimeControls(unittest.TestCase):
    def setUp(self):self.observed=v.read(v.BASE/'runtime-attempt-01/runtime.stdout')
    def test_retained(self):v.verify()
    def test_wrong_owner(self):
        self.observed['identities'][0]['owner']='Inherited.Opaque'
        with self.assertRaisesRegex(ValueError,'selector owner'):v.check_observation(self.observed)
    def test_wrong_selector(self):
        self.observed['identities'][0]['selector']='dfbOther:'
        with self.assertRaisesRegex(ValueError,'selector owner'):v.check_observation(self.observed)
    def test_wrong_arity(self):
        self.observed['identities'][1]['signature'].pop()
        with self.assertRaisesRegex(ValueError,'signature'):v.check_observation(self.observed)
    def test_position_zero_propagates(self):
        self.observed['observed']['position0']='tainted'
        with self.assertRaisesRegex(ValueError,'values/position'):v.check_observation(self.observed)
    def test_position_one_drops(self):
        self.observed['observed']['position1']='clean'
        with self.assertRaisesRegex(ValueError,'values/position'):v.check_observation(self.observed)
    def test_block_body_changed(self):
        self.observed['observed']['block']='clean'
        with self.assertRaisesRegex(ValueError,'values/position'):v.check_observation(self.observed)
if __name__=='__main__':unittest.main(verbosity=2)
