from __future__ import annotations

import ctypes
import errno
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from darwin_native_provider import (
    ABI_VERSION,
    COMMAND_CAPACITY,
    COMMAND_SOURCE_KINFO_P_COMM,
    COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
    COMMAND_SOURCE_PROC_PIDPATH,
    COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW,
    COMMAND_PATH_RESOLVED,
    COMMAND_PATH_SHORT_COMM_FALLBACK,
    DarwinKernProcAllProvider,
    DarwinNativeProviderError,
    MAX_COMMAND_BYTES,
    MAX_ROWS,
    NativeMetaV2,
    NativeRowV3,
    NATIVE_ORIGIN_FIRST_TABLE,
    NATIVE_ORIGIN_SECOND_TABLE_ONLY,
    PATH_ERRNO_NOT_ATTEMPTED,
    REVALIDATION_MATCHED_SECOND_TABLE,
    REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED,
    STATE_R,
    STATUS_NAMES,
)


class StubFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeLibrary:
    def __init__(self, rows=None, *, status=0, api=0, errno_value=0,
                 version=ABI_VERSION, first_record_count=None,
                 second_record_count=None, additional_count=0,
                 excluded_pid0=0, second_excluded_pid0=0, revalidated_count=None,
                 record_size=648, returned_status=None, max_rows=MAX_ROWS):
        self.rows = list(rows or [])
        self.status = status
        self.api = api
        self.errno_value = errno_value
        self.version = version
        first_positive = len(self.rows) - additional_count
        self.first_record_count = (
            first_positive + excluded_pid0
            if first_record_count is None else first_record_count
        )
        self.second_record_count = (
            first_positive + additional_count + second_excluded_pid0
            if second_record_count is None else second_record_count
        )
        self.additional_count = additional_count
        self.excluded_pid0 = excluded_pid0
        self.second_excluded_pid0 = second_excluded_pid0
        self.revalidated_count = (
            first_positive if revalidated_count is None else revalidated_count
        )
        self.record_size = record_size
        self.returned_status = status if returned_status is None else returned_status
        self.max_rows = max_rows
        self.snapshot_calls = 0

        self.dfb_native_abi_version = StubFunction(lambda: self.version)
        self.dfb_native_max_rows = StubFunction(lambda: self.max_rows)
        self.dfb_native_max_command_bytes = StubFunction(lambda: MAX_COMMAND_BYTES)
        self.dfb_native_max_short_comm_bytes = StubFunction(lambda: 16)
        self.dfb_native_row_size = StubFunction(lambda: ctypes.sizeof(NativeRowV3))
        self.dfb_native_meta_size = StubFunction(lambda: ctypes.sizeof(NativeMetaV2))
        self.dfb_native_snapshot_v3 = StubFunction(self._snapshot)

    @staticmethod
    def _write_command(row, command: bytes) -> None:
        ctypes.memset(
            ctypes.addressof(row) + NativeRowV3.command.offset,
            0,
            COMMAND_CAPACITY,
        )
        ctypes.memmove(
            ctypes.addressof(row) + NativeRowV3.command.offset,
            command,
            len(command),
        )
        row.command_length = len(command)

    def _snapshot(self, output, capacity, meta_pointer):
        self.snapshot_calls += 1
        meta = ctypes.cast(meta_pointer, ctypes.POINTER(NativeMetaV2)).contents
        meta.abi_version = self.version
        meta.struct_size = ctypes.sizeof(NativeMetaV2)
        meta.status = self.status
        meta.api = self.api
        meta.error_errno = self.errno_value
        meta.error_pid = 1234 if self.status else 0
        meta.error_returned = 0
        meta.error_expected = 0
        meta.first_record_count = self.first_record_count
        meta.second_record_count = self.second_record_count
        meta.output_row_count = len(self.rows)
        meta.revalidated_row_count = self.revalidated_count if not self.status else 0
        meta.additional_second_pid_count = self.additional_count
        meta.excluded_pid0_count = self.excluded_pid0
        meta.second_excluded_pid0_count = self.second_excluded_pid0
        meta.record_size = self.record_size
        meta.first_bytes = self.first_record_count * self.record_size
        meta.second_bytes = self.second_record_count * self.record_size
        meta.table_capacity_bytes = MAX_ROWS * self.record_size
        if self.status == 0:
            for index, item in enumerate(self.rows):
                row = output[index]
                row.pid = item.get("pid", 100 + index)
                row.ppid = item.get("ppid", 1)
                row.birth_seconds = item.get("birth_seconds", 1700000000 + index)
                row.birth_microseconds = item.get("birth_microseconds", 100 + index)
                row.state = item.get("state", STATE_R)
                row.command_source = item.get("command_source", COMMAND_SOURCE_PROC_PIDPATH)
                source = row.command_source
                row.command_path_errno = item.get(
                    "command_path_errno",
                    PATH_ERRNO_NOT_ATTEMPTED
                    if source == COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW else 0,
                )
                row.command_path_status = item.get(
                    "command_path_status",
                    {
                        COMMAND_SOURCE_PROC_PIDPATH: COMMAND_PATH_RESOLVED,
                        COMMAND_SOURCE_KINFO_P_COMM: COMMAND_PATH_SHORT_COMM_FALLBACK,
                        COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW:
                            COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW,
                    }.get(source, 0),
                )
                row.native_snapshot_origin = item.get(
                    "native_snapshot_origin",
                    NATIVE_ORIGIN_SECOND_TABLE_ONLY
                    if source == COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW
                    else NATIVE_ORIGIN_FIRST_TABLE,
                )
                row.revalidation_witness = item.get(
                    "revalidation_witness",
                    REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED
                    if source == COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW
                    else REVALIDATION_MATCHED_SECOND_TABLE,
                )
                self._write_command(row, item.get("command", b"/usr/bin/example"))
        return self.returned_status


class DarwinNativeProviderTests(unittest.TestCase):
    def provider(self, library: FakeLibrary) -> DarwinKernProcAllProvider:
        return DarwinKernProcAllProvider._from_test_library(library)

    def test_success_returns_native_snapshot_shape_and_scoped_metadata(self):
        library = FakeLibrary(
            [
                {
                    "pid": 101,
                    "ppid": 1,
                    "birth_seconds": 1700000100,
                    "birth_microseconds": 123,
                    "state": STATE_R,
                    "command_source": COMMAND_SOURCE_PROC_PIDPATH,
                    "command": b"/Applications/Example.app/Contents/MacOS/Example",
                },
                {
                    "pid": 102,
                    "ppid": 101,
                    "birth_seconds": 1700000101,
                    "birth_microseconds": 456,
                    "command_source": COMMAND_SOURCE_KINFO_P_COMM,
                    "command": b"python3",
                },
            ],
            excluded_pid0=1,
            second_excluded_pid0=1,
        )
        rows, coverage = self.provider(library).native_table()

        self.assertEqual([row["pid"] for row in rows], [101, 102])
        self.assertEqual(rows[0]["birth_identity"], "1700000100:123")
        self.assertEqual(rows[0]["command_source"], "proc_pidpath")
        self.assertEqual(rows[1]["command_source"], "sysctl_kern_proc_all.p_comm")
        self.assertEqual(rows[0]["command_path_status"], "resolved")
        self.assertEqual(rows[0]["native_snapshot_origin"], "first-table")
        self.assertEqual(rows[0]["revalidation_witness"], "matched-in-second-table")
        self.assertEqual(rows[0]["command_path_errno"], 0)
        self.assertFalse(rows[0]["command_source_is_kernel_comm"])
        self.assertEqual(rows[1]["command_path_status"], "short-comm-fallback")
        self.assertEqual(rows[1]["native_snapshot_origin"], "first-table")
        self.assertEqual(rows[1]["revalidation_witness"], "matched-in-second-table")
        self.assertEqual(rows[1]["command_path_errno"], 0)
        self.assertTrue(rows[1]["command_source_is_kernel_comm"])
        self.assertFalse(rows[0]["command_arguments_available"])
        self.assertEqual(
            coverage["enumeration"],
            "sysctl(KERN_PROC_ALL) first identities plus second-table-only additions",
        )
        self.assertEqual(coverage["excluded_pid0_kernel_entries"], 1)
        self.assertEqual(coverage["returned_pid_count"], 2)
        evidence = coverage["provider_evidence"]
        self.assertEqual(evidence["first_table_sysctl_calls"], 1)
        self.assertEqual(evidence["revalidation_table_sysctl_calls"], 1)
        self.assertEqual(evidence["revalidated_first_row_count"], 2)
        self.assertEqual(evidence["additional_second_snapshot_pid_count"], 0)
        self.assertEqual(evidence["second_snapshot_excluded_pid0_count"], 1)
        self.assertTrue(evidence["test_only_injected_library"])
        self.assertIn("do not imply historical absence", evidence["scope"])
        self.assertNotIn("argv", str(rows).lower())
        self.assertNotIn("credentials", str(coverage).lower())

    def test_zero_length_path_with_enoent_uses_typed_short_comm_fallback(self):
        library = FakeLibrary(
            [{
                "pid": 101,
                "ppid": 1,
                "birth_seconds": 1700000100,
                "birth_microseconds": 123,
                "command_source": COMMAND_SOURCE_KINFO_P_COMM,
                "command_path_errno": errno.ENOENT,
                "command": b"python3",
            }]
        )
        rows, _coverage = self.provider(library).native_table()
        self.assertEqual(rows[0]["command"], "python3")
        self.assertEqual(rows[0]["command_source"], "sysctl_kern_proc_all.p_comm")
        self.assertTrue(rows[0]["command_source_is_kernel_comm"])
        self.assertEqual(rows[0]["command_path_status"], "short-comm-fallback")
        self.assertEqual(rows[0]["command_path_errno"], errno.ENOENT)
        self.assertFalse(rows[0]["command_arguments_available"])

    def test_negative_path_errno_is_rejected(self):
        library = FakeLibrary(
            [{
                "pid": 101,
                "command_source": COMMAND_SOURCE_KINFO_P_COMM,
                "command_path_errno": -errno.EPERM,
                "command": b"python3",
            }]
        )
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("malformed or duplicate row", str(raised.exception))

    def test_nonzero_path_errno_with_full_path_is_rejected(self):
        library = FakeLibrary(
            [{"pid": 101, "command_path_errno": errno.ENOENT}]
        )
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("malformed or duplicate row", str(raised.exception))

    def test_new_second_snapshot_pid_is_retained_as_unverified_atomic_identity(self):
        library = FakeLibrary(
            [
                {"pid": 101, "command": b"/usr/bin/example"},
                {
                    "pid": 102,
                    "ppid": 101,
                    "birth_seconds": 1700000200,
                    "birth_microseconds": 321,
                    "state": ord("S"),
                    "command_source": COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
                    "command": b"new-observation",
                },
            ],
            additional_count=1,
        )
        rows, coverage = self.provider(library).native_table()
        self.assertEqual([row["pid"] for row in rows], [101, 102])
        added = rows[1]
        self.assertEqual(added["ppid"], 101)
        self.assertEqual(added["birth_identity"], "1700000200:321")
        self.assertEqual(added["state"], "S")
        self.assertEqual(added["command"], "new-observation")
        self.assertEqual(added["command_source"],
                         "sysctl_kern_proc_all.second_table_new.p_comm")
        self.assertTrue(added["command_source_is_kernel_comm"])
        self.assertEqual(added["command_path_status"], "not-attempted-second-table-new")
        self.assertIsNone(added["command_path_errno"])
        self.assertEqual(added["native_snapshot_origin"], "second-table-only")
        self.assertEqual(added["revalidation_witness"], "second-table-only-unverified")
        self.assertFalse(added["command_arguments_available"])
        evidence = coverage["provider_evidence"]
        self.assertEqual(evidence["revalidated_first_row_count"], 1)
        self.assertEqual(evidence["second_table_only_output_row_count"], 1)
        self.assertFalse(evidence["historical_absence_claim"])
        self.assertIn("not revalidated", evidence["scope"])
        self.assertIn("no path errno was inferred", evidence["scope"])

    def test_second_table_provenance_source_and_path_status_are_exact(self):
        cases = (
            {"native_snapshot_origin": NATIVE_ORIGIN_FIRST_TABLE},
            {"revalidation_witness": REVALIDATION_MATCHED_SECOND_TABLE},
            {"command_path_status": COMMAND_PATH_RESOLVED},
            {"command_path_errno": 0},
        )
        for override in cases:
            with self.subTest(override=override):
                row = {
                    "pid": 102,
                    "command_source": COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
                    "command": b"new-observation",
                } | override
                library = FakeLibrary(
                    [{"pid": 101}, row], additional_count=1
                )
                with self.assertRaises(DarwinNativeProviderError) as raised:
                    self.provider(library).native_table()
                self.assertIn("malformed or duplicate row", str(raised.exception))

    def test_second_table_coverage_counts_must_match_output_provenance(self):
        bad_counts = FakeLibrary(
            [
                {"pid": 101},
                {"pid": 102, "command_source": COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW,
                 "command": b"new-observation"},
            ],
            additional_count=1,
            revalidated_count=0,
        )
        with self.assertRaisesRegex(DarwinNativeProviderError, "inconsistent complete-coverage"):
            self.provider(bad_counts).native_table()

        missing_provenance = FakeLibrary(
            [{"pid": 101}], additional_count=1,
        )
        with self.assertRaisesRegex(DarwinNativeProviderError, "inconsistent complete-coverage"):
            self.provider(missing_provenance).native_table()

        mismatched_row_type = FakeLibrary(
            [
                {"pid": 101},
                {"pid": 102, "command_source": COMMAND_SOURCE_PROC_PIDPATH,
                 "command": b"/usr/bin/extra"},
            ],
            additional_count=1,
        )
        with self.assertRaisesRegex(DarwinNativeProviderError, "row provenance counts"):
            self.provider(mismatched_row_type).native_table()

    def test_unknown_command_source_is_rejected(self):
        library = FakeLibrary([{"pid": 101, "command_source": 99}])
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("malformed or duplicate row", str(raised.exception))

    def test_pinned_production_constructor_hashes_before_loading(self):
        library = FakeLibrary([])
        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            path = Path(directory) / "provider.dylib"
            contents = b"synthetic-test-file-not-a-dylib"
            path.write_bytes(contents)
            digest = hashlib.sha256(contents).hexdigest()
            with mock.patch("darwin_native_provider.ctypes.CDLL", return_value=library) as loader:
                provider = DarwinKernProcAllProvider(path, digest)
            loader.assert_called_once_with(str(path), use_errno=True)
            self.assertEqual(provider._library_sha256, digest)
            self.assertFalse(provider._test_only_injection)

    def test_wrong_hash_fails_before_loader(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            path = Path(directory) / "provider.dylib"
            path.write_bytes(b"not-a-dylib")
            with mock.patch("darwin_native_provider.ctypes.CDLL") as loader:
                with self.assertRaises(DarwinNativeProviderError) as raised:
                    DarwinKernProcAllProvider(path, "0" * 64)
            loader.assert_not_called()
            self.assertEqual(raised.exception.diagnostic["stage"], "library-hash-mismatch")

    def test_library_hashing_rejects_symlinked_ancestor_before_loader(self):
        library = FakeLibrary([])
        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            root = Path(directory)
            real_parent = root / "real-parent"
            real_parent.mkdir()
            path = real_parent / "provider.dylib"
            contents = b"synthetic-file-not-loaded"
            path.write_bytes(contents)
            alias_parent = root / "alias-parent"
            alias_parent.symlink_to(real_parent, target_is_directory=True)
            alias_path = alias_parent / "provider.dylib"
            digest = hashlib.sha256(contents).hexdigest()
            with mock.patch("darwin_native_provider.ctypes.CDLL", return_value=library) as loader:
                with self.assertRaises(DarwinNativeProviderError) as raised:
                    DarwinKernProcAllProvider(alias_path, digest)
            loader.assert_not_called()
            self.assertEqual(raised.exception.diagnostic["stage"], "library-stat")
            self.assertIn("symlink component", str(raised.exception))

    def test_relative_library_path_is_rejected(self):
        with self.assertRaises(DarwinNativeProviderError) as raised:
            DarwinKernProcAllProvider("provider.dylib", "0" * 64)
        self.assertEqual(raised.exception.diagnostic["stage"], "library-binding")

    def test_non_string_hash_pin_is_rejected_before_path_access(self):
        with self.assertRaises(DarwinNativeProviderError) as raised:
            DarwinKernProcAllProvider("/not-opened/provider.dylib", None)
        self.assertEqual(raised.exception.diagnostic["stage"], "library-binding")

    def test_abi_version_mismatch_fails_during_binding(self):
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(FakeLibrary(version=ABI_VERSION + 1))
        self.assertEqual(raised.exception.diagnostic["stage"], "abi-check")

    def test_abi_capacity_mismatch_fails_during_binding(self):
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(FakeLibrary(max_rows=MAX_ROWS - 1))
        self.assertEqual(raised.exception.diagnostic["stage"], "abi-check")

    def test_malformed_meta_size_fails_closed(self):
        library = FakeLibrary([])
        original = library.dfb_native_meta_size
        library.dfb_native_meta_size = StubFunction(lambda: ctypes.sizeof(NativeMetaV2) + 8)
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library)
        self.assertEqual(raised.exception.diagnostic["stage"], "abi-check")
        library.dfb_native_meta_size = original

    def test_provider_statuses_fail_closed_without_decoding_partial_rows(self):
        failures = [
            (3, 1, 1, "first-kern-proc-all-failed"),
            (4, 1, 0, "first-kern-proc-all-capacity-exceeded"),
            (5, 1, 0, "first-kern-proc-all-record-alignment-invalid"),
            (7, 4, 0, "first-kern-proc-all-duplicate-pid"),
            (8, 2, 1, "proc-pidpath-failed"),
            (14, 3, 0, "revalidation-pid-missing"),
            (15, 3, 0, "revalidation-identity-changed"),
        ]
        for status, api, errno_value, expected_name in failures:
            with self.subTest(status=status):
                library = FakeLibrary(
                    [{"pid": 1234, "command": b"partial"}],
                    status=status,
                    api=api,
                    errno_value=errno_value,
                )
                with self.assertRaises(DarwinNativeProviderError) as raised:
                    self.provider(library).native_table()
                self.assertEqual(raised.exception.diagnostic["status"], expected_name)
                self.assertEqual(raised.exception.diagnostic["error_errno"], errno_value)

    def test_success_at_fixed_table_capacity_is_rejected_as_ambiguous(self):
        library = FakeLibrary(
            [], first_record_count=MAX_ROWS, second_record_count=MAX_ROWS
        )
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("inconsistent complete-coverage metadata", str(raised.exception))

    def test_second_table_at_fixed_capacity_fails_closed(self):
        library = FakeLibrary(
            [{"pid": 101}],
            first_record_count=1,
            second_record_count=MAX_ROWS,
            revalidated_count=1,
        )
        with self.assertRaisesRegex(DarwinNativeProviderError, "inconsistent complete-coverage"):
            self.provider(library).native_table()

    def test_duplicate_pid_in_success_payload_is_rejected(self):
        library = FakeLibrary([{"pid": 101}, {"pid": 101}])
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("duplicate row", str(raised.exception))

    def test_birth_microseconds_out_of_range_is_rejected(self):
        library = FakeLibrary([{"pid": 101, "birth_microseconds": 1_000_000}])
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("malformed or duplicate row", str(raised.exception))

    def test_invalid_utf8_command_is_rejected(self):
        library = FakeLibrary([{"pid": 101, "command": b"/bin/\xff"}])
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("not valid UTF-8", str(raised.exception))

    def test_command_without_terminator_is_rejected(self):
        library = FakeLibrary([{"pid": 101, "command": b"/bin/x"}])

        def unterminated(output, capacity, meta_pointer):
            result = library._snapshot(output, capacity, meta_pointer)
            row = output[0]
            ctypes.memset(
                ctypes.addressof(row) + NativeRowV3.command.offset + row.command_length,
                ord("x"),
                1,
            )
            return result

        library.dfb_native_snapshot_v3 = StubFunction(unterminated)
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("invalid termination", str(raised.exception))

    def test_short_comm_fallback_respects_exported_bound(self):
        library = FakeLibrary(
            [{"pid": 101, "command_source": COMMAND_SOURCE_KINFO_P_COMM,
              "command": b"x" * 17}]
        )
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("short command fallback exceeds", str(raised.exception))

    def test_success_with_inconsistent_table_byte_count_fails_closed(self):
        library = FakeLibrary([{"pid": 101}], record_size=648)
        original = library.dfb_native_snapshot_v3

        def wrong_bytes(output, capacity, meta_pointer):
            result = original(output, capacity, meta_pointer)
            meta = ctypes.cast(meta_pointer, ctypes.POINTER(NativeMetaV2)).contents
            meta.first_bytes += 1
            return result

        library.dfb_native_snapshot_v3 = StubFunction(wrong_bytes)
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("inconsistent complete-coverage metadata", str(raised.exception))

    def test_success_with_inconsistent_table_capacity_fails_closed(self):
        library = FakeLibrary([{"pid": 101}], record_size=648)
        original = library.dfb_native_snapshot_v3

        def wrong_capacity(output, capacity, meta_pointer):
            result = original(output, capacity, meta_pointer)
            meta = ctypes.cast(meta_pointer, ctypes.POINTER(NativeMetaV2)).contents
            meta.table_capacity_bytes -= 648
            return result

        library.dfb_native_snapshot_v3 = StubFunction(wrong_capacity)
        with self.assertRaises(DarwinNativeProviderError) as raised:
            self.provider(library).native_table()
        self.assertIn("inconsistent complete-coverage metadata", str(raised.exception))

    def test_deadline_is_checked_before_native_call(self):
        library = FakeLibrary([])
        provider = self.provider(library)
        provider._deadline = 0.0
        with self.assertRaises(DarwinNativeProviderError) as raised:
            provider.native_table()
        self.assertTrue(raised.exception.diagnostic["deadline_exceeded"])
        self.assertEqual(library.snapshot_calls, 0)

    def test_deadline_is_checked_after_native_call(self):
        library = FakeLibrary([])
        provider = self.provider(library)
        provider._deadline = 10.0
        with mock.patch("darwin_native_provider.time.monotonic", side_effect=[5.0, 11.0]):
            with self.assertRaises(DarwinNativeProviderError) as raised:
                provider.native_table()
        self.assertTrue(raised.exception.diagnostic["deadline_exceeded"])
        self.assertEqual(library.snapshot_calls, 1)

    def test_known_status_names_are_stable_for_handoff(self):
        self.assertEqual(STATUS_NAMES[4], "first-kern-proc-all-capacity-exceeded")
        self.assertEqual(STATUS_NAMES[15], "revalidation-identity-changed")


if __name__ == "__main__":
    unittest.main()
