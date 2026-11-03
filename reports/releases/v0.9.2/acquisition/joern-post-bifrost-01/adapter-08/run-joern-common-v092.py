#!/usr/bin/env python3
"""Pinned adapter08 entrypoint for the reviewed Joern observer08 source."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any


OBSERVER_PATH = (
    "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py"
)
OBSERVER_SHA256 = "5d39a7931cdaa690566b7587142ed9abd2b44ffaf38d51a403028653a40e85b1"
MAX_OBSERVER_BYTES = 1024 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read_observer(root: Path) -> tuple[Path, bytes]:
    relative = Path(OBSERVER_PATH)
    _require(not relative.is_absolute() and ".." not in relative.parts,
             "observer source path is not repository relative")
    path = root / relative
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        _require(not cursor.is_symlink(), "observer source ancestry contains a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_OBSERVER_BYTES,
                 "observer source is not a bounded regular file")
        chunks = []
        remaining = MAX_OBSERVER_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    raw = b"".join(chunks)
    _require(len(raw) <= MAX_OBSERVER_BYTES and len(raw) == before.st_size and
             (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "observer source changed during bounded read")
    _require(hashlib.sha256(raw).hexdigest() == OBSERVER_SHA256,
             "observer source differs from its reviewed digest")
    return path, raw


def load_observer() -> ModuleType:
    """Execute only the exact observer08 bytes and return its module."""
    wrapper = Path(__file__).resolve()
    root = wrapper.parents[6]
    _require(wrapper.name == "run-joern-common-v092.py" and
             wrapper.parent.name == "adapter-08",
             "wrapper is outside its reviewed adapter08 location")
    path, raw = _read_observer(root)
    module = ModuleType("_dfb_joern_native_startup_observer_08_pinned")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    _require(callable(getattr(module, "main", None)),
             "pinned observer08 has no callable CLI entrypoint")
    return module


def main(argv: list[str] | None = None) -> int:
    """Pass the CLI argument vector through without rewriting its elements."""
    forwarded = sys.argv[1:] if argv is None else argv
    _require(type(forwarded) is list and all(type(item) is str for item in forwarded),
             "observer CLI arguments must be an exact string list")
    return load_observer().main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
