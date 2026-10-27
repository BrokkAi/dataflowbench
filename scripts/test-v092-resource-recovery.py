#!/usr/bin/env python3
"""Focused unit tests for the read-only v0.9.2 resource recovery parser."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import v092_resource_recovery as recovery


class ResourceRecoveryParserTests(unittest.TestCase):
    def test_canonical_ledger_returns_line_digest_and_rejects_noncanonical_json(self) -> None:
        row = {"attempt_id": "sample-attempt-01-series-01", "status": "completed"}
        raw = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        parsed = recovery._canonical_ledger(raw, "test ledger")
        self.assertEqual(parsed, [(row, hashlib.sha256(raw).hexdigest())])

        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._canonical_ledger(b'{"status":"completed", "attempt_id":"sample-attempt-01-series-01"}\n',
                                       "test ledger")

    def test_bound_reference_rejects_extra_fields_and_wrong_path(self) -> None:
        reference = {"path": recovery.MANIFEST_PATH.as_posix(), "sha256": "a" * 64}
        self.assertEqual(
            recovery._bound_ref(reference, recovery.MANIFEST_PATH, "manifest"),
            (recovery.MANIFEST_PATH.as_posix(), "a" * 64),
        )
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._bound_ref({**reference, "extra": True}, recovery.MANIFEST_PATH, "manifest")
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._bound_ref({**reference, "path": "../manifest.json"}, recovery.MANIFEST_PATH, "manifest")

    def test_json_objects_reject_duplicate_keys_and_nonstandard_constants(self) -> None:
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._json_object(b'{"schema":"first","schema":"second"}', "manifest")
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._json_object(b'{"budget":NaN}', "manifest")

    def test_authorization_preserves_the_exact_resource_and_history_scope(self) -> None:
        authorization = {
            "schema": "v092-resource-recovery-authorization/v1",
            "recorded_utc": "2026-10-20T12:00:00+00:00",
            "evidence_kind": "human-chat-authorization-record",
            "request": recovery.AUTHORIZATION_REQUEST,
            "human_reply": recovery.AUTHORIZATION_REPLY,
            "authorized_scope": recovery._expected_authorized_scope(),
            "forbidden": [
                "Promoting failed reports",
                "Relabeling C1, C2, or C3 measurements as executed under C4",
                "Changing the original deadline, execution series, or attempt cap",
                "Changing the v0.9.0 population, analyzer families, tool bindings, or C3 command vectors",
                "Reducing the 40 GiB protected reserve or weakening the 48 GiB stop and 12 GiB working-set guards",
            ],
        }
        recovery._validate_authorization(authorization)
        authorization["authorized_scope"] = dict(authorization["authorized_scope"])
        authorization["authorized_scope"]["minimum_launch_free_gib"] = 125
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._validate_authorization(authorization)
        authorization["authorized_scope"]["minimum_launch_free_gib"] = 110
        authorization["human_reply"] = "authorized to reduce the reserve"
        with self.assertRaises(recovery.ResourceRecoveryError):
            recovery._validate_authorization(authorization)

    def test_started_receipt_must_keep_the_original_runner_and_argv(self) -> None:
        attempt_id = "sample-attempt-01-series-01"
        fields = {
            "execution_series": 1,
            "group_id": "sample",
            "attempt_id": attempt_id,
            "source_commit": "1" * 40,
            "plan_commit": "2" * 40,
            "contract_sha256": "3" * 64,
            "runner_source_sha256": "4" * 64,
            "fixture_revision": "sha256:" + "5" * 64,
            "population": {"sha256": "6" * 64},
            "tool": "codeql",
            "tool_binding": {"path": "/tools/codeql", "sha256": "7" * 64},
            "identity_components": [],
            "qualification": {},
            "source_inputs": [],
            "cache_root": "/tmp/cache",
            "argv": ["/tools/harness", "run", "sample"],
            "environment": {"PATH": "/usr/bin"},
            "execution_root": "/tmp/exec",
            "output_roots": ["reports/sample.json"],
            "case_ids": ["case-1"],
            "deadline_seconds": 600,
            "start_utc": "2026-10-20T12:00:00+00:00",
        }
        completed = {**fields, "status": "completed", "end_utc": "2026-10-20T12:01:00+00:00"}
        started = {**fields, "status": "started", "end_utc": None}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt_root = root / "reports/releases/v0.9.2/attempts" / attempt_id
            attempt_root.mkdir(parents=True)
            started_raw = json.dumps(started).encode()
            completed_raw = json.dumps(completed).encode()
            (attempt_root / "started.json").write_bytes(started_raw)
            (attempt_root / "completed.json").write_bytes(completed_raw)
            item = {
                "attempt_id": attempt_id,
                "status": "completed",
                "started_receipt": {
                    "path": f"reports/releases/v0.9.2/attempts/{attempt_id}/started.json",
                    "sha256": hashlib.sha256(started_raw).hexdigest(),
                },
                "completed_receipt": {
                    "path": f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json",
                    "sha256": hashlib.sha256(completed_raw).hexdigest(),
                },
            }
            recovery._verify_attempt_artifacts(root, item, completed, status="completed")

            changed_started = {**started, "argv": ["/different/harness", "run", "sample"]}
            changed_raw = json.dumps(changed_started).encode()
            (attempt_root / "started.json").write_bytes(changed_raw)
            item["started_receipt"]["sha256"] = hashlib.sha256(changed_raw).hexdigest()
            with self.assertRaises(recovery.ResourceRecoveryError):
                recovery._verify_attempt_artifacts(root, item, completed, status="completed")


if __name__ == "__main__":
    unittest.main()
