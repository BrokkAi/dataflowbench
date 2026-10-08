#!/usr/bin/env python3
"""Focused contract tests for the bounded v0.9.1 Bifrost executor."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("execute-release-v091.py")
SPEC = importlib.util.spec_from_file_location("execute_release_v091", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runner = self.root / "runner"
        self.bifrost = self.root / "bifrost"
        self.runner.write_bytes(b"runner")
        self.bifrost.write_bytes(b"bifrost-0.13")
        self.fixture = "sha256:fixture-v090"
        self.group_id = "bifrost-c-kernel"
        self.execution = self.root / "execution-state/v091/groups" / self.group_id
        self.output_root = self.execution / "reports"
        self.raw = self.output_root / "raw" / "case.bin"
        self.report_source = self.output_root / "report.json"
        self.report_path = "reports/releases/v0.9.1/normal/bifrost-c-kernel.json"
        self.case_id = "dfb-taint-c-direct-positive"
        self.original_report = {
            "fixture_revision": self.fixture,
            "tool": "bifrost",
            "tool_version": "bifrost 0.13.0",
            "results": [{
                "case_id": self.case_id,
                "outcome": "inconclusive",
                "raw_output": "reports/raw/case.bin",
                "raw_sha256": hashlib.sha256(b"raw-native-bytes").hexdigest(),
            }],
        }
        self.plan_group = {
            "id": self.group_id,
            "argv": [str(self.runner), str(self.bifrost)],
            "case_ids": [self.case_id],
            "output_roots": [str(self.output_root)],
            "deadline_seconds": 5,
            "reports": [{
                "path": self.report_path,
                "source_path": str(self.report_source),
                "case_ids": [self.case_id],
                "tool": "bifrost",
                "tool_version": "bifrost 0.13.0",
            }],
        }
        self.plan = {
            "schema_version": 1,
            "release": "v0.9.1",
            "source_commit": "a" * 40,
            "fixture_revision": self.fixture,
            "population": {
                "path": "populations/v0.9.0.json",
                "sha256": "b" * 64,
                "fixture_revision": self.fixture,
            },
            "tools": {
                "runner": {"path": str(self.runner), "sha256": hashlib.sha256(b"runner").hexdigest()},
                "bifrost": {
                    "path": str(self.bifrost),
                    "sha256": hashlib.sha256(b"bifrost-0.13").hexdigest(),
                    "version": "0.13.0",
                    "build_identity": "9426a205c6ced4d438182068995d6279f0d885fe",
                    "binary_sha256": "640d0b8e4fe5fb34159c184f994e245021825b05e6144a09f2b4be9a76b129c9",
                    "archive_sha256": "8fb7212912cda0d6fc97e72188339b53aec4ea1ce31cc6a076765763e2273604",
                },
            },
            "groups": [self.plan_group],
        }
        self.validated = {
            "repo_root": self.root,
            "plan": self.plan,
            "fixture_revision": self.fixture,
            "runner": self.plan["tools"]["runner"],
            "bifrost": self.plan["tools"]["bifrost"],
            "groups": [{"id": self.group_id, "reports": self.plan_group["reports"]}],
        }
        self.lock = self.root / "exclusive.lock"

    def run_group(self, **patches):
        patches.setdefault("_exclusive_lock", mock.patch.object(executor, "LOCK_PATH", str(self.lock)))
        patches.setdefault("_git_head", mock.patch.object(executor, "_git_head", return_value=self.plan["source_commit"]))
        patches.setdefault("_assert_source_snapshot", mock.patch.object(executor, "_assert_source_snapshot"))
        patches.setdefault("_source_file", mock.patch.object(executor, "_source_file", return_value=b"population"))
        patches.setdefault("_check_tool_file", mock.patch.object(executor, "_check_tool_file"))
        patches.setdefault("_check_resources", mock.patch.object(executor, "_check_resources"))
        with contextlib.ExitStack() as stack:
            for patcher in patches.values():
                stack.enter_context(patcher)
            return executor.run_group(self.validated, self.group_id)

    def test_success_stages_exact_raw_bytes_and_task_cache(self):
        observed_environment = {}

        def materialize(_repo, _commit, destination):
            destination.mkdir(parents=True)
            self.output_root.mkdir(parents=True)
            self.raw.parent.mkdir(parents=True)
            self.raw.write_bytes(b"raw-native-bytes")
            self.report_source.write_bytes(json.dumps(self.original_report).encode() + b"\n")

        def native(_argv, cwd, env, stdout, stderr, timeout):
            self.assertEqual(cwd, self.execution)
            self.assertEqual(env["BIFROST_CACHE_ROOT"], str(self.root / "execution-state/v091/cache/bifrost-c-kernel"))
            self.assertNotIn("HOME", env)
            self.assertNotIn("DFB_TEST_SECRET", env)
            observed_environment.update(env)
            stdout.write_bytes(b"native stdout")
            stderr.write_bytes(b"native stderr")
            return 0, False, 0.01

        with mock.patch.dict(executor.os.environ, {"HOME": "/secret", "DFB_TEST_SECRET": "secret"}, clear=False):
            row = self.run_group(
                _materialize_source=mock.patch.object(executor, "_materialize_source", side_effect=materialize),
                _run_process=mock.patch.object(executor, "_run_process", side_effect=native),
            )
        self.assertEqual(row["status"], "completed")
        self.assertEqual((self.raw).read_bytes(), b"raw-native-bytes")
        attempt = self.root / "reports/releases/v0.9.1/attempts" / f"{self.group_id}-attempt-01"
        self.assertEqual((attempt / "capture/reports/raw/case.bin").read_bytes(), b"raw-native-bytes")
        self.assertEqual((attempt / "original/reports/releases/v0.9.1/normal/bifrost-c-kernel.json").read_bytes(),
                         json.dumps(self.original_report).encode() + b"\n")
        staged = json.loads((self.root / self.report_path).read_text())
        self.assertEqual(staged["results"][0]["raw_output"],
                         "reports/releases/v0.9.1/attempts/bifrost-c-kernel-attempt-01/capture/reports/raw/case.bin")
        self.assertEqual((attempt / "stdout.txt").read_bytes(), b"native stdout")
        receipt = json.loads((attempt / "completed.json").read_text())
        self.assertEqual(receipt["bifrost"]["build_identity"], self.plan["tools"]["bifrost"]["build_identity"])
        self.assertTrue(Path(receipt["bifrost_cache_root"]).is_dir())
        self.assertEqual(receipt["environment"], observed_environment)

    def test_membership_rejection_is_fail_closed(self):
        bad = dict(self.plan_group)
        bad["case_ids"] = ["outside-population"]
        with self.assertRaisesRegex(executor.ReleaseError, "case membership"):
            executor._validate_group_shape(
                bad, {self.case_id}, self.root,
                self.plan["tools"]["runner"], self.plan["tools"]["bifrost"],
            )

    def test_report_identity_mismatch_is_retained_as_recorder_error(self):
        def materialize(_repo, _commit, destination):
            destination.mkdir(parents=True)
            self.output_root.mkdir(parents=True)
            self.raw.parent.mkdir(parents=True)
            self.raw.write_bytes(b"raw-native-bytes")
            wrong = dict(self.original_report)
            wrong["tool_version"] = "0.12.0"
            self.report_source.write_bytes(json.dumps(wrong).encode())

        def native(_argv, _cwd, _env, stdout, stderr, _timeout):
            stdout.write_bytes(b"native stdout")
            stderr.write_bytes(b"native stderr")
            return 0, False, 0.01

        row = self.run_group(
            _materialize_source=mock.patch.object(executor, "_materialize_source", side_effect=materialize),
            _run_process=mock.patch.object(executor, "_run_process", side_effect=native),
        )
        self.assertEqual(row["status"], "recorder-error")
        self.assertIn("tool version mismatch", row["recorder_error"])
        self.assertTrue((self.root / "reports/releases/v0.9.1/attempts/bifrost-c-kernel-attempt-01/completed.json").is_file())
        self.assertFalse((self.root / self.report_path).exists())

    def test_timeout_is_retained_and_second_run_does_not_retry(self):
        def materialize(_repo, _commit, destination):
            destination.mkdir(parents=True)
            self.output_root.mkdir(parents=True)

        def timeout(_argv, _cwd, _env, stdout, stderr, _timeout):
            stdout.write_bytes(b"partial stdout")
            stderr.write_bytes(b"partial stderr")
            return 124, True, 5.0

        first = self.run_group(
            _materialize_source=mock.patch.object(executor, "_materialize_source", side_effect=materialize),
            _run_process=mock.patch.object(executor, "_run_process", side_effect=timeout),
        )
        self.assertEqual(first["status"], "timed-out")
        with self.assertRaisesRegex(executor.ReleaseError, "existing attempt"):
            self.run_group(
                _materialize_source=mock.patch.object(executor, "_materialize_source", side_effect=AssertionError("retry")),
                _run_process=mock.patch.object(executor, "_run_process", side_effect=AssertionError("retry")),
            )

    def test_contention_stops_before_allocating_attempt(self):
        with self.assertRaisesRegex(executor.ReleaseError, "contending"):
            self.run_group(
                _process_table=mock.patch.object(executor, "_process_table", return_value="42 cargo build\n"),
                _check_resources=mock.patch.object(executor, "_check_resources", wraps=executor._check_resources),
            )
        self.assertFalse((self.root / "reports/releases/v0.9.1/attempts").exists())
        self.assertFalse((self.root / "execution-state/v091/cache").exists())

    def test_child_environment_has_no_unapproved_inherited_values(self):
        with mock.patch.dict(executor.os.environ, {
            "PATH": "/bin", "LANG": "C", "LC_ALL": "C", "JAVA_HOME": "/java",
            "TMPDIR": "/tmp", "HOME": "/secret-home", "AWS_SECRET_ACCESS_KEY": "secret",
        }, clear=True):
            environment = executor._child_environment(self.root / "cache")
        self.assertEqual(environment["BIFROST_CACHE_ROOT"], str(self.root / "cache"))
        self.assertNotIn("HOME", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertEqual(set(environment), {
            "PATH", "LANG", "LC_ALL", "JAVA_HOME", "TMPDIR", "BIFROST_CACHE_ROOT",
        })

    def test_historical_smoke_overlap_is_allowed_but_rows_remain_1116(self):
        historical = executor._historical_bifrost_groups(Path(__file__).parents[1])
        self.assertIsNotNone(historical)
        rows = [case_id for cases in historical.values() for case_id in cases]
        self.assertEqual(len(historical), 20)
        self.assertEqual(len(rows), 1116)
        self.assertLess(len(set(rows)), len(rows))

    def test_idle_mcp_is_ignored_but_active_mcp_blocks(self):
        idle = "101 0.0 bifrost /opt/bifrost --mcp"
        active = "102 3.2 bifrost /opt/bifrost --mcp"
        self.assertEqual(executor._contenders(idle), [])
        self.assertEqual(executor._contenders(active), [active])

    def test_repo_mentions_and_service_process_are_not_analyzer_executables(self):
        table = "\n".join([
            "103 0.0 gh gh run watch --repo BrokkAi/bifrost-service",
            "104 0.0 /Users/dave/.cod /Users/dave/.codex/worktrees/a37f/bifrost-service/target/debug/bifrost-service-control",
            "105 0.0 /bin/zsh /bin/zsh -c 'gh pr view --repo BrokkAi/bifrost-packs'",
        ])
        self.assertEqual(executor._contenders(table), [])


if __name__ == "__main__":
    unittest.main()
