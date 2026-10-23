#!/usr/bin/env python3
"""Focused, read-only tests for the Joern continuation's admission rules."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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

    def test_default_contract_uses_append_only_repair02_artifact(self) -> None:
        self.assertTrue(MODULE.DEFAULT_CONTRACT.endswith("joern-capability-repair-02-contract.json"))

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
        observed = []
        executor = SimpleNamespace(
            _check_resources=lambda root, minimum: observed.append((root, minimum))
        )
        context = {
            "executor": executor,
            "root": Path("."),
            "manifest": {"execution_admission": {
                "phase_remaining_reserved_seconds": {
                    MODULE.JOERN_GROUP: 29400,
                    MODULE.CODEQL_GROUP: 28032,
                }
            }},
        }
        with mock.patch.object(MODULE.time, "time",
                               return_value=1792791180.680937 - 29400 + 1):
            with self.assertRaises(MODULE.ContinuationError):
                MODULE._require_live_execution_gates(context, MODULE.JOERN_GROUP)
        with mock.patch.object(MODULE.time, "time",
                               return_value=1792791180.680937 - 29400 - 10):
            MODULE._require_live_execution_gates(context, MODULE.JOERN_GROUP)
        self.assertEqual(observed, [(Path("."), 127 * 1024 ** 3)])

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
