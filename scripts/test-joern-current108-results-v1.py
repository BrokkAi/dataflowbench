#!/usr/bin/env python3
"""Portable full-population export tampering tests; no analyzer invocation."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from swift_normal_reports_v1 import ROOT,read
spec=importlib.util.spec_from_file_location('current108_replay',Path(__file__).with_name('check-joern-current108-results-v1.py'))
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)

class Results(unittest.TestCase):
    def test_complete_truthful_diagnostic_export(self):
        self.assertEqual(replay.verify()['normalized_outcomes'],{'inconclusive':96,'unsupported':12})

    def test_missing_row_cannot_be_filled_by_capability_decision(self):
        run_path=ROOT/replay.RUN/'run.json';original=replay.read
        def altered(path):
            value=original(path)
            if path==run_path:value['results']=value['results'][:-1]
            return value
        with patch.object(replay,'read',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'membership'):replay.verify()

    def test_exported_report_cannot_promote_inconclusive_to_clean(self):
        original=replay.read
        def altered(path):
            value=original(path)
            if path.name=='report-0.json':value['results'][0]['outcome']='not-reached'
            return value
        with patch.object(replay,'read',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'normal report drift'):replay.verify()

    def test_native_configuration_hash_tamper_rejects(self):
        import joern_normal_reports_v1 as reports
        original=reports.read
        def altered(path):
            value=original(path)
            if path.name=='raw.json' and value.get('executed'):
                value['native_outputs']=copy.deepcopy(value['native_outputs'])
                for reference in value['native_outputs']:
                    if reference['path'].endswith('/config.json'):reference['sha256']='0'*64
            return value
        with patch.object(reports,'read',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'digest'):replay.verify()

if __name__=='__main__':unittest.main()
