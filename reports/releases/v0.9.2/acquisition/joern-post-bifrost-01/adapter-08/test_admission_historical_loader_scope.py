"""Focused regression for the inherited Joern historical configuration route."""
from __future__ import annotations

import contextlib
import hashlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import admission
import packet


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class HistoricalConfigurationScopeTests(unittest.TestCase):
    def test_scope_binds_inherited88_and_only_the_sealed109_ledger_prefix(self):
        root = Path(admission.PACKET_ROOT).resolve()
        ledger_path = packet.LIVE_LEDGER_PATH
        raw = b"{}\n" * 130
        prefix109 = b"".join(raw.splitlines(keepends=True)[:109])
        prefix130 = raw
        events: list[object] = []
        modules: dict[str, object] = {}
        refs: dict[str, dict[str, str]] = {}

        class Member:
            def __init__(self, name: str, path: str, digest: str, module: object):
                self.name = name
                self.canonical_path = path
                self.source_sha256 = digest
                self.module_object = module

        class InheritedGraph:
            def __init__(self):
                self.members: list[Member] = []

            def module(self, name: str):
                return modules[name]

            def assert_member(self, name: str, value: object):
                member = next(item for item in self.members if item.name == name)
                if member.module_object is not value:
                    raise AssertionError("foreign module object")

        inherited = InheritedGraph()

        class Stage:
            @staticmethod
            def _read(candidate_root: Path, path: str) -> bytes:
                if candidate_root != root or path != ledger_path:
                    raise AssertionError("ledger read escaped its binding")
                return raw

            @staticmethod
            def _canonical_rows(candidate_raw: bytes, label: str):
                events.append(("canonical-rows", candidate_raw, label))
                return candidate_raw.splitlines()

            @staticmethod
            def _stage_modules(candidate_graph, *, require_legacy):
                if candidate_graph is not inherited or require_legacy is not True:
                    raise AssertionError("wrong graph/module mode")
                events.append("stage-modules")
                return module_bundle

            @staticmethod
            @contextlib.contextmanager
            def _stage_full_graph_scope(candidate_root, core, candidate_graph,
                                        candidate_modules, *, mode, ledger_bytes,
                                        stdlib_importlib):
                if (candidate_root != root or candidate_graph is not inherited or
                        candidate_modules is not module_bundle or mode != "after" or
                        ledger_bytes != prefix109 or stdlib_importlib is not host_importlib):
                    raise AssertionError("historical loader scope binding changed")
                # This is the exact selector routed by the frozen stage loader.
                target = candidate_graph.module("local_010_run_joern_swift_case")
                if target is not historical_config:
                    raise AssertionError("historical configuration was not graph-owned")
                events.append("historical-loader-enter")
                try:
                    yield
                finally:
                    events.append("historical-loader-exit")

        module_bundle = object()
        host_importlib = object()
        historical_config = object()
        stage_module = Stage()
        bridge_module = SimpleNamespace(HOST_STDLIB_IMPORTLIB=host_importlib)
        for index in range(88):
            role = ("stage_runtime11" if index == 0 else
                    "bridge19" if index == 1 else
                    "local_010_run_joern_swift_case" if index == 2 else
                    f"inherited_role_{index:02}")
            module = (stage_module if role == "stage_runtime11" else
                      bridge_module if role == "bridge19" else
                      historical_config if role == "local_010_run_joern_swift_case" else
                      object())
            digest = sha(role.encode())
            refs[role] = {"path": f"runtime/{index:02}.py", "sha256": digest}
            modules[role] = module
            inherited.members.append(Member(role, refs[role]["path"], digest, module))

        bridge = SimpleNamespace(inherited_view=lambda candidate: inherited)
        current_graph = SimpleNamespace(module=lambda name: {
            "joern05_bridge": bridge,
        }[name])
        historical_core = {"runtime_module_graph": refs, "ledger_path": ledger_path}
        provider = SimpleNamespace(
            LEDGER_ROWS=130,
            LEDGER_RAW_SHA256=sha(prefix130),
            SEALED109_RAW_SHA256=sha(prefix109),
        )

        def stable_read(_root, ref):
            if ref not in refs.values():
                raise AssertionError("unexpected inherited source ref")
            return b"pinned source bytes"

        with mock.patch.object(admission, "PACKET_ROOT", root), \
                mock.patch.object(packet, "inherited_core", return_value=historical_core), \
                mock.patch.object(packet, "load_history_provider", return_value=provider), \
                mock.patch.object(packet, "read_ref", stable_read), \
                mock.patch.object(packet, "read_live_ledger", return_value=raw):
            with admission._historical_joern_configuration_scope(root, current_graph):
                events.append("validate-current-plan")

        self.assertEqual(events[-3:], ["historical-loader-enter",
                                      "validate-current-plan",
                                      "historical-loader-exit"])
        self.assertEqual(sum(item == "stage-modules" for item in events), 1)
        self.assertEqual(sum(isinstance(item, tuple) and item[0] == "canonical-rows"
                             for item in events), 1)

    def test_execution_and_stage_qualification_wrap_plan_validation(self):
        root = Path("/synthetic/joern05").resolve()
        refs = {
            "current_core": {"path": "core.json", "sha256": "a" * 64},
            "current_manifest": {"path": "manifest.json", "sha256": "b" * 64},
            "current_contract": {"path": "contract.json", "sha256": "c" * 64},
            "current_source_evidence": {"path": "source.json", "sha256": "d" * 64},
            "eligible_joern_plan": {"path": "eligible.json", "sha256": "e" * 64},
            "external_launch_review": {"path": "launch-review.json", "sha256": "1" * 64},
        }
        plan = {"status": "execution-eligible", "execution_eligible": True,
                "full_model_qualification": False, "scored_activation": False}
        current = {"contract": refs["current_contract"],
                   "source_evidence": refs["current_source_evidence"],
                   "source_commit": "2" * 40, "plan_commit": "3" * 40}
        review = {"status": "approved", "automatic_retry": False,
                  "bindings": {
                      "manifest_sha256": refs["current_manifest"]["sha256"],
                      "core_identity_sha256": refs["current_core"]["sha256"],
                      "contract_sha256": refs["current_contract"]["sha256"],
                      "source_commit": current["source_commit"],
                      "plan_commit": current["plan_commit"],
                  }}
        documents = {
            tuple(refs["current_core"].items()): current,
            tuple(refs["current_manifest"].items()): {
                "core_identity": refs["current_core"]},
            tuple(refs["eligible_joern_plan"].items()): plan,
            tuple(refs["external_launch_review"].items()): review,
        }
        for purpose in ("execution", "stage-qualification"):
            events: list[str] = []

            @contextlib.contextmanager
            def historical_scope(_root, _graph):
                events.append("loader-enter")
                try:
                    yield
                finally:
                    events.append("loader-exit")

            @contextlib.contextmanager
            def eligible_scope(*_args, **_kwargs):
                events.append("eligible-enter")
                try:
                    yield
                finally:
                    events.append("eligible-exit")

            runner = SimpleNamespace(
                validate_plan=lambda *_args: (
                    events.append("validate-plan") or
                    (plan, {"accepted": True}, object())),
                _require_launch_guard=lambda _group: events.append("launch-guard"))
            graph = object()
            with self.subTest(purpose=purpose), \
                    mock.patch.object(admission, "PACKET_ROOT", root), \
                    mock.patch.object(admission, "missing_prerequisites", return_value=[]), \
                    mock.patch.object(admission, "require_markers", lambda _env: None), \
                    mock.patch.object(packet, "document",
                                      side_effect=lambda _root, ref: documents[tuple(ref.items())]), \
                    mock.patch.object(admission, "_historical_joern_configuration_scope",
                                      historical_scope), \
                    mock.patch.object(admission, "_eligible_plan_validation_scope",
                                      eligible_scope), \
                    mock.patch.object(admission, "validate_native_execution_decision",
                                      return_value={}):
                value = admission.validate_prerequisites(
                    root, refs, runner, "eligible.json", graph=graph,
                    runner_role=admission.ELIGIBLE_RUNNER_ROLE,
                    runner_ref={"path": "runner.py", "sha256": "f" * 64},
                    diagnostic_ref={"path": "diagnostic.py", "sha256": "0" * 64},
                    purpose=purpose)
            self.assertEqual(value[0], plan)
            self.assertLess(events.index("loader-enter"),
                            events.index("validate-plan"))
            self.assertLess(events.index("validate-plan"),
                            events.index("loader-exit"))


if __name__ == "__main__":
    unittest.main()
