#!/usr/bin/env python3
"""Focused integrity tests for the v0.9.2 publication evidence mapper."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import v092_publication_evidence as publication


ROOT = Path(__file__).resolve().parents[1]


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fixed_roster_manifest() -> dict[str, object]:
    selection_raw = publication._read_file(
        ROOT, publication.SELECTION_PATH,
        expected_sha256=publication.SELECTION_SHA256)
    selection = publication._json(selection_raw, "selection")
    selector_ref, selector_raw = publication._source_ref(
        ROOT, selection["source_selector"], "selector")
    selector = publication._json(selector_raw, "selector")
    receipt_ref, _ = publication._source_ref(
        ROOT, selection["canonical_validation"], "receipt")
    joern_ref, _ = publication._source_ref(ROOT, selection["joern_sidecar"], "sidecar")
    schema_raw = publication._read_file(ROOT, publication.SCHEMA_PATH,
                                        expected_sha256=publication.SCHEMA_SHA256)
    ledger_ref = selector["ledger"]
    sources = {
        "selection": {"path": publication.SELECTION_PATH,
                      "sha256": publication.SELECTION_SHA256,
                      "bytes": len(selection_raw)},
        "source_selector": selector_ref,
        "canonical_validation": receipt_ref,
        "joern_metadata_sidecar": joern_ref,
        "schema": {"path": publication.SCHEMA_PATH,
                   "sha256": publication.SCHEMA_SHA256,
                   "bytes": len(schema_raw)},
        "ledger": {
            "path": ledger_ref["path"], "sha256": ledger_ref["sha256"],
            "bytes": ledger_ref["bytes"], "line_count": ledger_ref["line_count"],
            "prefix_130_sha256": ledger_ref["prefix_130"],
            "prefix_131_sha256": ledger_ref["prefix_131"],
        },
    }
    fresh = {item["adapter"]: item for item in selector["fresh_reports"]}
    reports = []
    for selected in selection["selected_reports"]:
        item = fresh[selected["adapter"]]
        reports.append({
            "adapter": selected["adapter"],
            "adapter_id": Path(selected["adapter"]).stem,
            "attempt_id": selected["attempt_id"],
            "attempt_number": selected["attempt_number"],
            "row_count": item["rows"],
            "selected_original": selected["selected_original"],
            "canonical_report": selected["canonical_report"],
            "lifted_metadata": selected["metadata_lift"],
        })
    return {"sources": sources, "reports": reports}


class PublicationEvidenceTests(unittest.TestCase):
    def test_fixed_source_roster_accepts_exact_selection_and_rejects_tamper(self) -> None:
        manifest = _fixed_roster_manifest()
        ledger = manifest["sources"]["ledger"]
        computed_ledger = {
            "path": ledger["path"], "sha256": ledger["sha256"],
            "bytes": ledger["bytes"], "line_count": ledger["line_count"],
            "prefix_130_sha256": ledger["prefix_130_sha256"],
            "prefix_131_sha256": ledger["prefix_131_sha256"],
        }
        with mock.patch.object(publication, "_hash_ledger", return_value=computed_ledger):
            publication._verify_fixed_source_bindings(ROOT, manifest)
            changed = copy.deepcopy(manifest)
            changed["reports"][0]["canonical_report"]["sha256"] = "0" * 64
            with self.assertRaises(publication.PublicationEvidenceError):
                publication._verify_fixed_source_bindings(ROOT, changed)

    def test_relocation_changes_only_raw_output_paths(self) -> None:
        original = {
            "results": [
                {"case_id": "case-a", "outcome": "supported", "raw_output": "reports/raw/a.json"},
                {"case_id": "case-b", "outcome": "unsupported", "raw_output": "reports/raw/b.json"},
            ],
            "schema_version": "0.9.2",
        }
        mappings = [
            {"case_id": "case-a", "ordinal": 0, "source_path": "reports/raw/a.json",
             "capture_path": publication.CAPTURE_SCOPE + "/raw/adapter/case-a.json",
             "sha256": "a" * 64, "bytes": 3},
            {"case_id": "case-b", "ordinal": 1, "source_path": "reports/raw/b.json",
             "capture_path": publication.CAPTURE_SCOPE + "/raw/adapter/case-b.json",
             "sha256": "b" * 64, "bytes": 4},
        ]
        moved = copy.deepcopy(original)
        for row, mapping in zip(moved["results"], mappings):
            row["raw_output"] = mapping["capture_path"]
        publication._check_report_mapping(original, moved, {"raw_outputs": mappings})

        altered = copy.deepcopy(moved)
        altered["results"][0]["outcome"] = "inconclusive"
        with self.assertRaises(publication.PublicationEvidenceError):
            publication._check_report_mapping(original, altered, {"raw_outputs": mappings})

    def test_duplicate_raw_destination_is_rejected(self) -> None:
        canonical = {"results": [
            {"case_id": "case-a", "raw_output": "reports/raw/a.json"},
            {"case_id": "case-b", "raw_output": "reports/raw/b.json"},
        ]}
        collided = publication.CAPTURE_SCOPE + "/raw/adapter/shared.json"
        mappings = [
            {"case_id": "case-a", "ordinal": 0, "source_path": "reports/raw/a.json",
             "capture_path": collided, "sha256": "a" * 64, "bytes": 3},
            {"case_id": "case-b", "ordinal": 1, "source_path": "reports/raw/b.json",
             "capture_path": collided, "sha256": "b" * 64, "bytes": 4},
        ]
        published = {"results": [dict(canonical["results"][0], raw_output=collided),
                                  dict(canonical["results"][1], raw_output=collided)]}
        with self.assertRaisesRegex(publication.PublicationEvidenceError, "collides"):
            publication._check_report_mapping(canonical, published, {"raw_outputs": mappings})

    def test_qualification_sidecar_preserves_flags_and_rejects_drift(self) -> None:
        sidecar_raw = publication._read_file(ROOT, publication.JOERN_SIDECAR_PATH,
                                             expected_sha256=publication.JOERN_SIDECAR_SHA256)
        sidecar_obj = publication._json(sidecar_raw, "original Joern sidecar")
        context = {
            "joern_sidecar": sidecar_obj,
            "joern_sidecar_raw": sidecar_raw,
            "joern_sidecar_ref": {"path": publication.JOERN_SIDECAR_PATH,
                                  "sha256": publication.JOERN_SIDECAR_SHA256,
                                  "bytes": len(sidecar_raw)},
        }
        prepared = publication._qualification_sidecar(context)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rel = publication.PUBLICATION_SCOPE + "/qualification-sidecar.json"
            target = root.joinpath(*Path(rel).parts)
            target.parent.mkdir(parents=True)
            good_raw = json.dumps(prepared, sort_keys=True, indent=2,
                                  ensure_ascii=False).encode("utf-8") + b"\n"
            target.write_bytes(good_raw)
            sources = {"joern_metadata_sidecar": context["joern_sidecar_ref"]}
            state = {
                "publication_approved": False,
                "full_release_gate_satisfied": False,
                "freeze_created": False,
                "scoring_enabled": False,
                "scorecard_generation_allowed": False,
                "bifrost_full_policy_qualification": False,
                "joern_inconclusive": 96,
                "joern_unsupported": 12,
                "joern_aggregate_resource_qualification": "unavailable",
                "joern_scored_activation": False,
                "joern_scoring_permitted": False,
                "joern_timing_certified": False,
            }
            manifest = {
                "sources": sources,
                "qualification_sidecar": {"path": rel, "sha256": _digest(good_raw),
                                           "bytes": len(good_raw)},
                "qualification_state": state,
            }
            verified = publication._validate_qualification_sidecar(root, manifest)
            self.assertEqual(verified["joern_swift_common108"]["inconclusive"], 96)
            self.assertFalse(verified["joern_swift_common108"]["scored_activation"])

            drifted = copy.deepcopy(prepared)
            drifted["joern_swift_common108"]["scored_activation"] = True
            bad_raw = json.dumps(drifted, sort_keys=True, indent=2,
                                 ensure_ascii=False).encode("utf-8") + b"\n"
            target.write_bytes(bad_raw)
            manifest["qualification_sidecar"] = {"path": rel, "sha256": _digest(bad_raw),
                                                   "bytes": len(bad_raw)}
            with self.assertRaisesRegex(publication.PublicationEvidenceError,
                                        "nonqualification boundary"):
                publication._validate_qualification_sidecar(root, manifest)

            integer_drift = copy.deepcopy(prepared)
            integer_drift["publication"]["scoring_enabled"] = 0
            integer_raw = json.dumps(integer_drift, sort_keys=True, indent=2,
                                     ensure_ascii=False).encode("utf-8") + b"\n"
            target.write_bytes(integer_raw)
            manifest["qualification_sidecar"] = {"path": rel, "sha256": _digest(integer_raw),
                                                   "bytes": len(integer_raw)}
            with self.assertRaisesRegex(publication.PublicationEvidenceError,
                                        "nonqualification boundary"):
                publication._validate_qualification_sidecar(root, manifest)

            target.write_bytes(good_raw)
            manifest["qualification_sidecar"] = {"path": rel, "sha256": _digest(good_raw),
                                                   "bytes": len(good_raw)}
            manifest["qualification_state"]["scoring_enabled"] = 0
            with self.assertRaisesRegex(publication.PublicationEvidenceError,
                                        "qualification flags differ"):
                publication._validate_qualification_sidecar(root, manifest)

    def test_symlink_component_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            real = base / "real"
            real.mkdir()
            link = base / "linked"
            link.symlink_to(real, target_is_directory=True)
            root = publication._root(base)
            with self.assertRaises(publication.PublicationEvidenceError):
                publication._join(root, "linked/missing.json", "fixture path", exists=False)

    def test_bundle_index_symlink_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root.joinpath(*Path(publication.BUNDLE_PATH).parts)
            bundle.mkdir(parents=True)
            target = root / "outside-bundle-index.json"
            target.write_text("{}\n", encoding="utf-8")
            (bundle / "bundle.json").symlink_to(target)
            with self.assertRaises(publication.PublicationEvidenceError):
                publication._restore_bundle(root, bundle, {}, {})

    def test_stage_site_copies_only_manifest_bound_raw_bytes(self) -> None:
        payload = b'{"case_id":"case-a","raw":"fixture"}\n'
        payload_sha = _digest(payload)
        capture_path = publication.CAPTURE_SCOPE + "/raw/adapter/case-a.json"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root.joinpath(*Path(capture_path).parts)
            source.parent.mkdir(parents=True)
            source.write_bytes(payload)
            manifest_path = root / publication.PUBLICATION_SCOPE / "manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps({
                "reports": [{"adapter_id": "adapter", "raw_outputs": [{
                    "case_id": "case-a", "ordinal": 0, "capture_path": capture_path,
                    "sha256": payload_sha, "bytes": len(payload),
                }]}],
            }), encoding="utf-8")
            with mock.patch.object(publication, "verify", return_value={"counts": {"raw_files": 1}}):
                result = publication.stage_site(root, "docs/public/evidence/v0-9-2")
                self.assertEqual(result["files"], 1)
                output = root / "docs/public/evidence/v0-9-2/adapter/case-a.json"
                self.assertEqual(output.read_bytes(), payload)
                self.assertEqual(publication.stage_site(root, "docs/public/evidence/v0-9-2")["files"], 1)
                (output.parent / "unexpected.json").write_bytes(b"unexpected")
                with self.assertRaisesRegex(publication.PublicationEvidenceError, "exact expected file set"):
                    publication.stage_site(root, "docs/public/evidence/v0-9-2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
