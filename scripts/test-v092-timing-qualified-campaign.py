#!/usr/bin/env python3
"""Mocked regressions for the prospective v0.9.2 timing controller."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


campaign = load("qualified_campaign_under_test", Path(__file__).with_name("v092_timing_qualified_campaign.py"))


class QualifiedCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="dfb-qualified-campaign-test-")
        cls.root = Path(cls.temp.name)
        for relative in (
            "reports/timing/v0.9.2/20261113-01/plan.json",
            "reports/releases/v0.9.2/execution-v4/contract.json",
            *campaign.HELPERS,
        ):
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

        cls.source_plan_path = cls.root / "reports/timing/v0.9.2/20261113-01/plan.json"
        cls.source_plan = json.loads(cls.source_plan_path.read_text())
        cls.frozen = json.loads((cls.root / campaign.FROZEN_CONTRACT).read_text())
        cls.original_git_show = campaign.legacy.core._git_show
        cls.git_blob_cache = {}

        def real_git_show(_root, commit, relative):
            key = (commit, relative)
            if key not in cls.git_blob_cache:
                cls.git_blob_cache[key] = cls.original_git_show(ROOT, commit, relative)
            return cls.git_blob_cache[key]

        campaign.legacy.core._git_show = real_git_show
        original_frozen_blob = campaign._frozen_report_blob

        def cached_frozen_blob(_root, report_path):
            if report_path not in cls.git_blob_cache:
                cls.git_blob_cache[report_path] = original_frozen_blob(ROOT, report_path)
            return cls.git_blob_cache[report_path]

        campaign._frozen_report_blob = cached_frozen_blob
        cls.base_plan = cls.build_plan(cls.root, "20261114-40")

    @classmethod
    def tearDownClass(cls):
        campaign.legacy.core._git_show = cls.original_git_show
        cls.temp.cleanup()

    @classmethod
    def build_plan(cls, root: Path, campaign_id: str) -> dict:
        bins = root / "binding-tools"
        bins.mkdir(exist_ok=True)
        tools = {}
        for name in ["runner", *campaign.FAMILIES]:
            path = bins / name
            path.write_bytes(f"pinned {name}".encode())
            tools[name] = {"path": str(path), "sha256": campaign.sha(path)}

        runtime_root = root / "runtime-tree"
        runtime_root.mkdir(exist_ok=True)
        runtime_file = runtime_root / "runtime.bin"
        runtime_file.write_bytes(b"runtime-one")
        runtime = {
            "schema_version": 1,
            "root": str(runtime_root),
            "files": [{"path": "runtime.bin", "sha256": hashlib.sha256(b"runtime-one").hexdigest(),
                       "mode": 0o644}],
            "symlinks": [],
            "external_files": [],
        }
        runtime_path = root / "runtime-manifest.json"
        runtime_path.write_text(json.dumps(runtime, sort_keys=True))
        runtime_bindings = [{"id": "test-runtime", "path": str(runtime_path), "sha256": campaign.sha(runtime_path)}]

        family_first = {}
        source_cold = [group for group in cls.source_plan["groups"] if group.get("kind") == "cold"]
        for group in source_cold:
            if group["family"] not in family_first and group["id"] not in campaign.SWIFT_WRAPPERS:
                family_first[group["family"]] = group["id"]
        first_ids = [family_first[family] for family in campaign.FAMILIES]
        order = [*first_ids, *(group["id"] for group in source_cold if group["id"] not in first_ids)]
        overrides = {group_id: {"status": "ready", "runtime_ids": ["test-runtime"]}
                     for group_id in first_ids}
        rebindings = {source_cold[0]["argv"][0]: tools["runner"]["path"]}
        for group_id in first_ids:
            group = next(item for item in source_cold if item["id"] == group_id)
            flag = campaign.FAMILY_TOOL_FLAGS[group["family"]]
            value = group["argv"][group["argv"].index(flag) + 1]
            rebindings[value] = tools[group["family"]]["path"]
        bindings = {
            "schema": "v092-qualified-runtime-bindings/v1",
            "release_commit": campaign.RELEASE,
            "source_plan": {"path": "reports/timing/v0.9.2/20261113-01/plan.json",
                            "sha256": campaign.sha(cls.source_plan_path)},
            "campaign_id": campaign_id,
            "launch_after_utc": "2000-01-01T00:00:00+00:00",
            "tools": tools,
            "runtimes": runtime_bindings,
            "path_rebindings": rebindings,
            "group_overrides": overrides,
            "auxiliary_groups": [],
            "group_order": order,
            "qualification_note": "mocked qualification fixture",
        }
        bindings_raw = json.dumps(bindings, sort_keys=True).encode()
        binding_path = root / "runtime-bindings-test.json"
        binding_path.write_bytes(bindings_raw)
        return campaign._build_plan(root, bindings, hashlib.sha256(bindings_raw).hexdigest(),
                                    binding_path.relative_to(root).as_posix())

    @contextlib.contextmanager
    def using_root(self, campaign_id: str, plan_override: dict | None = None):
        old_campaign_root = campaign.ROOT
        old_legacy_root = campaign.legacy.ROOT
        old_report, old_work = campaign.legacy.REPORT, campaign.legacy.WORK
        campaign.ROOT = self.root
        campaign.legacy.ROOT = self.root
        plan = json.loads(json.dumps(plan_override or self.base_plan))
        plan["campaign_id"] = campaign_id
        report, _ = campaign.legacy.campaign_paths(campaign_id)
        report.mkdir(parents=True, exist_ok=True)
        path = report / "qualified-plan-01.json"
        path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
        try:
            yield plan, path, report
        finally:
            campaign.ROOT = old_campaign_root
            campaign.legacy.ROOT = old_legacy_root
            campaign.legacy.REPORT, campaign.legacy.WORK = old_report, old_work

    def test_real_source_plan_build_keeps_all_cases_and_corrects_swift_driver(self):
        plan = self.base_plan
        cold = [group for group in plan["groups"] if group["kind"] == "cold"]
        self.assertEqual(len(cold), 84)
        self.assertEqual(plan["group_order"][:8], [
            next(group["id"] for group in cold if group["family"] == family and group["status"] == "ready")
            for family in campaign.FAMILIES
        ])
        source = {group["id"]: group for group in self.source_plan["groups"] if group["kind"] == "cold"}
        frozen = {group["id"]: group for group in self.frozen["groups"]}
        for group in cold:
            self.assertEqual(group["case_ids"], source[group["id"]]["case_ids"])
            self.assertEqual(group["reports"], source[group["id"]]["reports"])
            self.assertEqual(group["case_ids"], frozen[group["id"]]["case_ids"])
        for group_id, driver in campaign.SWIFT_WRAPPERS.items():
            group = next(item for item in cold if item["id"] == group_id)
            self.assertEqual(group["argv"][:2], frozen[group_id]["argv"][:2])
            self.assertEqual(group["argv"][0], "/usr/bin/python3")
            self.assertEqual(group["argv"][1], driver)
            self.assertEqual(group["status"], "blocked")
            self.assertTrue(group["blocker"])
        bifrost = next(group for group in cold if group["id"] == "bifrost-c-kernel")
        frozen_report = plan["frozen_report_bindings"]["bifrost-c-kernel"][0]
        self.assertEqual(bifrost["reports"][0]["tool_version"], "bifrost 0.15.1")
        self.assertEqual(frozen_report["identity"]["tool_version"], "bifrost 0.15.1")
        self.assertEqual(frozen_report["git_path"],
                         "reports/releases/v0.9.2/publication-v1/normal/bifrost-c-kernel.json")
        self.assertFalse(plan["planned_coverage"]["full_coverage_claimed"])

    def test_verify_rehashes_tools_and_full_runtime_manifests(self):
        with self.using_root("20261114-41") as (plan, path, _):
            campaign.verify_plan(path, require_ready=True)
            tool = Path(plan["tools"]["bifrost"]["path"])
            tool.write_bytes(b"changed pinned tool")
            with self.assertRaisesRegex(RuntimeError, "bifrost tool SHA-256 differs"):
                campaign.verify_plan(path, require_ready=True)
            tool.write_bytes(b"pinned bifrost")

            runtime = Path(plan["runtimes"][0]["path"])
            runtime_file = Path(json.loads(runtime.read_text())["root"]) / "runtime.bin"
            runtime_file.write_bytes(b"changed runtime")
            with self.assertRaisesRegex(RuntimeError, "runtime tree file differs"):
                campaign.verify_plan(path, require_ready=True)

    def test_frozen_comparison_ignores_timing_but_stops_on_outcome_change(self):
        group = next(group for group in self.base_plan["groups"] if group["id"] == "bifrost-c-kernel")
        expected_raw = campaign.legacy.core._git_show(
            ROOT, campaign.RELEASE, "reports/releases/v0.9.2/publication-v1/normal/bifrost-c-kernel.json")
        expected = json.loads(expected_raw)
        with tempfile.TemporaryDirectory(prefix="dfb-report-compare-") as directory:
            source = Path(directory)
            report_path = source / group["reports"][0]["source_path"]
            report_path.parent.mkdir(parents=True)
            actual = json.loads(json.dumps(expected))
            actual["started_at_unix_seconds"] += 10
            actual["ended_at_unix_seconds"] += 10
            for row in actual["results"]:
                row["duration_ms"] += 10
            report_path.write_text(json.dumps(actual))
            receipt = campaign.compare_frozen_report_bytes(self.base_plan, group, source)
            self.assertEqual(receipt["status"], "matched")
            actual["results"][0]["outcome"] = "reached" if actual["results"][0]["outcome"] != "reached" else "not-reached"
            report_path.write_text(json.dumps(actual))
            with self.assertRaises(campaign.FrozenComparisonError) as error:
                campaign.compare_frozen_report_bytes(self.base_plan, group, source)
            self.assertEqual(error.exception.receipt["status"], "mismatch")

    def test_setup_files_are_pinned_and_confined_to_attempt_maven_home(self):
        with tempfile.TemporaryDirectory(prefix="dfb-maven-setup-") as directory:
            root = Path(directory)
            package = root / "scala-library.jar"
            package.write_bytes(b"pinned scala artifact")
            group = {"id": "bifrost-scala-kernel", "setup_files": [{
                "source": str(package), "path": "home/.m2/repository/org/scala/scala-library.jar",
                "sha256": campaign.sha(package), "mode": 0o644,
            }]}
            source = root / "attempt"
            source.mkdir()
            receipts = campaign._copy_setup_files(group, source)
            destination = source / group["setup_files"][0]["path"]
            self.assertEqual(destination.read_bytes(), package.read_bytes())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o644)
            self.assertEqual(receipts[0]["sha256"], campaign.sha(package))
            self.assertEqual(len(campaign._verify_setup_files(group, source)), 1)
            destination.write_bytes(b"changed dependency")
            with self.assertRaisesRegex(RuntimeError, "prepared dependency changed"):
                campaign._verify_setup_files(group, source)
            group["setup_files"][0]["path"] = "home/.m2/../../outside.jar"
            with self.assertRaisesRegex(RuntimeError, "below home/.m2"):
                campaign._copy_setup_files(group, source)

    def test_warm_validator_requires_prefixes_and_all_retained_case_files(self):
        root = Path(self.temp.name) / "warm-fixture"
        root.mkdir(exist_ok=True)
        ids = [f"case-{index:02d}" for index in range(12)]
        group = {"id": "warm-semgrep-java", "kind": "warm", "family": "semgrep", "language": "java",
                 "warm_case_ids": ids, "warm_batch_sizes": [1, 2, 4, 8, 12], "deadline_seconds": 600,
                 "output_roots": ["reports/raw/warm-latency/semgrep-java-kernel"],
                 "argv": ["runner", "--population", "v0.9.0", "measure-warm-latency", "--tool", "semgrep",
                          "--language", "java", "--batch-sizes", "1,2,4,8,12", "--semgrep", "semgrep"]}
        output = root / group["output_roots"][0]
        output.mkdir(parents=True)
        sizes = group["warm_batch_sizes"]
        runs = []
        for repeat in (1, 2):
            batches = []
            for size in sizes:
                batches.append({"k": size, "wall_ms": 1, "case_ids": ids[:size]})
                evidence_dir = output / f"run-{repeat}-batch-{size}-evidence"
                evidence_dir.mkdir()
                for case_id in ids[:size]:
                    (evidence_dir / f"{case_id}.json").write_text("{}")
            runs.append({"run": repeat, "batches": batches})
            identity = campaign._frozen_family_identity(self.base_plan, "semgrep", "java")
        artifact = {"schema_version": 1, "evidence_kind": "retained-warm-marginal-latency",
                    "adapter": "semgrep", "language": "java", "repeats": 2,
                    "population_available": len(ids), "tool_version": identity["tool_version"],
                    "tool_build_identity": identity["tool_build_identity"],
                    "fixture_revision": self.base_plan["fixture_revision"], "runs": runs}
        (output / "warm-latency.json").write_text(json.dumps(artifact))
        receipt = campaign.validate_warm_artifact(self.base_plan, group, root)
        self.assertTrue(receipt["equivalence_pending"])
        self.assertFalse(receipt["publication_eligible"])
        artifact["runs"][1]["batches"][2]["case_ids"] = ids[:7]
        (output / "warm-latency.json").write_text(json.dumps(artifact))
        with self.assertRaisesRegex(RuntimeError, "not the bound case prefix"):
            campaign.validate_warm_artifact(self.base_plan, group, root)

    def test_warm_dispatch_sizes_match_each_static_population(self):
        tools = self.base_plan["tools"]
        for family, ids, sizes in (
            ("joern", [f"joern-{index:02d}" for index in range(16)], [1, 2, 4, 8, 16]),
            ("semgrep", [f"semgrep-{index:02d}" for index in range(12)], [1, 2, 4, 8, 12]),
        ):
            flag = "--joern" if family == "joern" else "--semgrep"
            argv = [tools["runner"]["path"], "--population", "v0.9.0", "measure-warm-latency",
                    "--tool", family, "--language", "java", "--batch-sizes", ",".join(map(str, sizes)),
                    flag, tools[family]["path"]]
            group = {"id": f"warm-{family}-java", "kind": "warm", "family": family, "language": "java",
                     "warm_case_ids": ids, "warm_batch_sizes": sizes, "deadline_seconds": 600,
                     "output_roots": [f"reports/raw/warm-latency/{family}-java-kernel"], "argv": argv}
            campaign._validate_warm_group(group, tools)
            if family == "semgrep":
                group["warm_batch_sizes"] = [1, 2, 4, 8, 16]
                with self.assertRaisesRegex(RuntimeError, "static population"):
                    campaign._validate_warm_group(group, tools)

    def test_quiet_wait_is_bounded_by_campaign_wall_window(self):
        class NeverQuietWindow:
            elapsed_seconds = 0.0
            def observe(self, *_args, **_kwargs):
                return False
            def reset(self):
                pass

        host = Mock()
        host.QuietWindow = NeverQuietWindow
        host.SAMPLE_INTERVAL_SECONDS = 30
        host.HostObservationError = RuntimeError
        host.failure_record = lambda exc: {"error": str(exc)}
        observation = {"disk_free_bytes": 200 * campaign.GIB, "quiescent_service_pids": []}
        observer = Mock()
        observer.snapshot.return_value = observation
        clock = {"now": 0.0}
        def monotonic():
            return clock["now"]
        def sleep(seconds):
            clock["now"] += seconds
        with tempfile.TemporaryDirectory(prefix="dfb-quiet-window-") as directory:
            with patch.object(campaign.time, "monotonic", side_effect=monotonic), \
                    patch.object(campaign.time, "sleep", side_effect=sleep):
                with self.assertRaises(campaign.CampaignWindowEnded):
                    campaign.wait_fresh_quiet(host, observer, Path(directory) / "host.jsonl", deadline=1.0)
        self.assertEqual(observer.snapshot.call_count, 1)

    def _run_context(self, campaign_id: str, plan: dict | None = None):
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(campaign, "_assert_committed_inputs",
                                         return_value={"plan_commit": "fixture-head", "committed_inputs": {}}))
        stack.enter_context(patch.object(campaign.legacy.core, "_exclusive_lock", return_value=contextlib.nullcontext()))
        class FakeDiskGuard:
            def __init__(self, **_kwargs):
                pass
            def check(self, **_kwargs):
                return None
        stack.enter_context(patch.object(campaign.legacy.disk, "DiskGuard", FakeDiskGuard))
        tracker = Mock()
        tracker._start_identity.return_value = "100:200"
        stack.enter_context(patch.object(campaign.legacy.core, "_process_tracker", return_value=tracker))
        def materialize(_root, _commit, destination, _explicit, *, preflight_only=False, **_kwargs):
            if preflight_only:
                return 1
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.mkdir()
            return None
        stack.enter_context(patch.object(campaign.legacy.core, "_materialize_source", side_effect=materialize))
        stack.enter_context(patch.object(campaign.legacy.core, "_register_source_snapshot", return_value="release"))
        quiet_gate = stack.enter_context(patch.object(campaign, "wait_fresh_quiet", return_value={
            "quiet_elapsed_seconds": 300, "cpu_idle_percent": 95}))
        observer = Mock()
        observer.snapshot.return_value = {"hardware": {"logical_cpus": 1}, "processes": [
            {"pid": 1, "ppid": 0, "comm": "/tmp/unrelated", "cpu_percent": 99.0}]}
        stack.enter_context(patch.object(campaign.legacy, "Observer", return_value=observer))
        pysa_tmp = self.root / "pysa-scratch"
        pysa_tmp.mkdir(exist_ok=True)
        stack.enter_context(patch.object(campaign, "PYSA_TMP_ROOT", pysa_tmp))
        def child_environment(group, source, *_args):
            environment = {"HOME": str(source / "home"), "TMPDIR": str(source / "tmp")}
            if group.get("tool") == "pysa":
                identity = hashlib.sha256(str(source.resolve()).encode()).hexdigest()[:20]
                environment["TMPDIR"] = str(pysa_tmp / ("dfb-v092-pysa-" + identity))
            return environment
        stack.enter_context(patch.object(campaign.legacy.core, "_child_environment", side_effect=child_environment))
        stack.enter_context(patch.object(campaign.legacy, "reconcile", return_value={
            "kind": "cold", "publication_eligible": False}))
        stack.enter_context(patch.object(campaign, "compare_frozen_report_bytes", return_value={
            "status": "matched", "publication_eligible": False}))
        stack.enter_context(patch.object(campaign, "_assert_prepared_source", return_value={
            "source_commit": campaign.RELEASE, "source_and_fixture_inputs_unchanged": True}))
        stack.enter_context(patch.object(campaign, "verify_plan", wraps=campaign.verify_plan))
        stack.enter_context(patch.object(campaign.subprocess, "check_output", return_value=b""))
        return stack, observer, quiet_gate

    def test_each_group_gets_a_quiet_gate_and_active_cpu_does_not_abort(self):
        with self.using_root("20261114-42") as (_plan, path, report):
            stack, observer, quiet_gate = self._run_context("20261114-42")
            with stack:
                process_calls = []
                def run_process(_argv, _source, _env, stdout, stderr, _deadline, *, disk_guard, ownership, **_kwargs):
                    self.assertTrue(any("dfb-v092-pysa-" in str(p) for p in _kwargs["scratch_paths"]))
                    ownership.update({"root_pid": 123, "descendant_containment": "unproven"})
                    disk_guard.observe_background("analyzer-active", 123)
                    Path(stdout).write_text("")
                    Path(stderr).write_text("")
                    process_calls.append(1)
                    return 0, False, 0.01, None
                with patch.object(campaign.legacy.core, "_run_process", side_effect=run_process):
                    result = campaign.execute(path)
                self.assertEqual(result["status"], "unqualified")
                self.assertEqual(len(process_calls), 8)
                self.assertEqual(quiet_gate.call_count, 8)
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["completed_commands"], 8)
                self.assertEqual(terminal["blocked_cold_groups"], 76)
                self.assertFalse(terminal["full_84_group_coverage_claimed"])
                first = next(group for group in _plan["groups"] if group["status"] == "ready")
                evidence = json.loads((report / "attempts" / first["id"] / "attempt-01/terminal.json").read_text())
                self.assertFalse(evidence["quiet_certification"]["certified"])
                self.assertTrue(evidence["quiet_certification"]["contention_observed"])
                self.assertEqual(evidence["descendant_containment"], "unproven")
                self.assertFalse(evidence["publication_eligible"])

    def test_failure_stops_queue_without_retry(self):
        with self.using_root("20261114-43") as (_plan, path, report):
            stack, _observer, quiet_gate = self._run_context("20261114-43")
            with stack:
                calls = []
                def fail_first(*_args, **_kwargs):
                    calls.append(1)
                    return 1, False, 0.02, None
                with patch.object(campaign.legacy.core, "_run_process", side_effect=fail_first):
                    result = campaign.execute(path)
                self.assertEqual(len(calls), 1)
                self.assertEqual(quiet_gate.call_count, 1)
                self.assertEqual(result["status"], "unqualified")
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["completed_commands"], 0)
                self.assertEqual(len(terminal["remaining_ready_groups"]), 7)
                attempt = report / "attempts" / terminal["stopped_group"] / "attempt-01/terminal.json"
                self.assertEqual(json.loads(attempt.read_text())["status"], "failed")

    def test_launch_date_and_committed_plan_bytes_fail_closed(self):
        future = json.loads(json.dumps(self.base_plan))
        future["launch_after_utc"] = "2100-01-01T00:00:00+00:00"
        with self.using_root("20261114-44", future) as (_plan, path, _):
            with patch.object(campaign, "verify_plan") as verify:
                with self.assertRaisesRegex(RuntimeError, "launch is not authorized"):
                    campaign.execute(path)
                verify.assert_not_called()
        with self.using_root("20261114-45") as (plan, path, _):
            expected = path.resolve().relative_to(self.root.resolve()).as_posix()
            def changed_commit(root, relative):
                if relative == expected:
                    return b"different committed plan bytes"
                return (root / relative).read_bytes()
            with patch.object(campaign, "_committed_bytes", side_effect=changed_commit):
                with self.assertRaisesRegex(RuntimeError, "differs from committed and planned bytes"):
                    campaign._assert_committed_inputs(self.root, path, plan)

    def test_path_entries_relocate_without_losing_protected_environment(self):
        source = {"PATH": "/old/venv/bin:/old/jdk/bin:/usr/bin", "JAVA_HOME": "/old/jdk",
                  "PYTHONDONTWRITEBYTECODE": "1", "SEMGREP_ENABLE_VERSION_CHECK": "0", "LANG": "en_US.UTF-8"}
        mappings = {"/old/venv": "/new/venv", "/old/jdk": "/new/jdk"}
        override = {"JAVA_HOME": "/new/jdk", "PATH": "/compiler/bin:/new/venv/bin:/new/jdk/bin:/usr/bin",
                    "CC": "/compiler/bin/clang", "CXX": "/compiler/bin/clang++"}
        actual = campaign._environment_with_reviewed_overrides(source, override, mappings, "fixture")
        self.assertEqual(actual["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(actual["SEMGREP_ENABLE_VERSION_CHECK"], "0")
        self.assertEqual(actual["LANG"], "en_US.UTF-8")
        with self.assertRaisesRegex(RuntimeError, "protected environment"):
            campaign._environment_with_reviewed_overrides(source, {"LANG": "different"}, mappings, "fixture")
        with self.assertRaisesRegex(RuntimeError, "unregistered compiler"):
            campaign._environment_with_reviewed_overrides(source,
                {"PATH": "/unbound/bin:/new/venv/bin:/new/jdk/bin:/usr/bin"}, mappings, "fixture")

    def test_cold_arguments_cannot_change_analyzer_semantics(self):
        source = self.source_plan["groups"][0]
        frozen = next(g for g in self.frozen["groups"] if g["id"] == source["id"])
        with self.assertRaisesRegex(RuntimeError, "frozen command semantics"):
            campaign._normalize_source_group(source, frozen,
                {"argv": [*source["argv"], "--different-profile"]}, {}, self.base_plan["tools"])

    def test_auxiliary_identity_uses_exact_language_kernel_and_flowdroid_boundary(self):
        identity = campaign._frozen_family_identity(self.base_plan, "semgrep", "java")
        self.assertEqual(identity["tool_build_identity"], "semgrep-oss:1.181.0")
        cold = campaign._frozen_family_identity(self.base_plan, "flowdroid", "java")
        overhead = campaign._frozen_family_identity(self.base_plan, "flowdroid", "java", overhead=True)
        self.assertIn("; dexed by ", cold["tool_build_identity"])
        self.assertEqual(overhead["tool_build_identity"], cold["tool_build_identity"].partition("; dexed by ")[0])

    def test_missing_active_cpu_observations_do_not_stop_the_queue(self):
        with self.using_root("20261114-46") as (_plan, path, report):
            stack, observer, quiet = self._run_context("20261114-46")
            with stack:
                observer.snapshot.side_effect = OSError("fixture telemetry unavailable")
                def run(*args, disk_guard, ownership, **kwargs):
                    ownership["root_pid"] = 123
                    disk_guard.observe_background("analyzer-active", 123)
                    return 0, False, 1.0, None
                with patch.object(campaign.legacy.core, "_run_process", side_effect=run) as dispatch:
                    result = campaign.execute(path)
                self.assertEqual(dispatch.call_count, 8)
                self.assertEqual(quiet.call_count, 8)
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["completed_commands"], 8)
                attempt = next((report / "attempts").glob("*/attempt-01/terminal.json"))
                flags = json.loads(attempt.read_text())["quiet_certification"]
                self.assertFalse(flags["certified"])
                self.assertGreater(flags["observation_failures"], 0)

    def test_post_command_failure_does_not_double_count_execution_budget(self):
        with self.using_root("20261114-47") as (_plan, path, report):
            stack, _observer, _quiet = self._run_context("20261114-47")
            with stack:
                def run(*args, ownership, **kwargs):
                    ownership["root_pid"] = 123
                    return 0, False, 1.25, None
                with patch.object(campaign.legacy.core, "_run_process", side_effect=run), \
                        patch.object(campaign, "compare_frozen_report_bytes", side_effect=RuntimeError("fixture mismatch")):
                    campaign.execute(path)
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["execution_budget_consumed_seconds"], 1.25)
                self.assertEqual(terminal["completed_commands"], 0)

    def test_predispatch_failure_after_completed_command_has_zero_execution_time(self):
        with self.using_root("20261114-48") as (_plan, path, report):
            stack, _observer, quiet = self._run_context("20261114-48")
            with stack:
                quiet.side_effect = [{"quiet_elapsed_seconds": 300}, RuntimeError("fixture predispatch failure")]
                def run(*args, ownership, **kwargs):
                    ownership["root_pid"] = 123
                    return 0, False, 1.25, None
                with patch.object(campaign.legacy.core, "_run_process", side_effect=run):
                    campaign.execute(path)
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["execution_budget_consumed_seconds"], 1.25)
                attempt = report / "attempts" / terminal["stopped_group"] / "attempt-01/terminal.json"
                failed = json.loads(attempt.read_text())
                self.assertEqual(failed["elapsed_seconds"], 0)
                self.assertTrue(failed["not_dispatched"])

    def test_source_setup_failure_has_durable_terminal_and_no_dispatch(self):
        with self.using_root("20261114-49") as (_plan, path, report):
            stack, _observer, _quiet = self._run_context("20261114-49")
            with stack:
                with patch.object(campaign.legacy.core, "_materialize_source", side_effect=OSError("fixture source disk failure")), \
                        patch.object(campaign.legacy.core, "_run_process") as dispatch:
                    with self.assertRaisesRegex(OSError, "fixture source disk failure"):
                        campaign.execute(path)
                dispatch.assert_not_called()
                terminal = json.loads((report / "campaign-terminal.json").read_text())
                self.assertEqual(terminal["status"], "blocked")
                self.assertEqual(terminal["completed_commands"], 0)
                self.assertFalse(terminal["analyzer_dispatch_proven"])
                self.assertFalse((report / "campaign-start.json").exists())
                self.assertTrue((report / "launch-failure-001.json").exists())

    def test_attempt_directory_failure_after_completion_retains_campaign_terminal(self):
        with self.using_root("20261114-50") as (plan, path, report):
            stack, _observer, _quiet = self._run_context("20261114-50")
            second = campaign._ready_groups(plan)[1]["id"]
            forbidden = report / "attempts" / second / "attempt-01"
            original_mkdir = Path.mkdir
            def mkdir(target, *args, **kwargs):
                if target == forbidden:
                    raise OSError("fixture attempt directory failure")
                return original_mkdir(target, *args, **kwargs)
            def run(*args, ownership, **kwargs):
                ownership["root_pid"] = 123
                return 0, False, 1.25, None
            with stack, patch.object(Path, "mkdir", new=mkdir), \
                    patch.object(campaign.legacy.core, "_run_process", side_effect=run) as dispatch:
                with self.assertRaisesRegex(OSError, "fixture attempt directory failure"):
                    campaign.execute(path)
            self.assertEqual(dispatch.call_count, 1)
            terminal = json.loads((report / "campaign-terminal.json").read_text())
            self.assertEqual(terminal["status"], "unqualified")
            self.assertEqual(terminal["completed_commands"], 1)
            self.assertTrue(terminal["analyzer_dispatch_proven"])

    def test_storage_limits_still_stop_waiting_for_quiet(self):
        host, observer = Mock(), Mock()
        host.QuietWindow = Mock
        def exhausted():
            raise campaign.legacy.CampaignStop("retention ceiling lost while waiting")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(campaign.legacy.CampaignStop, "retention ceiling"):
                campaign.wait_fresh_quiet(host, observer, Path(directory) / "host.jsonl",
                    campaign.time.monotonic() + 60, capacity_check=exhausted)
        observer.snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
