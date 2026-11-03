"""Read-only, pinned 130-row history baseline for a future Joern adapter.

This module verifies one exact ledger snapshot and returns the sealed 109-row
history and the separate 21-row Bifrost v0.14.4 annex. It grants no execution
or publication authority and does not create a source CAS or current core.
"""

from __future__ import annotations

import collections
import gzip
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path("/Users/dave/.codex/worktrees/9f01/dataflowbench")
MAX_FILE_BYTES = 256 * 1024 * 1024
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

LIVE_LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
LEDGER_INDEX_PATH = "reports/releases/v0.9.2/ledger-archive-index.json"
LEDGER_INDEX_SHA256 = "899639bdae201a981a89922855ea49eef06606e70a016508cd9eafd77cd5635b"
LEDGER_MANIFEST_PATH = "reports/releases/v0.9.2/ledger-archives/ledger-130-01/manifest.json"
LEDGER_MANIFEST_SHA256 = "5408d3d312aa3da502ead1eb3f2273aaa05e7c6505305c487221008bdb5ad812"
LEDGER_ARCHIVE_PATH = "reports/releases/v0.9.2/ledger-archives/ledger-130-01/ledger-v1.jsonl.gz"
LEDGER_ARCHIVE_SHA256 = "499c7f844f18723947696657695dbea02f8525cff25bd34c6973f00ec2cd4efd"
LEDGER_ARCHIVE_BYTES = 13_299_105
LEDGER_RAW_SHA256 = "79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84"
LEDGER_RAW_BYTES = 126_023_630
LEDGER_ROWS = 130

SEALED109_ROWS = 109
SEALED109_RAW_SHA256 = "2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851"
SEALED109_MANIFEST_PATH = "reports/releases/v0.9.2/ledger-archives/ledger-109-01/manifest.json"
SEALED109_MANIFEST_SHA256 = "27ebd800655237012acb0bac6869294119947955501d737eab6e8d60a3ff3bb4"
SEALED109_ARCHIVE_PATH = "reports/releases/v0.9.2/ledger-archives/ledger-109-01/ledger-v1.jsonl.gz"
SEALED109_ARCHIVE_SHA256 = "1130e910b3b3198550652a90df1bdee487b0c097757cc7f785ab71c93a0813b1"
SEALED109_ARCHIVE_BYTES = 12_990_606
SEALED109_RAW_BYTES = 123_908_716

INDEX_TRANSITION_PATH = (
    "reports/releases/v0.9.2/validation/bifrost-v0144-delivery-01/"
    "ledger-index-transition-130-01.json"
)
INDEX_TRANSITION_SHA256 = "74fadc79ca6655e9c11c9d4893fff1b19ce3abb1865fd8da14b4d2e39ca6ac7b"
PREVIOUS_INDEX_SHA256 = "e9fa419bf07c7d86810d91c43cce03266a67d28ac7a31ac02ad35ea3dea75f30"
PREVIOUS_INDEX_SCHEMA = "dataflowbench-v092-ledger-index/v1"
LEDGER_INDEX_SCHEMA = "dataflowbench-v092-ledger-index/v1"
LEDGER_MANIFEST_SCHEMA = "dataflowbench-v092-ledger-archive/v1"
TRANSITION_SCHEMA = "v092-ledger-index-transition/v1"

SEALED109_DESCRIPTOR_PATH = (
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
    "history-provider-descriptor-01.json"
)
SEALED109_DESCRIPTOR_SHA256 = "dc771f3bf7de580d826bff62150fb64e28fdf7a3b7aeb180dab876ea19c35eca"
SEALED109_READER_PATH = "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history_provider_02.py"
SEALED109_READER_SHA256 = "da691ca16a4d1169e1f32d3524fb146bc4e60722dd99ea12bb9e03ac38436a8b"

C5_ANNEX_SHA256 = "3390bc38b5b3a8c2889c6654a816681012d578c42e6ac6a59cc6b2e4c8fbded0"
C5_SOURCE_COMMIT = "61ae0cb817322ac81528217479c0be7bd760fa36"
C5_PLAN_COMMIT = "6500465e02e28ac279047e610d7e8dbccc844ee8"
C5_CONTRACT_SHA256 = "1d2188df4e7bc7f5cc4e28cc0700a839a294b0cbecc484f4d9658bb5280164e4"

PREFIX_STATUS_COUNTS = {"completed": 103, "failed": 3, "recorder-error": 3}
ANNEX_STATUS_COUNTS = {"completed": 19, "recorder-error": 2}
TOTAL_STATUS_COUNTS = {"completed": 122, "failed": 3, "recorder-error": 5}


@dataclass(frozen=True)
class AnnexIdentity:
    group_id: str
    attempt_id: str
    global_attempt_number: int
    status: str


@dataclass(frozen=True)
class Pins:
    """Immutable baseline pins; alternate instances are for synthetic tests only."""

    live_ledger_path: str
    index_path: str
    index_sha256: str
    manifest_path: str
    manifest_sha256: str
    archive_path: str
    archive_sha256: str
    archive_bytes: int
    raw_sha256: str
    raw_bytes: int
    row_count: int
    transition_path: str
    transition_sha256: str
    previous_index_sha256: str
    previous_manifest_path: str
    previous_manifest_sha256: str
    previous_archive_path: str
    previous_archive_sha256: str
    previous_archive_bytes: int
    previous_raw_bytes: int
    prefix_rows: int
    prefix_raw_sha256: str
    suffix_raw_sha256: str
    prefix_status_counts: dict[str, int]
    suffix_status_counts: dict[str, int]
    total_status_counts: dict[str, int]
    suffix_source_commit: str
    suffix_plan_commit: str
    suffix_contract_sha256: str
    suffix_identities: tuple[AnnexIdentity, ...]


PRODUCTION_PINS = Pins(
    live_ledger_path=LIVE_LEDGER_PATH,
    index_path=LEDGER_INDEX_PATH,
    index_sha256=LEDGER_INDEX_SHA256,
    manifest_path=LEDGER_MANIFEST_PATH,
    manifest_sha256=LEDGER_MANIFEST_SHA256,
    archive_path=LEDGER_ARCHIVE_PATH,
    archive_sha256=LEDGER_ARCHIVE_SHA256,
    archive_bytes=LEDGER_ARCHIVE_BYTES,
    raw_sha256=LEDGER_RAW_SHA256,
    raw_bytes=LEDGER_RAW_BYTES,
    row_count=LEDGER_ROWS,
    transition_path=INDEX_TRANSITION_PATH,
    transition_sha256=INDEX_TRANSITION_SHA256,
    previous_index_sha256=PREVIOUS_INDEX_SHA256,
    previous_manifest_path=SEALED109_MANIFEST_PATH,
    previous_manifest_sha256=SEALED109_MANIFEST_SHA256,
    previous_archive_path=SEALED109_ARCHIVE_PATH,
    previous_archive_sha256=SEALED109_ARCHIVE_SHA256,
    previous_archive_bytes=SEALED109_ARCHIVE_BYTES,
    previous_raw_bytes=SEALED109_RAW_BYTES,
    prefix_rows=SEALED109_ROWS,
    prefix_raw_sha256=SEALED109_RAW_SHA256,
    suffix_raw_sha256=C5_ANNEX_SHA256,
    prefix_status_counts=PREFIX_STATUS_COUNTS,
    suffix_status_counts=ANNEX_STATUS_COUNTS,
    total_status_counts=TOTAL_STATUS_COUNTS,
    suffix_source_commit=C5_SOURCE_COMMIT,
    suffix_plan_commit=C5_PLAN_COMMIT,
    suffix_contract_sha256=C5_CONTRACT_SHA256,
    suffix_identities=(
        AnnexIdentity("bifrost-c-kernel", "bifrost-c-kernel-attempt-04-series-03", 111, "completed"),
        AnnexIdentity("bifrost-cpp-kernel", "bifrost-cpp-kernel-attempt-03-series-03", 112, "completed"),
        AnnexIdentity("bifrost-csharp-kernel", "bifrost-csharp-kernel-attempt-03-series-03", 113, "completed"),
        AnnexIdentity("bifrost-go-kernel", "bifrost-go-kernel-attempt-03-series-03", 114, "completed"),
        AnnexIdentity("bifrost-java-kernel", "bifrost-java-kernel-attempt-03-series-03", 115, "completed"),
        AnnexIdentity("bifrost-java-modeling", "bifrost-java-modeling-attempt-03-series-03", 116, "completed"),
        AnnexIdentity("bifrost-java-native", "bifrost-java-native-attempt-03-series-03", 117, "completed"),
        AnnexIdentity("bifrost-javascript-kernel", "bifrost-javascript-kernel-attempt-03-series-03", 118, "completed"),
        AnnexIdentity("bifrost-javascript-modeling", "bifrost-javascript-modeling-attempt-03-series-03", 119, "completed"),
        AnnexIdentity("bifrost-javascript-native", "bifrost-javascript-native-attempt-03-series-03", 120, "completed"),
        AnnexIdentity("bifrost-kotlin-kernel", "bifrost-kotlin-kernel-attempt-03-series-03", 121, "completed"),
        AnnexIdentity("bifrost-php-kernel", "bifrost-php-kernel-attempt-03-series-03", 122, "completed"),
        AnnexIdentity("bifrost-python-kernel", "bifrost-python-kernel-attempt-03-series-03", 123, "completed"),
        AnnexIdentity("bifrost-python-modeling", "bifrost-python-modeling-attempt-03-series-03", 124, "completed"),
        AnnexIdentity("bifrost-python-native", "bifrost-python-native-attempt-03-series-03", 125, "completed"),
        AnnexIdentity("bifrost-ruby-kernel", "bifrost-ruby-kernel-attempt-03-series-03", 126, "completed"),
        AnnexIdentity("bifrost-rust-kernel", "bifrost-rust-kernel-attempt-03-series-03", 127, "completed"),
        AnnexIdentity("bifrost-scala-kernel", "bifrost-scala-kernel-attempt-03-series-03", 128, "recorder-error"),
        AnnexIdentity("bifrost-smoke", "bifrost-smoke-attempt-04-series-03", 129, "recorder-error"),
        AnnexIdentity("bifrost-smoke", "bifrost-smoke-attempt-05-series-03", 130, "completed"),
        AnnexIdentity("bifrost-typescript-kernel", "bifrost-typescript-kernel-attempt-03-series-03", 131, "completed"),
    ),
)


class HistoryProviderError(ValueError):
    """A pinned current-history or caller-bound source identity check failed."""


def _require(condition: Any, message: str) -> None:
    if not condition:
        raise HistoryProviderError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HistoryProviderError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HistoryProviderError(f"invalid JSON in {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _safe_relative(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value,
             f"{label} must be a safe relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and path.as_posix() == value
             and not any(part in {"", ".", ".."} for part in path.parts),
             f"{label} is not canonical relative path")
    return value


def _read_stable(root: Path, relative: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    relative = _safe_relative(relative, "artifact path")
    _require(root.is_absolute(), "absolute repository root required")
    path = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    for part in (None, *PurePosixPath(relative).parts):
        if part is not None:
            current /= part
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise HistoryProviderError(f"cannot inspect {current}: {exc}") from exc
        _require(not stat.S_ISLNK(info.st_mode), f"symlinked path is forbidden: {current}")
        if current != path:
            _require(stat.S_ISDIR(info.st_mode), f"non-directory path component: {current}")
    before = os.lstat(path)
    _require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum,
             f"file kind or size is invalid: {relative}")
    raw = path.read_bytes()
    after = os.lstat(path)
    signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
    _require(signature(before) == signature(after), f"file changed while being read: {relative}")
    _require(not path.is_symlink(), f"path changed to symlink while being read: {relative}")
    return raw


def _read_ref(root: Path, path: str, digest: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    _require(HEX64.fullmatch(digest) is not None, "invalid pinned digest")
    raw = _read_stable(root, path, maximum=maximum)
    _require(_sha(raw) == digest, f"SHA-256 mismatch: {path}")
    return raw


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} fields differ")


def _exact_ref(value: Any, path: str, digest: str, label: str) -> None:
    _require(value == {"path": path, "sha256": digest}, f"{label} reference differs")


def _parse_jsonl(raw: bytes, label: str) -> tuple[list[bytes], list[dict[str, Any]]]:
    _require(raw.endswith(b"\n"), f"{label} lacks final newline")
    lines = raw.splitlines(keepends=True)
    _require(all(line.strip() for line in lines), f"{label} has a blank line")
    rows = [_json(line, f"{label} line {index}") for index, line in enumerate(lines, 1)]
    return lines, rows


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(collections.Counter(row.get("status") for row in rows).items()))


def _validate_rows(raw: bytes, pins: Pins) -> tuple[list[bytes], list[dict[str, Any]]]:
    lines, rows = _parse_jsonl(raw, "current ledger")
    _require(len(rows) == pins.row_count, "current ledger row count differs")
    _require(len(lines) == pins.row_count, "current ledger line count differs")

    identifiers: set[str] = set()
    for row in rows:
        _require(isinstance(row.get("group_id"), str) and row["group_id"], "ledger group_id missing")
        attempt_id = row.get("attempt_id")
        _require(isinstance(attempt_id, str) and attempt_id, "ledger attempt_id missing")
        _require(attempt_id not in identifiers, f"duplicate ledger attempt_id: {attempt_id}")
        identifiers.add(attempt_id)
        _require(row.get("status") in {"completed", "failed", "recorder-error"},
                 f"unknown ledger status for {attempt_id}")
    _require(_status_counts(rows) == dict(sorted(pins.total_status_counts.items())),
             "current ledger status counts differ")

    prefix = rows[:pins.prefix_rows]
    suffix = rows[pins.prefix_rows:]
    _require(len(prefix) == pins.prefix_rows, "sealed109 prefix row count differs")
    _require(_status_counts(prefix) == dict(sorted(pins.prefix_status_counts.items())),
             "sealed109 status counts differ")
    _require(_status_counts(suffix) == dict(sorted(pins.suffix_status_counts.items())),
             "C5 annex status counts differ")
    _require(_sha(b"".join(lines[:pins.prefix_rows])) == pins.prefix_raw_sha256,
             "sealed109 raw prefix SHA differs")
    _require(_sha(b"".join(lines[pins.prefix_rows:])) == pins.suffix_raw_sha256,
             "C5 annex raw suffix SHA differs")
    _require(len(suffix) == len(pins.suffix_identities), "C5 annex identity count differs")

    for index, (row, expected) in enumerate(zip(suffix, pins.suffix_identities), 1):
        _require(row.get("group_id") == expected.group_id
                 and row.get("attempt_id") == expected.attempt_id
                 and row.get("global_attempt_number") == expected.global_attempt_number
                 and row.get("status") == expected.status,
                 f"C5 annex identity differs at suffix row {index}")
        _require(row.get("source_commit") == pins.suffix_source_commit,
                 f"C5 source commit differs at suffix row {index}")
        _require(row.get("plan_commit") == pins.suffix_plan_commit,
                 f"C5 plan commit differs at suffix row {index}")
        _require(row.get("contract_sha256") == pins.suffix_contract_sha256,
                 f"C5 contract differs at suffix row {index}")
    return lines, rows


def _read_manifest(root: Path, path: str, digest: str) -> tuple[dict[str, Any], bytes]:
    raw = _read_ref(root, path, digest)
    manifest = _json(raw, path)
    _exact_keys(
        manifest,
        {"archive_path", "committed_prefix", "compressed", "line_count", "line_sha256",
         "schema", "source_path", "uncompressed"},
        path,
    )
    _require(manifest["schema"] == LEDGER_MANIFEST_SCHEMA, f"{path} schema differs")
    return manifest, raw


def _validate_manifest_shape(
    manifest: dict[str, Any],
    *,
    source_path: str,
    archive_path: str,
    rows: int,
    raw_sha256: str,
    raw_bytes: int,
    archive_sha256: str,
    archive_bytes: int,
) -> None:
    _require(manifest["source_path"] == source_path, "ledger manifest source path differs")
    _require(manifest["archive_path"] == PurePosixPath(archive_path).name,
             "ledger manifest archive name differs")
    _require(manifest["line_count"] == rows, "ledger manifest row count differs")
    _require(isinstance(manifest["line_sha256"], list)
             and len(manifest["line_sha256"]) == rows
             and all(isinstance(item, str) and HEX64.fullmatch(item) for item in manifest["line_sha256"]),
             "ledger manifest line hashes differ")
    _exact_keys(manifest["uncompressed"], {"bytes", "sha256"}, "manifest uncompressed")
    _exact_keys(manifest["compressed"], {"bytes", "sha256"}, "manifest compressed")
    _exact_keys(manifest["committed_prefix"],
                {"bytes", "git_blob_sha1", "line_count", "sha256"},
                "manifest committed_prefix")
    _require(isinstance(manifest["committed_prefix"]["git_blob_sha1"], str)
             and re.fullmatch(r"[0-9a-f]{40}", manifest["committed_prefix"]["git_blob_sha1"]),
             "manifest committed-prefix blob identity differs")
    _require(isinstance(manifest["committed_prefix"]["sha256"], str)
             and HEX64.fullmatch(manifest["committed_prefix"]["sha256"]) is not None,
             "manifest committed-prefix digest differs")
    _require(type(manifest["committed_prefix"]["bytes"]) is int
             and type(manifest["committed_prefix"]["line_count"]) is int,
             "manifest committed-prefix counters differ")
    _require(manifest["uncompressed"] == {"bytes": raw_bytes, "sha256": raw_sha256},
             "ledger manifest raw identity differs")
    _require(manifest["compressed"] == {"bytes": archive_bytes, "sha256": archive_sha256},
             "ledger manifest archive identity differs")


def _validate_archive_transition(root: Path, pins: Pins) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Verify the pinned130 receipt and109 predecessor without consulting latest index."""
    current_manifest, _ = _read_manifest(root, pins.manifest_path, pins.manifest_sha256)
    _validate_manifest_shape(
        current_manifest,
        source_path=pins.live_ledger_path,
        archive_path=pins.archive_path,
        rows=pins.row_count,
        raw_sha256=pins.raw_sha256,
        raw_bytes=pins.raw_bytes,
        archive_sha256=pins.archive_sha256,
        archive_bytes=pins.archive_bytes,
    )

    previous_manifest, _ = _read_manifest(
        root, pins.previous_manifest_path, pins.previous_manifest_sha256
    )
    _validate_manifest_shape(
        previous_manifest,
        source_path=pins.live_ledger_path,
        archive_path=pins.previous_archive_path,
        rows=pins.prefix_rows,
        raw_sha256=pins.prefix_raw_sha256,
        raw_bytes=pins.previous_raw_bytes,
        archive_sha256=pins.previous_archive_sha256,
        archive_bytes=pins.previous_archive_bytes,
    )
    _require(current_manifest["committed_prefix"] == previous_manifest["committed_prefix"],
             "committed historical ledger prefix differs between manifests")

    transition = _json(
        _read_ref(root, pins.transition_path, pins.transition_sha256), pins.transition_path
    )
    _exact_keys(
        transition,
        {"schema", "observed_utc", "previous_index_sha256", "previous_index",
         "new_index_sha256", "new_index", "new_manifest_line_count", "new_ledger_sha256",
         "root_decompression_equals_original_bytes", "original109prefix_sha256",
         "previous_archive_preserved", "no_measurement_reclassification"},
        "ledger index transition",
    )
    _require(transition["schema"] == TRANSITION_SCHEMA, "ledger transition schema differs")
    _require(transition["previous_index_sha256"] == pins.previous_index_sha256,
             "previous ledger index SHA differs")
    previous_index = transition["previous_index"]
    _exact_keys(previous_index, {"schema", "manifest"}, "previous ledger index")
    _require(previous_index["schema"] == PREVIOUS_INDEX_SCHEMA, "previous ledger index schema differs")
    _exact_ref(previous_index["manifest"], pins.previous_manifest_path,
                pins.previous_manifest_sha256, "previous ledger manifest")
    expected_new_index = {
        "schema": LEDGER_INDEX_SCHEMA,
        "manifest": {"path": pins.manifest_path, "sha256": pins.manifest_sha256},
    }
    _require(transition["new_index"] == expected_new_index,
             "ledger transition new index reference differs")
    _require(transition["new_index_sha256"] == pins.index_sha256,
             "ledger transition new index SHA differs")
    _require(transition["new_manifest_line_count"] == pins.row_count,
             "ledger transition line count differs")
    _require(transition["new_ledger_sha256"] == pins.raw_sha256,
             "ledger transition current ledger SHA differs")
    _require(transition["root_decompression_equals_original_bytes"] is True,
             "ledger transition lacks byte-preserving decompression proof")
    _require(transition["original109prefix_sha256"] == pins.prefix_raw_sha256,
             "ledger transition sealed109 prefix differs")
    _require(transition["previous_archive_preserved"] is True,
             "ledger transition does not preserve the prior archive")
    _require(transition["no_measurement_reclassification"] is True,
             "ledger transition records a measurement reclassification")
    return current_manifest, previous_manifest, transition


def _validate_index_and_transition(root: Path, pins: Pins) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    index_raw = _read_ref(root, pins.index_path, pins.index_sha256)
    index = _json(index_raw, pins.index_path)
    _exact_keys(index, {"schema", "manifest"}, "ledger index")
    _require(index["schema"] == LEDGER_INDEX_SCHEMA, "ledger index schema differs")
    _exact_ref(index["manifest"], pins.manifest_path, pins.manifest_sha256, "ledger index manifest")
    current_manifest, previous_manifest, transition = _validate_archive_transition(root, pins)
    _require(transition["new_index"] == index, "ledger transition new index differs")
    _require(transition["new_index_sha256"] == _sha(index_raw), "ledger transition index bytes differ")
    return index, current_manifest, previous_manifest


def _read_archive(root: Path, path: str, digest: str, expected_bytes: int,
                  raw_sha: str, raw_bytes: int) -> bytes:
    compressed = _read_ref(root, path, digest, maximum=MAX_FILE_BYTES)
    _require(len(compressed) == expected_bytes, f"compressed byte count differs: {path}")
    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise HistoryProviderError(f"invalid gzip archive {path}: {exc}") from exc
    _require(len(raw) == raw_bytes and _sha(raw) == raw_sha,
             f"decompressed ledger identity differs: {path}")
    return raw


def _validate_line_hashes(lines: list[bytes], manifest: dict[str, Any], label: str) -> None:
    actual = [_sha(line) for line in lines]
    _require(actual == manifest["line_sha256"], f"{label} line hash list differs")


def _validate_archive_only_130(root: Path, pins: Pins = PRODUCTION_PINS) -> dict[str, Any]:
    """Verify the sealed130 archive transition without reading latest index/live ledger."""
    _require(root.is_absolute(), "absolute repository root required")
    manifest, previous_manifest, _ = _validate_archive_transition(root, pins)
    previous_raw = _read_archive(
        root, pins.previous_archive_path, pins.previous_archive_sha256,
        pins.previous_archive_bytes, pins.prefix_raw_sha256,
        pins.previous_raw_bytes,
    )
    current_raw = _read_archive(
        root, pins.archive_path, pins.archive_sha256, pins.archive_bytes,
        pins.raw_sha256, pins.raw_bytes,
    )
    previous_lines, previous_rows = _validate_rows(previous_raw, _prefix_validation_pins(pins))
    current_lines, current_rows = _validate_rows(current_raw, pins)
    _validate_line_hashes(previous_lines, previous_manifest, "sealed109 archive")
    _validate_line_hashes(current_lines, manifest, "current130 archive")
    _require(current_lines[:pins.prefix_rows] == previous_lines,
             "current130 archive rewrites the exact sealed109 prefix")
    _require(len(previous_rows) == pins.prefix_rows, "sealed109 row count differs")
    return {
        "index": {"path": pins.index_path, "sha256": pins.index_sha256,
                  "verification": "pinned-by-130-transition-receipt; latest index not read"},
        "manifest": {"path": pins.manifest_path, "sha256": pins.manifest_sha256},
        "archive": {"path": pins.archive_path, "sha256": pins.archive_sha256,
                    "bytes": pins.archive_bytes},
        "raw_sha256": pins.raw_sha256,
        "raw_bytes": pins.raw_bytes,
        "row_count": pins.row_count,
        "status_counts": _status_counts(current_rows),
        "sealed109_rows": previous_rows,
        "annex21_rows": current_rows[pins.prefix_rows:],
        "rows": current_rows,
        "prefix_sha256": pins.prefix_raw_sha256,
        "suffix_sha256": pins.suffix_raw_sha256,
    }


def _validate_current_130(root: Path, pins: Pins = PRODUCTION_PINS) -> dict[str, Any]:
    """Verify the exact index/archive/live-ledger chain; private for test pins."""
    _require(root.is_absolute(), "absolute repository root required")
    _, manifest, previous_manifest = _validate_index_and_transition(root, pins)
    previous_raw = _read_archive(
        root, pins.previous_archive_path, pins.previous_archive_sha256,
        pins.previous_archive_bytes, pins.prefix_raw_sha256,
        pins.previous_raw_bytes,
    )
    current_raw = _read_archive(
        root, pins.archive_path, pins.archive_sha256, pins.archive_bytes,
        pins.raw_sha256, pins.raw_bytes,
    )
    previous_lines, previous_rows = _validate_rows(previous_raw, _prefix_validation_pins(pins))
    current_lines, current_rows = _validate_rows(current_raw, pins)
    _validate_line_hashes(previous_lines, previous_manifest, "sealed109 archive")
    _validate_line_hashes(current_lines, manifest, "current130 archive")
    _require(current_lines[:pins.prefix_rows] == previous_lines,
             "current130 archive rewrites the exact sealed109 prefix")

    live_raw = _read_stable(root, pins.live_ledger_path)
    _require(live_raw == current_raw, "live ledger differs from exact archived130 snapshot")
    _require(len(previous_rows) == pins.prefix_rows, "sealed109 row count differs")
    return {
        "index": {"path": pins.index_path, "sha256": pins.index_sha256},
        "manifest": {"path": pins.manifest_path, "sha256": pins.manifest_sha256},
        "archive": {"path": pins.archive_path, "sha256": pins.archive_sha256,
                    "bytes": pins.archive_bytes},
        "raw_sha256": pins.raw_sha256,
        "raw_bytes": pins.raw_bytes,
        "row_count": pins.row_count,
        "status_counts": _status_counts(current_rows),
        "sealed109_rows": previous_rows,
        "annex21_rows": current_rows[pins.prefix_rows:],
        "rows": current_rows,
        "prefix_sha256": pins.prefix_raw_sha256,
        "suffix_sha256": pins.suffix_raw_sha256,
    }


def _validate_current_source_identity(
    expected_head: str, expected_tree: str, actual_head: str, actual_tree: str
) -> None:
    """Compare live Git identity to explicit values supplied by a caller-bound core."""
    for label, value in (("expected HEAD", expected_head), ("expected tree", expected_tree),
                         ("observed HEAD", actual_head), ("observed tree", actual_tree)):
        _require(isinstance(value, str) and HEX40.fullmatch(value) is not None,
                 f"{label} must be a full lowercase SHA-1")
    _require(actual_head == expected_head, "current HEAD differs from caller-bound source commit")
    _require(actual_tree == expected_tree, "current tree differs from caller-bound source tree")


def _observe_git_source(root: Path) -> tuple[str, str]:
    """Read attached checkout identity without fetching or changing Git state."""
    _require(root.is_absolute(), "absolute repository root required")
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_CONFIG_") or key in {
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_PREFIX",
        }:
            env.pop(key, None)
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    values: list[str] = []
    for revision in ("HEAD^{commit}", "HEAD^{tree}"):
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", revision],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        _require(result.returncode == 0, f"cannot read current Git {revision}")
        try:
            value = result.stdout.decode("ascii", "strict").strip()
        except UnicodeDecodeError as exc:
            raise HistoryProviderError("Git source identity is not ASCII") from exc
        _require(HEX40.fullmatch(value) is not None, f"Git returned invalid {revision}")
        values.append(value)
    return values[0], values[1]


def _validate_sealed109_history(root: Path, *, exact_live_rows: int | None = LEDGER_ROWS) -> dict[str, Any]:
    """Call the exact old reader in prefix-only mode; it grants no tail authority."""
    raw = _read_ref(root, SEALED109_READER_PATH, SEALED109_READER_SHA256)
    name = "_private_joern_history_provider_02_for_03"
    spec = importlib.util.spec_from_file_location(name, root / SEALED109_READER_PATH)
    _require(spec is not None and spec.loader is not None, "cannot load sealed109 history reader")
    module = importlib.util.module_from_spec(spec)
    try:
        exec(compile(raw, str(root / SEALED109_READER_PATH), "exec"), module.__dict__)
    except BaseException as exc:
        raise HistoryProviderError(f"sealed109 history reader failed to load: {exc}") from exc
    facts = module.validate_tail(
        root,
        {"path": SEALED109_DESCRIPTOR_PATH, "sha256": SEALED109_DESCRIPTOR_SHA256},
        live_mode="prefix-history-only",
    )
    _require(facts.get("schema") == "v092-joern05-sealed109-history-context/v1",
             "sealed109 reader output schema differs")
    _require(facts.get("execution_authorized") is False
             and facts.get("automatic_retry") is False
             and facts.get("later_rows_authorized") is False,
             "sealed109 reader returned authority")
    live_rows = facts.get("live_rows_observed")
    if exact_live_rows is None:
        _require(type(live_rows) is int and live_rows >= SEALED109_ROWS,
                 "sealed109 reader did not preserve the sealed prefix")
    else:
        _require(live_rows == exact_live_rows,
                 f"sealed109 reader did not observe the exact {exact_live_rows}-row live ledger")
    _require(facts.get("ledger_prefix", {}).get("rows") == SEALED109_ROWS
             and facts.get("ledger_prefix", {}).get("sha256") == SEALED109_RAW_SHA256,
             "sealed109 reader returned a different historical prefix")
    _require(len(facts.get("source_contexts", {})) == 9,
             "sealed historical source-context roster differs")
    return facts


def validate(
    root: Path = ROOT,
    *,
    expected_head: str,
    expected_tree: str,
) -> dict[str, Any]:
    """Verify the fixed130 snapshot and old109 lineage, without granting authority.

    ``expected_head`` and ``expected_tree`` must come from a separately
    hash-bound current core/request. This API does not create that binding.
    """
    root = Path(root)
    _require(root.resolve() == ROOT.resolve(), "production reader is pinned to its checkout root")
    actual_head, actual_tree = _observe_git_source(root)
    _validate_current_source_identity(expected_head, expected_tree, actual_head, actual_tree)
    sealed = _validate_sealed109_history(root)
    baseline = _validate_current_130(root, PRODUCTION_PINS)
    annex = baseline["annex21_rows"]
    scala = next(row for row in annex if row["group_id"] == "bifrost-scala-kernel")
    _require(scala.get("global_attempt_number") == 128
             and scala.get("status") == "recorder-error"
             and scala.get("exit_code") == 124
             and scala.get("timed_out") is True,
             "Bifrost 0.14.4 Scala partial record differs")
    return {
        "schema": "v092-joern05-current130-history-context/v1",
        "status": "source-only-current130-baseline-verified",
        "execution_authorized": False,
        "automatic_retry": False,
        "current_joern_eligibility": "not-assessed-by-this-reader",
        "current_source_identity": {"commit": actual_head, "tree": actual_tree},
        "ledger_identity": {
            "index": baseline["index"],
            "manifest": baseline["manifest"],
            "archive": baseline["archive"],
            "rows": baseline["row_count"],
            "raw_sha256": baseline["raw_sha256"],
            "raw_bytes": baseline["raw_bytes"],
            "status_counts": baseline["status_counts"],
        },
        "sealed109_lineage": {
            "descriptor": {"path": SEALED109_DESCRIPTOR_PATH,
                           "sha256": SEALED109_DESCRIPTOR_SHA256},
            "reader": {"path": SEALED109_READER_PATH,
                       "sha256": SEALED109_READER_SHA256},
            "source_contexts": sealed["source_contexts"],
            "original89_provider": sealed["original89_provider"],
            "retained20": sealed["retained20"],
            "retained_codeql": sealed["retained_codeql"],
            "consumed_events": sealed["consumed_events"],
        },
        "historical109": {
            "rows": baseline["sealed109_rows"],
            "sha256": SEALED109_RAW_SHA256,
            "status_counts": PREFIX_STATUS_COUNTS,
        },
        "bifrost0144_c5_annex21": {
            "rows": annex,
            "sha256": C5_ANNEX_SHA256,
            "global_attempt_numbers": list(range(111, 132)),
            "source_commit": C5_SOURCE_COMMIT,
            "plan_commit": C5_PLAN_COMMIT,
            "contract_sha256": C5_CONTRACT_SHA256,
        },
        "bifrost0144_scala_partial": {
            "group_id": scala["group_id"],
            "attempt_id": scala["attempt_id"],
            "global_attempt_number": scala["global_attempt_number"],
            "status": scala["status"],
            "exit_code": scala["exit_code"],
            "timed_out": scala["timed_out"],
            "source_commit": scala["source_commit"],
            "plan_commit": scala["plan_commit"],
            "contract_sha256": scala["contract_sha256"],
            "completion_claim": False,
        },
    }


def validate_archive_only_130(
    root: Path = ROOT,
    *,
    expected_head: str,
    expected_tree: str,
) -> dict[str, Any]:
    """Verify archived130 and sealed109 lineage without reading the latest index.

    This baseline-only API intentionally does not validate the current live
    ledger tail. A caller must bind HEAD/tree to a separately verified core or
    request, then independently validate any live tail against this baseline.
    """
    root = Path(root)
    _require(root.resolve() == ROOT.resolve(), "production reader is pinned to its checkout root")
    actual_head, actual_tree = _observe_git_source(root)
    _validate_current_source_identity(expected_head, expected_tree, actual_head, actual_tree)
    sealed = _validate_sealed109_history(root, exact_live_rows=None)
    baseline = _validate_archive_only_130(root, PRODUCTION_PINS)
    annex = baseline["annex21_rows"]
    scala = next(row for row in annex if row["group_id"] == "bifrost-scala-kernel")
    _require(scala.get("global_attempt_number") == 128
             and scala.get("status") == "recorder-error"
             and scala.get("exit_code") == 124
             and scala.get("timed_out") is True,
             "Bifrost 0.14.4 Scala partial record differs")
    return {
        "schema": "v092-joern05-archived130-history-context/v1",
        "status": "source-only-archived130-baseline-verified",
        "execution_authorized": False,
        "automatic_retry": False,
        "current_live_ledger_validation": "not-performed-by-this-reader",
        "current_joern_eligibility": "not-assessed-by-this-reader",
        "current_source_identity": {"commit": actual_head, "tree": actual_tree},
        "ledger_identity": {
            "index": baseline["index"],
            "manifest": baseline["manifest"],
            "archive": baseline["archive"],
            "rows": baseline["row_count"],
            "raw_sha256": baseline["raw_sha256"],
            "raw_bytes": baseline["raw_bytes"],
            "status_counts": baseline["status_counts"],
        },
        "sealed109_lineage": {
            "descriptor": {"path": SEALED109_DESCRIPTOR_PATH,
                           "sha256": SEALED109_DESCRIPTOR_SHA256},
            "reader": {"path": SEALED109_READER_PATH,
                       "sha256": SEALED109_READER_SHA256},
            "source_contexts": sealed["source_contexts"],
            "original89_provider": sealed["original89_provider"],
            "retained20": sealed["retained20"],
            "retained_codeql": sealed["retained_codeql"],
            "consumed_events": sealed["consumed_events"],
        },
        "historical109": {
            "rows": baseline["sealed109_rows"],
            "sha256": SEALED109_RAW_SHA256,
            "status_counts": PREFIX_STATUS_COUNTS,
        },
        "bifrost0144_c5_annex21": {
            "rows": annex,
            "sha256": C5_ANNEX_SHA256,
            "global_attempt_numbers": list(range(111, 132)),
            "source_commit": C5_SOURCE_COMMIT,
            "plan_commit": C5_PLAN_COMMIT,
            "contract_sha256": C5_CONTRACT_SHA256,
        },
        "bifrost0144_scala_partial": {
            "group_id": scala["group_id"],
            "attempt_id": scala["attempt_id"],
            "global_attempt_number": scala["global_attempt_number"],
            "status": scala["status"],
            "exit_code": scala["exit_code"],
            "timed_out": scala["timed_out"],
            "source_commit": scala["source_commit"],
            "plan_commit": scala["plan_commit"],
            "contract_sha256": scala["contract_sha256"],
            "completion_claim": False,
        },
    }


def _prefix_validation_pins(pins: Pins) -> Pins:
    """Describe the already-sealed prefix as a no-tail snapshot."""
    prefix_statuses = dict(pins.prefix_status_counts)
    return Pins(
        live_ledger_path=pins.live_ledger_path,
        index_path=pins.index_path,
        index_sha256=pins.index_sha256,
        manifest_path=pins.previous_manifest_path,
        manifest_sha256=pins.previous_manifest_sha256,
        archive_path=pins.previous_archive_path,
        archive_sha256=pins.previous_archive_sha256,
        archive_bytes=pins.previous_archive_bytes,
        raw_sha256=pins.prefix_raw_sha256,
        raw_bytes=pins.previous_raw_bytes,
        row_count=pins.prefix_rows,
        transition_path=pins.transition_path,
        transition_sha256=pins.transition_sha256,
        previous_index_sha256=pins.previous_index_sha256,
        previous_manifest_path=pins.previous_manifest_path,
        previous_manifest_sha256=pins.previous_manifest_sha256,
        previous_archive_path=pins.previous_archive_path,
        previous_archive_sha256=pins.previous_archive_sha256,
        previous_archive_bytes=pins.previous_archive_bytes,
        previous_raw_bytes=pins.previous_raw_bytes,
        prefix_rows=pins.prefix_rows,
        prefix_raw_sha256=pins.prefix_raw_sha256,
        suffix_raw_sha256=_sha(b""),
        prefix_status_counts=prefix_statuses,
        suffix_status_counts={},
        total_status_counts=prefix_statuses,
        suffix_source_commit=pins.suffix_source_commit,
        suffix_plan_commit=pins.suffix_plan_commit,
        suffix_contract_sha256=pins.suffix_contract_sha256,
        suffix_identities=(),
    )
