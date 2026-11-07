#!/usr/bin/env python3
"""Hydrate the exact retained Swift hash inputs before canonical validation.

This postmeasurement helper leaves the original failed namespace and all
benchmark/source evidence untouched. It delegates the actual validation to
the pinned canonical helper and intercepts only the point immediately before
that helper invokes its unchanged Rust runner.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
from types import ModuleType
from typing import Callable


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = EVIDENCE_DIR / "swift-configuration-ref-manifest.json"
DIAGNOSIS_PATH = EVIDENCE_DIR / "repair-diagnosis.json"
CANONICAL_VALIDATOR = PurePosixPath("scripts/validate-v092-report-configurations.py")
RUN_NAMESPACE = "bifrost-v0151-configurations-02"
SOURCE_COMMIT = "7f99684668065b8fb1ebc9b2852f058c64430647"
SOURCE_TREE_SHA1 = "7af8853a1e2eb7ea7832f7c0bad4d2299c1ab416"
LOCKED_MANIFEST_SHA256 = "65120d4a6d0fdbc092c57ecae03b1969c733814be12f5a6952600ea408a24781"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_BLOB_RE = re.compile(r"[0-9a-f]{40}\Z")


class MaterializationError(ValueError):
    """A locked source or destination input failed verification."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MaterializationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _utc_now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _relative_path(value: object, description: str) -> PurePosixPath:
    _require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value,
             f"{description} must be a non-empty canonical relative POSIX path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and path.as_posix() == value and
             all(part not in ("", ".", "..") for part in path.parts),
             f"{description} is absolute, non-canonical, or escapes its root: {value!r}")
    return path


def _guard_directory_root(path: Path, description: str) -> Path:
    raw = Path(os.path.abspath(os.fspath(path)))
    current = Path(raw.anchor)
    for part in raw.parts[1:]:
        current = current / part
        _require(not current.is_symlink(), f"symlink in {description}: {current}")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise MaterializationError(f"{description} is missing: {raw}") from exc
    _require(resolved.is_dir(), f"{description} is not a directory: {resolved}")
    return resolved


def _safe_regular_file(root: Path, relative: object, description: str) -> tuple[Path, bytes]:
    root = _guard_directory_root(root, f"{description} root")
    path = _relative_path(relative, description)
    current = root
    for part in path.parts:
        current = current / part
        _require(not current.is_symlink(), f"symlink in {description}: {current}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise MaterializationError(f"{description} is missing or escapes its root: {path}") from exc
    _require(resolved.is_file() and not stat.S_ISLNK(resolved.lstat().st_mode),
             f"{description} is not a regular non-symlink file: {path}")
    try:
        return resolved, resolved.read_bytes()
    except OSError as exc:
        raise MaterializationError(f"cannot read {description}: {path}: {exc}") from exc


def _destination_path(root: Path, relative: object, *, create_parents: bool = False) -> Path:
    root = _guard_directory_root(root, "destination input root")
    path = _relative_path(relative, "destination input path")
    current = root
    for part in path.parts[:-1]:
        current = current / part
        _require(not current.is_symlink(), f"symlink in destination input path: {current}")
        if current.exists():
            _require(current.is_dir(), f"destination input parent is not a directory: {current}")
        elif create_parents:
            try:
                current.mkdir()
            except OSError as exc:
                raise MaterializationError(f"cannot create destination parent {current}: {exc}") from exc
    target = current / path.name
    _require(not target.is_symlink(), f"symlink at destination input path: {target}")
    try:
        target.parent.resolve(strict=create_parents).relative_to(root)
    except (OSError, ValueError) as exc:
        raise MaterializationError(f"destination input path escapes its checkout: {path}") from exc
    return target


def _git_text(root: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *arguments], cwd=root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise MaterializationError(f"cannot verify pinned Git provenance: git {' '.join(arguments)}") from exc


def _git_blob(root: Path, source_commit: str, relative: str) -> tuple[str, bytes]:
    blob_id = _git_text(root, "rev-parse", f"{source_commit}:{relative}")
    _require(GIT_BLOB_RE.fullmatch(blob_id) is not None,
             f"pinned Git source is not a regular blob: {relative}")
    try:
        data = subprocess.check_output(
            ["git", "cat-file", "blob", blob_id], cwd=root, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise MaterializationError(f"cannot read pinned Git blob for {relative}") from exc
    return blob_id, data


def _validate_reference_roster(references: object, supplement_paths: object) -> tuple[list[dict], set[str]]:
    _require(isinstance(references, list) and references,
             "locked Swift configuration reference roster must be a non-empty list")
    by_path: dict[str, dict] = {}
    for item in references:
        _require(isinstance(item, dict), "locked Swift configuration reference is malformed")
        path = _relative_path(item.get("path"), "locked Swift configuration reference").as_posix()
        digest = item.get("sha256")
        blob_id = item.get("git_blob_sha1")
        engines = item.get("engines")
        initial_state = item.get("initial_failed_checkout_state")
        _require(isinstance(digest, str) and SHA256_RE.fullmatch(digest) is not None,
                 f"locked SHA-256 is malformed for {path}")
        _require(isinstance(blob_id, str) and GIT_BLOB_RE.fullmatch(blob_id) is not None,
                 f"locked Git blob id is malformed for {path}")
        _require(isinstance(engines, list) and engines and
                 engines == sorted(set(engines)) and set(engines) <= {"codeql", "joern"},
                 f"locked engine roster is malformed for {path}")
        _require(initial_state in ("present", "supplement"),
                 f"locked initial checkout state is malformed for {path}")
        _require(path not in by_path, f"duplicate locked Swift configuration path: {path}")
        by_path[path] = item

    normalized = [by_path[path] for path in sorted(by_path)]
    _require(normalized == references, "locked Swift configuration roster is not canonical path order")
    _require(isinstance(supplement_paths, list) and
             all(isinstance(path, str) for path in supplement_paths) and
             supplement_paths == sorted(set(supplement_paths)),
             "locked supplement path roster is malformed or unordered")
    supplement_set = set(supplement_paths)
    expected_supplements = {
        path for path, item in by_path.items()
        if item["initial_failed_checkout_state"] == "supplement"
    }
    _require(supplement_set == expected_supplements,
             "supplement paths differ from the locked initially-missing reference roster")
    return normalized, supplement_set


def _verify_plan_bindings(root: Path, manifest: dict, *, checkout: Path | None = None) -> None:
    plan_bindings = manifest.get("plans")
    _require(isinstance(plan_bindings, dict) and set(plan_bindings) == {"codeql", "joern"},
             "manifest must bind exactly the CodeQL and Joern Swift execution plans")
    reference_index = {
        item["path"]: {"sha256": item["sha256"], "engines": set(item["engines"])}
        for item in manifest["references"]
    }
    found_by_path: dict[str, dict] = {}
    expected_plan_contracts = {
        "codeql": {
            "path": "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json",
            "configuration_key": "patched-codeql",
            "schema": "swift-common-execution-plan/v092",
            "tool": "codeql",
            "tool_version": "2.27.2",
            "adapter_version": "swift-normal-v092",
        },
        "joern": {
            "path": "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
            "configuration_key": "joern-current108",
            "schema": "joern-common-execution-plan/v092",
            "tool": "joern",
            "tool_version": "4.0.660",
            "adapter_version": "joern-normal-v092",
        },
    }
    for engine, expected in expected_plan_contracts.items():
        binding = plan_bindings[engine]
        _require(isinstance(binding, dict) and
                 binding.get("path") == expected["path"] and
                 binding.get("configuration_key") == expected["configuration_key"],
                 f"{engine} execution-plan binding differs from the fixed Swift closure")
        raw, data = _safe_regular_file(root, binding["path"], f"root {engine} Swift execution plan")
        digest = _sha(data)
        _require(digest == binding.get("sha256"), f"root {engine} Swift execution plan hash changed")
        blob_id, blob_data = _git_blob(root, manifest["source_commit"], binding["path"])
        _require(blob_id == binding.get("git_blob_sha1") and _sha(blob_data) == digest and blob_data == data,
                 f"root {engine} Swift execution plan is not the pinned source-commit file")
        if checkout is not None:
            _, checkout_data = _safe_regular_file(checkout, binding["path"],
                                                  f"checkout {engine} Swift execution plan")
            _require(_sha(checkout_data) == digest and checkout_data == data,
                     f"materialized {engine} Swift execution plan differs from its locked source bytes")
        try:
            plan = json.loads(data)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise MaterializationError(f"{engine} Swift execution plan is invalid JSON") from exc
        _require(isinstance(plan, dict) and plan.get("schema") == expected["schema"] and
                 plan.get("profile") == "v0.9.2" and isinstance(plan.get("identity"), dict),
                 f"{engine} Swift execution plan schema/profile changed")
        identity = plan["identity"]
        _require(identity.get("tool") == expected["tool"] and
                 identity.get("tool_version") == expected["tool_version"] and
                 identity.get("adapter_version") == expected["adapter_version"],
                 f"{engine} Swift execution plan tool identity changed")
        _require(binding.get("identity") == identity,
                 f"{engine} Swift execution plan identity differs from its lock")
        configs = plan.get("configurations")
        refs = configs.get(expected["configuration_key"]) if isinstance(configs, dict) else None
        _require(isinstance(refs, list) and len(refs) == binding.get("reference_count"),
                 f"{engine} Swift execution plan reference count changed")
        seen: set[str] = set()
        for reference in refs:
            _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
                     f"{engine} Swift execution plan reference is malformed")
            relative = _relative_path(reference.get("path"), f"{engine} plan reference").as_posix()
            _require(relative not in seen, f"{engine} Swift plan repeats an input path: {relative}")
            seen.add(relative)
            prior = found_by_path.get(relative)
            if prior is None:
                found_by_path[relative] = {"sha256": reference["sha256"], "engines": {engine}}
            else:
                _require(prior["sha256"] == reference["sha256"],
                         f"CodeQL and Joern bind conflicting hashes for {relative}")
                prior["engines"].add(engine)

    _require(set(found_by_path) == set(reference_index),
             "execution plans differ from the locked union of Swift configuration references")
    for path, actual in found_by_path.items():
        expected = reference_index[path]
        _require(actual["sha256"] == expected["sha256"] and actual["engines"] == expected["engines"],
                 f"execution-plan reference differs from the lock: {path}")


def verify_locked_source(root: Path, manifest: dict) -> None:
    _require(manifest.get("schema") == "v0.9.2-v0151-swift-configuration-ref-manifest/v1",
             "unknown Swift configuration repair manifest schema")
    _require(manifest.get("source_commit") == SOURCE_COMMIT and
             manifest.get("source_tree_sha1") == SOURCE_TREE_SHA1,
             "manifest source commit/tree differs from the fixed C6 source")
    tree = _git_text(root, "rev-parse", f"{SOURCE_COMMIT}^{{tree}}")
    _require(tree == SOURCE_TREE_SHA1, "fixed C6 source tree SHA-1 is unavailable or changed")
    references, supplements = _validate_reference_roster(
        manifest.get("references"), manifest.get("supplement_paths"),
    )
    counts = manifest.get("counts")
    _require(counts == {
        "codeql_plan_references": 99,
        "joern_plan_references": 33,
        "unique_references": 119,
        "common_references": 13,
        "initially_present_references": 97,
        "supplement_references": 22,
    }, "locked Swift configuration closure counts changed")
    _require(len(references) == counts["unique_references"] and len(supplements) == 22,
             "locked Swift configuration closure cardinality changed")
    _verify_plan_bindings(root, manifest)
    for item in references:
        relative = item["path"]
        _, source_data = _safe_regular_file(root, relative, "locked source configuration input")
        _require(_sha(source_data) == item["sha256"],
                 f"root source configuration input differs from locked SHA-256: {relative}")
        blob_id, blob_data = _git_blob(root, SOURCE_COMMIT, relative)
        _require(blob_id == item["git_blob_sha1"] and _sha(blob_data) == item["sha256"] and
                 blob_data == source_data,
                 f"root source input differs from pinned Git blob and plan SHA: {relative}")


def verify_failed_checkout(root: Path, manifest: dict) -> dict:
    """Confirm the original failure was limited to the locked sparse checkout."""
    failed = manifest.get("failed_validation")
    _require(isinstance(failed, dict), "manifest lacks the original failed-validation binding")
    checkout_relative = _relative_path(failed.get("checkout_relative"), "failed validation checkout")
    _verify_failed_receipt(root, failed)
    checkout = _guard_directory_root(root.joinpath(*checkout_relative.parts),
                                     "original failed validation checkout")
    absent: list[str] = []
    present_count = 0
    for item in manifest["references"]:
        target = _destination_path(checkout, item["path"])
        if target.is_symlink():
            raise MaterializationError(f"symlink at original validation input: {item['path']}")
        if not target.exists():
            absent.append(item["path"])
            continue
        _require(target.is_file(), f"original validation input is not a regular file: {item['path']}")
        _require(_sha(target.read_bytes()) == item["sha256"],
                 f"original validation input differs from its locked SHA: {item['path']}")
        present_count += 1
    _require(sorted(absent) == manifest["supplement_paths"],
             "original failed checkout's missing Swift inputs differ from the exact supplement list")
    return {"present": present_count, "missing": len(absent), "missing_paths": sorted(absent),
            "receipt_sha256": failed["receipt_sha256"]}


def _verify_failed_receipt(root: Path, failed: dict) -> dict:
    expected_receipt = "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-01/receipt.json"
    expected_checkout = "execution-state/v092/validation/bifrost-v0151-configurations-01"
    _require(failed.get("receipt_path") == expected_receipt and
             failed.get("checkout_relative") == expected_checkout,
             "original failed validation receipt or checkout path differs from the fixed namespace")
    _, raw = _safe_regular_file(root, expected_receipt, "original failed validation receipt")
    digest = _sha(raw)
    _require(digest == failed.get("receipt_sha256"),
             "original failed validation receipt bytes differ from their locked SHA-256")
    try:
        receipt = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MaterializationError("original failed validation receipt is invalid JSON") from exc
    for key in ("status", "exit_code", "command", "cwd", "runner", "source_identity", "checker_summary"):
        _require(receipt.get(key) == failed.get(key),
                 f"original failed validation receipt differs from its locked {key} binding")
    _require(receipt.get("status") == "failed" and receipt.get("exit_code") == 1 and
             receipt.get("command") == [failed["runner"]["path"], "--population", "v0.9.0", "validate-reports"],
             "original canonical validation was not the exact retained failed Rust invocation")
    _require(receipt.get("source_identity", {}).get("commit") == SOURCE_COMMIT and
             receipt.get("source_identity", {}).get("git_tree_sha1") == SOURCE_TREE_SHA1 and
             receipt.get("source_identity", {}).get("source_input_count") == 45,
             "original failed receipt no longer binds the fixed finite 45-input C6 source snapshot")
    receipt_directory = PurePosixPath(expected_receipt).parent
    stream_values = {}
    for stream in ("stdout", "stderr"):
        binding = receipt.get(stream)
        _require(isinstance(binding, dict) and set(binding) == {"path", "sha256", "bytes", "utf8"},
                 f"original failed {stream} binding is malformed")
        stream_path = _relative_path(binding["path"], f"original failed {stream} path")
        relative = (receipt_directory / stream_path).as_posix()
        _, data = _safe_regular_file(root, relative, f"original failed {stream} bytes")
        _require(_sha(data) == binding["sha256"] and len(data) == binding["bytes"] and
                 data.decode("utf-8", errors="replace") == binding["utf8"],
                 f"original failed {stream} bytes differ from the receipt binding")
        stream_values[stream] = {"path": relative, "sha256": binding["sha256"], "bytes": len(data)}
    _require(stream_values["stdout"]["sha256"] ==
             "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" and
             "applied-patch.json" in receipt["stderr"]["utf8"],
             "original failed stdout/stderr no longer match the observed missing-input failure")
    _require(failed.get("failure_message") == receipt["stderr"]["utf8"],
             "original failure summary differs from retained stderr")
    return {"receipt_sha256": digest, "status": receipt["status"], "exit_code": receipt["exit_code"],
            "stdout": stream_values["stdout"], "stderr": stream_values["stderr"]}


def _write_new(path: Path, data: bytes) -> None:
    _require(not path.exists() and not path.is_symlink(), f"append-only repair artifact already exists: {path}")
    try:
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except OSError as exc:
        raise MaterializationError(f"cannot write append-only repair artifact {path}: {exc}") from exc


def require_new_artifact_paths(paths: list[tuple[Path, str]]) -> None:
    """Refuse all fixed helper receipt collisions before any validation run."""
    for path, description in paths:
        _require(not path.exists() and not path.is_symlink(),
                 f"append-only {description} already exists or is a symlink: {path}")


def materialize_missing_refs(
    *,
    source_root: Path,
    checkout: Path,
    source_commit: str,
    source_tree_sha1: str,
    references: list[dict],
    supplement_paths: list[str],
    evidence_path: Path,
    materializer_sha256: str,
    manifest_sha256: str,
    expected_invocation: dict,
    expected_reference_count: int,
) -> dict:
    """Copy only the exact locked missing refs, then verify the entire closure."""
    source_root = _guard_directory_root(source_root, "materialization source root")
    checkout = _guard_directory_root(checkout, "new validation checkout")
    _require(checkout.is_relative_to(source_root), "new validation checkout is outside the source repository")
    _require(isinstance(source_commit, str) and GIT_BLOB_RE.fullmatch(source_commit) is not None and
             isinstance(source_tree_sha1, str) and GIT_BLOB_RE.fullmatch(source_tree_sha1) is not None,
             "materialization source commit/tree identity is malformed")
    _require(type(expected_reference_count) is int and expected_reference_count > 0 and
             len(references) == expected_reference_count,
             "materialization reference count differs from its caller's locked closure")
    _require(SHA256_RE.fullmatch(materializer_sha256) is not None and
             SHA256_RE.fullmatch(manifest_sha256) is not None,
             "materializer or manifest SHA-256 is malformed")
    normalized, supplement_set = _validate_reference_roster(references, supplement_paths)
    tree = _git_text(source_root, "rev-parse", f"{source_commit}^{{tree}}")
    _require(tree == source_tree_sha1, "materialization source tree no longer matches the C6 lock")

    missing: list[str] = []
    source_bytes: dict[str, bytes] = {}
    for item in normalized:
        relative = item["path"]
        _, data = _safe_regular_file(source_root, relative, "materialization source input")
        blob_id, blob_data = _git_blob(source_root, source_commit, relative)
        _require(blob_id == item["git_blob_sha1"] and _sha(data) == item["sha256"] and
                 _sha(blob_data) == item["sha256"] and data == blob_data,
                 f"source input is not the exact plan-bound source-commit blob: {relative}")
        target = _destination_path(checkout, relative)
        if target.is_symlink():
            raise MaterializationError(f"symlink in destination configuration closure: {relative}")
        if not target.exists():
            missing.append(relative)
            if relative in supplement_set:
                source_bytes[relative] = data
            continue
        _require(target.is_file(), f"destination input is not a regular file: {relative}")
        _require(_sha(target.read_bytes()) == item["sha256"],
                 f"pre-existing destination input differs from lock: {relative}")

    _require(sorted(missing) == sorted(supplement_set),
             "destination is not the expected 97-present/22-missing source-only checkout")
    _require(set(source_bytes) == supplement_set,
             "not all exact supplement inputs were loaded from the pinned source")

    copy_records: list[dict] = []
    by_path = {item["path"]: item for item in normalized}
    for relative in sorted(supplement_set):
        target = _destination_path(checkout, relative, create_parents=True)
        _require(not target.exists() and not target.is_symlink(),
                 f"supplement destination collision: {relative}")
        data = source_bytes[relative]
        try:
            with target.open("xb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
        except OSError as exc:
            raise MaterializationError(f"cannot write supplement input {relative}: {exc}") from exc
        item = by_path[relative]
        _require(_sha(target.read_bytes()) == item["sha256"],
                 f"supplement destination changed during materialization: {relative}")
        copy_records.append({
            "path": relative,
            "sha256": item["sha256"],
            "git_blob_sha1": item["git_blob_sha1"],
            "engines": item["engines"],
            "bytes": len(data),
        })

    verified_paths = []
    for item in normalized:
        _, data = _safe_regular_file(checkout, item["path"], "post-materialization configuration input")
        _require(_sha(data) == item["sha256"],
                 f"post-materialization input differs from its locked SHA-256: {item['path']}")
        verified_paths.append(item["path"])
    _require(len(verified_paths) == expected_reference_count and
             len(set(verified_paths)) == expected_reference_count,
             "post-materialization did not verify every unique locked configuration ref")
    _require(isinstance(expected_invocation, dict) and
             set(expected_invocation) == {"argv", "cwd", "environment"},
             "expected canonical Rust invocation binding is malformed")
    receipt = {
        "schema": "v0.9.2-v0151-swift-configuration-materialization/v1",
        "status": "exact-configuration-closure-materialized",
        "source_commit": source_commit,
        "source_tree_sha1": source_tree_sha1,
        "manifest_sha256": manifest_sha256,
        "materializer_sha256": materializer_sha256,
        "configuration_reference_count": len(verified_paths),
        "supplement_count": len(copy_records),
        "configuration_inputs_sha256": _sha(_canonical_json([
            {"path": item["path"], "sha256": item["sha256"]} for item in normalized
        ])),
        "supplements": copy_records,
        "verified_destination_count": len(verified_paths),
        "expected_canonical_invocation": expected_invocation,
        "recorded_at_utc": _utc_now(),
    }
    _write_new(evidence_path, _json_bytes(receipt))
    return receipt


def _load_manifest(root: Path) -> tuple[dict, str]:
    _, raw = _safe_regular_file(EVIDENCE_DIR, MANIFEST_PATH.name, "locked Swift configuration manifest")
    digest = _sha(raw)
    _require(digest == LOCKED_MANIFEST_SHA256,
             f"locked Swift configuration manifest SHA-256 mismatch: {digest}")
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MaterializationError("locked Swift configuration manifest is invalid JSON") from exc
    _require(isinstance(manifest, dict), "locked Swift configuration manifest must be a JSON object")
    diagnosis_path = DIAGNOSIS_PATH.name
    _, diagnosis_bytes = _safe_regular_file(EVIDENCE_DIR, diagnosis_path, "repair diagnosis record")
    try:
        diagnosis = json.loads(diagnosis_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MaterializationError("repair diagnosis record is invalid JSON") from exc
    _require(isinstance(diagnosis, dict) and diagnosis.get("manifest_sha256") == digest,
             "repair diagnosis does not bind the locked reference manifest")
    materializer_path = "materialize_v0151_swift_configuration_inputs.py"
    _, materializer_bytes = _safe_regular_file(EVIDENCE_DIR, materializer_path,
                                                "reviewed materializer source")
    _require(diagnosis.get("materializer_path") ==
             (EVIDENCE_DIR / materializer_path).relative_to(root).as_posix() and
             diagnosis.get("materializer_sha256") == _sha(materializer_bytes),
             "repair diagnosis does not bind the current materializer bytes")
    return manifest, digest


def _verify_canonical_python_sources(root: Path, manifest: dict) -> None:
    bindings = manifest.get("canonical_python_sources")
    _require(isinstance(bindings, dict) and ("validator" in bindings or "helper" in bindings),
             "manifest lacks canonical validator source bindings")
    for name, item in bindings.items():
        _require(isinstance(item, dict) and set(item) == {"path", "sha256", "git_blob_sha1"},
                 f"canonical Python source binding is malformed: {name}")
        relative = _relative_path(item["path"], f"canonical {name} source").as_posix()
        _, data = _safe_regular_file(root, relative, f"canonical {name} source")
        blob_id, blob_data = _git_blob(root, SOURCE_COMMIT, relative)
        _require(_sha(data) == item["sha256"] and blob_id == item["git_blob_sha1"] and
                 _sha(blob_data) == item["sha256"] and data == blob_data,
                 f"canonical {name} source differs from the original C6 checkout: {relative}")


def _load_canonical_validator(root: Path, manifest: dict) -> ModuleType:
    bindings = manifest["canonical_python_sources"]
    binding = bindings.get("validator", bindings.get("helper"))
    _require(isinstance(binding, dict), "manifest has no pinned canonical validator source")
    path, raw = _safe_regular_file(root, binding["path"], "pinned canonical validator")
    name = f"v0151_canonical_validation_{os.getpid()}"
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    _require(_sha(path.read_bytes()) == binding["sha256"],
             "canonical validator source changed while loading")
    return module


def _expected_environment(checkout: Path) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(checkout),
        "TMPDIR": str(checkout),
        "LANG": "C",
        "LC_ALL": "C",
        "NO_COLOR": "1",
    }


def _verify_runner_binding(binding: dict, manifest: dict) -> None:
    locked = manifest.get("runner")
    _require(isinstance(locked, dict) and
             binding == {"path": locked.get("path"), "sha256": locked.get("sha256")},
             "canonical validation runner differs from the original failed invocation")
    runner = Path(binding["path"])
    _require(runner.is_file() and not runner.is_symlink() and
             _sha(runner.read_bytes()) == locked["sha256"],
             "canonical runner bytes differ from the original failed invocation")
    _require(runner.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0,
             "canonical runner is not executable")


def _write_postcheck(root: Path, manifest: dict, manifest_sha256: str,
                     validation_result: dict, materialization_receipt_path: Path) -> dict:
    repair_receipt_path = root / "reports/releases/v0.9.2/validation" / RUN_NAMESPACE / "receipt.json"
    _, raw = _safe_regular_file(root, repair_receipt_path.relative_to(root).as_posix(),
                                "new canonical validation receipt")
    canonical = json.loads(raw)
    materialization = json.loads(materialization_receipt_path.read_text())
    _require(canonical.get("status") == validation_result.get("status"),
             "returned canonical validation result differs from the written receipt")
    failed = manifest["failed_validation"]
    _require(canonical.get("source_identity") == failed["source_identity"] and
             canonical.get("runner") == failed["runner"] and
             canonical.get("checker_summary") == failed["checker_summary"],
             "new canonical receipt differs from the pinned C6 source, runner, or selector evidence")
    expected_helpers = {
        name: {"path": item["path"], "sha256": item["sha256"]}
        for name, item in manifest["canonical_python_sources"].items()
    }
    _require(canonical.get("helper_identities") == expected_helpers,
             "new canonical receipt loaded different validator/preflight helper bytes")
    _require(canonical.get("command") == materialization.get("expected_canonical_invocation", {}).get("argv") and
             canonical.get("cwd") == materialization.get("expected_canonical_invocation", {}).get("cwd") and
             canonical.get("environment") == materialization.get("expected_canonical_invocation", {}).get("environment"),
             "canonical validation receipt differs from the separately verified invocation binding")
    materialization_digest = _sha(materialization_receipt_path.read_bytes())
    status = ("canonical-validation-passed-with-verified-supplement-materialization"
              if canonical.get("status") == "canonical-validation-passed"
              else "canonical-validation-failed-after-verified-supplement-materialization")
    postcheck = {
        "schema": "v0.9.2-v0151-swift-configuration-repair-postcheck/v1",
        "status": status,
        "canonical_validation_receipt": {
            "path": repair_receipt_path.relative_to(root).as_posix(),
            "sha256": _sha(raw),
            "status": canonical.get("status"),
            "exit_code": canonical.get("exit_code"),
            "command": canonical.get("command"),
            "cwd": canonical.get("cwd"),
            "metrics": canonical.get("metrics"),
            "source_identity": canonical.get("source_identity"),
            "runner": canonical.get("runner"),
            "checker_summary": canonical.get("checker_summary"),
            "helper_identities": canonical.get("helper_identities"),
        },
        "supplement_materialization_receipt": {
            "path": materialization_receipt_path.relative_to(root).as_posix(),
            "sha256": materialization_digest,
            "status": materialization.get("status"),
            "supplement_count": materialization.get("supplement_count"),
            "configuration_reference_count": materialization.get("configuration_reference_count"),
        },
        "manifest_sha256": manifest_sha256,
        "source_commit": manifest["source_commit"],
        "source_tree_sha1": manifest["source_tree_sha1"],
        "original_failed_namespace_retained": manifest["failed_validation"]["receipt_path"],
        "recorded_at_utc": _utc_now(),
    }
    return postcheck


def inspect(root: Path = ROOT) -> dict:
    root = root.resolve(strict=True)
    manifest, manifest_sha256 = _load_manifest(root)
    verify_locked_source(root, manifest)
    _verify_canonical_python_sources(root, manifest)
    failed_checkout = verify_failed_checkout(root, manifest)
    return {
        "status": "locked-source-and-original-sparse-checkout-verified",
        "manifest_sha256": manifest_sha256,
        "source_commit": manifest["source_commit"],
        "source_tree_sha1": manifest["source_tree_sha1"],
        "reference_count": len(manifest["references"]),
        "failed_checkout": failed_checkout,
        "runner": manifest["runner"],
        "intended_runner_namespace": RUN_NAMESPACE,
    }


def execute(root: Path = ROOT) -> dict:
    """Run the pinned validator in namespace 02 with only locked supplements."""
    root = root.resolve(strict=True)
    manifest, manifest_sha256 = _load_manifest(root)
    verify_locked_source(root, manifest)
    _verify_canonical_python_sources(root, manifest)
    verify_failed_checkout(root, manifest)
    module = _load_canonical_validator(root, manifest)
    original_invoke: Callable = module._invoke_runner
    materialization_receipt_path = EVIDENCE_DIR / "supplement-materialization.json"
    postcheck_path = EVIDENCE_DIR / "canonical-postcheck.json"
    require_new_artifact_paths([
        (materialization_receipt_path, "supplement materialization receipt"),
        (postcheck_path, "canonical postcheck receipt"),
    ])
    invocation_count = 0

    def _invoke_with_supplements(binding: dict, checkout: Path, environment: dict[str, str],
                                 timeout_seconds: int = 1800) -> dict:
        nonlocal invocation_count
        invocation_count += 1
        _require(invocation_count == 1, "canonical runner invocation attempted more than once")
        _verify_runner_binding(binding, manifest)
        checkout = _guard_directory_root(checkout, "canonical validation checkout")
        expected_checkout = root / "execution-state/v092/validation" / RUN_NAMESPACE
        _require(checkout == expected_checkout.resolve(strict=True),
                 "canonical validator selected a different fresh checkout namespace")
        expected_argv = [binding["path"], "--population", "v0.9.0", "validate-reports"]
        expected_environment = _expected_environment(checkout)
        _require(environment == expected_environment,
                 "canonical validator environment differs from the registered validation environment")
        invocation = {"argv": expected_argv, "cwd": str(checkout), "environment": expected_environment}
        receipt = materialize_missing_refs(
            source_root=root,
            checkout=checkout,
            source_commit=manifest["source_commit"],
            source_tree_sha1=manifest["source_tree_sha1"],
            references=manifest["references"],
            supplement_paths=manifest["supplement_paths"],
            evidence_path=materialization_receipt_path,
            materializer_sha256=_sha(Path(__file__).read_bytes()),
            manifest_sha256=manifest_sha256,
            expected_invocation=invocation,
            expected_reference_count=119,
        )
        _verify_plan_bindings(root, manifest, checkout=checkout)
        actual = original_invoke(binding, checkout, environment, timeout_seconds)
        _require(actual.get("argv") == expected_argv and actual.get("cwd") == str(checkout) and
                 actual.get("environment") == expected_environment,
                 "canonical validator invoked a different Rust command or environment")
        _require(receipt.get("verified_destination_count") == 119 and
                 receipt.get("supplement_count") == 22,
                 "supplement receipt does not cover the fixed closure")
        return actual

    module._invoke_runner = _invoke_with_supplements
    try:
        result = module.validate(
            root=root,
            output=RUN_NAMESPACE,
            execute=True,
            evidence_source="v0151",
        )
    finally:
        module._invoke_runner = original_invoke

    postcheck = _write_postcheck(
        root, manifest, manifest_sha256, result, materialization_receipt_path,
    )
    _write_new(postcheck_path, _json_bytes(postcheck))
    if postcheck["status"] != "canonical-validation-passed-with-verified-supplement-materialization":
        raise MaterializationError("canonical validation did not pass after verified Swift input hydration")
    return postcheck


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="run the exact canonical validator in the new -02 namespace")
    args = parser.parse_args(argv)
    try:
        result = execute() if args.execute else inspect()
    except Exception as exc:
        print(f"swift configuration repair preflight failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
