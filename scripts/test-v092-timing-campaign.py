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


if __name__ == "__main__":
    unittest.main()
