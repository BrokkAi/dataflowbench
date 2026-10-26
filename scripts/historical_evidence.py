#!/usr/bin/env python3
"""Verify and selectively restore the pre-filter DataFlowBench history.

The archived bundle is an evidence source, not a checkout source.  This module
validates the manifest and its byte-for-byte bundle parts before using a cached
bare Git repository.  Only paths named by the manifest can be restored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_RELATIVE = Path("evidence-archives/main-before-20261026/manifest.json")
PINNED_ORIGINAL_MAIN = "7fd8c3252a5ed0e03ec7bbc2d96ad0306613c64b"
PINNED_REWRITTEN_BASE = "2494ec1f232e2e16144e5fc6bfbcd60511a9474d"
EXPECTED_PRESERVED_TAGS = {
    "v0.1.0": "a0d19c19cd21e660d135162c6dc16a621e186e7e",
    "v0.2.0": "56673b6169f4bfbf4bbd82ff06ed4289d0eaa9bc",
    "v0.3.0": "b7269a5b507c5bb4d78dc97dee1d31cbb72bcbac",
    "v0.4.0": "306211a3f65c9574b2239241da38397a84cf6f7f",
    "v0.5.0": "7d688c61e8404d07905a46f498b0d98aa9f20d16",
    "v0.6.0": "8b70fd39d4c8777af40adadd70c6d91467a7299e",
    "v0.6.1": "a8cde574287c93e802d9a9253875db141d8b87be",
    "v0.7.0": "0a4d8b66c1e458b10e2c6196d0e4f9622f4c8ef5",
    "v0.7.1": "5aecced386d02258cbcc79435d08e45858c3de45",
    "v0.8.0": "129722f0f042b297ac3229b16bafcb667935c9e3",
    "v0.9.0": "f861b51aabfc98b56315d9097eda58d1801e4558",
}
PART_LIMIT = 40 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceError(RuntimeError):
    """An evidence archive or lineage assertion failed closed."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _require_object(value: Any, keys: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise EvidenceError(f"{where} must contain exactly: {', '.join(sorted(keys))}")
    return value


def _safe_relative_path(value: Any, where: str, *, allow_trailing_slash: bool = False) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise EvidenceError(f"{where} is not a safe relative path")
    if value.startswith("/") or value.startswith("~"):
        raise EvidenceError(f"{where} must be repository-relative")
    check = value[:-1] if allow_trailing_slash and value.endswith("/") else value
    if not check or check.endswith("/"):
        raise EvidenceError(f"{where} has an empty path component")
    parts = check.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise EvidenceError(f"{where} contains an unsafe path component")
    if any(any(ord(ch) < 0x20 for ch in part) for part in parts):
        raise EvidenceError(f"{where} contains a control character")
    return value


def _safe_lstat_chain(base: Path, relative: Path, *, final_regular: bool) -> os.stat_result:
    """Inspect every component without following symlinks."""
    current = base
    parts = relative.parts
    if not parts:
        raise EvidenceError("empty path")
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise EvidenceError(f"cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise EvidenceError(f"symlink is not allowed in path: {current}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise EvidenceError(f"non-directory path component: {current}")
    if final_regular and not stat.S_ISREG(info.st_mode):
        raise EvidenceError(f"expected a regular file: {current}")
    return info


def _open_nofollow(base: Path, relative: Path) -> int:
    """Open a regular file after a no-follow check of its path components."""
    info = _safe_lstat_chain(base, relative, final_regular=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(base / relative, flags)
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        raise EvidenceError(f"file changed while being opened: {base / relative}")
    return fd


def _manifest_for(root: Path) -> tuple[Path, dict[str, Any]]:
    try:
        root_path = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise EvidenceError(f"repository root does not exist: {root}: {exc}") from exc
    if not root_path.is_dir():
        raise EvidenceError(f"repository root is not a directory: {root_path}")
    rel = MANIFEST_RELATIVE
    _safe_lstat_chain(root_path, rel, final_regular=True)
    fd = _open_nofollow(root_path, rel)
    try:
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(1024 * 1024 + 1)
    except OSError as exc:
        raise EvidenceError(f"cannot read manifest: {exc}") from exc
    if len(raw) > 1024 * 1024:
        raise EvidenceError("manifest is larger than 1 MiB")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"manifest is not valid UTF-8 JSON: {exc}") from exc
    _validate_manifest(manifest)
    return root_path, manifest


def _validate_manifest(value: Any) -> None:
    manifest = _require_object(
        value,
        {
            "schema_version",
            "original_main",
            "rewritten_base",
            "original_ref",
            "preserved_tags",
            "removed_paths",
            "bundle",
        },
        "manifest",
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise EvidenceError("unsupported manifest schema_version")
    for key in ("original_main", "rewritten_base"):
        if not isinstance(manifest[key], str) or not HEX40.fullmatch(manifest[key]):
            raise EvidenceError(f"{key} must be a full lowercase SHA-1 object ID")
    if manifest["original_main"] != PINNED_ORIGINAL_MAIN:
        raise EvidenceError("manifest original_main does not match this migration's pinned source commit")
    if manifest["rewritten_base"] != PINNED_REWRITTEN_BASE:
        raise EvidenceError("manifest rewritten_base does not match this migration's pinned filtered base")
    if manifest["original_ref"] != "refs/remotes/origin/main":
        raise EvidenceError("original_ref must be refs/remotes/origin/main")

    tags = manifest["preserved_tags"]
    if not isinstance(tags, dict) or not tags:
        raise EvidenceError("preserved_tags must be a non-empty object")
    for tag, object_id in tags.items():
        if not isinstance(tag, str) or not tag or tag.startswith("-") or tag == "@":
            raise EvidenceError("invalid preserved tag name")
        if any(ord(ch) < 33 or ord(ch) == 127 or ch in "~^:?*[\\" for ch in tag):
            raise EvidenceError(f"invalid preserved tag name: {tag!r}")
        if not isinstance(object_id, str) or not HEX40.fullmatch(object_id):
            raise EvidenceError(f"preserved tag {tag!r} must have a full lowercase SHA-1 object ID")
        if ".." in tag or "@{" in tag or tag.endswith(".") or tag.endswith("/") or "//" in tag:
            raise EvidenceError(f"invalid preserved tag name: {tag!r}")
        if any(part in ("", ".", "..") or part.startswith(".") or part.endswith(".lock") for part in tag.split("/")):
            raise EvidenceError(f"invalid preserved tag name: {tag!r}")
    if tags != EXPECTED_PRESERVED_TAGS:
        raise EvidenceError("manifest preserved_tags do not match this migration's pinned tag identities")

    removed = _require_object(manifest["removed_paths"], {"prefixes", "files"}, "removed_paths")
    if not isinstance(removed["prefixes"], list) or not isinstance(removed["files"], list):
        raise EvidenceError("removed path prefixes and files must be arrays")
    prefixes: list[str] = []
    files: list[str] = []
    for prefix in removed["prefixes"]:
        prefix = _safe_relative_path(prefix, "removed prefix", allow_trailing_slash=True)
        if not prefix.endswith("/"):
            raise EvidenceError("removed directory prefixes must end with '/'")
        prefixes.append(prefix)
    for file_path in removed["files"]:
        file_path = _safe_relative_path(file_path, "removed file")
        if file_path.endswith("/"):
            raise EvidenceError("removed file paths must not end with '/'")
        files.append(file_path)
    if len(set(prefixes)) != len(prefixes) or len(set(files)) != len(files):
        raise EvidenceError("removed path entries must be unique")
    for index, left in enumerate(prefixes):
        if any(other.startswith(left) or left.startswith(other) for other in prefixes[index + 1 :]):
            raise EvidenceError("removed directory prefixes must not overlap")
        if any(file_path.startswith(left) for file_path in files):
            raise EvidenceError("removed file entries must not overlap a directory prefix")
    if _path_is_removed("reports/freeze.json", prefixes, files) or any(
        path.startswith("results/") for path in files
    ):
        raise EvidenceError("frozen report files must not be in removed_paths")
    if any(prefix.startswith("results/") or prefix == "results/" for prefix in prefixes):
        raise EvidenceError("results/ must not be in removed_paths")

    bundle = _require_object(manifest["bundle"], {"sha256", "bytes", "parts"}, "bundle")
    if not isinstance(bundle["sha256"], str) or not HEX64.fullmatch(bundle["sha256"]):
        raise EvidenceError("bundle.sha256 must be a lowercase SHA-256 digest")
    if type(bundle["bytes"]) is not int or bundle["bytes"] <= 0:
        raise EvidenceError("bundle.bytes must be a positive integer")
    if not isinstance(bundle["parts"], list) or not bundle["parts"]:
        raise EvidenceError("bundle.parts must be a non-empty array")
    part_paths: list[str] = []
    total = 0
    for index, part_value in enumerate(bundle["parts"]):
        part = _require_object(part_value, {"path", "sha256", "bytes"}, f"bundle.parts[{index}]")
        part_path = _safe_relative_path(part["path"], f"bundle.parts[{index}].path")
        if not isinstance(part["sha256"], str) or not HEX64.fullmatch(part["sha256"]):
            raise EvidenceError(f"bundle.parts[{index}].sha256 must be a lowercase SHA-256 digest")
        if type(part["bytes"]) is not int or part["bytes"] <= 0 or part["bytes"] > PART_LIMIT:
            raise EvidenceError(f"bundle.parts[{index}].bytes must be between 1 and {PART_LIMIT}")
        part_paths.append(part_path)
        total += part["bytes"]
    if len(set(part_paths)) != len(part_paths):
        raise EvidenceError("bundle part paths must be unique")
    if total != bundle["bytes"]:
        raise EvidenceError("bundle part byte counts do not add up to bundle.bytes")


def _path_is_removed(path: str, prefixes: list[str], files: list[str]) -> bool:
    return path in files or any(path.startswith(prefix) for prefix in prefixes)


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_CONFIG_") or key in {
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR",
            "GIT_PREFIX",
            "GIT_CEILING_DIRECTORIES",
            "GIT_TRACE",
            "GIT_TRACE_SETUP",
            "GIT_TRACE_PACKET",
            "GIT_TRACE_PERFORMANCE",
        }:
            env.pop(key, None)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(root: Path, args: list[str], *, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    git = shutil.which("git")
    if not git:
        raise EvidenceError("git executable was not found")
    command = [git, "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", str(root), *args]
    result = subprocess.run(command, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_git_env())
    if check and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace").strip()
        raise EvidenceError(f"git {' '.join(args)} failed: {stderr or result.returncode}")
    return result


def _repo_root(root_path: Path) -> tuple[Path, Path, str]:
    root_path = root_path.resolve(strict=True)
    top = _git(root_path, ["rev-parse", "--show-toplevel"]).stdout.decode("utf-8", "strict").strip()
    top_path = Path(top).resolve(strict=True)
    if top_path != root_path:
        raise EvidenceError(f"--root must be the worktree root (found {top_path})")
    gitdir_text = _git(root_path, ["rev-parse", "--absolute-git-dir"]).stdout.decode("utf-8", "strict").strip()
    gitdir = Path(gitdir_text).resolve(strict=True)
    if not gitdir.is_dir():
        raise EvidenceError(f"Git directory is not a directory: {gitdir}")
    head = _git(root_path, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.decode("ascii", "strict").strip()
    if not HEX40.fullmatch(head):
        raise EvidenceError("current HEAD is not a full SHA-1 commit")
    return root_path, gitdir, head


def _ensure_directory(path: Path) -> None:
    """Create cache directories while refusing symlinked path components."""
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            try:
                os.mkdir(current, 0o700)
            except FileExistsError:
                pass
            info = os.lstat(current)
        except OSError as exc:
            raise EvidenceError(f"cannot inspect cache directory {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise EvidenceError(f"cache path component is not a real directory: {current}")


def _sha256_file(path: Path) -> tuple[str, int]:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise EvidenceError(f"expected a regular file: {path}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        raise EvidenceError(f"file changed while being hashed: {path}")
    digest = hashlib.sha256()
    total = 0
    with os.fdopen(fd, "rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def _cache_paths(root: Path, gitdir: Path, bundle_sha: str) -> tuple[Path, Path, Path]:
    history_root = gitdir / "historical-evidence"
    cache_root = history_root / bundle_sha
    _ensure_directory(cache_root)
    return history_root, cache_root / "original-history.bundle", cache_root / "archive.git"


def _assert_object_store_has_no_symlinks(objects: Path) -> None:
    try:
        root_info = os.lstat(objects)
    except OSError as exc:
        raise EvidenceError(f"cannot inspect cached Git object store: {exc}") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise EvidenceError("cached archive Git objects path must be a real directory")

    pending = [objects]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode):
                        raise EvidenceError(f"symlink in cached Git object store: {entry.path}")
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(Path(entry.path))
                    elif not stat.S_ISREG(info.st_mode):
                        raise EvidenceError(f"non-regular entry in cached Git object store: {entry.path}")
        except OSError as exc:
            raise EvidenceError(f"cannot inspect cached Git object store: {exc}") from exc


def _check_part_inventory(root: Path, manifest: dict[str, Any]) -> None:
    archive_dir = MANIFEST_RELATIVE.parent
    expected = {part["path"] for part in manifest["bundle"]["parts"]}
    checked: set[tuple[str, str]] = set()
    for part_path in expected:
        relative = PurePosixPath(part_path)
        basename = relative.name
        marker = basename.rfind(".part")
        if marker < 0:
            continue
        prefix = basename[: marker + len(".part")]
        parent = relative.parent
        key = (str(parent), prefix)
        if key in checked:
            continue
        checked.add(key)
        directory_rel = archive_dir / Path(*parent.parts) if parent.parts else archive_dir
        directory_info = _safe_lstat_chain(root, directory_rel, final_regular=False)
        if not stat.S_ISDIR(directory_info.st_mode):
            raise EvidenceError(f"bundle part directory is not a real directory: {directory_rel}")
        directory = root / directory_rel
        with os.scandir(directory) as entries:
            for entry in entries:
                if not entry.name.startswith(prefix):
                    continue
                child_path = (parent / entry.name).as_posix()
                if child_path not in expected:
                    raise EvidenceError(f"unlisted bundle part found: {child_path}")


def _assemble_bundle(root: Path, gitdir: Path, manifest: dict[str, Any]) -> tuple[Path, Path]:
    bundle = manifest["bundle"]
    archive_dir = MANIFEST_RELATIVE.parent
    history_root, cached_bundle, archive_repo = _cache_paths(root, gitdir, bundle["sha256"])
    _check_part_inventory(root, manifest)
    temp_path: Path | None = None
    temp_fd: int | None = None
    if cached_bundle.exists() or cached_bundle.is_symlink():
        info = os.lstat(cached_bundle)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise EvidenceError("cached bundle is not a regular file")
        digest, size = _sha256_file(cached_bundle)
        if digest != bundle["sha256"] or size != bundle["bytes"]:
            raise EvidenceError("cached bundle does not match the verified archive hash")
    else:
        temp_fd, temp_name = tempfile.mkstemp(prefix="bundle-", suffix=".tmp", dir=history_root)
        temp_path = Path(temp_name)

    whole_hash = hashlib.sha256()
    whole_size = 0
    try:
        assembled_context = os.fdopen(temp_fd, "wb") if temp_fd is not None else None
        temp_fd = None
        try:
            for index, part in enumerate(bundle["parts"]):
                part_rel = archive_dir / PurePosixPath(part["path"])
                _safe_lstat_chain(root, part_rel, final_regular=True)
                part_fd = _open_nofollow(root, part_rel)
                part_hash = hashlib.sha256()
                part_size = 0
                with os.fdopen(part_fd, "rb") as source:
                    while chunk := source.read(CHUNK_SIZE):
                        part_hash.update(chunk)
                        whole_hash.update(chunk)
                        part_size += len(chunk)
                        whole_size += len(chunk)
                        if assembled_context is not None:
                            assembled_context.write(chunk)
                if part_size != part["bytes"] or part_hash.hexdigest() != part["sha256"]:
                    raise EvidenceError(f"bundle part {part['path']} failed its size or SHA-256 check")
            if assembled_context is not None:
                assembled_context.flush()
                os.fsync(assembled_context.fileno())
        finally:
            if assembled_context is not None:
                assembled_context.close()
        if whole_size != bundle["bytes"] or whole_hash.hexdigest() != bundle["sha256"]:
            raise EvidenceError("assembled bundle failed its size or SHA-256 check")
        if temp_path is not None:
            os.replace(temp_path, cached_bundle)
            digest, size = _sha256_file(cached_bundle)
            if digest != bundle["sha256"] or size != bundle["bytes"]:
                raise EvidenceError("cached bundle changed after installation")
        return cached_bundle, archive_repo
    finally:
        if temp_fd is not None:
            os.close(temp_fd)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def _expected_archive_refs(manifest: dict[str, Any]) -> dict[str, str]:
    refs = {manifest["original_ref"]: manifest["original_main"]}
    refs.update({f"refs/tags/{tag}": object_id for tag, object_id in manifest["preserved_tags"].items()})
    if len(refs) != len(manifest["preserved_tags"]) + 1:
        raise EvidenceError("a preserved tag collides with original_ref")
    return refs


def _bundle_refs(repo: Path, bundle_path: Path) -> dict[str, str]:
    output = _git(repo, ["bundle", "list-heads", str(bundle_path)]).stdout
    refs: dict[str, str] = {}
    for line in output.splitlines():
        try:
            object_id, ref = line.decode("ascii", "strict").split(" ", 1)
        except (UnicodeDecodeError, ValueError) as exc:
            raise EvidenceError("bundle has an invalid ref listing") from exc
        if not HEX40.fullmatch(object_id) or ref in refs:
            raise EvidenceError("bundle has an invalid or duplicate ref")
        refs[ref] = object_id
    return refs


def _archive_git(repo: Path, bundle_path: Path, archive_repo: Path, manifest: dict[str, Any]) -> Path:
    expected = _expected_archive_refs(manifest)
    actual = _bundle_refs(repo, bundle_path)
    if actual != expected:
        raise EvidenceError("bundle refs do not exactly match original_main and preserved_tags")

    if not archive_repo.exists() and not archive_repo.is_symlink():
        staging = archive_repo.parent / f"archive.git.tmp-{os.getpid()}-{next(tempfile._get_candidate_names())}"
        try:
            initialized = _git(repo, ["init", "--bare", "--template=/dev/null", "--object-format=sha1", str(staging)])
            if initialized.returncode != 0:
                raise EvidenceError("could not initialize the archive Git store")
            verify = _git(staging, ["bundle", "verify", str(bundle_path)], check=False)
            if verify.returncode != 0:
                details = verify.stderr.decode("utf-8", "replace").strip()
                raise EvidenceError(f"git bundle verify failed: {details or verify.returncode}")
            refspecs = [f"+{ref}:{ref}" for ref in expected]
            fetch = _git(staging, ["fetch", "--no-tags", "--no-write-fetch-head", str(bundle_path), *refspecs], check=False)
            if fetch.returncode != 0:
                details = fetch.stderr.decode("utf-8", "replace").strip()
                raise EvidenceError(f"could not import verified bundle: {details or fetch.returncode}")
            os.replace(staging, archive_repo)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
    elif archive_repo.is_symlink() or not archive_repo.is_dir():
        raise EvidenceError("cached archive Git store is not a real directory")

    _assert_object_store_has_no_symlinks(archive_repo / "objects")
    for required_directory in (Path("objects/info"), Path("objects/pack")):
        info = _safe_lstat_chain(archive_repo, required_directory, final_regular=False)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise EvidenceError(f"cached archive Git path must be a real directory: {required_directory}")
    alternate_file = archive_repo / "objects/info/alternates"
    if alternate_file.exists() or alternate_file.is_symlink():
        raise EvidenceError("cached archive Git store has object alternates")
    http_alternates = archive_repo / "objects/info/http-alternates"
    if http_alternates.exists() or http_alternates.is_symlink():
        raise EvidenceError("cached archive Git store has HTTP object alternates")
    bare = _git(archive_repo, ["rev-parse", "--is-bare-repository"]).stdout.strip()
    object_format = _git(archive_repo, ["rev-parse", "--show-object-format"]).stdout.strip()
    if bare != b"true" or object_format != b"sha1":
        raise EvidenceError("cached archive Git store is not a self-contained SHA-1 bare repository")
    config = _git(archive_repo, ["config", "--local", "--null", "--list"]).stdout.split(b"\x00")
    config_values: dict[bytes, bytes] = {}
    allowed_config = {
        b"core.repositoryformatversion",
        b"core.filemode",
        b"core.bare",
        b"core.logallrefupdates",
        b"core.ignorecase",
        b"core.precomposeunicode",
    }
    for entry in config:
        if not entry:
            continue
        try:
            key, value = entry.split(b"\n", 1)
        except ValueError as exc:
            raise EvidenceError("cached archive Git configuration is malformed") from exc
        key = key.lower()
        if key not in allowed_config or key in config_values:
            raise EvidenceError(f"unexpected cached archive Git configuration: {key.decode('ascii', 'replace')}")
        config_values[key] = value
    if config_values.get(b"core.repositoryformatversion") != b"0" or config_values.get(b"core.bare") != b"true":
        raise EvidenceError("cached archive Git configuration is not a plain bare repository")
    stored_refs_raw = _git(archive_repo, ["for-each-ref", "--format=%(refname) %(objectname)"]).stdout
    stored_refs: dict[str, str] = {}
    for line in stored_refs_raw.splitlines():
        try:
            ref, object_id = line.decode("ascii", "strict").split(" ", 1)
        except (UnicodeDecodeError, ValueError) as exc:
            raise EvidenceError("cached archive Git store has an invalid ref") from exc
        stored_refs[ref] = object_id
    if stored_refs != expected:
        raise EvidenceError("cached archive Git refs do not match the verified bundle")
    for object_id in expected.values():
        object_type = _git(archive_repo, ["cat-file", "-t", object_id]).stdout.strip()
        if object_type not in (b"commit", b"tag"):
            raise EvidenceError(f"archive ref {object_id} is neither a commit nor a tag object")
    integrity = _git(archive_repo, ["fsck", "--full", "--strict", "--no-reflogs", "--no-progress"], check=False)
    if integrity.returncode != 0:
        details = (integrity.stderr + integrity.stdout).decode("utf-8", "replace").strip()
        raise EvidenceError(f"cached archive Git store failed full fsck: {details or integrity.returncode}")
    verification = _git(archive_repo, ["bundle", "verify", str(bundle_path)], check=False)
    if verification.returncode != 0:
        details = verification.stderr.decode("utf-8", "replace").strip()
        raise EvidenceError(f"git bundle verify failed: {details or verification.returncode}")
    return archive_repo


def _load_archive(root: Path) -> tuple[Path, Path, dict[str, Any], Path, str]:
    root_path, manifest = _manifest_for(root)
    root_path, gitdir, head = _repo_root(root_path)
    bundle_path, archive_repo = _assemble_bundle(root_path, gitdir, manifest)
    archive_repo = _archive_git(root_path, bundle_path, archive_repo, manifest)
    return root_path, gitdir, manifest, archive_repo, head


def _tree_entries(repo: Path, revision: str) -> dict[bytes, tuple[bytes, bytes, bytes]]:
    raw = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", revision]).stdout
    entries: dict[bytes, tuple[bytes, bytes, bytes]] = {}
    for record in raw.split(b"\x00"):
        if not record:
            continue
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise EvidenceError(f"invalid Git tree entry in {revision}") from exc
        if path in entries:
            raise EvidenceError(f"duplicate Git tree path in {revision}")
        entries[path] = (mode, object_type, object_id)
    return entries


def _removed_bytes(manifest: dict[str, Any]) -> tuple[list[bytes], list[bytes]]:
    removed = manifest["removed_paths"]
    return (
        [prefix.encode("utf-8") for prefix in removed["prefixes"]],
        [path.encode("utf-8") for path in removed["files"]],
    )


def _check_filtered_tree(current_root: Path, archive_repo: Path, manifest: dict[str, Any], head: str) -> None:
    original = manifest["original_main"]
    base = manifest["rewritten_base"]
    original_entries = _tree_entries(archive_repo, original)
    base_entries = _tree_entries(current_root, base)
    prefixes, files = _removed_bytes(manifest)
    filtered: dict[bytes, tuple[bytes, bytes, bytes]] = {}
    matched = [False] * (len(prefixes) + len(files))
    for path, entry in original_entries.items():
        selected = False
        for index, prefix in enumerate(prefixes):
            if path.startswith(prefix):
                matched[index] = True
                selected = True
        for index, file_path in enumerate(files, start=len(prefixes)):
            if path == file_path:
                matched[index] = True
                selected = True
        if not selected:
            filtered[path] = entry
    if any(not item for item in matched):
        raise EvidenceError("a removed_paths entry does not match any original_main tree path")
    if filtered != base_entries:
        missing = len(filtered.keys() - base_entries.keys())
        added = len(base_entries.keys() - filtered.keys())
        changed = sum(1 for path in filtered.keys() & base_entries.keys() if filtered[path] != base_entries[path])
        raise EvidenceError(
            "rewritten_base tree differs from original_main after the declared removals "
            f"(missing={missing}, added={added}, changed={changed})"
        )

    head_entries = _tree_entries(current_root, head)
    frozen_paths = {b"reports/freeze.json"}
    frozen_paths.update(path for path in original_entries if path.startswith(b"results/"))
    current_frozen_paths = {path for path in head_entries if path == b"reports/freeze.json" or path.startswith(b"results/")}
    if b"reports/freeze.json" not in original_entries or b"reports/freeze.json" not in head_entries:
        raise EvidenceError("reports/freeze.json is absent from original_main or current HEAD")
    if frozen_paths != current_frozen_paths:
        raise EvidenceError("current reports/freeze.json and results/** paths differ from original_main")
    if any(original_entries[path] != head_entries[path] for path in frozen_paths):
        raise EvidenceError("current reports/freeze.json or results/** differs from original_main")


def _verify_current_tags(root: Path, manifest: dict[str, Any]) -> None:
    for tag, expected in manifest["preserved_tags"].items():
        ref = f"refs/tags/{tag}"
        result = _git(root, ["show-ref", "--verify", "--hash", ref], check=False)
        if result.returncode != 0 or result.stdout.decode("ascii", "replace").strip() != expected:
            raise EvidenceError(f"current tag {tag!r} does not match its preserved object ID")


def _verified_state(root: Path) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    root_path, _, manifest, archive_repo, head = _load_archive(Path(root))
    _verify_current_tags(root_path, manifest)
    ancestor = _git(root_path, ["merge-base", "--is-ancestor", manifest["rewritten_base"], head], check=False)
    if ancestor.returncode != 0:
        raise EvidenceError("rewritten_base is not an ancestor of current HEAD")
    _check_filtered_tree(root_path, archive_repo, manifest, head)
    result = {
        "verified": True,
        "original_main": manifest["original_main"],
        "rewritten_base": manifest["rewritten_base"],
        "head": head,
        "preserved_tags": len(manifest["preserved_tags"]),
        "removed_prefixes": len(manifest["removed_paths"]["prefixes"]),
        "removed_files": len(manifest["removed_paths"]["files"]),
        "bundle_sha256": manifest["bundle"]["sha256"],
    }
    return result, root_path, manifest, archive_repo


def verify(root: Path) -> dict[str, Any]:
    """Validate the archive, current tags, filtered base, and frozen reports."""
    result, _, _, _ = _verified_state(Path(root))
    return result


def prove_lineage(root: Path, revision: str, release: str) -> dict[str, Any]:
    """Prove that an original commit belongs to the preserved release history."""
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        raise EvidenceError("revision must be a full lowercase SHA-1 commit ID")
    if not isinstance(release, str) or not release:
        raise EvidenceError("release must be a preserved tag name")
    verification, _, manifest, archive_repo = _verified_state(Path(root))
    expected_tag = manifest["preserved_tags"].get(release)
    if expected_tag is None:
        raise EvidenceError(f"release tag {release!r} is not in preserved_tags")
    object_type = _git(archive_repo, ["cat-file", "-t", revision], check=False)
    if object_type.returncode != 0 or object_type.stdout.strip() != b"commit":
        raise EvidenceError("revision is not a commit in the recovered original history")
    for ancestor, descendant, label in (
        (revision, manifest["original_main"], "original_main"),
        (revision, f"refs/tags/{release}^{{commit}}", release),
    ):
        result = _git(archive_repo, ["merge-base", "--is-ancestor", ancestor, descendant], check=False)
        if result.returncode != 0:
            raise EvidenceError(f"revision is not an ancestor of preserved {label}")
    tag_id = _git(archive_repo, ["rev-parse", "--verify", f"refs/tags/{release}"]).stdout.decode("ascii", "strict").strip()
    if tag_id != expected_tag:
        raise EvidenceError(f"archive release tag {release!r} does not match preserved identity")
    return {
        "verified": True,
        "revision": revision,
        "release": release,
        "original_main": verification["original_main"],
        "rewritten_base": verification["rewritten_base"],
    }


def _selected_original_entries(archive_repo: Path, manifest: dict[str, Any]) -> list[tuple[bytes, bytes, bytes]]:
    entries = _tree_entries(archive_repo, manifest["original_main"])
    prefixes, files = _removed_bytes(manifest)
    selected: list[tuple[bytes, bytes, bytes]] = []
    matched = [False] * (len(prefixes) + len(files))
    for path, (mode, object_type, object_id) in entries.items():
        chosen = False
        for index, prefix in enumerate(prefixes):
            if path.startswith(prefix):
                matched[index] = True
                chosen = True
        for index, file_path in enumerate(files, start=len(prefixes)):
            if path == file_path:
                matched[index] = True
                chosen = True
        if chosen:
            if object_type != b"blob" or mode not in (b"100644", b"100755"):
                raise EvidenceError(f"refusing to hydrate non-regular Git entry at {os.fsdecode(path)!r}")
            try:
                decoded = os.fsdecode(path)
                if os.fsencode(decoded) != path:
                    raise EvidenceError("selected Git path cannot be represented by this filesystem")
                _safe_relative_path(decoded, "selected Git path")
            except (UnicodeError, EvidenceError) as exc:
                if isinstance(exc, EvidenceError):
                    raise
                raise EvidenceError("selected Git path cannot be represented by this filesystem") from exc
            selected.append((path, mode, object_id))
    if any(not item for item in matched):
        raise EvidenceError("a removed_paths entry does not match any original_main tree path")
    return sorted(selected, key=lambda item: item[0])


def _open_parent_directory(root: Path, relative: str, *, create: bool) -> tuple[int, str]:
    components = relative.split("/")
    parent_components = components[:-1]
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(root, flags)
    try:
        for component in parent_components:
            try:
                child = os.open(component, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    os.close(fd)
                    return -1, components[-1]
                try:
                    os.mkdir(component, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(component, flags, dir_fd=fd)
            except OSError as exc:
                raise EvidenceError(f"unsafe hydration parent path {relative!r}: {exc}") from exc
            os.close(fd)
            fd = child
        return fd, components[-1]
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


class _ArchiveBlobReader:
    """One persistent cat-file process for efficiently streaming many blobs."""

    def __init__(self, archive_repo: Path) -> None:
        git = shutil.which("git")
        if not git:
            raise EvidenceError("git executable was not found")
        command = [git, "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", str(archive_repo), "cat-file", "--batch"]
        self.errors = tempfile.TemporaryFile()
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.errors,
            env=_git_env(),
        )
        assert self.process.stdin is not None and self.process.stdout is not None
        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.closed = False

    @staticmethod
    def _write_all(fd: int, chunk: bytes) -> None:
        view = memoryview(chunk)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise EvidenceError("short write while hydrating archived evidence")
            view = view[written:]

    def stream(self, object_id: bytes, *, output_fd: int | None = None, compare_fd: int | None = None) -> int:
        if self.closed:
            raise EvidenceError("archive blob reader is already closed")
        if (output_fd is None) == (compare_fd is None):
            raise ValueError("provide exactly one hydration output or comparison file")
        try:
            request = object_id + b"\n"
            if self.stdin.write(request) != len(request):
                raise EvidenceError("short write while requesting archived blob")
            self.stdin.flush()
            header = self.stdout.readline()
        except (OSError, BrokenPipeError) as exc:
            raise EvidenceError(f"cannot request archived blob {object_id.decode('ascii', 'replace')}: {exc}") from exc
        try:
            returned_id, object_type, length_text = header.rstrip(b"\n").split(b" ", 2)
            length = int(length_text)
        except (ValueError, OverflowError) as exc:
            raise EvidenceError("archive Git store returned an invalid cat-file header") from exc
        if returned_id != object_id or object_type != b"blob" or length < 0:
            raise EvidenceError("archive Git store returned the wrong blob identity or type")
        sha1 = hashlib.sha1()
        sha1.update(b"blob " + str(length).encode("ascii") + b"\x00")
        remaining = length
        differs = False
        while remaining:
            chunk = self.stdout.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise EvidenceError("archive Git blob ended before its declared size")
            sha1.update(chunk)
            if output_fd is not None:
                self._write_all(output_fd, chunk)
            else:
                assert compare_fd is not None
                actual = os.read(compare_fd, len(chunk))
                if actual != chunk:
                    differs = True
            remaining -= len(chunk)
        if self.stdout.read(1) != b"\n":
            raise EvidenceError("archive Git blob framing is invalid")
        if compare_fd is not None and os.read(compare_fd, 1):
            differs = True
        if sha1.digest() != bytes.fromhex(object_id.decode("ascii")):
            raise EvidenceError("archive Git blob content does not match its object ID")
        if differs:
            raise EvidenceError("refusing to overwrite different bytes")
        return length

    def close(self, *, failed: bool = False) -> None:
        if self.closed:
            return
        self.closed = True
        if failed and self.process.poll() is None:
            self.process.kill()
        try:
            self.stdin.close()
        except OSError:
            pass
        try:
            extra = self.stdout.read()
        except OSError:
            extra = b""
        self.stdout.close()
        status = self.process.wait()
        if not failed and status != 0:
            self.errors.seek(0)
            details = self.errors.read().decode("utf-8", "replace").strip()
            self.errors.close()
            raise EvidenceError(f"could not read archive blobs: {details or status}")
        self.errors.close()
        if not failed and extra:
            raise EvidenceError("archive Git store returned unexpected trailing cat-file output")

    def __enter__(self) -> "_ArchiveBlobReader":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close(failed=exc_type is not None)


def _hydrate_one(root: Path, relative: str, mode: bytes, object_id: bytes, reader: _ArchiveBlobReader) -> tuple[bool, int]:
    parent_fd, basename = _open_parent_directory(root, relative, create=True)
    if parent_fd < 0:
        raise EvidenceError("could not open hydration parent directory")
    existing_fd: int | None = None
    target_fd: int | None = None
    created = False
    try:
        try:
            existing_info = os.stat(basename, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            try:
                target_fd = os.open(
                    basename,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
                created = True
            except FileExistsError:
                # Re-enter through fresh no-follow directory handles after a
                # concurrent creator wins the exclusive-create race.
                return _hydrate_one(root, relative, mode, object_id, reader)
        else:
            if not stat.S_ISREG(existing_info.st_mode):
                raise EvidenceError(f"refusing to overwrite non-regular path {relative!r}")
            try:
                existing_fd = os.open(
                    basename,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise EvidenceError(f"refusing unsafe existing hydration path {relative!r}: {exc}") from exc
            opened_info = os.fstat(existing_fd)
            if not stat.S_ISREG(opened_info.st_mode) or (opened_info.st_dev, opened_info.st_ino) != (
                existing_info.st_dev,
                existing_info.st_ino,
            ):
                raise EvidenceError(f"existing hydration path changed while opening: {relative!r}")

        if existing_fd is not None:
            size = reader.stream(object_id, compare_fd=existing_fd)
            return False, size

        assert target_fd is not None
        size = reader.stream(object_id, output_fd=target_fd)
        os.fchmod(target_fd, 0o755 if mode == b"100755" else 0o644)
        os.fsync(target_fd)
        return True, size
    except BaseException:
        if created:
            try:
                os.unlink(basename, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    finally:
        if existing_fd is not None:
            os.close(existing_fd)
        if target_fd is not None:
            os.close(target_fd)
        os.close(parent_fd)


def hydrate(root: Path) -> dict[str, Any]:
    """Restore only removed regular files, preserving archived blob bytes."""
    result, root_path, manifest, archive_repo = _verified_state(Path(root))
    selected = _selected_original_entries(archive_repo, manifest)
    restored = 0
    already_present = 0
    restored_bytes = 0
    already_present_bytes = 0
    with _ArchiveBlobReader(archive_repo) as reader:
        for path, mode, object_id in selected:
            relative = os.fsdecode(path)
            try:
                created, size = _hydrate_one(root_path, relative, mode, object_id, reader)
            except EvidenceError as exc:
                if str(exc) == "refusing to overwrite different bytes":
                    raise EvidenceError(f"refusing to overwrite different bytes at {relative!r}") from exc
                raise
            if created:
                restored += 1
                restored_bytes += size
            else:
                already_present += 1
                already_present_bytes += size
    return {
        "verified": True,
        "restored_files": restored,
        "already_present_files": already_present,
        "restored_bytes": restored_bytes,
        "already_present_bytes": already_present_bytes,
        "bundle_sha256": result["bundle_sha256"],
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify", help="verify the archive and filtered history")
    verify_parser.add_argument("--root", type=Path, required=True)
    prove_parser = subparsers.add_parser("prove", help="prove an original commit belongs to a preserved release")
    prove_parser.add_argument("--root", type=Path, required=True)
    prove_parser.add_argument("--revision", required=True)
    prove_parser.add_argument("--release", required=True)
    hydrate_parser = subparsers.add_parser("hydrate", help="restore only the manifest-selected removed paths")
    hydrate_parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify(args.root)
        elif args.command == "prove":
            result = prove_lineage(args.root, args.revision, args.release)
        else:
            result = hydrate(args.root)
    except (EvidenceError, OSError, subprocess.SubprocessError) as exc:
        print(f"historical-evidence: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
