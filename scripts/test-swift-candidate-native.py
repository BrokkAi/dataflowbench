#!/usr/bin/env python3
"""Catalog language matching must not conflate Swift with names or near misses."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('verify-swift-candidate-native.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CatalogTests(unittest.TestCase):
    def test_exact_language_with_case_normalization(self):
        rows = [{'name': 'positive', 'language': 'SWIFT'},
                {'name': 'near-miss', 'language': 'swiftish'},
                {'name': 'swift', 'language': 'java'}]
        self.assertEqual(audit.language_records(rows, 'swift'), [rows[0]])

    def test_real_catalog_positive_and_absence_are_scoped(self):
        rows = audit.read(audit.BASE / 'joern-catalog/querydb.json')
        self.assertEqual(len(audit.language_records(rows, 'c')), 27)
        self.assertEqual(audit.language_records(rows, 'swift'), [])
        summary = audit.read(audit.BASE / 'joern-catalog/summary.json')
        self.assertIsNone(summary['capability_decision'])

    def test_process_environment_sink_is_not_a_source(self):
        rows = audit.read(audit.BASE / 'codeql-models/model-rows.json')
        matches = [r for r in rows if r['fields'][1] == 'Process' and r['fields'][3] == 'environment']
        self.assertEqual([r['role'] for r in matches], ['sink'])
        audit.verify_models()

    def test_catalog_mismatch_cannot_be_reported_as_complete(self):
        original = audit.read
        def altered(path):
            value = original(path)
            if path.name == 'loaded-querydb.json':
                return value[:-1]
            return value
        with mock.patch.object(audit, 'read', side_effect=altered), self.assertRaises(AssertionError):
            audit.verify_catalog()


if __name__ == '__main__':
    unittest.main()
