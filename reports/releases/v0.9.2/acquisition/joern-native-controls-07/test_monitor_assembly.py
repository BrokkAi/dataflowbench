"""Cross-module checks using actual assembled sources, without OS queries."""
import hashlib
from pathlib import Path
import time
import unittest
from unittest import mock

import native_qualifier
import process_reconciliation
import snapshot_query

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]


class MonitorAssemblyTests(unittest.TestCase):
    def test_actual_qualifier_callback_accepts_actual_monitor_api_without_dispatch(self):
        names = {
            'module': 'darwin_native_provider.py',
            'c_source': 'darwin_native_provider.c',
            'header': 'darwin_native_provider.h',
            'library': 'darwin_native_provider.dylib',
            'build_receipt': 'build-receipt.json',
        }
        provider = {'abi_version': 3}
        for role, name in names.items():
            path = BASE / 'darwin-provider' / name
            provider[role] = {
                'path': path.relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        self.assertIs(native_qualifier.process_reconciliation, process_reconciliation)
        callback = native_qualifier.native_provider_query(ROOT, provider)
        # Exercise the real callback and real query function. An invalid existing
        # deadline must return before spawning or querying anything.
        forbidden = mock.Mock(side_effect=AssertionError('OS dispatch forbidden'))
        with mock.patch.dict(process_reconciliation.run_query_child.__kwdefaults__,
                             {'popen': forbidden}):
            value = callback(boundary_deadline=float('nan'), clock=time.monotonic)
        forbidden.assert_not_called()
        self.assertEqual(value['outcome']['status'], 'invalid-boundary-deadline')
        self.assertEqual(value['provider_identity'], 'not-started')
        self.assertIsNone(value['query_child']['pid'])

    def test_utf8_ucomm_padding_uses_bytes_and_preserves_actual_arguments(self):
        command = 'Cräsh pad'
        arguments = '/Applications/Browser.app/handler --message=naïve'
        raw = (snapshot_query.PS_V2_HEADER_BYTES + b'\n' +
               b'777'.rjust(64) + b' ' + b'0.2'.rjust(64) + b' ' +
               command.encode('utf-8').ljust(64) + b' ' +
               arguments.encode('utf-8') + b'\n')
        provider = snapshot_query.PsCommandProvider(time.monotonic() + 2, version='v2')
        rows, table, projected, coverage = provider._parse_v2(raw)
        self.assertEqual(table.encode('utf-8'), raw)
        self.assertEqual(len(rows[0]['ucomm_raw_field'].encode('utf-8')), 64)
        self.assertEqual(projected.split(None, 3)[3].rstrip('\n'), arguments)
        self.assertTrue(process_reconciliation._ucomm_rendered_field_matches(
            {'command': command}, rows[0]))
        self.assertEqual(coverage['raw_stdout_sha256'], hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    unittest.main()
