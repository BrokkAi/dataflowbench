#!/usr/bin/env python3
"""Verify and expose the pre-rebase v0.9.2 source history.

This is a deliberately narrow, read-only provenance helper.  The source bundle
is imported into a private bare cache, and original objects can optionally be
copied into the current repository without creating refs or changing its
checkout.  A separate sparse checkout at the original source commit is used
when historical source-snapshot checks need to run.

The descriptor and source identities below are production pins.  Tests replace
them only with ``unittest.mock.patch`` while building disposable repositories.
There is no command-line switch for changing production trust roots.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


MANIFEST_RELATIVE = Path(
    "reports/releases/v0.9.2/source-history/pre-main-rebase-01/manifest.json"
)
SCHEMA_VERSION = "v092-original-source-history/v1"

# Immutable source-lineage pins for this one archive.
PINNED_ORIGINAL_MAIN = "7fd8c3252a5ed0e03ec7bbc2d96ad0306613c64b"
PINNED_ORIGINAL_SOURCE = "2991bfb897cad98674efc2feb04388174295e885"
PINNED_ORIGINAL_CORE_SOURCE = "328bebab4a60ff10c5a79cd723d44516be2da5fc"
PINNED_PR295_REBASED = PINNED_ORIGINAL_SOURCE
PINNED_PRE_REBASE_MAIN = "0801eb591dda8a1e054931250b2934e0cbb763fd"
PINNED_REBASED_FEATURE_HEAD = "9c542306635e0a7eb24b3898280e267a85234f12"
PINNED_NEW_MAIN_BASE = "bff6e6ac2c6ab27f8370d81fa38ac9ba6cfe15d8"
PINNED_ORIGINAL_MAIN_ARCHIVE = PINNED_ORIGINAL_MAIN
PINNED_SOURCE_BUNDLE_SHA256 = "cfa74a597e9789655f0241f10c926989b6537620b7c35262a2baed385aa78eaa"
PINNED_SOURCE_BUNDLE_BYTES = 42_851_680
PINNED_MAIN_ARCHIVE_BUNDLE_SHA256 = "fe5e022a10d85c8b0b9497f677c82766a9b7ffbbe8c3fcf246d65a69e1c53c2d"
PINNED_HISTORICAL_HELPER_SHA256 = "fae3e4e0086700dca4b061d95e1c3c00fc617ca3c7049be8afd6a91514cb5a18"
PINNED_SOURCE_REFS = {
    "refs/heads/dave/v092-before-main-history-rebase-20261026": PINNED_PRE_REBASE_MAIN,
    "refs/heads/dave/v092-before-pr295-rebase-20261026": PINNED_PR295_REBASED,
}
PINNED_PREREQUISITES = (
    "7fd8c3252a5ed0e03ec7bbc2d96ad0306613c64b",
    "6f01ef26221ad53884941b95e6173102a1bbc6e5",
)
MAIN_ARCHIVE_MANIFEST = Path("evidence-archives/main-before-20261026/manifest.json")

PART_LIMIT = 40 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

SOURCE_DIRECTORIES = (
    "src",
    "cases",
    "populations",
    "adapters",
    "schemas",
    "scripts",
    "corpus",
)
SOURCE_FILES = (
    "Cargo.toml",
    "Cargo.lock",
    "reports/releases/v0.9.0/plan.json",
    "docs/v0.9.2-execution.md",
    "README.md",
    "LICENSE",
    "docs/adapters.md",
    "docs/benchmark-sources.md",
    "docs/challenge-tier.md",
    "docs/real-project-preregistration.md",
    "docs/real-project-r2-preregistration.md",
    "docs/real-project-review.md",
)


class SourceHistoryError(RuntimeError):
    """A source archive, cache, or historical source view failed closed."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceHistoryError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise SourceHistoryError(f"{label} must contain exactly: {', '.join(sorted(keys))}")
    return value


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SourceHistoryError(f"{label} must be a safe repository-relative path")
    if value.startswith(("/", "~")):
        raise SourceHistoryError(f"{label} must be repository-relative")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise SourceHistoryError(f"{label} contains an unsafe path component")
    if any(any(ord(ch) < 0x20 for ch in part) for part in parts):
        raise SourceHistoryError(f"{label} contains a control character")
    return value


def _ensure_directory(path: Path) -> None:
    """Create a directory chain while refusing symlinked/non-directory parts."""
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            try:
                os.mkdir(current, 0o700)
            except FileExistsError:
                pass
            info = os.lstat(current)
        except OSError as exc:
            raise SourceHistoryError(f"cannot inspect cache directory {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise SourceHistoryError(f"cache path component is not a real directory: {current}")


def _lstat_chain(base: Path, relative: Path, *, regular: bool | None = None) -> os.stat_result:
    current = base
    parts = relative.parts
    if not parts:
        raise SourceHistoryError("empty path")
    for index, part in enumerate(parts):
        current /= part
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise SourceHistoryError(f"cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise SourceHistoryError(f"symlink is not allowed in path: {current}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise SourceHistoryError(f"non-directory path component: {current}")
    if regular is True and not stat.S_ISREG(info.st_mode):
        raise SourceHistoryError(f"expected a regular file: {current}")
    if regular is False and not stat.S_ISDIR(info.st_mode):
        raise SourceHistoryError(f"expected a directory: {current}")
    return info


def _optional_lstat_chain(base: Path, relative: Path) -> os.stat_result | None:
    current = base
    parts = relative.parts
    if not parts:
        raise SourceHistoryError("empty path")
    for index, part in enumerate(parts):
        current /= part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise SourceHistoryError(f"cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise SourceHistoryError(f"symlink is not allowed in path: {current}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise SourceHistoryError(f"non-directory path component: {current}")
    return info


def _open_nofollow(base: Path, relative: Path) -> int:
    info = _lstat_chain(base, relative, regular=True)
    fd = os.open(base / relative, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        raise SourceHistoryError(f"file changed while being opened: {base / relative}")
    return fd


def _sha256_file(path: Path) -> tuple[str, int]:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise SourceHistoryError(f"expected a regular file: {path}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        raise SourceHistoryError(f"file changed while being hashed: {path}")
    digest = hashlib.sha256()
    size = 0
    with os.fdopen(fd, "rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_CONFIG_") or key in {
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_PREFIX",
            "GIT_CEILING_DIRECTORIES", "GIT_TRACE", "GIT_TRACE_SETUP",
            "GIT_TRACE_PACKET", "GIT_TRACE_PERFORMANCE", "GIT_GRAFT_FILE",
            "GIT_SHALLOW_FILE",
        }:
            env.pop(key, None)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(root: Path, args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    executable = shutil.which("git")
    if not executable:
        raise SourceHistoryError("git executable was not found")
    command = [
        executable,
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.fsmonitor=false",
        "-c", "core.commitGraph=false",
        "-c", "fetch.recurseSubmodules=false",
        "-C", str(root),
        *args,
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_git_env())
    if check and result.returncode != 0:
        error = result.stderr.decode("utf-8", "replace").strip()
        raise SourceHistoryError(f"git {' '.join(args)} failed: {error or result.returncode}")
    return result


def _read_json_nofollow(root: Path, relative: Path, *, maximum: int = 1024 * 1024) -> dict[str, Any]:
    _lstat_chain(root, relative, regular=True)
    fd = _open_nofollow(root, relative)
    try:
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(maximum + 1)
    except OSError as exc:
        raise SourceHistoryError(f"cannot read {relative}: {exc}") from exc
    if len(raw) > maximum:
        raise SourceHistoryError(f"{relative} exceeds {maximum} bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceHistoryError(f"{relative} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceHistoryError(f"{relative} must contain a JSON object")
    return value


def _validate_manifest(value: Any) -> dict[str, Any]:
    manifest = _exact_object(
        value,
        {
            "schema_version", "original_main", "original_core_source",
            "rebased_feature_head", "new_main_base", "original_source_refs",
            "main_archive", "bundle",
        },
        "source-history manifest",
    )
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise SourceHistoryError("unsupported source-history schema_version")
    pins = {
        "original_main": PINNED_ORIGINAL_MAIN,
        "original_core_source": PINNED_ORIGINAL_CORE_SOURCE,
        "rebased_feature_head": PINNED_REBASED_FEATURE_HEAD,
        "new_main_base": PINNED_NEW_MAIN_BASE,
    }
    for field, expected in pins.items():
        actual = manifest[field]
        if not isinstance(actual, str) or not HEX40.fullmatch(actual) or actual != expected:
            raise SourceHistoryError(f"manifest {field} does not match the pinned source identity")

    refs = manifest["original_source_refs"]
    if not isinstance(refs, dict) or refs != PINNED_SOURCE_REFS:
        raise SourceHistoryError("manifest original_source_refs do not exactly match the pinned source refs")
    for ref, object_id in refs.items():
        if not ref.startswith("refs/heads/") or not HEX40.fullmatch(object_id):
            raise SourceHistoryError("manifest source_refs contains an invalid ref or object ID")
    if refs.get("refs/heads/dave/v092-before-pr295-rebase-20261026") != PINNED_ORIGINAL_SOURCE:
        raise SourceHistoryError("PR295 source ref does not match the pinned original source commit")
    if refs.get("refs/heads/dave/v092-before-main-history-rebase-20261026") != PINNED_PRE_REBASE_MAIN:
        raise SourceHistoryError("pre-rebase main ref does not match its pinned source commit")

    main_archive = _exact_object(
        manifest["main_archive"], {"manifest_path", "bundle_sha256", "original_main"}, "main_archive"
    )
    if main_archive["manifest_path"] != MAIN_ARCHIVE_MANIFEST.as_posix():
        raise SourceHistoryError("main_archive manifest_path is not the pinned archive descriptor")
    if main_archive["bundle_sha256"] != PINNED_MAIN_ARCHIVE_BUNDLE_SHA256:
        raise SourceHistoryError("main_archive does not bind the pinned main bundle")
    if main_archive["original_main"] != PINNED_ORIGINAL_MAIN_ARCHIVE:
        raise SourceHistoryError("main_archive original_main does not match its pinned commit")

    bundle = _exact_object(manifest["bundle"], {"sha256", "bytes", "parts"}, "bundle")
    if bundle["sha256"] != PINNED_SOURCE_BUNDLE_SHA256:
        raise SourceHistoryError("bundle SHA-256 does not match the pinned source archive")
    if type(bundle["bytes"]) is not int or bundle["bytes"] != PINNED_SOURCE_BUNDLE_BYTES:
        raise SourceHistoryError("bundle byte count does not match the pinned source archive")
    if not isinstance(bundle["parts"], list) or not bundle["parts"]:
        raise SourceHistoryError("bundle.parts must be a non-empty array")
    expected_count = (PINNED_SOURCE_BUNDLE_BYTES + PART_LIMIT - 1) // PART_LIMIT
    if len(bundle["parts"]) != expected_count:
        raise SourceHistoryError("bundle.parts does not have the pinned archive's expected part count")
    part_names: set[str] = set()
    total = 0
    for index, part_value in enumerate(bundle["parts"]):
        part = _exact_object(part_value, {"path", "sha256", "bytes"}, f"bundle.parts[{index}]")
        expected_name = f"original-source.bundle.part{index:04d}"
        path = _safe_relative(part["path"], f"bundle.parts[{index}].path")
        if path != expected_name:
            raise SourceHistoryError(f"bundle.parts[{index}].path must be {expected_name}")
        if path in part_names:
            raise SourceHistoryError("bundle part paths must be unique")
        part_names.add(path)
        if not isinstance(part["sha256"], str) or not HEX64.fullmatch(part["sha256"]):
            raise SourceHistoryError(f"bundle.parts[{index}].sha256 must be a lowercase SHA-256 digest")
        if type(part["bytes"]) is not int or not (0 < part["bytes"] <= PART_LIMIT):
            raise SourceHistoryError(f"bundle.parts[{index}].bytes must be between 1 and {PART_LIMIT}")
        if index < len(bundle["parts"]) - 1 and part["bytes"] != PART_LIMIT:
            raise SourceHistoryError("all non-final bundle parts must be exactly 40 MiB")
        total += part["bytes"]
    if total != bundle["bytes"]:
        raise SourceHistoryError("bundle part byte counts do not add up to bundle.bytes")
    return manifest


def _root_and_gitdir(root: Path) -> tuple[Path, Path, str]:
    try:
        root = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise SourceHistoryError(f"repository root does not exist: {root}: {exc}") from exc
    if not root.is_dir():
        raise SourceHistoryError(f"repository root is not a directory: {root}")
    top = _git(root, ["rev-parse", "--show-toplevel"]).stdout.decode("utf-8", "strict").strip()
    top_path = Path(top).resolve(strict=True)
    if top_path != root:
        raise SourceHistoryError(f"root must be the worktree root (found {top_path})")
    gitdir = Path(_git(root, ["rev-parse", "--absolute-git-dir"]).stdout.decode("utf-8", "strict").strip())
    _assert_real_directory_path(gitdir, "current Git directory")
    gitdir = gitdir.resolve(strict=True)
    _assert_current_graph_metadata_safe(root, gitdir=gitdir)
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.decode("ascii", "strict").strip()
    if not HEX40.fullmatch(head):
        raise SourceHistoryError("current HEAD is not a full SHA-1 commit")
    return root, gitdir, head


def _historical_commit_pins() -> tuple[str, ...]:
    values = [
        PINNED_ORIGINAL_MAIN_ARCHIVE,
        PINNED_ORIGINAL_CORE_SOURCE,
        *PINNED_SOURCE_REFS.values(),
        *PINNED_PREREQUISITES,
    ]
    return tuple(dict.fromkeys(values))


def _assert_no_historical_ancestor(root: Path, head: str, *, require_present: bool) -> None:
    for object_id in _historical_commit_pins():
        object_type = _git(root, ["cat-file", "-t", object_id], check=False)
        if object_type.returncode != 0:
            if require_present:
                raise SourceHistoryError(f"historical source commit is absent after import: {object_id}")
            continue
        if object_type.stdout.strip() != b"commit":
            raise SourceHistoryError(f"historical source pin is not a commit: {object_id}")
        ancestry = _git(root, ["merge-base", "--is-ancestor", object_id, head], check=False)
        if ancestry.returncode == 0:
            raise SourceHistoryError(f"historical source commit is an ancestor of current HEAD: {object_id}")
        if ancestry.returncode != 1:
            raise SourceHistoryError(f"cannot establish the no-old-history ancestry boundary for {object_id}")


def _descriptor(root: Path, manifest_ref: str | Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(manifest_ref)
    if manifest_path.is_absolute() or manifest_path != MANIFEST_RELATIVE:
        raise SourceHistoryError("manifest_ref must name the pinned source-history descriptor")
    value = _read_json_nofollow(root, MANIFEST_RELATIVE)
    return root / MANIFEST_RELATIVE, _validate_manifest(value)


def _bundle_paths(root: Path, manifest: Mapping[str, Any]) -> list[tuple[Path, dict[str, Any]]]:
    directory = MANIFEST_RELATIVE.parent
    result: list[tuple[Path, dict[str, Any]]] = []
    for part in manifest["bundle"]["parts"]:
        relative = directory / part["path"]
        _lstat_chain(root, relative, regular=True)
        result.append((root / relative, part))
    return result


def _cache_paths(gitdir: Path, bundle_sha: str) -> tuple[Path, Path, Path, Path]:
    cache_root = gitdir / "original-source-history" / bundle_sha
    _ensure_directory(cache_root)
    return (
        cache_root,
        cache_root / "original-source.bundle",
        cache_root / "source.git",
        cache_root / "view",
    )


def _assemble_bundle(root: Path, gitdir: Path, manifest: Mapping[str, Any]) -> tuple[Path, Path]:
    cache_root, cached_bundle, source_repo, _ = _cache_paths(gitdir, manifest["bundle"]["sha256"])
    parts = _bundle_paths(root, manifest)
    whole_digest = hashlib.sha256()
    whole_size = 0
    temp: Path | None = None
    output = None
    try:
        cached_exists = cached_bundle.exists() or cached_bundle.is_symlink()
        if cached_exists:
            _lstat_chain(cache_root, Path(cached_bundle.name), regular=True)
        else:
            fd, name = tempfile.mkstemp(prefix="source-bundle-", suffix=".tmp", dir=cache_root)
            temp = Path(name)
            output = os.fdopen(fd, "wb")
        for path, part in parts:
            part_hash = hashlib.sha256()
            part_size = 0
            fd = _open_nofollow(root, path.relative_to(root))
            with os.fdopen(fd, "rb") as stream:
                while chunk := stream.read(CHUNK_SIZE):
                    if output is not None:
                        output.write(chunk)
                    part_hash.update(chunk)
                    whole_digest.update(chunk)
                    part_size += len(chunk)
                    whole_size += len(chunk)
            if part_size != part["bytes"] or part_hash.hexdigest() != part["sha256"]:
                raise SourceHistoryError(f"bundle part {path.name} failed its size or SHA-256 check")
        if output is not None:
            output.flush()
            os.fsync(output.fileno())
            output.close()
            output = None
        if whole_size != manifest["bundle"]["bytes"] or whole_digest.hexdigest() != manifest["bundle"]["sha256"]:
            raise SourceHistoryError("assembled source bundle failed its size or SHA-256 check")
        if cached_exists:
            digest, size = _sha256_file(cached_bundle)
            if digest != manifest["bundle"]["sha256"] or size != manifest["bundle"]["bytes"]:
                raise SourceHistoryError("cached source bundle does not match the pinned hash")
        else:
            os.replace(temp, cached_bundle)
            temp = None
            digest, size = _sha256_file(cached_bundle)
            if digest != manifest["bundle"]["sha256"] or size != manifest["bundle"]["bytes"]:
                raise SourceHistoryError("cached source bundle changed after installation")
        return cached_bundle, source_repo
    finally:
        if output is not None:
            output.close()
        if temp is not None:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass


def _load_pinned_historical_helper(root: Path):
    helper_relative = Path("scripts/historical_evidence.py")
    helper_path = root / helper_relative
    _lstat_chain(root, helper_relative, regular=True)
    digest, _ = _sha256_file(helper_path)
    if digest != PINNED_HISTORICAL_HELPER_SHA256:
        raise SourceHistoryError("scripts/historical_evidence.py is not the pinned main-archive verifier")
    spec = importlib.util.spec_from_file_location("_v092_pinned_historical_evidence", helper_path)
    if spec is None or spec.loader is None:
        raise SourceHistoryError("cannot load the pinned main-archive verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verified_main_archive(root: Path) -> tuple[Path, dict[str, Any]]:
    helper = _load_pinned_historical_helper(root)
    try:
        checked_root, _gitdir, archive_manifest, archive_repo, _current_head = helper._load_archive(root)
        helper._verify_current_tags(checked_root, archive_manifest)
        helper._check_filtered_tree(
            checked_root, archive_repo, archive_manifest, archive_manifest["rewritten_base"]
        )
    except Exception as exc:
        raise SourceHistoryError(f"the pinned main historical archive did not verify: {exc}") from exc
    if checked_root != root:
        raise SourceHistoryError("main archive verifier returned a different repository root")
    if archive_manifest.get("original_main") != PINNED_ORIGINAL_MAIN_ARCHIVE:
        raise SourceHistoryError("main archive original_main does not match the required prerequisite")
    if archive_manifest.get("rewritten_base") != helper.PINNED_REWRITTEN_BASE:
        raise SourceHistoryError("main archive rewritten_base does not match the pinned legacy base")
    if archive_manifest.get("bundle", {}).get("sha256") != PINNED_MAIN_ARCHIVE_BUNDLE_SHA256:
        raise SourceHistoryError("main archive bundle does not match the pinned prerequisite bundle")
    return archive_repo, {
        "manifest_path": MAIN_ARCHIVE_MANIFEST.as_posix(),
        "bundle_sha256": PINNED_MAIN_ARCHIVE_BUNDLE_SHA256,
        "original_main": PINNED_ORIGINAL_MAIN_ARCHIVE,
    }


def _read_refs(repo: Path) -> dict[str, str]:
    raw = _git(repo, ["for-each-ref", "--format=%(refname) %(objectname)"]).stdout
    result: dict[str, str] = {}
    for line in raw.splitlines():
        try:
            ref, object_id = line.decode("ascii", "strict").split(" ", 1)
        except (UnicodeDecodeError, ValueError) as exc:
            raise SourceHistoryError("Git store contains an invalid ref listing") from exc
        if ref in result or not HEX40.fullmatch(object_id):
            raise SourceHistoryError("Git store contains duplicate or invalid refs")
        result[ref] = object_id
    return result


def _bundle_refs(repo: Path, bundle: Path) -> dict[str, str]:
    raw = _git(repo, ["bundle", "list-heads", str(bundle)]).stdout
    result: dict[str, str] = {}
    for line in raw.splitlines():
        try:
            object_id, ref = line.decode("ascii", "strict").split(" ", 1)
        except (UnicodeDecodeError, ValueError) as exc:
            raise SourceHistoryError("source bundle has an invalid ref listing") from exc
        if not HEX40.fullmatch(object_id) or ref in result:
            raise SourceHistoryError("source bundle has duplicate or invalid refs")
        result[ref] = object_id
    return result


def _bundle_required_objects(repo: Path, bundle: Path) -> tuple[int, set[str]]:
    result = _git(repo, ["bundle", "verify", str(bundle)], check=False)
    output = (result.stdout + result.stderr).decode("utf-8", "replace")
    if result.returncode != 0:
        raise SourceHistoryError(f"git bundle verify failed: {output.strip() or result.returncode}")
    match = re.search(r"The bundle requires these (\d+) refs?:\s*(.*?)(?:\nThe bundle uses|\Z)", output, re.S)
    if match is None:
        if "The bundle does not require any existing ref" in output:
            return 0, set()
        return 0, set()
    count = int(match.group(1))
    object_ids = {
        line.strip().split(" ", 1)[0]
        for line in match.group(2).splitlines()
        if line.strip()
    }
    if len(object_ids) != count or any(not HEX40.fullmatch(object_id) for object_id in object_ids):
        raise SourceHistoryError("source bundle has an invalid prerequisite listing")
    return count, object_ids


def _assert_no_symlink_entries(root: Path) -> None:
    info = os.lstat(root)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise SourceHistoryError(f"cached Git directory is not a real directory: {root}")
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode):
                        raise SourceHistoryError(f"symlink in cached Git directory: {entry.path}")
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(Path(entry.path))
                    elif not stat.S_ISREG(info.st_mode):
                        raise SourceHistoryError(f"non-regular entry in cached Git directory: {entry.path}")
        except OSError as exc:
            raise SourceHistoryError(f"cannot inspect cached Git directory: {exc}") from exc


def _assert_no_alternates(repo: Path) -> None:
    for relative in (
        Path("objects/info/alternates"),
        Path("objects/info/http-alternates"),
        Path("objects/info/grafts"),
        Path("info/grafts"),
        Path("shallow"),
    ):
        if _optional_lstat_chain(repo, relative) is not None:
            raise SourceHistoryError(f"Git store uses forbidden external or history overrides: {relative}")


def _check_config(repo: Path, *, bare: bool) -> None:
    config = repo / "config"
    _lstat_chain(repo, Path("config"), regular=True)
    executable = shutil.which("git")
    if not executable:
        raise SourceHistoryError("git executable was not found")
    result = subprocess.run(
        [executable, "config", "--no-includes", "--file", str(config), "--null", "--list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_env(),
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SourceHistoryError(f"cannot safely read Git cache config: {detail or result.returncode}")
    raw = result.stdout.split(b"\x00")
    values: dict[bytes, bytes] = {}
    allowed = {
        b"core.repositoryformatversion", b"core.filemode", b"core.bare",
        b"core.logallrefupdates", b"core.ignorecase", b"core.precomposeunicode",
    }
    if not bare:
        allowed.add(b"core.sparsecheckout")
    for item in raw:
        if not item:
            continue
        try:
            key, value = item.split(b"\n", 1)
        except ValueError as exc:
            raise SourceHistoryError("Git cache config is malformed") from exc
        key = key.lower()
        if key not in allowed or key in values:
            raise SourceHistoryError(f"unexpected Git cache config key: {key.decode('ascii', 'replace')}")
        values[key] = value
    if values.get(b"core.repositoryformatversion") != b"0":
        raise SourceHistoryError("Git cache is not a plain repository")
    if values.get(b"core.bare") != (b"true" if bare else b"false"):
        raise SourceHistoryError("Git cache bare setting is wrong")
    if not bare and values.get(b"core.sparsecheckout") != b"true":
        raise SourceHistoryError("historical source view is not sparse-checkout enabled")


def _assert_bare_cache(repo: Path, expected_refs: Mapping[str, str]) -> None:
    _assert_no_symlink_entries(repo / "objects")
    _assert_no_alternates(repo)
    _lstat_chain(repo, Path("HEAD"), regular=True)
    for relative in (Path("objects/info"), Path("objects/pack"), Path("refs")):
        _lstat_chain(repo, relative, regular=False)
    _assert_no_symlink_entries(repo / "refs")
    if _git(repo, ["rev-parse", "--is-bare-repository"]).stdout.strip() != b"true":
        raise SourceHistoryError("source object cache is not bare")
    if _git(repo, ["rev-parse", "--show-object-format"]).stdout.strip() != b"sha1":
        raise SourceHistoryError("source object cache is not SHA-1")
    _check_config(repo, bare=True)
    if _read_refs(repo) != dict(expected_refs):
        raise SourceHistoryError("source object cache refs do not match the pinned source refs")
    for object_id in expected_refs.values():
        if _git(repo, ["cat-file", "-t", object_id]).stdout.strip() != b"commit":
            raise SourceHistoryError(f"source ref target is not a commit: {object_id}")
    for object_id in (PINNED_ORIGINAL_MAIN, PINNED_ORIGINAL_SOURCE, PINNED_ORIGINAL_CORE_SOURCE):
        if _git(repo, ["cat-file", "-t", object_id], check=False).stdout.strip() != b"commit":
            raise SourceHistoryError(f"required source commit is absent from source cache: {object_id}")
    if _git(repo, ["merge-base", "--is-ancestor", PINNED_ORIGINAL_CORE_SOURCE, PINNED_ORIGINAL_SOURCE], check=False).returncode:
        raise SourceHistoryError("original core source is not an ancestor of original source")
    integrity = _git(repo, ["fsck", "--full", "--strict", "--no-reflogs", "--no-progress"], check=False)
    if integrity.returncode:
        detail = (integrity.stderr + integrity.stdout).decode("utf-8", "replace").strip()
        raise SourceHistoryError(f"source object cache failed full fsck: {detail or integrity.returncode}")


def _build_source_cache(
    root: Path,
    archive_repo: Path,
    bundle: Path,
    source_repo: Path,
    manifest: Mapping[str, Any],
) -> None:
    refs = manifest["original_source_refs"]
    actual_refs = _bundle_refs(root, bundle)
    if actual_refs != dict(refs):
        raise SourceHistoryError("source bundle refs do not exactly match the pinned source refs")

    if source_repo.exists() or source_repo.is_symlink():
        if source_repo.is_symlink() or not source_repo.is_dir():
            raise SourceHistoryError("source cache path is not a real directory")
        _assert_bare_cache(source_repo, refs)
        count, required = _bundle_required_objects(source_repo, bundle)
        if count != len(PINNED_PREREQUISITES) or required != set(PINNED_PREREQUISITES):
            raise SourceHistoryError("source bundle prerequisite refs do not match the pinned main-history objects")
        return

    parent = source_repo.parent
    stage = parent / f"source.git.tmp-{os.getpid()}-{next(tempfile._get_candidate_names())}"
    try:
        _git(parent, ["init", "--bare", "--template=/dev/null", "--object-format=sha1", str(stage)])
        # Import the prerequisite chain only from the separately verified main archive.
        prerequisite_ref = "refs/remotes/origin/main"
        _git(stage, ["fetch", "--keep", "--no-tags", "--no-write-fetch-head", str(archive_repo), prerequisite_ref])
        for object_id in PINNED_PREREQUISITES:
            if _git(stage, ["cat-file", "-t", object_id], check=False).stdout.strip() != b"commit":
                raise SourceHistoryError(f"verified main archive lacks bundle prerequisite {object_id}")
        count, required = _bundle_required_objects(stage, bundle)
        if count != len(PINNED_PREREQUISITES) or required != set(PINNED_PREREQUISITES):
            raise SourceHistoryError("source bundle prerequisite refs do not match the pinned main-history objects")
        verify = _git(stage, ["bundle", "verify", str(bundle)], check=False)
        if verify.returncode:
            detail = (verify.stderr + verify.stdout).decode("utf-8", "replace").strip()
            raise SourceHistoryError(f"source bundle verify failed after importing main prerequisites: {detail}")
        refspecs = [f"+{ref}:{ref}" for ref in refs]
        _git(stage, ["fetch", "--keep", "--no-tags", "--no-write-fetch-head", str(bundle), *refspecs])
        _assert_bare_cache(stage, refs)
        os.replace(stage, source_repo)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    _assert_bare_cache(source_repo, refs)


def _load_verified(root: Path, manifest_ref: str | Path) -> tuple[Path, Path, Path, dict[str, Any], str, dict[str, Any]]:
    root, gitdir, head = _root_and_gitdir(root)
    _assert_current_store_has_no_alternates(root)
    for ancestor in (PINNED_NEW_MAIN_BASE, PINNED_REBASED_FEATURE_HEAD):
        result = _git(root, ["merge-base", "--is-ancestor", ancestor, head], check=False)
        if result.returncode != 0:
            raise SourceHistoryError(f"current HEAD does not descend from pinned rebased source {ancestor}")
    _assert_no_historical_ancestor(root, head, require_present=False)
    _, manifest = _descriptor(root, manifest_ref)
    archive_repo, main_archive = _verified_main_archive(root)
    if main_archive != manifest["main_archive"]:
        raise SourceHistoryError("source manifest main_archive binding does not match the verified archive")
    bundle, source_repo = _assemble_bundle(root, gitdir, manifest)
    if _bundle_refs(root, bundle) != manifest["original_source_refs"]:
        raise SourceHistoryError("source bundle refs do not exactly match the descriptor")
    _build_source_cache(root, archive_repo, bundle, source_repo, manifest)
    return root, gitdir, bundle, manifest, head, {"archive_repo": archive_repo, "source_repo": source_repo}


def _head_ref_state(root: Path) -> tuple[str, str, dict[str, str], tuple[str, int] | None, dict[str, str]]:
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.decode("ascii", "strict").strip()
    symbolic = _git(root, ["symbolic-ref", "-q", "HEAD"], check=False)
    symbolic_head = symbolic.stdout.decode("ascii", "replace").strip() if symbolic.returncode == 0 else ""
    gitdir = Path(_git(root, ["rev-parse", "--absolute-git-dir"]).stdout.decode("utf-8", "strict").strip()).resolve(strict=True)
    fetch_head = gitdir / "FETCH_HEAD"
    try:
        fetch_info = os.lstat(fetch_head)
    except FileNotFoundError:
        fetch_bytes = None
    except OSError as exc:
        raise SourceHistoryError(f"cannot inspect FETCH_HEAD: {exc}") from exc
    else:
        if stat.S_ISLNK(fetch_info.st_mode) or not stat.S_ISREG(fetch_info.st_mode):
            raise SourceHistoryError("FETCH_HEAD must not be a symlink or special file")
        fetch_bytes = _sha256_file(fetch_head)
    refs = _read_refs(root)
    replace_refs = {ref: oid for ref, oid in refs.items() if ref.startswith("refs/replace/")}
    return head, symbolic_head, refs, fetch_bytes, replace_refs


def _assert_current_store_has_no_alternates(root: Path) -> None:
    _assert_current_graph_metadata_safe(root)
    objects = Path(_git(root, ["rev-parse", "--git-path", "objects"]).stdout.decode("utf-8", "strict").strip())
    if not objects.is_absolute():
        objects = root / objects
    _lstat_chain(objects.parent, Path(objects.name), regular=False)
    _lstat_chain(objects, Path("info"), regular=False)
    for relative in (Path("info/alternates"), Path("info/http-alternates")):
        if _optional_lstat_chain(objects, relative) is not None:
            raise SourceHistoryError(f"current Git object store has forbidden alternates: {relative}")
    refs = Path(_git(root, ["rev-parse", "--git-path", "refs"]).stdout.decode("utf-8", "strict").strip())
    if not refs.is_absolute():
        refs = root / refs
    _lstat_chain(refs.parent, Path(refs.name), regular=False)
    _assert_no_symlink_entries(refs)
    head_path = Path(_git(root, ["rev-parse", "--git-path", "HEAD"]).stdout.decode("utf-8", "strict").strip())
    if not head_path.is_absolute():
        head_path = root / head_path
    _lstat_chain(head_path.parent, Path(head_path.name), regular=True)


def _absolute_git_directory(root: Path, args: Sequence[str]) -> Path:
    raw = _git(root, list(args)).stdout.decode("utf-8", "strict").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path


def _assert_real_directory_path(path: Path, label: str) -> None:
    """Check every Git metadata directory component without following symlinks."""
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise SourceHistoryError(f"cannot inspect {label} path {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise SourceHistoryError(f"{label} path contains a symlink or non-directory: {current}")


def _assert_current_graph_metadata_safe(
    root: Path,
    *,
    gitdir: Path | None = None,
) -> None:
    """Reject local ancestry overrides before any current-history walk.

    Git grafts and shallow boundaries change ancestry results without changing
    commit objects.  Inspect both the per-worktree Git directory and shared
    common directory, including candidate object directories, and reject
    symlinks even when they point outside the checkout.
    """
    if gitdir is None:
        gitdir = _absolute_git_directory(root, ("rev-parse", "--absolute-git-dir"))
    common = _absolute_git_directory(root, ("rev-parse", "--git-common-dir"))
    directories = list(dict.fromkeys((Path(os.path.abspath(gitdir)), Path(os.path.abspath(common)))))
    for index, directory in enumerate(directories):
        label = "current Git directory" if index == 0 else "current Git common directory"
        _assert_real_directory_path(directory, label)
        for relative in (
            Path("info/grafts"),
            Path("shallow"),
            Path("objects/info/grafts"),
        ):
            if _optional_lstat_chain(directory, relative) is not None:
                raise SourceHistoryError(
                    f"current Git metadata contains a forbidden graft or shallow override: "
                    f"{directory / relative}"
                )


def _assert_current_fetch_config_safe(root: Path) -> None:
    """Refuse local URL rewrites or includes that could redirect an object-only fetch."""
    gitdir = Path(_git(root, ["rev-parse", "--absolute-git-dir"]).stdout.decode("utf-8", "strict").strip()).resolve(strict=True)
    common = Path(_git(root, ["rev-parse", "--git-common-dir"]).stdout.decode("utf-8", "strict").strip())
    if not common.is_absolute():
        common = root / common
    common = common.resolve(strict=True)
    configs = list(dict.fromkeys((gitdir / "config", common / "config")))
    executable = shutil.which("git")
    if not executable:
        raise SourceHistoryError("git executable was not found")
    for config in configs:
        _lstat_chain(config.parent, Path(config.name), regular=True)
        result = subprocess.run(
            [executable, "config", "--no-includes", "--file", str(config), "--null", "--list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
        if result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            raise SourceHistoryError(f"cannot safely read current Git config: {detail or result.returncode}")
        for entry in result.stdout.split(b"\x00"):
            if not entry:
                continue
            try:
                key, _value = entry.split(b"\n", 1)
            except ValueError as exc:
                raise SourceHistoryError("current Git configuration is malformed") from exc
            key = key.lower()
            if key.startswith((b"include.path", b"includeif.")):
                raise SourceHistoryError("current Git config includes are not allowed for object-only import")
            if key.startswith(b"url.") and key.endswith(b".insteadof"):
                raise SourceHistoryError("current Git URL rewrites are not allowed for object-only import")


def ensure_original_objects(root: Path, manifest_ref: str | Path) -> dict[str, Any]:
    """Import pinned old-source objects into the current object store only.

    No current ref, FETCH_HEAD, replacement ref, or alternate is created.  The
    returned receipt explicitly disclaims any current-branch ancestry claim.
    """
    root, _, _, manifest, head_before, caches = _load_verified(Path(root), manifest_ref)
    source_repo = caches["source_repo"]
    _assert_current_store_has_no_alternates(root)
    _assert_current_fetch_config_safe(root)
    before = _head_ref_state(root)
    if before[0] != head_before:
        raise SourceHistoryError("current HEAD changed while source history was being verified")
    result = _git(root, [
        "fetch", "--keep", "--no-tags", "--no-write-fetch-head", "--no-recurse-submodules",
        str(source_repo), *PINNED_SOURCE_REFS.keys(),
    ], check=False)
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SourceHistoryError(f"could not import verified source objects: {detail or result.returncode}")
    after = _head_ref_state(root)
    if before != after:
        raise SourceHistoryError("object import changed HEAD, refs, FETCH_HEAD, or replacement refs")
    _assert_current_store_has_no_alternates(root)
    _assert_no_historical_ancestor(root, head_before, require_present=True)
    return {
        "verified": True,
        "operation": "object-only-import",
        "root": str(root),
        "manifest_ref": MANIFEST_RELATIVE.as_posix(),
        "current_head": head_before,
        "original_main": manifest["original_main"],
        "original_source": PINNED_ORIGINAL_SOURCE,
        "original_core_source": manifest["original_core_source"],
        "pr295_rebased": manifest["original_source_refs"]["refs/heads/dave/v092-before-pr295-rebase-20261026"],
        "pre_rebase_main": manifest["original_source_refs"]["refs/heads/dave/v092-before-main-history-rebase-20261026"],
        "rebased_feature_head": manifest["rebased_feature_head"],
        "new_main_base": manifest["new_main_base"],
        "original_source_refs": dict(manifest["original_source_refs"]),
        "historical_commits_checked": list(_historical_commit_pins()),
        "bundle_sha256": manifest["bundle"]["sha256"],
        "main_archive_bundle_sha256": manifest["main_archive"]["bundle_sha256"],
        "current_ancestor_claim": False,
        "refs_changed": False,
        "fetch_head_changed": False,
        "alternates_added": False,
    }


def _all_source_paths(extra_source_paths: Sequence[str]) -> list[str]:
    selected = list(SOURCE_DIRECTORIES) + list(SOURCE_FILES)
    if isinstance(extra_source_paths, (str, bytes)):
        raise SourceHistoryError("extra_source_paths must be a sequence of repository-relative paths")
    for path in extra_source_paths:
        path = _safe_relative(path, "extra source path")
        if path.endswith("/"):
            raise SourceHistoryError("extra source paths must not end in '/' ")
        selected.append(path)
    return list(dict.fromkeys(selected))


def _is_selected(path: str, selected: Sequence[str]) -> bool:
    return any(path == item or (item in SOURCE_DIRECTORIES and path.startswith(item + "/")) for item in selected)


def _tree_entries(repo: Path, revision: str) -> list[tuple[str, str, str, str]]:
    raw = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", revision]).stdout
    entries: list[tuple[str, str, str, str]] = []
    for record in raw.split(b"\x00"):
        if not record:
            continue
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split(" ", 2)
            path = path_raw.decode("utf-8", "strict")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SourceHistoryError("source commit contains an invalid tree entry") from exc
        entries.append((path, mode, object_type, object_id))
    return entries


def _sparse_patterns(selected: Sequence[str]) -> bytes:
    patterns: list[str] = []
    directories = set(SOURCE_DIRECTORIES)
    for path in selected:
        pattern = path
        for character in "\\*?[":
            pattern = pattern.replace(character, "\\" + character)
        if path in directories:
            patterns.append(f"/{pattern}/")
        else:
            patterns.append(f"/{pattern}")
    return ("\n".join(patterns) + "\n").encode("utf-8")


def _view_path(gitdir: Path, bundle_sha: str, snapshot_commit: str) -> Path:
    cache_root, _, _, _ = _cache_paths(gitdir, bundle_sha)
    return cache_root / f"view-{snapshot_commit[:12]}"


def _ensure_view(
    source_repo: Path,
    view: Path,
    selected: Sequence[str],
    snapshot_commit: str,
) -> None:
    if view.exists() or view.is_symlink():
        if view.is_symlink() or not view.is_dir():
            raise SourceHistoryError("historical source view path is not a real directory")
        _validate_view(view, source_repo, selected, snapshot_commit)
        return

    _ensure_directory(view.parent)
    stage = view.parent / f"view.tmp-{os.getpid()}-{next(tempfile._get_candidate_names())}"
    try:
        _git(stage.parent, ["init", "--template=/dev/null", "--object-format=sha1", str(stage)])
        # Populate an independent object store; no source checkout or alternates are shared.
        source_ref = "refs/heads/dave/v092-before-pr295-rebase-20261026"
        _git(stage, [
            "fetch", "--keep", "--no-tags", "--no-write-fetch-head", "--no-recurse-submodules",
            str(source_repo), f"+{source_ref}:refs/heads/original-source",
        ])
        if _git(stage, ["rev-parse", "refs/heads/original-source"]).stdout.decode("ascii", "strict").strip() != snapshot_commit:
            _git(stage, ["update-ref", "refs/heads/original-source", snapshot_commit])
        _git(stage, ["config", "--local", "core.sparseCheckout", "true"])
        info = stage / ".git" / "info"
        _ensure_directory(info)
        sparse = info / "sparse-checkout"
        sparse.write_bytes(_sparse_patterns(selected))
        _git(stage, ["checkout", "--detach", snapshot_commit])
        _validate_view(stage, source_repo, selected, snapshot_commit)
        os.replace(stage, view)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    _validate_view(view, source_repo, selected, snapshot_commit)


def _view_gitdir(view: Path) -> Path:
    _lstat_chain(view, Path(".git"), regular=False)
    return (view / ".git").resolve(strict=True)


def _selected_status_paths(selected: Sequence[str]) -> list[str]:
    return list(selected)


def _scan_view_paths(view: Path, selected: Sequence[str]) -> None:
    for path in selected:
        target = view / path
        if target.is_symlink():
            raise SourceHistoryError(f"historical source view contains a symlink: {path}")
        if target.is_file():
            if not stat.S_ISREG(os.lstat(target).st_mode):
                raise SourceHistoryError(f"historical source view contains a non-regular file: {path}")
            continue
        if target.is_dir():
            pending = [target]
            while pending:
                directory = pending.pop()
                try:
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            info = entry.stat(follow_symlinks=False)
                            if stat.S_ISLNK(info.st_mode):
                                raise SourceHistoryError(f"historical source view contains a symlink: {entry.path}")
                            if stat.S_ISDIR(info.st_mode):
                                pending.append(Path(entry.path))
                            elif not stat.S_ISREG(info.st_mode):
                                raise SourceHistoryError(f"historical source view contains a non-regular file: {entry.path}")
                except OSError as exc:
                    raise SourceHistoryError(f"cannot inspect historical source view: {exc}") from exc


def _validate_view(
    view: Path,
    source_repo: Path,
    selected: Sequence[str],
    snapshot_commit: str,
) -> None:
    if view.is_symlink() or not view.is_dir():
        raise SourceHistoryError("historical source view is not a real directory")
    gitdir = _view_gitdir(view)
    _assert_no_symlink_entries(gitdir / "objects")
    _assert_no_alternates(gitdir)
    _lstat_chain(gitdir, Path("HEAD"), regular=True)
    _check_config(gitdir, bare=False)
    if _read_refs(gitdir) != {"refs/heads/original-source": snapshot_commit}:
        raise SourceHistoryError("historical source view refs do not match its pinned checkout")
    head = _git(view, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.decode("ascii", "strict").strip()
    if head != snapshot_commit:
        raise SourceHistoryError("historical source view HEAD is not the requested pinned source commit")
    if snapshot_commit not in {PINNED_ORIGINAL_SOURCE, PINNED_ORIGINAL_CORE_SOURCE}:
        raise SourceHistoryError("historical source view commit is not one of the pinned source snapshots")
    source_tree = _tree_entries(source_repo, snapshot_commit)
    for path, mode, _kind, _oid in source_tree:
        if not _is_selected(path, selected):
            continue
        if mode in {"120000", "160000"}:
            raise SourceHistoryError(f"selected historical source path is a symlink or submodule: {path}")
    _scan_view_paths(view, selected)
    diff = _git(view, ["diff", "--quiet", snapshot_commit, "--", *_selected_status_paths(selected)], check=False)
    if diff.returncode:
        raise SourceHistoryError("historical source view has changed tracked source bytes")
    cached = _git(view, ["diff", "--cached", "--quiet", snapshot_commit, "--", *_selected_status_paths(selected)], check=False)
    if cached.returncode:
        raise SourceHistoryError("historical source view index differs from the original source tree")
    status = _git(view, ["status", "--porcelain=v1", "--untracked-files=all", "--", *_selected_status_paths(selected)]).stdout
    if status.strip():
        raise SourceHistoryError("historical source view has modified or untracked selected paths")
    sparse_file = gitdir / "info" / "sparse-checkout"
    _lstat_chain(gitdir, Path("info/sparse-checkout"), regular=True)
    if sparse_file.read_bytes() != _sparse_patterns(selected):
        raise SourceHistoryError("historical source view sparse path selection changed")
    # Ensure the view contains its own object store and not a linked worktree file.
    if not (gitdir / "objects").is_dir():
        raise SourceHistoryError("historical source view has no local object store")


def historical_source_view(
    root: Path,
    manifest_ref: str | Path,
    extra_source_paths: Sequence[str],
    snapshot_commit: str | None = None,
) -> dict[str, Any]:
    """Return a verified sparse checkout at pinned original source ``2991...``
    or core source ``328...``.

    Selected paths match ``execute-release-v092._assert_source_snapshot`` plus
    any explicitly bound ``source_inputs`` paths.  The receipt describes the
    historical view only and makes no claim about current-root ancestry.
    """
    selected = _all_source_paths(extra_source_paths)
    if snapshot_commit is None:
        snapshot_commit = PINNED_ORIGINAL_SOURCE
    if snapshot_commit not in {PINNED_ORIGINAL_SOURCE, PINNED_ORIGINAL_CORE_SOURCE}:
        raise SourceHistoryError("snapshot_commit must be one of the pinned original source commits")
    root, gitdir, _, manifest, _head, caches = _load_verified(Path(root), manifest_ref)
    view = _view_path(gitdir, manifest["bundle"]["sha256"], snapshot_commit)
    _ensure_view(caches["source_repo"], view, selected, snapshot_commit)
    _validate_view(view, caches["source_repo"], selected, snapshot_commit)
    return {
        "verified": True,
        "operation": "historical-source-view",
        "root": str(root),
        "view_root": str(view),
        "manifest_ref": MANIFEST_RELATIVE.as_posix(),
        "view_head": snapshot_commit,
        "snapshot_kind": "original-core-source" if snapshot_commit == PINNED_ORIGINAL_CORE_SOURCE else "original-source",
        "original_main": manifest["original_main"],
        "original_source": PINNED_ORIGINAL_SOURCE,
        "original_core_source": manifest["original_core_source"],
        "pr295_rebased": manifest["original_source_refs"]["refs/heads/dave/v092-before-pr295-rebase-20261026"],
        "pre_rebase_main": manifest["original_source_refs"]["refs/heads/dave/v092-before-main-history-rebase-20261026"],
        "rebased_feature_head": manifest["rebased_feature_head"],
        "new_main_base": manifest["new_main_base"],
        "original_source_refs": dict(manifest["original_source_refs"]),
        "historical_commits_checked": list(_historical_commit_pins()),
        "bundle_sha256": manifest["bundle"]["sha256"],
        "main_archive_bundle_sha256": manifest["main_archive"]["bundle_sha256"],
        "selected_source_paths": selected,
        "current_ancestor_claim": False,
    }
