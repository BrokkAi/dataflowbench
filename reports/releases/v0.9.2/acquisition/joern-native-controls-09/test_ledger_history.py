"""Synthetic hash-scoped tests for the exact 130-row ledger-history gate."""
from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest import mock
import zlib

import native_qualifier as n

ROOT = Path(__file__).resolve().parents[5]
ARCHIVE_DIRECTORY = ROOT / 'reports/releases/v0.9.2/ledger-archives/ledger-130-01'
ARCHIVE_MANIFEST_PATH = ARCHIVE_DIRECTORY / 'manifest.json'
ARCHIVE_MANIFEST_SHA256 = '5408d3d312aa3da502ead1eb3f2273aaa05e7c6505305c487221008bdb5ad812'
ARCHIVE_COMPRESSED_SHA256 = '499c7f844f18723947696657695dbea02f8525cff25bd34c6973f00ec2cd4efd'
ARCHIVE_COMPRESSED_BYTES = 13_299_105
ARCHIVE_LEDGER_BYTES = 126_023_630


class LedgerHistoryTests(unittest.TestCase):
    def fixture(self):
        prefix_statuses = ['completed'] * 103 + ['failed'] * 3 + ['recorder-error'] * 3
        prefix_rows = [n.canonical({'status': status}) for status in prefix_statuses]
        suffix_rows = [
            n.canonical({
                'global_attempt_number': number,
                'attempt_id': attempt_id,
                'group_id': group_id,
                'status': status,
                'target_id': 'bifrost-v0144-01',
                'tool': 'bifrost',
            })
            for number, attempt_id, group_id, status in n.LEDGER_SUFFIX_ROSTER
        ]
        prefix = b''.join(prefix_rows)
        suffix = b''.join(suffix_rows)
        return prefix + suffix, prefix, suffix

    def pins(self, raw, prefix, suffix):
        return {
            'LEDGER': {'path': 'fixture-ledger.jsonl', 'sha256': n.sha(raw)},
            'LEDGER_PREFIX_SHA256': n.sha(prefix),
            'LEDGER_SUFFIX_SHA256': n.sha(suffix),
            'LEDGER_STATUS_COUNTS': {'completed': 122, 'failed': 3, 'recorder-error': 5},
            'LEDGER_SUFFIX_ROSTER': n.LEDGER_SUFFIX_ROSTER,
        }

    def test_synthetic_exact_130_rows_returns_global_counts_and_suffix_numbers(self):
        raw, prefix, suffix = self.fixture()
        with mock.patch.multiple(n, **self.pins(raw, prefix, suffix)):
            result = n.validate_ledger_history(raw)
        self.assertEqual(result, {
            'rows': 130,
            'prefix_rows': 109,
            'suffix_rows': 21,
            'status_counts': {'completed': 122, 'failed': 3, 'recorder-error': 5},
            'suffix_global_attempt_numbers': list(range(111, 132)),
        })

    def test_immutable_130_row_archive_matches_production_pins(self):
        manifest_raw = ARCHIVE_MANIFEST_PATH.read_bytes()
        self.assertEqual(n.sha(manifest_raw), ARCHIVE_MANIFEST_SHA256)
        manifest = json.loads(manifest_raw)
        self.assertEqual(manifest['schema'], 'dataflowbench-v092-ledger-archive/v1')
        self.assertEqual(manifest['archive_path'], 'ledger-v1.jsonl.gz')
        self.assertEqual(manifest['compressed'], {
            'bytes': ARCHIVE_COMPRESSED_BYTES,
            'sha256': ARCHIVE_COMPRESSED_SHA256,
        })
        self.assertEqual(manifest['uncompressed'], {
            'bytes': ARCHIVE_LEDGER_BYTES,
            'sha256': n.LEDGER['sha256'],
        })

        compressed = (ARCHIVE_DIRECTORY / manifest['archive_path']).read_bytes()
        self.assertEqual(len(compressed), ARCHIVE_COMPRESSED_BYTES)
        self.assertEqual(n.sha(compressed), ARCHIVE_COMPRESSED_SHA256)
        decoder = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        raw = decoder.decompress(compressed, ARCHIVE_LEDGER_BYTES + 1)
        self.assertLessEqual(len(raw), ARCHIVE_LEDGER_BYTES)
        self.assertFalse(decoder.unconsumed_tail)
        self.assertTrue(decoder.eof)
        self.assertFalse(decoder.unused_data)
        self.assertEqual(len(raw), ARCHIVE_LEDGER_BYTES)
        self.assertEqual(n.sha(raw), manifest['uncompressed']['sha256'])

        lines = raw.splitlines(keepends=True)
        self.assertEqual(len(lines), 130)
        self.assertTrue(all(line.endswith(b'\n') for line in lines))
        self.assertEqual([n.sha(line) for line in lines], manifest['line_sha256'])
        result = n.validate_ledger_history(raw)
        self.assertEqual(result['rows'], 130)
        self.assertEqual(result['status_counts'], n.LEDGER_STATUS_COUNTS)
        self.assertEqual(n.sha(raw), '79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84')

    def test_prefix_tampering_is_rejected_even_when_full_fixture_digest_is_rebound(self):
        raw, prefix, suffix = self.fixture()
        changed_prefix = prefix.replace(b'completed', b'failed', 1)
        changed = changed_prefix + suffix
        pins = self.pins(changed, changed_prefix, suffix)
        pins['LEDGER_PREFIX_SHA256'] = self.pins(raw, prefix, suffix)['LEDGER_PREFIX_SHA256']
        with mock.patch.multiple(n, **pins), self.assertRaisesRegex(ValueError, 'original109-row byte-prefix'):
            n.validate_ledger_history(changed)

    def test_suffix_tampering_is_rejected_when_full_fixture_digest_is_rebound(self):
        raw, prefix, suffix = self.fixture()
        changed_suffix = suffix.replace(b'bifrost-c-kernel-attempt-04-series-03', b'bifrost-c-kernel-attempt-99-series-03', 1)
        changed = prefix + changed_suffix
        pins = self.pins(changed, prefix, changed_suffix)
        pins['LEDGER_SUFFIX_SHA256'] = self.pins(raw, prefix, suffix)['LEDGER_SUFFIX_SHA256']
        with mock.patch.multiple(n, **pins), self.assertRaisesRegex(ValueError, 'exact21-row suffix digest'):
            n.validate_ledger_history(changed)

    def test_unknown_suffix_attempt_is_rejected_by_ordered_roster(self):
        raw, prefix, suffix = self.fixture()
        changed_suffix = suffix.replace(b'bifrost-c-kernel-attempt-04-series-03', b'bifrost-unknown-attempt-04-series-03', 1)
        changed = prefix + changed_suffix
        with mock.patch.multiple(n, **self.pins(changed, prefix, changed_suffix)), self.assertRaisesRegex(ValueError, 'attempt roster'):
            n.validate_ledger_history(changed)

    def test_reordered_suffix_attempts_are_rejected_by_ordered_roster(self):
        raw, prefix, suffix = self.fixture()
        rows = suffix.splitlines(keepends=True)
        rows[0], rows[1] = rows[1], rows[0]
        changed_suffix = b''.join(rows)
        changed = prefix + changed_suffix
        with mock.patch.multiple(n, **self.pins(changed, prefix, changed_suffix)), self.assertRaisesRegex(ValueError, 'attempt roster'):
            n.validate_ledger_history(changed)

    def test_duplicate_suffix_attempt_is_rejected_by_ordered_roster(self):
        raw, prefix, suffix = self.fixture()
        rows = suffix.splitlines(keepends=True)
        rows[1] = rows[0]
        changed_suffix = b''.join(rows)
        changed = prefix + changed_suffix
        with mock.patch.multiple(n, **self.pins(changed, prefix, changed_suffix)), self.assertRaisesRegex(ValueError, 'attempt roster'):
            n.validate_ledger_history(changed)

    def test_wrong_global_status_counts_are_rejected(self):
        raw, prefix, suffix = self.fixture()
        rows = suffix.splitlines(keepends=True)
        rows[-1] = rows[-1].replace(b'"status":"completed"', b'"status":"failed"', 1)
        changed_suffix = b''.join(rows)
        changed = prefix + changed_suffix
        with mock.patch.multiple(n, **self.pins(changed, prefix, changed_suffix)), self.assertRaisesRegex(ValueError, 'global completed/failed/recorder-error'):
            n.validate_ledger_history(changed)

    def test_truncation_is_rejected(self):
        raw, _, _ = self.fixture()
        with mock.patch.multiple(n, **self.pins(*self.fixture())), self.assertRaisesRegex(ValueError, 'exact130 newline-terminated'):
            n.validate_ledger_history(b''.join(raw.splitlines(keepends=True)[:-1]))

    def test_extra_append_is_rejected(self):
        raw, _, _ = self.fixture()
        extra = n.canonical({'status': 'completed'})
        with mock.patch.multiple(n, **self.pins(*self.fixture())), self.assertRaisesRegex(ValueError, 'exact130 newline-terminated'):
            n.validate_ledger_history(raw + extra)


if __name__ == '__main__':
    unittest.main()
