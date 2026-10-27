#!/usr/bin/env python3
"""Fail-closed disk-capacity checks for bounded v0.9.2 evidence writes.

    The guard uses logical file sizes for the scratch, retention, and working-area
    ceilings. Capacity checks use current filesystem free bytes and reserve space
    for the complete projected write before any output is opened. Nested symlinks
    inside accounted trees are not followed or counted, matching the executor's
    prior accounting behavior; output source/target paths remain symlink-rejected.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import hashlib
from typing import Callable, Iterable


GIB = 1024**3
LAUNCH_FLOOR_BYTES = 110 * GIB
PROTECTED_RESERVE_BYTES = 40 * GIB
STOP_MARGIN_BYTES = 8 * GIB
STOP_FLOOR_BYTES = PROTECTED_RESERVE_BYTES + STOP_MARGIN_BYTES
SCRATCH_CEILING_BYTES = 24 * GIB
RETENTION_CEILING_BYTES = 24 * GIB
WORKING_CEILING_BYTES = 12 * GIB
COPY_CHUNK_BYTES = 1024**2


class DiskGuardError(RuntimeError):
    """A structured, fail-closed refusal or copy-integrity failure."""

    def __init__(self, code: str, message: str, **metadata: object) -> None:
        super().__init__(message)
        self.code = code
        self.metadata: dict[str, object] = {"code": code, **metadata}

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible error metadata suitable for evidence records."""
        return {**self.metadata, "message": str(self)}


DiskUsage = Callable[[Path], object]


def _budget(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DiskGuardError(
            "invalid_budget",
            f"{name} must be a non-negative integer byte count",
            field=name,
            value=repr(value),
        )
    return value


def _path(value: os.PathLike[str] | str, field: str) -> Path:
    try:
        return Path(value)
    except (TypeError, ValueError) as exc:
        raise DiskGuardError("invalid_path", f"{field} is not a valid filesystem path",
                             field=field, value=repr(value)) from exc


def _stat_signature(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class DiskGuard:
    """Check category ceilings and filesystem headroom before evidence writes.

    ``check(..., phase="launch")`` enforces the 110 GiB admission floor. All
    checks also ensure that the projected write leaves at least the 48 GiB
    proactive stop floor, which includes the protected 40 GiB reserve plus an
    8 GiB margin. ``paths`` are recursively measured by logical size; overlapping
    roots and hard links are counted once.

    ``disk_usage`` may return ``shutil.disk_usage``'s result or a free-byte
    integer, which keeps boundary behavior deterministic in small tests.
    """

    _CATEGORY_ALIASES = {
        "working": "working",
        "source": "working",
        "working_source": "working",
        "scratch": "scratch",
        "retention": "retention",
        "retained": "retention",
    }

    def __init__(
        self,
        *,
        launch_floor_bytes: int = LAUNCH_FLOOR_BYTES,
        protected_reserve_bytes: int = PROTECTED_RESERVE_BYTES,
        stop_margin_bytes: int = STOP_MARGIN_BYTES,
        stop_floor_bytes: int | None = None,
        scratch_ceiling_bytes: int = SCRATCH_CEILING_BYTES,
        retention_ceiling_bytes: int = RETENTION_CEILING_BYTES,
        working_ceiling_bytes: int = WORKING_CEILING_BYTES,
        disk_usage: DiskUsage | None = None,
    ) -> None:
        self.launch_floor_bytes = _budget(launch_floor_bytes, "launch_floor_bytes")
        self.protected_reserve_bytes = _budget(protected_reserve_bytes, "protected_reserve_bytes")
        self.stop_margin_bytes = _budget(stop_margin_bytes, "stop_margin_bytes")
        expected_stop_floor = self.protected_reserve_bytes + self.stop_margin_bytes
        self.stop_floor_bytes = _budget(
            expected_stop_floor if stop_floor_bytes is None else stop_floor_bytes,
            "stop_floor_bytes",
        )
        self.scratch_ceiling_bytes = _budget(scratch_ceiling_bytes, "scratch_ceiling_bytes")
        self.retention_ceiling_bytes = _budget(retention_ceiling_bytes, "retention_ceiling_bytes")
        self.working_ceiling_bytes = _budget(working_ceiling_bytes, "working_ceiling_bytes")
        if self.stop_floor_bytes < self.protected_reserve_bytes:
            raise DiskGuardError(
                "invalid_budget",
                "stop_floor_bytes cannot be below the protected reserve",
                field="stop_floor_bytes",
                value=self.stop_floor_bytes,
                protected_reserve_bytes=self.protected_reserve_bytes,
            )
        if self.launch_floor_bytes < self.stop_floor_bytes:
            raise DiskGuardError(
                "invalid_budget",
                "launch_floor_bytes cannot be below the proactive stop floor",
                field="launch_floor_bytes",
                value=self.launch_floor_bytes,
                stop_floor_bytes=self.stop_floor_bytes,
            )
        self._disk_usage = disk_usage or shutil.disk_usage

    @property
    def chunk_bytes(self) -> int:
        """Maximum file-copy chunk size used by bounded writers."""
        return COPY_CHUNK_BYTES

    @staticmethod
    def error(code: str, message: str, **metadata: object) -> DiskGuardError:
        """Create a typed guard error for a caller-detected write invariant."""
        return DiskGuardError(code, message, **metadata)

    def _free_bytes(self, capacity_path: os.PathLike[str] | str) -> int:
        path = _path(capacity_path, "capacity_path")
        try:
            result = self._disk_usage(path)
        except OSError as exc:
            raise DiskGuardError(
                "capacity_unavailable",
                f"cannot read filesystem capacity for {path}: {exc}",
                capacity_path=str(path),
            ) from exc
        free = result if isinstance(result, int) and not isinstance(result, bool) else getattr(result, "free", None)
        if isinstance(free, bool) or not isinstance(free, int) or free < 0:
            raise DiskGuardError(
                "capacity_unavailable",
                f"filesystem capacity for {path} did not provide a valid free-byte count",
                capacity_path=str(path),
                result_type=type(result).__name__,
            )
        return free

    def _category_limit(self, category: str) -> tuple[str, int]:
        canonical = self._CATEGORY_ALIASES.get(category)
        if canonical is None:
            raise DiskGuardError(
                "invalid_category",
                f"unknown disk-guard category {category!r}",
                category=category,
                allowed_categories=sorted(self._CATEGORY_ALIASES),
            )
        limit = {
            "working": self.working_ceiling_bytes,
            "scratch": self.scratch_ceiling_bytes,
            "retention": self.retention_ceiling_bytes,
        }[canonical]
        return canonical, limit

    @staticmethod
    def logical_size(paths: Iterable[os.PathLike[str] | str]) -> int:
        """Measure regular-file logical bytes once across overlapping roots."""
        total = 0
        seen_files: set[tuple[int, int]] = set()
        seen_dirs: set[tuple[int, int]] = set()
        for raw_path in paths:
            root = _path(raw_path, "accounting_path")
            try:
                root_info = root.lstat()
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise DiskGuardError(
                    "accounting_path_unavailable",
                    f"cannot inspect accounting path {root}: {exc}",
                    path=str(root),
                ) from exc
            if stat.S_ISLNK(root_info.st_mode):
                raise DiskGuardError(
                    "symlink_accounting_path",
                    f"accounting path is a symlink: {root}",
                    path=str(root),
                )
            if stat.S_ISREG(root_info.st_mode):
                identity = (root_info.st_dev, root_info.st_ino)
                if identity not in seen_files:
                    seen_files.add(identity)
                    total += root_info.st_size
                continue
            if not stat.S_ISDIR(root_info.st_mode):
                raise DiskGuardError(
                    "unsupported_accounting_path",
                    f"accounting path is not a regular file or directory: {root}",
                    path=str(root),
                    mode=root_info.st_mode,
                )

            stack = [root]
            while stack:
                directory = stack.pop()
                try:
                    directory_info = directory.lstat()
                except (FileNotFoundError, NotADirectoryError):
                    # Analyzer scratch entries may disappear while another
                    # process is trimming a temporary tree; a missing path has
                    # no current logical bytes to account.
                    continue
                except OSError as exc:
                    raise DiskGuardError(
                        "accounting_path_unavailable",
                        f"cannot inspect accounting directory {directory}: {exc}",
                        path=str(directory),
                    ) from exc
                if stat.S_ISLNK(directory_info.st_mode):
                    raise DiskGuardError(
                        "symlink_accounting_path",
                        f"accounting directory is a symlink: {directory}",
                        path=str(directory),
                    )
                dir_identity = (directory_info.st_dev, directory_info.st_ino)
                if dir_identity in seen_dirs:
                    continue
                seen_dirs.add(dir_identity)
                try:
                    entries = list(os.scandir(directory))
                except (FileNotFoundError, NotADirectoryError):
                    continue
                except OSError as exc:
                    raise DiskGuardError(
                        "accounting_path_unavailable",
                        f"cannot list accounting directory {directory}: {exc}",
                        path=str(directory),
                    ) from exc
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except (FileNotFoundError, NotADirectoryError):
                        continue
                    except OSError as exc:
                        raise DiskGuardError(
                            "accounting_path_unavailable",
                            f"cannot inspect accounting entry {entry.path}: {exc}",
                            path=entry.path,
                        ) from exc
                    # Do not follow links inside analyzer caches or temporary
                    # trees. A nested link consumes no additional bytes in the
                    # containing tree, and other explicitly accounted roots
                    # cover any target bytes stored within those roots.
                    if stat.S_ISLNK(info.st_mode):
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(Path(entry.path))
                    elif stat.S_ISREG(info.st_mode):
                        identity = (info.st_dev, info.st_ino)
                        if identity not in seen_files:
                            seen_files.add(identity)
                            total += info.st_size
                    # Sockets, FIFOs, and device entries have no regular-file
                    # logical size. Ignore them like the executor's legacy
                    # accounting, while still refusing non-regular roots.
        return total

    def check(
        self,
        *,
        projected_bytes: int = 0,
        additional_current_bytes: int = 0,
        category: str,
        paths: Iterable[os.PathLike[str] | str] = (),
        capacity_path: os.PathLike[str] | str | None = None,
        phase: str = "active",
    ) -> dict[str, object]:
        """Validate projected category usage and remaining filesystem capacity.

        ``phase="launch"`` additionally requires the current free space to meet
        the 110 GiB launch floor. Both phases require post-write free space to
        remain at or above the 48 GiB stop floor. ``additional_current_bytes``
        adds a previously measured immutable baseline while the caller rescans
        only a changing active tree; that baseline must be disjoint from
        ``paths``.
        """
        projected = _budget(projected_bytes, "projected_bytes")
        additional_current = _budget(additional_current_bytes, "additional_current_bytes")
        if phase not in {"launch", "active"}:
            raise DiskGuardError("invalid_phase", f"unknown disk-guard phase {phase!r}", phase=phase)
        canonical, limit = self._category_limit(category)
        path_list = tuple(_path(item, "accounting_path") for item in paths)
        current_bytes = self.logical_size(path_list) + additional_current
        category_projected = current_bytes + projected
        if category_projected > limit:
            raise DiskGuardError(
                "category_ceiling",
                f"projected {canonical} usage exceeds its configured ceiling",
                category=canonical,
                current_bytes=current_bytes,
                projected_bytes=projected,
                total_projected_bytes=category_projected,
                category_limit_bytes=limit,
                accounting_paths=[str(path) for path in path_list],
            )

        location = _path(
            capacity_path if capacity_path is not None else (path_list[0] if path_list else Path.cwd()),
            "capacity_path",
        )
        free = self._free_bytes(location)
        if phase == "launch" and free < self.launch_floor_bytes:
            raise DiskGuardError(
                "launch_floor",
                "current free space is below the v0.9.2 launch floor",
                phase=phase,
                free_bytes=free,
                required_free_bytes=self.launch_floor_bytes,
                projected_bytes=projected,
                capacity_path=str(location),
            )
        post_write_free = free - projected
        if post_write_free < self.stop_floor_bytes:
            raise DiskGuardError(
                "stop_floor",
                "projected write would cross the proactive protected-reserve stop floor",
                phase=phase,
                free_bytes=free,
                projected_bytes=projected,
                post_write_free_bytes=post_write_free,
                required_free_bytes=self.stop_floor_bytes,
                protected_reserve_bytes=self.protected_reserve_bytes,
                capacity_path=str(location),
            )
        return {
            "category": canonical,
            "current_bytes": current_bytes,
            "projected_bytes": projected,
            "total_projected_bytes": category_projected,
            "category_limit_bytes": limit,
            "free_bytes": free,
            "post_write_free_bytes": post_write_free,
            "stop_floor_bytes": self.stop_floor_bytes,
            "phase": phase,
            "capacity_path": str(location),
        }

    def check_capacity(
        self,
        *,
        projected_bytes: int = 0,
        capacity_path: os.PathLike[str] | str,
    ) -> dict[str, object]:
        """Recheck free-space headroom without rescanning category trees.

        Callers use ``check`` once to establish category usage for a projected
        operation, then this method before each bounded write chunk while
        tracking bytes written for that operation locally.
        """
        projected = _budget(projected_bytes, "projected_bytes")
        location = _path(capacity_path, "capacity_path")
        free = self._free_bytes(location)
        post_write_free = free - projected
        if post_write_free < self.stop_floor_bytes:
            raise DiskGuardError(
                "stop_floor",
                "projected write would cross the proactive protected-reserve stop floor",
                phase="active",
                free_bytes=free,
                projected_bytes=projected,
                post_write_free_bytes=post_write_free,
                required_free_bytes=self.stop_floor_bytes,
                protected_reserve_bytes=self.protected_reserve_bytes,
                capacity_path=str(location),
            )
        return {
            "free_bytes": free,
            "projected_bytes": projected,
            "post_write_free_bytes": post_write_free,
            "stop_floor_bytes": self.stop_floor_bytes,
            "capacity_path": str(location),
        }


def _lstat_regular(path: Path, *, role: str) -> os.stat_result:
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise DiskGuardError("missing_file", f"{role} file does not exist: {path}",
                             role=role, path=str(path)) from None
    except OSError as exc:
        raise DiskGuardError("file_unavailable", f"cannot inspect {role} file {path}: {exc}",
                             role=role, path=str(path)) from exc
    if stat.S_ISLNK(info.st_mode):
        raise DiskGuardError("symlink_path", f"{role} path is a symlink: {path}",
                             role=role, path=str(path))
    if not stat.S_ISREG(info.st_mode):
        raise DiskGuardError("not_regular_file", f"{role} path is not a regular file: {path}",
                             role=role, path=str(path), mode=info.st_mode)
    return info


def _ensure_target_parent(target: Path) -> None:
    try:
        info = target.parent.lstat()
    except OSError as exc:
        raise DiskGuardError("target_parent_unavailable",
                             f"cannot inspect target directory {target.parent}: {exc}",
                             path=str(target.parent)) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise DiskGuardError("unsafe_target_parent",
                             f"target parent must be a real directory: {target.parent}",
                             path=str(target.parent), mode=info.st_mode)


def bounded_regular_copy(
    source: os.PathLike[str] | str,
    target: os.PathLike[str] | str,
    guard: DiskGuard,
    *,
    category: str = "scratch",
    accounting_paths: Iterable[os.PathLike[str] | str] = (),
    category_preflight: bool = True,
    expected_source_signature: tuple[int, int, int, int, int] | None = None,
) -> dict[str, object]:
    """Copy one regular file with capacity checks and exclusive output creation.

    The source and target leaf paths must not be symlinks. The destination is
    opened with exclusive creation and is never truncated or replaced. A
    preflight refusal leaves the destination untouched; once copying begins,
    partial output is retained on any later capacity, I/O, or source-change
    failure so the caller can preserve the failure evidence.
    """
    source_path = _path(source, "source")
    target_path = _path(target, "target")
    source_before = _lstat_regular(source_path, role="source")
    if (expected_source_signature is not None and
            _stat_signature(source_before) != tuple(expected_source_signature)):
        raise DiskGuardError(
            "source_changed",
            f"source changed after its aggregate preflight: {source_path}",
            source_path=str(source_path),
            expected_signature=list(expected_source_signature),
            actual_signature=list(_stat_signature(source_before)),
        )
    _ensure_target_parent(target_path)
    try:
        existing_target = target_path.lstat()
    except FileNotFoundError:
        existing_target = None
    except OSError as exc:
        raise DiskGuardError("target_unavailable", f"cannot inspect target {target_path}: {exc}",
                             path=str(target_path)) from exc
    if existing_target is not None:
        code = "symlink_path" if stat.S_ISLNK(existing_target.st_mode) else "target_exists"
        raise DiskGuardError(code, f"refusing to replace existing target: {target_path}",
                             role="target", path=str(target_path))

    source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        source_fd = os.open(source_path, source_flags)
    except OSError as exc:
        raise DiskGuardError("source_open_failed", f"cannot open source {source_path}: {exc}",
                             path=str(source_path)) from exc
    try:
        source_info = os.fstat(source_fd)
        if not stat.S_ISREG(source_info.st_mode) or _stat_signature(source_info) != _stat_signature(source_before):
            raise DiskGuardError(
                "source_changed",
                f"source changed between preflight and open: {source_path}",
                source_path=str(source_path),
                expected_size_bytes=source_before.st_size,
                actual_size_bytes=source_info.st_size,
            )

        output_paths = tuple(_path(item, "accounting_path") for item in accounting_paths)
        # Include the target leaf so repeated checks account for bytes already
        # written even when the caller provides a broader aggregate directory.
        check_paths = (*output_paths, target_path)
        if category_preflight:
            guard.check(
                projected_bytes=source_info.st_size,
                category=category,
                paths=check_paths,
                capacity_path=target_path.parent,
            )
        else:
            guard.check_capacity(projected_bytes=source_info.st_size,
                                 capacity_path=target_path.parent)

        target_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            target_fd = os.open(target_path, target_flags, 0o600)
        except FileExistsError as exc:
            raise DiskGuardError("target_exists", f"refusing to replace existing target: {target_path}",
                                 path=str(target_path)) from exc
        except OSError as exc:
            raise DiskGuardError("target_open_failed", f"cannot create target {target_path}: {exc}",
                                 path=str(target_path)) from exc

        copied = 0
        digest = hashlib.sha256()
        source_file = os.fdopen(source_fd, "rb", buffering=0)
        source_fd = -1
        with source_file, os.fdopen(target_fd, "wb", buffering=0) as target_file:
            while True:
                # Re-read free space before every input chunk, then account for
                # that exact chunk before writing it.
                guard.check_capacity(capacity_path=target_path.parent)
                chunk = source_file.read(COPY_CHUNK_BYTES)
                if not chunk:
                    break
                if copied + len(chunk) > source_info.st_size:
                    raise DiskGuardError(
                        "source_grew",
                        f"source grew while it was being copied: {source_path}",
                        source_path=str(source_path),
                        expected_size_bytes=source_info.st_size,
                        observed_size_bytes=copied + len(chunk),
                        partial_bytes=copied,
                    )
                guard.check_capacity(projected_bytes=len(chunk), capacity_path=target_path.parent)
                chunk_written = 0
                try:
                    remaining = memoryview(chunk)
                    while remaining:
                        written = target_file.write(remaining)
                        if written is None or written <= 0:
                            raise OSError("write made no forward progress")
                        chunk_written += written
                        remaining = remaining[written:]
                    digest.update(chunk)
                except OSError as exc:
                    raise DiskGuardError(
                        "copy_write_failed",
                        f"failed writing {target_path} after {copied} bytes: {exc}",
                        source_path=str(source_path),
                        target_path=str(target_path),
                        partial_bytes=copied + chunk_written,
                    ) from exc
                copied += len(chunk)

            source_after = os.fstat(source_file.fileno())
            if copied != source_info.st_size or _stat_signature(source_after) != _stat_signature(source_info):
                raise DiskGuardError(
                    "source_changed",
                    f"source changed while it was being copied: {source_path}",
                    source_path=str(source_path),
                    expected_size_bytes=source_info.st_size,
                    copied_bytes=copied,
                    partial_bytes=copied,
                )
            target_file.flush()
            os.fsync(target_file.fileno())

        guard.check_capacity(capacity_path=target_path.parent)
        return {
            "source_path": str(source_path),
            "target_path": str(target_path),
            "copied_bytes": copied,
            "sha256": digest.hexdigest(),
            "category": category,
            "chunk_limit_bytes": COPY_CHUNK_BYTES,
        }
    except OSError as exc:
        raise DiskGuardError(
            "copy_io_failed",
            f"copy failed from {source_path} to {target_path}: {exc}",
            source_path=str(source_path),
            target_path=str(target_path),
        ) from exc
    finally:
        if source_fd >= 0:
            os.close(source_fd)


__all__ = [
    "COPY_CHUNK_BYTES",
    "DiskGuard",
    "DiskGuardError",
    "GIB",
    "LAUNCH_FLOOR_BYTES",
    "PROTECTED_RESERVE_BYTES",
    "RETENTION_CEILING_BYTES",
    "SCRATCH_CEILING_BYTES",
    "STOP_FLOOR_BYTES",
    "WORKING_CEILING_BYTES",
    "bounded_regular_copy",
]
