"""Bounded, provider-scoped reconciliation helpers for monitor06.

This module never starts an analyzer and never grants cleanup authority. It
launches at most one isolated process-snapshot query child per caller request;
callers own the admission-boundary candidate-consumption set.
"""
from __future__ import annotations

import datetime as dt
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time
import unicodedata
from typing import Any, Callable

MAX_RECONCILIATION_SECONDS = 5.0
QUERY_CLEANUP_RESERVE_SECONDS = 0.1
QUERY_FINALIZE_RESERVE_SECONDS = 0.05
MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_QUERY_STDERR_BYTES = 16 * 1024
MAX_QUERY_READ_CHUNK_BYTES = 64 * 1024
MAX_PROVIDER_EVENT_BYTES = 64 * 1024
QUERY_REAP_RESERVE_SECONDS = 0.05
QUERY_SCRIPT = Path(__file__).with_name("snapshot_query.py")
ABI3_NATIVE_PROVIDER_IDENTITY = "darwin-sysctl-kern-proc-all-libproc/v3"
ABI4_NATIVE_PROVIDER_IDENTITY = "darwin-sysctl-kern-proc-all-libproc/v4"
ABI4_NATIVE_BINDING_SCHEMA = "v092-darwin-native-provider-binding/v1"
ABI4_MAX_ROWS_PER_TABLE = 8192
ABI4_MAX_OUTPUT_ROWS = ABI4_MAX_ROWS_PER_TABLE
ABI4_MAX_OUTER_NATIVE_ROWS = 2 * ABI4_MAX_ROWS_PER_TABLE
ABI4_PROVIDER_MODULE_PATH = (
    "/Users/dave/.codex/worktrees/9f01/dataflowbench/reports/releases/v0.9.2/"
    "acquisition/joern-native-controls-09/darwin-provider/darwin_native_provider.py"
)
ABI4_PROVIDER_MODULE_SHA256 = "b67c56a10e80d7d208c4bbd0f923f41bcc2a710943bf78b6c52881ef386c3158"
ABI4_PROVIDER_LIBRARY_PATH = (
    "/Users/dave/.codex/worktrees/9f01/dataflowbench/reports/releases/v0.9.2/"
    "acquisition/joern-native-controls-09/darwin-provider/libdfb_native_provider_abi4.dylib"
)
ABI4_PROVIDER_LIBRARY_SHA256 = "242d8ff705a1bd3bc8b8f397e5018828942c23bb2fc12701bfc68a8030ebe9e2"
PS_V1_IDENTITY = "ps-axo-pid-percentcpu-comm-args/v1"
PS_V2_IDENTITY = "ps-axo-pid-pcpu-ucomm-args/v2"
PS_V2_FIELD_WIDTH = 64
PS_V2_HEADERS = tuple(
    value.ljust(PS_V2_FIELD_WIDTH, "_")
    for value in ("DFB_PID_V2", "DFB_PCPU_V2", "DFB_UCOMM_V2", "DFB_ARGS_V2")
)
PS_V2_HEADER_BYTES = b" ".join(value.encode("ascii") for value in PS_V2_HEADERS)
PS_V2_CLASSIFIER_MARKER = "__DFB_PS_COMM__"
PS_V2_ARG_LIMIT = 64 * 1024


class ReconciliationError(RuntimeError):
    pass


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _decode_query_stream(raw: bytes, *, fallback_error: dict[str, str] | None = None) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    provider_children: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    parse_error = None
    for line in raw.splitlines():
        if not line:
            continue
        try:
            record = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            parse_error = error
            break
        if type(record) is not dict:
            parse_error = ReconciliationError("query stream record is not an object")
            break
        if record.get("kind") == "snapshot" and type(record.get("snapshot")) is dict:
            snapshots.append(record["snapshot"])
        elif record.get("kind") == "provider-child" and type(record.get("provider_child")) is dict:
            child = record["provider_child"]
            child_pid = child.get("pid")
            prior = next((index for index, item in enumerate(provider_children)
                          if item.get("pid") == child_pid), None)
            if prior is None:
                provider_children.append(child)
            else:
                provider_children[prior] = child
        elif record.get("kind") == "final" and type(record.get("result")) is dict:
            if final is not None:
                parse_error = ReconciliationError("query stream contains multiple final records")
                break
            final = record["result"]
        else:
            parse_error = ReconciliationError("query stream record kind is invalid")
            break
    if final is None:
        provider = snapshots[0].get("provider_identity") if snapshots else "isolated-os-native-query-child"
        error = fallback_error or {"type": "IncompleteQueryStream", "message": "query child ended before final outcome"}
        result = {
            "schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": provider,
            "snapshots": snapshots,
            "provider_children": provider_children,
            "outcome": {"status": "query-stream-incomplete", "complete": False,
                        "order_valid": False, "error": error},
            "os_global_completeness_claim": False,
            "continuous_absence_claim": False,
        }
    else:
        result = dict(final)
        result["snapshots"] = snapshots
        merged = list(result.get("provider_children", []))
        for child in provider_children:
            child_pid = child.get("pid")
            prior = next((index for index, item in enumerate(merged)
                          if type(item) is dict and item.get("pid") == child_pid), None)
            if prior is None:
                merged.append(child)
            else:
                merged[prior] = child
        result["provider_children"] = merged
        if final.get("snapshot_count") != len(snapshots):
            result["outcome"] = {"status": "query-stream-snapshot-count-mismatch", "complete": False,
                                 "order_valid": False,
                                 "error": {"type": "IncompleteQueryStream", "message": "streamed snapshot count differs from final record"}}
    if parse_error is not None:
        result["outcome"] = {"status": "malformed-query-stream", "complete": False,
                             "order_valid": False,
                             "error": {"type": type(parse_error).__name__, "message": str(parse_error)}}
    result.setdefault("snapshots", snapshots)
    result["partial_stream_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def _finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == dt.timedelta(0)


class _BoundedCapture:
    """Keep at most ``limit`` bytes while hashing every observed byte."""

    def __init__(self, limit: int):
        self.limit = limit
        self.prefix = bytearray()
        self.observed_bytes = 0
        self.truncated = False
        self._observed_digest = hashlib.sha256()
        self._prefix_digest = hashlib.sha256()

    def read_size(self) -> int:
        remaining = self.limit - len(self.prefix)
        return min(MAX_QUERY_READ_CHUNK_BYTES, remaining) if remaining > 0 else 1

    def feed(self, chunk: bytes) -> None:
        self.observed_bytes += len(chunk)
        self._observed_digest.update(chunk)
        room = max(0, self.limit - len(self.prefix))
        retained = chunk[:room]
        if retained:
            self.prefix.extend(retained)
            self._prefix_digest.update(retained)
        if len(chunk) > room:
            self.truncated = True

    def metadata(self) -> dict[str, Any]:
        return {
            "limit_bytes": self.limit,
            "bytes_observed": self.observed_bytes,
            "bytes_retained": len(self.prefix),
            "truncated": self.truncated,
            "observed_sha256": self._observed_digest.hexdigest(),
            "prefix_sha256": self._prefix_digest.hexdigest(),
        }

    def prefix_base64(self) -> str:
        return base64.b64encode(self.prefix).decode("ascii")


def _provider_child_events_from_prefix(prefix: bytes) -> list[dict[str, Any]]:
    """Extract only small complete provider-child records from bounded bytes.

    Oversized query payloads are never handed to the general snapshot decoder.
    This narrow pass keeps already streamed nested-child identities available
    for cleanup evidence without parsing snapshot records or a large NDJSON
    line.
    """
    found: list[dict[str, Any]] = []
    start = 0
    while start < len(prefix):
        end = prefix.find(b"\n", start)
        if end < 0:
            break
        if end - start <= MAX_PROVIDER_EVENT_BYTES:
            try:
                record = json.loads(prefix[start:end])
            except (UnicodeDecodeError, json.JSONDecodeError):
                record = None
            if (type(record) is dict and record.get("kind") == "provider-child" and
                    type(record.get("provider_child")) is dict):
                child = record["provider_child"]
                pid = child.get("pid")
                prior = next((index for index, item in enumerate(found)
                              if item.get("pid") == pid), None)
                if prior is None:
                    found.append(child)
                else:
                    found[prior] = child
        start = end + 1
    return found


def _darwin_native_pin_cli_args(
    *,
    module_path: str | os.PathLike[str] | None,
    module_sha256: str | None,
    dylib_path: str | os.PathLike[str] | None,
    dylib_sha256: str | None,
) -> list[str]:
    values = (module_path, module_sha256, dylib_path, dylib_sha256)
    if all(value is None for value in values):
        return []
    if any(value is None for value in values):
        raise ReconciliationError("Darwin provider module and dylib paths/SHA-256 pins must be supplied together")
    module_file = Path(module_path)
    library_file = Path(dylib_path)
    if not module_file.is_absolute() or module_file.suffix != ".py" or not library_file.is_absolute():
        raise ReconciliationError("Darwin provider module and dylib paths must be absolute")
    for label, pin in (("module", module_sha256), ("dylib", dylib_sha256)):
        if not isinstance(pin, str) or len(pin) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in pin
        ):
            raise ReconciliationError("Darwin provider " + label + " SHA-256 pin is invalid")
    return [
        "--darwin-native-module-path", os.fspath(module_file),
        "--darwin-native-module-sha256", module_sha256,
        "--darwin-native-dylib-path", os.fspath(library_file),
        "--darwin-native-dylib-sha256", dylib_sha256,
    ]


def _capture_query_child(process: Any, *, capture_deadline: float, total_deadline: float,
                         clock: Callable[[], float]) -> dict[str, Any]:
    """Incrementally capture child pipes with fixed stdout/stderr storage caps."""
    captures = {
        "stdout": _BoundedCapture(MAX_RESULT_BYTES),
        "stderr": _BoundedCapture(MAX_QUERY_STDERR_BYTES),
    }
    selector = None
    error: BaseException | None = None
    timed_out = False
    output_limit = False
    kill_requested = False
    returncode = None
    reaped = False

    def drain_until(limit: float, *, stop_on_limit: bool) -> None:
        nonlocal output_limit
        if selector is None:
            return
        while selector.get_map():
            left = limit - clock()
            if left <= 0:
                return
            ready = selector.select(left)
            if not ready:
                return
            for key, _ in ready:
                label = key.data
                try:
                    chunk = os.read(key.fd, captures[label].read_size())
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                captures[label].feed(chunk)
                if captures[label].truncated:
                    output_limit = True
                    if stop_on_limit:
                        return

    try:
        selector = selectors.DefaultSelector()
        for label in ("stdout", "stderr"):
            stream = getattr(process, label, None)
            if stream is None:
                raise OSError("owned query child pipe is missing: " + label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        drain_until(capture_deadline, stop_on_limit=True)
        if not output_limit and not selector.get_map():
            try:
                left = max(0.0, capture_deadline - clock())
                returncode = process.wait(timeout=left)
                reaped = returncode is not None
            except subprocess.TimeoutExpired:
                timed_out = True
        elif not output_limit:
            timed_out = clock() >= capture_deadline
    except BaseException as caught:
        error = caught

    if output_limit or timed_out or error is not None:
        try:
            if process.poll() is None:
                process.kill()
                kill_requested = True
        except (OSError, ProcessLookupError):
            pass
        except BaseException as caught:
            error = error or caught
        # Reserve the final portion of the existing 100 ms cleanup window for
        # wait/poll. Draining stays bounded and only reads already-owned pipes.
        drain_deadline = max(clock(), total_deadline - QUERY_REAP_RESERVE_SECONDS)
        try:
            drain_until(drain_deadline, stop_on_limit=False)
        except BaseException as caught:
            error = error or caught
        try:
            left = max(0.0, total_deadline - clock())
            if left:
                process.wait(timeout=left)
        except (subprocess.TimeoutExpired, OSError):
            pass
        except BaseException as caught:
            error = error or caught
        try:
            returncode = process.poll()
        except BaseException as caught:
            error = error or caught
            returncode = getattr(process, "returncode", None)
        reaped = returncode is not None
    else:
        try:
            returncode = process.poll()
        except BaseException as caught:
            error = caught
            try:
                if process.poll() is None:
                    process.kill()
                    kill_requested = True
            except BaseException:
                pass
            try:
                left = max(0.0, total_deadline - clock())
                if left:
                    process.wait(timeout=left)
            except BaseException:
                pass
            try:
                returncode = getattr(process, "returncode", None)
            except BaseException:
                returncode = None
            reaped = returncode is not None
        else:
            reaped = returncode is not None

    if selector is not None:
        try:
            selector.close()
        except OSError:
            pass
    for label in ("stdout", "stderr"):
        stream = getattr(process, label, None)
        if stream is not None:
            try:
                stream.close()
            except BaseException:
                pass
    return {
        "captures": captures,
        "output_limit": output_limit,
        "timed_out": timed_out,
        "error": error,
        "returncode": returncode,
        "reaped": reaped,
        "kill_requested": kill_requested,
    }


def run_query_child(*, boundary_deadline: float, popen: Callable[..., Any] = subprocess.Popen,
                    clock: Callable[[], float] = time.monotonic,
                    python: str | None = None, script: Path = QUERY_SCRIPT,
                    env: dict[str, str] | None = None,
                    darwin_native_module_path: str | os.PathLike[str] | None = None,
                    darwin_native_module_sha256: str | None = None,
                    darwin_native_dylib_path: str | os.PathLike[str] | None = None,
                    darwin_native_dylib_sha256: str | None = None) -> dict[str, Any]:
    """Run one clean query child, bounded by the absolute five-second cap.

    ``boundary_deadline`` is the active phase/admission deadline, not a fresh
    budget. Timeout cleanup can signal only the direct Popen child.
    """
    start = clock()
    if not _finite_number(boundary_deadline):
        deadline = start
        return {
            "schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": "not-started",
            "snapshots": [],
            "outcome": {"status": "invalid-boundary-deadline", "complete": False,
                        "order_valid": False,
                        "error": {"type": "InvalidDeadline", "message": "existing phase/admission deadline is not finite"}},
            "started_monotonic": start,
            "ended_monotonic": clock(),
            "started_utc": _utc(),
            "ended_utc": _utc(),
            "deadline_monotonic": deadline,
            "duration_limit_seconds": 0.0,
            "query_child": {"pid": None, "returncode": None, "kill_requested": False,
                            "reaped": True, "cleanup_incomplete": False,
                            "direct_child_only": True,
                            "descendant_containment": "not-applicable-no-child-started"},
        }
    deadline = min(boundary_deadline, start + MAX_RECONCILIATION_SECONDS)
    if deadline <= start:
        return {
            "schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": "not-started",
            "snapshots": [],
            "outcome": {"status": "deadline-exhausted-before-query", "complete": False,
                        "order_valid": False,
                        "error": {"type": "DeadlineExceeded", "message": "existing phase/admission deadline has expired"}},
            "started_monotonic": start,
            "ended_monotonic": clock(),
            "started_utc": _utc(),
            "ended_utc": _utc(),
            "deadline_monotonic": deadline,
            "duration_limit_seconds": max(0.0, deadline - start),
            "query_child": {"pid": None, "returncode": None, "kill_requested": False,
                            "reaped": True, "cleanup_incomplete": False,
                            "direct_child_only": True,
                            "descendant_containment": "not-applicable-no-child-started"},
        }
    provider_deadline = deadline - QUERY_CLEANUP_RESERVE_SECONDS - QUERY_FINALIZE_RESERVE_SECONDS
    if provider_deadline <= start:
        return {
            "schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": "not-started",
            "snapshots": [],
            "outcome": {"status": "deadline-exhausted-before-query", "complete": False,
                        "order_valid": False,
                        "error": {"type": "DeadlineExceeded", "message": "no provider budget remains after direct-child cleanup reserve"}},
            "started_monotonic": start,
            "ended_monotonic": clock(),
            "started_utc": _utc(),
            "ended_utc": _utc(),
            "deadline_monotonic": deadline,
            "provider_deadline_monotonic": provider_deadline,
            "duration_limit_seconds": max(0.0, provider_deadline - start),
            "query_child": {"pid": None, "returncode": None, "kill_requested": False, "reaped": True,
                            "cleanup_incomplete": False, "direct_child_only": True,
                            "descendant_containment": "not-applicable-no-child-started"},
        }
    python = python or sys.executable
    child_env = env if env is not None else {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
    argv = [python, "-B", "-E", str(script), "--deadline-monotonic", repr(provider_deadline)]
    query_exit_deadline = deadline - QUERY_CLEANUP_RESERVE_SECONDS
    process = None
    capture = None
    native_provider_binding = None
    result: dict[str, Any]
    try:
        native_pin_args = _darwin_native_pin_cli_args(
            module_path=darwin_native_module_path,
            module_sha256=darwin_native_module_sha256,
            dylib_path=darwin_native_dylib_path,
            dylib_sha256=darwin_native_dylib_sha256,
        )
        if native_pin_args:
            native_provider_binding = {
                "schema": ABI4_NATIVE_BINDING_SCHEMA,
                "module_source_path": os.fspath(Path(darwin_native_module_path)),
                "module_source_sha256": darwin_native_module_sha256.lower(),
                "library_path": os.fspath(Path(darwin_native_dylib_path)),
                "library_sha256": darwin_native_dylib_sha256.lower(),
            }
        argv.extend(native_pin_args)
        process = popen(argv, cwd="/", env=child_env, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        capture = _capture_query_child(process, capture_deadline=query_exit_deadline,
                                       total_deadline=deadline, clock=clock)
        stdout_capture = capture["captures"]["stdout"]
        stderr_capture = capture["captures"]["stderr"]
        stdout_prefix = bytes(stdout_capture.prefix)
        stderr_prefix = bytes(stderr_capture.prefix)
        partial_status = capture["output_limit"] or capture["timed_out"] or capture["error"] is not None
        if capture["output_limit"]:
            known_children = _provider_child_events_from_prefix(stdout_prefix)
            output_name = "stdout" if stdout_capture.truncated else "stderr"
            result = {
                "schema": "v092-monitor06-reconciliation-query/v1",
                "provider_identity": "isolated-os-native-query-child",
                "snapshots": [],
                "provider_children": known_children,
                "outcome": {"status": "query-output-truncated", "complete": False,
                            "order_valid": False,
                            "error": {"type": "QueryOutputLimitExceeded",
                                      "message": output_name + " exceeded its bounded capture limit"}},
            }
        else:
            fallback = None
            if capture["timed_out"]:
                fallback = {"type": "DeadlineExceeded", "message": "isolated query exceeded its bounded capture deadline"}
            elif capture["error"] is not None:
                fallback = {"type": type(capture["error"]).__name__, "message": str(capture["error"])}
            result = _decode_query_stream(stdout_prefix, fallback_error=fallback)
            if capture["timed_out"]:
                result["outcome"] = {"status": "deadline-exceeded", "complete": False,
                                     "order_valid": False,
                                     "error": {"type": "DeadlineExceeded", "message": "isolated query exceeded its bounded capture deadline"}}
                result["timeout_output_bytes"] = stdout_capture.observed_bytes
            elif capture["error"] is not None:
                result["outcome"] = {"status": "query-child-error", "complete": False,
                                     "order_valid": False,
                                     "error": {"type": type(capture["error"]).__name__,
                                               "message": str(capture["error"])} }
            else:
                result["child_exit_code"] = capture["returncode"]
            result["child_stderr"] = stderr_prefix.decode("utf-8", "replace")[:4096]

        result["query_output_capture"] = {
            "stdout": stdout_capture.metadata(),
            "stderr": stderr_capture.metadata(),
            "capture_is_partial": partial_status,
        }
        if partial_status:
            # Preserve only fixed-size prefixes and hashes for partial streams;
            # no general decoder receives an over-limit stdout payload.
            result["partial_output_capture"] = {
                "label": "bounded-partial-output-prefix",
                "stdout_prefix_base64": stdout_capture.prefix_base64(),
                "stderr_prefix_base64": stderr_capture.prefix_base64(),
                "stdout": stdout_capture.metadata(),
                "stderr": stderr_capture.metadata(),
            }
        nested_complete = all(child.get("reaped") is True and child.get("cleanup_incomplete") is False
                              for child in result.get("provider_children", []))
        if capture["output_limit"]:
            containment = ("query-child-reaped; nested-provider-prefix-only"
                           if capture["reaped"] else "unproven-direct-child-cleanup-incomplete")
        elif capture["reaped"] and nested_complete and not partial_status:
            containment = "query-and-provider-children-reaped; no OS-global claim"
        elif capture["reaped"] and result.get("provider_children"):
            containment = "query-child-reaped; provider-child-state-recorded-but-incomplete"
        elif capture["reaped"]:
            containment = "query-child-reaped; provider-descendant-state-unknown"
        else:
            containment = "unproven-direct-child-cleanup-incomplete"
        result["query_child"] = {
            "pid": getattr(process, "pid", None),
            "returncode": capture["returncode"],
            "kill_requested": capture["kill_requested"],
            "reaped": capture["reaped"],
            "cleanup_incomplete": not capture["reaped"],
            "direct_child_only": True,
            "descendant_containment": containment,
        }
    except BaseException as error:
        # Popen construction errors have no pipes to inspect. All post-start
        # capture errors are converted to typed results by _capture_query_child.
        result = {
            "schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": "isolated-os-native-query-child",
            "snapshots": [],
            "provider_children": [],
            "outcome": {"status": "query-child-error", "complete": False,
                        "order_valid": False,
                        "error": {"type": type(error).__name__, "message": str(error)}},
            "query_child": {
                "pid": getattr(process, "pid", None),
                "returncode": getattr(process, "returncode", None),
                "kill_requested": False,
                "reaped": process is None or getattr(process, "returncode", None) is not None,
                "cleanup_incomplete": process is not None and getattr(process, "returncode", None) is None,
                "direct_child_only": True,
                "descendant_containment": "not-applicable-no-child-started" if process is None else "unproven",
            },
        }
    result.setdefault("started_monotonic", start)
    result.setdefault("started_utc", _utc())
    result["ended_monotonic"] = clock()
    result["ended_utc"] = _utc()
    result["deadline_monotonic"] = deadline
    result["provider_deadline_monotonic"] = provider_deadline
    result["duration_limit_seconds"] = max(0.0, provider_deadline - start)
    if native_provider_binding is not None:
        result["darwin_native_provider_binding"] = native_provider_binding
    result.setdefault("os_global_completeness_claim", False)
    result.setdefault("continuous_absence_claim", False)
    return result


_KERNEL_COMM_SOURCES = frozenset({
    "sysctl_kern_proc_all.p_comm",
    "sysctl_kern_proc_all.second_table_new.p_comm",
    "sysctl_kern_proc_all.first_table_only.p_comm",
    "proc_pidinfo.pbi_comm",
})


def _is_kernel_comm_source(source: object) -> bool:
    return isinstance(source, str) and source in _KERNEL_COMM_SOURCES


def _is_kernel_comm_fallback(row: dict[str, Any]) -> bool:
    return (
        row.get("command_source_is_kernel_comm") is True
        or _is_kernel_comm_source(row.get("command_source"))
    )


def _validate_rows(snapshot: dict[str, Any], *, native: bool) -> None:
    rows = snapshot.get("rows")
    if type(rows) is not list:
        raise ReconciliationError("snapshot rows are missing")
    seen = set()
    for row in rows:
        if type(row) is not dict:
            raise ReconciliationError("snapshot row is not an object")
        pid = row.get("pid")
        if type(pid) is not int or pid < 0 or pid in seen:
            raise ReconciliationError("snapshot PID is invalid, duplicated, or kernel PID zero was not excluded")
        if pid == 0 and row.get("kernel_pid0") is not True:
            raise ReconciliationError("PID zero is not explicitly identified as the kernel row")
        if pid > 0 and row.get("kernel_pid0") is True:
            raise ReconciliationError("positive PID is incorrectly marked as the kernel row")
        seen.add(pid)
        if not isinstance(row.get("command"), str) or not row["command"]:
            raise ReconciliationError("snapshot command field is missing")
        executable = row.get("command_executable")
        if not isinstance(executable, str) or not executable:
            raise ReconciliationError("snapshot executable field is missing")
        command_name = row.get("command_name")
        expected_name = os.path.basename(executable)
        if not isinstance(command_name, str) or not command_name or command_name != expected_name:
            raise ReconciliationError("snapshot command name does not match provider executable")
        if native:
            if pid == 0:
                raise ReconciliationError("native PID zero must be explicitly excluded and counted")
            if type(row.get("ppid")) is not int or row["ppid"] < 0:
                raise ReconciliationError("native PPID field is missing or invalid")
            if not isinstance(row.get("birth_identity"), str) or not row["birth_identity"]:
                raise ReconciliationError("native birth identity is missing")
            if not isinstance(row.get("state"), str) or not row["state"]:
                raise ReconciliationError("native state field is missing")
            command_source = row.get("command_source")
            kernel_comm_flag = row.get("command_source_is_kernel_comm")
            if kernel_comm_flag is not None and type(kernel_comm_flag) is not bool:
                raise ReconciliationError("native kernel-comm source flag is malformed")
            kernel_comm_source = _is_kernel_comm_source(command_source)
            if kernel_comm_source and kernel_comm_flag is False:
                raise ReconciliationError("native kernel-comm source contradicts its source flag")
            if kernel_comm_flag is True:
                if not kernel_comm_source:
                    raise ReconciliationError("native kernel-comm flag disagrees with command source")
                if row.get("command_arguments_available") is not False:
                    raise ReconciliationError("kernel-comm fallback incorrectly claims full command arguments")
                if command_source == "sysctl_kern_proc_all.second_table_new.p_comm":
                    if (row.get("command_path_status") != "not-attempted-second-table-new" or
                            row.get("command_path_errno") is not None or
                            row.get("native_snapshot_origin") != "second-table-only" or
                            row.get("revalidation_witness") != "second-table-only-unverified"):
                        raise ReconciliationError("second-table-only kernel-comm provenance is incomplete")
                elif command_source == "sysctl_kern_proc_all.first_table_only.p_comm":
                    path_errno = row.get("command_path_errno")
                    if (row.get("command_path_status") != "discarded-unrevalidated-first-table-only" or
                            type(path_errno) is not int or path_errno < 0 or
                            row.get("native_snapshot_origin") != "first-table-only" or
                            row.get("revalidation_witness") != "first-table-only-unverified"):
                        raise ReconciliationError("first-table-only kernel-comm provenance is incomplete")
                elif command_source != "proc_pidinfo.pbi_comm":
                    path_errno = row.get("command_path_errno")
                    if (row.get("command_path_status") != "short-comm-fallback" or
                            type(path_errno) is not int or path_errno < 0 or
                            row.get("command_arguments_available") is not False):
                        raise ReconciliationError("kernel-comm fallback metadata is incomplete")
        else:
            cpu = row.get("cpu_percent")
            if type(cpu) not in (int, float) or not math.isfinite(cpu) or cpu < 0:
                raise ReconciliationError("actual command-provider CPU percentage is missing")
            if not isinstance(row.get("comm"), str) or not row["comm"]:
                raise ReconciliationError("actual command-provider comm field is missing")
            if not isinstance(row.get("args"), str) or row["args"] != row["command"]:
                raise ReconciliationError("actual command-provider argv field is missing or differs")
            raw_row = row.get("raw_row")
            if not isinstance(raw_row, str):
                raise ReconciliationError("raw command-provider row is missing")
            fields = raw_row.split(None, 3)
            try:
                cpu_matches = len(fields) == 4 and float(fields[1]) == float(cpu)
            except ValueError:
                cpu_matches = False
            if (len(fields) != 4 or fields[0] != str(pid) or fields[2] != row["comm"] or
                    fields[3] != row["args"] or not cpu_matches):
                raise ReconciliationError("structured command row differs from raw provider row")


def _validate_abi3_native_snapshot(snapshot: dict[str, Any]) -> None:
    """Validate ABI-v3 provider provenance and exact two-table accounting."""
    rows = snapshot.get("rows")
    coverage = snapshot.get("coverage")
    if type(rows) is not list or type(coverage) is not dict:
        raise ReconciliationError("ABI-v3 native snapshot rows or coverage are missing")
    evidence = coverage.get("provider_evidence")
    if type(evidence) is not dict:
        raise ReconciliationError("ABI-v3 native provider evidence is missing")
    if (evidence.get("identity") != "darwin-sysctl-kern-proc-all-libproc/v3" or
            type(evidence.get("abi_version")) is not int or evidence.get("abi_version") != 3 or
            evidence.get("test_only_injected_library") is not False or
            type(evidence.get("first_table_sysctl_calls")) is not int or
            evidence.get("first_table_sysctl_calls") != 1 or
            type(evidence.get("revalidation_table_sysctl_calls")) is not int or
            evidence.get("revalidation_table_sysctl_calls") != 1 or
            evidence.get("historical_absence_claim") is not False):
        raise ReconciliationError("ABI-v3 native provider identity or call provenance is invalid")

    def count(name: str) -> int:
        value = evidence.get(name)
        if type(value) is not int or value < 0 or value > 8192:
            raise ReconciliationError("ABI-v3 native provider count is missing or out of bounds: " + name)
        return value

    library_digest = evidence.get("library_sha256")
    module_digest = evidence.get("module_source_sha256")
    if (not isinstance(library_digest, str) or len(library_digest) != 64 or
            any(character not in "0123456789abcdef" for character in library_digest) or
            not isinstance(module_digest, str) or len(module_digest) != 64 or
            any(character not in "0123456789abcdef" for character in module_digest) or
            not isinstance(evidence.get("library_path"), str) or
            not Path(evidence["library_path"]).is_absolute() or
            not isinstance(evidence.get("module_source_path"), str) or
            not Path(evidence["module_source_path"]).is_absolute()):
        raise ReconciliationError("ABI-v3 source or library pin evidence is malformed")
    if (snapshot.get("provider_identity") != evidence["identity"] or
            not isinstance(evidence.get("scope"), str) or not evidence["scope"]):
        raise ReconciliationError("ABI-v3 provider scope or identity evidence is inconsistent")

    first_pid0 = count("first_snapshot_excluded_pid0_count")
    second_pid0 = count("second_snapshot_excluded_pid0_count")
    if first_pid0 > 1 or second_pid0 > 1:
        raise ReconciliationError("ABI-v3 provider PID-zero exclusion count exceeds one row")
    revalidated = count("revalidated_first_row_count")
    second_records = count("second_snapshot_record_count")
    added = count("additional_second_snapshot_pid_count")
    second_only_output = count("second_table_only_output_row_count")
    first_rows = len(rows) - added
    # The provider's enumerated count is the raw first-table record count,
    # which includes its excluded PID-zero row, plus second-table-only rows.
    if (type(coverage.get("returned_pid_count")) is not int or
            type(coverage.get("enumerated_pid_count")) is not int or
            type(coverage.get("excluded_pid0_kernel_entries")) is not int or
            first_rows < 0 or added != second_only_output or
            revalidated != first_rows or
            second_records != first_rows + added + second_pid0 or
            coverage.get("returned_pid_count") != len(rows) or
            coverage.get("enumerated_pid_count") != first_rows + added + first_pid0 or
            coverage.get("excluded_pid0_kernel_entries") != first_pid0):
        raise ReconciliationError("ABI-v3 native provider coverage equations do not balance")

    first_seen = 0
    second_only_seen = 0
    for row in rows:
        source = row.get("command_source")
        birth_identity = row.get("birth_identity")
        birth_fields = birth_identity.split(":") if isinstance(birth_identity, str) else []
        try:
            birth_seconds = int(birth_fields[0]) if len(birth_fields) == 2 else 0
            birth_microseconds = int(birth_fields[1]) if len(birth_fields) == 2 else -1
        except ValueError:
            birth_seconds, birth_microseconds = 0, -1
        command = row.get("command")
        command_bytes = command.encode("utf-8") if isinstance(command, str) else b""
        if (len(birth_fields) != 2 or not all(field.isdecimal() for field in birth_fields) or
                not 0 < birth_seconds < 2**64 or not 0 <= birth_microseconds < 1_000_000 or
                row["pid"] > 2**31 - 1 or row["ppid"] > 2**31 - 1 or
                row.get("state") not in {"R", "S", "T", "Z"} or
                command != row.get("command_executable") or not command_bytes or
                len(command_bytes) > 4096 or b"\0" in command_bytes):
            raise ReconciliationError("ABI-v3 PID birth, state, or command identity fields are malformed")
        if (row.get("command_arguments_available") is not False or
                row.get("command_source_is_kernel_comm") is not (source != "proc_pidpath")):
            raise ReconciliationError("ABI-v3 command-source flag or argv provenance is invalid")
        if source == "proc_pidpath":
            if (not Path(command).is_absolute() or
                    row.get("command_path_status") != "resolved" or
                    type(row.get("command_path_errno")) is not int or
                    row.get("command_path_errno") != 0 or
                    row.get("native_snapshot_origin") != "first-table" or
                    row.get("revalidation_witness") != "matched-in-second-table"):
                raise ReconciliationError("ABI-v3 proc_pidpath row provenance is invalid")
            first_seen += 1
        elif source == "sysctl_kern_proc_all.p_comm":
            path_errno = row.get("command_path_errno")
            if (row.get("command_path_status") != "short-comm-fallback" or
                    type(path_errno) is not int or path_errno < 0 or
                    row.get("native_snapshot_origin") != "first-table" or
                    row.get("revalidation_witness") != "matched-in-second-table"):
                raise ReconciliationError("ABI-v3 first-table p_comm fallback provenance is invalid")
            first_seen += 1
        elif source == "sysctl_kern_proc_all.second_table_new.p_comm":
            if (row.get("command_path_status") != "not-attempted-second-table-new" or
                    row.get("command_path_errno") is not None or
                    row.get("native_snapshot_origin") != "second-table-only" or
                    row.get("revalidation_witness") != "second-table-only-unverified"):
                raise ReconciliationError("ABI-v3 second-table-only row provenance is invalid")
            second_only_seen += 1
        else:
            raise ReconciliationError("ABI-v3 native row uses an unrecognized exact command source")
    if first_seen != first_rows or second_only_seen != added:
        raise ReconciliationError("ABI-v3 native row source counts differ from provider evidence")


def _validate_abi4_binding(value: Any) -> dict[str, str]:
    if (type(value) is not dict or set(value) != {
            "schema", "module_source_path", "module_source_sha256", "library_path", "library_sha256"} or
            value.get("schema") != ABI4_NATIVE_BINDING_SCHEMA):
        raise ReconciliationError("ABI-v4 caller-bound source/library pins are missing or malformed")
    for path_name in ("module_source_path", "library_path"):
        path = value.get(path_name)
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ReconciliationError("ABI-v4 pinned provider path is not absolute: " + path_name)
    for digest_name in ("module_source_sha256", "library_sha256"):
        digest = value.get(digest_name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ReconciliationError("ABI-v4 pinned provider digest is malformed: " + digest_name)
    if (value["module_source_path"] != ABI4_PROVIDER_MODULE_PATH or
            value["module_source_sha256"] != ABI4_PROVIDER_MODULE_SHA256 or
            value["library_path"] != ABI4_PROVIDER_LIBRARY_PATH or
            value["library_sha256"] != ABI4_PROVIDER_LIBRARY_SHA256):
        raise ReconciliationError("ABI-v4 caller-bound source/library pins are not the exact approved refs")
    return value


def _bounded_abi4_count(value: Any, name: str, *, upper_exclusive: int) -> int:
    if type(value) is not int or value < 0 or value >= upper_exclusive:
        raise ReconciliationError("ABI-v4 provider count is missing or out of bounds: " + name)
    return value


def _validate_abi4_native_snapshot(
    snapshot: dict[str, Any], expected_binding: dict[str, str]
) -> None:
    """Validate ABI4 source pins, row provenance, and both-table equations."""
    rows = snapshot.get("rows")
    coverage = snapshot.get("coverage")
    if type(rows) is not list or type(coverage) is not dict:
        raise ReconciliationError("ABI-v4 native snapshot rows or coverage are missing")
    evidence = coverage.get("provider_evidence")
    if type(evidence) is not dict:
        raise ReconciliationError("ABI-v4 native provider evidence is missing")
    expected_evidence_keys = {
        "identity", "abi_version", "library_sha256", "test_only_injected_library",
        "first_table_sysctl_calls", "revalidation_table_sysctl_calls",
        "first_snapshot_record_count", "second_snapshot_record_count",
        "first_snapshot_excluded_pid0_count", "second_snapshot_excluded_pid0_count",
        "revalidated_first_row_count", "first_table_only_pid_count",
        "first_table_only_output_row_count", "additional_second_snapshot_pid_count",
        "second_table_only_output_row_count", "output_row_count",
        "historical_absence_claim", "scope", "module_source_path",
        "module_source_sha256", "library_path",
    }
    if set(evidence) != expected_evidence_keys:
        raise ReconciliationError("ABI-v4 provider evidence fields differ from the pinned schema")
    if (evidence.get("identity") != ABI4_NATIVE_PROVIDER_IDENTITY or
            snapshot.get("provider_identity") != ABI4_NATIVE_PROVIDER_IDENTITY or
            type(evidence.get("abi_version")) is not int or evidence.get("abi_version") != 4 or
            evidence.get("test_only_injected_library") is not False or
            type(evidence.get("historical_absence_claim")) is not bool or
            evidence.get("historical_absence_claim") is not False or
            type(evidence.get("first_table_sysctl_calls")) is not int or
            evidence.get("first_table_sysctl_calls") != 1 or
            type(evidence.get("revalidation_table_sysctl_calls")) is not int or
            evidence.get("revalidation_table_sysctl_calls") != 1 or
            not isinstance(evidence.get("scope"), str) or not evidence["scope"]):
        raise ReconciliationError("ABI-v4 provider identity or one-call provenance is invalid")
    actual_binding = {
        "schema": ABI4_NATIVE_BINDING_SCHEMA,
        "module_source_path": evidence.get("module_source_path"),
        "module_source_sha256": evidence.get("module_source_sha256"),
        "library_path": evidence.get("library_path"),
        "library_sha256": evidence.get("library_sha256"),
    }
    if actual_binding != expected_binding:
        raise ReconciliationError("ABI-v4 provider evidence differs from caller-bound module/library pins")

    def count(name: str) -> int:
        return _bounded_abi4_count(
            evidence.get(name), name, upper_exclusive=ABI4_MAX_ROWS_PER_TABLE
        )

    first_raw = count("first_snapshot_record_count")
    second_raw = count("second_snapshot_record_count")
    first_pid0 = count("first_snapshot_excluded_pid0_count")
    second_pid0 = count("second_snapshot_excluded_pid0_count")
    stable_count = count("revalidated_first_row_count")
    first_only_pid_count = count("first_table_only_pid_count")
    first_only_output = count("first_table_only_output_row_count")
    second_only_count = count("additional_second_snapshot_pid_count")
    second_only_output = count("second_table_only_output_row_count")
    output_count = count("output_row_count")
    if (first_pid0 > 1 or second_pid0 > 1 or
            first_only_pid_count != first_only_output or
            second_only_count != second_only_output or
            first_raw != stable_count + first_only_output + first_pid0 or
            second_raw != stable_count + second_only_output + second_pid0 or
            output_count != stable_count + first_only_output + second_only_output or
            output_count != len(rows)):
        raise ReconciliationError("ABI-v4 provider first/second/output equations do not balance")
    if (type(coverage.get("pid_capacity")) is not int or
            coverage["pid_capacity"] != ABI4_MAX_ROWS_PER_TABLE or
            coverage.get("enumerated_pid_count") != first_raw + second_only_count or
            coverage.get("returned_pid_count") != output_count or
            coverage.get("excluded_pid0_kernel_entries") != first_pid0):
        raise ReconciliationError("ABI-v4 native coverage counts differ from provider evidence")

    stable_seen = 0
    first_only_seen = 0
    second_only_seen = 0
    for row in rows:
        pid = row["pid"]
        ppid = row["ppid"]
        birth = row.get("birth_identity")
        fields = birth.split(":") if isinstance(birth, str) else []
        try:
            seconds = int(fields[0]) if len(fields) == 2 else 0
            micros = int(fields[1]) if len(fields) == 2 else -1
        except ValueError:
            seconds, micros = 0, -1
        command = row.get("command")
        command_bytes = command.encode("utf-8") if isinstance(command, str) else b""
        if (pid > 2**31 - 1 or ppid > 2**31 - 1 or
                len(fields) != 2 or not all(part.isdecimal() for part in fields) or
                not 0 < seconds < 2**64 or not 0 <= micros < 1_000_000 or
                row.get("state") not in {"R", "S", "T", "Z"} or
                command != row.get("command_executable") or not command_bytes or
                len(command_bytes) > 4096 or b"\0" in command_bytes or
                row.get("command_name") != os.path.basename(command)):
            raise ReconciliationError("ABI-v4 PID/birth/state/p_comm identity fields are malformed")
        if (row.get("command_arguments_available") is not False or
                row.get("command_source_is_kernel_comm") is not (row.get("command_source") != "proc_pidpath")):
            raise ReconciliationError("ABI-v4 command-source flag or argv provenance is invalid")

        source = row.get("command_source")
        origin = row.get("native_snapshot_origin")
        witness = row.get("revalidation_witness")
        if source == "proc_pidpath":
            if (origin != "first-table" or witness != "matched-in-second-table" or
                    row.get("command_path_status") != "resolved" or
                    type(row.get("command_path_errno")) is not int or
                    row["command_path_errno"] != 0 or not Path(command).is_absolute() or
                    row.get("command_source_is_kernel_comm") is not False):
                raise ReconciliationError("ABI-v4 stable proc_pidpath row provenance is invalid")
            stable_seen += 1
        elif source == "sysctl_kern_proc_all.p_comm":
            path_errno = row.get("command_path_errno")
            if (origin != "first-table" or witness != "matched-in-second-table" or
                    row.get("command_path_status") != "short-comm-fallback" or
                    type(path_errno) is not int or path_errno < 0 or
                    row.get("command_source_is_kernel_comm") is not True):
                raise ReconciliationError("ABI-v4 stable p_comm fallback provenance is invalid")
            stable_seen += 1
        elif source == "sysctl_kern_proc_all.first_table_only.p_comm":
            path_errno = row.get("command_path_errno")
            if (origin != "first-table-only" or witness != "first-table-only-unverified" or
                    row.get("command_path_status") != "discarded-unrevalidated-first-table-only" or
                    type(path_errno) is not int or path_errno < 0 or
                    row.get("command_source_is_kernel_comm") is not True):
                raise ReconciliationError("ABI-v4 first-table-only p_comm provenance is invalid")
            first_only_seen += 1
        elif source == "sysctl_kern_proc_all.second_table_new.p_comm":
            if (origin != "second-table-only" or witness != "second-table-only-unverified" or
                    row.get("command_path_status") != "not-attempted-second-table-new" or
                    row.get("command_path_errno") is not None or
                    row.get("command_source_is_kernel_comm") is not True):
                raise ReconciliationError("ABI-v4 second-table-only p_comm provenance is invalid")
            second_only_seen += 1
        else:
            raise ReconciliationError("ABI-v4 native row has an unknown command source")
    if (stable_seen != stable_count or first_only_seen != first_only_output or
            second_only_seen != second_only_output):
        raise ReconciliationError("ABI-v4 row provenance counts differ from provider evidence")


def _validate_ps_v2_snapshot(snapshot: dict[str, Any]) -> None:
    """Bind v2 structured rows and classifier projections to raw fixed-column bytes."""
    rows = snapshot.get("rows")
    coverage = snapshot.get("coverage")
    raw_table = snapshot.get("table")
    classifier_table = snapshot.get("classifier_table")
    if (type(rows) is not list or type(coverage) is not dict or
            not isinstance(raw_table, str) or not isinstance(classifier_table, str)):
        raise ReconciliationError("ps-v2 raw or classifier table is missing")
    try:
        raw_bytes = raw_table.encode("utf-8", "strict")
    except UnicodeEncodeError as error:
        raise ReconciliationError("ps-v2 raw table is not valid UTF-8 text") from error
    digest = coverage.get("raw_stdout_sha256")
    if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or
            hashlib.sha256(raw_bytes).hexdigest() != digest or
            type(coverage.get("raw_stdout_bytes")) is not int or
            coverage["raw_stdout_bytes"] != len(raw_bytes)):
        raise ReconciliationError("ps-v2 raw stdout digest or byte count does not match table")
    if (coverage.get("format_identity") != "fixed-four-64-byte-columns/v1" or
            coverage.get("raw_header") != PS_V2_HEADER_BYTES.decode("ascii") or
            b"\r" in raw_bytes or not raw_bytes.endswith(b"\n")):
        raise ReconciliationError("ps-v2 output header or raw line framing is invalid")
    lines = raw_bytes.split(b"\n")
    if lines[-1] != b"" or not lines or lines[0] != PS_V2_HEADER_BYTES:
        raise ReconciliationError("ps-v2 output header or final delimiter is invalid")
    data_lines = lines[1:-1]
    if (len(data_lines) > 8192 or len(rows) != len(data_lines) or
            coverage.get("enumerated_pid_count") != len(data_lines) or
            coverage.get("returned_pid_count") != len(rows) or
            coverage.get("excluded_pid0_kernel_entries") != 0 or
            coverage.get("kernel_pid0_rows_observed") != sum(
                type(row) is dict and row.get("pid") == 0 for row in rows
            )):
        raise ReconciliationError("ps-v2 row counts or PID-zero accounting differ from raw table")

    projection_lines: list[str] = []
    seen_pids: set[int] = set()
    for row, line in zip(rows, data_lines):
        if type(row) is not dict or not line or len(line) > 64 * 1024 or len(line) < 195:
            raise ReconciliationError("ps-v2 raw row is empty or outside its byte bound")
        if line[64:65] != b" " or line[129:130] != b" " or line[194:195] != b" ":
            raise ReconciliationError("ps-v2 row does not use the approved fixed delimiters")
        pid_field, cpu_field = line[:64], line[65:129]
        ucomm_field, args_field = line[130:194], line[195:]
        pid_token_bytes = pid_field.lstrip(b" ")
        cpu_token_bytes = cpu_field.lstrip(b" ")
        if (not pid_token_bytes.isdigit() or
                pid_field != pid_token_bytes.rjust(PS_V2_FIELD_WIDTH, b" ") or
                not cpu_token_bytes or
                cpu_field != cpu_token_bytes.rjust(PS_V2_FIELD_WIDTH, b" ")):
            raise ReconciliationError("ps-v2 PID or CPU fixed-width field is malformed")
        try:
            pid_token = pid_token_bytes.decode("ascii", "strict")
            cpu_token = cpu_token_bytes.decode("ascii", "strict")
            ucomm_raw_field = ucomm_field.decode("utf-8", "strict")
            args = args_field.decode("utf-8", "strict")
            raw_row = line.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise ReconciliationError("ps-v2 field is not valid UTF-8/ASCII") from error
        if (not re.fullmatch(r"[0-9]+", pid_token) or not re.fullmatch(
                r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", cpu_token)):
            raise ReconciliationError("ps-v2 PID or CPU token syntax is unknown")
        try:
            pid = int(pid_token)
            cpu = float(cpu_token)
        except ValueError as error:
            raise ReconciliationError("ps-v2 PID or CPU token is malformed") from error
        if (pid < 0 or pid in seen_pids or not math.isfinite(cpu) or cpu < 0 or
                type(row.get("pid")) is not int or row.get("pid") != pid or
                row.get("pid_token") != pid_token or
                type(row.get("cpu_percent")) is not float or row.get("cpu_percent") != cpu or
                row.get("cpu_token") != cpu_token or row.get("ucomm_raw_field") != ucomm_raw_field or
                row.get("raw_row") != raw_row):
            raise ReconciliationError("ps-v2 structured identity or CPU differs from raw fixed fields")
        seen_pids.add(pid)
        if (not ucomm_field.strip(b" ") or
                any(byte < 0x20 or byte == 0x7F for byte in ucomm_field) or
                any(unicodedata.category(character) == "Cc" for character in ucomm_raw_field)):
            raise ReconciliationError("ps-v2 ucomm fixed field is empty or contains a control character")
        if (not args_field or len(args_field) > PS_V2_ARG_LIMIT or
                any(byte < 0x20 or byte == 0x7F for byte in args_field) or
                row.get("args") != args or row.get("command") != args):
            raise ReconciliationError("ps-v2 argv differs from raw args or contains malformed controls")
        argv_fields = args.split(None, 1)
        if not argv_fields:
            raise ReconciliationError("ps-v2 args field lacks argv[0]")
        executable = argv_fields[0]
        command_name = Path(executable).name
        if (not command_name or row.get("command_executable") != executable or
                row.get("command_name") != command_name or row.get("command_source") != "ps-argv" or
                row.get("command_arguments_available") is not True or
                row.get("kernel_pid0") is not (pid == 0)):
            raise ReconciliationError("ps-v2 parsed argv fields differ from raw args")
        expected_projection = f"{pid_token} {cpu_token} {PS_V2_CLASSIFIER_MARKER} {args}"
        if row.get("classifier_row") != expected_projection:
            raise ReconciliationError("ps-v2 classifier projection differs from validated raw fields")
        projection_lines.append(expected_projection)
    expected_classifier_table = "\n".join(projection_lines) + ("\n" if projection_lines else "")
    if classifier_table != expected_classifier_table:
        raise ReconciliationError("ps-v2 classifier table differs from its validated row projections")


def validate_query_result(query: dict[str, Any], *, deadline: float) -> None:
    if type(query) is not dict or query.get("schema") != "v092-monitor06-reconciliation-query/v1":
        raise ReconciliationError("reconciliation query schema is invalid")
    if query.get("os_global_completeness_claim") is not False or query.get("continuous_absence_claim") is not False:
        raise ReconciliationError("query overclaims provider scope or continuous absence")
    child = query.get("query_child")
    if (type(child) is not dict or type(child.get("pid")) is not int or child["pid"] <= 0 or
            child.get("direct_child_only") is not True or child.get("reaped") is not True or
            child.get("cleanup_incomplete") is not False or child.get("returncode") != 0 or
            child.get("kill_requested") is not False):
        raise ReconciliationError("owned query child identity/reap state is missing or incomplete")
    provider_children = query.get("provider_children")
    if type(provider_children) is not list or len(provider_children) != 1:
        raise ReconciliationError("exactly one bounded command-provider child is required")
    for provider_child in provider_children:
        if (type(provider_child) is not dict or type(provider_child.get("pid")) is not int or
                provider_child["pid"] <= 0 or provider_child.get("direct_child_only") is not True or
                provider_child.get("provider_identity") not in {PS_V1_IDENTITY, PS_V2_IDENTITY} or
                provider_child.get("reaped") is not True or provider_child.get("cleanup_incomplete") is not False or
                provider_child.get("returncode") != 0 or provider_child.get("kill_requested") is not False or
                not _finite_number(provider_child.get("started_monotonic")) or
                not _finite_number(provider_child.get("ended_monotonic")) or
                provider_child["started_monotonic"] > provider_child["ended_monotonic"] or
                not _utc_timestamp(provider_child.get("started_utc")) or
                not _utc_timestamp(provider_child.get("ended_utc"))):
            raise ReconciliationError("nested provider child PID or cleanup state is uncertain")
    if provider_children[0]["pid"] == child["pid"]:
        raise ReconciliationError("query child and nested command-provider child PID collide")
    outcome = query.get("outcome")
    if type(outcome) is not dict or outcome.get("complete") is not True or outcome.get("order_valid") is not True:
        raise ReconciliationError("provider-scoped complete observation was not established")
    if query.get("provider_identity") != "monitor06-native-command-native/v1":
        raise ReconciliationError("provider identity is missing")
    snapshots = query.get("snapshots")
    expected_names = ["native-before", "command", "native-after"]
    if type(snapshots) is not list or len(snapshots) != 3 or [s.get("name") for s in snapshots if type(s) is dict] != expected_names:
        raise ReconciliationError("native-before, command, native-after snapshot order is incomplete")
    previous_end = None
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot.get("provider_identity"), str) or not snapshot["provider_identity"]:
            raise ReconciliationError("snapshot provider identity is missing")
        if snapshot.get("complete") is not True or snapshot.get("truncated") is not False or snapshot.get("error") is not None:
            raise ReconciliationError("provider reports incomplete, truncated, or erroring snapshot")
        scope = snapshot.get("provider_scope")
        if not isinstance(scope, str) or "not os-global" not in scope.lower():
            raise ReconciliationError("provider scope metadata is missing or overclaims")
        started, ended = snapshot.get("started_monotonic"), snapshot.get("ended_monotonic")
        if not _finite_number(started) or not _finite_number(ended) or started > ended or ended > deadline:
            raise ReconciliationError("snapshot monotonic bounds are invalid or exceed deadline")
        if not _utc_timestamp(snapshot.get("started_utc")) or not _utc_timestamp(snapshot.get("ended_utc")):
            raise ReconciliationError("snapshot UTC timestamps are missing")
        if previous_end is not None and started < previous_end:
            raise ReconciliationError("snapshot order overlaps or reverses")
        previous_end = ended
        coverage = snapshot.get("coverage")
        if type(coverage) is not dict or coverage.get("truncated") is not False:
            raise ReconciliationError("provider coverage metadata is incomplete or truncated")
        if type(coverage.get("enumerated_pid_count")) is not int or type(coverage.get("returned_pid_count")) is not int:
            raise ReconciliationError("provider row counts are missing")
        if coverage["enumerated_pid_count"] < coverage["returned_pid_count"]:
            raise ReconciliationError("provider returned more rows than it enumerated")
        if coverage.get("coverage_errors") != []:
            raise ReconciliationError("provider reports a coverage error")
        if type(coverage.get("excluded_pid0_kernel_entries")) is not int or coverage["excluded_pid0_kernel_entries"] < 0:
            raise ReconciliationError("PID zero/kernel exclusion accounting is missing")
        if coverage["enumerated_pid_count"] != coverage["returned_pid_count"] + coverage["excluded_pid0_kernel_entries"]:
            raise ReconciliationError("provider enumeration contains an unaccounted row omission")
        if index == 1:
            command_provider_identity = snapshot["provider_identity"]
            if command_provider_identity == PS_V1_IDENTITY:
                _validate_rows(snapshot, native=False)
                if not isinstance(snapshot.get("table"), str):
                    raise ReconciliationError("command provider table text is missing")
                if snapshot["table"].splitlines() != [row["raw_row"] for row in snapshot["rows"]]:
                    raise ReconciliationError("raw command table differs from structured provider rows")
                if coverage.get("kernel_pid0_rows_observed") != sum(row["pid"] == 0 for row in snapshot["rows"]):
                    raise ReconciliationError("command provider PID zero accounting differs from rows")
            elif command_provider_identity == PS_V2_IDENTITY:
                _validate_ps_v2_snapshot(snapshot)
            else:
                raise ReconciliationError("fresh command snapshot used an unknown ps provider format")
            provider_child = coverage.get("provider_child")
            if (type(provider_child) is not dict or
                    provider_children[0].get("provider_identity") != command_provider_identity or
                    provider_child.get("pid") != provider_children[0]["pid"] or
                    provider_child.get("reaped") is not True or provider_child.get("cleanup_incomplete") is not False or
                    provider_child.get("returncode") != 0 or provider_child.get("kill_requested") is not False or
                    provider_child.get("provider_identity") != command_provider_identity or
                    not _finite_number(provider_child.get("started_monotonic")) or
                    not _finite_number(provider_child.get("ended_monotonic")) or
                    not _utc_timestamp(provider_child.get("started_utc")) or
                    not _utc_timestamp(provider_child.get("ended_utc")) or
                    provider_child.get("started_monotonic", math.inf) < started or
                    provider_child.get("ended_monotonic", -math.inf) > ended or
                    provider_child.get("ended_monotonic", math.inf) > deadline):
                raise ReconciliationError("command snapshot does not retain its bounded provider child receipt")
        else:
            _validate_rows(snapshot, native=True)
            identity = snapshot["provider_identity"]
            if identity == ABI3_NATIVE_PROVIDER_IDENTITY:
                _validate_abi3_native_snapshot(snapshot)
            elif identity == ABI4_NATIVE_PROVIDER_IDENTITY:
                binding = _validate_abi4_binding(query.get("darwin_native_provider_binding"))
                _validate_abi4_native_snapshot(snapshot, binding)
            elif identity != "linux-procfs-proc-stat-cmdline-comm/v1":
                raise ReconciliationError("native snapshot used an unknown provider ABI")
            if any(row.get("native_snapshot_origin") == "first-table-only"
                   for row in snapshot["rows"]) and identity != ABI4_NATIVE_PROVIDER_IDENTITY:
                raise ReconciliationError("first-table-only rows require exact ABI-v4 provider evidence")
            if index == 0:
                native_provider_identity = identity
            elif identity != native_provider_identity:
                raise ReconciliationError("native provider identity changed across the ordered pass")
    if (native_provider_identity == ABI4_NATIVE_PROVIDER_IDENTITY and
            len(snapshots[0]["rows"]) + len(snapshots[2]["rows"]) > ABI4_MAX_OUTER_NATIVE_ROWS):
        raise ReconciliationError("ABI-v4 outer native observation row aggregate exceeds its bound")
    if not _finite_number(query.get("started_monotonic")) or not _finite_number(query.get("ended_monotonic")) or query["started_monotonic"] > query["ended_monotonic"] or query["ended_monotonic"] > deadline:
        raise ReconciliationError("query result completed after its absolute deadline")
    if not _utc_timestamp(query.get("started_utc")) or not _utc_timestamp(query.get("ended_utc")):
        raise ReconciliationError("query UTC start/end timestamps are missing")


def unresolved_candidates(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Select only originally rejected rows with no usable native birth."""
    candidates = []
    by_pid = {item.get("pid"): item for item in snapshot.get("rejected_command_rows", [])
              if type(item) is dict and type(item.get("pid")) is int}
    for line in snapshot.get("contenders", []):
        fields = str(line).split(None, 1)
        if not fields or not fields[0].isdigit():
            continue
        pid = int(fields[0])
        rejected = by_pid.get(pid)
        if rejected is None:
            continue
        native = rejected.get("native")
        if type(native) is not dict or not isinstance(native.get("birth_identity"), str) or not native.get("birth_identity"):
            candidates.append({"pid": pid, "row": rejected.get("row", line), "native": native})
    return candidates


def _native_map(snapshot: dict[str, Any]) -> dict[int, tuple[int, str, str]]:
    return {row["pid"]: (row["ppid"], row["birth_identity"], row["state"])
            for row in snapshot["rows"]
            if row.get("native_snapshot_origin") != "first-table-only"}


def _current_native_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Exclude unverified historical rows from every current/bridge projection."""
    return [row for row in snapshot["rows"]
            if row.get("native_snapshot_origin") != "first-table-only"]


def _first_only_observations(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observations = []
    for index in (0, 2):
        snapshot = snapshots[index]
        for row in snapshot["rows"]:
            if row.get("native_snapshot_origin") == "first-table-only":
                observations.append({
                    "pid": row.get("pid"),
                    "origin_snapshot": snapshot["name"],
                    "provider_identity": snapshot["provider_identity"],
                    "row": row,
                })
    return observations


def _rejected_first_only_observations(
    observations: list[dict[str, Any]], snapshots: list[dict[str, Any]], reason: str,
) -> list[dict[str, Any]]:
    rejected = []
    for observation in observations:
        snapshot_name = observation["origin_snapshot"]
        snapshot = next(item for item in snapshots if item["name"] == snapshot_name)
        provider_evidence = snapshot.get("coverage", {}).get("provider_evidence", {})
        rejected.append({
            "pid": observation["pid"],
            "origin_snapshot": snapshot_name,
            "provider_identity": observation["provider_identity"],
            "provider_evidence": dict(provider_evidence),
            "row": dict(observation["row"]),
            "rejection_reason": reason,
        })
    return rejected


def _first_only_absence_record(
    observation: dict[str, Any], *, command_snapshot: dict[str, Any],
    other_native_snapshot: dict[str, Any], query: dict[str, Any],
) -> dict[str, Any]:
    row = observation["row"]
    native_evidence = None
    origin_snapshot = next(
        item for item in query["snapshots"] if item["name"] == observation["origin_snapshot"]
    )
    coverage = origin_snapshot.get("coverage")
    if type(coverage) is dict and type(coverage.get("provider_evidence")) is dict:
        native_evidence = coverage["provider_evidence"]
    pid = observation["pid"]
    return {
        "pid": pid,
        "row": {
            "status": "unresolved_historical_intrasnapshot_disappearance",
            "origin_snapshot": observation["origin_snapshot"],
            "provider_identity": observation["provider_identity"],
            "provider_evidence": dict(native_evidence or {}),
            "source_row": dict(row),
            "absence_evidence": {
                "first_table_present": True,
                "same_observation_second_table_absent": (
                    row.get("revalidation_witness") == "first-table-only-unverified"
                    and row.get("native_snapshot_origin") == "first-table-only"
                ),
                "command_snapshot_absent_by_pid": not any(
                    candidate.get("pid") == pid for candidate in command_snapshot["rows"]
                ),
                "other_native_observation_absent_by_pid": not any(
                    candidate.get("pid") == pid for candidate in other_native_snapshot["rows"]
                ),
                "final_current_kernel_table_absent": (
                    observation["origin_snapshot"] == "native-after"
                    or (other_native_snapshot["name"] == "native-after" and
                        not any(candidate.get("pid") == pid
                                for candidate in other_native_snapshot["rows"]))
                ),
                "continuous_absence_claim": False,
                "os_global_absence_claim": False,
            },
            "historical_ownership": "unknown",
            "historical_foreignness": "unknown",
            "workload_relevance": "unknown",
            "exact_exit_time": "unknown",
            "current_map_eligible": False,
            "argv_bridge_allowed": False,
        },
    }


def _render_native_ambiguous_row(row: dict[str, Any]) -> str:
    name = row.get("command_name") or os.path.basename(row.get("command_executable", ""))
    if not isinstance(name, str) or not name:
        raise ReconciliationError("fresh command name is missing")
    # A missing CPU field remains explicitly unknown. The frozen classifier
    # treats an unparsable CPU as ambiguous, which is fail-closed without
    # fabricating a measured percentage or argv.
    return f"{row['pid']} ? {name} /{name}"


def _ucomm_rendered_field_matches(native_row: dict[str, Any], ps_row: dict[str, Any]) -> bool:
    command = native_row.get("command")
    rendered = ps_row.get("ucomm_raw_field")
    if not isinstance(command, str) or not isinstance(rendered, str):
        return False
    try:
        native_bytes = command.encode("utf-8", "strict")
        rendered_bytes = rendered.encode("utf-8", "strict")
    except UnicodeEncodeError:
        return False
    if not native_bytes or len(native_bytes) > 64 or len(rendered_bytes) != 64:
        return False
    # Preserve every native byte. Padding equivalence can collide when the
    # native name itself ends in ASCII space; callers keep that case fail-closed.
    return rendered_bytes == native_bytes + b" " * (64 - len(native_bytes))


def _native_fallback_display_is_stable(before: dict[str, Any], after: dict[str, Any],
                                       row: dict[str, Any]) -> tuple[bool, bool]:
    values = []
    for candidate in (before, after, row):
        current = []
        for field in ("command", "command_name", "command_source"):
            value = candidate.get(field)
            if not isinstance(value, str):
                return False, False
            try:
                current.append(value.encode("utf-8", "strict"))
            except UnicodeEncodeError:
                return False, False
        values.append(tuple(current))
    return values[0] == values[1] == values[2], values[0][0].endswith(b" ")


def evaluate_reconciliation(query: dict[str, Any], candidates: list[dict[str, Any]], *,
                            deadline: float, executor: Any, controller: Any,
                            proc: Any, tracked: dict[int, str]) -> dict[str, Any]:
    """Classify the one pass without promoting historical evidence to identity."""
    result: dict[str, Any] = {
        "schema": "v092-monitor06-reconciliation-evaluation/v1",
        "status": "incomplete-fail-closed",
        "complete": False,
        "candidate_outcomes": [],
        "fresh_contenders": [],
        "historical_only_intrasnapshot_rows": [],
        "rejected_intrasnapshot_observations": [],
        "tracked_after": dict(tracked),
        "automatic_retry": False,
        "cleanup_authorized": False,
        "historical_ownership": "unknown",
        "historical_foreignness": "unknown",
        "continuous_absence_claim": False,
        "os_global_absence_claim": False,
    }
    try:
        validate_query_result(query, deadline=deadline)
    except BaseException as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        result["query"] = query
        result["candidate_outcomes"] = [
            {"pid": item["pid"], "status": "reconciliation_incomplete_fail_closed",
             "historical_ownership": "unknown", "error": result["error"]}
            for item in candidates
        ]
        return result

    snapshots = query["snapshots"]
    first_only_observations = _first_only_observations(snapshots)
    candidate_pids = {item["pid"] for item in candidates}
    for item in candidates:
        pid = item["pid"]
        appearances = [snapshot["name"] for snapshot in snapshots
                       if any(row["pid"] == pid for row in snapshot["rows"])]
        if appearances:
            result["candidate_outcomes"].append({
                "pid": pid,
                "status": "candidate_present_in_fresh_snapshot_fail_closed",
                "present_in": appearances,
                "historical_ownership": "unknown",
                "native_birth_identity_absent_or_unknown_originally": True,
            })
        else:
            result["candidate_outcomes"].append({
                "pid": pid,
                "status": "unresolved_historical_absent_at_reconciliation",
                "present_in": [],
                "historical_ownership": "unknown",
                "historical_foreignness": "unknown",
                "exact_exit_time": "unknown",
            })

    if any(item["status"] != "unresolved_historical_absent_at_reconciliation"
           for item in result["candidate_outcomes"]):
        result["status"] = "candidate-present-fail-closed"
        result["complete"] = True
        result["rejected_intrasnapshot_observations"] = _rejected_first_only_observations(
            first_only_observations, snapshots, "original-candidate-present-in-fresh-snapshot"
        )
        result["query"] = query
        return result

    # ABI4 first-table-only rows describe unresolved historical observations.
    # Reject ambiguous or intersecting rows before descendants() can update the
    # ownership map. PID intersections deliberately ignore birth identity.
    if len(first_only_observations) > 1:
        result["status"] = "intrasnapshot-first-only-over-limit-fail-closed"
        result["complete"] = True
        result["rejected_intrasnapshot_observations"] = _rejected_first_only_observations(
            first_only_observations, snapshots, "more-than-one-first-table-only-row"
        )
        result["query"] = query
        return result
    if first_only_observations:
        observation = first_only_observations[0]
        pid = observation["pid"]
        if pid in candidate_pids:
            # Normally covered by the candidate-presence path above. Keep a
            # local guard in case a future candidate projection changes.
            reason = "first-table-only-pid-is-an-original-candidate"
        elif pid in tracked:
            reason = "first-table-only-pid-intersects-pretracked-map"
        else:
            other_native_snapshot = snapshots[2] if observation["origin_snapshot"] == "native-before" else snapshots[0]
            command_snapshot = snapshots[1]
            command_present = any(row["pid"] == pid for row in command_snapshot["rows"])
            other_native_present = any(row["pid"] == pid for row in other_native_snapshot["rows"])
            if command_present or other_native_present:
                reason = "first-table-only-pid-present-in-command-or-other-native-snapshot"
            else:
                reason = None
        if reason is not None:
            status = (
                "intrasnapshot-first-only-candidate-pid-fail-closed"
                if reason == "first-table-only-pid-is-an-original-candidate"
                else "intrasnapshot-first-only-tracked-pid-fail-closed"
                if reason == "first-table-only-pid-intersects-pretracked-map"
                else "intrasnapshot-first-only-cross-snapshot-presence-fail-closed"
            )
            result["status"] = status
            result["complete"] = True
            result["rejected_intrasnapshot_observations"] = _rejected_first_only_observations(
                first_only_observations, snapshots, reason
            )
            result["query"] = query
            return result

    # The last fresh native table may extend ownership only through the
    # existing exact-birth descendant algorithm. The unresolved candidates
    # themselves are never admitted to this map by their old command rows.
    native_after = _native_map(snapshots[2])
    native_before = _native_map(snapshots[0])
    native_before_rows = {row["pid"]: row for row in _current_native_rows(snapshots[0])}
    native_after_rows = {row["pid"]: row for row in _current_native_rows(snapshots[2])}
    tracked_after = proc.descendants(native_after, tracked)
    result["tracked_after"] = dict(tracked_after)

    command_snapshot = snapshots[1]
    command_rows = {row["pid"]: row for row in command_snapshot["rows"]}
    classifier_table = (
        command_snapshot["classifier_table"]
        if command_snapshot["provider_identity"] == PS_V2_IDENTITY
        else command_snapshot["table"]
    )
    classified_command = list(dict.fromkeys(
        executor._contenders(classifier_table) +
        controller._hashed_bifrost_contenders(classifier_table)
    ))
    for line in classified_command:
        fields = line.split(None, 1)
        pid = int(fields[0]) if fields and fields[0].isdigit() else None
        if pid is not None and pid in tracked_after and pid in native_after and native_after[pid][1] == tracked_after[pid]:
            continue
        result["fresh_contenders"].append({"row": line, "pid": pid,
                                           "status": "actual-command-provider-contender",
                                           "provider_identity": command_snapshot["provider_identity"]})

    native_contenders = []
    kernel_comm_unbridged: dict[int, dict[str, Any]] = {}
    ucomm_padding_ambiguous: dict[int, dict[str, Any]] = {}
    ucomm_native_classified: set[int] = set()
    for snapshot, native_table in ((snapshots[0], native_before), (snapshots[2], native_after)):
        for row in _current_native_rows(snapshot):
            pid = row["pid"]
            if (pid in tracked_after and pid in native_after and
                    row.get("birth_identity") == tracked_after[pid] and
                    native_after[pid][1] == tracked_after[pid]):
                continue
            command_row = command_rows.get(pid)
            before_row = native_before.get(pid)
            after_row = native_after.get(pid)
            identity_is_bracketed = (
                command_row is not None and before_row is not None and after_row is not None and
                before_row[0] == after_row[0] == row["ppid"] and
                before_row[1] == after_row[1] == row["birth_identity"]
            )
            argv_basename_bridge = (
                identity_is_bracketed and command_row is not None and
                Path(command_row["command_executable"]).name == row["command_name"]
            )
            ucomm_bridge = False
            padding_ambiguous = False
            if (identity_is_bracketed and command_row is not None and
                    command_snapshot["provider_identity"] == PS_V2_IDENTITY and
                    _is_kernel_comm_fallback(row)):
                before_display = native_before_rows.get(pid)
                after_display = native_after_rows.get(pid)
                if before_display is not None and after_display is not None:
                    display_is_stable, padding_ambiguous = _native_fallback_display_is_stable(
                        before_display, after_display, row
                    )
                    ucomm_bridge = (
                        display_is_stable and
                        _ucomm_rendered_field_matches(row, command_row)
                    )
            ucomm_only_bridge = ucomm_bridge and not argv_basename_bridge
            bridged_identity_is_stable = argv_basename_bridge or ucomm_bridge
            if bridged_identity_is_stable:
                # The exact PID/native birth/parent tuple brackets the actual
                # ps command row. An argv basename remains the original fast
                # path; ucomm only proves consistency with its fixed rendering.
                if ucomm_only_bridge and pid not in ucomm_native_classified:
                    ambiguous_line = _render_native_ambiguous_row(row)
                    native_classified = list(dict.fromkeys(
                        executor._contenders(ambiguous_line) +
                        controller._hashed_bifrost_contenders(ambiguous_line)
                    ))
                    for line in native_classified:
                        native_contenders.append({
                            "row": line,
                            "pid": pid,
                            "status": "ucomm-bridged-native-command-contender",
                            "provider_identity": snapshot["provider_identity"],
                            "cpu_percent": "unavailable-in-native-provider",
                            "command_arguments_available": False,
                        })
                    ucomm_native_classified.add(pid)
                if ucomm_only_bridge and padding_ambiguous:
                    contender = ucomm_padding_ambiguous.setdefault(pid, {
                        "row": _render_native_ambiguous_row(row),
                        "pid": pid,
                        "status": "kernel-comm-ucomm-padding-ambiguous-fail-closed",
                        "provider_identity": snapshot["provider_identity"],
                        "command_source": row.get("command_source"),
                        "present_in": [],
                        "command_arguments_available": False,
                    })
                    if snapshot["name"] not in contender["present_in"]:
                        contender["present_in"].append(snapshot["name"])
                continue
            if _is_kernel_comm_fallback(row):
                contender = kernel_comm_unbridged.get(pid)
                if contender is None:
                    contender = {
                        "row": _render_native_ambiguous_row(row),
                        "pid": pid,
                        "status": "kernel-comm-fallback-unbridged-fail-closed",
                        "provider_identity": snapshot["provider_identity"],
                        "command_source": row.get("command_source"),
                        "command_path_status": row.get("command_path_status", "legacy-short-comm-fallback"),
                        "command_path_errno": row.get("command_path_errno"),
                        "present_in": [],
                        "command_arguments_available": False,
                    }
                    kernel_comm_unbridged[pid] = contender
                if snapshot["name"] not in contender["present_in"]:
                    contender["present_in"].append(snapshot["name"])
                continue
            ambiguous_line = _render_native_ambiguous_row(row)
            native_classified = list(dict.fromkeys(
                executor._contenders(ambiguous_line) +
                controller._hashed_bifrost_contenders(ambiguous_line)
            ))
            for line in native_classified:
                native_contenders.append({
                    "row": line,
                    "pid": pid,
                    "status": "native-only-or-unbridged-command-identity-ambiguous",
                    "provider_identity": snapshot["provider_identity"],
                    "cpu_percent": "unavailable-in-native-provider",
                    "command_arguments_available": False,
                })
    result["fresh_contenders"].extend(
        kernel_comm_unbridged[pid] for pid in sorted(kernel_comm_unbridged)
    )
    result["fresh_contenders"].extend(
        ucomm_padding_ambiguous[pid] for pid in sorted(ucomm_padding_ambiguous)
    )
    result["fresh_contenders"].extend(native_contenders)
    result["complete"] = True
    result["query"] = query
    if result["fresh_contenders"]:
        result["status"] = "fresh-contender-fail-closed"
        if first_only_observations:
            result["rejected_intrasnapshot_observations"] = _rejected_first_only_observations(
                first_only_observations, snapshots, "fresh-contender-also-present"
            )
    elif first_only_observations:
        observation = first_only_observations[0]
        other_native_snapshot = snapshots[2] if observation["origin_snapshot"] == "native-before" else snapshots[0]
        result["historical_only_intrasnapshot_rows"] = [
            _first_only_absence_record(
                observation, command_snapshot=snapshots[1],
                other_native_snapshot=other_native_snapshot, query=query,
            )
        ]
        result["status"] = "historical-absence-with-unresolved-intrasnapshot-observations"
    else:
        result["status"] = "historical-absence-observed-no-fresh-contender"
    return result
