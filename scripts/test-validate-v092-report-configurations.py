#!/usr/bin/env python3
"""Focused tests for the canonical v0.9.2 report-configuration gate."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import py_compile
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("validate-v092-report-configurations.py")
SPEC = importlib.util.spec_from_file_location("validate_v092_report_configurations_tested", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReportProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.checkout = Path(temporary.name) / "checkout"
        self.root.mkdir()
        self.checkout.mkdir()
        self.bindings = []
        self.raw_paths = []

    def _add_report(self, name: str, attempt_id: str, case_id: str, raw_bytes: bytes,
                    *, raw_path: str | None = None, mapping_sha: str | None = None) -> None:
        raw_path = raw_path or (
            f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/raw/{case_id}.json"
        )
        raw_target = self.root / raw_path
        raw_target.parent.mkdir(parents=True, exist_ok=True)
        raw_target.write_bytes(raw_bytes)
        self.raw_paths.append(raw_path)

        adapter = f"reports/releases/v0.9.2/normal/{name}"
        staged = f"reports/releases/v0.9.2/normal/attempts/{attempt_id}/{name}"
        report_value = {
            "schema_version": 1,
            "tool": "bifrost",
            "tool_version": "0.13.1",
            "adapter_version": "fixture",
            "configuration_hash": "a" * 64,
            "results": [{"case_id": case_id, "raw_output": raw_path}],
        }
        report_bytes = (json.dumps(report_value, sort_keys=True) + "\n").encode()
        report_target = self.root / staged
        report_target.parent.mkdir(parents=True, exist_ok=True)
        report_target.write_bytes(report_bytes)
        completed = self.root / "reports/releases/v0.9.2/attempts" / attempt_id / "completed.json"
        completed.parent.mkdir(parents=True, exist_ok=True)
        completed.write_text(json.dumps({
            "status": "completed",
            "attempt_id": attempt_id,
            "reports": [{
                "staged_path": staged,
                "staged_sha256": sha(report_bytes),
                "raw_output_mappings": [{
                    "execution_relative": raw_path.split(
                        f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/", 1,
                    )[-1],
                    "captured_path": raw_path,
                    "sha256": mapping_sha or sha(raw_bytes),
                    "bytes": len(raw_bytes),
                }],
            }],
        }, sort_keys=True) + "\n")
        self.bindings.append({
            "adapter": adapter,
            "staged_path": staged,
            "sha256": sha(report_bytes),
            "rows": 1,
            "attempt_id": attempt_id,
            "attempt_number": 1,
        })

    def _project(self, expected_count: int | None = None):
        expected_count = expected_count if expected_count is not None else len(self.bindings)
        selected_attempts = []
        seen_attempts = set()
        for binding in self.bindings:
            attempt_id = binding["attempt_id"]
            if attempt_id in seen_attempts:
                continue
            seen_attempts.add(attempt_id)
            completed = self.root / "reports/releases/v0.9.2/attempts" / attempt_id / "completed.json"
            selected_attempts.append({
                "attempt_id": attempt_id,
                "status": "completed",
                "completed_receipt_sha256": sha(completed.read_bytes()),
            })
        return validator._project_reports(
            self.root,
            self.checkout,
            {"fresh_reports": self.bindings, "selected_attempts": selected_attempts},
            expected_report_count=expected_count,
            expected_row_count=len(self.bindings),
        )

    def _add_joern_projection(self):
        attempt_id = validator.JOERN_PROJECTION.ATTEMPT_ID
        partitions, _case_set = validator.JOERN_PROJECTION._load_partition_specs(validator.ROOT)
        output_dir = validator.JOERN_PROJECTION.PUBLICATION_PROJECTION_DIRECTORY
        config_hash = "a" * 64
        report_records = []
        receipt_reports = []
        self.bindings = []
        all_raw_paths = []
        for partition in partitions:
            name = Path(partition["report"]).name
            original_path = f"reports/releases/v0.9.2/normal/attempts/{attempt_id}/{name}"
            original_value = {
                "schema_version": 1,
                "tool": "joern",
                "adapter_version": "joern-normal-v092",
                "scored_activation": False,
                "results": [],
            }
            raw_mappings = []
            for case_id in partition["case_ids"]:
                raw_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/raw/{case_id}.json"
                raw_bytes = json.dumps({"case_id": case_id}, sort_keys=True).encode() + b"\n"
                raw_target = self.root / raw_path
                raw_target.parent.mkdir(parents=True, exist_ok=True)
                raw_target.write_bytes(raw_bytes)
                all_raw_paths.append(raw_path)
                original_value["results"].append({
                    "case_id": case_id,
                    "raw_output": raw_path,
                    "outcome": "unsupported" if case_id.endswith("-unsupported") else "inconclusive",
                })
                raw_mappings.append({
                    "execution_relative": f"raw/{case_id}.json",
                    "captured_path": raw_path,
                    "sha256": sha(raw_bytes),
                    "bytes": len(raw_bytes),
                })
            original_bytes = (json.dumps(original_value, sort_keys=True) + "\n").encode()
            original_target = self.root / original_path
            original_target.parent.mkdir(parents=True, exist_ok=True)
            original_target.write_bytes(original_bytes)
            receipt_reports.append({
                "staged_path": original_path,
                "staged_sha256": sha(original_bytes),
                "raw_output_mappings": raw_mappings,
            })

            projected_value = dict(original_value, configuration_hash=config_hash)
            projected_bytes = (json.dumps(projected_value, sort_keys=True) + "\n").encode()
            projected_path = f"{output_dir}/{name}"
            projected_target = self.root / projected_path
            projected_target.parent.mkdir(parents=True, exist_ok=True)
            projected_target.write_bytes(projected_bytes)
            original_ref = {"path": original_path, "sha256": sha(original_bytes)}
            projection_ref = {"path": projected_path, "sha256": sha(projected_bytes)}
            report_records.append({
                "path": projected_path,
                "sha256": sha(projected_bytes),
                "cases": len(partition["case_ids"]),
                "case_ids": partition["case_ids"],
                "source": {"path": "source.json", "sha256": "b" * 64},
                "staged": original_ref,
                "derived_source": {"path": "derived-source.json", "sha256": "c" * 64},
                "derived_staged": {"path": "derived-staged.json", "sha256": "d" * 64},
                "raw_outputs": [
                    {"case_id": row["case_id"], "path": row["raw_output"], "sha256": "e" * 64}
                    for row in projected_value["results"]
                ],
            })
            self.bindings.append({
                "adapter": f"reports/releases/v0.9.2/normal/{name}",
                "staged_path": projected_path,
                "sha256": sha(projected_bytes),
                "rows": len(partition["case_ids"]),
                "attempt_id": attempt_id,
                "attempt_number": 5,
                "original_staged": original_ref,
                "metadata_projection": projection_ref,
            })

        receipt_value = {
            "status": "completed",
            "attempt_id": attempt_id,
            "reports": receipt_reports,
        }
        receipt_path = self.root / "reports/releases/v0.9.2/attempts" / attempt_id / "completed.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt_value, sort_keys=True) + "\n")
        self.summary = {
            "fresh_reports": self.bindings,
            "selected_attempts": [{
                "attempt_id": attempt_id,
                "status": "completed",
                "completed_receipt_sha256": sha(receipt_path.read_bytes()),
            }],
        }
        self.manifest = {
            "schema": "v092-joern108-publication-projection/v1",
            "status": "verified-derived-report-metadata",
            "attempt_id": attempt_id,
            "group_id": validator.JOERN_PROJECTION.GROUP_ID,
            "case_count": 108,
            "report_count": 5,
            "scored_activation": False,
            "configuration_ready": False,
            "full_release_gate_satisfied": False,
            "publication_approved": False,
            "configuration_hash": config_hash,
            "reports": report_records,
        }
        manifest_path = self.root / validator.JOERN_PROJECTION.PUBLICATION_PROJECTION_MANIFEST
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_bytes = (json.dumps(self.manifest, sort_keys=True) + "\n").encode()
        manifest_path.write_bytes(manifest_bytes)
        self.summary["joern_metadata_projection"] = {
            "path": validator.JOERN_PROJECTION.PUBLICATION_PROJECTION_MANIFEST,
            "sha256": sha(manifest_bytes),
        }
        for binding in self.bindings:
            binding["metadata_projection"] = dict(self.summary["joern_metadata_projection"])
        return all_raw_paths

    def _project_joern(self):
        with patch.object(validator.JOERN_PROJECTION, "verify_existing_projection",
                          return_value=self.manifest):
            return validator._project_reports(
                self.root,
                self.checkout,
                self.summary,
                expected_report_count=5,
                expected_row_count=108,
            )

    def _replace_derived_report(self, index: int, report_value: dict) -> None:
        binding = self.bindings[index]
        report_bytes = (json.dumps(report_value, sort_keys=True) + "\n").encode()
        (self.root / binding["staged_path"]).write_bytes(report_bytes)
        report_sha = sha(report_bytes)
        binding["sha256"] = report_sha
        self.manifest["reports"][index]["sha256"] = report_sha
        manifest_bytes = (json.dumps(self.manifest, sort_keys=True) + "\n").encode()
        manifest_path = self.root / self.summary["joern_metadata_projection"]["path"]
        manifest_path.write_bytes(manifest_bytes)
        self.summary["joern_metadata_projection"]["sha256"] = sha(manifest_bytes)
        for item in self.bindings:
            item["metadata_projection"] = dict(self.summary["joern_metadata_projection"])

    def test_copies_only_selected_reports_and_referenced_raw_files(self):
        self._add_report("fixture-a.json", "group-a-attempt-01-series-07", "case-a", b"raw-a\n")
        self._add_report("fixture-b.json", "group-b-attempt-01-series-07", "case-b", b"raw-b\n")
        orphan = self.root / "reports/releases/v0.9.2/attempts/orphan/capture/unused.json"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"not referenced\n")

        reports, raw_files, attempts = self._project()

        self.assertEqual([item["validation_path"] for item in reports],
                         ["reports/fixture-a.json", "reports/fixture-b.json"])
        self.assertEqual(len(raw_files), 2)
        self.assertEqual(len(attempts), 2)
        self.assertEqual((self.checkout / self.raw_paths[0]).read_bytes(), b"raw-a\n")
        self.assertFalse((self.checkout / "reports/releases/v0.9.2/attempts/orphan/capture/unused.json").exists())

    def test_rejects_raw_path_escape(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw\n")
        report_path = self.root / self.bindings[0]["staged_path"]
        report_value = json.loads(report_path.read_text())
        report_value["results"][0]["raw_output"] = "../escape.json"
        report_path.write_text(json.dumps(report_value, sort_keys=True) + "\n")
        self.bindings[0]["sha256"] = sha(report_path.read_bytes())
        receipt_path = self.root / "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/completed.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["reports"][0]["staged_sha256"] = self.bindings[0]["sha256"]
        receipt["reports"][0]["raw_output_mappings"][0]["captured_path"] = "../escape.json"
        receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "escapes its root"):
            self._project()

    def test_rejects_conflicting_raw_path_collision_within_a_report_receipt(self):
        shared = "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/capture/raw/shared.json"
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"same bytes\n",
                         raw_path=shared)
        staged = self.root / self.bindings[0]["staged_path"]
        report = json.loads(staged.read_text())
        report["results"].append({"case_id": "case-b", "raw_output": shared})
        report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode()
        staged.write_bytes(report_bytes)
        self.bindings[0]["sha256"] = sha(report_bytes)
        self.bindings[0]["rows"] = 2
        receipt_path = self.root / "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/completed.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["reports"][0]["staged_sha256"] = self.bindings[0]["sha256"]
        receipt["reports"][0]["raw_output_mappings"].append({
            "execution_relative": "raw/shared.json",
            "captured_path": shared,
            "sha256": "0" * 64,
            "bytes": len(b"same bytes\n"),
        })
        receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "repeats a raw-output path"):
            self._project()

    def test_rejects_tampered_raw_bytes(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"original\n")
        (self.root / self.raw_paths[0]).write_bytes(b"tampered\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "changed after checker verification"):
            self._project()

    def test_rejects_tampered_staged_report(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw\n")
        (self.root / self.bindings[0]["staged_path"]).write_bytes(b"{}\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "changed after checker verification"):
            self._project()

    def test_rejects_report_filename_collision(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw-a\n")
        self._add_report("fixture.json", "group-b-attempt-01-series-07", "case-b", b"raw-b\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "collide"):
            self._project()

    def test_projects_exact_joern_configuration_metadata_from_original_receipt(self):
        self._add_joern_projection()
        original_bytes = [(self.root / item["original_staged"]["path"]).read_bytes()
                          for item in self.bindings]

        reports, raw_files, attempts = self._project_joern()

        self.assertEqual(len(reports), 5)
        self.assertEqual(sum(item["rows"] for item in reports), 108)
        self.assertEqual(len(raw_files), 108)
        self.assertEqual(len(attempts), 1)
        self.assertTrue(all("original_staged_path" in item for item in reports))
        for item, binding, original in zip(reports, self.bindings, original_bytes):
            copied = self.checkout / item["validation_path"]
            expected = (self.root / binding["staged_path"]).read_bytes()
            self.assertEqual(copied.read_bytes(), expected)
            self.assertNotIn(b"configuration_hash", original)

    def test_rejects_derived_joern_outcome_mutation(self):
        self._add_joern_projection()
        report = json.loads((self.root / self.bindings[0]["staged_path"]).read_text())
        report["results"][0]["outcome"] = "reached"
        self._replace_derived_report(0, report)

        with self.assertRaisesRegex(validator.ValidationEvidenceError,
                                    "changes fields beyond configuration_hash"):
            self._project_joern()

    def test_rejects_derived_joern_raw_path_mutation(self):
        raw_paths = self._add_joern_projection()
        report = json.loads((self.root / self.bindings[0]["staged_path"]).read_text())
        report["results"][0]["raw_output"] = raw_paths[-1]
        self._replace_derived_report(0, report)

        with self.assertRaisesRegex(validator.ValidationEvidenceError,
                                    "changes fields beyond configuration_hash"):
            self._project_joern()

    def test_rejects_derived_joern_configuration_hash_mutation(self):
        self._add_joern_projection()
        report = json.loads((self.root / self.bindings[0]["staged_path"]).read_text())
        report["configuration_hash"] = "f" * 64
        self._replace_derived_report(0, report)

        with self.assertRaisesRegex(validator.ValidationEvidenceError,
                                    "changes fields beyond configuration_hash"):
            self._project_joern()

    def test_rejects_derived_joern_path_outside_fixed_projection(self):
        self._add_joern_projection()
        record = self.manifest["reports"][0]
        record["path"] = "execution-state/v092/publication-evidence/other/report.json"

        with patch.object(validator.JOERN_PROJECTION, "verify_existing_projection",
                          return_value=self.manifest):
            with self.assertRaisesRegex(validator.ValidationEvidenceError,
                                        "fixed publication projection"):
                validator._project_reports(
                    self.root, self.checkout, self.summary,
                    expected_report_count=5, expected_row_count=108,
                )


class V0151PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        contract_path = self.root / Path(*validator.V0151_CONTRACT.parts)
        contract_path.parent.mkdir(parents=True)
        self.contract_bytes = b'{"fixed":"C6"}\n'
        contract_path.write_bytes(self.contract_bytes)
        self.contract_path = contract_path
        self.runner = self.root / "runner"
        self.runner.write_text("#!/bin/sh\nexit 0\n")
        self.runner.chmod(0o755)
        runner_binding = {"path": str(self.runner), "sha256": sha(self.runner.read_bytes())}
        source_commit = "a" * 40
        runner_source_sha = "b" * 64
        self.source_inputs = [
            {"path": validator.V0151_SELECTOR.as_posix(), "sha256": "1" * 64},
            {"path": validator.V0151_WRAPPER.as_posix(), "sha256": runner_source_sha},
            {"path": validator.V0151_CORE.as_posix(), "sha256": "3" * 64},
            {"path": validator.JOERN_PROJECTION_HELPER.as_posix(), "sha256": "4" * 64},
            {"path": validator.JOERN_EXPORTER_HELPER.as_posix(), "sha256": "5" * 64},
        ]
        self.contract_value = {
            "source_snapshot": {
                "source_commit": source_commit,
                "runner_source": {
                    "path": validator.V0151_WRAPPER.as_posix(),
                    "sha256": runner_source_sha,
                },
                "source_inputs": self.source_inputs,
            },
            "runtime": {"runner": runner_binding},
        }
        self.c6_result = {
            "contract": self.contract_value,
            "contract_sha256": sha(self.contract_bytes),
            "source_commit": source_commit,
            "runner_path": runner_binding["path"],
        }
        selected_attempts = [{
            "attempt_id": f"group-{index:02d}-attempt-01-series-04",
            "status": "completed",
            "completed_receipt_sha256": f"{index + 1:064x}",
        } for index in range(84)]
        self.summary = {
            "schema": "dataflowbench-v0.9.2-publication-evidence-selection/v1",
            "status": "fresh-evidence-verified",
            "fresh_groups": 84,
            "fresh_partitions": 92,
            "fresh_rows": 4252,
            "case_count": 1108,
            "carried_partitions": 0,
            "carried_rows": 0,
            "fresh_reports": [{} for _ in range(92)],
            "selected_attempts": selected_attempts,
            "configuration_hash_validation": {
                "canonical_rust_validate_reports": "required separate final-delivery gate",
            },
            "scoring_enabled": False,
            "publication_approved": False,
        }
        self.selector = SimpleNamespace(
            V0151_CONTRACT_REL=validator.V0151_CONTRACT.as_posix(),
            V0151_WRAPPER_REL=validator.V0151_WRAPPER.as_posix(),
            SUMMARY_SCHEMA=self.summary["schema"],
            select_evidence=lambda root: self.summary,
        )
        self.wrapper = SimpleNamespace(
            PINNED_IDENTITY={"target_id": "bifrost-v0151-01", "version": "0.15.1"},
            CORE_SOURCE_REL=validator.V0151_CORE.as_posix(),
            load_target_profile=lambda core: {"profile": "fixed"},
        )

        class FakeCore:
            def __init__(inner, result):
                inner.TARGET_ID = "bifrost-v0151-01"
                inner.BIFROST_VERSION = "0.15.1"
                inner.SERIES = 4
                inner.SERIES_LABEL = "series-04"
                inner.CONTRACT_REL = validator.V0151_CONTRACT.as_posix()
                inner.result = result
                inner.validation_calls = []
                inner.configured_profile = None

            def configure_target_profile(inner, profile):
                inner.configured_profile = profile

            def _validate_contract(inner, root, contract_path, **kwargs):
                inner.validation_calls.append((root, contract_path, kwargs))
                return inner.result

        self.core = FakeCore(self.c6_result)
        self.source_refs = {
            "selector": {"path": validator.V0151_SELECTOR.as_posix(), "sha256": "1" * 64},
            "target_wrapper": {"path": validator.V0151_WRAPPER.as_posix(), "sha256": runner_source_sha},
            "target_core": {"path": validator.V0151_CORE.as_posix(), "sha256": "3" * 64},
            "joern_projection": {"path": validator.JOERN_PROJECTION_HELPER.as_posix(), "sha256": "4" * 64},
            "joern_exporter": {"path": validator.JOERN_EXPORTER_HELPER.as_posix(), "sha256": "5" * 64},
        }
        self.components = (self.selector, self.wrapper, self.core, self.source_refs)

    def _run_v0151(self):
        with patch.object(validator, "_load_v0151_preflight_modules", return_value=self.components), \
                patch.object(validator, "_source_identity", return_value={"commit": "a" * 40}):
            return validator._preflight(
                self.root, self.contract_path, evidence_source="v0151",
            )

    def test_v0151_preflight_calls_wrapper_core_and_real_selector_api(self):
        summary, validated, runner, source_identity = self._run_v0151()

        self.assertIs(summary, self.summary)
        self.assertEqual(runner, self.contract_value["runtime"]["runner"])
        self.assertEqual(source_identity, {"commit": "a" * 40})
        self.assertEqual(self.core.configured_profile, {"profile": "fixed"})
        self.assertEqual(self.core.validation_calls, [(
            self.root,
            validator.V0151_CONTRACT.as_posix(),
            {"require_approval": True, "require_committed": True, "check_current_source": True},
        )])
        self.assertEqual(validated["plan"], {
            "source_commit": "a" * 40,
            "runner_source_sha256": "b" * 64,
        })
        self.assertEqual(validated["source_inputs"], self.source_inputs)
        self.assertEqual(validated["tools"]["runner"], runner)
        self.assertEqual(validated["bytes_sha256"], sha(self.contract_bytes))
        self.assertEqual(validated["_validation_context"]["mode"], "v0151")

    def test_default_preflight_remains_on_the_c4_checker_and_executor(self):
        runner = self.contract_value["runtime"]["runner"]
        validated = {
            "tools": {"runner": runner},
            "plan": {"source_commit": "a" * 40, "runner_source_sha256": "b" * 64},
            "source_inputs": self.source_inputs,
        }
        with patch.object(validator.CHECKER, "verify", return_value=self.summary) as verify, \
                patch.object(validator, "_validate_checker_summary", return_value=self.summary), \
                patch.object(validator.EXECUTOR, "validate_plan", return_value=validated) as validate_plan, \
                patch.object(validator, "_source_identity", return_value={"commit": "c4"}):
            result = validator._preflight(self.root, self.contract_path)
        verify.assert_called_once_with(self.root, self.contract_path)
        validate_plan.assert_called_once_with(self.contract_path, repo_root=self.root)
        self.assertIs(result[1], validated)

    def test_rejects_wrong_v0151_target_before_selector_use(self):
        self.core.TARGET_ID = "bifrost-v0144-01"
        with patch.object(validator, "_load_v0151_preflight_modules", return_value=self.components), \
                self.assertRaisesRegex(validator.ValidationEvidenceError, "configured C6 core target"):
            validator._preflight_v0151(self.root, self.contract_path)
        self.assertEqual(self.core.validation_calls, [])

    def test_rejects_source_commit_mismatch_in_c6_adapter(self):
        self.c6_result["source_commit"] = "d" * 40
        with patch.object(validator, "_load_v0151_preflight_modules", return_value=self.components), \
                self.assertRaisesRegex(validator.ValidationEvidenceError, "source commit differs"):
            validator._preflight_v0151(self.root, self.contract_path)
        self.selector.select_evidence = lambda root: self.fail("selector must not run after source mismatch")

    def test_rejects_joern_helper_digest_mismatch_with_c6_source_closure(self):
        item = next(item for item in self.source_inputs
                    if item["path"] == validator.JOERN_PROJECTION_HELPER.as_posix())
        item["sha256"] = "f" * 64
        with patch.object(validator, "_load_v0151_preflight_modules", return_value=self.components), \
                self.assertRaisesRegex(validator.ValidationEvidenceError,
                                       "do not bind the loaded joern_projection source"):
            validator._preflight_v0151(self.root, self.contract_path)

    def test_rejects_runner_hash_mismatch_after_c6_validation(self):
        runner = self.contract_value["runtime"]["runner"]
        runner["sha256"] = "0" * 64
        with patch.object(validator, "_load_v0151_preflight_modules", return_value=self.components), \
                self.assertRaisesRegex(validator.ValidationEvidenceError, "SHA-256 differs"):
            validator._preflight_v0151(self.root, self.contract_path)

    def test_rejects_alternate_c6_contract_path_before_loading_modules(self):
        other = self.root / "other-contract.json"
        other.write_text("{}\n")
        with patch.object(validator, "_load_v0151_preflight_modules") as load_modules, \
                self.assertRaisesRegex(validator.ValidationEvidenceError, "fixed C6 contract"):
            validator._preflight_v0151(self.root, other)
        load_modules.assert_not_called()

    def test_v0151_metadata_binds_selector_and_c6_contract(self):
        validated = {
            "plan": {"source_commit": "a" * 40, "runner_source_sha256": "b" * 64},
            "source_inputs": self.source_inputs,
            "tools": {"runner": self.contract_value["runtime"]["runner"]},
            "bytes_sha256": sha(self.contract_bytes),
            "_validation_context": {
                "mode": "v0151",
                "contract_path": validator.V0151_CONTRACT.as_posix(),
                "contract_sha256": sha(self.contract_bytes),
                "selection_summary_sha256": "c" * 64,
                "selector_status": "fresh-evidence-verified",
                "source_modules": self.source_refs,
            },
        }
        identities = {key: dict(value) for key, value in self.source_refs.items()}
        with patch.object(validator, "_preflight", return_value=(
            self.summary, validated, self.contract_value["runtime"]["runner"], {"commit": "a" * 40},
        )), patch.object(validator, "_helper_identities", return_value=identities):
            result = validator.validate(
                root=self.root,
                contract_path=self.contract_path,
                output="v0151-metadata-probe",
                evidence_source="v0151",
            )
        self.assertEqual(result["evidence_source"], "v0151")
        self.assertEqual(result["target_contract"], {
            "path": validator.V0151_CONTRACT.as_posix(),
            "sha256": sha(self.contract_bytes),
        })
        self.assertEqual(result["selector"], {
            "path": validator.V0151_SELECTOR.as_posix(),
            "sha256": self.source_refs["selector"]["sha256"],
            "status": "fresh-evidence-verified",
            "summary_sha256": "c" * 64,
        })
        self.assertEqual(result["helper_identities"], identities)

    def test_cli_v0151_flag_selects_the_explicit_target_mode(self):
        with patch.object(validator, "validate", return_value={"status": "ready-to-execute"}) as validate:
            with redirect_stdout(io.StringIO()):
                result = validator.main(["--output", "cli-v0151-probe", "--v0151"])
        self.assertEqual(result, 0)
        validate.assert_called_once_with(
            contract_path=None,
            output="cli-v0151-probe",
            execute=False,
            evidence_source="v0151",
        )

    def test_helper_identities_bind_current_selector_and_report_projection_sources(self):
        _selector, _wrapper, _core, source_refs = validator._load_v0151_preflight_modules(validator.ROOT)

        identities = validator._helper_identities(source_refs)

        for key in ("selector", "target_wrapper", "target_core", "joern_projection", "joern_exporter"):
            self.assertEqual(identities[key], source_refs[key])
        self.assertEqual(
            identities["joern_exporter"]["path"],
            "scripts/joern_normal_reports_v092_projection.py",
        )

    def test_validator_dynamic_module_loader_ignores_valid_stale_pyc(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "dependency.py"
            source.write_bytes(b"VALUE = 'old'\n")
            fixed_mtime = 1_700_000_000
            os.utime(source, (fixed_mtime, fixed_mtime))
            prior_prefix = sys.pycache_prefix
            sys.pycache_prefix = str(Path(temporary) / "pycache")
            try:
                py_compile.compile(
                    str(source), cfile=importlib.util.cache_from_source(str(source)), doraise=True,
                )
                source.write_bytes(b"VALUE = 'new'\n")
                os.utime(source, (fixed_mtime, fixed_mtime))

                stale_spec = importlib.util.spec_from_file_location("stale_pyc_control", source)
                stale_module = importlib.util.module_from_spec(stale_spec)
                stale_spec.loader.exec_module(stale_module)
                self.assertEqual(stale_module.VALUE, "old")

                current = validator._load_module(source, "exact_source_control")
                self.assertEqual(current.VALUE, "new")
            finally:
                sys.pycache_prefix = prior_prefix


class CanonicalOutputTests(unittest.TestCase):
    def test_validation_artifacts_use_the_punctuated_release_namespace(self):
        self.assertEqual(validator.RECEIPTS.as_posix(), "reports/releases/v0.9.2/validation")
        self.assertEqual(validator.CHECKOUTS.as_posix(), "execution-state/v092/validation")

    def test_parses_exact_validator_counts_and_derives_not_derivable_honestly(self):
        metrics = validator._parse_stdout(
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        self.assertEqual(metrics, {
            "validated_reports": 92,
            "checked_configuration_hashes": 81,
            "known_stale": 0,
            "not_derivable": 11,
        })
        self.assertTrue(validator._validation_success(0, metrics))

    def test_rejects_missing_or_duplicate_metric_lines(self):
        invalid = [
            b"validated 92 reports\n",
            b"validated 92 reports\nvalidated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n",
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n",
        ]
        for stdout in invalid:
            with self.subTest(stdout=stdout):
                with self.assertRaises(validator.ValidationEvidenceError):
                    validator._parse_stdout(stdout)

    def test_wrong_report_count_and_known_stale_metric_cannot_pass(self):
        wrong_count = validator._parse_stdout(
            b"validated 91 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        known_stale = validator._parse_stdout(
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (1 known-stale under issue #138)\n"
        )
        self.assertFalse(validator._validation_success(0, wrong_count))
        self.assertFalse(validator._validation_success(0, known_stale))

    def test_zero_checked_configuration_hashes_cannot_pass(self):
        metrics = validator._parse_stdout(
            b"validated 92 reports\nchecked 0 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        self.assertEqual(metrics["not_derivable"], 92)
        self.assertFalse(validator._validation_success(0, metrics))

    def test_nonzero_exit_or_mismatched_counts_cannot_pass(self):
        metrics = {
            "validated_reports": 92,
            "checked_configuration_hashes": 90,
            "known_stale": 0,
            "not_derivable": 2,
        }
        self.assertFalse(validator._validation_success(1, metrics))
        self.assertFalse(validator._validation_success(0, {**metrics, "validated_reports": 91}))
        self.assertFalse(validator._validation_success(0, {**metrics, "known_stale": 1}))

    def test_invokes_only_the_bound_runner_validate_reports_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "fake-runner"
            binary.write_text(
                "#!/bin/sh\n"
                "[ \"$1\" = \"--population\" ] && [ \"$2\" = \"v0.9.0\" ] && [ \"$3\" = \"validate-reports\" ] || exit 91\n"
                "printf 'validated 92 reports\\nchecked 90 configuration hashes against the working tree (0 known-stale under issue #138)\\n'\n"
                "printf 'fake canonical harness\\n' >&2\n"
            )
            binary.chmod(0o755)
            checkout = root / "checkout"
            checkout.mkdir()
            binding = {"path": str(binary), "sha256": sha(binary.read_bytes())}
            env = {"PATH": "/usr/bin:/bin", "HOME": str(checkout), "TMPDIR": str(checkout), "LANG": "C", "LC_ALL": "C"}

            result = validator._invoke_runner(binding, checkout, env)

            self.assertEqual(result["argv"], [str(binary), "--population", "v0.9.0", "validate-reports"])
            self.assertEqual(result["cwd"], str(checkout))
            self.assertEqual(result["exit_code"], 0)
            self.assertIn(b"validated 92 reports", result["stdout"])
            self.assertEqual(result["stderr"], b"fake canonical harness\n")

    def test_rejects_runner_binary_hash_drift_before_invocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "fake-runner"
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            binding = {"path": str(binary), "sha256": "0" * 64}
            with self.assertRaisesRegex(validator.ValidationEvidenceError, "SHA-256 differs"):
                validator._invoke_runner(binding, root, {"PATH": "/usr/bin:/bin"})


if __name__ == "__main__":
    unittest.main()
