from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import ModuleType


ROOT = Path(__file__).resolve().parents[6]
SCRIPT = Path(__file__).resolve().parents[1] / "run_canonical.py"


def load_gate() -> ModuleType:
    before = SCRIPT.read_bytes()
    module = ModuleType("canonical_schema_gate_tests")
    module.__file__ = str(SCRIPT)
    module.__package__ = ""
    exec(compile(before, str(SCRIPT), "exec"), module.__dict__)
    if SCRIPT.read_bytes() != before:
        raise AssertionError("gate helper bytes changed while test module loaded")
    return module


gate = load_gate()


class CanonicalSchemaGateTests(unittest.TestCase):
    def test_producer_shaped_joern_reports_project_and_reconstruct_exactly(self) -> None:
        failed = gate._verify_old_failure(ROOT)["receipt_json"]
        schema = json.loads((ROOT / "schemas/result.schema.json").read_bytes())
        projector = gate._load_exact_module(
            ROOT / Path(*gate.PROJECTOR_REL.parts),
            "canonical_schema_gate_test_projector",
            gate.PROJECTOR_SHA256,
        )
        checkout = ROOT / Path(*gate.OLD_CHECKOUT_REL.parts)
        projected, sidecar = gate._prepare_projection(ROOT, checkout, failed, schema, projector)
        self.assertEqual([item["path"] for item in projected],
                         [f"reports/{name}" for name in gate.JOERN_REPORTS])
        self.assertEqual(sum(item["rows"] for item in projected), 108)
        self.assertEqual(len(sidecar["reports"]), 5)
        for item in projected:
            self.assertNotIn("canonical", item["sidecar"])
            self.assertEqual(item["removed_top_level_fields"],
                             ["aggregate_resource_qualification", "scored_activation"])
            self.assertEqual(item["removed_result_row_field"], "raw_sha256")
            original_bytes = (ROOT / item["source_path"]).read_bytes()
            original_report = json.loads(original_bytes)
            self.assertEqual(hashlib.sha256(original_bytes).hexdigest(), item["source_sha256"])
            self.assertEqual(projector._object_sha256(original_report),
                             item["sidecar"]["source_report_object_sha256"])
            self.assertEqual(projector.reconstruct_report(item["canonical"], item["sidecar"]),
                             original_report)

    def test_unknown_metadata_is_a_near_miss_and_fails_closed(self) -> None:
        schema = json.loads((ROOT / "schemas/result.schema.json").read_bytes())
        report_path = ROOT / Path(*gate.OLD_CHECKOUT_REL.parts) / "reports/joern-swift-core.json"
        report = json.loads(report_path.read_bytes())
        top_extra = copy.deepcopy(report)
        top_extra["future_unreviewed_state"] = {"enabled": True}
        with self.assertRaises(gate.GateError):
            gate._schema_shape(top_extra, schema, allow_joern_metadata=True)
        row_extra = copy.deepcopy(report)
        row_extra["results"][0]["raw_digest_vendor"] = "unreviewed"
        with self.assertRaises(gate.GateError):
            gate._schema_shape(row_extra, schema, allow_joern_metadata=True)

    def test_copy_inventory_accepts_only_the_exact_five_report_changes(self) -> None:
        allowed = {f"reports/{name}" for name in gate.JOERN_REPORTS}
        stable = {"path": "src/main.rs", "kind": "file", "mode": 0o644,
                  "bytes": 3, "sha256": "c" * 64}
        before_entries = [copy.deepcopy(stable)]
        after_entries = [copy.deepcopy(stable)]
        for path in sorted(allowed):
            before_entries.append({"path": path, "kind": "file", "mode": 0o644,
                                   "bytes": 1, "sha256": "a" * 64})
            after_entries.append({"path": path, "kind": "file", "mode": 0o644,
                                  "bytes": 1, "sha256": "b" * 64})
        before = {"entries": before_entries}
        after = {"entries": after_entries}
        diff = gate._compare_inventories(before, after, allowed_changed_files=allowed)
        self.assertEqual(set(diff["changed"]), allowed)
        after_entries[0]["sha256"] = "d" * 64
        with self.assertRaises(gate.GateError):
            gate._compare_inventories(before, after, allowed_changed_files=allowed)

    def test_checkout_inventory_refuses_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "checkout"
            base.mkdir()
            (base / "safe.txt").write_bytes(b"safe")
            outside = Path(temporary) / "outside.txt"
            outside.write_bytes(b"outside")
            (base / "escape.txt").symlink_to(outside)
            with self.assertRaises(gate.GateError):
                gate._file_inventory(base)

    def test_full_c6_runner_binding_rejects_trimmed_metadata(self) -> None:
        contract = json.loads((ROOT / Path(*gate.C6_CONTRACT_REL.parts)).read_bytes())
        manifest = json.loads((ROOT / Path(*gate.REF_MANIFEST_REL.parts)).read_bytes())
        failed = gate._verify_old_failure(ROOT)["receipt_json"]
        runner = gate._verify_runner_binding(ROOT, contract, manifest, failed)
        self.assertEqual(set(runner), {"path", "sha256", "build_receipt"})
        trimmed = copy.deepcopy(contract)
        trimmed["runtime"]["runner"].pop("build_receipt")
        with self.assertRaises(gate.GateError):
            gate._verify_runner_binding(ROOT, trimmed, manifest, failed)

    def test_invoke_requires_explicit_root_confirmed_preparation_hash(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = gate.main(["--invoke"])
        self.assertEqual(result, 1)
        self.assertIn("--prepared-diagnosis-sha256", stderr.getvalue())

    def test_invoke_review_is_required_before_runner_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(gate.GateError):
                gate._verify_invocation_review(Path(temporary))


if __name__ == "__main__":
    unittest.main()
