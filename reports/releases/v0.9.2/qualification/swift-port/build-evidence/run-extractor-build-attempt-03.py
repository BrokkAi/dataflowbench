#!/usr/bin/env python3
"""Run one bounded build after restoring source-repository LFS provenance."""
import hashlib
import json
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "codeql-a7057b836bf29767461026718b14d20790b9085f"
BASE_RUNNER = ROOT / "run-extractor-build.py"
OUT = ROOT / "build-attempt-03"
SOURCE_ARCHIVE = ROOT / "codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz"
PICO = ROOT / "downloads/PicoSHA2-27fcf6979298949e8a462e16d09a0351c18fcaf2.tar.zst"
PICO_IN_SOURCE = SOURCE / "swift/third_party/resources/PicoSHA2-27fcf6979298949e8a462e16d09a0351c18fcaf2.tar.zst"
POINTER_INVENTORY = ROOT / "lfs-pointer-inventory.json"
ATTEMPT_02_LOG = ROOT / "build-attempt-02/build.log"
EXPECTED_BASE_RUNNER_SHA256 = "fed79a9da2fb2278f793caed03c35f8dbcee8581b5a7ce599d9b7d45bb918394"
EXPECTED_SOURCE_ARCHIVE_SHA256 = "c737189f5f9f6a89eefabf2e82e6ecf9a2f866c4de2caf1f6407f69d143eae16"
EXPECTED_PICO_SHA256 = "3082b319e6281be54b77b7619a38e5718266fca5e693bc4e23dd76bb17bc6420"
EXPECTED_PICO_SOURCE_POINTER_SHA256 = "f52382e2d97ce9e58049ae6330d5dd09a80e16edd2d77d6fafc1c80ac1b8b9bb"
EXPECTED_INVENTORY_SHA256 = "797eadbe6fded9e8a5d5e4c91ace94f179f39cfcbc6b3c9c47bb0690f7792861"
EXPECTED_LFS_ENDPOINT = "Endpoint=https://github.com/github/codeql.git/info/lfs (auth=none)"
EXPECTED_FAILURE = "no valid endpoints found"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(SOURCE), *args], text=True).strip()


if sha256(BASE_RUNNER) != EXPECTED_BASE_RUNNER_SHA256:
    raise SystemExit("Base bounded runner changed after attempt 01")
if sha256(SOURCE_ARCHIVE) != EXPECTED_SOURCE_ARCHIVE_SHA256:
    raise SystemExit("Immutable CodeQL source archive changed")
if git("rev-parse", "--show-toplevel") != str(SOURCE):
    raise SystemExit("Exact CodeQL source is no longer an isolated Git repository")
if git("remote", "get-url", "origin") != "https://github.com/github/codeql.git":
    raise SystemExit("Official CodeQL origin is missing or changed")
lfs_env = subprocess.check_output(["git", "-C", str(SOURCE), "lfs", "env"], text=True)
if EXPECTED_LFS_ENDPOINT not in lfs_env:
    raise SystemExit("Expected source-bound Git LFS endpoint is not active")
if not PICO.is_file() or not PICO_IN_SOURCE.is_file():
    raise SystemExit("Verified PicoSHA2 LFS asset or materialized source input is missing")
if PICO.stat().st_size != 8159 or sha256(PICO) != EXPECTED_PICO_SHA256:
    raise SystemExit("Acquired PicoSHA2 LFS asset identity mismatch")
if PICO_IN_SOURCE.stat().st_size != 8159 or sha256(PICO_IN_SOURCE) != EXPECTED_PICO_SHA256:
    raise SystemExit("Materialized PicoSHA2 source input identity mismatch")
if sha256(POINTER_INVENTORY) != EXPECTED_INVENTORY_SHA256:
    raise SystemExit("Source LFS pointer inventory changed")
source_pointer = subprocess.check_output(
    [
        "tar",
        "-xOf",
        str(SOURCE_ARCHIVE),
        "codeql-a7057b836bf29767461026718b14d20790b9085f/swift/third_party/resources/PicoSHA2-27fcf6979298949e8a462e16d09a0351c18fcaf2.tar.zst",
    ]
)
if hashlib.sha256(source_pointer).hexdigest() != EXPECTED_PICO_SOURCE_POINTER_SHA256:
    raise SystemExit("Pristine source archive no longer contains the expected PicoSHA2 LFS pointer")
if not ATTEMPT_02_LOG.is_file() or EXPECTED_FAILURE not in ATTEMPT_02_LOG.read_text(errors="replace"):
    raise SystemExit("Attempt 02 does not establish the exact missing-LFS-endpoint failure")

namespace = runpy.run_path(str(BASE_RUNNER))
runner_globals = namespace["main"].__globals__
runner_globals["OUT"] = OUT
original_write_json = runner_globals["write_json"]


def write_json(path, obj):
    if path.name == "command.json":
        obj["attempt_id"] = "03"
        obj["remediation"] = {
            "attempt01_cause": "Local swift-prebuilt-macos override lacked a Bazel repository-root marker",
            "attempt01_fix": "Added an empty REPO.bazel marker, matching Bazel-generated empty repository markers",
            "attempt02_cause": "The isolated exact-source Git repository had no remote, so CodeQL git_lfs_probe.py could not resolve an LFS endpoint for @picosha2",
            "attempt02_fix": "Configured origin as the official github/codeql repository and acquired the exact source-commit LFS object; source code and build checks are unchanged",
            "source_remote": git("remote", "get-url", "origin"),
            "lfs_endpoint": EXPECTED_LFS_ENDPOINT,
            "lfs_pointer_inventory_path": str(POINTER_INVENTORY),
            "lfs_pointer_inventory_sha256": EXPECTED_INVENTORY_SHA256,
            "picosha2_asset_path": str(PICO),
            "picosha2_asset_sha256": EXPECTED_PICO_SHA256,
            "picosha2_asset_size_bytes": 8159,
            "picosha2_pristine_source_pointer_sha256": EXPECTED_PICO_SOURCE_POINTER_SHA256,
            "picosha2_materialized_source_path": str(PICO_IN_SOURCE),
            "source_archive_sha256": EXPECTED_SOURCE_ARCHIVE_SHA256,
            "base_runner_path": str(BASE_RUNNER),
            "base_runner_sha256": EXPECTED_BASE_RUNNER_SHA256,
            "prior_attempt_results": [
                str(ROOT / "build-attempt-01/result.json"),
                str(ROOT / "build-attempt-02/result.json"),
                str(ROOT / "attempt-02-wrapper-preflight-failure.json"),
            ],
        }
    original_write_json(path, obj)


runner_globals["write_json"] = write_json
raise SystemExit(namespace["main"]())
