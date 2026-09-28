#!/usr/bin/env python3
"""Exercise prospective runner pinning and bounded-failure behavior without CodeQL."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('probe-swift-endpoints-v1.py')
spec = importlib.util.spec_from_file_location('endpoint_probe', PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def test_late_success_and_timeout_stop_remaining_selection(self):
        for record in [dict(timed_out=False, elapsed_seconds=75.001, exit_status=0),
                       dict(timed_out=True, elapsed_seconds=75, exit_status=-15)]:
            with patch.object(probe.process, 'run', return_value=record):
                with self.assertRaises(TimeoutError) as caught:
                    probe.invoke(['codeql'], Path('/unused'), 'query', 75)
                self.assertEqual(probe.failure_stop(caught.exception), 'StoppedAfterUncertainCleanup')

    def test_cleanup_uncertainty_cannot_be_completed(self):
        with patch.object(probe.process, 'run', side_effect=probe.process.ProcessCleanupError('tracking unavailable')):
            with self.assertRaises(probe.process.ProcessCleanupError) as caught:
                probe.invoke(['codeql'], Path('/unused'), 'query', 75)
            self.assertEqual(probe.failure_stop(caught.exception), 'StoppedAfterUncertainCleanup')

    def test_nonzero_exit_stops_diagnostics(self):
        with patch.object(probe.process, 'run', return_value=dict(timed_out=False, elapsed_seconds=1, exit_status=2)):
            with self.assertRaisesRegex(ValueError, 'CommandFailed:query') as caught:
                probe.invoke(['codeql'], Path('/unused'), 'query', 75)
            self.assertEqual(probe.failure_stop(caught.exception), 'StoppedAfterDiagnosticFailure')

    def test_new_output_only_and_pinned_paths(self):
        # The registration audit validates actual files, not expected digests
        # embedded in this test. It remains useful after runner changes.
        registration_path = probe.ADAPTER / 'registration.json'
        if not registration_path.exists():
            self.fail('Missing prospective registration')
        registration = probe.read(registration_path)
        for name, digest in registration['files'].items():
            with self.subTest(file=name):
                self.assertEqual(probe.sha(probe.ROOT / name), digest)
        self.assertEqual(len(registration['retained_case_ids']), 3)
        self.assertEqual(set(registration['retained_case_ids']), set(registration['retained_observations']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
