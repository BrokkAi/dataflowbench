#!/usr/bin/env python3
"""Focused, read-only tests for the Joern continuation's admission rules."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("joern-capability-continuation-01.py")
SPEC = importlib.util.spec_from_file_location("joern_capability_continuation_01_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def canonical(rows: list[dict]) -> bytes:
    return b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in rows)


class ContinuationAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_rows = [
            {"attempt_id": f"group-{n:03d}-attempt-01-series-01", "status": "completed",
             "execution_series": 1, "group_id": f"group-{n:03d}"}
            for n in range(86)
        ]
        self.old_rows[0]["status"] = "failed"
        self.old_rows[1]["status"] = "recorder-error"
        self.old_rows[2]["status"] = "failed"
        self.old_rows[3]["status"] = "recorder-error"
        # The real module binds the exact released prefix.  These pure tests
        # substitute a synthetic prefix so the state-machine checks stay fast.
        self.prefix_raw = canonical(self.old_rows)
        self.patcher = mock.patch.multiple(
            MODULE, SEALED_ROWS=86, SEALED_LEDGER_SHA=MODULE.sha_bytes(self.prefix_raw)
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_default_contract_uses_append_only_repair04_artifact(self) -> None:
        self.assertTrue(MODULE.DEFAULT_CONTRACT.endswith("joern-capability-repair-04-contract.json"))

    def test_commit_blob_verifier_streams_large_real_repository_closure(self) -> None:
        """Large real-tree requests and blobs must not deadlock cat-file --batch."""
        tree = subprocess.check_output(
            ["git", "ls-tree", "-r", "-z", "HEAD"],
            cwd=MODULE.ROOT,
        )
        objects = []
        for record in tree.split(b"\0"):
            if not record:
                continue
            header, path_raw = record.split(b"\t", 1)
            _mode, kind, object_sha = header.split()
            if kind != b"blob":
                continue
            path = path_raw.decode("utf-8")
            objects.append((object_sha.decode("ascii"), path))
            if len(objects) == 2_000:
                break
        self.assertEqual(len(objects), 2_000)
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=MODULE.ROOT, text=True
        ).strip()
        request_bytes = sum(len(f"{commit}:{path}\n".encode()) for _sha, path in objects)
        self.assertGreater(request_bytes, 64 * 1024)
        blobs = subprocess.check_output(
            ["git", "cat-file", "--batch"],
            cwd=MODULE.ROOT,
            input=b"".join(f"{object_sha}\n".encode() for object_sha, _path in objects),
        )
        bindings = {}
        blob_bytes = 0
        offset = 0
        for _object_sha, path in objects:
            header_end = blobs.index(b"\n", offset)
            fields = blobs[offset:header_end].split()
            self.assertEqual(len(fields), 3)
            size = int(fields[2])
            data_start = header_end + 1
            data_end = data_start + size
            self.assertEqual(len(blobs[data_start:data_end]), size)
            self.assertEqual(blobs[data_end:data_end + 1], b"\n")
            bindings[path] = MODULE.sha_bytes(blobs[data_start:data_end])
            blob_bytes += size
            offset = data_end + 1
        self.assertGreater(blob_bytes, 64 * 1024)

        class Timeout(Exception):
            pass

        def alarm(_signum, _frame):
            raise Timeout()

        previous = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, alarm)
        signal.setitimer(signal.ITIMER_REAL, 20.0)
        try:
            MODULE._verify_commit_blobs(
                MODULE.ROOT, commit, bindings, "large real repository closure"
            )
        except Timeout as exc:
            self.fail(f"large real repository blob verification timed out: {exc}")
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def test_prefix_preserves_history_and_allows_only_two_tail_rows(self) -> None:
        joern = {"attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
                 "execution_series": 1, "status": "completed", "exit_code": 0,
                 "timed_out": False, "capacity_loss": None}
        codeql = {"attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
                  "execution_series": 1, "status": "completed", "exit_code": 0,
                  "timed_out": False, "capacity_loss": None}
        rows = self.old_rows + [joern, codeql]
        raw = canonical(rows)
        self.assertEqual(MODULE._check_prefix(Path("."), rows, raw), self.old_rows)
        self.assertEqual(MODULE._tail(rows, final=True), [joern, codeql])

    def test_fourth_joern_attempt_is_rejected(self) -> None:
        joern = {"attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
                 "execution_series": 1, "status": "completed", "exit_code": 0}
        extra = dict(joern, attempt_id="joern-swift-common108-attempt-04-series-01")
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.old_rows + [joern, extra], final=False)

    def test_codeql_cannot_precede_joern(self) -> None:
        codeql = {"attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
                  "execution_series": 1, "status": "completed", "exit_code": 0}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.old_rows + [codeql], final=False)

    def test_failed_joern_cannot_unlock_codeql(self) -> None:
        joern = {"attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
                 "execution_series": 1, "status": "failed", "exit_code": 1}
        codeql = {"attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
                  "execution_series": 1, "status": "completed", "exit_code": 0}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.old_rows + [joern, codeql], final=False)

    def test_completed_joern_requires_successful_terminal_state(self) -> None:
        joern = {"attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
                 "execution_series": 1, "status": "completed", "exit_code": 1,
                 "timed_out": False, "capacity_loss": None}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.old_rows + [joern], final=False)

    def test_execute_result_requires_successful_terminal_state(self) -> None:
        failed = {"group_id": MODULE.JOERN_GROUP,
                  "attempt_id": MODULE.JOERN_ATTEMPT,
                  "status": "failed", "exit_code": 1,
                  "timed_out": False, "capacity_loss": None}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._require_execution_success(MODULE.JOERN_GROUP, failed)

        succeeded = dict(failed, status="completed", exit_code=0)
        self.assertIs(MODULE._require_execution_success(MODULE.JOERN_GROUP, succeeded), succeeded)

    def test_runtime_reservation_overlay_changes_only_expiry(self) -> None:
        original = {"expires_at_unix_seconds": 1792560780.680937,
                    "exclusive_analyzer_slot": True, "serial_analyzers": 1,
                    "owner": "reviewed-owner"}
        validated = {"plan": {"resource_reservation": original}}
        runtime = MODULE._runtime_plan_with_cutoff_reservation(validated)
        self.assertEqual(original["expires_at_unix_seconds"], 1792560780.680937)
        self.assertEqual(runtime["plan"]["resource_reservation"]["expires_at_unix_seconds"],
                         1792791180.680937)
        self.assertEqual({k: v for k, v in runtime["plan"]["resource_reservation"].items()
                          if k != "expires_at_unix_seconds"},
                         {k: v for k, v in original.items() if k != "expires_at_unix_seconds"})

    def test_live_execution_gate_checks_reserve_and_127_gib_resource_hook(self) -> None:
        """Live gates load the hash-bound receipt before reading its phase map."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay.json"
            replay_raw = json.dumps({
                "status": "continuation-preflight-passed",
                "ledger_rows": MODULE.SEALED_ROWS,
                "selected_groups": 82,
                "known_stale": 0,
            }, sort_keys=True, separators=(",", ":")).encode()
            replay_path.write_bytes(replay_raw)
            replay_ref = {"path": "replay.json", "sha256": MODULE.sha_bytes(replay_raw)}
            continuation_test = root / Path(*MODULE.CONTINUATION_TEST.split("/"))
            continuation_test.parent.mkdir(parents=True)
            continuation_test.write_bytes(b"continuation test\n")
            artifacts = {
                key: {"path": f"artifacts/{key}.json", "sha256": "a" * 64}
                for key in ("continuation_source", "continuation_contract",
                            "repaired_plan", "capability_evidence", "joern_shim")
            }
            manifest = {
                "execution_admission": None,
                "authorization": {"path": MODULE.AUTHORIZATION_PATH,
                                   "sha256": MODULE.AUTHORIZATION_SHA},
                "ledger_prefix": {"path": MODULE.LEDGER,
                                  "sha256": MODULE.SEALED_LEDGER_SHA,
                                  "rows": MODULE.SEALED_ROWS},
                "source_commit": "1" * 40,
                "plan_commit": "2" * 40,
                "final_review": {"path": "review.json", "sha256": "b" * 64},
                "artifacts": artifacts,
            }
            receipt = {
                "schema": "v092-joern-capability-continuation-admission/v1",
                "status": "ready-to-execute",
                "automatic_retry": False,
                "release_group_attempt": False,
                "original_origin_utc": MODULE.ORIGIN,
                "cutoff_utc": MODULE.CUTOFF,
                "total_wall_budget_seconds": MODULE.TOTAL_WALL_SECONDS,
                "authorization": manifest["authorization"],
                "ledger_prefix": manifest["ledger_prefix"],
                "source_commit": manifest["source_commit"],
                "plan_commit": manifest["plan_commit"],
                "final_review": manifest["final_review"],
                "artifacts": {
                    **artifacts,
                    "continuation_test": {
                        "path": MODULE.CONTINUATION_TEST,
                        "sha256": MODULE.sha(continuation_test),
                    },
                },
                "retained_replay_output": replay_ref,
                "phase_remaining_reserved_seconds": {
                    MODULE.JOERN_GROUP: MODULE.FULL_REMAINING_RESERVE_SECONDS,
                    MODULE.CODEQL_GROUP: MODULE.CODEQL_PHASE_REMAINING_RESERVE_SECONDS,
                },
                "no_foreign_processes": True,
                "resource_floor_bytes": MODULE.LIVE_RESOURCE_FLOOR_BYTES,
                "resource_floor_checked": True,
                "remaining_reserved_seconds": MODULE.FULL_REMAINING_RESERVE_SECONDS,
                "exclusive_lock_checked": True,
                "fresh_attempt_namespaces": True,
                "fresh_sidecar_namespaces": True,
            }
            admission_raw = (json.dumps(receipt, sort_keys=True,
                                         separators=(",", ":")) + "\n").encode()
            (root / "admission.json").write_bytes(admission_raw)
            admission_ref = {"path": "admission.json",
                             "sha256": MODULE.sha_bytes(admission_raw)}
            manifest["execution_admission"] = admission_ref
            observed = []
            executor = SimpleNamespace(
                _check_resources=lambda path, minimum: observed.append((path, minimum))
            )
            context = {"executor": executor, "root": root, "manifest": manifest}
            cutoff = 1792791180.680937
            with mock.patch.object(MODULE.time, "time", return_value=cutoff - 29400 + 1):
                with self.assertRaises(MODULE.ContinuationError):
                    MODULE._require_live_execution_gates(context, MODULE.JOERN_GROUP)
            with mock.patch.object(MODULE.time, "time", return_value=cutoff - 29400 - 10):
                MODULE._require_live_execution_gates(context, MODULE.JOERN_GROUP)
            self.assertEqual(observed, [(root, 127 * 1024 ** 3)])

    def test_attempt_number_field_cannot_override_attempt_id(self) -> None:
        joern = {"attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
                 "execution_series": 1, "attempt_number": 4, "status": "completed",
                 "exit_code": 0, "timed_out": False, "capacity_loss": None}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.old_rows + [joern], final=False)

    def test_safe_binding_rejects_parent_escape_and_symlink(self) -> None:
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._relative("../outside.json")
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._relative("/absolute.json")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real.json").write_bytes(b"{}")
            (root / "link.json").symlink_to(root / "real.json")
            with self.assertRaises(MODULE.ContinuationError):
                MODULE._read(root, "link.json")

    def test_fresh_control_reference_walk_is_recursive(self) -> None:
        value = {"raw": {"path": "capture/raw.json", "sha256": "a" * 64},
                 "records": [{"command": {"path": "capture/command.json",
                                            "sha256": "b" * 64}}]}
        self.assertEqual(sorted(MODULE._path_sha_refs(value)), [
            ("capture/command.json", "b" * 64),
            ("capture/raw.json", "a" * 64),
        ])

    def test_fresh_control_graph_rejects_missing_nested_native_output(self) -> None:
        """A nested JSON reference cannot be omitted from the committed closure."""
        prefix = MODULE.FRESH_CAPTURE_PREFIX
        run_path = prefix + "run.json"
        raw_path = prefix + "raw.json"
        command_path = prefix + "command.json"
        native_path = prefix + "native-output.bin"

        def write(path: str, value: object) -> bytes:
            raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
            target = Path(self.tmp.name) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            return raw

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        native = b"native output\n"
        native_target = Path(self.tmp.name) / native_path
        native_target.parent.mkdir(parents=True, exist_ok=True)
        native_target.write_bytes(native)
        command_raw = write(command_path, {"native_output": {
            "path": native_path, "sha256": MODULE.sha_bytes(native)
        }})
        raw_raw = write(raw_path, {"command": {
            "path": command_path, "sha256": MODULE.sha_bytes(command_raw)
        }})
        write(run_path, {"raw": {"path": raw_path, "sha256": MODULE.sha_bytes(raw_raw)}})

        closure = MODULE._fresh_control_index_closure(Path(self.tmp.name), [run_path])
        self.assertEqual(closure[native_path], MODULE.sha_bytes(native))
        native_target.unlink()
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._fresh_control_index_closure(Path(self.tmp.name), [run_path])

    def test_source_input_map_preserves_optional_inherited_role(self) -> None:
        value = [
            {"path": "reports/recovery.json", "sha256": "a" * 64,
             "role": "resource-recovery-evidence"},
            {"path": "reports/plain.json", "sha256": "b" * 64},
        ]
        self.assertEqual(MODULE._source_input_map(value, "inputs"), {
            "reports/recovery.json": ("a" * 64, "resource-recovery-evidence", True),
            "reports/plain.json": ("b" * 64, "release-input", False),
        })
        self.assertEqual(MODULE._normalized_source_inputs(value, "inputs"), [
            {"path": "reports/recovery.json", "sha256": "a" * 64,
             "role": "resource-recovery-evidence"},
            {"path": "reports/plain.json", "sha256": "b" * 64,
             "role": "release-input"},
        ])
        self.assertEqual(MODULE._normalized_source_inputs(
            value, "inputs", {"reports/plain.json": "qualification-evidence"}
        )[1], {
            "path": "reports/plain.json", "sha256": "b" * 64,
            "role": "qualification-evidence",
        })

    def test_frozen_base_raw_inputs_get_actual_qualification_role_enrichment(self) -> None:
        raw = json.loads((MODULE.ROOT / MODULE.BASE_CONTRACT).read_bytes())
        qualification = {
            name: {"path": binding["evidence"]["path"]}
            for name, binding in raw["qualifications"].items()
        }
        effective = MODULE._effective_source_input_map(
            raw["source_inputs"], "raw frozen base source inputs",
            MODULE._qualification_role_overrides({"qualification": qualification}),
        )
        self.assertEqual(len(effective), 789)
        self.assertEqual(sum(role == "resource-recovery-evidence"
                             for _digest, role, _explicit in effective.values()), 4)
        self.assertEqual(sum(role == "qualification-evidence"
                             for _digest, role, _explicit in effective.values()), 8)
        self.assertEqual(sum(role == "release-input"
                             for _digest, role, _explicit in effective.values()), 777)

    def test_contract_contexts_are_mixed_by_exact_contract_digest(self) -> None:
        base = {"validated": {"plan": {"source_commit": MODULE.BASE_SOURCE_COMMIT}},
                "plan_commit": MODULE.BASE_PLAN_COMMIT}
        repaired = {"validated": {"plan": {"source_commit": "a" * 40},
                                   "bytes_sha256": "c" * 64},
                    "plan_commit": "b" * 40}
        context = {"contexts": {MODULE.BASE_SHA: base, "c" * 64: repaired},
                   "repaired": repaired}
        row = {"contract_sha256": MODULE.BASE_SHA, "group_id": MODULE.JOERN_GROUP,
               "attempt_id": "joern-swift-common108-attempt-01-series-01"}
        self.assertIs(MODULE._context_for_row(context, row), base)
        row["contract_sha256"] = "c" * 64
        row["group_id"] = MODULE.JOERN_GROUP
        row["attempt_id"] = MODULE.JOERN_ATTEMPT
        self.assertIs(MODULE._context_for_row(context, row), repaired)

    def test_codeql_continuation_requires_repaired_context(self) -> None:
        base = {"validated": {"plan": {"source_commit": MODULE.BASE_SOURCE_COMMIT}},
                "plan_commit": MODULE.BASE_PLAN_COMMIT}
        repaired = {"validated": {"plan": {"source_commit": "a" * 40},
                                   "bytes_sha256": "c" * 64},
                    "plan_commit": "b" * 40}
        context = {"contexts": {MODULE.BASE_SHA: base, "c" * 64: repaired},
                   "repaired": repaired}
        row = {"contract_sha256": MODULE.BASE_SHA, "group_id": MODULE.CODEQL_GROUP,
               "attempt_id": MODULE.CODEQL_ATTEMPT}
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._context_for_row(context, row)


if __name__ == "__main__":
    unittest.main()
