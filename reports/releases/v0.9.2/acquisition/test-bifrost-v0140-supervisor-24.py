#!/usr/bin/env python3
"""Canonical BF24 timing regressions; no production launch path is invoked."""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import time
import tempfile
import types
import unittest
from unittest import mock

def _repo_root() -> Path:
    candidates = [Path(__file__).resolve(), Path.cwd().resolve()]
    candidates.extend(Path(__file__).resolve().parents)
    for candidate in candidates:
        root = candidate if (candidate / 'reports/releases/v0.9.2/acquisition').is_dir() else candidate.parent
        if (root / 'reports/releases/v0.9.2/acquisition').is_dir():
            return root
    raise RuntimeError('canonical DataFlowBench repository root is unavailable')

REPO_ROOT = _repo_root()
BASE = Path(__file__).resolve().parent
CANDIDATE_PATH = BASE / 'bifrost-v0140-supervisor-24.py'
spec = importlib.util.spec_from_file_location('bf24_supervisor_canonical', CANDIDATE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
executor_spec = importlib.util.spec_from_file_location(
    'bf24_actual_frozen_executor', REPO_ROOT / 'scripts/execute-release-v092.py')
assert executor_spec is not None and executor_spec.loader is not None
executor = importlib.util.module_from_spec(executor_spec)
executor_spec.loader.exec_module(executor)
fixture_loader_spec = importlib.util.spec_from_file_location(
    'bf24_canonical_current_fixture', BASE / 'test-bifrost-v0140-replacement-24.py')
assert fixture_loader_spec is not None and fixture_loader_spec.loader is not None
fixture_loader = importlib.util.module_from_spec(fixture_loader_spec)
fixture_loader_spec.loader.exec_module(fixture_loader)
opaque_fixture = fixture_loader.load_current_fixture()
admission_spec = importlib.util.spec_from_file_location(
    'bf24_actual_admission', BASE / 'bifrost-v0140-admission-24.py')
assert admission_spec is not None and admission_spec.loader is not None
actual_admission = importlib.util.module_from_spec(admission_spec)
admission_spec.loader.exec_module(actual_admission)
AdmissionError = getattr(actual_admission, 'Admission24Error', getattr(actual_admission, 'Admission23Error', ValueError))

class Clock:
    def __init__(self) -> None:
        self.now = 0.0
    def monotonic(self) -> float:
        return self.now

class Identity:
    index = 0
    source_commit = 's' * 40
    plan_commit = 'p' * 40
    contract_sha256 = 'c' * 64

class Graph:
    graph_sha256 = 'd' * 64

class Stage:
    identity = Identity()
    graph = Graph()
    identity_sha256 = 'a' * 64
    parent_identity_sha256 = 'a' * 64

class ChildStage(Stage):
    identity_sha256 = 'b' * 64
    parent_identity_sha256 = Stage.identity_sha256

class ParentStage(Stage):
    pass

PARENT_REF = {'path': 'reports/parent-stage.json', 'sha256': 'e' * 64}
PARENT_PROCESS = {'pid': 42000, 'birth_identity': 'parent-birth'}
WITNESS_TOKEN = '1' * 32

def child_witness():
    return {
        'schema': 'v092-bifrost-v0140-replay-stage/v4/child-admission',
        'status': 'child-stage-admitted',
        'parent_stage_identity_sha256': ParentStage.identity_sha256,
        'parent_receipt_ref': dict(PARENT_REF), 'parent_stage_index': 0,
        'child_stage_identity_sha256': ChildStage.identity_sha256,
        'child': {'creator_pid': PARENT_PROCESS['pid'],
                  'creator_birth': PARENT_PROCESS['birth_identity'],
                  'pid': FakeChild.pid, 'birth': 'Sun Oct 25 12:56:03 2026'},
        'startup_remaining_seconds': 600.0,
    }

class Protocol:
    def write_immutable(self, root: Path, path: str, value: dict) -> dict[str, str]:
        target = root / Path(*mod._relative(path, 'test output').parts)
        if target.exists():
            raise AssertionError(f'duplicate private output: {path}')
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = mod.canonical_json(value)
        target.write_bytes(raw)
        return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}

def child_ready_ref(root: Path, phase_path: str):
    return Protocol().write_immutable(
        root, mod._child_stage_witness_path(phase_path), child_witness())

class FakeChild:
    pid = 43123
    def __init__(self, clock: Clock, *, phase_at: float | None, exit_at: float,
                 exit_code: int, root: Path, phase_path: str, process: dict) -> None:
        self.clock, self.phase_at, self.exit_at = clock, phase_at, exit_at
        self.exit_code, self.root, self.phase_path, self.process = exit_code, root, phase_path, process
        self.phase_written = False
    def poll(self):
        if self.clock.now >= self.exit_at:
            return self.exit_code
        return None
    def _write_phase(self) -> None:
        if self.phase_written or self.phase_at is None:
            return
        witness = child_witness()
        witness_ref = Protocol().write_immutable(
            self.root, mod._child_stage_witness_path(self.phase_path), witness)
        value = {
            'schema': mod.ANALYZER_PHASE_SCHEMA,
            'status': 'analyzer-process-finished-awaiting-run-group-finalization',
            'automatic_retry': False,
            'group_id': 'bifrost-smoke',
            'attempt_id': 'bifrost-smoke-attempt-03-series-02',
            'pid': self.process['pid'], 'birth_identity': self.process['birth_identity'],
            'source_commit': Stage.identity.source_commit, 'plan_commit': Stage.identity.plan_commit,
            'contract_sha256': Stage.identity.contract_sha256,
            'stage_identity_sha256': ChildStage.identity_sha256,
            'parent_stage_identity_sha256': ParentStage.identity_sha256,
            'graph_sha256': Graph.graph_sha256, 'parent_graph_sha256': Graph.graph_sha256,
            'parent_stage_ref': dict(PARENT_REF), 'child_stage_witness': witness,
            'child_stage_witness_ref': witness_ref,
            'process_result': {'exit_code': 0, 'timed_out': False, 'duration_seconds': 616.0, 'capacity_loss': None},
            'result_sha256': mod.sha256(mod.canonical_json({'exit_code': 0, 'timed_out': False, 'duration_seconds': 616.0, 'capacity_loss': None})),
            'result_status': 'completed',
            'observed_monotonic': self.phase_at, 'registered_deadline_seconds': 706,
            'terminal_receipt_present': False,
        }
        target = self.root / Path(*mod._relative(self.phase_path, 'phase').parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(mod.canonical_json(value))
        self.phase_written = True
    def wait(self, timeout: float):
        target = self.clock.now + timeout
        events = [x for x in (self.phase_at if not self.phase_written else None, self.exit_at) if x is not None and x > self.clock.now]
        next_event = min(events) if events else target
        if next_event <= target:
            self.clock.now = next_event
            if self.phase_at is not None and self.clock.now >= self.phase_at and not self.phase_written:
                self._write_phase()
            if self.clock.now >= self.exit_at:
                return self.exit_code
            raise subprocess.TimeoutExpired(self.pid, timeout)
        self.clock.now = target
        raise subprocess.TimeoutExpired(self.pid, timeout)

class TimingTests(unittest.TestCase):
    def _identity_record(self, process=None, parent_process=None, stage=None,
                         group_id='bifrost-smoke', attempt_id='bifrost-smoke-attempt-03-series-02'):
        process = self.process if process is None else process
        parent_process = PARENT_PROCESS if parent_process is None else parent_process
        stage = ParentStage() if stage is None else stage
        return {
            'schema': mod.CHILD_STAGE_IDENTITY_SCHEMA,
            'status': 'child-stage-admission-verified',
            'group_id': group_id, 'attempt_id': attempt_id, 'token': WITNESS_TOKEN,
            'pid': process['pid'], 'birth_identity': process['birth_identity'],
            'parent_pid': parent_process['pid'], 'parent_birth_identity': parent_process['birth_identity'],
            'parent_stage_identity_sha256': stage.identity_sha256,
            'parent_stage_ref': dict(PARENT_REF), 'parent_stage_index': stage.identity.index,
            'child_stage_identity_sha256': ChildStage.identity_sha256,
            'child': {'creator_pid': parent_process['pid'], 'creator_birth': parent_process['birth_identity'],
                      'pid': process['pid'], 'birth': process['birth_identity']},
            'graph_sha256': Graph.graph_sha256, 'source_commit': stage.identity.source_commit,
            'plan_commit': stage.identity.plan_commit, 'contract_sha256': stage.identity.contract_sha256,
        }

    def _channel_for_record(self, record, *, suffix=b'', close_write=True):
        read_fd, write_fd = mod._open_child_stage_identity_pipe()
        os.write(write_fd, mod.canonical_json(record) + suffix)
        if close_write:
            os.close(write_fd)
        return mod._ChildStageIdentityChannel(read_fd)

    def _identity_channel(self, process=None, parent_process=None, stage=None,
                          group_id='bifrost-smoke', attempt_id='bifrost-smoke-attempt-03-series-02'):
        return self._channel_for_record(self._identity_record(
            process=process, parent_process=parent_process, stage=stage,
            group_id=group_id, attempt_id=attempt_id))

    def setUp(self):
        self.clock = Clock()
        self.original_monotonic = mod.time.monotonic
        mod.time.monotonic = self.clock.monotonic
        self.tmp = Path(tempfile.mkdtemp(prefix='bf24-timing-'))
        self.process = {'pid': FakeChild.pid, 'birth_identity': 'Sun Oct 25 12:56:03 2026'}
        self.validated = {'bytes_sha256': Stage.identity.contract_sha256,
                          'plan': {'groups': [{'id': 'bifrost-smoke', 'deadline_seconds': 706}]}}
        self.original_wait = mod._wait_group_child
        self.original_validate = mod._validate_analyzer_phase
        def wait_wrapper(*args, **kwargs):
            channel = kwargs.setdefault('child_stage_identity_channel', self._identity_channel())
            kwargs.setdefault('child_stage_identity_token', WITNESS_TOKEN)
            try:
                return self.original_wait(*args, **kwargs)
            finally:
                channel.close()
        def validate_wrapper(*args, **kwargs):
            kwargs.setdefault('expected_child_stage_identity_sha256', ChildStage.identity_sha256)
            return self.original_validate(*args, **kwargs)
        mod._wait_group_child = wait_wrapper
        mod._validate_analyzer_phase = validate_wrapper
    def tearDown(self):
        mod._wait_group_child = self.original_wait
        mod._validate_analyzer_phase = self.original_validate
        mod.time.monotonic = self.original_monotonic
    def run_wait(self, *, phase_at, exit_at, exit_code=0):
        phase = 'reports/attempt-03/analyzer-finished.json'
        timeout = 'reports/attempt-03/coordinator-timeout.json'
        child = FakeChild(self.clock, phase_at=phase_at, exit_at=exit_at, exit_code=exit_code,
                          root=self.tmp, phase_path=phase, process=self.process)
        return mod._wait_group_child(child, self.validated, 'bifrost-smoke',
            popen_monotonic=0.0, root=self.tmp,
            attempt_id='bifrost-smoke-attempt-03-series-02', phase_receipt_path=phase,
            timeout_evidence_path=timeout, process=self.process,
            stage=ParentStage(), protocol=Protocol(),
            terminal_receipt_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json',
            parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)
    def read_timeout(self):
        return json.loads((self.tmp / 'reports/attempt-03/coordinator-timeout.json').read_text())
    def test_analyzer_boundary_preserved_and_finalization_tail_is_separate(self):
        # Analyzer-phase return at 1300 = 600 startup + 706 registered lease;
        # successful finalization at 1539 remains inside the separate 240-second tail.
        self.assertEqual(self.run_wait(phase_at=1300.0, exit_at=1539.0), 0)
        self.assertFalse((self.tmp / 'reports/attempt-03/coordinator-timeout.json').exists())
    def test_phase_receipt_wins_same_tick_child_exit_race(self):
        # The child writes its phase receipt immediately before returning.
        # Parent polling must consume that receipt before interpreting exit 0.
        self.assertEqual(self.run_wait(phase_at=1300.0, exit_at=1300.0), 0)
        self.assertFalse((self.tmp / 'reports/attempt-03/coordinator-timeout.json').exists())

    def test_publication_between_exists_and_poll_is_revalidated(self):
        owner = self
        class PublishingChild(FakeChild):
            def poll(self):
                if not self.phase_written:
                    self.phase_at = self.clock.now
                    self._write_phase()
                return 0
        child = PublishingChild(self.clock, phase_at=None, exit_at=1300.0, exit_code=0,
                                root=self.tmp,
                                phase_path='reports/attempt-03/analyzer-finished.json',
                                process=self.process)
        self.assertEqual(mod._wait_group_child(
            child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
            root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
            phase_receipt_path='reports/attempt-03/analyzer-finished.json',
            timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
            process=self.process, stage=ParentStage(), protocol=Protocol(),
                terminal_receipt_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json',
                parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS), 0)
        self.assertFalse((self.tmp / 'reports/attempt-03/coordinator-timeout.json').exists())
    def test_late_phase_receipt_cannot_extend_analyzer_lease(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_wait(phase_at=1307.0, exit_at=1350.0)
        value = self.read_timeout()
        self.assertEqual(value['status'], 'coordinator-timeout-before-analyzer-phase')
        self.assertEqual(value['reason'], 'combined-startup-and-analyzer-lease-expired')
        self.assertFalse(value['semantic_completion_inferred'])
        self.assertFalse(value['ledger_success_written'])
    def test_finalization_timeout_is_typed_and_never_success(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_wait(phase_at=1300.0, exit_at=1541.0)
        value = self.read_timeout()
        self.assertEqual(value['status'], 'coordinator-timeout-during-finalization')
        self.assertEqual(value['phase'], 'finalization')
        self.assertFalse(value['terminal_receipt_present'])
        self.assertFalse(value['semantic_completion_inferred'])
        self.assertFalse(value['ledger_success_written'])
        self.assertEqual(value['registered_deadline_seconds'], 706)
        self.assertEqual(value['finalization_allowance_seconds'], 240)
    def test_initial_combined_lease_timeout_precedes_phase_and_has_no_success(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_wait(phase_at=None, exit_at=1400.0)
        value = self.read_timeout()
        self.assertEqual(value['status'], 'coordinator-timeout-before-analyzer-phase')
        self.assertEqual(value['phase'], 'analyzer')
        self.assertFalse(value['terminal_receipt_present'])
        self.assertFalse(value['ledger_success_written'])
    def test_nonzero_analyzer_exit_after_raw_like_work_is_not_success(self):
        self.assertEqual(self.run_wait(phase_at=None, exit_at=900.0, exit_code=7), 7)
        self.assertFalse((self.tmp / 'reports/attempt-03/coordinator-timeout.json').exists())
    def test_stale_birth_phase_is_rejected(self):
        phase = 'reports/attempt-03/analyzer-finished.json'
        target = self.tmp / phase
        target.parent.mkdir(parents=True, exist_ok=True)
        value = {
            'schema': mod.ANALYZER_PHASE_SCHEMA, 'status': 'analyzer-process-finished-awaiting-run-group-finalization',
            'automatic_retry': False, 'group_id': 'bifrost-smoke', 'attempt_id': 'bifrost-smoke-attempt-03-series-02',
            'pid': FakeChild.pid, 'birth_identity': 'foreign-birth',
            'source_commit': Stage.identity.source_commit, 'plan_commit': Stage.identity.plan_commit,
            'contract_sha256': Stage.identity.contract_sha256, 'stage_identity_sha256': ChildStage.identity_sha256,
            'parent_stage_identity_sha256': ParentStage.identity_sha256,
            'graph_sha256': Graph.graph_sha256, 'parent_graph_sha256': Graph.graph_sha256,
            'parent_stage_ref': dict(PARENT_REF), 'child_stage_witness': child_witness(),
            'process_result': {'exit_code': 0, 'timed_out': False, 'duration_seconds': 616.0, 'capacity_loss': None},
            'result_sha256': mod.sha256(mod.canonical_json({'exit_code': 0, 'timed_out': False, 'duration_seconds': 616.0, 'capacity_loss': None})),
            'result_status': 'completed',
            'observed_monotonic': 1300.0, 'registered_deadline_seconds': 706,
            'terminal_receipt_present': False,
        }
        target.write_bytes(mod.canonical_json(value))
        child = FakeChild(self.clock, phase_at=None, exit_at=1400, exit_code=0,
                          root=self.tmp, phase_path=phase, process=self.process)
        with self.assertRaises(mod.Supervisor24Error):
            mod._wait_group_child(child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
                phase_receipt_path=phase, timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
                process=self.process, stage=ParentStage(), protocol=Protocol(),
                terminal_receipt_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json',
                parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)
    def test_recording_deadline_is_anchored_to_phase_receipt_timestamp(self):
        phase = 'reports/attempt-03/analyzer-finished.json'
        timeout = 'reports/attempt-03/coordinator-timeout.json'
        child = FakeChild(self.clock, phase_at=1300.0, exit_at=2000.0, exit_code=0,
                          root=self.tmp, phase_path=phase, process=self.process)
        child._write_phase()
        self.clock.now = 1541.0
        with self.assertRaises(subprocess.TimeoutExpired):
            mod._wait_group_child(child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
                phase_receipt_path=phase, timeout_evidence_path=timeout, process=self.process,
                stage=ParentStage(), protocol=Protocol(),
                terminal_receipt_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json',
                parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)
        value = self.read_timeout()
        self.assertEqual(value['reason'], 'finalization-deadline-passed-before-parent-observation')
        self.assertEqual(value['finalization_allowance_seconds'], 240)
        self.assertFalse(value['semantic_completion_inferred'])
        self.assertFalse(value['ledger_success_written'])

    def test_timeout_observes_terminal_and_ledger_truth_before_cleanup(self):
        attempt = 'bifrost-smoke-attempt-03-series-02'
        terminal = self.tmp / 'reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json'
        terminal.parent.mkdir(parents=True, exist_ok=True)
        terminal.write_text(mod.canonical_json({'attempt_id': attempt, 'status': 'completed'}).decode())
        ledger = self.tmp / 'reports/releases/v0.9.2/ledger-v1.jsonl'
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(mod.canonical_json({'attempt_id': attempt, 'status': 'completed'}).decode())
        mod._write_coordinator_timeout(
            self.tmp, 'reports/attempt-03/coordinator-timeout.json', phase='finalization',
            reason='late-observation', group_id='bifrost-smoke', attempt_id=attempt,
            process=self.process, stage=ParentStage(), registered=706,
            observed_monotonic=1541.0, protocol=Protocol(),
            terminal_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json')
        value = json.loads((self.tmp / 'reports/attempt-03/coordinator-timeout.json').read_text())
        self.assertTrue(value['terminal_receipt_present'])
        self.assertTrue(value['ledger_success_written'])
        self.assertEqual(value['terminal_observation']['path'],
                         'reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json')
        self.assertEqual(value['cleanup_status'], 'pending-owned-cleanup')

    def test_late_successful_poll_stays_typed_timeout_even_with_terminal_row(self):
        attempt = 'bifrost-smoke-attempt-03-series-02'
        terminal = self.tmp / 'reports/releases/v0.9.2/attempts' / attempt / 'completed.json'
        terminal.parent.mkdir(parents=True, exist_ok=True)
        terminal.write_text(mod.canonical_json({'attempt_id': attempt, 'status': 'completed'}).decode())
        ledger = self.tmp / 'reports/releases/v0.9.2/ledger-v1.jsonl'
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(mod.canonical_json({'attempt_id': attempt, 'status': 'completed'}).decode())
        phase = 'reports/attempt-03/analyzer-finished.json'
        class LateExitChild(FakeChild):
            def poll(self):
                if not self.phase_written:
                    self.phase_at = 1300.0
                    self._write_phase()
                return 0
        child = LateExitChild(self.clock, phase_at=None, exit_at=1541.0, exit_code=0,
                              root=self.tmp, phase_path=phase, process=self.process)
        self.clock.now = 1541.0
        with self.assertRaises(subprocess.TimeoutExpired):
            mod._wait_group_child(
                child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                root=self.tmp, attempt_id=attempt, phase_receipt_path=phase,
                timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
                terminal_receipt_path=f'reports/releases/v0.9.2/attempts/{attempt}/completed.json',
                parent_stage_ref=PARENT_REF, process=self.process, stage=ParentStage(),
                protocol=Protocol(), parent_process=PARENT_PROCESS)
        value = self.read_timeout()
        self.assertEqual(value['reason'], 'child-exit-observed-after-finalization-without-bounded-transition')
        self.assertTrue(value['terminal_receipt_present'])
        self.assertTrue(value['ledger_success_written'])
        self.assertFalse(value['semantic_completion_inferred'])

    def test_phase_timestamp_must_be_after_popen_and_before_observation(self):
        for observed, now in ((-1.0, 100.0), (1300.0, 100.0)):
            with self.subTest(observed=observed, now=now):
                phase = 'reports/attempt-03/analyzer-finished.json'
                mod._phase_receipt(
                    self.tmp, phase,
                    process_result={'exit_code': 0, 'timed_out': False,
                                    'duration_seconds': 616.0, 'capacity_loss': None},
                    result_status='completed', group_id='bifrost-smoke',
                    attempt_id='bifrost-smoke-attempt-03-series-02', process=self.process,
                    stage=ChildStage(), graph_sha256=Graph.graph_sha256,
                    parent_stage_identity_sha256=ParentStage.identity_sha256,
                    parent_graph_sha256=Graph.graph_sha256,
                    parent_stage_ref=PARENT_REF, child_stage_witness=child_witness(),
                    child_stage_witness_ref=child_ready_ref(self.tmp, phase),
                    source_commit=Stage.identity.source_commit,
                    plan_commit=Stage.identity.plan_commit,
                    contract_sha256=Stage.identity.contract_sha256, registered=706,
                    observed_monotonic=observed, protocol=Protocol())
                with self.assertRaises(mod.Supervisor24Error):
                    mod._validate_analyzer_phase(
                        self.tmp, phase, validated=self.validated, group_id='bifrost-smoke',
                        attempt_id='bifrost-smoke-attempt-03-series-02', process=self.process,
                        stage=ParentStage(), registered=706, analyzer_deadline=1306.0,
                        popen_monotonic=0.0, observation_monotonic=now,
                        parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)
                (self.tmp / phase).unlink()
                (self.tmp / mod._child_stage_witness_path(phase)).unlink()

    def test_child_parent_identity_is_distinct_and_bound(self):
        self.assertNotEqual(ChildStage.identity_sha256, ParentStage.identity_sha256)
        phase = 'reports/attempt-03/analyzer-finished.json'
        mod._phase_receipt(
            self.tmp, phase,
            process_result={'exit_code': 0, 'timed_out': False,
                            'duration_seconds': 616.0, 'capacity_loss': None},
            result_status='completed', group_id='bifrost-smoke',
            attempt_id='bifrost-smoke-attempt-03-series-02', process=self.process,
            stage=ChildStage(), graph_sha256=Graph.graph_sha256,
            parent_stage_identity_sha256=ParentStage.identity_sha256,
            parent_graph_sha256=Graph.graph_sha256,
            parent_stage_ref=PARENT_REF, child_stage_witness=child_witness(),
            child_stage_witness_ref=child_ready_ref(self.tmp, phase),
            source_commit=Stage.identity.source_commit,
            plan_commit=Stage.identity.plan_commit,
            contract_sha256=Stage.identity.contract_sha256, registered=706,
            observed_monotonic=1300.0, protocol=Protocol())
        value = json.loads((self.tmp / phase).read_text())
        self.assertEqual(value['stage_identity_sha256'], ChildStage.identity_sha256)
        self.assertEqual(value['parent_stage_identity_sha256'], ParentStage.identity_sha256)
        self.assertEqual(mod._validate_analyzer_phase(
            self.tmp, phase, validated=self.validated, group_id='bifrost-smoke',
            attempt_id='bifrost-smoke-attempt-03-series-02', process=self.process,
            stage=ParentStage(), registered=706, analyzer_deadline=1306.0,
            popen_monotonic=0.0, observation_monotonic=1300.0,
            parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)['value']['parent_stage_identity_sha256'],
            ParentStage.identity_sha256)

    def test_phase_cannot_rotate_child_digest_with_matching_witness_fields(self):
        phase = 'reports/attempt-03/analyzer-finished.json'
        child = FakeChild(self.clock, phase_at=1300.0, exit_at=2000.0, exit_code=0,
                          root=self.tmp, phase_path=phase, process=self.process)
        child._write_phase()
        target = self.tmp / phase
        value = json.loads(target.read_text())
        value['stage_identity_sha256'] = 'f' * 64
        value['child_stage_witness']['child_stage_identity_sha256'] = 'f' * 64
        target.write_bytes(mod.canonical_json(value))
        with self.assertRaises(mod.Supervisor24Error):
            mod._wait_group_child(
                child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
                phase_receipt_path=phase,
                timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
                terminal_receipt_path='reports/releases/v0.9.2/attempts/'
                                    'bifrost-smoke-attempt-03-series-02/completed.json',
                parent_stage_ref=PARENT_REF, process=self.process, stage=ParentStage(),
                protocol=Protocol(), parent_process=PARENT_PROCESS)

    def test_actual_os_pipe_popen_child_binds_pid_birth_parent_and_closes_writer(self):
        """Exercise the real Popen/pass_fds seam, rather than a fake channel."""
        read_fd, write_fd = mod._open_child_stage_identity_pipe()
        stage = ParentStage()
        constants = {
            'schema': mod.CHILD_STAGE_IDENTITY_SCHEMA,
            'status': 'child-stage-admission-verified',
            'group_id': 'bifrost-smoke',
            'attempt_id': 'bifrost-smoke-attempt-03-series-02',
            'token': WITNESS_TOKEN,
            'parent_stage_identity_sha256': stage.identity_sha256,
            'parent_stage_ref': dict(PARENT_REF),
            'parent_stage_index': stage.identity.index,
            'child_stage_identity_sha256': ChildStage.identity_sha256,
            'graph_sha256': stage.graph.graph_sha256,
            'source_commit': stage.identity.source_commit,
            'plan_commit': stage.identity.plan_commit,
            'contract_sha256': stage.identity.contract_sha256,
        }
        child_code = (
            "import json,os,subprocess,time\n"
            "def b(pid): return 'test-birth-' + str(pid)\n"
            "v=json.loads(%r); pid=os.getpid(); ppid=os.getppid(); birth=b(pid); pbirth=b(ppid)\n"
            "v.update(pid=pid,birth_identity=birth,parent_pid=ppid,parent_birth_identity=pbirth,child={'creator_pid':ppid,'creator_birth':pbirth,'pid':pid,'birth':birth})\n"
            "fd=%d; os.write(fd,(json.dumps(v,sort_keys=True,separators=(',',':'))+'\\n').encode()); os.close(fd); time.sleep(0.05)"
        ) % (json.dumps(constants, sort_keys=True), write_fd)
        child = None
        channel = mod._ChildStageIdentityChannel(read_fd)
        old_birth = mod._birth
        try:
            # The production birth provider shells to ps, which is denied in
            # this sandbox. Keep the real Popen/FD seam while binding a
            # deterministic process-birth adapter for this private probe.
            mod._birth = lambda pid: 'test-birth-' + str(pid)
            self.assertFalse(os.get_inheritable(read_fd))
            self.assertTrue(os.get_inheritable(write_fd))
            child = subprocess.Popen([sys.executable, '-c', child_code],
                                     close_fds=True, pass_fds=(write_fd,))
            os.close(write_fd)
            write_fd = -1
            process = mod._process(child.pid)
            parent_process = mod._process(os.getpid())
            self.assertEqual(child.wait(timeout=2), 0)
            record = channel.drain(
                process=process, parent_process=parent_process,
                group_id='bifrost-smoke', attempt_id='bifrost-smoke-attempt-03-series-02',
                token=WITNESS_TOKEN, stage=stage, parent_stage_ref=PARENT_REF)
            self.assertEqual(record['child_stage_identity_sha256'], ChildStage.identity_sha256)
            self.assertEqual(record['pid'], child.pid)
            self.assertEqual(record['parent_pid'], os.getpid())
            self.assertEqual(channel.evidence()['state'], 'accepted')
        finally:
            mod._birth = old_birth
            channel.close()
            with self.assertRaises(OSError):
                os.fstat(read_fd)
            if write_fd >= 0:
                os.close(write_fd)
            if child is not None and child.poll() is None:
                child.kill(); child.wait(timeout=2)

    def test_build_command_token_is_in_argv_spec_and_raw_permit_identity(self):
        root = Path(tempfile.mkdtemp(prefix='bf24-command-'))
        group = 'bifrost-smoke'
        attempt = mod._attempt_id(group)
        manifest = {'execution_admission_slots': {
            group: {'attempt_id': attempt, 'admission_path': 'reports/group/admission.json'}}}
        core = {}
        context = {'execution_authorized': False,
                   'context_digest': 'd' * 64,
                   'canonical_contract_path_and_contract_sha256': {'path': 'contract.json', 'sha256': 'c' * 64},
                   'source_commit': Stage.identity.source_commit,
                   'plan_commit': Stage.identity.plan_commit,
                   'validated_full_normalized_plan': {'plan': {'execution_authorized': True,
                                                              'groups': [{'id': group}]}}}
        args = dict(root=root, manifest_path=mod.MANIFEST_PATH, manifest_sha256='m' * 64,
                    bridge_context=context, group_id=group, fixture_only=True,
                    context_path='reports/group/bridge-context.json', lock_fd=7,
                    stage=ParentStage(), bridge=object(), admission=object(),
                    protocol=types.SimpleNamespace(dispatch_groups=lambda value: [group]),
                    manifest=manifest, core=core, parent_stage_ref=PARENT_REF,
                    popen_monotonic=1.0)
        with mock.patch.dict(os.environ, {mod.FIXTURE_ENV: '1'}), \
             mock.patch.object(mod, '_temporary_fixture', return_value=True), \
             mock.patch.object(mod, '_validate_context', return_value=context), \
             mock.patch.object(mod, '_environment', return_value={'PATH': '/usr/bin'}), \
             mock.patch.object(mod, '_child_interpreter', return_value=sys.executable):
            first = mod.build_group_command(child_stage_witness_fd=9,
                                             child_stage_witness_token=WITNESS_TOKEN, **args)
            second = mod.build_group_command(child_stage_witness_fd=9,
                                              child_stage_witness_token='2' * 32, **args)
        self.assertIn('--child-stage-witness-token', first['argv'])
        self.assertEqual(first['argv'][first['argv'].index('--child-stage-witness-token') + 1], WITNESS_TOKEN)
        self.assertEqual(first['argv'][first['argv'].index('--child-stage-witness-fd') + 1], '9')
        self.assertRegex(first['command_spec_sha256'], r'^[0-9a-f]{64}$')
        self.assertNotEqual(first['command_spec_sha256'], second['command_spec_sha256'])
        # The frozen admission validator accepts exactly its sealed field set;
        # phase/FD/token remain argv-bound and must not become ad-hoc spec keys.
        admitted = dict(first)
        for field in ('stage_identity_sha256', 'parent_stage_identity_sha256', 'graph_sha256'):
            admitted.pop(field)
        admitted['command_spec_sha256'] = mod.sha256(mod.canonical_json(
            {key: value for key, value in admitted.items() if key != 'command_spec_sha256'}))
        actual_admission._validate_command_spec(
            admitted, group_id=group, attempt_id=attempt, bridge_context=context)
        extra = dict(admitted)
        extra['phase_receipt_path'] = 'reports/foreign/analyzer.json'
        extra['command_spec_sha256'] = mod.sha256(mod.canonical_json(
            {key: value for key, value in extra.items() if key != 'command_spec_sha256'}))
        with self.assertRaises(AdmissionError):
            actual_admission._validate_command_spec(
                extra, group_id=group, attempt_id=attempt, bridge_context=context)
        with self.assertRaises(mod.Supervisor24Error):
            mod.build_group_command(child_stage_witness_fd=2,
                                    child_stage_witness_token=WITNESS_TOKEN, **args)
        with self.assertRaises(mod.Supervisor24Error):
            mod.build_group_command(child_stage_witness_fd=9,
                                    child_stage_witness_token='bad-token', **args)
        old_birth = mod._birth
        mod._birth = lambda pid: 'test-birth-' + str(pid)
        try:
            permit = mod.raw_permit(os.getpid(), first, group_id=group, attempt_id=attempt,
                                    stage=ParentStage())
        finally:
            mod._birth = old_birth
        self.assertEqual(permit['command_spec_sha256'], first['command_spec_sha256'])
        self.assertEqual(permit['argv_sha256'], mod.sha256(mod.canonical_json(first['argv'])))

    def test_child_identity_pipe_wrong_pid_birth_parent_and_token_fail_closed(self):
        mutations = {
            'pid': lambda value: value.update(pid=value['pid'] + 1),
            'birth_identity': lambda value: value.update(birth_identity='foreign-birth'),
            'parent_pid': lambda value: value.update(parent_pid=value['parent_pid'] + 1),
            'parent_birth_identity': lambda value: value.update(parent_birth_identity='foreign-parent'),
            'token': lambda value: value.update(token='2' * 32),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                record = self._identity_record()
                mutate(record)
                channel = self._channel_for_record(record)
                try:
                    with self.assertRaises(mod.Supervisor24Error):
                        channel.drain(process=self.process, parent_process=PARENT_PROCESS,
                                      group_id='bifrost-smoke',
                                      attempt_id='bifrost-smoke-attempt-03-series-02',
                                      token=WITNESS_TOKEN, stage=ParentStage(),
                                      parent_stage_ref=PARENT_REF)
                finally:
                    channel.close()

    def test_child_identity_pipe_missing_extra_oversize_and_writer_held_open_fail_closed(self):
        # EOF without a frame is a typed missing witness, never a successful phase.
        read_fd, write_fd = mod._open_child_stage_identity_pipe()
        os.close(write_fd)
        missing = mod._ChildStageIdentityChannel(read_fd)
        try:
            with self.assertRaises(mod.Supervisor24Error):
                missing.drain(process=self.process, parent_process=PARENT_PROCESS,
                              group_id='bifrost-smoke',
                              attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                              stage=ParentStage(), parent_stage_ref=PARENT_REF)
        finally:
            missing.close()
        # A nonempty partial frame is distinct from an empty EOF and is also rejected.
        read_fd, write_fd = mod._open_child_stage_identity_pipe()
        os.write(write_fd, b'{"schema":"partial"')
        os.close(write_fd)
        partial = mod._ChildStageIdentityChannel(read_fd)
        try:
            with self.assertRaises(mod.Supervisor24Error):
                partial.drain(process=self.process, parent_process=PARENT_PROCESS,
                              group_id='bifrost-smoke',
                              attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                              stage=ParentStage(), parent_stage_ref=PARENT_REF)
        finally:
            partial.close()
        # A second frame and an oversized frame are both rejected before acceptance.
        record = self._identity_record()
        channel = self._channel_for_record(record, suffix=mod.canonical_json(record))
        try:
            with self.assertRaises(mod.Supervisor24Error):
                channel.drain(process=self.process, parent_process=PARENT_PROCESS,
                              group_id='bifrost-smoke',
                              attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                              stage=ParentStage(), parent_stage_ref=PARENT_REF)
        finally:
            channel.close()
        channel = self._channel_for_record(record, suffix=b'x' * (mod.CHILD_STAGE_IDENTITY_MAX_BYTES + 1))
        try:
            with self.assertRaises(mod.Supervisor24Error):
                channel.drain(process=self.process, parent_process=PARENT_PROCESS,
                              group_id='bifrost-smoke',
                              attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                              stage=ParentStage(), parent_stage_ref=PARENT_REF)
        finally:
            channel.close()
        # A live writer makes the nonblocking parent drain pending; EOF then seals it.
        read_fd, write_fd = mod._open_child_stage_identity_pipe()
        os.write(write_fd, mod.canonical_json(record))
        held = mod._ChildStageIdentityChannel(read_fd)
        try:
            self.assertIsNone(held.drain(process=self.process, parent_process=PARENT_PROCESS,
                                         group_id='bifrost-smoke',
                                         attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                                         stage=ParentStage(), parent_stage_ref=PARENT_REF))
            os.close(write_fd)
            self.assertIsNotNone(held.drain(process=self.process, parent_process=PARENT_PROCESS,
                                            group_id='bifrost-smoke',
                                            attempt_id='bifrost-smoke-attempt-03-series-02', token=WITNESS_TOKEN,
                                            stage=ParentStage(), parent_stage_ref=PARENT_REF))
        finally:
            held.close()

    def test_child_writes_identity_after_opaque_guard_before_runtime_engine(self):
        tree = ast.parse(CANDIDATE_PATH.read_text(), filename=str(CANDIDATE_PATH))
        fn = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == '_run_frozen_group')
        calls = [(node.lineno, node.func.id) for node in ast.walk(fn)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        write_line = next(line for line, name in calls if name == '_write_child_stage_identity')
        runtime_line = next(line for line, name in calls if name == '_actual_runtime_context')
        self.assertLess(write_line, runtime_line)
        source = CANDIDATE_PATH.read_text()
        self.assertIn('pass_fds=(lock.fileno(), witness_write_fd)', source)
        self.assertIn('os.close(witness_write_fd)', source)

    def test_phase_child_witness_ref_process_and_creator_near_misses_fail_closed(self):
        mutations = ('child_stage_witness_ref', 'child_pid', 'creator_pid')
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                phase = 'reports/attempt-03/analyzer-finished.json'
                child = FakeChild(self.clock, phase_at=1300.0, exit_at=2000.0, exit_code=0,
                                  root=self.tmp, phase_path=phase, process=self.process)
                child._write_phase()
                target = self.tmp / phase
                value = json.loads(target.read_text())
                if mutation == 'child_stage_witness_ref':
                    value['child_stage_witness_ref']['sha256'] = 'f' * 64
                elif mutation == 'child_pid':
                    value['child_stage_witness']['child']['pid'] += 1
                else:
                    value['child_stage_witness']['child']['creator_pid'] += 1
                target.write_bytes(mod.canonical_json(value))
                with self.assertRaises(mod.Supervisor24Error):
                    mod._wait_group_child(
                        child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                        root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
                        phase_receipt_path=phase,
                        timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
                        terminal_receipt_path='reports/releases/v0.9.2/attempts/'
                                            'bifrost-smoke-attempt-03-series-02/completed.json',
                        parent_stage_ref=PARENT_REF, process=self.process,
                        stage=ParentStage(), protocol=Protocol(), parent_process=PARENT_PROCESS)
                target.unlink()
                (self.tmp / mod._child_stage_witness_path(phase)).unlink()

    def test_actual_opaque_child_stage_witness_rejects_mutated_digest(self):
        fixture = opaque_fixture.ChildReadyReceiptTests(
            'test_receipt_contains_exact_inventory_sidecars_and_positive_child_guard')
        fixture.setUp()
        try:
            child = fixture.child
            parent = fixture.parent
            witness = {
                'schema': 'v092-bifrost-v0140-replay-stage/v4/child-admission', 'status': 'child-stage-admitted',
                'parent_stage_identity_sha256': parent.identity_sha256,
                'parent_receipt_ref': dict(fixture.parent_receipt),
                'parent_stage_index': parent.identity.index,
                'child_stage_identity_sha256': child.identity_sha256,
                'child': dict(child.child_identity), 'startup_remaining_seconds': 100.0,
            }
            process = {'pid': child.child_identity['pid'],
                       'birth_identity': child.child_identity['birth']}
            self.assertEqual(mod._validate_child_stage_witness(
                witness, stage=child, process=process,
                expected_child_stage_identity_sha256=child.identity_sha256,
                parent_stage_identity_sha256=parent.identity_sha256,
                parent_stage_ref=fixture.parent_receipt)['child_stage_identity_sha256'],
                child.identity_sha256)
            mutated = dict(witness)
            mutated['child_stage_identity_sha256'] = 'f' * 64
            with self.assertRaises(mod.Supervisor24Error):
                mod._validate_child_stage_witness(
                    mutated, stage=child, process=process,
                    expected_child_stage_identity_sha256=child.identity_sha256,
                    parent_stage_identity_sha256=parent.identity_sha256,
                    parent_stage_ref=fixture.parent_receipt)
        finally:
            fixture.tearDown()

    def test_phase_identity_near_misses_fail_closed(self):
        mutations = {
            'group_id': 'other-group',
            'pid': FakeChild.pid + 1,
            'birth_identity': 'foreign-birth',
            'stage_identity_sha256': 'f' * 64,
            'source_commit': 'x' * 40,
            'contract_sha256': 'd' * 64,
        }
        for field, bad in mutations.items():
            with self.subTest(field=field):
                phase = 'reports/attempt-03/analyzer-finished.json'
                child = FakeChild(self.clock, phase_at=1300.0, exit_at=2000.0, exit_code=0,
                                  root=self.tmp, phase_path=phase, process=self.process)
                child._write_phase()
                target = self.tmp / phase
                value = json.loads(target.read_text())
                value[field] = bad
                target.write_bytes(mod.canonical_json(value))
                with self.assertRaises(mod.Supervisor24Error):
                    mod._wait_group_child(child, self.validated, 'bifrost-smoke', popen_monotonic=0.0,
                        root=self.tmp, attempt_id='bifrost-smoke-attempt-03-series-02',
                        phase_receipt_path=phase, timeout_evidence_path='reports/attempt-03/coordinator-timeout.json',
                        process=self.process, stage=ParentStage(), protocol=Protocol(),
                terminal_receipt_path='reports/releases/v0.9.2/attempts/bifrost-smoke-attempt-03-series-02/completed.json',
                parent_stage_ref=PARENT_REF, parent_process=PARENT_PROCESS)
                target.unlink()
                (self.tmp / mod._child_stage_witness_path(phase)).unlink()

    def test_actual_executor_call_site_gets_phase_before_recorder_finalization(self):
        source = REPO_ROOT / 'scripts/execute-release-v092.py'
        tree = ast.parse(source.read_text(), filename=str(source))
        run_group = next(node for node in ast.walk(tree)
                         if isinstance(node, ast.FunctionDef) and node.name == 'run_group')
        self.assertTrue(any(isinstance(node, ast.Call) and
                            isinstance(node.func, ast.Name) and node.func.id == '_run_process'
                            for node in ast.walk(run_group)))
        class RecorderExecutor:
            def __init__(self):
                self.events = []
            def _run_process(self):
                self.events.append(('process-return', self.phase.exists()))
                return (0, False, 616.0, None)
            def run_group(self):
                result = self._run_process()
                self.events.append(('recorder-start', self.phase.exists()))
                self.phase.write_text('recorder-finalization')
                return result
        executor = RecorderExecutor()
        executor.phase = self.tmp / 'reports/attempt-03/analyzer-finished.json'
        executor.phase.parent.mkdir(parents=True, exist_ok=True)
        with mod._scoped_analyzer_phase_hook(
                executor, root=self.tmp, phase_receipt_path='reports/attempt-03/analyzer-finished.json',
                protocol=Protocol(), group_id='bifrost-smoke',
                attempt_id='bifrost-smoke-attempt-03-series-02', process=self.process,
                stage=ChildStage(), graph_sha256=Graph.graph_sha256,
                parent_stage_identity_sha256=ParentStage.identity_sha256,
                parent_graph_sha256=Graph.graph_sha256,
                parent_stage_ref=PARENT_REF, child_stage_witness=child_witness(),
                child_stage_witness_ref=child_ready_ref(
                    self.tmp, 'reports/attempt-03/analyzer-finished.json'),
                source_commit=Stage.identity.source_commit, plan_commit=Stage.identity.plan_commit,
                contract_sha256=Stage.identity.contract_sha256, registered=706):
            result = executor.run_group()
        self.assertEqual(result[0], 0)
        self.assertEqual(executor.events, [('process-return', False), ('recorder-start', True)])
        self.assertFalse(hasattr(executor._run_process, '__wrapped__'))

    def test_actual_frozen_run_group_body_sees_child_phase_before_recorder(self):
        """Exercise the real frozen run_group body with only IO/process seams."""
        root = self.tmp / 'actual-run-group'
        root.mkdir()
        group = {'id': 'bifrost-smoke', 'tool': 'bifrost', 'deadline_seconds': 706,
                 'maximum_attempts': 3, 'argv': ['never-execute'], 'output_roots': [],
                 'case_ids': []}
        validated = {
            'repo_root': root, 'bytes_sha256': 'c' * 64, 'fixture_revision': 'synthetic',
            'source_inputs': [], 'tools': {'bifrost': {}}, 'total_wall_budget_seconds': 1e20,
            'groups': [{'id': group['id'], 'reports': [], 'identity_components': []}],
            'plan': {'execution_authorized': True, 'groups': [group],
                     'source_commit': 's' * 40, 'runner_source_sha256': 'r' * 64,
                     'population': {'path': 'population.json', 'sha256': 'x' * 64},
                     'tools': {}, 'execution_series': 2,
                     'resource_reservation': {'exclusive_analyzer_slot': True,
                                              'expires_at_unix_seconds': 1e12},
                     'resource_budget': {'minimum_launch_free_gib': 127,
                                         'proposed_total_retention_ceiling_gib': 24,
                                         'scratch_gib': 24}}}
        events = []
        attempt, execution, cache, ledger = (root / x for x in ('attempt', 'execution', 'cache', 'ledger'))
        original = executor._run_process
        def materialize(*args, **kwargs): execution.mkdir(exist_ok=True)
        def process(*args, **kwargs):
            events.append(('process-return', (root / 'phase.json').exists()))
            attempt.mkdir(exist_ok=True); (attempt / 'stdout.txt').write_bytes(b''); (attempt / 'stderr.txt').write_bytes(b'')
            return (0, False, 616.0, None)
        def capture(*args, **kwargs):
            self.assertTrue((root / 'phase.json').exists())
            events.append(('recorder', True))
        patches = {
            '_exclusive_lock': contextlib.nullcontext,
            '_require_group_qualification': lambda *a: {},
            '_assert_contract_snapshot': lambda *a: 'p' * 40,
            '_matrix_elapsed_wall': lambda *a: 0,
            '_assert_source_snapshot': lambda *a: None,
            '_source_file': lambda *a: None, '_check_tool_file': lambda *a: None,
            '_check_resources': lambda *a: None,
            '_assert_fresh': lambda *a: (attempt, execution, cache, ledger, 'attempt-03'),
            '_child_environment': lambda *a: {'HOME': str(execution / 'home'), 'TMPDIR': str(execution / 'tmp')},
            '_materialize_source': materialize, '_matrix_capacity_paths': lambda *a: ([], []),
            '_run_process': process, '_capacity_loss': capture,
        }
        child = ChildStage()
        with mock.patch.multiple(executor, **patches):
            with mod._scoped_analyzer_phase_hook(
                    executor, root=root, phase_receipt_path='phase.json', protocol=Protocol(),
                    group_id=group['id'], attempt_id='bifrost-smoke-attempt-03-series-02',
                    process=self.process, stage=child, graph_sha256=Graph.graph_sha256,
                    parent_stage_identity_sha256=ParentStage.identity_sha256,
                    parent_graph_sha256=Graph.graph_sha256,
                    parent_stage_ref=PARENT_REF, child_stage_witness=child_witness(),
                    child_stage_witness_ref=child_ready_ref(root, 'phase.json'),
                    source_commit=Stage.identity.source_commit,
                    plan_commit=Stage.identity.plan_commit,
                    contract_sha256=Stage.identity.contract_sha256, registered=706):
                row = executor.run_group(validated, group['id'])
        self.assertEqual(row['status'], 'completed')
        self.assertEqual(events, [('process-return', False), ('recorder', True)])
        self.assertIs(executor._run_process, original)

    def test_owned_group_signal_refuses_replaced_birth(self):
        calls=[]
        old_birth = mod._birth
        old_killpg = mod.os.killpg
        try:
            mod._birth = lambda pid: 'foreign-birth'
            mod.os.killpg = lambda pid, sig: calls.append((pid, sig))
            child = FakeChild(self.clock, phase_at=None, exit_at=1000, exit_code=0,
                              root=self.tmp, phase_path='none', process=self.process)
            with self.assertRaises(mod.Supervisor24Error):
                mod._signal_owned_group(child, self.process, 15)
            self.assertEqual(calls, [])
        finally:
            mod._birth, mod.os.killpg = old_birth, old_killpg

    def test_bounded_reap_never_waits_unbounded_after_kill(self):
        calls = []
        class HungChild:
            pid = FakeChild.pid
            def poll(self): return None
            def wait(self, timeout):
                calls.append(('wait', timeout))
                raise subprocess.TimeoutExpired(self.pid, timeout)
        old_birth, old_killpg = mod._birth, mod.os.killpg
        try:
            mod._birth = lambda pid: self.process['birth_identity']
            mod.os.killpg = lambda pid, sig: calls.append(('signal', sig))
            result = mod._bounded_reap_owned_group(HungChild(), self.process,
                                                   term_seconds=0.25, kill_seconds=0.5)
        finally:
            mod._birth, mod.os.killpg = old_birth, old_killpg
        self.assertEqual(result['status'], 'containment-failed')
        self.assertEqual(calls, [('signal', mod.signal.SIGTERM), ('wait', 0.25),
                                 ('signal', mod.signal.SIGKILL), ('wait', 0.5)])

    def test_owned_detached_descendant_remains_explicitly_unknown(self):
        descendant = None
        leader = None
        script = (
            "import subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'], "
            "start_new_session=True); print(p.pid, flush=True); time.sleep(30)"
        )
        try:
            leader = subprocess.Popen([sys.executable, '-c', script],
                                     start_new_session=True, stdout=subprocess.PIPE,
                                     text=True)
            assert leader.stdout is not None
            descendant = int(leader.stdout.readline().strip())
            process = {'pid': leader.pid, 'birth_identity': 'owned-leader-birth'}
            old_birth = mod._birth
            mod._birth = lambda pid: 'owned-leader-birth'
            try:
                result = mod._bounded_reap_owned_group(leader, process,
                                                       term_seconds=1.0, kill_seconds=1.0)
            finally:
                mod._birth = old_birth
            self.assertEqual(result['status'], 'reaped')
            self.assertTrue(result['coordinator_reaped'])
            self.assertEqual(result['descendant_containment'], 'unknown')
            os.kill(descendant, 0)
        finally:
            for pid in (descendant, leader.pid if leader is not None else None):
                if pid is None:
                    continue
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
            if leader is not None:
                try:
                    leader.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    leader.kill(); leader.wait(timeout=1)
            if descendant is not None:
                for _ in range(20):
                    try:
                        os.kill(descendant, 0)
                    except OSError:
                        break
                    time.sleep(0.01)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TimingTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)
