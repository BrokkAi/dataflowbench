#!/usr/bin/env python3
"""Joern-specific report provenance mutations, no analyzer execution."""
import copy
import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from joern_normal_reports_v1 import export, validate_phases, phase_sequence
from swift_normal_reports_v1 import ROOT, read, sha
spec=importlib.util.spec_from_file_location('normal_test_fixtures',ROOT/'scripts/test-swift-normal-reports-v1.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
write=fixtures.write


class Reports(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.path,self.plan,self.run=fixtures.sample(self.root)
        tool={'tool':'joern','tool_version':'4.0.628','tool_build_identity':'joern-cli:4.0.628;engine:synthetic','adapter_version':'joern-normal-v1'}
        self.plan.update(schema='joern-normal-report-plan/v1',identity=tool,runtime={'joern':'/pinned/joern'},partition_status='resolved')
        contract={'schema':'joern-normal-contract/v1','population_sha256':self.plan['population_sha256'],'fixture_revision':self.plan['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,'total_wall_clock_seconds':75,'phase_sequence':[{'id':name,'role':'analysis'} for name in ['typecheck','frontend','query']],'memory_policy':{'fixture_peak_memory_mb':512,'aggregate_enforcement':'unavailable','jvm_heap_request_mb':512}}
        self.plan['execution_contract']=write(self.root,'adapters/test-normal/contract.json',contract)
        self.plan['activation_receipt']=write(self.root,'activation.json',{'synthetic':True})
        self.run['activation_receipt']=self.plan['activation_receipt']
        # Native control replay is covered separately; exercise export bindings.
        replay=patch('joern_normal_runner_v1.verify_activation');self.replay=replay.start();self.addCleanup(replay.stop)
        planref=write(self.root,self.path,self.plan)
        witness=read(self.root/self.run['identity_witness']['path']);witness['observed']=tool;witness['command']['argv']=['/pinned/joern']
        stdout=self.root/witness['stdout']['path'];stdout.write_text('Joern 4.0.628\n');witness['stdout']['sha256']=sha(stdout)
        self.run['identity_witness']=write(self.root,self.run['identity_witness']['path'],witness)
        self.run.update(schema='joern-normal-report-run/v1',identity=tool,plan_sha256=planref['sha256'])
        phases=[dict(witness['command'],phase_id=p['id'],role='analysis',deadline_seconds=25,elapsed_seconds=0.001) for p in contract['phase_sequence']]
        commands=[write(self.root,'reports/raw/phase-'+str(i)+'.json',phase) for i,phase in enumerate(phases)]
        for row in self.run['results']:
            raw=read(self.root/row['raw']['path']);raw.update(activation_receipt=self.plan['activation_receipt'],schema='joern-normal-raw/v1',plan_sha256=planref['sha256'],identity_witness_sha256=self.run['identity_witness']['sha256'],execution_contract_sha256=self.plan['execution_contract']['sha256'],commands=commands,total_elapsed_seconds=0.004)
            raw.pop('analysis_elapsed_seconds')
            row['raw']=write(self.root,row['raw']['path'],raw)

    def test_full108_and_no_score_promotion(self):
        bundle=export(self.root,self.path,self.run)
        self.assertEqual(len(bundle['audit']['results']),108)
        self.replay.assert_called_once()
        self.assertFalse(bundle['audit']['scored_activation'])
        self.assertEqual({r['outcome'] for report in bundle['reports'].values() for r in report['results']},{'inconclusive'})

    def test_wrong_tool_old_run_partial_or_unresolved_reject(self):
        for field,value in [('schema','swift-normal-report-run/v1'),('results',self.run['results'][:-1]),('identity',dict(self.run['identity'],tool='codeql'))]:
            run=copy.deepcopy(self.run);run[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):export(self.root,self.path,run)
        self.plan['partition_status']='unresolved';self.run['plan_sha256']=write(self.root,self.path,self.plan)['sha256']
        with self.assertRaisesRegex(ValueError,'unresolved'):export(self.root,self.path,self.run)

    def test_activation_run_and_raw_binding(self):
        self.run['activation_receipt']={'path':'foreign.json','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'activation receipt'):export(self.root,self.path,self.run)
        self.run['activation_receipt']=self.plan['activation_receipt']
        row=self.run['results'][0];raw=read(self.root/row['raw']['path']);raw.pop('activation_receipt');row['raw']=write(self.root,row['raw']['path'],raw)
        with self.assertRaisesRegex(ValueError,'raw activation'):export(self.root,self.path,self.run)

    def test_real_total_budget_and_failed_prefix_rules(self):
        seq=phase_sequence({'phase_sequence':[{'id':n,'role':'analysis'} for n in ['typecheck','frontend','query']]})
        refs=[]
        for i,p in enumerate(seq):
            refs.append(write(self.root,'phase'+str(i)+'.json',dict(p,phase_id=p['id'],argv=['fake'],exit_status=0,timed_out=False,cleanup_status='tracked-processes-stopped',elapsed_seconds=25,deadline_seconds=75-25*i)))
        raw={'commands':refs,'total_elapsed_seconds':75}
        validate_phases(self.root,raw,seq,'inconclusive',[])
        record=read(self.root/refs[2]['path']);record['deadline_seconds']=26;refs[2]=write(self.root,refs[2]['path'],record)
        with self.assertRaisesRegex(ValueError,'deadline'):validate_phases(self.root,raw,seq,'inconclusive',[])
        record=read(self.root/refs[0]['path']);record['exit_status']=1;refs[0]=write(self.root,refs[0]['path'],record)
        validate_phases(self.root,{'commands':refs[:1],'total_elapsed_seconds':25},seq,'runner-error',[])
        with self.assertRaisesRegex(ValueError,'after failed'):validate_phases(self.root,raw,seq,'runner-error',[])
        with self.assertRaises(ValueError):phase_sequence({'phase_sequence':[{'id':'extract','role':'extraction'},{'id':'query','role':'analysis'}]})

    def test_version_command_and_native_output_digest_bound(self):
        witness_path=self.root/self.run['identity_witness']['path'];witness=read(witness_path);witness['command']['argv']=['codeql','version']
        self.run['identity_witness']=write(self.root,str(witness_path.relative_to(self.root)),witness)
        with self.assertRaisesRegex(ValueError,'identity command'):export(self.root,self.path,self.run)
        witness['command']['argv']=['/pinned/joern'];self.run['identity_witness']=write(self.root,str(witness_path.relative_to(self.root)),witness)
        row=self.run['results'][0];raw=read(self.root/row['raw']['path']);(self.root/raw['native_outputs'][0]['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError,'digest'):export(self.root,self.path,self.run)


if __name__=='__main__':unittest.main()
