"""Source-only ctypes adapter for the bounded Darwin KERN_PROC_ALL helper.

The production constructor requires an absolute, regular, SHA-256-pinned dylib
path. Synthetic unit tests may use the explicitly test-only factory; its
coverage metadata says so and is not production provider evidence.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path
import stat
import time
from typing import Any


ABI_VERSION = 4
MAX_ROWS = 8192
MAX_COMMAND_BYTES = 4096
COMMAND_CAPACITY = MAX_COMMAND_BYTES + 1

STATE_R = ord("R")
STATE_S = ord("S")
STATE_T = ord("T")
STATE_Z = ord("Z")

COMMAND_SOURCE_PROC_PIDPATH = 1
COMMAND_SOURCE_KINFO_P_COMM = 2
COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW = 3
COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY = 4

COMMAND_PATH_RESOLVED = 1
COMMAND_PATH_SHORT_COMM_FALLBACK = 2
COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW = 3
COMMAND_PATH_RESERVED_V4_FIRST_TABLE_ONLY = 4
COMMAND_PATH_DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY = 5
PATH_ERRNO_NOT_ATTEMPTED = -1

NATIVE_ORIGIN_FIRST_TABLE = 1
NATIVE_ORIGIN_SECOND_TABLE_ONLY = 2
NATIVE_ORIGIN_FIRST_TABLE_ONLY = 3
REVALIDATION_MATCHED_SECOND_TABLE = 1
REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED = 2
REVALIDATION_FIRST_TABLE_ONLY_UNVERIFIED = 3

API_NAMES = {
    0: "none",
    1: "sysctl(KERN_PROC_ALL)/first",
    2: "proc_pidpath",
    3: "sysctl(KERN_PROC_ALL)/revalidation",
    4: "row-validation",
    5: "allocation",
    6: "argument-validation",
}

STATUS_NAMES = {
    0: "ok",
    1: "invalid-argument",
    2: "allocation-failure",
    3: "first-kern-proc-all-failed",
    4: "first-kern-proc-all-capacity-exceeded",
    5: "first-kern-proc-all-record-alignment-invalid",
    6: "first-kern-proc-all-row-invalid",
    7: "first-kern-proc-all-duplicate-pid",
    8: "proc-pidpath-failed",
    9: "revalidation-kern-proc-all-failed",
    10: "revalidation-kern-proc-all-capacity-exceeded",
    11: "revalidation-kern-proc-all-record-alignment-invalid",
    12: "revalidation-kern-proc-all-row-invalid",
    13: "revalidation-kern-proc-all-duplicate-pid",
    14: "reserved-v3-revalidation-pid-missing",
    15: "revalidation-identity-changed",
}


class NativeRowV4(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int32),
        ("ppid", ctypes.c_int32),
        ("birth_seconds", ctypes.c_uint64),
        ("birth_microseconds", ctypes.c_uint32),
        ("state", ctypes.c_uint32),
        ("command_source", ctypes.c_uint32),
        ("command_length", ctypes.c_uint32),
        ("command_path_errno", ctypes.c_int32),
        ("command_path_status", ctypes.c_uint32),
        ("native_snapshot_origin", ctypes.c_uint32),
        ("revalidation_witness", ctypes.c_uint32),
        ("command", ctypes.c_char * COMMAND_CAPACITY),
    ]


class NativeMetaV3(ctypes.Structure):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("status", ctypes.c_int32),
        ("api", ctypes.c_int32),
        ("error_errno", ctypes.c_int32),
        ("error_pid", ctypes.c_int32),
        ("error_returned", ctypes.c_int32),
        ("error_expected", ctypes.c_uint32),
        ("first_bytes", ctypes.c_uint64),
        ("second_bytes", ctypes.c_uint64),
        ("table_capacity_bytes", ctypes.c_uint64),
        ("record_size", ctypes.c_uint32),
        ("first_record_count", ctypes.c_uint32),
        ("second_record_count", ctypes.c_uint32),
        ("output_row_count", ctypes.c_uint32),
        ("revalidated_row_count", ctypes.c_uint32),
        ("first_table_only_pid_count", ctypes.c_uint32),
        ("additional_second_pid_count", ctypes.c_uint32),
        ("excluded_pid0_count", ctypes.c_uint32),
        ("second_excluded_pid0_count", ctypes.c_uint32),
    ]


class DarwinNativeProviderError(RuntimeError):
    def __init__(self, message: str, diagnostic: dict[str, Any] | None = None):
        super().__init__(message)
        self.diagnostic = diagnostic or {}


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _lstat_path_without_symlink_ancestors(path: Path, *, stage: str) -> os.stat_result:
    if not path.is_absolute():
        raise DarwinNativeProviderError(
            "native provider dylib path must be absolute",
            {"stage": stage, "path": str(path)},
        )
    current = Path(path.anchor)
    parts = path.parts[1:]
    final_stat = None
    for index, part in enumerate(parts):
        current = current / part
        try:
            observed = current.lstat()
        except OSError as error:
            raise DarwinNativeProviderError(
                "native provider dylib path component cannot be inspected",
                {"stage": stage, "errno": error.errno, "component": str(current)},
            ) from error
        if stat.S_ISLNK(observed.st_mode):
            raise DarwinNativeProviderError(
                "native provider dylib path contains a symlink component",
                {"stage": stage, "component": str(current)},
            )
        is_final = index == len(parts) - 1
        if is_final:
            if not stat.S_ISREG(observed.st_mode):
                raise DarwinNativeProviderError(
                    "native provider dylib path must end in a regular file",
                    {"stage": stage, "component": str(current)},
                )
            final_stat = observed
        elif not stat.S_ISDIR(observed.st_mode):
            raise DarwinNativeProviderError(
                "native provider dylib parent component is not a directory",
                {"stage": stage, "component": str(current)},
            )
    if final_stat is None:
        raise DarwinNativeProviderError(
            "native provider dylib path is not a file",
            {"stage": stage, "path": str(path)},
        )
    return final_stat


def _hash_file(path: Path) -> tuple[str, tuple[int, int, int, int, int]]:
    link_stat = _lstat_path_without_symlink_ancestors(path, stage="library-stat")
    try:
        with path.open("rb") as handle:
            opened_stat = os.fstat(handle.fileno())
            if _stat_identity(link_stat) != _stat_identity(opened_stat):
                raise DarwinNativeProviderError(
                    "native provider dylib changed while opening",
                    {"stage": "library-open-race"},
                )
            digest = hashlib.sha256()
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
            closed_identity = _stat_identity(os.fstat(handle.fileno()))
    except DarwinNativeProviderError:
        raise
    except OSError as error:
        raise DarwinNativeProviderError(
            "native provider dylib cannot be hashed",
            {"stage": "library-hash", "errno": error.errno},
        ) from error
    final_identity = _stat_identity(
        _lstat_path_without_symlink_ancestors(path, stage="library-stat-after-hash")
    )
    if closed_identity != final_identity or closed_identity != _stat_identity(link_stat):
        raise DarwinNativeProviderError(
            "native provider dylib changed while hashing",
            {"stage": "library-hash-race"},
        )
    return digest.hexdigest(), closed_identity


class DarwinKernProcAllProvider:
    """Read first-table identities and typed second-table-only observations."""

    identity = "darwin-sysctl-kern-proc-all-libproc/v4"

    def __init__(
        self,
        library_path: str | os.PathLike[str],
        expected_library_sha256: str,
        *,
        deadline: float | None = None,
    ) -> None:
        path = Path(library_path)
        if not path.is_absolute():
            raise DarwinNativeProviderError(
                "native provider dylib path must be absolute",
                {"stage": "library-binding"},
            )
        if not isinstance(expected_library_sha256, str) or len(expected_library_sha256) != 64 or any(
            char not in "0123456789abcdefABCDEF" for char in expected_library_sha256
        ):
            raise DarwinNativeProviderError(
                "native provider dylib requires a 64-digit SHA-256 pin",
                {"stage": "library-binding"},
            )
        actual_digest, identity_before_load = _hash_file(path)
        if actual_digest.lower() != expected_library_sha256.lower():
            raise DarwinNativeProviderError(
                "native provider dylib SHA-256 does not match its pin",
                {
                    "stage": "library-hash-mismatch",
                    "expected_sha256": expected_library_sha256.lower(),
                    "actual_sha256": actual_digest,
                },
            )
        try:
            library = ctypes.CDLL(os.fspath(path), use_errno=True)
        except OSError as error:
            raise DarwinNativeProviderError(
                "pinned native provider dylib could not be loaded",
                {"stage": "library-load", "errno": error.errno},
            ) from error
        actual_after_load, identity_after_load = _hash_file(path)
        if (
            actual_after_load.lower() != expected_library_sha256.lower()
            or identity_after_load != identity_before_load
        ):
            raise DarwinNativeProviderError(
                "native provider dylib changed during load",
                {
                    "stage": "library-load-race",
                    "expected_sha256": expected_library_sha256.lower(),
                    "actual_sha256": actual_after_load,
                },
            )
        self._library_sha256 = actual_digest.lower()
        self._test_only_injection = False
        self._deadline = deadline
        self._bind(library)
        self._check_abi()

    @classmethod
    def _from_test_library(
        cls,
        library: Any,
        *,
        test_sha256: str = "test-injected-not-a-production-dylib",
        deadline: float | None = None,
    ) -> "DarwinKernProcAllProvider":
        """Explicit test-only constructor; never evidence of a compiled dylib."""
        instance = cls.__new__(cls)
        instance._library_sha256 = test_sha256
        instance._test_only_injection = True
        instance._deadline = deadline
        instance._bind(library)
        instance._check_abi()
        return instance

    def _bind(self, library: Any) -> None:
        self._library = library
        try:
            self._abi_version_fn = library.dfb_native_abi_version
            self._max_rows_fn = library.dfb_native_max_rows
            self._max_command_bytes_fn = library.dfb_native_max_command_bytes
            self._max_short_comm_bytes_fn = library.dfb_native_max_short_comm_bytes
            self._row_size_fn = library.dfb_native_row_size
            self._meta_size_fn = library.dfb_native_meta_size
            self._snapshot_fn = library.dfb_native_snapshot_v4
        except AttributeError as error:
            raise DarwinNativeProviderError(
                "native provider dylib is missing a required ABI symbol",
                {"stage": "abi-symbol-binding", "missing_symbol": str(error)},
            ) from error
        for function in (
            self._abi_version_fn,
            self._max_rows_fn,
            self._max_command_bytes_fn,
            self._max_short_comm_bytes_fn,
            self._row_size_fn,
            self._meta_size_fn,
        ):
            function.argtypes = []
            function.restype = ctypes.c_uint32
        self._snapshot_fn.argtypes = [
            ctypes.POINTER(NativeRowV4),
            ctypes.c_uint32,
            ctypes.POINTER(NativeMetaV3),
        ]
        self._snapshot_fn.restype = ctypes.c_int32

    def _check_abi(self) -> None:
        values = {
            "abi_version": int(self._abi_version_fn()),
            "max_rows": int(self._max_rows_fn()),
            "max_command_bytes": int(self._max_command_bytes_fn()),
            "max_short_comm_bytes": int(self._max_short_comm_bytes_fn()),
            "row_size": int(self._row_size_fn()),
            "meta_size": int(self._meta_size_fn()),
        }
        expected = {
            "abi_version": ABI_VERSION,
            "max_rows": MAX_ROWS,
            "max_command_bytes": MAX_COMMAND_BYTES,
            "row_size": ctypes.sizeof(NativeRowV4),
            "meta_size": ctypes.sizeof(NativeMetaV3),
        }
        if values["abi_version"] != ABI_VERSION:
            raise DarwinNativeProviderError(
                "native provider ABI version mismatch",
                {"stage": "abi-check", "expected": expected, "actual": values},
            )
        for key, wanted in expected.items():
            if values[key] != wanted:
                raise DarwinNativeProviderError(
                    "native provider ABI size or bound mismatch",
                    {"stage": "abi-check", "expected": expected, "actual": values},
                )
        if not 1 <= values["max_short_comm_bytes"] < COMMAND_CAPACITY:
            raise DarwinNativeProviderError(
                "native provider short command bound is invalid",
                {"stage": "abi-check", "expected": expected, "actual": values},
            )
        self._max_short_comm_bytes = values["max_short_comm_bytes"]

    def _deadline_check(self, stage: str) -> None:
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise DarwinNativeProviderError(
                "absolute reconciliation deadline exceeded during " + stage,
                {"provider": self.identity, "stage": stage, "deadline_exceeded": True},
            )

    @staticmethod
    def _diagnostic(meta: NativeMetaV3, return_code: int) -> dict[str, Any]:
        return {
            "provider": DarwinKernProcAllProvider.identity,
            "status": STATUS_NAMES.get(int(meta.status), "unknown-status"),
            "return_code": int(return_code),
            "api": API_NAMES.get(int(meta.api), "unknown-api"),
            "error_errno": int(meta.error_errno),
            "error_pid": int(meta.error_pid),
            "error_returned": int(meta.error_returned),
            "error_expected": int(meta.error_expected),
            "first_record_count": int(meta.first_record_count),
            "second_record_count": int(meta.second_record_count),
            "output_row_count": int(meta.output_row_count),
            "revalidated_row_count": int(meta.revalidated_row_count),
            "first_table_only_pid_count": int(meta.first_table_only_pid_count),
            "additional_second_pid_count": int(meta.additional_second_pid_count),
            "excluded_pid0_count": int(meta.excluded_pid0_count),
            "second_excluded_pid0_count": int(meta.second_excluded_pid0_count),
            "first_bytes": int(meta.first_bytes),
            "second_bytes": int(meta.second_bytes),
            "record_size": int(meta.record_size),
            "table_capacity_bytes": int(meta.table_capacity_bytes),
        }

    def native_table(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        self._deadline_check("before Darwin native snapshot dylib call")
        output = (NativeRowV4 * MAX_ROWS)()
        meta = NativeMetaV3()
        return_code = int(self._snapshot_fn(output, MAX_ROWS, ctypes.byref(meta)))
        self._deadline_check("after Darwin native snapshot dylib call")

        if int(meta.abi_version) != ABI_VERSION or int(meta.struct_size) != ctypes.sizeof(NativeMetaV3):
            raise DarwinNativeProviderError(
                "native provider returned incompatible metadata ABI",
                {
                    "provider": self.identity,
                    "expected_abi_version": ABI_VERSION,
                    "observed_abi_version": int(meta.abi_version),
                    "expected_meta_size": ctypes.sizeof(NativeMetaV3),
                    "observed_meta_size": int(meta.struct_size),
                },
            )
        if return_code != 0 or int(meta.status) != 0:
            raise DarwinNativeProviderError(
                "Darwin native process provider is incomplete",
                self._diagnostic(meta, return_code),
            )

        row_count = int(meta.output_row_count)
        first_count = int(meta.first_record_count)
        second_count = int(meta.second_record_count)
        revalidated_count = int(meta.revalidated_row_count)
        added_count = int(meta.additional_second_pid_count)
        first_only_count = int(meta.first_table_only_pid_count)
        first_pid0_count = int(meta.excluded_pid0_count)
        second_pid0_count = int(meta.second_excluded_pid0_count)
        first_positive_count = first_count - first_pid0_count
        second_positive_count = second_count - second_pid0_count
        stable_count = revalidated_count
        if (
            row_count >= MAX_ROWS
            or first_count >= MAX_ROWS
            or second_count >= MAX_ROWS
            or first_pid0_count > 1
            or second_pid0_count > 1
            or added_count < 0
            or first_only_count < 0
            or first_positive_count < 1
            or first_count != first_positive_count + first_pid0_count
            or first_positive_count != stable_count + first_only_count
            or second_positive_count != stable_count + added_count
            or second_count != second_positive_count + second_pid0_count
            or row_count != first_positive_count + added_count
            or row_count != stable_count + first_only_count + added_count
            or int(meta.record_size) <= 0
            or int(meta.table_capacity_bytes) != MAX_ROWS * int(meta.record_size)
            or int(meta.first_bytes) != first_count * int(meta.record_size)
            or int(meta.second_bytes) != second_count * int(meta.record_size)
            or int(meta.first_bytes) > int(meta.table_capacity_bytes)
            or int(meta.second_bytes) > int(meta.table_capacity_bytes)
        ):
            raise DarwinNativeProviderError(
                "Darwin native provider returned inconsistent complete-coverage metadata",
                self._diagnostic(meta, return_code),
            )
        result_rows: list[dict[str, Any]] = []
        seen: set[int] = set()
        first_rows_seen = 0
        first_only_rows_seen = 0
        second_only_rows_seen = 0
        command_offset = NativeRowV4.command.offset
        for index in range(row_count):
            row = output[index]
            pid = int(row.pid)
            ppid = int(row.ppid)
            seconds = int(row.birth_seconds)
            microseconds = int(row.birth_microseconds)
            state_value = int(row.state)
            source_value = int(row.command_source)
            command_length = int(row.command_length)
            command_path_errno = int(row.command_path_errno)
            path_status = int(row.command_path_status)
            snapshot_origin = int(row.native_snapshot_origin)
            revalidation_witness = int(row.revalidation_witness)

            expected_origin = (
                NATIVE_ORIGIN_FIRST_TABLE
                if source_value in (COMMAND_SOURCE_PROC_PIDPATH, COMMAND_SOURCE_KINFO_P_COMM)
                else NATIVE_ORIGIN_SECOND_TABLE_ONLY
                if source_value == COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW
                else NATIVE_ORIGIN_FIRST_TABLE_ONLY
            )
            expected_witness = (
                REVALIDATION_MATCHED_SECOND_TABLE
                if expected_origin == NATIVE_ORIGIN_FIRST_TABLE
                else REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED
                if expected_origin == NATIVE_ORIGIN_SECOND_TABLE_ONLY
                else REVALIDATION_FIRST_TABLE_ONLY_UNVERIFIED
            )
            expected_path_status = {
                COMMAND_SOURCE_PROC_PIDPATH: COMMAND_PATH_RESOLVED,
                COMMAND_SOURCE_KINFO_P_COMM: COMMAND_PATH_SHORT_COMM_FALLBACK,
                COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW: COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW,
                COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY:
                    COMMAND_PATH_DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY,
            }.get(source_value)
            errno_valid = (
                command_path_errno == 0
                if source_value == COMMAND_SOURCE_PROC_PIDPATH
                else command_path_errno >= 0
                if source_value == COMMAND_SOURCE_KINFO_P_COMM
                else command_path_errno == PATH_ERRNO_NOT_ATTEMPTED
                if source_value == COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW
                else command_path_errno >= 0
                if source_value == COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY
                else False
            )

            if (
                pid <= 0
                or ppid < 0
                or seconds <= 0
                or not 0 <= microseconds < 1_000_000
                or state_value not in (STATE_R, STATE_S, STATE_T, STATE_Z)
                or source_value not in (
                    COMMAND_SOURCE_PROC_PIDPATH,
                    COMMAND_SOURCE_KINFO_P_COMM,
                    COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
                    COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY,
                )
                or not 0 < command_length <= MAX_COMMAND_BYTES
                or not errno_valid
                or path_status != expected_path_status
                or snapshot_origin != expected_origin
                or revalidation_witness != expected_witness
                or pid in seen
            ):
                raise DarwinNativeProviderError(
                    "Darwin native provider returned a malformed or duplicate row",
                    {
                        "provider": self.identity,
                        "row_index": index,
                        "pid": pid,
                        "ppid": ppid,
                        "birth_seconds": seconds,
                        "birth_microseconds": microseconds,
                        "state": state_value,
                        "command_source": source_value,
                        "command_length": command_length,
                        "command_path_errno": command_path_errno,
                        "command_path_status": path_status,
                        "native_snapshot_origin": snapshot_origin,
                        "revalidation_witness": revalidation_witness,
                    },
                )

            storage = ctypes.string_at(
                ctypes.addressof(row) + command_offset, COMMAND_CAPACITY
            )
            command_bytes = storage[:command_length]
            if storage[command_length : command_length + 1] != b"\0" or b"\0" in command_bytes:
                raise DarwinNativeProviderError(
                    "Darwin native provider command field has invalid termination",
                    {"provider": self.identity, "row_index": index, "pid": pid},
                )
            if (
                source_value in (
                    COMMAND_SOURCE_KINFO_P_COMM,
                    COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
                    COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY,
                )
                and command_length > self._max_short_comm_bytes
            ):
                raise DarwinNativeProviderError(
                    "Darwin native provider short command fallback exceeds SDK bound",
                    {
                        "provider": self.identity,
                        "row_index": index,
                        "pid": pid,
                        "command_length": command_length,
                        "max_short_comm_bytes": self._max_short_comm_bytes,
                    },
                )
            try:
                command = command_bytes.decode("utf-8", "strict")
            except UnicodeDecodeError as error:
                raise DarwinNativeProviderError(
                    "Darwin native provider command is not valid UTF-8",
                    {
                        "provider": self.identity,
                        "row_index": index,
                        "pid": pid,
                        "decode_error": str(error),
                    },
                ) from error
            if not command:
                raise DarwinNativeProviderError(
                    "Darwin native provider command is empty",
                    {"provider": self.identity, "row_index": index, "pid": pid},
                )

            seen.add(pid)
            if expected_origin == NATIVE_ORIGIN_FIRST_TABLE:
                first_rows_seen += 1
            elif expected_origin == NATIVE_ORIGIN_FIRST_TABLE_ONLY:
                first_only_rows_seen += 1
            else:
                second_only_rows_seen += 1
            source = {
                COMMAND_SOURCE_PROC_PIDPATH: "proc_pidpath",
                COMMAND_SOURCE_KINFO_P_COMM: "sysctl_kern_proc_all.p_comm",
                COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW:
                    "sysctl_kern_proc_all.second_table_new.p_comm",
                COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY:
                    "sysctl_kern_proc_all.first_table_only.p_comm",
            }[source_value]
            path_status_name = {
                COMMAND_PATH_RESOLVED: "resolved",
                COMMAND_PATH_SHORT_COMM_FALLBACK: "short-comm-fallback",
                COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW:
                    "not-attempted-second-table-new",
                COMMAND_PATH_DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY:
                    "discarded-unrevalidated-first-table-only",
            }[path_status]
            result_rows.append(
                {
                    "pid": pid,
                    "ppid": ppid,
                    "birth_identity": f"{seconds}:{microseconds}",
                    "state": chr(state_value),
                    "command": command,
                    "command_executable": command,
                    "command_name": os.path.basename(command),
                    "command_source": source,
                    "command_source_is_kernel_comm": (
                        source_value != COMMAND_SOURCE_PROC_PIDPATH
                    ),
                    "command_path_status": path_status_name,
                    "command_path_errno": (
                        None
                        if path_status == COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW
                        else command_path_errno
                    ),
                    "native_snapshot_origin": (
                        "first-table"
                        if snapshot_origin == NATIVE_ORIGIN_FIRST_TABLE
                        else "second-table-only"
                        if snapshot_origin == NATIVE_ORIGIN_SECOND_TABLE_ONLY
                        else "first-table-only"
                    ),
                    "revalidation_witness": (
                        "matched-in-second-table"
                        if revalidation_witness == REVALIDATION_MATCHED_SECOND_TABLE
                        else "second-table-only-unverified"
                        if revalidation_witness == REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED
                        else "first-table-only-unverified"
                    ),
                    "command_arguments_available": False,
                }
            )

        if (first_rows_seen != stable_count or
                first_only_rows_seen != first_only_count or
                second_only_rows_seen != added_count):
            raise DarwinNativeProviderError(
                "Darwin native provider row provenance counts differ from complete-coverage metadata",
                self._diagnostic(meta, return_code),
            )

        coverage = {
            "enumeration": "sysctl(KERN_PROC_ALL) first-table identities plus second-table-only additions",
            "enumerated_pid_count": first_count + added_count,
            "pid_capacity": MAX_ROWS,
            "truncated": False,
            "coverage_errors": [],
            "excluded_pid0_kernel_entries": int(meta.excluded_pid0_count),
            "returned_pid_count": row_count,
            "required_fields": ["pid", "ppid", "birth_identity", "state", "command"],
            "provider_evidence": {
                "identity": self.identity,
                "abi_version": int(meta.abi_version),
                "library_sha256": self._library_sha256,
                "test_only_injected_library": self._test_only_injection,
                "first_table_sysctl_calls": 1,
                "revalidation_table_sysctl_calls": 1,
                "first_snapshot_record_count": int(meta.first_record_count),
                "second_snapshot_record_count": int(meta.second_record_count),
                "output_row_count": row_count,
                "revalidated_first_row_count": int(meta.revalidated_row_count),
                "first_table_only_pid_count": first_only_count,
                "first_table_only_output_row_count": first_only_rows_seen,
                "first_snapshot_excluded_pid0_count": first_pid0_count,
                "second_snapshot_excluded_pid0_count": second_pid0_count,
                "additional_second_snapshot_pid_count": int(
                    meta.additional_second_pid_count
                ),
                "second_table_only_output_row_count": second_only_rows_seen,
                "historical_absence_claim": False,
                "scope": (
                    "One fixed-bound first KERN_PROC_ALL table is followed by exactly "
                    "one revalidation table. Stable rows retain their first-table path "
                    "or p_comm only when PID/PPID/birth match. First-table-only rows "
                    "retain only exact first-table PID/PPID/birth/state/p_comm with "
                    "unverified provenance; any earlier proc_pidpath bytes are discarded. "
                    "Second-table-only rows retain atomic PID/PPID/birth/state/p_comm. "
                    "Neither one-sided category is revalidated or implies historical "
                    "absence, ownership, or current identity. No retry or third table "
                    "is performed."
                ),
            },
        }
        return result_rows, coverage
