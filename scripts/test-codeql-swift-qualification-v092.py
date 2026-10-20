#!/usr/bin/env python3
"""Focused raw-table replay tests for the v0.9.2 CodeQL Swift controls."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import codeql_swift_qualification_v092 as replay
import swift_common_population_v2 as common
import swift_normal_runner_v092 as runner
import v092_qualification as qualification


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def reference(root: Path, path: Path) -> dict:
    path = path.resolve()
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": digest(path)}


class CodeQLQualificationReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        population, rows, swift_rows, cases, population_sha = common.load_common_population(ROOT)
        cls.population = population
        cls.rows = rows
        cls.swift_rows = swift_rows
        cls.cases = cases
        cls.population_sha = population_sha
        cls.case_paths = {row["id"]: row["path"] for row in rows}

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self._copy_entry_inputs()
        self._copy_activation_inputs()
        self.identity = {
            "tool": "codeql", "tool_version": "2.27.2",
            "tool_build_identity": "codeql:d7b185e374bfe18c0484dac07a521a810eb9c4fb;swift-extractor:" + "a" * 64 +
                                   ";schema:" + "b" * 64 + ";packs:" + "c" * 64,
            "adapter_version": "swift-normal-v092",
        }
        self.components = [{"name": "codeql-swift-packs", "path": str(self.root / "runtime-packs"), "sha256": "c" * 64}]
        self.plan = {
            "schema": "swift-common-execution-plan/v092", "profile": "v0.9.2", "engine": "codeql",
            "release_group_id": replay.GROUP_ID, "population_sha256": self.population_sha,
            "fixture_revision": self.population["fixture_revision"], "identity": self.identity,
            "identity_components": self.components,
            "runtime": {"codeql": "/runtime/codeql", "compiler": "/runtime/swiftc", "sdk": "/runtime/sdk",
                        "extractor_root": "/runtime/extractor", "packs": "/runtime/packs",
                        "swift_target": "arm64-apple-macosx26.5",
                        "pins": {"cli_build": "d7b185e374bfe18c0484dac07a521a810eb9c4fb", "schema_sha256": "b" * 64}},
            "codeql_packs": {"root": "/runtime/packs", "runtime_tree_component": "codeql-swift-packs",
                             "runtime_tree_manifest_sha256": "c" * 64},
            "query_root": "adapters/codeql/v0.9.2/swift", "configurations": {"patched-codeql": []},
            "cases": {}, "execution_contract": {"path": "contracts/swift.json", "sha256": "d" * 64},
        }
        self.projection = qualification.plan_projection_sha256(self.plan)
        self.control = self._make_control_plan()
        self.control_path = self.root / "reports/releases/v0.9.2/qualification/codeql/control-plan.json"
        write_json(self.control_path, self.control)
        self.control_ref = reference(self.root, self.control_path)
        self.plan["qualification_control_plan"] = self.control_ref
        self.plan["qualification_control_projection_sha256"] = self.projection
        self.patch_common = patch.object(common, "load_common_population", side_effect=self._load_population)
        self.patch_common.start()
        self.addCleanup(self.patch_common.stop)

    def _load_population(self, _root=ROOT):
        copied_cases = copy.deepcopy(self.cases)
        for case_id, case in copied_cases.items():
            case["path"] = self.case_paths[case_id]
        return self.population, self.rows, self.swift_rows, copied_cases, self.population_sha

    def _copy_entry_inputs(self) -> None:
        source = ROOT / "adapters/codeql/swift-entry-extractor-v1"
        destination = self.root / "adapters/codeql/swift-entry-extractor-v1"
        shutil.copytree(source / "controls", destination / "controls")
        shutil.copytree(source / "queries", destination / "queries")
        shutil.copyfile(source / "control-manifest.json", destination / "control-manifest.json")

    def _copy_activation_inputs(self) -> None:
        for case_id in replay.MODEL_EXPECTED.keys() | replay.SANITIZER_EXPECTED.keys():
            case_path = ROOT / self.case_paths[case_id]
            destination = self.root / case_path.parent.relative_to(ROOT)
            shutil.copytree(case_path.parent, destination)
        source_root = ROOT / "adapters/codeql/swift-normal-v1/queries/standard"
        query_root = self.root / "adapters/codeql/v0.9.2/swift/queries/standard"
        query_root.mkdir(parents=True, exist_ok=True)
        for name in ("kernel-flow.ql", "modeling-flow.ql"):
            shutil.copyfile(source_root / name, query_root / name)
        production = (query_root / "modeling-flow.ql").read_text()
        sanitizer_barrier = "predicate isBarrier(DataFlow::Node n) { sanitizer(n) or summaryBarrier(n) }"
        no_sanitizer_barrier = "predicate isBarrier(DataFlow::Node n) { summaryBarrier(n) }"
        assert production.count(sanitizer_barrier) == 1
        off = query_root / "modeling-flow-sanitizer-off.ql"
        off.write_text(production.replace(sanitizer_barrier, no_sanitizer_barrier, 1))
        patch_path = self.root / "adapters/codeql/v0.9.2/swift/controls/modeling-flow-sanitizer-off.patch"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text("--- modeling-flow.ql\n+++ modeling-flow-sanitizer-off.ql\n@@ -7 +7 @@\n- " + sanitizer_barrier + "\n+ " + no_sanitizer_barrier + "\n")

    def _make_control_plan(self) -> dict:
        entry_ids = list(replay.ENTRY_IDS)
        entry_queries = {
            role: reference(self.root, self.root / "adapters/codeql/swift-entry-extractor-v1/queries" / (role + ".ql"))
            for role in replay.ENTRY_QUERY_ROLES
        }
        qroot = "adapters/codeql/v0.9.2/swift/queries/standard"
        activation = {
            "model_activation": {"off": reference(self.root, self.root / qroot / "kernel-flow.ql"),
                                 "on": reference(self.root, self.root / qroot / "modeling-flow.ql")},
            "sanitizer_activation": {"off": reference(self.root, self.root / qroot / "modeling-flow-sanitizer-off.ql"),
                                     "on": reference(self.root, self.root / qroot / "modeling-flow.ql")},
        }
        counterfactual = {
            "production_query": activation["sanitizer_activation"]["on"],
            "counterfactual_query": activation["sanitizer_activation"]["off"],
            "diff": reference(self.root, self.root / "adapters/codeql/v0.9.2/swift/controls/modeling-flow-sanitizer-off.patch"),
        }
        return {
            "schema": "analyzer-qualification-control-plan/v092", "group_id": replay.GROUP_ID,
            "execution_plan_projection_sha256": self.projection, "identity": self.identity,
            "identity_components": self.components, "population_sha256": self.population_sha,
            "fixture_revision": self.population["fixture_revision"], "case_arm_budget_seconds": 75,
            "extraction_budget_seconds": 150, "total_budget_seconds": 5400,
            "scratch_allowance_bytes": 4 * 1024**3,
            "entry_extractor": {"control_ids": entry_ids,
                                "controls": {name: "adapters/codeql/swift-entry-extractor-v1/controls/" + name + "/main.swift" for name in entry_ids},
                                "queries": entry_queries},
            "activation_queries": activation,
            "sanitizer_counterfactual": counterfactual,
            "model_activation": {"case_ids": sorted(replay.MODEL_EXPECTED)},
            "sanitizer_activation": {"case_ids": sorted(replay.SANITIZER_EXPECTED)},
        }

    def _write_command_set(self, directory: Path, phases: tuple[str, ...], query_paths: dict[str, Path],
                           fixture_files: list[str]) -> list[dict]:
        source = (directory / "source").resolve()
        db = (directory / "database").resolve()
        runtime = self.plan["runtime"]
        compile_argv = [runtime["compiler"], "-swift-version", "6", "-Onone", "-sdk", runtime["sdk"],
                        "-target", runtime["swift_target"], "-module-name", "DataFlowBenchTaintSwift",
                        "-module-cache-path", str((directory / "cache").resolve()),
                        *[str((source / name).resolve()) for name in fixture_files],
                        "-o", str((directory / "never-executed").resolve())]
        expected = {
            "database-create": [runtime["codeql"], "database", "create", str(db), "--language=swift",
                                "--search-path=" + runtime["extractor_root"], "--source-root=" + str(source),
                                "--threads=2", "--ram=2048", "--command=" + __import__("shlex").join(compile_argv)],
            "resolve-database": [runtime["codeql"], "resolve", "database", "--format=json", str(db)],
        }
        for role, query in query_paths.items():
            bqrs = str((directory / (role + ".bqrs")).resolve())
            expected[role + "-query"] = [runtime["codeql"], "query", "run", str(query.resolve()),
                                          "--database=" + str(db), "--output=" + bqrs,
                                          "--additional-packs=" + runtime["packs"], "--threads=2", "--ram=2048"]
            expected[role + "-decode"] = [runtime["codeql"], "bqrs", "decode", bqrs, "--format=json",
                                           "--output=" + str((directory / (role + ".json")).resolve())]
        refs = []
        for phase in phases:
            record = {"phase_id": phase, "role": "extraction" if phase == "database-create" else "analysis",
                      "argv": expected[phase], "cwd": str(self.root), "exit_status": 0,
                      "timed_out": False, "cleanup_status": "tracked-processes-stopped",
                      "elapsed_seconds": 0.01, "deadline_seconds": 1.0}
            path = directory / (phase + ".command.json")
            write_json(path, record)
            refs.append(reference(self.root, path))
        return refs

    def _entry_evidence(self) -> dict:
        records = []
        for control_id in replay.ENTRY_IDS:
            fixture = self.root / self.control["entry_extractor"]["controls"][control_id]
            directory = self.root / "reports/releases/v0.9.2/qualification/synthetic/entry" / control_id
            (directory / "source").mkdir(parents=True)
            shutil.copyfile(fixture, directory / "source/main.swift")
            main = str((directory / "source/main.swift").resolve())
            entry_rows = [[main, "DataFlowBenchTaintSwift", 0, 1, 1, 1]]
            endpoint_rows = [[main, 1, 1, "source", 1, 1, 1, 1, 1, "DataFlowBenchTaintSwift:dfb_source()"],
                             [main, 2, 1, "sink", 1, 1, 1, 1, 1, "DataFlowBenchTaintSwift:dfb_sink(_:)" ]]
            flow_rows = [[main, 1, main, 2, 1]] if replay.ENTRY_EXPECTED[control_id] == "reached" else []
            rows = {"entry": entry_rows, "diagnostics": endpoint_rows, "kernel-flow": flow_rows}
            query_refs = {}
            query_paths = {role: self.root / self.control["entry_extractor"]["queries"][role]["path"]
                           for role in replay.ENTRY_QUERY_ROLES}
            for role, tuples in rows.items():
                path = directory / (role + ".json")
                write_json(path, {"#select": {"tuples": tuples}})
                query_refs[role] = reference(self.root, path)
            commands = self._write_command_set(directory, replay.ENTRY_PHASES, query_paths, ["main.swift"])
            observation = replay.swift_entry_observation.classify(entry_rows, endpoint_rows, flow_rows)
            raw = {"schema": "codeql-entry-control-raw/v092", "group_id": replay.GROUP_ID,
                   "control_id": control_id, "execution_plan_projection_sha256": self.projection,
                   "identity": self.identity, "identity_components": self.components,
                   "capture_root": str(self.root), "capture_output_dir": str(directory),
                   "fixture_sha256": digest(fixture), "source_files": {"main.swift": reference(self.root, fixture)},
                   "commands": commands, "query_outputs": query_refs, "entry_rows": entry_rows,
                   "exact_endpoint_rows": endpoint_rows, "flow_rows": flow_rows, "observation": observation,
                   "capture_state": "complete"}
            raw_path = directory / "raw.json"
            write_json(raw_path, raw)
            records.append({"control_id": control_id, "raw": reference(self.root, raw_path), "observed": observation})
        observations = {row["control_id"]: row["observed"]["diagnostic"] for row in records}
        assessment = {"status": "qualified", "execution_eligible": True, "strict_qualified": True,
                      "case_count": 10, "observations": observations, "known_limit_deltas": {}, "scored_activation": False}
        return {"schema": "codeql-entry-extractor-evidence/v092", "group_id": replay.GROUP_ID,
                "identity": self.identity, "identity_components": self.components,
                "execution_plan_projection_sha256": self.projection, "controls": records, "assessment": assessment}

    def _activation_evidence(self, dimension: str) -> dict:
        expected = replay.MODEL_EXPECTED if dimension == "model_activation" else replay.SANITIZER_EXPECTED
        records = []
        query_profiles = self.control["activation_queries"][dimension]
        for case_id, arms in expected.items():
            case = self.cases[case_id]
            case["path"] = self.case_paths[case_id]
            case_path = self.root / case["path"]
            for arm, wanted in arms.items():
                directory = self.root / "reports/releases/v0.9.2/qualification/synthetic" / dimension / case_id / arm
                (directory / "source").mkdir(parents=True)
                for name in case["fixture_files"]:
                    shutil.copyfile(case_path.parent / name, directory / "source" / name)
                source_file, source_line = replay._marker_line(self.root, case, case["source_anchors"][0]["marker"])
                sink_file, sink_line = replay._marker_line(self.root, case, case["sink_anchors"][0]["marker"])
                rows = [[source_file, source_line, sink_file, sink_line, 1]] if wanted == "reached" else []
                output_path = directory / "flow.json"
                write_json(output_path, {"#select": {"tuples": rows}})
                query_path = self.root / query_profiles[arm]["path"]
                commands = self._write_command_set(directory, replay.ACTIVATION_PHASES,
                                                   {"flow": query_path}, case["fixture_files"])
                raw = {"schema": "codeql-activation-control-raw/v092", "group_id": replay.GROUP_ID,
                       "dimension": dimension, "case_id": case_id, "arm": arm,
                       "execution_plan_projection_sha256": self.projection,
                       "identity": self.identity, "identity_components": self.components,
                       "capture_root": str(self.root), "capture_output_dir": str(directory),
                       "fixture_hashes": replay._fixture_hashes(self.root, case), "commands": commands,
                       "query_outputs": {"flow": reference(self.root, output_path)}, "flow_rows": rows,
                       "observed": wanted, "capture_state": "complete"}
                raw_path = directory / "raw.json"
                write_json(raw_path, raw)
                records.append({"case_id": case_id, "arm": arm, "raw": reference(self.root, raw_path), "observed": wanted})
        observations = {}
        for row in records:
            observations.setdefault(row["case_id"], {})[row["arm"]] = row["observed"]
        assessment = {"status": "qualified", "execution_eligible": True, "strict_qualified": True,
                      "case_count": len(expected), "case_arm_count": len(records), "observations": observations,
                      "scored_activation": False, "partition_registered": False}
        return {"schema": "codeql-activation-evidence/v092", "dimension": dimension,
                "group_id": replay.GROUP_ID, "identity": self.identity, "identity_components": self.components,
                "execution_plan_projection_sha256": self.projection, "controls": records, "assessment": assessment}

    def _version_witness(self) -> dict:
        directory = self.root / "reports/releases/v0.9.2/qualification/synthetic/identity"
        directory.mkdir(parents=True)
        stdout = directory / "version.stdout"
        write_json(stdout, {"productName": "CodeQL", "version": "2.27.2", "sha": "d7b185e374bfe18c0484dac07a521a810eb9c4fb"})
        command = directory / "version.command.json"
        write_json(command, {"argv": ["/runtime/codeql", "version", "--format=json"], "cwd": str(self.root),
                             "exit_status": 0, "timed_out": False, "cleanup_status": "tracked-processes-stopped",
                             "elapsed_seconds": 0.01, "deadline_seconds": 30})
        witness = directory / "identity.json"
        write_json(witness, {"observed": self.identity, "capture_root": str(self.root), "command": reference(self.root, command),
                             "stdout": reference(self.root, stdout)})
        return reference(self.root, witness)

    def _valid_replay(self) -> tuple[dict, dict, dict, dict]:
        entry = self._entry_evidence()
        model = self._activation_evidence("model_activation")
        sanitizer = self._activation_evidence("sanitizer_activation")
        refs = {}
        for name, evidence in (("entry_extractor", entry), ("model_activation", model), ("sanitizer_activation", sanitizer)):
            path = self.root / "reports/releases/v0.9.2/qualification/synthetic" / (name + ".json")
            write_json(path, evidence)
            refs[name] = reference(self.root, path)
        run = {"schema": "analyzer-qualification-control-run/v092", "group_id": replay.GROUP_ID,
               "identity": self.identity, "identity_components": self.components,
               "control_plan_sha256": self.control_ref["sha256"],
               "execution_plan_projection_sha256": self.projection,
               "identity_witness": self._version_witness(),
               "dimensions": {**refs, "query_resolution_compile": reference(self.root, self.control_path)},
               "elapsed_seconds": 2.0}
        dims = {name: {"evidence": value} for name, value in refs.items()}
        run["assessment"] = {
            "entry_extractor": replay.replay_entry_controls(self.root, self.plan, self.control, entry),
            "model_activation": replay.replay_activation_dimension(self.root, self.plan, self.control, model,
                                                                    dimension="model_activation"),
            "sanitizer_activation": replay.replay_activation_dimension(self.root, self.plan, self.control, sanitizer,
                                                                        dimension="sanitizer_activation"),
        }
        run["assessment"] = replay.replay_control_run(self.root, self.plan, self.control, run, dims)
        return entry, model, sanitizer, run

    def test_all_raw_entry_model_and_sanitizer_evidence_replays(self):
        entry, model, sanitizer, run = self._valid_replay()
        self.assertEqual(entry["assessment"]["case_count"], 10)
        self.assertEqual(model["assessment"]["case_arm_count"], 4)
        self.assertEqual(sanitizer["assessment"]["case_arm_count"], 8)
        self.assertEqual(run["assessment"]["entry_extractor"]["status"], "qualified")
        self.assertEqual(run["assessment"]["model_activation"]["status"], "qualified")
        self.assertEqual(run["assessment"]["sanitizer_activation"]["status"], "qualified")

    def test_fabricated_control_summary_cannot_override_retained_tables(self):
        _entry, model, _sanitizer, _run = self._valid_replay()
        first = model["controls"][0]
        first["observed"] = "not-reached" if first["observed"] == "reached" else "reached"
        with self.assertRaisesRegex(ValueError, "summary differs from exact anchor replay"):
            replay.replay_activation_dimension(self.root, self.plan, self.control, model,
                                               dimension="model_activation")

    def test_sanitizer_off_query_rejects_any_change_beyond_the_registered_barrier(self):
        off_ref = self.control["activation_queries"]["sanitizer_activation"]["off"]
        off_path = self.root / off_ref["path"]
        off_path.write_text(off_path.read_text().replace("predicate isSink", "predicate modifiedSink", 1))
        replacement_ref = reference(self.root, off_path)
        self.control["activation_queries"]["sanitizer_activation"]["off"] = replacement_ref
        self.control["sanitizer_counterfactual"]["counterfactual_query"] = replacement_ref
        with self.assertRaisesRegex(ValueError, "must differ only by removing the sanitizer barrier"):
            replay._validate_control_plan(self.root, self.plan, self.control)

    def test_command_replay_uses_original_capture_paths_after_snapshot_relocation(self):
        capture_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(capture_tmp.cleanup)
        capture_root = Path(capture_tmp.name).resolve()
        relative = Path("reports/releases/v0.9.2/qualification/relocated/direct-positive")
        output_dir = self.root / relative
        capture_output = capture_root / relative
        (capture_output / "source").mkdir(parents=True)
        fixture = self.root / self.control["entry_extractor"]["controls"]["direct-positive"]
        shutil.copyfile(fixture, capture_output / "source/main.swift")
        captured_queries = {}
        for role in replay.ENTRY_QUERY_ROLES:
            query_ref = self.control["entry_extractor"]["queries"][role]
            source = self.root / query_ref["path"]
            destination = capture_root / query_ref["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            captured_queries[role] = str(destination)

        runtime = self.plan["runtime"]
        source = capture_output / "source"
        database = capture_output / "database"
        compile_argv = [runtime["compiler"], "-swift-version", "6", "-Onone", "-sdk", runtime["sdk"],
                        "-target", runtime["swift_target"], "-module-name", "DataFlowBenchTaintSwift",
                        "-module-cache-path", str(capture_output / "cache"), str(source / "main.swift"),
                        "-o", str(capture_output / "never-executed")]
        expected = {
            "database-create": [runtime["codeql"], "database", "create", str(database), "--language=swift",
                                "--search-path=" + runtime["extractor_root"], "--source-root=" + str(source),
                                "--threads=2", "--ram=2048", "--command=" + __import__("shlex").join(compile_argv)],
            "resolve-database": [runtime["codeql"], "resolve", "database", "--format=json", str(database)],
        }
        for role, query in captured_queries.items():
            bqrs = str(capture_output / (role + ".bqrs"))
            expected[role + "-query"] = [runtime["codeql"], "query", "run", query,
                                          "--database=" + str(database), "--output=" + bqrs,
                                          "--additional-packs=" + runtime["packs"], "--threads=2", "--ram=2048"]
            expected[role + "-decode"] = [runtime["codeql"], "bqrs", "decode", bqrs,
                                           "--format=json", "--output=" + str(capture_output / (role + ".json"))]
        commands = []
        for phase in replay.ENTRY_PHASES:
            command = {
                "phase_id": phase,
                "role": "extraction" if phase == "database-create" else "analysis",
                "argv": expected[phase], "cwd": str(capture_root), "exit_status": 0,
                "timed_out": False, "cleanup_status": "tracked-processes-stopped",
                "elapsed_seconds": 0.01, "deadline_seconds": 150 if phase == "database-create" else 75,
            }
            path = output_dir / (phase + ".command.json")
            write_json(path, command)
            captured = capture_output / path.name
            captured.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, captured)
            commands.append(reference(self.root, path))
        raw = {"capture_root": str(capture_root), "capture_output_dir": str(capture_output), "commands": commands}
        replayed = replay._commands(self.root, self.plan, raw, replay.ENTRY_PHASES, output_dir,
                                    query_paths={role: captured_queries[role] for role in replay.ENTRY_QUERY_ROLES},
                                    fixture_files=["main.swift"])
        self.assertEqual(replayed[0]["argv"], expected["database-create"])
        self.assertTrue(all(str(capture_output) in " ".join(row["argv"]) for row in replayed[2:]))

    def test_pack_legacy_map_and_outer_tree_manifest_are_distinct_bindings(self):
        legacy_digest = "a" * 64
        outer_digest = "b" * 64
        plan = {
            "runtime": {
                "packs": "/acquired/swift-packs",
                "pins": {"packs_manifest_sha256": legacy_digest},
                "manifests": {"packs": {"path": "inventory.json", "sha256": legacy_digest}},
            },
            "codeql_packs": {
                "root": "/acquired/swift-packs",
                "runtime_tree_component": "codeql-swift-packs",
                "runtime_tree_manifest_sha256": outer_digest,
            },
            "identity_components": [{
                "name": "codeql-swift-packs", "path": "/acquired/outer.json", "sha256": outer_digest,
            }],
        }
        runner.validate_pack_bindings(plan)
        self.assertNotEqual(legacy_digest, outer_digest)

        plan["codeql_packs"]["runtime_tree_manifest_sha256"] = legacy_digest
        with self.assertRaisesRegex(ValueError, "runtime-tree digest differs"):
            runner.validate_pack_bindings(plan)

        plan["codeql_packs"]["runtime_tree_manifest_sha256"] = outer_digest
        plan["runtime"]["manifests"]["packs"]["sha256"] = outer_digest
        with self.assertRaisesRegex(ValueError, "legacy file-map digest"):
            runner.validate_pack_bindings(plan)


if __name__ == "__main__":
    unittest.main()
