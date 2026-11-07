#!/usr/bin/env python3
"""Focused offline tests for the fixed Bifrost v0.15.1 C5 successor profile."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import py_compile
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("bifrost_v0151_benchmark.py")
ROOT = SCRIPT.resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def isolated_core():
    return load_module(
        f"bifrost_v0151_core_test_{uuid.uuid4().hex}",
        ROOT / "scripts/bifrost_v0144_benchmark.py",
    )


def valid_profile_document(wrapper) -> dict:
    identity = dict(wrapper.PINNED_IDENTITY)
    evidence = {
        key: f"{index:064x}"
        for index, key in enumerate(sorted(wrapper.EVIDENCE_SHA_KEYS), start=1)
    }
    return {
        "schema": wrapper.PROFILE_SCHEMA,
        "identity": identity,
        "evidence_sha256": evidence,
        "runner_binary_bytes": 12_345_678,
    }


class V0151ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = load_module("bifrost_v0151_wrapper_test", SCRIPT)

    def test_legacy_defaults_remain_v0144(self):
        core = isolated_core()
        self.assertEqual(core.TARGET_ID, "bifrost-v0144-01")
        self.assertEqual(core.BIFROST_VERSION, "0.14.4")
        self.assertEqual(core.SERIES, 3)
        self.assertEqual(core.SERIES_LABEL, "series-03")
        self.assertEqual(core.LEDGER_PREFIX_LINES, 109)
        self.assertEqual(
            core.LEDGER_PREFIX_SHA256,
            "2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851",
        )
        self.assertEqual(core.ATTEMPT_POLICY["series"], 3)
        self.assertEqual(core.TARGET_WALL_BUDGET_SECONDS, 13_592)
        self.assertEqual(core.TARGET_DRIVER_SOURCE_REL, "scripts/bifrost_v0144_benchmark.py")
        self.assertEqual(core.TARGET_TEST_SOURCE_REL, "scripts/test_bifrost_v0144_benchmark.py")

    def test_publication_helpers_join_only_the_successor_source_closure(self):
        helper_paths = {
            "scripts/select-v092-publication-evidence.py",
            "scripts/test-select-v092-publication-evidence.py",
            "scripts/validate-v092-report-configurations.py",
            "scripts/test-validate-v092-report-configurations.py",
            "scripts/joern_v092_publication_projection.py",
            "scripts/joern_normal_reports_v092_projection.py",
            "scripts/test-joern-v092-publication-projection.py",
        }
        legacy = isolated_core()
        self.assertTrue(helper_paths.isdisjoint(legacy._source_input_paths(ROOT, {}, [])))
        current = isolated_core()
        current.configure_target_profile(
            self.wrapper.target_profile_values(valid_profile_document(self.wrapper), current)
        )
        self.assertTrue(helper_paths <= set(current._source_input_paths(ROOT, {}, [])))

    def test_core_loader_executes_exact_source_despite_old_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "core.py"
            source.write_bytes(b'VALUE = "old"\n')
            before = source.stat()
            py_compile.compile(str(source), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            current = b'VALUE = "new"\n'
            source.write_bytes(current)
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
            digest = hashlib.sha256(current).hexdigest()
            name = f"bifrost_v0151_c5_core_{digest[:16]}"
            try:
                with patch.object(self.wrapper, "ROOT", root), \
                        patch.object(self.wrapper, "CORE_SOURCE_REL", "core.py"):
                    loaded = self.wrapper._load_core_module()
                self.assertEqual(loaded.VALUE, "new")
                self.assertEqual(loaded.__verified_source_sha256__, digest)
            finally:
                sys.modules.pop(name, None)

    def test_v0151_profile_is_positive_and_does_not_leak_into_legacy_instance(self):
        legacy_core = isolated_core()
        new_core = isolated_core()
        original_budget = new_core.TARGET_WALL_BUDGET_SECONDS
        original_resource_policy = copy.deepcopy(new_core.RESOURCE_POLICY)
        original_attempt_policy = copy.deepcopy(new_core.ATTEMPT_POLICY)
        original_group_ids = list(new_core.BIFROST_GROUP_IDS)
        original_fixture = new_core.FIXTURE_REVISION
        original_wall_origin = new_core.ORIGINAL_WALL_ORIGIN_UTC
        original_base_contract = new_core.BASE_C4_CONTRACT_SHA256

        profile = self.wrapper.target_profile_values(valid_profile_document(self.wrapper), new_core)
        new_core.configure_target_profile(profile)

        self.assertEqual(new_core.TARGET_ID, "bifrost-v0151-01")
        self.assertEqual(new_core.BIFROST_VERSION, "0.15.1")
        self.assertEqual(new_core.BIFROST_REPORT_VERSION, "bifrost 0.15.1")
        self.assertEqual(new_core.BIFROST_BUILD_IDENTITY, self.wrapper.PINNED_IDENTITY["build_identity"])
        self.assertEqual(new_core.BIFROST_BINARY_SHA256, self.wrapper.PINNED_IDENTITY["binary_sha256"])
        self.assertEqual(new_core.RUNNER_BINARY_BYTES, 12_345_678)
        self.assertEqual(new_core.BIFROST_ARCHIVE_SHA256, self.wrapper.PINNED_IDENTITY["archive_sha256"])
        self.assertEqual(new_core.BIFROST_CATALOG_SHA256, self.wrapper.PINNED_IDENTITY["catalog_sha256"])
        self.assertEqual(new_core.PUBLIC_BIFROST_TAG_COMMIT, self.wrapper.PINNED_IDENTITY["public_tag_commit"])
        self.assertEqual(new_core.SERIES, 4)
        self.assertEqual(new_core.SERIES_LABEL, "series-04")
        self.assertEqual(new_core.LEDGER_PREFIX_LINES, 131)
        self.assertEqual(
            new_core.LEDGER_PREFIX_SHA256,
            "2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199",
        )
        self.assertEqual(new_core.CONTRACT_REL,
                         "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json")
        self.assertEqual(new_core.TARGET_DRIVER_SOURCE_REL, "scripts/bifrost_v0151_benchmark.py")
        self.assertEqual(new_core.TARGET_TEST_SOURCE_REL, "scripts/test_bifrost_v0151_benchmark.py")
        self.assertEqual(new_core.CORE_SOURCE_REL, "scripts/bifrost_v0144_benchmark.py")
        self.assertEqual(new_core.PROFILE_SOURCE_REL, self.wrapper.PROFILE_REL)

        self.assertEqual(new_core.TARGET_WALL_BUDGET_SECONDS, original_budget)
        self.assertEqual(new_core.RESOURCE_POLICY, original_resource_policy)
        self.assertEqual(list(new_core.BIFROST_GROUP_IDS), original_group_ids)
        self.assertEqual(len(new_core.BIFROST_GROUP_IDS), 20)
        self.assertEqual(new_core.FIXTURE_REVISION, original_fixture)
        self.assertEqual(new_core.ORIGINAL_WALL_ORIGIN_UTC, original_wall_origin)
        self.assertEqual(new_core.BASE_C4_CONTRACT_SHA256, original_base_contract)
        for field in set(original_attempt_policy) - {"series", "series_label"}:
            self.assertEqual(new_core.ATTEMPT_POLICY[field], original_attempt_policy[field])
        self.assertEqual(new_core.ATTEMPT_POLICY["series"], 4)
        self.assertEqual(new_core.ATTEMPT_POLICY["series_label"], "series-04")

        self.assertEqual(legacy_core.TARGET_ID, "bifrost-v0144-01")
        self.assertEqual(legacy_core.SERIES, 3)
        self.assertEqual(legacy_core.LEDGER_PREFIX_LINES, 109)

    def test_profile_rejects_wrong_version_and_build_identity(self):
        original = valid_profile_document(self.wrapper)
        wrong_version = copy.deepcopy(original)
        wrong_version["identity"]["version"] = "0.15.0"
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "version"):
            self.wrapper.validate_profile_document(wrong_version)

        wrong_build = copy.deepcopy(original)
        wrong_build["identity"]["build_identity"] = "f" * 40
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "build_identity"):
            self.wrapper.validate_profile_document(wrong_build)

    def test_profile_rejects_identity_or_digest_near_misses(self):
        wrong_catalog = valid_profile_document(self.wrapper)
        wrong_catalog["identity"]["catalog_sha256"] = "f" * 64
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "catalog"):
            self.wrapper.validate_profile_document(wrong_catalog)

        wrong_archive = valid_profile_document(self.wrapper)
        wrong_archive["identity"]["archive_sha256"] = "f" * 64
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "archive_sha256"):
            self.wrapper.validate_profile_document(wrong_archive)

        incomplete = valid_profile_document(self.wrapper)
        del incomplete["evidence_sha256"]["runner_build_stdout"]
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "digest roster"):
            self.wrapper.validate_profile_document(incomplete)

        redirected = valid_profile_document(self.wrapper)
        redirected["path"] = "reports/releases/v0.9.2/other.json"
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "top-level fields"):
            self.wrapper.validate_profile_document(redirected)

        wrong_size = valid_profile_document(self.wrapper)
        wrong_size["runner_binary_bytes"] = True
        with self.assertRaisesRegex(self.wrapper.TargetProfileError, "byte count"):
            self.wrapper.validate_profile_document(wrong_size)

    def test_shared_core_rejects_execution_policy_overrides(self):
        core = isolated_core()
        for disallowed in (
            {"TARGET_WALL_BUDGET_SECONDS": 1},
            {"RESOURCE_POLICY": {}},
            {"BIFROST_GROUP_IDS": []},
            {"ORIGINAL_WALL_ORIGIN_UTC": "2026-11-05T00:00:00+00:00"},
            {"ATTEMPT_POLICY": {"new_target_slots_per_group": 99}},
        ):
            with self.subTest(disallowed=disallowed):
                with self.assertRaisesRegex(core.BenchmarkError, "unknown fields"):
                    core.make_target_profile(disallowed)

    def test_target_profile_container_is_immutable_and_closed(self):
        core = isolated_core()
        profile = self.wrapper.target_profile_values(valid_profile_document(self.wrapper), core)
        with self.assertRaises(TypeError):
            profile.values["SERIES"] = 99
        bad_profile = core.TargetProfile({"SERIES": 4})
        with self.assertRaisesRegex(core.BenchmarkError, "incomplete"):
            core.configure_target_profile(bad_profile)

    def test_runner_binary_receipt_and_file_sizes_are_bound(self):
        core = isolated_core()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary_rel = "synthetic/release/dataflowbench"
            binary_path = root / binary_rel
            binary_path.parent.mkdir(parents=True)
            binary_path.write_bytes(b"runner")
            digest = hashlib.sha256(b"runner").hexdigest()
            with patch.object(core, "RUNNER_PATH_DEFAULT", binary_rel), \
                    patch.object(core, "RUNNER_BINARY_SHA256", digest), \
                    patch.object(core, "RUNNER_BINARY_BYTES", 6):
                binding = {"path": binary_rel, "sha256": digest, "bytes": 6}
                self.assertEqual(
                    core._verify_runner_binary_binding(root, binding, binary_path),
                    binary_path,
                )

                wrong_receipt_size = dict(binding, bytes=5)
                with self.assertRaisesRegex(core.BenchmarkError, "receipt identifies"):
                    core._verify_runner_binary_binding(root, wrong_receipt_size, binary_path)

                binary_path.write_bytes(b"changed-size")
                with patch.object(core, "_sha_file", return_value=digest):
                    with self.assertRaisesRegex(core.BenchmarkError, "recorded build artifact"):
                        core._verify_runner_binary_binding(root, binding, binary_path)


if __name__ == "__main__":
    unittest.main()
