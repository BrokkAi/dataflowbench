from __future__ import annotations

import contextlib
import ast
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import history
import packet
import protocol
import stage_runtime
import bridge
import supervisor


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _native_acceptance() -> dict:
    diagnostic_ref = {"path": "diagnostic/review.json", "sha256": "d" * 64}
    return {
        "eligible_plan": {
            "status": "execution-eligible",
            "execution_eligible": True,
            "diagnostic_execution_eligible": True,
            "full_model_qualification": False,
            "scored_activation": False,
            "identity": {"tool_version": "4.0.660"},
            "fresh_qualification": {"path": "qualification/receipt.json", "sha256": "e" * 64},
        },
        "eligible_plan_ref": {"path": "eligible/plan.json", "sha256": "f" * 64},
        "qualification": {
            "control_run": {"arms": 12},
            "diagnostic_admission_review": diagnostic_ref,
            "native_capture": {
                "control_arms": 12,
                "phase_invocations": 36,
                "full_model_qualification": False,
                "scored_activation": False,
            },
        },
        "finalization": {"qualification_receipt": {"path": "qualification/receipt.json", "sha256": "e" * 64}},
        "diagnostic_review": {"control_run": {"arms": 12}},
        "diagnostic_review_ref": diagnostic_ref,
    }


def _current_plan() -> tuple[dict, list[dict]]:
    cases = [f"case-{i:03}" for i in range(108)]
    partitions = [cases[:22], cases[22:44], cases[44:66], cases[66:87], cases[87:]]
    reports = [{"path": f"reports/joern-{i}.json", "case_ids": values}
               for i, values in enumerate(partitions)]
    group = {"id": protocol.GROUP, "tool": "joern", "case_ids": cases,
             "reports": reports}
    plan = {"source_commit": "a" * 40, "groups": [group]}
    current = {"validated": {"bytes_sha256": "b" * 64, "plan": plan},
               "source_commit": "a" * 40, "plan_commit": "c" * 40}
    bindings = [{
        "adapter": report["path"],
        "staged_path": f"reports/{i}.json",
        "sha256": f"{i + 1:064x}",
        "rows": len(report["case_ids"]),
        "attempt_id": protocol.ATTEMPT,
        "attempt_number": 5,
        "evidence_contract_sha256": "b" * 64,
    } for i, report in enumerate(reports)]
    return current, bindings


def _terminal_row(current: dict) -> dict:
    return {
        "tool": "joern",
        "group_id": protocol.GROUP,
        "attempt_id": protocol.ATTEMPT,
        "source_commit": current["source_commit"],
        "plan_commit": current["plan_commit"],
        "contract_sha256": current["validated"]["bytes_sha256"],
        "execution_series": 2,
        "status": "completed",
        "exit_code": 0,
        "timed_out": False,
        "capacity_loss": None,
        "recorder_error": None,
        "process_ownership": {
            "schema": "invocation-process-ownership/v1",
            "cleanup_status": "tracked-processes-stopped",
            "descendant_containment": "unproven",
            "tracking_interval_seconds": 2.0,
            "root_pid": 24680,
            "tracked_processes": [{"pid": 24680, "start_identity": "birth-24680"}],
        },
    }


def _global_attempt_annex() -> list[dict]:
    return [{"global_attempt_number": number} for number in range(111, 132)]


def _tail_proof(row: dict) -> dict:
    return {
        "row": copy.deepcopy(row),
        "physical_ledger_row": 131,
        "global_attempt_number": 132,
        "status": row["status"],
        "completion_claim": False,
        "eligible": False,
    }


class FrozenRunnerEntrypointTests(unittest.TestCase):
    def _wrapper(self):
        path = Path(__file__).with_name("run-joern-common-v092.py")
        spec = importlib.util.spec_from_file_location("joern05_task_entrypoint_test", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_wrapper_pins_exact_observer08_outside_the_seven_module_graph(self):
        wrapper = self._wrapper()
        observer = Path(__file__).parents[2] / "joern-native-startup-observer-08.py"
        self.assertEqual(wrapper.OBSERVER_PATH,
                         "reports/releases/v0.9.2/acquisition/joern-native-startup-observer-08.py")
        self.assertEqual(wrapper.OBSERVER_SHA256, sha(observer.read_bytes()))
        self.assertNotIn("run-joern-common-v092", bridge.ADAPTER_NAMES)
        loaded = wrapper.load_observer()
        self.assertEqual(Path(loaded.__file__), observer.resolve())
        self.assertTrue(callable(loaded.main))

    def test_wrapper_forwards_the_full_cli_vector_without_engine_execution(self):
        wrapper = self._wrapper()
        arguments = [
            "controls", "--root", "/retained/checkout", "--plan", "plan.json",
            "--evidence", "evidence.json", "--output", "attempt/capture.json",
            "--plan-sha256", "a" * 64, "--evidence-sha256", "b" * 64,
        ]
        received = []

        class FakeObserver:
            @staticmethod
            def main(argv):
                received.append(list(argv))
                return 23

        with mock.patch.object(wrapper, "load_observer", return_value=FakeObserver()):
            with mock.patch.object(wrapper.sys, "argv", ["renamed-entrypoint"] + arguments):
                self.assertEqual(wrapper.main(), 23)
        self.assertEqual(received, [arguments])

    def test_exact_execute_guard_and_near_misses(self):
        wrapper = self._wrapper()
        root = Path(__file__).parents[6].resolve()
        attempt = root / wrapper.ATTEMPT_CWD
        environment = {
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
            "DATAFLOWBENCH_V092_GROUP_ID": wrapper.GROUP_ID,
        }
        argv = wrapper._expected_execute_argv(root)
        checked_root, output = wrapper._validate_execute_invocation(
            argv, attempt_root=attempt, cwd=attempt, environment=environment)
        self.assertEqual(checked_root, root)
        self.assertEqual(output, attempt / wrapper.CLI_OUTPUT)

        bad = list(argv)
        bad[-1] = "reports/raw/joern-common-v2/other"
        with self.assertRaisesRegex(RuntimeError, "reviewed Joern05 command"):
            wrapper._validate_execute_invocation(
                bad, attempt_root=attempt, cwd=attempt, environment=environment)
        with self.assertRaisesRegex(RuntimeError, "working directory"):
            wrapper._validate_execute_invocation(
                argv, attempt_root=attempt, cwd=attempt / "near-miss",
                environment=environment)
        with self.assertRaisesRegex(RuntimeError, "environment markers"):
            wrapper._validate_execute_invocation(
                argv, attempt_root=attempt, cwd=attempt,
                environment={"DATAFLOWBENCH_V092_GROUP_ID": wrapper.GROUP_ID})

    def test_scoped_runner_copy_preserves_original_validation_and_restores(self):
        wrapper = self._wrapper()
        root = Path(__file__).parents[6].resolve()
        plan = json.loads((root / wrapper.PLAN_PATH).read_bytes())
        evidence = {"sealed": True}
        context = object()
        output = root / wrapper.ATTEMPT_CWD / "disposable-probe-output"
        calls = []

        class Runner:
            def validate_plan(self, candidate_root, plan_path):
                calls.append((candidate_root, plan_path))
                return copy.deepcopy(plan), evidence, context

        runner = Runner()
        original_validate = runner.validate_plan

        class Observer:
            __file__ = str(root / wrapper.OBSERVER_PATH)
            execute = staticmethod(lambda *_args, **_kwargs: None)

            @staticmethod
            def _runner_context(candidate_root, _old, _result, _observer):
                return runner, "historical-plan", contextlib.nullcontext()

        result = {"new_plan": plan, "new_plan_path": wrapper.PLAN_PATH,
                  "new_plan_sha256": wrapper.PLAN_SHA256}
        observer = Observer()
        original_context = observer._runner_context
        with wrapper._scoped_observer_output(observer, root, output):
            actual_runner, old_constant, scope = observer._runner_context(
                root, None, result, observer)
            self.assertIs(actual_runner, runner)
            self.assertEqual(old_constant, "historical-plan")
            with scope:
                projected, got_evidence, got_context = runner.validate_plan(
                    root, wrapper.PLAN_PATH)
                self.assertEqual(projected["output_root"],
                                 output.relative_to(root).as_posix())
                self.assertEqual(plan["output_root"], wrapper.ORIGINAL_OUTPUT_ROOT)
                self.assertIs(got_evidence, evidence)
                self.assertIs(got_context, context)
        restored = runner.validate_plan
        self.assertIs(restored.__self__, runner)
        self.assertIs(restored.__func__, Runner.validate_plan)
        self.assertIs(observer._runner_context, original_context)
        self.assertEqual(calls, [(root, wrapper.PLAN_PATH)])

    def _translation_fixture(self, root: Path):
        wrapper = self._wrapper()
        output = root / wrapper.ATTEMPT_CWD / wrapper.CLI_OUTPUT
        normal = output / "normal"
        normal.mkdir(parents=True)
        run_rows = []
        raw_hashes = {}
        for index in range(sum(wrapper.EXPECTED_REPORT_PARTITIONS)):
            case_id = f"dfb-taint-swift-synthetic-{index:03}"
            raw_path = output / case_id / "raw.json"
            raw_path.parent.mkdir(parents=True)
            raw_bytes = json.dumps({"case_id": case_id, "state": "incomplete"}).encode() + b"\n"
            raw_path.write_bytes(raw_bytes)
            raw_hash = sha(raw_bytes)
            raw_hashes[case_id] = raw_hash
            run_rows.append({"case_id": case_id, "raw": {
                "path": raw_path.relative_to(root).as_posix(),
                "sha256": raw_hash,
            }})
        run = {"schema": "joern-common-run/v092", "results": run_rows}
        cursor = 0
        report_paths = []
        for ordinal, size in enumerate(wrapper.EXPECTED_REPORT_PARTITIONS):
            rows = []
            for raw_row in run_rows[cursor:cursor + size]:
                case_id = raw_row["case_id"]
                rows.append({"case_id": case_id, "outcome": "incomplete",
                             "raw_output": raw_row["raw"]["path"],
                             "raw_sha256": raw_hashes[case_id]})
            cursor += size
            report_path = normal / f"report-{ordinal}.json"
            report_path.write_text(json.dumps({"kept": "field", "results": rows}, indent=2) + "\n")
            report_paths.append(report_path)
        raw_before = {row["case_id"]: (output / row["case_id"] / "raw.json").read_bytes()
                      for row in run_rows}
        return wrapper, output, run, report_paths, raw_hashes, raw_before

    def test_snapshot_translation_changes_only_raw_output_values(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-raw-map-") as temp:
            root = Path(temp).resolve()
            (root / "execution-state").mkdir()
            wrapper, output, run, report_paths, raw_hashes, raw_before = \
                self._translation_fixture(root)
            before = [json.loads(path.read_bytes()) for path in report_paths]
            wrapper._translate_report_raw_outputs(root, output, run)
            for index, report_path in enumerate(report_paths):
                after = json.loads(report_path.read_bytes())
                expected = copy.deepcopy(before[index])
                for old_row, new_row in zip(expected["results"], after["results"]):
                    self.assertEqual(new_row["raw_output"],
                                     f"{wrapper.SNAPSHOT_OUTPUT}/{new_row['case_id']}/raw.json")
                    self.assertEqual(new_row["raw_sha256"], raw_hashes[new_row["case_id"]])
                    old_row["raw_output"] = new_row["raw_output"]
                self.assertEqual(after, expected)
            self.assertEqual(raw_before, {
                row["case_id"]: (output / row["case_id"] / "raw.json").read_bytes()
                for row in run["results"]})

    def test_snapshot_translation_rejects_hash_or_membership_drift_before_writes(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-raw-nearmiss-") as temp:
            root = Path(temp).resolve()
            (root / "execution-state").mkdir()
            wrapper, output, run, report_paths, _hashes, _raw = \
                self._translation_fixture(root)
            original_reports = [path.read_bytes() for path in report_paths]
            bad_run = copy.deepcopy(run)
            bad_run["results"][0]["raw"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(RuntimeError, "raw output SHA"):
                wrapper._translate_report_raw_outputs(root, output, bad_run)
            self.assertEqual([path.read_bytes() for path in report_paths], original_reports)

            duplicate_run = copy.deepcopy(run)
            duplicate_run["results"][1]["case_id"] = duplicate_run["results"][0]["case_id"]
            with self.assertRaisesRegex(RuntimeError, "duplicate case"):
                wrapper._translate_report_raw_outputs(root, output, duplicate_run)
            self.assertEqual([path.read_bytes() for path in report_paths], original_reports)


class HistoryBindingTests(unittest.TestCase):
    def test_authority_documents_reject_duplicate_keys_at_every_object_depth(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-duplicate-json-") as temp:
            root = Path(temp).resolve()
            for index, raw in enumerate((
                    b'{"status":"first","status":"second"}\n',
                    b'{"outer":{"status":"first","status":"second"}}\n')):
                path = f"authority/{index}.json"
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                ref = {"path": path, "sha256": sha(raw)}
                with self.subTest(index=index), self.assertRaises(packet.AdapterError):
                    packet.document(root, ref)

    def test_exact130_keeps_c5_annex_separate_from_sealed109_selection(self):
        historical = [{
            "attempt_id": f"old-attempt-{index:03}",
            "group_id": f"old-group-{index:03}",
            "status": "completed",
        } for index in range(109)]
        annex = [{
            "attempt_id": f"c5-attempt-{index:03}",
            "global_attempt_number": 110 + index,
            "group_id": f"c5-group-{index:03}",
            "status": "completed",
        } for index in range(1, 22)]
        historical[-1]["group_id"] = protocol.GROUP
        historical[-1]["status"] = "failed"
        raw = b"".join(canonical(row) for row in historical + annex)
        historical_sha = sha(b"".join(canonical(row) for row in historical))
        annex_sha = sha(b"".join(canonical(row) for row in annex))
        provider = SimpleNamespace(
            LEDGER_ROWS=130,
            LEDGER_RAW_SHA256=sha(raw),
            TOTAL_STATUS_COUNTS={"completed": 129, "failed": 1},
            SEALED109_RAW_SHA256=historical_sha,
            C5_ANNEX_SHA256=annex_sha,
            C5_SOURCE_COMMIT="6" * 40,
            C5_PLAN_COMMIT="7" * 40,
            C5_CONTRACT_SHA256="8" * 64,
        )
        baseline = {
            "schema": "v092-joern05-archived130-history-context/v1",
            "status": "source-only-archived130-baseline-verified",
            "execution_authorized": False,
            "automatic_retry": False,
            "current_live_ledger_validation": "not-performed-by-this-reader",
            "current_source_identity": {"commit": "a" * 40, "tree": "b" * 40},
            "ledger_identity": {"rows": 130, "raw_sha256": sha(raw),
                                "status_counts": provider.TOTAL_STATUS_COUNTS},
            "historical109": {"rows": historical, "sha256": historical_sha},
            "bifrost0144_c5_annex21": {
                "rows": annex, "sha256": annex_sha,
                "global_attempt_numbers": list(range(111, 132)),
            },
            "sealed109_lineage": {
                "source_contexts": {f"context-{i}": {} for i in range(9)},
                "retained20": [], "consumed_events": [],
            },
            "bifrost0144_scala_partial": {
                "group_id": "bifrost-scala-kernel",
                "global_attempt_number": 128,
                "status": "recorder-error", "exit_code": 124,
                "timed_out": True, "completion_claim": False,
                "source_commit": provider.C5_SOURCE_COMMIT,
                "plan_commit": provider.C5_PLAN_COMMIT,
                "contract_sha256": provider.C5_CONTRACT_SHA256,
            },
        }
        current_source = "c" * 40
        current_plan = "d" * 40
        contract_raw = canonical({"source_commit": current_source})
        contract_ref = {"path": "contract/current.json", "sha256": sha(contract_raw)}
        evidence_raw = canonical({"source_commit": current_source,
                                  "plan_commit": current_plan,
                                  "contract_sha256": contract_ref["sha256"]})
        evidence_ref = {"path": "evidence/current.json", "sha256": sha(evidence_raw)}
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-130-") as temp:
            root = Path(temp).resolve()
            for ref, content in ((contract_ref, contract_raw), (evidence_ref, evidence_raw)):
                path = root / ref["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            result = history._combine_live_snapshot(
                root, raw, baseline, provider,
                {"contract": contract_ref, "source_commit": current_source,
                 "plan_commit": current_plan, "source_evidence": evidence_ref},
                {"path": packet.LIVE_LEDGER_PATH, "sha256": sha(raw), "rows": 130})
        self.assertEqual(result["live_ledger"]["rows"], 130)
        self.assertIsNone(result["tail_row131"])
        self.assertEqual(len(result["historical109"]["rows"]), 109)
        self.assertEqual(len(result["bifrost0144_c5_annex21"]["rows"]), 21)
        self.assertEqual(result["bifrost0144_scala_partial"]["status"], "recorder-error")
        self.assertFalse(result["current_target"]["current_target_full"])
        self.assertFalse(set(row["group_id"] for row in annex) &
                         set(result["selected_historical_joern_rows"]))

    def test_current_source_closure_excludes_post_source_evidence_and_review_cycles(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-cas-") as temp:
            root = Path(temp).resolve()
            plan_commit = "b" * 40
            source_commit = "c" * 40
            tree = "d" * 40
            baseline = history.CURRENT_SOURCE_BASELINE_HEAD
            runtime_ref = {"path": "runtime/frozen.py", "sha256": "1" * 64}
            adapter_ref = {"path": "adapter/current.py", "sha256": "2" * 64}
            design_ref = {"path": "qualification/design.json", "sha256": "3" * 64}
            qualification_ref = {"path": "qualification/old-qualification.json", "sha256": "4" * 64}
            runner_ref = {"path": "runner/current.py", "sha256": "5" * 64}
            eligible_ref = {"path": "eligible/plan.json", "sha256": "6" * 64}
            contract_ref = {"path": "contract/current.json", "sha256": "7" * 64}
            evidence_ref = {"path": "evidence/post-source.json", "sha256": "8" * 64}
            request_ref = {"path": "native/request.json", "sha256": "9" * 64}
            contract = {"source_inputs": []}
            request = {"expected_head": baseline}

            refs = {
                "native_control_request": request_ref,
                "eligible_joern_plan": eligible_ref,
            }
            core = {
                "source_commit": source_commit,
                "source_tree": tree,
                "plan_commit": plan_commit,
                "contract": contract_ref,
                "source_evidence": evidence_ref,
                "source_design": design_ref,
                "qualification": qualification_ref,
                "runtime_module_graph": {"frozen": runtime_ref},
                "adapter_module_refs": {"current": adapter_ref},
                "joern_runner_source": runner_ref,
                "source_history_input": {
                    "source_commit": source_commit,
                    "source_tree": tree,
                    "execution_head": plan_commit,
                    "execution_tree": "e" * 40,
                    "plan_commit": plan_commit,
                },
                "prerequisite_refs": refs,
            }
            source_refs = [runtime_ref, adapter_ref, design_ref, qualification_ref,
                           *[{"path": path, "sha256": digest}
                             for path, digest in history.NATIVE10_SOURCE_REFS.items()],
                           dict(packet.HISTORY_PROVIDER03_REF), dict(history.HISTORY02_REF),
                           eligible_ref, runner_ref]
            source_refs.sort(key=lambda entry: entry["path"])
            contract_raw = canonical(contract)
            contract_ref["sha256"] = sha(contract_raw)
            request_raw = canonical(request)
            request_ref["sha256"] = sha(request_raw)
            refs["native_control_request"] = request_ref
            review = {
                "schema": history.CURRENT_SOURCE_REVIEW_SCHEMA,
                "status": history.CURRENT_SOURCE_REVIEW_STATUS,
                "automatic_retry": False,
                "bindings": {
                    "source_commit": source_commit,
                    "source_tree": tree,
                    "baseline_current_head": baseline,
                    "source_refs_sha256": sha(packet.canonical(source_refs)),
                    "native_request_sha256": request_ref["sha256"],
                    "adapter_module_refs_sha256": sha(packet.canonical(core["adapter_module_refs"])),
                },
                "scope": history.CURRENT_SOURCE_REVIEW_SCOPE,
            }
            review_raw = canonical(review)
            review_ref = {"path": "review/current.json", "sha256": sha(review_raw)}
            cas = {
                "schema": history.CURRENT_SOURCE_CAS_SCHEMA,
                "source_commit": source_commit,
                "source_tree": tree,
                "baseline_current_head": baseline,
                "native_request": request_ref,
                "source_refs": source_refs,
                "source_review": review_ref,
            }
            cas_raw = canonical(cas)
            cas_ref = {"path": "cas/current.json", "sha256": sha(cas_raw)}
            core["current_source_cas"] = cas_ref
            source_input = dict(core["source_history_input"], source_tree=tree)
            source_input["source_commit"] = source_commit
            core["source_history_input"] = source_input

            def write(ref, raw):
                path = root / ref["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)

            write(contract_ref, contract_raw)
            write(request_ref, request_raw)
            write(review_ref, review_raw)
            write(cas_ref, cas_raw)

            def git(_root, *args):
                if args == ("rev-parse", f"{source_commit}^{{tree}}"):
                    return tree
                if args == ("rev-parse", "HEAD"):
                    return plan_commit
                if args == ("rev-parse", "HEAD^{tree}"):
                    return "e" * 40
                return ""

            value, source_map = history.validate_source_cas_fields(root, core, refs, git)
            self.assertEqual(value["source_refs"], source_refs)
            self.assertNotIn(evidence_ref["path"], source_map)
            self.assertNotIn(cas_ref["path"], source_map)
            self.assertNotIn(review_ref["path"], source_map)

    def test_seven_module_import_edges_remain_exact(self):
        observed = set()
        base = packet.ROOT / "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/adapter-08"
        for logical in bridge.ADAPTER_NAMES:
            role = "joern05_" + logical
            tree = ast.parse((base / f"{logical}.py").read_bytes())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in bridge.ADAPTER_NAMES:
                    observed.add((role, "joern05_" + node.module))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in bridge.ADAPTER_NAMES:
                            observed.add((role, "joern05_" + alias.name))
        self.assertEqual(observed, set(bridge.ADAPTER_IMPORT_EDGES))

    def test_tail_requires_exact_current_terminal_and_owned_process_record(self):
        current, _ = _current_plan()
        row = _terminal_row(current)
        result = history._validate_tail(row, {
            "contract": {"sha256": current["validated"]["bytes_sha256"]},
            "source_commit": current["source_commit"],
            "plan_commit": current["plan_commit"],
        }, _global_attempt_annex())
        self.assertNotIn("global_attempt_number", result["row"])
        self.assertEqual(result["physical_ledger_row"], 131)
        self.assertEqual(result["global_attempt_number"], 132)
        self.assertFalse(result["eligible"])
        self.assertFalse(result["completion_claim"])
        for change in (
            {"status": "capacity-lost"},
            {"process_ownership": {"schema": "invocation-process-ownership/v1"}},
            {"group_id": "bifrost-smoke"},
            {"global_attempt_number": 131},
        ):
            with self.subTest(change=change):
                candidate = dict(row, **change)
                with self.assertRaises(packet.AdapterError):
                    history._validate_tail(candidate, {
                        "contract": {"sha256": current["validated"]["bytes_sha256"]},
                        "source_commit": current["source_commit"],
                        "plan_commit": current["plan_commit"],
                    }, _global_attempt_annex())

    def test_next_global_number_derives_only_from_exact_archived_annex(self):
        self.assertEqual(protocol.derive_next_global_attempt_number(
            _global_attempt_annex()), 132)
        for changed in (
            _global_attempt_annex()[:-1],
            _global_attempt_annex()[:-1] + [{"global_attempt_number": 130}],
            _global_attempt_annex()[:-1] + [{"global_attempt_number": 132}],
        ):
            with self.subTest(changed=changed[-1:]):
                with self.assertRaises(packet.AdapterError):
                    protocol.derive_next_global_attempt_number(changed)

    def test_protocol_accepts_frozen_tail_schema_and_rejects_injected_global_field(self):
        current, _ = _current_plan()
        row = _terminal_row(current)
        rows = ([{} for _ in range(109)] + _global_attempt_annex() + [row])
        protocol.require_terminal_tail(rows, {
            "contract": {"sha256": current["validated"]["bytes_sha256"]},
            "source_commit": current["source_commit"],
            "plan_commit": current["plan_commit"],
        })
        injected = dict(row, global_attempt_number=132)
        with self.assertRaisesRegex(packet.AdapterError, "frozen recorder schema"):
            protocol.require_terminal_tail(rows[:-1] + [injected], {
                "contract": {"sha256": current["validated"]["bytes_sha256"]},
                "source_commit": current["source_commit"],
                "plan_commit": current["plan_commit"],
            })

    def test_completion_gate_reports_joern108_without_full_target_claim(self):
        current, bindings = _current_plan()
        row = _terminal_row(current)
        result = protocol.joern108_operational_completion(
            current, row, bindings, {"reached": 108}, _native_acceptance(),
            tail_proof=_tail_proof(row))
        self.assertEqual(result["status"], "joern108-operationally-complete")
        self.assertEqual(result["case_count"], 108)
        self.assertEqual(result["report_count"], 5)
        self.assertFalse(result["current_target_full"])
        self.assertFalse(result["configuration_ready"])
        self.assertFalse(result["full_model_qualification"])
        self.assertFalse(result["publication_approved"])
        with self.assertRaises(packet.AdapterError):
            protocol.joern108_operational_completion(
                current, dict(row, status="failed"), bindings,
                {"reached": 108}, _native_acceptance(),
                tail_proof=_tail_proof(row))

    def test_completion_gate_requires_exact_adapter_derived_tail_proof(self):
        current, bindings = _current_plan()
        row = _terminal_row(current)
        with self.assertRaises(packet.AdapterError):
            protocol.joern108_operational_completion(
                current, row, bindings, {"reached": 108}, _native_acceptance(),
                tail_proof={**_tail_proof(row), "global_attempt_number": 131})


class ReplayPartitionTests(unittest.TestCase):
    def test_replay_uses_109_contexts_plus_only_current131_not_c5_contexts(self):
        current, current_bindings = _current_plan()
        hist_contract_sha = "9" * 64
        hist_source = "1" * 40
        hist_plan = "2" * 40
        historical = [{
            "attempt_id": f"legacy-group-attempt-{index:03}-series-01",
            "group_id": "legacy-group",
            "status": "completed",
            "source_commit": hist_source,
            "plan_commit": hist_plan,
            "contract_sha256": hist_contract_sha,
            "execution_series": 1,
        } for index in range(109)]
        annex = [{
            "attempt_id": f"annex-{index:03}",
            "group_id": f"c5-annex-{index:03}",
            "status": "completed",
            "source_commit": "3" * 40,
            "plan_commit": "4" * 40,
            "contract_sha256": "5" * 64,
            "execution_series": 2,
            "global_attempt_number": 111 + index,
        } for index in range(21)]
        tail = _terminal_row(current)
        rows = historical + annex + [tail]
        raw = b"".join(canonical(row) for row in rows)
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-replay-") as temp:
            root = Path(temp).resolve()
            ledger_path = root / packet.LIVE_LEDGER_PATH
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_path.write_bytes(raw)

            hist_group = {"id": "legacy-group", "reports": [{"case_ids": ["old-case"]}]}
            current_group = current["validated"]["plan"]["groups"][0]
            hist_validated = {"bytes_sha256": hist_contract_sha,
                              "plan": {"source_commit": hist_source}}
            contexts = {
                hist_contract_sha: {"validated": hist_validated,
                                    "source_commit": hist_source,
                                    "plan_commit": hist_plan},
                current["validated"]["bytes_sha256"]: current,
            }
            origin_calls = []
            directory_calls = []
            wall_calls = []

            class Stage:
                @staticmethod
                def _origin_context(context, row):
                    origin_calls.append(row["attempt_id"])
                    return context["contexts"][row["contract_sha256"]]

                @staticmethod
                @contextlib.contextmanager
                def _resume_checker_context(_replacement, _context, _origin):
                    yield

                @staticmethod
                def _observed_wall(_checker, candidate_rows):
                    wall_calls.append(list(candidate_rows))
                    return 1.0

            class Executor:
                @staticmethod
                def _historical_group_for_replay(validated, row):
                    return current_group if row["group_id"] == protocol.GROUP else hist_group

            class Replacement:
                @staticmethod
                def _attempt_number(attempt_id):
                    return 5 if attempt_id == protocol.ATTEMPT else 1

            class Checker:
                @staticmethod
                def _verify_one_group(_root, validated, group, row, _plan_commit, _number):
                    if validated is hist_validated:
                        return ([{"adapter": "legacy-adapter", "staged_path": "old.json",
                                  "sha256": "6" * 64, "rows": 1}], {"reached": 1})
                    result = ([{
                        "adapter": report["path"],
                        "staged_path": f"current/{index}.json",
                        "sha256": f"{index + 1:064x}",
                        "rows": len(report["case_ids"]),
                    } for index, report in enumerate(current_group["reports"])],
                        {"reached": 108})
                    return result

                @staticmethod
                def _verify_failed_attempt(*_args):
                    raise AssertionError("successful synthetic tail cannot enter failed verifier")

                @staticmethod
                def _assert_attempt_directories(_root, ids):
                    directory_calls.append(set(ids))

            annex_rows = annex
            facts = {
                "historical109": {"rows": historical},
                "bifrost0144_c5_annex21": {"rows": annex_rows},
                "tail_row131": _tail_proof(tail),
                "sealed109_lineage": {"consumed_events": []},
            }
            selected = {
                "legacy-group": historical[-1],
                protocol.GROUP: tail,
            }
            mixed = {
                "root": root,
                "contexts": contexts,
                "history_result": facts,
                "current_core": {
                    "contract": {"sha256": current["validated"]["bytes_sha256"]},
                    "source_commit": current["source_commit"],
                    "plan_commit": current["plan_commit"],
                },
                "native_acceptance": _native_acceptance(),
                "validated": {"groups": [{"id": protocol.GROUP}]},
            }
            value = {
                "stage": Stage,
                "rows": rows,
                "raw": raw,
                "current_core": mixed["current_core"],
                "history_result": facts,
                "modules": {"replacement05": Replacement},
                "validated": mixed["validated"],
            }
            context = {
                **mixed,
                "checker": Checker,
                "executor": Executor,
                "modules": {"replacement05": Replacement},
            }
            # This synthetic ledger is deliberately not the pinned live ledger
            # with its one known pre-dispatch stop. Exercise the replay wall
            # call shape without claiming that fixture carries that live hash.
            with mock.patch.object(
                    stage_runtime, "_observed_replay_wall",
                    side_effect=lambda replay_stage, replay_checker, replay_rows, _hashes:
                    replay_stage._observed_wall(replay_checker, replay_rows)):
                summary = stage_runtime.replay_current_history(root, value, context, selected)

            self.assertEqual(summary["status"], "joern108-operationally-complete")
            self.assertEqual(summary["ledger_rows"], 131)
            self.assertEqual(len(directory_calls), 1)
            self.assertEqual(len(directory_calls[0]), 131)
            self.assertEqual(len(wall_calls[0]), 131)
            self.assertEqual(set(origin_calls), {row["attempt_id"] for row in historical} |
                             {protocol.ATTEMPT})
            self.assertEqual(summary["partitions"], 6)
            self.assertEqual(summary["rows"], 109)
            self.assertFalse(summary["full_release_gate_satisfied"])
            self.assertEqual(summary["joern108_operational_completion"]["case_count"], 108)


class CurrentSourceSnapshotScopeTests(unittest.TestCase):
    def _fixture(self, root: Path, *, current_core=None, historical_core=None):
        archived_refs = []
        for index in range(96):
            path = f"archive/raw-{index:03}.json"
            raw = f"raw-member-{index}\n".encode()
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            archived_refs.append({"path": path, "sha256": sha(raw)})
        direct_raw = b"direct current source input\n"
        direct = {"path": "inputs/direct.json", "sha256": sha(direct_raw)}
        direct_path = root / direct["path"]
        direct_path.parent.mkdir(parents=True, exist_ok=True)
        direct_path.write_bytes(direct_raw)
        # The CAS contains current graph/runtime inputs that the frozen plan
        # resolver does not return. Its set is deliberately a strict superset.
        if current_core is None:
            cas_only = [
                {"path": "reports/runtime/executor.py", "sha256": "1" * 64},
                {"path": "reports/runtime/stage_runtime11.py", "sha256": "2" * 64},
            ]
        else:
            cas_only = [current_core["runtime_module_graph"][name]
                        for name in ("executor", "stage_runtime11")]
        source_refs = sorted([*archived_refs, direct, *cas_only],
                             key=lambda item: item["path"])
        normalized = {
            "plan": {"runner_source_sha256": sha(b"runner source\n")},
            "source_inputs": [{**item, "role": "release-input"}
                              for item in sorted([*archived_refs, direct],
                                                 key=lambda item: item["path"])],
        }
        if historical_core is None:
            historical_core = {
                "contract": {"path": "reports/historical/contract.json",
                             "sha256": "3" * 64},
            }
        if current_core is None:
            current_core = {
                "source_commit": "a" * 40,
                "plan_commit": "b" * 40,
                "contract": {"path": "reports/current/contract.json",
                             "sha256": "4" * 64},
                "qualification": {"path": "reports/current/qualification.json",
                                  "sha256": "5" * 64},
                "runtime_module_graph": {
                    "executor": cas_only[0],
                    "stage_runtime11": cas_only[1],
                },
            }
        closure = stage_runtime.current_source_input_closure(
            current_core, historical_core, normalized["source_inputs"])
        proof = {
            "schema": "v092-joern05-current-source-proof/v1",
            "status": "verified", "source_commit": current_core["source_commit"],
            "source_refs_sha256": sha(packet.canonical(source_refs)),
            "source_ref_count": len(source_refs), "current_direct_count": 3,
            "archived_member_count": 96,
            "source_refs": source_refs,
            "archived_member_paths": [item["path"] for item in archived_refs],
            "archived_member_refs": archived_refs,
        }
        return normalized, proof, direct, current_core, historical_core, closure

    def test_snapshot_scope_keeps_direct_git_guard_and_serves_only_exact_archive_refs(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-snapshot-") as temp:
            root = Path(temp).resolve()
            normalized, proof, direct, core, historical_core, closure = self._fixture(root)
            guard_calls, git_reads = [], []
            archived_path = proof["archived_member_refs"][0]["path"]

            class Executor:
                def _assert_source_snapshot(self, candidate_root, commit, runner_sha, inputs):
                    guard_calls.append((candidate_root, commit, runner_sha, list(inputs)))
                    return {"checked": [item["path"] for item in inputs]}

                def _source_file(self, candidate_root, commit, relative, expected):
                    git_reads.append((candidate_root, commit, relative, expected))
                    return ("git:" + str(relative)).encode()

                def run_group(self, runtime, group_id):
                    result = self._assert_source_snapshot(
                        root, core["source_commit"],
                        normalized["plan"]["runner_source_sha256"],
                        normalized["source_inputs"])
                    archived = self._source_file(
                        root, core["source_commit"], archived_path,
                        proof["archived_member_refs"][0]["sha256"])
                    direct_result = self._source_file(
                        root, core["source_commit"], direct["path"], direct["sha256"])
                    unrelated = self._source_file(
                        root, "9" * 40, archived_path,
                        proof["archived_member_refs"][0]["sha256"])
                    return {"runtime": runtime, "group_id": group_id,
                            "source_guard_result": result,
                            "archived": archived, "direct": direct_result,
                            "unrelated": unrelated}

            executor = Executor()
            original_guard = executor._assert_source_snapshot
            original_source_file = executor._source_file
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical_core):
                result = supervisor._run_group_with_current_source_snapshot(
                    executor, object(), "joern-swift-common108",
                    stage_runtime=stage_runtime, root=root,
                    source_commit=core["source_commit"], current_core=core,
                    validated=normalized, source_proof=proof,
                    source_proof_sha256=sha(packet.canonical(proof)),
                    source_input_closure=closure,
                    source_input_closure_sha256=sha(packet.canonical(closure)))
            self.assertEqual(result["group_id"], "joern-swift-common108")
            self.assertEqual(len(guard_calls), 1)
            self.assertEqual(guard_calls[0][3], [{**direct, "role": "release-input"}])
            self.assertEqual(result["archived"],
                             (root / archived_path).read_bytes())
            self.assertEqual(result["direct"], ("git:" + direct["path"]).encode())
            self.assertEqual(result["unrelated"], ("git:" + archived_path).encode())
            self.assertEqual([call[2] for call in git_reads],
                             [direct["path"], archived_path])
            self.assertIs(executor._assert_source_snapshot.__self__,
                          original_guard.__self__)
            self.assertIs(executor._assert_source_snapshot.__func__,
                          original_guard.__func__)
            self.assertIs(executor._source_file.__self__, original_source_file.__self__)
            self.assertIs(executor._source_file.__func__, original_source_file.__func__)

    def test_live_scope_rejects_changed_archive_bytes_and_unbound_guard_calls(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-snapshot-reject-") as temp:
            root = Path(temp).resolve()
            normalized, proof, _direct, core, historical_core, closure = self._fixture(root)
            executor = type("Executor", (), {
                "_assert_source_snapshot": lambda *args: None,
                "_source_file": lambda *args: b"git",
                "run_group": lambda self, *_args: self._assert_source_snapshot(
                    root, core["source_commit"],
                    normalized["plan"]["runner_source_sha256"],
                    normalized["source_inputs"]),
            })()
            original_guard = executor._assert_source_snapshot
            original_source_file = executor._source_file
            with mock.patch.object(packet, "ROOT", root):
                old_core_patch = mock.patch.object(
                    packet, "inherited_core", return_value=historical_core)
                old_core_patch.start()
                self.addCleanup(old_core_patch.stop)
                # The first ref is part of the verified 96-member set. A
                # changed local copy cannot be hidden by the Git-blob filter.
                first = root / proof["archived_member_refs"][0]["path"]
                first.write_bytes(b"changed\n")
                with self.assertRaises(packet.AdapterError):
                    supervisor._run_group_with_current_source_snapshot(
                        executor, object(), "joern-swift-common108",
                        stage_runtime=stage_runtime, root=root,
                        source_commit=core["source_commit"], current_core=core,
                        validated=normalized, source_proof=proof,
                        source_proof_sha256=sha(packet.canonical(proof)),
                        source_input_closure=closure,
                        source_input_closure_sha256=sha(packet.canonical(closure)))
            self.assertIs(executor._assert_source_snapshot.__self__,
                          original_guard.__self__)
            self.assertIs(executor._assert_source_snapshot.__func__,
                          original_guard.__func__)
            self.assertIs(executor._source_file.__self__, original_source_file.__self__)
            self.assertIs(executor._source_file.__func__, original_source_file.__func__)

    def test_archive_roster_and_caller_binding_are_exact(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-snapshot-shape-") as temp:
            root = Path(temp).resolve()
            normalized, proof, _direct, core, historical_core, closure = self._fixture(root)
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical_core):
                for mutate in (
                    lambda value: value["archived_member_paths"].pop(),
                    lambda value: value["archived_member_paths"].__setitem__(1, value["archived_member_paths"][0]),
                    lambda value: value["archived_member_refs"][0].update(sha256="0" * 64),
                ):
                    changed = json.loads(json.dumps(proof))
                    mutate(changed)
                    executor = type("Executor", (), {
                        "_assert_source_snapshot": lambda *args: None,
                        "_source_file": lambda *args: b"git",
                    })()
                    with self.subTest(mutate=mutate), self.assertRaises(packet.AdapterError):
                        with stage_runtime.current_source_snapshot_scope(
                                executor, root, core["source_commit"],
                                normalized["plan"]["runner_source_sha256"],
                                normalized, changed, current_core=core,
                                source_input_closure=closure):
                            pass
                executor = type("Executor", (), {
                    "_assert_source_snapshot": lambda *args: None,
                    "_source_file": lambda *args: b"git",
                })()
                with self.assertRaises(packet.AdapterError):
                    supervisor._run_group_with_current_source_snapshot(
                        executor, object(), "joern-swift-common108",
                        stage_runtime=stage_runtime, root=root,
                        source_commit=core["source_commit"], current_core=core,
                        validated=normalized, source_proof=proof,
                        source_proof_sha256="0" * 64,
                        source_input_closure=closure,
                        source_input_closure_sha256=sha(packet.canonical(closure)))

    def test_cas_superset_is_required_to_cover_exact_resolver_closure(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-cas-superset-") as temp:
            root = Path(temp).resolve()
            normalized, proof, _direct, core, historical_core, closure = self._fixture(root)
            executor = type("Executor", (), {
                "_assert_source_snapshot": lambda *args: None,
                "_source_file": lambda *args: b"git",
            })()
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical_core):
                # Full CAS has two graph/runtime refs that are intentionally
                # absent from the exact plan resolver output.
                with stage_runtime.current_source_snapshot_scope(
                        executor, root, core["source_commit"],
                        normalized["plan"]["runner_source_sha256"], normalized,
                        proof, current_core=core, source_input_closure=closure,
                        expected_closure_sha256=sha(packet.canonical(closure))):
                    pass

                incomplete = copy.deepcopy(proof)
                incomplete["source_refs"] = [
                    item for item in incomplete["source_refs"]
                    if item["path"] != _direct["path"]]
                incomplete["source_ref_count"] = len(incomplete["source_refs"])
                incomplete["source_refs_sha256"] = sha(
                    packet.canonical(incomplete["source_refs"]))
                with self.assertRaises(packet.AdapterError):
                    with stage_runtime.current_source_snapshot_scope(
                            executor, root, core["source_commit"],
                            normalized["plan"]["runner_source_sha256"], normalized,
                            incomplete, current_core=core,
                            source_input_closure=closure):
                        pass

                changed_normalized = copy.deepcopy(normalized)
                changed_normalized["source_inputs"].pop()
                with self.assertRaises(packet.AdapterError):
                    with stage_runtime.current_source_snapshot_scope(
                            executor, root, core["source_commit"],
                            normalized["plan"]["runner_source_sha256"],
                            changed_normalized, proof, current_core=core,
                            source_input_closure=closure):
                        pass

    def test_archived_source_file_rejects_current_scope_root_or_digest_escape(self):
        with tempfile.TemporaryDirectory(prefix="joern-adapter08-source-file-") as temp:
            root = Path(temp).resolve()
            normalized, proof, _direct, core, historical_core, closure = self._fixture(root)
            archived = proof["archived_member_refs"][0]
            calls = []

            class Executor:
                def _assert_source_snapshot(self, *_args):
                    return None
                def _source_file(self, candidate_root, commit, relative, expected):
                    calls.append((candidate_root, commit, relative, expected))
                    return b"git-source"

            executor = Executor()
            with mock.patch.object(packet, "ROOT", root), \
                    mock.patch.object(packet, "inherited_core", return_value=historical_core):
                with stage_runtime.current_source_snapshot_scope(
                        executor, root, core["source_commit"],
                        normalized["plan"]["runner_source_sha256"], normalized,
                        proof, current_core=core, source_input_closure=closure):
                    self.assertEqual(executor._source_file(
                        root, core["source_commit"], archived["path"],
                        archived["sha256"]), (root / archived["path"]).read_bytes())
                    with self.assertRaises(packet.AdapterError):
                        executor._source_file(
                            root, core["source_commit"], archived["path"], "0" * 64)
                    with self.assertRaises(packet.AdapterError):
                        executor._source_file(
                            root.parent, core["source_commit"], archived["path"],
                            archived["sha256"])
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
