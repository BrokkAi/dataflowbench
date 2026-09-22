#!/usr/bin/env python3
"""Focused, analyzer-free tests for the Swift v2 additions runner."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "run_swift_v2_additions", ROOT / "scripts/run-swift-v2-additions.py"
)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class SwiftV2RunnerTests(unittest.TestCase):
    def _base_tree(self, root, manifest_entries=None):
        for relative in (
            "adapters/codeql/swift-v2",
            "scripts",
            "src/adapters",
        ):
            (root / relative).mkdir(parents=True, exist_ok=True)
        (root / "scripts/run-swift-v2-additions.py").write_text("runner\n")
        (root / "src/adapters/swift_v2.rs").write_text("module\n")
        entries = manifest_entries or ["adapters/codeql/swift-v2/input.txt"]
        (root / "adapters/codeql/swift-v2/input.txt").write_text("bound\n")
        manifest = root / "adapters/codeql/swift-v2/configuration-files.json"
        manifest.write_text(json.dumps(entries) + "\n")
        return manifest

    def test_configuration_path_duplicate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(root, ["adapters/codeql/swift-v2/input.txt"] * 2)
            with mock.patch.object(runner, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    runner.configuration_paths("codeql")

    def test_configuration_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(root, ["../outside.txt"])
            with mock.patch.object(runner, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "unsafe path"):
                    runner.configuration_paths("codeql")

    def test_configuration_path_missing_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(root, ["adapters/codeql/swift-v2/missing.txt"])
            with mock.patch.object(runner, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "missing input"):
                    runner.configuration_paths("codeql")

    def test_configuration_hash_changes_when_only_file_bytes_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(root)
            with mock.patch.object(runner, "ROOT", root):
                paths = runner.configuration_paths("codeql")
                first = runner.configuration_hash(paths)
                # Rust hashes sorted path bytes followed immediately by file bytes.
                expected = hashlib.sha256(
                    b"".join(path.encode() + (root / path).read_bytes() for path in sorted(paths))
                ).hexdigest()
                self.assertEqual(first, expected)
                (root / "adapters/codeql/swift-v2/input.txt").write_bytes(b"bound-mutated\n")
                second = runner.configuration_hash(paths)
                self.assertNotEqual(first, second)

    def test_verify_configuration_requires_result_activation_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(
                root,
                [
                    "adapters/codeql/swift-v2/query.ql",
                    "adapters/codeql/swift-v2/evidence.json",
                ],
            )
            bound_query = root / "adapters/codeql/swift-v2/query.ql"
            bound_evidence = root / "adapters/codeql/swift-v2/evidence.json"
            bound_query.write_text("query\n")
            bound_evidence.write_text("evidence\n")
            base = root / "adapters/codeql/swift-v2"
            ids = [f"case-{index:02d}" for index in range(14)]
            cases = [
                (
                    root / f"case-{index:02d}.json",
                    {
                        "id": case_id,
                        "model_profile": "tool-native" if index < 12 else "benchmark-controlled",
                    },
                )
                for index, case_id in enumerate(ids)
            ]
            partition = {
                "status": "resolved",
                "tool": "codeql",
                "population": "swift-synthetic-v2",
                "fixture_revision": "sha256:test",
                "budget": {"peak_memory_mb": 512, "wall_clock_seconds": 60},
                "cases": {
                    case_id: {
                        "decision": "unsupported" if index < 12 else "execute",
                        "reason": "committed decision",
                        "evidence": ["adapters/codeql/swift-v2/evidence.json"],
                    }
                    for index, case_id in enumerate(ids)
                },
            }
            activation = {
                "status": "active",
                "tool": "codeql",
                "scope": "swift-v2-additions",
                "executable_scope": "result-language-extension",
                "native_scope": "committed-capability-decisions-only",
                "version": "test",
                "build_identity": "test-build",
                "query_sha256": {
                    "adapters/codeql/swift-v2/query.ql": hashlib.sha256(bound_query.read_bytes()).hexdigest()
                },
                "evidence_sha256": {
                    "adapters/codeql/swift-v2/evidence.json": hashlib.sha256(bound_evidence.read_bytes()).hexdigest()
                },
            }
            (base / "partition.json").write_text(json.dumps(partition) + "\n")
            (base / "activation.json").write_text(json.dumps(activation) + "\n")
            population = {"population": "swift-synthetic-v2", "fixture_revision": "sha256:test"}
            with mock.patch.object(runner, "ROOT", root):
                paths, _, _ = runner.verify_configuration("codeql", population, cases, check_git=False)
                self.assertIn("adapters/codeql/swift-v2/query.ql", paths)
                activation["native_scope"] = "active"
                (base / "activation.json").write_text(json.dumps(activation) + "\n")
                with self.assertRaisesRegex(ValueError, "activation promotion"):
                    runner.verify_configuration("codeql", population, cases, check_git=False)

    def test_verify_configuration_separates_dirty_git_from_missing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._base_tree(root)
            base = root / "adapters/codeql/swift-v2"
            ids = [f"case-{index:02d}" for index in range(14)]
            (base / "partition.json").write_text(
                json.dumps({
                    "status": "resolved", "tool": "codeql", "population": "swift-synthetic-v2",
                    "fixture_revision": "sha256:test",
                    "budget": {"peak_memory_mb": 512, "wall_clock_seconds": 60},
                    "cases": {case_id: {"decision": "unsupported" if index < 12 else "execute",
                                         "reason": "reason", "evidence": ["adapters/codeql/swift-v2/input.txt"]}
                              for index, case_id in enumerate(ids)},
                }) + "\n"
            )
            evidence = base / "input.txt"
            activation = {"status": "active", "tool": "codeql", "scope": "swift-v2-additions",
                          "executable_scope": "result-language-extension",
                          "native_scope": "committed-capability-decisions-only", "version": "test",
                          "build_identity": "test", "query_sha256": {},
                          "evidence_sha256": {"adapters/codeql/swift-v2/input.txt": hashlib.sha256(evidence.read_bytes()).hexdigest()}}
            (base / "activation.json").write_text(json.dumps(activation) + "\n")
            cases = [(root / f"case-{index:02d}.json", {"id": case_id,
                       "model_profile": "tool-native" if index < 12 else "benchmark-controlled"})
                     for index, case_id in enumerate(ids)]
            population = {"population": "swift-synthetic-v2", "fixture_revision": "sha256:test"}
            with mock.patch.object(runner, "ROOT", root):
                with mock.patch.object(runner.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["git", "diff"])):
                    with self.assertRaises(subprocess.CalledProcessError):
                        runner.verify_configuration("codeql", population, cases, check_git=True)
                (base / "input.txt").unlink()
                with self.assertRaisesRegex(ValueError, "missing input"):
                    runner.configuration_paths("codeql")

    def test_native_activation_does_not_promote_native_capability(self):
        activation = runner.read(ROOT / "adapters/codeql/swift-v2/activation.json")
        self.assertEqual(activation["scope"], "swift-v2-additions")
        self.assertEqual(activation["executable_scope"], "result-language-extension")
        self.assertEqual(activation["native_scope"], "committed-capability-decisions-only")
        self.assertNotEqual(activation["native_scope"], "active")

    def test_checked_distinguishes_budget_timeout_from_value_failure(self):
        with self.assertRaises(runner.BudgetExceeded):
            runner.checked({"timed_out": True, "exit_status": None, "cleanup_status": "tracked-processes-stopped"}, "analysis")
        with self.assertRaisesRegex(ValueError, "invocation failed"):
            runner.checked({"timed_out": False, "exit_status": 17, "cleanup_status": "tracked-processes-stopped"}, "analysis")
        with self.assertRaisesRegex(ValueError, "cleanup uncertain"):
            runner.checked({"timed_out": False, "exit_status": 0, "cleanup_status": "uncertain"}, "analysis")

    def _sarif(self, source_line=4, sink_line=5, flow_line=None):
        def location(line):
            return {"physicalLocation": {"artifactLocation": {"uri": "main.swift"},
                                          "region": {"startLine": line}}}
        results = [
            {"ruleId": "dfb/swift-result-v2-endpoints",
             "message": {"text": "Benchmark source endpoint observed."},
             "locations": [location(source_line)]},
            {"ruleId": "dfb/swift-result-v2-endpoints",
             "message": {"text": "Benchmark sink endpoint observed."},
             "locations": [location(sink_line)]},
        ]
        if flow_line is not None:
            results.append({"ruleId": "dfb/swift-result-v2-flow",
                            "message": {"text": "Controlled input reaches the benchmark sink."},
                            "locations": [location(flow_line)]})
        return {"runs": [{"invocations": [{"executionSuccessful": True}], "results": results}]}

    def test_observe_sarif_accepts_exact_controls_and_rejects_near_misses(self):
        case = {"source_anchors": [{"line_hint": 4}], "sink_anchors": [{"line_hint": 5}]}
        observed = runner.observe_sarif(self._sarif(flow_line=5), case)
        self.assertTrue(observed["flow_observed"])
        with self.assertRaisesRegex(ValueError, "exact endpoint mismatch"):
            runner.observe_sarif(self._sarif(source_line=3), case)
        with self.assertRaisesRegex(ValueError, "exact sink"):
            runner.observe_sarif(self._sarif(flow_line=6), case)


if __name__ == "__main__":
    unittest.main()
