#!/usr/bin/env python3
"""Launch gates reject stale ownership and resource identity before native work."""
import hashlib
import json
import importlib.util
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('launch', Path(__file__).with_name('run-release-group-v090.py'))
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        binary = self.root/'runner'
        binary.write_bytes(b'pinned runner')
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        inventory = self.root/'inventory.json'
        inventory.write_text('{}')
        self.contract = {'runtime_trees': [{'path': 'inventory.json', 'sha256': hashlib.sha256(inventory.read_bytes()).hexdigest()}], 'unresolved': [], 'harness_commit': 'a'*40,
                         'execution_roots': {'one': str(self.root)},
                         'tools': {'runner': {'path': str(binary), 'sha256': digest}},
                         'runner_build': {'source_commit': 'a'*40, 'binary_sha256': digest},
                         'resource_reservation': {'exclusive_analyzer_slot': True, 'expires_at_unix_seconds': time.time()+60, 'window_started_at_unix_seconds': time.time()-60},
                         'total_wall_budget_seconds': 102960,
                         'resource_budget': {'minimum_launch_free_gib': 100, 'proposed_total_retention_ceiling_gib': 24}}

    def gate(self, *, processes='', free=120*1024**3):
        def output(argv, **kwargs):
            return 'a'*40 if argv[0] == 'git' else processes
        with patch('release_runtime_inventory_v090.verify', return_value=True), patch.object(launch.subprocess, 'check_output', side_effect=output), patch.object(launch.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=free)):
            launch.launch_gate(self.root, self.contract, {'id': 'one', 'deadline_seconds': 600})

    def test_valid_gate(self):
        self.gate()

    def test_another_build_blocks(self):
        with self.assertRaisesRegex(launch.AttemptError, 'contending'):
            self.gate(processes='12 /toolchain/rustc\n')

    def test_capacity_blocks(self):
        with self.assertRaisesRegex(launch.AttemptError, 'capacity'):
            self.gate(free=99*1024**3)

    def test_expired_reservation_blocks(self):
        self.contract['resource_reservation']['expires_at_unix_seconds'] = 0
        with self.assertRaisesRegex(launch.AttemptError, 'fresh exclusive'):
            self.gate()

    def test_new_root_cannot_reset_attempts(self):
        self.contract['execution_roots']['one'] = str(self.root/'other')
        with self.assertRaisesRegex(launch.AttemptError, 'explicitly designated'):
            self.gate()

    def test_binary_drift_blocks(self):
        (self.root/'runner').write_bytes(b'changed')
        with self.assertRaisesRegex(launch.AttemptError, 'binary identity'):
            self.gate()


if __name__ == '__main__':
    unittest.main()
