#!/usr/bin/env python3
"""Input/version/profile regressions; never executes native fixture binaries."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from swift_population_v2 import ROOT, audit, runtime_control_allowed, NATIVE


class SwiftV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'cases/taint/swift',self.root/'cases/taint/swift')
        (self.root/'populations').mkdir()
        for version in ['v1','v2']:
            shutil.copyfile(ROOT/f'populations/swift-synthetic-{version}.json',self.root/f'populations/swift-synthetic-{version}.json')

    def mutate(self, operation):
        path=self.root/'populations/swift-synthetic-v2.json'
        data=json.loads(path.read_text());operation(data);path.write_text(json.dumps(data))

    def test_complete_union_retains_v1_and_disjoint_additions(self):
        manifest,new=audit(self.root)
        self.assertEqual(len(manifest['cases']),104);self.assertEqual(len(new),14)
        self.assertEqual(sum(runtime_control_allowed(c) for _,c in new),2)
        self.assertEqual(sum(c['model_profile']=='tool-native' for _,c in new),12)

    def test_missing_new_pair_cannot_shrink_denominator(self):
        self.mutate(lambda m:m['cases'].pop())
        with self.assertRaisesRegex(ValueError,'104 unique'):audit(self.root)

    def test_duplicate_cannot_hide_omission(self):
        self.mutate(lambda m:m['cases'].__setitem__(1,m['cases'][0]))
        with self.assertRaisesRegex(ValueError,'104 unique'):audit(self.root)

    def test_existing_v1_member_cannot_be_relabelled(self):
        self.mutate(lambda m:m['cases'][0].update(model_profile='tool-native'))
        with self.assertRaisesRegex(ValueError,'v1 member changed'):audit(self.root)

    def test_v1_bytes_remain_immutable(self):
        path=self.root/'populations/swift-synthetic-v1.json';path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'immutable v1'):audit(self.root)

    def test_fixture_change_detected(self):
        path=self.root/'cases/taint/swift/native-source-sink-positive/main.swift'
        path.write_text(path.read_text()+'\n//changed\n')
        with self.assertRaisesRegex(ValueError,'fixture digest'):audit(self.root)

    def test_no_native_template_can_enter_runtime_control_path(self):
        for template in NATIVE:
            for tier in ['modeling','language-extension','core']:
                for profile in ['tool-native','benchmark-controlled']:
                    self.assertFalse(runtime_control_allowed({'template_id':template,'score_tier':tier,'model_profile':profile}))

    def test_extra_unregistered_fixture_rejected(self):
        path=self.root/'cases/taint/swift/unregistered/case.json';path.parent.mkdir();path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'complete file set'):audit(self.root)


if __name__=='__main__':unittest.main()
