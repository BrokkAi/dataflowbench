#!/usr/bin/env python3
"""Bind a stopped v0.9.2 timing segment with one semantic quarantine.

This module inventories only the named campaign report directory and the
output roots for the six commands already attempted by that segment. It never
dispatches tools or treats the quarantined Rust result as qualified evidence.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys


SCHEMA = "v092-timing-segment-checkpoint/v1"
AUTH_SCHEMA = "v092-continuation-execution-authorization/v1"
CAMPAIGN_ID = "20261121-01"
PARENT_CAMPAIGN_ID = "20261115-01"
PLAN_COMMIT = "5d03a54ba6dda101d3a9b2240f688c02432c201e"
RUST_GROUP = "joern-rust-kernel"
FIRST_SIX = [
    "joern-php-kernel", "joern-python-kernel", "joern-python-modeling",
    "joern-python-native", "joern-ruby-kernel", RUST_GROUP,
]
IDENTITY_FIELDS = [
    "tool", "tool_version", "tool_build_identity", "configuration_hash",
    "fixture_revision", "cold_or_warm", "adapter_version", "schema_version",
]
POLICY = {
    "outcome_only": "quarantine-and-continue",
    "identity_or_membership": "fail-stop",
    "command_timeout_resource_or_provenance": "fail-stop",
    "retry": False,
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def sha(path: Path) -> str:
    """Return SHA-256 for a regular, non-symlink file."""
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise RuntimeError(f"evidence path is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _old_module():
    path = Path(__file__).with_name("v092_timing_checkpoint.py")
    name = "_v092_timing_checkpoint_for_segment"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load the immutable v0.9.2 parent checkpoint helper")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def _ref(root: Path, path: Path, description: str) -> dict:
    old = _old_module()
    relative, resolved = old._repo_path(root, path, description)
    return {"path": relative, "sha256": sha(resolved)}


def _json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{description} must be a JSON object: {path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _safe_relative(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise RuntimeError(f"{description} must be a repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"{description} is unsafe")
    return path


def _within_output(path: str, group: dict, description: str) -> None:
    candidate = _safe_relative(path, description)
    roots = group.get("output_roots")
    if not isinstance(roots, list) or not roots:
        raise RuntimeError(f"{group.get('id')} has no declared output roots")
    valid = False
    for value in roots:
        root = _safe_relative(value, f"{group.get('id')} output root")
        if candidate == root or root in candidate.parents:
            valid = True
            break
    if not valid:
        raise RuntimeError(f"{description} is outside declared output roots: {path}")


def _attempt_paths(root: Path, report: Path, group_id: str) -> tuple[Path, Path, Path]:
    old = _old_module()
    attempt = report / "attempts" / group_id / "attempt-01"
    old._reject_symlink_components(root, attempt)
    if not attempt.is_dir():
        raise RuntimeError(f"attempt-01 is missing for {group_id}")
    start_path, terminal_path = attempt / "start.json", attempt / "terminal.json"
    if not start_path.is_file() or not terminal_path.is_file():
        raise RuntimeError(f"start or terminal receipt is missing for {group_id}")
    return attempt, start_path, terminal_path


def _expected_child_environment(work: Path, report: Path, group: dict) -> dict:
    source = work / "sources" / group["id"]
    attempt = report / "attempts" / group["id"] / "attempt-01"
    cache = source / "cache"
    replacements = {
        "@EXECUTION_ROOT@": str(source), "@ATTEMPT_ROOT@": str(attempt),
        "@CACHE_ROOT@": str(cache),
    }
    expected = {}
    for key, value in group.get("environment", {}).items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise RuntimeError(f"{group['id']} plan environment is malformed")
        for marker, replacement in replacements.items():
            value = value.replace(marker, replacement)
        if any(marker in value for marker in replacements):
            raise RuntimeError(f"{group['id']} plan environment has unresolved path markers")
        expected[key] = value
    expected["HOME"] = str(source / "home")
    expected["TMPDIR"] = str(source / "tmp")
    expected["DFB_CACHE_ROOT"] = str(cache)
    expected["BIFROST_CACHE_ROOT"] = str(cache)
    if group.get("tool") == "pysa":
        identity = hashlib.sha256(str(source.resolve()).encode()).hexdigest()[:20]
        expected["TMPDIR"] = f"/private/tmp/dfb-v092-pysa-{identity}"
    return expected


def _validate_start(start: dict, plan_sha: str, group: dict,
                    work: Path, report: Path) -> None:
    if (start.get("plan_sha256") != plan_sha or start.get("argv") != group.get("argv")
            or start.get("environment") != _expected_child_environment(work, report, group)
            or start.get("deadline_seconds") != group.get("deadline_seconds")
            or start.get("quiet_policy") != {
                "required_seconds": 300, "minimum_idle_percent": 90,
                "maximum_sample_gap_seconds": 60,
            }):
        raise RuntimeError(f"attempt start differs from frozen command contract: {group['id']}")


def _validate_success(root: Path, report: Path, work: Path, plan: dict,
                      group: dict, plan_sha: str) -> tuple[dict, dict]:
    old = _old_module()
    terminal_ref, raw_refs = old._validate_successful_terminal(
        root, report, work, plan, group, plan_sha,
    )
    attempt, start_path, terminal_path = _attempt_paths(root, report, group["id"])
    start = _json(start_path, f"{group['id']} attempt start")
    terminal = _json(terminal_path, f"{group['id']} attempt terminal")
    _validate_start(start, plan_sha, group, work, report)
    if terminal.get("argv") != group.get("argv"):
        raise RuntimeError(f"completed terminal command differs from the frozen plan: {group['id']}")
    for descriptor in group["reports"]:
        _within_output(descriptor.get("source_path"), group, f"{group['id']} source report")
    for raw in raw_refs:
        _within_output(raw, group, f"{group['id']} raw output")
    return _ref(root, start_path, f"{group['id']} attempt start"), terminal_ref


def _validate_rust_outcome_only(root: Path, report: Path, work: Path,
                                plan: dict, group: dict, plan_sha: str) -> tuple[dict, dict]:
    old = _old_module()
    attempt, start_path, terminal_path = _attempt_paths(root, report, RUST_GROUP)
    start = _json(start_path, "Rust attempt start")
    terminal = _json(terminal_path, "Rust attempt terminal")
    _validate_start(start, plan_sha, group, work, report)
    _validate_rust_terminal_core(terminal)
    if terminal.get("argv") != group.get("argv"):
        raise RuntimeError("Rust terminal command differs from the frozen plan")
    source_check = terminal.get("source_verified_after_analysis")
    if not _source_provenance_matches(source_check, plan.get("release_commit")):
        raise RuntimeError("Rust attempt source/provenance verification failed")

    descriptors = group.get("reports")
    frozen = plan.get("frozen_report_bindings", {}).get(RUST_GROUP)
    comparison = terminal.get("frozen_report_comparison")
    reconciliation = terminal.get("reconciliation")
    if (not isinstance(descriptors, list) or len(descriptors) != 1
            or not isinstance(frozen, list) or len(frozen) != 1
            or not isinstance(comparison, dict) or comparison.get("group") != RUST_GROUP
            or comparison.get("status") != "mismatch"
            or not isinstance(reconciliation, dict)
            or reconciliation.get("publication_eligible") is not False):
        raise RuntimeError("Rust frozen comparison or reconciliation is malformed")
    descriptor, frozen_report = descriptors[0], frozen[0]
    source_relative = _safe_relative(descriptor.get("source_path"), "Rust source report")
    _within_output(source_relative.as_posix(), group, "Rust source report")
    source_file = work / "sources" / RUST_GROUP / Path(*source_relative.parts)
    old._reject_symlink_components(root, source_file)
    measured_sha = sha(source_file)
    report_value = _json(source_file, "Rust measured report")
    identity = frozen_report.get("identity")
    if not _matches_frozen_identity(report_value, identity):
        raise RuntimeError("Rust mismatch includes frozen report identity or provenance drift")
    comparisons = comparison.get("reports")
    if not isinstance(comparisons, list) or len(comparisons) != 1:
        raise RuntimeError("Rust comparison does not contain exactly one report")
    observed = comparisons[0]
    if (observed.get("contract_path") != descriptor.get("path")
            or observed.get("frozen_sha256") != frozen_report.get("sha256")
            or observed.get("measured_sha256") != measured_sha
            or observed.get("case_outcomes_compared") != len(descriptor.get("case_ids", []))
            or observed.get("identity_fields_compared") != IDENTITY_FIELDS):
        raise RuntimeError("Rust comparison does not prove exact matched identity")
    mismatches = observed.get("mismatches")
    case_ids = descriptor.get("case_ids")
    if not _outcome_only_mismatches(mismatches, case_ids):
        raise RuntimeError("Rust comparison has identity, membership, or non-outcome mismatches")
    reconciled = reconciliation.get("reports")
    if not isinstance(reconciled, list) or len(reconciled) != 1:
        raise RuntimeError("Rust reconciliation is malformed")
    rec = reconciled[0]
    reconciled_path = rec.get("path")
    if (rec.get("sha256") != measured_sha or rec.get("case_count") != len(case_ids)
            or rec.get("timing_sidecars") != len(case_ids)
            or rec.get("configuration_hash") != identity.get("configuration_hash")
            or not isinstance(reconciled_path, str)
            or Path(reconciled_path).resolve() != source_file.resolve()):
        raise RuntimeError("Rust preserved report bytes do not match reconciliation")
    raw_refs = []
    results = report_value.get("results")
    if not isinstance(results, list) or len(results) != len(case_ids):
        raise RuntimeError("Rust measured report membership differs from frozen cases")
    for result in results:
        if not isinstance(result, dict):
            raise RuntimeError("Rust measured result is malformed")
        raw = result.get("raw_output")
        if raw is not None:
            _within_output(raw, group, "Rust raw output")
            raw_path = work / "sources" / RUST_GROUP / Path(*_safe_relative(raw, "Rust raw output").parts)
            old._reject_symlink_components(root, raw_path)
            if not raw_path.is_file():
                raise RuntimeError(f"Rust referenced raw output is missing: {raw}")
            raw_refs.append(raw)
    # Ensure all declared output roots were real evidence rather than empty placeholders.
    for output in group.get("output_roots", []):
        path = work / "sources" / RUST_GROUP / Path(*_safe_relative(output, "Rust output root").parts)
        if not path.exists():
            raise RuntimeError(f"Rust declared output root is missing: {output}")
    return _ref(root, start_path, "Rust attempt start"), _ref(root, terminal_path, "Rust attempt terminal")


def _source_provenance_matches(source_check: object, release_commit: object) -> bool:
    return (isinstance(source_check, dict) and isinstance(release_commit, str)
            and source_check.get("source_and_fixture_inputs_unchanged") is True
            and source_check.get("source_commit") == release_commit
            and source_check.get("snapshot_git_head") == release_commit)


def _matches_frozen_identity(report: object, identity: object) -> bool:
    return (isinstance(report, dict) and isinstance(identity, dict)
            and all(report.get(key) == identity.get(key) for key in IDENTITY_FIELDS))


def _validate_rust_terminal_core(terminal: dict) -> None:
    if (terminal.get("group") != RUST_GROUP or terminal.get("status") != "failed"
            or terminal.get("attempt") != 1 or terminal.get("automatic_retry") is not False
            or terminal.get("exit_code") != 0 or terminal.get("timed_out") is not False
            or terminal.get("capacity_loss") is not None
            or terminal.get("publication_eligible") is not False
            or terminal.get("not_dispatched") is not False
            or not str(terminal.get("error", "")).startswith("FrozenComparisonError:")):
        raise RuntimeError("Rust attempt failed for a reason other than a non-retried comparison mismatch")


def _outcome_only_mismatches(mismatches: object, case_ids: object) -> bool:
    return (isinstance(case_ids, list) and isinstance(mismatches, list)
            and len(mismatches) == len(case_ids)
            and all(isinstance(item, dict) for item in mismatches)
            and {item.get("case_id") for item in mismatches} == set(case_ids)
            and all(item.get("field") == "outcome" and item.get("classification") == "mismatch"
                    for item in mismatches))


def _read_progress(path: Path) -> list[dict]:
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("segment progress log is malformed") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError("segment progress rows must be objects")
    return rows


def _validate_partition(parent: dict, progress: list[dict], terminal: dict) -> tuple[list[str], list[str], list[str]]:
    inherited = parent.get("completed_groups")
    old_remaining = parent.get("remaining_ready_groups")
    if (not isinstance(inherited, list) or len(inherited) != 55
            or not isinstance(old_remaining, list) or len(old_remaining) != 38
            or old_remaining[:6] != FIRST_SIX):
        raise RuntimeError("original checkpoint does not define the expected 55/38 frontier")
    expected_progress = [item for group in FIRST_SIX for item in (
        {"group": group, "status": "started"},
        {"group": group, "status": "failed" if group == RUST_GROUP else "completed-candidate-evidence"},
    )]
    if len(progress) != len(expected_progress):
        raise RuntimeError("segment progress must contain exactly six alternating attempts")
    for actual, expected in zip(progress, expected_progress):
        if any(actual.get(key) != value for key, value in expected.items()):
            raise RuntimeError("segment progress is not the exact six-command prefix")
    old = _old_module()
    previous = None
    for row in progress:
        stamp = old._parse_utc(row.get("utc"), "segment progress utc")
        if previous is not None and stamp < previous:
            raise RuntimeError("segment progress timestamps are not monotonic")
        previous = stamp
    completed = FIRST_SIX[:5]
    remaining = old_remaining[6:]
    if (terminal.get("campaign_id") not in (None, CAMPAIGN_ID)
            or terminal.get("status") != "unqualified"
            or terminal.get("publication_eligible") is not False
            or terminal.get("stopped_group") != RUST_GROUP
            or terminal.get("completed_candidate_groups") != completed
            or terminal.get("completed_commands") != 5
            or terminal.get("inherited_candidate_groups") != inherited
            or terminal.get("inherited_candidate_commands") != 55
            or terminal.get("combined_completed_candidate_commands") != 60
            or terminal.get("remaining_ready_groups") != remaining
            or terminal.get("ready_groups") != 38
            or terminal.get("full_84_group_coverage_claimed") is not False):
        raise RuntimeError("segment terminal does not reconcile to 55 inherited, five new and 32 pending")
    return inherited + completed, [RUST_GROUP], remaining


def _validate_pending_attempts(root: Path, report: Path, remaining: list[str]) -> None:
    old = _old_module()
    for group_id in remaining:
        path = report / "attempts" / group_id
        old._reject_symlink_components(root, path)
        if path.exists():
            raise RuntimeError(f"pending group already has an attempt directory: {group_id}")


def _entry_digest(entries: list[dict]) -> str:
    raw = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _inventory_segment(root: Path, report: Path, work: Path, plan: dict,
                       evidence_inventory_path: Path, parent_ref: dict) -> list[dict]:
    old = _old_module()
    receipt = _json(evidence_inventory_path, "segment evidence inventory")
    expected = receipt.get("files")
    if not isinstance(expected, list):
        raise RuntimeError("segment evidence inventory files must be a list")
    seen = old._inventory_report(root, report)
    seen.pop(evidence_inventory_path.relative_to(root).as_posix(), None)
    plan_by_id = {group["id"]: group for group in plan["groups"]}
    for group_id in FIRST_SIX:
        attempt_group = report / "attempts" / group_id
        if {item.name for item in attempt_group.iterdir() if item.is_dir()} != {"attempt-01"}:
            raise RuntimeError(f"attempt history is not exactly one attempt for {group_id}")
        group = plan_by_id[group_id]
        for output in group.get("output_roots", []):
            output_path = work / "sources" / group_id / Path(*_safe_relative(output, "output root").parts)
            old._inventory_tree(root, output_path, seen)
    actual = [seen[key] for key in sorted(seen)]
    if (actual != expected or receipt.get("campaign_id") != CAMPAIGN_ID
            or receipt.get("plan_sha256") != sha(root / "reports/timing/v0.9.2" / CAMPAIGN_ID / "qualified-plan.json")
            or receipt.get("parent_checkpoint") != parent_ref
            or receipt.get("publication_eligible") is not False
            or receipt.get("file_count") != len(actual)
            or receipt.get("total_bytes") != sum(item["size_bytes"] for item in actual)
            or receipt.get("entries_sha256") != _entry_digest(actual)):
        raise RuntimeError("segment preserved evidence differs from its inventory receipt")
    old._inventory_file(root, evidence_inventory_path, seen)
    return [seen[key] for key in sorted(seen)]


def create_checkpoint(root: Path, parent_segment_plan_path: Path) -> dict:
    """Validate and build an immutable checkpoint for the stopped Nov 21 segment."""
    root = Path(root).resolve()
    old = _old_module()
    _relative, plan_path = old._repo_path(root, parent_segment_plan_path, "segment plan")
    plan = _json(plan_path, "segment plan")
    if plan.get("campaign_id") != CAMPAIGN_ID:
        raise RuntimeError("segment plan campaign identity is not 20261121-01")
    plan_sha = sha(plan_path)
    report = root / "reports" / "timing" / "v0.9.2" / CAMPAIGN_ID
    work = root / "execution-state" / f"timing-v092-{CAMPAIGN_ID}"
    start_path = report / "campaign-start.json"
    progress_path = report / "progress.jsonl"
    terminal_path = report / "campaign-terminal.json"
    evidence_path = report / "evidence-inventory-01.json"
    start = _json(start_path, "segment campaign-start")
    if start.get("plan_sha256") != plan_sha or start.get("plan_commit") != PLAN_COMMIT:
        raise RuntimeError("segment start does not bind its plan SHA and approved commit")
    old._verify_parent_plan_commit(root, plan_path, plan, start)
    parent_ref = plan.get("continuation")
    parent = old.verify_checkpoint(root, parent_ref, plan=plan)
    if (parent.get("parent_campaign_id") != PARENT_CAMPAIGN_ID
            or start.get("continuation_checkpoint") != parent_ref
            or start.get("inherited_candidate_groups") != parent.get("completed_groups")):
        raise RuntimeError("segment start does not inherit the sealed Nov 15 checkpoint")
    groups, ready, _blocked = old._plan_groups(plan)
    ready_ids = [group["id"] for group in ready]
    if (ready_ids[:55] != parent.get("completed_groups")
            or ready_ids[55:] != parent.get("remaining_ready_groups")):
        raise RuntimeError("segment plan changed the inherited ready-command membership or order")
    progress_rows = _read_progress(progress_path)
    campaign_terminal = _json(terminal_path, "segment campaign-terminal")
    completed_groups, quarantined, remaining = _validate_partition(parent, progress_rows, campaign_terminal)
    progress_hash = sha(progress_path)
    if len(progress_rows) != 12:
        raise RuntimeError("segment progress row count differs from the six-pair frontier")
    plan_by_id = {group["id"]: group for group in groups}
    attempt_dirs = {path.name for path in (report / "attempts").iterdir() if path.is_dir()}
    if attempt_dirs != set(FIRST_SIX):
        raise RuntimeError("segment attempt directory set differs from the exact six attempted groups")
    starts, terminals = [], []
    for group_id in FIRST_SIX[:5]:
        start_ref, terminal_ref = _validate_success(
            root, report, work, plan, plan_by_id[group_id], plan_sha,
        )
        starts.append(start_ref)
        terminals.append(terminal_ref)
    rust_start, rust_terminal = _validate_rust_outcome_only(
        root, report, work, plan, plan_by_id[RUST_GROUP], plan_sha,
    )
    starts.append(rust_start)
    terminals.append(rust_terminal)
    _validate_pending_attempts(root, report, remaining)
    evidence_files = _inventory_segment(root, report, work, plan, evidence_path, parent_ref)
    parent_segment_ref = _ref(root, plan_path, "segment plan")
    report_root = report.relative_to(root).as_posix()
    work_root = work.relative_to(root).as_posix()
    source_roots = [f"{work_root}/sources/{group}" for group in FIRST_SIX]
    return {
        "schema": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "parent_campaign_id": CAMPAIGN_ID,
        "resource_campaign_ids": [PARENT_CAMPAIGN_ID, CAMPAIGN_ID],
        "parent_checkpoint": parent_ref,
        "parent_checkpoint_sha256": parent_ref["sha256"],
        "parent_input_references": old.input_references(parent),
        "parent_plan": parent_segment_ref,
        "campaign_start": _ref(root, start_path, "segment campaign-start"),
        "progress": _ref(root, progress_path, "segment progress"),
        "campaign_terminal": _ref(root, terminal_path, "segment campaign-terminal"),
        "evidence_inventory": _ref(root, evidence_path, "segment evidence inventory"),
        "completed_groups": completed_groups,
        "segment_completed_groups": FIRST_SIX[:5],
        "quarantined_groups": quarantined,
        "remaining_ready_groups": remaining,
        "parent_report_root": report_root,
        "parent_work_root": work_root,
        "parent_source_roots": source_roots,
        "resource_campaign_report_roots": [
            f"reports/timing/v0.9.2/{PARENT_CAMPAIGN_ID}", report_root,
        ],
        "attempt_starts": starts,
        "completed_terminals": terminals[:5],
        "quarantined_terminal": terminals[5],
        "evidence_files": evidence_files,
        "publication_eligible": False,
    }


def _compare_new_plan(root: Path, parent_plan: dict, plan: dict,
                      reference: dict, checkpoint: dict) -> None:
    if plan.get("continuation") != reference:
        raise RuntimeError("new plan continuation reference differs from the checkpoint")
    if plan.get("continuation_mode") != "semantic-quarantine/v1" or plan.get("semantic_mismatch_policy") != POLICY:
        raise RuntimeError("new plan semantic mismatch policy differs from the frozen quarantine policy")
    auth_ref = plan.get("execution_authorization")
    if not isinstance(auth_ref, dict) or set(auth_ref) != {"path", "sha256"}:
        raise RuntimeError("new plan requires one execution authorization reference")
    old = _old_module()
    auth_raw, auth_path = old._read_bytes(root, auth_ref, "execution authorization")
    auth = _json(root / auth_path, "execution authorization")
    authorized, status = auth.get("authorized"), auth.get("status")
    if (auth.get("schema") != AUTH_SCHEMA or auth.get("campaign_id") != plan.get("campaign_id")
            or not isinstance(authorized, bool)
            or (authorized is False and status != "pending")
            or (authorized is True and status != "authorized")):
        raise RuntimeError("execution authorization receipt is malformed or inconsistent")

    left, right = json.loads(json.dumps(parent_plan)), json.loads(json.dumps(plan))
    allowed = {
        "campaign_id", "created_utc", "launch_after_utc", "preregistration", "runtime_bindings",
        "continuation", "continuation_mode", "semantic_mismatch_policy", "execution_authorization",
    }
    for key in allowed:
        left.pop(key, None)
        right.pop(key, None)
    left_source, right_source = left.get("source_plan"), right.get("source_plan")
    if not isinstance(left_source, dict) or not isinstance(right_source, dict):
        raise RuntimeError("source_plan binding is missing")
    left_source.pop("bindings_sha256", None)
    right_source.pop("bindings_sha256", None)
    left_resources, right_resources = left.get("resources"), right.get("resources")
    if not isinstance(left_resources, dict) or not isinstance(right_resources, dict):
        raise RuntimeError("resource declaration is malformed")
    left_resources.pop("total_execution_budget_seconds", None)
    right_resources.pop("total_execution_budget_seconds", None)
    left_helpers, right_helpers = left.get("execution_helpers"), right.get("execution_helpers")
    if not isinstance(left_helpers, dict) or not isinstance(right_helpers, dict):
        raise RuntimeError("active execution helper map is malformed")
    helper_key = "scripts/v092_timing_qualified_campaign.py"
    checkpoint_helper = "scripts/v092_timing_segment_checkpoint.py"
    for helper_map in (left_helpers, right_helpers):
        helper_map.pop(helper_key, None)
        helper_map.pop(checkpoint_helper, None)
    # The qualified helper digest may change; all other plan inputs remain exact.
    if left != right:
        raise RuntimeError("new plan drifts from the stopped segment beyond the allowed continuation metadata")
    parent_active = parent_plan.get("execution_helpers", {})
    new_active = plan.get("execution_helpers", {})
    expected_keys = set(parent_active) | {checkpoint_helper}
    if set(new_active) != expected_keys:
        raise RuntimeError("new active helper set must add only the segment checkpoint helper")
    for name, digest in parent_active.items():
        if name != helper_key and new_active.get(name) != digest:
            raise RuntimeError(f"new plan changed an existing execution helper: {name}")
    if not isinstance(new_active.get(helper_key), str) or not _SHA.fullmatch(new_active[helper_key]):
        raise RuntimeError("new qualified helper hash is malformed")
    if new_active.get(checkpoint_helper) != sha(Path(__file__)):
        raise RuntimeError("new plan does not bind this segment checkpoint helper")
    if (not isinstance(plan.get("groups"), list)
            or [group.get("id") for group in plan["groups"]] != parent_plan["group_order"]):
        raise RuntimeError("new plan changed the full group list or order")
    remaining = checkpoint["remaining_ready_groups"]
    by_id = {group["id"]: group for group in plan["groups"]}
    expected_budget = sum(by_id[group_id]["deadline_seconds"] for group_id in remaining)
    if plan["resources"].get("total_execution_budget_seconds") != expected_budget:
        raise RuntimeError("new plan execution budget must equal the exact 32-command suffix")


def verify_checkpoint(root: Path, reference: dict, plan: dict | None = None) -> dict:
    """Revalidate segment evidence, and optionally the exact next-plan delta."""
    root = Path(root).resolve()
    old = _old_module()
    raw, relative = old._read_bytes(root, reference, "segment checkpoint")
    checkpoint = _json(root / relative, "segment checkpoint")
    if checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported segment checkpoint schema")
    expected = create_checkpoint(root, checkpoint.get("parent_plan", {}).get("path", ""))
    comparable = dict(checkpoint)
    fresh = dict(expected)
    comparable.pop("created_utc", None)
    fresh.pop("created_utc", None)
    if comparable != fresh:
        raise RuntimeError("segment checkpoint no longer matches preserved evidence")
    if reference != {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}:
        raise RuntimeError("segment checkpoint reference is not canonical")
    if plan is not None:
        parent_path = old._repo_path(root, checkpoint["parent_plan"]["path"], "segment plan")[1]
        parent_plan = _json(parent_path, "segment plan")
        _compare_new_plan(root, parent_plan, plan, reference, checkpoint)
    return checkpoint


def input_references(checkpoint: dict) -> list[dict]:
    """Return the transitive input refs, excluding bulky evidence inventory entries."""
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise RuntimeError("unsupported segment checkpoint object")
    old = _old_module()
    parent_path = checkpoint.get("parent_checkpoint")
    if not isinstance(parent_path, dict):
        raise RuntimeError("segment checkpoint lacks its CPv1 reference")
    # CPv1 input refs are copied into the immutable object so callers can bind
    # the full provenance chain without reading unrelated runtime trees.
    inherited = checkpoint.get("parent_input_references")
    if not isinstance(inherited, list):
        raise RuntimeError("segment checkpoint lacks inherited CPv1 input references")
    refs = list(inherited) + [parent_path]
    refs.extend(checkpoint.get(key) for key in (
        "parent_plan", "campaign_start", "progress", "campaign_terminal", "evidence_inventory",
    ))
    refs.extend(checkpoint.get("attempt_starts", []))
    refs.extend(checkpoint.get("completed_terminals", []))
    refs.append(checkpoint.get("quarantined_terminal"))
    result, seen = [], {}
    for item in refs:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise RuntimeError("segment checkpoint input reference is malformed")
        path = _safe_relative(item.get("path"), "checkpoint input reference").as_posix()
        digest = item.get("sha256")
        if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
            raise RuntimeError("checkpoint input SHA-256 is malformed")
        if path in seen:
            if seen[path] != digest:
                raise RuntimeError(f"conflicting checkpoint input digest: {path}")
            continue
        seen[path] = digest
        result.append({"path": path, "sha256": digest})
    return result
