#!/usr/bin/env python3
"""Preparation must stay non-executable while preserving historical coverage."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock
from release_plan import require_executable_plan

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prep',ROOT/'scripts/prepare-swift-release-220.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)


class PreparationTests(unittest.TestCase):
    def test_pending_choice_cannot_execute(self):
        plan=prep.build()['execution-plan.json']
        path=prep.BASE/'execution-plan.json'
        with self.assertRaisesRegex(ValueError,'blocked'):
            require_executable_plan(path,plan)
        plan['status']='executable'
        with self.assertRaisesRegex(ValueError,'fixture_revision'):
            require_executable_plan(path,plan)

    def test_every_existing_lane_requires_fresh_evidence(self):
        plan=prep.build()['execution-plan.json']
        self.assertEqual(len(plan['reports']),92)
        self.assertEqual(sum(r['case_count'] for r in plan['reports']),4244)
        self.assertEqual(len(plan['historical_revision_groups']),3)
        self.assertTrue(all(r['requires_fresh_run'] and r['executable_argv'] is None for r in plan['reports']))
        self.assertFalse(plan['scope_decision']['exclusion_selected'])
        self.assertFalse(plan['scope_decision']['deferral_selected'])

    def test_no_opaque_identity_is_lost_or_reported_complete(self):
        coverage=prep.build()['coverage-v2.json']
        self.assertFalse(coverage['epic_complete'])
        pending={f['template_id'] for f in coverage['families'] if f['scope_resolution']=='pending-user-choice'}
        self.assertEqual(pending,set(prep.OPAQUE))
        self.assertEqual(sum(f['scope_resolution']=='A38/A39-inputs-A40-typed-coverage-complete' for f in coverage['families']),7)
        self.assertEqual(len(coverage['families']),58)

    def test_missing_result_coverage_fails(self):
        original=prep.read
        def altered(path):
            value=original(path)
            if path=='reports/joern-swift-v2-result.json':value['results']=[]
            return value
        with mock.patch.object(prep,'read',side_effect=altered),self.assertRaises(StopIteration):prep.build()


if __name__=='__main__':unittest.main()
