#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verify', Path(__file__).with_name('verify-swift-opaque-v3.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Population(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ['populations/swift-opaque-v3.json', 'populations/swift-synthetic-v2.json',
                     'evidence/swift-opaque-objc-v1/control-v2/main.swift']:
            target = self.root/path; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(module.ROOT/path, target)
        shutil.copytree(module.ROOT/'populations/swift-opaque-v3', self.root/'populations/swift-opaque-v3')

    def mutate(self, change):
        path = self.root/'populations/swift-opaque-v3.json'
        data = json.loads(path.read_text()); change(data); path.write_text(json.dumps(data))

    def test_balanced_prospective_inputs(self):
        self.assertEqual(len(module.verify(self.root)['cases']), 4)

    def test_missing_pair_rejected(self):
        self.mutate(lambda m: m['cases'].pop())
        with self.assertRaisesRegex(ValueError, 'balanced'): module.verify(self.root)

    def test_source_mutation_rejected(self):
        path = next((self.root/'populations/swift-opaque-v3').glob('*/main.swift'))
        path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'digest'): module.verify(self.root)

    def test_path_escape_rejected(self):
        self.mutate(lambda m: m['cases'][0].update(case_path='../case.json'))
        with self.assertRaisesRegex(ValueError, 'path'): module.verify(self.root)

    def test_unregistered_input_rejected(self):
        (self.root/'populations/swift-opaque-v3/extra.swift').write_text('')
        with self.assertRaisesRegex(ValueError, 'file closure'): module.verify(self.root)

    def test_activation_rejected(self):
        self.mutate(lambda m: m.update(scored_activation=True))
        with self.assertRaisesRegex(ValueError, 'prospective'): module.verify(self.root)

if __name__ == '__main__': unittest.main(verbosity=2)
