#!/usr/bin/env python3
"""Bounded integrity regressions for v092_ledger_archive; no release ledger use."""

import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


_SPEC = importlib.util.spec_from_file_location(
    "v092_ledger_archive", Path(__file__).with_name("v092_ledger_archive.py"),
)
tool = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tool)


def ledger_row(*, status="completed", extra=None):
    row = {
        "schema_version": 1,
        "release": "v0.9.2",
        "group_id": "fixture-group",
        "attempt_id": "fixture-group-attempt-01-series-01",
        "status": status,
        "duration_seconds": 1.5,
        "evidence": {"payload": "fixture bytes stay exact"},
    }
    if extra:
        row.update(extra)
    return (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()


class LedgerArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.release = self.root / "reports/releases/v0.9.2"
        self.release.mkdir(parents=True)
        self.ledger = self.release / "ledger-v1.jsonl"
        self.archive_dir = self.release / "ledger-archive"
        self.current_archive_dir = self.release / "ledger-archives/ledger-future-fixture-01"
        self.current_manifest_rel = "reports/releases/v0.9.2/ledger-archives/ledger-future-fixture-01/manifest.json"
        self.current_index_path = self.root / tool.CURRENT_INDEX_RELATIVE.as_posix()
        self.raw = (
            ledger_row() +
            ledger_row(status="recorder-error", extra={"attempt_id": "fixture-group-attempt-02-series-01"}) +
            ledger_row(status="completed", extra={
                "group_id": "future-joern-group",
                "attempt_id": "future-joern-group-attempt-01-series-01",
            })
        )
        self.ledger.write_bytes(self.raw)
        self.prefix = b"".join(self.raw.splitlines(keepends=True)[:2])
        prefix_sha = hashlib.sha256(self.prefix).hexdigest()
        prefix_blob = hashlib.sha1(
            b"blob " + str(len(self.prefix)).encode("ascii") + b"\0" + self.prefix,
        ).hexdigest()
        prefix_patch = mock.patch.multiple(
            tool,
            HISTORICAL_PREFIX_LINES=2,
            HISTORICAL_PREFIX_BYTES=len(self.prefix),
            HISTORICAL_PREFIX_SHA256=prefix_sha,
            HISTORICAL_PREFIX_GIT_BLOB_SHA1=prefix_blob,
        )
        prefix_patch.start()
        self.addCleanup(prefix_patch.stop)

    def pack(self):
        return tool.pack(self.root, self.archive_dir)

    @property
    def manifest_path(self):
        return "reports/releases/v0.9.2/ledger-archive/manifest.json"

    @property
    def archive_path(self):
        return self.archive_dir / tool.ARCHIVE_NAME

    def manifest(self):
        return json.loads((self.archive_dir / tool.MANIFEST_NAME).read_text())

    def write_manifest(self, value):
        (self.archive_dir / tool.MANIFEST_NAME).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
        )

    def pack_indexed_archive(self):
        self.current_archive_dir.parent.mkdir(parents=True, exist_ok=True)
        result = tool.pack(self.root, self.current_archive_dir)
        manifest_bytes = (self.current_archive_dir / tool.MANIFEST_NAME).read_bytes()
        index = {
            "schema": tool.INDEX_SCHEMA,
            "manifest": {
                "path": self.current_manifest_rel,
                "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            },
        }
        self.current_index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
        return result, manifest_bytes, index

    def bounded_hydrate_subprocess(self):
        code = """
import importlib.util
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location('ledger_archive_child', sys.argv[1])
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
tool.HISTORICAL_PREFIX_LINES = int(sys.argv[4])
tool.HISTORICAL_PREFIX_BYTES = int(sys.argv[5])
tool.HISTORICAL_PREFIX_SHA256 = sys.argv[6]
tool.HISTORICAL_PREFIX_GIT_BLOB_SHA1 = sys.argv[7]
try:
    tool.hydrate(Path(sys.argv[2]), sys.argv[3])
except Exception as exc:
    print(type(exc).__name__ + ': ' + str(exc))
    raise SystemExit(2)
"""
        return subprocess.run(
            [sys.executable, "-c", code,
             str(Path(__file__).with_name("v092_ledger_archive.py")), str(self.root),
             self.manifest_path, str(tool.HISTORICAL_PREFIX_LINES),
             str(tool.HISTORICAL_PREFIX_BYTES), tool.HISTORICAL_PREFIX_SHA256,
             tool.HISTORICAL_PREFIX_GIT_BLOB_SHA1],
            capture_output=True, text=True, timeout=3,
        )

    def test_lossless_round_trip_determinism_and_idempotent_existing_file(self):
        original_stat = self.ledger.stat()
        result = self.pack()
        self.assertEqual(result["status"], "packed")
        packed_bytes = self.archive_path.read_bytes()
        manifest_bytes = (self.archive_dir / tool.MANIFEST_NAME).read_bytes()
        manifest = self.manifest()
        self.assertEqual(manifest["source_path"], "reports/releases/v0.9.2/ledger-v1.jsonl")
        self.assertEqual(manifest["line_count"], 3)
        self.assertEqual(manifest["committed_prefix"], {
            "line_count": 2,
            "bytes": len(self.prefix),
            "sha256": hashlib.sha256(self.prefix).hexdigest(),
            "git_blob_sha1": hashlib.sha1(
                b"blob " + str(len(self.prefix)).encode("ascii") + b"\0" + self.prefix,
            ).hexdigest(),
        })
        self.assertEqual(manifest["line_sha256"], [
            hashlib.sha256(line).hexdigest() for line in self.raw.splitlines(keepends=True)
        ])
        self.assertEqual(gzip.decompress(packed_bytes), self.raw)
        self.assertEqual(self.ledger.read_bytes(), self.raw)
        self.assertEqual(self.ledger.stat().st_ino, original_stat.st_ino)
        self.assertEqual(self.ledger.stat().st_mtime_ns, original_stat.st_mtime_ns)

        second = self.release / "ledger-archive-second"
        tool.pack(self.root, second)
        self.assertEqual((second / tool.ARCHIVE_NAME).read_bytes(), packed_bytes)
        self.assertEqual((second / tool.MANIFEST_NAME).read_bytes(), manifest_bytes)

        self.ledger.unlink()
        restored = tool.hydrate(self.root, self.manifest_path)
        self.assertEqual(restored["status"], "hydrated")
        self.assertEqual(self.ledger.read_bytes(), self.raw)
        restored_stat = self.ledger.stat()
        again = tool.hydrate(self.root, self.manifest_path)
        self.assertEqual(again["status"], "already-present")
        self.assertTrue(again["existing_file_preserved"])
        self.assertEqual(self.ledger.stat().st_ino, restored_stat.st_ino)
        self.assertEqual(self.ledger.stat().st_mtime_ns, restored_stat.st_mtime_ns)

    def test_pack_rejects_invalid_json_duplicate_keys_nonfinite_and_bad_status(self):
        invalid_rows = {
            "duplicate key": (b'{"schema_version":1,"release":"v0.9.2",' +
                              b'"group_id":"g","attempt_id":"a","status":"completed",' +
                              b'"status":"failed"}\n'),
            "non-finite number": ledger_row().replace(b'1.5', b'1e10000'),
            "NaN token": ledger_row().replace(b'1.5', b'NaN'),
            "bad status": ledger_row(status="started"),
            "wrong row type": b"[]\n",
            "blank row": b"\n",
            "CRLF": ledger_row().replace(b"\n", b"\r\n"),
        }
        for label, contents in invalid_rows.items():
            with self.subTest(label=label):
                self.ledger.write_bytes(contents)
                with self.assertRaises(ValueError):
                    self.pack()
                self.assertFalse(self.archive_dir.exists())
                self.assertEqual(list(self.release.glob(".ledger-archive.tmp-*")), [])

    def test_pack_rejects_typed_rows_without_the_pinned_prefix(self):
        self.ledger.write_bytes(ledger_row())
        with self.assertRaisesRegex(ValueError, "pinned v0.9.2"):
            self.pack()
        self.assertFalse(self.archive_dir.exists())

    def test_pack_enforces_uncompressed_line_and_line_count_limits(self):
        limits = (
            ("uncompressed bytes", "MAX_UNCOMPRESSED_BYTES", len(self.raw) - 1),
            ("line bytes", "MAX_LINE_BYTES", 100),
            ("line count", "MAX_LINE_COUNT", 2),
        )
        for label, name, value in limits:
            with self.subTest(label=label):
                with mock.patch.object(tool, name, value):
                    with self.assertRaises(ValueError):
                        self.pack()
                self.assertFalse(self.archive_dir.exists())
                self.assertEqual(list(self.release.glob(".ledger-archive.tmp-*")), [])

    def test_pack_detects_source_change_and_leaves_no_published_output(self):
        original_validate = tool._validate_line
        changed = False

        def mutate_after_validation(line, number):
            nonlocal changed
            digest = original_validate(line, number)
            if not changed:
                changed = True
                with self.ledger.open("ab") as stream:
                    stream.write(ledger_row(status="failed", extra={"attempt_id": "late-row"}))
            return digest

        with mock.patch.object(tool, "_validate_line", side_effect=mutate_after_validation):
            with self.assertRaises(ValueError):
                self.pack()
        self.assertFalse(self.archive_dir.exists())
        self.assertEqual(list(self.release.glob(".ledger-archive.tmp-*")), [])

    def test_pack_never_replaces_output_created_during_pack(self):
        original_publish = tool._publish_directory
        marker = self.archive_dir / "keep.txt"

        def create_destination_then_publish(stage, output):
            output.mkdir()
            (output / "keep.txt").write_text("pre-existing destination")
            return original_publish(stage, output)

        with mock.patch.object(tool, "_publish_directory", side_effect=create_destination_then_publish):
            with self.assertRaises(OSError):
                self.pack()
        self.assertEqual(marker.read_text(), "pre-existing destination")
        self.assertEqual(list(self.release.glob(".ledger-archive.tmp-*")), [])

    def test_pack_refuses_source_symlink(self):
        payload = self.ledger.read_bytes()
        self.ledger.unlink()
        other = self.release / "other.jsonl"
        other.write_bytes(payload)
        self.ledger.symlink_to(other.name)
        with self.assertRaises(OSError):
            self.pack()
        self.assertFalse(self.archive_dir.exists())

    def test_fifo_source_is_rejected_quickly_without_a_writer(self):
        self.ledger.unlink()
        os.mkfifo(self.ledger)
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("v092_ledger_archive.py")),
             "pack", "--root", str(self.root), "--output", str(self.archive_dir)],
            capture_output=True, text=True, timeout=3,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not a regular file", completed.stderr)
        self.assertFalse(self.archive_dir.exists())

    def test_fifo_manifest_is_rejected_quickly_without_a_writer(self):
        self.archive_dir.mkdir()
        os.mkfifo(self.archive_dir / tool.MANIFEST_NAME)
        completed = self.bounded_hydrate_subprocess()
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn("not a regular file", completed.stdout)
        self.assertTrue(self.ledger.exists())

    def test_fifo_archive_is_rejected_quickly_without_a_writer(self):
        self.pack()
        self.archive_path.unlink()
        os.mkfifo(self.archive_path)
        completed = self.bounded_hydrate_subprocess()
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn("not a regular file", completed.stdout)
        self.assertTrue(self.ledger.exists())
        self.assertEqual(list(self.release.glob(".ledger-v1.jsonl.hydrate-*.tmp")), [])

    def test_hydrate_rejects_corrupt_or_truncated_gzip_even_with_updated_compressed_hash(self):
        for kind in ("crc", "truncated"):
            with self.subTest(kind=kind):
                if self.archive_dir.exists():
                    import shutil
                    shutil.rmtree(self.archive_dir)
                if not self.ledger.exists():
                    self.ledger.write_bytes(self.raw)
                self.pack()
                payload = self.archive_path.read_bytes()
                payload = payload[:-1] if kind == "truncated" else payload[:-8] + bytes([payload[-8] ^ 1]) + payload[-7:]
                self.archive_path.write_bytes(payload)
                value = self.manifest()
                value["compressed"].update(
                    bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                )
                self.write_manifest(value)
                self.ledger.unlink()
                with self.assertRaises((EOFError, OSError, ValueError)):
                    tool.hydrate(self.root, self.manifest_path)
                self.assertFalse(self.ledger.exists())
                self.assertEqual(list(self.release.glob(".ledger-v1.jsonl.hydrate-*.tmp")), [])

    def test_hydrate_rejects_compressed_size_hash_uncompressed_size_and_line_hash_mismatch(self):
        mutations = {
            "compressed size": lambda value: value["compressed"].update(bytes=value["compressed"]["bytes"] + 1),
            "compressed hash": lambda value: value["compressed"].update(sha256="0" * 64),
            "uncompressed size": lambda value: value["uncompressed"].update(bytes=value["uncompressed"]["bytes"] + 1),
            "line hash": lambda value: value["line_sha256"].__setitem__(0, "0" * 64),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                if self.archive_dir.exists():
                    import shutil
                    shutil.rmtree(self.archive_dir)
                if not self.ledger.exists():
                    self.ledger.write_bytes(self.raw)
                self.pack()
                value = self.manifest()
                mutate(value)
                self.write_manifest(value)
                self.ledger.unlink()
                with self.assertRaises(ValueError):
                    tool.hydrate(self.root, self.manifest_path)
                self.assertFalse(self.ledger.exists())

    def test_hydrate_checks_actual_prefix_even_when_other_hashes_are_recomputed(self):
        self.pack()
        rows = self.raw.splitlines(keepends=True)
        changed = ledger_row(status="failed") + b"".join(rows[1:])
        with self.archive_path.open("wb") as raw_stream:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as zipped:
                zipped.write(changed)
        value = self.manifest()
        value["compressed"].update(
            bytes=self.archive_path.stat().st_size,
            sha256=hashlib.sha256(self.archive_path.read_bytes()).hexdigest(),
        )
        value["uncompressed"].update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
        value["line_sha256"] = [hashlib.sha256(line).hexdigest()
                                for line in changed.splitlines(keepends=True)]
        self.write_manifest(value)
        self.ledger.unlink()
        with self.assertRaisesRegex(ValueError, "pinned committed prefix"):
            tool.hydrate(self.root, self.manifest_path)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_refuses_different_existing_file_without_changing_it(self):
        self.pack()
        different = b"a pre-existing different file\n"
        self.ledger.write_bytes(different)
        before = self.ledger.stat()
        with self.assertRaisesRegex(ValueError, "different existing"):
            tool.hydrate(self.root, self.manifest_path)
        self.assertEqual(self.ledger.read_bytes(), different)
        self.assertEqual(self.ledger.stat().st_ino, before.st_ino)
        self.assertEqual(self.ledger.stat().st_mtime_ns, before.st_mtime_ns)

    def test_hydrate_refuses_symlink_or_fifo_canonical_target(self):
        self.pack()
        outside = self.root / "outside"
        outside.write_bytes(b"outside bytes\n")
        self.ledger.unlink()
        self.ledger.symlink_to(outside)
        with self.assertRaises(ValueError):
            tool.hydrate(self.root, self.manifest_path)
        self.assertTrue(self.ledger.is_symlink())
        self.ledger.unlink()
        os.mkfifo(self.ledger)
        with self.assertRaisesRegex(ValueError, "not a regular file"):
            tool.hydrate(self.root, self.manifest_path)
        self.assertTrue(self.ledger.exists())
        self.assertTrue(self.ledger.is_fifo())

    def test_hydrate_refuses_manifest_symlink_archive_symlink_and_ancestor_symlink(self):
        self.pack()
        manifest = self.archive_dir / tool.MANIFEST_NAME
        real_manifest = self.archive_dir / "manifest-real.json"
        manifest.rename(real_manifest)
        manifest.symlink_to(real_manifest.name)
        self.ledger.unlink()
        with self.assertRaises(OSError):
            tool.hydrate(self.root, self.manifest_path)
        manifest.unlink()
        real_manifest.rename(manifest)

        real_archive = self.archive_dir / "archive-real.gz"
        self.archive_path.rename(real_archive)
        self.archive_path.symlink_to(real_archive.name)
        with self.assertRaises(OSError):
            tool.hydrate(self.root, self.manifest_path)
        self.archive_path.unlink()
        real_archive.rename(self.archive_path)

        outside_dir = self.release / "archive-real"
        self.archive_dir.rename(outside_dir)
        self.archive_dir.symlink_to(outside_dir.name, target_is_directory=True)
        with self.assertRaises(OSError):
            tool.hydrate(self.root, self.manifest_path)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_rejects_traversal_and_manifest_target_escape(self):
        self.pack()
        for path in ("../../outside/manifest.json", "/tmp/manifest.json", "reports\\escape.json",
                     "evidence/manifest.json"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    tool.hydrate(self.root, path)
        value = self.manifest()
        value["archive_path"] = "../../outside.gz"
        self.write_manifest(value)
        self.ledger.unlink()
        with self.assertRaisesRegex(ValueError, "archive path"):
            tool.hydrate(self.root, self.manifest_path)
        self.assertFalse((self.root.parent / "outside.gz").exists())
        self.assertFalse(self.ledger.exists())

    def test_hydrate_rejects_duplicate_manifest_keys(self):
        self.pack()
        manifest = self.archive_dir / tool.MANIFEST_NAME
        data = manifest.read_text()
        data = data.replace('"schema": "dataflowbench-v092-ledger-archive/v1",',
                            '"schema": "dataflowbench-v092-ledger-archive/v1",\n  "schema": "dataflowbench-v092-ledger-archive/v1",')
        manifest.write_text(data)
        self.ledger.unlink()
        with self.assertRaisesRegex(ValueError, "duplicate manifest key"):
            tool.hydrate(self.root, self.manifest_path)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_rejects_nonfinite_manifest_numbers(self):
        self.pack()
        manifest_path = self.archive_dir / tool.MANIFEST_NAME
        original = manifest_path.read_text()
        self.ledger.unlink()
        for value in ("NaN", "1e9999"):
            with self.subTest(value=value):
                mutated = original.replace('"line_count": 3,', f'"line_count": {value},')
                self.assertNotEqual(mutated, original)
                manifest_path.write_text(mutated)
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    tool.hydrate(self.root, self.manifest_path)
                self.assertFalse(self.ledger.exists())

    def test_hydrate_current_selects_and_verifies_indexed_archive(self):
        _packed, manifest_bytes, index = self.pack_indexed_archive()
        archive_bytes = (self.current_archive_dir / tool.ARCHIVE_NAME).read_bytes()
        self.ledger.unlink()
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            self.assertEqual(tool.main(["hydrate-current", "--root", str(self.root)]), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "hydrated")
        self.assertEqual(self.ledger.read_bytes(), self.raw)
        self.assertEqual(result["selected_manifest_path"], self.current_manifest_rel)
        self.assertEqual(result["selected_manifest_sha256"], index["manifest"]["sha256"])
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), result["selected_manifest_sha256"])
        self.assertEqual((self.current_archive_dir / tool.ARCHIVE_NAME).read_bytes(), archive_bytes)

    def test_hydrate_current_refuses_missing_index(self):
        self.pack_indexed_archive()
        self.current_index_path.unlink()
        self.ledger.unlink()
        with self.assertRaises(OSError):
            tool.hydrate_current(self.root)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_current_enforces_bounded_index_size(self):
        self.pack_indexed_archive()
        self.ledger.unlink()
        with mock.patch.object(tool, "MAX_INDEX_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "current index exceeds size limit"):
                tool.hydrate_current(self.root)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_current_refuses_bad_manifest_digest(self):
        _packed, _manifest_bytes, index = self.pack_indexed_archive()
        index["manifest"]["sha256"] = "0" * 64
        self.current_index_path.write_text(json.dumps(index))
        self.ledger.unlink()
        with self.assertRaisesRegex(ValueError, "indexed ledger archive manifest digest mismatch"):
            tool.hydrate_current(self.root)
        self.assertFalse(self.ledger.exists())

    def test_hydrate_current_refuses_unknown_or_extra_index_fields(self):
        self.pack_indexed_archive()
        good = json.loads(self.current_index_path.read_text())
        self.ledger.unlink()
        variants = (
            {**good, "extra": False},
            {**good, "manifest": {**good["manifest"], "extra": "ignored"}},
            {**good, "schema": "dataflowbench-v092-ledger-index/v2"},
        )
        for value in variants:
            with self.subTest(value=value):
                self.current_index_path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    tool.hydrate_current(self.root)
                self.assertFalse(self.ledger.exists())

    def test_hydrate_current_rejects_traversal_and_paths_outside_archive_collection(self):
        self.pack_indexed_archive()
        good = json.loads(self.current_index_path.read_text())
        self.ledger.unlink()
        paths = (
            "reports/releases/v0.9.2/ledger-archives/../../outside/manifest.json",
            "reports/releases/v0.9.2/ledger-archives/.hidden/manifest.json",
            "reports/releases/v0.9.2/manifest.json",
            "reports/releases/v0.9.2/acquisition/fixture/manifest.json",
            "../../outside/manifest.json",
        )
        for path in paths:
            with self.subTest(path=path):
                value = {**good, "manifest": {**good["manifest"], "path": path}}
                self.current_index_path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    tool.hydrate_current(self.root)
                self.assertFalse(self.ledger.exists())

    def test_hydrate_current_refuses_symlinked_index(self):
        self.pack_indexed_archive()
        real_index = self.release / "ledger-archive-index-real.json"
        self.current_index_path.rename(real_index)
        self.current_index_path.symlink_to(real_index.name)
        self.ledger.unlink()
        with self.assertRaises(OSError):
            tool.hydrate_current(self.root)
        self.assertFalse(self.ledger.exists())


if __name__ == "__main__":
    unittest.main()
