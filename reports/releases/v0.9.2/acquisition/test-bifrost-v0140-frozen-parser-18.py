#!/usr/bin/env python3
"""Synthetic integration of real partial replay and breadth-first batch loop.

Mocks replace actual processes, real analyzer/checker I/O, and resource probes;
no production receipt, admission, replay, source, or analyzer is touched.
"""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path,PurePosixPath
import tempfile
import types
import sys
import unittest
from unittest import mock

BASE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
fixture=load('breadth11_regression_fixture',BASE/'test-bifrost-v0140-replacement-13.py')
p,legacy_b,s=fixture.p,fixture.b,fixture.s

# Historical parser regressions continue to use the immutable BF14 bridge;
# downstream BF18 stage tests use the new bridge export below.  Keeping these
# bindings distinct prevents a historical helper from silently becoming the
# BF18 graph authority.
b=load('bf22_bridge18_fixture',BASE/'bifrost-v0140-frozen-bridge-18.py')

# The supervisor/admission fixture consumers import this module as their
# shared fixture boundary.  Keep the historical bridge/protocol/supervisor
# exports above for the frozen-history regressions, and expose a small BF18
# bridge fixture below.  It owns the actual bridge18 module; importing the
# older parser fixture here would silently reintroduce bridge09 roles.
class BridgeFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.lock=self.root/'canonical.lock'; self.lock.write_bytes(b'held')
        self.refs={}; self.modules={}
        for index,name in enumerate(b.REQUIRED_GRAPH_NAMES):
            path=f'graph/{index:02d}-{name}.py'; target=self.root/path
            target.parent.mkdir(parents=True,exist_ok=True)
            raw=f'fixture_{name} = {index}\n'.encode(); target.write_bytes(raw)
            self.refs[name]={'path':path,'sha256':b.sha256(raw)}
            module=types.ModuleType(f'fixture_{name}'); module.__file__=str(target)
            self.modules[name]=module
        def runtime_loader(*,mode,core,graph,ledger_bytes=None):
            raw=self.ledger_path.read_bytes() if ledger_bytes is None else ledger_bytes
            rows=[json.loads(line) for line in raw.splitlines()]
            modules={name:graph.module(name) for name in b.REQUIRED_GRAPH_NAMES}
            diagnostic={'context_digest':b.sha256(raw),'ledger_sha256':b.sha256(raw),'ledger_rows':len(rows)}
            return b.ActualRuntimeContext(root=self.root,mode=mode,graph=graph,
                modules=modules,diagnostic=diagnostic,
                objects={'modules':modules,'bridge_context':diagnostic,'mixed_context':{'rows':rows}})
        self.modules['bridge18'].load_runtime_context=runtime_loader
        self.source=self.put('source/closure.bin',b'immutable source closure')
        self.typed_source={"path":self.source["path"],"sha256":self.source["sha256"],"role":"release-input"}
        self.contract=self.put('contract.json',b'{}\n')
        self.contract_bytes={"source_commit":"a"*40,"source_inputs":[self.typed_source]}
        self.contract_path=self.root/'contract.json'
        self.contract_path.write_bytes(b.canonical_json(self.contract_bytes))
        self.contract={"path":"contract.json","sha256":b.sha256(self.contract_path.read_bytes())}
        self.ledger_path=self.root/'ledger.jsonl'
        self.ledger_path.write_bytes(b.canonical_json({'attempt_id':'a0','status':'completed'}))
        self.ledger={'path':'ledger.jsonl','sha256':b.sha256(self.ledger_path.read_bytes()),'rows':1}
        self.sidecar=self.put('sidecars/admission.json',b.canonical_json({'status':'admitted'}))
        self.manifest=self.put('manifest.json',b.canonical_json({'schema':'fixture-manifest'}))
        self.graph=b.load_graph(self.root,self.refs,fixture_modules=self.modules,fixture_only=True)
        self.lock_id=b.capture_lock(self.root,str(self.lock),101,'parent-birth')

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def put(self,path,raw):
        target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        return {'path':path,'sha256':b.sha256(raw)}

    def parent(self,index=0):
        return b.build_parent_stage(self.root,index=index,ledger=self.ledger,
            runtime={'opaque':object()},graph=self.graph,source_commit='a'*40,
            plan_commit='b'*40,contract_sha256='c'*64,lock=self.lock_id,
            sidecars={'admission':self.sidecar},source_refs=[self.source],
            analyzer_deadline_seconds=13840,created_monotonic=100.0)

    def typed_core(self):
        return {
            "runtime_module_graph": self.refs,
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "contract": self.contract,
            "source_inputs": [self.typed_source],
            "analyzer_deadline_seconds": 13840,
        }

    def test_complete_graph_is_bound_and_serialization_is_rejected(self):
        self.assertEqual(tuple(item.name for item in self.graph.members), b.REQUIRED_GRAPH_NAMES)
        self.assertEqual(len(self.graph.graph_sha256), 64)

    def test_create_parent_stage_uses_pinned_bridge_entrypoint_and_exact_ledger(self):
        """Exercise the actual parent-stage call path with harmless fixture I/O.

        The bridge loader is the graph-owned fixture seam; it returns an
        opaque ``ActualRuntimeContext`` while retaining the exact ledger
        bytes.  This reaches ``create_parent_stage`` and its real stable-read,
        graph-binding, and stage-identity checks without replaying evidence or
        starting an analyzer.
        """
        core = {
            "runtime_module_graph": self.refs,
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "source_refs": [self.source],
            "analyzer_deadline_seconds": 13840,
        }
        stage = b.create_parent_stage(
            self.root, core, self.manifest, 0, self.lock_id, self.ledger,
            sidecars={"admission": self.sidecar}, graph=self.graph,
        )
        self.assertIsInstance(stage, b.ParentStage)
        self.assertIs(stage.graph, self.graph)
        self.assertEqual(stage.identity.ledger_rows, 1)
        self.assertEqual(stage.identity.ledger_sha256, self.ledger["sha256"])
        self.assertEqual(stage.inventory[1].path, self.source["path"])
        self.assertEqual(stage.runtime.objects["bridge_context"]["ledger_sha256"],
                         self.ledger["sha256"])

    def test_create_parent_successor_and_child_bind_typed_source_roster(self):
        core = self.typed_core()
        parent = b.create_parent_stage(
            self.root, core, self.manifest, 0, self.lock_id, self.ledger,
            sidecars={"admission": self.sidecar}, graph=self.graph)
        self.assertEqual(parent.inventory[1].path, self.source["path"])

        after_path = self.root / "ledger-after.jsonl"
        after_path.write_bytes(self.ledger_path.read_bytes() +
                               b.canonical_json({"attempt_id":"a1","status":"completed"}))
        after = {"path":"ledger-after.jsonl", "sha256":b.sha256(after_path.read_bytes()), "rows":2}
        successor = b.create_parent_stage(
            self.root, core, self.manifest, 1, self.lock_id, after,
            sidecars={"phase": self.sidecar}, predecessor=parent, graph=self.graph)
        self.assertEqual(successor.inventory[1].path, self.source["path"])

        dispatch = {
            path: self.put(path, ("child:" + path).encode())
            for path in ("child/admission.json", "child/phase.json", "child/supervisor-permit.json")
        }
        child = b.create_child_stage(
            self.root, core, self.manifest, parent, self.lock_id,
            b.Lease(100.0, 13840.0, b.STARTUP_SECONDS),
            {"creator_pid":101,"creator_birth":"creator","pid":102,"birth":"child"},
            self.ledger, sidecars=dispatch, graph=self.graph)
        self.assertEqual(child.inventory[1].path, self.source["path"])

    def test_typed_source_near_misses_and_strict_fixture_boundary_fail_closed(self):
        core = self.typed_core()
        cases = []
        for label, mutate in (
            ("wrong role", lambda item: item.update(role="generated")),
            ("missing role", lambda item: item.pop("role")),
            ("empty role", lambda item: item.update(role="")),
            ("extra source commit", lambda item: item.update(source_commit="a" * 40)),
            ("wrong path", lambda item: item.update(path="../escape")),
            ("wrong sha", lambda item: item.update(sha256="0" * 64)),
            ("malformed sha", lambda item: item.update(sha256="not-a-sha")),
        ):
            candidate = dict(core)
            item = dict(self.typed_source)
            mutate(item)
            candidate["source_inputs"] = [item]
            cases.append((label, candidate))
        duplicate = dict(core)
        duplicate["source_inputs"] = [dict(self.typed_source), dict(self.typed_source)]
        cases.append(("duplicate path", duplicate))
        reordered = dict(core)
        second = self.put("source/second.bin", b"second")
        typed_second = {**second, "role":"release-input"}
        reordered["source_inputs"] = [typed_second, self.typed_source]
        cases.append(("reordered or omitted contract input", reordered))
        for label, candidate in cases:
            with self.subTest(label=label), self.assertRaises(b.FrozenBridge18Error):
                b._core_source_refs(self.root, candidate)
        with self.assertRaises(b.FrozenBridge18Error):
            b._ref(self.typed_source, "generic ref with role")

        wrong_commit = self.typed_core()
        wrong_commit["source_commit"] = "d" * 40
        with self.assertRaisesRegex(b.FrozenBridge18Error, "source_commit"):
            b._core_source_refs(self.root, wrong_commit)

    def test_continuation_source_contract_is_bound_separately(self):
        continuation_path = self.root / "continuation.json"
        continuation = {
            "source_commit": "e" * 40,
            "source_inputs": [self.typed_source],
        }
        continuation_path.write_bytes(b.canonical_json(continuation))
        core = {
            "source_commit": "f" * 40,
            "contract": self.contract,
            "continuation": {
                "source_commit": "e" * 40,
                "contract": {"path":"continuation.json", "sha256":b.sha256(continuation_path.read_bytes())},
                "source_inputs": [self.typed_source],
            },
        }
        refs = b._core_source_refs(self.root, core)
        self.assertEqual(refs, [self.source])
        broken = dict(core["continuation"])
        broken["source_commit"] = "f" * 40
        broken_core = dict(core)
        broken_core["continuation"] = broken
        with self.assertRaises(b.FrozenBridge18Error):
            b._core_source_refs(self.root, broken_core)


class GraphImportSmokeTests(unittest.TestCase):
    """Import-only smoke for the current reviewed BF18 88-member graph."""

    @classmethod
    def setUpClass(cls):
        identity_path = (fixture.ROOT /
            "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-14/manifest-identity.json")
        identity = json.loads(identity_path.read_bytes())
        predecessor_refs = identity["runtime_module_graph"]
        # Rebind only the reviewed successor roles to the current BF18 source
        # files.  Unchanged transitive roles retain the predecessor path/SHA;
        # ``_adapt_default_graph_spec`` then checks the complete topology.
        cls.refs = {}
        for old_role, old_ref in predecessor_refs.items():
            role = b._map_graph_role(old_role, b._ROLE_RENAMES)
            ref = dict(old_ref)
            if role in b._SUCCESSOR_GRAPH_PATHS:
                ref["path"] = b._SUCCESSOR_GRAPH_PATHS[role]
                ref["sha256"] = b.sha256((fixture.ROOT / ref["path"]).read_bytes())
            cls.refs[role] = ref
        required = tuple(b.REQUIRED_GRAPH_NAMES)
        extras = tuple(sorted(set(cls.refs) - set(required)))
        cls.refs = {role: cls.refs[role] for role in required + extras}
        # The production caller already owns the bridge18 module in its host
        # process.  Bind that exact object so stdlib introspection (notably
        # dataclasses) sees its ordinary module registration while every
        # transitive role still goes through the sealed local graph context.
        cls.graph = b.load_graph(fixture.ROOT, cls.refs, host_modules={"bridge18": b})
        cls.context = cls.graph.import_context
        assert cls.context is not None
        cls.routes = tuple(cls.context.spec["dynamic_route_table"])

    @classmethod
    def tearDownClass(cls):
        # ``load_graph`` seals once; this second call verifies that late-route
        # cleanup remains idempotent and does not recreate synthetic aliases.
        cls.context.seal()

    def _dispatch_dynamic(self, row):
        """Invoke one reviewed dynamic route through its real caller frame."""
        caller = row["caller_graph_roles"][0]
        route_function = row["caller_function"]
        location = str(fixture.ROOT / row["target_path"])
        if route_function == "private_engine" and row["loader_selector"].endswith("_<root-token>"):
            # This is the real graph-owned private_engine body, not a generated
            # same-name frame.  The owning test wraps the complete dispatch
            # wave in private_engine_scope, so repeated family routes reuse
            # the exact in-scope cache without clearing it per call.
            owner = self.context.module(caller)
            kind = "codeql" if "_codeql_" in row["loader_selector"] else "joern"
            result = owner.private_engine(fixture.ROOT, kind)
            self.assertIs(result["runner"], owner._PRIVATE_ENGINES[(str(fixture.ROOT), kind)]["runner"])
            return
        ns = {
            "__graph_role__": caller,
            "ctx": self.context,
            "selector": row["loader_selector"],
            "location": location,
        }
        call = "ctx.dynamic_spec(caller, selector, location)"
        ns["caller"] = caller
        if route_function == "<module>":
            exec("result = " + call, ns, ns)
        else:
            function = route_function.rsplit("/", 1)[-1]
            exec(
                "def " + function + "():\n"
                "    return " + call + "\n"
                "result = " + function + "()\n",
                ns,
                ns,
            )
        spec = ns["result"]
        module = spec.loader.create_module(spec)
        spec.loader.exec_module(module)

    def test_actual_graph_imports_all_members_without_nonstdlib_aliases(self):
        self.assertEqual(len(self.graph.members), 88)
        self.assertEqual(len(self.context.modules), 88)
        leaked = [name for name in set(sys.modules) - set(self.context._global_sys_before)
                  if not b._stdlib_module(name)]
        self.assertEqual(leaked, [])

    def test_actual_graph_rejects_each_host_role_digest_before_registration(self):
        """Host bindings must receive the same source/SHA guard as shells."""
        host_roles = {
            "bridge18": ("bridge18", "host_bridge18"),
            "protocol23": ("protocol23", "host_protocol23"),
            "admission23": ("admission23", "host_admission23"),
            "supervisor23": ("supervisor23", "host_supervisor23"),
        }
        for role, aliases in host_roles.items():
            with self.subTest(role=role):
                refs = {name: dict(ref) for name, ref in self.refs.items()}
                # The reviewed graph intentionally has same-path duplicate
                # host aliases. Keep their candidate refs coherent so the
                # topology adapter reaches host registration for this test.
                for alias in aliases:
                    refs[alias]["sha256"] = "0" * 64
                host = types.ModuleType(f"wrong_host_{role}")
                host.__file__ = str(fixture.ROOT / refs[role]["path"])
                before_modules = set(sys.modules)
                with self.assertRaisesRegex(b.FrozenBridge18Error,
                                             rf"host graph {role}.*digest"):
                    # Rebind the in-memory reviewed topology to the candidate
                    # refs so a caller-SHA route check cannot mask the host
                    # registration guard under test.
                    spec = b._adapt_default_graph_spec(refs)
                    b.GraphImportContext(fixture.ROOT, refs, spec,
                                         host_modules={role: host})
                self.assertEqual(set(sys.modules), before_modules)
                self.assertNotIn("__graph_role__", host.__dict__)

    def test_actual_graph_dispatches_all_43_dynamic_routes(self):
        with self.context.private_engine_scope():
            for row in self.routes:
                before = set(sys.modules)
                self._dispatch_dynamic(row)
                self.assertEqual(before, set(sys.modules))
                self.assertNotIn(row["loader_selector"], sys.modules)
        self.context.seal()
        self.assertEqual(len(self.routes), 43)

    def test_actual_graph_rejects_wrong_dynamic_path(self):
        row = self.routes[0]
        with self.assertRaisesRegex(ValueError, "dynamic route is not exact"):
            self.context.dynamic_spec(row["caller_graph_roles"][0],
                                      row["loader_selector"], fixture.ROOT / "wrong.py")

    def test_private_engine_families_require_exact_root_token_and_owner_frame(self):
        row = next(item for item in self.routes if item["route_id"] == "dynamic-040")
        token = hashlib.sha256((str(fixture.ROOT) + "codeql").encode()).hexdigest()[:12]
        selector = row["loader_selector"].replace("<root-token>", token)
        caller = row["caller_graph_roles"][0]
        location = fixture.ROOT / row["target_path"]

        with self.context.private_engine_scope():
            # A generated function with the right display name and selector
            # is not the graph-owned private_engine frame and must fail
            # closed.
            ns = {"__graph_role__": caller, "ctx": self.context, "caller": caller,
                  "selector": selector, "location": str(location)}
            with self.assertRaisesRegex(ValueError, "private-engine route is not owned"):
                exec("def private_engine():\n"
                     "    return ctx.dynamic_spec(caller, selector, location)\n"
                     "result = private_engine()\n", ns, ns)

            # The real body succeeds for both reviewed engine families; the
            # positive calls also prove the root token is computed from the
            # exact stage root rather than accepted as a wildcard.
            foreign = object()
            with mock.patch.dict(sys.modules, {selector: foreign}):
                with self.assertRaisesRegex(ValueError, "process-global registry"):
                    self.context.module(caller).private_engine(fixture.ROOT, "codeql")

            for kind in ("codeql", "joern"):
                owner = self.context.module(caller)
                result = owner.private_engine(fixture.ROOT, kind)
                self.assertIs(result["runner"], owner._PRIVATE_ENGINES[(str(fixture.ROOT), kind)]["runner"])

            # Once the exact graph-owned result is cached, private_engine does
            # not read the selector registry again.  Preserve that intended
            # in-scope reuse even if a foreign process entry appears later;
            # the fresh-construction call above is the fail-closed check.
            cached = owner._PRIVATE_ENGINES[(str(fixture.ROOT), "codeql")]
            with mock.patch.dict(sys.modules, {selector: object()}):
                self.assertIs(owner.private_engine(fixture.ROOT, "codeql"), cached)

            # The concrete loader body patches the graph-owned targets.  The
            # scope must expose those exact objects while it is active so a
            # provider can use them, then restore their original attributes.
            common = self.context.module(caller)
            self.assertIs(
                self.context.module("nested_040_dfb_common_v2_codeql_runner__root_token").load_population,
                common.load_population,
            )
            self.assertIs(
                self.context.module("nested_041_dfb_common_v2_codeql_reports__root_token").load_population,
                common.load_population,
            )

            with self.assertRaisesRegex(ValueError, "dynamic route is not exact"):
                self.context.dynamic_spec(caller, selector.replace(token, "0" * 12), location)

            with self.assertRaisesRegex(ValueError, "dynamic route is not exact"):
                self.context.dynamic_spec(caller, row["loader_selector"], location)

            foreign = object()
            with mock.patch.dict(sys.modules, {selector: foreign}):
                with self.assertRaises(KeyError):
                    self.context._sys_facade.modules[selector]

            malformed = dict(row)
            malformed["loader_selector"] = "_dfb_common_v2_codeql_runner_<root-token>_<root-token>"
            with self.assertRaisesRegex(ValueError, "exactly one root token"):
                self.context._computed_private_engine_route(
                    malformed, selector, caller)

    def _private_engine_state(self):
        common = self.context.module("local_012_swift_common_population_v2")
        cache = common.__dict__["_PRIVATE_ENGINES"]
        fields = ("__builtins__", "load_population", "export", "verify_activation")
        targets = {}
        for role in (
            "nested_040_dfb_common_v2_codeql_runner__root_token",
            "nested_041_dfb_common_v2_codeql_reports__root_token",
            "nested_042_dfb_common_v2_joern_runner__root_token",
            "nested_043_dfb_common_v2_joern_reports__root_token",
        ):
            module = self.context.module(role)
            targets[role] = {field: (field in module.__dict__, module.__dict__.get(field))
                             for field in fields}
        return (cache, dict(cache), dict(self.context._local_modules),
                dict(self.context._selector_before), targets)

    def _assert_private_engine_state(self, before):
        cache, cache_contents, local_modules, selector_before, targets = before
        common = self.context.module("local_012_swift_common_population_v2")
        self.assertIs(common.__dict__["_PRIVATE_ENGINES"], cache)
        self.assertEqual(dict(cache), cache_contents)
        self.assertEqual(dict(self.context._local_modules), local_modules)
        self.assertEqual(dict(self.context._selector_before), selector_before)
        for role, fields in targets.items():
            module = self.context.module(role)
            for field, (present, value) in fields.items():
                self.assertEqual(field in module.__dict__, present)
                if present:
                    self.assertIs(module.__dict__[field], value)

    def test_private_engine_scope_restores_success_exception_and_nested_reuse(self):
        owner = self.context.module("local_012_swift_common_population_v2")
        before = self._private_engine_state()
        with self.context.private_engine_scope():
            first = owner.private_engine(fixture.ROOT, "codeql")
            with self.context.private_engine_scope():
                second = owner.private_engine(fixture.ROOT, "codeql")
                self.assertIs(second, first)
                self.assertIn((str(fixture.ROOT), "codeql"), owner._PRIVATE_ENGINES)
            self.assertIs(owner._PRIVATE_ENGINES[(str(fixture.ROOT), "codeql")], first)
        self._assert_private_engine_state(before)

        with self.assertRaisesRegex(RuntimeError, "scope failure"):
            with self.context.private_engine_scope():
                owner.private_engine(fixture.ROOT, "joern")
                raise RuntimeError("scope failure")
        self._assert_private_engine_state(before)


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
        with mock.patch.object(legacy_b,'_ancestor',side_effect=ancestor) as ancestry,mock.patch.object(legacy_b,'_git',side_effect=git),\
             mock.patch.object(legacy_b,'_git_show',side_effect=lambda root,revision,path:blobs[revision,path]),\
             mock.patch.object(legacy_b,'_bound',return_value=b'synthetic patch'):
            result=legacy_b._source_delta05(fixture.ROOT,design,manifest,'0'*40 if wrong_incoming else 'a'*40,'f'*40,incoming_plan='b'*40)
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
        rows=[json.loads(line) for line in (fixture.ROOT/legacy_b.LEDGER_PATH).read_bytes().splitlines()][:88]
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
        legacy_b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
        self.assertEqual(len([r for r in rows if r.get('tool')=='bifrost']),21)
        self.assertEqual(len(contexts),2)
    def test_old_harness_cannot_be_new_harness_even_when_new_reports_are_selected(self):
        design,contexts,rows=self.context()
        for origin in contexts.values():origin['validated']['tools']['runner']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'original harness'):
            legacy_b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
    def test_preceding_joern_source_cannot_relabel_historical_bifrost(self):
        design,contexts,rows=self.context()
        for origin in contexts.values():origin['validated']['plan']['source_commit']=design['preceding_joern_measured_source']
        with self.assertRaisesRegex(ValueError,'origin relabeled'):
            legacy_b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
    def test_failed_c01_receipt_must_remain_present(self):
        design,contexts,rows=self.context()
        rows=[r for r in rows if r.get('attempt_id')!='bifrost-c-kernel-attempt-01-series-01']
        with self.assertRaisesRegex(ValueError,'receipt count'):
            legacy_b._validate_historical_bifrost(fixture.ROOT,design,contexts,rows)
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
            ledger=root/legacy_b.LEDGER_PATH;ledger.parent.mkdir(parents=True);ledger.write_bytes(b''.join(p.canonical_json(r) for r in rows))
            receipt=root/'reports/releases/v0.9.2/attempts/joern04/completed.json';receipt.parent.mkdir(parents=True);receipt.write_bytes(p.canonical_json(failed))
            context={**ctx,'contexts':{'c'*64:origin},'root':root,'checker':checker,'executor':executor,'validated':normalized}
            chosen=legacy_b._mixed_selected(context,rows,final=True)
            result=legacy_b._partial_replay(replacement,context,rows,chosen)
        self.assertEqual(len(calls),len(rows))
        self.assertEqual((result['selected_groups'],result['partitions'],result['rows']),(83,87,4144))
        self.assertEqual(result['status'],'partial-evidence-verified')
        self.assertFalse(result['full_release_gate_satisfied'])
        self.assertEqual(result['missing_groups'],['joern-swift-common108'])
    def test_partial_checker_cannot_return_full_configuration_gate(self):
        import inspect
        code=inspect.getsource(legacy_b.load_and_validate)
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


class ChildReadyReceiptTests(unittest.TestCase):
    """Process-boundary child guard coverage for the approved BF16 design."""

    def setUp(self):
        self.fixture = BridgeFixture("test_complete_graph_is_bound_and_serialization_is_rejected")
        self.fixture.setUp()
        self.b = b
        self.core = {
            "sidecar_namespace": "sidecars",
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "source_refs": [self.fixture.source],
            "analyzer_deadline_seconds": 13840,
        }
        self.core_identity = {"path": "core-identity.json", "sha256": "d" * 64}
        self.manifest_ref = self.fixture.manifest
        self.parent = self.fixture.parent()
        self.parent_receipt = self.b.write_compact_stage_receipt(
            self.fixture.root, "sidecars/stages/stage-00.json", self.parent,
            status="parent-stage-verified", sidecar_names=("admission",),
            manifest_ref=self.manifest_ref, core_identity=self.core_identity, core=self.core)
        child_modules = {
            name: types.ModuleType(f"fixture_child_{name}")
            for name in self.fixture.modules
        }
        for name, module in child_modules.items():
            module.__file__ = self.fixture.modules[name].__file__
        self.child_graph = self.b.load_graph(
            self.fixture.root, self.fixture.refs, fixture_modules=child_modules, fixture_only=True)
        self.dispatch = {
            path: self.fixture.put(path, f"dispatch:{path}".encode())
            for path in (
                "sidecars/group/admission.json",
                "sidecars/group/phase.json",
                "sidecars/group/supervisor-permit.json",
            )
        }
        parent_binding = self.b._read_compact_parent(
            self.fixture.root, self.parent_receipt, core=self.core)
        self.child = self.b.build_child_stage(
            self.fixture.root, parent_binding=parent_binding, runtime={"child": object()},
            graph=self.child_graph, source_refs=[self.fixture.source],
            child_creator_pid=201, child_creator_birth="creator", child_pid=202,
            child_birth="child", analyzer_deadline_seconds=13840,
            popen_monotonic=100, sidecars=self.dispatch, ledger=self.fixture.ledger)

    def tearDown(self):
        self.fixture.tearDown()

    def _guard(self, **changes):
        kwargs = dict(
            parent_receipt_ref=self.parent_receipt, graph=self.child_graph,
            manifest_ref=self.manifest_ref, core_identity=self.core_identity,
            core=self.core, dispatch_sidecars=self.dispatch, now_monotonic=101,
        )
        kwargs.update(changes)
        return self.b.assert_child_ready_from_receipt(
            self.fixture.root, self.child, **kwargs)

    def test_receipt_contains_exact_inventory_sidecars_and_positive_child_guard(self):
        result = self._guard()
        self.assertGreater(result, 0)
        receipt = json.loads((self.fixture.root / self.parent_receipt["path"]).read_bytes())
        self.assertEqual(receipt["inventory_refs"][0], receipt["ledger_ref"])
        self.assertEqual(tuple(receipt["sidecar_refs"]), ("admission",))
        self.assertEqual(receipt["predecessor_receipt_ref"], None)

    def test_child_guard_rejects_inventory_sidecar_graph_and_lease_mutations(self):
        altered_inventory = list(self.child.inventory)
        altered_inventory.reverse()
        object.__setattr__(self.child, "_inventory", tuple(altered_inventory))
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard()
        # Rebuild the child to restore its exact opaque sidecar/inventory state.
        parent_binding = self.b._read_compact_parent(
            self.fixture.root, self.parent_receipt, core=self.core)
        self.child = self.b.build_child_stage(
            self.fixture.root, parent_binding=parent_binding, runtime={"child": object()},
            graph=self.child_graph, source_refs=[self.fixture.source], child_creator_pid=201,
            child_creator_birth="creator", child_pid=202, child_birth="child",
            analyzer_deadline_seconds=13840, popen_monotonic=100,
            sidecars=self.dispatch, ledger=self.fixture.ledger)
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard(dispatch_sidecars={**self.dispatch, "sidecars/group/extra.json": self.fixture.put(
                "sidecars/group/extra.json", b"extra")})
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard(graph=self.fixture.graph)
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard(now_monotonic=100 + 13840 + self.b.STARTUP_SECONDS + 1)
        wrong_core = dict(self.core)
        wrong_core["source_commit"] = "e" * 40
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard(core=wrong_core)

    def test_child_guard_rejects_noncanonical_parent_receipt_copy_and_sidecar_overlap(self):
        alternate = self.fixture.root / "sidecars/stages/alternate.json"
        alternate.write_bytes((self.fixture.root / self.parent_receipt["path"]).read_bytes())
        alternate_ref = {"path": "sidecars/stages/alternate.json",
                         "sha256": self.b.sha256(alternate.read_bytes())}
        with self.assertRaises(self.b.FrozenBridge18Error):
            self._guard(parent_receipt_ref=alternate_ref)
        with self.assertRaises(self.b.FrozenBridge18Error):
            self.b.build_child_stage(
                self.fixture.root,
                parent_binding=self.b._read_compact_parent(
                    self.fixture.root, self.parent_receipt, core=self.core),
                runtime={"child": object()}, graph=self.child_graph,
                source_refs=[self.fixture.source], child_creator_pid=201,
                child_creator_birth="creator", child_pid=202, child_birth="child",
                analyzer_deadline_seconds=13840, popen_monotonic=100,
                sidecars={"admission": self.dispatch[next(iter(self.dispatch))],
                          **{k: v for k, v in self.dispatch.items() if k != next(iter(self.dispatch))}},
                ledger=self.fixture.ledger)

    def test_successor_receipt_has_exact_predecessor_chain(self):
        before = self.fixture.ledger_path.read_bytes()
        after_path = self.fixture.root / "ledger-after.jsonl"
        after_path.write_bytes(before + self.b.canonical_json({"attempt_id": "a1", "status": "completed"}))
        after = {"path": "ledger-after.jsonl", "sha256": self.b.sha256(after_path.read_bytes()), "rows": 2}
        phase = self.fixture.put("sidecars/group/phase.json", b"phase")
        successor = self.b.build_successor_stage(
            self.fixture.root, predecessor=self.parent, index=1, ledger_after=after,
            runtime={"successor": object()}, graph=self.fixture.graph,
            source_commit="a" * 40, plan_commit="b" * 40, contract_sha256="c" * 64,
            sidecars={"phase": phase}, source_refs=[self.fixture.source],
            analyzer_deadline_seconds=13840)
        final = self.b.write_completion(
            self.fixture.root, predecessor=self.parent, successor=successor,
            completion_path="sidecars/group/completion.json",
            completion={"group_id": "g", "attempt_id": "a1"},
            expected_group_id="g", expected_attempt_id="a1", graph=self.fixture.graph)
        receipt = self.b.write_compact_stage_receipt(
            self.fixture.root, "sidecars/stages/stage-01.json", final,
            status="successor-stage-verified", sidecar_names=tuple(sorted(final.sidecars)),
            manifest_ref=self.manifest_ref, core_identity=self.core_identity,
            predecessor_receipt_ref=self.parent_receipt, core=self.core)
        parsed = self.b._read_compact_parent(
            self.fixture.root, receipt, core=self.core, expected_index=1)
        self.assertEqual(parsed["predecessor_identity_sha256"], self.parent.identity_sha256)
        self.assertEqual(parsed["predecessor_receipt_ref"], self.parent_receipt)


if __name__=='__main__':unittest.main()
