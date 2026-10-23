#!/usr/bin/env python3
"""Guarded append-only continuation for the v0.9.2 Swift Joern group.

The v0.9.2 contract and its first 86 ledger rows are historical inputs.  This
module validates that history with the frozen executor/checker, derives an
isolated Joern context from a separately pinned continuation contract, and
then dispatches at most one Joern03 followed by CodeQL01.  It deliberately
does not teach the frozen executor about a new contract path: the new context
is assembled after the frozen base contract has been validated.

All prospective inputs are required to be committed, byte bound, and present
in a continuation manifest.  In particular, no model mode or capability value
is inferred here.  Capability and control rebinding remain the responsibility
of the hash-pinned repair shim and its reviewed artifacts.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
BASE_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
BASE_SHA = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
BASE_SOURCE_COMMIT = "0f105a6f4bd6a954fd09cb222e8a519162393aec"
OLD_JOERN_PLAN = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
OLD_JOERN_PLAN_SHA = "e5cfd9d5473fd47f54de25d74a6f945c667c086ce471d5f6cdcead797bf9e3ab"
LEDGER = "reports/releases/v0.9.2/ledger-v1.jsonl"
SEALED_ROWS = 86
SEALED_LEDGER_SHA = "ca7152afb422160b30c2f38677aa539a1463b45e3b41131848b3d9e81d4a1084"
ORIGIN = "2026-10-20T00:57:00.680937+00:00"
CUTOFF = "2026-10-23T21:33:00.680937+00:00"
TOTAL_WALL_SECONDS = 333360
FULL_REMAINING_RESERVE_SECONDS = 29400
CODEQL_PHASE_REMAINING_RESERVE_SECONDS = FULL_REMAINING_RESERVE_SECONDS - 1368
LIVE_RESOURCE_FLOOR_BYTES = 127 * 1024 ** 3
JOERN_GROUP = "joern-swift-common108"
CODEQL_GROUP = "codeql-swift-common108"
JOERN_ATTEMPT = "joern-swift-common108-attempt-03-series-01"
CODEQL_ATTEMPT = "codeql-swift-common108-attempt-01-series-01"
DEFAULT_MANIFEST = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "continuation-manifest.json"
)
DEFAULT_CONTRACT = (
    "reports/releases/v0.9.2/execution-v4/continuations/"
    "joern-capability-repair-01-contract.json"
)
QUAL_ROOT = "reports/releases/v0.9.2/qualification/joern-capability-repair-01"
FRESH_CAPTURE_PREFIX = f"{QUAL_ROOT}/control-capture-01/"
AUTHORIZATION_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "authorization.json"
)
AUTHORIZATION_SHA = "8268eb27d8f9f8ef3c00b90007b729973719aa1e83f30e95d6b157d95ed33d3b"
BOOTSTRAP_REVIEW_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "control-bootstrap-independent-review-01.json"
)
BOOTSTRAP_REVIEW_SHA = "47faef0104b9cddefaa4b2ef747d64074271c273372775af25eee52c361502bf"
CONTINUATION_TEST = "reports/releases/v0.9.2/acquisition/test-joern-capability-continuation-01.py"
SHIM_TEST = "scripts/test-joern-capability-repair-v092.py"
RE_SHA = re.compile(r"[0-9a-f]{64}\Z")
RE_COMMIT = re.compile(r"[0-9a-f]{40}\Z")

FROZEN = {
    "execute": (
        "scripts/execute-release-v092.py",
        "fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8",
    ),
    "checker": (
        "scripts/check-release-v092.py",
        "0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928",
    ),
    "configuration": (
        "scripts/validate-v092-report-configurations.py",
        "21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858",
    ),
}


class ContinuationError(ValueError):
    """A continuation input, identity, or receipt failed closed validation."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise ContinuationError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    try:
        return sha_bytes(path.read_bytes())
    except OSError as exc:
        raise ContinuationError(f"cannot hash {path}: {exc}") from exc


def _relative(value: object, description: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{description} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts),
            f"{description} is unsafe")
    return path


def _read(root: Path, value: str) -> bytes:
    path = root
    for part in _relative(value).parts:
        path = path / part
        require(not path.is_symlink(), f"symlink in bound path: {value}")
    require(path.is_file(), f"missing bound file: {value}")
    return path.read_bytes()


def _json(root: Path, value: str, description: str = "JSON") -> dict[str, Any]:
    try:
        parsed = json.loads(_read(root, value))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError(f"invalid {description}: {value}") from exc
    require(isinstance(parsed, dict), f"{description} must be an object: {value}")
    return parsed


def _binding(root: Path, ref: object, description: str) -> bytes:
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            f"{description} must be an exact path/SHA binding")
    path = ref.get("path")
    digest = ref.get("sha256")
    require(isinstance(path, str) and RE_SHA.fullmatch(str(digest or "")),
            f"{description} has malformed path/SHA")
    raw = _read(root, path)
    require(sha_bytes(raw) == digest, f"{description} digest changed: {path}")
    return raw


def _write_new(path: Path, value: object) -> None:
    require(not path.exists() and not path.is_symlink(), f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContinuationError(f"git identity query failed: git {' '.join(args)}") from exc


def _verify_commit_blobs(root: Path, commit: str,
                         bindings: dict[str, str], description: str) -> None:
    """Verify many source-input blobs in one read-only git cat-file session."""
    require(RE_COMMIT.fullmatch(commit), f"{description} commit is malformed")
    if not bindings:
        return
    try:
        process = subprocess.Popen(
            ["git", "cat-file", "--batch"], cwd=root,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise ContinuationError(f"cannot inspect {description} blobs") from exc
    assert process.stdin is not None and process.stdout is not None
    try:
        for path, expected in bindings.items():
            process.stdin.write(f"{commit}:{path}\n".encode())
        process.stdin.close()
        for path, expected in bindings.items():
            header = process.stdout.readline()
            require(header, f"{description} blob response is truncated: {path}")
            fields = header.decode("ascii", "strict").rstrip("\n").split()
            require(len(fields) == 3 and fields[1] == "blob" and fields[2].isdigit(),
                    f"{description} binding is not a regular blob: {path}")
            size = int(fields[2])
            data = process.stdout.read(size)
            require(len(data) == size, f"{description} blob response is truncated: {path}")
            require(process.stdout.read(1) == b"\n", f"{description} blob framing changed: {path}")
            require(sha_bytes(data) == expected,
                    f"{description} digest changed at {commit}: {path}")
        return_code = process.wait()
        require(return_code == 0, f"git blob inspection failed for {description}")
    except (UnicodeError, BrokenPipeError, OSError) as exc:
        raise ContinuationError(f"cannot inspect {description} blobs") from exc
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def _load_frozen(root: Path, name: str) -> Any:
    relative, expected = FROZEN[name]
    path = root / Path(*_relative(relative, "frozen module").parts)
    require(path.is_file() and not path.is_symlink(), f"missing frozen {name} module")
    require(sha(path) == expected, f"frozen {name} module digest changed")
    spec = importlib.util.spec_from_file_location(
        f"joern_continuation_frozen_{name}", path
    )
    require(spec is not None and spec.loader is not None, f"cannot import frozen {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_ledger(raw: bytes) -> list[dict[str, Any]]:
    require(not raw or raw.endswith(b"\n"), "ledger must end with a newline")
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines(keepends=True):
        try:
            row = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContinuationError("ledger contains invalid JSON") from exc
        require(isinstance(row, dict), "ledger rows must be objects")
        canonical = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        require(line == canonical, "ledger row is not canonical JSON")
        rows.append(row)
    ids = [row.get("attempt_id") for row in rows]
    require(all(isinstance(value, str) and value for value in ids), "ledger attempt identity missing")
    require(len(set(ids)) == len(ids), "ledger attempt identities are duplicated")
    return rows


def _ledger(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    raw = _read(root, LEDGER)
    return raw, _canonical_ledger(raw)


def _load_bound_object(root: Path, ref: object, description: str) -> dict[str, Any]:
    """Read a hash-bound JSON object, retaining the binding as an admission input."""
    raw = _binding(root, ref, description)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError(f"{description} is not valid JSON") from exc
    require(isinstance(value, dict), f"{description} must be a JSON object")
    return value


def _path_sha_refs(value: object) -> list[tuple[str, str]]:
    """Collect explicit path/SHA references from a JSON evidence index."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        path = value.get("path")
        digest = value.get("sha256")
        if isinstance(path, str) and isinstance(digest, str):
            found.append((path, digest))
        for child in value.values():
            found.extend(_path_sha_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_path_sha_refs(child))
    return found


def _source_input_map(value: object, description: str) -> dict[str, tuple[str, str | None]]:
    """Validate source-input entries while retaining reviewed role metadata.

    The frozen contract has four inherited entries carrying a ``role`` field.
    That metadata is part of each inherited entry and must survive the
    continuation byte-for-byte.  Additive entries emitted by the builder are
    plain path/SHA bindings, so a role on a newly added path is rejected by the
    continuation closure check rather than silently becoming unbound metadata.
    """
    require(isinstance(value, list), f"{description} is not a list")
    result: dict[str, tuple[str, str | None]] = {}
    for item in value:
        require(isinstance(item, dict) and
                set(item).issubset({"path", "sha256", "role"}) and
                {"path", "sha256"}.issubset(item) and
                isinstance(item.get("path"), str) and
                RE_SHA.fullmatch(str(item.get("sha256", ""))),
                f"{description} contains a malformed binding")
        path = item["path"]
        _relative(path, description)
        role = item.get("role")
        if "role" in item:
            require(isinstance(role, str) and role,
                    f"{description} contains malformed role metadata")
        require(path not in result, f"{description} contains a duplicate path: {path}")
        result[path] = (item["sha256"], role if isinstance(role, str) else None)
    return result


def _fresh_control_index_closure(root: Path, index_paths: list[str]) -> dict[str, str]:
    """Return the verified path/SHA graph reachable from fresh JSON indexes.

    The control receipts are indexes rather than self-contained evidence.  A
    receipt may reference a raw JSON object, which in turn references command,
    CPG, graph, stdout/stderr, or native-output files.  Walk JSON references to
    a fixed point so that the committed source snapshot contains every file the
    replay can consume.  Only the reviewed fresh-control namespace is allowed;
    historical raw witnesses are added separately from capability evidence.
    """
    result: dict[str, str] = {}
    pending = deque(index_paths)
    visited: set[str] = set()
    while pending:
        index_path = pending.popleft()
        require(index_path.startswith(FRESH_CAPTURE_PREFIX),
                f"fresh control index escaped its reviewed namespace: {index_path}")
        if index_path in visited:
            continue
        visited.add(index_path)
        index = _json(root, index_path, f"fresh control graph node: {index_path}")
        for referenced_path, referenced_digest in sorted(set(_path_sha_refs(index))):
            if not referenced_path.startswith(FRESH_CAPTURE_PREFIX):
                continue
            require(referenced_path != index_path,
                    f"fresh control index self-references itself: {index_path}")
            ref = {"path": referenced_path, "sha256": referenced_digest}
            _binding(root, ref, f"fresh control referenced artifact: {referenced_path}")
            require(referenced_path not in result or
                    result[referenced_path] == referenced_digest,
                    f"fresh control graph has conflicting duplicate: {referenced_path}")
            result[referenced_path] = referenced_digest
            if referenced_path.endswith(".json") and referenced_path not in visited:
                pending.append(referenced_path)
    return result


def _check_authorization(root: Path, ref: object) -> dict[str, Any]:
    """Bind the exact human grant and reject any clock or attempt expansion."""
    require(ref == {"path": AUTHORIZATION_PATH, "sha256": AUTHORIZATION_SHA},
            "continuation authorization is not the exact human grant")
    value = _load_bound_object(root, ref, "continuation authorization")
    require(value.get("schema") == "v092-joern-capability-repair-authorization/v1",
            "continuation authorization schema changed")
    require(value.get("status") ==
            "preparation-authorized; execution requires final evidence-backed plan and independent review",
            "continuation authorization is not in the reviewed preparation state")
    require(value.get("maximum_joern_global_attempts") == 3 and
            value.get("additional_joern_attempts") == 1 and
            value.get("additional_time_seconds") == 0 and
            value.get("other_attempt_limits_unchanged") is True,
            "continuation authorization changes attempt or time limits")
    require(value.get("origin_utc") in {ORIGIN, ORIGIN.replace("+00:00", "Z")} and
            value.get("deadline_utc") in {CUTOFF, CUTOFF.replace("+00:00", "Z")},
            "continuation authorization changes the original clock")
    prohibited = value.get("prohibited")
    require(isinstance(prohibited, list) and
            "Guessed capability values" in prohibited and
            "Weakened validation" in prohibited and
            "Further retry-budget extension" in prohibited,
            "continuation authorization does not prohibit guessed values, weakened validation, and retry extension")
    return value


def _check_bootstrap_review(root: Path, ref: object, manifest: dict[str, Any]) -> dict[str, Any]:
    """Bind the bootstrap review only for the fresh-control admission it approved."""
    require(ref == {"path": BOOTSTRAP_REVIEW_PATH, "sha256": BOOTSTRAP_REVIEW_SHA},
            "continuation bootstrap review is not the reviewed control binding")
    value = _load_bound_object(root, ref, "continuation bootstrap review")
    require(value.get("schema") == "v092-joern-control-bootstrap-independent-review/v1" and
            value.get("status") == "approved-for-fresh-controls-only",
            "continuation bootstrap review does not have its restricted approval status")
    require(value.get("implementation_sha256") == manifest["artifacts"]["joern_shim"]["sha256"] and
            value.get("evidence_sha256") == manifest["artifacts"]["capability_evidence"]["sha256"],
            "bootstrap review is not bound to the manifest shim/evidence")
    exact = value.get("exact_contract")
    require(isinstance(exact, dict) and
            exact.get("pending_plan_sha256") == value.get("pending_plan_sha256") and
            exact.get("pending_control_plan_path") ==
            "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-02/control-plan-01.json" and
            value.get("control_plan_sha256") ==
            "ad02fc04ed5e81765160f9e32b9b84d0ee55dfd0460f7a4156c2e6404fe5c7a5" and
            exact.get("repaired_projection_sha256") ==
            "aab7ae8939cb963e88b629cd2247ecba5ab71431456f3b94d18028d2e227ec41",
            "bootstrap review does not bind the reviewed repaired projection")
    return value


def _check_final_review(root: Path, ref: object, manifest: dict[str, Any]) -> dict[str, Any]:
    """Require a separate, post-finalization review with exact continuation bindings.

    The final review is deliberately outside the plan/source commit closure.  The
    review binds those commits and artifacts, while the manifest binds the review
    digest.  This avoids a manifest/review self-reference while still making a
    status=approved review mandatory for execution.
    """
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            "final independent review binding is required")
    require(ref != manifest.get("independent_review"),
            "final independent review cannot reuse the bootstrap-only review")
    value = _load_bound_object(root, ref, "final independent review")
    require(value.get("status") == "approved" and
            value.get("review_type") == "independent-final-continuation-review" and
            value.get("automatic_retry") is False,
            "final independent review is not approved for continuation execution")
    bindings = value.get("bindings")
    require(isinstance(bindings, dict), "final independent review bindings are missing")
    artifacts = manifest["artifacts"]
    expected = {
        "authorization": {"path": AUTHORIZATION_PATH, "sha256": AUTHORIZATION_SHA},
        "ledger_prefix": manifest["ledger_prefix"],
        "source_commit": manifest["source_commit"],
        "plan_commit": manifest["plan_commit"],
        "continuation_contract": artifacts["continuation_contract"],
        "repaired_plan": artifacts["repaired_plan"],
        "capability_evidence": artifacts["capability_evidence"],
        "joern_shim": artifacts["joern_shim"],
        "continuation_source": artifacts["continuation_source"],
        "continuation_test": {"path": CONTINUATION_TEST, "sha256": sha(root / CONTINUATION_TEST)},
    }
    require(bindings == expected,
            "final independent review does not bind the exact continuation source/plan/artifact closure")
    return value


def _check_execution_admission(root: Path, ref: object, manifest: dict[str, Any],
                               *, group_id: str | None = None) -> dict[str, Any]:
    """Require the parent launcher's one-shot, resource-gated preflight receipt."""
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            "execution admission receipt binding is required")
    value = _load_bound_object(root, ref, "execution admission receipt")
    require(value.get("schema") == "v092-joern-capability-continuation-admission/v1" and
            value.get("status") == "ready-to-execute" and
            value.get("automatic_retry") is False and
            value.get("release_group_attempt") is False,
            "execution admission receipt is not a one-shot preflight")
    require(value.get("original_origin_utc") in {ORIGIN, ORIGIN.replace("+00:00", "Z")} and
            value.get("cutoff_utc") in {CUTOFF, CUTOFF.replace("+00:00", "Z")} and
            value.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "execution admission receipt changes the original clock")
    require(value.get("authorization") == {"path": AUTHORIZATION_PATH, "sha256": AUTHORIZATION_SHA} and
            value.get("ledger_prefix") == manifest["ledger_prefix"] and
            value.get("source_commit") == manifest["source_commit"] and
            value.get("plan_commit") == manifest["plan_commit"] and
            value.get("final_review") == manifest["final_review"],
            "execution admission receipt is not bound to the reviewed continuation")
    artifacts = manifest["artifacts"]
    bindings = value.get("artifacts")
    require(isinstance(bindings, dict), "execution admission artifact bindings are missing")
    expected_artifacts = {
        "continuation_source": artifacts["continuation_source"],
        "continuation_test": {"path": CONTINUATION_TEST,
                               "sha256": sha(root / CONTINUATION_TEST)},
        "continuation_contract": artifacts["continuation_contract"],
        "repaired_plan": artifacts["repaired_plan"],
        "capability_evidence": artifacts["capability_evidence"],
        "joern_shim": artifacts["joern_shim"],
    }
    require(bindings == expected_artifacts,
            "execution admission artifact closure differs from the manifest")
    replay_ref = value.get("retained_replay_output")
    replay_raw = _binding(root, replay_ref, "retained continuation replay output")
    try:
        replay = json.loads(replay_raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError("retained continuation replay output is not valid JSON") from exc
    require(isinstance(replay, dict) and
            replay.get("status") == "continuation-preflight-passed" and
            replay.get("ledger_rows") == SEALED_ROWS and
            replay.get("selected_groups") == 82 and
            replay.get("known_stale") == 0,
            "execution admission is not bound to a successful retained replay")
    phase_reserve = value.get("phase_remaining_reserved_seconds")
    require(isinstance(phase_reserve, dict) and
            type(phase_reserve.get(JOERN_GROUP)) is int and
            phase_reserve[JOERN_GROUP] >= FULL_REMAINING_RESERVE_SECONDS and
            type(phase_reserve.get(CODEQL_GROUP)) is int and
            phase_reserve[CODEQL_GROUP] >= CODEQL_PHASE_REMAINING_RESERVE_SECONDS,
            "execution admission phase reserve is incomplete")
    if group_id is not None:
        required = (FULL_REMAINING_RESERVE_SECONDS if group_id == JOERN_GROUP
                    else CODEQL_PHASE_REMAINING_RESERVE_SECONDS)
        require(group_id in {JOERN_GROUP, CODEQL_GROUP} and
                phase_reserve.get(group_id, 0) >= required,
                f"execution admission reserve is insufficient for {group_id}")
    require(value.get("no_foreign_processes") is True and
            value.get("resource_floor_bytes") == 127 * 1024 ** 3 and
            value.get("resource_floor_checked") is True and
            type(value.get("remaining_reserved_seconds")) is int and
            value["remaining_reserved_seconds"] >= FULL_REMAINING_RESERVE_SECONDS and
            value.get("exclusive_lock_checked") is True and
            value.get("fresh_attempt_namespaces") is True and
            value.get("fresh_sidecar_namespaces") is True,
            "execution admission resource/process/freshness gates are incomplete")
    return value


def _load_manifest(root: Path, manifest_path: str, manifest_sha: str,
                   *, require_admission: bool = False) -> dict[str, Any]:
    require(RE_SHA.fullmatch(manifest_sha), "manifest SHA is malformed")
    raw = _read(root, manifest_path)
    require(sha_bytes(raw) == manifest_sha, "continuation manifest digest changed")
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError("continuation manifest is not valid JSON") from exc
    require(isinstance(manifest, dict), "continuation manifest must be an object")
    require(manifest.get("schema") == "v092-joern-capability-continuation/v1" and
            manifest.get("finalized") is True, "continuation manifest is not finalized")
    require(manifest.get("original_origin_utc") == ORIGIN and
            manifest.get("cutoff_utc") == CUTOFF and
            manifest.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "continuation changes the original clock")
    prefix = manifest.get("ledger_prefix")
    require(prefix == {"path": LEDGER, "sha256": SEALED_LEDGER_SHA, "rows": SEALED_ROWS},
            "continuation does not bind the sealed ledger prefix")
    base = manifest.get("base_contract")
    require(base == {"path": BASE_CONTRACT, "sha256": BASE_SHA},
            "continuation does not bind the frozen base contract")
    source_commit = manifest.get("source_commit")
    plan_commit = manifest.get("plan_commit")
    require(isinstance(source_commit, str) and RE_COMMIT.fullmatch(source_commit) and
            source_commit != BASE_SOURCE_COMMIT, "new source commit is missing or unchanged")
    require(isinstance(plan_commit, str) and RE_COMMIT.fullmatch(plan_commit) and
            plan_commit != BASE_PLAN_COMMIT, "new plan commit is missing or unchanged")
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", BASE_SOURCE_COMMIT, source_commit],
                       cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "merge-base", "--is-ancestor", source_commit, plan_commit],
                       cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContinuationError("continuation source/plan commits are not an ordered descendant closure") from exc
    continuation = manifest.get("continuation_contract")
    require(continuation == {"path": DEFAULT_CONTRACT, "sha256": continuation.get("sha256")}
            if isinstance(continuation, dict) else False,
            "continuation contract path is not registered")
    require(RE_SHA.fullmatch(str(continuation.get("sha256", ""))),
            "continuation contract SHA is malformed")
    artifacts = manifest.get("artifacts")
    require(isinstance(artifacts, dict), "continuation artifact manifest is missing")
    required_artifacts = {"repaired_plan", "capability_evidence", "joern_shim",
                          "continuation_source", "continuation_contract"}
    require(set(artifacts) == required_artifacts, "continuation artifact closure is incomplete")
    for key, ref in artifacts.items():
        _binding(root, ref, f"continuation artifact {key}")
    require(artifacts["continuation_contract"] == continuation,
            "artifact and contract bindings differ")
    _check_authorization(root, manifest.get("authorization"))
    _check_bootstrap_review(root, manifest.get("independent_review"), manifest)
    # The bootstrap review intentionally cannot authorize execution.  A final
    # review is a separate artifact so it can bind the immutable final plan,
    # source, contract, prefix, and artifact closure without a self-reference.
    _check_final_review(root, manifest.get("final_review"), manifest)
    if require_admission:
        _check_execution_admission(root, manifest.get("execution_admission"), manifest)
    source_ref = artifacts["continuation_source"]
    require(source_ref.get("path") == Path(__file__).resolve().relative_to(root).as_posix(),
            "continuation source does not bind this file")
    codeql = manifest.get("codeql")
    joern = manifest.get("joern")
    for label, item, attempt, group in (("Joern", joern, JOERN_ATTEMPT, JOERN_GROUP),
                                        ("CodeQL", codeql, CODEQL_ATTEMPT, CODEQL_GROUP)):
        require(isinstance(item, dict) and item.get("group_id") == group and
                item.get("attempt_id") == attempt, f"{label} continuation identity is missing")
        require(isinstance(item.get("argv"), list) and item["argv"],
                f"{label} continuation argv is missing")
        require(item.get("maximum_attempts") == (3 if label == "Joern" else 2),
                f"{label} attempt allowance changed")
    require(joern.get("contract_sha256") == continuation["sha256"] and
            joern.get("source_commit") == source_commit and
            joern.get("plan_commit") == plan_commit,
            "Joern is not bound to the continuation source/plan/contract")
    # CodeQL01 is a new execution row.  Its command and qualification fields
    # remain the byte-equal historical group definition, while its durable
    # source/contract/plan identity is the continuation context.  Historical
    # rows are replayed through their original contexts below.
    require(codeql.get("contract_sha256") == continuation["sha256"] and
            codeql.get("source_commit") == source_commit and
            codeql.get("plan_commit") == plan_commit,
            "CodeQL continuation is not bound to the new source/plan/contract")
    fixture_revision = manifest.get("fixture_revision")
    require(isinstance(fixture_revision, str) and fixture_revision,
            "continuation fixture identity is missing")
    source_delta = manifest.get("source_inputs_delta")
    require(isinstance(source_delta, list) and source_delta,
            "continuation source-input delta is missing")
    seen_delta: set[str] = set()
    for item in source_delta:
        require(isinstance(item, dict) and set(item) == {"path", "sha256"} and
                isinstance(item.get("path"), str) and RE_SHA.fullmatch(str(item.get("sha256", ""))),
                "continuation source-input delta has a malformed binding")
        _relative(item["path"], "continuation source-input delta path")
        require(item["path"] not in seen_delta, "continuation source-input delta contains a duplicate path")
        seen_delta.add(item["path"])
    expected = manifest.get("expected")
    require(expected == {"ledger_rows": 88, "selected_groups": 84,
                         "partitions": 92, "rows": 4252, "known_stale": 0},
            "continuation denominator changed")
    # The source and continuation contract must be represented by committed
    # blobs.  A matching working-tree digest alone would admit an uncommitted
    # launch input.
    for key, ref in artifacts.items():
        path = ref["path"]
        try:
            committed = subprocess.check_output(
                ["git", "show", f"{plan_commit}:{path}"], cwd=root
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ContinuationError(f"continuation artifact is absent from plan commit: {path}") from exc
        require(sha_bytes(committed) == ref["sha256"],
                f"continuation artifact differs from plan commit: {key}")
    source_path = source_ref["path"]
    try:
        source_blob = subprocess.check_output(["git", "show", f"{source_commit}:{source_path}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContinuationError("continuation source is absent from its registered source commit") from exc
    require(sha_bytes(source_blob) == source_ref["sha256"],
            "continuation source differs from its registered source commit")
    return manifest


def _check_prefix(root: Path, rows: list[dict[str, Any]], raw: bytes) -> list[dict[str, Any]]:
    require(len(rows) >= SEALED_ROWS and sha_bytes(b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in rows[:SEALED_ROWS]
    )) == SEALED_LEDGER_SHA, "historical ledger prefix changed")
    prefix_raw = b"".join(raw.splitlines(keepends=True)[:SEALED_ROWS])
    require(sha_bytes(prefix_raw) == SEALED_LEDGER_SHA, "historical ledger prefix bytes changed")
    prefix = rows[:SEALED_ROWS]
    require(sum(row.get("status") == "completed" for row in prefix) == 82,
            "historical completion count changed")
    require(all(row.get("execution_series") == 1 for row in prefix),
            "historical ledger series changed")
    return prefix


def _attempt_number(attempt_id: object) -> int:
    match = re.fullmatch(r".+-attempt-(\d+)-series-\d+", str(attempt_id))
    require(match is not None, f"malformed attempt id: {attempt_id}")
    return int(match.group(1))


def _tail(rows: list[dict[str, Any]], *, final: bool) -> list[dict[str, Any]]:
    tail = rows[SEALED_ROWS:]
    require(len(tail) <= 2, "continuation appended more than Joern03 and CodeQL01")
    if tail:
        require(tail[0].get("attempt_id") == JOERN_ATTEMPT and
                tail[0].get("group_id") == JOERN_GROUP and
                tail[0].get("execution_series") == 1,
                "first continuation row is not Joern03")
        require(_attempt_number(tail[0].get("attempt_id")) == 3 and
                (tail[0].get("attempt_number") is None or tail[0].get("attempt_number") == 3),
                "Joern attempt number changed")
        if tail[0].get("status") == "completed":
            require(tail[0].get("exit_code") == 0 and
                    tail[0].get("timed_out") is False and
                    tail[0].get("capacity_loss") is None,
                    "completed Joern03 has a non-success terminal state")
    if len(tail) == 2:
        require(tail[0].get("status") == "completed" and tail[0].get("exit_code") == 0,
                "CodeQL cannot run after a failed Joern03")
        require(tail[1].get("attempt_id") == CODEQL_ATTEMPT and
                tail[1].get("group_id") == CODEQL_GROUP and
                tail[1].get("execution_series") == 1,
                "second continuation row is not CodeQL01")
        require(_attempt_number(tail[1].get("attempt_id")) == 1 and
                (tail[1].get("attempt_number") is None or tail[1].get("attempt_number") == 1),
                "CodeQL attempt number changed")
        if tail[1].get("status") == "completed":
            require(tail[1].get("exit_code") == 0 and
                    tail[1].get("timed_out") is False and
                    tail[1].get("capacity_loss") is None,
                    "completed CodeQL01 has a non-success terminal state")
    if final:
        require(len(tail) == 2 and all(row.get("status") == "completed" and
                                       row.get("exit_code") == 0 and
                                       row.get("timed_out") is False and
                                       row.get("capacity_loss") is None for row in tail),
                "final continuation is incomplete")
    return tail


def _raw_plan_delta(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    plan_ref = manifest["artifacts"]["repaired_plan"]
    raw = _binding(root, plan_ref, "repaired execution plan")
    old_raw = _read(root, OLD_JOERN_PLAN)
    require(sha_bytes(old_raw) == OLD_JOERN_PLAN_SHA, "retained Joern plan changed")
    try:
        old_plan = json.loads(old_raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError("retained Joern plan is not JSON") from exc
    require(isinstance(old_plan, dict), "retained Joern plan must be an object")
    try:
        plan = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError("repaired execution plan is not JSON") from exc
    require(isinstance(plan, dict), "repaired execution plan must be an object")
    require(plan.get("schema") == old_plan.get("schema") and
            plan.get("execution_series", 1) == old_plan.get("execution_series", 1) and
            plan.get("source_commit", old_plan.get("source_commit")) == old_plan.get("source_commit"),
            "repaired plan execution or source identity changed")
    require(plan.get("release_group_id") == JOERN_GROUP, "repaired plan group identity changed")
    require(plan.get("cases") and set(plan["cases"]) == set(old_plan.get("cases", {})),
            "repaired plan case roster changed")
    # The old plan is compared structurally.  The shim owns the capability
    # semantics and projection calculation; this guard prevents any unrelated
    # runtime, population, or engine mutation from entering the continuation.
    allowed = {"cases", "qualification_control_projection_sha256",
               "qualification_control_plan", "fresh_qualification", "registered_at_unix_seconds"}
    for key in set(old_plan) | set(plan):
        if key in allowed:
            continue
        require(plan.get(key) == old_plan.get(key), f"repaired plan changed forbidden field: {key}")
    return plan


def _derive_context(base: dict[str, Any], contract: dict[str, Any], contract_raw: bytes,
                    manifest: dict[str, Any], repaired_plan: dict[str, Any], executor: Any) -> dict[str, Any]:
    """Build a checker context without calling frozen validate_plan on v4 paths."""
    require(contract.get("schema_version") == 1 and contract.get("release") == "v0.9.2",
            "continuation contract schema or release differs")
    require(contract.get("execution_series") == 1 and
            contract.get("source_commit") == manifest["source_commit"] and
            contract.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "continuation contract clock or source differs")
    base_plan = base["plan"]
    allowed_top_level = {"source_commit", "source_inputs", "total_wall_budget_seconds",
                         "groups", "qualifications"}
    require(set(contract) == set(base_plan), "continuation contract top-level shape changed")
    for key in set(base_plan) - allowed_top_level:
        require(contract.get(key) == base_plan.get(key),
                f"continuation contract changed forbidden top-level field: {key}")
    require(contract.get("source_commit") == manifest["source_commit"] and
            contract.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "continuation contract clock or source differs")
    base_qualifications = base_plan.get("qualifications")
    new_qualifications = contract.get("qualifications")
    require(isinstance(base_qualifications, dict) and isinstance(new_qualifications, dict) and
            set(base_qualifications) == set(new_qualifications),
            "continuation qualification roster changed")
    for tool, old_qualification in base_qualifications.items():
        if tool != "joern":
            require(new_qualifications.get(tool) == old_qualification,
                    f"continuation changed unrelated qualification: {tool}")
    joern_qualification = new_qualifications.get("joern")
    require(isinstance(joern_qualification, dict) and
            joern_qualification.get("evidence") == repaired_plan.get("fresh_qualification"),
            "continuation Joern qualification does not bind fresh repaired evidence")
    groups = contract.get("groups")
    base_groups = base_plan["groups"]
    require(isinstance(groups, list) and len(groups) == len(base_groups),
            "continuation contract group count changed")
    by_id = {group.get("id"): group for group in groups}
    old_by_id = {group.get("id"): group for group in base_groups}
    require(set(by_id) == set(old_by_id), "continuation contract group roster changed")
    joern = by_id.get(JOERN_GROUP)
    require(isinstance(joern, dict) and joern.get("maximum_attempts") == 3,
            "Joern continuation does not carry the sole max-attempt exception")
    old_joern = old_by_id[JOERN_GROUP]
    joern_allowed = {"argv", "output_roots", "reports", "maximum_attempts", "joern_plan"}
    require(set(joern) == set(old_joern) | {"joern_plan"},
            "Joern continuation group shape changed")
    for group_id, old in old_by_id.items():
        new = by_id[group_id]
        if group_id != JOERN_GROUP:
            require(new == old, f"non-Joern group changed: {group_id}")
    codeql = old_by_id.get(CODEQL_GROUP)
    require(isinstance(codeql, dict) and
            manifest["codeql"].get("argv") == codeql.get("argv") and
            manifest["codeql"].get("output_roots") == codeql.get("output_roots"),
            "CodeQL continuation command or output binding changed")
    for key in set(old_joern) | set(joern):
        if key in joern_allowed:
            continue
        require(joern.get(key) == old_joern.get(key),
                f"Joern continuation changed forbidden group field: {key}")
    require(joern.get("family") == "joern" and joern.get("tool") == "joern" and
            joern.get("output_roots") == ["reports/raw/joern-common-v2/current108-v092-02"],
            "Joern continuation output binding changed")
    require(manifest["joern"].get("argv") == joern.get("argv"),
            "Joern continuation argv is not contract bound")
    require(manifest["joern"].get("output_root") == joern["output_roots"][0],
            "Joern continuation output root is not contract bound")
    repaired_ref = manifest["artifacts"]["repaired_plan"]
    require(joern.get("joern_plan") == repaired_ref,
            "Joern continuation does not bind the repaired execution plan")
    old_reports = old_joern.get("reports", [])
    new_reports = joern.get("reports", [])
    require(isinstance(old_reports, list) and isinstance(new_reports, list) and len(old_reports) == len(new_reports),
            "Joern continuation report partitions changed")
    for old_report, new_report in zip(old_reports, new_reports):
        require(isinstance(old_report, dict) and isinstance(new_report, dict),
                "Joern continuation report binding is malformed")
        old_without_source = {k: v for k, v in old_report.items() if k != "source_path"}
        new_without_source = {k: v for k, v in new_report.items() if k != "source_path"}
        require(old_without_source == new_without_source,
                "Joern continuation changed report identity or case partition")
        require(new_report.get("source_path") != old_report.get("source_path") and
                str(new_report.get("source_path", "")).startswith(
                    "reports/raw/joern-common-v2/current108-v092-02/"),
                "Joern continuation report source is not fresh")
    validated = copy.deepcopy(base)
    validated["repo_root"] = base["repo_root"]
    validated["path"] = base["repo_root"] / Path(*_relative(DEFAULT_CONTRACT).parts)
    validated["bytes_sha256"] = sha_bytes(contract_raw)
    validated["plan_raw"] = contract_raw
    validated["plan"] = contract
    validated["source_inputs"] = contract.get("source_inputs", base.get("source_inputs", []))
    validated["total_wall_budget_seconds"] = TOTAL_WALL_SECONDS
    validated["qualification"] = copy.deepcopy(base["qualification"])
    validated["qualification"]["joern"] = copy.deepcopy(joern_qualification)
    validated["groups"] = copy.deepcopy(base["groups"])
    normalized = next(item for item in validated["groups"] if item.get("id") == JOERN_GROUP)
    normalized["maximum_attempts"] = 3
    normalized["argv"] = copy.deepcopy(joern["argv"])
    normalized["output_roots"] = copy.deepcopy(joern["output_roots"])
    normalized["reports"] = copy.deepcopy(joern.get("reports", normalized.get("reports", [])))
    # The frozen runner's normalized group uses the plan's per-group binding;
    # update only those fields which changed for the fresh Joern output.
    normalized["joern_plan"] = copy.deepcopy(joern["joern_plan"])
    return validated


def _fresh_control_source_closure(root: Path, manifest: dict[str, Any],
                                  repaired_plan: dict[str, Any],
                                  evidence: dict[str, Any],
                                  base_inputs: dict[str, str]) -> dict[str, str]:
    """Derive the exact fresh-control transitive reference closure.

    Fresh controls contain large unreferenced compiler/workspace trees.  Only
    path/SHA references reachable from the reviewed run, qualification
    receipt, diagnostic review, and identity indexes are admitted, and only
    when they remain under the reviewed ``control-capture-01`` namespace.
    """
    result: dict[str, str] = {}

    def add(ref: object, description: str) -> None:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
                f"{description} is not an exact path/SHA reference")
        path = ref.get("path")
        digest = ref.get("sha256")
        require(isinstance(path, str) and RE_SHA.fullmatch(str(digest or "")),
                f"{description} has a malformed path/SHA reference")
        _binding(root, ref, description)
        require(path not in result or result[path] == digest,
                f"fresh source closure has conflicting duplicate: {path}")
        result[path] = digest

    artifacts = manifest["artifacts"]
    add(artifacts["repaired_plan"], "repaired plan source input")
    add(artifacts["capability_evidence"], "capability evidence source input")
    add(repaired_plan.get("qualification_control_plan"), "fresh control plan source input")
    fresh_qualification = repaired_plan.get("fresh_qualification")
    add(fresh_qualification, "fresh qualification receipt source input")
    qualification = _load_bound_object(root, fresh_qualification,
                                       "fresh qualification receipt")
    add(qualification.get("control_run"), "fresh control run source input")
    add(qualification.get("diagnostic_admission_review"),
        "fresh diagnostic review source input")
    add({"path": f"{QUAL_ROOT}/control-capture-01/identity.json",
         "sha256": sha(_read_path(root, f"{QUAL_ROOT}/control-capture-01/identity.json"))},
        "fresh control identity source input")
    add({"path": f"{QUAL_ROOT}/qualification-finalization-01.json",
         "sha256": sha(_read_path(root, f"{QUAL_ROOT}/qualification-finalization-01.json"))},
        "qualification finalization source input")
    add(artifacts["continuation_source"], "continuation source input")
    add({"path": CONTINUATION_TEST, "sha256": sha(_read_path(root, CONTINUATION_TEST))},
        "continuation test source input")
    add(artifacts["joern_shim"], "Joern repair shim source input")
    add({"path": SHIM_TEST, "sha256": sha(_read_path(root, SHIM_TEST))},
        "Joern repair shim test source input")

    # These indexes are the only roots allowed to expand into the fresh
    # capture tree.  Traversal follows every referenced JSON object to a fixed
    # point, so raw, command, CPG, graph, stdout/stderr, native-output, and
    # source-closure witnesses are included exactly when their parent evidence
    # references them.
    index_paths = [
        qualification["control_run"]["path"],
        fresh_qualification["path"],
        qualification["diagnostic_admission_review"]["path"],
        f"{QUAL_ROOT}/control-capture-01/identity.json",
    ]
    for referenced_path, referenced_digest in _fresh_control_index_closure(root, index_paths).items():
        add({"path": referenced_path, "sha256": referenced_digest},
            f"fresh control referenced artifact: {referenced_path}")

    raw_cases = evidence.get("historical_raw_evidence", {}).get("case_reports", {})
    require(isinstance(raw_cases, dict) and len(raw_cases) == 96,
            "capability evidence does not expose the exact 96 raw case witnesses")
    for case_id, ref in sorted(raw_cases.items()):
        add(ref, f"raw capability witness {case_id}")
    require(set(result).isdisjoint(base_inputs),
            "fresh source closure unexpectedly repeats an inherited source input")
    return result


def _validate_source_closure(root: Path, base: dict[str, Any], contract: dict[str, Any],
                             manifest: dict[str, Any]) -> None:
    """Require the complete, explicitly enumerated source-input closure.

    The frozen validator has already checked the base list at the base source
    commit.  This continuation additionally binds every newly admitted path to
    the registered source commit; this is what prevents a manifest from naming
    arbitrary evidence files after the source snapshot was reviewed.
    """
    old_inputs = _source_input_map(base.get("source_inputs"), "base source inputs")
    new_inputs = _source_input_map(contract.get("source_inputs"), "continuation source inputs")
    require(old_inputs and all(new_inputs.get(path) == binding
                               for path, binding in old_inputs.items()),
            "continuation source closure removed, changed, or stripped frozen input metadata")
    # The reviewed builder keeps role-bearing metadata only on inherited
    # entries; newly added source files are represented by the explicit
    # path/SHA delta and therefore carry no unbound role field.
    require(all(new_inputs[path][1] is None for path in set(new_inputs) - set(old_inputs)),
            "continuation source closure added unbound role metadata")
    old_digests = {path: binding[0] for path, binding in old_inputs.items()}
    new_digests = {path: binding[0] for path, binding in new_inputs.items()}
    delta = {item["path"]: item["sha256"] for item in manifest["source_inputs_delta"]}
    require(set(delta).isdisjoint(old_digests),
            "continuation source-input delta repeats an inherited input")
    require(new_digests == {**old_digests, **delta},
            "continuation source-input closure differs from its explicit manifest delta")
    evidence = _json(root, manifest["artifacts"]["capability_evidence"]["path"],
                     "capability evidence")
    repaired_plan = _json(root, manifest["artifacts"]["repaired_plan"]["path"],
                          "repaired execution plan")
    expected_delta = _fresh_control_source_closure(root, manifest, repaired_plan,
                                                    evidence, old_digests)
    require(delta == expected_delta,
            "continuation source-input delta differs from the deterministic fresh-control closure")
    raw_cases = evidence.get("historical_raw_evidence", {}).get("case_reports", {})
    require(isinstance(raw_cases, dict) and len(raw_cases) == 96,
            "capability evidence does not expose the exact 96 raw case witnesses")
    for case_id, ref in raw_cases.items():
        require(isinstance(ref, dict) and isinstance(ref.get("path"), str) and
                RE_SHA.fullmatch(str(ref.get("sha256", ""))),
                f"raw capability witness is malformed: {case_id}")
        require(new_digests.get(ref["path"]) == ref["sha256"],
                f"raw capability witness is absent from the committed source closure: {case_id}")
    require(len({ref["path"] for ref in raw_cases.values()}) == 96,
            "capability witnesses do not identify 96 distinct raw files")
    # Verify the manifest delta both in the checkout and at the immutable
    # source commit.  The source-input list is consumed by the frozen runner,
    # so a path that only exists in the working tree is not admissible.
    for path, digest in delta.items():
        current = _read(root, path)
        require(sha_bytes(current) == digest, f"continuation source input changed: {path}")
    # Every path consumed by the frozen runner must resolve to the registered
    # source commit.  Checking only the additive delta would leave inherited
    # paths dependent on the caller's working tree and would not prove the
    # complete continuation closure.
    _verify_commit_blobs(root, manifest["source_commit"], new_digests,
                         "continuation source-input closure")


def _historical_contexts(base: dict[str, Any], rows: list[dict[str, Any]],
                        raw: bytes, base_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Retain every predecessor context supplied by the frozen C4 packet."""
    recovery = base.get("resource_recovery")
    require(isinstance(recovery, dict) and isinstance(recovery.get("contexts"), dict),
            "frozen resource-recovery context closure is missing")
    contexts = copy.deepcopy(recovery["contexts"])
    contexts[BASE_SHA] = base_context
    expected_contexts = {row.get("contract_sha256") for row in rows[:SEALED_ROWS]}
    require(all(isinstance(value, str) and RE_SHA.fullmatch(value)
                for value in expected_contexts),
            "historical row has a malformed contract context digest")
    require(set(contexts) == expected_contexts,
            "historical context closure differs from the sealed ledger contract roster")
    line_hashes = [sha_bytes(line) for line in raw.splitlines(keepends=True)]
    retained_completed: dict[str, dict[str, Any]] = {}
    retained_failures: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        key = row.get("contract_sha256")
        origin = contexts.get(key)
        require(isinstance(origin, dict) and isinstance(origin.get("validated"), dict),
                f"historical row lacks its original contract context: {row.get('attempt_id')}")
        validated = origin["validated"]
        require(validated.get("bytes_sha256") == key and
                isinstance(origin.get("plan_commit"), str) and
                RE_COMMIT.fullmatch(origin["plan_commit"]),
                f"historical row context binding is malformed: {row.get('attempt_id')}")
        require(row.get("source_commit") == validated.get("plan", {}).get("source_commit") and
                row.get("plan_commit") == origin.get("plan_commit"),
                f"historical row source/plan context changed: {row.get('attempt_id')}")
        group_ids = [group.get("id") for group in validated.get("plan", {}).get("groups", [])
                     if isinstance(group, dict)]
        require(row.get("group_id") in group_ids,
                f"historical row group is absent from its original context: {row.get('attempt_id')}")
        number_match = re.search(r"-attempt-(\d+)-series-", str(row.get("attempt_id")))
        require(number_match is not None, f"historical attempt number missing: {row.get('attempt_id')}")
        record = {"row": row, "ledger_line_sha256": line_hashes[index],
                  "context_sha256": key, "plan_commit": origin["plan_commit"],
                  "attempt_number": int(number_match.group(1))}
        if row.get("status") == "completed":
            retained_completed[row["group_id"]] = record
        else:
            retained_failures[row["attempt_id"]] = record
    require(len(retained_completed) == 82 and len(retained_failures) == 4,
            "historical retained completion/failure slots changed")
    recovery["contexts"] = contexts
    recovery["retained_completed"] = retained_completed
    recovery["retained_failures"] = retained_failures
    base["resource_recovery"] = recovery
    return contexts


def _invoke_repair_shim(root: Path, manifest: dict[str, Any]) -> None:
    """Require the separately owned shim to approve the repaired projection."""
    relative = manifest["artifacts"]["joern_shim"]["path"]
    spec = importlib.util.spec_from_file_location("joern_capability_repair_continuation_shim", root / Path(*_relative(relative).parts))
    require(spec is not None and spec.loader is not None, "cannot import Joern repair shim")
    shim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim)
    validator = getattr(shim, "validate_repair_inputs", None)
    require(callable(validator), "Joern repair shim lacks validate_repair_inputs")
    validator(root, new_plan_path=manifest["artifacts"]["repaired_plan"]["path"],
              evidence_path=manifest["artifacts"]["capability_evidence"]["path"],
              expected_new_plan_sha256=manifest["artifacts"]["repaired_plan"]["sha256"],
              expected_evidence_sha256=manifest["artifacts"]["capability_evidence"]["sha256"])


def validate(root: Path = ROOT, manifest_path: str = DEFAULT_MANIFEST,
             manifest_sha: str | None = None, *, require_admission: bool = False) -> dict[str, Any]:
    """Validate frozen history and return old/new execution contexts."""
    root = Path(root).resolve()
    manifest_raw = _read(root, manifest_path)
    digest = sha_bytes(manifest_raw)
    require(manifest_sha is not None, "manifest SHA is required; prospective manifests are not executable")
    manifest = _load_manifest(root, manifest_path, manifest_sha,
                              require_admission=require_admission)
    raw, rows = _ledger(root)
    prefix = _check_prefix(root, rows, raw)
    _tail(rows, final=False)
    require(sha(_read_path(root, BASE_CONTRACT)) == BASE_SHA, "base contract changed")
    executor = _load_frozen(root, "execute")
    checker = _load_frozen(root, "checker")
    config_checker = _load_frozen(root, "configuration")
    base = executor.validate_plan(root / Path(*_relative(BASE_CONTRACT).parts), repo_root=root)
    require(base.get("bytes_sha256") == BASE_SHA, "frozen validator returned a different base contract")
    # The historical plan bytes stay untouched, while the checker/executor
    # context carries the original release window through this continuation.
    # This is a derived in-memory field; it never changes the frozen contract.
    base["total_wall_budget_seconds"] = TOTAL_WALL_SECONDS
    base_context = {"validated": base, "plan_commit": BASE_PLAN_COMMIT}
    contexts = _historical_contexts(base, rows, raw, base_context)
    contract_ref = manifest["continuation_contract"]
    contract_raw = _binding(root, contract_ref, "continuation contract")
    try:
        contract = json.loads(contract_raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContinuationError("continuation contract is not valid JSON") from exc
    require(isinstance(contract, dict), "continuation contract must be an object")
    repaired_plan = _raw_plan_delta(root, manifest)
    _invoke_repair_shim(root, manifest)
    _validate_source_closure(root, base, contract, manifest)
    new = _derive_context(base, contract, contract_raw, manifest, repaired_plan, executor)
    new_sha = sha_bytes(contract_raw)
    contexts[new_sha] = {"validated": new, "plan_commit": manifest["plan_commit"]}
    new_recovery = copy.deepcopy(base.get("resource_recovery", {}))
    new_recovery["contexts"] = contexts
    # Keep the exact retained maps produced from the frozen C4 packet.  The
    # new context is deliberately not inserted into a historical completion
    # slot until its Joern03 receipt exists.
    new_recovery["retained_completed"] = copy.deepcopy(
        base["resource_recovery"]["retained_completed"]
    )
    new_recovery["retained_failures"] = copy.deepcopy(
        base["resource_recovery"]["retained_failures"]
    )
    new["resource_recovery"] = new_recovery
    _validate_tail_identity(
        {"manifest": manifest, "base": base_context,
         "repaired": contexts[new_sha]},
        _tail(rows, final=False),
    )
    return {"root": root, "manifest": manifest, "manifest_sha256": digest,
            "executor": executor, "checker": checker, "configuration": config_checker,
            "prefix": prefix, "rows": rows, "contexts": contexts,
            "base": base_context, "repaired": contexts[sha_bytes(contract_raw)],
            "joern_plan": repaired_plan}


def _context_for_row(context: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    contract_sha = row.get("contract_sha256")
    require(contract_sha in context["contexts"], "ledger row has an unregistered contract context")
    origin = context["contexts"][contract_sha]
    if row["group_id"] == JOERN_GROUP:
        if row.get("attempt_id") == JOERN_ATTEMPT:
            require(contract_sha == context["repaired"]["validated"]["bytes_sha256"],
                    "Joern03 is not bound to the repaired continuation context")
        else:
            require(contract_sha == BASE_SHA and row.get("attempt_id") in {
                "joern-swift-common108-attempt-01-series-01",
                "joern-swift-common108-attempt-02-series-01",
            }, "historical Joern row changed context")
    elif row["group_id"] == CODEQL_GROUP:
        require(contract_sha == context["repaired"]["validated"]["bytes_sha256"] and
                row.get("attempt_id") == CODEQL_ATTEMPT,
                "CodeQL continuation row is not bound to the new execution context")
    return origin


def _selected(rows: list[dict[str, Any]], final: bool) -> dict[str, dict[str, Any]]:
    tail = _tail(rows, final=final)
    selected = {row["group_id"]: row for row in rows[:SEALED_ROWS]
                if row.get("status") == "completed"}
    require(len(selected) == 82, "historical selected completion count changed")
    if final:
        for row in tail:
            require(row.get("status") == "completed" and row.get("exit_code") == 0,
                    "failed continuation cannot be selected")
            selected[row["group_id"]] = row
        require(len(selected) == 84, "final selected group count must be 84")
    return selected


def _validate_tail_identity(context: dict[str, Any], tail: list[dict[str, Any]]) -> None:
    """Check durable continuation rows against their exact source contexts."""
    manifest = context["manifest"]
    base_plan = context["base"]["validated"]["plan"]
    base_group = next(group for group in base_plan["groups"] if group.get("id") == CODEQL_GROUP)
    continuation_sha = context["repaired"]["validated"]["bytes_sha256"]
    for row in tail:
        require(row.get("fixture_revision") == manifest["fixture_revision"],
                f"{row.get('attempt_id')} fixture identity changed")
        if row.get("group_id") == JOERN_GROUP:
            require(row.get("contract_sha256") == continuation_sha and
                    row.get("source_commit") == manifest["source_commit"] and
                    row.get("plan_commit") == manifest["plan_commit"] and
                    row.get("argv") == manifest["joern"]["argv"] and
                    row.get("output_roots") == [manifest["joern"]["output_root"]],
                    "Joern03 durable row changed its reviewed source/plan/command identity")
        elif row.get("group_id") == CODEQL_GROUP:
            require(row.get("contract_sha256") == continuation_sha and
                    row.get("source_commit") == manifest["source_commit"] and
                    row.get("plan_commit") == manifest["plan_commit"] and
                    row.get("argv") == manifest["codeql"]["argv"] and
                    row.get("output_roots") == base_group.get("output_roots"),
                    "CodeQL01 durable row changed its continuation source/plan/command identity")


@contextlib.contextmanager
def _original_clock(executor: Any, validated: dict[str, Any]):
    old = getattr(executor, "_matrix_elapsed_wall", None)
    require(callable(old), "frozen executor does not expose its original wall-clock guard")
    def elapsed(current: dict[str, Any], *, now_seconds: float | None = None) -> float:
        require(current is validated, "unexpected execution clock context")
        now = time.time() if now_seconds is None else now_seconds
        result = now - dt.datetime.fromisoformat(ORIGIN).timestamp()
        require(result >= 0 and result <= TOTAL_WALL_SECONDS, "continuation is outside the original clock")
        return result
    executor._matrix_elapsed_wall = elapsed
    try:
        yield
    finally:
        executor._matrix_elapsed_wall = old


def _runtime_plan_with_cutoff_reservation(validated: dict[str, Any]) -> dict[str, Any]:
    """Overlay only the live reservation expiry on an immutable validated plan.

    The committed continuation contract retains the original reservation
    bytes, whose historical expiry is already past while this resumed matrix is
    being completed.  The frozen runner requires a live expiry at dispatch;
    this derived runtime view changes only that one in-memory field and leaves
    the contract/source/plan identities and the original wall-clock guard
    untouched.
    """
    plan = validated.get("plan")
    require(isinstance(plan, dict) and isinstance(plan.get("resource_reservation"), dict),
            "continuation plan lacks a resource reservation")
    reservation = plan["resource_reservation"]
    runtime = dict(validated)
    runtime["plan"] = dict(plan)
    runtime["plan"]["resource_reservation"] = dict(reservation)
    expiry = dt.datetime.fromisoformat(CUTOFF).timestamp()
    runtime["plan"]["resource_reservation"]["expires_at_unix_seconds"] = expiry
    require(runtime["plan"]["resource_reservation"] != reservation and
            all(runtime["plan"]["resource_reservation"].get(key) == value
                for key, value in reservation.items()
                if key != "expires_at_unix_seconds"),
            "runtime reservation overlay changed fields beyond expiry")
    return runtime


def _require_live_execution_gates(context: dict[str, Any], group_id: str) -> None:
    """Recheck the live capacity and original-clock reserve before dispatch."""
    require(group_id in {JOERN_GROUP, CODEQL_GROUP}, "unknown continuation group")
    admission = context["manifest"].get("execution_admission")
    require(isinstance(admission, dict), "execution admission is missing before live dispatch")
    # The receipt's phase map is an admission lower bound; this live check
    # prevents a stale receipt from authorizing dispatch after the original
    # cutoff window can no longer fit the reviewed phase reserve.
    phase_reserve = admission.get("phase_remaining_reserved_seconds")
    required = (FULL_REMAINING_RESERVE_SECONDS if group_id == JOERN_GROUP
                else CODEQL_PHASE_REMAINING_RESERVE_SECONDS)
    require(isinstance(phase_reserve, dict) and
            type(phase_reserve.get(group_id)) is int and
            phase_reserve[group_id] >= required,
            "live phase reserve is absent or below the reviewed floor")
    remaining = dt.datetime.fromisoformat(CUTOFF).timestamp() - time.time()
    require(remaining >= required,
            f"original cutoff no longer leaves the reviewed {required}s phase reserve")
    checker = getattr(context["executor"], "_check_resources", None)
    require(callable(checker), "frozen executor does not expose its resource gate")
    try:
        checker(context["root"], LIVE_RESOURCE_FLOOR_BYTES)
    except Exception as exc:
        raise ContinuationError(f"live 127 GiB resource admission failed: {exc}") from exc


def _require_execution_success(group_id: str, result: object) -> dict[str, Any]:
    """Turn a frozen runner's failed row into a nonzero continuation result."""
    expected_attempt = JOERN_ATTEMPT if group_id == JOERN_GROUP else CODEQL_ATTEMPT
    require(isinstance(result, dict) and result.get("group_id") == group_id and
            result.get("attempt_id") == expected_attempt and
            result.get("status") == "completed" and result.get("exit_code") == 0 and
            result.get("timed_out") is False and result.get("capacity_loss") is None,
            f"{group_id} continuation execution did not complete successfully")
    return result


def execute(context: dict[str, Any], group_id: str) -> dict[str, Any]:
    """Dispatch exactly the next continuation row through frozen run_group."""
    require(group_id in {JOERN_GROUP, CODEQL_GROUP}, "only Joern03 or CodeQL01 may execute")
    _check_execution_admission(
        context["root"], context["manifest"].get("execution_admission"),
        context["manifest"], group_id=group_id,
    )
    require(_git(context["root"], "rev-parse", "HEAD") == context["manifest"]["plan_commit"],
            "execution requires the exact registered plan commit")
    # A direct execute invocation must still replay the sealed history and any
    # already-produced continuation row.  The parent launcher adds its own
    # resource/sidecar reservation receipt; this replay gate prevents an
    # unreviewed direct call from bypassing the immutable evidence checker.
    verify(context, final=False)
    raw, rows = _ledger(context["root"])
    _check_prefix(context["root"], rows, raw)
    tail = _tail(rows, final=False)
    _validate_tail_identity(context, tail)
    if not tail:
        require(group_id == JOERN_GROUP, "Joern03 must precede CodeQL01")
    else:
        require(len(tail) == 1 and tail[0].get("status") == "completed" and
                tail[0].get("attempt_id") == JOERN_ATTEMPT and group_id == CODEQL_GROUP,
                "continuation order or Joern terminal state is invalid")
    _require_live_execution_gates(context, group_id)
    origin = context["repaired"]
    runtime = _runtime_plan_with_cutoff_reservation(origin["validated"])
    with _original_clock(context["executor"], runtime):
        result = context["executor"].run_group(runtime, group_id)
    return _require_execution_success(group_id, result)


def verify(context: dict[str, Any], final: bool = True) -> dict[str, Any]:
    """Replay each row in its original contract/source context."""
    if final:
        # Final replay is a post-admission operation.  Read-only preparation
        # uses final=False and is intentionally allowed before the one-shot
        # launcher receipt exists.
        _check_execution_admission(context["root"],
                                   context["manifest"].get("execution_admission"),
                                   context["manifest"])
    raw, rows = _ledger(context["root"])
    _check_prefix(context["root"], rows, raw)
    _validate_tail_identity(context, _tail(rows, final=final))
    selected = _selected(rows, final)
    line_hashes = {row["attempt_id"]: sha_bytes(line)
                   for row, line in zip(rows, raw.splitlines(keepends=True))}
    reports: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    outcomes: collections.Counter[str] = collections.Counter()
    for row in rows:
        origin = _context_for_row(context, row)
        validator = context["executor"]
        group = validator._historical_group_for_replay(origin["validated"], row)
        match = re.fullmatch(re.escape(row["group_id"]) + r"-attempt-(\d+)-series-\d+", row["attempt_id"])
        require(match is not None, f"malformed attempt id: {row.get('attempt_id')}")
        number = int(match.group(1))
        if row.get("status") == "completed":
            bindings, counts = context["checker"]._verify_one_group(
                context["root"], origin["validated"], group, row, origin["plan_commit"], number
            )
            if selected.get(row["group_id"], {}).get("attempt_id") == row["attempt_id"]:
                outcomes.update(counts)
                for binding in bindings:
                    binding.update(attempt_id=row["attempt_id"],
                                   attempt_number=number,
                                   evidence_contract_sha256=row["contract_sha256"])
                reports.extend(bindings)
        else:
            receipt_path = f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json"
            failures.append(context["checker"]._verify_failed_attempt(
                context["root"], origin["validated"], group, row, origin["plan_commit"], number,
                line_hashes[row["attempt_id"]], sha(_read_path(context["root"], receipt_path))
            ))
    require(not any(count for key, count in outcomes.items() if "stale" in key.lower()),
            "final selected reports contain stale outcomes")
    if final:
        require(len(reports) == 92 and sum(item.get("rows", 0) for item in reports) == 4252,
                "final report denominator changed")
    selected_attempts = []
    for row in selected.values():
        receipt_path = f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json"
        selected_attempts.append({
            "group_id": row["group_id"], "attempt_id": row["attempt_id"],
            "status": "completed", "evidence_contract_sha256": row["contract_sha256"],
            "evidence_plan_commit": context["contexts"][row["contract_sha256"]]["plan_commit"],
            "completed_receipt_sha256": sha(_read_path(context["root"], receipt_path)),
        })
    return {"status": "fresh-evidence-verified" if final else "continuation-preflight-passed",
            "ledger_rows": len(rows), "selected_groups": len(selected),
            "partitions": len(reports), "rows": sum(item.get("rows", 0) for item in reports),
            "known_stale": 0, "selected_attempts": selected_attempts,
            "failed_attempts": failures, "fresh_reports": reports}


def config(context: dict[str, Any], output: str) -> dict[str, Any]:
    """Run the frozen report configuration checker under each selected context."""
    summary = verify(context, final=True)
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", output) is not None,
            "configuration namespace is unsafe")
    directory = context["root"] / "reports/releases/v0.9.2/validation" / output
    require(not directory.exists() and not directory.is_symlink(), "configuration namespace exists")
    directory.mkdir(parents=True)
    helper = context["configuration"]
    buckets: dict[str, list[str]] = collections.defaultdict(list)
    for attempt in summary["selected_attempts"]:
        row = next(row for row in context["rows"] if row["attempt_id"] == attempt["attempt_id"])
        buckets[row["contract_sha256"]].append(attempt["attempt_id"])
    results = []
    for index, (contract_sha, attempt_ids) in enumerate(sorted(buckets.items())):
        origin = context["contexts"][contract_sha]
        checkout = context["root"] / "execution-state/v092/validation" / f"joern-capability-continuation-01-{index:02d}"
        require(not checkout.exists() and not checkout.is_symlink(), "configuration checkout exists")
        subset = dict(summary)
        subset["fresh_reports"] = [item for item in summary.get("fresh_reports", [])
                                    if item.get("attempt_id") in attempt_ids]
        subset["selected_attempts"] = [item for item in summary.get("selected_attempts", [])
                                        if item.get("attempt_id") in attempt_ids]
        partition_count = len(subset["fresh_reports"])
        row_count = sum(item.get("rows", 0) for item in subset["fresh_reports"])
        context["executor"]._materialize_source(
            context["root"], origin["validated"]["plan"]["source_commit"], checkout,
            [item["path"] for item in origin["validated"]["source_inputs"]]
        )
        helper._project_reports(context["root"], checkout, subset,
                                expected_report_count=partition_count,
                                expected_row_count=row_count)
        environment = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(checkout),
            "TMPDIR": str(checkout), "LANG": "C", "LC_ALL": "C", "NO_COLOR": "1",
        }
        invocation = helper._invoke_runner(origin["validated"]["tools"]["runner"], checkout, environment)
        (directory / f"{index:02d}-stdout.bin").write_bytes(invocation["stdout"])
        (directory / f"{index:02d}-stderr.bin").write_bytes(invocation["stderr"])
        metrics = helper._parse_stdout(invocation["stdout"])
        require(helper._validation_success(invocation["exit_code"], metrics, partition_count),
                "per-context configuration validation failed")
        results.append({"contract_sha256": contract_sha, "attempt_ids": attempt_ids,
                        "partitions": partition_count, "rows": row_count,
                        "metrics": metrics})
    result = {"status": "canonical-validation-passed", "partitions": sum(x["partitions"] for x in results),
              "rows": sum(x["rows"] for x in results),
              "known_stale": sum(x["metrics"].get("known_stale", 0) for x in results), "contexts": results}
    require(result["partitions"] == 92 and result["rows"] == 4252, "configuration denominator changed")
    _write_new(directory / "receipt.json", result)
    return result


def _read_path(root: Path, value: str) -> Path:
    path = root / Path(*_relative(value).parts)
    require(path.is_file() and not path.is_symlink(), f"missing path: {value}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "validate", "execute", "verify", "config"))
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--group")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        context = validate(
            ROOT, args.manifest, args.manifest_sha256,
            require_admission=args.command in {"execute", "verify", "config"},
        )
        if args.command in {"preflight", "validate"}:
            result = verify(context, final=False)
        elif args.command == "execute":
            require(args.group is not None, "execute requires --group")
            result = execute(context, args.group)
        elif args.command == "verify":
            result = verify(context, final=True)
        else:
            require(args.output is not None, "config requires --output")
            result = config(context, args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except ContinuationError as exc:
        print(f"continuation rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
