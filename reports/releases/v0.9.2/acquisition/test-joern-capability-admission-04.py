#!/usr/bin/env python3
"""Preflight namespace regression; never materializes or launches an analyzer."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('admission04', Path(__file__).with_name('joern-capability-admission-04.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class AdmissionPathTests(unittest.TestCase):
    def test_final_and_unregistered_paths_fail_before_loading_source(self):
        for path in [m.BASE + 'continuation-manifest-03.json', '../outside.json']:
            with self.subTest(path=path), patch.object(sys, 'argv', ['admission04',
                '--manifest', path, '--manifest-sha256', '0'*64, '--module-sha256', '0'*64]), \
                patch.object(m, 'sha') as digest, patch.object(m.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'exact reviewed provisional'):
                    m.main()
                digest.assert_not_called()
                run.assert_not_called()

    def test_exact_provisional_reaches_source_digest_gate(self):
        with patch.object(sys, 'argv', ['admission04', '--manifest', m.PROVISIONAL_MANIFEST,
            '--manifest-sha256', '0'*64, '--module-sha256', '0'*64]), \
            patch.object(m, 'sha', return_value='wrong') as digest, \
            patch.object(m.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'module changed'):
                m.main()
            digest.assert_called_once()
            run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
