#!/usr/bin/env python3
"""Regression guards for identity coverage, joins, bytes and typed outcomes."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('coverage_audit', Path(__file__).with_name('audit-swift-coverage.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = module.ROOT
        paths = list((source / 'cases').rglob('case.json'))
        paths += list((source / 'cases/taint/swift').rglob('*.swift'))
        paths += [source / 'docs/swift-kernel.md', source / 'populations/swift-synthetic-v1.json']
        for report_path in source.glob('reports/*-swift-*.json'):
            paths.append(report_path)
            paths += [source / row['raw_output'] for row in json.loads(report_path.read_text())['results']]
        for path in paths:
            target = self.root / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

    def mutate_report(self, change):
        path = self.root / 'reports/codeql-swift-kernel.json'
        report = json.loads(path.read_text())
        change(report)
        path.write_text(json.dumps(report))

    def test_complete_and_unresolved_remain_distinct(self):
        result = module.audit(self.root)
        self.assertEqual(len(result['families']), 58)
        self.assertEqual(sum(len(f['cases']) for f in result['families']), 90)
        self.assertEqual(result['identity_counts']['deferred'], 9)
        self.assertFalse(result['epic_complete'])
        self.assertEqual(sum(r['outcomes']['runner-error'] for r in result['reports']), 54)

    def test_duplicate_row_cannot_hide_omission(self):
        self.mutate_report(lambda r: r['results'].__setitem__(1, r['results'][0]))
        with self.assertRaisesRegex(ValueError, 'report membership'):
            module.audit(self.root)

    def test_missing_family_rejected(self):
        path = self.root / 'docs/swift-kernel.md'
        path.write_text('\n'.join(line for line in path.read_text().splitlines()
                                  if not line.startswith('| `dfb-template-native-sanitizer`')))
        with self.assertRaisesRegex(ValueError, 'contract/registry mismatch'):
            module.audit(self.root)

    def test_fixture_bytes_are_bound(self):
        path = next((self.root / 'cases/taint/swift').rglob('main.swift'))
        path.write_text(path.read_text() + '\n// changed\n')
        with self.assertRaisesRegex(ValueError, 'fixture digest'):
            module.audit(self.root)

    def test_uncertainty_cannot_be_promoted(self):
        self.mutate_report(lambda r: r['results'][0].update(outcome='not-reached'))
        with self.assertRaisesRegex(ValueError, 'normalization transition'):
            module.audit(self.root)

    def test_unknown_outcome_rejected(self):
        self.mutate_report(lambda r: r['results'][0].update(outcome='clean'))
        with self.assertRaisesRegex(ValueError, 'unknown outcome'):
            module.audit(self.root)


if __name__ == '__main__':
    unittest.main()
