#!/usr/bin/env python3
"""Cycle-free, fail-closed protocol for the Bifrost v0.14.0 replacement-15.

Importing this file and calling its ``validate_*`` functions are intentionally
side-effect free: the release executor is not imported, no analyzer process is
started, no lock is acquired, no ledger row is appended, and no workspace is
materialized.  The explicit ``write_immutable`` helper is reserved for a
separately reviewed admission/supervisor implementation and uses exclusive
creation; validation itself never calls it.

Runtime graph validation uses read-only Git object queries to bind scripts
already covered by the immutable executor's source snapshot directory roster.

The important boundary is the immutable ``manifest-identity.json``.  Group
admissions bind that identity and the final manifest *path*, but never the
final manifest digest.  Phase and completion sidecars are created outside the
final manifest and may therefore bind its digest.  Runtime receipts are
selected by an explicit group slot rather than by one release-wide receipt.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[4]
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
CANONICAL_LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"
IDENTITY_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-15/manifest-identity.json"
MANIFEST_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-15/manifest.json"
ADMISSION_SOURCE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-15.py"
SUPERVISOR_SOURCE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-15.py"

IDENTITY_SCHEMA = "v092-bifrost-v0140-execution-core-identity/v3"
MANIFEST_SCHEMA = "v092-bifrost-v0140-replacement-15/v1"
GROUP_ADMISSION_SCHEMA = "v092-bifrost-v0140-replacement-admission/v3"
PARENT_ADMISSION_SCHEMA = "v092-bifrost-v0140-parent-admission/v1"
PHASE_GATE_SCHEMA = "v092-bifrost-v0140-phase-gate/v2"
COMPLETION_SCHEMA = "v092-bifrost-v0140-replacement-completion/v3"
CONFIG_ADMISSION_SCHEMA = "v092-bifrost-v0140-configuration-admission/v1"
CONFIG_RECEIPT_SCHEMA = "v092-bifrost-v0140-configuration-receipt/v1"
PERMIT_SCHEMA = "v092-bifrost-v0140-supervisor-permit/v1"

ORIGIN = "2026-10-20T00:57:00.680937+00:00"
HISTORICAL_CUTOFF = "2026-10-23T21:33:00.680937+00:00"
CUTOFF = None
HISTORICAL_TOTAL_WALL_SECONDS = 333360
TOTAL_WALL_SECONDS = None
RESOURCE_POLICY = {
    "minimum_free_gib": 127,
    "minimum_remaining_reserve_seconds": None,
    "minimum_replacement_seconds": 13592,
    "startup_seconds": 600,
    "aggregate_source_working_gib": 30,
    "per_source_projection_gib": 12,
}
REVIEW_TYPES = [
    "independent-bifrost-v0140-replacement-review",
    "final-bifrost-v0140-replacement-review",
]
SOURCE_NAMES = ("implementation", "focused_tests", "helper", "supervisor", "bridge", "bridge_tests")
PREDECESSOR87_SHA256 = "57d8265e8eb0c216c56e184a5fed36f9931bcb5b36ea1047ae3f4a0c71f0a096"
ORIGINAL_PREFIX_SHA256 = "9ae98c51570149cc7ebe86573df518b4f469188e23dd58d7bcdc37ac93532476"
BRIDGE_SOURCE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-10.py"
BRIDGE_TEST_PATH = "reports/releases/v0.9.2/acquisition/test-bifrost-v0140-frozen-parser-10.py"
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")

# These are deliberately exact top-level field sets.  Nested evidence is
# checked by type and identity below, but a new top-level runtime field must
# go through a new protocol version rather than being silently ignored.
CORE_FIELDS = {
    "schema", "original_origin_utc", "cutoff_utc", "total_wall_budget_seconds", "execution_window_authority", "aggregate_source_working_authority",
    "source_commit", "plan_commit", "contract", "continuation", "runner", "binary",
    "runner_artifact", "runner_environment", "executor_environment", "source_design",
    "qualification", "control_review", "original_prefix", "continuation_prefix",
    "replacement_groups", "resource_policy", "lock_path", "sidecar_namespace",
    "implementation", "implementation_test", "bifrost_admission_source",
    "bifrost_supervisor_source", "review_policy", "frozen_bridge_source", "frozen_bridge_tests",
    "source_contexts", "source_evidence", "configuration_output",
    "breadth_first_authority", "incoming_history", "runtime_module_graph", "source_inputs", "manifest_path",
}
MANIFEST_FIELDS = {
    "schema", "finalized", "core_identity", "independent_review", "final_review",
    "bifrost_admission_source", "bifrost_supervisor_source", "execution_admission_slots",
    "configuration_admission_slot",
}
SLOT_FIELDS = {
    "group_id", "attempt_id", "admission_path", "completion_path", "phase_gate_path",
    "predecessor_attempt_id", "predecessor_receipt_path",
}
GROUP_ADMISSION_FIELDS = {
    "schema", "status", "automatic_retry", "group_id", "attempt_id", "phase",
    "core_identity", "manifest_path", "source_commit", "plan_commit", "contract_sha256",
    "ledger_prefix", "superseded_attempt_id", "superseded_receipt_sha256",
    "ledger_before_sha256", "process_ownership", "lock", "fresh_namespace",
    "admission_source", "supervisor_source", "helper", "supervisor_permit",
    "resource_policy", "resource_policy_sha256", "remaining_reserved_seconds",
}
PHASE_FIELDS = {
    "schema", "manifest_path", "manifest_sha256", "core_identity", "admission_ref", "group_id",
    "attempt_id", "phase", "source_commit", "plan_commit", "contract_sha256",
    "remaining_seconds", "minimum_remaining_reserve_seconds", "minimum_replacement_seconds",
    "startup_seconds", "minimum_free_gib", "observed_free_bytes", "resource_floor_checked",
    "no_foreign_processes", "exclusive_lock_checked", "lock_held", "fresh_sidecar_namespace",
    "source_snapshot_checked", "helper", "supervisor", "supervisor_permit",
}
COMPLETION_FIELDS = {
    "schema", "status", "automatic_retry", "manifest_path", "manifest_sha256", "core_identity",
    "group_id", "attempt_id", "admission_ref", "admission_sha256", "phase_gate_ref",
    "phase_gate_sha256", "completed_receipt_sha256", "ledger_before_sha256",
    "ledger_after_sha256", "continuation_safety",
}
CONFIG_FIELDS = {
    "schema", "status", "automatic_retry", "scope", "core_identity", "manifest_path",
    "manifest_sha256", "admission_source", "supervisor_source", "helper", "supervisor",
    "supervisor_permit", "resource_policy", "resource_policy_sha256",
    "remaining_reserved_seconds",
}
CONFIG_RECEIPT_FIELDS = {
    "schema", "status", "automatic_retry", "core_identity", "manifest_path",
    "manifest_sha256", "output_path", "output_sha256", "partitions", "rows", "known_stale",
}

_FORBIDDEN_CORE_KEYS = {
    "independent_review", "final_review", "execution_admission", "execution_admission_slots",
    "configuration_admission", "configuration_admission_slot", "manifest_path",
    "manifest_sha256", "phase_gate", "phase_gate_path", "completion", "completion_path",
    "dispatch", "launcher", "permit", "ledger_after_sha256", "ledger_transition",
}


class Replacement15Error(ValueError):
    """A static or runtime protocol binding failed closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise Replacement15Error(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _relative(value: object, label: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{label} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts), f"unsafe {label}")
    return path


def _read(root: Path, path: str) -> bytes:
    current = Path(root)
    for part in _relative(path).parts:
        current /= part
        require(not current.is_symlink(), f"symlink in bound path: {path}")
    require(current.is_file(), f"missing bound file: {path}")
    return current.read_bytes()


def _ref(value: object, label: str = "binding", *, rows: bool = False) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    allowed = {"path", "sha256"} | ({"rows"} if rows else set())
    require(set(value) == allowed, f"{label} has an unexpected field set")
    _relative(value.get("path"), f"{label} path")
    require(isinstance(value.get("sha256"), str) and SHA_RE.fullmatch(value["sha256"]),
            f"{label} SHA is malformed")
    if rows:
        require(type(value.get("rows")) is int and value["rows"] > 0, f"{label} rows malformed")
    return value


def _bound(root: Path, value: object, label: str = "binding", *, rows: bool = False) -> bytes:
    ref = _ref(value, label, rows=rows)
    raw = _read(root, ref["path"])
    require(sha256(raw) == ref["sha256"], f"{label} bytes changed: {ref['path']}")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Replacement15Error(f"{label} is not valid JSON") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _json_ref(root: Path, value: object, label: str, *, exact_fields: set[str] | None = None) -> dict[str, Any]:
    raw = _bound(root, value, label)
    loaded = _json(raw, label)
    if exact_fields is not None:
        require(set(loaded) == exact_fields, f"{label} has an unexpected field set")
    return loaded


def _jsonl(raw: bytes, label: str) -> list[dict[str, Any]]:
    """Parse immutable ledger bytes without normalizing or rewriting them."""
    require(raw and raw.endswith(b"\n"), f"{label} is not a complete newline-terminated ledger")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Replacement15Error(f"{label} line {index} is not valid JSON") from exc
        require(isinstance(value, dict), f"{label} line {index} is not an object")
        rows.append(value)
    require(rows, f"{label} is empty")
    return rows


def _slot_witness_path(slot_path: str, name: str) -> str:
    parent = PurePosixPath(slot_path).parent
    return str(parent / name)


def _successful_identity(value: dict[str, Any], *, group_id: str, attempt_id: str,
                         source_commit: str, plan_commit: str, contract_sha256: str,
                         execution_series: int, label: str) -> None:
    _commit(source_commit, f"{label} source_commit")
    _commit(plan_commit, f"{label} plan_commit")
    _sha(contract_sha256, f"{label} contract_sha256")
    require(value.get("status") == "completed" and value.get("exit_code") == 0 and
            value.get("timed_out") is False and value.get("capacity_loss") is None and
            value.get("tool") == "bifrost" and value.get("group_id") == group_id and
            value.get("attempt_id") == attempt_id and
            value.get("source_commit") == source_commit and
            value.get("plan_commit") == plan_commit and
            value.get("contract_sha256") == contract_sha256 and
            value.get("execution_series") == execution_series,
            f"{label} does not carry the exact successful attempt identity")


def _validate_predecessor(root: Path, core: dict[str, Any], slot: dict[str, Any],
                          group_id: str) -> dict[str, Any]:
    """Bind the predecessor receipt to its immutable prefix ledger row."""
    prefix_raw = _bound(root, core["continuation_prefix"], "continuation prefix", rows=True)
    prefix_rows = _jsonl(prefix_raw, "continuation prefix")
    predecessor_attempt = slot["predecessor_attempt_id"]
    matches = [row for row in prefix_rows if row.get("attempt_id") == predecessor_attempt]
    require(len(matches) == 1, f"continuation prefix lacks one predecessor row for {group_id}")
    row = matches[0]
    predecessor_raw = _read(root, slot["predecessor_receipt_path"])
    predecessor = _json(predecessor_raw, "predecessor completed receipt")
    _successful_identity(predecessor, group_id=group_id, attempt_id=predecessor_attempt,
                         source_commit=str(row.get("source_commit")),
                         plan_commit=str(row.get("plan_commit")),
                         contract_sha256=str(row.get("contract_sha256")),
                         execution_series=1, label="predecessor receipt")
    for key in ("status", "group_id", "attempt_id", "source_commit", "plan_commit", "contract_sha256",
                "exit_code", "timed_out", "capacity_loss", "execution_series", "tool"):
        require(predecessor.get(key) == row.get(key),
                f"predecessor receipt and ledger row differ for {key}")
    return {"row": row, "receipt": predecessor, "receipt_raw": predecessor_raw,
            "row_count": len(prefix_rows)}


def _validate_ledger_before(root: Path, manifest: dict[str, Any], core: dict[str, Any],
                            slot: dict[str, Any], value: dict[str, Any], *,
                            group_id: str) -> bytes:
    """Require the exact ordered ledger predecessor for this replacement slot.

    The first replacement group must start from the immutable continuation
    prefix.  Every later group must start from the previous slot's immutable
    completion witness.  Digest agreement alone is insufficient: a caller
    must not be able to substitute an unrelated, otherwise-valid ledger by
    updating ``ledger_before_sha256``.
    """
    before_path = _slot_witness_path(slot["admission_path"], "ledger-before.jsonl")
    before_raw = _read(root, before_path)
    require(sha256(before_raw) == value["ledger_before_sha256"],
            "ledger-before digest does not match immutable bytes")
    groups = core["replacement_groups"]
    require(group_id in groups, "ledger-before group is outside replacement order")
    index = groups.index(group_id)
    if index == 0:
        expected_raw = _bound(root, core["continuation_prefix"],
                              "continuation prefix", rows=True)
        expected_label = "immutable continuation prefix"
    else:
        previous_group = groups[index - 1]
        previous_slot = manifest["execution_admission_slots"][previous_group]
        expected_path = _slot_witness_path(previous_slot["completion_path"], "ledger-after.jsonl")
        expected_raw = _read(root, expected_path)
        prior_admission = validate_group_admission(root, MANIFEST_PATH, previous_group,
                                                    previous_slot["admission_path"])
        prior_phase = validate_phase_gate(root, MANIFEST_PATH, previous_group,
                                         previous_slot["phase_gate_path"], prior_admission["ref"])
        validate_completion(root, MANIFEST_PATH, previous_group,
                            previous_slot["completion_path"], prior_admission["ref"], prior_phase["ref"])
        expected_label = f"previous completion witness for {previous_group}"
    require(before_raw == expected_raw,
            f"ledger-before is not the exact {expected_label}")
    _jsonl(before_raw, "ledger-before witness")
    return before_raw


def _validate_ledger_transition(root: Path, slot: dict[str, Any], value: dict[str, Any],
                                *, group_id: str, source_commit: str, plan_commit: str,
                                contract_sha256: str) -> tuple[bytes, bytes, dict[str, Any]]:
    before_path = _slot_witness_path(slot["admission_path"], "ledger-before.jsonl")
    after_path = _slot_witness_path(slot["completion_path"], "ledger-after.jsonl")
    before_raw = _read(root, before_path)
    after_raw = _read(root, after_path)
    require(sha256(before_raw) == value["ledger_before_sha256"],
            "ledger-before digest does not match immutable bytes")
    before_rows = _jsonl(before_raw, "ledger-before witness")
    after_rows = _jsonl(after_raw, "ledger-after witness")
    require(after_raw.startswith(before_raw) and len(after_rows) == len(before_rows) + 1 and after_rows[:-1] == before_rows,
            "ledger transition is not exactly one appended row")
    appended = after_rows[-1]
    _terminal_identity(appended, group_id=group_id, attempt_id=slot["attempt_id"],
                         source_commit=source_commit, plan_commit=plan_commit,
                         contract_sha256=contract_sha256, execution_series=2,
                         label="ledger-after row")
    return before_raw, after_raw, appended


def _commit(value: object, label: str) -> None:
    require(isinstance(value, str) and COMMIT_RE.fullmatch(value), f"{label} is not a commit SHA")


def _sha(value: object, label: str) -> None:
    require(isinstance(value, str) and SHA_RE.fullmatch(value), f"{label} is not a SHA-256")


def _same_ref(actual: object, expected: object, label: str) -> None:
    require(actual == expected, f"{label} binding differs")


def _ref_or_object(root: Path, value: object, label: str) -> None:
    """Check a runner/binary identity without interpreting its command."""
    require(isinstance(value, dict), f"{label} must be an object")
    require(isinstance(value.get("path"), str) and value["path"] and
            "\x00" not in value["path"], f"{label} lacks a safe path")
    _sha(value.get("sha256"), f"{label} SHA")
    path = Path(value["path"])
    if path.is_absolute():
        # Frozen tool identities name absolute executables.  Preserve that
        # identity verbatim, and verify its bytes; rebasing it to a relative
        # alias would disagree with the qualified contract and runner artifact.
        require(str(path) == value["path"] and path.resolve() == path and
                path.is_file() and not path.is_symlink(),
                f"{label} absolute executable is missing or indirect")
        require(sha256(path.read_bytes()) == value["sha256"], f"{label} executable digest differs")
    else:
        _relative(value["path"], f"{label} path")
        _bound(root, {"path": value["path"], "sha256": value["sha256"]}, label)


def _forbidden_core(value: Any, where: str = "core_identity") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(key not in _FORBIDDEN_CORE_KEYS,
                    f"{where} contains runtime/review field {key}")
            _forbidden_core(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _forbidden_core(child, f"{where}[{index}]")


def _forbidden_root_core(identity: dict[str, Any]) -> None:
    """Allow only the canonical root manifest path, never runtime receipts.

    The path is a static cycle-free identity field; the recursive prohibition
    still applies unchanged to every other value and to all nested mappings.
    """
    require(identity.get("manifest_path") == MANIFEST_PATH,
            "core manifest path is not canonical replacement15")
    for key, child in identity.items():
        if key == "manifest_path":
            continue
        require(key not in _FORBIDDEN_CORE_KEYS,
                f"core_identity contains runtime/review field {key}")
        _forbidden_core(child, f"core_identity.{key}")


def _attempt_id(group: str) -> str:
    require(isinstance(group, str) and group.startswith("bifrost-") and group != "bifrost-",
            "replacement group is not a Bifrost group")
    number = 3 if group == "bifrost-c-kernel" else 2
    return f"{group}-attempt-{number:02d}-series-02"


def _namespace_path(namespace: str, path: str, label: str) -> None:
    _relative(path, label)
    require(path.startswith(namespace.rstrip("/") + "/"),
            f"{label} escapes the reviewed sidecar namespace")


def _typed_process(value: object) -> None:
    require(isinstance(value, dict), "process ownership evidence is missing")
    require(value.get("schema") == "invocation-process-ownership/v1" and
            value.get("status") == "verified" and value.get("automatic_retry") is False,
            "process ownership evidence is not verified")
    require(type(value.get("pid")) is int and value["pid"] > 0,
            "process ownership evidence lacks a positive pid")
    require(value.get("no_foreign_processes") is True, "foreign process evidence is not clear")
    require(value.get("birth_identity") or value.get("process_birth_identity") or
            isinstance(value.get("tracked_processes"), list),
            "process ownership evidence lacks a birth/contender witness")


def _typed_lock(value: object, expected_path: str) -> None:
    require(isinstance(value, dict), "lock evidence is missing")
    require(value.get("schema") == "exclusive-lock/v1" and value.get("status") == "held" and
            value.get("automatic_retry") is False and value.get("path") == expected_path and
            type(value.get("owner_pid")) is int and value["owner_pid"] > 0,
            "lock evidence does not hold the exact reviewed lock")


def _typed_namespace(value: object, expected_path: str) -> None:
    require(isinstance(value, dict), "namespace evidence is missing")
    require(value.get("schema") == "fresh-sidecar-namespace/v1" and
            value.get("status") == "fresh" and value.get("path") == expected_path and
            value.get("fresh") is True and value.get("sidecar_count") == 0,
            "sidecar namespace is not fresh")


def _permit(value: object, *, identity: dict[str, Any], manifest_path: str,
            helper: dict[str, str], supervisor: dict[str, str], scope: str,
            group: str | None = None, attempt: str | None = None) -> None:
    require(isinstance(value, dict), "supervisor permit is missing")
    expected_fields = {"schema", "status", "automatic_retry", "scope", "core_identity",
                       "manifest_path", "helper", "supervisor", "permit_id"}
    if group is not None:
        expected_fields |= {"group_id", "attempt_id"}
    require(set(value) == expected_fields, "supervisor permit has an unexpected field set")
    require(value.get("schema") == PERMIT_SCHEMA and value.get("status") == "permitted" and
            value.get("automatic_retry") is False and value.get("scope") == scope,
            "supervisor permit is not the reviewed one-shot scope")
    _same_ref(value.get("core_identity"), identity, "permit core identity")
    require(value.get("manifest_path") == manifest_path, "permit manifest path differs")
    _same_ref(value.get("helper"), helper, "permit helper")
    _same_ref(value.get("supervisor"), supervisor, "permit supervisor")
    require(isinstance(value.get("permit_id"), str) and value["permit_id"],
            "permit lacks a stable permit id")
    if group is not None:
        require(value.get("group_id") == group and value.get("attempt_id") == attempt,
                "group permit identity differs")


def _policy_sha(policy: Mapping[str, Any]) -> str:
    return sha256(canonical_json(dict(policy)))


WINDOW_AUTHORITY = {"path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json", "sha256": "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc"}


WORKING_CAP_AUTHORITY = {"path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/source-working-cap-30gib-authorization-01.json", "sha256": "bcba59ae10ea1cea565641249a0dc3bddfd063c66f298e19ce2ce0b86743cdbe"}
AGGREGATE_WORKING_BYTES = 30 * 1024**3
PER_SOURCE_PROJECTION_BYTES = 12 * 1024**3


def validate_working_cap(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    require(core.get("aggregate_source_working_authority") == WORKING_CAP_AUTHORITY,
            "core lacks exact aggregate source-working authority")
    value = _json(_bound(root, WORKING_CAP_AUTHORITY, "aggregate source-working authority"), "aggregate source-working authority")
    change = value.get("authorized_change", {})
    unchanged = value.get("unchanged", {})
    require(value.get("status") == "human-authorized-append-only-reviewed-amendment-required" and
            change.get("category") == "aggregate-source-working-set" and
            change.get("unit") == "GiB" and change.get("after_gib") == 30 and
            change.get("after_bytes") == AGGREGATE_WORKING_BYTES and
            change.get("before_gib") == 12 and change.get("before_bytes") == PER_SOURCE_PROJECTION_BYTES and
            unchanged == {"all_raw_evidence_and_historical_counters": "preserved", "analyzer_slots": 1,
                "historical_frozen_sources_contracts_receipts": "immutable", "joern_inner_floor_bytes": 125*1024**3,
                "original_clock_origin": ORIGIN, "outer_launch_floor_bytes": 110*1024**3,
                "per_source_projection_max_bytes": PER_SOURCE_PROJECTION_BYTES, "protected_reserve_bytes": 40*1024**3,
                "registered_individual_attempt_timeouts": "unchanged", "retention_ceiling_bytes": 24*1024**3,
                "scheduling_floor_bytes": 127*1024**3, "scratch_ceiling_bytes": 24*1024**3,
                "stop_free_bytes": 48*1024**3, "user_execution_expiry": None},
            "aggregate authority changes another guard or cap")
    return value


def validate_execution_window(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    require(core.get("cutoff_utc") is None and core.get("total_wall_budget_seconds") is None and
            core.get("original_origin_utc") == ORIGIN, "no-expiry core changes original origin or retains an expiry")
    require(core.get("execution_window_authority") == WINDOW_AUTHORITY, "no-expiry core lacks exact human authority")
    auth = _json(_bound(root, WINDOW_AUTHORITY, "no-expiry authority"), "no-expiry authority")
    window = auth.get("execution_window", {})
    require(auth.get("status") == "human-authorized" and window.get("mode") == "no-user-imposed-expiry" and
            window.get("cutoff_utc") is None and window.get("total_wall_budget_seconds") is None and
            window.get("expiry_and_reserve_window_admission_removed") is True and
            window.get("original_origin_utc") == ORIGIN.replace("+00:00", "Z") and
            window.get("historical_total_wall_budget_seconds") == HISTORICAL_TOTAL_WALL_SECONDS,
            "no-expiry authority semantics differ")
    return auth


SOURCE_DESIGN_04 = {"path": "reports/releases/v0.9.2/qualification/independent-pending-groups-01/bifrost-source-design-04.json",
                    "sha256": "97de7a841b371deae7d52f41188d13f2df7011eb48ed113ad182257145f8baaf"}


SOURCE_DESIGN_06 = {
    "path": "reports/releases/v0.9.2/qualification/independent-pending-groups-01/bifrost-source-design-06.json",
    "sha256": "fe6208f98fbdc626dbc67056300b0d3c477581c60169d5a637b14902c0ff4dbc",
}
SOURCE_DESIGN_10_PATH = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/bifrost-source-design-10.json"


def validate_source_design(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    ref = _ref(core.get("source_design"), "actual post-CodeQL source design10")
    require(ref["path"] == SOURCE_DESIGN_10_PATH, "source design must be actual reviewed successor10")
    design = _json(_bound(root, ref, "actual source design10"), "source design10")
    previous = _json(_bound(root, SOURCE_DESIGN_06, "corrected source design06"), "source design06")
    require(design.get("schema") == "v092-bifrost-source-post-codeql-rebase/v1" and
            design.get("predecessor_design") == SOURCE_DESIGN_06 and
            design.get("scheduling_authority") == BREADTH_FIRST_AUTHORITY and
            design.get("reviewed_baseline_head") == previous["reviewed_baseline_head"],
            "source10 predecessor/authority/baseline differs")
    for key in ("historical_outputs_immutable", "historical_evidence_strategy",
                "actual_historical_bifrost_contexts", "actual_historical_bifrost_rows",
                "allowed_source_delta", "unchanged_source_patch", "incoming_codeql"):
        require(design.get(key) == previous.get(key), f"source10 changes immutable source06 {key}")
    incoming = design.get("incoming_codeql")
    continuation = core.get("continuation", {})
    require(isinstance(incoming, dict) and set(incoming) == {"source_commit", "plan_commit", "contract"} and
            all(incoming.get(key) == continuation.get(key) for key in incoming),
            "source10 does not bind actual incoming CodeQL source/plan/contract")
    _commit(design.get("immediate_patch_base"), "source10 immediate patch base")
    require(isinstance(design.get("reviewed_intervening_changes"), list),
            "source10 reviewed intervening closure is absent")
    return design


# A JSON object is unordered: return the complete module roster in bridge order.
RUNTIME_GRAPH_NAMES = (
    "bridge10", "replacement15", "executor", "checker", "configuration",
    "incoming_recovery", "policy_source", "policy_runtime", "protocol15",
    "admission15", "supervisor15",
)
RUNTIME_FROZEN_REFS = {
    "executor": {"path":"scripts/execute-release-v092.py", "sha256":"fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8"},
    "checker": {"path":"scripts/check-release-v092.py", "sha256":"0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928"},
    "configuration": {"path":"scripts/validate-v092-report-configurations.py", "sha256":"21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858"},
}


def _stable_runtime_source(root: Path, ref: dict[str, str], name: str) -> bytes:
    """Bind a graph source without importing it or relying on mutable bytes."""
    path = Path(root).joinpath(*_relative(ref["path"]).parts)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f"runtime graph {name} is not a regular source")
    raw = _bound(root, ref, f"runtime graph {name}")
    after = path.lstat()
    signature = lambda value: (value.st_dev, value.st_ino, value.st_size,
                               value.st_mtime_ns, value.st_ctime_ns)
    require(signature(before) == signature(after), f"runtime graph {name} changed during read")
    current = Path(root)
    for part in _relative(ref["path"]).parts:
        current /= part
        require(not current.is_symlink(), f"runtime graph {name} changed to a symlink")
    return raw


def _validate_snapshot_scripts(root: Path, source_commit: str,
                               refs: Mapping[str, dict[str, str]]) -> None:
    """Scripts are frozen snapshot members, not new C4 source-input entries.

    The immutable executor's literal roster establishes snapshot coverage.
    Exact committed regular Git blobs and stable current bytes establish each
    script's source identity. No source snapshot or frozen replay is invoked.
    """
    _commit(source_commit, "runtime script source commit")
    executor_raw = _stable_runtime_source(root, dict(RUNTIME_FROZEN_REFS["executor"]), "executor")
    assignments = [node for node in ast.parse(executor_raw).body
                   if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == "SNAPSHOT_DIRECTORIES"
                       for target in node.targets)]
    require(len(assignments) == 1, "frozen source snapshot roster is ambiguous")
    directories = ast.literal_eval(assignments[0].value)
    require(isinstance(directories, tuple) and "scripts" in directories,
            "frozen source snapshot does not cover scripts")
    paths = sorted({ref["path"] for ref in refs.values() if ref["path"].startswith("scripts/")})
    environment = {key:value for key,value in os.environ.items() if not key.startswith("GIT_")}
    def query(*argv: str) -> bytes:
        try:
            return subprocess.check_output(["git", "--literal-pathspecs", *argv], cwd=root,
                                           env=environment, stderr=subprocess.PIPE, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:
            raise Replacement15Error("cannot verify committed runtime script closure") from exc
    tree = query("ls-tree", "-r", "-z", "--full-tree", source_commit, "--", *paths)
    objects = {}
    for line in tree.split(b"\0"):
        if not line:
            continue
        header, relative = line.split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split(" ")
        path = relative.decode("utf-8")
        require(path in paths and path not in objects and kind == "blob" and
                mode in {"100644", "100755"}, "runtime script is not an exact committed regular blob")
        objects[path] = object_id
    require(set(objects) == set(paths), "runtime script is absent from committed source snapshot")
    blobs = {path:query("cat-file", "blob", object_id) for path,object_id in objects.items()}
    for name, ref in refs.items():
        if ref["path"].startswith("scripts/"):
            require(sha256(blobs[ref["path"]]) == ref["sha256"],
                    f"runtime graph {name} differs from committed source blob")
            require(_stable_runtime_source(root, ref, name) == blobs[ref["path"]],
                    f"runtime graph {name} differs from source snapshot bytes")


def validate_runtime_core(root: Path, core: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Validate static graph and raw replacement source inputs, without imports.

    Runtime manifest SHA is supplied separately after packet sealing. The core
    stores only its canonical path so no core/manifest hash cycle is possible.
    Normalized runtime input defaults remain the frozen executor's authority.
    """
    require(core.get("manifest_path") == MANIFEST_PATH,
            "runtime manifest path is not canonical replacement15")
    refs = core.get("runtime_module_graph")
    require(isinstance(refs, dict) and set(RUNTIME_GRAPH_NAMES) <= set(refs),
            "runtime module graph omits a required authority")
    require(all(isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name)
                for name in refs), "runtime module graph contains a malformed module-instance name")
    # Distinct module instances may load the same exact source. Preserve those
    # aliases; source_inputs separately enforces unique path/hash bindings.
    names = RUNTIME_GRAPH_NAMES + tuple(sorted(set(refs) - set(RUNTIME_GRAPH_NAMES)))
    resolved = {name:_ref(refs[name], f"runtime graph {name}") for name in names}
    require(all(ref["path"].endswith(".py") and
                (ref["path"].startswith("scripts/") or
                 ref["path"].startswith("reports/releases/v0.9.2/acquisition/"))
                for ref in resolved.values()), "runtime graph source is outside the reviewed Python closure")
    expected = {"bridge10":core.get("frozen_bridge_source"),
                "replacement15":core.get("implementation"), "protocol15":core.get("implementation"),
                "admission15":core.get("bifrost_admission_source"),
                "supervisor15":core.get("bifrost_supervisor_source"), **RUNTIME_FROZEN_REFS}
    for name, ref in expected.items():
        require(resolved[name] == ref, f"runtime graph {name} differs from reviewed source role")
    seal = _json(_bound(root, core["incoming_history"], "runtime incoming history"), "runtime incoming history")
    # The historical terminal provider remains separately immutable. Runtime
    # stage replay may require a reviewed adapter with a richer loader API;
    # its exact source is part of this core graph and the source contract.
    _bound(root, _ref(seal.get("recovery_module"), "historical terminal provider"),
           "historical terminal provider")
    for name in ("incoming_recovery", "policy_source", "policy_runtime"):
        require(resolved[name]["path"].startswith("reports/releases/v0.9.2/acquisition/") and
                resolved[name]["path"].endswith(".py"),
                f"runtime graph {name} is not a canonical public acquisition module")
    entries = core.get("source_inputs")
    require(isinstance(entries, list) and entries, "runtime source closure is missing")
    paths = {}
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == {"path","sha256","role"} and
                entry.get("role") == "release-input", "runtime source input is not an exact typed release input")
        ref = _ref({key:entry[key] for key in ("path","sha256")}, "runtime source input")
        require(ref["path"] not in paths, "runtime source closure repeats a path")
        paths[ref["path"]] = ref["sha256"]
    contract = _json(_bound(root, core["contract"], "runtime replacement contract"), "runtime replacement contract")
    require(entries == contract.get("source_inputs"),
            "runtime source closure differs from actual replacement contract inputs")
    _validate_snapshot_scripts(root, core.get("source_commit"), resolved)
    for name, ref in resolved.items():
        if ref["path"].startswith("scripts/"):
            continue  # Exact committed frozen snapshot coverage checked above.
        require(paths.get(ref["path"]) == ref["sha256"],
                f"runtime graph {name} is not bound by replacement source inputs")
        _stable_runtime_source(root, ref, name)
    return resolved


def _validate_core(root: Path, identity: dict[str, Any], identity_ref: dict[str, str]) -> None:
    require(set(identity) == CORE_FIELDS, "core identity has an unexpected field set")
    require(identity.get("schema") == IDENTITY_SCHEMA, "core identity schema is wrong")
    require(identity.get("original_origin_utc") == ORIGIN and identity.get("cutoff_utc") == CUTOFF and
            identity.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "core identity changes the original clock")
    validate_execution_window(root, identity)
    validate_source_design(root, identity)
    validate_working_cap(root, identity)
    validate_runtime_core(root, identity)
    _commit(identity.get("source_commit"), "core source_commit")
    _commit(identity.get("plan_commit"), "core plan_commit")
    require(identity.get("source_commit") != identity.get("plan_commit"),
            "source and plan commits must be distinct provenance values")
    for key in ("contract", "source_design", "qualification", "control_review", "implementation",
                "implementation_test", "bifrost_admission_source", "bifrost_supervisor_source",
                "runner_artifact", "frozen_bridge_source", "frozen_bridge_tests", "source_evidence"):
        _ref(identity.get(key), f"core {key}")
    _ref(identity.get("original_prefix"), "core original_prefix", rows=True)
    _ref(identity.get("continuation_prefix"), "core continuation_prefix", rows=True)
    require(identity["frozen_bridge_source"]["path"] == BRIDGE_SOURCE_PATH and
            identity["frozen_bridge_tests"]["path"] == BRIDGE_TEST_PATH,
            "frozen bridge source roles are not canonical")
    _bound(root, identity["frozen_bridge_source"], "frozen bridge source")
    _bound(root, identity["frozen_bridge_tests"], "frozen bridge tests")
    _validate_historical_prefixes(root, identity)
    _ref_or_object(root, identity.get("runner"), "core runner")
    _ref_or_object(root, identity.get("binary"), "core binary")
    continuation = identity.get("continuation")
    require(isinstance(continuation, dict) and set(continuation) == {
        "schema", "contract", "source_commit", "plan_commit", "source_inputs"} and
        continuation.get("schema") == "v092-bifrost-v0140-continuation-context/v1",
        "core continuation context is not the exact typed context")
    _ref(continuation["contract"], "continuation contract")
    _commit(continuation["source_commit"], "continuation source")
    _commit(continuation["plan_commit"], "continuation plan")
    require(isinstance(continuation["source_inputs"], list) and continuation["source_inputs"],
            "continuation source closure is missing")
    contexts = identity.get("source_contexts")
    require(isinstance(contexts, dict) and contexts, "source contexts are missing")
    for digest, context in contexts.items():
        _sha(digest, "source context key")
        require(isinstance(context, dict) and set(context) == {
            "contract", "source_commit", "plan_commit", "role"} and
            context.get("role") in {"base", "historical", "continuation", "replacement"},
            "source context is not an exact typed binding")
        _ref(context["contract"], "source context contract")
        require(context["contract"]["sha256"] == digest, "source context contract key differs")
        _commit(context["source_commit"], "source context source")
        _commit(context["plan_commit"], "source context plan")
    _bound(root, identity["source_evidence"], "source change evidence")
    _namespace_path(identity["sidecar_namespace"], identity["configuration_output"],
                    "configuration output")
    require(isinstance(identity.get("runner_environment"), dict) and
            isinstance(identity.get("executor_environment"), dict),
            "core environments are not objects")
    groups = identity.get("replacement_groups")
    require(isinstance(groups, list) and groups and len(groups) == len(set(groups)),
            "core replacement_groups must be a non-empty ordered list")
    for group in groups:
        _attempt_id(group)
    require(identity.get("resource_policy") == RESOURCE_POLICY,
            "core resource policy lowers or changes a reviewed floor")
    require(identity.get("lock_path") == CANONICAL_LOCK_PATH,
            "core lock differs from the frozen shared analyzer lock")
    _relative(identity.get("sidecar_namespace"), "core sidecar_namespace")
    require(identity["sidecar_namespace"].rstrip("/") not in {"", "."},
            "core sidecar namespace is empty")
    helper = identity["bifrost_admission_source"]
    supervisor = identity["bifrost_supervisor_source"]
    require(helper["path"] == ADMISSION_SOURCE_PATH and supervisor["path"] == SUPERVISOR_SOURCE_PATH,
            "Bifrost source roles are not canonical replacement-15 paths")
    for name, source in (("admission helper", helper), ("supervisor", supervisor)):
        require("joern-capability-" not in source["path"] and "matrix-supervision-" not in source["path"],
                f"{name} uses a historical Joern/matrix source")
        # A control may legitimately name immutable historical evidence,
        # including the human preparation hold it must supersede.  Its role
        # is established by the exact canonical path and reviewed source
        # digest, not by screening arbitrary strings in its implementation.
        _bound(root, source, name)
    _same_ref(identity["bifrost_admission_source"],
              {"path": ADMISSION_SOURCE_PATH, "sha256": helper["sha256"]},
              "canonical admission source")
    _same_ref(identity["bifrost_supervisor_source"],
              {"path": SUPERVISOR_SOURCE_PATH, "sha256": supervisor["sha256"]},
              "canonical supervisor source")
    policy = identity.get("review_policy")
    require(isinstance(policy, dict) and set(policy) == {"schema", "review_types", "reviewed_sources"},
            "core review policy has an unexpected field set")
    require(policy["schema"] == "v092-bifrost-v0140-review-policy/v1" and
            policy["review_types"] == REVIEW_TYPES and
            isinstance(policy["reviewed_sources"], dict) and
            set(policy["reviewed_sources"]) == set(SOURCE_NAMES),
            "core review policy is incomplete")
    expected_sources = {
        "implementation": identity["implementation"],
        "focused_tests": identity["implementation_test"],
        "helper": helper,
        "supervisor": supervisor,
        "bridge": identity["frozen_bridge_source"],
        "bridge_tests": identity["frozen_bridge_tests"],
    }
    for name in SOURCE_NAMES:
        _same_ref(policy["reviewed_sources"][name], expected_sources[name],
                  f"review policy {name}")
    _forbidden_root_core(identity)
    # The identity ref itself is checked by the caller; this assertion guards
    # against accidentally passing a runtime receipt as the core artifact.
    _same_ref(identity_ref, {"path": IDENTITY_PATH, "sha256": identity_ref["sha256"]},
              "core identity canonical path")


BREADTH_FIRST_AUTHORITY = {"path": 'reports/releases/v0.9.2/qualification/independent-pending-groups-01/authorization-01.json', "sha256": '0f8413d52c348a9d89079c70d8cebdea3179c35a8b84a98d390c53227e6f5478'}
INCOMING_HISTORY_SCHEMA = "v092-bifrost-v0140-incoming-history/v1"
SAFETY_FIELDS = {"schema", "status", "group_id", "attempt_id", "receipt_sha256",
                 "checked_utc", "owned_processes_gone", "resources_valid",
                 "tracked_processes"}


def validate_breadth_first_authority(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    _same_ref(core.get("breadth_first_authority"), BREADTH_FIRST_AUTHORITY,
              "breadth-first human authority")
    value = _json(_bound(root, BREADTH_FIRST_AUTHORITY, "breadth-first authority"), "breadth-first authority")
    require(value.get("schema") == "v092-breadth-first-reviewed-scheduling-authorization/v1" and
            value.get("schedule_amendment_authorized") is True and
            value.get("fabricated_original84_success_forbidden") is True and
            value.get("history_and_attempt_counters_preserved") is True and
            value.get("one_analyzer_slot") is True and
            value.get("no_user_execution_window_expiry") is True and
            value.get("aggregate_source_working_gib") == 30 and
            value.get("per_source_snapshot_gib") == 12 and
            value.get("other_guards_timeouts_reserves_unchanged") is True,
            "breadth-first authority semantics changed")
    return value


def _terminal_identity(value: dict[str, Any], *, group_id: str, attempt_id: str,
                       source_commit: str, plan_commit: str, contract_sha256: str,
                       execution_series: int, label: str) -> None:
    """Accept a truthful terminal row, never a capacity/integrity/recorder error."""
    _commit(source_commit, f"{label} source")
    _commit(plan_commit, f"{label} plan")
    _sha(contract_sha256, f"{label} contract")
    status = value.get("status")
    code = value.get("exit_code")
    require(status in {"completed", "failed", "timed-out"} and type(code) is int and
            ((status == "completed" and code == 0 and value.get("timed_out") is False) or
             (status == "failed" and code != 0 and value.get("timed_out") is False) or
             (status == "timed-out" and code == 124 and value.get("timed_out") is True)) and
            value.get("capacity_loss") is None and not value.get("disk_guard_error") and
            not value.get("recorder_error") and value.get("tool") == "bifrost" and
            value.get("group_id") == group_id and value.get("attempt_id") == attempt_id and
            value.get("source_commit") == source_commit and value.get("plan_commit") == plan_commit and
            value.get("contract_sha256") == contract_sha256 and
            value.get("execution_series") == execution_series,
            f"{label} is not a contained ordinary terminal attempt")
    ownership = value.get("process_ownership")
    require(isinstance(ownership, dict) and
            ownership.get("cleanup_status") == "tracked-processes-stopped" and
            not ownership.get("cleanup_error") and not ownership.get("tracking_error") and
            type(ownership.get("root_pid")) is int and ownership["root_pid"] > 0 and
            isinstance(ownership.get("tracked_processes"), list) and ownership["tracked_processes"],
            f"{label} has no complete exact-birth process containment")
    tracked = ownership["tracked_processes"]
    require(ownership.get("schema") == "invocation-process-ownership/v1" and
            ownership.get("descendant_containment") == "unproven" and
            ownership.get("tracking_interval_seconds") == 2.0 and
            all(isinstance(item, dict) and set(item) == {"pid", "start_identity"} and
                type(item["pid"]) is int and item["pid"] > 0 and
                isinstance(item["start_identity"], str) and item["start_identity"] for item in tracked) and
            len({item["pid"] for item in tracked}) == len(tracked) and
            ownership["root_pid"] in {item["pid"] for item in tracked},
            f"{label} exact tracked process roster is incomplete or relabeled")


def validate_continuation_safety(value: object, row: Mapping[str, Any], receipt_sha: str) -> None:
    require(isinstance(value, dict) and set(value) == SAFETY_FIELDS and
            value.get("schema") == "v092-bifrost-v0140-terminal-continuation-safety/v1" and
            value.get("status") == "tracked-cleanup-and-resource-checked" and
            value.get("group_id") == row.get("group_id") and
            value.get("attempt_id") == row.get("attempt_id") and
            value.get("receipt_sha256") == receipt_sha and
            value.get("owned_processes_gone") is True and value.get("resources_valid") is True and
            value.get("tracked_processes") == row.get("process_ownership", {}).get("tracked_processes"),
            "terminal continuation safety proof differs from actual receipt")
    import datetime as dt
    try:
        checked = dt.datetime.fromisoformat(value["checked_utc"].replace("Z", "+00:00"))
        ended = dt.datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00"))
        require(checked.tzinfo is not None and ended.tzinfo is not None and checked >= ended,
                "continuation safety predates terminal evidence")
    except (KeyError, TypeError, ValueError) as exc:
        raise Replacement15Error("invalid continuation safety timestamp") from exc


def _validate_historical_prefixes(root: Path, core: Mapping[str, Any]) -> None:
    validate_breadth_first_authority(root, core)
    original = _bound(root, core["original_prefix"], "original historical prefix", rows=True)
    incoming = _bound(root, core["continuation_prefix"], "actual incoming prefix", rows=True)
    require(core["original_prefix"]["rows"] == 88 and
            core["original_prefix"]["sha256"] == ORIGINAL_PREFIX_SHA256 and
            sha256(original) == ORIGINAL_PREFIX_SHA256 and len(_jsonl(original, "original prefix")) == 88,
            "original historical88 prefix differs")
    require(sha256(b"".join(original.splitlines(keepends=True)[:87])) == PREDECESSOR87_SHA256,
            "original first87 predecessor changed")
    original_rows = _jsonl(original, "original prefix")
    require(original_rows[-1].get("attempt_id") == "joern-swift-common108-attempt-04-series-01" and
            original_rows[-1].get("status") == "failed", "consumed Joern04 was relabelled")
    seal = _json(_bound(root, core["incoming_history"], "incoming history seal"), "incoming history seal")
    require(set(seal) == {"schema", "authority", "ledger_prefix", "codeql_terminal_receipt",
                          "recovery_module", "recovery_manifest"} and
            seal.get("schema") == INCOMING_HISTORY_SCHEMA and
            seal.get("authority") == BREADTH_FIRST_AUTHORITY and
            seal.get("ledger_prefix") == core["continuation_prefix"],
            "incoming history seal identity differs")
    for key in ("codeql_terminal_receipt", "recovery_module", "recovery_manifest"):
        _bound(root, seal[key], f"incoming {key}")
    rows = _jsonl(incoming, "incoming prefix")
    require(incoming.startswith(original) and len(rows) == len(original_rows) + 1 and
            core["continuation_prefix"]["rows"] == len(rows),
            "incoming seal must contain actual historical88 plus the one CodeQL terminal outcome")
    ids = [row.get("attempt_id") for row in rows]
    require(all(isinstance(x, str) and x for x in ids) and len(ids) == len(set(ids)),
            "incoming history contains duplicate or missing attempt identities")
    row = rows[-1]
    receipt_path = "reports/releases/v0.9.2/attempts/codeql-swift-common108-attempt-01-series-01/completed.json"
    require(seal["codeql_terminal_receipt"]["path"] == receipt_path and
            row.get("group_id") == "codeql-swift-common108" and
            row.get("attempt_id") == "codeql-swift-common108-attempt-01-series-01" and
            row.get("execution_series") == 1 and row.get("tool") == "codeql" and
            row.get("status") in {"completed", "failed", "timed-out", "recorder-error", "capacity-lost"},
            "incoming history lacks the truthful CodeQL01 terminal outcome")
    receipt = _json(_bound(root, seal["codeql_terminal_receipt"], "actual CodeQL terminal receipt"),
                    "actual CodeQL terminal receipt")
    require(receipt == row, "incoming CodeQL receipt and actual ledger row differ")
    continuation = core["continuation"]
    require(row.get("contract_sha256") == continuation["contract"]["sha256"] and
            row.get("source_commit") == continuation["source_commit"] and
            row.get("plan_commit") == continuation["plan_commit"],
            "CodeQL terminal outcome changed its exact normalized origin")
    live = _read(root, LEDGER_PATH)
    require(live.startswith(incoming), "incoming seal is not actual canonical ledger history")


def _load_manifest(root: Path, manifest_path: str) -> tuple[dict[str, Any], dict[str, str], dict[str, Any], bytes]:
    require(manifest_path == MANIFEST_PATH, "final manifest path is not the registered replacement-15 path")
    raw = _read(root, manifest_path)
    manifest_ref = {"path": manifest_path, "sha256": sha256(raw)}
    manifest = _json(raw, "final manifest")
    require(set(manifest) == MANIFEST_FIELDS, "final manifest has an unexpected field set")
    require(manifest.get("schema") == MANIFEST_SCHEMA and manifest.get("finalized") is True,
            "final manifest is not finalized replacement-15")
    _ref(manifest.get("core_identity"), "manifest core_identity")
    require(manifest["core_identity"]["path"] == IDENTITY_PATH,
            "manifest core identity path is not canonical")
    core_raw = _bound(root, manifest["core_identity"], "manifest core identity")
    core = _json(core_raw, "core identity")
    _validate_core(root, core, manifest["core_identity"])
    require(sha256(core_raw) == manifest["core_identity"]["sha256"], "core identity digest changed")
    for name in ("bifrost_admission_source", "bifrost_supervisor_source"):
        _same_ref(manifest.get(name), core[name], f"manifest {name}")
    for name, review_type in (("independent_review", REVIEW_TYPES[0]), ("final_review", REVIEW_TYPES[1])):
        review_ref = _ref(manifest.get(name), f"manifest {name}")
        review = _json_ref(root, review_ref, f"{name} review")
        require(review.get("status") == "approved" and review.get("automatic_retry") is False and
                review.get("review_type") == review_type,
                f"{name} is not an approved one-shot review")
        _same_ref(review.get("core_identity"), manifest["core_identity"], f"{name} core identity")
        require(review.get("reviewed_sources") == core["review_policy"]["reviewed_sources"],
                f"{name} source bindings differ from the core review policy")
    slots = manifest.get("execution_admission_slots")
    groups = core["replacement_groups"]
    # JSON object order is not the execution sequence (canonical encoding
    # sorts keys).  The reviewed replacement_groups array owns that sequence.
    require(isinstance(slots, dict) and set(slots) == set(groups),
            "execution admission slot keys differ from replacement_groups")
    attempts: set[str] = set()
    paths: set[str] = set()
    for group in groups:
        slot = slots[group]
        require(isinstance(slot, dict) and set(slot) == SLOT_FIELDS,
                f"slot for {group} has an unexpected field set")
        require(slot["group_id"] == group and slot["attempt_id"] == _attempt_id(group),
                f"slot identity differs for {group}")
        require(slot["attempt_id"] not in attempts, "duplicate replacement attempt identity")
        attempts.add(slot["attempt_id"])
        for key in ("admission_path", "completion_path", "phase_gate_path", "predecessor_receipt_path"):
            _namespace_path(core["sidecar_namespace"], slot[key], f"slot {group} {key}")
            require(slot[key] not in paths, f"duplicate sidecar slot path: {slot[key]}")
            paths.add(slot[key])
        require(isinstance(slot["predecessor_attempt_id"], str) and slot["predecessor_attempt_id"],
                f"slot {group} predecessor attempt is missing")
    config_slot = manifest.get("configuration_admission_slot")
    require(isinstance(config_slot, dict) and set(config_slot) == {"admission_path", "receipt_path"},
            "configuration admission slot has an unexpected field set")
    config_paths: set[str] = set()
    for key in config_slot:
        _namespace_path(core["sidecar_namespace"], config_slot[key], f"configuration slot {key}")
        require(config_slot[key] not in paths and config_slot[key] not in config_paths,
                f"configuration slot collides with another sidecar slot: {config_slot[key]}")
        config_paths.add(config_slot[key])
    return manifest, manifest_ref, core, raw


def validate_static(root: Path | str, manifest_path: str = MANIFEST_PATH) -> dict[str, Any]:
    """Validate only immutable identity, reviews, source bindings and slots."""
    active = _PROTOCOL_STAGE.get()
    if active is not None:
        require(Path(root).resolve() == active["root"], "stage protocol root differs")
        active["bridge"].assert_stage_current(active["root"], active["stage"], active["graph"])
        static = active["runtime"]["protocol_static"]
        require(static.get("manifest_ref", {}).get("path") == manifest_path,
                "stage protocol manifest path differs")
        return static
    root = Path(root)
    manifest, manifest_ref, core, _ = _load_manifest(root, manifest_path)
    return {"status": "preparation-hold", "manifest": manifest, "manifest_ref": manifest_ref,
            "core": core, "groups": list(core["replacement_groups"])}


def _context(root: Path | str, manifest_path: str = MANIFEST_PATH) -> tuple[Path, dict[str, Any], dict[str, str], dict[str, Any]]:
    static = validate_static(root, manifest_path)
    return Path(root), static["manifest"], static["manifest_ref"], static["core"]


def _load_value(root: Path, value: object, label: str) -> tuple[dict[str, Any], dict[str, str]]:
    ref = _ref(value, label)
    return _json(_bound(root, ref, label), label), ref


def _base_runtime(root: Path, manifest: dict[str, Any], manifest_ref: dict[str, str], core: dict[str, Any],
                  value: dict[str, Any], label: str, fields: set[str], schema: str) -> dict[str, Any]:
    require(set(value) == fields, f"{label} has an unexpected field set")
    require(value.get("schema") == schema, f"{label} schema is wrong")
    require(value.get("automatic_retry") is False, f"{label} permits automatic retry")
    _same_ref(value.get("core_identity"), manifest["core_identity"], f"{label} core identity")
    require(value.get("manifest_path") == manifest_ref["path"], f"{label} manifest path differs")
    _same_ref(value.get("admission_source", value.get("helper")), core["bifrost_admission_source"],
              f"{label} helper source")
    _same_ref(value.get("supervisor_source", value.get("supervisor")), core["bifrost_supervisor_source"],
              f"{label} supervisor source")
    return value


def validate_parent_admission(root: Path | str, manifest_path: str, admission: object) -> dict[str, Any]:
    """Validate the batch parent receipt; it must carry no group identity."""
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    if isinstance(admission, (str, Path)):
        value, ref = _load_value(root, {"path": str(admission), "sha256": sha256(_read(root, str(admission)))},
                                 "parent admission")
    else:
        require(isinstance(admission, dict), "parent admission must be an object or path")
        value, ref = admission, None
    require(set(value) == {
        "schema", "status", "automatic_retry", "core_identity", "manifest_path", "manifest_sha256",
        "helper", "supervisor", "supervisor_permit", "process_ownership", "lock", "fresh_namespace",
        "resource_policy", "resource_policy_sha256", "remaining_reserved_seconds",
    }, "parent admission has an unexpected field set")
    require(value.get("schema") == PARENT_ADMISSION_SCHEMA and value.get("status") == "ready" and
            value.get("automatic_retry") is False, "parent admission is not ready")
    _same_ref(value.get("core_identity"), manifest["core_identity"], "parent core identity")
    require(value.get("manifest_path") == manifest_ref["path"] and
            value.get("manifest_sha256") == manifest_ref["sha256"],
            "parent admission is not bound to the finalized wrapper")
    _same_ref(value.get("helper"), core["bifrost_admission_source"], "parent helper")
    _same_ref(value.get("supervisor"), core["bifrost_supervisor_source"], "parent supervisor")
    _permit(value.get("supervisor_permit"), identity=manifest["core_identity"],
            manifest_path=manifest_ref["path"], helper=core["bifrost_admission_source"],
            supervisor=core["bifrost_supervisor_source"], scope="parent")
    _typed_process(value.get("process_ownership"))
    _typed_lock(value.get("lock"), core["lock_path"])
    _typed_namespace(value.get("fresh_namespace"), core["sidecar_namespace"])
    require(value.get("resource_policy") == RESOURCE_POLICY and
            value.get("resource_policy_sha256") == _policy_sha(RESOURCE_POLICY),
            "parent admission resource policy differs")
    require(value.get("remaining_reserved_seconds") is None,
            "parent admission has insufficient remaining reserve")
    for key in ("group_id", "attempt_id", "phase", "completion", "dispatch"):
        require(key not in value, f"parent admission carries group/runtime field {key}")
    return {"value": value, "ref": ref, "manifest_ref": manifest_ref}


def validate_group_admission(root: Path | str, manifest_path: str, group_id: str,
                             admission: object) -> dict[str, Any]:
    """Validate one v3 group receipt selected by the reviewed slot map."""
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    require(group_id in core["replacement_groups"], "group is outside the reviewed replacement order")
    slot = manifest["execution_admission_slots"][group_id]
    if isinstance(admission, (str, Path)):
        path = str(admission)
        raw = _read(root, path)
        admission = _json(raw, "group admission")
        admission_ref = {"path": path, "sha256": sha256(raw)}
    else:
        require(isinstance(admission, dict), "group admission must be an object or path")
        admission_ref = None
    value = _base_runtime(root, manifest, manifest_ref, core, admission, "group admission",
                          GROUP_ADMISSION_FIELDS, GROUP_ADMISSION_SCHEMA)
    require(value.get("status") == "ready-to-execute" and value.get("phase") == "execution" and
            value.get("group_id") == group_id and value.get("attempt_id") == slot["attempt_id"],
            "group admission identity or phase differs")
    require("manifest_sha256" not in value, "group admission recreates the manifest hash cycle")
    require(value.get("source_commit") == core["source_commit"] and
            value.get("plan_commit") == core["plan_commit"] and
            value.get("contract_sha256") == core["contract"]["sha256"],
            "group admission source/plan/contract differs")
    _ref(value.get("ledger_prefix"), "group admission ledger_prefix", rows=True)
    _same_ref(value.get("ledger_prefix"), core["continuation_prefix"],
              "group admission ledger prefix")
    _sha(value.get("superseded_receipt_sha256"), "group superseded receipt SHA")
    _sha(value.get("ledger_before_sha256"), "group ledger-before SHA")
    require(value.get("superseded_attempt_id") == slot["predecessor_attempt_id"],
            "group predecessor attempt differs")
    predecessor = _validate_predecessor(root, core, slot, group_id)
    require(sha256(predecessor["receipt_raw"]) == value["superseded_receipt_sha256"],
            "group predecessor receipt bytes differ")
    _validate_ledger_before(root, manifest, core, slot, value, group_id=group_id)
    _same_ref(value.get("admission_source"), core["bifrost_admission_source"], "group admission source")
    _same_ref(value.get("supervisor_source"), core["bifrost_supervisor_source"], "group supervisor source")
    _same_ref(value.get("helper"), core["bifrost_admission_source"], "group helper")
    _permit(value.get("supervisor_permit"), identity=manifest["core_identity"],
            manifest_path=manifest_ref["path"], helper=core["bifrost_admission_source"],
            supervisor=core["bifrost_supervisor_source"], scope="group", group=group_id,
            attempt=slot["attempt_id"])
    _typed_process(value.get("process_ownership"))
    _typed_lock(value.get("lock"), core["lock_path"])
    _typed_namespace(value.get("fresh_namespace"), core["sidecar_namespace"])
    require(value.get("resource_policy") == RESOURCE_POLICY and
            value.get("resource_policy_sha256") == _policy_sha(RESOURCE_POLICY),
            "group resource policy differs")
    require(value.get("remaining_reserved_seconds") is None,
            "group admission has insufficient remaining reserve")
    return {"value": value, "ref": admission_ref, "slot": slot}


def validate_phase_gate(root: Path | str, manifest_path: str, group_id: str,
                        phase_gate: object, admission_ref: dict[str, str]) -> dict[str, Any]:
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    require(group_id in core["replacement_groups"], "phase gate group is outside replacement order")
    slot = manifest["execution_admission_slots"][group_id]
    if isinstance(phase_gate, (str, Path)):
        path = str(phase_gate)
        raw = _read(root, path)
        value = _json(raw, "phase gate")
        phase_ref = {"path": path, "sha256": sha256(raw)}
    else:
        require(isinstance(phase_gate, dict), "phase gate must be an object or path")
        value, phase_ref = phase_gate, None
    require(set(value) == PHASE_FIELDS, "phase gate has an unexpected field set")
    require(value.get("schema") == PHASE_GATE_SCHEMA and value.get("phase") == "execution",
            "phase gate schema or phase is wrong")
    _same_ref(value.get("core_identity"), manifest["core_identity"], "phase core identity")
    require(value.get("manifest_path") == manifest_ref["path"] and
            value.get("manifest_sha256") == manifest_ref["sha256"],
            "phase gate is not bound to the finalized wrapper")
    _same_ref(value.get("admission_ref"), admission_ref, "phase admission ref")
    require(value.get("group_id") == group_id and value.get("attempt_id") == slot["attempt_id"],
            "phase gate group or attempt differs")
    require(value.get("source_commit") == core["source_commit"] and
            value.get("plan_commit") == core["plan_commit"] and
            value.get("contract_sha256") == core["contract"]["sha256"],
            "phase source/plan/contract differs")
    for key, expected in (("minimum_remaining_reserve_seconds", RESOURCE_POLICY["minimum_remaining_reserve_seconds"]),
                          ("minimum_replacement_seconds", RESOURCE_POLICY["minimum_replacement_seconds"]),
                          ("startup_seconds", RESOURCE_POLICY["startup_seconds"]),
                          ("minimum_free_gib", RESOURCE_POLICY["minimum_free_gib"])):
        require(value.get(key) == expected, f"phase gate {key} differs")
    require(value.get("remaining_seconds") is None and
            type(value.get("observed_free_bytes")) is int and value["observed_free_bytes"] >= 127 * 1024**3,
            "phase gate resource witness is below the reviewed floor")
    require(value.get("resource_floor_checked") is True and value.get("no_foreign_processes") is True and
            value.get("exclusive_lock_checked") is True and value.get("lock_held") is True and
            value.get("fresh_sidecar_namespace") is True and value.get("source_snapshot_checked") is True,
            "phase gate lacks complete live-state checks")
    _same_ref(value.get("helper"), core["bifrost_admission_source"], "phase helper")
    _same_ref(value.get("supervisor"), core["bifrost_supervisor_source"], "phase supervisor")
    _permit(value.get("supervisor_permit"), identity=manifest["core_identity"],
            manifest_path=manifest_ref["path"], helper=core["bifrost_admission_source"],
            supervisor=core["bifrost_supervisor_source"], scope="group", group=group_id,
            attempt=slot["attempt_id"])
    return {"value": value, "ref": phase_ref}


def validate_completion(root: Path | str, manifest_path: str, group_id: str,
                        completion: object, admission_ref: dict[str, str],
                        phase_ref: dict[str, str]) -> dict[str, Any]:
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    require(group_id in core["replacement_groups"], "completion group is outside replacement order")
    slot = manifest["execution_admission_slots"][group_id]
    if isinstance(completion, (str, Path)):
        path = str(completion)
        raw = _read(root, path)
        value = _json(raw, "completion")
        completion_ref = {"path": path, "sha256": sha256(raw)}
    else:
        require(isinstance(completion, dict), "completion must be an object or path")
        value, completion_ref = completion, None
    require(set(value) == COMPLETION_FIELDS, "completion has an unexpected field set")
    require(value.get("schema") == COMPLETION_SCHEMA and value.get("status") in {"completed", "failed", "timed-out"} and
            value.get("automatic_retry") is False, "completion is not a one-shot terminal result")
    _same_ref(value.get("core_identity"), manifest["core_identity"], "completion core identity")
    require(value.get("manifest_path") == manifest_ref["path"] and
            value.get("manifest_sha256") == manifest_ref["sha256"],
            "completion is not bound to the finalized wrapper")
    require(value.get("group_id") == group_id and value.get("attempt_id") == slot["attempt_id"],
            "completion group or attempt differs")
    _same_ref(value.get("admission_ref"), admission_ref, "completion admission ref")
    _same_ref(value.get("phase_gate_ref"), phase_ref, "completion phase ref")
    _sha(value.get("admission_sha256"), "completion admission SHA")
    _sha(value.get("phase_gate_sha256"), "completion phase SHA")
    require(value["admission_sha256"] == admission_ref["sha256"],
            "completion admission digest differs")
    require(value["phase_gate_sha256"] == phase_ref["sha256"],
            "completion phase digest differs")
    _sha(value.get("completed_receipt_sha256"), "completed receipt SHA")
    _sha(value.get("ledger_before_sha256"), "completion ledger-before SHA")
    _sha(value.get("ledger_after_sha256"), "completion ledger-after SHA")
    completed_path = f"reports/releases/v0.9.2/attempts/{slot['attempt_id']}/completed.json"
    completed_raw = _read(root, completed_path)
    completed = _json(completed_raw, "completed attempt receipt")
    _terminal_identity(completed, group_id=group_id, attempt_id=slot["attempt_id"],
                         source_commit=core["source_commit"], plan_commit=core["plan_commit"],
                         contract_sha256=core["contract"]["sha256"], execution_series=2,
                         label="completed receipt")
    require(value["status"] == completed["status"], "completion status relabels terminal receipt")
    validate_continuation_safety(value["continuation_safety"], completed, sha256(completed_raw))
    require(sha256(completed_raw) == value["completed_receipt_sha256"],
            "completed receipt digest does not match immutable bytes")
    _, after_raw, appended = _validate_ledger_transition(
        root, slot, value, group_id=group_id, source_commit=core["source_commit"],
        plan_commit=core["plan_commit"], contract_sha256=core["contract"]["sha256"])
    require(appended == completed, "terminal ledger row differs from full frozen receipt")
    require(sha256(after_raw) == value["ledger_after_sha256"],
            "ledger-after digest does not match immutable bytes")
    return {"value": value, "ref": completion_ref, "completed": completed}


def validate_configuration_admission(root: Path | str, manifest_path: str,
                                     admission: object, receipt: object | None = None) -> dict[str, Any]:
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    slot = manifest["configuration_admission_slot"]
    if isinstance(admission, (str, Path)):
        path = str(admission)
        raw = _read(root, path)
        value = _json(raw, "configuration admission")
        admission_ref = {"path": path, "sha256": sha256(raw)}
    else:
        require(isinstance(admission, dict), "configuration admission must be an object or path")
        value, admission_ref = admission, None
    require(set(value) == CONFIG_FIELDS, "configuration admission has an unexpected field set")
    require(value.get("schema") == CONFIG_ADMISSION_SCHEMA and value.get("status") == "ready" and
            value.get("scope") == "configuration" and value.get("automatic_retry") is False,
            "configuration admission is not ready")
    _same_ref(value.get("core_identity"), manifest["core_identity"], "configuration core identity")
    require(value.get("manifest_path") == manifest_ref["path"] and
            value.get("manifest_sha256") == manifest_ref["sha256"],
            "configuration admission is not bound to the finalized wrapper")
    _same_ref(value.get("admission_source"), core["bifrost_admission_source"], "configuration source")
    _same_ref(value.get("supervisor_source"), core["bifrost_supervisor_source"], "configuration supervisor")
    _same_ref(value.get("helper"), core["bifrost_admission_source"], "configuration helper")
    _permit(value.get("supervisor_permit"), identity=manifest["core_identity"],
            manifest_path=manifest_ref["path"], helper=core["bifrost_admission_source"],
            supervisor=core["bifrost_supervisor_source"], scope="configuration")
    _same_ref(admission_ref, {"path": slot["admission_path"], "sha256": admission_ref["sha256"]},
              "configuration admission slot")
    require(value.get("resource_policy") == RESOURCE_POLICY and
            value.get("resource_policy_sha256") == _policy_sha(RESOURCE_POLICY) and
            value.get("remaining_reserved_seconds") is None,
            "configuration resource floor is not preserved")
    if receipt is not None:
        if isinstance(receipt, (str, Path)):
            path = str(receipt)
            raw = _read(root, path)
            output = _json(raw, "configuration receipt")
            receipt_ref = {"path": path, "sha256": sha256(raw)}
        else:
            require(isinstance(receipt, dict), "configuration receipt must be an object or path")
            output, receipt_ref = receipt, None
        require(set(output) == CONFIG_RECEIPT_FIELDS and output.get("schema") == CONFIG_RECEIPT_SCHEMA and
                output.get("status") == "canonical-validation-passed" and output.get("automatic_retry") is False,
                "configuration output receipt is not a successful one-shot result")
        _same_ref(output.get("core_identity"), manifest["core_identity"], "configuration receipt identity")
        require(output.get("manifest_path") == manifest_ref["path"] and
                output.get("manifest_sha256") == manifest_ref["sha256"],
                "configuration receipt wrapper binding differs")
        _relative(output.get("output_path"), "configuration output path")
        require(output["output_path"] == core["configuration_output"],
                "configuration receipt names an unreviewed output path")
        _namespace_path(core["sidecar_namespace"], output["output_path"],
                        "configuration output path")
        output_raw = _read(root, output["output_path"])
        require(sha256(output_raw) == output["output_sha256"],
                "configuration output digest does not match immutable bytes")
        output_value = _json(output_raw, "configuration output")
        require(output_value.get("status") == "canonical-validation-passed" and
                output_value.get("partitions") == 92 and output_value.get("rows") == 4252 and
                output_value.get("known_stale") == 0 and output.get("partitions") == 92 and
                output.get("rows") == 4252 and output.get("known_stale") == 0,
                "configuration output does not prove the exact 92/4252/0 result")
        _validate_configuration_output(root, core, manifest_ref, manifest["core_identity"], output_value)
    else:
        receipt_ref = None
    return {"value": value, "ref": admission_ref, "receipt_ref": receipt_ref}


def _validate_configuration_output(root: Path, core: Mapping[str, Any],
                                   manifest_ref: Mapping[str, str], identity: Mapping[str, str],
                                   output: Mapping[str, Any]) -> None:
    """Check retained canonical stdout as well as the summary's denominators.

    These are the frozen validator's exact output lines, not analyzer-result
    interpretation. The production controller also calls the actual frozen
    parser and success predicate when it records each invocation.
    """
    require(output.get("core_identity") == identity and
            output.get("manifest_path") == manifest_ref["path"] and
            output.get("manifest_sha256") == manifest_ref["sha256"],
            "configuration summary is not bound to this exact packet")
    require(output.get("ledger_sha256") == sha256(_read(root, LEDGER_PATH)),
            "configuration summary does not bind the live final ledger")
    contexts = output.get("source_contexts")
    require(isinstance(contexts, list) and contexts, "configuration has no source-context invocations")
    selected = {}
    for row in _jsonl(_read(root, LEDGER_PATH), "configuration ledger"):
        if row.get("status") == "completed" and isinstance(row.get("group_id"), str):
            selected[row["group_id"]] = row
    require(len(selected) == 84, "configuration ledger does not select all 84 groups")
    selected_attempts = {row["attempt_id"]: row for row in selected.values()}
    contracts: set[str] = set()
    attempts: set[str] = set()
    total_partitions = total_rows = 0
    for context in contexts:
        require(isinstance(context, dict), "configuration context is malformed")
        digest = context.get("contract_sha256")
        _sha(digest, "configuration context contract")
        require(digest not in contracts, "configuration repeats a source context")
        contracts.add(digest)
        _commit(context.get("source_commit"), "configuration source commit")
        _commit(context.get("plan_commit"), "configuration plan commit")
        registered = core["source_contexts"].get(digest)
        require(isinstance(registered, dict) and
                registered["source_commit"] == context["source_commit"] and
                registered["plan_commit"] == context["plan_commit"],
                "configuration invocation has no exact registered source context")
        ids = context.get("attempt_ids")
        require(isinstance(ids, list) and ids and all(isinstance(x, str) and x for x in ids) and
                len(ids) == len(set(ids)) and not attempts.intersection(ids),
                "configuration repeats or omits attempt identities")
        attempts.update(ids)
        for attempt_id in ids:
            row = selected_attempts.get(attempt_id)
            require(isinstance(row, dict) and row.get("contract_sha256") == digest and
                    row.get("source_commit") == context["source_commit"] and
                    row.get("plan_commit") == context["plan_commit"],
                    "configuration attempt is absent, superseded, or assigned to the wrong source context")
        partitions, rows = context.get("partitions"), context.get("rows")
        require(type(partitions) is int and partitions > 0 and type(rows) is int and rows > 0,
                "configuration context denominators are malformed")
        total_partitions += partitions
        total_rows += rows
        captures = {}
        for stream in ("stdout", "stderr"):
            path = context.get(f"{stream}_path")
            _namespace_path(core["sidecar_namespace"], path, f"configuration {stream}")
            captures[stream] = _bound(root, {"path": path, "sha256": context.get(f"{stream}_sha256")},
                                      f"configuration {stream}")
        try:
            lines = captures["stdout"].decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise Replacement15Error("configuration stdout is not UTF-8") from exc
        validated = [int(match[1]) for line in lines
                     if (match := re.fullmatch(r"validated ([0-9]+) reports", line))]
        checked = [(int(match[1]), int(match[2])) for line in lines
                   if (match := re.fullmatch(
                       r"checked ([0-9]+) configuration hashes against the working tree "
                       r"\(([0-9]+) known-stale under issue #138\)", line))]
        require(len(validated) == len(checked) == 1 and validated[0] == partitions and
                0 < checked[0][0] <= partitions and checked[0][1] == 0,
                "configuration captures do not prove canonical validation")
        metrics = {"validated_reports": partitions, "checked_configuration_hashes": checked[0][0],
                   "known_stale": 0, "not_derivable": partitions - checked[0][0]}
        require(context.get("metrics") == metrics and context.get("exit_code") == 0 and
                context.get("timed_out") is False and context.get("invocation_error") is None,
                "configuration invocation result differs from retained stdout")
    require(total_partitions == 92 and total_rows == 4252,
            "configuration source contexts do not sum to 92/4252")
    require(attempts == set(selected_attempts),
            "configuration source contexts omit selected attempts")


def validate_runtime(root: Path | str, manifest_path: str = MANIFEST_PATH,
                     parent_admission: object | None = None,
                     configuration: tuple[object, object | None] | None = None) -> dict[str, Any]:
    """Validate supplied receipts without executing or creating any artifact."""
    root, manifest, manifest_ref, core = _context(root, manifest_path)
    require(parent_admission is not None, "runtime validation requires parent admission")
    require(configuration is not None and configuration[1] is not None,
            "runtime validation requires actual configuration admission and receipt")
    parent = validate_parent_admission(root, manifest_path, parent_admission)
    groups: dict[str, Any] = {}
    for group in core["replacement_groups"]:
        slot = manifest["execution_admission_slots"][group]
        admission = validate_group_admission(root, manifest_path, group, slot["admission_path"])
        require(admission["ref"] is not None, f"group {group} admission ref is missing")
        phase = validate_phase_gate(root, manifest_path, group, slot["phase_gate_path"], admission["ref"])
        require(phase["ref"] is not None, f"group {group} phase ref is missing")
        completion = validate_completion(root, manifest_path, group, slot["completion_path"],
                                         admission["ref"], phase["ref"])
        groups[group] = {"admission": admission, "phase": phase, "completion": completion}
    config = None
    if configuration is not None:
        config = validate_configuration_admission(root, manifest_path, configuration[0], configuration[1])
    final_slot = manifest["execution_admission_slots"][core["replacement_groups"][-1]]
    final_bytes = _read(root, _slot_witness_path(final_slot["completion_path"], "ledger-after.jsonl"))
    require(_read(root, LEDGER_PATH) == final_bytes,
            "live ledger differs from the complete ordered replacement witness chain")
    return {"status": "protocol-verified", "manifest_ref": manifest_ref,
            "core_identity": manifest["core_identity"], "parent": parent,
            "groups": groups, "configuration": config}


def write_immutable(root: Path | str, path: str, value: Mapping[str, Any]) -> dict[str, str]:
    """Create a JSON side artifact only if absent or byte-identical."""
    return write_immutable_bytes(root, path, canonical_json(dict(value)))


def write_immutable_bytes(root: Path | str, path: str, raw: bytes) -> dict[str, str]:
    """Publish complete retained bytes without changing an occupied path."""
    require(isinstance(raw, bytes), "immutable artifact must contain bytes")
    root = Path(root)
    relative_path = _relative(path)
    target = root / Path(*relative_path.parts)
    current = root
    for part in relative_path.parts[:-1]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                info = current.lstat()
            else:
                info = current.lstat()
        require(not stat.S_ISLNK(info.st_mode) and stat.S_ISDIR(info.st_mode),
                f"artifact parent is not a directory: {current}")
    try:
        info = target.lstat()
    except FileNotFoundError:
        info = None
    if info is not None:
        require(not stat.S_ISLNK(info.st_mode) and stat.S_ISREG(info.st_mode),
                f"immutable artifact target is not a regular file: {path}")
        # An occupied path is read-only.  Even an identical value never gets
        # reopened for writing, so a racing caller cannot truncate it.
        require(target.read_bytes() == raw, f"immutable artifact changed: {path}")
    else:
        # Write privately, fsync the complete bytes, and publish with an
        # exclusive hard-link.  Creating the final pathname before writing
        # would expose a zero-length file to a racing reader.
        temporary_fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.",
                                                        dir=str(target.parent))
        try:
            with os.fdopen(temporary_fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary_name, target)
            except FileExistsError:
                # Another writer won the one-shot race.  Validate its complete
                # regular-file bytes; never retry with a write or replacement.
                info = target.lstat()
                require(not stat.S_ISLNK(info.st_mode) and stat.S_ISREG(info.st_mode),
                        f"immutable artifact target is not a regular file: {path}")
                require(target.read_bytes() == raw, f"immutable artifact changed: {path}")
            else:
                try:
                    directory_fd = os.open(target.parent,
                                           os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                except OSError:
                    directory_fd = None
                if directory_fd is not None:
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
    return {"path": path, "sha256": sha256(raw)}


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--manifest", default=MANIFEST_PATH)
    parser.add_argument("--mode", choices=("static",), default="static",
                        help="Read-only protocol validation; runtime dispatch is intentionally absent")
    args = parser.parse_args(argv)
    try:
        result = validate_static(Path(args.root), args.manifest)
    except Replacement15Error as exc:
        print(json.dumps({"status": "preparation-hold", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": result["status"], "groups": result["groups"],
                      "manifest": result["manifest_ref"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


# BF15 stage boundary -----------------------------------------------------
# These functions intentionally live after the immutable protocol CLI.  They
# are imported by admission/supervisor-14; importing the protocol itself
# remains read-only and never loads the frozen executor.
STAGE_BRIDGE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-10.py"
STAGE_SCHEMA = "v092-bifrost-v0140-replay-stage/v4"
PARENT_STAGE_COUNT = 21
CHILD_STAGE_COUNT = 20


def _stage_bridge(root: Path) -> Any:
    active = _PROTOCOL_STAGE.get()
    require(active is not None and Path(root).resolve() == active["root"],
            "implicit stage bridge import is forbidden; provide pinned graph bridge")
    return active["bridge"]


def build_parent_stage(root: Path | str, **kwargs: Any) -> Any:
    """Build exactly one immutable parent stage from one actual runtime."""
    bridge = kwargs.pop("bridge", None) or _stage_bridge(Path(root).resolve())
    return bridge.build_parent_stage(Path(root).resolve(), **kwargs)


def build_successor_stage(root: Path | str, **kwargs: Any) -> Any:
    bridge = kwargs.pop("bridge", None) or _stage_bridge(Path(root).resolve())
    return bridge.build_successor_stage(Path(root).resolve(), **kwargs)


def assert_stage_current(root: Path | str, stage: Any, graph: Any | None = None, *, pinned_bridge: Any = None) -> None:
    bridge = pinned_bridge if pinned_bridge is not None else _stage_bridge(Path(root).resolve())
    graph = stage.graph if graph is None else graph
    graph.assert_member("bridge10", bridge)
    bridge.assert_stage_current(Path(root).resolve(), stage, graph)


def write_completion(root: Path | str, **kwargs: Any) -> Any:
    bridge = kwargs.pop("bridge", None) or _stage_bridge(Path(root).resolve())
    return bridge.write_completion(Path(root).resolve(), **kwargs)


def build_child_stage(root: Path | str, **kwargs: Any) -> Any:
    bridge = kwargs.pop("bridge", None) or _stage_bridge(Path(root).resolve())
    return bridge.build_child_stage(Path(root).resolve(), **kwargs)


def validate_stage_transition(root: Path | str, predecessor: Any, successor: Any,
                              graph: Any) -> None:
    require(successor.predecessor_identity_sha256 == predecessor.identity_sha256,
            "stage transition predecessor identity differs")
    predecessor.assert_graph(graph)
    successor.assert_graph(graph)
    bridge = _stage_bridge(Path(root).resolve())
    bridge.assert_stage_current(Path(root).resolve(), successor, graph)


# Receipt validation shares exact graph-owned objects within one stage.
import contextvars as _contextvars
import contextlib as _contextlib
_PROTOCOL_STAGE = _contextvars.ContextVar("bf14_protocol_stage", default=None)

@_contextlib.contextmanager
def stage_context(root: Path | str, *, stage: Any, graph: Any, pinned_bridge: Any):
    graph.assert_member("bridge10", pinned_bridge)
    require(graph.module("protocol15").__dict__ is globals(), "protocol module is not owned by stage graph")
    require(isinstance(stage, pinned_bridge._OpaqueStage), "protocol cannot accept reconstructed stage")
    stage.assert_graph(graph)
    root = Path(root).resolve()
    pinned_bridge.assert_stage_current(root, stage, graph)
    opaque_runtime = stage.runtime
    returned_runtime = pinned_bridge.runtime_objects(stage)
    require(returned_runtime is opaque_runtime, "bridge returned copied runtime authority")
    if isinstance(opaque_runtime, pinned_bridge.ActualRuntimeContext):
        runtime = opaque_runtime.objects
        require(opaque_runtime.graph is graph, "runtime graph instance differs")
        require(opaque_runtime.root == Path(root).resolve(), "runtime checkout differs")
        require(runtime is opaque_runtime.objects, "bridge returned copied runtime objects")
        actual_modules = runtime.get("modules")
        require(isinstance(actual_modules, Mapping) and
                tuple(actual_modules) == ("replacement05", "executor", "checker", "configuration"),
                "runtime object map lost its frozen module roster")
        require(actual_modules["replacement05"] is pinned_bridge._replacement_runtime_member(graph) and
                all(actual_modules[name] is graph.module(name)
                    for name in ("executor", "checker", "configuration")),
                "runtime object map lost exact pinned module instances")
    else:
        require(graph.fixture_only is True and isinstance(opaque_runtime, Mapping),
                "production requires actual opaque runtime context")
        runtime = opaque_runtime
    require(isinstance(runtime, Mapping), "stage does not retain actual runtime objects")
    require(isinstance(runtime, Mapping) and isinstance(runtime.get("protocol_static"), Mapping),
            "actual runtime lacks immutable protocol validation result")
    token = _PROTOCOL_STAGE.set({"root":root,"stage":stage,"graph":graph,"bridge":pinned_bridge,"runtime":runtime})
    try:
        yield
    finally:
        _PROTOCOL_STAGE.reset(token)
