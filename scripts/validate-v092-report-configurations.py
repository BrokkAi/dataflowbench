#!/usr/bin/env python3
"""Run the pinned harness configuration check in an isolated fresh source tree.

This final gate consumes already-verified v0.9.2 execution evidence. It does
not execute analyzers, create a freeze, or publish results. By default it only
checks readiness; ``--execute`` creates one append-only validation namespace.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import datetime as _datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.9.2"
CONTRACT = PurePosixPath("reports/releases/v0.9.2/execution-v1/contract.json")
V0151_SELECTOR = PurePosixPath("scripts/select-v092-publication-evidence.py")
V0151_WRAPPER = PurePosixPath("scripts/bifrost_v0151_benchmark.py")
V0151_CORE = PurePosixPath("scripts/bifrost_v0144_benchmark.py")
JOERN_PROJECTION_HELPER = PurePosixPath("scripts/joern_v092_publication_projection.py")
JOERN_EXPORTER_HELPER = PurePosixPath("scripts/joern_normal_reports_v092_projection.py")
V0151_CONTRACT = PurePosixPath(
    "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json"
)
CHECKOUTS = PurePosixPath("execution-state/v092/validation")
RECEIPTS = PurePosixPath("reports/releases/v0.9.2/validation")
ATTEMPTS = PurePosixPath("reports/releases/v0.9.2/attempts")
EXPECTED_GROUPS = 84
EXPECTED_REPORTS = 92
EXPECTED_ROWS = 4252
EXPECTED_CASES = 1108
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_TREE_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
NAMESPACE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
VALIDATED_RE = re.compile(r"validated ([0-9]+) reports\Z")
CONFIG_RE = re.compile(
    r"checked ([0-9]+) configuration hashes against the working tree "
    r"\(([0-9]+) known-stale under issue #138\)\Z"
)


class ValidationEvidenceError(ValueError):
    """The release report or canonical validation evidence is invalid."""


def _load_module(path: Path, name: str):
    source = path.read_bytes()
    source_sha256 = hashlib.sha256(source).hexdigest()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    module.__cached__ = None
    prior = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
        raise
    if hashlib.sha256(path.read_bytes()).hexdigest() != source_sha256:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
        raise RuntimeError(f"validation dependency changed while loading: {path}")
    return module


def _load_current_python_source(root: Path, relative: PurePosixPath, name: str):
    """Execute the exact current Python bytes so mode identities cannot use stale bytecode."""
    path = root / Path(*relative.parts)
    _require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
             f"required v0.15.1 preflight source is missing or unsafe: {relative}")
    source = path.read_bytes()
    digest = _sha(source)
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    _require(_sha(path.read_bytes()) == digest,
             f"v0.15.1 preflight source changed while loading: {relative}")
    return module, {"path": relative.as_posix(), "sha256": digest}


CHECKER = _load_module(Path(__file__).with_name("check-release-v092.py"), "check_release_v092_for_config_validation")
EXECUTOR = CHECKER.EXECUTOR
JOERN_PROJECTION = _load_module(
    Path(__file__).with_name("joern_v092_publication_projection.py"),
    "joern_v092_publication_projection_for_validation",
)

JOERN108_ADAPTERS = {
    "joern-swift-core.json",
    "joern-swift-modeling.json",
    "joern-swift-calibration.json",
    "joern-swift-native.json",
    "joern-swift-language-extension.json",
}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_LOADED_SOURCE_SHA = {
    "helper": _sha(Path(__file__).resolve().read_bytes()),
    "checker": _sha(Path(CHECKER.__file__).resolve().read_bytes()),
    "executor": _sha(Path(EXECUTOR.__file__).resolve().read_bytes()),
}


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _utc_now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationEvidenceError(message)


def _namespace(value: object) -> str:
    _require(isinstance(value, str) and NAMESPACE.fullmatch(value) is not None and value not in (".", ".."),
             "output must be a new simple namespace name")
    return value


def _relative(value: object, description: str) -> PurePosixPath:
    _require(isinstance(value, str) and bool(value) and "\\" not in value and "\x00" not in value,
             f"{description} must be a non-empty canonical relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and path.as_posix() == value and
             all(part not in ("", ".", "..") for part in path.parts),
             f"{description} is absolute, non-canonical, or escapes its root")
    return path


def _read_under(root: Path, relative: object, description: str) -> bytes:
    path = _relative(relative, description)
    root = root.resolve(strict=True)
    current = root
    for part in path.parts:
        current = current / part
        _require(not current.is_symlink(), f"symlink in {description}: {current}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ValidationEvidenceError(f"{description} escapes or is missing below {root}: {path}") from exc
    _require(resolved.is_file(), f"{description} is not a regular file: {path}")
    try:
        return resolved.read_bytes()
    except OSError as exc:
        raise ValidationEvidenceError(f"cannot read {description}: {path}: {exc}") from exc


def _ensure_directory(root: Path, relative: PurePosixPath, *, create: bool) -> Path:
    root = root.resolve()
    current = root
    for part in relative.parts:
        current = current / part
        _require(not current.is_symlink(), f"symlink in validation output path: {current}")
        if current.exists():
            _require(current.is_dir(), f"validation output component is not a directory: {current}")
        elif create:
            try:
                current.mkdir()
            except OSError as exc:
                raise ValidationEvidenceError(f"cannot create validation output directory {current}: {exc}") from exc
    return current


def _write_new(path: Path, data: bytes) -> None:
    _require(not path.exists() and not path.is_symlink(), f"append-only validation artifact already exists: {path}")
    try:
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except OSError as exc:
        raise ValidationEvidenceError(f"cannot write validation artifact {path}: {exc}") from exc


def _validate_checker_summary(summary: object) -> dict:
    _require(isinstance(summary, dict) and summary.get("status") == "fresh-evidence-verified",
             "fresh v0.9.2 matrix evidence did not pass its independent checker")
    for key, expected in (
        ("fresh_groups", EXPECTED_GROUPS),
        ("fresh_partitions", EXPECTED_REPORTS),
        ("fresh_rows", EXPECTED_ROWS),
        ("case_count", EXPECTED_CASES),
        ("carried_partitions", 0),
        ("carried_rows", 0),
    ):
        _require(summary.get(key) == expected, f"checker summary {key} is not the required fresh matrix value")
    _require(isinstance(summary.get("fresh_reports"), list) and
             len(summary["fresh_reports"]) == EXPECTED_REPORTS,
             "checker summary does not contain exactly 92 fresh reports")
    _require(isinstance(summary.get("selected_attempts"), list) and
             len(summary["selected_attempts"]) == EXPECTED_GROUPS,
             "checker summary does not contain one selected attempt for all 84 groups")
    selected_ids = set()
    for item in summary["selected_attempts"]:
        _require(isinstance(item, dict) and item.get("status") == "completed" and
                 isinstance(item.get("attempt_id"), str) and
                 isinstance(item.get("completed_receipt_sha256"), str) and
                 SHA256.fullmatch(item["completed_receipt_sha256"]) is not None,
                 "checker summary contains an invalid selected attempt receipt binding")
        selected_ids.add(item["attempt_id"])
    _require(len(selected_ids) == EXPECTED_GROUPS,
             "checker summary selected attempt IDs are not unique")
    _require(isinstance(summary.get("configuration_hash_validation"), dict) and
             summary["configuration_hash_validation"].get("canonical_rust_validate_reports") ==
             "required separate final-delivery gate",
             "checker summary does not preserve the separate canonical configuration-validation gate")
    return summary


def _safe_output_target(root: Path, relative: PurePosixPath) -> Path:
    root = root.resolve(strict=True)
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        _require(not current.is_symlink(), f"symlink in projected validation path: {current}")
        if not current.exists():
            current.mkdir()
        _require(current.is_dir(), f"projected validation parent is not a directory: {current}")
    target = current / relative.name
    _require(not target.exists() and not target.is_symlink(),
             f"projection collides with an existing source or report path: {relative}")
    try:
        target.parent.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise ValidationEvidenceError(f"projected validation path escapes its checkout: {relative}") from exc
    return target


def _attempt_report_receipt(
    root: Path, attempt_id: str, staged_path: str, staged_sha256: str,
    expected_receipt_sha256: str,
) -> tuple[dict, str]:
    _require(isinstance(attempt_id, str) and NAMESPACE.fullmatch(attempt_id) is not None,
             "report binding has a malformed attempt id")
    receipt_relative = (ATTEMPTS / attempt_id / "completed.json").as_posix()
    raw = _read_under(root, receipt_relative, "selected completed attempt receipt")
    receipt_sha256 = _sha(raw)
    _require(receipt_sha256 == expected_receipt_sha256,
             f"selected attempt receipt changed after checker verification: {attempt_id}")
    try:
        receipt = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationEvidenceError(f"selected completed attempt receipt is invalid JSON: {attempt_id}") from exc
    _require(isinstance(receipt, dict) and receipt.get("status") == "completed" and
             receipt.get("attempt_id") == attempt_id,
             f"selected attempt receipt is not a completed attempt: {attempt_id}")
    rows = receipt.get("reports")
    _require(isinstance(rows, list), f"selected attempt has no report receipt list: {attempt_id}")
    matches = [row for row in rows if isinstance(row, dict) and row.get("staged_path") == staged_path]
    _require(len(matches) == 1, f"selected attempt does not bind exactly one staged report: {staged_path}")
    report_receipt = matches[0]
    _require(report_receipt.get("staged_sha256") == staged_sha256,
             f"selected attempt report receipt disagrees with checker summary: {staged_path}")
    return report_receipt, receipt_sha256


def _paths_conflict(left: PurePosixPath, right: PurePosixPath) -> bool:
    return left == right or left in right.parents or right in left.parents


def _joern_projection_bindings(root: Path, summary: dict) -> tuple[dict | None, dict[str, dict]]:
    bindings = summary.get("fresh_reports")
    _require(isinstance(bindings, list), "checker summary report bindings are malformed")
    derived = [binding for binding in bindings if isinstance(binding, dict) and
               ("original_staged" in binding or "metadata_projection" in binding)]
    reference = summary.get("joern_metadata_projection")
    if not derived:
        _require(reference is None,
                 "Joern projection manifest is present without derived report bindings")
        return None, {}
    _require(len(derived) == len(JOERN108_ADAPTERS),
             "metadata-derived reports must cover exactly the five Joern108 partitions")
    _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"} and
             reference.get("path") == JOERN_PROJECTION.PUBLICATION_PROJECTION_MANIFEST and
             isinstance(reference.get("sha256"), str) and SHA256.fullmatch(reference["sha256"]) is not None,
             "derived Joern reports lack the exact metadata-projection manifest reference")
    manifest = JOERN_PROJECTION.verify_existing_projection(root, reference)
    _require(manifest.get("schema") == "v092-joern108-publication-projection/v1" and
             manifest.get("status") == "verified-derived-report-metadata" and
             manifest.get("attempt_id") == JOERN_PROJECTION.ATTEMPT_ID and
             manifest.get("group_id") == JOERN_PROJECTION.GROUP_ID and
             manifest.get("case_count") == 108 and manifest.get("report_count") == 5 and
             manifest.get("scored_activation") is False and
             manifest.get("configuration_ready") is False and
             manifest.get("full_release_gate_satisfied") is False and
             manifest.get("publication_approved") is False,
             "Joern metadata projection manifest identity or scope differs")
    report_rows = manifest.get("reports")
    _require(isinstance(report_rows, list) and len(report_rows) == 5,
             "Joern metadata projection manifest must bind exactly five reports")
    by_name = {}
    for item in report_rows:
        _require(isinstance(item, dict) and isinstance(item.get("staged"), dict),
                 "Joern projection manifest contains a malformed original staged binding")
        original_path = _relative(item["staged"].get("path"), "original Joern staged report")
        name = original_path.name
        _require(name in JOERN108_ADAPTERS and name not in by_name,
                 "Joern projection manifest contains a duplicate or unknown report partition")
        projected_path = _relative(item.get("path"), "derived Joern metadata report")
        _require(projected_path.as_posix() ==
                 (PurePosixPath(JOERN_PROJECTION.PUBLICATION_PROJECTION_DIRECTORY) / name).as_posix(),
                 "derived Joern report path differs from the fixed publication projection")
        by_name[name] = item
    _require(set(by_name) == JOERN108_ADAPTERS,
             "Joern metadata projection manifest does not cover the exact five adapters")
    derived_names = set()
    for binding in derived:
        _require(isinstance(binding.get("adapter"), str),
                 "derived Joern report adapter path is malformed")
        _require(binding.get("metadata_projection") == reference,
                 "derived Joern binding does not point to the exact top-level projection manifest")
        derived_names.add(_relative(binding["adapter"], "derived Joern adapter report").name)
    _require(derived_names == JOERN108_ADAPTERS,
             "derived Joern bindings do not cover the exact five adapters")
    return manifest, by_name


def _project_reports(
    root: Path,
    checkout: Path,
    summary: dict,
    *,
    expected_report_count: int = EXPECTED_REPORTS,
    expected_row_count: int = EXPECTED_ROWS,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Project verified staged reports and only their retained raw files."""
    root = root.resolve(strict=True)
    _require(checkout.is_dir() and not checkout.is_symlink(), "fresh source-only validation checkout is missing")
    bindings = summary.get("fresh_reports")
    _require(isinstance(bindings, list) and len(bindings) == expected_report_count,
             f"expected exactly {expected_report_count} checker-bound reports")
    selected_attempt_hashes = {
        item["attempt_id"]: item["completed_receipt_sha256"]
        for item in summary.get("selected_attempts", [])
        if isinstance(item, dict) and isinstance(item.get("attempt_id"), str)
    }
    _require(len(selected_attempt_hashes) == len(summary.get("selected_attempts", [])),
             "checker summary selected attempt receipt map is malformed")
    joern_projection, joern_projection_reports = _joern_projection_bindings(root, summary)
    derived_report_count = 0

    reports: list[dict] = []
    raw_by_path: dict[str, dict] = {}
    attempt_receipts: dict[str, dict] = {}
    report_targets: list[PurePosixPath] = []
    staged_sources: set[str] = set()
    original_staged_sources: set[str] = set()
    total_rows = 0
    for binding in bindings:
        _require(isinstance(binding, dict), "checker summary contains a malformed report binding")
        adapter = _relative(binding.get("adapter"), "normalized adapter report path")
        _require(adapter.parts[:4] == ("reports", "releases", "v0.9.2", "normal") and
                 len(adapter.parts) == 5,
                 f"normalized adapter report path is outside the v0.9.2 report set: {adapter}")
        report_name = adapter.name
        _require(report_name.endswith(".json") and report_name not in (".", ".."),
                 f"normalized adapter report has an invalid filename: {adapter}")
        destination_relative = PurePosixPath("reports") / report_name
        _require(destination_relative not in report_targets,
                 f"two adapter reports collide at {destination_relative}")
        report_targets.append(destination_relative)

        attempt_id = binding.get("attempt_id")
        staged_relative = _relative(binding.get("staged_path"), "attempt-staged report path")
        expected_original_staged = (
            PurePosixPath("reports/releases/v0.9.2/normal/attempts") /
            str(attempt_id) / adapter.relative_to("reports/releases/v0.9.2/normal")
        )
        derived_binding = "original_staged" in binding or "metadata_projection" in binding
        if derived_binding:
            _require(joern_projection is not None and adapter.name in JOERN108_ADAPTERS and
                     attempt_id == joern_projection.get("attempt_id"),
                     "metadata-derived report is outside the exact Joern108 attempt")
            original_ref = binding.get("original_staged")
            projection_ref = binding.get("metadata_projection")
            _require(isinstance(original_ref, dict) and set(original_ref) == {"path", "sha256"} and
                     isinstance(projection_ref, dict) and set(projection_ref) == {"path", "sha256"},
                     "derived Joern binding requires exact original_staged and metadata_projection refs")
            original_relative = _relative(original_ref.get("path"), "original staged report path")
            original_key = original_relative.as_posix()
            _require(original_relative == expected_original_staged and
                     original_key not in original_staged_sources,
                     "original_staged does not identify the exact selected attempt report")
            original_staged_sources.add(original_key)
            expected_manifest_report = joern_projection_reports[adapter.name]
            _require(projection_ref == summary.get("joern_metadata_projection") and
                     expected_manifest_report.get("path") == staged_relative.as_posix() and
                     expected_manifest_report.get("sha256") == binding.get("sha256") and
                     expected_manifest_report.get("staged") == original_ref and
                     expected_manifest_report.get("cases") == binding.get("rows"),
                     "derived Joern report refs differ from the verified projection manifest")
            original_staged_key = original_key
            original_staged_sha = original_ref["sha256"]
            derived_report_count += 1
        else:
            expected_staged = expected_original_staged
            _require(staged_relative == expected_staged,
                     f"staged report is not the selected attempt projection: {staged_relative}")
            original_staged_key = staged_relative.as_posix()
            original_staged_sha = binding.get("sha256")
        staged_key = staged_relative.as_posix()
        _require(staged_key not in staged_sources, f"duplicate staged report source: {staged_key}")
        staged_sources.add(staged_key)
        staged_sha = binding.get("sha256")
        _require(isinstance(staged_sha, str) and SHA256.fullmatch(staged_sha) is not None,
                 f"checker summary has an invalid report SHA-256: {adapter}")
        report_bytes = _read_under(root, staged_key, "selected normalized report")
        _require(_sha(report_bytes) == staged_sha,
                 f"selected normalized report changed after checker verification: {staged_key}")
        try:
            report_value = json.loads(report_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValidationEvidenceError(f"selected normalized report is invalid JSON: {staged_key}") from exc
        _require(isinstance(report_value, dict) and isinstance(report_value.get("results"), list),
                 f"selected normalized report has no result rows: {staged_key}")
        rows = report_value["results"]
        _require(type(binding.get("rows")) is int and len(rows) == binding["rows"],
                 f"selected normalized report row count changed: {staged_key}")
        total_rows += len(rows)

        _require(attempt_id in selected_attempt_hashes,
                 f"report binds an attempt absent from checker-selected receipts: {attempt_id}")
        _require(isinstance(original_staged_sha, str) and SHA256.fullmatch(original_staged_sha) is not None,
                 f"checker summary has an invalid original staged report SHA-256: {adapter}")
        report_receipt, receipt_sha = _attempt_report_receipt(
            root, attempt_id, original_staged_key, original_staged_sha,
            selected_attempt_hashes[attempt_id],
        )
        original_report_bytes = _read_under(root, original_staged_key, "original selected staged report")
        _require(_sha(original_report_bytes) == original_staged_sha,
                 f"original staged report changed after checker verification: {original_staged_key}")
        if derived_binding:
            try:
                original_report_value = json.loads(original_report_bytes)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise ValidationEvidenceError(
                    f"original staged Joern report is invalid JSON: {original_staged_key}"
                ) from exc
            _require(isinstance(original_report_value, dict) and
                     "configuration_hash" not in original_report_value and
                     report_value == dict(
                         original_report_value,
                         configuration_hash=joern_projection.get("configuration_hash"),
                     ),
                     "derived Joern report changes fields beyond configuration_hash")
        if attempt_id not in attempt_receipts:
            attempt_receipts[attempt_id] = {
                "attempt_id": attempt_id,
                "path": (ATTEMPTS / attempt_id / "completed.json").as_posix(),
                "sha256": receipt_sha,
            }
        else:
            _require(attempt_receipts[attempt_id]["sha256"] == receipt_sha,
                     f"selected attempt receipt changed while projecting reports: {attempt_id}")
        mappings = report_receipt.get("raw_output_mappings")
        _require(isinstance(mappings, list) and len(mappings) == len(rows),
                 f"selected attempt raw-output mappings do not cover {staged_key}")
        mapping_by_capture: dict[str, dict] = {}
        expected_prefix = (ATTEMPTS / attempt_id / "capture").as_posix() + "/"
        for mapping in mappings:
            _require(isinstance(mapping, dict), f"malformed raw-output mapping in {staged_key}")
            capture_relative = _relative(mapping.get("captured_path"), "captured raw-output path")
            capture_key = capture_relative.as_posix()
            _require(capture_key.startswith(expected_prefix),
                     f"raw-output path does not remain in its selected attempt capture: {capture_key}")
            execution_relative = _relative(mapping.get("execution_relative"), "captured execution-relative path")
            expected_capture = (ATTEMPTS / attempt_id / "capture" / execution_relative).as_posix()
            _require(capture_key == expected_capture,
                     f"captured raw-output path differs from its execution-relative path: {capture_key}")
            digest = mapping.get("sha256")
            size = mapping.get("bytes")
            _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None and
                     type(size) is int and size >= 0,
                     f"raw-output mapping has invalid digest or byte count: {capture_key}")
            _require(capture_key not in mapping_by_capture,
                     f"selected report repeats a raw-output path: {capture_key}")
            mapping_by_capture[capture_key] = mapping

        used: set[str] = set()
        for row in rows:
            _require(isinstance(row, dict), f"selected report contains a malformed result row: {staged_key}")
            _require(isinstance(row.get("case_id"), str),
                     f"selected report has a malformed case id: {staged_key}")
            raw_relative = _relative(row.get("raw_output"), "normalized raw_output reference").as_posix()
            mapping = mapping_by_capture.get(raw_relative)
            _require(mapping is not None, f"raw_output is not bound by its selected attempt receipt: {raw_relative}")
            _require(raw_relative not in used, f"result rows reuse one raw_output path: {raw_relative}")
            used.add(raw_relative)
            raw_bytes = _read_under(root, raw_relative, "retained raw output")
            digest = mapping["sha256"]
            size = mapping["bytes"]
            _require(len(raw_bytes) == size and _sha(raw_bytes) == digest,
                     f"retained raw output changed after checker verification: {raw_relative}")
            raw_posix = PurePosixPath(raw_relative)
            _require(not any(_paths_conflict(raw_posix, target) for target in report_targets),
                     f"raw_output collides with a projected report: {raw_relative}")
            prior = raw_by_path.get(raw_relative)
            if prior is not None:
                _require(prior["sha256"] == digest and prior["bytes"] == size,
                         f"conflicting raw-output path collision: {raw_relative}")
                prior["references"].append({"adapter": adapter.as_posix(), "case_id": row.get("case_id")})
            else:
                raw_by_path[raw_relative] = {
                    "relative_path": raw_relative,
                    "sha256": digest,
                    "bytes": size,
                    "references": [{"adapter": adapter.as_posix(), "case_id": row.get("case_id")}],
                }
        _require(used == set(mapping_by_capture),
                 f"raw-output receipt mappings are not a bijection for {staged_key}")

        target = _safe_output_target(checkout, destination_relative)
        _write_new(target, report_bytes)
        _require(_sha(target.read_bytes()) == staged_sha,
                 f"projected report copy changed bytes: {destination_relative}")
        reports.append({
            "adapter": adapter.as_posix(),
            "attempt_id": attempt_id,
            "attempt_number": binding.get("attempt_number"),
            "source_path": staged_key,
            **({"original_staged_path": original_staged_key} if derived_binding else {}),
            "validation_path": destination_relative.as_posix(),
            "sha256": staged_sha,
            "rows": len(rows),
        })

    _require((joern_projection is None and derived_report_count == 0) or
             (joern_projection is not None and derived_report_count == len(JOERN108_ADAPTERS)),
             "Joern metadata projection bindings are incomplete")
    _require(total_rows == expected_row_count,
             f"projected report rows total {total_rows}, expected {expected_row_count}")
    _require(set(attempt_receipts) == set(selected_attempt_hashes),
             "projected reports do not reference every checker-selected attempt receipt")
    for raw_relative, item in sorted(raw_by_path.items()):
        path = PurePosixPath(raw_relative)
        _require(not any(_paths_conflict(path, report_path) for report_path in report_targets),
                 f"raw-output path collides with a report destination: {raw_relative}")
        target = _safe_output_target(checkout, path)
        raw_bytes = _read_under(root, raw_relative, "retained raw output")
        _write_new(target, raw_bytes)
        _require(_sha(target.read_bytes()) == item["sha256"],
                 f"projected raw output copy changed bytes: {raw_relative}")

    return reports, [raw_by_path[path] for path in sorted(raw_by_path)], [attempt_receipts[path] for path in sorted(attempt_receipts)]


def _parse_stdout(stdout: bytes) -> dict:
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationEvidenceError("canonical validator stdout is not UTF-8") from exc
    validated_values = []
    checked_values = []
    for line in text.splitlines():
        match = VALIDATED_RE.fullmatch(line)
        if match:
            validated_values.append(int(match.group(1)))
        match = CONFIG_RE.fullmatch(line)
        if match:
            checked_values.append((int(match.group(1)), int(match.group(2))))
    _require(len(validated_values) == 1 and len(checked_values) == 1,
             "canonical validator stdout must contain one exact report-count line and one configuration-count line")
    validated_reports = validated_values[0]
    checked, known_stale = checked_values[0]
    _require(0 <= checked <= validated_reports,
             "canonical validator checked-configuration count exceeds its validated report count")
    return {
        "validated_reports": validated_reports,
        "checked_configuration_hashes": checked,
        "known_stale": known_stale,
        "not_derivable": validated_reports - checked,
    }


def _validation_success(exit_code: int | None, metrics: dict, expected_reports: int = EXPECTED_REPORTS) -> bool:
    if not isinstance(metrics, dict):
        return False
    validated = metrics.get("validated_reports")
    checked = metrics.get("checked_configuration_hashes")
    known_stale = metrics.get("known_stale")
    not_derivable = metrics.get("not_derivable")
    if any(type(value) is not int for value in (validated, checked, known_stale, not_derivable)):
        return False
    return (exit_code == 0 and validated == expected_reports and 0 < checked <= expected_reports and
            known_stale == 0 and not_derivable == expected_reports - checked)


def _invoke_runner(binding: dict, checkout: Path, environment: dict[str, str], timeout_seconds: int = 1800) -> dict:
    try:
        EXECUTOR._check_tool_file(binding, "runner")
    except EXECUTOR.ReleaseError as exc:
        raise ValidationEvidenceError(str(exc)) from exc
    binary = Path(binding["path"])
    _require(binary.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0,
             f"bound runner is not executable: {binary}")
    argv = [str(binary), "--population", "v0.9.0", "validate-reports"]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=checkout,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "argv": argv,
            "cwd": str(checkout),
            "environment": dict(environment),
            "exit_code": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_seconds": max(0.0, time.monotonic() - started),
            "invocation_error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": str(checkout),
            "environment": dict(environment),
            "exit_code": None,
            "timed_out": True,
            "stdout": exc.stdout or b"",
            "stderr": exc.stderr or b"",
            "duration_seconds": max(0.0, time.monotonic() - started),
            "invocation_error": f"timeout after {timeout_seconds} seconds",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "cwd": str(checkout),
            "environment": dict(environment),
            "exit_code": None,
            "timed_out": False,
            "stdout": b"",
            "stderr": b"",
            "duration_seconds": max(0.0, time.monotonic() - started),
            "invocation_error": f"{type(exc).__name__}: {exc}",
        }


def _source_identity(root: Path, validated: dict) -> dict:
    commit = validated["plan"]["source_commit"]
    try:
        tree_sha = subprocess.check_output(
            ["git", "rev-parse", f"{commit}^{{tree}}"], cwd=root,
            text=True, stderr=subprocess.PIPE,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationEvidenceError(f"cannot resolve exact source tree identity for {commit}") from exc
    _require(GIT_TREE_SHA1.fullmatch(tree_sha) is not None, "source commit did not resolve to an exact Git tree SHA-1")
    source_inputs = sorted(
        ({"path": item["path"], "sha256": item["sha256"]} for item in validated["source_inputs"]),
        key=lambda item: item["path"],
    )
    return {
        "commit": commit,
        "git_tree_sha1": tree_sha,
        "runner_source_sha256": validated["plan"]["runner_source_sha256"],
        "source_inputs_sha256": _sha(_canonical_json(source_inputs)),
        "source_input_count": len(source_inputs),
    }


def _helper_identities(
    extra_sources: dict[str, dict] | None = None,
    *,
    root: Path = ROOT,
) -> dict:
    checker_path = Path(CHECKER.__file__).resolve()
    executor_path = Path(EXECUTOR.__file__).resolve()
    helper_path = Path(__file__).resolve()
    current = {
        "helper": _sha(helper_path.read_bytes()),
        "checker": _sha(checker_path.read_bytes()),
        "executor": _sha(executor_path.read_bytes()),
    }
    _require(current == _LOADED_SOURCE_SHA,
             "validation helper, checker, or executor source changed after the code was loaded")
    identities = {
        "helper": {"path": helper_path.relative_to(ROOT).as_posix(), "sha256": current["helper"]},
        "checker": {"path": checker_path.relative_to(ROOT).as_posix(), "sha256": current["checker"]},
        "executor": {"path": executor_path.relative_to(ROOT).as_posix(), "sha256": current["executor"]},
    }
    for name, reference in (extra_sources or {}).items():
        _require(isinstance(name, str) and name in (
                     "selector", "target_wrapper", "target_core", "joern_projection", "joern_exporter",
                 ) and
                 isinstance(reference, dict) and set(reference) == {"path", "sha256"},
                 "v0.15.1 helper identity binding is malformed")
        relative = _relative(reference.get("path"), f"{name} source path")
        digest = reference.get("sha256")
        _require(isinstance(digest, str) and SHA256.fullmatch(digest) is not None,
                 f"{name} source SHA-256 is malformed")
        data = _read_under(root, relative.as_posix(), f"current {name} source")
        _require(_sha(data) == digest,
                 f"current {name} source changed after v0.15.1 preflight")
        identities[name] = {"path": relative.as_posix(), "sha256": digest}
    return identities


def _load_v0151_preflight_modules(root: Path) -> tuple[object, object, object, dict[str, dict]]:
    selector, selector_ref = _load_current_python_source(
        root, V0151_SELECTOR, f"v092_validation_selector_{os.getpid()}",
    )
    wrapper, wrapper_ref = _load_current_python_source(
        root, V0151_WRAPPER, f"v092_validation_v0151_wrapper_{os.getpid()}",
    )
    _require(getattr(wrapper, "CORE_SOURCE_REL", None) == V0151_CORE.as_posix(),
             "fixed v0.15.1 wrapper does not bind the registered C5 core")
    core, core_ref = _load_current_python_source(
        root, V0151_CORE, f"v092_validation_v0151_core_{os.getpid()}",
    )
    helper_refs = {}
    for key, relative in (("joern_projection", JOERN_PROJECTION_HELPER),
                          ("joern_exporter", JOERN_EXPORTER_HELPER)):
        raw = _read_under(root, relative.as_posix(), f"current {key} helper source")
        helper_refs[key] = {"path": relative.as_posix(), "sha256": _sha(raw)}
    return selector, wrapper, core, {
        "selector": selector_ref,
        "target_wrapper": wrapper_ref,
        "target_core": core_ref,
        **helper_refs,
    }


def _preflight_v0151(
    root: Path,
    contract_path: Path,
) -> tuple[dict, dict, dict, dict]:
    try:
        relative_contract = contract_path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValidationEvidenceError("v0.15.1 contract must be the fixed repository C6 path") from exc
    _require(relative_contract.as_posix() == V0151_CONTRACT.as_posix(),
             "v0.15.1 preflight accepts only the fixed C6 contract")
    try:
        selector, wrapper, core, source_refs = _load_v0151_preflight_modules(root)
        _require(getattr(selector, "V0151_CONTRACT_REL", None) == V0151_CONTRACT.as_posix() and
                 getattr(selector, "V0151_WRAPPER_REL", None) == V0151_WRAPPER.as_posix(),
                 "publication selector target differs from the fixed v0.15.1 contract")
        identity = getattr(wrapper, "PINNED_IDENTITY", {})
        _require(isinstance(identity, Mapping) and identity.get("target_id") == "bifrost-v0151-01" and
                 identity.get("version") == "0.15.1" and
                 getattr(wrapper, "CORE_SOURCE_REL", None) == V0151_CORE.as_posix(),
                 "loaded v0.15.1 wrapper target identity differs")
        profile = wrapper.load_target_profile(core)
        core.configure_target_profile(profile)
        _require(getattr(core, "TARGET_ID", None) == "bifrost-v0151-01" and
                 getattr(core, "BIFROST_VERSION", None) == "0.15.1" and
                 getattr(core, "SERIES", None) == 4 and
                 getattr(core, "SERIES_LABEL", None) == "series-04" and
                 getattr(core, "CONTRACT_REL", None) == V0151_CONTRACT.as_posix(),
                 "configured C6 core target is not the fixed v0.15.1 series04 contract")
        c6 = core._validate_contract(
            root,
            V0151_CONTRACT.as_posix(),
            require_approval=True,
            require_committed=True,
            check_current_source=True,
        )
        _require(isinstance(c6, dict) and isinstance(c6.get("contract"), dict),
                 "fixed C6 validator returned no validated contract")
        contract = c6["contract"]
        snapshot = contract.get("source_snapshot")
        runtime = contract.get("runtime")
        _require(isinstance(snapshot, dict) and isinstance(runtime, dict),
                 "fixed C6 source or runtime snapshot is malformed")
        source_commit = c6.get("source_commit")
        _require(isinstance(source_commit, str) and GIT_TREE_SHA1.fullmatch(source_commit) is not None and
                 snapshot.get("source_commit") == source_commit,
                 "validated C6 source commit differs from its contract snapshot")
        runner_source = snapshot.get("runner_source")
        runner_source_sha = runner_source.get("sha256") if isinstance(runner_source, dict) else None
        _require(isinstance(runner_source, dict) and
                 runner_source.get("path") == V0151_WRAPPER.as_posix() and
                 isinstance(runner_source_sha, str) and SHA256.fullmatch(runner_source_sha) is not None,
                 "validated C6 contract lacks the exact wrapper runner-source binding")
        _require(source_refs.get("target_wrapper", {}).get("sha256") == runner_source_sha,
                 "loaded v0.15.1 wrapper bytes differ from the C6 runner-source binding")
        source_inputs = snapshot.get("source_inputs")
        _require(isinstance(source_inputs, list) and source_inputs,
                 "validated C6 contract lacks its source input closure")
        source_map = {}
        for item in source_inputs:
            _require(isinstance(item, dict) and isinstance(item.get("path"), str) and
                     isinstance(item.get("sha256"), str) and SHA256.fullmatch(item["sha256"]) is not None and
                     item["path"] not in source_map,
                     "validated C6 source input closure is malformed or duplicated")
            source_map[item["path"]] = item["sha256"]
        expected_source_ref_names = {
            "selector", "target_wrapper", "target_core", "joern_projection", "joern_exporter",
        }
        _require(isinstance(source_refs, dict) and set(source_refs) == expected_source_ref_names,
                 "loaded v0.15.1 preflight source roster differs from the fixed selector/helper set")
        for source_name, reference in source_refs.items():
            _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"} and
                     isinstance(reference.get("path"), str) and
                     isinstance(reference.get("sha256"), str) and
                     source_map.get(reference["path"]) == reference["sha256"],
                     f"C6 source inputs do not bind the loaded {source_name} source")
        _require(source_map.get(V0151_WRAPPER.as_posix()) == runner_source_sha,
                 "validated C6 source inputs do not bind its exact wrapper runner source")
        runner = runtime.get("runner")
        _require(isinstance(runner, dict) and isinstance(runner.get("path"), str) and
                 isinstance(runner.get("sha256"), str) and SHA256.fullmatch(runner["sha256"]) is not None and
                 c6.get("runner_path") == runner["path"],
                 "validated C6 contract runtime.runner binding is malformed")
        contract_sha = c6.get("contract_sha256")
        _require(isinstance(contract_sha, str) and SHA256.fullmatch(contract_sha) is not None,
                 "validated C6 contract digest is malformed")
        _require(_sha(_read_under(root, V0151_CONTRACT.as_posix(), "fixed C6 contract")) == contract_sha,
                 "validated C6 contract digest differs from its fixed path")

        # Use the actual selector API; its evidence result is never supplied by a caller.
        checker_summary = _validate_checker_summary(selector.select_evidence(root))
        _require(checker_summary.get("schema") == selector.SUMMARY_SCHEMA and
                 checker_summary.get("scoring_enabled") is False and
                 checker_summary.get("publication_approved") is False,
                 "v0.15.1 selector returned a summary outside the fixed unscored evidence scope")
    except ValidationEvidenceError:
        raise
    except Exception as exc:
        raise ValidationEvidenceError(f"v0.15.1 evidence preflight failed: {exc}") from exc

    validated = {
        "plan": {
            "source_commit": source_commit,
            "runner_source_sha256": runner_source_sha,
        },
        "source_inputs": source_inputs,
        "tools": {"runner": runner},
        "bytes_sha256": contract_sha,
    }
    context = {
        "mode": "v0151",
        "contract_path": V0151_CONTRACT.as_posix(),
        "contract_sha256": contract_sha,
        "selection_summary_sha256": _sha(_canonical_json(checker_summary)),
        "selector_status": checker_summary["status"],
        "source_modules": source_refs,
    }
    validated["_validation_context"] = context
    try:
        EXECUTOR._check_tool_file(runner, "v0.15.1 bound runner")
    except EXECUTOR.ReleaseError as exc:
        raise ValidationEvidenceError(str(exc)) from exc
    binary = Path(runner["path"])
    _require(binary.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0,
             f"bound runner is not executable: {binary}")
    return checker_summary, validated, runner, _source_identity(root, validated)


def _preflight(root: Path, contract_path: Path, *, evidence_source: str = "c4") -> tuple[dict, dict, dict, dict]:
    if evidence_source == "v0151":
        return _preflight_v0151(root, contract_path)
    _require(evidence_source == "c4", "validation evidence source must be c4 or v0151")
    try:
        checker_summary = CHECKER.verify(root, contract_path)
        checker_summary = _validate_checker_summary(checker_summary)
        validated = EXECUTOR.validate_plan(contract_path, repo_root=root)
    except (CHECKER.EvidenceError, EXECUTOR.ReleaseError) as exc:
        raise ValidationEvidenceError(str(exc)) from exc
    runner = validated["tools"].get("runner")
    _require(isinstance(runner, dict), "execution contract does not bind tools.runner")
    try:
        EXECUTOR._check_tool_file(runner, "runner")
    except EXECUTOR.ReleaseError as exc:
        raise ValidationEvidenceError(str(exc)) from exc
    binary = Path(runner["path"])
    _require(binary.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0,
             f"bound runner is not executable: {binary}")
    return checker_summary, validated, runner, _source_identity(root, validated)


def validate(
    *,
    root: str | Path = ROOT,
    contract_path: str | Path | None = None,
    output: str,
    execute: bool = False,
    evidence_source: str = "c4",
) -> dict:
    root = Path(root).resolve(strict=True)
    namespace = _namespace(output)
    _require(evidence_source in ("c4", "v0151"), "evidence_source must be c4 or v0151")
    expected_contract = CONTRACT if evidence_source == "c4" else V0151_CONTRACT
    contract = Path(contract_path) if contract_path is not None else Path(*expected_contract.parts)
    if not contract.is_absolute():
        contract = root / contract
    contract = contract.resolve(strict=True)
    if evidence_source == "v0151":
        _require(contract.relative_to(root).as_posix() == V0151_CONTRACT.as_posix(),
                 "v0.15.1 preflight accepts only the fixed C6 contract")
    checker_summary, validated, runner, source_identity = _preflight(
        root, contract, evidence_source=evidence_source,
    )
    checkout_relative = CHECKOUTS / namespace
    receipt_relative = RECEIPTS / namespace
    checkout = root / Path(*checkout_relative.parts)
    receipt_directory = root / Path(*receipt_relative.parts)
    _require(not checkout.exists() and not checkout.is_symlink(),
             f"source-only validation checkout already exists: {checkout}")
    _require(not receipt_directory.exists() and not receipt_directory.is_symlink(),
             f"append-only validation receipt namespace already exists: {receipt_directory}")

    metadata = {
        "schema_version": 1,
        "release": RELEASE,
        "namespace": namespace,
        "contract": {"path": contract.relative_to(root).as_posix(), "sha256": validated["bytes_sha256"]},
        "source_identity": source_identity,
        "runner": {"path": runner["path"], "sha256": runner["sha256"]},
        "checker_summary": {
            "sha256": _sha(_canonical_json(checker_summary)),
            "status": checker_summary["status"],
            "fresh_groups": checker_summary["fresh_groups"],
            "fresh_reports": checker_summary["fresh_partitions"],
            "fresh_rows": checker_summary["fresh_rows"],
            "carried_rows": checker_summary["carried_rows"],
        },
        "helper_identities": _helper_identities(
            validated.get("_validation_context", {}).get("source_modules"),
            root=root,
        ),
        "planned_checkout": checkout_relative.as_posix(),
        "planned_receipt": (receipt_relative / "receipt.json").as_posix(),
        "execution_requested": bool(execute),
    }
    validation_context = validated.get("_validation_context")
    if validation_context is not None:
        metadata["evidence_source"] = "v0151"
        metadata["selector"] = {
            "path": V0151_SELECTOR.as_posix(),
            "sha256": validation_context["source_modules"]["selector"]["sha256"],
            "status": validation_context["selector_status"],
            "summary_sha256": validation_context["selection_summary_sha256"],
        }
        metadata["target_contract"] = {
            "path": validation_context["contract_path"],
            "sha256": validation_context["contract_sha256"],
        }
    if not execute:
        return {"status": "ready-to-execute", **metadata}

    _ensure_directory(root, checkout_relative.parent, create=True)
    _ensure_directory(root, receipt_relative.parent, create=True)
    try:
        receipt_directory.mkdir()
    except OSError as exc:
        raise ValidationEvidenceError(f"cannot allocate fresh validation namespace {namespace}: {exc}") from exc

    started_utc = _utc_now()
    started = time.monotonic()
    receipt = {
        **metadata,
        "status": "failed",
        "started_at_utc": started_utc,
        "ended_at_utc": None,
        "duration_seconds": None,
        "checkout": str(checkout),
        "command": [str(runner["path"]), "--population", "v0.9.0", "validate-reports"],
        "cwd": str(checkout),
        "environment": None,
        "exit_code": None,
        "timed_out": False,
        "stdout": None,
        "stderr": None,
        "stdout_parse_error": None,
        "metrics": None,
        "reports": [],
        "raw_files": [],
        "attempt_receipts": [],
        "error": None,
    }
    stdout = b""
    stderr = b""
    try:
        explicit = [item["path"] for item in validated["source_inputs"]]
        EXECUTOR._materialize_source(root, source_identity["commit"], checkout, explicit)
        reports, raw_files, attempt_receipts = _project_reports(root, checkout, checker_summary)
        receipt["reports"] = reports
        receipt["raw_files"] = raw_files
        receipt["attempt_receipts"] = attempt_receipts

        environment = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(checkout),
            "TMPDIR": str(checkout),
            "LANG": "C",
            "LC_ALL": "C",
            "NO_COLOR": "1",
        }
        invocation = _invoke_runner(runner, checkout, environment)
        receipt["command"] = invocation["argv"]
        receipt["cwd"] = invocation["cwd"]
        receipt["environment"] = invocation["environment"]
        receipt["exit_code"] = invocation["exit_code"]
        receipt["timed_out"] = invocation["timed_out"]
        receipt["duration_seconds"] = invocation["duration_seconds"]
        stdout = invocation["stdout"]
        stderr = invocation["stderr"]
        if invocation["invocation_error"]:
            receipt["error"] = invocation["invocation_error"]
        try:
            metrics = _parse_stdout(stdout)
            receipt["metrics"] = metrics
        except ValidationEvidenceError as exc:
            receipt["stdout_parse_error"] = str(exc)
            metrics = None

        try:
            EXECUTOR._check_tool_file(runner, "runner after canonical validation")
            receipt["runner_sha256_after"] = _sha(Path(runner["path"]).read_bytes())
            _require(receipt["runner_sha256_after"] == runner["sha256"],
                     "bound runner bytes changed during canonical validation")
        except EXECUTOR.ReleaseError as exc:
            receipt["error"] = str(exc)
        except ValidationEvidenceError as exc:
            receipt["error"] = str(exc)
        if metrics is not None and not receipt["error"] and _validation_success(
            receipt["exit_code"], metrics,
        ):
            receipt["status"] = "canonical-validation-passed"
        elif not receipt["error"] and not receipt["stdout_parse_error"]:
            receipt["error"] = "canonical validate-reports exit status or stdout metrics failed the registered gate"
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        receipt["ended_at_utc"] = _utc_now()
        receipt["duration_seconds"] = max(0.0, time.monotonic() - started)
        receipt["stdout"] = {
            "path": "stdout.bin",
            "sha256": _sha(stdout),
            "bytes": len(stdout),
            "utf8": stdout.decode("utf-8", errors="replace"),
        }
        receipt["stderr"] = {
            "path": "stderr.bin",
            "sha256": _sha(stderr),
            "bytes": len(stderr),
            "utf8": stderr.decode("utf-8", errors="replace"),
        }
        _write_new(receipt_directory / "stdout.bin", stdout)
        _write_new(receipt_directory / "stderr.bin", stderr)
        _write_new(receipt_directory / "receipt.json", _json_bytes(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path,
                        help="C4 contract path; v0.15.1 mode always uses its fixed C6 contract")
    parser.add_argument(
        "--output", required=True,
        help="new namespace name (receipts go under reports/releases/v0.9.2/validation/<name>/)",
    )
    parser.add_argument(
        "--v0151", action="store_true",
        help="select retained evidence and validate against the fixed approved v0.15.1 C6 contract",
    )
    parser.add_argument("--execute", action="store_true", help="materialize the fresh checkout and run the pinned validator")
    args = parser.parse_args(argv)
    try:
        result = validate(
            contract_path=args.contract,
            output=args.output,
            execute=args.execute,
            evidence_source="v0151" if args.v0151 else "c4",
        )
    except (ValidationEvidenceError, OSError, ValueError, EXECUTOR.ReleaseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({key: result.get(key) for key in (
        "status", "planned_checkout", "planned_receipt", "exit_code", "metrics", "error",
    )}, sort_keys=True))
    return 0 if result["status"] in ("ready-to-execute", "canonical-validation-passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
