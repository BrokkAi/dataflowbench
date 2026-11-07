#!/usr/bin/env python3
"""Verify the v0.9.2 publication freeze and generated result artifacts.

The gate validates the immutable publication manifest, then performs release
checks in a disposable sparse clone. It never hydrates historical release
captures and has no command that pushes a tag or publishes a release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Sequence


RELEASE = "v0.9.2"
REQUIRED_REMOTE = "https://github.com/BrokkAi/dataflowbench.git"
REMOTE_NAME = "release-github"
PUBLICATION_DIR = "reports/releases/v0.9.2/publication-v1"
PUBLICATION_MANIFEST = f"{PUBLICATION_DIR}/manifest.json"
QUALIFICATION_SIDECAR = f"{PUBLICATION_DIR}/qualification-sidecar.json"
PUBLICATION_CAPTURE = f"{PUBLICATION_DIR}/capture"
PUBLICATION_BUNDLE = "evidence-delivery/v0.9.2-publication-01/detail"
MAPPER = "scripts/v092_publication_evidence.py"
LEDGER_HYDRATOR = "scripts/v092_ledger_archive.py"
LEDGER_ARCHIVE_INCLUDE = "reports/releases/v0.9.2/ledger-archives/ledger-151-01/ledger-v1.jsonl.gz"
CAPTURE_LFS_INCLUDE = f"{PUBLICATION_BUNDLE}/**"
EXPECTED_COUNTS = {
    "groups": 84,
    "reports": 92,
    "rows": 4_252,
    "unique_case_ids": 1_108,
    "raw_files": 4_252,
    "selected_source_reports": 5,
}
EXPECTED_QUALIFICATION = {
    "publication": {
        "publication_approved": False,
        "full_release_gate_satisfied": False,
        "freeze_created": False,
        "scoring_enabled": False,
        "scorecard_generation_allowed": False,
    },
    "bifrost_v0151": {
        "full_policy_qualification": False,
        "scoring_permitted": False,
    },
    "joern_swift_common108": {
        "inconclusive": 96,
        "unsupported": 12,
        "aggregate_resource_qualification": "unavailable",
        "semantic_qualification": "unavailable",
        "evidence_scope": "semantic-only",
        "scored_activation": False,
        "scoring_permitted": False,
        "timing_certified": False,
    },
}
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class GateError(RuntimeError):
    """A release gate assertion failed."""


def _describe(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )
    except OSError as exc:
        raise GateError(f"could not run {_describe(command)}: {exc}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if len(detail) > 2_000:
            detail = detail[-2_000:]
        suffix = f": {detail}" if detail else ""
        raise GateError(f"command failed ({result.returncode}): {_describe(command)}{suffix}")
    return result


def _git(
    checkout: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    enable_lfs_smudge: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if enable_lfs_smudge:
        env.pop("GIT_LFS_SKIP_SMUDGE", None)
    else:
        env["GIT_LFS_SKIP_SMUDGE"] = "1"
    return _run(["git", "-C", str(checkout), *args], check=check, env=env)


def _git_output(checkout: Path, args: Sequence[str]) -> str:
    return _git(checkout, args).stdout.strip()


def _read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{description} must be a JSON object: {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _same_json_value(actual: object, expected: object) -> bool:
    """Compare pinned JSON values without Python's bool/int equality overlap."""
    if type(expected) is dict:
        return (
            type(actual) is dict
            and set(actual) == set(expected)
            and all(_same_json_value(actual[key], expected[key]) for key in expected)
        )
    if type(expected) is list:
        return (
            type(actual) is list
            and len(actual) == len(expected)
            and all(_same_json_value(left, right) for left, right in zip(actual, expected))
        )
    return type(actual) is type(expected) and actual == expected


def _safe_repo_path(value: object, description: str) -> str:
    if not isinstance(value, str) or not value:
        raise GateError(f"{description} must be a non-empty repository-relative path")
    if value.startswith("/") or "\\" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise GateError(f"{description} is not a safe repository-relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise GateError(f"{description} is not a safe repository-relative path: {value!r}")
    return path.as_posix()


def _read_bound_file(root: Path, record: object, description: str) -> bytes:
    if not isinstance(record, dict):
        raise GateError(f"{description} must be a path/hash/bytes object")
    path = _safe_repo_path(record.get("path"), f"{description}.path")
    expected_sha = record.get("sha256")
    expected_bytes = record.get("bytes")
    if not isinstance(expected_sha, str) or not HEX_SHA256.fullmatch(expected_sha):
        raise GateError(f"{description}.sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes < 0:
        raise GateError(f"{description}.bytes must be a non-negative integer")
    target = root / path
    cursor = root
    for part in PurePosixPath(path).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise GateError(f"{description} traverses a symlink: {path}")
    if not target.is_file():
        raise GateError(f"{description} is missing or is not a regular file: {path}")
    data = target.read_bytes()
    if len(data) != expected_bytes or _sha256(data) != expected_sha:
        raise GateError(f"{description} bytes do not match the manifest: {path}")
    return data


def _validate_qualification(root: Path, manifest: dict) -> dict:
    binding = manifest.get("qualification_sidecar")
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256", "bytes"}:
        raise GateError("publication manifest is missing qualification_sidecar binding")
    if binding.get("path") != QUALIFICATION_SIDECAR:
        raise GateError("qualification sidecar path is not the fixed v0.9.2 publication path")
    sidecar_bytes = _read_bound_file(root, binding, "qualification_sidecar")
    try:
        sidecar = json.loads(sidecar_bytes)
    except json.JSONDecodeError as exc:
        raise GateError(f"qualification sidecar is not valid JSON: {exc}") from exc
    if (
        not isinstance(sidecar, dict)
        or set(sidecar)
        != {
            "schema",
            "publication",
            "bifrost_v0151",
            "joern_swift_common108",
            "source_joern_sidecar",
            "source_joern_sidecar_json",
            "joern_metadata_lift",
        }
        or sidecar.get("schema") != "dataflowbench-v0.9.2-publication-qualification-boundary/v1"
    ):
        raise GateError("qualification sidecar has an unsupported schema")
    for section, expected in EXPECTED_QUALIFICATION.items():
        actual = sidecar.get(section)
        if not _same_json_value(actual, expected):
            raise GateError(f"qualification sidecar does not retain required {section} limits")
    source_ref = sidecar.get("source_joern_sidecar")
    sources = manifest.get("sources")
    if (
        not isinstance(source_ref, dict)
        or set(source_ref) != {"path", "sha256", "bytes"}
        or not isinstance(sources, dict)
    ):
        raise GateError("qualification sidecar does not bind the original Joern metadata sidecar")
    if not _same_json_value(source_ref, sources.get("joern_metadata_sidecar")):
        raise GateError("embedded Joern source reference differs from the publication manifest")
    raw_text = sidecar.get("source_joern_sidecar_json")
    lift = sidecar.get("joern_metadata_lift")
    if not isinstance(raw_text, str) or not isinstance(lift, dict):
        raise GateError("qualification sidecar is missing original Joern sidecar bytes/object")
    raw_bytes = raw_text.encode("utf-8")
    if _sha256(raw_bytes) != source_ref.get("sha256"):
        raise GateError("embedded original Joern sidecar bytes do not match the pinned source digest")
    try:
        original = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise GateError(f"embedded original Joern sidecar is invalid JSON: {exc}") from exc
    if not _same_json_value(original, lift):
        raise GateError("embedded original Joern sidecar JSON differs from metadata_lift object")
    expected_lift_boundary = {
        "evidence_scope": "semantic-only",
        "removed_top_level_fields": {
            "aggregate_resource_qualification": "unavailable",
            "scored_activation": False,
        },
        "removed_result_field": "results[*].raw_sha256",
        "scoring_permitted": False,
        "semantic_qualification": "unavailable",
        "this_is_not_a_schema_waiver": True,
        "timing_certified": False,
        "preserve_all_other_fields_exactly": True,
    }
    if (
        lift.get("schema") != "v092-joern-schema-metadata-lift-aggregate/v1"
        or not _same_json_value(
            lift.get("aggregate_counts"),
            {
                "cases": 108,
                "distinct_raw_output_paths": 108,
                "outcomes": {"inconclusive": 96, "unsupported": 12},
                "reports": 5,
            },
        )
        or not _same_json_value(lift.get("lift_boundary"), expected_lift_boundary)
    ):
        raise GateError("embedded Joern sidecar changed its exact metadata-only limitation boundary")
    state = manifest.get("qualification_state")
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
    if not _same_json_value(state, expected_state):
        raise GateError("publication manifest qualification flags differ from the fixed boundary")
    return sidecar


def _load_publication_manifest(root: Path) -> dict:
    manifest = _read_json(root / PUBLICATION_MANIFEST, "v0.9.2 publication manifest")
    if (
        manifest.get("schema") != "dataflowbench-v0.9.2-publication-evidence/v1"
        or manifest.get("scope") != PUBLICATION_DIR
        or manifest.get("capture_scope") != PUBLICATION_CAPTURE
        or manifest.get("bundle_delivery_path") != PUBLICATION_BUNDLE
    ):
        raise GateError("publication manifest has an unsupported schema")
    counts = manifest.get("counts")
    if not _same_json_value(counts, EXPECTED_COUNTS):
        raise GateError("publication manifest counts do not match the fixed v0.9.2 matrix")
    _validate_qualification(root, manifest)
    captures = manifest.get("capture_files")
    if not isinstance(captures, list) or len(captures) != 4_349:
        raise GateError("publication capture inventory must contain exactly 4,349 files")
    capture_paths: set[str] = set()
    capture_kinds: dict[str, int] = {}
    for capture in captures:
        if not isinstance(capture, dict):
            raise GateError("publication capture inventory contains a malformed record")
        path = _safe_repo_path(capture.get("path"), "capture_files.path")
        if not path.startswith(PUBLICATION_CAPTURE + "/") or path in capture_paths:
            raise GateError("publication capture inventory contains a duplicate or out-of-scope path")
        if capture.get("kind") not in {
            "canonical-source-report",
            "selected-original-joern-report",
            "raw-output",
        }:
            raise GateError(f"publication capture inventory has unsupported kind: {path}")
        capture_kinds[capture["kind"]] = capture_kinds.get(capture["kind"], 0) + 1
        if not isinstance(capture.get("sha256"), str) or not HEX_SHA256.fullmatch(capture["sha256"]):
            raise GateError(f"publication capture inventory has invalid digest: {path}")
        size = capture.get("bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise GateError(f"publication capture inventory has invalid size: {path}")
        capture_paths.add(path)
    if capture_kinds != {
        "canonical-source-report": 92,
        "selected-original-joern-report": 5,
        "raw-output": EXPECTED_COUNTS["raw_files"],
    }:
        raise GateError("publication capture inventory kinds differ from the fixed 92/5/4,252 mapping")
    reports = manifest.get("reports")
    if not isinstance(reports, list) or len(reports) != EXPECTED_COUNTS["reports"]:
        raise GateError("publication manifest must bind exactly 92 report partitions")
    seen_paths: set[str] = set()
    seen_attempts: set[tuple[str, str]] = set()
    total_rows = 0
    raw_count = 0
    raw_case_ids: set[str] = set()
    report_map: dict[str, str] = {}
    membership: dict[str, set[str]] = {}
    used_capture_paths: set[str] = set()
    lifted_reports = 0
    for index, entry in enumerate(reports):
        if not isinstance(entry, dict):
            raise GateError(f"publication report {index} must be an object")
        adapter = entry.get("adapter")
        attempt_id = entry.get("attempt_id")
        if not isinstance(adapter, str) or not adapter or not isinstance(attempt_id, str) or not attempt_id:
            raise GateError(f"publication report {index} is missing adapter or attempt_id")
        identity = (adapter, attempt_id)
        if identity in seen_attempts:
            raise GateError(f"publication manifest repeats report identity {identity!r}")
        seen_attempts.add(identity)
        adapter_id = entry.get("adapter_id")
        if not isinstance(adapter_id, str) or not adapter_id:
            raise GateError(f"publication report {identity!r} has invalid adapter_id")
        if PurePosixPath(adapter).stem != adapter_id:
            raise GateError(f"publication report adapter identity differs for {identity!r}")
        lifted = entry.get("lifted_metadata")
        canonical = entry.get("canonical_report")
        captured_source = entry.get("capture_source_report")
        selected = entry.get("selected_original")
        selected_capture = entry.get("capture_selected_report")
        if not isinstance(lifted, bool) or not all(
            isinstance(value, dict) for value in (canonical, captured_source, selected)
        ):
            raise GateError(f"publication report {identity!r} has malformed source-report bindings")
        canonical_path = _safe_repo_path(canonical.get("path"), "canonical_report.path")
        captured_source_path = _safe_repo_path(
            captured_source.get("path"), "capture_source_report.path"
        )
        canonical_name = PurePosixPath(canonical_path).name
        if (
            captured_source_path != f"{PUBLICATION_CAPTURE}/source-reports/{canonical_name}"
            or captured_source.get("sha256") != canonical.get("sha256")
            or captured_source.get("bytes") != canonical.get("bytes")
            or canonical.get("path") != selected.get("path") and not lifted
            or canonical.get("sha256") != selected.get("sha256") and not lifted
        ):
            raise GateError(f"publication report {identity!r} source and capture bindings differ")
        source_capture_record = next(
            (record for record in captures if record.get("path") == captured_source_path), None
        )
        if (
            source_capture_record is None
            or source_capture_record.get("kind") != "canonical-source-report"
            or source_capture_record.get("sha256") != canonical.get("sha256")
            or source_capture_record.get("bytes") != canonical.get("bytes")
        ):
            raise GateError(f"publication report {identity!r} canonical capture is not inventory-bound")
        if lifted:
            lifted_reports += 1
            if not isinstance(selected_capture, dict):
                raise GateError(f"lifted publication report {identity!r} lacks selected source capture")
            selected_path = _safe_repo_path(selected_capture.get("path"), "capture_selected_report.path")
            selected_record = next(
                (record for record in captures if record.get("path") == selected_path), None
            )
            if (
                selected_path != f"{PUBLICATION_CAPTURE}/selected-reports/{canonical_name}"
                or selected_path in used_capture_paths
                or selected_capture.get("sha256") != selected.get("sha256")
                or selected_capture.get("bytes") != selected.get("bytes")
                or selected_record is None
                or selected_record.get("kind") != "selected-original-joern-report"
                or selected_record.get("sha256") != selected_capture.get("sha256")
                or selected_record.get("bytes") != selected_capture.get("bytes")
            ):
                raise GateError(f"lifted publication report {identity!r} selected capture is unbound")
            used_capture_paths.add(selected_path)
        elif selected_capture is not None:
            raise GateError(f"unlifted publication report {identity!r} has an unexpected selected capture")
        row_count = entry.get("row_count")
        raw_outputs = entry.get("raw_outputs")
        if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 1:
            raise GateError(f"publication report {identity!r} has an invalid row_count")
        if not isinstance(raw_outputs, list) or len(raw_outputs) != row_count:
            raise GateError(f"publication report {identity!r} raw-output count differs from row_count")
        total_rows += row_count
        local_case_ids: set[str] = set()
        for raw_index, raw in enumerate(raw_outputs):
            if not isinstance(raw, dict):
                raise GateError(f"raw output {identity!r}/{raw_index} must be an object")
            case_id = raw.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                raise GateError(f"raw output {identity!r}/{raw_index} has no case_id")
            source_path = _safe_repo_path(raw.get("source_path"), "raw_output.source_path")
            capture_path = _safe_repo_path(raw.get("capture_path"), "raw_output.capture_path")
            raw_sha = raw.get("sha256")
            raw_bytes = raw.get("bytes")
            if not isinstance(raw_sha, str) or not HEX_SHA256.fullmatch(raw_sha):
                raise GateError(f"raw output {identity!r}/{case_id} has invalid sha256")
            if not isinstance(raw_bytes, int) or isinstance(raw_bytes, bool) or raw_bytes < 0:
                raise GateError(f"raw output {identity!r}/{case_id} has invalid byte count")
            if case_id in local_case_ids:
                raise GateError(f"publication report {identity!r} repeats case {case_id}")
            if raw.get("ordinal") != raw_index:
                raise GateError(f"publication raw output ordinal is not canonical: {identity!r}/{case_id}")
            if capture_path not in capture_paths or capture_path in used_capture_paths:
                raise GateError(f"publication raw output capture path is unbound or repeated: {capture_path}")
            used_capture_paths.add(capture_path)
            local_case_ids.add(case_id)
            raw_count += 1
            raw_case_ids.add(case_id)
        published = entry.get("published_report")
        if not isinstance(published, dict):
            raise GateError(f"publication report {identity!r} is missing published_report")
        path = _safe_repo_path(published.get("path"), "published_report.path")
        sha = published.get("sha256")
        size = published.get("bytes")
        if path != f"{PUBLICATION_DIR}/normal/{canonical_name}":
            raise GateError(f"published report path does not match its canonical source basename: {path}")
        if path in seen_paths:
            raise GateError(f"publication manifest repeats normalized report path {path}")
        if not isinstance(sha, str) or not HEX_SHA256.fullmatch(sha):
            raise GateError(f"published report {path} has invalid sha256")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise GateError(f"published report {path} has invalid byte count")
        report_bytes = _read_bound_file(root, published, f"published report {path}")
        try:
            report_json = json.loads(report_bytes)
        except json.JSONDecodeError as exc:
            raise GateError(f"published report is invalid JSON ({path}): {exc}") from exc
        results = report_json.get("results") if isinstance(report_json, dict) else None
        if not isinstance(results, list) or len(results) != row_count:
            raise GateError(f"published report row count differs from manifest for {path}")
        result_case_ids: list[str] = []
        for row_index, row in enumerate(results):
            if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
                raise GateError(f"published report {path} has malformed row {row_index}")
            result_case_ids.append(row["case_id"])
            if row.get("raw_output") != next(
                (raw["capture_path"] for raw in raw_outputs if raw.get("case_id") == row["case_id"]),
                None,
            ):
                raise GateError(f"published report raw_output mapping differs from manifest: {path}")
        if len(result_case_ids) != len(set(result_case_ids)) or set(result_case_ids) != local_case_ids:
            raise GateError(f"published report case membership differs from manifest: {path}")
        seen_paths.add(path)
        report_map[path] = sha
        membership[path] = local_case_ids
    if total_rows != EXPECTED_COUNTS["rows"] or raw_count != EXPECTED_COUNTS["raw_files"]:
        raise GateError("publication report/raw totals do not match the fixed v0.9.2 matrix")
    if lifted_reports != EXPECTED_COUNTS["selected_source_reports"]:
        raise GateError("publication report Joern metadata-lift count differs from the fixed five reports")
    if len(raw_case_ids) != EXPECTED_COUNTS["unique_case_ids"]:
        raise GateError("publication raw outputs do not cover exactly 1,108 unique cases")
    if used_capture_paths != {
        capture["path"] for capture in captures
        if capture.get("kind") in {"raw-output", "selected-original-joern-report"}
    }:
        raise GateError("publication report/raw rows do not cover the capture inventory")
    return {
        "manifest": manifest,
        "report_map": report_map,
        "membership": membership,
        "case_ids": raw_case_ids,
        "rows": total_rows,
        "raw_files": raw_count,
    }


def validate_freeze(root: Path, evidence_revision: str) -> dict:
    """Require the freeze's report/population map to equal the verified manifest."""
    if not HEX_COMMIT.fullmatch(evidence_revision):
        raise GateError("--evidence-revision must be a full lowercase 40-hex commit SHA")
    manifest_state = _load_publication_manifest(root)
    manifest = manifest_state["manifest"]
    freeze = _read_json(root / "reports" / "freeze.json", "v0.9.2 release freeze")
    if (
        type(freeze.get("schema_version")) is not int
        or freeze.get("schema_version") != 1
        or not isinstance(freeze.get("claim"), dict)
        or freeze["claim"].get("scope") != "release"
    ):
        raise GateError("v0.9.2 requires a schema-version-1 release-scope freeze")
    benchmark = freeze.get("benchmark")
    if not isinstance(benchmark, dict) or (
        benchmark.get("release") != RELEASE
        or benchmark.get("revision") != evidence_revision
        or benchmark.get("dirty") is not False
    ):
        raise GateError("freeze does not bind the exact merged v0.9.2 evidence revision")
    reports = freeze.get("reports")
    if not isinstance(reports, list) or len(reports) != EXPECTED_COUNTS["reports"]:
        raise GateError("freeze must bind exactly 92 publication reports")
    freeze_map: dict[str, str] = {}
    freeze_membership: dict[str, set[str]] = {}
    for index, entry in enumerate(reports):
        if not isinstance(entry, dict):
            raise GateError(f"freeze report {index} must be an object")
        path = _safe_repo_path(entry.get("path"), "freeze report path")
        sha = entry.get("normalized_report_sha256")
        if not isinstance(sha, str) or not HEX_SHA256.fullmatch(sha):
            raise GateError(f"freeze report {path} has invalid normalized_report_sha256")
        case_ids = entry.get("case_ids")
        if not isinstance(case_ids, list) or any(not isinstance(case_id, str) for case_id in case_ids):
            raise GateError(f"freeze report {path} has invalid case_ids")
        if path in freeze_map:
            raise GateError(f"freeze repeats report path {path}")
        freeze_map[path] = sha
        freeze_membership[path] = set(case_ids)
        if len(freeze_membership[path]) != len(case_ids):
            raise GateError(f"freeze report {path} repeats a case id")
    if freeze_map != manifest_state["report_map"]:
        raise GateError("freeze report paths/hashes differ from the verified publication manifest")
    if freeze_membership != manifest_state["membership"]:
        raise GateError("freeze report case membership differs from the verified publication manifest")
    if sum(len(ids) for ids in freeze_membership.values()) != EXPECTED_COUNTS["rows"]:
        raise GateError("freeze report membership does not contain exactly 4,252 rows")
    cases = freeze.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_COUNTS["unique_case_ids"]:
        raise GateError("freeze population must contain exactly 1,108 cases")
    case_ids = [item.get("id") for item in cases if isinstance(item, dict)]
    if len(case_ids) != len(cases) or any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise GateError("freeze population contains malformed case identities")
    if len(set(case_ids)) != EXPECTED_COUNTS["unique_case_ids"] or set(case_ids) != manifest_state["case_ids"]:
        raise GateError("freeze population case ids differ from the verified publication manifest")
    if manifest.get("qualification_sidecar", {}).get("path") != QUALIFICATION_SIDECAR:
        raise GateError("freeze input does not retain the qualification limitations sidecar")
    return {
        "release": RELEASE,
        "evidence_revision": evidence_revision,
        "groups": EXPECTED_COUNTS["groups"],
        "reports": len(reports),
        "rows": EXPECTED_COUNTS["rows"],
        "unique_case_ids": len(case_ids),
        "raw_files": EXPECTED_COUNTS["raw_files"],
        "qualification_sidecar": QUALIFICATION_SIDECAR,
    }


def _assert_clean_source(source: Path) -> str:
    top = Path(_git_output(source, ["rev-parse", "--show-toplevel"])).resolve()
    if top != source.resolve():
        raise GateError(f"source checkout is not the repository root: {top}")
    head = _git_output(source, ["rev-parse", "HEAD^{commit}"])
    status = _git_output(source, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status:
        raise GateError("cannot run release gate from a dirty checkout:\n" + status)
    return head


def _is_ancestor(checkout: Path, ancestor: str, descendant: str) -> bool:
    result = _git(checkout, ["merge-base", "--is-ancestor", ancestor, descendant], check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.strip() or result.stdout.strip()
    raise GateError(f"could not prove commit ancestry: {detail}")


def _clone_sparse_without_shared_objects(source: Path, clone: Path, current_head: str) -> None:
    env = os.environ.copy()
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    _run(
        [
            "git",
            "clone",
            "--no-local",
            "--no-hardlinks",
            "--no-checkout",
            "--no-tags",
            str(source),
            str(clone),
        ],
        env=env,
    )
    # Sparse cone selection includes the release freeze, normalized release
    # reports, fixtures/schema needed by the reviewed binary, and only the
    # v0.9.2 publication capture input. It omits historical attempts and the
    # large archival evidence trees.
    _git(clone, ["sparse-checkout", "init", "--cone"])
    _git(
        clone,
        [
            "sparse-checkout",
            "set",
            "cases",
            "adapters",
            "src",
            "populations",
            "schemas",
            "scripts",
            "results",
            f"{PUBLICATION_DIR}",
            "reports/releases/v0.9.2/review-handoff/bifrost-v0151-final-review-20261107-01",
            "reports/releases/v0.9.2/validation/bifrost-v0151-terminal-01",
            "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-04",
            "reports/releases/v0.9.2/ledger-archives/ledger-151-01",
            "execution-state/v092/publication-evidence/joern108-canonical-schema-01/projection-03/sidecars",
            "evidence-delivery/v0.9.2-publication-01/detail",
        ],
    )
    _git(clone, ["checkout", "--detach", current_head])
    source_git_dir = Path(_git_output(source, ["rev-parse", "--absolute-git-dir"])).resolve()
    clone_git_dir = Path(_git_output(clone, ["rev-parse", "--absolute-git-dir"])).resolve()
    if source_git_dir == clone_git_dir:
        raise GateError("disposable release clone shares the source Git directory")
    alternates = clone_git_dir / "objects" / "info" / "alternates"
    if alternates.exists() and alternates.read_text(encoding="utf-8").strip():
        raise GateError("disposable release clone uses a shared Git object store")
    # Explicitly assert that no historical source bundle/capture directory was
    # materialized by the sparse checkout.
    for excluded in (
        "evidence-archives",
        "reports/releases/v0.9.0",
        "execution-state/v092/diagnostics",
        "execution-state/v092/validation",
    ):
        if (clone / excluded).exists():
            raise GateError(f"sparse release clone unexpectedly includes {excluded}")


def _fetch_official_main_and_tags(clone: Path, git_remote: str) -> str:
    _git(clone, ["remote", "remove", "origin"], check=False)
    _git(clone, ["remote", "add", REMOTE_NAME, git_remote])
    # Fetch branch and tags in separate successful operations so a failed tag
    # lookup cannot be mistaken for an unpublished release.
    _git(
        clone,
        ["-c", "fetch.prune=false", "-c", "fetch.pruneTags=false", "fetch", "--no-prune", "--no-tags", REMOTE_NAME, "main"],
    )
    _git(
        clone,
        ["-c", "fetch.prune=false", "-c", "fetch.pruneTags=false", "fetch", "--no-prune", "--tags", REMOTE_NAME],
    )
    return _git_output(clone, ["rev-parse", f"refs/remotes/{REMOTE_NAME}/main^{{commit}}"])


def _remote_tag_commit(clone: Path) -> str | None:
    remote = _git(clone, ["ls-remote", "--exit-code", REMOTE_NAME, f"refs/tags/{RELEASE}"], check=False)
    local = _git(clone, ["show-ref", "--verify", "--quiet", f"refs/tags/{RELEASE}"], check=False)
    if remote.returncode == 2:
        if local.returncode != 1:
            raise GateError("remote tag is absent but an inherited local release tag exists or is unreadable")
        return None
    if remote.returncode != 0:
        raise GateError("cannot determine remote release tag state: " + remote.stderr.strip())
    if local.returncode != 0:
        raise GateError("remote release tag was not fetched")
    remote_oid = remote.stdout.split()[0]
    local_oid = _git_output(clone, ["rev-parse", f"refs/tags/{RELEASE}"])
    if remote_oid != local_oid:
        raise GateError("remote and fetched release tag identities differ")
    return _git_output(clone, ["rev-parse", f"refs/tags/{RELEASE}^{{commit}}"])


def _assert_release_tree_matches_current(clone: Path, current_head: str, tag: str) -> None:
    result = _git(
        clone,
        ["diff", "--quiet", current_head, tag, "--", "reports/freeze.json", "results"],
        check=False,
    )
    if result.returncode == 0:
        return
    if result.returncode == 1:
        raise GateError(
            f"existing {RELEASE} tag does not byte-match current reports/freeze.json and results"
        )
    raise GateError("could not compare current release tree with tag: " + result.stderr.strip())


def _materialize_publication_capture(clone: Path) -> None:
    env = os.environ.copy()
    env.pop("GIT_LFS_SKIP_SMUDGE", None)
    _run(
        ["git", "-C", str(clone), "lfs", "install", "--local", "--skip-repo"],
        env={**env, "GIT_LFS_SKIP_SMUDGE": "1"},
    )
    _git(
        clone,
        ["lfs", "pull", "--include", LEDGER_ARCHIVE_INCLUDE, REMOTE_NAME],
        enable_lfs_smudge=True,
    )
    _git(
        clone,
        ["lfs", "checkout", LEDGER_ARCHIVE_INCLUDE],
        enable_lfs_smudge=True,
    )
    _git(
        clone,
        ["lfs", "pull", "--include", CAPTURE_LFS_INCLUDE, REMOTE_NAME],
        enable_lfs_smudge=True,
    )
    _git(clone, ["lfs", "checkout", PUBLICATION_BUNDLE], enable_lfs_smudge=True)


def _hydrate_current_ledger(clone: Path) -> None:
    hydrator = clone / LEDGER_HYDRATOR
    if not hydrator.is_file():
        raise GateError(f"v0.9.2 ledger archive hydrator is missing: {hydrator}")
    result = _run(
        [sys.executable, str(hydrator), "hydrate-current", "--root", str(clone)],
        cwd=clone,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GateError("v0.9.2 ledger hydrate-current failed" + (f": {detail}" if detail else ""))


def _run_mapper(clone: Path, operation: str) -> None:
    if operation not in {"hydrate", "verify"}:
        raise GateError(f"unsupported publication mapper operation: {operation}")
    mapper = clone / MAPPER
    if not mapper.is_file():
        raise GateError(f"publication evidence mapper is missing: {mapper}")
    result = _run(
        [sys.executable, str(mapper), operation, "--root", str(clone)],
        cwd=clone,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if len(detail) > 2_000:
            detail = detail[-2_000:]
        raise GateError(f"publication mapper {operation} failed ({result.returncode})" + (f": {detail}" if detail else ""))


def _run_binary(binary: Path, args: Sequence[str], clone: Path) -> None:
    result = _run([str(binary), *args], cwd=clone, check=False)
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip()
    if len(detail) > 2_000:
        detail = detail[-2_000:]
    raise GateError(
        f"release binary failed ({result.returncode}): {binary} {' '.join(args)}"
        + (f": {detail}" if detail else "")
    )


def _copy_generated_results(clone: Path, output: Path) -> None:
    generated = (clone / "results").resolve()
    if not generated.is_dir():
        raise GateError(f"release binary did not generate a results directory: {generated}")
    destination = output.expanduser().resolve()
    if destination == generated or generated in destination.parents:
        raise GateError("--generate-output must be outside the disposable clone")
    if destination.exists():
        if not destination.is_dir() or any(destination.iterdir()):
            raise GateError(f"--generate-output must be a missing or empty directory: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
    shutil.copytree(generated, destination, dirs_exist_ok=True)


def run_gate(
    source: Path | None = None,
    *,
    binary: Path,
    evidence_revision: str,
    generate_output: Path | None = None,
    git_remote: str = REQUIRED_REMOTE,
) -> dict:
    """Run v0.9.2 verification against a clean source and disposable clone.

    ``git_remote`` is intentionally only an in-process injection point for
    focused tests. The command-line interface always uses the official remote.
    """
    source = (source or Path(__file__).resolve().parents[1]).resolve()
    binary = binary.expanduser()
    if not binary.is_absolute():
        raise GateError("--binary must be an absolute path to the reviewed binary")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise GateError(f"--binary is not an executable file: {binary}")
    if not HEX_COMMIT.fullmatch(evidence_revision):
        raise GateError("--evidence-revision must be a full lowercase 40-hex commit SHA")
    current_head = _assert_clean_source(source)
    if not _is_ancestor(source, evidence_revision, current_head):
        raise GateError("evidence revision is not an ancestor of the current source HEAD")

    with tempfile.TemporaryDirectory(prefix="dataflowbench-v092-release-") as temporary:
        clone = Path(temporary) / "repo"
        _clone_sparse_without_shared_objects(source, clone, current_head)
        fetched_main = _fetch_official_main_and_tags(clone, git_remote)
        if not _is_ancestor(clone, evidence_revision, fetched_main):
            raise GateError("evidence revision is not an ancestor of official main")
        if not _is_ancestor(clone, evidence_revision, current_head):
            raise GateError("evidence revision is not an ancestor of current HEAD")

        tag = _remote_tag_commit(clone)
        if tag is None:
            source_tag = _git(
                source,
                ["show-ref", "--verify", "--quiet", f"refs/tags/{RELEASE}"],
                check=False,
            )
            if source_tag.returncode != 1:
                raise GateError("remote tag absent but source checkout has a local v0.9.2 tag")
            _git(clone, ["-c", "tag.gpgsign=false", "tag", RELEASE, current_head])
            check_results = generate_output is None
        else:
            if not _is_ancestor(clone, evidence_revision, tag):
                raise GateError(f"existing {RELEASE} tag does not contain the evidence revision")
            _assert_release_tree_matches_current(clone, current_head, tag)
            if generate_output is not None:
                raise GateError(f"--generate-output is only valid when {RELEASE} is absent")
            check_results = True
            _git(clone, ["checkout", "--detach", tag])

        _materialize_publication_capture(clone)
        _hydrate_current_ledger(clone)
        _run_mapper(clone, "hydrate")
        _run_mapper(clone, "verify")
        summary = validate_freeze(clone, evidence_revision)
        _run_binary(binary, ["validate-freeze", "reports/freeze.json"], clone)
        result_args = [
            "generate-results",
            "--manifest",
            "reports/freeze.json",
            "--output-directory",
            "results",
        ]
        if check_results:
            result_args.append("--check")
        _run_binary(binary, result_args, clone)
        if not check_results and generate_output is not None:
            _copy_generated_results(clone, generate_output)
    return summary


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-revision", required=True, help="exact merged publication-input main SHA")
    parser.add_argument("--binary", required=True, type=Path, help="absolute path to the reviewed binary")
    parser.add_argument(
        "--generate-output",
        type=Path,
        help="copy generated results here when the v0.9.2 tag is absent",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = run_gate(
            binary=args.binary,
            evidence_revision=args.evidence_revision,
            generate_output=args.generate_output,
        )
    except GateError as exc:
        print(f"v0.9.2 release gate failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
