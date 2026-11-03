#!/usr/bin/env python3
"""Append-only replay/finalization of one reviewed native Joern controls capture.

This is a post-capture reader. It never invokes Joern, a provider, or a native
qualification wrapper. It accepts only an exact future request, invocation
review, successful native exit, control result, bounded JVM sidecar manifest,
and independent capture review. It then replays the real v0.9.2 control
assessment and diagnostic admission before it can write a new eligible plan.
"""

from __future__ import annotations

import argparse
import base64
import builtins
import copy
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import types
from contextlib import ExitStack
from typing import Any


ROOT = Path(__file__).resolve().parents[6]
SOURCE = "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/native-finalization-03/native_finalizer.py"
NATIVE_WRAPPER = "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py"
NATIVE10_SOURCE_SHA256 = {
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py": "5f513fe20ff23e3f2fed6f32adb311e3cfa77ab43b56b50b13a0251969777f42",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py": "7c0ef87663df318cbd4136d3d56bb17c3e3222294e321a3f853846e372368788",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py": "8be67e915b74105f89377b86cefb067b78573850b8e439377cb530e93c7197c9",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py": "ea8fa4268477a4411c55d44c1704f132d8b0b8b4b9bf0f722b4afd404f9bbe08",
}
NATIVE10_EXPECTED_OBSERVER = {
    "path": "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-07.py",
    "sha256": "4e3998dfb3f32b5d377c8697ea644d247f147220679eb784cc64fc501f7bc199",
}
POST_CAPTURE_COMMAND_OBSERVER = {
    "path": "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py",
    "sha256": "5d39a7931cdaa690566b7587142ed9abd2b44ffaf38d51a403028653a40e85b1",
}
COMMAND_PATH_HELPER = {
    "path": "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/command-path-amendment-01/command_path_amendment_01.py",
    "sha256": "9762b02eb4f8683800bc4b7358de668ba381fdf7d093acc42058c104696460f5",
}
NATIVE08_CAPTURE_RUN_PATH = (
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
    "native-controls-08/capture/run.json"
)
NATIVE08_REQUEST_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json",
    "sha256": "a444c55cf107d64089ed1470d56b3db7dd64e00d683c2278b0b62937a1bb75df",
}
NATIVE08_CONTROL_RESULT_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08/control-result.json",
    "sha256": "7701390bd9860147f0d3c654183d5220cf742824f83261251ff5cda13c1f2ba9",
}
NATIVE08_WORKER_INVOCATION_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08/worker-invocation.json",
    "sha256": "9438ed1365c5fea1737f7da22e9f30516f65565232e7b69e8835ecd70e27c81e",
}
NATIVE08_WORKER_ENVIRONMENT_SHA256 = "19f5ec0b18b4200e21d14c9b488ffb9737b02ec273af43ae9d5f31874dd0dc2a"
RETAINED_CONTROL_RUN_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-04/run.json",
    "sha256": "a4f68131bce1b79151ad361a2e05b861f37a1c43f74d1fcb660d4082f9bf4ada",
}
NATIVE08_SOURCE_HEAD = "ab5c8ade58b789957e48de29ca54f432457611c1"
NATIVE08_CONTROL_PLAN = {
    "path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/control-plan-01.json",
    "sha256": "05d8b63d78df07ad4a66b4609573ffd051f5b44cf0416f316aab7b2dc9755a2f",
}
NATIVE08_PATH_DELTA_SCHEMA = "v092-joern-native08-command-input-delta/v1"
NATIVE08_PATH_DELTA_STATUS = "semantic-only-PATH-delta-verified"
NATIVE08_OLD_PATH_SHA256 = "7c96ef759a4f8c588dde51712ab0690953d7add50968baa594a42ca9925e1f07"
NATIVE08_SANITIZED_PATH = (
    "/Users/dave/.sdkman/candidates/java/21.0.8-tem/bin:/opt/homebrew/bin:"
    "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
)
NATIVE08_SANITIZED_PATH_SHA256 = "f199a21ab656a5d5f6191757fc6982fbb94334a163f17143ccadef8d6e2763c2"
NATIVE10_PENDING_PLAN = {
    "path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/pending-execution-plan-01.json",
    "sha256": "09d6748e23b670dbd8998a9f5f80075a25f4b388788004f36fd8b279bec5533e",
}
NATIVE10_REQUEST_FIELDS = {
    "schema", "expected_head", "ledger", "observer", "pending_plan", "control_plan",
    "evidence", "agent_jar", "agent_source", "design", "source_review",
    "decision_review", "authority", "source_refs", "namespace", "tool_refs",
    "native_provider",
}
DIAGNOSTIC = "scripts/joern_diagnostic_admission_v092.py"
SCRIPTS = "scripts"
QUALIFICATION_ROOT = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/"
VALIDATION_ROOT = "reports/releases/v0.9.2/validation/"
NATIVE_CAPTURE_VALIDATION_ROOT = "reports/releases/v0.9.2/validation/joern-current130-01/"
CAPTURE_REVIEW_SCHEMA = "v092-native-capture-independent-review/v1"
SIDECAR_MANIFEST_SCHEMA = "v092-joern-startup-sidecar-manifest/v1"
PREPARED_FINALIZATION_SCHEMA = "v092-joern-post-capture-finalization-prepared/v1"
SEMANTIC_SCOPE = {
    "evaluation_scope": "semantic-only",
    "uncontended_timing_certified": False,
    "relative_performance_conclusions_authorized": False,
}
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
LEDGER_SHA256 = "79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84"
EXPECTED_LEDGER_ROWS = 130
EXPECTED_LEDGER_COUNTS = {"completed": 122, "failed": 3, "recorder-error": 5}
EXPECTED_TOOL_VERSION = "4.0.660"
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_EXIT_BYTES = 32 * 1024 * 1024
MAX_CONTROL_RESULT_BYTES = 16 * 1024 * 1024
MAX_REVIEW_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_STARTUP_EVENTS = 256
MAX_WITNESSES = 2048
MAX_SIDECAR_BYTES = 2 * 1024 * 1024
MAX_WITNESS_BYTES = 1024 * 1024
MAX_STARTUP_BYTES = 32 * 1024 * 1024
MAX_NATIVE_SOURCE_BYTES = 4 * 1024 * 1024
# Exact immutable130 payload size; native10/provider03 retain their 256 MiB ceiling.
MAX_LEDGER_BYTES = 126_023_630
MAX_FINALIZED_FILE_BYTES = 64 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
REQUEST_NAME_RE = re.compile(r"native-control-request-(0[8-9]|[1-9][0-9]+)\.json\Z")
NAMESPACE_RE = re.compile(r"native-controls-(0[8-9]|[1-9][0-9]+)\Z")
EVENT_PHASES = {"version", "typecheck", "frontend", "query"}
JVM_FILE_RE = re.compile(r"jvm-[0-9]+\.json\Z")
STARTUP_MANIFEST_REF_RE = re.compile(
    re.escape(NATIVE_CAPTURE_VALIDATION_ROOT) +
    r"native([0-9]{2})-startup-sidecar-manifest-([0-9]{2})\.json\Z"
)
SCRIPT_IMPORT_ALIASES = (
    ("swift_normal_reports_v1", "scripts/swift_normal_reports_v1.py"),
    ("joern_swift", "scripts/joern_swift.py"),
    ("joern_normal_controls_v1", "scripts/joern_normal_controls_v1.py"),
    ("swift_extraction_integrity", "scripts/swift_extraction_integrity.py"),
    ("swift_persistence_coverage", "scripts/swift_persistence_coverage.py"),
    ("swift_v3_reports", "scripts/swift_v3_reports.py"),
    ("swift_v3_runner", "scripts/swift_v3_runner.py"),
    ("swift_v2_process", "scripts/swift_v2_process.py"),
    ("swift_artifact_closure", "scripts/swift_artifact_closure.py"),
    ("swift_normal_runner_v1", "scripts/swift_normal_runner_v1.py"),
    ("swift_common_population_v2", "scripts/swift_common_population_v2.py"),
    ("v092_qualification", "scripts/v092_qualification.py"),
    ("joern_diagnostic_admission_v092", "scripts/joern_diagnostic_admission_v092.py"),
    ("joern_normal_runner_v092", "scripts/joern_normal_runner_v092.py"),
    ("joern_normal_execution_v1", "scripts/joern_normal_execution_v1.py"),
    ("joern_execution_revalidation_v1", "scripts/joern_execution_revalidation_v1.py"),
)


class FinalizationError(ValueError):
    """An input is missing, stale, unbound, or outside the approved scope."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FinalizationError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(_read_stable(path, MAX_FINALIZED_FILE_BYTES, "finalized file"))


def _open_parent_directory(path: Path, description: str) -> tuple[int, str]:
    absolute = Path(os.path.abspath(path))
    require(absolute.is_absolute() and len(absolute.parts) >= 2,
            f"{description} path is malformed")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    require(getattr(os, "O_NOFOLLOW", 0) and getattr(os, "O_DIRECTORY", 0),
            "platform lacks no-follow directory opens")
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:-1]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise FinalizationError(f"{description} has an unsafe or missing path component") from exc
            os.close(descriptor)
            descriptor = child
        return descriptor, absolute.name
    except OSError as exc:
        os.close(descriptor)
        raise FinalizationError(f"{description} parent is unsafe or missing") from exc
    except BaseException:
        os.close(descriptor)
        raise


def _open_directory(path: Path, description: str) -> int:
    absolute = Path(os.path.abspath(path))
    require(absolute.is_absolute(), f"{description} path is malformed")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    require(getattr(os, "O_NOFOLLOW", 0) and getattr(os, "O_DIRECTORY", 0),
            "platform lacks no-follow directory opens")
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise FinalizationError(f"{description} has an unsafe or missing path component") from exc
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError as exc:
        os.close(descriptor)
        raise FinalizationError(f"{description} is unsafe or missing") from exc
    except BaseException:
        os.close(descriptor)
        raise


def _directory_names(path: Path, description: str, *,
                     maximum_entries: int) -> set[str]:
    descriptor = _open_directory(path, description)
    try:
        before = os.fstat(descriptor)
        names = set()
        with os.scandir(descriptor) as entries:
            for entry in entries:
                require(len(names) < maximum_entries,
                        f"{description} exceeds its bounded entry count")
                names.add(entry.name)
        after = os.fstat(descriptor)
        signature = lambda item: (item.st_dev, item.st_ino, item.st_mtime_ns, item.st_ctime_ns)
        require(signature(before) == signature(after), f"{description} changed while listing")
        return names
    finally:
        os.close(descriptor)


def _path_state(path: Path, description: str) -> os.stat_result | None:
    descriptor, name = _open_parent_directory(path, description)
    try:
        try:
            result = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return None
        require(not stat.S_ISLNK(result.st_mode), f"{description} crosses a symlink")
        return result
    finally:
        os.close(descriptor)


def _read_stable(path: Path, maximum: int, description: str,
                 expected_sha256: str | None = None) -> bytes:
    require(type(maximum) is int and maximum > 0, f"{description} size bound is invalid")
    parent_fd, name = _open_parent_directory(path, description)
    descriptor = None
    try:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), f"{description} is not a regular file")
        require(0 < before.st_size <= maximum, f"{description} size exceeds its bound")
        chunks = []
        remaining = maximum + 1
        while remaining:
            block = os.read(descriptor, min(1024 * 1024, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        signature = lambda item: (item.st_dev, item.st_ino, item.st_size,
                                  item.st_mtime_ns, item.st_ctime_ns)
        require(signature(before) == signature(after) and len(raw) == before.st_size,
                f"{description} changed while reading")
        require(len(raw) <= maximum, f"{description} size exceeds its bound")
        require(expected_sha256 is None or sha_bytes(raw) == expected_sha256,
                f"{description} SHA-256 mismatch")
        return raw
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)


def _relative(root: Path, value: object, description: str) -> tuple[str, Path]:
    require(type(value) is str and value and not Path(value).is_absolute(),
            f"{description} must be a repository-relative path")
    rel = Path(value)
    require(rel.as_posix() == value and ".." not in rel.parts,
            f"{description} path is not canonical")
    require(root == root.resolve(), "repository root must be canonical")
    return value, root / rel


def _parse_json(raw: bytes, description: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FinalizationError(f"{description} is not valid JSON") from exc
    require(type(value) is dict, f"{description} must be an object")
    return value


def _read_json(path: Path, maximum: int, description: str,
               expected_sha256: str | None = None) -> tuple[dict[str, Any], bytes]:
    raw = _read_stable(path, maximum, description, expected_sha256)
    value = _parse_json(raw, description)
    return value, raw


def checked_ref(root: Path, relative: object, expected_sha256: object,
                description: str, *, maximum: int = MAX_CONTROL_RESULT_BYTES,
                prefix: str | None = None) -> tuple[dict[str, str], Path, dict[str, Any] | None, bytes]:
    rel, path = _relative(root, relative, description)
    require(type(expected_sha256) is str and SHA256_RE.fullmatch(expected_sha256),
            f"{description} SHA-256 is malformed")
    require(prefix is None or rel.startswith(prefix), f"{description} is outside its approved namespace")
    raw = _read_stable(path, maximum, description, expected_sha256)
    value = _parse_json(raw, description) if path.suffix.lower() == ".json" else None
    return {"path": rel, "sha256": expected_sha256}, path, value, raw


def _check_scope(value: dict[str, Any], description: str) -> None:
    require(all(value.get(k) == v for k, v in SEMANTIC_SCOPE.items()),
            f"{description} changed the semantic-only/performance boundary")


def expected_namespace(request: dict[str, Any], request_ref: dict[str, str]) -> str:
    namespace = request.get("namespace")
    require(type(namespace) is str and NAMESPACE_RE.fullmatch(Path(namespace).name),
            "fresh native-controls-08-or-later namespace required")
    require(Path(namespace).as_posix() == namespace and
            Path(namespace).parent.as_posix() == QUALIFICATION_ROOT.rstrip("/"),
            "native namespace is not canonical")
    require(REQUEST_NAME_RE.fullmatch(Path(request_ref["path"]).name) is not None,
            "historical/unsuccessor request cannot be finalized")
    request_number = int(Path(request_ref["path"]).stem.rsplit("-", 1)[1])
    namespace_number = int(Path(namespace).name.rsplit("-", 1)[1])
    require(request_number == namespace_number,
            "request sequence and native namespace sequence differ")
    require(request_ref["path"].startswith(QUALIFICATION_ROOT),
            "native request is outside the Joern qualification namespace")
    return namespace


def validate_startup_manifest_ref_path(path: str, namespace: str) -> None:
    """Bind manifest metadata to its canonical validation record location.

    The manifest document is stored in validation evidence; its body binds all
    observed files to the exact native namespace and capture root.
    """
    match = STARTUP_MANIFEST_REF_RE.fullmatch(path) if type(path) is str else None
    namespace_match = NAMESPACE_RE.fullmatch(Path(namespace).name)
    require(match is not None and namespace_match is not None and
            match.group(1) == namespace_match.group(1),
            "startup sidecar manifest ref is outside its canonical validation record path")


def _abs_ref_to_relative(root: Path, ref: object, description: str,
                         expected_parent: str) -> dict[str, str]:
    require(type(ref) is dict and set(ref) == {"path", "sha256"},
            f"{description} reference fields differ")
    raw_path = ref["path"]
    require(type(raw_path) is str and Path(raw_path).is_absolute(),
            f"{description} must retain its absolute observer path")
    path = Path(raw_path)
    require(path.as_posix() == raw_path, f"{description} path is not canonical")
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise FinalizationError(f"{description} escaped the repository") from exc
    require(rel == expected_parent or rel.startswith(expected_parent.rstrip("/") + "/"),
            f"{description} is outside the exact capture sidecar tree")
    checked, _path, _, _ = checked_ref(root, rel, ref["sha256"], description,
                                        maximum=MAX_WITNESS_BYTES)
    return checked


def _preflight_regular_file(root: Path, relative: str, maximum: int,
                            description: str) -> os.stat_result:
    _, path = _relative(root, relative, description)
    value = _path_state(path, description)
    require(value is not None and stat.S_ISREG(value.st_mode),
            f"{description} is missing or not a regular file")
    require(0 < value.st_size <= maximum, f"{description} size exceeds its bound")
    return value


def _startup_read_budget(aggregate_size: int, per_file_limit: int,
                         description: str) -> int:
    """Bound each next read by both its file cap and remaining aggregate bytes."""
    remaining = MAX_STARTUP_BYTES - aggregate_size
    require(remaining > 0,
            f"startup aggregate byte bound exhausted before reading {description}")
    return min(per_file_limit, remaining)


def validate_startup_manifest(root: Path, manifest: dict[str, Any], *,
                              namespace: str, capture_root: str,
                              startup_summary: dict[str, Any],
                              expected_policy: dict[str, Any]) -> dict[str, Any]:
    """Check only manifest-listed task-owned files; never recursively scan HOME."""
    required = {"schema", "capture_root", "summary", "events", "witnesses", "home", "predef"}
    require(set(manifest) == required and manifest.get("schema") == SIDECAR_MANIFEST_SCHEMA,
            "startup sidecar manifest schema/fields differ")
    require(manifest.get("capture_root") == capture_root,
            "startup sidecar manifest capture root differs")
    sidecar_root = namespace + "/capture.startup-observation"
    events_root = sidecar_root + "/events"
    home_rel = capture_root + "/jvm-home"
    predef_rel = home_rel + "/.scala-repl-pp.sc"
    require(Path(namespace).as_posix() == namespace and
            Path(namespace).parent.as_posix() == QUALIFICATION_ROOT.rstrip("/") and
            NAMESPACE_RE.fullmatch(Path(namespace).name) is not None and
            capture_root == namespace + "/capture",
            "startup namespace/capture root is not the exact canonical request root")
    for relative, description in ((namespace, "native namespace"),
                                  (capture_root, "native capture root"),
                                  (sidecar_root, "startup sidecar root"),
                                  (events_root, "startup event root"),
                                  (home_rel, "task-owned JVM home")):
        _, directory_path = _relative(root, relative, description)
        directory_fd = _open_directory(directory_path, description)
        os.close(directory_fd)
    _, predef_path = _relative(root, predef_rel, "task-owned Scala predef")
    require(_path_state(predef_path, "task-owned Scala predef") is None,
            "task-owned Scala predef is present or linked")

    phases_from_result = startup_summary.get("phases")
    count_from_result = startup_summary.get("event_count")
    require(type(count_from_result) is int and 0 < count_from_result <= MAX_STARTUP_EVENTS and
            type(phases_from_result) is list and len(phases_from_result) == count_from_result and
            all(type(phase) is str and phase in EVENT_PHASES for phase in phases_from_result),
            "startup result event count/phases are malformed or unbounded")
    events = manifest.get("events")
    witnesses = manifest.get("witnesses")
    require(type(events) is list and len(events) == count_from_result and
            type(witnesses) is list and len(witnesses) <= MAX_WITNESSES,
            "startup manifest event/witness list count differs or exceeds bounds")
    event_directories = []
    for index, phase in enumerate(phases_from_result, 1):
        event_rel = f"{sidecar_root}/{index:03d}-{phase}.json"
        event_dir_rel = f"{events_root}/{index:03d}-{phase}"
        event_ref = events[index - 1]
        require(type(event_ref) is dict and set(event_ref) == {"path", "sha256"} and
                event_ref.get("path") == event_rel and
                SHA256_RE.fullmatch(str(event_ref.get("sha256", ""))),
                "startup event ref differs from its deterministic sidecar path")
        _preflight_regular_file(root, event_rel, MAX_SIDECAR_BYTES, "startup event")
        _, event_dir = _relative(root, event_dir_rel, "startup witness event directory")
        event_fd = _open_directory(event_dir, "startup witness event directory")
        os.close(event_fd)
        event_directories.append(event_dir_rel)
    expected_event_directory_names = {
        Path(relative).name for relative in event_directories
    }
    actual_event_directory_names = _directory_names(
        root / events_root, "startup event root",
        maximum_entries=MAX_STARTUP_EVENTS)
    require(actual_event_directory_names == expected_event_directory_names,
            "startup event root contains missing or unmanifested directories")
    witness_paths: set[str] = set()
    for witness_ref in witnesses:
        require(type(witness_ref) is dict and set(witness_ref) == {"path", "sha256"} and
                type(witness_ref.get("path")) is str and
                SHA256_RE.fullmatch(str(witness_ref.get("sha256", ""))),
                "startup manifest witness ref is malformed")
        witness_rel = witness_ref["path"]
        _, witness_path = _relative(root, witness_rel, "startup JVM witness")
        require(witness_path.parent.relative_to(root).as_posix() in event_directories and
                JVM_FILE_RE.fullmatch(witness_path.name) is not None and
                witness_rel not in witness_paths,
                "startup manifest witness escapes or duplicates an event directory")
        _preflight_regular_file(root, witness_rel, MAX_WITNESS_BYTES, "startup JVM witness")
        witness_paths.add(witness_rel)
    expected_summary_path = sidecar_root + "/summary.json"
    summary_ref = manifest.get("summary")
    require(type(summary_ref) is dict and set(summary_ref) == {"path", "sha256"} and
            summary_ref.get("path") == expected_summary_path and
            SHA256_RE.fullmatch(str(summary_ref.get("sha256", ""))),
            "startup summary ref differs from the deterministic sidecar path")
    summary_file = root / expected_summary_path
    summary_budget = min(MAX_SIDECAR_BYTES, MAX_STARTUP_BYTES)
    _preflight_regular_file(root, expected_summary_path, summary_budget, "startup summary")
    summary, summary_raw = _read_json(summary_file, summary_budget,
                                      "startup summary", summary_ref["sha256"])
    require(set(startup_summary) == set(summary) | {"summary"} and
            {k: v for k, v in startup_summary.items() if k != "summary"} == summary,
            "control result startup summary differs from its retained bytes")
    returned_summary = startup_summary.get("summary")
    require(type(returned_summary) is dict and
            _abs_ref_to_relative(root, returned_summary, "control result startup summary",
                                 sidecar_root) == summary_ref,
            "control result does not bind the exact startup summary")
    require(summary.get("schema") == "v092-joern-native-startup-observation-summary/v7" and
            summary.get("status") == "startup-agent-observed" and
            summary.get("qualification_safe") is True and
            summary.get("property_witness", {}).get("status") == "exact-in-process-System.getProperty" and
            summary.get("policy") == expected_policy and
            summary.get("sidecar_root") == str(root / sidecar_root),
            "startup summary does not prove the exact safe JVM startup policy")
    phases = summary.get("phases")
    event_count = summary.get("event_count")
    require(event_count == count_from_result and phases == phases_from_result,
            "startup event count/phases are malformed or unbounded")
    expected_event_refs = []
    expected_witness_refs: list[dict[str, str]] = []
    aggregate_size = len(summary_raw)
    require(aggregate_size <= MAX_STARTUP_BYTES,
            "startup summary exceeds its aggregate byte bound")
    seen_witness_paths: set[str] = set()
    expected_sidecar_names = {"summary.json", "events"}
    for index, phase in enumerate(phases, 1):
        rel = f"{sidecar_root}/{index:03d}-{phase}.json"
        expected_sidecar_names.add(f"{index:03d}-{phase}.json")
        event_path = root / rel
        event_ref = events[index - 1]
        event_budget = _startup_read_budget(aggregate_size, MAX_SIDECAR_BYTES,
                                            "startup sidecar")
        _preflight_regular_file(root, rel, event_budget, "startup sidecar")
        event, event_raw = _read_json(event_path, event_budget,
                                      "startup sidecar", event_ref["sha256"])
        event_size = len(event_raw)
        aggregate_size += event_size
        require(aggregate_size <= MAX_STARTUP_BYTES,
                "startup sidecar manifest expands beyond its aggregate byte bound")
        event_sha = event_ref["sha256"]
        expected_event_refs.append({"path": rel, "sha256": event_sha})
        property_status = event.get("property_witness", {}).get("status")
        event_witnesses = event.get("jvm_witnesses")
        phase_witness_valid = (
            phase == "typecheck" and event_witnesses == [] and property_status == "unavailable"
        ) or (
            phase in {"frontend", "query"} and type(event_witnesses) is list and
            len(event_witnesses) > 0 and property_status == "exact-in-process-System.getProperty"
        ) or (
            phase == "version" and type(event_witnesses) is list and
            property_status in {"unavailable", "exact-in-process-System.getProperty"}
        )
        require(event.get("schema") == "v092-joern-native-startup-receipt/v7" and
                event.get("phase") == phase and event.get("error") is None and
                event.get("violations") == [] and
                phase_witness_valid and
                event.get("predef_before", {}).get("present") is False and
                event.get("predef_before", {}).get("symlink") is False and
                event.get("predef_after", {}).get("present") is False and
                event.get("predef_after", {}).get("symlink") is False,
                f"startup sidecar is unsafe or failed: {rel}")
        event_dir_rel = f"{sidecar_root}/events/{index:03d}-{phase}"
        event_dir = root / event_dir_rel
        require(event.get("event_witness_directory") == str(event_dir),
                "startup sidecar event directory differs from the deterministic path")
        require(type(event_witnesses) is list and len(event_witnesses) <= 128,
                "startup sidecar JVM witness list is malformed or unbounded")
        expected_witness_names: set[str] = set()
        for witness in event_witnesses:
            ref = _abs_ref_to_relative(root, {"path": witness.get("path"),
                                                "sha256": witness.get("sha256")},
                                       "JVM witness", event_dir_rel)
            require(JVM_FILE_RE.fullmatch(Path(ref["path"]).name) is not None and
                    ref["path"] not in seen_witness_paths,
                    "JVM witness path is malformed or duplicated")
            seen_witness_paths.add(ref["path"])
            expected_witness_names.add(Path(ref["path"]).name)
            witness_path = root / ref["path"]
            witness_budget = _startup_read_budget(aggregate_size, MAX_WITNESS_BYTES,
                                                  "startup JVM witness")
            _preflight_regular_file(root, ref["path"], witness_budget,
                                    "startup JVM witness")
            witness_value, witness_raw = _read_json(witness_path, witness_budget,
                                                   "JVM witness", ref["sha256"])
            aggregate_size += len(witness_raw)
            require(aggregate_size <= MAX_STARTUP_BYTES,
                    "startup sidecar manifest expands beyond its aggregate byte bound")
            try:
                witnessed_home = base64.b64decode(witness_value.get("user_home_b64", ""),
                                                  validate=True).decode("utf-8")
                witnessed_predef = base64.b64decode(witness_value.get("predef_path_b64", ""),
                                                    validate=True).decode("utf-8")
            except (ValueError, UnicodeDecodeError) as exc:
                raise FinalizationError("JVM witness home/predef bytes are malformed") from exc
            require(witness_value.get("schema") == "v092-joern-jvm-startup-witness/v5" and
                    witness_value.get("predef_present") is False and
                    witness_value.get("predef_symlink") is False and
                    witness.get("user_home") == str(root / home_rel) and
                    witnessed_home == str(root / home_rel) and
                    witnessed_predef == str(root / predef_rel),
                    "JVM witness does not bind the absent predef/task-owned user.home")
            expected_witness_refs.append(ref)
        event_entries = _directory_names(
            event_dir, "startup witness event directory", maximum_entries=128)
        require(len(event_entries) <= 128 and event_entries == expected_witness_names,
                "startup witness directory contains missing, extra, linked, or non-file entries")
    sidecar_entries = _directory_names(
        root / sidecar_root, "startup sidecar root",
        maximum_entries=MAX_STARTUP_EVENTS + 2)
    require(len(sidecar_entries) <= MAX_STARTUP_EVENTS + 2 and
            sidecar_entries == expected_sidecar_names,
            "startup sidecar root contains missing or unmanifested entries")
    require(events == expected_event_refs and witnesses == expected_witness_refs,
            "startup manifest references differ from the complete deterministic sidecar/witness set")
    require(aggregate_size <= MAX_STARTUP_BYTES,
            "startup sidecar manifest expands beyond its aggregate byte bound")
    home = root / home_rel
    predef = root / predef_rel
    home_fd = _open_directory(home, "task-owned JVM home")
    os.close(home_fd)
    require(manifest.get("home") == {"path": home_rel, "directory": True, "symlink": False},
            "startup task-owned HOME directory state differs")
    require(manifest.get("predef") == {
                "path": predef_rel, "present": False, "symlink": False,
                "bytes": 0, "sha256": None,
            } and _path_state(predef, "task-owned Scala predef") is None,
            "task-owned Scala predef is present, linked, or misreported")
    return {"summary": summary_ref, "events": expected_event_refs,
            "witnesses": expected_witness_refs,
            "home": manifest["home"], "predef": manifest["predef"],
            "total_bytes": aggregate_size}


def validate_capture_review(review: dict[str, Any], *, request_ref: dict[str, str],
                            invocation_review_ref: dict[str, str],
                            parent_started_ref: dict[str, str],
                            worker_invocation_ref: dict[str, str],
                            native_exit_ref: dict[str, str],
                            control_result_ref: dict[str, str],
                            startup_manifest_ref: dict[str, str],
                            source_head: str, source_closure_sha256: str,
                            ledger_ref: dict[str, str], namespace: str,
                            capture_root: str, pending_plan_ref: dict[str, str],
                            control_plan_ref: dict[str, str], projection_sha256: str) -> None:
    expected = {
        "request": request_ref,
        "invocation_review": invocation_review_ref,
        "native_parent_started": parent_started_ref,
        "worker_invocation": worker_invocation_ref,
        "native_exit": native_exit_ref,
        "control_result": control_result_ref,
        "startup_sidecar_manifest": startup_manifest_ref,
        "startup_sidecar_manifest_sha256": startup_manifest_ref["sha256"],
        "source_head": source_head,
        "source_closure_sha256": source_closure_sha256,
        "ledger": ledger_ref,
        "namespace": namespace,
        "capture_root": capture_root,
        "pending_plan": pending_plan_ref,
        "control_plan": control_plan_ref,
        "execution_plan_projection_sha256": projection_sha256,
    }
    require(review.get("schema") == CAPTURE_REVIEW_SCHEMA and
            review.get("status") == "approved-for-post-capture-diagnostic-replay-only",
            "independent capture review is absent or has a status beyond replay-only approval")
    require(review.get("bindings") == expected,
            "independent capture review does not bind every exact source/capture input")
    require(review.get("scope") == SEMANTIC_SCOPE,
            "independent capture review changed the semantic-only/performance boundary")
    require(review.get("full_model_qualification") is False and
            review.get("scored_activation") is False and
            review.get("publication_approved") is False and
            review.get("publication_hold") is True,
            "capture review overstates qualification/scoring/publication authority")


def validate_native_exit(exit_record: dict[str, Any], *, request_ref: dict[str, str],
                         ledger_unchanged: bool) -> dict[str, Any]:
    require(exit_record.get("schema") == "v092-native-control-parent-exit/v1" and
            exit_record.get("request") == request_ref and
            exit_record.get("ledger_unchanged") is True and
            exit_record.get("qualification_inferred") is False and
            exit_record.get("automatic_retry") is False and ledger_unchanged,
            "native exit does not bind the exact successful request/unchanged ledger")
    result = exit_record.get("result")
    require(type(result) is dict and result.get("status") == "process-returned" and
            type(result.get("exit_code")) is int and result["exit_code"] == 0 and
            result.get("failure") is None and
            result.get("qualification_inferred") is False and
            result.get("automatic_retry") is False and
            all(result.get(k) == v for k, v in SEMANTIC_SCOPE.items()),
            "native wrapper did not return successfully within semantic-only scope")
    phases = result.get("phases")
    require(type(phases) is list and [p.get("phase") for p in phases if type(p) is dict] ==
            ["ready", "controls-started", "controls-returned"] and
            len(phases) == 3,
            "native wrapper phase handshake did not reach controls-returned")
    cleanup = result.get("cleanup")
    require(type(cleanup) is dict and cleanup.get("coordinator_reaped") is True,
            "native wrapper did not prove direct child reaping")
    return result


def validate_control_result(control_result: dict[str, Any], *, request_ref: dict[str, str],
                             request: dict[str, Any], plan: dict[str, Any],
                             projection_sha256: str) -> tuple[dict[str, Any], dict[str, Any]]:
    require(control_result.get("schema") == "v092-native-control-qualification-result/v1" and
            control_result.get("request") == request_ref and
            control_result.get("observer") == request.get("observer") and
            control_result.get("pending_plan") == request.get("pending_plan") and
            all(control_result.get(k) == v for k, v in SEMANTIC_SCOPE.items()) and
            control_result.get("scored_activation") is False and
            control_result.get("creates_unsupported_decisions") is False and
            control_result.get("automatic_retry") is False,
            "control result is not the exact non-scored native qualification result")
    run = control_result.get("run")
    require(type(run) is dict and
            run.get("schema") == "analyzer-qualification-control-run/v092" and
            run.get("control_plan_sha256") == request["control_plan"]["sha256"] and
            run.get("execution_plan_projection_sha256") == projection_sha256 and
            run.get("identity") == plan.get("identity") and
            type(run.get("records")) is list and len(run["records"]) == 12 and
            type(run.get("phase_invocation_count")) is int and run["phase_invocation_count"] == 36 and
            run.get("scored_activation") is False,
            "control result does not contain the exact 12-arm/36-phase v4.0.660 capture")
    startup = control_result.get("startup_observation")
    require(type(startup) is dict and startup.get("qualification_safe") is True,
            "native control result lacks safe JVM startup evidence")
    return run, startup


def validate_native08_command_path_audit(
    audit: object,
    *,
    request_ref: dict[str, str],
    control_result_ref: dict[str, str],
    source_head: str,
    source_closure_sha256: str,
    ledger_ref: dict[str, str],
) -> dict[str, Any]:
    """Validate the independently pinned recorded-field PATH-delta audit."""
    require(type(audit) is dict and
            set(audit) == {"schema", "status", "bindings", "recorded_command_comparison", "interpretation"} and
            audit.get("schema") == NATIVE08_PATH_DELTA_SCHEMA and
            audit.get("status") == NATIVE08_PATH_DELTA_STATUS,
            "native08 recorded command-path audit schema/status differs")
    bindings = audit.get("bindings")
    required_bindings = {
        "request", "control_result", "worker_invocation", "worker_environment_sha256",
        "retained_control_run", "native08_control_run",
        "source_head", "source_closure_sha256", "retained_observer", "pending_plan",
        "control_plan", "ledger", "retained_script", "runtime_sources", "native_tools",
        "command_path_helper",
    }
    expected_runtime_sources = {
        "scripts/joern_capability_repair_v092_03.py": {
            "path": "scripts/joern_capability_repair_v092_03.py",
            "sha256": "8e3d986f20c2262045d8473837d1bf5a56b61da1bc23fee6e778bd0ac47d2b51",
        },
        "scripts/joern_normal_runner_v092.py": {
            "path": "scripts/joern_normal_runner_v092.py",
            "sha256": "683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4",
        },
        "scripts/joern_normal_reports_v092.py": {
            "path": "scripts/joern_normal_reports_v092.py",
            "sha256": "75531186a9091e9e907a2c42388efea0e33d4872787a28fa9fc20b3643131db1",
        },
        "scripts/swift_common_population_v2.py": {
            "path": "scripts/swift_common_population_v2.py",
            "sha256": "3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6",
        },
        "scripts/joern_diagnostic_admission_v092.py": {
            "path": "scripts/joern_diagnostic_admission_v092.py",
            "sha256": "c2faeeb5ef99f539ad8a4bee6fbc85656c0cc142f92196c02f5f26a446140a9e",
        },
    }
    expected_tools = {
        "wrapper": {
            "path": NATIVE_WRAPPER,
            "sha256": NATIVE10_SOURCE_SHA256[NATIVE_WRAPPER],
        },
        "resources": {
            "path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py",
            "sha256": NATIVE10_SOURCE_SHA256[
                "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py"],
        },
    }
    require(type(bindings) is dict and set(bindings) == required_bindings and
            request_ref == NATIVE08_REQUEST_REF and
            control_result_ref == NATIVE08_CONTROL_RESULT_REF and
            source_head == NATIVE08_SOURCE_HEAD and
            ledger_ref == {"path": LEDGER_PATH, "sha256": LEDGER_SHA256} and
            type(source_closure_sha256) is str and SHA256_RE.fullmatch(source_closure_sha256) is not None and
            bindings.get("request") == request_ref and
            bindings.get("control_result") == control_result_ref and
            bindings.get("worker_invocation") == NATIVE08_WORKER_INVOCATION_REF and
            bindings.get("worker_environment_sha256") == NATIVE08_WORKER_ENVIRONMENT_SHA256 and
            bindings.get("retained_control_run") == RETAINED_CONTROL_RUN_REF and
            bindings.get("source_head") == source_head and
            bindings.get("source_closure_sha256") == source_closure_sha256 and
            bindings.get("ledger") == ledger_ref and
            bindings.get("retained_observer") == NATIVE10_EXPECTED_OBSERVER and
            bindings.get("pending_plan") == NATIVE10_PENDING_PLAN and
            bindings.get("control_plan") == NATIVE08_CONTROL_PLAN,
            "native08 command-path audit provenance differs")
    require(type(bindings.get("native08_control_run")) is dict and
            set(bindings["native08_control_run"]) == {"path", "sha256"} and
            bindings["native08_control_run"].get("path") == NATIVE08_CAPTURE_RUN_PATH and
            type(bindings["native08_control_run"].get("sha256")) is str and
            SHA256_RE.fullmatch(bindings["native08_control_run"]["sha256"]) is not None and
            bindings.get("runtime_sources") == expected_runtime_sources and
            bindings.get("retained_script") == expected_runtime_sources[
                "scripts/joern_capability_repair_v092_03.py"] and
            bindings.get("native_tools") == expected_tools and
            bindings.get("command_path_helper") == COMMAND_PATH_HELPER,
            "native08 command-path audit source/runtime refs differ")
    comparison = audit.get("recorded_command_comparison")
    comparison_fields = {
        "retained_record_count", "native08_record_count", "phase_invocation_count",
        "recorded_input_fields_unchanged_except", "recorded_environment_keys_equal",
        "old_path_sha256", "native08_path", "native08_path_sha256",
        "ambient_os_environment_equivalence_proven", "command_input_equivalence", "pairs",
    }
    require(type(comparison) is dict and set(comparison) == comparison_fields and
            comparison.get("retained_record_count") == 12 and
            comparison.get("native08_record_count") == 12 and
            comparison.get("phase_invocation_count") == 36 and
            comparison.get("recorded_input_fields_unchanged_except") == "environment.PATH" and
            comparison.get("recorded_environment_keys_equal") is True and
            comparison.get("old_path_sha256") == NATIVE08_OLD_PATH_SHA256 and
            comparison.get("native08_path") == NATIVE08_SANITIZED_PATH and
            comparison.get("native08_path_sha256") == NATIVE08_SANITIZED_PATH_SHA256 and
            comparison.get("ambient_os_environment_equivalence_proven") is False and
            comparison.get("command_input_equivalence") is False and
            type(comparison.get("pairs")) is list and len(comparison["pairs"]) == 36,
            "native08 command-path audit overstates recorded-field comparability")
    pair_ids = set()
    for pair in comparison["pairs"]:
        require(type(pair) is dict and set(pair) == {
                    "control", "case_id", "arm", "phase", "retained_raw", "native08_raw",
                    "retained_command", "native08_command"},
                "native08 command-path audit pair shape differs")
        identity = (pair["control"], pair["case_id"], pair["arm"], pair["phase"])
        require(all(type(value) is str and value for value in identity) and
                pair["arm"] in {"on", "off"} and
                pair["phase"] in {"typecheck", "frontend", "query"} and
                identity not in pair_ids,
                "native08 command-path audit contains duplicate or malformed pair identity")
        pair_ids.add(identity)
        for field in ("retained_raw", "native08_raw", "retained_command", "native08_command"):
            ref = pair[field]
            require(type(ref) is dict and set(ref) == {"path", "sha256"} and
                    type(ref.get("path")) is str and type(ref.get("sha256")) is str and
                    SHA256_RE.fullmatch(ref["sha256"]) is not None,
                    "native08 command-path audit contains an unbound raw/command ref")
    interpretation = audit.get("interpretation")
    require(type(interpretation) is dict and set(interpretation) == {
                "scope", "result", "input_equivalence_claimed", "uncontended_timing_certified",
                "relative_performance_conclusions_authorized", "full_model_qualification",
                "scored_activation", "publication_approved", "publication_hold",
            } and interpretation.get("scope") == "semantic-only" and
            interpretation.get("result") == (
                "The only changed recorded command-input field is the prescribed PATH; "
                "unrecorded historical environment remains unknown." ) and
            interpretation.get("input_equivalence_claimed") is False and
            interpretation.get("uncontended_timing_certified") is False and
            interpretation.get("relative_performance_conclusions_authorized") is False and
            interpretation.get("full_model_qualification") is False and
            interpretation.get("scored_activation") is False and
            interpretation.get("publication_approved") is False and
            interpretation.get("publication_hold") is True,
            "native08 command-path audit interpretation exceeds its semantic-only scope")
    return audit


def validate_native_parent(parent: dict[str, Any], *, request_ref: dict[str, str],
                           invocation_review_ref: dict[str, str],
                           source_head: str, ledger_ref: dict[str, str]) -> None:
    require(parent.get("schema") == "v092-native-control-parent/v1" and
            parent.get("request") == request_ref and parent.get("review") == invocation_review_ref and
            parent.get("source_head") == source_head and parent.get("ledger") == ledger_ref and
            parent.get("publication_hold") is True and parent.get("automatic_retry") is False,
            "native parent-started receipt does not bind the exact reviewed invocation")


def validate_native_worker_invocation(root: Path, worker: dict[str, Any], *,
                                      request_ref: dict[str, str],
                                      invocation_review_ref: dict[str, str],
                                      parent_ref: dict[str, str],
                                      parent: dict[str, Any], request: dict[str, Any],
                                      wrapper: Any, plan: dict[str, Any]) -> None:
    fields = {
        "schema", "request", "review", "parent_started_ref", "process", "parent_process",
        "recorded_popen_argv", "actual_raw_argv", "interpreter_identity",
        "parent_interpreter_identity", "environment", "environment_sha256", "automatic_retry",
    }
    require(type(worker) is dict and set(worker) == fields and
            worker.get("schema") == "v092-native-control-worker-invocation/v1" and
            worker.get("request") == request_ref and
            worker.get("review") == invocation_review_ref and
            worker.get("parent_started_ref") == parent_ref and
            worker.get("parent_process") == parent.get("process") and
            worker.get("recorded_popen_argv") == parent.get("argv") and
            worker.get("parent_interpreter_identity") == parent.get("interpreter_identity") and
            worker.get("automatic_retry") is False,
            "worker invocation does not bind the exact request, review, parent, argv, and interpreter")
    process = worker.get("process")
    require(type(process) is dict and type(process.get("pid")) is int and
            process["pid"] > 0 and type(process.get("birth_identity")) is str and
            process["birth_identity"] and process != parent.get("process"),
            "worker invocation process identity is malformed or aliases its parent")
    identity = wrapper.validate_worker_argv(worker["recorded_popen_argv"],
                                             worker["actual_raw_argv"])
    environment = worker.get("environment")
    require(environment == wrapper.expected_environment(root, request, plan) and
            worker.get("interpreter_identity") == identity and
            worker.get("environment_sha256") == sha_bytes(
                (json.dumps(environment, sort_keys=True, separators=(",", ":")) + "\n").encode()),
            "worker invocation interpreter or environment differs from the reviewed launch")


@contextlib.contextmanager
def _owned_scripts_path(path: Path):
    """Make scripts importable and restore only this scope's own insertion."""
    resolved = Path(os.path.abspath(path))
    require(resolved.is_absolute() and
            not any(item.is_symlink() for item in (resolved, *resolved.parents)) and
            resolved.is_dir(),
            "owned script import directory is missing or linked")
    entry = str(resolved)
    original = list(sys.path)
    require(original.count(entry) <= 1,
            "script import directory is duplicated in sys.path")
    inserted = entry not in original
    owned_entry = (" " + entry)[1:] if inserted else None
    if inserted:
        sys.path.insert(0, owned_entry)
    primary: BaseException | None = None
    try:
        yield resolved
    except BaseException as error:
        primary = error
        raise
    finally:
        cleanup_error = None
        if inserted:
            positions = [index for index, value in enumerate(sys.path)
                         if value is owned_entry]
            if len(positions) == 1:
                del sys.path[positions[0]]
            else:
                cleanup_error = FinalizationError(
                    "owned scripts sys.path entry identity changed")
        if sys.path != original and cleanup_error is None:
            cleanup_error = FinalizationError(
                "foreign sys.path changes detected in the bounded script scope")
        if cleanup_error is not None:
            if primary is None:
                raise cleanup_error
            primary.add_note(str(cleanup_error))


def _load_module(name: str, path: Path, *, scripts_path: Path,
                 expected_sha256: str) -> Any:
    """Register one exact source buffer; the caller owns identity cleanup."""
    scripts = Path(os.path.abspath(scripts_path))
    path = Path(os.path.abspath(path))
    require(not any(item.is_symlink() for item in (scripts, *scripts.parents)) and
            not any(item.is_symlink() for item in (path, *path.parents)),
            "pinned module path crosses a symlink")
    require(str(scripts) in sys.path and path.parent == scripts,
            "pinned module path is outside the registered scripts scope")
    require(name not in sys.modules, f"refusing preloaded module identity: {name}")
    require(SHA256_RE.fullmatch(expected_sha256) is not None,
            "pinned module source SHA-256 is malformed")
    raw = _read_stable(path, MAX_NATIVE_SOURCE_BYTES,
                       "pinned module source " + name, expected_sha256)
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None,
            f"cannot load pinned source: {path}")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__spec__ = spec
    module.__package__ = spec.parent
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
        require(sys.modules.get(name) is module,
                "pinned module registration identity changed during execution: " + name)
    except BaseException as error:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            error.add_note("failed pinned module registration identity changed: " + name)
        raise
    return module


@contextlib.contextmanager
def _registered_module_scope(name: str, path: Path, *, scripts_path: Path,
                             expected_sha256: str):
    module = _load_module(name, path, scripts_path=scripts_path,
                          expected_sha256=expected_sha256)
    primary: BaseException | None = None
    try:
        yield module
    except BaseException as error:
        primary = error
        raise
    finally:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            cleanup_error = FinalizationError(
                "registered module identity changed before cleanup: " + name)
            if primary is None:
                raise cleanup_error
            primary.add_note(str(cleanup_error))


def _source_ref_sha256(source_refs: list[dict[str, str]], path: str) -> str:
    matches = [item for item in source_refs if item.get("path") == path]
    require(len(matches) == 1 and set(matches[0]) == {"path", "sha256"} and
            SHA256_RE.fullmatch(matches[0].get("sha256", "")) is not None,
            "current source closure lacks one exact module pin: " + path)
    return matches[0]["sha256"]


def _load_script_import_aliases(owned: ExitStack, root: Path,
                                source_refs: list[dict[str, str]],
                                scripts_path: Path) -> dict[str, Any]:
    """Load only known bare imports after the complete source closure is proved."""
    modules: dict[str, Any] = {}
    for name, relative in SCRIPT_IMPORT_ALIASES:
        modules[name] = owned.enter_context(_registered_module_scope(
            name, root / relative, scripts_path=scripts_path,
            expected_sha256=_source_ref_sha256(source_refs, relative)))
    return modules


@contextlib.contextmanager
def _owned_private_engine_modules(common: Any, root: Path,
                                  source_refs: list[dict[str, str]]):
    """Load and clean the retained runner's private modules from pinned bytes."""
    require(type(getattr(common, "_PRIVATE_ENGINES", None)) is dict and
            not common._PRIVATE_ENGINES,
            "preexisting private-engine cache is not owned by this finalizer")
    original_loader = common._load_private_module
    require(callable(original_loader), "pinned common loader is unavailable")
    cache = common._PRIVATE_ENGINES
    root = Path(root).resolve()
    module_paths = {
        "runner": "scripts/joern_normal_runner_v1.py",
        "reports": "scripts/joern_normal_reports_v1.py",
    }
    loaded: list[tuple[str, Any]] = []

    def owned_loader(name: str, path: Path, import_router: Any) -> Any:
        path = Path(os.path.abspath(path))
        role = "reports" if "_reports_" in name else "runner" if "_runner_" in name else None
        require(role in module_paths and
                re.fullmatch(r"_dfb_common_v2_joern_" + role + r"_[0-9a-f]{12}", name) is not None and
                path == root / module_paths[role],
                "private runner module path or identity is outside the exact source closure")
        require(name not in sys.modules,
                "preloaded private runner module identity is forbidden: " + name)
        expected_sha256 = _source_ref_sha256(source_refs, module_paths[role])
        raw = _read_stable(path, MAX_NATIVE_SOURCE_BYTES,
                           "private runner module " + name, expected_sha256)
        spec = importlib.util.spec_from_file_location(name, path)
        require(spec is not None and spec.loader is not None,
                "cannot construct pinned private runner module: " + name)
        module = importlib.util.module_from_spec(spec)
        private_builtins = dict(vars(builtins))
        private_builtins["__import__"] = import_router
        module.__dict__["__builtins__"] = private_builtins
        sys.modules[name] = module
        loaded.append((name, module))
        try:
            exec(compile(raw, str(path), "exec"), module.__dict__)
            require(sys.modules.get(name) is module,
                    "private runner module registration identity changed: " + name)
        except BaseException as error:
            if sys.modules.get(name) is not module:
                error.add_note("private runner module registration was replaced: " + name)
            raise
        return module

    common._load_private_module = owned_loader
    primary: BaseException | None = None
    try:
        yield loaded
    except BaseException as error:
        primary = error
        raise
    finally:
        failures: list[BaseException] = []
        if common._load_private_module is owned_loader:
            common._load_private_module = original_loader
        else:
            failures.append(FinalizationError(
                "private runner loader callback identity changed"))
        if common._PRIVATE_ENGINES is not cache:
            failures.append(FinalizationError(
                "private runner cache object identity changed"))
        else:
            owned_modules = {id(module) for _, module in loaded}
            for key, value in list(cache.items()):
                if (type(value) is dict and set(value) == {"runner", "reports"} and
                        all(id(module) in owned_modules for module in value.values())):
                    del cache[key]
                else:
                    failures.append(FinalizationError(
                        "unowned private runner cache entry retained"))
        for name, module in reversed(loaded):
            if sys.modules.get(name) is module:
                del sys.modules[name]
            else:
                failures.append(FinalizationError(
                    "private runner module identity changed before cleanup: " + name))
        if failures:
            if primary is not None:
                for failure in failures:
                    primary.add_note(str(failure))
            else:
                for failure in failures[1:]:
                    failures[0].add_note(str(failure))
                raise failures[0]


def _assert_script_import_identities(root: Path, source_refs: list[dict[str, str]],
                                      runner: Any) -> None:
    expected = dict(SCRIPT_IMPORT_ALIASES)
    modules = {name: sys.modules.get(name) for name in expected}
    for name, relative in expected.items():
        module = modules[name]
        require(module is not None and
                Path(getattr(module, "__file__", "")).resolve() == root / relative and
                getattr(getattr(module, "__spec__", None), "origin", None) ==
                str(root / relative) and
                sha_bytes(_read_stable(root / relative, MAX_NATIVE_SOURCE_BYTES,
                                       "bound script module " + name,
                                       _source_ref_sha256(source_refs, relative))) ==
                _source_ref_sha256(source_refs, relative),
                "owned script module identity or bytes differ: " + name)
    controls = modules["joern_normal_controls_v1"]
    reports = modules["swift_normal_reports_v1"]
    swift = modules["joern_swift"]
    projection = modules["v092_qualification"]
    canonical_runner = modules["joern_normal_runner_v092"]
    normal_execution = modules["joern_normal_execution_v1"]
    execution_revalidation = modules["joern_execution_revalidation_v1"]
    common_runner = modules["swift_normal_runner_v1"]
    v3_runner = modules["swift_v3_runner"]
    v3_reports = modules["swift_v3_reports"]
    require(runner is not canonical_runner and
            canonical_runner.EXECUTION_PLAN_PATH == "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json" and
            runner.common is modules["swift_common_population_v2"] and
            runner.qualification_binding is projection and
            runner.HISTORICAL_OPAQUE_WRAPPERS is controls.WRAPPERS and
            controls.require is reports.require and
            controls.configuration is swift.configuration and
            controls.normalize is swift.normalize and
            canonical_runner.common is modules["swift_common_population_v2"] and
            canonical_runner.qualification_binding is projection and
            canonical_runner.HISTORICAL_OPAQUE_WRAPPERS is controls.WRAPPERS and
            execution_revalidation.env_for is normal_execution.env_for and
            execution_revalidation.compiler_argv is normal_execution.compiler_argv and
            execution_revalidation.frontend_argv is normal_execution.frontend_argv and
            execution_revalidation.query_argv is normal_execution.query_argv and
            common_runner.process is modules["swift_v2_process"] and
            common_runner.inspect_logs is modules["swift_extraction_integrity"].inspect_logs and
            common_runner.snapshot is modules["swift_artifact_closure"].snapshot and
            common_runner.assess_coverage is modules["swift_persistence_coverage"].assess_coverage and
            common_runner.CoverageStatus is modules["swift_persistence_coverage"].CoverageStatus and
            common_runner.lane is v3_runner.lane and
            common_runner.observe is v3_runner.observe and
            v3_runner.inputs is v3_reports.inputs and
            v3_runner.read is v3_reports.read and
            v3_runner.sha is v3_reports.sha and
            v3_runner.require is v3_reports.require,
            "Joern runner bare imports differ from the owned exact source modules")


def _load_native_wrapper(root: Path, verified_sources: dict[str, bytes]) -> Any:
    """Execute only source bytes already bound to the request and expected HEAD."""
    require(set(verified_sources) == set(NATIVE10_SOURCE_SHA256),
            "native10 exact source dependency set differs")
    for relative, expected in NATIVE10_SOURCE_SHA256.items():
        require(sha_bytes(verified_sources[relative]) == expected,
                "native10 verified source bytes changed: " + relative)
    names = {
        "archive_evidence": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py",
        "process_reconciliation": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py",
        "joern_native_controls10_postcapture": NATIVE_WRAPPER,
    }
    require(all(name not in sys.modules for name in names),
            "preloaded native10 module identity is forbidden")
    owned: list[tuple[str, Any]] = []
    modules: dict[str, Any] = {}
    primary: BaseException | None = None
    wrapper = None
    try:
        for name in ("archive_evidence", "process_reconciliation",
                     "joern_native_controls10_postcapture"):
            relative = names[name]
            path = root / relative
            module = types.ModuleType(name)
            module.__file__ = str(path)
            module.__spec__ = importlib.util.spec_from_file_location(name, path)
            require(module.__spec__ is not None, "native10 module spec is unavailable: " + name)
            sys.modules[name] = module
            owned.append((name, module))
            modules[name] = module
            source = verified_sources[relative]
            exec(compile(source, str(path), "exec"), module.__dict__)
        wrapper = modules["joern_native_controls10_postcapture"]
    except BaseException as error:
        primary = error
        raise
    finally:
        cleanup_errors = []
        for name, module in reversed(owned):
            if sys.modules.get(name) is module:
                del sys.modules[name]
            else:
                cleanup_errors.append(name)
        if cleanup_errors:
            error = FinalizationError("native10 module registration identity changed: " +
                                      ", ".join(cleanup_errors))
            if primary is not None:
                primary.add_note(str(error))
            else:
                raise error
    require(wrapper is not None, "verified native10 wrapper did not load")
    return wrapper


def _make_bindings(root: Path, args: argparse.Namespace) -> tuple[dict[str, dict[str, str]], dict[str, Any], Any]:
    names = ("request", "invocation_review", "native_exit", "control_result",
             "capture_review", "startup_sidecar_manifest", "worker_invocation")
    refs: dict[str, dict[str, str]] = {}
    values: dict[str, Any] = {}
    caps = {
        "request": (MAX_REQUEST_BYTES, QUALIFICATION_ROOT),
        "invocation_review": (MAX_REVIEW_BYTES, VALIDATION_ROOT),
        "native_exit": (MAX_EXIT_BYTES, None),
        "control_result": (MAX_CONTROL_RESULT_BYTES, None),
        "capture_review": (MAX_REVIEW_BYTES, VALIDATION_ROOT),
        "startup_sidecar_manifest": (MAX_MANIFEST_BYTES, None),
        "worker_invocation": (MAX_REVIEW_BYTES, None),
    }
    for name in names:
        ref, _path, value, _raw = checked_ref(root, getattr(args, name),
                                               getattr(args, name + "_sha256"), name,
                                               maximum=caps[name][0], prefix=caps[name][1])
        refs[name] = ref
        values[name] = value
    request = values["request"]
    require(type(request) is dict and set(request) == NATIVE10_REQUEST_FIELDS and
            request.get("schema") == "v092-joern-native-control-request/v2" and
            type(request.get("expected_head")) is str and
            re.fullmatch(r"[0-9a-f]{40}", request["expected_head"]) is not None,
            "exact native10 request schema/committed expected HEAD required before source load")
    namespace = expected_namespace(request, refs["request"])
    for relative, description in ((namespace, "native namespace"),
                                  (namespace + "/capture", "native capture root")):
        _, directory_path = _relative(root, relative, description)
        directory_fd = _open_directory(directory_path, description)
        os.close(directory_fd)
    require(refs["native_exit"]["path"] == namespace + "/exit.json" and
            refs["control_result"]["path"] == namespace + "/control-result.json",
            "native exit/control result paths do not match the exact request namespace")
    validate_startup_manifest_ref_path(
        refs["startup_sidecar_manifest"]["path"], namespace)
    require(refs["worker_invocation"]["path"] == namespace + "/worker-invocation.json",
            "worker invocation path does not match the exact native namespace")
    require(request.get("ledger") == {"path": LEDGER_PATH, "sha256": LEDGER_SHA256},
            "native request does not retain the immutable 130-row ledger pin")
    require(request.get("observer") == NATIVE10_EXPECTED_OBSERVER and
            request.get("pending_plan") == NATIVE10_PENDING_PLAN,
            "native request observer or pending plan differs from independent hardpins")
    require(type(request.get("tool_refs")) is dict and
            set(request["tool_refs"]) == {"wrapper", "resources"} and
            request["tool_refs"].get("wrapper") == {
                "path": NATIVE_WRAPPER,
                "sha256": NATIVE10_SOURCE_SHA256[NATIVE_WRAPPER],
            } and request["tool_refs"].get("resources") == {
                "path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py",
                "sha256": NATIVE10_SOURCE_SHA256["reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py"],
            }, "native10 wrapper/resource refs differ from independent hardpins")
    source_refs = request.get("source_refs")
    require(type(source_refs) is list and source_refs and
            all(type(item) is dict and set(item) == {"path", "sha256"} for item in source_refs),
            "native request source closure is malformed")
    source_map = {item["path"]: item for item in source_refs}
    require(len(source_map) == len(source_refs), "native request source closure has duplicate paths")
    require(all(source_map.get(path) == {"path": path, "sha256": sha}
                for path, sha in NATIVE10_SOURCE_SHA256.items()),
            "native10 executable source closure differs from independent hardpins")
    review = values["invocation_review"]
    require(type(review) is dict and
            review.get("status") == "approved-for-native-control-qualification-only" and
            review.get("automatic_retry") is False,
            "independent native10 invocation review is not accepted")
    bindings = review.get("bindings", {})
    expected_review = {
        "request_sha256": refs["request"]["sha256"],
        "wrapper_sha256": request["tool_refs"]["wrapper"]["sha256"],
        "resources_sha256": request["tool_refs"]["resources"]["sha256"],
        "observer_sha256": request["observer"]["sha256"],
        "pending_plan_sha256": request["pending_plan"]["sha256"],
        "ledger_sha256": request["ledger"]["sha256"],
        "source_head": request["expected_head"],
        "native_provider_sha256": sha_bytes(
            (json.dumps(request["native_provider"], sort_keys=True,
                        separators=(",", ":")) + "\n").encode()),
    }
    require(all(bindings.get(key) == value for key, value in expected_review.items()),
            "independent invocation review does not bind exact request and native10 sources")
    expected_head = request["expected_head"]
    require(type(request.get("native_provider")) is dict and
            set(request["native_provider"]) == {
                "module", "c_source", "header", "library", "build_receipt", "abi_version"} and
            request["native_provider"].get("abi_version") == 4,
            "native provider request is not the exact ABI-4 shape")
    kind = subprocess.check_output(["git", "cat-file", "-t", expected_head], cwd=root, text=True).strip()
    require(kind == "commit", "request expected HEAD is not a committed source revision")
    verified_sources: dict[str, bytes] = {}
    for relative, expected_sha in NATIVE10_SOURCE_SHA256.items():
        expected_ref = {"path": relative, "sha256": expected_sha}
        require(source_map.get(relative) == expected_ref,
                "native10 source ref differs from the independent hardpin: " + relative)
        raw = _read_stable(root / relative, MAX_NATIVE_SOURCE_BYTES,
                           "native10 source " + relative, expected_sha)
        committed = subprocess.check_output(["git", "show", expected_head + ":" + relative], cwd=root)
        require(committed == raw, "native10 source bytes differ from the request's committed expected HEAD: " + relative)
        verified_sources[relative] = raw
    wrapper = _load_native_wrapper(root, verified_sources)
    return refs, values, wrapper


def _validate_ledger(root: Path, wrapper: Any, request: dict[str, Any]) -> dict[str, Any]:
    ref = request.get("ledger")
    require(ref == {"path": LEDGER_PATH, "sha256": LEDGER_SHA256},
            "live ledger pin differs from the finalizer's frozen 130-row identity")
    raw = _read_stable(root / LEDGER_PATH, MAX_LEDGER_BYTES,
                       "current release ledger", LEDGER_SHA256)
    history = wrapper.validate_ledger_history(raw)
    require(history.get("rows") == EXPECTED_LEDGER_ROWS and
            history.get("status_counts") == EXPECTED_LEDGER_COUNTS,
            "current release ledger row/status counts differ from the 130-row pin")
    return {"path": LEDGER_PATH, "sha256": LEDGER_SHA256,
            "rows": history["rows"], "status_counts": history["status_counts"]}


def _safe_output(root: Path, output_dir_text: str, plan_text: str) -> tuple[Path, str]:
    out_rel, out_dir = _relative(root, output_dir_text, "fresh output directory")
    plan_rel, plan_path = _relative(root, plan_text, "eligible plan output")
    required_root = QUALIFICATION_ROOT + "native-finalization-03/"
    require(out_rel.startswith(required_root) and plan_rel == out_rel + "/execution-plan.json",
            "output must be a new native-finalization-03 qualification directory")
    parent_fd = _open_directory(out_dir.parent, "fresh output parent directory")
    os.close(parent_fd)
    require(_path_state(out_dir, "fresh output directory") is None,
            "post-capture output already exists or is linked; append-only refusal")
    return out_dir, plan_rel


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _write_raw_exclusive(path: Path, raw: bytes) -> None:
    require(type(raw) is bytes, "exclusive raw output must be bytes")
    parent_fd, name = _open_parent_directory(path, "exclusive output")
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o666,
            dir_fd=parent_fd,
        )
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "exclusive raw output made no write progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)


def finalize(args: argparse.Namespace, *, root: Path = ROOT) -> dict[str, Any]:
    """Prepare a reviewed capture, then publish only after all scopes clean up."""
    root = Path(root).resolve()
    output_dir, eligible_plan_rel = _safe_output(root, args.output_dir,
                                                  args.eligible_plan_path)
    refs, values, wrapper = _make_bindings(root, args)
    scripts_path = root / SCRIPTS
    with _owned_scripts_path(scripts_path):
        with ExitStack() as owned:
            owned.enter_context(wrapper.owned_module_scope())
            prepared = _finalize_after_bindings(
                args, root=root, output_dir=output_dir,
                eligible_plan_rel=eligible_plan_rel, refs=refs, values=values,
                wrapper=wrapper, owned=owned)
    del wrapper, values, refs
    return _publish_after_cleanup(root, prepared)


def _publish_after_cleanup(root: Path, prepared: dict[str, Any]) -> dict[str, Any]:
    """Publish eligible artifacts from plain prepared data after imports clean up."""
    root = Path(root).resolve()
    required_fields = {
        "schema", "output_dir", "eligible_plan_path", "candidate_plan",
        "ledger", "finalization_receipt",
    }
    require(type(prepared) is dict and set(prepared) == required_fields and
            prepared.get("schema") == PREPARED_FINALIZATION_SCHEMA,
            "prepared post-capture finalization fields differ")
    try:
        json.dumps(prepared, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise FinalizationError("prepared finalization contains non-JSON data") from exc

    output_rel, output_dir = _relative(root, prepared.get("output_dir"),
                                       "prepared finalization output directory")
    eligible_rel, _ = _relative(root, prepared.get("eligible_plan_path"),
                                "prepared eligible plan")
    required_root = QUALIFICATION_ROOT + "native-finalization-03/"
    require(output_rel.startswith(required_root) and
            eligible_rel == output_rel + "/execution-plan.json",
            "prepared output paths differ from the exact native finalization namespace")
    output_fd = _open_directory(output_dir, "prepared finalization output directory")
    os.close(output_fd)

    candidate_rel = output_rel + "/preflight-candidate.json"
    candidate_ref = prepared.get("candidate_plan")
    require(type(candidate_ref) is dict and set(candidate_ref) == {"path", "sha256"} and
            candidate_ref.get("path") == candidate_rel and
            type(candidate_ref.get("sha256")) is str and
            SHA256_RE.fullmatch(candidate_ref["sha256"]) is not None,
            "prepared preflight candidate reference differs")
    candidate_raw = _read_stable(root / candidate_rel, MAX_FINALIZED_FILE_BYTES,
                                 "preflight candidate after cleanup",
                                 candidate_ref["sha256"])

    expected_ledger = {
        "path": LEDGER_PATH,
        "sha256": LEDGER_SHA256,
        "rows": EXPECTED_LEDGER_ROWS,
        "status_counts": EXPECTED_LEDGER_COUNTS,
    }
    ledger = prepared.get("ledger")
    require(type(ledger) is dict and ledger == expected_ledger,
            "prepared ledger identity differs from the immutable 130-row pin")
    ledger_raw = _read_stable(root / LEDGER_PATH, MAX_LEDGER_BYTES,
                              "release ledger after cleanup", LEDGER_SHA256)
    require(len(ledger_raw) == MAX_LEDGER_BYTES,
            "release ledger size changed after cleanup")

    finalization_receipt = prepared.get("finalization_receipt")
    require(type(finalization_receipt) is dict and
            finalization_receipt.get("schema") == "v092-joern-post-capture-finalization/v1" and
            finalization_receipt.get("status") == "diagnostic-replay-complete-publication-held" and
            finalization_receipt.get("ledger") == expected_ledger and
            finalization_receipt.get("preflight_candidate") == candidate_ref and
            finalization_receipt.get("full_model_qualification") is False and
            finalization_receipt.get("scored_activation") is False and
            finalization_receipt.get("publication_approved") is False and
            finalization_receipt.get("analyzer_invoked_by_finalizer") is False and
            all(finalization_receipt.get(key) == value
                for key, value in SEMANTIC_SCOPE.items()) and
            "eligible_plan" not in finalization_receipt and
            "receipt" not in finalization_receipt,
            "prepared finalization receipt exceeds its replay-only scope")
    command_delta_ref = finalization_receipt.get("command_input_delta_audit")
    require(type(command_delta_ref) is dict and
            set(command_delta_ref) == {"path", "sha256"} and
            command_delta_ref.get("path") == output_rel + "/command-input-delta-audit.json" and
            type(command_delta_ref.get("sha256")) is str and
            SHA256_RE.fullmatch(command_delta_ref["sha256"]) is not None,
            "prepared command-input delta reference is absent or outside the exact output directory")
    command_delta_raw = _read_stable(
        root / command_delta_ref["path"], MAX_FINALIZED_FILE_BYTES,
        "command-input delta audit after cleanup", command_delta_ref["sha256"])
    command_delta = _parse_json(command_delta_raw, "command-input delta audit after cleanup")
    validate_native08_command_path_audit(
        command_delta,
        request_ref=finalization_receipt.get("request"),
        control_result_ref=finalization_receipt.get("control_result"),
        source_head=finalization_receipt.get("source_head"),
        source_closure_sha256=finalization_receipt.get("source_closure_sha256"),
        ledger_ref={"path": finalization_receipt.get("ledger", {}).get("path"),
                    "sha256": finalization_receipt.get("ledger", {}).get("sha256")}
        if type(finalization_receipt.get("ledger")) is dict else None,
    )

    eligible_ref = {"path": eligible_rel, "sha256": sha_bytes(candidate_raw)}
    _write_raw_exclusive(root / eligible_rel, candidate_raw)
    written_candidate = _read_stable(root / eligible_rel, MAX_FINALIZED_FILE_BYTES,
                                     "published eligible plan", eligible_ref["sha256"])
    require(written_candidate == candidate_raw,
            "eligible plan bytes differ from the validated preflight candidate")

    final_receipt = {**finalization_receipt, "eligible_plan": eligible_ref}
    assembly_rel = output_rel + "/post-capture-finalization.json"
    assembly_raw = (json.dumps(final_receipt, indent=2, sort_keys=True,
                               ensure_ascii=False) + "\n").encode("utf-8")
    require(0 < len(assembly_raw) <= MAX_FINALIZED_FILE_BYTES,
            "post-capture finalization assembly exceeds its output bound")
    _write_raw_exclusive(root / assembly_rel, assembly_raw)
    final_receipt["receipt"] = {"path": assembly_rel, "sha256": sha_bytes(assembly_raw)}
    return final_receipt


def _finalize_after_bindings(args: argparse.Namespace, *, root: Path,
                             output_dir: Path, eligible_plan_rel: str,
                             refs: dict[str, dict[str, str]],
                             values: dict[str, Any], wrapper: Any,
                             owned: ExitStack) -> dict[str, Any]:
    request = values["request"]
    namespace = expected_namespace(request, refs["request"])
    capture_root = namespace + "/capture"
    cfg = request
    ledger = _validate_ledger(root, wrapper, cfg)
    checked_request = wrapper.validate_request(root, cfg, check_git=False)
    source_map = {ref["path"]: ref for ref in cfg["source_refs"]}
    archive_context = wrapper.archive_evidence.build_context(root, source_map)
    source_check = wrapper.verify_current_source_refs(
        root, cfg["expected_head"], cfg["source_refs"], archive_context)
    require(type(source_check) is dict and source_check.get("status") == "verified" and
            source_check.get("head") == cfg["expected_head"] and
            source_check.get("source_ref_count") == len(cfg["source_refs"]),
            "native request source closure did not verify against its committed expected HEAD")
    _load_script_import_aliases(owned, root, cfg["source_refs"], root / SCRIPTS)
    require(checked_request["plan"]["identity"].get("tool_version") == EXPECTED_TOOL_VERSION,
            "native request is not pinned to Joern 4.0.660")
    source_closure_sha256 = sha_bytes(wrapper.canonical(cfg["source_refs"]))
    invocation_review_ref = refs["invocation_review"]
    wrapper.validate_review(root, invocation_review_ref, refs["request"], cfg)
    parent_rel = namespace + "/parent-started.json"
    parent_raw = _read_stable(root / parent_rel, MAX_REVIEW_BYTES,
                              "native parent-started")
    parent_ref = {"path": parent_rel, "sha256": sha_bytes(parent_raw)}
    parent = _parse_json(parent_raw, "native parent-started")
    validate_native_parent(parent, request_ref=refs["request"],
                           invocation_review_ref=invocation_review_ref,
                           source_head=cfg["expected_head"], ledger_ref=cfg["ledger"])
    exit_record = values["native_exit"]
    native_result = validate_native_exit(exit_record, request_ref=refs["request"], ledger_unchanged=True)
    pending = cfg["pending_plan"]
    plan = wrapper.document(root, pending)
    require(plan.get("identity", {}).get("tool_version") == EXPECTED_TOOL_VERSION and
            plan.get("identity", {}).get("tool") == "joern" and
            plan.get("status") == "qualification-pending" and
            plan.get("execution_eligible") is False and
            plan.get("fresh_qualification") is None,
            "finalizer requires the exact pending 4.0.660 plan")
    worker_ref = refs["worker_invocation"]
    require(worker_ref["path"] == namespace + "/worker-invocation.json",
            "worker invocation path differs from the exact native namespace")
    validate_native_worker_invocation(
        root, values["worker_invocation"], request_ref=refs["request"],
        invocation_review_ref=invocation_review_ref, parent_ref=parent_ref,
        parent=parent, request=cfg, wrapper=wrapper, plan=plan)
    projection_sha256 = plan.get("qualification_control_projection_sha256")
    run, startup = validate_control_result(values["control_result"],
                                           request_ref=refs["request"], request=cfg,
                                           plan=plan, projection_sha256=projection_sha256)
    require(values["control_result"]["pending_plan"] == pending and
            values["control_result"]["observer"] == cfg["observer"],
            "control result differs from exact request plan/observer")
    observer_module = wrapper.load(root, cfg["observer"], "_finalizer_startup_observer")
    manifest = values["startup_sidecar_manifest"]
    manifest_result = validate_startup_manifest(root, manifest, namespace=namespace,
                                                capture_root=capture_root,
                                                startup_summary=startup,
                                                expected_policy=observer_module.STARTUP_POLICY_V5)
    manifest_ref = refs["startup_sidecar_manifest"]
    require(values["capture_review"].get("bindings", {}).get("startup_sidecar_manifest") == manifest_ref,
            "capture review does not bind the exact startup sidecar manifest")
    validate_capture_review(values["capture_review"], request_ref=refs["request"],
                            invocation_review_ref=invocation_review_ref,
                            parent_started_ref=parent_ref,
                            worker_invocation_ref=worker_ref,
                            native_exit_ref=refs["native_exit"],
                            control_result_ref=refs["control_result"],
                            startup_manifest_ref=manifest_ref,
                            source_head=cfg["expected_head"],
                            source_closure_sha256=source_closure_sha256,
                            ledger_ref=cfg["ledger"], namespace=namespace,
                            capture_root=capture_root, pending_plan_ref=pending,
                            control_plan_ref=cfg["control_plan"],
                            projection_sha256=projection_sha256)
    require(exit_record.get("result") == native_result and
            values["control_result"].get("request") == refs["request"],
            "native exit/control result request or process result binding differs")

    post_capture_observer = wrapper.load(
        root, POST_CAPTURE_COMMAND_OBSERVER, "_finalizer_native08_command_observer")
    require(getattr(post_capture_observer, "COMMAND_PATH_HELPER_PATH", None) ==
            COMMAND_PATH_HELPER["path"] and
            getattr(post_capture_observer, "COMMAND_PATH_HELPER_SHA256", None) ==
            COMMAND_PATH_HELPER["sha256"],
            "post-capture observer does not pin the exact independent command-path helper")
    wrapper.stable(root, COMMAND_PATH_HELPER)
    old = post_capture_observer.load_original(root)
    old._assert_canonical_historical_binding(root)
    common = sys.modules["swift_common_population_v2"]
    canonical_runner = sys.modules["joern_normal_runner_v092"]
    owned.enter_context(_owned_private_engine_modules(common, root, cfg["source_refs"]))
    bootstrap = old.validate_bootstrap_inputs(
        root, new_plan_path=pending["path"],
        expected_new_plan_sha256=pending["sha256"],
        expected_evidence_sha256=cfg["evidence"]["sha256"])
    retained_receipt = wrapper.document(root, bootstrap["old_plan"]["fresh_qualification"])
    retained_run = wrapper.document(root, retained_receipt["control_run"])
    old._validate_control_command_equivalence(root, retained_run, run)
    command_delta = old._native08_command_input_delta_audit()
    command_delta = validate_native08_command_path_audit(
        command_delta,
        request_ref=refs["request"],
        control_result_ref=refs["control_result"],
        source_head=cfg["expected_head"],
        source_closure_sha256=source_closure_sha256,
        ledger_ref=cfg["ledger"],
    )
    runner = bootstrap["runner"]
    _assert_script_import_identities(root, cfg["source_refs"], runner)
    runner.EXECUTION_PLAN_PATH = pending["path"]
    checked_plan, _unused, context = runner.validate_plan(
        root, pending["path"], allow_qualification_pending=True)
    require(checked_plan == plan and context["control"] == wrapper.document(root, cfg["control_plan"]),
            "real pending-plan validator returned different source/control bindings")
    _, common_rows, _, cases, _ = common.load_common_population(root)
    case_paths = {row["id"]: root / row["path"] for row in common_rows}
    observations, phase_count = runner._replay_control_run(
        root, plan, context["control"], run, cases, context["engine"], case_paths=case_paths)
    require(phase_count == 36 and len(run["records"]) == 12 and
            run.get("phase_invocation_count") == 36,
            "real control replay did not account for all 12 arms/36 phases")
    assessment = context["engine"].assess_controls(observations)
    require(run.get("assessment") == assessment,
            "captured assessment differs from the production replay")
    # The pending-plan validator imports this exact owned bare alias as well.
    # Reuse that pinned object rather than attempting a duplicate registration.
    _assert_script_import_identities(root, cfg["source_refs"], runner)
    diagnostic = sys.modules["joern_diagnostic_admission_v092"]
    review = diagnostic.replay_admission(root, plan, context["control"], run,
                                         observations, cases, case_paths)
    require(review.get("status") == "measurement-with-known-limits" and
            review.get("full_model_qualification") is False and
            review.get("scored_activation") is False and
            review.get("diagnostic_execution_eligible") is True,
            "actual replay does not support the narrow known-limits diagnostic state")

    # The production runner validates a standalone control-run file. Copy the
    # already captured run object byte-for-byte into the new append-only output.
    output_dir.mkdir(parents=False, exist_ok=False)
    run_rel = output_dir.relative_to(root).as_posix() + "/control-run.json"
    run_path = root / run_rel
    _write_exclusive(run_path, run)
    run_ref = {"path": run_rel, "sha256": sha_file(run_path)}
    command_delta_rel = output_dir.relative_to(root).as_posix() + "/command-input-delta-audit.json"
    command_delta_path = root / command_delta_rel
    _write_exclusive(command_delta_path, command_delta)
    command_delta_ref = {"path": command_delta_rel, "sha256": sha_file(command_delta_path)}
    review["control_run"] = run_ref
    review["reviewer"] = {"path": DIAGNOSTIC, "sha256": sha_file(root / DIAGNOSTIC)}
    review["control_plan"] = plan["qualification_control_plan"]
    review_rel = output_dir.relative_to(root).as_posix() + "/diagnostic-admission-review.json"
    review_path = root / review_rel
    _write_exclusive(review_path, review)
    review_ref = {"path": review_rel, "sha256": sha_file(review_path)}

    old_receipt_ref = bootstrap["old_plan"].get("fresh_qualification")
    require(type(old_receipt_ref) is dict, "retained prior qualification receipt is missing")
    receipt = copy.deepcopy(wrapper.document(root, old_receipt_ref))
    receipt.update(control_run=run_ref,
                   diagnostic_admission_review=review_ref,
                   execution_plan_projection_sha256=bootstrap["projection_sha256"],
                   native_capture={
                       "control_arms": 12,
                       "phase_invocations": phase_count,
                       "full_model_qualification": False,
                       "scored_activation": False,
                       "request": refs["request"],
                       "invocation_review": invocation_review_ref,
                       "native_parent_started": parent_ref,
                       "worker_invocation": worker_ref,
                       "native_exit": refs["native_exit"],
                       "control_result": refs["control_result"],
                       "capture_review": refs["capture_review"],
                       "startup_sidecar_manifest": manifest_ref,
                       "source_head": cfg["expected_head"],
                       "source_closure_sha256": source_closure_sha256,
                       "ledger": ledger,
                       "capture_root": capture_root,
                       "startup_manifest_summary": manifest_result["summary"],
                       "command_input_delta_audit": command_delta_ref,
                       "command_input_comparability": "recorded-fields-only-with-declared-PATH-delta",
                   },
                   **SEMANTIC_SCOPE)
    dims = receipt.setdefault("dimensions", {})
    controls = dims.setdefault("common108_controls", {})
    controls.update(control_run=run_ref, case_count=6, case_arm_count=12,
                    phase_invocation_count=phase_count, strict_assessment=assessment,
                    **SEMANTIC_SCOPE)
    dims["joern_diagnostic_admission"] = review_ref
    receipt_rel = output_dir.relative_to(root).as_posix() + "/qualification-receipt.json"
    receipt_path = root / receipt_rel
    _write_exclusive(receipt_path, receipt)
    receipt_ref = {"path": receipt_rel, "sha256": sha_file(receipt_path)}

    final_plan = copy.deepcopy(plan)
    final_plan.update(status="execution-eligible", execution_eligible=True,
                      diagnostic_execution_eligible=True, full_model_qualification=False,
                      scored_activation=False, fresh_qualification=receipt_ref,
                      registered_at_unix_seconds=int(time.time()) - 1)
    plan_rel = output_dir.relative_to(root).as_posix() + "/preflight-candidate.json"
    candidate_path = root / plan_rel
    _write_exclusive(candidate_path, final_plan)
    candidate_sha256 = sha_file(candidate_path)
    candidate_ref = {"path": plan_rel, "sha256": candidate_sha256}
    old_runner_path = runner.EXECUTION_PLAN_PATH
    try:
        runner.EXECUTION_PLAN_PATH = plan_rel
        preflight_plan, qualification, _ = runner.validate_plan(root, plan_rel)
        require(preflight_plan == final_plan and
                qualification.get("control_run") == run_ref and
                qualification.get("diagnostic_admission_review") == review_ref,
                "real production validate_plan/preflight rejected new post-capture bindings")
        preflight = old.preflight(
            root, new_plan_path=plan_rel,
            expected_new_plan_sha256=candidate_sha256,
            expected_evidence_sha256=cfg["evidence"]["sha256"])
        require(preflight.get("projection_sha256") == bootstrap["projection_sha256"],
                "production repair preflight changed the reviewed control projection")
        require(old._native08_command_input_delta_audit() == command_delta,
                "production preflight PATH-delta audit differs from the bound provisional audit")
    finally:
        runner.EXECUTION_PLAN_PATH = old_runner_path
    candidate_raw = _read_stable(root / plan_rel, MAX_FINALIZED_FILE_BYTES,
                                 "preflight candidate after production preflight",
                                 candidate_sha256)
    require(_parse_json(candidate_raw, "preflight candidate after production preflight") ==
            final_plan,
            "preflight candidate bytes changed after production validation")
    ledger_after_preflight = _validate_ledger(root, wrapper, cfg)
    require(ledger_after_preflight == ledger,
            "release ledger changed during post-capture replay/preflight")
    finalization_receipt = {
        "schema": "v092-joern-post-capture-finalization/v1",
        "status": "diagnostic-replay-complete-publication-held",
        "request": refs["request"],
        "invocation_review": invocation_review_ref,
        "native_parent_started": parent_ref,
        "worker_invocation": worker_ref,
        "native_exit": refs["native_exit"],
        "control_result": refs["control_result"],
        "capture_review": refs["capture_review"],
        "startup_sidecar_manifest": manifest_ref,
        "source_head": cfg["expected_head"],
        "source_closure_sha256": source_closure_sha256,
        "ledger": ledger,
        "capture_root": capture_root,
        "control_arms": 12,
        "phase_invocations": phase_count,
        "assessment": assessment,
        "diagnostic_review": review_ref,
        "qualification_receipt": receipt_ref,
        "preflight_candidate": candidate_ref,
        "command_input_delta_audit": command_delta_ref,
        "command_input_comparability": "recorded-fields-only-with-declared-PATH-delta",
        "full_model_qualification": False,
        "scored_activation": False,
        "publication_approved": False,
        "analyzer_invoked_by_finalizer": False,
        **SEMANTIC_SCOPE,
    }
    return {
        "schema": PREPARED_FINALIZATION_SCHEMA,
        "output_dir": output_dir.relative_to(root).as_posix(),
        "eligible_plan_path": eligible_plan_rel,
        "candidate_plan": candidate_ref,
        "ledger": ledger_after_preflight,
        "finalization_receipt": finalization_receipt,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("request", "invocation-review", "native-exit", "control-result",
                 "capture-review", "startup-sidecar-manifest", "worker-invocation"):
        parser.add_argument("--" + name, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--eligible-plan-path", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        receipt = finalize(args)
    except (FinalizationError, OSError, ImportError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
