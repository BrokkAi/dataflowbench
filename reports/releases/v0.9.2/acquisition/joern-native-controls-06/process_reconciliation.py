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
import selectors
import subprocess
import sys
import time
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
                    env: dict[str, str] | None = None) -> dict[str, Any]:
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
    result: dict[str, Any]
    try:
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
    result.setdefault("os_global_completeness_claim", False)
    result.setdefault("continuous_absence_claim", False)
    return result


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
                provider_child.get("provider_identity") != "ps-axo-pid-percentcpu-comm-args/v1" or
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
            if snapshot["provider_identity"] != "ps-axo-pid-percentcpu-comm-args/v1":
                raise ReconciliationError("fresh command snapshot did not use the bounded ps provider")
            _validate_rows(snapshot, native=False)
            if not isinstance(snapshot.get("table"), str):
                raise ReconciliationError("command provider table text is missing")
            if snapshot["table"].splitlines() != [row["raw_row"] for row in snapshot["rows"]]:
                raise ReconciliationError("raw command table differs from structured provider rows")
            if coverage.get("kernel_pid0_rows_observed") != sum(row["pid"] == 0 for row in snapshot["rows"]):
                raise ReconciliationError("command provider PID zero accounting differs from rows")
            provider_child = coverage.get("provider_child")
            if (type(provider_child) is not dict or provider_child.get("pid") != provider_children[0]["pid"] or
                    provider_child.get("reaped") is not True or provider_child.get("cleanup_incomplete") is not False or
                    provider_child.get("returncode") != 0 or provider_child.get("kill_requested") is not False or
                    provider_child.get("provider_identity") != "ps-axo-pid-percentcpu-comm-args/v1" or
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
            if index == 0:
                native_provider_identity = snapshot["provider_identity"]
            elif snapshot["provider_identity"] != native_provider_identity:
                raise ReconciliationError("native provider identity changed across the ordered pass")
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
            for row in snapshot["rows"]}


def _render_native_ambiguous_row(row: dict[str, Any]) -> str:
    name = row.get("command_name") or os.path.basename(row.get("command_executable", ""))
    if not isinstance(name, str) or not name:
        raise ReconciliationError("fresh command name is missing")
    # A missing CPU field remains explicitly unknown. The frozen classifier
    # treats an unparsable CPU as ambiguous, which is fail-closed without
    # fabricating a measured percentage or argv.
    return f"{row['pid']} ? {name} /{name}"


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
        result["query"] = query
        return result

    # The last fresh native table may extend ownership only through the
    # existing exact-birth descendant algorithm. The unresolved candidates
    # themselves are never admitted to this map by their old command rows.
    native_after = _native_map(snapshots[2])
    native_before = _native_map(snapshots[0])
    tracked_after = proc.descendants(native_after, tracked)
    result["tracked_after"] = dict(tracked_after)

    command_snapshot = snapshots[1]
    command_rows = {row["pid"]: row for row in command_snapshot["rows"]}
    classified_command = list(dict.fromkeys(
        executor._contenders(command_snapshot["table"]) +
        controller._hashed_bifrost_contenders(command_snapshot["table"])
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
    for snapshot, native_table in ((snapshots[0], native_before), (snapshots[2], native_after)):
        for row in snapshot["rows"]:
            pid = row["pid"]
            if pid in tracked_after and pid in native_after and native_after[pid][1] == tracked_after[pid]:
                continue
            command_row = command_rows.get(pid)
            before_row = native_before.get(pid)
            after_row = native_after.get(pid)
            bridged_identity_is_stable = (
                command_row is not None and before_row is not None and after_row is not None and
                before_row[0] == after_row[0] == row["ppid"] and
                before_row[1] == after_row[1] == row["birth_identity"] and
                Path(command_row["command_executable"]).name == row["command_name"]
            )
            if bridged_identity_is_stable:
                # The exact PID/native birth/parent tuple brackets the actual
                # ps command row, whose CPU and argv were classified above.
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
    result["fresh_contenders"].extend(native_contenders)
    result["complete"] = True
    result["query"] = query
    result["status"] = "historical-absence-observed-no-fresh-contender" if not result["fresh_contenders"] else "fresh-contender-fail-closed"
    return result
