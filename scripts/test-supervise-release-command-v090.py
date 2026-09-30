#!/usr/bin/env python3
"""Focused subprocess coverage for the durable release command supervisor."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
import subprocess

SPEC = importlib.util.spec_from_file_location(
    'supervise_release_command', Path(__file__).with_name('supervise-release-command-v090.py'))
supervisor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supervisor)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix='.release-supervisor-test-',
            dir=Path(__file__).resolve().parent.parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_python(self, log_name, code, timeout=5):
        return supervisor.supervise(
            self.root / log_name, timeout, [sys.executable, '-c', code])

    def test_success_persists_started_logs_and_terminal_receipt(self):
        logs = self.root / 'success'
        result = supervisor.supervise(
            logs, 5, [sys.executable, '-c',
                      "import sys; print('out'); print('err', file=sys.stderr)"])

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['exit_code'], 0)
        started = json.loads((logs / 'started.json').read_text())
        self.assertEqual(started['status'], 'started')
        self.assertEqual(started['argv'][0], sys.executable)
        self.assertIsInstance(started['command_pid'], int)
        self.assertEqual((logs / 'stdout.log').read_text(), 'out\n')
        self.assertEqual((logs / 'stderr.log').read_text(), 'err\n')
        self.assertEqual(json.loads((logs / 'terminal.json').read_text()), result)

    def test_failure_persists_nonzero_exit_code_and_output(self):
        logs = self.root / 'failure'
        result = supervisor.supervise(
            logs, 5, [sys.executable, '-c',
                      "import sys; print('failed', file=sys.stderr); sys.exit(7)"])

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['exit_code'], 7)
        self.assertIn('failed', (logs / 'stderr.log').read_text())
        self.assertEqual(json.loads((logs / 'terminal.json').read_text())['exit_code'], 7)

    def test_timeout_terminates_command_and_persists_terminal_status(self):
        logs = self.root / 'timeout'
        before = time.monotonic()
        result = self.run_python('timeout', 'import time; time.sleep(30)', timeout=0.15)

        self.assertLess(time.monotonic() - before, 5)
        self.assertEqual(result['status'], 'timed_out')
        self.assertEqual(result['exit_code'], 124)
        self.assertEqual(json.loads((logs / 'terminal.json').read_text()), result)

    def test_supervisor_signal_terminates_child_and_persists_interrupted_status(self):
        logs = self.root / 'interrupted'
        script = Path(__file__).with_name('supervise-release-command-v090.py')
        supervisor_process = subprocess.Popen(
            [sys.executable, str(script), '--log-dir', str(logs),
             '--timeout-seconds', '10', '--', sys.executable, '-c',
             'import time; time.sleep(30)'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: supervisor_process.poll() is None and supervisor_process.kill())

        deadline = time.monotonic() + 5
        started_path = logs / 'started.json'
        while time.monotonic() < deadline:
            if started_path.exists() and json.loads(started_path.read_text()).get('command_pid'):
                break
            if supervisor_process.poll() is not None:
                self.fail('supervisor exited before starting its command')
            time.sleep(0.02)
        else:
            self.fail('command pid was not persisted')

        os.kill(supervisor_process.pid, signal.SIGTERM)
        supervisor_process.communicate(timeout=5)
        result = json.loads((logs / 'terminal.json').read_text())
        self.assertEqual(result['status'], 'interrupted')
        self.assertEqual(result['signal'], signal.SIGTERM)
        self.assertEqual(supervisor_process.returncode, 128 + signal.SIGTERM)

    def test_rejects_temporary_log_roots_before_creating_anything(self):
        suffix = self.tmp.name.rsplit('-', 1)[-1]
        for root in (Path('/tmp'), Path('/private/tmp')):
            candidate = root / f'release-supervisor-{suffix}'
            with self.subTest(root=root):
                with self.assertRaisesRegex(supervisor.SupervisorError, 'outside'):
                    supervisor.supervise(candidate, 1, [sys.executable, '-c', 'pass'])
                self.assertFalse(candidate.exists())

    def test_rejects_existing_log_directory(self):
        existing = self.root / 'already-there'
        existing.mkdir()
        with self.assertRaisesRegex(supervisor.SupervisorError, 'already exists'):
            supervisor.supervise(existing, 1, [sys.executable, '-c', 'pass'])
        self.assertEqual(list(existing.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
