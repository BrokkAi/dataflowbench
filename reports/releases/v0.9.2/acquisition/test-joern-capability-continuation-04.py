#!/usr/bin/env python3
"""Focused no-analyzer tests for continuation-04's no-expiry policy."""
from __future__ import annotations

import contextlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).with_name("joern-capability-continuation-04.py")
SPEC = importlib.util.spec_from_file_location("joern_capability_continuation_04_tested", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NoExpiryAuthorizationTests(unittest.TestCase):
    def test_authority_is_exact_and_preserves_expired_clock_as_provenance(self):
        value = MODULE._check_authorization(
            MODULE.ROOT,
            {"path": MODULE.AUTHORIZATION_PATH, "sha256": MODULE.AUTHORIZATION_SHA},
        )
        window = value["execution_window"]
        self.assertEqual(value["schema"], MODULE.AUTHORIZATION_SCHEMA)
        self.assertEqual(window["mode"], "no-user-imposed-expiry")
        self.assertIsNone(window["cutoff_utc"])
        self.assertIsNone(window["total_wall_budget_seconds"])
        self.assertEqual(window["historical_cutoff_utc"], MODULE.CUTOFF.replace("+00:00", "Z"))
        self.assertEqual(window["historical_total_wall_budget_seconds"], MODULE.TOTAL_WALL_SECONDS)
        self.assertTrue(value["preserve"]["per_attempt_timeouts"])
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._check_authorization(MODULE.ROOT, {
                "path": MODULE.AUTHORIZATION_PATH, "sha256": "0" * 64,
            })

    def test_policy_rejects_reintroduced_wall_clock(self):
        policy = {
            "schema": MODULE.EXECUTION_WINDOW_SCHEMA,
            "mode": "no-user-imposed-expiry",
            "original_origin_utc": MODULE.ORIGIN,
            "historical_cutoff_utc": MODULE.CUTOFF,
            "historical_total_wall_budget_seconds": MODULE.TOTAL_WALL_SECONDS,
            "cutoff_utc": None,
            "total_wall_budget_seconds": None,
            "per_attempt_timeout_source": "registered-plan-group-deadline-seconds",
            "resource_reservation_source": "per-attempt-lease-under-exclusive-lock",
            "startup_allowance_seconds": 30,
            "startup_allowance_source": "matrix-supervision-27.GATE.stop-wait-seconds",
        }
        self.assertEqual(MODULE._execution_window(policy), policy)
        for field, value in (("cutoff_utc", MODULE.CUTOFF),
                             ("total_wall_budget_seconds", MODULE.TOTAL_WALL_SECONDS),
                             ("mode", "extended-deadline")):
            bad = dict(policy, **{field: value})
            with self.subTest(field=field), self.assertRaises(MODULE.ContinuationError):
                MODULE._execution_window(bad)


class ScopedLeaseTests(unittest.TestCase):
    def _validated(self):
        plan = {
            "resource_reservation": {
                "exclusive_analyzer_slot": True,
                "serial_analyzers": 1,
                "owner": "reviewed",
                "expires_at_unix_seconds": 1,
            },
            "groups": [{"id": MODULE.JOERN_GROUP, "deadline_seconds": 1368}],
            "total_wall_budget_seconds": None,
        }
        return {"plan": plan, "total_wall_budget_seconds": None}

    def test_lease_is_finite_per_attempt_and_keeps_plan_fields(self):
        validated = self._validated()
        before = time.time()
        runtime = MODULE._runtime_plan_with_no_expiry_lease(validated, MODULE.JOERN_GROUP)
        after = time.time()
        lease = runtime["execution_window_runtime"]
        self.assertEqual(lease["mode"], "no-user-imposed-expiry")
        self.assertGreaterEqual(lease["actual_elapsed_wall_seconds"], 0)
        self.assertEqual(lease["per_attempt_lease_seconds"], 1368 + MODULE.PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS)
        self.assertTrue(lease["actual_elapsed_wall_seconds"] < float("inf"))
        self.assertGreater(runtime["plan"]["total_wall_budget_seconds"], lease["actual_elapsed_wall_seconds"])
        expiry = runtime["plan"]["resource_reservation"]["expires_at_unix_seconds"]
        self.assertGreaterEqual(expiry, before + 1368)
        self.assertLessEqual(expiry, after + 1368 + MODULE.PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS + 1)
        self.assertEqual(validated["plan"]["total_wall_budget_seconds"], None)
        self.assertEqual(validated["plan"]["resource_reservation"]["expires_at_unix_seconds"], 1)

    def test_clock_reports_late_elapsed_time_without_reset_and_restores(self):
        class Executor:
            def _matrix_elapsed_wall(self, *_args, **_kwargs):
                return -1
        executor = Executor()
        original = executor._matrix_elapsed_wall
        validated = self._validated()
        with mock.patch.object(MODULE.time, "time", return_value=(MODULE.TOTAL_WALL_SECONDS + 10) + 0):
            # Use a late absolute timestamp relative to the old origin.
            late = MODULE._dt_origin_seconds() + MODULE.TOTAL_WALL_SECONDS + 10
            with mock.patch.object(MODULE.time, "time", return_value=late):
                with MODULE._original_clock(executor, validated):
                    elapsed = executor._matrix_elapsed_wall(validated)
                    self.assertEqual(elapsed, MODULE.TOTAL_WALL_SECONDS + 10)
        self.assertIs(executor._matrix_elapsed_wall.__func__, original.__func__)


class AppendOnlyBindingTests(unittest.TestCase):
    def test_new_paths_are_separate_from_historical_provenance(self):
        self.assertTrue(MODULE.DEFAULT_MANIFEST.endswith("continuation-manifest-05.json"))
        self.assertTrue(MODULE.DEFAULT_CONTRACT.endswith("joern-capability-repair-07-contract.json"))
        self.assertIn(MODULE.HISTORICAL_AUTHORIZATION_PATH, MODULE.HISTORICAL_CLOSURE)
        self.assertNotIn(MODULE.LEDGER, MODULE.HISTORICAL_CLOSURE)
        self.assertEqual(MODULE.JOERN_ATTEMPT, "joern-swift-common108-attempt-04-series-01")

    def test_runtime_lease_rejects_unknown_group(self):
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._runtime_plan_with_no_expiry_lease(self._minimal(), "unknown")

    @staticmethod
    def _minimal():
        return {"plan": {"resource_reservation": {}, "groups": []}}


if __name__ == "__main__":
    unittest.main()
