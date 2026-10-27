#!/usr/bin/env python3
"""Strict, read-only parsing for the authorized v0.9.2 scoped recovery packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any


MANIFEST_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest.json"
)
AUTHORIZATION_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/scoped-recovery-01/authorization.json"
)
LEDGER_PATH = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
PREFIX_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/scoped-recovery-01/ledger-prefix.jsonl"
)
C1_ARCHIVE = PurePosixPath("reports/releases/v0.9.2/acquisition/failed-contract-01.json")
C2_ARCHIVE = PurePosixPath(
    "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json"
)
C1_SHA256 = "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3"
C2_SHA256 = "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422"
C1_PLAN_COMMIT = "c5837c0e5b3b809cae3f347a748ef2fd03e3090f"
C2_PLAN_COMMIT = "a180c302b56f2c18a1fdfbbd1bc14489151fc54e"
C1_SOURCE_COMMIT = "4e7b1d9afd6bccf3e932e4222825afb44c436412"
C2_SOURCE_COMMIT = "21b76b747b72363aad4bbbc358fc2ae9aee24f1c"
PREFIX_SHA256 = "48e5a5eb985fa3dde72c62dee2cfa55e6c291050c68d7c5b8b4212d970aebd29"
PREFIX_BYTES = 7_738_871
PREFIX_LINES = 27
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_PREFIX_BYTES = 16 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class ScopedRecoveryError(ValueError):
    """The scoped recovery packet is malformed, changed, or overbroad."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _regular_bytes(root: Path, relative: str, description: str,
                   *, maximum_bytes: int = MAX_MANIFEST_BYTES) -> bytes:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ScopedRecoveryError(f"{description} path is not a safe repository-relative file")
    target = root.joinpath(*path.parts)
    try:
        info = target.lstat()
    except OSError as exc:
        raise ScopedRecoveryError(f"cannot read {description}: {target}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size > maximum_bytes:
        raise ScopedRecoveryError(f"{description} is not a bounded regular file: {target}")
    try:
        return target.read_bytes()
    except OSError as exc:
        raise ScopedRecoveryError(f"cannot read {description}: {target}") from exc


def _json_object(data: bytes, description: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ScopedRecoveryError(f"{description} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ScopedRecoveryError(f"{description} must be a JSON object")
    return value


def _bound_ref(value: object, expected_path: PurePosixPath, description: str) -> tuple[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ScopedRecoveryError(f"{description} must contain exactly path and sha256")
    path = value.get("path")
    digest = value.get("sha256")
    if path != expected_path.as_posix():
        raise ScopedRecoveryError(f"{description} must use the registered path {expected_path}")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ScopedRecoveryError(f"{description} must bind a lowercase SHA-256")
    return path, digest


def _canonical_ledger(raw: bytes, description: str) -> list[tuple[dict[str, Any], str]]:
    rows = []
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.endswith(b"\n") or line == b"\n" or line.endswith(b"\r\n"):
            raise ScopedRecoveryError(f"{description} line {index} is blank or non-canonical")
        try:
            value = json.loads(line[:-1])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ScopedRecoveryError(f"{description} line {index} is invalid JSON") from exc
        if not isinstance(value, dict):
            raise ScopedRecoveryError(f"{description} line {index} must be an object")
        canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if canonical != line:
            raise ScopedRecoveryError(f"{description} line {index} is not canonical JSON")
        rows.append((value, sha256(line)))
    if not rows:
        raise ScopedRecoveryError(f"{description} is empty")
    return rows


def _read_ref(root: Path, reference: object, expected_path: PurePosixPath,
              description: str, *, maximum_bytes: int = MAX_MANIFEST_BYTES) -> tuple[dict[str, Any], bytes, str]:
    path, digest = _bound_ref(reference, expected_path, description)
    raw = _regular_bytes(root, path, description, maximum_bytes=maximum_bytes)
    if sha256(raw) != digest:
        raise ScopedRecoveryError(f"{description} bytes differ from their digest")
    return _json_object(raw, description), raw, digest


def _expected_history() -> list[dict[str, str]]:
    return [
        {
            "path": C1_ARCHIVE.as_posix(),
            "sha256": C1_SHA256,
            "canonical_path": "reports/releases/v0.9.2/execution-v1/contract.json",
            "plan_commit": C1_PLAN_COMMIT,
            "source_commit": C1_SOURCE_COMMIT,
        },
        {
            "path": C2_ARCHIVE.as_posix(),
            "sha256": C2_SHA256,
            "canonical_path": "reports/releases/v0.9.2/execution-v2/contract.json",
            "plan_commit": C2_PLAN_COMMIT,
            "source_commit": C2_SOURCE_COMMIT,
        },
    ]


def _validate_authorization(value: dict[str, Any]) -> None:
    expected_scope = {
        "retained_current_completed_groups": 25,
        "corrected_harness_for_remaining_groups": True,
        "codeql_java_modeling_next_attempt": 2,
        "original_wall_origin_utc": "2026-10-20T00:57:00.680937+00:00",
        "total_wall_budget_seconds": 102960,
        "max_attempts_per_group_across_contracts": 2,
        "case_population": 1108,
        "groups": 84,
        "report_partitions": 92,
        "report_rows": 4252,
        "minimum_launch_free_gib": 125,
        "protected_reserve_gib": 40,
        "scratch_retention_caps_gib": 24,
    }
    if (value.get("schema") != "v092-scoped-recovery-authorization/v1" or
            value.get("evidence_kind") != "human-chat-authorization-record" or
            value.get("request") != (
                "Lift the no-new-contract-supersessions restriction; retain 25 completed v0.9.2 "
                "measurements under their original source records; resume with corrected harness, "
                "original clock, two-attempt limit, resources and population unchanged."
            ) or value.get("human_reply") != "Authorize scoped recovery (Recommended)" or
            value.get("authorized_scope") != expected_scope or
            value.get("forbidden") != [
                "Promoting failed reports",
                "Relabeling original measurements as executed under new source",
                "Reusing old-release reports",
                "Resetting clock or attempts",
                "Changing population or thresholds",
            ]):
        raise ScopedRecoveryError("recorded human authorization differs from the exact authorized scope")
    recorded = value.get("recorded_utc")
    if not isinstance(recorded, str) or not recorded.startswith("2026-10-20T"):
        raise ScopedRecoveryError("authorization record has no valid same-day timestamp")


def _artifact_reference(value: object, attempt_id: str, name: str,
                        description: str) -> tuple[str, str]:
    expected_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/{name}"
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ScopedRecoveryError(f"{description} reference has an unsupported shape")
    if value.get("path") != expected_path:
        raise ScopedRecoveryError(f"{description} reference escapes the exact attempt namespace")
    digest = value.get("sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ScopedRecoveryError(f"{description} reference has an invalid SHA-256")
    return expected_path, digest


def _verify_attempt_artifacts(root: Path, item: dict[str, Any], row: dict[str, Any],
                              *, status: str) -> None:
    attempt_id = item.get("attempt_id")
    if not isinstance(attempt_id, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*-attempt-[0-9]{2}-series-01", attempt_id):
        raise ScopedRecoveryError("retained attempt ID is malformed")
    for key, name in (("started_receipt", "started.json"), ("completed_receipt", "completed.json")):
        relative, digest = _artifact_reference(item.get(key), attempt_id, name, key)
        raw = _regular_bytes(root, relative, key, maximum_bytes=8 * 1024 * 1024)
        if sha256(raw) != digest:
            raise ScopedRecoveryError(f"{key} differs from the manifest-bound receipt digest")
        receipt = _json_object(raw, key)
        if key == "completed_receipt" and receipt != row:
            raise ScopedRecoveryError("completed receipt bytes do not equal the sealed ledger row")
        if key == "started_receipt":
            for field in (
                "execution_series", "group_id", "attempt_id", "source_commit", "plan_commit",
                "contract_sha256", "runner_source_sha256", "fixture_revision", "population",
                "tool", "tool_binding", "identity_components", "qualification", "source_inputs",
                "cache_root", "argv", "environment", "execution_root", "output_roots",
                "case_ids", "deadline_seconds",
            ):
                if field not in row or receipt.get(field) != row[field]:
                    raise ScopedRecoveryError(f"started receipt differs from ledger row: {field}")
            if (receipt.get("status") != "started" or receipt.get("end_utc") is not None or
                    receipt.get("start_utc") != row.get("start_utc")):
                raise ScopedRecoveryError("started receipt state differs from the retained attempt")
    if item.get("status") != status or row.get("status") != status:
        raise ScopedRecoveryError("manifest attempt status differs from its sealed ledger row")


def validate_packet(root: str | Path, reference: object) -> dict[str, Any]:
    """Validate the exact authorization packet and its byte-sealed ledger prefix.

    This function performs no analyzer execution and does not bless the rows; the
    executor separately replays their originating contracts and the checker
    independently validates each row under that context.
    """
    repository = Path(root).resolve()
    manifest_path, manifest_sha = _bound_ref(reference, MANIFEST_PATH, "scoped_recovery")
    manifest_raw = _regular_bytes(repository, manifest_path, "scoped recovery manifest")
    if sha256(manifest_raw) != manifest_sha:
        raise ScopedRecoveryError("scoped recovery manifest digest mismatch")
    manifest = _json_object(manifest_raw, "scoped recovery manifest")
    expected_keys = {
        "schema", "authorization", "historical_contracts", "ledger_prefix", "retained_completed",
        "retained_failures", "repair_patch", "repair_proof", "failure_diagnosis",
        "original_wall_origin_utc", "execution_series", "total_wall_budget_seconds",
        "maximum_attempts_per_group", "scope",
    }
    if set(manifest) != expected_keys or manifest.get("schema") != "v092-scoped-recovery-manifest/v1":
        raise ScopedRecoveryError("scoped recovery manifest has an unknown schema or field")
    if manifest.get("historical_contracts") != _expected_history():
        raise ScopedRecoveryError("scoped recovery does not name the two exact historical contracts")
    if (manifest.get("original_wall_origin_utc") != "2026-10-20T00:57:00.680937+00:00" or
            manifest.get("execution_series") != 1 or
            manifest.get("total_wall_budget_seconds") != 102960 or
            manifest.get("maximum_attempts_per_group") != 2 or
            manifest.get("scope") != (
                "Only current v0.9.2 C2 completed runs retain their own original source/contract "
                "provenance; new measurements use corrected C3; all failed evidence remains non-selected."
            )):
        raise ScopedRecoveryError("scoped recovery changes its original clock, series, budget, or stated scope")

    auth, auth_raw, auth_sha = _read_ref(
        repository, manifest.get("authorization"), AUTHORIZATION_PATH, "scoped recovery authorization"
    )
    _validate_authorization(auth)

    prefix = manifest.get("ledger_prefix")
    if not isinstance(prefix, dict) or set(prefix) != {"path", "sha256", "bytes", "lines"}:
        raise ScopedRecoveryError("ledger_prefix has an unsupported shape")
    if (prefix.get("path") != PREFIX_PATH.as_posix() or prefix.get("sha256") != PREFIX_SHA256 or
            prefix.get("bytes") != PREFIX_BYTES or prefix.get("lines") != PREFIX_LINES):
        raise ScopedRecoveryError("ledger prefix differs from the exact registered 27-line C1/C2 prefix")
    prefix_raw = _regular_bytes(
        repository, prefix["path"], "sealed historical ledger prefix", maximum_bytes=MAX_PREFIX_BYTES
    )
    if len(prefix_raw) != PREFIX_BYTES or sha256(prefix_raw) != PREFIX_SHA256:
        raise ScopedRecoveryError("sealed historical ledger prefix bytes or digest changed")
    prefix_rows = _canonical_ledger(prefix_raw, "sealed historical ledger prefix")
    if len(prefix_rows) != PREFIX_LINES:
        raise ScopedRecoveryError("sealed historical ledger prefix line count changed")
    current_raw = _regular_bytes(
        repository, LEDGER_PATH.as_posix(), "current execution ledger", maximum_bytes=64 * 1024 * 1024
    )
    if not current_raw.startswith(prefix_raw):
        raise ScopedRecoveryError("current ledger no longer begins with the exact sealed C1/C2 prefix")
    tail_rows = _canonical_ledger(current_raw[len(prefix_raw):], "post-prefix execution ledger") if len(current_raw) > len(prefix_raw) else []

    completed_items = manifest.get("retained_completed")
    failure_items = manifest.get("retained_failures")
    if not isinstance(completed_items, list) or len(completed_items) != 25:
        raise ScopedRecoveryError("scoped recovery must retain exactly 25 completed C2 groups")
    if not isinstance(failure_items, list) or len(failure_items) != 2:
        raise ScopedRecoveryError("scoped recovery must preserve exactly its two failed historical attempts")
    if [set(item) for item in completed_items + failure_items if isinstance(item, dict)] != [
            {"group_id", "attempt_id", "status", "contract_sha256", "source_commit", "plan_commit",
             "ledger_line_sha256", "started_receipt", "completed_receipt"}
            for _ in range(27)]:
        raise ScopedRecoveryError("retained roster entries have unknown or missing fields")
    if any(not isinstance(item, dict) for item in completed_items + failure_items):
        raise ScopedRecoveryError("retained roster contains a malformed entry")

    by_line = {line_sha: row for row, line_sha in prefix_rows}
    claimed_lines: set[str] = set()
    expected_completed = []
    expected_failures = []
    for row, line_sha in prefix_rows:
        contract_sha = row.get("contract_sha256")
        if row.get("execution_series") != 1:
            raise ScopedRecoveryError("historical ledger prefix crosses the registered execution series")
        if contract_sha == C1_SHA256:
            if (row.get("group_id") != "bifrost-c-kernel" or
                    row.get("attempt_id") != "bifrost-c-kernel-attempt-01-series-01" or
                    row.get("status") != "recorder-error"):
                raise ScopedRecoveryError("C1 prefix row differs from the one registered version-gate failure")
            expected_failures.append((row, line_sha, "C1"))
        elif contract_sha == C2_SHA256:
            if row.get("status") == "completed":
                expected_completed.append((row, line_sha))
            else:
                if (row.get("group_id") != "codeql-java-modeling" or
                        row.get("attempt_id") != "codeql-java-modeling-attempt-01-series-01" or
                        row.get("status") != "failed"):
                    raise ScopedRecoveryError("C2 prefix contains an unregistered failure")
                expected_failures.append((row, line_sha, "C2"))
        else:
            raise ScopedRecoveryError("historical ledger prefix contains a foreign contract revision")
    if len(expected_failures) != 2 or len(expected_completed) != 25:
        raise ScopedRecoveryError("historical prefix counts differ from the exact 25-completion, 2-failure scope")

    def validate_roster(items: list[dict[str, Any]], expected: list[tuple[dict[str, Any], str]],
                        status: str | None) -> None:
        item_lines = []
        for item in items:
            line_sha = item.get("ledger_line_sha256")
            row = by_line.get(line_sha)
            if row is None or line_sha in claimed_lines:
                raise ScopedRecoveryError("retained roster references an absent or duplicate ledger line")
            claimed_lines.add(line_sha)
            expected_contract = C1_SHA256 if row.get("contract_sha256") == C1_SHA256 else C2_SHA256
            expected_source = C1_SOURCE_COMMIT if expected_contract == C1_SHA256 else C2_SOURCE_COMMIT
            expected_plan = C1_PLAN_COMMIT if expected_contract == C1_SHA256 else C2_PLAN_COMMIT
            expected_status = status if status is not None else row.get("status")
            for key, value in {
                "group_id": row.get("group_id"), "attempt_id": row.get("attempt_id"),
                "status": expected_status, "contract_sha256": expected_contract,
                "source_commit": expected_source, "plan_commit": expected_plan,
                "ledger_line_sha256": line_sha,
            }.items():
                if item.get(key) != value or (key != "ledger_line_sha256" and row.get(key) != value):
                    raise ScopedRecoveryError(f"retained roster differs from sealed ledger row: {key}")
            _verify_attempt_artifacts(repository, item, row, status=expected_status)
            item_lines.append(line_sha)
        if set(item_lines) != {line_sha for _row, line_sha in expected}:
            raise ScopedRecoveryError("retained roster is incomplete or adds a foreign attempt")

    validate_roster(completed_items, expected_completed, "completed")
    validate_roster(
        failure_items,
        [(row, line_sha) for row, line_sha, _ctx in expected_failures],
        None,
    )
    if claimed_lines != set(by_line):
        raise ScopedRecoveryError("retained roster does not account for every sealed historical row")

    proof_refs = {
        "repair_patch": PurePosixPath("reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/fix-02.patch"),
        "repair_proof": PurePosixPath("reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/patch-manifest-02.json"),
        "failure_diagnosis": PurePosixPath("reports/releases/v0.9.2/qualification/scoped-recovery-01/repair/diagnosis.json"),
    }
    proof_bytes: dict[str, bytes] = {}
    proof_digests: dict[str, str] = {}
    for key, expected_path in proof_refs.items():
        reference_value = manifest.get(key)
        if not isinstance(reference_value, dict) or set(reference_value) != {"path", "sha256"}:
            raise ScopedRecoveryError(f"{key} must bind exactly a path and SHA-256")
        if reference_value.get("path") != expected_path.as_posix():
            raise ScopedRecoveryError(f"{key} must use its registered repair evidence path")
        digest = reference_value.get("sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ScopedRecoveryError(f"{key} SHA-256 is malformed")
        raw = _regular_bytes(repository, expected_path.as_posix(), key, maximum_bytes=8 * 1024 * 1024)
        if sha256(raw) != digest:
            raise ScopedRecoveryError(f"{key} bytes differ from the manifest-bound digest")
        proof_bytes[key] = raw
        proof_digests[key] = digest

    return {
        "repo_root": repository,
        "manifest": manifest,
        "manifest_sha256": manifest_sha,
        "manifest_path": manifest_path,
        "authorization": auth,
        "authorization_sha256": auth_sha,
        "authorization_bytes": auth_raw,
        "prefix_bytes": prefix_raw,
        "sealed_prefix_sha256": PREFIX_SHA256,
        "prefix_rows": prefix_rows,
        "tail_rows": tail_rows,
        "retained_completed": completed_items,
        "retained_failures": failure_items,
        "proof_bytes": proof_bytes,
        "proof_digests": proof_digests,
    }
