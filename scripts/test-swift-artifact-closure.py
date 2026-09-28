#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path

from swift_artifact_closure import (
    ArtifactClosureError,
    COMPLETE,
    INCOMPLETE,
    compare,
    snapshot,
)


class ArtifactClosure(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "artifacts"
        self.root.mkdir()

    def symlink(self, target, link):
        os.symlink(target, self.root / link)

    def test_internal_swiftc_to_swift_driver_link_is_recorded_literally(self):
        (self.root / "swift-driver").write_bytes(b"compiler driver")
        self.symlink("swift-driver", "swiftc")

        manifest = snapshot(self.root)
        by_path = {entry["path"]: entry for entry in manifest["entries"]}
        self.assertEqual(by_path["swiftc"]["kind"], "symlink")
        self.assertEqual(by_path["swiftc"]["target"], "swift-driver")
        self.assertEqual(by_path["swift-driver"]["kind"], "regular-file")
        self.assertIn("stability-and-containment-unproven", manifest["snapshot_semantics"])

    def test_escape_dangling_and_cycle_links_are_rejected(self):
        cases = [
            ("../outside", "escape"),
            ("missing", "dangling"),
        ]
        for target, name in cases:
            with self.subTest(name=name):
                self.symlink(target, name)
                with self.assertRaises(ArtifactClosureError) as raised:
                    snapshot(self.root)
                self.assertEqual(raised.exception.status, INCOMPLETE)
                (self.root / name).unlink()

        self.symlink("cycle-b", "cycle-a")
        self.symlink("cycle-a", "cycle-b")
        with self.assertRaisesRegex(ArtifactClosureError, "cycle"):
            snapshot(self.root)

    def test_internal_directory_symlink_is_inventoried_without_traversal(self):
        (self.root / "real-dir").mkdir()
        (self.root / "real-dir" / "payload").write_text("data")
        self.symlink("real-dir", "dir-alias")

        manifest = snapshot(self.root)
        by_path = {entry["path"]: entry for entry in manifest["entries"]}
        self.assertEqual(by_path["dir-alias"]["kind"], "symlink")
        self.assertEqual(by_path["dir-alias"]["target"], "real-dir")
        self.assertIn("real-dir/payload", by_path)
        self.assertNotIn("dir-alias/payload", by_path)

    def test_directory_symlink_to_ancestor_is_rejected_as_walk_cycle(self):
        (self.root / "nested").mkdir()
        self.symlink("..", "nested/up")
        with self.assertRaisesRegex(ArtifactClosureError, "cycle"):
            snapshot(self.root)

    def test_absolute_target_keeps_parent_component_after_symlink(self):
        (self.root / "b" / "c").mkdir(parents=True)
        (self.root / "b" / "x").write_text("resolved through a")
        self.symlink("b/c", "a")
        self.symlink(str(self.root / "a" / ".." / "x"), "absolute-link")

        manifest = snapshot(self.root)
        self.assertEqual(
            {entry["path"]: entry for entry in manifest["entries"]}["absolute-link"]["target"],
            str(self.root / "a" / ".." / "x"),
        )

    def test_regular_file_cannot_be_intermediate_even_before_parent_component(self):
        (self.root / "regular").write_text("not a directory")
        self.symlink("regular/child", "child-link")
        with self.assertRaisesRegex(ArtifactClosureError, "non-directory"):
            snapshot(self.root)
        (self.root / "child-link").unlink()
        self.symlink("regular/../regular", "parent-link")
        with self.assertRaisesRegex(ArtifactClosureError, "non-directory"):
            snapshot(self.root)

    def test_symlinked_root_is_rejected(self):
        alias = self.root.parent / "root-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ArtifactClosureError, "root must be a real directory"):
            snapshot(alias)

    def test_compare_reports_added_changed_and_removed_entries(self):
        (self.root / "kept").write_text("before")
        (self.root / "removed").write_text("gone")
        before = snapshot(self.root)

        (self.root / "kept").write_text("after")
        (self.root / "removed").unlink()
        (self.root / "added").write_text("new")
        after = snapshot(self.root)
        delta = compare(before, after)

        self.assertEqual(delta["status"], INCOMPLETE)
        self.assertEqual([row["path"] for row in delta["added"]], ["added"])
        self.assertEqual([row["path"] for row in delta["changed"]], ["kept"])
        self.assertEqual([row["path"] for row in delta["removed"]], ["removed"])
        self.assertIn("stability-and-containment-unproven", delta["snapshot_semantics"])

    def test_new_directory_and_late_child_are_explicit_additions(self):
        before = snapshot(self.root)
        (self.root / "late-dir").mkdir()
        (self.root / "late-dir" / "late-file").write_text("late")

        delta = compare(before, snapshot(self.root))
        self.assertEqual(delta["status"], INCOMPLETE)
        self.assertEqual(
            [row["path"] for row in delta["added"]],
            ["late-dir", "late-dir/late-file"],
        )

    def test_compare_allows_cloned_roots_and_compares_entry_closure(self):
        (self.root / "file").write_text("same")
        before = snapshot(self.root)
        clone = self.root.parent / "clone"
        clone.mkdir()
        (clone / "file").write_text("same")

        delta = compare(before, snapshot(clone))
        self.assertEqual(delta["status"], COMPLETE)
        self.assertNotEqual(delta["before_root"], delta["after_root"])

    def test_identical_observations_are_complete_but_not_containment_proof(self):
        (self.root / "file").write_text("same")
        before = snapshot(self.root)
        delta = compare(before, snapshot(self.root))

        self.assertEqual(delta["status"], COMPLETE)
        self.assertIn("containment-unproven", delta["snapshot_semantics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
