#!/usr/bin/env python3
"""Focused fixture tests for the one-group Joern Swift supplement controller."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


supplement = load("swift_supplement_test_subject", SCRIPTS / "v092_timing_swift_supplement.py")
raw_report_exporter = load("joern_supplement_raw_exporter_test", SCRIPTS / "joern_normal_reports_v092.py")
projection_exporter = load("joern_supplement_projection_exporter_test",
                           SCRIPTS / "joern_normal_reports_v092_projection.py")


class QualificationPublicationTests(unittest.TestCase):
    def test_actual_v092_receipt_preserves_undeclared_publication_state(self):
        receipt = json.loads((SCRIPTS.parent / supplement.QUALIFICATION_ROOT /
                             "control-attempt-01/qualification-receipt-01.json").read_text())
        before = json.loads(json.dumps(receipt))
        self.assertEqual(supplement._qualification_publication_state(receipt), "not-declared")
        self.assertEqual(receipt, before)
        self.assertEqual(supplement._qualification_publication_state(
            dict(receipt, publication_eligible=False)), "explicitly-disabled")

    def test_qualification_cannot_confer_or_flatten_publication_authority(self):
        for value in (True, None, 0, "false"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                supplement._qualification_publication_state({"publication_eligible": value})


class FakeHost:
    HEAVY = {"semgrep", "codeql", "joern", "swift", "swiftc", "java", "cargo"}

    @staticmethod
    def _valid_snapshot(observation):
        return (isinstance(observation, dict) and observation.get("status") == "ok"
                and isinstance(observation.get("processes"), list)
                and isinstance(observation.get("cpu_idle_percent"), (int, float))
                and isinstance(observation.get("hardware"), dict))

    @classmethod
    def _is_heavy_process(cls, comm):
        return Path(comm).name.lower() in cls.HEAVY


def observation(processes, idle=95.0, timestamp=0.0):
    return {
        "schema_version": 1,
        "status": "ok",
        "observed_at_utc": "2026-11-22T00:00:00Z",
        "monotonic_seconds": timestamp,
        "cpu_idle_percent": idle,
        "processes": processes,
        "uptime": "up 2 days, 1 user",
        "load_average": [0.1, 0.1, 0.1],
        "disk_total_bytes": 200 * 1024**3,
        "disk_used_bytes": 20 * 1024**3,
        "disk_free_bytes": 180 * 1024**3,
        "hardware": {"logical_cpus": 8, "physical_cpus": 4, "memory_bytes": 32 * 1024**3},
    }


def process(pid, comm, cpu=0.0, ppid=1):
    return {"pid": pid, "ppid": ppid, "cpu_percent": cpu, "comm": comm}


def plan_fixture():
    ids = [f"case-{index:03d}" for index in range(108)]
    sizes = [66, 24, 4, 12, 2]
    reports = []
    cursor = 0
    for index, size in enumerate(sizes):
        selected = ids[cursor:cursor + size]
        cursor += size
        reports.append({
            "path": f"reports/releases/v0.9.2/normal/report-{index}.json",
            "source_path": f"reports/raw/joern-common-v2/current108-v092-02/normal/report-{index}.json",
            "case_ids": selected,
        })
    argv = [
        "/usr/bin/python3", "scripts/run-joern-common-v092-relocated.py", "execute", "--plan",
        supplement.QUALIFIED_PLAN_PATH, "--output", supplement.OUTPUT_ARGUMENT,
    ]
    env = {
        "HOME": "@SUPPLEMENT_SOURCE@/home", "TMPDIR": "@SUPPLEMENT_SOURCE@/tmp",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1", "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
        "DATAFLOWBENCH_V092_GROUP_ID": supplement.GROUP_ID,
    }
    group = {
        "id": supplement.GROUP_ID, "family": "joern", "kind": "cold", "status": "ready",
        "argv": argv, "maximum_attempts": 1, "automatic_retry": False,
        "output_roots": [supplement.OUTPUT_RELATIVE],
        "runtime_ids": ["java-home", "joern-root", "swift-sdk", "swift-toolchain"],
        "case_ids": ids, "reports": reports, "environment": env,
    }
    root = str(supplement.ROOT)
    baseline_paths = {
        "working": [f"{root}/execution-state/timing-v092-{campaign_id}/sources"
                    for campaign_id in supplement.RESOURCE_CAMPAIGN_IDS],
        "retention": [f"{root}/reports/timing/v0.9.2/parent"],
        "scratch": [f"{root}/execution-state/timing-v092-{supplement.RESOURCE_CAMPAIGN_IDS[0]}"
                    "/sources/sample/tmp"],
    }
    preparation_paths = {
        "working": [f"{root}/{supplement.PORTABILITY_SOURCE_PATH}",
                    f"{root}/{supplement.QUALIFICATION_WORK_ROOT}"],
        "retention": [f"{root}/{supplement.PREPARATION_ROOT}"],
        "scratch": [f"{root}/{supplement.QUALIFICATION_CONTROL_SCRATCH}",
                    *[f"{root}/{supplement.QUALIFICATION_WORK_ROOT}/{name}"
                      for name in ("home", "tmp", "cache")]],
    }
    active_paths = {
        "working": [f"{root}/{supplement.SOURCE_RELATIVE}"],
        "retention": [f"{root}/{supplement.REPORT_ROOT}", f"{root}/{supplement.SOURCE_RELATIVE}/reports"],
        "scratch": [f"{root}/{supplement.SOURCE_RELATIVE}/{name}"
                    for name in ("home", "tmp", "cache")],
    }
    all_paths = {
        "working": [*baseline_paths["working"], *preparation_paths["working"], *active_paths["working"]],
        "retention": [*baseline_paths["retention"], *preparation_paths["retention"], *active_paths["retention"]],
        "scratch": [*baseline_paths["scratch"], *preparation_paths["scratch"], *active_paths["scratch"]],
    }
    return {
        "schema": "v092-timing-swift-supplement-plan/v1",
        "campaign_id": supplement.CAMPAIGN_ID, "group_id": supplement.GROUP_ID,
        "dispatch_groups": [supplement.GROUP_ID], "attempts_per_group": {supplement.GROUP_ID: 1},
        "parent_ready_frontier": [], "parent_group_count": 95,
        "case_count": 108, "report_partition_count": 5,
        "case_disposition_counts": {"attempt": 96, "unsupported": 12},
        "attempted_case_count": 96, "unsupported_case_count": 12,
        "diagnostic_execution_eligible": True, "full_model_qualification": False,
        "old_argv": [
            "/usr/bin/python3", "scripts/run-joern-common-v092.py", "execute", "--plan",
            "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json", "--output",
            "reports/raw/joern-common-v2/current108-v092-01",
        ],
        "argv": argv, "group": group, "environment": env,
        "qualified_execution_plan": {"path": supplement.QUALIFIED_PLAN_PATH, "sha256": "d" * 64},
        "pending_execution_plan": {"path": supplement.PENDING_PLAN_PATH, "sha256": "e" * 64},
        "source_projection": {
            "source_path": supplement.SOURCE_RELATIVE,
            "additional_paths": [supplement.QUALIFIED_PLAN_PATH, supplement.PENDING_PLAN_PATH],
            "execution_plan_inputs": [
                {"path": supplement.QUALIFIED_PLAN_PATH, "sha256": "d" * 64},
                {"path": supplement.PENDING_PLAN_PATH, "sha256": "e" * 64},
            ],
            "supplement_files_to_copy": [],
        },
        "deadline_seconds": 1368, "max_campaign_wall_seconds": 48 * 60 * 60,
        "resources": {
            "launch_free_gib": 127, "continuous_free_gib": 125,
            "per_source_gib": 12, "working_source_gib": 30,
            "scratch_gib": 24, "retention_gib": 24,
            "serial_analyzers": 1, "automatic_retry": False,
        },
        "resource_scope": {
            "resource_campaign_ids": list(supplement.RESOURCE_CAMPAIGN_IDS),
            "campaign_start_references": [
                {"path": f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json",
                 "sha256": "f" * 64}
                for campaign_id in supplement.RESOURCE_CAMPAIGN_IDS
            ],
            "parent_checkpoint": {
                "path": supplement.RESOURCE_PARENT_CHECKPOINT_PATH,
                "sha256": supplement.RESOURCE_PARENT_CHECKPOINT_SHA256,
            },
            "observer_profile": {"path": supplement.RESOURCE_PROFILE_PATH,
                                 "sha256": supplement.RESOURCE_PROFILE_SHA256},
            "closed_process_ownership": {"path": supplement.RESOURCE_OWNER_RECEIPT_PATH,
                                         "sha256": supplement.RESOURCE_OWNER_RECEIPT_SHA256},
            "closed_process_ownership_state": {
                "recorded_process_identities": 118, "same_identities_still_alive": 0,
                "command_records": 37, "serial_lock_available": True,
                "descendant_containment": "unproven",
            },
            "portability_preflight": {"path": supplement.PORTABILITY_RECEIPT_PATH,
                                       "sha256": supplement.PORTABILITY_RECEIPT_SHA256},
            "observer_method": supplement.RESOURCE_OBSERVER_METHOD,
            "profile_expected_parent_baseline_bytes": {
                "working": 19073573545, "retention": 630366349,
                "scratch": 3198936017,
            },
            "post_profile_retained_additions": [dict(row) for row in supplement.POST_PROFILE_RETAINED_ADDITIONS],
            "expected_parent_baseline_bytes": {
                "working": 19073573545, "retention": 630367193, "scratch": 3198936017,
            },
            "inherited_source_roots": [
                f"{supplement.ROOT}/execution-state/timing-v092-{campaign_id}/sources"
                for campaign_id in supplement.RESOURCE_CAMPAIGN_IDS
            ],
            "baseline_paths": baseline_paths, "preparation_paths": preparation_paths,
            "active_paths": active_paths,
            "retained": all_paths["retention"], "working": all_paths["working"],
            "scratch": all_paths["scratch"],
        },
        "publication_eligible": False, "scored_activation": False,
        "original_a24_settled_qualification_eligible": False,
        "active_cpu_policy": "record-and-continue", "retry_policy": "none",
        "admission_policy": {
            "schema": "v092-swift-supplement-background-admission/v1",
            "required_complete_quiet_seconds": 300,
            "aggregate_cpu_idle_percent_minimum": 90.0,
            "maximum_sample_gap_seconds": 45.0,
            "maximum_final_sample_to_spawn_seconds": 45.0,
            "sample_interval_seconds": 30.0,
            "tolerated_comm_paths": list(supplement.TOLERATED_COMM_PATHS),
            "matching": "exact-full-comm-path-only",
            "aggregate_cpu_adjusted": False,
            "active_cpu_policy": "record-and-continue",
            "missing_active_observation_policy": "record-and-continue",
            "original_a24_settled_qualification_eligible": False,
        },
        "configuration_provenance": {
            "schema": "v092-swift-supplement-configuration-provenance/v1",
            "removed_paths": [],
            "approved_additions": sorted(supplement.APPROVED_CONFIGURATION_ADDITIONS),
            "publication_eligible": False,
        },
        "semantic_uncertainty": {
            "schema": "joern-swift-semantic-uncertainty/v1",
            "decision_id": supplement.MODEL_LIMIT_DECISION_ID,
            "classification": "strict-model-qualification-incomplete",
            "strict_model_qualification": {"status": "incomplete", "full_model_qualification": False},
            "diagnostic_execution": {"status": "measurement-with-known-limits", "scored_activation": False},
            "normalized_report_match_is_model_certificate": False,
            "publication_eligible": False,
        },
    }


class SwiftSupplementPlanTests(unittest.TestCase):
    def test_exact_single_group_plan_is_accepted(self):
        supplement.validate_campaign_plan(plan_fixture())

    def test_dispatch_cannot_add_a_second_group(self):
        plan = plan_fixture()
        plan["dispatch_groups"].append("codeql-swift-common108")
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            supplement.validate_campaign_plan(plan)

    def test_attempt_count_cannot_allow_retries(self):
        plan = plan_fixture()
        plan["attempts_per_group"][supplement.GROUP_ID] = 2
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            supplement.validate_campaign_plan(plan)

    def test_actual_argv_must_use_relocated_wrapper_and_fresh_plan(self):
        plan = plan_fixture()
        plan["argv"][1] = "scripts/run-joern-common-v092.py"
        plan["group"]["argv"] = list(plan["argv"])
        with self.assertRaisesRegex(RuntimeError, "actual argv"):
            supplement.validate_campaign_plan(plan)

    def test_report_partition_near_miss_is_rejected(self):
        plan = plan_fixture()
        plan["group"]["reports"].pop()
        with self.assertRaisesRegex(RuntimeError, "five report partitions"):
            supplement.validate_campaign_plan(plan)

    def test_historical_and_new_argv_cannot_be_collapsed(self):
        plan = plan_fixture()
        plan["old_argv"] = list(plan["argv"])
        with self.assertRaisesRegex(RuntimeError, "historical and actual"):
            supplement.validate_campaign_plan(plan)

    def test_timing_population_rejects_wrong_executed_denominator(self):
        plan = plan_fixture()
        plan["attempted_case_count"] = 108
        with self.assertRaisesRegex(RuntimeError, "96 attempted cases"):
            supplement.validate_campaign_plan(plan)

    def test_resource_scope_requires_all_four_ancestor_namespaces(self):
        plan = plan_fixture()
        plan["resource_scope"]["resource_campaign_ids"].pop()
        with self.assertRaisesRegex(RuntimeError, "all four ancestor"):
            supplement.validate_campaign_plan(plan)


def make_resource_scope_fixture(root: Path, *, omit_parent_scratch=False):
    campaign_ids = list(supplement.RESOURCE_CAMPAIGN_IDS)
    roots = [root / f"execution-state/timing-v092-{campaign_id}/sources"
             for campaign_id in campaign_ids]
    scratch = [path / "sample" / "tmp" for path in roots]
    for index, campaign_id in enumerate(campaign_ids):
        relative = f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"campaign_id": campaign_id,
                                    "scratch_roots": [str(item) for item in scratch[:index + 1]]}) + "\n")

    checkpoint_path = root / supplement.RESOURCE_PARENT_CHECKPOINT_PATH
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps({
        "schema": "v092-timing-background-checkpoint/v1",
        "parent_campaign_id": "20261122-01",
        "resource_campaign_ids": campaign_ids[:-1],
    }) + "\n")
    checkpoint_sha = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    parent_path = root / f"reports/timing/v0.9.2/20261122-02/campaign-start.json"
    parent = json.loads(parent_path.read_text())
    parent["continuation_checkpoint"] = {
        "path": supplement.RESOURCE_PARENT_CHECKPOINT_PATH, "sha256": checkpoint_sha,
    }
    parent["cumulative_resource_scope"] = {
        "working": [str(path) for path in reversed(roots)],
        "retained": ["reports/timing/v0.9.2/20261122-02"],
    }
    parent["scratch_roots"] = [str(path) for path in (scratch[:-1] if omit_parent_scratch else scratch)]
    parent_path.write_text(json.dumps(parent) + "\n")

    inherited_retained = [root / "reports/timing/v0.9.2" / campaign_id for campaign_id in campaign_ids]
    static_retained = {
        Path("reports/timing/v0.9.2/20261122-02"),
        *(path.relative_to(root) for path in inherited_retained),
        Path("reports/timing/v0.9.2/reconciliation-20261122-01"),
        Path("reports/timing/v0.9.2/preparation-20261122-swift-01"),
        Path("reports/timing/v0.9.2/preparation-20261122-codeql-swift-01"),
    }
    static_paths = {
        "working": [str(path) for path in roots],
        "retention": [str(root / path) for path in sorted(static_retained)],
        "scratch": [str(path) for path in scratch],
    }
    preparation_paths = {
        "working": [str(root / supplement.PORTABILITY_SOURCE_PATH),
                    str(root / supplement.QUALIFICATION_WORK_ROOT)],
        "retention": [str(root / supplement.PREPARATION_ROOT)],
        "scratch": [str(root / supplement.QUALIFICATION_CONTROL_SCRATCH),
                    *[str(root / supplement.QUALIFICATION_WORK_ROOT / name)
                      for name in ("home", "tmp", "cache")]],
    }
    profile = {
        "schema": "v092-resource-observer-profile/v1",
        "scope": "untimed guard profile only; no analyzer or performance corpus measurement",
        "accounted_totals_equal": True, "limits_unchanged": True,
        "baseline_materialization_outside_profile_and_timed_window": True,
        "static_paths": static_paths, "active_proxy_paths": preparation_paths,
        "results": [
            {"mode": "full-ancestor-rescan", "checks": {
                category: {"current_bytes": 1000 + index} for index, category in enumerate(
                    ("working", "retention", "scratch"))}},
            {"mode": "immutable-baseline-plus-active-rescan",
             "baseline_bytes": {"working": 19073573545, "retention": 630366349,
                                "scratch": 3198936017},
             "checks": {category: {"current_bytes": 1000 + index} for index, category in enumerate(
                 ("working", "retention", "scratch"))}},
        ],
    }
    profile_path = root / supplement.RESOURCE_PROFILE_PATH
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile) + "\n")
    addition_path = root / supplement.POST_PROFILE_RETAINED_ADDITIONS[0]["path"]
    addition_path.parent.mkdir(parents=True, exist_ok=True)
    addition_bytes = b"x" * 844
    addition_path.write_bytes(addition_bytes)
    additions = ({"path": supplement.POST_PROFILE_RETAINED_ADDITIONS[0]["path"],
                  "sha256": hashlib.sha256(addition_bytes).hexdigest(),
                  "size_bytes": len(addition_bytes)},)
    owner = {
        "schema": "v092-joern-post-control-ownership/v1",
        "recorded_process_identities": 118, "command_records": 37,
        "same_identities_still_alive": [], "signals_sent_by_audit": [],
        "serial_lock_available": True, "descendant_containment": "unproven",
    }
    owner_path = root / supplement.RESOURCE_OWNER_RECEIPT_PATH
    owner_path.write_text(json.dumps(owner) + "\n")
    portability_input_refs = {}
    for index in range(49):
        relative = f"fixture/portability-ref-{index:02d}.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"ref-{index}\n")
        portability_input_refs[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    portability = {
        "schema": "v092-joern-prepared-source-portability-preflight/v1",
        "status": "passed", "exit_code": 0, "analyzer_invocations": 0,
        "source_commit": supplement.RELEASE,
        "source": str(root / supplement.PORTABILITY_SOURCE_PATH), "input_refs": portability_input_refs,
    }
    portability_path = root / supplement.PORTABILITY_RECEIPT_PATH
    portability_path.write_text(json.dumps(portability) + "\n")

    start_refs = []
    for campaign_id in campaign_ids:
        relative = f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        path = root / relative
        start_refs.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    def inherited(context):
        return roots, inherited_retained, scratch

    fake_q = type("FakeQualified", (), {"_inherited_resource_paths": staticmethod(inherited)})()
    return {
        "roots": roots, "scratch": scratch, "start_refs": start_refs,
        "checkpoint_sha": checkpoint_sha, "profile_sha": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        "post_profile_additions": additions,
        "owner_sha": hashlib.sha256(owner_path.read_bytes()).hexdigest(),
        "portability_sha": hashlib.sha256(portability_path.read_bytes()).hexdigest(),
        "fake_q": fake_q,
    }


class SwiftSupplementResourceScopeTests(unittest.TestCase):
    def test_resource_scope_uses_combined_ancestor_context_and_binds_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            fixture = make_resource_scope_fixture(root)
            with patch.object(supplement, "_qualified_module", return_value=fixture["fake_q"]), \
                    patch.object(supplement, "RESOURCE_PARENT_CHECKPOINT_SHA256", fixture["checkpoint_sha"]), \
                    patch.object(supplement, "POST_PROFILE_RETAINED_ADDITIONS", fixture["post_profile_additions"]), \
                    patch.object(supplement, "RESOURCE_PROFILE_SHA256", fixture["profile_sha"]), \
                    patch.object(supplement, "RESOURCE_OWNER_RECEIPT_SHA256", fixture["owner_sha"]), \
                    patch.object(supplement, "PORTABILITY_RECEIPT_SHA256", fixture["portability_sha"]):
                result = supplement._resource_scope(root)

            self.assertEqual(result["resource_campaign_ids"], list(supplement.RESOURCE_CAMPAIGN_IDS))
            self.assertEqual(result["campaign_start_references"], fixture["start_refs"])
            self.assertEqual(result["parent_checkpoint"]["sha256"], fixture["checkpoint_sha"])
            self.assertEqual(result["inherited_source_roots"], [str(path) for path in fixture["roots"]])
            self.assertEqual(result["observer_profile"]["sha256"], fixture["profile_sha"])
            self.assertEqual(result["post_profile_retained_additions"],
                             list(fixture["post_profile_additions"]))
            self.assertEqual(result["expected_parent_baseline_bytes"]["retention"], 630367193)
            self.assertEqual(result["closed_process_ownership"]["sha256"], fixture["owner_sha"])
            self.assertEqual(result["closed_process_ownership_state"]["descendant_containment"], "unproven")
            self.assertEqual(result["portability_preflight"]["sha256"], fixture["portability_sha"])
            self.assertEqual(result["active_paths"]["working"], [str(root / supplement.SOURCE_RELATIVE)])
            self.assertTrue(set(str(path) for path in fixture["roots"])
                            <= set(result["baseline_paths"]["working"]))

    def test_resource_scope_rejects_parent_missing_one_ancestor_scratch_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            fixture = make_resource_scope_fixture(root, omit_parent_scratch=True)
            with patch.object(supplement, "_qualified_module", return_value=fixture["fake_q"]), \
                    patch.object(supplement, "RESOURCE_PARENT_CHECKPOINT_SHA256", fixture["checkpoint_sha"]), \
                    patch.object(supplement, "POST_PROFILE_RETAINED_ADDITIONS", fixture["post_profile_additions"]), \
                    patch.object(supplement, "RESOURCE_PROFILE_SHA256", fixture["profile_sha"]), \
                    patch.object(supplement, "RESOURCE_OWNER_RECEIPT_SHA256", fixture["owner_sha"]), \
                    patch.object(supplement, "PORTABILITY_RECEIPT_SHA256", fixture["portability_sha"]):
                with self.assertRaisesRegex(RuntimeError, "scratch scope differs"):
                    supplement._resource_scope(root)

    def test_resource_scope_rejects_live_path_overlap_with_immutable_baseline(self):
        with self.assertRaisesRegex(RuntimeError, "overlap"):
            supplement._assert_disjoint_resource_paths(
                [Path("/tmp/parent/root")], [Path("/tmp/parent/root/new"),], "working")

    def test_initial_full_counts_equal_profile_parent_plus_fresh_preparation_and_live(self):
        scope = supplement._safe_accounting_scope(supplement.ROOT, plan_fixture())
        fake_disk = FakeBaselineDisk(scope)
        with patch.object(supplement, "_validate_reference", return_value=Path("/tmp/bound")), \
                patch.object(supplement, "_verify_post_profile_retained_additions",
                             return_value=[dict(row) for row in supplement.POST_PROFILE_RETAINED_ADDITIONS]), \
                patch.object(supplement, "_verify_parent_capture_inventory", return_value={"all_files_verified": True}):
            record = supplement._measure_resource_baseline(supplement.ROOT, scope, fake_disk)
        self.assertTrue(record["initial_full_equals_baseline_plus_live"])
        self.assertEqual(record["measured_parent_baseline_bytes"], scope["expected_parent_baseline_bytes"])
        self.assertEqual(record["combined_static_baseline_bytes"], {
            category: scope["expected_parent_baseline_bytes"][category]
            + fake_disk.preparation_bytes[category]
            for category in ("working", "retention", "scratch")
        })

    def test_initial_full_count_nearmiss_stops_before_any_timing(self):
        scope = supplement._safe_accounting_scope(supplement.ROOT, plan_fixture())
        fake_disk = FakeBaselineDisk(scope, bad_full_category="retention")
        with patch.object(supplement, "_validate_reference", return_value=Path("/tmp/bound")), \
                patch.object(supplement, "_verify_post_profile_retained_additions",
                             return_value=[dict(row) for row in supplement.POST_PROFILE_RETAINED_ADDITIONS]), \
                patch.object(supplement, "_verify_parent_capture_inventory", return_value={"all_files_verified": True}):
            with self.assertRaisesRegex(RuntimeError, "initial full retention count"):
                supplement._measure_resource_baseline(supplement.ROOT, scope, fake_disk)

    def test_post_command_parent_byte_change_is_not_certified(self):
        scope = supplement._safe_accounting_scope(supplement.ROOT, plan_fixture())
        fake_disk = FakeBaselineDisk(scope)
        with patch.object(supplement, "_validate_reference", return_value=Path("/tmp/bound")), \
                patch.object(supplement, "_verify_post_profile_retained_additions",
                             return_value=[dict(row) for row in supplement.POST_PROFILE_RETAINED_ADDITIONS]), \
                patch.object(supplement, "_verify_parent_capture_inventory", return_value={"all_files_verified": True}):
            record = supplement._measure_resource_baseline(supplement.ROOT, scope, fake_disk)
        fake_disk.parent_bytes["working"] += 1
        with self.assertRaisesRegex(RuntimeError, "parent resource baseline changed"):
            supplement._verify_resource_baseline_unchanged(scope, record, fake_disk)

    def test_post_profile_addition_is_exactly_hash_and_size_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            relative = supplement.POST_PROFILE_RETAINED_ADDITIONS[0]["path"]
            path = root / relative
            path.parent.mkdir(parents=True)
            raw = b"closed receipt fixture"
            path.write_bytes(raw)
            binding = ({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                        "size_bytes": len(raw)},)
            with patch.object(supplement, "POST_PROFILE_RETAINED_ADDITIONS", binding):
                self.assertEqual(
                    supplement._verify_post_profile_retained_additions(root, list(binding)),
                    list(binding))
                path.write_bytes(b"closed receipt changed")
                with self.assertRaisesRegex(RuntimeError, "changed"):
                    supplement._verify_post_profile_retained_additions(root, list(binding))

    def test_working_guard_reuses_active_source_count_for_per_source_limit(self):
        scope = supplement._safe_accounting_scope(supplement.ROOT, plan_fixture())
        baseline = {category: 1000 for category in ("working", "retention", "scratch")}
        fake_delegate = FakeBaselineDisk(scope)
        fake_delegate.result_current_bytes = {"working": baseline["working"] + 2048}
        guard = supplement._SupplementDiskGuard(fake_delegate, supplement.ROOT / supplement.SOURCE_RELATIVE,
                                                lambda: None, scope)
        guard.bind_baseline({"schema": "v092-swift-resource-baseline/v1",
                             "initial_full_equals_baseline_plus_live": True,
                             "combined_static_baseline_bytes": baseline})
        result = guard.check(category="working", paths=scope["all"]["working"], capacity_path=supplement.ROOT)
        self.assertEqual(result["current_bytes"], baseline["working"] + 2048)
        self.assertEqual(fake_delegate.last_kwargs["paths"], scope["active"]["working"])
        self.assertEqual(fake_delegate.last_kwargs["additional_current_bytes"], baseline["working"])

    def test_working_guard_stops_when_reused_source_count_exceeds_12_gib(self):
        scope = supplement._safe_accounting_scope(supplement.ROOT, plan_fixture())
        baseline = {category: 1000 for category in ("working", "retention", "scratch")}
        fake_delegate = FakeBaselineDisk(scope)
        fake_delegate.result_current_bytes = {"working": baseline["working"] + 12 * 1024**3 + 1}
        guard = supplement._SupplementDiskGuard(fake_delegate, supplement.ROOT / supplement.SOURCE_RELATIVE,
                                                lambda: None, scope)
        guard.bind_baseline({"schema": "v092-swift-resource-baseline/v1",
                             "initial_full_equals_baseline_plus_live": True,
                             "combined_static_baseline_bytes": baseline})
        class FakeDiskGuardError(RuntimeError):
            def __init__(self, code, message, **_metadata):
                self.code = code
                super().__init__(message)

        fake_q = type("FakeQ", (), {"legacy": type("Legacy", (), {
            "disk": type("Disk", (), {"DiskGuardError": FakeDiskGuardError})(),
        })()})()
        with patch.object(supplement, "_qualified_module", return_value=fake_q):
            with self.assertRaisesRegex(RuntimeError, "12 GiB ceiling"):
                guard.check(category="working", paths=scope["all"]["working"], capacity_path=supplement.ROOT)

    def test_all_category_live_growth_remains_inside_existing_ceilings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            parent, preparation, active = {}, {}, {}
            all_paths = {}
            expected_baseline = {}
            for index, category in enumerate(("working", "retention", "scratch")):
                parent[category] = root / category / "parent"
                preparation[category] = root / category / "preparation"
                active[category] = root / category / "active"
                for path in (parent[category], preparation[category], active[category]):
                    path.mkdir(parents=True, exist_ok=True)
                (parent[category] / "p.bin").write_bytes(b"p" * 10)
                (preparation[category] / "prep.bin").write_bytes(b"q" * 5)
                (active[category] / "live.bin").write_bytes(b"l" * 4)
                expected_baseline[category] = 15
                all_paths[category] = [parent[category], preparation[category], active[category]]
            scope = {"all": all_paths, "active": {key: [value] for key, value in active.items()}}
            delegate = supplement._qualified_module(supplement.ROOT).legacy.disk.DiskGuard(
                working_ceiling_bytes=20, retention_ceiling_bytes=20, scratch_ceiling_bytes=20,
                launch_floor_bytes=0, stop_floor_bytes=0,
                protected_reserve_bytes=0, stop_margin_bytes=0,
                disk_usage=lambda _path: 1024**4,
            )
            guard = supplement._SupplementDiskGuard(delegate, active["working"], lambda: None, scope)
            guard.bind_baseline({
                "schema": "v092-swift-resource-baseline/v1",
                "initial_full_equals_baseline_plus_live": True,
                "combined_static_baseline_bytes": expected_baseline,
            })
            for category in ("working", "retention", "scratch"):
                result = guard.check(category=category, paths=all_paths[category], capacity_path=root)
                self.assertEqual(result["current_bytes"], 19)
                (active[category] / "growth.bin").write_bytes(b"x" * 2)
                with self.assertRaisesRegex(RuntimeError, "exceeds its configured ceiling"):
                    guard.check(category=category, paths=all_paths[category], capacity_path=root)


class FakeBaselineDisk:
    def __init__(self, scope, *, bad_full_category=None):
        self.scope = scope
        self.parent_bytes = dict(scope["expected_parent_baseline_bytes"])
        self.preparation_bytes = {"working": 100, "retention": 200, "scratch": 300}
        self.active_bytes = {"working": 1000, "retention": 2000, "scratch": 3000}
        self.bad_full_category = bad_full_category
        self.last_kwargs = None
        self.result_current_bytes = {}

    def logical_size(self, paths):
        selected = {str(path) for path in paths}
        for category in ("working", "retention", "scratch"):
            parent = {str(path) for path in self.scope["parent"][category]}
            preparation = {str(path) for path in self.scope["preparation"][category]}
            active = {str(path) for path in self.scope["active"][category]}
            if selected == parent:
                return self.parent_bytes[category]
            if selected == preparation:
                return self.preparation_bytes[category]
            if selected == active:
                return self.active_bytes[category]
            if selected == parent | preparation:
                return self.parent_bytes[category] + self.preparation_bytes[category]
            if selected == parent | preparation | active:
                total = self.parent_bytes[category] + self.preparation_bytes[category] + self.active_bytes[category]
                return total + (1 if category == self.bad_full_category else 0)
        raise AssertionError(f"unexpected resource path set: {selected}")

    def check(self, **kwargs):
        self.last_kwargs = kwargs
        category = kwargs["category"]
        if category == "working":
            return {"current_bytes": self.result_current_bytes.get(
                category, kwargs.get("additional_current_bytes", 0) + 1)}
        return {"current_bytes": kwargs.get("additional_current_bytes", 0)}


class SwiftSupplementAdmissionTests(unittest.TestCase):
    def test_exact_tolerated_apple_paths_do_not_adjust_raw_cpu(self):
        path = supplement.TOLERATED_COMM_PATHS[-2]
        sample = observation([process(101, path, cpu=120.0)])
        before = json.dumps(sample, sort_keys=True)
        assessment = supplement.assess_admission(sample, FakeHost())
        self.assertTrue(assessment["quiet"])
        self.assertEqual(assessment["non_tolerated_external_cpu_percent"], 0.0)
        self.assertEqual(sample["cpu_idle_percent"], 95.0)
        self.assertEqual(json.dumps(sample, sort_keys=True), before)
        self.assertFalse(assessment["aggregate_cpu_adjusted"])

    def test_service_basename_or_prefix_is_not_tolerated(self):
        near_miss = "/private/tmp/spotlightknowledged.updater"
        sample = observation([process(102, near_miss, cpu=100.0)])
        assessment = supplement.assess_admission(sample, FakeHost())
        self.assertFalse(assessment["quiet"])
        self.assertEqual(assessment["tolerated_background"], [])
        self.assertEqual(assessment["non_tolerated_external_cpu_percent"], 100.0)

    def test_analyzer_path_is_never_allowed_by_service_prefix(self):
        sample = observation([process(103, "/opt/tools/semgrep", cpu=0.1)])
        assessment = supplement.assess_admission(sample, FakeHost())
        self.assertFalse(assessment["quiet"])
        self.assertEqual(assessment["non_tolerated_heavy_processes"][0]["comm"], "/opt/tools/semgrep")

    def test_settled_window_requires_full_span_and_resets_on_bad_samples(self):
        window = supplement.QuietAdmissionWindow(required_seconds=300, max_gap_seconds=45)
        quiet = {"quiet": True}
        self.assertFalse(window.observe(quiet, 0.0))
        for second in range(30, 301, 30):
            complete = window.observe(quiet, float(second))
        self.assertTrue(complete)
        self.assertEqual(window.samples, 11)
        self.assertFalse(window.observe({"quiet": False}, 330.0))
        self.assertFalse(window.observe(quiet, 360.0))
        self.assertFalse(window.observe(quiet, 420.0))  # gap >45 resets before starting again
        self.assertEqual(window.elapsed_seconds, 0.0)


class SwiftSupplementDispatchTests(unittest.TestCase):
    class FakePopenModule:
        def __init__(self):
            self.calls = []

        def Popen(self, command, *args, **kwargs):
            self.calls.append((command, args, kwargs))
            return "child"

    def test_spawn_guard_accepts_exact_45_second_boundary(self):
        module = self.FakePopenModule()
        argv = ["/usr/bin/python3", "runner.py", "execute"]
        cwd = Path("/private/tmp/source")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"

            def process_runner():
                self.assertFalse(output.exists())
                return module.Popen(argv, cwd=cwd)

            with patch.object(supplement.time, "monotonic", return_value=45.0):
                result, evidence = supplement._run_process_with_fresh_admission(
                    process_runner, module, argv, cwd, output, 0.0)
        self.assertEqual(result, "child")
        self.assertEqual(evidence["sample_age_seconds_at_popen"], 45.0)
        self.assertEqual(len(module.calls), 1)
        self.assertIs(module.Popen.__func__, self.FakePopenModule.Popen)

    def test_spawn_guard_refuses_stale_window_before_child_creation(self):
        module = self.FakePopenModule()
        argv = ["/usr/bin/python3", "runner.py", "execute"]
        cwd = Path("/private/tmp/source")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"

            def process_runner():
                self.assertFalse(output.exists())
                return module.Popen(argv, cwd=cwd)

            with patch.object(supplement.time, "monotonic", return_value=45.001):
                with self.assertRaises(supplement._AdmissionWindowExpired) as caught:
                    supplement._run_process_with_fresh_admission(
                        process_runner, module, argv, cwd, output, 0.0)
        self.assertEqual(caught.exception.age_seconds, 45.001)
        self.assertEqual(module.calls, [])
        self.assertIs(module.Popen.__func__, self.FakePopenModule.Popen)

    def test_spawn_guard_does_not_treat_auxiliary_process_as_analyzer_dispatch(self):
        module = self.FakePopenModule()
        argv = ["/usr/bin/python3", "runner.py", "execute"]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"

            def process_runner():
                self.assertFalse(output.exists())
                return module.Popen(["/bin/ps", "-axo", "pid"], cwd="/private/tmp/source")

            with patch.object(supplement.time, "monotonic", return_value=1000.0):
                result, evidence = supplement._run_process_with_fresh_admission(
                    process_runner, module, argv, Path("/private/tmp/source"), output, 0.0)
        self.assertEqual(result, "child")
        self.assertEqual(evidence, {})
        self.assertEqual(len(module.calls), 1)

    def test_output_path_must_be_fresh_and_inside_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp).resolve()
            output = supplement._fresh_output_path(source)
            self.assertEqual(output, source / supplement.OUTPUT_RELATIVE)
            output.parent.mkdir(parents=True)
            output.mkdir()
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                supplement._fresh_output_path(source)

    def test_output_path_rejects_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "reports").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "escapes|symlink"):
                supplement._fresh_output_path(source)


class SwiftSupplementClosureTests(unittest.TestCase):
    def _configuration_fixture(self, root):
        old_rows = []
        for index in range(33):
            relative = f"fixture/config-{index:02d}.json"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"config-{index}\n")
            old_rows.append({"path": relative,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        old_plan = {"configurations": {"joern-current108": old_rows}}
        old_path = root / supplement.V01_EXECUTION_PLAN_PATH
        old_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.write_text(json.dumps(old_plan, sort_keys=True) + "\n")
        addition_rows = []
        for index, relative in enumerate(supplement.APPROVED_CONFIGURATION_ADDITIONS):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative != supplement.V01_EXECUTION_PLAN_PATH:
                path.write_text(f"approved-addition-{index}\n")
            addition_rows.append({"path": relative,
                                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        qualified = {"configurations": {"joern-current108": old_rows + addition_rows}}
        old_hash, _ = supplement._configuration_hash(root, old_plan)
        base = {"frozen_report_bindings": {supplement.GROUP_ID: [
            {"identity": {"configuration_hash": old_hash}} for _ in range(5)
        ]}}
        return old_plan, qualified, base, old_rows, addition_rows

    def test_configuration_transition_requires_exact_33_plus_11_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _old_plan, qualified, base, old_rows, additions = self._configuration_fixture(root)
            result = supplement._configuration_provenance(root, qualified, base)
            self.assertEqual(result["retained_historical_paths_byte_identical"],
                             sorted(row["path"] for row in old_rows))
            self.assertEqual(result["approved_additions"], sorted(row["path"] for row in additions))
            reordered = json.loads(json.dumps(qualified))
            reordered["configurations"]["joern-current108"] = old_rows + list(reversed(additions))
            with self.assertRaisesRegex(RuntimeError, "exact old 33 rows"):
                supplement._configuration_provenance(root, reordered, base)

    def test_closure_keeps_new_cpg_proof_and_required_old_summary_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def write_json(relative, value):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                raw = json.dumps(value, sort_keys=True).encode() + b"\n"
                path.write_bytes(raw)
                return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}

            def write_bytes(relative, raw=b"capture"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}

            old_cpg = write_bytes("reports/releases/v0.9.2/qualification/old-capture/cpg.bin")
            old_receipt = write_json("reports/releases/v0.9.2/qualification/old-capture/receipt.json",
                                     {"raw_cpg": old_cpg})
            old_config = write_json("adapters/joern/swift-common-v2/models.json", {"models": []})
            old_plan = write_json(supplement.V01_EXECUTION_PLAN_PATH, {
                "fresh_qualification": old_receipt,
                "configurations": {"joern-current108": [old_config]},
            })

            prior_unused_cpg = write_bytes("reports/releases/v0.9.2/qualification/attempt-02/old-cpg.bin")
            prior_run = write_json(supplement.PRIOR_CONTROL_RUN_PATH, {"raw_cpg": prior_unused_cpg})
            archived_control_plan = write_json(supplement.PRIOR_CONTROL_PLAN_PATH, {"controls": {}})
            archive = write_json(supplement.PRIOR_REGISTRATION_ARCHIVE_PATH, {
                "control_plan": archived_control_plan,
                "files": [{"source_path": "old-plan.json", "archive_sha256": "a" * 64}],
            })
            admission = {"prior_control_run": prior_run,
                         "prior_registration_archive": archive}

            qual_root = supplement.QUALIFICATION_ROOT
            graph = write_json(f"{qual_root}/control-01/graph.json", {"nodes": []})
            config = write_json(f"{qual_root}/control-01/config.json", {"sources": []})
            cpg = write_bytes(f"{qual_root}/control-01/cpg.bin", b"new-cpg")
            command = write_json(f"{qual_root}/control-01/query.command.json", {
                "argv": ["/joern", "--script", "query.sc"], "exit_status": 0,
            })
            raw = write_json(f"{qual_root}/control-01/raw.json", {
                "native_outputs": [graph, config, cpg], "commands": [command],
            })
            control_run = write_json(f"{qual_root}/control-run.json", {
                "records": [{"raw": raw}],
            })
            receipt = write_json(f"{qual_root}/receipt.json", {"control_run": control_run})
            control_plan = write_json(supplement.CONTROL_PLAN_PATH, {
                "diagnostic_admission": admission,
            })
            unsupported_evidence = write_bytes("adapters/joern/swift-common-v2/unsupported-evidence.json",
                                               b"reviewed unsupported evidence")
            unsupported_decision = write_json("adapters/joern/swift-common-v2/unsupported-decision.json", {
                "case_id": "unsupported-case", "evidence": [unsupported_evidence],
            })
            final_plan = {
                "fresh_qualification": receipt,
                "qualification_control_plan": control_plan,
                "configurations": {"joern-current108": [old_plan, old_config]},
                "cases": {"unsupported-case": {"decision": unsupported_decision}},
            }

            closure = supplement._reference_closure(root, final_plan)
            self.assertIn(supplement.PRIOR_CONTROL_RUN_PATH, closure)
            self.assertIn(supplement.PRIOR_REGISTRATION_ARCHIVE_PATH, closure)
            self.assertIn(supplement.PRIOR_CONTROL_PLAN_PATH, closure)
            self.assertIn(f"{qual_root}/control-01/cpg.bin", closure)
            self.assertIn(f"{qual_root}/control-01/graph.json", closure)
            self.assertIn(f"{qual_root}/control-01/config.json", closure)
            self.assertIn(f"{qual_root}/control-01/query.command.json", closure)
            self.assertIn(unsupported_decision["path"], closure)
            self.assertIn(unsupported_evidence["path"], closure)
            self.assertNotIn(old_receipt["path"], closure)
            self.assertNotIn(old_cpg["path"], closure)
            self.assertNotIn(prior_unused_cpg["path"], closure)
            (root / cpg["path"]).write_bytes(b"changed-capture")
            with self.assertRaisesRegex(RuntimeError, "input changed"):
                supplement._reference_closure(root, final_plan)


class SwiftReportProjectionTests(unittest.TestCase):
    def _decisive_artifacts(self, root, phases, failed_phase=None, timed_out_phase=None):
        leaf = root / "attempted" / "case-001"
        leaf.mkdir(parents=True)

        def bind(name, value):
            path = leaf / name
            path.write_text(json.dumps(value) + "\n")
            return {"path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

        command_refs = []
        for phase in phases:
            command_refs.append(bind(f"{phase}.command.json", {
                "phase_id": phase, "role": "analysis", "cwd": str(leaf),
                "argv": ["/tool/joern", phase],
                "exit_status": 1 if phase == failed_phase else 0,
                "timed_out": phase == timed_out_phase,
                "cleanup_status": "tracked-processes-stopped", "elapsed_seconds": 0.001,
            }))
        config_ref = bind("config.json", {})
        closure_ref = bind("source-closure.json", {})
        raw = {"case_id": "case-001", "raw_outcome": "reached", "state": "reached",
               "executed": True, "duration_ms": 3, "total_elapsed_seconds": 0.003,
               "commands": command_refs, "native_outputs": [config_ref, closure_ref],
               "diagnostics": [], "witness_checkpoints": []}
        return supplement._validate_case_artifact_refs(root, leaf / "raw.json", raw, "attempt")

    def test_decisive_outcome_requires_all_three_successful_non_timeout_phases(self):
        with tempfile.TemporaryDirectory() as temp:
            record = self._decisive_artifacts(
                Path(temp), ["typecheck", "frontend", "query"])
            self.assertEqual(record["raw_outcome"], "reached")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "all three successful"):
                self._decisive_artifacts(Path(temp), ["typecheck", "frontend"])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "all three successful"):
                self._decisive_artifacts(
                    Path(temp), ["typecheck", "frontend", "query"], failed_phase="query")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "all three successful"):
                self._decisive_artifacts(
                    Path(temp), ["typecheck", "frontend", "query"], timed_out_phase="query")

    def test_attempted_runner_error_cost_is_retained_but_unqualified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            leaf = root / "attempted" / "case-001"
            leaf.mkdir(parents=True)

            def bind(name, value):
                path = leaf / name
                if isinstance(value, bytes):
                    path.write_bytes(value)
                else:
                    path.write_text(json.dumps(value) + "\n")
                return {"path": path.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

            (leaf / "config.json").write_text("{}\n")
            (leaf / "source-closure.json").write_text("{}\n")
            config_ref = {"path": (leaf / "config.json").relative_to(root).as_posix(),
                          "sha256": hashlib.sha256((leaf / "config.json").read_bytes()).hexdigest()}
            closure_ref = {"path": (leaf / "source-closure.json").relative_to(root).as_posix(),
                           "sha256": hashlib.sha256((leaf / "source-closure.json").read_bytes()).hexdigest()}
            command_ref = bind("typecheck.command.json", {
                "phase_id": "typecheck", "role": "analysis", "cwd": str(leaf),
                "argv": ["/tool/swiftc"], "exit_status": 1, "timed_out": False,
                "cleanup_status": "tracked-processes-stopped", "elapsed_seconds": 2.5,
            })
            raw = {"case_id": "case-001", "raw_outcome": "runner-error", "state": "runner-error",
                   "executed": True, "duration_ms": 2510, "total_elapsed_seconds": 2.51,
                   "commands": [command_ref],
                   "native_outputs": [config_ref, closure_ref],
                   "diagnostics": ["CommandFailed:typecheck"], "witness_checkpoints": []}
            raw_path = leaf / "raw.json"
            record = supplement._validate_case_artifact_refs(root, raw_path, raw, "attempt")
            self.assertEqual(record["duration_ms"], 2510)
            self.assertTrue(record["latency_sample_included"])
            self.assertEqual(record["raw_outcome"], "runner-error")
            self.assertEqual(record["qualification"], "unqualified")
            self.assertEqual(len(record["commands"]), 1)
            self.assertEqual(len(record["native_outputs"]), 2)

    def test_unsupported_no_invocation_is_excluded_from_latency_samples(self):
        row = supplement._validate_case_artifact_refs(Path("."), Path("case/raw.json"), {
            "case_id": "case-unsupported", "raw_outcome": "unsupported", "state": "unsupported",
            "executed": False, "duration_ms": 0, "total_elapsed_seconds": 0,
            "commands": [], "native_outputs": [],
            "diagnostics": ["UnsupportedCase"], "witness_checkpoints": [],
        }, "unsupported")
        self.assertFalse(row["latency_sample_included"])
        self.assertEqual(row["duration_ms"], 0)
        self.assertEqual(row["disposition"], "unsupported-no-invocation")

    def test_unsupported_case_cannot_hide_nonzero_duration(self):
        with self.assertRaisesRegex(RuntimeError, "no-invocation"):
            supplement._validate_case_artifact_refs(Path("."), Path("case/raw.json"), {
                "case_id": "case-unsupported", "raw_outcome": "unsupported", "state": "unsupported",
                "executed": False, "duration_ms": 1, "total_elapsed_seconds": 0.001,
                "commands": [], "native_outputs": [],
                "diagnostics": ["UnsupportedCase"], "witness_checkpoints": [],
            }, "unsupported")

    def test_existing_projection_export_writes_under_fresh_source_and_changes_only_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = (Path(temp) / "fresh-source").resolve()
            root.mkdir()
            plan_path = "adapters/joern/swift-common-v2/plan-v092-02/execution-plan-qualified.json"
            config_path = "adapters/joern/swift-common-v2/models.json"
            (root / config_path).parent.mkdir(parents=True)
            (root / config_path).write_bytes(b"fixed model and query config\n")
            config_sha = hashlib.sha256((root / config_path).read_bytes()).hexdigest()
            ids = [f"case-{index:03d}" for index in range(108)]
            partition_sizes = [66, 24, 4, 12, 2]
            parent_reports = []
            partition_rows = []
            cursor = 0
            for index, count in enumerate(partition_sizes):
                selected = ids[cursor:cursor + count]
                cursor += count
                report_path = f"reports/releases/v0.9.2/normal/joern-swift-{index}.json"
                parent_reports.append(report_path)
                partition_rows.append({"report": report_path, "execution_group": "joern-swift-common108",
                                       "case_ids": selected})
            parent = {
                "execution_groups": [{"id": "joern-swift-common108", "reports": parent_reports}],
                "reports": partition_rows,
            }
            parent_path = root / "reports/releases/v0.9.0/plan.json"
            parent_path.parent.mkdir(parents=True)
            parent_path.write_text(json.dumps(parent))
            identity = {
                "tool": "joern", "tool_version": "4.0.660",
                "tool_build_identity": "joern-cli:4.0.660;engine:abc;frontend:def",
                "adapter_version": "joern-normal-v092",
            }
            population_sha = "b" * 64
            fixture_revision = "sha256:" + "a" * 64
            cases = {
                case_id: {"source_anchors": [{"marker": f"source:{case_id}"}],
                          "sink_anchors": [{"marker": f"sink:{case_id}"}]}
                for case_id in ids
            }
            plan = {
                "schema": "joern-common-execution-plan/v092",
                "identity": identity,
                "population_sha256": population_sha,
                "fixture_revision": fixture_revision,
                "fresh_qualification": {"sha256": "c" * 64},
                "scored_activation": False,
                "aggregate_resource_qualification": "unavailable",
                "configurations": {"joern-current108": [{"path": config_path, "sha256": config_sha}]},
                "cases": {case_id: {"configuration": "joern-current108", "disposition": "attempt"}
                          for case_id in ids},
            }
            plan_file = root / plan_path
            plan_file.parent.mkdir(parents=True)
            plan_file.write_text(json.dumps(plan, sort_keys=True) + "\n")
            plan_sha = hashlib.sha256(plan_file.read_bytes()).hexdigest()
            raw_results = []
            for case_id in ids:
                raw_path = root / "reports/raw" / case_id / "raw.json"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw = {
                    "case_id": case_id, "plan_sha256": plan_sha,
                    "population_sha256": population_sha, "fixture_revision": fixture_revision,
                    "configuration": "joern-current108", "identity": identity,
                    "raw_outcome": "reached", "state": "inconclusive", "executed": True,
                    "duration_ms": 2, "diagnostics": ["MeasuredCase"],
                    "witness_checkpoints": ["source-reached", "sink-reached"],
                }
                raw_path.write_text(json.dumps(raw, sort_keys=True) + "\n")
                raw_results.append({
                    "case_id": case_id, "configuration": "joern-current108",
                    "raw": {"path": raw_path.relative_to(root).as_posix(),
                            "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()},
                })
            run = {
                "schema": "joern-common-run/v092", "plan_sha256": plan_sha,
                "qualification_sha256": plan["fresh_qualification"]["sha256"],
                "population_sha256": population_sha, "fixture_revision": fixture_revision,
                "identity": identity, "scored_activation": False,
                "aggregate_resource_qualification": "unavailable",
                "started_at_unix_seconds": 1, "ended_at_unix_seconds": 2,
                "results": raw_results,
            }
            population = {"fixture_revision": fixture_revision}
            normal_output = root / "reports/raw/joern-common-v2/current108-v092-02/normal"
            derived_output = root / "reports/timing/v0.9.2/20261122-03/derived/joern-swift-common108"
            with patch.object(raw_report_exporter.common, "load_common_population",
                              return_value=(population, [], [], cases, population_sha)), \
                 patch.object(projection_exporter.common, "load_common_population",
                              return_value=(population, [], [], cases, population_sha)):
                raw_report_exporter.export(root, plan_path, run, normal_output)
                original_bytes = [(normal_output / f"report-{index}.json").read_bytes() for index in range(5)]
                projection_exporter.export(root, plan_path, run, derived_output)
                config_hash = projection_exporter.configuration_hash(root, plan)
                self.assertEqual(len(list(derived_output.glob("report-*.json"))), 5)
                self.assertTrue(derived_output.resolve().is_relative_to(root.resolve()))
                for index, original_raw in enumerate(original_bytes):
                    original = json.loads(original_raw)
                    derived = json.loads((derived_output / f"report-{index}.json").read_text())
                    self.assertEqual(derived, dict(original, configuration_hash=config_hash))
                    self.assertEqual((normal_output / f"report-{index}.json").read_bytes(), original_raw)

    def test_projection_rejects_any_change_beyond_configuration_hash(self):
        original = {"tool": "joern", "results": [{"case_id": "x", "diagnostics": ["one"]}]}
        supplement.validate_projection_only(original, dict(original, configuration_hash="a" * 64), "a" * 64)
        changed = dict(original, configuration_hash="a" * 64)
        changed["results"] = [{"case_id": "x", "diagnostics": ["two"]}]
        with self.assertRaisesRegex(RuntimeError, "differs beyond"):
            supplement.validate_projection_only(original, changed, "a" * 64)
        with self.assertRaisesRegex(RuntimeError, "already contains"):
            supplement.validate_projection_only(dict(original, configuration_hash="b" * 64),
                                                dict(original, configuration_hash="a" * 64), "a" * 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
