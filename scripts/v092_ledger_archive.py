#!/usr/bin/env python3
"""Pack and hydrate a lossless gzip archive of the v0.9.2 execution ledger.

The archive preserves the ledger's exact bytes. Its hashes establish integrity
only; they do not validate benchmark semantics or authorize execution.
"""

from __future__ import annotations

import argparse
import codecs
import ctypes
import errno
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import sys
import tempfile


LEDGER_RELATIVE = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
ARCHIVE_NAME = "ledger-v1.jsonl.gz"
MANIFEST_NAME = "manifest.json"
SCHEMA = "dataflowbench-v092-ledger-archive/v1"
CURRENT_INDEX_RELATIVE = PurePosixPath("reports/releases/v0.9.2/ledger-archive-index.json")
INDEX_SCHEMA = "dataflowbench-v092-ledger-index/v1"
ARCHIVES_RELATIVE = LEDGER_RELATIVE.parent / "ledger-archives"
BLOCK_BYTES = 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 4 * 1024 * 1024 * 1024
MAX_COMPRESSED_BYTES = MAX_UNCOMPRESSED_BYTES + 64 * 1024 * 1024
MAX_LINE_BYTES = 128 * 1024 * 1024
MAX_LINE_COUNT = 100_000
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_INDEX_BYTES = 64 * 1024
MAX_JSON_DEPTH = 128
MAX_JSON_TOKENS_PER_LINE = 10_000_000
MAX_JSON_KEY_BYTES = 1024 * 1024
TERMINAL_STATUSES = {"completed", "failed", "timed-out", "capacity-lost", "recorder-error"}
HISTORICAL_PREFIX_LINES = 57
HISTORICAL_PREFIX_BYTES = 16_086_045
HISTORICAL_PREFIX_SHA256 = "31ea08cf5f0fa04fe07697bb8d3683e2a313140e6e12e15fe7e7963a82cdc1f2"
HISTORICAL_PREFIX_GIT_BLOB_SHA1 = "aa299771be8ebce13c8e7473723aa37cdafac305"
_NUMBER = re.compile(rb"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ARCHIVE_ENTRY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
_STRING_SPECIAL = re.compile(rb'["\\\x00-\x1f]')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(BLOCK_BYTES)
            if not block:
                break
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _stamp(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, stat.S_IMODE(info.st_mode))


def _directory_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _open_root(root: Path) -> int:
    root = Path(root)
    info = root.lstat()
    require(stat.S_ISDIR(info.st_mode), "root must be a real directory")
    root = root.resolve(strict=True)
    return os.open(root, _directory_flags())


def _open_dir(root_fd: int, parts: tuple[str, ...]) -> int:
    fd = os.dup(root_fd)
    try:
        for part in parts:
            require(part not in ("", ".", "..") and "/" not in part and "\\" not in part,
                    "unsafe path component")
            next_fd = os.open(part, _directory_flags(), dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _safe_relative(value: str | Path) -> PurePosixPath:
    text = str(value)
    require(bool(text) and "\\" not in text and not text.startswith("/"), "unsafe relative path")
    path = PurePosixPath(text)
    require(path.parts and text == path.as_posix() and
            all(part not in ("", ".", "..") for part in path.parts), "unsafe relative path")
    require(not re.match(r"^[A-Za-z]:", text), "unsafe relative path")
    return path


def _open_file(root_fd: int, relative: PurePosixPath) -> tuple[int, tuple[int, ...]]:
    parent_fd = _open_dir(root_fd, relative.parts[:-1])
    try:
        fd = os.open(relative.name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                      getattr(os, "O_NONBLOCK", 0), dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        os.close(fd)
        raise ValueError(f"not a regular file: {relative}")
    return fd, _stamp(info)


def _validate_utf8_segment(data: bytes, start: int, end: int) -> None:
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    cursor = start
    while cursor < end:
        stop = min(cursor + 64 * 1024, end)
        decoder.decode(data[cursor:stop], final=False)
        cursor = stop
    decoder.decode(b"", final=True)


class _JsonRowParser:
    """Validate one JSON object without building its potentially huge value tree."""

    _TRACKED_ROOT_FIELDS = {"schema_version", "release", "status", "group_id", "attempt_id"}

    def __init__(self, data: bytes):
        self.data = data
        self.index = 0
        self.tokens = 0

    def _token(self) -> None:
        self.tokens += 1
        require(self.tokens <= MAX_JSON_TOKENS_PER_LINE, "ledger JSON row has too many values")

    def _ws(self) -> None:
        while self.index < len(self.data) and self.data[self.index] in b" \t\r\n":
            self.index += 1

    def _string(self, *, decode: bool) -> str | None:
        require(self.index < len(self.data) and self.data[self.index] == 0x22,
                "expected JSON string")
        start = self.index
        self.index += 1
        segment_start = self.index
        while True:
            special = _STRING_SPECIAL.search(self.data, self.index)
            require(special is not None, "unterminated JSON string")
            self.index = special.start()
            byte = self.data[self.index]
            if byte == 0x22:
                _validate_utf8_segment(self.data, segment_start, self.index)
                self.index += 1
                raw_length = self.index - start
                if decode:
                    require(raw_length <= MAX_JSON_KEY_BYTES,
                            "ledger JSON key or status string is too long")
                    return json.loads(self.data[start:self.index])
                return None
            if byte < 0x20:
                raise ValueError("unescaped control byte in JSON string")
            if byte == 0x5C:
                _validate_utf8_segment(self.data, segment_start, self.index)
                self.index += 1
                require(self.index < len(self.data), "truncated JSON escape")
                escape = self.data[self.index]
                if escape == ord("u"):
                    end = self.index + 5
                    require(end <= len(self.data) and
                            all(c in b"0123456789abcdefABCDEF" for c in self.data[self.index + 1:end]),
                            "invalid JSON unicode escape")
                    self.index = end
                else:
                    require(escape in b'"\\/bfnrt', "invalid JSON escape")
                    self.index += 1
                segment_start = self.index
                continue
            raise AssertionError("string terminator scanner returned an unexpected byte")

    def _number(self) -> tuple[str, int | None]:
        start = self.index
        while self.index < len(self.data) and self.data[self.index] not in b" \t\r\n,]}":
            self.index += 1
        token = self.data[start:self.index]
        require(bool(token) and len(token) <= 4096 and _NUMBER.fullmatch(token) is not None,
                "invalid JSON number")
        if b"." in token or b"e" in token.lower():
            try:
                require(math.isfinite(float(token)), "non-finite JSON number")
            except (OverflowError, ValueError) as exc:
                raise ValueError("invalid or non-finite JSON number") from exc
            return "number", None
        if len(token.lstrip(b"-")) <= 1000:
            return "integer", int(token)
        return "integer", None

    def _value(self, depth: int, *, capture_string: bool = False) -> tuple[str, object | None]:
        self._token()
        self._ws()
        require(depth <= MAX_JSON_DEPTH and self.index < len(self.data), "invalid or too-deep JSON row")
        byte = self.data[self.index]
        if byte == ord('"'):
            return "string", self._string(decode=capture_string)
        if byte == ord("{"):
            self._object(depth + 1, root=False)
            return "object", None
        if byte == ord("["):
            self._array(depth + 1)
            return "array", None
        for literal, kind, value in ((b"true", "boolean", True),
                                     (b"false", "boolean", False),
                                     (b"null", "null", None)):
            if self.data.startswith(literal, self.index):
                self.index += len(literal)
                return kind, value
        if byte == ord("-") or ord("0") <= byte <= ord("9"):
            return self._number()
        raise ValueError("invalid JSON value")

    def _array(self, depth: int) -> None:
        require(depth <= MAX_JSON_DEPTH, "ledger JSON row is too deeply nested")
        self.index += 1
        self._ws()
        count = 0
        if self.index < len(self.data) and self.data[self.index] == ord("]"):
            self.index += 1
            return
        while True:
            count += 1
            require(count <= MAX_JSON_TOKENS_PER_LINE, "ledger JSON array is too large")
            self._value(depth)
            self._ws()
            require(self.index < len(self.data), "unterminated JSON array")
            byte = self.data[self.index]
            self.index += 1
            if byte == ord("]"):
                return
            require(byte == ord(","), "invalid JSON array separator")
            self._ws()

    def _object(self, depth: int, *, root: bool) -> dict[str, tuple[str, object | None]] | None:
        require(depth <= MAX_JSON_DEPTH, "ledger JSON row is too deeply nested")
        self.index += 1
        self._ws()
        seen: set[str] = set()
        tracked: dict[str, tuple[str, object | None]] = {}
        count = 0
        if self.index < len(self.data) and self.data[self.index] == ord("}"):
            self.index += 1
            return tracked if root else None
        while True:
            count += 1
            require(count <= MAX_JSON_TOKENS_PER_LINE, "ledger JSON object is too large")
            key = self._string(decode=True)
            assert key is not None
            require(key not in seen, f"duplicate JSON object key: {key!r}")
            seen.add(key)
            self._ws()
            require(self.index < len(self.data) and self.data[self.index] == ord(":"),
                    "invalid JSON object separator")
            self.index += 1
            is_tracked = root and key in self._TRACKED_ROOT_FIELDS
            kind, value = self._value(depth, capture_string=is_tracked and key != "schema_version")
            if is_tracked:
                tracked[key] = (kind, value)
            self._ws()
            require(self.index < len(self.data), "unterminated JSON object")
            byte = self.data[self.index]
            self.index += 1
            if byte == ord("}"):
                return tracked if root else None
            require(byte == ord(","), "invalid JSON object separator")
            self._ws()

    def parse(self) -> dict[str, tuple[str, object | None]]:
        self._ws()
        require(self.index < len(self.data) and self.data[self.index] == ord("{"),
                "ledger JSON row must be an object")
        tracked = self._object(0, root=True)
        self._ws()
        require(self.index == len(self.data), "trailing data after ledger JSON object")
        assert tracked is not None
        return tracked


def _validate_line(line: bytes, line_number: int) -> str:
    require(len(line) <= MAX_LINE_BYTES, f"ledger line {line_number} exceeds size limit")
    require(line.endswith(b"\n") and line != b"\n" and not line.endswith(b"\r\n"),
            f"ledger line {line_number} is blank or not canonical newline-terminated JSON")
    row = _JsonRowParser(line[:-1]).parse()
    expected_types = {"schema_version": "integer", "release": "string", "status": "string",
                      "group_id": "string", "attempt_id": "string"}
    for field, expected in expected_types.items():
        require(field in row and row[field][0] == expected,
                f"ledger line {line_number} has invalid {field}")
    version = row["schema_version"][1]
    require(version == 1, f"ledger line {line_number} has an unsupported schema_version")
    require(row["release"][1] == "v0.9.2", f"ledger line {line_number} has the wrong release")
    require(isinstance(row["group_id"][1], str) and bool(row["group_id"][1]),
            f"ledger line {line_number} has an empty group_id")
    require(isinstance(row["attempt_id"][1], str) and bool(row["attempt_id"][1]),
            f"ledger line {line_number} has an empty attempt_id")
    status = row["status"][1]
    require(isinstance(status, str) and status in TERMINAL_STATUSES,
            f"ledger line {line_number} has an unknown or non-terminal status")
    return hashlib.sha256(line).hexdigest()


def _source_file(root_fd: int) -> tuple[int, tuple[int, ...]]:
    return _open_file(root_fd, LEDGER_RELATIVE)


def _check_stamp(fd: int, before: tuple[int, ...], message: str) -> None:
    require(_stamp(os.fstat(fd)) == before, message)


def _digest_fd(fd: int) -> tuple[str, int]:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    size = 0
    while True:
        block = os.read(fd, BLOCK_BYTES)
        if not block:
            break
        size += len(block)
        digest.update(block)
    return digest.hexdigest(), size


def _prefix_blob_hasher():
    blob = hashlib.sha1()
    blob.update(b"blob " + str(HISTORICAL_PREFIX_BYTES).encode("ascii") + b"\0")
    return blob


def _prefix_manifest() -> dict[str, object]:
    return {
        "line_count": HISTORICAL_PREFIX_LINES,
        "bytes": HISTORICAL_PREFIX_BYTES,
        "sha256": HISTORICAL_PREFIX_SHA256,
        "git_blob_sha1": HISTORICAL_PREFIX_GIT_BLOB_SHA1,
    }


def _write_manifest(path: Path, manifest: dict) -> None:
    data = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    require(len(data) <= MAX_MANIFEST_BYTES, "ledger archive manifest exceeds size limit")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _absolute_new_output(output: Path) -> Path:
    output = Path(os.path.abspath(output))
    require(output.name not in ("", ".", ".."), "output must name a new directory")
    try:
        parent = output.parent.resolve(strict=True)
    except OSError as exc:
        raise ValueError("output parent must already exist") from exc
    require(parent.is_dir(), "output parent must be a directory")
    output = parent / output.name
    require(not output.exists() and not output.is_symlink(), "output directory already exists")
    return output


def _publish_directory(stage: Path, output: Path) -> None:
    """Atomically publish a directory only when the destination is absent."""
    source = os.fsencode(stage)
    destination = os.fsencode(output)
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename_exclusive = getattr(libc, "renamex_np", None)
        if rename_exclusive is None:
            raise OSError(errno.ENOTSUP, "atomic exclusive directory rename is unavailable", output)
        rename_exclusive.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename_exclusive.restype = ctypes.c_int
        result = rename_exclusive(source, destination, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        rename_noreplace = getattr(libc, "renameat2", None)
        if rename_noreplace is None:
            raise OSError(errno.ENOTSUP, "atomic no-replace directory rename is unavailable", output)
        rename_noreplace.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                     ctypes.c_char_p, ctypes.c_uint)
        rename_noreplace.restype = ctypes.c_int
        result = rename_noreplace(-100, source, -100, destination, 1)  # AT_FDCWD / RENAME_NOREPLACE
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace directory rename is unavailable", output)
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), output)


def pack(root: Path, output: Path) -> dict:
    """Pack the fixed ledger to a new directory without changing its source."""
    output = _absolute_new_output(Path(output))
    root_fd = _open_root(Path(root))
    source_fd = -1
    stage: Path | None = None
    try:
        source_fd, source_before = _source_file(root_fd)
        require(source_before[2] <= MAX_UNCOMPRESSED_BYTES,
                "ledger exceeds the uncompressed size limit")
        stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
        archive_path = stage / ARCHIVE_NAME
        line_hashes: list[str] = []
        raw_digest = hashlib.sha256()
        prefix_digest = hashlib.sha256()
        prefix_blob_digest = _prefix_blob_hasher()
        prefix_bytes = 0
        raw_bytes = 0
        line_count = 0
        os.lseek(source_fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(source_fd), "rb", buffering=0) as raw_stream:
            with archive_path.open("xb") as compressed_stream:
                with gzip.GzipFile(filename="", mode="wb", fileobj=compressed_stream, mtime=0,
                                   compresslevel=9) as zipped:
                    for line_number in range(1, MAX_LINE_COUNT + 1):
                        line = raw_stream.readline(MAX_LINE_BYTES + 1)
                        if not line:
                            break
                        require(len(line) <= MAX_LINE_BYTES,
                                f"ledger line {line_number} exceeds size limit")
                        line_sha = _validate_line(line, line_number)
                        line_count += 1
                        line_hashes.append(line_sha)
                        if line_count <= HISTORICAL_PREFIX_LINES:
                            prefix_digest.update(line)
                            prefix_blob_digest.update(line)
                            prefix_bytes += len(line)
                        raw_bytes += len(line)
                        require(raw_bytes <= MAX_UNCOMPRESSED_BYTES,
                                "ledger exceeds the uncompressed size limit")
                        raw_digest.update(line)
                        zipped.write(line)
                    else:
                        require(not raw_stream.read(1), "ledger exceeds the line-count limit")
                compressed_stream.flush()
                os.fsync(compressed_stream.fileno())
        require(line_count > 0, "ledger must be non-empty")
        require(line_count >= HISTORICAL_PREFIX_LINES and
                prefix_bytes == HISTORICAL_PREFIX_BYTES and
                prefix_digest.hexdigest() == HISTORICAL_PREFIX_SHA256 and
                prefix_blob_digest.hexdigest() == HISTORICAL_PREFIX_GIT_BLOB_SHA1,
                "ledger does not preserve the pinned v0.9.2 57-line committed prefix")
        require(raw_bytes == source_before[2], "ledger size changed while being packed")
        _check_stamp(source_fd, source_before, "ledger changed while being packed")
        current_source_fd, current_source_stamp = _source_file(root_fd)
        try:
            require(current_source_stamp == source_before,
                    "canonical ledger path changed while being packed")
        finally:
            os.close(current_source_fd)
        source_sha, source_size = _digest_fd(source_fd)
        require(source_sha == raw_digest.hexdigest() and source_size == raw_bytes,
                "ledger bytes changed while being packed")
        _check_stamp(source_fd, source_before, "ledger changed during final verification")
        compressed_sha, compressed_size = _sha_file(archive_path)
        require(compressed_size <= MAX_COMPRESSED_BYTES,
                "compressed ledger exceeds the archive size limit")
        current_source_fd, current_source_stamp = _source_file(root_fd)
        try:
            require(current_source_stamp == source_before,
                    "canonical ledger path changed during final verification")
        finally:
            os.close(current_source_fd)
        manifest = {
            "schema": SCHEMA,
            "source_path": LEDGER_RELATIVE.as_posix(),
            "archive_path": ARCHIVE_NAME,
            "uncompressed": {"sha256": raw_digest.hexdigest(), "bytes": raw_bytes},
            "compressed": {"sha256": compressed_sha, "bytes": compressed_size},
            "line_count": line_count,
            "line_sha256": line_hashes,
            "committed_prefix": _prefix_manifest(),
        }
        _write_manifest(stage / MANIFEST_NAME, manifest)
        # The caller chooses a new directory. The second check narrows races and
        # rename only publishes the complete staged directory.
        require(not output.exists() and not output.is_symlink(), "output directory appeared during packing")
        _publish_directory(stage, output)
        stage = None
        return {
            "status": "packed",
            "manifest_path": (output / MANIFEST_NAME).as_posix(),
            "archive_path": (output / ARCHIVE_NAME).as_posix(),
            "source_path": LEDGER_RELATIVE.as_posix(),
            "line_count": line_count,
            "uncompressed_bytes": raw_bytes,
            "uncompressed_sha256": raw_digest.hexdigest(),
            "compressed_bytes": compressed_size,
            "compressed_sha256": compressed_sha,
        }
    finally:
        if source_fd >= 0:
            os.close(source_fd)
        os.close(root_fd)
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)


def _no_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate manifest key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite manifest value: {value}")


def _parse_manifest(data: bytes) -> dict:
    try:
        manifest = json.loads(data, object_pairs_hook=_no_duplicate_pairs,
                              parse_constant=_reject_constant,
                              parse_float=lambda value: _finite_float(value))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"invalid ledger archive manifest: {exc}") from exc
    require(type(manifest) is dict, "ledger archive manifest must be an object")
    require(set(manifest) == {"schema", "source_path", "archive_path", "uncompressed",
                              "compressed", "line_count", "line_sha256", "committed_prefix"},
            "ledger archive manifest has an unsupported shape")
    require(manifest["schema"] == SCHEMA and manifest["source_path"] == LEDGER_RELATIVE.as_posix(),
            "ledger archive manifest schema or source path is unsupported")
    require(manifest["archive_path"] == ARCHIVE_NAME,
            "ledger archive path must be the fixed sibling archive")
    for key, maximum in (("uncompressed", MAX_UNCOMPRESSED_BYTES),
                         ("compressed", MAX_COMPRESSED_BYTES)):
        item = manifest[key]
        require(type(item) is dict and set(item) == {"sha256", "bytes"},
                f"invalid {key} archive metadata")
        require(type(item["bytes"]) is int and 0 < item["bytes"] <= maximum,
                f"invalid {key} archive size")
        require(type(item["sha256"]) is str and _SHA256.fullmatch(item["sha256"]) is not None,
                f"invalid {key} archive digest")
    require(type(manifest["line_count"]) is int and
            HISTORICAL_PREFIX_LINES <= manifest["line_count"] <= MAX_LINE_COUNT,
            "invalid ledger archive line count")
    prefix = manifest["committed_prefix"]
    require(type(prefix) is dict and prefix == _prefix_manifest(),
            "ledger archive manifest does not contain the pinned committed prefix")
    lines = manifest["line_sha256"]
    require(type(lines) is list and len(lines) == manifest["line_count"],
            "ledger line hash list does not match line count")
    require(all(type(value) is str and _SHA256.fullmatch(value) is not None for value in lines),
            "invalid ledger line digest")
    return manifest


def _finite_float(value: str) -> float:
    result = float(value)
    require(math.isfinite(result), "non-finite manifest number")
    return result


def _parse_index(data: bytes) -> tuple[PurePosixPath, str]:
    try:
        index = json.loads(data, object_pairs_hook=_no_duplicate_pairs,
                           parse_constant=_reject_constant,
                           parse_float=lambda value: _finite_float(value))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"invalid ledger archive index: {exc}") from exc
    require(type(index) is dict and set(index) == {"schema", "manifest"},
            "ledger archive index has an unsupported shape")
    require(index["schema"] == INDEX_SCHEMA, "unsupported ledger archive index schema")
    selected = index["manifest"]
    require(type(selected) is dict and set(selected) == {"path", "sha256"},
            "ledger archive index manifest reference has an unsupported shape")
    require(type(selected["path"]) is str, "ledger archive index manifest path must be a string")
    relative = _safe_relative(selected["path"])
    prefix = ARCHIVES_RELATIVE.parts
    require(relative.parts[:len(prefix)] == prefix and len(relative.parts) == len(prefix) + 2 and
            relative.parts[-1] == MANIFEST_NAME and
            _ARCHIVE_ENTRY.fullmatch(relative.parts[-2]) is not None,
            "indexed manifest must be a manifest.json inside a ledger-archives entry")
    digest = selected["sha256"]
    require(type(digest) is str and _SHA256.fullmatch(digest) is not None,
            "ledger archive index has an invalid manifest digest")
    return relative, digest


class _HashingReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.size = 0

    def read(self, size: int = -1) -> bytes:
        data = self.stream.read(size)
        self.digest.update(data)
        self.size += len(data)
        return data


def _read_bounded_file(root_fd: int, relative: PurePosixPath,
                       maximum: int, description: str) -> tuple[bytes, tuple[int, ...]]:
    fd, before = _open_file(root_fd, relative)
    try:
        require(before[2] <= maximum, f"{description} exceeds size limit")
        chunks = []
        remaining = maximum + 1
        while remaining:
            block = os.read(fd, min(BLOCK_BYTES, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        data = b"".join(chunks)
        require(len(data) <= maximum, f"{description} exceeds size limit")
        require(len(data) == before[2], f"{description} changed while being read")
        require(_stamp(os.fstat(fd)) == before, f"{description} changed while being read")
        return data, before
    finally:
        os.close(fd)


def _read_manifest(root_fd: int, relative: PurePosixPath,
                   expected_sha256: str | None = None) -> tuple[dict, tuple[int, ...], str]:
    data, before = _read_bounded_file(root_fd, relative, MAX_MANIFEST_BYTES,
                                      "ledger archive manifest")
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None:
        require(digest == expected_sha256,
                "indexed ledger archive manifest digest mismatch")
    return _parse_manifest(data), before, digest


def _read_current_index(root_fd: int) -> tuple[PurePosixPath, str, str]:
    data, _before = _read_bounded_file(root_fd, CURRENT_INDEX_RELATIVE, MAX_INDEX_BYTES,
                                       "ledger archive current index")
    index_digest = hashlib.sha256(data).hexdigest()
    manifest_path, manifest_digest = _parse_index(data)
    return manifest_path, manifest_digest, index_digest


def _hash_existing(root_fd: int, relative: PurePosixPath) -> tuple[str, int] | None:
    parent_fd = _open_dir(root_fd, relative.parts[:-1])
    try:
        try:
            info = os.stat(relative.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        require(stat.S_ISREG(info.st_mode), "existing canonical ledger is not a regular file")
        fd = os.open(relative.name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                      getattr(os, "O_NONBLOCK", 0), dir_fd=parent_fd)
        try:
            before = _stamp(os.fstat(fd))
            require(stat.S_ISREG(os.fstat(fd).st_mode),
                    "existing canonical ledger is not a regular file")
            result = _digest_fd(fd)
            require(_stamp(os.fstat(fd)) == before, "existing canonical ledger changed while being checked")
            return result
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def _create_temp(parent_fd: int) -> tuple[str, int]:
    for _ in range(100):
        name = f".ledger-v1.jsonl.hydrate-{secrets.token_hex(12)}.tmp"
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
            return name, fd
        except FileExistsError:
            continue
    raise FileExistsError("could not allocate a unique temporary ledger file")


def _hydrate_archive(root_fd: int, archive_relative: PurePosixPath,
                     manifest: dict, parent_fd: int, temp_fd: int) -> tuple[str, int]:
    archive_fd, archive_before = _open_file(root_fd, archive_relative)
    try:
        require(archive_before[2] == manifest["compressed"]["bytes"],
                "compressed ledger size mismatch")
        digest = hashlib.sha256()
        prefix_digest = hashlib.sha256()
        prefix_blob_digest = _prefix_blob_hasher()
        prefix_bytes = 0
        line_hashes = manifest["line_sha256"]
        total = 0
        line_count = 0
        os.lseek(temp_fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(archive_fd), "rb", buffering=0) as raw_archive:
            hashing = _HashingReader(raw_archive)
            with gzip.GzipFile(fileobj=hashing, mode="rb") as zipped:
                while True:
                    line = zipped.readline(MAX_LINE_BYTES + 1)
                    if not line:
                        break
                    line_count += 1
                    require(line_count <= MAX_LINE_COUNT, "ledger exceeds the line-count limit")
                    require(line_count <= len(line_hashes), "archive has more ledger lines than manifest")
                    line_sha = _validate_line(line, line_count)
                    require(line_sha == line_hashes[line_count - 1],
                            f"ledger line {line_count} digest mismatch")
                    if line_count <= HISTORICAL_PREFIX_LINES:
                        prefix_digest.update(line)
                        prefix_blob_digest.update(line)
                        prefix_bytes += len(line)
                    total += len(line)
                    require(total <= MAX_UNCOMPRESSED_BYTES,
                            "ledger exceeds the uncompressed size limit")
                    digest.update(line)
                    view = memoryview(line)
                    while view:
                        count = os.write(temp_fd, view)
                        view = view[count:]
                # Reading to EOF forces gzip CRC/length verification.
            while hashing.read(BLOCK_BYTES):
                pass
        require(line_count == manifest["line_count"], "ledger line count mismatch")
        require(line_count >= HISTORICAL_PREFIX_LINES and
                prefix_bytes == HISTORICAL_PREFIX_BYTES and
                prefix_digest.hexdigest() == HISTORICAL_PREFIX_SHA256 and
                prefix_blob_digest.hexdigest() == HISTORICAL_PREFIX_GIT_BLOB_SHA1,
                "uncompressed ledger does not preserve the pinned committed prefix")
        require(total == manifest["uncompressed"]["bytes"], "uncompressed ledger size mismatch")
        require(digest.hexdigest() == manifest["uncompressed"]["sha256"],
                "uncompressed ledger digest mismatch")
        require(hashing.size == manifest["compressed"]["bytes"] and
                hashing.digest.hexdigest() == manifest["compressed"]["sha256"],
                "compressed ledger digest mismatch")
        require(total > 0, "uncompressed ledger is empty")
        os.fsync(temp_fd)
        require(_stamp(os.fstat(archive_fd)) == archive_before,
                "compressed ledger changed while being hydrated")
        return digest.hexdigest(), total
    finally:
        os.close(archive_fd)


def hydrate(root: Path, manifest_path: str | Path, *,
            expected_manifest_sha256: str | None = None) -> dict:
    """Verify and atomically restore the fixed canonical ledger path."""
    manifest_relative = _safe_relative(manifest_path)
    if expected_manifest_sha256 is not None:
        require(_SHA256.fullmatch(expected_manifest_sha256) is not None,
                "expected manifest digest must be lowercase SHA-256")
    release_parts = LEDGER_RELATIVE.parent.parts
    require(manifest_relative.parts[:len(release_parts)] == release_parts,
            "manifest must be inside the v0.9.2 release directory")
    root_fd = _open_root(Path(root))
    parent_fd = -1
    temp_name: str | None = None
    temp_fd = -1
    try:
        manifest, _manifest_before, _manifest_sha256 = _read_manifest(
            root_fd, manifest_relative, expected_manifest_sha256,
        )
        archive_relative = manifest_relative.parent / ARCHIVE_NAME
        archive_relative = _safe_relative(archive_relative.as_posix())
        # Canonical placement prevents the manifest from selecting an archive
        # elsewhere in the repository, even with a valid digest.
        require(archive_relative.parent == manifest_relative.parent,
                "archive must be a sibling of its manifest")
        parent_fd = _open_dir(root_fd, LEDGER_RELATIVE.parts[:-1])
        temp_name, temp_fd = _create_temp(parent_fd)
        raw_sha, raw_bytes = _hydrate_archive(root_fd, archive_relative, manifest,
                                              parent_fd, temp_fd)
        os.fchmod(temp_fd, 0o644)
        temp_stamp = _stamp(os.fstat(temp_fd))
        require(temp_stamp[2] == raw_bytes, "temporary ledger size mismatch")
        os.close(temp_fd)
        temp_fd = -1

        existing = _hash_existing(root_fd, LEDGER_RELATIVE)
        if existing is not None:
            require(existing == (raw_sha, raw_bytes),
                    "refusing to replace different existing canonical ledger bytes")
            os.unlink(temp_name, dir_fd=parent_fd)
            temp_name = None
            return {
                "status": "already-present",
                "canonical_path": LEDGER_RELATIVE.as_posix(),
                "line_count": manifest["line_count"],
                "bytes": raw_bytes,
                "sha256": raw_sha,
                "existing_file_preserved": True,
            }

        try:
            os.link(temp_name, LEDGER_RELATIVE.name, src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd, follow_symlinks=False)
        except FileExistsError:
            existing = _hash_existing(root_fd, LEDGER_RELATIVE)
            require(existing == (raw_sha, raw_bytes),
                    "refusing to replace different existing canonical ledger bytes")
            os.unlink(temp_name, dir_fd=parent_fd)
            temp_name = None
            return {
                "status": "already-present",
                "canonical_path": LEDGER_RELATIVE.as_posix(),
                "line_count": manifest["line_count"],
                "bytes": raw_bytes,
                "sha256": raw_sha,
                "existing_file_preserved": True,
            }
        os.unlink(temp_name, dir_fd=parent_fd)
        temp_name = None
        os.fsync(parent_fd)
        return {
            "status": "hydrated",
            "canonical_path": LEDGER_RELATIVE.as_posix(),
            "line_count": manifest["line_count"],
            "bytes": raw_bytes,
            "sha256": raw_sha,
            "existing_file_preserved": False,
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


def hydrate_current(root: Path) -> dict:
    """Hydrate only the immutable manifest selected by the tracked current index."""
    root_fd = _open_root(Path(root))
    try:
        manifest_path, manifest_sha256, index_sha256 = _read_current_index(root_fd)
    finally:
        os.close(root_fd)
    result = hydrate(root, manifest_path, expected_manifest_sha256=manifest_sha256)
    result.update({
        "current_index_path": CURRENT_INDEX_RELATIVE.as_posix(),
        "current_index_sha256": index_sha256,
        "selected_manifest_path": manifest_path.as_posix(),
        "selected_manifest_sha256": manifest_sha256,
    })
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack", help="pack the fixed v0.9.2 ledger")
    pack_parser.add_argument("--root", type=Path, required=True)
    pack_parser.add_argument("--output", type=Path, required=True,
                             help="new directory for ledger-v1.jsonl.gz and manifest.json")
    hydrate_parser = commands.add_parser("hydrate", help="verify and restore the fixed ledger path")
    hydrate_parser.add_argument("--root", type=Path, required=True)
    hydrate_parser.add_argument("--manifest", required=True,
                                help="safe repository-relative path to the tracked manifest")
    current_parser = commands.add_parser(
        "hydrate-current", help="hydrate the immutable archive selected by the tracked current index",
    )
    current_parser.add_argument("--root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "pack":
        result = pack(args.root, args.output)
    elif args.command == "hydrate":
        result = hydrate(args.root, args.manifest)
    else:
        result = hydrate_current(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
