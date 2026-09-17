#!/usr/bin/env python3
"""Focused fail-closed tests for release plan selection."""

import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock


SCRIPT_DIR = pathlib.Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("release_plan", SCRIPT_DIR / "release_plan.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleasePlanTests(unittest.TestCase):
    def test_v071_remains_executable(self):
        _base, path, plan = MODULE.load_plan("v0.7.1")
        MODULE.require_executable_plan(path, plan)
        steps = MODULE.command_steps(path.parent, plan, "reports")
        MODULE.require_executable_steps(steps)
        self.assertEqual(len(steps), 66)

    def test_v080_resolved_plan_is_executable(self):
        base, path, plan = MODULE.load_plan("v0.8.0")
        steps = MODULE.command_steps(base, plan, "reports")
        self.assertTrue(MODULE.display_argv(steps[0]))
        MODULE.require_executable_plan(path, plan)
        MODULE.require_executable_steps(steps)
        self.assertEqual(len(steps), 66)

    def test_any_non_executable_status_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "integration-blocked"):
            MODULE.require_executable_plan(
                MODULE.ROOT / "reports/releases/v0.8.0/rerun-plan.json",
                {"status": "integration-blocked"},
            )

    def test_invalid_release_cannot_escape_release_root(self):
        with self.assertRaisesRegex(ValueError, "invalid release"):
            MODULE.release_base("../../tmp")

    def test_finalized_plan_still_requires_exact_argv_and_membership(self):
        step = {
            "id": "pending",
            "command_template": ["dataflowbench", "run"],
            "case_membership": "pending",
        }
        with self.assertRaisesRegex(ValueError, "pending"):
            MODULE.require_executable_steps([step])

    def test_command_template_is_for_listing_only(self):
        step = {"id": "template-only", "command_template": ["dataflowbench", "run"]}
        self.assertEqual(MODULE.display_argv(step), ["dataflowbench", "run"])
        with self.assertRaisesRegex(ValueError, "template-only"):
            MODULE.require_executable_steps([step])

    def test_report_step_requires_digest_bound_case_ids(self):
        step = {
            "id": "report-without-membership",
            "report": "reports/example.json",
            "argv": ["dataflowbench", "run"],
            "case_membership": {"count": 1, "sha256": "0" * 64},
        }
        with self.assertRaisesRegex(ValueError, "report-without-membership"):
            MODULE.require_executable_steps([step])


if __name__ == "__main__":
    unittest.main()
