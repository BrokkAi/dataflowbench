#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from swift_v2_process import run, descendants, active, ProcessCleanupError


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
                self.assertEqual(result['cleanup_status'], 'verified-stopped')
                self.assertTrue(any(s['pid'] == pid and s['signal'] == 'SIGKILL' for s in result['cleanup_signaled']))
                self.assertLess(result['elapsed_seconds'], 3)
                self.assertIsNone(unrelated.poll())
                status = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
                self.assertTrue(not status or status.startswith('Z'))
                self.assertTrue((root / 'held').exists())
            finally:
                unrelated.terminate(); unrelated.wait(timeout=3)
        self.assertFalse(root.exists())

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

    def test_success_keeps_exit_and_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run([sys.executable, '-c', 'print(42)'], root, 'success', 2)
            self.assertEqual(result['exit_status'], 0)
            self.assertFalse(result['timed_out'])
            self.assertEqual(result['cleanup_status'], 'verified-stopped')
            self.assertEqual((root / 'success.stdout').read_text().strip(), '42')


if __name__ == '__main__': unittest.main()
