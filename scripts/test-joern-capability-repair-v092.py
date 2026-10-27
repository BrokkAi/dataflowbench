#!/usr/bin/env python3
"""Focused fail-closed tests for the Joern capability-repair shim."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock

import joern_capability_repair_v092 as repair


class FakeRunner(ModuleType):
    def __init__(self, old_plan: dict):
        super().__init__("fake_joern_runner")
        self.old_plan = old_plan
        self.calls: list[str] = []
        self.EXECUTION_PLAN_PATH = repair.OLD_PLAN_PATH

    def validate_plan(self, root: Path, plan_path: str):
        self.calls.append(plan_path)
        plan = json.loads((root / plan_path).read_text())
        return plan, {"status": "synthetic"}, {}


class JoernCapabilityRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "scripts").mkdir()
        shutil.copy2(repair.ROOT / "scripts/v092_qualification.py", self.root / "scripts/v092_qualification.py")
        self.old_relative = "base/plan.json"
        self.new_relative = "repair/plan.json"
        self.evidence_relative = "repair/evidence.json"
        self.source_relative = "repair/source.json"
        self.old_plan_path = self.root / self.old_relative
        self.new_plan_path = self.root / self.new_relative
        self.old_plan_path.parent.mkdir(parents=True)
        self.new_plan_path.parent.mkdir(parents=True)
        self.case_ids = [f"case-{index:03d}" for index in range(108)]
        self.attempted = set(self.case_ids[:96])
        self.unsupported = set(self.case_ids[96:])
        self.identity = {"tool": "joern", "tool_version": "4.0.660", "tool_build_identity": "joern:test", "adapter_version": "joern-normal-v092"}
        self.components = [{"name": "joern-root", "path": "/runtime/joern", "sha256": "a" * 64}]
        self.runtime = {"joern": "/runtime/joern/bin/joern", "frontend": "/runtime/frontend", "astgen": "/runtime/astgen", "compiler": "/runtime/swiftc"}
        self._build_artifacts()
        self.patchers = [
            mock.patch.object(repair, "OLD_PLAN_PATH", self.old_relative),
            mock.patch.object(repair, "OLD_PLAN_SHA256", repair.sha(self.old_plan_path)),
            mock.patch.object(repair, "RUNNER_PATH", "runner.py"),
            mock.patch.object(repair, "RUNNER_SHA256", "runner-sha"),
            mock.patch.object(repair, "_assert_canonical_historical_binding"),
        ]
        # The loader is bypassed by the fake runner, but constants still prove
        # that a real invocation would be hash-pinned.
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.fake_runner = FakeRunner(self.old_plan)

    def _write(self, relative: str, value: dict) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        path.write_bytes(raw)
        return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}

    def _build_control_capture(self, prefix: str, projection: str, control_plan_ref: dict) -> dict:
        capture_root = f"/capture/{prefix}"
        records = []
        for index in range(12):
            control = f"control-{index:02d}"
            case_id = self.case_ids[index]
            arm = "off" if index % 2 == 0 else "on"
            raw_capture = f"{capture_root}/{control}/{arm}"
            command = {
                "argv": ["/tool/swiftc", "-sdk", "/SDK", raw_capture + "/main.swift"],
                "cwd": raw_capture,
                "environment": {"LANG": "C"},
                "measurement_wrapper": [],
                "phase_id": "typecheck",
                "role": "analysis",
                "deadline_scope": "non-scored probe phase",
            }
            command_ref = self._write(f"controls/{prefix}/{index:02d}/command.json", command)
            raw_ref = self._write(f"controls/{prefix}/{index:02d}/raw.json", {
                "case_id": case_id,
                "control": control,
                "arm": arm,
                "capture_directory": raw_capture,
                "commands": [command_ref],
            })
            records.append({"control": control, "case_id": case_id, "arm": arm, "raw": raw_ref, "observed": "inconclusive"})
        return {
            "schema": "analyzer-qualification-control-run/v092",
            "group_id": repair.GROUP_ID,
            "execution_plan_projection_sha256": projection,
            "control_plan_sha256": control_plan_ref["sha256"],
            "phase_invocation_count": 36,
            "records": records,
        }

    def _build_artifacts(self) -> None:
        old_control = {
            "schema": "analyzer-qualification-control-plan/v092",
            "group_id": repair.GROUP_ID,
            "execution_plan_projection_sha256": "old-projection",
            "controls": {f"control-{index:02d}": self.case_ids[index] for index in range(12)},
            "arms": ["off", "on"],
            "case_arm_count": 12,
            "maximum_phase_invocations": 36,
            "case_arm_budget_seconds": 75,
            "total_budget_seconds": 900,
            "scratch_allowance_bytes": 1,
            "population_sha256": "population",
            "fixture_revision": "fixture",
            "identity": self.identity,
            "identity_components": self.components,
        }
        old_control_ref = self._write("qualification/old-control.json", old_control)
        old_run = self._build_control_capture("old", "old-projection", old_control_ref)
        old_run_ref = self._write("qualification/old-run.json", old_run)
        old_receipt = {
            "schema": "analyzer-qualification-receipt/v092",
            "group_id": repair.GROUP_ID,
            "execution_plan_projection_sha256": "old-projection",
            "control_run": old_run_ref,
            "identity": self.identity,
            "identity_components": self.components,
        }
        old_receipt_ref = self._write("qualification/old-receipt.json", old_receipt)

        cases = {}
        for case_id in self.case_ids:
            cases[case_id] = {"configuration": "joern-current108", "disposition": "attempt" if case_id in self.attempted else "unsupported", "phase_sequence": "joern-current108"}
        self.old_plan = {
            "schema": repair.PLAN_SCHEMA,
            "profile": "v0.9.2",
            "engine": "joern",
            "release_group_id": repair.GROUP_ID,
            "population_sha256": "population",
            "fixture_revision": "fixture",
            "identity": self.identity,
            "identity_components": self.components,
            "runtime": self.runtime,
            "codeql_packs": None,
            "query_root": "adapters/joern/swift-common-v2",
            "configurations": {"joern-current108": []},
            "cases": cases,
            "execution_contract": {"path": "contract.json", "sha256": "c" * 64},
            "qualification_control_projection_sha256": "old-projection",
            "qualification_control_plan": old_control_ref,
            "fresh_qualification": old_receipt_ref,
            "output_root": "reports/raw/joern-common-v2",
            "phase_sequence": "joern-current108",
            "resources": {"disk": "reserved"},
            "diagnostic_execution_eligible": True,
            "execution_eligible": True,
            "full_model_qualification": False,
            "scored_activation": False,
            "aggregate_resource_qualification": "unavailable",
            "status": "execution-eligible",
            "registered_at_unix_seconds": 1,
        }
        self.old_plan_ref = self._write(self.old_relative, self.old_plan)
        repair.OLD_PLAN_SHA256 = self.old_plan_ref["sha256"]

        capability = {"identity_gate": "exact-native-edges", "model_mode": "off", "model_status": "unqualified"}
        source_ref = self._write(self.source_relative, {"source": "reviewed-parent-mapping"})
        evidence = {
            "schema": repair.EVIDENCE_SCHEMA,
            "status": "independently-reviewed",
            "base_plan": {"path": self.old_relative, "sha256": self.old_plan_ref["sha256"]},
            "population_sha256": "population",
            "fixture_revision": "fixture",
            "cases": {case_id: {"capability": capability, "source_ref": source_ref, "provenance": "reviewed mapping"} for case_id in self.attempted},
        }
        self.evidence_ref = self._write(self.evidence_relative, evidence)
        repair.EVIDENCE_DEFAULT = self.evidence_relative

        new_cases = copy.deepcopy(cases)
        for case_id in self.attempted:
            new_cases[case_id]["capability"] = capability
        new_control = copy.deepcopy(old_control)
        new_control["execution_plan_projection_sha256"] = "placeholder"
        new_control_ref = self._write("qualification/new-control.json", new_control)
        new_run = self._build_control_capture("new", "placeholder", new_control_ref)
        new_run_ref = self._write("qualification/new-run.json", new_run)
        new_receipt = copy.deepcopy(old_receipt)
        new_receipt["execution_plan_projection_sha256"] = "placeholder"
        new_receipt["control_run"] = new_run_ref
        new_receipt_ref = self._write("qualification/new-receipt.json", new_receipt)
        self.new_plan = copy.deepcopy(self.old_plan)
        self.new_plan["cases"] = new_cases
        self.new_plan["qualification_control_plan"] = new_control_ref
        self.new_plan["fresh_qualification"] = new_receipt_ref
        self.new_plan["registered_at_unix_seconds"] = 2
        # Calculate the actual projection after the capabilities are present.
        sys.path.insert(0, str(self.root / "scripts"))
        import v092_qualification
        projection = v092_qualification.plan_projection_sha256(self.new_plan)
        self.new_plan["qualification_control_projection_sha256"] = projection
        for path, value in ((self.root / "qualification/new-control.json", new_control), (self.root / "qualification/new-receipt.json", new_receipt), (self.root / "qualification/new-run.json", new_run)):
            value["execution_plan_projection_sha256"] = projection
            path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        # The run references the newly rewritten control-plan digest.
        new_control_ref = {"path": new_control_ref["path"], "sha256": repair.sha(self.root / new_control_ref["path"])}
        new_run["control_plan_sha256"] = new_control_ref["sha256"]
        (self.root / "qualification/new-run.json").write_text(json.dumps(new_run, sort_keys=True, separators=(",", ":")) + "\n")
        new_run_ref = {"path": new_run_ref["path"], "sha256": repair.sha(self.root / new_run_ref["path"])}
        new_receipt["control_run"] = new_run_ref
        (self.root / "qualification/new-receipt.json").write_text(json.dumps(new_receipt, sort_keys=True, separators=(",", ":")) + "\n")
        new_receipt_ref = {"path": new_receipt_ref["path"], "sha256": repair.sha(self.root / new_receipt_ref["path"])}
        self.new_plan["qualification_control_plan"] = new_control_ref
        self.new_plan["fresh_qualification"] = new_receipt_ref
        self.new_plan_ref = self._write(self.new_relative, self.new_plan)
        self.fake_runner = None

    def _valid(self):
        fake = FakeRunner(self.old_plan)
        return repair.validate_repair_inputs(self.root, new_plan_path=self.new_relative, evidence_path=self.evidence_relative, runner_module=fake)

    def test_valid_repair_requires_old_validation_and_fresh_projection(self):
        result = self._valid()
        self.assertEqual(result["new_plan_sha256"], repair.sha(self.new_plan_path))
        self.assertNotEqual(result["projection_sha256"], "old-projection")

    def test_preflight_does_not_execute_analyzer(self):
        fake = FakeRunner(self.old_plan)
        result = repair.preflight(self.root, new_plan_path=self.new_relative, evidence_path=self.evidence_relative, runner_module=fake)
        self.assertEqual(result["new_plan_path"], self.new_relative)
        self.assertEqual(fake.calls, [self.old_relative, self.new_relative])
        self.assertNotIn("execute", fake.calls)

    def test_pending_bootstrap_allows_controls_before_receipt_exists(self):
        self.new_plan["status"] = "qualification-pending"
        self.new_plan["execution_eligible"] = False
        self.new_plan["diagnostic_execution_eligible"] = False
        self.new_plan.pop("fresh_qualification")
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        fake = FakeRunner(self.old_plan)
        result = repair.validate_bootstrap_inputs(
            self.root,
            new_plan_path=self.new_relative,
            evidence_path=self.evidence_relative,
            runner_module=fake,
        )
        self.assertEqual(result["new_plan_path"], self.new_relative)
        self.assertEqual(result["projection_sha256"], self.new_plan["qualification_control_projection_sha256"])

    def test_missing_capability_rejected(self):
        original = self.new_plan["cases"].pop("case-000").copy()
        self.addCleanup(lambda: self.new_plan["cases"].__setitem__("case-000", original))
        self.new_plan["cases"]["case-000"] = {"configuration": "joern-current108", "disposition": "attempt", "phase_sequence": "joern-current108"}
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "capability-only"):
            self._valid()

    def test_changed_mode_rejected(self):
        self.new_plan["cases"]["case-000"]["capability"]["model_mode"] = "on"
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "does not match reviewed evidence"):
            self._valid()

    def test_existing_case_field_mutation_rejected(self):
        self.new_plan["cases"]["case-000"]["configuration"] = "unreviewed-configuration"
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "pre-existing fields changed"):
            self._valid()

    def test_disposition_change_rejected(self):
        self.new_plan["cases"]["case-100"]["disposition"] = "attempt"
        self.new_plan["cases"]["case-100"]["capability"] = {"identity_gate": "exact-native-edges", "model_mode": "off", "model_status": "unqualified"}
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "unsupported case was changed"):
            self._valid()

    def test_identity_change_rejected(self):
        self.new_plan["identity"] = {**self.new_plan["identity"], "tool_version": "4.0.661"}
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "outside capabilities"):
            self._valid()

    def test_projection_change_or_stale_digest_rejected(self):
        self.new_plan["qualification_control_projection_sha256"] = self.old_plan["qualification_control_projection_sha256"]
        self.new_plan_path.write_text(json.dumps(self.new_plan))
        with self.assertRaisesRegex(repair.RepairError, "projection digest is not truthful"):
            self._valid()

    def test_evidence_source_digest_rejected(self):
        self._rewrite_evidence(lambda row: row["source_ref"].update(sha256="0" * 64))
        with self.assertRaisesRegex(repair.RepairError, "digest mismatch"):
            self._valid()

    def test_evidence_path_traversal_rejected(self):
        self._rewrite_evidence(lambda row: row["source_ref"].update(path="../escape.json"))
        with self.assertRaisesRegex(repair.RepairError, "safe relative path"):
            self._valid()

    def _rewrite_evidence(self, mutate) -> None:
        evidence = json.loads((self.root / self.evidence_relative).read_text())
        mutate(next(iter(evidence["cases"].values())))
        (self.root / self.evidence_relative).write_text(json.dumps(evidence))


if __name__ == "__main__":
    unittest.main()
