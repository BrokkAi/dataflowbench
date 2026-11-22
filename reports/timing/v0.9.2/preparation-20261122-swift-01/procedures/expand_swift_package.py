#!/usr/bin/env python3
"""Expand the pinned Swift installer payload without installing it."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path("/Users/dave/.codex/worktrees/cb55/dataflowbench")
ATTEMPT = ROOT / "execution-state/timing-swift-repair-20261122-01/expansion-attempt-01"
PACKAGE = ROOT / "execution-state/timing-runtime-20261114-01/jvm/swift-6.3.3/swift-6.3.3-RELEASE-osx.pkg"
MANIFEST = ROOT / "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-6.3.3.json"
DESTINATION = ROOT / "execution-state/timing-swift-repair-20261122-01/expanded/swift-6.3.3-RELEASE-osx-package.pkg"
DISK_ROOT = ROOT
MIN_FREE_BYTES = 134_217_728_000
PACKAGE_SHA256 = "ee82e57774d6650f94aa06302435d6f44a055b9411698db8ecb85d9a3bcc91d0"
MANIFEST_SHA256 = "f31ae5b23c775e0c69227363a1a0c4e4bf87964f8bcd79b8f9de9d7acd7d4a58"
PKGUTIL = "/usr/sbin/pkgutil"
SAMPLE_SECONDS = 30


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def process_identity(pid):
    try:
        result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
                                check=False, capture_output=True, text=True, timeout=5)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except Exception as exc:  # record process identity failure without hiding the expansion result
        return {"error": f"{type(exc).__name__}: {exc}"}


def main():
    ATTEMPT.mkdir(parents=True, exist_ok=False)
    if DESTINATION.exists():
        raise RuntimeError(f"refusing to replace existing destination: {DESTINATION}")
    if not PACKAGE.is_file() or not MANIFEST.is_file():
        raise RuntimeError("pinned package or manifest is unavailable")

    package_hash = sha256(PACKAGE)
    manifest_hash = sha256(MANIFEST)
    if package_hash != PACKAGE_SHA256:
        raise RuntimeError(f"package hash mismatch: {package_hash}")
    if manifest_hash != MANIFEST_SHA256:
        raise RuntimeError(f"manifest hash mismatch: {manifest_hash}")
    free_before = shutil.disk_usage(DISK_ROOT).free
    if free_before < MIN_FREE_BYTES:
        raise RuntimeError(f"free-space floor already lost: {free_before} bytes")

    argv = [PKGUTIL, "--expand-full", str(PACKAGE), str(DESTINATION)]
    started = time.monotonic()
    start_utc = utc_now()
    write_json(ATTEMPT / "command.json", {
        "schema": "dfb-swift-runtime-expansion-command/v1",
        "argv": argv,
        "cwd": str(ROOT),
        "started_utc": start_utc,
        "package_sha256": package_hash,
        "package_size_bytes": PACKAGE.stat().st_size,
        "manifest_sha256": manifest_hash,
        "destination": str(DESTINATION),
        "minimum_free_bytes": MIN_FREE_BYTES,
        "free_bytes_before": free_before,
        "disk_sample_interval_seconds": SAMPLE_SECONDS,
        "non_installing": True,
    })

    with (ATTEMPT / "stdout.txt").open("wb") as stdout, (ATTEMPT / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            process_group_id = os.getpgid(process.pid)
        except OSError as exc:
            process_group_id = None
            identity_error = f"{type(exc).__name__}: {exc}"
        else:
            identity_error = None
        write_json(ATTEMPT / "process-start.json", {
            "schema": "dfb-swift-runtime-expansion-process/v1",
            "pid": process.pid,
            "start_identity": process_identity(process.pid),
            "observed_utc": utc_now(),
            "process_group_id": process_group_id,
            "process_group_id_error": identity_error,
            "argv": argv,
        })

        stop_reason = None
        while process.poll() is None:
            free_bytes = shutil.disk_usage(DISK_ROOT).free
            append_jsonl(ATTEMPT / "disk-observations.jsonl", {
                "observed_utc": utc_now(),
                "free_bytes": free_bytes,
                "minimum_free_bytes": MIN_FREE_BYTES,
                "pid": process.pid,
            })
            if free_bytes < MIN_FREE_BYTES:
                stop_reason = "free-space floor fell below 125 GiB"
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(SAMPLE_SECONDS)

    exit_code = process.wait()
    free_after = shutil.disk_usage(DISK_ROOT).free
    write_json(ATTEMPT / "terminal.json", {
        "schema": "dfb-swift-runtime-expansion-terminal/v1",
        "status": "stopped-resource-floor" if stop_reason else ("success" if exit_code == 0 else "failed"),
        "stop_reason": stop_reason,
        "exit_code": exit_code,
        "started_utc": start_utc,
        "finished_utc": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "pid": process.pid,
        "start_identity": process_identity(process.pid),
        "free_bytes_before": free_before,
        "free_bytes_after": free_after,
        "minimum_free_bytes": MIN_FREE_BYTES,
        "destination_exists": DESTINATION.exists(),
        "analyzer_or_build_invoked": False,
        "package_sha256": package_hash,
        "manifest_sha256": manifest_hash,
    })
    return exit_code if stop_reason is None else 70


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"expansion wrapper failed before/after dispatch: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
