#!/usr/bin/env python3
"""Contract and evidence-projection tests for the v0.9.2 executor."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import unittest
from unittest.mock import patch
import sys
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name("execute-release-v092.py")
SPEC = importlib.util.spec_from_file_location("execute_release_v092", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


class ExecutorTests(unittest.TestCase):
    def test_only_exact_extractor_provenance_is_allowed_outside_evidence(self):
        relative = "execution-state/v092/swift-source/patch-application/applied-patch.json"
        target = self.root / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b"provenance")
        item = {"path": relative, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        resolved = executor._source_inputs({"source_inputs": [item]}, self.root, {})
        self.assertEqual(resolved[0]["path"], relative)
        item["path"] = relative + ".other"
        with self.assertRaises(executor.ReleaseError):
            executor._source_inputs({"source_inputs": [item]}, self.root, {})

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.parent_bytes = (ROOT / executor.PARENT_PLAN).read_bytes()
        self.parent = json.loads(self.parent_bytes)
        self.parent_execution_bytes = (ROOT / executor.PARENT_EXECUTION_CONTRACT).read_bytes()
        self.parent_execution = json.loads(self.parent_execution_bytes)
        self.population_bytes = (ROOT / "populations/v0.9.0.json").read_bytes()
        self.population = json.loads(self.population_bytes)
        self.contract_path = self.root / "reports/releases/v0.9.2/execution-v1/contract.json"
        self.plan = self._contract()
        self._write_contract()

    def _contract(self):
        parent_ref_path = self.root / executor.PARENT_PLAN
        parent_ref_path.parent.mkdir(parents=True, exist_ok=True)
        parent_ref_path.write_bytes(self.parent_bytes)
        parent_execution_path = self.root / executor.PARENT_EXECUTION_CONTRACT
        parent_execution_path.parent.mkdir(parents=True, exist_ok=True)
        parent_execution_path.write_bytes(self.parent_execution_bytes)
        pop_path = self.root / "populations/v0.9.0.json"
        pop_path.parent.mkdir(parents=True, exist_ok=True)
        pop_path.write_bytes(self.population_bytes)

        self.tools = {}
        qualifications = {}
        for tool in sorted({group["tool"] for group in self.parent["execution_groups"]}):
            tool_path = self.root / "tools" / f"{tool}.bin"
            tool_path.parent.mkdir(parents=True, exist_ok=True)
            tool_path.write_bytes(f"fixture-{tool}".encode())
            identity = {
                "path": str(tool_path),
                "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
                "version": "1.0.0",
                "report_version": "1.0.0",
            }
            self.tools[tool] = identity
        self.tool_components = {}
        for tool in ("codeql", "joern", "semgrep", "pysa"):
            component = f"{tool}-component"
            component_path = self.root / "tools" / f"{component}.bin"
            component_path.parent.mkdir(parents=True, exist_ok=True)
            component_path.write_bytes(f"fixture-{component}".encode())
            self.tools[component] = {
                "path": str(component_path),
                "sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
            }
            self.tool_components[tool] = [component]
        self.codeql_packs_root = self.root / "execution-state/v092/tools/codeql-packs"
        self.codeql_packs_root.mkdir(parents=True)
        pack_file = self.codeql_packs_root / "fixture.ql"
        pack_file.write_bytes(b"fixture pack\n")
        packs_manifest = {
            "schema_version": 1,
            "root": str(self.codeql_packs_root),
            "files": [{"path": "fixture.ql", "sha256": hashlib.sha256(pack_file.read_bytes()).hexdigest()}],
            "symlinks": [],
            "external_files": [],
        }
        packs_manifest_path = self.root / "tools/codeql-packs-manifest.json"
        packs_manifest_raw = json.dumps(packs_manifest, sort_keys=True).encode() + b"\n"
        packs_manifest_path.write_bytes(packs_manifest_raw)
        self.tools["codeql-packs-manifest"] = {
            "path": str(packs_manifest_path),
            "sha256": hashlib.sha256(packs_manifest_raw).hexdigest(),
            "kind": "runtime-tree-manifest",
        }
        self.tool_components["codeql"].append("codeql-packs-manifest")
        self.swift_packs_root = self.root / "execution-state/v092/tools/swift-codeql/candidate-packs-entry2"
        self.swift_packs_root.mkdir(parents=True)
        swift_pack_file = self.swift_packs_root / "codeql/swift-all/6.8.5-dfb.entry2/swift.dbscheme"
        swift_pack_file.parent.mkdir(parents=True)
        swift_pack_file.write_bytes(b"swift pack schema\n")
        swift_manifest = {
            "schema_version": 1,
            "root": str(self.swift_packs_root),
            "files": [{"path": "codeql/swift-all/6.8.5-dfb.entry2/swift.dbscheme", "sha256": hashlib.sha256(swift_pack_file.read_bytes()).hexdigest()}],
            "symlinks": [],
            "external_files": [],
        }
        swift_manifest_path = self.root / "tools/codeql-swift-packs-manifest.json"
        swift_manifest_raw = json.dumps(swift_manifest, sort_keys=True).encode() + b"\n"
        swift_manifest_path.write_bytes(swift_manifest_raw)
        self.tools["codeql-swift-packs"] = {
            "path": str(swift_manifest_path),
            "sha256": hashlib.sha256(swift_manifest_raw).hexdigest(),
            "kind": "runtime-tree-manifest",
        }
        self.tool_components["codeql"].append("codeql-swift-packs")
        swift_plan_rel = Path("adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json")
        swift_plan_path = self.root / swift_plan_rel
        swift_plan_path.parent.mkdir(parents=True, exist_ok=True)
        swift_plan_path.write_text(json.dumps({
            "schema": "swift-common-execution-plan/v092",
            "profile": "v0.9.2",
            "engine": "codeql",
            "execution_eligible": True,
            "codeql_packs": {
                "root": str(self.swift_packs_root),
                "runtime_tree_component": "codeql-swift-packs",
                "runtime_tree_manifest_sha256": hashlib.sha256(swift_manifest_raw).hexdigest(),
            },
        }))
        joern_plan_rel = Path("adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json")
        joern_plan_path = self.root / joern_plan_rel
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

        for tool in sorted({group["tool"] for group in self.parent["execution_groups"]}):
            evidence_rel = Path("reports/releases/v0.9.2/qualification") / f"{tool}.json"
            evidence_path = self.root / evidence_rel
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            qualified_groups = [group["id"] for group in self.parent["execution_groups"]
                                if group["tool"] == tool]
            components = [executor._component_identity(alias, self.tools[alias])
                          for alias in self.tool_components.get(tool, [])]
            evidence = {
                "status": "qualified",
                "execution_eligible": True,
                "groups": qualified_groups,
                "identity_components": components,
                "tool": {
                    "path": self.tools[tool]["path"],
                    "sha256": self.tools[tool]["sha256"],
                    "version": self.tools[tool]["version"],
                },
            }
            raw = json.dumps(evidence, sort_keys=True).encode() + b"\n"
            evidence_path.write_bytes(raw)
            qualifications[tool] = {
                "status": "qualified",
                "execution_eligible": True,
                "groups": qualified_groups,
                "evidence": {
                    "path": evidence_rel.as_posix(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                },
            }

        registered = {report["report"]: report for report in self.parent["reports"]}
        groups = []
        for old in self.parent["execution_groups"]:
            tool = old["tool"]
            group_id = old["id"]
            output_root = f"reports/raw/v092-fixture/{group_id}"
            reports = []
            for ordinal, old_path in enumerate(old["reports"]):
                historical = registered[old_path]
                report_name = Path(old_path).name
                version = self.tools[tool]["report_version"]
                reports.append({
                    "ordinal": ordinal,
                    "path": old_path.replace(
                        "reports/releases/v0.9.0/normal/",
                        "reports/releases/v0.9.2/normal/",
                        1,
                    ),
                    "source_path": f"{output_root}/normalized-{ordinal}-{report_name}",
                    "case_ids": list(historical["case_ids"]),
                    "tool": tool,
                    "tool_version": version,
                })
            if group_id == "codeql-swift-common108":
                argv = [
                    "/usr/bin/python3", "scripts/run-swift-common-v092.py", "execute",
                    "--plan", swift_plan_rel.as_posix(), "--output", output_root,
                    "--query-receipt", "reports/releases/v0.9.2/qualification/codeql-query-receipt.json",
                ]
            elif group_id == "joern-swift-common108":
                argv = [
                    "/usr/bin/python3", "scripts/run-joern-common-v092.py", "execute",
                    "--plan", joern_plan_rel.as_posix(), "--output", output_root,
                ]
            else:
                argv = [str(self.root / "tools" / f"{tool}.bin")]
                if old["tool"] == "codeql":
                    argv.extend(["--codeql-packs", str(self.codeql_packs_root)])
            groups.append({
                "id": group_id,
                "family": old["tool"],
                "tool": tool,
                "argv": argv,
                "environment": {"PATH": "/bin", "LANG": "C"},
                "output_roots": [output_root],
                "deadline_seconds": 600,
                "maximum_attempts": 1,
                "case_ids": list(old["case_ids"]),
                "reports": reports,
            })
        return {
            "schema_version": 1,
            "release": "v0.9.2",
            "source_commit": "a" * 40,
            "execution_series": 1,
            "execution_authorized": False,
            "runner_source_sha256": "b" * 64,
            "fixture_revision": self.population["fixture_revision"],
            "parent_plan": {
                "path": executor.PARENT_PLAN.as_posix(),
                "sha256": hashlib.sha256(self.parent_bytes).hexdigest(),
            },
            "parent_execution_contract": {
                "path": executor.PARENT_EXECUTION_CONTRACT.as_posix(),
                "sha256": hashlib.sha256(self.parent_execution_bytes).hexdigest(),
            },
            "population": {
                "path": "populations/v0.9.0.json",
                "sha256": hashlib.sha256(self.population_bytes).hexdigest(),
                "fixture_revision": self.population["fixture_revision"],
            },
            "tools": self.tools,
            "tool_components": self.tool_components,
            "codeql_packs": {
                "root": str(self.codeql_packs_root),
                "component": "codeql-packs-manifest",
                "swift_root": str(self.swift_packs_root),
                "swift_component": "codeql-swift-packs",
            },
            "qualifications": qualifications,
            "groups": groups,
            "resource_budget": {"serial_analyzers": 1, "minimum_launch_free_gib": 125,
                                "protected_reserve_gib": 40, "scratch_gib": 24,
                                "proposed_total_retention_ceiling_gib": 24},
            "resource_reservation": {
                "exclusive_analyzer_slot": True,
                "expires_at_unix_seconds": time.time() + 600,
            },
            "total_wall_budget_seconds": 100000,
        }

    def _write_contract(self):
        self.contract_path.parent.mkdir(parents=True, exist_ok=True)
        self.contract_path.write_text(json.dumps(self.plan, sort_keys=True) + "\n")

    def validate(self):
        return executor.validate_plan(self.contract_path, repo_root=self.root)

    def test_fixed_population_group_and_partition_contract(self):
        validated = self.validate()
        self.assertEqual(len(validated["groups"]), 84)
        self.assertEqual(sum(len(group["reports"]) for group in self.plan["groups"]), 92)
        self.assertEqual(len({case["id"] for case in self.population["cases"]}), 1108)
        self.assertEqual(validated["plan"]["execution_authorized"], False)
        codeql_groups = [group for group in validated["groups"] if group["id"].startswith("codeql-")]
        self.assertEqual(len(codeql_groups), 18)
        self.assertTrue(all("codeql-packs-manifest" in group["identity_components"] for group in codeql_groups))
        swift = next(group for group in codeql_groups if group["id"] == "codeql-swift-common108")
        self.assertEqual(swift["swift_plan"]["sha256"], hashlib.sha256(
            (self.root / swift["swift_plan"]["path"]).read_bytes()
        ).hexdigest())
        joern = next(group for group in validated["groups"] if group["id"] == "joern-swift-common108")
        self.assertEqual(joern["joern_plan"]["path"], "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json")
        self.assertEqual(joern["joern_plan"]["sha256"], hashlib.sha256(
            (self.root / joern["joern_plan"]["path"]).read_bytes()
        ).hexdigest())

    def test_swift_plan_must_bind_the_exact_custom_pack_manifest(self):
        swift = next(group for group in self.plan["groups"] if group["id"] == "codeql-swift-common108")
        plan_path = self.root / swift["argv"][swift["argv"].index("--plan") + 1]
        swift_plan = json.loads(plan_path.read_text())
        swift_plan["codeql_packs"]["runtime_tree_manifest_sha256"] = "0" * 64
        plan_path.write_text(json.dumps(swift_plan))
        with self.assertRaisesRegex(executor.ReleaseError, "manifest SHA differs"):
            self.validate()

    def test_missing_group_is_rejected(self):
        self.plan["groups"].pop()
        self._write_contract()
        with self.assertRaisesRegex(executor.ReleaseError, "84 historical execution groups"):
            self.validate()

    def test_changed_historical_membership_is_rejected(self):
        self.plan["groups"][0]["case_ids"].pop()
        self._write_contract()
        with self.assertRaisesRegex(executor.ReleaseError, "case membership"):
            self.validate()

    def test_changed_partition_is_rejected(self):
        group = next(group for group in self.plan["groups"] if group["reports"])
        group["reports"][0]["case_ids"].pop()
        self._write_contract()
        with self.assertRaisesRegex(executor.ReleaseError, "report partition"):
            self.validate()

    def test_pending_analyzer_is_retained_but_cannot_run(self):
        tool = next(iter(self.plan["qualifications"]))
        first = self.plan["qualifications"][tool]
        first["status"] = "pending"
        first["execution_eligible"] = False
        first["groups"] = []
        first.pop("evidence")
        self._write_contract()
        validated = self.validate()
        with self.assertRaisesRegex(executor.ReleaseError, "not covered by eligible qualification"):
            executor._require_group_qualification(
                validated,
                next(group["id"] for group in self.plan["groups"] if group["tool"] == tool),
            )

    def test_measurement_with_known_limits_stays_distinct_and_scoped(self):
        tool = "bifrost"
        qualification = self.plan["qualifications"][tool]
        evidence_path = self.root / qualification["evidence"]["path"]
        evidence = json.loads(evidence_path.read_text())
        evidence["status"] = "measurement-with-known-limits"
        raw = json.dumps(evidence, sort_keys=True).encode() + b"\n"
        evidence_path.write_bytes(raw)
        qualification["status"] = "measurement-with-known-limits"
        qualification["evidence"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self._write_contract()
        validated = self.validate()
        self.assertEqual(
            validated["qualification"][tool]["status"],
            "measurement-with-known-limits",
        )
        group_id = qualification["groups"][0]
        self.assertTrue(executor._require_group_qualification(validated, group_id)["execution_eligible"])

    def test_qualification_scope_cannot_authorize_an_unlisted_group(self):
        tool = "codeql"
        qualification = self.plan["qualifications"][tool]
        group_id = qualification["groups"].pop()
        evidence_path = self.root / qualification["evidence"]["path"]
        evidence = json.loads(evidence_path.read_text())
        evidence["groups"] = qualification["groups"]
        raw = json.dumps(evidence, sort_keys=True).encode() + b"\n"
        evidence_path.write_bytes(raw)
        qualification["evidence"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self._write_contract()
        validated = self.validate()
        with self.assertRaisesRegex(executor.ReleaseError, "not covered by eligible qualification"):
            executor._require_group_qualification(validated, group_id)

    def test_runtime_tree_manifest_detects_changed_or_unlisted_engine_files(self):
        runtime = self.root / "pysa-runtime"
        runtime.mkdir()
        core = runtime / "pyre.bin"
        core.write_bytes(b"pyre-core")
        manifest = {
            "schema_version": 1,
            "root": str(runtime),
            "files": [{
                "path": "pyre.bin",
                "sha256": hashlib.sha256(core.read_bytes()).hexdigest(),
            }],
            "symlinks": [],
            "external_files": [],
        }
        manifest_path = self.root / "tools/pysa-runtime-manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode() + b"\n"
        manifest_path.write_bytes(manifest_bytes)
        binding = {
            "path": str(manifest_path),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "kind": "runtime-tree-manifest",
        }
        executor._check_tool_file(binding, "pysa runtime")
        (runtime / "unlisted.bin").write_bytes(b"changed runtime")
        with self.assertRaisesRegex(executor.ReleaseError, "differs from manifest"):
            executor._check_tool_file(binding, "pysa runtime")

    def test_runtime_tree_manifest_checks_optional_file_modes(self):
        runtime = self.root / "mode-runtime"
        runtime.mkdir()
        core = runtime / "engine"
        core.write_bytes(b"engine")
        core.chmod(0o755)
        manifest = {
            "schema_version": 1,
            "root": str(runtime),
            "files": [{
                "path": "engine",
                "sha256": hashlib.sha256(core.read_bytes()).hexdigest(),
                "mode": stat.S_IMODE(core.stat().st_mode),
            }],
            "symlinks": [],
            "external_files": [],
        }
        raw = json.dumps(manifest, sort_keys=True).encode() + b"\n"
        executor._check_runtime_tree_manifest(raw, "mode fixture")
        core.chmod(0o644)
        with self.assertRaisesRegex(executor.ReleaseError, "file mode differs"):
            executor._check_runtime_tree_manifest(raw, "mode fixture")

    def test_runtime_tree_manifest_rejects_external_directory_symlink(self):
        runtime = self.root / "directory-link-runtime"
        runtime.mkdir()
        target = self.root / "external-directory"
        target.mkdir()
        os.symlink(target, runtime / "external")
        manifest = {
            "schema_version": 1,
            "root": str(runtime),
            "files": [],
            "symlinks": [{"path": "external", "target": str(target)}],
            "external_files": [{"path": str(target), "sha256": "0" * 64}],
        }
        raw = json.dumps(manifest, sort_keys=True).encode() + b"\n"
        with self.assertRaisesRegex(executor.ReleaseError, "external directory symlink needs"):
            executor._check_runtime_tree_manifest(raw, "directory link fixture")

    def test_runtime_tree_manifest_allows_internal_directory_symlink(self):
        runtime = self.root / "internal-link-runtime"
        target_dir = runtime / "target"
        target_dir.mkdir(parents=True)
        target_file = target_dir / "engine"
        target_file.write_bytes(b"engine")
        os.symlink(target_dir, runtime / "alias")
        manifest = {
            "schema_version": 1,
            "root": str(runtime),
            "files": [{
                "path": "target/engine",
                "sha256": hashlib.sha256(target_file.read_bytes()).hexdigest(),
            }],
            "symlinks": [{"path": "alias", "target": str(target_dir)}],
            "external_files": [],
        }
        raw = json.dumps(manifest, sort_keys=True).encode() + b"\n"
        executor._check_runtime_tree_manifest(raw, "internal link fixture")

    def test_tool_identity_mismatch_in_qualification_is_rejected(self):
        tool = next(iter(self.plan["qualifications"]))
        evidence_path = self.root / self.plan["qualifications"][tool]["evidence"]["path"]
        evidence = json.loads(evidence_path.read_text())
        evidence["tool"]["sha256"] = "0" * 64
        raw = json.dumps(evidence, sort_keys=True).encode() + b"\n"
        evidence_path.write_bytes(raw)
        self.plan["qualifications"][tool]["evidence"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self._write_contract()
        with self.assertRaisesRegex(executor.ReleaseError, "exact bound identity"):
            self.validate()

    def test_resource_floor_cannot_be_lowered(self):
        self.plan["resource_budget"]["minimum_launch_free_gib"] = 100
        self._write_contract()
        with self.assertRaisesRegex(executor.ReleaseError, "125 GiB"):
            self.validate()

    def test_staging_changes_only_raw_output_and_preserves_incomplete_state(self):
        group = self.plan["groups"][0]
        report = group["reports"][0]
        execution = self.root / "execution"
        output = execution / group["output_roots"][0]
        output.mkdir(parents=True)
        raw_path = output / "raw.json"
        raw_bytes = b'{"state":"incomplete","diagnostic":"budget exhausted"}\n'
        raw_path.write_bytes(raw_bytes)
        original = {
            "fixture_revision": self.population["fixture_revision"],
            "tool": report["tool"],
            "tool_version": report["tool_version"],
            "results": [{
                "case_id": case_id,
                "outcome": "inconclusive",
                "diagnostics": ["BudgetExhausted"],
                "raw_output": raw_path.relative_to(execution).as_posix(),
                "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            } for case_id in report["case_ids"]],
        }
        source = execution / report["source_path"]
        source.parent.mkdir(parents=True, exist_ok=True)
        original_bytes = json.dumps(original, sort_keys=True).encode() + b"\n"
        source.write_bytes(original_bytes)
        attempt_id = "fixture-attempt-01"
        attempt = self.root / executor.ATTEMPTS_ROOT / attempt_id
        captured = executor._copy_tree(output, execution, execution, attempt / "capture")
        capture_rows = {item["execution_relative"]: item for item in captured}
        result = executor._stage_report(
            self.root,
            attempt,
            execution,
            attempt_id,
            report,
            capture_rows,
            [output],
            self.population["fixture_revision"],
        )
        retained_original = self.root / result["original_path"]
        staged = self.root / result["staged_path"]
        captured_raw = self.root / result["raw_output_mappings"][0]["captured_path"]
        self.assertEqual(retained_original.read_bytes(), original_bytes)
        self.assertEqual(captured_raw.read_bytes(), raw_bytes)
        projection = json.loads(staged.read_bytes())
        projected_row = projection["results"][0]
        self.assertEqual(projected_row["outcome"], "inconclusive")
        self.assertEqual(projected_row["diagnostics"], ["BudgetExhausted"])
        self.assertEqual(
            projected_row["raw_output"],
            f"{executor.ATTEMPTS_ROOT.as_posix()}/{attempt_id}/capture/{raw_path.relative_to(execution).as_posix()}",
        )

    def test_attempt_roots_are_series_scoped_and_never_overwritten(self):
        group = self.plan["groups"][0]
        reports = group["reports"]
        first = executor._assert_fresh(self.root, group, reports, 1)
        self.assertIn("attempt-01", first[0].name)
        self.assertIn("series-01", str(first[1]))
        first[0].mkdir(parents=True)
        with self.assertRaisesRegex(executor.ReleaseError, "cannot be overwritten"):
            executor._assert_fresh(self.root, group, reports, 1)
        second = executor._assert_fresh(self.root, group, reports, 2)
        self.assertIn("attempt-01", second[0].name)
        self.assertIn("series-02", str(second[1]))

    def test_failed_attempt_retry_preserves_series_and_uses_fresh_roots(self):
        group = {**self.plan["groups"][0], "maximum_attempts": 2}
        first = executor._assert_fresh(self.root, group, group["reports"], 1)
        first[0].mkdir(parents=True)
        first[1].mkdir(parents=True)
        first[2].mkdir(parents=True)
        executor._append_ledger(first[3], {"group_id": group["id"], "execution_series": 1, "status": "failed"})
        second = executor._assert_fresh(self.root, group, group["reports"], 1)
        self.assertIn("attempt-02", second[0].name)
        self.assertEqual(second[1].name, "attempt-02")
        self.assertEqual(second[2].name, "attempt-02")
        self.assertNotEqual(first[1], second[1])
        self.assertTrue(first[1].is_dir())
        executor._append_ledger(first[3], {"group_id": group["id"], "execution_series": 1, "status": "failed"})
        with self.assertRaisesRegex(executor.ReleaseError, "maximum_attempts"):
            executor._assert_fresh(self.root, group, group["reports"], 1)

    def test_resume_does_not_reset_matrix_wall_budget(self):
        validated = {"repo_root": self.root, "plan": {"execution_series": 1}, "bytes_sha256": "a" * 64}
        row = {"execution_series": 1, "contract_sha256": "a" * 64,
               "start_utc": "2026-10-20T00:00:00+00:00", "duration_seconds": 15}
        executor._append_ledger(self.root / Path(*executor.LEDGER_PATH.parts), row)
        start = executor._datetime.datetime.fromisoformat(row["start_utc"]).timestamp()
        self.assertEqual(executor._matrix_elapsed_wall(validated, now_seconds=start + 3600), 3600)
        self.assertEqual(executor._matrix_elapsed_wall(validated, now_seconds=start + 10), 15)
        with self.assertRaisesRegex(executor.ReleaseError, "wall clock"):
            executor._matrix_elapsed_wall(validated, now_seconds=start - 1)

    def test_environment_is_explicit_and_attempt_scoped(self):
        group = {"environment": {
            "PATH": "/pinned/bin", "HOME": "@EXECUTION_ROOT@/home",
            "CACHE": "@CACHE_ROOT@", "LOG": "@ATTEMPT_ROOT@/run.log",
        }}
        execution = self.root / "exec-root"
        attempt = self.root / "attempt-root"
        cache = self.root / "cache-root"
        environment = executor._child_environment(group, execution, attempt, cache)
        self.assertEqual(environment["PATH"], "/pinned/bin")
        self.assertEqual(environment["HOME"], str(execution / "home"))
        self.assertEqual(environment["TMPDIR"], str(execution / "tmp"))
        self.assertEqual(environment["CACHE"], str(cache))
        self.assertEqual(environment["LOG"], str(attempt / "run.log"))
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)

    def test_capacity_counts_prior_outputs_home_caches_and_external_pysa_scratch(self):
        group = self.plan["groups"][0]
        previous = self.root / Path(*executor.EXECUTION_ROOT.parts) / "series-01" / group["id"] / "attempt-01"
        executor._append_ledger(self.root / Path(*executor.LEDGER_PATH.parts),
                                {"group_id": group["id"], "execution_root": str(previous)})
        current = previous.parent / "attempt-02"
        env = {"HOME": str(current / "home"), "TMPDIR": str(current / "tmp")}
        retained, scratch = executor._matrix_capacity_paths(
            {"repo_root": self.root, "plan": self.plan}, current, env, [current / "reports/raw"])
        self.assertIn(previous / group["output_roots"][0], retained)
        self.assertIn(previous / "home", scratch)
        self.assertIn(current / "home", scratch)
        self.assertIn(self.root / Path(*executor.CACHE_ROOT.parts), scratch)
        pysa = next(item for item in self.plan["groups"] if item["tool"] == "pysa")
        pysa_root = previous.parent.parent / pysa["id"] / "attempt-01"
        executor._append_ledger(self.root / Path(*executor.LEDGER_PATH.parts),
                                {"group_id": pysa["id"], "execution_root": str(pysa_root)})
        _, scratch = executor._matrix_capacity_paths(
            {"repo_root": self.root, "plan": self.plan}, current, env, [])
        external = [path for path in scratch if path.parent == Path("/private/tmp")]
        self.assertEqual(len(external), 1)
        self.assertTrue(external[0].name.startswith("dfb-v092-pysa-"))
        one = self.root / "one.json"
        one.write_bytes(b"1234567")
        self.assertEqual(executor._tree_bytes([one, one]), 7)

    def test_pysa_scratch_avoids_ancestor_git_ignore_rules(self):
        group = {"tool": "pysa", "environment": {"PATH": "/pinned/bin"}}
        execution = self.root / "execution-state/group-1"
        first = executor._child_environment(group, execution, self.root / "attempt", self.root / "cache")
        second = executor._child_environment(group, execution.with_name("group-2"), self.root / "attempt", self.root / "cache")
        self.assertEqual(Path(first["TMPDIR"]).parent, Path("/private/tmp"))
        self.assertTrue(Path(first["TMPDIR"]).name.startswith("dfb-v092-pysa-"))
        self.assertNotEqual(first["TMPDIR"], second["TMPDIR"])
        self.assertFalse(Path(first["TMPDIR"]).is_relative_to(self.root))

    def test_v092_wrapper_receives_release_group_gate_only_for_versioned_entrypoint(self):
        group = {
            "id": "codeql-swift-common108",
            "argv": ["scripts/run-swift-common-v092.py", "execute"],
            "environment": {"PATH": "/pinned/bin"},
        }
        environment = executor._child_environment(
            group,
            self.root / "exec-root",
            self.root / "attempt-root",
            self.root / "cache-root",
        )
        self.assertEqual(environment["DATAFLOWBENCH_V092_RELEASE_EXECUTION"], "1")
        self.assertEqual(environment["DATAFLOWBENCH_V092_GROUP_ID"], "codeql-swift-common108")
        legacy = executor._child_environment(
            {"id": "codeql-swift", "argv": ["scripts/run-swift-common-v2.py"], "environment": {"PATH": "/pinned/bin"}},
            self.root / "exec-root",
            self.root / "attempt-root",
            self.root / "cache-root",
        )
        self.assertNotIn("DATAFLOWBENCH_V092_RELEASE_EXECUTION", legacy)

    def test_live_capacity_loss_stops_child_and_preserves_partial_output(self):
        stdout, stderr = self.root / "stdout", self.root / "stderr"
        with patch.object(executor, "_capacity_loss", side_effect=[None, None, "protected disk reserve lost"]):
            code, timed_out, duration, loss = executor._run_process(
                [sys.executable, "-u", "-c", "import time; print('partial evidence'); time.sleep(30)"],
                self.root, dict(os.environ), stdout, stderr, 20,
            )
        self.assertNotEqual(code, 0)
        self.assertFalse(timed_out)
        self.assertEqual(loss, "protected disk reserve lost")
        self.assertLess(duration, 10)
        self.assertIn(b"partial evidence", stdout.read_bytes())

    def test_capacity_stop_tracks_detached_child_and_preserves_unrelated_process(self):
        pid_path = self.root / "detached.pid"
        child_code = ("import os,time; from pathlib import Path; "
                      f"Path({str(pid_path)!r}).write_text(str(os.getpid())); time.sleep(30)")
        parent_code = ("import subprocess,sys,time; "
                       f"subprocess.Popen([sys.executable,'-c',{child_code!r}], start_new_session=True); "
                       "print('partial detached evidence',flush=True); time.sleep(30)")
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                     start_new_session=True)
        ownership = {}
        started = time.monotonic()
        def capacity(*args, **kwargs):
            return "protected disk reserve lost" if pid_path.exists() and time.monotonic() - started > 2 else None
        try:
            with patch.object(executor, "_capacity_loss", side_effect=capacity):
                code, timed_out, duration, loss = executor._run_process(
                    [sys.executable, "-u", "-c", parent_code], self.root, dict(os.environ),
                    self.root / "detached.stdout", self.root / "detached.stderr", 15,
                    ownership=ownership,
                )
            self.assertNotEqual(code, 0)
            self.assertFalse(timed_out)
            self.assertEqual(loss, "protected disk reserve lost")
            self.assertLess(duration, 10)
            child_pid = int(pid_path.read_text())
            tracked = {row["pid"]: row["start_identity"] for row in ownership["tracked_processes"]}
            self.assertIn(child_pid, tracked)
            tracker = executor._process_tracker()
            self.assertFalse(tracker._active(tracker._process_table(), tracked))
            self.assertEqual(ownership["cleanup_status"], "tracked-processes-stopped")
            self.assertEqual(ownership["descendant_containment"], "unproven")
            self.assertNotIn(unrelated.pid, tracked)
            self.assertIsNone(unrelated.poll())
            self.assertIn(b"partial detached evidence", (self.root / "detached.stdout").read_bytes())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=5)

    def test_tracker_failure_before_launch_retains_error_without_process_claim(self):
        attempt_id = "prelaunch-attempt-01-series-01"
        attempt = self.root / Path(*executor.ATTEMPTS_ROOT.parts) / attempt_id
        attempt.mkdir(parents=True)
        ownership = {}
        with patch.object(executor, "_process_tracker", side_effect=RuntimeError("tracker unavailable")):
            with patch.object(executor.subprocess, "Popen") as launch:
                with self.assertRaisesRegex(RuntimeError, "tracker unavailable"):
                    executor._run_process(["unused"], self.root, {}, attempt / "stdout.txt",
                                          attempt / "stderr.txt", 10, ownership=ownership)
                launch.assert_not_called()
        row = {"status": "recorder-error", "recorder_error": "tracker unavailable",
               "process_ownership": ownership}
        executor._preserve_recorder_failure(self.root, attempt, attempt_id, row)
        self.assertNotIn("process_ownership", row)
        self.assertEqual(row["stdout"]["bytes"], 0)
        self.assertEqual(row["reports"], [])

    def test_cleanup_never_signals_a_recycled_process_identity(self):
        from types import SimpleNamespace
        tracker = executor._process_tracker()
        tracker._process_table = lambda: {123: (1, "new-birth", "S")}
        process = SimpleNamespace(poll=lambda: 0)
        signals = []
        with patch.object(executor.os, "kill") as kill:
            executor._stop_owned_processes(process, tracker, {123: "old-birth"}, signals)
        kill.assert_not_called()
        self.assertEqual(signals, [])

    def test_contention_detects_compilers_and_engine_children_but_allows_idle_mcp(self):
        rows = [
            "11 0.0 bifrost /pinned/bifrost --mcp",
            "17 0.0 bifrost /pinned/bifrost --root /source --lsp",
            "12 52.0 clang /toolchain/clang -c source.c",
            "13 25.0 semgrep-core /venv/semgrep-core -json fixture.py",
            "14 40.0 pyre.bin /venv/pyre.bin analyze",
            "15 99.0 suite_bench /tmp/suite_bench_policy-deadbeef",
            "16 0.0 bazel-9 /tmp/bazel-9.0.0-darwin-arm64 build //swift/extractor",
        ]
        busy = executor._contenders("\n".join(rows))
        self.assertEqual(busy, rows[2:])

    def test_retention_ceiling_is_a_live_capacity_failure(self):
        output = self.root / "retained"
        output.mkdir()
        (output / "native.json").write_bytes(b"12345")
        with patch.object(executor.shutil, "disk_usage", return_value=type("Disk", (), {"free": executor.MIN_FREE_BYTES})()):
            self.assertIn("retention ceiling", executor._capacity_loss(self.root, [output], 4))
            self.assertIsNone(executor._capacity_loss(self.root, [output], 5))
            self.assertIn("scratch ceiling", executor._capacity_loss(self.root, [], 5, [output], 4))

    def test_live_capacity_walk_allows_deleted_temporary_files_only(self):
        output = self.root / "mutable-scratch"
        output.mkdir()
        (output / "disappearing.tmp").write_text("temporary")
        with patch.object(Path, "lstat", side_effect=FileNotFoundError()):
            self.assertEqual(executor._tree_bytes([output]), 0)
        with patch.object(Path, "lstat", side_effect=PermissionError()):
            with self.assertRaises(PermissionError):
                executor._tree_bytes([output])

    def test_partial_recorder_writes_are_bound_without_promotion(self):
        attempt_id = "swift-attempt-01-series-01"
        attempt = self.root / Path(*executor.ATTEMPTS_ROOT.parts) / attempt_id
        captured = attempt / "capture/reports/raw/partial.json"
        original = attempt / "original/reports/releases/v0.9.2/normal/swift.json"
        staged = self.root / Path(*executor.NORMAL_ROOT.parts) / "attempts" / attempt_id / "swift.json"
        for path in (captured, original, staged):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"partial bytes")
        (attempt / "stdout.txt").write_text("retained stdout")
        row = {"status": "recorder-error", "reports": [{"must": "not promote"}]}
        executor._preserve_recorder_failure(self.root, attempt, attempt_id, row)
        self.assertEqual(row["reports"], [])
        self.assertEqual(len(row["captured_files"]), 1)
        self.assertEqual(row["captured_files"][0]["execution_relative"], "reports/raw/partial.json")
        self.assertEqual({item["path"] for item in row["failed_staging_artifacts"]},
                         {original.relative_to(self.root).as_posix(), staged.relative_to(self.root).as_posix()})
        self.assertTrue(all(item["sha256"] == executor._sha(b"partial bytes")
                            for item in row["failed_staging_artifacts"]))
        self.assertEqual(row["stdout"]["path"], "stdout.txt")
        staged.unlink()
        staged.symlink_to(original)
        with self.assertRaisesRegex(executor.ReleaseError, "non-regular partial"):
            executor._preserve_recorder_failure(self.root, attempt, attempt_id, row)

    def test_plan_can_be_committed_after_its_source_without_a_hash_cycle(self):
        def git(*args):
            return subprocess.check_output(
                ["git", "-c", "commit.gpgsign=false", *args], cwd=self.root,
                stderr=subprocess.PIPE,
            ).decode().strip()
        git("init", "-q")
        self.contract_path.unlink()
        (self.root / "src").mkdir(exist_ok=True)
        (self.root / "src/main.rs").write_text("fn main() {}\n")
        git("add", ".")
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Source")
        source = git("rev-parse", "HEAD")
        self.plan["source_commit"] = source
        self._write_contract()
        git("add", ".")
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Execution plan")
        plan_commit = git("rev-parse", "HEAD")
        self.assertNotEqual(source, plan_commit)
        validated = {"path": str(self.contract_path), "repo_root": self.root,
                     "bytes_sha256": executor._sha(self.contract_path.read_bytes())}
        executor._assert_source_snapshot(self.root, source)
        self.assertEqual(executor._assert_contract_snapshot(validated), plan_commit)
        snapshot = self.root / "isolated-snapshot"
        (snapshot / "src").mkdir(parents=True)
        (snapshot / "src/main.rs").write_bytes((self.root / "src/main.rs").read_bytes())
        self.assertEqual(executor._register_source_snapshot(self.root, source, snapshot), source)
        command = ["git", "diff", "--quiet", "HEAD", "--", "src/main.rs"]
        self.assertEqual(subprocess.run(command, cwd=snapshot).returncode, 0)
        (snapshot / "src/main.rs").write_text("fn changed() {}\n")
        self.assertEqual(subprocess.run(command, cwd=snapshot).returncode, 1)
        self.contract_path.write_text("{}\n")
        with self.assertRaisesRegex(executor.ReleaseError, "changed after validation"):
            executor._assert_contract_snapshot(validated)


if __name__ == "__main__":
    unittest.main()
