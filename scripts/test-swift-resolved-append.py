#!/usr/bin/env python3
"""Portable integrity and semantic mutation tests for resolved-append evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'swift_resolved_append_verifier', ROOT / 'scripts/verify-swift-resolved-append.py')
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)
BASE = ROOT / 'evidence/swift-resolved-native-v1'


class ResolvedAppendPortableTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dfb-swift-resolved-append-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name) / 'swift-resolved-native-v1'
        shutil.copytree(BASE, self.base)

    def path(self, relative):
        return self.base / relative

    def mutate_json(self, relative, change):
        path = self.path(relative)
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value, indent=2) + '\n')

    def refresh_manifests(self):
        directories = sorted((path for path in self.base.rglob('*') if path.is_dir()),
                             key=lambda path: len(path.parts), reverse=True)
        for directory in directories + [self.base]:
            manifest_path = directory / 'manifest.json'
            if not manifest_path.exists():
                continue
            manifest = {
                str(path.relative_to(directory)): verifier.sha(path)
                for path in sorted(directory.rglob('*'))
                if path.is_file() and path != manifest_path
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

    def verify(self):
        return verifier.verify(self.base, root=ROOT, check_original_database=False)

    def test_real_retained_packages_verify_portably(self):
        report = self.verify()
        self.assertEqual([package['package'] for package in report['packages']], [
            'append-attempt-01', 'append-body-attempt-01', 'canonical-append-attempt-01'])
        self.assertEqual(report['qualification'], 'not established')
        self.assertFalse(report['whole_library_qualification'])

    def test_body_control_preserves_body_flow_and_filters_wrong_arity(self):
        plan = verifier.read(self.path('append-body-plan.json'))
        tuples = set(map(tuple, verifier.rows(self.path(
            'append-body-attempt-01/probe/append-flow.json'))))
        labels = plan['control_labels']
        self.assertIn((labels['SOURCE'], labels['BODY_SINK'], 87,
                       'adapter-resolved-experiment'), tuples)
        self.assertNotIn((labels['SOURCE'], labels['ARITY_SINK'], 87,
                          'adapter-resolved-experiment'), tuples)
        self.assertIn((labels['SOURCE'], labels['ARITY_SINK'], 87,
                       'adapter-corrected-stock'), tuples)

    def test_missing_body_flow_is_rejected_after_valid_manifest_refresh(self):
        path = self.path('append-body-attempt-01/probe/append-flow.json')
        value = json.loads(path.read_text())
        value['#select']['tuples'] = [row for row in value['#select']['tuples']
                                      if row != [15, 30, 87, 'adapter-resolved-experiment']]
        path.write_text(json.dumps(value, indent=2) + '\n')
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'append-body flow rows'):
            self.verify()

    def test_rewritten_near_miss_is_rejected(self):
        path = self.path('append-body-attempt-01/probe/append-flow.json')
        value = json.loads(path.read_text())
        value['#select']['tuples'] = [
            row for row in value['#select']['tuples']
            if row != [15, 27, 87, 'adapter-corrected-stock']]
        value['#select']['tuples'].append([15, 27, 87, 'adapter-resolved-experiment'])
        path.write_text(json.dumps(value, indent=2) + '\n')
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'append-body flow rows'):
            self.verify()

    def test_invented_canonical_lane_is_rejected(self):
        relative = ('canonical-append-attempt-01/'
                    'dfb-taint-swift-native-propagator-positive/probe/flow.json')
        self.mutate_json(relative, lambda value: value['#select']['tuples'].append(
            [4, 7, 87, 'invented-adapter-lane']))
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'unknown canonical flow lane'):
            self.verify()

    def test_changed_canonical_source_is_rejected_after_manifest_refresh(self):
        relative = ('canonical-append-attempt-01/'
                    'dfb-taint-swift-native-propagator-positive/probe/main.swift')
        path = self.path(relative)
        path.write_bytes(path.read_bytes() + b'// changed source\n')
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'canonical source changed'):
            self.verify()

    def test_scored_promotion_is_rejected_after_manifest_refresh(self):
        relative = ('canonical-append-attempt-01/'
                    'dfb-taint-swift-native-propagator-positive/observation.json')
        self.mutate_json(relative, lambda value: value.update(scored_activation=True))
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'canonical observation promotion'):
            self.verify()

    def test_wrong_initial_append_rows_are_rejected(self):
        relative = 'append-attempt-01/append-flow.json'
        self.mutate_json(relative, lambda value: value['#select']['tuples'].append(
            [11, 23, 87, 'adapter-resolved-experiment']))
        self.refresh_manifests()
        with self.assertRaisesRegex(ValueError, 'initial append rows'):
            self.verify()


if __name__ == '__main__':
    unittest.main(verbosity=2)
