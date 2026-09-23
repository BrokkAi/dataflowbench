#!/usr/bin/env python3
"""Synthetic retained-evidence tests for the non-scored Swift qualification."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    'swift_native_qualification', SCRIPTS / 'run-swift-entrypoint-qualification.py')
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class NativeQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dfb-swift-native-qualification-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.attempt = self.root / 'attempt'
        self.attempt.mkdir()
        self.retained = self.root / 'retained'
        (self.retained / 'db').mkdir(parents=True)

    @staticmethod
    def read_json(path):
        return json.loads(path.read_text())

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value) + '\n')

    def case(self, polarity):
        path = ROOT / 'cases/taint/swift' / f'native-entrypoint-{polarity}' / 'case.json'
        return qualification.read(path)

    def make_attempt(self, polarity):
        case = self.case(polarity)
        source = case['source_anchors'][0]['line_hint']
        sink = case['sink_anchors'][0]['line_hint']
        source_text = (ROOT / 'cases/taint/swift' / f'native-entrypoint-{polarity}' / 'main.swift').read_bytes()
        self.write_json(self.attempt / 'witness.json', {
            'probe_error': None,
            'cleanup_error': None,
            'extraction_integrity': {'ready_for_observation': True},
            'analysis_budget': {'wall_clock_seconds': 60, 'peak_memory_mb': 2048},
            'extraction_phase_deadline_seconds': 150,
            'retained_scratch': str(self.retained),
        })
        (self.attempt / 'main.swift').write_bytes(source_text)

        phases = ['database-create', 'database-resolve', 'roles', 'flow', 'identity',
                  'roles-decode', 'flow-decode', 'identity-decode']
        for phase in phases:
            self.write_json(self.attempt / f'{phase}.command.json', {
                'exit_status': 0, 'timed_out': False,
                'cleanup_status': 'tracked-processes-stopped', 'elapsed_seconds': 1.25,
            })
        for index, phase in enumerate(['database-create', 'roles', 'flow', 'identity'], start=1):
            (self.attempt / f'{phase}.stderr').write_text(
                f'{index * 100} maximum resident set size\n')

        log_dir = self.attempt / 'log/swift/extractor'
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / 'extractor.log').write_text('Swift extraction completed successfully.\n')

        roles = []
        for profile in ('vendor-native', 'adapter-corrected'):
            roles.extend([
                [source, 20, profile, 'source'],
                [sink, 20, profile, 'sink'],
            ])
        flows = []
        if polarity == 'positive':
            flows.append([source, sink, 20, 'adapter-corrected'])
        self.write_json(self.attempt / 'roles.json', {'#select': {'tuples': roles}})
        self.write_json(self.attempt / 'flow.json', {'#select': {'tuples': flows}})
        self.write_json(self.attempt / 'identity.json', {
            '#select': {'tuples': [[source, 'Swift', 'Swift', 'CommandLine', 'arguments']]}
        })

        with zipfile.ZipFile(self.retained / 'db/src.zip', 'w') as archive:
            archive.writestr('db/source/main.swift', source_text)
        return case

    def test_preregistration_matches_existing_plan_without_git_checks(self):
        plan, config = qualification.verify_preregistration(check_git=False)
        self.assertEqual(plan['configuration_hash'], config['configuration_hash'])
        self.assertEqual(plan['scope'], 'non-scored-canonical-qualification')
        self.assertEqual(len(plan['cases']), 2)

    def test_positive_and_negative_rows_join_by_lane_and_location(self):
        for polarity, expected_adapter_flow in [('positive', True), ('negative', False)]:
            with self.subTest(polarity=polarity):
                case = self.make_attempt(polarity)
                observation = qualification.observe(self.attempt, case)
                self.assertEqual(observation['status'], 'observed-unqualified')
                self.assertEqual(observation['phase_measurements'], {
                    phase: {'elapsed_seconds': 1.25, 'command_maxrss_bytes': index * 100}
                    for index, phase in enumerate(
                        ('database-create', 'roles', 'flow', 'identity'), start=1)
                })
                for lane in ('vendor-native', 'adapter-assisted'):
                    result = observation['lanes'][lane]
                    self.assertTrue(result['source_anchor_recognized'])
                    self.assertTrue(result['sink_anchor_recognized'])
                self.assertEqual(observation['lanes']['vendor-native']['observed_anchor_flow'], False)
                self.assertEqual(observation['lanes']['adapter-assisted']['observed_anchor_flow'],
                                 expected_adapter_flow)

    def test_extraction_error_log_is_rejected(self):
        case = self.make_attempt('positive')
        (self.attempt / 'log/swift/extractor/extractor.log').write_text('ERRO extractor failed\n')
        with self.assertRaisesRegex(ValueError, 'extraction errors'):
            qualification.observe(self.attempt, case)

    def test_guard_getter_flow_is_not_canonical_anchor_flow(self):
        case = self.make_attempt('positive')
        source = case['source_anchors'][0]['line_hint']
        sink = case['sink_anchors'][0]['line_hint']
        roles = self.read_json(self.attempt / 'roles.json')
        roles['#select']['tuples'].append([source - 1, 20, 'adapter-corrected', 'argv'])
        self.write_json(self.attempt / 'roles.json', roles)
        self.write_json(self.attempt / 'flow.json', {'#select': {'tuples': [
            [source - 1, sink, 20, 'adapter-corrected']]}})
        observation = qualification.observe(self.attempt, case)
        self.assertFalse(observation['lanes']['adapter-assisted']['observed_anchor_flow'])
        self.assertEqual(len(observation['lanes']['adapter-assisted']['flow_rows']), 1)

    def test_missing_decoded_phase_is_rejected(self):
        case = self.make_attempt('positive')
        (self.attempt / 'flow-decode.command.json').unlink()
        with self.assertRaises((ValueError, OSError)):
            qualification.observe(self.attempt, case)

    def test_timed_out_phase_is_rejected(self):
        case = self.make_attempt('positive')
        record_path = self.attempt / 'roles.command.json'
        record = self.read_json(record_path)
        record['timed_out'] = True
        self.write_json(record_path, record)
        with self.assertRaisesRegex(ValueError, 'phase failure: roles'):
            qualification.observe(self.attempt, case)

    def test_archive_with_wrong_source_is_rejected(self):
        case = self.make_attempt('positive')
        with zipfile.ZipFile(self.retained / 'db/src.zip', 'w') as archive:
            archive.writestr('db/source/main.swift', b'// different retained source\n')
        with self.assertRaisesRegex(ValueError, 'archived canonical source differs'):
            qualification.observe(self.attempt, case)

    def test_wrong_resolved_identity_is_rejected(self):
        case = self.make_attempt('positive')
        self.write_json(self.attempt / 'identity.json', {'#select': {'tuples': []}})
        with self.assertRaisesRegex(ValueError, 'resolved canonical argv identity missing'):
            qualification.observe(self.attempt, case)

    def test_unknown_flow_profile_is_rejected(self):
        case = self.make_attempt('positive')
        result_path = self.attempt / 'flow.json'
        result = self.read_json(result_path)
        result['#select']['tuples'].append([4, 6, 20, 'mystery-profile'])
        self.write_json(result_path, result)
        with self.assertRaisesRegex(ValueError, 'unknown flow profile'):
            qualification.observe(self.attempt, case)

    def test_flow_with_unrecognized_source_or_sink_location_is_rejected(self):
        for row in ([999, 6, 20, 'adapter-corrected'], [4, 999, 20, 'adapter-corrected']):
            with self.subTest(row=row):
                case = self.make_attempt('positive')
                self.write_json(self.attempt / 'flow.json', {'#select': {'tuples': [row]}})
                with self.assertRaisesRegex(ValueError, 'unjoined flow'):
                    qualification.observe(self.attempt, case)


class PortableEvidenceTests(unittest.TestCase):
    def setUp(self):
        import shutil
        spec = importlib.util.spec_from_file_location('portable', ROOT / 'scripts/verify-swift-entrypoint-qualification.py')
        self.verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.verifier)
        self.temp = tempfile.TemporaryDirectory(prefix='dfb-native-portable-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'evidence'
        shutil.copytree(ROOT / 'evidence/swift-entrypoint-qualification-v1', self.root)
        self.attempt = self.root / 'attempt-01'
        self.positive = self.attempt / 'dfb-taint-swift-native-entrypoint-positive'

    def mutate(self, path, change):
        value = qualification.read(path)
        change(value)
        qualification.write(path, value)

    def refresh_manifest(self):
        qualification.write(self.attempt / 'manifest.json', {
            str(p.relative_to(self.attempt)): qualification.sha(p)
            for p in sorted(self.attempt.rglob('*'))
            if p.is_file() and p != self.attempt / 'manifest.json'})

    def test_portable_package(self):
        self.verifier.verify(self.attempt)

    def test_changed_canonical_join(self):
        self.mutate(self.positive / 'canonical-join.json', lambda v: v.update(fixture_revision='wrong'))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, 'canonical join'):
            self.verifier.verify(self.attempt)

    def test_promoted_observation(self):
        self.mutate(self.positive / 'observation.json', lambda v: v.update(scored_activation=True))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, 'observation promotion'):
            self.verifier.verify(self.attempt)

    def test_fabricated_clean_positive(self):
        self.mutate(self.positive / 'probe/flow.json', lambda v: v['#select'].update(tuples=[]))
        self.mutate(self.positive / 'observation.json',
                    lambda v: v['lanes']['adapter-assisted'].update(flow_rows=[], observed_anchor_flow=False))
        self.refresh_manifest()
        with self.assertRaises(ValueError):
            self.verifier.verify(self.attempt)

    def test_guard_only_flow_cannot_replace_canonical_flow(self):
        source = qualification.read(self.positive / 'canonical-case.json')['source_anchors'][0]['line_hint']
        def guard_only(value):
            for row in value['#select']['tuples']:
                if row[0] == source:
                    row[0] = source - 1
        self.mutate(self.positive / 'probe/flow.json', guard_only)
        def observation(value):
            for row in value['lanes']['adapter-assisted']['flow_rows']:
                if row[0] == source:
                    row[0] = source - 1
            value['lanes']['adapter-assisted']['observed_anchor_flow'] = False
        self.mutate(self.positive / 'observation.json', observation)
        self.refresh_manifest()
        with self.assertRaises(ValueError):
            self.verifier.verify(self.attempt)

    def test_negative_auxiliary_flow_is_not_hidden(self):
        negative = self.attempt / 'dfb-taint-swift-native-entrypoint-negative'
        case = qualification.read(negative / 'canonical-case.json')
        source = case['source_anchors'][0]['line_hint']
        view = qualification.read(negative / 'observation.json')['lanes']['adapter-assisted']
        sink = view['sink_rows'][-1]
        flow = [source - 1, sink[0], sink[1], 'adapter-corrected']
        self.mutate(negative / 'probe/flow.json', lambda v: v['#select'].update(tuples=[flow]))
        self.mutate(negative / 'observation.json',
                    lambda v: v['lanes']['adapter-assisted'].update(flow_rows=[flow], observed_anchor_flow=False))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, 'negative auxiliary flow'):
            self.verifier.verify(self.attempt)

    def test_extractor_error(self):
        (self.positive / 'probe/log/swift/extractor/new.log').write_text('ERRO: extraction error\n')
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, 'raw extraction gate'):
            self.verifier.verify(self.attempt)


if __name__ == '__main__':
    unittest.main(verbosity=2)
