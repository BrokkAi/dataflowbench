#!/usr/bin/env python3
import importlib.util
import inspect
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-03.py"


def load():
    spec = importlib.util.spec_from_file_location("supervisor_independent_pending_codeql_tested", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CodeQLSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def test_worker_environment_requires_exact_markers(self):
        good = {
            "PATH": "/usr/bin",
            "LANG": "C",
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
            "DATAFLOWBENCH_V092_GROUP_ID": self.m.GROUP,
            "__CF_USER_TEXT_ENCODING": self.m.CF_USER_TEXT_ENCODING,
            "SECRET_SHOULD_NOT_BE_INHERITED": "redacted",
        }
        with tempfile.TemporaryDirectory() as directory:
            env = self.m.worker_environment(good, scoped_root=Path(directory))
        self.assertEqual(env["PATH"], "/usr/bin")
        self.assertEqual(env["LANG"], "C")
        self.assertEqual(env["DATAFLOWBENCH_V092_RELEASE_EXECUTION"], "1")
        self.assertEqual(env["DATAFLOWBENCH_V092_GROUP_ID"], self.m.GROUP)
        self.assertEqual(env["__CF_USER_TEXT_ENCODING"], self.m.CF_USER_TEXT_ENCODING)
        self.assertNotIn("SECRET_SHOULD_NOT_BE_INHERITED", env)
        self.assertTrue(env["HOME"].endswith("/worker-home"))
        self.assertTrue(env["TMPDIR"].endswith("/worker-tmp"))
        for key, value in (("DATAFLOWBENCH_V092_GROUP_ID", "joern-swift-common108"),
                           ("__CF_USER_TEXT_ENCODING", "wrong")):
            bad = dict(good)
            bad[key] = value
            with self.assertRaises(self.m.CodeQLSupervisorError):
                self.m.worker_environment(bad)

    def test_harmless_child_probe_binds_full_sanitized_environment(self):
        probe = self.m.probe_worker_environment({"PATH": "/usr/bin", "LANG": "C"})
        self.assertEqual(probe["status"], "passed")
        self.assertIn("HOME", probe["keys"])
        self.assertIn("TMPDIR", probe["keys"])
        with self.assertRaises(self.m.CodeQLSupervisorError):
            self.m.probe_worker_environment({
                "PATH": "/usr/bin",
                "DATAFLOWBENCH_V092_GROUP_ID": "wrong-group",
            })

    def test_manifest_binding_rejects_tamper_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text('{"status":"approved"}\n')
            digest = self.m.sha(manifest)
            self.assertEqual(
                self.m.read_bound_manifest(root, "manifest.json", digest)["status"],
                "approved",
            )
            manifest.write_text('{"status":"tampered"}\n')
            with self.assertRaises(self.m.CodeQLSupervisorError):
                self.m.read_bound_manifest(root, "manifest.json", digest)
            manifest.unlink()
            target = root / "target.json"
            target.write_text('{"status":"approved"}\n')
            manifest.symlink_to(target)
            with self.assertRaises(self.m.CodeQLSupervisorError):
                self.m.read_bound_manifest(root, "manifest.json", digest)

    def test_gate_binds_the_single_codeql_command(self):
        args = type("Args", (), {
            "manifest": self.m.MANIFEST,
            "manifest_sha256": "a" * 64,
        })()
        command = self.m.command(args, "execute")
        self.assertIn("execute", command)
        self.assertIn(self.m.MODULE, [str(x).replace(str(ROOT) + "/", "") for x in command])
        self.assertNotIn("joern-swift-common108", command)

    def test_validation_rechecks_frozen_127_gib_gate_before_namespace_launch(self):
        source = inspect.getsource(self.m.validate)
        self.assertIn("check_live_resource_floor", source)
        self.assertIn("load_frozen", source)
        self.assertIn("admission_helper_sha256", source)
        self.assertIn("admission_receipt_sha256", source)

    def test_one_shot_gate_has_no_retry_policy(self):
        args = type("Args", (), {
            "manifest": self.m.MANIFEST,
            "manifest_sha256": "a" * 64,
        })()
        command = self.m.command(args, "execute")
        gate = self.m._gate(Path("/tmp/codeql-permit"), "token", command)
        self.assertNotIn("retry", " ".join(gate).lower())
        self.assertEqual(gate[-len(command):], command)

    def test_gate_waits_only_for_the_one_permit_and_is_valid_python(self):
        args = type("Args", (), {
            "manifest": self.m.MANIFEST,
            "manifest_sha256": "a" * 64,
        })()
        gate = self.m._gate(Path("/tmp/codeql-permit"), "token", self.m.command(args, "execute"))
        compile(gate[3], "codeql-supervisor-gate", "exec")
        self.assertIn("range(3000)", gate[3])
        self.assertNotIn("retry", gate[3].lower())

    def test_gate_executes_exact_permit_and_rejects_wrong_or_missing_permit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "child-sentinel"
            permit = root / "permit.json"
            token = "token-good"
            command = [sys.executable, "-E", "-B", "-c",
                       "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('sentinel')",
                       str(marker)]
            process = subprocess.Popen(
                self.m._gate(permit, token, command), cwd=ROOT,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=True,
            )
            self.m._permit(permit, process.pid, token, command)
            self.assertEqual(process.wait(timeout=5), 0)
            self.assertEqual(marker.read_text(), "sentinel")

            wrong_permit = root / "wrong-permit.json"
            wrong_process = subprocess.Popen(
                self.m._gate(wrong_permit, token, command), cwd=ROOT,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=True,
            )
            self.m._permit(wrong_permit, wrong_process.pid, "wrong-token", command)
            self.assertEqual(wrong_process.wait(timeout=5), 126)

            missing_permit = root / "missing-permit.json"
            missing_process = subprocess.Popen(
                self.m._gate(missing_permit, token, command), cwd=ROOT,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=True,
            )
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    missing_process.wait(timeout=0.5)
            finally:
                missing_process.kill()
                missing_process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
