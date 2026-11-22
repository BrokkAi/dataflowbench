"""Focused capability-source and closure checks for the v0.9.2 plan-v092-03 runner."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import joern_normal_runner_v092_capability as runner
import joern_diagnostic_admission_v092_capability as admission
import v092_capability_qualification as qualification


OLD_PLAN_PATH = ROOT / "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
V090_PLAN_PATH = ROOT / runner.CAPABILITY_SOURCE_PLAN_PATH


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class CapabilityPlanTests(unittest.TestCase):
    def setUp(self):
        self.pending = read_json(ROOT / runner.PENDING_EXECUTION_PLAN_PATH)
        self.old = read_json(OLD_PLAN_PATH)

    def test_plan03_preserves_original_cases_and_exact_configuration_closure(self):
        previous = read_json(
            ROOT / "adapters/joern/swift-common-v2/plan-v092-03/qualification-pending-plan-03.json"
        )
        self.assertEqual(self.pending["cases"], previous["cases"])
        old_rows = self.old["configurations"]["joern-current108"]
        new_rows = self.pending["configurations"]["joern-current108"]
        self.assertEqual(len(old_rows), 33)
        self.assertEqual(new_rows[:33], old_rows)
        self.assertEqual(
            [row["path"] for row in new_rows[33:]],
            list(admission.APPROVED_CONFIG_ADDITIONS),
        )
        self.assertEqual(len(new_rows), 45)
        admission._validate_configuration_closure(ROOT, self.old, self.pending)
        admission.validate_component_rebinding(ROOT, self.pending)

    def test_configuration_closure_rejects_missing_changed_duplicate_and_reordered_refs(self):
        mutations = {
            "missing old reference": lambda value: value["configurations"]["joern-current108"].pop(0),
            "changed old digest": lambda value: value["configurations"]["joern-current108"][0].__setitem__("sha256", "0" * 64),
            "duplicate reference": lambda value: value["configurations"]["joern-current108"].append(
                value["configurations"]["joern-current108"][-1]
            ),
            "unapproved reference": lambda value: value["configurations"]["joern-current108"].append(
                {"path": "scripts/unreviewed.py", "sha256": "a" * 64}
            ),
            "reordered additions": lambda value: value["configurations"]["joern-current108"].__setitem__(
                slice(33, 35),
                list(reversed(value["configurations"]["joern-current108"][33:35])),
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.pending)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, "configuration"):
                    admission._validate_configuration_closure(ROOT, self.old, changed)

    def test_preflight_binds_exactly_96_attempt_capabilities_and_12_unsupported(self):
        binding = qualification.validate_capability_binding(ROOT, self.pending)
        self.assertEqual(binding["schema"], "joern-v092-capability-binding/v2")
        self.assertEqual(binding["source"], {
            "path": runner.CAPABILITY_SOURCE_PLAN_PATH,
            "sha256": runner.CAPABILITY_SOURCE_PLAN_SHA256,
        })
        self.assertEqual(binding["attempt_count"], 96)
        self.assertEqual(binding["unsupported_count"], 12)
        self.assertEqual(len(binding["capabilities"]), 96)
        self.assertEqual(len(binding["unsupported_decisions"]), 12)
        self.assertEqual(len(binding["historical_unsupported_decisions"]), 12)
        self.assertTrue(all(value == runner.EXPECTED_CAPABILITY for value in binding["capabilities"].values()))
        self.assertEqual(
            set(binding["unsupported_decisions"]),
            {case_id for case_id, row in self.pending["cases"].items() if row["disposition"] == "unsupported"},
        )

    def test_capability_preflight_occurs_before_control_validation_or_engine_creation(self):
        with patch.object(runner, "_validate_control_plan") as controls, \
             patch.object(runner, "_engine") as engine, \
             patch.object(runner, "_load_bound_capabilities", side_effect=ValueError("capability blocked")) as preflight:
            with self.assertRaisesRegex(ValueError, "capability blocked"):
                runner.validate_plan(
                    ROOT, runner.PENDING_EXECUTION_PLAN_PATH,
                    allow_qualification_pending=True,
                )
            preflight.assert_called_once()
            controls.assert_not_called()
            engine.assert_not_called()

    def test_source_reference_must_be_unique_and_exact(self):
        for label, mutate in (
            ("missing", lambda rows: rows.remove(next(row for row in rows if row["path"] == runner.CAPABILITY_SOURCE_PLAN_PATH))),
            ("duplicate", lambda rows: rows.append(copy.deepcopy(next(row for row in rows if row["path"] == runner.CAPABILITY_SOURCE_PLAN_PATH)))),
            ("wrong digest", lambda rows: next(row for row in rows if row["path"] == runner.CAPABILITY_SOURCE_PLAN_PATH).__setitem__("sha256", "0" * 64)),
        ):
            with self.subTest(label=label):
                changed = copy.deepcopy(self.pending)
                mutate(changed["configurations"]["joern-current108"])
                with self.assertRaisesRegex(ValueError, "capability source"):
                    runner.validate_capability_binding(ROOT, changed)

    def test_missing_changed_or_activated_historical_capability_fails_closed(self):
        first_attempt = next(
            case_id for case_id, row in self.pending["cases"].items()
            if row["disposition"] == "attempt"
        )
        mutations = {
            "missing capability": lambda source: source["cases"][first_attempt].pop("capability"),
            "model activated": lambda source: source["cases"][first_attempt]["capability"].__setitem__("model_mode", "on"),
            "wrong gate": lambda source: source["cases"][first_attempt]["capability"].__setitem__("identity_gate", "approximate"),
            "extra field": lambda source: source["cases"][first_attempt]["capability"].__setitem__("inferred", True),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                source = read_json(V090_PLAN_PATH)
                mutate(source)
                temp_root = Path(temporary)
                source_digest = write_json(temp_root / runner.CAPABILITY_SOURCE_PLAN_PATH, source)
                plan = copy.deepcopy(self.pending)
                ref = next(
                    row for row in plan["configurations"]["joern-current108"]
                    if row["path"] == runner.CAPABILITY_SOURCE_PLAN_PATH
                )
                ref["sha256"] = source_digest
                with patch.object(runner, "CAPABILITY_SOURCE_PLAN_SHA256", source_digest):
                    with self.assertRaisesRegex(ValueError, "capability|unsupported"):
                        runner.validate_capability_binding(temp_root, plan)

    def test_full_raw_replay_verifies_capability_and_unsupported_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp_root = Path(temporary)
            source_destination = temp_root / runner.CAPABILITY_SOURCE_PLAN_PATH
            source_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(V090_PLAN_PATH, source_destination)
            source_plan = read_json(V090_PLAN_PATH)
            binding = qualification.validate_capability_binding(ROOT, self.pending)
            for decision in binding["unsupported_decisions"].values():
                source = ROOT / decision["path"]
                destination = temp_root / decision["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)

            result_rows = []
            for case_id, selection in self.pending["cases"].items():
                raw = {"case_id": case_id, "configuration": selection["configuration"]}
                if selection["disposition"] == "attempt":
                    raw.update(
                        capability=runner.EXPECTED_CAPABILITY,
                        capability_source={
                            "path": runner.CAPABILITY_SOURCE_PLAN_PATH,
                            "sha256": runner.CAPABILITY_SOURCE_PLAN_SHA256,
                            "case_id": case_id,
                        },
                    )
                else:
                    disposition_ref = binding["unsupported_decisions"][case_id]
                    record = read_json(ROOT / disposition_ref["path"])
                    historical_ref = record["historical_decision"]
                    raw.update(
                        raw_outcome="unsupported",
                        state="unsupported",
                        executed=False,
                        duration_ms=0,
                        total_elapsed_seconds=0,
                        decision_sha256=disposition_ref["sha256"],
                        historical_decision_sha256=historical_ref["sha256"],
                        disposition_sha256=disposition_ref["sha256"],
                        unsupported_provenance={**disposition_ref, "case_id": case_id},
                        diagnostics=[record["historical_reason"]],
                    )
                relative = f"{runner.CASE_OUTPUT_RELATIVE}/{case_id}/raw.json"
                raw_path = temp_root / relative
                raw_digest = write_json(raw_path, raw)
                result_rows.append({
                    "case_id": case_id,
                    "configuration": selection["configuration"],
                    "raw": {"path": relative, "sha256": raw_digest},
                })

            run = {"results": result_rows}
            with patch.object(runner, "validate_capability_binding", return_value=binding):
                verified = qualification.verify_raw_capability_rows(temp_root, self.pending, run)
            self.assertEqual(verified["status"], "verified")
            self.assertEqual(verified["attempt_count"], 96)
            self.assertEqual(verified["unsupported_count"], 12)
            self.assertEqual(verified["raw_rows"], 108)

            attempt_id = next(
                case_id for case_id, row in self.pending["cases"].items()
                if row["disposition"] == "attempt"
            )
            raw_ref = next(row["raw"] for row in result_rows if row["case_id"] == attempt_id)
            fresh_raw_path = raw_ref["path"]
            raw_ref["path"] = fresh_raw_path.replace("current108-v092-03", "current108-v092-02")
            with patch.object(runner, "validate_capability_binding", return_value=binding), \
                 self.assertRaisesRegex(ValueError, "fresh v0.9.2-03 output namespace"):
                qualification.verify_raw_capability_rows(temp_root, self.pending, run)
            raw_ref["path"] = fresh_raw_path

            changed_raw = read_json(temp_root / raw_ref["path"])
            changed_raw["capability"]["model_mode"] = "on"
            raw_ref["sha256"] = write_json(temp_root / raw_ref["path"], changed_raw)
            with patch.object(runner, "validate_capability_binding", return_value=binding), \
                 self.assertRaisesRegex(ValueError, "raw capability"):
                qualification.verify_raw_capability_rows(temp_root, self.pending, run)

            changed_raw["capability"]["model_mode"] = "off"
            changed_raw["capability_source"]["case_id"] = "wrong-case"
            raw_ref["sha256"] = write_json(temp_root / raw_ref["path"], changed_raw)
            with patch.object(runner, "validate_capability_binding", return_value=binding), \
                 self.assertRaisesRegex(ValueError, "raw capability"):
                qualification.verify_raw_capability_rows(temp_root, self.pending, run)

    def test_decline_map_and_failure_policy_are_exact_and_preflighted(self):
        qualification.validate_capability_binding(ROOT, self.pending)
        for label, mutate in (
            ("missing disposition", lambda value: value["unsupported_decisions"].pop(next(iter(value["unsupported_decisions"])))),
            ("wrong current identity", lambda value: value.__setitem__("identity", {"tool_version": "4.0.628"})),
            ("wrong failure policy", lambda value: value["failure_policy"].__setitem__("sha256", "0" * 64)),
        ):
            with self.subTest(label=label):
                changed = copy.deepcopy(self.pending)
                mutate(changed)
                with self.assertRaises(ValueError):
                    qualification.validate_capability_binding(ROOT, changed)


class FailStopTests(unittest.TestCase):
    def _raw_with_command(self, root: Path, *, exit_status=0, timed_out=False,
                          cleanup="tracked-processes-stopped", outcome="inconclusive",
                          phase_count=1, elapsed=1.0, deadline=75.0):
        command_refs = []
        for index in range(phase_count):
            command_path = root / f"phase-{index}.command.json"
            command_ref = {"path": command_path.relative_to(root).as_posix(),
                           "sha256": write_json(command_path, {
                               "phase_id": ("typecheck", "frontend", "query")[index],
                               "role": "analysis",
                               "exit_status": exit_status,
                               "timed_out": timed_out,
                               "cleanup_status": cleanup,
                               "elapsed_seconds": elapsed,
                               "deadline_seconds": deadline,
                           })}
            command_refs.append(command_ref)
        return {"raw_outcome": outcome, "commands": command_refs}

    def test_nonzero_command_fail_stops_even_when_runner_stop_flag_is_false(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = self._raw_with_command(root, exit_status=1)
            with self.assertRaisesRegex(ValueError, "phase command failed"):
                runner._require_case_continuation(root, raw, False)

    def test_timeout_and_uncertain_cleanup_fail_stop(self):
        for kwargs in ({"timed_out": True}, {"cleanup": "uncertain"}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                raw = self._raw_with_command(root, **kwargs)
                with self.assertRaisesRegex(ValueError, "phase command failed"):
                    runner._require_case_continuation(root, raw, False)

    def test_successful_incomplete_semantics_and_short_successful_phase_prefix_continue(self):
        for phase_count in (2, 3):
            with self.subTest(phase_count=phase_count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                raw = self._raw_with_command(root, outcome="inconclusive", phase_count=phase_count)
                runner._require_case_continuation(root, raw, False)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = self._raw_with_command(root, elapsed=float("nan"))
            with self.assertRaisesRegex(ValueError, "phase command failed"):
                runner._require_case_continuation(root, raw, False)

    def test_stop_flag_is_honored_after_raw_and_run_checkpoint_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = self._raw_with_command(root)
            raw_path = root / "raw.json"
            raw_path.write_text(json.dumps(raw))
            run_path = root / "run.json"
            run_path.write_text(json.dumps({"results": [{"raw": raw_path.name}]}))
            with self.assertRaisesRegex(ValueError, "runner requested fail-stop"):
                runner._require_case_continuation(root, raw, True)
            self.assertTrue(raw_path.is_file())
            self.assertTrue(run_path.is_file())

    def test_execute_checkpoints_raw_and_run_before_stopping_on_nonzero_phase(self):
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_id = "dfb-taint-swift-test-case"
            case_path = root / "cases/taint/swift/test/case.json"
            case_path.parent.mkdir(parents=True)
            case_path.write_text("{}\n")
            output = root / "reports/raw/joern-common-v2/attempt-01"
            output.parent.mkdir(parents=True)
            identity = {"tool": "joern", "tool_version": "4.0.660"}

            class FakeProcess:
                def run(self, argv, directory, name, timeout, *, env, cwd):
                    (directory / "version.stdout").write_text("Joern 4.0.660\n")
                    return {"exit_status": 0, "timed_out": False,
                            "cleanup_status": "tracked-processes-stopped"}

            class FakeEngine:
                process = FakeProcess()

                @staticmethod
                def env_for(runtime):
                    return {}

                def run_case(self, selected_root, plan, selected_case_path, case, leaf, mode):
                    leaf.mkdir(parents=True)
                    command_path = leaf / "typecheck.command.json"
                    digest = write_json(command_path, {
                        "phase_id": "typecheck", "role": "analysis",
                        "exit_status": 9, "timed_out": False,
                        "cleanup_status": "tracked-processes-stopped",
                        "elapsed_seconds": 1.0, "deadline_seconds": 75.0,
                    })
                    ref = {"path": command_path.relative_to(selected_root).as_posix(),
                           "sha256": digest}
                    return ({"raw_outcome": "inconclusive", "state": "inconclusive",
                             "duration_ms": 1000, "total_elapsed_seconds": 1.0,
                             "diagnostics": ["CommandFailed:typecheck"],
                             "witness_checkpoints": [], "executed": True,
                             "commands": [ref], "native_outputs": []}, False)

            plan = {
                "output_root": "reports/raw/joern-common-v2",
                "runtime": {"joern": "/unused/joern"},
                "identity": identity,
                "fresh_qualification": {"sha256": "a" * 64},
                "cases": {case_id: {"configuration": "joern-current108",
                                    "disposition": "attempt"}},
            }
            write_json(root / runner.FINAL_EXECUTION_PLAN_PATH, plan)
            context = {
                "engine": FakeEngine(),
                "cases": {case_id: {"fixture_files": ["main.swift"]}},
                "capabilities": {case_id: runner.EXPECTED_CAPABILITY},
                "unsupported_decisions": {},
                "historical_unsupported_decisions": {},
                "capability_source": {"path": runner.CAPABILITY_SOURCE_PLAN_PATH,
                                      "sha256": runner.CAPABILITY_SOURCE_PLAN_SHA256},
            }
            population = {"fixture_revision": "test-fixture-revision"}
            common_rows = [{"id": case_id, "path": case_path.relative_to(root).as_posix()}]
            with patch.object(runner, "validate_plan", return_value=(plan, {}, context)), \
                 patch.object(runner, "_require_launch_guard"), \
                 patch.object(runner.common, "load_common_population",
                              return_value=(population, common_rows, [], {}, "population")), \
                 patch.object(runner.shutil, "disk_usage",
                              return_value=SimpleNamespace(free=130 * 1024**3)):
                with self.assertRaisesRegex(ValueError, "phase command failed"):
                    runner.execute(root, runner.FINAL_EXECUTION_PLAN_PATH, output)

            raw_path = output / case_id / "raw.json"
            run_path = output / "run.json"
            self.assertTrue(raw_path.is_file())
            self.assertTrue(run_path.is_file())
            saved_run = read_json(run_path)
            self.assertEqual(len(saved_run["results"]), 1)
            self.assertEqual(saved_run["results"][0]["raw"]["sha256"],
                             hashlib.sha256(raw_path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
