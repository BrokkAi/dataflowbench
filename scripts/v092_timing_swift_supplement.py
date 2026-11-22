#!/usr/bin/env python3
"""One-group, fail-closed Joern Swift supplement for v0.9.2 timing evidence.

This controller adds exactly one fresh Joern Swift common-108 attempt to the
retained 95-command campaign. It never changes or repairs the historical
campaign, and successful execution remains unqualified timing evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "20261122-08"
FAILED_PREPARATION_REPORT = "reports/timing/v0.9.2/20261122-03"
FAILED_PREPARATION_SOURCE = "execution-state/timing-v092-20261122-03/sources/joern-swift-common108"
FAILED_PREPARATION_INVENTORY = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/campaign-03-preparation-failure-inventory-01.json"
FAILED_PREPARATION_INVENTORY_SHA256 = "2674c28d4c25e72b531b94d8434a6a10ec3c0bff2d26ca88e8c9a9b9227d3195"
FAILED_PREPARATION_04_REPORT = "reports/timing/v0.9.2/20261122-04"
FAILED_PREPARATION_04_SOURCE = "execution-state/timing-v092-20261122-04/sources/joern-swift-common108"
FAILED_PREPARATION_04_INVENTORY = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/campaign-04-preparation-failure-inventory-01.json"
FAILED_PREPARATION_04_INVENTORY_SHA256 = "bd23d37d473e795a3dc6b71b340488e259901092d74669b86762ca1c6695a40b"
FAILED_PREPARATION_05_REPORT = "reports/timing/v0.9.2/20261122-05"
FAILED_PREPARATION_05_SOURCE = "execution-state/timing-v092-20261122-05/sources/joern-swift-common108"
FAILED_PREPARATION_05_INVENTORY = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/campaign-05-preparation-failure-inventory-01.json"
FAILED_PREPARATION_05_INVENTORY_SHA256 = "773abdb61d283134552e9ee8adfa0869cb207ed20a8b4df8784bd502b8c3f8bc"
FAILED_WRAPPER_REPORT = "reports/timing/v0.9.2/20261122-06"
FAILED_WRAPPER_SOURCE = "execution-state/timing-v092-20261122-06/sources/joern-swift-common108"
FAILED_WRAPPER_INVENTORY = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/campaign-06-invocation-failure-inventory-01.json"
FAILED_WRAPPER_INVENTORY_SHA256 = "70b093fb3356773580560aa9937994e1f3ec5a264684c5b11b6646657ee100a6"
LAUNCHER_RECOVERY_PATH = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/launcher-path-recovery-01.json"
LAUNCHER_RECOVERY_SHA256 = "5f425e249985e19b2ebb468c711dbe7e6cd56e4d870941d4ad038823f9d03b07"
LAUNCHER_CONTROL_VERSION_PATH = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/qualification/control-attempt-01/version.command.json"
LAUNCHER_CONTROL_VERSION_SHA256 = "f6c8d478e42fda83f5370141458b890f1992842510c17bc15a0fb6cb60c74331"
LAUNCHER_SMOKE_ROOT = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/launcher-smoke-01"
LAUNCHER_SMOKE_TERMINAL_PATH = f"{LAUNCHER_SMOKE_ROOT}/terminal.json"
LAUNCHER_SMOKE_TERMINAL_SHA256 = "40f1521eac678322a00082689fbe166deb1e674704b16163b1cbc89f6513a296"
LAUNCHER_SMOKE_START_PATH = f"{LAUNCHER_SMOKE_ROOT}/start.json"
LAUNCHER_SMOKE_START_SHA256 = "97692d870317a416efa84f69b2f08e3f88afe30de680db0b7c7ec6e39cf2db5d"
LAUNCHER_SMOKE_STDOUT_PATH = f"{LAUNCHER_SMOKE_ROOT}/stdout.txt"
LAUNCHER_SMOKE_STDOUT_SHA256 = "a1eeb9de9d8ce7866b0838822371298e1bf2b715c4fabf066bdaab031d8f5cda"
LAUNCHER_SMOKE_STDERR_PATH = f"{LAUNCHER_SMOKE_ROOT}/stderr.txt"
LAUNCHER_SMOKE_STDERR_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
FAILED_WRAPPER_VERSION_DIR = (
    f"{FAILED_WRAPPER_SOURCE}/reports/raw/joern-common-v2/current108-v092-02/identity"
)
FAILED_CAPABILITY_REPORT = "reports/timing/v0.9.2/20261122-07"
FAILED_CAPABILITY_SOURCE = "execution-state/timing-v092-20261122-07/sources/joern-swift-common108"
FAILED_CAPABILITY_INVENTORY = (
    "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/"
    "campaign-07-capability-failure-inventory-01.json"
)
FAILED_CAPABILITY_INVENTORY_SHA256 = "fdcd2cbf27491bfce5b4af20f274818fb640112b6e8a4faa57ef2ec0ceb4df08"
FAILED_CAPABILITY_INVENTORY_FILE_COUNT = 4675
FAILED_CAPABILITY_INVENTORY_TOTAL_BYTES = 114269184
FAILED_CAPABILITY_VERSION_DIR = (
    f"{FAILED_CAPABILITY_SOURCE}/reports/raw/joern-common-v2/current108-v092-02/identity"
)
CAPABILITY_RECOVERY_AUTHORIZATION_PATH = "docs/latency-v092-20261122-capability-recovery.md"
CAPABILITY_RECOVERY_AUTHORIZATION_SHA256 = "eebbd44140a4548b6b67604f74c172fe53baee9a663ff0d3a8388a652440d6dc"
CAPABILITY_SOURCE_PATH = "adapters/joern/swift-common-v2/plan-v090-01/plan.json"
CAPABILITY_SOURCE_SHA256 = "14dde3a42a90c19d5c4eb696688f19cf31463a9d38bf153c227d0b82097604e6"
CAPABILITY_V3_RUNNER_PATH = "scripts/joern_normal_runner_v092_capability.py"
CAPABILITY_V3_CLI_PATH = "scripts/run-joern-common-v092-capability.py"
CAPABILITY_V3_QUALIFIER_PATH = "scripts/v092_capability_qualification.py"
CAPABILITY_V3_ADMISSION_PATH = "scripts/joern_diagnostic_admission_v092_capability.py"
CAPABILITY_V3_REPORTER_PATH = "scripts/joern_normal_reports_v092_capability.py"
GNU_READLINK_LOOKUP_PATH = "/opt/homebrew/bin/greadlink"
GNU_READLINK_REAL_PATH = "/opt/homebrew/Cellar/coreutils/9.8/bin/greadlink"
GNU_READLINK_SYMLINK_TARGET = "../Cellar/coreutils/9.8/bin/greadlink"
GNU_READLINK_SHA256 = "1b0f8ddb83bb76e9dd395be61326d7fe2e45a6093e88ae544f94dd6524a94383"
GNU_READLINK_SIZE_BYTES = 76680
GNU_READLINK_MODE = 365
FAILED_PREPARATION_PROCESS_HELPER = "scripts/v092_closed_process_identity.py"
DIAGNOSTIC_AUTHORIZATION_PATH = "docs/latency-v092-20261122-diagnostic-continuation.md"
DIAGNOSTIC_AUTHORIZATION_SHA256 = "2e213648637bf897639a8cab6ee92f3533ba2be2c183c28d599337bc93f2d6a8"
LAUNCHER_RECOVERY_AUTHORIZATION_PATH = "docs/latency-v092-20261122-launcher-recovery.md"
LAUNCHER_RECOVERY_AUTHORIZATION_SHA256 = "bad56349e0a30903519a2ac165e7fd3bc75ed6749e238b3377d351c55adf3c9a"
UNSUPPORTED_PROVENANCE_AUTHORIZATION_PATH = "docs/latency-v092-20261122-unsupported-provenance.md"
UNSUPPORTED_PROVENANCE_AUTHORIZATION_SHA256 = "2d5b8ceef68603a08e33be2f22edd39910bf7a1c1eca30c0e898b075bb62fed1"
PROJECTION_RECOVERY_AUTHORIZATION_PATH = "docs/latency-v092-20261122-projection-recovery.md"
PROJECTION_RECOVERY_AUTHORIZATION_SHA256 = "b914e521b198bf1e17b11daf2dd2c77737646722e9dc60ea2a095f8112db8654"
PARENT_GROUP_PATH = (
    "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-runtime-20261114-01/"
    "jvm/jdk-21.0.8-tem/bin:/opt/homebrew/bin:/usr/local/bin:/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin"
)
QUIESCENT_SERVICE_RECOGNITION = (
    "legacy.Observer exact bifrost --mcp/--lsp argv, unchanged PID/birth/argv/cumulative-CPU, "
    "zero sampled CPU and no descendants/v1"
)
GROUP_ID = "joern-swift-common108"
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
MODEL_LIMIT_DECISION_ID = "joern-swift-common108-endpoint-identity-gap-2026-10-20"
BASE_PLAN_PATH = "reports/timing/v0.9.2/20261122-02/qualified-plan-02.json"
BASE_PLAN_SHA256 = "cf703f9cc6abe256a44b82af9fd6ad6a7195e44bf0e6b1972a326d8b479c49d9"
BASE_TERMINAL_PATH = "reports/timing/v0.9.2/20261122-02/campaign-terminal.json"
BASE_TERMINAL_SHA256 = "08de3bb1e12a743786bf81bf95b8d636ec27d9bd7e7284c33e3b33eb531365cb"
BASE_INVENTORY_PATH = "reports/timing/v0.9.2/20261122-02/capture-evidence-inventory-01.json"
BASE_INVENTORY_SHA256 = "31ba9d8691f85e7f5e28f6d92f973a6be4b5df529fb28dac9f793b77e8ff193d"
BASE_AUDIT_PATH = "reports/timing/v0.9.2/reconciliation-20261122-01/semgrep-warm-audit-02/validation-receipt.json"
BASE_AUDIT_SHA256 = "14dd96bea7dd8ee228eb2ea29c4c715ab404a1c507ee90300542db5a8512cfd9"
QUALIFIED_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-03/execution-plan-qualified.json"
PENDING_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-03/qualification-pending-plan-04.json"
PENDING_PLAN_SHA256 = "9ad9bf8429e159dd2bfc0553d03277ba8fe13954ea865d0bc87c6eeadb964959"
CONTROL_PLAN_PATH = (
    "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/"
    "capability-qualification/control-plan-04.json"
)
CONTROL_PLAN_SHA256 = "58bd2876c55cdc35c1b3eb32d808339365587444d736b4dbbfa4f39276182535"
QUALIFICATION_ROOT = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/capability-qualification"
PREPARATION_ROOT = "reports/timing/v0.9.2/preparation-20261122-joern-swift-01"
RESOURCE_PROFILE_PATH = f"{PREPARATION_ROOT}/resource-observer-profile-01.json"
RESOURCE_PROFILE_SHA256 = "3c183f20e8bce13c8ec36f872ce743d7319097c4a562662f0813352c4e0d3076"
POST_PROFILE_RETAINED_ADDITIONS = ({
    "path": "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01/public-artifact-check-01.json",
    "sha256": "52b328d4ce0b07a9d291c6e27ad8bea131a982d6b00f2daaf73288e7186b64fa",
    "size_bytes": 844,
},)
RESOURCE_OBSERVER_METHOD = "immutable-parent-and-preparation-baseline-plus-live-current-paths/v1"
RESOURCE_OWNER_RECEIPT_PATH = f"{PREPARATION_ROOT}/post-control-ownership-01.json"
RESOURCE_OWNER_RECEIPT_SHA256 = "3633f11344edaff0e7b800648af42a597c418a208e7c11ea8018a66975ab23e6"
PORTABILITY_RECEIPT_PATH = f"{PREPARATION_ROOT}/root-portability-preflight-02.json"
PORTABILITY_RECEIPT_SHA256 = "ed7c7e769e577dedbd9a077d593f4475c8c61eb096bfa429a8898cfe0c3877b2"
QUALIFICATION_WORK_ROOT = "execution-state/timing-joern-swift-qualification-20261122-01"
QUALIFICATION_CONTROL_SCRATCH = f"{QUALIFICATION_ROOT}/control-attempt-01"
PRIOR_CONTROL_RUN_PATH = "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-02/run.json"
PRIOR_REGISTRATION_ARCHIVE_PATH = "reports/releases/v0.9.2/qualification/joern-swift-common108/control-attempt-02-registration-archive-01/archive.json"
PRIOR_CONTROL_PLAN_PATH = "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-02.json"
PORTABILITY_SOURCE_PATH = "execution-state/timing-joern-swift-portability-preflight-20261122-01/source"
CAPABILITY_PORTABILITY_SOURCE = "execution-state/timing-joern-capability-portability-20261122-01/source"
CAPABILITY_PORTABILITY_REPORT = f"{PREPARATION_ROOT}/capability-portability-preflight-01.json"
CAPABILITY_QUALIFICATION_WORK_ROOT = "execution-state/timing-joern-capability-qualification-20261122-01"
CAPABILITY_CONTROL_OUTPUT = f"{QUALIFICATION_ROOT}/control-attempt-03"
CAPABILITY_CONTROL_SUPERVISION = f"{PREPARATION_ROOT}/capability-control-supervision-03"
CAPABILITY_POST_CONTROL_OWNERSHIP = f"{PREPARATION_ROOT}/capability-post-control-ownership-01.json"
CAPABILITY_PREPARED_SOURCE_PROCEDURE = f"{PREPARATION_ROOT}/procedures/capability_check_prepared_source.py"
CAPABILITY_CONTROL_PROCEDURE = f"{PREPARATION_ROOT}/procedures/capability_run_controls_supervised.py"
CAPABILITY_FINALIZE_PROCEDURE = f"{PREPARATION_ROOT}/procedures/capability_finalize_qualification.py"
CAPABILITY_OWNERSHIP_PROCEDURE = f"{PREPARATION_ROOT}/procedures/capability_audit_controls_ownership.py"
RESOURCE_CAMPAIGN_IDS = ("20261115-01", "20261121-01", "20261122-01", "20261122-02")
RESOURCE_PARENT_CHECKPOINT_PATH = "reports/timing/v0.9.2/20261122-02/parent-checkpoint-01.json"
RESOURCE_PARENT_CHECKPOINT_SHA256 = "91da67df63ef979e5436117806811ee9f938c56235395536584cb950d7782f63"
PLAN_PATH = f"reports/timing/v0.9.2/{CAMPAIGN_ID}/supplement-plan-01.json"
REPORT_ROOT = f"reports/timing/v0.9.2/{CAMPAIGN_ID}"
WORK_ROOT = f"execution-state/timing-v092-{CAMPAIGN_ID}"
SOURCE_RELATIVE = f"{WORK_ROOT}/sources/{GROUP_ID}"
OUTPUT_RELATIVE = "reports/raw/joern-common-v2/current108-v092-03"
OUTPUT_ARGUMENT = f"{OUTPUT_RELATIVE}"
NORMAL_AUDIT_RELATIVE = f"{OUTPUT_RELATIVE}/normal/audit.json"
DERIVED_RELATIVE = f"{REPORT_ROOT}/derived/{GROUP_ID}"
ATTEMPT_RELATIVE = f"{REPORT_ROOT}/attempts/{GROUP_ID}/attempt-01"
RESOURCE_BASELINE_PATH = f"{REPORT_ROOT}/resource-baseline-01.json"
GROUP_TIMEOUT_SECONDS = 1368
MAX_CAMPAIGN_WALL_SECONDS = 48 * 60 * 60
QUIET_SECONDS = 300
QUIET_IDLE_PERCENT = 90.0
MAX_SAMPLE_GAP_SECONDS = 45.0
SAMPLE_INTERVAL_SECONDS = 30.0
CASE_COUNT = 108
REPORT_PARTITION_COUNT = 5
GIB = 1024**3
V01_EXECUTION_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"

# These are additive provenance/runtime bindings only. No old configuration
# path may be removed or re-bound. The final candidate plan must declare this
# same exact set after the qualification owner freezes the v03 plan.
APPROVED_CONFIGURATION_ADDITIONS: tuple[str, ...] = (
    "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
    "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/joern.json",
    "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/java.json",
    "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated.json",
    "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated-receipt.json",
    "reports/timing/v0.9.2/preparation-20261122-swift-01/manifest-verification.json",
    "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests-receipt-v2.json",
    CAPABILITY_V3_RUNNER_PATH,
    CAPABILITY_V3_CLI_PATH,
    CAPABILITY_V3_QUALIFIER_PATH,
    CAPABILITY_V3_ADMISSION_PATH,
    CAPABILITY_V3_REPORTER_PATH,
)

HELPER_PATHS = (
    "scripts/execute-release-v092.py",
    "scripts/v092_timing_campaign.py",
    "scripts/v092_timing_host.py",
    "scripts/v092_timing_qualified_campaign.py",
    CAPABILITY_V3_RUNNER_PATH,
    CAPABILITY_V3_CLI_PATH,
    "scripts/joern_normal_reports_v092.py",
    "scripts/joern_normal_reports_v092_projection.py",
    CAPABILITY_V3_QUALIFIER_PATH,
    "scripts/v092_qualification.py",
    "scripts/joern_diagnostic_admission_v092.py",
    CAPABILITY_V3_ADMISSION_PATH,
    CAPABILITY_V3_REPORTER_PATH,
    CAPABILITY_PREPARED_SOURCE_PROCEDURE,
    CAPABILITY_CONTROL_PROCEDURE,
    CAPABILITY_FINALIZE_PROCEDURE,
    CAPABILITY_OWNERSHIP_PROCEDURE,
    "scripts/v092_timing_swift_supplement.py",
    "scripts/v092_disk_guard.py",
    "scripts/swift_v2_scored_process.py",
    FAILED_PREPARATION_PROCESS_HELPER,
)

# Paths are exact A28 process identities. Only these complete comm paths are
# ignored by the new admission assessment; aggregate CPU idle and raw process
# samples are never altered, and descendants are never inherited as tolerated.
TOLERATED_COMM_PATHS = (
    "/System/Library/Frameworks/Contacts.framework/Support/contactsd",
    "/System/Library/PrivateFrameworks/ContactsDonation.framework/Versions/A/Support/contactsdonationagent",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/corespotlightd",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/managedcorespotlightd",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mds",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mds_stores",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mdworker_shared",
    "/usr/libexec/spotlightknowledged.updater",
    "/System/Library/Frameworks/Virtualization.framework/Versions/A/XPCServices/com.apple.Virtualization.VirtualMachine.xpc/Contents/MacOS/com.apple.Virtualization.VirtualMachine",
)


def _diagnostic_admission_policy() -> dict:
    return {
        "schema": "v092-swift-supplement-diagnostic-background-admission/v1",
        "mode": "diagnostic-background-admission",
        "required_seconds": 0,
        "settled_seconds_minimum_for_certification": QUIET_SECONDS,
        "aggregate_cpu_idle_percent_minimum_for_certification": QUIET_IDLE_PERCENT,
        "aggregate_cpu_idle_is_dispatch_gate": False,
        "dispatch_requires_complete_snapshot": True,
        "dispatch_rejects_non_tolerated_heavy_processes": True,
        "dispatch_rejects_significant_external_cpu": True,
        "significant_external_cpu_rule": "non-tolerated external CPU >= logical CPUs * 10.0 percent",
        "maximum_sample_gap_seconds": MAX_SAMPLE_GAP_SECONDS,
        "maximum_final_sample_to_spawn_seconds": MAX_SAMPLE_GAP_SECONDS,
        "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
        "missing_predispatch_observation_policy": "wait-for-next-complete-snapshot",
        "tolerated_comm_paths": list(TOLERATED_COMM_PATHS),
        "matching": "exact-full-comm-path-only",
        "quiescent_service_recognition": QUIESCENT_SERVICE_RECOGNITION,
        "aggregate_cpu_adjusted": False,
        "raw_aggregate_idle_preserved": True,
        "settled_quiet_window_established": False,
        "active_cpu_policy": "record-and-continue",
        "missing_active_observation_policy": "record-and-continue",
        "original_a24_settled_qualification_eligible": False,
        "publication_eligible": False,
    }

IDENTITY_FIELDS = [
    "tool", "tool_version", "tool_build_identity", "configuration_hash",
    "fixture_revision", "cold_or_warm", "adapter_version", "schema_version",
]


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError(f"expected a JSON object: {path}")
    return value


def _reference(root: Path, relative: str) -> dict:
    path = _repo_file(root, relative)
    return {"path": relative, "sha256": sha(path)}


def _repo_file(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or "\\" in relative):
        raise RuntimeError(f"invalid repository-relative path: {relative!r}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise RuntimeError(f"unsafe repository-relative path: {relative!r}")
    target = root.joinpath(*pure.parts)
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"repository input path traverses a symlink: {relative}")
    if not target.is_file():
        raise RuntimeError(f"repository input is missing or not a regular file: {relative}")
    if not target.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise RuntimeError(f"repository input escapes the repository: {relative}")
    return target


def _validate_reference(root: Path, reference: object) -> Path:
    if (not isinstance(reference, dict) or set(reference) != {"path", "sha256"}
            or not isinstance(reference.get("sha256"), str)
            or len(reference["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in reference["sha256"])):
        raise RuntimeError("repository reference must contain exactly path and lowercase sha256")
    path = _repo_file(root, reference["path"])
    if sha(path) != reference["sha256"]:
        raise RuntimeError(f"bound repository file changed: {reference['path']}")
    return path


def validate_projection_only(original: dict, derived: dict, configuration_hash: str) -> None:
    """Require the existing metadata projection to add exactly one field."""
    if "configuration_hash" in original:
        raise RuntimeError("raw normalized report already contains configuration_hash")
    expected = dict(original, configuration_hash=configuration_hash)
    if derived != expected:
        raise RuntimeError("derived Joern report differs beyond configuration_hash")


def _validate_case_artifact_refs(source: Path, raw_path: Path, raw: dict,
                                 disposition: str) -> dict:
    """Validate and retain case-level timing costs plus raw proof references."""
    duration = raw.get("duration_ms")
    if type(duration) is not int or duration < 0:
        raise RuntimeError(f"invalid Joern case duration: {raw.get('case_id')}")
    elapsed = raw.get("total_elapsed_seconds")
    if (type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0
            or duration != int(elapsed * 1000)):
        raise RuntimeError(f"Joern case duration does not match its recorded elapsed cost: {raw.get('case_id')}")
    commands = raw.get("commands")
    outputs = raw.get("native_outputs")
    if not isinstance(commands, list) or not isinstance(outputs, list):
        raise RuntimeError(f"Joern case command/native output references are malformed: {raw.get('case_id')}")

    command_refs = []
    phase_order = {"typecheck": 0, "frontend": 1, "query": 2}
    prior_phase = -1
    observed_phases = []
    for reference in commands:
        command_path = _validate_reference(source, reference)
        if command_path.parent != raw_path.parent or not command_path.name.endswith(".command.json"):
            raise RuntimeError(f"Joern phase command escaped its case output directory: {raw.get('case_id')}")
        phase = command_path.name.removesuffix(".command.json")
        if phase not in phase_order or phase_order[phase] <= prior_phase:
            raise RuntimeError(f"Joern phase command order/identity is invalid: {raw.get('case_id')}")
        prior_phase = phase_order[phase]
        observed_phases.append(phase)
        command = _read_json(command_path)
        if (command.get("phase_id") != phase or command.get("role") != "analysis"
                or command.get("cwd") != str(raw_path.parent)
                or not isinstance(command.get("argv"), list) or not command["argv"]
                or any(not isinstance(arg, str) or not arg for arg in command["argv"])
                or type(command.get("exit_status")) is not int
                or type(command.get("timed_out")) is not bool
                or command.get("cleanup_status") != "tracked-processes-stopped"
                or type(command.get("elapsed_seconds")) not in (int, float)
                or command["elapsed_seconds"] < 0):
            raise RuntimeError(f"Joern phase command evidence is incomplete: {raw.get('case_id')}")
        command_refs.append({"reference": reference, "phase_id": phase,
                             "exit_status": command["exit_status"],
                             "timed_out": command["timed_out"],
                             "elapsed_seconds": command["elapsed_seconds"]})
    if observed_phases != ["typecheck", "frontend", "query"][:len(observed_phases)]:
        raise RuntimeError(f"Joern phase command evidence is not an invocation prefix: {raw.get('case_id')}")
    if raw.get("raw_outcome") in {"reached", "not-reached"} and (
            observed_phases != ["typecheck", "frontend", "query"]
            or any(row["exit_status"] != 0 or row["timed_out"] is not False
                   for row in command_refs)):
        raise RuntimeError(
            f"decisive Joern outcome requires all three successful non-timeout phases: {raw.get('case_id')}"
        )

    output_refs = []
    output_names: set[str] = set()
    for reference in outputs:
        output_path = _validate_reference(source, reference)
        if output_path.parent != raw_path.parent:
            raise RuntimeError(f"Joern native output escaped its case directory: {raw.get('case_id')}")
        if output_path.name in output_names:
            raise RuntimeError(f"duplicate Joern native output path: {raw.get('case_id')}")
        output_names.add(output_path.name)
        output_refs.append(reference)

    if disposition == "unsupported":
        if (raw.get("raw_outcome") != "unsupported" or raw.get("state") != "unsupported"
                or raw.get("executed") is not False or duration != 0
                or commands or outputs or raw.get("witness_checkpoints") != []):
            raise RuntimeError(f"unsupported Joern case must be a typed no-invocation row: {raw.get('case_id')}")
        return {
            "case_id": raw["case_id"], "disposition": "unsupported-no-invocation",
            "executed": False, "raw_outcome": "unsupported", "normalized_outcome": "unsupported",
            "duration_ms": 0, "latency_sample_included": False,
            "qualification": "unqualified", "commands": [], "native_outputs": [],
            "diagnostics": raw.get("diagnostics", []), "witness_checkpoints": [],
        }

    if disposition != "attempt" or raw.get("executed") is not True:
        raise RuntimeError(f"Joern attempted-case disposition changed: {raw.get('case_id')}")
    if not output_refs or "config.json" not in output_names or "source-closure.json" not in output_names:
        raise RuntimeError(f"attempted Joern case lacks bound configuration/source-closure proof: {raw.get('case_id')}")
    raw_outcome = raw.get("raw_outcome")
    if raw_outcome not in {"reached", "not-reached", "inconclusive", "runner-error"}:
        raise RuntimeError(f"attempted Joern case has an invalid typed raw outcome: {raw.get('case_id')}")
    return {
        "case_id": raw["case_id"], "disposition": "attempted-cost-not-qualified-result",
        "executed": True, "raw_outcome": raw_outcome, "normalized_outcome": raw["state"],
        "duration_ms": duration, "latency_sample_included": True,
        "qualification": "unqualified", "commands": command_refs,
        "native_outputs": output_refs,
        "diagnostics": raw.get("diagnostics", []),
        "witness_checkpoints": raw.get("witness_checkpoints", []),
    }


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load controller dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _qualified_module(root: Path):
    return _load_module("swift_supplement_qualified_campaign", root / "scripts/v092_timing_qualified_campaign.py")


def _validate_parent_lineage(root: Path) -> tuple[dict, dict, dict, dict]:
    refs = {
        "base_plan": {"path": BASE_PLAN_PATH, "sha256": BASE_PLAN_SHA256},
        "base_terminal": {"path": BASE_TERMINAL_PATH, "sha256": BASE_TERMINAL_SHA256},
        "base_inventory": {"path": BASE_INVENTORY_PATH, "sha256": BASE_INVENTORY_SHA256},
        "semgrep_audit": {"path": BASE_AUDIT_PATH, "sha256": BASE_AUDIT_SHA256},
    }
    paths = {key: _validate_reference(root, value) for key, value in refs.items()}
    base_plan = _read_json(paths["base_plan"])
    terminal = _read_json(paths["base_terminal"])
    inventory = _read_json(paths["base_inventory"])
    audit = _read_json(paths["semgrep_audit"])
    if base_plan.get("campaign_id") != "20261122-02" or base_plan.get("release_commit") != RELEASE:
        raise RuntimeError("parent plan is not the exact frozen v0.9.2-02 campaign")
    if len(base_plan.get("groups", [])) != 95:
        raise RuntimeError("parent plan must retain exactly 95 commands")
    if terminal.get("status") != "unqualified" or terminal.get("publication_eligible") is not False:
        raise RuntimeError("parent terminal must remain unqualified and non-publishable")
    if terminal.get("completed_commands") != 2 or terminal.get("remaining_ready_groups") != []:
        raise RuntimeError("parent terminal frontier or completed count changed")
    if set(terminal.get("blocked_groups", [])) != {"joern-swift-common108", "codeql-swift-common108"}:
        raise RuntimeError("parent blocked Swift frontier changed")
    if (inventory.get("schema") != "v092-timing-evidence-inventory/v1"
            or inventory.get("campaign_id") != "20261122-02"
            or inventory.get("file_count") != 111
            or inventory.get("publication_eligible") is not False):
        raise RuntimeError("parent 111-file evidence seal is malformed")
    if (audit.get("schema") != "v092-retrospective-warm-reconciliation/v1"
            or audit.get("status") != "diagnostic-candidate-recovered"
            or audit.get("original_controller_status") != "failed"
            or audit.get("publication_eligible") is not False
            or audit.get("original_plan", {}).get("sha256") != BASE_PLAN_SHA256
            or audit.get("capture_inventory", {}).get("sha256") != BASE_INVENTORY_SHA256
            or audit.get("capture_inventory_files_verified") != 111):
        raise RuntimeError("retrospective Semgrep audit no longer binds the failed historical attempt")
    original_start = audit.get("original_campaign_start")
    if (not isinstance(original_start, dict)
            or original_start.get("path") != "reports/timing/v0.9.2/20261122-02/campaign-start.json"):
        raise RuntimeError("Semgrep retrospective audit lost its original campaign-start binding")
    _validate_reference(root, {"path": original_start.get("path"), "sha256": original_start.get("sha256")})
    parent_start = _read_json(_repo_file(root, original_start["path"]))
    if parent_start.get("campaign_id") != "20261122-02" or parent_start.get("plan_sha256") != BASE_PLAN_SHA256:
        raise RuntimeError("parent campaign-start no longer binds the retained 95-command plan")
    group = next((item for item in base_plan["groups"] if item.get("id") == GROUP_ID), None)
    if not isinstance(group, dict) or group.get("status") != "blocked" or group.get("family") != "joern":
        raise RuntimeError("the Joern Swift group is no longer the exact blocked parent template")
    ids = group.get("case_ids")
    reports = group.get("reports")
    if (not isinstance(ids, list) or len(ids) != CASE_COUNT or len(set(ids)) != CASE_COUNT
            or not isinstance(reports, list) or len(reports) != REPORT_PARTITION_COUNT):
        raise RuntimeError("the frozen Joern Swift template must preserve 108 cases in five partitions")
    flattened = [case_id for report in reports for case_id in report.get("case_ids", [])]
    if len(flattened) != CASE_COUNT or len(flattened) != len(set(flattened)) or set(flattened) != set(ids):
        raise RuntimeError("frozen five-report partition membership does not cover the exact 108 cases")
    if group.get("argv") != [
        "/usr/bin/python3", "scripts/run-joern-common-v092.py", "execute", "--plan",
        "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json", "--output",
        "reports/raw/joern-common-v2/current108-v092-01",
    ]:
        raise RuntimeError("the historical frozen Joern argv changed")
    return base_plan, terminal, inventory, {"refs": refs, "group": group, "audit": audit}


def _collect_references(value: Any, found: dict[str, str]) -> None:
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            path, digest = value.get("path"), value.get("sha256")
            if not isinstance(path, str) or not isinstance(digest, str):
                raise RuntimeError("malformed exact path/SHA reference in Joern inputs")
            existing = found.get(path)
            if existing is not None and existing != digest:
                raise RuntimeError(f"conflicting SHA references for {path}")
            found[path] = digest
        for child in value.values():
            _collect_references(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_references(child, found)


def _reference_closure(root: Path, plan: dict) -> dict[str, str]:
    """Bind exact inputs and recursively retain only the fresh control capture.

    The frozen v0.9.2-01 plan is needed for its contract/configuration identity,
    but its old fresh-qualification receipt and old CPG capture are not inputs
    to this supplement. The relocated admission adapter independently replays
    only the prior strict summary, registration archive, and archived control
    plan. The new qualification receipt is followed recursively so every fresh
    raw, graph, config, command, and binary reference is copied and verified.
    """
    found: dict[str, str] = {}
    _collect_references(plan, found)

    case_decision_paths: set[str] = set()
    for selection in plan.get("cases", {}).values():
        decision_ref = selection.get("decision") if isinstance(selection, dict) else None
        if decision_ref is None:
            continue
        decision_path = _validate_reference(root, decision_ref)
        case_decision_paths.add(decision_ref["path"])
        decision = _read_json(decision_path)
        before = set(found)
        _collect_references(decision, found)
        for relative in set(found) - before:
            if relative in found:
                _validate_reference(root, {"path": relative, "sha256": found[relative]})

    # The v0.9.2-03 plan carries current-identity unsupported dispositions in
    # a top-level map while retaining the old v0.9.0 case decisions in cases.
    # Open each new decision record here so policy and historical provenance
    # references nested inside it enter the prepared-source closure as well.
    unsupported_rows = {
        case_id for case_id, selection in plan.get("cases", {}).items()
        if isinstance(selection, dict) and selection.get("disposition") == "unsupported"
    }
    top_level_unsupported = plan.get("unsupported_decisions")
    unsupported_decision_paths: set[str] = set()
    if (not isinstance(top_level_unsupported, dict)
            or set(top_level_unsupported) != unsupported_rows):
        raise RuntimeError("plan must bind one current-identity decision for every unsupported case")
    for case_id, decision_ref in top_level_unsupported.items():
        decision_path = _validate_reference(root, decision_ref)
        relative_path = decision_ref["path"]
        if relative_path in unsupported_decision_paths:
            raise RuntimeError("two unsupported cases share one decision record")
        unsupported_decision_paths.add(relative_path)
        decision = _read_json(decision_path)
        if decision.get("case_id") != case_id:
            raise RuntimeError(f"current unsupported decision identity differs for {case_id}")
        before = set(found)
        _collect_references(decision, found)
        for relative in set(found) - before:
            if relative in found:
                _validate_reference(root, {"path": relative, "sha256": found[relative]})

    failure_policy_ref = plan.get("failure_policy")
    expected_failure_policy = {"path": PROJECTION_RECOVERY_AUTHORIZATION_PATH,
                               "sha256": PROJECTION_RECOVERY_AUTHORIZATION_SHA256}
    if failure_policy_ref != expected_failure_policy:
        raise RuntimeError("unsupported disposition failure policy is missing or changed")
    _validate_reference(root, failure_policy_ref)

    control_ref = plan.get("qualification_control_plan")
    control_path = _validate_reference(root, control_ref)
    if control_ref.get("path") != CONTROL_PLAN_PATH:
        raise RuntimeError("qualified plan must bind the exact prospective control plan")
    control = _read_json(control_path)
    admission = control.get("diagnostic_admission")
    if not isinstance(admission, dict):
        raise RuntimeError("new control plan lacks its bounded prior-control admission")
    prior_run_ref = admission.get("prior_control_run")
    prior_archive_ref = admission.get("prior_registration_archive")
    if (not isinstance(prior_run_ref, dict) or prior_run_ref.get("path") != PRIOR_CONTROL_RUN_PATH
            or not isinstance(prior_archive_ref, dict)
            or prior_archive_ref.get("path") != PRIOR_REGISTRATION_ARCHIVE_PATH):
        raise RuntimeError("new control plan no longer binds the exact prior strict control summary/archive")
    prior_run_path = _validate_reference(root, prior_run_ref)
    prior_archive_path = _validate_reference(root, prior_archive_ref)
    archive = _read_json(prior_archive_path)
    archived_control_ref = archive.get("control_plan")
    if (not isinstance(archived_control_ref, dict)
            or archived_control_ref.get("path") != PRIOR_CONTROL_PLAN_PATH):
        raise RuntimeError("prior registration archive no longer binds control-plan-02")
    _validate_reference(root, archived_control_ref)
    for reference in (control_ref, prior_run_ref, prior_archive_ref, archived_control_ref):
        relative, digest = reference["path"], reference["sha256"]
        existing = found.get(relative)
        if existing is not None and existing != digest:
            raise RuntimeError(f"conflicting SHA references for {relative}")
        found[relative] = digest

    # All direct configuration/runtime references stay in the source closure,
    # but only the new qualification subtree is recursively hydrated. This
    # avoids pulling the unused v0.9.2-01 qualification CPGs through the frozen
    # plan while preserving the exact new control proof chain.
    qualification_prefix = QUALIFICATION_ROOT.rstrip("/") + "/"
    decision_paths = case_decision_paths | unsupported_decision_paths
    pending = [relative for relative in found
               if relative.startswith(qualification_prefix) or relative in decision_paths]
    visited: set[str] = set()
    while pending:
        relative = pending.pop()
        if relative in visited:
            continue
        visited.add(relative)
        if len(visited) > 5000:
            raise RuntimeError("qualified Joern input closure exceeds the bounded reference count")
        path = _repo_file(root, relative)
        if sha(path) != found[relative]:
            raise RuntimeError(f"qualified Joern input changed: {relative}")
        if relative in decision_paths:
            continue
        if path.suffix not in {".json", ".gz"}:
            continue
        raw = path.read_bytes()
        candidate = raw
        if path.suffix == ".gz":
            try:
                candidate = gzip.decompress(raw)
            except OSError:
                continue
        if not candidate.lstrip().startswith((b"{", b"[")):
            continue
        try:
            value = json.loads(candidate)
        except (UnicodeError, json.JSONDecodeError):
            continue
        before = set(found)
        _collect_references(value, found)
        pending.extend(relative for relative in set(found) - before
                       if relative.startswith(qualification_prefix))
    return found


def _load_runner(root: Path):
    scripts = root / "scripts"
    module_names = (
        "swift_common_population_v2", "swift_normal_reports_v1", "joern_normal_controls_v1",
        "v092_qualification", "v092_capability_qualification",
        "joern_diagnostic_admission_v092", "joern_diagnostic_admission_v092_capability",
        "joern_normal_reports_v092", "joern_normal_reports_v092_projection",
    )
    saved = {name: sys.modules.pop(name) for name in module_names if name in sys.modules}
    sys.path.insert(0, str(scripts))
    try:
        return _load_module(
            f"joern_runner_supplement_{hashlib.sha256(str(root).encode()).hexdigest()[:8]}",
            scripts / CAPABILITY_V3_RUNNER_PATH.rsplit("/", 1)[-1],
        )
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass
        sys.modules.update(saved)


def _case_disposition_counts(cases: object) -> dict[str, int]:
    if not isinstance(cases, dict) or len(cases) != CASE_COUNT:
        raise RuntimeError("Joern case disposition roster must contain exactly 108 cases")
    counts = {"attempt": 0, "unsupported": 0}
    for case_id, selection in cases.items():
        if not isinstance(case_id, str) or not isinstance(selection, dict):
            raise RuntimeError("Joern case disposition row is malformed")
        disposition = selection.get("disposition")
        if disposition not in counts:
            raise RuntimeError(f"Joern case has an unsupported disposition value: {case_id}")
        counts[disposition] += 1
    if counts != {"attempt": 96, "unsupported": 12}:
        raise RuntimeError(f"Joern supplement must preserve 96 attempted and 12 unsupported cases: {counts}")
    return counts


def _qualification_publication_state(evidence: dict) -> str:
    # The v0.9.2 qualification schema authorizes execution, not publication.
    # Preserve an absent field rather than inventing a statement in its receipt.
    if "publication_eligible" not in evidence:
        return "not-declared"
    if evidence["publication_eligible"] is not False:
        raise RuntimeError("fresh Joern controls cannot enable publication")
    return "explicitly-disabled"


def _validate_v03_qualification(root: Path) -> tuple[dict, dict, dict, dict, dict]:
    pending_path = _validate_reference(root, {"path": PENDING_PLAN_PATH, "sha256": PENDING_PLAN_SHA256})
    pending = _read_json(pending_path)
    control_ref = pending.get("qualification_control_plan")
    if control_ref != {"path": CONTROL_PLAN_PATH, "sha256": CONTROL_PLAN_SHA256}:
        raise RuntimeError("v03 pending plan no longer binds the exact capability control plan")
    _validate_reference(root, control_ref)
    if (pending.get("schema") != "joern-common-execution-plan/v092"
            or pending.get("release_group_id") != GROUP_ID
            or pending.get("status") != "qualification-pending"
            or pending.get("execution_eligible") is not False
            or pending.get("full_model_qualification") is not False
            or pending.get("population_sha256") != "d05be4f2d9effe7b14a2ce5544238364f171e1fb763db2f79ff486526ca7c890"
            or len(pending.get("cases", {})) != CASE_COUNT):
        raise RuntimeError("pending v0.9.2 Joern plan no longer preserves its 108-case identity")
    _case_disposition_counts(pending["cases"])
    final_path = _repo_file(root, QUALIFIED_PLAN_PATH)
    if final_path.is_symlink():
        raise RuntimeError("qualified Joern execution plan must be a regular file")
    runner = _load_runner(root)
    plan, evidence, context = runner.validate_plan(root, QUALIFIED_PLAN_PATH)
    if (plan.get("status") != "execution-eligible" or plan.get("execution_eligible") is not True
            or plan.get("diagnostic_execution_eligible") is not True
            or plan.get("full_model_qualification") is not False
            or plan.get("scored_activation") is not False
            or len(plan.get("cases", {})) != CASE_COUNT
            or set(plan.get("cases", {})) != set(pending.get("cases", {}))):
        raise RuntimeError("qualified Joern plan must enable only diagnostic execution over the same 108 cases")
    if plan.get("cases") != pending.get("cases"):
        raise RuntimeError("qualified Joern plan changed the pending case configuration or disposition roster")
    _case_disposition_counts(plan["cases"])
    capability_binding = runner.validate_capability_binding(root, plan)
    attempted_ids = {case_id for case_id, row in plan["cases"].items()
                     if row.get("disposition") == "attempt"}
    unsupported_ids = {case_id for case_id, row in plan["cases"].items()
                       if row.get("disposition") == "unsupported"}
    pending_unsupported = pending.get("unsupported_decisions")
    final_unsupported = plan.get("unsupported_decisions")
    if (not isinstance(pending_unsupported, dict) or len(pending_unsupported) != 12
            or final_unsupported != pending_unsupported or set(pending_unsupported) != unsupported_ids):
        raise RuntimeError("v03 pending and qualified plans must preserve the exact 12 unsupported disposition references")
    for case_id, decision_ref in pending_unsupported.items():
        expected_path = f"adapters/joern/swift-common-v2/plan-v092-03/unsupported-dispositions-02/{case_id}.json"
        if (not isinstance(decision_ref, dict) or set(decision_ref) != {"path", "sha256"}
                or decision_ref.get("path") != expected_path
                or not isinstance(decision_ref.get("sha256"), str)
                or len(decision_ref["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in decision_ref["sha256"])):
            raise RuntimeError(f"v03 unsupported decision reference is not exact for {case_id}")
        _validate_reference(root, decision_ref)
    expected_capability = {
        "identity_gate": "exact-native-edges",
        "model_mode": "off",
        "model_status": "unqualified",
    }
    historical_decisions = capability_binding.get("historical_unsupported_decisions")
    if (capability_binding.get("schema") != "joern-v092-capability-binding/v2"
            or capability_binding.get("source") != {
                "path": CAPABILITY_SOURCE_PATH, "sha256": CAPABILITY_SOURCE_SHA256,
            }
            or capability_binding.get("attempt_count") != 96
            or capability_binding.get("unsupported_count") != 12
            or not isinstance(capability_binding.get("capabilities"), dict)
            or set(capability_binding["capabilities"]) != attempted_ids
            or any(row != expected_capability for row in capability_binding["capabilities"].values())
            or capability_binding.get("unsupported_decisions") != pending_unsupported
            or not isinstance(historical_decisions, dict)
            or set(historical_decisions) != unsupported_ids):
        raise RuntimeError("v03 plan does not preserve the exact 96 frozen capabilities and 12 unsupported decisions")
    if evidence.get("diagnostic_execution_eligible") is not True or evidence.get("full_model_qualification") is not False:
        raise RuntimeError("fresh Joern controls did not qualify diagnostic execution while retaining uncertainty")
    _qualification_publication_state(evidence)
    return plan, evidence, context, {"pending": pending, "runner": runner}, capability_binding


def _input_code_paths(plan: dict) -> list[str]:
    # Runtime manifests and qualification captures are digest-bound, but they
    # are generated evidence and need not be Git-tracked. Executable helpers,
    # both exact plan files, and the explicit authorization must be committed.
    return sorted({*HELPER_PATHS, QUALIFIED_PLAN_PATH, PENDING_PLAN_PATH,
                   DIAGNOSTIC_AUTHORIZATION_PATH,
                   LAUNCHER_RECOVERY_AUTHORIZATION_PATH,
                   CAPABILITY_RECOVERY_AUTHORIZATION_PATH,
                   UNSUPPORTED_PROVENANCE_AUTHORIZATION_PATH,
                   PROJECTION_RECOVERY_AUTHORIZATION_PATH,
                   V01_EXECUTION_PLAN_PATH})


def _require_committed_code_inputs(root: Path, plan: dict, expected: dict[str, str] | None = None) -> dict[str, str]:
    expected = {} if expected is None else dict(expected)
    for relative in _input_code_paths(plan):
        path = _repo_file(root, relative)
        digest = sha(path)
        try:
            committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Joern execution input is not committed at HEAD: {relative}") from exc
        if _sha_bytes(committed) != digest or (relative in expected and expected[relative] != digest):
            raise RuntimeError(f"committed Joern execution input differs from its binding: {relative}")
        status = subprocess.check_output(["git", "status", "--porcelain=v1", "--", relative], cwd=root, text=True)
        if status.strip():
            raise RuntimeError(f"Joern execution input has uncommitted edits: {relative}")
        expected[relative] = digest
    return expected


def _validate_group_and_command(plan: dict, base_group: dict) -> dict:
    output = plan.get("output_root")
    if output != "reports/raw/joern-common-v2":
        raise RuntimeError("qualified Joern plan must preserve its exact common output root")
    parent_environment = base_group.get("environment")
    if (not isinstance(parent_environment, dict)
            or parent_environment.get("PATH") != PARENT_GROUP_PATH):
        raise RuntimeError("frozen parent Joern group PATH differs from the recorded launch environment")
    expected_argv = [
        "/usr/bin/python3", CAPABILITY_V3_CLI_PATH, "execute", "--plan",
        QUALIFIED_PLAN_PATH, "--output", OUTPUT_ARGUMENT,
    ]
    group = json.loads(json.dumps(base_group))
    group.update({
        "argv": expected_argv,
        "status": "ready",
        "blocker": None,
        "deadline_seconds": GROUP_TIMEOUT_SECONDS,
        "maximum_attempts": 1,
        "automatic_retry": False,
        "output_roots": [OUTPUT_RELATIVE],
        "reports": [
            {**row, "source_path": f"{OUTPUT_RELATIVE}/normal/report-{index}.json"}
            for index, row in enumerate(base_group["reports"])
        ],
        "runtime_ids": sorted(row["name"] for row in plan["identity_components"]),
        "environment": {
            "HOME": "@SUPPLEMENT_SOURCE@/home",
            "TMPDIR": "@SUPPLEMENT_SOURCE@/tmp",
            "PATH": PARENT_GROUP_PATH,
            "LANG": "en_US.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
            "DATAFLOWBENCH_V092_GROUP_ID": GROUP_ID,
        },
    })
    if group["argv"] != expected_argv or group.get("kind") != "cold" or group.get("family") != "joern":
        raise RuntimeError("supplement command differs from the one reviewed Joern Swift execution")
    if len(group["case_ids"]) != CASE_COUNT or len(group["reports"]) != REPORT_PARTITION_COUNT:
        raise RuntimeError("supplement command lost the exact 108-case/five-report population")
    if [row.get("path") for row in group["reports"]] != [row.get("path") for row in base_group["reports"]]:
        raise RuntimeError("supplement report contract paths drifted from the frozen template")
    if [row.get("case_ids") for row in group["reports"]] != [row.get("case_ids") for row in base_group["reports"]]:
        raise RuntimeError("supplement report partition membership drifted from the frozen template")
    return group


def _configuration_hash(root: Path, plan: dict) -> tuple[str, list[str]]:
    references = plan.get("configurations", {}).get("joern-current108")
    if not isinstance(references, list) or not references:
        raise RuntimeError("Joern configuration closure is missing")
    normalized = []
    seen: set[str] = set()
    for reference in references:
        path = _validate_reference(root, reference)
        relative = reference["path"]
        if relative in seen:
            raise RuntimeError(f"duplicate Joern configuration path: {relative}")
        seen.add(relative)
        normalized.append((relative, path.read_bytes()))
    digest = hashlib.sha256()
    for relative, raw in sorted(normalized, key=lambda item: PurePosixPath(item[0]).parts):
        digest.update(relative.encode())
        digest.update(raw)
    return digest.hexdigest(), sorted(seen)


def _configuration_provenance(root: Path, qualified_plan: dict, base_plan: dict) -> dict:
    old = _read_json(_repo_file(root, V01_EXECUTION_PLAN_PATH))
    old_rows = old.get("configurations", {}).get("joern-current108")
    new_rows = qualified_plan.get("configurations", {}).get("joern-current108")
    if (not isinstance(old_rows, list) or len(old_rows) != 33
            or not isinstance(new_rows, list) or len(new_rows) != 45):
        raise RuntimeError("v03 configuration closure must retain exactly 33 historical and 12 additive rows")
    expected_addition_rows = [
        {"path": relative, "sha256": sha(_repo_file(root, relative))}
        for relative in APPROVED_CONFIGURATION_ADDITIONS
    ]
    if new_rows != old_rows + expected_addition_rows:
        raise RuntimeError("v03 configuration closure must preserve the exact old 33 rows and append the reviewed 12 in order")
    old_hash, old_paths = _configuration_hash(root, old)
    new_hash, new_paths = _configuration_hash(root, qualified_plan)
    old_refs = {item["path"]: item["sha256"] for item in old_rows}
    new_refs = {item["path"]: item["sha256"] for item in new_rows}
    missing = sorted(set(old_refs) - set(new_refs))
    changed = sorted(path for path in old_refs.keys() & new_refs.keys()
                     if old_refs[path] != new_refs[path])
    additions = sorted(set(new_refs) - set(old_refs))
    if missing or changed:
        raise RuntimeError("v02 configuration closure removed or changed an old bound entry: "
                           + json.dumps({"removed": missing, "changed": changed}, sort_keys=True))
    if additions != sorted(APPROVED_CONFIGURATION_ADDITIONS):
        raise RuntimeError("v02 configuration closure additions differ from the exact approved provenance list: "
                           + json.dumps({"expected": sorted(APPROVED_CONFIGURATION_ADDITIONS),
                                         "actual": additions}, sort_keys=True))
    frozen = base_plan.get("frozen_report_bindings", {}).get(GROUP_ID, [])
    frozen_hashes = {item.get("identity", {}).get("configuration_hash") for item in frozen}
    if len(frozen_hashes) != 1 or old_hash not in frozen_hashes:
        raise RuntimeError("old v01 configuration hash does not match all five frozen report headers")
    return {
        "schema": "v092-swift-supplement-configuration-provenance/v1",
        "formula": "sha256(sorted(path.parts): path UTF-8 bytes followed by bound file bytes)",
        "historical_plan": _reference(root, V01_EXECUTION_PLAN_PATH),
        "historical_configuration_hash": old_hash,
        "candidate_configuration_hash": new_hash,
        "historical_configuration_paths": old_paths,
        "candidate_configuration_paths": new_paths,
        "retained_historical_paths_byte_identical": sorted(old_refs),
        "removed_paths": [],
        "approved_additions": additions,
        "approved_addition_reason": (
            "versioned relocated execution/qualification helpers and hash-bound relocated runtime "
            "component provenance; the Joern contract, case population, model/query, and all prior "
            "configuration entries remain byte-identical"
        ),
        "historical_report_configuration_hashes": sorted(frozen_hashes),
        "report_header_configuration_hash_policy": (
            "preserve each original normalized report byte-for-byte; the capability-aware projection "
            "exporter adds exactly one candidate configuration_hash field in a separate derived namespace "
            "using the separately bound historical hash helper"
        ),
        "publication_eligible": False,
    }


def _resource_scope(root: Path) -> dict:
    q = _qualified_module(root)
    campaign_ids = list(RESOURCE_CAMPAIGN_IDS)
    start_refs = []
    starts = {}
    for campaign_id in campaign_ids:
        relative = f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        reference = _reference(root, relative)
        start = _read_json(_validate_reference(root, reference))
        if start.get("campaign_id") != campaign_id or not isinstance(start.get("scratch_roots"), list):
            raise RuntimeError(f"resource ancestor campaign-start is malformed: {campaign_id}")
        start_refs.append(reference)
        starts[campaign_id] = start

    checkpoint_ref = {"path": RESOURCE_PARENT_CHECKPOINT_PATH,
                      "sha256": RESOURCE_PARENT_CHECKPOINT_SHA256}
    checkpoint = _read_json(_validate_reference(root, checkpoint_ref))
    if (checkpoint.get("schema") != "v092-timing-background-checkpoint/v1"
            or checkpoint.get("parent_campaign_id") != "20261122-01"
            or checkpoint.get("resource_campaign_ids") != campaign_ids[:-1]):
        raise RuntimeError("20261122-02 parent checkpoint has unexpected resource ancestry")

    continuation = starts["20261122-02"].get("continuation_checkpoint")
    if continuation != checkpoint_ref:
        raise RuntimeError("20261122-02 campaign-start does not bind its exact parent checkpoint")
    context = {"schema": "v092-swift-supplement-resource-context/v1",
               "parent_campaign_id": "20261122-02",
               "resource_campaign_ids": campaign_ids}
    inherited_roots, inherited_retained, inherited_scratch = q._inherited_resource_paths(context)
    expected_roots = [root / f"execution-state/timing-v092-{campaign_id}/sources"
                      for campaign_id in campaign_ids]
    if [path.resolve(strict=False) for path in inherited_roots] != [
            path.resolve(strict=False) for path in expected_roots]:
        raise RuntimeError("combined inherited resource roots differ from the four bound ancestors")

    start = starts["20261122-02"]
    scope = start.get("cumulative_resource_scope")
    if (not isinstance(scope, dict)
            or not all(isinstance(scope.get(key), list) for key in ("retained", "working"))):
        raise RuntimeError("parent cumulative resource scope is malformed")
    expected_working = {path.resolve(strict=False) for path in expected_roots}
    parent_working = {
        _validated_accounting_path(root, item, scratch=False).resolve(strict=False)
        for item in scope["working"]
    }
    if parent_working != expected_working:
        raise RuntimeError("parent cumulative working scope does not cover exactly all four ancestors")
    expected_scratch = {
        _validated_accounting_path(root, item, scratch=True).resolve(strict=False)
        for campaign_id in campaign_ids
        for item in starts[campaign_id]["scratch_roots"]
    }
    helper_scratch = {path.resolve(strict=False) for path in inherited_scratch}
    parent_scratch = {
        _validated_accounting_path(root, item, scratch=True).resolve(strict=False)
        for item in start["scratch_roots"]
    }
    if helper_scratch != expected_scratch or parent_scratch != expected_scratch:
        raise RuntimeError("combined inherited scratch scope differs from the four bound campaign starts")

    profile_ref = {"path": RESOURCE_PROFILE_PATH, "sha256": RESOURCE_PROFILE_SHA256}
    profile = _read_json(_validate_reference(root, profile_ref))
    results = profile.get("results")
    if (profile.get("schema") != "v092-resource-observer-profile/v1"
            or profile.get("accounted_totals_equal") is not True
            or profile.get("limits_unchanged") is not True
            or profile.get("baseline_materialization_outside_profile_and_timed_window") is not True
            or profile.get("scope") != "untimed guard profile only; no analyzer or performance corpus measurement"
            or not isinstance(results, list) or len(results) != 2
            or results[0].get("mode") != "full-ancestor-rescan"
            or results[1].get("mode") != "immutable-baseline-plus-active-rescan"):
        raise RuntimeError("resource observer profile is not the reviewed untimed equivalent-count profile")
    profile_parent_bytes = {"working": 19073573545, "retention": 630366349,
                            "scratch": 3198936017}
    if results[1].get("baseline_bytes") != profile_parent_bytes:
        raise RuntimeError("resource observer profile parent baseline byte counts changed")
    if {category: results[0].get("checks", {}).get(category, {}).get("current_bytes")
        for category in profile_parent_bytes} != {
            category: results[1].get("checks", {}).get(category, {}).get("current_bytes")
            for category in profile_parent_bytes
        }:
        raise RuntimeError("resource observer profile optimized totals no longer match full scans")
    post_profile_additions = []
    for addition in POST_PROFILE_RETAINED_ADDITIONS:
        ref = {"path": addition["path"], "sha256": addition["sha256"]}
        addition_path = _validate_reference(root, ref)
        if addition_path.stat().st_size != addition["size_bytes"]:
            raise RuntimeError(f"post-profile retained addition size changed: {addition['path']}")
        post_profile_additions.append(dict(addition))
    expected_parent_bytes = dict(profile_parent_bytes)
    expected_parent_bytes["retention"] += sum(
        row["size_bytes"] for row in post_profile_additions)
    owner_ref = {"path": RESOURCE_OWNER_RECEIPT_PATH,
                 "sha256": RESOURCE_OWNER_RECEIPT_SHA256}
    owner_receipt = _read_json(_validate_reference(root, owner_ref))
    if (owner_receipt.get("schema") != "v092-joern-post-control-ownership/v1"
            or owner_receipt.get("recorded_process_identities") != 118
            or owner_receipt.get("command_records") != 37
            or owner_receipt.get("same_identities_still_alive") != []
            or owner_receipt.get("signals_sent_by_audit") != []
            or owner_receipt.get("serial_lock_available") is not True
            or owner_receipt.get("descendant_containment") != "unproven"):
        raise RuntimeError("preparation ownership receipt does not prove the bound stopped process identities")
    portability_ref = {"path": PORTABILITY_RECEIPT_PATH,
                       "sha256": PORTABILITY_RECEIPT_SHA256}
    portability = _read_json(_validate_reference(root, portability_ref))
    if (portability.get("schema") != "v092-joern-prepared-source-portability-preflight/v1"
            or portability.get("status") != "passed" or portability.get("exit_code") != 0
            or type(portability.get("exit_code")) is not int
            or portability.get("analyzer_invocations") != 0
            or type(portability.get("analyzer_invocations")) is not int
            or portability.get("source_commit") != RELEASE
            or portability.get("source") != str(root / PORTABILITY_SOURCE_PATH)
            or not isinstance(portability.get("input_refs"), dict)
            or len(portability["input_refs"]) != 49):
        raise RuntimeError("portability receipt does not bind the closed, analyzer-free source preparation")
    for relative, digest in portability["input_refs"].items():
        if (not isinstance(relative, str) or not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)
                or sha(_repo_file(root, relative)) != digest):
            raise RuntimeError(f"closed portability preflight input changed: {relative}")

    parent_baseline = {
        "working": list(expected_roots),
        "retention": [_validated_accounting_path(root, item, scratch=False)
                      for item in scope["retained"]],
        "scratch": list(inherited_scratch),
    }
    parent_baseline["retention"].extend(inherited_retained)
    parent_baseline["retention"].extend(root / relative for relative in (
        "reports/timing/v0.9.2/reconciliation-20261122-01",
        "reports/timing/v0.9.2/preparation-20261122-swift-01",
        "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01",
    ))
    parent_baseline = {category: _unique_paths(paths)
                       for category, paths in parent_baseline.items()}
    addition_paths = [root / row["path"] for row in post_profile_additions]
    for addition_path in addition_paths:
        if not any(addition_path.is_relative_to(retained_root)
                   for retained_root in parent_baseline["retention"]):
            raise RuntimeError("post-profile retained addition is outside the bound retention roots")

    preparation_paths = {
        "working": [root / PORTABILITY_SOURCE_PATH, root / QUALIFICATION_WORK_ROOT,
                    root / FAILED_PREPARATION_SOURCE, root / FAILED_PREPARATION_04_SOURCE,
                    root / FAILED_PREPARATION_05_SOURCE, root / FAILED_WRAPPER_SOURCE,
                    root / FAILED_CAPABILITY_SOURCE, root / LAUNCHER_SMOKE_ROOT],
        "retention": [root / PREPARATION_ROOT, root / FAILED_PREPARATION_REPORT,
                      root / FAILED_PREPARATION_04_REPORT,
                      root / FAILED_PREPARATION_04_SOURCE / "reports",
                      root / FAILED_PREPARATION_05_REPORT,
                      root / FAILED_PREPARATION_05_SOURCE / "reports",
                      root / FAILED_WRAPPER_REPORT, root / FAILED_WRAPPER_SOURCE / "reports",
                      root / FAILED_CAPABILITY_REPORT, root / FAILED_CAPABILITY_SOURCE / "reports"],
        "scratch": [root / QUALIFICATION_CONTROL_SCRATCH,
                    *(root / QUALIFICATION_WORK_ROOT / name for name in ("home", "tmp", "cache")),
                    *(root / FAILED_PREPARATION_04_SOURCE / name for name in ("home", "tmp", "cache")),
                    *(root / FAILED_PREPARATION_05_SOURCE / name for name in ("home", "tmp", "cache")),
                    *(root / FAILED_WRAPPER_SOURCE / name for name in ("home", "tmp", "cache")),
                    *(root / FAILED_CAPABILITY_SOURCE / name for name in ("home", "tmp", "cache")),
                    root / LAUNCHER_SMOKE_ROOT],
    }
    closed_preparation_paths = {
        "working": {root / FAILED_PREPARATION_SOURCE, root / FAILED_PREPARATION_04_SOURCE,
                    root / FAILED_PREPARATION_05_SOURCE, root / FAILED_WRAPPER_SOURCE,
                    root / FAILED_CAPABILITY_SOURCE, root / LAUNCHER_SMOKE_ROOT},
        "retention": {root / FAILED_PREPARATION_REPORT, root / FAILED_PREPARATION_04_REPORT,
                      root / FAILED_PREPARATION_04_SOURCE / "reports",
                      root / FAILED_PREPARATION_05_REPORT,
                      root / FAILED_PREPARATION_05_SOURCE / "reports",
                      root / FAILED_WRAPPER_REPORT, root / FAILED_WRAPPER_SOURCE / "reports",
                      root / FAILED_CAPABILITY_REPORT, root / FAILED_CAPABILITY_SOURCE / "reports"},
        "scratch": {
            *(root / FAILED_PREPARATION_04_SOURCE / name for name in ("home", "tmp", "cache")),
            *(root / FAILED_PREPARATION_05_SOURCE / name for name in ("home", "tmp", "cache")),
            *(root / FAILED_WRAPPER_SOURCE / name for name in ("home", "tmp", "cache")),
            *(root / FAILED_CAPABILITY_SOURCE / name for name in ("home", "tmp", "cache")),
            root / LAUNCHER_SMOKE_ROOT,
        },
    }
    active_paths = {
        "working": [root / SOURCE_RELATIVE],
        "retention": [root / REPORT_ROOT, root / SOURCE_RELATIVE / "reports"],
        "scratch": [root / SOURCE_RELATIVE / name for name in ("home", "tmp", "cache")],
    }
    profile_static = profile.get("static_paths")
    profile_preparation = profile.get("active_proxy_paths")
    if not isinstance(profile_static, dict) or not isinstance(profile_preparation, dict):
        raise RuntimeError("resource observer profile path partitions are malformed")
    for category in ("working", "retention", "scratch"):
        static_paths = [_validated_accounting_path(root, item, scratch=category == "scratch")
                        for item in profile_static.get(category, [])]
        preparation_proxy = [_validated_accounting_path(root, item, scratch=category == "scratch")
                             for item in profile_preparation.get(category, [])]
        prior_preparation = [path for path in preparation_paths[category]
                             if path not in closed_preparation_paths[category]]
        if ({str(path) for path in static_paths} != {str(path) for path in parent_baseline[category]}
                or {str(path) for path in preparation_proxy} != {str(path) for path in prior_preparation}):
            raise RuntimeError(f"resource observer profile path partition differs for {category}")
        _assert_disjoint_resource_paths(parent_baseline[category], preparation_paths[category], category)
        _assert_disjoint_resource_paths(parent_baseline[category], active_paths[category], category)
        _assert_disjoint_resource_paths(preparation_paths[category], active_paths[category], category)

    all_paths = {
        category: _unique_paths([*parent_baseline[category], *preparation_paths[category],
                                *active_paths[category]])
        for category in ("working", "retention", "scratch")
    }
    return {
        "retained": [str(path) for path in all_paths["retention"]],
        "working": [str(path) for path in all_paths["working"]],
        "scratch": [str(path) for path in all_paths["scratch"]],
        "resource_campaign_ids": campaign_ids,
        "campaign_start_references": start_refs,
        "parent_checkpoint": checkpoint_ref,
        "inherited_source_roots": [str(path) for path in inherited_roots],
        "parent_campaign_start": start_refs[-1],
        "observer_profile": profile_ref,
        "closed_process_ownership": owner_ref,
        "closed_process_ownership_state": {
            "recorded_process_identities": 118, "same_identities_still_alive": 0,
            "command_records": 37, "serial_lock_available": True,
            "descendant_containment": "unproven",
        },
        "portability_preflight": portability_ref,
        "observer_method": RESOURCE_OBSERVER_METHOD,
        "closed_preparation_roots": {
            category: [str(path) for path in preparation_paths[category]
                       if path in closed_preparation_paths[category]]
            for category in ("working", "retention", "scratch")
        },
        "profile_expected_parent_baseline_bytes": profile_parent_bytes,
        "post_profile_retained_additions": post_profile_additions,
        "expected_parent_baseline_bytes": expected_parent_bytes,
        "baseline_paths": {category: [str(path) for path in paths]
                           for category, paths in parent_baseline.items()},
        "preparation_paths": {category: [str(path) for path in paths]
                              for category, paths in preparation_paths.items()},
        "active_paths": {category: [str(path) for path in paths]
                         for category, paths in active_paths.items()},
    }


def _assert_disjoint_resource_paths(left: list[Path], right: list[Path], category: str) -> None:
    left_paths = [path.resolve(strict=False) for path in left]
    right_paths = [path.resolve(strict=False) for path in right]
    for left_path in left_paths:
        if any(left_path == right_path or left_path.is_relative_to(right_path)
               or right_path.is_relative_to(left_path) for right_path in right_paths):
            raise RuntimeError(f"resource baseline and live paths overlap for {category}: {left_path}")


def _validated_accounting_path(root: Path, raw: object, *, scratch: bool) -> Path:
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("parent resource path is malformed")
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    normalized = path.resolve(strict=False)
    if normalized != path:
        raise RuntimeError(f"parent resource path is not normalized: {path}")
    if path.is_relative_to(root):
        return path
    if scratch and path.parent == Path("/private/tmp") and path.name.startswith("dfb-v092-pysa-"):
        return path
    raise RuntimeError(f"parent resource path escapes the registered roots: {path}")


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result = []
    for path in paths:
        value = str(path)
        if value not in seen:
            seen.add(value)
            result.append(path)
    return result


def validate_campaign_plan(plan: dict) -> None:
    """Validate invariants that do not depend on repository files."""
    if plan.get("schema") != "v092-timing-swift-supplement-plan/v1":
        raise RuntimeError("unsupported Swift supplement plan schema")
    if plan.get("campaign_id") != CAMPAIGN_ID or plan.get("group_id") != GROUP_ID:
        raise RuntimeError("supplement campaign/group identity changed")
    if plan.get("dispatch_groups") != [GROUP_ID] or plan.get("attempts_per_group") != {GROUP_ID: 1}:
        raise RuntimeError("supplement may dispatch exactly one Joern Swift command once")
    if plan.get("parent_ready_frontier") != [] or plan.get("parent_group_count") != 95:
        raise RuntimeError("supplement must preserve the terminal 95-command parent frontier")
    if plan.get("case_count") != CASE_COUNT or plan.get("report_partition_count") != REPORT_PARTITION_COUNT:
        raise RuntimeError("supplement denominator must remain 108 cases across five reports")
    if (plan.get("case_disposition_counts") != {"attempt": 96, "unsupported": 12}
            or plan.get("attempted_case_count") != 96
            or plan.get("unsupported_case_count") != 12):
        raise RuntimeError("timing population must retain 96 attempted cases and 12 no-invocation unsupported cases")
    if plan.get("old_argv") == plan.get("argv") or not isinstance(plan.get("argv"), list):
        raise RuntimeError("historical and actual supplement argv must be distinct and explicit")
    if plan.get("argv") != [
        "/usr/bin/python3", CAPABILITY_V3_CLI_PATH, "execute", "--plan",
        QUALIFIED_PLAN_PATH, "--output", OUTPUT_ARGUMENT,
    ]:
        raise RuntimeError("supplement actual argv differs from the reviewed v03 capability wrapper command")
    if plan.get("old_argv") != [
        "/usr/bin/python3", "scripts/run-joern-common-v092.py", "execute", "--plan",
        "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json", "--output",
        "reports/raw/joern-common-v2/current108-v092-01",
    ]:
        raise RuntimeError("historical frozen argv was changed")
    if plan.get("prior_preparation_failures") != _failed_preparation_bindings():
        raise RuntimeError("both zero-analyzer preparation failure inventories must remain exactly bound")
    source_projection = plan.get("source_projection")
    expected_plan_inputs = [plan.get("qualified_execution_plan"), plan.get("pending_execution_plan")]
    if (not isinstance(source_projection, dict)
            or source_projection.get("source_path") != SOURCE_RELATIVE
            or source_projection.get("execution_plan_inputs") != expected_plan_inputs
            or not isinstance(source_projection.get("additional_paths"), list)
            or not set(item["path"] for item in expected_plan_inputs) <= set(source_projection["additional_paths"])
            or not isinstance(source_projection.get("supplement_files_to_copy"), list)):
        raise RuntimeError("prepared source must bind and include both exact v03 plan files")
    group = plan.get("group")
    if (not isinstance(group, dict) or group.get("id") != GROUP_ID
            or group.get("family") != "joern" or group.get("kind") != "cold"
            or group.get("status") != "ready" or group.get("argv") != plan["argv"]
            or group.get("maximum_attempts") != 1 or group.get("automatic_retry") is not False
            or group.get("output_roots") != [OUTPUT_RELATIVE]
            or group.get("runtime_ids") != ["java-home", "joern-root", "swift-sdk", "swift-toolchain"]):
        raise RuntimeError("supplement group descriptor differs from its sole qualified Joern command")
    group_ids = group.get("case_ids")
    reports = group.get("reports")
    if (not isinstance(group_ids, list) or len(group_ids) != CASE_COUNT
            or len(set(group_ids)) != CASE_COUNT or not isinstance(reports, list)
            or len(reports) != REPORT_PARTITION_COUNT):
        raise RuntimeError("supplement group must preserve 108 unique cases and five report partitions")
    capability_binding = plan.get("capability_binding")
    expected_capability = {
        "identity_gate": "exact-native-edges",
        "model_mode": "off",
        "model_status": "unqualified",
    }
    capabilities = capability_binding.get("capabilities") if isinstance(capability_binding, dict) else None
    unsupported_decisions = capability_binding.get("unsupported_decisions") if isinstance(capability_binding, dict) else None
    historical_unsupported = (capability_binding.get("historical_unsupported_decisions")
                              if isinstance(capability_binding, dict) else None)
    if (not isinstance(capability_binding, dict)
            or set(capability_binding) != {"schema", "source", "capabilities", "unsupported_decisions",
                                           "historical_unsupported_decisions", "attempt_count",
                                           "unsupported_count"}
            or capability_binding.get("schema") != "joern-v092-capability-binding/v2"
            or capability_binding.get("source") != {
                "path": CAPABILITY_SOURCE_PATH, "sha256": CAPABILITY_SOURCE_SHA256,
            }
            or capability_binding.get("attempt_count") != 96
            or capability_binding.get("unsupported_count") != 12
            or not isinstance(capabilities, dict) or len(capabilities) != 96
            or not isinstance(unsupported_decisions, dict) or len(unsupported_decisions) != 12
            or not isinstance(historical_unsupported, dict) or len(historical_unsupported) != 12
            or set(capabilities) & set(unsupported_decisions)
            or set(capabilities) | set(unsupported_decisions) != set(group_ids)
            or set(historical_unsupported) != set(unsupported_decisions)
            or plan.get("unsupported_decisions") != unsupported_decisions
            or any(not isinstance(case_id, str) or value != expected_capability
                   for case_id, value in capabilities.items())):
        raise RuntimeError("supplement must bind all 96 exact capabilities and both provenance sets for 12 declines")
    for case_id, decision in unsupported_decisions.items():
        if (not isinstance(case_id, str) or not isinstance(decision, dict)
                or set(decision) != {"path", "sha256"}
                or decision.get("path") != (
                    f"adapters/joern/swift-common-v2/plan-v092-03/unsupported-dispositions-02/{case_id}.json")
                or not isinstance(decision.get("sha256"), str)
                or len(decision["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in decision["sha256"])):
            raise RuntimeError("supplement unsupported capability decision references are malformed")
    for case_id, decision in historical_unsupported.items():
        if (not isinstance(case_id, str) or not isinstance(decision, dict)
                or set(decision) != {"path", "sha256"}
                or not isinstance(decision.get("path"), str)
                or not decision["path"].startswith("adapters/joern/swift-common-v2/plan-v090-01/")
                or not isinstance(decision.get("sha256"), str)
                or len(decision["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in decision["sha256"])):
            raise RuntimeError("supplement historical unsupported decision references are malformed")
    if plan.get("failure_policy") != {
            "path": PROJECTION_RECOVERY_AUTHORIZATION_PATH,
            "sha256": PROJECTION_RECOVERY_AUTHORIZATION_SHA256}:
        raise RuntimeError("supplement must retain the exact unsupported disposition failure policy")
    projection_exporter = plan.get("projection_exporter")
    configuration_hash_helper = plan.get("configuration_hash_helper")
    if (not isinstance(projection_exporter, dict)
            or projection_exporter.get("path") != CAPABILITY_V3_REPORTER_PATH
            or not isinstance(configuration_hash_helper, dict)
            or configuration_hash_helper.get("path")
            != "scripts/joern_normal_reports_v092_projection.py"):
        raise RuntimeError("report projection exporter and delegated configuration hash helper are misidentified")
    report_ids = []
    for index, report in enumerate(reports):
        if (report.get("source_path") != f"{OUTPUT_RELATIVE}/normal/report-{index}.json"
                or not isinstance(report.get("case_ids"), list) or not report["case_ids"]):
            raise RuntimeError("supplement report path or partition membership is malformed")
        report_ids.extend(report["case_ids"])
    if len(report_ids) != CASE_COUNT or len(set(report_ids)) != CASE_COUNT or set(report_ids) != set(group_ids):
        raise RuntimeError("five supplement partitions do not cover the exact 108-case group")
    expected_environment = {
        "HOME": "@SUPPLEMENT_SOURCE@/home", "TMPDIR": "@SUPPLEMENT_SOURCE@/tmp",
        "PATH": PARENT_GROUP_PATH, "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1", "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
        "DATAFLOWBENCH_V092_GROUP_ID": GROUP_ID,
    }
    if (plan.get("environment") != expected_environment
            or plan.get("group", {}).get("environment") != expected_environment):
        raise RuntimeError("supplement child environment is not isolated and explicitly bound")
    if plan.get("deadline_seconds") != GROUP_TIMEOUT_SECONDS:
        raise RuntimeError("supplement timeout differs from the frozen 1368-second deadline")
    if plan.get("max_campaign_wall_seconds") != MAX_CAMPAIGN_WALL_SECONDS:
        raise RuntimeError("supplement campaign wall bound differs from the retained 48-hour limit")
    resources = plan.get("resources")
    expected_resources = {
        "launch_free_gib": 127, "continuous_free_gib": 125,
        "per_source_gib": 12, "working_source_gib": 30,
        "scratch_gib": 24, "retention_gib": 24,
        "serial_analyzers": 1, "automatic_retry": False,
    }
    if resources != expected_resources:
        raise RuntimeError("supplement resource policy differs from the authorized bounded envelope")
    resource_scope = plan.get("resource_scope")
    expected_start_paths = [
        f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        for campaign_id in RESOURCE_CAMPAIGN_IDS
    ]
    if (not isinstance(resource_scope, dict)
            or resource_scope.get("resource_campaign_ids") != list(RESOURCE_CAMPAIGN_IDS)
            or resource_scope.get("parent_checkpoint") != {
                "path": RESOURCE_PARENT_CHECKPOINT_PATH,
                "sha256": RESOURCE_PARENT_CHECKPOINT_SHA256,
            }
            or not isinstance(resource_scope.get("campaign_start_references"), list)
            or [row.get("path") for row in resource_scope["campaign_start_references"]
                if isinstance(row, dict)] != expected_start_paths
            or len(resource_scope["campaign_start_references"]) != len(expected_start_paths)):
        raise RuntimeError("resource scope must bind all four ancestor starts and the exact parent checkpoint")
    expected_bound_refs = {
        "observer_profile": {"path": RESOURCE_PROFILE_PATH, "sha256": RESOURCE_PROFILE_SHA256},
        "closed_process_ownership": {
            "path": RESOURCE_OWNER_RECEIPT_PATH, "sha256": RESOURCE_OWNER_RECEIPT_SHA256,
        },
        "portability_preflight": {
            "path": PORTABILITY_RECEIPT_PATH, "sha256": PORTABILITY_RECEIPT_SHA256,
        },
    }
    expected_closed_preparation_roots = {
        "working": [f"{ROOT}/{FAILED_PREPARATION_SOURCE}",
                    f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}",
                    f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}",
                    f"{ROOT}/{FAILED_WRAPPER_SOURCE}",
                    f"{ROOT}/{FAILED_CAPABILITY_SOURCE}", f"{ROOT}/{LAUNCHER_SMOKE_ROOT}"],
        "retention": [f"{ROOT}/{FAILED_PREPARATION_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_04_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}/reports",
                      f"{ROOT}/{FAILED_PREPARATION_05_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}/reports",
                      f"{ROOT}/{FAILED_WRAPPER_REPORT}", f"{ROOT}/{FAILED_WRAPPER_SOURCE}/reports",
                      f"{ROOT}/{FAILED_CAPABILITY_REPORT}",
                      f"{ROOT}/{FAILED_CAPABILITY_SOURCE}/reports"],
        "scratch": [
            *(f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}/{name}" for name in ("home", "tmp", "cache")),
            *(f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}/{name}" for name in ("home", "tmp", "cache")),
            *(f"{ROOT}/{FAILED_WRAPPER_SOURCE}/{name}" for name in ("home", "tmp", "cache")),
            *(f"{ROOT}/{FAILED_CAPABILITY_SOURCE}/{name}" for name in ("home", "tmp", "cache")),
            f"{ROOT}/{LAUNCHER_SMOKE_ROOT}",
        ],
    }
    expected_post_profile_additions = [dict(row) for row in POST_PROFILE_RETAINED_ADDITIONS]
    expected_profile_parent_bytes = {"working": 19073573545, "retention": 630366349,
                                     "scratch": 3198936017}
    expected_current_parent_bytes = dict(expected_profile_parent_bytes)
    expected_current_parent_bytes["retention"] += sum(
        row["size_bytes"] for row in expected_post_profile_additions)
    if (resource_scope.get("observer_method") != RESOURCE_OBSERVER_METHOD
            or any(resource_scope.get(key) != reference for key, reference in expected_bound_refs.items())
            or resource_scope.get("profile_expected_parent_baseline_bytes") != expected_profile_parent_bytes
            or resource_scope.get("post_profile_retained_additions") != expected_post_profile_additions
            or resource_scope.get("closed_process_ownership_state") != {
                "recorded_process_identities": 118, "same_identities_still_alive": 0,
                "command_records": 37, "serial_lock_available": True,
                "descendant_containment": "unproven",
            }
            or resource_scope.get("expected_parent_baseline_bytes") != expected_current_parent_bytes):
        raise RuntimeError("resource observer method or immutable provenance bindings changed")
    if resource_scope.get("closed_preparation_roots") != expected_closed_preparation_roots:
        raise RuntimeError("both failed preparation source/report/scratch roots must remain fully accounted")
    for reference in [*resource_scope["campaign_start_references"], resource_scope["parent_checkpoint"],
                      *expected_bound_refs.values(),
                      *[{"path": row["path"], "sha256": row["sha256"]}
                        for row in expected_post_profile_additions]]:
        if (not isinstance(reference, dict) or set(reference) != {"path", "sha256"}
                or not isinstance(reference.get("sha256"), str)
                or len(reference["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in reference["sha256"])):
            raise RuntimeError("resource ancestry reference is malformed")
    expected_roots = [
        f"{ROOT}/execution-state/timing-v092-{campaign_id}/sources"
        for campaign_id in RESOURCE_CAMPAIGN_IDS
    ]
    roots = resource_scope.get("inherited_source_roots")
    working = resource_scope.get("working")
    retained = resource_scope.get("retained")
    scratch = resource_scope.get("scratch")
    categories = ("working", "retention", "scratch")
    baseline_paths = resource_scope.get("baseline_paths")
    preparation_paths = resource_scope.get("preparation_paths")
    active_paths = resource_scope.get("active_paths")
    exact_preparation = {
        "working": [f"{ROOT}/{PORTABILITY_SOURCE_PATH}", f"{ROOT}/{QUALIFICATION_WORK_ROOT}",
                    f"{ROOT}/{FAILED_PREPARATION_SOURCE}", f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}",
                    f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}", f"{ROOT}/{FAILED_WRAPPER_SOURCE}",
                    f"{ROOT}/{FAILED_CAPABILITY_SOURCE}", f"{ROOT}/{LAUNCHER_SMOKE_ROOT}"],
        "retention": [f"{ROOT}/{PREPARATION_ROOT}", f"{ROOT}/{FAILED_PREPARATION_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_04_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}/reports",
                      f"{ROOT}/{FAILED_PREPARATION_05_REPORT}",
                      f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}/reports",
                      f"{ROOT}/{FAILED_WRAPPER_REPORT}", f"{ROOT}/{FAILED_WRAPPER_SOURCE}/reports",
                      f"{ROOT}/{FAILED_CAPABILITY_REPORT}",
                      f"{ROOT}/{FAILED_CAPABILITY_SOURCE}/reports"],
        "scratch": [f"{ROOT}/{QUALIFICATION_CONTROL_SCRATCH}",
                    *[f"{ROOT}/{QUALIFICATION_WORK_ROOT}/{name}" for name in ("home", "tmp", "cache")],
                    *[f"{ROOT}/{FAILED_PREPARATION_04_SOURCE}/{name}"
                      for name in ("home", "tmp", "cache")],
                    *[f"{ROOT}/{FAILED_PREPARATION_05_SOURCE}/{name}"
                      for name in ("home", "tmp", "cache")],
                    *[f"{ROOT}/{FAILED_WRAPPER_SOURCE}/{name}"
                      for name in ("home", "tmp", "cache")],
                    *[f"{ROOT}/{FAILED_CAPABILITY_SOURCE}/{name}"
                      for name in ("home", "tmp", "cache")],
                    f"{ROOT}/{LAUNCHER_SMOKE_ROOT}"],
    }
    exact_active = {
        "working": [f"{ROOT}/{SOURCE_RELATIVE}"],
        "retention": [f"{ROOT}/{REPORT_ROOT}", f"{ROOT}/{SOURCE_RELATIVE}/reports"],
        "scratch": [f"{ROOT}/{SOURCE_RELATIVE}/{name}" for name in ("home", "tmp", "cache")],
    }
    paths_valid = isinstance(baseline_paths, dict) and isinstance(preparation_paths, dict) \
        and isinstance(active_paths, dict)
    if paths_valid:
        paths_valid = all(
            isinstance(baseline_paths.get(category), list) and baseline_paths[category]
            and isinstance(preparation_paths.get(category), list)
            and preparation_paths[category] == exact_preparation[category]
            and isinstance(active_paths.get(category), list)
            and active_paths[category] == exact_active[category]
            for category in categories
        )
    if paths_valid:
        paths_valid = all(
            isinstance(value, str) and Path(value).is_absolute()
            and Path(value).resolve(strict=False) == Path(value)
            for category in categories
            for paths in (baseline_paths[category], preparation_paths[category], active_paths[category])
            for value in paths
        )
    if paths_valid:
        paths_valid = baseline_paths["working"] == expected_roots
    expected_full = {}
    if paths_valid:
        for category, total in (("working", working), ("retention", retained), ("scratch", scratch)):
            expected_full[category] = {str(Path(item)) for item in (
                *baseline_paths[category], *preparation_paths[category], *active_paths[category])}
            _assert_disjoint_resource_paths(
                [Path(item) for item in baseline_paths[category]],
                [Path(item) for item in preparation_paths[category]], category)
            _assert_disjoint_resource_paths(
                [Path(item) for item in baseline_paths[category]],
                [Path(item) for item in active_paths[category]], category)
            _assert_disjoint_resource_paths(
                [Path(item) for item in preparation_paths[category]],
                [Path(item) for item in active_paths[category]], category)
    if (roots != expected_roots or not isinstance(working, list) or not isinstance(retained, list)
            or not isinstance(scratch, list)
            or not set(expected_roots) <= set(working)
            or not paths_valid
            or any(not isinstance(paths, list) or not paths for paths in (working, retained, scratch))
            or any(not isinstance(value, str) or not Path(value).is_absolute()
                   or Path(value).resolve(strict=False) != Path(value)
                   for paths in (working, retained, scratch, *[baseline_paths[c] for c in categories],
                                 *[preparation_paths[c] for c in categories],
                                 *[active_paths[c] for c in categories]) for value in paths)
            or any({str(Path(value)) for value in total} != expected_full[category]
                   for category, total in (("working", working), ("retention", retained),
                                           ("scratch", scratch)))):
        raise RuntimeError("resource accounting must include normalized four-ancestor, retention, and scratch paths")
    if plan.get("publication_eligible") is not False or plan.get("scored_activation") is not False:
        raise RuntimeError("supplement can never assert score or publication eligibility")
    if plan.get("diagnostic_execution_eligible") is not True or plan.get("full_model_qualification") is not False:
        raise RuntimeError("diagnostic execution must remain separate from incomplete full-model qualification")
    if plan.get("original_a24_settled_qualification_eligible") is not False:
        raise RuntimeError("the original A24 settled qualification must remain false")
    if plan.get("active_cpu_policy") != "record-and-continue" or plan.get("retry_policy") != "none":
        raise RuntimeError("active CPU telemetry must not abort or retry this invocation")
    admission = plan.get("admission_policy")
    if admission != _diagnostic_admission_policy():
        raise RuntimeError("diagnostic admission policy or its non-certification limits changed")
    if plan.get("diagnostic_authorization") != {
            "path": DIAGNOSTIC_AUTHORIZATION_PATH,
            "sha256": DIAGNOSTIC_AUTHORIZATION_SHA256,
            "authorization": "user-authorized-diagnostic-continuation",
    }:
        raise RuntimeError("diagnostic continuation authorization binding changed")
    committed_inputs = plan.get("committed_code_inputs")
    if (not isinstance(committed_inputs, dict)
            or committed_inputs.get(DIAGNOSTIC_AUTHORIZATION_PATH) != DIAGNOSTIC_AUTHORIZATION_SHA256
            or committed_inputs.get(LAUNCHER_RECOVERY_AUTHORIZATION_PATH)
            != LAUNCHER_RECOVERY_AUTHORIZATION_SHA256
            or committed_inputs.get(CAPABILITY_RECOVERY_AUTHORIZATION_PATH)
            != CAPABILITY_RECOVERY_AUTHORIZATION_SHA256
            or committed_inputs.get(UNSUPPORTED_PROVENANCE_AUTHORIZATION_PATH)
            != UNSUPPORTED_PROVENANCE_AUTHORIZATION_SHA256
            or committed_inputs.get(PROJECTION_RECOVERY_AUTHORIZATION_PATH)
            != PROJECTION_RECOVERY_AUTHORIZATION_SHA256):
        raise RuntimeError("diagnostic authorization must remain a committed, hash-bound plan input")
    if plan.get("launcher_recovery_authorization") != {
            "path": LAUNCHER_RECOVERY_AUTHORIZATION_PATH,
            "sha256": LAUNCHER_RECOVERY_AUTHORIZATION_SHA256,
            "authorization": "user-authorized-diagnostic-continuation",
    }:
        raise RuntimeError("launcher recovery authorization binding changed")
    if plan.get("capability_recovery_authorization") != {
            "path": CAPABILITY_RECOVERY_AUTHORIZATION_PATH,
            "sha256": CAPABILITY_RECOVERY_AUTHORIZATION_SHA256,
            "authorization": "user-authorized-diagnostic-continuation",
    }:
        raise RuntimeError("capability recovery authorization binding changed")
    if plan.get("unsupported_provenance_authorization") != {
            "path": UNSUPPORTED_PROVENANCE_AUTHORIZATION_PATH,
            "sha256": UNSUPPORTED_PROVENANCE_AUTHORIZATION_SHA256,
            "authorization": "user-authorized-diagnostic-continuation",
    }:
        raise RuntimeError("unsupported-case provenance authorization binding changed")
    if plan.get("projection_recovery_authorization") != {
            "path": PROJECTION_RECOVERY_AUTHORIZATION_PATH,
            "sha256": PROJECTION_RECOVERY_AUTHORIZATION_SHA256,
            "authorization": "user-authorized-diagnostic-continuation",
    }:
        raise RuntimeError("report projection recovery authorization binding changed")
    if plan.get("launcher_prerequisite_preflight") != _launcher_preflight_binding():
        raise RuntimeError("launcher dependency or positive version-only preflight binding changed")
    prior_wrapper_failure = plan.get("prior_wrapper_failure")
    expected_wrapper_failure = {
        "schema": "v092-swift-closed-wrapper-failure/v1",
        "campaign_id": "20261122-06",
        "classification": "wrapper-launcher-path-dependency-failure",
        "inventory": {"path": FAILED_WRAPPER_INVENTORY,
                       "sha256": FAILED_WRAPPER_INVENTORY_SHA256},
        "wrapper_invocations": 1, "identity_phase_invocations": 1,
        "analysis_phase_invocations": 0, "benchmark_case_rows": 0,
        "exit_code": 1, "timed_out": False, "capacity_loss": None,
        "run_json_status": "absent", "version_discovery_complete": False,
        "inner_cleanup_status": "uncertain",
        "inner_cleanup_error": "process tracking failed: invocation root start identity was never captured",
        "outer_cleanup_status": "tracked-processes-stopped", "outer_signals_sent": [],
        "descendant_containment": "unproven", "automatic_retry": False,
        "publication_eligible": False,
    }
    if not isinstance(prior_wrapper_failure, dict) or any(
            prior_wrapper_failure.get(key) != value for key, value in expected_wrapper_failure.items()):
        raise RuntimeError("typed campaign 06 wrapper failure must retain its invocation and uncertainty")
    expected_refs = {
        "campaign_start": f"{FAILED_WRAPPER_REPORT}/campaign-start.json",
        "campaign_terminal": f"{FAILED_WRAPPER_REPORT}/campaign-terminal.json",
        "attempt_start": f"{FAILED_WRAPPER_REPORT}/attempts/{GROUP_ID}/attempt-01/start.json",
        "attempt_terminal": f"{FAILED_WRAPPER_REPORT}/attempts/{GROUP_ID}/attempt-01/terminal.json",
        "version_command": f"{FAILED_WRAPPER_VERSION_DIR}/version.command.json",
        "version_stdout": f"{FAILED_WRAPPER_VERSION_DIR}/version.stdout",
        "version_stderr": f"{FAILED_WRAPPER_VERSION_DIR}/version.stderr",
    }
    for key, relative in expected_refs.items():
        reference = prior_wrapper_failure.get(key)
        if (not isinstance(reference, dict) or reference.get("path") != relative
                or not isinstance(reference.get("sha256"), str) or len(reference["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in reference["sha256"])):
            raise RuntimeError("typed campaign 06 wrapper failure lost a retained evidence reference")
    for key in ("elapsed_seconds", "command_elapsed_seconds", "version_elapsed_seconds"):
        if (type(prior_wrapper_failure.get(key)) not in {int, float}
                or not math.isfinite(prior_wrapper_failure[key]) or prior_wrapper_failure[key] <= 0):
            raise RuntimeError("typed campaign 06 wrapper failure lost its execution cost")
    prior_capability_failure = plan.get("prior_capability_failure")
    expected_capability_failure = {
        "schema": "v092-swift-closed-capability-failure/v1",
        "campaign_id": "20261122-07",
        "classification": "missing-explicit-capability-before-case-analysis",
        "inventory": {"path": FAILED_CAPABILITY_INVENTORY,
                       "sha256": FAILED_CAPABILITY_INVENTORY_SHA256},
        "wrapper_invocations": 1, "identity_phase_invocations": 1,
        "analysis_phase_invocations": 0, "benchmark_case_rows": 0,
        "version_invocations": 1, "exit_code": 1, "timed_out": False,
        "capacity_loss": None, "run_json_status": "absent", "version_exit_status": 0,
        "version_cleanup_status": "tracked-processes-stopped",
        "version_cleanup_signaled": [], "outer_cleanup_status": "tracked-processes-stopped",
        "outer_signals_sent": [], "inner_cleanup_status": "tracked-processes-stopped",
        "descendant_containment": "unproven", "automatic_retry": False,
        "publication_eligible": False,
    }
    if not isinstance(prior_capability_failure, dict) or any(
            prior_capability_failure.get(key) != value
            for key, value in expected_capability_failure.items()):
        raise RuntimeError("typed campaign 07 capability failure must retain version success and zero case analysis")
    expected_capability_refs = {
        "campaign_start": f"{FAILED_CAPABILITY_REPORT}/campaign-start.json",
        "campaign_terminal": f"{FAILED_CAPABILITY_REPORT}/campaign-terminal.json",
        "launch_failure": f"{FAILED_CAPABILITY_REPORT}/launch-failure-001.json",
        "attempt_start": f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01/start.json",
        "attempt_terminal": f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01/terminal.json",
        "attempt_stdout": f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01/stdout.txt",
        "attempt_stderr": f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01/stderr.txt",
        "version_command": f"{FAILED_CAPABILITY_VERSION_DIR}/version.command.json",
        "version_stdout": f"{FAILED_CAPABILITY_VERSION_DIR}/version.stdout",
        "version_stderr": f"{FAILED_CAPABILITY_VERSION_DIR}/version.stderr",
        "identity": f"{FAILED_CAPABILITY_VERSION_DIR}/identity.json",
    }
    for key, relative in expected_capability_refs.items():
        reference = prior_capability_failure.get(key)
        if (not isinstance(reference, dict) or reference.get("path") != relative
                or not isinstance(reference.get("sha256"), str) or len(reference["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in reference["sha256"])):
            raise RuntimeError("typed campaign 07 capability failure lost a retained evidence reference")
    for key in ("elapsed_seconds", "command_elapsed_seconds", "version_elapsed_seconds"):
        if (type(prior_capability_failure.get(key)) not in {int, float}
                or not math.isfinite(prior_capability_failure[key])
                or prior_capability_failure[key] <= 0):
            raise RuntimeError("typed campaign 07 capability failure lost its invocation cost")
    provenance = plan.get("configuration_provenance")
    if (not isinstance(provenance, dict)
            or provenance.get("schema") != "v092-swift-supplement-configuration-provenance/v1"
            or provenance.get("removed_paths") != []
            or provenance.get("approved_additions") != sorted(APPROVED_CONFIGURATION_ADDITIONS)
            or provenance.get("publication_eligible") is not False):
        raise RuntimeError("configuration closure transition is not explicitly retained and bounded")
    uncertainty = plan.get("semantic_uncertainty")
    if (not isinstance(uncertainty, dict)
            or uncertainty.get("schema") != "joern-swift-semantic-uncertainty/v1"
            or uncertainty.get("decision_id") != MODEL_LIMIT_DECISION_ID
            or uncertainty.get("classification") != "strict-model-qualification-incomplete"
            or uncertainty.get("strict_model_qualification", {}).get("status") != "incomplete"
            or uncertainty.get("strict_model_qualification", {}).get("full_model_qualification") is not False
            or uncertainty.get("diagnostic_execution", {}).get("status") != "measurement-with-known-limits"
            or uncertainty.get("diagnostic_execution", {}).get("scored_activation") is not False
            or uncertainty.get("normalized_report_match_is_model_certificate") is not False
            or uncertainty.get("publication_eligible") is not False):
        raise RuntimeError("known Joern endpoint-identity uncertainty must remain explicit and unqualified")


def assess_admission(observation: dict, host, *, root_pid: int | None = None) -> dict:
    """Assess one raw observation without changing it or adjusting aggregate CPU."""
    if not host._valid_snapshot(observation):
        raise ValueError("admission requires a complete raw host observation")
    service_rows = observation.get("service_observations", [])
    quiescent_service_pids = observation.get("quiescent_service_pids", [])
    if not isinstance(service_rows, list) or not isinstance(quiescent_service_pids, list):
        raise ValueError("legacy observer service metadata is malformed")
    observer_proven = []
    for row in service_rows:
        if not isinstance(row, dict) or type(row.get("pid")) is not int:
            raise ValueError("legacy observer service identity is malformed")
        if row.get("unchanged_idle_service") is True:
            argv = row.get("argv")
            if (not isinstance(argv, list) or not argv or Path(argv[0]).name != "bifrost"
                    or any(not isinstance(arg, str) for arg in argv)
                    or not ({"--mcp", "--lsp"} & set(argv[1:]))
                    or not isinstance(row.get("start_identity"), str) or not row["start_identity"]
                    or row.get("cpu_percent") != 0.0 or row.get("descendants") != []
                    or not isinstance(row.get("cpu_time"), str)):
                raise ValueError("legacy observer marked a service idle without the exact identity proof")
            observer_proven.append(row["pid"])
    if (any(type(pid) is not int or pid <= 0 for pid in quiescent_service_pids)
            or len(set(quiescent_service_pids)) != len(quiescent_service_pids)
            or quiescent_service_pids != observer_proven):
        raise ValueError("quiescent service PID list differs from Observer-proven service identities")
    owned: set[int] = set()
    if root_pid is not None:
        owned = set(host.process_tree_pids(observation, root_pid)) if hasattr(host, "process_tree_pids") else set()
        # Reuse the release executor's PID/parent traversal when the host API
        # does not expose a tree helper; exact tolerated paths never inherit.
        if not owned:
            parent_map: dict[int, list[int]] = {}
            for process in observation["processes"]:
                parent_map.setdefault(int(process["ppid"]), []).append(int(process["pid"]))
            pending, owned = [root_pid], {root_pid}
            while pending:
                for child in parent_map.get(pending.pop(), []):
                    if child not in owned:
                        owned.add(child)
                        pending.append(child)
    tolerated = set(TOLERATED_COMM_PATHS)
    heavy = []
    external_cpu = 0.0
    tolerated_rows = []
    for process in observation["processes"]:
        pid = int(process["pid"])
        comm = process["comm"]
        if pid in owned or pid in quiescent_service_pids:
            continue
        if comm in tolerated:
            tolerated_rows.append({"pid": pid, "comm": comm, "cpu_percent": process["cpu_percent"]})
            continue
        external_cpu += float(process["cpu_percent"])
        if host._is_heavy_process(comm):
            heavy.append({"pid": pid, "comm": comm, "cpu_percent": process["cpu_percent"]})
    logical = int(observation["hardware"]["logical_cpus"])
    significant = external_cpu >= logical * 10.0
    aggregate_idle_ok = float(observation["cpu_idle_percent"]) >= QUIET_IDLE_PERCENT
    quiet = aggregate_idle_ok and not heavy and not significant
    diagnostic_admissible = not heavy and not significant
    return {
        "schema": "v092-swift-supplement-admission-assessment/v1",
        "aggregate_cpu_idle_percent_raw": observation["cpu_idle_percent"],
        "aggregate_cpu_idle_threshold_percent": QUIET_IDLE_PERCENT,
        "aggregate_cpu_adjusted": False,
        "tolerated_background": tolerated_rows,
        "tolerated_comm_paths": list(TOLERATED_COMM_PATHS),
        "quiescent_service_recognition": QUIESCENT_SERVICE_RECOGNITION,
        "quiescent_service_pids": list(quiescent_service_pids),
        "service_observations": service_rows,
        "non_tolerated_heavy_processes": heavy,
        "non_tolerated_external_cpu_percent": external_cpu,
        "significant_external_cpu": significant,
        "observation_complete": True,
        "quiet": quiet,
        "diagnostic_background_admissible": diagnostic_admissible,
        "settled_quiet_window_established": False,
        "owned_process_ids_excluded": sorted(owned),
        "original_a24_settled_qualification_eligible": False,
        "publication_eligible": False,
    }


class _AdmissionHostFacade:
    """Use the campaign's existing service observer while preserving host APIs."""

    def __init__(self, host, observer):
        self.host = host
        self.observer = observer

    def snapshot(self, root: Path | None = None):
        if root is not None and Path(root).resolve() != ROOT.resolve():
            raise RuntimeError("admission observer was asked to sample outside the campaign root")
        return self.observer.snapshot()

    def __getattr__(self, name):
        return getattr(self.host, name)


def _admission_host(root: Path, host, legacy=None):
    if legacy is None:
        legacy = _qualified_module(root).legacy
    observer = legacy.Observer(host)
    return _AdmissionHostFacade(host, observer)


class QuietAdmissionWindow:
    """Track a 300-second complete, quiet window with a strict 45-second gap."""

    def __init__(self, required_seconds: float = QUIET_SECONDS,
                 max_gap_seconds: float = MAX_SAMPLE_GAP_SECONDS):
        self.required_seconds = required_seconds
        self.max_gap_seconds = max_gap_seconds
        self.started: float | None = None
        self.previous: float | None = None
        self.samples = 0

    def reset(self) -> None:
        self.started = None
        self.previous = None
        self.samples = 0

    def observe(self, assessment: dict, monotonic_seconds: float) -> bool:
        if not assessment.get("quiet") or not isinstance(monotonic_seconds, (int, float)):
            self.reset()
            return False
        current = float(monotonic_seconds)
        if self.previous is not None and (current <= self.previous or current - self.previous > self.max_gap_seconds):
            self.reset()
        if self.started is None:
            self.started = current
        self.previous = current
        self.samples += 1
        return current - self.started >= self.required_seconds

    @property
    def elapsed_seconds(self) -> float:
        return 0.0 if self.started is None or self.previous is None else self.previous - self.started


def _component_manifest_references(root: Path, plan: dict) -> dict:
    references = {}
    for component in plan["identity_components"]:
        if component.get("kind") != "runtime-tree-manifest" or component["name"] in references:
            raise RuntimeError("runtime component identity kind or membership changed")
        try:
            relative = Path(component["path"]).relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise RuntimeError("runtime component manifest escapes its canonical capture repository") from exc
        reference = {"path": relative, "sha256": component["sha256"]}
        _validate_reference(root, reference)
        references[component["name"]] = reference
    if set(references) != {"swift-toolchain", "java-home", "joern-root", "swift-sdk"}:
        raise RuntimeError("qualified Joern plan lacks the exact four runtime component manifests")
    return references


def _base_plan(root: Path, base_group: dict, final_plan: dict, evidence: dict,
               closure: dict[str, str], resource_scope: dict, committed_inputs: dict[str, str],
               configuration_provenance: dict, postprocessing_dependencies: list[dict],
               prior_wrapper_failure: dict, prior_capability_failure: dict,
               capability_binding: dict,
               created_utc: str) -> dict:
    group = _validate_group_and_command(final_plan, base_group)
    helper_refs = {relative: sha(_repo_file(root, relative)) for relative in HELPER_PATHS}
    control_ref = final_plan.get("qualification_control_plan")
    control = _read_json(_validate_reference(root, control_ref))
    admission = control.get("diagnostic_admission")
    if not isinstance(admission, dict):
        raise RuntimeError("qualified Joern plan lost its bounded semantic-admission descriptor")
    strict_model = admission.get("strict_model_qualification")
    diagnostic_execution = admission.get("diagnostic_execution")
    if (admission.get("decision_id") != MODEL_LIMIT_DECISION_ID
            or not isinstance(strict_model, dict) or strict_model.get("status") != "incomplete"
            or strict_model.get("full_model_qualification") is not False
            or not isinstance(diagnostic_execution, dict)
            or diagnostic_execution.get("status") != "measurement-with-known-limits"
            or diagnostic_execution.get("scored_activation") is not False):
        raise RuntimeError("Joern endpoint-identity uncertainty changed or was removed")
    semantic_uncertainty = {
        "schema": "joern-swift-semantic-uncertainty/v1",
        "decision_id": admission["decision_id"],
        "classification": "strict-model-qualification-incomplete",
        "strict_model_qualification": strict_model,
        "diagnostic_execution": diagnostic_execution,
        "normalized_report_match_is_model_certificate": False,
        "publication_eligible": False,
    }
    runtime_components = _component_manifest_references(root, final_plan)
    group_report_bindings = final_plan.get("frozen_report_bindings")
    # The v02 execution plan may not duplicate old campaign comparison refs;
    # preserve the original frozen comparison bindings as a separate lineage.
    frozen_bindings = _read_json(_repo_file(root, BASE_PLAN_PATH)).get("frozen_report_bindings", {}).get(GROUP_ID)
    if not isinstance(frozen_bindings, list) or len(frozen_bindings) != REPORT_PARTITION_COUNT:
        raise RuntimeError("parent plan lost its five frozen Joern report bindings")
    if group_report_bindings is not None and group_report_bindings.get(GROUP_ID) not in (None, frozen_bindings):
        raise RuntimeError("v02 plan attempts to redefine frozen report comparison bindings")
    old_group = json.loads(json.dumps(base_group))
    actual_argv = group["argv"]
    qualified_plan_ref = _reference(root, QUALIFIED_PLAN_PATH)
    pending_plan_ref = _reference(root, PENDING_PLAN_PATH)
    plan = {
        "schema": "v092-timing-swift-supplement-plan/v1",
        "campaign_id": CAMPAIGN_ID,
        "created_utc": created_utc,
        "release_commit": RELEASE,
        "parent_group_count": 95,
        "parent_ready_frontier": [],
        "dispatch_groups": [GROUP_ID],
        "attempts_per_group": {GROUP_ID: 1},
        "group_id": GROUP_ID,
        "case_count": CASE_COUNT,
        "report_partition_count": REPORT_PARTITION_COUNT,
        "old_argv": old_group["argv"],
        "argv": actual_argv,
        "group": group,
        "environment": group["environment"],
        "frozen_report_bindings": frozen_bindings,
        "base_plan": {"path": BASE_PLAN_PATH, "sha256": BASE_PLAN_SHA256},
        "base_terminal": {"path": BASE_TERMINAL_PATH, "sha256": BASE_TERMINAL_SHA256},
        "diagnostic_authorization": {
            **_reference(root, DIAGNOSTIC_AUTHORIZATION_PATH),
            "authorization": "user-authorized-diagnostic-continuation",
        },
        "launcher_recovery_authorization": {
            **_reference(root, LAUNCHER_RECOVERY_AUTHORIZATION_PATH),
            "authorization": "user-authorized-diagnostic-continuation",
        },
        "capability_recovery_authorization": {
            **_reference(root, CAPABILITY_RECOVERY_AUTHORIZATION_PATH),
            "authorization": "user-authorized-diagnostic-continuation",
        },
        "unsupported_provenance_authorization": {
            **_reference(root, UNSUPPORTED_PROVENANCE_AUTHORIZATION_PATH),
            "authorization": "user-authorized-diagnostic-continuation",
        },
        "projection_recovery_authorization": {
            **_reference(root, PROJECTION_RECOVERY_AUTHORIZATION_PATH),
            "authorization": "user-authorized-diagnostic-continuation",
        },
        "launcher_prerequisite_preflight": _verify_launcher_preflight(root),
        "prior_wrapper_failure": prior_wrapper_failure,
        "prior_capability_failure": prior_capability_failure,
        "capability_binding": capability_binding,
        "unsupported_decisions": final_plan["unsupported_decisions"],
        "capture_inventory": {"path": BASE_INVENTORY_PATH, "sha256": BASE_INVENTORY_SHA256,
                              "file_count": 111},
        "semgrep_retrospective_audit": {"path": BASE_AUDIT_PATH, "sha256": BASE_AUDIT_SHA256,
                                        "status": "diagnostic-candidate-recovered",
                                        "original_controller_status": "failed"},
        "qualified_execution_plan": qualified_plan_ref,
        "pending_execution_plan": pending_plan_ref,
        "fresh_qualification": final_plan["fresh_qualification"],
        "qualification_evidence": evidence,
        "configuration_provenance": configuration_provenance,
        "failure_policy": final_plan["failure_policy"],
        "population_sha256": final_plan["population_sha256"],
        "case_disposition_counts": _case_disposition_counts(final_plan.get("cases")),
        "attempted_case_count": 96,
        "unsupported_case_count": 12,
        "diagnostic_execution_eligible": final_plan["diagnostic_execution_eligible"],
        "full_model_qualification": final_plan["full_model_qualification"],
        "semantic_uncertainty": semantic_uncertainty,
        "fixture_revision": final_plan["fixture_revision"],
        "runtime_component_manifests": runtime_components,
        "input_reference_closure": [{"path": path, "sha256": digest}
                                    for path, digest in sorted(closure.items())],
        "committed_code_inputs": committed_inputs,
        "execution_helpers": helper_refs,
        "postprocessing_dependencies": postprocessing_dependencies,
        "projection_exporter": _reference(root, CAPABILITY_V3_REPORTER_PATH),
        "configuration_hash_helper": _reference(
            root, "scripts/joern_normal_reports_v092_projection.py"),
        "source_projection": {
            "commit": RELEASE,
            "additional_paths": sorted({*closure, *(item["path"] for item in postprocessing_dependencies),
                                         qualified_plan_ref["path"], pending_plan_ref["path"]}),
            "source_path": SOURCE_RELATIVE,
            "execution_plan_inputs": [qualified_plan_ref, pending_plan_ref],
            "supplement_files_to_copy": [],
        },
        "resource_scope": resource_scope,
        "resources": {
            "launch_free_gib": 127,
            "continuous_free_gib": 125,
            "per_source_gib": 12,
            "working_source_gib": 30,
            "scratch_gib": 24,
            "retention_gib": 24,
            "serial_analyzers": 1,
            "automatic_retry": False,
        },
        "deadline_seconds": GROUP_TIMEOUT_SECONDS,
        "max_campaign_wall_seconds": MAX_CAMPAIGN_WALL_SECONDS,
        "admission_policy": _diagnostic_admission_policy(),
        "active_cpu_policy": "record-and-continue",
        "retry_policy": "none",
        "original_a24_settled_qualification_eligible": False,
        "timing_status": "diagnostic supplemental candidate; no settled quiet window; unqualified",
        "scored_activation": False,
        "publication_eligible": False,
    }
    plan["prior_preparation_failures"] = _failed_preparation_bindings()
    validate_campaign_plan(plan)
    return plan


def _supplement_files_to_copy(root: Path, closure: dict[str, str], legacy_core) -> list[dict]:
    missing_from_release = []
    for relative, digest in sorted(closure.items()):
        try:
            archived = legacy_core._git_show(root, RELEASE, relative)
        except Exception:
            archived = None
        if archived is not None:
            if _sha_bytes(archived) != digest:
                raise RuntimeError(f"qualified source input differs from frozen release bytes: {relative}")
        else:
            source_path = _repo_file(root, relative)
            missing_from_release.append({
                "path": relative, "sha256": digest,
                "source": str(source_path), "mode": stat.S_IMODE(source_path.stat().st_mode),
            })
    return missing_from_release


def _verify_failed_preparation(root: Path) -> list[dict]:
    bindings = _failed_preparation_bindings()
    for binding, report_root, source_root in zip(
            bindings,
            (FAILED_PREPARATION_REPORT, FAILED_PREPARATION_04_REPORT, FAILED_PREPARATION_05_REPORT),
            (FAILED_PREPARATION_SOURCE, FAILED_PREPARATION_04_SOURCE, FAILED_PREPARATION_05_SOURCE)):
        reference = binding["inventory"]
        inventory = _read_json(_validate_reference(root, reference))
        if (inventory.get("schema") != "v092-swift-preparation-failure-inventory/v1"
                or inventory.get("campaign_id") != binding["campaign_id"]
                or inventory.get("analyzer_invocations") != 0
                or inventory.get("file_count") != binding["file_count"]
                or inventory.get("total_bytes") != binding["total_bytes"]
                or inventory.get("source_error") != binding["source_error"]
                or not isinstance(inventory.get("files"), list)
                or len(inventory["files"]) != binding["file_count"]):
            raise RuntimeError(f"prior source preparation failure inventory changed: {binding['campaign_id']}")
        roots = [root / report_root, root / source_root]
        observed = set()
        for tree in roots:
            for path in tree.rglob("*"):
                if path.is_symlink():
                    raise RuntimeError("prior preparation acquired a symlink")
                if path.is_file():
                    observed.add(path.relative_to(root).as_posix())
        rows = inventory["files"]
        if (len({row.get("path") for row in rows if isinstance(row, dict)}) != len(rows)
                or observed != {row.get("path") for row in rows}
                or sum(row.get("size_bytes", -1) for row in rows if isinstance(row, dict))
                != inventory["total_bytes"]):
            raise RuntimeError(f"prior preparation membership changed: {binding['campaign_id']}")
        for row in rows:
            if (not isinstance(row, dict) or type(row.get("size_bytes")) is not int
                    or row["size_bytes"] < 0):
                raise RuntimeError("prior preparation inventory has a malformed file row")
            path = _validate_reference(root, {"path": row.get("path"), "sha256": row.get("sha256")})
            if path.stat().st_size != row["size_bytes"]:
                raise RuntimeError("prior preparation byte counts changed")
        terminal_path = root / report_root / "campaign-terminal.json"
        start_path = root / report_root / "campaign-start.json"
        terminal = _read_json(terminal_path)
        _read_json(start_path)
        failure = terminal.get("failure")
        attempt_start = root / report_root / f"attempts/{GROUP_ID}/attempt-01/start.json"
        if (terminal.get("campaign_id") != binding["campaign_id"]
                or terminal.get("status") != "blocked"
                or not isinstance(failure, dict) or failure.get("process_ownership") != {}
                or failure.get("error") != inventory["source_error"]
                or terminal.get("completed_groups") != []
                or terminal.get("execution_status") != "stopped-fail-closed"
                or inventory["analyzer_invocations"] != 0
                or attempt_start.exists() or attempt_start.is_symlink()):
            raise RuntimeError(f"prior campaign was not a zero-analyzer preparation failure: {binding['campaign_id']}")
    return bindings


def _verify_failed_wrapper_attempt(root: Path) -> dict:
    inventory_ref = {"path": FAILED_WRAPPER_INVENTORY,
                     "sha256": FAILED_WRAPPER_INVENTORY_SHA256}
    inventory = _read_json(_validate_reference(root, inventory_ref))
    expected_error = "RuntimeError: Joern supplement invocation failed: exit=1, timed_out=False, capacity=None"
    if (inventory.get("schema") != "v092-swift-identity-invocation-failure-inventory/v1"
            or inventory.get("campaign_id") != "20261122-06"
            or inventory.get("file_count") != 4674
            or inventory.get("total_bytes") != 114076071
            or inventory.get("source_error") != expected_error
            or inventory.get("wrapper_invocations") != 1
            or inventory.get("identity_phase_invocations") != 1
            or inventory.get("analysis_phase_invocations") != 0
            or inventory.get("benchmark_case_rows") != 0
            or inventory.get("publication_eligible") is not False
            or not isinstance(inventory.get("files"), list)
            or len(inventory["files"]) != 4674):
        raise RuntimeError("campaign 06 invocation failure inventory changed or was flattened into preparation")
    roots = [root / FAILED_WRAPPER_REPORT, root / FAILED_WRAPPER_SOURCE]
    observed = set()
    for tree in roots:
        for path in tree.rglob("*"):
            if path.is_symlink():
                raise RuntimeError("campaign 06 wrapper failure tree acquired a symlink")
            if path.is_file():
                observed.add(path.relative_to(root).as_posix())
    rows = inventory["files"]
    listed = {row.get("path") for row in rows if isinstance(row, dict)}
    if (len(listed) != len(rows) or observed != listed
            or sum(row.get("size_bytes", -1) for row in rows if isinstance(row, dict))
            != inventory["total_bytes"]):
        raise RuntimeError("campaign 06 wrapper failure tree no longer matches its closed inventory")
    for row in rows:
        if (not isinstance(row, dict) or type(row.get("size_bytes")) is not int
                or row["size_bytes"] < 0):
            raise RuntimeError("campaign 06 wrapper failure inventory has a malformed file row")
        path = _validate_reference(root, {"path": row.get("path"), "sha256": row.get("sha256")})
        if path.stat().st_size != row["size_bytes"]:
            raise RuntimeError("campaign 06 wrapper failure byte counts changed")

    campaign_start_path = f"{FAILED_WRAPPER_REPORT}/campaign-start.json"
    campaign_terminal_path = f"{FAILED_WRAPPER_REPORT}/campaign-terminal.json"
    start = _read_json(_repo_file(root, campaign_start_path))
    terminal = _read_json(_repo_file(root, campaign_terminal_path))
    if (start.get("campaign_id") != "20261122-06"
            or type(start.get("supervisor_pid")) is not int
            or start["supervisor_pid"] <= 0
            or not isinstance(start.get("supervisor_start_identity"), str)
            or not start["supervisor_start_identity"]
            or terminal.get("campaign_id") != "20261122-06"
            or terminal.get("status") != "unqualified"
            or terminal.get("execution_status") != "stopped-fail-closed"
            or terminal.get("failed_group") != GROUP_ID
            or terminal.get("completed_groups") != []
            or terminal.get("automatic_retry") is not False
            or terminal.get("publication_eligible") is not False
            or terminal.get("descendant_containment") != "unproven"):
        raise RuntimeError("campaign 06 wrapper failure campaign-level terminal changed")

    attempt_relative = f"{FAILED_WRAPPER_REPORT}/attempts/{GROUP_ID}/attempt-01"
    attempt_start_path = f"{attempt_relative}/start.json"
    attempt_terminal_path = f"{attempt_relative}/terminal.json"
    attempt_start = _read_json(_repo_file(root, attempt_start_path))
    attempt_terminal_ref = terminal.get("attempt_terminal")
    expected_attempt_terminal_path = {"path": attempt_terminal_path}
    if (not isinstance(attempt_terminal_ref, dict)
            or attempt_terminal_ref.get("path") != expected_attempt_terminal_path["path"]
            or not isinstance(attempt_terminal_ref.get("sha256"), str)
            or len(attempt_terminal_ref["sha256"]) != 64):
        raise RuntimeError("campaign 06 attempt terminal binding changed")
    attempt_terminal = _read_json(_validate_reference(root, attempt_terminal_ref))
    attempt_ownership = attempt_terminal.get("process_ownership")
    if (attempt_start.get("campaign_id") != "20261122-06"
            or attempt_start.get("group") != GROUP_ID or attempt_start.get("attempt") != 1
            or attempt_start.get("automatic_retry") is not False
            or attempt_start.get("publication_eligible") is not False
            or attempt_terminal.get("group") != GROUP_ID or attempt_terminal.get("attempt") != 1
            or attempt_terminal.get("status") != "failed"
            or attempt_terminal.get("error") != expected_error
            or attempt_terminal.get("exit_code") != 1
            or attempt_terminal.get("timed_out") is not False
            or attempt_terminal.get("capacity_loss") is not None
            or attempt_terminal.get("automatic_retry") is not False
            or attempt_terminal.get("publication_eligible") is not False
            or not isinstance(attempt_terminal.get("elapsed_seconds"), (int, float))
            or attempt_terminal["elapsed_seconds"] <= 0
            or not isinstance(attempt_terminal.get("command_elapsed_seconds"), (int, float))
            or attempt_terminal["command_elapsed_seconds"] <= 0
            or not isinstance(attempt_ownership, dict)
            or attempt_ownership.get("cleanup_status") != "tracked-processes-stopped"
            or attempt_ownership.get("signals_sent") != []
            or attempt_ownership.get("descendant_containment") != "unproven"
            or not isinstance(attempt_ownership.get("tracked_processes"), list)
            or not attempt_ownership["tracked_processes"]):
        raise RuntimeError("campaign 06 outer invocation failure, costs, or cleanup evidence changed")
    wrapper_failure = terminal.get("failure")
    if (not isinstance(wrapper_failure, dict)
            or wrapper_failure.get("status") != "failed"
            or wrapper_failure.get("error") != expected_error
            or wrapper_failure.get("exit_code") != 1
            or wrapper_failure.get("timed_out") is not False
            or wrapper_failure.get("capacity_loss") is not None
            or wrapper_failure.get("process_ownership") != attempt_ownership):
        raise RuntimeError("campaign 06 terminal no longer preserves the exact wrapper failure")

    version_dir = root / FAILED_WRAPPER_VERSION_DIR
    version_path = f"{FAILED_WRAPPER_VERSION_DIR}/version.command.json"
    version = _read_json(_repo_file(root, version_path))
    version_stdout_path = f"{FAILED_WRAPPER_VERSION_DIR}/version.stdout"
    version_stderr_path = f"{FAILED_WRAPPER_VERSION_DIR}/version.stderr"
    version_stdout = _repo_file(root, version_stdout_path).read_text()
    version_stderr = _repo_file(root, version_stderr_path).read_text()
    if (version.get("argv") != ["/Users/dave/.codex/worktrees/cb55/dataflowbench/"
                                 "execution-state/timing-runtime-20261114-01/joern/joern-cli/joern"]
            or version.get("exit_status") != 1 or version.get("timed_out") is not False
            or version.get("discovery_complete") is not False
            or version.get("cleanup_status") != "uncertain"
            or version.get("cleanup_error") != "process tracking failed: invocation root start identity was never captured"
            or version.get("cleanup_signaled") != []
            or version.get("tracked_descendants") != []
            or version.get("descendant_containment") != "unproven"
            or version.get("memory_compliance") != "unproven"
            or version.get("scratch_cleanup_authorized") is not False
            or version.get("environment", {}).get("PATH") != "/usr/bin:/bin:/usr/sbin:/sbin"
            or not isinstance(version.get("elapsed_seconds"), (int, float))
            or version["elapsed_seconds"] <= 0
            or "Unable to find ./bin/repl-bridge" not in version_stdout
            or "greadlink: command not found" not in version_stderr):
        raise RuntimeError("campaign 06 version probe failure or uncertain inner cleanup changed")
    run_path = root / FAILED_WRAPPER_SOURCE / OUTPUT_RELATIVE / "run.json"
    if run_path.exists() or run_path.is_symlink():
        raise RuntimeError("campaign 06 unexpectedly created an analyzer run.json after wrapper failure")
    if version_dir.is_symlink():
        raise RuntimeError("campaign 06 version evidence directory unexpectedly became a symlink")

    return {
        "schema": "v092-swift-closed-wrapper-failure/v1",
        "campaign_id": "20261122-06",
        "classification": "wrapper-launcher-path-dependency-failure",
        "inventory": inventory_ref,
        "campaign_start": _reference(root, campaign_start_path),
        "campaign_terminal": _reference(root, campaign_terminal_path),
        "attempt_start": _reference(root, attempt_start_path),
        "attempt_terminal": attempt_terminal_ref,
        "version_command": _reference(root, version_path),
        "version_stdout": _reference(root, version_stdout_path),
        "version_stderr": _reference(root, version_stderr_path),
        "wrapper_invocations": 1,
        "identity_phase_invocations": 1,
        "analysis_phase_invocations": 0,
        "benchmark_case_rows": 0,
        "exit_code": 1,
        "timed_out": False,
        "capacity_loss": None,
        "elapsed_seconds": attempt_terminal["elapsed_seconds"],
        "command_elapsed_seconds": attempt_terminal["command_elapsed_seconds"],
        "version_elapsed_seconds": version["elapsed_seconds"],
        "run_json_status": "absent",
        "version_discovery_complete": False,
        "inner_cleanup_status": "uncertain",
        "inner_cleanup_error": version["cleanup_error"],
        "outer_cleanup_status": "tracked-processes-stopped",
        "outer_signals_sent": [],
        "descendant_containment": "unproven",
        "automatic_retry": False,
        "publication_eligible": False,
    }


def _verify_failed_capability_attempt(root: Path) -> dict:
    """Bind the 07 wrapper failure from the sealed inventory and targeted receipts."""
    inventory_ref = {"path": FAILED_CAPABILITY_INVENTORY,
                     "sha256": FAILED_CAPABILITY_INVENTORY_SHA256}
    inventory_path = _validate_reference(root, inventory_ref)
    inventory = _read_json(inventory_path)
    expected_error = "RuntimeError: Joern supplement invocation failed: exit=1, timed_out=False, capacity=None"
    if (inventory.get("schema") != "v092-swift-capability-invocation-failure-inventory/v1"
            or inventory.get("campaign_id") != "20261122-07"
            or inventory.get("file_count") != FAILED_CAPABILITY_INVENTORY_FILE_COUNT
            or inventory.get("total_bytes") != FAILED_CAPABILITY_INVENTORY_TOTAL_BYTES
            or inventory.get("source_error") != expected_error
            or inventory.get("wrapper_invocations") != 1
            or inventory.get("identity_phase_invocations") != 1
            or inventory.get("analysis_phase_invocations") != 0
            or inventory.get("benchmark_case_rows") != 0
            or inventory.get("publication_eligible") is not False):
        raise RuntimeError("campaign 07 capability failure inventory changed or hides an analyzer invocation")

    rows = inventory.get("files")
    if not isinstance(rows, list) or len(rows) != FAILED_CAPABILITY_INVENTORY_FILE_COUNT:
        raise RuntimeError("campaign 07 capability failure inventory file roster is malformed")
    indexed_rows: dict[str, dict] = {}
    total_bytes = 0
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"path", "sha256", "size_bytes"}
                or not isinstance(row.get("path"), str)
                or not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in row["sha256"])
                or type(row.get("size_bytes")) is not int or row["size_bytes"] < 0
                or row["path"] in indexed_rows):
            raise RuntimeError("campaign 07 capability failure inventory has a malformed or duplicate row")
        indexed_rows[row["path"]] = row
        total_bytes += row["size_bytes"]
    if total_bytes != FAILED_CAPABILITY_INVENTORY_TOTAL_BYTES:
        raise RuntimeError("campaign 07 capability failure inventory byte total changed")

    attempt_relative = f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01"
    version_relative = FAILED_CAPABILITY_VERSION_DIR
    expected_paths = {
        "campaign_start": f"{FAILED_CAPABILITY_REPORT}/campaign-start.json",
        "campaign_terminal": f"{FAILED_CAPABILITY_REPORT}/campaign-terminal.json",
        "launch_failure": f"{FAILED_CAPABILITY_REPORT}/launch-failure-001.json",
        "attempt_start": f"{attempt_relative}/start.json",
        "attempt_terminal": f"{attempt_relative}/terminal.json",
        "attempt_stdout": f"{attempt_relative}/stdout.txt",
        "attempt_stderr": f"{attempt_relative}/stderr.txt",
        "version_command": f"{version_relative}/version.command.json",
        "version_stdout": f"{version_relative}/version.stdout",
        "version_stderr": f"{version_relative}/version.stderr",
        "identity": f"{version_relative}/identity.json",
    }
    references = {}
    for name, relative in expected_paths.items():
        row = indexed_rows.get(relative)
        if row is None:
            raise RuntimeError(f"campaign 07 sealed inventory omits required {name} evidence")
        reference = {"path": relative, "sha256": row["sha256"]}
        path = _validate_reference(root, reference)
        if path.stat().st_size != row["size_bytes"]:
            raise RuntimeError(f"campaign 07 {name} byte count differs from its sealed inventory")
        references[name] = reference

    campaign_start = _read_json(_validate_reference(root, references["campaign_start"]))
    campaign_terminal = _read_json(_validate_reference(root, references["campaign_terminal"]))
    attempt_start = _read_json(_validate_reference(root, references["attempt_start"]))
    attempt_terminal = _read_json(_validate_reference(root, references["attempt_terminal"]))
    launch_failure = _read_json(_validate_reference(root, references["launch_failure"]))
    attempt_stdout = _repo_file(root, references["attempt_stdout"]["path"]).read_text()
    attempt_stderr = _repo_file(root, references["attempt_stderr"]["path"]).read_text()
    ownership = attempt_terminal.get("process_ownership")
    if (campaign_start.get("campaign_id") != "20261122-07"
            or type(campaign_start.get("supervisor_pid")) is not int
            or campaign_start["supervisor_pid"] <= 0
            or not isinstance(campaign_start.get("supervisor_start_identity"), str)
            or campaign_terminal.get("campaign_id") != "20261122-07"
            or campaign_terminal.get("status") != "unqualified"
            or campaign_terminal.get("execution_status") != "stopped-fail-closed"
            or campaign_terminal.get("failed_group") != GROUP_ID
            or campaign_terminal.get("completed_groups") != []
            or campaign_terminal.get("automatic_retry") is not False
            or campaign_terminal.get("publication_eligible") is not False
            or campaign_terminal.get("descendant_containment") != "unproven"
            or campaign_terminal.get("attempt_terminal") != references["attempt_terminal"]
            or campaign_terminal.get("failure") != attempt_terminal
            or launch_failure != attempt_terminal
            or attempt_start.get("campaign_id") != "20261122-07"
            or attempt_start.get("group") != GROUP_ID or attempt_start.get("attempt") != 1
            or attempt_start.get("automatic_retry") is not False
            or attempt_start.get("publication_eligible") is not False
            or attempt_start.get("argv") != [
                "/usr/bin/python3", "scripts/run-joern-common-v092-relocated.py", "execute", "--plan",
                "adapters/joern/swift-common-v2/plan-v092-02/execution-plan-qualified.json",
                "--output", "reports/raw/joern-common-v2/current108-v092-02",
            ]
            or attempt_start.get("old_frozen_argv") != [
                "/usr/bin/python3", "scripts/run-joern-common-v092.py", "execute", "--plan",
                "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
                "--output", "reports/raw/joern-common-v2/current108-v092-01",
            ]
            or attempt_start.get("environment", {}).get("PATH") != PARENT_GROUP_PATH
            or attempt_terminal.get("group") != GROUP_ID or attempt_terminal.get("attempt") != 1
            or attempt_terminal.get("status") != "failed"
            or attempt_terminal.get("error") != expected_error
            or attempt_terminal.get("exit_code") != 1
            or attempt_terminal.get("timed_out") is not False
            or attempt_terminal.get("capacity_loss") is not None
            or attempt_terminal.get("automatic_retry") is not False
            or attempt_terminal.get("publication_eligible") is not False
            or not isinstance(ownership, dict)
            or ownership.get("cleanup_status") != "tracked-processes-stopped"
            or ownership.get("signals_sent") != []
            or ownership.get("descendant_containment") != "unproven"
            or type(ownership.get("root_pid")) is not int
            or not isinstance(ownership.get("tracked_processes"), list)
            or not ownership["tracked_processes"]):
        raise RuntimeError("campaign 07 wrapper failure, terminal, or outer process ownership changed")
    if (attempt_stdout != ""
            or "attempted case lacks explicit capability evidence" not in attempt_stderr
            or "ValueError: Joern attempted case lacks explicit capability evidence" not in attempt_stderr):
        raise RuntimeError("campaign 07 failure no longer identifies the missing capability before analysis")
    for key in ("elapsed_seconds", "command_elapsed_seconds"):
        if (type(attempt_terminal.get(key)) not in {int, float}
                or not math.isfinite(attempt_terminal[key]) or attempt_terminal[key] <= 0):
            raise RuntimeError(f"campaign 07 failure no longer records its {key}")

    version = _read_json(_validate_reference(root, references["version_command"]))
    version_stdout = _repo_file(root, references["version_stdout"]["path"]).read_text()
    version_stderr = _repo_file(root, references["version_stderr"]["path"]).read_text()
    if (version.get("argv") != ["/Users/dave/.codex/worktrees/cb55/dataflowbench/"
                                 "execution-state/timing-runtime-20261114-01/joern/joern-cli/joern"]
            or version.get("exit_status") != 0 or version.get("timed_out") is not False
            or version.get("cleanup_status") != "tracked-processes-stopped"
            or version.get("cleanup_error") is not None or version.get("cleanup_signaled") != []
            or version.get("descendant_containment") != "unproven"
            or version.get("scratch_cleanup_authorized") is not False
            or version.get("discovery_complete") is not False
            or version.get("environment", {}).get("PATH") != PARENT_GROUP_PATH
            or not isinstance(version.get("tracked_descendants"), list)
            or not version["tracked_descendants"]
            or type(version.get("elapsed_seconds")) not in {int, float}
            or not math.isfinite(version["elapsed_seconds"]) or version["elapsed_seconds"] <= 0
            or "Version: 4.0.660" not in version_stdout
            or "joern>" not in version_stdout or version_stderr != ""):
        raise RuntimeError("campaign 07 successful version probe or tracked inner cleanup changed")

    failed_run_path = root / FAILED_CAPABILITY_SOURCE / "reports/raw/joern-common-v2/current108-v092-02/run.json"
    if failed_run_path.exists() or failed_run_path.is_symlink():
        raise RuntimeError("campaign 07 unexpectedly retained run.json despite zero case analysis")
    if failed_run_path.relative_to(root).as_posix() in indexed_rows:
        raise RuntimeError("campaign 07 inventory claims an analyzer run.json exists")

    return {
        "schema": "v092-swift-closed-capability-failure/v1",
        "campaign_id": "20261122-07",
        "classification": "missing-explicit-capability-before-case-analysis",
        "inventory": inventory_ref,
        **references,
        "wrapper_invocations": 1, "identity_phase_invocations": 1,
        "analysis_phase_invocations": 0, "benchmark_case_rows": 0,
        "version_invocations": 1, "exit_code": 1, "timed_out": False,
        "capacity_loss": None,
        "elapsed_seconds": attempt_terminal["elapsed_seconds"],
        "command_elapsed_seconds": attempt_terminal["command_elapsed_seconds"],
        "version_elapsed_seconds": version["elapsed_seconds"],
        "run_json_status": "absent", "version_exit_status": 0,
        "version_cleanup_status": "tracked-processes-stopped",
        "version_cleanup_signaled": [],
        "outer_cleanup_status": "tracked-processes-stopped", "outer_signals_sent": [],
        "inner_cleanup_status": "tracked-processes-stopped",
        "descendant_containment": "unproven", "automatic_retry": False,
        "publication_eligible": False,
    }


def _failed_preparation_bindings() -> list[dict]:
    return [
        {"campaign_id": "20261122-03",
         "inventory": {"path": FAILED_PREPARATION_INVENTORY,
                       "sha256": FAILED_PREPARATION_INVENTORY_SHA256},
         "file_count": 8, "total_bytes": 721027, "analyzer_invocations": 0,
         "source_error": "AttributeError: '_SupplementDiskGuard' object has no attribute 'chunk_bytes'"},
        {"campaign_id": "20261122-04",
         "inventory": {"path": FAILED_PREPARATION_04_INVENTORY,
                       "sha256": FAILED_PREPARATION_04_INVENTORY_SHA256},
         "file_count": 4672, "total_bytes": 114774850, "analyzer_invocations": 0,
         "source_error": "KeyboardInterrupt: "},
        {"campaign_id": "20261122-05",
         "inventory": {"path": FAILED_PREPARATION_05_INVENTORY,
                       "sha256": FAILED_PREPARATION_05_INVENTORY_SHA256},
         "file_count": 4670, "total_bytes": 121883730, "analyzer_invocations": 0,
         "source_error": "KeyboardInterrupt: "},
    ]


def _observe_closed_prior_processes(root: Path, legacy) -> dict:
    helper = _load_module("swift_supplement_closed_process_identity",
                          root / FAILED_PREPARATION_PROCESS_HELPER)
    helper_ref = _reference(root, FAILED_PREPARATION_PROCESS_HELPER)
    tracker = legacy.core._process_tracker()
    known: list[dict] = []
    for binding, report_root in zip(
            _failed_preparation_bindings(),
            (FAILED_PREPARATION_REPORT, FAILED_PREPARATION_04_REPORT, FAILED_PREPARATION_05_REPORT)):
        start_path = root / report_root / "campaign-start.json"
        start = _read_json(start_path)
        if start.get("campaign_id") != binding["campaign_id"]:
            raise RuntimeError(f"closed preparation campaign-start changed: {binding['campaign_id']}")
        pid = start.get("supervisor_pid")
        identity = start.get("supervisor_start_identity")
        if type(pid) is not int or pid <= 0 or not isinstance(identity, str) or not identity:
            raise RuntimeError(f"closed preparation supervisor identity is malformed: {binding['campaign_id']}")
        known.append({"campaign_id": binding["campaign_id"], "role": "campaign-supervisor",
                      "pid": pid, "start_identity": identity,
                      "campaign_start": _reference(root, f"{report_root}/campaign-start.json")})

    failure_start = _read_json(_repo_file(root, f"{FAILED_WRAPPER_REPORT}/campaign-start.json"))
    failure_terminal = _read_json(_repo_file(root, f"{FAILED_WRAPPER_REPORT}/attempts/{GROUP_ID}/attempt-01/terminal.json"))
    failure_owner = failure_terminal.get("process_ownership")
    if (failure_start.get("campaign_id") != "20261122-06"
            or type(failure_start.get("supervisor_pid")) is not int
            or not isinstance(failure_start.get("supervisor_start_identity"), str)
            or not isinstance(failure_owner, dict)
            or failure_owner.get("cleanup_status") != "tracked-processes-stopped"
            or failure_owner.get("signals_sent") != []
            or failure_owner.get("descendant_containment") != "unproven"):
        raise RuntimeError("campaign 06 outer process identity evidence is malformed")
    failure_start_ref = _reference(root, f"{FAILED_WRAPPER_REPORT}/campaign-start.json")
    known.append({"campaign_id": "20261122-06", "role": "campaign-supervisor",
                  "pid": failure_start["supervisor_pid"],
                  "start_identity": failure_start["supervisor_start_identity"],
                  "campaign_start": failure_start_ref})
    tracked = failure_owner.get("tracked_processes")
    if not isinstance(tracked, list) or not tracked:
        raise RuntimeError("campaign 06 did not record its outer process identities")
    for row in tracked:
        if (not isinstance(row, dict) or type(row.get("pid")) is not int or row["pid"] <= 0
                or not isinstance(row.get("start_identity"), str) or not row["start_identity"]):
            raise RuntimeError("campaign 06 recorded a malformed outer process identity")
        known.append({"campaign_id": "20261122-06", "role": "invocation-process",
                      "pid": row["pid"], "start_identity": row["start_identity"],
                      "campaign_start": failure_start_ref})

    smoke_start = _read_json(_validate_reference(
        root, {"path": LAUNCHER_SMOKE_START_PATH, "sha256": LAUNCHER_SMOKE_START_SHA256}))
    smoke_terminal = _read_json(_validate_reference(
        root, {"path": LAUNCHER_SMOKE_TERMINAL_PATH, "sha256": LAUNCHER_SMOKE_TERMINAL_SHA256}))
    smoke_owner = smoke_terminal.get("process_ownership")
    if (type(smoke_terminal.get("supervisor_pid")) is not int
            or not isinstance(smoke_terminal.get("supervisor_start_identity"), str)
            or not isinstance(smoke_owner, dict)
            or smoke_owner.get("cleanup_status") != "tracked-processes-stopped"
            or smoke_owner.get("signals_sent") != []
            or smoke_owner.get("descendant_containment") != "unproven"):
        raise RuntimeError("launcher smoke outer process identity evidence is malformed")
    smoke_ref = _reference(root, LAUNCHER_SMOKE_START_PATH)
    known.append({"campaign_id": "launcher-smoke-01", "role": "campaign-supervisor",
                  "pid": smoke_terminal["supervisor_pid"],
                  "start_identity": smoke_terminal["supervisor_start_identity"],
                  "campaign_start": smoke_ref})
    smoke_tracked = smoke_owner.get("tracked_processes")
    if not isinstance(smoke_tracked, list) or not smoke_tracked:
        raise RuntimeError("launcher smoke did not record its outer process identities")
    for row in smoke_tracked:
        if (not isinstance(row, dict) or type(row.get("pid")) is not int or row["pid"] <= 0
                or not isinstance(row.get("start_identity"), str) or not row["start_identity"]):
            raise RuntimeError("launcher smoke recorded a malformed outer process identity")
        known.append({"campaign_id": "launcher-smoke-01", "role": "version-process",
                      "pid": row["pid"], "start_identity": row["start_identity"],
                      "campaign_start": smoke_ref})

    capability_start_path = f"{FAILED_CAPABILITY_REPORT}/campaign-start.json"
    capability_start = _read_json(_repo_file(root, capability_start_path))
    capability_terminal_path = f"{FAILED_CAPABILITY_REPORT}/attempts/{GROUP_ID}/attempt-01/terminal.json"
    capability_terminal = _read_json(_repo_file(root, capability_terminal_path))
    capability_owner = capability_terminal.get("process_ownership")
    if (capability_start.get("campaign_id") != "20261122-07"
            or type(capability_start.get("supervisor_pid")) is not int
            or not isinstance(capability_start.get("supervisor_start_identity"), str)
            or not isinstance(capability_owner, dict)
            or capability_owner.get("cleanup_status") != "tracked-processes-stopped"
            or capability_owner.get("signals_sent") != []
            or capability_owner.get("descendant_containment") != "unproven"):
        raise RuntimeError("campaign 07 outer process identity evidence is malformed")
    capability_start_ref = _reference(root, capability_start_path)
    known.append({"campaign_id": "20261122-07", "role": "campaign-supervisor",
                  "pid": capability_start["supervisor_pid"],
                  "start_identity": capability_start["supervisor_start_identity"],
                  "campaign_start": capability_start_ref})
    capability_tracked = capability_owner.get("tracked_processes")
    if not isinstance(capability_tracked, list) or not capability_tracked:
        raise RuntimeError("campaign 07 did not record its outer process identities")
    for row in capability_tracked:
        if (not isinstance(row, dict) or type(row.get("pid")) is not int or row["pid"] <= 0
                or not isinstance(row.get("start_identity"), str) or not row["start_identity"]):
            raise RuntimeError("campaign 07 recorded a malformed outer process identity")
        known.append({"campaign_id": "20261122-07", "role": "invocation-process",
                      "pid": row["pid"], "start_identity": row["start_identity"],
                      "campaign_start": capability_start_ref})
    version = _read_json(_repo_file(root, f"{FAILED_CAPABILITY_VERSION_DIR}/version.command.json"))
    version_descendants = version.get("tracked_descendants")
    if (version.get("exit_status") != 0 or version.get("timed_out") is not False
            or version.get("cleanup_status") != "tracked-processes-stopped"
            or version.get("cleanup_signaled") != []
            or version.get("descendant_containment") != "unproven"
            or not isinstance(version_descendants, list) or not version_descendants):
        raise RuntimeError("campaign 07 version process identity evidence is malformed")
    for row in version_descendants:
        if (not isinstance(row, dict) or type(row.get("pid")) is not int or row["pid"] <= 0
                or not isinstance(row.get("start_identity"), str) or not row["start_identity"]):
            raise RuntimeError("campaign 07 version command recorded a malformed descendant identity")
        known.append({"campaign_id": "20261122-07", "role": "version-process",
                      "pid": row["pid"], "start_identity": row["start_identity"],
                      "campaign_start": capability_start_ref})

    unique: dict[tuple[int, str], dict] = {}
    pid_birth: dict[int, str] = {}
    for identity in known:
        pid = identity["pid"]
        birth = identity["start_identity"]
        if pid in pid_birth and pid_birth[pid] != birth:
            raise RuntimeError(f"prior process PID {pid} has conflicting recorded birth identities")
        pid_birth[pid] = birth
        unique.setdefault((pid, birth), identity)
    observations = []
    for identity in unique.values():
        proof = helper.observe_stopped(identity["pid"], identity["start_identity"],
                                       tracker._start_identity)
        if (proof.get("schema") != "v092-closed-process-observation/v1"
                or proof.get("pid") != identity["pid"]
                or proof.get("expected_start_identity") != identity["start_identity"]
                or proof.get("status") not in {"confirmed-pid-absent", "confirmed-different-birth-identity"}
                or proof.get("signals_sent") != []):
            raise RuntimeError(f"prior process identity stop is unproven: {identity['campaign_id']}/{identity['pid']}")
        observations.append({
            **identity,
            "observation": proof,
        })
    return {"schema": "v092-closed-prior-processes/v1",
            "status": "confirmed-stopped", "observations": observations,
            "observer_helper": helper_ref,
            "campaign06_inner_cleanup_status": "uncertain",
            "campaign07_inner_cleanup_status": "tracked-processes-stopped",
            "descendant_containment": "unproven",
            "publication_eligible": False}


def _verify_gnu_readlink() -> dict:
    lookup = Path(GNU_READLINK_LOOKUP_PATH)
    if not lookup.is_symlink() or os.readlink(lookup) != GNU_READLINK_SYMLINK_TARGET:
        raise RuntimeError("frozen GNU greadlink lookup symlink changed")
    real = lookup.resolve(strict=True)
    if real != Path(GNU_READLINK_REAL_PATH) or not real.is_file() or real.is_symlink():
        raise RuntimeError("frozen GNU greadlink resolved path or type changed")
    info = real.stat()
    if (stat.S_IMODE(info.st_mode) != GNU_READLINK_MODE
            or info.st_size != GNU_READLINK_SIZE_BYTES
            or sha(real) != GNU_READLINK_SHA256):
        raise RuntimeError("frozen GNU greadlink bytes, mode, or size changed")
    if shutil.which("greadlink", path=PARENT_GROUP_PATH) != GNU_READLINK_LOOKUP_PATH:
        raise RuntimeError("frozen parent PATH no longer resolves the approved GNU greadlink")
    return {
        "name": "greadlink", "lookup_path": GNU_READLINK_LOOKUP_PATH,
        "real_path": GNU_READLINK_REAL_PATH, "symlink_target": GNU_READLINK_SYMLINK_TARGET,
        "sha256": GNU_READLINK_SHA256, "size_bytes": GNU_READLINK_SIZE_BYTES,
        "mode": GNU_READLINK_MODE, "version_banner": "readlink (GNU coreutils) 9.8",
    }


def _launcher_preflight_binding() -> dict:
    return {
        "schema": "v092-joern-launcher-prerequisite-proof/v1",
        "parent_group_path": PARENT_GROUP_PATH,
        "recovery_receipt": {"path": LAUNCHER_RECOVERY_PATH, "sha256": LAUNCHER_RECOVERY_SHA256},
        "control_version_command": {"path": LAUNCHER_CONTROL_VERSION_PATH,
                                    "sha256": LAUNCHER_CONTROL_VERSION_SHA256},
        "gnu_dependency": {
            "name": "greadlink", "lookup_path": GNU_READLINK_LOOKUP_PATH,
            "real_path": GNU_READLINK_REAL_PATH, "symlink_target": GNU_READLINK_SYMLINK_TARGET,
            "sha256": GNU_READLINK_SHA256, "size_bytes": GNU_READLINK_SIZE_BYTES,
            "mode": GNU_READLINK_MODE, "version_banner": "readlink (GNU coreutils) 9.8",
        },
        "positive_smoke_terminal": {"path": LAUNCHER_SMOKE_TERMINAL_PATH,
                                     "sha256": LAUNCHER_SMOKE_TERMINAL_SHA256},
        "positive_smoke_artifacts": {
            "start": {"path": LAUNCHER_SMOKE_START_PATH, "sha256": LAUNCHER_SMOKE_START_SHA256},
            "stdout": {"path": LAUNCHER_SMOKE_STDOUT_PATH, "sha256": LAUNCHER_SMOKE_STDOUT_SHA256},
            "stderr": {"path": LAUNCHER_SMOKE_STDERR_PATH, "sha256": LAUNCHER_SMOKE_STDERR_SHA256},
        },
        "analysis_phase_invocations": 0,
        "benchmark_case_rows": 0,
        "publication_eligible": False,
    }


def _verify_launcher_preflight(root: Path) -> dict:
    recovery_ref = {"path": LAUNCHER_RECOVERY_PATH, "sha256": LAUNCHER_RECOVERY_SHA256}
    recovery = _read_json(_validate_reference(root, recovery_ref))
    if (recovery.get("schema") != "v092-joern-launcher-path-recovery/v1"
            or recovery.get("path") != PARENT_GROUP_PATH
            or recovery.get("parent_plan") != {"path": BASE_PLAN_PATH, "sha256": BASE_PLAN_SHA256}
            or recovery.get("analysis_phase_invocations") != 0
            or recovery.get("publication_eligible") is not False
            or recovery.get("qualification_scope") != (
                "restore the exact PATH used by retained fresh controls, prospectively pin external "
                "canonicalization helper, no analyzer/fixture/query changes")):
        raise RuntimeError("launcher PATH recovery receipt changed or claims broader qualification")
    expected_dependency = _verify_gnu_readlink()
    if recovery.get("dependency") != {
            **expected_dependency,
            "linked_libraries": [
                "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
                "/System/Library/Frameworks/CoreServices.framework/Versions/A/CoreServices",
                "/usr/lib/libSystem.B.dylib",
            ],
    }:
        raise RuntimeError("launcher PATH recovery dependency identity differs from the approved GNU helper")
    if recovery.get("launcher") != {
            "path": "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/"
                    "timing-runtime-20261114-01/joern/joern-cli/joern",
            "canonicalized_path": "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/"
                                 "timing-runtime-20261114-01/joern/joern-cli/joern",
            "sha256": "0df7e8db4282ef2c6fc37998917aca694176e23192de5f0c631511d993e99736",
    }:
        raise RuntimeError("launcher path recovery no longer identifies the pinned Joern launcher")
    control_ref = {"path": LAUNCHER_CONTROL_VERSION_PATH,
                   "sha256": LAUNCHER_CONTROL_VERSION_SHA256}
    if recovery.get("successful_control_version_command") != control_ref:
        raise RuntimeError("launcher recovery receipt lost the exact successful control version command")
    control_command = _read_json(_validate_reference(root, control_ref))
    if (control_command.get("argv") != [recovery["launcher"]["path"]]
            or control_command.get("exit_status") != 0
            or control_command.get("timed_out") is not False
            or control_command.get("cleanup_status") != "tracked-processes-stopped"
            or control_command.get("cleanup_signaled") != []
            or control_command.get("environment", {}).get("PATH") != PARENT_GROUP_PATH):
        raise RuntimeError("retained fresh-control Joern version command did not verify the exact PATH")

    smoke_ref = {"path": LAUNCHER_SMOKE_TERMINAL_PATH,
                 "sha256": LAUNCHER_SMOKE_TERMINAL_SHA256}
    smoke = _read_json(_validate_reference(root, smoke_ref))
    if (smoke.get("schema") != "v092-joern-launcher-preflight/v1"
            or smoke.get("status") != "passed" or smoke.get("exit_code") != 0
            or smoke.get("timed_out") is not False or smoke.get("capacity_loss") is not None
            or smoke.get("banner_4_0_660") is not True
            or smoke.get("analysis_phase_invocations") != 0
            or smoke.get("benchmark_case_rows") != 0 or smoke.get("version_invocations") != 1
            or smoke.get("dependency_unchanged") is not True
            or smoke.get("static_counts_unchanged") is not True
            or smoke.get("publication_eligible") is not False):
        raise RuntimeError("positive launcher preflight did not remain version-only and successful")
    smoke_artifact_refs = {
        "start": {"path": LAUNCHER_SMOKE_START_PATH, "sha256": LAUNCHER_SMOKE_START_SHA256},
        "stdout": {"path": LAUNCHER_SMOKE_STDOUT_PATH, "sha256": LAUNCHER_SMOKE_STDOUT_SHA256},
        "stderr": {"path": LAUNCHER_SMOKE_STDERR_PATH, "sha256": LAUNCHER_SMOKE_STDERR_SHA256},
    }
    for key, expected in smoke_artifact_refs.items():
        if smoke.get(key) != expected:
            raise RuntimeError(f"positive launcher preflight {key} binding changed")
        _validate_reference(root, expected)
    start = _read_json(_validate_reference(root, smoke_artifact_refs["start"]))
    environment = start.get("environment")
    control_environment = control_command.get("environment")
    if (start.get("schema") != "v092-joern-launcher-preflight-start/v1"
            or start.get("dependency_receipt") != recovery_ref
            or not isinstance(environment, dict)
            or environment.get("PATH") != PARENT_GROUP_PATH
            or environment.get("JAVA_HOME") != control_environment.get("JAVA_HOME")
            or environment.get("SWIFTASTGEN_BIN") != control_environment.get("SWIFTASTGEN_BIN")
            or environment.get("HOME") != str(root / LAUNCHER_SMOKE_ROOT / "home")
            or environment.get("TMPDIR") != str(root / LAUNCHER_SMOKE_ROOT / "tmp")
            or start.get("live_paths", {}).get("working") != [str(root / LAUNCHER_SMOKE_ROOT)]
            or start.get("live_paths", {}).get("scratch") != [str(root / LAUNCHER_SMOKE_ROOT)]
            or start.get("live_paths", {}).get("retention") != [str(root / PREPARATION_ROOT)]):
        raise RuntimeError("positive launcher smoke used a different toolchain, PATH, or accounted workspace")
    for name in ("home", "tmp", "cache"):
        if not (root / LAUNCHER_SMOKE_ROOT / name).is_dir():
            raise RuntimeError(f"positive launcher smoke scratch directory is missing: {name}")
    return _launcher_preflight_binding()


def _launcher_preflight_observation(root: Path, phase: str) -> dict:
    proof = _verify_launcher_preflight(root)
    return {**proof, "phase": phase,
            "verified_utc": dt.datetime.now(dt.timezone.utc).isoformat()}


def _derive_plan(root: Path, created_utc: str) -> dict:
    failed_preparation = _verify_failed_preparation(root)
    failed_wrapper = _verify_failed_wrapper_attempt(root)
    failed_capability = _verify_failed_capability_attempt(root)
    base_plan, _terminal, _inventory, lineage = _validate_parent_lineage(root)
    qualified, evidence, _context, _runner_data, capability_binding = _validate_v03_qualification(root)
    closure = _reference_closure(root, qualified)
    if closure.get(CAPABILITY_SOURCE_PATH) != CAPABILITY_SOURCE_SHA256:
        raise RuntimeError("the immutable v0.9.0 capability source is absent or changed in the copied input closure")
    projection_exporter = CAPABILITY_V3_REPORTER_PATH
    configuration_hash_helper = "scripts/joern_normal_reports_v092_projection.py"
    postprocessing_dependencies = [
        _reference(root, projection_exporter),
        _reference(root, configuration_hash_helper),
    ]
    committed_inputs = _require_committed_code_inputs(root, qualified)
    resource_scope = _resource_scope(root)
    configuration_provenance = _configuration_provenance(root, qualified, base_plan)
    plan = _base_plan(root, lineage["group"], qualified, evidence, closure, resource_scope,
                      committed_inputs, configuration_provenance, postprocessing_dependencies,
                      failed_wrapper, failed_capability, capability_binding, created_utc)
    plan["prior_preparation_failures"] = failed_preparation
    legacy_core = _qualified_module(root).legacy.core
    copy_closure = dict(closure)
    copy_closure.update({item["path"]: item["sha256"] for item in postprocessing_dependencies})
    copy_closure.update({item["path"]: item["sha256"]
                         for item in plan["source_projection"]["execution_plan_inputs"]})
    plan["source_projection"]["supplement_files_to_copy"] = _supplement_files_to_copy(
        root, copy_closure, legacy_core)
    validate_campaign_plan(plan)
    return plan


def prepare(qualified_plan_path: str = QUALIFIED_PLAN_PATH, output_path: str = PLAN_PATH) -> dict:
    if qualified_plan_path != QUALIFIED_PLAN_PATH:
        raise RuntimeError("only the fixed v0.9.2-02 qualified Joern plan may feed this supplement")
    if output_path != PLAN_PATH:
        raise RuntimeError("supplement plan path is fixed and cannot be version-retried")
    output = _repo_file_parent_path(ROOT, output_path)
    if output.exists() or output.is_symlink():
        raise RuntimeError(f"supplement plan/output namespace already exists: {output}")
    report_root = ROOT / REPORT_ROOT
    work_root = ROOT / WORK_ROOT
    if report_root.exists() or report_root.is_symlink() or work_root.exists() or work_root.is_symlink():
        raise RuntimeError("supplement report/source namespace already exists; refusing to reuse it")
    created_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    plan = _derive_plan(ROOT, created_utc)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_new(output, plan)
    return {"status": "prepared-unqualified", "campaign_id": CAMPAIGN_ID,
            "group_id": GROUP_ID, "plan": output_path, "case_count": CASE_COUNT,
            "report_partition_count": REPORT_PARTITION_COUNT,
            "dispatch_groups": [GROUP_ID], "publication_eligible": False}


def _repo_file_parent_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
        raise RuntimeError("unsafe output path")
    target = root.joinpath(*pure.parts)
    parent = target.parent
    cursor = root
    for part in pure.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"output path traverses a symlink: {cursor}")
    return target


def _write_new(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"refusing to overwrite append-only evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def _append_jsonl(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "ab") as stream:
        stream.write(_json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def _append_raw_observation(path: Path, observation: dict) -> None:
    # This exact dict is written without policy annotations or CPU adjustment.
    _append_jsonl(path, observation)


def _safe_accounting_scope(root: Path, plan: dict) -> dict:
    raw = plan["resource_scope"]
    result = {"parent": {}, "preparation": {}, "active": {}, "all": {}, "baseline": {}}
    for category in ("working", "retention", "scratch"):
        scratch = category == "scratch"
        result["parent"][category] = [
            _validated_accounting_path(root, item, scratch=scratch)
            for item in raw["baseline_paths"][category]
        ]
        result["preparation"][category] = [
            _validated_accounting_path(root, item, scratch=scratch)
            for item in raw["preparation_paths"][category]
        ]
        result["active"][category] = [
            _validated_accounting_path(root, item, scratch=scratch)
            for item in raw["active_paths"][category]
        ]
        result["baseline"][category] = _unique_paths(
            [*result["parent"][category], *result["preparation"][category]])
        result["all"][category] = [Path(item) for item in raw[
            "retained" if category == "retention" else category
        ]]
    result["expected_parent_baseline_bytes"] = raw["expected_parent_baseline_bytes"]
    result["profile_expected_parent_baseline_bytes"] = raw["profile_expected_parent_baseline_bytes"]
    result["post_profile_retained_additions"] = raw["post_profile_retained_additions"]
    result["campaign_start_references"] = raw["campaign_start_references"]
    result["parent_checkpoint"] = raw["parent_checkpoint"]
    result["observer_profile"] = raw["observer_profile"]
    result["observer_method"] = raw["observer_method"]
    result["closed_process_ownership"] = raw["closed_process_ownership"]
    result["closed_process_ownership_state"] = raw["closed_process_ownership_state"]
    result["portability_preflight"] = raw["portability_preflight"]
    return result


def _verify_parent_capture_inventory(root: Path) -> dict:
    inventory_path = _repo_file(root, BASE_INVENTORY_PATH)
    if sha(inventory_path) != BASE_INVENTORY_SHA256:
        raise RuntimeError("sealed parent capture inventory digest changed")
    inventory = _read_json(inventory_path)
    files = inventory.get("files")
    if (inventory.get("schema") != "v092-timing-evidence-inventory/v1"
            or inventory.get("campaign_id") != "20261122-02"
            or inventory.get("file_count") != 111 or not isinstance(files, list)
            or len(files) != 111 or inventory.get("publication_eligible") is not False):
        raise RuntimeError("sealed parent capture inventory is malformed")
    seen: set[str] = set()
    total_bytes = 0
    for row in files:
        if (not isinstance(row, dict) or set(row) != {"path", "sha256", "size_bytes"}
                or not isinstance(row.get("path"), str)
                or not isinstance(row.get("sha256"), str)
                or len(row["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in row["sha256"])
                or type(row.get("size_bytes")) is not int or row["size_bytes"] < 0
                or row["path"] in seen):
            raise RuntimeError("sealed parent inventory contains a malformed or duplicate file row")
        seen.add(row["path"])
        path = _repo_file(root, row["path"])
        if path.stat().st_size != row["size_bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"sealed parent capture changed: {row['path']}")
        total_bytes += row["size_bytes"]
    if total_bytes != inventory.get("total_bytes"):
        raise RuntimeError("sealed parent inventory total byte count changed")
    return {"path": BASE_INVENTORY_PATH, "sha256": BASE_INVENTORY_SHA256,
            "file_count": len(files), "total_bytes": total_bytes,
            "all_files_verified": True}


def _verify_post_profile_retained_additions(root: Path, additions: object) -> list[dict]:
    expected = [dict(row) for row in POST_PROFILE_RETAINED_ADDITIONS]
    if additions != expected:
        raise RuntimeError("post-profile retained additions differ from the exact reviewed set")
    for row in expected:
        path = _validate_reference(root, {"path": row["path"], "sha256": row["sha256"]})
        if path.stat().st_size != row["size_bytes"]:
            raise RuntimeError(f"post-profile retained addition size changed: {row['path']}")
    return expected


def _measure_resource_baseline(root: Path, scope: dict, disk) -> dict:
    for field in ("observer_profile", "closed_process_ownership", "portability_preflight"):
        _validate_reference(root, scope[field])
    inventory = _verify_parent_capture_inventory(root)
    post_profile_additions = _verify_post_profile_retained_additions(
        root, scope.get("post_profile_retained_additions"))
    expected_parent = scope["expected_parent_baseline_bytes"]
    categories = ("working", "retention", "scratch")
    parent_bytes, preparation_bytes, active_bytes, full_bytes = {}, {}, {}, {}
    for category in categories:
        parent_bytes[category] = disk.logical_size(scope["parent"][category])
        preparation_bytes[category] = disk.logical_size(scope["preparation"][category])
        active_bytes[category] = disk.logical_size(scope["active"][category])
        full_bytes[category] = disk.logical_size([
            *scope["parent"][category], *scope["preparation"][category],
            *scope["active"][category],
        ])
        if parent_bytes[category] != expected_parent[category]:
            raise RuntimeError(f"profile-bound immutable parent {category} baseline bytes changed")
        if full_bytes[category] != (parent_bytes[category] + preparation_bytes[category]
                                    + active_bytes[category]):
            raise RuntimeError(f"initial full {category} count differs from disjoint baseline plus live paths")
    result = {
        "schema": "v092-swift-resource-baseline/v1",
        "campaign_id": CAMPAIGN_ID,
        "observer_method": RESOURCE_OBSERVER_METHOD,
        "profile": scope["observer_profile"],
        "profile_expected_parent_baseline_bytes": scope["profile_expected_parent_baseline_bytes"],
        "post_profile_retained_additions": post_profile_additions,
        "closed_process_ownership": scope["closed_process_ownership"],
        "closed_process_ownership_state": scope["closed_process_ownership_state"],
        "portability_preflight": scope["portability_preflight"],
        "parent_campaign_starts": scope["campaign_start_references"],
        "parent_checkpoint": scope["parent_checkpoint"],
        "parent_capture_inventory": inventory,
        "parent_baseline_paths": {category: [str(path) for path in scope["parent"][category]]
                                  for category in categories},
        "preparation_baseline_paths": {category: [str(path) for path in scope["preparation"][category]]
                                       for category in categories},
        "active_paths": {category: [str(path) for path in scope["active"][category]]
                         for category in categories},
        "expected_parent_baseline_bytes": expected_parent,
        "measured_parent_baseline_bytes": parent_bytes,
        "measured_preparation_baseline_bytes": preparation_bytes,
        "combined_static_baseline_bytes": {
            category: parent_bytes[category] + preparation_bytes[category]
            for category in categories
        },
        "initial_active_bytes": active_bytes,
        "initial_full_bytes": full_bytes,
        "initial_full_equals_baseline_plus_live": True,
        "resource_limits_unchanged": {
            "working_bytes": 30 * GIB, "scratch_bytes": 24 * GIB,
            "retention_bytes": 24 * GIB, "launch_free_bytes": 127 * GIB,
            "continuous_free_bytes": 125 * GIB,
        },
        "qualification_status": "unqualified",
        "publication_eligible": False,
    }
    return result


def _verify_resource_baseline_unchanged(scope: dict, baseline_record: dict, disk) -> dict:
    post_profile_additions = _verify_post_profile_retained_additions(
        ROOT, scope.get("post_profile_retained_additions"))
    if baseline_record.get("post_profile_retained_additions") != post_profile_additions:
        raise RuntimeError("post-profile retained addition bindings changed during the supplement")
    categories = ("working", "retention", "scratch")
    observed_parent, observed_preparation = {}, {}
    for category in categories:
        observed_parent[category] = disk.logical_size(scope["parent"][category])
        observed_preparation[category] = disk.logical_size(scope["preparation"][category])
    if observed_parent != baseline_record["measured_parent_baseline_bytes"]:
        raise RuntimeError("immutable parent resource baseline changed during the supplement")
    if observed_preparation != baseline_record["measured_preparation_baseline_bytes"]:
        raise RuntimeError("closed preparation resource baseline changed during the supplement")
    for category in categories:
        combined = disk.logical_size([*scope["parent"][category], *scope["preparation"][category]])
        expected = observed_parent[category] + observed_preparation[category]
        if combined != expected:
            raise RuntimeError(f"static {category} baseline roots became overlapping or aliased")
    return {"schema": "v092-swift-resource-baseline-recheck/v1",
            "parent_baseline_bytes": observed_parent,
            "preparation_baseline_bytes": observed_preparation,
            "unchanged": True, "publication_eligible": False}


def _copy_bound_inputs(root: Path, source: Path, plan: dict) -> list[dict]:
    records = []
    for item in plan["source_projection"]["supplement_files_to_copy"]:
        relative, digest, mode = item["path"], item["sha256"], item["mode"]
        origin = _repo_file(root, relative)
        if sha(origin) != digest or stat.S_IMODE(origin.stat().st_mode) != mode:
            raise RuntimeError(f"supplement source input changed before copying: {relative}")
        target = _repo_file_parent_path(source, relative)
        if target.exists() or target.is_symlink():
            raise RuntimeError(f"supplement source input target already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
        target.chmod(mode)
        if sha(target) != digest or stat.S_IMODE(target.stat().st_mode) != mode:
            raise RuntimeError(f"copied supplement input failed byte/mode verification: {relative}")
        records.append({"path": relative, "sha256": digest, "mode": mode,
                        "source": str(origin), "destination": str(target)})
    return records


def _verify_source_inputs(source: Path, plan: dict) -> dict:
    # Frozen release files are validated through the detached source Git index;
    # additive v02 files are checked individually against the plan closure.
    core = _qualified_module(ROOT).legacy.core
    subprocess.run(["git", "diff", "--quiet", RELEASE, "--", "src", "cases", "populations",
                    "adapters", "scripts", "schemas", "corpus", "Cargo.toml", "Cargo.lock"],
                   cwd=source, check=True)
    expected = {row["path"]: row["sha256"] for row in plan["source_projection"]["supplement_files_to_copy"]}
    for row in [*plan["input_reference_closure"], *plan["postprocessing_dependencies"],
                *plan["source_projection"]["execution_plan_inputs"]]:
        relative, digest = row["path"], row["sha256"]
        path = _repo_file(source, relative)
        if sha(path) != digest:
            raise RuntimeError(f"prepared source input changed: {relative}")
        expected.setdefault(relative, digest)
    return {"release_commit": RELEASE, "tracked_release_projection_clean": True,
            "supplement_input_count": len(expected), "supplement_inputs": expected}


def _source_runner(source: Path):
    return _load_runner(source)


class _SupplementDiskGuard:
    def __init__(self, delegate, source: Path, observation_callback, resource_scope: dict):
        self.delegate = delegate
        self.source = source
        self.observation_callback = observation_callback
        self.resource_scope = resource_scope
        self.baseline_record: dict | None = None

    @property
    def chunk_bytes(self) -> int:
        return self.delegate.chunk_bytes

    def error(self, code: str, message: str, **metadata):
        return self.delegate.error(code, message, **metadata)

    def bind_baseline(self, record: dict) -> None:
        if (self.baseline_record is not None
                or record.get("schema") != "v092-swift-resource-baseline/v1"
                or record.get("initial_full_equals_baseline_plus_live") is not True):
            raise RuntimeError("immutable resource baseline is missing, malformed, or already bound")
        self.baseline_record = record

    def check(self, **kwargs):
        self.observation_callback()
        category = kwargs.get("category")
        canonical = {"source": "working", "working_source": "working", "working": "working",
                     "retention": "retention", "retained": "retention", "scratch": "scratch"}.get(category)
        if canonical is None or self.baseline_record is None:
            raise RuntimeError("resource guard check lacks a bound category baseline")
        supplied_paths = {str(Path(value)) for value in kwargs.get("paths", ())}
        expected_paths = {str(path) for path in self.resource_scope["all"][canonical]}
        if supplied_paths != expected_paths:
            raise RuntimeError(f"resource guard caller changed the bound {canonical} accounting roots")
        baseline_bytes = self.baseline_record["combined_static_baseline_bytes"][canonical]
        kwargs["paths"] = self.resource_scope["active"][canonical]
        kwargs["additional_current_bytes"] = baseline_bytes
        result = self.delegate.check(**kwargs)
        size = result["current_bytes"] - baseline_bytes if canonical == "working" else 0
        if size < 0:
            raise RuntimeError("working resource probe returned less than its immutable baseline")
        if size > 12 * GIB:
            raise _qualified_module(ROOT).legacy.disk.DiskGuardError(
                "per_source_ceiling", "supplement source exceeded its 12 GiB ceiling",
                source=str(self.source), source_bytes=size, limit_bytes=12 * GIB,
            )
        return result

    def check_capacity(self, **kwargs):
        return self.delegate.check_capacity(**kwargs)


class _AdmissionWindowExpired(RuntimeError):
    def __init__(self, sample_monotonic_seconds: float, now_monotonic_seconds: float):
        self.sample_monotonic_seconds = sample_monotonic_seconds
        self.now_monotonic_seconds = now_monotonic_seconds
        self.age_seconds = now_monotonic_seconds - sample_monotonic_seconds
        super().__init__("admission observation became stale before child process creation")


def _run_process_with_fresh_admission(process_runner, popen_module, argv: list[str],
                                      cwd: Path, output_path: Path,
                                      sample_monotonic_seconds: float):
    """Guard the exact analyzer Popen call, after the runner's capacity preflight."""
    if output_path.exists() or output_path.is_symlink():
        raise RuntimeError("fresh Joern output path must be absent when the runner is dispatched")
    original_popen = popen_module.Popen
    observed: dict[str, float] = {}

    def guarded_popen(command, *args, **kwargs):
        raw_cwd = kwargs.get("cwd")
        matches_cwd = isinstance(raw_cwd, (str, os.PathLike)) and str(Path(raw_cwd)) == str(cwd)
        matches_command = (not isinstance(command, (str, bytes))
                           and list(command) == argv)
        if matches_command and matches_cwd:
            now = time.monotonic()
            age = now - sample_monotonic_seconds
            if age < 0 or age > MAX_SAMPLE_GAP_SECONDS:
                raise _AdmissionWindowExpired(sample_monotonic_seconds, now)
            if "popen_monotonic_seconds" in observed:
                raise RuntimeError("supplement attempted to create the analyzer process more than once")
            observed["popen_monotonic_seconds"] = now
            observed["sample_age_seconds_at_popen"] = age
        return original_popen(command, *args, **kwargs)

    popen_module.Popen = guarded_popen
    try:
        result = process_runner()
    finally:
        popen_module.Popen = original_popen
    return result, observed


def _fresh_output_path(source: Path) -> Path:
    output = source / OUTPUT_RELATIVE
    if not output.resolve(strict=False).is_relative_to(source.resolve(strict=True)):
        raise RuntimeError("Joern output path escapes the fresh supplement source")
    cursor = source
    for part in PurePosixPath(OUTPUT_RELATIVE).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"Joern output path traverses a symlink: {cursor}")
    if output.exists():
        raise RuntimeError("fresh Joern output path already exists")
    return output


def _append_host_sample(host, raw_path: Path, assessment_path: Path,
                        phase: str, root_pid: int | None = None) -> dict | None:
    try:
        observation = host.snapshot(ROOT)
    except Exception as exc:
        failure = host.failure_record(exc)
        _append_jsonl(raw_path, failure)
        _append_jsonl(assessment_path, {
            "schema": "v092-swift-supplement-admission-assessment/v1",
            "phase": phase, "observation_complete": False,
            "observation_error": f"{type(exc).__name__}: {exc}",
            "quiet": False, "diagnostic_background_admissible": False,
            "settled_quiet_window_established": False,
            "original_a24_settled_qualification_eligible": False,
            "publication_eligible": False,
        })
        return None
    _append_raw_observation(raw_path, observation)
    try:
        assessment = assess_admission(observation, host, root_pid=root_pid)
    except Exception as exc:
        assessment = {
            "schema": "v092-swift-supplement-admission-assessment/v1",
            "observation_complete": False,
            "assessment_error": f"{type(exc).__name__}: {exc}",
            "quiet": False,
            "diagnostic_background_admissible": False,
            "settled_quiet_window_established": False,
            "original_a24_settled_qualification_eligible": False,
            "publication_eligible": False,
        }
    assessment.update({"phase": phase, "observed_at_utc": observation.get("observed_at_utc"),
                       "monotonic_seconds": observation.get("monotonic_seconds")})
    _append_jsonl(assessment_path, assessment)
    return observation


def _wait_initial_quiet(host, raw_path: Path, assessment_path: Path,
                        deadline: float, capacity_check) -> dict:
    window = QuietAdmissionWindow()
    last = None
    while time.monotonic() < deadline:
        capacity_check(launch=True)
        observation = _append_host_sample(host, raw_path, assessment_path, "initial-admission")
        if observation is None:
            window.reset()
        else:
            try:
                assessment = assess_admission(observation, host)
            except Exception:
                assessment = {"quiet": False}
            if window.observe(assessment, float(observation.get("monotonic_seconds", -1.0))):
                last = observation
                return {"status": "complete-quiet-window", "required_seconds": QUIET_SECONDS,
                        "observed_seconds": window.elapsed_seconds, "samples": window.samples,
                        "last_observation_utc": last["observed_at_utc"],
                        "last_observation_monotonic_seconds": float(last["monotonic_seconds"]),
                        "aggregate_cpu_idle_percent_raw": last["cpu_idle_percent"],
                        "original_a24_settled_qualification_eligible": False}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(SAMPLE_INTERVAL_SECONDS, remaining))
    raise RuntimeError("bounded campaign wall elapsed before a fresh 300-second quiet admission")


def _wait_diagnostic_admission(host, raw_path: Path, assessment_path: Path,
                               deadline: float, capacity_check) -> dict:
    """Wait for a complete low-contention snapshot without claiming settled quiet."""
    while time.monotonic() < deadline:
        capacity_check(launch=True)
        observation = _append_host_sample(host, raw_path, assessment_path, "diagnostic-admission")
        if observation is not None:
            try:
                assessment = assess_admission(observation, host)
            except Exception:
                assessment = None
            if assessment is not None and assessment.get("diagnostic_background_admissible") is True:
                return {
                    "status": "diagnostic-background-admission",
                    "required_seconds": 0,
                    "observed_seconds": 0,
                    "samples": 1,
                    "admission_basis": "complete snapshot with no non-tolerated heavy process or significant external CPU",
                    "last_observation_utc": observation["observed_at_utc"],
                    "last_observation_monotonic_seconds": float(observation["monotonic_seconds"]),
                    "aggregate_cpu_idle_percent_raw": observation["cpu_idle_percent"],
                    "aggregate_cpu_idle_met_certification_threshold": (
                        float(observation["cpu_idle_percent"]) >= QUIET_IDLE_PERCENT
                    ),
                    "non_tolerated_heavy_processes": assessment["non_tolerated_heavy_processes"],
                    "significant_external_cpu": assessment["significant_external_cpu"],
                    "non_tolerated_external_cpu_percent": assessment["non_tolerated_external_cpu_percent"],
                    "quiescent_service_pids": assessment["quiescent_service_pids"],
                    "service_observations": assessment["service_observations"],
                    "settled_quiet_window_established": False,
                    "original_a24_settled_qualification_eligible": False,
                    "publication_eligible": False,
                }
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(SAMPLE_INTERVAL_SECONDS, remaining))
    raise RuntimeError("bounded campaign wall elapsed before a complete diagnostic background admission")


def _record_runtime_receipts(source: Path, runner, plan_path: str) -> dict:
    plan, evidence, _context = runner.validate_plan(source, plan_path)
    manifests = _component_manifest_references(source, plan)
    return {"status": evidence["status"], "runtime_component_manifests": manifests,
            "runtime_legacy_inventories": plan["runtime"]["inventories"],
            "identity_components": plan["identity_components"],
            "identity": plan["identity"], "population_sha256": plan["population_sha256"],
            "fixture_revision": plan["fixture_revision"],
            "execution_eligible": plan["execution_eligible"],
            "diagnostic_execution_eligible": plan["diagnostic_execution_eligible"],
            "full_model_qualification": plan["full_model_qualification"],
            "qualification_publication_state": _qualification_publication_state(evidence),
            "publication_eligible": False}


def _normal_audit_path(output: Path) -> Path:
    return output / "normal" / "audit.json"


def _validate_outputs(root: Path, source: Path, plan: dict, qualified_plan: dict) -> dict:
    q = _qualified_module(root)
    group = plan["group"]
    output = source / OUTPUT_RELATIVE
    run_path = output / "run.json"
    if run_path.is_symlink() or not run_path.is_file():
        raise RuntimeError("Joern raw run.json is missing")
    run = _read_json(run_path)
    results = run.get("results")
    expected_ids = set(group["case_ids"])
    result_ids = [row.get("case_id") for row in results] if isinstance(results, list) else []
    if (run.get("schema") != "joern-common-run/v092" or len(result_ids) != CASE_COUNT
            or len(set(result_ids)) != CASE_COUNT or set(result_ids) != expected_ids
            or run.get("population_sha256") != plan["population_sha256"]
            or run.get("fixture_revision") != plan["fixture_revision"]
            or run.get("identity") != qualified_plan["identity"]
            or run.get("scored_activation") is not False
            or run.get("aggregate_resource_qualification") != "unavailable"):
        raise RuntimeError("Joern raw run identity or 108-case membership is incomplete")
    capability_replay = _load_runner(source).verify_raw_capability_rows(source, qualified_plan, run)
    if (capability_replay.get("schema") != "joern-v092-capability-raw-replay/v2"
            or capability_replay.get("status") != "verified"
            or capability_replay.get("source") != plan["capability_binding"]["source"]
            or capability_replay.get("attempt_count") != 96
            or capability_replay.get("unsupported_count") != 12
            or capability_replay.get("raw_rows") != CASE_COUNT):
        raise RuntimeError("measured raw reports do not preserve all 96 source-bound capabilities and 12 unsupported cases")
    original_report_paths = [source / row["source_path"] for row in group["reports"]]
    original_report_hashes = {path: sha(path) for path in original_report_paths}
    configuration_hash_module_path = source / "scripts/joern_normal_reports_v092_projection.py"
    projection_module_path = source / CAPABILITY_V3_REPORTER_PATH
    if (not configuration_hash_module_path.is_file() or configuration_hash_module_path.is_symlink()
            or sha(configuration_hash_module_path) != plan["execution_helpers"].get(
                "scripts/joern_normal_reports_v092_projection.py")
            or plan.get("configuration_hash_helper") != {
                "path": "scripts/joern_normal_reports_v092_projection.py",
                "sha256": plan["execution_helpers"].get("scripts/joern_normal_reports_v092_projection.py")}
            or not projection_module_path.is_file() or projection_module_path.is_symlink()
            or sha(projection_module_path) != plan["execution_helpers"].get(CAPABILITY_V3_REPORTER_PATH)
            or plan.get("projection_exporter") != {
                "path": CAPABILITY_V3_REPORTER_PATH,
                "sha256": plan["execution_helpers"].get(CAPABILITY_V3_REPORTER_PATH)}):
        raise RuntimeError("bound capability-aware normalized-report projection helper is missing or changed")
    projection_dependencies = (
        "swift_common_population_v2", "swift_normal_reports_v1", "joern_normal_reports_v092_projection",
    )
    saved_projection_dependencies = {
        name: sys.modules.pop(name) for name in projection_dependencies if name in sys.modules
    }
    sys.path.insert(0, str(source / "scripts"))
    try:
        projector = _load_module("swift_supplement_report_projector", projection_module_path)
    finally:
        try:
            sys.path.remove(str(source / "scripts"))
        except ValueError:
            pass
        sys.modules.update(saved_projection_dependencies)
    derived_output = source / DERIVED_RELATIVE
    if derived_output.exists() or derived_output.is_symlink():
        raise RuntimeError("derived report namespace is not fresh")
    derived_output.parent.mkdir(parents=True, exist_ok=True)
    written = projector.export_projection(source, QUALIFIED_PLAN_PATH, run, derived_output)
    if len(written) != REPORT_PARTITION_COUNT:
        raise RuntimeError("projection exporter did not write exactly five derived reports")
    candidate_configuration_hash = projector.configuration_hash(source, qualified_plan)
    if candidate_configuration_hash != plan["configuration_provenance"]["candidate_configuration_hash"]:
        raise RuntimeError("projection exporter configuration hash differs from the bound candidate closure")
    if any(sha(path) != digest for path, digest in original_report_hashes.items()):
        raise RuntimeError("projection exporter modified one of the five original normalized reports")
    runtime_script_dir = source / "scripts"
    normalizer_dependency_names = ("swift_normal_reports_v1",)
    saved_normalizer_dependencies = {
        name: sys.modules.pop(name) for name in normalizer_dependency_names if name in sys.modules
    }
    sys.path.insert(0, str(runtime_script_dir))
    try:
        normalizer = _load_module(
            "swift_supplement_normalizer", runtime_script_dir / "swift_normal_reports_v1.py")
        normalized_outcome = normalizer.normalized
    finally:
        try:
            sys.path.remove(str(runtime_script_dir))
        except ValueError:
            pass
        sys.modules.update(saved_normalizer_dependencies)
    raw_by_id = {}
    case_timing_rows = []
    for row in results:
        case_id = row.get("case_id")
        if case_id in raw_by_id:
            raise RuntimeError(f"duplicate Joern run case row: {case_id}")
        selection = qualified_plan["cases"].get(case_id)
        if not isinstance(selection, dict) or row.get("configuration") != selection.get("configuration"):
            raise RuntimeError(f"Joern raw result configuration binding differs: {case_id}")
        raw_path = _validate_reference(source, row.get("raw"))
        raw = _read_json(raw_path)
        if raw.get("schema") != "joern-common-raw/v092":
            raise RuntimeError(f"Joern raw result schema changed: {case_id}")
        expected_raw_fields = {
            "case_id": case_id,
            "plan_sha256": sha(_repo_file(source, QUALIFIED_PLAN_PATH)),
            "qualification_sha256": qualified_plan["fresh_qualification"]["sha256"],
            "population_sha256": plan["population_sha256"],
            "fixture_revision": plan["fixture_revision"],
            "configuration": selection["configuration"],
            "identity": qualified_plan["identity"],
        }
        for field, expected_value in expected_raw_fields.items():
            if raw.get(field) != expected_value:
                raise RuntimeError(f"Joern raw result lost its bound {field}: {case_id}")
        if (raw.get("state") != normalized_outcome(raw.get("raw_outcome"))
                or not isinstance(raw.get("diagnostics"), list)
                or any(not isinstance(item, str) for item in raw["diagnostics"])
                or not isinstance(raw.get("witness_checkpoints"), list)
                or any(not isinstance(item, str) for item in raw["witness_checkpoints"])):
            raise RuntimeError(f"Joern raw outcome/diagnostic/checkpoint evidence is malformed: {case_id}")
        expected_disposition = selection.get("disposition")
        timing_row = _validate_case_artifact_refs(source, raw_path, raw, expected_disposition)
        timing_row["raw_output"] = row["raw"]
        timing_row["semantic_uncertainty"] = plan["semantic_uncertainty"]
        case_timing_rows.append(timing_row)
        raw_by_id[case_id] = {"row": row, "ref": row["raw"], "raw": raw}

    timing_counts = {
        "attempted_cost_rows": sum(row["executed"] is True for row in case_timing_rows),
        "unsupported_no_invocation_rows": sum(row["executed"] is False for row in case_timing_rows),
        "latency_sample_rows": sum(row["latency_sample_included"] is True for row in case_timing_rows),
    }
    if timing_counts != {"attempted_cost_rows": 96, "unsupported_no_invocation_rows": 12,
                         "latency_sample_rows": 96}:
        raise RuntimeError(f"Joern timing rows do not preserve 96 attempts and 12 unsupported cases: {timing_counts}")
    case_timing_rows.sort(key=lambda row: row["case_id"])

    base_plan = _read_json(_repo_file(root, BASE_PLAN_PATH))
    base_bindings = plan["frozen_report_bindings"]
    reports = []
    semantic_mismatches = []
    for index, descriptor in enumerate(group["reports"]):
        relative = descriptor["source_path"]
        path = _repo_file(source, relative)
        report = _read_json(path)
        if "configuration_hash" in report:
            raise RuntimeError("original normalized report already contains configuration_hash; raw evidence must remain unchanged")
        derived_relative = f"{DERIVED_RELATIVE}/report-{index}.json"
        derived_path = _repo_file(source, derived_relative)
        derived = _read_json(derived_path)
        actual_rows = derived.get("results", [])
        actual_ids = [row.get("case_id") for row in actual_rows]
        if (len(actual_ids) != len(descriptor["case_ids"])
                or len(set(actual_ids)) != len(actual_ids)
                or set(actual_ids) != set(descriptor["case_ids"])):
            raise RuntimeError(f"normalized report partition membership differs: {relative}")
        binding = base_bindings[index]
        frozen_git_path, frozen_raw = q._frozen_report_blob(root, descriptor["path"])
        frozen_sha = hashlib.sha256(frozen_raw).hexdigest()
        if frozen_git_path != binding["git_path"] or frozen_sha != binding["sha256"]:
            raise RuntimeError(f"frozen report bytes no longer match the retained plan binding: {relative}")
        frozen = json.loads(frozen_raw)
        try:
            validate_projection_only(report, derived, candidate_configuration_hash)
        except RuntimeError as exc:
            raise RuntimeError(f"derived report changed fields beyond configuration_hash: {derived_relative}: {exc}") from exc
        frozen_by_id = {item["case_id"]: item for item in frozen.get("results", [])}
        actual_by_id = {item["case_id"]: item for item in actual_rows}
        for field in IDENTITY_FIELDS:
            if field == "configuration_hash":
                if (frozen.get(field) != plan["configuration_provenance"]["historical_configuration_hash"]
                        or derived.get(field) != candidate_configuration_hash):
                    semantic_mismatches.append({"report": relative, "field": field,
                                                "classification": "configuration-closure-transition-mismatch",
                                                "expected_old": plan["configuration_provenance"]["historical_configuration_hash"],
                                                "expected_new": candidate_configuration_hash,
                                                "frozen": frozen.get(field), "derived": derived.get(field)})
                continue
            if field not in frozen or field not in derived or frozen[field] != derived[field]:
                semantic_mismatches.append({"report": relative, "field": field,
                                            "classification": "identity-mismatch",
                                            "expected": frozen.get(field), "actual": derived.get(field)})
        for case_id in descriptor["case_ids"]:
            expected = frozen_by_id.get(case_id)
            actual = actual_by_id[case_id]
            raw_binding = raw_by_id.get(case_id)
            if expected is None or raw_binding is None:
                raise RuntimeError(f"frozen/raw case evidence is missing: {case_id}")
            raw = raw_binding["raw"]
            raw_ref = raw_binding["ref"]
            derived_diagnostics = sorted(set(raw["diagnostics"] + ["AggregateResourceQualificationUnavailable"]))
            if actual.get("outcome") != raw["state"]:
                raise RuntimeError(f"normalized report outcome does not follow its bound raw result: {case_id}")
            if actual.get("diagnostics") != derived_diagnostics:
                raise RuntimeError(f"normalized report diagnostics do not follow raw evidence: {case_id}")
            if actual.get("witness_checkpoints") != raw["witness_checkpoints"]:
                raise RuntimeError(f"normalized report checkpoints do not follow raw evidence: {case_id}")
            if actual.get("raw_output") != raw_ref.get("path") or actual.get("raw_sha256") != raw_ref.get("sha256"):
                raise RuntimeError(f"normalized report raw-output binding differs: {case_id}")
            for field in ("outcome", "diagnostics", "witness_checkpoints", "source_anchors", "sink_anchors"):
                if actual.get(field) != expected.get(field):
                    semantic_mismatches.append({"report": relative, "case_id": case_id,
                                                "field": field, "classification": "semantic-mismatch",
                                                "expected": expected.get(field), "actual": actual.get(field)})
        reports.append({"original_path": relative, "original_sha256": sha(path),
                        "derived_path": derived_relative, "derived_sha256": sha(derived_path),
                        "case_count": len(actual_ids),
                        "configuration_hash": candidate_configuration_hash,
                        "projection_only_field": "configuration_hash"})
    audit_path = _normal_audit_path(output)
    audit = _read_json(audit_path)
    audit_rows = audit.get("results")
    if (not isinstance(audit_rows, list) or len(audit_rows) != CASE_COUNT
            or {row.get("case_id") for row in audit_rows} != expected_ids):
        raise RuntimeError("Joern audit artifact does not preserve all 108 case outcomes")
    for row in audit_rows:
        bound = raw_by_id.get(row["case_id"])
        if (bound is None or row.get("raw_outcome") != bound["raw"].get("raw_outcome")
                or row.get("outcome") != bound["raw"].get("state")
                or row.get("raw_sha256") != bound["ref"].get("sha256")):
            raise RuntimeError(f"Joern audit raw/outcome binding differs: {row.get('case_id')}")
    reconciliation = q.legacy.reconcile(group, source)
    comparison = {
        "status": "matched" if not semantic_mismatches else "mismatch",
        "group": GROUP_ID,
        "reports": reports,
        "per_case_count": len(raw_by_id),
        "case_disposition_counts": {"attempt": timing_counts["attempted_cost_rows"],
                                     "unsupported": timing_counts["unsupported_no_invocation_rows"]},
        "case_timing_rows": case_timing_rows,
        "timing_row_counts": timing_counts,
        "timing_row_policy": {
            "attempted_cost_rows_included_even_when_inconclusive_or_runner_error": True,
            "unsupported_no_invocation_zero_duration_excluded": True,
            "attempted_rows_are_certified_successes": False,
            "full_model_qualification": False,
        },
        "outcome_diagnostic_checkpoint_rows_checked": len(raw_by_id),
        "capability_source_replay": capability_replay,
        "mismatches": semantic_mismatches,
        "configuration_provenance": plan["configuration_provenance"],
        "semantic_uncertainty": plan["semantic_uncertainty"],
        "projection_exporter": dict(plan["projection_exporter"]),
        "configuration_hash_helper": dict(plan["configuration_hash_helper"]),
        "raw_normal_reports_unchanged": True,
        "derived_namespace": str(derived_output),
        "comparison_scope": (
            "all five frozen report partitions; exact non-configuration identity fields; all 108 outcomes, "
            "diagnostics, witness checkpoints, source/sink anchors, and raw evidence links. Configuration "
            "closure change is separately hash-bound as provenance and appears only in derived projections; "
            "original normalized report bytes remain unchanged."),
        "publication_eligible": False,
    }
    return {"run_path": str(run_path), "run_sha256": sha(run_path),
            "result_count": len(result_ids), "reports": reports,
            "reconciliation": reconciliation, "frozen_report_comparison": comparison,
            "status": comparison["status"], "publication_eligible": False}


def _campaign_paths(root: Path, plan: dict) -> tuple[Path, Path, Path, Path]:
    report = root / REPORT_ROOT
    work = root / WORK_ROOT
    source = root / SOURCE_RELATIVE
    attempt = root / ATTEMPT_RELATIVE
    if not report.is_dir() or report.is_symlink():
        raise RuntimeError(f"supplement report namespace is missing or redirected: {report}")
    expected_report_entries = {"supplement-plan-01.json"}
    if {path.name for path in report.iterdir()} != expected_report_entries:
        raise RuntimeError("supplement report namespace contains preexisting or unexpected evidence")
    for path in (work, source, attempt, source / OUTPUT_RELATIVE, source / DERIVED_RELATIVE):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"supplement namespace is already in use: {path}")
    return report, work, source, attempt


def verify_plan(plan_path: str = PLAN_PATH) -> dict:
    if plan_path != PLAN_PATH:
        raise RuntimeError("only the fixed v0.9.2-07 supplement plan is accepted")
    path = _repo_file(ROOT, plan_path)
    plan = _read_json(path)
    validate_campaign_plan(plan)
    if not isinstance(plan.get("created_utc"), str) or not plan["created_utc"]:
        raise RuntimeError("supplement plan creation timestamp is malformed")
    expected = _derive_plan(ROOT, plan["created_utc"])
    if plan != expected:
        raise RuntimeError("supplement plan differs from its exact parent, source, runtime, or qualification derivation")
    try:
        committed_plan = subprocess.check_output(["git", "show", f"HEAD:{plan_path}"], cwd=ROOT)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("supplement execution plan must be committed before dispatch") from exc
    if _sha_bytes(committed_plan) != sha(path):
        raise RuntimeError("committed supplement plan differs from its prepared bytes")
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--", plan_path], cwd=ROOT, text=True)
    if status.strip():
        raise RuntimeError("supplement execution plan has uncommitted edits")
    return {"status": "verified-unqualified", "campaign_id": CAMPAIGN_ID,
            "group_id": GROUP_ID, "case_count": CASE_COUNT,
            "report_partition_count": REPORT_PARTITION_COUNT,
            "execution_authorized_by_plan": True, "publication_eligible": False,
            "diagnostic_execution_eligible": True, "full_model_qualification": False}


def _disk_guard(root: Path, source: Path, host, raw_host: Path, assessment: Path,
                ownership: dict, resource_scope: dict):
    q = _qualified_module(root)
    delegate = q.legacy.disk.DiskGuard(
        launch_floor_bytes=127 * GIB, stop_floor_bytes=125 * GIB,
        working_ceiling_bytes=30 * GIB, scratch_ceiling_bytes=24 * GIB,
        retention_ceiling_bytes=24 * GIB,
    )
    last_sample = [0.0]

    def observe_if_due():
        if ownership.get("root_pid") and time.monotonic() - last_sample[0] >= SAMPLE_INTERVAL_SECONDS:
            _append_host_sample(host, raw_host, assessment, "analyzer-active", ownership["root_pid"])
            last_sample[0] = time.monotonic()

    guard = _SupplementDiskGuard(delegate, source, observe_if_due, resource_scope)
    return guard


def execute(plan_path: str = PLAN_PATH) -> dict:
    verified = verify_plan(plan_path)
    plan_file = _repo_file(ROOT, plan_path)
    plan = _read_json(plan_file)
    report, work, source, attempt = _campaign_paths(ROOT, plan)
    q = _qualified_module(ROOT)
    base_plan = _read_json(_repo_file(ROOT, BASE_PLAN_PATH))
    resource_paths = _safe_accounting_scope(ROOT, plan)
    raw_host = _load_module("swift_supplement_host", ROOT / "scripts/v092_timing_host.py")
    host = _admission_host(ROOT, raw_host, q.legacy)
    lock = q.legacy.core._exclusive_lock
    dispatch_started = time.monotonic()
    dispatch_deadline = dispatch_started + MAX_CAMPAIGN_WALL_SECONDS
    ownership: dict = {}
    attempt_record: dict = {"group": GROUP_ID, "attempt": 1, "automatic_retry": False,
                            "old_argv": plan["old_argv"], "argv": plan["argv"],
                            "publication_eligible": False}
    launcher_dependency_proofs: dict[str, dict] = {}
    with lock():
        # Revalidate all bound inputs after acquiring the analyzer-wide lock.
        verify_plan(plan_path)
        work.mkdir(parents=True, exist_ok=False)
        (work / "sources").mkdir(parents=True, exist_ok=False)
        attempt.mkdir(parents=True, exist_ok=False)
        raw_host = attempt / "host.jsonl"
        assessments = attempt / "admission-assessments.jsonl"
        report_start = {
            "schema": "v092-timing-swift-supplement-start/v1",
            "campaign_id": CAMPAIGN_ID, "plan_sha256": sha(plan_file),
            "group_id": GROUP_ID, "dispatch_groups": [GROUP_ID],
            "parent_plan": plan["base_plan"], "parent_terminal": plan["base_terminal"],
            "capture_inventory": plan["capture_inventory"],
            "semgrep_retrospective_audit": plan["semgrep_retrospective_audit"],
            "old_argv": plan["old_argv"], "actual_argv": plan["argv"],
            "launcher_prerequisite_preflight": plan["launcher_prerequisite_preflight"],
            "source_commit": RELEASE, "source": str(source),
            "diagnostic_authorization": plan["diagnostic_authorization"],
            "resource_scope": plan["resource_scope"],
            "resource_observer_profile": plan["resource_scope"]["observer_profile"],
            "resource_observer_method": RESOURCE_OBSERVER_METHOD,
            "resource_baseline_path": RESOURCE_BASELINE_PATH,
            "resources": plan["resources"], "deadline_seconds": GROUP_TIMEOUT_SECONDS,
            "publication_eligible": False,
            "settled_quiet_window_established": False,
            "original_a24_settled_qualification_eligible": False,
        }
        try:
            _campaign_artifacts = (report / "campaign-terminal.json", report / "launch-failure-001.json")
            if any(path.exists() or path.is_symlink() for path in _campaign_artifacts):
                raise RuntimeError("campaign terminal/failure receipt unexpectedly exists")
            retained_paths = resource_paths["all"]["retention"]
            working_paths = resource_paths["all"]["working"]
            scratch_paths = resource_paths["all"]["scratch"]
            free = shutil.disk_usage(ROOT).free
            if free < 127 * GIB:
                raise RuntimeError(f"launch free space below 127 GiB: {free} bytes")
            disk = _disk_guard(ROOT, source, host, raw_host, assessments, ownership, resource_paths)
            tracker = q.legacy.core._process_tracker()
            supervisor_identity = tracker._start_identity(os.getpid())
            if supervisor_identity is None:
                raise RuntimeError("controller process start identity was unavailable before resource baseline")
            baseline_record = _measure_resource_baseline(ROOT, resource_paths, disk.delegate)
            baseline_record["supervisor_pid"] = os.getpid()
            baseline_record["supervisor_start_identity"] = supervisor_identity
            baseline_path = ROOT / RESOURCE_BASELINE_PATH
            _write_new(baseline_path, baseline_record)
            baseline_ref = {"path": RESOURCE_BASELINE_PATH, "sha256": sha(baseline_path)}
            disk.bind_baseline(baseline_record)
            attempt_record["resource_baseline"] = baseline_ref
            report_start["resource_baseline"] = baseline_ref
            report_start["supervisor_pid"] = os.getpid()
            report_start["supervisor_start_identity"] = supervisor_identity
            closed_prior_processes = _observe_closed_prior_processes(ROOT, q.legacy)
            report_start["closed_prior_processes"] = closed_prior_processes
            attempt_record["closed_prior_processes"] = closed_prior_processes
            _write_new(report / "campaign-start.json", report_start)
            _append_jsonl(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                                       "phase": "source-materialization-starting",
                                                       "group": GROUP_ID, "analyzer_dispatched": False})
            disk.check(category="working", paths=working_paths, capacity_path=ROOT, phase="launch")
            disk.check(category="retention", paths=retained_paths, capacity_path=ROOT, phase="launch")
            disk.check(category="scratch", paths=scratch_paths, capacity_path=ROOT, phase="launch")

            explicit = plan["source_projection"]["additional_paths"]
            source.parent.mkdir(parents=True, exist_ok=True)
            projected = q.legacy.core._materialize_source(
                ROOT, RELEASE, source, explicit, disk_guard=disk,
                working_paths=working_paths, preflight_only=True,
            )
            if projected > 12 * GIB:
                raise RuntimeError("source archive projection exceeds the 12 GiB per-source limit")
            q.legacy.core._materialize_source(
                ROOT, RELEASE, source, explicit, disk_guard=disk,
                working_paths=working_paths, expected_projected_bytes=projected,
            )
            q.legacy.core._register_source_snapshot(ROOT, RELEASE, source)
            _append_jsonl(report / "preparation-progress.jsonl", {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "phase": "base-source-materialized",
                "source": str(source), "source_archive_bytes": projected,
            })
            copied_inputs = _copy_bound_inputs(ROOT, source, plan)
            for directory in ("home", "tmp", "cache"):
                target = source / directory
                if target.exists() or target.is_symlink():
                    raise RuntimeError(f"attempt-local scratch path already exists: {target}")
                target.mkdir(mode=0o700)
            output = _fresh_output_path(source)
            output.parent.mkdir(parents=True, exist_ok=True)
            output = _fresh_output_path(source)
            source_probe = disk.check(category="working", paths=working_paths,
                                      capacity_path=ROOT, phase="launch")
            source_bytes = (source_probe["current_bytes"]
                            - baseline_record["combined_static_baseline_bytes"]["working"])
            if source_bytes < 0 or source_bytes > 12 * GIB:
                raise RuntimeError("prepared supplement source exceeds its 12 GiB per-source limit")
            source_runner = _source_runner(source)
            pre_runtime = _record_runtime_receipts(source, source_runner, QUALIFIED_PLAN_PATH)
            source_input_proof = _verify_source_inputs(source, plan)
            # This full derivation and committed-input check belongs before
            # the quiet window. Post-window gates use only the exact plan bytes.
            verify_plan(plan_path)
            dispatch_plan_sha256 = sha(plan_file)
            if dispatch_plan_sha256 != report_start["plan_sha256"]:
                raise RuntimeError("supplement plan digest changed during source preparation")
            environment = {
                key: value.replace("@SUPPLEMENT_SOURCE@", str(source))
                for key, value in plan["environment"].items()
            }
            if any("@SUPPLEMENT_SOURCE@" in value for value in environment.values()):
                raise RuntimeError("unresolved supplement environment marker")
            _append_jsonl(report / "preparation-progress.jsonl", {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "phase": "inputs-and-runtime-verified",
                "copied_input_count": len(copied_inputs), "source_bytes": source_bytes,
                "runtime_receipts": pre_runtime, "source_input_proof": source_input_proof,
                "plan_sha256": dispatch_plan_sha256,
            })

            admission_ledger = attempt / "dispatch-admissions.jsonl"
            admission_sequence = 0
            start_written = False
            while True:
                admission = _wait_diagnostic_admission(
                    host, raw_host, assessments, dispatch_deadline,
                    lambda launch: _check_capacity(disk, retained_paths, working_paths, scratch_paths, launch),
                )
                admission_sequence += 1
                admission_id = f"diagnostic-admission-{admission_sequence:02d}"
                _append_jsonl(admission_ledger, {
                    "event": "diagnostic-admission", "admission_id": admission_id,
                    "admission": admission, "used_for_dispatch": False,
                    "settled_quiet_window_established": False,
                    "publication_eligible": False,
                })
                try:
                    if sha(plan_file) != dispatch_plan_sha256:
                        raise RuntimeError("supplement plan digest changed after diagnostic admission")
                    if tracker._start_identity(os.getpid()) != supervisor_identity:
                        raise RuntimeError("controller process identity changed before dispatch")
                    output = _fresh_output_path(source)
                    _check_capacity(disk, retained_paths, working_paths, scratch_paths, True)
                    if not start_written:
                        start = {
                            "schema": "v092-timing-swift-supplement-attempt-start/v1",
                            "campaign_id": CAMPAIGN_ID, "group": GROUP_ID, "attempt": 1,
                            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "argv": plan["argv"], "old_frozen_argv": plan["old_argv"],
                            "cwd": str(source), "environment": environment,
                            "deadline_seconds": GROUP_TIMEOUT_SECONDS,
                            "initial_diagnostic_admission": admission,
                            "diagnostic_admission_is_sufficient_dispatch_authorization": False,
                            "dispatch_admissions_path": f"{ATTEMPT_RELATIVE}/dispatch-admissions.jsonl",
                            "admission_policy": plan["admission_policy"],
                            "diagnostic_authorization": plan["diagnostic_authorization"],
                            "launcher_prerequisite_preflight": plan["launcher_prerequisite_preflight"],
                            "settled_quiet_window_established": False,
                            "original_a24_settled_qualification_eligible": False,
                            "runtime_manifests_before_dispatch": pre_runtime,
                            "source_input_proof_before_dispatch": source_input_proof,
                            "plan_sha256_before_dispatch": dispatch_plan_sha256,
                            "supervisor_pid": os.getpid(), "supervisor_start_identity": supervisor_identity,
                            "resource_baseline": baseline_ref,
                            "automatic_retry": False, "publication_eligible": False,
                        }
                        _write_new(attempt / "start.json", start)
                        start_written = True
                    _append_jsonl(report / "progress.jsonl", {
                        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "group": GROUP_ID, "status": "dispatch-preflight-ready",
                        "admission_id": admission_id, "analyzer_dispatched": False,
                    })
                    command_started = time.monotonic()

                    def run_one_process():
                        launcher_dependency_proofs["before_dispatch"] = _verify_gnu_readlink()
                        try:
                            return q.legacy.core._run_process(
                                plan["argv"], source, environment, attempt / "stdout.txt",
                                attempt / "stderr.txt", GROUP_TIMEOUT_SECONDS, disk_guard=disk,
                                retained_paths=retained_paths, retention_limit=24 * GIB,
                                scratch_paths=scratch_paths, scratch_limit=24 * GIB,
                                working_paths=working_paths, ownership=ownership,
                            )
                        finally:
                            launcher_dependency_proofs["after_dispatch"] = _verify_gnu_readlink()

                    (code, timed_out, elapsed, capacity_loss), popen_evidence = (
                        _run_process_with_fresh_admission(
                            run_one_process, q.legacy.core.subprocess, plan["argv"], source,
                            output,
                            admission["last_observation_monotonic_seconds"],
                        )
                    )
                except _AdmissionWindowExpired as stale:
                    _append_jsonl(admission_ledger, {
                        "event": "expired-before-dispatch", "admission_id": admission_id,
                        "sample_monotonic_seconds": stale.sample_monotonic_seconds,
                        "check_monotonic_seconds": stale.now_monotonic_seconds,
                        "age_seconds": stale.age_seconds, "maximum_age_seconds": MAX_SAMPLE_GAP_SECONDS,
                        "analyzer_dispatched": False, "automatic_retry": False,
                        "publication_eligible": False,
                    })
                    _append_jsonl(report / "progress.jsonl", {
                        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "group": GROUP_ID, "status": "diagnostic-admission-expired-before-dispatch",
                        "admission_id": admission_id, "analyzer_dispatched": False,
                    })
                    continue
                if ownership.get("root_pid") is not None:
                    dispatch_evidence = {
                        "admission_id": admission_id, "diagnostic_admission": admission,
                        "popen": popen_evidence, "process_pid": ownership["root_pid"],
                        "process_created": True,
                    }
                    _append_jsonl(admission_ledger, {
                        "event": "process-created", **dispatch_evidence,
                        "used_for_dispatch": True, "publication_eligible": False,
                    })
                    attempt_record["dispatch_admission"] = dispatch_evidence
                else:
                    _append_jsonl(admission_ledger, {
                        "event": "process-not-created", "admission_id": admission_id,
                        "popen": popen_evidence, "capacity_loss": capacity_loss,
                        "used_for_dispatch": False, "publication_eligible": False,
                    })
                break
            command_elapsed = time.monotonic() - command_started
            _append_host_sample(host, raw_host, assessments, "after-analysis", ownership.get("root_pid"))
            post_runtime = _record_runtime_receipts(source, source_runner, QUALIFIED_PLAN_PATH)
            source_after = _verify_source_inputs(source, plan)
            resource_recheck = _verify_resource_baseline_unchanged(
                resource_paths, baseline_record, disk.delegate)
            parent_inventory_after = _verify_parent_capture_inventory(ROOT)
            verify_plan(plan_path)
            attempt_record.update({
                "exit_code": code, "timed_out": timed_out, "elapsed_seconds": elapsed,
                "command_elapsed_seconds": command_elapsed, "capacity_loss": capacity_loss,
                "process_ownership": ownership, "runtime_manifests_before_dispatch": pre_runtime,
                "runtime_manifests_after_dispatch": post_runtime,
                "source_input_proof_after_dispatch": source_after,
                "launcher_dependency_identity": launcher_dependency_proofs,
                "resource_baseline_after_dispatch": resource_recheck,
                "parent_capture_inventory_after_dispatch": parent_inventory_after,
            })
            if code != 0 or timed_out or capacity_loss is not None:
                raise RuntimeError(f"Joern supplement invocation failed: exit={code}, timed_out={timed_out}, capacity={capacity_loss}")
            if ownership.get("cleanup_status") != "tracked-processes-stopped":
                raise RuntimeError("Joern child cleanup did not prove all tracked process identities stopped")
            reconciliation = _validate_outputs(ROOT, source, plan, _read_json(_repo_file(source, QUALIFIED_PLAN_PATH)))
            attempt_record["reconciliation"] = reconciliation
            if reconciliation["status"] != "matched":
                raise RuntimeError("measured Joern reports differ from frozen outcomes/diagnostics/checkpoints; fail-stop without retry")
            attempt_record.update({
                "status": "completed-candidate-evidence",
                "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source_copies": copied_inputs,
                "host_observations_path": str(raw_host),
                "admission_assessments_path": str(assessments),
                "active_cpu_policy": "record-and-continue",
                "publication_eligible": False, "scored_activation": False,
                "original_a24_settled_qualification_eligible": False,
                "qualification_status": "unqualified; prospective candidate only",
            })
            _write_new(attempt / "terminal.json", attempt_record)
            _append_jsonl(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                                       "group": GROUP_ID,
                                                       "status": "completed-candidate-evidence"})
            terminal = {
                "schema": "v092-timing-swift-supplement-terminal/v1",
                "campaign_id": CAMPAIGN_ID, "status": "unqualified",
                "execution_status": "completed-candidate-evidence",
                "completed_groups": [GROUP_ID], "completed_commands": 1,
                "failed_group": None, "remaining_ready_groups": [],
                "original_parent_terminal_preserved": plan["base_terminal"],
                "new_attempt_terminal": {"path": f"{ATTEMPT_RELATIVE}/terminal.json",
                                         "sha256": sha(attempt / "terminal.json")},
                "qualification_status": "unqualified",
                "full_model_qualification": False, "scored_activation": False,
                "publication_eligible": False,
                "descendant_containment": ownership.get("descendant_containment", "unproven"),
                "original_a24_settled_qualification_eligible": False,
                "automatic_retry": False,
            }
            _write_new(report / "campaign-terminal.json", terminal)
            return {"status": "unqualified", "execution_status": "completed-candidate-evidence",
                    "campaign_id": CAMPAIGN_ID, "completed_commands": 1,
                    "publication_eligible": False}
        except BaseException as exc:
            attempt_record.update({
                "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "process_ownership": ownership, "automatic_retry": False,
                "launcher_dependency_identity": launcher_dependency_proofs,
                "publication_eligible": False, "scored_activation": False,
                "qualification_status": "unqualified; failure retained without retry",
                "original_a24_settled_qualification_eligible": False,
            })
            failure_path = report / "launch-failure-001.json"
            if not failure_path.exists() and not failure_path.is_symlink():
                _write_new(failure_path, attempt_record)
            attempt_terminal = attempt / "terminal.json"
            if attempt.exists() and not attempt_terminal.exists() and not attempt_terminal.is_symlink():
                _write_new(attempt_terminal, attempt_record)
            terminal_path = report / "campaign-terminal.json"
            if not terminal_path.exists() and not terminal_path.is_symlink():
                terminal = {
                    "schema": "v092-timing-swift-supplement-terminal/v1",
                    "campaign_id": CAMPAIGN_ID,
                    "status": "unqualified" if ownership.get("root_pid") else "blocked",
                    "execution_status": "stopped-fail-closed",
                    "failed_group": GROUP_ID, "completed_groups": [],
                    "remaining_ready_groups": [], "failure": attempt_record,
                    "attempt_terminal": ({"path": f"{ATTEMPT_RELATIVE}/terminal.json",
                                          "sha256": sha(attempt_terminal)}
                                         if attempt_terminal.is_file() else None),
                    "automatic_retry": False, "publication_eligible": False,
                    "qualification_status": "unqualified",
                    "descendant_containment": ownership.get("descendant_containment", "unproven"),
                    "original_a24_settled_qualification_eligible": False,
                }
                _write_new(terminal_path, terminal)
            _append_jsonl(report / "progress.jsonl", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                                       "group": GROUP_ID, "status": "failed",
                                                       "error": f"{type(exc).__name__}: {exc}"})
            raise


def _check_capacity(disk, retained: list[Path], working: list[Path], scratch: list[Path], launch: bool) -> None:
    phase = "launch" if launch else "active"
    disk.check(category="retention", paths=retained, capacity_path=ROOT, phase=phase)
    disk.check(category="scratch", paths=scratch, capacity_path=ROOT, phase=phase)
    disk.check(category="working", paths=working, capacity_path=ROOT, phase=phase)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--qualified-plan", default=QUALIFIED_PLAN_PATH)
    prepare_parser.add_argument("--output", default=PLAN_PATH)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--plan", default=PLAN_PATH)
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--plan", default=PLAN_PATH)
    args = parser.parse_args(argv)
    try:
        if args.mode == "prepare":
            result = prepare(args.qualified_plan, args.output)
        elif args.mode == "verify":
            result = verify_plan(args.plan)
        else:
            result = execute(args.plan)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
