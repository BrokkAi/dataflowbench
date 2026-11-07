#!/usr/bin/env python3
"""Focused offline regressions for the v0.14.4 C5 benchmark driver."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import PurePosixPath
from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import unittest
from unittest.mock import Mock, patch
import zipfile


SCRIPT = Path(__file__).with_name("bifrost_v0144_benchmark.py")
ROOT = SCRIPT.resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bifrost_v0144_benchmark_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

UNIT_FIXTURE_ROOT = SCRIPT.parent / "test-fixtures" / "bifrost-v0144-benchmark-01"
UNIT_FIXTURE_MANIFEST_SHA256 = "a9742444f056ee6f3f5d573ac47a01bd966cbd0955b411638fd4b7f10f28d1b0"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def unit_fixture_manifest() -> dict:
    path = UNIT_FIXTURE_ROOT / "manifest.json"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != UNIT_FIXTURE_MANIFEST_SHA256:
        raise AssertionError("versioned C5 unit-fixture manifest digest differs")
    value = json.loads(raw)
    if (value.get("schema") != "bifrost-v0144-c5-unit-fixtures/v1" or
            value.get("scope") != "unit tests only; these fixtures are not qualification evidence or benchmark measurements"):
        raise AssertionError("versioned C5 unit-fixture manifest identity differs")
    return value


def unit_fixture_bytes(entry: dict) -> bytes:
    relative = PurePosixPath(entry["path"])
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise AssertionError("C5 unit-fixture path is not repository-relative")
    path = UNIT_FIXTURE_ROOT.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file():
        raise AssertionError(f"C5 unit fixture is missing or unsafe: {entry['path']}")
    raw = path.read_bytes()
    if len(raw) != entry.get("bytes") or hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
        raise AssertionError(f"C5 unit fixture size or SHA-256 differs: {entry['path']}")
    return raw


def scala_unit_fixture_artifacts() -> list[dict]:
    manifest = unit_fixture_manifest()
    artifacts = []
    expected_roles = {
        "scala-library-2.13.16.jar": "binary-jar",
        "scala-library-2.13.16-sources.jar": "sources-jar",
        "scala-library-2.13.16.pom": "upstream-pom",
    }
    entries = manifest.get("scala_artifacts")
    if not isinstance(entries, list) or {item.get("name") for item in entries} != set(expected_roles):
        raise AssertionError("C5 Scala unit-fixture roster differs")
    for entry in entries:
        name = entry["name"]
        if entry.get("role") != expected_roles[name]:
            raise AssertionError(f"C5 Scala unit-fixture role differs: {name}")
        raw = unit_fixture_bytes(entry)
        path = UNIT_FIXTURE_ROOT / entry["path"]
        if name.endswith(".jar"):
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None or "META-INF/MANIFEST.MF" not in archive.namelist():
                    raise AssertionError(f"C5 Scala unit fixture is not a valid JAR: {name}")
                if b"X-Unit-Fixture-Only: true" not in archive.read("META-INF/MANIFEST.MF"):
                    raise AssertionError(f"C5 Scala JAR fixture lacks its unit-only marker: {name}")
        else:
            pom = ET.fromstring(raw)
            namespace = "{http://maven.apache.org/POM/4.0.0}"
            if (pom.findtext(f"{namespace}artifactId") != "scala-library" or
                    pom.findtext(f"{namespace}version") != "2.13.16" or
                    "test fixture only" not in (pom.findtext(f"{namespace}description") or "")):
                raise AssertionError("C5 POM fixture identity or unit-only description differs")
        artifacts.append({
            "name": name,
            "role": entry["role"],
            "source_path": str(path),
            "sha256": entry["sha256"],
            "size_bytes": entry["bytes"],
        })
    return artifacts


def scala_unit_fixture_pins() -> dict:
    return {
        item["name"]: {
            "role": item["role"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in scala_unit_fixture_artifacts()
    }


def restore_control_capture_fixture(destination: Path) -> dict:
    """Restore the exact LFS-preserved capture into a temporary test root."""
    fixture = unit_fixture_manifest()["control_capture_archive"]
    manifest_path = ROOT / fixture["manifest_path"]
    archive_path = ROOT / fixture["part_path"]
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise AssertionError("lossless control-copy manifest is missing or unsafe")
    manifest_raw = manifest_path.read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != fixture["manifest_sha256"]:
        raise AssertionError("lossless control-copy manifest digest differs")
    archive_manifest = json.loads(manifest_raw)
    archive_info = archive_manifest.get("archive", {})
    if (archive_manifest.get("schema") != "v092-lossless-control-copy/v1" or
            archive_manifest.get("original_paths_unchanged") is not True or
            archive_manifest.get("full_content_verification") is not True or
            archive_manifest.get("original_root") != driver.CONTROL_CAPTURE_DEFAULT or
            archive_info.get("path") != fixture["part_path"] or
            archive_info.get("sha256") != fixture["part_sha256"] or
            archive_info.get("bytes") != fixture["part_bytes"] or
            archive_manifest.get("original_file_count") != fixture["file_count"] or
            archive_manifest.get("original_bytes") != fixture["original_bytes"]):
        raise AssertionError("lossless control-copy archive identity differs from unit-fixture pin")
    if archive_path.is_symlink() or not archive_path.is_file():
        raise AssertionError("lossless control-copy archive is missing or unsafe")
    if (archive_path.stat().st_size != fixture["part_bytes"] or
            hashlib.sha256(archive_path.read_bytes()).hexdigest() != fixture["part_sha256"]):
        raise AssertionError("lossless control-copy archive part size or SHA-256 differs")

    entries = archive_manifest.get("original_files")
    if not isinstance(entries, list) or len(entries) != fixture["file_count"]:
        raise AssertionError("lossless control-copy file roster differs")
    expected = {item["path"]: item for item in entries}
    if len(expected) != len(entries):
        raise AssertionError("lossless control-copy manifest repeats a path")
    capture_root = destination / driver.CONTROL_CAPTURE_DEFAULT
    capture_root.mkdir(parents=True, exist_ok=False)
    seen = set()
    total_bytes = 0
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(expected):
            raise AssertionError("lossless control-copy tar member count differs")
        for member in members:
            relative = PurePosixPath(member.name)
            if (not member.isfile() or relative.is_absolute() or
                    any(part in {"", ".", ".."} for part in relative.parts) or
                    member.name in seen or member.name not in expected):
                raise AssertionError(f"lossless control-copy tar member is unsafe or unexpected: {member.name}")
            seen.add(member.name)
            item = expected[member.name]
            if member.size != item.get("bytes"):
                raise AssertionError(f"lossless control-copy tar member size differs: {member.name}")
            output = capture_root.joinpath(*relative.parts)
            if not output.resolve().is_relative_to(capture_root.resolve()):
                raise AssertionError(f"lossless control-copy path escapes test root: {member.name}")
            output.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            if stream is None:
                raise AssertionError(f"lossless control-copy tar member has no content: {member.name}")
            digest = hashlib.sha256()
            copied = 0
            with stream, output.open("xb") as target:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    copied += len(chunk)
                    digest.update(chunk)
            if copied != item["bytes"] or digest.hexdigest() != item["sha256"]:
                raise AssertionError(f"lossless control-copy tar member digest differs: {member.name}")
            total_bytes += copied
    if seen != set(expected) or total_bytes != fixture["original_bytes"]:
        raise AssertionError("lossless control-copy extraction is incomplete")
    return archive_manifest


def actual_base_groups() -> list[dict]:
    contract = read_json(ROOT / driver.BASE_CONTRACT_REL)
    return contract["groups"]


def all_group_ids() -> list[str]:
    return [item["id"] for item in actual_base_groups()]


def write_ledger(root: Path, rows: list[dict]) -> Path:
    path = root / driver.LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


class FrozenTargetTests(unittest.TestCase):
    def test_release_helper_loader_executes_bound_source_despite_old_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scripts/execute-release-v092.py"
            source.parent.mkdir()
            source.write_bytes(b'VALUE = "old"\n')
            before = source.stat()
            py_compile.compile(str(source), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            current = b'VALUE = "new"\n'
            source.write_bytes(current)
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
            digest = hashlib.sha256(current).hexdigest()
            loaded, bound_digest = driver._load_core(root, digest)
            self.assertEqual(loaded.VALUE, "new")
            self.assertEqual(bound_digest, digest)
            self.assertEqual(loaded.__verified_source_sha256__, digest)

    def test_target_roster_and_runtime_vector_are_exactly_projected_from_c4(self):
        baseline = actual_base_groups()
        runner = "/tmp/c5/execute-release-v092.py"
        binary = "/tmp/c5/bifrost-0.14.4"
        projected = driver.project_target_groups(baseline, runner, binary)
        driver.validate_group_projections(projected, baseline, runner, binary)

        self.assertEqual([item["id"] for item in projected], list(driver.BIFROST_GROUP_IDS))
        self.assertEqual(len(projected), 20)
        for item in projected:
            argv = item["runtime_argv"]
            self.assertEqual(argv[0], runner)
            self.assertEqual(argv.count(binary), 1)
            self.assertEqual(argv[argv.index("--bifrost") + 1], binary)
            self.assertEqual(item["base_group_sha256"], driver._group_sha256(item["base_group"]))

    def test_projection_rejects_membership_group_fields_and_argv_structure_changes(self):
        baseline = actual_base_groups()
        runner = "/tmp/c5/execute-release-v092.py"
        binary = "/tmp/c5/bifrost-0.14.4"
        projected = driver.project_target_groups(baseline, runner, binary)

        reordered = copy.deepcopy(projected)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        with self.assertRaisesRegex(driver.BenchmarkError, "membership or order"):
            driver.validate_group_projections(reordered, baseline, runner, binary)

        changed_group = copy.deepcopy(projected)
        changed_group[0]["base_group"]["deadline_seconds"] += 1
        with self.assertRaisesRegex(driver.BenchmarkError, "changed baseline group fields"):
            driver.validate_group_projections(changed_group, baseline, runner, binary)

        changed_argv = copy.deepcopy(projected)
        changed_argv[0]["runtime_argv"].append("--no-incremental")
        with self.assertRaisesRegex(driver.BenchmarkError, "argv structure"):
            driver.validate_group_projections(changed_argv, baseline, runner, binary)

        duplicate_flag = copy.deepcopy(baseline)
        first = next(item for item in duplicate_flag if item.get("id") == driver.BIFROST_GROUP_IDS[0])
        first["argv"] = [*first["argv"], "--bifrost", "/tmp/second-bifrost"]
        with self.assertRaisesRegex(driver.BenchmarkError, "exactly one --bifrost"):
            driver.project_target_groups(duplicate_flag, runner, binary)

    def test_resource_policy_is_an_immutable_exact_ceiling(self):
        expected = {
            "launch_free_floor_gib": 127,
            "continuous_free_floor_gib": 125,
            "protected_reserve_gib": 40,
            "emergency_margin_gib": 8,
            "guard_stop_floor_gib": 48,
            "scratch_ceiling_gib": 24,
            "retention_ceiling_gib": 24,
            "source_aggregate_ceiling_gib": 30,
            "source_per_attempt_ceiling_gib": 12,
            "serial_analyzer_slots": 1,
        }
        self.assertEqual(driver.RESOURCE_POLICY, expected)
        driver.validate_resource_policy(copy.deepcopy(expected))
        for key in expected:
            changed = copy.deepcopy(expected)
            changed[key] += 1
            with self.subTest(key=key), self.assertRaisesRegex(driver.BenchmarkError, "resource gates"):
                driver.validate_resource_policy(changed)

    def test_approval_subject_mutation_invalidates_approval(self):
        contract = {
            "schema": driver.CONTRACT_SCHEMA,
            "groups": [{"id": group_id, "deadline_seconds": 17} for group_id in driver.BIFROST_GROUP_IDS],
            "resource_policy": copy.deepcopy(driver.RESOURCE_POLICY),
            "execution_authorized": True,
            "approval": {
                "status": "approved",
                "approved_by": "root-review",
                "approved_at_utc": "2026-11-01T12:00:00Z",
                "subject_sha256": "",
            },
        }
        contract["approval"]["subject_sha256"] = driver.approval_subject_sha256(contract)
        driver.validate_approval(contract, required=True)

        mutated = copy.deepcopy(contract)
        mutated["groups"][0]["deadline_seconds"] += 1
        with self.assertRaisesRegex(driver.BenchmarkError, "does not bind"):
            driver.validate_approval(mutated, required=True)


class QualificationReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.qualification = read_json(ROOT / driver.QUALIFICATION_DEFAULT)
        self.fixture_manifest = unit_fixture_manifest()
        ledger_entry = self.fixture_manifest["ledger"]
        self.ledger_fixture_bytes = unit_fixture_bytes(ledger_entry)
        self.ledger_fixture_lines = ledger_entry["line_count"]
        self.ledger_fixture_sha256 = ledger_entry["sha256"]
        if (self.ledger_fixture_lines != 109 or
                len(self.ledger_fixture_bytes.splitlines()) != self.ledger_fixture_lines):
            raise AssertionError("synthetic C5 unit ledger must contain exactly 109 fixture rows")
        self.bifrost_binding = {
            "path": self.qualification["tool"]["path"],
            "sha256": driver.BIFROST_BINARY_SHA256,
            "build_identity": driver.BIFROST_BUILD_IDENTITY,
        }

    def install_fixture(self, mutate=None) -> str:
        qualification = copy.deepcopy(self.qualification)
        if mutate is not None:
            mutate(qualification)
        append_ref = qualification["append_after_ledger"]
        append_ref["rows"] = self.ledger_fixture_lines
        append_ref["sha256"] = self.ledger_fixture_sha256
        raw = driver._pretty_json(qualification)
        qualification_path = self.root / driver.QUALIFICATION_DEFAULT
        qualification_path.parent.mkdir(parents=True, exist_ok=True)
        qualification_path.write_bytes(raw)

        restore_control_capture_fixture(self.root)

        required = {
            driver.CONTROL_REVIEW_DEFAULT,
            driver.INDEPENDENT_REVIEW_DEFAULT,
            driver.BIFROST_RECEIPT_DEFAULT,
            "reports/releases/v0.9.2/qualification/bifrost-v0144-01/review-bifrost-v0144-01.py",
            "reports/releases/v0.9.2/qualification/bifrost-v0144-01/control-comparison-diagnostic-01.json",
            "reports/releases/v0.9.2/qualification/bifrost-v0140-01/controls-attempt-01/artifact-hashes.json",
            "reports/releases/v0.9.2/qualification/bifrost-v0140-01/control-review-01.json",
            driver.NATIVE_EVIDENCE_PATHS["help_stdout"],
            f"{driver.CONTROL_CAPTURE_DEFAULT}/artifact-hashes.json",
            f"{driver.CONTROL_CAPTURE_DEFAULT}/commands.jsonl",
            f"{driver.CONTROL_CAPTURE_DEFAULT}/qualification.json",
            driver.HUMAN_AUTHORIZATION_DEFAULT,
            driver.BASE_PARENT_EXECUTION_REL,
            driver.LEDGER_REL,
            qualification["binding_implementation"]["path"],
        }
        capture_manifest = read_json(self.root / f"{driver.CONTROL_CAPTURE_DEFAULT}/artifact-hashes.json")
        required.update(
            f"{driver.CONTROL_CAPTURE_DEFAULT}/{item['path']}"
            for item in capture_manifest["files"]
        )
        independent_review = read_json(ROOT / driver.INDEPENDENT_REVIEW_DEFAULT)
        required.update(independent_review["source_review"]["files"])
        required.update(item["path"] for item in independent_review["evidence_refs"].values())
        for relative in required:
            if (relative == driver.LEDGER_REL or
                    relative.startswith(driver.CONTROL_CAPTURE_DEFAULT + "/")):
                continue
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        ledger_path = self.root / driver.LEDGER_REL
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_bytes(self.ledger_fixture_bytes)
        return driver._sha(raw)

    def verify_with_digest(self, digest: str):
        with patch.object(driver, "QUALIFICATION_SHA256", digest), \
             patch.object(driver, "LEDGER_PREFIX_LINES", self.ledger_fixture_lines), \
             patch.object(driver, "LEDGER_PREFIX_SHA256", self.ledger_fixture_sha256):
            return driver._verify_qualification(self.root, driver.QUALIFICATION_DEFAULT,
                                                self.bifrost_binding)

    def test_limited_qualification_passes_with_exact_refs(self):
        digest = self.install_fixture()
        qualification, binding = self.verify_with_digest(digest)
        self.assertIs(qualification["execution_eligible"], True)
        self.assertIs(qualification["full_policy_qualification"], False)
        self.assertEqual(binding["groups"], list(driver.BIFROST_GROUP_IDS))
        self.assertEqual(binding["independent_review"]["sha256"], driver.INDEPENDENT_REVIEW_SHA256)

    def test_incomplete_qualification_cannot_bypass_typed_gate(self):
        digest = self.install_fixture(lambda value: value.update(full_policy_qualification=True))
        with self.assertRaisesRegex(driver.BenchmarkError, "limited measurement coverage"):
            self.verify_with_digest(digest)

    def test_wrong_review_reference_is_rejected(self):
        def mutate(value):
            value["control_review"]["path"] = "reports/releases/v0.9.2/qualification/bifrost-review-01.json"

        digest = self.install_fixture(mutate)
        with self.assertRaisesRegex(driver.BenchmarkError, "unexpected independent review"):
            self.verify_with_digest(digest)


class SnapshotAndHistoryTests(unittest.TestCase):
    def synthetic_ledger_row(self, root: Path, group: str, attempt_number: int) -> dict:
        execution_root = (root / driver.EXECUTION_GROUPS_REL / "series-02" /
                          group / f"attempt-{attempt_number:02d}")
        return {
            "group_id": group,
            "attempt_id": f"{group}-attempt-{attempt_number:02d}-series-02",
            "execution_series": 2,
            "status": "completed",
            "execution_root": str(execution_root),
            "cache_root": str(root / driver.CACHE_REL / "series-02" / group /
                               f"attempt-{attempt_number:02d}"),
            "environment": {"HOME": str(execution_root / "home"),
                            "TMPDIR": str(execution_root / "tmp")},
            "output_roots": [],
            "source_inputs": [],
            "start_utc": "2026-10-20T00:57:00.680937+00:00",
        }

    def test_current_source_closure_does_not_reclassify_old_historical_inputs(self):
        historical = [{"path": f"archived/c4-source-{index:04d}.bin"} for index in range(1712)]
        base = {"source_inputs": historical}
        refs = ["reports/releases/v0.9.2/qualification/bifrost-v0144-01/bifrost-release-01.json",
                "reports/releases/v0.9.2/qualification/bifrost-v0144-01/bifrost-review-03.json"]
        current = driver._source_input_paths(ROOT, base, refs)
        self.assertEqual(len(current), len(set(current)))
        self.assertLess(len(current), 20)
        self.assertTrue(set(refs).issubset(current))
        self.assertFalse(set(item["path"] for item in historical) & set(current))

    def make_synthetic_history(self, root: Path) -> tuple[list[str], dict]:
        group = "bifrost-smoke"
        series_two = root / driver.EXECUTION_GROUPS_REL / "series-02" / group
        (series_two / "attempt-02").mkdir(parents=True)
        row = self.synthetic_ledger_row(root, group, 3)
        write_ledger(root, [row])
        return all_group_ids(), row

    def permissive_synthetic_prefix(self):
        return (
            patch.object(driver, "LEDGER_PREFIX_LINES", 0),
            patch.object(driver, "LEDGER_PREFIX_SHA256", hashlib.sha256(b"").hexdigest()),
        )

    def test_history_counts_unledgered_smoke02_as_consumed_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            groups, row = self.make_synthetic_history(root)
            old_source_path = "reports/older-qual/raw.json"
            old_source_bytes = b"older qualification source copy\n"
            old_source = root / old_source_path
            old_source.parent.mkdir(parents=True, exist_ok=True)
            old_source.write_bytes(old_source_bytes)
            row["source_inputs"] = [{"path": old_source_path, "sha256": hashlib.sha256(old_source_bytes).hexdigest()}]
            write_ledger(root, [row])
            historical_execution_root = Path(row["execution_root"])
            historical_source_copy = historical_execution_root / old_source_path
            historical_source_copy.parent.mkdir(parents=True, exist_ok=True)
            historical_source_copy.write_bytes(old_source_bytes)
            copied_project = root / "execution-state/v092/joern-capability-materialized-preflight-01"
            (copied_project / "src").mkdir(parents=True)
            (copied_project / "cases").mkdir()
            (copied_project / "src/copied.rs").write_bytes(b"copied source\n")
            (copied_project / "cases/copied.json").write_bytes(b'{"case":true}\n')
            (copied_project / "Cargo.toml").write_bytes(b"[package]\nname='copied'\n")
            copied_release_attempt = (
                copied_project / "reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01"
            )
            copied_release_attempt.mkdir(parents=True)
            retained_marker = copied_release_attempt / "copied-evidence.json"
            retained_marker.write_text('{"preserve":true}\n', encoding="utf-8")
            excluded_roots = []
            for name in ("groups", "cache", "tools", "builds", "swift-source"):
                runtime_project = root / "execution-state/v092" / name / "synthetic-project"
                (runtime_project / "src").mkdir(parents=True)
                (runtime_project / "cases").mkdir()
                (runtime_project / "Cargo.toml").write_bytes(b"[package]\n")
                excluded_roots.append(runtime_project)
            over_depth = root / "execution-state/v092/aux/level-two/level-three/project"
            (over_depth / "src").mkdir(parents=True)
            (over_depth / "cases").mkdir()
            (over_depth / "Cargo.toml").write_bytes(b"[package]\n")
            prefix_lines, prefix_hash = self.permissive_synthetic_prefix()
            with prefix_lines, prefix_hash:
                history = driver._scan_history(root, groups, preparing=False)
            counters = history["snapshot"]["historical_group_counters"]["bifrost-smoke"]
            self.assertEqual(history["snapshot"]["global_prior_consumed_attempt_count"], 2)
            self.assertEqual(counters["prior_consumed_count"], 2)
            self.assertEqual(counters["prior_max_attempt_number"], 3)
            self.assertEqual(counters["next_attempt_number"], 4)
            self.assertEqual(len(counters["unledgered_started_attempts"]), 1)
            consumed = counters["unledgered_started_attempts"][0]
            self.assertEqual(consumed["attempt_id"], "bifrost-smoke-attempt-02-series-02")
            self.assertEqual(consumed["status"], "unclosed-started-namespace")
            self.assertNotIn("joern-swift-common108", history["ledger"]["historical_records"])
            self.assertEqual(retained_marker.read_text(encoding="utf-8"), '{"preserve":true}\n')

            baseline = ROOT / driver.BASE_CONTRACT_REL
            local_baseline = root / driver.BASE_CONTRACT_REL
            local_baseline.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(baseline, local_baseline)

            def logical_size(paths):
                seen = set()
                total = 0
                for item in paths:
                    item = Path(item)
                    files = [item] if item.is_file() else (
                        [value for value in item.rglob("*") if value.is_file()]
                        if item.is_dir() else []
                    )
                    for file_path in files:
                        identity = file_path.resolve()
                        if identity not in seen:
                            seen.add(identity)
                            total += file_path.stat().st_size
                return total

            fake_guard_module = SimpleNamespace(
                DiskGuard=SimpleNamespace(logical_size=logical_size)
            )
            fake_core = SimpleNamespace(
                SNAPSHOT_DIRECTORIES=("src", "cases"),
                SNAPSHOT_FILES=("Cargo.toml",),
            )
            with patch.object(driver, "_strict_guard_module", fake_guard_module):
                current_paths, _retained, _scratch, working_bytes, projections, inventory = (
                    driver._historical_capacity_paths(
                        root, {}, history, fake_core,
                        execution_root=root / "execution-state/v092/groups/series-03/bifrost-smoke/attempt-01",
                        env={"HOME": str(root / "temporary-home"),
                             "TMPDIR": str(root / "temporary-tmp")},
                        output_roots=[], current_source_inputs=[],
                    )
                )
            expected_project_bytes = logical_size([copied_project])
            self.assertEqual(projections, [{"path": str(copied_project), "bytes": expected_project_bytes}])
            self.assertIn(old_source_path, inventory["paths"])
            self.assertEqual(inventory["path_count"], len(inventory["paths"]))
            self.assertEqual(inventory["present_logical_bytes"], len(old_source_bytes))
            self.assertEqual(logical_size([historical_source_copy]), len(old_source_bytes))
            self.assertEqual(working_bytes, expected_project_bytes + 2 * len(old_source_bytes))
            self.assertLess(len(current_paths), 20)
            self.assertNotIn(old_source_path, current_paths)
            current_source_closure = driver._source_input_paths(
                ROOT, {"source_inputs": [{"path": old_source_path, "sha256": "f" * 64}]},
                ["reports/releases/v0.9.2/qualification/bifrost-v0144-01/bifrost-release-01.json"],
            )
            self.assertNotIn(old_source_path, current_source_closure)
            self.assertFalse(set(excluded_roots) & {Path(item["path"]) for item in projections})
            self.assertNotIn(over_depth.resolve(), [Path(item["path"]) for item in projections])
            self.assertEqual(history["snapshot"]["global_prior_consumed_attempt_count"], 2)
            self.assertEqual(len(counters["unledgered_started_attempts"]), 1)

            row["source_inputs"] = [{"path": "../outside/raw.json", "sha256": "f" * 64}]
            write_ledger(root, [row])
            prefix_lines, prefix_hash = self.permissive_synthetic_prefix()
            with prefix_lines, prefix_hash, self.assertRaisesRegex(
                    driver.BenchmarkError, "not a safe repository-relative path"):
                driver._scan_ledger(root, groups)

    def test_auxiliary_source_projection_rejects_symlinks_inside_a_detected_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            project = root / "execution-state/v092/preflight-copy"
            (project / "src").mkdir(parents=True)
            (project / "cases").mkdir()
            (project / "Cargo.toml").write_bytes(b"[package]\n")
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            (project / "src/external-link").symlink_to(outside)
            with self.assertRaisesRegex(driver.BenchmarkError, "symlink"):
                driver._auxiliary_source_projection_roots(root)

    def test_duplicate_ledger_attempt_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            group = "bifrost-smoke"
            row = self.synthetic_ledger_row(root, group, 1)
            write_ledger(root, [row, row])
            prefix_lines, prefix_hash = self.permissive_synthetic_prefix()
            with prefix_lines, prefix_hash, self.assertRaisesRegex(driver.BenchmarkError, "duplicates an attempt identity"):
                driver._scan_ledger(root, all_group_ids())

    def test_fresh_prepare_rejects_existing_target_attempt_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            groups, _row = self.make_synthetic_history(root)
            target = root / driver.EXECUTION_GROUPS_REL / driver.SERIES_LABEL / "bifrost-c-kernel" / "attempt-01"
            target.mkdir(parents=True)
            prefix_lines, prefix_hash = self.permissive_synthetic_prefix()
            with prefix_lines, prefix_hash, self.assertRaisesRegex(driver.BenchmarkError, "already contains started attempts"):
                driver._scan_history(root, groups, preparing=True)

    def test_prepared_contract_is_written_only_to_a_fresh_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = {"schema": driver.CONTRACT_SCHEMA, "execution_authorized": False, "approval": None}
            output = driver._write_prepared_manifest(root, value)
            before = output.read_bytes()
            self.assertEqual(json.loads(before), value)
            with self.assertRaisesRegex(driver.BenchmarkError, "refusing to replace existing C5 contract"):
                driver._write_prepared_manifest(root, {**value, "execution_authorized": True})
            self.assertEqual(output.read_bytes(), before)


class ExecutionEvidenceTests(unittest.TestCase):
    @contextmanager
    def fake_group_execution(self, root: Path, *, recorder_failure: bool = False):
        """Run the real C5 recorder with a fake core boundary and no analyzer."""
        core, core_sha = driver._load_core(ROOT)
        group_id = "bifrost-c-kernel"
        binary = root / "fake-bifrost"
        binary.write_bytes(b"offline fake engine identity")
        runner = root / "fake-harness"
        runner.write_bytes(b"offline fake harness identity")
        baseline = actual_base_groups()
        groups = driver.project_target_groups(baseline, str(runner), str(binary))
        projection = next(item for item in groups if item["id"] == group_id)
        counters = {
            item: {"prior_max_attempt_number": 0}
            for item in driver.BIFROST_GROUP_IDS
        }
        contract = {
            "groups": groups,
            "resource_policy": copy.deepcopy(driver.RESOURCE_POLICY),
            "parent_population": {"population": "v0.9.0"},
            "runtime": {
                "runner": {"sha256": hashlib.sha256(b"synthetic harness").hexdigest()},
                "scala_maven": {"receipt": {"path": "synthetic-scala-receipt"}},
            },
            "source_snapshot": {
                "core_helpers": [{"sha256": core_sha}],
                "runner_source": {"sha256": hashlib.sha256(b"synthetic runner source").hexdigest()},
                "source_inputs": [],
            },
            "attempt_history": {
                "global_prior_consumed_attempt_count": 109,
                "historical_group_counters": counters,
            },
        }
        validated = {
            "path": root / driver.CONTRACT_REL,
            "contract": contract,
            "contract_sha256": "c" * 64,
            "source_commit": "a" * 40,
            "plan_commit": "b" * 40,
            "runner_path": str(runner),
            "bifrost": {"path": str(binary), "sha256": driver._sha_file(binary)},
            "qualification": {"path": "synthetic-qualification", "sha256": "d" * 64},
            "history": {"target_records": []},
            "ledger": {
                "line_count": 109,
                "bytes": 1000,
                "target_rows": [],
                "target_line_count": 0,
                "target_suffix_sha256": hashlib.sha256(b"").hexdigest(),
                "target_suffix_state": hashlib.sha256(),
            },
        }
        processed_argv: list[list[str]] = []
        guard_checks: list[dict] = []
        source_inventory_paths = ["Cargo.toml", "cases", "src"]
        source_inventory = {
            "paths": source_inventory_paths,
            "path_count": len(source_inventory_paths),
            "paths_sha256": driver._sha(driver._canonical_json(source_inventory_paths)),
            "present_logical_bytes": 0,
        }

        class FakeDiskGuard:
            def check(self, **kwargs):
                guard_checks.append(kwargs)
                return {"free_bytes": 200 * 1024**3,
                        "post_write_free_bytes": 200 * 1024**3 - kwargs.get("projected_bytes", 0)}

        fake_guard_module = SimpleNamespace(
            DiskGuard=SimpleNamespace(logical_size=lambda paths: 0)
        )

        def materialize(*_args, preflight_only=False, **_kwargs):
            if preflight_only:
                return 0
            if recorder_failure:
                raise RuntimeError("synthetic source materialization recorder failure")
            return None

        def run_process(argv, cwd, _env, stdout, stderr, *_args, **_kwargs):
            processed_argv.append(list(argv))
            stdout.parent.mkdir(parents=True, exist_ok=True)
            stdout.write_bytes(b"synthetic stdout\n")
            stderr.write_bytes(b"")
            for relative in projection["base_group"]["output_roots"]:
                output = cwd / Path(relative)
                if Path(relative).suffix:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(b'{"synthetic":true}\n')
                else:
                    output.mkdir(parents=True, exist_ok=True)
            return 0, False, 0.25, None

        def copy_tree(source, _target, execution_root, capture_root, *, preflight_only=False,
                      planned_files=None, **_kwargs):
            if preflight_only:
                sources = [source] if source.is_file() else sorted(
                    item for item in source.rglob("*") if item.is_file()
                )
                planned = []
                for item in sources:
                    relative = item.resolve().relative_to(execution_root.resolve()).as_posix()
                    planned.append({
                        "source": item,
                        "target": capture_root / Path(relative),
                        "relative": relative,
                        "bytes": item.stat().st_size,
                    })
                return planned
            result = []
            for item in planned_files or []:
                target = item["target"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item["source"], target)
                data = target.read_bytes()
                result.append({
                    "execution_relative": item["relative"],
                    "capture_path": str(target),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
            return result

        def stage_report(repo_root, attempt, _execution_root, attempt_id, spec,
                         _capture_map, _output_roots, _fixture, **_kwargs):
            source_bytes = b'{"synthetic-report":true}\n'
            original_rel = Path("original") / Path(spec["path"])
            original = attempt / original_rel
            report_rel = Path(spec["path"]).relative_to("reports/releases/v0.9.2/normal")
            staged_rel = Path(driver.NORMAL_ATTEMPTS_REL) / attempt_id / report_rel
            staged = repo_root / staged_rel
            original.parent.mkdir(parents=True, exist_ok=True)
            staged.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(source_bytes)
            staged.write_bytes(source_bytes)
            digest = hashlib.sha256(source_bytes).hexdigest()
            return {
                "source_path": spec["source_path"],
                "staged_path": staged_rel.as_posix(),
                "original_path": (Path(driver.ATTEMPTS_REL) / attempt_id / original_rel).as_posix(),
                "original_sha256": digest,
                "staged_sha256": digest,
                "case_ids": list(spec["case_ids"]),
                "tool": spec["tool"],
                "tool_version": spec["tool_version"],
                "raw_output_mappings": [],
            }

        with ExitStack() as stack:
            stack.enter_context(patch.object(driver, "_load_core", return_value=(core, core_sha)))
            stack.enter_context(patch.object(driver, "_disk_guard", return_value=FakeDiskGuard()))
            stack.enter_context(patch.object(
                driver, "_historical_capacity_paths", return_value=([], [], [], 0, [], source_inventory)
            ))
            stack.enter_context(patch.object(driver, "_strict_guard_module", fake_guard_module))
            stack.enter_context(patch.object(driver, "BIFROST_BINARY_SHA256", driver._sha_file(binary)))
            stack.enter_context(patch.object(driver, "_verify_source_capacity_admission", return_value=None))
            stack.enter_context(patch.object(core, "_materialize_source", side_effect=materialize))
            stack.enter_context(patch.object(core, "_assert_source_snapshot", return_value=None))
            stack.enter_context(patch.object(core, "_check_tool_file", return_value=None))
            stack.enter_context(patch.object(core, "_check_resources", return_value=None))
            stack.enter_context(patch.object(core, "_run_process", side_effect=run_process))
            stack.enter_context(patch.object(core, "_copy_tree", side_effect=copy_tree))
            stack.enter_context(patch.object(core, "_stage_report", side_effect=stage_report))
            stack.enter_context(patch.object(core, "_report_identity", return_value={}))
            yield validated, core, processed_argv, guard_checks

    def test_one_group_records_completed_fake_execution_and_verifies_hash_bound_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.fake_group_execution(root) as (validated, _core, processed_argv, guard_checks):
                row = driver._one_group(
                    validated, "bifrost-c-kernel", global_attempt_number=110,
                    remaining_group_count=20, invocation_id="synthetic-invocation",
                )
                self.assertEqual(row["status"], "completed")
                self.assertEqual(row["exit_code"], 0)
                self.assertEqual(row["source_capacity_admission"]["working_baseline_bytes"], 0)
                self.assertEqual(row["source_capacity_admission"]["auxiliary_source_projections"], [])
                self.assertEqual(row["source_capacity_admission"]["resource_policy"], driver.RESOURCE_POLICY)
                self.assertEqual(len(processed_argv), 1)
                self.assertEqual(processed_argv[0], validated["contract"]["groups"][0]["runtime_argv"])
                self.assertGreaterEqual(len(guard_checks), 3)
                attempt = root / driver.ATTEMPTS_REL / row["attempt_id"]
                self.assertEqual(read_json(attempt / "completed.json"), row)
                ledger_rows = [json.loads(line) for line in (root / driver.LEDGER_REL).read_text().splitlines()]
                self.assertEqual(ledger_rows, [row])
                progress = [json.loads(line) for line in (root / driver.PROGRESS_REL).read_text().splitlines()]
                self.assertEqual([item["phase"] for item in progress], ["attempt-started", "attempt-terminal"])
                self.assertEqual(progress[-1]["status"], "completed")
                driver._verify_attempt_outputs(root, validated, row)

                capture = Path(row["captured_files"][0]["capture_path"])
                original_capture = capture.read_bytes()
                capture.write_bytes(original_capture + b"tampered")
                with self.assertRaisesRegex(driver.BenchmarkError, "raw capture changed"):
                    driver._verify_attempt_outputs(root, validated, row)
                capture.write_bytes(original_capture)

                staged = root / row["reports"][0]["staged_path"]
                original_staged = staged.read_bytes()
                staged.write_bytes(original_staged + b"tampered")
                with self.assertRaisesRegex(driver.BenchmarkError, "staged/original report changed"):
                    driver._verify_attempt_outputs(root, validated, row)
                staged.write_bytes(original_staged)
                driver._verify_attempt_outputs(root, validated, row)

    def test_one_group_recorder_failure_is_terminal_and_never_claims_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.fake_group_execution(root, recorder_failure=True) as (
                validated, _core, processed_argv, _guard_checks
            ):
                row = driver._one_group(
                    validated, "bifrost-c-kernel", global_attempt_number=110,
                    remaining_group_count=20, invocation_id="synthetic-recorder-failure",
                )
                self.assertEqual(row["status"], "recorder-error")
                self.assertEqual(row["exit_code"], 125)
                self.assertEqual(row["reports"], [])
                self.assertEqual(processed_argv, [])
                self.assertIn("synthetic source materialization recorder failure", row["recorder_error"])
                attempt = root / driver.ATTEMPTS_REL / row["attempt_id"]
                self.assertEqual(read_json(attempt / "completed.json"), row)
                ledger_rows = [json.loads(line) for line in (root / driver.LEDGER_REL).read_text().splitlines()]
                self.assertEqual(ledger_rows, [row])
                self.assertTrue((attempt / "stdout.txt").is_file())
                self.assertTrue((attempt / "stderr.txt").is_file())
                driver._verify_attempt_outputs(root, validated, row)

    def test_scala_staging_copies_only_exact_hash_bound_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "sources"
            source_root.mkdir()
            artifacts = scala_unit_fixture_artifacts()
            for artifact in artifacts:
                source = source_root / artifact["name"]
                shutil.copyfile(artifact["source_path"], source)
                artifact["source_path"] = str(source)
            home = root / "home"
            home.mkdir()

            class Guard:
                def check(self, **_kwargs):
                    return None

            binding = {"scala": {"artifacts": artifacts, "source_entry_count": 3}}
            production_pins = driver.SCALA_FILES
            with patch.object(driver, "SCALA_FILES", scala_unit_fixture_pins()):
                result = driver._stage_scala_maven(binding, home, Guard())
                self.assertEqual(result["source_entry_count"], 3)
                self.assertEqual(len(result["artifacts"]), 3)
                self.assertEqual({item["role"] for item in result["artifacts"]},
                                 {"binary-jar", "sources-jar", "upstream-pom"})
                for source_info, staged in zip(artifacts, result["artifacts"]):
                    staged_path = Path(staged["path"])
                    self.assertEqual(staged["sha256"], source_info["sha256"])
                    self.assertEqual(staged["bytes"], source_info["size_bytes"])
                    self.assertEqual(hashlib.sha256(staged_path.read_bytes()).hexdigest(), source_info["sha256"])

                (source_root / artifacts[0]["name"]).write_bytes(b"altered")
                retry_home = root / "retry-home"
                retry_home.mkdir()
                with self.assertRaisesRegex(driver.BenchmarkError, "pinned Scala artifact changed"):
                    driver._stage_scala_maven(binding, retry_home, Guard())
            self.assertIs(driver.SCALA_FILES, production_pins)

    def test_scala_attempt_verifier_rehashes_exact_home_and_postcheck(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            execution_root = root / "execution"
            home = execution_root / "home"
            staged_root = home / ".m2/repository/org/scala-lang/scala-library/2.13.16"
            staged_root.mkdir(parents=True)
            staged = []
            postcheck = []
            fixture_artifacts = scala_unit_fixture_artifacts()
            fixture_pins = scala_unit_fixture_pins()
            for source_info in fixture_artifacts:
                name = source_info["name"]
                expected = fixture_pins[name]
                destination = staged_root / name
                shutil.copyfile(source_info["source_path"], destination)
                staged.append({
                    "path": str(destination), "sha256": expected["sha256"],
                    "bytes": expected["size_bytes"], "role": expected["role"],
                })
                postcheck.append({
                    "name": name, "sha256": expected["sha256"], "bytes": expected["size_bytes"],
                })
            row = {
                "group_id": "bifrost-scala-kernel",
                "environment": {"HOME": str(home)},
                "scala_maven_staging": {
                    "repository": str(staged_root), "source_entry_count": 3,
                    "artifacts": staged,
                },
                "scala_maven_staging_postcheck": {"verified": True, "artifacts": postcheck},
            }
            validated = {"scala": {"source_entry_count": 3}}
            production_pins = driver.SCALA_FILES
            with patch.object(driver, "SCALA_FILES", fixture_pins):
                result = driver._check_scala_staging(
                    row, execution_root, validated, require_postcheck=True
                )
                self.assertEqual(result, {"verified": True, "artifacts": postcheck})

                tampered = staged_root / "scala-library-2.13.16-sources.jar"
                tampered.write_bytes(tampered.read_bytes() + b"tampered")
                with self.assertRaisesRegex(driver.BenchmarkError, "Scala attempt staged artifact changed"):
                    driver._check_scala_staging(row, execution_root, validated, require_postcheck=True)
            self.assertIs(driver.SCALA_FILES, production_pins)

    def test_read_only_reconcile_does_not_launch_analyzer_or_write_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validated = {
                "contract": {"parent_population": {"full_counts": {
                    "groups": 84, "report_partitions": 92, "report_rows": 4252,
                    "population_cases": 1108,
                }}},
                "contract_sha256": "c" * 64,
                "source_commit": "a" * 40,
                "plan_commit": "b" * 40,
                "ledger": {"line_count": 109, "bytes": 1000, "sha256": "e" * 64,
                           "target_line_count": 0, "target_suffix_sha256": hashlib.sha256(b"").hexdigest()},
                "qualification": {"full_policy_qualification": False},
            }
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            validate_contract = Mock(return_value=validated)
            @contextmanager
            def fake_lock():
                yield

            fake_core = SimpleNamespace(_exclusive_lock=fake_lock)
            with patch.object(driver, "_validate_contract", validate_contract), \
                 patch.object(driver, "_load_core", return_value=(fake_core, "f" * 64)), \
                 patch.object(driver, "_validate_existing_target_attempts", return_value=[]), \
                 patch.object(driver, "_one_group", side_effect=AssertionError("verify launched an attempt")), \
                 patch("subprocess.Popen", side_effect=AssertionError("verify launched a process")) as popen:
                result = driver.reconcile_outputs(root, driver.CONTRACT_REL)
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            self.assertEqual(before, after)
            validate_contract.assert_called_once_with(
                root, driver.CONTRACT_REL, require_approval=True, require_committed=True,
                check_current_source=False,
            )
            popen.assert_not_called()
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["completed_group_count"], 0)
            self.assertEqual(result["missing_groups"], list(driver.BIFROST_GROUP_IDS))


class GitPlanBindingTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()

    def test_plan_introduction_commit_is_stable_after_head_advance_and_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.git(root, "init", "-q")
            self.git(root, "config", "user.name", "C5 test")
            self.git(root, "config", "user.email", "c5-test@example.invalid")
            self.git(root, "config", "commit.gpgsign", "false")
            frozen_source_file = root / "src/frozen.rs"
            frozen_source_file.parent.mkdir(parents=True)
            frozen_source_file.write_text("source", encoding="utf-8")
            helper_copy = root / "scripts/execute-release-v092.py"
            helper_copy.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / "scripts/execute-release-v092.py", helper_copy)
            driver_copy = root / "scripts/bifrost_v0144_benchmark.py"
            shutil.copyfile(SCRIPT, driver_copy)

            plan, _population, base, _parent, all_ids = (None, None, None, None, None)
            plan, population, base, parent, all_ids = driver._base_inputs(ROOT)
            runner = root / "fake-harness"
            runner.write_bytes(b"synthetic runner")
            runner_sha = driver._sha_file(runner)
            runner_build = {"binary": {"sha256": runner_sha}, "synthetic": True}
            binary = {"path": str(root / "fake-bifrost"), "sha256": "1" * 64}
            scala = {"receipt": {"path": "synthetic-scala-receipt"}, "artifacts": []}
            qualification = {"path": "synthetic-qualification", "sha256": "2" * 64}
            native = {}
            source_inputs = []
            for role, relative in driver.NATIVE_EVIDENCE_PATHS.items():
                evidence = root / relative
                evidence.parent.mkdir(parents=True, exist_ok=True)
                evidence.write_text(f"synthetic {role}\n", encoding="utf-8")
                digest = driver._sha_file(evidence)
                native[role] = {"path": relative, "sha256": digest}
                source_inputs.append({"path": relative, "sha256": digest})
            source_inputs.append({
                "path": "src/frozen.rs",
                "sha256": hashlib.sha256(b"source").hexdigest(),
            })
            source_inputs.append({"path": "scripts/bifrost_v0144_benchmark.py",
                                  "sha256": driver._sha_file(driver_copy)})
            source_inputs.extend([
                {"path": driver.RUNNER_BUILD_RECEIPT, "sha256": driver.RUNNER_BUILD_RECEIPT_SHA256},
                {"path": driver.RUNNER_BUILD_INPUTS, "sha256": driver.RUNNER_BUILD_INPUTS_SHA256},
                {"path": driver.RUNNER_BUILD_STDOUT, "sha256": driver.RUNNER_BUILD_STDOUT_SHA256},
                {"path": driver.RUNNER_BUILD_STDERR, "sha256": driver.RUNNER_BUILD_STDERR_SHA256},
            ])

            self.git(root, "add", "src/frozen.rs", "scripts/execute-release-v092.py",
                     "scripts/bifrost_v0144_benchmark.py",
                     *driver.NATIVE_EVIDENCE_PATHS.values())
            self.git(root, "commit", "-m", "freeze source inputs")
            source_commit = self.git(root, "rev-parse", "HEAD")

            groups = driver.project_target_groups(base["groups"], str(runner), binary["path"])
            contract = {
                "schema": driver.CONTRACT_SCHEMA, "schema_version": 1,
                "target_id": driver.TARGET_ID, "release": driver.RELEASE,
                "execution_authorized": True,
                "approval": {"status": "approved", "approved_by": "synthetic", "subject_sha256": ""},
                "approval_subject_sha256": "",
                "resource_policy": copy.deepcopy(driver.RESOURCE_POLICY),
                "attempt_policy": copy.deepcopy(driver.ATTEMPT_POLICY),
                "allowed_runtime_projections": copy.deepcopy(driver.ALLOWED_RUNTIME_PROJECTIONS),
                "parent_population": {
                    "full_counts": {"groups": 84, "report_partitions": 92, "report_rows": 4252,
                                    "population_cases": 1108},
                    "target_bifrost_report_partitions": 20,
                    "target_bifrost_case_references": sum(
                        len(group["case_ids"]) for group in base["groups"]
                        if group.get("tool") == "bifrost"
                    ),
                    "population": "v0.9.0",
                },
                "source_lineage": {
                    "source_commit": source_commit,
                    "reviewed_origin_main": source_commit,
                    "tracking_ref_name": "origin/main",
                    "tracking_ref_commit": source_commit,
                    "source_is_descendant_of_reviewed_origin_main": True,
                    "source_must_be_ancestor_of_later_plan_commit": True,
                },
                "source_snapshot": {
                    "source_commit": source_commit,
                    "source_inputs": source_inputs,
                    "runner_source": {"path": "scripts/bifrost_v0144_benchmark.py",
                                      "sha256": driver._sha_file(driver_copy)},
                    "historical_c4_source_inputs": copy.deepcopy(base.get("source_inputs", [])),
                    "closure_boundary": {
                        "historical_c4_source_inputs_retained_for_capacity_accounting":
                            len(base.get("source_inputs", [])),
                    },
                    "core_helpers": [{"path": "scripts/execute-release-v092.py",
                                      "sha256": driver._sha_file(helper_copy)}],
                },
                "runtime": {
                    "runner": {"path": str(runner), "sha256": runner_sha,
                               "build_receipt": runner_build},
                    "bifrost": binary, "scala_maven": scala,
                    "qualification": qualification,
                    "native_configuration_evidence": native,
                },
                "groups": groups,
                "wall_budget": {
                    "original_global_origin_utc": driver.ORIGINAL_WALL_ORIGIN_UTC,
                    "target_total_deadline_seconds": driver.TARGET_WALL_BUDGET_SECONDS,
                },
                "ledger_anchor": {"line_count": 109, "sha256": "4" * 64},
            }
            contract["approval_subject_sha256"] = driver.approval_subject_sha256(contract)
            contract_path = root / driver.CONTRACT_REL
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_bytes(driver._pretty_json(contract))
            self.git(root, "add", driver.CONTRACT_REL)
            self.git(root, "commit", "-m", "introduce plan")
            plan_commit = self.git(root, "rev-parse", "HEAD")
            (root / "unrelated.txt").write_text("later unrelated head", encoding="utf-8")
            self.git(root, "add", "unrelated.txt")
            self.git(root, "commit", "-m", "advance head without changing plan")
            advanced_head = self.git(root, "rev-parse", "HEAD")
            self.assertNotEqual(advanced_head, plan_commit)

            source_core_sha = driver._sha_file(helper_copy)
            source_core, _ = driver._load_core(ROOT)
            immutable_source_paths = {
                "src/frozen.rs", "scripts/bifrost_v0144_benchmark.py",
                *driver.NATIVE_EVIDENCE_PATHS.values(),
            }

            def read_source_file(repo, commit, relative, expected):
                if relative in immutable_source_paths:
                    return source_core._source_file(repo, commit, relative, expected)
                return b"synthetic pinned build evidence"

            def assert_source_snapshot(repo, commit, helper_sha, source_hashes):
                tracked_source = [item for item in source_hashes
                                  if item["path"] in immutable_source_paths]
                return source_core._assert_source_snapshot(repo, commit, helper_sha, tracked_source)

            fake_core = SimpleNamespace(
                _source_file=read_source_file,
                _assert_source_snapshot=assert_source_snapshot,
            )
            history = {"ledger": {
                "line_count": 109, "bytes": 1000, "sha256": "4" * 64,
                "target_line_count": 0, "target_suffix_sha256": hashlib.sha256(b"").hexdigest(),
            }}
            digest, qual_binding = "2" * 64, qualification
            with ExitStack() as stack:
                stack.enter_context(patch.object(driver, "SOURCE_BASELINE_COMMIT", source_commit))
                stack.enter_context(patch.object(driver, "_base_inputs",
                                                 return_value=(plan, population, base, parent, all_ids)))
                stack.enter_context(patch.object(driver, "_load_core",
                                                 return_value=(fake_core, source_core_sha)))
                stack.enter_context(patch.object(driver, "_verify_runner_build", return_value=runner_build))
                stack.enter_context(patch.object(driver, "validate_approval", return_value=None))
                stack.enter_context(patch.object(driver, "_verify_bifrost_receipt",
                                                 return_value=({}, binary)))
                stack.enter_context(patch.object(driver, "_verify_scala_receipt",
                                                 return_value=({}, scala)))
                stack.enter_context(patch.object(driver, "_verify_qualification",
                                                 return_value=({}, qual_binding)))
                stack.enter_context(patch.object(driver, "_verify_capture_manifest", return_value=None))
                stack.enter_context(patch.object(driver, "validate_group_projections", return_value=None))
                stack.enter_context(patch.object(driver, "_scan_history", return_value=history))
                stack.enter_context(patch.object(driver, "_assert_history_unchanged", return_value=None))
                validated = driver._validate_contract(root, driver.CONTRACT_REL,
                                                      require_approval=False, require_committed=True)
                self.assertEqual(validated["source_commit"], source_commit)
                self.assertEqual(validated["plan_commit"], plan_commit)
                self.assertEqual(self.git(root, "rev-parse", "HEAD"), advanced_head)

                changed = read_json(contract_path)
                changed["approval"]["approved_by"] = "mutated-after-plan-commit"
                changed["approval_subject_sha256"] = driver.approval_subject_sha256(changed)
                contract_path.write_bytes(driver._pretty_json(changed))
                with self.assertRaisesRegex(driver.BenchmarkError,
                                            "differs from its committed plan or current HEAD readback"):
                    driver._validate_contract(root, driver.CONTRACT_REL,
                                              require_approval=False, require_committed=True)
                contract_path.write_bytes(driver._pretty_json(contract))

                frozen_source_file.write_text("source changed after SOURCE\n", encoding="utf-8")
                driver_copy.write_bytes(driver_copy.read_bytes() + b"\n# successor runtime helper\n")
                self.git(root, "add", "src/frozen.rs", "scripts/bifrost_v0144_benchmark.py")
                self.git(root, "commit", "-m", "change frozen source and runtime helper")
                with self.assertRaisesRegex(
                        RuntimeError,
                        "current C5 target driver differs from the frozen source binding|"
                        "source drift: runner or fixture inputs differ"):
                    driver._validate_contract(root, driver.CONTRACT_REL,
                                              require_approval=False, require_committed=True)
                # Read-only replay must use the runner and helper bytes bound
                # by SOURCE. The same changed working tree is rejected above
                # for any dispatch that checks the current source snapshot.
                historical = driver._validate_contract(
                    root, driver.CONTRACT_REL, require_approval=False,
                    require_committed=True, check_current_source=False,
                )
                self.assertEqual(historical["plan_commit"], plan_commit)
                self.assertEqual(historical["source_commit"], source_commit)


if __name__ == "__main__":
    unittest.main()
