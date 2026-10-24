#!/usr/bin/env python3
"""Synthetic integration of real partial replay and breadth-first batch loop.

Mocks replace actual processes, real analyzer/checker I/O, and resource probes;
no production receipt, admission, replay, source, or analyzer is touched.
"""
from __future__ import annotations
import contextlib
import importlib.util
import json
from pathlib import Path,PurePosixPath
import tempfile
import types
import unittest
from unittest import mock

BASE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
fixture=load('breadth11_regression_fixture',BASE/'test-bifrost-v0140-replacement-12.py')
p,b,s=fixture.p,fixture.b,fixture.s

class SourceDelta05Tests(unittest.TestCase):
    def run_delta(self,*,extra=False,wrong_after=False,wrong_base=False,wrong_incoming=False,
                  missing_closure=False,wrong_closure_bytes=False,extra_source=False,bad_ancestry=False):
        design=json.loads((fixture.ROOT/p.SOURCE_DESIGN_04['path']).read_bytes())
        design['reviewed_baseline_head']=design['actual_observed_head']
        design['immediate_patch_base']='d'*40
        design['incoming_codeql']={'source_commit':'a'*40,'plan_commit':'b'*40,'contract':{'path':'codeql.json','sha256':'c'*64}}
        blobs={}
        for item in design['allowed_source_delta']:
            if item['current_before_sha256'] is not None:
                blobs[('d'*40,item['path'])]=b'before';item['current_before_sha256']=p.sha256(b'before')
            blobs[('f'*40,item['path'])]=b'after'
            item['expected_after_sha256']=p.sha256(b'wrong' if wrong_after else b'after')
        path='scripts/reviewed-codeql.py' if not extra_source else 'src/unapproved.rs'
        design['reviewed_intervening_changes']=[{'path':path,'status':'A','before_sha256':None,
            'after_sha256':p.sha256(b'wrong' if wrong_closure_bytes else b'actual-codeql-script')}]
        blobs[('d'*40,path)]=b'actual-codeql-script'
        if missing_closure:design['reviewed_intervening_changes']=[]
        paths=[x['path'] for x in design['allowed_source_delta']]
        changes='\n'.join(('A' if x['current_before_sha256'] is None else 'M')+'\t'+x['path'] for x in design['allowed_source_delta'])
        if extra:changes+='\nM\tsrc/unapproved.rs'
        manifest={'source_delta_paths':paths,'source_delta_baseline':'0'*40 if wrong_base else 'd'*40}
        def git(root,*args):
            self.assertEqual(args[:3],('diff','--name-status','--no-renames'))
            return 'A\t'+path if args[3]==design['reviewed_baseline_head'] else changes
        def ancestor(root,left,right,label):
            if bad_ancestry and label=='actual CodeQL plan to immediate patch base':raise ValueError('wrong actual CodeQL plan ancestry')
        with mock.patch.object(b,'_ancestor',side_effect=ancestor) as ancestry,mock.patch.object(b,'_git',side_effect=git),\
             mock.patch.object(b,'_git_show',side_effect=lambda root,revision,path:blobs[revision,path]),\
             mock.patch.object(b,'_bound',return_value=b'synthetic patch'):
            result=b._source_delta05(fixture.ROOT,design,manifest,'0'*40 if wrong_incoming else 'a'*40,'f'*40,incoming_plan='b'*40)
            self.assertTrue(any(call.args[1:3]==('b'*40,'d'*40) for call in ancestry.call_args_list))
            return result
    def test_actual_codeql_source_is_not_relabelled_old_joern_and_nine_bytes_remain_fixed(self):
        result=self.run_delta();self.assertEqual(len(result['paths']),9);self.assertEqual(result['incoming_source'],'a'*40)
    def test_new_source_cannot_include_unreviewed_changed_file(self):
        with self.assertRaisesRegex(ValueError,'outside exact'):self.run_delta(extra=True)
    def test_formatted_target_bytes_are_not_inferred(self):
        with self.assertRaisesRegex(ValueError,'target bytes'):self.run_delta(wrong_after=True)
    def test_immediate_base_must_match_immutable_source_evidence(self):
        with self.assertRaisesRegex(ValueError,'actual immediate patch base'):self.run_delta(wrong_base=True)
    def test_actual_codeql_source_cannot_be_relabelled(self):
        with self.assertRaisesRegex(ValueError,'incoming CodeQL source/plan'):self.run_delta(wrong_incoming=True)
    def test_full_intervening_closure_cannot_omit_a_file(self):
        with self.assertRaisesRegex(ValueError,'intervening source changes'):self.run_delta(missing_closure=True)
    def test_intervening_closure_hashes_are_verified(self):
        with self.assertRaisesRegex(ValueError,'after bytes'):self.run_delta(wrong_closure_bytes=True)
    def test_intervening_unreviewed_rust_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside exact reviewed CodeQL'):self.run_delta(extra_source=True)
    def test_immediate_base_must_descend_actual_codeql_plan(self):
        with self.assertRaisesRegex(ValueError,'CodeQL plan ancestry'):self.run_delta(bad_ancestry=True)

class HistoricalOriginTests(unittest.TestCase):
    def context(self):
        import copy
        design=json.loads((fixture.ROOT/p.SOURCE_DESIGN_04['path']).read_bytes())
        rows=[json.loads(line) for line in (fixture.ROOT/b.LEDGER_PATH).read_bytes().splitlines()][:88]
        contexts={}
        for old in design['actual_historical_bifrost_contexts']:
            digest=old['contract']['sha256']
            declaration=next(x for x in design['actual_historical_bifrost_rows'] if x['contract_sha256']==digest)
            contexts[digest]={'plan_commit':declaration['plan_commit'],'validated':{
                'bytes_sha256':digest,'plan':{'source_commit':old['contract_source_commit']},
                'tools':{'runner':copy.deepcopy(old['historical_harness']),'bifrost':copy.deepcopy(old['tool'])}}}
        return design,contexts,rows
    def test_real_21_old_receipt_rows_preserve_two_original_contexts_and_harnesses(self):
        design,contexts,rows=self.context()
        b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
        self.assertEqual(len([r for r in rows if r.get('tool')=='bifrost']),21)
        self.assertEqual(len(contexts),2)
    def test_old_harness_cannot_be_new_harness_even_when_new_reports_are_selected(self):
        design,contexts,rows=self.context()
        for origin in contexts.values():origin['validated']['tools']['runner']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'original harness'):
            b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
    def test_preceding_joern_source_cannot_relabel_historical_bifrost(self):
        design,contexts,rows=self.context()
        for origin in contexts.values():origin['validated']['plan']['source_commit']=design['preceding_joern_measured_source']
        with self.assertRaisesRegex(ValueError,'origin relabeled'):
            b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
    def test_failed_c01_receipt_must_remain_present(self):
        design,contexts,rows=self.context()
        rows=[r for r in rows if r.get('attempt_id')!='bifrost-c-kernel-attempt-01-series-01']
        with self.assertRaisesRegex(ValueError,'receipt count'):
            b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
    def test_real_frozen_helper_never_rebinds_old_native_reports_to_new_harness(self):
        helper=load('history05_native_adapter',BASE/'bifrost-v0140-replacement-05.py')
        design,contexts,rows=self.context()
        old_native=lambda *args:'original0131-native-validation'
        checker=types.SimpleNamespace(EXPECTED_TOOL_VERSIONS={'bifrost':'bifrost 0.13.1'},_native_report_build_identity=old_native)
        for origin in contexts.values():
            origin['role']='historical'
            with helper._checker_context({'checker':checker},origin):
                self.assertEqual(checker.EXPECTED_TOOL_VERSIONS['bifrost'],'bifrost 0.13.1')
                self.assertIs(checker._native_report_build_identity,old_native)
        replacement={'validated':{},'role':'replacement'}
        with helper._checker_context({'checker':checker},replacement):
            self.assertEqual(checker.EXPECTED_TOOL_VERSIONS['bifrost'],'bifrost 0.14.0')
        self.assertIs(checker._native_report_build_identity,old_native)
        self.assertEqual(checker.EXPECTED_TOOL_VERSIONS['bifrost'],'bifrost 0.13.1')
    def test_successor05_cannot_mutate_source04_history_or_nine_reviewed_bytes(self):
        import copy
        original=json.loads((fixture.ROOT/p.SOURCE_DESIGN_04['path']).read_bytes())
        core={'source_design':{'path':p.SOURCE_DESIGN_05_PATH,'sha256':'a'*64},
              'continuation':{'source_commit':'a'*40,'plan_commit':'b'*40,'contract':{'path':'actual.json','sha256':'c'*64}}}
        design={k:copy.deepcopy(original[k]) for k in ('historical_outputs_immutable','historical_evidence_strategy',
                'actual_historical_bifrost_contexts','actual_historical_bifrost_rows','allowed_source_delta','unchanged_source_patch')}
        design.update(schema='v092-bifrost-source-post-codeql-rebase/v1',predecessor_design=p.SOURCE_DESIGN_04,
            scheduling_authority=p.BREADTH_FIRST_AUTHORITY,reviewed_baseline_head=original['actual_observed_head'],
            incoming_codeql=copy.deepcopy(core['continuation']),immediate_patch_base='d'*40,reviewed_intervening_changes=[])
        def bound(root,ref,label):return p.canonical_json(original if ref==p.SOURCE_DESIGN_04 else design)
        with mock.patch.object(p,'_bound',side_effect=bound):
            self.assertEqual(p.validate_source_design(fixture.ROOT,core)['incoming_codeql']['source_commit'],'a'*40)
            for key in ['actual_historical_bifrost_rows','allowed_source_delta','unchanged_source_patch']:
                saved=copy.deepcopy(design[key]);design[key]=[]
                with self.subTest(key=key),self.assertRaisesRegex(ValueError,'immutable source04'):
                    p.validate_source_design(fixture.ROOT,core)
                design[key]=saved
            design['incoming_codeql']['source_commit']='0'*40
            with self.assertRaisesRegex(ValueError,'actual incoming CodeQL'):p.validate_source_design(fixture.ROOT,core)

class ReplayTests(unittest.TestCase):
    def test_real_partial_loop_verifies_all_history_including_failures_and_exact_selected_partitions(self):
        ctx=fixture.SelectionTests().context();tail=[fixture.row(g) for g in ctx['ids']]
        rows=ctx['prefix']+tail
        for i,row in enumerate(rows):
            row.setdefault('contract_sha256','c'*64)
            row.setdefault('source_commit','a'*40);row.setdefault('plan_commit','b'*40)
            row['start_utc']=f'2026-10-24T12:{i//60:02d}:{i%60:02d}Z';row['end_utc']=row['start_utc']
        failed={'group_id':'joern-swift-common108','attempt_id':'joern04','status':'failed',
                'source_commit':'a'*40,'plan_commit':'b'*40,'contract_sha256':'c'*64,
                'start_utc':'2026-10-24T11:59:59Z','end_utc':'2026-10-24T11:59:59Z'}
        rows.insert(0,failed);ctx['prefix'].insert(0,failed)
        groups={g['id']:g for g in fixture.PLAN['groups']}
        calls=[]
        normalized={'groups':fixture.PLAN['groups'],'bytes_sha256':'c'*64,'plan':{'source_commit':'a'*40}}
        origin={'validated':normalized,'plan_commit':'b'*40}
        def verify(root,value,group,row,*args):
            calls.append(('success',row['attempt_id']))
            return ([{'rows':len(r['case_ids'])} for r in group['reports']],{'KnownStale':0})
        def failed_verify(*args):calls.append(('failure',args[3]['attempt_id']));return {'attempt_id':args[3]['attempt_id']}
        checker=types.SimpleNamespace(_verify_one_group=verify,_verify_failed_attempt=failed_verify,
           _assert_attempt_directories=lambda root,ids:self.assertEqual(len(ids),len(rows)),
           _validate_wall_budget=lambda rows,window:None)
        executor=types.SimpleNamespace(_historical_group_for_replay=lambda value,row:groups[row['group_id']])
        replacement=types.SimpleNamespace(_row_context=lambda context,row:origin,
          _attempt_number=lambda attempt:3 if attempt.startswith('bifrost-c-kernel-attempt-03') else 1,
          _checker_context=lambda *args:contextlib.nullcontext())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ledger=root/b.LEDGER_PATH;ledger.parent.mkdir(parents=True);ledger.write_bytes(b''.join(p.canonical_json(r) for r in rows))
            receipt=root/'reports/releases/v0.9.2/attempts/joern04/completed.json';receipt.parent.mkdir(parents=True);receipt.write_bytes(p.canonical_json(failed))
            context={**ctx,'contexts':{'c'*64:origin},'root':root,'checker':checker,'executor':executor,'validated':normalized}
            chosen=b._mixed_selected(context,rows,final=True)
            result=b._partial_replay(replacement,context,rows,chosen)
        self.assertEqual(len(calls),len(rows))
        self.assertEqual((result['selected_groups'],result['partitions'],result['rows']),(83,87,4144))
        self.assertEqual(result['status'],'partial-evidence-verified')
        self.assertFalse(result['full_release_gate_satisfied'])
        self.assertEqual(result['missing_groups'],['joern-swift-common108'])
    def test_partial_checker_cannot_return_full_configuration_gate(self):
        import inspect
        code=inspect.getsource(b.load_and_validate)
        self.assertIn('checker_result.get("full_release_gate_satisfied") is not True',code)
        self.assertNotIn('CONTINUATION06',code)

class BatchTests(unittest.TestCase):
    def run_batch(self,stop_at=None):
        groups=['bifrost-c-kernel','bifrost-js-kernel','bifrost-java-modeling']
        outcomes={g:fixture.row(g,'failed' if i==0 else 'completed') for i,g in enumerate(groups)}
        core={'replacement_groups':groups,'sidecar_namespace':'sidecars','lock_path':'lock',
              'breadth_first_authority':p.BREADTH_FIRST_AUTHORITY,'incoming_history':{'path':'actual-seal','sha256':'a'*64}}
        slots={g:{'attempt_id':p._attempt_id(g),'admission_path':f'sidecars/{g}/admission.json',
                  'phase_gate_path':f'sidecars/{g}/phase.json','completion_path':f'sidecars/{g}/completion.json'} for g in groups}
        manifest={'execution_admission_slots':slots}
        summary={'status':'partial-evidence-verified','selected_groups':82,'full_release_gate_satisfied':False}
        context={'validated_full_normalized_plan':{'plan':{'groups':[{'id':g,'deadline_seconds':30} for g in groups]}},
                 'checker_summary_or_pending':summary}
        writes=[];dispatched=[];completions=[]
        protocol=types.SimpleNamespace(write_immutable=lambda root,path,value:writes.append((path,value)),
                                      canonical_json=p.canonical_json)
        def refs(*args,**kwargs):return {'path':'bound','sha256':'d'*64}
        def complete(root,manifest_path,sha,group,*args,**kwargs):
            self.assertTrue(kwargs['continuation_safety']['owned_processes_gone'])
            completions.append((group,outcomes[group]['status']));return refs()
        admission=types.SimpleNamespace(admit_parent=refs,admit_group=refs,write_phase_gate=refs,
                                      write_completion=complete,_write_bytes_exclusive=refs)
        bridge=types.SimpleNamespace(load_and_validate=lambda *a,**kw:context,load_dependencies=lambda root:{'executor':object()})
        class Child:
            pid=12345
            def wait(self,timeout=None):return 0
            def poll(self):return 0
        def popen(argv,**kwargs):dispatched.append(argv[0]);return Child()
        def read(root,path,*args):
            if path.endswith('/completed.json'):
                value=next(value for value in outcomes.values() if value['attempt_id'] in path)
                return p.canonical_json(value)
            return b'{}\n'
        def safety(root,core,value,*args):
            if value['group_id']==stop_at:raise s.Supervisor12Error('synthetic resource/containment guard failed')
            return {'owned_processes_gone':True}
        with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.dict(s.os.environ,{s.FIXTURE_ENV:'1'}))
            replacements={'_static':lambda *a:(protocol,manifest,core),'_load_admission':lambda *a:admission,
              '_validate_context':lambda *a:context,'_load_bridge':lambda *a:bridge,'_lock_target':lambda *a:Path(tmp)/'lock',
              '_lock_fd':lambda *a:contextlib.nullcontext(types.SimpleNamespace(fileno=lambda:3,name=str(Path(tmp)/"lock"),closed=False)),
              '_process':lambda *a:{},'raw_permit':lambda *a,**kw:{},'_write_raw_permit':refs,'_write_context':refs,
              'build_group_command':lambda root,path,sha,ctx,g,**kw:{'argv':[g],'environment':{}},
              '_wait_group_child':lambda *a:0,'_read':read,'_terminal_continuation_safety':safety}
            for key,value in replacements.items():stack.enter_context(mock.patch.object(s,key,value))
            stack.enter_context(mock.patch.object(s.subprocess,'Popen',popen))
            if stop_at:
                with self.assertRaisesRegex(ValueError,'synthetic resource'):s.run_groups(Path(tmp),'m','f'*64,context,{},'e'*64,
                       {g:({},'d'*64) for g in groups},fixture_only=True)
                result=None
            else:result=s.run_groups(Path(tmp),'m','f'*64,context,{},'e'*64,
                       {g:({},'d'*64) for g in groups},fixture_only=True)
        return result,dispatched,completions,writes
    def test_actual_run_groups_continues_failed_first_group_then_next_two_exactly_once(self):
        result,dispatched,completed,writes=self.run_batch()
        self.assertEqual(len(dispatched),3);self.assertEqual(len(set(dispatched)),3)
        self.assertEqual([value for group,value in completed],['failed','completed','completed'])
        self.assertEqual(result['status'],'batch-covered-with-failures')
        self.assertEqual([x['status'] for x in result['outcomes']],['failed','completed','completed'])
        self.assertFalse(result['full_release_gate_satisfied'])
        self.assertTrue(writes[-1][0].endswith('batch-outcomes.json'))
    def test_resource_guard_stops_whole_batch_and_preserves_explicit_partial_outcomes(self):
        result,dispatched,completed,writes=self.run_batch('bifrost-js-kernel')
        self.assertEqual(len(dispatched),2);self.assertEqual(len(completed),1)
        self.assertTrue(writes[-1][0].endswith('batch-stop-01.json'))
        self.assertEqual(writes[-1][1]['outcomes'][0]['status'],'failed')
        self.assertFalse(writes[-1][1]['later_groups_dispatched'])

if __name__=='__main__':unittest.main()
