#!/usr/bin/env python3
"""Harmless production-path regressions for the BF21 supervisor.

These tests load the actual supervisor entry points but keep every external
boundary inside a temporary fixture: no frozen executor, analyzer, checkout,
or production subprocess is started.  The fixture still exercises the
supervisor's real lease, child-entry, stage, and batch orchestration paths.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import sys
import unittest
from unittest.mock import patch


BASE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


supervisor = load("supervisor21_production_test", BASE / "bifrost-v0140-supervisor-21.py")
bridge_tests = load(
    "bridge16_fixture_for_supervisor21_production",
    BASE / "test-bifrost-v0140-frozen-parser-16.py",
)


def validated(group_id: str = "bifrost-a", deadline: int = 100) -> dict:
    return {
        "plan": {
            "groups": [{"id": group_id, "deadline_seconds": deadline}],
            "resource_guards": {"stop_free_gib": 48, "working_set_gib": 30},
            "resource_reservation": {},
            "source_commit": "a" * 40,
            "execution_series": 2,
        }
    }


class Child:
    def __init__(self, code: int = 0):
        self.code = code
        self.timeouts: list[float] = []
        self.pid = 43210

    def wait(self, timeout: float):
        self.timeouts.append(timeout)
        return self.code


class Supervisor21ProductionTests(unittest.TestCase):
    def test_wait_group_child_charges_setup_from_actual_popen(self):
        child = Child()
        with patch.object(supervisor.time, "monotonic", return_value=150.0):
            code = supervisor._wait_group_child(
                child, validated(), "bifrost-a", popen_monotonic=100.0
            )
        self.assertEqual(code, 0)
        self.assertEqual(child.timeouts, [650.0])

    def test_wait_group_child_rejects_expired_or_backwards_popen_clock(self):
        with patch.object(supervisor.time, "monotonic", return_value=50.0):
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor._wait_group_child(
                    Child(), validated(), "bifrost-a", popen_monotonic=100.0
                )
        with patch.object(supervisor.time, "monotonic", return_value=801.0):
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor._wait_group_child(
                    Child(), validated(), "bifrost-a", popen_monotonic=100.0
                )

    def test_dispatch_lease_preserves_popen_origin_and_setup_charge(self):
        value = validated(deadline=100)
        origin = supervisor.dt.datetime.fromisoformat(supervisor.ORIGIN).timestamp()
        result = supervisor._dispatch_lease(
            value,
            "bifrost-a",
            popen_monotonic=100.0,
            now_seconds=origin + 500.0,
            now_monotonic=125.0,
        )
        runtime = result["execution_window_runtime"]
        self.assertEqual(runtime["popen_monotonic"], 100.0)
        self.assertEqual(runtime["setup_elapsed_seconds"], 25.0)
        self.assertEqual(runtime["per_attempt_lease_seconds"], 675.0)
        self.assertEqual(result["total_wall_budget_seconds"], 1175.0)

    def test_dispatch_lease_rejects_backwards_or_expired_setup(self):
        origin = supervisor.dt.datetime.fromisoformat(supervisor.ORIGIN).timestamp()
        with self.assertRaises(supervisor.Supervisor21Error):
            supervisor._dispatch_lease(
                validated(), "bifrost-a", popen_monotonic=100.0,
                now_seconds=origin, now_monotonic=99.0,
            )
        with self.assertRaises(supervisor.Supervisor21Error):
            supervisor._dispatch_lease(
                validated(deadline=1), "bifrost-a", popen_monotonic=100.0,
                now_seconds=origin, now_monotonic=701.0,
            )

    def test_main_import_and_child_entrypoint_are_fixed_and_unbound_mode_fails(self):
        with self.assertRaises(supervisor.Supervisor21Error):
            supervisor.main([])
        captured: dict[str, object] = {}

        def child_main(args: argparse.Namespace) -> int:
            captured["args"] = args
            return 0

        argv = [
            "--child", "--root", tempfile.gettempdir(), "--manifest", supervisor.MANIFEST_PATH,
            "--manifest-sha256", "a" * 64, "--group", "bifrost-a",
            "--attempt-id", "bifrost-a-attempt-02-series-02",
            "--bridge-context", supervisor.CONTEXT_PATH, "--context-sha256", "b" * 64,
            "--lock-fd", "3", "--parent-stage", "sidecars/parent.json",
            "--parent-stage-sha256", "c" * 64, "--popen-monotonic", "100.0",
        ]
        with patch.object(supervisor, "_child_main", side_effect=child_main):
            self.assertEqual(supervisor.main(argv), 0)
        args = captured["args"]
        self.assertTrue(args.child)
        self.assertEqual(args.group, "bifrost-a")
        self.assertEqual(args.lock_fd, 3)

    def test_child_permit_uses_os_invocation_and_rejects_argv_near_misses(self):
        code = (
            "import json,sys; "
            "print(json.dumps({'orig': getattr(sys, 'orig_argv', None), 'argv': sys.argv}))"
        )
        launcher = getattr(sys, "orig_argv", [sys.executable])[0]
        completed = subprocess.run(
            [launcher, "-E", "-c", code, "fixture-child"],
            check=True, capture_output=True, text=True,
        )
        observed = json.loads(completed.stdout)
        actual = observed["orig"]
        if actual is None:
            # Xcode's bundled Python 3.9 predates sys.orig_argv.  The
            # supervisor's production runtime is newer; still verify the
            # child-visible argv shape here and exercise the exact binding
            # with a synthetic orig_argv in the child fixture below.
            self.assertEqual(observed["argv"], ["-c", "fixture-child"])
            actual = [launcher, "-E", "-c", code, "fixture-child"]
        else:
            self.assertEqual(actual[:3], [launcher, "-E", "-c"])
            self.assertEqual(actual[3:], [code, "fixture-child"])
        self.assertEqual(observed["argv"], ["-c", "fixture-child"])
        self.assertNotEqual(observed["argv"], actual)
        signed = supervisor.sha256(supervisor.canonical_json(actual))
        self.assertNotEqual(
            signed,
            supervisor.sha256(supervisor.canonical_json(["/wrong/python", *actual[1:]])),
        )
        self.assertNotEqual(
            signed,
            supervisor.sha256(supervisor.canonical_json([actual[0], "-B", *actual[2:]])),
        )
        self.assertNotEqual(
            signed,
            supervisor.sha256(supervisor.canonical_json([*actual[:-1], "wrong-child"])),
        )

    def test_raw_permit_binds_parent_and_group_stage_fields_and_rejects_near_misses(self):
        graph = types.SimpleNamespace(graph_sha256="g" * 64)
        stage = types.SimpleNamespace(identity_sha256="s" * 64, graph=graph)
        command = {"argv": ["python-child", "--group", "fixture"],
                   "command_spec_sha256": "c" * 64}
        parent_command = {"argv": ["python-supervisor"], "command_spec_sha256": None}
        with patch.object(supervisor, "_birth", return_value="birth-identity"):
            parent = supervisor.raw_permit(1234, parent_command, scope="parent", stage=stage)
            group = supervisor.raw_permit(
                1234, command, scope="group", group_id="fixture",
                attempt_id="fixture-attempt-02-series-02", stage=stage,
            )
        self.assertEqual(parent["scope"], "parent")
        self.assertIsNone(parent["command_spec_sha256"])
        self.assertEqual(parent["stage_identity_sha256"], stage.identity_sha256)
        self.assertEqual(parent["graph_sha256"], graph.graph_sha256)
        self.assertNotIn("group_id", parent)
        self.assertEqual(group["scope"], "group")
        self.assertEqual(group["group_id"], "fixture")
        self.assertEqual(group["attempt_id"], "fixture-attempt-02-series-02")
        self.assertEqual(group["command_spec_sha256"], command["command_spec_sha256"])
        self.assertEqual(group["parent_stage_identity_sha256"], stage.identity_sha256)
        self.assertEqual(group["permit_id"], supervisor.sha256(
            supervisor.canonical_json({**{key: value for key, value in group.items()
                                        if key != "permit_id"}, "permit_id": None})
        ))
        with patch.object(supervisor, "_birth", return_value="birth-identity"):
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.raw_permit(1234, command, scope="group", stage=stage)
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.raw_permit(
                    1234, {"argv": command["argv"], "command_spec_sha256": None},
                    scope="group", group_id="fixture",
                    attempt_id="fixture-attempt-02-series-02", stage=stage,
                )
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.raw_permit(1234, command, scope="parent", stage=stage)

    def test_stage_sequence_uses_exact_21_parent_and_20_child_states_and_near_misses_fail(self):
        fixture = bridge_tests.BridgeFixture(
            "test_complete_graph_is_bound_and_serialization_is_rejected"
        )
        fixture.setUp()
        try:
            parents = []
            raw = b""
            ledgers = []
            for index in range(supervisor.PARENT_STAGE_COUNT):
                raw += bridge_tests.b.canonical_json(
                    {"attempt_id": f"a{index}", "status": "completed"}
                )
                path = fixture.root / f"ledger-{index:02d}.jsonl"
                path.write_bytes(raw)
                ledgers.append({"path": path.name, "sha256": bridge_tests.b.sha256(raw), "rows": index + 1})
            specs = [
                {
                    "ledger": ledger,
                    "runtime": {"stage": index},
                    "graph": fixture.graph,
                    "source_commit": "a" * 40,
                    "plan_commit": "b" * 40,
                    "contract_sha256": "c" * 64,
                    "lock": fixture.lock_id,
                    "sidecars": {"admission": fixture.sidecar},
                    "source_refs": [fixture.source],
                    "analyzer_deadline_seconds": 13840,
                    "created_monotonic": float(index),
                }
                for index, ledger in enumerate(ledgers)
            ]
            parents = bridge_tests.b.build_parent_sequence(fixture.root, specs)
            child_specs = [
                {
                    "parent": parents[index],
                    "runtime": {"child": index},
                    "graph": fixture.graph,
                    "source_refs": [fixture.source],
                    "child_creator_pid": 300 + index,
                    "child_creator_birth": f"creator-{index}",
                    "child_pid": 400 + index,
                    "child_birth": f"child-{index}",
                    "analyzer_deadline_seconds": 13840,
                    "popen_monotonic": float(index),
                    "sidecars": {path: fixture.put(path, f"dispatch:{index}:{kind}".encode())
                        for kind in ("admission", "phase", "supervisor-permit")
                        for path in (f"sidecars/group-{index:02d}/{kind}.json",)},
                    "ledger": ledgers[index],
                }
                for index in range(supervisor.CHILD_STAGE_COUNT)
            ]
            children = bridge_tests.b.build_child_sequence(fixture.root, child_specs, parents)
            result = supervisor.validate_stage_sequence(
                fixture.root, parents, children, [fixture.graph] * len(parents),
                stage_bridges=[bridge_tests.b] * len(parents),
            )
            self.assertEqual(result["parent_stages"], 21)
            self.assertEqual(result["child_stages"], 20)
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.validate_stage_sequence(
                    fixture.root, parents[:-1], children, [fixture.graph] * 20,
                    stage_bridges=[bridge_tests.b] * 20,
                )
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.staged_parent_ready(
                    fixture.root, parents[1], fixture.graph, index=0,
                    expected_ledger_sha256=parents[0].identity.ledger_sha256,
                    stage_bridge=bridge_tests.b,
                )
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.staged_parent_ready(
                    fixture.root, parents[0], fixture.graph, index=0,
                    expected_ledger_sha256="0" * 64,
                    stage_bridge=bridge_tests.b,
                )
            foreign_modules = {
                name: types.ModuleType(f"fixture_foreign_{name}")
                for name in bridge_tests.b.REQUIRED_GRAPH_NAMES
            }
            foreign_graph = bridge_tests.b.load_graph(
                fixture.root, fixture.refs, fixture_modules=foreign_modules, fixture_only=True
            )
            with self.assertRaises(supervisor.Supervisor21Error):
                supervisor.staged_child_ready(
                    fixture.root, children[0], parents[0], foreign_graph,
                    now_monotonic=1.0, stage_bridge=bridge_tests.b,
                )
        finally:
            fixture.tearDown()

    def test_run_frozen_group_requires_dispatch_origin_and_uses_lossless_fixture_runtime(self):
        """Exercise the actual child entrypoint without starting an analyzer."""
        group = "bifrost-a"
        attempt = "bifrost-a-attempt-02-series-02"
        context_digest = "d" * 64
        contract_digest = "c" * 64
        manifest = {
            "core_identity": {"id": "fixture-core"},
            "execution_admission_slots": {
                group: {
                    "attempt_id": attempt,
                    "admission_path": "slots/a/admission.json",
                    "phase_gate_path": "slots/a/phase.json",
                }
            }
        }
        core = {
            "contract": {"path": "contract.json", "sha256": contract_digest},
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "lock_path": "canonical.lock",
        }
        protocol = types.SimpleNamespace(_terminal_identity=lambda *args, **kwargs: None)
        fake_executor = types.SimpleNamespace()
        fake_executor._exclusive_lock = lambda: contextlib.nullcontext()
        fake_executor._matrix_elapsed_wall = lambda runtime, *, now_seconds=None: 1.0
        fake_executor._contenders = lambda table: []
        fake_executor._assert_contract_snapshot = lambda runtime: "b" * 40
        fake_executor._assert_fresh = lambda root, group_value, reports, series: (
            Path("attempt"), Path("execution"), Path("cache"), Path("ledger"),
            f"{group_value['id']}-attempt-02-series-02"
        )
        fake_executor._materialize_source = lambda *args, **kwargs: 0
        dispatch_events = []

        def run_group(runtime, group_id):
            dispatch_events.append("run_group")
            return {
                "status": "completed", "group_id": group_id, "attempt_id": attempt,
                "source_commit": "a" * 40, "plan_commit": "b" * 40,
                "contract_sha256": contract_digest, "execution_series": 2,
            }

        fake_executor.run_group = run_group
        loader_calls = []

        @contextlib.contextmanager
        def runtime_loader_scope(root, *, executor, graph, module_names):
            self.assertIs(executor, fake_executor)
            self.assertIs(module_names, loader_module.PRODUCTION_MODULE_NAMES)
            loader_calls.append("enter")
            try:
                yield
            finally:
                loader_calls.append("exit")

        loader_module = types.SimpleNamespace(scoped_runtime_loaders=runtime_loader_scope,
                                              PRODUCTION_MODULE_NAMES={"fixture": "explicit"})
        graph = types.SimpleNamespace(
            graph_sha256="g" * 64,
            module=lambda name: loader_module if name == "runtime_loaders21" else None,
        )
        parent_binding = {
            "manifest_ref": {"path": supervisor.MANIFEST_PATH, "sha256": "e" * 64},
            "core_identity": manifest["core_identity"],
            "stage_identity_sha256": "f" * 64,
            "graph_sha256": graph.graph_sha256,
            "lock": {},
            "ledger_ref": {"path": "ledger.jsonl", "sha256": "a" * 64, "rows": 1},
        }
        child_stages: list[object] = []
        guard_calls = []
        fail_guard_at = [None]

        def child_ready(root, child, **kwargs):
            self.assertIs(child, child_stages[-1])
            self.assertIs(kwargs["graph"], graph)
            self.assertIs(kwargs["stage_bridge"], fake_bridge)
            self.assertEqual(kwargs["core_identity"], manifest["core_identity"])
            self.assertEqual(set(kwargs["dispatch_sidecars"]), {
                "slots/a/admission.json", "slots/a/phase.json", "slots/a/supervisor-permit.json"})
            self.assertEqual(kwargs["now_monotonic"], 110.0)
            guard_calls.append(kwargs)
            dispatch_events.append("ready")
            if len(guard_calls) == fail_guard_at[0]:
                raise bridge_tests.b.FrozenBridge16Error("stale parent witness or expired lease")
            return {"status": "child-stage-admitted"}

        admission_object = types.SimpleNamespace(validate_child_stage_from_receipt=child_ready)

        def prepare_child_graph(root, refs, host_modules):
            self.assertEqual(set(host_modules), {
                "supervisor21", "protocol21", "admission21", "bridge16"})
            self.assertIs(host_modules["supervisor21"], supervisor)
            self.assertIs(host_modules["protocol21"], protocol)
            self.assertIs(host_modules["admission21"], admission_object)
            self.assertIs(host_modules["bridge16"], fake_bridge)
            return graph

        fake_bridge = types.SimpleNamespace(
            _core_graph_inputs=lambda core_value: {},
            prepare_graph=prepare_child_graph,
            _read_compact_parent=lambda root, ref, **kwargs: parent_binding,
            LockIdentity=bridge_tests.b.LockIdentity,
            Lease=bridge_tests.b.Lease,
            validate_lease_progress=lambda *args, **kwargs: 1.0,
            create_child_stage=lambda *args, **kwargs: child_stages.append(types.SimpleNamespace()) or child_stages[-1],
        )
        runtime = {
            "validated": {
                **validated(group),
                "bytes_sha256": contract_digest,
            },
            "modules": {"executor": fake_executor, "replacement05": object()},
            "bridge_context": {"context_digest": context_digest},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "slots/a").mkdir(parents=True)
            (root / "slots/a/admission.json").write_text(
                json.dumps({"supervisor_permit": {"scope": "group", "group_id": group, "attempt_id": attempt}})
            )
            (root / "slots/a/phase.json").write_text(
                json.dumps({"group_id": group, "attempt_id": attempt})
            )
            fixture_orig_argv = [
                getattr(sys, "orig_argv", [sys.executable])[0], "-E", "fake-supervisor21-child.py",
                "--group", group, "--attempt-id", attempt,
            ]
            had_orig_argv = hasattr(os.sys, "orig_argv")
            saved_orig_argv = getattr(os.sys, "orig_argv", None)
            os.sys.orig_argv = fixture_orig_argv
            permit = {
                "schema": supervisor.RAW_PERMIT_SCHEMA, "scope": "group", "pid": os.getpid(),
                "group_id": group, "attempt_id": attempt,
                "argv_sha256": supervisor.sha256(
                    supervisor.canonical_json(list(os.sys.orig_argv))
                ),
            }
            (root / "slots/a/supervisor-permit.json").write_text(json.dumps(permit))
            lock = root / "canonical.lock"
            lock.write_bytes(b"lock")
            fd = os.open(lock, os.O_RDWR)
            lock_stat = os.fstat(fd)
            parent_binding["lock"] = {
                "path": str(lock), "dev": lock_stat.st_dev, "ino": lock_stat.st_ino,
                "parent_pid": os.getppid(), "parent_birth": "parent-birth",
            }
            permit.update({
                "birth": "child-birth",
                "parent_stage_identity_sha256": parent_binding["stage_identity_sha256"],
                "stage_identity_sha256": parent_binding["stage_identity_sha256"],
                "graph_sha256": graph.graph_sha256,
            })
            (root / "slots/a/supervisor-permit.json").write_text(json.dumps(permit))
            old_marker = os.environ.get(supervisor.EXPERIMENT_ENV)
            os.environ[supervisor.EXPERIMENT_ENV] = "1"
            try:
                with patch.object(supervisor, "_static", return_value=(protocol, manifest, core)), \
                     patch.object(supervisor, "_context_file", return_value={"context_digest": context_digest}), \
                     patch.object(supervisor, "_load_admission", return_value=admission_object), \
                     patch.object(supervisor, "_load_bridge", return_value=fake_bridge), \
                     patch.object(supervisor, "_actual_runtime_context", return_value=runtime), \
                     patch.object(supervisor, "_load_protocol", return_value=protocol), \
                     patch.object(supervisor, "_bound", return_value=supervisor.canonical_json(validated(group)["plan"])), \
                     patch.object(supervisor, "_birth", side_effect=lambda pid: "parent-birth" if pid == os.getppid() else "child-birth"), \
                     patch.object(supervisor, "_dispatch_lease", autospec=True) as dispatch:
                    dispatch.return_value = runtime["validated"]

                    def run_child() -> dict[str, object]:
                        return supervisor._run_frozen_group(
                            root, supervisor.MANIFEST_PATH, "e" * 64, group, attempt,
                            "slots/a/bridge-context.json", context_digest, fd,
                            parent_stage_ref={"path": "sidecars/parent.json", "sha256": "f" * 64},
                            popen_monotonic=100.0,
                        )

                    permit["attempt_id"] = "wrong-attempt"
                    (root / "slots/a/supervisor-permit.json").write_text(json.dumps(permit))
                    with patch.object(supervisor.time, "monotonic", return_value=110.0):
                        with self.assertRaises(supervisor.Supervisor21Error):
                            run_child()
                    permit["attempt_id"] = attempt
                    parent_binding["lock"]["parent_birth"] = "wrong-parent-birth"
                    (root / "slots/a/supervisor-permit.json").write_text(json.dumps(permit))
                    with patch.object(supervisor.time, "monotonic", return_value=110.0):
                        with self.assertRaises(supervisor.Supervisor21Error):
                            run_child()
                    parent_binding["lock"]["parent_birth"] = "parent-birth"
                    parent_binding["lock"]["ino"] += 1
                    (root / "slots/a/supervisor-permit.json").write_text(json.dumps(permit))
                    with patch.object(supervisor.time, "monotonic", return_value=110.0):
                        with self.assertRaises(supervisor.Supervisor21Error):
                            run_child()
                    parent_binding["lock"]["ino"] = lock_stat.st_ino
                    with patch.object(supervisor.time, "monotonic", return_value=250.0):
                        with self.assertRaises(supervisor.Supervisor21Error):
                            run_child()
                    with patch.object(supervisor.time, "monotonic", return_value=110.0):
                        result = run_child()
                    self.assertEqual(result["status"], "completed")
                    self.assertEqual(loader_calls, ["enter", "exit"])
                    dispatch.assert_called_once()
                    self.assertIn("popen_monotonic", dispatch.call_args.kwargs)
                    self.assertIsInstance(dispatch.call_args.kwargs["popen_monotonic"], float)
                    self.assertEqual(len(child_stages), 1)
                    self.assertEqual(dispatch_events, ["ready", "ready", "run_group"])
                    self.assertEqual(len(guard_calls), 2)
                    # Either guard fails closed, including the final guard inside
                    # the loader/contract/fresh/resource scopes. No retry occurs.
                    restored = (fake_executor._exclusive_lock, fake_executor._matrix_elapsed_wall,
                                fake_executor._contenders)
                    for failing_call in (1, 2):
                        guard_calls.clear()
                        dispatch_events.clear()
                        loader_calls.clear()
                        fail_guard_at[0] = failing_call
                        with patch.object(supervisor.time, "monotonic", return_value=110.0):
                            with self.assertRaises(bridge_tests.b.FrozenBridge16Error):
                                run_child()
                        self.assertEqual(dispatch_events, ["ready"] * failing_call)
                        self.assertEqual(loader_calls, [] if failing_call == 1 else ["enter", "exit"])
                        self.assertEqual((fake_executor._exclusive_lock,
                                          fake_executor._matrix_elapsed_wall,
                                          fake_executor._contenders), restored)
            finally:
                os.close(fd)
                if had_orig_argv:
                    os.sys.orig_argv = saved_orig_argv
                else:
                    del os.sys.orig_argv
                if old_marker is None:
                    os.environ.pop(supervisor.EXPERIMENT_ENV, None)
                else:
                    os.environ[supervisor.EXPERIMENT_ENV] = old_marker

    def test_actual_child_entrypoint_composes_real_receipt_guard(self):
        """Synthetic executor boundary, actual admission and opaque receipt guard."""
        case = bridge_tests.ChildReadyReceiptTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        fixture, bridge = case.fixture, case.b
        root = fixture.root
        admission = load("admission21_real_guard_production_test", BASE / "bifrost-v0140-admission-21.py")
        group, attempt = "bifrost-a", "bifrost-a-attempt-02-series-02"
        events = []
        stale_inside_loader_scope = [False]
        protocol = types.SimpleNamespace(_terminal_identity=lambda *args, **kwargs: None)
        executor = types.SimpleNamespace(
            _exclusive_lock=lambda: contextlib.nullcontext(),
            _matrix_elapsed_wall=lambda runtime, **kwargs: 1.0,
            _contenders=lambda table: [], _assert_contract_snapshot=lambda runtime: "b" * 40,
            _assert_fresh=lambda *args: (Path("attempt"), Path("execution"), Path("cache"),
                                       Path("ledger"), attempt),
            _materialize_source=lambda *args, **kwargs: 0,
            run_group=lambda runtime, group_id: events.append("run_group") or {"status": "completed"},
        )

        @contextlib.contextmanager
        def loaders_scope(*args, **kwargs):
            events.append("loader-enter")
            if stale_inside_loader_scope[0]:
                (root / fixture.source["path"]).write_bytes(b"stale source witness")
            try:
                yield
            finally:
                events.append("loader-exit")

        loaders = types.SimpleNamespace(scoped_runtime_loaders=loaders_scope,
                                         PRODUCTION_MODULE_NAMES={"fixture": "explicit"})
        # Reuse the designer's real receipt/source/inventory fixture, selecting
        # actual guard-owning objects under unchanged source-backed bindings.
        modules = dict(case.child_graph._by_name)
        members = []
        for name, member in modules.items():
            obj = {"bridge16": bridge, "admission21": admission}.get(name, member.module_object)
            members.append(bridge.GraphMember(name, member.canonical_path,
                member.source_sha256, obj, "integration:" + name))
        loader_ref = fixture.put("graph/runtime-loaders19.py", b"# synthetic downstream loader boundary\n")
        members.append(bridge.GraphMember("runtime_loaders21", loader_ref["path"],
                                         loader_ref["sha256"], loaders, "integration:loaders"))
        graph = bridge.PinnedBridgeGraph(members, fixture_only=True)
        fixture.graph = graph
        fixture.lock_id = bridge.capture_lock(root, str(fixture.lock), os.getppid(), "parent-birth")
        core = dict(case.core, contract={"path": "contract.json", "sha256": "c" * 64},
                    lock_path="canonical.lock", sidecar_namespace="integration-sidecars")
        parent = fixture.parent()
        parent_ref = bridge.write_compact_stage_receipt(
            root, "integration-sidecars/stages/stage-00.json", parent,
            status="parent-stage-verified", sidecar_names=("admission",),
            manifest_ref=case.manifest_ref, core_identity=case.core_identity, core=core)
        parent_binding = bridge._read_compact_parent(root, parent_ref, core=core)
        manifest = {"core_identity": case.core_identity, "execution_admission_slots": {group: {
            "attempt_id": attempt, "admission_path": "sidecars/group/admission.json",
            "phase_gate_path": "sidecars/group/phase.json"}}}
        fixture.put("sidecars/group/admission.json", json.dumps({"supervisor_permit": {
            "scope": "group", "group_id": group, "attempt_id": attempt}}).encode())
        fixture.put("sidecars/group/phase.json", json.dumps({"group_id": group, "attempt_id": attempt}).encode())
        invocation = [sys.executable, "-E", "synthetic-supervisor21.py", "--group", group]
        permit = {"schema": supervisor.RAW_PERMIT_SCHEMA, "scope": "group", "pid": os.getpid(),
            "birth": "child-birth", "group_id": group, "attempt_id": attempt,
            "argv_sha256": supervisor.sha256(supervisor.canonical_json(invocation)),
            "parent_stage_identity_sha256": parent.identity_sha256,
            "stage_identity_sha256": parent.identity_sha256, "graph_sha256": graph.graph_sha256}
        fixture.put("sidecars/group/supervisor-permit.json", json.dumps(permit).encode())
        dispatch = {path: supervisor._file_ref(root, path, "synthetic dispatch")
                    for path in case.dispatch}
        child = bridge.build_child_stage(root, parent_binding=parent_binding,
            runtime={"synthetic": object()}, graph=graph, source_refs=[fixture.source],
            child_creator_pid=os.getppid(), child_creator_birth="parent-birth",
            child_pid=os.getpid(), child_birth="child-birth", analyzer_deadline_seconds=13840,
            popen_monotonic=100, sidecars=dispatch, ledger=fixture.ledger)
        runtime = {"validated": {**validated(group, 13840), "bytes_sha256": "c" * 64},
                   "modules": {"executor": executor, "replacement05": object()},
                   "bridge_context": {"context_digest": "d" * 64}}
        original_guard = bridge.assert_child_ready_from_receipt
        original_admission = admission.validate_child_stage_from_receipt
        fd = os.open(fixture.lock, os.O_RDWR)
        self.addCleanup(os.close, fd)
        calls = []
        # A wrapping spy retains and invokes the actual guard body. It does
        # not return synthetic success or replace the admission wrapper.
        def observe_guard(*args, **kwargs):
            calls.append(kwargs)
            events.append("real-guard")
            return original_guard(*args, **kwargs)

        def run():
            return supervisor._run_frozen_group(root, case.manifest_ref["path"],
                case.manifest_ref["sha256"], group, attempt,
                "sidecars/group/bridge-context.json", "d" * 64, fd,
                parent_stage_ref=parent_ref, popen_monotonic=100.0)

        with patch.dict(os.environ, {supervisor.EXPERIMENT_ENV: "1"}), \
             patch.object(sys, "orig_argv", invocation), \
             patch.object(supervisor, "_static", return_value=(protocol, manifest, core)), \
             patch.object(supervisor, "_load_admission", return_value=admission), \
             patch.object(supervisor, "_load_bridge", return_value=bridge), \
             patch.object(bridge, "_core_graph_inputs", return_value={}), \
             patch.object(bridge, "prepare_graph", return_value=graph), \
             patch.object(bridge, "create_child_stage", return_value=child), \
             patch.object(bridge, "assert_child_ready_from_receipt", side_effect=observe_guard), \
             patch.object(supervisor, "_actual_runtime_context", return_value=runtime), \
             patch.object(supervisor, "_bound", return_value=supervisor.canonical_json(validated(group, 13840)["plan"])), \
             patch.object(supervisor, "_birth", side_effect=lambda pid: "parent-birth" if pid == os.getppid() else "child-birth"), \
             patch.object(supervisor, "_dispatch_lease", return_value=runtime["validated"]):
            with patch.object(supervisor.time, "monotonic", return_value=110.0):
                self.assertEqual(run()["status"], "completed")
            self.assertEqual(events, ["real-guard", "loader-enter", "real-guard", "run_group", "loader-exit"])
            self.assertEqual(len(calls), 2)
            self.assertIs(admission.validate_child_stage_from_receipt, original_admission)
            for call in calls:
                self.assertIs(call["graph"], graph)
                self.assertEqual(call["parent_receipt_ref"], parent_ref)
            events.clear()
            calls.clear()
            # Expiry occurs in the actual guard, after handshake and the
            # supervisor's first lease check have passed. No runtime starts.
            with patch.object(supervisor.time, "monotonic", side_effect=[110.0, 110.0, 14541.0]):
                with self.assertRaisesRegex(bridge.FrozenBridge16Error, "lease expired"):
                    run()
            self.assertEqual(events, ["real-guard"])
            self.assertEqual(len(calls), 1)
            events.clear()
            calls.clear()
            # The first real guard passes. Change a witnessed source only
            # inside the loader scope: the final real guard must reject it
            # before dispatch and all temporary executor hooks must unwind.
            restored = (executor._exclusive_lock, executor._matrix_elapsed_wall, executor._contenders)
            stale_inside_loader_scope[0] = True
            with patch.object(supervisor.time, "monotonic", return_value=110.0):
                with self.assertRaisesRegex(bridge.FrozenBridge16Error, "changed|differs"):
                    run()
            self.assertEqual(events, ["real-guard", "loader-enter", "real-guard", "loader-exit"])
            self.assertEqual(len(calls), 2)
            self.assertEqual((executor._exclusive_lock, executor._matrix_elapsed_wall,
                              executor._contenders), restored)
        self.assertIs(bridge.assert_child_ready_from_receipt, original_guard)

    def test_run_groups_uses_one_fixed_child_and_forwards_its_popen_origin(self):
        """Exercise the real batch entrypoint with exact 21/20 stage counts."""
        test = self
        groups = [f"bifrost-fixture-{index:02d}" for index in range(20)]
        context_digest = "d" * 64
        manifest_sha = "e" * 64
        slots = {
            group: {
                "attempt_id": f"{group}-attempt-02-series-02",
                "admission_path": f"slots/{index:02d}/admission.json",
                "phase_gate_path": f"slots/{index:02d}/phase.json",
                "completion_path": f"slots/{index:02d}/completion.json",
            }
            for index, group in enumerate(groups)
        }
        manifest = {
            "core_identity": {"id": "fixture-core"},
            "execution_admission_slots": slots,
        }
        plan = validated(groups[0])
        context = {
            "context_digest": context_digest,
            "validated_full_normalized_plan": plan,
            "checker_summary_or_pending": {"full_release_gate_satisfied": True},
        }
        core = {
            "replacement_groups": groups,
            "execution_admission_slots": slots,
            "graph_refs": {},
            "sidecar_namespace": "sidecars",
            "lock_path": "canonical.lock",
            "breadth_first_authority": {"scope": "fixture"},
            "incoming_history": {"schema": "fixture"},
        }

        class Protocol:
            def write_immutable(self, root, relative, value):
                raw = supervisor.canonical_json(value)
                target = Path(root) / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                return {"path": relative, "sha256": supervisor.sha256(raw)}

        class Stage:
            def __init__(self, index):
                self.identity = types.SimpleNamespace(index=index)
                self.sidecars = {}
                executor = types.SimpleNamespace()
                self.runtime = types.SimpleNamespace(objects={
                    "bridge_context": context,
                    "validated": plan,
                    "modules": {"executor": executor},
                })

        class Admission:
            def __init__(self):
                self.calls: list[str] = []
                self.completions = 0
                self.final_stage_factory = None

            def validate_authorization_bundle(self, *args, **kwargs):
                return {
                    "parent": {"path": "parent-auth", "sha256": "6" * 64},
                    "groups": {
                        item: {"path": f"auth/{index:02d}", "sha256": "7" * 64}
                        for index, item in enumerate(groups)
                    },
                }

            def admit_parent(self, *args, **kwargs):
                self.calls.append("parent")
                return {"path": "sidecars/parent.json", "sha256": "1" * 64}

            def admit_group(self, *args, **kwargs):
                self.calls.append("group")
                return {"path": "group-admission", "sha256": "2" * 64}

            def write_phase_gate(self, *args, **kwargs):
                self.calls.append("phase")
                return {"path": "group-phase", "sha256": "3" * 64}

            def _write_bytes_exclusive(self, root, relative, raw):
                return {"path": relative, "sha256": supervisor.sha256(raw)}

            def write_completion(self, *args, **kwargs):
                self.calls.append("completion")
                self.completions += 1
                return (
                    {"path": "group-completion", "sha256": "4" * 64},
                    self.final_stage_factory(self.completions),
                )

        class Bridge:
            def __init__(self):
                self.parent_stages = 0
                self.runtime_loads = 0
                self.prepare_graph_calls = 0
                self.graph = types.SimpleNamespace(
                    module=lambda name: types.SimpleNamespace(
                        scoped_runtime_loaders=lambda *args, **kwargs: contextlib.nullcontext(),
                        PRODUCTION_MODULE_NAMES={"fixture": "explicit"},
                    )
                )

            def _core_graph_inputs(self, core_value):
                return core_value["graph_refs"]

            def prepare_graph(self, root, refs, host_modules):
                test.assertEqual(set(host_modules), {
                    "supervisor21", "protocol21", "admission21", "bridge16"})
                test.assertIs(host_modules["supervisor21"], supervisor)
                test.assertIs(host_modules["admission21"], admission)
                test.assertIs(host_modules["bridge16"], self)
                self.prepare_graph_calls += 1
                return self.graph

            def capture_lock(self, root, path, pid, birth):
                return types.SimpleNamespace(path=str(Path(root) / path),
                                             parent_pid=pid, parent_birth=birth)

            def create_parent_stage(self, root, core_value, manifest_ref, index,
                                    lock_identity, ledger_ref, **kwargs):
                self.parent_stages = max(self.parent_stages, index + 1)
                self.runtime_loads += 1
                return Stage(index)

            def runtime_objects(self, stage):
                return stage.runtime

            def assert_stage_current(self, root, stage, graph):
                return None

            def write_compact_stage_receipt(self, root, path, stage, **kwargs):
                index = stage.identity.index
                test.assertEqual(path, f"{core['sidecar_namespace']}/stages/stage-{index:02d}.json")
                test.assertEqual(kwargs["status"], "parent-stage-verified" if index == 0
                                 else "successor-stage-verified")
                expected = None if index == 0 else {
                    "path": f"{core['sidecar_namespace']}/stages/stage-{index - 1:02d}.json",
                    "sha256": f"{index:064x}",
                }
                test.assertEqual(kwargs["predecessor_receipt_ref"], expected)
                return {"path": path, "sha256": f"{index + 1:064x}"}

        class Process:
            _next_pid = 43210

            def __init__(self):
                self.pid = Process._next_pid
                Process._next_pid += 1

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

        admission = Admission()
        bridge = Bridge()
        admission.final_stage_factory = Stage
        processes: list[Process] = []
        waited: list[dict[str, object]] = []

        @contextlib.contextmanager
        def held_lock(path):
            lock = Path(path)
            lock.parent.mkdir(parents=True, exist_ok=True)
            with lock.open("a+") as stream:
                yield stream

        def fake_wait(child, validated_value, group_id, *, popen_monotonic):
            waited.append({"child": child, "group_id": group_id,
                           "popen_monotonic": popen_monotonic})
            return 0

        def fake_read(root_value, relative, label="file"):
            if relative.endswith("completed.json"):
                attempt_id = Path(relative).parent.name
                group_id = attempt_id.removesuffix("-attempt-02-series-02")
                return supervisor.canonical_json({
                    "status": "completed", "group_id": group_id,
                    "attempt_id": attempt_id, "source_commit": "a" * 40,
                    "plan_commit": "b" * 40, "contract_sha256": "c" * 64,
                    "execution_series": 2,
                })
            return b"{}\n"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_marker = os.environ.get(supervisor.FIXTURE_ENV)
            os.environ[supervisor.FIXTURE_ENV] = "1"
            try:
                with patch.object(supervisor, "_static",
                                  return_value=(Protocol(), manifest, core)), \
                     patch.object(supervisor, "_load_admission",
                                  return_value=admission), \
                     patch.object(supervisor, "_load_bridge",
                                  return_value=bridge), \
                     patch.object(supervisor, "_validate_context",
                                  side_effect=lambda *args, **kwargs: context), \
                     patch.object(supervisor, "_lock_target",
                                  return_value=root / "canonical.lock"), \
                     patch.object(supervisor, "_process",
                                  side_effect=lambda pid: {
                                      "pid": pid, "birth_identity": "birth"
                                  }), \
                     patch.object(supervisor, "raw_permit",
                                  return_value={"scope": "parent"}), \
                     patch.object(supervisor, "_write_raw_permit",
                                  return_value={"path": "permit", "sha256": "5" * 64}), \
                     patch.object(supervisor, "build_group_command",
                                  side_effect=lambda *args, **kwargs: {
                                      "argv": ["fixed-child", kwargs["parent_stage_ref"]["path"]],
                                      "environment": {"PATH": "/usr/bin"},
                                  }), \
                     patch.object(supervisor, "subprocess") as subprocess_mock, \
                     patch.object(supervisor, "_wait_group_child",
                                  side_effect=fake_wait), \
                     patch.object(supervisor, "_read",
                                  side_effect=fake_read), \
                     patch.object(supervisor, "_json",
                                  side_effect=lambda raw, label: json.loads(raw)), \
                     patch.object(supervisor, "_jsonl",
                                  return_value=(b"{}\n", [{}])), \
                     patch.object(supervisor, "_terminal_continuation_safety",
                                  return_value={"status": "checked"}), \
                     patch.object(supervisor, "_lock_fd", held_lock):
                    def popen(*args, **kwargs):
                        process = Process()
                        processes.append(process)
                        return process
                    subprocess_mock.Popen.side_effect = popen
                    result = supervisor.run_groups(
                        root, supervisor.MANIFEST_PATH, manifest_sha, context,
                        {"path": "parent-auth", "sha256": "6" * 64}, "6" * 64,
                        {
                            group: (
                                {"path": f"auth/{index:02d}", "sha256": "7" * 64},
                                "7" * 64,
                            )
                            for index, group in enumerate(groups)
                        },
                        fixture_only=True,
                        authorization_bundle_ref={"path": "bundle", "sha256": "8" * 64},
                        authorization_bundle_sha256="8" * 64,
                    )
            finally:
                if old_marker is None:
                    os.environ.pop(supervisor.FIXTURE_ENV, None)
                else:
                    os.environ[supervisor.FIXTURE_ENV] = old_marker

        self.assertEqual(result["status"], "batch-covered")
        self.assertEqual(subprocess_mock.Popen.call_count, 20)
        self.assertEqual(len(waited), 20)
        self.assertTrue(all(isinstance(item["popen_monotonic"], float)
                            for item in waited))
        self.assertEqual(admission.calls.count("parent"), 1)
        self.assertEqual(admission.calls.count("group"), 20)
        self.assertEqual(admission.calls.count("phase"), 20)
        self.assertEqual(admission.calls.count("completion"), 20)
        self.assertEqual(bridge.parent_stages, 21)
        self.assertEqual(bridge.runtime_loads, 21)
        self.assertEqual(bridge.prepare_graph_calls, 1)
        self.assertEqual(len(processes), 20)


class DirectFileEntrypoint21Tests(unittest.TestCase):
    """Execute complete successor source; never filter its bottom entrypoint."""

    def _execute(self, name, spec, argv):
        path = BASE / "bifrost-v0140-supervisor-21.py"
        host = types.ModuleType(name)
        host.__file__ = str(path)
        host.__spec__ = spec
        host.__package__ = None
        with patch.dict(sys.modules, {name: host}), patch.object(sys, "argv", argv):
            exec(compile(path.read_bytes(), str(path), "exec"), host.__dict__)
        return host

    def test_named_import_initializes_without_entering_cli(self):
        host = self._execute("bf21_named_guard_test", None, ["supervisor21", "--bad-option"])
        self.assertTrue(callable(host.main))
        self.assertIs(host.main.__globals__, host.__dict__)

    def test_duplicate_main_shell_with_owned_spec_initializes_without_cli(self):
        spec = importlib.util.spec_from_file_location(
            "bf21_owned_shell_guard_test", BASE / "bifrost-v0140-supervisor-21.py")
        original = sys.modules["__main__"]
        host = self._execute("__main__", spec, ["supervisor21", "--bad-option"])
        self.assertIs(sys.modules["__main__"], original)
        self.assertEqual(host.__name__, "__main__")
        self.assertIs(host.__spec__, spec)
        self.assertIs(host.run_groups.__globals__, host.__dict__)
        self.assertIsNot(host, original)

    def test_direct_file_main_with_no_spec_still_rejects_unbound_launch(self):
        original = sys.modules["__main__"]
        with self.assertRaisesRegex(ValueError, "no unbound CLI launch mode"):
            self._execute("__main__", None, ["supervisor21"])
        self.assertIs(sys.modules["__main__"], original)

    def test_real_direct_file_help_exits_without_runtime_or_analysis(self):
        interpreter = str(Path(sys.executable).resolve())
        result = subprocess.run(
            [interpreter, "-E", str(BASE / "bifrost-v0140-supervisor-21.py"), "--help"],
            capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--batch", result.stdout)
        self.assertIn("--child", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_direct_batch_and_child_seal_actual_graph_and_restore_process_state(self):
        root = BASE.parents[3]
        identity = json.loads((root / "reports/releases/v0.9.2/qualification/"
                               "bifrost-v0140-replacement-14/manifest-identity.json").read_bytes())
        bridge = bridge_tests.b
        refs = {}
        for old_role, old_ref in identity["runtime_module_graph"].items():
            role = bridge._map_graph_role(old_role, bridge._ROLE_RENAMES)
            ref = dict(old_ref)
            if role in bridge._SUCCESSOR_GRAPH_PATHS:
                ref["path"] = bridge._SUCCESSOR_GRAPH_PATHS[role]
                ref["sha256"] = hashlib.sha256((root / ref["path"]).read_bytes()).hexdigest()
            refs[role] = ref
        order = tuple(bridge.REQUIRED_GRAPH_NAMES)
        refs = {role: refs[role] for role in order + tuple(sorted(set(refs) - set(order)))}
        self.assertEqual(len(refs), 88)
        protocol = load("bf21_cli_probe_protocol", BASE / "bifrost-v0140-replacement-21.py")
        admission = load("bf21_cli_probe_admission", BASE / "bifrost-v0140-admission-21.py")
        path = BASE / "bifrost-v0140-supervisor-21.py"
        source = compile(path.read_bytes(), str(path), "exec")

        class AfterGraphSeal(RuntimeError):
            pass

        try:
            for child in (False, True):
                with self.subTest(child=child), tempfile.TemporaryFile() as lock:
                    host = types.ModuleType("__main__")
                    host.__file__, host.__spec__, host.__package__ = str(path), None, ""
                    events, holder = [], {}
                    core = {"replacement_groups": [], "runtime_module_graph": refs,
                            "lock_path": "unused-cli-regression.lock"}
                    manifest = {"replacement_groups": [], "execution_admission_slots": {},
                                "core_identity": {"id": "cli-regression"}}
                    argv = [str(path), "--root", str(root), "--manifest", "unused-manifest.json",
                            "--manifest-sha256", "a" * 64]
                    if child:
                        argv += ["--child", "--group", "unused-group", "--attempt-id", "unused-attempt",
                                 "--bridge-context", "unused-context.json", "--context-sha256", "c" * 64,
                                 "--lock-fd", str(lock.fileno()), "--parent-stage", "unused-stage.json",
                                 "--parent-stage-sha256", "d" * 64, "--popen-monotonic", "100.0"]
                    else:
                        argv += ["--batch", "--output", "unused-output.json", "--authorization-bundle",
                                 "unused-auth.json", "--authorization-bundle-sha256", "b" * 64]

                    def trace(frame, event, arg):
                        if frame.f_code.co_filename != str(path):
                            return trace
                        if event == "call":
                            events.append(frame.f_code.co_name)
                            if frame.f_code.co_name == "main" and frame.f_globals is host.__dict__:
                                host.__dict__.update(
                                    _static=lambda *a, **k: (protocol, manifest, core),
                                    _file_ref=lambda *a, **k: {"path": "unused-auth.json", "sha256": "b" * 64},
                                    _load_admission=lambda *a, **k: admission,
                                    _load_bridge=lambda *a, **k: bridge)
                        graph = frame.f_locals.get("graph")
                        if (event == "line" and frame.f_code.co_name in {"run_groups", "_run_frozen_group"}
                                and hasattr(graph, "_by_name") and len(graph._by_name) == 88):
                            holder["graph"] = graph
                            raise AfterGraphSeal("deliberate stop before lock, stage or analyzer")
                        return trace

                    old_main, old_argv, old_trace = sys.modules["__main__"], sys.argv, sys.gettrace()
                    old_env = dict(os.environ)
                    aliases = {k: v for k, v in sys.modules.items() if k.startswith("v092_bifrost16_graph_")}
                    with patch.dict(sys.modules, {"__main__": host}), patch.object(sys, "argv", argv), \
                            patch.dict(os.environ, {"DATAFLOWBENCH_V092_REPLACEMENT21_EXPERIMENT": "1"}):
                        try:
                            sys.settrace(trace)
                            with self.assertRaises(AfterGraphSeal):
                                exec(source, host.__dict__)
                        finally:
                            sys.settrace(old_trace)
                    graph = holder["graph"]
                    self.assertTrue(graph.import_context._sealed_once)
                    self.assertIs(graph.module("supervisor21"), host)
                    duplicate = graph.module("host_supervisor21")
                    self.assertIsNot(duplicate.__dict__, host.__dict__)
                    self.assertIsNotNone(duplicate.__spec__)
                    for name in (("main", "_child_main", "_run_frozen_group") if child else ("main", "run_groups")):
                        self.assertEqual(events.count(name), 1)
                    self.assertIs(sys.modules["__main__"], old_main)
                    self.assertIs(sys.argv, old_argv)
                    self.assertIs(sys.gettrace(), old_trace)
                    self.assertEqual(dict(os.environ), old_env)
                    self.assertEqual({k: v for k, v in sys.modules.items()
                                      if k.startswith("v092_bifrost16_graph_")}, aliases)
        finally:
            sys.modules.pop("bf21_cli_probe_protocol", None)
            sys.modules.pop("bf21_cli_probe_admission", None)



if __name__ == "__main__":
    unittest.main()
