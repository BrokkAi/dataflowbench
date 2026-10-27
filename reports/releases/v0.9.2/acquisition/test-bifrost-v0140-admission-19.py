#!/usr/bin/env python3
"""Fixture-only admission/stage identity regressions for BF19."""
from __future__ import annotations

import importlib.util
import json
import pickle
import tempfile
import os
import types
from unittest.mock import patch
from pathlib import Path
import shutil
import sys
import unittest


BASE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module); return module


# Independent miniature stage fixture, derived from immutable parser09 fixture.
# Actual parser10 production smoke remains a separate designer-owned gate; this
# suite exercises admission19 against the real bridge14 stage APIs directly.
b = load("bridge14_for_admission19_fixture", BASE / "bifrost-v0140-frozen-bridge-14.py")

class AdmissionStageFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lock = self.root / "canonical.lock"
        self.lock.write_bytes(b"held")
        self.refs: dict[str, dict[str, str]] = {}
        self.modules: dict[str, object] = {}
        for index, name in enumerate(b.REQUIRED_GRAPH_NAMES):
            path = f"graph/{index:02d}-{name}.py"
            raw = f"fixture_{name} = {index}\n".encode()
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            self.refs[name] = {"path": path, "sha256": b.sha256(raw)}
            self.modules[name] = types.ModuleType(f"fixture_{name}")
            self.modules[name].__file__ = str(target)
        def runtime_loader(*, mode, core, graph, ledger_bytes=None):
            raw = self.ledger_path.read_bytes() if ledger_bytes is None else ledger_bytes
            rows = [json.loads(line) for line in raw.splitlines()]
            modules = {name: graph.module(name) for name in b.REQUIRED_GRAPH_NAMES}
            diagnostic = {"context_digest": b.sha256(raw), "ledger_sha256": b.sha256(raw),
                          "ledger_rows": len(rows)}
            return b.ActualRuntimeContext(root=self.root, mode=mode, graph=graph,
                modules=modules, diagnostic=diagnostic,
                objects={"modules": modules, "bridge_context": diagnostic,
                         "mixed_context": {"rows": rows}})
        self.modules["bridge14"].load_runtime_context = runtime_loader
        self.source = self.put("source/closure.bin", b"immutable source closure")
        self.contract = self.put("contract.json", b'{"schema":"fixture-contract"}\n')
        self.ledger_path = self.root / "ledger.jsonl"
        self.ledger_path.write_bytes(b.canonical_json({"attempt_id": "a0", "status": "completed"}))
        self.ledger = {"path": "ledger.jsonl", "sha256": b.sha256(self.ledger_path.read_bytes()), "rows": 1}
        self.sidecar = self.put("sidecars/admission.json", b.canonical_json({"status": "admitted"}))
        self.manifest = self.put("manifest.json", b.canonical_json({"schema": "fixture-manifest"}))
        self.graph = b.load_graph(self.root, self.refs, fixture_modules=self.modules, fixture_only=True)
        self.lock_id = b.capture_lock(self.root, str(self.lock), 101, "parent-birth")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def put(self, path: str, raw: bytes) -> dict[str, str]:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return {"path": path, "sha256": b.sha256(raw)}

    def parent(self, index: int = 0):
        return b.build_parent_stage(
            self.root, index=index, ledger=self.ledger, runtime={"opaque": object()}, graph=self.graph,
            source_commit="a" * 40, plan_commit="b" * 40, contract_sha256="c" * 64,
            lock=self.lock_id, sidecars={"admission": self.sidecar}, source_refs=[self.source],
            analyzer_deadline_seconds=13840, created_monotonic=100.0)

    def test_complete_graph_is_bound_and_serialization_is_rejected(self):
        self.assertEqual(tuple(x.name for x in self.graph.members), b.REQUIRED_GRAPH_NAMES)
        self.assertEqual(len(self.graph.graph_sha256), 64)
        with self.assertRaises(b.FrozenBridge14Error):
            pickle.dumps(self.graph)
        parent = self.parent()
        with self.assertRaises(b.FrozenBridge14Error):
            pickle.dumps(parent)
        foreign = types.ModuleType("fixture_executor")
        with self.assertRaises(b.FrozenBridge14Error):
            self.graph.assert_member("executor", foreign)


fixture_mod = types.SimpleNamespace(BridgeFixture=AdmissionStageFixture, b=b)
admission = load("admission19_test", BASE / "bifrost-v0140-admission-19.py")


class Admission19Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_mod.BridgeFixture("test_complete_graph_is_bound_and_serialization_is_rejected")
        self.fixture.setUp()
        target = self.fixture.root / admission.STAGE_BRIDGE_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BASE / "bifrost-v0140-frozen-bridge-14.py", target)

    def tearDown(self):
        self.fixture.tearDown()

    def test_parent_and_child_stage_admission_reuses_exact_graph(self):
        parent = self.fixture.parent()
        result = admission.validate_parent_stage(self.fixture.root, parent, self.fixture.graph, expected_index=0,
                                                 stage_bridge=fixture_mod.b)
        self.assertEqual(result["status"], "stage-admitted")
        child_modules = {name: type(module)(f"fixture_child_{name}")
                         for name, module in self.fixture.modules.items()}
        graph = fixture_mod.b.load_graph(self.fixture.root, self.fixture.refs,
                                         fixture_modules=child_modules, fixture_only=True)
        child = fixture_mod.b.build_child_stage(
            self.fixture.root, parent=parent, runtime={"child": object()}, graph=graph,
            source_refs=[self.fixture.source], child_creator_pid=201,
            child_creator_birth="creator", child_pid=202, child_birth="child",
            analyzer_deadline_seconds=13840, popen_monotonic=100,
            sidecars={"dispatch-admission":self.fixture.put("sidecars/child-dispatch.json",b"fresh child dispatch")},
            ledger=self.fixture.ledger)
        child_result = admission.validate_child_stage(self.fixture.root, child, parent, graph, now_monotonic=101,
                                                      stage_bridge=fixture_mod.b)
        self.assertEqual(child_result["status"], "child-stage-admitted")

    def test_substituted_graph_or_stage_index_is_rejected(self):
        parent = self.fixture.parent()
        with self.assertRaises(admission.Admission19Error):
            admission.validate_parent_stage(self.fixture.root, parent, self.fixture.graph, expected_index=1,
                                            stage_bridge=fixture_mod.b)
        foreign = object()
        with self.assertRaises(admission.Admission19Error):
            admission.validate_parent_stage(self.fixture.root, parent, foreign, expected_index=0,
                                            stage_bridge=fixture_mod.b)




class ProductionStageAdmission19Tests(unittest.TestCase):
    """Actual writer/protocol path; only external auth/process/resource probes mocked.

    Static/runtime proof is an explicitly synthetic miniature stage, never a
    production qualification. Imports and bridge replays are forbidden mocks.
    """
    def setUp(self):
        self.fixture = fixture_mod.BridgeFixture("test_complete_graph_is_bound_and_serialization_is_rejected")
        self.fixture.setUp()
        self.b = fixture_mod.b
        self.p = load("fixture_stage_protocol19_actual", BASE / "bifrost-v0140-replacement-19.py")
        modules = dict(self.fixture.modules)
        modules.update(bridge14=self.b, admission19=admission, protocol19=self.p)
        members = tuple(self.b.GraphMember(x.name,x.canonical_path,x.source_sha256,modules[x.name],x.loader_identity)
                        for x in self.fixture.graph.members)
        self.graph = self.b.PinnedBridgeGraph(members,fixture_only=True)
        self.core = {"source_commit":"a"*40,"plan_commit":"b"*40,
                     "contract":{"path":"contract.json","sha256":"c"*64},
                     "original_prefix":{"path":"original.jsonl","sha256":"d"*64},
                     "continuation_prefix":{"path":"incoming.jsonl","sha256":"e"*64},
                     "replacement_groups":["bifrost-c-kernel"],
                     "sidecar_namespace":"sidecars/batch", "lock_path":str(self.fixture.lock),
                     "bifrost_admission_source":{"path":"admission.py","sha256":"1"*64},
                     "bifrost_supervisor_source":{"path":"supervisor.py","sha256":"2"*64}}
        self.context={"execution_authorized":False,"status":"read-only-frozen-validation-passed",
                      "context_digest":"3"*64,"source_commit":"a"*40,"plan_commit":"b"*40,
                      "canonical_contract_path_and_contract_sha256":self.core["contract"],
                      "original_prefix_ref":self.core["original_prefix"],"continuation_prefix_ref":self.core["continuation_prefix"],
                      "exact_replacement_group_subset_derived_from_full_plan":["bifrost-c-kernel"],
                      "historical_context_map_keyed_by_contract_sha256":{},"validated_full_normalized_plan":{"plan":{}}}
        self.static={"manifest_ref":{"path":admission.FINAL_MANIFEST_PATH,"sha256":"4"*64},
                     "manifest":{"core_identity":{"path":"core.json","sha256":"5"*64}},"core":self.core}
        modules={name:self.graph.module(name) for name in self.b.REQUIRED_GRAPH_NAMES}
        objects={"modules":{"replacement05":self.b._replacement_runtime_member(self.graph),
                            **{name:modules[name] for name in ("executor","checker","configuration")}},
                 "protocol_static":self.static,"bridge_context":self.context}
        self.runtime=self.b.ActualRuntimeContext(root=self.fixture.root.resolve(),mode="before",graph=self.graph,
                    modules=modules,diagnostic=self.context,objects=objects)
        self.stage=self.b.build_parent_stage(self.fixture.root,index=0,ledger=self.fixture.ledger,runtime=self.runtime,
                       graph=self.graph,source_commit="a"*40,plan_commit="b"*40,contract_sha256="c"*64,
                       lock=self.fixture.lock_id,sidecars={self.fixture.sidecar["path"]:self.fixture.sidecar},source_refs=[self.fixture.source],
                       analyzer_deadline_seconds=600,created_monotonic=100)
        self.kw={"stage":self.stage,"graph":self.graph,"pinned_bridge":self.b}

    def tearDown(self):self.fixture.tearDown()

    def test_actual_preparation_and_protocol_use_stage_without_import_or_replay(self):
        with patch.object(admission,"_load_module",side_effect=AssertionError("hidden import")), \
             patch.object(self.b,"load_and_validate",side_effect=AssertionError("hidden replay")), \
             patch.object(self.p,"_load_manifest",side_effect=AssertionError("hidden static reload")):
            result=admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,self.context,**self.kw)
            self.assertIs(result["bridge_context"],self.context)
            with self.p.stage_context(self.fixture.root,**self.kw):
                self.assertIs(self.p.validate_static(self.fixture.root),self.static)
        self.assertIsNone(admission._ACTIVE_STAGE.get())
        self.assertIsNone(self.p._PROTOCOL_STAGE.get())

    def _receipt_child_inputs(self):
        dispatch = {path:self.fixture.put(path,b"dispatch fixture") for path in
                    ("sidecars/dispatch-admission.json", "sidecars/dispatch-phase.json",
                     "sidecars/dispatch-permit.json")}
        child = self.b.build_child_stage(
            self.fixture.root, parent=self.stage, runtime=self.runtime, graph=self.graph,
            source_refs=[self.fixture.source], child_creator_pid=201,
            child_creator_birth="creator", child_pid=202, child_birth="child",
            analyzer_deadline_seconds=600, popen_monotonic=100,
            sidecars=dispatch, ledger=self.fixture.ledger)
        return child, {"parent_receipt_ref":self.fixture.put("sidecars/batch/stages/stage-00.json",b"synthetic parent metadata"),
                       "graph":self.graph, "manifest_ref":self.static["manifest_ref"],
                       "core_identity":self.static["manifest"]["core_identity"], "core":self.core,
                       "dispatch_sidecars":dispatch, "now_monotonic":101,
                       "stage_bridge":self.b}

    def test_child_receipt_wrapper_delegates_exact_opaque_graph_without_reload(self):
        child,kwargs=self._receipt_child_inputs()
        # The designer independently tests metadata/lease validation. This tests
        # the actual admission wrapper with a real opaque child and exact graph.
        with patch.object(self.b,"assert_child_ready_from_receipt",return_value=1199.0,create=True) as guard, \
             patch.object(admission,"_load_module",side_effect=AssertionError("hidden import")), \
             patch.object(self.b,"load_and_validate",side_effect=AssertionError("hidden replay")):
            result=admission.validate_child_stage_from_receipt(self.fixture.root,child,**kwargs)
        self.assertEqual(result["status"],"child-stage-admitted")
        self.assertEqual(result["startup_remaining_seconds"],1199.0)
        self.assertEqual(result["parent_receipt_ref"],kwargs["parent_receipt_ref"])
        guard.assert_called_once_with(self.fixture.root.resolve(),child,
            **{key:value for key,value in kwargs.items() if key!="stage_bridge"})
        self.assertIs(guard.call_args.kwargs["core"],self.core)
        self.assertIs(guard.call_args.kwargs["graph"],self.graph)

    def test_child_receipt_wrapper_rejects_foreign_bridge_graph_and_serialized_child(self):
        child,kwargs=self._receipt_child_inputs()
        with patch.object(self.b,"assert_child_ready_from_receipt",return_value=1199.0,create=True) as guard:
            for changed in ({"stage_bridge":object()}, {"graph":self.fixture.graph}, {"stage_bridge":None}):
                with self.subTest(changed=list(changed)),self.assertRaises(Exception):
                    admission.validate_child_stage_from_receipt(self.fixture.root,child,**{**kwargs,**changed})
            with self.assertRaises(admission.Admission19Error):
                admission.validate_child_stage_from_receipt(self.fixture.root,{"serialized":True},**kwargs)
            guard.assert_not_called()

    def test_child_receipt_guard_failure_propagates_once_and_invalid_lease_rejects(self):
        child,kwargs=self._receipt_child_inputs()
        with patch.object(self.b,"assert_child_ready_from_receipt",side_effect=self.b.FrozenBridge14Error("stale or expired"),create=True) as guard:
            with self.assertRaisesRegex(self.b.FrozenBridge14Error,"stale or expired"):
                admission.validate_child_stage_from_receipt(self.fixture.root,child,**kwargs)
            guard.assert_called_once()
        for remaining in (0,-1,True,float("inf"),float("nan"),{"serialized":1199}):
            with self.subTest(remaining=remaining),patch.object(self.b,"assert_child_ready_from_receipt",return_value=remaining,create=True):
                with self.assertRaises(admission.Admission19Error):
                    admission.validate_child_stage_from_receipt(self.fixture.root,child,**kwargs)

    def test_context_copy_wrong_graph_and_foreign_bridge_fail_closed(self):
        with self.assertRaises(admission.Admission19Error):
            admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,dict(self.context),**self.kw)
        with self.assertRaises(Exception):
            admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,self.context,
                stage=self.stage,graph=self.fixture.graph,pinned_bridge=self.b)
        with self.assertRaises(Exception):
            admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,self.context,
                stage=self.stage,graph=self.graph,pinned_bridge=object())
        with self.assertRaises(admission.Admission19Error):
            admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,self.context)
        self.assertIsNone(admission._ACTIVE_STAGE.get())

    def test_real_parent_writer_and_real_protocol_receipt_validation_no_replay(self):
        process={"schema":"invocation-process-ownership/v1","status":"verified","automatic_retry":False,
                 "pid":os.getpid(),"birth_identity":"synthetic-birth","no_foreign_processes":True}
        resources={"resource_policy":dict(self.p.RESOURCE_POLICY),"resource_policy_sha256":self.p._policy_sha(self.p.RESOURCE_POLICY),
                   "remaining_reserved_seconds":None}
        # The external controls are explicit fixtures. The actual writer and
        # complete protocol parent receipt field validation execute unmocked.
        with patch.dict(os.environ,{admission.FIXTURE_ENV:"1"}), \
             patch.object(admission,"_authorization") as auth, \
             patch.object(admission,"_process",return_value=process), \
             patch.object(admission,"_live_resources",return_value=resources), \
             patch.object(admission,"_permit",return_value={"permit_id":"synthetic-permit"}), \
             patch.object(admission,"_require_lock"), \
             patch.object(admission,"_load_module",side_effect=AssertionError("hidden import")), \
             patch.object(self.b,"load_and_validate",side_effect=AssertionError("hidden replay")):
            result=admission.admit_parent(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,{},"6"*64,
                       {},process,self.context,fixture_only=True,lock=object(),**self.kw)
            auth.assert_called_once()
            self.assertTrue((self.fixture.root/result["path"]).is_file())
            with self.p.stage_context(self.fixture.root,**self.kw):
                checked=self.p.validate_parent_admission(self.fixture.root,admission.FINAL_MANIFEST_PATH,result["path"])
            self.assertEqual(checked["value"]["process_ownership"],process)

    def test_stage_context_restores_on_exception_and_detects_source_mutation(self):
        with self.assertRaisesRegex(RuntimeError,"sentinel"):
            with self.p.stage_context(self.fixture.root,**self.kw):raise RuntimeError("sentinel")
        self.assertIsNone(self.p._PROTOCOL_STAGE.get())
        (self.fixture.root/self.fixture.source["path"]).write_bytes(b"mutated source")
        with self.assertRaises(Exception):
            admission.validate_preparation(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,self.context,**self.kw)

    def test_protocol_actual_four_member_map_rejects_impostors_and_extra_members(self):
        frozen_modules = self.runtime.objects["modules"]
        # ActualRuntimeContext.modules is the full host graph; objects.modules
        # intentionally retains the frozen four-module API, with exact objects.
        self.assertIsNot(frozen_modules, self.runtime.modules)
        with self.p.stage_context(self.fixture.root, **self.kw):
            self.assertIs(self.p._PROTOCOL_STAGE.get()["runtime"]["modules"], frozen_modules)
        for role in ("replacement05", "executor", "checker", "configuration"):
            original = frozen_modules[role]
            frozen_modules[role] = types.ModuleType("foreign_" + role)
            try:
                with self.assertRaises(Exception):
                    with self.p.stage_context(self.fixture.root, **self.kw): self.fail("accepted foreign module")
            finally:
                frozen_modules[role] = original
            self.assertIsNone(self.p._PROTOCOL_STAGE.get())
        frozen_modules["unexpected"] = object()
        try:
            with self.assertRaises(Exception):
                with self.p.stage_context(self.fixture.root, **self.kw): self.fail("accepted expanded frozen roster")
        finally:
            del frozen_modules["unexpected"]


    def test_real_command_and_raw_permit_reject_near_miss_stage_bindings(self):
        group="bifrost-c-kernel";attempt="c-attempt-fixture"
        spec={"schema":"v092-bifrost-v0140-frozen-command/v1","group_id":group,"attempt_id":attempt,
              "argv":["fixture-only-no-execution"],"context_digest":self.context["context_digest"],
              "canonical_contract":self.core["contract"],"source_commit":self.core["source_commit"],
              "plan_commit":self.core["plan_commit"],"environment":{},
              "stage_identity_sha256":self.stage.identity_sha256,
              "parent_stage_identity_sha256":self.stage.identity_sha256,"graph_sha256":self.graph.graph_sha256}
        def sign(value):
            value=dict(value);value.pop("command_spec_sha256",None)
            value["argv_sha256"]=self.p.sha256(self.p.canonical_json(value["argv"]))
            value["command_spec_sha256"]=self.p.sha256(self.p.canonical_json(value));return value
        spec=sign(spec)
        active=admission._stage_bindings(self.fixture.root,self.stage,self.graph,self.b)
        token=admission._ACTIVE_STAGE.set(active)
        try:
            admission._validate_command_spec(spec,group_id=group,attempt_id=attempt,bridge_context=self.context)
            for key in ("stage_identity_sha256","parent_stage_identity_sha256","graph_sha256"):
                wrong=sign({**spec,key:"f"*64})
                with self.assertRaises(admission.Admission19Error):
                    admission._validate_command_spec(wrong,group_id=group,attempt_id=attempt,bridge_context=self.context)
            permit={"schema":admission.RAW_PERMIT_SCHEMA,"scope":"group","automatic_retry":False,
                    "pid":os.getpid(),"birth":"synthetic-birth","token":"fixture-only",
                    "argv_sha256":spec["argv_sha256"],"permit_id":"synthetic-permit","group_id":group,
                    "attempt_id":attempt,"command_spec_sha256":spec["command_spec_sha256"],
                    "stage_identity_sha256":self.stage.identity_sha256,
                    "parent_stage_identity_sha256":self.stage.identity_sha256,"graph_sha256":self.graph.graph_sha256}
            def check(value):
                raw=self.p.canonical_json(value);path=self.fixture.root/"permit-fixture.json";path.write_bytes(raw)
                return admission._permit(self.fixture.root,{"path":"permit-fixture.json","sha256":self.p.sha256(raw)},
                    scope="group",group_id=group,attempt_id=attempt,command_sha256=spec["command_spec_sha256"])
            check(permit)
            for key in ("stage_identity_sha256","parent_stage_identity_sha256","graph_sha256"):
                with self.assertRaises(admission.Admission19Error):check({**permit,key:"f"*64})
        finally:admission._ACTIVE_STAGE.reset(token)

    def test_actual_completion_writer_finalizes_successor_without_replay_or_retry(self):
        group="bifrost-c-kernel"; attempt="bifrost-c-kernel-attempt-03-series-02"
        slot={"attempt_id":attempt,"admission_path":"sidecars/batch/c/admission.json",
              "phase_gate_path":"sidecars/batch/c/phase.json","completion_path":"sidecars/batch/c/completion.json"}
        self.static["manifest"]["execution_admission_slots"]={group:slot}
        def write(path, raw):
            target=self.fixture.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            return {"path":path,"sha256":self.p.sha256(raw)}
        ownership={"schema":"invocation-process-ownership/v1","cleanup_status":"tracked-processes-stopped",
                   "descendant_containment":"unproven","tracking_interval_seconds":2.0,"root_pid":123,
                   "tracked_processes":[{"pid":123,"start_identity":"fixture-only-birth"}]}
        terminal={"group_id":group,"attempt_id":attempt,"tool":"bifrost","status":"completed","exit_code":0,
                  "timed_out":False,"capacity_loss":None,"source_commit":self.core["source_commit"],
                  "plan_commit":self.core["plan_commit"],"contract_sha256":self.core["contract"]["sha256"],
                  "execution_series":2,"process_ownership":ownership,"end_utc":"2026-10-24T17:00:00Z"}
        ar=write(slot["admission_path"],self.p.canonical_json({"group_id":group,"attempt_id":attempt}))
        pr=write(slot["phase_gate_path"],self.p.canonical_json({"group_id":group,"attempt_id":attempt}))
        cr=write(f"reports/releases/v0.9.2/attempts/{attempt}/completed.json",self.p.canonical_json(terminal))
        before=self.fixture.ledger_path.read_bytes()
        br=write("sidecars/batch/c/ledger-before.jsonl",before)
        after=before+self.p.canonical_json(terminal)
        lr=write("sidecars/batch/c/ledger-after.jsonl",after)
        safety={"schema":"v092-bifrost-v0140-terminal-continuation-safety/v1",
                "status":"tracked-cleanup-and-resource-checked","group_id":group,"attempt_id":attempt,
                "receipt_sha256":cr["sha256"],"owned_processes_gone":True,"resources_valid":True,
                "tracked_processes":ownership["tracked_processes"],"checked_utc":"2026-10-24T17:00:01Z"}
        # A different transition must never reuse or replace a prior sidecar key.
        with self.assertRaises(self.b.FrozenBridge14Error):
            self.b.build_successor_stage(self.fixture.root,predecessor=self.stage,index=1,
                ledger_after={**lr,"rows":2},runtime=self.runtime,graph=self.graph,
                source_commit=self.core["source_commit"],plan_commit=self.core["plan_commit"],
                contract_sha256=self.core["contract"]["sha256"],
                sidecars={self.fixture.sidecar["path"]:ar},source_refs=[self.fixture.source],
                analyzer_deadline_seconds=600,created_monotonic=101)
        draft=self.b.build_successor_stage(self.fixture.root,predecessor=self.stage,index=1,
            ledger_after={**lr,"rows":2},runtime=self.runtime,graph=self.graph,
            source_commit=self.core["source_commit"],plan_commit=self.core["plan_commit"],
            contract_sha256=self.core["contract"]["sha256"],sidecars={ar["path"]:ar,pr["path"]:pr},
            source_refs=[self.fixture.source],analyzer_deadline_seconds=600,created_monotonic=101)
        kwargs={"predecessor_stage":self.stage,"successor_stage":draft,"graph":self.graph,"pinned_bridge":self.b,
                "fixture_only":True,"lock":object(),"continuation_safety":safety}
        with patch.dict(os.environ,{admission.FIXTURE_ENV:"1"}),patch.object(admission,"_require_lock"), \
             patch.object(admission,"_load_module",side_effect=AssertionError("hidden import")), \
             patch.object(self.b,"load_and_validate",side_effect=AssertionError("hidden replay")):
            ref,finalized=admission.write_completion(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,
                            group,ar,pr,cr,br,lr,self.context,**kwargs)
            self.assertIsInstance(finalized,self.b.FinalizedParentStage)
            self.assertIs(finalized.runtime,self.runtime)
            self.assertEqual(finalized.predecessor_identity_sha256,self.stage.identity_sha256)
            self.assertEqual(ref["path"],slot["completion_path"])
            self.assertEqual(finalized.sidecars[self.fixture.sidecar["path"]].sha256,self.fixture.sidecar["sha256"])
            self.assertEqual(finalized.sidecars[ar["path"]].sha256,ar["sha256"])
            self.assertEqual(finalized.sidecars[pr["path"]].sha256,pr["sha256"])
            with self.assertRaises(self.b.FrozenBridge14Error):
                admission.write_completion(self.fixture.root,admission.FINAL_MANIFEST_PATH,"4"*64,
                            group,ar,pr,cr,br,lr,self.context,**kwargs)
        self.assertIsNone(admission._ACTIVE_STAGE.get())
        self.assertIsNone(self.p._PROTOCOL_STAGE.get())

if __name__ == "__main__":
    unittest.main()
