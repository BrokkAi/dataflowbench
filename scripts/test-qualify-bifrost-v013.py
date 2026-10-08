#!/usr/bin/env python3
"""Tests for the mocked, evidence-preserving Bifrost v0.13 control."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("qualify-bifrost-v013.py")
SPEC = importlib.util.spec_from_file_location("qualify_bifrost_v013", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finding(policy_id: str) -> dict[str, object]:
    return {
        "id": "finding-id",
        "identity_stability": "strong",
        "policy_id": policy_id,
        "policy_hash": "policy-hash",
        "analysis_type": "taint",
        "severity": "warning",
        "message": "declared flow",
        "classification": {"type": "unclassified"},
        "certainty": {"type": "definite"},
        "completeness": {"type": "complete"},
        "primary": {"path": "fixture.source", "byte_span": {"start": 0, "end": 1}},
        "related": [],
        "related_truncated": False,
        "omitted_related_locations_lower_bound": 0,
        "evidence": {"type": "taint", "evidence": {"source": "mock"}},
        "evidence_refs_truncated": False,
        "omitted_evidence_refs_lower_bound": 0,
        "cvss": None,
        "organizational_risk": None,
        "proof": {"state": "proven", "reasons": [{"type": "dataflow_witness"}]},
        "witnesses": [],
        "witnesses_truncated": False,
        "omitted_witnesses_lower_bound": 0,
        "display_path": {},
        "suppression": None,
        "scope": None,
    }


def report(language: str, count: int) -> dict[str, object]:
    policy_id = f"dataflowbench.taint.model-{language}"
    run = {
        "policy_id": policy_id,
        "policy_hash": "policy-hash",
        "analysis_type": "taint",
        "completion": {"type": "complete"},
        "findings": [finding(policy_id) for _ in range(count)],
        "diagnostics": [],
        "diagnostics_truncated": False,
        "obligations": [],
        "obligations_truncated": False,
        "omitted_obligations_lower_bound": 0,
        "work": {"scanned_files": 1, "retained_findings": count},
    }
    rule = {
        "policy_id": policy_id,
        "policy_hash": "policy-hash",
        "analysis_type": "taint",
        "policy_schema": {"version": 1, "origin": "explicit"},
        "selector_schemas": [],
        "endpoint_dependencies": [],
        "match_directory_manifests": [],
        "precedence_manifest": {"edges": []},
        "name": "mock policy",
        "message": {"type": "static", "text": "declared flow"},
        "severity": {"type": "fixed", "level": "warning"},
        "description": None,
        "help_uri": None,
        "tags": [],
    }
    return {
        "schema_version": 5,
        "evaluation": {},
        "execution": {},
        "rules": [rule],
        "runs": [run],
        "suppressions": [],
        "scope": [],
        "packs": {"document_path": ".bifrost/packs.json", "complete": True},
        "diagnostics": [],
        "diagnostics_truncated": False,
        "omitted_diagnostics_lower_bound": 0,
        "worst_omitted_diagnostic_severity": None,
    }


def native_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "not-evaluated",
        "reason": "no-active-rule-packs",
        "findings": [],
    }


class MockBifrost:
    def __init__(self, *, catalog: object | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.catalog = {"schema_version": 2, "packs": []} if catalog is None else catalog

    def run(self, argv, *, cwd, stdout, stderr, env, timeout):
        argv = [str(value) for value in argv]
        self.calls.append({"argv": argv, "cwd": cwd, "env": dict(env), "timeout": timeout})
        stdout.write(b"mock stdout\n")
        stderr.write(b"mock stderr\n")
        if argv[-1:] == ["--version"]:
            stdout.seek(0)
            stdout.truncate()
            stdout.write(b"bifrost 0.13.0\n")
            return 0
        if argv[-1:] == ["--build-identity"]:
            stdout.seek(0)
            stdout.truncate()
            stdout.write((MODULE.EXPECTED_BUILD_IDENTITY + "\n").encode())
            return 0
        if "--list-builtin-policies" in argv or "--list-policies" in argv:
            stdout.seek(0)
            stdout.truncate()
            indent = 2 if "--list-policies" in argv else None
            stdout.write((json.dumps(self.catalog, indent=indent) + "\n").encode())
            return 0
        if "scan" in argv and "--policy-file" not in argv:
            stdout.seek(0)
            stdout.truncate()
            stdout.write((json.dumps(native_report()) + "\n").encode())
            return 0
        if "--output" in argv:
            output = Path(argv[argv.index("--output") + 1])
            name = output.stem
            language = next(language for language in MODULE.LANGUAGES if f"-{language}-" in name)
            if "sanitizer" in name:
                count = 1 if (
                    "kill-positive" in name
                    or "selectivity-positive" in name
                    or ("kill-negative-without" in name)
                ) else 0
            else:
                count = 1 if name.endswith("positive-with") else 0
            document = report(language, count)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(document) + "\n", encoding="utf-8")
        return 0


class QualifyBifrostV013Tests(unittest.TestCase):
    def test_mocked_capture_runs_all_controls_serially_and_retains_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            root.mkdir()
            binary = root / "bifrost"
            binary.write_bytes(b"mock pinned binary")
            output = Path(temporary) / "capture"
            runner = MockBifrost()
            with patch.object(MODULE, "EXPECTED_BINARY_SHA256", sha256(binary)), \
                 patch.object(MODULE, "ROOT", root):
                # Populate the minimal repository files used by the capture.
                for language, extension in (("java", "java"), ("javascript", "js"), ("python", "py")):
                    policy_dir = root / "adapters/bifrost/policies"
                    policy_dir.mkdir(parents=True, exist_ok=True)
                    (policy_dir / f"model-{language}.rqlp").write_text(
                        f"(policy :schema-version 1 (analysis (source :id declared-source) (sink :id declared-sink)))\n",
                        encoding="utf-8",
                    )
                    for case in (
                        "model-declared-source-positive", "model-declared-source-negative",
                        "model-declared-sink-positive", "model-declared-sink-negative",
                        "model-sanitizer-kill-positive", "model-sanitizer-kill-negative",
                        "model-sanitizer-selectivity-positive", "model-sanitizer-selectivity-negative",
                        "native-source-sink-positive",
                    ):
                        case_dir = root / "cases/taint" / language / case
                        case_dir.mkdir(parents=True, exist_ok=True)
                        (case_dir / f"fixture.{extension}").write_text("source(); sink();\n", encoding="utf-8")
                # The mocked sanitizer section must be removable by the control.
                for language in ("java", "javascript", "python"):
                    policy = root / "adapters/bifrost/policies" / f"model-{language}.rqlp"
                    policy.write_text(
                        "(policy :schema-version 1\n"
                        "  :analysis (analysis\n"
                        "    :sources (endpoint-set :entries [(source :id declared-source)])\n"
                        "    :sanitizers (endpoint-set :entries [(sanitizer :id declared-sanitizer)])\n"
                        "    :sinks (endpoint-set :entries [(sink :id declared-sink)])))\n",
                        encoding="utf-8",
                    )
                status = MODULE.capture(binary, output, root=root, runner=runner.run)
            qualification = json.loads((output / "qualification.json").read_text())
            self.assertEqual(status, 0, qualification["failures"])
            self.assertEqual(len(runner.calls), 44)
            self.assertTrue((output / "commands.jsonl").is_file())
            self.assertTrue((output / "stdout/catalog-list-policies.txt").is_file())
            self.assertTrue((output / "stderr/native-python-source-sink-positive.txt").is_file())
            self.assertTrue((output / "native-summary.json").is_file())
            native_call = next(
                call for call in runner.calls
                if call["argv"][1:2] == ["scan"] and "--list-builtin-policies" not in call["argv"]
            )
            self.assertNotIn("--output", native_call["argv"])
            self.assertEqual(
                json.loads((output / "stdout/native-python-source-sink-positive.txt").read_text()),
                native_report(),
            )
            self.assertFalse((output / "reports/native-python-source-sink-positive.json").exists())
            self.assertEqual(qualification["qualification"], "qualified")
            self.assertEqual(qualification["invocations"], 44)
            self.assertEqual(
                set(runner.calls[0]["env"]),
                set(MODULE.ENVIRONMENT_ALLOWLIST),
            )
            self.assertNotIn("HOME", runner.calls[0]["env"])
            self.assertTrue(all(call["env"]["BIFROST_CACHE_ROOT"] == str(output / "cache") for call in runner.calls))
            self.assertEqual(len({str(call["cwd"]) for call in runner.calls}), 44)

    def test_wrong_tool_hash_rejects_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "bifrost"
            binary.write_bytes(b"wrong binary")
            output = root / "capture"
            with self.assertRaisesRegex(MODULE.QualificationError, "wrong Bifrost binary"):
                MODULE.capture(binary, output, root=root, runner=lambda **_: 0)
            self.assertFalse(output.exists())

    def test_nonempty_catalog_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalog.json"
            path.write_text(json.dumps({"schema_version": 2, "packs": [{"id": "private"}]}), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.QualificationError, "packs=\[\]"):
                MODULE._validate_catalog(path)

    def test_native_no_rules_requires_exact_typed_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid_path = root / "valid.json"
            valid_path.write_text(json.dumps(native_report()), encoding="utf-8")
            self.assertEqual(
                MODULE._validate_native_report(valid_path)["interpretation"],
                "confirmed-no-rules-evaluated",
            )
            for label, changes, message in (
                ("status", {"status": "evaluated"}, "status is not not-evaluated"),
                ("reason", {"reason": "empty-selection"}, "reason is not no-active-rule-packs"),
                ("findings", {"findings": [{"id": "unexpected"}]}, "findings are not empty"),
            ):
                document = native_report()
                document.update(changes)
                path = root / f"invalid-{label}.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaisesRegex(MODULE.QualificationError, message):
                    MODULE._validate_native_report(path)

    def test_incomplete_and_absent_evidence_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            incomplete = report("python", 0)
            incomplete["runs"][0]["completion"] = {"type": "inconclusive", "reasons": ["partial_discovery"]}
            incomplete_path = root / "incomplete.json"
            incomplete_path.write_text(json.dumps(incomplete), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.QualificationError, "incomplete"):
                MODULE._validate_policy_report(incomplete_path, language="python", expected_findings=0)

            absent = report("python", 1)
            absent["runs"][0]["findings"][0].pop("evidence")
            absent_path = root / "absent.json"
            absent_path.write_text(json.dumps(absent), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.QualificationError, "no retained taint evidence"):
                MODULE._validate_policy_report(absent_path, language="python", expected_findings=1)

    def test_timeout_kills_process_group_and_returns_without_retry(self) -> None:
        calls: list[tuple[int, int]] = []

        class MockProcess:
            pid = 41

            def __init__(self):
                self.wait_calls = 0

            def wait(self, timeout=None):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise MODULE.subprocess.TimeoutExpired("mock", timeout)
                return -signal.SIGKILL

        process = MockProcess()
        with patch.object(MODULE.subprocess, "Popen", return_value=process) as popen, \
             patch.object(MODULE.os, "killpg", side_effect=lambda pid, sig: calls.append((pid, sig))):
            with tempfile.TemporaryDirectory() as temporary:
                result = MODULE._run_bounded(
                    ["mock"], cwd=Path(temporary), stdout=None, stderr=None,
                    env={"PATH": "/mock"}, timeout=1,
                )
        self.assertEqual(result, 124)
        self.assertEqual(popen.call_args.kwargs["start_new_session"], True)
        self.assertEqual(calls, [(41, signal.SIGTERM), (41, signal.SIGKILL)])
        self.assertEqual(process.wait_calls, 3)


if __name__ == "__main__":
    unittest.main()
