#!/usr/bin/env python3
"""Focused selection tests for retained C2/C3 evidence under C4."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("check-release-v092.py")
SPEC = importlib.util.spec_from_file_location("check_release_v092_resource_tested", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

DISK_GUARD_PATH = Path(__file__).with_name("v092_disk_guard.py")
DISK_GUARD_SPEC = importlib.util.spec_from_file_location("v092_disk_guard_checker_test", DISK_GUARD_PATH)
assert DISK_GUARD_SPEC is not None and DISK_GUARD_SPEC.loader is not None
disk_guard = importlib.util.module_from_spec(DISK_GUARD_SPEC)
DISK_GUARD_SPEC.loader.exec_module(disk_guard)


class ResourceRecoverySelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current_sha = "d" * 64
        self.current_source = "e" * 40
        self.current_plan_commit = "f" * 40
        self.manifest_sha = "5" * 64
        self.c1_sha = checker.RESOURCE_C1_SHA256
        self.c2_sha = checker.RESOURCE_C2_SHA256
        self.c3_sha = checker.RESOURCE_C3_SHA256
        self.c1_source = checker.SCOPED_C1_SOURCE_COMMIT
        self.c2_source = checker.SCOPED_C2_SOURCE_COMMIT
        self.c3_source = checker.RESOURCE_C3_SOURCE_COMMIT
        self.c1_commit = checker.SCOPED_C1_PLAN_COMMIT
        self.c2_commit = checker.SCOPED_C2_PLAN_COMMIT
        self.c3_commit = checker.RESOURCE_C3_PLAN_COMMIT

        self.groups = []
        for index in range(checker.EXPECTED_GROUPS):
            if index == 0:
                group_id, tool, family = "bifrost-c-kernel", "bifrost", "bifrost"
            elif index == 25:
                group_id, tool, family = "codeql-java-modeling", "codeql", "codeql"
            else:
                group_id, tool, family = f"fixture-group-{index:03d}", "bifrost", "bifrost"
            self.groups.append({
                "id": group_id,
                "tool": tool,
                "family": family,
                "case_ids": [f"case-{index:03d}"],
                "maximum_attempts": 2,
                "deadline_seconds": 60,
                "output_roots": [f"reports/raw/{group_id}"],
                "argv": ["/original/runner", "run", group_id],
                "environment": {"LANG": "C.UTF-8"},
            })
        self.group_by_id = {item["id"]: item for item in self.groups}
        self.tools = {"bifrost": {"path": "/tools/bifrost"}, "codeql": {"path": "/tools/codeql"}}
        self.tool_components = {"codeql": ["codeql-packs"]}
        self.scoped_ref = {
            "path": "reports/releases/v0.9.2/qualification/scoped-recovery-01/manifest.json",
            "sha256": "6" * 64,
        }
        self.plan = {
            "execution_series": 1,
            "maximum_attempts_per_group": 2,
            "total_wall_budget_seconds": 102960,
            "source_commit": self.current_source,
            "tools": json.loads(json.dumps(self.tools)),
            "tool_components": json.loads(json.dumps(self.tool_components)),
            "scoped_recovery": json.loads(json.dumps(self.scoped_ref)),
            "resource_recovery": {
                "path": checker.RESOURCE_RECOVERY_MANIFEST_PATH.as_posix(),
                "sha256": self.manifest_sha,
            },
            "groups": json.loads(json.dumps(self.groups)),
        }
        self.contexts = {
            self.c1_sha: self._context(self.c1_sha, self.c1_source, self.c1_commit),
            self.c2_sha: self._context(self.c2_sha, self.c2_source, self.c2_commit),
            self.c3_sha: self._context(self.c3_sha, self.c3_source, self.c3_commit),
        }
        self.prefix = []
        self.retained_completed = {}
        self.retained_failures = {}

        # The C1 failure precedes its C2 completion; the C2 modeling failure
        # precedes its C3 completion. All other historical completions retain
        # the contract under which they were originally measured.
        self._append("bifrost-c-kernel", 1, self.c1_sha, self.c1_commit,
                     self.c1_source, "recorder-error")
        self._append("bifrost-c-kernel", 2, self.c2_sha, self.c2_commit,
                     self.c2_source, "completed")
        for group in self.groups[1:25]:
            self._append(group["id"], 1, self.c2_sha, self.c2_commit,
                         self.c2_source, "completed")
        self._append("codeql-java-modeling", 1, self.c2_sha, self.c2_commit,
                     self.c2_source, "failed")
        self._append("codeql-java-modeling", 2, self.c3_sha, self.c3_commit,
                     self.c3_source, "completed")
        for group in self.groups[26:55]:
            self._append(group["id"], 1, self.c3_sha, self.c3_commit,
                         self.c3_source, "completed")

        self.manifest = {
            "schema": "v092-resource-recovery-manifest/v1",
            "original_wall_origin_utc": "2026-10-20T00:57:00.680937+00:00",
            "deadline_utc": "2026-10-21T05:33:00.680937+00:00",
            "execution_series": 1,
            "total_wall_budget_seconds": 102960,
            "maximum_attempts_per_group": 2,
            "retained_completed": [],
            "retained_failures": [],
        }
        for row, line_sha, context_sha in self.prefix:
            item = self._manifest_item(row, line_sha)
            record = {
                "row": row,
                "ledger_line_sha256": line_sha,
                "context_sha256": context_sha,
                "plan_commit": row["plan_commit"],
                "attempt_number": int(row["attempt_id"].split("-attempt-")[1][:2]),
            }
            if row["status"] == "completed":
                self.manifest["retained_completed"].append(item)
                self.retained_completed[row["group_id"]] = record
            else:
                self.manifest["retained_failures"].append(item)
                self.retained_failures[row["attempt_id"]] = record

        self.rows = [(row, line_sha) for row, line_sha, _context in self.prefix]
        for group in self.groups[55:]:
            self.rows.append((self._row(group["id"], 1, self.current_sha,
                                        self.current_plan_commit, self.current_source, "completed"), None))
        self._rehash_rows()
        self.resource = {
            "manifest": self.manifest,
            "manifest_sha256": self.manifest_sha,
            "contexts": self.contexts,
            "prefix_rows": [(row, line_sha) for row, line_sha, _context in self.prefix],
            "retained_completed": self.retained_completed,
            "retained_failures": self.retained_failures,
        }

    def _context(self, contract_sha, source_commit, plan_commit):
        plan = {
            "source_commit": source_commit,
            "tools": json.loads(json.dumps(self.tools)),
            "tool_components": json.loads(json.dumps(self.tool_components)),
            "scoped_recovery": json.loads(json.dumps(self.scoped_ref)),
            "groups": json.loads(json.dumps(self.groups)),
        }
        return {"validated": {"bytes_sha256": contract_sha, "plan": plan},
                "plan_commit": plan_commit}

    @staticmethod
    def _line_sha(row):
        raw = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        return hashlib.sha256(raw).hexdigest()

    def _row(self, group_id, number, contract_sha, plan_commit, source, status):
        group = self.group_by_id[group_id]
        return {
            "group_id": group_id,
            "attempt_id": f"{group_id}-attempt-{number:02d}-series-01",
            "execution_series": 1,
            "plan_commit": plan_commit,
            "source_commit": source,
            "contract_sha256": contract_sha,
            "tool": group["tool"],
            "case_ids": group["case_ids"],
            "status": status,
        }

    def _append(self, group_id, number, contract_sha, plan_commit, source, status):
        row = self._row(group_id, number, contract_sha, plan_commit, source, status)
        self.prefix.append((row, self._line_sha(row), contract_sha))

    def _manifest_item(self, row, line_sha):
        attempt_id = row["attempt_id"]
        receipt_base = f"reports/releases/v0.9.2/attempts/{attempt_id}"
        return {
            "group_id": row["group_id"],
            "attempt_id": attempt_id,
            "status": row["status"],
            "contract_sha256": row["contract_sha256"],
            "source_commit": row["source_commit"],
            "plan_commit": row["plan_commit"],
            "ledger_line_sha256": line_sha,
            "started_receipt": {"path": f"{receipt_base}/started.json", "sha256": "8" * 64},
            "completed_receipt": {"path": f"{receipt_base}/completed.json", "sha256": "9" * 64},
        }

    def _rehash_rows(self):
        self.rows = [(row, line_sha or self._line_sha(row)) for row, line_sha in self.rows]

    def _select(self):
        self._rehash_rows()
        return checker._select_resource_recovery_attempts(
            self.plan, self.current_sha, self.rows, self.resource,
        )

    def test_retained_selection_preserves_original_c2_and_c3_contract_origins(self):
        _plan_commit, selected, failures = self._select()
        self.assertEqual(len(selected), checker.EXPECTED_GROUPS)
        self.assertEqual(sum(item[6] and item[5] == self.c2_sha for item in selected.values()), 25)
        self.assertEqual(sum(item[6] and item[5] == self.c3_sha for item in selected.values()), 30)
        self.assertEqual(sum(not item[6] for item in selected.values()), 29)
        self.assertEqual(selected["bifrost-c-kernel"][5], self.c2_sha)
        self.assertEqual(selected["bifrost-c-kernel"][4], self.c2_commit)
        self.assertEqual(selected["bifrost-c-kernel"][0]["source_commit"], self.c2_source)
        self.assertEqual(selected["codeql-java-modeling"][5], self.c3_sha)
        self.assertEqual(selected["codeql-java-modeling"][4], self.c3_commit)
        self.assertEqual(selected["codeql-java-modeling"][0]["source_commit"], self.c3_source)
        self.assertEqual(len(failures), 2)
        self.assertEqual({(item[0]["contract_sha256"], item[4]) for item in failures},
                         {(self.c1_sha, self.c1_commit), (self.c2_sha, self.c2_commit)})

    def test_unknown_post_prefix_contract_is_rejected(self):
        row, _line_sha = self.rows[-1]
        row["contract_sha256"] = self.c2_sha
        self._rehash_rows()
        with self.assertRaisesRegex(checker.EvidenceError, "after the C1/C2/C3 prefix"):
            self._select()

    def test_completed_c4_attempt_cannot_be_rerun(self):
        completed, _line_sha = self.rows[-1]
        group_id = completed["group_id"]
        rerun = self._row(group_id, 2, self.current_sha, self.current_plan_commit,
                          self.current_source, "completed")
        self.rows.append((rerun, self._line_sha(rerun)))
        with self.assertRaisesRegex(checker.EvidenceError, "one final completed attempt"):
            self._select()

    def test_c4_attempt_cap_cannot_be_exceeded(self):
        first = self.rows[-1][0]
        group_id = first["group_id"]
        failed_first = self._row(group_id, 1, self.current_sha, self.current_plan_commit,
                                 self.current_source, "failed")
        retry = self._row(group_id, 2, self.current_sha, self.current_plan_commit,
                          self.current_source, "failed")
        over_cap = self._row(group_id, 3, self.current_sha, self.current_plan_commit,
                             self.current_source, "completed")
        self.rows[-1] = (failed_first, self._line_sha(failed_first))
        self.rows.extend(((retry, self._line_sha(retry)), (over_cap, self._line_sha(over_cap))))
        with self.assertRaisesRegex(checker.EvidenceError, "attempt numbering or source/contract identity"):
            self._select()

    def test_all_c4_rows_must_share_one_plan_commit(self):
        row, _line_sha = self.rows[-1]
        row["plan_commit"] = "a" * 40
        self._rehash_rows()
        with self.assertRaisesRegex(checker.EvidenceError, "one exact committed contract"):
            self._select()

    def test_c4_plan_commit_must_be_present_on_shared_head(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            contract = root / "reports/releases/v0.9.2/execution-v4/contract.json"
            contract.parent.mkdir(parents=True)
            contract_bytes = b"exact committed C4 contract\n"
            contract.write_bytes(contract_bytes)
            validated = {
                "path": str(contract),
                "bytes_sha256": hashlib.sha256(contract_bytes).hexdigest(),
                "plan": {"source_commit": self.current_source},
            }
            with patch.object(checker.subprocess, "check_output", side_effect=[
                    contract_bytes, "a" * 40, ""]), patch.object(checker, "_assert_ancestor") as ancestor:
                checker._assert_committed_contract(root, validated, self.current_plan_commit)
            self.assertEqual(ancestor.call_args_list[0].args[1:], (
                self.current_plan_commit, "a" * 40, "execution-plan commit",
            ))
            self.assertEqual(ancestor.call_args_list[1].args[1:], (
                self.current_source, self.current_plan_commit, "source commit to execution-plan commit",
            ))


class ResourceGuardFailureReplayTests(unittest.TestCase):
    def _write_failure(self, root: Path, status: str, *, guard_error: dict,
                       as_capacity_loss: bool) -> tuple[dict, dict, dict, str, int, str]:
        group_id = "resource-guard-test"
        attempt_id = f"{group_id}-attempt-01-series-01"
        plan_commit = "f" * 40
        environment = {"HOME": "/task/home", "TMPDIR": "/task/tmp"}
        tool_binding = {"path": "/tools/fake", "sha256": "1" * 64}
        population = {"path": "populations/v0.9.0", "sha256": "2" * 64}
        group = {
            "id": group_id,
            "tool": "fake-tool",
            "identity_components": [],
            "argv": ["/tools/fake", "analyze"],
            "output_roots": ["reports/raw/resource-guard-test"],
            "case_ids": ["case-001"],
            "deadline_seconds": 30,
        }
        plan = {
            "execution_series": 1,
            "source_commit": "e" * 40,
            "runner_source_sha256": "3" * 64,
            "population": population,
            "resource_recovery": {"path": "resource-recovery/manifest.json", "sha256": "4" * 64},
        }
        validated = {
            "plan": plan,
            "bytes_sha256": "d" * 64,
            "fixture_revision": "sha256:" + "5" * 64,
            "tools": {"fake-tool": tool_binding},
            "qualification": {"fake-tool": {"qualified": True}},
            "source_inputs": [],
        }
        attempt = root / Path(*checker.ATTEMPTS_ROOT.parts) / attempt_id
        execution = (root / Path(*checker.EXECUTOR.EXECUTION_ROOT.parts) /
                     "series-01" / group_id / "attempt-01")
        cache = (root / Path(*checker.EXECUTOR.CACHE_ROOT.parts) /
                 "series-01" / group_id / "attempt-01")
        attempt.mkdir(parents=True)
        expected = {
            "execution_series": 1,
            "group_id": group_id,
            "attempt_id": attempt_id,
            "source_commit": plan["source_commit"],
            "plan_commit": plan_commit,
            "contract_sha256": validated["bytes_sha256"],
            "runner_source_sha256": plan["runner_source_sha256"],
            "fixture_revision": validated["fixture_revision"],
            "population": population,
            "tool": "fake-tool",
            "tool_binding": tool_binding,
            "identity_components": [],
            "swift_plan": None,
            "joern_plan": None,
            "qualification": validated["qualification"]["fake-tool"],
            "source_inputs": [],
            "cache_root": str(cache),
            "argv": group["argv"],
            "environment": environment,
            "execution_root": str(execution),
            "output_roots": group["output_roots"],
            "case_ids": group["case_ids"],
            "deadline_seconds": group["deadline_seconds"],
            "started_receipt": "started.json",
        }
        timestamp = "2026-10-20T18:00:00+00:00"
        receipt = {
            **expected,
            "schema_version": 1,
            "release": checker.RELEASE,
            "status": status,
            "start_utc": timestamp,
            "end_utc": "2026-10-20T18:00:00.250000+00:00",
            "snapshot_git_head": None,
            "exit_code": 125,
            "timed_out": False,
            "duration_seconds": 0.0,
            "capacity_loss": guard_error if as_capacity_loss else None,
            "stdout": {"path": "stdout.txt", "sha256": hashlib.sha256(b"").hexdigest(), "bytes": 0},
            "stderr": {"path": "stderr.txt", "sha256": hashlib.sha256(b"").hexdigest(), "bytes": 0},
            "captured_files": [],
            "reports": [],
            "recorder_error": f"DiskGuardError: {guard_error['message']}",
            "failed_staging_artifacts": [],
        }
        if not as_capacity_loss:
            receipt["disk_guard_error"] = guard_error
        started = {
            **expected,
            "schema_version": 1,
            "release": checker.RELEASE,
            "status": "started",
            "start_utc": timestamp,
            "end_utc": None,
        }
        (attempt / "started.json").write_text(json.dumps(started, sort_keys=True, separators=(",", ":")))
        for stream in ("stdout", "stderr"):
            (attempt / f"{stream}.txt").write_bytes(b"")
        completed_bytes = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        (attempt / "completed.json").write_bytes(completed_bytes)
        ledger_line_sha = hashlib.sha256(completed_bytes + b"\n").hexdigest()
        return validated, group, receipt, plan_commit, 1, ledger_line_sha

    def _replay(self, root: Path, failure: tuple) -> dict:
        validated, group, receipt, plan_commit, attempt_number, ledger_line_sha = failure
        attempt_id = receipt["attempt_id"]
        completed_bytes = (root / Path(*checker.ATTEMPTS_ROOT.parts) / attempt_id /
                           "completed.json").read_bytes()
        with patch.object(checker.EXECUTOR, "_child_environment",
                          return_value=receipt["environment"]):
            return checker._verify_failed_attempt(
                root, validated, group, receipt, plan_commit, attempt_number,
                ledger_line_sha, hashlib.sha256(completed_bytes).hexdigest(),
            )

    def test_prelaunch_capacity_loss_replays_without_claiming_analyzer_start(self) -> None:
        guard_error = {
            "code": "stop_floor",
            "message": "projected write would cross the proactive protected-reserve stop floor",
            "phase": "active",
            "free_bytes": 10 * 1024**3,
            "projected_bytes": 60 * 1024**3,
            "post_write_free_bytes": -50 * 1024**3,
            "required_free_bytes": 48 * 1024**3,
            "protected_reserve_bytes": 40 * 1024**3,
            "capacity_path": "/task/repo",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            failure = self._write_failure(root, "capacity-lost", guard_error=guard_error,
                                          as_capacity_loss=True)
            summary = self._replay(root, failure)
            self.assertEqual(summary["status"], "capacity-lost")
            self.assertIs(summary["analyzer_started"], False)
            self.assertEqual(summary["stdout"]["bytes"], 0)
            self.assertEqual(summary["stderr"]["bytes"], 0)

            legacy_validated = json.loads(json.dumps(failure[0]))
            legacy_validated["plan"].pop("resource_recovery")
            with patch.object(checker.EXECUTOR, "_child_environment",
                              return_value=failure[2]["environment"]):
                with self.assertRaisesRegex(checker.EvidenceError, "process ownership"):
                    checker._verify_failed_attempt(
                        root, legacy_validated, failure[1], failure[2], failure[3], failure[4],
                        failure[5],
                    )

            malformed = json.loads(json.dumps(failure[2]))
            malformed["capacity_loss"]["unreviewed"] = True
            failure[2].clear()
            failure[2].update(malformed)
            attempt = root / Path(*checker.ATTEMPTS_ROOT.parts) / malformed["attempt_id"]
            (attempt / "completed.json").write_text(
                json.dumps(malformed, sort_keys=True, separators=(",", ":")),
            )
            with self.assertRaisesRegex(checker.EvidenceError, "unknown metadata"):
                self._replay(root, failure)

    def test_category_guard_accepts_and_checks_additional_current_bytes(self) -> None:
        receipt = {
            "code": "category_ceiling",
            "message": "projected working usage exceeds its configured ceiling",
            "category": "working",
            "current_bytes": 100,
            "additional_current_bytes": 20,
            "projected_bytes": 30,
            "total_projected_bytes": 130,
            "category_limit_bytes": 120,
            "accounting_paths": ["/task/working"],
        }
        self.assertEqual(
            checker._verify_resource_guard_error("capacity-test", receipt, capacity_loss=True), receipt,
        )
        receipt["total_projected_bytes"] = 129
        with self.assertRaisesRegex(checker.EvidenceError, "arithmetically inconsistent"):
            checker._verify_resource_guard_error("capacity-test", receipt, capacity_loss=True)

    def test_noncapacity_guard_failure_stays_a_prelaunch_recorder_error(self) -> None:
        guard_error = {
            "code": "source_changed",
            "message": "source changed while it was being copied",
            "source_path": "src/main.rs",
            "expected_size_bytes": 1024,
            "copied_bytes": 512,
            "partial_bytes": 512,
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            failure = self._write_failure(root, "recorder-error", guard_error=guard_error,
                                          as_capacity_loss=False)
            summary = self._replay(root, failure)
            self.assertEqual(summary["status"], "recorder-error")
            self.assertIs(summary["analyzer_started"], False)

    def test_executor_capacity_refusal_is_replayed_by_checker_from_saved_receipt(self) -> None:
        executor = checker.EXECUTOR
        group_id = "resource-guard-integration"
        attempt_id = f"{group_id}-attempt-01-series-01"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            attempt = root / Path(*checker.ATTEMPTS_ROOT.parts) / attempt_id
            execution = (root / Path(*executor.EXECUTION_ROOT.parts) /
                         "series-01" / group_id / "attempt-01")
            cache = (root / Path(*executor.CACHE_ROOT.parts) /
                     "series-01" / group_id / "attempt-01")
            environment = {"HOME": str(attempt / "home"), "TMPDIR": str(attempt / "tmp")}
            group = {
                "id": group_id,
                "tool": "fake-tool",
                "argv": ["/tools/fake", "analyze"],
                "output_roots": ["reports/raw/resource-guard-integration"],
                "case_ids": ["case-001"],
                "deadline_seconds": 30,
                "maximum_attempts": 2,
            }
            plan = {
                "execution_authorized": True,
                "execution_series": 1,
                "source_commit": "e" * 40,
                "runner_source_sha256": "3" * 64,
                "population": {"path": "populations/v0.9.0", "sha256": "2" * 64},
                "resource_recovery": {"path": "resource-recovery/manifest.json", "sha256": "4" * 64},
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
                "repo_root": root,
                "plan": plan,
                "groups": [{"id": group_id, "reports": [], "identity_components": []}],
                "source_inputs": [],
                "tools": {"fake-tool": {"path": "/tools/fake", "sha256": "1" * 64}},
                "bytes_sha256": "d" * 64,
                "fixture_revision": "sha256:" + "5" * 64,
                "total_wall_budget_seconds": 3600,
                "qualification": {"fake-tool": {"qualified": True}},
            }

            class FakeDiskGuard:
                def __init__(self, **_kwargs):
                    pass

                @staticmethod
                def logical_size(_paths):
                    return 0

                def check(self, **_kwargs):
                    return {}

                def check_capacity(self, **_kwargs):
                    return {}

            class FakeLoader:
                def exec_module(self, module):
                    module.DiskGuard = FakeDiskGuard
                    module.DiskGuardError = disk_guard.DiskGuardError

            error = disk_guard.DiskGuardError(
                "stop_floor",
                "projected write would cross the proactive protected-reserve stop floor",
                phase="active",
                free_bytes=49 * 1024**3,
                projected_bytes=2 * 1024**3,
                post_write_free_bytes=47 * 1024**3,
                required_free_bytes=48 * 1024**3,
                protected_reserve_bytes=40 * 1024**3,
                capacity_path=str(root),
            )

            def materialize(_repo, _commit, _destination, _inputs, *, preflight_only=False, **_kwargs):
                if preflight_only:
                    return 128
                execution.mkdir(parents=True, exist_ok=True)
                (execution / "src").mkdir(exist_ok=True)
                (execution / "src" / "partial.rs").write_bytes(b"partial source")
                raise error

            def forbidden_process(*_args, **_kwargs):
                self.fail("analyzer process must not start after source materialization refusal")

            fake_spec = types.SimpleNamespace(loader=FakeLoader())
            with contextlib.ExitStack() as patches:
                for name, value in (
                    ("_exclusive_lock", contextlib.nullcontext()),
                    ("_process_table", ""),
                    ("_contenders", []),
                    ("_assert_contract_snapshot", "1" * 40),
                    ("_matrix_elapsed_wall", 0),
                    ("_assert_source_snapshot", None),
                    ("_source_file", b"source"),
                    ("_check_tool_file", None),
                    ("_require_group_qualification", {"qualified": True}),
                    ("_child_environment", environment),
                    ("_matrix_capacity_paths", ([], [])),
                    ("_verified_completed_groups", set()),
                    ("_run_process", forbidden_process),
                ):
                    kwargs = {"side_effect": value} if callable(value) and name == "_run_process" else {
                        "return_value": value,
                    }
                    patches.enter_context(patch.object(executor, name, **kwargs))
                patches.enter_context(patch.object(
                    executor, "_assert_fresh", return_value=(attempt, execution, cache,
                                                              root / Path(*executor.LEDGER_PATH.parts), attempt_id),
                ))
                patches.enter_context(patch.object(
                    executor, "_materialize_source", side_effect=materialize,
                ))
                patches.enter_context(patch.object(
                    executor.importlib.util, "spec_from_file_location", return_value=fake_spec,
                ))
                patches.enter_context(patch.object(
                    executor.importlib.util, "module_from_spec", return_value=types.SimpleNamespace(),
                ))
                row = executor.run_group(validated, group_id)
                self.assertEqual(row["status"], "capacity-lost")
                self.assertEqual(row["capacity_loss"]["code"], "stop_floor")
                self.assertNotIn("process_ownership", row)

                checker_group = {**group, "identity_components": []}
                ledger_bytes = (root / Path(*executor.LEDGER_PATH.parts)).read_bytes()
                ledger_line_sha = hashlib.sha256(ledger_bytes).hexdigest()
                completed_sha = hashlib.sha256((attempt / "completed.json").read_bytes()).hexdigest()
                summary = checker._verify_failed_attempt(
                    root, validated, checker_group, row, "1" * 40, 1, ledger_line_sha,
                    completed_sha,
                )
                self.assertIs(summary["analyzer_started"], False)
                self.assertEqual(summary["stdout"]["bytes"], 0)
                self.assertEqual(summary["stderr"]["bytes"], 0)

    def test_postprocess_capacity_refusal_replays_preserved_partial_staging(self) -> None:
        executor = checker.EXECUTOR
        group_id = "resource-stage-guard-integration"
        attempt_id = f"{group_id}-attempt-01-series-01"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            attempt = root / Path(*checker.ATTEMPTS_ROOT.parts) / attempt_id
            execution = (root / Path(*executor.EXECUTION_ROOT.parts) /
                         "series-01" / group_id / "attempt-01")
            cache = (root / Path(*executor.CACHE_ROOT.parts) /
                     "series-01" / group_id / "attempt-01")
            environment = {"HOME": str(attempt / "home"), "TMPDIR": str(attempt / "tmp")}
            output_relative = "reports/raw/resource-stage-guard-integration/result.json"
            report_path = "reports/releases/v0.9.2/normal/resource-stage-guard-integration.json"
            report = {"path": report_path, "case_ids": ["case-001"]}
            group = {
                "id": group_id,
                "tool": "fake-tool",
                "argv": ["/tools/fake", "analyze"],
                "output_roots": ["reports/raw/resource-stage-guard-integration"],
                "case_ids": ["case-001"],
                "deadline_seconds": 30,
                "maximum_attempts": 2,
            }
            plan = {
                "execution_authorized": True,
                "execution_series": 1,
                "source_commit": "e" * 40,
                "runner_source_sha256": "3" * 64,
                "population": {"path": "populations/v0.9.0", "sha256": "2" * 64},
                "resource_recovery": {"path": "resource-recovery/manifest.json", "sha256": "4" * 64},
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
                "repo_root": root,
                "plan": plan,
                "groups": [{"id": group_id, "reports": [report], "identity_components": []}],
                "source_inputs": [],
                "tools": {"fake-tool": {"path": "/tools/fake", "sha256": "1" * 64}},
                "bytes_sha256": "d" * 64,
                "fixture_revision": "sha256:" + "5" * 64,
                "total_wall_budget_seconds": 3600,
                "qualification": {"fake-tool": {"qualified": True}},
            }

            class FakeDiskGuard:
                def __init__(self, **_kwargs):
                    pass

                @staticmethod
                def logical_size(_paths):
                    return 0

                def check(self, **_kwargs):
                    return {}

                def check_capacity(self, **_kwargs):
                    return {}

            class FakeLoader:
                def exec_module(self, module):
                    module.DiskGuard = FakeDiskGuard
                    module.DiskGuardError = disk_guard.DiskGuardError

            error = disk_guard.DiskGuardError(
                "stop_floor",
                "projected write would cross the proactive protected-reserve stop floor",
                phase="active",
                free_bytes=10 * 1024**3,
                projected_bytes=60 * 1024**3,
                post_write_free_bytes=-50 * 1024**3,
                required_free_bytes=48 * 1024**3,
                protected_reserve_bytes=40 * 1024**3,
                capacity_path=str(root),
            )

            def materialize(_repo, _commit, _destination, _inputs, *, preflight_only=False, **_kwargs):
                if preflight_only:
                    return 128
                execution.mkdir(parents=True, exist_ok=True)
                return None

            def finish_analyzer(_argv, cwd, _env, stdout, stderr, _deadline, *, ownership, **_kwargs):
                stdout.write_bytes(b"analyzer completed\n")
                stderr.write_bytes(b"")
                ownership.update({
                    "schema": "invocation-process-ownership/v1",
                    "root_pid": 123,
                    "tracking_interval_seconds": 2.0,
                    "tracked_processes": [{"pid": 123, "start_identity": "123:1"}],
                    "signals_sent": [],
                    "cleanup_status": "tracked-processes-stopped",
                    "descendant_containment": "unproven",
                })
                output = cwd / Path(*Path(output_relative).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"{\"result\":\"captured\"}\n")
                return 0, False, 1.25, None

            def copy_tree(_output_root, execution_root, _snapshot_root, capture_root, *,
                          preflight_only=False, **_kwargs):
                source = execution_root / Path(*Path(output_relative).parts)
                data = source.read_bytes()
                if preflight_only:
                    return [{"execution_relative": output_relative, "bytes": len(data)}]
                destination = capture_root / Path(*Path(output_relative).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                return [{
                    "execution_relative": output_relative,
                    "capture_path": str(destination),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                }]

            def fail_staging(repo_root, attempt_path, _execution_root, current_attempt_id,
                             _report, _captured, _output_roots, _fixture_revision, **_kwargs):
                original = attempt_path / "original" / "partial-report.json"
                staged = (repo_root / Path(*executor.NORMAL_ROOT.parts) / "attempts" /
                          current_attempt_id / "partial-report.json")
                original.parent.mkdir(parents=True, exist_ok=True)
                staged.parent.mkdir(parents=True, exist_ok=True)
                original.write_bytes(b"partial original")
                staged.write_bytes(b"partial staged")
                raise error

            fake_spec = types.SimpleNamespace(loader=FakeLoader())
            with contextlib.ExitStack() as patches:
                patch_values = (
                    ("_exclusive_lock", contextlib.nullcontext()),
                    ("_process_table", ""),
                    ("_contenders", []),
                    ("_assert_contract_snapshot", "1" * 40),
                    ("_matrix_elapsed_wall", 0),
                    ("_assert_source_snapshot", None),
                    ("_source_file", b"source"),
                    ("_check_tool_file", None),
                    ("_require_group_qualification", {"qualified": True}),
                    ("_child_environment", environment),
                    ("_matrix_capacity_paths", ([], [])),
                    ("_verified_completed_groups", set()),
                )
                for name, value in patch_values:
                    patches.enter_context(patch.object(executor, name, return_value=value))
                patches.enter_context(patch.object(
                    executor, "_assert_fresh", return_value=(attempt, execution, cache,
                                                              root / Path(*executor.LEDGER_PATH.parts), attempt_id),
                ))
                patches.enter_context(patch.object(executor, "_materialize_source", side_effect=materialize))
                patches.enter_context(patch.object(executor, "_run_process", side_effect=finish_analyzer))
                patches.enter_context(patch.object(executor, "_copy_tree", side_effect=copy_tree))
                patches.enter_context(patch.object(executor, "_stage_report", side_effect=fail_staging))
                patches.enter_context(patch.object(
                    executor.importlib.util, "spec_from_file_location", return_value=fake_spec,
                ))
                patches.enter_context(patch.object(
                    executor.importlib.util, "module_from_spec", return_value=types.SimpleNamespace(),
                ))
                row = executor.run_group(validated, group_id)
                self.assertEqual(row["status"], "capacity-lost")
                self.assertEqual(row["exit_code"], 0)
                self.assertTrue(row["failed_staging_artifacts"])
                self.assertEqual(row["reports"], [])

                checker_group = {**group, "identity_components": []}
                ledger_bytes = (root / Path(*executor.LEDGER_PATH.parts)).read_bytes()
                ledger_line_sha = hashlib.sha256(ledger_bytes).hexdigest()
                completed_sha = hashlib.sha256((attempt / "completed.json").read_bytes()).hexdigest()
                summary = checker._verify_failed_attempt(
                    root, validated, checker_group, row, "1" * 40, 1, ledger_line_sha,
                    completed_sha,
                )
                self.assertIs(summary["analyzer_started"], True)
                self.assertEqual(len(summary["failed_staging_artifacts"]), 2)
                self.assertEqual(summary["captured_files"][0]["execution_relative"], output_relative)


if __name__ == "__main__":
    unittest.main()
