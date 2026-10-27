#!/usr/bin/env python3
"""Synthetic integration of real partial replay and breadth-first batch loop.

Mocks replace actual processes, real analyzer/checker I/O, and resource probes;
no production receipt, admission, replay, source, or analyzer is touched.
"""
from __future__ import annotations
import contextlib
import ctypes
import importlib
import importlib.util
import hashlib
import json
from pathlib import Path,PurePosixPath
import tempfile
import types
import unittest
import sys
from unittest import mock

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
SOURCE=BASE/'bifrost-v0140-stage-runtime-07.py'

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


def load_source(path, name):
    return load(name, path)


fixture=load('breadth12_regression_fixture',BASE/'test-bifrost-v0140-replacement-13.py')
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


class ReaderScopeOwnershipTests(unittest.TestCase):
    """Exercise the two real local proxy factories through the stage pair.

    The target modules are harmless in-memory graph members.  The reader
    context managers and their local ``_LoaderProxy``/``_NestedLoader`` bodies
    are the repository implementations; no replay or validator is entered.
    """

    def setUp(self):
        self.stage = load("stage_reader_scope_ownership", BASE / "bifrost-v0140-stage-runtime-07.py")
        self.provider = load("provider_reader_scope_ownership", BASE / "codeql-terminal-history-04.py")
        self.codeql = load("codeql_reader_scope_ownership", BASE / "independent-pending-codeql-03.py")
        self.raw = (ROOT / "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
                    "sealed-ledger-prefix-88.jsonl").read_bytes()
        self.modules = []

        def target(name, relative):
            module = types.ModuleType(name)
            module.__file__ = str(ROOT / relative)
            module.LEDGER_PATH = PurePosixPath("reports/releases/v0.9.2/ledger-v1.jsonl")
            module._regular_bytes = lambda *args, **kwargs: b"original"
            module.validate_packet = lambda *args, **kwargs: {"status": "ok"}
            self.modules.append(types.SimpleNamespace(
                name=name, canonical_path=relative,
                source_sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                module_object=module))
            return module

        self.packet = target("incoming_nested_scoped_recovery", "scripts/v092_scoped_recovery.py")
        self.resource = target("incoming_nested_resource_recovery", "scripts/v092_resource_recovery.py")
        for role, relative, module in (
            ("nested_020_v092_scoped_recovery_packet", "scripts/v092_scoped_recovery.py", self.packet),
            ("nested_021_v092_resource_recovery", "scripts/v092_resource_recovery.py", self.resource),
        ):
            self.modules.append(types.SimpleNamespace(
                name=role, canonical_path=relative,
                source_sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                module_object=module))
        for name, relative, module in (
            ("incoming_recovery", "reports/releases/v0.9.2/acquisition/codeql-terminal-history-04.py",
             self.provider),
            ("incoming_predecessor03", "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py",
             self.codeql),
        ):
            self.modules.append(types.SimpleNamespace(
                name=name, canonical_path=relative,
                source_sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                module_object=module))
        policy = types.ModuleType("reader_scope_policy")
        policy.__file__ = str(ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py")
        self.modules.append(types.SimpleNamespace(
            name="policy_source",
            canonical_path="reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py",
            source_sha256=hashlib.sha256((ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py").read_bytes()).hexdigest(),
            module_object=policy))
        self.graph = types.SimpleNamespace(
            members=tuple(self.modules),
            module=lambda name: next(item.module_object for item in self.modules if item.name == name))
        self.factory = self.stage._StageImportFactory(
            ROOT, self.graph, importlib, policy_path=self.stage.OLD_POLICY_PATH, policy=policy)
        self.factory.bound_raw_sha256.add(hashlib.sha256(self.raw).hexdigest())
        self.provider_importlib = self.provider.importlib
        self.codeql_importlib = self.codeql.importlib
        self.provider.importlib = self.stage._stage_pinned_importlib(
            ROOT, self.graph, importlib, factory=self.factory)
        self.codeql.importlib = self.stage._stage_pinned_importlib(
            ROOT, self.graph, importlib, factory=self.factory)

    def tearDown(self):
        self.provider.importlib = self.provider_importlib
        self.codeql.importlib = self.codeql_importlib

    def _observer(self, owner, attribute, route, selector, role, raw_position):
        member = next(item for item in self.modules if item.name == role)
        return self.stage._stage_observe_context(
            self.factory, owner, attribute, route, selector,
            member.source_sha256, raw_position)

    def _load_target(self, owner, selector, relative, target):
        util = owner.importlib.util
        spec = util.spec_from_file_location(selector, ROOT / relative)
        self.assertIs(util.module_from_spec(spec), target)
        spec.loader.exec_module(target)

    def test_real_context_manager_factories_are_captured_and_restored(self):
        provider_observer = self._observer(
            self.provider, "_scoped_nested_ledger", "provider-nested",
            "v092_scoped_recovery_packet", "incoming_recovery", 1)
        codeql_observer = self._observer(
            self.codeql, "_scoped_resource_recovery_ledger", "codeql-resource",
            "v092_resource_recovery", "incoming_predecessor03", 0)
        with provider_observer:
            with self.provider._scoped_nested_ledger(ROOT, self.raw):
                with codeql_observer:
                    with self.codeql._scoped_resource_recovery_ledger(self.raw):
                        self.assertEqual(len(self.factory.invocations), 2)
                        self._load_target(self.codeql, "v092_resource_recovery",
                                          "scripts/v092_resource_recovery.py", self.resource)
                        self._load_target(self.provider, "v092_scoped_recovery_packet",
                                          "scripts/v092_scoped_recovery.py", self.packet)
                        bindings = {item.route: item for item in self.factory.invocations}
                        self.assertEqual(bindings["codeql-resource"].helper.__code__.co_freevars,
                                         ("func",))
                        self.assertIs(bindings["codeql-resource"].helper.__closure__[0].cell_contents,
                                      bindings["codeql-resource"].generator)
                        self.assertEqual(bindings["codeql-resource"].factory_function.__code__.co_freevars,
                                         ("_LoaderProxy", "original_factory"))
                        self.assertIs(bindings["codeql-resource"].factory_closure[0].cell_contents,
                                      bindings["codeql-resource"].wrapper_class)
                        self.assertIs(bindings["codeql-resource"].factory_closure[1].cell_contents,
                                      bindings["codeql-resource"].previous_factory)
                        self.assertEqual(bindings["provider-nested"].helper.__code__.co_freevars,
                                         ("func",))
                        self.assertIs(bindings["provider-nested"].helper.__closure__[0].cell_contents,
                                      bindings["provider-nested"].generator)
                        self.assertEqual(bindings["provider-nested"].factory_function.__code__.co_freevars,
                                         ("_NestedLoader", "original_factory"))
                        self.assertIs(bindings["provider-nested"].factory_closure[0].cell_contents,
                                      bindings["provider-nested"].wrapper_class)
                        self.assertIs(bindings["provider-nested"].factory_closure[1].cell_contents,
                                      bindings["provider-nested"].previous_factory)
                    self.assertEqual(len(self.factory.invocations), 1)
                self.assertEqual(len(self.factory.invocations), 1)
        self.assertIs(self.provider._scoped_nested_ledger, provider_observer.helper)
        self.assertIs(self.codeql._scoped_resource_recovery_ledger, codeql_observer.helper)

    def test_actual_codeql_load_frozen_body_uses_owner_bound_graph_instances(self):
        """Run the retained CodeQL loader body through the scoped route table.

        The regression must exercise ``load_frozen`` itself.  Replacing that
        function with a four-module facade would prove only the adapter, and
        would miss the source/digest/name checks performed by the real body.
        Each selector therefore has a distinct source-backed graph member,
        while a path mutation is rejected before a foreign instance can be
        returned.
        """
        target_specs = {
            "nested_003_codeql_pending_executor": "scripts/execute-release-v092.py",
            "nested_005_codeql_pending_checker": "scripts/check-release-v092.py",
            "nested_007_codeql_pending_configuration": "scripts/validate-v092-report-configurations.py",
            "nested_008_codeql_pending_disk_guard": "scripts/v092_disk_guard.py",
        }
        members = list(self.modules)
        targets = {}
        for role, relative in target_specs.items():
            module = types.ModuleType(role)
            module.__file__ = str(ROOT / relative)
            targets[role] = module
            members.append(types.SimpleNamespace(
                name=role,
                canonical_path=relative,
                source_sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                module_object=module,
            ))
        graph = types.SimpleNamespace(
            members=tuple(members),
            module=lambda name: next(item.module_object for item in members if item.name == name),
        )
        modules = {
            "executor": targets["nested_003_codeql_pending_executor"],
            "checker": targets["nested_005_codeql_pending_checker"],
            "configuration": targets["nested_007_codeql_pending_configuration"],
        }
        original_loader = self.codeql._load_module
        original_provider_importlib = self.provider.importlib
        original_codeql_importlib = self.codeql.importlib
        self.provider.importlib = importlib
        self.codeql.importlib = importlib
        try:
            with self.stage._stage_provider_scope(
                    ROOT, self.provider, modules, graph, stdlib_importlib=importlib):
                loaded = self.codeql.load_frozen(ROOT)
        finally:
            self.provider.importlib = original_provider_importlib
            self.codeql.importlib = original_codeql_importlib
        self.assertIs(loaded["executor"], targets["nested_003_codeql_pending_executor"])
        self.assertIs(loaded["checker"], targets["nested_005_codeql_pending_checker"])
        self.assertIs(loaded["configuration"], targets["nested_007_codeql_pending_configuration"])
        self.assertIs(loaded["disk_guard"], targets["nested_008_codeql_pending_disk_guard"])
        self.assertIs(self.codeql._load_module, original_loader)

        bad_members = [
            item if item.name != "nested_003_codeql_pending_executor" else
            types.SimpleNamespace(
                name=item.name,
                canonical_path="scripts/check-release-v092.py",
                source_sha256=item.source_sha256,
                module_object=item.module_object,
            )
            for item in members
        ]
        bad_graph = types.SimpleNamespace(
            members=tuple(bad_members),
            module=lambda name: next(item.module_object for item in bad_members if item.name == name),
        )
        self.provider.importlib = importlib
        self.codeql.importlib = importlib
        try:
            with self.assertRaisesRegex(ValueError, "route path differs"):
                with self.stage._stage_provider_scope(
                        ROOT, self.provider, modules, bad_graph,
                        stdlib_importlib=importlib):
                    self.codeql.load_frozen(ROOT)
        finally:
            self.provider.importlib = original_provider_importlib
            self.codeql.importlib = original_codeql_importlib
        self.assertIs(self.codeql._load_module, original_loader)

    def test_real_proxy_callbacks_restore_on_exception_and_second_entry(self):
        original_packet_validate = self.packet.validate_packet
        original_resource_validate = self.resource.validate_packet
        original_packet_bytes = self.packet._regular_bytes
        original_resource_bytes = self.resource._regular_bytes
        provider_observer = self._observer(
            self.provider, "_scoped_nested_ledger", "provider-nested",
            "v092_scoped_recovery_packet", "incoming_recovery", 1)
        codeql_observer = self._observer(
            self.codeql, "_scoped_resource_recovery_ledger", "codeql-resource",
            "v092_resource_recovery", "incoming_predecessor03", 0)
        for _ in range(2):
            with provider_observer:
                with self.provider._scoped_nested_ledger(ROOT, self.raw):
                    self._load_target(self.provider, "v092_scoped_recovery_packet",
                                      "scripts/v092_scoped_recovery.py", self.packet)
                    self.assertIsNot(self.packet.validate_packet, original_packet_validate)
                    self.packet.validate_packet = original_packet_validate
                self.assertIs(self.packet.validate_packet, original_packet_validate)
                self.assertIs(self.packet._regular_bytes, original_packet_bytes)
            with codeql_observer:
                with self.codeql._scoped_resource_recovery_ledger(self.raw):
                    self._load_target(self.codeql, "v092_resource_recovery",
                                      "scripts/v092_resource_recovery.py", self.resource)
                    self.assertIsNot(self.resource.validate_packet, original_resource_validate)
                    self.resource.validate_packet = original_resource_validate
                self.assertIs(self.resource.validate_packet, original_resource_validate)
                self.assertIs(self.resource._regular_bytes, original_resource_bytes)

    def test_foreign_helper_and_proxy_class_are_rejected(self):
        observer = self._observer(
            self.provider, "_scoped_nested_ledger", "provider-nested",
            "v092_scoped_recovery_packet", "incoming_recovery", 1)
        with self.assertRaisesRegex(ValueError, "observer state is invalid"):
            with observer:
                self.provider._scoped_nested_ledger = lambda *args, **kwargs: None
        self.assertIs(self.provider._scoped_nested_ledger, observer.helper)

    def test_reader_scope_rejects_known_but_wrong_raw_closure(self):
        """A known digest is insufficient when the invocation captured another raw."""
        wrong_raw = self.raw + b"\nknown-but-wrong\n"
        self.factory.bound_raw_sha256.add(hashlib.sha256(wrong_raw).hexdigest())
        helper = self.provider._scoped_nested_ledger
        generator = helper.__wrapped__
        previous_factory = self.provider.importlib.util.module_from_spec
        with self.provider._scoped_nested_ledger(ROOT, self.raw):
            installed_factory = self.provider.importlib.util.module_from_spec
            factory_cells = self.stage._stage_invocation_closure(installed_factory)
            wrapper = factory_cells["_NestedLoader"]
            raw_cells = dict(zip(wrapper.exec_module.__code__.co_freevars,
                                 wrapper.exec_module.__closure__))
            raw_cell = raw_cells["historical_raw"]
            ctypes.pythonapi.PyCell_Set(ctypes.py_object(raw_cell), ctypes.py_object(wrong_raw))
            try:
                with self.assertRaisesRegex(ValueError, "different raw ledger"):
                    self.factory.register_invocation(
                        route="provider-nested", owner=self.provider, helper=helper,
                        generator=generator, factory_function=installed_factory,
                        previous_factory=previous_factory, wrapper_class=None,
                        raw=self.raw, selector="v092_scoped_recovery_packet",
                        facade=self.provider.importlib)
            finally:
                ctypes.pythonapi.PyCell_Set(ctypes.py_object(raw_cell), ctypes.py_object(self.raw))

    def test_actual_executor_resource_path_reaches_both_real_reader_proxies(self):
        """Exercise the frozen executor import path with both real reader bodies.

        The resource packet is stopped at its validated-packet boundary, after
        the real executor has loaded it and after both repository context
        managers have installed and executed their local proxy loaders.  This
        keeps the regression import/read-only while proving the production
        call path rather than a generated caller frame or a shell validator.
        """
        executor = load("actual_executor_reader_chain", ROOT / "scripts/execute-release-v092.py")
        resource = load("actual_resource_reader_chain", ROOT / "scripts/v092_resource_recovery.py")
        packet = load("actual_packet_reader_chain", ROOT / "scripts/v092_scoped_recovery.py")
        policy = load("actual_policy_reader_chain", ROOT / self.stage.OLD_POLICY_PATH)

        def member(name, relative, module):
            return types.SimpleNamespace(
                name=name, canonical_path=relative,
                source_sha256=hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                module_object=module,
            )

        members = [
            member("incoming_recovery",
                   "reports/releases/v0.9.2/acquisition/codeql-terminal-history-04.py",
                   self.provider),
            member("incoming_predecessor03",
                   "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py",
                   self.codeql),
            member("incoming_nested_resource_recovery", "scripts/v092_resource_recovery.py", resource),
            member("incoming_nested_scoped_recovery", "scripts/v092_scoped_recovery.py", packet),
            member("nested_020_v092_scoped_recovery_packet", "scripts/v092_scoped_recovery.py", packet),
            member("nested_021_v092_resource_recovery", "scripts/v092_resource_recovery.py", resource),
            member("executor", "scripts/execute-release-v092.py", executor),
            member("policy_source", self.stage.OLD_POLICY_PATH, policy),
        ]
        graph = types.SimpleNamespace(
            members=tuple(members),
            module=lambda name: next(item.module_object for item in members if item.name == name),
        )
        factory = self.stage._StageImportFactory(
            ROOT, graph, importlib, policy_path=self.stage.OLD_POLICY_PATH, policy=policy)
        factory.bound_raw_sha256.add(hashlib.sha256(self.raw).hexdigest())
        facade = factory.facade()
        saved_importlib = {
            module: getattr(module, "importlib", importlib)
            for module in (self.provider, self.codeql, executor, resource, packet)
        }
        seen_routes = []
        original_validate = resource.validate_packet

        def stop_after_real_reader_proxies(*args, **kwargs):
            with self.provider._scoped_nested_ledger(ROOT, self.raw):
                spec = self.provider.importlib.util.spec_from_file_location(
                    "v092_scoped_recovery_packet", ROOT / "scripts/v092_scoped_recovery.py")
                target = self.provider.importlib.util.module_from_spec(spec)
                spec.loader.exec_module(target)
                seen_routes.append("provider-nested")
            with self.codeql._scoped_resource_recovery_ledger(self.raw):
                spec = self.codeql.importlib.util.spec_from_file_location(
                    "v092_resource_recovery", ROOT / "scripts/v092_resource_recovery.py")
                target = self.codeql.importlib.util.module_from_spec(spec)
                spec.loader.exec_module(target)
                seen_routes.append("codeql-resource")
            raise RuntimeError("downstream resource evidence sentinel")

        for module in saved_importlib:
            module.importlib = facade
        resource.validate_packet = stop_after_real_reader_proxies
        provider_observer = self.stage._stage_observe_context(
            factory, self.provider, "_scoped_nested_ledger", "provider-nested",
            "v092_scoped_recovery_packet",
            hashlib.sha256((ROOT / "reports/releases/v0.9.2/acquisition/codeql-terminal-history-04.py").read_bytes()).hexdigest(),
            1)
        codeql_observer = self.stage._stage_observe_context(
            factory, self.codeql, "_scoped_resource_recovery_ledger", "codeql-resource",
            "v092_resource_recovery",
            hashlib.sha256((ROOT / "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py").read_bytes()).hexdigest(),
            0)
        try:
            with provider_observer:
                with codeql_observer:
                    with self.assertRaisesRegex(RuntimeError, "downstream resource evidence sentinel"):
                        executor._validate_resource_recovery({
                            "repo_root": ROOT,
                            "plan": {"resource_recovery": {}},
                        })
            self.assertEqual(seen_routes, ["provider-nested", "codeql-resource"])
        finally:
            resource.validate_packet = original_validate
            for module, previous in saved_importlib.items():
                module.importlib = previous

    def test_create_parent_stage_enters_real_nested_recovery_chain_before_io_sentinel(self):
        """Drive the real parent/stage/provider/CodeQL/executor chain once.

        The test uses the sealed replacement-16 identity and the current
        graph, but creates a temporary successor-shaped source-design object
        solely to cross replacement-17's reviewed source-design dispatch
        boundary.  It does not use that object as qualification evidence.
        The immutable source-snapshot guard is isolated because this checkout
        intentionally contains the uncommitted successor sources under test.
        The only downstream stop is ``validate_packet`` after the real
        resource and scoped packet reader proxies have been entered.
        """
        import copy

        bridge = load("bridge15_real_nested_parent_test",
                      BASE / "bifrost-v0140-frozen-bridge-15.py")
        stage = load("stage_runtime_real_nested_parent_test", SOURCE)
        manifest_path = ROOT / "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-16/manifest-identity.json"
        core = json.loads(manifest_path.read_bytes())
        raw_graph = dict(core["runtime_module_graph"])
        successor_files = {
            "admission20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-20.py",
            "bridge15": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-15.py",
            "host_admission20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-20.py",
            "host_bridge15": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-15.py",
            "host_protocol20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
            "host_supervisor20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-20.py",
            "protocol20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
            "policy_source": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
            "policy_runtime": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
            "replacement20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
            "runtime_loaders20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-runtime-loaders-20.py",
            "stage_runtime07": "reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-07.py",
            "supervisor20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-20.py",
        }
        predecessor_names = {
            "admission16": "admission20", "bridge11": "bridge15",
            "host_admission16": "host_admission20", "host_bridge11": "host_bridge15",
            "host_protocol16": "host_protocol20", "host_supervisor16": "host_supervisor20",
            "protocol16": "protocol20", "replacement16": "replacement20",
            "runtime_loaders16": "runtime_loaders20", "stage_runtime03": "stage_runtime07",
            "supervisor16": "supervisor20",
        }
        graph_refs = {name: ref for name, ref in raw_graph.items()
                      if name not in predecessor_names}
        for old_name, new_name in predecessor_names.items():
            self.assertNotIn(new_name, graph_refs)
            self.assertIn(old_name, raw_graph)
            graph_refs[new_name] = raw_graph[old_name]
        for name, relative in successor_files.items():
            path = ROOT / relative
            graph_refs[name] = {"path": relative, "sha256": p.sha256(path.read_bytes())}
        required = tuple(bridge.REQUIRED_GRAPH_NAMES)
        graph_refs = {name: graph_refs[name] for name in required} | {
            name: graph_refs[name] for name in sorted(set(graph_refs) - set(required))
        }
        graph = bridge.prepare_graph(
            ROOT, graph_refs, host_modules={"bridge15": bridge, "stage_runtime07": stage})
        self.assertEqual(len(graph.members), 88)

        source_design_dir = ROOT / "reports/releases/v0.9.2/qualification/independent-pending-groups-01"
        source_design_path13 = source_design_dir / "bifrost-source-design-14.json"
        source_design = json.loads(source_design_path13.read_bytes())
        source_design["predecessor_design"] = {
            "path": "reports/releases/v0.9.2/qualification/independent-pending-groups-01/bifrost-source-design-14.json",
            "sha256": p.sha256(source_design_path13.read_bytes()),
        }
        # Each check owns a fresh temporary fixture; never overwrite evidence
        # left by a separate or interrupted check.
        with tempfile.NamedTemporaryFile(
                dir=source_design_dir, prefix=".stage04-test-source-design-",
                suffix=".json", delete=False) as source_design_file:
            source_design_file.write(p.canonical_json(source_design))
            source_design_path = Path(source_design_file.name)
        source_design_ref = {
            "path": str(source_design_path.relative_to(ROOT)),
            "sha256": p.sha256(source_design_path.read_bytes()),
        }
        core["runtime_module_graph"] = graph_refs
        core["source_design"] = source_design_ref
        core["manifest_ref"] = {
            "path": core["manifest_path"],
            "sha256": p.sha256((ROOT / core["manifest_path"]).read_bytes()),
        }
        ledger_path = ROOT / "reports/releases/v0.9.2/qualification/independent-pending-groups-01/sealed-ledger-prefix-89.jsonl"
        ledger_raw = ledger_path.read_bytes()
        ledger_ref = {
            "path": str(ledger_path.relative_to(ROOT)),
            "sha256": p.sha256(ledger_raw),
            "rows": len(ledger_raw.splitlines()),
        }
        modules = {member.name: member.module_object for member in graph.members}
        policy = modules["policy_source"]
        executor = modules["executor"]
        resource = modules["nested_021_v092_resource_recovery"]
        packet = modules["nested_020_v092_scoped_recovery_packet"]
        policy_attr = next((name for name in ("SOURCE_DESIGN_15_PATH", "SOURCE_DESIGN_14_PATH", "SOURCE_DESIGN_12_PATH")
                            if hasattr(policy, name)), None)
        self.assertIsNotNone(policy_attr)
        original_policy_path = getattr(policy, policy_attr)
        original_snapshot = executor._assert_source_snapshot
        original_contract_snapshot = getattr(executor, "_assert_contract_snapshot", None)
        original_stage_git = stage._git
        original_resource_validate = resource.validate_packet
        original_packet_validate = packet.validate_packet
        seen: list[tuple[str, frozenset[str]]] = []

        def active_routes() -> frozenset[str]:
            factory = stage._ACTIVE_STAGE_FACTORY
            self.assertIsNotNone(factory)
            routes = {
                record.decorator_binding.route
                for record in factory.records
                if record.decorator_binding is not None
            }
            return frozenset(routes)

        def resource_validate(*args, **kwargs):
            routes = active_routes()
            self.assertEqual(routes, frozenset({"codeql-resource"}))
            seen.append(("resource", routes))
            return original_resource_validate(*args, **kwargs)

        def packet_validate(*args, **kwargs):
            routes = active_routes()
            self.assertEqual(routes, frozenset({"provider-nested", "codeql-resource"}))
            seen.append(("packet", routes))
            raise RuntimeError("downstream nested-reader sentinel")

        setattr(policy, policy_attr, source_design_ref["path"])
        executor._assert_source_snapshot = lambda *args, **kwargs: None
        stage._git = lambda root, *args, **kwargs: (core["plan_commit"]
            if args == ("rev-parse", "HEAD") else original_stage_git(root, *args, **kwargs))
        if original_contract_snapshot is not None:
            executor._assert_contract_snapshot = lambda *args, **kwargs: None
        resource.validate_packet = resource_validate
        packet.validate_packet = packet_validate
        try:
            lock = bridge.LockIdentity("/tmp/bf17-stage-test.lock", 1, 2, 123, "test-birth")
            with self.assertRaisesRegex(stage.FrozenBridgeError,
                                        "frozen executor rejected canonical contract"):
                bridge.create_parent_stage(
                    ROOT, core, core["manifest_ref"], 0, lock, ledger_ref,
                    graph=graph, mode="before")
            self.assertEqual([name for name, _ in seen], ["resource", "packet"])
            self.assertEqual(seen, [
                ("resource", frozenset({"codeql-resource"})),
                ("packet", frozenset({"provider-nested", "codeql-resource"})),
            ])
            self.assertIsNone(stage._ACTIVE_STAGE_FACTORY)
        finally:
            setattr(policy, policy_attr, original_policy_path)
            executor._assert_source_snapshot = original_snapshot
            stage._git = original_stage_git
            if original_contract_snapshot is not None:
                executor._assert_contract_snapshot = original_contract_snapshot
            resource.validate_packet = original_resource_validate
            packet.validate_packet = original_packet_validate
            source_design_path.unlink(missing_ok=True)

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
        replacement = types.ModuleType("fixture_replacement20")
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
        names = ("bridge15", "replacement20", "executor", "checker", "configuration",
                 "incoming_recovery", "policy_source", "policy_runtime", "protocol20",
                 "admission20", "supervisor20")
        for name, module in {
            "replacement20": replacement, "executor": executor, "checker": checker,
            "configuration": configuration, "incoming_recovery": incoming,
            "policy_source": types.ModuleType("fixture_policy_source"),
            "policy_runtime": types.ModuleType("fixture_policy_runtime"),
            "protocol20": types.ModuleType("fixture_protocol20"),
            "admission20": types.ModuleType("fixture_admission20"),
            "supervisor20": types.ModuleType("fixture_supervisor20"),
            "bridge15": types.ModuleType("fixture_bridge15"),
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
        stage = load("stage_runtime_graph_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        value = stage.load_runtime_context(self.root, self.core, graph=self.graph)
        self.assertEqual(value["schema"], "v092-bifrost-v0140-runtime-context/v1")
        self.assertTrue(value["lossless_runtime_objects"])
        self.assertIs(value["modules"]["replacement05"], self.modules["replacement20"])
        self.assertIs(value["modules"]["executor"], self.modules["executor"])
        self.assertIs(value["mixed_context"]["executor"], self.modules["executor"])
        self.assertRegex(value["bridge_context"]["context_digest"], r"^[0-9a-f]{64}$")

    def test_provider_foreign_module_is_rejected(self):
        stage = load("stage_runtime_foreign_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        foreign = types.ModuleType("foreign_executor")
        original = self.modules["incoming_recovery"].load_runtime_context
        self.modules["incoming_recovery"].load_runtime_context = lambda **kwargs: {
            **original(**kwargs), "modules": {"replacement05": self.modules["replacement20"],
                                               "executor": foreign, "checker": self.modules["checker"],
                                               "configuration": self.modules["configuration"]}}
        try:
            with self.assertRaisesRegex(ValueError, "foreign executor"):
                stage.load_runtime_context(self.root, self.core, graph=self.graph)
        finally:
            self.modules["incoming_recovery"].load_runtime_context = original

    def test_transitive_closure_wrong_digest_and_symlink_fail_closed(self):
        stage = load("stage_runtime_closure_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        path = self.root / "nested.py"
        path.write_bytes(b"nested")
        self.core["runtime_graph_closure"] = [{"name": "nested", "path": "nested.py", "sha256": "0" * 64}]
        with self.assertRaisesRegex(ValueError, "digest changed"):
            stage.load_runtime_context(self.root, self.core, graph=self.graph)
        self.core["runtime_graph_closure"] = [{"name": "nested", "path": "../nested.py", "sha256": p.sha256(b"nested")}]
        with self.assertRaisesRegex(ValueError, "unsafe"):
            stage.load_runtime_context(self.root, self.core, graph=self.graph)

    def test_production_closure_rejects_reordered_complete_named_members(self):
        stage = load("stage_runtime_ordered_closure_test", BASE / "bifrost-v0140-stage-runtime-07.py")
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
        stage = load("stage_runtime_named_loader_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        path = self.root / "nested.py"
        raw = b"nested-source"
        path.write_bytes(raw)
        first = types.SimpleNamespace(name="nested_first", canonical_path="nested.py",
                                      source_sha256=p.sha256(raw), module_object=types.ModuleType("nested_first"))
        second = types.SimpleNamespace(name="nested_second", canonical_path="nested.py",
                                       source_sha256=p.sha256(raw), module_object=types.ModuleType("nested_second"))
        policy_member = types.SimpleNamespace(name="policy_source", canonical_path="policy.py",
                                              source_sha256="2" * 64, module_object=types.ModuleType("policy"))
        members = (first, second, policy_member)
        graph = types.SimpleNamespace(members=members, module=lambda name: next(item.module_object for item in members if item.name == name))
        facade = stage._stage_pinned_importlib(self.root.resolve(), graph, stage.importlib, stdlib_importlib=importlib)
        spec = facade.util.spec_from_file_location("nested_second", path)
        self.assertIs(facade.util.module_from_spec(spec), second.module_object)
        with self.assertRaisesRegex(ValueError, "explicitly bound"):
            facade.util.spec_from_file_location("unregistered_nested", path)

    def test_scoped_loader_checks_historical_policy_sha_before_policy14_proxy(self):
        stage = load("stage_runtime_policy_route_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement20"]
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
                                           mode="before", ledger_bytes=None, stdlib_importlib=importlib):
            with self.assertRaisesRegex(ValueError, "historical source digest"):
                stage._load_module(self.root, "source_design04_policy",
                                   {"path": stage.OLD_POLICY_PATH, "sha256": "0" * 64})
            loaded = stage._load_module(
                self.root, "source_design04_policy",
                {"path": stage.OLD_POLICY_PATH, "sha256": stage.OLD_POLICY_SHA256})
            self.assertIs(loaded, policy)

    def test_bridge15_dispatches_graph_owned_stage_runtime(self):
        bridge = load("bridge15_stage_dispatch_test", BASE / "bifrost-v0140-frozen-bridge-15.py")
        stage = load("stage_runtime_bridge_member_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        names = ("bridge15", "replacement20", "executor", "checker", "configuration",
                 "incoming_recovery", "policy_source", "policy_runtime", "protocol20",
                 "admission20", "supervisor20", "stage_runtime07")
        modules = dict(self.modules)
        modules["bridge15"] = bridge
        modules["stage_runtime07"] = stage
        modules["protocol20"].validate_static = lambda root, path: {
            "manifest": {"schema": "fixture-manifest"}, "core": self.core}
        modules["incoming_recovery"].load_runtime_context = lambda **kwargs: {
            "modules": {"replacement05": modules["replacement20"],
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
        self.assertIs(value.objects["modules"]["replacement05"], modules["replacement20"])
        self.assertEqual(value.objects["schema"], "v092-bifrost-v0140-runtime-context/v1")

    def test_actual_stage_entrypoint_pairs_policy_and_late_provider_loaders(self):
        """Run the copied full entrypoint with downstream validation I/O stubbed.

        This intentionally stops inside the copied legacy body after its
        policy and late-loader boundaries.  It therefore exercises the real
        ``load_runtime_context -> _stage_build_runtime_full`` call chain,
        rather than only testing a generated facade or a direct helper call.
        """
        stage = load("stage_runtime_actual_entrypoint_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        modules, graph = runtime_scope_fixture(stage)
        # The copied full entrypoint requires the BF16 host-role names in
        # addition to the retained replacement05 runtime member.  These are
        # explicit aliases to the already loaded objects, never fresh imports.
        modules["bridge15"] = stage
        modules["replacement20"] = modules["replacement05"]
        graph.members.extend([
            types.SimpleNamespace(name="bridge15", module_object=stage,
                                  canonical_path="reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-07.py",
                                  source_sha256=p.sha256((ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-07.py").read_bytes())),
            types.SimpleNamespace(name="replacement20", module_object=modules["replacement05"],
                                  canonical_path="reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
                                  source_sha256=p.sha256((ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py").read_bytes())),
        ])
        replacement = modules["replacement05"]
        incoming = modules["incoming_recovery"]
        checker = modules["checker"]
        nested = modules["nested_018_v092_resource_recovery_for_checker"]
        nested.importlib = importlib
        nested_path = self.root / "scripts/v092_resource_recovery.py"
        nested_path.parent.mkdir(parents=True, exist_ok=True)
        nested_path.write_bytes((ROOT / "scripts/v092_resource_recovery.py").read_bytes())
        nested.__file__ = str(nested_path)
        policy_path = self.root / stage.OLD_POLICY_PATH
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_bytes((ROOT / stage.OLD_POLICY_PATH).read_bytes())
        observed = []

        def provider_loader(**kwargs):
            observed.append("provider")
            late_spec = checker.importlib.util.spec_from_file_location(
                "v092_resource_recovery_for_checker", nested_path)
            self.assertIs(checker.importlib.util.module_from_spec(late_spec), nested)
            late_spec.loader.exec_module(nested)
            return {"modules": {"replacement05": replacement, "executor": modules["executor"],
                                 "checker": checker, "configuration": modules["configuration"]},
                    "validated": {"plan": {}},
                    "mixed_context": {"validated": {"plan": {}}},
                    "checker_summary": {"status": "fixture"},
                    "configuration_summary": {"status": "fixture"},
                    "bridge_context": {"context_digest": "a" * 64}}

        incoming.load_runtime_context = provider_loader
        original_legacy = stage._STAGE_LEGACY_LOAD_RUNTIME_CONTEXT
        original_closure = stage._stage_closure

        def copied_legacy(root, core, *, mode="before", ledger_bytes=None, fixture_only=False):
            self.assertFalse(fixture_only)
            policy_spec = stage.importlib.util.spec_from_file_location(
                "bridge03_window_policy", policy_path)
            policy = stage.importlib.util.module_from_spec(policy_spec)
            policy_spec.loader.exec_module(policy)
            policy.validate_execution_window(root, core)
            policy.validate_source_design(root, core)
            provided = stage._stage_incoming_pinned(
                incoming, root, core, graph,
                {"replacement05": replacement, "executor": modules["executor"],
                 "checker": checker, "configuration": modules["configuration"]},
                mode, ledger_bytes, stdlib_importlib=importlib)
            observed.append("copied-load-and-validate")
            validated = {"plan": {}, "bytes_sha256": "b" * 64}
            return {"modules": provided["modules"], "validated": validated,
                    "mixed_context": {"validated": validated},
                    "checker_summary": provided["checker_summary"],
                    "configuration_summary": provided["configuration_summary"],
                    "bridge_context": {"validated_full_normalized_plan": validated,
                                        "context_digest": "c" * 64}}

        with mock.patch.object(stage, "_STAGE_LEGACY_LOAD_RUNTIME_CONTEXT", copied_legacy), \
             mock.patch.object(stage, "_stage_closure", return_value=[]):
            value = stage.load_runtime_context(
                self.root, self.core, graph=graph, mode="before",
                stdlib_importlib=importlib)
        self.assertEqual(observed, ["provider", "copied-load-and-validate"])
        self.assertIs(value["modules"]["executor"], modules["executor"])
        self.assertIs(checker.importlib, importlib)
        self.assertIs(incoming.importlib, importlib)
        self.assertIs(nested.importlib, importlib)
        self.assertIs(stage._STAGE_LEGACY_LOAD_RUNTIME_CONTEXT, original_legacy)
        self.assertIs(stage._stage_closure, original_closure)

    def test_create_parent_reaches_real_copied_body_policy_factory(self):
        """Stop real production-dispatch bodies at downstream Git evidence I/O.

        Module shells stand in for downstream policy validation, not for any
        runtime loader/validator body. This is a synthetic composition test;
        it creates no qualified runtime, successful stage, or replay proof.
        """
        import inspect
        stage = load("stage_runtime_real_copied_body_test", SOURCE)
        bridge = load("bridge15_real_copied_body_test", BASE / "bifrost-v0140-frozen-bridge-15.py")
        modules, graph = runtime_scope_fixture(stage)
        modules["bridge15"] = bridge
        modules["replacement20"] = modules["replacement05"]
        for name, relative in (
            ("bridge15", "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-15.py"),
            ("replacement20", "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py"),
        ):
            member = Member(name, relative)
            member.module_object = modules[name]
            graph.members.append(member)
        by_name = {member.name: member for member in graph.members}
        names = bridge.REQUIRED_GRAPH_NAMES + tuple(sorted(set(by_name) - set(bridge.REQUIRED_GRAPH_NAMES)))
        graph = bridge.PinnedBridgeGraph(tuple(bridge.GraphMember(
            member.name, member.canonical_path, member.source_sha256,
            member.module_object, "synthetic:" + member.name) for member in (by_name[name] for name in names)),
            fixture_only=False)  # exercise _stage_build_runtime_full
        historical_path = self.root / stage.OLD_POLICY_PATH
        historical_path.parent.mkdir(parents=True, exist_ok=True)
        historical_raw = (ROOT / stage.OLD_POLICY_PATH).read_bytes()
        historical_path.write_bytes(historical_raw)
        core = dict(self.core)
        core.update({
            "runtime_module_graph": {member.name: {
                "path": member.canonical_path, "sha256": member.source_sha256
            } for member in graph.members},
            "continuation": {"schema": "v092-bifrost-v0140-continuation-context/v1",
                "contract": core["contract"], "source_commit": "a" * 40,
                "plan_commit": "b" * 40, "source_inputs": []},
            "source_evidence": {}, "source_contexts": [],
        })
        ledger_raw = self.ledger_path.read_bytes()
        ledger_ref = {"path": core["ledger_path"], "sha256": p.sha256(ledger_raw),
                      "rows": len(ledger_raw.splitlines())}
        policy = modules["policy_source"]
        observed = []
        factory_records = []
        legacy_runtime = stage._STAGE_LEGACY_LOAD_RUNTIME_CONTEXT
        legacy_validator = stage._STAGE_LEGACY_LOAD_AND_VALIDATE
        # Match production's pre-existing graph-local facade. Its context
        # cannot be used: the corrected pair must use host-captured stdlib
        # primitives instead. Prove the original mixed-spec defect is live.
        forbidden_context = mock.Mock(name="unreachable_graph_import_context")
        stage.importlib = bridge._GraphImportlibFacade(forbidden_context, "stage_runtime07")
        original_importlib = stage.importlib
        detached_spec = importlib.util.spec_from_file_location("bridge03_window_policy", historical_path)
        with self.assertRaisesRegex(ValueError, "foreign graph import spec"):
            original_importlib.util.module_from_spec(detached_spec)
        forbidden_context.assert_not_called()
        required_bodies = {
            bridge.create_parent_stage.__code__, bridge._load_bound_ledger_runtime.__code__,
            bridge.load_stage_runtime.__code__, bridge.load_runtime_stage.__code__,
            bridge.load_runtime_context.__code__, bridge._graph_runtime_context.__code__,
            stage.load_runtime_context.__code__, stage._stage_build_runtime_full.__code__,
            legacy_runtime.__code__, legacy_validator.__code__,
        }

        def policy_check(label):
            def check(root, actual_core):
                self.assertEqual(root, self.root.resolve())
                self.assertIs(actual_core, core)
                factory = stage._ACTIVE_STAGE_FACTORY
                self.assertIs(factory.policy, policy)
                self.assertIs(factory.stdlib, bridge.HOST_STDLIB_IMPORTLIB)
                self.assertEqual(len(factory.records), 1)
                record = factory.records[0]
                self.assertEqual(record.kind, "historical-policy")
                self.assertIs(record.target, policy)
                self.assertIs(record.spec.loader.source, policy)
                self.assertIs(factory.module_from_spec(record.spec), policy)
                factory_records.append(record)
                observed.append(label)
            return check

        for name in ("validate_execution_window", "validate_working_cap",
                     "validate_breadth_first_authority", "_validate_historical_prefixes"):
            setattr(policy, name, policy_check(name))

        class DownstreamEvidenceRead(Exception):
            pass

        def stop_at_git(root, left, right, label):
            self.assertEqual((left, right, label), ("a" * 40, "b" * 40, "source to plan"))
            actual_codes = {frame.frame.f_code for frame in inspect.stack()}
            self.assertTrue(required_bodies <= actual_codes,
                            "the real parent/runtime/copied-validator call chain was not reached")
            observed.append("downstream-git-evidence")
            raise DownstreamEvidenceRead()

        # __file__ locates the immutable historical policy in this isolated
        # checkout. No function body, factory pair, proxy, or loader is replaced.
        with mock.patch.object(stage, "__file__", str(self.root / SOURCE.relative_to(ROOT))), \
             mock.patch.object(stage, "_ancestor", side_effect=stop_at_git) as ancestry:
            with self.assertRaises(DownstreamEvidenceRead):
                bridge.create_parent_stage(self.root, core, core["manifest_ref"], 0,
                                           None, ledger_ref, graph=graph)
            self.assertEqual(ancestry.call_count, 1)
            self.assertEqual(observed, ["validate_execution_window", "validate_working_cap",
                "validate_breadth_first_authority", "_validate_historical_prefixes",
                "downstream-git-evidence"])
            self.assertEqual(len({id(record) for record in factory_records}), 1)
            # The identical real call chain rejects altered historical bytes
            # before exposing the graph policy or reaching evidence I/O.
            observed.clear()
            historical_path.write_bytes(historical_raw + b"\n# foreign source\n")
            with self.assertRaisesRegex(ValueError, "historical policy source changed"):
                bridge.create_parent_stage(self.root, core, core["manifest_ref"], 0,
                                           None, ledger_ref, graph=graph)
            self.assertEqual(observed, [])
            self.assertEqual(ancestry.call_count, 1)
        self.assertIs(stage._STAGE_LEGACY_LOAD_RUNTIME_CONTEXT, legacy_runtime)
        self.assertIs(stage._STAGE_LEGACY_LOAD_AND_VALIDATE, legacy_validator)
        self.assertIs(stage.importlib, original_importlib)
        self.assertEqual(forbidden_context.mock_calls, [])
        self.assertIs(modules["checker"].importlib, importlib)
        self.assertFalse(hasattr(modules["checker"], "EXECUTOR"))

    def test_full_scope_uses_local_importlib_facade_and_positional_root_loader(self):
        stage = load("stage_runtime_scope_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement20"]
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
                                           ledger_bytes=None, stdlib_importlib=importlib):
            self.assertIsNot(stage.importlib, original_importlib)
            self.assertIsNot(stage.importlib.util, original_util)
            loaded = stage.load_dependencies(self.root)
            self.assertIs(loaded["replacement05"], modules["replacement05"])
        self.assertIs(stage.importlib, original_importlib)
        self.assertIs(stage.importlib.util, original_util)

    def test_full_scope_routes_late_checker_recovery_loader_and_restores_it(self):
        stage = load("stage_runtime_late_checker_loader_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement20"]
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
        resource.__file__ = str(nested_path)
        modules["incoming_nested_resource_recovery"] = resource
        modules["stage_runtime07"] = stage
        modules["nested_018_v092_resource_recovery_for_checker"] = resource
        names = tuple(self.modules) + ("replacement05", "incoming_nested_resource_recovery", "nested_018_v092_resource_recovery_for_checker", "stage_runtime07")
        members = [types.SimpleNamespace(name=name, module_object=modules[name],
                                         canonical_path=("fixture/incoming_nested_resource_recovery.py"
                                                         if name in {"incoming_nested_resource_recovery", "nested_018_v092_resource_recovery_for_checker"}
                                                         else f"fixture/{name}.py"),
                                         source_sha256=(p.sha256(nested_raw)
                                                        if name in {"incoming_nested_resource_recovery", "nested_018_v092_resource_recovery_for_checker"}
                                                        else "2" * 64))
                   for name in names]
        graph = types.SimpleNamespace(members=tuple(members), graph_sha256="4" * 64,
                                      fixture_only=False, module=lambda name: modules[name])
        with stage._stage_full_graph_scope(self.root, self.core, graph, modules,
                                           mode="before", ledger_bytes=None, stdlib_importlib=importlib):
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
        stage = load("stage_runtime_provider_alias_test", BASE / "bifrost-v0140-stage-runtime-07.py")
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
        stage = load("stage_runtime_provider_named_loader_test", BASE / "bifrost-v0140-stage-runtime-07.py")
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
        stage = load("stage_runtime_full_alias_test", BASE / "bifrost-v0140-stage-runtime-07.py")
        policy = self.modules["policy_source"]
        policy.validate_execution_window = lambda root, core: None
        policy.validate_source_design = lambda root, core: None
        modules = dict(self.modules)
        modules["replacement05"] = modules["replacement20"]
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
                                           mode="before", ledger_bytes=None, stdlib_importlib=importlib):
            self.assertIs(modules["checker"].EXECUTOR, modules["executor"])
            self.assertIs(modules["configuration"].CHECKER, modules["checker"])
            self.assertIs(modules["configuration"].EXECUTOR, modules["executor"])
        self.assertIs(modules["checker"].EXECUTOR, foreign_executor)
        self.assertIs(modules["configuration"].CHECKER, foreign_checker)
        self.assertIs(modules["configuration"].EXECUTOR, foreign_executor)




class Member:
    def __init__(self, name: str, relative: str):
        self.name = name
        self.canonical_path = relative
        self.source_sha256 = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        self.module_object = types.ModuleType(name)
        self.module_object.__file__ = str(ROOT / relative)


class Graph:
    def __init__(self, *members):
        self.members = list(members)

    def module(self, name):
        return next(member.module_object for member in self.members if member.name == name)


def runtime_scope_fixture(stage):
    """Build a real-root graph of source-backed objects for scope probes.

    The objects are harmless module shells; the scope itself is the actual
    copied-validator loader boundary. No validator, replay, or analyzer runs.
    """
    paths = {
        "replacement05": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py",
        "executor": "scripts/execute-release-v092.py",
        "checker": "scripts/check-release-v092.py",
        "configuration": "scripts/check-release-v092.py",
        "incoming_recovery": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py",
        "policy_source": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
        "policy_runtime": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
        "protocol20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-20.py",
        "admission20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-20.py",
        "supervisor20": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-20.py",
        "stage_runtime07": "reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-07.py",
        "disk_guard": "scripts/v092_disk_guard.py",
        "incoming_nested_resource_recovery": "scripts/v092_resource_recovery.py",
        "nested_018_v092_resource_recovery_for_checker": "scripts/v092_resource_recovery.py",
    }
    modules = {}
    members = []
    for name, relative in paths.items():
        module = stage if name == "stage_runtime07" else types.ModuleType("scope_" + name)
        module.__file__ = str(ROOT / relative)
        if name in {"checker", "configuration", "incoming_recovery"}:
            module.importlib = importlib
        if name == "policy_source":
            module.validate_execution_window = lambda root, core: None
            module.validate_source_design = lambda root, core: None
        modules[name] = module
        members.append(Member(name, relative))
        members[-1].module_object = module
    return modules, Graph(*members)



class StageRuntime03FactoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = load_source(SOURCE, "stage_runtime07_test_module")
        cls.policy_path = "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py"

    def factory(self):
        executor = Member("executor", "scripts/execute-release-v092.py")
        policy = Member("policy_source", self.policy_path)
        graph = Graph(executor, policy)
        factory = self.stage._StageImportFactory(
            ROOT, graph, importlib, policy_path=self.policy_path,
            policy=policy.module_object,
        )
        return factory, executor, policy

    def test_graph_and_historical_policy_use_paired_stdlib_factory(self):
        factory, executor, policy = self.factory()
        graph_spec = factory.spec_from_file_location(
            "executor", ROOT / executor.canonical_path,
        )
        self.assertIs(factory.module_from_spec(graph_spec), executor.module_object)
        graph_spec.loader.exec_module(executor.module_object)
        policy_spec = factory.spec_from_file_location(
            "bridge03_window_policy", ROOT / self.policy_path,
        )
        self.assertIs(factory.module_from_spec(policy_spec), policy.module_object)
        policy_spec.loader.exec_module(policy.module_object)
        self.assertIs(policy_spec.loader.source, policy.module_object)

    def test_metadata_and_identity_are_restored_after_module_from_spec(self):
        factory, executor, _ = self.factory()
        sentinel = object()
        executor.module_object.__spec__ = sentinel
        executor.module_object.__loader__ = sentinel
        spec = factory.spec_from_file_location("executor", ROOT / executor.canonical_path)
        self.assertIs(factory.module_from_spec(spec), executor.module_object)
        self.assertIs(executor.module_object.__spec__, sentinel)
        self.assertIs(executor.module_object.__loader__, sentinel)

    def test_detached_standard_spec_is_rejected(self):
        factory, executor, _ = self.factory()
        registered = factory.spec_from_file_location("executor", ROOT / executor.canonical_path)
        detached = importlib.util.spec_from_file_location(
            "executor", ROOT / executor.canonical_path, loader=registered.loader,
        )
        with self.assertRaises(self.stage.FrozenBridgeError):
            factory.module_from_spec(detached)

    def test_cross_factory_spec_is_rejected(self):
        first, executor, _ = self.factory()
        second, _, _ = self.factory()
        spec = first.spec_from_file_location("executor", ROOT / executor.canonical_path)
        with self.assertRaises(self.stage.FrozenBridgeError):
            second.module_from_spec(spec)

    def test_graph_facade_spec_is_rejected_by_stage_factory(self):
        factory, executor, _ = self.factory()
        foreign = types.SimpleNamespace(_context=object(), target_role="executor")
        with self.assertRaises(self.stage.FrozenBridgeError):
            factory.module_from_spec(foreign)

    def test_wrong_policy_selector_and_path_fail_closed(self):
        factory, _, _ = self.factory()
        with self.assertRaises(self.stage.FrozenBridgeError):
            factory.spec_from_file_location("unreviewed_policy", ROOT / self.policy_path)
        with self.assertRaises(self.stage.FrozenBridgeError):
            factory.spec_from_file_location(
                "bridge03_window_policy", ROOT / "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py",
            )

    def test_no_reexecution_policy_loader_preserves_object(self):
        factory, _, policy = self.factory()
        policy.module_object.marker = object()
        spec = factory.spec_from_file_location("bridge03_window_policy", ROOT / self.policy_path)
        candidate = factory.module_from_spec(spec)
        spec.loader.exec_module(candidate)
        self.assertIs(candidate, policy.module_object)
        self.assertIs(candidate.marker, policy.module_object.marker)

    def test_six_late_routes_keep_distinct_same_path_graph_objects(self):
        routes = (
            ("v092_resource_recovery_for_checker", "nested_018_v092_resource_recovery_for_checker", "scripts/v092_resource_recovery.py"),
            ("v092_scoped_recovery_for_checker", "nested_019_v092_scoped_recovery_for_checker", "scripts/v092_scoped_recovery.py"),
            ("v092_scoped_recovery_packet", "nested_020_v092_scoped_recovery_packet", "scripts/v092_scoped_recovery.py"),
            ("v092_resource_recovery", "nested_021_v092_resource_recovery", "scripts/v092_resource_recovery.py"),
            ("check_release_v092_scoped_replay", "nested_022_check_release_v092_scoped_replay", "scripts/check-release-v092.py"),
            ("check_release_v092_resource_replay", "nested_023_check_release_v092_resource_replay", "scripts/check-release-v092.py"),
        )
        members = [Member(role, path) for _, role, path in routes]
        # Earlier aliases share both file and hash but remain foreign objects.
        aliases = [Member("same_path_alias_" + str(i), path)
                   for i, (_, _, path) in enumerate(routes)]
        graph = Graph(*(aliases + members))
        policy = types.ModuleType("six_route_policy")
        factory = self.stage._StageImportFactory(
            ROOT, graph, importlib, policy_path=self.policy_path, policy=policy)
        for i, (selector, role, path) in enumerate(routes):
            with self.subTest(selector=selector):
                target = graph.module(role)
                spec = factory.spec_from_file_location(selector, ROOT / path)
                self.assertIs(factory.module_from_spec(spec), target)
                self.assertIsNot(target, aliases[i].module_object)
                spec.loader.exec_module(target)
                with self.assertRaises(ValueError):
                    spec.loader.exec_module(aliases[i].module_object)
                with self.assertRaises(ValueError):
                    factory.spec_from_file_location(selector, ROOT / "scripts/v092_disk_guard.py")
        with self.assertRaises(ValueError):
            factory.spec_from_file_location("unregistered_same_path", ROOT / routes[0][2])

    def test_actual_scope_pairs_policy_and_late_resource_loader(self):
        modules, graph = runtime_scope_fixture(self.stage)
        checker = modules["checker"]
        original_checker_importlib = checker.importlib
        nested = modules["nested_018_v092_resource_recovery_for_checker"]
        nested_path = ROOT / nested.__file__.replace(str(ROOT) + "/", "")
        with self.stage._stage_full_graph_scope(
                ROOT, {}, graph, modules, mode="before", ledger_bytes=None,
                stdlib_importlib=importlib):
            policy_spec = self.stage.importlib.util.spec_from_file_location(
                "bridge03_window_policy", ROOT / self.stage.OLD_POLICY_PATH)
            self.assertIs(self.stage.importlib.util.module_from_spec(policy_spec),
                          modules["policy_source"])
            late_spec = checker.importlib.util.spec_from_file_location(
                "v092_resource_recovery_for_checker", nested_path)
            self.assertIs(checker.importlib.util.module_from_spec(late_spec), nested)
            late_spec.loader.exec_module(nested)
        self.assertIs(checker.importlib, original_checker_importlib)
        self.assertIs(self.stage.importlib, importlib)



if __name__ == '__main__':
    unittest.main()
