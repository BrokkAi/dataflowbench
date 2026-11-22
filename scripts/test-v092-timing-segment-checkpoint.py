#!/usr/bin/env python3
"""Focused standard-library regressions for semantic segment checkpoints."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("v092_timing_segment_checkpoint.py")
SPEC = importlib.util.spec_from_file_location("v092_timing_segment_checkpoint_test", SCRIPT)
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)


def _terminal():
    return {
        "group": checkpoint.RUST_GROUP,
        "status": "failed",
        "attempt": 1,
        "automatic_retry": False,
        "exit_code": 0,
        "timed_out": False,
        "capacity_loss": None,
        "publication_eligible": False,
        "not_dispatched": False,
        "error": "FrozenComparisonError: outcome mismatch",
    }


class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.parent = {
            "completed_groups": [f"old-{i}" for i in range(55)],
            "remaining_ready_groups": checkpoint.FIRST_SIX + [f"tail-{i}" for i in range(32)],
        }
        self.progress = [
            row for i, group in enumerate(checkpoint.FIRST_SIX) for row in (
                {"group": group, "status": "started", "utc": f"2026-11-21T00:{i * 2:02d}:00Z"},
                {"group": group,
                 "status": "failed" if group == checkpoint.RUST_GROUP else "completed-candidate-evidence",
                 "utc": f"2026-11-21T00:{i * 2 + 1:02d}:00Z"},
            )
        ]
        self.terminal = {
            "campaign_id": checkpoint.CAMPAIGN_ID,
            "status": "unqualified",
            "publication_eligible": False,
            "stopped_group": checkpoint.RUST_GROUP,
            "completed_candidate_groups": checkpoint.FIRST_SIX[:5],
            "completed_commands": 5,
            "inherited_candidate_groups": self.parent["completed_groups"],
            "inherited_candidate_commands": 55,
            "combined_completed_candidate_commands": 60,
            "remaining_ready_groups": self.parent["remaining_ready_groups"][6:],
            "ready_groups": 38,
            "full_84_group_coverage_claimed": False,
        }

    def test_exact_60_quarantine_32_partition(self):
        completed, quarantined, pending = checkpoint._validate_partition(
            self.parent, self.progress, self.terminal,
        )
        self.assertEqual(len(completed), 60)
        self.assertEqual(quarantined, [checkpoint.RUST_GROUP])
        self.assertEqual(len(pending), 32)
        self.assertEqual(pending[0], "tail-0")

    def test_progress_and_terminal_drift_fail_closed(self):
        progress = copy.deepcopy(self.progress)
        progress[2] = {"group": checkpoint.FIRST_SIX[1], "status": "failed"}
        with self.assertRaises(RuntimeError):
            checkpoint._validate_partition(self.parent, progress, self.terminal)
        terminal = copy.deepcopy(self.terminal)
        terminal["remaining_ready_groups"] = ["wrong"]
        with self.assertRaises(RuntimeError):
            checkpoint._validate_partition(self.parent, self.progress, terminal)


class RustQuarantineTests(unittest.TestCase):
    def test_only_exact_outcome_mismatches_are_quarantinable(self):
        case_ids = ["case-a", "case-b"]
        mismatches = [
            {"case_id": case, "field": "outcome", "classification": "mismatch"}
            for case in case_ids
        ]
        self.assertTrue(checkpoint._outcome_only_mismatches(mismatches, case_ids))
        mismatches[0]["field"] = "configuration_hash"
        self.assertFalse(checkpoint._outcome_only_mismatches(mismatches, case_ids))

    def test_command_timeout_capacity_retry_and_provenance_fail(self):
        base = _terminal()
        checkpoint._validate_rust_terminal_core(base)
        for key, value in (
            ("exit_code", 1), ("timed_out", True), ("capacity_loss", "memory"),
            ("automatic_retry", True), ("status", "completed-candidate-evidence"),
        ):
            terminal = copy.deepcopy(base)
            terminal[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                checkpoint._validate_rust_terminal_core(terminal)
        good = {"source_and_fixture_inputs_unchanged": True,
                "source_commit": "abc", "snapshot_git_head": "abc"}
        self.assertTrue(checkpoint._source_provenance_matches(good, "abc"))
        good["snapshot_git_head"] = "other"
        self.assertFalse(checkpoint._source_provenance_matches(good, "abc"))

    def test_identity_drift_is_not_an_outcome_only_mismatch(self):
        identity = {name: f"value-{name}" for name in checkpoint.IDENTITY_FIELDS}
        measured = dict(identity)
        self.assertTrue(checkpoint._matches_frozen_identity(measured, identity))
        measured["tool_build_identity"] = "different"
        self.assertFalse(checkpoint._matches_frozen_identity(measured, identity))


class PendingAndPlanDriftTests(unittest.TestCase):
    def test_any_pending_attempt_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "reports" / "campaign"
            checkpoint._validate_pending_attempts(root, report, ["pending-group"])
            (report / "attempts" / "pending-group").mkdir(parents=True)
            with self.assertRaises(RuntimeError):
                checkpoint._validate_pending_attempts(root, report, ["pending-group"])

    def _plan_fixture(self, temp_root):
        root = Path(temp_root)
        checkpoint_path = root / "checkpoint.json"
        checkpoint_path.write_text("{}")
        reference = {"path": "checkpoint.json", "sha256": checkpoint.sha(checkpoint_path)}
        auth_path = root / "authorization.json"
        auth_path.write_text(json.dumps({
            "schema": checkpoint.AUTH_SCHEMA, "campaign_id": "20261122-01",
            "authorized": False, "status": "pending", "user_request": "await authorization",
        }, sort_keys=True))
        auth_ref = {"path": "authorization.json", "sha256": checkpoint.sha(auth_path)}
        parent = {
            "campaign_id": checkpoint.CAMPAIGN_ID,
            "created_utc": "old", "launch_after_utc": "old",
            "continuation": {"path": "old.json", "sha256": "a" * 64},
            "preregistration": {"path": "old.md", "sha256": "b" * 64},
            "runtime_bindings": {"path": "old-runtime.json", "sha256": "c" * 64},
            "source_plan": {"path": "source.json", "sha256": "d" * 64, "bindings_sha256": "e" * 64},
            "resources": {"total_execution_budget_seconds": 300, "working_source_gib": 30},
            "execution_helpers": {
                "scripts/v092_timing_qualified_campaign.py": "1" * 64,
                "scripts/v092_timing_checkpoint.py": "2" * 64,
                "scripts/other.py": "3" * 64,
            },
            "source_execution_helpers": {"scripts/other.py": "3" * 64},
            "helper_transitions": {"scripts/other.py": {"active_sha256": "3" * 64}},
            "group_order": ["finished", "pending"],
            "groups": [
                {"id": "finished", "argv": ["run", "finished"], "environment": {"A": "1"},
                 "deadline_seconds": 100},
                {"id": "pending", "argv": ["run", "pending"], "environment": {"B": "2"},
                 "deadline_seconds": 200},
            ],
        }
        new = copy.deepcopy(parent)
        new.update({
            "campaign_id": "20261122-01", "created_utc": "new", "launch_after_utc": "new",
            "continuation": reference, "continuation_mode": "semantic-quarantine/v1",
            "semantic_mismatch_policy": dict(checkpoint.POLICY),
            "execution_authorization": auth_ref,
            "preregistration": {"path": "new.md", "sha256": "f" * 64},
            "runtime_bindings": {"path": "new-runtime.json", "sha256": "9" * 64},
        })
        new["source_plan"]["bindings_sha256"] = "8" * 64
        new["resources"]["total_execution_budget_seconds"] = 200
        new["execution_helpers"]["scripts/v092_timing_qualified_campaign.py"] = "4" * 64
        new["execution_helpers"]["scripts/v092_timing_segment_checkpoint.py"] = checkpoint.sha(SCRIPT)
        frozen = {"completed_groups": ["finished"], "remaining_ready_groups": ["pending"]}
        return root, parent, new, reference, frozen

    def test_allowed_metadata_delta_and_pending_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, parent, plan, reference, frozen = self._plan_fixture(tmp)
            checkpoint._compare_new_plan(root, parent, plan, reference, frozen)

    def test_command_environment_order_budget_and_policy_drift_fail(self):
        mutations = [
            lambda p: p["groups"][1].update(argv=["different"]),
            lambda p: p["groups"][1].update(environment={"B": "changed"}),
            lambda p: p.update(group_order=list(reversed(p["group_order"]))),
            lambda p: p["resources"].update(total_execution_budget_seconds=201),
            lambda p: p["semantic_mismatch_policy"].update(retry=True),
            lambda p: p["resources"].update(working_source_gib=31),
        ]
        for mutate in mutations:
            with tempfile.TemporaryDirectory() as tmp:
                root, parent, plan, reference, frozen = self._plan_fixture(tmp)
                mutate(plan)
                with self.subTest(mutation=mutate), self.assertRaises(RuntimeError):
                    checkpoint._compare_new_plan(root, parent, plan, reference, frozen)

    def test_authorization_receipt_must_be_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, parent, plan, reference, frozen = self._plan_fixture(tmp)
            auth_path = root / "authorization.json"
            auth = json.loads(auth_path.read_text())
            auth["authorized"] = True
            auth["status"] = "authorized"
            auth_path.write_text(json.dumps(auth, sort_keys=True))
            plan["execution_authorization"]["sha256"] = checkpoint.sha(auth_path)
            checkpoint._compare_new_plan(root, parent, plan, reference, frozen)
            auth["status"] = "pending"
            auth_path.write_text(json.dumps(auth, sort_keys=True))
            plan["execution_authorization"]["sha256"] = checkpoint.sha(auth_path)
            with self.assertRaises(RuntimeError):
                checkpoint._compare_new_plan(root, parent, plan, reference, frozen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
