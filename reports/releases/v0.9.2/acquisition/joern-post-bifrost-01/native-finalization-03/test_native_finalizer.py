"""Synthetic gate tests for the append-only post-capture finalizer."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
from unittest import mock

import native_finalizer as nf


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def put_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(raw)
    return digest(raw)


class NativeExitTests(unittest.TestCase):
    def setUp(self):
        self.request_ref = {"path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json",
                            "sha256": "a" * 64}
        self.result = {
            "status": "process-returned", "exit_code": 0, "failure": None,
            "qualification_inferred": False, "automatic_retry": False,
            "cleanup": {"coordinator_reaped": True},
            "phases": [{"phase": x} for x in ("ready", "controls-started", "controls-returned")],
            **nf.SEMANTIC_SCOPE,
        }
        self.exit_record = {
            "schema": "v092-native-control-parent-exit/v1",
            "request": self.request_ref, "result": self.result,
            "ledger_unchanged": True, "qualification_inferred": False,
            "automatic_retry": False,
        }

    def test_accepts_only_successful_wrapper_return(self):
        self.assertIs(nf.validate_native_exit(self.exit_record,
                                              request_ref=self.request_ref,
                                              ledger_unchanged=True), self.result)

    def test_rejects_failed_status_even_with_zero_exit(self):
        bad = {**self.exit_record, "result": {**self.result, "status": "failed"}}
        with self.assertRaisesRegex(nf.FinalizationError, "did not return successfully"):
            nf.validate_native_exit(bad, request_ref=self.request_ref, ledger_unchanged=True)

    def test_rejects_nonzero_exit(self):
        bad = {**self.exit_record, "result": {**self.result, "exit_code": 1}}
        with self.assertRaises(nf.FinalizationError):
            nf.validate_native_exit(bad, request_ref=self.request_ref, ledger_unchanged=True)

    def test_rejects_missing_controls_returned_phase(self):
        bad_result = {**self.result, "phases": self.result["phases"][:2]}
        bad = {**self.exit_record, "result": bad_result}
        with self.assertRaisesRegex(nf.FinalizationError, "controls-returned"):
            nf.validate_native_exit(bad, request_ref=self.request_ref, ledger_unchanged=True)

    def test_rejects_changed_scope_and_ledger(self):
        bad = {**self.exit_record, "result": {**self.result, "uncontended_timing_certified": True}}
        with self.assertRaisesRegex(nf.FinalizationError, "semantic-only scope"):
            nf.validate_native_exit(bad, request_ref=self.request_ref, ledger_unchanged=True)
        with self.assertRaises(nf.FinalizationError):
            nf.validate_native_exit(self.exit_record, request_ref=self.request_ref,
                                    ledger_unchanged=False)


class RequestAndReviewTests(unittest.TestCase):
    def setUp(self):
        self.namespace = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08"
        self.request_ref = {"path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json",
                            "sha256": "a" * 64}
        self.refs = {
            name: {"path": f"reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08/{name}.json",
                   "sha256": (chr(ord("b") + i) * 64)}
            for i, name in enumerate(("native-exit", "control-result", "parent-started",
                                      "startup-manifest", "request", "invocation-review"))
        }
        self.refs["request"] = self.request_ref
        self.refs["invocation_review"] = {"path": "reports/releases/v0.9.2/validation/joern-current130-01/native08-exact-invocation-review-01.json",
                                           "sha256": "c" * 64}
        self.refs["native_parent_started"] = self.refs.pop("parent-started")
        self.refs["native_exit"] = self.refs.pop("native-exit")
        self.refs["control_result"] = self.refs.pop("control-result")
        self.refs["startup_sidecar_manifest"] = self.refs.pop("startup-manifest")
        self.refs["worker_invocation"] = {
            "path": self.namespace + "/worker-invocation.json", "sha256": "8" * 64}
        self.refs["startup_sidecar_manifest_sha256"] = self.refs["startup_sidecar_manifest"]["sha256"]
        self.refs.pop("invocation-review", None)
        self.ledger = {"path": nf.LEDGER_PATH, "sha256": nf.LEDGER_SHA256}
        self.bindings = {
            **self.refs,
            "source_head": "1" * 40,
            "source_closure_sha256": "d" * 64,
            "ledger": self.ledger,
            "namespace": self.namespace,
            "capture_root": self.namespace + "/capture",
            "pending_plan": {"path": "reports/releases/v0.9.2/qualification/plan.json", "sha256": "e" * 64},
            "control_plan": {"path": "reports/releases/v0.9.2/qualification/control.json", "sha256": "f" * 64},
            "execution_plan_projection_sha256": "0" * 64,
        }
        self.review = {
            "schema": nf.CAPTURE_REVIEW_SCHEMA,
            "status": "approved-for-post-capture-diagnostic-replay-only",
            "bindings": self.bindings,
            "scope": dict(nf.SEMANTIC_SCOPE),
            "full_model_qualification": False,
            "scored_activation": False,
            "publication_approved": False,
            "publication_hold": True,
        }

    def _validate(self, review=None):
        nf.validate_capture_review(review or self.review,
            request_ref=self.request_ref,
            invocation_review_ref=self.refs["invocation_review"],
            parent_started_ref=self.refs["native_parent_started"],
            worker_invocation_ref=self.refs["worker_invocation"],
            native_exit_ref=self.refs["native_exit"],
            control_result_ref=self.refs["control_result"],
            startup_manifest_ref=self.refs["startup_sidecar_manifest"],
            source_head="1" * 40, source_closure_sha256="d" * 64,
            ledger_ref=self.ledger, namespace=self.namespace,
            capture_root=self.namespace + "/capture",
            pending_plan_ref=self.bindings["pending_plan"],
            control_plan_ref=self.bindings["control_plan"],
            projection_sha256="0" * 64)

    def test_accepts_exact_replay_only_capture_review(self):
        self._validate()

    def test_rejects_nonapproved_status_or_extra_authority(self):
        for changes in (
            {"status": "approved-for-qualification"},
            {"publication_approved": True},
            {"publication_hold": False},
            {"full_model_qualification": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(nf.FinalizationError):
                self._validate({**self.review, **changes})

    def test_rejects_missing_startup_manifest_hash_binding(self):
        bindings = dict(self.bindings)
        del bindings["startup_sidecar_manifest_sha256"]
        with self.assertRaisesRegex(nf.FinalizationError, "does not bind every exact"):
            self._validate({**self.review, "bindings": bindings})

    def test_rejects_wrong_parent_started_receipt(self):
        bindings = dict(self.bindings)
        bindings["native_parent_started"] = {**self.refs["native_parent_started"], "sha256": "9" * 64}
        with self.assertRaises(nf.FinalizationError):
            self._validate({**self.review, "bindings": bindings})

    def test_accepts_manifest_reference_in_canonical_validation_record_path(self):
        nf.validate_startup_manifest_ref_path(
            "reports/releases/v0.9.2/validation/joern-current130-01/"
            "native08-startup-sidecar-manifest-01.json",
            self.namespace)
        for path in (
            self.namespace + "/capture/startup-sidecar-manifest.json",
            "reports/releases/v0.9.2/validation/joern-current130-01/"
            "native09-startup-sidecar-manifest-01.json",
            "reports/releases/v0.9.2/validation/other/"
            "native08-startup-sidecar-manifest-01.json",
            "reports/releases/v0.9.2/validation/joern-current130-01/"
            "native08-startup-sidecar-manifest-1.json",
        ):
            with self.subTest(path=path), self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest_ref_path(path, self.namespace)

    def test_rejects_scope_relaxation(self):
        with self.assertRaisesRegex(nf.FinalizationError, "semantic-only/performance"):
            self._validate({**self.review, "scope": {**nf.SEMANTIC_SCOPE,
                                                      "relative_performance_conclusions_authorized": True}})

    def test_namespace_and_request_sequence_must_be_fresh(self):
        request = {"namespace": self.namespace}
        self.assertEqual(nf.expected_namespace(request, self.request_ref), self.namespace)
        old_request = {"path": self.request_ref["path"].replace("request-08", "request-07"),
                       "sha256": "a" * 64}
        with self.assertRaises(nf.FinalizationError):
            nf.expected_namespace({"namespace": self.namespace.replace("controls-08", "controls-07")}, old_request)


class StartupManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.namespace = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-08"
        self.capture = self.namespace + "/capture"
        self.sidecar_rel = self.namespace + "/capture.startup-observation"
        self.policy = {"schema": "synthetic-policy-for-unit-test", "predef_expectation": "absent"}
        self.home = self.root / self.capture / "jvm-home"
        self.home.mkdir(parents=True)
        self.event_dir_rel = self.sidecar_rel + "/events/001-frontend"
        event_dir = self.root / self.event_dir_rel
        event_dir.mkdir(parents=True)
        witness_path = event_dir / "jvm-123.json"
        home_text = str(self.home.resolve())
        predef_text = str((self.home / ".scala-repl-pp.sc").resolve())
        witness = {
            "schema": "v092-joern-jvm-startup-witness/v5",
            "predef_present": False, "predef_symlink": False,
            "user_home_b64": base64.b64encode(home_text.encode()).decode(),
            "predef_path_b64": base64.b64encode(predef_text.encode()).decode(),
        }
        self.witness_sha = put_json(witness_path, witness)
        event = {
            "schema": "v092-joern-native-startup-receipt/v7",
            "phase": "frontend", "error": None, "violations": [],
            "property_witness": {"status": "exact-in-process-System.getProperty"},
            "predef_before": {"present": False, "symlink": False},
            "predef_after": {"present": False, "symlink": False},
            "event_witness_directory": str(event_dir.resolve()),
            "jvm_witnesses": [{"path": str(witness_path.resolve()),
                               "sha256": self.witness_sha,
                               "user_home": home_text}],
        }
        event_rel = self.sidecar_rel + "/001-frontend.json"
        event_sha = put_json(self.root / event_rel, event)
        summary = {
            "schema": "v092-joern-native-startup-observation-summary/v7",
            "observer": "v092-joern-native-startup-observer/v7",
            "policy": self.policy,
            "event_count": 1, "phases": ["frontend"],
            "status": "startup-agent-observed", "qualification_safe": True,
            "property_witness": {"status": "exact-in-process-System.getProperty"},
            "failures": [],
            "sidecar_root": str((self.root / self.sidecar_rel).resolve()),
            "topology": {"test-only": True},
        }
        self.summary_rel = self.sidecar_rel + "/summary.json"
        self.summary_sha = put_json(self.root / self.summary_rel, summary)
        self.startup_summary = {**summary, "summary": {
            "path": str((self.root / self.summary_rel).resolve()),
            "sha256": self.summary_sha,
        }}
        self.manifest = {
            "schema": nf.SIDECAR_MANIFEST_SCHEMA,
            "capture_root": self.capture,
            "summary": {"path": self.summary_rel, "sha256": self.summary_sha},
            "events": [{"path": event_rel, "sha256": event_sha}],
            "witnesses": [{"path": self.event_dir_rel + "/jvm-123.json",
                           "sha256": self.witness_sha}],
            "home": {"path": self.capture + "/jvm-home", "directory": True,
                     "symlink": False},
            "predef": {"path": self.capture + "/jvm-home/.scala-repl-pp.sc",
                       "present": False, "symlink": False, "bytes": 0,
                       "sha256": None},
        }

    def test_accepts_explicit_bounded_sidecars_and_exact_home(self):
        result = nf.validate_startup_manifest(self.root, self.manifest,
            namespace=self.namespace, capture_root=self.capture,
            startup_summary=self.startup_summary, expected_policy=self.policy)
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(len(result["witnesses"]), 1)

    def test_late_oversized_witness_is_rejected_before_its_json_read(self):
        summary_size = (self.root / self.summary_rel).stat().st_size
        event_size = (self.root / self.manifest["events"][0]["path"]).stat().st_size
        witness_path = self.root / self.manifest["witnesses"][0]["path"]
        witness_size = witness_path.stat().st_size
        self.assertGreater(witness_size, 1)
        read_paths = []
        original = nf._read_json

        def tracked(path, maximum, description, expected_sha256=None):
            read_paths.append(path)
            return original(path, maximum, description, expected_sha256)

        limit = summary_size + event_size + witness_size - 1
        with mock.patch.object(nf, "MAX_STARTUP_BYTES", limit), \
                mock.patch.object(nf, "_read_json", side_effect=tracked):
            with self.assertRaisesRegex(nf.FinalizationError, "size exceeds its bound"):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
        self.assertEqual(read_paths, [self.root / self.summary_rel,
                                      self.root / self.manifest["events"][0]["path"]])
        self.assertNotIn(witness_path, read_paths)

    def test_reader_is_not_called_after_aggregate_budget_is_exhausted(self):
        summary_size = (self.root / self.summary_rel).stat().st_size
        event_size = (self.root / self.manifest["events"][0]["path"]).stat().st_size
        witness_path = self.root / self.manifest["witnesses"][0]["path"]
        read_paths = []
        original = nf._read_json

        def tracked(path, maximum, description, expected_sha256=None):
            read_paths.append(path)
            return original(path, maximum, description, expected_sha256)

        with mock.patch.object(nf, "MAX_STARTUP_BYTES", summary_size + event_size), \
                mock.patch.object(nf, "_read_json", side_effect=tracked):
            with self.assertRaisesRegex(nf.FinalizationError, "aggregate byte bound exhausted"):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
        self.assertEqual(read_paths, [self.root / self.summary_rel,
                                      self.root / self.manifest["events"][0]["path"]])
        self.assertNotIn(witness_path, read_paths)

    def test_accepts_typecheck_sidecar_without_a_jvm_witness(self):
        old_event = self.root / self.manifest["events"][0]["path"]
        old_dir = self.root / self.event_dir_rel
        (old_dir / "jvm-123.json").unlink()
        old_dir.rmdir()
        old_event.unlink()
        event_dir_rel = self.sidecar_rel + "/events/001-typecheck"
        event_dir = self.root / event_dir_rel
        event_dir.mkdir()
        event = {
            "schema": "v092-joern-native-startup-receipt/v7",
            "phase": "typecheck", "error": None, "violations": [],
            "property_witness": {"status": "unavailable"},
            "predef_before": {"present": False, "symlink": False},
            "predef_after": {"present": False, "symlink": False},
            "event_witness_directory": str(event_dir.resolve()),
            "jvm_witnesses": [],
        }
        event_rel = self.sidecar_rel + "/001-typecheck.json"
        event_sha = put_json(self.root / event_rel, event)
        summary = {k: v for k, v in self.startup_summary.items() if k != "summary"}
        summary["phases"] = ["typecheck"]
        summary_sha = put_json(self.root / self.summary_rel, summary)
        self.startup_summary = {**summary, "summary": {
            "path": str((self.root / self.summary_rel).resolve()),
            "sha256": summary_sha,
        }}
        self.manifest["summary"]["sha256"] = summary_sha
        self.manifest["events"] = [{"path": event_rel, "sha256": event_sha}]
        self.manifest["witnesses"] = []
        result = nf.validate_startup_manifest(self.root, self.manifest,
            namespace=self.namespace, capture_root=self.capture,
            startup_summary=self.startup_summary, expected_policy=self.policy)
        self.assertEqual(result["witnesses"], [])

    def test_rejects_extra_or_missing_manifest_entries(self):
        for manifest in (
            {**self.manifest, "unexpected": []},
            {**self.manifest, "events": []},
            {**self.manifest, "witnesses": []},
        ):
            with self.subTest(manifest=manifest), self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)

    def test_rejects_summary_or_policy_near_miss(self):
        for changes in (
            {"qualification_safe": False},
            {"status": "failed"},
            {"policy": {"predef_expectation": "present"}},
        ):
            with self.subTest(changes=changes), self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary={**self.startup_summary, **changes},
                    expected_policy=self.policy)

    def test_rejects_unlisted_file_hash_change(self):
        event_path = self.root / self.manifest["events"][0]["path"]
        event_path.write_bytes(event_path.read_bytes() + b" ")
        with self.assertRaisesRegex(nf.FinalizationError, "SHA-256 mismatch|complete deterministic"):
            nf.validate_startup_manifest(self.root, self.manifest,
                namespace=self.namespace, capture_root=self.capture,
                startup_summary=self.startup_summary, expected_policy=self.policy)

    def test_rejects_unmanifested_sidecar_root_file(self):
        (self.root / self.sidecar_rel / "unexpected.json").write_text("{}")
        with self.assertRaisesRegex(nf.FinalizationError, "unmanifested entries"):
            nf.validate_startup_manifest(self.root, self.manifest,
                namespace=self.namespace, capture_root=self.capture,
                startup_summary=self.startup_summary, expected_policy=self.policy)

    def test_rejects_unmanifested_event_directory_before_reading_sidecars(self):
        events_root = self.root / self.sidecar_rel / "events"
        (events_root / "002-query").mkdir()
        read_paths = []
        original = nf._read_json

        def tracked(path, maximum, description, expected_sha256=None):
            read_paths.append(path)
            return original(path, maximum, description, expected_sha256)

        with mock.patch.object(nf, "_read_json", side_effect=tracked):
            with self.assertRaisesRegex(nf.FinalizationError,
                                        "startup event root contains missing or unmanifested"):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
        self.assertEqual(read_paths, [])

    def test_event_root_directory_listing_stops_at_its_entry_cap(self):
        events_root = self.root / self.sidecar_rel / "events"
        (events_root / "002-query").mkdir()
        with self.assertRaisesRegex(nf.FinalizationError, "bounded entry count"):
            nf._directory_names(events_root, "synthetic event root", maximum_entries=1)

    def test_rejects_predef_appearance_or_home_symlink(self):
        predef = self.home / ".scala-repl-pp.sc"
        predef.write_text("synthetic-test-only")
        with self.assertRaises(nf.FinalizationError):
            nf.validate_startup_manifest(self.root, self.manifest,
                namespace=self.namespace, capture_root=self.capture,
                startup_summary=self.startup_summary, expected_policy=self.policy)

    def test_rejects_witness_outside_manifested_event_directory(self):
        bad = json.loads(json.dumps(self.manifest))
        bad["witnesses"][0]["path"] = self.summary_rel
        with self.assertRaises(nf.FinalizationError):
            nf.validate_startup_manifest(self.root, bad,
                namespace=self.namespace, capture_root=self.capture,
                startup_summary=self.startup_summary, expected_policy=self.policy)

    def test_rejects_symlinked_namespace_ancestor_before_reading_sidecars(self):
        namespace_path = self.root / self.namespace
        moved = namespace_path.with_name("native-controls-08-real")
        namespace_path.rename(moved)
        namespace_path.symlink_to(moved, target_is_directory=True)
        with mock.patch.object(nf, "_read_json", side_effect=AssertionError("read before path validation")) as read_json:
            with self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
            read_json.assert_not_called()

    def test_rejects_symlinked_capture_root_before_reading_sidecars(self):
        capture_path = self.root / self.capture
        moved = capture_path.with_name("capture-real")
        capture_path.rename(moved)
        capture_path.symlink_to(moved, target_is_directory=True)
        with mock.patch.object(nf, "_read_json", side_effect=AssertionError("read before path validation")) as read_json:
            with self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
            read_json.assert_not_called()

    def test_rejects_symlinked_startup_sidecar_ancestor_before_reading(self):
        sidecar_path = self.root / self.sidecar_rel
        moved = sidecar_path.with_name("capture.startup-observation-real")
        sidecar_path.rename(moved)
        sidecar_path.symlink_to(moved, target_is_directory=True)
        with mock.patch.object(nf, "_read_json", side_effect=AssertionError("read before path validation")) as read_json:
            with self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
            read_json.assert_not_called()

    def test_rejects_symlinked_event_file_before_reading_any_json(self):
        event_path = self.root / self.manifest["events"][0]["path"]
        target = self.root / "external-event.json"
        target.write_text("{}")
        event_path.unlink()
        event_path.symlink_to(target)
        with mock.patch.object(nf, "_read_json", side_effect=AssertionError("read before path validation")) as read_json:
            with self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
            read_json.assert_not_called()

    def test_rejects_symlinked_raw_witness_before_reading_any_json(self):
        witness_path = self.root / self.manifest["witnesses"][0]["path"]
        target = self.root / "external-witness.json"
        target.write_text("{}")
        witness_path.unlink()
        witness_path.symlink_to(target)
        with mock.patch.object(nf, "_read_json", side_effect=AssertionError("read before path validation")) as read_json:
            with self.assertRaises(nf.FinalizationError):
                nf.validate_startup_manifest(self.root, self.manifest,
                    namespace=self.namespace, capture_root=self.capture,
                    startup_summary=self.startup_summary, expected_policy=self.policy)
            read_json.assert_not_called()


class StableBindingAndModuleTests(unittest.TestCase):
    def _synthetic_script_refs(self, root):
        scripts = root / "scripts"
        scripts.mkdir()
        refs = []
        for name, relative in nf.SCRIPT_IMPORT_ALIASES:
            path = root / relative
            raw = ("VALUE = " + repr(name) + "\n").encode()
            path.write_bytes(raw)
            refs.append({"path": relative, "sha256": digest(raw)})
        return scripts, refs

    def test_script_alias_loader_owns_exact_projection_and_canonical_runner_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            scripts, refs = self._synthetic_script_refs(root)
            names = [name for name, _ in nf.SCRIPT_IMPORT_ALIASES]
            prior = {name: sys.modules.pop(name) for name in names if name in sys.modules}
            original_path = list(sys.path)
            try:
                with nf._owned_scripts_path(scripts):
                    with ExitStack() as owned:
                        modules = nf._load_script_import_aliases(
                            owned, root, refs, scripts)
                        self.assertEqual(set(modules), set(names))
                        for name, module in modules.items():
                            self.assertIs(sys.modules[name], module)
                            self.assertEqual(module.VALUE, name)
                self.assertTrue(set(names).isdisjoint(sys.modules))
                self.assertEqual(sys.path, original_path)
            finally:
                for name in names:
                    sys.modules.pop(name, None)
                sys.modules.update(prior)

    def test_script_alias_loader_rejects_preloaded_projection_and_cleans_earlier_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            scripts, refs = self._synthetic_script_refs(root)
            names = [name for name, _ in nf.SCRIPT_IMPORT_ALIASES]
            prior = {name: sys.modules.pop(name) for name in names if name in sys.modules}
            projection = object()
            original_path = list(sys.path)
            try:
                with nf._owned_scripts_path(scripts):
                    with mock.patch.dict(sys.modules, {"v092_qualification": projection}):
                        with self.assertRaisesRegex(nf.FinalizationError,
                                                    "preloaded module identity: v092_qualification"):
                            with ExitStack() as owned:
                                nf._load_script_import_aliases(owned, root, refs, scripts)
                        self.assertIs(sys.modules["v092_qualification"], projection)
                for name in names:
                    if name != "v092_qualification":
                        self.assertNotIn(name, sys.modules)
                self.assertEqual(sys.path, original_path)
            finally:
                for name in names:
                    sys.modules.pop(name, None)
                sys.modules.update(prior)

    def test_checked_ref_parses_the_exact_buffer_whose_digest_was_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            path = root / "bound.json"
            original = b'{"value":"bound"}\n'
            replacement = b'{"value":"replacement"}\n'
            path.write_bytes(original)
            real_read = nf._read_stable

            def replace_after_read(target, maximum, description, expected_sha256=None):
                raw = real_read(target, maximum, description, expected_sha256)
                target.write_bytes(replacement)
                return raw

            with mock.patch.object(nf, "_read_stable", side_effect=replace_after_read):
                ref, _, parsed, raw = nf.checked_ref(root, "bound.json", digest(original), "synthetic ref")
            self.assertEqual(raw, original)
            self.assertEqual(parsed, {"value": "bound"})
            self.assertEqual(ref["sha256"], digest(original))
            self.assertEqual(json.loads(path.read_bytes()), {"value": "replacement"})

    def test_owned_scripts_path_is_restored_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = list(sys.path)
            with nf._owned_scripts_path(Path(tmp).resolve()) as scripts:
                self.assertEqual(sys.path[0], str(scripts))
            self.assertEqual(sys.path, original)

    def test_owned_scripts_path_removes_only_its_entry_and_fails_on_foreign_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = list(sys.path)
            scripts = str(Path(tmp).resolve())
            foreign = str(Path(tmp) / "foreign")
            with self.assertRaisesRegex(nf.FinalizationError, "foreign sys.path changes"):
                with nf._owned_scripts_path(Path(tmp).resolve()):
                    sys.path.append(foreign)
            self.assertNotIn(scripts, sys.path)
            self.assertIn(foreign, sys.path)
            sys.path.remove(foreign)
            self.assertEqual(sys.path, original)

    def test_registered_module_scope_cleans_exact_module_on_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp).resolve() / "scripts"
            scripts.mkdir()
            source = scripts / "diagnostic.py"
            raw = b"VALUE = 'bound source'\n"
            source.write_bytes(raw)
            name = "_synthetic_finalizer_owned_diagnostic"
            original = list(sys.path)
            with nf._owned_scripts_path(scripts):
                with nf._registered_module_scope(name, source, scripts_path=scripts,
                                                 expected_sha256=digest(raw)) as module:
                    self.assertIs(sys.modules[name], module)
                    self.assertEqual(module.VALUE, "bound source")
            self.assertNotIn(name, sys.modules)
            self.assertEqual(sys.path, original)

    def test_registered_module_cleanup_never_removes_replacement_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp).resolve() / "scripts"
            scripts.mkdir()
            source = scripts / "diagnostic.py"
            raw = b"VALUE = 'bound source'\n"
            source.write_bytes(raw)
            name = "_synthetic_finalizer_replaced_diagnostic"
            foreign = object()
            original = list(sys.path)
            try:
                with self.assertRaisesRegex(nf.FinalizationError,
                                            "registered module identity changed"):
                    with nf._owned_scripts_path(scripts):
                        with nf._registered_module_scope(name, source,
                                                         scripts_path=scripts,
                                                         expected_sha256=digest(raw)):
                            sys.modules[name] = foreign
                self.assertIs(sys.modules[name], foreign)
                self.assertEqual(sys.path, original)
            finally:
                if sys.modules.get(name) is foreign:
                    del sys.modules[name]

    def test_private_engine_modules_load_exact_pins_and_clean_cache_and_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            runner_path = root / "scripts/joern_normal_runner_v1.py"
            reports_path = root / "scripts/joern_normal_reports_v1.py"
            runner_path.parent.mkdir(parents=True)
            runner_raw = b"VALUE = 'runner-pinned'\n"
            reports_raw = b"VALUE = 'reports-pinned'\n"
            runner_path.write_bytes(runner_raw)
            reports_path.write_bytes(reports_raw)
            refs = [
                {"path": "scripts/joern_normal_runner_v1.py", "sha256": digest(runner_raw)},
                {"path": "scripts/joern_normal_reports_v1.py", "sha256": digest(reports_raw)},
            ]

            class Common:
                def __init__(self):
                    self._PRIVATE_ENGINES = {}
                    self._load_private_module = lambda *args: self.fail("ambient loader used")

                @staticmethod
                def fail(message):
                    raise AssertionError(message)

            common = Common()
            original_loader = common._load_private_module
            runner_name = "_dfb_common_v2_joern_runner_0123456789ab"
            reports_name = "_dfb_common_v2_joern_reports_0123456789ab"
            runner_module = reports_module = None
            with nf._owned_private_engine_modules(common, root, refs):
                reports_module = common._load_private_module(
                    reports_name, reports_path, __import__)
                runner_module = common._load_private_module(
                    runner_name, runner_path, __import__)
                self.assertEqual(reports_module.VALUE, "reports-pinned")
                self.assertEqual(runner_module.VALUE, "runner-pinned")
                self.assertIs(sys.modules[reports_name], reports_module)
                self.assertIs(sys.modules[runner_name], runner_module)
                common._PRIVATE_ENGINES[(str(root), "joern")] = {
                    "runner": runner_module, "reports": reports_module}
            self.assertEqual(common._PRIVATE_ENGINES, {})
            self.assertIs(common._load_private_module, original_loader)
            self.assertNotIn(runner_name, sys.modules)
            self.assertNotIn(reports_name, sys.modules)

    def test_private_engine_module_failure_cleans_only_owned_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root / "scripts/joern_normal_runner_v1.py"
            source.parent.mkdir(parents=True)
            raw = b"raise RuntimeError('synthetic load failure')\n"
            source.write_bytes(raw)
            refs = [{"path": "scripts/joern_normal_runner_v1.py", "sha256": digest(raw)},
                    {"path": "scripts/joern_normal_reports_v1.py", "sha256": "0" * 64}]

            class Common:
                def __init__(self):
                    self._PRIVATE_ENGINES = {}
                    self._load_private_module = lambda *args: None

            common = Common()
            name = "_dfb_common_v2_joern_runner_0123456789ab"
            with self.assertRaisesRegex(RuntimeError, "synthetic load failure"):
                with nf._owned_private_engine_modules(common, root, refs):
                    common._load_private_module(name, source, __import__)
            self.assertNotIn(name, sys.modules)
            self.assertEqual(common._PRIVATE_ENGINES, {})

    def test_private_engine_scope_preserves_unowned_cache_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()

            class Common:
                def __init__(self):
                    self._PRIVATE_ENGINES = {}
                    self._load_private_module = lambda *args: None

            common = Common()
            foreign = {"runner": object(), "reports": object()}
            with self.assertRaisesRegex(nf.FinalizationError,
                                        "unowned private runner cache entry"):
                with nf._owned_private_engine_modules(common, root, []):
                    common._PRIVATE_ENGINES[("foreign", "joern")] = foreign
            self.assertIs(common._PRIVATE_ENGINES[("foreign", "joern")], foreign)
            common._PRIVATE_ENGINES.clear()

    def test_bad_request_is_rejected_before_native_sources_are_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            namespace = nf.QUALIFICATION_ROOT + "native-controls-08"
            paths = {
                "request": nf.QUALIFICATION_ROOT + "native-control-request-08.json",
                "invocation_review": nf.VALIDATION_ROOT + "synthetic-invocation-review.json",
                "native_exit": namespace + "/exit.json",
                "control_result": namespace + "/control-result.json",
                "capture_review": nf.VALIDATION_ROOT + "synthetic-capture-review.json",
                "startup_sidecar_manifest": nf.NATIVE_CAPTURE_VALIDATION_ROOT +
                    "native08-startup-sidecar-manifest-01.json",
                "worker_invocation": namespace + "/worker-invocation.json",
            }
            values = {name: {"schema": "synthetic"} for name in paths}
            for name, rel in paths.items():
                raw = (json.dumps(values[name], sort_keys=True, separators=(",", ":")) + "\n").encode()
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                values[name]["_sha256"] = digest(raw)
            args = SimpleNamespace()
            for name, rel in paths.items():
                setattr(args, name, rel)
                setattr(args, name + "_sha256", values[name]["_sha256"])
            with mock.patch.object(nf, "_load_native_wrapper", side_effect=AssertionError("untrusted import")) as loader:
                with self.assertRaisesRegex(nf.FinalizationError, "exact native10 request schema"):
                    nf._make_bindings(root, args)
                loader.assert_not_called()

    def test_native_wrapper_executes_only_verified_source_buffers_and_cleans_modules(self):
        synthetic = {
            "reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py":
                b"ARCHIVE_MARKER = 'verified-archive'\n",
            "reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py":
                b"PROCESS_MARKER = 'verified-process'\n",
            "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py":
                b"import archive_evidence\nimport process_reconciliation\n"
                b"MARKERS = (archive_evidence.ARCHIVE_MARKER, process_reconciliation.PROCESS_MARKER)\n",
            "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py":
                b"RESOURCE_MARKER = 'pinned-but-not-imported'\n",
        }
        pins = {path: digest(raw) for path, raw in synthetic.items()}
        with mock.patch.object(nf, "NATIVE10_SOURCE_SHA256", pins):
            wrapper = nf._load_native_wrapper(Path("/synthetic/root"), synthetic)
        self.assertEqual(wrapper.MARKERS, ("verified-archive", "verified-process"))
        self.assertTrue(set(("archive_evidence", "process_reconciliation",
                             "joern_native_controls10_postcapture")).isdisjoint(sys.modules))

    def test_native_wrapper_rejects_wrong_source_bytes_before_import(self):
        sources = {path: b"pass\n" for path in nf.NATIVE10_SOURCE_SHA256}
        with mock.patch.dict(sys.modules, {"archive_evidence": None}):
            with self.assertRaisesRegex(nf.FinalizationError, "verified source bytes changed"):
                nf._load_native_wrapper(Path("/synthetic/root"), sources)

    def test_native_wrapper_rejects_preloaded_bare_dependency_identity(self):
        synthetic = {path: b"pass\n" for path in nf.NATIVE10_SOURCE_SHA256}
        pins = {path: digest(raw) for path, raw in synthetic.items()}
        with mock.patch.object(nf, "NATIVE10_SOURCE_SHA256", pins):
            with mock.patch.dict(sys.modules, {"archive_evidence": object()}):
                with self.assertRaisesRegex(nf.FinalizationError, "preloaded native10 module identity"):
                    nf._load_native_wrapper(Path("/synthetic/root"), synthetic)

    def test_finalizer_proves_request_source_at_historical_measured_head(self):
        tree = ast.parse(Path(nf.__file__).read_text())
        finalize = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and
                        node.name == "_finalize_after_bindings")
        calls = [node for node in ast.walk(finalize)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        validate = next(node for node in calls
                        if node.func.attr == "validate_request")
        self.assertTrue(any(keyword.arg == "check_git" and
                            isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                            for keyword in validate.keywords))
        source_check = next(node for node in calls
                            if node.func.attr == "verify_current_source_refs")
        self.assertTrue(any(isinstance(argument, ast.Subscript) and
                            isinstance(argument.slice, ast.Constant) and
                            argument.slice.value == "expected_head"
                            for argument in source_check.args))


class WorkerInvocationTests(unittest.TestCase):
    class Wrapper:
        def validate_worker_argv(self, recorded, actual):
            if recorded[1:] != actual[1:]:
                raise nf.FinalizationError("worker command arguments differ")
            return {"interpreter": "synthetic-verified"}

        def expected_environment(self, root, request, plan):
            return {"HOME": "/task-owned/home", "PLAN": "pending"}

    def setUp(self):
        self.request_ref = {"path": "request.json", "sha256": "a" * 64}
        self.review_ref = {"path": "review.json", "sha256": "b" * 64}
        self.parent_ref = {"path": "parent-started.json", "sha256": "c" * 64}
        self.parent = {
            "process": {"pid": 100, "birth_identity": "parent"},
            "argv": ["/python313", "worker.py", "--request", "request.json"],
            "interpreter_identity": {"parent": "synthetic"},
        }
        self.environment = {"HOME": "/task-owned/home", "PLAN": "pending"}
        self.worker = {
            "schema": "v092-native-control-worker-invocation/v1",
            "request": self.request_ref,
            "review": self.review_ref,
            "parent_started_ref": self.parent_ref,
            "process": {"pid": 101, "birth_identity": "worker"},
            "parent_process": self.parent["process"],
            "recorded_popen_argv": self.parent["argv"],
            "actual_raw_argv": ["/python313-alias", "worker.py", "--request", "request.json"],
            "interpreter_identity": {"interpreter": "synthetic-verified"},
            "parent_interpreter_identity": self.parent["interpreter_identity"],
            "environment": self.environment,
            "environment_sha256": digest((json.dumps(self.environment, sort_keys=True,
                                                      separators=(",", ":")) + "\n").encode()),
            "automatic_retry": False,
        }

    def _validate(self, worker=None):
        nf.validate_native_worker_invocation(Path("/synthetic/root"), worker or self.worker,
            request_ref=self.request_ref, invocation_review_ref=self.review_ref,
            parent_ref=self.parent_ref, parent=self.parent,
            request={"expected_head": "1" * 40}, wrapper=self.Wrapper(), plan={})

    def test_accepts_parent_bound_invocation_with_validated_argv0_alias(self):
        self._validate()

    def test_rejects_worker_request_review_parent_or_environment_near_misses(self):
        for change in (
            {"request": {**self.request_ref, "sha256": "f" * 64}},
            {"review": {**self.review_ref, "sha256": "f" * 64}},
            {"parent_started_ref": {**self.parent_ref, "sha256": "f" * 64}},
            {"recorded_popen_argv": ["/python313", "other.py"]},
            {"environment": {"HOME": "/foreign", "PLAN": "pending"}},
            {"automatic_retry": True},
        ):
            with self.subTest(change=change), self.assertRaises(nf.FinalizationError):
                self._validate({**self.worker, **change})


class ControlResultAndOutputTests(unittest.TestCase):
    def setUp(self):
        self.request_ref = {"path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json",
                            "sha256": "a" * 64}
        self.plan = {"identity": {"tool": "joern", "tool_version": "4.0.660"},
                     "qualification_control_plan": {"sha256": "b" * 64}}
        self.request = {"observer": {"path": "observer.py", "sha256": "c" * 64},
                        "pending_plan": {"path": "pending.json", "sha256": "d" * 64},
                        "control_plan": {"path": "control.json", "sha256": "b" * 64}}
        self.run = {
            "schema": "analyzer-qualification-control-run/v092",
            "control_plan_sha256": "b" * 64,
            "execution_plan_projection_sha256": "e" * 64,
            "identity": self.plan["identity"],
            "records": [{} for _ in range(12)],
            "phase_invocation_count": 36,
            "scored_activation": False,
        }
        self.control_result = {
            "schema": "v092-native-control-qualification-result/v1",
            "request": self.request_ref,
            "observer": self.request["observer"],
            "pending_plan": self.request["pending_plan"],
            "run": self.run,
            "startup_observation": {"qualification_safe": True},
            "scored_activation": False,
            "creates_unsupported_decisions": False,
            "automatic_retry": False,
            **nf.SEMANTIC_SCOPE,
        }

    def test_accepts_exact_12_by_36_control_result(self):
        run, startup = nf.validate_control_result(self.control_result,
            request_ref=self.request_ref, request=self.request,
            plan=self.plan, projection_sha256="e" * 64)
        self.assertIs(run, self.run)
        self.assertIs(startup, self.control_result["startup_observation"])

    def test_rejects_arm_phase_scope_and_version_near_misses(self):
        for changes in (
            {"run": {**self.run, "records": self.run["records"][:11]}},
            {"run": {**self.run, "phase_invocation_count": 35}},
            {"run": {**self.run, "execution_plan_projection_sha256": "f" * 64}},
            {"run": {**self.run, "identity": {"tool": "joern", "tool_version": "4.0.670"}}},
            {"relative_performance_conclusions_authorized": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(nf.FinalizationError):
                nf.validate_control_result({**self.control_result, **changes},
                    request_ref=self.request_ref, request=self.request,
                    plan=self.plan, projection_sha256="e" * 64)

    def test_output_path_is_fresh_and_confined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            parent = root / "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-finalization-03"
            parent.mkdir(parents=True)
            out_rel = "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-finalization-03/run-01"
            out, plan_rel = nf._safe_output(root, out_rel, out_rel + "/execution-plan.json")
            self.assertFalse(out.exists())
            self.assertEqual(plan_rel, out_rel + "/execution-plan.json")
            with self.assertRaises(nf.FinalizationError):
                nf._safe_output(root, "reports/releases/v0.9.2/qualification/outside/run-01",
                                "reports/releases/v0.9.2/qualification/outside/run-01/execution-plan.json")

    def test_source_has_replay_calls_but_no_dispatch_api(self):
        tree = ast.parse(Path(nf.__file__).read_text())
        attrs = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertIn("validate_plan", attrs)
        self.assertIn("_replay_control_run", attrs)
        self.assertIn("replay_admission", attrs)
        self.assertTrue({"Popen", "run_controls", "execute", "run_case",
                         "native_provider_query"}.isdisjoint(attrs))


class RealNative10InterfaceTests(unittest.TestCase):
    def test_real_repair_loader_isolates_mutable_plan_constant_from_canonical_archive(self):
        request = json.loads((nf.ROOT / "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-08.json").read_bytes())
        scripts = nf.ROOT / "scripts"
        with nf._owned_scripts_path(scripts), ExitStack() as owned:
            aliases = nf._load_script_import_aliases(owned, nf.ROOT, request["source_refs"], scripts)
            relative = "scripts/joern_capability_repair_v092_03.py"
            repair = owned.enter_context(nf._registered_module_scope(
                "finalizer_interface_repair", nf.ROOT / relative, scripts_path=scripts,
                expected_sha256=nf._source_ref_sha256(request["source_refs"], relative)))
            canonical = aliases["joern_normal_runner_v092"]
            diagnostic = aliases["joern_diagnostic_admission_v092"]
            self.assertIs(diagnostic, sys.modules["joern_diagnostic_admission_v092"])
            self.assertEqual(diagnostic.SCHEMA, "joern-diagnostic-admission/v1")
            runner = repair._load_runner(nf.ROOT)
            self.assertIsNot(runner, canonical)
            runner.EXECUTION_PLAN_PATH = "qualification/fresh-plan.json"
            repair._assert_canonical_historical_binding(nf.ROOT)
            self.assertEqual(canonical.EXECUTION_PLAN_PATH, repair.OLD_PLAN_PATH)
            runner2 = repair._load_runner(nf.ROOT)
            self.assertIsNot(runner2, runner)
            self.assertEqual(runner2.EXECUTION_PLAN_PATH, repair.OLD_PLAN_PATH)
            common = aliases["swift_common_population_v2"]
            with nf._owned_private_engine_modules(common, nf.ROOT, request["source_refs"]):
                engine = common.private_engine(nf.ROOT, "joern")
                self.assertIs(common.private_engine(nf.ROOT, "joern"), engine)
                names = [module.__name__ for module in engine.values()]
                self.assertTrue(all(name in sys.modules for name in names))
            self.assertEqual(common._PRIVATE_ENGINES, {})
            self.assertTrue(all(name not in sys.modules for name in names))
        tree = ast.parse(Path(nf.__file__).read_bytes())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and
                 isinstance(node.func.value, ast.Name) and node.func.value.id == "old"
                 and node.func.attr in {"validate_bootstrap_inputs", "preflight"}]
        self.assertEqual(len(calls), 2)
        finalizer = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name == "_finalize_after_bindings")
        private_scopes = [node for node in ast.walk(finalizer) if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Name)
                          and node.func.id == "_owned_private_engine_modules"]
        self.assertEqual(len(private_scopes), 1)
        self.assertTrue(all("runner_module" not in {kw.arg for kw in node.keywords} for node in calls))

    def test_emitted_nested_capture_retains_exact_operational_boundary_fields(self):
        tree = ast.parse(Path(nf.__file__).read_bytes())
        captures = [node.value for node in ast.walk(tree)
                    if isinstance(node, ast.keyword) and node.arg == "native_capture"]
        self.assertEqual(len(captures), 1)
        expression = ast.Expression(captures[0])
        inputs = {"phase_count": 36, "refs": {key: {"marker": key} for key in
                  ("request", "native_exit", "control_result", "capture_review")},
                  "invocation_review_ref": {}, "parent_ref": {}, "worker_ref": {},
                  "manifest_ref": {}, "cfg": {"expected_head": "a" * 40},
                  "source_closure_sha256": "b" * 64, "ledger": {},
                  "command_delta_ref": {},
                  "capture_root": "/private/capture", "manifest_result": {"summary": {}}}
        capture = eval(compile(expression, nf.__file__, "eval"), {"__builtins__": {}}, inputs)
        self.assertEqual(capture["control_arms"], 12)
        self.assertEqual(capture["phase_invocations"], inputs["phase_count"])
        self.assertIs(capture["full_model_qualification"], False)
        self.assertIs(capture["scored_activation"], False)
        self.assertEqual(capture["request"], inputs["refs"]["request"])

    def test_exact_ledger_cap_matches_pinned_archive130_and_rejects_extra_byte(self):
        provider = nf.ROOT / "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history-provider-03/history_provider_03.py"
        tree = ast.parse(provider.read_bytes())
        constants = {target.id: ast.literal_eval(node.value)
                     for node in tree.body if isinstance(node, ast.Assign)
                     for target in node.targets if isinstance(target, ast.Name)
                     and target.id in {"LEDGER_RAW_BYTES", "MAX_FILE_BYTES"}
                     and target.id == "LEDGER_RAW_BYTES"}
        manifest_path = nf.ROOT / "reports/releases/v0.9.2/ledger-archives/ledger-130-01/manifest.json"
        manifest_raw = manifest_path.read_bytes()
        self.assertEqual(digest(manifest_raw),
                         "5408d3d312aa3da502ead1eb3f2273aaa05e7c6505305c487221008bdb5ad812")
        manifest = json.loads(manifest_raw)
        self.assertEqual(manifest["source_path"], nf.LEDGER_PATH)
        self.assertEqual(manifest["line_count"], 130)
        self.assertEqual(nf.MAX_LEDGER_BYTES, constants["LEDGER_RAW_BYTES"])
        self.assertEqual(nf.MAX_LEDGER_BYTES, manifest["uncompressed"]["bytes"])
        self.assertEqual(nf.LEDGER_SHA256, manifest["uncompressed"]["sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / "oversize"
            with path.open("wb") as stream:
                stream.truncate(nf.MAX_LEDGER_BYTES + 1)
            with self.assertRaisesRegex(nf.FinalizationError, "size exceeds"):
                nf._read_stable(path, nf.MAX_LEDGER_BYTES, "oversize ledger")

    def test_real_pinned_wrapper_exposes_every_used_api_and_cleans_owned_module(self):
        sources = {relative: (nf.ROOT / relative).read_bytes()
                   for relative in nf.NATIVE10_SOURCE_SHA256}
        wrapper = nf._load_native_wrapper(nf.ROOT, sources)
        tree = ast.parse(Path(nf.__file__).read_text())
        required = {node.attr for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and
                    isinstance(node.value, ast.Name) and node.value.id == "wrapper"}
        for name in required:
            with self.subTest(name=name):
                self.assertTrue(hasattr(wrapper, name), name)
        self.assertNotIn("owned_modules", required)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = b"VALUE = 42\n"
            (root / "owned.py").write_bytes(source)
            with wrapper.owned_module_scope():
                module = wrapper.load(root, {"path": "owned.py", "sha256": digest(source)},
                                      "native10_real_interface_test")
                name = module.__name__
                self.assertEqual(module.VALUE, 42)
                self.assertIs(sys.modules[name], module)
            self.assertNotIn(name, sys.modules)


class PostCleanupPublicationTests(unittest.TestCase):
    def _command_path_audit(self) -> dict:
        runtime_sources = {
            "scripts/joern_capability_repair_v092_03.py": {
                "path": "scripts/joern_capability_repair_v092_03.py",
                "sha256": "8e3d986f20c2262045d8473837d1bf5a56b61da1bc23fee6e778bd0ac47d2b51",
            },
            "scripts/joern_normal_runner_v092.py": {
                "path": "scripts/joern_normal_runner_v092.py",
                "sha256": "683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4",
            },
            "scripts/joern_normal_reports_v092.py": {
                "path": "scripts/joern_normal_reports_v092.py",
                "sha256": "75531186a9091e9e907a2c42388efea0e33d4872787a28fa9fc20b3643131db1",
            },
            "scripts/swift_common_population_v2.py": {
                "path": "scripts/swift_common_population_v2.py",
                "sha256": "3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6",
            },
            "scripts/joern_diagnostic_admission_v092.py": {
                "path": "scripts/joern_diagnostic_admission_v092.py",
                "sha256": "c2faeeb5ef99f539ad8a4bee6fbc85656c0cc142f92196c02f5f26a446140a9e",
            },
        }
        native_tools = {
            "wrapper": {"path": nf.NATIVE_WRAPPER,
                        "sha256": nf.NATIVE10_SOURCE_SHA256[nf.NATIVE_WRAPPER]},
            "resources": {
                "path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py",
                "sha256": nf.NATIVE10_SOURCE_SHA256[
                    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py"],
            },
        }
        pairs = []
        for index, phase in enumerate(("typecheck", "frontend", "query") * 12):
            case_index, arm_index = divmod(index // 3, 2)
            case_id = f"synthetic-case-{case_index}"
            arm = "off" if arm_index == 0 else "on"
            control = f"synthetic-control-{case_index}"
            def ref(label: str) -> dict:
                return {"path": f"synthetic/{label}-{index}.json", "sha256": f"{index % 10}" * 64}
            pairs.append({
                "control": control, "case_id": case_id, "arm": arm, "phase": phase,
                "retained_raw": ref("retained-raw"), "native08_raw": ref("native08-raw"),
                "retained_command": ref("retained-command"),
                "native08_command": ref("native08-command"),
            })
        return {
            "schema": nf.NATIVE08_PATH_DELTA_SCHEMA,
            "status": nf.NATIVE08_PATH_DELTA_STATUS,
            "bindings": {
                "request": nf.NATIVE08_REQUEST_REF,
                "control_result": nf.NATIVE08_CONTROL_RESULT_REF,
                "worker_invocation": nf.NATIVE08_WORKER_INVOCATION_REF,
                "worker_environment_sha256": nf.NATIVE08_WORKER_ENVIRONMENT_SHA256,
                "retained_control_run": nf.RETAINED_CONTROL_RUN_REF,
                "native08_control_run": {"path": nf.NATIVE08_CAPTURE_RUN_PATH, "sha256": "c" * 64},
                "source_head": nf.NATIVE08_SOURCE_HEAD,
                "source_closure_sha256": "d" * 64,
                "retained_observer": nf.NATIVE10_EXPECTED_OBSERVER,
                "pending_plan": nf.NATIVE10_PENDING_PLAN,
                "control_plan": nf.NATIVE08_CONTROL_PLAN,
                "ledger": {"path": nf.LEDGER_PATH, "sha256": nf.LEDGER_SHA256},
                "retained_script": runtime_sources["scripts/joern_capability_repair_v092_03.py"],
                "runtime_sources": runtime_sources,
                "native_tools": native_tools,
                "command_path_helper": nf.COMMAND_PATH_HELPER,
            },
            "recorded_command_comparison": {
                "retained_record_count": 12, "native08_record_count": 12,
                "phase_invocation_count": 36,
                "recorded_input_fields_unchanged_except": "environment.PATH",
                "recorded_environment_keys_equal": True,
                "old_path_sha256": nf.NATIVE08_OLD_PATH_SHA256,
                "native08_path": nf.NATIVE08_SANITIZED_PATH,
                "native08_path_sha256": nf.NATIVE08_SANITIZED_PATH_SHA256,
                "ambient_os_environment_equivalence_proven": False,
                "command_input_equivalence": False,
                "pairs": pairs,
            },
            "interpretation": {
                "scope": "semantic-only",
                "result": "The only changed recorded command-input field is the prescribed PATH; unrecorded historical environment remains unknown.",
                "input_equivalence_claimed": False,
                "uncontended_timing_certified": False,
                "relative_performance_conclusions_authorized": False,
                "full_model_qualification": False,
                "scored_activation": False,
                "publication_approved": False,
                "publication_hold": True,
            },
        }

    def _fake_finalize(self, root: Path, *, failure: str | None = None):
        events = []

        @contextmanager
        def scope(name):
            events.append(name + "-enter")
            try:
                yield
            finally:
                events.append(name + "-exit")
                if failure == name:
                    raise nf.FinalizationError(name + " cleanup failed")

        class Wrapper:
            def owned_module_scope(self):
                return scope("alias")

        def scripts_scope(_path):
            return scope("scripts")

        def prepare(*_args, **kwargs):
            events.append("prepare")
            kwargs["owned"].enter_context(scope("private"))
            return {"prepared": True}

        output_rel = nf.QUALIFICATION_ROOT + "native-finalization-03/attempt-cleanup-test"
        output_dir = root / output_rel
        eligible_rel = output_rel + "/execution-plan.json"
        args = SimpleNamespace(output_dir=output_rel, eligible_plan_path=eligible_rel)
        return events, args, output_dir, eligible_rel, Wrapper(), scripts_scope, prepare

    def test_any_owned_cleanup_failure_blocks_publisher_and_eligible_output(self):
        for failure in ("private", "alias", "scripts"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                (events, args, output_dir, eligible_rel, wrapper,
                 scripts_scope, prepare) = self._fake_finalize(root, failure=failure)
                publisher = mock.Mock(return_value={"published": True})
                with mock.patch.object(nf, "_safe_output",
                                       return_value=(output_dir, eligible_rel)), \
                        mock.patch.object(nf, "_make_bindings",
                                          return_value=({}, {}, wrapper)), \
                        mock.patch.object(nf, "_owned_scripts_path", scripts_scope), \
                        mock.patch.object(nf, "_finalize_after_bindings", side_effect=prepare), \
                        mock.patch.object(nf, "_publish_after_cleanup", publisher):
                    with self.assertRaisesRegex(nf.FinalizationError, "cleanup failed"):
                        nf.finalize(args, root=root)
                publisher.assert_not_called()
                self.assertFalse((root / eligible_rel).exists())

    def test_successful_all_scope_cleanup_precedes_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (events, args, output_dir, eligible_rel, wrapper,
             scripts_scope, prepare) = self._fake_finalize(root)

            def publish(publish_root, prepared):
                events.append("publish")
                self.assertEqual(publish_root, root)
                self.assertEqual(prepared, {"prepared": True})
                self.assertEqual(events, [
                    "scripts-enter", "alias-enter", "prepare", "private-enter",
                    "private-exit", "alias-exit", "scripts-exit", "publish",
                ])
                return {"published": True}

            with mock.patch.object(nf, "_safe_output",
                                   return_value=(output_dir, eligible_rel)), \
                    mock.patch.object(nf, "_make_bindings",
                                      return_value=({}, {}, wrapper)), \
                    mock.patch.object(nf, "_owned_scripts_path", scripts_scope), \
                    mock.patch.object(nf, "_finalize_after_bindings", side_effect=prepare), \
                    mock.patch.object(nf, "_publish_after_cleanup", side_effect=publish):
                result = nf.finalize(args, root=root)
            self.assertEqual(result, {"published": True})

    def _prepared_publication(self, root: Path, candidate_raw: bytes,
                              ledger_raw: bytes) -> tuple[dict, Path, Path, Path]:
        output_rel = nf.QUALIFICATION_ROOT + "native-finalization-03/attempt-publisher-test"
        output_dir = root / output_rel
        output_dir.mkdir(parents=True)
        candidate_rel = output_rel + "/preflight-candidate.json"
        candidate_path = root / candidate_rel
        candidate_path.write_bytes(candidate_raw)
        eligible_path = root / output_rel / "execution-plan.json"
        ledger_path = root / nf.LEDGER_PATH
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_bytes(ledger_raw)
        ledger = {
            "path": nf.LEDGER_PATH,
            "sha256": digest(ledger_raw),
            "rows": nf.EXPECTED_LEDGER_ROWS,
            "status_counts": nf.EXPECTED_LEDGER_COUNTS,
        }
        candidate_ref = {"path": candidate_rel, "sha256": digest(candidate_raw)}
        audit_rel = output_rel + "/command-input-delta-audit.json"
        audit = self._command_path_audit()
        audit["bindings"]["ledger"] = {"path": ledger["path"], "sha256": ledger["sha256"]}
        audit_ref = {"path": audit_rel, "sha256": put_json(root / audit_rel, audit)}
        finalization_receipt = {
            "schema": "v092-joern-post-capture-finalization/v1",
            "status": "diagnostic-replay-complete-publication-held",
            "ledger": ledger,
            "preflight_candidate": candidate_ref,
            "request": nf.NATIVE08_REQUEST_REF,
            "control_result": nf.NATIVE08_CONTROL_RESULT_REF,
            "source_head": nf.NATIVE08_SOURCE_HEAD,
            "source_closure_sha256": "d" * 64,
            "command_input_delta_audit": audit_ref,
            "command_input_comparability": "recorded-fields-only-with-declared-PATH-delta",
            "full_model_qualification": False,
            "scored_activation": False,
            "publication_approved": False,
            "analyzer_invoked_by_finalizer": False,
            **nf.SEMANTIC_SCOPE,
        }
        prepared = {
            "schema": nf.PREPARED_FINALIZATION_SCHEMA,
            "output_dir": output_rel,
            "eligible_plan_path": output_rel + "/execution-plan.json",
            "candidate_plan": candidate_ref,
            "ledger": ledger,
            "finalization_receipt": finalization_receipt,
        }
        return prepared, candidate_path, eligible_path, ledger_path

    def test_publisher_copies_exact_preflight_candidate_after_rechecking_pins(self):
        candidate_raw = b'{ "execution_eligible": true, "status": "execution-eligible" }\n'
        ledger_raw = b"synthetic immutable ledger pin\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prepared, candidate_path, eligible_path, _ledger_path = self._prepared_publication(
                root, candidate_raw, ledger_raw)
            with mock.patch.object(nf, "LEDGER_SHA256", digest(ledger_raw)), \
                    mock.patch.object(nf, "MAX_LEDGER_BYTES", len(ledger_raw)):
                result = nf._publish_after_cleanup(root, prepared)
            self.assertEqual(eligible_path.read_bytes(), candidate_raw)
            assembly_path = eligible_path.parent / "post-capture-finalization.json"
            assembly_raw = assembly_path.read_bytes()
            assembly = json.loads(assembly_raw)
            self.assertEqual(assembly["eligible_plan"], {
                "path": prepared["eligible_plan_path"], "sha256": digest(candidate_raw)})
            self.assertEqual(result["receipt"], {
                "path": assembly_path.relative_to(root).as_posix(),
                "sha256": digest(assembly_raw),
            })
            self.assertEqual(result["command_input_delta_audit"],
                             prepared["finalization_receipt"]["command_input_delta_audit"])
            self.assertEqual(candidate_path.read_bytes(), eligible_path.read_bytes())

    def test_command_path_audit_requires_exact_provenance_and_honest_scope(self):
        audit = self._command_path_audit()
        checked = nf.validate_native08_command_path_audit(
            audit, request_ref=nf.NATIVE08_REQUEST_REF,
            control_result_ref=nf.NATIVE08_CONTROL_RESULT_REF,
            source_head=nf.NATIVE08_SOURCE_HEAD,
            source_closure_sha256="d" * 64,
            ledger_ref={"path": nf.LEDGER_PATH, "sha256": nf.LEDGER_SHA256})
        self.assertIs(checked, audit)
        for mutate in (
            lambda value: value["bindings"].update(request={"path": "other.json", "sha256": "a" * 64}),
            lambda value: value["bindings"].update(command_path_helper={"path": "other.py", "sha256": "a" * 64}),
            lambda value: value["recorded_command_comparison"].update(command_input_equivalence=True),
            lambda value: value["recorded_command_comparison"].update(ambient_os_environment_equivalence_proven=True),
            lambda value: value["recorded_command_comparison"]["pairs"].pop(),
            lambda value: value["interpretation"].update(uncontended_timing_certified=True),
            lambda value: value["interpretation"].update(publication_hold=False),
        ):
            bad = json.loads(json.dumps(audit))
            mutate(bad)
            with self.subTest(mutate=mutate), self.assertRaises(nf.FinalizationError):
                nf.validate_native08_command_path_audit(
                    bad, request_ref=nf.NATIVE08_REQUEST_REF,
                    control_result_ref=nf.NATIVE08_CONTROL_RESULT_REF,
                    source_head=nf.NATIVE08_SOURCE_HEAD,
                    source_closure_sha256="d" * 64,
                    ledger_ref={"path": nf.LEDGER_PATH, "sha256": nf.LEDGER_SHA256})

    def test_publisher_rechecks_command_path_audit_before_eligible_write(self):
        candidate_raw = b'{"execution_eligible":true}\n'
        ledger_raw = b"synthetic immutable ledger pin\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prepared, _candidate_path, eligible_path, _ledger_path = self._prepared_publication(
                root, candidate_raw, ledger_raw)
            ref = prepared["finalization_receipt"]["command_input_delta_audit"]
            (root / ref["path"]).write_bytes(b"{}\n")
            with mock.patch.object(nf, "LEDGER_SHA256", digest(ledger_raw)), \
                    mock.patch.object(nf, "MAX_LEDGER_BYTES", len(ledger_raw)):
                with self.assertRaisesRegex(nf.FinalizationError, "SHA-256 mismatch"):
                    nf._publish_after_cleanup(root, prepared)
            self.assertFalse(eligible_path.exists())

    def test_publisher_rejects_candidate_drift_before_eligible_write(self):
        candidate_raw = b'{"execution_eligible":true}\n'
        ledger_raw = b"synthetic immutable ledger pin\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prepared, candidate_path, eligible_path, _ledger_path = self._prepared_publication(
                root, candidate_raw, ledger_raw)
            candidate_path.write_bytes(b'{"execution_eligible":false}\n')
            with mock.patch.object(nf, "LEDGER_SHA256", digest(ledger_raw)), \
                    mock.patch.object(nf, "MAX_LEDGER_BYTES", len(ledger_raw)):
                with self.assertRaisesRegex(nf.FinalizationError, "SHA-256 mismatch"):
                    nf._publish_after_cleanup(root, prepared)
            self.assertFalse(eligible_path.exists())

    def test_publisher_rejects_ledger_drift_before_eligible_write(self):
        candidate_raw = b'{"execution_eligible":true}\n'
        ledger_raw = b"synthetic immutable ledger pin\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prepared, _candidate_path, eligible_path, ledger_path = self._prepared_publication(
                root, candidate_raw, ledger_raw)
            ledger_path.write_bytes(b"x" * len(ledger_raw))
            with mock.patch.object(nf, "LEDGER_SHA256", digest(ledger_raw)), \
                    mock.patch.object(nf, "MAX_LEDGER_BYTES", len(ledger_raw)):
                with self.assertRaisesRegex(nf.FinalizationError, "SHA-256 mismatch"):
                    nf._publish_after_cleanup(root, prepared)
            self.assertFalse(eligible_path.exists())

    def test_prepare_phase_has_no_eligible_or_finalization_writer(self):
        tree = ast.parse(Path(nf.__file__).read_bytes())
        prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                       and node.name == "_finalize_after_bindings")
        calls = [node for node in ast.walk(prepare) if isinstance(node, ast.Call)]
        called_names = {node.func.id for node in calls if isinstance(node.func, ast.Name)}
        written_names = {
            node.args[0].id for node in calls
            if isinstance(node.func, ast.Name) and node.func.id == "_write_exclusive" and
            node.args and isinstance(node.args[0], ast.Name)
        }
        string_constants = {node.value for node in ast.walk(prepare)
                            if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertNotIn("_publish_after_cleanup", called_names)
        self.assertEqual(written_names,
                         {"run_path", "review_path", "command_delta_path", "receipt_path", "candidate_path"})
        self.assertNotIn("_write_raw_exclusive", called_names)
        self.assertNotIn("post-capture-finalization.json", string_constants)
        self.assertTrue(any(value.endswith("/preflight-candidate.json")
                            for value in string_constants))

    def test_publisher_has_no_runner_or_provider_imports(self):
        tree = ast.parse(Path(nf.__file__).read_bytes())
        publisher = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name == "_publish_after_cleanup")
        nodes = list(ast.walk(publisher))
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in nodes))
        called_names = {node.func.id for node in nodes
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue({"validate_plan", "validate_request", "private_engine",
                         "replay_admission", "_load_native_wrapper"}.isdisjoint(called_names))

    def test_assembly_io_failure_keeps_only_incomplete_partial_attempt(self):
        candidate_raw = b'{"execution_eligible":true}\n'
        ledger_raw = b"synthetic immutable ledger pin\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prepared, _candidate_path, eligible_path, _ledger_path = self._prepared_publication(
                root, candidate_raw, ledger_raw)
            original_writer = nf._write_raw_exclusive

            def fail_assembly(path, raw):
                if path.name == "post-capture-finalization.json":
                    raise OSError("synthetic final assembly write failure")
                return original_writer(path, raw)

            with mock.patch.object(nf, "LEDGER_SHA256", digest(ledger_raw)), \
                    mock.patch.object(nf, "MAX_LEDGER_BYTES", len(ledger_raw)), \
                    mock.patch.object(nf, "_write_raw_exclusive", side_effect=fail_assembly):
                with self.assertRaisesRegex(OSError, "final assembly"):
                    nf._publish_after_cleanup(root, prepared)
            self.assertEqual(eligible_path.read_bytes(), candidate_raw)
            self.assertFalse((eligible_path.parent / "post-capture-finalization.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
