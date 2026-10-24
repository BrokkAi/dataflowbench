#!/usr/bin/env python3
"""Harmless fixture tests for frozen-bridge-02's actual-call boundary."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest


MODULE_PATH = Path(__file__).with_name("bifrost-v0140-frozen-bridge-02.py")
SPEC = importlib.util.spec_from_file_location("bifrost_frozen_bridge_02", MODULE_PATH)
assert SPEC and SPEC.loader
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


def put(root: Path, path: str, raw: bytes) -> dict[str, str]:
    target = root.joinpath(*bridge._relative(path).parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {"path": path, "sha256": bridge.sha256(raw)}


class FixtureBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls: list[str] = []
        self._git("init", "-q")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "frozen bridge fixture")
        self._git("config", "commit.gpgsign", "false")
        source = put(root, "fixtures/source.txt", b"source fixture\n")
        runner = put(root, "scripts/execute-release-v092.py", b"runner fixture\n")
        binary = put(root, "fixtures/bifrost.bin", b"bifrost fixture\n")
        self.source_inputs = [source, runner]
        self.binary = binary
        self.source_commit = self._commit("source")
        self._build_plan()
        self.plan_commit = self._commit("plan")
        self.modules = self._modules()

    def _git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def _commit(self, message: str) -> str:
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, check=True)
        return self._git("rev-parse", "HEAD")

    def _build_plan(self) -> None:
        groups: list[dict[str, object]] = []
        case_cursor = 0
        case_ids = [f"case-{i:04d}" for i in range(bridge.EXPECTED_CASES)]
        for index in range(bridge.EXPECTED_GROUPS):
            count = 15 if index < 8 else 13
            cases = case_ids[case_cursor:case_cursor + count]
            case_cursor += count
            report_count = 2 if index < 8 else 1
            row_count = 51 if index < 52 else 50
            report_rows: list[list[str]] = []
            rows = [f"row-{index:02d}-{i:04d}" for i in range(row_count)]
            for report_index in range(report_count):
                start = report_index * len(rows) // report_count
                end = (report_index + 1) * len(rows) // report_count
                report_rows.append(rows[start:end])
            groups.append({
                "id": f"bifrost-group-{index:02d}", "tool": "bifrost",
                "case_ids": cases,
                "reports": [{"case_ids": rows} for rows in report_rows],
            })
        self.assert_shape(groups)
        self.runner_sha = self.source_inputs[1]["sha256"]
        self.plan = {
            "release": "v0.9.2", "schema_version": 1,
            "source_commit": self.source_commit,
            "runner_source_sha256": self.runner_sha,
            "total_wall_budget_seconds": bridge.TOTAL_WALL_SECONDS,
            "source_inputs": self.source_inputs,
            "tools": {"bifrost": self.binary,
                      "runner": {"path": self.source_inputs[1]["path"],
                                 "sha256": self.source_inputs[1]["sha256"]}},
            "groups": groups,
        }
        contract_raw = bridge.canonical_json(self.plan)
        self.contract = put(self.root, "reports/releases/v0.9.2/execution-v4/contract.json", contract_raw)
        self.source_design = put(self.root, "evidence/source-design.json", bridge.canonical_json({
            "baseline_source_commit": self.source_commit,
            "target_source_commit": self.source_commit,
            "patch_files": [], "approved_additive_scripts": [],
        }))
        self.manifest_object = {
            "source_inputs_delta": [], "source_delta_baseline": self.source_commit,
            "final_projection_groups": [group["id"] for group in groups],
        }
        self.manifest_ref = put(self.root, "evidence/manifest.json", bridge.canonical_json(self.manifest_object))
        self.original_prefix = self._prefix(bridge.HISTORICAL_ROWS, "historical")
        self.continuation_prefix = self._prefix(bridge.CONTINUATION_ROWS, "continued")

    @staticmethod
    def assert_shape(groups: list[dict[str, object]]) -> None:
        assert len(groups) == 84
        assert len({case for group in groups for case in group["case_ids"]}) == 1108
        assert sum(len(group["reports"]) for group in groups) == 92
        assert sum(len(report["case_ids"]) for group in groups for report in group["reports"]) == 4252

    def _prefix(self, count: int, label: str) -> dict[str, str]:
        rows = []
        for index in range(count):
            rows.append({"attempt_id": f"{label}-{index:03d}",
                         "contract_sha256": self.contract["sha256"],
                         "source_commit": self.source_commit,
                         "plan_commit": self.plan_commit if hasattr(self, "plan_commit") else "0" * 40})
        # Prefixes are written after the plan commit is known; the first call
        # is replaced below by _rewrite_prefixes().
        return put(self.root, f"evidence/{label}.jsonl", b"".join(bridge.canonical_json(row) for row in rows))

    def _rewrite_prefixes(self) -> None:
        for ref, count, label in ((self.original_prefix, bridge.HISTORICAL_ROWS, "historical"),
                                  (self.continuation_prefix, bridge.CONTINUATION_ROWS, "continued")):
            rows = [{"attempt_id": f"{label}-{index:03d}",
                     "contract_sha256": self.contract["sha256"],
                     "source_commit": self.source_commit, "plan_commit": self.plan_commit,
                     "group_id": f"bifrost-group-{index % bridge.EXPECTED_GROUPS:02d}",
                     "status": "completed", "exit_code": 0}
                    for index in range(count)]
            raw = b"".join(bridge.canonical_json(row) for row in rows)
            path = self.root.joinpath(*bridge._relative(ref["path"]).parts)
            path.write_bytes(raw)
            ref["sha256"] = bridge.sha256(raw)
        # The continuation ref has exactly the same first 87 bytes as the
        # historical ref, which is the immutable-prefix relationship tested
        # by the production adapter.
        original = self.root.joinpath(*bridge._relative(self.original_prefix["path"]).parts).read_bytes()
        continued_path = self.root.joinpath(*bridge._relative(self.continuation_prefix["path"]).parts)
        continued = continued_path.read_bytes()
        continued_path.write_bytes(original + continued[-2 * 1:])
        # Recreate two complete canonical rows rather than slicing bytes.
        rows = [{"attempt_id": f"continued-{index:03d}",
                 "contract_sha256": self.contract["sha256"],
                 "source_commit": self.source_commit, "plan_commit": self.plan_commit,
                 "group_id": f"bifrost-group-{index % bridge.EXPECTED_GROUPS:02d}",
                 "status": "completed", "exit_code": 0}
                for index in range(bridge.HISTORICAL_ROWS, bridge.CONTINUATION_ROWS)]
        continued_path.write_bytes(original + b"".join(bridge.canonical_json(row) for row in rows))
        self.continuation_prefix["sha256"] = bridge.sha256(continued_path.read_bytes())

    def _modules(self) -> dict[str, types.ModuleType]:
        replacement = types.ModuleType("fixture_replacement05")
        executor = types.ModuleType("fixture_executor")
        checker = types.ModuleType("fixture_checker")
        configuration = types.ModuleType("fixture_configuration")
        replacement._calls = self.calls
        executor._calls = self.calls
        checker._calls = self.calls
        configuration._calls = self.calls
        def normalized_source_inputs(plan: dict, root: Path, qualifications: dict) -> list[dict]:
            combined: dict[str, dict] = {}
            for item in plan["source_inputs"]:
                path = item["path"]
                combined[path] = {"path": path, "sha256": item["sha256"],
                                  "role": item.get("role", "release-input")}
            for item in qualifications.values():
                path = item["path"]
                combined[path] = {"path": path, "sha256": item["sha256"],
                                  "role": "qualification-evidence"}
            return [combined[path] for path in sorted(combined)]
        def validate_plan(path: Path, *, repo_root: Path) -> dict[str, object]:
            self.calls.append(f"validate_plan:{path}")
            raw = path.read_bytes()
            plan = json.loads(raw)
            qualification = {
                "fixture-runner-review": {
                    "path": self.source_inputs[1]["path"],
                    "sha256": self.source_inputs[1]["sha256"],
                }
            }
            return {"path": path, "repo_root": repo_root, "bytes_sha256": bridge.sha256(raw),
                    "plan": plan, "groups": plan["groups"],
                    "source_inputs": normalized_source_inputs(plan, repo_root, qualification),
                    "qualification": qualification,
                    "plan_commit": self.plan_commit,
                    "total_wall_budget_seconds": bridge.TOTAL_WALL_SECONDS}
        def source_file(root: Path, commit: str, path: str, expected: str) -> bytes:
            raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root)
            if bridge.sha256(raw) != expected:
                raise ValueError(path)
            return raw
        def snapshot(root: Path, source_commit: str, runner_sha: str, source_inputs: list[dict]) -> None:
            self.calls.append("_assert_source_snapshot")
            subprocess.run(["git", "merge-base", "--is-ancestor", source_commit, "HEAD"], cwd=root, check=True)
            assert bridge.sha256(subprocess.check_output(["git", "show", f"{source_commit}:scripts/execute-release-v092.py"], cwd=root)) == runner_sha
            for item in source_inputs:
                source_file(root, source_commit, item["path"], item["sha256"])
        executor.validate_plan = validate_plan
        executor._source_inputs = normalized_source_inputs
        executor._source_file = source_file
        executor._assert_source_snapshot = snapshot
        def source_delta(root: Path, design: dict, manifest: dict, baseline: str, target: str) -> dict:
            self.calls.append("_source_delta")
            assert design["baseline_source_commit"] == baseline and design["target_source_commit"] == target
            assert manifest["source_delta_baseline"] == baseline
            return {"baseline": baseline, "target": target, "paths": []}
        def source_inputs(root: Path, executor_module: object, inherited: list[dict], plan: dict, manifest: dict, source: str) -> dict:
            self.calls.append("_source_inputs")
            assert inherited == [] and manifest["source_inputs_delta"] == []
            executor_module._assert_source_snapshot(root, source, plan["runner_source_sha256"], plan["source_inputs"])
            return {"count": len(plan["source_inputs"]), "inherited": 0, "added": len(plan["source_inputs"]),
                    "runner_source_sha256": plan["runner_source_sha256"]}
        def validate_replacement(root: Path, executor_module: object, ref: dict, raw: bytes, plan: dict, commit: str) -> dict:
            self.calls.append("_validate_replacement_plan")
            value = executor_module.validate_plan(root / Path(*bridge._relative(ref["path"]).parts), repo_root=root)
            assert value["bytes_sha256"] == ref["sha256"] and value["plan"] == plan
            return value
        def context_map(base: dict, continuation: dict, replacement_context: dict, *args: object, **kwargs: object) -> dict:
            self.calls.append("_context_map")
            return {self.contract["sha256"]: {"validated": replacement_context["validated"],
                    "source_commit": self.source_commit, "plan_commit": self.plan_commit, "role": "replacement"}}
        def check_rows(rows: list[dict], contexts: dict, replacement_sha: str, source: str, plan: str, prefix_len: int) -> None:
            self.calls.append("_check_rows_context")
            assert len(rows) >= prefix_len
            assert all(row["contract_sha256"] == replacement_sha and row["source_commit"] == source and
                       row["plan_commit"] == plan for row in rows)
        replacement._source_delta = source_delta
        replacement._source_inputs = source_inputs
        replacement._validate_replacement_plan = validate_replacement
        replacement._context_map = context_map
        replacement._check_rows_context = check_rows
        def mixed_replay(context: dict, rows: list[dict], selected: dict) -> dict:
            self.calls.append("mixed_replay")
            assert context["contract_sha256"] == self.contract["sha256"]
            return {"status": "replacement-preflight-passed", "fresh_groups": 84,
                    "fresh_partitions": 92, "fresh_rows": 4252}
        replacement._replay = mixed_replay
        def verify(root: Path, contract: Path) -> dict:
            self.calls.append("verify")
            return {"status": "fresh-evidence-verified", "fresh_groups": 84,
                    "fresh_partitions": 92, "fresh_rows": 4252}
        checker.verify = verify
        def config_validate(*, root: Path, contract_path: Path, output: str, execute: bool) -> dict:
            self.calls.append(f"configuration:{execute}")
            assert execute is False
            return {"status": "ready-to-execute", "execute": execute,
                    "output": output, "fresh_groups": 84, "fresh_partitions": 92, "fresh_rows": 4252}
        configuration.validate = config_validate
        return {"replacement05": replacement, "executor": executor,
                "checker": checker, "configuration": configuration}

    def core(self) -> dict[str, object]:
        return {
            "schema": "fixture-core", "source_commit": self.source_commit, "plan_commit": self.plan_commit,
            "contract": self.contract, "source_design": self.source_design, "source_evidence": self.manifest_ref,
            "binary": self.binary,
            "continuation": {"schema": "v092-bifrost-v0140-continuation-context/v1",
                              "source_commit": self.source_commit, "plan_commit": self.plan_commit,
                              "contract": self.contract, "source_inputs": []},
            "continuation_source_commit": self.source_commit, "inherited_source_inputs": [],
            "original_prefix": self.original_prefix, "continuation_prefix": self.continuation_prefix,
            "ledger_path": "evidence/continued.jsonl",
            "replacement_groups": [group["id"] for group in self.plan["groups"]],
            "configuration_output": "evidence/config-output.json",
            "source_contexts": {self.contract["sha256"]: {
                "contract": self.contract, "source_commit": self.source_commit,
                "plan_commit": self.plan_commit, "role": "replacement",
            }},
        }


class FrozenBridge02Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fixture = FixtureBuilder(self.root)
        self.fixture._rewrite_prefixes()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_before_calls_actual_retained_checker_and_all_frozen_boundaries(self) -> None:
        result = bridge.load_and_validate(self.root, self.fixture.core(), mode="before",
                                          fixture_modules=self.fixture.modules, fixture_only=True)
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["normalized_shape"]["groups"], 84)
        self.assertIn("mixed_replay", self.fixture.calls)
        for name in ("validate_plan", "_source_delta", "_source_inputs", "_assert_source_snapshot",
                     "_context_map", "_check_rows_context", "configuration:False"):
            self.assertTrue(any(name in call for call in self.fixture.calls), name)
        self.assertNotIn("verify", self.fixture.calls)
        self.assertEqual(result["original_prefix_ref"]["path"], "evidence/historical.jsonl")
        normalized_inputs = result["validated_full_normalized_plan"]["source_inputs"]
        self.assertEqual([item["role"] for item in normalized_inputs],
                         ["release-input", "qualification-evidence"])

    def test_after_calls_full_checker_and_configuration_execute_false(self) -> None:
        result = bridge.load_and_validate(self.root, self.fixture.core(), mode="after",
                                          fixture_modules=self.fixture.modules, fixture_only=True)
        self.assertEqual(result["checker_summary_or_pending"]["status"], "replacement-preflight-passed")
        self.assertIn("mixed_replay", self.fixture.calls)
        self.assertIn("configuration:False", self.fixture.calls)

    def test_runtime_context_exports_live_objects_without_round_trip(self) -> None:
        runtime = bridge.load_runtime_context(
            self.root, self.fixture.core(), mode="after",
            fixture_modules=self.fixture.modules, fixture_only=True)
        self.assertTrue(runtime["lossless_runtime_objects"])
        self.assertIs(runtime["modules"]["executor"], self.fixture.modules["executor"])
        self.assertIs(runtime["validated"], runtime["mixed_context"]["validated"])
        self.assertIsInstance(runtime["validated"]["path"], Path)
        self.assertEqual(runtime["mixed_context"]["source_commit"], self.fixture.source_commit)
        self.assertEqual(runtime["mixed_context"]["plan_commit"], self.fixture.plan_commit)
        self.assertIsNot(runtime["validated"], runtime["bridge_context"]["validated_full_normalized_plan"])
        self.assertEqual(runtime["bridge_context"]["context_digest"],
                         bridge.sha256(bridge.canonical_json({
                             **{key: value for key, value in runtime["bridge_context"].items()
                                if key != "context_digest"},
                         })))

    def test_real_git_identity_and_immutable_prefix_near_misses_fail_closed(self) -> None:
        bad = dict(self.fixture.core())
        bad["contract"] = {**self.fixture.contract, "sha256": "0" * 64}
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge.load_and_validate(self.root, bad, fixture_modules=self.fixture.modules, fixture_only=True)
        bad = dict(self.fixture.core())
        bad["continuation_prefix"] = dict(self.fixture.continuation_prefix)
        bad["continuation_prefix"]["sha256"] = "f" * 64
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge.load_and_validate(self.root, bad, fixture_modules=self.fixture.modules, fixture_only=True)
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge.load_and_validate(self.root, self.fixture.core(), fixture_modules=self.fixture.modules)

    def test_binary_identity_must_match_normalized_plan_tool(self) -> None:
        bad = dict(self.fixture.core())
        bad["binary"] = {**self.fixture.binary, "sha256": "0" * 64}
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge.load_and_validate(self.root, bad, fixture_modules=self.fixture.modules,
                                     fixture_only=True)

    def test_supplied_serialized_result_and_execution_boundaries_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            bridge.load_and_validate(self.root, self.fixture.core(), checker_result={})  # type: ignore[call-arg]
        for operation in (bridge.execute, bridge.admit, bridge.materialize, bridge.replay,
                          bridge.dispatch, bridge.build_group_command, bridge.run_groups,
                          bridge.write_phase_gate, bridge.write_completion):
            with self.assertRaises(bridge.FrozenBridgeUnsupported):
                operation()

    def test_production_typed_context_rejects_legacy_aliases_and_unknown_fields(self) -> None:
        core = self.fixture.core()
        # The test fixture is intentionally allowed to use its temporary
        # validator seam, but the production roster parser is independently
        # strict about the protocol-07 entry shape.
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge._exact_source_context_entries(
                {"source_contexts": {
                    self.fixture.contract["sha256"]: {
                        "contract": self.fixture.contract,
                        "source_commit": self.fixture.source_commit,
                        "plan_commit": self.fixture.plan_commit,
                        "role": "replacement",
                        "legacy_context": True,
                    }
                }}, fixture_only=False)
        with self.assertRaises(bridge.FrozenBridgeError):
            bridge.load_and_validate(
                self.root,
                {**core, "continuation": {**core["continuation"], "legacy": True}},
                fixture_modules=self.fixture.modules, fixture_only=False)

    def test_dependency_pins_match_immutable_local_source_bytes(self) -> None:
        """Catch a typo in a reviewed SHA even when fixture calls still pass."""
        repo = MODULE_PATH.parents[4]
        refs = {"replacement05": bridge.REPLACEMENT05, "continuation03": bridge.CONTINUATION03,
                **bridge.FROZEN}
        for name, ref in refs.items():
            raw = repo.joinpath(*bridge._relative(ref["path"]).parts).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref["sha256"], name)

    def test_configuration_adapter_uses_actual_boundaries_and_restores_modules(self) -> None:
        """Exercise the production adapter path without fixture_only or real validators."""
        root = self.root.resolve()
        contract = root / "contract.json"
        contract.write_bytes(b"{}\n")
        checker = types.SimpleNamespace()
        executor = types.SimpleNamespace()
        old_verify = lambda *args, **kwargs: {"old": True}
        old_validate = lambda *args, **kwargs: {"old": True}
        checker.verify = old_verify
        executor.validate_plan = old_validate
        old_configuration_checker = object()
        old_configuration_executor = object()
        configuration = types.SimpleNamespace(
            CHECKER=old_configuration_checker,
            EXECUTOR=old_configuration_executor,
        )
        validated = {"plan": {"tools": {"runner": "bound"}, "source_inputs": ["exact"]},
                     "lossless_normalized_fields": {"qualification": "preserved"}}
        summary = {"status": "fresh-evidence-verified", "fresh_groups": 84}

        def config_validate(*, root: Path, contract_path: Path, output: str, execute: bool) -> dict:
            self.assertIs(configuration.CHECKER, checker)
            self.assertIs(configuration.EXECUTOR, executor)
            seen_summary = configuration.CHECKER.verify(root=root, contract_path=contract_path)
            seen_validated = configuration.EXECUTOR.validate_plan(contract_path, repo_root=root)
            self.assertEqual(seen_summary, summary)
            self.assertIs(seen_validated, validated)
            self.assertFalse(execute)
            return {"status": "ready-to-execute", "output": output}

        configuration.validate = config_validate
        result = bridge._call_configuration(
            configuration, checker, executor, root, contract, "reports/config.json", validated, summary)
        self.assertEqual(result["status"], "ready-to-execute")
        self.assertIs(configuration.CHECKER, old_configuration_checker)
        self.assertIs(configuration.EXECUTOR, old_configuration_executor)
        self.assertIs(checker.verify, old_verify)
        self.assertIs(executor.validate_plan, old_validate)


if __name__ == "__main__":
    unittest.main()
