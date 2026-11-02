"""Synthetic policy checks for ABI4 first-table-only history observations."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

import process_reconciliation as pr


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EXECUTOR_PATH = ROOT / "scripts/execute-release-v092.py"
CONTROLLER_PATH = ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py"
PROCESS_PATH = ROOT / "scripts/swift_v2_process.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EXECUTOR = _load("controls10_test_executor", EXECUTOR_PATH)
CONTROLLER = _load("controls10_test_controller", CONTROLLER_PATH)
PROCESS = _load("controls10_test_process", PROCESS_PATH)


def _native_row(pid: int, *, origin: str = "first-table", birth: str = "100:12345",
                source: str | None = None) -> dict:
    source = source or (
        "sysctl_kern_proc_all.first_table_only.p_comm"
        if origin == "first-table-only" else "proc_pidpath"
    )
    if origin == "first-table-only":
        path_status, path_errno, witness, kernel_comm = (
            "discarded-unrevalidated-first-table-only", 3,
            "first-table-only-unverified", True
        )
    elif source == "proc_pidpath":
        path_status, path_errno, witness, kernel_comm = "resolved", 0, "matched-in-second-table", False
    else:
        path_status, path_errno, witness, kernel_comm = (
            "short-comm-fallback", 0, "matched-in-second-table", True
        )
    command = "python3" if origin == "first-table-only" else "/usr/bin/python3"
    return {
        "pid": pid, "ppid": 1, "birth_identity": birth, "state": "S",
        "command": command, "command_executable": command,
        "command_name": Path(command).name, "command_source": source,
        "command_source_is_kernel_comm": kernel_comm,
        "command_path_status": path_status, "command_path_errno": path_errno,
        "native_snapshot_origin": origin,
        "revalidation_witness": witness,
        "command_arguments_available": False,
    }


def _command_row(pid: int) -> dict:
    row = {
        "pid": pid, "cpu_percent": 25.0, "comm": "python3",
        "args": "/usr/bin/python3", "raw_row": f"{pid} 25.0 python3 /usr/bin/python3",
        "command": "/usr/bin/python3", "command_executable": "/usr/bin/python3",
        "command_name": "python3", "command_source": "ps-argv",
        "command_arguments_available": True, "kernel_pid0": False,
    }
    return row


def _provider_child() -> dict:
    return {
        "provider_identity": pr.PS_V1_IDENTITY, "pid": 1235,
        "started_utc": "2026-10-26T00:00:02+00:00",
        "ended_utc": "2026-10-26T00:00:03+00:00",
        "started_monotonic": 2.1, "ended_monotonic": 2.4,
        "returncode": 0, "kill_requested": False, "reaped": True,
        "cleanup_incomplete": False, "direct_child_only": True,
        "descendant_containment": "direct-child-reaped",
    }


def _abi4_snapshot(name: str, rows: list[dict], start: float, end: float) -> dict:
    stable = [row for row in rows if row["native_snapshot_origin"] == "first-table"]
    first_only = [row for row in rows if row["native_snapshot_origin"] == "first-table-only"]
    second_only = [row for row in rows if row["native_snapshot_origin"] == "second-table-only"]
    first_pid0 = second_pid0 = 0
    first_raw = len(stable) + len(first_only) + first_pid0
    second_raw = len(stable) + len(second_only) + second_pid0
    evidence = {
        "identity": pr.ABI4_NATIVE_PROVIDER_IDENTITY,
        "abi_version": 4,
        "library_sha256": pr.ABI4_PROVIDER_LIBRARY_SHA256,
        "test_only_injected_library": False,
        "first_table_sysctl_calls": 1,
        "revalidation_table_sysctl_calls": 1,
        "first_snapshot_record_count": first_raw,
        "second_snapshot_record_count": second_raw,
        "first_snapshot_excluded_pid0_count": first_pid0,
        "second_snapshot_excluded_pid0_count": second_pid0,
        "revalidated_first_row_count": len(stable),
        "first_table_only_pid_count": len(first_only),
        "first_table_only_output_row_count": len(first_only),
        "additional_second_snapshot_pid_count": len(second_only),
        "second_table_only_output_row_count": len(second_only),
        "output_row_count": len(rows),
        "historical_absence_claim": False,
        "scope": "One first table and one revalidation table; provider-scoped observations only.",
        "module_source_path": pr.ABI4_PROVIDER_MODULE_PATH,
        "module_source_sha256": pr.ABI4_PROVIDER_MODULE_SHA256,
        "library_path": pr.ABI4_PROVIDER_LIBRARY_PATH,
    }
    return {
        "name": name, "provider_identity": pr.ABI4_NATIVE_PROVIDER_IDENTITY,
        "provider_scope": "local Darwin provider, not OS-global",
        "started_utc": f"2026-10-26T00:00:0{int(start)}+00:00",
        "ended_utc": f"2026-10-26T00:00:0{int(end)}+00:00",
        "started_monotonic": start, "ended_monotonic": end,
        "complete": True, "truncated": False, "error": None, "rows": rows,
        "coverage": {
            "enumeration": "synthetic ABI4 test fixture",
            "enumerated_pid_count": first_raw + len(second_only),
            "returned_pid_count": len(rows),
            "pid_capacity": pr.ABI4_MAX_ROWS_PER_TABLE,
            "truncated": False, "coverage_errors": [],
            "excluded_pid0_kernel_entries": first_pid0,
            "required_fields": ["pid", "ppid", "birth_identity", "state", "command"],
            "provider_evidence": evidence,
        },
    }


def _command_snapshot(rows: list[dict]) -> dict:
    child = _provider_child()
    table = "\n".join(row["raw_row"] for row in rows) + ("\n" if rows else "")
    return {
        "name": "command", "provider_identity": pr.PS_V1_IDENTITY,
        "provider_scope": "local ps provider, not OS-global",
        "started_utc": "2026-10-26T00:00:02+00:00",
        "ended_utc": "2026-10-26T00:00:03+00:00",
        "started_monotonic": 2.0, "ended_monotonic": 3.0,
        "complete": True, "truncated": False, "error": None, "rows": rows,
        "table": table,
        "coverage": {
            "enumeration": "synthetic ps fixture", "enumerated_pid_count": len(rows),
            "returned_pid_count": len(rows), "truncated": False,
            "coverage_errors": [], "excluded_pid0_kernel_entries": 0,
            "kernel_pid0_rows_observed": 0,
            "required_fields": ["pid", "cpu_percent", "comm", "args", "command"],
            "provider_child": child,
        },
    }


def _query(before: list[dict] | None = None, command: list[dict] | None = None,
           after: list[dict] | None = None) -> dict:
    before = [] if before is None else before
    command = [] if command is None else command
    after = [] if after is None else after
    child = _provider_child()
    child["pid"] = 1234
    snapshots = [
        _abi4_snapshot("native-before", before, 1.0, 1.5),
        _command_snapshot(command),
        _abi4_snapshot("native-after", after, 3.5, 4.0),
    ]
    return {
        "schema": "v092-monitor06-reconciliation-query/v1",
        "provider_identity": "monitor06-native-command-native/v1",
        "started_utc": "2026-10-26T00:00:00+00:00", "started_monotonic": 0.5,
        "ended_utc": "2026-10-26T00:00:04+00:00", "ended_monotonic": 4.5,
        "deadline_monotonic": 5.0, "provider_deadline_monotonic": 4.9,
        "duration_limit_seconds": 4.4,
        "darwin_native_provider_binding": {
            "schema": pr.ABI4_NATIVE_BINDING_SCHEMA,
            "module_source_path": pr.ABI4_PROVIDER_MODULE_PATH,
            "module_source_sha256": pr.ABI4_PROVIDER_MODULE_SHA256,
            "library_path": pr.ABI4_PROVIDER_LIBRARY_PATH,
            "library_sha256": pr.ABI4_PROVIDER_LIBRARY_SHA256,
        },
        "snapshots": snapshots,
        "outcome": {"status": "complete-provider-scoped", "complete": True,
                    "order_valid": True, "error": None},
        "query_child": {"pid": 1234, "returncode": 0, "kill_requested": False,
                        "reaped": True, "cleanup_incomplete": False,
                        "direct_child_only": True,
                        "descendant_containment": "query-and-provider-children-reaped"},
        "provider_children": [_provider_child()],
        "os_global_completeness_claim": False, "continuous_absence_claim": False,
    }


class ReconciliationBoundedSetPolicyTests(unittest.TestCase):
    def setUp(self):
        self.descendant_calls = []
        self.executor = types.SimpleNamespace(_contenders=lambda _table: [])
        self.controller = types.SimpleNamespace(_hashed_bifrost_contenders=lambda _table: [])

    def _evaluate(self, query: dict, *, candidates=None, tracked=None, deadline=5.0):
        tracked = {} if tracked is None else tracked

        def descendants(native, previous):
            self.descendant_calls.append((dict(native), dict(previous)))
            return dict(previous)

        proc = types.SimpleNamespace(descendants=descendants)
        return pr.evaluate_reconciliation(
            query, [] if candidates is None else candidates, deadline=deadline,
            executor=self.executor, controller=self.controller, proc=proc, tracked=tracked,
        )

    def test_exact_abi4_source_library_and_counts_validate(self):
        query = _query(before=[_native_row(700, origin="first-table-only")])
        pr.validate_query_result(query, deadline=5.0)
        self.assertEqual(query["snapshots"][0]["coverage"]["provider_evidence"]["output_row_count"], 1)

    def test_abi4_source_library_binding_is_exact_and_case_sensitive(self):
        for field, value in (
            ("module_source_sha256", "0" * 64),
            ("library_path", pr.ABI4_PROVIDER_LIBRARY_PATH + ".copy"),
            ("library_sha256", "A" + pr.ABI4_PROVIDER_LIBRARY_SHA256[1:]),
        ):
            with self.subTest(field=field):
                query = _query(before=[_native_row(700, origin="first-table-only")])
                query["darwin_native_provider_binding"][field] = value
                with self.assertRaises(pr.ReconciliationError):
                    pr.validate_query_result(query, deadline=5.0)

    def test_abi4_row_provenance_and_count_equations_are_strict(self):
        bad_row = _native_row(700, origin="first-table-only")
        bad_row["revalidation_witness"] = "matched-in-second-table"
        old_unattempted_status = _native_row(700, origin="first-table-only")
        old_unattempted_status["command_path_status"] = "not-attempted-first-table-only"
        missing_path_errno = _native_row(700, origin="first-table-only")
        missing_path_errno["command_path_errno"] = None
        negative_path_errno = _native_row(700, origin="first-table-only")
        negative_path_errno["command_path_errno"] = -1
        bad_count = _query(before=[_native_row(700, origin="first-table-only")])
        bad_count["snapshots"][0]["coverage"]["provider_evidence"]["first_snapshot_record_count"] = 2
        extra_evidence = _query(before=[_native_row(700, origin="first-table-only")])
        extra_evidence["snapshots"][0]["coverage"]["provider_evidence"]["unexpected"] = True
        for query in (
            _query(before=[bad_row]),
            _query(before=[old_unattempted_status]),
            _query(before=[missing_path_errno]),
            _query(before=[negative_path_errno]),
            bad_count, extra_evidence,
        ):
            with self.subTest(rows=query["snapshots"][0]["rows"]):
                with self.assertRaises(pr.ReconciliationError):
                    pr.validate_query_result(query, deadline=5.0)

    def test_abi4_per_snapshot_count_bounds_are_exclusive_with_outer_aggregate_separate(self):
        self.assertEqual(pr.ABI4_MAX_OUTPUT_ROWS, 8192)
        self.assertEqual(pr.ABI4_MAX_OUTER_NATIVE_ROWS, 16384)
        for field in (
            "first_snapshot_record_count", "second_snapshot_record_count", "output_row_count"
        ):
            with self.subTest(valid_boundary=field):
                self.assertEqual(
                    pr._bounded_abi4_count(8191, field, upper_exclusive=8192), 8191
                )

        forged_values = (
            ("first_snapshot_record_count", 8192),
            ("second_snapshot_record_count", 8192),
            ("output_row_count", 8192),
            ("output_row_count", 8193),
            ("output_row_count", 16384),
        )
        for field, value in forged_values:
            with self.subTest(field=field, value=value):
                query = _query(before=[_native_row(700, origin="first-table-only")])
                query["snapshots"][0]["coverage"]["provider_evidence"][field] = value
                with self.assertRaisesRegex(pr.ReconciliationError, "count is missing or out of bounds"):
                    pr.validate_query_result(query, deadline=5.0)

    def test_single_before_and_after_first_only_rows_are_history_only(self):
        for origin in ("native-before", "native-after"):
            with self.subTest(origin=origin):
                row = _native_row(700, origin="first-table-only")
                query = _query(before=[row] if origin == "native-before" else None,
                               after=[row] if origin == "native-after" else None)
                result = self._evaluate(query, tracked={900: "900:12"})
                self.assertEqual(result["status"],
                                 "historical-absence-with-unresolved-intrasnapshot-observations")
                self.assertEqual(len(result["historical_only_intrasnapshot_rows"]), 1)
                event = result["historical_only_intrasnapshot_rows"][0]
                self.assertEqual(event["pid"], 700)
                record = event["row"]
                self.assertEqual(record["status"],
                                 "unresolved_historical_intrasnapshot_disappearance")
                self.assertEqual(record["source_row"]["native_snapshot_origin"], "first-table-only")
                self.assertEqual(record["historical_ownership"], "unknown")
                self.assertEqual(record["historical_foreignness"], "unknown")
                self.assertEqual(record["workload_relevance"], "unknown")
                self.assertEqual(record["exact_exit_time"], "unknown")
                self.assertFalse(record["current_map_eligible"])
                self.assertFalse(record["argv_bridge_allowed"])
                self.assertFalse(record["absence_evidence"]["continuous_absence_claim"])
                self.assertFalse(record["absence_evidence"]["os_global_absence_claim"])
                self.assertNotIn(700, result["tracked_after"])
                self.assertFalse(result["fresh_contenders"])

    def test_original_candidate_first_only_presence_fails_and_preserves_raw_observation(self):
        row = _native_row(601, origin="first-table-only")
        result = self._evaluate(
            _query(before=[row]), candidates=[{"pid": 601, "row": "601 java", "native": None}]
        )
        self.assertEqual(result["status"], "candidate-present-fail-closed")
        self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual(result["rejected_intrasnapshot_observations"][0]["row"], row)
        self.assertEqual(self.descendant_calls, [])

    def test_tracked_pid_intersection_ignores_birth_and_precedes_descendant_update(self):
        for existing_birth in ("100:12345", "900:54321"):
            with self.subTest(existing_birth=existing_birth):
                row = _native_row(700, origin="first-table-only", birth="100:12345")
                result = self._evaluate(_query(before=[row]), tracked={700: existing_birth})
                self.assertEqual(result["status"],
                                 "intrasnapshot-first-only-tracked-pid-fail-closed")
                self.assertEqual(result["tracked_after"], {700: existing_birth})
                self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
                self.assertEqual(self.descendant_calls, [])

    def test_command_or_other_native_presence_by_pid_fails_even_with_different_birth(self):
        only_row = _native_row(700, origin="first-table-only", birth="100:12345")
        stable_other = _native_row(700, origin="first-table", birth="200:54321")
        cases = (
            _query(before=[only_row], command=[_command_row(700)]),
            _query(before=[only_row], after=[stable_other]),
            _query(before=[stable_other], after=[only_row]),
        )
        for query in cases:
            with self.subTest(query=query):
                result = self._evaluate(query)
                self.assertEqual(result["status"],
                                 "intrasnapshot-first-only-cross-snapshot-presence-fail-closed")
                self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
                self.assertEqual(len(result["rejected_intrasnapshot_observations"]), 1)
                self.assertEqual(self.descendant_calls, [])

    def test_multiple_distinct_first_only_rows_across_both_tables_are_collected_as_one_set(self):
        query = _query(
            before=[
                _native_row(700, origin="first-table-only"),
                _native_row(701, origin="first-table-only", birth="101:12345"),
            ],
            after=[_native_row(702, origin="first-table-only", birth="102:12345")],
        )
        tracked = {900: "900:12"}
        result = self._evaluate(query, tracked=tracked)
        self.assertEqual(
            result["status"],
            "historical-absence-with-unresolved-intrasnapshot-observations",
        )
        events = result["historical_only_intrasnapshot_rows"]
        self.assertEqual([event["pid"] for event in events], [700, 701, 702])
        self.assertEqual(len(self.descendant_calls), 1)
        self.assertEqual(result["tracked_after"], tracked)
        for event in events:
            record = event["row"]
            self.assertEqual(
                record["status"], "unresolved_historical_intrasnapshot_disappearance"
            )
            self.assertTrue(record["absence_evidence"]["first_table_present"])
            self.assertTrue(record["absence_evidence"]["same_observation_second_table_absent"])
            self.assertTrue(record["absence_evidence"]["command_snapshot_absent_by_pid"])
            self.assertTrue(record["absence_evidence"]["other_native_observation_absent_by_pid"])
            self.assertFalse(record["absence_evidence"]["continuous_absence_claim"])
            self.assertFalse(record["absence_evidence"]["os_global_absence_claim"])
            self.assertEqual(record["historical_ownership"], "unknown")
            self.assertEqual(record["historical_foreignness"], "unknown")
            self.assertEqual(record["workload_relevance"], "unknown")
            self.assertEqual(record["exact_exit_time"], "unknown")
            self.assertFalse(record["current_map_eligible"])
            self.assertFalse(record["argv_bridge_allowed"])
            self.assertNotIn(event["pid"], result["tracked_after"])
        self.assertEqual(result["rejected_intrasnapshot_observations"], [])

    def test_multiple_first_only_rows_in_one_observation_are_collected_without_subset_selection(self):
        query = _query(before=[
            _native_row(700, origin="first-table-only"),
            _native_row(701, origin="first-table-only"),
        ])
        result = self._evaluate(query)
        self.assertEqual(
            result["status"],
            "historical-absence-with-unresolved-intrasnapshot-observations",
        )
        self.assertEqual([row["pid"] for row in result["historical_only_intrasnapshot_rows"]],
                         [700, 701])
        self.assertEqual(result["rejected_intrasnapshot_observations"], [])
        self.assertEqual(len(self.descendant_calls), 1)

    def test_same_pid_first_only_in_both_outer_observations_counts_twice(self):
        query = _query(
            before=[_native_row(700, origin="first-table-only", birth="100:12345")],
            after=[_native_row(700, origin="first-table-only", birth="999:54321")],
        )
        result = self._evaluate(query)
        self.assertEqual(
            result["status"],
            "intrasnapshot-first-only-cross-snapshot-presence-fail-closed",
        )
        self.assertEqual(len(result["rejected_intrasnapshot_observations"]), 2)

    def test_last_set_member_candidate_or_tracked_intersection_rejects_all_before_descendants(self):
        rows = [
            _native_row(700, origin="first-table-only"),
            _native_row(701, origin="first-table-only", birth="101:12345"),
        ]
        candidate_result = self._evaluate(
            _query(before=rows), candidates=[{"pid": 701, "row": "701 java", "native": None}]
        )
        self.assertEqual(candidate_result["status"], "candidate-present-fail-closed")
        self.assertEqual(candidate_result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in candidate_result[
            "rejected_intrasnapshot_observations"]], [700, 701])
        self.assertEqual(self.descendant_calls, [])

        self.descendant_calls.clear()
        tracked_result = self._evaluate(
            _query(before=rows), tracked={701: "different-birth:still-same-pid"}
        )
        self.assertEqual(
            tracked_result["status"], "intrasnapshot-first-only-tracked-pid-fail-closed"
        )
        self.assertEqual(tracked_result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in tracked_result[
            "rejected_intrasnapshot_observations"]], [700, 701])
        self.assertEqual(tracked_result["tracked_after"], {701: "different-birth:still-same-pid"})
        self.assertEqual(self.descendant_calls, [])

    def test_last_set_member_command_or_other_native_overlap_rejects_every_row(self):
        first_only = [
            _native_row(700, origin="first-table-only"),
            _native_row(701, origin="first-table-only", birth="101:12345"),
        ]
        command_result = self._evaluate(_query(before=first_only,
                                               command=[_command_row(701)]))
        self.assertEqual(
            command_result["status"],
            "intrasnapshot-first-only-cross-snapshot-presence-fail-closed",
        )
        self.assertEqual(command_result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in command_result[
            "rejected_intrasnapshot_observations"]], [700, 701])
        self.assertEqual(self.descendant_calls, [])

        self.descendant_calls.clear()
        other_native_result = self._evaluate(_query(
            before=first_only,
            after=[_native_row(701, origin="first-table", birth="999:54321")],
        ))
        self.assertEqual(
            other_native_result["status"],
            "intrasnapshot-first-only-cross-snapshot-presence-fail-closed",
        )
        self.assertEqual(other_native_result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in other_native_result[
            "rejected_intrasnapshot_observations"]], [700, 701])
        self.assertEqual(self.descendant_calls, [])

    def test_last_malformed_member_and_duplicate_pid_reject_without_partial_history(self):
        malformed = _native_row(701, origin="first-table-only", birth="101:12345")
        malformed["command_path_status"] = "not-attempted-first-table-only"
        malformed_query = _query(before=[
            _native_row(700, origin="first-table-only"), malformed,
        ])
        result = self._evaluate(malformed_query)
        self.assertEqual(result["status"], "incomplete-fail-closed")
        self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in result["query"]["snapshots"][0]["rows"]],
                         [700, 701])
        self.assertEqual(self.descendant_calls, [])

        duplicate_query = _query(before=[
            _native_row(700, origin="first-table-only"),
            _native_row(700, origin="first-table-only", birth="101:12345"),
        ])
        duplicate_result = self._evaluate(duplicate_query)
        self.assertEqual(duplicate_result["status"], "incomplete-fail-closed")
        self.assertEqual(duplicate_result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual(len(duplicate_result["query"]["snapshots"][0]["rows"]), 2)
        self.assertEqual(self.descendant_calls, [])

    def test_bad_deadline_provider_error_and_capacity_near_misses_preserve_no_history(self):
        baseline = _query(before=[_native_row(700, origin="first-table-only")])
        for label, mutate, deadline in (
            ("deadline", lambda query: None, 3.9),
            ("provider error", lambda query: query["snapshots"][0].update(error={"type": "EIO"}), 5.0),
            ("capacity", lambda query: query["snapshots"][0]["coverage"][
                "provider_evidence"].update(first_snapshot_record_count=8192), 5.0),
        ):
            with self.subTest(label=label):
                query = json.loads(json.dumps(baseline))
                mutate(query)
                result = self._evaluate(query, tracked={900: "900:12"}, deadline=deadline)
                self.assertEqual(result["status"], "incomplete-fail-closed")
                self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
                self.assertEqual(result["tracked_after"], {900: "900:12"})
                self.assertEqual(self.descendant_calls, [])
                self.descendant_calls.clear()

    def test_failed_fresh_contender_status_does_not_carry_history_records(self):
        query = _query(
            before=[
                _native_row(700, origin="first-table-only"),
                _native_row(701, origin="first-table-only", birth="101:12345"),
            ],
            command=[_command_row(800)],
        )
        self.executor._contenders = lambda _table: ["800 100.0 python3 /usr/bin/python3"]
        result = self._evaluate(query)
        self.assertEqual(result["status"], "fresh-contender-fail-closed")
        self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual([row["pid"] for row in result[
            "rejected_intrasnapshot_observations"]], [700, 701])
        self.assertTrue(all(row["rejection_reason"] == "fresh-contender-also-present"
                            for row in result["rejected_intrasnapshot_observations"]))

    def test_stable_kernel_comm_fallback_remains_fail_closed(self):
        before = _native_row(700, origin="first-table", source="sysctl_kern_proc_all.p_comm")
        after = _native_row(700, origin="first-table", source="sysctl_kern_proc_all.p_comm")
        query = _query(before=[before], after=[after])
        result = self._evaluate(query)
        self.assertEqual(result["status"], "fresh-contender-fail-closed")
        self.assertEqual(result["fresh_contenders"][0]["status"],
                         "kernel-comm-fallback-unbridged-fail-closed")
        self.assertEqual(result["historical_only_intrasnapshot_rows"], [])

    def test_incomplete_query_remains_fail_closed_without_history_or_map_change(self):
        query = _query(before=[_native_row(700, origin="first-table-only")])
        query["outcome"]["complete"] = False
        tracked = {900: "900:1"}
        result = self._evaluate(query, tracked=tracked)
        self.assertEqual(result["status"], "incomplete-fail-closed")
        self.assertEqual(result["historical_only_intrasnapshot_rows"], [])
        self.assertEqual(result["tracked_after"], tracked)
        self.assertEqual(self.descendant_calls, [])

    def test_abi3_history_query_remains_accepted_without_abi4_binding(self):
        row = {
            "pid": 700, "ppid": 1, "birth_identity": "100:12345", "state": "S",
            "command": "/usr/bin/python3", "command_executable": "/usr/bin/python3",
            "command_name": "python3", "command_source": "proc_pidpath",
            "command_source_is_kernel_comm": False, "command_path_status": "resolved",
            "command_path_errno": 0, "native_snapshot_origin": "first-table",
            "revalidation_witness": "matched-in-second-table",
            "command_arguments_available": False,
        }
        query = _query()
        for index, name, start, end in ((0, "native-before", 1.0, 1.5),
                                        (2, "native-after", 3.5, 4.0)):
            snapshot = _abi4_snapshot(name, [row], start, end)
            snapshot["provider_identity"] = pr.ABI3_NATIVE_PROVIDER_IDENTITY
            evidence = snapshot["coverage"]["provider_evidence"]
            snapshot["coverage"]["provider_evidence"] = {
                "identity": pr.ABI3_NATIVE_PROVIDER_IDENTITY, "abi_version": 3,
                "library_sha256": "a" * 64, "test_only_injected_library": False,
                "module_source_path": "/private/tmp/provider.py",
                "module_source_sha256": "b" * 64,
                "library_path": "/private/tmp/provider.dylib",
                "first_table_sysctl_calls": 1, "revalidation_table_sysctl_calls": 1,
                "revalidated_first_row_count": 1,
                "second_snapshot_record_count": 1,
                "first_snapshot_excluded_pid0_count": 0,
                "second_snapshot_excluded_pid0_count": 0,
                "additional_second_snapshot_pid_count": 0,
                "second_table_only_output_row_count": 0,
                "historical_absence_claim": False,
                "scope": "ABI3 historical fixture",
            }
            snapshot["coverage"].update({
                "enumerated_pid_count": 1, "returned_pid_count": 1,
                "excluded_pid0_kernel_entries": 0,
            })
            query["snapshots"][index] = snapshot
        query.pop("darwin_native_provider_binding")
        pr.validate_query_result(query, deadline=5.0)
        query["snapshots"][0]["rows"][0]["native_snapshot_origin"] = "first-table-only"
        with self.assertRaises(pr.ReconciliationError):
            pr.validate_query_result(query, deadline=5.0)


if __name__ == "__main__":
    unittest.main()
