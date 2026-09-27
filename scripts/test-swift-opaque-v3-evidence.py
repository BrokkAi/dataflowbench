#!/usr/bin/env python3
import copy
import json
from pathlib import Path
import tempfile
import shutil
import unittest
from swift_opaque_v3_evidence import ROOT, PROFILES, bind_rows, verify_closure, sha, read
from swift_opaque_v3_provenance import verify_commands

class Evidence(unittest.TestCase):
    def rows(self, case):
        source=case['source_anchors'][0]['line_hint'];sink=case['sink_anchors'][0]['line_hint']
        positional=case['template_id'].endswith('position')
        member='select(_:_:)' if positional else ('carry(_:)' if case['polarity']=='positive' else 'block(_:)')
        return {'roles':[[source,19,p,'source'] for p in PROFILES]+[[sink,14,p,'sink'] for p in PROFILES],
                'flow':[[source,sink,14,PROFILES[1]]] if case['polarity']=='positive' else [],
                'identity':[[sink,'DataFlowBenchTaintSwift','Opaque',member,2 if positional else 1,i,
                             'Swift','String','Swift','String', i==1 if positional else member=='carry(_:)']
                            for i in range(2 if positional else 1)]}

    def cases(self):
        return [json.loads(p.read_text()) for p in sorted((ROOT/'populations/swift-opaque-v3').glob('*/case.json'))]

    def test_all_four_exact_observations(self):
        for case in self.cases():
            self.assertEqual(bind_rows(case,self.rows(case)), 'reached' if case['polarity']=='positive' else 'not-reached')

    def test_missing_or_duplicate_endpoint(self):
        case=self.cases()[0]
        for change in [lambda r:r['roles'].pop(),lambda r:r['roles'].append(r['roles'][0])]:
            rows=self.rows(case);change(rows)
            with self.assertRaisesRegex(ValueError,'endpoints'):bind_rows(case,rows)

    def test_wrong_owner_or_position(self):
        case=self.cases()[-1]
        for index,value in [(2,'Lookalike'),(5,7),(10,False)]:
            rows=self.rows(case);rows['identity'][-1][index]=value
            with self.assertRaisesRegex(ValueError,'wrapper identity'):bind_rows(case,rows)

    def test_model_off_leak_rejected(self):
        case=next(c for c in self.cases() if c['polarity']=='positive')
        rows=self.rows(case);leak=copy.deepcopy(rows['flow'][0]);leak[-1]=PROFILES[0];rows['flow'].append(leak)
        with self.assertRaisesRegex(ValueError,'model-off/on'):bind_rows(case,rows)

    def test_negative_false_positive_rejected(self):
        case=self.cases()[0];rows=self.rows(case)
        rows['flow']=[[case['source_anchors'][0]['line_hint'],case['sink_anchors'][0]['line_hint'],14,PROFILES[1]]]
        with self.assertRaisesRegex(ValueError,'model-off/on'):bind_rows(case,rows)

    def test_changed_artifact_and_missing_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').write_text('original')
            (root/'manifest.json').write_text(json.dumps({'data':sha(root/'data')}))
            verify_closure(root)
            (root/'data').write_text('changed')
            with self.assertRaisesRegex(ValueError,'digest'):verify_closure(root)
            (root/'extra').write_text('extra')
            with self.assertRaisesRegex(ValueError,'closure'):verify_closure(root)

class CommandProvenance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.attempt=Path(self.temp.name)/'attempt-01'
        shutil.copytree(ROOT/'evidence/swift-opaque-v3/attempt-01',self.attempt)
        self.plan=read(ROOT/'adapters/codeql/swift-opaque-v3/plan.json')

    def mutate(self, filename, operation):
        path=next(self.attempt.glob('*/probe/'+filename))
        value=read(path);operation(value);path.write_text(json.dumps(value))

    def test_real_retained_commands(self):
        verify_commands(ROOT,self.attempt,self.plan)

    def test_different_database_rejected(self):
        self.mutate('flow.command.json',lambda r:r['argv'].__setitem__(4,'--database=/foreign/db'))
        with self.assertRaisesRegex(ValueError,'query command'):verify_commands(ROOT,self.attempt,self.plan)

    def test_different_decoder_output_rejected(self):
        self.mutate('flow-decode.command.json',lambda r:r['argv'].__setitem__(-1,'--output=/foreign/result.json'))
        with self.assertRaisesRegex(ValueError,'decode command'):verify_commands(ROOT,self.attempt,self.plan)

    def test_expanded_query_deadline_rejected(self):
        self.mutate('flow.command.json',lambda r:r.update(deadline_seconds=120))
        with self.assertRaisesRegex(ValueError,'query deadline'):verify_commands(ROOT,self.attempt,self.plan)

    def test_changed_runner_copy_rejected(self):
        path=next(self.attempt.glob('*/probe/probe.py'));path.write_text('changed')
        with self.assertRaisesRegex(ValueError,'runner bytes'):verify_commands(ROOT,self.attempt,self.plan)

if __name__=='__main__':unittest.main(verbosity=2)
