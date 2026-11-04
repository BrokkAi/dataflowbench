"""Graph-owned archive130/physical131 history and exact source identity checks."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Callable

import packet


GROUP = "joern-swift-common108"
ATTEMPT = "joern-swift-common108-attempt-05-series-02"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_HISTORY_SCHEMA = "v092-joern05-source-history-input/v1"
SOURCE_HISTORY_FIELDS = {
    "schema", "provider_ref", "execution_head", "execution_tree", "source_commit",
    "source_tree", "plan_commit", "contract_ref", "source_evidence_ref", "live_ledger_ref",
}
CURRENT_SOURCE_CAS_SCHEMA = "v092-joern05-current-source-cas/v1"
CURRENT_SOURCE_CAS_FIELDS = {
    "schema", "source_commit", "source_tree", "baseline_current_head",
    "native_request", "source_refs", "source_review",
}
CURRENT_SOURCE_BASELINE_HEAD = "ab5c8ade58b789957e48de29ca54f432457611c1"
CURRENT_SOURCE_REVIEW_SCHEMA = "v092-joern05-current-source-review/v1"
CURRENT_SOURCE_REVIEW_STATUS = "approved-current-source-snapshot-only"
CURRENT_SOURCE_REVIEW_SCOPE = {
    "source_only": True,
    "evaluation_scope": "semantic-only",
    "uncontended_timing_certified": False,
    "relative_performance_conclusions_authorized": False,
    "publication_hold": True,
    "execution_authorized": False,
}
NATIVE10_SOURCE_REFS = {
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py":
        "5f513fe20ff23e3f2fed6f32adb311e3cfa77ab43b56b50b13a0251969777f42",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py":
        "7c0ef87663df318cbd4136d3d56bb17c3e3222294e321a3f853846e372368788",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py":
        "8be67e915b74105f89377b86cefb067b78573850b8e439377cb530e93c7197c9",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-10/retained_resources.py":
        "ea8fa4268477a4411c55d44c1704f132d8b0b8b4b9bf0f722b4afd404f9bbe08",
}
HISTORY02_REF = {
    "path": "reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history_provider_02.py",
    "sha256": "da691ca16a4d1169e1f32d3524fb146bc4e60722dd99ea12bb9e03ac38436a8b",
}
NATIVE_SOURCE_INPUT_REFS = (
    # The eligible plan is safe declarative source input. Native capture,
    # process reconciliation, and sidecar observations remain private runtime
    # prerequisites and are validated at their own evidence boundary.
    "eligible_joern_plan",
)


def _json_line(line: bytes, number: int) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            packet.require(key not in value, f"duplicate JSON key on live ledger row {number}: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(line, object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise packet.AdapterError(f"invalid live ledger row {number}: {exc}") from exc
    packet.require(isinstance(value, dict), f"live ledger row {number} must be an object")
    return value


def _parse_jsonl(raw: bytes) -> tuple[list[bytes], list[dict[str, Any]]]:
    packet.require(type(raw) is bytes and raw.endswith(b"\n"),
                   "live ledger must be bounded JSONL ending in newline")
    lines = raw.splitlines(keepends=True)
    packet.require(all(line.strip() for line in lines), "live ledger contains a blank row")
    return lines, [_json_line(line, index) for index, line in enumerate(lines, 1)]


def validate_source_history_input(root: Path, core: dict[str, Any],
                                  git: Callable[..., str]) -> dict[str, Any]:
    """Bind plan execution HEAD separately from Bifrost source commit S."""
    value = core.get("source_history_input")
    packet.require(type(value) is dict and set(value) == SOURCE_HISTORY_FIELDS
                   and value.get("schema") == SOURCE_HISTORY_SCHEMA,
                   "exact caller-bound source_history_input is required")
    packet.require(value.get("provider_ref") == packet.HISTORY_PROVIDER03_REF,
                   "source history provider03 source pin differs")
    for field in ("execution_head", "source_commit", "plan_commit"):
        packet.require(type(value.get(field)) is str and HEX40.fullmatch(value[field]),
                       f"source history {field} must be a full lowercase commit SHA")
    for field in ("execution_tree", "source_tree"):
        packet.require(type(value.get(field)) is str and HEX40.fullmatch(value[field]),
                       f"source history {field} must be a full lowercase tree SHA")
    packet.require(value["execution_head"] == value["plan_commit"] == core.get("plan_commit")
                   and value["source_commit"] == core.get("source_commit"),
                   "plan P or source S differs from the bound current core")
    packet.require(value["contract_ref"] == core.get("contract")
                   and value["source_evidence_ref"] == core.get("source_evidence"),
                   "source history contract/evidence refs differ from core")
    live = value.get("live_ledger_ref")
    provider = packet.load_history_provider(root)
    packet.require(type(live) is dict and set(live) == {"path", "sha256", "rows"}
                   and live.get("path") == packet.LIVE_LEDGER_PATH
                   and live.get("sha256") == provider.LEDGER_RAW_SHA256
                   and type(live.get("rows")) is int and live["rows"] == 130,
                   "source history must bind the exact starting live130 snapshot")
    packet.require(git(root, "rev-parse", "HEAD") == value["execution_head"]
                   and git(root, "rev-parse", "HEAD^{tree}") == value["execution_tree"],
                   "execution HEAD/tree differs from the current plan-bound identity")
    packet.require(git(root, "rev-parse", value["source_commit"] + "^{tree}") == value["source_tree"],
                   "source S tree differs from the separately bound source identity")
    contract = packet.document(root, value["contract_ref"])
    evidence = packet.document(root, value["source_evidence_ref"])
    packet.require(contract.get("source_commit") == value["source_commit"]
                   and evidence.get("source_commit") == value["source_commit"]
                   and evidence.get("plan_commit") == value["plan_commit"],
                   "current contract/source evidence S/P identities differ")
    if "contract_sha256" in evidence:
        packet.require(evidence["contract_sha256"] == value["contract_ref"]["sha256"],
                       "current source evidence contract SHA differs")
    if "contract" in evidence:
        packet.require(evidence["contract"] == value["contract_ref"],
                       "current source evidence contract ref differs")
    return copy.deepcopy(value)


def validate_source_cas_fields(root: Path, core: dict[str, Any], refs: dict[str, Any],
                               git: Callable[..., str]) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """Validate the caller-bound current source CAS and its independent review."""
    cas_ref = core.get("current_source_cas")
    packet.require(type(cas_ref) is dict and set(cas_ref) == {"path", "sha256"},
                   "exact current_source_cas ref is required")
    value = packet.document(root, cas_ref)
    packet.require(type(value) is dict and set(value) == CURRENT_SOURCE_CAS_FIELDS and
                   value.get("schema") == CURRENT_SOURCE_CAS_SCHEMA,
                   "current source CAS fields or schema differ")
    for key in ("source_commit", "source_tree", "baseline_current_head"):
        pattern = HEX40.fullmatch(value.get(key, "")) if type(value.get(key)) is str else None
        packet.require(pattern is not None, f"current source CAS {key} must be a full SHA-1")
    packet.require(value["baseline_current_head"] == CURRENT_SOURCE_BASELINE_HEAD and
                   value["source_commit"] == core.get("source_commit") and
                   value["source_tree"] == core.get("source_tree"),
                   "current source CAS S/tree/baseline differs from current core")
    source_input = core.get("source_history_input")
    packet.require(type(source_input) is dict and
                   source_input.get("source_commit") == value["source_commit"] and
                   source_input.get("source_tree") == value["source_tree"] and
                   source_input.get("execution_head") == core.get("plan_commit") and
                   source_input.get("plan_commit") == core.get("plan_commit"),
                   "source history and current source CAS S/P identities differ")
    packet.require(git(root, "rev-parse", value["source_commit"] + "^{tree}") == value["source_tree"] and
                   git(root, "rev-parse", "HEAD") == core.get("plan_commit") and
                   git(root, "rev-parse", "HEAD^{tree}") == source_input.get("execution_tree"),
                   "current source S/tree or executable plan P/HEAD/tree differs")
    git(root, "merge-base", "--is-ancestor", value["baseline_current_head"],
        value["source_commit"])
    git(root, "merge-base", "--is-ancestor", value["source_commit"],
        core["plan_commit"])

    native_request_ref = value.get("native_request")
    packet.require(type(native_request_ref) is dict and
                   set(native_request_ref) == {"path", "sha256"} and
                   native_request_ref == refs.get("native_control_request"),
                   "current source CAS must bind the actual native08 request ref")
    request = packet.document(root, native_request_ref)
    packet.require(request.get("expected_head") == value["baseline_current_head"],
                   "native08 request did not run against the exact baseline HEAD")

    source_refs = value.get("source_refs")
    packet.require(type(source_refs) is list and source_refs,
                   "current source CAS closure must be a non-empty typed path/SHA list")
    source_map: dict[str, dict[str, str]] = {}
    for item in source_refs:
        packet.require(type(item) is dict and set(item) == {"path", "sha256"},
                       "current source CAS entries must contain only path and sha256")
        path = item.get("path")
        digest = item.get("sha256")
        packet.require(type(path) is str and path and type(digest) is str and
                       HEX64.fullmatch(digest) and path not in source_map,
                       "current source CAS contains a malformed or duplicate source ref")
        source_map[path] = copy.deepcopy(item)

    source_review_ref = value.get("source_review")
    packet.require(type(source_review_ref) is dict and
                   set(source_review_ref) == {"path", "sha256"},
                   "current source CAS independent review ref is malformed")
    packet.require(source_review_ref["path"] not in source_map and
                   cas_ref["path"] not in source_map,
                   "current source CAS/review cannot be self-included in its source closure")
    review = packet.document(root, source_review_ref)
    packet.require(type(review) is dict and set(review) == {
        "schema", "status", "automatic_retry", "bindings", "scope"},
        "current source review fields differ")
    expected_bindings = {
        "source_commit": value["source_commit"],
        "source_tree": value["source_tree"],
        "baseline_current_head": value["baseline_current_head"],
        "source_refs_sha256": packet.digest(packet.canonical(source_refs)),
        "native_request_sha256": native_request_ref["sha256"],
        "adapter_module_refs_sha256": packet.digest(packet.canonical(
            core.get("adapter_module_refs"))),
    }
    packet.require(review.get("schema") == CURRENT_SOURCE_REVIEW_SCHEMA and
                   review.get("status") == CURRENT_SOURCE_REVIEW_STATUS and
                   review.get("automatic_retry") is False and
                   review.get("bindings") == expected_bindings and
                   review.get("scope") == CURRENT_SOURCE_REVIEW_SCOPE,
                   "current source review does not approve the exact S-only closure")

    required: dict[str, dict[str, str]] = {}

    def add(ref: Any, label: str) -> None:
        packet.require(type(ref) is dict and set(ref) == {"path", "sha256"},
                       f"{label} ref is malformed")
        path = ref["path"]
        packet.require(source_map.get(path) == ref,
                       f"current source CAS omitted or rebound {label}: {path}")
        required[path] = ref

    contract = packet.document(root, core["contract"])
    contract_inputs = contract.get("source_inputs")
    packet.require(type(contract_inputs) is list,
                   "current contract source-input inventory is missing")
    for item in contract_inputs:
        packet.require(type(item) is dict and
                       {"path", "sha256"} <= set(item),
                       "current contract source input is malformed")
        add({"path": item["path"], "sha256": item["sha256"]},
            "current contract input")
    for ref in core.get("runtime_module_graph", {}).values():
        add(ref, "runtime88 module")
    for ref in core.get("adapter_module_refs", {}).values():
        add(ref, "adapter7 module")
    for ref, label in ((packet.HISTORY_PROVIDER03_REF, "provider03"),
                       (HISTORY02_REF, "provider02")):
        add(ref, label)
    for path, digest in NATIVE10_SOURCE_REFS.items():
        add({"path": path, "sha256": digest}, "native10 source")
    # Source evidence is produced after S and binds S/P; including it in the
    # source closure would create a post-S/self-reference cycle.  The retained
    # source design and BF0140 qualification are immutable predecessor inputs
    # committed at S, so they remain ordinary source refs.
    for key in ("source_design", "qualification"):
        if key in core:
            add(core[key], "current core " + key)
    for key in NATIVE_SOURCE_INPUT_REFS:
        packet.require(key in refs, "current source CAS prerequisite is missing: " + key)
        add(refs[key], "current prerequisite " + key)
    require_ref = core.get("joern_runner_source")
    packet.require(require_ref is not None, "current Joern runner source ref is missing")
    add(require_ref, "current Joern runner source")
    packet.require(set(source_map) == set(required),
                   "current source CAS contains missing or non-input refs")
    return copy.deepcopy(value), source_map


def validate_current_source_cas(root: Path, core: dict[str, Any], refs: dict[str, Any],
                                git: Callable[..., str]) -> dict[str, Any]:
    """Prove the exact current-S source closure using the pinned native10 CAS verifier.

    The native10 helper files are source-evidence utilities here. This path
    never loads the provider, invokes a query, or starts an analyzer.
    """
    value, source_map = validate_source_cas_fields(root, core, refs, git)
    entries: list[tuple[str, Any]] = []
    primary: BaseException | None = None
    result: dict[str, Any] | None = None
    try:
        archive_ref = {"path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py",
                       "sha256": NATIVE10_SOURCE_REFS["reports/releases/v0.9.2/acquisition/joern-native-controls-10/archive_evidence.py"]}
        reconcile_ref = {"path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py",
                         "sha256": NATIVE10_SOURCE_REFS["reports/releases/v0.9.2/acquisition/joern-native-controls-10/process_reconciliation.py"]}
        wrapper_ref = {"path": "reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py",
                       "sha256": NATIVE10_SOURCE_REFS["reports/releases/v0.9.2/acquisition/joern-native-controls-10/native_qualifier.py"]}
        archive_module = packet.load_bound_module(root, "archive_evidence", archive_ref)
        entries.append(("archive_evidence", archive_module))
        reconcile_module = packet.load_bound_module(root, "process_reconciliation", reconcile_ref)
        entries.append(("process_reconciliation", reconcile_module))
        wrapper = packet.load_bound_module(root, "native_qualifier", wrapper_ref)
        entries.append(("native_qualifier", wrapper))
        packet.require(wrapper.archive_evidence is archive_module and
                       wrapper.process_reconciliation is reconcile_module,
                       "native10 source module imports do not bind the exact preloaded leaves")
        archive_context = archive_module.build_context(root, source_map)
        checked = wrapper.verify_current_source_refs(
            root, value["source_commit"], value["source_refs"], archive_context)
        packet.require(type(checked) is dict and checked.get("status") == "verified" and
                       checked.get("head") == value["source_commit"] and
                       checked.get("source_ref_count") == len(value["source_refs"]),
                       "native10 archive-aware current source proof differs")
        archived_paths = checked.get("archived_member_paths")
        packet.require(type(archived_paths) is list and len(archived_paths) == 96
                       and archived_paths == sorted(set(archived_paths))
                       and checked.get("archived_member_count") == 96
                       and all(path in source_map for path in archived_paths),
                       "native10 verified archived-member set is not the exact96 source subset")
        result = {
            "schema": "v092-joern05-current-source-proof/v1",
            "status": "verified",
            "source_commit": value["source_commit"],
            "source_tree": value["source_tree"],
            "execution_head": core["plan_commit"],
            "baseline_current_head": value["baseline_current_head"],
            "source_refs_sha256": packet.digest(packet.canonical(value["source_refs"])),
            "source_ref_count": checked["source_ref_count"],
            "current_direct_count": checked["current_direct_count"],
            "archived_member_count": checked["archived_member_count"],
            # Keep the exact verifier-derived raw-member set in the opaque
            # in-process context. The compact diagnostic publishes only its
            # count and digest; these refs let the live snapshot callback
            # recheck raw bytes absent from the current Git tree.
            "source_refs": copy.deepcopy(value["source_refs"]),
            "archived_member_paths": copy.deepcopy(archived_paths),
            "archived_member_refs": [copy.deepcopy(source_map[path])
                                     for path in archived_paths],
            "archive": copy.deepcopy(checked["archive"]),
            "native_request": copy.deepcopy(value["native_request"]),
            "source_review": copy.deepcopy(value["source_review"]),
        }
    except BaseException as error:
        primary = error
        raise
    finally:
        if entries:
            try:
                packet.cleanup_registered_modules(entries)
            except BaseException as cleanup_error:
                if primary is not None:
                    packet.attach_cleanup_error(primary, cleanup_error)
                else:
                    raise
    packet.require(result is not None, "current source CAS did not produce an actual proof")
    return result


def _validate_current_context(root: Path, current: dict[str, Any]) -> dict[str, Any]:
    fields = {"contract", "source_commit", "plan_commit", "source_evidence"}
    packet.require(type(current) is dict and set(current) == fields,
                   "current context must contain exact contract/source/plan/evidence fields")
    source_commit = current["source_commit"]
    plan_commit = current["plan_commit"]
    packet.require(type(source_commit) is str and HEX40.fullmatch(source_commit)
                   and type(plan_commit) is str and HEX40.fullmatch(plan_commit),
                   "current source and plan commits must be full lowercase SHA-1 values")
    contract_ref, evidence_ref = current["contract"], current["source_evidence"]
    packet.require(type(contract_ref) is dict and set(contract_ref) == {"path", "sha256"}
                   and type(evidence_ref) is dict and set(evidence_ref) == {"path", "sha256"}
                   and type(contract_ref.get("sha256")) is str
                   and HEX64.fullmatch(contract_ref["sha256"])
                   and type(evidence_ref.get("sha256")) is str
                   and HEX64.fullmatch(evidence_ref["sha256"]),
                   "current contract or source-evidence ref is malformed")
    contract = packet.document(root, contract_ref)
    evidence = packet.document(root, evidence_ref)
    packet.require(contract.get("source_commit") == source_commit
                   and evidence.get("source_commit") == source_commit
                   and evidence.get("plan_commit") == plan_commit,
                   "current contract/source evidence commit differs")
    if "contract_sha256" in evidence:
        packet.require(evidence["contract_sha256"] == contract_ref["sha256"],
                       "current source evidence contract differs")
    if "contract" in evidence:
        packet.require(evidence["contract"] == contract_ref,
                       "current source evidence contract ref differs")
    return {
        "contract": copy.deepcopy(contract_ref),
        "source_commit": source_commit,
        "plan_commit": plan_commit,
        "source_evidence": copy.deepcopy(evidence_ref),
    }


def _validate_baseline_facts(provider: Any, baseline: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packet.require(baseline.get("schema") == "v092-joern05-archived130-history-context/v1"
                   and baseline.get("status") == "source-only-archived130-baseline-verified"
                   and baseline.get("execution_authorized") is False
                   and baseline.get("automatic_retry") is False
                   and baseline.get("current_live_ledger_validation") == "not-performed-by-this-reader",
                   "provider03 archive-only result carries unexpected authority or live-tail state")
    identity = baseline.get("ledger_identity", {})
    packet.require(identity.get("rows") == provider.LEDGER_ROWS == 130
                   and identity.get("raw_sha256") == provider.LEDGER_RAW_SHA256
                   and identity.get("status_counts") == provider.TOTAL_STATUS_COUNTS,
                   "provider03 archived130 ledger identity differs")
    historical = baseline.get("historical109", {})
    annex = baseline.get("bifrost0144_c5_annex21", {})
    old_rows, annex_rows = historical.get("rows"), annex.get("rows")
    packet.require(type(old_rows) is list and len(old_rows) == 109
                   and historical.get("sha256") == provider.SEALED109_RAW_SHA256,
                   "provider03 historical109 partition differs")
    packet.require(type(annex_rows) is list and len(annex_rows) == 21
                   and annex.get("sha256") == provider.C5_ANNEX_SHA256
                   and annex.get("global_attempt_numbers") == list(range(111, 132)),
                   "provider03 C5 annex21 partition differs")
    sealed = baseline.get("sealed109_lineage", {})
    packet.require(type(sealed.get("source_contexts")) is dict
                   and len(sealed["source_contexts"]) == 9
                   and type(sealed.get("retained20")) is list,
                   "provider03 sealed109 source-context lineage differs")
    packet.require(len({row.get("attempt_id") for row in old_rows + annex_rows}) == 130,
                   "provider03 archive partitions contain duplicate attempt identities")
    scala = baseline.get("bifrost0144_scala_partial", {})
    packet.require(scala.get("group_id") == "bifrost-scala-kernel"
                   and scala.get("global_attempt_number") == 128
                   and scala.get("status") == "recorder-error"
                   and scala.get("exit_code") == 124
                   and scala.get("timed_out") is True
                   and scala.get("source_commit") == provider.C5_SOURCE_COMMIT
                   and scala.get("plan_commit") == provider.C5_PLAN_COMMIT
                   and scala.get("contract_sha256") == provider.C5_CONTRACT_SHA256
                   and scala.get("completion_claim") is False,
                   "provider03 typed 0.14.4 Scala partial differs")
    return old_rows, annex_rows


def _validate_tail_terminal(row: dict[str, Any], current: dict[str, Any]) -> None:
    status = row.get("status")
    code = row.get("exit_code")
    packet.require(status in {"completed", "failed", "timed-out"}
                   and type(code) is int
                   and ((status == "completed" and code == 0 and row.get("timed_out") is False)
                        or (status == "failed" and code != 0 and row.get("timed_out") is False)
                        or (status == "timed-out" and code == 124 and row.get("timed_out") is True))
                   and row.get("capacity_loss") is None
                   and not row.get("disk_guard_error")
                   and not row.get("recorder_error")
                   and row.get("tool") == "joern"
                   and row.get("group_id") == GROUP
                   and row.get("attempt_id") == ATTEMPT
                   and row.get("source_commit") == current["source_commit"]
                   and row.get("plan_commit") == current["plan_commit"]
                   and row.get("contract_sha256") == current["contract"]["sha256"]
                   and row.get("execution_series") == 2,
                   "physical row131 is not the exact ordinary Joern terminal")
    ownership = row.get("process_ownership")
    packet.require(type(ownership) is dict
                   and ownership.get("schema") == "invocation-process-ownership/v1"
                   and ownership.get("cleanup_status") == "tracked-processes-stopped"
                   and not ownership.get("cleanup_error")
                   and not ownership.get("tracking_error")
                   and type(ownership.get("root_pid")) is int
                   and ownership["root_pid"] > 0
                   and type(ownership.get("tracked_processes")) is list
                   and ownership["tracked_processes"]
                   and ownership.get("descendant_containment") == "unproven"
                   and ownership.get("tracking_interval_seconds") == 2.0
                   and all(type(item) is dict and set(item) == {"pid", "start_identity"}
                           and type(item["pid"]) is int and item["pid"] > 0
                           and type(item["start_identity"]) is str and item["start_identity"]
                           for item in ownership["tracked_processes"])
                   and len({item["pid"] for item in ownership["tracked_processes"]}) ==
                   len(ownership["tracked_processes"])
                   and ownership["root_pid"] in {
                       item["pid"] for item in ownership["tracked_processes"]},
                   "physical row131 has incomplete exact-birth process ownership")


def _validate_tail(row: dict[str, Any], current: dict[str, Any],
                   annex_rows: list[dict[str, Any]]) -> dict[str, Any]:
    packet.require(type(annex_rows) is list and len(annex_rows) == 21,
                   "exact archived C5 annex21 is required to derive the next global attempt")
    annex_numbers = [item.get("global_attempt_number") if type(item) is dict else None
                     for item in annex_rows]
    packet.require(annex_numbers == list(range(111, 132)),
                   "archived C5 annex global attempts must be the exact111..131 prefix")
    global_attempt_number = annex_numbers[-1] + 1
    packet.require(row.get("group_id") == GROUP and row.get("attempt_id") == ATTEMPT,
                   "physical row131 is not the exact Joern05 attempt")
    packet.require(global_attempt_number == 132 and "global_attempt_number" not in row,
                   "frozen physical row131 schema must omit adapter-derived global attempt number")
    packet.require(row.get("source_commit") == current["source_commit"]
                   and row.get("plan_commit") == current["plan_commit"]
                   and row.get("contract_sha256") == current["contract"]["sha256"]
                   and row.get("execution_series") == 2,
                   "physical row131 current contract/source/plan/series differs")
    _validate_tail_terminal(row, current)
    return {
        "row": copy.deepcopy(row),
        "physical_ledger_row": 131,
        "global_attempt_number": global_attempt_number,
        "status": row["status"],
        "completion_claim": False,
        "eligible": False,
    }


def _selected_historical_rows(
    old_rows: list[dict[str, Any]], retained20: list[dict[str, Any]],
    tail: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    replacements = {item["group_id"] for item in retained20}
    selected = {
        row["group_id"]: row for row in old_rows[:89]
        if row.get("status") == "completed" and row["group_id"] not in replacements
    }
    for row in old_rows[89:]:
        selected[row["group_id"]] = row
    if tail is not None:
        row = tail["row"]
        if row.get("status") == "completed" and row.get("exit_code") == 0 \
                and row.get("timed_out") is False and row.get("capacity_loss") is None \
                and row.get("recorder_error") is None:
            selected[GROUP] = row
    return selected


def _combine_live_snapshot(
    root: Path, raw: bytes, baseline: dict[str, Any], provider: Any,
    current_context: dict[str, Any], live_ledger_ref: dict[str, Any],
) -> dict[str, Any]:
    old_rows, annex_rows = _validate_baseline_facts(provider, baseline)
    lines, rows = _parse_jsonl(raw)
    packet.require(len(rows) in (130, 131),
                   "live ledger must be exact archived130 or archived130 plus one physical row131")
    packet.require(packet.digest(b"".join(lines[:130])) == provider.LEDGER_RAW_SHA256,
                   "live ledger does not preserve exact archived130 bytes")
    packet.require(rows[:109] == old_rows and rows[109:130] == annex_rows,
                   "live ledger archive partitions differ from provider03")
    ids = [row.get("attempt_id") for row in rows]
    packet.require(all(isinstance(value, str) and value for value in ids)
                   and len(set(ids)) == len(ids),
                   "live ledger attempt identities are missing or duplicated")
    packet.require(packet.digest(b"".join(lines[:130])) == live_ledger_ref["sha256"]
                   and live_ledger_ref["rows"] == 130,
                   "live snapshot does not start at the separately bound exact130 ref")
    current = _validate_current_context(root, current_context)
    tail = _validate_tail(rows[130], current, annex_rows) if len(rows) == 131 else None
    selected = _selected_historical_rows(
        old_rows, baseline["sealed109_lineage"]["retained20"], tail)
    annex_attempt_ids = {row["attempt_id"] for row in annex_rows}
    selected_attempt_ids = {row.get("attempt_id") for row in selected.values()}
    packet.require(not annex_attempt_ids.intersection(selected_attempt_ids),
                   "C5 annex attempt identities leaked into selected sealed109 Joern history")
    raw_sha = packet.digest(raw)
    scala = copy.deepcopy(baseline["bifrost0144_scala_partial"])
    return {
        "schema": "v092-joern05-adapter08-history-context/v1",
        "status": "source-only-archive130-live-tail-verified",
        "history_provider_ref": copy.deepcopy(packet.HISTORY_PROVIDER03_REF),
        "execution_authorized": False,
        "automatic_retry": False,
        "current_joern_eligibility": "not-assessed-by-this-reader",
        "source_history_input": {
            "schema": SOURCE_HISTORY_SCHEMA,
            "provider_ref": copy.deepcopy(packet.HISTORY_PROVIDER03_REF),
            "execution_head": baseline["current_source_identity"]["commit"],
            "execution_tree": baseline["current_source_identity"]["tree"],
            "source_commit": current["source_commit"],
            "plan_commit": current["plan_commit"],
            "contract_ref": current["contract"],
            "source_evidence_ref": current["source_evidence"],
        },
        "current_source_identity": copy.deepcopy(baseline["current_source_identity"]),
        "current_context_candidate": current,
        "baseline_identity": copy.deepcopy(baseline["ledger_identity"]),
        "live_ledger": {
            "path": live_ledger_ref["path"],
            "sha256": raw_sha,
            "rows": len(rows),
            "appended_rows": len(rows) - 130,
            "archived130_prefix_sha256": provider.LEDGER_RAW_SHA256,
        },
        "historical109": {"rows": old_rows, "sha256": provider.SEALED109_RAW_SHA256},
        "bifrost0144_c5_annex21": {
            "rows": annex_rows,
            "sha256": provider.C5_ANNEX_SHA256,
            "global_attempt_numbers": list(range(111, 132)),
        },
        "bifrost0144_scala_partial": scala,
        "tail_row131": tail,
        "selected_historical_joern_rows": selected,
        "sealed109_source_contexts": copy.deepcopy(
            baseline["sealed109_lineage"]["source_contexts"]),
        "sealed109_lineage": {
            "consumed_events": copy.deepcopy(
                baseline["sealed109_lineage"]["consumed_events"]),
            "retained20": copy.deepcopy(
                baseline["sealed109_lineage"]["retained20"]),
        },
        "source_context_roster_extension": "not-created-by-adapter08",
        "current_target": {
            "status": "partial-target-evidence",
            "current_target_full": False,
            "full_model_qualification": False,
            "configuration_ready": False,
            "publication_approved": False,
            "configuration_status": "pending-current-target-incomplete",
            "reason": "C5 annex remains separate and its typed Scala attempt is recorder-error/timeout",
            "scala_partial": scala,
        },
    }


def validate(
    root: Path = packet.ROOT,
    *,
    core: dict[str, Any],
    git: Callable[..., str],
    live_ledger_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Validate exact source S/P, archive130, sealed109, and physical row131 only."""
    root = Path(root)
    packet.require(root.resolve() == packet.ROOT.resolve(),
                   "adapter08 history reader is pinned to its repository checkout")
    source_input = validate_source_history_input(root, core, git)
    provider = packet.load_history_provider(root)
    baseline = provider.validate_archive_only_130(
        root, expected_head=source_input["execution_head"],
        expected_tree=source_input["execution_tree"])
    if live_ledger_bytes is None:
        live_ledger_bytes = packet.read_live_ledger(root)
    result = _combine_live_snapshot(
        root, live_ledger_bytes, baseline, provider,
        {key: core[key] for key in ("contract", "source_commit", "plan_commit", "source_evidence")},
        source_input["live_ledger_ref"])
    packet.require(result["current_source_identity"] == {
        "commit": source_input["execution_head"], "tree": source_input["execution_tree"]},
        "provider03 observed source identity differs from source_history_input")
    prerequisite_refs = core.get("prerequisite_refs")
    packet.require(type(prerequisite_refs) is dict,
                   "current source CAS requires the caller-bound prerequisite refs")
    result["current_source_proof"] = validate_current_source_cas(
        root, core, prerequisite_refs, git)
    result["source_history_input"] = copy.deepcopy(source_input)
    return result


def context_bindings(root: Path) -> dict[str, dict[str, Any]]:
    """Return only the nine sealed109 contexts; never extend them with current."""
    old = packet.inherited_core(root)
    result = copy.deepcopy(old["source_contexts"])
    packet.require(type(result) is dict and len(result) == 9,
                   "sealed109 historical context roster differs")
    return result


def selected_rows(root: Path, history_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packet.require(history_result.get("schema") == "v092-joern05-adapter08-history-context/v1"
                   and history_result.get("execution_authorized") is False
                   and history_result.get("source_context_roster_extension") == "not-created-by-adapter08",
                   "adapter08 verified history context required")
    selected = history_result.get("selected_historical_joern_rows")
    historical = history_result.get("historical109", {}).get("rows")
    retained = history_result.get("sealed109_lineage", {}).get("retained20")
    tail = history_result.get("tail_row131")
    packet.require(type(selected) is dict and type(historical) is list and
                   len(historical) == 109 and type(retained) is list,
                   "selected sealed109/current Joern history inputs are absent")
    packet.require(tail is None or
                   (type(tail) is dict and set(tail) == {
                       "row", "physical_ledger_row", "global_attempt_number",
                       "status", "completion_claim", "eligible"} and
                    type(tail.get("row")) is dict and
                    tail.get("physical_ledger_row") == 131 and
                    tail.get("global_attempt_number") == 132 and
                    tail.get("status") == tail["row"].get("status") and
                    tail.get("completion_claim") is False and
                    tail.get("eligible") is False),
                   "current selector tail is not the exact typed physical131 row")
    expected = _selected_historical_rows(historical, retained, tail)
    packet.require(selected == expected,
                   "current Joern selection is not derived from exact history and physical tail")
    if tail is not None and tail.get("row", {}).get("status") == "completed":
        packet.require(selected.get(GROUP) == tail["row"],
                       "successful physical131 is absent from current Joern selection")
    return copy.deepcopy(selected)


def selected_historical_rows(history_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the historical109 selection without replacing Joern with row131."""
    packet.require(history_result.get("schema") == "v092-joern05-adapter08-history-context/v1"
                   and history_result.get("execution_authorized") is False,
                   "adapter08 verified history context required")
    historical = history_result.get("historical109", {}).get("rows")
    retained = history_result.get("sealed109_lineage", {}).get("retained20")
    packet.require(type(historical) is list and len(historical) == 109
                   and type(retained) is list,
                   "exact sealed109 selection inputs are missing")
    selected = _selected_historical_rows(historical, retained, None)
    packet.require(GROUP in selected,
                   "historical109 Joern selection is absent")
    return selected
