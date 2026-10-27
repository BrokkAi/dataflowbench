"""Bounded source-only contention-monitor repair tests; no engine/JVM launch."""
import importlib.util
import json
import os
from pathlib import Path
import types
import unittest
from unittest import mock

import native_qualifier as n


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContentionRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor_source = load_path(
            n.ROOT / 'scripts/execute-release-v092.py',
            'contention_repair_frozen_executor',
        )
        cls.controller_source = load_path(
            n.ROOT / 'reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py',
            'contention_repair_frozen_controller',
        )
        cls.process_source = load_path(
            n.ROOT / 'scripts/swift_v2_process.py',
            'contention_repair_process',
        )

    def probe(self, command_table, native_table, tracked=None, *, events=None):
        tracked = {} if tracked is None else dict(tracked)
        events = [] if events is None else events
        executor = types.SimpleNamespace(
            _process_table=lambda: (events.append('command') or command_table),
            _contenders=self.executor_source._contenders,
        )
        controller = types.SimpleNamespace(
            _hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders,
        )
        proc = types.SimpleNamespace(
            process_table=lambda: (events.append('native') or native_table),
            descendants=lambda table, current: (
                events.append('descendants') or self.process_source.descendants(table, current)
            ),
        )
        return n._contention_snapshot(executor, controller, proc, tracked)

    def test_command_first_native_after_and_exact_owned_descendants_are_retained(self):
        events = []
        native = {
            100: (1, 'root-birth', 'S'),
            101: (100, 'child-birth', 'S'),
            102: (101, 'grandchild-birth', 'S'),
        }
        result = self.probe(
            '101 95.0 joern /usr/bin/joern --scan\n102 95.0 joern /usr/bin/joern --scan',
            native,
            {100: 'root-birth'},
            events=events,
        )
        self.assertEqual(events, ['command', 'native', 'descendants'])
        self.assertEqual(result['contenders'], [])
        self.assertEqual(result['tracked_after'], {
            100: 'root-birth', 101: 'child-birth', 102: 'grandchild-birth',
        })
        self.assertEqual([row['pid'] for row in result['proven_owned_rows']], [101, 102])

    def test_frozen_classifiers_still_reject_foreign_heavy_and_hashed_rows(self):
        rows = '\n'.join((
            '201 80.0 joern /usr/bin/joern --scan',
            '202 80.0 bifrost /tmp/bifrost-abcdef --scan',
        ))
        native = {
            100: (1, 'root-birth', 'S'),
            201: (999, 'foreign-joern', 'S'),
            202: (999, 'foreign-bifrost', 'S'),
        }
        result = self.probe(rows, native, {100: 'root-birth'})
        self.assertEqual(result['contenders'], rows.splitlines())
        self.assertEqual([row['pid'] for row in result['rejected_command_rows']], [201, 202])

    def test_wrong_birth_same_argv_reparented_and_recycled_parent_fail_closed(self):
        cases = {
            'wrong-birth': (
                '301 80.0 joern /usr/bin/joern --scan',
                {100: (1, 'root-birth', 'S'), 301: (100, 'wrong-birth', 'S')},
                {100: 'root-birth', 301: 'expected-birth'},
                301,
            ),
            'same-argv': (
                '302 80.0 joern /usr/bin/joern --scan',
                {100: (1, 'root-birth', 'S'), 302: (999, 'foreign-birth', 'S')},
                {100: 'root-birth'},
                302,
            ),
            'recycled-parent': (
                '303 80.0 joern /usr/bin/joern --scan',
                {100: (1, 'recycled-root', 'S'), 303: (100, 'child-birth', 'S')},
                {100: 'root-birth'},
                303,
            ),
            'reparented': (
                '304 80.0 joern /usr/bin/joern --scan',
                {100: (1, 'root-birth', 'S'), 304: (999, 'child-birth', 'S')},
                {100: 'root-birth'},
                304,
            ),
        }
        for name, (row, native, tracked, pid) in cases.items():
            with self.subTest(name=name):
                result = self.probe(row, native, tracked)
                self.assertEqual(result['contenders'], [row])
                self.assertEqual([item['pid'] for item in result['rejected_command_rows']], [pid])
                self.assertNotIn(pid, [item['pid'] for item in result['proven_owned_rows']])

    def test_missing_native_or_disappeared_child_remains_rejected(self):
        row = '305 80.0 joern /usr/bin/joern --scan'
        result = self.probe(row, {100: (1, 'root-birth', 'S')}, {100: 'root-birth'})
        self.assertEqual(result['contenders'], [row])
        self.assertIsNone(result['rejected_command_rows'][0]['native'])

    def test_native_process_table_failure_is_propagated_without_empty_exemption(self):
        calls = []
        executor = types.SimpleNamespace(
            _process_table=lambda: (calls.append('command') or '305 80.0 joern /usr/bin/joern --scan'),
            _contenders=self.executor_source._contenders,
        )
        controller = types.SimpleNamespace(
            _hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders,
        )
        failure = OSError('native process table unavailable')
        proc = types.SimpleNamespace(process_table=lambda: (_ for _ in ()).throw(failure))
        with self.assertRaises(OSError) as caught:
            n.contenders(executor, controller, proc, {100: 'root-birth'})
        self.assertIs(caught.exception, failure)
        self.assertEqual(calls, ['command'])

    def fake_supervise(self, command_table, native_tables, *, write_receipt=True, fail_receipt=False):
        read_fd, write_fd = os.pipe()
        lock_path = Path(self._testMethodName + '-lock')
        lock_path.write_bytes(b'')
        lock_fd = os.open(lock_path, os.O_RDONLY)
        frames = [
            {'token': 'token', 'pid': 500, 'birth_identity': 'root-birth',
             'phase': phase, 'observed_monotonic': 0.0}
            for phase in ('ready', 'controls-started', 'controls-returned')
        ]
        for frame in frames:
            os.write(write_fd, n.canonical(frame))
        class Child:
            pid = 500
            def __init__(self):
                self.calls = 0
            def poll(self):
                self.calls += 1
                return None if self.calls == 1 and write_receipt else 0
        child = Child()
        controller = types.SimpleNamespace(
            _process=lambda pid: {'pid': pid, 'birth_identity': 'root-birth'},
            _bounded_reap_unidentified_child=lambda value: {'coordinator_reaped': True},
            _hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders,
        )
        states = iter(native_tables)
        command_calls = iter(command_table)
        executor = types.SimpleNamespace(
            _process_table=lambda: next(command_calls),
            _contenders=self.executor_source._contenders,
        )
        proc = types.SimpleNamespace(
            start_identity=lambda pid, fallback: 'root-birth',
            process_table=lambda: next(states),
            descendants=self.process_source.descendants,
            active=lambda table, tracked: [],
        )
        original_immutable = n.immutable
        def immutable(path, value):
            if fail_receipt and path.name == 'contention-stop.json':
                raise OSError('diagnostic path unavailable')
            return original_immutable(path, value)
        namespace = Path(self._testMethodName + '-namespace')
        namespace.mkdir(exist_ok=True)
        try:
            with mock.patch.object(n, 'immutable', side_effect=immutable), \
                 mock.patch.object(n.time, 'sleep', return_value=None):
                result = n.supervise(
                    ['fixture-only'], root=namespace, env={}, stdout=None, stderr=None,
                    lock_fd=lock_fd, request_sha='a' * 64, controller=controller,
                    proc=proc, resources=types.SimpleNamespace(sample=lambda **kw: None),
                    executor=executor, namespace=namespace, token='token', read_fd=read_fd,
                    write_fd=write_fd, popen=lambda *args, **kwargs: child,
                    clock=lambda: 0.0,
                )
            receipt = ((namespace / 'contention-stop.json').read_bytes()
                       if (namespace / 'contention-stop.json').exists() else None)
            return result, receipt
        finally:
            os.close(lock_fd)
            if namespace.exists():
                for path in namespace.iterdir():
                    path.unlink()
                namespace.rmdir()
            lock_path.unlink(missing_ok=True)

    def test_supervise_merges_owned_child_for_later_cleanup(self):
        native = {
            500: (1, 'root-birth', 'S'),
            501: (500, 'child-birth', 'S'),
        }
        result, _ = self.fake_supervise(
            ['501 80.0 /usr/bin/joern --scan', ''],
            [native, native, {}],
            write_receipt=True,
        )
        self.assertIsNone(result['failure'], result)
        self.assertEqual(
            {item['pid'] for item in result['tracked_processes']},
            {500, 501},
        )
        self.assertTrue(result['cleanup']['coordinator_reaped'])

    def test_supervise_writes_rejected_rows_before_failure(self):
        result, receipt_bytes = self.fake_supervise(
            ['601 80.0 joern /usr/bin/joern --scan'],
            [{500: (1, 'root-birth', 'S'), 601: (999, 'foreign-birth', 'S')}, {}],
            write_receipt=False,
        )
        self.assertEqual(result['failure']['message'], 'foreign analyzer/heavy contender')
        self.assertIsNotNone(receipt_bytes)
        receipt = json.loads(receipt_bytes)
        self.assertEqual(receipt['status'], 'contention-stop')
        self.assertEqual(receipt['actual_rejected_command_rows'][0]['pid'], 601)
        self.assertEqual(receipt['actual_rejected_command_rows'][0]['native']['ppid'], 999)
        self.assertEqual(receipt['actual_rejected_command_rows'][0]['native']['birth_identity'], 'foreign-birth')
        self.assertEqual(receipt['proven_owned_rows'], [])
        self.assertFalse(receipt['automatic_retry'])

    def test_supervise_preserves_contention_failure_if_receipt_write_fails(self):
        result, _ = self.fake_supervise(
            ['602 80.0 joern /usr/bin/joern --scan'],
            [{500: (1, 'root-birth', 'S'), 602: (999, 'foreign-birth', 'S')}, {}],
            write_receipt=False,
            fail_receipt=True,
        )
        self.assertEqual(result['failure']['type'], 'ValueError')
        self.assertEqual(result['failure']['message'], 'foreign analyzer/heavy contender')


if __name__ == '__main__':
    unittest.main()
