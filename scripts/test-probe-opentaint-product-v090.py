#!/usr/bin/env python3
"""Mock-only contract, identity, receipt and interruption tests for v0.9 probe."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import tempfile
import unittest
from unittest.mock import Mock, call, patch


SCRIPT = Path(__file__).with_name("probe-opentaint-product-v090.py")
SPEC = importlib.util.spec_from_file_location("opentaint_product_v090", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Fixture:
    def __init__(self, base: Path):
        self.root = base
        self.bundle = base / "bundle"
        self.bundle.mkdir()
        self._write(self.bundle / "opentaint", b"mock wrapper bytes", 0o755)
        self._write(self.bundle / "jre/bin/java", b"mock bundled java", 0o755)
        self._write(self.bundle / "lib/rules/builtin.yaml", b"mock builtin rules")
        filler = self.bundle / "payload"
        filler.mkdir()
        # The restoration points at the historical 329-file identity.
        for index in range(326):
            self._write(filler / f"member-{index:03}.bin", f"member {index}\n".encode())
        files = sorted(p for p in self.bundle.rglob("*") if p.is_file())
        assert len(files) == 329
        self.historical_rel = Path("reports/releases/v0.7.1/opentaint-full-bundle-identity.json")
        self.historical_path = self.root / self.historical_rel
        self.historical_path.parent.mkdir(parents=True)
        archive_sha = "a" * 64
        historical = {
            "archive_sha256": archive_sha,
            "files": [{"relative_path": p.relative_to(self.bundle).as_posix(), "sha256": sha(p.read_bytes())}
                      for p in files],
        }
        self._json(self.historical_path, historical)
        self.restoration_rel = MODULE.RESTORATION_REL
        self.restoration_path = self.root / self.restoration_rel
        self.restoration_path.parent.mkdir(parents=True)
        restoration = {
            "schema": "runtime-restoration/v1", "bundle_root": str(self.bundle),
            "archive_sha256": archive_sha, "exact_file_membership": True,
            "runtime_executed": False, "verified_files": 329,
            "reference": {"path": self.historical_rel.as_posix(), "sha256": sha(self.historical_path.read_bytes())},
        }
        self._json(self.restoration_path, restoration)
        self.runtime_rel = MODULE.RUNTIME_TREE_REL
        self.runtime_path = self.root / self.runtime_rel
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_tree = {
            "schema": "release-runtime-tree/v1", "root": str(self.bundle),
            "entries": MODULE._tree_entries(self.bundle), "external_files": {},
        }
        self._json(self.runtime_path, runtime_tree)

        javac = base / "jdk/bin/javac"
        self._write(javac, b"mock contract javac", 0o755)
        self.javac = javac
        self.control_root = base / "isolated-control-root"
        self.tmpdir = self.control_root / "reports/raw/control-scratch/probe-opentaint-product-v090"
        self.tmpdir.mkdir(parents=True)
        (self.root / "scripts").mkdir()
        self.probe_script = self.root / MODULE.SCRIPT_REL
        shutil.copyfile(SCRIPT, self.probe_script)

        self.control_rel = Path("reports/releases/v0.9.0/execution-v1/control-inventory.json")
        self.control_path = self.root / self.control_rel
        self.control_path.parent.mkdir(parents=True, exist_ok=True)
        control = {
            "controls": [{
                "id": "probe-opentaint-product-v090",
                "argv": ["/usr/bin/python3", MODULE.SCRIPT_REL.as_posix()],
                "deadline_seconds": 10200,
                "environment": {"HOME": str(base), "PATH": "/system/bin", "TMPDIR": str(self.tmpdir)},
                "output_roots": [MODULE.OUTPUT_REL.as_posix(), "reports/raw/control-scratch/probe-opentaint-product-v090"],
                "script_identity": [{"path": MODULE.SCRIPT_REL.as_posix(), "sha256": sha(self.probe_script.read_bytes())}],
            }]
        }
        self._json(self.control_path, control)
        contract = {
            "schema": "release-execution-contract/v1", "release": "v0.9.0",
            "execution_authorized": True, "unresolved": [],
            "tools": {
                "opentaint-wrapper": {"path": str(self.bundle / "opentaint"),
                                      "sha256": sha((self.bundle / "opentaint").read_bytes()), "version": "0.4.6"},
                "javac": {"path": str(javac), "sha256": sha(javac.read_bytes())},
            },
            "groups": [{"id": "opentaint-java-native", "tool": "opentaint",
                        "environment": {"HOME": str(base), "JAVA_HOME": "/reviewed/jdk",
                                        "LANG": "C.UTF-8", "PATH": "/reviewed/jdk/bin:/usr/bin",
                                        "TMPDIR": "/private/tmp"}}],
            "runtime_trees": [{"path": self.runtime_rel.as_posix(), "sha256": sha(self.runtime_path.read_bytes())}],
            "control_inventory": {"path": self.control_rel.as_posix(), "sha256": sha(self.control_path.read_bytes())},
            "control_execution_roots": {"probe-opentaint-product-v090": str(self.control_root)},
            "input_identities": {
                self.restoration_rel.as_posix(): sha(self.restoration_path.read_bytes()),
                self.runtime_rel.as_posix(): sha(self.runtime_path.read_bytes()),
                self.control_rel.as_posix(): sha(self.control_path.read_bytes()),
            },
        }
        self.contract_rel = Path("reports/releases/v0.9.0/execution-v1/contract.json")
        self.contract_path = self.root / self.contract_rel
        self._json(self.contract_path, contract)

        cases = self.root / "cases/taint/java"
        for index in range(12):
            case = cases / f"native-case-{index:02}"
            case.mkdir(parents=True)
            (case / f"Case{index}.java").write_text(
                f"package dataflowbench.taint; class Case{index} {{}}\n", encoding="utf-8")

    @staticmethod
    def _write(path: Path, data: bytes, mode: int = 0o644) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)

    @staticmethod
    def _json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


class ProductProbeV090Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fx = Fixture(Path(self.temp.name))
        self.output = self.fx.root / MODULE.OUTPUT_REL

    def capture(self, runner):
        return MODULE.capture(
            self.fx.root, self.fx.contract_rel, MODULE.OUTPUT_REL,
            probe_script_path=self.fx.probe_script, runner=runner,
        )

    @staticmethod
    def successful_runner(calls):
        def run(argv, *, cwd, stdout, stderr, env, timeout):
            calls.append((list(map(str, argv)), dict(env), timeout))
            stdout.write(b"mock stdout\n")
            stderr.write(b"mock stderr\n")
            return 0
        return run

    def test_authorization_gate_has_no_output_or_runner_side_effect(self):
        contract = json.loads(self.fx.contract_path.read_text())
        contract["execution_authorized"] = False
        Fixture._json(self.fx.contract_path, contract)
        calls = []
        with self.assertRaisesRegex(MODULE.ProbeError, "execution_authorized"):
            self.capture(self.successful_runner(calls))
        self.assertFalse(self.output.exists())
        self.assertEqual(calls, [])

    def test_bundle_membership_is_verified_before_output_creation(self):
        (self.fx.bundle / "unregistered.bin").write_bytes(b"extra")
        calls = []
        with self.assertRaisesRegex(MODULE.ProbeError, "runtime tree membership"):
            self.capture(self.successful_runner(calls))
        self.assertFalse(self.output.exists())
        self.assertEqual(calls, [])

    def test_runs_mocked_help_and_all_fourteen_fixture_pairs_with_scoped_envs(self):
        calls = []
        self.assertEqual(self.capture(self.successful_runner(calls)), 0)
        self.assertEqual(len(calls), 31)
        records = [json.loads(line) for line in (self.output / "commands.jsonl").read_text().splitlines()]
        self.assertEqual(len(records), 31)
        self.assertEqual(sum(row["command_id"].endswith("-compile") for row in records), 14)
        self.assertEqual(sum(row["command_id"].endswith("-product") for row in records), 14)
        self.assertEqual(len([row for row in records if row["command_id"] in {"wrapper-version", "wrapper-help", "scan-help"}]), 3)
        compile_call = next(row for row in calls if "-nowarn" in row[0])
        product_call = next(row for row in calls if "--project-model" in row[0])
        self.assertEqual(compile_call[1]["JAVA_HOME"], "/reviewed/jdk")
        self.assertEqual(compile_call[1]["TMPDIR"], str(self.fx.tmpdir))
        self.assertEqual(product_call[1]["JAVA_HOME"], str(self.fx.bundle / "jre"))
        self.assertTrue(product_call[1]["PATH"].startswith(str(self.fx.bundle / "jre/bin") + os.pathsep))
        self.assertEqual(product_call[1]["TMPDIR"], str(self.fx.tmpdir))
        scope = json.loads((self.output / "scope.json").read_text())
        self.assertEqual(len(scope["native_fixtures"]), 12)
        self.assertEqual(scope["outer_deadline_seconds"], 10200)
        self.assertEqual(scope["nested_timeouts"], [])
        self.assertFalse((self.output / "reports/releases/v0.9.0").exists())
        with self.assertRaises(FileExistsError):
            self.capture(self.successful_runner([]))

    def test_nonzero_compile_is_retained_and_later_controls_continue(self):
        calls = []

        def run(argv, *, cwd, stdout, stderr, env, timeout):
            calls.append(list(map(str, argv)))
            stdout.write(b"captured\n")
            stderr.write(b"captured\n")
            return 9 if "-nowarn" in argv and not any("-nowarn" in x for x in calls[:-1]) else 0

        self.assertEqual(self.capture(run), 1)
        records = [json.loads(line) for line in (self.output / "commands.jsonl").read_text().splitlines()]
        self.assertEqual(records[3]["status"], "failed")
        self.assertEqual(records[4]["status"], "skipped-after-prerequisite-failure")
        self.assertTrue(any(row["command_id"] == "servlet-positive-product" and row["status"] == "succeeded" for row in records))
        self.assertTrue((self.output / "native-case-00-compile-stderr.txt").exists())
        self.assertEqual(len(calls), 30)

    def test_interrupt_cleans_child_group_and_command_recorder_persists_failure(self):
        process = Mock()
        process.pid = 41234
        first_wait = True

        def wait(timeout=None):
            nonlocal first_wait
            if first_wait:
                first_wait = False
                os.kill(os.getpid(), signal.SIGTERM)
            return 0

        process.wait.side_effect = wait
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch.object(MODULE.subprocess, "Popen", return_value=process), \
                 patch.object(MODULE.os, "killpg") as killpg:
                with (out / "o").open("wb") as stdout, (out / "e").open("wb") as stderr:
                    with self.assertRaises(MODULE.ProbeInterrupted):
                        MODULE._run_bounded(["mock"], cwd=out, stdout=stdout, stderr=stderr,
                                            env={}, timeout=1)
                self.assertEqual(killpg.call_args_list, [call(41234, signal.SIGTERM), call(41234, signal.SIGKILL)])

            command_out = out / "command-out"
            command_out.mkdir()

            def interrupted(*args, **kwargs):
                raise MODULE.ProbeInterrupted("mock outer interruption")

            with self.assertRaises(MODULE.ProbeInterrupted):
                MODULE._record_command(command_out, command_id="interrupted", argv=["mock"], env={},
                                       identities={}, runner=interrupted, timeout=1, cwd=out)
            receipt = json.loads((command_out / "commands.jsonl").read_text())
            self.assertEqual(receipt["status"], "interrupted")
            self.assertIn("ProbeInterrupted", receipt["error"])


if __name__ == "__main__":
    unittest.main()
