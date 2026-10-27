#!/usr/bin/env python3
"""Build the append-only Joern fourth-attempt capability continuation contract.

This is a prospective artifact builder. It reads the reviewed repaired plan,
capability evidence, fresh control receipt, the consumed Joern03 diagnosis, and
the explicit fourth-attempt authorization, then derives an append-only
continuation contract from the immutable v0.9.2 contract.  It never invokes an analyzer,
runner, checker, compiler, or launch process.  The contract deliberately does
not contain a containing commit hash: the source commit is supplied by the
caller, while the plan commit is checked separately after the contract has
been materialized and committed.  That keeps the contract/plan commit closure
non-circular.

The normal two-step use is:

1. pass ``--source-commit`` and emit a new contract into the untracked output
   path; commit the contract with the repaired plan closure;
2. pass ``--source-commit --plan-commit --verify`` to check that exact plan
   commit contains every artifact and that the committed contract is the
   deterministic result of the reviewed inputs.

The builder has no overwrite mode. It never consumes an analyzer attempt and
never modifies the historical contract, plan, ledger, or continuation-01 inputs.  A later manifest, final review, and
one-shot admission receipt remain separate artifacts and are intentionally not
generated here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
BASE_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
BASE_CONTRACT_SHA = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
BASE_SOURCE_COMMIT = "0f105a6f4bd6a954fd09cb222e8a519162393aec"
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
OLD_CONTRACT = (
    "reports/releases/v0.9.2/execution-v4/continuations/"
    "joern-capability-repair-04-contract.json"
)
OLD_CONTRACT_SHA = "5a9aa55014847fdedce612429c4b856213ac228d59418e95e302483a472ca827"
OLD_CONTINUATION_SOURCE = (
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py"
)
OLD_CONTINUATION_SOURCE_SHA = "712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa"
OLD_CONTINUATION_TEST = (
    "reports/releases/v0.9.2/acquisition/test-joern-capability-continuation-01.py"
)
OLD_CONTINUATION_TEST_SHA = "9eef52992edc1699584521496c3036c1595c6616ae453de336ffcb315627f1e9"
OLD_PLAN = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
OLD_PLAN_SHA = "e5cfd9d5473fd47f54de25d74a6f945c667c086ce471d5f6cdcead797bf9e3ab"
FINAL_PLAN = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "plan-v092-02/execution-plan.json"
)
EVIDENCE = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "capability-evidence.json"
)
DEFAULT_OUTPUT = (
    "reports/releases/v0.9.2/execution-v4/continuations/"
    "joern-capability-repair-05-contract.json"
)
QUAL_ROOT = "reports/releases/v0.9.2/qualification/joern-capability-repair-01"
CONTINUATION_SOURCE = "reports/releases/v0.9.2/acquisition/joern-capability-continuation-02.py"
CONTINUATION_TEST = "reports/releases/v0.9.2/acquisition/test-joern-capability-continuation-02.py"
SHIM = "scripts/joern_capability_repair_v092.py"
SHIM_TEST = "scripts/test-joern-capability-repair-v092.py"
JOERN_GROUP = "joern-swift-common108"
CODEQL_GROUP = "codeql-swift-common108"
JOERN_OUTPUT = "reports/raw/joern-common-v2/current108-v092-02"
AUTHORIZATION_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "authorization-fourth-attempt-01.json"
)
AUTHORIZATION_SHA = "d0068fa640f953912cc0b682b0fb8b957282e174ad3f103493d38cb2c140f9d7"
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
LEDGER_ROWS = 87
LEDGER_SHA = "57d8265e8eb0c216c56e184a5fed36f9931bcb5b36ea1047ae3f4a0c71f0a096"
# The live predecessor has 87 rows including the consumed Joern03 recorder
# error.  The older continuation validator recovers its own contexts from the
# first 86 rows, so keep that historical boundary explicit and separate from
# the immutable 87-row source snapshot.
HISTORICAL_LEDGER_ROWS = 86
HISTORICAL_LEDGER_SHA = "ca7152afb422160b30c2f38677aa539a1463b45e3b41131848b3d9e81d4a1084"
SEALED_LEDGER_ROWS = 87
SEALED_LEDGER_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "sealed-ledger-prefix-87.jsonl"
)
SEALED_LEDGER_SHA = LEDGER_SHA
HISTORICAL_MANIFEST = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "continuation-manifest-02.json"
)
HISTORICAL_MANIFEST_SHA = "fa81d5f6aee3cf5099eab6aeafabcbf59c3020b9cc2cdbe88a19a56167e2b73f"
HISTORICAL_REVIEW = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "final-continuation-independent-review-06.json"
)
HISTORICAL_REVIEW_SHA = "dac59010aa334d8d7b1531ae193ead8bca1542ae4a19b77fe0035ef29851f73c"
HISTORICAL_ADMISSION = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "execution-admission-03.json"
)
HISTORICAL_ADMISSION_SHA = "bff52a5fe497c4bac35932fb75cb0c11552981f6e582c3f274384da4dadf7e7b"
HISTORICAL_STOP_REVIEW = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "supervision24-stop-independent-review-01.json"
)
HISTORICAL_STOP_REVIEW_SHA = "09615a269a7b75dfb4b8ff11f2dd984eaa7c11a11b69a825cdd21d6df7d66601"
HISTORICAL_HELPER = "reports/releases/v0.9.2/acquisition/joern-capability-admission-03.py"
HISTORICAL_HELPER_SHA = "cd4865c1171cd27b68edcf2d77046307f22dfc511cb1706d931fdbea4cb69e44"
RE_SHA = re.compile(r"[0-9a-f]{64}\Z")
RE_COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class BuildError(ValueError):
    """A prospective continuation input is malformed or not hash-bound."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise BuildError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(path: str, description: str = "path") -> Path:
    candidate = Path(path)
    require(not candidate.is_absolute(), f"{description} must be relative")
    parts = candidate.parts
    require(parts and all(part not in {"", ".", ".."} for part in parts),
            f"{description} escapes the repository")
    return candidate


def _full(root: Path, path: str, description: str = "path") -> Path:
    relative = _relative(path, description)
    full = (root / relative).resolve()
    require(full == root or root in full.parents, f"{description} escapes the repository")
    return full


def read_bytes(root: Path, path: str, description: str = "file") -> bytes:
    full = _full(root, path, description)
    require(full.exists() and full.is_file() and not full.is_symlink(),
            f"{description} is absent or not a regular file: {path}")
    return full.read_bytes()


def file_sha(root: Path, path: str, description: str = "file") -> str:
    return sha_bytes(read_bytes(root, path, description))


def load_json(root: Path, path: str, description: str) -> dict[str, Any]:
    try:
        value = json.loads(read_bytes(root, path, description))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"{description} is not valid JSON: {path}") from exc
    require(isinstance(value, dict), f"{description} must be a JSON object: {path}")
    return value


def load_json_value(root: Path, path: str, description: str) -> object:
    """Load any valid JSON value for recursive evidence-graph traversal.

    The top-level qualification indexes are objects, but their referenced
    command/raw/fixture files are independently authored JSON documents and
    may be arrays or scalar values.  They still have to be parsed so that a
    nested path/SHA reference cannot be omitted from the committed closure.
    """
    try:
        return json.loads(read_bytes(root, path, description))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"{description} is not valid JSON: {path}") from exc


def git(root: Path, *args: str, text: bool = True) -> str | bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=text,
                                       stderr=subprocess.PIPE).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr)
        raise BuildError(f"git {' '.join(args)} failed: {detail.strip()}") from exc


def check_commit(root: Path, commit: str, label: str) -> None:
    require(RE_COMMIT.fullmatch(commit) is not None, f"{label} must be an exact 40-hex commit")
    git(root, "cat-file", "-e", f"{commit}^{{commit}}")


def ancestor(root: Path, older: str, newer: str, label: str) -> None:
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=root,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError(f"{label} is not an ordered commit ancestry") from exc


def committed_sha(root: Path, commit: str, path: str, label: str = "committed file") -> str:
    _relative(path, label)
    try:
        raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root,
                                      stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError(f"{label} is absent at {commit}: {path}") from exc
    return sha_bytes(raw)


def ref(root: Path, path: str, description: str) -> dict[str, str]:
    return {"path": path, "sha256": file_sha(root, path, description)}


def require_ref(root: Path, value: object, description: str) -> dict[str, str]:
    require(isinstance(value, dict) and set(value) == {"path", "sha256"},
            f"{description} is not a path/SHA reference")
    path = value.get("path")
    digest = value.get("sha256")
    require(isinstance(path, str) and RE_SHA.fullmatch(str(digest or "")),
            f"{description} has a malformed path/SHA reference")
    require(file_sha(root, path, description) == digest, f"{description} digest changed")
    return {"path": path, "sha256": digest}


def path_sha_refs(value: object) -> Iterable[tuple[str, str]]:
    """Yield only explicit path/SHA objects; traversal is read-only."""
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value["path"], value["sha256"]
        for child in value.values():
            yield from path_sha_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from path_sha_refs(child)


def _case_map(plan: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    cases = plan.get("cases")
    require(isinstance(cases, dict), f"{label} cases must be an object")
    require(len(cases) == 108, f"{label} must contain exactly 108 cases")
    require(all(isinstance(k, str) and isinstance(v, dict) for k, v in cases.items()),
            f"{label} cases are malformed")
    return cases


def validate_final_plan(root: Path, evidence: dict[str, Any], old: dict[str, Any],
                       new: dict[str, Any]) -> None:
    require(new.get("schema") == old.get("schema") == "joern-common-execution-plan/v092",
            "repaired plan schema changed")
    for key in ("execution_contract", "fixture_revision", "identity", "identity_components",
                "output_root", "phase_sequence", "population_sha256", "profile", "query_root",
                "resources", "runtime", "engine", "configurations", "codeql_packs", "release_group_id"):
        require(new.get(key) == old.get(key), f"repaired plan changed forbidden field: {key}")
    require(new.get("release_group_id") == JOERN_GROUP, "repaired plan group identity changed")
    require(new.get("execution_eligible") is True and
            new.get("diagnostic_execution_eligible") is True and
            new.get("status") == "execution-eligible", "repaired plan is not execution eligible")
    require(new.get("full_model_qualification") is False and
            new.get("scored_activation") is False and
            new.get("aggregate_resource_qualification") == old.get("aggregate_resource_qualification"),
            "repaired plan qualification limits changed")
    old_cases = _case_map(old, "old plan")
    new_cases = _case_map(new, "repaired plan")
    require(set(old_cases) == set(new_cases), "repaired plan case roster changed")
    patch = evidence.get("proposed_repaired_execution_plan", {}).get("case_capability_patch")
    require(isinstance(patch, dict) and len(patch) == 96,
            "capability evidence does not provide exactly 96 reviewed cases")
    attempts = {case_id for case_id, case in new_cases.items()
                if case.get("disposition") == "attempt"}
    unsupported = {case_id for case_id, case in new_cases.items()
                   if case.get("disposition") == "unsupported"}
    require(len(attempts) == 96 and len(unsupported) == 12,
            "repaired plan must retain 96 attempts and 12 unsupported cases")
    require(set(patch) == attempts, "capability patch does not cover exactly the attempted cases")
    for case_id, old_case in old_cases.items():
        new_case = new_cases[case_id]
        old_without_capability = {k: v for k, v in old_case.items() if k != "capability"}
        new_without_capability = {k: v for k, v in new_case.items() if k != "capability"}
        require(new_without_capability == old_without_capability,
                f"repaired plan changed selection semantics for {case_id}")
        if case_id in attempts:
            expected = patch[case_id]
            require(new_case.get("capability") == expected,
                    f"repaired capability is not the reviewed evidence value: {case_id}")
            require(set(expected) == {"identity_gate", "model_status", "model_mode"} and
                    expected.get("identity_gate") and expected.get("model_status") and
                    expected.get("model_mode") in {"off", "on"},
                    f"repaired capability is not explicit: {case_id}")
        else:
            require("capability" not in new_case and new_case == old_case,
                    f"unsupported case was changed: {case_id}")
    allowed = {"cases", "qualification_control_projection_sha256", "qualification_control_plan",
               "fresh_qualification", "registered_at_unix_seconds"}
    for key in set(old) | set(new):
        if key in allowed:
            continue
        require(new.get(key) == old.get(key), f"repaired plan changed forbidden field: {key}")
    require(new.get("qualification_control_projection_sha256") ==
            evidence.get("qualification_projection_gate", {}).get("repaired_projection_sha256"),
            "repaired projection does not match capability evidence")


def validate_fresh_qualification(root: Path, plan: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    control_plan = require_ref(root, plan.get("qualification_control_plan"), "fresh control plan")
    receipt = require_ref(root, plan.get("fresh_qualification"), "fresh qualification receipt")
    control = load_json(root, control_plan["path"], "fresh control plan")
    qual = load_json(root, receipt["path"], "fresh qualification receipt")
    projection = plan.get("qualification_control_projection_sha256")
    require(isinstance(projection, str) and RE_SHA.fullmatch(projection),
            "repaired projection digest is malformed")
    require(control.get("execution_plan_projection_sha256") == projection and
            control.get("group_id") == JOERN_GROUP and control.get("arms") == ["off", "on"] and
            control.get("case_arm_count") == 12 and control.get("maximum_phase_invocations") == 36 and
            control.get("case_arm_budget_seconds") == 75 and control.get("total_budget_seconds") == 900,
            "fresh control plan does not preserve reviewed control bounds")
    require(qual.get("execution_plan_projection_sha256") == projection and
            qual.get("group_id") == JOERN_GROUP and qual.get("execution_eligible") is True and
            qual.get("diagnostic_execution_eligible") is True and
            qual.get("status") == "measurement-with-known-limits" and
            qual.get("full_model_qualification") is False and qual.get("scored_activation") is False,
            "fresh qualification does not bind the repaired projection and limits")
    run_ref = require_ref(root, qual.get("control_run"), "fresh control run")
    diagnostic_ref = require_ref(root, qual.get("diagnostic_admission_review"),
                                 "fresh diagnostic admission review")
    run = load_json(root, run_ref["path"], "fresh control run")
    diagnostic = load_json(root, diagnostic_ref["path"], "fresh diagnostic admission review")
    require(run.get("control_plan_sha256") == control_plan["sha256"] and
            run.get("execution_plan_projection_sha256") == projection and
            run.get("group_id") == JOERN_GROUP and run.get("phase_invocation_count") == 36 and
            isinstance(run.get("records"), list) and len(run["records"]) == 12,
            "fresh control run is not bound to the reviewed control plan")
    require(diagnostic.get("control_plan") == control_plan and
            diagnostic.get("control_run") == run_ref and
            diagnostic.get("execution_plan_projection_sha256") == projection and
            diagnostic.get("diagnostic_execution_eligible") is True,
            "fresh diagnostic review is not bound to the fresh control artifacts")
    finalization_path = f"{QUAL_ROOT}/qualification-finalization-01.json"
    finalization = load_json(root, finalization_path, "qualification finalization")
    require(finalization.get("repaired_plan") == {
                "path": FINAL_PLAN, "sha256": file_sha(root, FINAL_PLAN, "repaired plan")
            } and finalization.get("qualification_receipt") == receipt and
            finalization.get("control_run") == run_ref and
            finalization.get("diagnostic_review") == diagnostic_ref and
            finalization.get("projection_sha256") == projection and
            finalization.get("fresh_case_arms") == 12 and
            finalization.get("fresh_phase_invocations") == 36 and
            finalization.get("full_model_qualification") is False and
            finalization.get("scored_activation") is False,
            "qualification finalization is not bound to the fresh reviewed artifacts")
    return control_plan, receipt, run_ref


def validate_fourth_attempt_inputs(root: Path) -> dict[str, Any]:
    """Validate the one explicit Joern04 grant and the consumed Joern03 ledger row."""
    authorization_ref = {"path": AUTHORIZATION_PATH, "sha256": AUTHORIZATION_SHA}
    authorization = load_json(root, AUTHORIZATION_PATH, "fourth-attempt authorization")
    require(file_sha(root, AUTHORIZATION_PATH, "fourth-attempt authorization") == AUTHORIZATION_SHA,
            "fourth-attempt authorization digest changed")
    require(authorization.get("schema") == "v092-joern-capability-repair-authorization/v1" and
            authorization.get("status") ==
            "preparation-authorized; execution requires final evidence-backed plan and independent review",
            "fourth-attempt authorization is not in the reviewed preparation state")
    require(authorization.get("maximum_joern_global_attempts") == 4 and
            authorization.get("additional_joern_attempts") == 1 and
            authorization.get("additional_time_seconds") == 0 and
            authorization.get("other_attempt_limits_unchanged") is True and
            authorization.get("sealed_ledger_rows") == LEDGER_ROWS and
            authorization.get("sealed_ledger_sha256") == LEDGER_SHA,
            "fourth-attempt authorization changes the reviewed attempt or ledger boundary")
    require(authorization.get("origin_utc") in {"2026-10-20T00:57:00.680937Z",
                                                   "2026-10-20T00:57:00.680937+00:00"} and
            authorization.get("deadline_utc") in {"2026-10-23T21:33:00.680937Z",
                                                    "2026-10-23T21:33:00.680937+00:00"},
            "fourth-attempt authorization changes the original clock")
    prohibited = authorization.get("prohibited")
    require(isinstance(prohibited, list) and
            "Guessed capability values" in prohibited and
            "Weakened validation" in prohibited and
            "Further retry-budget extension" in prohibited and
            "Releases, tags, deployments or release-triggering merges" in prohibited,
            "fourth-attempt authorization does not preserve the prohibited actions")

    ledger_raw = read_bytes(root, LEDGER_PATH, "continuation ledger")
    require(sha_bytes(ledger_raw) == LEDGER_SHA, "continuation ledger digest changed")
    rows: list[dict[str, Any]] = []
    for line in ledger_raw.splitlines(keepends=True):
        try:
            row = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise BuildError("continuation ledger contains invalid JSON") from exc
        require(isinstance(row, dict), "continuation ledger rows must be objects")
        require(line == (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode(),
                "continuation ledger row is not canonical JSON")
        rows.append(row)
    require(len(rows) == LEDGER_ROWS, "continuation ledger row count changed")
    historical_prefix = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in rows[:HISTORICAL_LEDGER_ROWS]
    )
    require(sha_bytes(historical_prefix) == HISTORICAL_LEDGER_SHA,
            "historical 86-row ledger prefix changed before Joern03")
    tail = rows[HISTORICAL_LEDGER_ROWS:]
    require(len(tail) == 1 and tail[0].get("attempt_id") ==
            "joern-swift-common108-attempt-03-series-01" and
            tail[0].get("group_id") == JOERN_GROUP and
            tail[0].get("status") == "recorder-error" and
            tail[0].get("exit_code") == 1 and
            tail[0].get("timed_out") is False and tail[0].get("capacity_loss") is None,
            "continuation ledger tail is not the consumed Joern03 recorder error")
    return {"authorization": authorization_ref, "ledger": {"path": LEDGER_PATH,
                                                              "sha256": LEDGER_SHA,
                                                              "rows": LEDGER_ROWS}}


def validate_sealed_ledger_snapshot(root: Path) -> dict[str, Any]:
    """Require immutable pre-attempt bytes for the future source closure."""
    raw = read_bytes(root, SEALED_LEDGER_PATH, "sealed 87-row ledger snapshot")
    require(sha_bytes(raw) == SEALED_LEDGER_SHA,
            "sealed 87-row ledger snapshot differs from the reviewed predecessor")
    lines = raw.splitlines(keepends=True)
    require(len(lines) == SEALED_LEDGER_ROWS and raw.endswith(b"\n"),
            "sealed ledger snapshot has the wrong canonical row count")
    live = read_bytes(root, LEDGER_PATH, "continuation ledger")
    require(raw == live,
            "sealed ledger snapshot must equal the current 87-row ledger before Joern04")
    return {"path": SEALED_LEDGER_PATH, "sha256": SEALED_LEDGER_SHA,
            "rows": SEALED_LEDGER_ROWS}


def validate_historical_continuation(root: Path) -> None:
    """Bind the prior manifest/review/admission/helper and preserve their exact hashes."""
    for path, digest, label in (
        (OLD_CONTRACT, OLD_CONTRACT_SHA, "Joern03 continuation contract"),
        (OLD_CONTINUATION_SOURCE, OLD_CONTINUATION_SOURCE_SHA, "continuation-01 source"),
        (OLD_CONTINUATION_TEST, OLD_CONTINUATION_TEST_SHA, "continuation-01 test"),
        (HISTORICAL_MANIFEST, HISTORICAL_MANIFEST_SHA, "continuation-02 manifest"),
        (HISTORICAL_REVIEW, HISTORICAL_REVIEW_SHA, "continuation-02 final review"),
        (HISTORICAL_ADMISSION, HISTORICAL_ADMISSION_SHA, "continuation-02 admission"),
        (HISTORICAL_STOP_REVIEW, HISTORICAL_STOP_REVIEW_SHA, "Joern03 stop diagnosis"),
        (HISTORICAL_HELPER, HISTORICAL_HELPER_SHA, "admission helper-03"),
    ):
        require(file_sha(root, path, label) == digest, f"{label} digest changed")
    old = load_json(root, OLD_CONTRACT, "Joern03 continuation contract")
    require(old.get("source_commit") == "131fbe662844ca2e6303f8c5a90fee7dfc378f79" and
            old.get("total_wall_budget_seconds") == 333360,
            "historical Joern03 contract source or clock changed")
    old_groups = {item.get("id"): item for item in old.get("groups", [])
                  if isinstance(item, dict)}
    old_joern = old_groups.get(JOERN_GROUP)
    require(isinstance(old_joern, dict) and old_joern.get("maximum_attempts") == 3,
            "historical Joern03 contract does not preserve max3")
    old_env = old_joern.get("environment")
    require(isinstance(old_env, dict) and
            "DATAFLOWBENCH_V092_RELEASE_EXECUTION" not in old_env and
            "DATAFLOWBENCH_V092_GROUP_ID" not in old_env,
            "historical Joern03 contract already contains the new guard markers")


def collect_delta(root: Path, evidence: dict[str, Any], plan: dict[str, Any],
                  base_inputs: dict[str, str]) -> list[dict[str, str]]:
    """Return the reviewed additive source closure, sorted and duplicate-free.

    The new closure carries the full historical Joern03 stop context as small,
    explicitly bound files.  It does not recursively walk those historical
    receipts because their source-input graph is already inherited by the
    frozen contract; only the fresh control namespace is traversed transitively.
    """
    fresh_plan_ref = ref(root, FINAL_PLAN, "repaired execution plan")
    evidence_ref = ref(root, EVIDENCE, "capability evidence")
    control_plan_ref = require_ref(root, plan.get("qualification_control_plan"), "fresh control plan")
    qual_ref = require_ref(root, plan.get("fresh_qualification"), "fresh qualification receipt")
    qual = load_json(root, qual_ref["path"], "fresh qualification receipt")
    direct = [
        evidence_ref,
        fresh_plan_ref,
        control_plan_ref,
        qual_ref,
        require_ref(root, qual.get("control_run"), "fresh control run"),
        require_ref(root, qual.get("diagnostic_admission_review"), "fresh diagnostic admission review"),
        ref(root, f"{QUAL_ROOT}/control-capture-01/identity.json", "fresh control identity"),
        ref(root, f"{QUAL_ROOT}/qualification-finalization-01.json", "qualification finalization"),
        ref(root, CONTINUATION_SOURCE, "continuation source"),
        ref(root, CONTINUATION_TEST, "continuation test"),
        ref(root, SHIM, "Joern repair shim"),
        ref(root, SHIM_TEST, "Joern repair shim test"),
        ref(root, OLD_CONTRACT, "historical Joern03 continuation contract"),
        ref(root, OLD_CONTINUATION_SOURCE, "historical continuation-01 source"),
        ref(root, OLD_CONTINUATION_TEST, "historical continuation-01 test"),
        ref(root, HISTORICAL_MANIFEST, "historical continuation manifest"),
        ref(root, HISTORICAL_REVIEW, "historical continuation final review"),
        ref(root, HISTORICAL_ADMISSION, "historical continuation admission"),
        ref(root, HISTORICAL_STOP_REVIEW, "historical Joern03 stop diagnosis"),
        ref(root, HISTORICAL_HELPER, "historical admission helper"),
        ref(root, AUTHORIZATION_PATH, "fourth-attempt authorization"),
        ref(root, SEALED_LEDGER_PATH, "sealed 87-row ledger predecessor"),
    ]
    historical_paths = [
        f"{QUAL_ROOT}/continuation-manifest-review-06.json",
        f"{QUAL_ROOT}/final-review-request-06.json",
        f"{QUAL_ROOT}/materialized-preflight-03.json",
        f"{QUAL_ROOT}/retained-preflight-03.json",
        f"reports/releases/v0.9.2/attempts/{JOERN_GROUP}-attempt-03-series-01/started.json",
        f"reports/releases/v0.9.2/attempts/{JOERN_GROUP}-attempt-03-series-01/completed.json",
        f"reports/releases/v0.9.2/attempts/{JOERN_GROUP}-attempt-03-series-01/stderr.txt",
        f"reports/releases/v0.9.2/attempts/{JOERN_GROUP}-attempt-03-series-01/stdout.txt",
        "reports/releases/v0.9.2/execution-v4/supervision-24/joern-swift-common108-dispatch.json",
        "reports/releases/v0.9.2/execution-v4/supervision-24/joern-swift-common108-exit.json",
        "reports/releases/v0.9.2/execution-v4/supervision-24/supervisor-error.json",
    ]
    direct.extend(ref(root, path, "historical Joern03 context") for path in historical_paths)
    # Fresh control receipts are compact indexes over the captured raw/CPG,
    # command, fixture, and native-output files.  Follow the exact path/SHA
    # file graph to a fixed point: a receipt can point at a run index, which
    # points at raw/command JSON, which can point at further outputs.  Include
    # only references under the fresh capture namespace.  This intentionally
    # excludes unreferenced compiler caches and temporary workspace files,
    # which are not part of the reviewed qualification evidence and can be
    # very large.
    fresh_capture_prefix = f"{QUAL_ROOT}/control-capture-01/"
    fresh_index_paths = [
        f"{QUAL_ROOT}/control-capture-01/run.json",
        f"{QUAL_ROOT}/control-capture-01/qualification-receipt-01.json",
        f"{QUAL_ROOT}/control-capture-01/diagnostic-admission-review-01.json",
        f"{QUAL_ROOT}/control-capture-01/identity.json",
    ]
    pending = list(fresh_index_paths)
    visited: set[str] = set()
    while pending:
        index_path = pending.pop(0)
        if index_path in visited:
            continue
        visited.add(index_path)
        index = load_json_value(root, index_path, f"fresh control graph node: {index_path}")
        for referenced_path, referenced_sha in sorted(set(path_sha_refs(index))):
            if not referenced_path.startswith(fresh_capture_prefix):
                continue
            require(referenced_path != index_path,
                    f"fresh control graph self-references itself: {index_path}")
            require(file_sha(root, referenced_path, "fresh control referenced artifact") == referenced_sha,
                    f"fresh control referenced artifact digest changed: {referenced_path}")
            direct.append({"path": referenced_path, "sha256": referenced_sha})
            if referenced_path.endswith(".json") and referenced_path not in visited:
                pending.append(referenced_path)
    raw_cases = evidence.get("historical_raw_evidence", {}).get("case_reports")
    require(isinstance(raw_cases, dict) and len(raw_cases) == 96,
            "capability evidence does not contain exactly 96 raw witnesses")
    direct.extend(require_ref(root, witness, f"raw witness {case_id}")
                  for case_id, witness in sorted(raw_cases.items()))
    result: dict[str, str] = {}
    for item in direct:
        path, digest = item["path"], item["sha256"]
        require(path not in result or result[path] == digest,
                f"source closure has conflicting duplicate: {path}")
        result[path] = digest
    require(LEDGER_PATH not in result and
            set(result).isdisjoint(base_inputs),
            "source closure unexpectedly repeats an inherited source input")
    return [{"path": path, "sha256": result[path]} for path in sorted(result)]


def validate_source_commit(root: Path, source_commit: str, delta: list[dict[str, str]]) -> None:
    check_commit(root, source_commit, "source commit")
    require(source_commit != BASE_SOURCE_COMMIT, "source commit must be additive")
    ancestor(root, BASE_SOURCE_COMMIT, source_commit, "base/source")
    for item in delta:
        require(committed_sha(root, source_commit, item["path"], "source-input closure") == item["sha256"],
                f"source-input closure is absent or changed at source commit: {item['path']}")


def validate_plan_commit(root: Path, plan_commit: str, source_commit: str,
                         delta: Iterable[dict[str, str]],
                         artifacts: Iterable[dict[str, str]]) -> None:
    check_commit(root, plan_commit, "plan commit")
    require(plan_commit != BASE_PLAN_COMMIT, "plan commit must be additive")
    ancestor(root, source_commit, plan_commit, "source/plan")
    checked: dict[str, str] = {}
    for item in [*delta, *artifacts]:
        require(checked.setdefault(item["path"], item["sha256"]) == item["sha256"],
                f"plan closure has conflicting duplicate: {item['path']}")
        require(committed_sha(root, plan_commit, item["path"], "plan artifact") == item["sha256"],
                f"plan artifact is absent or changed at plan commit: {item['path']}")


def validate_contract_delta(root: Path, contract: dict[str, Any]) -> None:
    """Require contract-05 to differ from contract-04 only at Joern04 bindings."""
    old = load_json(root, OLD_CONTRACT, "historical Joern03 continuation contract")
    require(old.get("schema_version") == contract.get("schema_version") == 1 and
            old.get("release") == contract.get("release") == "v0.9.2" and
            old.get("execution_series") == contract.get("execution_series") == 1 and
            old.get("total_wall_budget_seconds") == contract.get("total_wall_budget_seconds") == 333360,
            "continuation contract schema or clock changed")
    old_groups = {item.get("id"): item for item in old.get("groups", [])
                  if isinstance(item, dict)}
    new_groups = {item.get("id"): item for item in contract.get("groups", [])
                  if isinstance(item, dict)}
    require(set(old_groups) == set(new_groups), "continuation group roster changed")
    for group_id, old_group in old_groups.items():
        new_group = new_groups[group_id]
        if group_id != JOERN_GROUP:
            require(new_group == old_group, f"non-Joern group changed: {group_id}")
    old_joern = old_groups[JOERN_GROUP]
    joern = new_groups[JOERN_GROUP]
    require(set(joern) == set(old_joern),
            "Joern contract shape changed beyond the reviewed marker amendment")
    for key in set(old_joern) - {"maximum_attempts", "environment"}:
        require(joern.get(key) == old_joern.get(key),
                f"Joern contract changed outside max-attempt/guard fields: {key}")
    require(old_joern.get("maximum_attempts") == 3 and joern.get("maximum_attempts") == 4,
            "Joern maximum attempt allowance is not exactly the approved fourth attempt")
    old_env = old_joern.get("environment")
    new_env = joern.get("environment")
    require(isinstance(old_env, dict) and isinstance(new_env, dict),
            "Joern environment binding is malformed")
    marker_env = {
        "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
        "DATAFLOWBENCH_V092_GROUP_ID": JOERN_GROUP,
    }
    require(new_env == {**old_env, **marker_env} and
            set(new_env) == set(old_env) | set(marker_env),
            "Joern04 environment does not add exactly the two reviewed guard markers")
    require(old_env.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION") is None and
            old_env.get("DATAFLOWBENCH_V092_GROUP_ID") is None,
            "historical Joern03 contract already contains the new markers")


def build_contract(root: Path, source_commit: str, *, plan: dict[str, Any],
                   evidence: dict[str, Any], base: dict[str, Any],
                   delta: list[dict[str, str]]) -> dict[str, Any]:
    contract = copy.deepcopy(base)
    contract["source_commit"] = source_commit
    contract["total_wall_budget_seconds"] = 333360
    contract["source_inputs"] = sorted(
        [*base["source_inputs"], *delta], key=lambda item: item["path"]
    )
    require(len({item["path"] for item in contract["source_inputs"]}) == len(contract["source_inputs"]),
            "contract source inputs contain duplicate paths")
    fresh_qualification = require_ref(root, plan["fresh_qualification"], "fresh qualification receipt")
    qualifications = contract.get("qualifications")
    require(isinstance(qualifications, dict) and isinstance(qualifications.get("joern"), dict),
            "base contract qualification roster is malformed")
    qualifications["joern"]["evidence"] = fresh_qualification
    groups = contract.get("groups")
    require(isinstance(groups, list), "base contract group roster is malformed")
    joern = next((group for group in groups if group.get("id") == JOERN_GROUP), None)
    codeql = next((group for group in groups if group.get("id") == CODEQL_GROUP), None)
    require(isinstance(joern, dict) and isinstance(codeql, dict), "base contract groups are incomplete")
    old_output = joern["output_roots"][0]
    joern["argv"] = [
        "/usr/bin/python3", SHIM, "execute", "--plan", FINAL_PLAN,
        "--evidence", EVIDENCE, "--plan-sha256", file_sha(root, FINAL_PLAN, "repaired plan"),
        "--evidence-sha256", file_sha(root, EVIDENCE, "capability evidence"),
        "--output", JOERN_OUTPUT,
    ]
    joern["maximum_attempts"] = 4
    joern["output_roots"] = [JOERN_OUTPUT]
    joern["joern_plan"] = ref(root, FINAL_PLAN, "repaired plan")
    environment = joern.get("environment")
    require(isinstance(environment, dict), "base Joern environment binding is malformed")
    require("DATAFLOWBENCH_V092_RELEASE_EXECUTION" not in environment and
            "DATAFLOWBENCH_V092_GROUP_ID" not in environment,
            "base Joern environment already contains continuation guard markers")
    joern["environment"] = {
        **environment,
        "DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
        "DATAFLOWBENCH_V092_GROUP_ID": JOERN_GROUP,
    }
    for report in joern.get("reports", []):
        if isinstance(report, dict) and isinstance(report.get("source_path"), str):
            source = report["source_path"]
            require(source.startswith(old_output + "/"), "base Joern report path is outside its output root")
            report["source_path"] = JOERN_OUTPUT + source[len(old_output):]
    # CodeQL01 runs through the same new continuation source/plan/contract
    # context, but retains its frozen command, output partitions, and attempt
    # allowance.  The continuation manifest records the new identity; this
    # contract keeps the historical CodeQL group fields byte-equal.
    validate_contract_delta(root, contract)
    return contract


def canonical_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def emit(root: Path, output: str, contract: dict[str, Any]) -> str:
    full = _full(root, output, "contract output")
    require(not full.exists() and not full.is_symlink(), "contract output already exists")
    full.parent.mkdir(parents=True, exist_ok=True)
    full.open("xb").write(canonical_json(contract))
    return sha_bytes(full.read_bytes())


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    base_raw = read_bytes(root, BASE_CONTRACT, "base contract")
    require(sha_bytes(base_raw) == BASE_CONTRACT_SHA, "base contract digest changed")
    base = load_json(root, BASE_CONTRACT, "base contract")
    old_raw = read_bytes(root, OLD_PLAN, "retained Joern plan")
    require(sha_bytes(old_raw) == OLD_PLAN_SHA, "retained Joern plan digest changed")
    old = load_json(root, OLD_PLAN, "retained Joern plan")
    evidence = load_json(root, EVIDENCE, "capability evidence")
    plan = load_json(root, args.plan, "repaired execution plan")
    require(args.plan == FINAL_PLAN, "builder only accepts the reviewed final plan path")
    require(file_sha(root, EVIDENCE, "capability evidence") ==
            "deefa524579114d6fa42271193b6f4def69e296ffd23023f1e72ae7d2ee4a005",
            "capability evidence digest changed")
    validate_final_plan(root, evidence, old, plan)
    validate_fresh_qualification(root, plan)
    validate_fourth_attempt_inputs(root)
    sealed_ledger = validate_sealed_ledger_snapshot(root)
    validate_historical_continuation(root)
    base_inputs = {item["path"]: item["sha256"] for item in base.get("source_inputs", [])}
    require(len(base_inputs) == len(base.get("source_inputs", [])), "base source inputs contain duplicates")
    delta = collect_delta(root, evidence, plan, base_inputs)
    validate_source_commit(root, args.source_commit, delta)
    contract = build_contract(root, args.source_commit, plan=plan, evidence=evidence,
                              base=base, delta=delta)
    artifacts = [
        {"path": FINAL_PLAN, "sha256": file_sha(root, FINAL_PLAN, "repaired plan")},
        {"path": EVIDENCE, "sha256": file_sha(root, EVIDENCE, "capability evidence")},
        {"path": SHIM, "sha256": file_sha(root, SHIM, "Joern repair shim")},
        {"path": CONTINUATION_SOURCE, "sha256": file_sha(root, CONTINUATION_SOURCE, "continuation source")},
        {"path": args.output, "sha256": sha_bytes(canonical_json(contract))},
    ]
    if args.plan_commit:
        validate_plan_commit(root, args.plan_commit, args.source_commit, delta, artifacts[:-1])
    result = {
        "schema": "v092-joern-capability-continuation-contract-build/v1",
        "status": "verified-existing" if args.verify else "prospective-contract-ready",
        "source_commit": args.source_commit,
        "plan_commit": args.plan_commit,
        "contract": {"path": args.output, "sha256": sha_bytes(canonical_json(contract))},
        "source_inputs_delta_count": len(delta),
        "raw_witness_count": 96,
        "repaired_plan": {"path": FINAL_PLAN, "sha256": file_sha(root, FINAL_PLAN)},
        "fresh_qualification": plan["fresh_qualification"],
        "sealed_ledger": sealed_ledger,
    }
    if args.verify:
        expected = canonical_json(contract)
        actual = read_bytes(root, args.output, "existing continuation contract")
        require(actual == expected, "existing contract differs from deterministic reviewed output")
        # The contract itself is an artifact of the plan commit.  It is checked
        # only after its containing commit exists, so no self-referential hash
        # enters the contract's source_inputs list.
        require(committed_sha(root, args.plan_commit, args.output, "continuation contract") ==
                sha_bytes(expected), "continuation contract differs at plan commit")
    else:
        result["emitted_sha256"] = emit(root, args.output, contract)
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=str(ROOT), help="repository root")
    p.add_argument("--source-commit", required=True, help="exact additive source commit")
    p.add_argument("--plan-commit", help="exact plan commit; required with --verify")
    p.add_argument("--plan", default=FINAL_PLAN, help="reviewed repaired plan path")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="new continuation contract path")
    p.add_argument("--verify", action="store_true",
                   help="verify an already materialized contract after the plan commit exists")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        require(not args.verify or args.plan_commit, "--verify requires --plan-commit")
        print(json.dumps(build(args), indent=2, sort_keys=True))
        return 0
    except BuildError as exc:
        print(f"continuation contract rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
