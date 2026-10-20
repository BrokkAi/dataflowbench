#!/usr/bin/env python3
"""Tests for deterministic v0.9.2 contract preparation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name("prepare-release-v092.py")
SPEC = importlib.util.spec_from_file_location("prepare_release_v092", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)
executor = generator.executor


class ContractGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source_bytes = (ROOT / generator.SOURCE_CONTRACT).read_bytes()
        self.parent_bytes = (ROOT / generator.PARENT_PLAN).read_bytes()
        self.population_bytes = (ROOT / "populations/v0.9.0.json").read_bytes()
        for relative, content in (
            (generator.SOURCE_CONTRACT, self.source_bytes),
            (generator.PARENT_PLAN, self.parent_bytes),
            (Path("populations/v0.9.0.json"), self.population_bytes),
        ):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        self.source = json.loads(self.source_bytes)
        self.parent = json.loads(self.parent_bytes)
        self.bindings = self._bindings()

    def _add_tool(self, alias: str, version: str | None = None) -> dict:
        path = self.root / "tool-fixtures" / f"{alias}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = f"test-tool-{alias}".encode()
        path.write_bytes(content)
        binding = {"path": str(path), "sha256": hashlib.sha256(content).hexdigest()}
        if version is not None:
            binding["version"] = version
            binding["report_version"] = version
        return binding

    def _bindings(self) -> dict:
        families = sorted({group["tool"] for group in self.source["groups"]})
        tools = {family: self._add_tool(family, f"{family}-1.0") for family in families}
        tools["runner"] = self._add_tool("runner")
        component_map = {}
        for family in ("codeql", "joern", "semgrep", "pysa"):
            alias = f"{family}-runtime-component"
            tools[alias] = self._add_tool(alias)
            component_map[family] = [alias]

        def add_pack_manifest(alias: str, relative: str) -> tuple[Path, str]:
            pack_root = self.root / relative
            pack_root.mkdir(parents=True)
            pack_file = pack_root / "fixture.ql"
            pack_file.write_bytes((alias + " fixture\n").encode())
            manifest = {
                "schema_version": 1,
                "root": str(pack_root),
                "files": [{"path": "fixture.ql", "sha256": hashlib.sha256(pack_file.read_bytes()).hexdigest()}],
                "symlinks": [],
                "external_files": [],
            }
            manifest_path = self.root / f"tool-fixtures/{alias}.json"
            manifest_bytes = json.dumps(manifest, sort_keys=True).encode() + b"\n"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_bytes(manifest_bytes)
            tools[alias] = {
                "path": str(manifest_path),
                "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "kind": "runtime-tree-manifest",
            }
            component_map["codeql"].append(alias)
            return pack_root, hashlib.sha256(manifest_bytes).hexdigest()

        ordinary_root, _ordinary_manifest_sha = add_pack_manifest(
            "codeql-packs-manifest", "execution-state/v092/tools/codeql-packs"
        )
        swift_root, swift_manifest_sha = add_pack_manifest(
            "swift-codeql-packs-manifest", "execution-state/v092/tools/swift-codeql/candidate-packs-entry2"
        )
        swift_plan_path = self.root / generator.DEFAULT_SWIFT_PLAN
        swift_plan_path.parent.mkdir(parents=True, exist_ok=True)
        swift_plan_path.write_text(json.dumps({
            "schema": "swift-common-execution-plan/v092",
            "profile": "v0.9.2",
            "engine": "codeql",
            "status": "execution-eligible",
            "execution_eligible": True,
            "codeql_packs": {
                "root": str(swift_root),
                "runtime_tree_component": "swift-codeql-packs-manifest",
                "runtime_tree_manifest_sha256": swift_manifest_sha,
            },
        }))
        joern_plan_path = self.root / generator.DEFAULT_JOERN_PLAN
        joern_plan_path.parent.mkdir(parents=True, exist_ok=True)
        joern_plan_path.write_text(json.dumps({
            "schema": "joern-common-execution-plan/v092",
            "profile": "v0.9.2",
            "engine": "joern",
            "release_group_id": "joern-swift-common108",
            "status": "execution-eligible",
            "execution_eligible": True,
            "scored_activation": False,
            "aggregate_resource_qualification": "unavailable",
        }))

        historical_tool_names = {
            "bifrost": "bifrost",
            "codeql": "codeql",
            "joern": "joern",
            "semgrep": "semgrep",
            "opentaint": "opentaint-wrapper",
            "infer": "infer",
            "flowdroid": "flowdroid",
            "pysa": "pyre",
        }
        replacements = {}
        for family, old_name in historical_tool_names.items():
            old_path = self.source["tools"][old_name]["path"]
            replacements[old_path] = tools[family]["path"]
        old_runner = self.source["tools"]["runner"]["path"]
        replacements[old_runner] = tools["runner"]["path"]
        old_semgrep_bin = str(Path(self.source["tools"]["semgrep"]["path"]).parent)
        new_semgrep_bin = str(Path(tools["semgrep"]["path"]).parent)
        replacements[old_semgrep_bin] = new_semgrep_bin

        group_tools = {group["id"]: group["tool"] for group in self.source["groups"]}
        input_path = self.root / "reports/releases/v0.9.2/acquisition/tool-inventory.json"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_bytes = b'{"inventory":"fixture"}\n'
        input_path.write_bytes(input_bytes)
        return {
            "source_commit": "a" * 40,
            "execution_series": 1,
            "group_tools": group_tools,
            "tool_bindings": tools,
            "tool_components": component_map,
            "codeql_packs_component": "codeql-packs-manifest",
            "swift_codeql_packs_component": "swift-codeql-packs-manifest",
            "path_replacements": replacements,
            "source_inputs": [{
                "path": "reports/releases/v0.9.2/acquisition/tool-inventory.json",
                "sha256": hashlib.sha256(input_bytes).hexdigest(),
                "role": "acquisition-inventory",
            }],
            "resource_budget": {"serial_analyzers": 1, "minimum_launch_free_gib": 125},
            "resource_reservation": {
                "exclusive_analyzer_slot": True,
                "expires_at_unix_seconds": time.time() + 600,
            },
            "total_wall_budget_seconds": 100000,
        }

    def test_full_contract_preserves_membership_and_is_unapproved(self):
        contract = generator.build_contract(
            self.bindings,
            "b" * 64,
            repo_root=self.root,
        )
        path = self.root / generator.OUTPUT
        validated = executor.validate_plan(path, repo_root=self.root)
        self.assertEqual(len(contract["groups"]), 84)
        self.assertEqual(sum(len(group["reports"]) for group in contract["groups"]), 92)
        self.assertEqual(len(validated["plan"]["population"]["sha256"]), 64)
        self.assertFalse(contract["execution_authorized"])
        self.assertTrue(all(item["status"] == "pending" for item in contract["qualifications"].values()))
        self.assertEqual(contract["source_commit"], "a" * 40)
        self.assertEqual(contract["source_inputs"][0]["role"], "acquisition-inventory")

    def test_required_environment_pins_bifrost_and_semgrep(self):
        contract = generator.build_contract(
            self.bindings,
            "b" * 64,
            repo_root=self.root,
        )
        bifrost = next(group for group in contract["groups"] if group["family"] == "bifrost")
        semgrep = next(group for group in contract["groups"] if group["family"] == "semgrep")
        self.assertEqual(bifrost["environment"]["BIFROST_OPEN_PACKS_DISABLE"], "1")
        self.assertEqual(
            semgrep["environment"]["PATH"].split(":", 1)[0],
            str(Path(self.bindings["tool_bindings"]["semgrep"]["path"]).parent),
        )

    def test_python_and_codeql_groups_keep_their_single_analyzer_identity(self):
        contract = generator.build_contract(
            self.bindings,
            "b" * 64,
            repo_root=self.root,
        )
        python_groups = [group for group in contract["groups"] if group["family"] == "pysa"]
        self.assertTrue(python_groups)
        self.assertEqual({group["tool"] for group in python_groups}, {"pysa"})
        codeql_groups = [group for group in contract["groups"] if group["family"] == "codeql"]
        self.assertEqual({group["tool"] for group in codeql_groups}, {"codeql"})
        swift = next(group for group in codeql_groups if group["id"] == "codeql-swift-common108")
        plan_index = swift["argv"].index("--plan")
        self.assertEqual(swift["argv"][plan_index + 1], generator.DEFAULT_SWIFT_PLAN.as_posix())
        self.assertIn("scripts/run-swift-common-v092.py", swift["argv"])
        receipt_index = swift["argv"].index("--query-receipt")
        self.assertEqual(
            swift["argv"][receipt_index + 1],
            "reports/releases/v0.9.2/qualification/codeql-swift-common108/query-check-02/receipt.json",
        )
        for group in codeql_groups:
            if group is swift:
                continue
            packs_index = group["argv"].index("--codeql-packs")
            self.assertEqual(group["argv"][packs_index + 1], contract["codeql_packs"]["root"])
        self.assertNotEqual(contract["codeql_packs"]["root"], contract["codeql_packs"]["swift_root"])
        self.assertEqual(contract["codeql_packs"]["swift_component"], "swift-codeql-packs-manifest")
        joern = next(group for group in contract["groups"] if group["id"] == "joern-swift-common108")
        self.assertIn("scripts/run-joern-common-v092.py", joern["argv"])
        self.assertNotIn("--reservation", joern["argv"])
        self.assertEqual(joern["argv"][joern["argv"].index("--plan") + 1], generator.DEFAULT_JOERN_PLAN.as_posix())
        self.assertEqual(joern["output_roots"], ["reports/raw/joern-common-v2/current108-v092-01"])
        self.assertTrue(all("current108-v092-01/normal/" in report["source_path"] for report in joern["reports"]))
        self.assertEqual(joern["argv"][joern["argv"].index("--output") + 1], joern["output_roots"][0])

    def test_generator_never_overwrites_a_contract(self):
        generator.build_contract(self.bindings, "b" * 64, repo_root=self.root)
        path = self.root / generator.OUTPUT
        original = path.read_bytes()
        with self.assertRaisesRegex(executor.ReleaseError, "will not be overwritten"):
            generator.build_contract(self.bindings, "b" * 64, repo_root=self.root)
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
