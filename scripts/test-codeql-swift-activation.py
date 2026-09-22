#!/usr/bin/env python3
"""Anti-vacuous activation regressions using retained native SARIF."""
import importlib.util
import json
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name('verify-codeql-swift-activation.py')
SPEC = importlib.util.spec_from_file_location('activation', SCRIPT)
activation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activation)


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.positive = json.loads((activation.ROOT / activation.EVIDENCE / 'attempt-04/positive.sarif').read_text())

    def test_real_positive(self):
        activation.check_sarif(self.positive, 1, 2)

    def test_missing_source_is_not_clean_negative(self):
        run = self.positive['runs'][0]
        run['results'] = [r for r in run['results'] if r['message']['text'] == 'Benchmark sink endpoint observed.']
        with self.assertRaises(ValueError):
            activation.check_sarif(self.positive, 0, 2)

    def test_success_boolean_does_not_override_retained_error(self):
        invocation = self.positive['runs'][0]['invocations'][0]
        invocation.setdefault('toolExecutionNotifications', []).append({'level': 'error', 'message': {'text': 'extraction failed'}})
        with self.assertRaises(ValueError):
            activation.check_sarif(self.positive, 1, 2)

    def test_missing_invocation_is_not_success(self):
        self.positive['runs'][0].pop('invocations')
        with self.assertRaises(ValueError):
            activation.check_sarif(self.positive, 1, 2)

    def test_wrong_identity_cannot_count_as_endpoint(self):
        for r in self.positive['runs'][0]['results']:
            if r['ruleId'] == 'dfb/swift-kernel-endpoint-probe':
                r['message']['text'] = 'Benchmark sink endpoint observed.'
        with self.assertRaises(ValueError):
            activation.check_sarif(self.positive, 1, 2)

    def test_empty_decoy(self):
        value = json.loads((activation.ROOT / activation.EVIDENCE / 'attempt-05/positive.sarif').read_text())
        activation.check_sarif(value, 0, 0)
        with self.assertRaises(ValueError):
            activation.check_sarif(value, 0, 2)

    def test_real_historical_error_is_rejected(self):
        value = json.loads((activation.ROOT / activation.EVIDENCE / 'attempt-04/negative-02.sarif').read_text())
        with self.assertRaises(ValueError):
            activation.check_sarif(value, 0, 2)


if __name__ == '__main__':
    unittest.main()
