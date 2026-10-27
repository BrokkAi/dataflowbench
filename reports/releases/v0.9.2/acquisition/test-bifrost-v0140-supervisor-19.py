#!/usr/bin/env python3
"""Fixture-only staged controller regressions for BF19."""
from __future__ import annotations

import importlib.util
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


fixture_mod = load("bridge14_fixture_tests_for_supervisor", BASE / "test-bifrost-v0140-frozen-parser-14.py")
supervisor = load("supervisor19_test", BASE / "bifrost-v0140-supervisor-19.py")


class Supervisor19Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_mod.BridgeFixture("test_complete_graph_is_bound_and_serialization_is_rejected")
        self.fixture.setUp()
        target = self.fixture.root / supervisor.STAGE_BRIDGE_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BASE / "bifrost-v0140-frozen-bridge-14.py", target)

    def tearDown(self):
        self.fixture.tearDown()

    def test_parent_ready_and_child_ready_are_explicit_stage_calls(self):
        parent = self.fixture.parent()
        result = supervisor.staged_parent_ready(self.fixture.root, parent, self.fixture.graph, index=0,
                                                stage_bridge=fixture_mod.b)
        self.assertEqual(result["status"], "ready")
        child_modules = {name: type(module)(f"fixture_child_{name}")
                         for name, module in self.fixture.modules.items()}
        graph = fixture_mod.b.load_graph(self.fixture.root, self.fixture.refs,
                                         fixture_modules=child_modules, fixture_only=True)
        child = fixture_mod.b.build_child_stage(
            self.fixture.root, parent=parent, runtime={"child": object()}, graph=graph,
            source_refs=[self.fixture.source], child_creator_pid=201,
            child_creator_birth="creator", child_pid=202, child_birth="child",
            analyzer_deadline_seconds=13840, popen_monotonic=100,
            sidecars={path: self.fixture.put(path, b"current dispatch") for path in (
                "dispatch/admission.json", "dispatch/phase.json", "dispatch/supervisor-permit.json")},
            ledger=self.fixture.ledger)
        child_result = supervisor.staged_child_ready(self.fixture.root, child, parent, graph, now_monotonic=101,
                                                     stage_bridge=fixture_mod.b)
        self.assertEqual(child_result["status"], "ready")
        self.assertGreater(child_result["startup_remaining_seconds"], 0)

    def test_graph_loader_requires_complete_core_binding(self):
        core = {"runtime_module_graph": self.fixture.refs}
        graph = fixture_mod.b.prepare_graph(self.fixture.root, core,
                                            host_modules=self.fixture.modules)
        supervisor.validate_stage_graph(graph)
        self.assertEqual(graph.graph_sha256, self.fixture.graph.graph_sha256)
        with self.assertRaises(fixture_mod.b.FrozenBridge14Error):
            fixture_mod.b.prepare_graph(self.fixture.root, {},
                                        host_modules=self.fixture.modules)

    def test_sequence_cardinality_and_parent_child_identity_are_strict(self):
        parent = self.fixture.parent()
        with self.assertRaises(supervisor.Supervisor19Error):
            supervisor.validate_stage_sequence(self.fixture.root, [parent], [], [self.fixture.graph])
        self.assertEqual(supervisor.PARENT_STAGE_COUNT, 21)
        self.assertEqual(supervisor.CHILD_STAGE_COUNT, 20)


if __name__ == "__main__":
    unittest.main()
