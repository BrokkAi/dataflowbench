#!/usr/bin/env python3
"""Isolated, read-only process snapshot query used by monitor06.

This child collects exactly native -> command -> native. It uses only OS-native
PID enumeration providers around one bounded owned ``ps`` command-table child.
It never invokes an analyzer or cleanup operation. Provider completeness is
deliberately scoped to the observations returned by the selected local APIs.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import time
import unicodedata
import types
from typing import Any

MAX_PIDS = 8192
MAX_COMMAND_BYTES = 4096
MAX_PS_TABLE_BYTES = 8 * 1024 * 1024
MAX_PS_ROW_BYTES = 64 * 1024
MAX_PS_ARGS_BYTES = 64 * 1024
MAX_PS_STDERR_BYTES = 4096
MAX_PS_CLEANUP_RESERVE_SECONDS = 0.05
QUERY_PROVIDER_IDENTITY = "monitor06-native-command-native/v1"
PS_V1_IDENTITY = "ps-axo-pid-percentcpu-comm-args/v1"
PS_V2_IDENTITY = "ps-axo-pid-pcpu-ucomm-args/v2"
PS_V2_FIELD_WIDTH = 64
PS_V2_HEADERS = tuple(
    value.ljust(PS_V2_FIELD_WIDTH, "_")
    for value in ("DFB_PID_V2", "DFB_PCPU_V2", "DFB_UCOMM_V2", "DFB_ARGS_V2")
)
PS_V2_HEADER_BYTES = b" ".join(value.encode("ascii") for value in PS_V2_HEADERS)
PS_V2_FORMAT = ",".join(
    field + "=" + header
    for field, header in zip(("pid", "pcpu", "ucomm", "args"), PS_V2_HEADERS)
)
PS_V2_CLASSIFIER_MARKER = "__DFB_PS_COMM__"


class SnapshotFailure(RuntimeError):
    def __init__(self, message: str, *, partial: dict[str, Any] | None = None,
                 diagnostic: dict[str, Any] | None = None):
        super().__init__(message)
        self.partial = partial
        self.diagnostic = diagnostic


def _stat_fingerprint(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _pinned_regular_file_lstat(path: Path, *, artifact: str, stage: str) -> os.stat_result:
    if not path.is_absolute():
        raise SnapshotFailure("Darwin provider " + artifact + " path must be absolute")
    current = Path(path.anchor)
    parts = path.parts[1:]
    final_stat = None
    for index, part in enumerate(parts):
        current = current / part
        try:
            observed = current.lstat()
        except OSError as error:
            raise SnapshotFailure(
                "Darwin provider " + artifact + " path component cannot be inspected",
                diagnostic={"stage": stage, "errno": error.errno, "component": os.fspath(current)},
            ) from error
        if stat.S_ISLNK(observed.st_mode):
            raise SnapshotFailure(
                "Darwin provider " + artifact + " path contains a symlink component",
                diagnostic={"stage": stage, "component": os.fspath(current)},
            )
        is_final = index == len(parts) - 1
        if is_final:
            if not stat.S_ISREG(observed.st_mode):
                raise SnapshotFailure(
                    "Darwin provider " + artifact + " path must end in a regular file",
                    diagnostic={"stage": stage, "component": os.fspath(current)},
                )
            final_stat = observed
        elif not stat.S_ISDIR(observed.st_mode):
            raise SnapshotFailure(
                    "Darwin provider " + artifact + " parent component is not a directory",
                diagnostic={"stage": stage, "component": os.fspath(current)},
            )
    if final_stat is None:
        raise SnapshotFailure("Darwin provider " + artifact + " path is not a file")
    return final_stat


def _read_pinned_source(source_path: str | os.PathLike[str], expected_sha256: str) -> tuple[bytes, str]:
    path = Path(source_path)
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
        character not in "0123456789abcdefABCDEF" for character in expected_sha256
    ):
        raise SnapshotFailure("Darwin provider module requires an explicit SHA-256 source pin")
    try:
        link_stat = _pinned_regular_file_lstat(
            path, artifact="module source", stage="module-source-open"
        )
        with path.open("rb") as source_file:
            opened_stat = os.fstat(source_file.fileno())
            if _stat_fingerprint(opened_stat) != _stat_fingerprint(link_stat):
                raise SnapshotFailure("Darwin provider module changed while opening")
            digest = hashlib.sha256()
            source = bytearray()
            while True:
                block = source_file.read(min(64 * 1024, 1024 * 1024 + 1 - len(source)))
                if not block:
                    break
                source.extend(block)
                digest.update(block)
                if len(source) > 1024 * 1024:
                    raise SnapshotFailure("Darwin provider module exceeds its source-size bound")
            closed_stat = os.fstat(source_file.fileno())
        final_stat = _pinned_regular_file_lstat(
            path, artifact="module source", stage="module-source-after-read"
        )
    except SnapshotFailure:
        raise
    except OSError as error:
        raise SnapshotFailure(
            "Darwin provider module cannot be inspected",
            diagnostic={"stage": "module-source-pin", "errno": error.errno},
        ) from error
    actual_sha256 = digest.hexdigest()
    if (
        actual_sha256.lower() != expected_sha256.lower()
        or _stat_fingerprint(closed_stat) != _stat_fingerprint(final_stat)
        or _stat_fingerprint(closed_stat) != _stat_fingerprint(link_stat)
    ):
        raise SnapshotFailure(
            "Darwin provider module source pin mismatch or file race",
            diagnostic={
                "stage": "module-source-pin",
                "expected_sha256": expected_sha256.lower(),
                "actual_sha256": actual_sha256,
            },
        )
    return bytes(source), actual_sha256


def _libproc_failure(api: str, message: str, *, pid: int | None,
                     returned_count: int, expected_size: int,
                     ctypes_errno: int, **extra: Any) -> SnapshotFailure:
    diagnostic = {
        "provider": "darwin-libproc",
        "api": api,
        "pid": pid,
        "returned_count": returned_count,
        "expected_size": expected_size,
        "ctypes_errno": ctypes_errno,
    }
    diagnostic.update(extra)
    return SnapshotFailure(message, diagnostic=diagnostic)


def _error_value(error: BaseException) -> dict[str, Any]:
    value: dict[str, Any] = {"type": type(error).__name__, "message": str(error)}
    diagnostic = getattr(error, "diagnostic", None)
    if type(diagnostic) is dict:
        value["diagnostic"] = diagnostic
    return value


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def deadline_check(deadline: float, where: str) -> None:
    if time.monotonic() >= deadline:
        raise SnapshotFailure("absolute reconciliation deadline exceeded during " + where)


def _safe_text(value: bytes, field: str) -> str:
    try:
        text = value.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise SnapshotFailure(field + " is not valid UTF-8") from error
    if not text or "\x00" in text:
        raise SnapshotFailure(field + " is missing or malformed")
    if len(value) > MAX_COMMAND_BYTES:
        raise SnapshotFailure(field + " exceeds provider field bound")
    return text


class DarwinProvider:
    identity = "darwin-libproc-proc_listallpids-proc_pidinfo-proc_pidpath/v1"

    class BsdInfo(ctypes.Structure):
        # Layout used by the existing invocation-owned Darwin birth reader.
        _fields_ = [
            ("header", ctypes.c_uint32 * 12),
            ("comm", ctypes.c_char * 16),
            ("name", ctypes.c_char * 32),
            ("tail", ctypes.c_uint32 * 6),
            ("seconds", ctypes.c_uint64),
            ("microseconds", ctypes.c_uint64),
        ]

    def __init__(self, deadline: float):
        self.deadline = deadline
        try:
            self.libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
            self.libproc.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
            self.libproc.proc_listallpids.restype = ctypes.c_int
            self.libproc.proc_pidinfo.argtypes = [
                ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                ctypes.c_void_p, ctypes.c_int,
            ]
            self.libproc.proc_pidinfo.restype = ctypes.c_int
            self.libproc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
            self.libproc.proc_pidpath.restype = ctypes.c_int
        except (OSError, AttributeError) as error:
            raise SnapshotFailure("Darwin libproc provider unavailable") from error

    def _pids(self) -> tuple[list[int], dict[str, Any]]:
        capacity = 1024
        last_count = -1
        last_errno = 0
        last_size = 0
        while capacity <= MAX_PIDS:
            deadline_check(self.deadline, "Darwin PID enumeration")
            buffer = (ctypes.c_int * capacity)()
            ctypes.set_errno(0)
            count = self.libproc.proc_listallpids(buffer, ctypes.sizeof(buffer))
            call_errno = ctypes.get_errno()
            last_count, last_errno, last_size = count, call_errno, ctypes.sizeof(buffer)
            if count < 0 or call_errno != 0:
                raise _libproc_failure(
                    "proc_listallpids", "proc_listallpids reported provider error",
                    pid=None, returned_count=count, expected_size=last_size,
                    ctypes_errno=call_errno,
                )
            if count < capacity:
                pids = list(buffer[:count])
                if len(pids) != count or any(type(pid) is not int or pid < 0 for pid in pids):
                    raise SnapshotFailure("proc_listallpids returned malformed PID data")
                return pids, {
                    "enumeration": "proc_listallpids",
                    "enumerated_pid_count": count,
                    "pid_capacity": capacity,
                    "truncated": False,
                    "coverage_errors": [],
                    "excluded_pid0_kernel_entries": sum(pid == 0 for pid in pids),
                }
            capacity *= 2
        raise _libproc_failure(
            "proc_listallpids", "proc_listallpids remained at capacity; enumeration truncation suspected",
            pid=None, returned_count=last_count, expected_size=last_size,
            ctypes_errno=last_errno, capacity=capacity // 2,
        )

    def _row(self, pid: int, *, command: bool) -> dict[str, Any]:
        deadline_check(self.deadline, "Darwin process row")
        info = self.BsdInfo()
        expected_size = ctypes.sizeof(info)
        ctypes.set_errno(0)
        count = self.libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        call_errno = ctypes.get_errno()
        if count != expected_size or call_errno != 0:
            raise _libproc_failure(
                "proc_pidinfo", "proc_pidinfo did not return a complete BSD identity for PID " + str(pid),
                pid=pid, returned_count=count, expected_size=expected_size,
                ctypes_errno=call_errno,
            )
        if int(info.header[3]) != pid:
            raise _libproc_failure(
                "proc_pidinfo", "proc_pidinfo returned a different PID",
                pid=pid, returned_count=count, expected_size=expected_size,
                ctypes_errno=call_errno, observed_pid=int(info.header[3]),
            )
        ppid = int(info.header[4])
        seconds, micros = int(info.seconds), int(info.microseconds)
        if ppid < 0 or seconds <= 0 or not 0 <= micros < 1000000:
            raise _libproc_failure(
                "proc_pidinfo", "Darwin PID/PPID/birth fields are missing for PID " + str(pid),
                pid=pid, returned_count=count, expected_size=expected_size,
                ctypes_errno=call_errno, observed_ppid=ppid,
                observed_birth_seconds=seconds, observed_birth_microseconds=micros,
            )
        birth = f"{seconds}:{micros}"
        status = int(info.header[1])
        state = "Z" if status == 5 else "R" if status == 1 else "T" if status == 4 else "S"
        row: dict[str, Any] = {
            "pid": pid,
            "ppid": ppid,
            "birth_identity": birth,
            "state": state,
        }
        if command:
            path_buffer = ctypes.create_string_buffer(MAX_COMMAND_BYTES + 1)
            ctypes.set_errno(0)
            path_size = self.libproc.proc_pidpath(pid, path_buffer, MAX_COMMAND_BYTES)
            path_errno = ctypes.get_errno()
            if path_size < 0 or path_size > MAX_COMMAND_BYTES or path_errno != 0:
                raise _libproc_failure(
                    "proc_pidpath", "proc_pidpath failed or exceeded bound for PID " + str(pid),
                    pid=pid, returned_count=path_size, expected_size=MAX_COMMAND_BYTES,
                    ctypes_errno=path_errno, buffer_size=ctypes.sizeof(path_buffer),
                )
            path_bytes = bytes(path_buffer.raw[:path_size]).split(b"\x00", 1)[0]
            comm_bytes = bytes(info.comm).split(b"\x00", 1)[0]
            command_text = _safe_text(path_bytes or comm_bytes, "Darwin executable command")
            row["command"] = command_text
            row["command_executable"] = command_text
            row["command_name"] = os.path.basename(command_text)
            row["command_source"] = "proc_pidpath" if path_bytes else "proc_pidinfo.pbi_comm"
            row["command_arguments_available"] = False
            after = self.BsdInfo()
            after_expected_size = ctypes.sizeof(after)
            ctypes.set_errno(0)
            after_count = self.libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(after), ctypes.sizeof(after))
            after_errno = ctypes.get_errno()
            identity_changed = False
            observed_identity: dict[str, int] = {}
            if after_count == after_expected_size and after_errno == 0:
                observed_identity = {
                    "observed_pid": int(after.header[3]),
                    "observed_ppid": int(after.header[4]),
                    "observed_birth_seconds": int(after.seconds),
                    "observed_birth_microseconds": int(after.microseconds),
                }
                identity_changed = (
                    observed_identity["observed_pid"] != pid or
                    observed_identity["observed_ppid"] != ppid or
                    observed_identity["observed_birth_seconds"] != seconds or
                    observed_identity["observed_birth_microseconds"] != micros
                )
            if after_count != after_expected_size or after_errno != 0 or identity_changed:
                raise _libproc_failure(
                    "proc_pidinfo", "Darwin PID identity changed while reading command for PID " + str(pid),
                    pid=pid, returned_count=after_count, expected_size=after_expected_size,
                    ctypes_errno=after_errno, **observed_identity,
                )
        return row

    def native_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        pids, coverage = self._pids()
        rows = []
        try:
            for pid in pids:
                deadline_check(self.deadline, "Darwin native table")
                if pid == 0:
                    continue
                rows.append(self._row(pid, command=True))
        except BaseException as error:
            coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "ppid", "birth_identity", "state", "command"],
                             "coverage_errors": [_error_value(error)]})
            error.partial = {"rows": rows, "coverage": coverage, "truncated": False}
            raise
        if any(row["pid"] <= 0 or row.get("ppid") is None or
               not row.get("birth_identity") or not row.get("command") for row in rows):
            raise SnapshotFailure("Darwin native table contains a missing required field")
        coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "ppid", "birth_identity", "state", "command"]})
        return rows, coverage

    def command_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        pids, coverage = self._pids()
        rows = []
        try:
            for pid in pids:
                deadline_check(self.deadline, "Darwin command table")
                if pid == 0:
                    continue
                row = self._row(pid, command=True)
                rows.append({"pid": pid, "command": row["command"], "command_executable": row["command_executable"],
                             "command_name": row["command_name"],
                             "command_source": row["command_source"], "command_arguments_available": False})
        except BaseException as error:
            coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "command"],
                             "coverage_errors": [_error_value(error)]})
            error.partial = {"rows": rows, "coverage": coverage, "truncated": False}
            raise
        coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "command"]})
        return rows, coverage


class PinnedDarwinNativeProvider:
    """Load the ABI-v3 provider only from explicit source and dylib pins."""

    identity = "darwin-sysctl-kern-proc-all-libproc/v3"

    def __init__(
        self,
        deadline: float,
        *,
        module_path: str | os.PathLike[str] | None,
        module_sha256: str | None,
        dylib_path: str | os.PathLike[str] | None,
        dylib_sha256: str | None,
    ):
        self.deadline = deadline
        if None in (module_path, module_sha256, dylib_path, dylib_sha256):
            raise SnapshotFailure(
                "Darwin native provider requires explicit absolute module/dylib paths and SHA-256 pins"
            )
        module_file = Path(module_path)
        library_file = Path(dylib_path)
        if module_file.suffix != ".py":
            raise SnapshotFailure("Darwin provider module path must name Python source")
        if not library_file.is_absolute():
            raise SnapshotFailure("Darwin provider dylib path must be absolute")
        if not isinstance(dylib_sha256, str) or len(dylib_sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in dylib_sha256
        ):
            raise SnapshotFailure("Darwin provider dylib requires an explicit SHA-256 pin")
        library_stat_before = _pinned_regular_file_lstat(
            library_file, artifact="dylib", stage="dylib-before-provider-load"
        )
        source_bytes, module_digest = _read_pinned_source(module_file, module_sha256)
        module_name = "_dfb_darwin_native_provider_" + module_digest[:16]
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise SnapshotFailure("pinned Darwin provider module cannot be loaded")
        module = types.ModuleType(module_name)
        module.__file__ = os.fspath(module_file)
        module.__loader__ = spec.loader
        module.__package__ = ""
        module.__spec__ = spec
        sys.modules[module_name] = module
        try:
            code = compile(source_bytes, os.fspath(module_file), "exec", dont_inherit=True)
            exec(code, module.__dict__)
        except BaseException as error:
            sys.modules.pop(module_name, None)
            raise SnapshotFailure(
                "pinned Darwin provider module failed during import",
                diagnostic={"stage": "module-import", "type": type(error).__name__},
            ) from error
        provider_type = getattr(module, "DarwinKernProcAllProvider", None)
        if (
            getattr(module, "ABI_VERSION", None) != 3
            or provider_type is None
            or getattr(provider_type, "identity", None) != self.identity
        ):
            raise SnapshotFailure(
                "pinned Darwin provider module has an incompatible ABI or provider identity"
            )
        self.module_source_sha256 = module_digest
        self.module_source_path = os.fspath(module_file)
        self.dylib_path = os.fspath(library_file)
        self.dylib_sha256 = dylib_sha256.lower()
        self._provider = provider_type(
            library_file, dylib_sha256, deadline=deadline
        )
        library_stat_after = _pinned_regular_file_lstat(
            library_file, artifact="dylib", stage="dylib-after-provider-load"
        )
        if _stat_fingerprint(library_stat_before) != _stat_fingerprint(library_stat_after):
            raise SnapshotFailure("Darwin provider dylib path changed during provider load")
        if getattr(self._provider, "identity", None) != self.identity:
            raise SnapshotFailure("loaded Darwin provider identity differs from the pinned module")

    def native_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        deadline_check(self.deadline, "pinned Darwin native provider")
        rows, coverage = self._provider.native_table()
        deadline_check(self.deadline, "pinned Darwin native provider")
        if type(coverage) is not dict or type(coverage.get("provider_evidence")) is not dict:
            raise SnapshotFailure("pinned Darwin provider omitted source/library pin evidence")
        evidence = coverage["provider_evidence"]
        observed_library_sha256 = evidence.get("library_sha256")
        if (not isinstance(observed_library_sha256, str) or
                observed_library_sha256.lower() != self.dylib_sha256):
            raise SnapshotFailure("pinned Darwin provider returned mismatched library SHA-256 evidence")
        evidence.update({
            "module_source_path": self.module_source_path,
            "module_source_sha256": self.module_source_sha256,
            "library_path": self.dylib_path,
        })
        return rows, coverage


class LinuxProvider:
    identity = "linux-procfs-proc-stat-cmdline-comm/v1"

    def __init__(self, deadline: float):
        self.deadline = deadline
        self.proc = Path("/proc")
        if not self.proc.is_dir():
            raise SnapshotFailure("Linux /proc provider unavailable")

    def _pids(self) -> tuple[list[int], dict[str, Any]]:
        deadline_check(self.deadline, "Linux PID enumeration")
        try:
            with os.scandir(self.proc) as entries:
                pids = []
                for entry in entries:
                    if not entry.name.isdecimal():
                        continue
                    pids.append(int(entry.name))
                    if len(pids) > MAX_PIDS:
                        raise SnapshotFailure("Linux /proc PID enumeration exceeds provider bound")
        except OSError as error:
            raise SnapshotFailure("cannot enumerate Linux /proc") from error
        pids.sort()
        if any(pid < 0 for pid in pids):
            raise SnapshotFailure("Linux /proc returned a malformed PID")
        return pids, {
            "enumeration": "os.scandir(/proc)",
            "enumerated_pid_count": len(pids),
            "pid_capacity": MAX_PIDS,
            "truncated": False,
            "coverage_errors": [],
            "excluded_pid0_kernel_entries": sum(pid == 0 for pid in pids),
        }

    def _stat(self, pid: int) -> tuple[int, str, str]:
        deadline_check(self.deadline, "Linux stat row")
        try:
            raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        except (OSError, UnicodeError) as error:
            raise SnapshotFailure("cannot read complete Linux stat for PID " + str(pid)) from error
        close = raw.rfind(")")
        if close < 0:
            raise SnapshotFailure("malformed Linux stat row for PID " + str(pid))
        fields = raw[close + 1:].strip().split()
        # fields start at stat field 3 (state): PPID is field 4, starttime is field 22.
        if len(fields) <= 19 or len(raw) > MAX_COMMAND_BYTES:
            raise SnapshotFailure("Linux stat row lacks PPID or starttime for PID " + str(pid))
        try:
            state = fields[0]
            ppid = int(fields[1])
            birth = fields[19]
            if ppid < 0 or not birth.isdecimal() or int(birth) <= 0:
                raise ValueError("invalid PPID/starttime")
        except (IndexError, ValueError) as error:
            raise SnapshotFailure("Linux PPID/starttime fields malformed for PID " + str(pid)) from error
        return ppid, birth, state

    def _command(self, pid: int) -> tuple[str, str, str]:
        deadline_check(self.deadline, "Linux command row")
        try:
            raw = Path(f"/proc/{pid}/cmdline").read_bytes()
            source = "procfs-cmdline"
            if not raw:
                raw = Path(f"/proc/{pid}/comm").read_bytes()
                source = "procfs-comm"
        except OSError as error:
            raise SnapshotFailure("cannot read complete Linux command for PID " + str(pid)) from error
        if len(raw) > MAX_COMMAND_BYTES:
            raise SnapshotFailure("Linux command row exceeds provider field bound for PID " + str(pid))
        argv = [part for part in raw.split(b"\x00") if part]
        if not argv:
            raise SnapshotFailure("Linux command fields are missing for PID " + str(pid))
        executable = _safe_text(argv[0], "Linux argv[0]")
        command_line = " ".join(_safe_text(part, "Linux command argument") for part in argv)
        return command_line, source, executable

    def native_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        pids, coverage = self._pids()
        rows = []
        try:
            for pid in pids:
                deadline_check(self.deadline, "Linux native table")
                if pid == 0:
                    continue
                ppid, birth, state = self._stat(pid)
                command, command_source, executable = self._command(pid)
                after_ppid, after_birth, after_state = self._stat(pid)
                if (after_ppid, after_birth, after_state) != (ppid, birth, state):
                    raise SnapshotFailure("Linux PID identity changed while reading command for PID " + str(pid))
                rows.append({"pid": pid, "ppid": ppid, "birth_identity": birth, "state": state,
                             "command": command, "command_executable": executable,
                             "command_name": Path(executable).name,
                             "command_source": command_source,
                             "command_arguments_available": command_source == "procfs-cmdline"})
        except BaseException as error:
            coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "ppid", "birth_identity", "state", "command"],
                             "coverage_errors": [_error_value(error)]})
            error.partial = {"rows": rows, "coverage": coverage, "truncated": False}
            raise
        coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "ppid", "birth_identity", "state", "command"]})
        return rows, coverage

    def command_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        pids, coverage = self._pids()
        rows = []
        try:
            for pid in pids:
                deadline_check(self.deadline, "Linux command table")
                if pid == 0:
                    continue
                command, source, executable = self._command(pid)
                rows.append({"pid": pid, "command": command, "command_executable": executable,
                             "command_name": Path(executable).name,
                             "command_source": source, "command_arguments_available": True})
        except BaseException as error:
            coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "command"],
                             "coverage_errors": [_error_value(error)]})
            error.partial = {"rows": rows, "coverage": coverage, "truncated": False}
            raise
        coverage.update({"returned_pid_count": len(rows), "required_fields": ["pid", "command"]})
        return rows, coverage


class PsCommandProvider:
    """Bounded ps command table using the explicitly selected output format."""

    def __init__(self, deadline: float, *, child_event: Any = None, version: str = "v1"):
        self.deadline = deadline
        self.child_event = child_event
        if version not in {"v1", "v2"}:
            raise ValueError("unsupported ps command-table version")
        self.version = version

    @property
    def identity(self) -> str:
        return PS_V2_IDENTITY if self.version == "v2" else PS_V1_IDENTITY

    @property
    def enumeration(self) -> str:
        return ("/bin/ps -axo " + PS_V2_FORMAT + " -ww"
                if self.version == "v2" else "ps -axo pid=,%cpu=,comm=,args=")

    def _event(self, process: Any, *, kill_requested: bool, reaped: bool,
               returncode: int | None, started: float, started_utc: str,
               error: str | None = None) -> dict[str, Any]:
        value = {
            "kind": "provider-child",
            "provider_identity": self.identity,
            "pid": getattr(process, "pid", None),
            "started_utc": started_utc,
            "ended_utc": utc_now(),
            "started_monotonic": started,
            "ended_monotonic": time.monotonic(),
            "kill_requested": kill_requested,
            "returncode": returncode,
            "reaped": reaped,
            "cleanup_incomplete": not reaped,
            "direct_child_only": True,
            "descendant_containment": "direct-child-reaped" if reaped else "unproven-direct-child-cleanup-incomplete",
        }
        if error is not None:
            value["error"] = error
        if callable(self.child_event):
            self.child_event(value)
        return value

    def _parse(self, stdout: bytes) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
        if len(stdout) > MAX_PS_TABLE_BYTES:
            raise SnapshotFailure("ps command table exceeds 8 MiB provider bound",
                                  partial={"rows": [], "table": "", "truncated": True,
                                  "coverage": {"enumeration": self.enumeration,
                                               "enumerated_pid_count": 0, "returned_pid_count": 0,
                                               "truncated": True, "coverage_errors": ["table-byte-bound"],
                                               "excluded_pid0_kernel_entries": 0,
                                               "observed_table_bytes": len(stdout)}})
        try:
            table = stdout.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise SnapshotFailure("ps command table is not valid UTF-8",
                                  partial={"rows": [], "table": "", "truncated": False,
                                           "coverage": {"enumeration": self.enumeration,
                                               "enumerated_pid_count": 0, "returned_pid_count": 0,
                                               "truncated": False, "coverage_errors": ["invalid-utf8"],
                                               "excluded_pid0_kernel_entries": 0}}) from error
        lines = table.splitlines()
        rows = []
        pid0 = 0
        try:
            if len(lines) > MAX_PIDS:
                raise SnapshotFailure("ps command row count exceeds PID provider bound")
            for line in lines:
                line_bytes = line.encode("utf-8")
                if not line.strip() or len(line_bytes) > MAX_PS_ROW_BYTES:
                    raise SnapshotFailure("ps command row is blank or exceeds 64 KiB row bound")
                fields = line.split(None, 3)
                if len(fields) != 4:
                    raise SnapshotFailure("ps command row lacks pid, CPU, comm, or argv fields")
                try:
                    pid = int(fields[0])
                    cpu = float(fields[1])
                except ValueError as error:
                    raise SnapshotFailure("ps command PID or CPU field is malformed") from error
                if pid < 0 or not math.isfinite(cpu) or cpu < 0 or not fields[2] or not fields[3]:
                    raise SnapshotFailure("ps command row contains an invalid required field")
                if len(fields[3].encode("utf-8")) > MAX_PS_ARGS_BYTES:
                    raise SnapshotFailure("ps command argv exceeds 64 KiB field bound")
                executable = fields[3].split(None, 1)[0]
                name = Path(executable).name
                if not name:
                    raise SnapshotFailure("ps command argv[0] is missing")
                pid0 += pid == 0
                rows.append({
                    "pid": pid,
                    "cpu_percent": cpu,
                    "comm": fields[2],
                    "args": fields[3],
                    "raw_row": line,
                    "command": fields[3],
                    "command_executable": executable,
                    "command_name": name,
                    "command_source": "ps-argv",
                    "command_arguments_available": True,
                    "kernel_pid0": pid == 0,
                })
        except BaseException as error:
            coverage = {"enumeration": self.enumeration,
                        "enumerated_pid_count": len(lines), "returned_pid_count": len(rows),
                        "truncated": False, "coverage_errors": [{"type": type(error).__name__, "message": str(error)}],
                        "excluded_pid0_kernel_entries": 0, "kernel_pid0_rows_observed": pid0,
                        "required_fields": ["pid", "cpu_percent", "comm", "args", "command"]}
            error.partial = {"rows": rows, "table": table, "coverage": coverage, "truncated": False}
            raise
        coverage = {"enumeration": self.enumeration,
                    "enumerated_pid_count": len(lines), "returned_pid_count": len(rows),
                    "truncated": False, "coverage_errors": [],
                    "excluded_pid0_kernel_entries": 0, "kernel_pid0_rows_observed": pid0,
                    "required_fields": ["pid", "cpu_percent", "comm", "args", "command"]}
        return rows, table, coverage

    def _parse_v2(self, stdout: bytes) -> tuple[list[dict[str, Any]], str, str, dict[str, Any]]:
        raw_digest = hashlib.sha256(stdout).hexdigest()
        rows: list[dict[str, Any]] = []
        projection_rows: list[str] = []
        decoded_table = ""
        data_line_count = 0
        pid0 = 0

        def fail(message: str, code: str, *, truncated: bool = False) -> None:
            coverage = {
                "enumeration": self.enumeration,
                "format_identity": "fixed-four-64-byte-columns/v1",
                "raw_stdout_sha256": raw_digest,
                "raw_stdout_bytes": len(stdout),
                "raw_header": PS_V2_HEADER_BYTES.decode("ascii"),
                "enumerated_pid_count": data_line_count,
                "returned_pid_count": len(rows),
                "truncated": truncated,
                "coverage_errors": [code],
                "excluded_pid0_kernel_entries": 0,
                "kernel_pid0_rows_observed": pid0,
                "required_fields": ["pid", "cpu_percent", "cpu_token", "ucomm_raw_field",
                                    "args", "command", "classifier_row"],
            }
            partial = {
                "rows": rows,
                "table": decoded_table,
                "classifier_table": "\n".join(projection_rows) + ("\n" if projection_rows else ""),
                "coverage": coverage,
                "truncated": truncated,
            }
            raise SnapshotFailure(message, partial=partial)

        if len(stdout) > MAX_PS_TABLE_BYTES:
            data_line_count = 0
            fail("ps-v2 command table exceeds 8 MiB provider bound", "table-byte-bound", truncated=True)
        try:
            decoded_table = stdout.decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail("ps-v2 command table is not valid UTF-8", "invalid-utf8")
        if not stdout or not stdout.endswith(b"\n") or b"\r" in stdout:
            fail("ps-v2 command table has malformed line delimiters", "malformed-line-delimiter")
        raw_lines = stdout.split(b"\n")
        if raw_lines[-1] != b"":
            fail("ps-v2 command table has an unterminated final row", "unterminated-final-row")
        lines = raw_lines[:-1]
        if not lines or lines[0] != PS_V2_HEADER_BYTES:
            fail("ps-v2 command table header or fixed layout is unknown", "unknown-header-layout")
        data_lines = lines[1:]
        data_line_count = len(data_lines)
        if data_line_count > MAX_PIDS:
            fail("ps-v2 command row count exceeds PID provider bound", "row-count-bound")

        seen_pids: set[int] = set()
        for index, line in enumerate(data_lines):
            if (not line or len(line) > MAX_PS_ROW_BYTES or len(line) < 195 or
                    line[64:65] != b" " or line[129:130] != b" " or
                    line[194:195] != b" "):
                fail("ps-v2 row has an invalid fixed-column delimiter or 64 KiB size", "malformed-fixed-row")
            pid_field = line[0:64]
            cpu_field = line[65:129]
            ucomm_field = line[130:194]
            args_field = line[195:]

            pid_token_bytes = pid_field.lstrip(b" ")
            cpu_token_bytes = cpu_field.lstrip(b" ")
            if (not pid_token_bytes or not pid_token_bytes.isdigit() or
                    pid_field != pid_token_bytes.rjust(PS_V2_FIELD_WIDTH, b" ") or
                    not cpu_token_bytes or cpu_field != cpu_token_bytes.rjust(PS_V2_FIELD_WIDTH, b" ")):
                fail("ps-v2 PID or CPU fixed field is malformed", "malformed-pid-or-cpu")
            try:
                pid_token = pid_token_bytes.decode("ascii", "strict")
                cpu_token = cpu_token_bytes.decode("ascii", "strict")
            except UnicodeDecodeError:
                fail("ps-v2 PID or CPU field is not ASCII", "non-ascii-pid-or-cpu")
            if not re.fullmatch(r"[0-9]+", pid_token) or not re.fullmatch(
                r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", cpu_token
            ):
                fail("ps-v2 PID or CPU token has an unknown syntax", "unknown-pid-or-cpu-syntax")
            try:
                pid = int(pid_token)
                cpu = float(cpu_token)
            except ValueError:
                fail("ps-v2 PID or CPU token is malformed", "malformed-pid-or-cpu")
            if pid < 0 or not math.isfinite(cpu) or cpu < 0 or pid in seen_pids:
                fail("ps-v2 row contains an invalid or duplicate PID/CPU", "invalid-or-duplicate-row")
            seen_pids.add(pid)

            if (not ucomm_field.strip(b" ") or
                    any(byte < 0x20 or byte == 0x7F for byte in ucomm_field)):
                fail("ps-v2 ucomm field is empty or contains a control byte", "malformed-ucomm-field")
            if not args_field or len(args_field) > MAX_PS_ARGS_BYTES:
                fail("ps-v2 args field is empty or exceeds 64 KiB field bound", "args-field-bound")
            if any(byte < 0x20 or byte == 0x7F for byte in args_field):
                fail("ps-v2 args field contains an unescaped control character", "unescaped-args-control")
            try:
                ucomm_raw_field = ucomm_field.decode("utf-8", "strict")
                args = args_field.decode("utf-8", "strict")
                raw_row = line.decode("utf-8", "strict")
            except UnicodeDecodeError:
                fail("ps-v2 row field is not valid UTF-8", "invalid-row-utf8")
            if any(unicodedata.category(character) == "Cc" for character in ucomm_raw_field):
                fail("ps-v2 ucomm field contains a Unicode control character", "malformed-ucomm-field")
            if not args:
                fail("ps-v2 args field is empty", "empty-args-field")
            argv_fields = args.split(None, 1)
            if not argv_fields:
                fail("ps-v2 args field lacks argv[0]", "missing-argv0")
            argv0 = argv_fields[0]
            name = Path(argv0).name
            if not name:
                fail("ps-v2 argv[0] is missing", "missing-argv0")
            pid0 += pid == 0
            classifier_row = f"{pid_token} {cpu_token} {PS_V2_CLASSIFIER_MARKER} {args}"
            projection_rows.append(classifier_row)
            rows.append({
                "pid": pid,
                "pid_token": pid_token,
                "cpu_percent": cpu,
                "cpu_token": cpu_token,
                "ucomm_raw_field": ucomm_raw_field,
                "args": args,
                "raw_row": raw_row,
                "command": args,
                "command_executable": argv0,
                "command_name": name,
                "classifier_row": classifier_row,
                "command_source": "ps-argv",
                "command_arguments_available": True,
                "kernel_pid0": pid == 0,
            })

        classifier_table = "\n".join(projection_rows) + ("\n" if projection_rows else "")
        coverage = {
            "enumeration": self.enumeration,
            "format_identity": "fixed-four-64-byte-columns/v1",
            "raw_stdout_sha256": raw_digest,
            "raw_stdout_bytes": len(stdout),
            "raw_header": PS_V2_HEADER_BYTES.decode("ascii"),
            "enumerated_pid_count": data_line_count,
            "returned_pid_count": len(rows),
            "truncated": False,
            "coverage_errors": [],
            "excluded_pid0_kernel_entries": 0,
            "kernel_pid0_rows_observed": pid0,
            "required_fields": ["pid", "cpu_percent", "cpu_token", "ucomm_raw_field",
                                "args", "command", "classifier_row"],
        }
        return rows, decoded_table, classifier_table, coverage

    def _parse_selected(self, stdout: bytes) -> tuple[list[dict[str, Any]], str, str | None, dict[str, Any]]:
        if self.version == "v2":
            return self._parse_v2(stdout)
        rows, table, coverage = self._parse(stdout)
        return rows, table, None, coverage

    def command_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        started = time.monotonic()
        started_utc = utc_now()
        child_deadline = self.deadline - MAX_PS_CLEANUP_RESERVE_SECONDS
        if child_deadline <= started:
            raise SnapshotFailure("no bounded time remains to run ps and reap its child")
        process = None
        kill_requested = False
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        overflow = None
        timed_out = False
        selector = selectors.DefaultSelector()

        def register_streams() -> None:
            for label, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
                if stream is None:
                    raise SnapshotFailure("ps provider pipe was not created")
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)

        def drain_until(limit: float, *, stop_on_overflow: bool = False) -> None:
            nonlocal overflow
            while selector.get_map():
                left = limit - time.monotonic()
                if left <= 0:
                    return
                for key, _ in selector.select(left):
                    label = key.data
                    try:
                        chunk = os.read(key.fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        selector.unregister(key.fileobj)
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    cap = MAX_PS_TABLE_BYTES if label == "stdout" else MAX_PS_STDERR_BYTES
                    target = buffers[label]
                    room = max(0, cap + 1 - len(target))
                    if room:
                        target.extend(chunk[:room])
                    if len(target) > cap:
                        overflow = label
                        if stop_on_overflow:
                            return

        def kill_and_reap() -> tuple[int | None, bool]:
            nonlocal kill_requested
            if process is None:
                return None, True
            try:
                process.kill()
                kill_requested = True
            except (OSError, ProcessLookupError):
                pass
            # Keep draining the owned direct child's pipes while reserving no
            # time beyond the absolute query deadline. No descendant signal is
            # sent and failure to reap remains explicit evidence.
            drain_until(self.deadline)
            try:
                left = max(0.0, self.deadline - time.monotonic())
                if left:
                    process.wait(timeout=left)
            except (subprocess.TimeoutExpired, OSError, AttributeError):
                pass
            try:
                returncode = process.poll()
            except (OSError, AttributeError):
                returncode = getattr(process, "returncode", None)
            return returncode, returncode is not None

        try:
            argv = (["/bin/ps", "-axo", PS_V2_FORMAT, "-ww"]
                    if self.version == "v2" else ["ps", "-axo", "pid=,%cpu=,comm=,args="])
            child_env = dict(os.environ)
            if self.version == "v2":
                child_env["LC_ALL"] = "C"
                child_env["LANG"] = "C"
            process = subprocess.Popen(
                argv, cwd="/", env=child_env,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                close_fds=True,
            )
            self._event(process, kill_requested=False, reaped=False, returncode=None,
                        started=started, started_utc=started_utc)
            register_streams()
            drain_until(child_deadline, stop_on_overflow=True)
            if selector.get_map():
                timed_out = time.monotonic() >= child_deadline
            if timed_out or overflow is not None:
                returncode, reaped = kill_and_reap()
                stdout = bytes(buffers["stdout"])
                stderr = bytes(buffers["stderr"])
                child_value = self._event(process, kill_requested=kill_requested, reaped=reaped,
                                          returncode=returncode, started=started,
                                          started_utc=started_utc,
                                          error=("ps command output exceeded provider byte bound" if overflow
                                                 else "ps command provider timed out"))
                error_name = "ps-output-limit" if overflow else "ps-timeout"
                partial = {"rows": [], "table": "", "truncated": overflow == "stdout",
                           "coverage": {"enumeration": self.enumeration,
                                        "enumerated_pid_count": 0, "returned_pid_count": 0,
                                        "truncated": overflow == "stdout", "coverage_errors": [error_name],
                                        "excluded_pid0_kernel_entries": 0,
                                        "observed_stdout_bytes_capped": len(stdout),
                                        "observed_stderr_bytes_capped": len(stderr),
                                        "provider_child": child_value}}
                if not overflow and stdout:
                    try:
                        partial_rows, partial_table, partial_classifier, partial_coverage = self._parse_selected(stdout)
                        partial.update({"rows": partial_rows, "table": partial_table,
                                        "coverage": partial_coverage})
                        if partial_classifier is not None:
                            partial["classifier_table"] = partial_classifier
                        partial["coverage"]["coverage_errors"] = [error_name]
                        partial["coverage"]["provider_child"] = child_value
                    except BaseException as parse_error:
                        parsed = getattr(parse_error, "partial", None)
                        if isinstance(parsed, dict):
                            partial.update(parsed)
                            partial["coverage"]["provider_child"] = child_value
                raise SnapshotFailure("ps command provider output is incomplete", partial=partial)
            returncode = process.wait(timeout=max(0.0, child_deadline - time.monotonic()))
            reaped = returncode is not None
            stdout = bytes(buffers["stdout"])
            stderr = bytes(buffers["stderr"])
        except subprocess.TimeoutExpired:
            returncode, reaped = kill_and_reap()
            child_value = self._event(process, kill_requested=kill_requested, reaped=reaped,
                                      returncode=returncode, started=started,
                                      started_utc=started_utc,
                                      error="ps command provider timed out")
            partial = {"rows": [], "table": "", "truncated": False,
                       "coverage": {"enumeration": self.enumeration,
                                    "enumerated_pid_count": 0, "returned_pid_count": 0,
                                    "truncated": False, "coverage_errors": ["ps-timeout"],
                                    "excluded_pid0_kernel_entries": 0,
                                    "provider_child": child_value}}
            error = SnapshotFailure("ps command provider timed out", partial=partial)
            raise error from None
        except OSError as error:
            if process is None:
                raise SnapshotFailure("cannot start owned ps command provider") from error
            returncode, reaped = kill_and_reap()
            child_value = self._event(process, kill_requested=kill_requested, reaped=reaped,
                                      returncode=returncode, started=started,
                                      started_utc=started_utc,
                                      error="ps command provider I/O failed")
            raise SnapshotFailure("owned ps command provider I/O failed",
                                  partial={"rows": [], "table": "", "truncated": False,
                                           "coverage": {"enumeration": self.enumeration,
                                               "enumerated_pid_count": 0, "returned_pid_count": 0,
                                               "truncated": False, "coverage_errors": ["ps-provider-io-error"],
                                               "excluded_pid0_kernel_entries": 0,
                                               "provider_child": child_value}}) from error
        finally:
            selector.close()
            if process is not None:
                for stream in (getattr(process, "stdout", None), getattr(process, "stderr", None)):
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError:
                            pass
        if process is None:
            raise SnapshotFailure("ps command provider did not start")
        child_value = self._event(process, kill_requested=False, reaped=reaped,
                                  returncode=returncode, started=started, started_utc=started_utc)
        if not reaped:
            raise SnapshotFailure("ps command provider returned without an observed reap")
        if returncode != 0:
            raise SnapshotFailure("ps command provider exited unsuccessfully",
                                  partial={"rows": [], "table": "", "truncated": False,
                                           "coverage": {"enumeration": self.enumeration,
                                               "enumerated_pid_count": 0, "returned_pid_count": 0,
                                               "truncated": False, "coverage_errors": ["ps-nonzero-exit"],
                                               "excluded_pid0_kernel_entries": 0,
                                               "provider_child": child_value,
                                               "stderr": stderr.decode("utf-8", "replace")[:4096]}})
        if stderr:
            raise SnapshotFailure("ps command provider wrote stderr",
                                  partial={"rows": [], "table": "", "truncated": False,
                                           "coverage": {"enumeration": self.enumeration,
                                               "enumerated_pid_count": 0, "returned_pid_count": 0,
                                               "truncated": False, "coverage_errors": ["ps-stderr"],
                                               "excluded_pid0_kernel_entries": 0,
                                               "provider_child": child_value,
                                               "stderr": stderr.decode("utf-8", "replace")[:4096]}})
        rows, table, classifier_table, coverage = self._parse_selected(stdout)
        coverage["provider_child"] = child_value
        values = {"raw_table": table}
        if classifier_table is not None:
            values["classifier_table"] = classifier_table
        return rows, coverage | values


def _snapshot(name: str, provider: Any, function: Any, deadline: float) -> dict[str, Any]:
    value: dict[str, Any] = {
        "name": name,
        "provider_identity": provider.identity,
        "provider_scope": "local provider-scoped snapshot; not OS-global proof",
        "started_utc": utc_now(),
        "started_monotonic": time.monotonic(),
        "complete": False,
        "truncated": False,
        "rows": [],
        "coverage": None,
        "error": None,
    }
    try:
        deadline_check(deadline, name)
        rows, coverage = function()
        value["rows"] = rows
        table = coverage.pop("raw_table", None)
        classifier_table = coverage.pop("classifier_table", None)
        value["coverage"] = coverage
        if name == "command":
            value["table"] = table
            if classifier_table is not None:
                value["classifier_table"] = classifier_table
        value["complete"] = True
    except BaseException as error:
        partial = getattr(error, "partial", None)
        if isinstance(partial, dict):
            value["rows"] = partial.get("rows", [])
            value["coverage"] = partial.get("coverage")
            value["truncated"] = bool(partial.get("truncated", False))
            if "table" in partial:
                value["table"] = partial["table"]
            if "classifier_table" in partial:
                value["classifier_table"] = partial["classifier_table"]
        value["error"] = _error_value(error)
    finally:
        value["ended_monotonic"] = time.monotonic()
        value["ended_utc"] = utc_now()
    if value["complete"] and value["ended_monotonic"] >= deadline:
        value["complete"] = False
        value["error"] = {"type": "DeadlineExceeded", "message": "snapshot ended at or after absolute deadline"}
    return value


def query(deadline: float, *, on_snapshot: Any = None,
          on_provider_child: Any = None,
          darwin_native_module_path: str | os.PathLike[str] | None = None,
          darwin_native_module_sha256: str | None = None,
          darwin_native_dylib_path: str | os.PathLike[str] | None = None,
          darwin_native_dylib_sha256: str | None = None) -> dict[str, Any]:
    start_mono = time.monotonic()
    start_utc = utc_now()
    if sys.platform == "darwin":
        provider_type = PinnedDarwinNativeProvider
    elif sys.platform.startswith("linux"):
        provider_type = LinuxProvider
    else:
        return {"schema": "v092-monitor06-reconciliation-query/v1", "provider_identity": "unsupported",
                "started_utc": start_utc, "started_monotonic": start_mono,
                "snapshots": [], "provider_children": [],
                "outcome": {"status": "provider-unavailable", "complete": False,
                "error": {"type": "UnsupportedPlatform", "message": sys.platform}}}
    provider_identity = QUERY_PROVIDER_IDENTITY
    snapshots: list[dict[str, Any]] = []
    provider_children: list[dict[str, Any]] = []

    def record_provider_child(value: dict[str, Any]) -> None:
        pid = value.get("pid")
        existing = next((index for index, item in enumerate(provider_children)
                         if item.get("pid") == pid), None)
        if existing is None:
            provider_children.append(dict(value))
        else:
            provider_children[existing] = dict(value)
        if callable(on_provider_child):
            on_provider_child(value)

    try:
        if provider_type is PinnedDarwinNativeProvider:
            native_provider = provider_type(
                deadline,
                module_path=darwin_native_module_path,
                module_sha256=darwin_native_module_sha256,
                dylib_path=darwin_native_dylib_path,
                dylib_sha256=darwin_native_dylib_sha256,
            )
        else:
            native_provider = provider_type(deadline)
        command_provider = PsCommandProvider(
            deadline, child_event=record_provider_child,
            version="v2" if sys.platform == "darwin" else "v1",
        )
        for name, provider, function in (("native-before", native_provider, native_provider.native_table),
                                         ("command", command_provider, command_provider.command_table),
                                         ("native-after", native_provider, native_provider.native_table)):
            snapshot = _snapshot(name, provider, function, deadline)
            snapshots.append(snapshot)
            if on_snapshot is not None:
                on_snapshot(snapshot)
        order_valid = len(snapshots) == 3 and all(
            snapshots[index]["ended_monotonic"] <= snapshots[index + 1]["started_monotonic"]
            for index in range(len(snapshots) - 1)
        )
        complete = len(snapshots) == 3 and all(s["complete"] and s["coverage"] and not s["truncated"] for s in snapshots) and order_valid
        outcome = {"status": "complete-provider-scoped" if complete else "incomplete-provider-observation",
                   "complete": complete, "order_valid": order_valid, "error": None}
    except BaseException as error:
        outcome = {"status": "provider-error", "complete": False, "order_valid": False,
                   "error": {"type": type(error).__name__, "message": str(error)}}
    return {
        "schema": "v092-monitor06-reconciliation-query/v1",
        "provider_identity": provider_identity,
        "started_utc": start_utc,
        "started_monotonic": start_mono,
        "ended_utc": utc_now(),
        "ended_monotonic": time.monotonic(),
        "snapshots": snapshots,
        "outcome": outcome,
        "provider_children": provider_children,
        "os_global_completeness_claim": False,
        "continuous_absence_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline-monotonic", required=True, type=float)
    parser.add_argument("--darwin-native-module-path")
    parser.add_argument("--darwin-native-module-sha256")
    parser.add_argument("--darwin-native-dylib-path")
    parser.add_argument("--darwin-native-dylib-sha256")
    args = parser.parse_args()
    emitted_bytes = 0

    def emit_snapshot(snapshot: dict[str, Any]) -> None:
        nonlocal emitted_bytes
        record = {"kind": "snapshot", "snapshot": snapshot}
        raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
        if emitted_bytes + len(raw) > 16 * 1024 * 1024 - 4096:
            import hashlib
            rows_raw = json.dumps(snapshot.get("rows", []), sort_keys=True, separators=(",", ":")).encode("utf-8")
            snapshot["complete"] = False
            snapshot["truncated"] = True
            snapshot["error"] = {"type": "OutputLimit", "message": "combined snapshot stream exceeds 16 MiB"}
            coverage = dict(snapshot.get("coverage") or {})
            coverage["truncated"] = True
            snapshot["coverage"] = coverage
            snapshot["row_count_before_output_truncation"] = len(snapshot.get("rows", []))
            snapshot["rows_sha256_before_output_truncation"] = hashlib.sha256(rows_raw).hexdigest()
            snapshot["rows"] = []
            snapshot.pop("table", None)
            record = {"kind": "snapshot", "snapshot": snapshot}
            raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()
        emitted_bytes += len(raw)

    def emit_provider_child(value: dict[str, Any]) -> None:
        nonlocal emitted_bytes
        raw = json.dumps({"kind": "provider-child", "provider_child": value},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
        if emitted_bytes + len(raw) > 16 * 1024 * 1024 - 4096:
            compact = {key: value.get(key) for key in (
                "kind", "provider_identity", "pid", "started_monotonic", "ended_monotonic",
                "kill_requested", "returncode", "reaped", "cleanup_incomplete",
                "direct_child_only", "descendant_containment")}
            compact["stream_truncated"] = True
            raw = json.dumps({"kind": "provider-child", "provider_child": compact},
                             sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()
        emitted_bytes += len(raw)

    try:
        result = query(
            args.deadline_monotonic,
            on_snapshot=emit_snapshot,
            on_provider_child=emit_provider_child,
            darwin_native_module_path=args.darwin_native_module_path,
            darwin_native_module_sha256=args.darwin_native_module_sha256,
            darwin_native_dylib_path=args.darwin_native_dylib_path,
            darwin_native_dylib_sha256=args.darwin_native_dylib_sha256,
        )
    except BaseException as error:
        result = {"schema": "v092-monitor06-reconciliation-query/v1", "provider_identity": "initialization-failed",
                  "snapshots": [], "outcome": {"status": "provider-error", "complete": False,
                  "order_valid": False, "error": {"type": type(error).__name__, "message": str(error)}}}
    final = {key: value for key, value in result.items() if key != "snapshots"}
    final["snapshot_count"] = len(result.get("snapshots", []))
    record = {"kind": "final", "result": final}
    raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
    if emitted_bytes + len(raw) > 16 * 1024 * 1024:
        record["result"]["outcome"] = {"status": "truncated-output", "complete": False,
                                        "order_valid": False,
                                        "error": {"type": "OutputLimit", "message": "query result exceeds 16 MiB"}}
        raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return 0 if result.get("outcome", {}).get("complete") else 2

if __name__ == "__main__":
    raise SystemExit(main())
