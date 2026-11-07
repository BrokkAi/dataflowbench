#!/usr/bin/env python3
"""Focused synthetic tests for the v0.9.2 publication release gate."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest import mock


GATE_PATH = Path(__file__).with_name("check-release-v092-results.py")
GATE_SOURCE = GATE_PATH.read_bytes()
gate = types.ModuleType("check_release_v092_results_tested_source")
exec(compile(GATE_SOURCE, str(GATE_PATH), "exec"), gate.__dict__)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(root: Path, path: str, data: bytes) -> Path:
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def _write_json(root: Path, path: str, value: object) -> tuple[Path, bytes]:
    data = _json_bytes(value)
    return _write(root, path, data), data


def _record(path: str, data: bytes) -> dict:
    return {"path": path, "sha256": _sha(data), "bytes": len(data)}


def _qualification(root: Path) -> dict:
    source_path = (
        "execution-state/v092/publication-evidence/joern108-canonical-schema-01/"
        "projection-03/sidecars/aggregate-metadata-lift.json"
    )
    state = copy.deepcopy(gate.EXPECTED_QUALIFICATION)
    lift = {
        "schema": "v092-joern-schema-metadata-lift-aggregate/v1",
        "aggregate_counts": {
            "cases": 108,
            "distinct_raw_output_paths": 108,
            "outcomes": {"inconclusive": 96, "unsupported": 12},
            "reports": 5,
        },
        "lift_boundary": {
            "evidence_scope": "semantic-only",
            "preserve_all_other_fields_exactly": True,
            "removed_result_field": "results[*].raw_sha256",
            "removed_top_level_fields": {
                "aggregate_resource_qualification": "unavailable",
                "scored_activation": False,
            },
            "scoring_permitted": False,
            "semantic_qualification": "unavailable",
            "this_is_not_a_schema_waiver": True,
            "timing_certified": False,
        },
        "reports": [{"report": index} for index in range(5)],
    }
    source_data = (
        json.dumps(lift, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    _write(root, source_path, source_data)
    sidecar = {
        "schema": "dataflowbench-v0.9.2-publication-qualification-boundary/v1",
        **state,
        "source_joern_sidecar": _record(source_path, source_data),
        "source_joern_sidecar_json": source_data.decode(),
        "joern_metadata_lift": lift,
    }
    sidecar_data = _json_bytes(sidecar)
    _write(root, gate.QUALIFICATION_SIDECAR, sidecar_data)
    return _record(gate.QUALIFICATION_SIDECAR, sidecar_data)


def _make_publication(root: Path) -> dict:
    qualification = _qualification(root)
    source_joern_sidecar = json.loads(
        (root / gate.QUALIFICATION_SIDECAR).read_bytes()
    )["source_joern_sidecar"]
    case_ids = [f"case-{index:04d}" for index in range(gate.EXPECTED_COUNTS["unique_case_ids"])]
    publication_reports = []
    freeze_reports = []
    capture_files = []
    row_cursor = 0
    raw_file_index = 0
    for index in range(gate.EXPECTED_COUNTS["reports"]):
        group = index // 2 if index < 16 else 8 + index - 16
        adapter = f"adapter-{group:03d}"
        row_count = 46 if index < 91 else 66
        attempt_id = f"{adapter}-attempt-{index:02d}"
        selected_ids = [case_ids[(row_cursor + offset) % len(case_ids)] for offset in range(row_count)]
        row_cursor += row_count
        raw_outputs = []
        results = []
        for case_id in selected_ids:
            source_path = f"capture/raw/{adapter}/{case_id}.json"
            capture_path = f"{gate.PUBLICATION_CAPTURE}/raw/{adapter}/{raw_file_index:04d}.json"
            raw_file_index += 1
            raw_outputs.append(
                {
                    "case_id": case_id,
                    "ordinal": len(raw_outputs),
                    "source_path": source_path,
                    "capture_path": capture_path,
                    "sha256": _sha(b"raw fixture"),
                    "bytes": len(b"raw fixture"),
                }
            )
            capture_files.append(
                {
                    "path": capture_path,
                    "sha256": _sha(b"raw fixture"),
                    "bytes": len(b"raw fixture"),
                    "kind": "raw-output",
                }
            )
            results.append({"case_id": case_id, "raw_output": capture_path})
        report_path = f"{gate.PUBLICATION_DIR}/normal/{index:02d}.json"
        report_data = _json_bytes({"schema_version": 1, "results": results})
        _write(root, report_path, report_data)
        report_record = _record(report_path, report_data)
        canonical_path = f"{gate.PUBLICATION_CAPTURE}/source-reports/{index:02d}.json"
        canonical_data = _json_bytes({"source_report": index})
        capture_files.append(
            {
                "path": canonical_path,
                "sha256": _sha(canonical_data),
                "bytes": len(canonical_data),
                "kind": "canonical-source-report",
            }
        )
        if index < 5:
            selected_path = f"{gate.PUBLICATION_CAPTURE}/selected-reports/{index:02d}.json"
            selected_data = _json_bytes({"selected_report": index})
            capture_files.append(
                {
                    "path": selected_path,
                    "sha256": _sha(selected_data),
                    "bytes": len(selected_data),
                    "kind": "selected-original-joern-report",
                }
            )
            selected_original = _record(selected_path, selected_data)
        else:
            selected_original = _record(canonical_path, canonical_data)
        publication_reports.append(
            {
                "adapter": adapter,
                "attempt_id": attempt_id,
                "attempt_number": index + 1,
                "row_count": row_count,
                "adapter_id": adapter,
                "canonical_report": _record(canonical_path, canonical_data),
                "capture_source_report": _record(canonical_path, canonical_data),
                "capture_selected_report": (
                    _record(selected_path, selected_data) if index < 5 else None
                ),
                "selected_original": selected_original,
                "lifted_metadata": index < 5,
                "published_report": report_record,
                "raw_outputs": raw_outputs,
            }
        )
        freeze_reports.append(
            {
                "path": report_path,
                "normalized_report_sha256": report_record["sha256"],
                "case_ids": selected_ids,
            }
        )
    publication = {
        "schema": "dataflowbench-v0.9.2-publication-evidence/v1",
        "scope": gate.PUBLICATION_DIR,
        "capture_scope": gate.PUBLICATION_CAPTURE,
        "bundle_delivery_path": gate.PUBLICATION_BUNDLE,
        "counts": copy.deepcopy(gate.EXPECTED_COUNTS),
        "sources": {"joern_metadata_sidecar": source_joern_sidecar},
        "capture_files": capture_files,
        "qualification_state": {
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
        },
        "qualification_sidecar": qualification,
        "reports": publication_reports,
    }
    _write_json(root, gate.PUBLICATION_MANIFEST, publication)
    freeze = {
        "schema_version": 1,
        "claim": {"scope": "release"},
        "benchmark": {"release": gate.RELEASE, "revision": "a" * 40, "dirty": False},
        "reports": freeze_reports,
        "cases": [{"id": case_id} for case_id in case_ids],
    }
    _write_json(root, "reports/freeze.json", freeze)
    return publication


class PublicationFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="v092-freeze-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.revision = "a" * 40
        self.publication = _make_publication(self.root)
        self.freeze_path = self.root / "reports/freeze.json"

    def write_manifest(self, manifest: dict) -> None:
        _write_json(self.root, gate.PUBLICATION_MANIFEST, manifest)

    def write_freeze(self, freeze: dict) -> None:
        _write_json(self.root, "reports/freeze.json", freeze)

    def test_exact_publication_manifest_and_freeze_are_accepted(self) -> None:
        summary = gate.validate_freeze(self.root, self.revision)
        self.assertEqual(summary["release"], "v0.9.2")
        self.assertEqual(summary["reports"], 92)
        self.assertEqual(summary["rows"], 4_252)
        self.assertEqual(summary["unique_case_ids"], 1_108)
        self.assertEqual(summary["raw_files"], 4_252)

    def test_wrong_release_revision_or_dirty_claim_is_rejected(self) -> None:
        original = json.loads(self.freeze_path.read_text())
        for field, value in (("release", "v0.9.0"), ("revision", "b" * 40), ("dirty", True)):
            with self.subTest(field=field):
                freeze = copy.deepcopy(original)
                freeze["benchmark"][field] = value
                self.write_freeze(freeze)
                with self.assertRaisesRegex(gate.GateError, "exact merged"):
                    gate.validate_freeze(self.root, self.revision)
        self.write_freeze(original)

    def test_manifest_report_hash_mapping_must_match_freeze(self) -> None:
        freeze = json.loads(self.freeze_path.read_text())
        freeze["reports"][0]["normalized_report_sha256"] = "f" * 64
        self.write_freeze(freeze)
        with self.assertRaisesRegex(gate.GateError, "paths/hashes differ"):
            gate.validate_freeze(self.root, self.revision)

    def test_missing_partition_or_wrong_row_total_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.publication)
        manifest["reports"].pop()
        self.write_manifest(manifest)
        with self.assertRaisesRegex(gate.GateError, "exactly 92"):
            gate.validate_freeze(self.root, self.revision)

        manifest = copy.deepcopy(self.publication)
        manifest["counts"]["rows"] -= 1
        self.write_manifest(manifest)
        with self.assertRaisesRegex(gate.GateError, "counts do not match"):
            gate.validate_freeze(self.root, self.revision)

    def test_population_substitution_is_rejected(self) -> None:
        freeze = json.loads(self.freeze_path.read_text())
        freeze["cases"][0]["id"] = "substituted-case"
        self.write_freeze(freeze)
        with self.assertRaisesRegex(gate.GateError, "population case ids differ"):
            gate.validate_freeze(self.root, self.revision)

    def test_qualification_upgrade_is_rejected_even_with_rebound_hash(self) -> None:
        sidecar_path = self.root / gate.QUALIFICATION_SIDECAR
        sidecar = json.loads(sidecar_path.read_text())
        sidecar["joern_swift_common108"]["scored_activation"] = True
        sidecar_data = _json_bytes(sidecar)
        sidecar_path.write_bytes(sidecar_data)
        manifest = copy.deepcopy(self.publication)
        binding = manifest["qualification_sidecar"]
        binding["sha256"] = _sha(sidecar_data)
        binding["bytes"] = len(sidecar_data)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(gate.GateError, "required joern_swift_common108 limits"):
            gate.validate_freeze(self.root, self.revision)

    def test_unknown_qualification_signal_is_rejected_even_with_rebound_hash(self) -> None:
        sidecar_path = self.root / gate.QUALIFICATION_SIDECAR
        sidecar = json.loads(sidecar_path.read_text())
        sidecar["publication"]["extra_qualification_signal"] = True
        sidecar_data = _json_bytes(sidecar)
        sidecar_path.write_bytes(sidecar_data)
        manifest = copy.deepcopy(self.publication)
        manifest["qualification_sidecar"]["sha256"] = _sha(sidecar_data)
        manifest["qualification_sidecar"]["bytes"] = len(sidecar_data)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(gate.GateError, "required publication limits"):
            gate.validate_freeze(self.root, self.revision)

    def test_integer_zero_cannot_substitute_for_pinned_boolean_false(self) -> None:
        sidecar_path = self.root / gate.QUALIFICATION_SIDECAR
        sidecar = json.loads(sidecar_path.read_text())
        sidecar["publication"]["scoring_enabled"] = 0
        sidecar_data = _json_bytes(sidecar)
        sidecar_path.write_bytes(sidecar_data)
        manifest = copy.deepcopy(self.publication)
        manifest["qualification_sidecar"]["sha256"] = _sha(sidecar_data)
        manifest["qualification_sidecar"]["bytes"] = len(sidecar_data)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(gate.GateError, "required publication limits"):
            gate.validate_freeze(self.root, self.revision)

    def test_noncanonical_revision_and_unsafe_path_are_rejected(self) -> None:
        with self.assertRaisesRegex(gate.GateError, "lowercase 40-hex"):
            gate.validate_freeze(self.root, self.revision.upper())
        with self.assertRaisesRegex(gate.GateError, "safe repository-relative"):
            gate._safe_repo_path("../outside", "test path")


class DisposableGateTests(unittest.TestCase):
    @staticmethod
    def _git(*args: str, cwd: Path | None = None) -> str:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

    def test_fake_binary_and_temporary_remote_exercise_sparse_no_tag_path(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="v092-gate-integration-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        source = base / "source"
        source.mkdir()
        _make_publication(source)
        mapper = source / gate.MAPPER
        mapper.parent.mkdir(parents=True, exist_ok=True)
        mapper.write_text("import sys\nsys.exit(0)\n")
        ledger_hydrator = source / gate.LEDGER_HYDRATOR
        ledger_hydrator.write_text("import sys\nsys.exit(0)\n")
        (source / "scripts/check-release-v092-results.py").write_bytes(GATE_SOURCE)
        _write(source, "cases/placeholder.json", b"{}\n")
        _write(source, f"{gate.PUBLICATION_BUNDLE}/placeholder", b"x")
        _write(source, "reports/releases/v0.9.0/old-capture.json", b"historical capture")
        _write(source, "evidence-archives/old-bundle.part0000", b"history archive")

        def git(*args: str, cwd: Path | None = None) -> None:
            subprocess.run(
                ["git", *args], cwd=cwd, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )

        git("init", "-b", "main", cwd=source)
        git("config", "user.name", "Release Gate Test", cwd=source)
        git("config", "user.email", "release-gate@example.invalid", cwd=source)
        git("config", "commit.gpgsign", "false", cwd=source)
        git("add", "-A", cwd=source)
        git("commit", "-m", "synthetic publication inputs", cwd=source)
        evidence_revision = self._git("rev-parse", "HEAD", cwd=source)

        freeze = json.loads((source / "reports/freeze.json").read_text())
        freeze["benchmark"]["revision"] = evidence_revision
        _write_json(source, "reports/freeze.json", freeze)
        git("add", "reports/freeze.json", cwd=source)
        git("commit", "-m", "synthetic release freeze", cwd=source)
        current_head = self._git("rev-parse", "HEAD", cwd=source)

        bare = base / "remote.git"
        git("init", "--bare", str(bare))
        git("push", str(bare), f"{current_head}:refs/heads/main", cwd=source)
        binary = base / "fake-dataflowbench"
        binary.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib, sys\n"
            "args=sys.argv[1:]\n"
            "if args and args[0]=='generate-results':\n"
            " p=pathlib.Path(args[args.index('--output-directory')+1]); p.mkdir(parents=True, exist_ok=True); (p/'synthetic.json').write_text('{}\\n')\n"
        )
        binary.chmod(0o755)
        with mock.patch.object(gate, "_materialize_publication_capture"):
            summary = gate.run_gate(
                source,
                binary=binary,
                evidence_revision=evidence_revision,
                generate_output=base / "generated-results",
                git_remote=str(bare),
            )
        self.assertEqual(summary["release"], "v0.9.2")
        self.assertTrue((base / "generated-results/synthetic.json").is_file())
        self.assertEqual(self._git("tag", "--list", gate.RELEASE, cwd=source), "")
        self.assertTrue((source / "evidence-archives").is_dir())


if __name__ == "__main__":
    unittest.main()
