from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HELPER_PATH = HERE / "materialize_v0151_swift_configuration_inputs.py"
MANIFEST_PATH = HERE / "swift-configuration-ref-manifest.json"
SPEC = importlib.util.spec_from_file_location("swift_configuration_materializer_test", HELPER_PATH)
assert SPEC is not None and SPEC.loader is not None
MATERIALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATERIALIZER)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *arguments: str, binary: bool = False):
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


class MaterializeSwiftConfigurationInputsTest(unittest.TestCase):
    def _temporary_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory(prefix=".materializer-test-", dir=HERE)
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def _fixture(self) -> tuple[Path, Path, str, str, list[dict], list[str]]:
        root = self._temporary_root()
        _git(root, "init", "-q")
        _git(root, "config", "user.name", "DataFlowBench materializer test")
        _git(root, "config", "user.email", "dataflowbench-materializer-test@example.invalid")
        present_path = "adapters/present/config.json"
        supplement_path = "execution-state/v092/swift-source/patch-application/applied-patch.json"
        present_bytes = b'{"fixture":"present"}\n'
        supplement_bytes = b'{"fixture":"supplement"}\n'
        for relative, data in ((present_path, present_bytes), (supplement_path, supplement_bytes)):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        _git(root, "add", "--", present_path, supplement_path)
        _git(root, "-c", "user.name=DataFlowBench materializer test", "-c",
             "user.email=dataflowbench-materializer-test@example.invalid", "-c",
             "commit.gpgsign=false", "commit", "-qm", "fixture")
        commit = _git(root, "rev-parse", "HEAD")
        tree = _git(root, "rev-parse", "HEAD^{tree}")
        references = []
        for relative, data, state in (
            (present_path, present_bytes, "present"),
            (supplement_path, supplement_bytes, "supplement"),
        ):
            blob = _git(root, "rev-parse", f"{commit}:{relative}")
            references.append({
                "path": relative,
                "sha256": _sha(data),
                "git_blob_sha1": blob,
                "engines": ["codeql"],
                "initial_failed_checkout_state": state,
            })
        checkout = root / "execution-state/v092/validation/fresh"
        checkout.mkdir(parents=True)
        present_target = checkout / present_path
        present_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / present_path, present_target)
        return root, checkout, commit, tree, references, [supplement_path]

    def _materialize(self, root, checkout, commit, tree, references, supplements, evidence):
        invocation = {
            "argv": ["/fixture/dataflowbench", "--population", "v0.9.0", "validate-reports"],
            "cwd": str(checkout),
            "environment": {"PATH": "/usr/bin:/bin"},
        }
        return MATERIALIZER.materialize_missing_refs(
            source_root=root,
            checkout=checkout,
            source_commit=commit,
            source_tree_sha1=tree,
            references=references,
            supplement_paths=supplements,
            evidence_path=evidence,
            materializer_sha256=_sha(HELPER_PATH.read_bytes()),
            manifest_sha256="a" * 64,
            expected_invocation=invocation,
            expected_reference_count=len(references),
        )

    def test_real_locked_closure_hydrates_exactly_22_and_verifies_all_119(self):
        manifest = json.loads(MANIFEST_PATH.read_text())
        old_checkout = ROOT / manifest["failed_validation"]["checkout_relative"]
        temporary = self._temporary_root()
        checkout = temporary / "execution-state/v092/validation/fresh"
        checkout.mkdir(parents=True)
        for item in manifest["references"]:
            if item["initial_failed_checkout_state"] != "present":
                continue
            source = old_checkout / item["path"]
            target = checkout / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        evidence = temporary / "supplement-materialization.json"
        result = MATERIALIZER.materialize_missing_refs(
            source_root=ROOT,
            checkout=checkout,
            source_commit=manifest["source_commit"],
            source_tree_sha1=manifest["source_tree_sha1"],
            references=manifest["references"],
            supplement_paths=manifest["supplement_paths"],
            evidence_path=evidence,
            materializer_sha256=_sha(HELPER_PATH.read_bytes()),
            manifest_sha256=_sha(MANIFEST_PATH.read_bytes()),
            expected_invocation={
                "argv": [manifest["runner"]["path"], "--population", "v0.9.0", "validate-reports"],
                "cwd": str(checkout),
                "environment": {"PATH": "/usr/bin:/bin"},
            },
            expected_reference_count=119,
        )
        self.assertEqual(result["status"], "exact-configuration-closure-materialized")
        self.assertEqual(result["supplement_count"], 22)
        self.assertEqual(result["verified_destination_count"], 119)
        self.assertEqual(len(result["supplements"]), 22)
        for item in manifest["references"]:
            self.assertEqual(_sha((checkout / item["path"]).read_bytes()), item["sha256"])
        self.assertEqual(json.loads(evidence.read_text()), result)

    def test_fixture_materializes_exact_missing_ref(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        evidence = root / "materialization.json"
        result = self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertEqual(result["supplement_count"], 1)
        self.assertEqual(result["configuration_reference_count"], 2)
        self.assertEqual(
            (checkout / supplements[0]).read_bytes(),
            (root / supplements[0]).read_bytes(),
        )

    def test_locked_inspection_binds_original_receipt_and_sparse_checkout(self):
        result = MATERIALIZER.inspect(ROOT)
        self.assertEqual(result["status"], "locked-source-and-original-sparse-checkout-verified")
        self.assertEqual(result["reference_count"], 119)
        self.assertEqual(result["failed_checkout"]["present"], 97)
        self.assertEqual(result["failed_checkout"]["missing"], 22)
        self.assertEqual(
            result["failed_checkout"]["receipt_sha256"],
            json.loads(MANIFEST_PATH.read_text())["failed_validation"]["receipt_sha256"],
        )

    def test_original_failed_receipt_rejects_changed_stderr(self):
        manifest = json.loads(MANIFEST_PATH.read_text())
        failed = manifest["failed_validation"]
        temporary = self._temporary_root()
        for relative in (
            failed["receipt_path"],
            "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-01/stdout.bin",
            "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-01/stderr.bin",
        ):
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        stderr = temporary / "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-01/stderr.bin"
        stderr.write_bytes(stderr.read_bytes() + b"tampered")
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "stderr bytes differ"):
            MATERIALIZER._verify_failed_receipt(temporary, failed)

    def test_helper_receipt_collisions_fail_before_validation_run(self):
        temporary = self._temporary_root()
        collision = temporary / "canonical-postcheck.json"
        collision.write_text("already present")
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "canonical postcheck receipt"):
            MATERIALIZER.require_new_artifact_paths([
                (temporary / "supplement-materialization.json", "supplement materialization receipt"),
                (collision, "canonical postcheck receipt"),
            ])
        self.assertFalse((temporary / "supplement-materialization.json").exists())
        collision.unlink()
        collision.symlink_to(temporary / "missing-target")
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "canonical postcheck receipt"):
            MATERIALIZER.require_new_artifact_paths([(collision, "canonical postcheck receipt")])

    def test_altered_source_bytes_fail_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        (root / supplements[0]).write_bytes(b'{"fixture":"altered"}\n')
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "source-commit blob"):
            self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertFalse((checkout / supplements[0]).exists())
        self.assertFalse(evidence.exists())

    def test_wrong_locked_git_blob_fails_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        references[1]["git_blob_sha1"] = "f" * 40
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "source-commit blob"):
            self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertFalse((checkout / supplements[0]).exists())
        self.assertFalse(evidence.exists())

    def test_path_escape_fails_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        references[1]["path"] = "../escape.json"
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "escapes its root"):
            self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertFalse(evidence.exists())

    def test_destination_symlink_fails_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        target = checkout / supplements[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(checkout / references[0]["path"])
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "symlink"):
            self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertTrue(target.is_symlink())
        self.assertFalse(evidence.exists())

    def test_destination_checkout_root_symlink_fails_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        alias = checkout.parent / "fresh-link"
        alias.symlink_to(checkout, target_is_directory=True)
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "symlink in new validation checkout"):
            self._materialize(root, alias, commit, tree, references, supplements, evidence)
        self.assertTrue(alias.is_symlink())
        self.assertFalse(evidence.exists())

    def test_destination_parent_symlink_fails_before_copy(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        alias_parent = root / "validation-link"
        alias_parent.symlink_to(checkout.parent, target_is_directory=True)
        alias = alias_parent / checkout.name
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "symlink in new validation checkout"):
            self._materialize(root, alias, commit, tree, references, supplements, evidence)
        self.assertTrue(alias_parent.is_symlink())
        self.assertFalse(evidence.exists())

    def test_existing_destination_collision_fails_before_any_write(self):
        root, checkout, commit, tree, references, supplements = self._fixture()
        target = checkout / supplements[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"unexpected pre-existing content")
        evidence = root / "materialization.json"
        with self.assertRaisesRegex(MATERIALIZER.MaterializationError, "pre-existing destination input differs"):
            self._materialize(root, checkout, commit, tree, references, supplements, evidence)
        self.assertEqual(target.read_bytes(), b"unexpected pre-existing content")
        self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
