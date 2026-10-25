"""Private static/source-bound tests. No actual qualification or dispatch."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import packet, history, protocol, stage_runtime, bridge, admission, supervisor
ROOT = packet.ROOT

class StopAfterGroups(Exception):
    pass

class AdapterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = packet.inherited_core(ROOT)
        cls.old = packet.document(ROOT, cls.core['contract'])
        cls.raw = packet.read_ref(ROOT, cls.core['contract'])
        cls.executor = packet.load_bound_module(ROOT, 'private_joern05_test_executor', cls.core['runtime_module_graph']['executor'])
        sys.path.insert(0, str(ROOT / 'scripts'))
        cls.runner_ref = {'path': 'scripts/joern_normal_runner_v092.py', 'sha256': packet.digest((ROOT / 'scripts/joern_normal_runner_v092.py').read_bytes())}
        cls.runner = packet.load_bound_module(ROOT, 'private_joern05_test_runner', cls.runner_ref)

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(ROOT / 'scripts'))
        sys.modules.pop('private_joern05_test_executor', None)
        sys.modules.pop('private_joern05_test_runner', None)

    def successor(self):
        new = copy.deepcopy(self.old)
        next((g for g in new['groups'] if g['id'] == protocol.GROUP))['maximum_attempts'] = 5
        return new

    def test_actual_history_reader_nine_contexts_twenty_retained(self):
        result = history.validate(ROOT)
        self.assertEqual(len(result['source_contexts']), 9)
        self.assertEqual(len(result['retained20']), 20)
        self.assertEqual(result['counters'][protocol.GROUP], 4)
        self.assertFalse(result['execution_authorized'])

    def test_context_roster_no_future_tenth(self):
        self.assertEqual(history.context_bindings(ROOT), self.core['source_contexts'])
        with self.assertRaises(FileNotFoundError):
            history.context_bindings(ROOT, {'contract': {'path': 'missing-actual-contract', 'sha256': '0' * 64}, 'source_commit': '0' * 40, 'plan_commit': '1' * 40, 'source_evidence': {'path': 'missing-actual-evidence', 'sha256': '0' * 64}})

    def test_metadata_cannot_supply_normalized_runtime_contexts(self):
        with self.assertRaisesRegex(packet.AdapterError, 'normalized context roster'):
            stage_runtime.verify_runtime_context_bindings(ROOT, {})
        with self.assertRaisesRegex(packet.AdapterError, 'actual normalized contract identity'):
            stage_runtime.verify_runtime_context_bindings(ROOT, self.core['source_contexts'])

    def test_source_roster_exact_inherited_not_counts(self):
        self.assertEqual(protocol.source_roster(ROOT, []), self.old['source_inputs'])

    def test_source_roster_replacement_or_untyped_rejects(self):
        with self.assertRaises(packet.AdapterError):
            protocol.source_roster(ROOT, [self.old['source_inputs'][0]])
        with self.assertRaises(packet.AdapterError):
            protocol.source_roster(ROOT, [{'path': 'x', 'sha256': '0' * 64}])

    def test_contract_exact_joern_delta(self):
        new = self.successor()
        g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
        protocol.contract_delta(self.old, new, g)

    def test_contract_wrong_cap_or_changed_retained_rejects(self):
        new = self.successor()
        g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
        g['maximum_attempts'] = 6
        with self.assertRaises(packet.AdapterError):
            protocol.contract_delta(self.old, new, g)
        new = self.successor()
        g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
        new['groups'][0]['deadline_seconds'] += 1
        with self.assertRaises(packet.AdapterError):
            protocol.contract_delta(self.old, new, g)

    def test_contract_changed_joern_cases_or_guard_rejects(self):
        for change in ('cases', 'guards'):
            new = self.successor()
            g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
            if change == 'cases':
                g['case_ids'] = g['case_ids'][:-1]
            else:
                new['resource_guards']['working_set_gib'] = 31
            with self.assertRaises(packet.AdapterError):
                protocol.contract_delta(self.old, new, g)

    def test_literal_reservation_expiry_and_report_metadata_preserved(self):
        new = self.successor()
        g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
        new['resource_reservation']['expires_at_unix_seconds'] = None
        with self.assertRaisesRegex(packet.AdapterError, 'resource_reservation'):
            protocol.contract_delta(self.old, new, g)
        new = self.successor()
        g = next((g for g in new['groups'] if g['id'] == protocol.GROUP))
        g['reports'][0]['unreviewed'] = 'field'
        with self.assertRaisesRegex(packet.AdapterError, 'report fields'):
            protocol.contract_delta(self.old, new, g)

    def test_runtime_missing_artifacts_stops_before_history_replay(self):
        with self.assertRaisesRegex(packet.AdapterError, 'missing actual artifacts'):
            with stage_runtime.current_validation_scope(ROOT, {}, object(), {}):
                self.fail('missing artifacts reached runtime')

    def test_real_graph_import_and_historical_scope_stops_at_recovery_io(self):
        bridge_module = packet.load_bound_module(ROOT, 'private_joern05_graph_bridge', self.core['runtime_module_graph']['bridge19'])
        try:
            hosts = {'bridge19': bridge_module}
            for role in ('supervisor24', 'protocol24', 'admission24'):
                hosts[role] = packet.load_bound_module(ROOT, 'private_joern05_host_' + role, self.core['runtime_module_graph'][role])
            graph = bridge_module.prepare_graph(ROOT, self.core, host_modules=hosts)
            for (role, ref) in self.core['runtime_module_graph'].items():
                self.assertIs(stage_runtime._pinned_member(ROOT, graph, role, ref), graph.module(role))
            stage = graph.module('stage_runtime11')
            provider = graph.module('incoming_recovery')
            before = (stage._ACTIVE_RESUME, stage._incoming_recovery, stage.load_dependencies, stage._read, graph.module('protocol24').validate_resume_history)

            def no_replay(*args, **kwargs):
                raise StopAfterGroups('actual provider evidence I/O sentinel')
            with mock.patch.object(provider, 'recover_bifrost_history', side_effect=no_replay):
                with self.assertRaisesRegex(Exception, 'actual provider evidence I/O sentinel'):
                    with stage_runtime.historical_context_scope(ROOT, graph):
                        self.fail('must not reconstruct runtime in this preparation test')
            self.assertEqual((stage._ACTIVE_RESUME, stage._incoming_recovery, stage.load_dependencies, stage._read, graph.module('protocol24').validate_resume_history), before)
            expanded = dict(self.core['runtime_module_graph'])
            expanded['joern05_packet'] = self.core['runtime_module_graph']['protocol24']
            with self.assertRaisesRegex(Exception, 'fixed BF15 topology'):
                bridge_module._adapt_default_graph_spec(expanded)
        finally:
            sys.modules.pop('private_joern05_graph_bridge', None)
            for role in ('supervisor24', 'protocol24', 'admission24'):
                sys.modules.pop('private_joern05_host_' + role, None)

    def test_child_controller_missing_markers_cannot_reach_freshness(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(packet.AdapterError, 'outer marker'):
                supervisor.run_child_group(ROOT, {}, {}, graph=None, child=None, parent_ref={}, dispatch_sidecars={}, lock_fd=-1, popen_monotonic=0, phase_bindings={})

    def test_all_seven_module_bodies_compile_without_execution(self):
        for name in ('packet', 'history', 'protocol', 'stage_runtime', 'bridge', 'admission', 'supervisor'):
            path = HERE / (name + '.py')
            compile(path.read_bytes(), str(path), 'exec')

    def test_dispatch_singleton_and_cap(self):
        plan = self.successor()
        self.assertEqual(supervisor.dispatch_plan({'dispatch_groups': [protocol.GROUP]}, {'plan': plan})['attempt_id'], protocol.ATTEMPT)
        for groups in ([], ['bifrost-smoke'], [protocol.GROUP, 'codeql-swift-common108']):
            with self.assertRaises(packet.AdapterError):
                protocol.dispatch_groups({'dispatch_groups': groups})

    def test_actual_frozen_freshness_selects_five(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            ledger = root / self.executor.LEDGER_PATH
            ledger.parent.mkdir(parents=True)
            rows = [{'group_id': protocol.GROUP, 'attempt_id': f'{protocol.GROUP}-attempt-{n:02}-series-01', 'execution_series': 1, 'status': 'failed'} for n in range(1, 5)]
            ledger.write_text(''.join((json.dumps(row) + '\n' for row in rows)))
            group = {'id': protocol.GROUP, 'maximum_attempts': 5}
            result = supervisor.frozen_freshness(self.executor, root, group, [])
            self.assertEqual(result[-1], protocol.ATTEMPT)
            result[0].mkdir(parents=True)
            with self.assertRaises(self.executor.ReleaseError):
                supervisor.frozen_freshness(self.executor, root, group, [])

    def test_freshness_reused_global_number_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            ledger = root / self.executor.LEDGER_PATH
            ledger.parent.mkdir(parents=True)
            rows = [{'group_id': protocol.GROUP, 'attempt_id': f'{protocol.GROUP}-attempt-{n:02}-series-{i}', 'execution_series': i, 'status': 'failed'} for (i, n) in enumerate((1, 2, 3, 3), 1)]
            ledger.write_text(''.join((json.dumps(row) + '\n' for row in rows)))
            with self.assertRaises(packet.AdapterError):
                supervisor.frozen_freshness(self.executor, root, {'id': protocol.GROUP, 'maximum_attempts': 5}, [])

    def test_actual_validate_plan_cap_projection_reaches_real_all84_shapes(self):
        actual = self.successor()
        raw = packet.canonical(actual)
        ref = {**self.core['contract'], 'sha256': packet.digest(raw)}
        calls = []
        real_shape = self.executor._validate_group_shape

        def shape(*args, **kwargs):
            result = real_shape(*args, **kwargs)
            calls.append((args[0]['id'], args[0]['maximum_attempts']))
            return result
        before = (self.executor._read_json, self.executor.V4_CONTRACT_PATH)
        with stage_runtime.parser_scope(self.executor, ROOT, ref, actual, raw):
            with mock.patch.object(self.executor, '_validate_group_shape', side_effect=shape), mock.patch.object(self.executor, '_check_tool_file', side_effect=StopAfterGroups):
                with self.assertRaises(StopAfterGroups):
                    self.executor.validate_plan(ROOT / ref['path'], repo_root=ROOT)
        self.assertEqual(len(calls), 84)
        self.assertEqual(dict(calls)[protocol.GROUP], 2)
        self.assertEqual((self.executor._read_json, self.executor.V4_CONTRACT_PATH), before)
        self.assertEqual(next((g for g in actual['groups'] if g['id'] == protocol.GROUP))['maximum_attempts'], 5)

    def test_projection_restores_after_exception_and_rejects_six(self):
        actual = self.successor()
        raw = packet.canonical(actual)
        ref = {**self.core['contract'], 'sha256': packet.digest(raw)}
        before = (self.executor._read_json, self.executor.V4_CONTRACT_PATH)
        with self.assertRaises(StopAfterGroups):
            with stage_runtime.parser_scope(self.executor, ROOT, ref, actual, raw):
                raise StopAfterGroups
        self.assertEqual((self.executor._read_json, self.executor.V4_CONTRACT_PATH), before)
        next((g for g in actual['groups'] if g['id'] == protocol.GROUP))['maximum_attempts'] = 6
        raw = packet.canonical(actual)
        ref['sha256'] = packet.digest(raw)
        with self.assertRaises(packet.AdapterError):
            with stage_runtime.parser_scope(self.executor, ROOT, ref, actual, raw):
                pass

    def test_projected_plan_must_equal_bound_raw_contract(self):
        actual = self.successor()
        raw = packet.canonical(actual)
        ref = {**self.core['contract'], 'sha256': packet.digest(raw)}
        actual['source_commit'] = '0' * 40
        with self.assertRaisesRegex(packet.AdapterError, 'actual plan differs'):
            with stage_runtime.parser_scope(self.executor, ROOT, ref, actual, raw):
                pass

    def test_qualification_pending_fail_closed_before_runner(self):
        with self.assertRaisesRegex(packet.AdapterError, 'missing actual artifacts'):
            admission.validate_prerequisites(ROOT, {}, self.runner, 'missing-plan')

    def markers(self):
        return {protocol.EXPERIMENT_ENV: '1', 'DATAFLOWBENCH_V092_RELEASE_EXECUTION': '1', 'DATAFLOWBENCH_V092_GROUP_ID': protocol.GROUP}

    def test_real_inner_guard_and_outer_markers(self):
        env = self.markers()
        admission.require_markers(env)
        with mock.patch.dict(os.environ, env, clear=True):
            self.runner._require_launch_guard(protocol.GROUP)
        for key in env:
            bad = dict(env)
            bad.pop(key)
            with self.assertRaises(packet.AdapterError):
                admission.require_markers(bad)
            if key != protocol.EXPERIMENT_ENV:
                with mock.patch.dict(os.environ, bad, clear=True), self.assertRaises(ValueError):
                    self.runner._require_launch_guard(protocol.GROUP)
        with self.assertRaises(packet.AdapterError):
            admission.require_markers({**env, protocol.FIXTURE_ENV: '1'})

    def test_child_ledger_metadata_not_lost(self):
        parent = {'ledger_rows': 109, 'ledger_sha256': 'a' * 64, 'ledger_ref': {'path': 'history', 'sha256': 'a' * 64, 'stat': {'ino': 42}}}
        selected = bridge.child_ledger_selector(parent)
        self.assertEqual(selected['rows'], 109)
        self.assertEqual(selected['stat'], parent['ledger_ref']['stat'])
        self.assertNotIn('rows', parent['ledger_ref'])
        for rows in (None, True, 108):
            with self.assertRaises(packet.AdapterError):
                bridge.child_ledger_selector({**parent, 'ledger_rows': rows})

    def test_graph_keeps_original_provider_and_all_roles(self):
        old = self.core['runtime_module_graph']
        bridge.validate_graph_roles(ROOT, old, {}, {})
        changed = copy.deepcopy(old)
        changed.pop('replacement05')
        with self.assertRaises(packet.AdapterError):
            bridge.validate_graph_roles(ROOT, changed, {}, {})
        changed = copy.deepcopy(old)
        changed['incoming_recovery']['sha256'] = '0' * 64
        with self.assertRaises(packet.AdapterError):
            bridge.validate_graph_roles(ROOT, changed, {}, {})

    def test_dict_cannot_transfer_opaque_runtime(self):
        with self.assertRaises(packet.AdapterError):
            bridge.runtime_objects(None, {}, None)

    def test_current_head_assumption_explicit(self):
        stage_runtime.require_current_head(ROOT, {'plan_commit': 'a'}, lambda *args: 'a')
        with self.assertRaises(packet.AdapterError):
            stage_runtime.require_current_head(ROOT, {'plan_commit': 'old'}, lambda *args: 'new')

    def test_full_gate_not_inferred_from_partial(self):
        with self.assertRaises(packet.AdapterError):
            supervisor.require_full_summary({'status': 'partial-evidence-verified', 'selected_groups': 83, 'partitions': 87, 'rows': 4144, 'known_stale': 0}, {})

    def test_reviewed_environment_reaches_actual_runner_guard(self):
        group = next((g for g in self.old['groups'] if g['id'] == protocol.GROUP))
        before = copy.deepcopy(group)
        env = admission.child_environment(group)
        self.assertEqual(group, before)
        with mock.patch.dict(os.environ, env, clear=True):
            self.runner._require_launch_guard(protocol.GROUP)
        with self.assertRaises(packet.AdapterError):
            admission.child_environment({**group, 'environment': {'PATH': '/usr/bin', protocol.FIXTURE_ENV: '1'}})

    def first_case_fixture(self, capability):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        plan_path = 'fixture-plan.json'
        case_id = 'fixture-first-attempted-case'
        selection = {'configuration': 'joern-current108', 'disposition': 'attempted'}
        if capability is not None:
            selection['capability'] = capability
        plan = {'output_root': 'out', 'runtime': {'joern': 'never-invoked'}, 'identity': {'fixture': True}, 'fresh_qualification': {'sha256': 'f' * 64}, 'cases': {case_id: selection}}
        (root / plan_path).write_text(json.dumps(plan))
        seen = []

        def process_run(argv, directory, *args, **kwargs):
            (directory / 'version.stdout').write_text('Joern 4.0.660')
            return {'exit_status': 0, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped'}

        def analysis(*args):
            seen.append(args[-1])
            raise StopAfterGroups('first analysis sentinel')
        engine = types.SimpleNamespace(process=types.SimpleNamespace(run=process_run), env_for=lambda rt: {}, run_case=analysis)
        context = {'engine': engine, 'cases': {case_id: {'id': case_id}}}
        population = ({'fixture_revision': 'fixture'}, [{'id': case_id, 'path': 'not-read.swift'}], [], None, 'p' * 64)
        stack = __import__('contextlib').ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(self.runner, 'validate_plan', return_value=(plan, {'synthetic': True}, context)))
        stack.enter_context(mock.patch.object(self.runner.common, 'load_common_population', return_value=population))
        stack.enter_context(mock.patch.object(self.runner.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=200 * 1024 ** 3)))
        stack.enter_context(mock.patch.dict(os.environ, self.markers(), clear=True))
        return (root, plan_path, seen)

    def test_actual_execute_first_case_capability_and_mode(self):
        (root, path, seen) = self.first_case_fixture({'model_mode': 'on'})
        with self.assertRaisesRegex(StopAfterGroups, 'first analysis sentinel'):
            self.runner.execute(root, path, root / 'out' / 'attempt')
        self.assertEqual(seen, ['on'])

    def test_actual_execute_missing_first_capability_never_analyzes(self):
        (root, path, seen) = self.first_case_fixture(None)
        with self.assertRaisesRegex(ValueError, 'explicit capability'):
            self.runner.execute(root, path, root / 'out' / 'attempt')
        self.assertEqual(seen, [])

    def test_actual_execute_invalid_first_mode_never_analyzes(self):
        (root, path, seen) = self.first_case_fixture({'model_mode': 'inferred'})
        with self.assertRaisesRegex(ValueError, 'model mode must be explicit'):
            self.runner.execute(root, path, root / 'out' / 'attempt')
        self.assertEqual(seen, [])
if __name__ == '__main__':
    unittest.main()
