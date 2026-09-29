#!/usr/bin/env python3
"""Isolated recorder tests use only synthetic fake commands."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest

SCRIPT = Path(__file__).with_name("release_attempt_v090.py")
SPEC = importlib.util.spec_from_file_location("release_attempt_v090", SCRIPT)
RECORDER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = RECORDER
SPEC.loader.exec_module(RECORDER)

FIXTURE = "sha256:" + "a" * 64
ENV = {"PATH": "/pinned/semgrep/bin:/usr/bin", "SEMGREP_ENABLE_VERSION_CHECK": "0"}
CONTRACT_PATH = "reports/releases/v0.9.0/execution-v1/contract.json"


class ReleaseAttemptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.output = "reports/releases/v0.9.0/fake-output"
        self.report_paths = [
            "reports/releases/v0.9.0/normal/fake-alpha.json",
            "reports/releases/v0.9.0/normal/fake-beta.json",
        ]
        self.case_partitions = [["case-a"], ["case-b"]]
        self._write("reports/releases/v0.9.0/input-pin.json", b"pinned input\n")
        input_sha = self.sha(b"pinned input\n")
        population = {"population": "v0.9.0", "fixture_revision": FIXTURE}
        population_bytes = self.json_bytes(population)
        self._write(RECORDER.POPULATION_PATH, population_bytes)
        plan = {
            "release": "v0.9.0",
            "fixture_revision": FIXTURE,
            "input_commits": {"corpus": "a" * 40},
            "population": {"path": RECORDER.POPULATION_PATH, "sha256": self.sha(population_bytes)},
            "execution_groups": [{"id": "fake-matrix", "case_ids": ["case-a", "case-b"], "reports": self.report_paths}],
            "reports": [
                {"report": path, "execution_group": "fake-matrix", "tool": "fake", "case_ids": ids}
                for path, ids in zip(self.report_paths, self.case_partitions)
            ],
        }
        plan_bytes = self.json_bytes(plan)
        self._write(RECORDER.PLAN_PATH, plan_bytes)
        self._write(CONTRACT_PATH.rsplit("/", 1)[0] + "/fake-runner.py", self.fake_runner().encode())
        self.argv = [sys.executable, "reports/releases/v0.9.0/execution-v1/fake-runner.py"]
        self.contract = {
            "schema_version": 1,
            "release": "v0.9.0",
            "execution_authorized": True,
            "parent_plan": {"path": RECORDER.PLAN_PATH, "sha256": self.sha(plan_bytes)},
            "population": {"path": RECORDER.POPULATION_PATH, "sha256": self.sha(population_bytes)},
            "fixture_revision": FIXTURE,
            "input_commits": plan["input_commits"],
            "input_identities": {"reports/releases/v0.9.0/input-pin.json": input_sha},
            "groups": [{
                "id": "fake-matrix",
                "historical_seconds": 100,
                "argv": self.argv,
                "case_ids": ["case-a", "case-b"],
                "output_roots": [self.output],
                "environment": ENV,
                "maximum_attempts": 2,
                "reports": [
                    {"ordinal": ordinal,
                     "source_path": f"{self.output}/ordinal/{ordinal}.json",
                     "path": path,
                     "case_ids": ids,
                     "tool": "fake",
                     "tool_version": "fake-tool 1.0"}
                    for ordinal, (path, ids) in enumerate(zip(self.report_paths, self.case_partitions))
                ],
            }],
        }
        self._write(CONTRACT_PATH, self.json_bytes(self.contract))

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def sha(data):
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def json_bytes(value):
        return (json.dumps(value, sort_keys=True) + "\n").encode()

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    @staticmethod
    def fake_runner():
        return r'''import hashlib, json, pathlib, sys
root = pathlib.Path.cwd()
base = pathlib.Path("reports/releases/v0.9.0/fake-output")
raw = base / "raw"
for case_id in ("case-a", "case-b"):
    case = raw / case_id
    (case / "command").mkdir(parents=True, exist_ok=True)
    (case / "native").mkdir(parents=True, exist_ok=True)
    (case / "execution.json").write_bytes((json.dumps({"case_id": case_id, "command": str(base / "raw" / case_id / "command/stdout.txt"), "native": str(base / "raw" / case_id / "native/tool.json")}) + "\n").encode())
    (case / "command/stdout.txt").write_bytes(b"original command bytes\n")
    (case / "native/tool.json").write_bytes(b"original native bytes\n")
for ordinal, case_id in enumerate(("case-a", "case-b")):
    raw_path = base / "raw" / case_id / "execution.json"
    value = {"fixture_revision": "sha256:" + "a" * 64, "tool": "fake", "tool_version": "fake-tool 1.0", "results": [{"case_id": case_id, "raw_output": str(raw_path), "outcome": "inconclusive"}]}
    if "--bad-raw-hash" in sys.argv:
        value["results"][0]["raw_sha256"] = "0" * 64
    if "--bad-id" in sys.argv and ordinal == 0:
        value["results"][0]["case_id"] = "foreign-case"
    if "--bad-tool" in sys.argv:
        value["tool_version"] = "fake-tool 9.9"
    if "--bad-fixture" in sys.argv:
        value["fixture_revision"] = "sha256:" + "b" * 64
    target = base / "ordinal" / (str(ordinal) + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, separators=(",", ":")) + "\n")
sys.exit(17 if "--fail" in sys.argv else 0)
'''

    def run_group(self, argv=None, env=None, timeout=None):
        return RECORDER.run_group(
            self.root, CONTRACT_PATH, "fake-matrix",
            argv=self.argv if argv is None else argv,
            env=ENV if env is None else env,
            timeout_seconds=timeout,
        )

    def run_fake_with_flag(self, flag):
        self.argv = self.argv + [flag]
        self.contract["groups"][0]["argv"] = self.argv
        self._write(CONTRACT_PATH, self.json_bytes(self.contract))
        return self.run_group()

    def test_multi_report_mapping_preserves_raw_tree_and_original_normalized_bytes(self):
        row = self.run_group()
        self.assertEqual(row["status"], "completed")
        self.assertEqual([item["ordinal"] for item in row["reports"]], [0, 1])
        self.assertEqual([item["execution_output_path"] for item in row["reports"]], [
            f"{self.output}/ordinal/0.json", f"{self.output}/ordinal/1.json"
        ])
        self.assertTrue(row["execution_root_mapping"]["nested_raw_references_resolve_from_execution_root_namespace"])
        self.assertFalse(row["execution_root_mapping"]["raw_json_bytes_rewritten"])
        attempt = self.root / RECORDER.ATTEMPTS_PATH / row["attempt_id"]
        for case_id, report_meta in zip(("case-a", "case-b"), row["reports"]):
            original_report = self.root / self.contract["groups"][0]["reports"][int(case_id[-1] == "b")]["source_path"]
            retained_original = attempt / report_meta["original_normalized"]
            self.assertEqual(retained_original.read_bytes(), original_report.read_bytes())
            staged = json.loads((self.root / report_meta["staged_path"]).read_text())
            raw_rel = staged["results"][0]["raw_output"]
            raw_capture = self.root / raw_rel
            source_raw = self.root / self.output / "raw" / case_id
            self.assertEqual(raw_capture.read_bytes(), (source_raw / "execution.json").read_bytes())
            capture_case = raw_capture.parent
            self.assertEqual((capture_case / "command/stdout.txt").read_bytes(), b"original command bytes\n")
            self.assertEqual((capture_case / "native/tool.json").read_bytes(), b"original native bytes\n")
            self.assertEqual(report_meta["original_normalized_sha256"], self.sha(retained_original.read_bytes()))
        self.assertEqual(len((self.root / RECORDER.LEDGER_PATH).read_text().splitlines()), 1)

    def test_optional_wrong_raw_digest_is_rejected(self):
        row = self.run_fake_with_flag('--bad-raw-hash')
        self.assertEqual(row['status'], 'recorder-error')
        self.assertIn('raw_output digest mismatch', row['recorder_error'])

    def test_planning_validation_does_not_authorize_execution(self):
        self.contract['execution_authorized'] = False
        self._write(CONTRACT_PATH, self.json_bytes(self.contract))
        result = RECORDER.validate_group(self.root, CONTRACT_PATH, 'fake-matrix')
        self.assertFalse(result['execution_authorized'])
        self.assertFalse((self.root / RECORDER.ATTEMPTS_PATH).exists())
        with self.assertRaisesRegex(RECORDER.AttemptError, 'validation-only'):
            self.run_group()

    def test_nonzero_exit_retains_attempt_and_all_declared_output(self):
        row = self.run_fake_with_flag("--fail")
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["exit_code"], 17)
        self.assertEqual(row["reports"], [])
        attempt = self.root / RECORDER.ATTEMPTS_PATH / row["attempt_id"]
        self.assertTrue((attempt / "completed.json").is_file())
        self.assertTrue((attempt / "capture" / self.output / "raw/case-a/native/tool.json").is_file())
        self.assertEqual(len((self.root / RECORDER.LEDGER_PATH).read_text().splitlines()), 1)

    def test_exact_argv_environment_and_fresh_roots_fail_before_launch(self):
        with self.assertRaisesRegex(RECORDER.AttemptError, "exact argv"):
            self.run_group(argv=self.argv + ["changed"])
        with self.assertRaisesRegex(RECORDER.AttemptError, "environment"):
            self.run_group(env={"PATH": "/system/bin"})
        self._write(self.output + "/old.json", b"old")
        with self.assertRaisesRegex(RECORDER.AttemptError, "not fresh"):
            self.run_group()
        self.assertFalse((self.root / RECORDER.ATTEMPTS_PATH).exists())

    def test_deadline_is_contract_bound_and_at_least_ten_minutes(self):
        with self.assertRaisesRegex(RECORDER.AttemptError, "reviewed group deadline"):
            self.run_group(timeout=599)
        row = self.run_group()
        self.assertEqual(row["deadline_seconds"], 600)

    def test_timeout_terminates_process_group_including_descendants(self):
        child_pid_file = self.root / "child.pid"
        child_code = (
            "import os,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "open(os.environ['CHILD_PID_FILE'],'w').write(str(os.getpid())); time.sleep(30)"
        )
        parent_code = (
            "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',sys.argv[1]]); "
            "time.sleep(30)"
        )
        env = {"PATH": os.defpath, "CHILD_PID_FILE": str(child_pid_file)}
        stdout = self.root / "timeout.stdout"
        stderr = self.root / "timeout.stderr"
        # Establish the descendant before testing cleanup; process startup is
        # not part of the behavior under test and can exceed 200ms in CI.
        process = subprocess.Popen([sys.executable, '-c', parent_code, child_code],
                                   cwd=self.root, env=env, start_new_session=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not child_pid_file.exists():
                time.sleep(0.01)
            self.assertTrue(child_pid_file.exists(), 'fake descendant did not start')
        finally:
            RECORDER._terminate_process_group(process, grace_seconds=0.1)
        _, timed_out, _ = RECORDER._run(
            [sys.executable, '-c', 'import time; time.sleep(30)'], self.root, env,
            stdout, stderr, 0.1)
        self.assertTrue(timed_out)
        child_pid = int(child_pid_file.read_text())
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            self.fail("timeout left the fake descendant alive")

    def test_wrong_members_fixture_or_tool_version_is_retained_as_recorder_error(self):
        for flag, message in (("--bad-id", "member IDs"), ("--bad-fixture", "fixture_revision"), ("--bad-tool", "tool_version")):
            with self.subTest(flag=flag):
                # Use a fresh test root for each separate attempt.
                self.tearDown()
                self.setUp()
                row = self.run_fake_with_flag(flag)
                self.assertEqual(row["status"], "recorder-error")
                self.assertIn(message, row["recorder_error"])
                self.assertTrue((self.root / RECORDER.ATTEMPTS_PATH / row["attempt_id"] / "capture").is_dir())
                self.assertEqual(len((self.root / RECORDER.LEDGER_PATH).read_text().splitlines()), 1)

    def test_contract_path_escape_and_wrong_member_identity_are_rejected(self):
        with self.assertRaisesRegex(RECORDER.AttemptError, "unsafe output root"):
            self.contract["groups"][0]["output_roots"] = ["../outside"]
            self._write(CONTRACT_PATH, self.json_bytes(self.contract))
            self.run_group()
        self.contract["groups"][0]["output_roots"] = [self.output]
        self.contract["groups"][0]["case_ids"] = ["case-a"]
        self._write(CONTRACT_PATH, self.json_bytes(self.contract))
        with self.assertRaisesRegex(RECORDER.AttemptError, "membership"):
            self.run_group()
        self.assertFalse((self.root / RECORDER.ATTEMPTS_PATH).exists())

    def test_symlink_output_root_is_rejected_before_attempt_creation(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir()
        try:
            (self.root / self.output).parent.mkdir(parents=True, exist_ok=True)
            (self.root / self.output).symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RECORDER.AttemptError, "symlink"):
                self.run_group()
            self.assertFalse((self.root / RECORDER.ATTEMPTS_PATH).exists())
        finally:
            (self.root / self.output).unlink()
            outside.rmdir()


if __name__ == "__main__":
    unittest.main()
