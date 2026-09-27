#!/usr/bin/env python3
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from swift_v3_reports import ROOT,inputs,assemble,sha

class Reports(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name in ['cases','populations','adapters']:(self.root/name).symlink_to(ROOT/name,target_is_directory=True)
        pop,contract,cases,ph,ch=inputs(self.root)
        self.run={'scope':'swift-v3-contract-bound-execution','population':pop['population'],'population_sha256':ph,
                  'fixture_revision':pop['fixture_revision'],'contract_id':contract['contract_id'],'contract_sha256':ch,
                  'phases':contract['phases'],'results':[]}
        for case_id in cases:
            path=Path('reports/raw/swift-v3/test')/(case_id+'.json');target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True)
            raw={k:self.run[k] for k in ['scope','population_sha256','fixture_revision','contract_sha256']}
            raw.update(case_id=case_id,outcome='not-reached',diagnostics=['IncompleteInitialState'])
            target.write_text(json.dumps(raw))
            self.run['results'].append({'case_id':case_id,'outcome':'not-reached','raw_output':str(path),'raw_sha256':sha(target)})

    def test_all108_retained_and_no_claimed_qualification(self):
        self.run['qualified']=True
        report=assemble(self.root,self.run)
        self.assertEqual(len(report['results']),108)
        self.assertTrue(all(r['outcome']=='inconclusive' and 'IncompleteInitialState' in r['diagnostics'] for r in report['results']))
        self.assertFalse(report['scored_activation'])

    def test_missing_foreign_duplicate_rejected(self):
        for operation in [lambda r:r['results'].pop(),lambda r:r['results'][0].update(case_id='foreign'),lambda r:r['results'].__setitem__(0,r['results'][1])]:
            run=copy.deepcopy(self.run);operation(run)
            with self.assertRaisesRegex(ValueError,'membership'):assemble(self.root,run)

    def test_mismatched_contract_population_revision_rejected(self):
        for key in ['contract_sha256','population_sha256','fixture_revision']:
            run=copy.deepcopy(self.run);run[key]='wrong'
            with self.assertRaisesRegex(ValueError,'binding'):assemble(self.root,run)

    def test_old_diagnostics_not_promoted(self):
        self.run['scope']='native-composed-retained-database-diagnostic'
        with self.assertRaisesRegex(ValueError,'new execution'):assemble(self.root,self.run)

    def test_historical_raw_path_rejected(self):
        self.run['results'][0]['raw_output']='evidence/swift-native-composed-v1/attempt-01/flow.json'
        with self.assertRaisesRegex(ValueError,'new raw'):assemble(self.root,self.run)

    def test_raw_hash_and_binding_rejected(self):
        row=self.run['results'][0];path=self.root/row['raw_output'];raw=json.loads(path.read_text());raw['contract_sha256']='old'
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError,'digest'):assemble(self.root,self.run)
        row['raw_sha256']=sha(path)
        with self.assertRaisesRegex(ValueError,'raw execution binding'):assemble(self.root,self.run)

    def test_budget_drift_rejected(self):
        self.run['phases']=copy.deepcopy(self.run['phases']);self.run['phases']['analysis']['peak_memory_mb']=512
        with self.assertRaisesRegex(ValueError,'phase budgets'):assemble(self.root,self.run)

if __name__=='__main__':unittest.main(verbosity=2)
