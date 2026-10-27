#!/usr/bin/env python3
"""Synthetic, local-only tests for the original-source history helper."""

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
from contextlib import nullcontext
from types import SimpleNamespace
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_history_under_test", HERE / "source_history.py")
assert SPEC is not None and SPEC.loader is not None
history = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(history)


def git(
    path: Path,
    *args: str,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_CONFIG_") or key in {"GIT_DIR", "GIT_WORK_TREE", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}:
            env.pop(key, None)
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Source History Test",
        "GIT_AUTHOR_EMAIL": "source-history@example.invalid",
        "GIT_COMMITTER_NAME": "Source History Test",
        "GIT_COMMITTER_EMAIL": "source-history@example.invalid",
    })
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(path), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if check and result.returncode:
        raise AssertionError((args, result.returncode, result.stderr.decode("utf-8", "replace")))
    return result


def commit(path: Path, message: str) -> str:
    git(path, "add", "-A")
    git(path, "commit", "-m", message)
    return git(path, "rev-parse", "HEAD").stdout.decode().strip()


class SourceHistoryFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="v092-source-history-test-")
        self.addCleanup(self.temp.cleanup)
        self.tmp = Path(self.temp.name)
        self.root = self.tmp / "current"
        self.source = self.tmp / "source"
        self.main_archive = self.tmp / "main-archive.git"
        self.archive_root = self.root / history.MANIFEST_RELATIVE.parent
        self.archive_root.mkdir(parents=True)

        git(self.root, "init", "-b", "main")
        (self.root / "README.md").write_text("new main base\n", encoding="utf-8")
        self.new_base = commit(self.root, "new main base")
        (self.root / "feature.txt").write_text("rebased feature\n", encoding="utf-8")
        self.feature = commit(self.root, "rebased feature")

        self.source.mkdir()
        git(self.source, "init", "-b", "main")
        (self.source / "src").mkdir()
        (self.source / "src/lib.rs").write_text("pub fn old() -> bool { true }\n", encoding="utf-8")
        (self.source / "scripts").mkdir()
        (self.source / "scripts/execute-release-v092.py").write_text("# original runner\n", encoding="utf-8")
        (self.source / "extra").mkdir()
        (self.source / "extra/input.txt").write_text("bound source input\n", encoding="utf-8")
        (self.source / "README.md").write_text("original README\n", encoding="utf-8")
        self.base = commit(self.source, "archive base")
        (self.source / "README.md").write_text("pre-rebase main\n", encoding="utf-8")
        self.pre_main = commit(self.source, "pre-rebase main")
        (self.source / "scripts/execute-release-v092.py").write_text("# core source runner\n", encoding="utf-8")
        self.core = commit(self.source, "core source")
        (self.source / "src/lib.rs").write_text("pub fn original_source() -> bool { true }\n", encoding="utf-8")
        self.original = commit(self.source, "original source head")

        git(self.source, "update-ref", "refs/heads/dave/v092-before-main-history-rebase-20261026", self.pre_main)
        git(self.source, "update-ref", "refs/heads/dave/v092-before-pr295-rebase-20261026", self.original)
        self.bundle = self.tmp / "source.bundle"
        git(
            self.source,
            "bundle", "create", str(self.bundle),
            "refs/heads/dave/v092-before-main-history-rebase-20261026",
            "refs/heads/dave/v092-before-pr295-rebase-20261026",
        )
        self.bundle_bytes = self.bundle.read_bytes()
        self.bundle_sha = hashlib.sha256(self.bundle_bytes).hexdigest()
        self.parts = [self.bundle_bytes]
        self.part_sha = hashlib.sha256(self.bundle_bytes).hexdigest()
        (self.archive_root / "original-source.bundle.part0000").write_bytes(self.bundle_bytes)

        git(self.main_archive.parent, "init", "--bare", str(self.main_archive))
        git(
            self.main_archive,
            "fetch", "--no-tags", "--no-write-fetch-head", str(self.source),
            f"refs/heads/dave/v092-before-main-history-rebase-20261026:refs/remotes/origin/main",
        )

        self.ref_map = {
            "refs/heads/dave/v092-before-main-history-rebase-20261026": self.pre_main,
            "refs/heads/dave/v092-before-pr295-rebase-20261026": self.original,
        }
        self.main_bundle_sha = "a" * 64
        self.helper_sha = "b" * 64
        self.patchers = [
            mock.patch.object(history, "PINNED_ORIGINAL_MAIN", self.pre_main),
            mock.patch.object(history, "PINNED_ORIGINAL_SOURCE", self.original),
            mock.patch.object(history, "PINNED_ORIGINAL_CORE_SOURCE", self.core),
            mock.patch.object(history, "PINNED_PR295_REBASED", self.original),
            mock.patch.object(history, "PINNED_PRE_REBASE_MAIN", self.pre_main),
            mock.patch.object(history, "PINNED_REBASED_FEATURE_HEAD", self.feature),
            mock.patch.object(history, "PINNED_NEW_MAIN_BASE", self.new_base),
            mock.patch.object(history, "PINNED_ORIGINAL_MAIN_ARCHIVE", self.pre_main),
            mock.patch.object(history, "PINNED_SOURCE_BUNDLE_SHA256", self.bundle_sha),
            mock.patch.object(history, "PINNED_SOURCE_BUNDLE_BYTES", len(self.bundle_bytes)),
            mock.patch.object(history, "PINNED_MAIN_ARCHIVE_BUNDLE_SHA256", self.main_bundle_sha),
            mock.patch.object(history, "PINNED_HISTORICAL_HELPER_SHA256", self.helper_sha),
            mock.patch.object(history, "PINNED_SOURCE_REFS", self.ref_map),
            mock.patch.object(history, "PINNED_PREREQUISITES", ()),
            mock.patch.object(history, "PART_LIMIT", max(history.PART_LIMIT, len(self.bundle_bytes))),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.manifest = {
            "schema_version": history.SCHEMA_VERSION,
            "original_main": self.pre_main,
            "original_core_source": self.core,
            "rebased_feature_head": self.feature,
            "new_main_base": self.new_base,
            "original_source_refs": self.ref_map,
            "main_archive": {
                "manifest_path": history.MAIN_ARCHIVE_MANIFEST.as_posix(),
                "bundle_sha256": self.main_bundle_sha,
                "original_main": self.pre_main,
            },
            "bundle": {
                "sha256": self.bundle_sha,
                "bytes": len(self.bundle_bytes),
                "parts": [{
                    "path": "original-source.bundle.part0000",
                    "sha256": self.part_sha,
                    "bytes": len(self.bundle_bytes),
                }],
            },
        }
        self.write_manifest()
        self.main_archive_binding = {
            "manifest_path": history.MAIN_ARCHIVE_MANIFEST.as_posix(),
            "bundle_sha256": self.main_bundle_sha,
            "original_main": self.pre_main,
        }
        self.main_archive_patch = mock.patch.object(
            history,
            "_verified_main_archive",
            return_value=(self.main_archive, self.main_archive_binding),
        )
        self.main_archive_patch.start()
        self.addCleanup(self.main_archive_patch.stop)

    def write_manifest(self) -> None:
        path = self.root / history.MANIFEST_RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.manifest, sort_keys=True) + "\n", encoding="utf-8")

    def call_view(self, paths: tuple[str, ...] = ("extra/input.txt",)) -> dict:
        return history.historical_source_view(self.root, history.MANIFEST_RELATIVE, paths)

    def test_object_import_does_not_change_refs_fetch_head_or_ancestry(self) -> None:
        before_refs = git(self.root, "for-each-ref", "--format=%(refname) %(objectname)").stdout
        head_before = git(self.root, "rev-parse", "HEAD").stdout
        self.assertFalse((self.root / ".git/FETCH_HEAD").exists())

        receipt = history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

        self.assertTrue(receipt["verified"])
        self.assertFalse(receipt["current_ancestor_claim"])
        self.assertEqual(git(self.root, "for-each-ref", "--format=%(refname) %(objectname)").stdout, before_refs)
        self.assertEqual(git(self.root, "rev-parse", "HEAD").stdout, head_before)
        self.assertFalse((self.root / ".git/FETCH_HEAD").exists())
        self.assertEqual(git(self.root, "cat-file", "-t", self.original).stdout.strip(), b"commit")
        self.assertEqual(git(self.root, "merge-base", "--is-ancestor", self.original, "HEAD", check=False).returncode, 1)
        self.assertFalse((self.root / ".git/objects/info/alternates").exists())

    def test_any_old_history_merge_parent_is_rejected(self) -> None:
        git(
            self.root,
            "fetch", "--keep", "--no-tags", "--no-write-fetch-head", str(self.source),
            "refs/heads/dave/v092-before-main-history-rebase-20261026",
            "refs/heads/dave/v092-before-pr295-rebase-20261026",
        )
        for historical in (self.pre_main, self.core, self.original, self.base):
            pin_context = (
                mock.patch.object(history, "PINNED_PREREQUISITES", (historical,))
                if historical == self.base
                else nullcontext()
            )
            with pin_context:
                tree = git(self.root, "rev-parse", f"{self.feature}^{{tree}}").stdout.decode().strip()
                merge = git(
                    self.root,
                    "commit-tree", tree, "-p", self.feature, "-p", historical,
                    input_bytes=b"synthetic old-history merge\n",
                ).stdout.decode().strip()
                git(self.root, "update-ref", "refs/heads/main", merge)
                with self.assertRaisesRegex(history.SourceHistoryError, "historical source commit is an ancestor"):
                    history._load_verified(self.root, history.MANIFEST_RELATIVE)
                git(self.root, "update-ref", "refs/heads/main", self.feature)

    def test_graft_cannot_hide_raw_old_merge_parent_from_ancestry_gate(self) -> None:
        git(
            self.root,
            "fetch", "--keep", "--no-tags", "--no-write-fetch-head", str(self.source),
            "refs/heads/dave/v092-before-main-history-rebase-20261026",
            "refs/heads/dave/v092-before-pr295-rebase-20261026",
        )
        tree = git(self.root, "rev-parse", f"{self.feature}^{{tree}}").stdout.decode().strip()
        raw_merge = git(
            self.root,
            "commit-tree", tree, "-p", self.feature, "-p", self.original,
            input_bytes=b"synthetic raw old-history merge\n",
        ).stdout.decode().strip()
        git(self.root, "update-ref", "refs/heads/main", raw_merge)

        info = self.root / ".git/info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "grafts").write_text(f"{raw_merge} {self.feature}\n", encoding="ascii")
        # Demonstrate why checking for graph overrides must precede merge-base:
        # Git now hides the raw second parent and reports no historical ancestry.
        self.assertEqual(
            git(self.root, "merge-base", "--is-ancestor", self.original, "HEAD", check=False).returncode,
            1,
        )
        with self.assertRaisesRegex(history.SourceHistoryError, "graft or shallow override"):
            history._load_verified(self.root, history.MANIFEST_RELATIVE)

    def test_current_graft_and_shallow_override_paths_are_refused(self) -> None:
        gitdir = Path(git(self.root, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        candidates = (
            gitdir / "info/grafts",
            gitdir / "objects/info/grafts",
            gitdir / "shallow",
        )
        for candidate in candidates:
            with self.subTest(path=candidate.relative_to(gitdir)):
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text("synthetic ancestry override\n", encoding="ascii")
                with self.assertRaisesRegex(history.SourceHistoryError, "graft or shallow override"):
                    history._load_verified(self.root, history.MANIFEST_RELATIVE)
                candidate.unlink()

    def test_current_graft_and_shallow_symlinks_are_refused(self) -> None:
        gitdir = Path(git(self.root, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        outside = self.tmp / "outside-git-metadata"
        outside.write_text("not trusted\n", encoding="ascii")
        candidates = (
            gitdir / "info/grafts",
            gitdir / "objects/info/grafts",
            gitdir / "shallow",
        )
        for candidate in candidates:
            with self.subTest(path=candidate.relative_to(gitdir)):
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.symlink_to(outside)
                with self.assertRaises(history.SourceHistoryError):
                    history._load_verified(self.root, history.MANIFEST_RELATIVE)
                candidate.unlink()

    def test_linked_worktree_common_grafts_are_refused(self) -> None:
        linked = self.tmp / "linked-current"
        git(self.root, "worktree", "add", "--detach", str(linked), self.feature)
        gitdir = Path(git(linked, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        common = Path(git(linked, "rev-parse", "--git-common-dir").stdout.decode().strip())
        self.assertNotEqual(gitdir, common)

        graft = common / "info/grafts"
        graft.parent.mkdir(parents=True, exist_ok=True)
        graft.write_text("synthetic common-dir graft\n", encoding="ascii")
        with self.assertRaisesRegex(history.SourceHistoryError, "graft or shallow override"):
            history._assert_current_graph_metadata_safe(linked, gitdir=gitdir)

    def test_historical_view_is_at_original_commit_with_exact_source_bytes(self) -> None:
        receipt = self.call_view()
        view = Path(receipt["view_root"])

        self.assertEqual(receipt["view_head"], self.original)
        self.assertFalse(receipt["current_ancestor_claim"])
        self.assertEqual(git(view, "rev-parse", "HEAD").stdout.decode().strip(), self.original)
        self.assertEqual(
            git(view, "show", f"{self.original}:src/lib.rs").stdout,
            b"pub fn original_source() -> bool { true }\n",
        )
        self.assertEqual((view / "extra/input.txt").read_bytes(), b"bound source input\n")
        view_gitdir = Path(git(view, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        self.assertFalse((view_gitdir / "objects/info/alternates").exists())

    def test_historical_core_view_supports_frozen_source_and_ancestry_checks(self) -> None:
        receipt = history.historical_source_view(
            self.root,
            history.MANIFEST_RELATIVE,
            ("extra/input.txt",),
            snapshot_commit=self.core,
        )
        view = Path(receipt["view_root"])

        self.assertEqual(receipt["view_head"], self.core)
        self.assertEqual(receipt["snapshot_kind"], "original-core-source")
        self.assertFalse(receipt["current_ancestor_claim"])
        self.assertEqual(git(view, "rev-parse", "HEAD").stdout.decode().strip(), self.core)
        self.assertEqual(
            git(view, "merge-base", "--is-ancestor", self.core, self.original, check=False).returncode,
            0,
        )
        # The selected frozen source scope is the real 328-like tree, while the
        # later original-source commit has distinct src bytes.
        self.assertEqual(
            git(view, "show", f"{self.core}:scripts/execute-release-v092.py").stdout,
            b"# core source runner\n",
        )
        self.assertEqual(
            (view / "src/lib.rs").read_bytes(),
            b"pub fn old() -> bool { true }\n",
        )
        self.assertEqual(
            git(self.source, "show", f"{self.original}:src/lib.rs").stdout,
            b"pub fn original_source() -> bool { true }\n",
        )
        self.assertIn("src", receipt["selected_source_paths"])
        self.assertIn("scripts", receipt["selected_source_paths"])
        self.assertIn("extra/input.txt", receipt["selected_source_paths"])

    def test_unpinned_historical_snapshot_commit_is_refused(self) -> None:
        with self.assertRaisesRegex(history.SourceHistoryError, "one of the pinned original source commits"):
            history.historical_source_view(
                self.root,
                history.MANIFEST_RELATIVE,
                ("extra/input.txt",),
                snapshot_commit=self.feature,
            )

    def test_wrong_descriptor_ref_is_rejected(self) -> None:
        self.manifest["original_source_refs"]["refs/heads/dave/v092-before-pr295-rebase-20261026"] = self.pre_main
        self.write_manifest()
        with self.assertRaises(history.SourceHistoryError):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_bundle_parts_are_rechecked_even_after_cache_creation(self) -> None:
        history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)
        part = self.archive_root / "original-source.bundle.part0000"
        part.write_bytes(part.read_bytes() + b"tamper")
        with self.assertRaises(history.SourceHistoryError):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_missing_main_archive_prerequisite_fails_closed(self) -> None:
        missing = "f" * 40
        with mock.patch.object(history, "PINNED_PREREQUISITES", (missing,)):
            with mock.patch.object(history, "_bundle_required_objects", return_value=(1, {missing})):
                with self.assertRaisesRegex(history.SourceHistoryError, "lacks bundle prerequisite"):
                    history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_current_repository_url_rewrite_is_refused_before_fetch(self) -> None:
        git(self.root, "config", "--local", "url.https://example.invalid/.insteadOf", str(self.main_archive))
        with self.assertRaisesRegex(history.SourceHistoryError, "URL rewrites"):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_main_archive_refusal_is_propagated(self) -> None:
        with mock.patch.object(history, "_verified_main_archive", side_effect=history.SourceHistoryError("archive missing")):
            with self.assertRaisesRegex(history.SourceHistoryError, "archive missing"):
                history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_main_archive_uses_verified_legacy_base_not_current_freeze(self) -> None:
        self.main_archive_patch.stop()
        rewritten_base = "d" * 40
        archive_manifest = {
            "original_main": self.pre_main,
            "rewritten_base": rewritten_base,
            "bundle": {"sha256": self.main_bundle_sha},
        }
        helper = SimpleNamespace(
            PINNED_REWRITTEN_BASE=rewritten_base,
            _load_archive=mock.Mock(return_value=(self.root, self.tmp / "gitdir", archive_manifest, self.main_archive, self.feature)),
            _verify_current_tags=mock.Mock(),
            _check_filtered_tree=mock.Mock(),
        )
        with mock.patch.object(history, "_load_pinned_historical_helper", return_value=helper):
            archive_repo, binding = history._verified_main_archive(self.root)

        self.assertEqual(archive_repo, self.main_archive)
        helper._verify_current_tags.assert_called_once_with(self.root, archive_manifest)
        helper._check_filtered_tree.assert_called_once_with(
            self.root, self.main_archive, archive_manifest, rewritten_base
        )
        self.assertNotEqual(rewritten_base, self.feature)
        self.assertEqual(binding["original_main"], self.pre_main)

    def test_cache_config_and_alternates_tampering_are_rejected(self) -> None:
        history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)
        gitdir = Path(git(self.root, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        source_repo = gitdir / "original-source-history" / self.bundle_sha / "source.git"
        git(source_repo, "config", "--local", "remote.bad.url", "/tmp/untrusted")
        with self.assertRaisesRegex(history.SourceHistoryError, "unexpected Git cache config"):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_alternates_are_refused(self) -> None:
        history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)
        gitdir = Path(git(self.root, "rev-parse", "--absolute-git-dir").stdout.decode().strip())
        source_repo = gitdir / "original-source-history" / self.bundle_sha / "source.git"
        (source_repo / "objects/info/alternates").write_text("/tmp/elsewhere\n", encoding="utf-8")
        with self.assertRaisesRegex(history.SourceHistoryError, "alternates"):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_descriptor_symlink_is_refused(self) -> None:
        manifest = self.root / history.MANIFEST_RELATIVE
        saved = self.tmp / "manifest.json"
        shutil.copyfile(manifest, saved)
        manifest.unlink()
        manifest.symlink_to(saved)
        with self.assertRaisesRegex(history.SourceHistoryError, "symlink"):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_bundle_part_symlink_is_refused(self) -> None:
        part = self.archive_root / "original-source.bundle.part0000"
        saved = self.tmp / "source-part.bin"
        shutil.copyfile(part, saved)
        part.unlink()
        part.symlink_to(saved)
        with self.assertRaisesRegex(history.SourceHistoryError, "symlink"):
            history.ensure_original_objects(self.root, history.MANIFEST_RELATIVE)

    def test_non_root_path_is_refused(self) -> None:
        subdirectory = self.root / "src"
        subdirectory.mkdir()
        with self.assertRaisesRegex(history.SourceHistoryError, "worktree root"):
            history.ensure_original_objects(subdirectory, history.MANIFEST_RELATIVE)

    def test_path_escape_is_refused(self) -> None:
        with self.assertRaisesRegex(history.SourceHistoryError, "unsafe path"):
            history.historical_source_view(self.root, history.MANIFEST_RELATIVE, ("../../outside.txt",))

    def test_changed_historical_view_is_not_repaired(self) -> None:
        receipt = self.call_view()
        view = Path(receipt["view_root"])
        (view / "src/lib.rs").write_text("modified\n", encoding="utf-8")
        with self.assertRaisesRegex(history.SourceHistoryError, "changed tracked source bytes"):
            self.call_view()
        self.assertEqual((view / "src/lib.rs").read_text(encoding="utf-8"), "modified\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
