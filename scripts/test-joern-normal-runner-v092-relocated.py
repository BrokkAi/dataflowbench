"""Focused path and provenance gates for the additive v0.9.2-02 Joern runner."""

from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import joern_normal_runner_v092_relocated as runner
import v092_qualification
import v092_relocated_qualification as relocated_qualification
import v092_qualification
import joern_diagnostic_admission_v092_relocated as relocated_admission


OLD_RUNNER_PATH = ROOT / "scripts/joern_normal_runner_v092.py"
NEW_RUNNER_PATH = ROOT / "scripts/joern_normal_runner_v092_relocated.py"


class RelocatedRunnerTests(unittest.TestCase):
    def test_only_explicit_path_and_root_transitions_differ_from_frozen_runner(self):
        original = OLD_RUNNER_PATH.read_text()
        expected = original
        substitutions = (
            (
                "import v092_qualification as qualification_binding",
                "import v092_relocated_qualification as qualification_binding",
            ),
            (
                "import joern_diagnostic_admission_v092 as diagnostic_admission",
                "import joern_diagnostic_admission_v092_relocated as diagnostic_admission",
            ),
            (
                'EXECUTION_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"',
                'PENDING_EXECUTION_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-02/qualification-pending-plan-05.json"\n'
                'FINAL_EXECUTION_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-02/execution-plan-qualified.json"\n'
                'QUALIFICATION_OUTPUT_ROOT = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/qualification"',
            ),
            (
                '    require(Path(plan_path).as_posix() == EXECUTION_PLAN_PATH, "Joern v0.9.2 executable plan must use plan-v092-01")',
                '    expected_plan_path = PENDING_EXECUTION_PLAN_PATH if allow_qualification_pending else FINAL_EXECUTION_PLAN_PATH\n'
                '    require(Path(plan_path).as_posix() == expected_plan_path, "Joern v0.9.2 mode must use its exact plan-v092-02 path")',
            ),
            (
                '        "reports/releases/v0.9.0/plan.json",\n    )',
                '        "reports/releases/v0.9.0/plan.json",\n'
                '        "scripts/joern_normal_runner_v092_relocated.py",\n'
                '        "scripts/run-joern-common-v092-relocated.py",\n'
                '        "scripts/v092_relocated_qualification.py",\n'
                '        "scripts/joern_diagnostic_admission_v092_relocated.py",\n    )',
            ),
            (
                '    require(output.is_relative_to(root / "reports/releases/v0.9.2/qualification"), "Joern qualification output must stay under the v0.9.2 qualification root")',
                '    require(output.is_relative_to(root / QUALIFICATION_OUTPUT_ROOT), "Joern qualification output must stay under the v0.9.2-02 preparation root")',
            ),
        )
        for before, after in substitutions:
            self.assertIn(before, expected)
            expected = expected.replace(before, after)
        self.assertEqual(NEW_RUNNER_PATH.read_text(), expected)

    def test_pending_and_final_plan_paths_are_mode_specific(self):
        with self.assertRaisesRegex(ValueError, "exact plan-v092-02 path"):
            runner.validate_plan(ROOT, "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json", allow_qualification_pending=True)
        with self.assertRaisesRegex(ValueError, "exact plan-v092-02 path"):
            runner.validate_plan(ROOT, runner.PENDING_EXECUTION_PLAN_PATH)
        with self.assertRaisesRegex(ValueError, "exact plan-v092-02 path"):
            runner.validate_plan(ROOT, runner.FINAL_EXECUTION_PLAN_PATH, allow_qualification_pending=True)

    def test_relocated_qualification_accepts_only_exact_preparation_root(self):
        good = {
            "path": relocated_qualification.QUALIFICATION_ROOT + "control-attempt-01/receipt.json",
            "sha256": "a" * 64,
        }
        relocated_qualification._check_new_root_reference(good)
        for path in (
            "reports/releases/v0.9.2/qualification/old-receipt.json",
            relocated_qualification.QUALIFICATION_ROOT + "../old-receipt.json",
            "/tmp/receipt.json",
            relocated_qualification.QUALIFICATION_ROOT[:-1] + "-near-miss/receipt.json",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                relocated_qualification._check_new_root_reference({"path": path, "sha256": "a" * 64})

    def test_shared_receipt_replay_runs_with_temporary_exact_root(self):
        original_root = v092_qualification.QUALIFICATION_ROOT
        observed = []

        def stub(root, plan, reference, *, group_id):
            observed.append(v092_qualification.QUALIFICATION_ROOT)
            return {"status": "replayed"}, root / reference["path"]

        with patch.object(v092_qualification, "validate_common_receipt", side_effect=stub):
            result = relocated_qualification.validate_common_receipt(
                ROOT,
                {},
                {
                    "path": relocated_qualification.QUALIFICATION_ROOT + "attempt-01/receipt.json",
                    "sha256": "b" * 64,
                },
                group_id="joern-swift-common108",
            )
        self.assertEqual(result[0]["status"], "replayed")
        self.assertEqual(observed, [relocated_qualification.QUALIFICATION_ROOT])
        self.assertEqual(v092_qualification.QUALIFICATION_ROOT, original_root)

    def test_old_receipt_cannot_be_reused_even_with_matching_digest(self):
        with self.assertRaisesRegex(ValueError, "must use the v0.9.2-02 preparation root"):
            relocated_qualification.validate_common_receipt(
                ROOT,
                {},
                {
                    "path": "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-04/qualification-receipt-02.json",
                    "sha256": "c" * 64,
                },
                group_id="joern-swift-common108",
            )

    def test_wrong_receipt_identity_is_rejected_by_shared_validator(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = Path(relocated_qualification.QUALIFICATION_ROOT) / "attempt-01" / "receipt.json"
            path = root / relative
            path.parent.mkdir(parents=True)
            evidence = {
                "schema": "analyzer-qualification-receipt/v092",
                "status": "qualified",
                "execution_eligible": True,
                "group_id": "joern-swift-common108",
                "groups": ["joern-swift-common108"],
                "population_sha256": "population",
                "fixture_revision": "fixture",
                "identity": {"tool": "wrong-joern-build"},
            }
            raw = json.dumps(evidence).encode()
            path.write_bytes(raw)
            reference = {"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
            plan = {
                "population_sha256": "population",
                "fixture_revision": "fixture",
                "identity": {"tool": "expected-joern-build"},
            }
            with self.assertRaisesRegex(ValueError, "qualification analyzer identity mismatch"):
                relocated_qualification.validate_common_receipt(
                    root, plan, reference, group_id="joern-swift-common108"
                )

    def test_pending_plan_preserves_frozen_population_and_control_limits(self):
        pending_path = ROOT / runner.PENDING_EXECUTION_PLAN_PATH
        control_ref_path = ROOT / "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/qualification/control-plan-05.json"
        pending = json.loads(pending_path.read_text())
        old = json.loads((ROOT / "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json").read_text())
        control = json.loads(control_ref_path.read_text())
        old_control = json.loads((ROOT / "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-04.json").read_text())

        self.assertEqual(set(pending["cases"]), set(old["cases"]))
        self.assertEqual(pending["cases"], old["cases"])
        self.assertEqual(pending["phase_sequence"], old["phase_sequence"])
        self.assertEqual(pending["execution_contract"], old["execution_contract"])
        self.assertEqual(pending["query_root"], old["query_root"])
        self.assertEqual(pending["output_root"], old["output_root"])
        self.assertEqual(pending["identity"]["tool_build_identity"], old["identity"]["tool_build_identity"])
        self.assertEqual(sum(row["disposition"] == "unsupported" for row in pending["cases"].values()), 12)
        self.assertEqual(pending["status"], "qualification-pending")
        self.assertIs(pending["execution_eligible"], False)
        self.assertIs(pending["diagnostic_execution_eligible"], False)
        self.assertIs(pending["full_model_qualification"], False)
        self.assertNotIn("fresh_qualification", pending)

        self.assertEqual(control["controls"], old_control["controls"])
        self.assertEqual(control["arms"], ["off", "on"])
        self.assertEqual(control["case_arm_count"], 12)
        self.assertEqual(control["maximum_phase_invocations"], 36)
        self.assertEqual(control["case_arm_budget_seconds"], 75)
        self.assertEqual(control["total_budget_seconds"], 900)
        self.assertEqual(control["scratch_allowance_bytes"], 4 * 1024**3)
        self.assertEqual(control["diagnostic_admission"]["strict_model_qualification"]["failed_case_arm_count"], 8)
        self.assertFalse(control["diagnostic_admission"]["strict_model_qualification"]["full_model_qualification"])

        projection = v092_qualification.plan_projection_sha256(pending)
        self.assertEqual(pending["qualification_control_projection_sha256"], projection)
        self.assertEqual(control["execution_plan_projection_sha256"], projection)
        self.assertEqual(pending["qualification_control_plan"]["path"], control_ref_path.relative_to(ROOT).as_posix())
        self.assertEqual(pending["qualification_control_plan"]["sha256"], hashlib.sha256(control_ref_path.read_bytes()).hexdigest())

    def test_pending_plan_binds_relocated_runtime_manifests_and_helpers(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        refs = {row["path"]: row["sha256"] for row in pending["configurations"]["joern-current108"]}
        expected = {
            "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/joern.json",
            "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/java.json",
            "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated.json",
            "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
            "reports/releases/v0.9.2/acquisition/runtime-manifests/joern.json",
            "reports/releases/v0.9.2/acquisition/runtime-manifests/java.json",
            "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-6.3.3.json",
            "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-sdk-26.5.json",
            "scripts/joern_normal_runner_v092_relocated.py",
            "scripts/run-joern-common-v092-relocated.py",
            "scripts/v092_relocated_qualification.py",
            "scripts/joern_diagnostic_admission_v092_relocated.py",
        }
        self.assertTrue(expected <= set(refs))
        for relative in expected:
            self.assertEqual(refs[relative], hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        self.assertEqual(
            pending["runtime"]["compiler_root"],
            "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-swift-repair-20261122-01/expanded/swift-6.3.3-RELEASE-osx-package.pkg/swift-6.3.3-RELEASE-osx-package.pkg/Payload/usr",
        )
        self.assertEqual(pending["runtime"]["joern_root"], "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-runtime-20261114-01/joern/joern-cli")
        self.assertEqual(pending["runtime"]["java_home"], "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-runtime-20261114-01/jvm/jdk-21.0.8-tem")
        old = json.loads((ROOT / "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json").read_text())
        self.assertEqual(pending["runtime"]["inventories"], old["runtime"]["inventories"])

    def test_configuration_closure_retains_frozen_list_and_exact_approved_additions(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        old = json.loads((ROOT / relocated_admission.HISTORICAL_PLAN_PATH).read_text())
        old_rows = old["configurations"]["joern-current108"]
        new_rows = pending["configurations"]["joern-current108"]
        self.assertEqual(len(old_rows), 33)
        self.assertEqual(new_rows[:33], old_rows)
        self.assertEqual(
            [row["path"] for row in new_rows[33:]],
            list(relocated_admission.APPROVED_CONFIG_ADDITIONS),
        )
        self.assertEqual(len({row["path"] for row in new_rows}), 44)
        relocated_admission._validate_configuration_closure(ROOT, old, pending)

    def test_configuration_closure_rejects_removed_changed_duplicate_and_extra_refs(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        old = json.loads((ROOT / relocated_admission.HISTORICAL_PLAN_PATH).read_text())
        near_misses = {}

        removed = copy.deepcopy(pending)
        removed["configurations"]["joern-current108"].pop(0)
        near_misses["removed old ref"] = removed

        changed = copy.deepcopy(pending)
        changed["configurations"]["joern-current108"][0]["sha256"] = "0" * 64
        near_misses["changed old ref digest"] = changed

        duplicate = copy.deepcopy(pending)
        duplicate["configurations"]["joern-current108"].append(
            duplicate["configurations"]["joern-current108"][-1]
        )
        near_misses["duplicate ref"] = duplicate

        extra = copy.deepcopy(pending)
        extra["configurations"]["joern-current108"].append(
            {"path": "scripts/unreviewed-joern-helper.py", "sha256": "a" * 64}
        )
        near_misses["unapproved extra"] = extra

        changed_addition = copy.deepcopy(pending)
        changed_addition["configurations"]["joern-current108"][33]["sha256"] = "b" * 64
        near_misses["changed approved addition"] = changed_addition

        for label, candidate in near_misses.items():
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "configuration"):
                relocated_admission._validate_configuration_closure(ROOT, old, candidate)

    def test_query_root_is_frozen_across_runtime_rebinding(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        changed = copy.deepcopy(pending)
        changed["query_root"] = "adapters/joern/swift-common-v2/unreviewed-query"
        with self.assertRaisesRegex(ValueError, "changed frozen analyzer"):
            relocated_admission.validate_component_rebinding(ROOT, changed)

    def test_modified_control_projection_is_not_accepted_by_static_binding(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        modified = copy.deepcopy(pending)
        modified["runtime"]["compiler"] += ".unexpected"
        self.assertNotEqual(
            v092_qualification.plan_projection_sha256(modified),
            pending["qualification_control_projection_sha256"],
        )

    def test_path_rebinding_requires_exact_manifests_and_replays_history_against_v01(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        control_path = ROOT / pending["qualification_control_plan"]["path"]
        control = json.loads(control_path.read_text())
        old_plan = relocated_admission.validate_component_rebinding(ROOT, pending)
        self.assertEqual(old_plan["identity"], pending["identity"])
        admission = relocated_admission.validate_control_plan_admission(ROOT, pending, control)
        self.assertEqual(admission["schema"], "joern-diagnostic-admission/v1")

    def test_manifest_file_mode_symlink_and_external_mutations_fail_closed(self):
        old_path = ROOT / "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-6.3.3.json"
        new_path = ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated.json"
        old = json.loads(old_path.read_text())
        new = json.loads(new_path.read_text())
        mutations = {
            "file digest": lambda value: value["files"][0].__setitem__("sha256", "0" * 64),
            "file mode": lambda value: value["files"][0].__setitem__("mode", value["files"][0]["mode"] ^ 1),
            "symlink target": lambda value: value["symlinks"][0].__setitem__("target", "changed-target"),
            "symlink mode": lambda value: value["symlinks"][0].__setitem__("mode", value["symlinks"][0]["mode"] ^ 1),
            "external dependency": lambda value: value["external_files"].append("/unexpected/external"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(new)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    relocated_admission._validate_rebased_inventory(
                        old, changed, old["root"], new["root"], "swift-toolchain"
                    )

    def test_rebinding_validation_works_from_a_separate_prepared_source_root(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        control_path = ROOT / pending["qualification_control_plan"]["path"]
        control = json.loads(control_path.read_text())
        relatives = {
            relocated_admission.HISTORICAL_PLAN_PATH,
            relocated_admission.JOERN_JAVA_RELOCATION_RECEIPT,
            relocated_admission.SWIFT_RELOCATION_RECEIPT,
            relocated_admission.SWIFT_VERIFICATION_RECEIPT,
            "scripts/joern_diagnostic_admission_v092.py",
            "scripts/joern_diagnostic_admission_v092_relocated.py",
            "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-02.json",
            control["diagnostic_admission"]["prior_control_run"]["path"],
            control["diagnostic_admission"]["prior_registration_archive"]["path"],
        }
        for item in relocated_admission.COMPONENTS.values():
            relatives.add(item["old_manifest"])
            relatives.add(item["new_manifest"])
            relatives.add(pending["runtime"]["inventories"][item["runtime_key"]]["path"])
        relatives.update(relocated_admission.APPROVED_CONFIG_ADDITIONS)
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            for relative in relatives:
                source = ROOT / relative
                destination = source_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            old_plan = relocated_admission.validate_component_rebinding(source_root, pending)
            admission = relocated_admission.validate_control_plan_admission(
                source_root, pending, control
            )
        self.assertEqual(old_plan["identity"], pending["identity"])
        self.assertEqual(admission["schema"], "joern-diagnostic-admission/v1")

    def test_command_and_scalar_identity_path_drift_fail_closed(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        changed = copy.deepcopy(pending)
        changed["runtime"]["compiler"] += ".wrong-driver"
        with self.assertRaisesRegex(ValueError, "runtime commands or non-path settings"):
            relocated_admission.validate_component_rebinding(ROOT, changed)
        changed = copy.deepcopy(pending)
        changed["runtime"]["engine_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "scalar digest"):
            relocated_admission.validate_component_rebinding(ROOT, changed)

    def test_current_raw_replay_keeps_v02_components_while_history_uses_v01(self):
        pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
        control_path = ROOT / pending["qualification_control_plan"]["path"]
        control = json.loads(control_path.read_text())
        observed = {}

        def historical_check(root, plan, selected_control):
            observed["historical_components"] = plan["identity_components"]
            return {"status": "historical-check"}

        with patch.object(relocated_admission, "_ORIGINAL_VALIDATE_CONTROL_PLAN_ADMISSION", side_effect=historical_check):
            result = relocated_admission.validate_control_plan_admission(ROOT, pending, control)
        old_plan = json.loads((ROOT / relocated_admission.HISTORICAL_PLAN_PATH).read_text())
        self.assertEqual(result["status"], "historical-check")
        self.assertEqual(observed["historical_components"], old_plan["identity_components"])
        self.assertNotEqual(observed["historical_components"], pending["identity_components"])

        replay_observed = {}

        def current_replay(root, plan, selected_control, run, observations, cases, case_paths):
            replay_observed["plan"] = plan
            return {"status": "current-replay"}

        with patch.object(relocated_admission, "_ORIGINAL_REPLAY_ADMISSION", side_effect=current_replay):
            replay = relocated_admission.replay_admission(
                ROOT, pending, control, {}, {}, {}, {}
            )
        self.assertEqual(replay["status"], "current-replay")
        self.assertIs(replay_observed["plan"], pending)
        self.assertEqual(replay_observed["plan"]["identity_components"], pending["identity_components"])


if __name__ == "__main__":
    unittest.main()
