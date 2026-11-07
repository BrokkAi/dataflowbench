#!/usr/bin/env python3
"""Focused pure-fixture tests for v0.9.2 publication evidence selection."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import py_compile
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("select-v092-publication-evidence.py")
SPEC = importlib.util.spec_from_file_location("select_v092_publication_evidence_tests", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load selector: {SCRIPT}")
selector = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = selector
SPEC.loader.exec_module(selector)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fixture_plan():
    groups = [
        {
            "id": "codeql-java-kernel", "tool": "codeql", "case_ids": ["case-a", "case-b"],
            "reports": ["reports/releases/v0.9.0/normal/codeql-java-kernel.json",
                        "reports/releases/v0.9.0/normal/codeql-java-extra.json"],
        },
        {
            "id": "joern-swift-common108", "tool": "joern", "case_ids": ["case-c"],
            "reports": ["reports/releases/v0.9.0/normal/joern-swift-partition.json"],
        },
        {
            "id": "bifrost-c-kernel", "tool": "bifrost", "case_ids": ["case-d"],
            "reports": ["reports/releases/v0.9.0/normal/bifrost-c-kernel.json"],
        },
    ]
    partitions = [
        (groups[0]["id"], groups[0]["reports"][0], ["case-a"]),
        (groups[0]["id"], groups[0]["reports"][1], ["case-b"]),
        (groups[1]["id"], groups[1]["reports"][0], ["case-c"]),
        (groups[2]["id"], groups[2]["reports"][0], ["case-d"]),
    ]
    reports = []
    for index, (group_id, path, case_ids) in enumerate(partitions):
        reports.append({
            "id": f"report-{index}", "execution_group": group_id,
            "report": path, "case_ids": case_ids,
        })
    return {
        "schema_version": 1,
        "execution_group_count": 3,
        "expected_cases": 4,
        "expected_report_partitions": 4,
        "expected_report_rows": 4,
        "fixture_revision": "sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62",
        "population": dict(selector.POPULATION_REF),
        "execution_groups": groups,
        "reports": reports,
    }


def fixture_bindings(plan):
    out = []
    attempts = []
    group_sha = {}
    for group in plan["execution_groups"]:
        attempt_id = f"{group['id']}-attempt-01"
        receipt_sha = sha((attempt_id + "-receipt").encode())
        group_sha[group["id"]] = (attempt_id, receipt_sha)
        attempts.append({
            "attempt_id": attempt_id, "group_id": group["id"],
            "status": "completed", "completed_receipt_sha256": receipt_sha,
        })
    for report in plan["reports"]:
        attempt_id, receipt_sha = group_sha[report["execution_group"]]
        rows = [{"case_id": case_id, "raw_output": f"raw/{case_id}.json"}
                for case_id in report["case_ids"]]
        raw = (json.dumps({"results": rows}, sort_keys=True) + "\n").encode()
        out.append({
            "adapter": selector._report_adapter(report),
            "attempt_id": attempt_id,
            "attempt_number": 1,
            "sha256": sha(raw),
            "rows": len(rows),
            "staged_path": f"reports/releases/v0.9.2/normal/attempts/{attempt_id}/{Path(report['report']).name}",
            "_case_ids": list(report["case_ids"]),
            "_group_id": report["execution_group"],
            "_receipt_sha256": receipt_sha,
        })
    return out, attempts


def joern_fixture():
    return {
        "scored_activation": False,
        "configuration_ready": False,
        "full_release_gate_satisfied": False,
        "publication_approved": False,
        "typed_outcomes": {"inconclusive": 96, "unsupported": 12},
        "projection_ref": {"path": "projection.json", "sha256": "b" * 64},
    }


def bifrost_fixture():
    return {
        "status": "completed", "target_id": selector.V0151_TARGET_ID,
        "full_policy_qualification": False,
        "reconciliation_sha256": "e" * 64,
        "wrapper": {"path": selector.V0151_WRAPPER_REL, "sha256": "f" * 64},
        "core": {"path": "scripts/bifrost_v0144_benchmark.py", "sha256": "1" * 64},
        "target_profile": {"path": "profile.json", "sha256": "2" * 64},
        "contract": {"path": selector.V0151_CONTRACT_REL, "sha256": "3" * 64},
        "summary_ref": {"path": "series-summary.json", "sha256": "c" * 64},
    }


def joern_projection_fixture(root: Path):
    output_dir = root / selector.JOERN_OUTPUT_REL
    output_dir.mkdir(parents=True)
    partitions = [
        ("joern-swift-core.json", 66),
        ("joern-swift-modeling.json", 24),
        ("joern-swift-calibration.json", 4),
        ("joern-swift-native.json", 12),
        ("joern-swift-language-extension.json", 2),
    ]
    records = []
    plan_by_path = {}
    next_case = 0
    for name, count in partitions:
        case_ids = [f"joern-case-{index:03d}" for index in range(next_case, next_case + count)]
        next_case += count
        report_path = f"reports/releases/v0.9.0/normal/{name}"
        plan_by_path[report_path] = {
            "report": report_path, "execution_group": selector.JOERN_GROUP_ID,
            "case_ids": case_ids,
        }
        payload = {"results": [{"case_id": case_id} for case_id in case_ids]}
        report_bytes = (json.dumps(payload, sort_keys=True) + "\n").encode()
        projected_path = (Path(selector.JOERN_OUTPUT_REL) / name).as_posix()
        (root / projected_path).write_bytes(report_bytes)
        staged = {
            "path": f"reports/releases/v0.9.2/normal/attempts/{selector.JOERN_ATTEMPT_ID}/{name}",
            "sha256": "a" * 64,
        }
        records.append({
            "path": projected_path, "sha256": sha(report_bytes), "cases": count,
            "case_ids": case_ids, "staged": staged,
        })
    manifest = {
        "schema": "v092-joern108-publication-projection/v1",
        "status": "verified-derived-report-metadata",
        "attempt_id": selector.JOERN_ATTEMPT_ID,
        "group_id": selector.JOERN_GROUP_ID,
        "case_count": 108,
        "report_count": 5,
        "typed_outcomes": {"inconclusive": 96, "unsupported": 12},
        "scored_activation": False,
        "configuration_ready": False,
        "full_release_gate_satisfied": False,
        "publication_approved": False,
        "reports": records,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output_dir / "projection.json").write_bytes(manifest_bytes)
    return dict(manifest, manifest_sha256=sha(manifest_bytes)), plan_by_path


def joern_projection_fixture_plan_specs():
    partitions = [
        ("joern-swift-core.json", 66),
        ("joern-swift-modeling.json", 24),
        ("joern-swift-calibration.json", 4),
        ("joern-swift-native.json", 12),
        ("joern-swift-language-extension.json", 2),
    ]
    specs = []
    next_case = 0
    for name, count in partitions:
        report_path = f"reports/releases/v0.9.0/normal/{name}"
        specs.append({
            "report": report_path, "execution_group": selector.JOERN_GROUP_ID,
            "case_ids": [f"joern-case-{index:03d}" for index in range(next_case, next_case + count)],
        })
        next_case += count
    return specs


class MockJoernProjectionHelper:
    class ProjectionError(ValueError):
        pass

    def __init__(self):
        self.calls = []

    def verify_and_project(self, root, output_dir):
        self.calls.append(("create", output_dir))
        manifest, _ = joern_projection_fixture(root)
        return manifest

    def verify_existing_projection(self, root, manifest_ref):
        self.calls.append(("verify-existing", dict(manifest_ref)))
        raw = (root / manifest_ref["path"]).read_bytes()
        self.assert_sha(raw, manifest_ref["sha256"])
        value = json.loads(raw)
        return dict(value, manifest_sha256=sha(raw))

    @staticmethod
    def assert_sha(raw, expected):
        if sha(raw) != expected:
            raise MockJoernProjectionHelper.ProjectionError("manifest reference mismatch")


class SelectorPureFixtureTests(unittest.TestCase):
    def test_joern_projection_creation_returns_manifest_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = MockJoernProjectionHelper()
            report_by_path = {
                spec["report"]: spec
                for spec in joern_projection_fixture_plan_specs()
            }
            with patch.object(selector, "_load_module", return_value=helper):
                manifest, reports, metadata = selector._run_joern_projection(root, report_by_path)
            self.assertEqual(helper.calls, [("create", selector.JOERN_OUTPUT_REL)])
            self.assertEqual(metadata, {"projection": {
                "path": selector.JOERN_MANIFEST_REL,
                "sha256": manifest["manifest_sha256"],
            }})
            self.assertEqual(len(reports), 5)
            self.assertTrue(all(report["metadata_projection"] == metadata["projection"]
                                for report in reports))

    def test_joern_existing_projection_is_reverified_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, report_by_path = joern_projection_fixture(root)
            before = {path.relative_to(root): path.read_bytes()
                      for path in root.rglob("*") if path.is_file()}
            helper = MockJoernProjectionHelper()
            with patch.object(selector, "_load_module", return_value=helper):
                manifest, reports, metadata = selector._run_joern_projection(root, report_by_path)
            after = {path.relative_to(root): path.read_bytes()
                     for path in root.rglob("*") if path.is_file()}
            self.assertEqual(helper.calls[0][0], "verify-existing")
            self.assertEqual(before, after)
            self.assertEqual(len(reports), 5)
            self.assertEqual(metadata["projection"]["sha256"], manifest["manifest_sha256"])

    def test_positive_exact_join_has_expected_checker_shape_and_closed_gates(self):
        plan = fixture_plan()
        reports, attempts = fixture_bindings(plan)
        summary = selector.build_checker_summary(
            plan, reports, attempts,
            retained_stage={"runtime_authority_reused": False, "analyzer_dispatches": 0,
                            "failure_history": []},
            ledger_binding={"path": selector.LEDGER_PATH, "sha256": "d" * 64,
                            "prefix_130": selector.PREFIX_130_SHA256,
                            "prefix_131": selector.PREFIX_131_SHA256},
            joern_projection=joern_fixture(),
            bifrost_reconciliation=bifrost_fixture(),
            counts=selector.Counts(3, 4, 4, 4, 1, 1, 1),
        )
        self.assertEqual(summary["status"], "fresh-evidence-verified")
        self.assertEqual((summary["fresh_groups"], summary["fresh_partitions"],
                          summary["fresh_rows"], summary["case_count"]), (3, 4, 4, 4))
        self.assertEqual(summary["configuration_hash_validation"]["canonical_rust_validate_reports"],
                         "required separate final-delivery gate")
        self.assertFalse(summary["scoring_enabled"])
        self.assertFalse(summary["scorecard_generation_allowed"])
        self.assertFalse(summary["publication_approved"])

    def test_report_digest_tamper_is_rejected(self):
        binding = {"sha256": "0" * 64, "rows": 1}
        report = b'{"results":[{"case_id":"case-a"}]}\n'
        with self.assertRaisesRegex(selector.SelectionError, "SHA-256 mismatch"):
            selector.verify_report_payload(binding, report, ["case-a"], "sample report")

    def test_report_case_membership_tamper_is_rejected_even_with_recomputed_hash(self):
        report = b'{"results":[{"case_id":"case-x"}]}\n'
        binding = {"sha256": sha(report), "rows": 1}
        with self.assertRaisesRegex(selector.SelectionError, "case IDs differ"):
            selector.verify_report_payload(binding, report, ["case-a"], "sample report")

    def test_ledger_prefix_tamper_is_rejected(self):
        lines = [json.dumps({"attempt_id": f"attempt-{i:03d}", "status": "completed"}).encode() + b"\n"
                 for i in range(131)]
        valid = b"".join(lines)
        expected_130 = sha(b"".join(lines[:130]))
        expected_131 = sha(valid)
        result = selector.verify_ledger_bytes(
            valid, {"attempt-000", "attempt-130"}, expected_130, expected_131,
        )
        self.assertEqual(result["line_count"], 131)
        tampered = valid.replace(b'"status": "completed"', b'"status": "failed"', 1)
        with self.assertRaisesRegex(selector.SelectionError, "130-row ledger prefix"):
            selector.verify_ledger_bytes(
                tampered, {"attempt-000", "attempt-130"}, expected_130, expected_131,
            )

    def test_diagnostic_boolean_cannot_substitute_for_core_reconciliation(self):
        core = SimpleNamespace(RECONCILIATION_SCHEMA="target-reconcile/v1")
        diagnostic = {
            "status": "completed", "eligible": True, "output_rows_complete": True,
            "target_group_count": 20, "completed_group_count": 20,
        }
        with self.assertRaisesRegex(selector.SelectionError, "core.reconcile_outputs"):
            selector._validate_bifrost_reconciliation(diagnostic, core, {})

    def test_scoring_or_publication_promotion_is_rejected(self):
        plan = fixture_plan()
        reports, attempts = fixture_bindings(plan)
        joern = joern_fixture()
        joern["scored_activation"] = True
        with self.assertRaisesRegex(selector.SelectionError, "overstates scoring"):
            selector.build_checker_summary(
                plan, reports, attempts,
                retained_stage={"runtime_authority_reused": False, "analyzer_dispatches": 0},
                ledger_binding={}, joern_projection=joern,
                bifrost_reconciliation=bifrost_fixture(),
                counts=selector.Counts(3, 4, 4, 4, 1, 1, 1),
            )

    def test_incomplete_case_join_is_rejected(self):
        plan = fixture_plan()
        reports, attempts = fixture_bindings(plan)
        reports.pop()
        with self.assertRaisesRegex(selector.SelectionError, "report count"):
            selector._validate_join(plan, reports, attempts, counts=selector.Counts(3, 4, 4, 4, 1, 1, 1))

    def test_group_report_roster_must_match_top_level_partition_map(self):
        plan = fixture_plan()
        population = {
            "fixture_revision": plan["fixture_revision"],
            "cases": [{"id": case_id} for case_id in ["case-a", "case-b", "case-c", "case-d"]],
        }
        plan["execution_groups"][0]["reports"].pop()
        with self.assertRaisesRegex(selector.SelectionError, "group report roster"):
            selector._group_and_report_plan(
                plan, population, selector.Counts(3, 4, 4, 4, 1, 1, 1),
            )

    def test_dynamic_loader_executes_source_despite_timestamp_valid_old_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cached_helper.py"
            source.write_bytes(b'VALUE = "old"\n')
            before = source.stat()
            py_compile.compile(str(source), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            current = b'VALUE = "new"\n'
            source.write_bytes(current)
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
            name = "selector_exact_source_loader_test"
            try:
                loaded = selector._load_module(source, name)
                self.assertEqual(loaded.VALUE, "new")
                self.assertEqual(loaded.__verified_source_sha256__, sha(current))
            finally:
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
