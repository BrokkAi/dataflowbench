#!/usr/bin/env python3
"""The observed non-Cargo exporter denies a release slot."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(path))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


OLD=load('historical_gate_tests','test-run-release-group-v090.py')
NEW=load('recovery_gate','run-release-group-recovery-v090.py')
OBSERVED='39259 /Users/dave/.codex/worktrees/fbf7/bifrost-dev/target/coverage-tools/python/bin/python scripts/test-cost/workspace-branch-export.py /Users/dave/.codex/worktrees/fbf7/bifrost-dev/target/workspace-coverage/run-003'


class RecoveryGateTests(OLD.LaunchTests):
    def gate(self, **kwargs):
        with patch.object(OLD,'launch',NEW):
            return super().gate(**kwargs)

    def test_observed_python_exporter_blocks_without_cargo(self):
        with self.assertRaisesRegex(NEW.AttemptError,'contending'):
            self.gate(processes=OBSERVED)

    def test_unrelated_python_does_not_block(self):
        self.gate(processes='9 /usr/bin/python3 scripts/ordinary.py')

    def test_script_mentioned_as_prose_is_not_exporter(self):
        self.assertEqual(NEW.coverage_exporter_processes('9 /usr/bin/echo scripts/test-cost/workspace-branch-export.py'),[])


if __name__=='__main__':unittest.main()
