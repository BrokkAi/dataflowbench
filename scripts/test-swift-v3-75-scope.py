#!/usr/bin/env python3
"""Exercise smoke/full Swift v3 report boundaries without running CodeQL."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from swift_v3_reports75 import assemble, inputs, read, sha
from swift_v3_runner75 import lane
from swift_v3_verify75 import verify


REPOSITORY = Path(__file__).resolve().parents[1]
PLAN = Path("adapters/codeql/swift-v3-75/runner-plan.json")
SELECTION = Path("adapters/codeql/swift-v3-75/selection.json")


class SmokeBoundary(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        self.root.mkdir()

        # Copy the real preregistered configuration into a temporary root so
        # verification exercises its actual hashes without touching run output.
        plan = read(REPOSITORY / PLAN)
        for relative in [PLAN, *map(Path, plan["files"])]:
            source = REPOSITORY / relative
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        self.population, self.contract, self.cases, self.population_hash, self.contract_hash = inputs(self.root)
        self.selection = read(self.root / SELECTION)["case_ids"]
        self.envelope = {
            "scope": "swift-v3-budget-retry-subset",
            "population": self.population["population"],
            "population_sha256": self.population_hash,
            "fixture_revision": self.population["fixture_revision"],
            "contract_id": self.contract["contract_id"],
            "contract_sha256": self.contract_hash,
            "phases": self.contract["phases"],
            "selected_case_ids": self.selection,
        }

    def make_run(self, result_ids=None, scope=None):
        output = self.root / "reports/raw/swift-v3/smoke-regression"
        output.mkdir(parents=True, exist_ok=True)
        result_ids = self.selection if result_ids is None else result_ids
        run = dict(self.envelope, scope=scope or self.envelope["scope"], results=[])
        rows_by_case = {}

        for case_id in result_ids:
            if case_id in rows_by_case:
                run["results"].append(rows_by_case[case_id])
                continue
            case = self.cases.get(case_id)
            case_dir = output / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            artifacts_path = case_dir / "artifacts.json"
            artifacts_path.write_text("{}\n")
            raw = {
                "scope": run["scope"],
                "population_sha256": self.population_hash,
                "fixture_revision": self.population["fixture_revision"],
                "contract_sha256": self.contract_hash,
                "case_id": case_id,
                "outcome": "inconclusive",
                "execution_status": "not-attempted",
                "commands": {},
                "lane": lane(case),
                "diagnostics": ["DiskReserveReached"],
                "artifacts_sha256": sha(artifacts_path),
            }
            raw_path = case_dir / "observation.json"
            raw_path.write_text(json.dumps(raw, indent=2) + "\n")
            relative = raw_path.relative_to(self.root)
            row = {
                "case_id": case_id,
                "outcome": raw["outcome"],
                "raw_output": str(relative),
                "raw_sha256": sha(raw_path),
            }
            rows_by_case[case_id] = row
            run["results"].append(row)

        run_path = output / "run.json"
        run_path.write_text(json.dumps(run, indent=2) + "\n")
        launch = dict(
            run,
            runner_plan_sha256=sha(self.root / PLAN),
            paths={
                "repository": str(self.root),
                "output": str(output),
                "cli": "/unused/codeql",
                "compiler": "/unused/swiftc",
                "sdk": "/unused/sdk",
                "packs": "/unused/packs",
                "native_packs": "/unused/native-packs",
            },
        )
        (output / "run-plan.json").write_text(json.dumps(launch, indent=2) + "\n")
        return output, run

    def test_inconsistent_resource_plan_rejected(self):
        output, _ = self.make_run()
        plan = read(self.root / PLAN)
        plan["resources"]["analysis_total_seconds"] = 60
        (self.root / PLAN).write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, "preregistered resource envelope"):
            verify(self.root, output, allow_smoke=True)

    def test_smoke_verification_requires_explicit_opt_in(self):
        output, _ = self.make_run()
        with self.assertRaisesRegex(ValueError, "explicit smoke replay required"):
            verify(self.root, output)

    def test_smoke_verification_accepts_exact_temporary_envelope(self):
        output, _ = self.make_run()
        report = verify(self.root, output, allow_smoke=True)
        self.assertEqual(report["scope"], "verified-eight-case-retry-not-full-report")
        self.assertEqual(report["selected_case_ids"], self.selection)
        self.assertEqual([row["case_id"] for row in report["results"]], self.selection)

    def test_full_assembly_rejects_smoke_scope(self):
        _, run = self.make_run()
        with self.assertRaisesRegex(ValueError, "new execution scope required"):
            assemble(self.root, run)

    def test_full_assembly_rejects_five_case_subset(self):
        self.make_run()
        run = dict(
            self.envelope,
            scope="swift-v3-contract-bound-execution",
            results=[{"case_id": case_id} for case_id in self.selection],
        )
        with self.assertRaisesRegex(ValueError, "exact result membership"):
            assemble(self.root, run)

    def test_smoke_verifier_rejects_missing_membership(self):
        output, _ = self.make_run(self.selection[:-1])
        with self.assertRaisesRegex(ValueError, "exact smoke membership"):
            verify(self.root, output, allow_smoke=True)

    def test_smoke_verifier_rejects_duplicate_membership(self):
        ids = list(self.selection)
        ids[-1] = ids[0]
        output, _ = self.make_run(ids)
        with self.assertRaisesRegex(ValueError, "exact smoke membership"):
            verify(self.root, output, allow_smoke=True)

    def test_smoke_verifier_rejects_foreign_membership(self):
        ids = list(self.selection)
        ids[-1] = next(case_id for case_id in self.cases if case_id not in self.selection)
        output, _ = self.make_run(ids)
        with self.assertRaisesRegex(ValueError, "exact smoke membership"):
            verify(self.root, output, allow_smoke=True)

    def test_smoke_verifier_rejects_reordered_membership(self):
        ids = list(self.selection)
        ids[0], ids[1] = ids[1], ids[0]
        output, _ = self.make_run(ids)
        with self.assertRaisesRegex(ValueError, "exact smoke membership"):
            verify(self.root, output, allow_smoke=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
