from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import types
import unittest


HERE = pathlib.Path(__file__).resolve().parent
CODE_DIR = HERE.parent
REPO = next(parent for parent in CODE_DIR.parents if (parent / "schemas/result.schema.json").is_file())
SOURCE_REPORTS = REPO / "execution-state/v092/publication-evidence/joern108-metadata-projection-01"
RAW_ROOT = REPO
SCHEMA = json.loads((REPO / "schemas/result.schema.json").read_bytes())
SOURCE_BYTES = (CODE_DIR / "project_joern.py").read_bytes()
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).hexdigest()

# Execute the exact reviewed helper bytes. This intentionally bypasses importlib
# bytecode caches so a stale .pyc cannot stand in for the hashed source.
MODULE = types.ModuleType("project_joern_tested_exact_bytes")
MODULE.__file__ = str(CODE_DIR / "project_joern.py")
exec(compile(SOURCE_BYTES, MODULE.__file__, "exec"), MODULE.__dict__)

REPORT_NAMES = (
    "joern-swift-calibration.json",
    "joern-swift-core.json",
    "joern-swift-language-extension.json",
    "joern-swift-modeling.json",
    "joern-swift-native.json",
)


def load_report(name: str) -> dict:
    return json.loads((SOURCE_REPORTS / name).read_bytes())


class ProjectorTests(unittest.TestCase):
    def test_actual_five_reports_project_and_reconstruct_losslessly(self) -> None:
        total = 0
        all_ids: set[str] = set()
        outcome_counts: dict[str, int] = {}
        for name in REPORT_NAMES:
            source_bytes = (SOURCE_REPORTS / name).read_bytes()
            source = json.loads(source_bytes)
            canonical, sidecar = MODULE.project_report(source, RAW_ROOT, SCHEMA)
            self.assertEqual(MODULE.reconstruct_report(canonical, sidecar), source)
            self.assertNotIn("aggregate_resource_qualification", canonical)
            self.assertNotIn("scored_activation", canonical)
            self.assertTrue(all("raw_sha256" not in row for row in canonical["results"]))
            self.assertEqual(sidecar["qualification"]["aggregate_resource_qualification"], "unavailable")
            self.assertIs(sidecar["qualification"]["scored_activation"], False)
            self.assertIs(sidecar["qualification"]["timing_certified"], False)
            self.assertEqual(sidecar["source_report_object_sha256"], MODULE._object_sha256(source))
            self.assertEqual(sidecar["canonical_report_object_sha256"], MODULE._object_sha256(canonical))
            # Independent field-delta assertion: all non-lift fields are identical.
            expected = copy.deepcopy(source)
            expected.pop("aggregate_resource_qualification")
            expected.pop("scored_activation")
            for row in expected["results"]:
                row.pop("raw_sha256")
            self.assertEqual(canonical, expected)
            for row in source["results"]:
                self.assertNotIn(row["case_id"], all_ids)
                all_ids.add(row["case_id"])
                outcome_counts[row["outcome"]] = outcome_counts.get(row["outcome"], 0) + 1
                total += 1
            self.assertEqual(
                hashlib.sha256(source_bytes).hexdigest(),
                hashlib.sha256((SOURCE_REPORTS / name).read_bytes()).hexdigest(),
            )
        self.assertEqual(total, 108)
        self.assertEqual(len(all_ids), 108)
        self.assertEqual(outcome_counts, {"inconclusive": 96, "unsupported": 12})

    def _minimal_copied_report(self, temp_root: pathlib.Path) -> dict:
        source = load_report(REPORT_NAMES[0])
        source["results"] = [copy.deepcopy(source["results"][0])]
        raw_rel = pathlib.PurePosixPath(source["results"][0]["raw_output"])
        target = temp_root.joinpath(*raw_rel.parts)
        target.parent.mkdir(parents=True)
        original = REPO.joinpath(*raw_rel.parts).read_bytes()
        target.write_bytes(original)
        return source

    def test_rejects_unknown_fields_and_unsupported_version_before_output(self) -> None:
        report = load_report(REPORT_NAMES[0])
        report["unrecognized"] = True
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)
        report = load_report(REPORT_NAMES[0])
        report["results"][0]["unrecognized"] = True
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)
        report = load_report(REPORT_NAMES[0])
        report["tool_version"] = "4.0.661"
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)
        changed_schema = copy.deepcopy(SCHEMA)
        changed_schema["title"] = "modified"
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(load_report(REPORT_NAMES[0]), RAW_ROOT, changed_schema)

    def test_rejects_missing_metadata_bad_hash_and_duplicate_case_ids(self) -> None:
        report = load_report(REPORT_NAMES[0])
        del report["scored_activation"]
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)
        report = load_report(REPORT_NAMES[0])
        report["results"][0]["raw_sha256"] = "not-a-hash"
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)
        report = load_report(REPORT_NAMES[0])
        report["results"].append(copy.deepcopy(report["results"][0]))
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.project_report(report, RAW_ROOT, SCHEMA)

    def test_rejects_missing_mismatched_and_symlinked_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            report = self._minimal_copied_report(root)
            raw_rel = pathlib.PurePosixPath(report["results"][0]["raw_output"])
            raw_path = root.joinpath(*raw_rel.parts)
            raw_path.unlink()
            with self.assertRaises(MODULE.ProjectionError):
                MODULE.project_report(report, root, SCHEMA)

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            report = self._minimal_copied_report(root)
            raw_rel = pathlib.PurePosixPath(report["results"][0]["raw_output"])
            raw_path = root.joinpath(*raw_rel.parts)
            raw_path.write_bytes(raw_path.read_bytes() + b"changed")
            with self.assertRaises(MODULE.ProjectionError):
                MODULE.project_report(report, root, SCHEMA)

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            report = self._minimal_copied_report(root)
            raw_rel = pathlib.PurePosixPath(report["results"][0]["raw_output"])
            raw_path = root.joinpath(*raw_rel.parts)
            original = REPO.joinpath(*raw_rel.parts)
            raw_path.unlink()
            raw_path.symlink_to(original)
            with self.assertRaises(MODULE.ProjectionError):
                MODULE.project_report(report, root, SCHEMA)

    def test_reconstruction_rejects_sidecar_tampering(self) -> None:
        source = load_report(REPORT_NAMES[0])
        canonical, sidecar = MODULE.project_report(source, RAW_ROOT, SCHEMA)
        altered = copy.deepcopy(sidecar)
        altered["qualification"]["scored_activation"] = True
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.reconstruct_report(canonical, altered)
        altered = copy.deepcopy(sidecar)
        altered["schema_object_sha256"] = "0" * 64
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.reconstruct_report(canonical, altered)
        altered = copy.deepcopy(sidecar)
        altered["removed_result_metadata"][0]["raw_output"] = "wrong/path"
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.reconstruct_report(canonical, altered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
