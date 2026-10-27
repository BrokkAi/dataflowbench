#!/usr/bin/env python3
"""Safely restore the exact ignored cache files retained in the v0.9.2 bundle.

Bundle verification is delivery-integrity checking only. It does not qualify a
tool, rerun an analyzer, or change the retained failed qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import uuid


ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = PurePosixPath("reports/releases/v0.9.2/qualification/bifrost-attempt-02")
MANIFEST = ATTEMPT / "artifact-hashes.json"
BUNDLE = Path("evidence-delivery/v092-control-cache-01/detail")

# This allowlist binds the restore helper to the eight cache objects that were
# checked against bifrost-attempt-02/artifact-hashes.json before bundling.
EXPECTED = {
    "cache/dataflowbench-9c6918ff99f31ecf/bifrost_cache.v188.db":
        (27983872, "b15df377291f9f575a46f8556a64b27d81974189d60ad3b86734b310f74b53a4"),
    "cache/dataflowbench-9c6918ff99f31ecf/bifrost_cache.v188.db-shm":
        (32768, "8730731b7155fced08979712dcec9ce837cbd1a19e3cb2bd02bcfd1e2298b6aa"),
    "cache/dataflowbench-9c6918ff99f31ecf/bifrost_cache.v188.db-wal":
        (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "cache/dataflowbench-9c6918ff99f31ecf/bifrost_cache.v188.db.initial-build.lock":
        (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "cache/dataflowbench-9c6918ff99f31ecf/semantic-pack-catalog.v21/catalog.db":
        (450560, "24c48b72a23e4109544996e73b0269d8fb74501e2d339c8f1cf183024f16c52d"),
    "cache/dataflowbench-9c6918ff99f31ecf/semantic-pack-catalog.v21/locks/catalog-initialization.lock":
        (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "cache/store-templates/semantic-pack-catalog-template-21-08c95f3e4cb0a1f7d9da729920a6c2644d78c5726d2a8a0ea76cf0c441fe07b8.db":
        (450560, "24c48b72a23e4109544996e73b0269d8fb74501e2d339c8f1cf183024f16c52d"),
    "cache/store-templates/store-template-188-b7b492d6077cb3fd843dc43df3e9278719f8944f6887cb392ed358108a12ddb0.db":
        (27656192, "a3bb0c308ff5f025490e8e2144dcf2fba3d74af2fce823d5a0f21e92d63e9c1a"),
}
EXPECTED_BYTES = 56573952


def _load_bundle_module():
    spec = importlib.util.spec_from_file_location(
        "v092_evidence_bundle", ROOT / "scripts" / "evidence_bundle.py")
    if spec is None or spec.loader is None:
        raise ValueError("cannot load evidence bundle verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_source_manifest(root: Path) -> dict[str, dict]:
    manifest_path = root.joinpath(*MANIFEST.parts)
    eb = _load_bundle_module()
    eb._assert_no_symlink_components(manifest_path)
    require(stat.S_ISREG(manifest_path.lstat().st_mode), "artifact manifest is not regular")
    require(manifest_path.stat().st_size <= 16 * 1024 * 1024, "artifact manifest too large")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid artifact manifest: {exc}") from exc
    files = manifest.get("files") if type(manifest) is dict else None
    require(type(files) is list, "artifact manifest has no file list")
    by_path: dict[str, dict] = {}
    for row in files:
        require(type(row) is dict, "invalid artifact manifest row")
        path = eb.safe_path(row.get("path"))
        if path.parts and path.parts[0] == "cache":
            require(str(path) not in by_path, "duplicate cache manifest path")
            by_path[str(path)] = row
    require(set(by_path) == set(EXPECTED), "cache manifest membership changed")
    require(sum(row.get("bytes", -1) for row in by_path.values()) == EXPECTED_BYTES,
            "cache manifest byte total changed")
    for path, (size, sha) in EXPECTED.items():
        row = by_path[path]
        require(type(row.get("bytes")) is int and row["bytes"] == size and
                row.get("sha256") == sha, f"cache artifact fingerprint changed: {path}")
    return by_path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def restore(root: os.PathLike[str] | str = ROOT,
            bundle: os.PathLike[str] | str | None = None) -> dict:
    """Verify and restore only absent cache files; matching files are untouched."""
    root_path = Path(os.path.abspath(os.fspath(root)))
    attempt = root_path.joinpath(*ATTEMPT.parts)
    eb = _load_bundle_module()
    eb._assert_no_symlink_components(root_path)
    eb._assert_no_symlink_components(attempt)
    require(attempt.is_dir(), "attempt directory is missing")
    source_rows = _validate_source_manifest(root_path)

    bundle_path = Path(bundle) if bundle is not None else root_path / BUNDLE
    if not bundle_path.is_absolute():
        bundle_path = root_path / bundle_path
    # check() verifies metadata, every part, the compressed manifest, every
    # archived object, the tar structure, and the gzip trailer before restore.
    index, scope, bundle_manifest, parts = eb._validated_index(bundle_path)
    records, by_object = eb._manifest_records(bundle_path, index, scope, bundle_manifest)
    expected_bundle_paths = {
        (ATTEMPT / relative).as_posix(): source_rows[relative]
        for relative in EXPECTED
    }
    require(set(row["path"] for row in records) == set(expected_bundle_paths),
            "bundle membership differs from the eight cache files")
    for row in records:
        expected = expected_bundle_paths[row["path"]]
        require(row["bytes"] == expected["bytes"] and row["sha256"] == expected["sha256"],
                f"bundle fingerprint differs from artifact manifest: {row['path']}")
    require(index["scope"] == ATTEMPT.as_posix() + "/cache" and
            index["snapshot_file_count"] == len(EXPECTED) and
            index["original_bytes"] == EXPECTED_BYTES,
            "bundle scope or totals changed")
    eb.check(bundle_path)

    targets: list[tuple[Path, str, int]] = []
    for relative, source_row in source_rows.items():
        target = attempt.joinpath(*PurePosixPath(relative).parts)
        eb._assert_no_symlink_components(target.parent)
        if os.path.lexists(target):
            eb._assert_no_symlink_components(target)
            info = target.lstat()
            require(stat.S_ISREG(info.st_mode), f"cache target is not a regular file: {relative}")
            require(info.st_size == source_row["bytes"] and _sha(target) == source_row["sha256"],
                    f"existing cache target differs; refusing overwrite: {relative}")
        targets.append((target, source_row["sha256"], source_row["bytes"]))

    # evidence_bundle restores atomically to a new private staging directory.
    stage = attempt / (".v092-control-cache-stage-" + uuid.uuid4().hex)
    selected = [path for path in expected_bundle_paths]
    eb.check(bundle_path, restore=stage, paths=selected)
    staged_targets: list[tuple[Path, Path, str, int]] = []
    created: list[tuple[Path, int, int]] = []
    try:
        for target, sha, size in targets:
            relative = target.relative_to(attempt).as_posix()
            staged = stage.joinpath(*ATTEMPT.parts, *PurePosixPath(relative).parts)
            eb._assert_no_symlink_components(staged)
            info = staged.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_size == size and _sha(staged) == sha,
                    f"staged cache object failed verification: {relative}")
            staged_targets.append((staged, target, sha, size))

        for staged, target, sha, size in staged_targets:
            if os.path.lexists(target):
                # A matching file that appeared after preflight remains intact.
                info = target.lstat()
                require(stat.S_ISREG(info.st_mode) and info.st_size == size and _sha(target) == sha,
                        f"cache target appeared with different bytes: {target}")
                continue
            eb._assert_no_symlink_components(target.parent)
            target.parent.mkdir(parents=True, exist_ok=True)
            eb._assert_no_symlink_components(target.parent)
            try:
                os.link(staged, target, follow_symlinks=False)
            except FileExistsError:
                info = target.lstat()
                require(stat.S_ISREG(info.st_mode) and info.st_size == size and _sha(target) == sha,
                        f"cache target raced with different bytes: {target}")
                continue
            info = target.lstat()
            created.append((target, info.st_dev, info.st_ino))

        restored = sum(1 for target, _, _ in targets if target.exists())
        return {"status": "verified-and-restored", "cache_files": len(targets),
                "restored_files": len(created), "preserved_existing_files": restored - len(created),
                "original_bytes": EXPECTED_BYTES,
                "bundle_check_status": "verified",
                "qualification_claim": False}
    except BaseException:
        # Roll back only hard links this invocation can identify by inode.
        for target, device, inode in reversed(created):
            try:
                info = target.lstat()
                if (info.st_dev, info.st_ino) == (device, inode):
                    target.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        import shutil
        shutil.rmtree(stage, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.root, args.bundle), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
