#!/usr/bin/env python3
"""Create, verify, selectively restore, or read a lossless evidence bundle.

The bundle format is deliberately generic: callers choose the source scope.
Repeated bytes are stored once, while restores create independent regular files.
Archives are gzip-compressed POSIX tar streams split into bounded-size parts.
Verification establishes delivery integrity only; it does not qualify evidence.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile
import zlib
from typing import BinaryIO, Iterable


BLOCK = 1024 * 1024
SCHEMA = "dataflowbench-lossless-evidence-bundle/v1"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_PLATFORM_PATH_ALIASES = {
    Path("/var"): Path("/private/var"),
    Path("/tmp"): Path("/private/tmp"),
    Path("/etc"): Path("/private/etc"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _lexical_absolute(path: os.PathLike[str] | str) -> Path:
    """Make an absolute path without resolving away symlink components."""
    raw = os.fspath(path)
    require(".." not in Path(raw).parts, "parent path component refused")
    return Path(os.path.abspath(raw))


def _assert_no_symlink_components(path: Path, *, include_self: bool = True) -> None:
    """Reject symlinks anywhere in an existing path prefix (including dangling ones)."""
    path = _lexical_absolute(path)
    components = list(reversed(path.parents))
    if include_self:
        components.append(path)
    for component in components:
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            # No descendant can exist beneath a missing component. The caller may
            # create the remaining suffix after all existing components are checked.
            break
        if stat.S_ISLNK(mode):
            # macOS exposes these fixed system aliases. Permit only the canonical
            # platform links so normal tempfile paths work; arbitrary aliases,
            # including any below these roots, remain rejected.
            target = _PLATFORM_PATH_ALIASES.get(component)
            raw_target = Path(os.readlink(component))
            resolved_target = (raw_target if raw_target.is_absolute() else
                               component.parent / raw_target)
            require(target is not None and _lexical_absolute(resolved_target) == target,
                    f"symlink path component refused: {component}")


def safe_path(value: object) -> PurePosixPath:
    """Validate portable, relative bundle paths using POSIX separators."""
    require(type(value) is str and bool(value), "invalid path")
    require("\x00" not in value and "\\" not in value, "unsafe path")
    # Colons admit drive-relative paths and NTFS alternate data streams. They are
    # not portable bundle names, even though POSIX itself permits them.
    require(":" not in value, "unsafe Windows path")
    p = PurePosixPath(value)
    require(bool(p.parts) and not p.is_absolute() and value == str(p) and
            all(part not in ("", ".", "..") for part in p.parts), "unsafe path")
    return p


def stable_stat(path: Path) -> tuple[int, int, int, int, int, int]:
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode), f"not a regular file: {path}")
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
            stat.S_IMODE(s.st_mode))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            h.update(block)
    return h.hexdigest()


class PartsWriter:
    def __init__(self, directory: Path, limit: int):
        self.directory, self.limit = directory, limit
        self.stream: BinaryIO | None = None
        self.size = 0
        self.paths: list[Path] = []

    def write(self, data: bytes) -> int:
        original = len(data)
        while data:
            if self.stream is None or self.size == self.limit:
                if self.stream:
                    self.stream.close()
                path = self.directory / f"detail.tar.gz.part{len(self.paths):04d}"
                self.stream = path.open("xb")
                self.paths.append(path)
                self.size = 0
            count = min(len(data), self.limit - self.size)
            self.stream.write(data[:count])
            data, self.size = data[count:], self.size + count
        return original

    def flush(self) -> None:
        if self.stream:
            self.stream.flush()

    def close(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None


class PartsReader(io.RawIOBase):
    """Concatenate bundle parts without joining them in memory."""
    def __init__(self, paths: Iterable[Path]):
        self.paths = iter(paths)
        self.stream: BinaryIO | None = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray | memoryview) -> int:
        while True:
            if self.stream is None:
                path = next(self.paths, None)
                if path is None:
                    return 0
                self.stream = path.open("rb")
            count = self.stream.readinto(buffer)
            if count:
                return count
            self.stream.close()
            self.stream = None

    def close(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None
        super().close()


class HashReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.hash = hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        data = self.stream.read(size)
        self.hash.update(data)
        return data


def _source_inventory(root: Path, source: Path) -> tuple[list[dict], dict[str, Path], dict[Path, tuple]]:
    records: list[dict] = []
    objects: dict[str, Path] = {}
    stamps: dict[Path, tuple] = {}
    paths: list[Path] = []
    for base, dirs, files in os.walk(source, followlinks=False):
        base_path = Path(base)
        for name in dirs:
            child = base_path / name
            require(not child.is_symlink(), f"symlink directory refused: {child}")
        for name in files:
            paths.append(base_path / name)

    for path in sorted(paths):
        before = stable_stat(path)
        sha = digest(path)
        require(before == stable_stat(path), f"file changed during hash: {path}")
        relative_path = path.relative_to(root).as_posix()
        safe_path(relative_path)
        record = {"path": relative_path, "sha256": sha,
                  "bytes": before[2], "mode": before[5], "mtime_ns": before[3]}
        records.append(record)
        stamps[path] = before
        objects.setdefault(sha, path)
    return records, objects, stamps


def pack(root: os.PathLike[str] | str, scope: str,
         output: os.PathLike[str] | str, part_bytes: int) -> dict:
    """Pack all regular files under ``root/scope`` into a new bundle directory."""
    root_path = _lexical_absolute(root)
    output_path = _lexical_absolute(output)
    relative = safe_path(scope)
    source = root_path.joinpath(*relative.parts)

    _assert_no_symlink_components(root_path)
    _assert_no_symlink_components(source)
    _assert_no_symlink_components(output_path.parent)
    require(source.is_dir() and not source.is_symlink(), "invalid evidence scope")
    require(not output_path.exists() and not os.path.lexists(output_path),
            "output bundle already exists")
    require(not output_path.is_relative_to(source), "output must be outside evidence scope")
    require(not Path(os.path.realpath(output_path)).is_relative_to(
        Path(os.path.realpath(source))), "output must be outside evidence scope")
    require(type(part_bytes) is int and 1024 <= part_bytes <= 40 * BLOCK,
            "part limit must be between 1 KiB and 40 MiB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(output_path.parent)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_path.name}.staging-",
                                  dir=output_path.parent))
    try:
        records, objects, stamps = _source_inventory(root_path, source)
        manifest = stage / "files.jsonl.gz"
        with manifest.open("xb") as raw, gzip.GzipFile(filename="", mode="wb",
                                                         fileobj=raw, mtime=0) as gz:
            for record in records:
                gz.write((json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))

        parts = PartsWriter(stage, part_bytes)
        try:
            with gzip.GzipFile(filename="", mode="wb", fileobj=parts, mtime=0) as gz:
                with tarfile.open(mode="w|", fileobj=gz,
                                  format=tarfile.USTAR_FORMAT) as tar:
                    for sha, path in sorted(objects.items()):
                        require(stamps[path] == stable_stat(path),
                                "source changed before compression")
                        info = tarfile.TarInfo("objects/" + sha)
                        info.size, info.mode, info.mtime = stamps[path][2], 0o644, 0
                        with path.open("rb") as stream:
                            reader = HashReader(stream)
                            tar.addfile(info, reader)
                        require(reader.hash.hexdigest() == sha,
                                "source changed during compression")
        finally:
            parts.close()

        for path, before in stamps.items():
            require(before == stable_stat(path), f"snapshot source changed: {path}")
        index = {
            "schema": SCHEMA,
            "scope": str(relative),
            "snapshot_file_count": len(records),
            "original_bytes": sum(record["bytes"] for record in records),
            "unique_objects": len(objects),
            "unique_object_bytes": sum(stamps[path][2] for path in objects.values()),
            "manifest": {"path": manifest.name, "sha256": digest(manifest),
                         "bytes": manifest.stat().st_size},
            "parts": [{"path": path.name, "sha256": digest(path),
                       "bytes": path.stat().st_size} for path in parts.paths],
            "scope_note": "Files inventoried at pack start only; later files require a successor snapshot.",
            "originals_modified": False,
            "benchmark_qualification": False,
            "publication_authorized": False,
        }
        with (stage / "bundle.json").open("x", encoding="utf-8") as stream:
            json.dump(index, stream, indent=2)
            stream.write("\n")
        _assert_no_symlink_components(stage)
        require(not os.path.lexists(output_path), "output bundle appeared during pack")
        os.rename(stage, output_path)
        return index
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _nonnegative_int(value: object, message: str) -> int:
    require(type(value) is int and value >= 0, message)
    return value


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"invalid JSON constant: {value}")


def _read_index(bundle: Path) -> dict:
    _assert_no_symlink_components(bundle)
    require(bundle.is_dir(), "bundle must be a directory")
    bundle_json = bundle / "bundle.json"
    _assert_no_symlink_components(bundle_json)
    require(stat.S_ISREG(bundle_json.lstat().st_mode), "bundle.json is not a regular file")
    try:
        with bundle_json.open("r", encoding="utf-8") as stream:
            index = json.load(stream, object_pairs_hook=_unique_json_object,
                              parse_constant=_reject_json_constant)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"invalid bundle metadata: {exc}") from exc
    require(type(index) is dict and index.get("schema") == SCHEMA, "unknown or invalid schema")
    return index


def _validated_index(bundle: Path) -> tuple[dict, PurePosixPath, list[dict], list[dict]]:
    index = _read_index(bundle)
    scope = safe_path(index.get("scope"))
    _nonnegative_int(index.get("snapshot_file_count"), "invalid snapshot file count")
    _nonnegative_int(index.get("original_bytes"), "invalid original byte count")
    _nonnegative_int(index.get("unique_objects"), "invalid unique object count")
    _nonnegative_int(index.get("unique_object_bytes"), "invalid unique object byte count")
    require(type(index.get("manifest")) is dict, "invalid manifest metadata")
    require(type(index.get("parts")) is list and index["parts"], "missing bundle parts")
    manifest = index["manifest"]
    parts = index["parts"]
    items = [manifest, *parts]
    names: list[str] = []
    for item in items:
        require(type(item) is dict, "invalid bundle file metadata")
        p = safe_path(item.get("path"))
        require(len(p.parts) == 1 and p.name != "bundle.json",
                "bundle files must be direct children")
        require(type(item.get("sha256")) is str and HASH_RE.fullmatch(item["sha256"]),
                "invalid bundle file digest")
        _nonnegative_int(item.get("bytes"), "invalid bundle file size")
        names.append(p.name)
    require(len(set(names)) == len(names), "duplicate bundle file reference")

    expected_children = {"bundle.json", *names}
    try:
        children = list(bundle.iterdir())
    except OSError as exc:
        raise ValueError(f"cannot enumerate bundle directory: {exc}") from exc
    require({child.name for child in children} == expected_children,
            "bundle directory contents differ from metadata")
    for child in children:
        _assert_no_symlink_components(child)
        require(stat.S_ISREG(child.lstat().st_mode),
                f"bundle child is not a regular file: {child.name}")

    for item in items:
        path = bundle / item["path"]
        require(stable_stat(path)[2] == item["bytes"] and digest(path) == item["sha256"],
                f"bundle digest mismatch: {item['path']}")
    return index, scope, manifest, parts


def _manifest_records(bundle: Path, index: dict, scope: PurePosixPath,
                      manifest: dict) -> tuple[list[dict], dict[str, list[dict]]]:
    records: list[dict] = []
    by_object: dict[str, list[dict]] = collections.defaultdict(list)
    try:
        with gzip.open(bundle / manifest["path"], "rt", encoding="utf-8", newline="") as stream:
            for line in stream:
                try:
                    record = json.loads(line, object_pairs_hook=_unique_json_object,
                                         parse_constant=_reject_json_constant)
                except ValueError as exc:
                    raise ValueError(f"invalid manifest JSON: {exc}") from exc
                require(type(record) is dict, "invalid manifest record")
                path = safe_path(record.get("path"))
                require(path != scope and path.is_relative_to(scope),
                        "manifest path outside scope")
                sha = record.get("sha256")
                require(type(sha) is str and HASH_RE.fullmatch(sha),
                        "invalid object digest")
                size = _nonnegative_int(record.get("bytes"), "invalid file size")
                mode = record.get("mode")
                require(type(mode) is int and 0 <= mode <= 0o7777,
                        "invalid file mode")
                mtime_ns = record.get("mtime_ns")
                require(type(mtime_ns) is int, "invalid file mtime")
                normalized = {"path": str(path), "sha256": sha,
                              "bytes": size, "mode": mode, "mtime_ns": mtime_ns}
                records.append(normalized)
                by_object[sha].append(normalized)
    except (OSError, EOFError, gzip.BadGzipFile, UnicodeError) as exc:
        raise ValueError(f"invalid compressed manifest: {exc}") from exc

    _nonnegative_int(index["snapshot_file_count"], "invalid snapshot file count")
    require(len(records) == index["snapshot_file_count"] and
            len({record["path"] for record in records}) == len(records),
            "manifest count or duplicate path")
    file_paths = {PurePosixPath(record["path"]) for record in records}
    require(not any(parent in file_paths for path in file_paths for parent in path.parents),
            "manifest file/child path collision")
    require(all(len({record["bytes"] for record in values}) == 1
                for values in by_object.values()), "object size differs across manifest")
    require(sum(record["bytes"] for record in records) == index["original_bytes"] and
            len(by_object) == index["unique_objects"] and
            sum(values[0]["bytes"] for values in by_object.values()) ==
            index["unique_object_bytes"], "manifest totals differ")
    return records, by_object


def _selected_records(records: list[dict], paths: Iterable[str] | str | None) -> dict[str, list[dict]]:
    all_by_path = {record["path"]: record for record in records}
    if paths is None:
        selected = set(all_by_path)
    else:
        values = [paths] if isinstance(paths, str) else list(paths)
        selected = set()
        for value in values:
            path = str(safe_path(value))
            require(path not in selected, "duplicate selected path")
            selected.add(path)
        missing = selected.difference(all_by_path)
        if missing:
            raise ValueError(f"selected path missing from manifest: {sorted(missing)[0]}")
    return {record["path"]: record for path, record in all_by_path.items()
            if path in selected}


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        block = stream.read(size - len(chunks))
        if not block:
            break
        chunks.extend(block)
    return bytes(chunks)


def _copy_object(source: BinaryIO, size: int, sha: str,
                 destinations: list[BinaryIO], capture: io.BytesIO | None) -> None:
    h = hashlib.sha256()
    remaining = size
    while remaining:
        block = source.read(min(BLOCK, remaining))
        require(bool(block), "truncated archive object")
        h.update(block)
        for destination in destinations:
            destination.write(block)
        if capture is not None:
            capture.write(block)
        remaining -= len(block)
    require(h.hexdigest() == sha, "uncompressed object digest differs")


def _verify_archive(bundle: Path, parts: list[dict], by_object: dict[str, list[dict]],
                    selected: dict[str, dict], stage: Path | None,
                    capture_path: str | None) -> tuple[set[str], io.BytesIO | None]:
    selected_by_object: dict[str, list[dict]] = collections.defaultdict(list)
    for record in selected.values():
        selected_by_object[record["sha256"]].append(record)
    seen: set[str] = set()
    capture: io.BytesIO | None = io.BytesIO() if capture_path is not None else None
    final_metadata: list[tuple[Path, int, int]] = []
    part_paths = [bundle / item["path"] for item in parts]

    try:
        with PartsReader(part_paths) as raw:
            with gzip.GzipFile(fileobj=io.BufferedReader(raw), mode="rb") as archive:
                while True:
                    header = _read_exact(archive, 512)
                    require(len(header) == 512, "truncated tar header or missing archive trailer")
                    if header == b"\x00" * 512:
                        second = _read_exact(archive, 512)
                        require(second == b"\x00" * 512,
                                "invalid tar end marker")
                        # POSIX tar writers pad to a record boundary. The remainder
                        # must be zero padding; this also rejects hidden extra members.
                        zero_count = 1024
                        while True:
                            block = archive.read(BLOCK)
                            if not block:
                                break
                            require(not any(block), "nonzero bytes after tar end marker")
                            zero_count += len(block)
                        require(zero_count >= 1024, "missing tar end marker")
                        break

                    try:
                        member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
                    except (tarfile.HeaderError, UnicodeError, ValueError) as exc:
                        raise ValueError(f"invalid tar header: {exc}") from exc
                    require(member.isfile() and member.type in (tarfile.REGTYPE, tarfile.AREGTYPE),
                            "non-regular archive member refused")
                    name = member.name
                    require(name.startswith("objects/"), "unexpected archive member")
                    sha = name.removeprefix("objects/")
                    require(HASH_RE.fullmatch(sha) is not None and name == "objects/" + sha and
                            sha in by_object and sha not in seen,
                            "unexpected archive object")
                    require(type(member.size) is int and member.size >= 0 and
                            all(record["bytes"] == member.size for record in by_object[sha]),
                            "object size differs")

                    object_targets = selected_by_object.get(sha, []) if stage is not None else []
                    spool = tempfile.TemporaryFile() if object_targets else None
                    try:
                        capture_for_object = (
                            capture if capture_path is not None and
                            selected.get(capture_path, {}).get("sha256") == sha else None
                        )
                        destinations = [spool] if spool is not None else []
                        _copy_object(archive, member.size, sha, destinations,
                                     capture_for_object)
                        if spool is not None and stage is not None:
                            for record in object_targets:
                                target = stage.joinpath(*PurePosixPath(record["path"]).parts)
                                target.parent.mkdir(parents=True, exist_ok=True)
                                _assert_no_symlink_components(target.parent)
                                spool.seek(0)
                                with target.open("xb") as output:
                                    shutil.copyfileobj(spool, output, BLOCK)
                                final_metadata.append((target, record["mode"],
                                                       record["mtime_ns"]))
                    finally:
                        if spool is not None:
                            spool.close()
                    padding_size = (-member.size) % 512
                    padding = _read_exact(archive, padding_size)
                    require(len(padding) == padding_size and not any(padding),
                            "invalid tar member padding")
                    seen.add(sha)

        require(seen == set(by_object), "missing archive objects")
        # Apply metadata only after the complete archive, gzip trailer, and all
        # object digests have been verified. The staged tree is still unpublished.
        for target, mode, mtime_ns in final_metadata:
            target.chmod(mode)
            os.utime(target, ns=(mtime_ns, mtime_ns), follow_symlinks=False)
        return seen, capture
    except (EOFError, OSError, zlib.error) as exc:
        raise ValueError(f"invalid or truncated archive: {exc}") from exc


def _prepare_restore_path(restore: os.PathLike[str] | str) -> tuple[Path, Path]:
    destination = _lexical_absolute(restore)
    _assert_no_symlink_components(destination.parent)
    require(not os.path.lexists(destination), "restore destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(destination.parent)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-",
                                  dir=destination.parent))
    return destination, stage


def check(bundle: os.PathLike[str] | str, restore: os.PathLike[str] | str | None = None,
          paths: Iterable[str] | str | None = None) -> dict:
    """Verify a bundle and optionally atomically restore all or selected paths."""
    bundle_path = _lexical_absolute(bundle)
    index, scope, manifest, parts = _validated_index(bundle_path)
    records, by_object = _manifest_records(bundle_path, index, scope, manifest)
    selected = _selected_records(records, paths)
    destination: Path | None = None
    stage: Path | None = None
    if restore is not None:
        destination, stage = _prepare_restore_path(restore)
    try:
        seen, _ = _verify_archive(bundle_path, parts, by_object, selected, stage, None)
        if stage is not None and destination is not None:
            _assert_no_symlink_components(stage)
            require(not os.path.lexists(destination), "restore destination appeared during verification")
            os.rename(stage, destination)
            stage = None
        return {"status": "verified", "files": len(records), "objects": len(seen),
                "original_bytes": index["original_bytes"],
                "compressed_bytes": sum(item["bytes"] for item in parts) + manifest["bytes"],
                "restored": destination is not None,
                "restored_files": len(selected) if destination is not None else 0}
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)


def read_file(bundle: os.PathLike[str] | str, path: str) -> bytes:
    """Return one file only after full bundle, object, archive, and trailer checks."""
    bundle_path = _lexical_absolute(bundle)
    index, scope, manifest, parts = _validated_index(bundle_path)
    records, by_object = _manifest_records(bundle_path, index, scope, manifest)
    selected = _selected_records(records, path)
    selected_path = str(safe_path(path))
    captured_sha = selected[selected_path]["sha256"]
    seen, captured = _verify_archive(bundle_path, parts, by_object, selected, None,
                                     selected_path)
    require(seen == set(by_object) and captured is not None and
            hashlib.sha256(captured.getvalue()).hexdigest() == captured_sha,
            "selected file verification failed")
    return captured.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack", help="create a lossless bundle")
    pack_parser.add_argument("root", type=Path)
    pack_parser.add_argument("scope")
    pack_parser.add_argument("output", type=Path)
    pack_parser.add_argument("--part-bytes", type=int, default=40 * BLOCK)
    check_parser = commands.add_parser("check", help="verify and optionally restore a bundle")
    check_parser.add_argument("bundle", type=Path)
    check_parser.add_argument("--restore", type=Path)
    check_parser.add_argument("--path", action="append", dest="paths")
    args = parser.parse_args()
    if args.command == "pack":
        result = pack(args.root, args.scope, args.output, args.part_bytes)
    else:
        result = check(args.bundle, args.restore, args.paths)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
