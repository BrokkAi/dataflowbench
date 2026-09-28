#!/usr/bin/env python3
"""Synthetic provenance/mutation tests, never analyzer execution."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from swift_normal_reports_v1 import ROOT, POPULATION, export, sha, load_population


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
    return {'path': name, 'sha256': sha(path)}


def sample(root):
    for name in ['cases', 'populations', 'schemas']:
        shutil.copytree(ROOT / name, root / name)
    population, cases, ph = load_population(root)
    tool = {'tool': 'codeql', 'tool_version': 'test-version-1', 'tool_build_identity': 'synthetic-patched-test-build', 'adapter_version': 'test-normal-v1'}
    config = write(root, 'adapters/test-normal/config.json', {'synthetic': True})
    plan = {'schema': 'swift-normal-report-plan/v1', 'population_sha256': ph, 'fixture_revision': population['fixture_revision'], 'aggregate_resource_qualification': 'unavailable', 'scored_activation': False, 'registered_at_unix_seconds': 1, 'identity': tool, 'configurations': {'test': [config]}, 'cases': {i: {'configuration': 'test', 'disposition': 'attempt'} for i in cases}}
    plan['execution_contract'] = write(root, 'adapters/test-normal/contract.json', {'population_sha256': ph, 'fixture_revision': population['fixture_revision'], 'aggregate_resource_qualification': 'unavailable', 'scored_activation': False, 'phases': {'extraction': {'wall_clock_seconds': 150, 'peak_memory_mb': 2048}, 'analysis': {'wall_clock_seconds': 75, 'peak_memory_mb': 2048}}})
    planref = write(root, 'adapters/test-normal/plan.json', plan)
    import hashlib
    ch = hashlib.sha256(config['path'].encode() + (root / config['path']).read_bytes()).hexdigest()
    stdout = write(root, 'reports/raw/normal-test/version.stdout', {'test': 'synthetic identity only'})
    command = {'argv': ['synthetic-test-only'], 'exit_status': 0, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped', 'elapsed_seconds': 0.001, 'deadline_seconds': 1}
    witness = write(root, 'reports/raw/normal-test/identity.json', {'observed': tool, 'observed_at_unix_seconds': 2, 'command': command, 'stdout': stdout})
    cmdref = write(root, 'reports/raw/normal-test/command.json', command)
    run = {'schema': 'swift-normal-report-run/v1', 'plan_sha256': planref['sha256'], 'population_sha256': ph, 'fixture_revision': population['fixture_revision'], 'aggregate_resource_qualification': 'unavailable', 'scored_activation': False, 'started_at_unix_seconds': 2, 'ended_at_unix_seconds': 3, 'cold_or_warm': 'cold', 'identity': tool, 'identity_witness': witness, 'results': []}
    for i in cases:
        raw = {'schema': 'swift-normal-raw/v1', 'case_id': i, 'plan_sha256': planref['sha256'], 'population_sha256': ph, 'fixture_revision': population['fixture_revision'], 'configuration_hash': ch, 'identity_witness_sha256': witness['sha256'], 'execution_contract_sha256': plan['execution_contract']['sha256'], 'raw_outcome': 'not-reached', 'state': 'inconclusive', 'duration_ms': 1, 'diagnostics': ['IncompleteCoverage'], 'witness_checkpoints': [], 'executed': True, 'commands': [cmdref], 'native_outputs': [write(root, 'reports/raw/normal-test/' + i + '-native.json', {'synthetic_observation': []})]}
        ref = write(root, 'reports/raw/normal-test/' + i + '.json', raw)
        run['results'].append({'case_id': i, 'configuration': 'test', 'raw': ref})
    return planref['path'], plan, run


def fixture(root):
    planpath, plan, run = sample(root)
    bundle = export(root, planpath, run)
    pop = json.loads((root / POPULATION).read_text())
    manifest = {'schema_version': 1, 'benchmark': {'revision': 'a' * 40, 'release': 'development', 'case_schema_version': 2, 'result_schema_version': 1, 'fixture_revision': pop['fixture_revision'], 'dirty': False}, 'claim': {'scope': 'development', 'tracks': ['taint'], 'dimensions': ['taint'], 'exclusions': [], 'score_tiers': sorted({c['score_tier'] for c in pop['cases']}), 'model_profiles': sorted({c['model_profile'] for c in pop['cases']})}, 'cases': pop['cases'], 'adapters': [], 'reports': []}
    for n, (group, report) in enumerate(bundle['reports'].items()):
        ref = write(root, 'reports/normal-test-' + str(n) + '.json', report)
        adapter_id = 'normal-test-' + str(n)
        manifest['adapters'].append({'id': adapter_id, 'tool': report['tool'], 'tool_version': report['tool_version'], 'build_identity': report['tool_build_identity'], 'adapter_version': report['adapter_version'], 'configuration_hash': report['configuration_hash'], 'track': group[0], 'dimension': group[0], 'model_profile': group[1]})
        manifest['reports'].append({'path': ref['path'], 'sha256': ref['sha256'], 'normalized_report_sha256': ref['sha256'], 'adapter': adapter_id, 'track': group[0], 'dimension': group[0], 'model_profile': group[1], 'case_ids': [r['case_id'] for r in report['results']], 'outcomes': [{'case_id': r['case_id'], 'outcome': r['outcome']} for r in report['results']], 'raw_evidence': [{'case_id': r['case_id'], 'path': r['raw_output'], 'sha256': sha(root / r['raw_output'])} for r in report['results']]})
    write(root, 'reports/freeze.json', manifest)


class Exporter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path, self.plan, self.run = sample(self.root)

    def export(self, run=None):
        return export(self.root, self.path, self.run if run is None else run)

    def mutate_raw(self, **changes):
        row = self.run['results'][0]
        raw = json.loads((self.root / row['raw']['path']).read_text())
        raw.update(changes)
        row['raw'] = write(self.root, row['raw']['path'], raw)

    def test_all108_inconclusive_partitioned_by_case_metadata(self):
        result = self.export()
        self.assertEqual(result['audit']['profile_counts'], {'benchmark-controlled': 96, 'tool-native': 12})
        self.assertEqual(sorted(len(r['results']) for r in result['reports'].values()), [2, 4, 12, 24, 66])
        self.assertEqual(len(result['audit']['results']), 108)
        self.assertTrue(all(r['outcome'] == 'inconclusive' for report in result['reports'].values() for r in report['results']))
        self.assertFalse(result['audit']['scored_activation'])

    def test_empty_and_missing_run_metadata_fail_closed(self):
        for field in self.run:
            run = copy.deepcopy(self.run)
            del run[field]
            with self.subTest(field=field), self.assertRaises((ValueError, KeyError)):
                self.export(run)
        with self.assertRaises(ValueError): self.export({})

    def test_no_missing_duplicate_foreign_members(self):
        for kind in ['missing', 'duplicate', 'foreign']:
            run = copy.deepcopy(self.run)
            if kind == 'missing': run['results'].pop()
            if kind == 'duplicate': run['results'][0] = run['results'][1]
            if kind == 'foreign': run['results'][0]['case_id'] = 'foreign'
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.export(run)

    def test_runner_error_and_budget_reasons_preserved(self):
        self.mutate_raw(raw_outcome='runner-error', state='runner-error', diagnostics=['BudgetExhausted', 'ExtractionFailed'])
        result = self.export()['audit']['results']
        row = next(r for r in result if r['case_id'] == self.run['results'][0]['case_id'])
        self.assertEqual(row['outcome'], 'runner-error')
        reports = self.export()['reports']
        self.assertTrue(any('BudgetExhausted' in r['diagnostics'] for report in reports.values() for r in report['results']))

    def test_missing_identity_and_false_qualification(self):
        for change in [{'identity': {}}, {'identity_witness': {}}, {'scored_activation': True}, {'aggregate_resource_qualification': 'qualified'}, {'started_at_unix_seconds': True}]:
            run = copy.deepcopy(self.run); run.update(change)
            with self.subTest(change=change), self.assertRaises((ValueError, KeyError)): self.export(run)

    def test_raw_hash_and_state_cannot_be_promoted(self):
        self.mutate_raw(state='not-reached')
        with self.assertRaisesRegex(ValueError, 'special state'): self.export()
        self.mutate_raw(state='inconclusive')
        self.run['results'][0]['raw']['sha256'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'digest'): self.export()

    def test_unsupported_requires_prospective_partition(self):
        self.mutate_raw(raw_outcome='unsupported', state='unsupported', executed=False, duration_ms=0)
        with self.assertRaisesRegex(ValueError, 'prospective partition'): self.export()

    def test_prospective_unsupported_preserved_and_retrospective_rejected(self):
        row = self.run['results'][0]
        raw = json.loads((self.root / row['raw']['path']).read_text())
        proof = write(self.root, 'adapters/test-normal/capability.json', {'finding': 'synthetic unavailable feature'})
        decision = {'case_id': row['case_id'], 'population_sha256': self.run['population_sha256'], 'configuration_hash': raw['configuration_hash'], 'identity': self.run['identity'], 'outcome': 'unsupported', 'reviewed_at_unix_seconds': 1, 'reason': 'Synthetic prospective partition test', 'evidence': [proof]}
        decision_ref = write(self.root, 'adapters/test-normal/decision.json', decision)
        self.plan['cases'][row['case_id']].update(disposition='unsupported', decision=decision_ref)
        planref = write(self.root, self.path, self.plan)
        self.run['plan_sha256'] = planref['sha256']
        for item in self.run['results']:
            record = json.loads((self.root / item['raw']['path']).read_text())
            record['plan_sha256'] = planref['sha256']
            if item['case_id'] == row['case_id']:
                record.update(raw_outcome='unsupported', state='unsupported', executed=False, duration_ms=0, commands=[], decision_sha256=decision_ref['sha256'])
            item['raw'] = write(self.root, item['raw']['path'], record)
        result = self.export()
        observed = next(r for r in result['audit']['results'] if r['case_id'] == row['case_id'])
        self.assertEqual(observed['outcome'], 'unsupported')
        decision['reviewed_at_unix_seconds'] = 3
        self.plan['cases'][row['case_id']]['decision'] = write(self.root, decision_ref['path'], decision)
        planref = write(self.root, self.path, self.plan)
        self.run['plan_sha256'] = planref['sha256']
        for item in self.run['results']:
            record = json.loads((self.root / item['raw']['path']).read_text())
            record['plan_sha256'] = planref['sha256']
            item['raw'] = write(self.root, item['raw']['path'], record)
        with self.assertRaisesRegex(ValueError, 'retrospective'): self.export()

    def test_failed_command_cannot_hide_in_inconclusive(self):
        ref = self.run['results'][0]['raw']
        raw = json.loads((self.root / ref['path']).read_text())
        command = {'argv': ['synthetic-failure'], 'exit_status': 2, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped', 'elapsed_seconds': 1, 'deadline_seconds': 2}
        cmdref = write(self.root, 'reports/raw/normal-test/failure.json', command)
        self.mutate_raw(commands=[cmdref])
        with self.assertRaisesRegex(ValueError, 'failed invocation'): self.export()
        command.update(timed_out=True, exit_status=-15)
        cmdref = write(self.root, cmdref['path'], command)
        self.mutate_raw(commands=[cmdref])
        with self.assertRaisesRegex(ValueError, 'budget reason'): self.export()
        self.mutate_raw(diagnostics=['BudgetExhausted'])
        self.export()

    def test_native_outputs_and_configuration_provenance(self):
        self.mutate_raw(native_outputs=[])
        with self.assertRaisesRegex(ValueError, 'native output'): self.export()
        row = self.run['results'][0]
        self.mutate_raw(native_outputs=[{'path': 'reports/raw/missing.json', 'sha256': '0' * 64}])
        with self.assertRaisesRegex(ValueError, 'artifact'): self.export()
        self.mutate_raw(configuration_hash='0' * 64)
        with self.assertRaisesRegex(ValueError, 'configuration_hash'): self.export()

    def test_case_metadata_drift_is_rejected(self):
        pop = json.loads((self.root / POPULATION).read_text())
        path = self.root / pop['cases'][0]['path']
        case = json.loads(path.read_text());case['model_profile'] = 'tool-native';path.write_text(json.dumps(case))
        with self.assertRaisesRegex(ValueError, 'digest'): self.export()

    def test_historical_run_not_relabelled(self):
        run = copy.deepcopy(self.run);run['schema'] = 'swift-v3-coverage-report/v1'
        with self.assertRaisesRegex(ValueError, 'new run'): self.export(run)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--freeze-fixture':
        fixture(Path(sys.argv[2]))
    else:
        unittest.main()
