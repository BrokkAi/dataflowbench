#!/usr/bin/env python3
"""Replay mutations independent of retained finding expectations."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from swift_native_composed import ROOT, replay, sha

class Replay(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        # Only the replay attempt is copied; immutable inputs remain in ROOT.
        self.attempt=self.root/'attempt-01'
        shutil.copytree(ROOT/'evidence/swift-native-composed-v1/attempt-01',self.attempt)

    def test_changed_raw_bytes_rejected(self):
        path=next(self.attempt.glob('*/flow.json'));path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'artifact digest'):replay(ROOT,self.attempt)

    def test_missing_case_rejected_even_with_updated_digest(self):
        path=self.attempt/'run.json';run=json.loads(path.read_text());run['cases'].pop(next(iter(run['cases'])))
        path.write_text(json.dumps(run))
        manifest=self.attempt/'manifest.json';m=json.loads(manifest.read_text());m['run.json']=sha(path);manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'complete native selection'):replay(ROOT,self.attempt)

if __name__=='__main__':unittest.main(verbosity=2)
