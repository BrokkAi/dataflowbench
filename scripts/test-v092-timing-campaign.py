#!/usr/bin/env python3
"""Focused regressions for measurement isolation and report reconciliation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


campaign = load("campaign_under_test", "v092_timing_campaign.py")
host = load("host_under_test", "v092_timing_host.py")


class CampaignTests(unittest.TestCase):
    def make_guard(self, directory):
        observer = Mock()
        ownership = {"root_pid": 100}
        return campaign.ObservedGuard(host, observer, ownership, Path(directory) / "host.jsonl", Path(directory))

    def observation(self):
        return {"hardware": {"logical_cpus": 10}, "processes": [
            {"pid": 1, "ppid": 0, "comm": "/sbin/launchd", "cpu_percent": 1.0},
            {"pid": 100, "ppid": 1, "comm": "/tmp/dataflowbench", "cpu_percent": 2.0},
            {"pid": 101, "ppid": 100, "comm": "/tmp/bifrost", "cpu_percent": 700.0},
        ]}

    def test_owned_analysis_does_not_count_as_external_contention(self):
        result = campaign.external_contention(self.observation(), 100, host)
        self.assertFalse(result["contended"])
        self.assertEqual(result["external_cpu_percent"], 1.0)

    def test_unrelated_compiler_stops_even_when_idle(self):
        observation = self.observation()
        observation["processes"].append(
            {"pid": 200, "ppid": 1, "comm": "/tmp/clang-21", "cpu_percent": 0.0})
        self.assertTrue(campaign.external_contention(observation, 100, host)["contended"])

    def test_significant_unrelated_cpu_boundary(self):
        observation = self.observation()
        observation["processes"][0]["cpu_percent"] = 100.0
        self.assertTrue(campaign.external_contention(observation, 100, host)["contended"])
        observation["processes"][0]["cpu_percent"] = 99.9
        self.assertFalse(campaign.external_contention(observation, 100, host)["contended"])

    def test_reconcile_reads_original_source_path_and_rejects_missing_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/test.json"
            path.parent.mkdir()
            path.write_text(json.dumps({"tool_version": "v1", "results": [{"case_id": "positive"}]}))
            raw = root / "reports/raw/bifrost"
            raw.mkdir(parents=True)
            (raw / "positive-timing.json").write_text("{}")
            group = {"kind": "cold", "output_roots": ["reports/test.json", "reports/raw/bifrost"],
                     "reports": [{"path": "never-read/frozen.json",
                "source_path": "reports/test.json", "tool_version": "v1", "case_ids": ["positive"]}]}
            result = campaign.reconcile(group, root)
            self.assertFalse(result["publication_eligible"])
            self.assertEqual(result["reports"][0]["timing_sidecars"], 1)
            group["reports"][0]["case_ids"].append("negative")
            with self.assertRaisesRegex(RuntimeError, "population differs"):
                campaign.reconcile(group, root)

    def test_idle_service_needs_stable_identity_and_cpu_and_no_descendants(self):
        observer = campaign.Observer.__new__(campaign.Observer)
        observer.host = Mock()
        observer.tracker = Mock()
        observer.tracker._start_identity.return_value = "123:456"
        observer.previous = {}
        service = {"pid": 50, "ppid": 1, "comm": "/tmp/bifrost", "cpu_percent": 0.0}
        observer.host.snapshot.side_effect = lambda *_: {"processes": [dict(service)]}
        with patch.object(campaign.subprocess, "check_output", return_value="50 0:00.01 /tmp/bifrost --mcp symbol|extended\n"):
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [])
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [50])
        with patch.object(campaign.subprocess, "check_output", return_value="50 0:00.02 /tmp/bifrost --mcp symbol|extended\n"):
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [])
            observer.tracker._start_identity.return_value = "999:000"
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [])
            observer.host.snapshot.side_effect = lambda *_: {"processes": [dict(service),
                {"pid": 51, "ppid": 50, "comm": "/tmp/helper", "cpu_percent": 0.0}]}
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [])

    def test_missing_or_malformed_service_counter_never_certifies_inactivity(self):
        observer = campaign.Observer.__new__(campaign.Observer)
        observer.host = Mock()
        observer.tracker = Mock()
        observer.previous = {}
        observer.host.snapshot.return_value = {"processes": [
            {"pid": 50, "ppid": 1, "comm": "/tmp/bifrost", "cpu_percent": 0.0}]}
        with patch.object(campaign.subprocess, "check_output", return_value=""):
            self.assertEqual(observer.snapshot()["quiescent_service_pids"], [])
        with patch.object(campaign.subprocess, "check_output", return_value="50 unknown /tmp/bifrost --mcp symbol|extended\n"):
            with self.assertRaisesRegex(ValueError, "CPU time"):
                observer.snapshot()

    def test_active_cpu_contention_records_without_aborting(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = self.make_guard(directory)
            guard.guard = Mock()
            observation = self.observation()
            observation["processes"][0]["cpu_percent"] = 550.0
            guard.observer.snapshot.return_value = observation
            with patch.object(campaign.core, "_tree_bytes", return_value=0), \
                    patch.object(campaign.time, "monotonic", return_value=100.0):
                guard.check(category="working", paths=[])
            self.assertTrue(guard.contention_observed)
            self.assertEqual(guard.active_observations, 1)
            self.assertFalse(guard.quiet_certification()["certified"])
            self.assertTrue(json.loads(guard.evidence.read_text())["contention"]["contended"])

    def test_active_and_post_observation_failures_are_nonfatal(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = self.make_guard(directory)
            guard.guard = Mock()
            guard.observer.snapshot.side_effect = host.HostObservationError("unavailable CPU")
            with patch.object(campaign.core, "_tree_bytes", return_value=0), \
                    patch.object(campaign.time, "monotonic", return_value=100.0):
                guard.check(category="working", paths=[])
            result = guard.observe_background("after-analysis")
            self.assertFalse(result["observation_available"])
            self.assertEqual(guard.observation_failures, 2)
            self.assertFalse(guard.quiet_certification()["certified"])

    def test_resource_failures_still_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = self.make_guard(directory)
            guard.guard = Mock()
            guard.guard.check.side_effect = RuntimeError("disk reserve lost")
            with self.assertRaisesRegex(RuntimeError, "disk reserve"):
                guard.check(category="working", paths=[])
            guard.observer.snapshot.assert_not_called()
            guard.guard.check.side_effect = None
            with patch.object(campaign.core, "_tree_bytes", return_value=12 * campaign.GIB + 1):
                with self.assertRaisesRegex(campaign.CampaignStop, "12 GiB"):
                    guard.check(category="working", paths=[])

    def test_only_first_dispatch_waits_for_quiet(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = self.make_guard(directory)
            guard.launch_check = Mock()
            guard.observe_background = Mock(return_value={"contention_observed": True})
            with patch.object(campaign, "wait_quiet", return_value={"cpu_idle_percent": 95}) as wait:
                first = campaign.prelaunch_state(0, host, guard.observer, guard, guard.evidence, guard.source)
                self.assertIsNotNone(first["quiet_observation"])
                self.assertTrue(guard.initial_quiet_gate_passed)
                wait.assert_called_once()
                later = campaign.prelaunch_state(1, host, guard.observer, guard, guard.evidence, guard.source)
                self.assertIsNone(later["quiet_observation"])
                self.assertTrue(guard.settle_skipped)
                wait.assert_called_once()
                self.assertEqual(guard.launch_check.call_count, 2)
                guard.observe_background.assert_called_once_with("prelaunch-after-campaign-start")

    def test_campaign_ids_are_dated_and_cannot_escape_workspace(self):
        report, work = campaign.campaign_paths("20261111-01")
        self.assertEqual(report.name, "20261111-01")
        self.assertEqual(work.name, "timing-v092-20261111-01")
        for value in ["../20261111-01", "/tmp/20261111-01", "20260230-01", "20261111-00"]:
            with self.assertRaises(ValueError, msg=value):
                campaign.campaign_paths(value)

    def test_overhead_pairing_rejects_php_before_dispatch(self):
        group = {"kind": "overhead", "family": "bifrost", "argv": [
            "runner", "estimate-invocation-overhead", "--tool", "bifrost", "--language", "python"]}
        campaign.validate_overhead_group(group)
        group["argv"][-1] = "php"
        with self.assertRaisesRegex(RuntimeError, "unregistered overhead"):
            campaign.validate_overhead_group(group)

    def test_auxiliary_continuation_preserves_budget_and_rejects_real_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "reports/timing/v0.9.2/20261113-01"
            current = root / "reports/timing/v0.9.2/20261113-02"
            def put(path, value):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value))
            cold = {"id": "cold", "kind": "cold", "status": "ready"}
            bad = {"id": "overhead-bifrost-php", "kind": "overhead", "status": "ready",
                   "family": "bifrost", "deadline_seconds": 600, "argv": [
                       "runner", "--tool", "bifrost", "--language", "php"],
                   "output_roots": ["reports/raw/invocation-overhead/bifrost-php"]}
            infer = {**bad, "id": "overhead-infer-c", "family": "infer", "argv": [
                "runner", "--tool", "infer", "--language", "c"],
                "output_roots": ["reports/raw/invocation-overhead/infer-c"]}
            original = {"release_commit": "release", "population": "population",
                        "fixture_revision": "fixture", "tools": {}, "source_projection": {},
                        "resources": {"total_execution_budget_seconds": 2000},
                        "groups": [cold, bad, infer]}
            put(parent / "plan.json", original)
            put(parent / "campaign-terminal.json", {"status": "stopped", "group": bad["id"]})
            failed_path = parent / "attempts" / bad["id"] / "attempt-01/terminal.json"
            failed = {"exit_code": 1, "timed_out": False, "capacity_loss": None, "elapsed_seconds": 2}
            put(failed_path, failed)
            failed_path.with_name("stderr.txt").write_text("Error: no Bifrost overhead arm for php\n")
            put(parent / "attempts/cold/attempt-01/terminal.json", {
                "status": "completed-candidate-evidence", "elapsed_seconds": 1})
            first = parent / "attempts/cold/attempt-01/start.json"
            put(first, {"plan_sha256": campaign.sha(parent / "plan.json"),
                        "quiet_observation": {"quiet_elapsed_seconds": 315, "cpu_idle_percent": 95}})
            corrected = {**bad, "id": "overhead-bifrost-python", "argv": [
                "runner", "--tool", "bifrost", "--language", "python"],
                "output_roots": ["reports/raw/invocation-overhead/bifrost-python"]}
            plan = {**original, "groups": [corrected, infer], "continuation": {
                "kind": "pre-analysis-overhead-language-correction", "parent_campaign_id": "20261113-01",
                "parent_plan_sha256": campaign.sha(parent / "plan.json"),
                "parent_terminal_sha256": campaign.sha(parent / "campaign-terminal.json"),
                "initial_dispatch_sha256": campaign.sha(first)}}
            with patch.object(campaign, "ROOT", root), patch.object(campaign, "REPORT", current):
                consumed, evidence = campaign.admit_auxiliary_continuation(plan)
                self.assertEqual(consumed, 3)
                self.assertTrue(evidence["cold_groups_not_repeated"])
                put(failed_path, {**failed, "timed_out": True})
                with self.assertRaisesRegex(RuntimeError, "pre-analysis configuration"):
                    campaign.admit_auxiliary_continuation(plan)
                put(failed_path, failed)
                plan["resources"] = {"total_execution_budget_seconds": 3000}
                with self.assertRaisesRegex(RuntimeError, "changed invariant"):
                    campaign.admit_auxiliary_continuation(plan)


if __name__ == "__main__":
    unittest.main()
