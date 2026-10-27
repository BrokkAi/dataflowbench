#!/usr/bin/env python3
"""Synthetic full-108 frozen-loop regression. No JVM/analyzer or qualification proof.

Copies exact current inputs into a temporary tree. Mocks runtime acquisition
validation, process/case dispatch and free-disk readings; executes the real
population loader, unsupported-decision checks, loop, exporter and env factory.
"""
from pathlib import Path
import copy
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import swift_common_population_v2 as common
import joern_normal_runner_v092 as runner
import joern_normal_reports_v092 as reports

PLAN = 'reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-03/pending-execution-plan-01.json'
spec = importlib.util.spec_from_file_location('successor_runtime_shim03', ROOT / 'scripts/joern_capability_repair_v092_03.py')
shim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shim)


class FullSuccessorRuntime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.copied = set()
        def copy_file(relative):
            if relative in self.copied:
                return
            self.copied.add(relative)
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for relative in [PLAN, 'populations/v0.9.0.json', 'populations/swift-synthetic-v3.json',
                         'reports/releases/v0.9.0/plan.json', 'scripts/swift_normal_reports_v1.py',
                         'scripts/swift_normal_runner_v1.py', 'scripts/joern_normal_reports_v1.py',
                         'scripts/joern_normal_runner_v1.py']:
            copy_file(relative)
        population = json.loads((ROOT / 'populations/v0.9.0.json').read_text())
        for row in population['cases']:
            copy_file(row['path'])
            for fixture in row['fixture_digests']:
                copy_file(fixture['path'])
        self.plan = json.loads((self.root / PLAN).read_text())
        for selection in self.plan['cases'].values():
            if selection['disposition'] == 'unsupported':
                reference = selection['decision']
                copy_file(reference['path'])
                decision = json.loads((ROOT / reference['path']).read_text())
                for evidence in decision['evidence']:
                    copy_file(evidence['path'])
        self.population, self.rows, _, self.cases, self.digest = common.load_common_population(self.root)
        self.output = self.root / shim.EXECUTION_OUTPUT_ROOT / 'synthetic-test-01'
        self.plan['output_root'] = shim.EXECUTION_OUTPUT_ROOT
        # Pending production qualification is deliberately absent. This test-only
        # sentinel exercises the runtime field shape, never an eligible receipt.
        sentinel = self.root / 'SYNTHETIC-NOT-QUALIFICATION.json'
        sentinel.write_text(json.dumps({'synthetic': True, 'qualification': False}))
        self.plan['fresh_qualification'] = {'path': sentinel.name, 'sha256': runner.sha(sentinel)}
        # Output namespace/qualification sentinel change only in the temp copy.
        (self.root / PLAN).write_text(json.dumps(self.plan))
        self.environment = {'PATH': '/usr/bin', 'HOME': str(self.root / 'parent-home'),
            'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1', 'DATAFLOWBENCH_V092_GROUP_ID': runner.GROUP_ID}
        self.attempted = []
        self.environments = []

    def execute(self):
        original_factory = common.private_engine
        factory, restore = shim._scoped_startup_engine_factory(
            original_factory, self.root, self.output, shim.JVM_STARTUP_POLICY)
        with mock.patch.dict(os.environ, self.environment, clear=True), mock.patch.object(common, 'private_engine', factory):
            engine = runner._engine(self.root)  # Actual dictionary bundle -> runner extraction.
            self.assertIsInstance(factory(self.root, 'joern'), dict)
            def process(argv, directory, phase, timeout, **kwargs):
                self.environments.append(kwargs['env'])
                (directory / 'version.stdout').write_text('synthetic Joern 4.0.660 version witness\n')
                return {'exit_status': 0, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped'}
            def run_case(root, plan, case_path, case, leaf, mode):
                self.assertTrue(case_path.is_file())
                self.assertIn(mode, ['off', 'on'])
                self.attempted.append(case['id'])
                environment = engine.env_for(plan['runtime'])
                self.environments.append(environment)
                leaf.mkdir()
                return {'raw_outcome': 'inconclusive', 'state': 'inconclusive', 'duration_ms': 1,
                    'total_elapsed_seconds': 0.001, 'diagnostics': ['SyntheticPhaseDispatch'],
                    'witness_checkpoints': [], 'executed': True, 'commands': [], 'native_outputs': []}, False
            try:
                with mock.patch.object(runner, 'validate_plan', return_value=(self.plan, {}, {'engine': engine, 'cases': self.cases})), \
                     mock.patch.object(runner.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=200 * 1024**3)), \
                     mock.patch.object(engine.process, 'run', side_effect=process), \
                     mock.patch.object(engine, 'run_case', side_effect=run_case):
                    return runner.execute(self.root, PLAN, self.output)
            finally:
                restore()

    def test_real_full108_loop_and_real_five_partition_export(self):
        run = self.execute()
        self.assertEqual(len(run['results']), 108)
        self.assertEqual(len(self.attempted), 96)
        expected_unsupported = {key for key, row in self.plan['cases'].items() if row['disposition'] == 'unsupported'}
        self.assertEqual(len(expected_unsupported), 12)
        self.assertEqual(set(self.attempted), set(self.cases) - expected_unsupported)
        raws = {row['case_id']: json.loads((self.root / row['raw']['path']).read_text()) for row in run['results']}
        self.assertEqual({key for key, raw in raws.items() if raw['state'] == 'unsupported'}, expected_unsupported)
        for key in expected_unsupported:
            self.assertFalse(raws[key]['executed'])
            self.assertEqual(raws[key]['decision_sha256'], self.plan['cases'][key]['decision']['sha256'])
        written = reports.export(self.root, PLAN, run, self.root / 'synthetic-normal')
        self.assertEqual(len(written), 5)
        flattened = [row for ref in written for row in json.loads((self.root / ref['path']).read_text())['results']]
        self.assertEqual(len(flattened), 108)
        self.assertEqual({row['case_id'] for row in flattened}, set(self.cases))
        self.assertEqual(sum(row['outcome'] == 'unsupported' for row in flattened), 12)
        for environment in self.environments:
            self.assertEqual(environment['JAVA_TOOL_OPTIONS'], '-Duser.home=' + str(self.output / 'jvm-home'))
            self.assertEqual(environment['JAVA_OPTS'], shim.JVM_STARTUP_POLICY['retained_java_opts'])
            self.assertEqual(environment['DATAFLOWBENCH_V092_GROUP_ID'], runner.GROUP_ID)
            self.assertEqual(environment['DATAFLOWBENCH_V092_RELEASE_EXECUTION'], '1')
            self.assertFalse(any(key in environment for key in ['_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH']))

    def test_real_loop_rejects_missing_native_decision(self):
        key = next(key for key, row in self.plan['cases'].items() if row['disposition'] == 'unsupported')
        (self.root / self.plan['cases'][key]['decision']['path']).unlink()
        with self.assertRaises(ValueError):
            self.execute()
        self.assertNotIn(key, self.attempted)

    def test_actual_launch_markers_and_policy_near_misses(self):
        for environment in [{}, {'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1', 'DATAFLOWBENCH_V092_GROUP_ID': 'foreign'}]:
            with mock.patch.dict(os.environ, environment, clear=True), self.assertRaises(ValueError):
                runner._require_launch_guard(runner.GROUP_ID)
        policy = copy.deepcopy(shim.JVM_STARTUP_POLICY)
        policy['option_template'] = '-Duser.home=/foreign'
        with self.assertRaises(ValueError):
            shim._scoped_startup_engine_factory(common.private_engine, self.root, self.output, policy)
        factory, restore = shim._scoped_startup_engine_factory(common.private_engine, self.root, self.output, shim.JVM_STARTUP_POLICY)
        with mock.patch.dict(os.environ, {**self.environment, 'JAVA_TOOL_OPTIONS': 'ambient', '_JAVA_OPTIONS': 'ambient',
                                       'JDK_JAVA_OPTIONS': 'ambient', 'CLASSPATH': 'ambient'}, clear=True):
            try:
                bundle = factory(self.root, 'joern')
                self.assertIsInstance(bundle, dict)
                env = bundle['runner'].env_for(self.plan['runtime'])
                self.assertEqual(env['JAVA_TOOL_OPTIONS'], '-Duser.home=' + str(self.output / 'jvm-home'))
                self.assertFalse(any(key in env for key in ['_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH']))
            finally:
                restore()


if __name__ == '__main__':
    unittest.main()
