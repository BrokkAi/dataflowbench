"""Synthetic regression for archive-aware live and terminal source gates."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import packet
import stage_runtime
import supervisor
import test_adapter_08 as fixtures


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class FreshGateArchiveScopeTests(unittest.TestCase):
    def _case(self, root: Path):
        graph_refs = {
            "executor": {"path": "runtime/executor.py", "sha256": "1" * 64},
            "stage_runtime11": {"path": "runtime/stage_runtime.py", "sha256": "2" * 64},
        }
        core = {
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract": {"path": "reports/current/contract.json", "sha256": "c" * 64},
            "qualification": {"path": "reports/current/qualification.json", "sha256": "d" * 64},
            "runtime_module_graph": graph_refs,
            "lock_path": "/private/tmp/joern05-fresh-gate-test.lock",
        }
        historical_core = {"contract": {"path": "reports/historical/contract.json",
                                         "sha256": "e" * 64}}
        normalized, proof, direct, _core, _historical, closure = \
            fixtures.CurrentSourceSnapshotScopeTests()._fixture(
                root, current_core=core, historical_core=historical_core)
        return core, historical_core, normalized, proof, direct, closure

    def _graph(self, root: Path, core: dict, historical_core: dict,
               normalized: dict, proof: dict, closure: dict):
        events = []
        source_guard_calls = []
        source_file_calls = []

        class Executor:
            def _assert_source_snapshot(inner, candidate_root, commit, runner_sha, inputs):
                events.append("source-guard")
                source_guard_calls.append((candidate_root, commit, runner_sha, list(inputs)))
                for item in inputs:
                    inner._source_file(candidate_root, commit, item["path"], item["sha256"])
                return {"source_paths_checked": len(inputs)}

            def _source_file(inner, candidate_root, commit, path, expected):
                source_file_calls.append((candidate_root, commit, path, expected))
                return b"git-blob"

            def _check_resources(inner, candidate_root, minimum):
                events.append(("resources", candidate_root, minimum))

            def _process_table(inner):
                events.append("process-table")
                return []

            def _contenders(inner, table):
                events.append("contenders")
                return []

        executor = Executor()
        objects = {
            "modules": {"executor": executor},
            "validated": normalized,
            "current_core": core,
            "current_source_proof": proof,
            "current_source_input_closure": closure,
        }
        actual = SimpleNamespace(
            root=root,
            graph=None,
            objects=objects,
            diagnostic={
                "current_source_proof_sha256": sha(packet.canonical(proof)),
                "current_source_input_closure_sha256": sha(packet.canonical(closure)),
            },
        )

        class LockProxy:
            def __init__(self, candidate_root, stream):
                self.path = stream.name

            def assert_live(self, expected):
                events.append("lock")
                if self.path != expected:
                    raise AssertionError("wrong lock path")

        def configuration_live_gate(admission, candidate_executor, candidate_root,
                                    candidate_core, lock, validated, source_commit, phase):
            events.append("configuration-gate")
            lock.assert_live(candidate_core["lock_path"])
            admission._live_resources(candidate_root, candidate_core)
            candidate_executor._check_resources(candidate_root, 1024)
            table = candidate_executor._process_table()
            if candidate_executor._contenders(table):
                raise AssertionError("contender gate changed")
            candidate_executor._assert_source_snapshot(
                candidate_root, source_commit,
                validated["plan"]["runner_source_sha256"],
                validated["source_inputs"])
            events.append("configuration-gate-passed")
            return {"status": "live-gates-passed", "phase": phase,
                    "source_snapshot_checked": True}

        class Controller:
            _HeldLockProxy = LockProxy
            _configuration_live_gate = staticmethod(configuration_live_gate)

            @staticmethod
            def _terminal_continuation_safety(candidate_root, candidate_core,
                                              terminal, terminal_sha256,
                                              candidate_executor, candidate_admission,
                                              validated, lock, *, protocol, disk):
                events.append("terminal-safety")
                lock.assert_live(candidate_core["lock_path"])
                candidate_admission._live_resources(candidate_root, candidate_core)
                candidate_executor._assert_source_snapshot(
                    candidate_root, candidate_core["source_commit"],
                    validated["plan"]["runner_source_sha256"],
                    validated["source_inputs"])
                events.append("terminal-safety-passed")
                return {"status": "terminal-safety-passed",
                        "terminal": terminal, "sha256": terminal_sha256,
                        "protocol": protocol, "disk": disk}

            @staticmethod
            def _hashed_bifrost_contenders(table):
                events.append("hashed-contenders")
                return []

        admission = SimpleNamespace(_live_resources=lambda candidate_root, candidate_core:
                                    events.append("admission-resources"))

        class RuntimeLoaders:
            PRODUCTION_MODULE_NAMES = ("executor", "checker", "configuration")

            @contextlib.contextmanager
            def scoped_runtime_loaders(self, candidate_root, *, executor, graph,
                                       module_names):
                events.append("loader-scope-enter")
                if (candidate_root != root or executor is not actual.objects["modules"]["executor"] or
                        graph is not graph_value or
                        module_names != self.PRODUCTION_MODULE_NAMES):
                    raise AssertionError("runtime loader scope changed")
                try:
                    yield
                finally:
                    events.append("loader-scope-exit")

        class FrozenBridge:
            def assert_stage_current(self, candidate_root, stage, graph):
                events.append("stage-current")
                if candidate_root != root or graph is not graph_value:
                    raise AssertionError("stage validation escaped root/graph")

            def runtime_objects(self, stage):
                events.append("runtime-objects")
                return actual

        modules = {
            "bridge19": FrozenBridge(),
            "supervisor24": Controller(),
            "admission24": admission,
            "executor": executor,
            "joern05_stage_runtime": stage_runtime,
            "runtime_loaders24": RuntimeLoaders(),
            "joern05_protocol": object(),
            "disk_guard": object(),
        }

        class Graph:
            def module(self, name):
                return modules[name]

        graph_value = Graph()
        actual.graph = graph_value
        stream = SimpleNamespace(name=core["lock_path"], fileno=lambda: 19)
        return (graph_value, actual, executor, events, source_guard_calls,
                source_file_calls, stream)

    def test_fresh_gate_retains_live_gates_and_scopes_only_archived_git_reads(self):
        with tempfile.TemporaryDirectory(prefix="joern05-fresh-gate-") as temp:
            root = Path(temp).resolve()
            core, historical, normalized, proof, direct, closure = self._case(root)
            (graph, actual, executor, events, guard_calls, source_files,
             stream) = self._graph(root, core, historical, normalized, proof, closure)
            stage = object()
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical):
                result = supervisor._fresh_gate(root, core, graph, stage, stream)

            self.assertEqual(result["status"], "live-gates-passed")
            self.assertIs(guard_calls[0][0], root)
            self.assertEqual(guard_calls[0][1:3],
                             (core["source_commit"],
                              normalized["plan"]["runner_source_sha256"]))
            self.assertEqual(guard_calls[0][3], [{**direct, "role": "release-input"}])
            self.assertEqual(len(source_files), 1)
            self.assertEqual(source_files[0][2], direct["path"])
            self.assertIs(executor._assert_source_snapshot.__func__,
                          type(executor)._assert_source_snapshot)
            self.assertIn("configuration-gate", events)
            self.assertEqual(sum(isinstance(item, tuple) and item[0] == "resources"
                                 for item in events), 2)
            self.assertIn("lock", events)
            self.assertIn("admission-resources", events)
            self.assertIn("process-table", events)
            self.assertIn("contenders", events)
            self.assertIn("hashed-contenders", events)

    def test_changed_archive_member_fails_before_gate_pass_and_outer_checks(self):
        with tempfile.TemporaryDirectory(prefix="joern05-fresh-gate-mutated-") as temp:
            root = Path(temp).resolve()
            core, historical, normalized, proof, _direct, closure = self._case(root)
            archived = proof["archived_member_refs"][0]
            (root / archived["path"]).write_bytes(b"tampered after proof")
            (graph, _actual, _executor, events, _guard_calls, _source_files,
             stream) = self._graph(root, core, historical, normalized, proof, closure)
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical):
                with self.assertRaises(packet.AdapterError):
                    supervisor._fresh_gate(root, core, graph, object(), stream)
            self.assertIn("configuration-gate", events)
            self.assertNotIn("configuration-gate-passed", events)
            self.assertNotIn("source-guard", events)
            self.assertNotIn("hashed-contenders", events)

    def test_diagnostic_hash_mismatch_fails_closed_before_live_gate(self):
        with tempfile.TemporaryDirectory(prefix="joern05-fresh-gate-binding-") as temp:
            root = Path(temp).resolve()
            core, historical, normalized, proof, _direct, closure = self._case(root)
            (graph, actual, _executor, events, _guard_calls, _source_files,
             stream) = self._graph(root, core, historical, normalized, proof, closure)
            actual.diagnostic["current_source_input_closure_sha256"] = "0" * 64
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical):
                with self.assertRaises(packet.AdapterError):
                    supervisor._fresh_gate(root, core, graph, object(), stream)
            self.assertNotIn("configuration-gate", events)

    def test_terminal_safety_runs_inside_loader_and_archive_aware_scopes(self):
        with tempfile.TemporaryDirectory(prefix="joern05-terminal-source-scope-") as temp:
            root = Path(temp).resolve()
            core, historical, normalized, proof, direct, closure = self._case(root)
            (graph, actual, executor, events, guard_calls, source_files,
             stream) = self._graph(root, core, historical, normalized, proof, closure)
            original_guard = executor._assert_source_snapshot
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical):
                result = supervisor._terminal_continuation_safety_with_scopes(
                    root, core, graph, actual,
                    {"status": "completed", "attempt_id": "terminal-test"},
                    "a" * 64, stream)

            self.assertEqual(result["status"], "terminal-safety-passed")
            self.assertEqual(result["terminal"]["attempt_id"], "terminal-test")
            self.assertEqual(guard_calls[0][3], [{**direct, "role": "release-input"}])
            self.assertEqual(len(source_files), 1)
            self.assertEqual(source_files[0][2], direct["path"])
            self.assertLess(events.index("loader-scope-enter"),
                            events.index("terminal-safety"))
            self.assertLess(events.index("terminal-safety"),
                            events.index("loader-scope-exit"))
            self.assertIs(executor._assert_source_snapshot.__self__,
                          original_guard.__self__)
            self.assertIs(executor._assert_source_snapshot.__func__,
                          original_guard.__func__)

    def test_terminal_archive_mutation_fails_inside_loader_scope_before_safety(self):
        with tempfile.TemporaryDirectory(prefix="joern05-terminal-source-mutated-") as temp:
            root = Path(temp).resolve()
            core, historical, normalized, proof, _direct, closure = self._case(root)
            archived = proof["archived_member_refs"][0]
            (root / archived["path"]).write_bytes(b"tampered before terminal check")
            (graph, actual, _executor, events, _guard_calls, _source_files,
             stream) = self._graph(root, core, historical, normalized, proof, closure)
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical):
                with self.assertRaises(packet.AdapterError):
                    supervisor._terminal_continuation_safety_with_scopes(
                        root, core, graph, actual,
                        {"status": "completed", "attempt_id": "terminal-test"},
                        "a" * 64, stream)
            self.assertIn("loader-scope-enter", events)
            self.assertIn("loader-scope-exit", events)
            self.assertIn("terminal-safety", events)
            self.assertNotIn("terminal-safety-passed", events)


if __name__ == "__main__":
    unittest.main()
