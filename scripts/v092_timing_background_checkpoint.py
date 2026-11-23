#!/usr/bin/env python3
"""Seal the final between-command handoff for the v0.9.2 timing campaign.

The checkpoint binds the 29 additional completed commands and the policy
handoff without changing prior evidence. It inventories only the named report
directory and those completed groups' declared source output roots.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


SCHEMA = "v092-timing-background-checkpoint/v1"
AUTH_SCHEMA = "v092-continuation-execution-authorization/v1"
CAMPAIGN_ID = "20261122-01"
NEW_CAMPAIGN_ID = "20261122-02"
PLAN_COMMIT = "ee69bef15a6ffadd4fd60f1467f316208d8a3e44"
RELEASE_COMMIT = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
PENDING_GROUPS = ["overhead-pysa-python", "warm-joern-java", "warm-semgrep-java"]
PENDING_HOST_ONLY = "overhead-pysa-python"
EXPECTED_NEW_COMPLETIONS = 29
EXPECTED_COLD = 21
EXPECTED_OVERHEAD = 8
RESOURCE_CAMPAIGN_IDS = ["20261115-01", "20261121-01", CAMPAIGN_ID]
BACKGROUND_MODE = "background-tolerance/v1"
IDENTITY_FIELDS = [
    "tool", "tool_version", "tool_build_identity", "configuration_hash",
    "fixture_revision", "cold_or_warm", "adapter_version", "schema_version",
]
QUALIFICATION_REPLACEMENTS = {
    "evidence_status": "prospective timing evidence under explicit user background tolerance; original settled qualification not asserted",
    "quiet_window": "fresh complete host sample before each remaining command; exact Contacts, Spotlight and Apple VM paths tolerated; original 300-second settled gate not asserted",
    "quiet_predicate": "original settled qualification false; raw telemetry and user-policy assessments retained separately",
}
SEMANTIC_POLICY = {
    "outcome_only": "quarantine-and-continue",
    "identity_or_membership": "fail-stop",
    "command_timeout_resource_or_provenance": "fail-stop",
    "retry": False,
}
DISPATCH_ADMISSION = {
    "schema": "v092-background-tolerance-admission/v1",
    "scope": "final-three-admissions-only",
    "process_match": "exact-full-comm-path",
    "tolerated_comm_paths": [
        "/System/Library/Frameworks/Contacts.framework/Support/contactsd",
        "/System/Library/PrivateFrameworks/ContactsDonation.framework/Versions/A/Support/contactsdonationagent",
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/corespotlightd",
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/managedcorespotlightd",
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mds",
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mds_stores",
        "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/Metadata.framework/Versions/A/Support/mdworker_shared",
        "/usr/libexec/spotlightknowledged.updater",
        "/System/Library/Frameworks/Virtualization.framework/Versions/A/XPCServices/com.apple.Virtualization.VirtualMachine.xpc/Contents/MacOS/com.apple.Virtualization.VirtualMachine",
    ],
    "aggregate_cpu_idle": "record-only-without-adjustment",
    "required_settled_seconds": 0,
    "non_tolerated_heavy_processes": "wait-before-dispatch",
    "external_cpu_percent_per_logical_cpu": 10,
    "observation_failure": "wait-before-dispatch",
    "sample_interval_seconds": 45,
    "active_invocation_cpu_policy": "record-and-continue",
    "original_settled_qualification_eligible": False,
}
DISPATCH_POLICY_PATH = "reports/timing/v0.9.2/20261122-02/dispatch-admission-policy-01.json"
VM_IDENTITY_PATH = "reports/timing/v0.9.2/20261122-02/vm-identity-01.json"
VM_EXECUTABLE = DISPATCH_ADMISSION["tolerated_comm_paths"][-1]
INVENTORY_PATH = "reports/timing/v0.9.2/20261122-01/evidence-inventory-01.json"
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def sha(path: Path) -> str:
    """Return SHA-256 of a regular, non-symlink file."""
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise RuntimeError(f"evidence path is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module(name: str, path: Path):
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load checkpoint module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _v1():
    return _load_module("_v092_timing_checkpoint_for_background", Path(__file__).with_name("v092_timing_checkpoint.py"))


def _v2():
    return _load_module("_v092_timing_segment_checkpoint_for_background", Path(__file__).with_name("v092_timing_segment_checkpoint.py"))


def _read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{description} must be a JSON object: {path}")
    return value


def _ref(root: Path, path: Path, description: str) -> dict:
    relative, resolved = _v1()._repo_path(root, path, description)
    return {"path": relative, "sha256": sha(resolved)}


def _safe_relative(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise RuntimeError(f"{description} must be a safe repository-relative path")
    relative = PurePosixPath(value)
    if (relative.is_absolute() or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)):
        raise RuntimeError(f"{description} is unsafe")
    return relative


def _within_output(value: str, group: dict, description: str) -> None:
    candidate = _safe_relative(value, description)
    roots = group.get("output_roots")
    if not isinstance(roots, list) or not roots:
        raise RuntimeError(f"{group.get('id')} has no declared output roots")
    for value in roots:
        root = _safe_relative(value, f"{group.get('id')} output root")
        if candidate == root or root in candidate.parents:
            return
    raise RuntimeError(f"{description} is outside declared output roots: {value}")


def _progress(path: Path) -> list[dict]:
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("campaign progress log is malformed") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError("campaign progress rows must be objects")
    return rows


def _validate_partition(parent: dict, rows: list[dict], terminal: dict) -> tuple[list[str], list[str], list[str]]:
    inherited = parent.get("completed_groups")
    quarantined = parent.get("quarantined_groups")
    remaining = parent.get("remaining_ready_groups")
    if (not isinstance(inherited, list) or len(inherited) != 60
            or quarantined != ["joern-rust-kernel"]
            or not isinstance(remaining, list) or len(remaining) != 32
            or remaining[-3:] != PENDING_GROUPS):
        raise RuntimeError("CPv2 does not define the expected 60/1/32 continuation frontier")
    if len(rows) != 2 * EXPECTED_NEW_COMPLETIONS:
        raise RuntimeError("progress must contain exactly 29 started/completed command pairs")
    completed = []
    previous = None
    for index in range(0, len(rows), 2):
        started, finished = rows[index:index + 2]
        group_id = remaining[index // 2]
        if (started.get("group") != group_id or started.get("status") != "started"
                or finished.get("group") != group_id
                or finished.get("status") != "completed-candidate-evidence"):
            raise RuntimeError("progress is not the exact 29-success prefix with no failure or new quarantine")
        start_time = _v1()._parse_utc(started.get("utc"), "progress start timestamp")
        finish_time = _v1()._parse_utc(finished.get("utc"), "progress completion timestamp")
        if finish_time < start_time or (previous is not None and start_time < previous):
            raise RuntimeError("progress timestamps are out of order")
        previous = finish_time
        completed.append(group_id)
    suffix = remaining[EXPECTED_NEW_COMPLETIONS:]
    if (terminal.get("campaign_id") != CAMPAIGN_ID
            or terminal.get("status") != "superseded-between-commands"
            or terminal.get("execution_status") != "handed-off-before-next-command"
            or terminal.get("completed_commands") != EXPECTED_NEW_COMPLETIONS
            or terminal.get("completed_candidate_groups") != completed
            or terminal.get("inherited_candidate_commands") != len(inherited)
            or terminal.get("inherited_candidate_groups") != inherited
            or terminal.get("combined_completed_candidate_commands") != 89
            or terminal.get("inherited_quarantined_groups") != quarantined
            or terminal.get("quarantined_groups") != []
            or terminal.get("combined_quarantined_groups") != quarantined
            or terminal.get("remaining_ready_groups") != suffix
            or terminal.get("paused_before_group") != suffix[0]
            or terminal.get("stopped_group") is not None
            or terminal.get("qualification_status") != "unqualified"
            or terminal.get("publication_eligible") is not False
            or terminal.get("no_active_invocation_at_handoff") is not True
            or terminal.get("external_controller_terminal") is not True
            or terminal.get("controller_exit_signal") != "SIGTERM"):
        raise RuntimeError("campaign terminal does not reconcile to 60 inherited, 29 completed, Rust quarantined, 3 pending")
    return inherited + completed, quarantined, suffix


def _validate_handoff(root: Path, report: Path, start: dict, progress_path: Path,
                      terminal: dict, remaining: list[str]) -> tuple[dict, dict, dict]:
    request_path = report / "dispatch-policy-handoff-request-01.json"
    handoff_path = report / "dispatch-policy-handoff-01.json"
    ownership_path = report / "post-handoff-ownership-01.json"
    request = _read_json(request_path, "dispatch policy handoff request")
    handoff = _read_json(handoff_path, "dispatch policy handoff receipt")
    ownership = _read_json(ownership_path, "post-handoff ownership receipt")
    common = (
        "schema", "requested_utc", "user_request", "supervisor_pid", "supervisor_start_identity",
        "frontier_completed", "next_group", "analyzer_start_absent", "quiet_observation_utc",
        "quiet_elapsed_seconds", "progress_sha256", "publication_eligible",
    )
    if any(request.get(key) != handoff.get(key) for key in common):
        raise RuntimeError("dispatch-policy handoff receipt differs from its request")
    progress_sha = sha(progress_path)
    expected_identity = (start.get("supervisor_pid"), start.get("supervisor_start_identity"))
    if (request.get("schema") != "v092-dispatch-policy-handoff/v1"
            or not isinstance(request.get("user_request"), str) or not request["user_request"].strip()
            or (request.get("supervisor_pid"), request.get("supervisor_start_identity")) != expected_identity
            or request.get("frontier_completed") != EXPECTED_NEW_COMPLETIONS
            or request.get("next_group") != remaining[0]
            or request.get("analyzer_start_absent") is not True
            or request.get("progress_sha256") != progress_sha
            or request.get("publication_eligible") is not False
            or handoff.get("no_active_invocation") is not True
            or handoff.get("supervisor_state") != "Ts"
            or handoff.get("signals_sent") != ["SIGSTOP", "SIGTERM", "SIGCONT"]
            or not str(handoff.get("reason", "")).startswith("User-authorized background-tolerance policy handoff")):
        raise RuntimeError("dispatch-policy handoff identity/frontier is invalid")
    if (terminal.get("handoff_receipt") != handoff_path.name
            or terminal.get("no_active_invocation_at_handoff") is not True):
        raise RuntimeError("campaign terminal does not point to its no-active-invocation handoff")
    if (ownership.get("schema") != "v092-post-handoff-ownership/v1"
            or ownership.get("supervisor_pid") != expected_identity[0]
            or ownership.get("recorded_start_identity") != expected_identity[1]
            or ownership.get("observed_start_identity") is not None
            or ownership.get("recorded_supervisor_gone") is not True
            or ownership.get("controller_exit_code") != 143
            or ownership.get("no_active_invocation_at_handoff") is not True
            or ownership.get("signals_to_analyzers_or_unrelated_workloads") != []
            or ownership.get("campaign_lock_available") is not True):
        raise RuntimeError("post-handoff ownership receipt does not prove the exact supervisor identity is gone")
    return (
        _ref(root, request_path, "handoff request"),
        _ref(root, handoff_path, "handoff receipt"),
        _ref(root, ownership_path, "post-handoff ownership"),
    )


def _validate_start_bindings(root: Path, plan: dict, start: dict) -> None:
    inputs = start.get("execution_inputs")
    if not isinstance(inputs, dict):
        raise RuntimeError("campaign-start execution_inputs must be an object")
    for ref_name in ("source_plan", "runtime_bindings"):
        ref = plan.get(ref_name)
        if (not isinstance(ref, dict) or inputs.get(ref.get("path")) != ref.get("sha256")
                or sha(_v1()._repo_path(root, ref["path"], ref_name)[1]) != ref.get("sha256")):
            raise RuntimeError(f"campaign start does not bind the plan {ref_name}")
    helpers = plan.get("execution_helpers")
    if not isinstance(helpers, dict):
        raise RuntimeError("plan execution helper map is malformed")
    for path, digest in helpers.items():
        if inputs.get(path) != digest:
            raise RuntimeError(f"campaign start does not bind execution helper {path}")
    expected_tools = {
        name: {"path": item.get("path"), "sha256": item.get("sha256")}
        for name, item in plan.get("tools", {}).items()
    }
    observed_tools = {
        item.get("name"): {"path": item.get("path"), "sha256": item.get("sha256")}
        for item in start.get("tools_verified_before_start", []) if isinstance(item, dict)
    }
    if observed_tools != expected_tools:
        raise RuntimeError("campaign-start tool identities differ from plan")
    expected_runtimes = {
        item.get("id"): {key: item.get(key) for key in ("path", "sha256", "uncompressed_sha256")}
        for item in plan.get("runtimes", []) if isinstance(item, dict)
    }
    observed_runtimes = {
        item.get("id"): {key: item.get(key) for key in ("path", "sha256", "uncompressed_sha256")}
        for item in start.get("runtime_manifests_verified_before_start", []) if isinstance(item, dict)
    }
    if observed_runtimes != expected_runtimes:
        raise RuntimeError("campaign-start runtime manifest identities differ from plan")


def _validate_success_common(root: Path, report: Path, work: Path, plan: dict,
                             group: dict, plan_sha: str) -> tuple[dict, dict, dict]:
    old, segment = _v1(), _v2()
    group_id = group["id"]
    attempt = report / "attempts" / group_id / "attempt-01"
    old._reject_symlink_components(root, attempt)
    if not attempt.is_dir():
        raise RuntimeError(f"completed group lacks attempt-01: {group_id}")
    start_path, terminal_path = attempt / "start.json", attempt / "terminal.json"
    start, terminal = _read_json(start_path, f"{group_id} start"), _read_json(terminal_path, f"{group_id} terminal")
    segment._validate_start(start, plan_sha, group, work, report)
    if (terminal.get("group") != group_id or terminal.get("argv") != group.get("argv")
            or terminal.get("status") != "completed-candidate-evidence"
            or terminal.get("attempt") != 1 or terminal.get("automatic_retry") is not False
            or terminal.get("exit_code") != 0 or terminal.get("timed_out") is not False
            or terminal.get("capacity_loss") is not None
            or terminal.get("publication_eligible") is not False):
        raise RuntimeError(f"completed terminal is not one successful, unqualified attempt: {group_id}")
    source = terminal.get("source_verified_after_analysis")
    if (not isinstance(source, dict) or source.get("source_and_fixture_inputs_unchanged") is not True
            or source.get("source_commit") != plan.get("release_commit")
            or source.get("snapshot_git_head") != plan.get("release_commit")):
        raise RuntimeError(f"completed group source/provenance verification differs: {group_id}")
    start_ref = _ref(root, start_path, f"{group_id} attempt start")
    terminal_ref = _ref(root, terminal_path, f"{group_id} attempt terminal")
    return start_ref, terminal_ref, terminal


def _validate_cold(root: Path, report: Path, work: Path, plan: dict,
                   group: dict, plan_sha: str) -> tuple[dict, dict]:
    start_ref, terminal_ref, terminal = _validate_success_common(root, report, work, plan, group, plan_sha)
    checked_terminal, raw_outputs = _v1()._validate_successful_terminal(
        root, report, work, plan, group, plan_sha,
    )
    if checked_terminal != terminal_ref:
        raise RuntimeError(f"cold report validator returned a different terminal: {group['id']}")
    for descriptor in group.get("reports", []):
        _within_output(descriptor.get("source_path"), group, f"{group['id']} source report")
    for raw in raw_outputs:
        _within_output(raw, group, f"{group['id']} raw output")
    return start_ref, terminal_ref


def _frozen_overhead_identity(plan: dict, group: dict, family: str, language: str) -> dict:
    group_id = f"{family}-{language}-kernel"
    frozen = plan.get("frozen_report_bindings", {}).get(group_id)
    if not isinstance(frozen, list) or not frozen:
        raise RuntimeError(f"overhead group lacks frozen {family}/{language} kernel identity")
    identities = [item.get("identity") for item in frozen if isinstance(item, dict)]
    fields = ("tool", "tool_version", "tool_build_identity", "fixture_revision")
    if (not identities or any(not isinstance(identity, dict) for identity in identities)):
        raise RuntimeError("overhead frozen identity entries are malformed")
    identity = {key: identities[0].get(key) for key in fields}
    if (any({key: value.get(key) for key in fields} != identity for value in identities[1:])
            or identity["tool"] != family or identity["fixture_revision"] != plan.get("fixture_revision")):
        raise RuntimeError(f"overhead frozen family identity differs: {family}/{language}")
    if family == "flowdroid":
        base, separator, _d8 = identity["tool_build_identity"].partition("; dexed by ")
        if not separator:
            raise RuntimeError("FlowDroid frozen identity lacks its D8 materialization suffix")
        identity["tool_build_identity"] = base
        identity["identity_scope"] = "A24 analyzer/platform witness; D8 is separately runtime-bound"
    return identity


def _validate_overhead_artifact(root: Path, work: Path, plan: dict, group: dict) -> dict:
    argv = group.get("argv")
    if not isinstance(argv, list):
        raise RuntimeError("overhead command argv is malformed")
    def arg(flag):
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise RuntimeError(f"overhead command has missing or ambiguous {flag}")
        return argv[argv.index(flag) + 1]
    family, language = arg("--tool"), arg("--language")
    if family != group.get("family"):
        raise RuntimeError("overhead tool differs from group family")
    roots = group.get("output_roots")
    if not isinstance(roots, list) or len(roots) != 1:
        raise RuntimeError("overhead group must declare exactly one output root")
    raw_relative = _safe_relative(roots[0], "overhead output root")
    source = work / "sources" / group["id"]
    raw_root = source / Path(*raw_relative.parts)
    old = _v1()
    old._reject_symlink_components(root, raw_root)
    artifact_path = raw_root / "invocation-overhead.json"
    old._reject_symlink_components(root, artifact_path)
    artifact = _read_json(artifact_path, "invocation-overhead artifact")
    artifact_sha = sha(artifact_path)
    if (artifact.get("schema_version") != 1
            or artifact.get("evidence_kind") != "retained-invocation-overhead-estimate"
            or artifact.get("amendment") != "A24"
            or artifact.get("adapter") != family
            or artifact.get("language") != language
            or artifact.get("repeats") != 3):
        raise RuntimeError("overhead artifact schema, amendment, adapter or repeat count differs")
    runs = artifact.get("runs")
    if not isinstance(runs, list) or len(runs) != 3:
        raise RuntimeError("overhead artifact must contain three run records")
    for repeat, run in enumerate(runs, 1):
        wall = run.get("wall_ms") if isinstance(run, dict) else None
        if (not isinstance(run, dict) or run.get("repeat") != repeat
                or type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0):
            raise RuntimeError("overhead run records are malformed")
    fixture_value = artifact.get("fixture_file")
    fixture_relative = _safe_relative(fixture_value, "overhead fixture path")
    fixture_path = raw_root / Path(*fixture_relative.parts)
    old._reject_symlink_components(root, fixture_path)
    fixture_sha = artifact.get("fixture_sha256")
    if not isinstance(fixture_sha, str) or _SHA.fullmatch(fixture_sha) is None or sha(fixture_path) != fixture_sha:
        raise RuntimeError("overhead fixture artifact is missing or its hash differs")
    identity = _frozen_overhead_identity(plan, group, family, language)
    if (artifact.get("tool_version") != identity["tool_version"]
            or artifact.get("tool_build_identity") != identity["tool_build_identity"]):
        raise RuntimeError("overhead artifact tool identity differs from frozen family identity")
    env_path = raw_root / "run-environment.json"
    old._reject_symlink_components(root, env_path)
    env = _read_json(env_path, "overhead run-environment witness")
    if (env.get("schema_version") != 1 or env.get("evidence_kind") != "retained-run-environment"
            or env.get("tool") != family or env.get("witnessed_tool_version") != artifact.get("tool_version")
            or env.get("witnessed_tool_build_identity") != artifact.get("tool_build_identity")):
        raise RuntimeError("overhead environment witness does not match its artifact identity")
    expected = {
        "kind": "overhead", "status": "candidate", "artifact": str(artifact_path),
        "sha256": artifact_sha, "repeats": 3, "fixture_file": str(fixture_path),
        "fixture_sha256": fixture_sha, "fixture_revision": plan["fixture_revision"],
        "frozen_family_identity": identity, "environment_identity_verified": True,
        "publication_eligible": False,
    }
    return expected


def _validate_overhead(root: Path, report: Path, work: Path, plan: dict,
                       group: dict, plan_sha: str) -> tuple[dict, dict]:
    start_ref, terminal_ref, terminal = _validate_success_common(root, report, work, plan, group, plan_sha)
    expected = _validate_overhead_artifact(root, work, plan, group)
    if terminal.get("reconciliation") != expected:
        raise RuntimeError(f"overhead terminal reconciliation differs from preserved artifact: {group['id']}")
    return start_ref, terminal_ref


def _validate_pending(root: Path, report: Path, work: Path, plan: dict,
                      pending: list[str], completed: list[str]) -> None:
    old = _v1()
    attempts_root = report / "attempts"
    # The Pysa gate has quiet-only telemetry. Its attempt directory must contain
    # exactly that receipt and no analyzer start, terminal, stdout or stderr.
    for group_id in pending:
        group_root = attempts_root / group_id
        old._reject_symlink_components(root, group_root)
        if group_id == PENDING_HOST_ONLY:
            attempt = group_root / "attempt-01"
            old._reject_symlink_components(root, attempt)
            if not attempt.is_dir() or {item.name for item in attempt.iterdir()} != {"host.jsonl"}:
                raise RuntimeError("Pysa pending attempt must retain only its quiet-host receipt")
            host_path = attempt / "host.jsonl"
            if not stat.S_ISREG(host_path.lstat().st_mode):
                raise RuntimeError("Pysa quiet-host receipt is not a regular file")
            try:
                rows = [json.loads(line) for line in host_path.read_text().splitlines() if line]
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Pysa quiet-host receipt is malformed") from exc
            if (not rows or any(not isinstance(row, dict) or row.get("phase") != "settle-before-group"
                                or row.get("status") not in {"ok", "failed"} for row in rows)):
                raise RuntimeError("Pysa pending host telemetry contains a non-admission observation")
        elif group_root.exists():
            raise RuntimeError(f"warm pending group unexpectedly has attempt evidence: {group_id}")
        group = next(item for item in plan["groups"] if item["id"] == group_id)
        for output_root in group.get("output_roots", []):
            output = work / "sources" / group_id / Path(*_safe_relative(output_root, "pending output root").parts)
            old._reject_symlink_components(root, output)
            if output.exists():
                if not output.is_dir() or any(output.iterdir()):
                    raise RuntimeError(f"pending group has analyzer output: {group_id}/{output_root}")
    actual_dirs = {item.name for item in attempts_root.iterdir() if item.is_dir()}
    if actual_dirs != set(completed) | {PENDING_HOST_ONLY}:
        raise RuntimeError("campaign attempt directory set includes an unplanned or pending command")


def _inventory(root: Path, report: Path, work: Path, groups: list[dict], inventory_path: Path) -> list[dict]:
    old = _v1()
    inventory = _read_json(inventory_path, "campaign evidence inventory")
    if inventory.get("schema") != "v092-timing-evidence-inventory/v1":
        raise RuntimeError("campaign evidence inventory schema differs")
    if inventory.get("campaign_id") != CAMPAIGN_ID or inventory.get("report_root") != report.relative_to(root).as_posix():
        raise RuntimeError("campaign evidence inventory identity differs")
    if (inventory.get("source_output_groups") != [group["id"] for group in groups]
            or inventory.get("publication_eligible") is not False):
        raise RuntimeError("campaign evidence inventory scope or qualification differs")
    expected_files = inventory.get("files")
    if not isinstance(expected_files, list):
        raise RuntimeError("campaign evidence inventory file list is malformed")
    seen = old._inventory_report(root, report)
    inventory_relative = inventory_path.relative_to(root).as_posix()
    if inventory_relative not in seen:
        raise RuntimeError("campaign evidence inventory is missing from its report root")
    del seen[inventory_relative]
    for group in groups:
        for output_root in group.get("output_roots", []):
            output = work / "sources" / group["id"] / Path(*_safe_relative(output_root, "output root").parts)
            old._inventory_tree(root, output, seen)
    actual = [seen[path] for path in sorted(seen)]
    if (actual != expected_files or inventory.get("file_count") != len(actual)
            or inventory.get("total_bytes") != sum(item["size_bytes"] for item in actual)):
        raise RuntimeError("campaign evidence inventory differs from preserved receipts and source outputs")
    old._inventory_file(root, inventory_path, seen)
    return [seen[path] for path in sorted(seen)]


def create_checkpoint(root: Path, parent_segment_plan_path: Path) -> dict:
    """Validate the handoff and build a checkpoint for the final three commands."""
    root = Path(root).resolve()
    old, segment = _v1(), _v2()
    _relative, plan_path = old._repo_path(root, parent_segment_plan_path, "parent campaign plan")
    plan = _read_json(plan_path, "parent campaign plan")
    if plan.get("campaign_id") != CAMPAIGN_ID:
        raise RuntimeError("parent plan is not campaign 20261122-01")
    plan_sha = sha(plan_path)
    report = root / "reports" / "timing" / "v0.9.2" / CAMPAIGN_ID
    work = root / "execution-state" / f"timing-v092-{CAMPAIGN_ID}"
    start_path, progress_path = report / "campaign-start.json", report / "progress.jsonl"
    terminal_path, inventory_path = report / "campaign-terminal.json", root / INVENTORY_PATH
    start = _read_json(start_path, "campaign start")
    if (start.get("plan_sha256") != plan_sha or start.get("plan_commit") != PLAN_COMMIT
            or start.get("source_commit") != RELEASE_COMMIT
            or start.get("campaign_id") != CAMPAIGN_ID
            or start.get("continuation_checkpoint") != plan.get("continuation")):
        raise RuntimeError("campaign-start identity differs from committed plan/ancestor")
    old._verify_parent_plan_commit(root, plan_path, plan, start)
    parent_ref = plan.get("continuation")
    parent = segment.verify_checkpoint(root, parent_ref, plan=plan)
    if (parent.get("parent_campaign_id") != "20261121-01"
            or parent.get("resource_campaign_ids") != RESOURCE_CAMPAIGN_IDS[:2]
            or start.get("inherited_candidate_groups") != parent.get("completed_groups")
            or start.get("inherited_quarantined_groups") != parent.get("quarantined_groups")):
        raise RuntimeError("campaign start does not inherit the verified CPv2 partition")
    _validate_start_bindings(root, plan, start)
    groups, ready, _blocked = old._plan_groups(plan)
    ready_ids = [group["id"] for group in ready]
    if (len(groups) != 95 or len(ready_ids) != 93
            or start.get("ready_commands") != len(parent["remaining_ready_groups"])
            or start.get("planned_ready_commands") != 93
            or start.get("planned_cold_groups") != 84
            or start.get("ready_cold_groups") != 82
            or start.get("blocked_cold_groups") != 2
            or start.get("max_campaign_wall_seconds") != plan.get("max_campaign_wall_seconds")):
        raise RuntimeError("campaign start does not retain the full frozen 95-group plan")
    progress_rows = _progress(progress_path)
    campaign_terminal = _read_json(terminal_path, "campaign terminal")
    completed_groups, quarantined, remaining = _validate_partition(parent, progress_rows, campaign_terminal)
    current_groups = completed_groups[len(parent["completed_groups"]):]
    if (current_groups != parent["remaining_ready_groups"][:EXPECTED_NEW_COMPLETIONS]
            or remaining != PENDING_GROUPS):
        raise RuntimeError("current dispatch prefix differs from the sealed CPv2 frontier")
    current_group_records = [next(group for group in groups if group["id"] == group_id)
                             for group_id in current_groups]
    if (sum(group.get("kind") == "cold" for group in current_group_records) != EXPECTED_COLD
            or sum(group.get("kind") == "overhead" for group in current_group_records) != EXPECTED_OVERHEAD
            or any(group.get("kind") == "warm" for group in current_group_records)):
        raise RuntimeError("current successful prefix is not 21 cold plus 8 overhead commands")
    if (campaign_terminal.get("plan_sha256") != plan_sha
            or campaign_terminal.get("plan_commit") != PLAN_COMMIT):
        raise RuntimeError("campaign terminal plan identity differs from start")
    handoff_refs = _validate_handoff(root, report, start, progress_path, campaign_terminal, remaining)
    attempt_groups = {path.name for path in (report / "attempts").iterdir() if path.is_dir()}
    if attempt_groups != set(current_groups) | {PENDING_HOST_ONLY}:
        raise RuntimeError("campaign attempt directories differ from the 29 completed plus quiet-only Pysa group")
    _validate_pending(root, report, work, plan, remaining, current_groups)

    plan_by_id = {group["id"]: group for group in groups}
    starts, terminals = [], []
    for group_id in current_groups:
        group = plan_by_id[group_id]
        if group.get("kind") == "cold":
            start_ref, terminal_ref = _validate_cold(root, report, work, plan, group, plan_sha)
        elif group.get("kind") == "overhead":
            start_ref, terminal_ref = _validate_overhead(root, report, work, plan, group, plan_sha)
        else:
            raise RuntimeError(f"unsupported completed command kind: {group_id}")
        starts.append(start_ref)
        terminals.append(terminal_ref)
    evidence_files = _inventory(root, report, work, current_group_records, inventory_path)
    parent_plan_ref = _ref(root, plan_path, "parent campaign plan")
    report_relative, work_relative = report.relative_to(root).as_posix(), work.relative_to(root).as_posix()
    return {
        "schema": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "parent_campaign_id": CAMPAIGN_ID,
        "resource_campaign_ids": RESOURCE_CAMPAIGN_IDS,
        "parent_checkpoint": parent_ref,
        "parent_input_references": segment.input_references(parent),
        "parent_plan": parent_plan_ref,
        "campaign_start": _ref(root, start_path, "campaign start"),
        "progress": _ref(root, progress_path, "campaign progress"),
        "campaign_terminal": _ref(root, terminal_path, "campaign terminal"),
        "handoff_request": handoff_refs[0],
        "handoff_receipt": handoff_refs[1],
        "post_handoff_ownership": handoff_refs[2],
        "evidence_inventory": _ref(root, inventory_path, "campaign evidence inventory"),
        "completed_groups": completed_groups,
        "new_completed_groups": current_groups,
        "quarantined_groups": quarantined,
        "new_quarantined_groups": [],
        "remaining_ready_groups": remaining,
        "parent_report_root": report_relative,
        "parent_work_root": work_relative,
        "parent_sources_root": f"{work_relative}/sources",
        "parent_scratch_roots": start.get("scratch_roots", []),
        "parent_source_roots": [f"{work_relative}/sources/{group_id}" for group_id in current_groups],
        "resource_campaign_report_roots": [f"reports/timing/v0.9.2/{campaign_id}" for campaign_id in RESOURCE_CAMPAIGN_IDS],
        "attempt_starts": starts,
        "completed_terminals": terminals,
        "evidence_files": evidence_files,
        "publication_eligible": False,
    }


def _validate_authorization(root: Path, plan: dict) -> None:
    reference = plan.get("execution_authorization")
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise RuntimeError("new plan must bind one execution authorization receipt")
    raw, relative = _v1()._read_bytes(root, reference, "execution authorization")
    auth = _read_json(root / relative, "execution authorization")
    authorized, status = auth.get("authorized"), auth.get("status")
    if (auth.get("schema") != AUTH_SCHEMA or auth.get("campaign_id") != plan.get("campaign_id")
            or not isinstance(authorized, bool)
            or (authorized is False and status != "pending")
            or (authorized is True and status != "authorized")):
        raise RuntimeError("new execution authorization receipt is malformed or inconsistent")


def _validate_background_binding(root: Path, plan: dict) -> None:
    if plan.get("dispatch_admission") != DISPATCH_ADMISSION:
        raise RuntimeError("new plan dispatch_admission differs from the exact user-policy object")
    policy_path = root / DISPATCH_POLICY_PATH
    vm_path = root / VM_IDENTITY_PATH
    policy = _read_json(policy_path, "background admission policy")
    vm = _read_json(vm_path, "VM identity receipt")
    if policy != DISPATCH_ADMISSION or vm.get("schema") != "v092-tolerated-vm-identity/v1":
        raise RuntimeError("background policy or VM identity receipt schema differs")
    signature = vm.get("signature_description")
    if (vm.get("executable_path") != VM_EXECUTABLE
            or vm.get("signature_verification_exit_code") != 0
            or not isinstance(signature, str)
            or "Identifier=com.apple.Virtualization.VirtualMachine" not in signature
            or "Authority=Apple Root CA" not in signature):
        raise RuntimeError("VM identity receipt does not verify the exact tolerated Apple executable")
    runtime_ref = plan.get("runtime_bindings")
    if not isinstance(runtime_ref, dict) or set(runtime_ref) != {"path", "sha256"}:
        raise RuntimeError("new runtime-bindings reference is malformed")
    raw, relative = _v1()._read_bytes(root, runtime_ref, "new runtime bindings")
    bindings = _read_json(root / relative, "new runtime bindings")
    if (plan.get("source_plan", {}).get("bindings_sha256") != runtime_ref.get("sha256")
            or bindings.get("campaign_id") != plan.get("campaign_id")
            or bindings.get("dispatch_admission") != DISPATCH_ADMISSION):
        raise RuntimeError("new runtime bindings do not carry the plan admission contract")
    source_ref = plan.get("source_plan", {})
    bound_source = bindings.get("source_plan")
    if (not isinstance(bound_source, dict)
            or {key: bound_source.get(key) for key in ("path", "sha256")}
            != {key: source_ref.get(key) for key in ("path", "sha256")}):
        raise RuntimeError("new runtime bindings changed the source-plan identity")
    for key in ("tools", "runtimes", "source_projection", "path_rebindings", "group_order",
                "max_campaign_wall_seconds", "semantic_mismatch_policy", "continuation_mode",
                "continuation", "execution_authorization"):
        if key in plan and bindings.get(key) != plan.get(key):
            raise RuntimeError(f"new runtime bindings differ from plan field {key}")
    source_ref = plan.get("source_plan", {})
    bound_source = bindings.get("source_plan")
    if (not isinstance(bound_source, dict)
            or {key: bound_source.get(key) for key in ("path", "sha256")}
            != {key: source_ref.get(key) for key in ("path", "sha256")}):
        raise RuntimeError("new runtime bindings changed the source-plan identity")
    for key in ("tools", "runtimes", "source_projection", "path_rebindings", "group_order",
                "max_campaign_wall_seconds", "semantic_mismatch_policy", "continuation_mode",
                "continuation", "execution_authorization"):
        if key in plan and bindings.get(key) != plan.get(key):
            raise RuntimeError(f"new runtime bindings differ from plan field {key}")
    receipts = bindings.get("preparation_receipts")
    if not isinstance(receipts, list):
        raise RuntimeError("new runtime bindings omit preparation receipts")
    ref_map = {item.get("path"): item.get("sha256") for item in receipts if isinstance(item, dict)}
    for path in (DISPATCH_POLICY_PATH, VM_IDENTITY_PATH):
        if ref_map.get(path) != sha(root / path):
            raise RuntimeError(f"new runtime bindings do not pin {path}")


def _compare_new_plan(root: Path, parent_plan: dict, plan: dict,
                      reference: dict, checkpoint: dict) -> None:
    if (plan.get("campaign_id") != NEW_CAMPAIGN_ID
            or plan.get("continuation") != reference
            or plan.get("continuation_mode") != BACKGROUND_MODE
            or plan.get("semantic_mismatch_policy") != SEMANTIC_POLICY):
        raise RuntimeError("new plan continuation mode, reference, or semantic policy differs")
    _validate_authorization(root, plan)
    _validate_background_binding(root, plan)
    left, right = json.loads(json.dumps(parent_plan)), json.loads(json.dumps(plan))
    for key in ("campaign_id", "created_utc", "launch_after_utc", "preregistration",
                "runtime_bindings", "continuation", "continuation_mode", "dispatch_admission",
                "execution_authorization"):
        left.pop(key, None)
        right.pop(key, None)
    for key, expected in QUALIFICATION_REPLACEMENTS.items():
        if right.get("qualification", {}).get(key) != expected:
            raise RuntimeError(f"new plan qualification field differs: {key}")
        left.get("qualification", {}).pop(key, None)
        right.get("qualification", {}).pop(key, None)
    left_source, right_source = left.get("source_plan"), right.get("source_plan")
    if not isinstance(left_source, dict) or not isinstance(right_source, dict):
        raise RuntimeError("source plan binding is malformed")
    left_source.pop("bindings_sha256", None)
    right_source.pop("bindings_sha256", None)
    left_resources, right_resources = left.get("resources"), right.get("resources")
    if not isinstance(left_resources, dict) or not isinstance(right_resources, dict):
        raise RuntimeError("resource declarations are malformed")
    left_resources.pop("total_execution_budget_seconds", None)
    right_resources.pop("total_execution_budget_seconds", None)
    left_helpers, right_helpers = left.get("execution_helpers"), right.get("execution_helpers")
    if not isinstance(left_helpers, dict) or not isinstance(right_helpers, dict):
        raise RuntimeError("execution helper map is malformed")
    qualified = "scripts/v092_timing_qualified_campaign.py"
    background = "scripts/v092_timing_background_checkpoint.py"
    for mapping in (left_helpers, right_helpers):
        mapping.pop(qualified, None)
        mapping.pop(background, None)
    if left != right:
        raise RuntimeError("new plan changes frozen groups, commands, runtimes, source or qualification fields")
    old_helpers, new_helpers = parent_plan["execution_helpers"], plan["execution_helpers"]
    if set(new_helpers) != set(old_helpers) | {background}:
        raise RuntimeError("new plan must add only the background checkpoint helper")
    for name, digest in old_helpers.items():
        if name != qualified and new_helpers.get(name) != digest:
            raise RuntimeError(f"new plan changed an existing helper pin: {name}")
    if (not isinstance(new_helpers.get(qualified), str) or _SHA.fullmatch(new_helpers[qualified]) is None
            or new_helpers.get(background) != sha(Path(__file__))):
        raise RuntimeError("new qualified or background checkpoint helper hash is invalid")
    deadlines = {group["id"]: group["deadline_seconds"] for group in plan.get("groups", [])}
    expected_budget = sum(deadlines[group_id] for group_id in checkpoint["remaining_ready_groups"])
    if plan.get("resources", {}).get("total_execution_budget_seconds") != expected_budget:
        raise RuntimeError("new execution budget must equal only the final three command deadlines")


def verify_checkpoint(root: Path, reference: dict, plan: dict | None = None) -> dict:
    """Revalidate the handoff seal and optionally the next-plan delta."""
    root = Path(root).resolve()
    raw, relative = _v1()._read_bytes(root, reference, "background checkpoint")
    checkpoint = _read_json(root / relative, "background checkpoint")
    if checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported background checkpoint schema")
    expected = create_checkpoint(root, checkpoint.get("parent_plan", {}).get("path", ""))
    actual_copy, expected_copy = dict(checkpoint), dict(expected)
    actual_copy.pop("created_utc", None)
    expected_copy.pop("created_utc", None)
    if actual_copy != expected_copy:
        raise RuntimeError("background checkpoint no longer matches preserved evidence")
    if reference != {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}:
        raise RuntimeError("background checkpoint reference is not canonical")
    if plan is not None:
        parent_plan_path = _v1()._repo_path(root, checkpoint["parent_plan"]["path"], "parent campaign plan")[1]
        parent_plan = _read_json(parent_plan_path, "parent campaign plan")
        _compare_new_plan(root, parent_plan, plan, reference, checkpoint)
    return checkpoint


def input_references(checkpoint: dict) -> list[dict]:
    """Return transitive CPv1/CPv2 and handoff evidence refs, excluding raw inventory entries."""
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported background checkpoint object")
    refs = list(checkpoint.get("parent_input_references", []))
    refs.append(checkpoint.get("parent_checkpoint"))
    refs.extend(checkpoint.get(key) for key in (
        "parent_plan", "campaign_start", "progress", "campaign_terminal", "handoff_request",
        "handoff_receipt", "post_handoff_ownership", "evidence_inventory",
    ))
    refs.extend(checkpoint.get("attempt_starts", []))
    refs.extend(checkpoint.get("completed_terminals", []))
    result, seen = [], {}
    for item in refs:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise RuntimeError("background checkpoint input reference is malformed")
        path = _safe_relative(item.get("path"), "checkpoint input path").as_posix()
        digest = item.get("sha256")
        if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
            raise RuntimeError("background checkpoint input SHA-256 is malformed")
        if path in seen:
            if seen[path] != digest:
                raise RuntimeError(f"conflicting background checkpoint input digest: {path}")
            continue
        seen[path] = digest
        result.append({"path": path, "sha256": digest})
    return result
