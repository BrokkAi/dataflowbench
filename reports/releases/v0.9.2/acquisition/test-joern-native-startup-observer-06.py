#!/usr/bin/env python3
"""Isolated synthetic tests for the v6 Joern startup observer.

No Java, Java agent, Joern, Swift compiler, analyzer, replay, or engine
qualification is launched here. The fake process callback only writes the
same shape of agent receipt that the reviewed Java source produces.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import sys
import unittest

MODULE_PATH = Path(__file__).with_name("joern-native-startup-observer-06.py")
REPO_SCRIPTS = (Path(__file__).resolve().parents[4] / "scripts")
if str(REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(REPO_SCRIPTS))
SPEC = importlib.util.spec_from_file_location("joern_native_control_observer_v06_tested", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
observer_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer_module)
RUNNER_PATH = (REPO_SCRIPTS / "joern_normal_runner_v1.py")
RUNNER_SPEC = importlib.util.spec_from_file_location("joern_v3_retained_runner", RUNNER_PATH)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
retained_runner = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(retained_runner)


def b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


SYNTHETIC_SECONDS = 1704067200
SYNTHETIC_NANOS = 123000000
SYNTHETIC_INSTANT = "2024-01-01T00:00:00.123Z"


def good_env(observer, *, ambient=None):
    observer.ensure_home()
    env = {
        "JAVA_HOME": "/private/tmp/fake-java-21",
        "JAVA_TOOL_OPTIONS": observer_module._expected_option(observer.policy, observer.home),
        "JAVA_OPTS": observer.policy["retained_java_opts"],
        "HOME": "/private/tmp/fake-parent-home",
        "TMPDIR": str(observer.output / "tmp"),
        "PATH": "/private/tmp/fake-java-21/bin:/usr/bin",
        "SWIFTASTGEN_BIN": "/private/tmp/fake-astgen",
        "LANG": "C", "LC_ALL": "C",
    }
    env.update(ambient or {})
    return env


def witness(observer, event_dir, pid, command, *, home=None, predef=False,
            identity=None, parent_pid=None, parent_identity=None):
    home = str(home if home is not None else observer.home.resolve())
    payload = {
        "schema": observer_module.WITNESS_SCHEMA,
        "agent_version": "synthetic",
        "pid": pid,
        "parent_pid": parent_pid,
        "process_start_identity": identity or SYNTHETIC_INSTANT,
        "process_start_epoch_seconds": SYNTHETIC_SECONDS,
        "process_start_epoch_nanos": SYNTHETIC_NANOS,
        "parent_start_identity": parent_identity,
        "parent_start_epoch_seconds": SYNTHETIC_SECONDS if parent_pid not in (None, 0) else None,
        "parent_start_epoch_nanos": SYNTHETIC_NANOS if parent_pid not in (None, 0) else None,
        "runtime_start_millis": 123,
        "user_home_b64": b64(home),
        "java_command_present": command is not None,
        "java_command_b64": b64(command or ""),
        "java_class_path_b64": b64("synthetic-classpath"),
        "predef_path_b64": b64(str(observer.predef)),
        "predef_present": predef,
        "predef_symlink": predef,
        "witness_directory_b64": b64(str(Path(event_dir).resolve())),
    }
    (Path(event_dir) / f"jvm-{pid}.json").write_text(json.dumps(payload) + "\n")


def fake_runner(argv, directory, name, timeout, measure=False, env=None, cwd=None,
                *, roles=True, wrong_home=None, unknown=False, fail=False,
                no_witness=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    event_dir = Path(env[observer_module.AGENT_ENV])
    tracked = []
    commands = {
        "version": ["io.joern.joerncli.console.ReplBridge"],
        "frontend": ["io.joern.swiftsrc2cpg-4.0.660-launcher.jar"],
        "query": ["io.joern.joerncli.console.ReplBridge",
                  "replpp.scripting.NonForkingScriptRunner"],
        "typecheck": [],
    }[name]
    if roles and not no_witness:
        for index, command in enumerate(commands, 1):
            pid = 2000 + index
            tracked.append({"pid": pid, "start_identity": "1704067200:123000"})
            witness(observer_ref, event_dir, pid,
                    "unknown.command" if unknown else command,
                    home=wrong_home)
    (directory / f"{name}.stdout").write_text("synthetic stdout\n")
    (directory / f"{name}.stderr").write_text("Picked up JAVA_TOOL_OPTIONS: ignored text\n")
    record = {
        "argv": list(argv), "cwd": str(cwd or directory), "exit_status": 0,
        "timed_out": False, "cleanup_status": "tracked-processes-stopped",
        "elapsed_seconds": 0.01, "deadline_seconds": timeout,
        "tracked_descendants": tracked,
    }
    (directory / f"{name}.command.json").write_text(json.dumps(record) + "\n")
    if fail:
        raise RuntimeError("synthetic process failure")
    return record


class ObserverTests(unittest.TestCase):
    def make_observer(self, root, output, **kwargs):
        return observer_module.StartupObserver(
            root, output, observer_module.STARTUP_POLICY_V4,
            static_check=False, **kwargs,
        )

    def setUp(self):
        global observer_ref
        observer_ref = None

    def test_birth_identity_precision_is_typed_and_near_miss_rejected(self):
        payload = {
            "process_start_identity": "2024-01-01T00:00:00.123456789Z",
            "process_start_epoch_seconds": SYNTHETIC_SECONDS,
            "process_start_epoch_nanos": 123456789,
        }
        self.assertEqual(
            observer_module._parse_java_birth(payload, "synthetic"),
            (SYNTHETIC_SECONDS, 123456789),
        )
        with self.assertRaises(observer_module.ObservationError):
            observer_module._parse_java_birth(
                {**payload, "process_start_epoch_nanos": 123456000}, "truncated"
            )
        self.assertEqual(
            observer_module._native_birth_comparison(
                SYNTHETIC_SECONDS, 123000000, "1704067200:123456", "positive"
            ),
            (True, "java-millisecond-floor"),
        )
        self.assertFalse(observer_module._native_birth_matches(
            SYNTHETIC_SECONDS, 123000000, "1704067200:124000", "near-miss"
        ))

    def test_actual_captured_v4_witness_binds_process_record_projection(self):
        fixture = json.loads(
            (Path(__file__).with_name("joern-startup-witness-actual-probe-04.json")).read_text()
        )
        self.assertFalse(fixture["engine_invoked"])
        payload = fixture["witness"]
        seconds, nanos = observer_module._parse_java_birth(payload, "captured")
        tracked = observer_module._process_identity_map(fixture["process_record"])
        self.assertEqual(payload["pid"], next(iter(tracked)))
        self.assertEqual(
            observer_module._native_birth_comparison(
                seconds, nanos, tracked[payload["pid"]], "captured"
            ),
            (True, "java-millisecond-floor"),
        )
        self.assertEqual(payload["schema"], observer_module.WITNESS_SCHEMA)

    def test_positive_agent_bridge_and_fork_witnesses(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v3-positive-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            observer.process_runner = fake_runner
            result = observer.observed_run(
                ["/private/tmp/fake/joern", "--script", "query.sc"], output,
                "query", 30, env=good_env(observer), cwd=output)
            self.assertEqual(result["exit_status"], 0)
            self.assertEqual([x["role"] for x in observer.events[0]["jvm_witnesses"]],
                             ["bridge", "query-script-fork"])
            self.assertEqual(observer.events[0]["property_witness"]["status"],
                             "exact-in-process-System.getProperty")

    def test_phase_wrapper_uses_actual_early_bound_phase_seam(self):
        path = (REPO_SCRIPTS / "joern_normal_runner_v1.py")
        spec = importlib.util.spec_from_file_location("joern_v3_phase", path)
        assert spec is not None and spec.loader is not None
        retained = importlib.util.module_from_spec(spec); spec.loader.exec_module(retained)
        with tempfile.TemporaryDirectory(prefix="joern05-v3-phase-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            observer.process_runner = fake_runner
            retained.phase(["/private/tmp/fake/swiftsrc2cpg"], output, "frontend",
                           time.monotonic() + 30, good_env(observer),
                           invoke=observer.observed_run)
            self.assertEqual(observer.events[0]["phase"], "frontend")
            self.assertTrue((output / "frontend.command.json").is_file())

    def test_missing_or_unclassified_witness_fails_closed(self):
        for kwargs in ({"no_witness": True}, {"unknown": True}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory(prefix="joern05-v3-miss-") as tmp:
                root = Path(tmp); output = root / "capture"
                observer = self.make_observer(root, output)
                global observer_ref
                observer_ref = observer
                observer.process_runner = lambda *a, **k: fake_runner(*a, **k, **kwargs)
                with self.assertRaises(observer_module.ObservationError):
                    observer.observed_run(["/private/tmp/fake/joern"], output,
                                         "version", 30, env=good_env(observer), cwd=output)
                self.assertEqual(len(observer.events), 1)
                if kwargs.get("unknown"):
                    self.assertEqual(observer.events[0]["jvm_witnesses"][0]["role"],
                                     "unclassified")

    def test_untracked_short_version_requires_parent_correlation(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v4-short-version-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer

            def short_version_runner(argv, directory, name, timeout, measure=False,
                                     env=None, cwd=None):
                directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
                event_dir = Path(env[observer_module.AGENT_ENV])
                witness(observer, event_dir, 2301,
                        "-version", parent_pid=None)
                (directory / f"{name}.stdout").write_text("")
                (directory / f"{name}.stderr").write_text("")
                record = {"tracked_descendants": [], "exit_status": 0,
                          "timed_out": False,
                          "cleanup_status": "tracked-processes-stopped",
                          "elapsed_seconds": 0.01}
                (directory / f"{name}.command.json").write_text(json.dumps(record))
                return record

            observer.process_runner = short_version_runner
            with self.assertRaises(observer_module.ObservationError):
                observer.observed_run(["/private/tmp/fake/java", "-version"], output,
                                      "version", 30, env=good_env(observer), cwd=output)

    def test_untracked_version_without_java_command_is_diagnostic_only(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v4-version-diagnostic-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer

            def version_runner(argv, directory, name, timeout, measure=False,
                               env=None, cwd=None):
                directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
                event_dir = Path(env[observer_module.AGENT_ENV])
                witness(observer, event_dir, 2401,
                        "io.joern.joerncli.console.ReplBridge")
                parent_pid = os.getpid()
                host_identity = observer_module._host_start_identity(parent_pid)
                self.assertIsNotNone(host_identity)
                witness(observer, event_dir, 2402, None, parent_pid=parent_pid,
                        parent_identity=host_identity)
                payload_path = event_dir / "jvm-2402.json"
                payload = json.loads(payload_path.read_text())
                host_seconds, host_micros = host_identity.split(":", 1)
                from datetime import datetime, timezone
                host_dt = datetime.fromtimestamp(int(host_seconds), timezone.utc).replace(
                    microsecond=int(host_micros)
                )
                payload["parent_start_identity"] = host_dt.isoformat(
                    timespec="microseconds"
                ).replace("+00:00", "Z")
                payload["parent_start_epoch_seconds"] = int(host_seconds)
                payload["parent_start_epoch_nanos"] = int(host_micros) * 1000
                payload_path.write_text(json.dumps(payload) + "\n")
                tracked = [{"pid": 2401, "start_identity": "1704067200:123000"}]
                (directory / f"{name}.stdout").write_text("")
                (directory / f"{name}.stderr").write_text("")
                record = {"tracked_descendants": tracked, "exit_status": 0,
                          "timed_out": False,
                          "cleanup_status": "tracked-processes-stopped",
                          "elapsed_seconds": 0.01}
                (directory / f"{name}.command.json").write_text(json.dumps(record))
                return record

            observer.process_runner = version_runner
            observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                  env=good_env(observer), cwd=output)
            diagnostic = next(row for row in observer.events[0]["jvm_witnesses"]
                              if row["pid"] == 2402)
            self.assertEqual(diagnostic["role"], "version-check")
            self.assertFalse(diagnostic["birth_verified"])

    def test_host_parent_birth_identity_is_bound_when_java_replaces_launcher(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v3-parent-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer

            def parent_runner(argv, directory, name, timeout, measure=False, env=None, cwd=None):
                directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
                event_dir = Path(env[observer_module.AGENT_ENV])
                pid = 2201
                parent_pid = os.getpid()
                witness(observer, event_dir, pid,
                        "io.joern.joerncli.console.ReplBridge",
                        parent_pid=parent_pid,
                        parent_identity=observer_module._host_start_identity(parent_pid))
                payload_path = event_dir / "jvm-2201.json"
                payload = json.loads(payload_path.read_text())
                # Bind the Java parent Instant to the actual host identity
                # observed by the retained native helper.  This exercises the
                # host-parent path without inventing a birth value.
                host_identity = observer_module._host_start_identity(parent_pid)
                self.assertIsNotNone(host_identity)
                host_seconds, host_micros = host_identity.split(":", 1)
                from datetime import datetime, timezone
                host_dt = datetime.fromtimestamp(
                    int(host_seconds), tz=timezone.utc
                ).replace(microsecond=int(host_micros))
                payload["parent_start_identity"] = host_dt.isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                )
                payload["parent_start_epoch_seconds"] = int(host_seconds)
                payload["parent_start_epoch_nanos"] = int(host_micros) * 1000
                payload_path.write_text(json.dumps(payload) + "\n")
                (directory / f"{name}.stdout").write_text("")
                (directory / f"{name}.stderr").write_text("")
                record = {"tracked_descendants": [{"pid": pid, "start_identity": "1704067200:123000"}],
                          "exit_status": 0, "timed_out": False,
                          "cleanup_status": "tracked-processes-stopped", "elapsed_seconds": 0.01}
                (directory / f"{name}.command.json").write_text(json.dumps(record))
                return record

            observer.process_runner = parent_runner
            observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                  env=good_env(observer), cwd=output)
            self.assertEqual(observer.events[0]["jvm_witnesses"][0]["parent_pid"], os.getpid())

    def test_home_and_predef_near_misses_fail(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v3-home-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            observer.process_runner = lambda *a, **k: fake_runner(*a, **k,
                                                                   wrong_home="/wrong-home")
            with self.assertRaises(observer_module.ObservationError):
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)
        with tempfile.TemporaryDirectory(prefix="joern05-v3-predef-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            observer.ensure_home(); observer.predef.write_text("ambient\n")
            observer_ref = observer
            observer.process_runner = fake_runner
            with self.assertRaises(observer_module.ObservationError):
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)

    def test_malformed_failure_witness_retained_without_masking_original(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v5-malformed-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            original = RuntimeError("original failure identity")
            def runner(*a, **k):
                fake_runner(*a, **k)
                event_dir = Path(k["env"][observer_module.AGENT_ENV])
                (event_dir / "jvm-2001.json").write_text("malformed")
                raise original
            observer.process_runner = runner
            with self.assertRaises(RuntimeError) as caught:
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)
            self.assertIs(caught.exception, original)
            event = observer.events[0]
            self.assertEqual(len(event["jvm_witness_files"]), 1)
            self.assertEqual(event["jvm_witnesses"], [])
            self.assertTrue(event["failure_evidence_errors"])
            self.assertIsNone(event["result"])
            self.assertFalse(observer.summary()["qualification_safe"])

    def test_failure_before_process_record_does_not_claim_startup(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v5-early-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            original = RuntimeError("early process failure")
            def runner(*a, **k):
                raise original
            observer.process_runner = runner
            with self.assertRaises(RuntimeError) as caught:
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)
            self.assertIs(caught.exception, original)
            event = observer.events[0]
            self.assertEqual(event["jvm_witness_files"], [])
            self.assertEqual(event["jvm_witnesses"], [])
            self.assertIsNone(event["failure_process_record"])
            self.assertIsNone(event["result"])
            self.assertFalse(observer.summary()["qualification_safe"])

    def test_returned_process_record_is_failure_only_on_missing_witness(self):
        self._returned_record_failure(False)

    def test_returned_process_record_is_failure_only_on_malformed_witness(self):
        self._returned_record_failure(True)

    def _returned_record_failure(self, malformed):
        with tempfile.TemporaryDirectory(prefix="joern05-v6-result-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            def runner(*a, **k):
                record = fake_runner(*a, **k, no_witness=not malformed)
                if malformed:
                    event_dir = Path(k["env"][observer_module.AGENT_ENV])
                    (event_dir / "jvm-2001.json").write_text("malformed")
                return record
            observer.process_runner = runner
            with self.assertRaises((observer_module.ObservationError, ValueError)):
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)
            event = observer.events[0]
            self.assertIsNone(event["result"])
            self.assertEqual(event["failure_process_record"]["exit_status"], 0)
            self.assertEqual(event["property_witness"]["status"], "failure-only")
            self.assertFalse(observer.summary()["qualification_safe"])
            if malformed:
                self.assertEqual(len(event["jvm_witness_files"]), 1)
                self.assertTrue(event["failure_evidence_errors"])

    def test_factory_binds_actual_phase_and_shared_process_once(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v3-factory-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            def original_process(*args, **kwargs):
                return fake_runner(*args, **kwargs)
            def original_env(_runtime):
                return good_env(observer)
            shared_process = SimpleNamespace(run=original_process)
            engine = SimpleNamespace(env_for=original_env, phase=retained_runner.phase,
                                    process=shared_process)
            original_factory = lambda *args, **kwargs: {"runner": engine}
            common = SimpleNamespace(private_engine=original_factory)
            scope = observer_module.ScopedObservation(common, observer)
            with scope:
                bundle = common.private_engine(root, "joern")
                env = bundle["runner"].env_for({})
                bundle["runner"].phase(["/private/tmp/fake/joern"], output, "version",
                                       time.monotonic() + 30, env)
                # A second factory entry returns the cached/shared process
                # object and must not bind the observer callback recursively.
                common.private_engine(root, "joern")
            self.assertEqual(observer.events[0]["phase"], "version")
            self.assertIs(shared_process.run, original_process)
            self.assertIs(common.private_engine, original_factory)

    def test_failure_sidecar_and_factory_runner_binding_restore(self):
        with tempfile.TemporaryDirectory(prefix="joern05-v3-failure-") as tmp:
            root = Path(tmp); output = root / "capture"
            observer = self.make_observer(root, output)
            global observer_ref
            observer_ref = observer
            observer.process_runner = lambda *a, **k: fake_runner(*a, **k, fail=True)
            with self.assertRaisesRegex(RuntimeError, "synthetic process failure"):
                observer.observed_run(["/private/tmp/fake/joern"], output, "version", 30,
                                     env=good_env(observer), cwd=output)
            self.assertEqual(observer.events[0]["error"]["type"], "RuntimeError")
            event = observer.events[0]
            self.assertIsNone(event["result"])
            self.assertEqual(len(event["jvm_witnesses"]), 1)
            self.assertEqual(len(event["jvm_witness_files"]), 1)
            self.assertEqual(event["failure_process_record"]["exit_status"], 0)
            self.assertEqual(event["property_witness"]["status"], "failure-only")
            summary = observer.write_summary()
            self.assertEqual(summary["status"], "failed")
            self.assertFalse(summary["qualification_safe"])

            calls = []
            def original_process(*args, **kwargs):
                calls.append("original")
                return fake_runner(*args, **kwargs)
            def original_env(_runtime):
                return good_env(observer)
            engine = SimpleNamespace(
                env_for=original_env,
                phase=retained_runner.phase,
                process=SimpleNamespace(run=original_process),
            )
            original_factory = lambda *args, **kwargs: {"runner": engine}
            common = SimpleNamespace(private_engine=original_factory)
            observer.process_runner = None
            saved_runner = observer.process_runner
            scope = observer_module.ScopedObservation(common, observer)
            with scope:
                bundle = common.private_engine(root, "joern")
                self.assertIs(observer.process_runner, original_process)
                self.assertIsNot(bundle["runner"].process.run, original_process)
                # Re-entering the same factory must not bind the already-patched
                # observer callback as the original process runner.
                common.private_engine(root, "joern")
            self.assertIs(common.private_engine, original_factory)
            self.assertIs(engine.process.run, original_process)
            self.assertIs(observer.process_runner, saved_runner)



if __name__ == "__main__":
    unittest.main()
