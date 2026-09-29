#!/usr/bin/env python3
"""Control launch must pass both identity validation and the shared host gate."""
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('control_launch', Path(__file__).with_name('run-release-control-v090.py'))
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)


class LaunchTests(unittest.TestCase):
    def test_validation_only_never_runs_control(self):
        fake = types.ModuleType('release_control_attempt_v090')
        fake.validate_control = Mock(return_value={})
        fake.run_control = Mock()
        with tempfile.TemporaryDirectory() as tmp, patch.dict('sys.modules', {fake.__name__: fake}):
            self.assertEqual(launch.launch_control(tmp, 'contract.json', 'one'),
                             {'mode': 'validation-only', 'control_id': 'one'})
            fake.run_control.assert_not_called()
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_failed_validation_never_opens_host_lock(self):
        fake = types.ModuleType('release_control_attempt_v090')
        fake.validate_control = Mock(side_effect=ValueError('unreviewed identity'))
        fake.run_control = Mock()
        with tempfile.TemporaryDirectory() as tmp, patch.dict('sys.modules', {fake.__name__: fake}), patch.object(launch.os, 'open') as opened:
            with self.assertRaisesRegex(ValueError, 'unreviewed'):
                launch.launch_control(tmp, 'contract.json', 'one', execute=True)
            opened.assert_not_called()
            fake.run_control.assert_not_called()


if __name__ == '__main__':
    unittest.main()
