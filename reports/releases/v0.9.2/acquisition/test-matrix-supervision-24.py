#!/usr/bin/env python3
"""No-analyzer regression tests for durable control24 stop behavior."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import os
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('control24', Path(__file__).with_name('matrix-supervision-24.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ControlTests(unittest.TestCase):
    def setup_control(self, root):
        state = root / 'state'
        public = root / 'public'
        state.mkdir()
        public.mkdir()
        (state / 'allow-supervisor-start').write_text('test-only')
        return state, public

    def exercise(self, codes):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state, public = self.setup_control(root)
            calls = []
            def popen(argv, **kwargs):
                calls.append(argv)
                code = codes[len(calls) - 1]
                return SimpleNamespace(pid=12345, wait=lambda: code)
            args = SimpleNamespace(manifest_sha256='test-manifest', module_sha256='module',
                                   supervisor_sha256='supervisor', review_sha256='review')
            m.write(public / 'parent-preflight.json', {'exit_code': 0,
                    'automatic_retry': False,
                    'manifest_sha256': args.manifest_sha256, 'argv': m.command(args, 'preflight')})
            (state / 'allow-supervisor-start').unlink()
            m.write(state / 'allow-supervisor-start', {'pid': os.getpid(), 'birth': 'test-birth',
                    'token': 'test-token', 'argv_sha256': m.hashlib.sha256(m.json.dumps(
                        [str(Path(m.__file__).resolve()), *sys.argv[1:]]).encode()).hexdigest()})
            m.write(public / 'launcher.json', {'supervisor_pid': os.getpid(),
                    'supervisor_token': 'test-token', 'automatic_retry': False,
                    'supervisor_birth': 'test-birth', 'manifest_sha256': args.manifest_sha256,
                    'module_sha256': args.module_sha256, 'supervisor_sha256': args.supervisor_sha256,
                    'review_sha256': args.review_sha256,
                    'preflight_sha256': m.sha(public / 'parent-preflight.json')})
            with patch.multiple(m, STATE=state, PUBLIC=public, ROOT=root), \
                    patch.object(m, 'validate'), patch.object(m, 'birth', return_value='test-birth'), \
                    patch.object(m.subprocess, 'Popen', side_effect=popen):
                if codes[0]:
                    with self.assertRaisesRegex(ValueError, 'stopped after joern'):
                        m.supervise(args)
                    self.assertEqual(len(calls), 1)
                    self.assertTrue((public / 'supervisor-error.json').is_file())
                    self.assertFalse((public / 'codeql-swift-common108-dispatch.json').exists())
                else:
                    m.supervise(args)
                    self.assertEqual(len(calls), 2)
                    self.assertTrue((public / 'exit.json').is_file())
                self.assertTrue((public / 'joern-swift-common108-dispatch.json').is_file())
                self.assertTrue((public / 'joern-swift-common108-exit.json').is_file())

    def test_first_failure_stops_without_codeql(self):
        self.exercise([1])

    def test_success_dispatches_exactly_once_each(self):
        self.exercise([0, 0])

    def test_consumed_namespace_never_relaunches(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state, public = self.setup_control(root)
            with patch.multiple(m, STATE=state, PUBLIC=public), patch.object(m, 'validate'), \
                    patch.object(m.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'namespace already consumed'):
                    m.launch(SimpleNamespace())
                run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
