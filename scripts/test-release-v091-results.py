#!/usr/bin/env python3
"""Reject stale freezes, changed report sets and fixture substitution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('gate', Path(__file__).with_name('check-release-v091-results.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class FreezeGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.revision = 'a' * 40
        self.fixture = 'sha256:' + 'b' * 64
        self.fresh = [{'path': f'reports/fresh/{index}.json', 'sha256': 'c' * 64} for index in range(20)]
        self.carried = [{'path': f'reports/carried/{index}.json', 'normalized_report_sha256': 'd' * 64} for index in range(72)]
        self.cases = [{'id': 'retained-case', 'fixture_digests': [{'path': 'fixture.rs', 'sha256': 'e' * 64}]}]
        self.manifest = {'schema_version': 1, 'claim': {'scope': 'release'},
                         'benchmark': {'release': 'v0.9.1', 'revision': self.revision,
                                       'dirty': False, 'fixture_revision': self.fixture},
                         'cases': self.cases,
                         'reports': [{'path': entry['path'], 'normalized_report_sha256': entry['sha256']} for entry in self.fresh] + self.carried}
        self.write('reports/releases/v0.9.1/plan.json', {'fixture_revision': self.fixture, 'carried_reports': self.carried, 'baseline_freeze': {'path': 'baseline.json'}})
        self.write('reports/releases/v0.9.1/evidence-validation.json', {'fresh_reports': self.fresh})
        self.write('baseline.json', {'cases': self.cases})

    def write(self, path, value):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value))

    def validate(self, manifest=None):
        self.write('reports/freeze.json', manifest or self.manifest)
        return gate.validate_manifest(self.root, self.revision)

    def test_exact_fresh_and_carried_manifest_is_accepted(self):
        self.assertEqual(self.validate(), self.manifest)

    def test_old_release_or_branch_revision_is_rejected(self):
        for key, value in [('release', 'v0.9.0'), ('revision', 'f' * 40), ('dirty', True)]:
            with self.subTest(key=key):
                manifest = copy.deepcopy(self.manifest)
                manifest['benchmark'][key] = value
                with self.assertRaisesRegex(ValueError, 'exact merged'):
                    self.validate(manifest)

    def test_missing_or_substituted_report_is_rejected(self):
        for mutation in ('missing', 'substitute'):
            manifest = copy.deepcopy(self.manifest)
            if mutation == 'missing':
                manifest['reports'].pop()
            else:
                manifest['reports'][0]['normalized_report_sha256'] = 'f' * 64
            with self.assertRaisesRegex(ValueError, '20 fresh and 72 carried'):
                self.validate(manifest)

    def test_changed_fixture_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['cases'][0]['fixture_digests'][0]['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'population or fixture'):
            self.validate(manifest)


if __name__ == '__main__':
    unittest.main()
