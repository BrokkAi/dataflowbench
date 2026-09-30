#!/usr/bin/env python3
"""Durably claim prospective v0.9.0 release operations before dispatch.

Contracts opt into this guard with a cumulative_attempts object. Its baseline
is a hash-pinned JSON document with schema release-attempt-baseline/v1 and a
historical_counts map from root-independent operation keys (group:<id> or
control:<id>) to non-negative integers or null. Missing or
unknown counts block that operation unless an explicit hash-bound recovery
allocation is approved. A recovery allowance never asserts the original
cumulative two-attempt limit was satisfied.

The ledger is outside execution roots. Its separately created random anchor is
hash-pinned by the reviewed contract, so a missing ledger cannot be silently
reinitialized. Initialize explicitly with this script's init command, review
the printed cumulative_attempts object, and add it to the prospective contract.
Launchers never initialize a missing ledger. The versioned recovery launchers require this field; historical launchers stay unchanged.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import sys

from release_attempt_v090 import AttemptError, SERIAL_LOCK_PATH


FIELD_SCHEMA = "release-cumulative-attempts/v1"
BASELINE_SCHEMA = "release-attempt-baseline/v1"
LEDGER_SCHEMA = "release-cumulative-attempt-ledger/v1"
ANCHOR_SCHEMA = "release-cumulative-attempt-anchor/v1"
RELEASE = "v0.9.0"
MAX_ATTEMPTS = 2
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OPERATION = re.compile(r"(?:group|control):[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class ClaimError(AttemptError):
    """A fail-closed prospective cumulative-attempt error."""


def _fail(message: str, exc: BaseException | None = None):
    error = ClaimError(message)
    if exc is not None:
        raise error from exc
    raise error


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_regular(path: Path, description: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                _fail(f"{description} is not a regular file: {path}")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(fd)
    except ClaimError:
        raise
    except OSError as exc:
        _fail(f"cannot read {description} {path}: {exc}", exc)


def _json_object(raw: bytes, description: str) -> dict:
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"{description} is not valid JSON: {exc}", exc)
    if not isinstance(value, dict):
        _fail(f"{description} must be a JSON object")
    return value


def _relative_baseline_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        _fail("cumulative_attempts.baseline.path must be a repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        _fail(f"unsafe cumulative-attempt baseline path: {value!r}")
    return path


def _root_file(root: Path, relative: PurePosixPath, description: str) -> Path:
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            _fail(f"cannot inspect {description} {current}: {exc}", exc)
        if stat.S_ISLNK(mode):
            _fail(f"symlink in {description} path: {relative.as_posix()}")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(mode):
            _fail(f"non-directory ancestor in {description} path: {relative.as_posix()}")
    try:
        current.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        _fail(f"{description} escapes the execution root: {relative.as_posix()}", exc)
    return current


def _absolute_path(value: object, description: str) -> Path:
    if not isinstance(value, str) or not value:
        _fail(f"{description} must be an absolute path")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        _fail(f"{description} must be a normalized absolute path")
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        _fail(f"cannot resolve {description}: {exc}", exc)
    if resolved != path:
        _fail(f"{description} must not use symlinked or non-canonical components")
    return path


def _validate_counts(value: object, description: str) -> dict:
    if not isinstance(value, dict):
        _fail(f"{description} must be an operation-to-count object")
    for operation, count in value.items():
        if not isinstance(operation, str) or not _OPERATION.fullmatch(operation):
            _fail(f"invalid root-independent operation key in {description}: {operation!r}")
        if count is not None and (type(count) is not int or count < 0):
            _fail(f"{description}[{operation!r}] must be a non-negative integer or null")
    return value


def contract_binding(contract: dict) -> str:
    """Exclude accounting metadata and its allocation pin to avoid hash cycles.

    The reviewed ledger anchor separately binds the omitted allocation digest.
    All other fields, including baseline input identity and command inventory,
    remain covered by this projection.
    """
    projected = json.loads(json.dumps(contract))
    accounting = projected.pop('cumulative_attempts', {})
    allocation = accounting.get('recovery_allocation', {})
    projected.get('input_identities', {}).pop(allocation.get('path'), None)
    return _sha(_canonical(projected))


def _allocation(root, contract, baseline, counts, ledger_path):
    limits = {key: (max(0, MAX_ATTEMPTS-count) if count is not None else 0)
              for key, count in counts.items()}
    ref = contract.get('cumulative_attempts', {}).get('recovery_allocation')
    if ref is None:
        return baseline, limits
    if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
        _fail('recovery allocation must bind path and sha256')
    path = _root_file(root, _relative_baseline_path(ref['path']), 'recovery allocation')
    raw = _read_regular(path, 'recovery allocation')
    if _sha(raw) != ref['sha256']:
        _fail('recovery allocation digest mismatch')
    allocation = _json_object(raw, 'recovery allocation')
    if (allocation.get('schema') != 'release-recovery-allocation/v1' or
            allocation.get('release') != RELEASE or allocation.get('approved') is not True or
            allocation.get('claims_per_operation') != 1 or
            type(allocation.get('claims_per_operation')) is not int or
            not isinstance(allocation.get('allocation_id'), str) or not allocation['allocation_id']):
        _fail('explicitly approved one-claim recovery allocation required')
    if allocation.get('ledger_path') != str(ledger_path):
        _fail('recovery allocation cannot move to another ledger')
    digest = contract_binding(contract)
    if allocation.get('contract_binding_sha256') != digest:
        _fail('recovery allocation contract binding mismatch')
    operations = allocation.get('operations')
    if (not isinstance(operations, list) or not operations or
            any(not isinstance(op, str) or op not in counts for op in operations) or
            len(set(operations)) != len(operations)):
        _fail('recovery allocation requires unique named baseline operations')
    # This is a distinct disclosed allowance, never an inferred historical count.
    limits = {op: 1 for op in operations}
    return {**baseline, 'recovery_allocation': ref,
            'contract_binding_sha256': digest}, limits


def _binding(root: Path, contract: dict) -> tuple[dict, dict, Path, Path, dict]:
    field = contract.get("cumulative_attempts")
    if not isinstance(field, dict) or field.get("schema") != FIELD_SCHEMA:
        _fail("cumulative_attempts must use schema " + FIELD_SCHEMA)
    baseline = field.get("baseline")
    if not isinstance(baseline, dict):
        _fail("cumulative_attempts.baseline must bind path and sha256")
    baseline_path = _relative_baseline_path(baseline.get("path"))
    baseline_sha = baseline.get("sha256")
    if not isinstance(baseline_sha, str) or not _SHA256.fullmatch(baseline_sha):
        _fail("cumulative_attempts.baseline.sha256 must be a lowercase SHA-256")
    baseline_file = _root_file(root, baseline_path, "historical-attempt baseline")
    baseline_raw = _read_regular(baseline_file, "historical-attempt baseline")
    if _sha(baseline_raw) != baseline_sha:
        _fail("hash-bound historical-attempt baseline mismatch")
    baseline_doc = _json_object(baseline_raw, "historical-attempt baseline")
    if baseline_doc.get("schema") != BASELINE_SCHEMA or baseline_doc.get("release") != RELEASE:
        _fail("historical-attempt baseline schema or release mismatch")
    counts = _validate_counts(baseline_doc.get("historical_counts"), "historical_counts")

    ledger_path = _absolute_path(field.get("ledger_path"), "cumulative-attempt ledger path")
    if baseline_doc.get('ledger_path') != str(ledger_path):
        _fail('historical baseline pins a different release ledger')
    roots = [root, *[Path(p) for p in contract.get('execution_roots', {}).values()],
             *[Path(p) for p in contract.get('control_execution_roots', {}).values()]]
    if any(ledger_path == r.resolve() or r.resolve() in ledger_path.parents for r in roots):
        _fail('release claim ledger must be outside execution roots')
    identity = field.get("ledger_identity")
    if not isinstance(identity, dict):
        _fail("cumulative_attempts.ledger_identity must bind anchor_path and anchor_sha256")
    anchor_path = _absolute_path(identity.get("anchor_path"), "cumulative-attempt anchor path")
    anchor_sha = identity.get("anchor_sha256")
    if not isinstance(anchor_sha, str) or not _SHA256.fullmatch(anchor_sha):
        _fail("cumulative_attempts.ledger_identity.anchor_sha256 must be a lowercase SHA-256")
    if ledger_path == anchor_path:
        _fail("ledger and initialized anchor paths must be distinct")
    if field.get("max_attempts_per_operation") != MAX_ATTEMPTS or type(field.get("max_attempts_per_operation")) is not int:
        _fail("prospective cumulative-attempt cap must be exactly two")
    baseline, limits = _allocation(root, contract, baseline, counts, ledger_path)
    return field, baseline, ledger_path, anchor_path, {
        "counts": counts, "limits": limits, "anchor_sha256": anchor_sha,
        "identity": {"anchor_path": str(anchor_path), "anchor_sha256": anchor_sha},
    }


def _anchor_bytes(anchor_path: Path, expected_sha: str, baseline: dict,
                  ledger_path: Path) -> bytes:
    raw = _read_regular(anchor_path, "initialized cumulative-attempt anchor")
    if _sha(raw) != expected_sha:
        _fail("initialized cumulative-attempt anchor identity mismatch")
    anchor = _json_object(raw, "initialized cumulative-attempt anchor")
    if (anchor.get("schema") != ANCHOR_SCHEMA or anchor.get("release") != RELEASE or
            anchor.get("baseline") != baseline or anchor.get("ledger_path") != str(ledger_path) or
            not isinstance(anchor.get("nonce"), str) or not re.fullmatch(r"[0-9a-f]{64}", anchor["nonce"])):
        _fail("initialized anchor does not match the reviewed ledger and baseline binding")
    if raw != _canonical(anchor) + b"\n":
        _fail("initialized anchor is not in canonical form")
    return raw


def _ledger_rows(raw: bytes, *, baseline: dict, identity: dict, ledger_path: Path,
                 anchor_sha: str, limits: dict) -> tuple[list[dict], bytes]:
    if not raw.endswith(b"\n"):
        _fail("cumulative-attempt ledger has a partial final record")
    lines = raw.splitlines(keepends=True)
    if not lines or any(line == b"\n" for line in lines):
        _fail("cumulative-attempt ledger is empty or contains blank records")
    expected_header = {
        "kind": "anchor", "schema": LEDGER_SCHEMA, "release": RELEASE,
        "baseline": baseline, "ledger_path": str(ledger_path),
        "ledger_identity": identity,
    }
    header = _json_object(lines[0][:-1], "cumulative-attempt ledger header")
    if header != expected_header or lines[0] != _canonical(expected_header) + b"\n":
        _fail("cumulative-attempt ledger header or reviewed identity mismatch")
    previous = _sha(lines[0])
    rows = []
    observed = {}
    sequence = 0
    for line in lines[1:]:
        row = _json_object(line[:-1], "cumulative-attempt ledger record")
        if line != _canonical(row) + b"\n":
            _fail("cumulative-attempt ledger record is not canonical")
        expected_keys = {"kind", "sequence", "operation_key", "previous_sha256", "record_sha256"}
        if set(row) != expected_keys or row.get("kind") != "claim":
            _fail("cumulative-attempt ledger record has an unsupported shape")
        sequence += 1
        if type(row.get("sequence")) is not int or row["sequence"] != sequence:
            _fail("cumulative-attempt ledger sequence has a gap or reset")
        operation = row.get("operation_key")
        if not isinstance(operation, str) or not _OPERATION.fullmatch(operation):
            _fail("cumulative-attempt ledger contains an invalid operation key")
        if row.get("previous_sha256") != previous:
            _fail("cumulative-attempt ledger hash chain mismatch")
        payload = {key: value for key, value in row.items() if key != "record_sha256"}
        if row.get("record_sha256") != _sha(_canonical(payload)):
            _fail("cumulative-attempt ledger record hash mismatch")
        observed[operation] = observed.get(operation, 0) + 1
        if observed[operation] > limits.get(operation, 0):
            _fail(f"cumulative-attempt ledger exceeds the approved cap for {operation}")
        rows.append(row)
        previous = _sha(line)
    return rows, previous


def _write_exclusive(path: Path, raw: bytes, description: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            written = os.write(fd, raw)
            if written != len(raw):
                _fail(f"short write while creating {description}; state is now fail-closed")
            os.fsync(fd)
        finally:
            os.close(fd)
        dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except ClaimError:
        raise
    except OSError as exc:
        _fail(f"cannot exclusively create {description} {path}: {exc}", exc)


def _global_lock():
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(SERIAL_LOCK_PATH, flags, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd
    except OSError as exc:
        _fail(f"cannot acquire the release serial lock: {exc}", exc)


def initialize_ledger(root, baseline_path: str, baseline_sha256: str,
                      ledger_path: str, anchor_path: str, *, contract: dict | None = None) -> dict:
    """Explicitly create the immutable anchor and empty ledger with O_EXCL.

    The returned cumulative_attempts object is the binding to review and add
    to the prospective contract. Existing paths are never overwritten.
    """
    root = Path(root).resolve(strict=True)
    relative = _relative_baseline_path(baseline_path)
    if not isinstance(baseline_sha256, str) or not _SHA256.fullmatch(baseline_sha256):
        _fail("reviewed baseline SHA-256 must be lowercase hexadecimal")
    baseline_file = _root_file(root, relative, "historical-attempt baseline")
    raw = _read_regular(baseline_file, "historical-attempt baseline")
    if _sha(raw) != baseline_sha256:
        _fail("reviewed historical-attempt baseline SHA-256 mismatch")
    document = _json_object(raw, "historical-attempt baseline")
    if document.get("schema") != BASELINE_SCHEMA or document.get("release") != RELEASE:
        _fail("historical-attempt baseline schema or release mismatch")
    counts = _validate_counts(document.get("historical_counts"), "historical_counts")
    baseline = {"path": relative.as_posix(), "sha256": baseline_sha256}
    ledger = _absolute_path(ledger_path, "cumulative-attempt ledger path")
    if document.get('ledger_path') != str(ledger):
        _fail('historical baseline pins a different release ledger')
    anchor_file = _absolute_path(anchor_path, "cumulative-attempt anchor path")
    if ledger == anchor_file:
        _fail("ledger and initialized anchor paths must be distinct")
    for path, description in ((ledger, "ledger"), (anchor_file, "anchor")):
        if not path.parent.is_dir():
            _fail(f"{description} parent directory must already exist: {path.parent}")
        if path.exists() or path.is_symlink():
            _fail(f"{description} already exists; initialization never resets state: {path}")

    if contract is not None:
        field = contract.get('cumulative_attempts', {})
        if field.get('baseline') != baseline or field.get('ledger_path') != str(ledger):
            _fail('initialization arguments differ from reviewed contract')
        baseline, _ = _allocation(root, contract, baseline, counts, ledger)
    lock_fd = _global_lock()
    try:
        nonce = secrets.token_hex(32)
        anchor_doc = {"schema": ANCHOR_SCHEMA, "release": RELEASE,
                      "baseline": baseline, "ledger_path": str(ledger), "nonce": nonce}
        anchor_raw = _canonical(anchor_doc) + b"\n"
        anchor_sha = _sha(anchor_raw)
        identity = {"anchor_path": str(anchor_file), "anchor_sha256": anchor_sha}
        header = {"kind": "anchor", "schema": LEDGER_SCHEMA, "release": RELEASE,
                  "baseline": baseline, "ledger_path": str(ledger),
                  "ledger_identity": identity}
        # Both files are exclusive; a crash between creations leaves an
        # incomplete state that launchers reject and initialization won't reset.
        _write_exclusive(anchor_file, anchor_raw, "initialized anchor")
        _write_exclusive(ledger, _canonical(header) + b"\n", "cumulative-attempt ledger")
        return {"schema": FIELD_SCHEMA, "baseline": {"path": relative.as_posix(), "sha256": baseline_sha256},
                **({"recovery_allocation": contract["cumulative_attempts"]["recovery_allocation"]} if contract is not None and "recovery_allocation" in contract.get("cumulative_attempts", {}) else {}),
                "ledger_path": str(ledger), "ledger_identity": identity,
                "max_attempts_per_operation": MAX_ATTEMPTS}
    finally:
        os.close(lock_fd)


def claim_attempt(root, contract: dict, operation_key: str) -> dict | None:
    """Append and fsync one claim; recovery accounting is mandatory.

    The caller runs this only after the launch gate, inside the existing global
    serial lock. A ledger-local flock also serializes direct concurrent calls.
    """
    if "cumulative_attempts" not in contract:
        _fail("recovery launcher requires cumulative_attempts")
    if not isinstance(operation_key, str) or not _OPERATION.fullmatch(operation_key):
        _fail("claim operation key must be a root-independent group:<id> or control:<id>")
    root = Path(root).resolve(strict=True)
    field, baseline, ledger_path, anchor_path, validated = _binding(root, contract)
    _anchor_bytes(anchor_path, validated["anchor_sha256"], baseline, ledger_path)
    limit = validated["limits"].get(operation_key, 0)
    if limit <= 0:
        _fail(f"historical count unknown or allowance exhausted for {operation_key}")

    flags = os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(ledger_path, flags)
    except OSError as exc:
        _fail(f"durable cumulative-attempt ledger is missing or unreadable: {exc}", exc)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            _fail("durable cumulative-attempt ledger is not a regular file")
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        baseline_ref = baseline
        rows, previous = _ledger_rows(
            b"".join(chunks), baseline=baseline_ref,
            identity=validated["identity"], ledger_path=ledger_path,
            anchor_sha=validated["anchor_sha256"], limits=validated["limits"])
        current = sum(row["operation_key"] == operation_key for row in rows)
        if current >= limit:
            _fail(f"approved new-claim allowance ({limit}) exhausted for {operation_key}")
        payload = {"kind": "claim", "sequence": len(rows) + 1,
                   "operation_key": operation_key, "previous_sha256": previous}
        row = {**payload, "record_sha256": _sha(_canonical(payload))}
        encoded = _canonical(row) + b"\n"
        written = os.write(fd, encoded)
        if written != len(encoded):
            _fail("short append to cumulative-attempt ledger; dispatch blocked")
        os.fsync(fd)
        return row
    except ClaimError:
        raise
    except OSError as exc:
        _fail(f"cannot validate or durably append cumulative-attempt claim: {exc}", exc)
    finally:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="explicitly initialize a prospective claim ledger")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--baseline", required=True, help="reviewed repository-relative baseline JSON")
    init.add_argument("--baseline-sha256", required=True)
    init.add_argument("--ledger-path", required=True, help="durable absolute JSONL path")
    init.add_argument("--anchor-path", required=True, help="durable absolute immutable anchor path")
    init.add_argument("--contract", help="prospective contract containing any approved recovery allocation")
    args = parser.parse_args()
    if args.command == "init":
        binding = initialize_ledger(args.root, args.baseline, args.baseline_sha256,
                                    args.ledger_path, args.anchor_path,
                                    contract=json.loads((args.root/args.contract).read_text()) if args.contract else None)
        print(json.dumps({"cumulative_attempts": binding}, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ClaimError, OSError, ValueError) as exc:
        raise SystemExit(str(exc))
