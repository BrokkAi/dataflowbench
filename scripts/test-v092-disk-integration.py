#!/usr/bin/env python3
"""Focused executor integration tests for C4 disk-guard failure handling."""

from __future__ import annotations

import contextlib
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


EXECUTOR_PATH = Path(__file__).with_name("execute-release-v092.py")
EXECUTOR_SPEC = importlib.util.spec_from_file_location("execute_release_v092_test", EXECUTOR_PATH)
assert EXECUTOR_SPEC is not None and EXECUTOR_SPEC.loader is not None
executor = importlib.util.module_from_spec(EXECUTOR_SPEC)
EXECUTOR_SPEC.loader.exec_module(executor)


class FakeDiskGuardError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code

    def as_dict(self) -> dict:
        return {"code": self.code, "message": str(self)}


class FakeDiskGuard:
    fail_check = False
    failure_code = "launch_floor"

    def __init__(self, **_kwargs: object) -> None:
        self.checks = 0

    def check(self, **_kwargs: object) -> dict:
        self.checks += 1
        if self.fail_check:
            raise FakeDiskGuardError(self.failure_code, "launch preflight refused")
        return {}

    def check_capacity(self, **_kwargs: object) -> dict:
        return {}

    @staticmethod
    def logical_size(_paths) -> int:
        return 0


class FakeLoader:
    def exec_module(self, module: types.SimpleNamespace) -> None:
        module.DiskGuard = FakeDiskGuard
        module.DiskGuardError = FakeDiskGuardError


class DiskGuardExecutorTests(unittest.TestCase):
    def make_validated(self, root: Path) -> tuple[dict, Path, Path, Path, Path]:
        group_id = "guard-test"
        attempt = root / "attempts" / "guard-test-attempt-01-series-01"
        execution = root / "execution" / "series-01" / group_id / "attempt-01"
        cache = root / "cache" / "series-01" / group_id / "attempt-01"
        ledger = root / "ledger.jsonl"
        group = {
            "id": group_id,
            "tool": "fake-tool",
            "argv": ["fake-tool"],
            "output_roots": ["out"],
            "case_ids": ["case-1"],
            "deadline_seconds": 30,
        }
        plan = {
            "execution_authorized": True,
            "execution_series": 1,
            "source_commit": "a" * 40,
            "runner_source_sha256": "b" * 64,
            "population": {"path": "populations/v0.9.0", "sha256": "c" * 64},
            "resource_recovery": {"path": "manifest.json", "sha256": "d" * 64},
            "resource_reservation": {
                "exclusive_analyzer_slot": True,
                "expires_at_unix_seconds": 4_000_000_000,
            },
            "resource_budget": {
                "minimum_launch_free_gib": 110,
                "protected_reserve_gib": 40,
                "scratch_gib": 24,
                "proposed_total_retention_ceiling_gib": 24,
            },
            "resource_guards": {"stop_free_gib": 48, "working_set_gib": 12},
            "groups": [group],
        }
        validated = {
            "plan": plan,
            "repo_root": root,
            "groups": [{"id": group_id, "reports": [], "identity_components": []}],
            "source_inputs": [],
            "tools": {"fake-tool": {}},
            "bytes_sha256": "e" * 64,
            "fixture_revision": "sha256:" + "f" * 64,
            "total_wall_budget_seconds": 3600,
            "qualification": {},
        }
        return validated, attempt, execution, cache, ledger

    def patch_executor(self, validated: dict, attempt: Path, execution: Path,
                       cache: Path, ledger: Path, materialize, run_process):
        patches = contextlib.ExitStack()
        patches.enter_context(patch.object(executor, "_exclusive_lock", contextlib.nullcontext))
        patches.enter_context(patch.object(executor, "_process_table", return_value=""))
        patches.enter_context(patch.object(executor, "_contenders", return_value=[]))
        patches.enter_context(patch.object(executor, "_assert_contract_snapshot", return_value="1" * 40))
        patches.enter_context(patch.object(executor, "_matrix_elapsed_wall", return_value=0))
        patches.enter_context(patch.object(executor, "_assert_source_snapshot", return_value=None))
        patches.enter_context(patch.object(executor, "_source_file", return_value=b"source"))
        patches.enter_context(patch.object(executor, "_check_tool_file", return_value=None))
        patches.enter_context(patch.object(executor, "_require_group_qualification", return_value={}))
        patches.enter_context(patch.object(
            executor, "_assert_fresh",
            return_value=(attempt, execution, cache, ledger, attempt.name),
        ))
        patches.enter_context(patch.object(
            executor, "_child_environment",
            return_value={"HOME": str(attempt / "home"), "TMPDIR": str(attempt / "tmp")},
        ))
        patches.enter_context(patch.object(executor, "_matrix_capacity_paths", return_value=([], [])))
        patches.enter_context(patch.object(executor, "_verified_completed_groups", return_value=set()))
        patches.enter_context(patch.object(executor, "_materialize_source", side_effect=materialize))
        patches.enter_context(patch.object(executor, "_run_process", side_effect=run_process))
        fake_spec = types.SimpleNamespace(loader=FakeLoader())
        patches.enter_context(patch.object(executor.importlib.util, "spec_from_file_location",
                                           return_value=fake_spec))
        patches.enter_context(patch.object(executor.importlib.util, "module_from_spec",
                                           return_value=types.SimpleNamespace()))
        return patches

    def test_mid_materialization_refusal_is_capacity_lost_and_preserves_partial_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            validated, attempt, execution, cache, ledger = self.make_validated(root)

            def materialize(_repo: Path, _commit: str, destination: Path, _inputs,
                            *, preflight_only=False, **_kwargs):
                if preflight_only:
                    return 128
                destination.mkdir(parents=True)
                (destination / "src").mkdir()
                (destination / "src" / "partial.rs").write_bytes(b"partial evidence")
                raise FakeDiskGuardError("stop_floor", "free space dropped during extraction")

            def forbidden_process(*_args, **_kwargs):
                self.fail("analyzer process must not start after source extraction refusal")

            patches = self.patch_executor(validated, attempt, execution, cache, ledger,
                                          materialize, forbidden_process)
            with patches:
                row = executor.run_group(validated, "guard-test")

            self.assertEqual(row["status"], "capacity-lost")
            self.assertEqual(row["capacity_loss"]["code"], "stop_floor")
            self.assertEqual(row["exit_code"], 125)
            self.assertFalse(row["timed_out"])
            self.assertEqual(row["duration_seconds"], 0.0)
            self.assertTrue((execution / "src" / "partial.rs").is_file())
            self.assertEqual(row["stdout"]["bytes"], 0)
            self.assertEqual(row["stderr"]["bytes"], 0)
            self.assertNotIn("process_ownership", row)
            self.assertTrue((attempt / "started.json").is_file())
            self.assertTrue((attempt / "completed.json").is_file())
            self.assertTrue(ledger.is_file())

    def test_launch_projection_refusal_creates_no_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            validated, attempt, execution, cache, ledger = self.make_validated(root)
            FakeDiskGuard.fail_check = True

            def materialize(_repo: Path, _commit: str, _destination: Path, _inputs,
                            *, preflight_only=False, **_kwargs):
                self.assertTrue(preflight_only)
                return 128

            def forbidden_process(*_args, **_kwargs):
                self.fail("analyzer process must not run after launch preflight refusal")

            patches = self.patch_executor(validated, attempt, execution, cache, ledger,
                                          materialize, forbidden_process)
            try:
                with patches:
                    with self.assertRaises(FakeDiskGuardError):
                        executor.run_group(validated, "guard-test")
            finally:
                FakeDiskGuard.fail_check = False

            self.assertFalse(attempt.exists())
            self.assertFalse(execution.exists())
            self.assertFalse(cache.exists())
            self.assertFalse(ledger.exists())

    def test_noncapacity_disk_error_is_recorder_error_not_capacity_lost(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            validated, attempt, execution, cache, ledger = self.make_validated(root)

            def materialize(_repo: Path, _commit: str, destination: Path, _inputs,
                            *, preflight_only=False, **_kwargs):
                if preflight_only:
                    return 128
                destination.mkdir(parents=True)
                for name in ("src", "cases", "populations"):
                    (destination / name).mkdir()
                return None

            def disk_integrity_failure(_argv, _cwd, _env, stdout: Path, stderr: Path,
                                      _timeout, *, ownership, **_kwargs):
                stdout.write_bytes(b"")
                stderr.write_bytes(b"")
                return 125, False, 0.0, {
                    "code": "source_changed",
                    "message": "source changed during guarded materialization",
                }

            patches = self.patch_executor(validated, attempt, execution, cache, ledger,
                                          materialize, disk_integrity_failure)
            with patches:
                row = executor.run_group(validated, "guard-test")

            self.assertEqual(row["status"], "recorder-error")
            self.assertEqual(row["disk_guard_error"]["code"], "source_changed")
            self.assertIsNone(row["capacity_loss"])
            self.assertNotIn("process_ownership", row)
            self.assertEqual(row["stdout"]["bytes"], 0)
            self.assertEqual(row["stderr"]["bytes"], 0)
            self.assertTrue((attempt / "completed.json").is_file())
            self.assertTrue(ledger.is_file())

    def test_noncapacity_accounting_error_is_raised_from_active_monitor(self) -> None:
        FakeDiskGuard.fail_check = True
        FakeDiskGuard.failure_code = "accounting_path_unavailable"
        try:
            with self.assertRaises(FakeDiskGuardError) as caught:
                executor._capacity_loss(Path("/tmp"), [], 1024,
                                        disk_guard=FakeDiskGuard())
            self.assertEqual(caught.exception.code, "accounting_path_unavailable")
        finally:
            FakeDiskGuard.fail_check = False
            FakeDiskGuard.failure_code = "launch_floor"

    def test_capture_plan_rejects_changed_file_before_target_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            execution = root / "execution"
            output_root = execution / "out"
            output_root.mkdir(parents=True)
            source = output_root / "result.bin"
            source.write_bytes(b"captured size")
            capture_root = root / "attempt" / "capture"
            helper_spec = importlib.util.spec_from_file_location(
                "v092_disk_guard_capture_test", Path(__file__).with_name("v092_disk_guard.py"),
            )
            assert helper_spec is not None and helper_spec.loader is not None
            helper = importlib.util.module_from_spec(helper_spec)
            helper_spec.loader.exec_module(helper)
            guard = helper.DiskGuard(
                launch_floor_bytes=110,
                protected_reserve_bytes=40,
                stop_margin_bytes=8,
                stop_floor_bytes=48,
                scratch_ceiling_bytes=1024,
                retention_ceiling_bytes=1024,
                working_ceiling_bytes=1024,
                disk_usage=lambda _path: 10_000,
            )
            planned = executor._copy_tree(
                output_root, execution, execution, capture_root,
                disk_guard=guard,
                preflight_only=True,
            )
            source.write_bytes(b"changed after the whole-tree preflight")

            with self.assertRaises(helper.DiskGuardError) as caught:
                executor._copy_tree(
                    output_root, execution, execution, capture_root,
                    disk_guard=guard,
                    disk_guard_module=helper,
                    planned_files=planned,
                )

            self.assertEqual(caught.exception.code, "source_changed")
            self.assertFalse(planned[0]["target"].exists())


if __name__ == "__main__":
    unittest.main()
