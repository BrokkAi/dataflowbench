#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name('probe-swift-v2-codeql.py')
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location('probe_swift_v2_codeql', SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProbeArgumentTests(unittest.TestCase):
    def test_overrides_must_be_complete(self):
        with self.assertRaisesRegex(ValueError, 'require --compiler, --sdk, and --target'):
            MODULE.validate_toolchain_overrides(Path('/tmp/swiftc'), None, 'arm64-test', Path('/tmp/control'))

    def test_overrides_are_limited_to_non_scored_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = root / 'swiftc'
            compiler.write_bytes(b'compiler')
            compiler.chmod(0o755)
            sdk = root / 'MacOSX.sdk'
            sdk.mkdir()
            with self.assertRaisesRegex(ValueError, 'non-scored scope'):
                MODULE.validate_toolchain_overrides(compiler, sdk, 'arm64-test', None)

            self.assertEqual(
                MODULE.validate_toolchain_overrides(compiler, sdk, 'arm64-test', root / 'control'),
                (str(compiler), str(sdk), 'arm64-test'))

    def test_compiler_must_be_absolute_executable_and_sdk_must_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = root / 'swiftc'
            compiler.write_bytes(b'compiler')
            compiler.chmod(0o755)
            with self.assertRaisesRegex(ValueError, 'absolute executable'):
                MODULE.validate_toolchain_overrides(Path('swiftc'), root, 'arm64-test', root)
            with self.assertRaisesRegex(ValueError, 'absolute existing directory'):
                MODULE.validate_toolchain_overrides(compiler, root / 'missing.sdk', 'arm64-test', root)
            sdk_file = root / 'not-a-directory'
            sdk_file.write_text('not an SDK directory')
            with self.assertRaisesRegex(ValueError, 'absolute existing directory'):
                MODULE.validate_toolchain_overrides(compiler, sdk_file, 'arm64-test', root)

    def test_default_tuple_does_not_require_explicit_overrides(self):
        self.assertIsNone(MODULE.validate_toolchain_overrides(None, None, None, None))


class CompileArgvTests(unittest.TestCase):
    def test_compile_argv_preserves_explicit_toolchain_and_source_order(self):
        argv = MODULE.build_compile_argv(
            '/tmp/toolchain/swiftc', '/tmp/sdk', 'arm64-apple-macosx26.5',
            Path('/tmp/cache'), [Path('/tmp/source/helper.swift'), Path('/tmp/source/main.swift')],
            Path('/tmp/never-executed'))
        self.assertEqual(argv, [
            '/tmp/toolchain/swiftc', '-swift-version', '6', '-Onone', '-sdk', '/tmp/sdk',
            '-target', 'arm64-apple-macosx26.5', '-module-name', 'DataFlowBenchTaintSwift',
            '-module-cache-path', '/tmp/cache', '/tmp/source/helper.swift',
            '/tmp/source/main.swift', '-o', '/tmp/never-executed'])

    def test_default_target_remains_current_target(self):
        self.assertEqual(MODULE.DEFAULT_TARGET, 'arm64-apple-macosx27.0.0')

    def test_compiler_version_ready_requires_success_and_identity(self):
        self.assertTrue(MODULE.compiler_version_ready({'exit_status': 0, 'timed_out': False, 'stdout': 'Swift 6.3.3'}))
        for record in [
            {'exit_status': 1, 'timed_out': False, 'stdout': 'Swift 6.3.3'},
            {'exit_status': 0, 'timed_out': True, 'stdout': 'Swift 6.3.3'},
            {'exit_status': 0, 'timed_out': False, 'stdout': ''},
        ]:
            with self.subTest(record=record):
                self.assertFalse(MODULE.compiler_version_ready(record))

    def test_bounded_output_decodes_timeout_bytes(self):
        self.assertEqual(MODULE._bounded_output(b'Swift 6.3.3\n'), 'Swift 6.3.3\n')


class PhaseBudgetTests(unittest.TestCase):
    def test_extraction_extension_does_not_extend_analysis(self):
        with mock.patch.object(MODULE.commands, 'run', return_value={}) as run:
            MODULE.run_extraction(['codeql', 'database', 'create'], Path('/tmp/out'))
            self.assertEqual(run.call_args.args[3], 150)
            MODULE.run_analysis_query(['codeql', 'query', 'run'], Path('/tmp/out'), 'flow')
            self.assertEqual(run.call_args.args[3], 60)
        self.assertEqual(MODULE.ANALYSIS_MEMORY_MB, 512)
        self.assertFalse(MODULE.EXTRACTION_POLICY['extraction_memory_is_analysis_budget'])

    def test_approved_default_and_150_pass_parser_but_151_needs_override(self):
        class Parsed(Exception):
            pass
        base = ['probe', '--output', '/unused', '--codeql', '/unused',
                '--packs', '/unused', '--case-id', 'not-executed']
        for extra in ([], ['--extraction-timeout', '150']):
            with mock.patch.object(sys, 'argv', base + extra), mock.patch.object(
                    MODULE, 'resolve_toolchain', side_effect=Parsed):
                with self.assertRaises(Parsed):
                    MODULE.main()
        with mock.patch.object(sys, 'argv', base + ['--extraction-timeout', '151']), mock.patch(
                'sys.stderr'), mock.patch.object(MODULE, 'resolve_toolchain') as resolve:
            with self.assertRaises(SystemExit) as failure:
                MODULE.main()
            self.assertEqual(failure.exception.code, 2)
            resolve.assert_not_called()

    def test_explicit_diagnostic_deadline_cannot_leak_into_analysis(self):
        with mock.patch.object(MODULE.commands, 'run', return_value={}) as run:
            MODULE.run_extraction(['extract'], Path('/tmp/out'), 180)
            self.assertEqual(run.call_args.args[3], 180)
            MODULE.run_analysis_query(['query'], Path('/tmp/out'), 'flow')
            self.assertEqual(run.call_args.args[3], 60)


if __name__ == '__main__':
    unittest.main()
