#!/usr/bin/env python3
"""Exercise review semantics against retained schema-6 controls.

The installed-binary SHA check uses the retained acquisition identity as a
unit-test witness so these assertions run in a fresh checkout without the
macOS-installed executable. This does not verify a fresh binary or qualify a
production review; all captured manifests, streams, reports and proof checks
remain real and unmocked.
"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v092_review", HERE / "review-v092-bifrost-controls.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
restore_spec = importlib.util.spec_from_file_location(
    "v092_restore_control_cache", HERE / "restore-v092-control-cache.py")
restore_cache = importlib.util.module_from_spec(restore_spec)
restore_spec.loader.exec_module(restore_cache)


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        attempt = self.root.joinpath(*restore_cache.ATTEMPT.parts)
        attempt.mkdir(parents=True)
        source_manifest = review.ROOT.joinpath(*restore_cache.MANIFEST.parts)
        shutil.copyfile(source_manifest, attempt / "artifact-hashes.json")
        self.bundle = review.ROOT / restore_cache.BUNDLE

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_checkout_restores_only_manifest_verified_cache_files(self):
        result = restore_cache.restore(self.root, self.bundle)
        self.assertEqual(result["status"], "verified-and-restored")
        self.assertEqual(result["cache_files"], 8)
        self.assertEqual(result["restored_files"], 8)
        self.assertEqual(result["qualification_claim"], False)
        attempt = self.root.joinpath(*restore_cache.ATTEMPT.parts)
        for relative, (size, sha) in restore_cache.EXPECTED.items():
            path = attempt / relative
            self.assertEqual(path.stat().st_size, size)
            self.assertEqual(restore_cache._sha(path), sha)

    def test_mismatching_existing_cache_is_never_overwritten(self):
        attempt = self.root.joinpath(*restore_cache.ATTEMPT.parts)
        relative = next(iter(restore_cache.EXPECTED))
        target = attempt / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b"preserve this mismatch")
        with self.assertRaisesRegex(ValueError, "refusing overwrite"):
            restore_cache.restore(self.root, self.bundle)
        self.assertEqual(target.read_bytes(), b"preserve this mismatch")
        self.assertFalse(any((attempt / path).exists()
                             for path in list(restore_cache.EXPECTED)[1:]))

    def test_tampered_bundle_fails_before_restoring_any_file(self):
        bad_bundle = self.root / "tampered-bundle"
        shutil.copytree(self.bundle, bad_bundle)
        part = bad_bundle / "detail.tar.gz.part0000"
        payload = bytearray(part.read_bytes())
        payload[len(payload) // 2] ^= 1
        part.write_bytes(payload)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            restore_cache.restore(self.root, bad_bundle)
        attempt = self.root.joinpath(*restore_cache.ATTEMPT.parts)
        self.assertFalse(any((attempt / path).exists() for path in restore_cache.EXPECTED))


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CI checkouts omit the ignored cache. Restore only if absent; the helper
        # verifies the archive and source manifest and preserves matching files.
        restore_cache.restore(review.ROOT)

    def identity_hash_mock(self, witness=None):
        identity_path = review.ROOT / "reports/releases/v0.9.2/acquisition/bifrost-binary.json"
        identity = json.loads(identity_path.read_text())
        installed_path = Path(identity["path"])
        real_sha = review.sha
        # The default is the exact retained identity witness. Tests can pass an
        # intentionally wrong witness to prove production review still rejects it.
        retained_witness = identity["sha256"] if witness is None else witness

        def unit_identity_sha(path):
            # Unit semantics only: stand in for the unavailable installed macOS
            # binary hash. No other digest in the review is replaced.
            if path == installed_path:
                return retained_witness
            return real_sha(path)
        return unit_identity_sha

    def run_review(self, witness=None):
        identity_sha = self.identity_hash_mock(witness)
        with patch.object(review, "sha", side_effect=identity_sha):
            return review.review()

    def altered(self, case_name, mutate):
        prior = review.module("v092_test_prior", "review-bifrost-v013-controls.py")
        original = prior.qualifier._load_report

        def decode(path):
            result = original(path)
            if path.name == case_name + ".json":
                result = copy.deepcopy(result)
                mutate(result)
            return result

        prior.qualifier._load_report = decode
        with patch.object(review, "module", return_value=prior), \
                patch.object(review, "sha", side_effect=self.identity_hash_mock()):
            return review.review()

    def test_real_partial_runs_stay_inconclusive(self):
        result = self.run_review()
        self.assertEqual(result["status"], "measurement-with-known-limits")
        self.assertFalse(result["full_policy_qualification"])
        partial = [row for row in result["controls"] if row["interpretation"] == "inconclusive"]
        self.assertEqual(len(partial), 3)
        self.assertTrue(all(row["clean"] is False for row in partial))

    def test_wrong_installed_binary_hash_witness_still_rejects(self):
        with self.assertRaisesRegex(ValueError, "binary changed"):
            self.run_review("0" * 64)

    def test_unreviewed_obligation_rejects_measurement(self):
        def mutate(report):
            report["runs"][0]["obligations"] = [{"kind": "unresolved_call"}]
        with self.assertRaisesRegex(ValueError, "unreviewed schema-6 obligations"):
            self.altered("policy-java-declared-source-positive-with", mutate)

    def test_partial_scope_cannot_be_dropped(self):
        def mutate(report):
            report["runs"][0]["completion"].pop("scope")
        with self.assertRaisesRegex(ValueError, "unexpected partial scope"):
            self.altered("policy-javascript-declared-source-positive-with", mutate)

    def test_positive_proof_cannot_be_downgraded_silently(self):
        def mutate(report):
            report["runs"][0]["findings"][0]["proof"]["state"] = "unproven"
        with self.assertRaisesRegex(ValueError, "finding is not proven"):
            self.altered("policy-javascript-declared-source-positive-with", mutate)


if __name__ == "__main__":
    unittest.main()
