"""Actual outer95 graph/runtime positives with synthetic evidence I/O only."""
from __future__ import annotations

import contextlib
import copy
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import bridge
import history
import packet
import protocol
import admission
import stage_runtime
import test_adapter_08 as fixtures


class OpaqueCurrentRuntimeGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_core = packet.inherited_core(packet.ROOT)
        cls.host_names = []
        cls.host_modules = {}
        for role in ("bridge19", "supervisor24", "protocol24", "admission24"):
            name = "_joern_adapter08_runtime_test_" + role
            cls.host_names.append(name)
            cls.host_modules[role] = packet.load_bound_module(
                packet.ROOT, name, cls.old_core["runtime_module_graph"][role])
        cls.frozen = cls.host_modules["bridge19"]
        cls.graph88 = cls.frozen.prepare_graph(
            packet.ROOT, cls.old_core, host_modules=cls.host_modules)

    @classmethod
    def tearDownClass(cls):
        for name in cls.host_names:
            sys.modules.pop(name, None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="joern-adapter08-opaque95-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        paths = {ref["path"] for ref in self.old_core["runtime_module_graph"].values()}
        paths.update({packet.CORE_PATH, packet.HISTORY_RELATIVE_PATH})
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(packet.ROOT / relative, target)
        self.adapter_refs = {}
        for name in bridge.ADAPTER_NAMES:
            relative = f"candidate/adapter08-{name}.py"
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = (HERE / f"{name}.py").read_bytes()
            target.write_bytes(raw)
            self.adapter_refs["joern05_" + name] = {
                "path": relative, "sha256": packet.digest(raw)}
        self.graph_refs = {**self.old_core["runtime_module_graph"],
                           **self.adapter_refs}
        self.graph = bridge.prepare_graph95(
            self.root, inherited_graph=self.graph88, graph_refs=self.graph_refs,
            adapter_refs=self.adapter_refs,
            import_edges=bridge.adapter_import_edges())
        self.addCleanup(bridge.close_graph95, self.graph)

    @staticmethod
    def _group(group_id: str, report_sizes: list[int]) -> dict:
        reports = []
        case_ids = []
        for part, count in enumerate(report_sizes):
            cases = [f"{group_id}-case-{part}-{index}" for index in range(count)]
            case_ids.extend(cases)
            reports.append({"path": f"history/{group_id}/{part}.json",
                            "case_ids": cases})
        return {"id": group_id, "reports": reports, "case_ids": case_ids}

    def _rows_and_contexts(self):
        current, _bindings = fixtures._current_plan()
        current["validated"]["groups"] = copy.deepcopy(
            current["validated"]["plan"]["groups"])
        hist_source, hist_plan, hist_contract = "1" * 40, "2" * 40, "9" * 64

        report_sizes = [48] * 55 + [47] * 32
        cursor = 0
        selected_groups = []
        for index in range(83):
            count = 2 if index < 4 else 1
            selected_groups.append(self._group(
                f"history-group-{index:02}", report_sizes[cursor:cursor + count]))
            cursor += count
        self.assertEqual(cursor, 87)
        self.assertEqual(sum(report_sizes), 4144)
        joern_old = {"id": protocol.GROUP, "reports": [], "case_ids": []}
        failed_only = {"id": "historical-failed-only", "reports": [], "case_ids": []}
        historical_groups = [*selected_groups, joern_old, failed_only]
        historical_validated = {
            "bytes_sha256": hist_contract,
            "plan": {"source_commit": hist_source, "groups": historical_groups},
            "groups": historical_groups,
        }
        historical_origin = {"validated": historical_validated,
                             "source_commit": hist_source,
                             "plan_commit": hist_plan}
        current_origin = current
        contexts = {hist_contract: historical_origin,
                    current["validated"]["bytes_sha256"]: current_origin}

        historical = []
        def old_row(number: int, group_id: str, status: str) -> dict:
            return {
                "attempt_id": f"legacy-attempt-{number:03}-series-01",
                "group_id": group_id, "status": status,
                "source_commit": hist_source, "plan_commit": hist_plan,
                "contract_sha256": hist_contract, "execution_series": 1,
            }

        # 63 distinct first89 successes, followed by repeated successes for
        # 21 of those groups. The four latest historical Joern attempts are
        # recorder/error rows and are intentionally not selected.
        for number in range(1, 64):
            historical.append(old_row(number, f"history-group-{number - 1:02}",
                                       "completed"))
        for number in range(64, 85):
            historical.append(old_row(number, f"history-group-{number - 64:02}",
                                       "completed"))
        historical.extend([
            old_row(85, protocol.GROUP, "recorder-error"),
            old_row(86, protocol.GROUP, "failed"),
            old_row(87, protocol.GROUP, "recorder-error"),
            old_row(88, protocol.GROUP, "failed"),
            old_row(89, "historical-failed-only", "failed"),
        ])
        for number in range(90, 110):
            group_number = number - 27
            historical.append(old_row(
                number, f"history-group-{group_number:02}", "completed"))
        self.assertEqual(len(historical), 109)

        annex = [{
            "attempt_id": f"c5-annex-attempt-{index:03}-series-02",
            "group_id": f"c5-annex-{index:03}", "status": "completed",
            "global_attempt_number": 110 + index,
        } for index in range(1, 22)]
        tail = fixtures._terminal_row(current)
        baseline_selected = history._selected_historical_rows(historical, [], None)
        after_selected = history._selected_historical_rows(
            historical, [], {"row": tail})
        self.assertEqual(len(baseline_selected), 83)
        self.assertNotIn(protocol.GROUP, baseline_selected)
        self.assertEqual(len(after_selected), 84)
        self.assertEqual(after_selected[protocol.GROUP], tail)

        proof_paths = [f"archive/proof-only-{index:03}.json" for index in range(96)]
        source_proof = {
            "schema": "v092-joern05-current-source-proof/v1",
            "status": "verified", "source_commit": current["source_commit"],
            "source_tree": "3" * 40, "execution_head": current["plan_commit"],
            "baseline_current_head": "4" * 40,
            "source_refs_sha256": "5" * 64, "source_ref_count": 97,
            "current_direct_count": 1, "archived_member_count": 96,
            "archived_member_paths": proof_paths,
        }
        facts = {
            "schema": "v092-joern05-adapter08-history-context/v1",
            "execution_authorized": False,
            "source_context_roster_extension": "not-created-by-adapter08",
            "historical109": {"rows": historical},
            "bifrost0144_c5_annex21": {"rows": annex},
            "tail_row131": None,
            "selected_historical_joern_rows": baseline_selected,
            "sealed109_lineage": {"retained20": [], "consumed_events": []},
            "current_source_proof": source_proof,
        }
        return current, hist_source, hist_plan, hist_contract, historical, annex, tail, contexts, facts, source_proof

    def _runtime_value(self, current, historical, annex, tail, contexts, facts,
                       source_proof, ledger_bytes, mode):
        rows = historical + annex + ([tail] if mode == "after" else [])
        facts = copy.deepcopy(facts)
        facts["tail_row131"] = ({
            "row": tail, "physical_ledger_row": 131,
            "global_attempt_number": 132, "status": tail["status"],
            "completion_claim": False, "eligible": False,
        } if mode == "after" else None)
        facts["selected_historical_joern_rows"] = history._selected_historical_rows(
            historical, [], facts["tail_row131"])
        raw = b"".join(packet.canonical(row) for row in rows)
        self.assertEqual(ledger_bytes, raw)
        ledger_path = self.root / packet.LIVE_LEDGER_PATH
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_bytes(raw)
        for row in rows:
            if row["status"] != "completed":
                path = self.root / "reports/releases/v0.9.2/attempts" / row["attempt_id"] / "completed.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(packet.canonical({"synthetic_receipt": row["attempt_id"]}))

        modules = {name: self.graph.module(name) for name in (
            "replacement05", "executor", "checker", "configuration")}
        old_stage = self.graph.module("stage_runtime11")
        checker = modules["checker"]
        executor = modules["executor"]
        current["validated"]["source_inputs"] = [{
            "path": "synthetic/resolver-input.json", "sha256": "7" * 64,
            "role": "release-input",
        }]
        current_core = {
            "contract": {"sha256": current["validated"]["bytes_sha256"]},
            "source_commit": current["source_commit"],
            "plan_commit": current["plan_commit"],
            "qualification": {"path": "synthetic/current-qualification.json",
                               "sha256": "8" * 64},
            "runtime_module_graph": self.graph_refs,
        }
        current_core["contract"].setdefault(
            "path", "synthetic/current-contract.json")
        source_input_closure = stage_runtime.current_source_input_closure(
            current_core, self.old_core, current["validated"]["source_inputs"])
        value = {
            "raw": raw, "rows": rows, "stage": old_stage,
            "modules": modules, "contexts": contexts,
            "validated": current["validated"],
            "current_core": current_core, "history_result": facts,
            "current_source_proof": source_proof,
            "current_source_input_closure": source_input_closure,
            "native_acceptance": fixtures._native_acceptance(),
        }

        def _one_group(_root, validated, group, row, _plan_commit, _number):
            bindings = [{
                "adapter": report["path"],
                "staged_path": f"synthetic/{row['attempt_id']}/{index}.json",
                "sha256": packet.digest(f"{row['attempt_id']}:{index}".encode()),
                "rows": len(report["case_ids"]),
            } for index, report in enumerate(group["reports"])]
            return bindings, {"reached": sum(item["rows"] for item in bindings)}

        def _failed(*_args):
            return {"synthetic_failed_attempt": True}

        def _directories(_root, ids):
            self.directory_checks.append(set(ids))

        @contextlib.contextmanager
        def _resume(_replacement, _context, _origin):
            yield

        def _wall(_checker, observed_rows):
            self.wall_checks.append(list(observed_rows))
            return 1.0

        if not self.checker_patches_added:
            self.test_patches.extend([
                mock.patch.object(checker, "_verify_one_group", _one_group),
                mock.patch.object(checker, "_verify_failed_attempt", _failed),
                mock.patch.object(checker, "_assert_attempt_directories", _directories),
                mock.patch.object(old_stage, "_resume_checker_context", _resume),
                mock.patch.object(old_stage, "_observed_wall", _wall),
            ])
            self.checker_patches_added = True
        return value

    def test_before130_and_after131_use_graph_owned_loader_and_opaque_stage(self):
        current, hist_source, hist_plan, hist_contract, historical, annex, tail, contexts, facts, source_proof = self._rows_and_contexts()
        self.directory_checks = []
        self.wall_checks = []
        self.test_patches = []
        self.checker_patches_added = False
        current_runtime_module = self.graph.module("joern05_stage_runtime")
        current_supervisor = self.graph.module("joern05_supervisor")
        runtime_core = {
            "source_commit": current["source_commit"],
            "plan_commit": current["plan_commit"],
            "contract": {"path": "synthetic/current-contract.json",
                         "sha256": current["validated"]["bytes_sha256"]},
            "qualification": {"path": "synthetic/current-qualification.json",
                              "sha256": "6" * 64},
            "prerequisite_refs": {},
            "runtime_module_graph": self.graph_refs,
            "adapter_module_refs": self.adapter_refs,
            "adapter_import_edges": bridge.adapter_import_edges(),
            "joern_runner_role": "nested_037_joern_normal_runner_v092_repair_pinned",
            "joern_runner_source": self.graph_refs[
                "nested_037_joern_normal_runner_v092_repair_pinned"],
        }

        raw130 = b"".join(packet.canonical(row) for row in historical + annex)
        raw131 = raw130 + packet.canonical(tail)
        before_path = self.root / "synthetic/ledger-130.jsonl"
        after_path = self.root / "synthetic/ledger-131.jsonl"
        before_path.parent.mkdir(parents=True, exist_ok=True)
        before_path.write_bytes(raw130)
        after_path.write_bytes(raw131)

        values = {}
        @contextlib.contextmanager
        def synthetic_validation_scope(root, core, graph, refs, *, ledger_bytes=None):
            mode = "before" if len(ledger_bytes.splitlines()) == 130 else "after"
            yield values[mode]

        self.test_patches.append(mock.patch.object(
            current_runtime_module, "current_validation_scope", synthetic_validation_scope))

        for mode, raw in (("before", raw130), ("after", raw131)):
            values[mode] = self._runtime_value(
                current, historical, annex, tail, contexts, facts,
                source_proof, raw, mode)

        with contextlib.ExitStack() as stack:
            for patcher in self.test_patches:
                stack.enter_context(patcher)
            for mode, raw in (("before", raw130), ("after", raw131)):
                live_path = self.root / packet.LIVE_LEDGER_PATH
                live_path.parent.mkdir(parents=True, exist_ok=True)
                live_path.write_bytes(raw)
                runtime, _ = self.frozen.load_runtime_stage(
                    self.root, graph=self.graph,
                    runtime_loader=current_runtime_module.load_runtime_context,
                    mode=mode, core_identity=runtime_core,
                    ledger_bytes=raw)
                self.assertIsInstance(runtime, self.frozen.ActualRuntimeContext)
                self.assertIs(runtime.graph, self.graph)
                summary = runtime.objects["checker_summary"]
                expected = ((130, 83, 87, 4144, "partial-evidence-verified")
                            if mode == "before" else
                            (131, 84, 92, 4252, "joern108-operationally-complete"))
                self.assertEqual((runtime.diagnostic["ledger_rows"],
                                  summary["selected_groups"], summary["partitions"],
                                  summary["rows"], summary["status"]), expected)
                self.assertFalse(summary["full_release_gate_satisfied"])
                self.assertEqual(runtime.objects["configuration_summary"]["status"], "pending")
                if mode == "before":
                    self.assertIsNone(summary["joern108_operational_completion"])
                else:
                    self.assertEqual(summary["joern108_operational_completion"]["case_count"], 108)

                lock_path = self.root / "synthetic/parent.lock"
                lock_path.parent.mkdir(parents=True, exist_ok=True)
                lock_path.write_bytes(b"")
                lock_stat = lock_path.stat()
                lock = self.frozen.LockIdentity(str(lock_path), lock_stat.st_dev,
                                                lock_stat.st_ino, os.getpid(), "test-birth")
                ledger_before = {"path": before_path.relative_to(self.root).as_posix(),
                                 "sha256": packet.digest(raw130), "rows": 130}
                live_path = self.root / packet.LIVE_LEDGER_PATH
                live_ref = {"path": packet.LIVE_LEDGER_PATH,
                            "sha256": packet.digest(raw), "rows": len(raw.splitlines())}
                parent = self.frozen.build_parent_stage(
                    self.root, index=0, ledger=ledger_before, runtime=runtime,
                    graph=self.graph, source_commit=current["source_commit"],
                    plan_commit=current["plan_commit"],
                    contract_sha256=current["validated"]["bytes_sha256"],
                    lock=lock, sidecars={}, source_refs=[],
                    analyzer_deadline_seconds=1368, live_ledger=live_ref)
                self.assertIs(self.frozen.runtime_objects(parent), runtime)
                if mode == "before":
                    self.assertEqual(self.frozen.runtime_objects(parent).diagnostic["ledger_rows"], 130)
                    self.parent_stage = parent
                else:
                    after_ref = {"path": after_path.relative_to(self.root).as_posix(),
                                 "sha256": packet.digest(raw131), "rows": 131}
                    successor = self.frozen.build_successor_stage(
                        self.root, predecessor=self.parent_stage, index=1,
                        ledger_after=after_ref, runtime=runtime, graph=self.graph,
                        source_commit=current["source_commit"],
                        plan_commit=current["plan_commit"],
                        contract_sha256=current["validated"]["bytes_sha256"],
                        sidecars={}, source_refs=[], analyzer_deadline_seconds=1368,
                        live_ledger=live_ref)
                    self.assertIs(self.frozen.runtime_objects(successor), runtime)
                    self.frozen.assert_stage_current(self.root, successor, self.graph)

        # Exercise the exact graph-owned wrapper used around production
        # executor.run_group. The fake run_group enters the installed guard;
        # it does not execute analyzer code.
        scope_fixture = fixtures.CurrentSourceSnapshotScopeTests()
        scope_normalized, scope_proof, direct, scope_core, _old_core, closure = \
            scope_fixture._fixture(self.root, current_core=runtime_core,
                                   historical_core=self.old_core)
        graph_packet = self.graph.module("joern05_packet")
        graph_executor = self.graph.module("executor")
        guard_calls = []
        def frozen_guard(root, commit, runner_sha, inputs):
            guard_calls.append((root, commit, runner_sha, list(inputs)))
            return {"checked": len(inputs)}
        def synthetic_run_group(_runtime, group_id):
            return {"group_id": group_id,
                    "guard": graph_executor._assert_source_snapshot(
                        self.root, current["source_commit"],
                        scope_normalized["plan"]["runner_source_sha256"],
                        scope_normalized["source_inputs"])}
        with mock.patch.object(graph_packet, "ROOT", self.root), \
                mock.patch.object(graph_executor, "_assert_source_snapshot", frozen_guard), \
                mock.patch.object(graph_executor, "run_group", synthetic_run_group):
            result = current_supervisor._run_group_with_current_source_snapshot(
                graph_executor, object(), protocol.GROUP,
                stage_runtime=current_runtime_module, root=self.root,
                source_commit=current["source_commit"], current_core=scope_core,
                validated=scope_normalized,
                source_proof=scope_proof,
                source_proof_sha256=packet.digest(packet.canonical(scope_proof)),
                source_input_closure=closure,
                source_input_closure_sha256=packet.digest(packet.canonical(closure)))
        self.assertEqual(result["group_id"], protocol.GROUP)
        self.assertEqual(guard_calls[0][3], [{**direct, "role": "release-input"}])
        self.assertEqual(result["guard"]["checked"], 1)

        self.assertEqual(len(self.directory_checks), 2)
        self.assertEqual([len(value) for value in self.directory_checks], [130, 131])
        self.assertEqual([len(value) for value in self.wall_checks], [130, 131])

    def test_frozen_run_group_source_preflight_reads_archive_refs_before_tool_boundary(self):
        fixture = fixtures.CurrentSourceSnapshotScopeTests()
        current_core = {
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "contract": {"path": "synthetic/current-contract.json",
                         "sha256": "c" * 64},
            "qualification": {"path": "synthetic/current-qualification.json",
                              "sha256": "d" * 64},
            "runtime_module_graph": self.graph_refs,
        }
        validated, proof, direct, current_core, _old_core, closure = fixture._fixture(
            self.root, current_core=current_core, historical_core=self.old_core)
        runner_raw = b"synthetic frozen runner source\n"
        validated["plan"].update({
            "execution_authorized": True,
            "source_commit": current_core["source_commit"],
            "runner_source_sha256": packet.digest(runner_raw),
            "groups": [{"id": protocol.GROUP, "tool": "joern",
                        "deadline_seconds": 1, "reports": []}],
            "population": dict(proof["archived_member_refs"][0]),
        })
        validated.update({
            "repo_root": self.root,
            "path": str(self.root / "synthetic/current-contract.json"),
            "bytes_sha256": current_core["contract"]["sha256"],
            "groups": [{"id": protocol.GROUP, "reports": []}],
            "qualification": {"joern": {
                "execution_eligible": True, "groups": [protocol.GROUP]}},
            "tools": {"synthetic-tool": {}},
            "total_wall_budget_seconds": 3600,
        })
        executor = self.graph.module("executor")
        graph_packet = self.graph.module("joern05_packet")
        source_file_reads = []
        git_arguments = []
        git_blob_reads = []
        archive_reads = []
        boundary = RuntimeError("source-preflight-boundary")
        original_snapshot = executor._assert_source_snapshot
        original_source_file = executor._source_file
        original_read_ref = graph_packet.read_ref

        class SyntheticSubprocess:
            DEVNULL = object()
            PIPE = object()
            STDOUT = object()
            CalledProcessError = RuntimeError

            @staticmethod
            def run(args, **_kwargs):
                git_arguments.append(list(args))
                return type("Result", (), {"returncode": 0})()

            @staticmethod
            def check_output(args, **_kwargs):
                git_arguments.append(list(args))
                return ""

        def git_show(_root, _commit, path):
            git_blob_reads.append(path)
            if path == "scripts/execute-release-v092.py":
                return runner_raw
            if path == direct["path"]:
                return (self.root / direct["path"]).read_bytes()
            raise AssertionError("archive path reached frozen Git blob reader: " + path)

        def stop_at_tool(binding, name):
            source_file_reads.append((name, binding))
            raise boundary

        def read_ref(candidate_root, ref):
            if ref.get("path") in set(proof["archived_member_paths"]):
                archive_reads.append(ref["path"])
            return original_read_ref(candidate_root, ref)

        with mock.patch.object(graph_packet, "ROOT", self.root), \
                mock.patch.object(graph_packet, "read_ref", read_ref), \
                mock.patch.object(executor, "subprocess", SyntheticSubprocess), \
                mock.patch.object(executor, "_git_show", git_show), \
                mock.patch.object(executor, "_exclusive_lock", contextlib.nullcontext), \
                mock.patch.object(executor, "_assert_contract_snapshot",
                                  lambda _validated: current_core["plan_commit"]), \
                mock.patch.object(executor, "_matrix_elapsed_wall", lambda _validated: 0), \
                mock.patch.object(executor, "_check_tool_file", stop_at_tool):
            with self.assertRaisesRegex(RuntimeError, "source-preflight-boundary"):
                self.graph.module("joern05_supervisor")._run_group_with_current_source_snapshot(
                    executor, validated, protocol.GROUP,
                    stage_runtime=self.graph.module("joern05_stage_runtime"),
                    root=self.root, source_commit=current_core["source_commit"],
                    validated=validated, source_proof=proof,
                    source_proof_sha256=packet.digest(packet.canonical(proof)),
                    current_core=current_core,
                    source_input_closure=closure,
                    source_input_closure_sha256=packet.digest(
                        packet.canonical(closure)))

        self.assertEqual(len(source_file_reads), 1)
        self.assertEqual(source_file_reads[0][0], "synthetic-tool")
        archive_paths = set(proof["archived_member_paths"])
        self.assertFalse(archive_paths.intersection(git_blob_reads))
        self.assertEqual(git_blob_reads.count("scripts/execute-release-v092.py"), 1)
        self.assertEqual(git_blob_reads.count(direct["path"]), 2)
        self.assertEqual(len(archive_reads), 193)
        self.assertEqual(set(archive_reads), archive_paths)
        self.assertEqual(archive_reads.count(proof["archived_member_refs"][0]["path"]), 3)
        diff = next(args for args in git_arguments
                    if args[:3] == ["git", "diff", "--quiet"])
        status = next(args for args in git_arguments
                      if args[:3] == ["git", "status", "--porcelain=v1"])
        self.assertIn(direct["path"], diff)
        self.assertIn(direct["path"], status)
        self.assertFalse(archive_paths.intersection(diff))
        self.assertFalse(archive_paths.intersection(status))
        self.assertIs(executor._assert_source_snapshot, original_snapshot)
        self.assertIs(executor._source_file, original_source_file)

        def changed_direct_git_show(_root, _commit, path):
            if path == "scripts/execute-release-v092.py":
                return runner_raw
            if path == direct["path"]:
                return b"direct source changed after resolver capture\n"
            raise AssertionError("archive path reached frozen Git blob reader: " + path)

        with mock.patch.object(graph_packet, "ROOT", self.root), \
                mock.patch.object(executor, "subprocess", SyntheticSubprocess), \
                mock.patch.object(executor, "_git_show", changed_direct_git_show), \
                mock.patch.object(executor, "_exclusive_lock", contextlib.nullcontext), \
                mock.patch.object(executor, "_assert_contract_snapshot",
                                  lambda _validated: current_core["plan_commit"]), \
                mock.patch.object(executor, "_matrix_elapsed_wall", lambda _validated: 0), \
                mock.patch.object(executor, "_check_tool_file", stop_at_tool):
            with self.assertRaisesRegex(
                    executor.ReleaseError,
                    "source input at source_commit differs from its contract digest"):
                self.graph.module("joern05_supervisor")._run_group_with_current_source_snapshot(
                    executor, validated, protocol.GROUP,
                    stage_runtime=self.graph.module("joern05_stage_runtime"),
                    root=self.root, source_commit=current_core["source_commit"],
                    validated=validated, source_proof=proof,
                    source_proof_sha256=packet.digest(packet.canonical(proof)),
                    current_core=current_core,
                    source_input_closure=closure,
                    source_input_closure_sha256=packet.digest(
                        packet.canonical(closure)))

        archive_guard_reads = 0
        def tamper_archive_after_guard(candidate_root, ref):
            nonlocal archive_guard_reads
            raw = original_read_ref(candidate_root, ref)
            if ref.get("path") in archive_paths:
                archive_guard_reads += 1
                if archive_guard_reads == 96:
                    (self.root / proof["archived_member_refs"][0]["path"]).write_bytes(
                        b"changed after frozen snapshot guard\n")
            return raw

        with mock.patch.object(graph_packet, "ROOT", self.root), \
                mock.patch.object(graph_packet, "read_ref", tamper_archive_after_guard), \
                mock.patch.object(executor, "subprocess", SyntheticSubprocess), \
                mock.patch.object(executor, "_git_show", git_show), \
                mock.patch.object(executor, "_exclusive_lock", contextlib.nullcontext), \
                mock.patch.object(executor, "_assert_contract_snapshot",
                                  lambda _validated: current_core["plan_commit"]), \
                mock.patch.object(executor, "_matrix_elapsed_wall", lambda _validated: 0), \
                mock.patch.object(executor, "_check_tool_file", stop_at_tool):
            with self.assertRaisesRegex(
                    graph_packet.AdapterError,
                    "artifact SHA differs"):
                self.graph.module("joern05_supervisor")._run_group_with_current_source_snapshot(
                    executor, validated, protocol.GROUP,
                    stage_runtime=self.graph.module("joern05_stage_runtime"),
                    root=self.root, source_commit=current_core["source_commit"],
                    validated=validated, source_proof=proof,
                    source_proof_sha256=packet.digest(packet.canonical(proof)),
                    current_core=current_core,
                    source_input_closure=closure,
                    source_input_closure_sha256=packet.digest(
                        packet.canonical(closure)))
        self.assertEqual(archive_guard_reads, 96)

    def test_eligible_runner_scope_preserves_historical_archive_gate(self):
        runner_role = admission.ELIGIBLE_RUNNER_ROLE
        diagnostic_role = admission.DIAGNOSTIC_ADMISSION_ROLE
        runner = self.graph.module(runner_role)
        diagnostic = self.graph.module(diagnostic_role)
        self.assertEqual(runner.__graph_role__, runner_role)
        self.assertEqual(diagnostic.__graph_role__, diagnostic_role)

        control_raw = packet.canonical({"schema": "synthetic-control/v1"})
        control_ref = {"path": "synthetic/current-control.json",
                       "sha256": packet.digest(control_raw)}
        plan = {
            "schema": "synthetic-eligible-plan/v1",
            "status": "execution-eligible",
            "execution_eligible": True,
            "full_model_qualification": False,
            "scored_activation": False,
            "qualification_control_plan": control_ref,
        }
        plan_raw = packet.canonical(plan)
        plan_ref = {"path": "synthetic/current-plan.json",
                    "sha256": packet.digest(plan_raw)}
        for ref, raw in ((control_ref, control_raw), (plan_ref, plan_raw)):
            target = self.root / ref["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        old_path = runner.EXECUTION_PLAN_PATH
        observed = []

        def archive_gate(call_root, call_plan, call_control):
            self.assertEqual(Path(call_root).resolve(), self.root)
            self.assertEqual(call_plan, plan)
            self.assertEqual(call_control, {"schema": "synthetic-control/v1"})
            self.assertEqual(runner.EXECUTION_PLAN_PATH,
                             admission.HISTORICAL_EXECUTION_PLAN_PATH)
            observed.append(("historical", runner.EXECUTION_PLAN_PATH))
            return {"status": "historical-archive-validated"}

        def current_validate_plan(call_root, call_path):
            self.assertEqual(Path(call_root).resolve(), self.root)
            self.assertEqual(call_path, plan_ref["path"])
            self.assertEqual(runner.EXECUTION_PLAN_PATH, call_path)
            observed.append(("current", runner.EXECUTION_PLAN_PATH))
            result = diagnostic.validate_control_plan_admission(
                call_root, packet.document(self.root, plan_ref),
                packet.document(self.root, control_ref))
            self.assertEqual(runner.EXECUTION_PLAN_PATH, call_path)
            return plan, {"diagnostic": result}, {"synthetic": True}

        reviewed_group = {"argv": ["python", "runner", "--plan", plan_ref["path"]]}
        executor = type("Executor", (), {
            "_validate_joern_common_plan": staticmethod(lambda *_: None)})()
        original_archive_gate = diagnostic.validate_control_plan_admission
        with mock.patch.object(admission, "PACKET_ROOT", self.root), \
                mock.patch.object(runner, "validate_plan", current_validate_plan), \
                mock.patch.object(diagnostic, "validate_control_plan_admission",
                                  archive_gate):
            with admission.eligible_plan_scope(
                    executor, self.root, reviewed_group, plan_ref, runner,
                    graph=self.graph, runner_role=runner_role,
                    runner_ref=self.graph_refs[runner_role],
                    diagnostic_ref=self.graph_refs[diagnostic_role]):
                self.assertEqual(runner.EXECUTION_PLAN_PATH, plan_ref["path"])
                self.assertIsNot(diagnostic.validate_control_plan_admission,
                                 archive_gate)
                projected = dict(reviewed_group, maximum_attempts=2)
                self.assertEqual(
                    executor._validate_joern_common_plan(projected, self.root),
                    (plan_ref["path"], packet.digest(plan_raw)))
            self.assertEqual(runner.EXECUTION_PLAN_PATH, old_path)
            self.assertIs(diagnostic.validate_control_plan_admission, archive_gate)
        self.assertEqual(observed, [
            ("current", plan_ref["path"]),
            ("historical", admission.HISTORICAL_EXECUTION_PLAN_PATH),
        ])

        # The independent prerequisite path uses the same scoped validator;
        # it cannot call the current plan through the old default constant.
        observed.clear()
        core_ref = {"path": "synthetic/core.json", "sha256": "1" * 64}
        manifest_ref = {"path": "synthetic/manifest.json", "sha256": "2" * 64}
        contract_ref = {"path": "synthetic/contract.json", "sha256": "3" * 64}
        evidence_ref = {"path": "synthetic/source-evidence.json", "sha256": "4" * 64}
        docs = {
            tuple(core_ref.items()): {"contract": contract_ref,
                                      "source_evidence": evidence_ref},
            tuple(manifest_ref.items()): {"core_identity": core_ref},
            tuple(plan_ref.items()): plan,
            tuple(control_ref.items()): {"schema": "synthetic-control/v1"},
        }

        def synthetic_document(_root, ref):
            return docs[tuple(ref.items())]

        prereq_refs = {
            "current_core": core_ref,
            "current_manifest": manifest_ref,
            "current_contract": contract_ref,
            "current_source_evidence": evidence_ref,
            "eligible_joern_plan": plan_ref,
        }
        with mock.patch.object(admission, "PACKET_ROOT", self.root), \
                mock.patch.object(packet, "document", synthetic_document), \
                mock.patch.object(admission, "missing_prerequisites", return_value=[]), \
                mock.patch.object(admission, "validate_native_execution_decision",
                                  return_value={}), \
                mock.patch.object(runner, "validate_plan", current_validate_plan), \
                mock.patch.object(diagnostic, "validate_control_plan_admission",
                                  archive_gate):
            validated = admission.validate_prerequisites(
                self.root, prereq_refs, runner, plan_ref["path"], graph=self.graph,
                runner_role=runner_role, runner_ref=self.graph_refs[runner_role],
                diagnostic_ref=self.graph_refs[diagnostic_role], purpose="preflight")
        self.assertEqual(validated[0], plan)
        self.assertTrue(validated[1])
        self.assertEqual(runner.EXECUTION_PLAN_PATH, old_path)
        self.assertIs(diagnostic.validate_control_plan_admission,
                      original_archive_gate)
        self.assertEqual(observed, [
            ("current", plan_ref["path"]),
            ("historical", admission.HISTORICAL_EXECUTION_PLAN_PATH),
        ])

        # Ordinary exceptions and foreign global writes cannot leak scoped state.
        with mock.patch.object(admission, "PACKET_ROOT", self.root):
            with self.assertRaisesRegex(RuntimeError, "synthetic validator failure"):
                with admission._eligible_plan_validation_scope(
                        self.root, plan_ref, runner, graph=self.graph,
                        runner_role=runner_role, runner_ref=self.graph_refs[runner_role],
                        diagnostic_role=diagnostic_role,
                        diagnostic_ref=self.graph_refs[diagnostic_role]):
                    raise RuntimeError("synthetic validator failure")
            self.assertEqual(runner.EXECUTION_PLAN_PATH, old_path)
            self.assertIs(diagnostic.validate_control_plan_admission,
                          original_archive_gate)

            with self.assertRaises(packet.AdapterError):
                with admission._eligible_plan_validation_scope(
                        self.root, plan_ref, runner, graph=self.graph,
                        runner_role=runner_role, runner_ref=self.graph_refs[runner_role],
                        diagnostic_role=diagnostic_role,
                        diagnostic_ref=self.graph_refs[diagnostic_role]):
                    runner.EXECUTION_PLAN_PATH = "synthetic/foreign-plan.json"
                    diagnostic.validate_control_plan_admission = lambda *_: None
            self.assertEqual(runner.EXECUTION_PLAN_PATH, old_path)
            self.assertIs(diagnostic.validate_control_plan_admission,
                          original_archive_gate)


if __name__ == "__main__":
    unittest.main()
