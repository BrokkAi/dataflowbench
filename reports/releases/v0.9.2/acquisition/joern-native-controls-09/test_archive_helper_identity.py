"""Near-miss checks for the strict source-08 archive-helper identity pin."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import archive_evidence as ae


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ArchiveHelperIdentityTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix='archive-helper-identity-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        index_ref = {'path': 'index.json', 'sha256': sha(b'index')}
        request_ref = {'path': 'request.json', 'sha256': sha(b'request')}
        helper_path = ae.HELPER_SOURCE_PATH
        helper_raw = b'fixture source-08 helper bytes\n'
        helper = root / helper_path
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_bytes(helper_raw)
        source_map = {
            index_ref['path']: index_ref,
            request_ref['path']: request_ref,
            helper_path: {'path': helper_path, 'sha256': sha(helper_raw)},
        }

        def read_stable(_root, path, *, max_bytes=ae.MAX_REFERENCE_BYTES):
            del max_bytes
            if path == index_ref['path']:
                return b'index'
            if path == request_ref['path']:
                return b'request'
            if path == helper_path:
                return helper_raw
            raise AssertionError('unexpected fixture read: ' + path)

        def strict_json(_raw, label):
            if label == 'archive index':
                return {'retained_request05': request_ref, 'archive': {}}
            if label == 'retained request05':
                return {}
            raise AssertionError('unexpected fixture JSON: ' + label)

        return root, index_ref, request_ref, helper_path, helper_raw, source_map, read_stable, strict_json

    def test_old_07_helper_path_is_rejected(self):
        root, index_ref, request_ref, helper_path, _, source_map, read_stable, strict_json = self.fixture()
        wrong_path = helper_path.replace('joern-native-controls-09', 'joern-native-controls-07')
        with (
            mock.patch.object(ae, 'INDEX_REF', index_ref),
            mock.patch.object(ae, 'REQUEST05_REF', request_ref),
            mock.patch.object(ae, 'HELPER_SOURCE_PATH', helper_path),
            mock.patch.object(ae, 'ARCHIVE_PATH', 'archive.gz'),
            mock.patch.object(ae, 'read_stable', side_effect=read_stable),
            mock.patch.object(ae, '_strict_json', side_effect=strict_json),
            mock.patch.object(ae, '_member_specs', return_value={}),
            mock.patch.object(ae, '_request05_sources'),
            mock.patch.object(ae, '__file__', str(root / wrong_path)),
            self.assertRaisesRegex(ae.ArchiveEvidenceError, 'exact committed source path'),
        ):
            ae.build_context(root, source_map)

    def test_rebound_helper_digest_is_rejected_at_source_map_guard(self):
        root, index_ref, request_ref, helper_path, _, source_map, read_stable, strict_json = self.fixture()
        bad_map = dict(source_map)
        bad_map[helper_path] = {'path': helper_path, 'sha256': '0' * 64}
        helper = root / helper_path
        with (
            mock.patch.object(ae, 'INDEX_REF', index_ref),
            mock.patch.object(ae, 'REQUEST05_REF', request_ref),
            mock.patch.object(ae, 'HELPER_SOURCE_PATH', helper_path),
            mock.patch.object(ae, 'ARCHIVE_PATH', 'archive.gz'),
            mock.patch.object(ae, 'read_stable', side_effect=read_stable),
            mock.patch.object(ae, '_strict_json', side_effect=strict_json),
            mock.patch.object(ae, '_member_specs', return_value={}),
            mock.patch.object(ae, '_request05_sources'),
            mock.patch.object(ae, '__file__', str(helper)),
            self.assertRaisesRegex(ae.ArchiveEvidenceError, 'outside exact current source closure'),
        ):
            ae.build_context(root, bad_map)


if __name__ == '__main__':
    unittest.main()
