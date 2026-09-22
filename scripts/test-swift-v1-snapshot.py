#!/usr/bin/env python3
"""Historical views reject drift and never admit arbitrary new inputs."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from swift_population_v2 import ROOT
from swift_v1_snapshot import materialize


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        self.dest = Path(self.temp.name) / 'view'
        self.dest.mkdir()
        shutil.copytree(ROOT / 'cases/taint/swift', self.root / 'cases/taint/swift')
        (self.root / 'populations').mkdir()
        self.manifest = self.root / 'populations/swift-synthetic-v1.json'
        shutil.copyfile(ROOT / 'populations/swift-synthetic-v1.json', self.manifest)
        self.entries = json.loads(self.manifest.read_text())['cases']

    def test_only_exact_v1_inputs_are_selected(self):
        extra = self.root / 'cases/taint/swift/arbitrary/case.json'
        extra.parent.mkdir(); extra.write_text('{}')
        materialize(self.root, self.dest)
        actual = {str(p.relative_to(self.dest)) for p in self.dest.glob('cases/taint/swift/*/case.json')}
        self.assertEqual(actual, {e['path'] for e in self.entries})
        self.assertEqual(len(actual), 90)

    def test_missing_input_fails(self):
        (self.root / self.entries[0]['path']).unlink()
        with self.assertRaises(FileNotFoundError): materialize(self.root, self.dest)

    def test_modified_fixture_fails(self):
        path = self.root / self.entries[0]['fixture_digests'][0]['path']
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'input digest'): materialize(self.root, self.dest)

    def test_duplicate_or_omitted_manifest_entry_fails(self):
        original = self.manifest.read_text()
        for duplicate in [True, False]:
            data = json.loads(original)
            if duplicate: data['cases'][1] = data['cases'][0]
            else: data['cases'].pop()
            self.manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'immutable v1'): materialize(self.root, self.dest)


if __name__ == '__main__': unittest.main()
