#!/usr/bin/env python3
"""Focused common-population projection checks; no analyzer execution."""
import copy
import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import swift_common_population_v2 as common

ROOT = common.ROOT


class CommonPopulationTests(unittest.TestCase):
    def setUp(self):
        self.population = common.read(ROOT / common.POPULATION_PATH)
        self.swift = common.read(ROOT / common.SWIFT_BASELINE_PATH)
        self.rows = copy.deepcopy(self.population["cases"])
        self.swift_rows = copy.deepcopy(self.swift["cases"])
        self.swift_ids = {row["id"] for row in self.swift_rows}

    def test_full_common_hash_revision_and_exact_swift_projection(self):
        population, full_rows, rows, cases, digest = common.load_common_population(ROOT)
        release_plan = common.read(ROOT / common.RELEASE_PLAN_PATH)
        self.assertEqual(len(full_rows), 1108)
        self.assertEqual(len(rows), 108)
        self.assertEqual(len(cases), 108)
        self.assertEqual(digest, release_plan["population"]["sha256"])
        self.assertEqual(population["fixture_revision"], release_plan["fixture_revision"])
        self.assertEqual({row["id"] for row in rows}, self.swift_ids)
        self.assertEqual({case["language"] for case in cases.values()}, {"swift"})

    def test_missing_swift_row_is_rejected(self):
        missing = next(row for row in self.rows if row["id"] in self.swift_ids)
        replacement = copy.deepcopy(next(row for row in self.rows if row["id"] not in self.swift_ids))
        replacement["id"] = "dfb-taint-nonswift-replacement"
        replacement["path"] = "cases/taint/c/replacement/case.json"
        rows = [row for row in self.rows if row["id"] != missing["id"]]
        rows.append(replacement)
        with self.assertRaisesRegex(ValueError, "Swift projection membership mismatch"):
            common.validate_swift_projection(rows, self.swift_rows, self.swift_ids)

    def test_tampered_swift_row_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        selected = next(row for row in rows if row["id"] in self.swift_ids)
        selected["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Swift projection row mismatch"):
            common.validate_swift_projection(rows, self.swift_rows, self.swift_ids)

    def test_extra_swift_identity_is_rejected(self):
        extra_id = "dfb-taint-swift-unregistered-extra"
        extra = copy.deepcopy(self.swift_rows[0])
        extra["id"] = extra_id
        extra["path"] = "cases/taint/swift/unregistered-extra/case.json"
        rows = self.rows + [extra]
        with self.assertRaisesRegex(ValueError, "exact common 1108 population required"):
            common.validate_swift_projection(rows, self.swift_rows, self.swift_ids | {extra_id})

    def test_real_common_joern_bridge_replays_original_activation(self):
        plan = common.read(ROOT / 'adapters/joern/swift-common-v2/plan-v090-01/plan.json')
        receipt = common.verify_common_activation(ROOT, plan)
        self.assertEqual(len(receipt['admitted_case_ids']), 96)
        self.assertEqual(receipt['population_sha256'], common.sha(ROOT / common.POPULATION_PATH))

    def test_bridge_rejects_runtime_drift(self):
        plan = common.read(ROOT / 'adapters/joern/swift-common-v2/plan-v090-01/plan.json')
        plan['runtime']['java_home'] = '/different/jdk'
        with self.assertRaisesRegex(ValueError, 'runtime, capability policy or identity'):
            common.verify_common_activation(ROOT, plan)

    def test_bridge_rejects_capability_promotion(self):
        plan = common.read(ROOT / 'adapters/joern/swift-common-v2/plan-v090-01/plan.json')
        selected = next(c for c in plan['cases'].values() if c['disposition'] == 'attempt')
        selected['capability']['model_mode'] = 'on'
        with self.assertRaisesRegex(ValueError, 'capability changed'):
            common.verify_common_activation(ROOT, plan)

    def test_bridge_rejects_dropped_historical_configuration(self):
        plan = common.read(ROOT / 'adapters/joern/swift-common-v2/plan-v090-01/plan.json')
        plan['configurations']['joern-current108'].pop(0)
        with self.assertRaisesRegex(ValueError, 'configuration closure changed'):
            common.verify_common_activation(ROOT, plan)

    def test_private_engine_keeps_v1_semantic_and_phase_helpers(self):
        for kind, runner_name, reporter_name in (
            ("codeql", "swift_normal_runner_v1", "swift_normal_reports_v1"),
            ("joern", "joern_normal_runner_v1", "joern_normal_reports_v1"),
        ):
            private = common.private_engine(ROOT, kind)
            self.assertEqual(private["runner"].__file__, str(ROOT / "scripts" / (runner_name + ".py")))
            self.assertEqual(private["reports"].__file__, str(ROOT / "scripts" / (reporter_name + ".py")))
            self.assertIs(private["runner"].load_population, common.load_population)
            reference = __import__(reporter_name)
            for name in ("normalized", "validate_phases"):
                with self.subTest(engine=kind, helper=name):
                    private_function = getattr(private["reports"], name)
                    reference_function = getattr(reference, name)
                    self.assertEqual(private_function.__code__.co_code, reference_function.__code__.co_code)
                    self.assertEqual(private_function.__code__.co_consts, reference_function.__code__.co_consts)

            self.assert_runtime_export_import(kind, private)

    def assert_runtime_export_import(self, kind, private):
        reporter, runner = private["reports"], private["runner"]
        case_ids = [f"swift-case-{index:03}" for index in range(108)]
        cases = {
            case_id: {
                "track": "taint", "model_profile": "benchmark-controlled", "score_tier": "core",
                "template_id": "test-template", "polarity": "positive",
                "source_anchors": [], "sink_anchors": [],
            }
            for case_id in case_ids
        }
        identity = {
            "tool": "codeql" if kind == "codeql" else "joern",
            "tool_version": "2.27.1" if kind == "codeql" else "4.0.628",
            "tool_build_identity": "test-build",
            "adapter_version": "swift-normal-v1" if kind == "codeql" else "joern-normal-v1",
        }
        reference = {"path": "plan.json", "sha256": "plan-hash"}
        contract_ref = {"path": "contract.json", "sha256": "contract-hash"}
        witness_ref = {"path": "witness.json", "sha256": "witness-hash"}
        stdout_ref = {"path": "version.stdout", "sha256": "stdout-hash"}
        receipt_ref = {"path": "receipt.json", "sha256": "receipt-hash"}
        config_ref = {"path": "configuration.json", "sha256": "configuration-file-hash"}
        config_key = "patched-codeql" if kind == "codeql" else "joern-current108"
        plan = {
            "schema": "swift-normal-report-plan/v1" if kind == "codeql" else "joern-normal-report-plan/v1",
            "population_sha256": "population-hash", "fixture_revision": "fixture-revision",
            "aggregate_resource_qualification": "unavailable", "scored_activation": False,
            "registered_at_unix_seconds": 1, "identity": identity,
            "execution_contract": contract_ref,
            "configurations": {config_key: [config_ref]},
            "cases": {case_id: {"configuration": config_key} for case_id in case_ids},
            "partition_status": "resolved",
            "runtime": {"joern": "/test/joern"},
        }
        if kind == "joern":
            plan["activation_receipt"] = {"path": "activation.json", "sha256": "activation-hash"}
        rows = [
            {"case_id": case_id, "configuration": config_key, "raw": {"path": "raw.json", "sha256": "raw-hash"}}
            for case_id in case_ids
        ]
        command = {
            "argv": ["/test/joern"] if kind == "joern" else ["codeql", "version"],
            "exit_status": 0, "timed_out": False, "cleanup_status": "tracked-processes-stopped",
        }
        witness = {"observed": identity, "command": command, "observed_at_unix_seconds": 2, "stdout": stdout_ref}
        contract = {
            "aggregate_resource_qualification": "unavailable", "scored_activation": False,
            "population_sha256": "population-hash", "fixture_revision": "fixture-revision",
        }
        if kind == "codeql":
            contract["phases"] = {
                "extraction": {"wall_clock_seconds": 150, "peak_memory_mb": 2048},
                "analysis": {"wall_clock_seconds": 75, "peak_memory_mb": 2048},
            }
            contract["phase_sequences"] = {
                "standard": [
                    {"id": "extract", "role": "extraction"},
                    {"id": "resolve", "role": "analysis"},
                    {"id": "roles", "role": "analysis"},
                    {"id": "flow", "role": "analysis"},
                ],
                "persistence": [
                    {"id": "extract", "role": "extraction"},
                    {"id": "resolve", "role": "analysis"},
                    {"id": "roles", "role": "analysis"},
                    {"id": "flow", "role": "analysis"},
                    {"id": "coverage", "role": "analysis"},
                    {"id": "scopes", "role": "analysis"},
                ],
            }
        else:
            contract.update({
                "schema": "joern-normal-contract/v1", "total_wall_clock_seconds": 75,
                "memory_policy": {"fixture_peak_memory_mb": 512, "aggregate_enforcement": "unavailable", "jvm_heap_request_mb": 512},
                "phase_sequence": [{"id": name, "role": "analysis"} for name in ("typecheck", "frontend", "query")],
            })
        run = {
            "schema": "swift-normal-report-run/v1" if kind == "codeql" else "joern-normal-report-run/v1",
            "plan_sha256": "plan-hash", "population_sha256": "population-hash",
            "fixture_revision": "fixture-revision", "aggregate_resource_qualification": "unavailable",
            "scored_activation": False, "started_at_unix_seconds": 2, "ended_at_unix_seconds": 3,
            "cold_or_warm": "cold", "identity": identity, "identity_witness": witness_ref,
            "results": rows,
        }
        if kind == "codeql":
            run["query_qualification"] = receipt_ref
        else:
            run["activation_receipt"] = plan["activation_receipt"]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            version_stdout = root / "version.stdout"
            version_stdout.write_text("CodeQL test\n" if kind == "codeql" else "Joern 4.0.628\n")
            paths = {
                "plan.json": root / "plan.json", "witness.json": root / "witness.json",
                "version.stdout": version_stdout, "contract.json": root / "contract.json",
                "receipt.json": root / "receipt.json",
            }

            def fake_read(path):
                name = Path(path).name
                if name == "plan.json": return plan
                if name == "witness.json": return witness
                if name == "contract.json": return contract
                if name == "receipt.json": return {"plan_path": "plan.json"}
                raise AssertionError("unexpected exporter read: " + str(path))

            def fake_bound_file(_root, ref):
                return paths[ref["path"]]

            class PrivateImportReached(Exception):
                pass

            class HistoricalImportReached(Exception):
                pass

            historical = importlib.import_module("swift_normal_runner_v1" if kind == "codeql" else "joern_normal_runner_v1")
            method = "verify_query_receipt" if kind == "codeql" else "verify_activation"

            def private_probe(*_args, **_kwargs):
                raise PrivateImportReached()

            def historical_probe(*_args, **_kwargs):
                raise HistoricalImportReached()

            with patch.object(reporter, "repository_file", return_value=paths["plan.json"]), \
                 patch.object(reporter, "read", side_effect=fake_read), \
                 patch.object(reporter, "sha", return_value="plan-hash"), \
                 patch.object(reporter, "bound_file", side_effect=fake_bound_file), \
                 patch.object(reporter, "load_population", return_value=({"fixture_revision": "fixture-revision"}, cases, "population-hash")), \
                 patch.object(reporter, "configuration_hash", return_value="configuration-hash"), \
                 patch.object(runner, method, side_effect=private_probe), \
                 patch.object(historical, method, side_effect=historical_probe):
                with self.assertRaises(PrivateImportReached):
                    reporter.export(root, "plan.json", run)


if __name__ == "__main__":
    unittest.main()
