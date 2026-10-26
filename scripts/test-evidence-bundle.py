#!/usr/bin/env python3
"""Focused lossless-bundle regressions; never reads production evidence."""

import gzip
import importlib.util
import json
import os
from pathlib import Path
try:
    import resource
except ImportError:
    resource = None
import stat
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "evidence_bundle", Path(__file__).with_name("evidence_bundle.py"))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "source-root"
        self.scope = self.root / "archive" / "evidence"
        self.scope.mkdir(parents=True)
        self.bundle = self.base / "bundle"

    def write_fixture(self):
        self.scope.mkdir(parents=True, exist_ok=True)
        (self.scope / "alpha.bin").write_bytes(b"alpha\x00\xff\r\n")
        (self.scope / "nested").mkdir(exist_ok=True)
        (self.scope / "nested" / "same.bin").write_bytes(b"repeated bytes" * 1000)
        (self.scope / "nested" / "copy.bin").write_bytes(b"repeated bytes" * 1000)
        (self.scope / "noise.bin").write_bytes(os.urandom(9000))

    def pack(self, part_bytes=1024):
        return tool.pack(self.root, "archive/evidence", self.bundle, part_bytes)

    def index(self):
        return json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))

    def write_index(self, value):
        (self.bundle / "bundle.json").write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def records(self):
        with gzip.open(self.bundle / "files.jsonl.gz", "rt", encoding="utf-8") as stream:
            return [json.loads(line) for line in stream]

    def rewrite_manifest(self, records):
        manifest_path = self.bundle / "files.jsonl.gz"
        with manifest_path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
                for record in records:
                    gz.write((json.dumps(record, sort_keys=True) + "\n").encode())
        index = self.index()
        index["manifest"].update(sha256=tool.digest(manifest_path),
                                 bytes=manifest_path.stat().st_size)
        self.write_index(index)

    def rewrite_archive(self, mutate):
        """Alter decompressed tar bytes, then re-gzip and refresh the outer hashes."""
        index = self.index()
        part_paths = [self.bundle / item["path"] for item in index["parts"]]
        compressed = b"".join(path.read_bytes() for path in part_paths)
        uncompressed = bytearray(gzip.decompress(compressed))
        mutate(uncompressed)
        rebuilt = gzip.compress(bytes(uncompressed), mtime=0)
        sizes = [item["bytes"] for item in index["parts"]]
        for path in part_paths:
            path.unlink()
        new_parts = []
        offset = 0
        for number, size in enumerate(sizes):
            if offset >= len(rebuilt):
                break
            chunk = rebuilt[offset:offset + size]
            offset += len(chunk)
            part_path = self.bundle / f"detail.tar.gz.part{number:04d}"
            part_path.write_bytes(chunk)
            new_parts.append({"path": part_path.name, "sha256": tool.digest(part_path),
                              "bytes": part_path.stat().st_size})
        while offset < len(rebuilt):
            chunk = rebuilt[offset:offset + 1024]
            offset += len(chunk)
            part_path = self.bundle / f"detail.tar.gz.part{len(new_parts):04d}"
            part_path.write_bytes(chunk)
            new_parts.append({"path": part_path.name, "sha256": tool.digest(part_path),
                              "bytes": part_path.stat().st_size})
        index["parts"] = new_parts
        self.write_index(index)

    def update_part_hashes_after_mutation(self):
        index = self.index()
        for item in index["parts"]:
            path = self.bundle / item["path"]
            item.update(sha256=tool.digest(path), bytes=path.stat().st_size)
        self.write_index(index)

    def test_generic_scope_roundtrip_dedup_metadata_and_read_file(self):
        self.write_fixture()
        (self.scope / "alpha.bin").chmod(0o640)
        os.utime(self.scope / "alpha.bin", ns=(1700000000123456789,) * 2)
        before = {path.relative_to(self.root).as_posix(): tool.stable_stat(path)
                  for path in self.scope.rglob("*") if path.is_file()}
        index = self.pack()
        self.assertEqual(index["scope"], "archive/evidence")
        self.assertEqual(index["unique_objects"], 3)
        self.assertGreater(len(index["parts"]), 1)
        self.assertEqual(tool.read_file(self.bundle, "archive/evidence/alpha.bin"),
                         b"alpha\x00\xff\r\n")

        restored = self.base / "restored"
        result = tool.check(self.bundle, restored)
        self.assertEqual(result["files"], 4)
        self.assertEqual(result["restored_files"], 4)
        for relative, original in before.items():
            destination = restored / relative
            source = self.root / relative
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(destination.stat().st_mtime_ns, original[3])
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), original[5])
        self.assertNotEqual((restored / "archive/evidence/nested/same.bin").stat().st_ino,
                            (restored / "archive/evidence/nested/copy.bin").stat().st_ino)

    def test_selected_restore_is_partial_and_empty_selection_still_verifies_objects(self):
        self.write_fixture()
        self.pack()
        restored = self.base / "partial"
        result = tool.check(self.bundle, restored,
                            paths=["archive/evidence/alpha.bin"])
        self.assertEqual(result["files"], 4)
        self.assertEqual(result["restored_files"], 1)
        self.assertTrue((restored / "archive/evidence/alpha.bin").is_file())
        self.assertFalse((restored / "archive/evidence/nested/same.bin").exists())

        empty_restore = self.base / "empty-restore"
        empty_result = tool.check(self.bundle, empty_restore, paths=[])
        self.assertEqual(empty_result["restored_files"], 0)
        self.assertEqual(list(empty_restore.iterdir()), [])

        self.rewrite_archive(lambda data: data.__setitem__(512, data[512] ^ 1))
        with self.assertRaisesRegex(ValueError, "digest differs"):
            tool.check(self.bundle, paths=[])

    @unittest.skipIf(resource is None, "resource limits are unavailable")
    def test_many_duplicate_paths_restore_with_bounded_open_file_descriptors(self):
        repeated = b"one object, many independent restore targets\n"
        names = [f"copy-{number:03d}.bin" for number in range(96)]
        for name in names:
            (self.scope / name).write_bytes(repeated)
        self.pack()
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft < 16:
            self.skipTest("existing descriptor limit is too low for this test")
        limited = min(soft, 32)
        resource.setrlimit(resource.RLIMIT_NOFILE, (limited, hard))
        try:
            result = tool.check(self.bundle, self.base / "many-restored",
                                paths=[f"archive/evidence/{name}" for name in names])
        finally:
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
        self.assertEqual(result["objects"], 1)
        self.assertEqual(result["restored_files"], len(names))
        self.assertTrue(all((self.base / "many-restored/archive/evidence" / name).read_bytes()
                            == repeated for name in names))

    def test_selected_missing_path_and_existing_destination_are_not_published_over(self):
        self.write_fixture()
        self.pack()
        missing = self.base / "missing-restore"
        with self.assertRaisesRegex(ValueError, "selected path missing"):
            tool.check(self.bundle, missing, paths=["archive/evidence/nope"])
        self.assertFalse(missing.exists())

        existing = self.base / "existing"
        existing.mkdir()
        (existing / "keep").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            tool.check(self.bundle, existing)
        self.assertEqual((existing / "keep").read_text(encoding="utf-8"), "keep")

    def test_read_file_verifies_unselected_objects_too(self):
        self.write_fixture()
        self.pack()
        # Corrupt a different object's payload in the valid gzip stream, then refresh
        # only the part hashes. Reading alpha must still reject the full bundle.
        def corrupt_first_object(data):
            offset = 0
            name = bytes(data[:100]).split(b"\0", 1)[0]
            size = int(bytes(data[124:136]).strip(b"\0 ") or b"0", 8)
            self.assertTrue(name.startswith(b"objects/"))
            data[offset + 512] ^= 0x01
            self.assertGreater(size, 0)

        self.rewrite_archive(corrupt_first_object)
        with self.assertRaisesRegex(ValueError, "digest differs"):
            tool.read_file(self.bundle, "archive/evidence/alpha.bin")

    def test_corrupt_object_rejected_after_outer_part_digest_is_updated(self):
        self.write_fixture()
        self.pack()

        def corrupt_object(data):
            size = int(bytes(data[124:136]).strip(b"\0 ") or b"0", 8)
            self.assertGreater(size, 0)
            data[512] ^= 0x40

        self.rewrite_archive(corrupt_object)
        with self.assertRaisesRegex(ValueError, "digest differs"):
            tool.check(self.bundle)

    def test_missing_tar_terminator_rejected_after_outer_digest_update(self):
        self.write_fixture()
        self.pack()

        def remove_tar_end(data):
            offset = 0
            while data[offset:offset + 512] != b"\0" * 512:
                size = int(bytes(data[offset + 124:offset + 136]).strip(b"\0 ") or b"0", 8)
                offset += 512 + size + (-size) % 512
            self.assertEqual(bytes(data[offset:]), b"\0" * (len(data) - offset))
            del data[offset:]

        self.rewrite_archive(remove_tar_end)
        with self.assertRaisesRegex(ValueError, "missing archive trailer|end marker"):
            tool.check(self.bundle)

    def test_corrupt_gzip_trailer_rejected_after_outer_part_digest_is_updated(self):
        self.write_fixture()
        self.pack()
        index = self.index()
        last = self.bundle / index["parts"][-1]["path"]
        payload = bytearray(last.read_bytes())
        payload[-1] ^= 0x01
        last.write_bytes(payload)
        self.update_part_hashes_after_mutation()
        with self.assertRaises((ValueError, OSError, EOFError)):
            tool.check(self.bundle)

    def test_truncated_gzip_rejected_after_outer_part_digest_is_updated(self):
        self.write_fixture()
        self.pack()
        index = self.index()
        part_paths = [self.bundle / item["path"] for item in index["parts"]]
        compressed = b"".join(path.read_bytes() for path in part_paths)[:-5]
        for path in part_paths:
            path.unlink()
        part = self.bundle / "detail.tar.gz.part0000"
        part.write_bytes(compressed)
        index["parts"] = [{"path": part.name, "sha256": tool.digest(part),
                           "bytes": part.stat().st_size}]
        self.write_index(index)
        with self.assertRaises((ValueError, OSError, EOFError)):
            tool.check(self.bundle)

    def test_manifest_traversal_windows_names_and_scope_file_collisions_rejected(self):
        self.write_fixture()
        self.pack()
        for unsafe in ("archive/evidence/../../escape", r"archive\evidence\escape",
                       "C:/archive/evidence/file", "archive/evidence/C:stream"):
            records = self.records()
            records[0]["path"] = unsafe
            self.rewrite_manifest(records)
            with self.assertRaises(ValueError):
                tool.check(self.bundle)
        with self.assertRaises(ValueError):
            tool.safe_path(r"C:\tmp\file")

        records = self.records()
        records[0]["path"] = "archive/evidence/nested"
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, "file/child path collision"):
            tool.check(self.bundle)

    def test_manifest_duplicate_path_and_object_size_mismatch_rejected(self):
        self.write_fixture()
        self.pack()
        records = self.records()
        records[1]["path"] = records[0]["path"]
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, "duplicate path"):
            tool.check(self.bundle)

        records = self.records()
        records[1]["path"] = "archive/evidence/nested/copy.bin"
        records[2]["bytes"] += 1
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, "object size differs"):
            tool.check(self.bundle)

    def test_bundle_symlink_children_and_ancestors_rejected(self):
        self.write_fixture()
        self.pack()
        index = self.index()
        part = self.bundle / index["parts"][0]["path"]
        saved = self.base / "saved-part"
        part.rename(saved)
        part.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            tool.check(self.bundle)

        ancestor_alias = self.base / "bundle-parent-alias"
        ancestor_alias.symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            tool.check(ancestor_alias / "real-bundle")

        real_bundle = self.base / "real-bundle"
        self.bundle.rename(real_bundle)
        self.bundle.symlink_to(real_bundle, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            tool.check(self.bundle)

    def test_restore_symlink_ancestor_rejected_and_failure_leaves_no_destination(self):
        self.write_fixture()
        self.pack()
        outside = self.base / "outside"
        outside.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            tool.check(self.bundle, alias / "restore")
        self.assertFalse((outside / "restore").exists())

        # A later archive failure removes any staging files and publishes nothing.
        part = self.bundle / self.index()["parts"][0]["path"]
        raw = bytearray(part.read_bytes())
        raw[-1] ^= 0x80
        part.write_bytes(raw)
        self.update_part_hashes_after_mutation()
        failed = self.base / "failed-restore"
        with self.assertRaises((ValueError, OSError, EOFError)):
            tool.check(self.bundle, failed)
        self.assertFalse(failed.exists())
        self.assertFalse(any(self.base.glob(".failed-restore.staging-*")))

    def test_symlink_source_and_output_inside_scope_do_not_leave_bundle(self):
        (self.scope / "link").symlink_to(self.base / "missing-target")
        with self.assertRaisesRegex(ValueError, "regular file"):
            self.pack()
        self.assertFalse(self.bundle.exists())
        self.assertFalse(any(self.base.glob(".bundle.staging-*")))

        with self.assertRaisesRegex(ValueError, "outside evidence scope"):
            tool.pack(self.root, "archive/evidence", self.scope / "inner-bundle", 1024)

    def test_symlink_scope_ancestor_and_nonportable_source_name_rejected(self):
        self.write_fixture()
        (self.root / "alias").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            tool.pack(self.root, "alias/source-root/archive/evidence", self.bundle, 1024)
        self.assertFalse(self.bundle.exists())
        (self.root / "alias").unlink()

        (self.scope / "bad\\name").write_bytes(b"not portable")
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            self.pack()
        self.assertFalse(self.bundle.exists())

    def test_bundle_metadata_malformed_and_unknown_schema_rejected(self):
        self.write_fixture()
        self.pack()
        (self.bundle / "bundle.json").write_text(
            '{"schema":"dataflowbench-lossless-evidence-bundle/v1",'
            '"schema":"dataflowbench-lossless-evidence-bundle/v1"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            tool.check(self.bundle)
        self.write_index({"schema": "other"})
        with self.assertRaisesRegex(ValueError, "unknown or invalid schema"):
            tool.check(self.bundle)
        (self.bundle / "bundle.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid bundle metadata"):
            tool.check(self.bundle)

    def test_archive_symlink_member_rejected(self):
        self.write_fixture()
        index = self.pack()
        manifest_records = self.records()
        sha = manifest_records[0]["sha256"]

        # Build a syntactically valid gzip/tar payload containing a symlink member
        # under an otherwise expected object name. The manifest and part digests are
        # internally consistent, so rejection must come from member type validation.
        import io
        import tarfile
        tar_bytes = io.BytesIO()
        with tarfile.open(fileobj=tar_bytes, mode="w", format=tarfile.USTAR_FORMAT) as tar:
            link = tarfile.TarInfo("objects/" + sha)
            link.type = tarfile.SYMTYPE
            link.linkname = "../../outside"
            tar.addfile(link)
            seen = {sha}
            for record in manifest_records:
                if record["sha256"] not in seen:
                    content = (self.scope / Path(record["path"]).relative_to("archive/evidence")).read_bytes()
                    info = tarfile.TarInfo("objects/" + record["sha256"])
                    info.size = len(content)
                    tar.addfile(info, io.BytesIO(content))
                    seen.add(record["sha256"])
        compressed = gzip.compress(tar_bytes.getvalue(), mtime=0)
        index = self.index()
        old_parts = [self.bundle / item["path"] for item in index["parts"]]
        for path in old_parts:
            path.unlink()
        part = self.bundle / "detail.tar.gz.part0000"
        part.write_bytes(compressed)
        index["parts"] = [{"path": part.name, "sha256": tool.digest(part),
                           "bytes": part.stat().st_size}]
        self.write_index(index)
        with self.assertRaisesRegex(ValueError, "non-regular archive member"):
            tool.check(self.bundle)


if __name__ == "__main__":
    unittest.main()
