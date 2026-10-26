#!/usr/bin/env python3
"""Small review/reader/consumer regressions; never touch retained evidence."""

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('package_tool', Path(__file__).with_name('package-evidence.py'))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

REAL_BINARY = None
if '--binary' in sys.argv:
    argument = sys.argv.index('--binary')
    REAL_BINARY = Path(sys.argv[argument + 1]).resolve()
    del sys.argv[argument:argument + 2]


class PackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'root'
        self.scope = self.root / 'evidence'
        self.scope.mkdir(parents=True)
        self.package = self.base / 'package'
        self.report = {
            'schema_version': 1, 'tool': 'example', 'tool_version': '1',
            'tool_build_identity': 'example-build', 'adapter_version': '1',
            'cold_or_warm': 'cold', 'started_at_unix_seconds': 1, 'ended_at_unix_seconds': 2,
            'configuration_hash': 'config', 'fixture_revision': 'fixtures',
            'results': [
                {'case_id': f'case-{i}', 'outcome': outcome, 'duration_ms': i,
                 'peak_memory_mb': None, 'raw_output': f'evidence/raw/{i}.json',
                 'diagnostics': ['BudgetExhausted' if outcome == 'inconclusive' else 'detail'],
                 'source_anchors': ['source'], 'sink_anchors': ['sink'],
                 'witness_checkpoints': [], 'unknown_future_field': {'proof': None}}
                for i, outcome in enumerate(sorted(tool.OUTCOMES))],
        }
        self.report_bytes = (json.dumps(self.report, indent=2) + '\n').encode()
        (self.scope / 'report.json').write_bytes(self.report_bytes)
        self.ledger = (b'{"status":"failed","exit_code":1,"nested":{"error":"failure"}}\r\n'
                       b'{"status":"started-unclosed-unknown","attempt_id":"two","nullable":null}\n')
        (self.scope / 'ledger.jsonl').write_bytes(self.ledger)
        (self.scope / 'hold.md').write_bytes(b'Publication hold; partial matrix.\n')

    def create(self):
        return tool.create(self.root, 'evidence', self.package,
                           ['evidence/report.json'], ['evidence/ledger.jsonl'], ['evidence/hold.md'], 1024)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(Path(tool.__file__)), *map(str, args)],
                              capture_output=True, check=False)

    def test_concise_review_preserves_denominators_states_identity_and_attempts(self):
        self.create()
        result = tool.verify(self.package)
        self.assertEqual(result['review'], 'verified')
        summary = json.loads((self.package / 'review/summary.json').read_bytes())
        report, attempts, _ = summary['inputs']
        self.assertEqual(report['result_count'], 5)
        self.assertEqual(report['outcome_counts'], {v: 1 for v in tool.OUTCOMES})
        self.assertEqual(report['metadata']['fixture_revision'], 'fixtures')
        self.assertFalse(summary['qualification'])
        self.assertEqual(attempts['row_count'], 2)
        with (self.package / 'review/cases.csv').open() as stream:
            cases = list(csv.DictReader(stream))
        self.assertEqual(len(cases), 5)
        for row, original in zip(cases, self.report['results']):
            self.assertEqual(row['result_sha256'], tool.hashlib.sha256(tool.encoded(original)).hexdigest())
            self.assertEqual(tool.pointer(self.report, row['detail_pointer']), original)
        rows = [json.loads(line) for line in (self.package / 'review/attempts.jsonl').read_bytes().splitlines()]
        self.assertEqual([r['scalars']['status'] for r in rows], ['failed', 'started-unclosed-unknown'])
        self.assertEqual(rows[0]['detail_fields'], ['nested'])
        self.assertEqual(rows[0]['raw_line_sha256'], tool.hashlib.sha256(self.ledger.splitlines(keepends=True)[0]).hexdigest())
        self.assertIsNone(rows[1]['scalars']['nullable'])
        self.assertEqual((self.package / 'review/files/evidence/hold.md').read_bytes(),
                         (self.scope / 'hold.md').read_bytes())

    def test_cli_read_exact_bytes_case_pointer_ledger_line_and_materialize(self):
        self.create()
        read = self.cli('read', self.package, 'evidence/report.json')
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertEqual(read.stdout, self.report_bytes)
        read = self.cli('read', self.package, 'evidence/report.json', '--pointer', '/results/0')
        self.assertEqual(json.loads(read.stdout), self.report['results'][0])
        read = self.cli('read', self.package, 'evidence/ledger.jsonl', '--line', 1)
        self.assertEqual(read.stdout, self.ledger.splitlines(keepends=True)[0])
        destination = self.base / 'restored'
        result = self.cli('materialize', self.package, '--output', destination, '--path', 'evidence/report.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((destination / 'evidence/report.json').read_bytes(), self.report_bytes)
        self.assertFalse((destination / 'evidence/ledger.jsonl').exists())
        self.assertNotEqual(self.cli('materialize', self.package, '--output', destination).returncode, 0)
        self.assertNotEqual(self.cli('read', self.package, '../escape').returncode, 0)
        self.assertNotEqual(self.cli('read', self.package, 'evidence/ledger.jsonl', '--line', 0).returncode, 0)

    def test_review_tamper_rejected_even_with_updated_outer_hash(self):
        manifest = self.create()
        summary = self.package / 'review/summary.json'
        data = json.loads(summary.read_bytes())
        data['inputs'][0]['outcome_counts'] = {'not-reached': 5}
        summary.write_bytes(tool.encoded(data))
        for item in manifest['files']:
            if item['path'] == 'review/summary.json':
                item.update(tool.reference(self.package, item['path']))
        (self.package / 'review-manifest.json').write_bytes(tool.encoded(manifest))
        with self.assertRaisesRegex(ValueError, 'review differs'):
            tool.verify(self.package)

    def test_bad_input_never_publishes_partial_package(self):
        self.report['results'].append(self.report['results'][0])
        (self.scope / 'report.json').write_bytes(tool.encoded(self.report))
        with self.assertRaisesRegex(ValueError, 'duplicate case'):
            self.create()
        self.assertFalse(self.package.exists())
        self.assertEqual(list(self.base.glob('.evidence-*')), [])

    def test_no_implicit_input_selection_or_completion_claim(self):
        tool.create(self.root, 'evidence', self.package, part_bytes=1024)
        summary = json.loads((self.package / 'review/summary.json').read_bytes())
        self.assertEqual(summary['inputs'], [])
        self.assertEqual(tool.verify(self.package)['review_inputs'], 0)
        self.assertEqual(tool.read_file(self.package / 'detail', 'evidence/ledger.jsonl'), self.ledger)

    def test_zero_counts_and_spreadsheet_safe_display_keep_original_case(self):
        row = self.report['results'][0]
        row.update(case_id='=SUM(1,2)', outcome='inconclusive', raw_output='@hostile')
        self.report['results'] = [row]
        (self.scope / 'report.json').write_bytes(tool.encoded(self.report))
        self.create()
        summary = json.loads((self.package / 'review/summary.json').read_bytes())
        self.assertEqual(summary['inputs'][0]['outcome_counts'],
                         {outcome: int(outcome == 'inconclusive') for outcome in tool.OUTCOMES})
        with (self.package / 'review/cases.csv').open() as stream:
            display = next(csv.DictReader(stream))
        self.assertEqual(display['case_id'], "'=SUM(1,2)")
        self.assertEqual(display['raw_output'], "'@hostile")
        original = json.loads(tool.read_file(self.package / 'detail', 'evidence/report.json'))
        self.assertEqual(tool.pointer(original, display['detail_pointer'])['case_id'], '=SUM(1,2)')

    def test_materialize_uses_one_archive_pass_and_cleans_review_only_inputs(self):
        self.create()
        for selection in (None, ['evidence/report.json'], []):
            destination = self.base / ('restore-' + str(selection))
            with mock.patch.object(tool, 'check', wraps=tool.check) as checker:
                result = tool.verify(self.package, destination, paths=selection)
                self.assertEqual(checker.call_count, 1)
            restored = [p.relative_to(destination).as_posix()
                        for p in destination.rglob('*') if p.is_file()]
            self.assertEqual(set(restored), {'evidence/report.json', 'evidence/ledger.jsonl', 'evidence/hold.md'}
                             if selection is None else set(selection))
            self.assertEqual(result['restored_files'], len(restored))

    def test_compare_preflight_refuses_nested_outputs_and_leaves_no_partial_output(self):
        self.create()
        binary = self.scope / 'report.json'  # Preflight must fail before executing anything.
        for source in (self.package, self.root):
            output = source / 'new-comparison'
            with self.assertRaisesRegex(ValueError, 'outside input trees'):
                tool.compare(source, self.package, output, binary)
            self.assertFalse(output.exists())
        summary = self.package / 'review/summary.json'
        summary.write_bytes(b'corruption')
        output = self.base / 'failed-comparison'
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            tool.compare(self.scope / 'report.json', self.package, output, binary)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob('.dfb-compare-*')), [])
        with self.assertRaises(ValueError):
            tool.verify(self.package, self.package / 'restored')
        self.assertFalse((self.package / 'restored').exists())

    def test_duplicate_json_keys_nonfinite_numbers_and_bad_pointers_refused(self):
        for data in ('{"status":1,"status":2}', '{"duration":NaN}', '{"duration":Infinity}'):
            with self.assertRaises(ValueError):
                tool.load_json(data)
        self.assertEqual(tool.pointer({'a/b': {'~': 1}}, '/a~1b/~0'), 1)
        for selection in ('0', '/01', '/-1', '/~2'):
            with self.assertRaises((ValueError, KeyError)):
                tool.pointer([1, 2], selection)

    def test_package_path_symlink_and_review_input_traversal_refused(self):
        self.create()
        file = self.package / 'review/cases.csv'
        copy = self.base / 'outside.csv'
        file.rename(copy)
        file.symlink_to(copy)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            tool.verify(self.package)
        with self.assertRaisesRegex(ValueError, 'unsafe path'):
            tool.create(self.root, 'evidence', self.base / 'other', ['evidence/../bad'])

    def test_compare_uses_exact_originals_preserves_receipt_and_failure_status(self):
        self.create()
        binary = self.base / 'fake-dataflowbench'
        # A subprocess contract test: a nonzero Rust CLI status must propagate.
        binary.write_text('#!' + sys.executable + '\n' +
                          'import json,pathlib,sys\n'
                          'args=sys.argv[1:]\n'
                          'assert args[0] == "compare-reports"\n'
                          'assert "--allow-configuration-mismatch" not in args\n'
                          'current=pathlib.Path(args[args.index("--current")+1])\n'
                          'baseline=pathlib.Path(args[args.index("--baseline")+1])\n'
                          'assert (current/"evidence/report.json").read_bytes() == baseline.read_bytes()\n'
                          'assert not (current/"evidence/ledger.jsonl").exists()\n'
                          'sys.exit(7)\n')
        binary.chmod(0o700)
        output = self.base / 'comparison'
        status = tool.compare(self.scope / 'report.json', self.package, output, binary)
        self.assertEqual(status, 7)
        receipt = json.loads((output / 'package-inputs.json').read_bytes())
        self.assertEqual(receipt['exit_code'], 7)
        self.assertEqual(receipt['inputs']['current']['reports'][0]['sha256'],
                         tool.hashlib.sha256(self.report_bytes).hexdigest())
        self.assertTrue((output / 'current/evidence/report.json').exists())
        if REAL_BINARY is not None:
            native_output = self.base / 'native-comparison'
            status = tool.compare(self.scope / 'report.json', self.package, native_output, REAL_BINARY)
            self.assertEqual(status, 0)
            comparison = json.loads((native_output / 'comparison.json').read_bytes())
            self.assertTrue(comparison['populations_equal'])
            for side in ('baseline', 'current'):
                self.assertEqual(comparison[side]['case_count'], 5)
                self.assertEqual(comparison[side]['reports'][0]['sha256'],
                                 tool.hashlib.sha256(self.report_bytes).hexdigest())


if __name__ == '__main__':
    unittest.main()
