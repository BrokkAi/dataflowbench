#!/usr/bin/env python3
"""Strict, read-only parsing for the authorized v0.9.2 resource recovery packet."""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any


MANIFEST_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/resource-recovery-01/manifest.json"
)
AUTHORIZATION_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/resource-recovery-01/authorization.json"
)
LEDGER_PATH = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
PREFIX_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/resource-recovery-01/ledger-prefix.jsonl"
)
C3_ARCHIVE = PurePosixPath(
    "reports/releases/v0.9.2/acquisition/resource-recovery-contract-03.json"
)
C3_CANONICAL_PATH = PurePosixPath(
    "reports/releases/v0.9.2/execution-v3/contract.json"
)
C3_SHA256 = "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063"
C3_PLAN_COMMIT = "216bbaaf6513f334a31111983bf6cd35de6232e2"
C3_SOURCE_COMMIT = "3b583cd10fd66f27977d17d43fb06afc5006f4c3"
C3_SCOPED_MANIFEST_PATH = PurePosixPath(
    "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest.json"
)
C1_SHA256 = "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3"
C1_PLAN_COMMIT = "c5837c0e5b3b809cae3f347a748ef2fd03e3090f"
C1_SOURCE_COMMIT = "4e7b1d9afd6bccf3e932e4222825afb44c436412"
C2_SHA256 = "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422"
C2_PLAN_COMMIT = "a180c302b56f2c18a1fdfbbd1bc14489151fc54e"
C2_SOURCE_COMMIT = "21b76b747b72363aad4bbbc358fc2ae9aee24f1c"
PREFIX_SHA256 = "31ea08cf5f0fa04fe07697bb8d3683e2a313140e6e12e15fe7e7963a82cdc1f2"
PREFIX_BYTES = 16_086_045
PREFIX_LINES = 57
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_PREFIX_BYTES = 32 * 1024 * 1024
MAX_LEDGER_BYTES = 64 * 1024 * 1024
MAX_RECEIPT_BYTES = 16 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
ATTEMPT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*-attempt-[0-9]{2}-series-01\Z")

ORIGINAL_WALL_ORIGIN_UTC = "2026-10-20T00:57:00.680937+00:00"
ORIGINAL_DEADLINE_UTC = "2026-10-21T05:33:00.680937+00:00"
TOTAL_WALL_BUDGET_SECONDS = 102_960
MAXIMUM_ATTEMPTS_PER_GROUP = 2
EXECUTION_SERIES = 1
ANALYZER_FAMILIES = ["bifrost", "codeql", "joern", "semgrep", "opentaint", "infer", "flowdroid", "pysa"]
AUTHORIZATION_REQUEST = (
    "Resource-only successor contract with a 110 GiB launch floor and stronger disk guards; preserve the 40 GiB reserve, "
    "55 completed measurements (25 C2 plus 30 C3), two historical failures, the original deadline and attempt cap, "
    "population, and analyzer families."
)
AUTHORIZATION_REPLY = (
    "Go ahead with the resource-only successor contract and 110 GiB launch floor, adding the stronger disk guards. "
    "Keep the 40 GiB reserve, completed evidence, attempt limits and original deadline unchanged.\n"
    "I've asked a bunch of sessions to clear their caches (`mbx clean`) but feel free to ping other codex sessions "
    "(all i did was message claude sessons). Machine should be quieter tonight, please try evaluate and clean up after "
    "yourself from finished candidates (i know CodeQL runs can be demanding)."
)


class ResourceRecoveryError(ValueError):
    """The resource recovery packet is malformed, changed, or overbroad."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ResourceRecoveryError(f"{description} must be a canonical repository-relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or not path.parts or path.as_posix() != value or
            any(part in ("", ".", "..") for part in path.parts)):
        raise ResourceRecoveryError(f"{description} path is absolute, non-canonical, or escapes the repository")
    return path


def _regular_bytes(root: Path, relative: str, description: str,
                   *, maximum_bytes: int = MAX_MANIFEST_BYTES) -> bytes:
    path = _safe_relative(relative, f"{description} path")
    target = root
    for index, part in enumerate(path.parts):
        target = target / part
        try:
            info = target.lstat()
        except OSError as exc:
            raise ResourceRecoveryError(f"cannot read {description}: {target}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ResourceRecoveryError(f"{description} path contains a symlink: {target}")
        if index < len(path.parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ResourceRecoveryError(f"{description} parent is not a directory: {target}")
    if not stat.S_ISREG(info.st_mode) or info.st_size > maximum_bytes:
        raise ResourceRecoveryError(f"{description} is not a bounded regular file: {target}")
    try:
        return target.read_bytes()
    except OSError as exc:
        raise ResourceRecoveryError(f"cannot read {description}: {target}") from exc


def _json_object(data: bytes, description: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ResourceRecoveryError(f"{description} contains a duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ResourceRecoveryError(f"{description} contains a non-standard JSON constant: {value}")

    try:
        value = json.loads(data, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResourceRecoveryError(f"{description} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ResourceRecoveryError(f"{description} must be a JSON object")
    return value


def _bound_ref(value: object, expected_path: PurePosixPath,
               description: str) -> tuple[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ResourceRecoveryError(f"{description} must contain exactly path and sha256")
    path, digest = value.get("path"), value.get("sha256")
    if path != expected_path.as_posix():
        raise ResourceRecoveryError(f"{description} must use the registered path {expected_path}")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise ResourceRecoveryError(f"{description} must bind a lowercase SHA-256")
    return path, digest


def _read_ref(root: Path, reference: object, expected_path: PurePosixPath,
              description: str, *, maximum_bytes: int = MAX_MANIFEST_BYTES
              ) -> tuple[dict[str, Any], bytes, str]:
    path, digest = _bound_ref(reference, expected_path, description)
    raw = _regular_bytes(root, path, description, maximum_bytes=maximum_bytes)
    if sha256(raw) != digest:
        raise ResourceRecoveryError(f"{description} bytes differ from their digest")
    return _json_object(raw, description), raw, digest


def _canonical_ledger(raw: bytes, description: str) -> list[tuple[dict[str, Any], str]]:
    rows = []
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.endswith(b"\n") or line == b"\n" or line.endswith(b"\r\n"):
            raise ResourceRecoveryError(f"{description} line {index} is blank or non-canonical")
        try:
            value = json.loads(line[:-1])
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ResourceRecoveryError(f"{description} line {index} is invalid JSON") from exc
        if not isinstance(value, dict):
            raise ResourceRecoveryError(f"{description} line {index} must be an object")
        canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if canonical != line:
            raise ResourceRecoveryError(f"{description} line {index} is not canonical JSON")
        rows.append((value, sha256(line)))
    if not rows:
        raise ResourceRecoveryError(f"{description} is empty")
    return rows


def _expected_authorized_scope() -> dict[str, Any]:
    return {
        "retained_completed_groups": 55,
        "retained_c2_completed_groups": 25,
        "retained_c3_completed_groups": 30,
        "retained_failures": 2,
        "historical_c3_contract_sha256": C3_SHA256,
        "historical_c3_plan_commit": C3_PLAN_COMMIT,
        "historical_c3_source_commit": C3_SOURCE_COMMIT,
        "original_wall_origin_utc": ORIGINAL_WALL_ORIGIN_UTC,
        "deadline_utc": ORIGINAL_DEADLINE_UTC,
        "total_wall_budget_seconds": TOTAL_WALL_BUDGET_SECONDS,
        "maximum_attempts_per_group_across_contracts": MAXIMUM_ATTEMPTS_PER_GROUP,
        "execution_series": EXECUTION_SERIES,
        "case_population": 1108,
        "groups": 84,
        "report_partitions": 92,
        "report_rows": 4252,
        "analyzer_families": ANALYZER_FAMILIES,
        "minimum_launch_free_gib": 110,
        "protected_reserve_gib": 40,
        "scratch_gib": 24,
        "proposed_total_retention_ceiling_gib": 24,
        "stop_free_gib": 48,
        "working_set_gib": 12,
    }


def _validate_authorization(value: dict[str, Any]) -> None:
    expected_forbidden = [
        "Promoting failed reports",
        "Relabeling C1, C2, or C3 measurements as executed under C4",
        "Changing the original deadline, execution series, or attempt cap",
        "Changing the v0.9.0 population, analyzer families, tool bindings, or C3 command vectors",
        "Reducing the 40 GiB protected reserve or weakening the 48 GiB stop and 12 GiB working-set guards",
    ]
    if (set(value) != {"schema", "recorded_utc", "evidence_kind", "request", "human_reply",
                       "authorized_scope", "forbidden"} or
            value.get("schema") != "v092-resource-recovery-authorization/v1" or
            value.get("evidence_kind") != "human-chat-authorization-record" or
            value.get("request") != AUTHORIZATION_REQUEST or
            value.get("human_reply") != AUTHORIZATION_REPLY or
            value.get("authorized_scope") != _expected_authorized_scope() or
            value.get("forbidden") != expected_forbidden):
        raise ResourceRecoveryError("recorded authorization differs from the exact resource-only C4 scope")
    recorded = value.get("recorded_utc")
    try:
        timestamp = _datetime.datetime.fromisoformat(recorded) if isinstance(recorded, str) else None
    except ValueError as exc:
        raise ResourceRecoveryError("authorization record has no valid same-day timestamp") from exc
    if (timestamp is None or timestamp.isoformat() != recorded or timestamp.date().isoformat() != "2026-10-20" or
            timestamp.tzinfo is None or timestamp.utcoffset() != _datetime.timedelta(0)):
        raise ResourceRecoveryError("authorization record has no valid same-day timestamp")


def _artifact_reference(value: object, attempt_id: str, name: str,
                        description: str) -> tuple[str, str]:
    expected_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/{name}"
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ResourceRecoveryError(f"{description} reference has an unsupported shape")
    if value.get("path") != expected_path:
        raise ResourceRecoveryError(f"{description} reference escapes the exact attempt namespace")
    digest = value.get("sha256")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise ResourceRecoveryError(f"{description} reference has an invalid SHA-256")
    return expected_path, digest


def _verify_attempt_artifacts(root: Path, item: dict[str, Any], row: dict[str, Any],
                              *, status: str) -> None:
    attempt_id = item.get("attempt_id")
    if not isinstance(attempt_id, str) or ATTEMPT_ID.fullmatch(attempt_id) is None:
        raise ResourceRecoveryError("retained attempt ID is malformed")
    for key, name in (("started_receipt", "started.json"), ("completed_receipt", "completed.json")):
        relative, digest = _artifact_reference(item.get(key), attempt_id, name, key)
        raw = _regular_bytes(root, relative, key, maximum_bytes=MAX_RECEIPT_BYTES)
        if sha256(raw) != digest:
            raise ResourceRecoveryError(f"{key} differs from the manifest-bound receipt digest")
        receipt = _json_object(raw, key)
        if key == "completed_receipt" and receipt != row:
            raise ResourceRecoveryError("completed receipt bytes do not equal the sealed ledger row")
        if key == "started_receipt":
            for field in (
                "execution_series", "group_id", "attempt_id", "source_commit", "plan_commit",
                "contract_sha256", "runner_source_sha256", "fixture_revision", "population",
                "tool", "tool_binding", "identity_components", "qualification", "source_inputs",
                "cache_root", "argv", "environment", "execution_root", "output_roots",
                "case_ids", "deadline_seconds",
            ):
                if field not in row or receipt.get(field) != row[field]:
                    raise ResourceRecoveryError(f"started receipt differs from ledger row: {field}")
            if (receipt.get("status") != "started" or receipt.get("end_utc") is not None or
                    receipt.get("start_utc") != row.get("start_utc")):
                raise ResourceRecoveryError("started receipt state differs from retained attempt")
    if item.get("status") != status or row.get("status") != status:
        raise ResourceRecoveryError("manifest attempt status differs from its sealed ledger row")


def _historical_contract(value: object) -> dict[str, str]:
    expected = {
        "path": C3_ARCHIVE.as_posix(),
        "sha256": C3_SHA256,
        "canonical_path": C3_CANONICAL_PATH.as_posix(),
        "plan_commit": C3_PLAN_COMMIT,
        "source_commit": C3_SOURCE_COMMIT,
    }
    if not isinstance(value, dict) or set(value) != set(expected) or value != expected:
        raise ResourceRecoveryError("resource recovery does not name the exact original C3 contract identity")
    return expected


def _read_c3_archive(root: Path, reference: dict[str, str]) -> tuple[dict[str, Any], bytes]:
    raw = _regular_bytes(root, reference["path"], "immutable C3 contract archive", maximum_bytes=MAX_MANIFEST_BYTES * 16)
    if sha256(raw) != C3_SHA256:
        raise ResourceRecoveryError("immutable C3 contract archive digest changed")
    contract = _json_object(raw, "immutable C3 contract archive")
    if (contract.get("release") != "v0.9.2" or contract.get("execution_authorized") is not True or
            contract.get("execution_series") != EXECUTION_SERIES or
            contract.get("source_commit") != C3_SOURCE_COMMIT or
            contract.get("total_wall_budget_seconds") != TOTAL_WALL_BUDGET_SECONDS or
            not isinstance(contract.get("groups"), list) or len(contract["groups"]) != 84 or
            not isinstance(contract.get("tools"), dict) or not isinstance(contract.get("tool_components"), dict)):
        raise ResourceRecoveryError("archived C3 contract has changed its authorized execution identity")
    if {group.get("family") for group in contract["groups"] if isinstance(group, dict)} != set(ANALYZER_FAMILIES):
        raise ResourceRecoveryError("archived C3 contract no longer binds the exact eight analyzer families")
    scoped = contract.get("scoped_recovery")
    if (not isinstance(scoped, dict) or set(scoped) != {"path", "sha256"} or
            scoped.get("path") != C3_SCOPED_MANIFEST_PATH.as_posix() or
            not isinstance(scoped.get("sha256"), str) or SHA256.fullmatch(scoped["sha256"]) is None):
        raise ResourceRecoveryError("archived C3 contract no longer binds the original scoped-recovery packet")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", C3_SOURCE_COMMIT, C3_PLAN_COMMIT],
            cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        canonical = subprocess.check_output(
            ["git", "show", f"{C3_PLAN_COMMIT}:{C3_CANONICAL_PATH.as_posix()}"],
            cwd=root, stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ResourceRecoveryError("cannot prove the original C3 source-to-plan ancestry and contract bytes") from exc
    if canonical != raw:
        raise ResourceRecoveryError("C3 archive differs from its original canonical contract bytes")
    return contract, raw


def _validate_roster(root: Path, manifest: dict[str, Any],
                     prefix_rows: list[tuple[dict[str, Any], str]],
                     c3_contract: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    completed_items = manifest.get("retained_completed")
    failure_items = manifest.get("retained_failures")
    if not isinstance(completed_items, list) or len(completed_items) != 55:
        raise ResourceRecoveryError("resource recovery must retain exactly 55 completed measurements")
    if not isinstance(failure_items, list) or len(failure_items) != 2:
        raise ResourceRecoveryError("resource recovery must preserve exactly two historical failures")
    required_item_keys = {
        "group_id", "attempt_id", "status", "contract_sha256", "source_commit", "plan_commit",
        "ledger_line_sha256", "started_receipt", "completed_receipt",
    }
    if any(not isinstance(item, dict) or set(item) != required_item_keys
           for item in completed_items + failure_items):
        raise ResourceRecoveryError("retained roster entries have unknown or missing fields")

    by_line = {line_sha: row for row, line_sha in prefix_rows}
    if len(by_line) != PREFIX_LINES:
        raise ResourceRecoveryError("sealed historical prefix contains duplicate line digests")
    expected_contracts = {
        C1_SHA256: (C1_SOURCE_COMMIT, C1_PLAN_COMMIT),
        C2_SHA256: (C2_SOURCE_COMMIT, C2_PLAN_COMMIT),
        C3_SHA256: (C3_SOURCE_COMMIT, C3_PLAN_COMMIT),
    }
    completed_lines: set[str] = set()
    failure_lines: set[str] = set()
    completed_groups: set[str] = set()
    completed_c2 = completed_c3 = 0
    failure_ids: set[str] = set()
    attempt_numbers: dict[str, list[int]] = {}
    observed = {"c1-failure": 0, "c2-completed": 0, "c2-failure": 0, "c3-completed": 0}
    c3_groups = {group.get("id"): group for group in c3_contract["groups"] if isinstance(group, dict)}
    if len(c3_groups) != 84 or len(c3_groups) != len(c3_contract["groups"]):
        raise ResourceRecoveryError("archived C3 contract group roster is not exactly 84 unique groups")

    for row, line_sha in prefix_rows:
        group_id = row.get("group_id")
        attempt_id = row.get("attempt_id")
        contract_sha = row.get("contract_sha256")
        status = row.get("status")
        context = expected_contracts.get(contract_sha)
        if (not isinstance(group_id, str) or not isinstance(attempt_id, str) or
                ATTEMPT_ID.fullmatch(attempt_id) is None or context is None or
                row.get("source_commit") != context[0] or row.get("plan_commit") != context[1] or
                row.get("execution_series") != EXECUTION_SERIES):
            raise ResourceRecoveryError("historical ledger row has foreign contract, source, plan, or series provenance")
        attempt_number = int(attempt_id.split("-attempt-")[1].split("-series-")[0])
        if attempt_number > MAXIMUM_ATTEMPTS_PER_GROUP:
            raise ResourceRecoveryError("historical ledger row exceeds the original two-attempt cap")
        attempt_numbers.setdefault(group_id, []).append(attempt_number)
        if contract_sha == C1_SHA256:
            if (group_id != "bifrost-c-kernel" or attempt_id != "bifrost-c-kernel-attempt-01-series-01" or
                    status != "recorder-error"):
                raise ResourceRecoveryError("C1 prefix row differs from the one registered historical failure")
            observed["c1-failure"] += 1
        elif contract_sha == C2_SHA256:
            if status == "completed":
                observed["c2-completed"] += 1
                completed_c2 += 1
            elif (group_id == "codeql-java-modeling" and
                  attempt_id == "codeql-java-modeling-attempt-01-series-01" and status == "failed"):
                observed["c2-failure"] += 1
            else:
                raise ResourceRecoveryError("C2 prefix row is not a registered completion or the C2 failure")
        elif contract_sha == C3_SHA256:
            if status != "completed" or row.get("source_commit") != C3_SOURCE_COMMIT:
                raise ResourceRecoveryError("C3 prefix contains a non-completed or relabeled measurement")
            group = c3_groups.get(group_id)
            if not isinstance(group, dict):
                raise ResourceRecoveryError("C3 ledger row names a group outside the original C3 contract")
            for key, expected in (("tool", group.get("tool")), ("case_ids", group.get("case_ids")),
                                  ("deadline_seconds", group.get("deadline_seconds"))):
                if row.get(key) != expected:
                    raise ResourceRecoveryError(f"C3 ledger row differs from its original contract: {key}")
            if row.get("argv") != group.get("argv"):
                raise ResourceRecoveryError("C3 ledger argv differs from its original contract")
            environment = row.get("environment")
            if not isinstance(environment, dict) or any(
                    environment.get(key) != value for key, value in group.get("environment", {}).items()
                    if key not in {"HOME", "TMPDIR"}):
                raise ResourceRecoveryError("C3 ledger environment differs from its original contract")
            if not isinstance(row.get("runner_source_sha256"), str) or not SHA256.fullmatch(row["runner_source_sha256"]):
                raise ResourceRecoveryError("C3 ledger row lacks its original runner source digest")
            if row.get("runner_source_sha256") != c3_contract.get("runner_source_sha256"):
                raise ResourceRecoveryError("C3 ledger runner digest differs from the original C3 contract")
            if row.get("tool_binding") != c3_contract["tools"].get(group.get("tool")):
                raise ResourceRecoveryError("C3 ledger tool binding differs from the original C3 contract")
            observed["c3-completed"] += 1
            completed_c3 += 1
        else:
            raise ResourceRecoveryError("historical ledger prefix contains an unsupported contract")

    if observed != {"c1-failure": 1, "c2-completed": 25, "c2-failure": 1, "c3-completed": 30}:
        raise ResourceRecoveryError("historical prefix differs from the exact 25 C2, 30 C3, and two-failure scope")
    for group_id, numbers in attempt_numbers.items():
        if numbers != list(range(1, len(numbers) + 1)):
            raise ResourceRecoveryError(f"{group_id}: historical attempt numbering is not contiguous")

    def validate(items: list[dict[str, Any]], *, completed: bool) -> None:
        claimed = completed_lines if completed else failure_lines
        for item in items:
            line_sha = item.get("ledger_line_sha256")
            row = by_line.get(line_sha)
            if row is None or line_sha in completed_lines or line_sha in failure_lines:
                raise ResourceRecoveryError("retained roster references an absent or duplicate ledger line")
            expected_status = "completed" if completed else row.get("status")
            expected = {
                "group_id": row.get("group_id"),
                "attempt_id": row.get("attempt_id"),
                "status": expected_status,
                "contract_sha256": row.get("contract_sha256"),
                "source_commit": row.get("source_commit"),
                "plan_commit": row.get("plan_commit"),
                "ledger_line_sha256": line_sha,
            }
            if any(item.get(key) != value or (key != "ledger_line_sha256" and row.get(key) != value)
                   for key, value in expected.items()):
                raise ResourceRecoveryError("retained roster differs from its original ledger row")
            if completed:
                if row.get("status") != "completed":
                    raise ResourceRecoveryError("failed historical evidence cannot enter the completion roster")
                if row["group_id"] in completed_groups:
                    raise ResourceRecoveryError("retained completion roster repeats a completed group")
                completed_groups.add(row["group_id"])
                if row["contract_sha256"] == C2_SHA256:
                    pass
                elif row["contract_sha256"] != C3_SHA256:
                    raise ResourceRecoveryError("only C2 and C3 completions may be retained")
            elif row.get("status") not in {"failed", "recorder-error"}:
                raise ResourceRecoveryError("failure roster contains non-failure evidence")
            _verify_attempt_artifacts(root, item, row, status=expected_status)
            claimed.add(line_sha)

    validate(completed_items, completed=True)
    validate(failure_items, completed=False)
    if (len(completed_lines) != 55 or len(failure_lines) != 2 or
            completed_c2 != 25 or completed_c3 != 30):
        raise ResourceRecoveryError("retained rosters do not account for the exact 55 completions and two failures")
    expected_failure_ids = {
        "bifrost-c-kernel-attempt-01-series-01",
        "codeql-java-modeling-attempt-01-series-01",
    }
    failure_ids.update(item["attempt_id"] for item in failure_items)
    if failure_ids != expected_failure_ids or completed_lines | failure_lines != set(by_line):
        raise ResourceRecoveryError("retained rosters omit or add historical ledger attempts")
    return completed_items, failure_items


def validate_packet(root: str | Path, reference: object) -> dict[str, Any]:
    """Validate the authorized C4 packet without executing or selecting attempts.

    The returned tail rows are only canonicalized and hashed. A C4 checker must
    validate them under the new contract and must independently replay retained
    rows under their original C1/C2/C3 contexts.
    """
    repository = Path(root).resolve()
    manifest_path, manifest_sha = _bound_ref(reference, MANIFEST_PATH, "resource_recovery")
    manifest_raw = _regular_bytes(repository, manifest_path, "resource recovery manifest")
    if sha256(manifest_raw) != manifest_sha:
        raise ResourceRecoveryError("resource recovery manifest digest mismatch")
    manifest = _json_object(manifest_raw, "resource recovery manifest")
    expected_keys = {
        "schema", "authorization", "historical_contract", "ledger_prefix", "retained_completed",
        "retained_failures", "original_wall_origin_utc", "deadline_utc", "execution_series",
        "total_wall_budget_seconds", "maximum_attempts_per_group", "scope", "resource_budget",
        "resource_guards",
    }
    if set(manifest) != expected_keys or manifest.get("schema") != "v092-resource-recovery-manifest/v1":
        raise ResourceRecoveryError("resource recovery manifest has an unknown schema or field")
    history = _historical_contract(manifest.get("historical_contract"))
    if (manifest.get("original_wall_origin_utc") != ORIGINAL_WALL_ORIGIN_UTC or
            manifest.get("deadline_utc") != ORIGINAL_DEADLINE_UTC or
            manifest.get("execution_series") != EXECUTION_SERIES or
            manifest.get("total_wall_budget_seconds") != TOTAL_WALL_BUDGET_SECONDS or
            manifest.get("maximum_attempts_per_group") != MAXIMUM_ATTEMPTS_PER_GROUP or
            manifest.get("scope") != (
                "Retain the 25 original C2 and 30 original C3 completions plus both historical failures; "
                "continue only remaining groups under C4 resource changes with source, contract, and "
                "attempt provenance preserved."
            ) or
            manifest.get("resource_budget") != {
                "minimum_launch_free_gib": 110,
                "protected_reserve_gib": 40,
                "scratch_gib": 24,
                "proposed_total_retention_ceiling_gib": 24,
            } or
            manifest.get("resource_guards") != {"stop_free_gib": 48, "working_set_gib": 12}):
        raise ResourceRecoveryError("resource recovery changes the original clock, scope, or guarded resource limits")

    authorization, authorization_raw, authorization_sha = _read_ref(
        repository, manifest.get("authorization"), AUTHORIZATION_PATH,
        "resource recovery authorization",
    )
    _validate_authorization(authorization)

    prefix_ref = manifest.get("ledger_prefix")
    if not isinstance(prefix_ref, dict) or set(prefix_ref) != {"path", "sha256", "bytes", "lines"}:
        raise ResourceRecoveryError("ledger_prefix has an unsupported shape")
    if (prefix_ref.get("path") != PREFIX_PATH.as_posix() or
            prefix_ref.get("sha256") != PREFIX_SHA256 or
            prefix_ref.get("bytes") != PREFIX_BYTES or prefix_ref.get("lines") != PREFIX_LINES):
        raise ResourceRecoveryError("ledger prefix differs from the exact registered 57-line C1/C2/C3 prefix")
    prefix_raw = _regular_bytes(
        repository, prefix_ref["path"], "sealed historical ledger prefix", maximum_bytes=MAX_PREFIX_BYTES,
    )
    if len(prefix_raw) != PREFIX_BYTES or sha256(prefix_raw) != PREFIX_SHA256:
        raise ResourceRecoveryError("sealed historical ledger prefix bytes or digest changed")
    prefix_rows = _canonical_ledger(prefix_raw, "sealed historical ledger prefix")
    if len(prefix_rows) != PREFIX_LINES:
        raise ResourceRecoveryError("sealed historical ledger prefix line count changed")
    current_raw = _regular_bytes(
        repository, LEDGER_PATH.as_posix(), "current execution ledger", maximum_bytes=MAX_LEDGER_BYTES,
    )
    if not current_raw.startswith(prefix_raw):
        raise ResourceRecoveryError("current ledger no longer begins with the exact sealed C1/C2/C3 prefix")
    tail_raw = current_raw[len(prefix_raw):]
    tail_rows = _canonical_ledger(tail_raw, "post-prefix execution ledger") if tail_raw else []

    c3_contract, c3_contract_raw = _read_c3_archive(repository, history)
    _validate_roster(repository, manifest, prefix_rows, c3_contract)

    return {
        "repo_root": repository,
        "manifest": manifest,
        "manifest_raw": manifest_raw,
        "manifest_sha256": manifest_sha,
        "manifest_path": manifest_path,
        "authorization": authorization,
        "authorization_raw": authorization_raw,
        "authorization_sha256": authorization_sha,
        "prefix_bytes": prefix_raw,
        "sealed_prefix_sha256": PREFIX_SHA256,
        "prefix_rows": prefix_rows,
        "tail_rows": tail_rows,
        "historical_contract_ref": history,
        "historical_contract": c3_contract,
        "historical_contract_raw": c3_contract_raw,
        "retained_completed": manifest["retained_completed"],
        "retained_failures": manifest["retained_failures"],
    }
