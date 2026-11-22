#!/usr/bin/env python3
"""Focused standard-library tests for the terminal background handoff seal."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("v092_timing_background_checkpoint.py")
SPEC = importlib.util.spec_from_file_location("v092_timing_background_checkpoint_test", SCRIPT)
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)


def _partition_fixture():
    inherited = [f"inherited-{index}" for index in range(60)]
    remaining = [f"pending-prefix-{index}" for index in range(29)] + checkpoint.PENDING_GROUPS
    parent = {"completed_groups": inherited,
              "quarantined_groups": ["joern-rust-kernel"],
              "remaining_ready_groups": remaining}
    rows = []
    for index, group in enumerate(remaining[:29]):
        rows.extend([
            {"group": group, "status": "started", "utc": f"2026-11-22T00:{index:02d}:00Z"},
            {"group": group, "status": "completed-candidate-evidence", "utc": f"2026-11-22T00:{index:02d}:30Z"},
        ])
    terminal = {
        "campaign_id": checkpoint.CAMPAIGN_ID,
        "status": "superseded-between-commands",
        "execution_status": "handed-off-before-next-command",
        "completed_commands": 29,
        "completed_candidate_groups": remaining[:29],
        "inherited_candidate_commands": 60,
        "inherited_candidate_groups": inherited,
        "combined_completed_candidate_commands": 89,
        "inherited_quarantined_groups": ["joern-rust-kernel"],
        "quarantined_groups": [],
        "combined_quarantined_groups": ["joern-rust-kernel"],
        "remaining_ready_groups": checkpoint.PENDING_GROUPS,
        "paused_before_group": checkpoint.PENDING_GROUPS[0],
        "stopped_group": None,
        "qualification_status": "unqualified",
        "publication_eligible": False,
        "no_active_invocation_at_handoff": True,
        "external_controller_terminal": True,
        "controller_exit_signal": "SIGTERM",
    }
    return parent, rows, terminal


class PartitionTests(unittest.TestCase):
    def test_89_completed_one_quarantined_three_remaining(self):
        parent, rows, terminal = _partition_fixture()
        completed, quarantined, pending = checkpoint._validate_partition(parent, rows, terminal)
        self.assertEqual(len(completed), 89)
        self.assertEqual(quarantined, ["joern-rust-kernel"])
        self.assertEqual(pending, checkpoint.PENDING_GROUPS)

    def test_failure_reordering_and_count_drift_are_rejected(self):
        parent, rows, terminal = _partition_fixture()
        bad_rows = copy.deepcopy(rows)
        bad_rows[3]["status"] = "failed"
        with self.assertRaises(RuntimeError):
            checkpoint._validate_partition(parent, bad_rows, terminal)
        bad_rows = copy.deepcopy(rows)
        bad_rows[0], bad_rows[2] = bad_rows[2], bad_rows[0]
        with self.assertRaises(RuntimeError):
            checkpoint._validate_partition(parent, bad_rows, terminal)
        bad_terminal = copy.deepcopy(terminal)
        bad_terminal["combined_quarantined_groups"] = []
        with self.assertRaises(RuntimeError):
            checkpoint._validate_partition(parent, rows, bad_terminal)


class EvidenceInventoryTests(unittest.TestCase):
    def test_inventory_hashes_and_mutation_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "reports" / "timing" / checkpoint.CAMPAIGN_ID
            work = root / "execution-state" / f"timing-v092-{checkpoint.CAMPAIGN_ID}"
            report.mkdir(parents=True)
            output = work / "sources" / "cold-one" / "reports" / "raw"
            output.mkdir(parents=True)
            (report / "campaign-terminal.json").write_text('{"publication_eligible":false}\n')
            (output / "artifact.json").write_text('{"value":1}\n')
            inventory_path = report / "evidence-inventory-01.json"
            inventory_path.write_text("{}\n")
            seen = checkpoint._v1()._inventory_report(root, report)
            del seen[inventory_path.relative_to(root).as_posix()]
            checkpoint._v1()._inventory_tree(root, output, seen)
            entries = [seen[path] for path in sorted(seen)]
            inventory = {
                "schema": "v092-timing-evidence-inventory/v1",
                "campaign_id": checkpoint.CAMPAIGN_ID,
                "report_root": report.relative_to(root).as_posix(),
                "source_output_groups": ["cold-one"],
                "file_count": len(entries),
                "total_bytes": sum(item["size_bytes"] for item in entries),
                "files": entries,
                "publication_eligible": False,
            }
            inventory_path.write_text(json.dumps(inventory, sort_keys=True) + "\n")
            group = {"id": "cold-one", "output_roots": ["reports/raw"]}
            sealed = checkpoint._inventory(root, report, work, [group], inventory_path)
            self.assertEqual(len(sealed), 3)
            (output / "artifact.json").write_text('{"value":2}\n')
            with self.assertRaises(RuntimeError):
                checkpoint._inventory(root, report, work, [group], inventory_path)

    def test_unsafe_paths_and_symlink_roots_fail_closed(self):
        with self.assertRaises(RuntimeError):
            checkpoint._safe_relative("../escape", "test path")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                checkpoint._v1()._inventory_tree(root, link, {})


class PendingTests(unittest.TestCase):
    def test_only_pysa_quiet_host_receipt_is_allowed_before_frontier(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "reports" / "timing" / checkpoint.CAMPAIGN_ID
            work = root / "execution-state" / f"timing-v092-{checkpoint.CAMPAIGN_ID}"
            attempt = report / "attempts" / checkpoint.PENDING_HOST_ONLY / "attempt-01"
            attempt.mkdir(parents=True)
            (attempt / "host.jsonl").write_text(json.dumps({"status": "ok", "phase": "settle-before-group"}) + "\n")
            groups = [{"id": group, "output_roots": ["reports/out"]} for group in checkpoint.PENDING_GROUPS]
            checkpoint._validate_pending(root, report, work, {"groups": groups}, checkpoint.PENDING_GROUPS, [])
            (attempt / "start.json").write_text("{}\n")
            with self.assertRaises(RuntimeError):
                checkpoint._validate_pending(root, report, work, {"groups": groups}, checkpoint.PENDING_GROUPS, [])


class PlanDeltaTests(unittest.TestCase):
    def _fixture(self, root):
        root = Path(root)
        def write(relative, value):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, sort_keys=True) + "\n")
            return hashlib.sha256(path.read_bytes()).hexdigest()

        policy_sha = write(checkpoint.DISPATCH_POLICY_PATH, checkpoint.DISPATCH_ADMISSION)
        vm = {
            "schema": "v092-tolerated-vm-identity/v1",
            "executable_path": checkpoint.VM_EXECUTABLE,
            "signature_verification_exit_code": 0,
            "signature_description": "Identifier=com.apple.Virtualization.VirtualMachine\nAuthority=Apple Root CA",
        }
        vm_sha = write(checkpoint.VM_IDENTITY_PATH, vm)
        source_sha = write("reports/timing/source-plan.json", {"source": "pinned"})
        continuation_path = "reports/timing/checkpoint.json"
        continuation_sha = write(continuation_path, {"checkpoint": True})
        auth_path = "reports/timing/authorization.json"
        auth_sha = write(auth_path, {
            "schema": checkpoint.AUTH_SCHEMA, "campaign_id": checkpoint.NEW_CAMPAIGN_ID,
            "authorized": False, "status": "pending", "user_request": "explicit permission recorded",
        })
        parent = {
            "campaign_id": checkpoint.CAMPAIGN_ID,
            "created_utc": "parent", "launch_after_utc": "parent",
            "continuation": {"path": "reports/timing/old-checkpoint.json", "sha256": "a" * 64},
            "continuation_mode": "semantic-quarantine/v1",
            "semantic_mismatch_policy": dict(checkpoint.SEMANTIC_POLICY),
            "preregistration": {"path": "old.md", "sha256": "b" * 64},
            "runtime_bindings": {"path": "old-bindings.json", "sha256": "c" * 64},
            "source_plan": {"path": "reports/timing/source-plan.json", "sha256": source_sha,
                            "bindings_sha256": "d" * 64},
            "resources": {"total_execution_budget_seconds": 400, "working_source_gib": 30},
            "execution_helpers": {
                "scripts/v092_timing_qualified_campaign.py": "1" * 64,
                "scripts/v092_timing_checkpoint.py": "2" * 64,
                "scripts/v092_timing_segment_checkpoint.py": "3" * 64,
            },
            "source_execution_helpers": {"scripts/v092_timing_campaign.py": "4" * 64},
            "helper_transitions": {"scripts/v092_timing_campaign.py": {"source_sha256": "5" * 64}},
            "qualification": {
                "evidence_status": "old evidence status", "quiet_window": "old quiet window",
                "quiet_predicate": "old predicate", "note": "frozen qualification note",
                "publication_eligible": False,
            },
            "group_order": ["finished", *checkpoint.PENDING_GROUPS],
            "groups": [
                {"id": "finished", "kind": "cold", "status": "ready", "argv": ["run", "finished"],
                 "environment": {"A": "one"}, "deadline_seconds": 100},
                *[{
                    "id": group, "kind": "ready", "status": "ready", "argv": ["run", group],
                    "environment": {"B": "two"}, "deadline_seconds": 100,
                } for group in checkpoint.PENDING_GROUPS],
            ],
            "tools": {"runner": {"path": "/runner", "sha256": "6" * 64}},
            "runtimes": [{"id": "runtime", "path": "runtime.json", "sha256": "7" * 64,
                          "uncompressed_sha256": None}],
            "source_projection": {"commit": "8" * 40},
            "path_rebindings": {"old": "new"},
            "max_campaign_wall_seconds": 172800,
        }
        new = copy.deepcopy(parent)
        new.update({
            "campaign_id": checkpoint.NEW_CAMPAIGN_ID,
            "created_utc": "new", "launch_after_utc": "new",
            "continuation": {"path": continuation_path, "sha256": continuation_sha},
            "continuation_mode": checkpoint.BACKGROUND_MODE,
            "dispatch_admission": copy.deepcopy(checkpoint.DISPATCH_ADMISSION),
            "execution_authorization": {"path": auth_path, "sha256": auth_sha},
            "preregistration": {"path": "new.md", "sha256": "9" * 64},
            "runtime_bindings": {},
        })
        new["qualification"].update(checkpoint.QUALIFICATION_REPLACEMENTS)
        new["source_plan"]["bindings_sha256"] = "f" * 64
        new["resources"]["total_execution_budget_seconds"] = 300
        new["execution_helpers"]["scripts/v092_timing_qualified_campaign.py"] = "a" * 64
        new["execution_helpers"]["scripts/v092_timing_background_checkpoint.py"] = checkpoint.sha(SCRIPT)
        new["runtime_bindings"] = {
            "path": "reports/timing/20261122-02/runtime-bindings.json",
            "sha256": "0" * 64,
        }
        binding = {
            "campaign_id": checkpoint.NEW_CAMPAIGN_ID,
            "source_plan": {"path": new["source_plan"]["path"], "sha256": new["source_plan"]["sha256"]},
            "tools": new["tools"], "runtimes": new["runtimes"],
            "source_projection": new["source_projection"], "path_rebindings": new["path_rebindings"],
            "group_order": new["group_order"], "max_campaign_wall_seconds": new["max_campaign_wall_seconds"],
            "semantic_mismatch_policy": new["semantic_mismatch_policy"],
            "continuation_mode": new["continuation_mode"], "continuation": new["continuation"],
            "execution_authorization": new["execution_authorization"],
            "dispatch_admission": checkpoint.DISPATCH_ADMISSION,
            "preparation_receipts": [
                {"path": checkpoint.DISPATCH_POLICY_PATH, "sha256": policy_sha},
                {"path": checkpoint.VM_IDENTITY_PATH, "sha256": vm_sha},
            ],
        }
        binding_sha = write(new["runtime_bindings"]["path"], binding)
        new["runtime_bindings"]["sha256"] = binding_sha
        new["source_plan"]["bindings_sha256"] = binding_sha
        frozen = {"remaining_ready_groups": list(checkpoint.PENDING_GROUPS)}
        return parent, new, new["continuation"], frozen

    def test_allowed_background_plan_delta(self):
        with tempfile.TemporaryDirectory() as temp:
            parent, new, reference, frozen = self._fixture(temp)
            checkpoint._compare_new_plan(Path(temp), parent, new, reference, frozen)

    def test_frozen_command_source_policy_and_budget_drift_fail(self):
        mutations = [
            lambda p: p["groups"][1].update(argv=["changed"]),
            lambda p: p["groups"][1].update(environment={"B": "changed"}),
            lambda p: p["groups"][1].update(deadline_seconds=101),
            lambda p: p["source_projection"].update(commit="changed"),
            lambda p: p["resources"].update(total_execution_budget_seconds=301),
            lambda p: p["dispatch_admission"].update(required_settled_seconds=60),
            lambda p: p["semantic_mismatch_policy"].update(retry=True),
            lambda p: p["qualification"].update(note="changed frozen note"),
        ]
        for mutate in mutations:
            with tempfile.TemporaryDirectory() as temp:
                parent, new, reference, frozen = self._fixture(temp)
                mutate(new)
                with self.subTest(mutation=mutate), self.assertRaises(RuntimeError):
                    checkpoint._compare_new_plan(Path(temp), parent, new, reference, frozen)

    def test_authorization_binding_accepts_consistent_pending_or_authorized(self):
        with tempfile.TemporaryDirectory() as temp:
            parent, new, reference, frozen = self._fixture(temp)
            auth = Path(temp) / new["execution_authorization"]["path"]
            value = json.loads(auth.read_text())
            value.update(authorized=True, status="authorized")
            auth.write_text(json.dumps(value, sort_keys=True) + "\n")
            new["execution_authorization"]["sha256"] = checkpoint.sha(auth)
            binding_path = Path(temp) / new["runtime_bindings"]["path"]
            binding = json.loads(binding_path.read_text())
            binding["execution_authorization"] = new["execution_authorization"]
            binding_path.write_text(json.dumps(binding, sort_keys=True) + "\n")
            new["runtime_bindings"]["sha256"] = checkpoint.sha(binding_path)
            new["source_plan"]["bindings_sha256"] = new["runtime_bindings"]["sha256"]
            checkpoint._compare_new_plan(Path(temp), parent, new, reference, frozen)
            value["status"] = "pending"
            auth.write_text(json.dumps(value, sort_keys=True) + "\n")
            new["execution_authorization"]["sha256"] = checkpoint.sha(auth)
            binding["execution_authorization"] = new["execution_authorization"]
            binding_path.write_text(json.dumps(binding, sort_keys=True) + "\n")
            new["runtime_bindings"]["sha256"] = checkpoint.sha(binding_path)
            new["source_plan"]["bindings_sha256"] = new["runtime_bindings"]["sha256"]
            with self.assertRaises(RuntimeError):
                checkpoint._compare_new_plan(Path(temp), parent, new, reference, frozen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
