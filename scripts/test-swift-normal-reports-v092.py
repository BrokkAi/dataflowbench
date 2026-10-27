#!/usr/bin/env python3
"""Focused provenance checks for the v0.9.2 CodeQL report boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import swift_normal_reports_v092 as reports


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CodeQLReportProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.plan_path = self.root / reports.PLAN_PATH
        self.plan_path.parent.mkdir(parents=True)
        self.identity = {
            "tool": "codeql", "tool_version": "2.27.2", "tool_build_identity": "exact-build",
            "adapter_version": "swift-normal-v092",
        }
        self.plan = {"schema": reports.PLAN_SCHEMA, "identity": self.identity}
        self.plan_path.write_text(json.dumps(self.plan))
        receipt_path = self.root / "reports/releases/v0.9.2/qualification/query/receipt.json"
        receipt_path.parent.mkdir(parents=True)
        self.receipt = {"plan_path": reports.PLAN_PATH, "queries": {}}
        receipt_path.write_text(json.dumps(self.receipt))
        self.query_ref = {"path": receipt_path.relative_to(self.root).as_posix(), "sha256": digest(receipt_path)}
        self.results = []
        for index in range(108):
            raw_path = self.root / "reports/raw/cases" / f"case-{index:03d}.json"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps({"schema": reports.RAW_SCHEMA, "query_qualification": self.query_ref}))
            self.results.append({
                "case_id": f"case-{index:03d}",
                "raw": {"path": raw_path.relative_to(self.root).as_posix(), "sha256": digest(raw_path)},
            })
        self.run = {
            "schema": reports.RUN_SCHEMA,
            "plan_sha256": digest(self.plan_path),
            "identity": self.identity,
            "query_qualification": self.query_ref,
            "results": self.results,
        }

    def test_missing_run_receipt_is_rejected(self):
        run = dict(self.run)
        del run["query_qualification"]
        with patch("swift_normal_runner_v092.verify_query_receipt"):
            with self.assertRaisesRegex(ValueError, "fresh CodeQL query qualification receipt"):
                reports.validate_query_provenance(self.root, reports.PLAN_PATH, run)

    def test_raw_receipt_must_equal_run_receipt(self):
        raw_path = self.root / self.results[17]["raw"]["path"]
        raw = json.loads(raw_path.read_text())
        raw["query_qualification"] = {"path": self.query_ref["path"], "sha256": "0" * 64}
        raw_path.write_text(json.dumps(raw))
        self.results[17]["raw"]["sha256"] = digest(raw_path)
        with patch("swift_normal_runner_v092.verify_query_receipt"):
            with self.assertRaisesRegex(ValueError, "raw CodeQL query provenance differs"):
                reports.validate_query_provenance(self.root, reports.PLAN_PATH, self.run)

    def test_query_revalidation_is_rejected(self):
        run = dict(self.run, query_revalidation={"path": "old.json", "sha256": "a" * 64})
        with patch("swift_normal_runner_v092.verify_query_receipt"):
            with self.assertRaisesRegex(ValueError, "query revalidation is forbidden"):
                reports.validate_query_provenance(self.root, reports.PLAN_PATH, run)

    def test_export_replays_provenance_then_delegates_with_v092_plan_compatibility(self):
        fake_reporter = SimpleNamespace()
        fake_reporter.read = lambda path: json.loads(Path(path).read_text())

        def fake_export(root, plan_path, run):
            self.assertEqual(fake_reporter.read(root / plan_path)["schema"], "swift-normal-report-plan/v1")
            self.assertIs(run, self.run)
            return {"delegated": True}

        fake_reporter.export = fake_export
        with patch("swift_normal_runner_v092.verify_query_receipt") as verify, \
             patch.object(reports.common, "private_engine", return_value={"reports": fake_reporter}):
            self.assertEqual(reports.export(self.root, reports.PLAN_PATH, self.run), {"delegated": True})
            verify.assert_called_once_with(self.root, self.plan, self.receipt, reports.PLAN_PATH)
        self.assertEqual(json.loads(self.plan_path.read_text())["schema"], reports.PLAN_SCHEMA)


if __name__ == "__main__":
    unittest.main()
