"""Versioned point-in-time inventory for Swift extraction artifacts.

The inventory uses lstat semantics: directory symlinks are recorded as links
and never traversed. Link targets are resolved structurally to reject targets
that escape the inventory root, dangle, or form a link cycle. A successful
snapshot is not a stable snapshot and does not prove process containment.
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path


MANIFEST_SCHEMA = "swift-artifact-closure/v1"
DELTA_SCHEMA = "swift-artifact-closure-delta/v1"
INCOMPLETE = "IncompleteArtifactClosure"
COMPLETE = "CompleteArtifactClosure"


class ArtifactClosureError(ValueError):
    """Inventory could not establish a complete point-in-time closure."""

    status = INCOMPLETE


def _fail(message: str) -> None:
    raise ArtifactClosureError(f"{INCOMPLETE}: {message}")


def _signature(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)


def _absolute_target(root: Path, target: str) -> tuple[str, ...]:
    """Convert an absolute link target to root-relative components."""
    try:
        relative = Path(target).relative_to(root)
    except ValueError:
        _fail(f"symlink target escapes root: {target!r}")
    return relative.parts


def _resolve_link(root: Path, link_parts: tuple[str, ...]) -> tuple[tuple[str, ...], int]:
    """Resolve a link without opening/following it, returning target and mode."""
    link_path = root.joinpath(*link_parts)
    try:
        literal = os.readlink(link_path)
    except OSError as error:
        _fail(f"cannot read symlink {link_path}: {error}")

    if os.path.isabs(literal):
        pending = list(_absolute_target(root, literal))
        resolved: list[str] = []
    else:
        resolved = list(link_parts[:-1])
        pending = literal.split(os.sep)

    visited: set[tuple[str, ...]] = {link_parts}
    while pending:
        # POSIX path lookup requires every already-resolved prefix to be a
        # directory before processing another component, including "..".
        if resolved:
            prefix = root.joinpath(*resolved)
            try:
                prefix_info = os.lstat(prefix)
            except OSError as error:
                _fail(f"dangling or inaccessible symlink {link_path} -> {literal!r}: {error}")
            if stat.S_ISLNK(prefix_info.st_mode) or not stat.S_ISDIR(prefix_info.st_mode):
                _fail(f"non-directory symlink target component: {prefix}")
        component = pending.pop(0)
        if component in ("", "."):
            continue
        if component == "..":
            if not resolved:
                _fail(f"symlink target escapes root: {link_path} -> {literal!r}")
            resolved.pop()
            continue

        resolved.append(component)
        candidate = root.joinpath(*resolved)
        try:
            info = os.lstat(candidate)
        except OSError as error:
            _fail(f"dangling or inaccessible symlink {link_path} -> {literal!r}: {error}")

        if stat.S_ISLNK(info.st_mode):
            current = tuple(resolved)
            if current in visited:
                _fail(f"symlink cycle at {candidate}")
            visited.add(current)
            try:
                chained = os.readlink(candidate)
            except OSError as error:
                _fail(f"cannot read symlink {candidate}: {error}")
            resolved.pop()
            if os.path.isabs(chained):
                resolved = []
                pending = list(_absolute_target(root, chained)) + pending
            else:
                pending = chained.split(os.sep) + pending

    terminal = root.joinpath(*resolved)
    try:
        terminal_info = os.lstat(terminal)
    except OSError as error:
        _fail(f"dangling symlink {link_path} -> {literal!r}: {error}")

    # A directory link to its own directory or an ancestor would create a
    # recursive walk if a consumer followed it. Reject that structural cycle
    # even though this inventory deliberately does not traverse the link.
    if stat.S_ISDIR(terminal_info.st_mode) and tuple(resolved) == tuple(link_parts[:-1]):
        _fail(f"directory symlink cycle at {link_path}")
    if stat.S_ISDIR(terminal_info.st_mode) and tuple(link_parts[:-1][:len(resolved)]) == tuple(resolved):
        _fail(f"directory symlink cycle at {link_path}")
    return tuple(resolved), terminal_info.st_mode


def _hash_regular_file(path: Path, before: os.stat_result) -> str:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        _fail(f"cannot open regular file without following links {path}: {error}")
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _signature(opened) != _signature(before):
            _fail(f"file changed during inventory: {path}")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if _signature(after) != _signature(opened):
            _fail(f"file changed while hashing: {path}")
    finally:
        os.close(descriptor)
    try:
        path_after = os.lstat(path)
    except OSError as error:
        _fail(f"file disappeared during inventory {path}: {error}")
    if _signature(path_after) != _signature(before):
        _fail(f"file changed during inventory: {path}")
    return digest.hexdigest()


def snapshot(root: str | os.PathLike[str]) -> dict:
    """Return a versioned lstat inventory for one artifact root.

    Entries include directories, regular files, and symlinks. Symlink targets
    are stored literally with a digest of their filesystem-encoded bytes. The
    returned manifest describes an observation interval; it does not prove
    that the tree stayed stable before, during, or after the scan.
    """
    supplied = Path(root).absolute()
    try:
        root_info = os.lstat(supplied)
    except OSError as error:
        _fail(f"cannot lstat root {supplied}: {error}")
    if not stat.S_ISDIR(root_info.st_mode):
        _fail(f"root must be a real directory: {supplied}")
    canonical_root = Path(os.path.realpath(supplied))

    entries: list[dict] = []
    pending_dirs: list[tuple[str, ...]] = [()]
    while pending_dirs:
        directory_parts = pending_dirs.pop()
        directory = canonical_root.joinpath(*directory_parts)
        try:
            before_dir = os.lstat(directory)
            if not stat.S_ISDIR(before_dir.st_mode):
                _fail(f"directory changed type during inventory: {directory}")
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
            for child in children:
                parts = directory_parts + (child.name,)
                path = canonical_root.joinpath(*parts)
                try:
                    info = os.lstat(path)
                except OSError as error:
                    _fail(f"entry disappeared during inventory {path}: {error}")

                relative = Path(*parts).as_posix()
                mode = stat.S_IMODE(info.st_mode)
                if stat.S_ISDIR(info.st_mode):
                    entries.append({"path": relative, "kind": "directory", "mode": mode})
                    pending_dirs.append(parts)
                elif stat.S_ISREG(info.st_mode):
                    entries.append({
                        "path": relative,
                        "kind": "regular-file",
                        "mode": mode,
                        "size_bytes": info.st_size,
                        "sha256": _hash_regular_file(path, info),
                    })
                elif stat.S_ISLNK(info.st_mode):
                    try:
                        target = os.readlink(path)
                    except OSError as error:
                        _fail(f"cannot read symlink {path}: {error}")
                    _resolve_link(canonical_root, parts)
                    try:
                        after_link = os.lstat(path)
                        after_target = os.readlink(path)
                    except OSError as error:
                        _fail(f"symlink changed during inventory {path}: {error}")
                    if _signature(after_link) != _signature(info) or after_target != target:
                        _fail(f"symlink changed during inventory: {path}")
                    target_bytes = os.fsencode(target)
                    entries.append({
                        "path": relative,
                        "kind": "symlink",
                        "target": target,
                        "target_sha256": hashlib.sha256(target_bytes).hexdigest(),
                    })
                else:
                    _fail(f"unsupported special filesystem entry: {path}")

            after_dir = os.lstat(directory)
            if _signature(after_dir) != _signature(before_dir):
                _fail(f"directory changed during inventory: {directory}")
        except ArtifactClosureError:
            raise
        except OSError as error:
            _fail(f"cannot enumerate directory {directory}: {error}")

    entries.sort(key=lambda entry: entry["path"])
    return {
        "schema": MANIFEST_SCHEMA,
        "version": 1,
        "root": str(canonical_root),
        "snapshot_semantics": "point-in-time-observation; stability-and-containment-unproven",
        "entries": entries,
    }


def compare(before: dict, after: dict) -> dict:
    """Compare two manifests, reporting complete added/changed/removed rows."""
    for label, manifest in (("before", before), ("after", after)):
        if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("version") != 1:
            _fail(f"unsupported {label} manifest")
        if not isinstance(manifest.get("root"), str) or not isinstance(manifest.get("entries"), list):
            _fail(f"malformed {label} manifest")
    def index(manifest: dict, label: str) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for entry in manifest["entries"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                _fail(f"malformed {label} entry")
            path = entry["path"]
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts or path in ("", "."):
                _fail(f"unsafe {label} path: {path!r}")
            if path in result:
                _fail(f"duplicate {label} path: {path!r}")
            result[path] = entry
        return result

    old = index(before, "before")
    new = index(after, "after")
    old_paths, new_paths = set(old), set(new)
    added = [{"path": path, "after": new[path]} for path in sorted(new_paths - old_paths)]
    removed = [{"path": path, "before": old[path]} for path in sorted(old_paths - new_paths)]
    changed = [
        {"path": path, "before": old[path], "after": new[path]}
        for path in sorted(old_paths & new_paths)
        if old[path] != new[path]
    ]
    status = COMPLETE if not (added or changed or removed) else INCOMPLETE
    return {
        "schema": DELTA_SCHEMA,
        "version": 1,
        "before_root": before["root"],
        "after_root": after["root"],
        "status": status,
        "snapshot_semantics": "point-in-time-observation; stability-and-containment-unproven",
        "added": added,
        "changed": changed,
        "removed": removed,
    }
