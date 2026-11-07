#!/usr/bin/env python3
"""Prepare and verify the v0.9.2 Bifrost 0.15.1 target.

This fixed successor wrapper loads the reviewed C5 implementation in an
isolated module namespace. Only the target's enumerated identity, evidence
paths, schema names, and verified context digests vary; execution policy and
qualification semantics remain in the shared implementation.

The wrapper refuses to run until its fixed, tracked target-profile JSON binds
the actual acquisition, controls, qualification, and optimized runner build.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE_REL = "scripts/bifrost_v0144_benchmark.py"
WRAPPER_SOURCE_REL = "scripts/bifrost_v0151_benchmark.py"
TEST_SOURCE_REL = "scripts/test_bifrost_v0151_benchmark.py"
PROFILE_REL = "reports/releases/v0.9.2/qualification/bifrost-v0151-01/target-profile.json"
PROFILE_SCHEMA = "dataflowbench-v0.9.2-bifrost-v0151-target-profile/v1"

PINNED_IDENTITY = MappingProxyType({
    "target_id": "bifrost-v0151-01",
    "version": "0.15.1",
    "report_version": "bifrost 0.15.1",
    "build_identity": "90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69",
    "binary_sha256": "00b279126297d5e9f7805390799493e915eaf4a2d5940dc3e755138a577a6df9",
    "archive_sha256": "d7ca6901787455bdabf18ec9c36453032a9be354180e54b5ff183b1e4bf83038",
    "catalog_sha256": "f9d3b4efcf20e0ca8e8a976d6524556f114f4a4ccab3f4b0cc761f0b9248d206",
    "public_tag_commit": "04fdd17d2606d13a7a5f13b012bfbe3ad9729d1e",
})

PROFILE_KEYS = frozenset({
    "schema", "identity", "evidence_sha256", "runner_binary_bytes",
})
IDENTITY_KEYS = frozenset({
    "target_id", "version", "report_version", "build_identity", "binary_sha256",
    "archive_sha256", "catalog_sha256", "public_tag_commit",
})
EVIDENCE_SHA_KEYS = frozenset({
    "acquisition_receipt", "qualification", "control_review", "independent_review",
    "capture_manifest", "capture_qualification", "runner_binary",
    "runner_build_receipt", "runner_build_inputs", "runner_build_stdout",
    "runner_build_stderr",
})
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class TargetProfileError(ValueError):
    """The fixed v0.15.1 profile is missing, malformed, or misbound."""


V0151_OVERRIDES = {
    "TARGET_HELP_DESCRIPTION": (
        "Prepare, execute, and independently verify the v0.9.2 Bifrost 0.15.1 target.\n\n"
        "This fixed successor reuses the reviewed C5 execution implementation in an isolated "
        "module namespace. It preserves the 20-group roster, budgets, resource gates, "
        "historical ledger semantics, and known-limits qualification boundary."
    ),
    "TARGET_ID": "bifrost-v0151-01",
    "CONTRACT_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target/v1",
    "SERIES": 4,
    "SERIES_LABEL": "series-04",
    "CONTRACT_REL": "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json",
    "PROGRESS_REL": "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/progress.jsonl",
    "SUMMARY_REL": "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/series-summary.json",
    "INVOCATIONS_REL": "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/invocations",
    "QUALIFICATION_DEFAULT": "reports/releases/v0.9.2/qualification/bifrost-v0151-01/bifrost-release-01.json",
    "CONTROL_REVIEW_DEFAULT": "reports/releases/v0.9.2/qualification/bifrost-v0151-01/bifrost-review-01.json",
    "INDEPENDENT_REVIEW_DEFAULT": "reports/releases/v0.9.2/qualification/bifrost-v0151-01/independent-review-v0151-01.json",
    "CONTROL_CAPTURE_DEFAULT": "reports/releases/v0.9.2/qualification/bifrost-v0151-01/controls-attempt-01",
    "HUMAN_AUTHORIZATION_DEFAULT": "reports/releases/v0.9.2/qualification/bifrost-v0151-01/human-authorization-01.json",
    "BIFROST_RECEIPT_DEFAULT": "reports/releases/v0.9.2/acquisition/bifrost-v0151-01/acquisition-receipt.json",
    "BIFROST_PATH_DEFAULT": (
        "execution-state/v092/tools/bifrost0151/extracted/"
        "bifrost-v0.15.1-universal-apple-darwin/bifrost"
    ),
    "RUNNER_PATH_DEFAULT": "execution-state/v092/builds/bifrost0151-01-target/release/dataflowbench",
    "RUNNER_BUILD_RECEIPT": "reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/receipt.json",
    "RUNNER_BUILD_INPUTS": "reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/source-inputs.json",
    "RUNNER_BUILD_STDOUT": "reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/stdout",
    "RUNNER_BUILD_STDERR": "reports/releases/v0.9.2/validation/bifrost-v0151-release-build-01/stderr",
    "RUNNER_CARGO_TARGET_DIR": "execution-state/v092/builds/bifrost0151-01-target",
    "TARGET_DRIVER_SOURCE_REL": WRAPPER_SOURCE_REL,
    "TARGET_TEST_SOURCE_REL": TEST_SOURCE_REL,
    "CORE_SOURCE_REL": CORE_SOURCE_REL,
    "PROFILE_SOURCE_REL": PROFILE_REL,
    "LEDGER_PREFIX_LINES": 131,
    "LEDGER_PREFIX_SHA256": "2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199",
    "BIFROST_VERSION": PINNED_IDENTITY["version"],
    "BIFROST_REPORT_VERSION": PINNED_IDENTITY["report_version"],
    "BIFROST_BUILD_IDENTITY": PINNED_IDENTITY["build_identity"],
    "BIFROST_BINARY_SHA256": PINNED_IDENTITY["binary_sha256"],
    "BIFROST_ARCHIVE_SHA256": PINNED_IDENTITY["archive_sha256"],
    "BIFROST_CONTROL_REVIEW_SCHEMA": "v092-bifrost-v0151-control-review/v1",
    "INDEPENDENT_REVIEW_SCHEMA": "v092-bifrost-v0151-independent-review/v1",
    "REVIEW_IMPLEMENTATION_PATH": (
        "reports/releases/v0.9.2/qualification/bifrost-v0151-01/"
        "review-bifrost-v0151-01.py"
    ),
    "CONTROL_COMPARISON_DIAGNOSTIC_PATH": (
        "reports/releases/v0.9.2/qualification/bifrost-v0151-01/"
        "control-comparison-diagnostic-01.json"
    ),
    "PIN_PROFILE_PATH": "adapters/pins/v0.9.2-bifrost-v0151.json",
    "PIN_PROFILE_NATIVE_EVIDENCE_DIRECTORY": "reports/releases/v0.9.2/qualification/bifrost-v0151-01",
    "ATTEMPT_RECEIPT_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target-attempt/v1",
    "PROGRESS_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target-progress/v1",
    "INVOCATION_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target-invocation/v1",
    "SERIES_SUMMARY_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target-series-summary/v1",
    "RECONCILIATION_SCHEMA": "dataflowbench-v0.9.2-bifrost-v0151-target-reconciliation/v1",
    "NATIVE_EVIDENCE_PATHS": {
        "help_stdout": "reports/releases/v0.9.2/acquisition/bifrost-v0151-01/help.stdout.txt",
        "controls_identity_version_stdout": (
            "reports/releases/v0.9.2/qualification/bifrost-v0151-01/"
            "controls-attempt-01/stdout/identity-version.txt"
        ),
        "controls_identity_build_stdout": (
            "reports/releases/v0.9.2/qualification/bifrost-v0151-01/"
            "controls-attempt-01/stdout/identity-build.txt"
        ),
        "controls_catalog_list_stdout": (
            "reports/releases/v0.9.2/qualification/bifrost-v0151-01/"
            "controls-attempt-01/stdout/catalog-list-policies.txt"
        ),
        "pin_profile": "adapters/pins/v0.9.2-bifrost-v0151.json",
    },
}

PROFILE_EVIDENCE_TARGET_FIELDS = MappingProxyType({
    "acquisition_receipt": "BIFROST_RECEIPT_SHA256",
    "qualification": "QUALIFICATION_SHA256",
    "control_review": "CONTROL_REVIEW_SHA256",
    "independent_review": "INDEPENDENT_REVIEW_SHA256",
    "capture_manifest": "CAPTURE_MANIFEST_SHA256",
    "capture_qualification": "CAPTURE_QUALIFICATION_SHA256",
    "runner_binary": "RUNNER_BINARY_SHA256",
    "runner_build_receipt": "RUNNER_BUILD_RECEIPT_SHA256",
    "runner_build_inputs": "RUNNER_BUILD_INPUTS_SHA256",
    "runner_build_stdout": "RUNNER_BUILD_STDOUT_SHA256",
    "runner_build_stderr": "RUNNER_BUILD_STDERR_SHA256",
})


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise TargetProfileError(f"duplicate target-profile JSON key: {key}")
        result[key] = value
    return result


def validate_profile_document(value: object) -> dict:
    """Validate the fixed post-control profile format without accepting overrides."""
    if not isinstance(value, dict) or set(value) != PROFILE_KEYS:
        raise TargetProfileError("v0.15.1 target profile has missing or unapproved top-level fields")
    if value.get("schema") != PROFILE_SCHEMA:
        raise TargetProfileError("v0.15.1 target profile schema is wrong")
    identity = value.get("identity")
    if not isinstance(identity, dict) or set(identity) != IDENTITY_KEYS:
        raise TargetProfileError("v0.15.1 target identity is incomplete or contains unapproved fields")
    expected = dict(PINNED_IDENTITY)
    for key, expected_value in expected.items():
        if identity.get(key) != expected_value:
            raise TargetProfileError(f"v0.15.1 pinned identity mismatch: {key}")
    binary_bytes = value.get("runner_binary_bytes")
    if type(binary_bytes) is not int or not 0 < binary_bytes <= 512 * 1024**2:
        raise TargetProfileError("v0.15.1 runner binary byte count is missing or outside the fixed bound")
    evidence = value.get("evidence_sha256")
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_SHA_KEYS:
        raise TargetProfileError("v0.15.1 evidence digest roster is incomplete or contains unapproved fields")
    for name, digest in evidence.items():
        if not isinstance(digest, str) or not HEX256.fullmatch(digest):
            raise TargetProfileError(f"v0.15.1 profile digest is missing or malformed: {name}")
    return value


def target_profile_values(value: object, core_module) -> object:
    """Create only the wrapper's fixed v0.15.1 data profile."""
    document = validate_profile_document(value)
    evidence = document["evidence_sha256"]
    overrides = dict(V0151_OVERRIDES)
    overrides.update({
        "BIFROST_CATALOG_SHA256": PINNED_IDENTITY["catalog_sha256"],
        "PUBLIC_BIFROST_TAG_COMMIT": PINNED_IDENTITY["public_tag_commit"],
        "RUNNER_BINARY_BYTES": document["runner_binary_bytes"],
    })
    for evidence_key, target_field in PROFILE_EVIDENCE_TARGET_FIELDS.items():
        overrides[target_field] = evidence[evidence_key]
    profile = core_module.make_target_profile(overrides)
    # Do not return caller-owned containers that could mutate the configured profile.
    return profile


def _read_profile(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise TargetProfileError(f"required tracked target profile is missing or unsafe: {path}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except TargetProfileError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TargetProfileError(f"cannot read the fixed v0.15.1 target profile: {exc}") from exc
    return validate_profile_document(value)


def _load_core_module():
    source = ROOT / CORE_SOURCE_REL
    if source.is_symlink() or not source.is_file():
        raise TargetProfileError(f"shared C5 implementation is missing or unsafe: {source}")
    source_bytes = source.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    module_name = f"bifrost_v0151_c5_core_{digest[:16]}"
    existing = sys.modules.get(module_name)
    if existing is not None:
        if getattr(existing, "__verified_source_sha256__", None) != digest:
            raise TargetProfileError("cached shared C5 module lacks its exact source binding")
        return existing
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise TargetProfileError("cannot load the shared C5 implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        exec(compile(source_bytes, str(source), "exec"), module.__dict__)
        module.__verified_source_sha256__ = digest
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_target_profile(core_module=None):
    """Read only the one fixed profile path; CLI callers cannot redirect it."""
    core = core_module or _load_core_module()
    path = ROOT / PROFILE_REL
    try:
        tracked = core._git(ROOT, "ls-files", "--error-unmatch", "--", PROFILE_REL).strip()
    except (OSError, ValueError, core.BenchmarkError) as exc:
        raise TargetProfileError("v0.15.1 profile must be tracked before the execution source commit") from exc
    if tracked != PROFILE_REL:
        raise TargetProfileError("v0.15.1 profile must be tracked before the execution source commit")
    document = _read_profile(path)
    return target_profile_values(document, core)


def run(argv: Sequence[str] | None = None) -> int:
    core = _load_core_module()
    profile = load_target_profile(core)
    try:
        core.configure_target_profile(profile)
        return core._main(argv)
    except core.BenchmarkError as exc:
        raise TargetProfileError(str(exc)) from exc


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (TargetProfileError, OSError, ValueError) as exc:
        raise SystemExit(f"C5 Bifrost 0.15.1 target refused: {exc}")
