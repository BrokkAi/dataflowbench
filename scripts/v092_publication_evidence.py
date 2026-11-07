#!/usr/bin/env python3
"""Prepare, verify, hydrate, and stage the pinned v0.9.2 publication evidence.

This maps the already selected and canonically validated reports into a
portable publication scope. It does not run analyzers, infer qualification,
or create scorecards. The raw capture bundle is verified through the existing
``evidence_bundle`` implementation before any hydration copy is made.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

import evidence_bundle


SCHEMA = "dataflowbench-v0.9.2-publication-evidence/v1"
QUALIFICATION_SCHEMA = "dataflowbench-v0.9.2-publication-qualification-boundary/v1"
PUBLICATION_SCOPE = "reports/releases/v0.9.2/publication-v1"
CAPTURE_SCOPE = PUBLICATION_SCOPE + "/capture"
SELECTION_PATH = (
    "reports/releases/v0.9.2/review-handoff/"
    "bifrost-v0151-final-review-20261107-01/"
    "publication-selection-with-canonical-validation.json"
)
SELECTION_SHA256 = "2f3ceb7d1da3b4402cfcab83a59eba6f3d28341ae4433490cab908aba70a2e9d"
SOURCE_SELECTOR_PATH = "reports/releases/v0.9.2/validation/bifrost-v0151-terminal-01/publication-selection.json"
SOURCE_SELECTOR_SHA256 = "f12336ab245b4bc7b4ef31eca16f9f1c331310a2a3ee0f478b112fc09339faea"
CANONICAL_RECEIPT_PATH = "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-04/receipt.json"
CANONICAL_RECEIPT_SHA256 = "694b25c5c62cbed78adb267c1f39478ec5febe1c845487a333afb2c5f4f85366"
JOERN_SIDECAR_PATH = (
    "execution-state/v092/publication-evidence/joern108-canonical-schema-01/"
    "projection-03/sidecars/aggregate-metadata-lift.json"
)
JOERN_SIDECAR_SHA256 = "42f4ea66b124357bd341e8d543ecb41d2fdb61116c1a5c5149c65dd5005416cd"
SCHEMA_PATH = "schemas/result.schema.json"
SCHEMA_SHA256 = "d8fa8aeb9c17a792e858b5168a318794079ff1ae65404699cd96ee886d302217"
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
LEDGER_SHA256 = "5528a3ff7683546a09c03d5791b5283bba3e08428c9380890e3e4cfe5d268679"
LEDGER_PREFIX_130_SHA256 = "79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84"
LEDGER_PREFIX_131_SHA256 = "2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199"
BUNDLE_PATH = "evidence-delivery/v0.9.2-publication-01/detail"
EXPECTED_COUNTS = {
    "groups": 84,
    "reports": 92,
    "rows": 4252,
    "unique_case_ids": 1108,
    "raw_files": 4252,
    "selected_source_reports": 5,
}
EXPECTED_JOERN_OUTCOMES = {"inconclusive": 96, "unsupported": 12}
MAX_REPORT_BYTES = 256 * 1024 * 1024
BLOCK = 1024 * 1024


class PublicationEvidenceError(ValueError):
    pass


def _require(value: object, message: str) -> None:
    if not value:
        raise PublicationEvidenceError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        _require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> object:
    raise PublicationEvidenceError(f"invalid JSON constant: {value}")


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=_strict_object,
                           parse_constant=_reject_json_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationEvidenceError(f"invalid {label} JSON: {exc}") from exc
    _require(type(value) is dict, f"{label} must be a JSON object")
    return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False) + "\n").encode("utf-8")


def _same_json_object(actual: object, expected: object) -> bool:
    """Compare JSON objects while distinguishing booleans from integers."""
    return _json_bytes(actual) == _json_bytes(expected)


def _object_sha(value: object) -> str:
    return _sha(_json_bytes(value).rstrip(b"\n"))


def _safe_relative(value: object, label: str) -> str:
    try:
        return evidence_bundle.safe_path(value).as_posix()
    except (TypeError, ValueError) as exc:
        raise PublicationEvidenceError(f"{label} is not a safe relative path") from exc


def _assert_no_symlinks(path: Path) -> None:
    try:
        evidence_bundle._assert_no_symlink_components(path)
    except (OSError, ValueError) as exc:
        raise PublicationEvidenceError(f"symlink or unsafe path refused: {path}") from exc


def _root(path: os.PathLike[str] | str) -> Path:
    candidate = Path(os.path.abspath(os.fspath(path)))
    _assert_no_symlinks(candidate)
    _require(candidate.is_dir(), f"repository root is not a directory: {candidate}")
    return candidate.resolve(strict=True)


def _join(root: Path, relative: object, label: str, *, exists: bool) -> Path:
    rel = _safe_relative(relative, label)
    path = root.joinpath(*PurePosixPath(rel).parts)
    _assert_no_symlinks(path)
    try:
        resolved = path.resolve(strict=exists)
    except OSError as exc:
        raise PublicationEvidenceError(f"cannot resolve {label}: {rel}") from exc
    _require(resolved.is_relative_to(root.resolve(strict=True)),
             f"{label} escapes repository root: {rel}")
    return path


def _sig(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _open_regular(path: Path, label: str):
    _assert_no_symlinks(path)
    try:
        before = path.lstat()
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_REPORT_BYTES,
                 f"{label} is not a bounded regular file")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        opened = os.fstat(fd)
        _require(stat.S_ISREG(opened.st_mode) and _sig(before) == _sig(opened),
                 f"{label} changed before open")
        return os.fdopen(fd, "rb"), before
    except (OSError, ValueError) as exc:
        if isinstance(exc, PublicationEvidenceError):
            raise
        raise PublicationEvidenceError(f"cannot open {label}: {path}") from exc


def _read_file(root: Path, relative: object, *, expected_sha256: str | None = None,
               label: str = "file") -> bytes:
    path = _join(root, relative, label, exists=True)
    stream, before = _open_regular(path, label)
    try:
        raw = stream.read(MAX_REPORT_BYTES + 1)
        after = os.fstat(stream.fileno())
    finally:
        stream.close()
    _require(len(raw) <= MAX_REPORT_BYTES and _sig(before) == _sig(after) and
             _sig(path.lstat()) == _sig(after), f"{label} changed while being read")
    actual = _sha(raw)
    if expected_sha256 is not None:
        _require(actual == expected_sha256, f"{label} SHA-256 differs")
    return raw


def _file_digest(path: Path) -> tuple[str, int]:
    stream, before = _open_regular(path, "file")
    h = hashlib.sha256()
    size = 0
    try:
        for block in iter(lambda: stream.read(BLOCK), b""):
            h.update(block)
            size += len(block)
        after = os.fstat(stream.fileno())
    finally:
        stream.close()
    _require(_sig(before) == _sig(after) and _sig(path.lstat()) == _sig(after),
             f"file changed while hashing: {path}")
    return h.hexdigest(), size


def _copy_file(source: Path, destination: Path, *, expected_sha256: str | None = None,
               expected_bytes: int | None = None, allow_identical: bool = False) -> tuple[str, int]:
    """Copy one regular file without following links or replacing a destination."""
    source_stream, source_before = _open_regular(source, "copy source")
    _assert_no_symlinks(destination.parent)
    if os.path.lexists(destination):
        _require(allow_identical, f"destination already exists: {destination}")
        actual_sha, actual_bytes = _file_digest(destination)
        _require((expected_sha256 is None or actual_sha == expected_sha256) and
                 (expected_bytes is None or actual_bytes == expected_bytes),
                 f"existing destination differs: {destination}")
        source_stream.close()
        return actual_sha, actual_bytes

    destination.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(destination.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(destination, flags, 0o644)
    h = hashlib.sha256()
    count = 0
    try:
        with os.fdopen(fd, "wb") as output:
            for block in iter(lambda: source_stream.read(BLOCK), b""):
                output.write(block)
                h.update(block)
                count += len(block)
            output.flush()
        source_after = os.fstat(source_stream.fileno())
        _require(_sig(source_before) == _sig(source_after) and
                 _sig(source.lstat()) == _sig(source_after),
                 "copy source changed while being copied")
        actual_sha = h.hexdigest()
        _require(expected_sha256 is None or actual_sha == expected_sha256,
                 "copied file SHA-256 differs")
        _require(expected_bytes is None or count == expected_bytes,
                 "copied file byte count differs")
        return actual_sha, count
    except BaseException:
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        source_stream.close()


def _write_new(destination: Path, raw: bytes) -> tuple[str, int]:
    _assert_no_symlinks(destination.parent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(destination.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(destination, flags, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
    except OSError as exc:
        raise PublicationEvidenceError(f"cannot create new publication file: {destination}") from exc
    return _sha(raw), len(raw)


def _write_json(destination: Path, value: object) -> tuple[str, int]:
    return _write_new(destination, json.dumps(value, sort_keys=True, indent=2,
                                              ensure_ascii=False).encode("utf-8") + b"\n")


def _sha_file_ref(root: Path, path: str, expected: str, label: str) -> tuple[bytes, dict[str, Any]]:
    raw = _read_file(root, path, expected_sha256=expected, label=label)
    return raw, {"path": path, "sha256": expected, "bytes": len(raw)}


def _hash_ledger(root: Path, selector: dict[str, Any]) -> dict[str, Any]:
    ledger = selector.get("ledger")
    _require(type(ledger) is dict and ledger.get("path") == LEDGER_PATH and
             ledger.get("sha256") == LEDGER_SHA256 and ledger.get("line_count") == 151 and
             ledger.get("bytes") == 130404899 and
             ledger.get("prefix_130") == LEDGER_PREFIX_130_SHA256 and
             ledger.get("prefix_131") == LEDGER_PREFIX_131_SHA256,
             "publication source selector ledger binding differs")
    path = _join(root, LEDGER_PATH, "source ledger", exists=True)
    stream, before = _open_regular(path, "source ledger")
    whole = hashlib.sha256()
    prefix130, prefix131 = hashlib.sha256(), hashlib.sha256()
    total = lines = 0
    try:
        for line in stream:
            whole.update(line)
            total += len(line)
            lines += 1
            if lines <= 130:
                prefix130.update(line)
            if lines <= 131:
                prefix131.update(line)
        after = os.fstat(stream.fileno())
    finally:
        stream.close()
    _require(_sig(before) == _sig(after) and _sig(path.lstat()) == _sig(after) and
             total == ledger["bytes"] and lines == ledger["line_count"] and
             whole.hexdigest() == ledger["sha256"] and
             prefix130.hexdigest() == ledger["prefix_130"] and
             prefix131.hexdigest() == ledger["prefix_131"],
             "source ledger bytes or preserved prefixes differ")
    return {"path": LEDGER_PATH, "sha256": whole.hexdigest(), "bytes": total,
            "line_count": lines, "prefix_130_sha256": prefix130.hexdigest(),
            "prefix_131_sha256": prefix131.hexdigest()}


def _source_ref(root: Path, value: object, label: str) -> tuple[dict[str, Any], bytes]:
    _require(type(value) is dict and isinstance(value.get("path"), str) and
             isinstance(value.get("sha256"), str), f"{label} reference is malformed")
    path = _safe_relative(value["path"], f"{label} path")
    digest = value["sha256"]
    _require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
             f"{label} digest is malformed")
    raw = _read_file(root, path, expected_sha256=digest, label=label)
    return {"path": path, "sha256": digest, "bytes": len(raw)}, raw


def _metadata_lift(selected: dict[str, Any], canonical: dict[str, Any],
                   lift_entry: dict[str, Any], label: str) -> None:
    source_obj_sha = lift_entry.get("source_report_object_sha256")
    canonical_obj_sha = lift_entry.get("canonical_report_object_sha256")
    _require(_object_sha(selected) == source_obj_sha and
             _object_sha(canonical) == canonical_obj_sha and
             lift_entry.get("source_report_path") == label,
             "Joern metadata lift object or source path binding differs")
    metadata = lift_entry.get("metadata_lift")
    _require(type(metadata) is dict and
             metadata.get("source_report_object_sha256") == source_obj_sha and
             metadata.get("canonical_report_object_sha256") == canonical_obj_sha,
             "Joern metadata lift inner object binding differs")
    qualification = metadata.get("qualification")
    exact_qualification = {
        "aggregate_resource_qualification": "unavailable",
        "evidence_scope": "semantic-only",
        "scored_activation": False,
        "scoring_permitted": False,
        "semantic_qualification": "unavailable",
        "timing_certified": False,
    }
    _require(qualification == exact_qualification and
             metadata.get("removed_top_level") == {
                 "aggregate_resource_qualification": "unavailable",
                 "scored_activation": False,
             } and metadata.get("schema") == "v092-joern-schema-metadata-lift/v1",
             "Joern metadata lift qualification boundary differs")
    rows = selected.get("results")
    canonical_rows = canonical.get("results")
    removed = metadata.get("removed_result_metadata")
    _require(type(rows) is list and type(canonical_rows) is list and
             type(removed) is list and len(rows) == len(canonical_rows) == len(removed),
             "Joern metadata lift row count differs")
    restored = copy.deepcopy(selected)
    _require(restored.pop("aggregate_resource_qualification", None) == "unavailable" and
             restored.pop("scored_activation", None) is False,
             "Joern original top-level qualification values differ")
    seen: set[tuple[int, str]] = set()
    for ordinal, (row, canonical_row, lift_row) in enumerate(zip(rows, canonical_rows, removed)):
        _require(type(row) is dict and type(canonical_row) is dict and type(lift_row) is dict and
                 lift_row == {"case_id": row.get("case_id"), "ordinal": ordinal,
                              "raw_output": row.get("raw_output"),
                              "raw_sha256": row.get("raw_sha256")},
                 "Joern removed raw metadata mapping differs")
        _require("raw_sha256" in row and "raw_sha256" not in canonical_row and
                 type(row["raw_sha256"]) is str and len(row["raw_sha256"]) == 64,
                 "Joern raw SHA field is missing or present in canonical report")
        restored["results"][ordinal].pop("raw_sha256", None)
        _require(restored["results"][ordinal] == canonical_row,
                 "Joern source and canonical row differ beyond the approved raw SHA lift")
        case_key = (ordinal, row.get("case_id"))
        _require(case_key not in seen, "duplicate Joern lift row")
        seen.add(case_key)
    _require(restored == canonical, "Joern canonical report differs beyond the exact three-field lift")


def _preflight(source_root: Path) -> dict[str, Any]:
    selection_raw, selection_ref = _sha_file_ref(
        source_root, SELECTION_PATH, SELECTION_SHA256, "publication selection overlay")
    selection = _json(selection_raw, "publication selection overlay")
    _require(selection.get("schema") == "v092-final-review-selection-with-canonical-validation/v1" and
             selection.get("status") == "selection-and-canonical-report-validation-verified" and
             selection.get("partitions") == 92 and selection.get("rows") == 4252 and
             selection.get("distinct_case_ids") == 1108 and
             selection.get("freeze_created") is False and
             selection.get("full_release_gate_satisfied") is False and
             selection.get("publication_approved") is False and
             selection.get("scoring_enabled") is False and
             selection.get("scorecard_generation_allowed") is False,
             "final review selection does not preserve the exact validation-only boundary")

    source_selector_ref, source_selector_raw = _source_ref(
        source_root, selection.get("source_selector"), "source selector")
    _require(source_selector_ref == {"path": SOURCE_SELECTOR_PATH,
                                    "sha256": SOURCE_SELECTOR_SHA256,
                                    "bytes": source_selector_ref["bytes"]},
             "source selector ref differs from its fixed identity")
    selector = _json(source_selector_raw, "source selector")
    _require(selector.get("schema") == "dataflowbench-v0.9.2-publication-evidence-selection/v1" and
             selector.get("status") == "fresh-evidence-verified" and
             selector.get("fresh_groups") == 84 and selector.get("fresh_partitions") == 92 and
             selector.get("fresh_rows") == 4252 and selector.get("case_count") == 1108 and
             selector.get("carried_partitions") == 0 and selector.get("carried_rows") == 0 and
             selector.get("publication_approved") is False and
             selector.get("full_release_gate_satisfied") is False and
             selector.get("freeze_created") is False and selector.get("scoring_enabled") is False and
             selector.get("scorecard_generation_allowed") is False and
             selector.get("bifrost_v0151_reconciliation", {}).get("full_policy_qualification") is False and
             selector.get("typed_outcomes", {}).get("joern_swift_common108") == EXPECTED_JOERN_OUTCOMES,
             "source selector counts or qualification boundary differ")
    ledger = _hash_ledger(source_root, selector)

    receipt_ref, canonical_raw = _source_ref(
        source_root, selection.get("canonical_validation"), "canonical validation receipt")
    _require(receipt_ref["path"] == CANONICAL_RECEIPT_PATH and
             receipt_ref["sha256"] == CANONICAL_RECEIPT_SHA256,
             "canonical validation receipt ref differs from the reviewed run")
    receipt = _json(canonical_raw, "canonical validation receipt")
    _require(receipt.get("status") == "canonical-validation-passed" and
             receipt.get("exit_code") == 0 and receipt.get("timed_out") is False and
             receipt.get("invocation_matches_pinned_argv_cwd_environment") is True and
             receipt.get("metrics") == {"checked_configuration_hashes": 76,
                                        "known_stale": 0,
                                        "not_derivable": 16,
                                        "validated_reports": 92} and
             receipt.get("validation_gate", {}).get("passed") is True and
             receipt.get("validation_gate", {}).get("required_known_stale") == 0,
             "canonical validation receipt did not pass the fixed 92/0 gate")
    _require(selection.get("canonical_validation", {}).get("path") == CANONICAL_RECEIPT_PATH,
             "selection points at a noncanonical validation receipt")

    joern_ref, joern_raw = _source_ref(
        source_root, selection.get("joern_sidecar"), "Joern aggregate metadata sidecar")
    _require(joern_ref["path"] == JOERN_SIDECAR_PATH and
             joern_ref["sha256"] == JOERN_SIDECAR_SHA256 and
             selection.get("joern_sidecar", {}).get("aggregate_resource_qualification") == "unavailable" and
             selection.get("joern_sidecar", {}).get("scored_activation") is False and
             selection.get("joern_sidecar", {}).get("timing_certified") is False,
             "Joern aggregate metadata sidecar identity or qualification differs")
    joern = _json(joern_raw, "Joern aggregate metadata sidecar")
    _require(joern.get("schema") == "v092-joern-schema-metadata-lift-aggregate/v1" and
             joern.get("aggregate_counts") == {
                 "cases": 108, "distinct_raw_output_paths": 108,
                 "outcomes": EXPECTED_JOERN_OUTCOMES, "reports": 5} and
             joern.get("lift_boundary", {}).get("removed_top_level_fields") == {
                 "aggregate_resource_qualification": "unavailable", "scored_activation": False} and
             joern.get("lift_boundary", {}).get("removed_result_field") == "results[*].raw_sha256" and
             joern.get("lift_boundary", {}).get("scoring_permitted") is False and
             joern.get("lift_boundary", {}).get("timing_certified") is False and
             joern.get("lift_boundary", {}).get("preserve_all_other_fields_exactly") is True,
             "Joern sidecar does not retain the exact metadata lift boundary")

    schema_raw, schema_ref = _sha_file_ref(source_root, SCHEMA_PATH, SCHEMA_SHA256,
                                           "canonical report schema")
    _require(schema_ref["sha256"] == joern.get("source_identity", {}).get("frozen_schema_bytes_sha256"),
             "Joern sidecar frozen schema digest differs")
    _require(_hash_ledger(source_root, selector) == ledger,
             "ledger changed during preflight")

    fresh_reports = selector.get("fresh_reports")
    selected_reports = selection.get("selected_reports")
    _require(type(fresh_reports) is list and len(fresh_reports) == 92 and
             type(selected_reports) is list and len(selected_reports) == 92,
             "publication selection must contain exactly 92 fresh report sources")
    fresh_by_adapter: dict[str, dict[str, Any]] = {}
    for row in fresh_reports:
        _require(type(row) is dict and isinstance(row.get("adapter"), str) and
                 row["adapter"] not in fresh_by_adapter,
                 "source selector report roster is malformed or repeats an adapter")
        fresh_by_adapter[row["adapter"]] = row
    lift_by_source = {entry.get("source_report_path"): entry for entry in joern.get("reports", [])
                      if isinstance(entry, dict)}
    _require(len(lift_by_source) == 5, "Joern sidecar must identify exactly five source reports")

    reports: list[dict[str, Any]] = []
    seen_adapter_ids: set[str] = set()
    seen_basenames: set[str] = set()
    seen_case_ids: set[str] = set()
    seen_raw_sources: set[str] = set()
    seen_capture_paths: set[str] = set()
    total_rows = 0
    lifted_count = 0
    for selected in selected_reports:
        _require(type(selected) is dict and
                 set(selected) == {"adapter", "attempt_id", "attempt_number",
                                   "canonical_report", "metadata_lift", "selected_original"},
                 "selected report row has an unexpected field set")
        adapter_path = _safe_relative(selected["adapter"], "adapter path")
        fresh = fresh_by_adapter.get(adapter_path)
        _require(fresh is not None and fresh.get("attempt_id") == selected["attempt_id"] and
                 fresh.get("attempt_number") == selected["attempt_number"],
                 "selected report does not match its source selector attempt")
        selected_ref, selected_raw = _source_ref(source_root, selected["selected_original"],
                                                 "selected original report")
        _require(selected_ref["path"] == fresh.get("staged_path") and
                 selected_ref["sha256"] == fresh.get("sha256"),
                 "selected original report differs from the pinned source selector")
        canonical_ref, canonical_raw = _source_ref(source_root, selected["canonical_report"],
                                                   "canonical report")
        adapter_id = PurePosixPath(adapter_path).stem
        basename = PurePosixPath(canonical_ref["path"]).name
        _require(PurePosixPath(adapter_path).name == basename and
                 PurePosixPath(selected_ref["path"]).name == basename and
                 adapter_id not in seen_adapter_ids and basename not in seen_basenames,
                 "report adapter or original basename is ambiguous")
        seen_adapter_ids.add(adapter_id)
        seen_basenames.add(basename)
        is_lifted = selected["metadata_lift"]
        _require(type(is_lifted) is bool and
                 selected_ref["path"] == fresh["staged_path"] and
                 canonical_ref["path"] == selected["canonical_report"]["path"] and
                 selected["canonical_report"].get("rows") == fresh.get("rows"),
                 "canonical report mapping differs from source selector")
        selected_obj = _json(selected_raw, "selected report")
        canonical_obj = _json(canonical_raw, "canonical report")
        rows = canonical_obj.get("results")
        _require(type(rows) is list and len(rows) == fresh.get("rows") and
                 type(selected_obj.get("results")) is list and
                 len(selected_obj["results"]) == len(rows),
                 "report result-row count differs from the frozen selector")
        if is_lifted:
            lifted_count += 1
            lift_entry = lift_by_source.get(selected_ref["path"])
            _require(lift_entry is not None and lift_entry.get("canonical_report_path") == canonical_ref["path"] and
                     lift_entry.get("source_report_bytes_sha256") == selected_ref["sha256"] and
                     lift_entry.get("canonical_report_bytes_sha256") == canonical_ref["sha256"] and
                     lift_entry.get("case_count") == len(rows),
                     "selected Joern report is not bound by the original metadata-lift sidecar")
            _metadata_lift(selected_obj, canonical_obj, lift_entry, selected_ref["path"])
        else:
            _require(selected_ref["path"] == canonical_ref["path"] and
                     selected_ref["sha256"] == canonical_ref["sha256"] and
                     selected_raw == canonical_raw and selected_obj == canonical_obj,
                     "unlifted selected and canonical report bytes differ")
        for ordinal, (selected_row, canonical_row) in enumerate(zip(selected_obj["results"], rows)):
            _require(type(canonical_row) is dict and type(selected_row) is dict and
                     selected_row.get("case_id") == canonical_row.get("case_id") and
                     selected_row.get("raw_output") == canonical_row.get("raw_output"),
                     "selected and canonical raw-row membership differs")
            case_id = canonical_row.get("case_id")
            _require(type(case_id) is str and case_id and
                     len(PurePosixPath(case_id).parts) == 1 and
                     PurePosixPath(case_id).as_posix() == case_id,
                     "report case ID is not a single safe path segment")
            seen_case_ids.add(case_id)
            source_raw = _safe_relative(canonical_row.get("raw_output"), "source raw output")
            _require(source_raw not in seen_raw_sources,
                     "two rows refer to the same raw source path")
            seen_raw_sources.add(source_raw)
            suffix = "".join(PurePosixPath(source_raw).suffixes)
            capture_path = f"{CAPTURE_SCOPE}/raw/{adapter_id}/{case_id}{suffix}"
            capture_path = _safe_relative(capture_path, "capture raw output")
            _require(capture_path not in seen_capture_paths,
                     "two rows collide at one publication raw destination")
            seen_capture_paths.add(capture_path)
        total_rows += len(rows)
        reports.append({
            "adapter": adapter_path,
            "adapter_id": adapter_id,
            "attempt_id": selected["attempt_id"],
            "attempt_number": selected["attempt_number"],
            "row_count": len(rows),
            "selected_original": selected_ref,
            "canonical_report": canonical_ref,
            "lifted_metadata": is_lifted,
            "_selected_raw": selected_raw,
            "_selected_object": selected_obj,
            "_canonical_raw": canonical_raw,
            "_canonical_object": canonical_obj,
            "_lift_entry": lift_by_source.get(selected_ref["path"]),
        })
    _require(lifted_count == 5 and len(lift_by_source) == 5 and len(reports) == 92 and
             total_rows == 4252 and len(seen_case_ids) == 1108 and
             len(seen_raw_sources) == len(seen_capture_paths) == 4252 and
             len(fresh_by_adapter) == 92,
             "source report membership does not match fixed publication counts")
    _require(len(selector.get("fresh_groups", [])) == 84 if isinstance(selector.get("fresh_groups"), list)
             else selector.get("fresh_groups") == 84,
             "source selector group count differs")
    _require(receipt_ref["path"] == CANONICAL_RECEIPT_PATH and
             receipt_ref["sha256"] == CANONICAL_RECEIPT_SHA256,
             "canonical validation receipt reference changed during report enumeration")
    return {
        "selection": selection,
        "selection_ref": selection_ref,
        "selector": selector,
        "selector_ref": source_selector_ref,
        "receipt": receipt,
        "receipt_ref": receipt_ref,
        "joern_sidecar": joern,
        "joern_sidecar_raw": joern_raw,
        "joern_sidecar_ref": joern_ref,
        "schema_ref": schema_ref,
        "schema_raw": schema_raw,
        "ledger": ledger,
        "reports": reports,
        "counts": dict(EXPECTED_COUNTS),
    }


def _qualification_sidecar(context: dict[str, Any]) -> dict[str, Any]:
    state = {
        "publication_approved": False,
        "full_release_gate_satisfied": False,
        "freeze_created": False,
        "scoring_enabled": False,
        "scorecard_generation_allowed": False,
    }
    return {
        "schema": QUALIFICATION_SCHEMA,
        "publication": state,
        "bifrost_v0151": {
            "full_policy_qualification": False,
            "scoring_permitted": False,
        },
        "joern_swift_common108": {
            **EXPECTED_JOERN_OUTCOMES,
            "aggregate_resource_qualification": "unavailable",
            "semantic_qualification": "unavailable",
            "evidence_scope": "semantic-only",
            "scored_activation": False,
            "scoring_permitted": False,
            "timing_certified": False,
        },
        "source_joern_sidecar": context["joern_sidecar_ref"],
        "source_joern_sidecar_json": context["joern_sidecar_raw"].decode("utf-8"),
        "joern_metadata_lift": context["joern_sidecar"],
    }


def _normal_report(canonical: dict[str, Any], raw_map: list[dict[str, Any]]) -> dict[str, Any]:
    value = copy.deepcopy(canonical)
    rows = value.get("results")
    _require(type(rows) is list and len(rows) == len(raw_map),
             "published report raw mapping count differs")
    for ordinal, item in enumerate(raw_map):
        _require(rows[ordinal].get("case_id") == item["case_id"] and
                 rows[ordinal].get("raw_output") == item["source_path"],
                 "published report mapping does not align with canonical rows")
        rows[ordinal]["raw_output"] = item["capture_path"]
    return value


def _build_raw_destination(adapter_id: str, case_id: str, source_path: str) -> str:
    suffix = "".join(PurePosixPath(source_path).suffixes)
    return _safe_relative(f"{CAPTURE_SCOPE}/raw/{adapter_id}/{case_id}{suffix}",
                          "publication raw destination")


def prepare(source_root: os.PathLike[str] | str, root: os.PathLike[str] | str) -> dict[str, Any]:
    """Create a new publication scope from the exact selected and validated source set."""
    source = _root(source_root)
    target_root = _root(root)
    final = _join(target_root, PUBLICATION_SCOPE, "publication output", exists=False)
    _require(not os.path.lexists(final), "publication output already exists")
    context = _preflight(source)
    try:
        head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PublicationEvidenceError("cannot identify source repository HEAD") from exc

    stage_parent = target_root / "reports/releases/v0.9.2"
    _assert_no_symlinks(stage_parent)
    stage = Path(tempfile.mkdtemp(prefix=".publication-v1-staging-", dir=stage_parent))
    raw_records: list[dict[str, Any]] = []
    report_records: list[dict[str, Any]] = []
    capture_records: dict[str, dict[str, Any]] = {}
    try:
        for item in context["reports"]:
            basename = PurePosixPath(item["canonical_report"]["path"]).name
            canonical_capture = f"{CAPTURE_SCOPE}/source-reports/{basename}"
            canonical_stage = stage / "capture/source-reports" / basename
            canonical_sha, canonical_bytes = _copy_file(
                _join(source, item["canonical_report"]["path"], "canonical report source", exists=True),
                canonical_stage, expected_sha256=item["canonical_report"]["sha256"],
                expected_bytes=item["canonical_report"]["bytes"] if "bytes" in item["canonical_report"] else None)
            _require(canonical_sha == item["canonical_report"]["sha256"],
                     "captured canonical report digest differs")
            capture_records[canonical_capture] = {
                "path": canonical_capture, "sha256": canonical_sha,
                "bytes": canonical_bytes, "kind": "canonical-source-report"}

            selected_capture = None
            if item["lifted_metadata"]:
                selected_basename = PurePosixPath(item["selected_original"]["path"]).name
                _require(selected_basename == basename, "selected Joern source basename differs")
                selected_capture = f"{CAPTURE_SCOPE}/selected-reports/{selected_basename}"
                selected_stage = stage / "capture/selected-reports" / selected_basename
                selected_sha, selected_bytes = _copy_file(
                    _join(source, item["selected_original"]["path"], "selected original report", exists=True),
                    selected_stage, expected_sha256=item["selected_original"]["sha256"])
                capture_records[selected_capture] = {
                    "path": selected_capture, "sha256": selected_sha,
                    "bytes": selected_bytes, "kind": "selected-original-joern-report"}

            mappings: list[dict[str, Any]] = []
            for ordinal, row in enumerate(item["_canonical_object"]["results"]):
                source_path = _safe_relative(row.get("raw_output"), "canonical raw output path")
                raw_target_rel = _build_raw_destination(item["adapter_id"], row["case_id"], source_path)
                raw_stage = stage.joinpath(*PurePosixPath(raw_target_rel).parts[len(PurePosixPath(PUBLICATION_SCOPE).parts):])
                source_raw = _join(source, source_path, "source raw output", exists=True)
                digest_value, byte_count = _copy_file(source_raw, raw_stage)
                if item["lifted_metadata"]:
                    lift_row = item["_lift_entry"]["metadata_lift"]["removed_result_metadata"][ordinal]
                    _require(lift_row["raw_sha256"] == digest_value,
                             "Joern raw payload differs from the source sidecar digest")
                mapping = {
                    "case_id": row["case_id"], "ordinal": ordinal,
                    "source_path": source_path, "capture_path": raw_target_rel,
                    "sha256": digest_value, "bytes": byte_count,
                }
                mappings.append(mapping)
                raw_records.append(mapping)
                capture_records[raw_target_rel] = {
                    "path": raw_target_rel, "sha256": digest_value,
                    "bytes": byte_count, "kind": "raw-output"}

            published = _normal_report(item["_canonical_object"], mappings)
            published_path = f"{PUBLICATION_SCOPE}/normal/{basename}"
            published_bytes = _json_bytes(published)
            published_sha = _sha(published_bytes)
            _write_new(stage / "normal" / basename, published_bytes)
            report_records.append({
                "adapter": item["adapter"],
                "adapter_id": item["adapter_id"],
                "attempt_id": item["attempt_id"],
                "attempt_number": item["attempt_number"],
                "row_count": item["row_count"],
                "selected_original": item["selected_original"],
                "canonical_report": item["canonical_report"],
                "capture_source_report": {
                    "path": canonical_capture, "sha256": canonical_sha,
                    "bytes": canonical_bytes},
                "capture_selected_report": None if selected_capture is None else {
                    "path": selected_capture,
                    "sha256": capture_records[selected_capture]["sha256"],
                    "bytes": capture_records[selected_capture]["bytes"]},
                "published_report": {"path": published_path,
                                     "sha256": published_sha,
                                     "bytes": len(published_bytes)},
                "lifted_metadata": item["lifted_metadata"],
                "raw_outputs": mappings,
            })

        qualification = _qualification_sidecar(context)
        qualification_path = f"{PUBLICATION_SCOPE}/qualification-sidecar.json"
        qualification_raw = json.dumps(qualification, sort_keys=True, indent=2,
                                       ensure_ascii=False).encode("utf-8") + b"\n"
        qualification_sha = _sha(qualification_raw)
        _write_new(stage / "qualification-sidecar.json", qualification_raw)

        manifest = {
            "schema": SCHEMA,
            "scope": PUBLICATION_SCOPE,
            "producer": {
                "path": "scripts/v092_publication_evidence.py",
                "sha256": _sha(Path(__file__).read_bytes()),
            },
            "bundle_tool": {
                "path": "scripts/evidence_bundle.py",
                "sha256": _sha((target_root / "scripts/evidence_bundle.py").read_bytes()),
            },
            "source_root_head": head,
            "sources": {
                "selection": context["selection_ref"],
                "source_selector": context["selector_ref"],
                "canonical_validation": context["receipt_ref"],
                "joern_metadata_sidecar": context["joern_sidecar_ref"],
                "ledger": context["ledger"],
                "schema": context["schema_ref"],
            },
            "counts": context["counts"],
            "capture_scope": CAPTURE_SCOPE,
            "capture_files": [capture_records[path] for path in sorted(capture_records)],
            "qualification_sidecar": {"path": qualification_path,
                                       "sha256": qualification_sha,
                                       "bytes": len(qualification_raw)},
            "qualification_state": {
                "publication_approved": False,
                "full_release_gate_satisfied": False,
                "freeze_created": False,
                "scoring_enabled": False,
                "scorecard_generation_allowed": False,
                "bifrost_full_policy_qualification": False,
                "joern_inconclusive": 96,
                "joern_unsupported": 12,
                "joern_aggregate_resource_qualification": "unavailable",
                "joern_scored_activation": False,
                "joern_scoring_permitted": False,
                "joern_timing_certified": False,
            },
            "reports": report_records,
            "bundle_delivery_path": BUNDLE_PATH,
        }
        manifest_raw = json.dumps(manifest, sort_keys=True, indent=2,
                                  ensure_ascii=False).encode("utf-8") + b"\n"
        _write_new(stage / "manifest.json", manifest_raw)
        _require(not os.path.lexists(final), "publication output appeared during prepare")
        os.rename(stage, final)
    except BaseException:
        if stage.exists() and stage != final:
            shutil.rmtree(stage, ignore_errors=True)
        raise
    result = verify(target_root)
    result["status"] = "prepared-and-verified"
    result["manifest_sha256"] = _sha((final / "manifest.json").read_bytes())
    return result


def _capture_file_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = manifest.get("capture_files")
    _require(type(records) is list, "publication capture file list is missing")
    output: dict[str, dict[str, Any]] = {}
    for record in records:
        _require(type(record) is dict and
                 set(record) == {"path", "sha256", "bytes", "kind"},
                 "publication capture record has an unexpected field set")
        path = _safe_relative(record["path"], "publication capture path")
        _require(path.startswith(CAPTURE_SCOPE + "/") and path not in output and
                 type(record["bytes"]) is int and record["bytes"] >= 0 and
                 type(record["sha256"]) is str and len(record["sha256"]) == 64 and
                 record["kind"] in {"canonical-source-report", "selected-original-joern-report", "raw-output"},
                 "publication capture record is malformed or duplicated")
        output[path] = record
    return output


def _validate_qualification_sidecar(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    expected_ref = manifest.get("qualification_sidecar")
    _require(type(expected_ref) is dict and
             expected_ref.get("path") == f"{PUBLICATION_SCOPE}/qualification-sidecar.json",
             "publication qualification sidecar path differs")
    raw = _read_file(root, expected_ref["path"], expected_sha256=expected_ref.get("sha256"),
                     label="publication qualification sidecar")
    _require(len(raw) == expected_ref.get("bytes"), "publication qualification sidecar size differs")
    sidecar = _json(raw, "publication qualification sidecar")
    state = {
        "publication_approved": False,
        "full_release_gate_satisfied": False,
        "freeze_created": False,
        "scoring_enabled": False,
        "scorecard_generation_allowed": False,
    }
    expected_bifrost = {
        "full_policy_qualification": False, "scoring_permitted": False}
    expected_joern = {
        **EXPECTED_JOERN_OUTCOMES,
        "aggregate_resource_qualification": "unavailable",
        "semantic_qualification": "unavailable",
        "evidence_scope": "semantic-only",
        "scored_activation": False,
        "scoring_permitted": False,
        "timing_certified": False,
    }
    _require(sidecar.get("schema") == QUALIFICATION_SCHEMA and
             _same_json_object(sidecar.get("publication"), state) and
             _same_json_object(sidecar.get("bifrost_v0151"), expected_bifrost) and
             _same_json_object(sidecar.get("joern_swift_common108"), expected_joern),
             "publication qualification sidecar changed its nonqualification boundary")
    source_ref = sidecar.get("source_joern_sidecar")
    sources = manifest.get("sources", {})
    _require(source_ref == sources.get("joern_metadata_sidecar") and
             source_ref == {"path": JOERN_SIDECAR_PATH,
                            "sha256": JOERN_SIDECAR_SHA256,
                            "bytes": source_ref.get("bytes")},
             "qualification sidecar no longer binds the reviewed Joern sidecar")
    raw_text = sidecar.get("source_joern_sidecar_json")
    _require(type(raw_text) is str and raw_text.encode("utf-8") ==
             json.dumps(sidecar.get("joern_metadata_lift"), sort_keys=True, indent=2,
                        ensure_ascii=False).encode("utf-8") + b"\n",
             "embedded Joern metadata sidecar object differs from its exact source bytes")
    _require(_sha(raw_text.encode("utf-8")) == JOERN_SIDECAR_SHA256 and
             sidecar.get("joern_metadata_lift") is not None,
             "embedded Joern sidecar bytes do not match the exact reviewed source digest")
    joern = _json(raw_text.encode("utf-8"), "embedded original Joern sidecar")
    _require(joern.get("schema") == "v092-joern-schema-metadata-lift-aggregate/v1" and
             joern.get("aggregate_counts") == {
                 "cases": 108, "distinct_raw_output_paths": 108,
                 "outcomes": EXPECTED_JOERN_OUTCOMES, "reports": 5},
             "embedded original Joern sidecar counts differ")
    state_ref = manifest.get("qualification_state")
    expected_state = {
        "publication_approved": False,
        "full_release_gate_satisfied": False,
        "freeze_created": False,
        "scoring_enabled": False,
        "scorecard_generation_allowed": False,
        "bifrost_full_policy_qualification": False,
        "joern_inconclusive": 96,
        "joern_unsupported": 12,
        "joern_aggregate_resource_qualification": "unavailable",
        "joern_scored_activation": False,
        "joern_scoring_permitted": False,
        "joern_timing_certified": False,
    }
    _require(_same_json_object(state_ref, expected_state),
             "publication manifest qualification flags differ")
    return sidecar


def _validate_manifest(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    manifest_path = f"{PUBLICATION_SCOPE}/manifest.json"
    manifest = _json(_read_file(root, manifest_path, label="publication manifest"),
                     "publication manifest")
    _require(manifest.get("schema") == SCHEMA and manifest.get("scope") == PUBLICATION_SCOPE and
             manifest.get("capture_scope") == CAPTURE_SCOPE and
             manifest.get("bundle_delivery_path") == BUNDLE_PATH and
             manifest.get("counts") == EXPECTED_COUNTS,
             "publication manifest schema, scope, or fixed counts differ")
    producer = manifest.get("producer")
    _require(type(producer) is dict and producer.get("path") == "scripts/v092_publication_evidence.py" and
             producer.get("sha256") == _sha(Path(__file__).read_bytes()),
             "publication producer source differs from its manifest binding")
    bundle_tool = manifest.get("bundle_tool")
    _require(type(bundle_tool) is dict and bundle_tool.get("path") == "scripts/evidence_bundle.py" and
             bundle_tool.get("sha256") == _sha((root / "scripts/evidence_bundle.py").read_bytes()),
             "lossless bundle implementation differs from its manifest binding")
    sources = manifest.get("sources")
    _require(type(sources) is dict and
             sources.get("selection") == {"path": SELECTION_PATH, "sha256": SELECTION_SHA256,
                                           "bytes": sources.get("selection", {}).get("bytes")} and
             sources.get("source_selector", {}).get("path") == SOURCE_SELECTOR_PATH and
             sources.get("source_selector", {}).get("sha256") == SOURCE_SELECTOR_SHA256 and
             sources.get("canonical_validation", {}).get("path") == CANONICAL_RECEIPT_PATH and
             sources.get("canonical_validation", {}).get("sha256") == CANONICAL_RECEIPT_SHA256 and
             sources.get("joern_metadata_sidecar", {}).get("path") == JOERN_SIDECAR_PATH and
             sources.get("joern_metadata_sidecar", {}).get("sha256") == JOERN_SIDECAR_SHA256 and
             sources.get("schema") == {"path": SCHEMA_PATH, "sha256": SCHEMA_SHA256,
                                       "bytes": sources.get("schema", {}).get("bytes")} and
             sources.get("ledger", {}).get("path") == LEDGER_PATH and
             sources.get("ledger", {}).get("sha256") == LEDGER_SHA256 and
             sources.get("ledger", {}).get("line_count") == 151,
             "publication manifest source inputs differ")
    captures = _capture_file_records(manifest)
    sidecar = _validate_qualification_sidecar(root, manifest)
    _verify_fixed_source_bindings(root, manifest)
    return manifest, captures, sidecar


def _verify_fixed_source_bindings(root: Path, manifest: dict[str, Any]) -> None:
    """Reopen the immutable selection inputs and bind every report entry to them."""
    sources = manifest["sources"]
    selection_raw, selection_ref = _sha_file_ref(
        root, SELECTION_PATH, SELECTION_SHA256, "fixed publication selection")
    _require(sources["selection"] == selection_ref,
             "manifest selection reference differs from the fixed selection bytes")
    selection = _json(selection_raw, "fixed publication selection")
    _require(selection.get("schema") == "v092-final-review-selection-with-canonical-validation/v1" and
             selection.get("status") == "selection-and-canonical-report-validation-verified" and
             selection.get("partitions") == 92 and selection.get("rows") == 4252 and
             selection.get("distinct_case_ids") == 1108 and
             selection.get("publication_approved") is False and
             selection.get("full_release_gate_satisfied") is False and
             selection.get("freeze_created") is False and
             selection.get("scoring_enabled") is False and
             selection.get("scorecard_generation_allowed") is False,
             "fixed publication selection changed its counts or nonpublication boundary")

    selector_ref, selector_raw = _source_ref(root, selection.get("source_selector"),
                                             "fixed source selector")
    _require(selector_ref["path"] == SOURCE_SELECTOR_PATH and
             selector_ref["sha256"] == SOURCE_SELECTOR_SHA256 and
             sources["source_selector"] == selector_ref,
             "manifest source selector differs from the fixed selection input")
    selector = _json(selector_raw, "fixed source selector")
    _require(selector.get("schema") == "dataflowbench-v0.9.2-publication-evidence-selection/v1" and
             selector.get("status") == "fresh-evidence-verified" and
             selector.get("fresh_groups") == 84 and selector.get("fresh_partitions") == 92 and
             selector.get("fresh_rows") == 4252 and selector.get("case_count") == 1108 and
             selector.get("carried_partitions") == 0 and selector.get("carried_rows") == 0 and
             selector.get("publication_approved") is False and
             selector.get("full_release_gate_satisfied") is False and
             selector.get("freeze_created") is False and selector.get("scoring_enabled") is False and
             selector.get("scorecard_generation_allowed") is False and
             selector.get("bifrost_v0151_reconciliation", {}).get("full_policy_qualification") is False and
             selector.get("typed_outcomes", {}).get("joern_swift_common108") == EXPECTED_JOERN_OUTCOMES,
             "fixed source selector changed its counts or qualification boundary")

    receipt_ref, _ = _source_ref(root, selection.get("canonical_validation"),
                                 "fixed canonical validation receipt")
    _require(receipt_ref["path"] == CANONICAL_RECEIPT_PATH and
             receipt_ref["sha256"] == CANONICAL_RECEIPT_SHA256 and
             sources["canonical_validation"] == receipt_ref,
             "manifest canonical validation receipt differs from the fixed selection input")

    sidecar_ref, sidecar_raw = _source_ref(root, selection.get("joern_sidecar"),
                                           "fixed Joern metadata sidecar")
    _require(sidecar_ref["path"] == JOERN_SIDECAR_PATH and
             sidecar_ref["sha256"] == JOERN_SIDECAR_SHA256 and
             sources["joern_metadata_sidecar"] == sidecar_ref,
             "manifest Joern sidecar differs from the fixed selection input")

    schema_raw, schema_ref = _sha_file_ref(root, SCHEMA_PATH, SCHEMA_SHA256,
                                           "fixed canonical report schema")
    _require(sources["schema"] == schema_ref and
             _sha(schema_raw) == SCHEMA_SHA256,
             "manifest schema reference differs from the frozen schema bytes")
    joern_source = _json(sidecar_raw, "fixed Joern metadata sidecar")
    _require(joern_source.get("source_identity", {}).get("frozen_schema_bytes_sha256") == SCHEMA_SHA256,
             "fixed Joern sidecar does not bind the frozen schema")

    ledger = _hash_ledger(root, selector)
    for key in ("path", "sha256", "bytes", "line_count",
                "prefix_130_sha256", "prefix_131_sha256"):
        _require(sources["ledger"].get(key) == ledger[key],
                 "manifest ledger reference differs from the fixed ledger bytes")

    fresh_reports = selector.get("fresh_reports")
    selected_reports = selection.get("selected_reports")
    published_reports = manifest.get("reports")
    _require(type(fresh_reports) is list and len(fresh_reports) == 92 and
             type(selected_reports) is list and len(selected_reports) == 92 and
             type(published_reports) is list and len(published_reports) == 92,
             "fixed selection report roster must contain exactly 92 entries")
    fresh_by_adapter = {entry.get("adapter"): entry for entry in fresh_reports
                        if type(entry) is dict}
    selected_by_adapter = {entry.get("adapter"): entry for entry in selected_reports
                           if type(entry) is dict}
    manifest_by_adapter = {entry.get("adapter"): entry for entry in published_reports
                           if type(entry) is dict}
    _require(len(fresh_by_adapter) == len(selected_by_adapter) == len(manifest_by_adapter) == 92,
             "fixed report rosters contain duplicate or malformed adapter identities")
    _require(set(fresh_by_adapter) == set(selected_by_adapter) == set(manifest_by_adapter),
             "manifest report adapter membership differs from the fixed selection")
    for adapter, selected in selected_by_adapter.items():
        fresh = fresh_by_adapter[adapter]
        report = manifest_by_adapter[adapter]
        expected_source = selected.get("selected_original")
        expected_canonical = selected.get("canonical_report")
        _require(type(expected_source) is dict and type(expected_canonical) is dict and
                 selected.get("attempt_id") == fresh.get("attempt_id") == report.get("attempt_id") and
                 selected.get("attempt_number") == fresh.get("attempt_number") == report.get("attempt_number") and
                 report.get("adapter_id") == PurePosixPath(adapter).stem and
                 report.get("selected_original", {}).get("path") == expected_source.get("path") == fresh.get("staged_path") and
                 report.get("selected_original", {}).get("sha256") == expected_source.get("sha256") == fresh.get("sha256") and
                 report.get("canonical_report", {}).get("path") == expected_canonical.get("path") and
                 report.get("canonical_report", {}).get("sha256") == expected_canonical.get("sha256") and
                 report.get("row_count") == fresh.get("rows") and
                 report.get("lifted_metadata") is selected.get("metadata_lift"),
                 f"manifest report identity differs from fixed selection for {adapter}")


def _walk_regular_files(root: Path) -> set[str]:
    _assert_no_symlinks(root)
    _require(root.is_dir(), f"expected directory missing: {root}")
    result: set[str] = set()
    for base, directories, files in os.walk(root, topdown=True, followlinks=False):
        base_path = Path(base)
        for name in list(directories):
            child = base_path / name
            _require(not child.is_symlink() and stat.S_ISDIR(child.lstat().st_mode),
                     f"symlink or non-directory refused: {child}")
        for name in files:
            child = base_path / name
            _require(not child.is_symlink() and stat.S_ISREG(child.lstat().st_mode),
                     f"symlink or non-regular file refused: {child}")
            result.add(child.relative_to(root).as_posix())
    return result


def _check_report_mapping(canonical: dict[str, Any], published: dict[str, Any],
                          report: dict[str, Any]) -> None:
    expected = copy.deepcopy(canonical)
    mappings = report.get("raw_outputs")
    _require(type(mappings) is list and len(mappings) == len(expected.get("results", [])),
             "publication raw mapping list differs from source report")
    seen: set[str] = set()
    for ordinal, mapping in enumerate(mappings):
        _require(type(mapping) is dict and
                 set(mapping) == {"case_id", "ordinal", "source_path", "capture_path", "sha256", "bytes"} and
                 mapping.get("ordinal") == ordinal and
                 mapping.get("case_id") == expected["results"][ordinal].get("case_id") and
                 mapping.get("source_path") == expected["results"][ordinal].get("raw_output"),
                 "publication raw mapping differs from canonical report row")
        capture_path = _safe_relative(mapping["capture_path"], "published raw output")
        _require(capture_path.startswith(CAPTURE_SCOPE + "/raw/") and capture_path not in seen,
                 "published raw path escapes capture scope or collides")
        seen.add(capture_path)
        expected["results"][ordinal]["raw_output"] = capture_path
    _require(expected == published,
             "published report differs from canonical report beyond raw_output relocation")


def _check_selected_lift(selected: dict[str, Any], canonical: dict[str, Any],
                         lift_entry: dict[str, Any]) -> None:
    _metadata_lift(selected, canonical, lift_entry, lift_entry["source_report_path"])


def verify(root: os.PathLike[str] | str) -> dict[str, Any]:
    """Verify normal report semantics, all captured inputs, and qualification boundaries."""
    repo = _root(root)
    manifest, captures, sidecar = _validate_manifest(repo)
    report_rows = manifest.get("reports")
    _require(type(report_rows) is list and len(report_rows) == 92,
             "publication manifest must bind exactly 92 reports")
    normal_dir = _join(repo, f"{PUBLICATION_SCOPE}/normal", "normal report directory", exists=True)
    expected_normal: set[str] = set()
    expected_capture: set[str] = set()
    seen_case_ids: set[str] = set()
    seen_raw_sources: set[str] = set()
    published_hashes: list[dict[str, str]] = []
    total_rows = 0
    lifted_reports = 0
    lifted_rows = 0
    original_sidecar = sidecar["joern_metadata_lift"]
    lift_by_source = {entry["source_report_path"]: entry for entry in original_sidecar["reports"]}

    for report in report_rows:
        _require(type(report) is dict and
                 set(report) == {"adapter", "adapter_id", "attempt_id", "attempt_number",
                                 "row_count", "selected_original", "canonical_report",
                                 "capture_source_report", "capture_selected_report",
                                 "published_report", "lifted_metadata", "raw_outputs"},
                 "publication report entry has an unexpected field set")
        basename = PurePosixPath(report["canonical_report"]["path"]).name
        expected_published_path = f"{PUBLICATION_SCOPE}/normal/{basename}"
        published = report["published_report"]
        _require(published.get("path") == expected_published_path and
                 published.get("bytes", -1) >= 0 and
                 report["adapter_id"] == PurePosixPath(report["adapter"]).stem and
                 report["adapter"] == f"reports/releases/v0.9.2/normal/{basename}",
                 "publication report destination is not the original adapter basename")
        expected_normal.add(basename)

        canonical_capture = report["capture_source_report"]
        _require(type(canonical_capture) is dict and
                 canonical_capture.get("path") == f"{CAPTURE_SCOPE}/source-reports/{basename}" and
                 canonical_capture.get("sha256") == report["canonical_report"].get("sha256") and
                 canonical_capture.get("bytes") == report["canonical_report"].get("bytes"),
                 "canonical source capture ref differs")
        expected_capture.add(canonical_capture["path"])
        capture_record = captures.get(canonical_capture["path"])
        _require(capture_record is not None and capture_record["sha256"] == canonical_capture["sha256"] and
                 capture_record["bytes"] == canonical_capture["bytes"] and
                 capture_record["kind"] == "canonical-source-report",
                 "canonical source report is not in the bound capture inventory")
        canonical_raw = _read_file(repo, canonical_capture["path"],
                                   expected_sha256=canonical_capture["sha256"],
                                   label="captured canonical source report")
        _require(len(canonical_raw) == canonical_capture["bytes"],
                 "captured canonical source report size differs")
        canonical = _json(canonical_raw, "captured canonical report")
        _require(_sha(canonical_raw) == report["canonical_report"]["sha256"],
                 "captured canonical source report differs from source selection hash")

        published_path = _join(repo, published["path"], "published report", exists=True)
        published_raw = _read_file(repo, published["path"], expected_sha256=published.get("sha256"),
                                   label="published report")
        _require(len(published_raw) == published["bytes"], "published report size differs")
        published_obj = _json(published_raw, "published report")
        _check_report_mapping(canonical, published_obj, report)
        _require(len(canonical.get("results", [])) == report["row_count"],
                 "published report row count differs")
        total_rows += report["row_count"]
        published_hashes.append({"path": published["path"], "sha256": published["sha256"]})

        selected_capture = report["capture_selected_report"]
        if report["lifted_metadata"]:
            lifted_reports += 1
            _require(type(selected_capture) is dict and
                     selected_capture.get("path") == f"{CAPTURE_SCOPE}/selected-reports/{basename}",
                     "lifted Joern source report copy is missing")
            expected_capture.add(selected_capture["path"])
            selected_record = captures.get(selected_capture["path"])
            _require(selected_record is not None and
                     selected_record["sha256"] == selected_capture.get("sha256") and
                     selected_record["bytes"] == selected_capture.get("bytes") and
                     selected_record["kind"] == "selected-original-joern-report",
                     "selected Joern source report is not in the bound capture inventory")
            selected_raw = _read_file(repo, selected_capture["path"],
                                      expected_sha256=selected_capture["sha256"],
                                      label="captured selected Joern report")
            _require(len(selected_raw) == selected_capture["bytes"] and
                     selected_capture["sha256"] == report["selected_original"]["sha256"],
                     "captured selected Joern report differs from the selector hash")
            selected_obj = _json(selected_raw, "captured selected Joern report")
            lift_entry = lift_by_source.get(report["selected_original"]["path"])
            _require(lift_entry is not None and
                     lift_entry.get("canonical_report_path") == report["canonical_report"]["path"] and
                     lift_entry.get("source_report_bytes_sha256") == report["selected_original"]["sha256"] and
                     lift_entry.get("canonical_report_bytes_sha256") == report["canonical_report"]["sha256"],
                     "Joern selected source and canonical report paths differ from the original sidecar")
            _check_selected_lift(selected_obj, canonical, lift_entry)
            lifted_rows += report["row_count"]
        else:
            _require(selected_capture is None and
                     report["selected_original"]["path"] == report["canonical_report"]["path"] and
                     report["selected_original"]["sha256"] == report["canonical_report"]["sha256"],
                     "unlifted report has an unexpected selected-source copy")

        raw_outputs = report["raw_outputs"]
        _require(type(raw_outputs) is list and len(raw_outputs) == report["row_count"],
                 "raw output mapping count differs from report rows")
        for ordinal, mapping in enumerate(raw_outputs):
            row = canonical["results"][ordinal]
            _require(mapping.get("case_id") == row.get("case_id") and
                     mapping.get("ordinal") == ordinal and
                     mapping.get("source_path") == row.get("raw_output"),
                     "manifest raw output row membership differs")
            source_path = _safe_relative(mapping["source_path"], "raw source path")
            _require(source_path not in seen_raw_sources,
                     "manifest repeats a raw source path")
            seen_raw_sources.add(source_path)
            case_id = row.get("case_id")
            _require(type(case_id) is str and case_id,
                     "published row case ID is malformed")
            seen_case_ids.add(case_id)
            expected_raw = _build_raw_destination(report["adapter_id"], case_id, source_path)
            _require(mapping.get("capture_path") == expected_raw,
                     "manifest raw capture path differs from adapter/case/suffix mapping")
            expected_capture.add(expected_raw)
            raw_record = captures.get(expected_raw)
            _require(raw_record is not None and raw_record["kind"] == "raw-output" and
                     raw_record["sha256"] == mapping.get("sha256") and
                     raw_record["bytes"] == mapping.get("bytes"),
                     "raw output hash is absent from capture inventory")
            raw_path = _join(repo, expected_raw, "captured raw output", exists=True)
            raw_sha, raw_bytes = _file_digest(raw_path)
            _require(raw_sha == mapping["sha256"] and raw_bytes == mapping["bytes"],
                     "captured raw output bytes differ from manifest")
            if report["lifted_metadata"]:
                removed = lift_by_source[report["selected_original"]["path"]]["metadata_lift"]["removed_result_metadata"][ordinal]
                _require(removed["raw_sha256"] == raw_sha,
                         "captured Joern raw output differs from preserved row digest")
    _require(_walk_regular_files(normal_dir) == expected_normal,
             "normal report directory contains missing or unknown files")
    _require(_walk_regular_files(_join(repo, CAPTURE_SCOPE, "capture scope", exists=True)) ==
             {path.removeprefix(CAPTURE_SCOPE + "/") for path in expected_capture},
             "capture scope has missing or unknown files")
    _require(set(captures) == expected_capture and
             len(seen_case_ids) == 1108 and len(seen_raw_sources) == 4252 and
             len(expected_capture) == 4349 and total_rows == 4252 and
             lifted_reports == 5 and lifted_rows == 108,
             "publication output counts differ from fixed membership")
    return {"status": "verified", "counts": manifest["counts"],
            "reports": published_hashes,
            "capture_files": len(captures),
            "qualification_sidecar": manifest["qualification_sidecar"]}


def _restore_bundle(root: Path, bundle: Path, manifest: dict[str, Any],
                    captures: dict[str, dict[str, Any]]) -> dict[str, Any]:
    _assert_no_symlinks(bundle)
    _require(bundle.is_dir(), "publication detail bundle is missing")
    index_raw = _read_file(root, f"{BUNDLE_PATH}/bundle.json",
                           label="evidence bundle index")
    index = _json(index_raw, "evidence bundle index")
    _require(index.get("schema") == evidence_bundle.SCHEMA and
             index.get("scope") == CAPTURE_SCOPE and
             index.get("snapshot_file_count") == len(captures) and
             index.get("original_bytes") == sum(record["bytes"] for record in captures.values()),
             "publication bundle does not contain the exact capture scope")
    with tempfile.TemporaryDirectory(prefix="v092-publication-hydrate-") as temporary:
        restore = Path(temporary) / "restore"
        result = evidence_bundle.check(bundle, restore=restore)
        _require(result.get("status") == "verified" and
                 result.get("files") == len(captures) and
                 result.get("restored_files") == len(captures),
                 "publication bundle restore did not verify the complete capture")
        restored_capture = restore.joinpath(*PurePosixPath(CAPTURE_SCOPE).parts)
        expected_local = {path.removeprefix(CAPTURE_SCOPE + "/") for path in captures}
        _require(_walk_regular_files(restored_capture) == expected_local,
                 "restored bundle contains missing or unmanifested capture paths")
        capture_destination = root.joinpath(*PurePosixPath(CAPTURE_SCOPE).parts)
        if capture_destination.exists() or capture_destination.is_symlink():
            _require(capture_destination.is_dir() and not capture_destination.is_symlink(),
                     "existing capture destination is not a regular directory")
            existing = _walk_regular_files(capture_destination)
            _require(existing <= expected_local,
                     "existing capture contains paths outside the publication manifest")
        for relative, record in captures.items():
            local = relative.removeprefix(CAPTURE_SCOPE + "/")
            source = restored_capture / local
            destination = root.joinpath(*PurePosixPath(relative).parts)
            _copy_file(source, destination, expected_sha256=record["sha256"],
                       expected_bytes=record["bytes"], allow_identical=True)
    return {"status": "hydrated", "files": len(captures),
            "bytes": sum(item["bytes"] for item in captures.values()),
            "bundle_path": BUNDLE_PATH}


def hydrate(root: os.PathLike[str] | str) -> dict[str, Any]:
    """Verify the committed evidence bundle and restore only manifest-bound capture files."""
    repo = _root(root)
    manifest, captures, _ = _validate_manifest(repo)
    bundle = _join(repo, BUNDLE_PATH, "publication detail bundle", exists=True)
    _restore_bundle(repo, bundle, manifest, captures)
    result = verify(repo)
    return {"status": "hydrated-and-verified", "counts": result["counts"],
            "capture_files": result["capture_files"], "bundle_path": BUNDLE_PATH}


def stage_site(root: os.PathLike[str] | str, output: str) -> dict[str, Any]:
    """Stage raw payloads for the static site without changing the publication capture."""
    repo = _root(root)
    result = verify(repo)
    manifest = _json(_read_file(repo, f"{PUBLICATION_SCOPE}/manifest.json",
                                label="publication manifest"), "publication manifest")
    output_rel = _safe_relative(output, "site evidence output")
    _require(not output_rel.startswith(CAPTURE_SCOPE + "/") and
             not output_rel.startswith(PUBLICATION_SCOPE + "/"),
             "site evidence output must be outside publication source scope")
    records: list[tuple[str, str, dict[str, Any]]] = []
    expected_destinations: set[str] = set()
    for report in manifest["reports"]:
        for raw in report["raw_outputs"]:
            source_rel = raw["capture_path"]
            name = PurePosixPath(source_rel).name
            destination_rel = f"{output_rel}/{report['adapter_id']}/{name}"
            _safe_relative(destination_rel, "site raw destination")
            _require(destination_rel not in expected_destinations,
                     "two payloads collide in the static site output")
            expected_destinations.add(destination_rel)
            records.append((source_rel, destination_rel, raw))
    output_root = _join(repo, output_rel, "site evidence output", exists=False)
    if os.path.lexists(output_root):
        _require(output_root.is_dir() and not output_root.is_symlink(),
                 "site evidence destination must be a regular directory")
        existing = _walk_regular_files(output_root)
        expected_local = {item.removeprefix(output_rel + "/") for item in expected_destinations}
        _require(existing == expected_local,
                 "existing site evidence tree is not the exact expected file set")
        for source_rel, destination_rel, raw in records:
            dest = _join(repo, destination_rel, "site evidence file", exists=True)
            _require(_file_digest(dest) == (raw["sha256"], raw["bytes"]),
                     "existing site evidence file differs from publication capture")
    else:
        output_root.mkdir(parents=True)
        for source_rel, destination_rel, raw in records:
            source_file = _join(repo, source_rel, "captured raw output", exists=True)
            dest = _join(repo, destination_rel, "site evidence file", exists=False)
            _copy_file(source_file, dest, expected_sha256=raw["sha256"],
                       expected_bytes=raw["bytes"])
        _require(_walk_regular_files(output_root) ==
                 {item.removeprefix(output_rel + "/") for item in expected_destinations},
                 "staged site evidence tree differs from its fixed path map")
    return {"status": "staged-and-verified", "files": len(records),
            "counts": result["counts"], "output": output_rel}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="prepare a new publication scope")
    prepare_parser.add_argument("--source-root", required=True, type=Path)
    prepare_parser.add_argument("--root", required=True, type=Path)
    verify_parser = commands.add_parser("verify", help="verify prepared publication evidence")
    verify_parser.add_argument("--root", required=True, type=Path)
    hydrate_parser = commands.add_parser("hydrate", help="restore capture from the lossless detail bundle")
    hydrate_parser.add_argument("--root", required=True, type=Path)
    site_parser = commands.add_parser("stage-site", help="stage raw evidence for the static site")
    site_parser.add_argument("--root", required=True, type=Path)
    site_parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.source_root, args.root)
    elif args.command == "verify":
        result = verify(args.root)
    elif args.command == "hydrate":
        result = hydrate(args.root)
    else:
        result = stage_site(args.root, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublicationEvidenceError as exc:
        print(f"publication evidence refused: {exc}", file=sys.stderr)
        raise SystemExit(1)
