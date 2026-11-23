"""Exercise the top-level declared-decline/report boundary without analyzers."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import joern_normal_reports_v092_capability as reports
import joern_normal_runner_v092_capability as runner

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return {"path": path.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class DeclineProjectionTests(unittest.TestCase):
    def fixture(self, root):
        population, common, swift, cases, digest = reports.common.load_common_population(ROOT)
        old = json.loads((ROOT / "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json").read_text())
        plan = {"schema": "joern-common-execution-plan/v092", "identity": old["identity"],
                "fresh_qualification": {"sha256": "1" * 64}, "cases": old["cases"],
                "unsupported_decisions": {case_id: {"path": "declines/" + case_id + ".json",
                                                   "sha256": "2" * 64}
                                          for case_id, row in old["cases"].items()
                                          if row["disposition"] == "unsupported"}}
        relative = "plan.json"
        write(root / relative, plan)
        run = {"schema": "joern-common-run/v092", "plan_sha256": reports.sha(root / relative),
               "population_sha256": digest, "fixture_revision": population["fixture_revision"],
               "identity": plan["identity"], "qualification_sha256": "1" * 64,
               "scored_activation": False, "aggregate_resource_qualification": "unavailable",
               "started_at_unix_seconds": 1, "ended_at_unix_seconds": 2, "results": []}
        for case_id, row in plan["cases"].items():
            declined = row["disposition"] == "unsupported"
            outcome = "unsupported" if declined else "not-reached"
            raw = {"case_id": case_id, "plan_sha256": run["plan_sha256"],
                   "population_sha256": digest, "fixture_revision": population["fixture_revision"],
                   "configuration": row["configuration"], "identity": plan["identity"],
                   "raw_outcome": outcome, "state": reports.normalized(outcome), "executed": not declined,
                   "duration_ms": 0 if declined else 1, "total_elapsed_seconds": 0 if declined else .001,
                   "commands": [], "native_outputs": [], "diagnostics": [], "witness_checkpoints": []}
            if declined:
                raw["decision_sha256"] = plan["unsupported_decisions"][case_id]["sha256"]
            path = root / "raw" / (case_id + ".json")
            ref = write(path, raw)
            ref["path"] = path.relative_to(root).as_posix()
            run["results"].append({"case_id": case_id, "configuration": row["configuration"], "raw": ref})
        dest = root / "reports/releases/v0.9.0/plan.json"
        dest.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "reports/releases/v0.9.0/plan.json", dest)
        return relative, run, (population, common, swift, cases, digest)

    def test_top_level_declines_export_all_five_partitions_and_normal_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            plan, run, population = self.fixture(root)
            with patch.object(runner, "verify_raw_capability_rows") as replay, \
                 patch.object(reports.common, "load_common_population", return_value=population):
                written = reports.export(root, plan, run, root / "normal")
            replay.assert_called_once()
            self.assertEqual(len(written), 5)
            audit = json.loads((root / "normal/audit.json").read_text())
            self.assertEqual(len(audit["results"]), 108)
            self.assertEqual(sum(row["outcome"] == "unsupported" for row in audit["results"]), 12)
            self.assertFalse((root / "audit.json").exists())

    def test_decline_cannot_hide_nonzero_duration_before_any_report_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            plan, run, population = self.fixture(root)
            row = next(row for row in run["results"] if "native-" in row["case_id"])
            path = root / row["raw"]["path"]
            raw = json.loads(path.read_text())
            raw["duration_ms"] = 7
            write(path, raw)
            row["raw"]["sha256"] = reports.sha(path)
            with patch.object(runner, "verify_raw_capability_rows"), \
                 patch.object(reports.common, "load_common_population", return_value=population):
                with self.assertRaisesRegex(ValueError, "invocation cost"):
                    reports.export(root, plan, run, root / "normal")
            self.assertFalse((root / "normal").exists())

    def test_derived_projection_changes_only_configuration_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            plan, run, population = self.fixture(root)
            with patch.object(runner, "verify_raw_capability_rows"), \
                 patch.object(reports.common, "load_common_population", return_value=population), \
                 patch.object(reports, "configuration_hash", return_value="3" * 64):
                original = reports.export(root, plan, run, root / "normal")
                derived = reports.export_projection(root, plan, run, root / "derived")
            for old, new in zip(original, derived):
                before = json.loads((root / old["path"]).read_text())
                after = json.loads((root / new["path"]).read_text())
                self.assertEqual(after.pop("configuration_hash"), "3" * 64)
                self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
