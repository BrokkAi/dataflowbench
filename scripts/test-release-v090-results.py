#!/usr/bin/env python3
"""Focused tests for the prospective v0.9.0 release wrapper."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("check-release-v090-results.py")
SPEC = importlib.util.spec_from_file_location("check_release_v090_results", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class ReleaseV090Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="dfb-release-v090-test-")
        self.root = Path(self.temp.name)
        self.population_ids = [f"case-{index:04d}" for index in range(GATE.EXPECTED_CASES)]
        self.partitions = self._partition_memberships()
        self.plan = {
            "schema_version": 1,
            "release": GATE.RELEASE,
            "status": "pending-parent-review",
            "execution_blockers": ["parent plan review"],
            "expected_cases": GATE.EXPECTED_CASES,
            "expected_report_partitions": GATE.EXPECTED_REPORT_PARTITIONS,
            "expected_report_rows": GATE.EXPECTED_REPORT_ROWS,
            "fixture_revision": "sha256:" + "a" * 64,
            "population": {
                "path": GATE.V090_POPULATION.as_posix(),
                "sha256": "",
            },
            "reports": [],
        }
        self.population = {
            "population": GATE.RELEASE,
            "status": "prospective-inputs-not-release-evidence",
            "fixture_revision": self.plan["fixture_revision"],
            "cases": [
                {
                    "id": case_id,
                    "path": f"cases/{case_id}.json",
                    "sha256": "b" * 64,
                    "track": "taint",
                    "score_tier": "core",
                    "model_profile": "benchmark-controlled",
                    "fixture_digests": [],
                }
                for case_id in self.population_ids
            ],
        }
        self.plan["reports"] = [
            {
                "id": f"adapter-{index:02d}",
                "report": f"reports/releases/v0.9.0/normal/report-{index:02d}.json",
                "case_ids": case_ids,
                "case_membership": {
                    "count": len(case_ids),
                    "sha256": GATE._membership_digest(case_ids),
                },
            }
            for index, case_ids in enumerate(self.partitions)
        ]
        self._write_inputs()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _partition_memberships() -> list[list[str]]:
        ids = [f"case-{index:04d}" for index in range(GATE.EXPECTED_CASES)]
        memberships = [[] for _ in range(GATE.EXPECTED_REPORT_PARTITIONS)]
        for row in range(GATE.EXPECTED_REPORT_ROWS):
            memberships[row % len(memberships)].append(ids[row % len(ids)])
        return memberships

    def _write_inputs(self) -> None:
        population_path = self.root / GATE.V090_POPULATION
        population_path.parent.mkdir(parents=True, exist_ok=True)
        population_path.write_text(json.dumps(self.population), encoding="utf-8")
        self.plan["population"]["sha256"] = GATE._sha256(population_path.read_bytes())
        plan_path = self.root / GATE.V090_PLAN
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(self.plan), encoding="utf-8")

    def _manifest(self) -> dict:
        return {
            "schema_version": 1,
            "benchmark": {
                "release": GATE.RELEASE,
                "revision": "1" * 40,
                "dirty": False,
                "fixture_revision": self.population["fixture_revision"],
            },
            "claim": {"scope": "release"},
            "cases": [
                {
                    key: item[key]
                    for key in (
                        "id", "path", "sha256", "track", "score_tier",
                        "model_profile", "fixture_digests",
                    )
                }
                for item in self.population["cases"]
            ],
            "reports": [
                {
                    "path": planned["report"],
                    "case_ids": list(planned["case_ids"]),
                }
                for planned in self.plan["reports"]
            ],
        }

    def test_plan_only_reports_prospective_counts(self) -> None:
        result = GATE.validate_plan(self.root)
        self.assertEqual(
            (result["population_cases"], result["report_partitions"], result["report_rows"]),
            (GATE.EXPECTED_CASES, GATE.EXPECTED_REPORT_PARTITIONS, GATE.EXPECTED_REPORT_ROWS),
        )
        self.assertFalse(result["release_evidence"])

    def test_actual_freeze_is_bound_to_exact_per_report_membership(self) -> None:
        manifest = self._manifest()
        (self.root / "reports").mkdir(exist_ok=True)
        (self.root / "reports" / "freeze.json").write_text(json.dumps(manifest), encoding="utf-8")
        GATE._load_release_manifest(self.root, "1" * 40)

    def test_attempt_projection_requires_exact_membership_digest_and_mapping(self) -> None:
        import hashlib
        manifest = self._manifest()
        mappings = []
        for planned, frozen in zip(self.plan["reports"], manifest["reports"]):
            staged = "reports/releases/v0.9.0/normal/attempts/series/" + Path(planned["report"]).name
            data = json.dumps({"case_ids": planned["case_ids"]}).encode()
            target = self.root / staged
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            frozen["path"] = staged
            mappings.append({"source_path": planned["report"], "staged_path": staged,
                             "staged_sha256": hashlib.sha256(data).hexdigest(),
                             "case_ids": planned["case_ids"]})
        ledger = self.root / "reports/releases/v0.9.0/ledger-v1.jsonl"
        ledger.write_text(json.dumps({"status": "completed", "reports": mappings}) + "\n")
        (self.root / "reports/freeze.json").write_text(json.dumps(manifest))
        GATE._load_release_manifest(self.root, "1" * 40)
        for mutation in ("digest", "duplicate", "missing", "membership", "traversal"):
            changed = json.loads(json.dumps(mappings))
            if mutation == "digest": changed[0]["staged_sha256"] = "0" * 64
            elif mutation == "duplicate": changed.append(changed[0])
            elif mutation == "missing": changed.pop()
            elif mutation == "membership": changed[0]["case_ids"] = []
            else: changed[0]["staged_path"] = "reports/releases/v0.9.0/normal/attempts/../escape.json"
            ledger.write_text(json.dumps({"status": "completed", "reports": changed}) + "\n")
            with self.subTest(mutation=mutation), self.assertRaises(GATE.GateError):
                GATE._load_release_manifest(self.root, "1" * 40)

    def test_swapped_memberships_fail_even_when_total_rows_match(self) -> None:
        manifest = self._manifest()
        left = manifest["reports"][0]["case_ids"]
        right = manifest["reports"][1]["case_ids"]
        left[0], right[0] = right[0], left[0]
        (self.root / "reports").mkdir(exist_ok=True)
        (self.root / "reports" / "freeze.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(GATE.GateError, "do not match the reviewed v0.9.0 plan"):
            GATE._load_release_manifest(self.root, "1" * 40)

    def test_historical_or_missing_freeze_cannot_qualify_v090(self) -> None:
        with self.assertRaisesRegex(GATE.GateError, "actual v0.9.0 release freeze is absent"):
            GATE._load_release_manifest(self.root, "1" * 40)
        (self.root / "reports").mkdir(exist_ok=True)
        (self.root / "reports" / "freeze.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "benchmark": {
                        "release": "v0.8.0",
                        "revision": "1" * 40,
                        "dirty": False,
                        "fixture_revision": self.population["fixture_revision"],
                    },
                    "claim": {"scope": "release"},
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(GATE.GateError, "expected 'v0.9.0'"):
            GATE._load_release_manifest(self.root, "1" * 40)

    def test_delegation_restores_v080_constants(self) -> None:
        old_release = GATE._V080_GATE.RELEASE
        old_revision = GATE._V080_GATE.EXPECTED_REVISION
        with mock.patch.object(GATE, "_load_release_manifest", return_value={}):
            with mock.patch.object(GATE._V080_GATE, "run_gate") as run_gate:
                GATE.run_gate(
                    self.root,
                    binary=Path("/tmp/reviewed-binary"),
                    evidence_revision="2" * 40,
                )
        run_gate.assert_called_once()
        self.assertEqual(GATE._V080_GATE.RELEASE, old_release)
        self.assertEqual(GATE._V080_GATE.EXPECTED_REVISION, old_revision)


if __name__ == "__main__":
    unittest.main()
