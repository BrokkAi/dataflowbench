#!/usr/bin/env python3
"""Mocked, lightweight tests for ``validate-swift-fixtures.py``.

These tests deliberately do not invoke Swift, Xcode, xcrun, or a fixture
compile.  They exercise fail-closed pin witnessing, evidence-directory
ownership, command evidence retention, convention inspection, instrumentation,
and the positive/negative control rule through temporary files and mocks.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("validate-swift-fixtures.py")
SPEC = importlib.util.spec_from_file_location("validate_swift_fixtures", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fake_witness_runner(outputs):
    def run(argv, *, evidence, env=None, cwd=None, timeout=None):
        key = tuple(argv)
        for predicate, result in outputs:
            if predicate(key):
                return MODULE.CommandResult(key, result[0], result[1], result[2])
        raise AssertionError(f"unmocked command: {key}")

    return run


class SwiftFixtureValidatorTests(unittest.TestCase):
    def make_evidence(self, directory: Path):
        return MODULE.Evidence(MODULE.create_evidence_directory(None, directory))

    def test_existing_evidence_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "run"
            path.mkdir()
            with self.assertRaisesRegex(MODULE.ValidationError, "already exists"):
                MODULE.create_evidence_directory(path, Path(temporary))

    def test_command_failure_retains_raw_result_with_mocked_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.make_evidence(Path(temporary))
            completed = mock.Mock(returncode=17, stdout="out\n", stderr="err\n")
            with mock.patch.object(MODULE.subprocess, "run", return_value=completed) as run:
                result = MODULE.run_command(
                    ["mock-swiftc", "-version"], evidence=evidence, env={"DFB_TEST": "1"}
                )
            run.assert_called_once()
            self.assertEqual(result.returncode, 17)
            record = evidence.data["commands"][-1]
            self.assertEqual(record["argv"], ["mock-swiftc", "-version"])
            self.assertEqual(record["env"], {"DFB_TEST": "1"})
            self.assertEqual(record["stdout"], "out\n")
            self.assertEqual(record["stderr"], "err\n")
            self.assertEqual(record["exit"], 17)

    def test_child_environment_allowlist_excludes_secrets_and_requires_ci_identity(self):
        with mock.patch.dict(
            MODULE.os.environ,
            {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "GITHUB_ACTIONS": "true",
                "GITHUB_SHA": "abc",
                "GITHUB_WORKFLOW": "Swift",
                "GITHUB_RUN_ID": "1",
                "GITHUB_RUN_ATTEMPT": "2",
                "ImageOS": "macos-27",
                "ImageVersion": "20260922.1",
                "SECRET_TOKEN": "must-not-be-copied",
            },
            clear=True,
        ):
            environment = MODULE.child_environment("github-xcode27")
        self.assertEqual(environment["GITHUB_SHA"], "abc")
        self.assertEqual(environment["ImageOS"], "macos-27")
        self.assertNotIn("SECRET_TOKEN", environment)

    def test_pin_mismatch_fails_before_fixture_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self.make_evidence(Path(temporary))
            compiler = Path(temporary) / "swiftc"
            compiler.write_bytes(b"mock compiler")
            exact = {
                "swift": ("Apple Swift version 6.4 (swiftlang-6.4.0.34.1 clang-2100.3.34.1)\n" "swift-driver version: 1.168.6\n", "", 0),
                "xcode": ("Xcode 27.0\nBuild version WRONG\n", "", 0),
                "swvers": ("ProductName:\tmacOS\nProductVersion:\t27.0\nBuildVersion:\t26A428\n", "", 0),
                "arch": ("arm64\n", "", 0),
                "sdkpath": (temporary + "/MacOSX.sdk\n", "", 0),
                "sdkversion": ("27.0\n", "", 0),
                "sdkbuild": ("26A425\n", "", 0),
                "target": (json.dumps({"target": {"triple": MODULE.EXPECTED_TARGET}}), "", 0),
            }
            Path(temporary, "MacOSX.sdk").mkdir()
            runner = fake_witness_runner(
                [
                    (lambda argv: argv[-1:] == ("--version",), exact["swift"]),
                    (lambda argv: argv[0] == "xcodebuild", exact["xcode"]),
                    (lambda argv: argv[0] == "sw_vers", exact["swvers"]),
                    (lambda argv: argv[0] == "uname", exact["arch"]),
                    (lambda argv: argv[-1:] == ("--show-sdk-path",), exact["sdkpath"]),
                    (lambda argv: argv[-1:] == ("--show-sdk-version",), exact["sdkversion"]),
                    (lambda argv: argv[-1:] == ("--show-sdk-build-version",), exact["sdkbuild"]),
                    (lambda argv: argv[-1:] == ("-print-target-info",), exact["target"]),
                ]
            )
            with self.assertRaisesRegex(MODULE.ValidationError, "xcodebuild -version"):
                MODULE.witness_environment(
                    str(compiler),
                    evidence,
                    profile="local",
                    child_env={"PATH": "/usr/bin", "HOME": temporary},
                    runner=runner,
                    command_paths={
                        "xcodebuild": "xcodebuild",
                        "sw_vers": "sw_vers",
                        "xcrun": "xcrun",
                        "uname": "uname",
                    },
                )
            self.assertNotIn("inventory", evidence.data)

    def test_probe_convention_and_temporary_instrumentation(self):
        source = """func dfb_source() -> Int {\n    return 7 // DFB-SOURCE: source\n}\n\nfunc dfb_sink(_ value: Int) { }\n\nfunc main() {\n    dfb_sink(dfb_source()) // DFB-SINK: sink\n}\n"""
        contents = {"main.swift": source}
        convention = MODULE.inspect_probe_convention(contents)
        self.assertEqual(convention["source"]["value_line"], 2)
        self.assertEqual(convention["sink"]["line"], 5)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture_dir = root / "case"
            fixture_dir.mkdir()
            fixture = fixture_dir / "main.swift"
            fixture.write_text(source, encoding="utf-8")
            metadata = {"id": "dfb-taint-swift-one-hop-positive"}
            case = MODULE.SwiftCase(fixture_dir, metadata, "metadata", ("main.swift",), ())
            destination = root / "instrumented"
            result = MODULE.instrument_case(case, destination, 19)
            updated = (destination / "main.swift").read_text(encoding="utf-8")
            self.assertIn("return 19", updated)
            self.assertIn("print(value)", updated)
            self.assertTrue(result["differences"][0]["diff"])
            self.assertEqual(fixture.read_text(encoding="utf-8"), source)

    def test_one_line_numeric_source_and_print_sink_are_accepted(self):
        contents = {
            "helper.swift": "func dfb_source() -> Int { 7 }\nfunc dfb_sink(_ value: Int) { print(value) }\n"
        }
        convention = MODULE.inspect_probe_convention(contents)
        self.assertEqual(convention["source"]["value_line"], 1)
        self.assertEqual(convention["sink"]["line"], 2)

    def test_default_xcrun_resolution_keeps_driver_spelling_but_hashes_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "swift-frontend"
            target.write_bytes(b"actual xcode compiler")
            lexical = root / "swiftc"
            lexical.symlink_to(target)
            sdk = root / "MacOSX.sdk"
            sdk.mkdir()
            outputs = [
                (lambda argv: argv[0] == "xcrun" and argv[-2:] == ("--find", "swiftc"), (str(lexical) + "\n", "", 0)),
                (lambda argv: argv[-1:] == ("--version",), ("Apple Swift version 6.4 (swiftlang-6.4.0.34.1 clang-2100.3.34.1)\nswift-driver version: 1.168.6\n", "", 0)),
                (lambda argv: argv[0] == "xcodebuild", ("Xcode 27.0\nBuild version 27A266a\n", "", 0)),
                (lambda argv: argv[0] == "sw_vers", ("ProductName:\tmacOS\nProductVersion:\t27.0\nBuildVersion:\t26A428\n", "", 0)),
                (lambda argv: argv[0] == "uname", ("arm64\n", "", 0)),
                (lambda argv: argv[-1:] == ("--show-sdk-path",), (str(sdk) + "\n", "", 0)),
                (lambda argv: argv[-1:] == ("--show-sdk-version",), ("27.0\n", "", 0)),
                (lambda argv: argv[-1:] == ("--show-sdk-build-version",), ("26A425\n", "", 0)),
                (lambda argv: argv[-1:] == ("-print-target-info",), (json.dumps({"target": {"triple": MODULE.EXPECTED_TARGET}}), "", 0)),
            ]
            with tempfile.TemporaryDirectory() as evidence_root:
                evidence = MODULE.Evidence(MODULE.create_evidence_directory(None, Path(evidence_root)))
                witness = MODULE.witness_environment(
                    None,
                    evidence,
                    profile="local",
                    child_env={"PATH": "/usr/bin", "HOME": temporary},
                    runner=fake_witness_runner(outputs),
                    command_paths={"xcrun": "xcrun", "xcodebuild": "xcodebuild", "sw_vers": "sw_vers", "uname": "uname"},
                )
            self.assertEqual(witness["compiler_path"], str(lexical))
            self.assertEqual(witness["compiler_resolved_path"], str(target.resolve()))

    def test_controls_require_dependence_for_positive_and_independence_for_negative(self):
        check = MODULE.check_control_observation
        check("positive", {7: 7, 19: 19})
        check("negative", {7: 3, 19: 3})
        with self.assertRaises(MODULE.ValidationError):
            check("positive", {7: 7, 19: 7})
        with self.assertRaises(MODULE.ValidationError):
            check("negative", {7: 7, 19: 19})


if __name__ == "__main__":
    unittest.main()
