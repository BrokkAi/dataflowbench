"""Guard the offline reconciler's file and process boundaries."""
import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import v092_reconcile_joern_swift_wording as cli


class OfflineBoundaryTests(unittest.TestCase):
    def test_shared_historical_reason_does_not_allow_cross_case_rebinding(self):
        case_id = "case-one"
        decision_ref = {"path": "decisions/case-one.json", "sha256": "1" * 64}
        case_row = {"disposition": "unsupported", "decision": decision_ref}
        historical = {"schema": "joern-current108-partition-decision/v1", "case_id": case_id,
                      "outcome": "unsupported", "population_sha256": "2" * 64,
                      "identity": {"tool": "historical"}, "reason": "shared wording",
                      "fixture_revision": "historical-per-case-revision",
                      "current_case_sha256": "3" * 64, "current_fixture_digests": []}
        scope = {"historical_reason": historical["reason"], "historical_identity": historical["identity"],
                 "historical_fixture_revision": historical["fixture_revision"],
                 "case_json": {"sha256": "3" * 64}, "fixtures": [],
                 "historical_case_row": case_row, "historical_decision": decision_ref}
        plan = {"identity": historical["identity"], "cases": {case_id: case_row}}
        cli.validate_historical_provenance(case_id, historical, scope, plan, "2" * 64)
        with self.assertRaisesRegex(ValueError, "exact case-bound decline"):
            cli.validate_historical_provenance(case_id, {**historical, "case_id": "case-two"}, scope, plan, "2" * 64)

    def test_report_raw_link_and_timing_cannot_drift(self):
        raw = {"duration_ms": 23, "state": "inconclusive", "witness_checkpoints": []}
        ref = {"path": "raw/case.json", "sha256": "1" * 64}
        row = {"duration_ms": 23, "outcome": "inconclusive", "witness_checkpoints": [],
               "raw_output": ref["path"], "raw_sha256": ref["sha256"]}
        cli.validate_report_raw_binding(row, raw, ref)
        for changed in ({"raw_output": "raw/other-case.json"}, {"raw_sha256": "2" * 64},
                        {"duration_ms": 24}, {"duration_ms": False}):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "raw-result binding"):
                cli.validate_report_raw_binding({**row, **changed}, raw, ref)

    def capture(self, root, path):
        result = object.__new__(cli.Capture)
        result.root = root
        info = path.stat()
        result.files = [{"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "size_bytes": info.st_size, "mode": stat.S_IMODE(info.st_mode)}]
        result.by_path = {row["path"]: row for row in result.files}
        return result

    def test_same_size_capture_edit_fails_hash_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / "evidence.json"
            path.write_bytes(b"original")
            capture = self.capture(root, path)
            capture.verify()
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "sealed capture changed"):
                capture.verify()

    def test_missing_capture_file_fails_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / "evidence.json"
            path.write_text("source")
            capture = self.capture(root, path)
            path.unlink()
            with self.assertRaisesRegex(ValueError, "sealed file missing"):
                capture.verify()

    def test_symlink_alias_and_parent_traversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "original").mkdir()
            (root / "alias").symlink_to(root / "original", target_is_directory=True)
            for value in ("alias/result.json", "../result.json", "/absolute/result.json"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    cli.safe_path(root, value)

    def test_unsealed_file_cannot_supply_a_source_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / "evidence.json"
            path.write_text("source")
            capture = self.capture(root, path)
            (root / "extra.json").write_text("unsealed")
            with self.assertRaisesRegex(ValueError, "outside the sealed capture"):
                capture.read("extra.json")

    def test_release_reader_uses_only_exact_git_show(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with patch.object(cli.subprocess, "check_output", return_value=b"released") as command:
                self.assertEqual(cli.released(root, "records/decline.json", cli.digest(b"released")), b"released")
            command.assert_called_once_with(
                ["git", "show", cli.RELEASE + ":records/decline.json"], cwd=root)
            with patch.object(cli.subprocess, "check_output", return_value=b"different"):
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    cli.released(root, "records/decline.json", cli.digest(b"released"))

    def test_existing_audit_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = root / cli.PREFIX / "joern-swift-audit-01"
            output.mkdir(parents=True)
            sentinel = output / "retained.json"
            sentinel.write_text("preserved")
            with patch.object(cli, "validate_capture") as validate:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    cli.build(root, "01")
            validate.assert_not_called()
            self.assertEqual(sentinel.read_text(), "preserved")


if __name__ == "__main__":
    unittest.main()
