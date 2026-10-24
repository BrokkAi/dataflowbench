#!/usr/bin/env python3
"""Scoped CodeQL terminal-history adapter for the failed 03 boundary.

The predecessor provider (``independent-pending-codeql-03.py``) already owns
all CodeQL manifest, ledger, frozen-checker, and terminal-row semantics.  The
only repair here is the nested ``v092_scoped_recovery`` reader: its historical
packet reader has a 64 MiB read bound, while the mutable live ledger can be
larger.  During predecessor validation this adapter supplies that reader with
the already verified 88-row prefix, and only that reader.  The predecessor
still receives the caller's exact 89-row prefix and performs all terminal
checks itself.

This module has no CLI and does not launch, replay, admit, write, or mutate
production evidence.  ``recover_bifrost_history`` is the sole integration
entry point for a later independently reviewed caller.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[4]
PREDECESSOR_SOURCE = (
    "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py"
)
# This is the exact source currently reviewed by the CodeQL03 proof.  The
# source is checked before import and again after import; no caller-selected
# predecessor is accepted.
PREDECESSOR_SHA256 = "f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8"
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
SEALED_PREFIX_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "sealed-ledger-prefix-88.jsonl"
)
SEALED_PREFIX_SHA256 = "9ae98c51570149cc7ebe86573df518b4f469188e23dd58d7bcdc37ac93532476"
SEALED_ROWS = 88
TERMINAL_PREFIX_ROWS = 89
NESTED_MODULE_NAME = "v092_scoped_recovery_packet"
NESTED_LEDGER_PATH = LEDGER_PATH
NESTED_LEDGER_MAX_BYTES = 64 * 1024 * 1024
# The live 89-row prefix is currently about 114 MiB; this outer bound is only
# a memory-safety sanity limit and is independent of the nested 64 MiB reader.
TERMINAL_PREFIX_MAX_BYTES = 256 * 1024 * 1024
SHA256 = 64


class CodeQLTerminalHistoryError(ValueError):
    """A CodeQL history input or scoped reader failed closed validation."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise CodeQLTerminalHistoryError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _relative(value: object, description: str) -> PurePosixPath:
    _require(isinstance(value, str) and value and "\\" not in value,
             f"{description} is not a safe relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and all(part not in {"", ".", ".."}
                                             for part in path.parts),
             f"{description} is not a safe relative path")
    return path


def _safe_path(root: Path, relative: str, description: str) -> Path:
    path = root
    for part in _relative(relative, description).parts:
        path = path / part
        _require(not path.is_symlink(), f"symlink in {description}: {relative}")
    return path


def _regular_bytes(root: Path, relative: str, description: str,
                   *, maximum: int | None = None) -> bytes:
    path = _safe_path(root, relative, description)
    _require(path.is_file(), f"{description} is not a regular file: {relative}")
    try:
        info = path.stat()
        if maximum is not None:
            _require(info.st_size <= maximum,
                     f"{description} exceeds its bounded read limit")
        return path.read_bytes()
    except OSError as exc:
        raise CodeQLTerminalHistoryError(f"cannot read {description}: {relative}") from exc


def _prefix_bytes(root: Path, relative: str, length: int, description: str) -> bytes:
    """Read only a bounded prefix from a potentially much larger live file."""
    path = _safe_path(root, relative, description)
    _require(path.is_file(), f"{description} is not a regular file: {relative}")
    try:
        size = path.stat().st_size
        _require(size >= length, f"{description} is shorter than the supplied prefix")
        with path.open("rb") as stream:
            raw = stream.read(length)
    except OSError as exc:
        raise CodeQLTerminalHistoryError(f"cannot read {description}: {relative}") from exc
    _require(len(raw) == length, f"{description} prefix was truncated")
    return raw


def _canonical_json_lines(raw: bytes, description: str) -> list[bytes]:
    lines = raw.splitlines(keepends=True)
    _require(all(line.endswith(b"\n") and not line.endswith(b"\r\n") for line in lines),
             f"{description} contains a non-canonical line ending")
    for index, line in enumerate(lines, 1):
        try:
            value = json.loads(line[:-1])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CodeQLTerminalHistoryError(
                f"{description} line {index} is not JSON"
            ) from exc
        _require(isinstance(value, dict), f"{description} line {index} is not an object")
        canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        _require(canonical == line, f"{description} line {index} is not canonical JSON")
    return lines


def _verified_89_prefix(root: Path, raw: bytes) -> bytes:
    """Validate the exact live 89-row prefix and return its immutable 88-row part."""
    _require(isinstance(raw, bytes), "CodeQL terminal prefix must be raw bytes")
    _require(len(raw) <= TERMINAL_PREFIX_MAX_BYTES,
             "CodeQL terminal prefix exceeds its bounded input limit")
    sealed = _regular_bytes(root, SEALED_PREFIX_PATH, "sealed 88-row ledger prefix",
                            maximum=NESTED_LEDGER_MAX_BYTES)
    _require(_sha(sealed) == SEALED_PREFIX_SHA256 and
             len(_canonical_json_lines(sealed, "sealed ledger prefix")) == SEALED_ROWS,
             "sealed 88-row ledger prefix binding changed")
    lines = _canonical_json_lines(raw, "CodeQL terminal ledger prefix")
    _require(len(lines) == TERMINAL_PREFIX_ROWS,
             "CodeQL terminal provider requires exactly the 89-row prefix")
    historical = b"".join(lines[:SEALED_ROWS])
    _require(historical == sealed,
             "CodeQL terminal prefix does not begin with the exact sealed 88 rows")
    # Check the live file without reading its potentially over-64-MiB tail.
    live_head = _prefix_bytes(root, LEDGER_PATH, len(raw), "live execution ledger")
    _require(live_head == raw,
             "supplied CodeQL terminal prefix is not the exact live-ledger prefix")
    return historical


@contextlib.contextmanager
def _scoped_nested_ledger(root: Path, historical_raw: bytes) -> Iterator[None]:
    """Patch only the nested packet's current-ledger reader, restoring always.

    The import hook is deliberately name- and API-bound.  Other modules and
    all other reads continue through their original loaders/readers.  The
    scoped packet receives the exact sealed 88-row bytes; the outer frozen
    executor and predecessor continue to receive the caller's 89-row bytes.
    """
    _require(len(_canonical_json_lines(historical_raw, "scoped historical ledger")) == SEALED_ROWS,
             "scoped nested ledger must contain exactly 88 rows")
    _require(_sha(historical_raw) == SEALED_PREFIX_SHA256,
             "scoped nested ledger is not the sealed 88-row prefix")
    original_factory = importlib.util.module_from_spec

    class _NestedLoader:
        def __init__(self, loader: Any) -> None:
            self._loader = loader

        def create_module(self, spec: Any) -> Any:
            creator = getattr(self._loader, "create_module", None)
            return creator(spec) if creator is not None else None

        def exec_module(self, module: Any) -> None:
            self._loader.exec_module(module)
            original_regular = getattr(module, "_regular_bytes", None)
            original_validate = getattr(module, "validate_packet", None)
            module_ledger = getattr(getattr(module, "LEDGER_PATH", None), "as_posix",
                                    lambda: "")()
            _require(module_ledger == NESTED_LEDGER_PATH,
                     "nested scoped-recovery module binds an unexpected ledger path")
            _require(callable(original_regular) and callable(original_validate),
                     "nested scoped-recovery reader API changed")

            def scoped_regular(repository: Any, relative: Any, description: str,
                              *args: Any, **kwargs: Any) -> bytes:
                if (relative == NESTED_LEDGER_PATH and
                        description == "current execution ledger"):
                    _require(len(historical_raw) <= NESTED_LEDGER_MAX_BYTES,
                             "scoped historical ledger exceeds nested reader bound")
                    return historical_raw
                return original_regular(repository, relative, description, *args, **kwargs)

            def scoped_validate(*args: Any, **kwargs: Any) -> Any:
                module._regular_bytes = scoped_regular
                try:
                    return original_validate(*args, **kwargs)
                finally:
                    module._regular_bytes = original_regular

            module.validate_packet = scoped_validate

    def factory(spec: Any) -> Any:
        if getattr(spec, "name", None) == NESTED_MODULE_NAME:
            loader = getattr(spec, "loader", None)
            _require(loader is not None and callable(getattr(loader, "exec_module", None)),
                     "nested scoped-recovery loader changed")
            spec.loader = _NestedLoader(loader)
        return original_factory(spec)

    importlib.util.module_from_spec = factory
    try:
        yield
    finally:
        importlib.util.module_from_spec = original_factory


def load_predecessor(root: Path = ROOT) -> Any:
    """Load the exact 03 provider after a pre- and post-import byte check."""
    path = _safe_path(root, PREDECESSOR_SOURCE, "CodeQL03 predecessor")
    raw = path.read_bytes()
    _require(_sha(raw) == PREDECESSOR_SHA256,
             "CodeQL03 predecessor source changed before import")
    spec = importlib.util.spec_from_file_location("codeql_terminal_history_03", path)
    _require(spec is not None and spec.loader is not None,
             "cannot load CodeQL03 predecessor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _require(_sha(path.read_bytes()) == PREDECESSOR_SHA256,
             "CodeQL03 predecessor source changed during import")
    _require(callable(getattr(module, "recover_bifrost_history", None)),
             "CodeQL03 predecessor lacks recover_bifrost_history")
    return module


def recover_bifrost_history(root: Path, manifest_path: str,
                            manifest_sha256: str, prefix_raw: bytes) -> dict[str, Any]:
    """Delegate exact 89-row recovery while scoping only the nested 88 reader."""
    root = Path(root).resolve()
    historical_raw = _verified_89_prefix(root, prefix_raw)
    predecessor = load_predecessor(root)
    with _scoped_nested_ledger(root, historical_raw):
        result = predecessor.recover_bifrost_history(
            root, manifest_path, manifest_sha256, prefix_raw
        )
    _require(isinstance(result, dict), "CodeQL03 predecessor returned a non-object recovery")
    return result


__all__ = [
    "CodeQLTerminalHistoryError",
    "PREDECESSOR_SOURCE",
    "PREDECESSOR_SHA256",
    "recover_bifrost_history",
    "load_predecessor",
    "_verified_89_prefix",
    "_scoped_nested_ledger",
]
