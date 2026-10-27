#!/usr/bin/env python3
"""Run one separately recorded bounded build after adding Bazel's repo marker."""
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_RUNNER = ROOT / "run-extractor-build.py"
OUT = ROOT / "build-attempt-02"
MARKER = ROOT / "compiler-prebuilt/REPO.bazel"
ATTEMPT_01_LOG = ROOT / "build-attempt-01/build.log"
EXPECTED_MARKER_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EXPECTED_BASE_RUNNER_SHA256 = "fed79a9da2fb2278f793caed03c35f8dbcee8581b5a7ce599d9b7d45bb918394"
EXPECTED_FAILURE = "No MODULE.bazel, REPO.bazel, or WORKSPACE file found"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if sha256(BASE_RUNNER) != EXPECTED_BASE_RUNNER_SHA256:
    raise SystemExit("Base bounded runner changed after attempt 01")
if not MARKER.is_file() or sha256(MARKER) != EXPECTED_MARKER_SHA256:
    raise SystemExit("Expected empty Bazel REPO.bazel marker is missing or changed")
if not ATTEMPT_01_LOG.is_file() or EXPECTED_FAILURE not in ATTEMPT_01_LOG.read_text(errors="replace"):
    raise SystemExit("Attempt 01 does not establish the exact missing-marker failure")

# Bazel's own generated external repository contains empty REPO.bazel markers,
# so an empty file is the repository-boundary marker only; no build rules or
# checks are added, removed, or bypassed.
marker_example = ROOT / "bazel-cache/fc0a27fb3432cf895e26517b46b55445/external/platforms+host_platform+host_platform/REPO.bazel"
if not marker_example.is_file() or marker_example.stat().st_size != 0:
    raise SystemExit("Bazel-generated empty REPO.bazel convention is not present")

namespace = runpy.run_path(str(BASE_RUNNER))
runner_globals = namespace["main"].__globals__
runner_globals["OUT"] = OUT
original_write_json = runner_globals["write_json"]


def write_json(path, obj):
    if path.name == "command.json":
        obj["attempt_id"] = "02"
        obj["remediation"] = {
            "cause": "Bazel rejected the local swift-prebuilt-macos override because it lacked a repository-root marker",
            "change": "Added an empty REPO.bazel marker to compiler-prebuilt; this matches Bazel-generated empty REPO.bazel markers and adds no rules or bypasses",
            "marker_path": str(MARKER),
            "marker_sha256": EXPECTED_MARKER_SHA256,
            "architecture_contract": "swift/rules.bzl transitions macOS extractor compilation/linking to x86_64; source-bound Swift libraries and stock CodeQL 2.27.2 osx64 extractor are x86_64",
            "base_runner_path": str(BASE_RUNNER),
            "base_runner_sha256": EXPECTED_BASE_RUNNER_SHA256,
            "prior_attempt_result": str(ROOT / "build-attempt-01/result.json"),
        }
    original_write_json(path, obj)


runner_globals["write_json"] = write_json
raise SystemExit(namespace["main"]())
