#!/usr/bin/env python3
"""Regression tests for non-cyclic v0.9.2 control and receipt binding."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).with_name("v092_qualification.py")
SPEC = importlib.util.spec_from_file_location("v092_qualification", MODULE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class QualificationBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.group_id = "joern-swift-common108"
        self.identity = {
            "tool": "joern",
            "tool_version": "4.0.660",
            "tool_build_identity": "joern-cli:4.0.660;engine:" + "a" * 64 + ";frontend:" + "b" * 64,
            "adapter_version": "joern-normal-v092",
        }
        runtime = {
            "joern_root": str(self.root / "joern"),
            "java_home": str(self.root / "java"),
            "compiler_root": str(self.root / "swift"),
            "sdk": str(self.root / "sdk"),
        }
        component_paths = {
            "joern-root": runtime["joern_root"],
            "java-home": runtime["java_home"],
            "swift-toolchain": runtime["compiler_root"],
            "swift-sdk": runtime["sdk"],
        }
        self.components = []
        for name, root_text in component_paths.items():
            Path(root_text).mkdir()
            manifest = self.root / (name + ".json")
            data = qualification.canonical_json({
                "schema_version": 1,
                "root": root_text,
                "files": [],
                "symlinks": [],
                "external_files": [],
            })
            manifest.write_bytes(data)
            self.components.append({
                "name": name,
                "path": str(manifest),
                "sha256": hashlib.sha256(data).hexdigest(),
                "kind": "runtime-tree-manifest",
            })
        self.plan = {
            "schema": "joern-common-execution-plan/v092",
            "profile": "v0.9.2",
            "engine": "joern",
            "release_group_id": self.group_id,
            "population_sha256": "d" * 64,
            "fixture_revision": "sha256:" + "e" * 64,
            "identity": self.identity,
            "identity_components": self.components,
            "runtime": runtime,
            "codeql_packs": None,
            "query_root": "adapters/joern/v0.9.2/swift-common108",
            "configurations": {"joern-current108": []},
            "cases": {"case-a": {"configuration": "joern-current108"}},
            "execution_contract": {"path": "reports/releases/v0.9.2/qualification/execution.json", "sha256": "f" * 64},
        }
        self.projection_sha = qualification.plan_projection_sha256(self.plan)

    def _write(self, relative: str, value: dict) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        path.write_bytes(data)
        return {"path": relative, "sha256": hashlib.sha256(data).hexdigest()}

    def _bound_evidence(self) -> None:
        control_plan = {
            "schema": "analyzer-qualification-control-plan/v092",
            "group_id": self.group_id,
            "execution_plan_projection_sha256": self.projection_sha,
            "identity": self.identity,
            "identity_components": self.components,
            "population_sha256": self.plan["population_sha256"],
            "fixture_revision": self.plan["fixture_revision"],
            "controls": {"direct-positive": "case-a"},
        }
        control_ref = self._write("reports/releases/v0.9.2/qualification/joern/control-plan.json", control_plan)
        self.plan["qualification_control_plan"] = control_ref
        self.plan["qualification_control_projection_sha256"] = self.projection_sha
        control_run = {
            "schema": "analyzer-qualification-control-run/v092",
            "group_id": self.group_id,
            "control_plan_sha256": control_ref["sha256"],
            "execution_plan_projection_sha256": self.projection_sha,
            "identity": self.identity,
            "identity_components": self.components,
            "records": [{"case_id": "case-a", "state": "reached"}],
        }
        run_ref = self._write("reports/releases/v0.9.2/qualification/joern/control-run.json", control_run)
        receipt = {
            "schema": "analyzer-qualification-receipt/v092",
            "status": "qualified",
            "execution_eligible": True,
            "group_id": self.group_id,
            "groups": [self.group_id],
            "population_sha256": self.plan["population_sha256"],
            "fixture_revision": self.plan["fixture_revision"],
            "identity": self.identity,
            "identity_components": self.components,
            "execution_plan_projection_sha256": self.projection_sha,
            "control_run": run_ref,
        }
        self.plan["fresh_qualification"] = self._write(
            "reports/releases/v0.9.2/qualification/joern/receipt.json", receipt
        )

    def test_projection_is_non_cyclic_and_receipt_closes_actual_digests(self):
        self.assertNotIn("qualification_control_plan", qualification.PROJECTION_FIELDS)
        self._bound_evidence()
        original = qualification.plan_projection_sha256(self.plan)
        self.assertEqual(original, self.projection_sha)
        evidence, control_path = qualification.validate_common_receipt(
            self.root, self.plan, self.plan["fresh_qualification"], group_id=self.group_id
        )
        self.assertEqual(control_path, self.root / self.plan["qualification_control_plan"]["path"])
        self.assertEqual(evidence["control_run"]["path"], "reports/releases/v0.9.2/qualification/joern/control-run.json")

    def test_receipt_cannot_claim_a_different_group(self):
        self._bound_evidence()
        receipt_path = self.root / self.plan["fresh_qualification"]["path"]
        receipt = json.loads(receipt_path.read_text())
        receipt["groups"] = ["codeql-swift-common108"]
        reference = self._write("reports/releases/v0.9.2/qualification/joern/receipt-mutated.json", receipt)
        with self.assertRaisesRegex(ValueError, "exactly the selected group"):
            qualification.validate_common_receipt(self.root, self.plan, reference, group_id=self.group_id)

    def test_control_plan_digest_is_independently_bound_by_control_run(self):
        self._bound_evidence()
        control_path = self.root / self.plan["qualification_control_plan"]["path"]
        control = json.loads(control_path.read_text())
        control["controls"]["direct-negative"] = "other-case"
        control_path.write_text(json.dumps(control))
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            qualification.validate_common_receipt(
                self.root, self.plan, self.plan["fresh_qualification"], group_id=self.group_id
            )

    def test_component_manifest_root_must_match_its_declared_role(self):
        component = self.components[0]
        manifest_path = Path(component["path"])
        manifest = json.loads(manifest_path.read_text())
        manifest["root"] = str(self.root / "other-joern")
        raw = qualification.canonical_json(manifest)
        manifest_path.write_bytes(raw)
        component["sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "manifest root differs"):
            qualification.expected_identity_components(self.plan)

    def test_component_binding_must_hash_a_regular_manifest_file(self):
        component = self.components[0]
        component["path"] = self.plan["runtime"]["joern_root"]
        with self.assertRaisesRegex(ValueError, "regular file"):
            qualification.expected_identity_components(self.plan)

    def test_codeql_runtime_manifests_bind_external_roots_from_a_fresh_snapshot(self):
        external_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(external_tmp.cleanup)
        external = Path(external_tmp.name).resolve()
        runtime = {
            "codeql": str(external / "codeql" / "codeql"),
            "extractor_root": str(external / "extractor"),
            "packs": str(external / "swift-packs"),
            "compiler_root": str(external / "swift-toolchain"),
            "sdk_root": str(external / "swift-sdk"),
            "sdk": str(external / "swift-sdk"),
        }
        for directory in (Path(runtime["extractor_root"]) / "swift", Path(runtime["packs"]),
                          Path(runtime["compiler_root"]), Path(runtime["sdk_root"]), Path(runtime["codeql"]).parent):
            directory.mkdir(parents=True, exist_ok=True)
        cli = Path(runtime["codeql"])
        cli.write_bytes(b"codeql-cli")
        schema = Path(runtime["extractor_root"]) / "swift/swift.dbscheme"
        schema.write_bytes(b"swift-schema")
        tree_components = {
            "codeql-swift-extractor": runtime["extractor_root"],
            "codeql-swift-packs": runtime["packs"],
            "swift-toolchain": runtime["compiler_root"],
            "swift-sdk": runtime["sdk_root"],
        }
        components = [{"name": "codeql-cli", "path": str(cli), "sha256": hashlib.sha256(cli.read_bytes()).hexdigest()}]
        for name, selected_root in tree_components.items():
            manifest_path = external / (name + ".json")
            raw = qualification.canonical_json({
                "schema_version": 1, "root": selected_root,
                "files": [], "symlinks": [], "external_files": [],
            })
            manifest_path.write_bytes(raw)
            components.append({
                "name": name, "path": str(manifest_path),
                "sha256": hashlib.sha256(raw).hexdigest(), "kind": "runtime-tree-manifest",
            })
        components.append({"name": "codeql-swift-schema", "path": str(schema),
                           "sha256": hashlib.sha256(schema.read_bytes()).hexdigest()})
        plan = {
            "engine": "codeql", "runtime": runtime,
            "codeql_packs": {"root": runtime["packs"]},
            "identity_components": components,
        }

        # These runtime roots intentionally live outside self.root, which is
        # the materialized execution snapshot used by the release runner.
        self.assertNotEqual(external, self.root)
        self.assertEqual(qualification.expected_identity_components(plan), components)


if __name__ == "__main__":
    unittest.main()
