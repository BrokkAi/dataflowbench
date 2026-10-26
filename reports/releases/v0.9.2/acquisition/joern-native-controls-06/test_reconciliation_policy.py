"""Focused policy regressions for the private monitor06 prototype."""
import base64
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import types
import unittest
from unittest import mock

import native_qualifier as n
import process_reconciliation as pr
import snapshot_query


PROVIDER = "fake-native-provider/v1"


def native_row(pid, ppid=1, birth="birth", command="/usr/bin/python3", state="S"):
    return {"pid": pid, "ppid": ppid, "birth_identity": birth, "state": state,
            "command": command, "command_executable": command,
            "command_name": Path(command).name,
            "command_source": "fake-native-command", "command_arguments_available": False}


def command_row(pid, command="/usr/bin/python3", *, cpu=100.0, comm=None, args=None):
    args = command if args is None else args
    executable = args.split(None, 1)[0]
    name = Path(executable).name
    comm = name if comm is None else comm
    raw = f"{pid} {cpu} {comm} {args}"
    return {"pid": pid, "cpu_percent": cpu, "comm": comm, "args": args,
            "raw_row": raw, "command": args, "command_executable": executable,
            "command_name": name, "command_source": "ps-argv",
            "command_arguments_available": True, "kernel_pid0": pid == 0}


def snapshot(name, rows, start, end, *, native=True, complete=True, truncated=False,
             error=None, omit=(), table=None):
    coverage = {"enumeration": "fake-provider", "enumerated_pid_count": len(rows),
                "returned_pid_count": len(rows), "truncated": truncated,
                "coverage_errors": [], "excluded_pid0_kernel_entries": 0,
                "required_fields": ["pid", "ppid", "birth_identity", "state", "command"] if native else ["pid", "command"]}
    value = {"name": name, "provider_identity": PROVIDER,
             "provider_scope": "local fake provider; not OS-global proof",
             "started_utc": f"2026-10-26T00:00:0{int(start)}+00:00",
             "ended_utc": f"2026-10-26T00:00:0{int(end)}+00:00",
             "started_monotonic": start, "ended_monotonic": end,
             "complete": complete, "truncated": truncated,
             "error": error, "coverage": coverage, "rows": rows}
    if not native:
        value["provider_identity"] = "ps-axo-pid-percentcpu-comm-args/v1"
        coverage["kernel_pid0_rows_observed"] = sum(row["pid"] == 0 for row in rows)
        coverage["required_fields"] = ["pid", "cpu_percent", "comm", "args", "command"]
        coverage["provider_child"] = {
            "provider_identity": "ps-axo-pid-percentcpu-comm-args/v1", "pid": 1235,
            "started_utc": "2026-10-26T00:00:02.1+00:00", "ended_utc": "2026-10-26T00:00:02.4+00:00",
            "started_monotonic": 2.1, "ended_monotonic": 2.4,
            "returncode": 0, "kill_requested": False, "reaped": True,
            "cleanup_incomplete": False, "direct_child_only": True,
            "descendant_containment": "direct-child-reaped"}
        value["table"] = table if table is not None else "\n".join(row["raw_row"] for row in rows) + ("\n" if rows else "")
    for field in omit:
        value.pop(field, None)
    return value


def query(native_before=None, command=None, native_after=None, *, outcome=True, end=4.5):
    native_before = [native_row(500)] if native_before is None else native_before
    command = [command_row(500)] if command is None else command
    native_after = [native_row(500)] if native_after is None else native_after
    snapshots = [
        snapshot("native-before", native_before, 1.0, 1.5),
        snapshot("command", command, 2.0, 2.5, native=False,
                 table="\n".join(row["raw_row"] for row in command) + ("\n" if command else "")),
        snapshot("native-after", native_after, 3.0, 3.5),
    ]
    return {"schema": "v092-monitor06-reconciliation-query/v1",
            "provider_identity": "monitor06-native-command-native/v1",
            "started_utc": "2026-10-26T00:00:00+00:00", "started_monotonic": 0.5,
            "ended_utc": "2026-10-26T00:00:04+00:00", "ended_monotonic": end,
            "snapshots": snapshots,
            "outcome": {"status": "complete-provider-scoped" if outcome else "provider-error",
                        "complete": outcome, "order_valid": True, "error": None},
            "query_child": {"pid": 1234, "returncode": 0, "kill_requested": False,
                            "reaped": True, "cleanup_incomplete": False,
                            "direct_child_only": True, "descendant_containment": "direct-child-reaped"},
            "provider_children": [{"pid": 1235, "provider_identity": "ps-axo-pid-percentcpu-comm-args/v1",
                                   "started_utc": "2026-10-26T00:00:02.1+00:00",
                                   "ended_utc": "2026-10-26T00:00:02.4+00:00",
                                   "started_monotonic": 2.1, "ended_monotonic": 2.4,
                                   "returncode": 0, "kill_requested": False,
                                   "reaped": True, "cleanup_incomplete": False,
                                   "direct_child_only": True, "descendant_containment": "direct-child-reaped"}],
            "os_global_completeness_claim": False, "continuous_absence_claim": False}


class ReconciliationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = n.ROOT / "scripts/execute-release-v092.py"
        spec = importlib.util.spec_from_file_location("monitor06_test_executor", path)
        cls.executor_source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.executor_source)
        path = n.ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py"
        spec = importlib.util.spec_from_file_location("monitor06_test_controller", path)
        cls.controller_source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.controller_source)
        path = n.ROOT / "scripts/swift_v2_process.py"
        spec = importlib.util.spec_from_file_location("monitor06_test_process", path)
        cls.process_source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.process_source)

    def evaluate(self, value, candidates=None):
        candidates = [{"pid": 601, "row": "601 80.0 java /usr/bin/java", "native": None}] if candidates is None else candidates
        executor = types.SimpleNamespace(_contenders=self.executor_source._contenders)
        controller = types.SimpleNamespace(_hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders)
        proc = types.SimpleNamespace(descendants=self.process_source.descendants)
        return pr.evaluate_reconciliation(value, candidates, deadline=5.0, executor=executor,
                                          controller=controller, proc=proc,
                                          tracked={500: "birth"})

    def test_vanished_historical_candidate_is_typed_and_never_owned(self):
        result = self.evaluate(query())
        self.assertEqual(result["status"], "historical-absence-observed-no-fresh-contender")
        self.assertEqual(result["candidate_outcomes"][0]["status"],
                         "unresolved_historical_absent_at_reconciliation")
        self.assertEqual(result["candidate_outcomes"][0]["historical_ownership"], "unknown")
        self.assertFalse(result["cleanup_authorized"])
        self.assertFalse(result["automatic_retry"])
        self.assertFalse(result["continuous_absence_claim"])

    def test_candidate_presence_in_each_fresh_table_fails_closed_including_pid_reuse(self):
        cases = (
            query(native_before=[native_row(601, birth="new-birth")]),
            query(command=[command_row(601, "/usr/bin/java")]),
            query(native_after=[native_row(601, birth="recycled-birth")]),
        )
        for result in cases:
            with self.subTest(names=[s["name"] for s in result["snapshots"]]):
                evaluated = self.evaluate(result)
                self.assertEqual(evaluated["status"], "candidate-present-fail-closed")
                self.assertEqual(evaluated["candidate_outcomes"][0]["status"],
                                 "candidate_present_in_fresh_snapshot_fail_closed")
                self.assertNotIn("retired_candidates", evaluated)

    def test_other_fresh_heavy_contender_stops_even_when_candidate_is_absent(self):
        result = self.evaluate(query(command=[command_row(500), command_row(777, "/usr/local/bin/joern")]))
        self.assertEqual(result["status"], "fresh-contender-fail-closed")
        self.assertEqual(result["fresh_contenders"][0]["pid"], 777)
        native_only = self.evaluate(query(native_before=[native_row(500), native_row(778, command="/usr/local/bin/joern")]))
        self.assertEqual(native_only["status"], "fresh-contender-fail-closed")
        self.assertEqual(native_only["fresh_contenders"][0]["pid"], 778)

    def test_actual_command_table_preserves_bifrost_mcp_cpu_and_hashed_rules(self):
        def run(pid, executable, cpu, args):
            command = command_row(pid, executable, cpu=cpu, args=args)
            before = [native_row(500), native_row(pid, ppid=1, birth=f"birth-{pid}", command=executable)]
            after = [native_row(500), native_row(pid, ppid=1, birth=f"birth-{pid}", command=executable)]
            return self.evaluate(query(native_before=before, command=[command], native_after=after))

        low_mcp = run(700, "/opt/bifrost/bifrost", 0.2, "/opt/bifrost/bifrost --mcp --stdio")
        self.assertEqual(low_mcp["status"], "historical-absence-observed-no-fresh-contender")
        high_mcp = run(701, "/opt/bifrost/bifrost", 4.2, "/opt/bifrost/bifrost --mcp --stdio")
        self.assertEqual(high_mcp["status"], "fresh-contender-fail-closed")
        self.assertEqual(high_mcp["fresh_contenders"][0]["pid"], 701)

        hashed = "/opt/bifrost/bin/bifrost-abcdef012345"
        low_hashed = run(702, hashed, 0.3, hashed + " --mcp")
        self.assertEqual(low_hashed["status"], "historical-absence-observed-no-fresh-contender")
        high_hashed = run(703, hashed, 2.0, hashed + " --mcp")
        self.assertEqual(high_hashed["status"], "fresh-contender-fail-closed")
        self.assertEqual(high_hashed["fresh_contenders"][0]["pid"], 703)
        self.assertEqual(high_hashed["fresh_contenders"][0]["status"], "actual-command-provider-contender")

    def _fake_ps(self, stdout=b"", stderr=b"", *, returncode=0, stalled=False, unreapable=False):
        streams = []
        writers = []
        for data in (stdout, stderr):
            read_fd, write_fd = os.pipe()
            streams.append(os.fdopen(read_fd, "rb", buffering=0))
            writers.append(write_fd)
            if data:
                os.write(write_fd, data)
            if not stalled:
                os.close(write_fd)
                writers[-1] = None

        class Child:
            pid = 43210
            def __init__(self):
                self.stdout, self.stderr = streams
                self.returncode = None if stalled else returncode
                self.killed = False
            def wait(self, timeout=None):
                if self.returncode is None:
                    raise subprocess.TimeoutExpired(["ps"], timeout)
                return self.returncode
            def poll(self):
                return self.returncode
            def kill(self):
                self.killed = True
                if not unreapable:
                    self.returncode = -9
                for index, fd in enumerate(writers):
                    if fd is not None and not unreapable:
                        os.close(fd)
                        writers[index] = None

        return Child(), writers

    def _fake_query_process(self, stdout=b"", stderr=b"", *, returncode=0, pid=8765,
                            hold_open=False, unreapable=False):
        streams = []
        writers = []
        for data in (stdout, stderr):
            read_fd, write_fd = os.pipe()
            streams.append(os.fdopen(read_fd, "rb", buffering=0))
            writers.append(write_fd)
            if data:
                os.write(write_fd, data)
            if not hold_open:
                os.close(write_fd)
                writers[-1] = None

        class Child:
            def __init__(self):
                self.pid = pid
                self.stdout, self.stderr = streams
                self.returncode = None if hold_open else returncode
                self.killed = False
            def wait(self, timeout=None):
                if self.returncode is None:
                    raise subprocess.TimeoutExpired(["python", "snapshot_query.py"], timeout)
                return self.returncode
            def poll(self):
                return self.returncode
            def kill(self):
                self.killed = True
                if self.returncode is None and not unreapable:
                    self.returncode = -9
                for index, fd in enumerate(writers):
                    if fd is not None and not unreapable:
                        os.close(fd)
                        writers[index] = None

        return Child(), writers

    def test_bounded_ps_provider_retains_actual_fields_and_reaps_owned_child(self):
        raw = b"700 0.2 bifrost /opt/bifrost/bifrost --mcp --stdio\n"
        child, _ = self._fake_ps(raw)
        events = []
        def fake_popen(argv, **kwargs):
            self.assertEqual(argv, ["ps", "-axo", "pid=,%cpu=,comm=,args="])
            self.assertTrue(kwargs["close_fds"])
            return child
        provider = snapshot_query.PsCommandProvider(time.monotonic() + 2.0, child_event=events.append)
        with mock.patch.object(snapshot_query.subprocess, "Popen", side_effect=fake_popen):
            rows, coverage = provider.command_table()
        self.assertEqual(rows[0]["cpu_percent"], 0.2)
        self.assertEqual(rows[0]["comm"], "bifrost")
        self.assertEqual(rows[0]["args"], "/opt/bifrost/bifrost --mcp --stdio")
        self.assertEqual(coverage["raw_table"], raw.decode())
        self.assertEqual(len(events), 2)
        self.assertTrue(events[-1]["reaped"])
        self.assertEqual(events[-1]["returncode"], 0)
        self.assertFalse(events[-1]["kill_requested"])

    def test_bounded_ps_provider_missing_fields_and_byte_limit_fail_closed(self):
        child, _ = self._fake_ps(b"700 0.2 bifrost\n")
        with mock.patch.object(snapshot_query.subprocess, "Popen", return_value=child):
            with self.assertRaises(snapshot_query.SnapshotFailure) as caught:
                snapshot_query.PsCommandProvider(time.monotonic() + 2.0).command_table()
        self.assertTrue(caught.exception.partial["coverage"]["coverage_errors"])

        child, _ = self._fake_ps(b"123456789\n")
        with mock.patch.object(snapshot_query, "MAX_PS_TABLE_BYTES", 4), \
             mock.patch.object(snapshot_query.subprocess, "Popen", return_value=child):
            with self.assertRaises(snapshot_query.SnapshotFailure) as caught:
                snapshot_query.PsCommandProvider(time.monotonic() + 2.0).command_table()
        self.assertTrue(caught.exception.partial["truncated"])
        self.assertEqual(caught.exception.partial["coverage"]["observed_stdout_bytes_capped"], 5)

    def _long_editor_args(self, target_bytes=9239):
        prefix = (
            "/Applications/VisualStudioCode.app/Contents/MacOS/Electron "
            "--type=renderer --user-data-dir=/Users/dave/Library/Application Support/Code "
            "--vscode-window-config={\"windowId\":4588,\"workspace\":\"/Users/dave/Workspace/Bifrost\","
            "\"extensions\":[\"ms-python.python\",\"github.copilot\"],\"persistedEditorState\":\""
        )
        suffix = "\"}"
        self.assertLess(len(prefix.encode()), target_bytes - len(suffix))
        return prefix + ("x" * (target_bytes - len(prefix.encode()) - len(suffix))) + suffix

    def test_ps_provider_accepts_9239_byte_editor_args_and_preserves_raw_classifier_input(self):
        args = self._long_editor_args()
        self.assertEqual(len(args.encode("utf-8")), 9239)
        raw = f"4588 0.0 Code {args}\n".encode("utf-8")
        child, _ = self._fake_ps(raw)
        with mock.patch.object(snapshot_query.subprocess, "Popen", return_value=child):
            rows, coverage = snapshot_query.PsCommandProvider(time.monotonic() + 2.0).command_table()
        self.assertEqual(rows[0]["pid"], 4588)
        self.assertEqual(len(rows[0]["args"].encode("utf-8")), 9239)
        self.assertEqual(rows[0]["raw_row"], raw.decode("utf-8").rstrip("\n"))
        self.assertEqual(coverage["raw_table"], raw.decode("utf-8"))

        value = query(command=[])
        command_snapshot = value["snapshots"][1]
        command_snapshot["rows"] = rows
        command_snapshot["table"] = coverage["raw_table"]
        command_snapshot["coverage"] = dict(coverage)
        command_snapshot["coverage"].pop("raw_table")
        command_snapshot["coverage"]["provider_child"] = value["provider_children"][0]
        command_inputs = []
        hashed_inputs = []
        self.assertEqual(self.evaluate_with_classifiers(value, command_inputs, hashed_inputs)["status"],
                         "historical-absence-observed-no-fresh-contender")
        self.assertEqual(command_inputs, [raw.decode("utf-8")])
        self.assertEqual(hashed_inputs, [raw.decode("utf-8")])

    def evaluate_with_classifiers(self, value, command_inputs, hashed_inputs):
        executor = types.SimpleNamespace(
            _contenders=lambda table: (command_inputs.append(table) or self.executor_source._contenders(table)),
        )
        controller = types.SimpleNamespace(
            _hashed_bifrost_contenders=lambda table: (
                hashed_inputs.append(table) or self.controller_source._hashed_bifrost_contenders(table)
            ),
        )
        proc = types.SimpleNamespace(descendants=self.process_source.descendants)
        return pr.evaluate_reconciliation(
            value, [{"pid": 601, "row": "601 80.0 java /usr/bin/java", "native": None}],
            deadline=5.0, executor=executor, controller=controller, proc=proc,
            tracked={500: "birth"},
        )

    def test_ps_provider_rejects_rows_and_args_above_64_kib_and_table_above_8_mib(self):
        long_row = f"4588 0.0 Code {self._long_editor_args(64 * 1024)}\n".encode("utf-8")
        self.assertGreater(len(long_row.rstrip(b"\n")), snapshot_query.MAX_PS_ROW_BYTES)
        with self.assertRaisesRegex(snapshot_query.SnapshotFailure, "64 KiB row bound") as caught:
            snapshot_query.PsCommandProvider(time.monotonic() + 2.0)._parse(long_row)
        self.assertEqual(caught.exception.partial["table"], long_row.decode("utf-8"))

        overlong_args = self._long_editor_args(snapshot_query.MAX_PS_ARGS_BYTES + 1)
        with mock.patch.object(snapshot_query, "MAX_PS_ROW_BYTES", 128 * 1024):
            with self.assertRaisesRegex(snapshot_query.SnapshotFailure, "64 KiB field bound"):
                snapshot_query.PsCommandProvider(time.monotonic() + 2.0)._parse(
                    f"4588 0.0 Code {overlong_args}\n".encode("utf-8"),
                )

        with self.assertRaisesRegex(snapshot_query.SnapshotFailure, "8 MiB provider bound") as table_error:
            snapshot_query.PsCommandProvider(time.monotonic() + 2.0)._parse(
                b" " * (snapshot_query.MAX_PS_TABLE_BYTES + 1),
            )
        self.assertTrue(table_error.exception.partial["truncated"])
        self.assertEqual(table_error.exception.partial["coverage"]["observed_table_bytes"],
                         snapshot_query.MAX_PS_TABLE_BYTES + 1)

    def test_darwin_native_short_read_is_detailed_and_never_skips_enumerated_pid(self):
        class Libproc:
            def __init__(self):
                self.calls = []
                self.errno_at_entry = []
            def proc_pidinfo(self, pid, flavor, arg, info_ptr, expected_size):
                self.calls.append(pid)
                self.errno_at_entry.append(ctypes.get_errno())
                ctypes.set_errno(errno.ESRCH)
                return 0

        provider = snapshot_query.DarwinProvider.__new__(snapshot_query.DarwinProvider)
        provider.deadline = time.monotonic() + 2.0
        provider.libproc = Libproc()
        provider._pids = lambda: ([10491, 10492], {
            "enumeration": "fixture-proc_listallpids", "enumerated_pid_count": 2,
            "pid_capacity": 1024, "truncated": False, "coverage_errors": [],
            "excluded_pid0_kernel_entries": 0,
        })
        ctypes.set_errno(errno.EINTR)
        try:
            value = snapshot_query._snapshot("native-before", provider, provider.native_table,
                                             provider.deadline)
        finally:
            ctypes.set_errno(0)
        self.assertFalse(value["complete"])
        self.assertEqual(provider.libproc.calls, [10491])
        self.assertEqual(provider.libproc.errno_at_entry, [0])
        diagnostic = value["error"]["diagnostic"]
        self.assertEqual(diagnostic["pid"], 10491)
        self.assertEqual(diagnostic["returned_count"], 0)
        self.assertEqual(diagnostic["expected_size"], ctypes.sizeof(provider.BsdInfo()))
        self.assertEqual(diagnostic["ctypes_errno"], errno.ESRCH)
        coverage_error = value["coverage"]["coverage_errors"][0]["diagnostic"]
        self.assertEqual(coverage_error, diagnostic)
        self.assertEqual(value["coverage"]["returned_pid_count"], 0)

    def test_darwin_proc_pidpath_error_clears_errno_and_reports_bounded_call_details(self):
        class Libproc:
            def __init__(self):
                self.errno_at_path_entry = None
            def proc_pidinfo(self, pid, flavor, arg, info_ptr, expected_size):
                ctypes.get_errno()
                info = ctypes.cast(info_ptr, ctypes.POINTER(snapshot_query.DarwinProvider.BsdInfo)).contents
                info.header[1] = 1
                info.header[3] = pid
                info.header[4] = 1
                info.seconds = 123
                info.microseconds = 456
                return expected_size
            def proc_pidpath(self, pid, buffer, buffer_size):
                self.errno_at_path_entry = ctypes.get_errno()
                ctypes.set_errno(errno.EACCES)
                return -1

        provider = snapshot_query.DarwinProvider.__new__(snapshot_query.DarwinProvider)
        provider.deadline = time.monotonic() + 2.0
        provider.libproc = Libproc()
        ctypes.set_errno(errno.EINTR)
        try:
            with self.assertRaises(snapshot_query.SnapshotFailure) as caught:
                provider._row(10491, command=True)
        finally:
            ctypes.set_errno(0)
        self.assertEqual(provider.libproc.errno_at_path_entry, 0)
        self.assertEqual(caught.exception.diagnostic, {
            "provider": "darwin-libproc", "api": "proc_pidpath", "pid": 10491,
            "returned_count": -1, "expected_size": snapshot_query.MAX_COMMAND_BYTES,
            "ctypes_errno": errno.EACCES, "buffer_size": snapshot_query.MAX_COMMAND_BYTES + 1,
        })

    def test_bounded_ps_provider_stall_kills_and_records_only_direct_child(self):
        child, _ = self._fake_ps(stalled=True)
        events = []
        with mock.patch.object(snapshot_query, "MAX_PS_CLEANUP_RESERVE_SECONDS", 0.01), \
             mock.patch.object(snapshot_query.subprocess, "Popen", return_value=child):
            with self.assertRaises(snapshot_query.SnapshotFailure) as caught:
                snapshot_query.PsCommandProvider(time.monotonic() + 0.08,
                                                 child_event=events.append).command_table()
        self.assertTrue(child.killed)
        self.assertEqual(len(events), 2)
        final = caught.exception.partial["coverage"]["provider_child"]
        self.assertEqual(final["pid"], child.pid)
        self.assertTrue(final["kill_requested"])
        self.assertTrue(final["reaped"])
        self.assertFalse(final["cleanup_incomplete"])
        self.assertTrue(final["direct_child_only"])

    def test_bounded_ps_provider_unreaped_child_remains_explicitly_uncertain(self):
        child, writers = self._fake_ps(stalled=True, unreapable=True)
        events = []
        start = time.monotonic()
        with mock.patch.object(snapshot_query, "MAX_PS_CLEANUP_RESERVE_SECONDS", 0.01), \
             mock.patch.object(snapshot_query.subprocess, "Popen", return_value=child):
            with self.assertRaises(snapshot_query.SnapshotFailure) as caught:
                snapshot_query.PsCommandProvider(start + 0.07,
                                                 child_event=events.append).command_table()
        self.assertLessEqual(time.monotonic() - start, 0.15)
        final = caught.exception.partial["coverage"]["provider_child"]
        self.assertEqual(final["pid"], child.pid)
        self.assertTrue(final["kill_requested"])
        self.assertFalse(final["reaped"])
        self.assertTrue(final["cleanup_incomplete"])
        self.assertTrue(final["direct_child_only"])
        for fd in writers:
            if fd is not None:
                os.close(fd)

    def test_provider_errors_truncation_missing_fields_and_deadline_fail_closed(self):
        cases = []
        incomplete = query()
        incomplete["outcome"]["complete"] = False
        cases.append(incomplete)
        truncated = query()
        truncated["snapshots"][0]["truncated"] = True
        truncated["snapshots"][0]["coverage"]["truncated"] = True
        cases.append(truncated)
        missing_birth = query(native_after=[{"pid": 500, "ppid": 1, "state": "S", "command": "/usr/bin/python3"}])
        cases.append(missing_birth)
        late = query(end=5.1)
        cases.append(late)
        uncertain_nested = query()
        uncertain_nested["provider_children"][0]["reaped"] = False
        uncertain_nested["provider_children"][0]["cleanup_incomplete"] = True
        uncertain_nested["snapshots"][1]["coverage"]["provider_child"]["reaped"] = False
        uncertain_nested["snapshots"][1]["coverage"]["provider_child"]["cleanup_incomplete"] = True
        cases.append(uncertain_nested)
        for result in cases:
            with self.subTest(outcome=result["outcome"]):
                evaluated = self.evaluate(result)
                self.assertEqual(evaluated["status"], "incomplete-fail-closed")
                self.assertEqual(evaluated["candidate_outcomes"][0]["status"],
                                 "reconciliation_incomplete_fail_closed")
                self.assertNotIn("retired_candidates", evaluated)

    def test_snapshot_order_and_timestamps_are_mandatory(self):
        reversed_query = query()
        reversed_query["snapshots"][0], reversed_query["snapshots"][1] = reversed_query["snapshots"][1], reversed_query["snapshots"][0]
        result = self.evaluate(reversed_query)
        self.assertEqual(result["status"], "incomplete-fail-closed")
        missing_time = query()
        missing_time["snapshots"][1].pop("started_utc")
        self.assertEqual(self.evaluate(missing_time)["status"], "incomplete-fail-closed")

    def test_kernel_pid_zero_exclusion_must_be_accounted_for(self):
        missing_exclusion = query()
        missing_exclusion["snapshots"][0]["coverage"].pop("excluded_pid0_kernel_entries")
        self.assertEqual(self.evaluate(missing_exclusion)["status"], "incomplete-fail-closed")

    def test_one_child_timeout_is_typed_and_only_direct_child_is_killed(self):
        records = [
            {"kind": "snapshot", "snapshot": query()["snapshots"][0]},
            {"kind": "provider-child", "provider_child": {
                "provider_identity": "ps-axo-pid-percentcpu-comm-args/v1", "pid": 4999,
                "returncode": None, "kill_requested": True, "reaped": False,
                "cleanup_incomplete": True, "direct_child_only": True}},
        ]
        partial = ("\n".join(json.dumps(item) for item in records) + "\n").encode()
        child, writers = self._fake_query_process(partial, hold_open=True, unreapable=True)
        calls = []
        def fake_popen(argv, **kwargs):
            calls.append((argv, kwargs))
            return child
        with (mock.patch.object(pr, "QUERY_CLEANUP_RESERVE_SECONDS", 0.01),
              mock.patch.object(pr, "QUERY_FINALIZE_RESERVE_SECONDS", 0.005)):
            result = pr.run_query_child(boundary_deadline=time.monotonic() + 0.07,
                                        popen=fake_popen, python="/fake/python",
                                        script=Path("/tmp/query.py"))
        self.assertEqual(result["outcome"]["status"], "deadline-exceeded")
        self.assertTrue(child.killed)
        self.assertEqual(len(result["snapshots"]), 1)
        self.assertEqual(result["snapshots"][0]["name"], "native-before")
        self.assertEqual(result["provider_children"][0]["pid"], 4999)
        self.assertFalse(result["provider_children"][0]["reaped"])
        self.assertEqual(result["query_child"]["pid"], child.pid)
        self.assertTrue(result["query_child"]["kill_requested"])
        self.assertFalse(result["query_child"]["reaped"])
        self.assertTrue(result["query_child"]["cleanup_incomplete"])
        self.assertIn("unproven", result["query_child"]["descendant_containment"])
        self.assertEqual(calls[0][0][1:3], ["-B", "-E"])
        self.assertEqual(calls[0][1]["cwd"], "/")
        self.assertNotIn("start_new_session", calls[0][1])
        self.assertLessEqual(result["query_output_capture"]["stdout"]["bytes_retained"], pr.MAX_RESULT_BYTES)
        self.assertEqual(result["partial_output_capture"]["label"], "bounded-partial-output-prefix")
        for fd in writers:
            if fd is not None:
                os.close(fd)

    def test_query_child_non_timeout_error_still_kills_and_reaps_direct_child(self):
        nested = {"kind": "provider-child", "provider_child": {
            "provider_identity": "ps-axo-pid-percentcpu-comm-args/v1", "pid": 9876,
            "returncode": None, "kill_requested": False, "reaped": False,
            "cleanup_incomplete": True, "direct_child_only": True}}
        stream = (json.dumps(nested) + "\n").encode()
        child, _ = self._fake_query_process(stream, hold_open=True)
        original_read = os.read
        fail_once = [True]
        def broken_read(fd, size):
            if fail_once[0]:
                fail_once[0] = False
                raise OSError("query output read failed")
            return original_read(fd, size)
        with mock.patch.object(pr.os, "read", side_effect=broken_read):
            result = pr.run_query_child(boundary_deadline=time.monotonic() + 1.0,
                                        popen=lambda *args, **kwargs: child,
                                        python="/fake/python", script=Path("/tmp/query.py"))
        self.assertEqual(result["outcome"]["status"], "query-child-error")
        self.assertTrue(child.killed)
        self.assertEqual(result["query_child"]["pid"], child.pid)
        self.assertTrue(result["query_child"]["kill_requested"])
        self.assertTrue(result["query_child"]["reaped"])
        self.assertEqual(result["provider_children"][0]["pid"], 9876)

    def test_query_child_stream_reconstructs_all_snapshots_and_final_outcome(self):
        value = query()
        lines = [json.dumps({"kind": "snapshot", "snapshot": snapshot}, separators=(",", ":"))
                 for snapshot in value["snapshots"]]
        final = {key: item for key, item in value.items() if key != "snapshots"}
        final["snapshot_count"] = len(value["snapshots"])
        lines.append(json.dumps({"kind": "final", "result": final}, separators=(",", ":")))
        output = ("\n".join(lines) + "\n").encode()
        child, _ = self._fake_query_process(output, pid=1234)
        result = pr.run_query_child(boundary_deadline=time.monotonic() + 10.0,
                                    popen=lambda *a, **kw: child, python="/fake/python",
                                    script=Path("/tmp/query.py"))
        self.assertEqual([item["name"] for item in result["snapshots"]],
                         ["native-before", "command", "native-after"])
        self.assertTrue(result["outcome"]["complete"])
        self.assertEqual(result["query_child"]["pid"], 1234)
        self.assertTrue(result["query_child"]["reaped"])
        self.assertAlmostEqual(result["provider_deadline_monotonic"],
                               result["deadline_monotonic"] - 0.15)
        self.assertAlmostEqual(result["duration_limit_seconds"], 4.85)

    def test_bounded_capture_never_retains_more_than_its_limit(self):
        capture = pr._BoundedCapture(4)
        capture.feed(b"abc")
        capture.feed(b"defgh")
        self.assertEqual(len(capture.prefix), 4)
        self.assertEqual(bytes(capture.prefix), b"abcd")
        metadata = capture.metadata()
        self.assertEqual(metadata["bytes_retained"], 4)
        self.assertEqual(metadata["bytes_observed"], 8)
        self.assertTrue(metadata["truncated"])
        self.assertEqual(metadata["prefix_sha256"], hashlib.sha256(b"abcd").hexdigest())
        self.assertEqual(metadata["observed_sha256"], hashlib.sha256(b"abcdefgh").hexdigest())

    def test_query_child_stdout_over_limit_is_partial_prefix_only_for_normal_and_stalled_child(self):
        oversized = b"x" * 100
        cases = (("normal", False), ("stalled", True))
        for label, stalled in cases:
            with self.subTest(label=label):
                child, _ = self._fake_query_process(oversized, hold_open=stalled)
                with (mock.patch.object(pr, "MAX_RESULT_BYTES", 32),
                      mock.patch.object(pr, "QUERY_CLEANUP_RESERVE_SECONDS", 0.01),
                      mock.patch.object(pr, "QUERY_FINALIZE_RESERVE_SECONDS", 0.005),
                      mock.patch.object(pr, "_decode_query_stream", side_effect=AssertionError("oversized stream decoded"))):
                    result = pr.run_query_child(boundary_deadline=time.monotonic() + 0.08,
                                                popen=lambda *a, **kw: child,
                                                python="/fake/python", script=Path("/tmp/query.py"))
                self.assertEqual(result["outcome"]["status"], "query-output-truncated")
                self.assertEqual(result["snapshots"], [])
                capture = result["query_output_capture"]["stdout"]
                self.assertEqual(capture["limit_bytes"], 32)
                self.assertEqual(capture["bytes_retained"], 32)
                self.assertEqual(capture["bytes_observed"], 100)
                self.assertTrue(capture["truncated"])
                prefix = base64.b64decode(result["partial_output_capture"]["stdout_prefix_base64"])
                self.assertEqual(prefix, oversized[:32])
                self.assertEqual(result["query_child"]["reaped"], True)
                self.assertEqual(result["query_child"]["kill_requested"], stalled)

    def test_query_child_stderr_over_limit_is_bounded_and_fails_closed(self):
        child, _ = self._fake_query_process(b"bounded stdout\n", b"e" * 20)
        with (mock.patch.object(pr, "MAX_QUERY_STDERR_BYTES", 8),
              mock.patch.object(pr, "_decode_query_stream", side_effect=AssertionError("truncated stderr accepted"))):
            result = pr.run_query_child(boundary_deadline=time.monotonic() + 1.0,
                                        popen=lambda *a, **kw: child,
                                        python="/fake/python", script=Path("/tmp/query.py"))
        self.assertEqual(result["outcome"]["status"], "query-output-truncated")
        stderr = result["query_output_capture"]["stderr"]
        self.assertEqual(stderr["bytes_retained"], 8)
        self.assertEqual(stderr["bytes_observed"], 20)
        self.assertTrue(stderr["truncated"])
        self.assertEqual(base64.b64decode(result["partial_output_capture"]["stderr_prefix_base64"]), b"e" * 8)

    def supervise_candidate(self, fresh_query, *, fail_reconciliation_receipt=False,
                            current_reappearance=False, query_raises=False,
                            clock_value=None, advance_after_receipt=False):
        clock_value = [0.0] if clock_value is None else clock_value
        directory = Path(tempfile.mkdtemp(prefix="monitor06-test-", dir=Path(__file__).parent))
        read_fd, write_fd = os.pipe()
        lock_path = directory / "lock"
        lock_path.write_bytes(b"")
        lock_fd = os.open(lock_path, os.O_RDONLY)
        frames = [
            {"token": "token", "pid": 500, "birth_identity": "root-birth",
             "phase": phase, "observed_monotonic": 0.0}
            for phase in ("ready", "controls-started", "controls-returned")
        ]
        for frame in frames:
            os.write(write_fd, n.canonical(frame))

        class Child:
            pid = 500
            def __init__(self):
                self.calls = 0
            def poll(self):
                self.calls += 1
                return None if self.calls == 1 else 0

        child = Child()
        controller = types.SimpleNamespace(
            _process=lambda pid: {"pid": pid, "birth_identity": "root-birth"},
            _bounded_reap_unidentified_child=lambda value: {"coordinator_reaped": True},
            _hashed_bifrost_contenders=self.controller_source._hashed_bifrost_contenders,
        )
        native_states = iter([
            {500: (1, "root-birth", "S")},  # original snapshot, rejected row lacks native identity
            ({500: (1, "root-birth", "S"), 601: (500, "recycled-birth", "S")}
             if current_reappearance else {500: (1, "root-birth", "S")}),
            {},                                  # cleanup verification
        ])
        command_tables = iter([
            "601 80.0 java /usr/bin/java -version",
            "601 80.0 java /usr/bin/java -version" if current_reappearance is True else "",
        ])
        executor = types.SimpleNamespace(
            _process_table=lambda: next(command_tables),
            _contenders=self.executor_source._contenders,
        )
        proc = types.SimpleNamespace(
            start_identity=lambda pid, fallback: "root-birth",
            process_table=lambda: next(native_states),
            descendants=self.process_source.descendants,
            active=lambda table, tracked: [],
        )
        resources = types.SimpleNamespace(sample=lambda **kwargs: None)
        query_calls = []
        def query_runner(*, boundary_deadline, clock):
            query_calls.append(boundary_deadline)
            if query_raises:
                raise RuntimeError("query runner failed before returning evidence")
            return fresh_query
        original_immutable = n.immutable
        def immutable(path, value):
            if fail_reconciliation_receipt and path.name.startswith("contention-reconciliation-"):
                raise OSError("reconciliation receipt path unavailable")
            receipt_ref = original_immutable(path, value)
            if advance_after_receipt and path.name.startswith("contention-reconciliation-"):
                clock_value[0] = 6.0
            return receipt_ref
        try:
            with mock.patch.object(n, "immutable", side_effect=immutable), \
                 mock.patch.object(n.time, "sleep", return_value=None):
                result = n.supervise(
                    ["fixture-only"], root=directory, env={}, stdout=None, stderr=None,
                    lock_fd=lock_fd, request_sha="a" * 64, controller=controller,
                    proc=proc, resources=resources, executor=executor, namespace=directory,
                    token="token", read_fd=read_fd, write_fd=write_fd,
                    popen=lambda *args, **kwargs: child, clock=lambda: clock_value[0],
                    reconciliation_query=query_runner,
                )
            receipt_path = directory / "contention-reconciliation-01.json"
            receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else None
            stop_path = directory / "contention-stop.json"
            stop_receipt = json.loads(stop_path.read_bytes()) if stop_path.exists() else None
            return result, query_calls, receipt, stop_receipt
        finally:
            os.close(lock_fd)
            for path in directory.iterdir():
                path.unlink()
            directory.rmdir()

    def test_supervisor_persists_successful_receipt_and_uses_one_pass(self):
        result, calls, receipt, _ = self.supervise_candidate(query())
        self.assertIsNone(result["failure"], result)
        self.assertEqual(len(calls), 1)
        self.assertLessEqual(calls[0], 5.0)
        self.assertEqual(receipt["status"], "historical-absence-observed-no-fresh-contender")
        self.assertEqual(receipt["evaluation"]["candidate_outcomes"][0]["status"],
                         "unresolved_historical_absent_at_reconciliation")
        self.assertEqual([item["name"] for item in receipt["fresh_query"]["snapshots"]],
                         ["native-before", "command", "native-after"])
        self.assertFalse(receipt["continuous_absence_claim"])
        attempt = result["reconciliation_attempts"][0]
        self.assertEqual(attempt["receipt_write_state"], "durable")
        self.assertTrue(attempt["supervisor_continuation_authorized"])
        self.assertTrue(all(check["within_deadline"] for check in attempt["deadline_checks"].values()))
        self.assertTrue(result["reconciliation_continuation_authorized"])

    def test_slow_evaluation_past_absolute_pass_deadline_stops_before_continuation(self):
        clock_value = [0.0]
        evaluator = n.process_reconciliation.evaluate_reconciliation
        def slow_evaluator(*args, **kwargs):
            result = evaluator(*args, **kwargs)
            clock_value[0] = 6.0
            return result
        with mock.patch.object(n.process_reconciliation, "evaluate_reconciliation", side_effect=slow_evaluator):
            result, _, receipt, stop_receipt = self.supervise_candidate(
                query(), clock_value=clock_value,
            )
        self.assertEqual(result["failure"]["type"], "TimeoutError")
        attempt = stop_receipt["reconciliation_attempt"]
        self.assertFalse(attempt["deadline_checks"]["after_evaluation"]["within_deadline"])
        self.assertFalse(attempt["supervisor_continuation_authorized"])
        self.assertFalse(result["reconciliation_continuation_authorized"])
        self.assertFalse(receipt["supervisor_continuation_authorized"])
        self.assertEqual(attempt["receipt_write_state"], "durable")

    def test_slow_durable_receipt_past_absolute_pass_deadline_stops_before_continuation(self):
        result, _, receipt, stop_receipt = self.supervise_candidate(
            query(), advance_after_receipt=True,
        )
        self.assertEqual(result["failure"]["type"], "TimeoutError")
        attempt = stop_receipt["reconciliation_attempt"]
        self.assertTrue(attempt["deadline_checks"]["after_evaluation"]["within_deadline"])
        self.assertFalse(attempt["deadline_checks"]["after_durable_receipt_write"]["within_deadline"])
        self.assertFalse(attempt["supervisor_continuation_authorized"])
        self.assertFalse(result["reconciliation_continuation_authorized"])
        self.assertFalse(receipt["supervisor_continuation_authorized"])
        self.assertEqual(attempt["receipt_write_state"], "durable")

    def test_supervisor_reappearance_stops_and_receipt_failure_keeps_primary_error(self):
        result, calls, receipt, stop_receipt = self.supervise_candidate(
            query(native_after=[native_row(601, birth="recycled-birth")]),
            fail_reconciliation_receipt=True,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["failure"]["type"], "ValueError")
        self.assertEqual(result["failure"]["message"],
                         "unresolved candidate appears in a fresh reconciliation snapshot")
        self.assertIsNone(receipt)
        self.assertTrue(result.get("failure"))
        attempt = stop_receipt["reconciliation_attempt"]
        self.assertEqual(attempt["fresh_query"]["snapshots"][2]["name"], "native-after")
        self.assertEqual(attempt["evaluation"]["status"], "candidate-present-fail-closed")
        self.assertEqual(attempt["receipt_write_state"], "failed")
        self.assertEqual(attempt["reconciliation_receipt_write_error"]["type"], "OSError")

    def test_query_runner_exception_is_persisted_as_typed_incomplete_attempt(self):
        result, calls, receipt, stop_receipt = self.supervise_candidate(
            query(), query_raises=True,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["failure"]["type"], "RuntimeError")
        self.assertEqual(receipt["fresh_query"]["outcome"]["status"], "query-call-error")
        attempt = stop_receipt["reconciliation_attempt"]
        self.assertEqual(attempt["evaluation"]["status"], "incomplete-fail-closed")
        self.assertFalse(attempt["evidence_complete"])
        self.assertEqual(attempt["primary_failure"]["type"], "RuntimeError")

    def test_evaluator_exception_keeps_query_and_typed_incomplete_evaluation(self):
        with mock.patch.object(n.process_reconciliation, "evaluate_reconciliation",
                               side_effect=RuntimeError("evaluator failed")):
            result, calls, receipt, stop_receipt = self.supervise_candidate(query())
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["failure"]["type"], "RuntimeError")
        self.assertEqual(result["failure"]["message"], "evaluator failed")
        self.assertEqual([item["name"] for item in receipt["fresh_query"]["snapshots"]],
                         ["native-before", "command", "native-after"])
        attempt = stop_receipt["reconciliation_attempt"]
        self.assertEqual(attempt["evaluation"]["status"], "incomplete-fail-closed")
        self.assertEqual(attempt["evaluation"]["error"]["message"], "evaluator failed")
        self.assertEqual(attempt["primary_failure"]["message"], "evaluator failed")

    def test_later_current_reappearance_cannot_inherit_the_absence_or_get_second_pass(self):
        for mode in (True, "native-only"):
            with self.subTest(mode=mode):
                result, calls, receipt, stop_receipt = self.supervise_candidate(
                    query(), current_reappearance=mode,
                )
                self.assertEqual(len(calls), 1)
                self.assertEqual(receipt["evaluation"]["candidate_outcomes"][0]["status"],
                                 "unresolved_historical_absent_at_reconciliation")
                self.assertEqual(result["failure"]["message"],
                                 "historical absent PID reappeared in current raw snapshot")
                self.assertEqual(stop_receipt["historical_absent_pid_reappearances"][0]["pid"], 601)
                if mode is True:
                    self.assertIn("original-command", stop_receipt["historical_absent_pid_reappearances"][0]["present_in"])
                    self.assertEqual(stop_receipt["historical_absent_pid_reappearances"][0]["native"]["ppid"], 500)
                    self.assertIn(601, stop_receipt["current_raw_pid_observations"]["command_pids"])
                else:
                    self.assertEqual(stop_receipt["historical_absent_pid_reappearances"][0]["present_in"], ["original-native"])

    def test_query_child_keeps_native_command_native_order_after_provider_error(self):
        calls = []
        class FakeProvider:
            identity = "fake-ordered-provider/v1"
            def __init__(self, deadline):
                self.deadline = deadline
                self.native_calls = 0
            def native_table(self):
                calls.append("native")
                self.native_calls += 1
                if self.native_calls == 1:
                    raise snapshot_query.SnapshotFailure("first native snapshot failed")
                return [native_row(500)], {"enumerated_pid_count": 1, "returned_pid_count": 1,
                                           "truncated": False, "excluded_pid0_kernel_entries": 0,
                                           "coverage_errors": [], "required_fields": []}
            def command_table(self):
                calls.append("command")
                return [command_row(500)], {"enumerated_pid_count": 1, "returned_pid_count": 1,
                                            "truncated": False, "excluded_pid0_kernel_entries": 0,
                                            "coverage_errors": [], "required_fields": []}

        class FakePsProvider:
            identity = "ps-axo-pid-percentcpu-comm-args/v1"
            def __init__(self, deadline, child_event=None):
                self.child_event = child_event
            def command_table(self):
                calls.append("command")
                value = {"provider_identity": self.identity, "pid": 9001,
                         "started_utc": "2026-10-26T00:00:02+00:00",
                         "ended_utc": "2026-10-26T00:00:02.1+00:00",
                         "started_monotonic": 2.0, "ended_monotonic": 2.1,
                         "kill_requested": False, "returncode": 0, "reaped": True,
                         "cleanup_incomplete": False, "direct_child_only": True,
                         "descendant_containment": "direct-child-reaped"}
                if self.child_event:
                    self.child_event({"kind": "provider-child", **value})
                rows = [command_row(500)]
                coverage = {"enumerated_pid_count": 1, "returned_pid_count": 1,
                            "truncated": False, "excluded_pid0_kernel_entries": 0,
                            "coverage_errors": [], "required_fields": [],
                            "kernel_pid0_rows_observed": 0, "provider_child": value}
                return rows, coverage | {"raw_table": rows[0]["raw_row"] + "\n"}

        with mock.patch.object(snapshot_query.sys, "platform", "darwin"), \
             mock.patch.object(snapshot_query, "DarwinProvider", FakeProvider), \
             mock.patch.object(snapshot_query, "PsCommandProvider", FakePsProvider):
            result = snapshot_query.query(deadline=10**12)
        self.assertEqual(calls, ["native", "command", "native"])
        self.assertEqual([item["name"] for item in result["snapshots"]],
                         ["native-before", "command", "native-after"])
        self.assertFalse(result["outcome"]["complete"])

    def test_complete_query_collects_native_ps_native_and_provider_lifecycle(self):
        calls = []
        class FakeNativeProvider:
            identity = "fake-native-provider/v1"
            def __init__(self, deadline):
                self.deadline = deadline
            def native_table(self):
                calls.append("native")
                rows = [native_row(500)]
                return rows, {"enumeration": "fixture", "enumerated_pid_count": 1,
                              "returned_pid_count": 1, "truncated": False,
                              "coverage_errors": [], "excluded_pid0_kernel_entries": 0,
                              "required_fields": ["pid", "ppid", "birth_identity", "state", "command"]}

        class FakePsProvider:
            identity = "ps-axo-pid-percentcpu-comm-args/v1"
            def __init__(self, deadline, child_event=None):
                self.child_event = child_event
            def command_table(self):
                calls.append("command")
                now = time.monotonic()
                child = {"provider_identity": self.identity, "pid": 6000,
                         "started_utc": "2026-10-26T00:00:02+00:00",
                         "ended_utc": "2026-10-26T00:00:02.1+00:00",
                         "started_monotonic": now, "ended_monotonic": now,
                         "kill_requested": False, "returncode": 0, "reaped": True,
                         "cleanup_incomplete": False, "direct_child_only": True,
                         "descendant_containment": "direct-child-reaped"}
                if callable(self.child_event):
                    self.child_event({"kind": "provider-child", **child})
                rows = [command_row(500, cpu=0.2, args="/usr/bin/python3 -m worker")]
                coverage = {"enumeration": "ps fixture", "enumerated_pid_count": 1,
                            "returned_pid_count": 1, "truncated": False,
                            "coverage_errors": [], "excluded_pid0_kernel_entries": 0,
                            "kernel_pid0_rows_observed": 0,
                            "required_fields": ["pid", "cpu_percent", "comm", "args", "command"],
                            "provider_child": child}
                return rows, coverage | {"raw_table": rows[0]["raw_row"] + "\n"}

        with (mock.patch.object(snapshot_query.sys, "platform", "darwin"),
              mock.patch.object(snapshot_query, "DarwinProvider", FakeNativeProvider),
              mock.patch.object(snapshot_query, "PsCommandProvider", FakePsProvider)):
            result = snapshot_query.query(time.monotonic() + 2.0)
        self.assertEqual(calls, ["native", "command", "native"])
        self.assertTrue(result["outcome"]["complete"])
        self.assertTrue(result["outcome"]["order_valid"])
        self.assertEqual(result["snapshots"][1]["table"], "500 0.2 python3 /usr/bin/python3 -m worker\n")
        self.assertEqual(result["provider_children"][0]["pid"], 6000)


if __name__ == "__main__":
    unittest.main()
