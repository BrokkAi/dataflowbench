#!/usr/bin/env python3
"""Pinned fallback beats a stale system executable without losing dependencies."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from release_environment_v090 import semgrep_environment


class EnvironmentTests(unittest.TestCase):
    def test_pinned_fallback_wins_and_dependency_stays_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pinned = root / 'pinned'
            system = root / 'system'
            pinned.mkdir()
            system.mkdir()
            for path in [pinned/'semgrep', pinned/'pysemgrep', system/'pysemgrep', system/'javac']:
                path.write_text('#!/bin/sh\nexit 0\n')
                path.chmod(0o755)
            before = {'PATH': str(system), 'JAVA_HOME': '/exact/jdk'}
            env = semgrep_environment(pinned/'semgrep', before)
            self.assertEqual(shutil.which('pysemgrep', path=env['PATH']), str(pinned/'pysemgrep'))
            self.assertEqual(shutil.which('javac', path=env['PATH']), str(system/'javac'))
            self.assertEqual(env['JAVA_HOME'], '/exact/jdk')
            self.assertEqual(env['SEMGREP_ENABLE_VERSION_CHECK'], '0')
            self.assertEqual(before, {'PATH': str(system), 'JAVA_HOME': '/exact/jdk'})

    def test_missing_pinned_fallback_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp)/'semgrep'
            launcher.touch()
            with self.assertRaisesRegex(ValueError, 'lacks pysemgrep'):
                semgrep_environment(launcher, {})


if __name__ == '__main__':
    unittest.main()
