#!/usr/bin/env python3
"""Synthetic-only tests for the immutable release control recorder."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("release_control_attempt_v090.py")
SPEC = importlib.util.spec_from_file_location("release_control_attempt_v090", SCRIPT)
RECORDER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = RECORDER
SPEC.loader.exec_module(RECORDER)

CONTRACT = "reports/releases/v0.9.0/execution-v1/contract.json"
FIXTURE = "sha256:" + "a" * 64


class ControlAttemptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.control_id = "fake-control"
        self.output = "reports/raw/fake-control"
        self.scratch = f"reports/raw/control-scratch/{self.control_id}"
        (self.root / self.scratch).parent.mkdir(parents=True)
        self.command = [sys.executable, "scripts/fake-control.py"]
        self._write("scripts/fake-control.py", b"synthetic script identity\n")
        self._write("reports/releases/v0.9.0/input-pin.json", b"pinned input\n")
        population = {"population": "v0.9.0", "fixture_revision": FIXTURE}
        population_raw = self._json(population)
        self._write("populations/v0.9.0.json", population_raw)
        plan = {
            "release": "v0.9.0", "fixture_revision": FIXTURE,
            "input_commits": {"corpus": "a" * 40},
            "population": {"path": "populations/v0.9.0.json", "sha256": self.sha(population_raw)},
        }
        plan_raw = self._json(plan)
        self._write("reports/releases/v0.9.0/plan.json", plan_raw)
        self.inventory = {"schema": "release-control-inventory/v1", "release": "v0.9.0",
                          "execution_authorized": True,
                          "controls": [self._control()]}
        inventory_raw = self._json(self.inventory)
        self._write("reports/releases/v0.9.0/execution-v1/control-inventory.json", inventory_raw)
        self.contract = {
            "schema_version": 1, "release": "v0.9.0", "execution_authorized": True,
            "fixture_revision": FIXTURE,
            "parent_plan": {"path": "reports/releases/v0.9.0/plan.json", "sha256": self.sha(plan_raw)},
            "population": {"path": "populations/v0.9.0.json", "sha256": self.sha(population_raw)},
            "input_commits": plan["input_commits"],
            "input_identities": {
                "reports/releases/v0.9.0/input-pin.json": self.sha(b"pinned input\n"),
                "scripts/fake-control.py": self.sha(b"synthetic script identity\n"),
                "reports/releases/v0.9.0/execution-v1/control-inventory.json": self.sha(inventory_raw),
            },
            "control_inventory": {"path": "reports/releases/v0.9.0/execution-v1/control-inventory.json",
                                  "sha256": self.sha(inventory_raw)},
            "control_execution_roots": {self.control_id: str(self.root)},
            "tools": {}, "unresolved": [],
        }
        self._write(CONTRACT, self._json(self.contract))

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def sha(value):
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def _json(value):
        return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()

    def _write(self, rel, data):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def _control(self):
        return {
            "id": self.control_id, "argv": self.command,
            "environment": {"PATH": os.defpath, "TMPDIR": str(self.root / self.scratch)},
            "deadline_seconds": 5, "maximum_attempts": 2,
            "measurement_repeats": 2, "repeat_mechanism": "inside-harness-command",
            "output_roots": [self.output, self.scratch],
            "script_identity": [{"path": "scripts/fake-control.py", "sha256": self.sha(b"synthetic script identity\n")}],
        }

    def _install_command(self, code):
        self.command = [sys.executable, "-c", code]
        self.inventory["controls"][0]["argv"] = self.command
        raw = self._json(self.inventory)
        self._write("reports/releases/v0.9.0/execution-v1/control-inventory.json", raw)
        self.contract["input_identities"]["reports/releases/v0.9.0/execution-v1/control-inventory.json"] = self.sha(raw)
        self.contract["control_inventory"]["sha256"] = self.sha(raw)
        self._write(CONTRACT, self._json(self.contract))

    def _run_and_verify(self, expected):
        row = RECORDER.run_control(self.root, CONTRACT, self.control_id)
        self.assertEqual(row["status"], expected)
        attempt = Path(RECORDER.ATTEMPTS_PATH) / self.control_id / "attempt-01" / "completed.json"
        verified = RECORDER.verify_control(self.root, attempt, CONTRACT)
        self.assertTrue(verified["verified"])
        self.assertEqual(verified["status"], expected)
        self.assertEqual(len((self.root / RECORDER.LEDGER_PATH).read_text().splitlines()), 1)
        return row, attempt

    def test_successful_control_capture_and_verify_roundtrip(self):
        code = ("from pathlib import Path; "
                f"p=Path({self.output!r}); p.mkdir(parents=True); (p/'raw.bin').write_bytes(b'raw\\x00bytes'); "
                f"Path({self.scratch!r},'tmp.txt').write_text('scratch'); "
                "print('synthetic stdout')")
        self._install_command(code)
        result = RECORDER.validate_control(self.root, CONTRACT, self.control_id)
        self.assertEqual(result["control"]["measurement_repeats"], 2)
        self.assertEqual(result["execution_root"], str(self.root))
        row, receipt = self._run_and_verify("completed")
        self.assertEqual(len(row["captured_files"]), 2)

    def test_failed_control_is_captured_and_verifiable(self):
        code = ("from pathlib import Path; "
                f"p=Path({self.output!r}); p.mkdir(parents=True); (p/'partial').write_text('kept'); "
                "print('failure output'); raise SystemExit(7)")
        self._install_command(code)
        row, _ = self._run_and_verify("failed")
        self.assertEqual(row["exit_code"], 7)
        self.assertTrue(row["captured_files"])

    def test_runner_binary_only_control_uses_runner_build_provenance(self):
        binary = self.root / "fake-runner"
        binary.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\n"
                          f"p=Path({self.output!r}); p.mkdir(parents=True); (p/'runner.bin').write_bytes(b'ok')\n")
        binary.chmod(0o755)
        digest = self.sha(binary.read_bytes())
        self.command = [str(binary), "probe"]
        self.inventory["controls"][0]["argv"] = self.command
        self.inventory["controls"][0]["script_identity"] = []
        self.inventory["controls"][0]["output_roots"] = [self.output, self.scratch]
        inventory_raw = self._json(self.inventory)
        self._write("reports/releases/v0.9.0/execution-v1/control-inventory.json", inventory_raw)
        self.contract["input_identities"].pop("scripts/fake-control.py")
        self.contract["input_identities"]["reports/releases/v0.9.0/execution-v1/control-inventory.json"] = self.sha(inventory_raw)
        self.contract["control_inventory"]["sha256"] = self.sha(inventory_raw)
        self.contract["tools"]["runner"] = {"path": str(binary), "sha256": digest}
        self.contract["runner_build"] = {"binary_path": str(binary), "binary_sha256": digest,
            "source_commit": "b" * 40, "source_files": {"src/main.rs": "c" * 64},
            "schema": "release-runner-build/v1"}
        self._write(CONTRACT, self._json(self.contract))
        validated = RECORDER.validate_control(self.root, CONTRACT, self.control_id)
        self.assertEqual(validated["script_identity"], [])
        self.assertEqual(validated["runner_identity"]["sha256"], digest)
        row, _ = self._run_and_verify("completed")
        self.assertEqual(row["script_identity"], [])
        self.assertEqual(row["runner_identity"]["sha256"], digest)

    def test_existing_attempt_does_not_allocate_attempt_two(self):
        prior = self.root / RECORDER.ATTEMPTS_PATH / self.control_id / "attempt-01"
        prior.mkdir(parents=True)
        with self.assertRaisesRegex(RECORDER.ControlError, "existing control attempt"):
            RECORDER.validate_control(self.root, CONTRACT, self.control_id)
        self.assertFalse((prior.parent / "attempt-02").exists())

    def test_tampered_capture_is_rejected(self):
        self._install_command(f"from pathlib import Path; p=Path({self.output!r}); p.mkdir(parents=True); (p/'raw').write_text('original')")
        row = RECORDER.run_control(self.root, CONTRACT, self.control_id)
        captured = self.root / RECORDER.ATTEMPTS_PATH / self.control_id / "attempt-01" / "capture" / self.output / "raw"
        captured.write_text("tampered")
        with self.assertRaisesRegex(RECORDER.ControlError, "digest mismatch|tree differs"):
            receipt = captured.parents[4] / "completed.json"
            RECORDER.verify_control(self.root, receipt.relative_to(self.root), CONTRACT)

    def test_success_with_missing_declared_root_is_recorder_error(self):
        self._install_command("print('did not create declared outputs')")
        row, _ = self._run_and_verify("recorder-error")
        self.assertIn(self.output, row["missing_output_roots"])

    def test_timeout_is_terminal_and_verifiable(self):
        self.inventory["controls"][0]["deadline_seconds"] = 1
        self._install_command("import time; time.sleep(3)")
        row, _ = self._run_and_verify("timed-out")
        self.assertTrue(row["timed_out"])

    def test_unauthorized_validation_and_existing_attempt_have_no_launch_side_effects(self):
        self.contract["execution_authorized"] = False
        self._write(CONTRACT, self._json(self.contract))
        validated = RECORDER.validate_control(self.root, CONTRACT, self.control_id, require_authorized=False)
        self.assertFalse(validated["authorized"])
        with self.assertRaisesRegex(RECORDER.ControlError, "validation-only"):
            RECORDER.run_control(self.root, CONTRACT, self.control_id)
        self.assertFalse((self.root / RECORDER.ATTEMPTS_PATH).exists())


if __name__ == "__main__":
    unittest.main()
