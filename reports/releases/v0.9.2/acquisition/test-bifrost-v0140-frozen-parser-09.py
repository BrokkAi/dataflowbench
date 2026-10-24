#!/usr/bin/env python3
"""Fixture-only regressions for the BF14 replay-stage bridge.

The tests construct ordinary temporary files and fixture module objects.  No
frozen executor, analyzer, subprocess, lock acquisition, or production
bridge is imported.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import pickle
import sys
import tempfile
import types
import unittest


BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bridge09_test_module", BASE / "bifrost-v0140-frozen-bridge-09.py")
assert spec is not None and spec.loader is not None
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class BridgeFixture(unittest.TestCase):
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
        self.modules["bridge09"].load_runtime_context = runtime_loader
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
        with self.assertRaises(b.FrozenBridge09Error):
            pickle.dumps(self.graph)
        parent = self.parent()
        with self.assertRaises(b.FrozenBridge09Error):
            pickle.dumps(parent)
        foreign = types.ModuleType("fixture_executor")
        with self.assertRaises(b.FrozenBridge09Error):
            self.graph.assert_member("executor", foreign)

    def test_runtime_loader_must_be_graph_owned_and_runs_once(self):
        runtime, digest = b.load_stage_runtime(self.root, graph=self.graph, mode="before", core_identity={"id": "core"})
        self.assertEqual(runtime.mode, "before")
        self.assertEqual(len(digest), 64)
        with self.assertRaises(b.FrozenBridge09Error):
            b.load_runtime_stage(self.root, graph=self.graph, runtime_loader=lambda **_: object(),
                                 mode="before", core_identity={})

    def test_runtime_digest_binds_actual_context_and_snapshot_bytes(self):
        runtime, digest = b.load_stage_runtime(self.root, graph=self.graph, mode="before",
            core_identity={}, ledger_bytes=self.ledger_path.read_bytes())
        self.assertEqual(digest, runtime.diagnostic["context_digest"])
        changed = b.canonical_json({"attempt_id": "different", "status": "completed"})
        _, changed_digest = b.load_stage_runtime(self.root, graph=self.graph, mode="before",
            core_identity={}, ledger_bytes=changed)
        self.assertNotEqual(digest, changed_digest)

    def test_ledger_runtime_rejects_a_foreign_validated_snapshot(self):
        original = self.modules["bridge09"].load_runtime_context
        def wrong_loader(*, mode, core, graph, ledger_bytes=None):
            return original(mode=mode, core=core, graph=graph,
                ledger_bytes=b.canonical_json({"attempt_id": "foreign", "status": "completed"}))
        self.modules["bridge09"].load_runtime_context = wrong_loader
        with self.assertRaisesRegex(b.FrozenBridge09Error, "different ledger snapshot"):
            b._load_bound_ledger_runtime(self.root, self.graph, {}, self.ledger, "before")

    def test_ledger_runtime_rejects_snapshot_changed_during_validation(self):
        original = self.modules["bridge09"].load_runtime_context
        def changed_loader(*, mode, core, graph, ledger_bytes=None):
            runtime = original(mode=mode, core=core, graph=graph, ledger_bytes=ledger_bytes)
            self.ledger_path.write_bytes(ledger_bytes + b"\n")
            return runtime
        self.modules["bridge09"].load_runtime_context = changed_loader
        with self.assertRaisesRegex(b.FrozenBridge09Error, "metadata changed"):
            b._load_bound_ledger_runtime(self.root, self.graph, {}, self.ledger, "before")

    def test_graph_runtime_provider_returns_complete_lossless_mapping(self):
        contract_ref = self.contract
        manifest_path = self.manifest["path"]
        replacement = self.modules["replacement14"]
        executor = self.modules["executor"]
        incoming = self.modules["incoming_recovery"]
        replacement.validate_static = lambda root, path: {
            "status": "fixture-static", "manifest_ref": self.manifest,
            "core": {"contract": contract_ref}, "manifest": {"schema": "fixture"}}
        executor.validate_plan = lambda path, repo_root=None: {
            "bytes_sha256": contract_ref["sha256"], "path": str(self.root / path),
            "repo_root": str(self.root), "plan": {"groups": []}}
        def provider(*, root, core, graph, mode, ledger_bytes):
            modules = {name: graph.module(name) for name in b.REQUIRED_GRAPH_NAMES}
            validated = executor.validate_plan(self.root / contract_ref["path"], repo_root=self.root)
            context = {"context_digest": "d" * 64, "execution_authorized": False}
            return {
                "modules": modules, "validated": validated,
                "mixed_context": {"root": self.root, "validated": validated},
                "checker_summary": {"status": "partial-evidence-verified"},
                "configuration_summary": {"status": "configuration-pending-complete-matrix"},
                "bridge_context": context,
            }
        incoming.load_runtime_context = provider
        core = {"manifest_ref": self.manifest}
        runtime = b._graph_runtime_context(self.root, core, self.graph,
                                            mode="before", ledger_bytes=b"ledger\n")
        self.assertIs(runtime.objects["modules"], runtime.modules)
        self.assertEqual(set(runtime.objects), {
            "protocol_static", "modules", "validated", "mixed_context",
            "checker_summary", "configuration_summary", "bridge_context"})
        self.assertEqual(runtime.diagnostic["protocol_static"]["status"], "fixture-static")
        def foreign_provider(**kwargs):
            provided = dict(provider(**kwargs))
            provided["modules"] = {**provided["modules"],
                                    "executor": types.ModuleType("foreign")}
            return provided
        incoming.load_runtime_context = foreign_provider
        with self.assertRaises(b.FrozenBridge09Error):
            b._graph_runtime_context(self.root, core, self.graph,
                                     mode="before", ledger_bytes=b"ledger\n")

    def test_host_graph_factory_binds_existing_modules_and_runtime(self):
        core = {
            "graph_refs": self.refs,
            "source_refs": [self.source],
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "analyzer_deadline_seconds": 13840,
            "startup_seconds": 600,
        }
        parent = b.create_parent_stage(
            self.root, core, self.manifest, 0, self.lock_id, self.ledger,
            sidecars={"admission": self.sidecar}, host_modules=self.modules)
        runtime_objects = b.runtime_objects(parent)
        self.assertIs(runtime_objects, parent.runtime)
        self.assertIs(parent.graph.module("bridge09"), self.modules["bridge09"])
        foreign = dict(self.modules)
        foreign["executor"] = types.ModuleType("fixture_executor_foreign")
        foreign_path = self.root / "graph" / "foreign-executor.py"
        foreign_path.write_bytes(self.root.joinpath(self.refs["executor"]["path"]).read_bytes())
        foreign["executor"].__file__ = str(foreign_path)
        with self.assertRaises(b.FrozenBridge09Error):
            b.create_parent_stage(
                self.root, core, self.manifest, 0, self.lock_id, self.ledger,
                host_modules=foreign)

    def test_optional_disk_guard_member_is_supported_without_changing_required_roster(self):
        refs = dict(self.refs)
        modules = dict(self.modules)
        raw = b"fixture_disk_guard = True\n"
        path = self.root / "graph" / "12-disk_guard.py"
        path.write_bytes(raw)
        refs["disk_guard"] = {"path": str(path.relative_to(self.root)), "sha256": b.sha256(raw)}
        modules["disk_guard"] = types.ModuleType("fixture_disk_guard")
        modules["disk_guard"].__file__ = str(path)
        graph = b.load_graph(self.root, refs, fixture_modules=modules, fixture_only=True)
        self.assertIs(graph.module("disk_guard"), modules["disk_guard"])
        self.assertEqual(tuple(item.name for item in graph.members),
                         b.REQUIRED_GRAPH_NAMES + b.OPTIONAL_GRAPH_NAMES)

    def test_serialized_core_reconstructs_required_roles_without_losing_aliases(self):
        refs = dict(self.refs)
        refs["extra_alias"] = dict(refs["executor"])
        core = json.loads(b.canonical_json({"runtime_module_graph": refs}))
        graph = b.prepare_graph(self.root, core, host_modules=self.modules)
        self.assertEqual(tuple(member.name for member in graph.members),
                         b.REQUIRED_GRAPH_NAMES + ("extra_alias",))
        self.assertEqual(next(member for member in graph.members if member.name == "extra_alias").source_sha256,
                         refs["executor"]["sha256"])
        del core["runtime_module_graph"]["checker"]
        with self.assertRaises(b.FrozenBridge09Error):
            b.prepare_graph(self.root, core, host_modules=self.modules)

    def test_explicit_sorted_transitive_graph_extras_are_hash_bound(self):
        refs = dict(self.refs)
        modules = dict(self.modules)
        extra_names = ("bridge08", "disk_guard", "replacement05", "runtime_loaders14", "stage_runtime01")
        for index, name in enumerate(extra_names, 30):
            path = self.root / "graph" / f"{index:02d}-{name}.py"
            raw = f"fixture_{name} = {index}\n".encode()
            path.write_bytes(raw)
            refs[name] = {"path": str(path.relative_to(self.root)), "sha256": b.sha256(raw)}
            module = types.ModuleType(f"fixture_{name}")
            module.__file__ = str(path)
            modules[name] = module
        graph = b.load_graph(self.root, refs, fixture_modules=modules, fixture_only=True)
        self.assertEqual(tuple(item.name for item in graph.members),
                         b.REQUIRED_GRAPH_NAMES + extra_names)
        self.assertIs(graph.module("replacement05"), modules["replacement05"])
        graph.assert_complete({member.name: member.module_object for member in graph.members})
        with self.assertRaises(b.FrozenBridge09Error):
            graph.assert_complete({name: modules[name] for name in b.REQUIRED_GRAPH_NAMES + ("bridge08",)})
        foreign = {member.name: member.module_object for member in graph.members}
        foreign["disk_guard"] = types.ModuleType("fixture_foreign_disk_guard")
        with self.assertRaises(b.FrozenBridge09Error):
            graph.assert_complete(foreign)

    def test_transitive_graph_extras_must_be_sorted_and_named(self):
        refs = dict(self.refs)
        modules = dict(self.modules)
        for index, name in enumerate(("stage_runtime01", "replacement05"), 30):
            path = self.root / "graph" / f"{index:02d}-{name}.py"
            raw = f"fixture_{name} = {index}\n".encode()
            path.write_bytes(raw)
            refs[name] = {"path": str(path.relative_to(self.root)), "sha256": b.sha256(raw)}
            module = types.ModuleType(f"fixture_{name}")
            module.__file__ = str(path)
            modules[name] = module
        with self.assertRaisesRegex(b.FrozenBridge09Error, "sorted"):
            b.load_graph(self.root, refs, fixture_modules=modules, fixture_only=True)

    def test_parent_predecessor_transition_reuses_exact_graph(self):
        core = {
            "graph_refs": self.refs,
            "source_refs": [self.source],
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "analyzer_deadline_seconds": 13840,
            "startup_seconds": 600,
        }
        parent = b.create_parent_stage(
            self.root, core, self.manifest, 0, self.lock_id, self.ledger,
            sidecars={"admission": self.sidecar}, host_modules=self.modules)
        successor_path = self.root / "ledger-successor.jsonl"
        successor_raw = self.ledger_path.read_bytes() + b.canonical_json(
            {"attempt_id": "a1", "status": "completed"})
        successor_path.write_bytes(successor_raw)
        successor = b.create_parent_stage(
            self.root, core, self.manifest, 1, self.lock_id,
            {"path": successor_path.name, "sha256": b.sha256(successor_raw), "rows": 2},
            sidecars={"phase": self.sidecar}, predecessor=parent, graph=parent.graph)
        self.assertIsInstance(successor, b.SuccessorStageDraft)
        self.assertIs(successor.graph, parent.graph)
        self.assertEqual(successor.predecessor_identity_sha256, parent.identity_sha256)
        self.assertIn("admission", successor.sidecars)
        self.assertIn("phase", successor.sidecars)

    def test_compact_parent_receipt_binds_fresh_child_and_rejects_tampering(self):
        parent = self.parent()
        manifest_ref = self.manifest
        core_identity = {"core": "fixture-core"}
        receipt_ref = b.write_compact_stage_receipt(
            self.root, "sidecars/stage-00.json", parent,
            status="parent-stage-verified", sidecar_names=("admission",),
            manifest_ref=manifest_ref, core_identity=core_identity)
        child_modules = {name: types.ModuleType(f"fixture_child_{name}")
                         for name in b.REQUIRED_GRAPH_NAMES}
        for name, module in child_modules.items():
            module.__file__ = str(self.root / self.refs[name]["path"])
        def child_loader(*, mode, core, graph, ledger_bytes=None):
            return self.modules["bridge09"].load_runtime_context(
                mode=mode, core=core, graph=graph, ledger_bytes=ledger_bytes)
        child_modules["bridge09"].load_runtime_context = child_loader
        core = {
            "graph_refs": self.refs,
            "source_refs": [self.source],
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract_sha256": "c" * 64,
            "analyzer_deadline_seconds": 13840,
            "startup_seconds": 600,
            "core_identity": core_identity,
        }
        child = b.create_child_stage(
            self.root, core, manifest_ref, receipt_ref, self.lock_id,
            b.Lease(200.0, 13840.0),
            {"creator_pid": 201, "creator_birth": "creator-birth",
             "pid": 202, "birth": "child-birth"},
            self.ledger, host_modules=child_modules)
        self.assertEqual(child.parent_identity_sha256, parent.identity_sha256)
        self.assertIsNot(child.graph, parent.graph)
        receipt_path = self.root / receipt_ref["path"]
        tampered = dict(receipt_ref)
        tampered["sha256"] = "0" * 64
        with self.assertRaises(b.FrozenBridge09Error):
            b.create_child_stage(
                self.root, core, manifest_ref, tampered, self.lock_id,
                b.Lease(200.0, 13840.0),
                {"creator_pid": 201, "creator_birth": "creator-birth",
                 "pid": 202, "birth": "child-birth"},
                self.ledger, host_modules=child_modules)
        self.assertTrue(receipt_path.is_file())

    def test_stat_metadata_mutation_fails_same_stage(self):
        parent = self.parent()
        source = self.root / self.source["path"]
        source.write_bytes(source.read_bytes() + b"changed")
        with self.assertRaisesRegex(b.FrozenBridge09Error, "metadata changed"):
            b.assert_stage_current(self.root, parent, self.graph)

    def test_successor_requires_one_row_and_completion_keeps_predecessor_immutable(self):
        parent = self.parent()
        successor_path = self.root / "ledger-after.jsonl"
        successor_path.write_bytes(self.ledger_path.read_bytes() + b.canonical_json({"attempt_id": "a1", "status": "completed"}))
        successor = b.build_successor_stage(
            self.root, predecessor=parent, index=1,
            ledger_after={"path": "ledger-after.jsonl", "sha256": b.sha256(successor_path.read_bytes()), "rows": 2},
            runtime={"opaque": object()}, graph=self.graph, source_commit="a" * 40,
            plan_commit="b" * 40, contract_sha256="c" * 64,
            sidecars={"phase": self.sidecar}, source_refs=[self.source],
            analyzer_deadline_seconds=13840, created_monotonic=101.0)
        final = b.write_completion(
            self.root, predecessor=parent, successor=successor,
            completion_path="sidecars/completion.json",
            completion={"group_id": "g0", "attempt_id": "g0-attempt-01", "status": "completed"},
            expected_group_id="g0", expected_attempt_id="g0-attempt-01", graph=self.graph)
        self.assertIsInstance(final, b.FinalizedParentStage)
        self.assertEqual(final.predecessor_identity_sha256, parent.identity_sha256)
        self.assertNotIn("sidecars/completion.json", successor.sidecars)
        self.assertIn("sidecars/completion.json", final.sidecars)
        with self.assertRaises(b.FrozenBridge09Error):
            b.write_completion(self.root, predecessor=parent, successor=successor,
                               completion_path="sidecars/second.json",
                               completion={"group_id": "other", "attempt_id": "x"},
                               expected_group_id="g0", expected_attempt_id="g0-attempt-01", graph=self.graph)

    def test_child_uses_fresh_graph_but_same_path_sha_binding(self):
        parent = self.parent()
        child_modules = {name: types.ModuleType(f"fixture_child_{name}") for name in b.REQUIRED_GRAPH_NAMES}
        child_graph = b.load_graph(self.root, self.refs, fixture_modules=child_modules, fixture_only=True)
        child = b.build_child_stage(
            self.root, parent=parent, runtime={"child": object()}, graph=child_graph,
            source_refs=[self.source], child_creator_pid=201, child_creator_birth="creator-birth",
            child_pid=202, child_birth="child-birth", analyzer_deadline_seconds=13840,
            popen_monotonic=200.0, sidecars={"admission": self.sidecar}, ledger=self.ledger)
        remaining = b.assert_child_ready(self.root, child, parent=parent, graph=child_graph, now_monotonic=201.0)
        self.assertEqual(remaining, 14439.0)
        self.assertEqual(child.child_identity["creator_pid"], 201)
        self.assertNotEqual(child.graph, parent.graph)
        bad = dict(self.refs["executor"]); bad["sha256"] = "0" * 64
        refs = dict(self.refs); refs["executor"] = bad
        with self.assertRaises(b.FrozenBridge09Error):
            b.load_graph(self.root, refs, fixture_modules=child_modules, fixture_only=True)

    def test_sidecar_future_and_resource_near_misses_fail_closed(self):
        b.validate_sidecar_transition(allowed={"admission", "phase", "completion"}, present={"admission"}, future={"completion"})
        with self.assertRaises(b.FrozenBridge09Error):
            b.validate_sidecar_transition(allowed={"admission"}, present={"unknown"})
        with self.assertRaises(b.FrozenBridge09Error):
            b.validate_resource_sample(b.ResourceSample(127, 31, 1, 1), free_floor=127, working_cap=30, scratch_cap=24, retention_cap=24)
        b.validate_resource_sample(b.ResourceSample(128, 29, 24, 24), free_floor=127, working_cap=30, scratch_cap=24, retention_cap=24)

    def test_lease_charges_delayed_setup_without_reset(self):
        lease = b.Lease(100.0, 13840.0)
        self.assertEqual(b.validate_lease_progress(lease, now_monotonic=130.0, registered_deadline_seconds=13840.0), 14410.0)
        with self.assertRaises(b.FrozenBridge09Error):
            b.validate_lease_progress(lease, now_monotonic=15000.0, registered_deadline_seconds=13840.0)
        with self.assertRaises(b.FrozenBridge09Error):
            b.validate_lease_progress(lease, now_monotonic=101.0, registered_deadline_seconds=13839.0)

    def test_exact_21_parent_and_20_child_stage_sequence(self):
        ledgers = []
        raw = b""
        for index in range(21):
            raw += b.canonical_json({"attempt_id": f"a{index}", "status": "completed"})
            path = self.root / f"ledger-{index:02d}.jsonl"; path.write_bytes(raw)
            ledgers.append({"path": path.name, "sha256": b.sha256(raw), "rows": index + 1})
        specs = [{"ledger": ledger, "runtime": {"stage": index}, "graph": self.graph,
                  "source_commit": "a" * 40, "plan_commit": "b" * 40,
                  "contract_sha256": "c" * 64, "lock": self.lock_id,
                  "sidecars": {"admission": self.sidecar}, "source_refs": [self.source],
                  "analyzer_deadline_seconds": 13840, "created_monotonic": float(index)}
                 for index, ledger in enumerate(ledgers)]
        parents = b.build_parent_sequence(self.root, specs)
        child_specs = [{"parent": parents[index], "runtime": {"child": index}, "graph": self.graph,
                        "source_refs": [self.source], "child_creator_pid": 300 + index,
                        "child_creator_birth": f"creator-{index}", "child_pid": 400 + index,
                        "child_birth": f"child-{index}", "analyzer_deadline_seconds": 13840,
                        "popen_monotonic": float(index), "sidecars": {"admission": self.sidecar},
                        "ledger": ledgers[index]}
                       for index in range(20)]
        children = b.build_child_sequence(self.root, child_specs, parents)
        self.assertEqual(len(parents), b.PARENT_STAGE_COUNT)
        self.assertEqual(len(children), b.CHILD_STAGE_COUNT)


if __name__ == "__main__":
    unittest.main()
