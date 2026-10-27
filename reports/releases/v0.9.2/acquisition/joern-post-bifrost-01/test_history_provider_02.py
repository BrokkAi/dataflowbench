from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest
from unittest import mock
HERE = Path(__file__).parent
ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
spec = importlib.util.spec_from_file_location('history_provider_under_test', HERE / 'history_provider_02.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class HistoryProviderTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ref = {'path': m.DESCRIPTOR_PATH, 'sha256': m.DESCRIPTOR_SHA}
        cls.d = m.document(ROOT, cls.ref)
        cls.c = m.document(ROOT, cls.d['core'])
        cls.stage = m.document(ROOT, cls.d['stage02'])
        cls.batch = m.document(ROOT, cls.d['batch'])
        cls.history = m.document(ROOT, cls.d['resume_history'])
        cls.raw = m.bound(ROOT, {k: cls.d['ledger_prefix'][k] for k in ['path', 'sha256']})
        (cls.lines, cls.rows) = m.ledger_rows(cls.raw)

    def documents(self, d=None, c=None, stage=None, rows=None):
        return m.validate_documents(d or self.d, c or self.c, stage or self.stage, self.batch, self.history, self.lines, rows or self.rows)

    def test_actual_complete_reader(self):
        result = m.validate_tail(ROOT, self.ref)
        self.assertEqual(len(result['source_contexts']), 9)
        self.assertEqual(len(result['retained20']), 20)
        self.assertEqual(result['live_rows_observed'], 109)
        self.assertEqual(result['counters']['joern-swift-common108'], 4)
        self.assertEqual(result['counters']['bifrost-smoke'], 3)
        self.assertFalse(result['execution_authorized'])

    def test_wrong_descriptor_digest(self):
        with self.assertRaisesRegex(m.HistoryError, 'immutable descriptor'):
            m.validate_tail(ROOT, {**self.ref, 'sha256': '0' * 64})

    def test_wrong_descriptor_path(self):
        with self.assertRaisesRegex(m.HistoryError, 'immutable descriptor'):
            m.validate_tail(ROOT, {**self.ref, 'path': 'elsewhere.json'})

    def test_ninth_context_removed(self):
        d = copy.deepcopy(self.d)
        d['source_contexts'].pop(next(iter(d['source_contexts'])))
        with self.assertRaisesRegex(m.HistoryError, 'nine source'):
            self.documents(d=d)

    def test_context_source_rebound(self):
        c = copy.deepcopy(self.c)
        next(iter(c['source_contexts'].values()))['source_commit'] = '0' * 40
        with self.assertRaisesRegex(m.HistoryError, 'nine source'):
            self.documents(c=c)

    def test_wrong_original89_prefix(self):
        d = copy.deepcopy(self.d)
        d['prefixes']['89'] = '0' * 64
        with self.assertRaisesRegex(m.HistoryError, 'prefix closure'):
            self.documents(d=d)

    def test_missing_retained_group(self):
        d = copy.deepcopy(self.d)
        d['replacements'].pop()
        with self.assertRaisesRegex(m.HistoryError, 'full20'):
            self.documents(d=d)

    def test_unknown_consumed_event(self):
        d = copy.deepcopy(self.d)
        d['consumed_events'].append(copy.deepcopy(d['consumed_events'][0]))
        with self.assertRaisesRegex(m.HistoryError, 'consumed event'):
            self.documents(d=d)

    def test_unknown_descriptor_field(self):
        d = dict(self.d, approval='invented')
        with self.assertRaisesRegex(m.HistoryError, 'fields'):
            self.documents(d=d)

    def test_wrong_stage109(self):
        s = dict(self.stage, ledger_rows=110)
        with self.assertRaisesRegex(m.HistoryError, 'stage02'):
            self.documents(stage=s)

    def test_original_provider_bytes_unchanged(self):
        r = self.d['original89_provider']
        self.assertEqual(m.sha(m.bound(ROOT, r)), r['sha256'])

    def test_symlink_denial(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / 'file').write_text('data')
            (root / 'link').symlink_to(root / 'file')
            with self.assertRaisesRegex(m.HistoryError, 'symlink'):
                m.stable(root, 'link')

    def test_missing_input_denial(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                m.stable(Path(td).resolve(), 'missing')

    def test_bound_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / 'file').write_text('{}')
            with self.assertRaisesRegex(m.HistoryError, 'digest differs'):
                m.bound(root, {'path': 'file', 'sha256': '0' * 64})

    def test_unregistered_live_tail_rejected_exact(self):
        actual = m.stable

        def read(root, path):
            return self.raw + b'{"synthetic_future_row":true}\n' if path == m.LIVE_LEDGER else actual(root, path)
        with mock.patch.object(m, 'stable', side_effect=read):
            with self.assertRaisesRegex(m.HistoryError, 'unregistered live tail'):
                m.validate_tail(ROOT, self.ref)

    def test_explicit_prefix_history_does_not_authorize_later_rows(self):
        actual = m.stable

        def read(root, path):
            return self.raw + b'{"synthetic_future_row":true}\n' if path == m.LIVE_LEDGER else actual(root, path)
        with mock.patch.object(m, 'stable', side_effect=read):
            result = m.validate_tail(ROOT, self.ref, live_mode='prefix-history-only')
        self.assertEqual(result['live_rows_observed'], 110)
        self.assertFalse(result['later_rows_authorized'])
        self.assertEqual(result['ledger_prefix']['rows'], 109)

    def test_unknown_live_mode(self):
        with self.assertRaisesRegex(m.HistoryError, 'unknown live'):
            m.validate_tail(ROOT, self.ref, live_mode='automatic')

    def test_actual_api_matches_candidate01_except_explicit_next_metadata(self):
        spec = importlib.util.spec_from_file_location('history_provider_01_comparison', HERE / 'history_provider_01.py')
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        actual = m.validate_tail(ROOT, self.ref)
        next_metadata = actual.pop('joern_next_attempt')
        self.assertEqual(actual, original.validate_tail(ROOT, self.ref))
        self.assertEqual(next_metadata, {'group_id': 'joern-swift-common108', 'consumed_global_attempt': 4, 'next_global_attempt': 5, 'execution_authorized': False, 'permit': False})

    def test_reused_global_attempt_across_series_rejected(self):
        rows = copy.deepcopy(self.rows)
        first = rows[0]
        match = m.re.fullmatch(m.re.escape(first['group_id']) + '-attempt-(\\d+)-series-(\\d+)', first['attempt_id'])
        duplicate = copy.deepcopy(first)
        duplicate['attempt_id'] = first['group_id'] + '-attempt-' + match.group(1) + '-series-999'
        rows.append(duplicate)
        with self.assertRaisesRegex(m.HistoryError, 'reused global group/attempt'):
            m.consumed_attempts(rows, self.d['consumed_events'][0], self.c['replacement_groups'])

    def test_joern_consumed_three_rejected(self):
        rows = [row for row in self.rows if row['attempt_id'] != 'joern-swift-common108-attempt-04-series-02']
        rows = [row for row in rows if not (row['group_id'] == 'joern-swift-common108' and '-attempt-04-' in row['attempt_id'])]
        with self.assertRaisesRegex(m.HistoryError, 'Joern consumed counter must be four'):
            m.consumed_attempts(rows, self.d['consumed_events'][0], self.c['replacement_groups'])

    def test_joern_consumed_five_rejected(self):
        rows = copy.deepcopy(self.rows)
        joern = next((row for row in rows if row['group_id'] == 'joern-swift-common108'))
        extra = copy.deepcopy(joern)
        extra['attempt_id'] = 'joern-swift-common108-attempt-05-series-99'
        rows.append(extra)
        with self.assertRaisesRegex(m.HistoryError, 'Joern consumed counter must be four'):
            m.consumed_attempts(rows, self.d['consumed_events'][0], self.c['replacement_groups'])

    def test_foreign_descriptor_schema_rejected(self):
        descriptor = dict(self.d, schema='v092-invented-descriptor/v1')
        with self.assertRaisesRegex(m.HistoryError, 'descriptor authority differs'):
            self.documents(d=descriptor)

    def test_descriptor_missing_field_rejected(self):
        descriptor = dict(self.d)
        descriptor.pop('publication_hold')
        with self.assertRaisesRegex(m.HistoryError, 'descriptor fields differ'):
            self.documents(d=descriptor)

    def test_descriptor_cannot_grant_execution(self):
        descriptor = dict(self.d, execution_authorized=True)
        with self.assertRaisesRegex(m.HistoryError, 'descriptor authority differs'):
            self.documents(d=descriptor)
if __name__ == '__main__':
    unittest.main()
