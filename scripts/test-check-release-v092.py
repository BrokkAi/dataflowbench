#!/usr/bin/env python3
"""Focused tests for fresh-report and typed-outcome verification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("check-release-v092.py")
SPEC = importlib.util.spec_from_file_location("check_release_v092_tested", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class FreshReportProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.attempt_id = "fixture-group-attempt-01-series-01"
        self.expected = {
            "path": "reports/releases/v0.9.2/normal/fixture-codeql-java-kernel.json",
            "source_path": "reports/raw/fixture-group/normal.json",
            "case_ids": ["case-a", "case-b", "case-c"],
            "tool": "codeql",
            "tool_version": "2.27.2",
        }
        outcomes = ["inconclusive", "unsupported", "runner-error"]
        self.original = {
            "schema_version": 1,
            "tool": "codeql",
            "tool_version": "2.27.2",
            "tool_build_identity": "codeql-build-fixture",
            "adapter_version": "0.1.0",
            "configuration_hash": "a" * 64,
            "fixture_revision": "sha256:" + "b" * 64,
            "started_at_unix_seconds": 10,
            "ended_at_unix_seconds": 20,
            "cold_or_warm": "cold",
            "results": [],
        }
        self.captured = {}
        mappings = []
        for ordinal, (case_id, outcome) in enumerate(zip(self.expected["case_ids"], outcomes)):
            relative = f"reports/raw/fixture-group/{case_id}.json"
            raw_data = json.dumps({"case_id": case_id, "outcome": outcome}).encode() + b"\n"
            captured_path = self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id / "capture" / relative
            captured_path.parent.mkdir(parents=True, exist_ok=True)
            captured_path.write_bytes(raw_data)
            digest = hashlib.sha256(raw_data).hexdigest()
            self.captured[relative] = {"sha256": digest, "bytes": len(raw_data)}
            mappings.append({
                "execution_relative": relative,
                "captured_path": f"reports/releases/v0.9.2/attempts/{self.attempt_id}/capture/{relative}",
                "sha256": digest,
                "bytes": len(raw_data),
            })
            self.original["results"].append({
                "case_id": case_id,
                "outcome": outcome,
                "source_anchors": ["Source"],
                "sink_anchors": ["Sink"],
                "witness_checkpoints": [],
                "diagnostics": ["typed state retained"],
                "duration_ms": ordinal,
                "raw_output": relative,
            })
        self.original_raw_outputs = {row["case_id"]: row["raw_output"] for row in self.original["results"]}

        output = self.root / "reports/raw/fixture-group/normal.json"
        output.parent.mkdir(parents=True)
        original_bytes = json.dumps(self.original, sort_keys=True).encode() + b"\n"
        output.write_bytes(original_bytes)
        source_relative = self.expected["source_path"]
        self.captured[source_relative] = {
            "sha256": hashlib.sha256(original_bytes).hexdigest(),
            "bytes": len(original_bytes),
        }
        self.original_path = self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id / "original" / self.expected["path"]
        self.original_path.parent.mkdir(parents=True, exist_ok=True)
        self.original_path.write_bytes(original_bytes)

        self.staged = json.loads(json.dumps(self.original))
        self.staged_path = self.root / "reports/releases/v0.9.2/normal/attempts" / self.attempt_id / "fixture-codeql-java-kernel.json"
        self.staged_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_staged()
        self.entry = {
            "source_path": self.expected["source_path"],
            "staged_path": "reports/releases/v0.9.2/normal/attempts/" + self.attempt_id + "/fixture-codeql-java-kernel.json",
            "original_path": "reports/releases/v0.9.2/attempts/" + self.attempt_id + "/original/" + self.expected["path"],
            "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
            "staged_sha256": hashlib.sha256(self.staged_path.read_bytes()).hexdigest(),
            "case_ids": self.expected["case_ids"],
            "tool": self.expected["tool"],
            "tool_version": self.expected["tool_version"],
            "raw_output_mappings": mappings,
        }

    def _write_staged(self) -> None:
        capture_prefix = f"reports/releases/v0.9.2/attempts/{self.attempt_id}/capture/"
        for row in self.staged["results"]:
            row["raw_output"] = capture_prefix + self.original_raw_outputs[row["case_id"]]
        self.staged_path.write_text(json.dumps(self.staged, sort_keys=True) + "\n")

    def test_incomplete_and_error_outcomes_survive_raw_path_projection(self):
        _, rows, outcomes, raw_by_case = checker._verify_report_projection(
            self.root,
            self.attempt_id,
            self.original["fixture_revision"],
            self.expected,
            self.entry,
            self.captured,
            "0.1.0",
        )
        self.assertEqual(rows, 3)
        self.assertEqual(outcomes, {"inconclusive": 1, "unsupported": 1, "runner-error": 1})
        self.assertEqual(set(raw_by_case), set(self.expected["case_ids"]))

    def test_outcome_cannot_be_flattened_during_staging(self):
        self.staged["results"][0]["outcome"] = "not-reached"
        self._write_staged()
        self.entry["staged_sha256"] = hashlib.sha256(self.staged_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(checker.EvidenceError, "changed report fields"):
            checker._verify_report_projection(
                self.root,
                self.attempt_id,
                self.original["fixture_revision"],
                self.expected,
                self.entry,
                self.captured,
                "0.1.0",
            )

    def test_report_rows_must_match_the_registered_partition_membership(self):
        self.expected["case_ids"][0] = "different-case"
        self.entry["case_ids"] = self.expected["case_ids"]
        with self.assertRaisesRegex(checker.EvidenceError, "case membership"):
            checker._verify_report_projection(
                self.root,
                self.attempt_id,
                self.original["fixture_revision"],
                self.expected,
                self.entry,
                self.captured,
                "0.1.0",
            )

    def test_report_rows_and_raw_mappings_must_be_a_bijection(self):
        self.original["results"][1]["raw_output"] = self.original["results"][0]["raw_output"]
        self.original_raw_outputs["case-b"] = self.original_raw_outputs["case-a"]
        original_bytes = json.dumps(self.original, sort_keys=True).encode() + b"\n"
        source = self.root / self.expected["source_path"]
        source.write_bytes(original_bytes)
        self.captured[self.expected["source_path"]] = {
            "sha256": hashlib.sha256(original_bytes).hexdigest(),
            "bytes": len(original_bytes),
        }
        self.original_path.write_bytes(original_bytes)
        self.entry["original_sha256"] = hashlib.sha256(original_bytes).hexdigest()
        self.staged = json.loads(json.dumps(self.original))
        self._write_staged()
        self.entry["staged_sha256"] = hashlib.sha256(self.staged_path.read_bytes()).hexdigest()

        with self.assertRaisesRegex(checker.EvidenceError, "reuse one raw-output mapping"):
            checker._verify_report_projection(
                self.root,
                self.attempt_id,
                self.original["fixture_revision"],
                self.expected,
                self.entry,
                self.captured,
                "0.1.0",
            )


class ExactBuildIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.validated = self._fixture_bindings()

    @staticmethod
    def _sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _write_runtime_manifest(self, root: Path, manifest_path: Path) -> dict:
        files = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append({
                    "path": path.relative_to(root).as_posix(),
                    "sha256": self._sha(path.read_bytes()),
                    "mode": 0o644,
                })
        manifest = {
            "schema_version": 1,
            "root": str(root),
            "files": files,
            "symlinks": [],
            "external_files": [],
        }
        raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
        manifest_path.write_bytes(raw)
        return {"path": str(manifest_path), "sha256": self._sha(raw), "kind": "runtime-tree-manifest"}

    def _fixture_bindings(self) -> dict:
        d = lambda digit: digit * 64
        codeql_root = self.root / "codeql-packs"
        for language, version in checker.CODEQL_NATIVE_PACKS.items():
            qlpack = codeql_root / f"codeql/{language}-queries/{version}/qlpack.yml"
            qlpack.parent.mkdir(parents=True, exist_ok=True)
            qlpack.write_text(
                f"---\nname: codeql/{language}-queries\nversion: {version}\n", encoding="utf-8",
            )
        codeql_manifest = self._write_runtime_manifest(
            codeql_root, self.root / "codeql-packs-runtime.json",
        )

        pysa_root = self.root / "pysa-env"
        pyre = pysa_root / "bin/pyre"
        pyre.parent.mkdir(parents=True)
        pyre.write_bytes(b"bound pyre client\n")
        suite = pysa_root / "lib/pyre_check/taint"
        (suite / "common").mkdir(parents=True)
        (suite / "core_privacy_security").mkdir(parents=True)
        (suite / "common/taint.config").write_bytes(b"common suite\n")
        (suite / "core_privacy_security/model.pysa").write_bytes(b"security suite\n")
        pysa_manifest = self._write_runtime_manifest(
            pysa_root, self.root / "pysa-runtime.json",
        )

        d8_identity = f"{checker.D8_VERSION_LINE}; r8 jar sha256:{checker.D8_JAR_SHA256}"
        return {
            "tools": {
                "bifrost": {"version": "0.13.1", "report_version": "bifrost 0.13.1",
                            "sha256": d("1"), "build_identity": "271a0bd840372a1ce6e6e11fc60a788e997ed353"},
                "codeql": {"version": "2.27.2", "report_version": "2.27.2",
                           "sha256": d("2"), "build_identity": checker.CODEQL_CLI_BUILD_SHA},
                "codeql-packs": codeql_manifest,
                "joern": {"version": "4.0.660", "report_version": "4.0.660", "sha256": d("3")},
                "semgrep": {"version": "1.181.0", "report_version": "1.181.0", "sha256": d("4")},
                "infer": {"version": "v1.3.0", "report_version": "v1.3.0", "sha256": d("5")},
                "flowdroid": {"version": "2.15.1", "report_version": "2.15.1",
                              "sha256": checker.FLOWDROID_JAR_SHA256},
                "android-platform": {"sha256": checker.ANDROID_PLATFORM_SHA256},
                "d8": {"sha256": checker.D8_JAR_SHA256, "build_identity": d8_identity},
                "opentaint": {"version": "v0.4.6", "report_version": "v0.4.6",
                              "sha256": checker.OPENTAINT_JAR_SHA256},
                "opentaint-models": {"sha256": checker.OPENTAINT_MODELS_SHA256},
                "pysa": {"path": str(pyre), "version": "0.10.0",
                         "report_version": "0.10.0", "sha256": d("a")},
                "pysa-runtime": pysa_manifest,
                "pyre.bin": {"sha256": d("b")},
                "pyrefly": {"version": "1.4.0", "sha256": d("c")},
            },
            "tool_components": {
                "codeql": ["codeql-packs"],
                "pysa": ["pyre.bin", "pyrefly", "pysa-runtime"],
            },
            "codeql_packs": {"component": "codeql-packs"},
            "source_inputs": [{
                "path": checker.D8_VERSION_WITNESS_PATH,
                "sha256": checker.D8_VERSION_WITNESS_SHA256,
            }],
        }

    def _expected(self, tool: str, group_id: str | None = None) -> str:
        group = {"tool": tool, "identity_components": ["d8"] if tool == "flowdroid" else []}
        if group_id is not None:
            group["id"] = group_id
        version = checker.EXPECTED_TOOL_VERSIONS[tool]
        return checker._expected_report_build_identity(
            group, {"tool_version": version}, self.validated,
        )

    def test_each_analyzer_identity_is_derived_from_its_exact_bindings(self):
        d = lambda digit: digit * 64
        flowdroid_base = (
            f"soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:{checker.FLOWDROID_JAR_SHA256}; "
            f"android-34 platform android.jar sha256:{checker.ANDROID_PLATFORM_SHA256}"
        )
        examples = [
            ("bifrost", "bifrost 0.13.1", "271a0bd840372a1ce6e6e11fc60a788e997ed353"),
            ("codeql", "2.27.2", f"codeql-cli:{checker.CODEQL_CLI_BUILD_SHA}"),
            ("joern", "4.0.660", "joern-cli:4.0.660"),
            ("semgrep", "1.181.0", "semgrep-oss:1.181.0"),
            ("infer", "v1.3.0", f"infer:v1.3.0 bin-sha256:{d('5')}"),
            ("flowdroid", "2.15.1", f"{flowdroid_base}; dexed by {self.validated['tools']['d8']['build_identity']}"),
            ("opentaint", "v0.4.6", f"opentaint-project-analyzer.jar sha256:{checker.OPENTAINT_JAR_SHA256}; opentaint-models.tar.gz sha256:{checker.OPENTAINT_MODELS_SHA256}"),
            ("pysa", "0.10.0", f"pyre-check:0.10.0 pyre.bin-sha256:{d('b')} pyrefly:1.4.0 pyrefly-sha256:{d('c')}"),
        ]
        for tool, version, expected in examples:
            with self.subTest(tool=tool):
                actual = checker._expected_report_build_identity(
                    {"tool": tool,
                     "identity_components": ["d8"] if tool == "flowdroid" else [],
                     "id": "flowdroid-java-kernel" if tool == "flowdroid" else f"{tool}-java-kernel"},
                    {"tool_version": version}, self.validated,
                )
                self.assertEqual(actual, expected)

    def test_native_identities_cover_every_registered_profile_and_language(self):
        profiles = [
            ("bifrost", "java"), ("bifrost", "javascript"), ("bifrost", "python"),
            ("codeql", "java"), ("codeql", "javascript"), ("codeql", "python"),
            ("flowdroid", "java"), ("infer", "java"),
            ("joern", "java"), ("joern", "javascript"), ("joern", "python"),
            ("opentaint", "java"), ("pysa", "python"),
            ("semgrep", "java"), ("semgrep", "javascript"), ("semgrep", "python"),
        ]
        self.assertEqual(len(profiles), 16)
        for tool, language in profiles:
            group_id = f"{tool}-{language}-native"
            expected = checker._expected_report_build_identity(
                {"tool": tool, "id": group_id,
                 "identity_components": ["d8"] if tool == "flowdroid" else []},
                {"tool_version": checker.EXPECTED_TOOL_VERSIONS[tool]},
                self.validated,
            )
            with self.subTest(group=group_id):
                checker._verify_report_build_identity(
                    {"tool": tool, "id": group_id,
                     "identity_components": ["d8"] if tool == "flowdroid" else []},
                    {"tool_version": checker.EXPECTED_TOOL_VERSIONS[tool],
                     "tool_build_identity": expected}, self.validated,
                )
                with self.assertRaisesRegex(checker.EvidenceError, "build identity"):
                    checker._verify_report_build_identity(
                        {"tool": tool, "id": group_id,
                         "identity_components": ["d8"] if tool == "flowdroid" else []},
                        {"tool_version": checker.EXPECTED_TOOL_VERSIONS[tool],
                         "tool_build_identity": expected + "x"}, self.validated,
                    )
                with self.assertRaisesRegex(checker.EvidenceError, "profile pin"):
                    checker._verify_report_build_identity(
                        {"tool": tool, "id": group_id,
                         "identity_components": ["d8"] if tool == "flowdroid" else []},
                        {"tool_version": "unexpected-version", "tool_build_identity": expected},
                        self.validated,
                    )

    def test_flowdroid_d8_suffix_is_exact_for_kernel_and_modeling_but_absent_from_native(self):
        base = (
            f"soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:{checker.FLOWDROID_JAR_SHA256}; "
            f"android-34 platform android.jar sha256:{checker.ANDROID_PLATFORM_SHA256}"
        )
        d8 = self.validated["tools"]["d8"]["build_identity"]
        for group_id in ("flowdroid-java-kernel", "flowdroid-java-modeling", "flowdroid-kotlin-kernel"):
            with self.subTest(group=group_id):
                self.assertEqual(self._expected("flowdroid", group_id), f"{base}; dexed by {d8}")
        native = self._expected("flowdroid", "flowdroid-java-native")
        self.assertEqual(native, (
            f"{base} — FlowDroid 2.15.1 shipped SourcesAndSinks.txt catalog "
            "(extracted verbatim from the pinned soot-infoflow-cmd jar) and default summariesManual taint wrapper"
        ))
        self.assertNotIn("dexed by", native)

    def test_flowdroid_requires_the_witnessed_d8_binding_and_identity_component(self):
        group = {"tool": "flowdroid", "id": "flowdroid-java-kernel",
                 "identity_components": ["d8"]}
        report = {"tool_version": "2.15.1"}
        wrong_version = json.loads(json.dumps(self.validated))
        wrong_version["tools"]["d8"]["build_identity"] = (
            checker.D8_VERSION_LINE.replace("8.5.35", "8.5.34") +
            f"; r8 jar sha256:{checker.D8_JAR_SHA256}"
        )
        with self.assertRaisesRegex(checker.EvidenceError, "exact version witness"):
            checker._expected_report_build_identity(group, report, wrong_version)

        wrong_digest = json.loads(json.dumps(self.validated))
        wrong_digest["tools"]["d8"]["sha256"] = "9" * 64
        with self.assertRaisesRegex(checker.EvidenceError, "JAR SHA-256"):
            checker._expected_report_build_identity(group, report, wrong_digest)

        wrong_witness = json.loads(json.dumps(self.validated))
        wrong_witness["source_inputs"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(checker.EvidenceError, "witness is not bound"):
            checker._expected_report_build_identity(group, report, wrong_witness)

        without_component = {"tool": "flowdroid", "id": "flowdroid-java-kernel",
                             "identity_components": []}
        with self.assertRaisesRegex(checker.EvidenceError, "not included in this group identity"):
            checker._expected_report_build_identity(without_component, report, self.validated)

    def test_native_report_rejects_near_miss_version_suffix_and_digest(self):
        group = {"tool": "opentaint", "id": "opentaint-java-native", "identity_components": []}
        version = checker.EXPECTED_TOOL_VERSIONS["opentaint"]
        expected = self._expected("opentaint", group["id"])
        for mutated in (expected + "x", expected.replace("v0.4.6", "v0.4.5")):
            with self.subTest(mutated=mutated[-32:]):
                with self.assertRaisesRegex(checker.EvidenceError, "build identity"):
                    checker._verify_report_build_identity(
                        group, {"tool_version": version, "tool_build_identity": mutated}, self.validated,
                    )

        broken_assets = json.loads(json.dumps(self.validated))
        broken_assets["tools"]["opentaint-models"]["sha256"] = "9" * 64
        with self.assertRaisesRegex(checker.EvidenceError, "release-asset digest"):
            checker._expected_report_build_identity(group, {"tool_version": version}, broken_assets)

        with self.assertRaisesRegex(checker.EvidenceError, "profile pin"):
            checker._expected_report_build_identity(group, {"tool_version": "v0.4.5"}, self.validated)

    def test_codeql_native_identity_requires_exact_bound_query_pack_metadata(self):
        group = {"tool": "codeql", "id": "codeql-java-native", "identity_components": []}
        expected = self._expected("codeql", group["id"])
        self.assertIn("codeql/java-queries@1.11.12:codeql-suites/java-security-extended.qls", expected)
        nested = (self.root / "codeql-packs/codeql/java-queries/1.11.12/.codeql/libraries/"
                  "codeql/java-all/4.0.4/qlpack.yml")
        nested.parent.mkdir(parents=True)
        nested.write_text("---\nname: codeql/java-all\nversion: 4.0.4\n", encoding="utf-8")
        self.validated["tools"]["codeql-packs"] = self._write_runtime_manifest(
            self.root / "codeql-packs", self.root / "codeql-packs-runtime.json",
        )
        # The root pack remains the only direct qlpack.yml at the exact
        # package/version path; nested dependency metadata is part of its
        # closure, not a competing native suite identity.
        self.assertEqual(self._expected("codeql", group["id"]), expected)

        qlpack = self.root / "codeql-packs/codeql/java-queries/1.11.12/qlpack.yml"
        qlpack.write_text("---\nname: codeql/java-queries\nversion: 1.11.13\n", encoding="utf-8")
        self.validated["tools"]["codeql-packs"] = self._write_runtime_manifest(
            self.root / "codeql-packs", self.root / "codeql-packs-runtime.json",
        )
        with self.assertRaisesRegex(checker.EvidenceError, "metadata disagrees"):
            self._expected("codeql", group["id"])

    def test_codeql_native_identity_rejects_an_alternate_direct_pack_version(self):
        group = {"tool": "codeql", "id": "codeql-java-native", "identity_components": []}
        alternate = self.root / "codeql-packs/codeql/java-queries/1.11.13/qlpack.yml"
        alternate.parent.mkdir(parents=True)
        alternate.write_text("---\nname: codeql/java-queries\nversion: 1.11.13\n", encoding="utf-8")
        self.validated["tools"]["codeql-packs"] = self._write_runtime_manifest(
            self.root / "codeql-packs", self.root / "codeql-packs-runtime.json",
        )
        with self.assertRaisesRegex(checker.EvidenceError, "does not bind exactly"):
            self._expected("codeql", group["id"])

    def test_pysa_native_identity_binds_the_exact_suite_digest(self):
        group = {"tool": "pysa", "id": "pysa-python-native", "identity_components": []}
        expected = self._expected("pysa", group["id"])
        suite_digest = checker._pysa_native_suite_sha256(self.validated["tools"], self.validated)
        self.assertIn(f"(suite-sha256:{suite_digest})", expected)
        report = {
            "tool_version": "0.10.0",
            "tool_build_identity": expected.replace(suite_digest, "0" * 64),
        }
        with self.assertRaisesRegex(checker.EvidenceError, "build identity"):
            checker._verify_report_build_identity(group, report, self.validated)

        suite_file = self.root / "pysa-env/lib/pyre_check/taint/common/taint.config"
        suite_file.write_bytes(b"changed after binding\n")
        with self.assertRaisesRegex(checker.EvidenceError, "differs from its runtime-tree manifest"):
            checker._expected_report_build_identity(
                group, {"tool_version": "0.10.0"}, self.validated,
            )

    def test_codeql_identity_requires_the_bound_cli_build_sha(self):
        validated = {"tools": {"codeql": {"version": "2.27.2", "sha256": "a" * 64,
                                             "build_identity": "0" * 40}}}
        with self.assertRaisesRegex(checker.EvidenceError, "CLI build SHA"):
            checker._expected_report_build_identity(
                {"tool": "codeql"}, {"tool_version": "2.27.2"}, validated,
            )


class RetrySelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_commit = "f" * 40
        self.plan_commit = "a" * 40
        self.contract_sha256 = "b" * 64
        groups = [
            {"id": f"group-{index:03d}", "tool": "bifrost", "case_ids": [f"case-{index:03d}"],
             "maximum_attempts": 2}
            for index in range(checker.EXPECTED_GROUPS)
        ]
        self.plan = {
            "execution_series": 7,
            "source_commit": self.source_commit,
            "groups": groups,
        }
        self.rows = []
        for index, group in enumerate(groups):
            if index == 0:
                self.rows.append(self._row(group, 1, "failed"))
                self.rows.append(self._row(group, 2, "completed"))
            else:
                self.rows.append(self._row(group, 1, "completed"))

    def _row(self, group, number, status):
        return {
            "group_id": group["id"],
            "attempt_id": f"{group['id']}-attempt-{number:02d}-series-07",
            "execution_series": 7,
            "plan_commit": self.plan_commit,
            "source_commit": self.source_commit,
            "contract_sha256": self.contract_sha256,
            "tool": group["tool"],
            "case_ids": group["case_ids"],
            "status": status,
        }

    def _select(self):
        ledger = [(row, hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest())
                  for row in self.rows]
        return checker._select_attempts(self.plan, self.contract_sha256, ledger)

    def test_selects_one_completed_attempt_and_retains_prior_failure(self):
        plan_commit, selected, failures = self._select()
        self.assertEqual(plan_commit, self.plan_commit)
        self.assertEqual(len(selected), checker.EXPECTED_GROUPS)
        self.assertEqual(selected["group-000"][2], 2)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0]["status"], "failed")

    def test_rejects_two_completed_attempts_for_one_group(self):
        self.rows[0]["status"] = "completed"
        self.rows[1]["status"] = "completed"
        with self.assertRaisesRegex(checker.EvidenceError, "exactly one completed attempt"):
            self._select()

    def test_rejects_attempt_number_above_the_two_attempt_cap(self):
        group = self.plan["groups"][0]
        self.rows[0] = self._row(group, 1, "failed")
        self.rows[1] = self._row(group, 2, "failed")
        self.rows.insert(2, self._row(group, 3, "completed"))
        with self.assertRaisesRegex(checker.EvidenceError, "attempt number or series"):
            self._select()

    def test_rejects_wrong_contract_source_series_and_unknown_group(self):
        mutations = (
            ("contract_sha256", "c" * 64),
            ("source_commit", "e" * 40),
            ("plan_commit", "d" * 40),
            ("execution_series", 8),
            ("group_id", "unknown-group"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                original = self.rows[0][field]
                self.rows[0][field] = value
                with self.assertRaises(checker.EvidenceError):
                    self._select()
                self.rows[0][field] = original

    def test_rejects_an_attempt_after_a_completed_attempt(self):
        group = self.plan["groups"][0]
        self.rows[0] = self._row(group, 1, "completed")
        self.rows[1] = self._row(group, 2, "failed")
        with self.assertRaisesRegex(checker.EvidenceError, "appears after its completed attempt"):
            self._select()

    def test_wall_budget_includes_time_between_attempts(self):
        rows = [
            ({"start_utc": "2026-10-20T10:00:00+00:00", "end_utc": "2026-10-20T10:00:10+00:00"}, "a" * 64),
            ({"start_utc": "2026-10-20T10:30:00+00:00", "end_utc": "2026-10-20T10:30:10+00:00"}, "b" * 64),
        ]
        self.assertEqual(checker._validate_wall_budget(rows, 2000), 1810)
        with self.assertRaisesRegex(checker.EvidenceError, "including pauses"):
            checker._validate_wall_budget(rows, 1800)


class FailedStagingInventoryTests(unittest.TestCase):
    def test_global_staging_inventory_keeps_recorder_leftovers_separate_from_selected_reports(self):
        selected = {"reports/releases/v0.9.2/normal/attempts/selected/report.json"}
        failures = [{"failed_staging_artifacts": [
            {"path": "reports/releases/v0.9.2/attempts/failed/original/report.json"},
            {"path": "reports/releases/v0.9.2/normal/attempts/failed/partial.json"},
        ]}]
        self.assertEqual(
            checker._expected_staged_files(selected, failures),
            {"selected/report.json", "failed/partial.json"},
        )

    def test_failed_staged_artifact_cannot_overlap_a_selected_report(self):
        path = "reports/releases/v0.9.2/normal/attempts/selected/report.json"
        with self.assertRaisesRegex(checker.EvidenceError, "overlap selected"):
            checker._expected_staged_files(
                {path}, [{"failed_staging_artifacts": [{"path": path}]}],
            )


class FailedAttemptReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.group_id = "bifrost-test-group"
        self.attempt_number = 1
        self.series = 7
        self.attempt_id = f"{self.group_id}-attempt-01-series-07"
        self.source_commit = "f" * 40
        self.plan_commit = "a" * 40
        self.contract_sha256 = "b" * 64
        self.fixture_revision = "sha256:" + "c" * 64
        self.group = {
            "id": self.group_id,
            "tool": "bifrost",
            "identity_components": [],
            "swift_plan": None,
            "joern_plan": None,
            "qualification": None,
            "source_inputs": [],
            "environment": {"PATH": "/usr/bin"},
            "argv": ["bifrost", "run"],
            "output_roots": ["out"],
            "case_ids": ["case-1"],
            "deadline_seconds": 90,
        }
        self.plan = {
            "execution_series": self.series,
            "source_commit": self.source_commit,
            "runner_source_sha256": "d" * 64,
            "population": {"path": "populations/v0.9.0.json", "sha256": "e" * 64},
        }
        self.binding = {
            "path": "/tools/bifrost",
            "sha256": "1" * 64,
            "version": "0.13.1",
            "report_version": "bifrost 0.13.1",
            "build_identity": "271a0bd840372a1ce6e6e11fc60a788e997ed353",
        }
        self.validated = {
            "plan": self.plan,
            "bytes_sha256": self.contract_sha256,
            "fixture_revision": self.fixture_revision,
            "tools": {"bifrost": self.binding},
            "qualification": {"bifrost": {"status": "qualified", "groups": [self.group_id]}},
            "source_inputs": [],
        }
        execution = (self.root / "execution-state/v092/groups" /
                     f"series-{self.series:02d}" / self.group_id / "attempt-01")
        cache = (self.root / "execution-state/v092/cache" /
                 f"series-{self.series:02d}" / self.group_id / "attempt-01")
        attempt = self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id
        environment = checker.EXECUTOR._child_environment(self.group, execution, attempt, cache)
        self.expected_fields = {
            "execution_series": self.series,
            "group_id": self.group_id,
            "attempt_id": self.attempt_id,
            "source_commit": self.source_commit,
            "plan_commit": self.plan_commit,
            "contract_sha256": self.contract_sha256,
            "runner_source_sha256": self.plan["runner_source_sha256"],
            "fixture_revision": self.fixture_revision,
            "population": self.plan["population"],
            "tool": self.group["tool"],
            "tool_binding": self.binding,
            "identity_components": [],
            "swift_plan": None,
            "joern_plan": None,
            "qualification": self.validated["qualification"]["bifrost"],
            "source_inputs": [],
            "cache_root": str(cache),
            "argv": self.group["argv"],
            "environment": environment,
            "execution_root": str(execution),
            "output_roots": self.group["output_roots"],
            "case_ids": self.group["case_ids"],
            "deadline_seconds": self.group["deadline_seconds"],
            "started_receipt": "started.json",
        }
        attempt.mkdir(parents=True)
        self.started = {
            "schema_version": 1,
            "release": checker.RELEASE,
            "status": "started",
            "start_utc": "2026-10-20T10:00:00+00:00",
            "end_utc": None,
            **self.expected_fields,
        }
        (attempt / "started.json").write_text(json.dumps(self.started, sort_keys=True) + "\n")
        self.receipt = {
            **self.started,
            "status": "failed",
            "end_utc": "2026-10-20T10:00:01+00:00",
            "exit_code": 2,
            "timed_out": False,
            "capacity_loss": None,
            "duration_seconds": 1.0,
            "captured_files": [],
            "reports": [],
            "process_ownership": {
                "schema": "invocation-process-ownership/v1",
                "root_pid": 4101,
                "tracked_processes": [{"pid": 4101, "start_identity": "100:200"}],
                "signals_sent": [],
                "cleanup_status": "tracked-processes-stopped",
                "descendant_containment": "unproven",
                "tracking_interval_seconds": 2.0,
            },
        }
        for stream in ("stdout", "stderr"):
            (attempt / f"{stream}.txt").write_bytes(b"")
            self.receipt[stream] = {
                "path": f"{stream}.txt",
                "sha256": hashlib.sha256(b"").hexdigest(),
                "bytes": 0,
            }
        (attempt / "completed.json").write_text(json.dumps(self.receipt, sort_keys=True) + "\n")

    def test_failure_is_bound_and_hashed_as_nonselected_evidence(self):
        result = checker._verify_failed_attempt(
            self.root, self.validated, self.group, self.receipt,
            self.plan_commit, self.attempt_number, "9" * 64,
        )
        self.assertEqual(result["attempt_id"], self.attempt_id)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["completed_receipt_sha256"],
                         hashlib.sha256((self.root / "reports/releases/v0.9.2/attempts" /
                                         self.attempt_id / "completed.json").read_bytes()).hexdigest())

    def test_failed_attempt_requires_process_ownership_receipt(self):
        receipt = dict(self.receipt)
        receipt.pop("process_ownership")
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        with self.assertRaisesRegex(checker.EvidenceError, "lacks process ownership"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, receipt,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

    def test_failed_attempt_process_ownership_keeps_typed_uncertainty(self):
        receipt = json.loads(json.dumps(self.receipt))
        receipt["process_ownership"].update({
            "cleanup_status": "uncertain",
            "cleanup_error": "ReleaseError: tracked invocation processes remain alive",
        })
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        result = checker._verify_failed_attempt(
            self.root, self.validated, self.group, receipt,
            self.plan_commit, self.attempt_number, "9" * 64,
        )
        self.assertEqual(result["status"], "failed")

    def test_process_ownership_rejects_duplicate_or_mismatched_pid_identity(self):
        ownership = json.loads(json.dumps(self.receipt["process_ownership"]))
        ownership["tracked_processes"].append(dict(ownership["tracked_processes"][0]))
        with self.assertRaisesRegex(checker.EvidenceError, "duplicate tracked PID"):
            checker._verify_process_ownership("fixture", "failed", ownership, required=True)

        ownership = json.loads(json.dumps(self.receipt["process_ownership"]))
        ownership["signals_sent"] = [
            {"pid": 4101, "start_identity": "old-process", "signal": "SIGTERM"}
        ]
        with self.assertRaisesRegex(checker.EvidenceError, "does not bind an exact tracked PID identity"):
            checker._verify_process_ownership("fixture", "failed", ownership, required=True)

    def test_process_ownership_rejects_completed_uncertainty_and_unproven_success(self):
        ownership = json.loads(json.dumps(self.receipt["process_ownership"]))
        ownership["cleanup_status"] = "uncertain"
        ownership["cleanup_error"] = "cleanup failed"
        with self.assertRaisesRegex(checker.EvidenceError, "completed attempt lacks confirmed"):
            checker._verify_process_ownership("fixture", "completed", ownership, required=True)

        ownership = json.loads(json.dumps(self.receipt["process_ownership"]))
        ownership["descendant_containment"] = "contained"
        with self.assertRaisesRegex(checker.EvidenceError, "overstates descendant containment"):
            checker._verify_process_ownership("fixture", "completed", ownership, required=True)

    def test_capacity_loss_before_launch_has_explicit_not_started_ownership(self):
        ownership = {
            "schema": "invocation-process-ownership/v1",
            "root_pid": None,
            "tracked_processes": [],
            "signals_sent": [],
            "cleanup_status": "not-started",
            "descendant_containment": "unproven",
            "tracking_interval_seconds": 2.0,
        }
        checker._verify_process_ownership("fixture", "capacity-lost", ownership, required=True)
        with self.assertRaisesRegex(checker.EvidenceError, "valid only for capacity loss"):
            checker._verify_process_ownership("fixture", "failed", ownership, required=True)

    def test_failed_attempt_with_report_artifacts_is_rejected(self):
        staged = self.root / "reports/releases/v0.9.2/normal/attempts" / self.attempt_id / "report.json"
        staged.parent.mkdir(parents=True)
        staged.write_text("{}\n")
        with self.assertRaisesRegex(checker.EvidenceError, "failed staged files differ"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, self.receipt,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

    def _recorder_error_with_partial_staging(self):
        attempt = self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id
        original = attempt / "original/reports/raw/fixture/report.json"
        staged = (self.root / "reports/releases/v0.9.2/normal/attempts" /
                  self.attempt_id / "fixture-report.json")
        original.parent.mkdir(parents=True)
        staged.parent.mkdir(parents=True)
        original_data = b'{"partial":"original"}\n'
        staged_data = b'{"partial":"staged"}\n'
        original.write_bytes(original_data)
        staged.write_bytes(staged_data)
        artifacts = [
            {"path": original.relative_to(self.root).as_posix(),
             "sha256": hashlib.sha256(original_data).hexdigest(), "bytes": len(original_data)},
            {"path": staged.relative_to(self.root).as_posix(),
             "sha256": hashlib.sha256(staged_data).hexdigest(), "bytes": len(staged_data)},
        ]
        receipt = {
            **self.receipt,
            "status": "recorder-error",
            "recorder_error": "OSError: simulated partial report publication",
            "failed_staging_artifacts": artifacts,
        }
        receipt.pop("duration_seconds")
        (attempt / "completed.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        return receipt, artifacts

    def test_recorder_error_preserves_only_hash_bound_partial_originals_and_staging(self):
        receipt, artifacts = self._recorder_error_with_partial_staging()
        result = checker._verify_failed_attempt(
            self.root, self.validated, self.group, receipt,
            self.plan_commit, self.attempt_number, "9" * 64,
        )
        self.assertEqual(result["failed_staging_artifacts"], artifacts)

    def test_recorder_error_rejects_tampered_duplicate_or_orphan_partial_files(self):
        receipt, artifacts = self._recorder_error_with_partial_staging()

        duplicate = json.loads(json.dumps(receipt))
        duplicate["failed_staging_artifacts"].append(dict(artifacts[0]))
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(duplicate, sort_keys=True) + "\n")
        with self.assertRaisesRegex(checker.EvidenceError, "duplicate failed staging artifact"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, duplicate,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

        tampered = json.loads(json.dumps(receipt))
        tampered["failed_staging_artifacts"][0]["sha256"] = "0" * 64
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(tampered, sort_keys=True) + "\n")
        with self.assertRaisesRegex(checker.EvidenceError, "SHA-256 mismatch"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, tampered,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

        orphan = json.loads(json.dumps(receipt))
        orphan["failed_staging_artifacts"].pop()
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(orphan, sort_keys=True) + "\n")
        with self.assertRaisesRegex(checker.EvidenceError, "differ from the exact recorder inventory"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, orphan,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

    def test_non_recorder_failure_cannot_claim_or_leave_partial_staging(self):
        staged = (self.root / "reports/releases/v0.9.2/normal/attempts" /
                  self.attempt_id / "unexpected.json")
        staged.parent.mkdir(parents=True)
        staged.write_text("{}\n")
        receipt = {**self.receipt, "failed_staging_artifacts": []}
        (self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id /
         "completed.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        with self.assertRaisesRegex(checker.EvidenceError, "recorder-only staging artifacts"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, receipt,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

    def test_failed_staging_namespace_rejects_symlinked_attempt_root(self):
        normal_attempts = self.root / "reports/releases/v0.9.2/normal/attempts"
        normal_attempts.mkdir(parents=True)
        outside = self.root / "outside-staging"
        outside.mkdir()
        (normal_attempts / self.attempt_id).symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(checker.EvidenceError, "symlink in .*failed staged reports"):
            checker._verify_failed_attempt(
                self.root, self.validated, self.group, self.receipt,
                self.plan_commit, self.attempt_number, "9" * 64,
            )

    def test_all_executor_terminal_failure_states_are_accepted_as_nonselected(self):
        attempt = self.root / "reports/releases/v0.9.2/attempts" / self.attempt_id
        cases = [
            ("timed-out", {"exit_code": 124, "timed_out": True, "capacity_loss": None}),
            ("capacity-lost", {"exit_code": 125, "timed_out": False,
                                "capacity_loss": "scratch ceiling exceeded",
                                "process_ownership": {
                                    "schema": "invocation-process-ownership/v1",
                                    "root_pid": None,
                                    "tracked_processes": [],
                                    "signals_sent": [],
                                    "cleanup_status": "not-started",
                                    "descendant_containment": "unproven",
                                    "tracking_interval_seconds": 2.0,
                                }}),
            ("recorder-error", {"recorder_error": "OSError: simulated receipt failure"}),
        ]
        for status, updates in cases:
            with self.subTest(status=status):
                receipt = {**self.receipt, "status": status, **updates}
                if status == "recorder-error":
                    receipt, _artifacts = self._recorder_error_with_partial_staging()
                (attempt / "completed.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
                result = checker._verify_failed_attempt(
                    self.root, self.validated, self.group, receipt,
                    self.plan_commit, self.attempt_number, "9" * 64,
                )
                self.assertEqual(result["status"], status)


if __name__ == "__main__":
    unittest.main()
