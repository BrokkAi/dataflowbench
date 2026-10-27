#!/usr/bin/env python3
"""Exercise Joern v0.9.2 receipt replay against retained control artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest

import joern_normal_controls_v1 as historical_controls
import joern_normal_runner_v092 as runner


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "direct-positive": {"off": "reached", "on": "reached"},
    "direct-negative": {"off": "not-reached", "on": "not-reached"},
    "dfb-taint-swift-model-opaque-propagator-positive": {"off": "not-reached", "on": "reached"},
    "dfb-taint-swift-model-opaque-propagator-negative": {"off": "reached", "on": "not-reached"},
    "dfb-taint-swift-model-propagator-position-positive": {"off": "not-reached", "on": "reached"},
    "dfb-taint-swift-model-propagator-position-negative": {"off": "not-reached", "on": "not-reached"},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class JoernReceiptReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.runtime = {
            "joern": str(self.root / "joern-cli"),
            "frontend": str(self.root / "swiftsrc2cpg"),
            "astgen": str(self.root / "SwiftAstGen-mac"),
            "compiler": str(self.root / "swiftc"),
        }
        self.identity = {
            "tool": "joern",
            "tool_version": "4.0.660",
            "tool_build_identity": "joern-cli:4.0.660;engine:" + "a" * 64 + ";frontend:" + "b" * 64,
            "adapter_version": "joern-normal-v092",
        }
        self.components = [{"name": "joern-root", "path": str(self.root / "tree.json"), "sha256": "c" * 64}]
        self.plan = {
            "identity": self.identity,
            "identity_components": self.components,
            "runtime": self.runtime,
            "qualification_control_projection_sha256": "d" * 64,
        }
        self.cases = {}
        for index, (label, case_id) in enumerate(runner.CONTROL_CASES.items()):
            template = "dfb-template-model-opaque-propagator" if "opaque-propagator" in case_id else (
                "dfb-template-model-propagator-position" if "propagator-position" in case_id else "dfb-template-direct-propagation"
            )
            case_path = self.root / "cases" / case_id / "case.json"
            case_path.parent.mkdir(parents=True, exist_ok=True)
            case_path.write_text(json.dumps({"id": case_id}))
            (case_path.parent / "main.swift").write_text("// fixture " + str(index) + "\n")
            self.cases[case_id] = {"id": case_id, "path": case_path.relative_to(self.root).as_posix(), "fixture_files": ["main.swift"], "template_id": template}

        self.engine = SimpleNamespace(
            normalized=lambda outcome: outcome if outcome in ("runner-error", "unsupported") else "inconclusive",
            config_for=lambda _root, case, arm: {"case_id": case["id"], "arm": arm},
            observe=lambda graph, _config: (graph["observed_outcome"], []),
            compiler_argv=lambda runtime, case, directory: [runtime["compiler"], case["id"], "-typecheck", str(directory)],
            frontend_argv=lambda runtime, directory: [runtime["frontend"], str(directory / "cpg.bin")],
            query_argv=lambda _root, runtime, directory: [runtime["joern"], "--script", str(directory / "query.sc")],
            assess_controls=historical_controls.assess_controls,
        )
        self.control_plan = {"controls": runner.CONTROL_CASES}

    def _write(self, relative: str, value: dict) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        path.write_bytes(raw)
        return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}

    def _ref(self, path: Path) -> dict:
        return {"path": path.relative_to(self.root).as_posix(), "sha256": sha(path)}

    def _copy_to_capture(self, path: Path, capture_root: Path) -> None:
        destination = capture_root / path.resolve().relative_to(self.root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())

    def _build_run(self, *, failed_phase: bool = False, failed_states: bool = False,
                   capture_root: Path | None = None) -> dict:
        capture_root = self.root if capture_root is None else capture_root.resolve()
        if capture_root != self.root:
            for case in self.cases.values():
                source_dir = (self.root / case["path"]).parent
                copied_dir = capture_root / source_dir.relative_to(self.root)
                copied_dir.mkdir(parents=True, exist_ok=True)
                for source in source_dir.iterdir():
                    if source.is_file():
                        (copied_dir / source.name).write_bytes(source.read_bytes())
        version_dir = self.root / "qualification" / "identity"
        version_dir.mkdir(parents=True, exist_ok=True)
        banner = version_dir / "version.stdout"
        banner.write_text("joern-cli 4.0.660\n")
        capture_directory = capture_root / "qualification/identity"
        capture_directory.mkdir(parents=True, exist_ok=True)
        version_command = {
            "argv": [self.runtime["joern"]],
            "cwd": str(capture_directory),
            "exit_status": 0,
            "timed_out": False,
            "cleanup_status": "tracked-processes-stopped",
        }
        witness = self._write("qualification/identity/identity.json", {
            "observed": self.identity,
            "capture_root": str(capture_root),
            "capture_directory": str(capture_directory),
            "command": version_command,
            "stdout": self._ref(banner),
        })
        self._copy_to_capture(banner, capture_root)
        self._copy_to_capture(self.root / "qualification/identity/identity.json", capture_root)
        records = []
        for control, case_id in self.control_plan["controls"].items():
            case = self.cases[case_id]
            case_path = self.root / case["path"]
            for arm in runner.CONTROL_ARMS:
                leaf = self.root / "qualification" / "controls" / control / arm
                leaf.mkdir(parents=True, exist_ok=True)
                capture_leaf = capture_root / leaf.relative_to(self.root)
                capture_leaf.mkdir(parents=True, exist_ok=True)
                outcome = "runner-error" if failed_states else EXPECTED[control][arm]
                graph = leaf / "graph.json"
                graph.write_text(json.dumps({"observed_outcome": outcome}))
                config = leaf / "config.json"
                config.write_text(json.dumps(self.engine.config_for(capture_root, case, arm)))
                native = [self._ref(graph), self._ref(config)]
                self._copy_to_capture(graph, capture_root)
                self._copy_to_capture(config, capture_root)
                commands = []
                phase_ids = ("typecheck", "frontend", "query")
                for index, phase_id in enumerate(phase_ids):
                    if failed_phase and control == "direct-positive" and arm == "off" and index == 0:
                        break
                    if phase_id == "typecheck":
                        argv = self.engine.compiler_argv(self.runtime, case, capture_leaf)
                    elif phase_id == "frontend":
                        argv = self.engine.frontend_argv(self.runtime, capture_leaf)
                    else:
                        argv = self.engine.query_argv(capture_root, self.runtime, capture_leaf)
                    command = self._write(f"qualification/controls/{control}/{arm}/{phase_id}.command.json", {
                        "phase_id": phase_id,
                        "role": "analysis",
                        "argv": argv,
                        "cwd": str(capture_leaf),
                        "exit_status": 0,
                        "timed_out": False,
                        "cleanup_status": "tracked-processes-stopped",
                        "elapsed_seconds": 1,
                        "deadline_seconds": 75,
                    })
                    commands.append(command)
                    self._copy_to_capture(self.root / command["path"], capture_root)
                raw_path = leaf / "raw.json"
                raw = {
                    "schema": "joern-common-control-raw/v092",
                    "case_id": case_id,
                    "control": control,
                    "arm": arm,
                    "plan_projection_sha256": self.plan["qualification_control_projection_sha256"],
                    "identity": self.identity,
                    "identity_components": self.components,
                    "capture_root": str(capture_root),
                    "capture_directory": str(capture_leaf),
                    "fixture_hashes": {name: sha(case_path.parent / name) for name in case["fixture_files"]},
                    "raw_outcome": outcome,
                    "state": outcome if outcome in ("runner-error", "unsupported") else "inconclusive",
                    "diagnostics": [],
                    "commands": commands,
                    "native_outputs": native,
                }
                raw_path.write_text(json.dumps(raw))
                self._copy_to_capture(graph, capture_root)
                self._copy_to_capture(config, capture_root)
                records.append({"control": control, "case_id": case_id, "arm": arm, "raw": self._ref(raw_path), "observed": outcome})
        return {
            "schema": "analyzer-qualification-control-run/v092",
            "group_id": runner.GROUP_ID,
            "identity": self.identity,
            "identity_components": self.components,
            "identity_witness": witness,
            "elapsed_seconds": 20,
            "records": records,
            "phase_invocation_count": sum(len(json.loads((self.root / row["raw"]["path"]).read_text())["commands"]) for row in records),
        }

    def test_valid_control_run_replays_exact_positive_negative_and_model_arms(self):
        run = self._build_run()
        observations, invocations = runner._replay_control_run(self.root, self.plan, self.control_plan, run, self.cases, self.engine)
        assessment = self.engine.assess_controls(observations)
        self.assertEqual(invocations, 36)
        self.assertEqual(assessment["status"], "bounded-controls-observed")

    def test_missing_phase_command_rejects_receipt(self):
        run = self._build_run(failed_phase=True)
        with self.assertRaisesRegex(ValueError, "all three command phase records"):
            runner._replay_control_run(self.root, self.plan, self.control_plan, run, self.cases, self.engine)

    def test_receipt_cannot_claim_qualification_when_all_raw_controls_fail(self):
        run = self._build_run(failed_states=True)
        observations, invocations = runner._replay_control_run(self.root, self.plan, self.control_plan, run, self.cases, self.engine)
        assessment = self.engine.assess_controls(observations)
        self.assertEqual(invocations, 36)
        self.assertEqual(assessment["status"], "incomplete")
        self.assertTrue(assessment["failures"])

    def test_capture_root_remains_exact_when_replaying_from_a_fresh_snapshot(self):
        capture_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(capture_tmp.cleanup)
        capture_root = Path(capture_tmp.name).resolve()
        run = self._build_run(capture_root=capture_root)
        relocated_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(relocated_tmp.cleanup)
        relocated = Path(relocated_tmp.name).resolve()
        shutil.copytree(self.root, relocated, dirs_exist_ok=True)
        capture_tmp.cleanup()
        self.assertFalse(capture_root.exists())
        observations, invocations = runner._replay_control_run(
            relocated, self.plan, self.control_plan, run, self.cases, self.engine
        )
        self.assertEqual(invocations, 36)
        self.assertEqual(self.engine.assess_controls(observations)["status"], "bounded-controls-observed")

    def test_capture_complete_does_not_promote_failed_control_assessment(self):
        run = {"records": [{} for _ in range(12)], "phase_invocation_count": 36,
               "assessment": {"status": "incomplete"}}
        summary = runner.summarize_control_capture(run)
        self.assertEqual(summary["status"], "capture-complete-qualification-incomplete")
        self.assertEqual(summary["capture_status"], "complete")
        self.assertFalse(summary["qualification_eligible"])

    def test_capture_and_qualification_statuses_are_separate(self):
        run = {"records": [{} for _ in range(12)], "phase_invocation_count": 36,
               "assessment": {"status": "bounded-controls-observed"}}
        summary = runner.summarize_control_capture(run)
        self.assertEqual(summary["status"], "complete")
        self.assertTrue(summary["qualification_eligible"])


if __name__ == "__main__":
    unittest.main()
