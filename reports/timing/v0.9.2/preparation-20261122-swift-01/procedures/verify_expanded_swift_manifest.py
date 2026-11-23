#!/usr/bin/env python3
"""Compare an expanded Swift Payload/usr tree to its frozen file manifest."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import sys
import time


ROOT = Path("/Users/dave/.codex/worktrees/cb55/dataflowbench")
PAYLOAD_ROOT = ROOT / (
    "execution-state/timing-swift-repair-20261122-01/expanded/"
    "swift-6.3.3-RELEASE-osx-package.pkg/swift-6.3.3-RELEASE-osx-package.pkg/Payload/usr"
)
MANIFEST_PATH = ROOT / "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-6.3.3.json"
RECEIPT_PATH = ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01/manifest-verification.json"
EXPECTED_MANIFEST_SHA256 = "f31ae5b23c775e0c69227363a1a0c4e4bf87964f8bcd79b8f9de9d7acd7d4a58"
MIN_FREE_BYTES = 134_217_728_000


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mode(path):
    return stat.S_IMODE(path.lstat().st_mode)


def actual_tree(root):
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                result[path.relative_to(root).as_posix()] = {
                    "kind": "symlink", "target": os.readlink(path), "mode": mode(path)
                }
                directories.remove(name)
        for name in files:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = {"kind": "symlink", "target": os.readlink(path), "mode": mode(path)}
            elif stat.S_ISREG(path.lstat().st_mode):
                result[relative] = {"kind": "file", "sha256": sha256(path), "mode": mode(path)}
            else:
                raise RuntimeError(f"unsupported filesystem entry: {path}")
    return result


def main():
    started_utc = utc_now()
    started = time.monotonic()
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError(f"manifest SHA-256 mismatch: {manifest_sha}")
    manifest = json.loads(manifest_bytes)
    expected = {}
    duplicates = []
    for item in manifest["files"]:
        relative = item["path"]
        if relative in expected:
            duplicates.append(relative)
        expected[relative] = {"kind": "file", "sha256": item["sha256"], "mode": item["mode"]}
    for item in manifest["symlinks"]:
        relative = item["path"]
        if relative in expected:
            duplicates.append(relative)
        expected[relative] = {"kind": "symlink", "target": item["target"], "mode": item["mode"]}
    if duplicates:
        raise RuntimeError(f"duplicate manifest entries: {duplicates[:20]}")
    if not PAYLOAD_ROOT.is_dir() or PAYLOAD_ROOT.is_symlink():
        raise RuntimeError(f"payload root is unavailable or not a real directory: {PAYLOAD_ROOT}")
    free_before = shutil.disk_usage(ROOT).free
    if free_before < MIN_FREE_BYTES:
        raise RuntimeError(f"free-space floor lost before verification: {free_before} bytes")

    actual = actual_tree(PAYLOAD_ROOT)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    different = []
    for relative in sorted(set(expected) & set(actual)):
        if expected[relative] != actual[relative]:
            different.append({"path": relative, "expected": expected[relative], "actual": actual[relative]})
    free_after = shutil.disk_usage(ROOT).free
    success = not missing and not extra and not different and free_after >= MIN_FREE_BYTES
    receipt = {
        "schema": "dfb-swift-expanded-payload-manifest-verification/v1",
        "status": "verified" if success else "mismatch",
        "started_utc": started_utc,
        "finished_utc": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "package_path": "execution-state/timing-runtime-20261114-01/jvm/swift-6.3.3/swift-6.3.3-RELEASE-osx.pkg",
        "package_sha256": "ee82e57774d6650f94aa06302435d6f44a055b9411698db8ecb85d9a3bcc91d0",
        "payload_usr_root": str(PAYLOAD_ROOT),
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "manifest_sha256": manifest_sha,
        "expected_regular_files": len(manifest["files"]),
        "actual_regular_files": sum(item["kind"] == "file" for item in actual.values()),
        "expected_symlinks": len(manifest["symlinks"]),
        "actual_symlinks": sum(item["kind"] == "symlink" for item in actual.values()),
        "manifest_external_files": len(manifest.get("external_files", [])),
        "verification_scope": "all regular files, symlink targets, modes, and membership under Payload/usr; external_files is empty",
        "expected_entries": len(expected),
        "actual_entries": len(actual),
        "membership_exact": not missing and not extra,
        "hashes_modes_symlinks_exact": not different,
        "missing_paths": missing,
        "extra_paths": extra,
        "different_entries": different,
        "disk_floor_bytes": MIN_FREE_BYTES,
        "free_bytes_before": free_before,
        "free_bytes_after": free_after,
        "verifier_script": str(Path(__file__).relative_to(ROOT)),
        "analyzer_or_build_invoked": False,
    }
    if RECEIPT_PATH.exists():
        raise RuntimeError(f"refusing to overwrite receipt: {RECEIPT_PATH}")
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in (
        "status", "expected_regular_files", "actual_regular_files", "expected_symlinks",
        "actual_symlinks", "expected_entries", "actual_entries", "membership_exact",
        "hashes_modes_symlinks_exact", "free_bytes_after", "elapsed_seconds")}, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"manifest verification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
