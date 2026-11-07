#!/usr/bin/env python3
"""Restore the one pinned historical Scala report needed by the CI unit test.

This restores a Bifrost 0.14.0 attempt JSON byte-for-byte. It is test-fixture
hydration only: it does not establish Bifrost v0.14.4 completion, and Scala
0.7.0 remains missing.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys


MANIFEST_RELATIVE = PurePosixPath(
    "evidence-delivery/v0.9.2-bifrost-v0144-01/ci-baseline-scala-0140/manifest.json"
)
MANIFEST_SHA256 = "b6b3456863d6605a55304dbf264c85bb6a91ec7a58f31027a54077fdfff0b063"
MANIFEST_BYTES = 889
DESTINATION_RELATIVE = PurePosixPath(
    "reports/releases/v0.9.2/normal/attempts/"
    "bifrost-scala-kernel-attempt-02-series-02/bifrost-scala-kernel.json"
)
PART_RELATIVE = PurePosixPath(
    "detail/bifrost-scala-kernel.json.gz.part00001"
)
SOURCE_BYTES = 56575
SOURCE_SHA256 = "5f6350db340428b4d0c1865f312d6457077eb967a99ac3b966e6335fc09c8c46"
PART_BYTES = 3301
PART_SHA256 = "a5ebd939a572d7fda939390429204f57c47477cac227e677db9faadf8cdf4ebe"
SCHEMA = "dataflowbench-v092-bifrost-scala-ci-baseline/v1"
PURPOSE = (
    "CI unit-test hydration of one exact historical Bifrost 0.14.0 Scala attempt JSON. "
    "This is not Bifrost v0.14.4 completion evidence; Scala 0.7.0 remains missing."
)
DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _open_real_root(path: Path) -> int:
    info = path.lstat()
    _require(stat.S_ISDIR(info.st_mode), "--root must be a real directory, not a symlink")
    return os.open(path.resolve(strict=True), DIRECTORY_FLAGS)


def _open_dirs(root_fd: int, components: tuple[str, ...], *, create: bool = False) -> int:
    fd = os.dup(root_fd)
    try:
        for component in components:
            _require(component not in ("", ".", "..") and "/" not in component and "\\" not in component,
                     "unsafe path component")
            if create:
                try:
                    os.mkdir(component, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            next_fd = os.open(component, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_regular_at(root_fd: int, relative: PurePosixPath, expected_bytes: int) -> bytes:
    parent_fd = _open_dirs(root_fd, relative.parts[:-1])
    try:
        fd = os.open(relative.name, os.O_RDONLY | NOFOLLOW, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    try:
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode), f"{relative} must be a regular file")
        _require(before.st_size == expected_bytes, f"{relative} size mismatch")
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(fd, min(65536, expected_bytes + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            _require(total <= expected_bytes, f"{relative} exceeds its pinned size")
        after = os.fstat(fd)
        _require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                 (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                 f"{relative} changed while being read")
        _require(total == expected_bytes, f"{relative} size changed while being read")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _expected_manifest() -> dict:
    return {
        "schema": SCHEMA,
        "purpose": PURPOSE,
        "historical_source": {
            "path": DESTINATION_RELATIVE.as_posix(),
            "bytes": SOURCE_BYTES,
            "sha256": SOURCE_SHA256,
        },
        "restore": {"path": DESTINATION_RELATIVE.as_posix()},
        "compressed_part": {
            "path": PART_RELATIVE.as_posix(),
            "bytes": PART_BYTES,
            "sha256": PART_SHA256,
            "compression": "gzip, one deterministic lossless stream",
        },
    }


def _load_pinned_payload() -> bytes:
    repository_root = Path(__file__).resolve().parent.parent
    repository_fd = _open_real_root(repository_root)
    try:
        manifest_bytes = _read_regular_at(repository_fd, MANIFEST_RELATIVE, MANIFEST_BYTES)
        _require(hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256,
                 "manifest digest mismatch")
        manifest = json.loads(manifest_bytes)
        _require(manifest == _expected_manifest(),
                 "manifest fields do not match fixed expectations")

        part_relative = MANIFEST_RELATIVE.parent / PART_RELATIVE
        compressed = _read_regular_at(repository_fd, part_relative, PART_BYTES)
        _require(hashlib.sha256(compressed).hexdigest() == PART_SHA256,
                 "compressed part digest mismatch")
    finally:
        os.close(repository_fd)

    with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as zipped:
        payload = zipped.read(SOURCE_BYTES + 1)
        _require(len(payload) == SOURCE_BYTES, "decompressed payload size mismatch")
        _require(zipped.read(1) == b"", "decompressed payload exceeds its pinned size")
    _require(hashlib.sha256(payload).hexdigest() == SOURCE_SHA256,
             "decompressed payload digest mismatch")
    return payload


def _existing_payload(parent_fd: int, name: str) -> bytes | None:
    try:
        fd = os.open(name, os.O_RDONLY | NOFOLLOW, dir_fd=parent_fd)
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode), "existing destination is not a regular file")
        _require(info.st_size == SOURCE_BYTES,
                 "refusing to replace different existing destination bytes")
        data = bytearray()
        while True:
            block = os.read(fd, SOURCE_BYTES + 1 - len(data))
            if not block:
                break
            data.extend(block)
            _require(len(data) <= SOURCE_BYTES,
                     "refusing to replace different existing destination bytes")
        existing = bytes(data)
        _require(hashlib.sha256(existing).hexdigest() == SOURCE_SHA256,
                 "refusing to replace different existing destination bytes")
        _require(existing == _load_pinned_payload(),
                 "existing destination differs from the pinned payload")
        return existing
    finally:
        os.close(fd)


def restore(root: Path) -> dict:
    payload = _load_pinned_payload()
    root_fd = _open_real_root(Path(root))
    parent_fd = -1
    temp_name: str | None = None
    temp_fd = -1
    try:
        parent_fd = _open_dirs(root_fd, DESTINATION_RELATIVE.parts[:-1], create=True)
        existing = _existing_payload(parent_fd, DESTINATION_RELATIVE.name)
        if existing is not None:
            return {
                "status": "already-present-identical",
                "path": DESTINATION_RELATIVE.as_posix(),
                "bytes": SOURCE_BYTES,
                "sha256": SOURCE_SHA256,
            }

        temp_name = f".bifrost-scala-ci-baseline-{os.getpid()}-{os.urandom(8).hex()}.tmp"
        temp_fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW,
                          0o600, dir_fd=parent_fd)
        view = memoryview(payload)
        while view:
            written = os.write(temp_fd, view)
            _require(written > 0, "short write while staging pinned payload")
            view = view[written:]
        os.fchmod(temp_fd, 0o644)
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = -1

        try:
            os.link(temp_name, DESTINATION_RELATIVE.name, src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd, follow_symlinks=False)
        except FileExistsError:
            existing = _existing_payload(parent_fd, DESTINATION_RELATIVE.name)
            _require(existing is not None,
                     "destination disappeared while restoring pinned payload")
            return {
                "status": "already-present-identical",
                "path": DESTINATION_RELATIVE.as_posix(),
                "bytes": SOURCE_BYTES,
                "sha256": SOURCE_SHA256,
            }
        os.fsync(parent_fd)
        return {
            "status": "restored",
            "path": DESTINATION_RELATIVE.as_posix(),
            "bytes": SOURCE_BYTES,
            "sha256": SOURCE_SHA256,
        }
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        if temp_name is not None and parent_fd >= 0:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        if parent_fd >= 0:
            os.close(parent_fd)
        os.close(root_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="existing checkout root")
    args = parser.parse_args(argv)
    try:
        result = restore(args.root)
    except (OSError, ValueError, EOFError, gzip.BadGzipFile, json.JSONDecodeError) as exc:
        print(f"restore failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
