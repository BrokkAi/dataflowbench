#!/usr/bin/env python3
"""Focused boundary and failure-preservation tests for v092_disk_guard."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("v092_disk_guard.py")
SPEC = importlib.util.spec_from_file_location("v092_disk_guard", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
disk_guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(disk_guard)


class DiskGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make_guard(self, free_bytes=10_000, **overrides):
        def usage(_path):
            return free_bytes() if callable(free_bytes) else free_bytes

        config = {
            "launch_floor_bytes": 110,
            "protected_reserve_bytes": 40,
            "stop_margin_bytes": 8,
            "scratch_ceiling_bytes": 1_000,
            "retention_ceiling_bytes": 1_000,
            "working_ceiling_bytes": 1_000,
        }
        config.update(overrides)
        return disk_guard.DiskGuard(disk_usage=usage, **config)

    def test_budget_inputs_reject_negative_boolean_and_non_integer_values(self):
        for value in (-1, True, 1.5, "12"):
            with self.subTest(value=value):
                with self.assertRaises(disk_guard.DiskGuardError) as caught:
                    self.make_guard(working_ceiling_bytes=value)
                self.assertEqual(caught.exception.code, "invalid_budget")

        guard = self.make_guard()
        for value in (-1, True, 2.5):
            with self.subTest(projected=value):
                with self.assertRaises(disk_guard.DiskGuardError) as caught:
                    guard.check(projected_bytes=value, category="working")
                self.assertEqual(caught.exception.code, "invalid_budget")

    def test_overlapping_roots_and_hardlinks_are_counted_once(self):
        outer = self.root / "outer"
        nested = outer / "nested"
        nested.mkdir(parents=True)
        original = nested / "evidence.bin"
        original.write_bytes(b"1234567890")
        hardlink = self.root / "same-inode.bin"
        try:
            os.link(original, hardlink)
        except OSError as exc:
            self.skipTest(f"hard links unavailable: {exc}")

        measured = disk_guard.DiskGuard.logical_size([outer, nested, hardlink])
        self.assertEqual(measured, 10)

    def test_accounting_skips_nested_symlinks_without_following_their_targets(self):
        tracked = self.root / "tracked"
        tracked.mkdir()
        (tracked / "owned.bin").write_bytes(b"owned")
        external = self.root / "external.bin"
        external.write_bytes(b"outside")
        try:
            (tracked / "sdk-link.h").symlink_to(external)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        self.assertEqual(disk_guard.DiskGuard.logical_size([tracked]), 5)
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.DiskGuard.logical_size([tracked / "sdk-link.h"])
        self.assertEqual(caught.exception.code, "symlink_accounting_path")

    def test_accounting_skips_nested_unix_sockets(self):
        tracked = self.root / "tracked-socket"
        tracked.mkdir()
        (tracked / "owned.bin").write_bytes(b"owned")
        socket_path = tracked / "pysa.sock"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        try:
            listener.bind(str(socket_path))
        except OSError as exc:
            self.skipTest(f"Unix-domain sockets unavailable: {exc}")

        self.assertEqual(disk_guard.DiskGuard.logical_size([tracked]), 5)

    def test_accounting_skips_entries_removed_during_a_tree_walk(self):
        tracked = self.root / "tracked-race"
        tracked.mkdir()
        disappearing = tracked / "temporary.bin"
        disappearing.write_bytes(b"temporary")

        class DisappearingEntry:
            path = str(disappearing)

            def stat(self, *, follow_symlinks: bool):
                disappearing.unlink(missing_ok=True)
                raise FileNotFoundError(self.path)

        with patch.object(disk_guard.os, "scandir", return_value=[DisappearingEntry()]):
            self.assertEqual(disk_guard.DiskGuard.logical_size([tracked]), 0)
        self.assertFalse(disappearing.exists())

    def test_category_ceiling_accepts_exact_limit_and_rejects_one_byte_over(self):
        folder = self.root / "working"
        folder.mkdir()
        (folder / "existing.bin").write_bytes(b"1234567")
        guard = self.make_guard(working_ceiling_bytes=10)

        accepted = guard.check(projected_bytes=3, category="working", paths=[folder])
        self.assertEqual(accepted["total_projected_bytes"], 10)
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            guard.check(projected_bytes=4, category="source", paths=[folder])
        self.assertEqual(caught.exception.code, "category_ceiling")
        self.assertEqual(caught.exception.metadata["category_limit_bytes"], 10)

    def test_precomputed_immutable_baseline_is_counted_in_category_usage(self):
        active = self.root / "active-source"
        active.mkdir()
        (active / "new-source.bin").write_bytes(b"123")
        guard = self.make_guard(working_ceiling_bytes=10)

        result = guard.check(
            category="working", paths=[active], additional_current_bytes=7,
        )
        self.assertEqual(result["current_bytes"], 10)
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            guard.check(
                category="working", paths=[active], additional_current_bytes=8,
            )
        self.assertEqual(caught.exception.code, "category_ceiling")
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            guard.check(category="working", additional_current_bytes=-1)
        self.assertEqual(caught.exception.code, "invalid_budget")

    def test_launch_and_active_checks_enforce_110_48_and_40_gib_boundaries(self):
        guard = self.make_guard(free_bytes=110)
        result = guard.check(projected_bytes=62, category="scratch", phase="launch")
        self.assertEqual(result["post_write_free_bytes"], 48)

        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            self.make_guard(free_bytes=109).check(category="scratch", phase="launch")
        self.assertEqual(caught.exception.code, "launch_floor")

        self.assertEqual(self.make_guard(free_bytes=48).check(category="retention")["free_bytes"], 48)
        for free in (47, 40):
            with self.subTest(free=free):
                with self.assertRaises(disk_guard.DiskGuardError) as caught:
                    self.make_guard(free_bytes=free).check(category="retention")
                self.assertEqual(caught.exception.code, "stop_floor")
                self.assertEqual(caught.exception.metadata["protected_reserve_bytes"], 40)

    def test_capture_peak_is_checked_as_one_projected_write(self):
        guard = self.make_guard(free_bytes=130)
        # A capture that leaves exactly the protected reserve plus margin passes.
        guard.check(projected_bytes=82, category="working", phase="launch")
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            guard.check(projected_bytes=83, category="working", phase="launch")
        self.assertEqual(caught.exception.code, "stop_floor")
        self.assertEqual(caught.exception.metadata["post_write_free_bytes"], 47)

    def test_preflight_refusal_does_not_create_or_change_output(self):
        source = self.root / "source.bin"
        target = self.root / "output.bin"
        source.write_bytes(b"evidence")

        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.bounded_regular_copy(source, target, self.make_guard(free_bytes=47))
        self.assertEqual(caught.exception.code, "stop_floor")
        self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(), b"evidence")

    def test_existing_destination_is_preserved(self):
        source = self.root / "source.bin"
        target = self.root / "output.bin"
        source.write_bytes(b"new data")
        target.write_bytes(b"keep this")

        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.bounded_regular_copy(source, target, self.make_guard())
        self.assertEqual(caught.exception.code, "target_exists")
        self.assertEqual(target.read_bytes(), b"keep this")

    def test_successful_copy_is_exclusive_and_reports_byte_count(self):
        source = self.root / "source.bin"
        target = self.root / "output.bin"
        payload = b"a" * (disk_guard.COPY_CHUNK_BYTES + 17)
        source.write_bytes(payload)

        result = disk_guard.bounded_regular_copy(
            source, target, self.make_guard(
                free_bytes=100 * 1024**2,
                scratch_ceiling_bytes=3 * 1024**2,
            ),
        )
        self.assertEqual(result["copied_bytes"], len(payload))
        self.assertLessEqual(result["chunk_limit_bytes"], 1024**2)
        self.assertEqual(target.read_bytes(), payload)

    def test_copy_refuses_source_changed_since_aggregate_preflight_without_output(self):
        source = self.root / "planned.bin"
        source.write_bytes(b"planned")
        before = source.lstat()
        signature = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns,
        )
        source.write_bytes(b"changed after plan")
        target = self.root / "copy" / "planned.bin"
        target.parent.mkdir()

        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.bounded_regular_copy(
                source,
                target,
                self.make_guard(),
                expected_source_signature=signature,
            )

        self.assertEqual(caught.exception.code, "source_changed")
        self.assertFalse(target.exists())

    def test_free_space_drop_during_copy_preserves_partial_output(self):
        source = self.root / "source.bin"
        target = self.root / "output.bin"
        source.write_bytes(b"abcdefghijkl")
        calls = 0

        def free_space():
            nonlocal calls
            calls += 1
            return 47 if calls == 5 else 10_000

        with patch.object(disk_guard, "COPY_CHUNK_BYTES", 4):
            with self.assertRaises(disk_guard.DiskGuardError) as caught:
                disk_guard.bounded_regular_copy(source, target, self.make_guard(free_bytes=free_space))
        self.assertEqual(caught.exception.code, "stop_floor")
        self.assertEqual(target.read_bytes(), b"abcd")

    def test_source_growth_during_copy_fails_and_keeps_copied_evidence(self):
        source = self.root / "source.bin"
        target = self.root / "output.bin"
        payload = b"abcdefghijklmnop"
        source.write_bytes(payload)
        calls = 0

        def free_space():
            nonlocal calls
            calls += 1
            if calls == 4:
                with source.open("ab") as stream:
                    stream.write(b"XYZ")
            return 10_000

        with patch.object(disk_guard, "COPY_CHUNK_BYTES", 4):
            with self.assertRaises(disk_guard.DiskGuardError) as caught:
                disk_guard.bounded_regular_copy(source, target, self.make_guard(free_bytes=free_space))
        self.assertIn(caught.exception.code, {"source_grew", "source_changed"})
        self.assertTrue(target.exists())
        self.assertEqual(target.read_bytes(), payload)

    def test_symlink_source_and_symlink_output_are_rejected(self):
        source = self.root / "source.bin"
        other = self.root / "other.bin"
        symlink_source = self.root / "source-link.bin"
        source.write_bytes(b"source")
        other.write_bytes(b"other")
        try:
            symlink_source.symlink_to(source)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.bounded_regular_copy(symlink_source, self.root / "new.bin", self.make_guard())
        self.assertEqual(caught.exception.code, "symlink_path")

        output_link = self.root / "output-link.bin"
        output_link.symlink_to(other)
        with self.assertRaises(disk_guard.DiskGuardError) as caught:
            disk_guard.bounded_regular_copy(source, output_link, self.make_guard())
        self.assertEqual(caught.exception.code, "symlink_path")
        self.assertEqual(other.read_bytes(), b"other")


if __name__ == "__main__":
    unittest.main()
