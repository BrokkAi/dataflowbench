#!/usr/bin/env python3
"""Focused tests for the canonical v0.9.2 report-configuration gate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("validate-v092-report-configurations.py")
SPEC = importlib.util.spec_from_file_location("validate_v092_report_configurations_tested", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReportProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.checkout = Path(temporary.name) / "checkout"
        self.root.mkdir()
        self.checkout.mkdir()
        self.bindings = []
        self.raw_paths = []

    def _add_report(self, name: str, attempt_id: str, case_id: str, raw_bytes: bytes,
                    *, raw_path: str | None = None, mapping_sha: str | None = None) -> None:
        raw_path = raw_path or (
            f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/raw/{case_id}.json"
        )
        raw_target = self.root / raw_path
        raw_target.parent.mkdir(parents=True, exist_ok=True)
        raw_target.write_bytes(raw_bytes)
        self.raw_paths.append(raw_path)

        adapter = f"reports/releases/v0.9.2/normal/{name}"
        staged = f"reports/releases/v0.9.2/normal/attempts/{attempt_id}/{name}"
        report_value = {
            "schema_version": 1,
            "tool": "bifrost",
            "tool_version": "0.13.1",
            "adapter_version": "fixture",
            "configuration_hash": "a" * 64,
            "results": [{"case_id": case_id, "raw_output": raw_path}],
        }
        report_bytes = (json.dumps(report_value, sort_keys=True) + "\n").encode()
        report_target = self.root / staged
        report_target.parent.mkdir(parents=True, exist_ok=True)
        report_target.write_bytes(report_bytes)
        completed = self.root / "reports/releases/v0.9.2/attempts" / attempt_id / "completed.json"
        completed.parent.mkdir(parents=True, exist_ok=True)
        completed.write_text(json.dumps({
            "status": "completed",
            "attempt_id": attempt_id,
            "reports": [{
                "staged_path": staged,
                "staged_sha256": sha(report_bytes),
                "raw_output_mappings": [{
                    "execution_relative": raw_path.split(
                        f"reports/releases/v0.9.2/attempts/{attempt_id}/capture/", 1,
                    )[-1],
                    "captured_path": raw_path,
                    "sha256": mapping_sha or sha(raw_bytes),
                    "bytes": len(raw_bytes),
                }],
            }],
        }, sort_keys=True) + "\n")
        self.bindings.append({
            "adapter": adapter,
            "staged_path": staged,
            "sha256": sha(report_bytes),
            "rows": 1,
            "attempt_id": attempt_id,
            "attempt_number": 1,
        })

    def _project(self, expected_count: int | None = None):
        expected_count = expected_count if expected_count is not None else len(self.bindings)
        selected_attempts = []
        seen_attempts = set()
        for binding in self.bindings:
            attempt_id = binding["attempt_id"]
            if attempt_id in seen_attempts:
                continue
            seen_attempts.add(attempt_id)
            completed = self.root / "reports/releases/v0.9.2/attempts" / attempt_id / "completed.json"
            selected_attempts.append({
                "attempt_id": attempt_id,
                "status": "completed",
                "completed_receipt_sha256": sha(completed.read_bytes()),
            })
        return validator._project_reports(
            self.root,
            self.checkout,
            {"fresh_reports": self.bindings, "selected_attempts": selected_attempts},
            expected_report_count=expected_count,
            expected_row_count=len(self.bindings),
        )

    def test_copies_only_selected_reports_and_referenced_raw_files(self):
        self._add_report("fixture-a.json", "group-a-attempt-01-series-07", "case-a", b"raw-a\n")
        self._add_report("fixture-b.json", "group-b-attempt-01-series-07", "case-b", b"raw-b\n")
        orphan = self.root / "reports/releases/v0.9.2/attempts/orphan/capture/unused.json"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"not referenced\n")

        reports, raw_files, attempts = self._project()

        self.assertEqual([item["validation_path"] for item in reports],
                         ["reports/fixture-a.json", "reports/fixture-b.json"])
        self.assertEqual(len(raw_files), 2)
        self.assertEqual(len(attempts), 2)
        self.assertEqual((self.checkout / self.raw_paths[0]).read_bytes(), b"raw-a\n")
        self.assertFalse((self.checkout / "reports/releases/v0.9.2/attempts/orphan/capture/unused.json").exists())

    def test_rejects_raw_path_escape(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw\n")
        report_path = self.root / self.bindings[0]["staged_path"]
        report_value = json.loads(report_path.read_text())
        report_value["results"][0]["raw_output"] = "../escape.json"
        report_path.write_text(json.dumps(report_value, sort_keys=True) + "\n")
        self.bindings[0]["sha256"] = sha(report_path.read_bytes())
        receipt_path = self.root / "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/completed.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["reports"][0]["staged_sha256"] = self.bindings[0]["sha256"]
        receipt["reports"][0]["raw_output_mappings"][0]["captured_path"] = "../escape.json"
        receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "escapes its root"):
            self._project()

    def test_rejects_conflicting_raw_path_collision_within_a_report_receipt(self):
        shared = "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/capture/raw/shared.json"
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"same bytes\n",
                         raw_path=shared)
        staged = self.root / self.bindings[0]["staged_path"]
        report = json.loads(staged.read_text())
        report["results"].append({"case_id": "case-b", "raw_output": shared})
        report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode()
        staged.write_bytes(report_bytes)
        self.bindings[0]["sha256"] = sha(report_bytes)
        self.bindings[0]["rows"] = 2
        receipt_path = self.root / "reports/releases/v0.9.2/attempts/group-a-attempt-01-series-07/completed.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["reports"][0]["staged_sha256"] = self.bindings[0]["sha256"]
        receipt["reports"][0]["raw_output_mappings"].append({
            "execution_relative": "raw/shared.json",
            "captured_path": shared,
            "sha256": "0" * 64,
            "bytes": len(b"same bytes\n"),
        })
        receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "repeats a raw-output path"):
            self._project()

    def test_rejects_tampered_raw_bytes(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"original\n")
        (self.root / self.raw_paths[0]).write_bytes(b"tampered\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "changed after checker verification"):
            self._project()

    def test_rejects_tampered_staged_report(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw\n")
        (self.root / self.bindings[0]["staged_path"]).write_bytes(b"{}\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "changed after checker verification"):
            self._project()

    def test_rejects_report_filename_collision(self):
        self._add_report("fixture.json", "group-a-attempt-01-series-07", "case-a", b"raw-a\n")
        self._add_report("fixture.json", "group-b-attempt-01-series-07", "case-b", b"raw-b\n")

        with self.assertRaisesRegex(validator.ValidationEvidenceError, "collide"):
            self._project()


class CanonicalOutputTests(unittest.TestCase):
    def test_validation_artifacts_use_the_punctuated_release_namespace(self):
        self.assertEqual(validator.RECEIPTS.as_posix(), "reports/releases/v0.9.2/validation")
        self.assertEqual(validator.CHECKOUTS.as_posix(), "execution-state/v092/validation")

    def test_parses_exact_validator_counts_and_derives_not_derivable_honestly(self):
        metrics = validator._parse_stdout(
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        self.assertEqual(metrics, {
            "validated_reports": 92,
            "checked_configuration_hashes": 81,
            "known_stale": 0,
            "not_derivable": 11,
        })
        self.assertTrue(validator._validation_success(0, metrics))

    def test_rejects_missing_or_duplicate_metric_lines(self):
        invalid = [
            b"validated 92 reports\n",
            b"validated 92 reports\nvalidated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n",
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n",
        ]
        for stdout in invalid:
            with self.subTest(stdout=stdout):
                with self.assertRaises(validator.ValidationEvidenceError):
                    validator._parse_stdout(stdout)

    def test_wrong_report_count_and_known_stale_metric_cannot_pass(self):
        wrong_count = validator._parse_stdout(
            b"validated 91 reports\nchecked 81 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        known_stale = validator._parse_stdout(
            b"validated 92 reports\nchecked 81 configuration hashes against the working tree (1 known-stale under issue #138)\n"
        )
        self.assertFalse(validator._validation_success(0, wrong_count))
        self.assertFalse(validator._validation_success(0, known_stale))

    def test_zero_checked_configuration_hashes_cannot_pass(self):
        metrics = validator._parse_stdout(
            b"validated 92 reports\nchecked 0 configuration hashes against the working tree (0 known-stale under issue #138)\n"
        )
        self.assertEqual(metrics["not_derivable"], 92)
        self.assertFalse(validator._validation_success(0, metrics))

    def test_nonzero_exit_or_mismatched_counts_cannot_pass(self):
        metrics = {
            "validated_reports": 92,
            "checked_configuration_hashes": 90,
            "known_stale": 0,
            "not_derivable": 2,
        }
        self.assertFalse(validator._validation_success(1, metrics))
        self.assertFalse(validator._validation_success(0, {**metrics, "validated_reports": 91}))
        self.assertFalse(validator._validation_success(0, {**metrics, "known_stale": 1}))

    def test_invokes_only_the_bound_runner_validate_reports_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "fake-runner"
            binary.write_text(
                "#!/bin/sh\n"
                "[ \"$1\" = \"--population\" ] && [ \"$2\" = \"v0.9.0\" ] && [ \"$3\" = \"validate-reports\" ] || exit 91\n"
                "printf 'validated 92 reports\\nchecked 90 configuration hashes against the working tree (0 known-stale under issue #138)\\n'\n"
                "printf 'fake canonical harness\\n' >&2\n"
            )
            binary.chmod(0o755)
            checkout = root / "checkout"
            checkout.mkdir()
            binding = {"path": str(binary), "sha256": sha(binary.read_bytes())}
            env = {"PATH": "/usr/bin:/bin", "HOME": str(checkout), "TMPDIR": str(checkout), "LANG": "C", "LC_ALL": "C"}

            result = validator._invoke_runner(binding, checkout, env)

            self.assertEqual(result["argv"], [str(binary), "--population", "v0.9.0", "validate-reports"])
            self.assertEqual(result["cwd"], str(checkout))
            self.assertEqual(result["exit_code"], 0)
            self.assertIn(b"validated 92 reports", result["stdout"])
            self.assertEqual(result["stderr"], b"fake canonical harness\n")

    def test_rejects_runner_binary_hash_drift_before_invocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "fake-runner"
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            binding = {"path": str(binary), "sha256": "0" * 64}
            with self.assertRaisesRegex(validator.ValidationEvidenceError, "SHA-256 differs"):
                validator._invoke_runner(binding, root, {"PATH": "/usr/bin:/bin"})


if __name__ == "__main__":
    unittest.main()
