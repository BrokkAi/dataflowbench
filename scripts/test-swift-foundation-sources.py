#!/usr/bin/env python3
"""Mutation regressions for retained Foundation source observations."""
import copy
import gzip
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = ROOT / 'evidence/swift-foundation-sources-v1/control-attempt-01'
PLAN_PATH = ROOT / 'evidence/swift-foundation-sources-v1/control-plan.json'

spec = importlib.util.spec_from_file_location(
    'verify_swift_foundation_sources',
    Path(__file__).with_name('verify-swift-foundation-sources.py'),
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class SemanticMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [ATTEMPT / 'roles.json', ATTEMPT / 'flow.json', PLAN_PATH]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise AssertionError('required control records missing: ' + ', '.join(missing))
        cls.roles = verifier.read(required[0])['#select']['tuples']
        cls.flows = verifier.read(required[1])['#select']['tuples']
        cls.plan = verifier.read(PLAN_PATH)
        cls.labels = cls.plan['labels']

    def assert_semantics_rejected(self, roles=None, flows=None):
        with self.assertRaises(AssertionError):
            verifier.verify_semantics(
                self.roles if roles is None else roles,
                self.flows if flows is None else flows,
                self.plan,
            )

    def test_missing_negative_identity_fails(self):
        identities = verifier.read(ATTEMPT / 'identity.json')['#select']['tuples']
        identities = [r for r in identities if r[0] != self.labels['LOCAL_ENV']]
        with self.assertRaises(AssertionError):
            verifier.verify_identities(identities, self.plan)

    def test_actual_attempt_records_pass(self):
        verifier.verify_semantics(self.roles, self.flows, self.plan)

    def test_empty_corrected_flows_fail(self):
        flows = [row for row in self.flows if row[3] != 'adapter-corrected']
        self.assert_semantics_rejected(flows=flows)

    def test_added_near_miss_source_fails(self):
        roles = copy.deepcopy(self.roles)
        roles.append([self.labels['LOCAL_ENV'], 1, 'adapter-corrected', 'environment'])
        self.assert_semantics_rejected(roles=roles)

    def test_added_near_miss_source_to_negative_sink_flow_fails(self):
        flows = copy.deepcopy(self.flows)
        flows.append([
            self.labels['LOCAL_ENV'], self.labels['NEG_LOCAL'], 36,
            'adapter-corrected',
        ])
        self.assert_semantics_rejected(flows=flows)

    def test_missing_negative_sink_fails(self):
        roles = [
            row for row in self.roles
            if not (row[0] == self.labels['NEG_SAFE'] and row[3] == 'sink')
        ]
        self.assert_semantics_rejected(roles=roles)

    def test_vendor_profile_flow_leak_fails(self):
        flows = copy.deepcopy(self.flows)
        corrected = next(
            row for row in flows
            if row[0] == self.labels['SOURCE_ENV']
            and row[1] == self.labels['POS_ENV_RUN']
            and row[3] == 'adapter-corrected'
        )
        flows.append([corrected[0], corrected[1], corrected[2], 'vendor-native'])
        self.assert_semantics_rejected(flows=flows)


class LogMutationTests(unittest.TestCase):
    def test_compressed_erro_diagnostic_fails(self):
        with tempfile.TemporaryDirectory(prefix='dfb-foundation-source-test-') as directory:
            log = Path(directory) / 'extractor.log.txt.gz'
            with gzip.open(log, 'wt') as stream:
                stream.write('INFO extraction started\n')
                stream.write('ERRO [extractor/compiler] missing resolved property\n')
                stream.write('INFO extraction finalized\n')
            with self.assertRaises(AssertionError):
                verifier.verify_logs(directory)


if __name__ == '__main__':
    unittest.main(verbosity=2)
