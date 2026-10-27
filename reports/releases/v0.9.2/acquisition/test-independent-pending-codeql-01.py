#!/usr/bin/env python3
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "reports/releases/v0.9.2/acquisition/independent-pending-codeql-01.py"


def load():
    spec = importlib.util.spec_from_file_location("independent_pending_codeql_tested", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CodeQLContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def test_real_sealed_prefix_retains_82_and_no_tail(self):
        raw, rows = self.m._ledger(ROOT)
        self.assertEqual(len(rows), 88)
        self.assertEqual(len(self.m.selected(rows, final=False)), 82)
        self.assertEqual(self.m._tail(rows, final=False), [])
        self.assertEqual(self.m.sha_bytes(raw.splitlines(keepends=True)[0] * 0 +
                                         self.m._read(ROOT, self.m.SEALED_LEDGER)),
                         self.m.SEALED_LEDGER_SHA)

    def test_preterminal_final_review_gate_accepts_sealed_prefix(self):
        # Admission/execute must be able to validate a final-reviewed
        # candidate before the one terminal CodeQL row exists.  The explicit
        # terminal parameter keeps that lifecycle distinction visible in the
        # public validator API; terminal verification still rejects 88 rows.
        self.assertIsNone(inspect.signature(self.m.validate).parameters["terminal"].default)
        _raw, rows = self.m._ledger(ROOT)
        self.assertEqual(self.m._tail(rows, final=False), [])
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m._tail(rows, final=True)

    def test_base_packet_projection_is_bound_to_supplied_prefix(self):
        raw, rows = self.m._ledger(ROOT)
        lines = raw.splitlines(keepends=True)
        packet = {
            "prefix_rows": [(row, self.m.sha_bytes(line)) for row, line in zip(rows[:57], lines[:57])],
            "tail_rows": [(row, self.m.sha_bytes(line)) for row, line in zip(rows[57:], lines[57:])],
        }
        projected = self.m._project_packet(packet, rows, raw)
        self.assertEqual(projected["prefix_rows"] + projected["tail_rows"],
                         packet["prefix_rows"] + packet["tail_rows"][:29])
        later = rows + [{"group_id": self.m.CODEQL_GROUP,
                         "attempt_id": self.m.CODEQL_ATTEMPT}]
        later_raw = raw + (json.dumps(later[-1], sort_keys=True) + "\n").encode()
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m._project_packet(packet, later, later_raw)

    def test_one_codeql_success_tail_yields_83_without_joern(self):
        _raw, rows = self.m._ledger(ROOT)
        row = {
            "group_id": self.m.CODEQL_GROUP,
            "attempt_id": self.m.CODEQL_ATTEMPT,
            "execution_series": 1,
            "attempt_number": 1,
            "status": "completed",
            "exit_code": 0,
            "timed_out": False,
            "capacity_loss": None,
        }
        rows.append(row)
        self.assertEqual(len(self.m.selected(rows, final=True)), 83)
        bad = list(rows)
        bad[-1] = dict(row, group_id="joern-swift-common108",
                       attempt_id="joern-swift-common108-attempt-05-series-01")
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m._tail(bad, final=True)

    def test_worker_marker_requires_macos_observed_value(self):
        class Executor:
            @staticmethod
            def _child_environment(group, execution, attempt, cache):
                return {
                    "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
                    "DATAFLOWBENCH_V092_GROUP_ID": self.m.CODEQL_GROUP,
                    "__CF_USER_TEXT_ENCODING": self.m.CF_USER_TEXT_ENCODING,
                }
        env = self.m.build_worker_environment(
            Executor(), {"id": self.m.CODEQL_GROUP}, Path("/x"), Path("/y"), Path("/z"))
        self.assertEqual(env["__CF_USER_TEXT_ENCODING"], self.m.CF_USER_TEXT_ENCODING)

        class Bad(Executor):
            @staticmethod
            def _child_environment(group, execution, attempt, cache):
                return {
                    "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
                    "DATAFLOWBENCH_V092_GROUP_ID": self.m.CODEQL_GROUP,
                    "__CF_USER_TEXT_ENCODING": "wrong",
                }
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m.build_worker_environment(
                Bad(), {"id": self.m.CODEQL_GROUP}, Path("/x"), Path("/y"), Path("/z"))

    def test_projection_guard_rejects_over_12_gib_and_restores(self):
        class Executor:
            def _materialize_source(self, *args, **kwargs):
                return 13 * 1024**3
        executor = Executor()
        original = executor._materialize_source
        with self.m._scoped_source_projection_guard(executor):
            with self.assertRaises(self.m.CodeQLContinuationError):
                executor._materialize_source("root", "commit", Path("dest"), [],
                                             disk_guard=object())
        self.assertIs(executor._materialize_source.__func__, original.__func__)

    def test_no_expiry_lease_is_finite_and_preserves_nonlease_fields(self):
        plan = {
            "resource_reservation": {"exclusive_analyzer_slot": True, "owner": "x"},
            "groups": [{"id": self.m.CODEQL_GROUP, "deadline_seconds": self.m.CODEQL_DEADLINE_SECONDS}],
            "source_commit": "a" * 40,
        }
        validated = {"plan": plan, "total_wall_budget_seconds": None, "marker": "retained"}
        runtime = self.m._runtime_lease(validated, ROOT)
        self.assertGreater(runtime["total_wall_budget_seconds"], 0)
        self.assertEqual(runtime["plan"]["resource_reservation"]["owner"], "x")
        self.assertEqual(runtime["execution_window_runtime"]["per_attempt_lease_seconds"], 13870)

    def test_terminal_failure_handoff_requires_durable_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt = root / "reports/releases/v0.9.2/attempts" / self.m.CODEQL_ATTEMPT
            attempt.mkdir(parents=True)
            stdout = attempt / "stdout.txt"
            stderr = attempt / "stderr.txt"
            stdout.write_bytes(b"partial stdout\n")
            stderr.write_bytes(b"capacity stop\n")
            (attempt / "started.json").write_text("started\n")
            (attempt / "completed.json").write_text("completed\n")
            execution = root / "execution-state/v092/groups/series-01" / self.m.CODEQL_GROUP / "attempt-01"
            row = {
                "group_id": self.m.CODEQL_GROUP,
                "attempt_id": self.m.CODEQL_ATTEMPT,
                "status": "capacity-lost",
                "timed_out": False,
                "started_receipt": "started.json",
                "stdout": {"path": "stdout.txt", "sha256": self.m.sha(stdout),
                           "bytes": stdout.stat().st_size},
                "stderr": {"path": "stderr.txt", "sha256": self.m.sha(stderr),
                           "bytes": stderr.stat().st_size},
                "execution_root": str(execution),
            }
            self.m._validate_terminal_failure({"root": root}, row)
            bad = dict(row)
            bad["stdout"] = dict(row["stdout"], sha256="0" * 64)
            with self.assertRaises(self.m.CodeQLContinuationError):
                self.m._validate_terminal_failure({"root": root}, bad)

    def test_terminal_tail_accepts_failure_but_rejects_unknown_status(self):
        _raw, rows = self.m._ledger(ROOT)
        failure = {
            "group_id": self.m.CODEQL_GROUP,
            "attempt_id": self.m.CODEQL_ATTEMPT,
            "execution_series": 1,
            "attempt_number": 1,
            "status": "recorder-error",
        }
        rows.append(failure)
        self.assertEqual(self.m._tail(rows, final=True)[0]["status"], "recorder-error")
        rows[-1] = dict(failure, status="running")
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m._tail(rows, final=True)

    def test_frozen_working_guard_keeps_twelve_gib_source_limit_and_thirty_gib_cap(self):
        base = json.loads((ROOT / Path(*self.m._relative(self.m.BASE_CONTRACT).parts)).read_text())
        base["resource_guards"] = {"stop_free_gib": 48, "working_set_gib": 30}
        frozen = self.m.load_frozen(ROOT)
        guard = self.m._codeql_disk_guard({
            "successor": {"plan": base}, "frozen": frozen,
        })
        self.assertEqual(guard.working_ceiling_bytes, 30 * 1024**3)
        with self.assertRaises(frozen["disk_guard"].DiskGuardError):
            guard.check(projected_bytes=30 * 1024**3 + 1,
                        category="working", capacity_path=ROOT)

    def test_live_resource_gate_binds_frozen_127_gib_check(self):
        seen = []

        class Executor:
            @staticmethod
            def _check_resources(root, minimum):
                seen.append((root, minimum))

        self.m.check_live_resource_floor(Executor(), ROOT)
        self.assertEqual(seen, [(ROOT, 127 * 1024**3)])

        class Bad(Executor):
            @staticmethod
            def _check_resources(root, minimum):
                raise RuntimeError("contender")

        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m.check_live_resource_floor(Bad(), ROOT)

    def test_locked_resource_adapter_raises_floor_before_fresh_attempt(self):
        calls = []

        class Executor:
            def _check_resources(self, root, minimum):
                calls.append(("resources", root, minimum))

            def _assert_fresh(self, root, group, reports, series):
                calls.append(("fresh", root, group, reports, series))
                return "fresh"

            def _materialize_source(self, *args, **kwargs):
                calls.append(("materialize", args, kwargs))
                return 0

        executor = Executor()
        with self.m._scoped_locked_resource_floor(executor, ROOT):
            self.assertEqual(executor._assert_fresh(ROOT, {}, [], 1), "fresh")
        self.assertEqual(calls[0], ("resources", ROOT, 127 * 1024**3))
        self.assertEqual(calls[1][0], "fresh")
        self.assertTrue(callable(executor._check_resources))
        self.assertTrue(callable(executor._assert_fresh))
        calls.clear()
        with self.m._scoped_locked_resource_floor(executor, ROOT):
            executor._materialize_source(ROOT, "source", Path("/tmp/codeql"), [],
                                         preflight_only=True)
        self.assertEqual(calls[0], ("resources", ROOT, 127 * 1024**3))
        self.assertEqual(calls[1][0], "materialize")

    def test_terminal_failure_replay_calls_frozen_verifier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt = root / "reports/releases/v0.9.2/attempts" / self.m.CODEQL_ATTEMPT
            attempt.mkdir(parents=True)
            stdout = attempt / "stdout.txt"
            stderr = attempt / "stderr.txt"
            stdout.write_bytes(b"partial stdout\n")
            stderr.write_bytes(b"capacity stop\n")
            (attempt / "started.json").write_text("started\n")
            completed = attempt / "completed.json"
            completed.write_text("completed\n")
            execution = root / "execution-state/v092/groups/series-01" / self.m.CODEQL_GROUP / "attempt-01"
            row = {
                "group_id": self.m.CODEQL_GROUP,
                "attempt_id": self.m.CODEQL_ATTEMPT,
                "plan_commit": "p" * 40,
                "status": "capacity-lost",
                "timed_out": False,
                "started_receipt": "started.json",
                "stdout": {"path": "stdout.txt", "sha256": self.m.sha(stdout), "bytes": stdout.stat().st_size},
                "stderr": {"path": "stderr.txt", "sha256": self.m.sha(stderr), "bytes": stderr.stat().st_size},
                "execution_root": str(execution),
            }
            seen = []

            class Executor:
                @staticmethod
                def _historical_group_for_replay(origin, value):
                    return {"id": value["group_id"]}

            class Checker:
                @staticmethod
                def _verify_failed_attempt(*args):
                    seen.append(args)
                    return {"verified": True}

            result = self.m._verify_codeql_terminal_failure(
                {"root": root, "successor": {"groups": []},
                 "frozen": {"executor": Executor(), "checker": Checker()}},
                row, "l" * 64,
            )
            self.assertEqual(result, {"verified": True})
            self.assertEqual(len(seen), 1)
            self.assertEqual(seen[0][-1], self.m.sha(completed))

    def test_historical_normalizer_sources_are_exactly_pinned(self):
        previous = self.m._load_historical_previous_helper(ROOT)
        current = self.m._load_historical_replay_helper(ROOT)
        self.assertEqual(previous.__file__, str(ROOT / self.m.HISTORICAL_REPLAY_PREVIOUS_SOURCE))
        self.assertEqual(current.__file__, str(ROOT / self.m.HISTORICAL_REPLAY_SOURCE))
        self.assertEqual(self.m.sha(Path(previous.__file__)),
                         self.m.HISTORICAL_REPLAY_PREVIOUS_SOURCE_SHA)
        self.assertEqual(self.m.sha(Path(current.__file__)),
                         self.m.HISTORICAL_REPLAY_SOURCE_SHA)

    def test_failure_context_rejects_raw_groups_without_normalized_identity(self):
        row = {"contract_sha256": self.m.HISTORICAL_REPLAY_PREVIOUS_CONTRACT_SHA,
               "attempt_id": "joern-swift-common108-attempt-03-series-01",
               "plan_commit": "c" * 40, "source_commit": "s" * 40}
        raw_origin = {"bytes_sha256": row["contract_sha256"],
                      "plan": {"source_commit": row["source_commit"]},
                      "groups": [{"id": "joern-swift-common108"}]}
        context = {"_historical_replay_contexts": {
            row["contract_sha256"]: {"validated": raw_origin,
                                     "plan_commit": row["plan_commit"]}
        }}
        with self.assertRaises(self.m.CodeQLContinuationError):
            self.m._historical_contract_context(context, row)

    def test_builder_closure_contains_normalizer_and_registered_plan_blob(self):
        spec = importlib.util.spec_from_file_location(
            "codeql_pending_builder_test",
            ROOT / "reports/releases/v0.9.2/acquisition/build-independent-pending-codeql-01.py",
        )
        builder = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(builder)
        closure = {item["path"]: item["sha256"] for item in builder.source_closure(ROOT)}
        self.assertEqual(closure[self.m.HISTORICAL_REPLAY_SOURCE],
                         self.m.HISTORICAL_REPLAY_SOURCE_SHA)
        self.assertEqual(closure[self.m.HISTORICAL_REPLAY_PREVIOUS_SOURCE],
                         self.m.HISTORICAL_REPLAY_PREVIOUS_SOURCE_SHA)
        self.assertEqual(closure[self.m.HISTORICAL_REPLAY_CONTRACT],
                         self.m.HISTORICAL_REPLAY_CONTRACT_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
