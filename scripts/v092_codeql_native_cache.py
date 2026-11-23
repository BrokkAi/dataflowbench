#!/usr/bin/env python3
"""Prepare and verify an offline CodeQL package cache for native runs.

This utility only materializes the already-pinned, manifest-bound CodeQL pack
tree into an isolated HOME's default package cache. It never invokes CodeQL and
does not establish suite discovery, analysis, or semantic qualification.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELOCATED_MANIFEST = Path(
    "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/"
    "relocated-manifests/codeql-packs.json.gz"
)
DEFAULT_ORIGINAL_MANIFEST = Path(
    "reports/releases/v0.9.2/acquisition/runtime-manifests/codeql-packs.json"
)
DEFAULT_RELOCATION_RECEIPT = Path(
    "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/"
    "relocated-manifests-receipt-v2.json"
)
DEFAULT_ACQUISITION_RECEIPT = Path(
    "reports/releases/v0.9.2/acquisition/codeql-packs-download.json"
)

SCHEMA = "dataflowbench.v092-codeql-native-cache-preparation.v1"
RELOCATION_SCHEMA = "dataflowbench.jvm-runtime-relocation-receipt.v2"
MANIFEST_KEYS = {"schema_version", "root", "files", "symlinks", "external_files"}
FILE_KEYS = {"path", "sha256", "mode"}
LINK_KEYS = {"path", "target", "mode"}

# Exact package identities from the retained CodeQL acquisition receipt.
PACK_PINS: dict[str, tuple[str, bool]] = {
    "codeql/java-all": ("9.3.2", True),
    "codeql/python-all": ("7.2.7", True),
    "codeql/javascript-all": ("2.10.3", True),
    "codeql/csharp-all": ("7.4.0", True),
    "codeql/go-all": ("8.0.0", True),
    "codeql/cpp-all": ("12.2.0", True),
    "codeql/ruby-all": ("7.0.2", True),
    "codeql/rust-all": ("0.2.23", True),
    "codeql/swift-all": ("6.8.5", True),
    "codeql/java-queries": ("1.11.12", False),
    "codeql/javascript-queries": ("2.4.7", False),
    "codeql/python-queries": ("1.8.12", False),
}
NATIVE_SUITES = (
    "codeql/java-queries/1.11.12/codeql-suites/java-security-extended.qls",
    "codeql/javascript-queries/2.4.7/codeql-suites/javascript-security-extended.qls",
    "codeql/python-queries/1.8.12/codeql-suites/python-security-extended.qls",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PACKAGE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PACKAGE_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


class CachePreparationError(RuntimeError):
    """A fail-closed preparation or verification error."""


def _json_no_duplicate_keys(raw: bytes, description: str):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CachePreparationError(f"duplicate JSON key in {description}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CachePreparationError(f"invalid JSON in {description}: {exc}") from exc


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular_file(path: Path, description: str) -> bytes:
    try:
        info = path.lstat()
    except OSError as exc:
        raise CachePreparationError(f"{description} is unavailable: {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise CachePreparationError(f"{description} is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CachePreparationError(f"could not read {description}: {path}") from exc


def _safe_relative(raw: object, description: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise CachePreparationError(f"unsafe relative path for {description}: {raw!r}")
    relative = PurePosixPath(raw)
    if (relative.is_absolute() or relative.as_posix() != raw
            or any(part in {"", ".", ".."} for part in relative.parts)):
        raise CachePreparationError(f"unsafe relative path for {description}: {raw!r}")
    return relative


def _safe_link_target(link_path: PurePosixPath, raw: object) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw or "\x00" in raw:
        raise CachePreparationError(f"unsafe symlink target for {link_path}: {raw!r}")
    stack = list(link_path.parent.parts)
    for part in raw.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not stack:
                raise CachePreparationError(f"symlink escapes package root: {link_path} -> {raw}")
            stack.pop()
        else:
            stack.append(part)
    if not stack:
        raise CachePreparationError(f"symlink does not target a package file: {link_path}")
    return PurePosixPath(*stack)


def _validate_mode(value: object, description: str) -> int:
    if type(value) is not int or not 0 <= value <= 0o777:
        raise CachePreparationError(f"invalid POSIX mode for {description}: {value!r}")
    return value


def _validate_inventory(manifest: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise CachePreparationError("unsupported CodeQL pack manifest schema/fields")
    if manifest.get("schema_version") != 1:
        raise CachePreparationError("unsupported CodeQL pack manifest version")
    root_value = manifest.get("root")
    if not isinstance(root_value, str) or not Path(root_value).is_absolute():
        raise CachePreparationError("manifest root must be an absolute path")
    if not all(isinstance(manifest.get(key), list) for key in ("files", "symlinks", "external_files")):
        raise CachePreparationError("manifest inventory sections must be lists")
    if manifest["external_files"]:
        raise CachePreparationError("external CodeQL pack files are unsupported")

    files: dict[str, dict] = {}
    links: dict[str, dict] = {}
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != FILE_KEYS:
            raise CachePreparationError("unsupported file entry in CodeQL pack manifest")
        relative = _safe_relative(entry["path"], "manifest file")
        path = relative.as_posix()
        digest = entry["sha256"]
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise CachePreparationError(f"invalid manifest digest: {path}")
        mode = _validate_mode(entry["mode"], path)
        if path in files or path in links:
            raise CachePreparationError(f"duplicate manifest path: {path}")
        files[path] = {"path": path, "sha256": digest, "mode": mode}

    for entry in manifest["symlinks"]:
        if not isinstance(entry, dict) or set(entry) != LINK_KEYS:
            raise CachePreparationError("unsupported symlink entry in CodeQL pack manifest")
        relative = _safe_relative(entry["path"], "manifest symlink")
        path = relative.as_posix()
        target = entry["target"]
        _safe_link_target(relative, target)
        mode = _validate_mode(entry["mode"], path)
        if path in files or path in links:
            raise CachePreparationError(f"duplicate manifest path: {path}")
        links[path] = {"path": path, "target": target, "mode": mode}

    if not files:
        raise CachePreparationError("CodeQL pack manifest contains no regular files")
    return files, links


def _derive_pack_versions(paths, acquisition_pins: dict[str, tuple[str, bool]]) -> list[dict]:
    roots: set[tuple[str, str]] = set()
    for path in paths:
        parts = PurePosixPath(path).parts
        if len(parts) < 4 or parts[0] != "codeql":
            raise CachePreparationError(f"manifest path is outside the versioned CodeQL pack layout: {path}")
        name = f"{parts[0]}/{parts[1]}"
        version = parts[2]
        if (not PACKAGE_SEGMENT_RE.fullmatch(parts[1])
                or not PACKAGE_VERSION_RE.fullmatch(version)
                or version.lower() == "latest"):
            raise CachePreparationError(f"unsafe CodeQL package path identity: {path}")
        roots.add((name, version))

    roots_by_name: dict[str, set[str]] = {}
    for name, version in roots:
        roots_by_name.setdefault(name, set()).add(version)
    ambiguous = [name for name, versions in roots_by_name.items() if len(versions) != 1]
    if ambiguous:
        raise CachePreparationError(f"multiple package versions are present in the cache tree: {sorted(ambiguous)[0]}")
    for name, (expected_version, _) in acquisition_pins.items():
        if expected_version not in roots_by_name.get(name, set()):
            raise CachePreparationError(f"manifest lacks exact acquisition pack: {name}@{expected_version}")
    return [
        {"name": name, "version": version,
         "acquisition_pin": name in acquisition_pins and acquisition_pins[name][0] == version,
         "library": acquisition_pins[name][1] if name in acquisition_pins
         and acquisition_pins[name][0] == version else None}
        for name, version in sorted(roots)
    ]


def _validate_pack_receipt(acquisition: dict, manifest: dict,
                           files: dict[str, dict], links: dict[str, dict]) -> list[dict]:
    if not isinstance(acquisition, dict) or set(acquisition) != {"packDir", "packs"}:
        raise CachePreparationError("unsupported CodeQL pack acquisition receipt")
    if acquisition.get("packDir") != manifest.get("root"):
        raise CachePreparationError("acquisition packDir differs from the original manifest root")
    packs = acquisition.get("packs")
    if not isinstance(packs, list) or len(packs) != len(PACK_PINS):
        raise CachePreparationError("CodeQL acquisition package set is incomplete or unexpected")
    actual: dict[str, dict] = {}
    for pack in packs:
        if not isinstance(pack, dict) or set(pack) != {"name", "version", "library", "result"}:
            raise CachePreparationError("unsupported CodeQL package receipt entry")
        name, version = pack["name"], pack["version"]
        if (not isinstance(name, str) or name.count("/") != 1
                or not all(PACKAGE_SEGMENT_RE.fullmatch(part) for part in name.split("/"))):
            raise CachePreparationError(f"unsafe CodeQL package name: {name!r}")
        if (not isinstance(version, str) or not version or version.lower() == "latest"
                or "/" in version or "\\" in version or version in {".", ".."}):
            raise CachePreparationError(f"unsafe or floating CodeQL package version: {version!r}")
        if name in actual:
            raise CachePreparationError(f"duplicate CodeQL package receipt entry: {name}")
        if pack["result"] != "INSTALLED":
            raise CachePreparationError(f"CodeQL package was not installed: {name}@{version}")
        if type(pack["library"]) is not bool:
            raise CachePreparationError(f"invalid library flag for {name}")
        actual[name] = pack

    if set(actual) != set(PACK_PINS):
        raise CachePreparationError("CodeQL acquisition package names differ from the frozen native pack set")

    for name, (expected_version, expected_library) in PACK_PINS.items():
        pack = actual[name]
        if pack["version"] != expected_version or pack["library"] is not expected_library:
            raise CachePreparationError(f"CodeQL package pin differs: {name}")
    pack_versions = _derive_pack_versions((*files.keys(), *links.keys()), PACK_PINS)
    for suite in NATIVE_SUITES:
        if suite not in files:
            raise CachePreparationError(f"manifest lacks exact native security suite: {suite}")

    for path, link in links.items():
        if any(candidate.startswith(path + "/") for candidate in files) or any(
                candidate.startswith(path + "/") for candidate in links):
            raise CachePreparationError(f"symlink directories are unsupported: {path}")
        target = _safe_link_target(PurePosixPath(path), link["target"]).as_posix()
        seen: set[str] = set()
        while target in links:
            if target in seen:
                raise CachePreparationError(f"symlink cycle in CodeQL manifest: {path}")
            seen.add(target)
            target = _safe_link_target(PurePosixPath(target), links[target]["target"]).as_posix()
        if target not in files or files[target]["mode"] != link["mode"]:
            raise CachePreparationError(f"symlink target is not a pinned file with matching mode: {path}")
    return pack_versions


def _load_bound_inputs(repo_root: Path, relocated_manifest_path: Path,
                       original_manifest_path: Path, relocation_receipt_path: Path,
                       acquisition_receipt_path: Path):
    repo_root = repo_root.resolve(strict=True)
    relocated_manifest_path = _resolve_argument_path(repo_root, relocated_manifest_path)
    original_manifest_path = _resolve_argument_path(repo_root, original_manifest_path)
    relocation_receipt_path = _resolve_argument_path(repo_root, relocation_receipt_path)
    acquisition_receipt_path = _resolve_argument_path(repo_root, acquisition_receipt_path)

    relocation_raw = _read_regular_file(relocation_receipt_path, "relocation receipt")
    relocation = _json_no_duplicate_keys(relocation_raw, str(relocation_receipt_path))
    if not isinstance(relocation, dict) or relocation.get("schema") != RELOCATION_SCHEMA:
        raise CachePreparationError("unsupported CodeQL pack relocation receipt")
    manifests = relocation.get("manifests")
    if not isinstance(manifests, list):
        raise CachePreparationError("relocation receipt has no manifest list")
    rows = [item for item in manifests if isinstance(item, dict) and item.get("manifest_id") == "codeql-packs"]
    if len(rows) != 1:
        raise CachePreparationError("relocation receipt must bind exactly one codeql-packs manifest")
    row = rows[0]
    if row.get("changed_json_property") != "root" or row.get("compressed") is not True:
        raise CachePreparationError("CodeQL pack relocation did not use the supported root-only gzip form")
    if row.get("closure_status") != "passed-static-full-tree-hash-mode-symlink-and-external-file-check":
        raise CachePreparationError("CodeQL pack source closure was not statically verified")
    if not isinstance(row.get("manifest_path"), str) or row["manifest_path"] != _relative_to_root(
            relocated_manifest_path, repo_root):
        raise CachePreparationError("relocation receipt points at a different CodeQL pack manifest")
    if not isinstance(row.get("source_path"), str) or row["source_path"] != _relative_to_root(
            original_manifest_path, repo_root):
        raise CachePreparationError("relocation receipt points at a different original manifest")

    relocated_raw_file = _read_regular_file(relocated_manifest_path, "relocated CodeQL pack manifest")
    compressed_sha = _sha256(relocated_raw_file)
    if compressed_sha != row.get("manifest_sha256"):
        raise CachePreparationError("relocated CodeQL pack manifest archive digest differs")
    try:
        relocated_raw = gzip.decompress(relocated_raw_file)
    except (OSError, EOFError) as exc:
        raise CachePreparationError("relocated CodeQL pack manifest gzip is corrupt") from exc
    uncompressed_sha = _sha256(relocated_raw)
    if uncompressed_sha != row.get("uncompressed_sha256"):
        raise CachePreparationError("relocated CodeQL pack manifest content digest differs")
    if row.get("uncompressed_bytes") != len(relocated_raw):
        raise CachePreparationError("relocated CodeQL pack manifest byte count differs")

    original_raw = _read_regular_file(original_manifest_path, "original CodeQL pack manifest")
    original_sha = _sha256(original_raw)
    if original_sha != row.get("source_sha256") or original_sha != row.get("source_audit_manifest_sha256"):
        raise CachePreparationError("original CodeQL pack manifest digest differs from relocation receipt")
    original = _json_no_duplicate_keys(original_raw, str(original_manifest_path))
    relocated = _json_no_duplicate_keys(relocated_raw, str(relocated_manifest_path))
    if not isinstance(original, dict) or not isinstance(relocated, dict):
        raise CachePreparationError("CodeQL pack manifest must be a JSON object")
    source_root = original.get("root")
    new_root = row.get("new_root")
    if (source_root != row.get("source_root") or relocated.get("root") != new_root
            or not isinstance(new_root, str) or not Path(new_root).is_absolute()):
        raise CachePreparationError("CodeQL pack roots differ from relocation receipt")
    expected_relocated = dict(original)
    expected_relocated["root"] = new_root
    if relocated != expected_relocated:
        raise CachePreparationError("relocated manifest differs beyond its recorded root rewrite")

    acquisition_raw = _read_regular_file(acquisition_receipt_path, "CodeQL pack acquisition receipt")
    acquisition = _json_no_duplicate_keys(acquisition_raw, str(acquisition_receipt_path))
    files, links = _validate_inventory(relocated)
    pack_versions = _validate_pack_receipt(acquisition, original, files, links)
    source_root_path = Path(new_root)
    try:
        source_info = source_root_path.lstat()
    except OSError as exc:
        raise CachePreparationError(f"CodeQL pack source root is unavailable: {source_root_path}") from exc
    if not stat.S_ISDIR(source_info.st_mode) or stat.S_ISLNK(source_info.st_mode):
        raise CachePreparationError(f"CodeQL pack source root is not a real directory: {source_root_path}")
    if source_root_path.resolve(strict=True) != source_root_path.absolute():
        raise CachePreparationError("CodeQL pack source root resolves through a symlink or alternate path")
    return {
        "repo_root": repo_root,
        "relocated_manifest_path": relocated_manifest_path,
        "original_manifest_path": original_manifest_path,
        "relocation_receipt_path": relocation_receipt_path,
        "acquisition_receipt_path": acquisition_receipt_path,
        "relocation_sha256": _sha256(relocation_raw),
        "acquisition_sha256": _sha256(acquisition_raw),
        "manifest_sha256": compressed_sha,
        "manifest_uncompressed_sha256": uncompressed_sha,
        "original_manifest_sha256": original_sha,
        "source_root": source_root_path,
        "original_source_root": source_root,
        "manifest": relocated,
        "files": files,
        "links": links,
        "pack_versions": pack_versions,
    }


def _source_binding(inputs: dict) -> dict:
    return {
        "manifest_path": _relative_to_root(inputs["relocated_manifest_path"], inputs["repo_root"]),
        "manifest_sha256": inputs["manifest_sha256"],
        "manifest_uncompressed_sha256": inputs["manifest_uncompressed_sha256"],
        "original_manifest_path": _relative_to_root(inputs["original_manifest_path"], inputs["repo_root"]),
        "original_manifest_sha256": inputs["original_manifest_sha256"],
        "relocation_receipt_path": _relative_to_root(inputs["relocation_receipt_path"], inputs["repo_root"]),
        "relocation_receipt_sha256": inputs["relocation_sha256"],
        "acquisition_receipt_path": _relative_to_root(inputs["acquisition_receipt_path"], inputs["repo_root"]),
        "acquisition_receipt_sha256": inputs["acquisition_sha256"],
        "original_root": inputs["original_source_root"],
        "relocated_root": str(inputs["source_root"]),
    }


def _expected_target_inventory(inputs: dict) -> list[dict]:
    inventory = [
        {"path": path, "kind": "file", "sha256": entry["sha256"], "mode": entry["mode"]}
        for path, entry in inputs["files"].items()
    ]
    inventory.extend(
        {"path": path, "kind": "symlink", "target": entry["target"], "mode": entry["mode"]}
        for path, entry in inputs["links"].items()
    )
    return sorted(inventory, key=lambda entry: entry["path"])


def _resolve_argument_path(repo_root: Path, path: Path) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    candidate = Path(os.path.abspath(candidate))
    resolved = candidate.resolve(strict=True)
    if resolved != candidate:
        raise CachePreparationError(f"path resolves through a symlink or alternate path: {candidate}")
    return candidate


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise CachePreparationError(f"bound manifest must be inside repository: {path}") from exc


def _scan_tree(root: Path, expected_files: dict[str, dict], expected_links: dict[str, dict],
               *, hash_files: bool) -> list[dict]:
    try:
        root_info = root.lstat()
    except OSError as exc:
        raise CachePreparationError(f"tree root is unavailable: {root}") from exc
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        raise CachePreparationError(f"tree root is not a real directory: {root}")

    seen_files: set[str] = set()
    seen_links: set[str] = set()
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(directory)
        for name in list(dirnames):
            item = current / name
            rel = item.relative_to(root).as_posix()
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                dirnames.remove(name)
                if rel not in expected_links:
                    raise CachePreparationError(f"unlisted source symlink: {rel}")
                seen_links.add(rel)
            elif not stat.S_ISDIR(info.st_mode):
                raise CachePreparationError(f"unsupported source directory entry: {rel}")
        for name in filenames:
            item = current / name
            rel = item.relative_to(root).as_posix()
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                if rel not in expected_links:
                    raise CachePreparationError(f"unlisted source symlink: {rel}")
                seen_links.add(rel)
            elif stat.S_ISREG(info.st_mode):
                if rel not in expected_files:
                    raise CachePreparationError(f"unlisted source file: {rel}")
                seen_files.add(rel)
                expected = expected_files[rel]
                mode = stat.S_IMODE(info.st_mode)
                if mode != expected["mode"]:
                    raise CachePreparationError(f"source file mode differs: {rel}")
                if hash_files:
                    actual_sha = _hash_regular_source(item, info, expected["mode"])
                    if actual_sha != expected["sha256"]:
                        raise CachePreparationError(f"source file SHA-256 differs: {rel}")
            else:
                raise CachePreparationError(f"unsupported source file type: {rel}")

    missing_files = set(expected_files) - seen_files
    missing_links = set(expected_links) - seen_links
    if missing_files:
        raise CachePreparationError(f"source tree is missing manifest file: {sorted(missing_files)[0]}")
    if missing_links:
        raise CachePreparationError(f"source tree is missing manifest symlink: {sorted(missing_links)[0]}")

    inventory: list[dict] = []
    for path in sorted(expected_files):
        expected = expected_files[path]
        inventory.append({"path": path, "kind": "file", "sha256": expected["sha256"],
                          "mode": expected["mode"]})
    for path in sorted(expected_links):
        expected = expected_links[path]
        source_link = root / Path(*PurePosixPath(path).parts)
        try:
            actual_target = os.readlink(source_link)
        except OSError as exc:
            raise CachePreparationError(f"source symlink cannot be read: {path}") from exc
        if actual_target != expected["target"]:
            raise CachePreparationError(f"source symlink target differs: {path}")
        _verify_link_target(root, path, expected, expected_files, expected_links)
        inventory.append({"path": path, "kind": "symlink", "target": expected["target"],
                          "mode": expected["mode"]})
    return sorted(inventory, key=lambda item: item["path"])


def _hash_regular_source(path: Path, previous_info, expected_mode: int) -> str:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CachePreparationError(f"could not securely open source file: {path}") from exc
    digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != expected_mode:
                raise CachePreparationError(f"source file type or mode changed: {path}")
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (
                    previous_info.st_dev, previous_info.st_ino, previous_info.st_size, previous_info.st_mtime_ns):
                raise CachePreparationError(f"source file changed during inventory: {path}")
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise CachePreparationError(f"source file changed while being read: {path}")
    except OSError as exc:
        raise CachePreparationError(f"could not read source file: {path}") from exc
    return digest.hexdigest()


def _verify_link_target(root: Path, relative: str, link: dict,
                        files: dict[str, dict], links: dict[str, dict]) -> str:
    cursor = relative
    seen = set()
    while cursor in links:
        if cursor in seen:
            raise CachePreparationError(f"symlink cycle detected: {relative}")
        seen.add(cursor)
        target_path = _safe_link_target(PurePosixPath(cursor), links[cursor]["target"])
        cursor = target_path.as_posix()
    if cursor not in files or files[cursor]["mode"] != link["mode"]:
        raise CachePreparationError(f"symlink target is not a manifest file with matching mode: {relative}")
    resolved = (root / Path(*PurePosixPath(relative).parts)).resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)):
        raise CachePreparationError(f"symlink resolves outside its root: {relative}")
    return cursor


def _copy_file(source_root: Path, destination_root: Path, entry: dict) -> None:
    relative = PurePosixPath(entry["path"])
    source = source_root / Path(*relative.parts)
    destination = destination_root / Path(*relative.parts)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(source, flags)
    except OSError as exc:
        raise CachePreparationError(f"could not securely open source file: {source}") from exc
    digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as incoming:
            before = os.fstat(incoming.fileno())
            if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != entry["mode"]:
                raise CachePreparationError(f"source file type or mode differs during copy: {entry['path']}")
            with destination.open("xb") as outgoing:
                for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                    outgoing.write(chunk)
                    digest.update(chunk)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            after = os.fstat(incoming.fileno())
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise CachePreparationError(f"source file changed during copy: {entry['path']}")
    except OSError as exc:
        raise CachePreparationError(f"could not copy source file: {entry['path']}") from exc
    if digest.hexdigest() != entry["sha256"]:
        raise CachePreparationError(f"source file SHA-256 differs during copy: {entry['path']}")
    try:
        destination.chmod(entry["mode"])
    except OSError as exc:
        raise CachePreparationError(f"could not preserve destination mode: {entry['path']}") from exc


def _copy_links(destination_root: Path, links: dict[str, dict]) -> None:
    for path, entry in sorted(links.items()):
        relative = PurePosixPath(path)
        destination = destination_root / Path(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        try:
            os.symlink(entry["target"], destination)
        except OSError as exc:
            raise CachePreparationError(f"could not preserve manifest symlink: {path}") from exc


def _verify_target_inventory(root: Path, files: dict[str, dict], links: dict[str, dict]) -> list[dict]:
    inventory = _scan_tree(root, files, links, hash_files=True)
    for path, link in links.items():
        _verify_link_target(root, path, link, files, links)
    return inventory


def _fresh_home_and_destination(home: Path) -> tuple[Path, Path, bool]:
    try:
        info = home.lstat()
    except OSError as exc:
        raise CachePreparationError(f"isolated HOME must already exist: {home}") from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise CachePreparationError(f"isolated HOME is not a real directory: {home}")
    if home.resolve(strict=True) != home.absolute():
        raise CachePreparationError("isolated HOME resolves through a symlink or alternate path")
    codeql_home = home / ".codeql"
    created_codeql_home = False
    if codeql_home.exists() or codeql_home.is_symlink():
        if codeql_home.is_symlink() or not codeql_home.is_dir():
            raise CachePreparationError(f"CodeQL cache root is not a real directory: {codeql_home}")
    else:
        created_codeql_home = True
    destination = codeql_home / "packages"
    if destination.exists() or destination.is_symlink():
        raise CachePreparationError(f"refusing to reuse CodeQL package cache: {destination}")
    return codeql_home, destination, created_codeql_home


def _write_new_receipt(path: Path, receipt: dict) -> None:
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise CachePreparationError(f"receipt parent must be an existing real directory: {parent}")
    if path.exists() or path.is_symlink():
        raise CachePreparationError(f"append-only preparation receipt already exists: {path}")
    payload = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise CachePreparationError(f"could not create append-only receipt: {path}") from exc
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise CachePreparationError(f"could not write append-only receipt: {path}") from exc


def _validated_receipt_path(repo_root: Path, receipt_path: Path,
                            source_root: Path, destination: Path) -> Path:
    candidate = receipt_path if receipt_path.is_absolute() else repo_root / receipt_path
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(repo_root)
    except ValueError as exc:
        raise CachePreparationError("append-only receipt must be inside the repository") from exc
    cursor = repo_root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink() or (cursor.exists() and not cursor.is_dir()):
            raise CachePreparationError(f"receipt path traverses a non-directory or symlink: {cursor}")
        if not cursor.exists():
            raise CachePreparationError(f"receipt parent directory does not exist: {cursor}")
    if candidate.is_relative_to(destination) or candidate.is_relative_to(source_root):
        raise CachePreparationError("receipt must be outside both source and destination pack trees")
    return candidate


def _failure_receipt(inputs: dict, home: Path, codeql_home: Path, destination: Path,
                     *, cache_created: bool, cache_state: str, error: Exception) -> dict:
    return {
        "schema": SCHEMA,
        "status": "failed",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "operation": "offline-exact-pack-cache-materialization",
        "source": _source_binding(inputs),
        "target": {
            "home": str(home),
            "common_cache_root": str(codeql_home),
            "package_cache_root": str(destination),
            "cache_state": cache_state,
            "inventory_status": "not-captured-for-failed-preparation",
            "expected_file_count": len(inputs["files"]),
            "expected_symlink_count": len(inputs["links"]),
            "pack_versions": inputs["pack_versions"],
        },
        "failure": {
            "phase": "offline-cache-preparation",
            "error_type": type(error).__name__,
            "error": str(error),
            "partial_cache_retained": cache_created,
            "retry_requires_new_home_and_receipt_path": True,
        },
        "qualification": {
            "suite_discovery": "unproven",
            "analysis": "unproven",
            "semantic_qualification": "unproven",
            "publication_eligible": False,
        },
    }


def _append_failure_receipt(requested_path: Path, receipt: dict) -> Path | None:
    """Append a failure receipt at a fresh path without replacing prior evidence."""
    candidates = [requested_path]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = requested_path.suffix or ".json"
    stem = requested_path.name[:-len(requested_path.suffix)] if requested_path.suffix else requested_path.name
    candidates.extend(
        requested_path.with_name(f"{stem}.failure-{stamp}-{index}{suffix}")
        for index in range(1, 11)
    )
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            continue
        try:
            _write_new_receipt(candidate, receipt)
            return candidate
        except CachePreparationError:
            if candidate.exists() or candidate.is_symlink():
                continue
            return None
    return None


def prepare_cache(*, home: Path, receipt_path: Path, repo_root: Path = ROOT,
                  relocated_manifest_path: Path = DEFAULT_RELOCATED_MANIFEST,
                  original_manifest_path: Path = DEFAULT_ORIGINAL_MANIFEST,
                  relocation_receipt_path: Path = DEFAULT_RELOCATION_RECEIPT,
                  acquisition_receipt_path: Path = DEFAULT_ACQUISITION_RECEIPT) -> dict:
    """Validate the pinned tree and copy it into a fresh HOME/.codeql/packages."""
    inputs = _load_bound_inputs(repo_root, relocated_manifest_path, original_manifest_path,
                                relocation_receipt_path, acquisition_receipt_path)
    raw_home = home if home.is_absolute() else inputs["repo_root"] / home
    home = Path(os.path.abspath(raw_home))
    codeql_home = home / ".codeql"
    destination = codeql_home / "packages"
    receipt_path = _validated_receipt_path(inputs["repo_root"], receipt_path,
                                           inputs["source_root"], destination)
    did_create_codeql_home = False
    did_create_destination = False
    try:
        if receipt_path.exists() or receipt_path.is_symlink():
            raise CachePreparationError(f"append-only preparation receipt already exists: {receipt_path}")
        codeql_home, destination, created_codeql_home = _fresh_home_and_destination(home)
        if created_codeql_home:
            try:
                codeql_home.mkdir(mode=0o700)
            except FileExistsError as exc:
                raise CachePreparationError(f"CodeQL cache root appeared during preparation: {codeql_home}") from exc
            did_create_codeql_home = True
        destination.mkdir(mode=0o755)
        did_create_destination = True
        # Validate the complete source before copying, after reserving this fresh
        # destination so a failed attempt cannot be retried in the same HOME.
        _scan_tree(inputs["source_root"], inputs["files"], inputs["links"], hash_files=True)
        for path in sorted(inputs["files"]):
            _copy_file(inputs["source_root"], destination, inputs["files"][path])
        _copy_links(destination, inputs["links"])
        target_inventory = _verify_target_inventory(destination, inputs["files"], inputs["links"])
        receipt = {
            "schema": SCHEMA,
            "status": "prepared",
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "operation": "offline-exact-pack-cache-materialization",
            "source": _source_binding(inputs),
            "target": {
                "home": str(home),
                "common_cache_root": str(codeql_home),
                "package_cache_root": str(destination),
                "inventory": target_inventory,
                "file_count": len(inputs["files"]),
                "symlink_count": len(inputs["links"]),
                "pack_versions": inputs["pack_versions"],
            },
            "qualification": {
                "suite_discovery": "unproven",
                "analysis": "unproven",
                "semantic_qualification": "unproven",
                "publication_eligible": False,
            },
        }
        _write_new_receipt(receipt_path, receipt)
        return {"receipt": str(receipt_path), "package_cache_root": str(destination),
                "file_count": len(inputs["files"]), "symlink_count": len(inputs["links"]),
                "pack_versions": inputs["pack_versions"], "qualification": receipt["qualification"]}
    except Exception as exc:
        cache_created = did_create_codeql_home or did_create_destination
        if cache_created:
            cache_state = "partial-retained"
        elif destination.exists() or destination.is_symlink():
            cache_state = "preexisting-refused"
        else:
            cache_state = "not-created"
        failure = _failure_receipt(inputs, home, codeql_home, destination,
                                   cache_created=cache_created, cache_state=cache_state, error=exc)
        failure_path = _append_failure_receipt(receipt_path, failure)
        if failure_path is not None:
            raise CachePreparationError(f"{exc}; failed preparation receipt: {failure_path}") from exc
        if isinstance(exc, CachePreparationError):
            raise
        raise CachePreparationError(f"unexpected preparation failure: {exc}") from exc


def verify_receipt(receipt_path: Path, *, repo_root: Path = ROOT) -> dict:
    """Verify the current package-cache tree against its immutable receipt."""
    repo_root = repo_root.resolve(strict=True)
    receipt_path = _resolve_argument_path(repo_root, receipt_path)
    _relative_to_root(receipt_path, repo_root)
    raw = _read_regular_file(receipt_path, "CodeQL cache preparation receipt")
    receipt = _json_no_duplicate_keys(raw, str(receipt_path))
    if (not isinstance(receipt, dict) or set(receipt) != {
            "schema", "status", "created_at_utc", "operation", "source", "target", "qualification"}
            or receipt.get("schema") != SCHEMA or receipt.get("status") != "prepared"):
        raise CachePreparationError("unsupported CodeQL native cache receipt")
    if receipt.get("operation") != "offline-exact-pack-cache-materialization":
        raise CachePreparationError("cache receipt operation is unsupported")
    source = receipt.get("source")
    source_keys = {
        "manifest_path", "manifest_sha256", "manifest_uncompressed_sha256",
        "original_manifest_path", "original_manifest_sha256", "relocation_receipt_path",
        "relocation_receipt_sha256", "acquisition_receipt_path", "acquisition_receipt_sha256",
        "original_root", "relocated_root",
    }
    if not isinstance(source, dict) or set(source) != source_keys:
        raise CachePreparationError("cache receipt source bindings are incomplete or unsupported")
    for key in ("manifest_path", "original_manifest_path", "relocation_receipt_path",
                "acquisition_receipt_path"):
        if not isinstance(source[key], str):
            raise CachePreparationError(f"cache receipt source path is invalid: {key}")
    inputs = _load_bound_inputs(
        repo_root,
        Path(source["manifest_path"]),
        Path(source["original_manifest_path"]),
        Path(source["relocation_receipt_path"]),
        Path(source["acquisition_receipt_path"]),
    )
    if source != _source_binding(inputs):
        raise CachePreparationError("cache receipt source bindings differ from retained manifests/receipts")

    target = receipt.get("target")
    if not isinstance(target, dict) or set(target) != {
            "home", "common_cache_root", "package_cache_root", "inventory", "file_count",
            "symlink_count", "pack_versions"}:
        raise CachePreparationError("cache receipt target fields are incomplete or unsupported")
    if receipt.get("qualification") != {
            "suite_discovery": "unproven", "analysis": "unproven",
            "semantic_qualification": "unproven", "publication_eligible": False}:
        raise CachePreparationError("cache receipt must keep all qualification claims unproven")
    if any(not isinstance(target.get(key), str) for key in ("home", "common_cache_root", "package_cache_root")):
        raise CachePreparationError("cache receipt target paths must be strings")
    home = Path(target["home"])
    root = Path(target["package_cache_root"])
    if (not home.is_absolute() or not root.is_absolute()
            or root != home / ".codeql" / "packages"
            or target["common_cache_root"] != str(home / ".codeql")):
        raise CachePreparationError("receipt package cache path is not HOME/.codeql/packages")
    try:
        canonical_home = home.resolve(strict=True)
        canonical_root = root.resolve(strict=True)
    except OSError as exc:
        raise CachePreparationError("receipt HOME or package cache path is unavailable") from exc
    if home != Path(os.path.abspath(home)) or canonical_home != home or canonical_root != root:
        raise CachePreparationError("receipt HOME or package cache path resolves through an unsafe path")

    inventory = target.get("inventory")
    if not isinstance(inventory, list):
        raise CachePreparationError("receipt target inventory must be a list")
    expected_inventory = _expected_target_inventory(inputs)
    if inventory != expected_inventory:
        raise CachePreparationError("receipt target inventory differs from the bound source manifest")
    if (type(target.get("file_count")) is not int or type(target.get("symlink_count")) is not int
            or target.get("file_count") != len(inputs["files"])
            or target.get("symlink_count") != len(inputs["links"])):
        raise CachePreparationError("receipt inventory counts differ")
    if target.get("pack_versions") != inputs["pack_versions"]:
        raise CachePreparationError("receipt CodeQL pack identities differ from bound source manifest")
    actual = _verify_target_inventory(root, inputs["files"], inputs["links"])
    if actual != inventory:
        raise CachePreparationError("cache inventory differs from append-only receipt")
    return {"receipt": str(receipt_path), "package_cache_root": str(root),
            "file_count": len(inputs["files"]), "symlink_count": len(inputs["links"]), "verified": True,
            "qualification": receipt["qualification"]}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="materialize exact pinned packs into a fresh isolated HOME")
    prepare.add_argument("--home", type=Path, required=True, help="existing, isolated HOME directory")
    prepare.add_argument("--receipt", type=Path, required=True, help="new append-only JSON receipt path")
    prepare.add_argument("--relocated-manifest", type=Path, default=DEFAULT_RELOCATED_MANIFEST)
    prepare.add_argument("--original-manifest", type=Path, default=DEFAULT_ORIGINAL_MANIFEST)
    prepare.add_argument("--relocation-receipt", type=Path, default=DEFAULT_RELOCATION_RECEIPT)
    prepare.add_argument("--acquisition-receipt", type=Path, default=DEFAULT_ACQUISITION_RECEIPT)
    verify = commands.add_parser("verify", help="verify a prepared cache against its receipt")
    verify.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_cache(
                home=args.home,
                receipt_path=args.receipt,
                relocated_manifest_path=args.relocated_manifest,
                original_manifest_path=args.original_manifest,
                relocation_receipt_path=args.relocation_receipt,
                acquisition_receipt_path=args.acquisition_receipt,
            )
        else:
            result = verify_receipt(args.receipt)
        print(json.dumps(result, sort_keys=True))
        return 0
    except CachePreparationError as exc:
        print(f"CodeQL cache preparation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
