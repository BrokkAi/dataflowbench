#!/usr/bin/env python3
import gzip
from pathlib import Path
import tempfile
import unittest
from swift_extraction_integrity import inspect_logs


class IntegrityTests(unittest.TestCase):
    def test_missing_logs_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(inspect_logs(d)['ready_for_observation'])

    def test_plain_error_blocks_even_with_success_message(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'extractor.log.txt').write_text('INFO started\nERRO [extractor/compiler] unknown argument\nINFO finalized\n')
            result = inspect_logs(d)
            self.assertFalse(result['ready_for_observation'])
            self.assertEqual(result['errors'][0]['line'], 2)

    def test_compressed_error_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            with gzip.open(Path(d, 'extractor.log.txt.gz'), 'wt') as f:
                f.write('ERROR [extractor/compiler] cannot find URL\n')
            self.assertFalse(inspect_logs(d)['ready_for_observation'])

    def test_clean_log_allows_observation_not_qualification(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'extractor.log.txt').write_text('INFO extracted\nWARN optional information\n')
            self.assertTrue(inspect_logs(d)['ready_for_observation'])

    def test_retained_finalized_attempts_block(self):
        base = Path(__file__).resolve().parents[1] / 'evidence/swift-candidate-native-controls-220'
        attempts = list(base.glob('codeql-*-attempt-02/log/swift/extractor'))
        self.assertEqual(len(attempts), 3)
        for attempt in attempts:
            self.assertFalse(inspect_logs(attempt)['ready_for_observation'])


if __name__ == '__main__':
    unittest.main()
