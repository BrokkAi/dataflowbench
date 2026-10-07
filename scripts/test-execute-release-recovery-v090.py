"""The v0.9 recovery executor is bounded, fail-stop, and recovery-only."""
import importlib.util
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "recovery_executor", Path(__file__).with_name("execute-release-recovery-v090.py")
)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class RecoveryExecutorTests(unittest.TestCase):
    def test_retained_recovery_inventory_has_stale_contract_arguments(self):
        packet = Path(__file__).resolve().parents[1] / "reports/releases/v0.9.0/execution-v1/resume-20261007-03"
        controls = json.loads((packet / "control-inventory.json").read_text())["controls"]
        with self.assertRaisesRegex(ValueError, "reviewed contract"):
            recovery.validate_control_contract_arguments(controls, "reports/releases/v0.9.0/execution-v1/resume-20261007-03/contract.json")

    def test_corrected_supplemental_arguments_and_invalid_variants(self):
        contract = "reports/releases/v0.9.0/execution-v1/replacement/contract.json"
        controls = [{"id": name, "argv": ["python3", "probe.py", "--contract", contract]}
                    for name in sorted(recovery.CONTRACT_CONTROLS)]
        recovery.validate_control_contract_arguments(controls, contract)
        for mutation in ("stale", "missing", "duplicate", "truncated"):
            changed = copy.deepcopy(controls)
            argv = changed[-1]["argv"]
            if mutation == "stale":
                argv[-1] = "reports/releases/v0.9.0/execution-v1/original/contract.json"
            elif mutation == "missing":
                del argv[-2:]
            elif mutation == "duplicate":
                argv.extend(["--contract", contract])
            else:
                argv.pop()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "reviewed contract"):
                recovery.validate_control_contract_arguments(changed, contract)

    def test_stale_bound_inventory_stops_before_preparation_or_claim(self):
        control = {"id": "probe-python-modeling-load-bearing",
                   "argv": ["python3", "probe.py", "--contract", "old-contract.json"]}
        inventory = json.dumps({"controls": [control]}).encode()
        contract = json.dumps({
            "execution_authorized": True, "unresolved": [],
            "control_inventory": {"path": "inventory.json",
                                  "sha256": hashlib.sha256(inventory).hexdigest()},
            "control_execution_roots": {control["id"]: "/unused/root"},
        }).encode()
        with patch.object(recovery, "_reviewed_file", side_effect=[contract, inventory]), \
                patch.object(recovery, "_run") as run:
            with self.assertRaisesRegex(ValueError, "reviewed contract"):
                recovery.execute_controls(Path("/unused/source"), "a" * 40,
                                          "new-contract.json", python="python3")
            run.assert_not_called()

    def test_launcher_constants_cannot_select_historical_executors(self):
        self.assertEqual(recovery.CONTROL_LAUNCHER,
                         "scripts/run-release-control-recovery-v090.py")
        self.assertEqual(recovery.GROUP_LAUNCHER,
                         "scripts/run-release-group-recovery-v090.py")
        self.assertNotIn("execute-release-control", recovery.CONTROL_LAUNCHER)
        self.assertNotIn("execute-release-v090.py", recovery.GROUP_LAUNCHER)

    def test_unauthorized_controls_never_prepare_or_launch(self):
        contract = {"execution_authorized": False, "control_inventory": {
            "path": "inventory.json", "sha256": "a" * 64},
                    "control_execution_roots": {}}
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(recovery, "reviewed_inventory", return_value=(contract, [])), \
                patch.object(recovery.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "final executable-plan"):
                recovery.execute_controls(Path(tmp), "a" * 40, "contract.json", python="python")
            run.assert_not_called()

    def test_control_uses_preparer_then_only_recovery_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            root = source / "control-root"
            contract = {"execution_authorized": True, "unresolved": [],
                        "control_execution_roots": {"one": str(root)}}
            calls = []

            def record(command, **kwargs):
                calls.append(command)

            with patch.object(recovery, "reviewed_inventory", return_value=(contract, [{"id": "one"}])), \
                    patch.object(recovery, "verified_control_completion", side_effect=[False, True]), \
                    patch.object(recovery, "_run", side_effect=record):
                recovery.execute_controls(source, "a" * 40, "contract.json", python="python")

            self.assertEqual(len(calls), 2)
            self.assertTrue(calls[0][1].endswith("prepare-release-root-v090.py"))
            self.assertTrue(calls[1][1].endswith("run-release-control-recovery-v090.py"))
            self.assertNotIn("execute-release-controls-v090.py", " ".join(calls[1]))
            self.assertIn("--execute", calls[1])

    def test_control_failure_stops_before_next_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            contract = {"execution_authorized": True, "unresolved": [],
                        "control_execution_roots": {"one": str(source / "one"),
                                                     "two": str(source / "two")}}
            with patch.object(recovery, "reviewed_inventory",
                              return_value=(contract, [{"id": "one"}, {"id": "two"}])), \
                    patch.object(recovery, "verified_control_completion", return_value=False), \
                    patch.object(recovery, "_run", side_effect=RuntimeError("first failure")) as run:
                with self.assertRaisesRegex(RuntimeError, "first failure"):
                    recovery.execute_controls(source, "a" * 40, "contract.json", python="python")
            self.assertEqual(run.call_count, 1)

    def test_matrix_skips_only_verified_completion_and_uses_recovery_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = {"execution_authorized": True, "unresolved": [],
                        "groups": [{"id": "one"}, {"id": "two"}], "control_execution_roots": {"control": str(root / "control")}}
            calls = []

            with patch.object(recovery, "verified_control_completion", return_value=True), \
                    patch.object(recovery, "_read_json", return_value=contract), \
                    patch.object(recovery, "verified_completed_groups",
                                  side_effect=[{"one"}, {"one", "two"}]), \
                    patch.object(recovery, "_run", side_effect=lambda command: calls.append(command)):
                recovery.execute_matrix(root, "contract.json", python="python")

            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0][1].endswith("run-release-group-recovery-v090.py"))
            self.assertNotIn("execute-release-v090.py", " ".join(calls[0]))
            self.assertIn("--group", calls[0])
            self.assertEqual(calls[0][calls[0].index("--group") + 1], "two")

    def test_matrix_tampered_resume_stops_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = {"execution_authorized": True, "unresolved": [],
                        "groups": [{"id": "one"}], "control_execution_roots": {"control": str(root / "control")}}
            with patch.object(recovery, "verified_control_completion", return_value=True), \
                    patch.object(recovery, "_read_json", return_value=contract), \
                    patch.object(recovery, "verified_completed_groups",
                                  side_effect=ValueError("receipt digest mismatch")), \
                    patch.object(recovery, "_run") as run:
                with self.assertRaisesRegex(ValueError, "receipt digest mismatch"):
                    recovery.execute_matrix(root, "contract.json", python="python")
            run.assert_not_called()

    def test_matrix_launcher_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = {"execution_authorized": True, "unresolved": [],
                        "groups": [{"id": "one"}, {"id": "two"}], "control_execution_roots": {"control": str(root / "control")}}
            with patch.object(recovery, "verified_control_completion", return_value=True), \
                    patch.object(recovery, "_read_json", return_value=contract), \
                    patch.object(recovery, "verified_completed_groups", return_value=set()), \
                    patch.object(recovery, "_run", side_effect=RuntimeError("launcher failed")) as run:
                with self.assertRaisesRegex(RuntimeError, "launcher failed"):
                    recovery.execute_matrix(root, "contract.json", python="python")
            self.assertEqual(run.call_count, 1)

    def test_started_only_control_is_not_resumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempt = root / recovery.CONTROL_ATTEMPTS / "one" / "attempt-01"
            attempt.mkdir(parents=True)
            (attempt / "started.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                recovery.verified_control_completion(root, "contract.json", "one")

    def test_matrix_requires_controls_before_any_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = {"execution_authorized": True, "unresolved": [],
                        "groups": [{"id": "one"}],
                        "control_execution_roots": {"one": str(root / "missing-control")}}
            with patch.object(recovery, "_read_json", return_value=contract), \
                    patch.object(recovery, "_run") as run:
                with self.assertRaisesRegex(ValueError, "verified completed control"):
                    recovery.execute_matrix(root, "contract.json", python="python")
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
