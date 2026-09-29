#!/usr/bin/env python3
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

fixture=load('attempt_fixture','test-release-attempt-v090.py')
verifier=load('verifier','verify-release-attempt-v090.py')

class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.ReleaseAttemptTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown);f=self.fixture
        plan=json.loads((f.root/fixture.RECORDER.PLAN_PATH).read_text())
        for r in plan['reports']:
            ids=r['case_ids'];r['case_membership']={'count':len(ids),'sha256':hashlib.sha256((json.dumps(ids,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()}
        raw=f.json_bytes(plan);f._write(fixture.RECORDER.PLAN_PATH,raw);f.contract['parent_plan']['sha256']=f.sha(raw);f.contract['groups'][0]['tool']='fake';f._write(fixture.CONTRACT_PATH,f.json_bytes(f.contract));self.row=f.run_group();self.receipt=Path(fixture.RECORDER.ATTEMPTS_PATH)/self.row['attempt_id']/'completed.json'

    def check(self):return verifier.verify_attempt(self.fixture.root,self.receipt,fixture.CONTRACT_PATH)
    def test_real_recorder_shape(self):self.assertEqual(self.check()['status'],'completed')
    def test_raw_tamper_rejected(self):
        p=self.fixture.root/fixture.RECORDER.ATTEMPTS_PATH/self.row['attempt_id']/'capture'/self.fixture.output/'raw/case-a/execution.json';p.write_text('{}')
        with self.assertRaises(verifier.VerificationError):self.check()
    def test_extra_capture_rejected(self):
        p=self.fixture.root/fixture.RECORDER.ATTEMPTS_PATH/self.row['attempt_id']/'capture'/'extra';p.write_text('extra')
        with self.assertRaises(verifier.VerificationError):self.check()
    def test_outcome_mutation_rejected(self):
        p=self.fixture.root/self.row['reports'][0]['staged_path'];value=json.loads(p.read_text());value['results'][0]['outcome']='not-reached';p.write_text(json.dumps(value))
        with self.assertRaises(verifier.VerificationError):self.check()
    def test_failed_receipt_rejected(self):
        p=self.fixture.root/self.receipt;value=json.loads(p.read_text());value['status']='failed';p.write_text(json.dumps(value))
        with self.assertRaises(verifier.VerificationError):self.check()

if __name__=='__main__':unittest.main()
