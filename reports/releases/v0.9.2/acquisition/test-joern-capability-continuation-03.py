#!/usr/bin/env python3
"""Focused, read-only regressions for the Joern continuation-03 guards."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("joern-capability-continuation-03.py")
SPEC = importlib.util.spec_from_file_location("joern_capability_continuation_03_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def canonical(rows: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in rows
    )


class Continuation03StateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.real_sealed_sha = MODULE.SEALED_LEDGER_SHA
        self.prefix = [
            {"attempt_id": f"group-{n:03d}-attempt-01-series-01",
             "status": "completed", "execution_series": 1,
             "group_id": f"group-{n:03d}"}
            for n in range(MODULE.SEALED_ROWS)
        ]
        for index in (0, 1, 2, 3, 4):
            self.prefix[index]["status"] = "failed" if index % 2 == 0 else "recorder-error"
        self.patcher = mock.patch.multiple(
            MODULE, SEALED_ROWS=87, SEALED_LEDGER_SHA=MODULE.sha_bytes(canonical(self.prefix))
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_authorization_and_sealed_ledger_constants_are_fourth_attempt(self) -> None:
        self.assertEqual(MODULE.SEALED_ROWS, 87)
        self.assertEqual(self.real_sealed_sha,
                         "57d8265e8eb0c216c56e184a5fed36f9931bcb5b36ea1047ae3f4a0c71f0a096")
        self.assertEqual(MODULE.JOERN_ATTEMPT, "joern-swift-common108-attempt-04-series-01")
        self.assertEqual(MODULE.DEFAULT_CONTRACT.split("/")[-1], "joern-capability-repair-06-contract.json")
        self.assertEqual(MODULE.DEFAULT_MANIFEST.split("/")[-1], "continuation-manifest-04.json")
        with mock.patch.object(MODULE, "SEALED_LEDGER_SHA", self.real_sealed_sha):
            authorization = MODULE._check_authorization(
                MODULE.ROOT,
                {"path": MODULE.AUTHORIZATION_PATH, "sha256": MODULE.AUTHORIZATION_SHA},
            )
        self.assertEqual(authorization["maximum_joern_global_attempts"], 4)
        self.assertEqual(authorization["sealed_ledger_rows"], 87)

    def test_prefix_and_tail_preserve_five_failures_and_allow_one_new_joern(self) -> None:
        joern = {
            "attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
            "timed_out": False, "capacity_loss": None,
        }
        codeql = {
            "attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
            "timed_out": False, "capacity_loss": None,
        }
        rows = self.prefix + [joern, codeql]
        raw = canonical(rows)
        self.assertEqual(MODULE._check_prefix(Path("."), rows, raw), self.prefix)
        self.assertEqual(MODULE._tail(rows, final=True), [joern, codeql])

    def test_extra_joern_attempt_or_failed_joern_does_not_unlock_codeql(self) -> None:
        failed = {
            "attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
            "execution_series": 1, "status": "failed", "exit_code": 1,
        }
        codeql = {
            "attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
        }
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.prefix + [failed, codeql], final=False)
        extra = dict(failed, attempt_id="joern-swift-common108-attempt-05-series-01")
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.prefix + [dict(failed, status="completed", exit_code=0), extra], final=False)

    def test_attempt_number_must_match_new_joern_identity(self) -> None:
        joern = {
            "attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
            "execution_series": 1, "attempt_number": 3,
            "status": "completed", "exit_code": 0,
        }
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(self.prefix + [joern], final=False)

    def test_historical_roster_excludes_live_ledger_and_snapshot_is_exact(self) -> None:
        self.assertEqual(len(MODULE.HISTORICAL_CLOSURE), 22)
        self.assertNotIn(MODULE.LEDGER, MODULE.HISTORICAL_CLOSURE)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / MODULE.SEALED_LEDGER_SNAPSHOT_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(canonical(self.prefix))
            manifest = {"sealed_ledger_snapshot": {
                "path": MODULE.SEALED_LEDGER_SNAPSHOT_PATH,
                "sha256": MODULE.sha(path),
                "rows": MODULE.SEALED_ROWS,
            }}
            with mock.patch.object(MODULE, "SEALED_LEDGER_SHA", MODULE.sha(path)):
                self.assertEqual(
                    MODULE._sealed_ledger_snapshot(root, manifest),
                    {"path": MODULE.SEALED_LEDGER_SNAPSHOT_PATH,
                     "sha256": MODULE.sha(path)},
                )
            bad = {"sealed_ledger_snapshot": {
                "path": MODULE.LEDGER,
                "sha256": self.real_sealed_sha,
            }}
            with self.assertRaises(MODULE.ContinuationError):
                MODULE._sealed_ledger_snapshot(root, bad)

    def test_sealed_snapshot_path_cannot_be_rebound_to_another_qualification_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / MODULE.QUAL_ROOT / "other-prefix.jsonl"
            path.parent.mkdir(parents=True)
            path.write_bytes(canonical(self.prefix))
            with mock.patch.object(MODULE, "SEALED_LEDGER_SHA", MODULE.sha(path)):
                with self.assertRaises(MODULE.ContinuationError):
                    MODULE._sealed_ledger_snapshot(root, {
                        "sealed_ledger_snapshot": {
                            "path": f"{MODULE.QUAL_ROOT}/other-prefix.jsonl",
                            "sha256": MODULE.sha(path),
                            "rows": MODULE.SEALED_ROWS,
                        }
                    })

    def test_admission_bootstrap_accepts_only_registered_provisional_manifest(self) -> None:
        # The admission helper runs the read-only preflight before the final
        # receipt is written.  Prove validate() reaches manifest loading on
        # that exact path, while the execution-required mode rejects it.
        with mock.patch.object(MODULE, "_read", return_value=b"manifest"), \
                mock.patch.object(MODULE, "_load_manifest",
                                  side_effect=RuntimeError("path gate passed")):
            with self.assertRaisesRegex(RuntimeError, "path gate passed"):
                MODULE.validate(
                    MODULE.ROOT, MODULE.PROVISIONAL_MANIFEST, "a" * 64,
                    require_admission=False,
                )
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._check_manifest_path(MODULE.PROVISIONAL_MANIFEST,
                                         require_admission=True)
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._check_manifest_path(
                MODULE.QUAL_ROOT + "/continuation-manifest-admission-07.json",
                require_admission=False,
            )
        MODULE._check_manifest_path(MODULE.DEFAULT_MANIFEST, require_admission=True)


class FrozenTailBoundaryTests(unittest.TestCase):
    """Exercise the narrow C4 adapter against the actual immutable packet."""

    def _actual_packet(self) -> tuple[bytes, list[dict], dict]:
        raw, rows = MODULE._ledger(MODULE.ROOT)
        recovery_path = MODULE.ROOT / "scripts/v092_resource_recovery.py"
        spec = importlib.util.spec_from_file_location("resource_recovery_for_c3_test", recovery_path)
        assert spec is not None and spec.loader is not None
        recovery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recovery)
        plan = json.loads((MODULE.ROOT / MODULE.BASE_CONTRACT).read_bytes())
        packet = recovery.validate_packet(MODULE.ROOT, plan["resource_recovery"])
        return raw, rows, packet

    def _nested_c3_packet(self, rows: list[dict], raw: bytes) -> dict:
        scoped_path = MODULE.ROOT / "scripts/v092_scoped_recovery.py"
        spec = importlib.util.spec_from_file_location("scoped_recovery_for_c3_test", scoped_path)
        assert spec is not None and spec.loader is not None
        scoped = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoped)
        c3_plan = json.loads(
            (MODULE.ROOT / "reports/releases/v0.9.2/acquisition/resource-recovery-contract-03.json")
            .read_bytes()
        )
        packet = scoped.validate_packet(MODULE.ROOT, c3_plan["scoped_recovery"])
        actual_lines = raw.splitlines(keepends=True)
        actual = [(row, MODULE.sha_bytes(line)) for row, line in zip(rows, actual_lines)]
        packet["tail_rows"] = actual[len(packet["prefix_rows"]):57]
        return packet

    def test_actual_87_packet_is_rejected_unprojected_and_passes_projected_frozen_tail(self) -> None:
        raw, rows, packet = self._actual_packet()
        executor = MODULE._load_frozen(MODULE.ROOT, "execute")
        plan = json.loads((MODULE.ROOT / MODULE.BASE_CONTRACT).read_bytes())
        validated = {"plan": plan, "bytes_sha256": MODULE.BASE_SHA}
        original = executor._validate_scoped_tail
        with self.assertRaises(executor.ReleaseError):
            # This is the real frozen function and the real current packet;
            # the failure proves the adapter is needed for the C4 boundary.
            original(validated, packet)
        projected = MODULE._project_frozen_resource_recovery_packet(packet, rows, raw)
        original(validated, projected)
        self.assertEqual(len(projected["prefix_rows"]) + len(projected["tail_rows"]), 86)

    def test_packet_snapshot_line_hash_unknown_prefix_and_boundary_digest_fail_closed(self) -> None:
        raw, rows, packet = self._actual_packet()
        bad_hash = copy.deepcopy(packet)
        row, _digest = bad_hash["tail_rows"][0]
        bad_hash["tail_rows"][0] = (row, "0" * 64)
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._project_frozen_resource_recovery_packet(bad_hash, rows, raw)

        bad_prefix = copy.deepcopy(packet)
        row, digest = bad_prefix["prefix_rows"][0]
        bad_prefix["prefix_rows"][0] = (dict(row, group_id="foreign-group"), digest)
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._project_frozen_resource_recovery_packet(bad_prefix, rows, raw)

        changed_rows = copy.deepcopy(rows)
        changed_rows[0] = dict(changed_rows[0], status="changed-boundary")
        changed_raw = canonical(changed_rows)
        changed_packet = copy.deepcopy(packet)
        changed_pairs = [(row, MODULE.sha_bytes(line)) for row, line in zip(
            changed_rows, changed_raw.splitlines(keepends=True)
        )]
        changed_packet["prefix_rows"] = changed_pairs[:len(packet["prefix_rows"])]
        changed_packet["tail_rows"] = changed_pairs[len(packet["prefix_rows"]):]
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._project_frozen_resource_recovery_packet(
                changed_packet, changed_rows, changed_raw,
            )

    def test_valid_88_and_89_structural_tails_still_reach_exact_identity_gate(self) -> None:
        raw, rows, packet = self._actual_packet()
        new_contract = "a" * 64
        source_commit = "b" * 40
        plan_commit = "c" * 40
        base_plan = json.loads((MODULE.ROOT / MODULE.BASE_CONTRACT).read_bytes())
        base_codeql = next(group for group in base_plan["groups"]
                           if group["id"] == MODULE.CODEQL_GROUP)
        joern_argv = ["python3", "repaired-joern", "execute"]
        joern_output = "reports/raw/joern-common-v2/current108-v092-04"
        manifest = {
            "fixture_revision": "fixture-v092",
            "source_commit": source_commit,
            "plan_commit": plan_commit,
            "joern": {"argv": joern_argv, "output_root": joern_output},
            "codeql": {"argv": ["python3", "codeql", "execute"]},
        }
        joern = {
            "attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
            "timed_out": False, "capacity_loss": None,
            "fixture_revision": manifest["fixture_revision"],
            "contract_sha256": new_contract, "source_commit": source_commit,
            "plan_commit": plan_commit, "argv": joern_argv,
            "output_roots": [joern_output],
        }
        codeql = {
            "attempt_id": MODULE.CODEQL_ATTEMPT, "group_id": MODULE.CODEQL_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
            "timed_out": False, "capacity_loss": None,
            "fixture_revision": manifest["fixture_revision"],
            "contract_sha256": new_contract, "source_commit": source_commit,
            "plan_commit": plan_commit,
            "argv": ["python3", "codeql", "execute"],
            "output_roots": base_codeql["output_roots"],
        }
        for future in ([joern], [joern, codeql]):
            future_rows = rows + future
            future_raw = raw + canonical(future)
            self.assertEqual(MODULE._check_prefix(MODULE.ROOT, future_rows, future_raw), rows[:87])
            self.assertEqual(MODULE._tail(future_rows, final=len(future) == 2), future)
            future_packet = copy.deepcopy(packet)
            future_packet["tail_rows"] = list(future_packet["tail_rows"])
            future_packet["tail_rows"].extend(
                (row, MODULE.sha_bytes(line))
                for row, line in zip(future, canonical(future).splitlines(keepends=True))
            )
            projected = MODULE._project_frozen_resource_recovery_packet(
                future_packet, future_rows, future_raw,
            )
            self.assertEqual(len(projected["tail_rows"]), 29)

        context = {
            "manifest": manifest,
            "base": {"validated": {"plan": base_plan}},
            "repaired": {"validated": {"bytes_sha256": new_contract}},
        }
        MODULE._validate_tail_identity(context, [joern, codeql])
        bad_identity = copy.deepcopy(joern)
        bad_identity["argv"] = ["python3", "unreviewed-joern"]
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._validate_tail_identity(context, [bad_identity])

    def test_unknown_future_wrong_attempt_and_max_rows_are_rejected_before_adapter(self) -> None:
        raw, rows, _packet = self._actual_packet()
        valid = {
            "attempt_id": MODULE.JOERN_ATTEMPT, "group_id": MODULE.JOERN_GROUP,
            "execution_series": 1, "status": "completed", "exit_code": 0,
            "timed_out": False, "capacity_loss": None,
        }
        for bad in (
            dict(valid, group_id="unknown-group"),
            dict(valid, attempt_id="joern-swift-common108-attempt-05-series-01"),
        ):
            with self.assertRaises(MODULE.ContinuationError):
                MODULE._tail(rows + [bad], final=False)
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._tail(rows + [valid, dict(valid, attempt_id=MODULE.CODEQL_ATTEMPT,
                                               group_id=MODULE.CODEQL_GROUP),
                                  dict(valid, attempt_id="extra-attempt")], final=False)

    def test_frozen_tail_adapter_restores_original_on_validation_exception(self) -> None:
        raw, rows, packet = self._actual_packet()
        original_calls: list[tuple[dict, dict]] = []

        def original(validated: dict, projected: dict) -> None:
            original_calls.append((validated, projected))

        class FakeExecutor:
            _validate_scoped_tail = staticmethod(original)

            def validate_plan(self, _path: Path, *, repo_root: Path) -> dict:
                self._validate_scoped_tail({
                    "path": str((repo_root / Path(*MODULE._relative(MODULE.BASE_CONTRACT).parts)).resolve()),
                    "bytes_sha256": MODULE.BASE_SHA,
                }, packet)
                raise RuntimeError("synthetic validator failure")

        executor = FakeExecutor()
        saved = executor._validate_scoped_tail
        with self.assertRaisesRegex(RuntimeError, "synthetic validator failure"):
            MODULE._validate_base_with_historical_boundary(
                executor, MODULE.ROOT / MODULE.BASE_CONTRACT, MODULE.ROOT, rows, raw,
            )
        self.assertIs(executor._validate_scoped_tail, saved)
        self.assertEqual(len(original_calls), 1)
        self.assertEqual(len(original_calls[0][1]["tail_rows"]), 29)

    def test_nested_c3_dispatches_unchanged_before_outer_c4_projection(self) -> None:
        raw, rows, packet = self._actual_packet()
        nested_packet = self._nested_c3_packet(rows, raw)
        nested_validated = {
            "path": str((MODULE.ROOT / "reports/releases/v0.9.2/acquisition/resource-recovery-contract-03.json").resolve()),
            "bytes_sha256": "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063",
        }
        outer_validated = {
            "path": str((MODULE.ROOT / Path(*MODULE._relative(MODULE.BASE_CONTRACT).parts)).resolve()),
            "bytes_sha256": MODULE.BASE_SHA,
        }
        calls: list[tuple[dict, dict]] = []

        def original(validated: dict, supplied: dict) -> None:
            calls.append((validated, supplied))

        class SequencedExecutor:
            _validate_scoped_tail = staticmethod(original)

            def validate_plan(self, _path: Path, *, repo_root: Path) -> dict:
                self._validate_scoped_tail(nested_validated, nested_packet)
                self._validate_scoped_tail(outer_validated, packet)
                return outer_validated

        executor = SequencedExecutor()
        result = MODULE._validate_base_with_historical_boundary(
            executor, MODULE.ROOT / MODULE.BASE_CONTRACT, MODULE.ROOT, rows, raw,
        )
        self.assertIs(result, outer_validated)
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0][0], nested_validated)
        self.assertIs(calls[0][1], nested_packet)
        self.assertIs(calls[1][0], outer_validated)
        self.assertIsNot(calls[1][1], packet)
        self.assertEqual(len(calls[1][1]["tail_rows"]), 29)
        self.assertEqual(executor._validate_scoped_tail, original)

    def test_unknown_nested_identity_and_tampered_outer_packet_fail_closed(self) -> None:
        raw, rows, packet = self._actual_packet()
        calls = []

        def original(validated: dict, supplied: dict) -> None:
            calls.append((validated, supplied))

        outer_validated = {
            "path": str((MODULE.ROOT / Path(*MODULE._relative(MODULE.BASE_CONTRACT).parts)).resolve()),
            "bytes_sha256": MODULE.BASE_SHA,
        }

        class FakeExecutor:
            _validate_scoped_tail = staticmethod(original)

            def __init__(self, supplied: dict, validated: dict) -> None:
                self.supplied = supplied
                self.validated = validated

            def validate_plan(self, _path: Path, *, repo_root: Path) -> dict:
                self._validate_scoped_tail(self.validated, self.supplied)
                return outer_validated

        unknown = FakeExecutor(
            packet,
            {"path": str(MODULE.ROOT / "unknown-contract.json"), "bytes_sha256": "d" * 64},
        )
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._validate_base_with_historical_boundary(
                unknown, MODULE.ROOT / MODULE.BASE_CONTRACT, MODULE.ROOT, rows, raw,
            )
        tampered = copy.deepcopy(packet)
        row, _digest = tampered["tail_rows"][0]
        tampered["tail_rows"][0] = (row, "0" * 64)
        outer = FakeExecutor(tampered, outer_validated)
        with self.assertRaises(MODULE.ContinuationError):
            MODULE._validate_base_with_historical_boundary(
                outer, MODULE.ROOT / MODULE.BASE_CONTRACT, MODULE.ROOT, rows, raw,
            )


class FrozenLaunchGuardTests(unittest.TestCase):
    def _groups(self) -> tuple[dict, dict]:
        contract = json.loads(
            (MODULE.ROOT / MODULE.BASE_CONTRACT).read_text(encoding="utf-8")
        )
        old = next(
            group for group in contract["groups"] if group.get("id") == MODULE.JOERN_GROUP
        )
        self.assertIn("scripts/run-joern-common-v092.py", old["argv"])
        new = copy.deepcopy(old)
        # Match the builder's production repaired-shim argv shape while
        # retaining the base contract's exact inherited environment.
        new["argv"] = [
            "/usr/bin/python3", "scripts/joern_capability_repair_v092.py", "execute",
            "--plan", "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-02/execution-plan.json",
            "--evidence", "reports/releases/v0.9.2/qualification/joern-capability-repair-01/capability-evidence.json",
            "--plan-sha256", "76264424ddfa31b11788459368ae9b65058685cb7bab60d14353d9c96fca102f",
            "--evidence-sha256", "deefa524579114d6fa42271193b6f4def69e296ffd23023f1e72ae7d2ee4a005",
            "--output", "reports/raw/joern-common-v2/current108-v092-03",
        ]
        new["environment"].update(MODULE.LAUNCH_MARKERS)
        return old, new

    def test_actual_frozen_child_environment_preserves_exact_marker_delta(self) -> None:
        executor = MODULE._load_frozen(MODULE.ROOT, "execute")
        old, new = self._groups()
        MODULE._check_joern_launch_environment(executor, old, new)
        expanded = executor._child_environment(
            new, Path("/tmp/execution"), Path("/tmp/attempt"), Path("/tmp/cache")
        )
        self.assertEqual(
            {key: expanded[key] for key in MODULE.LAUNCH_MARKERS}, MODULE.LAUNCH_MARKERS
        )

    def test_missing_or_wrong_markers_and_inherited_changes_are_rejected(self) -> None:
        executor = MODULE._load_frozen(MODULE.ROOT, "execute")
        old, new = self._groups()
        for bad in (
            {key: value for key, value in new["environment"].items()
             if key != "DATAFLOWBENCH_V092_GROUP_ID"},
            dict(new["environment"], DATAFLOWBENCH_V092_GROUP_ID="other-group"),
            dict(new["environment"], PATH="/changed"),
        ):
            candidate = copy.deepcopy(new)
            candidate["environment"] = bad
            with self.assertRaises(MODULE.ContinuationError):
                MODULE._check_joern_launch_environment(executor, old, candidate)

    def test_immutable_runner_launch_guard_is_exercised_without_launching(self) -> None:
        runner_path = MODULE.ROOT / "scripts/joern_normal_runner_v092.py"
        self.assertEqual(MODULE.sha(runner_path), "683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4")
        spec = importlib.util.spec_from_file_location("joern_runner_guard_tested", runner_path)
        assert spec is not None and spec.loader is not None
        scripts = str(runner_path.parent)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with mock.patch.dict(os.environ, MODULE.LAUNCH_MARKERS, clear=True):
            runner._require_launch_guard(MODULE.JOERN_GROUP)
        with mock.patch.dict(os.environ, {"DATAFLOWBENCH_V092_GROUP_ID": MODULE.JOERN_GROUP}, clear=True):
            with self.assertRaises(Exception):
                runner._require_launch_guard(MODULE.JOERN_GROUP)
        with mock.patch.dict(os.environ, {
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
            "DATAFLOWBENCH_V092_GROUP_ID": "wrong-group",
        }, clear=True):
            with self.assertRaises(Exception):
                runner._require_launch_guard(MODULE.JOERN_GROUP)


class MaterializedAdmissionTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[dict, dict]:
        output = root / MODULE.MATERIALIZED_PREFLIGHT_PATH
        output.parent.mkdir(parents=True)
        plan_ref = {"path": "plan.json", "sha256": "a" * 64}
        evidence_ref = {"path": "evidence.json", "sha256": "b" * 64}
        checked = {
            "new_plan_path": plan_ref["path"],
            "new_plan_sha256": plan_ref["sha256"],
            "evidence_path": evidence_ref["path"],
            "evidence_sha256": evidence_ref["sha256"],
            "projection_sha256": "c" * 64,
            "launch_guard_checked": True,
            "launch_environment_markers": dict(MODULE.LAUNCH_MARKERS),
        }
        output.write_text(json.dumps(checked), encoding="utf-8")
        preflight_ref = {"path": MODULE.MATERIALIZED_PREFLIGHT_PATH,
                         "sha256": MODULE.sha(output)}
        receipt = {
            "materialized_source": str(
                (root / MODULE.MATERIALIZED_SOURCE_SUFFIX).resolve()
            ),
            "materialized_source_projected_bytes": 1,
            "materialized_launch_guard_checked": True,
            "materialized_launch_environment_markers": dict(MODULE.LAUNCH_MARKERS),
            "materialized_preflight_output": preflight_ref,
            "materialized_projection_sha256": "c" * 64,
        }
        manifest = {"artifacts": {
            "repaired_plan": plan_ref,
            "capability_evidence": evidence_ref,
            "joern_shim": {"path": "shim.py", "sha256": "d" * 64},
        }}
        return receipt, manifest

    def test_materialized_preflight_is_bound_to_projection_guard_and_markers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, manifest = self._fixture(root)
            with mock.patch.object(MODULE, "_recompute_repaired_projection",
                                   return_value="c" * 64):
                MODULE._check_materialized_preflight_fields(root, receipt, manifest)

    def test_materialized_preflight_marker_near_miss_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, manifest = self._fixture(root)
            receipt["materialized_launch_environment_markers"][
                "DATAFLOWBENCH_V092_GROUP_ID"] = "other-group"
            with mock.patch.object(MODULE, "_recompute_repaired_projection",
                                   return_value="c" * 64):
                with self.assertRaises(MODULE.ContinuationError):
                    MODULE._check_materialized_preflight_fields(root, receipt, manifest)


class SupervisorPermitTests(unittest.TestCase):
    def test_execute_only_permit_binds_live_pid_birth_and_argv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = (f"{MODULE.SUPERVISOR_STATE_SUFFIX}/"
                        f"{MODULE.JOERN_GROUP}-allow-start")
            permit_path = root / relative
            permit_path.parent.mkdir(parents=True)
            argv = ["/checkout/continuation-03.py", "execute",
                    "--manifest-sha256", "f" * 64, "--group", MODULE.JOERN_GROUP]
            birth = "Thu Oct 23 08:00:00 2026"
            permit_path.write_text(json.dumps({
                "pid": 4242,
                "birth": birth,
                "token": "token",
                "argv_sha256": MODULE.sha_bytes(json.dumps(argv).encode()),
            }), encoding="utf-8")
            with mock.patch.object(MODULE.os, "getpid", return_value=4242), \
                    mock.patch.object(MODULE.subprocess, "check_output", return_value=birth):
                with mock.patch.object(MODULE.sys, "argv", argv):
                    MODULE._check_supervisor_group_permit(root, MODULE.JOERN_GROUP)

    def test_execute_only_permit_rejects_wrong_birth_or_argv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = (f"{MODULE.SUPERVISOR_STATE_SUFFIX}/"
                        f"{MODULE.JOERN_GROUP}-allow-start")
            permit_path = root / relative
            permit_path.parent.mkdir(parents=True)
            argv = ["/checkout/continuation-03.py", "execute",
                    "--manifest-sha256", "f" * 64, "--group", MODULE.JOERN_GROUP]
            permit_path.write_text(json.dumps({
                "pid": 4242,
                "birth": "old-birth",
                "token": "token",
                "argv_sha256": MODULE.sha_bytes(json.dumps(argv).encode()),
            }), encoding="utf-8")
            with mock.patch.object(MODULE.os, "getpid", return_value=4242), \
                    mock.patch.object(MODULE.subprocess, "check_output", return_value="new-birth"), \
                    mock.patch.object(MODULE.sys, "argv", argv):
                with self.assertRaises(MODULE.ContinuationError):
                    MODULE._check_supervisor_group_permit(root, MODULE.JOERN_GROUP)
            permit = json.loads(permit_path.read_text(encoding="utf-8"))
            permit["birth"] = "new-birth"
            permit["argv_sha256"] = "0" * 64
            permit_path.write_text(json.dumps(permit), encoding="utf-8")
            with mock.patch.object(MODULE.os, "getpid", return_value=4242), \
                    mock.patch.object(MODULE.subprocess, "check_output", return_value="new-birth"), \
                    mock.patch.object(MODULE.sys, "argv", argv):
                with self.assertRaises(MODULE.ContinuationError):
                    MODULE._check_supervisor_group_permit(root, MODULE.JOERN_GROUP)

if __name__ == "__main__":
    unittest.main()
