#!/usr/bin/env python3
"""Hermetic tests for the append-only CodeQL terminal-history adapter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).with_name("codeql-terminal-history-04.py")
SPEC = importlib.util.spec_from_file_location("codeql_terminal_history_04_tested", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def canonical_row(index: int) -> bytes:
    return (json.dumps({"index": index}, sort_keys=True, separators=(",", ":")) + "\n").encode()


class CodeQLTerminalHistory04Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        sealed = b"".join(canonical_row(index) for index in range(88))
        tail = canonical_row(88)
        self.raw88 = sealed
        self.raw89 = sealed + tail
        sealed_path = self.root / MODULE.SEALED_PREFIX_PATH
        ledger_path = self.root / MODULE.LEDGER_PATH
        sealed_path.parent.mkdir(parents=True)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        sealed_path.write_bytes(sealed)
        ledger_path.write_bytes(self.raw89 + b"x" * (MODULE.NESTED_LEDGER_MAX_BYTES + 1))
        self.sealed_sha = MODULE.SEALED_PREFIX_SHA256
        self.constants = mock.patch.multiple(
            MODULE,
            SEALED_PREFIX_SHA256=MODULE._sha(sealed),
            NESTED_LEDGER_MAX_BYTES=4096,
            TERMINAL_PREFIX_MAX_BYTES=4096,
        )
        self.constants.start()

    def tearDown(self) -> None:
        self.constants.stop()
        self.temp.cleanup()

    def test_verified_prefix_reads_only_the_exact_89_row_head_of_a_large_live_ledger(self):
        with mock.patch.object(MODULE, "NESTED_LEDGER_MAX_BYTES", 64 * 1024 * 1024), \
                mock.patch.object(MODULE, "TERMINAL_PREFIX_MAX_BYTES", 256 * 1024 * 1024):
            self.assertEqual(MODULE._verified_89_prefix(self.root, self.raw89), self.raw88)

    def test_tampered_prefix_is_rejected_before_nested_import(self):
        bad = self.raw89.replace(b'"index":17', b'"index":70', 1)
        with self.assertRaisesRegex(MODULE.CodeQLTerminalHistoryError, "exact sealed"):
            MODULE._verified_89_prefix(self.root, bad)

    def test_oversize_terminal_prefix_is_rejected_fail_closed(self):
        with self.assertRaisesRegex(MODULE.CodeQLTerminalHistoryError, "exceeds"):
            MODULE._verified_89_prefix(self.root, self.raw89 + b"z" * 4096)

    def test_symlinked_live_ledger_is_rejected(self):
        ledger = self.root / MODULE.LEDGER_PATH
        ledger.unlink()
        ledger.symlink_to(self.root / "elsewhere")
        with self.assertRaisesRegex(MODULE.CodeQLTerminalHistoryError, "symlink"):
            MODULE._verified_89_prefix(self.root, self.raw89)

    def _fake_nested_module(self) -> Path:
        path = self.root / "fake-scoped-recovery.py"
        path.write_text(
            "from pathlib import PurePosixPath\n"
            f"LEDGER_PATH = PurePosixPath({MODULE.NESTED_LEDGER_PATH!r})\n"
            "def _regular_bytes(root, relative, description, *args, **kwargs):\n"
            "    return (root / relative).read_bytes()\n"
            "def validate_packet(root, reference):\n"
            "    return _regular_bytes(root, LEDGER_PATH.as_posix(), 'current execution ledger')\n",
            encoding="utf-8",
        )
        return path

    def test_nested_reader_receives_exact_88_rows_and_restores_reader(self):
        fake = self._fake_nested_module()
        original_factory = importlib.util.module_from_spec
        with MODULE._scoped_nested_ledger(self.root, self.raw88):
            spec = importlib.util.spec_from_file_location(MODULE.NESTED_MODULE_NAME, fake)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            self.assertEqual(module.validate_packet(self.root, {}), self.raw88)
            self.assertIsNotNone(module._regular_bytes)
        self.assertIs(importlib.util.module_from_spec, original_factory)

    def test_nested_reader_restores_module_function_after_validation_exception(self):
        fake = self.root / "fake-scoped-recovery-failing.py"
        fake.write_text(
            "from pathlib import PurePosixPath\n"
            f"LEDGER_PATH = PurePosixPath({MODULE.NESTED_LEDGER_PATH!r})\n"
            "def _regular_bytes(root, relative, description, *args, **kwargs):\n"
            "    return b'original'\n"
            "def validate_packet(root, reference):\n"
            "    _regular_bytes(root, LEDGER_PATH.as_posix(), 'current execution ledger')\n"
            "    raise RuntimeError('fixture failure')\n",
            encoding="utf-8",
        )
        original_factory = importlib.util.module_from_spec
        with MODULE._scoped_nested_ledger(self.root, self.raw88):
            spec = importlib.util.spec_from_file_location(MODULE.NESTED_MODULE_NAME, fake)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            original_reader = module._regular_bytes
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                module.validate_packet(self.root, {})
            self.assertIs(module._regular_bytes, original_reader)
        self.assertIs(importlib.util.module_from_spec, original_factory)

    def test_recovery_delegates_exact_89_bytes_and_does_not_rewrite_tail(self):
        predecessor = types.SimpleNamespace(
            recover_bifrost_history=mock.Mock(return_value={"contexts": {}})
        )
        with mock.patch.object(MODULE, "load_predecessor", return_value=predecessor):
            result = MODULE.recover_bifrost_history(
                self.root, "manifest.json", "m" * 64, self.raw89
            )
        self.assertEqual(result, {"contexts": {}})
        predecessor.recover_bifrost_history.assert_called_once_with(
            self.root.resolve(), "manifest.json", "m" * 64, self.raw89
        )

    def test_recovery_does_not_accept_substituted_live_prefix(self):
        ledger = self.root / MODULE.LEDGER_PATH
        ledger.write_bytes(self.raw89.replace(b'"index":21', b'"index":91', 1))
        predecessor = types.SimpleNamespace(recover_bifrost_history=mock.Mock())
        with mock.patch.object(MODULE, "load_predecessor", return_value=predecessor):
            with self.assertRaises(MODULE.CodeQLTerminalHistoryError):
                MODULE.recover_bifrost_history(self.root, "manifest.json", "m" * 64, self.raw89)
        predecessor.recover_bifrost_history.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
