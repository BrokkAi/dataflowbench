#!/usr/bin/env python3
"""Prepare and optionally run the hash-bound v0.15.1 canonical schema gate.

Preparation is read-only with respect to benchmark/source evidence. It verifies
the retained configurations-03 receipt and inputs, copies that private checkout
to configurations-04, then applies the version-scoped Joern metadata projector
to exactly five reports. ``--invoke`` is a separate operation; it calls the
immutable original validator's runner and stdout gate without rerunning the C6
selector or any analyzer.
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
import time
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SCRIPT_DIR = Path(__file__).resolve().parent
DIAGNOSIS_DIR = SCRIPT_DIR / "diagnosis"
OLD_NAMESPACE = "bifrost-v0151-configurations-03"
NEW_NAMESPACE = "bifrost-v0151-configurations-04"
OLD_CHECKOUT_REL = PurePosixPath("execution-state/v092/validation") / OLD_NAMESPACE
NEW_CHECKOUT_REL = PurePosixPath("execution-state/v092/validation") / NEW_NAMESPACE
OLD_RECEIPT_REL = PurePosixPath("reports/releases/v0.9.2/validation") / OLD_NAMESPACE / "receipt.json"
OLD_STDOUT_REL = PurePosixPath("reports/releases/v0.9.2/validation") / OLD_NAMESPACE / "stdout.bin"
OLD_STDERR_REL = PurePosixPath("reports/releases/v0.9.2/validation") / OLD_NAMESPACE / "stderr.bin"
NEW_RECEIPT_DIR_REL = PurePosixPath("reports/releases/v0.9.2/validation") / NEW_NAMESPACE
NEW_RECEIPT_REL = NEW_RECEIPT_DIR_REL / "receipt.json"
C6_CONTRACT_REL = PurePosixPath("reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json")
REF_MANIFEST_REL = PurePosixPath(
    "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-repair-02/swift-configuration-ref-manifest.json"
)
BUILD_RECEIPT_REL = PurePosixPath("reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/receipt.json")
BUILD_INPUTS_REL = PurePosixPath("reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/source-inputs.json")
LEDGER_REL = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
SCHEMA_REL = PurePosixPath("schemas/result.schema.json")
PROJECTOR_REL = PurePosixPath(
    "reports/releases/v0.9.2/validation/joern-v092-canonical-schema-01/project_joern.py"
)
PROJECTOR_MANIFEST_REL = PurePosixPath(
    "reports/releases/v0.9.2/validation/joern-v092-canonical-schema-01/manifest.json"
)
VALIDATOR_REL = PurePosixPath("scripts/validate-v092-report-configurations.py")
VALIDATOR_SHA256 = "2e8e17261f60c0b8aed816e7b3b1df690865a111b5f121079b83b2b47296f515"
SCHEMA_SHA256 = "d8fa8aeb9c17a792e858b5168a318794079ff1ae65404699cd96ee886d302217"
PROJECTOR_SHA256 = "13f8312504f641743d050101bb695ede820af90797db66de940ebdd318269f91"
PROJECTOR_MANIFEST_SHA256 = "07cfbcbcf1fba81ef00bfa66abda0b10668ff8b63c8ace4ce0bd1f36381428a3"
FAILED_RECEIPT_SHA256 = "ee64f260ca05192a1f0c064905df54e1d9f27687eb549605fad9f31482d7d11b"
FAILED_STDERR_SHA256 = "11d65e6a0a27148dc70681cd0b4534c5391dcdcf6bd58eb624ede0068af5012e"
FAILED_STDOUT_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
C6_CONTRACT_SHA256 = "f2c0fe969eb959856c650e8e892a9078342ec63600fc23dd05c3f069c068af65"
C6_CONTRACT_BLOB_SHA1 = "932813cdb3dcb0c004e9e2d3686fd7273c90a7e7"
C6_COMMIT = "515d9941978c12cafa37ba58eecacc0a4182226f"
SOURCE_COMMIT = "7f99684668065b8fb1ebc9b2852f058c64430647"
SOURCE_TREE_SHA1 = "7af8853a1e2eb7ea7832f7c0bad4d2299c1ab416"
RUNNER_SHA256 = "99d997b31024ee7ff5edbee381cf2addff5f25d6851cc19980f515142b9508a5"
RUNNER_BYTES = 11021696
RUNNER_CANONICAL_JSON_SHA256 = "9dfc1651cb26147777451c85cfcfef9d1907b4ee2071ffd9f5c7dc917ac99a7b"
LEDGER_SHA256 = "5528a3ff7683546a09c03d5791b5283bba3e08428c9380890e3e4cfe5d268679"
REF_MANIFEST_SHA256 = "63a2930d12453e02c01f87228c6952a21a2b98e261586cc4338b4d3e2789e74f"
EXPECTED_REPORTS = 92
EXPECTED_ROWS = 4252
EXPECTED_GROUPS = 84
EXPECTED_RAW_FILES = 4252
EXPECTED_CONFIG_REFS = 119
EXPECTED_JOERN_ROWS = 108
TIMEOUT_SECONDS = 1800
JOERN_REPORTS = (
    "joern-swift-calibration.json",
    "joern-swift-core.json",
    "joern-swift-language-extension.json",
    "joern-swift-modeling.json",
    "joern-swift-native.json",
)
INDEPENDENT_REVIEW_REL = PurePosixPath(
    "reports/releases/v0.9.2/validation/bifrost-v0151-canonical-schema-01/independent-review-01.json"
)
TOP_LEVEL_MOVED_FIELDS = ("aggregate_resource_qualification", "scored_activation")
ROW_MOVED_FIELD = "raw_sha256"


class GateError(ValueError):
    """Fail-closed canonical-schema gate error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def _safe_relative(value: object, description: str) -> PurePosixPath:
    _require(isinstance(value, str) and value != "" and "\\" not in value,
             f"{description} is not a safe repository-relative POSIX path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and path.parts and
             all(part not in ("", ".", "..") for part in path.parts),
             f"{description} escapes its repository root")
    return path


def _read_under(root: Path, relative: object, description: str) -> bytes:
    root = root.resolve(strict=True)
    rel = _safe_relative(relative, description)
    candidate = root
    for component in rel.parts:
        candidate = candidate / component
        _require(not candidate.is_symlink(), f"{description} crosses a symlink: {rel.as_posix()}")
    _require(candidate.is_file(), f"{description} is missing or not a regular file: {rel.as_posix()}")
    resolved = candidate.resolve(strict=True)
    _require(resolved == root or root in resolved.parents,
             f"{description} escapes its root: {rel.as_posix()}")
    mode = os.lstat(candidate).st_mode
    _require(stat.S_ISREG(mode), f"{description} is not a regular file: {rel.as_posix()}")
    return candidate.read_bytes()


def _read_json_under(root: Path, relative: PurePosixPath, description: str) -> tuple[dict, bytes]:
    raw = _read_under(root, relative.as_posix(), description)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"{description} is invalid JSON") from exc
    _require(isinstance(value, dict), f"{description} must be a JSON object")
    return value, raw


def _check_sha(data: bytes, expected: str, description: str) -> None:
    _require(_sha(data) == expected,
             f"{description} SHA-256 drift: expected {expected}, got {_sha(data)}")


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GateError(f"read-only Git identity query failed: git {' '.join(args)}") from exc


def _file_inventory(checkout: Path) -> dict:
    """Hash every checkout path without following symlinks or special files."""
    _require(checkout.is_dir() and not checkout.is_symlink(),
             f"checkout is missing or unsafe: {checkout}")
    root = checkout.resolve(strict=True)
    entries: list[dict] = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        here = Path(directory)
        names.sort()
        files.sort()
        for name in names:
            path = here / name
            _require(not path.is_symlink(), f"checkout contains a symlink: {path}")
            mode = os.lstat(path).st_mode
            _require(stat.S_ISDIR(mode), f"checkout contains a non-directory path: {path}")
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "kind": "directory",
                "mode": stat.S_IMODE(mode),
            })
        for name in files:
            path = here / name
            _require(not path.is_symlink(), f"checkout contains a symlink: {path}")
            st = os.lstat(path)
            _require(stat.S_ISREG(st.st_mode), f"checkout contains a non-regular file: {path}")
            data = path.read_bytes()
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "kind": "file",
                "mode": stat.S_IMODE(st.st_mode),
                "bytes": len(data),
                "sha256": _sha(data),
            })
    entries.sort(key=lambda item: item["path"])
    canonical = _canonical_json(entries)
    return {
        "root": str(root),
        "file_count": sum(item["kind"] == "file" for item in entries),
        "directory_count": sum(item["kind"] == "directory" for item in entries),
        "total_file_bytes": sum(item.get("bytes", 0) for item in entries),
        "entries_sha256": _sha(canonical),
        "entries": entries,
    }


def _compare_inventories(
    before: dict,
    after: dict,
    *,
    allowed_changed_files: set[str] | None = None,
) -> dict:
    allowed = allowed_changed_files or set()
    left = {item["path"]: item for item in before["entries"]}
    right = {item["path"]: item for item in after["entries"]}
    _require(len(left) == len(before["entries"]) and len(right) == len(after["entries"]),
             "checkout inventory contains duplicate paths")
    added, removed, changed = [], [], []
    for path in sorted(set(left) | set(right)):
        if path not in left:
            added.append(path)
        elif path not in right:
            removed.append(path)
        elif left[path] != right[path]:
            changed.append(path)
    _require(not added and not removed,
             f"checkout inventory paths changed; added={added[:5]}, removed={removed[:5]}")
    unexpected = sorted(set(changed) - allowed)
    _require(not unexpected,
             f"checkout files outside the exact Joern projection changed: {unexpected[:8]}")
    _require(set(changed) == allowed,
             f"expected all and only the five declared Joern reports to change; changed={changed}")
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_file_count": len(left) - len(changed),
        "unchanged_path_and_mode_count": len(left) - len(changed),
    }


def _verify_runner_binding(root: Path, contract: dict, ref_manifest: dict, failed: dict) -> dict:
    runtime = contract.get("runtime")
    _require(isinstance(runtime, dict) and isinstance(runtime.get("runner"), dict),
             "C6 contract lacks the full runtime runner binding")
    runner = runtime["runner"]
    _require(set(runner) == {"path", "sha256", "build_receipt"},
             "C6 runtime runner binding must retain exactly its full three-field shape")
    approved = ref_manifest.get("approved_c6_contract")
    _require(isinstance(approved, dict) and
             approved.get("runtime_runner_canonical_json_sha256") == RUNNER_CANONICAL_JSON_SHA256 and
             approved.get("sha256") == C6_CONTRACT_SHA256 and
             approved.get("plan_commit") == C6_COMMIT and
             approved.get("plan_blob_sha1") == C6_CONTRACT_BLOB_SHA1,
             "repair-02 manifest does not bind the exact C6 plan and full runner object")
    _check_sha(_canonical_json(runner), RUNNER_CANONICAL_JSON_SHA256,
               "full C6 runner object canonical JSON")
    _require(runner == ref_manifest.get("runner"),
             "repair-02 manifest runner differs from the complete C6 contract runner object")
    _require(runner.get("path") == failed.get("runner", {}).get("path") and
             runner.get("sha256") == RUNNER_SHA256 and
             failed.get("runner", {}).get("sha256") == RUNNER_SHA256,
             "metadata03 runner identity differs from the full C6 runner binding")
    _require(runner["path"] == str((root / "execution-state/v092/builds/bifrost0151-01-target/release/dataflowbench").resolve()),
             "C6 runner path differs from the exact retained release build")
    runner_path = Path(runner["path"])
    _require(runner_path.is_file() and not runner_path.is_symlink(),
             "bound canonical runner is missing or unsafe")
    binary = runner_path.read_bytes()
    _require(len(binary) == RUNNER_BYTES and _sha(binary) == RUNNER_SHA256,
             "bound canonical runner bytes or size drifted")
    build = runner.get("build_receipt")
    _require(isinstance(build, dict) and isinstance(build.get("receipt"), dict),
             "C6 runner binding lacks its nested build receipt identity")
    build_receipt = _read_under(root, build["receipt"].get("path"), "C6 build receipt")
    _check_sha(build_receipt, build["receipt"].get("sha256"), "C6 build receipt")
    _check_sha(build_receipt, "513e035d700b396fc4b33ede8e481e5888c59406b3f0833e721feccd40af1e48",
               "pinned C6 build receipt")
    build_inputs = _read_under(root, build["source_inputs"].get("path"), "C6 build source input receipt")
    _check_sha(build_inputs, build["source_inputs"].get("sha256"), "C6 build source input receipt")
    _require(failed.get("runner_sha256_after") == RUNNER_SHA256,
             "metadata03 runner-after identity differs from C6")
    return runner


def _verify_contract_and_ledger(root: Path, contract: dict, contract_bytes: bytes) -> dict:
    _check_sha(contract_bytes, C6_CONTRACT_SHA256, "C6 contract")
    _require(_git(root, "rev-parse", f"{C6_COMMIT}:{C6_CONTRACT_REL.as_posix()}") == C6_CONTRACT_BLOB_SHA1,
             "C6 contract Git blob differs from the pinned plan object")
    _require(_git(root, "rev-parse", f"{SOURCE_COMMIT}^{{tree}}") == SOURCE_TREE_SHA1,
             "pinned source commit tree identity changed")
    _require(contract.get("source_snapshot", {}).get("source_commit") == SOURCE_COMMIT,
             "C6 contract no longer names the pinned source commit")
    ledger_anchor = contract.get("ledger_anchor")
    _require(isinstance(ledger_anchor, dict), "C6 contract lacks its ledger anchor")
    ledger = _read_under(root, LEDGER_REL.as_posix(), "v0.9.2 release ledger")
    _check_sha(ledger, LEDGER_SHA256, "151-row C6 ledger")
    lines = ledger.splitlines(keepends=True)
    _require(len(lines) == 151, "current C6 ledger no longer contains exactly 151 rows")
    anchor_count = ledger_anchor.get("line_count")
    _require(anchor_count == 131 and len(lines) >= anchor_count,
             "C6 ledger anchor does not retain its exact 131-row prefix")
    prefix = b"".join(lines[:anchor_count])
    _check_sha(prefix, ledger_anchor.get("sha256"), "C6 preserved ledger prefix")
    return {
        "path": LEDGER_REL.as_posix(),
        "sha256": _sha(ledger),
        "bytes": len(ledger),
        "line_count": len(lines),
        "preserved_prefix_lines": anchor_count,
        "preserved_prefix_sha256": _sha(prefix),
    }


def _verify_old_failure(root: Path) -> dict:
    failed, receipt_bytes = _read_json_under(root, OLD_RECEIPT_REL, "retained metadata03 receipt")
    _check_sha(receipt_bytes, FAILED_RECEIPT_SHA256, "retained metadata03 receipt")
    _require(failed.get("status") == "failed" and failed.get("exit_code") == 1 and
             failed.get("execution_requested") is True and failed.get("timed_out") is False and
             failed.get("metrics") is None,
             "retained metadata03 receipt does not bind the expected schema-validation failure")
    _require(failed.get("stdout_parse_error") ==
             "canonical validator stdout must contain one exact report-count line and one configuration-count line",
             "metadata03 failure no longer records the exact missing canonical stdout metrics")
    stdout = _read_under(root, OLD_STDOUT_REL.as_posix(), "metadata03 stdout")
    stderr = _read_under(root, OLD_STDERR_REL.as_posix(), "metadata03 stderr")
    _check_sha(stdout, FAILED_STDOUT_SHA256, "metadata03 stdout")
    _check_sha(stderr, FAILED_STDERR_SHA256, "metadata03 schema stderr")
    _require(stdout == b"", "metadata03 stdout is not the retained empty stdout")
    text = stderr.decode("utf-8")
    for required in ("'raw_sha256' was unexpected", "'aggregate_resource_qualification', 'scored_activation' were unexpected"):
        _require(required in text, f"metadata03 stderr no longer contains the exact schema failure {required}")
    return {
        "receipt": {"path": OLD_RECEIPT_REL.as_posix(), "sha256": _sha(receipt_bytes), "bytes": len(receipt_bytes)},
        "stdout": {"path": OLD_STDOUT_REL.as_posix(), "sha256": _sha(stdout), "bytes": len(stdout)},
        "stderr": {"path": OLD_STDERR_REL.as_posix(), "sha256": _sha(stderr), "bytes": len(stderr)},
        "status": failed["status"],
        "exit_code": failed["exit_code"],
        "metrics": failed["metrics"],
        "stdout_parse_error": failed["stdout_parse_error"],
        "stderr_text": text,
        "receipt_json": failed,
    }


def _verify_metadata03_evidence(root: Path, failed: dict, ref_manifest: dict) -> dict:
    checkout = root / Path(*OLD_CHECKOUT_REL.parts)
    _require(checkout.is_dir() and not checkout.is_symlink(), "metadata03 private checkout is missing or unsafe")
    identity = failed.get("source_identity")
    _require(identity == {
        "commit": SOURCE_COMMIT,
        "git_tree_sha1": SOURCE_TREE_SHA1,
        "runner_source_sha256": "45083ff44ebbc698e5d7e70d376b28039a6c6648a174e0adc7eac12b55d730dd",
        "source_input_count": 45,
        "source_inputs_sha256": "050a91566744a46b3604e4c65afa75601f690a4f70c86b65c16f187f151217d5",
    }, "metadata03 source identity differs from the pinned C6 source commit and closure")
    summary = failed.get("checker_summary")
    _require(isinstance(summary, dict) and summary.get("status") == "fresh-evidence-verified" and
             summary.get("fresh_groups") == EXPECTED_GROUPS and
             summary.get("fresh_reports") == EXPECTED_REPORTS and
             summary.get("fresh_rows") == EXPECTED_ROWS and summary.get("carried_rows") == 0,
             "metadata03 selector summary no longer binds the exact fresh C6 set")
    _require(failed.get("contract") == {"path": C6_CONTRACT_REL.as_posix(), "sha256": C6_CONTRACT_SHA256} and
             failed.get("target_contract") == {"path": C6_CONTRACT_REL.as_posix(), "sha256": C6_CONTRACT_SHA256},
             "metadata03 receipt does not bind the exact C6 target contract")
    _require(failed.get("runner", {}).get("sha256") == RUNNER_SHA256 and
             failed.get("runner_sha256_after") == RUNNER_SHA256,
             "metadata03 receipt does not bind the retained release runner")
    helper_identities = failed.get("helper_identities")
    _require(isinstance(helper_identities, dict) and len(helper_identities) == 8,
             "metadata03 receipt does not bind all eight immutable Python helpers")
    for name, item in helper_identities.items():
        _require(isinstance(item, dict) and set(item) == {"path", "sha256"},
                 f"metadata03 helper identity is malformed: {name}")
        data = _read_under(root, item["path"], f"retained validation helper {name}")
        _check_sha(data, item["sha256"], f"retained validation helper {name}")
    expected_command = [
        str((root / "execution-state/v092/builds/bifrost0151-01-target/release/dataflowbench").resolve()),
        "--population", "v0.9.0", "validate-reports",
    ]
    _require(failed.get("command") == expected_command,
             "metadata03 command differs from the immutable canonical argv")
    expected_env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(checkout.resolve()),
        "TMPDIR": str(checkout.resolve()),
        "LANG": "C", "LC_ALL": "C", "NO_COLOR": "1",
    }
    _require(failed.get("cwd") == str(checkout.resolve()) and failed.get("environment") == expected_env,
             "metadata03 cwd or six-variable environment differs from its retained receipt")
    source_identity = ref_manifest.get("source_commit")
    _require(source_identity == SOURCE_COMMIT and ref_manifest.get("source_tree_sha1") == SOURCE_TREE_SHA1,
             "repair-02 input manifest differs from the pinned C6 source snapshot")
    refs = ref_manifest.get("references")
    counts = ref_manifest.get("counts")
    _require(isinstance(refs, list) and len(refs) == EXPECTED_CONFIG_REFS and
             isinstance(counts, dict) and counts.get("unique_references") == EXPECTED_CONFIG_REFS and
             counts.get("initially_present_references") == 97 and
             counts.get("supplement_references") == 22,
             "repair-02 manifest does not bind all 119 original configuration inputs")
    seen_refs: set[str] = set()
    for item in refs:
        _require(isinstance(item, dict), "repair-02 input manifest contains a malformed reference")
        rel = _safe_relative(item.get("path"), "declared configuration input")
        _require(rel.as_posix() not in seen_refs, f"duplicate declared configuration input: {rel}")
        seen_refs.add(rel.as_posix())
        data = _read_under(checkout, rel.as_posix(), "materialized Swift configuration input")
        _check_sha(data, item.get("sha256"), f"declared configuration input {rel}")
    supplement_paths = ref_manifest.get("supplement_paths")
    _require(isinstance(supplement_paths, list) and len(supplement_paths) == 22 and
             set(supplement_paths) <= seen_refs,
             "repair-02 supplement list differs from the 22 verified configuration references")
    refs_by_path = {item["path"]: item for item in refs}
    _require({path for path, item in refs_by_path.items() if item.get("initial_failed_checkout_state") == "supplement"} ==
             set(supplement_paths),
             "the 22 supplements are not exactly the manifest-designated inputs added after failed checkout 01")

    reports = failed.get("reports")
    raw_files = failed.get("raw_files")
    attempt_receipts = failed.get("attempt_receipts")
    _require(isinstance(reports, list) and len(reports) == EXPECTED_REPORTS,
             "metadata03 report binding count differs from C6")
    _require(isinstance(raw_files, list) and len(raw_files) == EXPECTED_RAW_FILES,
             "metadata03 raw output binding count differs from C6")
    _require(isinstance(attempt_receipts, list) and len(attempt_receipts) == EXPECTED_GROUPS,
             "metadata03 attempt receipt binding count differs from C6")
    report_names: set[str] = set()
    total_rows = 0
    for report in reports:
        rel = _safe_relative(report.get("validation_path"), "metadata03 projected report")
        _require(rel.as_posix() not in report_names, f"duplicate metadata03 report path: {rel}")
        report_names.add(rel.as_posix())
        data = _read_under(checkout, rel.as_posix(), "metadata03 projected report")
        _check_sha(data, report.get("sha256"), f"metadata03 report {rel}")
        source_rel = _safe_relative(report.get("source_path"), "metadata03 source report")
        source_data = _read_under(root, source_rel.as_posix(), "retained C6 source report")
        _check_sha(source_data, report.get("sha256"), f"metadata03 source report {source_rel}")
        _require(source_data == data, f"metadata03 report copy differs from its retained C6 source: {rel}")
        parsed = json.loads(data)
        _require(isinstance(parsed, dict) and isinstance(parsed.get("results"), list) and
                 len(parsed["results"]) == report.get("rows"),
                 f"metadata03 report row count changed: {rel}")
        total_rows += len(parsed["results"])
    _require(total_rows == EXPECTED_ROWS, "metadata03 reports do not total the pinned 4,252 rows")
    joern = {PurePosixPath(path).name for path in report_names if PurePosixPath(path).name.startswith("joern-swift-")}
    _require(joern == set(JOERN_REPORTS), "metadata03 does not contain the exact five Joern partitions")

    raw_paths: set[str] = set()
    for item in raw_files:
        rel = _safe_relative(item.get("relative_path"), "metadata03 raw output")
        _require(rel.as_posix() not in raw_paths, f"duplicate raw output path: {rel}")
        raw_paths.add(rel.as_posix())
        data = _read_under(checkout, rel.as_posix(), "metadata03 raw output")
        _require(len(data) == item.get("bytes"), f"metadata03 raw output byte count changed: {rel}")
        _check_sha(data, item.get("sha256"), f"metadata03 raw output {rel}")
        _require(isinstance(item.get("references"), list) and item["references"],
                 f"metadata03 raw output lacks report/row references: {rel}")

    for item in attempt_receipts:
        rel = _safe_relative(item.get("path"), "metadata03 attempt receipt")
        data = _read_under(root, rel.as_posix(), "retained selected attempt receipt")
        _check_sha(data, item.get("sha256"), f"selected attempt receipt {rel}")

    return {
        "source_identity": identity,
        "checker_summary": summary,
        "configuration_inputs": {
            "manifest_path": REF_MANIFEST_REL.as_posix(),
            "manifest_sha256": REF_MANIFEST_SHA256,
            "unique_references": len(seen_refs),
            "initially_present": 97,
            "verified_supplements": 22,
        },
        "reports": {"count": len(reports), "rows": total_rows, "verified": len(report_names)},
        "raw_outputs": {"count": len(raw_files), "verified": len(raw_paths), "unique_paths": len(raw_paths)},
        "attempt_receipts": {"count": len(attempt_receipts), "verified": len(attempt_receipts),
                             "verification_root": str(root)},
        "helper_identities": helper_identities,
        "command": failed["command"],
        "cwd": failed["cwd"],
        "environment": failed["environment"],
    }


def _inventory_for_receipt(inventory: dict) -> dict:
    return {key: value for key, value in inventory.items() if key != "entries"}


def _write_new(path: Path, data: bytes) -> None:
    _require(not path.exists() and not path.is_symlink(), f"append-only output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.parent.is_symlink(), f"output parent is a symlink: {path.parent}")
    with path.open("xb") as handle:
        handle.write(data)


def _load_exact_module(path: Path, name: str, expected_sha256: str) -> ModuleType:
    _require(path.is_file() and not path.is_symlink(), f"required Python source is missing or unsafe: {path}")
    source = path.read_bytes()
    _check_sha(source, expected_sha256, f"pinned Python source {path}")
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
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
    _check_sha(path.read_bytes(), expected_sha256, f"Python source after exact-byte load {path}")
    return module


def _schema_shape(report: dict, schema: dict, *, allow_joern_metadata: bool) -> None:
    props = schema.get("properties")
    _require(isinstance(props, dict) and "results" in props,
             "pinned result schema lacks its results property")
    allowed_top = set(props)
    allowed_rows_obj = props["results"].get("items", {})
    allowed_rows = allowed_rows_obj.get("properties") if isinstance(allowed_rows_obj, dict) else None
    _require(isinstance(allowed_rows, dict), "pinned result schema lacks result-row properties")
    top_extra = set(report) - allowed_top
    row_extras = {
        key
        for row in report.get("results", [])
        if isinstance(row, dict)
        for key in set(row) - set(allowed_rows)
    }
    if allow_joern_metadata:
        _require(top_extra == set(TOP_LEVEL_MOVED_FIELDS),
                 f"Joern report contains unknown top-level properties: {sorted(top_extra - set(TOP_LEVEL_MOVED_FIELDS))}")
        _require(row_extras == {ROW_MOVED_FIELD},
                 f"Joern report contains unknown result-row properties: {sorted(row_extras - {ROW_MOVED_FIELD})}")
    else:
        _require(not top_extra and not row_extras,
                 f"projected report still has undeclared properties: top={sorted(top_extra)}, row={sorted(row_extras)}")


def _assert_only_metadata_moved(original: dict, canonical: dict) -> None:
    expected = copy.deepcopy(original)
    for name in TOP_LEVEL_MOVED_FIELDS:
        _require(name in expected, f"producer report is missing expected metadata field {name}")
        expected.pop(name)
    rows = expected.get("results")
    _require(isinstance(rows, list) and rows, "producer report has no result rows")
    removed = 0
    for row in rows:
        _require(isinstance(row, dict) and ROW_MOVED_FIELD in row,
                 "producer report row is missing the expected raw SHA annotation")
        row.pop(ROW_MOVED_FIELD)
        removed += 1
    _require(canonical == expected,
             "projected report changed a field outside the three explicitly moved metadata types")


def _projector_identity(root: Path) -> dict:
    raw = _read_under(root, PROJECTOR_REL.as_posix(), "Joern metadata projector")
    _check_sha(raw, PROJECTOR_SHA256, "pinned Joern metadata projector")
    manifest, manifest_raw = _read_json_under(root, PROJECTOR_MANIFEST_REL, "Joern projector manifest")
    _check_sha(manifest_raw, PROJECTOR_MANIFEST_SHA256, "pinned Joern projector manifest")
    implementation = manifest.get("implementation")
    source_bindings = manifest.get("source_bindings")
    projector_binding = implementation.get("projector") if isinstance(implementation, dict) else None
    schema_binding = source_bindings.get("frozen_schema") if isinstance(source_bindings, dict) else None
    _require(isinstance(projector_binding, dict) and
             projector_binding.get("path") == PROJECTOR_REL.as_posix() and
             projector_binding.get("sha256") == PROJECTOR_SHA256 and
             isinstance(schema_binding, dict) and
             schema_binding.get("path") == SCHEMA_REL.as_posix() and
             schema_binding.get("sha256") == SCHEMA_SHA256 and
             schema_binding.get("pinned_sha256") == SCHEMA_SHA256 and
             manifest.get("source_commit") == SOURCE_COMMIT and
             manifest.get("source_tree_sha1") == SOURCE_TREE_SHA1,
             "projector manifest does not bind the exact helper and production schema")
    _require(implementation.get("removed_fields_only") == [
                 "aggregate_resource_qualification", "scored_activation", "results[*].raw_sha256",
             ] and implementation.get(
                 "rejects_unknown_extra_fields_unsupported_identity_missing_fields_invalid_hash_missing_raw_hash_mismatch_symlink_duplicate_case_id"
             ) is True,
             "projector manifest does not state the strict three-field removal and near-miss rejection contract")
    prior_failure = source_bindings.get("canonical03_failure", {})
    _require(isinstance(prior_failure, dict) and
             prior_failure.get("receipt_sha256") == FAILED_RECEIPT_SHA256 and
             prior_failure.get("stderr_sha256") == FAILED_STDERR_SHA256,
             "projector manifest does not bind the retained metadata03 schema failure")
    projection_binding = source_bindings.get("projection_manifest", {})
    _require(isinstance(projection_binding, dict) and
             projection_binding.get("path") ==
             "execution-state/v092/publication-evidence/joern108-metadata-projection-01/projection.json" and
             projection_binding.get("sha256") == "fbb306636dcd92c22ef296dba9716acd4dae127c617332212f33ebc2bd68a907",
             "projector manifest does not bind the retained terminal projection")
    projection_bytes = _read_under(root, projection_binding["path"], "retained Joern projection manifest")
    _check_sha(projection_bytes, projection_binding["sha256"], "retained Joern projection manifest")
    report_bindings = source_bindings.get("five_original_reports")
    _require(isinstance(report_bindings, list) and len(report_bindings) == len(JOERN_REPORTS),
             "projector manifest does not bind exactly five original Joern reports")
    by_name = {PurePosixPath(item.get("path", "")).name: item
               for item in report_bindings if isinstance(item, dict)}
    _require(set(by_name) == set(JOERN_REPORTS), "projector manifest original report set differs")
    for name, item in by_name.items():
        data = _read_under(root, item.get("path"), f"pinned source report {name}")
        _check_sha(data, item.get("sha256"), f"pinned source report {name}")
    return {
        "path": PROJECTOR_REL.as_posix(),
        "sha256": PROJECTOR_SHA256,
        "manifest_path": PROJECTOR_MANIFEST_REL.as_posix(),
        "manifest_sha256": PROJECTOR_MANIFEST_SHA256,
        "manifest": manifest,
    }


def _prepare_projection(root: Path, checkout: Path, failed: dict, schema: dict, projector: ModuleType) -> tuple[list[dict], dict]:
    report_map = {PurePosixPath(item["validation_path"]).name: item for item in failed["reports"]}
    _require(set(JOERN_REPORTS) <= set(report_map), "metadata03 receipt does not bind the exact five Joern outputs")
    projected_reports: list[dict] = []
    sidecar_reports: list[dict] = []
    allowed_top = set(schema.get("properties", {}))
    _require("results" in allowed_top, "result schema has no results property")
    for name in JOERN_REPORTS:
        binding = report_map[name]
        rel = _safe_relative(binding["validation_path"], "Joern validation report")
        _require(rel == PurePosixPath("reports") / name,
                 f"unexpected Joern validator destination: {rel.as_posix()}")
        original_checkout_bytes = _read_under(checkout, rel.as_posix(), f"metadata03 Joern checkout report {name}")
        _check_sha(original_checkout_bytes, binding["sha256"], f"metadata03 Joern checkout report {name}")
        source_rel = _safe_relative(binding.get("source_path"), "original C6 Joern report source")
        source_bytes = _read_under(root, source_rel.as_posix(), f"original C6 Joern source report {name}")
        _check_sha(source_bytes, binding["sha256"], f"original C6 Joern source report {name}")
        _require(source_bytes == original_checkout_bytes,
                 f"metadata03 Joern checkout report differs from its retained C6 source: {name}")
        try:
            original = json.loads(source_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GateError(f"metadata03 Joern report is invalid JSON: {name}") from exc
        _require(isinstance(original, dict) and isinstance(original.get("results"), list),
                 f"metadata03 Joern report has invalid shape: {name}")
        _schema_shape(original, schema, allow_joern_metadata=True)
        _require(original.get("aggregate_resource_qualification") == "unavailable" and
                 original.get("scored_activation") is False,
                 f"Joern report qualification state drifted: {name}")
        canonical, sidecar = projector.project_report(original, checkout, schema)
        _require(isinstance(canonical, dict) and isinstance(sidecar, dict),
                 f"Joern projector returned malformed output for {name}")
        _schema_shape(canonical, schema, allow_joern_metadata=False)
        _assert_only_metadata_moved(original, canonical)
        restored = projector.reconstruct_report(canonical, sidecar)
        _require(restored == original,
                 f"Joern sidecar cannot reconstruct the exact producer report: {name}")
        canonical_bytes = _json_bytes(canonical)
        _require(json.loads(canonical_bytes) == canonical,
                 f"projected Joern report is not stable JSON: {name}")
        projected_reports.append({
            "path": rel.as_posix(),
            "source_path": source_rel.as_posix(),
            "source_sha256": _sha(source_bytes),
            "projected_sha256": _sha(canonical_bytes),
            "rows": len(original["results"]),
            "removed_top_level_fields": list(TOP_LEVEL_MOVED_FIELDS),
            "removed_result_row_field": ROW_MOVED_FIELD,
            "sidecar": sidecar,
            "sidecar_sha256": _sha(_canonical_json(sidecar)),
            "canonical": canonical,
        })
        sidecar_reports.append({
            "report_path": rel.as_posix(),
            "source_path": source_rel.as_posix(),
            "source_sha256": _sha(source_bytes),
            "projected_sha256": _sha(canonical_bytes),
            "sidecar": sidecar,
            "sidecar_sha256": _sha(_canonical_json(sidecar)),
        })
    _require(sum(item["rows"] for item in projected_reports) == EXPECTED_JOERN_ROWS,
             "five Joern partitions do not contain exactly 108 rows")
    sidecar_doc = {
        "schema": "dataflowbench-joern-metadata-sidecar-bundle/v1",
        "projection_kind": "schema-compatible-report-metadata-relocation",
        "schema_path": SCHEMA_REL.as_posix(),
        "schema_sha256": SCHEMA_SHA256,
        "projector_path": PROJECTOR_REL.as_posix(),
        "projector_sha256": PROJECTOR_SHA256,
        "reports": sidecar_reports,
        "qualification": {
            "aggregate_resource_qualification": "unavailable",
            "scored_activation": False,
            "timing_certified": False,
            "publication_approved": False,
        },
    }
    return projected_reports, sidecar_doc


def _collect_baseline_context(root: Path) -> dict:
    """Verify the immutable metadata03 evidence and return the exact source inventory."""
    old_checkout = root / Path(*OLD_CHECKOUT_REL.parts)
    failed_binding = _verify_old_failure(root)
    failed = failed_binding["receipt_json"]
    ref_manifest, ref_manifest_bytes = _read_json_under(root, REF_MANIFEST_REL, "119-reference repair manifest")
    _check_sha(ref_manifest_bytes, REF_MANIFEST_SHA256, "119-reference repair manifest")
    contract, contract_bytes = _read_json_under(root, C6_CONTRACT_REL, "C6 v0.15.1 contract")
    _require(_git(root, "rev-parse", f"{C6_COMMIT}:{C6_CONTRACT_REL.as_posix()}") == C6_CONTRACT_BLOB_SHA1,
             "C6 contract object does not match plan commit")
    runner_binding = _verify_runner_binding(root, contract, ref_manifest, failed)
    ledger_binding = _verify_contract_and_ledger(root, contract, contract_bytes)
    evidence = _verify_metadata03_evidence(root, failed, ref_manifest)
    helper_identities = failed.get("helper_identities")
    _require(isinstance(helper_identities, dict) and len(helper_identities) == 8,
             "metadata03 receipt does not bind all eight immutable Python helpers")
    for name, item in helper_identities.items():
        _require(isinstance(item, dict) and set(item) == {"path", "sha256"},
                 f"metadata03 helper identity is malformed: {name}")
        data = _read_under(root, item["path"], f"retained validation helper {name}")
        _check_sha(data, item["sha256"], f"retained validation helper {name}")
    validator_bytes = _read_under(root, VALIDATOR_REL.as_posix(), "immutable original validation helper")
    _check_sha(validator_bytes, VALIDATOR_SHA256, "immutable original validation helper")
    schema_bytes = _read_under(root, SCHEMA_REL.as_posix(), "production Rust result schema")
    _check_sha(schema_bytes, SCHEMA_SHA256, "production Rust result schema")
    schema = json.loads(schema_bytes)
    _require(schema.get("additionalProperties") is False,
             "production result schema must remain closed to undeclared top-level properties")
    projector_info = _projector_identity(root)
    projector = _load_exact_module(root / Path(*PROJECTOR_REL.parts),
                                   "joern_v092_canonical_schema01_projector", PROJECTOR_SHA256)
    inventory = _file_inventory(old_checkout)
    diagnosis = {
        "schema": "dataflowbench-v0151-configurations03-baseline-diagnosis/v1",
        "status": "metadata03-failure-and-source-inputs-verified",
        "canonical_invocation_performed_by_this_diagnosis": False,
        "source": {
            "commit": SOURCE_COMMIT,
            "tree_sha1": SOURCE_TREE_SHA1,
            "c6_plan_commit": C6_COMMIT,
            "c6_contract": {"path": C6_CONTRACT_REL.as_posix(), "sha256": C6_CONTRACT_SHA256,
                            "git_blob_sha1": C6_CONTRACT_BLOB_SHA1},
            "full_runner_binding": runner_binding,
            "full_runner_binding_canonical_json_sha256": RUNNER_CANONICAL_JSON_SHA256,
            "ledger": ledger_binding,
        },
        "metadata03_failure": {
            "receipt": failed_binding["receipt"],
            "stdout": failed_binding["stdout"],
            "stderr": failed_binding["stderr"],
            "status": failed_binding["status"],
            "exit_code": failed_binding["exit_code"],
            "metrics": failed_binding["metrics"],
            "stdout_parse_error": failed_binding["stdout_parse_error"],
        },
        "metadata03_evidence": evidence,
        "configuration_reference_manifest": {
            "path": REF_MANIFEST_REL.as_posix(),
            "sha256": REF_MANIFEST_SHA256,
            "unique_reference_count": EXPECTED_CONFIG_REFS,
            "references": [{"path": item["path"], "sha256": item["sha256"]}
                           for item in ref_manifest["references"]],
        },
        "validator_helpers": helper_identities,
        "immutable_validator": {"path": VALIDATOR_REL.as_posix(), "sha256": VALIDATOR_SHA256},
        "production_schema": {"path": SCHEMA_REL.as_posix(), "sha256": SCHEMA_SHA256,
                              "additional_properties": False},
        "joern_projector": {key: value for key, value in projector_info.items() if key != "manifest"},
        "joern_projector_manifest": projector_info["manifest"],
        "checkout_inventory": inventory,
    }
    return {
        "diagnosis": diagnosis,
        "failed_binding": failed_binding,
        "failed": failed,
        "ref_manifest": ref_manifest,
        "contract": contract,
        "runner_binding": runner_binding,
        "ledger_binding": ledger_binding,
        "evidence": evidence,
        "helper_identities": helper_identities,
        "schema": schema,
        "projector_info": projector_info,
        "projector": projector,
        "inventory": inventory,
    }


def diagnose(root: str | Path = ROOT) -> dict:
    """Write the static, hash-bound metadata03 baseline diagnosis without creating04."""
    root = Path(root).resolve(strict=True)
    context = _collect_baseline_context(root)
    DIAGNOSIS_DIR.mkdir(parents=True, exist_ok=True)
    _require(not DIAGNOSIS_DIR.is_symlink(), "diagnosis directory is a symlink")
    diagnosis_bytes = _json_bytes(context["diagnosis"])
    diagnosis_path = DIAGNOSIS_DIR / "baseline-diagnosis.json"
    _write_new(diagnosis_path, diagnosis_bytes)
    return {"status": context["diagnosis"]["status"],
            "diagnosis_path": str(diagnosis_path.relative_to(root)),
            "diagnosis_sha256": _sha(diagnosis_bytes),
            "checkout_files": context["inventory"]["file_count"],
            "checkout_bytes": context["inventory"]["total_file_bytes"],
            "configuration_refs": context["evidence"]["configuration_inputs"]["unique_references"],
            "reports": context["evidence"]["reports"]["count"],
            "raw_outputs": context["evidence"]["raw_outputs"]["count"],
            "canonical_invocation_performed": False}


def prepare(root: str | Path = ROOT) -> dict:
    root = Path(root).resolve(strict=True)
    old_checkout = root / Path(*OLD_CHECKOUT_REL.parts)
    new_checkout = root / Path(*NEW_CHECKOUT_REL.parts)
    _require(not new_checkout.exists() and not new_checkout.is_symlink(),
             f"fresh configurations-04 checkout already exists: {new_checkout}")
    _require(not (root / Path(*NEW_RECEIPT_REL.parts)).exists(),
             "configurations-04 canonical receipt namespace already exists")
    context = _collect_baseline_context(root)
    baseline_diagnosis_path = DIAGNOSIS_DIR / "baseline-diagnosis.json"
    baseline_diagnosis_bytes = _read_under(root, baseline_diagnosis_path.relative_to(root).as_posix(),
                                           "reviewed metadata03 baseline diagnosis")
    _require(baseline_diagnosis_bytes == _json_bytes(context["diagnosis"]),
             "metadata03 baseline diagnosis differs from its reviewed, committed evidence")
    failed_binding = context["failed_binding"]
    failed = context["failed"]
    ref_manifest = context["ref_manifest"]
    runner_binding = context["runner_binding"]
    ledger_binding = context["ledger_binding"]
    evidence = context["evidence"]
    helper_identities = context["helper_identities"]
    schema = context["schema"]
    projector_info = context["projector_info"]
    projector = context["projector"]
    baseline_inventory = context["inventory"]

    # Copy without following links; all source entries were just checked as regular files/directories.
    new_checkout.parent.mkdir(parents=True, exist_ok=True)
    _require(not new_checkout.parent.is_symlink(), "configurations-04 parent is a symlink")
    shutil.copytree(old_checkout, new_checkout, copy_function=shutil.copy2, symlinks=False)
    copy_method = "shutil.copytree(copy2, symlinks=False)"
    copied_inventory = _file_inventory(new_checkout)
    _require(copied_inventory["entries"] == baseline_inventory["entries"],
             "fresh configurations-04 copy differs from metadata03 before projection")

    projected_reports, sidecar_doc = _prepare_projection(root, new_checkout, failed, schema, projector)
    # The projector validates every raw_output binding before we replace the five report files.
    write_set: list[tuple[Path, bytes]] = []
    for report in projected_reports:
        canonical = report["canonical"]
        write_set.append((new_checkout / Path(*PurePosixPath(report["path"]).parts), _json_bytes(canonical)))
    _require(len(write_set) == len(JOERN_REPORTS), "projection did not produce exactly five report writes")
    for path, contents in write_set:
        _require(not path.is_symlink() and path.is_file(), f"unsafe projected report destination: {path}")
        mode = stat.S_IMODE(os.lstat(path).st_mode)
        temp = path.with_name(f".{path.name}.schema-projection.tmp")
        _require(not temp.exists() and not temp.is_symlink(), f"projection temporary path collides: {temp}")
        with temp.open("xb") as handle:
            handle.write(contents)
        os.chmod(temp, mode)
        os.replace(temp, path)

    final_inventory = _file_inventory(new_checkout)
    expected_changes = {f"reports/{name}" for name in JOERN_REPORTS}
    diff = _compare_inventories(baseline_inventory, final_inventory, allowed_changed_files=expected_changes)
    for report in projected_reports:
        actual = _read_under(new_checkout, report["path"], "projected configurations-04 report")
        _check_sha(actual, report["projected_sha256"], f"projected configurations-04 report {report['path']}")

    # Recheck the complete input and raw bindings on the finished copy.
    for item in ref_manifest["references"]:
        data = _read_under(new_checkout, item["path"], "final configurations-04 Swift input")
        _check_sha(data, item["sha256"], f"final configurations-04 Swift input {item['path']}")
    for item in failed["raw_files"]:
        data = _read_under(new_checkout, item["relative_path"], "final configurations-04 raw output")
        _require(len(data) == item["bytes"], f"raw output size changed during projection: {item['relative_path']}")
        _check_sha(data, item["sha256"], f"final configurations-04 raw output {item['relative_path']}")

    # Only create new append-only diagnosis outputs after all verification succeeds.
    DIAGNOSIS_DIR.mkdir(parents=True, exist_ok=True)
    _require(not DIAGNOSIS_DIR.is_symlink(), "diagnosis directory is a symlink")
    sidecar_bytes = _json_bytes(sidecar_doc)
    sidecar_path = DIAGNOSIS_DIR / "joern-projection-sidecar.json"
    _write_new(sidecar_path, sidecar_bytes)
    helper_sha = _sha(Path(__file__).read_bytes())
    diagnosis = {
        "schema": "dataflowbench-v0151-configurations04-preparation/v1",
        "status": "prepared-awaiting-canonical-invocation",
        "canonical_invocation_performed": False,
        "source": {
            "commit": SOURCE_COMMIT,
            "tree_sha1": SOURCE_TREE_SHA1,
            "c6_plan_commit": C6_COMMIT,
            "c6_contract_path": C6_CONTRACT_REL.as_posix(),
            "c6_contract_sha256": C6_CONTRACT_SHA256,
            "c6_contract_blob_sha1": C6_CONTRACT_BLOB_SHA1,
            "c6_runner_full_object_sha256": RUNNER_CANONICAL_JSON_SHA256,
            "runner_binding": runner_binding,
            "ledger": ledger_binding,
        },
        "previous_failed_validation": {
            "receipt": failed_binding["receipt"],
            "stdout": failed_binding["stdout"],
            "stderr": failed_binding["stderr"],
            "status": failed_binding["status"],
            "exit_code": failed_binding["exit_code"],
            "metrics": failed_binding["metrics"],
            "stdout_parse_error": failed_binding["stdout_parse_error"],
        },
        "metadata03_verified": evidence,
        "source_copy": {
            "source_checkout": str(old_checkout),
            "destination_checkout": str(new_checkout),
            "copy_method": copy_method,
            "before_projection_inventory_sha256": baseline_inventory["entries_sha256"],
            "before_projection_copy_identical": True,
            "after_projection_inventory_sha256": final_inventory["entries_sha256"],
            "allowed_report_changes": sorted(expected_changes),
            "all_other_paths_unchanged": diff["unchanged_path_and_mode_count"],
            "inventory_artifact": {
                "path": str(baseline_diagnosis_path.relative_to(ROOT)),
                "sha256": _sha(baseline_diagnosis_bytes),
            },
            "inventory": {"source": _inventory_for_receipt(baseline_inventory), "final_copy": _inventory_for_receipt(final_inventory)},
        },
        "projection": {
            "schema_path": SCHEMA_REL.as_posix(),
            "schema_sha256": SCHEMA_SHA256,
            "projector": {key: value for key, value in projector_info.items() if key != "manifest"},
            "sidecar": {"path": str(sidecar_path.relative_to(ROOT)), "sha256": _sha(sidecar_bytes)},
            "report_count": len(projected_reports),
            "row_count": sum(item["rows"] for item in projected_reports),
            "reports": [{key: value for key, value in item.items() if key not in ("sidecar", "canonical")} for item in projected_reports],
            "only_removed_fields": {"top_level": list(TOP_LEVEL_MOVED_FIELDS), "each_result_row": ROW_MOVED_FIELD},
            "qualification_and_scoring_unchanged": True,
        },
        "immutable_validator": {"path": VALIDATOR_REL.as_posix(), "sha256": VALIDATOR_SHA256,
                                "runner_timeout_seconds": TIMEOUT_SECONDS},
        "helper_sha256": helper_sha,
    }
    diagnosis_bytes = _json_bytes(diagnosis)
    diagnosis_path = DIAGNOSIS_DIR / "preparation-diagnosis.json"
    _write_new(diagnosis_path, diagnosis_bytes)
    return {
        "status": diagnosis["status"],
        "checkout": str(new_checkout),
        "diagnosis_path": str(diagnosis_path),
        "diagnosis_sha256": _sha(diagnosis_bytes),
        "projection_report_count": len(projected_reports),
        "projection_row_count": diagnosis["projection"]["row_count"],
        "canonical_invocation_performed": False,
    }


def _load_original_validator(root: Path) -> ModuleType:
    path = root / Path(*VALIDATOR_REL.parts)
    return _load_exact_module(path, "v092_immutable_validator_for_configurations04", VALIDATOR_SHA256)


def _verify_invocation_review(root: Path) -> dict:
    review, review_bytes = _read_json_under(root, INDEPENDENT_REVIEW_REL, "canonical-schema independent review")
    _require(review.get("schema") == "v0.9.2-v0151-canonical-schema-independent-review/v1" and
             review.get("review_id") == "bifrost-v0151-canonical-schema-01-independent-review-01" and
             review.get("status") == "passed-for-root-integration-review" and
             review.get("findings") == [] and review.get("canonical_invocation_authorized") is False,
             "independent review is absent, incomplete, or does not have its exact root-review status")
    reviewed = review.get("reviewed_artifacts_sha256")
    _require(isinstance(reviewed, dict), "independent review lacks its exact artifact hash map")
    required = (
        Path(__file__).resolve().relative_to(root).as_posix(),
        "reports/releases/v0.9.2/validation/bifrost-v0151-canonical-schema-01/tests/test_run_canonical.py",
        "reports/releases/v0.9.2/validation/bifrost-v0151-canonical-schema-01/diagnosis/baseline-diagnosis.json",
        PROJECTOR_REL.as_posix(),
        PROJECTOR_MANIFEST_REL.as_posix(),
        SCHEMA_REL.as_posix(),
    )
    for rel in required:
        actual = _sha(_read_under(root, rel, f"reviewed artifact {rel}"))
        bound = reviewed.get(rel)
        if bound is None:
            bound = reviewed.get(str(root / rel))
        _require(bound == actual, f"independent review hash is missing or stale for {rel}")
    # The runtime code and review evidence must be committed before the root opts in.
    commit_paths = set(required) | {INDEPENDENT_REVIEW_REL.as_posix()}
    for rel in sorted(commit_paths):
        _git(root, "ls-files", "--error-unmatch", rel)
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--", rel], cwd=root, text=True,
        )
        _require(status == "", f"reviewed invocation artifact is not committed and clean: {rel}")
    return {"path": INDEPENDENT_REVIEW_REL.as_posix(), "sha256": _sha(review_bytes),
            "status": review["status"], "review_id": review["review_id"]}


def invoke(root: str | Path = ROOT, *, prepared_diagnosis_sha256: str) -> dict:
    root = Path(root).resolve(strict=True)
    diagnosis_path = DIAGNOSIS_DIR / "preparation-diagnosis.json"
    diagnosis, diagnosis_bytes = _read_json_under(root, diagnosis_path.relative_to(root).as_posix(),
                                                  "configurations-04 preparation diagnosis")
    _check_sha(diagnosis_bytes, prepared_diagnosis_sha256, "root-approved configurations-04 preparation diagnosis")
    _require(diagnosis.get("status") == "prepared-awaiting-canonical-invocation" and
             diagnosis.get("canonical_invocation_performed") is False,
             "configurations-04 preparation diagnosis is not an unexecuted preparation")
    current_helper = Path(__file__).read_bytes()
    _check_sha(current_helper, diagnosis.get("helper_sha256"), "sealed canonical-schema helper")
    review = _verify_invocation_review(root)
    _check_sha(_read_under(root, VALIDATOR_REL.as_posix(), "immutable original validator"),
               VALIDATOR_SHA256, "immutable original validator")
    _check_sha(_read_under(root, SCHEMA_REL.as_posix(), "production result schema"),
               SCHEMA_SHA256, "production result schema")
    checkout = root / Path(*NEW_CHECKOUT_REL.parts)
    _require(checkout.is_dir() and not checkout.is_symlink(), "prepared configurations-04 checkout is missing")
    _require(not (root / Path(*NEW_RECEIPT_REL.parts)).exists(),
             "canonical configurations-04 result receipt already exists")
    # Fail if the reviewed prepared checkout drifted after its preparation record.
    inventory_path = DIAGNOSIS_DIR / "baseline-diagnosis.json"
    inv_doc, inv_bytes = _read_json_under(root, inventory_path.relative_to(root).as_posix(),
                                          "configurations-03 source inventory diagnosis")
    _check_sha(inv_bytes, diagnosis["source_copy"]["inventory_artifact"]["sha256"],
               "configurations-03 source inventory artifact")
    _require(inv_doc.get("checkout_inventory", {}).get("entries_sha256") ==
             diagnosis["source_copy"]["before_projection_inventory_sha256"],
             "committed metadata03 inventory does not match the sealed source-copy baseline")
    final_inventory = _file_inventory(checkout)
    expected_digest = diagnosis["source_copy"]["inventory"]["final_copy"]["entries_sha256"]
    _require(final_inventory["entries_sha256"] == expected_digest,
             "prepared configurations-04 checkout drifted since independent review")
    # Rebind the full C6 runner object at invocation time; never pass the old receipt's two-field view.
    contract, contract_bytes = _read_json_under(root, C6_CONTRACT_REL, "C6 contract at invocation")
    ref_manifest, _ = _read_json_under(root, REF_MANIFEST_REL, "119-reference manifest at invocation")
    failed, _ = _read_json_under(root, OLD_RECEIPT_REL, "metadata03 receipt at invocation")
    _verify_contract_and_ledger(root, contract, contract_bytes)
    _projector_identity(root)
    _check_sha(_read_under(root, REF_MANIFEST_REL.as_posix(), "119-reference manifest at invocation"),
               REF_MANIFEST_SHA256, "119-reference manifest at invocation")
    _check_sha(_read_under(root, OLD_RECEIPT_REL.as_posix(), "metadata03 receipt at invocation"),
               FAILED_RECEIPT_SHA256, "metadata03 receipt at invocation")
    runner = _verify_runner_binding(root, contract, ref_manifest, failed)
    helper_identities = failed.get("helper_identities")
    _require(isinstance(helper_identities, dict) and len(helper_identities) == 8,
             "metadata03 immutable helper identity set changed before invocation")
    for name, item in helper_identities.items():
        helper_bytes = _read_under(root, item["path"], f"immutable validator dependency {name}")
        _check_sha(helper_bytes, item["sha256"], f"immutable validator dependency {name}")
    validator = _load_original_validator(root)
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(checkout),
        "TMPDIR": str(checkout),
        "LANG": "C",
        "LC_ALL": "C",
        "NO_COLOR": "1",
    }
    receipt_directory = root / Path(*NEW_RECEIPT_DIR_REL.parts)
    _require(not receipt_directory.exists() and not receipt_directory.is_symlink(),
             "canonical configurations-04 receipt namespace is already allocated")
    receipt_directory.mkdir(parents=True, exist_ok=False)
    expected_argv = [runner["path"], "--population", "v0.9.0", "validate-reports"]
    invocation_exception = None
    try:
        invocation = validator._invoke_runner(runner, checkout, environment, timeout_seconds=TIMEOUT_SECONDS)
    except Exception as exc:
        invocation_exception = f"{type(exc).__name__}: {exc}"
        invocation = {
            "argv": None,
            "cwd": None,
            "environment": None,
            "exit_code": None,
            "timed_out": False,
            "stdout": b"",
            "stderr": b"",
            "duration_seconds": 0.0,
            "invocation_error": invocation_exception,
        }
    # Persist the returned process streams before any post-run verification can fail.
    stdout = invocation["stdout"]
    stderr = invocation["stderr"]
    _write_new(receipt_directory / "stdout.bin", stdout)
    _write_new(receipt_directory / "stderr.bin", stderr)
    invocation_matches = (
        invocation.get("argv") == expected_argv and
        invocation.get("cwd") == str(checkout) and
        invocation.get("environment") == environment
    )
    metrics = None
    parse_error = None
    try:
        metrics = validator._parse_stdout(invocation["stdout"])
    except validator.ValidationEvidenceError as exc:
        parse_error = str(exc)
    postcheck_errors = []
    try:
        current_inventory = _file_inventory(checkout)
        if current_inventory["entries_sha256"] != expected_digest:
            postcheck_errors.append("canonical validator modified the prepared source/report checkout")
    except Exception as exc:
        current_inventory = None
        postcheck_errors.append(f"post-invocation checkout inventory failed: {type(exc).__name__}: {exc}")
    runner_sha256_after = None
    try:
        runner_sha256_after = _sha(Path(runner["path"]).read_bytes())
        if runner_sha256_after != RUNNER_SHA256:
            postcheck_errors.append("bound Rust runner bytes changed during canonical validation")
    except OSError as exc:
        postcheck_errors.append(f"post-invocation runner hash failed: {type(exc).__name__}: {exc}")
    passed = bool(invocation_matches and not invocation_exception and
                  not invocation["invocation_error"] and not postcheck_errors and
                  runner_sha256_after == RUNNER_SHA256 and metrics is not None and
                  validator._validation_success(invocation["exit_code"], metrics))
    status = "canonical-validation-passed" if passed else "failed"
    receipt = {
        "schema": "dataflowbench-v092-canonical-schema-validation/v1",
        "status": status,
        "release": "v0.9.2",
        "namespace": NEW_NAMESPACE,
        "preparation_diagnosis": {
            "path": str(diagnosis_path.relative_to(root)),
            "sha256": _sha(diagnosis_bytes),
        },
        "previous_failed_validation": {
            "receipt_path": OLD_RECEIPT_REL.as_posix(),
            "receipt_sha256": FAILED_RECEIPT_SHA256,
            "failure_preserved": True,
        },
        "source_identity": diagnosis["source"]["commit"],
        "source_tree_sha1": diagnosis["source"]["tree_sha1"],
        "c6_contract": {
            "path": C6_CONTRACT_REL.as_posix(),
            "sha256": C6_CONTRACT_SHA256,
            "git_blob_sha1": C6_CONTRACT_BLOB_SHA1,
            "plan_commit": C6_COMMIT,
        },
        "runner_binding": runner,
        "runner_full_object_canonical_json_sha256": RUNNER_CANONICAL_JSON_SHA256,
        "argv": invocation["argv"],
        "cwd": invocation["cwd"],
        "environment": invocation["environment"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "exit_code": invocation["exit_code"],
        "timed_out": invocation["timed_out"],
        "duration_seconds": invocation["duration_seconds"],
        "runner_sha256_after": runner_sha256_after,
        "stdout": {"path": "stdout.bin", "sha256": _sha(stdout), "bytes": len(stdout),
                   "utf8": stdout.decode("utf-8", errors="replace")},
        "stderr": {"path": "stderr.bin", "sha256": _sha(stderr), "bytes": len(stderr),
                   "utf8": stderr.decode("utf-8", errors="replace")},
        "metrics": metrics,
        "stdout_parse_error": parse_error,
        "invocation_error": invocation["invocation_error"],
        "invocation_exception": invocation_exception,
        "invocation_matches_pinned_argv_cwd_environment": invocation_matches,
        "postcheck_errors": postcheck_errors,
        "independent_review": review,
        "validation_gate": {
            "original_validator_path": VALIDATOR_REL.as_posix(),
            "original_validator_sha256": VALIDATOR_SHA256,
            "expected_reports": EXPECTED_REPORTS,
            "required_known_stale": 0,
            "passed": passed,
        },
        "projection": diagnosis["projection"],
        "post_invocation_checkout_inventory_sha256": current_inventory["entries_sha256"] if current_inventory else None,
    }
    receipt_bytes = _json_bytes(receipt)
    _write_new(receipt_directory / "receipt.json", receipt_bytes)
    return {"status": status, "exit_code": invocation["exit_code"], "metrics": metrics,
            "receipt": str((receipt_directory / "receipt.json").relative_to(root)),
            "receipt_sha256": _sha(receipt_bytes)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diagnose-only", action="store_true",
                      help="verify and seal metadata03 evidence without creating configurations04")
    mode.add_argument("--prepare", action="store_true", help="verify metadata03 and prepare configurations04 only")
    mode.add_argument("--invoke", action="store_true",
                      help="invoke only from an independently reviewed sealed preparation")
    parser.add_argument("--prepared-diagnosis-sha256",
                        help="root-confirmed SHA-256 of the exact prepared configurations04 diagnosis")
    args = parser.parse_args(argv)
    try:
        if args.invoke:
            _require(args.prepared_diagnosis_sha256 is not None,
                     "--invoke requires the root-confirmed --prepared-diagnosis-sha256")
            result = invoke(args.root, prepared_diagnosis_sha256=args.prepared_diagnosis_sha256)
        elif args.diagnose_only:
            _require(args.prepared_diagnosis_sha256 is None,
                     "--prepared-diagnosis-sha256 is valid only with --invoke")
            result = diagnose(args.root)
        else:
            _require(args.prepared_diagnosis_sha256 is None,
                     "--prepared-diagnosis-sha256 is valid only with --invoke")
            result = prepare(args.root)
    except (GateError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"canonical schema gate failed closed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") in (
        "metadata03-failure-and-source-inputs-verified",
        "prepared-awaiting-canonical-invocation",
        "canonical-validation-passed",
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
