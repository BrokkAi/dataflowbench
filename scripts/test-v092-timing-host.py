#!/usr/bin/env python3
"""Focused tests for the fail-closed v0.9.2 timing host observer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("v092_timing_host.py")
SPEC = importlib.util.spec_from_file_location("v092_timing_host", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
host = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(host)


def observation(monotonic: float, *, idle: float = 95.0, processes=None) -> dict:
    return {
        "schema_version": 1,
        "status": "ok",
        "observed_at_utc": "2026-11-10T00:00:00.000Z",
        "monotonic_seconds": monotonic,
        "cpu_idle_percent": idle,
        "processes": processes if processes is not None else [
            {"pid": 1, "ppid": 0, "cpu_percent": 0.0, "comm": "launchd"},
        ],
        "uptime": "up 2 days, 3 users, load averages: 1.00 1.25 1.50",
        "load_average": [1.0, 1.25, 1.5],
        "disk_total_bytes": 1000,
        "disk_used_bytes": 400,
        "disk_free_bytes": 600,
        "hardware": {
            "model": "MacTest,1",
            "logical_cpus": 8,
            "physical_cpus": 4,
            "memory_bytes": 16000000000,
        },
    }


class HostObserverTests(unittest.TestCase):
    def test_top_parser_uses_last_cpu_idle_record(self):
        output = """Processes: 300 total
CPU usage: 1.0% user, 0.0% sys, 99.0% idle
CPU usage: 7.0% user, 4.0% sys, 89.0% idle
"""
        self.assertEqual(host.parse_top_idle(output), 89.0)

    def test_top_parser_fails_when_last_record_is_unreadable(self):
        output = "CPU usage: 1.0% user, 0.0% sys, 99.0% idle\nCPU usage: unavailable"
        with self.assertRaises(host.HostObservationError):
            host.parse_top_idle(output)

    def test_quiet_classification_includes_exact_idle_boundary(self):
        self.assertTrue(host.classify(observation(10.0, idle=90.0)))
        self.assertFalse(host.classify(observation(10.0, idle=89.999)))

    def test_missing_required_state_fails_closed(self):
        missing = observation(0.0)
        del missing["hardware"]
        self.assertFalse(host.classify(missing))
        window = host.QuietWindow(required_seconds=2, max_gap_seconds=1)
        self.assertFalse(window.observe(observation(0.0)))
        self.assertFalse(window.observe(missing))
        self.assertEqual(window.elapsed_seconds, 0.0)

    def test_competing_heavy_process_blocks_quiet_except_allowed_descendant(self):
        rows = [
            {"pid": 100, "ppid": 1, "cpu_percent": 0.0, "comm": "python3"},
            {"pid": 101, "ppid": 100, "cpu_percent": 0.0, "comm": "/usr/bin/rustc"},
        ]
        sample = observation(1.0, processes=rows)
        self.assertFalse(host.classify(sample))
        self.assertTrue(host.classify(sample, allowed_pids=[100]))

    def test_engine_harness_and_versioned_infer_compiler_are_heavy(self):
        for pid, comm in enumerate(("bifrost", "dataflowbench", "/opt/infer/bin/clang-21"), start=200):
            with self.subTest(comm=comm):
                sample = observation(1.0, processes=[
                    {"pid": 1, "ppid": 0, "cpu_percent": 0.0, "comm": "launchd"},
                    {"pid": pid, "ppid": 1, "cpu_percent": 0.0, "comm": comm},
                ])
                self.assertFalse(host.classify(sample))

        near_miss = observation(1.0, processes=[
            {"pid": 1, "ppid": 0, "cpu_percent": 0.0, "comm": "launchd"},
            {"pid": 210, "ppid": 1, "cpu_percent": 0.0, "comm": "clang-21-wrapper"},
        ])
        self.assertTrue(host.classify(near_miss))

    def test_quiet_window_needs_300_monotonic_seconds_and_resets_on_gap(self):
        window = host.QuietWindow()
        for second in range(0, 300, 60):
            self.assertFalse(window.observe(observation(float(second))))
        self.assertTrue(window.observe(observation(300.0)))
        self.assertEqual(window.elapsed_seconds, 300.0)

        reset = host.QuietWindow()
        reset.observe(observation(0.0))
        reset.observe(observation(60.0))
        self.assertFalse(reset.observe(observation(121.0)))
        self.assertEqual(reset.elapsed_seconds, 0.0)
        self.assertFalse(reset.observe(observation(181.0)))
        self.assertFalse(reset.observe(observation(241.0)))
        self.assertFalse(reset.observe(observation(301.0)))
        self.assertFalse(reset.qualified)

    def test_nonquiet_sample_resets_window(self):
        window = host.QuietWindow(required_seconds=120, max_gap_seconds=60)
        window.observe(observation(0.0))
        window.observe(observation(60.0))
        self.assertFalse(window.observe(observation(90.0, idle=80.0)))
        self.assertEqual(window.elapsed_seconds, 0.0)
        self.assertFalse(window.observe(observation(150.0)))

    def test_evidence_append_preserves_prior_records_and_failure_is_nonquiet(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "host.jsonl"
            host.append_evidence(path, observation(1.0))
            failed = host.failure_record(RuntimeError("sample unavailable"))
            self.assertFalse(failed["quiet"])
            host.append_evidence(path, failed)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["status"], "failed")
            self.assertIn("observed_at_utc", rows[1])
            self.assertIn("monotonic_seconds", rows[1])


if __name__ == "__main__":
    unittest.main()
