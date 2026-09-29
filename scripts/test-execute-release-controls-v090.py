#!/usr/bin/env python3
"""The control orchestrator cannot silently reset attempts or drift membership."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('controls', Path(__file__).with_name('execute-release-controls-v090.py'))
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)


class ControlTests(unittest.TestCase):
    def test_requires_immutable_commit(self):
        with self.assertRaisesRegex(ValueError, 'exact reviewed'):
            controls.reviewed_inventory(Path('.'), 'main', 'contract.json')

    def test_tampered_inventory_rejected(self):
        contract = {'control_inventory': {'path': 'inventory.json', 'sha256': '0'*64}}
        with patch.object(controls.subprocess, 'check_output', side_effect=[json.dumps(contract).encode(), b'{}']):
            with self.assertRaisesRegex(ValueError, 'differs'):
                controls.reviewed_inventory(Path('.'), 'a'*40, 'contract.json')

    def test_unauthorized_execution_never_prepares_root(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(controls, 'reviewed_inventory', return_value=({'execution_authorized': False}, [])), patch.object(controls.subprocess, 'run') as run, patch('sys.argv', ['controls', '--source', tmp, '--plan-commit', 'a'*40, '--execute']):
            with self.assertRaisesRegex(ValueError, 'final executable-plan'):
                controls.main()
            run.assert_not_called()

    def test_existing_root_never_restarted(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = {'execution_authorized': True, 'unresolved': [], 'control_execution_roots': {'one': tmp}}
            with patch.object(controls, 'reviewed_inventory', return_value=(contract, [{'id': 'one'}])), patch.object(controls.subprocess, 'run') as run, patch('sys.argv', ['controls', '--source', tmp, '--plan-commit', 'a'*40, '--execute']):
                with self.assertRaisesRegex(ValueError, 'resume review'):
                    controls.main()
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
