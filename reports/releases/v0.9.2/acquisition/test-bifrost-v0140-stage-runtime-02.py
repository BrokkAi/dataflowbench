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
import sys
from unittest import mock

BASE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    # Dataclasses resolve the defining module through sys.modules while the
    # bridge fixture is being imported.  Keep this helper scoped to the test
    # import and remove it if execution fails.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module
fixture=load('breadth11_regression_fixture',BASE/'test-bifrost-v0140-replacement-13.py')
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
        core={'source_design':{'path':p.SOURCE_DESIGN_06_PATH,'sha256':'a'*64},
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
            if value['group_id']==stop_at:raise s.Supervisor13Error('synthetic resource/containment guard failed')
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

class StageRuntimeGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ledger_path = self.root / "reports/releases/v0.9.2/ledger-v1.jsonl"
        self.ledger_path.parent.mkdir(parents=True)
        row = {"attempt_id": "historical-attempt-01", "group_id": "historical-group",
               "status": "completed", "exit_code": 0, "execution_series": 1}
        self.ledger_path.write_bytes(p.canonical_json(row))
        self.contract = {"groups": [], "source_commit": "a" * 40,
                         "total_wall_budget_seconds": None}
        self.contract_path = self.root / "contract.json"
        self.contract_raw = p.canonical_json(self.contract)
        self.contract_path.write_bytes(self.contract_raw)
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_bytes(p.canonical_json({"schema": "fixture-manifest"}))
        self.historical_sha = "1" * 64
        historical = {"bytes_sha256": self.historical_sha,
                      "plan": {"source_commit": "b" * 40}, "groups": []}
        self.modules = {}
        replacement = types.ModuleType("fixture_replacement15")
        replacement.validate_static = lambda root, path: {
            "manifest": {"schema": "fixture-manifest"},
            "core": {"contract": {"path": "contract.json", "sha256": p.sha256(self.contract_raw)}}}
        executor = types.ModuleType("fixture_executor")
        executor.validate_plan = lambda path, repo_root: {
            "bytes_sha256": p.sha256(self.contract_raw), "path": str(self.contract_path),
            "repo_root": str(self.root), "plan": dict(self.contract)}
        checker = types.ModuleType("fixture_checker")
        configuration = types.ModuleType("fixture_configuration")
        incoming = types.ModuleType("fixture_incoming")
        incoming.load_runtime_context = lambda **kwargs: {
            "base": {"validated": historical, "plan_commit": "b" * 40,
                     "source_commit": "b" * 40, "role": "base"},
            "repaired": {"validated": historical, "plan_commit": "b" * 40,
                         "source_commit": "b" * 40, "role": "continuation"},
            "contexts": {self.historical_sha: {"validated": historical,
                          "plan_commit": "b" * 40, "source_commit": "b" * 40,
                          "role": "historical"}},
            "checker_summary": {"status": "partial-evidence-verified", "selected_groups": 1},
            "configuration_summary": {"status": "configuration-pending-complete-matrix"},
        }
        names = ("bridge10", "replacement15", "executor", "checker", "configuration",
                 "incoming_recovery", "policy_source", "policy_runtime", "protocol15",
                 "admission15", "supervisor15")
        for name, module in {
            "replacement15": replacement, "executor": executor, "checker": checker,
            "configuration": configuration, "incoming_recovery": incoming,
            "policy_source": types.ModuleType("fixture_policy_source"),
            "policy_runtime": types.ModuleType("fixture_policy_runtime"),
            "protocol15": types.ModuleType("fixture_protocol15"),
            "admission15": types.ModuleType("fixture_admission15"),
            "supervisor15": types.ModuleType("fixture_supervisor15"),
            "bridge10": types.ModuleType("fixture_bridge10"),
        }.items():
            self.modules[name] = module
        self.members = [types.SimpleNamespace(name=name, module_object=self.modules[name],
                                               canonical_path=f"fixture/{name}.py",
                                               source_sha256="2" * 64) for name in names]
        self.graph = types.SimpleNamespace(
            members=tuple(self.members), graph_sha256="3" * 64,
            fixture_only=True, module=lambda name: self.modules[name])
        self.core = {
            "manifest_ref": {"path": "manifest.json", "sha256": p.sha256(self.manifest_path.read_bytes())},
            "manifest_path": "manifest.json",
            "contract": {"path": "contract.json", "sha256": p.sha256(self.contract_raw)},
            "source_commit": "a" * 40, "plan_commit": "b" * 40,
            "ledger_path": "reports/releases/v0.9.2/ledger-v1.jsonl",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_graph_owned_runtime_keeps_lossless_frozen_module_identity(self):
        stage = load("stage_runtime_graph_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        value = stage.load_runtime_context(self.root, self.core, graph=self.graph)
        self.assertEqual(value["schema"], "v092-bifrost-v0140-runtime-context/v1")
        self.assertTrue(value["lossless_runtime_objects"])
        self.assertIs(value["modules"]["replacement05"], self.modules["replacement15"])
        self.assertIs(value["modules"]["executor"], self.modules["executor"])
        self.assertIs(value["mixed_context"]["executor"], self.modules["executor"])
        self.assertRegex(value["bridge_context"]["context_digest"], r"^[0-9a-f]{64}$")

    def test_provider_foreign_module_is_rejected(self):
        stage = load("stage_runtime_foreign_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        foreign = types.ModuleType("foreign_executor")
        original = self.modules["incoming_recovery"].load_runtime_context
        self.modules["incoming_recovery"].load_runtime_context = lambda **kwargs: {
            **original(**kwargs), "modules": {"replacement05": self.modules["replacement15"],
                                               "executor": foreign, "checker": self.modules["checker"],
                                               "configuration": self.modules["configuration"]}}
        try:
            with self.assertRaisesRegex(ValueError, "foreign executor"):
                stage.load_runtime_context(self.root, self.core, graph=self.graph)
        finally:
            self.modules["incoming_recovery"].load_runtime_context = original

    def test_transitive_closure_wrong_digest_and_symlink_fail_closed(self):
        stage = load("stage_runtime_closure_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        path = self.root / "nested.py"
        path.write_bytes(b"nested")
        self.core["runtime_graph_closure"] = [{"name": "nested", "path": "nested.py", "sha256": "0" * 64}]
        with self.assertRaisesRegex(ValueError, "digest changed"):
            stage.load_runtime_context(self.root, self.core, graph=self.graph)
        self.core["runtime_graph_closure"] = [{"name": "nested", "path": "../nested.py", "sha256": p.sha256(b"nested")}]
        with self.assertRaisesRegex(ValueError, "unsafe"):
            stage.load_runtime_context(self.root, self.core, graph=self.graph)

    def test_production_closure_rejects_reordered_complete_named_members(self):
        stage = load("stage_runtime_ordered_closure_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        first_raw, second_raw = b"first-member\n", b"second-member\n"
        first_path, second_path = self.root / "first.py", self.root / "second.py"
        first_path.write_bytes(first_raw)
        second_path.write_bytes(second_raw)
        first = types.SimpleNamespace(name="first", canonical_path="first.py",
                                      source_sha256=p.sha256(first_raw), module_object=types.ModuleType("first"))
        second = types.SimpleNamespace(name="second", canonical_path="second.py",
                                       source_sha256=p.sha256(second_raw), module_object=types.ModuleType("second"))
        graph = types.SimpleNamespace(members=(first, second), fixture_only=False)
        self.core["runtime_graph_closure"] = [
            {"name": "second", "path": "second.py", "sha256": p.sha256(second_raw)},
            {"name": "first", "path": "first.py", "sha256": p.sha256(first_raw)},
        ]
        with self.assertRaisesRegex(ValueError, "ordered graph membership"):
            stage._stage_closure(self.root, self.core, graph)

    def test_pinned_nested_loader_requires_explicit_name_route_for_duplicate_paths(self):
        stage = load("stage_runtime_named_loader_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        path = self.root / "nested.py"
        raw = b"nested-source"
        path.write_bytes(raw)
        first = types.SimpleNamespace(name="nested_first", canonical_path="nested.py",
                                      source_sha256=p.sha256(raw), module_object=types.ModuleType("nested_first"))
        second = types.SimpleNamespace(name="nested_second", canonical_path="nested.py",
                                       source_sha256=p.sha256(raw), module_object=types.ModuleType("nested_second"))
        graph = types.SimpleNamespace(members=(first, second))
        facade = stage._stage_pinned_importlib(self.root.resolve(), graph, stage.importlib)
        spec = facade.util.spec_from_file_location("nested_second", path)
        self.assertIs(facade.util.module_from_spec(spec), second.module_object)
        with self.assertRaisesRegex(ValueError, "explicitly bound"):
            facade.util.spec_from_file_location("unregistered_nested", path)

    def test_scoped_loader_checks_historical_policy_sha_before_policy14_proxy(self):
        stage = load("stage_runtime_policy_route_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement15"]
        names = tuple(self.modules) + ("replacement05",)
        members = tuple(types.SimpleNamespace(name=name, module_object=modules[name],
                                              canonical_path=f"fixture/{name}.py",
                                              source_sha256="2" * 64) for name in names)
        graph = types.SimpleNamespace(members=members, graph_sha256="4" * 64,
                                      fixture_only=False, module=lambda name: modules[name])
        old_path = self.root / stage.OLD_POLICY_PATH
        old_path.parent.mkdir(parents=True)
        old_path.write_bytes((BASE / "bifrost-v0140-replacement-13.py").read_bytes())
        with stage._stage_full_graph_scope(self.root, self.core, graph, modules,
                                           mode="before", ledger_bytes=None):
            with self.assertRaisesRegex(ValueError, "historical source digest"):
                stage._load_module(self.root, "source_design04_policy",
                                   {"path": stage.OLD_POLICY_PATH, "sha256": "0" * 64})
            loaded = stage._load_module(
                self.root, "source_design04_policy",
                {"path": stage.OLD_POLICY_PATH, "sha256": stage.OLD_POLICY_SHA256})
            self.assertIs(loaded, policy)

    def test_bridge10_dispatches_graph_owned_stage_runtime(self):
        bridge = load("bridge10_stage_dispatch_test", BASE / "bifrost-v0140-frozen-bridge-10.py")
        stage = load("stage_runtime_bridge_member_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        names = ("bridge10", "replacement15", "executor", "checker", "configuration",
                 "incoming_recovery", "policy_source", "policy_runtime", "protocol15",
                 "admission15", "supervisor15", "stage_runtime02")
        modules = dict(self.modules)
        modules["bridge10"] = bridge
        modules["stage_runtime02"] = stage
        modules["protocol15"].validate_static = lambda root, path: {
            "manifest": {"schema": "fixture-manifest"}, "core": self.core}
        modules["incoming_recovery"].load_runtime_context = lambda **kwargs: {
            "modules": {"replacement05": modules["replacement15"],
                         "executor": modules["executor"], "checker": modules["checker"],
                         "configuration": modules["configuration"]},
            "validated": {"plan": dict(self.contract), "bytes_sha256": p.sha256(self.contract_raw)},
            "mixed_context": {"validated": {"plan": dict(self.contract)}},
            "base": {"validated": {"plan": dict(self.contract)}, "plan_commit": "b" * 40},
            "repaired": {"validated": {"plan": dict(self.contract)}, "plan_commit": "b" * 40},
            "contexts": {self.historical_sha: {"validated": {"plan": dict(self.contract)},
                                                  "plan_commit": "b" * 40}},
            "checker_summary": {"status": "fixture"},
            "configuration_summary": {"status": "fixture"},
            "bridge_context": {"context_digest": "4" * 64},
        }
        members = tuple(bridge.GraphMember(name, f"fixture/{name}.py", "2" * 64,
                                            modules[name], f"fixture:{name}") for name in names)
        graph = bridge.PinnedBridgeGraph(members, fixture_only=True)
        value = bridge._graph_runtime_context(self.root, self.core, graph, mode="before", ledger_bytes=None)
        self.assertIs(value.objects["modules"]["replacement05"], modules["replacement15"])
        self.assertEqual(value.objects["schema"], "v092-bifrost-v0140-runtime-context/v1")

    def test_full_scope_uses_local_importlib_facade_and_positional_root_loader(self):
        stage = load("stage_runtime_scope_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement15"]
        names = tuple(self.modules) + ("replacement05",)
        members = tuple(types.SimpleNamespace(name=name, module_object=modules[name],
                                              canonical_path=f"fixture/{name}.py",
                                              source_sha256="2" * 64) for name in names)
        graph = types.SimpleNamespace(members=members, graph_sha256="4" * 64,
                                      fixture_only=False, module=lambda name: modules[name])
        original_importlib = stage.importlib
        original_util = stage.importlib.util
        with stage._stage_full_graph_scope(self.root, self.core, graph,
                                           stage._stage_modules(graph), mode="before",
                                           ledger_bytes=None):
            self.assertIsNot(stage.importlib, original_importlib)
            self.assertIsNot(stage.importlib.util, original_util)
            loaded = stage.load_dependencies(self.root)
            self.assertIs(loaded["replacement05"], modules["replacement05"])
        self.assertIs(stage.importlib, original_importlib)
        self.assertIs(stage.importlib.util, original_util)

    def test_full_scope_routes_late_checker_recovery_loader_and_restores_it(self):
        stage = load("stage_runtime_late_checker_loader_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement15"]
        # The frozen checker imports this role only during failed-attempt
        # verification.  Give it a real module-local importlib attribute so
        # the full scope must install the same explicit route facade that the
        # provider scope uses for incoming replay.
        checker = modules["checker"]
        checker_importlib = stage.importlib
        checker.importlib = checker_importlib
        resource = types.ModuleType("fixture_nested_resource_recovery")
        resource.importlib = checker_importlib
        nested_path = self.root / "fixture/incoming_nested_resource_recovery.py"
        nested_path.parent.mkdir(parents=True, exist_ok=True)
        nested_raw = b"late-checker-resource-recovery\n"
        nested_path.write_bytes(nested_raw)
        modules["incoming_nested_resource_recovery"] = resource
        modules["stage_runtime02"] = stage
        names = tuple(self.modules) + ("replacement05", "incoming_nested_resource_recovery", "stage_runtime02")
        members = [types.SimpleNamespace(name=name, module_object=modules[name],
                                         canonical_path=("fixture/incoming_nested_resource_recovery.py"
                                                         if name == "incoming_nested_resource_recovery"
                                                         else f"fixture/{name}.py"),
                                         source_sha256=(p.sha256(nested_raw)
                                                        if name == "incoming_nested_resource_recovery"
                                                        else "2" * 64))
                   for name in names]
        graph = types.SimpleNamespace(members=tuple(members), graph_sha256="4" * 64,
                                      fixture_only=False, module=lambda name: modules[name])
        with stage._stage_full_graph_scope(self.root, self.core, graph, modules,
                                           mode="before", ledger_bytes=None):
            self.assertIsNot(checker.importlib, checker_importlib)
            outer_checker_importlib = checker.importlib
            with stage._stage_provider_scope(
                    self.root.resolve(), self.modules["incoming_recovery"],
                    {"executor": modules["executor"], "checker": checker,
                     "configuration": modules["configuration"]}, graph):
                # Nested provider scope must reuse the outer graph facade,
                # including its spec registry, rather than wrapping it again.
                self.assertIs(checker.importlib, outer_checker_importlib)
                spec = checker.importlib.util.spec_from_file_location(
                    "v092_resource_recovery_for_checker", nested_path)
                self.assertIs(checker.importlib.util.module_from_spec(spec), resource)
        self.assertIs(checker.importlib, checker_importlib)
        self.assertIs(resource.importlib, checker_importlib)

    def test_provider_scope_aliases_checker_executor_and_restores_foreign_instances(self):
        stage = load("stage_runtime_provider_alias_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        executor = self.modules["executor"]
        checker = self.modules["checker"]
        configuration = self.modules["configuration"]
        incoming = self.modules["incoming_recovery"]
        foreign_executor = object()
        foreign_checker = object()
        checker.EXECUTOR = foreign_executor
        configuration.CHECKER = foreign_checker
        configuration.EXECUTOR = foreign_executor
        incoming.EXECUTOR = foreign_executor
        incoming.CHECKER = foreign_checker
        observed = []
        incoming.load_runtime_context = lambda **kwargs: observed.append(
            (checker.EXECUTOR is executor, configuration.CHECKER is checker,
             configuration.EXECUTOR is executor, incoming.EXECUTOR is executor,
             incoming.CHECKER is checker)) or {"contexts": {}}
        try:
            with stage._stage_provider_scope(self.root.resolve(), incoming,
                                             {"executor": executor, "checker": checker,
                                              "configuration": configuration}, self.graph):
                stage._stage_incoming(incoming, self.root.resolve(), self.core, self.graph,
                                      "before", None)
            self.assertEqual(observed, [(True, True, True, True, True)])
            self.assertIs(checker.EXECUTOR, foreign_executor)
            self.assertIs(configuration.CHECKER, foreign_checker)
            self.assertIs(configuration.EXECUTOR, foreign_executor)
            self.assertIs(incoming.EXECUTOR, foreign_executor)
            self.assertIs(incoming.CHECKER, foreign_checker)
        finally:
            incoming.load_runtime_context = lambda **kwargs: {
                "base": {"validated": {}, "plan_commit": "b" * 40},
                "repaired": {"validated": {}, "plan_commit": "b" * 40},
                "contexts": {}}

    def test_provider_named_loaders_bind_route_and_reject_ambiguous_or_foreign_requests(self):
        stage = load("stage_runtime_provider_named_loader_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        incoming = self.modules["incoming_recovery"]
        original_pinned = getattr(incoming, "_load_pinned_helper", None)
        original_generic = getattr(incoming, "_load_module", None)
        incoming._load_pinned_helper = lambda *args: None
        incoming._load_module = lambda *args: None
        replay_raw = b"named-replay-helper\n"
        executor_raw = b"named-executor\n"
        replay_path = self.root / "fixture/named-replay.py"
        executor_path = self.root / "fixture/named-executor.py"
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        replay_path.write_bytes(replay_raw)
        executor_path.write_bytes(executor_raw)
        replay_module = types.ModuleType("fixture_named_replay")
        executor_module = types.ModuleType("fixture_named_executor")
        base_members = list(self.graph.members)
        base_members.extend([
            types.SimpleNamespace(name="incoming_historical_replay_helper05",
                                  module_object=replay_module,
                                  canonical_path="fixture/named-replay.py",
                                  source_sha256=p.sha256(replay_raw)),
            types.SimpleNamespace(name="incoming_nested_executor",
                                  module_object=executor_module,
                                  canonical_path="fixture/named-executor.py",
                                  source_sha256=p.sha256(executor_raw)),
        ])
        graph = types.SimpleNamespace(members=tuple(base_members), graph_sha256="5" * 64,
                                      fixture_only=True,
                                      module=lambda name: next(item.module_object for item in base_members
                                                               if item.name == name))
        try:
            with stage._stage_provider_scope(self.root.resolve(), incoming,
                                             {"executor": self.modules["executor"],
                                              "checker": self.modules["checker"],
                                              "configuration": self.modules["configuration"]}, graph):
                self.assertIs(incoming._load_pinned_helper(
                    self.root, "fixture/named-replay.py", p.sha256(replay_raw),
                    "historical-replay-helper"), replay_module)
                self.assertIs(incoming._load_module(
                    self.root, "fixture/named-executor.py", "codeql_pending_executor"), executor_module)
                with self.assertRaisesRegex(ValueError, "explicitly bound"):
                    incoming._load_pinned_helper(
                        self.root, "fixture/named-replay.py", p.sha256(replay_raw), "unknown-helper")
                with self.assertRaisesRegex(ValueError, "digest differs"):
                    incoming._load_pinned_helper(
                        self.root, "fixture/named-replay.py", "0" * 64, "historical-replay-helper")
                with self.assertRaisesRegex(ValueError, "escaped"):
                    incoming._load_module(self.root.parent, "fixture/named-executor.py",
                                          "codeql_pending_executor")

            ambiguous = list(base_members)
            ambiguous.append(types.SimpleNamespace(
                name="incoming_historical_replay_helper05", module_object=types.ModuleType("duplicate"),
                canonical_path="fixture/named-replay.py", source_sha256=p.sha256(replay_raw)))
            ambiguous_graph = types.SimpleNamespace(members=tuple(ambiguous), graph_sha256="6" * 64,
                                                     fixture_only=True, module=lambda name: next(
                                                         item.module_object for item in ambiguous
                                                         if item.name == name))
            with stage._stage_provider_scope(self.root.resolve(), incoming,
                                             {"executor": self.modules["executor"],
                                              "checker": self.modules["checker"],
                                              "configuration": self.modules["configuration"]}, ambiguous_graph):
                with self.assertRaisesRegex(ValueError, "explicitly bound"):
                    incoming._load_pinned_helper(
                        self.root, "fixture/named-replay.py", p.sha256(replay_raw),
                        "historical-replay-helper")
        finally:
            if original_pinned is None:
                delattr(incoming, "_load_pinned_helper")
            else:
                incoming._load_pinned_helper = original_pinned
            if original_generic is None:
                delattr(incoming, "_load_module")
            else:
                incoming._load_module = original_generic

    def test_full_scope_aliases_checker_executor_and_restores_foreign_instances(self):
        stage = load("stage_runtime_full_alias_test", BASE / "bifrost-v0140-stage-runtime-02.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement15"]
        names = tuple(self.modules) + ("replacement05",)
        members = tuple(types.SimpleNamespace(name=name, module_object=modules[name],
                                              canonical_path=f"fixture/{name}.py",
                                              source_sha256="2" * 64) for name in names)
        graph = types.SimpleNamespace(members=members, graph_sha256="4" * 64,
                                      fixture_only=False, module=lambda name: modules[name])
        foreign_executor = object()
        foreign_checker = object()
        modules["checker"].EXECUTOR = foreign_executor
        modules["configuration"].CHECKER = foreign_checker
        modules["configuration"].EXECUTOR = foreign_executor
        with stage._stage_full_graph_scope(self.root, self.core, graph, modules,
                                           mode="before", ledger_bytes=None):
            self.assertIs(modules["checker"].EXECUTOR, modules["executor"])
            self.assertIs(modules["configuration"].CHECKER, modules["checker"])
            self.assertIs(modules["configuration"].EXECUTOR, modules["executor"])
        self.assertIs(modules["checker"].EXECUTOR, foreign_executor)
        self.assertIs(modules["configuration"].CHECKER, foreign_checker)
        self.assertIs(modules["configuration"].EXECUTOR, foreign_executor)


if __name__ == '__main__':
    unittest.main()
