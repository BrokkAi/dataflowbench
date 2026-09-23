#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-swift-resolved-conversion.py'))
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)

class ConversionControls(unittest.TestCase):
    def setUp(self):
        base=verify.BASE/'conversion-attempt-03'
        self.rows={n:verify.read(base/(n+'.json'))['#select']['tuples'] for n in ['roles','flow','summary-identity','summary-ports','summary-transfer','summary-store']}

    def test_retained(self):
        verify.verify()

    def test_local_summary_rejected(self):
        self.rows['summary-identity'][-1][-1]=True
        with self.assertRaisesRegex(ValueError,'summary applicability'):verify.check_rows(self.rows)

    def test_missing_real_flow_rejected(self):
        self.rows['flow']=[]
        with self.assertRaisesRegex(ValueError,'endpoint separation'):verify.check_rows(self.rows)

    def test_local_false_flow_rejected(self):
        self.rows['flow'].append([12,27,87,'adapter-patched-conversion'])
        with self.assertRaisesRegex(ValueError,'endpoint separation'):verify.check_rows(self.rows)

    def test_defining_module_not_owner_identity(self):
        self.rows['summary-identity'][-1][2]='Foundation'
        with self.assertRaisesRegex(ValueError,'declaration provenance'):verify.check_rows(self.rows)

    def test_missing_optional_content_rejected(self):
        self.rows['summary-store'][-1][-1]='CollectionElement'
        with self.assertRaisesRegex(ValueError,'content stores'):verify.check_rows(self.rows)

    def test_vendor_relabel_rejected(self):
        self.rows['roles'][0][2]='vendor-native'
        with self.assertRaisesRegex(ValueError,'profile attribution'):verify.check_rows(self.rows)

if __name__=='__main__':unittest.main(verbosity=2)
