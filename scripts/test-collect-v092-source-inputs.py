#!/usr/bin/env python3
"""Relocation and fail-closed tests for v0.9.2 source-input collection."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "collect_v092_source_inputs", Path(__file__).with_name("collect-v092-source-inputs.py")
)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceInputClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.cpg_size = None
        self.codeql_plan = self._make_plan("codeql")
        self.joern_plan = self._make_plan("joern")

    def _write(self, relative: str, data: bytes) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"path": relative, "sha256": sha(path)}

    def _write_json(self, relative: str, value: dict) -> dict:
        return self._write(relative, (json.dumps(value, sort_keys=True) + "\n").encode())

    def _make_plan(self, engine: str) -> str:
        group_id = engine + "-swift-common108"
        root = self.root
        attempt_root = f"reports/releases/v0.9.2/qualification/{engine}-control-attempt-01"
        cpg_relative = attempt_root + "/native/cpg.bin"
        if self.cpg_size is None:
            cpg_ref = self._write(cpg_relative, b"small native cpg")
        else:
            cpg_path = self.root / cpg_relative
            cpg_path.parent.mkdir(parents=True, exist_ok=True)
            with cpg_path.open("wb") as stream:
                stream.truncate(self.cpg_size)
            cpg_ref = {"path": cpg_relative, "sha256": sha(cpg_path)}
        capture_ref = self._write_json(
            attempt_root + "/captured-table.json",
            {"rows": [{"kind": "native decoded result"}]},
        )
        self._write(
            attempt_root + "/workspace/cpg.bin",
            b"must not be recursively copied",
        )
        self._write(
            attempt_root + "/cache/large-cache.bin",
            b"must be omitted",
        )
        raw_ref = self._write_json(
            attempt_root + "/raw.json",
            {
                "capture_root": str(root),
                "native_outputs": [cpg_ref],
                "captured_table": {
                    "capture_path": str((root / capture_ref["path"]).resolve()),
                    "sha256": capture_ref["sha256"],
                },
                "scratch": [
                    {"path": attempt_root + "/workspace/cpg.bin",
                     "sha256": sha(root / attempt_root / "workspace/cpg.bin")},
                    {"path": attempt_root + "/cache/large-cache.bin",
                     "sha256": sha(root / attempt_root / "cache/large-cache.bin")},
                ],
            },
        )
        run_ref = self._write_json(
            attempt_root + "/run.json",
            {},
        )
        identity = {"tool": engine, "adapter_version": engine + "-normal-v092", "tool_version": "test"}
        components = []
        contract_ref = self._write_json(
            "reports/releases/v0.9.2/acquisition/execution-contract.json", {"fixed": True}
        )
        acquisition_ref = self._write_json(
            f"reports/releases/v0.9.2/acquisition/{engine}-runtime-binding.json",
            {"nested": raw_ref, "external_pack": {"path": "tool-relative/file", "sha256": "a" * 64}},
        )
        reviewer_ref = {"path": "scripts/joern_diagnostic_admission_v092.py", "sha256": "f" * 64}
        config_rows = [acquisition_ref, contract_ref]
        if engine == "joern":
            config_rows.append(reviewer_ref)
        plan = {
            "schema": ("swift-common-execution-plan/v092" if engine == "codeql"
                       else "joern-common-execution-plan/v092"),
            "profile": "v0.9.2",
            "engine": engine,
            "release_group_id": group_id,
            "population_sha256": "1" * 64,
            "fixture_revision": "sha256:" + "2" * 64,
            "identity": identity,
            "identity_components": components,
            "runtime": {},
            "codeql_packs": {},
            "query_root": "adapters/placeholder",
            "configurations": {
                "selected": [acquisition_ref, contract_ref],
            },
            "cases": {},
            "execution_contract": contract_ref,
            "qualification_control_plan": None,
            "qualification_control_projection_sha256": None,
            "status": "execution-eligible",
            "execution_eligible": True,
        }
        if engine == "joern":
            plan.update({"diagnostic_execution_eligible": True, "full_model_qualification": False,
                         "scored_activation": False})
            plan["configurations"] = {"selected": config_rows}
        projection = collector._plan_projection(root, plan)
        control = {
            "schema": "analyzer-qualification-control-plan/v092",
            "group_id": group_id,
            "execution_plan_projection_sha256": projection,
            "identity": identity,
            "identity_components": components,
            "population_sha256": plan["population_sha256"],
            "fixture_revision": plan["fixture_revision"],
            "attempt": "registered",
        }
        if engine == "joern":
            control["diagnostic_admission"] = {
                "schema": "joern-diagnostic-admission/v1",
                "decision_date": "2026-10-20",
                "state": "prospective",
                "reviewer": reviewer_ref,
            }
        control_ref = self._write_json(
            f"reports/releases/v0.9.2/qualification/{engine}-control-plan.json", control
        )
        plan["qualification_control_plan"] = control_ref
        plan["qualification_control_projection_sha256"] = projection
        receipt = {
            "schema": "analyzer-qualification-receipt/v092",
            "status": "measurement-with-known-limits",
            "execution_eligible": True,
            "group_id": group_id,
            "groups": [group_id],
            "execution_plan_projection_sha256": projection,
            "identity": identity,
            "identity_components": components,
            "control_run": run_ref,
            "dimensions": {"raw": raw_ref},
        }
        if engine == "joern":
            proof_rows = [
                {"case_id": case_id, "arm": arm}
                for case_id in (
                    "dfb-taint-swift-model-opaque-propagator-negative",
                    "dfb-taint-swift-model-opaque-propagator-positive",
                    "dfb-taint-swift-model-propagator-position-negative",
                    "dfb-taint-swift-model-propagator-position-positive",
                )
                for arm in ("off", "on")
            ]
            review_ref = self._write_json(
                "reports/releases/v0.9.2/qualification/joern-review.json",
                {"schema": "joern-diagnostic-admission-review/v1",
                 "status": "measurement-with-known-limits",
                 "diagnostic_execution_eligible": True,
                 "full_model_qualification": False,
                 "scored_activation": False,
                 "control_run": run_ref,
                 "endpoint_identity_proofs": proof_rows,
                 "strict_assessment": {"status": "incomplete", "failures": [{}] * 8}},
            )
            receipt.update({"diagnostic_execution_eligible": True,
                            "full_model_qualification": False,
                            "scored_activation": False,
                            "diagnostic_admission_review": review_ref})
            receipt["dimensions"] = {"raw": raw_ref, "joern_diagnostic_admission": review_ref}
        receipt_ref = self._write_json(
            f"reports/releases/v0.9.2/qualification/{engine}-qualification.json", receipt
        )
        plan["fresh_qualification"] = receipt_ref
        # Rewrite the run with its actual registered control-plan binding.
        run = {
            "schema": "analyzer-qualification-control-run/v092",
            "group_id": group_id,
            "control_plan_sha256": control_ref["sha256"],
            "execution_plan_projection_sha256": projection,
            "identity": identity,
            "identity_components": components,
            "dimensions": {"raw": raw_ref},
        }
        run_ref = self._write_json(attempt_root + "/run.json", run)
        receipt["control_run"] = run_ref
        receipt_ref = self._write_json(
            f"reports/releases/v0.9.2/qualification/{engine}-qualification.json", receipt
        )
        plan["fresh_qualification"] = receipt_ref
        if engine == "joern":
            review_path = self.root / "reports/releases/v0.9.2/qualification/joern-review.json"
            review = json.loads(review_path.read_text())
            review["control_run"] = run_ref
            review_ref = self._write_json(
                "reports/releases/v0.9.2/qualification/joern-review.json", review
            )
            receipt["diagnostic_admission_review"] = review_ref
            receipt["dimensions"]["joern_diagnostic_admission"] = review_ref
            receipt_ref = self._write_json(
                f"reports/releases/v0.9.2/qualification/{engine}-qualification.json", receipt
            )
            plan["fresh_qualification"] = receipt_ref
        plan_rel = collector.CODEQL_PLAN if engine == "codeql" else collector.JOERN_PLAN
        plan_path = root / plan_rel
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(plan, sort_keys=True) + "\n")
        return plan_rel

    def _codeql_captured_sources(self):
        scripts = ROOT / "scripts"
        if str(scripts) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(scripts))
        import codeql_swift_qualification_v092 as codeql

        base = "reports/releases/v0.9.2/qualification/codeql-swift-common108/control-attempt-01"
        entry_ids = list(codeql.ENTRY_IDS)
        entry_controls = {
            case_id: f"adapters/codeql/swift-entry-extractor-v1/controls/{case_id}/main.swift"
            for case_id in entry_ids
        }
        entry_manifest = {"files": {}}
        for case_id, source_path in entry_controls.items():
            content = ("entry " + case_id + "\n").encode()
            self._write(source_path, content)
            entry_manifest["files"][case_id + "/main.swift"] = hashlib.sha256(content).hexdigest()
        self._write_json("adapters/codeql/swift-entry-extractor-v1/control-manifest.json", entry_manifest)

        control = {
            "population_sha256": "1" * 64,
            "entry_extractor": {"control_ids": entry_ids, "controls": entry_controls},
        }
        common_rows = []
        population_cases = {}
        activation_sources = {}
        for dimension, expected_cases in (
            ("model_activation", codeql.MODEL_EXPECTED),
            ("sanitizer_activation", codeql.SANITIZER_EXPECTED),
        ):
            for case_id in expected_cases:
                extra_name = "fixture-" + case_id.rsplit("-", 1)[-1] + ".swift"
                fixture_names = [extra_name, "main.swift"]
                fixture_digests = []
                hashes = {}
                for filename in fixture_names:
                    source_path = f"cases/{case_id}/{filename}"
                    content = (case_id + " " + filename + "\n").encode()
                    digest = hashlib.sha256(content).hexdigest()
                    self._write(source_path, content)
                    fixture_digests.append({"path": source_path, "sha256": digest})
                    hashes[filename] = digest
                common_rows.append({"id": case_id, "fixture_digests": fixture_digests})
                population_cases[case_id] = {"fixture_files": fixture_names}
                activation_sources[(dimension, case_id)] = hashes

        evidence_refs = {}
        for dimension in ("entry_extractor", "model_activation", "sanitizer_activation"):
            rows = []
            if dimension == "entry_extractor":
                combinations = [(case_id, None) for case_id in entry_ids]
            else:
                expected_cases = codeql.MODEL_EXPECTED if dimension == "model_activation" else codeql.SANITIZER_EXPECTED
                combinations = [(case_id, arm) for case_id in expected_cases for arm in ("off", "on")]
            for case_id, arm in combinations:
                suffix = f"{dimension}/{case_id}" + (f"/{arm}" if arm else "")
                raw_rel = f"{base}/{suffix}/raw.json"
                raw_parent = self.root / raw_rel
                raw_parent.parent.mkdir(parents=True, exist_ok=True)
                output_directory = raw_parent.parent
                if dimension == "entry_extractor":
                    filenames = ["main.swift"]
                    hashes = {"main.swift": entry_manifest["files"][case_id + "/main.swift"]}
                    raw = {
                        "schema": "codeql-entry-control-raw/v092", "group_id": "codeql-swift-common108",
                        "control_id": case_id, "capture_root": str(self.root),
                        "capture_output_dir": str(output_directory), "capture_state": "complete",
                        "fixture_sha256": hashes["main.swift"],
                        "source_files": {"main.swift": {"path": entry_controls[case_id], "sha256": hashes["main.swift"]}},
                    }
                    rows.append({"control_id": case_id, "raw": {"path": raw_rel}})
                else:
                    hashes = activation_sources[(dimension, case_id)]
                    filenames = list(hashes)
                    raw = {
                        "schema": "codeql-activation-control-raw/v092", "group_id": "codeql-swift-common108",
                        "dimension": dimension, "case_id": case_id, "arm": arm,
                        "capture_root": str(self.root), "capture_output_dir": str(output_directory),
                        "capture_state": "complete", "fixture_hashes": hashes,
                    }
                    rows.append({"case_id": case_id, "arm": arm, "raw": {"path": raw_rel}})
                source_dir = output_directory / "source"
                source_dir.mkdir(exist_ok=True)
                for filename in filenames:
                    if dimension == "entry_extractor":
                        tracked = self.root / entry_controls[case_id]
                    else:
                        match = next(item["path"] for item in common_rows if item["id"] == case_id
                                     for item in item["fixture_digests"] if Path(item["path"]).name == filename)
                        tracked = self.root / match
                    shutil.copyfile(tracked, source_dir / filename)
                raw_ref = self._write_json(raw_rel, raw)
                rows[-1]["raw"] = raw_ref
            evidence_schema = "codeql-entry-extractor-evidence/v092" if dimension == "entry_extractor" else "codeql-activation-evidence/v092"
            evidence_ref = self._write_json(base + "/" + dimension + "-evidence.json",
                                            {"schema": evidence_schema, "controls": rows})
            evidence_refs[dimension] = {"evidence": evidence_ref}
        receipt = {"dimensions": evidence_refs}
        return control, receipt, common_rows, population_cases

    def test_codeql_capture_sources_are_exact_and_digest_bound(self):
        control, receipt, common_rows, population_cases = self._codeql_captured_sources()
        with mock.patch("swift_common_population_v2.load_common_population",
                        return_value=({}, common_rows, [], population_cases, "1" * 64)):
            rows = collector._codeql_captured_source_inputs(self.root, control, receipt)
        self.assertEqual(len(rows), 34)
        self.assertEqual(len({path for path, _digest in rows}), 34)
        for relative, digest in rows:
            self.assertTrue(relative.as_posix().startswith("reports/releases/v0.9.2/qualification/"))
            self.assertEqual(sha(self.root / relative.as_posix()), digest)

    def test_codeql_capture_sources_reject_missing_copy_and_extra_arm(self):
        control, receipt, common_rows, population_cases = self._codeql_captured_sources()
        with mock.patch("swift_common_population_v2.load_common_population",
                        return_value=({}, common_rows, [], population_cases, "1" * 64)):
            first = next((path, digest) for path, digest in
                         collector._codeql_captured_source_inputs(self.root, control, receipt))
            (self.root / first[0].as_posix()).unlink()
            with self.assertRaisesRegex(collector.ClosureError, "captured source is missing"):
                collector._codeql_captured_source_inputs(self.root, control, receipt)

        control, receipt, common_rows, population_cases = self._codeql_captured_sources()
        dimensions = receipt["dimensions"]
        evidence_ref = dimensions["model_activation"]["evidence"]
        evidence_path = self.root / evidence_ref["path"]
        evidence = json.loads(evidence_path.read_text())
        evidence["controls"].append({"case_id": "not-a-registered-case", "arm": "off", "raw": {"path": "unused"}})
        evidence_path.write_text(json.dumps(evidence) + "\n")
        dimensions["model_activation"]["evidence"]["sha256"] = sha(evidence_path)
        with mock.patch("swift_common_population_v2.load_common_population",
                        return_value=({}, common_rows, [], population_cases, "1" * 64)):
            with self.assertRaisesRegex(collector.ClosureError, "unknown fixture"):
                collector._codeql_captured_source_inputs(self.root, control, receipt)

    def test_recursive_closure_relocates_exact_bound_files(self):
        result = collector.collect_source_inputs(
            self.root, [self.codeql_plan, self.joern_plan], replay=False
        )
        inputs = {row["path"]: row for row in result["source_inputs"]}
        self.assertIn("reports/releases/v0.9.2/acquisition/codeql-runtime-binding.json", inputs)
        codeql_attempt = "reports/releases/v0.9.2/qualification/codeql-control-attempt-01"
        self.assertIn(codeql_attempt + "/raw.json", inputs)
        self.assertIn(codeql_attempt + "/native/cpg.bin", inputs)
        self.assertIn(codeql_attempt + "/captured-table.json", inputs)
        self.assertNotIn(codeql_attempt + "/workspace/cpg.bin", inputs)
        self.assertNotIn(codeql_attempt + "/cache/large-cache.bin", inputs)
        self.assertEqual(result["counts"]["cpg_files"], 2)

        relocated = Path(self.temp.name) / "relocated"
        for row in result["source_inputs"]:
            source = self.root / row["path"]
            destination = relocated / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            self.assertEqual(sha(destination), row["sha256"], row["path"])
        self.assertEqual(
            (relocated / codeql_attempt / "native/cpg.bin").read_bytes(),
            b"small native cpg",
        )
        for plan_path in (self.codeql_plan, self.joern_plan):
            source = self.root / plan_path
            destination = relocated / plan_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        relocated_result = collector.collect_source_inputs(
            relocated, [self.codeql_plan, self.joern_plan], replay=False
        )
        self.assertEqual(
            [(row["path"], row["sha256"]) for row in result["source_inputs"]],
            [(row["path"], row["sha256"]) for row in relocated_result["source_inputs"]],
        )

    def test_joern_plan_envelope_uses_joern_schema(self):
        plan_path = self.root / self.joern_plan
        plan = json.loads(plan_path.read_text())
        self.assertEqual(plan["schema"], "joern-common-execution-plan/v092")
        checked, _control, _receipt, _run_path, _run_rel = collector._validate_plan_envelope(
            self.root, self.joern_plan
        )
        self.assertEqual(checked["engine"], "joern")

    def test_joern_plan_rejects_codeql_plan_schema(self):
        plan_path = self.root / self.joern_plan
        plan = json.loads(plan_path.read_text())
        plan["schema"] = "swift-common-execution-plan/v092"
        plan_path.write_text(json.dumps(plan) + "\n")
        with self.assertRaisesRegex(collector.ClosureError, "joern Swift plan"):
            collector._validate_plan_envelope(self.root, self.joern_plan)

    def test_nested_digest_drift_fails_closed(self):
        raw = self.root / "reports/releases/v0.9.2/qualification/codeql-control-attempt-01/raw.json"
        document = json.loads(raw.read_text())
        document["native_outputs"][0]["sha256"] = "0" * 64
        raw.write_text(json.dumps(document) + "\n")
        with self.assertRaisesRegex(collector.ClosureError, "digest mismatch"):
            collector.collect_source_inputs(self.root, [self.codeql_plan, self.joern_plan], replay=False)

    def test_oversized_explicit_cpg_fails_closed(self):
        oversize_temp = tempfile.TemporaryDirectory()
        self.addCleanup(oversize_temp.cleanup)
        self.root = Path(oversize_temp.name).resolve()
        self.cpg_size = collector.MAX_CPG_BYTES + 1
        self.codeql_plan = self._make_plan("codeql")
        self.joern_plan = self._make_plan("joern")
        with self.assertRaisesRegex(collector.ClosureError, "CPG exceeds"):
            collector.collect_source_inputs(self.root, [self.codeql_plan, self.joern_plan], replay=False)


if __name__ == "__main__":
    unittest.main()
