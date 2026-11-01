from __future__ import annotations

from contextlib import contextmanager
import hashlib
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import archive_evidence as ae
import native_qualifier as n


CHECKOUT_ROOT = Path(__file__).resolve().parents[5]
REPO = CHECKOUT_ROOT


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class FakeGit:
    def __init__(self, context: ae.ArchiveContext):
        self.context = context
        self.direct_blobs: dict[str, bytes] = {
            ae.INDEX_REF["path"]: (REPO / ae.INDEX_REF["path"]).read_bytes(),
            ae.REQUEST05_REF["path"]: (REPO / ae.REQUEST05_REF["path"]).read_bytes(),
            context.helper_ref["path"]: Path(ae.__file__).read_bytes(),
            context.archive_path: context.lfs_pointer,
            "scripts/ordinary-a.py": b"ordinary source A\n",
            "reports/ordinary-b.json": b"ordinary source B\n",
        }
        self.missing_paths = set(context.member_refs)
        self.present_overrides: dict[str, bytes] = {}
        self.batch_response: bytes | None = None
        self.batch_returncode = 0
        self.batch_stderr = b""
        self.blob_overrides: dict[str, bytes] = {}
        self.pointer_tree_mode = b"100644"
        self.pointer_tree_override: bytes | None = None
        self.calls: list[tuple[list[str], dict]] = []

    def run(self, argv, *, cwd, input=None, stdout=None, stderr=None, check=None):
        self.calls.append((list(argv), {"cwd": cwd, "input": input}))
        if argv[:3] == ["git", "cat-file", "--batch-check"]:
            if self.batch_response is not None:
                return types.SimpleNamespace(returncode=self.batch_returncode,
                                             stdout=self.batch_response,
                                             stderr=self.batch_stderr)
            output = bytearray()
            for line in input.splitlines():
                identity = line.decode("utf-8")
                path = identity.split(":", 1)[1]
                if path in self.missing_paths:
                    output += line + b" missing\n"
                    continue
                raw = self.present_overrides.get(path, self.direct_blobs.get(path))
                if raw is None:
                    output += line + b" missing\n"
                    continue
                oid = git_oid(raw)
                output += f"{oid} blob {len(raw)}\n".encode("ascii")
            return types.SimpleNamespace(returncode=0, stdout=bytes(output), stderr=b"")
        if argv[:3] == ["git", "cat-file", "blob"]:
            oid = argv[3]
            raw = self.blob_overrides.get(oid)
            if raw is None:
                candidates = [*self.direct_blobs.values(), *self.present_overrides.values(),
                              self.context.lfs_pointer]
                candidates += list(self.blob_overrides.values())
                raw = next((item for item in candidates if git_oid(item) == oid), None)
            if raw is None:
                return types.SimpleNamespace(returncode=1, stdout=b"", stderr=b"missing synthetic object")
            return types.SimpleNamespace(returncode=0, stdout=raw, stderr=b"")
        if argv[:3] == ["git", "ls-tree", "-z"]:
            if self.pointer_tree_override is not None:
                return types.SimpleNamespace(returncode=0, stdout=self.pointer_tree_override, stderr=b"")
            path = argv[-1]
            raw = self.direct_blobs[self.context.archive_path]
            line = (self.pointer_tree_mode + b" blob " + git_oid(raw).encode() + b"\t" +
                    path.encode() + b"\0")
            return types.SimpleNamespace(returncode=0, stdout=line, stderr=b"")
        raise AssertionError(f"unexpected synthetic Git command: {argv!r}")


def fake_context() -> ae.ArchiveContext:
    member_refs: dict[str, dict[str, str]] = {}
    member_bytes: dict[str, bytes] = {}
    member_sizes: dict[str, int] = {}
    for index in range(ae.EXPECTED_MEMBER_COUNT):
        path = ae.ARCHIVE_PREFIX + f"case-{index:03d}/raw.json"
        raw = f"synthetic historical record {index}\n".encode()
        member_refs[path] = {"path": path, "sha256": sha(raw)}
        member_bytes[path] = raw
        member_sizes[path] = len(raw)
    helper_raw = Path(ae.__file__).read_bytes()
    return ae.ArchiveContext(
        index_ref=dict(ae.INDEX_REF),
        request05_ref=dict(ae.REQUEST05_REF),
        helper_ref={"path": ae.HELPER_SOURCE_PATH, "sha256": sha(helper_raw)},
        member_refs=member_refs,
        member_bytes=member_bytes,
        member_sizes=member_sizes,
        required_source_refs=(),
        archive_path=ae.ARCHIVE_PATH,
        lfs_pointer=ae.lfs_pointer({
            "bytes": ae.EXPECTED_ARCHIVE_BYTES,
            "path": ae.ARCHIVE_PATH,
            "sha256": ae.EXPECTED_ARCHIVE_SHA256,
            "tar_bytes": ae.EXPECTED_TAR_BYTES,
        }),
        archive_sha256=ae.EXPECTED_ARCHIVE_SHA256,
        archive_bytes=ae.EXPECTED_ARCHIVE_BYTES,
        tar_bytes=ae.EXPECTED_TAR_BYTES,
        total_payload_bytes=ae.EXPECTED_PAYLOAD_BYTES,
        historical_source_commit=ae.HISTORICAL_SOURCE,
    )


def source_refs(context: ae.ArchiveContext) -> list[dict[str, str]]:
    direct = [
        dict(ae.INDEX_REF),
        dict(ae.REQUEST05_REF),
        context.helper_ref,
        {"path": "scripts/ordinary-a.py", "sha256": sha(b"ordinary source A\n")},
        {"path": "reports/ordinary-b.json", "sha256": sha(b"ordinary source B\n")},
    ]
    return direct + list(context.member_refs.values())


@contextmanager
def patched_git(fake: FakeGit):
    with mock.patch.object(n.subprocess, "run", side_effect=fake.run):
        yield


class ArchiveSourceGateTests(unittest.TestCase):
    def setUp(self):
        self.context = fake_context()
        self.refs = source_refs(self.context)
        self.fake = FakeGit(self.context)
        self.temporary = tempfile.TemporaryDirectory(prefix="archive-source-gate-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        for path, payload in self.context.member_bytes.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

    def verify(self, *, refs=None):
        with patched_git(self.fake):
            return n.verify_current_source_refs(
                self.root, "a" * 40,
                self.refs if refs is None else refs, self.context,
            )

    def test_only_exact_96_explicit_git_missing_members_use_archive_proof(self):
        result = self.verify()
        self.assertEqual(result["current_direct_count"], 5)
        self.assertEqual(result["archived_member_count"], 96)
        self.assertEqual(result["source_ref_count"], 101)
        self.assertEqual(result["archive"]["historical_source_commit"], ae.HISTORICAL_SOURCE)
        self.assertIs(result["archive"]["current_ancestor_claim"], False)
        self.assertEqual(result["archive"]["pointer_bytes"], len(self.context.lfs_pointer))
        self.assertEqual(len(result["archived_member_paths"]), 96)

    def test_missing_off_index_raw_path_fails_without_generic_fallback(self):
        path = ae.ARCHIVE_PREFIX + "off-index/raw.json"
        refs = [*self.refs, {"path": path, "sha256": "a" * 64}]
        with self.assertRaisesRegex(ValueError, "ordinary current source path is explicitly missing"):
            self.verify(refs=refs)

    def test_missing_nonraw_path_inside_capture_prefix_fails_without_fallback(self):
        path = ae.ARCHIVE_PREFIX + "case-extra/metadata.json"
        refs = [*self.refs, {"path": path, "sha256": "a" * 64}]
        with self.assertRaisesRegex(ValueError, "ordinary current source path is explicitly missing"):
            self.verify(refs=refs)

    def test_indexed_raw_present_in_current_head_is_rejected_without_direct_claim(self):
        path = next(iter(self.context.member_refs))
        self.fake.missing_paths.remove(path)
        self.fake.present_overrides[path] = self.context.member_bytes[path]
        with self.assertRaisesRegex(ValueError, "must remain absent from current Git"):
            self.verify()

    def test_current_present_mismatching_archive_raw_fails_and_never_uses_archive_fallback(self):
        path = next(iter(self.context.member_refs))
        self.fake.missing_paths.remove(path)
        self.fake.present_overrides[path] = b"changed current raw blob"
        with self.assertRaisesRegex(ValueError, "must remain absent from current Git"):
            self.verify()

    def test_live_indexed_raw_file_must_still_match_archive_payload(self):
        path = next(iter(self.context.member_refs))
        (self.root / path).write_bytes(b"changed live file")
        with self.assertRaisesRegex(ValueError, "live archived raw source changed"):
            self.verify()

    def test_missing_lfs_pointer_is_explicit_failure(self):
        self.fake.missing_paths.add(self.context.archive_path)
        with self.assertRaisesRegex(ValueError, "committed LFS archive pointer is explicitly missing"):
            self.verify()

    def test_malformed_or_tampered_lfs_pointer_is_rejected(self):
        self.fake.present_overrides[self.context.archive_path] = b"version https://git-lfs.github.com/spec/v1\n"
        with self.assertRaisesRegex(ValueError, "exact indexed three-line pointer"):
            self.verify()

    def test_lfs_pointer_tree_entry_must_be_regular_exact_blob(self):
        self.fake.pointer_tree_mode = b"120000"
        with self.assertRaisesRegex(ValueError, "exact committed regular Git LFS pointer"):
            self.verify()
        self.fake.pointer_tree_mode = b"100644"
        self.fake.pointer_tree_override = b"malformed\0extra\0"
        with self.assertRaisesRegex(ValueError, "malformed tree-entry"):
            self.verify()

    def test_source_closure_index_request_and_helper_must_be_direct_refs(self):
        refs = [ref for ref in self.refs if ref["path"] != ae.INDEX_REF["path"]]
        with self.assertRaisesRegex(ValueError, "outside direct current source closure"):
            self.verify(refs=refs)

    def test_ordinary_current_blob_mismatch_fails(self):
        self.fake.present_overrides["scripts/ordinary-a.py"] = b"changed ordinary source\n"
        with self.assertRaisesRegex(ValueError, "ordinary source input does not match direct current HEAD blob"):
            self.verify()

    def test_cat_file_operational_error_never_becomes_archived_fallback(self):
        self.fake.batch_returncode = 128
        self.fake.batch_stderr = b"synthetic git failure"
        self.fake.batch_response = b""
        with self.assertRaisesRegex(ValueError, "failed operationally"):
            self.verify()

    def test_cat_file_malformed_missing_nonblob_truncated_and_trailing_replies_fail_closed(self):
        malformed = [
            b"",  # truncated response
            b"arbitrary missing\n",  # missing must echo the exact object expression
            b"a" * 40 + b" tree 2\n",  # source references must be blobs
            b"a" * 40 + b" blob 1\nextra\n",  # no unconsumed output
            b"a" * 40 + b" blob nope\n",  # malformed size
        ]
        for response in malformed:
            with self.subTest(response=response[:24]):
                self.fake.batch_response = response
                with self.assertRaises(ValueError):
                    self.verify()
                self.fake.batch_response = None

    def test_git_blob_object_identity_must_match_returned_content(self):
        self.fake.blob_overrides[git_oid(b"ordinary source A\n")] = b"badinary source A\n"
        with self.assertRaisesRegex(ValueError, "content does not match returned object identity"):
            self.verify()

    def test_duplicate_source_path_is_rejected_before_git_lookup(self):
        refs = [*self.refs, self.refs[0]]
        with self.assertRaisesRegex(ValueError, "duplicate current source path"):
            self.verify(refs=refs)
        self.assertEqual(self.fake.calls, [])


if __name__ == "__main__":
    unittest.main()
