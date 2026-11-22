#!/usr/bin/env python3
"""Run only the compiler's version banner from the verified Swift payload."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path("/Users/dave/.codex/worktrees/cb55/dataflowbench")
ATTEMPT = ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01/version-smoke-01"
PAYLOAD_ROOT = ROOT / (
    "execution-state/timing-swift-repair-20261122-01/expanded/"
    "swift-6.3.3-RELEASE-osx-package.pkg/swift-6.3.3-RELEASE-osx-package.pkg/Payload/usr"
)
SWIFT = PAYLOAD_ROOT / "bin/swift"
PACKAGE_SHA256 = "ee82e57774d6650f94aa06302435d6f44a055b9411698db8ecb85d9a3bcc91d0"
MANIFEST_SHA256 = "f31ae5b23c775e0c69227363a1a0c4e4bf87964f8bcd79b8f9de9d7acd7d4a58"
MIN_FREE_BYTES = 134_217_728_000


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process_identity(pid):
    try:
        result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
                                check=False, capture_output=True, text=True, timeout=5)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ATTEMPT.mkdir(parents=True, exist_ok=False)
    free_before = shutil.disk_usage(ROOT).free
    if free_before < MIN_FREE_BYTES:
        raise RuntimeError(f"free-space floor lost before version smoke: {free_before} bytes")
    argv = [str(SWIFT), "--version"]
    start_utc = utc_now()
    started = time.monotonic()
    write_json(ATTEMPT / "command.json", {
        "schema": "dfb-swift-version-smoke-command/v1",
        "argv": argv,
        "cwd": str(ROOT),
        "started_utc": start_utc,
        "package_sha256": PACKAGE_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "payload_usr_root": str(PAYLOAD_ROOT),
        "qualification": "version banner only; no compiler, typecheck, build, analyzer, or source input",
        "minimum_free_bytes": MIN_FREE_BYTES,
        "free_bytes_before": free_before,
    })
    with (ATTEMPT / "stdout.txt").open("wb") as stdout, (ATTEMPT / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
        write_json(ATTEMPT / "process-start.json", {
            "schema": "dfb-swift-version-smoke-process/v1",
            "pid": process.pid,
            "popen_started_utc": start_utc,
            "system_start_identity": process_identity(process.pid),
            "argv": argv,
        })
        exit_code = process.wait()
    free_after = shutil.disk_usage(ROOT).free
    receipt = {
        "schema": "dfb-swift-version-smoke-terminal/v1",
        "status": "success" if exit_code == 0 else "failed",
        "started_utc": start_utc,
        "finished_utc": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "exit_code": exit_code,
        "pid": process.pid,
        "process_identity_after_wait": process_identity(process.pid),
        "stdout_bytes": (ATTEMPT / "stdout.txt").stat().st_size,
        "stderr_bytes": (ATTEMPT / "stderr.txt").stat().st_size,
        "stdout_sha256": digest(ATTEMPT / "stdout.txt"),
        "stderr_sha256": digest(ATTEMPT / "stderr.txt"),
        "free_bytes_before": free_before,
        "free_bytes_after": free_after,
        "minimum_free_bytes": MIN_FREE_BYTES,
        "analyzer_or_build_invoked": False,
    }
    write_json(ATTEMPT / "terminal.json", receipt)
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"version smoke wrapper failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
