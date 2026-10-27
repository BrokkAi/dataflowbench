"""Private controller composition: real graph/stages/writers, synthetic evidence.

No benchmark/qualification is invoked. Authority, historical evidence, live
resource observations, and analyzer work are explicit fixture I/O seams. Tiny
Popen controls exercise only post-Popen failure cleanup. Terminal positives use
synthetic rows and stopped process observations, never production evidence.
"""
from pathlib import Path
import contextlib
import copy
import json
import os
import subprocess
import sys
import time
import types
import unittest
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import packet
import protocol
import supervisor
import test_graph95 as fixtures


class DurableTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.Graph95Tests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.Graph95Tests.tearDownClass.__func__)
    setUp = fixtures.Graph95Tests.setUp
    prepare = fixtures.Graph95Tests.prepare
    artifact = fixtures.Graph95Tests.artifact
    fixture = fixtures.Graph95Tests.fixture

    def current(self):
        graph = self.prepare()
        core, manifest, ledger, lock, fd = self.fixture(graph)
        contract = packet.document(self.root, core['contract'])
        contract['groups'][0].update(maximum_attempts=5, environment={'PATH': os.environ['PATH']},
                                     argv=['not-dispatched-fixture'])
        contract['execution_series'] = 2
        core.pop('core_identity')
        core.update(contract=self.artifact('candidate/contract.json', contract),
                    dispatch_groups=[protocol.GROUP], lock_path=lock.path,
                    qualification_namespace='candidate/qualification')
        identity = self.artifact('candidate/core.json', core)
        core['core_identity'] = identity
        base = core['sidecar_namespace'] + '/group'
        slot = {'attempt_id': protocol.ATTEMPT,
                **{key: base + '/' + filename for key, filename in (
                    ('admission_path', 'admission.json'), ('phase_gate_path', 'phase.json'),
                    ('completion_path', 'completion.json'), ('analyzer_phase_path', 'analyzer-phase.json'))}}
        manifest = self.artifact('candidate/manifest.json', {
            'core_identity': identity, 'execution_admission_slots': {protocol.GROUP: slot}})
        core['prerequisite_refs'] = {'current_manifest': manifest,
            'external_launch_review': {'path': 'fixture-review', 'sha256': '1' * 64},
            'authorization_bundle': {'path': 'fixture-authority', 'sha256': '2' * 64}}
        return graph, core, manifest, ledger, fd, slot

    def runtime_io(self, graph, core, *, after=False):
        modules = {name: graph.module(name) for name in self.frozen.REQUIRED_GRAPH_NAMES}
        summary = {'status': 'fresh-evidence-verified', 'selected_groups': 84 if after else 83,
                   'partitions': 92 if after else 87, 'rows': 4252 if after else 4144,
                   'known_stale': 0, 'missing_groups': [] if after else [protocol.GROUP],
                   'full_release_gate_satisfied': after}
        validated = {'plan': packet.document(self.root, core['contract']),
                     'bytes_sha256': core['contract']['sha256']}
        objects = {'modules': modules, 'validated': validated, 'checker_summary': summary,
                   'configuration_summary': {'status': 'ready-to-execute' if after else 'pending',
                                             'execution_requested': False}}
        return self.frozen.ActualRuntimeContext(self.root, 'after' if after else 'before', graph,
            modules, {'context_digest': 'd' * 64, 'ledger_rows': 110 if after else 109,
                     'graph_provenance': graph.module('joern05_bridge').graph_provenance(graph)}, objects)

    @contextlib.contextmanager
    def parent_io(self, graph, core, ledger):
        current = graph.module('joern05_supervisor')
        stage = graph.module('joern05_stage_runtime')
        history = graph.module('joern05_history')
        admission = graph.module('joern05_admission')
        controller = graph.module('supervisor24')
        original_snapshot = current._snapshot

        def snapshot(root, given_core, given_graph, index):
            if index == 0:
                return original_snapshot(root, given_core, given_graph, index)
            raw = (root / 'reports/releases/v0.9.2/ledger-v1.jsonl').read_bytes()
            path = core['sidecar_namespace'] + '/stages/stage-01-ledger.jsonl'
            graph.module('protocol24').write_immutable_bytes(root, path, raw)
            return {'path': path, 'sha256': packet.digest(raw), 'rows': 110}

        def io(root, core, *, graph, mode, ledger_bytes):
            return self.runtime_io(graph, core, after=mode == 'after')

        # Only acquisition/history/resource I/O is replaced. Actual current
        # create_parent/build_successor/write_completion and receipts remain.
        with mock.patch.dict(os.environ, {controller.FIXTURE_ENV: '1'}), \
             mock.patch.object(stage, 'load_runtime_context', io), \
             mock.patch.object(history, 'validate', return_value={'ledger_prefix': ledger}), \
             mock.patch.object(current, '_snapshot', snapshot), \
             mock.patch.object(graph.module('joern05_protocol'), 'require_terminal_tail'), \
             mock.patch.object(admission, 'validate_execution_authority', return_value={'fixture': True}), \
             mock.patch.object(current, '_fresh_gate', return_value={'fixture_resource_io': True}):
            yield current, controller

    def terminal(self, core, *, status='completed'):
        return {'tool': 'joern', 'group_id': protocol.GROUP, 'attempt_id': protocol.ATTEMPT,
                'source_commit': core['source_commit'], 'plan_commit': core['plan_commit'],
                'contract_sha256': core['contract']['sha256'], 'execution_series': 2,
                'status': status, 'exit_code': 0 if status == 'completed' else 1,
                'timed_out': False, 'capacity_loss': None,
                'process_ownership': {'schema': 'invocation-process-ownership/v1',
                    'cleanup_status': 'tracked-processes-stopped', 'root_pid': 123456,
                    'descendant_containment': 'unproven', 'tracking_interval_seconds': 2.0,
                    'tracked_processes': [{'pid': 123456, 'start_identity': 'fixture-stopped-birth'}]}}

    def test_command_real_environment_and_singleton_binding(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        current = graph.module('joern05_supervisor')
        result = current.command_spec(self.root, core, manifest, {'path': 'request', 'sha256': 'a' * 64},
            {'path': 'parent', 'sha256': 'b' * 64}, graph=graph, lock_fd=fd,
            witness_fd=fd + 1, token='fixture-token', popen_monotonic=time.monotonic())
        self.assertEqual(result['group_id'], protocol.GROUP)
        self.assertIn('child', result['argv'])
        graph.module('joern05_admission').require_markers(result['environment'])
        self.assertEqual(result['graph_sha256'], graph.graph_sha256)
        core['dispatch_groups'] = ['bifrost-smoke']
        with self.assertRaises(ValueError):
            current.run_parent(self.root, core, manifest, graph=graph, held_lock=None)

    def test_post_popen_birth_failure_reaps_only_owned_control_child_and_fds(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        control = None
        real_popen = subprocess.Popen
        process_calls = 0
        with self.parent_io(graph, core, ledger) as (current, controller):

            def process(pid):
                nonlocal process_calls
                process_calls += 1
                if process_calls == 2:
                    raise RuntimeError('fixture post-Popen birth probe unavailable')
                return {'pid': pid, 'birth_identity': 'fixture-birth'}

            def popen(spec, **kwargs):
                nonlocal control
                # Task-owned, harmless sleeping Python; no benchmark argv is
                # dispatched. All actual parent FD/stream setup still executes.
                control = real_popen([sys.executable, '-B', '-E', '-c', 'import time; time.sleep(60)'], **kwargs)
                return control

            descriptors = []
            real_pipe = controller._open_child_stage_identity_pipe
            def pipe():
                pair = real_pipe()
                descriptors.extend(pair)
                return pair
            with os.fdopen(os.dup(fd), 'rb') as lock, \
                 mock.patch.object(controller, '_process', process), \
                 mock.patch.object(controller, '_birth', return_value='fixture-birth'), \
                 mock.patch.object(controller, '_open_child_stage_identity_pipe', pipe), \
                 mock.patch('subprocess.Popen', popen):
                with self.assertRaisesRegex(RuntimeError, 'birth probe unavailable'):
                    current.run_parent(self.root, core, manifest, graph=graph, held_lock=lock)
            self.assertIsNotNone(control)
            self.assertIsNotNone(control.poll())
            stop = json.loads((self.root / core['sidecar_namespace'] / 'stop.json').read_bytes())
            self.assertTrue(stop['cleanup']['coordinator_reaped'])
            self.assertEqual(stop['cleanup']['signal_scope'], 'popen-owned-direct-child-only')
            self.assertFalse(stop['semantic_completion_inferred'])
            for descriptor in descriptors:
                with self.assertRaises(OSError):
                    os.fstat(descriptor)
            os.fstat(fd)  # Caller's canonical lock remains owned by caller.
            self.assertFalse((self.root / slot['completion_path']).exists())

    def test_popen_failure_closes_pipe_and_writes_no_terminal(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        with self.parent_io(graph, core, ledger) as (current, controller):
            descriptors = []
            original = controller._open_child_stage_identity_pipe
            def pipe():
                pair = original()
                descriptors.extend(pair)
                return pair
            with os.fdopen(os.dup(fd), 'rb') as lock, \
                 mock.patch.object(controller, '_open_child_stage_identity_pipe', pipe), \
                 mock.patch.object(controller, '_process', side_effect=lambda pid: {'pid': pid, 'birth_identity': 'fixture-birth'}), \
                 mock.patch.object(controller, '_birth', return_value='fixture-birth'), \
                 mock.patch('subprocess.Popen', side_effect=OSError('fixture Popen denied')):
                with self.assertRaisesRegex(OSError, 'Popen denied'):
                    current.run_parent(self.root, core, manifest, graph=graph, held_lock=lock)
            for descriptor in descriptors:
                with self.assertRaises(OSError):
                    os.fstat(descriptor)
            self.assertFalse((self.root / slot['completion_path']).exists())
            self.assertFalse((self.root / 'reports/releases/v0.9.2/attempts' / protocol.ATTEMPT).exists())

    def test_parent_actual_successor_finalization_and_second_launch_denial(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        terminal = self.terminal(core)
        terminal_path = 'reports/releases/v0.9.2/attempts/' + protocol.ATTEMPT + '/completed.json'
        class StoppedChild:
            pid = 123456
            def poll(self): return 0
            def wait(self, timeout=None): return 0
        with self.parent_io(graph, core, ledger) as (current, controller):
            def complete(child, validated, group, **kwargs):
                self.assertEqual(group, protocol.GROUP)
                self.assertIsInstance(kwargs['stage'], self.frozen.ParentStage)
                self.artifact(terminal_path, terminal)
                live = self.root / 'reports/releases/v0.9.2/ledger-v1.jsonl'
                live.write_bytes(live.read_bytes() + packet.canonical(terminal))
                return 0
            with os.fdopen(os.dup(fd), 'rb') as lock, \
                 mock.patch('subprocess.Popen', return_value=StoppedChild()), \
                 mock.patch.object(controller, '_process', side_effect=lambda pid: {'pid': pid, 'birth_identity': 'fixture-birth'}), \
                 mock.patch.object(controller, '_birth', return_value='fixture-birth'), \
                 mock.patch.object(controller, '_wait_group_child', complete), \
                 mock.patch.object(controller, '_terminal_continuation_safety', return_value={'fixture_resource_io': True}), \
                 mock.patch.object(graph.module('runtime_loaders24'), 'scoped_runtime_loaders', return_value=contextlib.nullcontext()):
                result = current.run_parent(self.root, core, manifest, graph=graph, held_lock=lock)
                self.assertEqual(result['checker_summary']['selected_groups'], 84)
                self.assertEqual(result['child_exit_code'], 0)
                self.assertTrue((self.root / slot['completion_path']).is_file())
                stage = packet.document(self.root, result['stage_after'])
                self.assertEqual(stage['ledger_rows'], 110)
                self.assertEqual(stage['predecessor_receipt_ref']['path'],
                    core['sidecar_namespace'] + '/stages/stage-00.json')
                self.assertEqual(stage['graph_sha256'], graph.graph_sha256)
                # A second invocation cannot reuse the exclusive source snapshot.
                with self.assertRaises((ValueError, FileExistsError)):
                    current.run_parent(self.root, core, manifest, graph=graph, held_lock=lock)

    def test_actual_terminal_validator_tool_and_containment_near_misses(self):
        graph, core, *_ = self.current()
        checker = graph.module('joern05_protocol')._terminal_identity
        row = self.terminal(core)
        kwargs = dict(group_id=protocol.GROUP, attempt_id=protocol.ATTEMPT,
                      source_commit=core['source_commit'], plan_commit=core['plan_commit'],
                      contract_sha256=core['contract']['sha256'], execution_series=2, label='fixture')
        checker(row, **kwargs)
        for key, value in (('tool', 'bifrost'), ('attempt_id', 'old-attempt'),
                           ('exit_code', 1), ('timed_out', True), ('capacity_loss', 'lost'),
                           ('process_ownership', {})):
            with self.subTest(key=key):
                bad = {**row, key: value}
                with self.assertRaises(ValueError): checker(bad, **kwargs)

    def child_fixture(self, mutation=None):
        graph, core, manifest, ledger, fd, slot = self.current()
        current = graph.module('joern05_supervisor')
        controller = graph.module('supervisor24')
        source = graph.module('joern05_stage_runtime')
        admission = graph.module('joern05_admission')
        frozen = graph.module('bridge19')
        started = time.monotonic()
        token = 'a' * 32
        read_fd, write_fd = controller._open_child_stage_identity_pipe()
        self.addCleanup(lambda: self.safe_close(read_fd))
        self.addCleanup(lambda: self.safe_close(write_fd))
        runtime_calls = []
        def io(root, core, *, graph, mode, ledger_bytes):
            runtime_calls.append(mode)
            return self.runtime_io(graph, core)
        # Synthetic native birth I/O only. Actual opaque receipt guard, pipe
        # producer/consumer, all same-object graph and stage bodies remain.
        birth = lambda pid: 'fixture-child' if pid == os.getpid() else 'fixture-parent'
        with mock.patch.object(source, 'load_runtime_context', io), \
             mock.patch.object(controller, '_birth', birth), \
             mock.patch.object(controller, '_process', side_effect=lambda pid: {'pid': pid, 'birth_identity': birth(pid)}), \
             mock.patch.object(admission, 'validate_execution_authority', return_value={'fixture': True}):
            lock = frozen.capture_lock(self.root, core['lock_path'], os.getppid(), 'fixture-parent')
            parent = graph.module('joern05_bridge').create_parent(self.root, core, manifest, ledger,
                graph=graph, lock_identity=lock, sidecars={}, runtime_role='joern05_stage_runtime',
                runtime_ref=self.adapters['joern05_stage_runtime'])
            parent_ref = current._stage_receipt(self.root, core, manifest, parent, graph)
            request = self.artifact(core['sidecar_namespace'] + '/request.json', {
                'core_identity': core['core_identity'], 'manifest_ref': manifest,
                'prerequisite_refs': core['prerequisite_refs']})
            spec = current.command_spec(self.root, core, manifest, request, parent_ref,
                graph=graph, lock_fd=fd, witness_fd=write_fd, token=token,
                popen_monotonic=started)
            permit = controller.raw_permit(os.getpid(), spec, group_id=protocol.GROUP,
                                           attempt_id=protocol.ATTEMPT, stage=parent)
            parent_permit = controller.raw_permit(os.getppid(), {'argv': ['fixture-parent'],
                                                   'command_spec_sha256': None}, scope='parent', stage=parent)
            parent_admission = self.artifact(core['sidecar_namespace'] + '/parent-admission.json', {
                'schema': 'v092-joern05-parent-admission/v1', 'status': 'admitted',
                'manifest_ref': manifest, 'core_identity': core['core_identity'], 'stage_ref': parent_ref,
                'permit': parent_permit, 'external_review': core['prerequisite_refs']['external_launch_review'],
                'authorization_bundle': core['prerequisite_refs']['authorization_bundle']})
            permit_path = str(Path(slot['admission_path']).parent / 'supervisor-permit.json')
            permit_ref = self.artifact(permit_path, permit)
            group = {'schema': 'v092-joern05-group-admission/v1', 'status': 'admitted',
                'group_id': protocol.GROUP, 'attempt_id': protocol.ATTEMPT,
                'manifest_ref': manifest, 'core_identity': core['core_identity'],
                'parent_stage_ref': parent_ref, 'parent_admission': parent_admission,
                'process': {'pid': os.getpid(), 'birth_identity': 'fixture-child'},
                'supervisor_permit_ref': permit_ref, 'command': spec}
            if mutation:
                mutation(group)
            group_ref = self.artifact(slot['admission_path'], group)
            self.artifact(slot['phase_gate_path'], {
                'schema': 'v092-joern05-phase-gate/v1', 'group_id': protocol.GROUP,
                'attempt_id': protocol.ATTEMPT, 'manifest_ref': manifest,
                'core_identity': core['core_identity'], 'parent_stage_ref': parent_ref,
                'supervisor_permit_ref': permit_ref, 'admission_ref': group_ref,
                'process': {'pid': os.getpid(), 'birth_identity': 'fixture-child'},
                'command_spec_sha256': spec['command_spec_sha256'], 'popen_monotonic': started})
            reached = []
            def engine_io(root, core, manifest_ref, **kwargs):
                # This is the sole analyzer boundary; no executor is invoked.
                self.assertIs(type(kwargs['child']), frozen.ChildStage)
                frozen.assert_child_ready_from_receipt(root, kwargs['child'], parent_receipt_ref=parent_ref,
                    graph=graph, manifest_ref=manifest_ref, core_identity=core['core_identity'],
                    core=core, dispatch_sidecars=kwargs['dispatch_sidecars'],
                    now_monotonic=time.monotonic(), stage_bridge=frozen)
                reached.append(kwargs['child'])
                return {'fixture_engine_io': True}
            with mock.patch.dict(os.environ, spec['environment'], clear=True), \
                 mock.patch.object(sys, 'orig_argv', spec['argv']), \
                 mock.patch.object(current, 'run_child_group', engine_io):
                result = current.consume_dispatch(self.root, core, manifest, graph=graph,
                    request_ref=request, parent_ref=parent_ref, lock_fd=fd,
                    witness_fd=write_fd, token=token, popen_monotonic=started)
            self.assertEqual(result, {'fixture_engine_io': True})
            self.assertEqual(len(reached), 1)
            self.assertEqual(runtime_calls, ['before', 'before'])
            channel = controller._ChildStageIdentityChannel(read_fd)
            try:
                record = channel.drain(process={'pid': os.getpid(), 'birth_identity': 'fixture-child'},
                    parent_process={'pid': os.getppid(), 'birth_identity': 'fixture-parent'},
                    group_id=protocol.GROUP, attempt_id=protocol.ATTEMPT, token=token,
                    stage=parent, parent_stage_ref=parent_ref)
                self.assertEqual(record['child_stage_identity_sha256'], reached[0].identity_sha256)
                self.assertTrue(channel.complete)
            finally:
                channel.close()
            self.assertTrue((self.root / controller._child_stage_witness_path(slot['analyzer_phase_path'])).is_file())

    @staticmethod
    def safe_close(fd):
        try:
            os.close(fd)
        except OSError:
            pass

    def test_actual_child_receipt_guard_pipe_producer_consumer(self):
        self.child_fixture()

    def test_actual_child_rejects_foreign_attempt_before_runtime(self):
        with self.assertRaisesRegex(ValueError, 'dispatch receipt identity'):
            self.child_fixture(lambda value: value.update(attempt_id='joern-swift-common108-attempt-04-series-02'))

    def test_actual_child_rejects_changed_parent_admission(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.child_fixture(lambda value: value.update(parent_admission={'path': 'foreign-parent', 'sha256': '0' * 64}))

    def wait_fixture(self, *, phase_at, exit_at, exit_code=0):
        graph = self.prepare()
        controller = graph.module('supervisor24')
        test_path = 'reports/releases/v0.9.2/acquisition/test-bifrost-v0140-supervisor-24.py'
        reference = {'path': test_path, 'sha256': packet.digest((packet.ROOT / test_path).read_bytes())}
        # Reuse retained source-only phase/clock fixture, not its old assertions.
        # All actual wait/phase/pipe validation bodies are graph-owned controller.
        import uuid
        fixture_name = '_joern05_retained_wait_fixture_' + uuid.uuid4().hex
        fixture = packet.load_bound_module(packet.ROOT, fixture_name, reference)
        self.addCleanup(lambda: sys.modules.pop(fixture_name, None))
        fixture.mod = controller
        case = fixture.TimingTests('runTest')
        case.setUp()
        try:
            case.validated['plan']['groups'] = [{'id': protocol.GROUP, 'deadline_seconds': 1368}]
            root = case.tmp
            phase_path = 'reports/joern05/analyzer-finished.json'
            timeout = 'reports/joern05/coordinator-timeout.json'
            class CurrentPhaseChild(fixture.FakeChild):
                def _write_phase(self):
                    super()._write_phase()
                    target = self.root / self.phase_path
                    value = json.loads(target.read_bytes())
                    value.update(group_id=protocol.GROUP, attempt_id=protocol.ATTEMPT,
                                 registered_deadline_seconds=1368)
                    target.write_bytes(packet.canonical(value))
            child = CurrentPhaseChild(case.clock, phase_at=phase_at, exit_at=exit_at,
                exit_code=exit_code, root=root, phase_path=phase_path, process=case.process)
            channel = case._identity_channel(group_id=protocol.GROUP, attempt_id=protocol.ATTEMPT)
            try:
                return controller._wait_group_child(child, case.validated, protocol.GROUP,
                    popen_monotonic=0.0, root=root, attempt_id=protocol.ATTEMPT,
                    phase_receipt_path=phase_path, timeout_evidence_path=timeout,
                    terminal_receipt_path='reports/releases/v0.9.2/attempts/' + protocol.ATTEMPT + '/completed.json',
                    parent_stage_ref=fixture.PARENT_REF, process=case.process,
                    stage=fixture.ParentStage(), protocol=fixture.Protocol(),
                    child_stage_identity_channel=channel, child_stage_identity_token=fixture.WITNESS_TOKEN,
                    parent_process=fixture.PARENT_PROCESS)
            finally:
                channel.close()
        finally:
            case.tearDown()
            import shutil
            shutil.rmtree(case.tmp)

    def test_real_inherited_wait_uses_1368_600_and_240_tail(self):
        self.assertEqual(self.wait_fixture(phase_at=1960.0, exit_at=2199.0), 0)

    def test_real_inherited_wait_denies_missing_and_late_phase(self):
        for phase in (None, 1969.0):
            with self.subTest(phase=phase), self.assertRaises(subprocess.TimeoutExpired):
                self.wait_fixture(phase_at=phase, exit_at=3000.0)

    def test_real_inherited_wait_tail_finite_and_nonzero_truthful(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.wait_fixture(phase_at=1960.0, exit_at=2201.0)
        self.assertEqual(self.wait_fixture(phase_at=1960.0, exit_at=2000.0, exit_code=1), 1)

    def test_bootstrap_is_once_only_startup_not_completion(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        class LiveFixture:
            def __init__(self, pid): self.pid = pid
            def poll(self): return None
        launches = []
        def spawn(argv, **kwargs):
            launches.append((argv, kwargs))
            return LiveFixture(123450 + len(launches))
        with self.parent_io(graph, core, ledger) as (current, controller), \
             os.fdopen(os.dup(fd), 'rb') as lock, \
             mock.patch('subprocess.Popen', spawn), \
             mock.patch.object(controller, '_process', side_effect=lambda pid: {'pid': pid, 'birth_identity': 'fixture-birth'}), \
             mock.patch.object(current, 'await_startup_ready', return_value={
                 'receipt_ref': {'path': core['sidecar_namespace'] + '/supervision/startup-ready.json',
                                 'sha256': 'a' * 64},
                 'frame': {'schema': supervisor.STARTUP_HANDOFF_SCHEMA, 'status': 'lock-ready'}}):
            request = self.artifact('candidate/bootstrap-request.json', {'fixture': True})
            result = current.bootstrap_parent(self.root, core, manifest, request, graph=graph, held_lock=lock)
            self.assertEqual(result['status'], 'owned-parent-started')
            self.assertFalse(result['semantic_completion_inferred'])
            self.assertFalse(result['execution_terminal_observed'])
            self.assertEqual(len(launches), 2)
            self.assertIn('execution', launches[0][0])
            self.assertTrue(launches[0][1]['start_new_session'])
            self.assertEqual(launches[1][0], ['/usr/bin/caffeinate', '-w', '123451'])
            with self.assertRaises(ValueError):
                current.bootstrap_parent(self.root, core, manifest, request, graph=graph, held_lock=lock)
            self.assertEqual(len(launches), 2)
            self.assertFalse((self.root / slot['completion_path']).exists())

    def test_bootstrap_post_popen_probe_error_reaps_owned_control(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        control = None
        original_popen = subprocess.Popen
        def spawn(argv, **kwargs):
            nonlocal control
            control = original_popen([sys.executable, '-B', '-E', '-c', 'import time; time.sleep(60)'], **kwargs)
            return control
        with self.parent_io(graph, core, ledger) as (current, controller), \
             os.fdopen(os.dup(fd), 'rb') as lock, \
             mock.patch('subprocess.Popen', spawn), \
             mock.patch.object(controller, '_process', side_effect=RuntimeError('fixture bootstrap birth unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'birth unavailable'):
                current.bootstrap_parent(self.root, core, manifest,
                    {'path': 'candidate/request.json', 'sha256': '1' * 64}, graph=graph, held_lock=lock)
            self.assertIsNotNone(control.poll())
            receipt = json.loads((self.root / core['sidecar_namespace'] / 'supervision/bootstrap-failed.json').read_bytes())
            self.assertTrue(receipt['cleanup']['parent']['coordinator_reaped'])
            self.assertEqual(receipt['cleanup']['parent']['signal_scope'], 'popen-owned-direct-child-only')
            self.assertFalse(receipt['semantic_completion_inferred'])

    def test_actual_qualification_command_no_popen_or_execution_namespace_writes(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        with self.parent_io(graph, core, ledger) as (current, controller), \
             os.fdopen(os.dup(fd), 'rb') as lock, \
             mock.patch.object(graph.module('joern05_packet'), 'missing_prerequisites', return_value=[]), \
             mock.patch.object(controller, '_birth', return_value='fixture-birth'), \
             mock.patch('subprocess.Popen', side_effect=AssertionError('qualification cannot Popen')):
            proof = current.qualify_stage(self.root, core, manifest, graph=graph, held_lock=lock)
            self.assertEqual(proof['analyzer_dispatches'], 0)
            self.assertEqual(len(proof['fixed_commands']), 1)
            self.assertFalse(proof['execution_authorized'])
            self.assertFalse(proof['runtime_authority_reusable_across_processes'])
            self.assertFalse((self.root / core['sidecar_namespace']).exists())
            self.assertTrue((self.root / proof['stage_receipt']['path']).is_file())

    def test_qualification_purpose_does_not_require_execution_review(self):
        # Missing future execution artifacts are intentionally absent, never
        # fabricated for the positive qualification shape.
        refs = {}
        names = ('current_contract', 'current_core', 'current_manifest', 'current_source_evidence',
                 'eligible_joern_plan', 'native_decision_review', 'startup_control_review',
                 'first_case_capability_review', 'source_regression_review', 'group_contract_review')
        for name in names:
            refs[name] = self.artifact('candidate/prereqs/' + name + '.json', {'fixture': name})
        self.assertEqual(packet.missing_prerequisites(self.root, refs, purpose='stage-qualification'), [])
        self.assertEqual(packet.missing_prerequisites(self.root, refs), ['external_launch_review'])
        with self.assertRaises(ValueError): packet.missing_prerequisites(self.root, refs, purpose='other')


    def test_parent_exit_receipt_records_return_without_completion_inference(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        current = graph.module('joern05_supervisor')
        controller = graph.module('supervisor24')
        outcome = {'fixture': 'controller-returned'}
        with mock.patch.object(current, 'run_parent', return_value=outcome), \
             mock.patch.object(controller, '_process', return_value={'pid': 123451, 'birth_identity': 'fixture-birth'}):
            self.assertIs(current.execute_recorded(self.root, core, manifest, graph=graph, held_lock=None), outcome)
        receipt = json.loads((self.root / core['sidecar_namespace'] / 'supervision/parent-exit.json').read_bytes())
        self.assertEqual(receipt['exit_code'], 0)
        self.assertTrue(receipt['actual_outcome_returned'])
        self.assertFalse(receipt['semantic_completion_inferred'])
        self.assertEqual(receipt['core_identity'], core['core_identity'])
        self.assertFalse((self.root / slot['completion_path']).exists())

    def test_parent_exit_receipt_preserves_original_exception(self):
        graph, core, manifest, ledger, fd, slot = self.current()
        current = graph.module('joern05_supervisor')
        controller = graph.module('supervisor24')
        original = RuntimeError('fixture original controller error')
        with mock.patch.object(current, 'run_parent', side_effect=original), \
             mock.patch.object(controller, '_process', return_value={'pid': 123451, 'birth_identity': 'fixture-birth'}):
            with self.assertRaises(RuntimeError) as caught:
                current.execute_recorded(self.root, core, manifest, graph=graph, held_lock=None)
        self.assertIs(caught.exception, original)
        receipt = json.loads((self.root / core['sidecar_namespace'] / 'supervision/parent-exit.json').read_bytes())
        self.assertEqual(receipt['exit_code'], 1)
        self.assertFalse(receipt['actual_outcome_returned'])
        self.assertFalse(receipt['semantic_completion_inferred'])
        self.assertEqual(receipt['error']['message'], str(original))
        self.assertFalse((self.root / slot['completion_path']).exists())

if __name__ == '__main__':
    unittest.main()
