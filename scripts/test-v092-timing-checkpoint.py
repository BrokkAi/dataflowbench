#!/usr/bin/env python3
"""Focused synthetic tests for v092_timing_checkpoint.py."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import v092_timing_checkpoint as checkpoint


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


class CheckpointFixture:
    def __init__(self, root: Path):
        self.root = root
        self.campaign_id = "20261115-01"
        self.report = root / "reports/timing/v0.9.2" / self.campaign_id
        self.work = root / "execution-state" / f"timing-v092-{self.campaign_id}"
        self.report.mkdir(parents=True)

        ready_cold = []
        for index in range(82):
            group_id = checkpoint.EXPECTED_FIRST_REMAINING if index == 55 else f"cold-{index:02d}"
            ready_cold.append(self._group(group_id, "cold", "ready", index))
        blocked = [
            self._group("joern-swift-common108", "cold", "blocked", 82),
            self._group("codeql-swift-common108", "cold", "blocked", 83),
        ]
        overhead = [self._group(f"overhead-{index:02d}", "overhead", "ready", index)
                    for index in range(9)]
        warm = [self._group(f"warm-{index:02d}", "warm", "ready", index) for index in range(2)]
        groups = [*ready_cold, *blocked, *overhead, *warm]
        ready = [group for group in groups if group["status"] == "ready"]
        self.completed = [group["id"] for group in ready[:checkpoint.EXPECTED_COMPLETED]]
        self.remaining = [group["id"] for group in ready[checkpoint.EXPECTED_COMPLETED:]]
        self.plan = {
            "schema": "v092-qualified-timing-campaign-plan/v1",
            "campaign_id": self.campaign_id,
            "created_utc": "2026-11-15T00:00:00+00:00",
            "launch_after_utc": "2026-11-15T00:00:00+00:00",
            "max_campaign_wall_seconds": 172800,
            "release_commit": "e" * 40,
            "population": "v0.9.0",
            "fixture_revision": "fixture-r1",
            "frozen_release_unchanged": True,
            "new_campaign_not_old_series_resume": True,
            "source_plan": {"path": "reports/timing/v0.9.2/source-plan.json",
                             "sha256": "a" * 64, "bindings_sha256": "b" * 64},
            "runtime_bindings": {"path": "reports/timing/v0.9.2/20261115-01/bindings.json",
                                 "sha256": "c" * 64},
            "preregistration": {"path": "reports/timing/v0.9.2/prereg.md", "sha256": "d" * 64},
            "frozen_execution_contract": {"path": "reports/releases/v0.9.2/contract.json",
                                          "sha256": "e" * 64},
            "source_projection": {"commit": "e" * 40, "additional_paths": ["reports"]},
            "source_cold_group_order": [group["id"] for group in [*ready_cold, *blocked]],
            "path_rebindings": {},
            "tools": {"runner": {"path": "/opt/runner", "sha256": "1" * 64}},
            "runtimes": [{"id": "runtime-r1", "path": "reports/runtime.json", "sha256": "2" * 64}],
            "source_execution_helpers": {"scripts/helper.py": "3" * 64},
            "helper_transitions": {},
            "execution_helpers": {"scripts/helper.py": "3" * 64,
                                  checkpoint.QUALIFIED_HELPER: "4" * 64},
            "frozen_report_bindings": {
                group["id"]: [{"contract_path": group["reports"][0]["path"],
                               "sha256": "f" * 64, "identity": {}}]
                for group in [*ready_cold, *blocked]
            },
            "group_order": [group["id"] for group in groups],
            "groups": groups,
            "planned_coverage": {"cold_groups": 84, "ready_cold_groups": 82,
                                 "blocked_cold_groups": 2, "full_coverage_claimed": False},
            "qualification": {"note": "unchanged", "publication_eligible": False,
                              "quiet_window": "300 seconds, 90 percent idle"},
            "resources": {"launch_free_gib": 127, "continuous_free_gib": 125,
                          "working_source_gib": 30, "per_source_gib": 12,
                          "scratch_gib": 24, "retention_gib": 24,
                          "serial_analyzers": 1, "automatic_retry": False,
                          "total_execution_budget_seconds": 93 * 10},
        }
        self.plan_path = self.report / "qualified-plan.json"
        self.plan_path.write_bytes(_json_bytes(self.plan))
        self.plan_sha = hashlib.sha256(self.plan_path.read_bytes()).hexdigest()

        progress = []
        for group_id in self.completed:
            progress.extend([
                {"group": group_id, "status": "started", "utc": "2026-11-15T01:00:00Z"},
                {"group": group_id, "status": "completed-candidate-evidence",
                 "utc": "2026-11-15T01:01:00Z"},
            ])
        self.progress_path = self.report / "progress.jsonl"
        self.progress_path.write_text("".join(json.dumps(row) + "\n" for row in progress))
        progress_sha = hashlib.sha256(self.progress_path.read_bytes()).hexdigest()

        for group_id in self.completed:
            group = next(group for group in ready if group["id"] == group_id)
            self._write_completed(group)
        pending_attempt = self.report / "attempts" / self.remaining[0] / "attempt-01"
        pending_attempt.mkdir(parents=True)
        (pending_attempt / "host.jsonl").write_text('{"phase":"settle-before-group"}\n')

        start = {
            "campaign_id": self.campaign_id,
            "created_utc": "2026-11-15T00:00:00Z",
            "plan_sha256": self.plan_sha,
            "plan_commit": "9" * 40,
            "source_commit": self.plan["release_commit"],
            "ready_commands": 93,
            "planned_cold_groups": 84,
            "ready_cold_groups": 82,
            "blocked_cold_groups": 2,
            "max_campaign_wall_seconds": 172800,
            "external_scratch_ownership": {},
            "scratch_roots": self._scratch_roots(ready),
        }
        (self.report / "campaign-start.json").write_bytes(_json_bytes(start))
        pause = {
            "schema": "dataflowbench-v092-user-pause/v1",
            "campaign_id": self.campaign_id,
            "paused_utc": "2026-11-15T02:00:00Z",
            "status": "paused-between-commands",
            "signal": "SIGSTOP",
            "observed_process_state": "Ts",
            "supervisor_pid": 1234,
            "supervisor_start_identity": "123456:789",
            "supervisor_command": "/usr/bin/python3 -B scripts/v092_timing_qualified_campaign.py execute --plan reports/timing/v0.9.2/20261115-01/qualified-plan.json",
            "active_analyzer_groups": [],
            "completed_command_count": 55,
            "completed_groups": self.completed,
            "remaining_ready_command_count": 38,
            "remaining_ready_groups": self.remaining,
            "progress_sha256": progress_sha,
            "plan_sha256": self.plan_sha,
            "existing_evidence_unchanged": True,
            "invocations_interrupted": False,
            "automatic_resume": False,
        }
        self.pause_path = self.report / "campaign-pause-01.json"
        self.pause_path.write_bytes(_json_bytes(pause))

    def _group(self, group_id: str, kind: str, status: str, index: int) -> dict:
        group = {"id": group_id, "kind": kind, "status": status, "family": "bifrost",
                 "argv": ["/opt/runner", "--group", group_id], "environment": {"PROFILE": "default"},
                 "deadline_seconds": 10, "runtime_ids": ["runtime-r1"], "setup_files": []}
        if kind == "cold":
            group["case_ids"] = [f"case-{group_id}"]
            group["reports"] = [{"case_ids": group["case_ids"], "ordinal": 0,
                                  "path": f"reports/releases/v0.9.2/normal/{group_id}.json",
                                  "source_path": f"reports/{group_id}.json", "tool": "bifrost"}]
            group["output_roots"] = [f"reports/{group_id}.json", f"reports/raw/{group_id}"]
        else:
            group["output_roots"] = [f"reports/raw/{group_id}"]
        if status == "blocked":
            group["blocker"] = "Swift runtime unavailable"
            group["runtime_ids"] = []
        return group

    def _scratch_roots(self, ready: list[dict]) -> list[str]:
        result = []
        for group in ready:
            source = self.work / "sources" / group["id"]
            result.extend(str(source / name) for name in ("home", "tmp", "cache"))
        return result

    def _write_completed(self, group: dict) -> None:
        group_id = group["id"]
        source = self.work / "sources" / group_id
        report_file = source / group["reports"][0]["source_path"]
        raw_file = source / "reports/raw" / group_id / "result.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        raw_file.parent.mkdir(parents=True, exist_ok=True)
        raw_file.write_text(json.dumps({"raw": group_id}) + "\n")
        measured = {"results": [{"case_id": group["case_ids"][0],
                                  "raw_output": raw_file.relative_to(source).as_posix()}]}
        report_file.write_bytes(_json_bytes(measured))
        digest = hashlib.sha256(report_file.read_bytes()).hexdigest()
        attempt = self.report / "attempts" / group_id / "attempt-01"
        attempt.mkdir(parents=True)
        (attempt / "start.json").write_bytes(_json_bytes({
            "plan_sha256": self.plan_sha,
            "argv": group["argv"],
            "deadline_seconds": group["deadline_seconds"],
            "quiet_policy": {"required_seconds": 300, "minimum_idle_percent": 90,
                             "maximum_sample_gap_seconds": 60},
        }))
        (attempt / "host.jsonl").write_text('{"phase":"settle-before-group"}\n')
        terminal = {
            "group": group_id,
            "attempt": 1,
            "automatic_retry": False,
            "status": "completed-candidate-evidence",
            "exit_code": 0,
            "timed_out": False,
            "capacity_loss": None,
            "publication_eligible": False,
            "frozen_report_comparison": {
                "status": "matched",
                "publication_eligible": False,
                "reports": [{"contract_path": group["reports"][0]["path"],
                              "frozen_sha256": "f" * 64, "measured_sha256": digest}],
            },
            "reconciliation": {
                "kind": "cold",
                "publication_eligible": False,
                "reports": [{"path": str(report_file), "sha256": digest, "timing_sidecars": 1}],
            },
        }
        (attempt / "terminal.json").write_bytes(_json_bytes(terminal))


class TimingCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.fixture = CheckpointFixture(self.root)
        self.git_show = patch.object(checkpoint.subprocess, "check_output",
                                     return_value=self.fixture.plan_path.read_bytes())
        self.git_show.start()
        self.addCleanup(self.git_show.stop)

    def create(self) -> dict:
        return checkpoint.create_checkpoint(self.root, self.fixture.plan_path, self.fixture.pause_path)

    def write_checkpoint(self, value: dict) -> dict:
        path = self.root / "reports/timing/v0.9.2/20261121-01/continuation-checkpoint.json"
        path.parent.mkdir(parents=True)
        raw = _json_bytes(value)
        path.write_bytes(raw)
        return {"path": path.relative_to(self.root).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest()}

    def test_creates_exact_frontier_and_binds_parent_evidence(self):
        value = self.create()
        self.assertEqual(value["completed_groups"], self.fixture.completed)
        self.assertEqual(value["remaining_ready_groups"], self.fixture.remaining)
        self.assertEqual(len(value["completed_terminals"]), 55)
        paths = {item["path"] for item in value["evidence_files"]}
        self.assertIn("reports/timing/v0.9.2/20261115-01/campaign-pause-01.json", paths)
        self.assertIn("execution-state/timing-v092-20261115-01/sources/cold-00/reports/raw/cold-00/result.json", paths)
        self.assertIn("reports/timing/v0.9.2/20261115-01/attempts/joern-php-kernel/attempt-01/host.jsonl", paths)
        refs = checkpoint.input_references(value)
        self.assertEqual(len(refs), 59)
        self.assertFalse(any("host.jsonl" in item["path"] for item in refs))
        self.assertEqual(value["parent_report_root"], "reports/timing/v0.9.2/20261115-01")
        self.assertEqual(len(value["parent_source_roots"]), 93)

    def test_verify_checkpoint_rechecks_artifact_inventory(self):
        value = self.create()
        reference = self.write_checkpoint(value)
        verified = checkpoint.verify_checkpoint(self.root, reference)
        self.assertEqual(verified["completed_groups"], self.fixture.completed)
        raw = self.root / "execution-state/timing-v092-20261115-01/sources/cold-00/reports/raw/cold-00/result.json"
        raw.write_text("changed\n")
        with self.assertRaisesRegex(RuntimeError, "evidence_files"):
            checkpoint.verify_checkpoint(self.root, reference)

    def test_rejects_pending_group_start_record(self):
        attempt = self.fixture.report / "attempts" / self.fixture.remaining[0] / "attempt-01"
        (attempt / "start.json").write_text("{}\n")
        with self.assertRaisesRegex(RuntimeError, "quiet-window host.jsonl"):
            self.create()

    def test_rejects_pause_receipt_order_or_count_drift(self):
        pause = json.loads(self.fixture.pause_path.read_text())
        pause["remaining_ready_groups"][0], pause["remaining_ready_groups"][1] = (
            pause["remaining_ready_groups"][1], pause["remaining_ready_groups"][0])
        self.fixture.pause_path.write_bytes(_json_bytes(pause))
        with self.assertRaisesRegex(RuntimeError, "pause receipt group counts or order"):
            self.create()

    def test_continuation_delta_allows_only_referenced_budget_and_bindings(self):
        value = self.create()
        reference = self.write_checkpoint(value)
        child = json.loads(json.dumps(self.fixture.plan))
        child["campaign_id"] = "20261121-01"
        child["created_utc"] = "2026-11-21T00:00:00Z"
        child["launch_after_utc"] = "2026-11-21T00:00:00Z"
        child["preregistration"] = {"path": "reports/timing/v0.9.2/continued.md", "sha256": "5" * 64}
        child["runtime_bindings"] = {"path": "reports/timing/v0.9.2/new-bindings.json", "sha256": "6" * 64}
        child["source_plan"]["bindings_sha256"] = "7" * 64
        child["execution_helpers"][checkpoint.QUALIFIED_HELPER] = "8" * 64
        child["execution_helpers"][checkpoint.CHECKPOINT_HELPER] = "9" * 64
        child["resources"]["total_execution_budget_seconds"] = 38 * 10
        child["continuation"] = reference
        checkpoint.verify_checkpoint(self.root, reference, child)

        child["groups"][0]["environment"]["PROFILE"] = "changed"
        with self.assertRaisesRegex(RuntimeError, "commands, environments, profiles"):
            checkpoint.verify_checkpoint(self.root, reference, child)

    def test_rejects_command_deadline_status_resource_and_order_drift(self):
        value = self.create()
        reference = self.write_checkpoint(value)
        mutations = [
            ("argv", lambda plan: plan["groups"][0]["argv"].append("--profile-changed"),
             "commands, environments, profiles"),
            ("deadline", lambda plan: plan["groups"][0].__setitem__("deadline_seconds", 11),
             "commands, environments, profiles"),
            ("status", lambda plan: plan["groups"][0].__setitem__("status", "blocked"),
             "commands, environments, profiles"),
            ("resource", lambda plan: plan["resources"].__setitem__("launch_free_gib", 126),
             "resource setting"),
            ("order", lambda plan: plan["group_order"].reverse(),
             "commands, environments, profiles"),
        ]
        for label, mutate, expected in mutations:
            with self.subTest(label=label):
                child = json.loads(json.dumps(self.fixture.plan))
                child.update({
                    "campaign_id": "20261121-01",
                    "created_utc": "2026-11-21T00:00:00Z",
                    "launch_after_utc": "2026-11-21T00:00:00Z",
                    "preregistration": {"path": "reports/timing/v0.9.2/continued.md",
                                         "sha256": "5" * 64},
                    "runtime_bindings": {"path": "reports/timing/v0.9.2/new-bindings.json",
                                         "sha256": "6" * 64},
                    "continuation": reference,
                })
                child["source_plan"]["bindings_sha256"] = "7" * 64
                child["execution_helpers"][checkpoint.QUALIFIED_HELPER] = "8" * 64
                child["execution_helpers"][checkpoint.CHECKPOINT_HELPER] = "9" * 64
                child["resources"]["total_execution_budget_seconds"] = 38 * 10
                mutate(child)
                with self.assertRaisesRegex(RuntimeError, expected):
                    checkpoint.verify_checkpoint(self.root, reference, child)

    def test_rejects_reordered_checkpoint_frontier(self):
        value = self.create()
        value["remaining_ready_groups"][0], value["remaining_ready_groups"][1] = (
            value["remaining_ready_groups"][1], value["remaining_ready_groups"][0])
        reference = self.write_checkpoint(value)
        with self.assertRaisesRegex(RuntimeError, "remaining_ready_groups"):
            checkpoint.verify_checkpoint(self.root, reference)

    def test_rejects_missing_raw_output(self):
        raw = self.fixture.work / "sources/cold-00/reports/raw/cold-00/result.json"
        raw.unlink()
        with self.assertRaisesRegex(RuntimeError, "referenced raw output is missing"):
            self.create()

    def test_rejects_missing_terminal(self):
        terminal = self.fixture.report / "attempts/cold-00/attempt-01/terminal.json"
        terminal.unlink()
        with self.assertRaisesRegex(RuntimeError, "lacks start or terminal"):
            self.create()

    def test_rejects_unsafe_raw_output_path(self):
        group = next(group for group in self.fixture.plan["groups"] if group["id"] == "cold-00")
        source = self.fixture.work / "sources/cold-00"
        report_file = source / group["reports"][0]["source_path"]
        measured = {"results": [{"case_id": group["case_ids"][0], "raw_output": "../../outside.json"}]}
        report_file.write_bytes(_json_bytes(measured))
        digest = hashlib.sha256(report_file.read_bytes()).hexdigest()
        terminal_path = self.fixture.report / "attempts/cold-00/attempt-01/terminal.json"
        terminal = json.loads(terminal_path.read_text())
        terminal["frozen_report_comparison"]["reports"][0]["measured_sha256"] = digest
        terminal["reconciliation"]["reports"][0]["sha256"] = digest
        terminal_path.write_bytes(_json_bytes(terminal))
        with self.assertRaisesRegex(RuntimeError, "raw_output path escapes its source"):
            self.create()

    def test_rejects_parent_plan_path_outside_repository(self):
        outside = self.root.parent / "not-a-plan.json"
        with self.assertRaisesRegex(RuntimeError, "parent plan must remain inside the repository"):
            checkpoint.create_checkpoint(self.root, outside, self.fixture.pause_path)

    def test_allows_declared_unreferenced_zero_sidecar_output_absence(self):
        group = next(group for group in self.fixture.plan["groups"] if group["id"] == self.fixture.completed[0])
        source = self.fixture.work / "sources" / group["id"]
        report_file = source / group["reports"][0]["source_path"]
        measured = {"results": [{"case_id": group["case_ids"][0], "raw_output": None}]}
        report_file.write_bytes(_json_bytes(measured))
        digest = hashlib.sha256(report_file.read_bytes()).hexdigest()
        attempt = self.fixture.report / "attempts" / group["id"] / "attempt-01"
        terminal = json.loads((attempt / "terminal.json").read_text())
        terminal["frozen_report_comparison"]["reports"][0]["measured_sha256"] = digest
        terminal["reconciliation"]["reports"][0]["sha256"] = digest
        terminal["reconciliation"]["reports"][0]["timing_sidecars"] = 0
        (attempt / "terminal.json").write_bytes(_json_bytes(terminal))
        raw_root = source / group["output_roots"][1]
        for path in sorted(raw_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        raw_root.rmdir()
        value = self.create()
        self.assertEqual(value["absent_output_roots"], [{
            "group": group["id"],
            "path": (source / group["output_roots"][1]).relative_to(self.root).as_posix(),
            "reason": "unreferenced-output-root-with-zero-timing-sidecars",
        }])


if __name__ == "__main__":
    unittest.main(verbosity=2)
