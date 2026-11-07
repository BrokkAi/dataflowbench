"""Strict in-memory proof for the exact v0.9.2 native06 evidence mini-archive.

This module never imports objects, creates a checkout, or extracts files. It
validates the committed LFS pointer separately from the stable worktree bytes,
then parses a bounded gzip/USTAR stream in memory.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Mapping
import zlib


INDEX_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native06-archived-evidence-index-02.json",
    "sha256": "9d4f9b105a0b936873cbd7ca578262b445a9aebeda8501583f56bf0d7bdf2e6e",
}
REQUEST05_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-05.json",
    "sha256": "c5de0f8732a375db15ee7ba1148d227abe6c7ece736ea28a6573105b9a183fe5",
}
HELPER_SOURCE_PATH = "reports/releases/v0.9.2/acquisition/joern-native-controls-08/archive_evidence.py"
ARCHIVE_PATH = "evidence-delivery/v092-native-evidence-96-01/detail/native-evidence.tar.gz.part0000"
ARCHIVE_PREFIX = "reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/"
HISTORICAL_SOURCE = "2991bfb897cad98674efc2feb04388174295e885"
INDEX_SCHEMA = "v092-native-evidence-copies/v1"
SCOPE = "Lossless copies of historical measurement JSON inputs; not new experiments or direct raw Git blobs."
EXPECTED_MEMBER_COUNT = 96
EXPECTED_ARCHIVE_SHA256 = "78b5b2b2a551d2cd666013dd43d2b1fd947a5431d8d742533c06c06f5351cfbd"
EXPECTED_ARCHIVE_BYTES = 57839
EXPECTED_TAR_BYTES = 501760
EXPECTED_PAYLOAD_BYTES = 431729
MAX_COMPRESSED_BYTES = 2 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 2 * 1024 * 1024
MAX_REFERENCE_BYTES = 256 * 1024 * 1024
LFS_VERSION = b"version https://git-lfs.github.com/spec/v1\n"


class ArchiveEvidenceError(ValueError):
    """An index, archive, source binding, or bounded parse check failed."""


@dataclass(frozen=True)
class ArchiveContext:
    index_ref: dict[str, str]
    request05_ref: dict[str, str]
    helper_ref: dict[str, str]
    member_refs: dict[str, dict[str, str]]
    member_bytes: dict[str, bytes]
    member_sizes: dict[str, int]
    required_source_refs: tuple[dict[str, str], ...]
    archive_path: str
    lfs_pointer: bytes
    archive_sha256: str
    archive_bytes: int
    tar_bytes: int
    total_payload_bytes: int
    historical_source_commit: str


def _require(value: Any, message: str) -> None:
    if not value:
        raise ArchiveEvidenceError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON object key")
        result[key] = value
    return result


def _strict_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ArchiveEvidenceError) as error:
        raise ArchiveEvidenceError(label + " is not strict UTF-8 JSON") from error
    _require(type(value) is dict, label + " must be a JSON object")
    return value


def _canonical_ref(ref: Any, label: str) -> dict[str, str]:
    _require(type(ref) is dict and set(ref) == {"path", "sha256"}, label + " reference fields differ")
    path = ref["path"]
    digest = ref["sha256"]
    _require(type(path) is str and path and "\n" not in path and "\r" not in path,
             label + " path is malformed")
    pure = PurePosixPath(path)
    _require(not pure.is_absolute() and pure.as_posix() == path and ".." not in pure.parts,
             label + " path is not canonical")
    _require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
             label + " SHA-256 is malformed")
    return {"path": path, "sha256": digest}


def read_stable(root: Path, relative_path: str, *, max_bytes: int = MAX_REFERENCE_BYTES) -> bytes:
    """Read one non-symlink regular file whose identity/size/times stay fixed."""
    ref = _canonical_ref({"path": relative_path, "sha256": "0" * 64}, "stable file")
    path = root / ref["path"]
    _require(not any(part.is_symlink() for part in (path, *path.parents)),
             "symlink source path forbidden: " + relative_path)
    try:
        before = path.stat()
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= max_bytes,
                 "bounded regular source file required: " + relative_path)
        raw = path.read_bytes()
        after = path.stat()
    except OSError as error:
        raise ArchiveEvidenceError("source file cannot be read: " + relative_path) from error
    signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
    _require(signature(before) == signature(after) and len(raw) == after.st_size,
             "source file changed while read: " + relative_path)
    _require(not any(part.is_symlink() for part in (path, *path.parents)),
             "source path changed to symlink: " + relative_path)
    return raw


def _member_specs(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _require(set(index) == {
        "archive", "historical_source_commit", "member_count", "members", "path_prefix",
        "retained_request05", "schema", "scope", "total_payload_bytes",
    }, "archive index fields differ")
    _require(index["schema"] == INDEX_SCHEMA and index["scope"] == SCOPE,
             "archive index identity/scope differs")
    _require(index["historical_source_commit"] == HISTORICAL_SOURCE,
             "historical source identity differs")
    _require(type(index["path_prefix"]) is str and index["path_prefix"] == ARCHIVE_PREFIX,
             "archive member prefix differs")
    _require(type(index["member_count"]) is int and index["member_count"] == EXPECTED_MEMBER_COUNT,
             "archive member count differs")
    _require(type(index["total_payload_bytes"]) is int and index["total_payload_bytes"] == EXPECTED_PAYLOAD_BYTES,
             "archive payload size differs")
    _require(type(index["archive"]) is dict and set(index["archive"]) == {"bytes", "path", "sha256", "tar_bytes"},
             "archive binding fields differ")
    archive = index["archive"]
    _require(archive == {
        "bytes": EXPECTED_ARCHIVE_BYTES,
        "path": ARCHIVE_PATH,
        "sha256": EXPECTED_ARCHIVE_SHA256,
        "tar_bytes": EXPECTED_TAR_BYTES,
    }, "archive pointer binding differs")
    _require(type(index["members"]) is list and len(index["members"]) == EXPECTED_MEMBER_COUNT,
             "archive member list count differs")

    result: dict[str, dict[str, Any]] = {}
    paths: list[str] = []
    for item in index["members"]:
        _require(type(item) is dict and set(item) == {"bytes", "path", "sha256"},
                 "archive member fields differ")
        path = item["path"]
        _require(type(path) is str and is_archived_member_path(path),
                 "archive member is outside the exact raw-capture path scope")
        pure = PurePosixPath(path)
        _require(not pure.is_absolute() and pure.as_posix() == path and ".." not in pure.parts,
                 "archive member path traversal")
        _require(path not in result, "duplicate archive index member")
        _require(type(item["bytes"]) is int and 0 <= item["bytes"] <= MAX_DECOMPRESSED_BYTES,
                 "archive member byte count is malformed")
        _require(type(item["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
                 "archive member SHA-256 is malformed")
        result[path] = {"bytes": item["bytes"], "path": path, "sha256": item["sha256"]}
        paths.append(path)
    _require(paths == sorted(paths), "archive index members are not in canonical sorted order")
    _require(sum(item["bytes"] for item in result.values()) == EXPECTED_PAYLOAD_BYTES,
             "archive member payload total differs")
    return result


def is_archived_member_path(path: Any) -> bool:
    """Whether a path is exactly `<pinned capture prefix>/<case-id>/raw.json`."""
    if type(path) is not str or re.fullmatch(re.escape(ARCHIVE_PREFIX) + r"[^/]+/raw\.json", path) is None:
        return False
    case_id = path[len(ARCHIVE_PREFIX):-len("/raw.json")]
    return case_id not in {".", ".."} and "\\" not in case_id and "\0" not in case_id


def _request05_sources(request05: dict[str, Any], members: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    _require(request05.get("schema") == "v092-joern-native-control-request/v1",
             "retained request05 schema differs")
    _require(request05.get("expected_head") == HISTORICAL_SOURCE,
             "retained request05 expected head differs from historical source pin")
    source_refs = request05.get("source_refs")
    _require(type(source_refs) is list and len(source_refs) > 0,
             "retained request05 source references missing")
    result: dict[str, dict[str, str]] = {}
    for value in source_refs:
        ref = _canonical_ref(value, "retained request05 source")
        _require(ref["path"] not in result, "duplicate retained request05 source path")
        result[ref["path"]] = ref
    archived_request_paths = {
        path for path in result
        if path.startswith(ARCHIVE_PREFIX) and path.endswith("/raw.json")
    }
    _require(archived_request_paths == set(members),
             "archive index is not the exact retained request05 raw-capture subset")
    for path, member in members.items():
        _require(result.get(path) == {"path": path, "sha256": member["sha256"]},
                 "archive member SHA differs from retained request05 source refs")
    return result


def lfs_pointer(archive_record: dict[str, Any]) -> bytes:
    """Return the exact three-line Git LFS pointer bound by the index."""
    _require(type(archive_record) is dict and set(archive_record) == {"bytes", "path", "sha256", "tar_bytes"},
             "archive pointer record malformed")
    _require(archive_record["path"] == ARCHIVE_PATH and archive_record["sha256"] == EXPECTED_ARCHIVE_SHA256 and
             archive_record["bytes"] == EXPECTED_ARCHIVE_BYTES,
             "archive pointer identity differs")
    return (
        LFS_VERSION + b"oid sha256:" + archive_record["sha256"].encode("ascii") + b"\nsize " +
        str(archive_record["bytes"]).encode("ascii") + b"\n"
    )


def _field(block: bytes, start: int, end: int, label: str) -> str:
    value = block[start:end]
    nul = value.find(b"\0")
    if nul >= 0:
        _require(not any(value[nul:]), "nonzero bytes after USTAR " + label + " terminator")
        value = value[:nul]
    try:
        return value.decode("ascii")
    except UnicodeDecodeError as error:
        raise ArchiveEvidenceError("non-ASCII USTAR " + label) from error


def _octal(block: bytes, start: int, end: int, label: str) -> int:
    value = block[start:end].strip(b" \0")
    _require(bool(value) and all(byte in b"01234567" for byte in value),
             "malformed USTAR octal " + label)
    return int(value, 8)


def _parse_ustar(tar_bytes: bytes, members: Mapping[str, dict[str, Any]], total_payload_bytes: int) -> dict[str, bytes]:
    _require(len(tar_bytes) % 512 == 0, "tar stream is not block aligned")
    payloads: dict[str, bytes] = {}
    payload_total = 0
    offset = 0
    terminated = False
    while offset + 512 <= len(tar_bytes):
        block = tar_bytes[offset:offset + 512]
        if block == b"\0" * 512:
            _require(offset + 1024 <= len(tar_bytes), "USTAR end marker is truncated")
            _require(tar_bytes[offset:] == b"\0" * (len(tar_bytes) - offset),
                     "nonzero data follows USTAR end marker")
            terminated = True
            break
        _require(block[257:263] == b"ustar\0" and block[263:265] == b"00",
                 "archive contains non-USTAR or extension header")
        _require(block[156:157] in (b"\0", b"0"),
                 "archive entry is not a regular USTAR file")
        _require(block[157:257] == b"\0" * 100,
                 "archive regular file has a link target")
        expected_checksum = _octal(block, 148, 156, "checksum")
        actual_checksum = sum(block[:148]) + sum(b" " * 8) + sum(block[156:])
        _require(actual_checksum == expected_checksum, "USTAR header checksum mismatch")
        name = _field(block, 0, 100, "name")
        prefix = _field(block, 345, 500, "prefix")
        path = prefix + "/" + name if prefix else name
        pure = PurePosixPath(path)
        _require(path and not pure.is_absolute() and pure.as_posix() == path and ".." not in pure.parts,
                 "USTAR member path traversal or noncanonical name")
        _require(path in members, "USTAR contains an unindexed extra member")
        _require(path not in payloads, "USTAR contains a duplicate member")
        size = _octal(block, 124, 136, "size")
        _require(size == members[path]["bytes"], "USTAR member length differs from index")
        data_start = offset + 512
        data_end = data_start + size
        padded_end = data_start + ((size + 511) // 512) * 512
        _require(data_end <= len(tar_bytes) and padded_end <= len(tar_bytes),
                 "USTAR member data is truncated")
        data = tar_bytes[data_start:data_end]
        _require(sha256(data) == members[path]["sha256"],
                 "USTAR member SHA-256 differs from index")
        _require(tar_bytes[data_end:padded_end] == b"\0" * (padded_end - data_end),
                 "USTAR member padding is nonzero")
        payloads[path] = data
        payload_total += size
        offset = padded_end
    _require(terminated, "USTAR end marker missing")
    _require(set(payloads) == set(members), "USTAR member set differs from exact index set")
    _require(payload_total == total_payload_bytes, "USTAR total payload differs from index")
    return payloads


def parse_compressed_archive(
    compressed: bytes,
    *,
    archive_record: dict[str, Any],
    members: Mapping[str, dict[str, Any]],
    total_payload_bytes: int,
) -> dict[str, bytes]:
    """Bound and validate a single gzip stream containing exact USTAR members."""
    _require(type(compressed) is bytes and len(compressed) <= MAX_COMPRESSED_BYTES,
             "compressed archive exceeds size bound")
    _require(len(compressed) == archive_record.get("bytes") and
             sha256(compressed) == archive_record.get("sha256"),
             "compressed archive length or SHA-256 differs from index")
    decoder = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
    try:
        tar_bytes = decoder.decompress(compressed, MAX_DECOMPRESSED_BYTES + 1)
    except zlib.error as error:
        raise ArchiveEvidenceError("archive gzip stream is malformed") from error
    _require(len(tar_bytes) <= MAX_DECOMPRESSED_BYTES and not decoder.unconsumed_tail,
             "decompressed archive exceeds size bound")
    _require(decoder.eof and not decoder.unused_data,
             "archive must be one complete gzip stream with no trailing bytes")
    _require(len(tar_bytes) == archive_record.get("tar_bytes"),
             "decompressed tar length differs from index")
    _require(total_payload_bytes <= MAX_DECOMPRESSED_BYTES,
             "declared archive payload exceeds size bound")
    return _parse_ustar(tar_bytes, members, total_payload_bytes)


def build_context(root: Path, source_map: Mapping[str, dict[str, str]]) -> ArchiveContext:
    """Validate fixed index/request/helper/live files and return one reusable context."""
    _require(isinstance(root, Path) and root.is_absolute() and root.resolve() == root,
             "canonical repository root required for archive evidence")
    _require(isinstance(source_map, Mapping), "source reference map required")
    _require(ARCHIVE_PATH not in source_map,
             "LFS archive part must be handled as typed pointer evidence, not an ordinary source ref")
    for ref, label in ((INDEX_REF, "archive index"), (REQUEST05_REF, "retained request05")):
        _require(source_map.get(ref["path"]) == ref, label + " is outside current source closure")

    index_raw = read_stable(root, INDEX_REF["path"], max_bytes=8 * 1024 * 1024)
    _require(sha256(index_raw) == INDEX_REF["sha256"], "archive index source digest differs")
    index = _strict_json(index_raw, "archive index")
    members = _member_specs(index)
    _require(index.get("retained_request05") == REQUEST05_REF,
             "archive index retained-request05 identity differs")

    request05_raw = read_stable(root, REQUEST05_REF["path"], max_bytes=32 * 1024 * 1024)
    _require(sha256(request05_raw) == REQUEST05_REF["sha256"], "retained request05 source digest differs")
    request05 = _strict_json(request05_raw, "retained request05")
    _request05_sources(request05, members)

    module_path = Path(__file__)
    expected_running_path = (root / HELPER_SOURCE_PATH).resolve(strict=True)
    _require(module_path.is_absolute() and not module_path.is_symlink() and
             module_path == expected_running_path,
             "archive helper must execute from its exact committed source path")
    running_helper = read_stable(root, HELPER_SOURCE_PATH, max_bytes=8 * 1024 * 1024)
    helper_ref = {"path": HELPER_SOURCE_PATH, "sha256": sha256(running_helper)}
    helper_ref = _canonical_ref(helper_ref, "archive helper source")
    _require(source_map.get(HELPER_SOURCE_PATH) == helper_ref,
             "archive helper source is outside exact current source closure")
    helper_bytes = read_stable(root, HELPER_SOURCE_PATH, max_bytes=8 * 1024 * 1024)
    _require(helper_bytes == running_helper, "running archive helper differs from bound helper source")

    archive_record = index["archive"]
    _require(archive_record["path"] == ARCHIVE_PATH,
             "archive path differs from exact evidence-delivery location")
    compressed = read_stable(root, ARCHIVE_PATH, max_bytes=MAX_COMPRESSED_BYTES)
    member_bytes = parse_compressed_archive(
        compressed,
        archive_record=archive_record,
        members=members,
        total_payload_bytes=index["total_payload_bytes"],
    )

    member_refs: dict[str, dict[str, str]] = {}
    for path, member in members.items():
        ref = {"path": path, "sha256": member["sha256"]}
        _require(source_map.get(path) == ref,
                 "archived raw source is outside exact reviewed source closure: " + path)
        live = read_stable(root, path, max_bytes=MAX_DECOMPRESSED_BYTES)
        _require(len(live) == member["bytes"] and sha256(live) == member["sha256"] and
                 live == member_bytes[path],
                 "live archived raw source differs from stable indexed archive member: " + path)
        member_refs[path] = ref

    required: dict[str, dict[str, str]] = {}
    for ref in (INDEX_REF, REQUEST05_REF, helper_ref, *member_refs.values()):
        _require(ref["path"] not in required or required[ref["path"]] == ref,
                 "archive required-source closure contains a conflicting path")
        required[ref["path"]] = ref
    for path, ref in required.items():
        _require(source_map.get(path) == ref,
                 "archive required-source closure omitted or rebound: " + path)

    return ArchiveContext(
        index_ref=dict(INDEX_REF),
        request05_ref=dict(REQUEST05_REF),
        helper_ref=helper_ref,
        member_refs=member_refs,
        member_bytes=member_bytes,
        member_sizes={path: item["bytes"] for path, item in members.items()},
        required_source_refs=tuple(required[path] for path in sorted(required)),
        archive_path=ARCHIVE_PATH,
        lfs_pointer=lfs_pointer(archive_record),
        archive_sha256=archive_record["sha256"],
        archive_bytes=archive_record["bytes"],
        tar_bytes=archive_record["tar_bytes"],
        total_payload_bytes=index["total_payload_bytes"],
        historical_source_commit=index["historical_source_commit"],
    )
