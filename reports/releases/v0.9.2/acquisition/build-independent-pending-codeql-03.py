#!/usr/bin/env python3
"""Build the append-only CodeQL-only continuation contract.

The builder is a pure artifact operation. It never launches an analyzer and
never reads the mutable live ledger as a source input. The base C4 contract is
copied byte-for-byte except for the reviewed successor source closure, the
no-expiry execution-window declaration, the 30 GiB aggregate working cap, and
the explicit macOS worker environment witness for the CodeQL child.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
BASE_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
BASE_SHA = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
DEFAULT_OUTPUT = "reports/releases/v0.9.2/execution-v4/continuations/codeql-independent-pending-03-contract.json"
CODEQL_GROUP = "codeql-swift-common108"
CODEQL_OUTPUT_ROOT = "reports/raw/swift-common-v2/current108-v092-01"
QUERY_RECEIPT = "reports/releases/v0.9.2/qualification/codeql-swift-common108/query-check-02/receipt.json"
QUERY_RECEIPT_SHA = "62b934fb5546296ebd790bb952a169a8fe8ea59c9e056ea377c839cfcf3fa468"
SEALED_LEDGER = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/sealed-ledger-prefix-88.jsonl"
SEALED_LEDGER_SHA = "9ae98c51570149cc7ebe86573df518b4f469188e23dd58d7bcdc37ac93532476"
NO_EXPIRY_AUTH = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json"
NO_EXPIRY_AUTH_SHA = "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc"
SOURCE_CAP_AUTH = "reports/releases/v0.9.2/qualification/joern-capability-repair-01/source-working-cap-30gib-authorization-01.json"
SOURCE_CAP_AUTH_SHA = "bcba59ae10ea1cea565641249a0dc3bddfd063c66f298e19ce2ce0b86743cdbe"
BREADTH_AUTH = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/authorization-01.json"
BREADTH_AUTH_SHA = "0f8413d52c348a9d89079c70d8cebdea3179c35a8b84a98d390c53227e6f5478"
DESIGN_01 = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-scheduling-design-01.json"
DESIGN_02 = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-scheduling-design-02.json"
DESIGN_03 = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-scheduling-design-03.json"
DESIGN_04 = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-scheduling-design-04.json"
DESIGN_05 = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-scheduling-design-05.json"
HISTORICAL_REPLAY_CONTRACT = (
    "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-08-contract.json"
)
CF_USER_TEXT_ENCODING = "0x1F5:0x0:0x0"
HISTORICAL_CONTEXT_FILES = (
    "reports/releases/v0.9.2/acquisition/failed-contract-01.json",
    "reports/releases/v0.9.2/acquisition/scoped-recovery-contract-02.json",
    "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-04-contract.json",
    "reports/releases/v0.9.2/execution-v4/continuations/joern-capability-repair-08-contract.json",
    "reports/releases/v0.9.2/attempts/bifrost-c-kernel-attempt-01-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/bifrost-c-kernel-attempt-01-series-01/started.json",
    "reports/releases/v0.9.2/attempts/bifrost-c-kernel-attempt-01-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/bifrost-c-kernel-attempt-01-series-01/stderr.txt",
    "reports/releases/v0.9.2/attempts/codeql-java-modeling-attempt-01-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/codeql-java-modeling-attempt-01-series-01/started.json",
    "reports/releases/v0.9.2/attempts/codeql-java-modeling-attempt-01-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/codeql-java-modeling-attempt-01-series-01/stderr.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-01-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-01-series-01/started.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-01-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-01-series-01/stderr.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-02-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-02-series-01/started.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-02-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-02-series-01/stderr.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-03-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-03-series-01/started.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-03-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-03-series-01/stderr.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-04-series-01/completed.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-04-series-01/started.json",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-04-series-01/stdout.txt",
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-04-series-01/stderr.txt",
)
HISTORICAL_REPLAY_SUPPORT_FILES = {
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py":
        "712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa",
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py":
        "848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/continuation-manifest-02.json":
        "fa81d5f6aee3cf5099eab6aeafabcbf59c3020b9cc2cdbe88a19a56167e2b73f",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/continuation-manifest-06.json":
        "96cc7331c6043f270b07398dc546e07688e6df99c024c1b9da48a0782cd714ce",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-02/execution-plan.json":
        "76264424ddfa31b11788459368ae9b65058685cb7bab60d14353d9c96fca102f",
    "reports/releases/v0.9.2/acquisition/matrix-supervision-28.py":
        "1327fe49cc9223bcdccc312635a698160530942e649d096fb3a8e145667abdfb",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/capability-evidence.json":
        "deefa524579114d6fa42271193b6f4def69e296ffd23023f1e72ae7d2ee4a005",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/authorization-fourth-attempt-01.json":
        "d0068fa640f953912cc0b682b0fb8b957282e174ad3f103493d38cb2c140f9d7",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/continuation-manifest-review-06.json":
        "8e461c2d154d47e810ad64f1bf7e518e126d2589581751a4e8ad176cb15537dc",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/execution-admission-03.json":
        "bff52a5fe497c4bac35932fb75cb0c11552981f6e582c3f274384da4dadf7e7b",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/final-continuation-independent-review-06.json":
        "dac59010aa334d8d7b1531ae193ead8bca1542ae4a19b77fe0035ef29851f73c",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/final-review-request-06.json":
        "f35032c71d4551f432f65db3e92b25da36983d5e10a6e8798ec591ed60a39fd1",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/materialized-preflight-03.json":
        "38f5f2dc604eb134884b9ffff0bcb1bd615298e52d0f87ff93bb96ed0085cf31",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/retained-preflight-03.json":
        "428ff31f52f0bb8eeb4743a7fa462b83c63a23db4a67e4df88f504cc8e6036cf",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/supervision24-stop-independent-review-01.json":
        "09615a269a7b75dfb4b8ff11f2dd984eaa7c11a11b69a825cdd21d6df7d66601",
    "reports/releases/v0.9.2/acquisition/joern-capability-admission-03.py":
        "cd4865c1171cd27b68edcf2d77046307f22dfc511cb1706d931fdbea4cb69e44",
    "reports/releases/v0.9.2/acquisition/joern-capability-continuation-02.py":
        "2a661f91cab8877acffcd8104c7710237a321432091d0a1ac2765bee3a340798",
    "reports/releases/v0.9.2/acquisition/test-joern-capability-continuation-02.py":
        "a3b8a0d93cdcf119a3e7512092600e114a121a4aead14b3824739108a5a297d1",
    "reports/releases/v0.9.2/acquisition/test-joern-capability-continuation-01.py":
        "9eef52992edc1699584521496c3036c1595c6616ae453de336ffcb315627f1e9",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json":
        "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc",
}
RE_SHA = re.compile(r"[0-9a-f]{64}\Z")
RE_COMMIT = re.compile(r"[0-9a-f]{40}\Z")

OWNED_FILES = (
    "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/test-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/build-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/test-build-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/admission-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/test-admission-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-03.py",
    "reports/releases/v0.9.2/acquisition/test-supervisor-independent-pending-codeql-03.py",
)

PREDECESSOR_FILES = (
    "reports/releases/v0.9.2/acquisition/independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/test-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/build-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/test-build-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/admission-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/test-admission-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/acquisition/test-supervisor-independent-pending-codeql-02.py",
    "reports/releases/v0.9.2/execution-v4/continuations/codeql-independent-pending-02-contract.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-manifest-02.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-admission-02.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/execution-admission-codeql-02.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/final-codeql-independent-review-02.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/control-review-codeql-02.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/control02-stop-diagnosis-01.json",
    "reports/releases/v0.9.2/acquisition/independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/test-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/build-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/test-build-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/admission-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/test-admission-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/acquisition/test-supervisor-independent-pending-codeql-01.py",
    "reports/releases/v0.9.2/execution-v4/continuations/codeql-independent-pending-01-contract.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-admission-01.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/final-codeql-independent-review-01.json",
    "reports/releases/v0.9.2/qualification/independent-pending-groups-01/runtime-registration-review-01.json",
)

# These three scripts were already present in the source tree when CodeQL02
# reached the frozen source snapshot gate.  They are explicit prospective
# source inputs for this successor; binding them here makes the next source
# commit reviewable instead of relying on a broad untracked-file exception.
PROSPECTIVE_SOURCE_FILES = (
    "scripts/joern_capability_repair_v092_03.py",
    "scripts/test-joern-capability-repair-v092-03.py",
    "scripts/test-joern-successor-runtime-v092-01.py",
)


class CodeQLBuildError(ValueError):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise CodeQLBuildError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    try:
        return sha_bytes(path.read_bytes())
    except OSError as exc:
        raise CodeQLBuildError(f"cannot hash {path}: {exc}") from exc


def _relative(value: object, description: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{description} is malformed")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts),
            f"{description} is unsafe")
    return path


def _path(root: Path, value: str) -> Path:
    path = root
    for part in _relative(value).parts:
        path = path / part
        require(not path.is_symlink(), f"symlink in source closure: {value}")
    return path


def binding(root: Path, value: str) -> dict[str, str]:
    path = _path(root, value)
    require(path.is_file(), f"source closure file is missing: {value}")
    return {"path": value, "sha256": sha(path)}


def _git_show(root: Path, commit: str, path: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CodeQLBuildError(f"{path} is absent from source commit {commit}") from exc


def verify_commit_contains(root: Path, commit: str, refs: list[dict[str, str]], description: str) -> None:
    require(RE_COMMIT.fullmatch(commit), f"{description} is not a full commit SHA")
    for item in refs:
        raw = _git_show(root, commit, item["path"])
        require(sha_bytes(raw) == item["sha256"],
                f"{description} does not contain the bound bytes: {item['path']}")


def verify_exact_commit(root: Path, commit: str, description: str) -> None:
    """Require a resolvable full commit, never an arbitrary 40-hex token."""
    require(isinstance(commit, str) and RE_COMMIT.fullmatch(commit),
            f"{description} is not a full commit SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=root, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CodeQLBuildError(f"{description} is not a repository commit") from exc
    require(resolved == commit, f"{description} is not the exact resolved commit")


def _base(root: Path) -> dict[str, Any]:
    raw = _path(root, BASE_CONTRACT).read_bytes()
    require(sha_bytes(raw) == BASE_SHA, "frozen C4 contract changed")
    value = json.loads(raw)
    require(isinstance(value, dict) and len(value.get("groups", [])) == 84,
            "frozen C4 contract has an unexpected group roster")
    return value


def source_closure(root: Path) -> list[dict[str, str]]:
    """Return only additive immutable refs; the live ledger is deliberately excluded."""
    paths = list(OWNED_FILES) + list(PREDECESSOR_FILES) + [
        SEALED_LEDGER, QUERY_RECEIPT, NO_EXPIRY_AUTH,
        SOURCE_CAP_AUTH, BREADTH_AUTH,
    ] + list(HISTORICAL_CONTEXT_FILES) + list(HISTORICAL_REPLAY_SUPPORT_FILES)
    # Retain the scheduling design chain as immutable provenance.  The
    # successor is validated against design-04; earlier designs remain
    # source inputs rather than being overwritten or relabeled.
    paths.extend([DESIGN_01, DESIGN_02, DESIGN_03, DESIGN_04, DESIGN_05])
    paths.extend(PROSPECTIVE_SOURCE_FILES)
    # The frozen C4 base has 789 source inputs while the retained Joern04
    # predecessor has 1,133.  Preserve the exact predecessor-only inputs so
    # its historical context can be replayed from this successor's closure.
    # This is a read-only union and rejects the mutable live ledger.
    predecessor_raw = _path(root, HISTORICAL_REPLAY_CONTRACT).read_bytes()
    try:
        predecessor = json.loads(predecessor_raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CodeQLBuildError("historical Joern04 contract is not valid JSON") from exc
    predecessor_items = predecessor.get("source_inputs") if isinstance(predecessor, dict) else None
    require(isinstance(predecessor_items, list), "historical Joern04 source closure is missing")
    predecessor_digests: dict[str, str] = {}
    for item in predecessor_items:
        require(isinstance(item, dict) and isinstance(item.get("path"), str) and
                RE_SHA.fullmatch(str(item.get("sha256") or "")),
                "historical Joern04 source closure binding is malformed")
        path = item["path"]
        require(path != "reports/releases/v0.9.2/ledger-v1.jsonl",
                "mutable live ledger may not enter the CodeQL source closure")
        old = predecessor_digests.get(path)
        require(old is None or old == item["sha256"],
                f"historical Joern04 source closure repeats a path with a different digest: {path}")
        predecessor_digests[path] = item["sha256"]
    paths.extend(predecessor_digests)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        item = binding(root, path)
        expected = HISTORICAL_REPLAY_SUPPORT_FILES.get(path) or predecessor_digests.get(path)
        require(expected is None or item["sha256"] == expected,
                f"historical replay support changed: {path}")
        result.append(item)
    return result


def draft_contract(root: Path, source_commit: str, source_refs: list[dict[str, str]]) -> dict[str, Any]:
    base = _base(root)
    value = copy.deepcopy(base)
    value["source_commit"] = source_commit
    value["total_wall_budget_seconds"] = None
    value["resource_guards"]["working_set_gib"] = 30
    value["execution_window"] = {
        "schema": "v092-no-user-execution-window-policy/v1",
        "mode": "no-user-imposed-expiry",
        "original_origin_utc": "2026-10-20T00:57:00.680937+00:00",
        "cutoff_utc": None,
        "total_wall_budget_seconds": None,
        "phase_remaining_reserved_seconds": 28032,
        "per_attempt_timeout_seconds": 13840,
        "startup_allowance_seconds": 30,
        "authorization": {"path": NO_EXPIRY_AUTH, "sha256": NO_EXPIRY_AUTH_SHA},
    }
    value["aggregate_source_working_cap"] = {
        "before_gib": 12, "after_gib": 30,
        "before_bytes": 12 * 1024**3, "after_bytes": 30 * 1024**3,
        "authorization": {"path": SOURCE_CAP_AUTH, "sha256": SOURCE_CAP_AUTH_SHA},
    }
    value["breadth_first_authorization"] = {
        "path": BREADTH_AUTH, "sha256": BREADTH_AUTH_SHA,
    }
    value["independent_codeql_scope"] = {
        "schema": "v092-independent-codeql-continuation/v1",
        "sealed_prefix_rows": 88, "sealed_prefix_sha256": SEALED_LEDGER_SHA,
        "historical_completed_groups": 82, "tail_rows_allowed": 1,
        "group_id": CODEQL_GROUP, "attempt_id": "codeql-swift-common108-attempt-01-series-01",
        "maximum_attempts": 2, "automatic_retry": False,
        "expected_final_selected_groups": 83,
        "expected_final_partitions": 87,
        "expected_final_rows": 4144,
        "terminal_outcomes": {
            "success": {"status": "completed", "selected_groups": 83,
                         "partitions": 87, "rows": 4144},
            "failure": {"statuses": ["failed", "timed-out", "capacity-lost", "recorder-error"],
                         "selected_groups": 82, "partitions": 82, "rows": 4036,
                         "automatic_retry": False},
        },
        "query_receipt": {"path": QUERY_RECEIPT, "sha256": QUERY_RECEIPT_SHA},
    }
    groups = value["groups"]
    codeql = next(g for g in groups if g.get("id") == CODEQL_GROUP)
    codeql["environment"] = dict(codeql["environment"])
    codeql["environment"]["__CF_USER_TEXT_ENCODING"] = CF_USER_TEXT_ENCODING
    base_inputs = list(value.get("source_inputs", []))
    by_path = {item.get("path"): item for item in base_inputs}
    for item in source_refs:
        old = by_path.get(item["path"])
        require(old is None or old.get("sha256") == item["sha256"],
                f"source closure conflicts with frozen input: {item['path']}")
        by_path[item["path"]] = {"path": item["path"], "role": "release-input", "sha256": item["sha256"]}
    value["source_inputs"] = [by_path[path] for path in sorted(by_path)]
    return value


def validate_draft(root: Path, value: dict[str, Any], source_commit: str) -> None:
    base = _base(root)
    require(value.get("source_commit") == source_commit and value.get("total_wall_budget_seconds") is None,
            "draft contract source or no-expiry clock differs")
    require(value.get("resource_guards", {}).get("working_set_gib") == 30 and
            value.get("resource_guards", {}).get("stop_free_gib") == 48,
            "draft contract aggregate guard differs")
    require(value.get("execution_window", {}).get("phase_remaining_reserved_seconds") == 28032,
            "draft contract CodeQL phase reserve differs")
    require(value.get("breadth_first_authorization") == {
        "path": BREADTH_AUTH, "sha256": BREADTH_AUTH_SHA,
    }, "draft contract breadth authorization differs")
    require(value.get("independent_codeql_scope", {}).get("tail_rows_allowed") == 1,
            "draft contract admits more than one CodeQL tail")
    require(value.get("independent_codeql_scope", {}).get("terminal_outcomes", {}).get("failure", {}).get(
        "automatic_retry") is False,
            "draft contract does not bind the terminal-failure handoff")
    old_groups = {g["id"]: g for g in base["groups"]}
    new_groups = {g["id"]: g for g in value["groups"]}
    require(set(old_groups) == set(new_groups) and len(new_groups) == 84,
            "draft contract changed the fixed group roster")
    for group_id, old in old_groups.items():
        new = new_groups[group_id]
        if group_id != CODEQL_GROUP:
            require(new == old, f"draft changed non-CodeQL group: {group_id}")
        else:
            old_without_environment = copy.deepcopy(old)
            new_without_environment = copy.deepcopy(new)
            old_without_environment.pop("environment", None)
            new_without_environment.pop("environment", None)
            require(new_without_environment == old_without_environment and
                    new.get("maximum_attempts") == 2 and
                    new.get("environment", {}).get("__CF_USER_TEXT_ENCODING") == CF_USER_TEXT_ENCODING,
                    "draft changed the frozen CodeQL runtime")
    require(set(value) - set(base) <= {
        "source_commit", "source_inputs", "total_wall_budget_seconds", "resource_guards",
        "execution_window", "aggregate_source_working_cap", "independent_codeql_scope",
        "breadth_first_authorization",
    }, "draft added an unreviewed top-level contract field")
    base_inputs = {item["path"]: item["sha256"] for item in base["source_inputs"]}
    new_inputs = {item["path"]: item["sha256"] for item in value["source_inputs"]}
    require(all(new_inputs.get(path) == digest for path, digest in base_inputs.items()),
            "draft dropped or changed a frozen source input")
    require(SEALED_LEDGER not in {"reports/releases/v0.9.2/ledger-v1.jsonl"},
            "mutable live ledger may not be used as a source input")


def build(root: Path, source_commit: str, plan_commit: str, output: str) -> dict[str, str]:
    verify_exact_commit(root, source_commit, "source commit")
    verify_exact_commit(root, plan_commit, "plan commit")
    refs = source_closure(root)
    verify_commit_contains(root, source_commit, refs, "source commit")
    value = draft_contract(root, source_commit, refs)
    validate_draft(root, value, source_commit)
    raw = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode() + b"\n"
    out = _path(root, output)
    require(not out.exists() and not out.is_symlink(), "refusing to overwrite contract output")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    # The contract is committed separately. This builder only proves that the
    # supplied plan commit is an exact repository commit; it never creates it.
    return {"path": output, "sha256": sha_bytes(raw), "source_commit": source_commit,
            "plan_commit": plan_commit, "source_inputs": len(value["source_inputs"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--plan-commit", required=True)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(ROOT, args.source_commit, args.plan_commit, args.output), sort_keys=True))
        return 0
    except (CodeQLBuildError, OSError, subprocess.SubprocessError) as exc:
        print(f"CodeQL contract rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
