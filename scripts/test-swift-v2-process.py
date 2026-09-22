#!/usr/bin/env python3
import json
import importlib.util
import os
import signal
import time
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from swift_v2_process import run, descendants, active, ProcessCleanupError, start_identity


class ProcessTests(unittest.TestCase):
    def test_detached_descendant_holding_scratch_stops_before_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); f=open(" + repr(str(root / 'held')) + ",'w'); f.write('held'); f.flush(); time.sleep(30)"
            parent = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c'," + repr(child) + "],start_new_session=True); print(p.pid,flush=True); time.sleep(30)"
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'], start_new_session=True)
            try:
                result = run([sys.executable, '-c', parent], root, 'detached', 0.5)
                pid = int((root / 'detached.stdout').read_text())
                self.assertTrue(result['timed_out'])
                self.assertEqual(result['cleanup_status'], 'tracked-processes-stopped')
                self.assertFalse(result['discovery_complete'])
                self.assertFalse(result['scratch_cleanup_authorized'])
                self.assertTrue(any(s['pid'] == pid and s['signal'] == 'SIGKILL' for s in result['cleanup_signaled']))
                self.assertLess(result['elapsed_seconds'], 3)
                self.assertIsNone(unrelated.poll())
                status = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
                self.assertTrue(not status or status.startswith('Z'))
                self.assertTrue((root / 'held').exists())
            finally:
                unrelated.terminate(); unrelated.wait(timeout=3)
        self.assertFalse(root.exists())

    def test_fast_exit_double_fork_never_claims_containment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pidfile = root / 'detached-pid'
            code = "import os,time; child=os.fork();\nif child: os._exit(0)\nos.setsid(); child=os.fork();\nif child: os._exit(0)\nf=open(" + repr(str(pidfile)) + ", 'w'); f.write(str(os.getpid())); f.flush(); time.sleep(10)"
            try:
                try: record = run([sys.executable, '-c', code], root, 'fast', 1)
                except ProcessCleanupError: record = json.loads((root / 'fast.command.json').read_text())
                self.assertFalse(record['discovery_complete'])
                self.assertFalse(record['scratch_cleanup_authorized'])
                self.assertEqual(record['descendant_containment'], 'unproven')
            finally:
                for _ in range(20):
                    if pidfile.exists() and pidfile.read_text(): break
                    time.sleep(0.05)
                if pidfile.exists() and pidfile.read_text():
                    pid = int(pidfile.read_text())
                    birth = start_identity(pid, '')
                    if birth is not None and start_identity(pid, '') == birth:
                        try: os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError: pass

    def test_missing_root_identity_is_explicit_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); process = MagicMock(pid=10)
            process.poll.return_value = 0; process.wait.return_value = 0
            with patch('swift_v2_process.subprocess.Popen', return_value=process), patch('swift_v2_process.process_table', return_value={}):
                with self.assertRaises(ProcessCleanupError): run(['never-executed'], root, 'missing-root', 1)
            record = json.loads((root / 'missing-root.command.json').read_text())
            self.assertIn('root start identity was never captured', record['cleanup_error'])

    def test_recycled_parent_cannot_authorize_signals_or_descendants(self):
        table = {10: (1, 'new-start', 'S'), 20: (10, 'child-start', 'S')}
        tracked = descendants(table, {10: 'old-start'})
        self.assertNotIn(20, tracked)
        self.assertEqual(active(table, tracked), [])

    def test_uncertain_cleanup_is_explicit_failure_with_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            process = MagicMock(pid=10)
            process.poll.return_value = 0
            with patch('swift_v2_process.subprocess.Popen', return_value=process), patch('swift_v2_process.process_table', side_effect=RuntimeError('ps unavailable')):
                with self.assertRaises(ProcessCleanupError):
                    run(['fixture-not-executed'], root, 'uncertain', 1)
            record = json.loads((root / 'uncertain.command.json').read_text())
            self.assertEqual(record['cleanup_status'], 'uncertain')
            self.assertIn('ps unavailable', record['cleanup_error'])

    def test_finalized_database_progress_is_separate_from_containment(self):
        spec = importlib.util.spec_from_file_location('v2_probe', Path(__file__).with_name('probe-swift-v2-codeql.py'))
        probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as temporary:
            db = Path(temporary); (db / 'db-swift').mkdir()
            record = {'exit_status': 0, 'timed_out': False, 'cleanup_status': 'tracked-processes-stopped', 'discovery_complete': False, 'scratch_cleanup_authorized': False}
            metadata = '---\nfinalised: true\n'
            resolved = {'languages': ['swift'], 'datasetFolder': str(db / 'db-swift')}
            self.assertTrue(probe.database_ready(record, metadata, resolved, db))
            for field, value in [('exit_status', 1), ('timed_out', True), ('cleanup_status', 'uncertain')]:
                changed = dict(record); changed[field] = value
                self.assertFalse(probe.database_ready(changed, metadata, resolved, db))
            self.assertFalse(probe.database_ready(record, 'finalised: false\n', resolved, db))
            self.assertFalse(probe.database_ready(record, metadata + 'inProgress:\n', resolved, db))
            self.assertFalse(probe.database_ready(record, metadata, {'languages': ['swift'], 'datasetFolder': '/unrelated'}, db))

    def test_success_keeps_exit_and_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run([sys.executable, '-c', 'import time;print(42);time.sleep(0.2)'], root, 'success', 2)
            self.assertEqual(result['exit_status'], 0)
            self.assertFalse(result['timed_out'])
            self.assertEqual(result['cleanup_status'], 'tracked-processes-stopped')
            self.assertFalse(result['scratch_cleanup_authorized'])
            self.assertEqual((root / 'success.stdout').read_text().strip(), '42')


if __name__ == '__main__': unittest.main()
