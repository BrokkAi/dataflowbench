#!/usr/bin/env python3
"""Delivery integrity regressions; no production evidence or analyzer execution."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('packaging_tool', Path(__file__).with_name('package-v092-evidence.py'))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class EvidenceDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.scope = self.root / 'evidence'
        self.scope.mkdir(parents=True)
        self.output = self.base / 'bundle'

    def pack(self):
        return tool.pack(self.root, 'evidence', self.output, 1024)

    def rewrite_manifest(self, records):
        p = self.output / 'files.jsonl.gz'
        with gzip.open(p, 'wt') as stream:
            for r in records:
                stream.write(json.dumps(r) + '\n')
        index_path = self.output / 'bundle.json'
        index = json.loads(index_path.read_text())
        index['manifest'].update(sha256=tool.digest(p), bytes=p.stat().st_size)
        index_path.write_text(json.dumps(index))

    def records(self):
        with gzip.open(self.output / 'files.jsonl.gz', 'rt') as stream:
            return [json.loads(line) for line in stream]

    def test_binary_roundtrip_parts_metadata_and_independent_duplicate_files(self):
        content = os.urandom(9000) + b'\x00\r\n'
        for name in ('one', 'two'):
            p = self.scope / name
            p.write_bytes(content)
            p.chmod(0o640 if name == 'one' else 0o600)
            os.utime(p, ns=(1700000000123456789, 1700000000123456789))
        (self.scope / 'empty').touch()
        before = {p.name: tool.stable_stat(p) for p in self.scope.iterdir()}
        index = self.pack()
        self.assertEqual(index['unique_objects'], 2)
        self.assertGreater(len(index['parts']), 1)
        restored = self.base / 'restored'
        self.assertEqual(tool.check(self.output, restored)['files'], 3)
        for name, original in before.items():
            dest = restored / 'evidence' / name
            self.assertEqual(dest.read_bytes(), (self.scope / name).read_bytes())
            self.assertEqual(tool.stable_stat(self.scope / name), original)
            self.assertEqual(dest.stat().st_mtime_ns, original[3])
            self.assertEqual(dest.stat().st_mode & 0o7777, original[5])
        self.assertNotEqual((restored / 'evidence/one').stat().st_ino,
                            (restored / 'evidence/two').stat().st_ino)

    def test_changed_compressed_part_rejected(self):
        (self.scope / 'a').write_bytes(b'payload')
        index = self.pack()
        part = self.output / index['parts'][0]['path']
        part.write_bytes(part.read_bytes() + b'corruption')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            tool.check(self.output)

    def test_manifest_traversal_rejected_even_with_updated_digest(self):
        (self.scope / 'a').write_bytes(b'payload')
        self.pack()
        records = self.records()
        records[0]['path'] = 'evidence/../../escape'
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, 'unsafe path'):
            tool.check(self.output, self.base / 'restored')
        self.assertFalse((self.base / 'escape').exists())

    def test_manifest_wrong_content_digest_rejected(self):
        (self.scope / 'a').write_bytes(b'payload')
        self.pack()
        records = self.records()
        records[0]['sha256'] = '0' * 64
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, 'unexpected archive object'):
            tool.check(self.output)

    def test_duplicate_manifest_paths_rejected(self):
        (self.scope / 'a').write_bytes(b'payload')
        (self.scope / 'b').write_bytes(b'payload')
        self.pack()
        records = self.records()
        records[1]['path'] = records[0]['path']
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, 'duplicate path'):
            tool.check(self.output)

    def test_symlink_evidence_rejected(self):
        (self.scope / 'a').symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'regular file'):
            self.pack()

    def test_output_inside_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside evidence scope'):
            tool.pack(self.root, 'evidence', self.scope / 'bundle', 1024)

    def test_existing_restore_or_bundle_refused(self):
        (self.scope / 'a').write_bytes(b'payload')
        self.pack()
        with self.assertRaises(FileExistsError):
            self.pack()
        self.scope.mkdir(exist_ok=True)
        with self.assertRaises(FileExistsError):
            tool.check(self.output, self.scope)

    def test_scope_symlink_ancestor_rejected(self):
        (self.root / 'alias').symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink scope ancestor'):
            tool.pack(self.root, 'alias/source/evidence', self.output, 1024)

    def test_file_child_path_collision_rejected(self):
        (self.scope / 'a').write_bytes(b'payload')
        (self.scope / 'b').write_bytes(b'payload')
        self.pack()
        records = self.records()
        records[1]['path'] = 'evidence/a/child'
        self.rewrite_manifest(records)
        with self.assertRaisesRegex(ValueError, 'file/child path collision'):
            tool.check(self.output)

    def test_duplicate_part_reference_rejected(self):
        (self.scope / 'a').write_bytes(b'payload')
        self.pack()
        path = self.output / 'bundle.json'
        index = json.loads(path.read_text())
        index['parts'].append(index['parts'][0])
        path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'duplicate bundle file reference'):
            tool.check(self.output)


if __name__ == '__main__':
    unittest.main()
