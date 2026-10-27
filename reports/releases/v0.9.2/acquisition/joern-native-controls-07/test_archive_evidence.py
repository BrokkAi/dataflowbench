from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zlib

import archive_evidence as ae

REPO = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / 'Cargo.toml').is_file()
    and (parent / 'scripts/test-v092-scoped-recovery.py').is_file()
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def octal(value: int, width: int) -> bytes:
    encoded = f"{value:0{width - 1}o}".encode("ascii") + b"\0"
    if len(encoded) > width:
        raise ValueError("octal field too large")
    return encoded


def split_ustar_path(path: str) -> tuple[bytes, bytes]:
    for position in reversed([index for index, value in enumerate(path) if value == "/"]):
        prefix, name = path[:position], path[position + 1:]
        if prefix and len(prefix.encode("ascii")) <= 155 and len(name.encode("ascii")) <= 100:
            return prefix.encode("ascii"), name.encode("ascii")
    if len(path.encode("ascii")) <= 100:
        return b"", path.encode("ascii")
    raise ValueError("path cannot fit a USTAR header")


def ustar_header(path: str, data: bytes, *, typeflag: bytes = b"0", linkname: bytes = b"") -> bytes:
    prefix, name = split_ustar_path(path)
    header = bytearray(512)
    header[0:len(name)] = name
    header[100:108] = octal(0o644, 8)
    header[108:116] = octal(0, 8)
    header[116:124] = octal(0, 8)
    header[124:136] = octal(len(data), 12)
    header[136:148] = octal(0, 12)
    header[148:156] = b" " * 8
    header[156:157] = typeflag
    header[157:157 + len(linkname)] = linkname
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[345:345 + len(prefix)] = prefix
    checksum = sum(header)
    header[148:156] = f"{checksum:06o}".encode("ascii") + b"\0 "
    return bytes(header)


def make_tar(entries: list[tuple[str, bytes]], *, flags: list[bytes] | None = None,
             links: list[bytes] | None = None, trailer: bool = True) -> bytes:
    chunks: list[bytes] = []
    for index, (path, data) in enumerate(entries):
        flag = flags[index] if flags is not None else b"0"
        link = links[index] if links is not None else b""
        chunks.append(ustar_header(path, data, typeflag=flag, linkname=link))
        chunks.append(data)
        chunks.append(b"\0" * ((-len(data)) % 512))
    if trailer:
        chunks.append(b"\0" * 10240)
    return b"".join(chunks)


def gzip_bytes(raw: bytes) -> bytes:
    compressor = zlib.compressobj(level=6, wbits=16 + zlib.MAX_WBITS)
    return compressor.compress(raw) + compressor.flush()


def archive_record(compressed: bytes, tar_bytes: bytes) -> dict:
    return {"bytes": len(compressed), "sha256": sha(compressed), "tar_bytes": len(tar_bytes)}


def synthetic_index() -> tuple[dict, dict[str, bytes]]:
    payloads: dict[str, bytes] = {}
    records = []
    for index in range(ae.EXPECTED_MEMBER_COUNT):
        case_id = f"case-{index:03d}"
        path = ae.ARCHIVE_PREFIX + case_id + "/raw.json"
        size = 4498 if index < 17 else 4497
        value = bytes([index]) * size
        payloads[path] = value
        records.append({"bytes": len(value), "path": path, "sha256": sha(value)})
    index = {
        "archive": {
            "bytes": ae.EXPECTED_ARCHIVE_BYTES,
            "path": ae.ARCHIVE_PATH,
            "sha256": ae.EXPECTED_ARCHIVE_SHA256,
            "tar_bytes": ae.EXPECTED_TAR_BYTES,
        },
        "historical_source_commit": ae.HISTORICAL_SOURCE,
        "member_count": ae.EXPECTED_MEMBER_COUNT,
        "members": records,
        "path_prefix": ae.ARCHIVE_PREFIX,
        "retained_request05": dict(ae.REQUEST05_REF),
        "schema": ae.INDEX_SCHEMA,
        "scope": ae.SCOPE,
        "total_payload_bytes": ae.EXPECTED_PAYLOAD_BYTES,
    }
    return index, payloads


class ArchiveEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payloads = {
            ae.ARCHIVE_PREFIX + f"case-{index:03d}/raw.json":
                ("case-%03d\n" % index).encode("ascii")
            for index in range(ae.EXPECTED_MEMBER_COUNT)
        }
        self.members = {
            path: {"bytes": len(raw), "path": path, "sha256": sha(raw)}
            for path, raw in self.payloads.items()
        }

    def parse_tar(self, entries: list[tuple[str, bytes]], *, members=None, total=None,
                  flags=None, links=None, trailer=True):
        tar = make_tar(entries, flags=flags, links=links, trailer=trailer)
        compressed = gzip_bytes(tar)
        return ae.parse_compressed_archive(
            compressed,
            archive_record=archive_record(compressed, tar),
            members=self.members if members is None else members,
            total_payload_bytes=sum(len(value) for value in self.payloads.values()) if total is None else total,
        )

    def test_exact_96_regular_ustar_members_parse_without_extraction(self):
        entries = list(self.payloads.items())
        result = self.parse_tar(entries)
        self.assertEqual(result, self.payloads)

    def test_index_member_records_and_retained_request05_bind_exact_96_raw_paths(self):
        index, payloads = synthetic_index()
        members = ae._member_specs(index)
        self.assertEqual(set(members), set(payloads))
        refs = [{"path": path, "sha256": sha(raw)} for path, raw in payloads.items()]
        refs.append({"path": "ordinary/input.json", "sha256": "a" * 64})
        request05 = {
            "expected_head": ae.HISTORICAL_SOURCE,
            "schema": "v092-joern-native-control-request/v1",
            "source_refs": refs,
        }
        old = ae._request05_sources(request05, members)
        self.assertEqual(len(old), 97)
        self.assertEqual(index["member_count"], len(members))

    def test_index_rejects_wrong_schema_count_prefix_nested_raw_and_duplicate(self):
        index, _ = synthetic_index()
        mutations = [
            lambda value: value.update(schema="other"),
            lambda value: value.update(member_count=95),
            lambda value: value.update(path_prefix="reports/wrong/"),
            lambda value: value["members"][0].update(path=ae.ARCHIVE_PREFIX + "case/nested/raw.json"),
            lambda value: value["members"].__setitem__(-1, copy.deepcopy(value["members"][0])),
            lambda value: value["members"][0].update(path=ae.ARCHIVE_PREFIX + "../escape/raw.json"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate.__code__.co_firstlineno):
                bad = copy.deepcopy(index)
                mutate(bad)
                with self.assertRaises(ae.ArchiveEvidenceError):
                    ae._member_specs(bad)

    def test_retained_request05_requires_historical_head_exact_raw_subset_and_member_hashes(self):
        index, payloads = synthetic_index()
        members = ae._member_specs(index)
        refs = [{"path": path, "sha256": sha(raw)} for path, raw in payloads.items()]
        base = {"expected_head": ae.HISTORICAL_SOURCE,
                "schema": "v092-joern-native-control-request/v1", "source_refs": refs}
        ae._request05_sources(base, members)
        mutations = [
            lambda req: req.update(expected_head="1" * 40),
            lambda req: req["source_refs"].pop(),
            lambda req: req["source_refs"][0].update(sha256="f" * 64),
            lambda req: req["source_refs"].append({
                "path": ae.ARCHIVE_PREFIX + "off-index/raw.json", "sha256": "0" * 64
            }),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate.__code__.co_firstlineno):
                bad = copy.deepcopy(base)
                mutate(bad)
                with self.assertRaises(ae.ArchiveEvidenceError):
                    ae._request05_sources(bad, members)

    def test_lfs_pointer_is_exact_three_line_lf_pointer(self):
        record = {
            "bytes": ae.EXPECTED_ARCHIVE_BYTES,
            "path": ae.ARCHIVE_PATH,
            "sha256": ae.EXPECTED_ARCHIVE_SHA256,
            "tar_bytes": ae.EXPECTED_TAR_BYTES,
        }
        pointer = ae.lfs_pointer(record)
        self.assertEqual(pointer.count(b"\n"), 3)
        self.assertTrue(pointer.endswith(b"\n"))
        self.assertEqual(pointer.splitlines()[0], b"version https://git-lfs.github.com/spec/v1")
        for key, value in (("bytes", record["bytes"] + 1), ("sha256", "0" * 64),
                           ("path", "elsewhere.tar.gz")):
            bad = dict(record)
            bad[key] = value
            with self.subTest(field=key), self.assertRaises(ae.ArchiveEvidenceError):
                ae.lfs_pointer(bad)

    def test_build_context_binds_current_index_request_helper_live_raw_and_archive_once(self):
        temporary = tempfile.TemporaryDirectory(prefix="archive-evidence-context-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        prefix = "captures/native06/"
        index_path = "qualification/native06-index.json"
        request_path = "qualification/native-control-request-05.json"
        helper_path = "acquisition/archive_evidence.py"
        archive_path = "delivery/native-evidence.tar.gz.part0000"
        historical = "2" * 40
        payloads = {
            prefix + f"case-{index:03d}/raw.json": f"raw fixture {index}\n".encode()
            for index in range(ae.EXPECTED_MEMBER_COUNT)
        }
        ordinary_path = "scripts/test-v092-scoped-recovery.py"
        ordinary_current_bytes = (REPO / ordinary_path).read_bytes()
        ordinary_current_sha = sha(ordinary_current_bytes)
        self.assertEqual(ordinary_current_sha,
                         "41f0f5c6a57557aa11d43e93e6049ba808282527053969ac86f47e7753055335")
        members = [
            {"bytes": len(raw), "path": path, "sha256": sha(raw)}
            for path, raw in payloads.items()
        ]
        tar = make_tar(list(payloads.items()))
        compressed = gzip_bytes(tar)
        archive = {
            "bytes": len(compressed), "path": archive_path,
            "sha256": sha(compressed), "tar_bytes": len(tar),
        }
        request05 = {
            "expected_head": historical,
            "schema": "v092-joern-native-control-request/v1",
            "source_refs": [*({"path": path, "sha256": sha(raw)} for path, raw in payloads.items()),
                            {"path": ordinary_path,
                             "sha256": "9500ad6c863ae06fb354eaa3fa51429ee4bd742a7fefbc5cc3de63898ad02009"}],
        }
        request_raw = (json.dumps(request05, sort_keys=True, separators=(",", ":")) + "\n").encode()
        request_ref = {"path": request_path, "sha256": sha(request_raw)}
        index = {
            "archive": archive,
            "historical_source_commit": historical,
            "member_count": ae.EXPECTED_MEMBER_COUNT,
            "members": members,
            "path_prefix": prefix,
            "retained_request05": request_ref,
            "schema": ae.INDEX_SCHEMA,
            "scope": ae.SCOPE,
            "total_payload_bytes": sum(map(len, payloads.values())),
        }
        index_raw = (json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n").encode()
        index_ref = {"path": index_path, "sha256": sha(index_raw)}
        helper_raw = Path(ae.__file__).read_bytes()
        helper_ref = {"path": helper_path, "sha256": sha(helper_raw)}

        def write(relative: str, raw: bytes) -> None:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

        write(index_path, index_raw)
        write(request_path, request_raw)
        write(helper_path, helper_raw)
        write(archive_path, compressed)
        write(ordinary_path, ordinary_current_bytes)
        for path, raw in payloads.items():
            write(path, raw)
        source_map = {
            ref["path"]: ref for ref in
            [index_ref, request_ref, helper_ref,
             {"path": ordinary_path, "sha256": ordinary_current_sha},
             *({"path": path, "sha256": sha(raw)} for path, raw in payloads.items())]
        }
        with (
            mock.patch.object(ae, "INDEX_REF", index_ref),
            mock.patch.object(ae, "REQUEST05_REF", request_ref),
            mock.patch.object(ae, "HELPER_SOURCE_PATH", helper_path),
            mock.patch.object(ae, "ARCHIVE_PATH", archive_path),
            mock.patch.object(ae, "ARCHIVE_PREFIX", prefix),
            mock.patch.object(ae, "HISTORICAL_SOURCE", historical),
            mock.patch.object(ae, "EXPECTED_ARCHIVE_SHA256", archive["sha256"]),
            mock.patch.object(ae, "EXPECTED_ARCHIVE_BYTES", archive["bytes"]),
            mock.patch.object(ae, "EXPECTED_TAR_BYTES", archive["tar_bytes"]),
            mock.patch.object(ae, "EXPECTED_PAYLOAD_BYTES", sum(map(len, payloads.values()))),
            mock.patch.object(ae, "__file__", str(root / helper_path)),
        ):
            context = ae.build_context(root, source_map)
            self.assertEqual(context.archive_bytes, len(compressed))
            self.assertEqual(context.tar_bytes, len(tar))
            self.assertEqual(context.member_bytes, payloads)
            self.assertIn(helper_path, {ref["path"] for ref in context.required_source_refs})
            self.assertNotIn(ordinary_path, {ref["path"] for ref in context.required_source_refs})
            omitted_obsolete = dict(source_map)
            omitted_obsolete.pop(ordinary_path)
            omitted_context = ae.build_context(root, omitted_obsolete)
            self.assertEqual(set(omitted_context.member_refs), set(payloads))

            changed_path = next(iter(payloads))
            write(changed_path, b"changed live raw input\n")
            with self.assertRaisesRegex(ae.ArchiveEvidenceError, "live archived raw source differs"):
                ae.build_context(root, source_map)

    def test_compressed_byte_length_and_hash_are_required(self):
        entries = list(self.payloads.items())
        tar = make_tar(entries)
        compressed = gzip_bytes(tar)
        record = archive_record(compressed, tar)
        for field, value in (("bytes", len(compressed) + 1), ("sha256", "0" * 64)):
            bad = dict(record)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ae.ArchiveEvidenceError):
                ae.parse_compressed_archive(compressed, archive_record=bad,
                                            members=self.members,
                                            total_payload_bytes=sum(len(v) for v in self.payloads.values()))

    def test_malformed_gzip_trailing_bytes_and_truncated_tar_fail(self):
        good_tar = make_tar(list(self.payloads.items()))
        good_gzip = gzip_bytes(good_tar)
        trailing = good_gzip + b"extra"
        with self.assertRaises(ae.ArchiveEvidenceError):
            ae.parse_compressed_archive(trailing, archive_record=archive_record(trailing, good_tar),
                                        members=self.members,
                                        total_payload_bytes=sum(map(len, self.payloads.values())))
        corrupt = bytearray(good_gzip)
        corrupt[2] ^= 0xFF
        corrupt_bytes = bytes(corrupt)
        with self.assertRaises(ae.ArchiveEvidenceError):
            ae.parse_compressed_archive(corrupt_bytes,
                                        archive_record=archive_record(corrupt_bytes, good_tar),
                                        members=self.members,
                                        total_payload_bytes=sum(map(len, self.payloads.values())))
        no_trailer = make_tar(list(self.payloads.items()), trailer=False)
        compressed = gzip_bytes(no_trailer)
        with self.assertRaisesRegex(ae.ArchiveEvidenceError, "end marker"):
            ae.parse_compressed_archive(compressed, archive_record=archive_record(compressed, no_trailer),
                                        members=self.members,
                                        total_payload_bytes=sum(map(len, self.payloads.values())))

    def test_decompression_limit_is_enforced_before_tar_processing(self):
        oversized = b"z" * (ae.MAX_DECOMPRESSED_BYTES + 1)
        compressed = gzip_bytes(oversized)
        record = archive_record(compressed, oversized)
        with self.assertRaisesRegex(ae.ArchiveEvidenceError, "decompressed archive exceeds"):
            ae.parse_compressed_archive(compressed, archive_record=record, members={},
                                        total_payload_bytes=len(oversized))

    def test_duplicate_pax_symlink_hardlink_directory_and_traversal_entries_fail(self):
        first_path, first_bytes = next(iter(self.payloads.items()))
        cases = [
            ([(first_path, first_bytes), (first_path, first_bytes)], None, "duplicate"),
            ([(first_path, first_bytes)], [b"x"], "regular USTAR"),
            ([(first_path, first_bytes)], [b"1"], "regular USTAR"),
            ([(first_path, first_bytes)], [b"2"], "regular USTAR"),
            ([(first_path, first_bytes)], [b"5"], "regular USTAR"),
            ([(ae.ARCHIVE_PREFIX + "../escape/raw.json", first_bytes)], None, "traversal"),
            ([("/absolute/raw.json", first_bytes)], None, "traversal"),
        ]
        for entries, flags, expected in cases:
            with self.subTest(expected=expected, entry=entries[0][0]):
                tar = make_tar(entries, flags=flags, links=[b"/outside"] if flags == [b"2"] else None)
                compressed = gzip_bytes(tar)
                with self.assertRaisesRegex(ae.ArchiveEvidenceError, expected):
                    ae.parse_compressed_archive(
                        compressed, archive_record=archive_record(compressed, tar),
                        members=self.members,
                        total_payload_bytes=sum(map(len, self.payloads.values())),
                    )

    def test_extra_incomplete_and_tampered_ustar_entries_fail(self):
        entries = list(self.payloads.items())
        path, value = entries[0]
        extra = (ae.ARCHIVE_PREFIX + "unexpected/raw.json", b"extra")
        bad_cases = [
            (entries[:-1], "member set"),
            ([*entries, extra], "extra member"),
            ([(path, b"bad")], "length differs"),
            ([(path, value[:-1] + b"!")], "SHA-256"),
        ]
        for bad_entries, expected in bad_cases:
            with self.subTest(expected=expected), self.assertRaisesRegex(ae.ArchiveEvidenceError, expected):
                tar = make_tar(bad_entries)
                compressed = gzip_bytes(tar)
                ae.parse_compressed_archive(
                    compressed, archive_record=archive_record(compressed, tar),
                    members=self.members,
                    total_payload_bytes=sum(map(len, self.payloads.values())),
                )
        header = bytearray(ustar_header(path, value))
        header[0] ^= 1
        checksum_bad = bytes(header) + value + b"\0" * ((-len(value)) % 512) + b"\0" * 10240
        compressed = gzip_bytes(checksum_bad)
        with self.assertRaisesRegex(ae.ArchiveEvidenceError, "checksum"):
            ae.parse_compressed_archive(
                compressed, archive_record=archive_record(compressed, checksum_bad),
                members=self.members, total_payload_bytes=sum(map(len, self.payloads.values())),
            )


if __name__ == "__main__":
    unittest.main()
