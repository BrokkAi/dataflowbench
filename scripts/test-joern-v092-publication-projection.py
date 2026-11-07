#!/usr/bin/env python3
"""Focused tests for Joern v0.9.2 report metadata and retained projection."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import joern_normal_reports_v092_projection as exporter
import joern_v092_publication_projection as projection


PLAN_PATH = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-finalization-03/attempt-07/execution-plan.json"
RUN_PATH = "execution-state/v092/groups/series-02/joern-swift-common108/attempt-05/reports/raw/joern-common-v2/current108-v092-01/run.json"
EXPECTED_CONFIGURATION_HASH = "5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e"


class JoernExporterConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = exporter.read(ROOT / PLAN_PATH)
        self.run = exporter.read(ROOT / RUN_PATH)

    def test_projection_uses_versioned_exporter_and_preserves_measured_source(self) -> None:
        measured_ref = next(
            reference for reference in self.plan["configurations"]["joern-current108"]
            if reference["path"] == "scripts/joern_normal_reports_v092.py"
        )
        measured_hash = hashlib.sha256((ROOT / measured_ref["path"]).read_bytes()).hexdigest()
        self.assertEqual(measured_hash, measured_ref["sha256"])
        projection_hash = exporter.sha(ROOT / "scripts/joern_normal_reports_v092_projection.py")
        self.assertEqual(projection.exporter.__source_sha256__, projection_hash)

    def test_export_binds_configuration_hash_and_all_108_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "execution-state/v092") as directory:
            output = Path(directory) / "reports"
            written = exporter.export(ROOT, PLAN_PATH, self.run, output)
            self.assertEqual(len(written), 5)
            self.assertEqual(sum(len(item["case_ids"]) for item in written), 108)
            reports = [json.loads(path.read_text()) for path in sorted(output.glob("report-*.json"))]
            self.assertEqual(len(reports), 5)
            self.assertTrue(all(report["configuration_hash"] == EXPECTED_CONFIGURATION_HASH for report in reports))
            self.assertTrue(all(report["scored_activation"] is False for report in reports))
            self.assertTrue(all(report["aggregate_resource_qualification"] == "unavailable" for report in reports))
            ids = [row["case_id"] for report in reports for row in report["results"]]
            self.assertEqual(len(ids), 108)
            self.assertEqual(len(set(ids)), 108)

    def test_configuration_hash_rejects_changed_or_unsafe_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = root / "models.json"
            config.write_text('{"models":[]}\n')
            reference = {"path": "models.json", "sha256": exporter.sha(config)}
            plan = {"configurations": {"joern-current108": [reference]}}
            expected = hashlib.sha256(b"models.json" + config.read_bytes()).hexdigest()
            self.assertEqual(exporter.configuration_hash(root, plan), expected)
            config.write_text('{"models":["tampered"]}\n')
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                exporter.configuration_hash(root, plan)
            plan["configurations"]["joern-current108"] = [{"path": "../models.json", "sha256": reference["sha256"]}]
            with self.assertRaisesRegex(ValueError, "unsafe"):
                exporter.configuration_hash(root, plan)

    def test_same_plan_run_from_an_alternate_attempt_cannot_use_attempt05_snapshot(self) -> None:
        alternate = copy.deepcopy(self.run)
        for row in alternate["results"]:
            row["raw"]["path"] = row["raw"]["path"].replace("/attempt-05/", "/attempt-04/")
        with tempfile.TemporaryDirectory(dir=ROOT / "execution-state/v092") as directory:
            with self.assertRaisesRegex(ValueError, "exact retained attempt-05 run"):
                exporter.export(ROOT, PLAN_PATH, alternate, Path(directory) / "reports")

    def test_matching_alternate_row_and_raw_configuration_is_rejected(self) -> None:
        altered = copy.deepcopy(self.run)
        row = altered["results"][0]
        raw = exporter.read(ROOT / row["raw"]["path"])
        row["configuration"] = "joern-alternate-configuration"
        raw["configuration"] = row["configuration"]
        with tempfile.TemporaryDirectory(dir=ROOT / "execution-state/v092") as directory:
            raw_path = Path(directory) / "alternate-configuration-raw.json"
            raw_path.write_text(json.dumps(raw, sort_keys=True) + "\n")
            row["raw"] = {
                "path": raw_path.relative_to(ROOT).as_posix(),
                "sha256": exporter.sha(raw_path),
            }
            self.assertEqual(exporter.read(raw_path)["configuration"], row["configuration"])
            with self.assertRaisesRegex(ValueError, "exact joern-current108 plan"):
                exporter.export(ROOT, PLAN_PATH, altered, Path(directory) / "reports")

    def test_projection_dependency_loader_ignores_valid_stale_pyc(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "dependency.py"
            source.write_bytes(b"VALUE = 'old'\n")
            fixed_mtime = 1_700_000_000
            os.utime(source, (fixed_mtime, fixed_mtime))
            prior_prefix = sys.pycache_prefix
            sys.pycache_prefix = str(Path(directory) / "pycache")
            try:
                py_compile.compile(
                    str(source), cfile=importlib.util.cache_from_source(str(source)), doraise=True,
                )
                source.write_bytes(b"VALUE = 'new'\n")
                os.utime(source, (fixed_mtime, fixed_mtime))

                stale_spec = importlib.util.spec_from_file_location("projection_stale_pyc_control", source)
                stale_module = importlib.util.module_from_spec(stale_spec)
                stale_spec.loader.exec_module(stale_module)
                self.assertEqual(stale_module.VALUE, "old")

                current = projection._load_exact_source(source, "projection_exact_source_control")
                self.assertEqual(current.VALUE, "new")
            finally:
                sys.pycache_prefix = prior_prefix


class RetainedProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT
        self.supplement = projection._verify_supplement(self.root, projection.VERIFICATION_REF)
        _path, terminal_bytes = projection._bound(self.root, self.supplement["terminal"], "test terminal")
        self.terminal = projection._json(terminal_bytes, "test terminal")
        _path, plan_bytes = projection._bound(self.root, self.supplement["plan"], "test plan")
        self.plan = projection._json(plan_bytes, "test plan")
        self.partitions, self.case_set = projection._load_partition_specs(self.root)
        self.config_hash = exporter.configuration_hash(
            self.root, self.plan, source_snapshot=exporter.HISTORICAL_SOURCE_SNAPSHOT,
        )

    def _report_inputs(self, index: int = 0):
        partition = self.partitions[index]
        evidence_record = self.supplement["reports"][index]
        terminal_record = self.terminal["reports"][index]
        return partition, evidence_record, terminal_record

    def test_append_only_projection_preserves_raw_typed_and_partition_order(self) -> None:
        ledger_before = (self.root / self.supplement["ledger"]["path"]).read_bytes()
        completion_before = (self.root / self.supplement["terminal"]["path"]).read_bytes()
        source_refs = [record["source"] for record in self.supplement["reports"]]
        source_before = [(self.root / ref["path"]).read_bytes() for ref in source_refs]
        staged_refs = [record["staged"] for record in self.supplement["reports"]]
        staged_before = [(self.root / ref["path"]).read_bytes() for ref in staged_refs]
        flattened = [case for partition in self.partitions for case in partition["case_ids"]]
        self.assertEqual(set(flattened), self.case_set)
        self.assertEqual(set(self.terminal["case_ids"]), self.case_set)
        self.assertNotEqual(flattened, self.terminal["case_ids"])

        with tempfile.TemporaryDirectory(dir=self.root / "execution-state/v092") as directory:
            output = Path(directory) / "publication-projection"
            result = projection.verify_and_project(self.root, output)
            self.assertEqual(result["configuration_hash"], EXPECTED_CONFIGURATION_HASH)
            self.assertEqual(result["typed_outcomes"], {"inconclusive": 96, "unsupported": 12})
            self.assertFalse(result["scored_activation"])
            self.assertFalse(result["publication_approved"])
            self.assertEqual(result["ledger_binding"]["binding"], "historical-prefix-131")
            self.assertEqual(
                result["ledger_binding"]["historical_prefix_sha256"],
                projection.EXPECTED_LEDGER_REF["sha256"],
            )
            self.assertEqual(
                result["ledger_binding"]["current_file_sha256"],
                hashlib.sha256(ledger_before).hexdigest(),
            )
            self.assertEqual(len(result["reports"]), 5)
            manifest_path = output / "projection.json"
            manifest_ref = {
                "path": manifest_path.relative_to(self.root).as_posix(),
                "sha256": projection._sha(manifest_path.read_bytes()),
            }
            verified_existing = projection.verify_existing_projection(
                self.root, manifest_ref, expected_path=manifest_ref["path"],
            )
            self.assertEqual(verified_existing["manifest_sha256"], manifest_ref["sha256"])
            self.assertEqual(verified_existing["reports"], result["reports"])
            for item, partition in zip(result["reports"], self.partitions):
                report = json.loads((self.root / item["path"]).read_text())
                _derived_path, derived_bytes = projection._bound(
                    self.root, item["derived_staged"], "test derived staged report",
                )
                self.assertEqual(report, json.loads(derived_bytes))
                self.assertEqual([row["case_id"] for row in report["results"]], partition["case_ids"])
                self.assertEqual(report["configuration_hash"], EXPECTED_CONFIGURATION_HASH)
                self.assertTrue(all(row["raw_output"].startswith(
                    "reports/releases/v0.9.2/attempts/" + projection.ATTEMPT_ID + "/capture/"
                ) for row in report["results"]))
                self.assertEqual(item["raw_outputs"], [
                    {"case_id": row["case_id"], "path": row["raw_output"], "sha256": row["raw_sha256"]}
                    for row in report["results"]
                ])
        self.assertEqual(ledger_before, (self.root / self.supplement["ledger"]["path"]).read_bytes())
        self.assertEqual(completion_before, (self.root / self.supplement["terminal"]["path"]).read_bytes())
        self.assertEqual(source_before, [(self.root / ref["path"]).read_bytes() for ref in source_refs])
        self.assertEqual(staged_before, [(self.root / ref["path"]).read_bytes() for ref in staged_refs])

    def test_changed_report_digest_is_rejected(self) -> None:
        partition, evidence_record, terminal_record = self._report_inputs()
        changed = copy.deepcopy(evidence_record)
        changed["source"]["sha256"] = "0" * 64
        changed_terminal = copy.deepcopy(terminal_record)
        changed_terminal["original_sha256"] = "0" * 64
        with self.assertRaisesRegex(projection.ProjectionError, "SHA-256 mismatch"):
            projection._verify_report_pair(
                self.root, self.supplement, self.plan, self.terminal, partition,
                changed, changed_terminal, self.config_hash,
            )

    def test_partition_case_order_is_checked_independently_of_group_order(self) -> None:
        partition, evidence_record, terminal_record = self._report_inputs()
        reversed_partition = dict(partition, case_ids=list(reversed(partition["case_ids"])))
        with self.assertRaisesRegex(projection.ProjectionError, "partition row order"):
            projection._verify_report_pair(
                self.root, self.supplement, self.plan, self.terminal, reversed_partition,
                evidence_record, terminal_record, self.config_hash,
            )

    def test_captured_raw_digest_is_bound_to_original_report(self) -> None:
        partition, evidence_record, terminal_record = self._report_inputs()
        changed_terminal = copy.deepcopy(terminal_record)
        changed_terminal["raw_output_mappings"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(projection.ProjectionError, "SHA-256 mismatch"):
            projection._verify_report_pair(
                self.root, self.supplement, self.plan, self.terminal, partition,
                evidence_record, changed_terminal, self.config_hash,
            )

    def test_projection_refuses_to_reuse_an_existing_output_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root / "execution-state/v092") as directory:
            output = Path(directory) / "already-selected"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("existing projection stays intact\n")
            with self.assertRaisesRegex(projection.ProjectionError, "new directory"):
                projection.verify_and_project(self.root, output)
            self.assertEqual(marker.read_text(), "existing projection stays intact\n")

    def test_valid_complete_suffix_keeps_historical_prefix_binding(self) -> None:
        prefix = [json.dumps({"row": index}, separators=(",", ":")).encode() + b"\n"
                  for index in range(131)]
        suffix = json.dumps({"group_id": "series04", "attempt": 1},
                            separators=(",", ":")).encode() + b"\n"
        prefix_sha = hashlib.sha256(b"".join(prefix)).hexdigest()
        terminal = json.loads(prefix[-1])
        result = projection._verify_ledger_lines(iter(prefix + [suffix]), prefix_sha, terminal)
        self.assertEqual(result["binding"], "historical-prefix-131")
        self.assertEqual(result["historical_prefix_sha256"], prefix_sha)
        self.assertEqual(result["appended_suffix_rows"], 1)
        self.assertEqual(result["current_file_sha256"], hashlib.sha256(b"".join(prefix + [suffix])).hexdigest())

    def test_tampered_prefix_and_truncated_suffix_are_rejected(self) -> None:
        prefix = [json.dumps({"row": index}, separators=(",", ":")).encode() + b"\n"
                  for index in range(131)]
        prefix_sha = hashlib.sha256(b"".join(prefix)).hexdigest()
        terminal = json.loads(prefix[-1])
        tampered = list(prefix)
        tampered[0] = b'{"row":999}\n'
        with self.assertRaisesRegex(projection.ProjectionError, "prefix SHA-256 mismatch"):
            projection._verify_ledger_lines(iter(tampered), prefix_sha, terminal)
        truncated_suffix = prefix + [b'{"attempt":132}']
        with self.assertRaisesRegex(projection.ProjectionError, "incomplete"):
            projection._verify_ledger_lines(iter(truncated_suffix), prefix_sha, terminal)


if __name__ == "__main__":
    unittest.main()
