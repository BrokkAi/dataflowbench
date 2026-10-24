#!/usr/bin/env python3
"""Synthetic breadth-first actual-history/terminal accounting regressions.

Real successor protocol/bridge methods, temporary byte-bound receipts and
actual frozen plan partition definitions. No production replay or analyzer.
"""
from __future__ import annotations
import contextlib
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
p=load('breadth11_protocol',BASE/'bifrost-v0140-replacement-12.py')
b=load('breadth11_bridge',BASE/'bifrost-v0140-frozen-bridge-07.py')
s=load('breadth11_supervisor',BASE/'bifrost-v0140-supervisor-12.py')
PLAN=json.loads((ROOT/'reports/releases/v0.9.2/execution-v4/contract.json').read_bytes())

def row(group='bifrost-c-kernel',status='completed'):
    code=0 if status=='completed' else 124 if status=='timed-out' else 1
    return {'group_id':group,'attempt_id':p._attempt_id(group), 'tool':'bifrost',
            'status':status,'exit_code':code,'timed_out':status=='timed-out','capacity_loss':None,
            'source_commit':'a'*40,'plan_commit':'b'*40,'contract_sha256':'c'*64,'execution_series':2,
            'end_utc':'2026-10-24T12:00:00+00:00',
            'process_ownership':{'schema':'invocation-process-ownership/v1','descendant_containment':'unproven','tracking_interval_seconds':2.0,'root_pid':123,'cleanup_status':'tracked-processes-stopped',
                                 'tracked_processes':[{'pid':123,'start_identity':'exact-birth'}]}}
def terminal(value):
    return p._terminal_identity(value,group_id=value['group_id'],attempt_id=value['attempt_id'],
             source_commit='a'*40,plan_commit='b'*40,contract_sha256='c'*64,execution_series=2,label='test')

class IncomingSealTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.oldsha=p.ORIGINAL_PREFIX_SHA256;self.old87=p.PREDECESSOR87_SHA256
        self.original=[{'attempt_id':f'historical-{i}','status':'completed'} for i in range(87)]
        self.original.append({'attempt_id':'joern-swift-common108-attempt-04-series-01','status':'failed'})
        raw=b''.join(p.canonical_json(x) for x in self.original)
        p.ORIGINAL_PREFIX_SHA256=p.sha256(raw);p.PREDECESSOR87_SHA256=p.sha256(b''.join(raw.splitlines(keepends=True)[:87]))
        self.original_ref=self.put('prefix88.jsonl',raw);self.original_ref['rows']=88
        self.put(p.BREADTH_FIRST_AUTHORITY['path'],(ROOT/p.BREADTH_FIRST_AUTHORITY['path']).read_bytes())
        self.recovery=self.put('recovery.py',b'# synthetic provider source\n')
        self.manifest=self.put('recovery.json',b'{}\n')
    def tearDown(self):
        p.ORIGINAL_PREFIX_SHA256=self.oldsha;p.PREDECESSOR87_SHA256=self.old87;self.tmp.cleanup()
    def put(self,path,raw):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        return {'path':path,'sha256':p.sha256(raw)}
    def core(self,status):
        codeql={'tool':'codeql','group_id':'codeql-swift-common108',
                 'attempt_id':'codeql-swift-common108-attempt-01-series-01','execution_series':1,
                 'status':status,'source_commit':'d'*40,'plan_commit':'e'*40,'contract_sha256':'f'*64}
        receipt=self.put(f'reports/releases/v0.9.2/attempts/{codeql["attempt_id"]}/completed.json',p.canonical_json(codeql))
        raw=b''.join(p.canonical_json(x) for x in [*self.original,codeql])
        prefix=self.put('incoming.jsonl',raw);prefix['rows']=len(self.original)+1
        self.put(p.LEDGER_PATH,raw)
        seal={'schema':p.INCOMING_HISTORY_SCHEMA,'authority':p.BREADTH_FIRST_AUTHORITY,
              'ledger_prefix':prefix,'codeql_terminal_receipt':receipt,
              'recovery_module':self.recovery,'recovery_manifest':self.manifest}
        return {'original_prefix':self.original_ref,'continuation_prefix':prefix,
                'breadth_first_authority':p.BREADTH_FIRST_AUTHORITY,
                'incoming_history':self.put('incoming-seal.json',p.canonical_json(seal)),
                'continuation':{'contract':{'path':'codeql-contract.json','sha256':'f'*64},
                                'source_commit':'d'*40,'plan_commit':'e'*40}}
    def test_codeql_completed_or_failed_terminal_is_truthful_without_joern_success(self):
        for status in ['completed','failed','timed-out','recorder-error','capacity-lost']:
            with self.subTest(status=status):p._validate_historical_prefixes(self.root,self.core(status))
    def test_seal_cannot_be_future_or_off_canonical_ledger(self):
        core=self.core('completed');self.put(p.LEDGER_PATH,b'{}\n')
        with self.assertRaisesRegex(ValueError,'actual canonical ledger'):p._validate_historical_prefixes(self.root,core)
    def test_receipt_cannot_relabel_failed_as_completed(self):
        core=self.core('failed');seal=json.loads((self.root/core['incoming_history']['path']).read_bytes())
        target=self.root/seal['codeql_terminal_receipt']['path'];value=json.loads(target.read_bytes());value['status']='completed'
        seal['codeql_terminal_receipt']=self.put(seal['codeql_terminal_receipt']['path'],p.canonical_json(value))
        core['incoming_history']=self.put('incoming-seal.json',p.canonical_json(seal))
        with self.assertRaisesRegex(ValueError,'ledger row differ'):p._validate_historical_prefixes(self.root,core)
    def test_authority_bytes_are_fixed_not_a_proposal(self):
        core=self.core('completed');core['breadth_first_authority']['sha256']='0'*64
        try:
            with self.assertRaises(ValueError):p._validate_historical_prefixes(self.root,core)
        finally:p.BREADTH_FIRST_AUTHORITY['sha256']=p.sha256((ROOT/p.BREADTH_FIRST_AUTHORITY['path']).read_bytes())
    def test_no_inserted_joern_success_or_additional_retry(self):
        core=self.core('completed');raw=(self.root/core['continuation_prefix']['path']).read_bytes()+p.canonical_json({'attempt_id':'joern05','status':'completed'})
        core['continuation_prefix']=self.put('incoming.jsonl',raw);core['continuation_prefix']['rows']=90
        seal=json.loads((self.root/core['incoming_history']['path']).read_bytes());seal['ledger_prefix']=core['continuation_prefix']
        core['incoming_history']=self.put('incoming-seal.json',p.canonical_json(seal));self.put(p.LEDGER_PATH,raw)
        with self.assertRaisesRegex(ValueError,'one CodeQL terminal'):p._validate_historical_prefixes(self.root,core)

class TerminalTests(unittest.TestCase):
    def test_actual_success_failed_timeout_terminal_are_not_retries(self):
        for status in ['completed','failed','timed-out']:terminal(row(status=status))
    def test_global_errors_never_continue(self):
        for mutation in [{'status':'recorder-error'},{'status':'capacity-lost'},
                         {'capacity_loss':{'code':'stop_floor'}},{'recorder_error':'integrity'},
                         {'disk_guard_error':{'code':'working_ceiling'}}, {'timed_out':True}]:
            value=row(status='failed');value.update(mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):terminal(value)
    def test_untracked_or_uncertain_descendants_never_continue(self):
        for mutation in [{'cleanup_status':'uncertain'}, {'tracking_error':'lost'},
                         {'tracked_processes':[]}, {'root_pid':None}]:
            value=row(status='failed');value['process_ownership'].update(mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):terminal(value)
    def test_global_c03_and_all_other02_preserved(self):
        self.assertEqual(p._attempt_id('bifrost-c-kernel'),'bifrost-c-kernel-attempt-03-series-02')
        self.assertEqual(p._attempt_id('bifrost-java-modeling'),'bifrost-java-modeling-attempt-02-series-02')
    def test_safety_proof_is_exact_and_after_terminal_receipt(self):
        value=row(status='failed');safety={'schema':'v092-bifrost-v0140-terminal-continuation-safety/v1',
          'status':'tracked-cleanup-and-resource-checked','group_id':value['group_id'],'attempt_id':value['attempt_id'],
          'receipt_sha256':'d'*64,'checked_utc':'2026-10-24T12:00:01Z','owned_processes_gone':True,
          'resources_valid':True,'tracked_processes':value['process_ownership']['tracked_processes']}
        p.validate_continuation_safety(safety,value,'d'*64)
        for field,bad in [('checked_utc','2026-10-24T11:59:59Z'),('resources_valid',False),
                          ('owned_processes_gone',False),('receipt_sha256','e'*64),('tracked_processes',[])]:
            changed={**safety,field:bad}
            with self.subTest(field=field),self.assertRaises(ValueError):p.validate_continuation_safety(changed,value,'d'*64)
    def test_stronger_hashed_bifrost_detector_and_idle_exception(self):
        self.assertTrue(s._hashed_bifrost_contenders('1 0.0 0.0 /bin/bifrost-abcdef scan'))
        self.assertFalse(s._hashed_bifrost_contenders('1 0.0 0.0 /bin/bifrost-abcdef --mcp'))
        self.assertTrue(s._hashed_bifrost_contenders('1 1.0 0.0 /bin/bifrost-abcdef --mcp'))

class SelectionTests(unittest.TestCase):
    def context(self,codeql=True):
        ids=[g['id'] for g in PLAN['groups'] if g['tool']=='bifrost']
        prefix=[]
        for g in PLAN['groups']:
            if g['id']=='joern-swift-common108' or (not codeql and g['id']=='codeql-swift-common108'):continue
            prefix.append({'group_id':g['id'],'attempt_id':f'{g["id"]}-old','status':'completed','exit_code':0})
        return {'ids':ids,'prefix':prefix,'source_commit':'a'*40,'plan_commit':'b'*40,'contract_sha256':'c'*64}
    def shape(self,selected):
        reports=[r for g in PLAN['groups'] if g['id'] in selected for r in g['reports']]
        return len(selected),len(reports),sum(len(r['case_ids']) for r in reports)
    def test_actual_complete20_with_codeql_but_missing_joern_is83_87_4144(self):
        ctx=self.context();tail=[row(g) for g in ctx['ids']]
        chosen=b._mixed_selected(ctx,ctx['prefix']+tail,final=True)
        self.assertEqual(self.shape(chosen),(83,87,4144))
        self.assertTrue(all(chosen[g]['attempt_id']==p._attempt_id(g) for g in ctx['ids']))
    def test_failed_codeql_is82_82_4036_no_fake_success(self):
        ctx=self.context(False);chosen=b._mixed_selected(ctx,ctx['prefix']+[row(g) for g in ctx['ids']],final=True)
        self.assertEqual(self.shape(chosen),(82,82,4036))
    def test_failed_replacement_never_falls_back_to_old0131(self):
        ctx=self.context();tail=[row(g,'failed' if i==0 else 'completed') for i,g in enumerate(ctx['ids'])]
        chosen=b._mixed_selected(ctx,ctx['prefix']+tail,final=True)
        self.assertNotIn(ctx['ids'][0],chosen)
        self.assertEqual(len(chosen),82)
    def test_prebatch_does_not_claim_any_old_bifrost_as0140(self):
        ctx=self.context();chosen=b._mixed_selected(ctx,ctx['prefix'],final=False)
        self.assertFalse(set(ctx['ids'])&set(chosen))
    def test_out_of_order_duplicate_or_c02_rejected(self):
        ctx=self.context();tail=[row(g) for g in ctx['ids']]
        for change in ['order','duplicate','c02']:
            mutated=copy.deepcopy(tail)
            if change=='order':mutated[0],mutated[1]=mutated[1],mutated[0]
            elif change=='duplicate':mutated.append(mutated[0])
            else:next(x for x in mutated if x['group_id']=='bifrost-c-kernel')['attempt_id']='bifrost-c-kernel-attempt-02-series-02'
            with self.subTest(change=change),self.assertRaises(ValueError):b._mixed_selected(ctx,ctx['prefix']+mutated,final=True)
    def test_final_batch_requires_actual_all20_outcomes(self):
        ctx=self.context()
        with self.assertRaises(ValueError):b._mixed_selected(ctx,ctx['prefix']+[row(ctx['ids'][0])],final=True)

if __name__=='__main__':unittest.main()
