#!/usr/bin/env python3
"""Bounded, append-only Bifrost v0.14.0 continuation.

This adapter is deliberately independent of replacement-04.  It consumes a
finalized manifest which names the already qualified 89-row continuation
prefix, the exact replacement contract, and every source/plan/proof binding.
It never invents a source commit, runner, contract, admission receipt, or
resource value.  The frozen release executor/checker remain the execution and
replay authorities; this module only supplies the three exact contexts needed
to keep the historical, Swift continuation, and Bifrost rows separate.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Iterator, Sequence


ROOT = Path(__file__).resolve().parents[4]
LEDGER = "reports/releases/v0.9.2/ledger-v1.jsonl"
BASE_CONTRACT = "reports/releases/v0.9.2/execution-v4/contract.json"
BASE_CONTRACT_SHA = "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb"
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
BASE_SOURCE_COMMIT = "0f105a6f4bd6a954fd09cb222e8a519162393aec"
ORIGIN = "2026-10-20T00:57:00.680937+00:00"
CUTOFF = "2026-10-23T21:33:00.680937+00:00"
TOTAL_WALL_SECONDS = 333360

JOERN_GROUP = "joern-swift-common108"
CODEQL_GROUP = "codeql-swift-common108"
JOERN_ATTEMPT = "joern-swift-common108-attempt-04-series-01"
CODEQL_ATTEMPT = "codeql-swift-common108-attempt-01-series-01"
ORIGINAL_ROWS = 89
HISTORICAL_ROWS = 87
ORIGINAL_SELECTED = 84
ORIGINAL_PARTITIONS = 92
ORIGINAL_REPORT_ROWS = 4252

# These are immutable predecessor artifacts.  The 87-row predecessor is
# already sealed; replacement-05's 89-row continuation prefix is written by
# the reviewed Joern04/CodeQL01 continuation builder at this exact path.  A
# manifest may bind the bytes at this path, but may not select another path.
ORIGINAL_PREFIX_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "sealed-ledger-prefix-87.jsonl"
)
ORIGINAL_PREFIX_SHA256 = "57d8265e8eb0c216c56e184a5fed36f9931bcb5b36ea1047ae3f4a0c71f0a096"
CONTINUATION_PREFIX_PATH = (
    "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-05/"
    "ledger-prefix-89.jsonl"
)

VERSION = "bifrost 0.14.0"
BUILD = "c11a13ffa03ebea154f587b899954e412b5b871e"
BINARY_SHA = "fc9a2a4cff4e73b91a1b4e15f403bf572052bc796a362440e347336be46385e6"
BINARY_BYTES = 641365456
PUBLIC_TAG_COMMIT = "0d713d9a1582e9e6fdef75f3b27027409bd7ec19"

CONTINUATION_MODULE = "reports/releases/v0.9.2/acquisition/joern-capability-continuation-03.py"
DEFAULT_MANIFEST = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-05/manifest.json"
SCHEMA = "v092-bifrost-v0140-replacement-05/v1"
REPLACEMENT_SCHEMA = "v092-bifrost-v0140-replacement-05-contract/v1"
PHASE_GATE_SCHEMA = "v092-bifrost-v0140-phase-gate/v1"
ADMISSION_SOURCE_REF = {
    "path": "reports/releases/v0.9.2/acquisition/joern-capability-admission-05.py",
    "sha256": "85dd72ab1c17371f927db19352da675876a3ac8dcb5e9cde8365ef153ab21e14",
}
SUPERVISOR_SOURCE_REF = {
    "path": "reports/releases/v0.9.2/acquisition/matrix-supervision-26.py",
    "sha256": "2733e9cb858053d0ac71a489c891f393b083a928e96399679650121e35922047",
}
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
ATTEMPT_RE = re.compile(r"^.+-attempt-(\d+)-series-(\d+)$")

FROZEN = {
    "executor": {"path": "scripts/execute-release-v092.py",
                  "sha256": "fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8"},
    "checker": {"path": "scripts/check-release-v092.py",
                 "sha256": "0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928"},
    "configuration": {"path": "scripts/validate-v092-report-configurations.py",
                       "sha256": "21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858"},
}
SOURCE_DIFF_SCOPE = (
    "src", "cases", "populations", "adapters", "schemas", "scripts",
    "Cargo.toml", "Cargo.lock", "docs/v0.9.2-execution.md", "corpus",
    "README.md", "LICENSE", "docs/adapters.md", "reports/releases/v0.9.0/plan.json",
    "docs/benchmark-sources.md", "docs/challenge-tier.md",
    "docs/real-project-preregistration.md", "docs/real-project-r2-preregistration.md",
    "docs/real-project-review.md",
)

# These values are reviewed release inputs.  A finalized replacement manifest
# may only point at these bytes and floors; it cannot lower them by making a
# self-consistent receipt of its own.
QUALIFICATION_REF = {
    "path": "reports/releases/v0.9.2/qualification/bifrost-v0140-01/qualification.json",
    "sha256": "c7c3e4761619716ea653da47b41ebfb0f62b284a64ef55d9a316e14828726190",
}
CONTROL_REVIEW_REF = {
    "path": "reports/releases/v0.9.2/qualification/bifrost-v0140-01/control-review-01.json",
    "sha256": "ca73ca5ad53d74c4521b68b3395da7297747c0ff8c3e22230a1594243d642a5f",
}
QUALIFICATION_LIMITS = (
    "Three JavaScript policy controls remain inconclusive with partial discovery.",
    "Unbound endpoint controls are not evidence of cleanliness.",
    "The empty shipped native catalog remains not evaluated.",
    "Strict schema-5 qualification failed and remains preserved.",
    "Control eligibility is separate from completed release-group execution.",
)
RESOURCE_POLICY = {
    "minimum_free_gib": 127,
    "minimum_remaining_reserve_seconds": 29400,
    "minimum_replacement_seconds": 13592,
    "startup_seconds": 600,
}


class Replacement05Error(ValueError):
    """A replacement input failed closed validation."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise Replacement05Error(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def relative(value: object, description: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{description} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts),
            f"{description} is unsafe")
    return path


def read(root: Path, value: str) -> bytes:
    current = Path(root)
    for part in relative(value).parts:
        current /= part
        require(not current.is_symlink(), f"symlink in bound path: {value}")
    require(current.is_file(), f"missing bound file: {value}")
    return current.read_bytes()


def bound(root: Path, ref: object, description: str = "file") -> bytes:
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            f"{description} must be an exact path/SHA binding")
    require(isinstance(ref["sha256"], str) and SHA_RE.fullmatch(ref["sha256"]),
            f"{description} SHA is malformed")
    raw = read(root, ref["path"])
    require(sha(raw) == ref["sha256"], f"{description} bytes changed: {ref['path']}")
    return raw


def _json(raw: bytes, description: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Replacement05Error(f"{description} is not valid JSON") from exc
    require(isinstance(value, dict), f"{description} must be an object")
    return value


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True,
                                       stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Replacement05Error(f"git command failed: git {' '.join(args)}") from exc


def _git_show(root: Path, commit: str, path: str) -> bytes:
    relative(path, "git path")
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root,
                                       stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Replacement05Error(f"{commit} lacks {path}") from exc


def _ancestor(root: Path, ancestor: str, descendant: str, description: str) -> None:
    require(COMMIT_RE.fullmatch(str(ancestor)) and COMMIT_RE.fullmatch(str(descendant)),
            f"{description} must use exact commits")
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                       cwd=root, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Replacement05Error(f"{description} is not an ancestor") from exc


def _load_frozen(root: Path, name: str) -> Any:
    ref = FROZEN[name]
    raw = read(root, ref["path"])
    require(sha(raw) == ref["sha256"], f"frozen dependency changed: {name}")
    spec = importlib.util.spec_from_file_location("replacement05_" + name, root / ref["path"])
    require(spec is not None and spec.loader is not None, f"cannot import frozen {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rows(raw: bytes) -> list[dict[str, Any]]:
    require(not raw or raw.endswith(b"\n"), "ledger must end with newline")
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines(keepends=True):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Replacement05Error("ledger contains invalid JSON") from exc
        require(isinstance(value, dict), "ledger rows must be objects")
        require(line == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(),
                "ledger row is not canonical JSON")
        rows.append(value)
    attempts = [row.get("attempt_id") for row in rows]
    require(all(isinstance(value, str) and value for value in attempts),
            "ledger attempt identity is missing")
    require(len(set(attempts)) == len(attempts), "duplicate attempt identity")
    return rows


def replacement_ids(plan: dict[str, Any]) -> list[str]:
    groups = plan.get("groups")
    require(isinstance(groups, list), "plan groups are missing")
    ids = [group.get("id") for group in groups if group.get("tool") == "bifrost"]
    require(len(ids) == 20 and all(isinstance(value, str) for value in ids),
            "plan must contain exactly20 Bifrost groups")
    return ids


def validate_prefix(prefix_raw: bytes, *, prefix_sha: str, continuation_sha: str,
                    continuation_source: str, continuation_plan: str) -> list[dict[str, Any]]:
    require(SHA_RE.fullmatch(prefix_sha) and sha(prefix_raw) == prefix_sha,
            "sealed 89-row prefix digest changed")
    rows = canonical_rows(prefix_raw)
    require(len(rows) == ORIGINAL_ROWS, "sealed prefix must contain exactly89 rows")
    require(sum(row.get("status") == "completed" for row in rows) == ORIGINAL_SELECTED,
            "sealed prefix completion count is not84")
    require(sum(row.get("status") == "completed" and row.get("tool") != "bifrost"
                for row in rows) == 64,
            "sealed prefix must retain64 non-Bifrost completions")
    for row in rows[:HISTORICAL_ROWS]:
        # The retained C2/C3 history intentionally contains mixed contract,
        # source, and plan identities.  The exact per-row context is recovered
        # from the continuation implementation; only the execution series and
        # absence of the new continuation contract are checked here.
        require(row.get("execution_series") == 1 and
                row.get("contract_sha256") != continuation_sha,
                "historical prefix row changed its original execution series")
    joern, codeql = rows[-2:]
    require(joern.get("group_id") == JOERN_GROUP and joern.get("attempt_id") == JOERN_ATTEMPT,
            "prefix does not end with the reviewed Joern04 repair")
    require(codeql.get("group_id") == CODEQL_GROUP and codeql.get("attempt_id") == CODEQL_ATTEMPT,
            "CodeQL01 does not follow Joern04")
    for row, label in ((joern, "Joern04"), (codeql, "CodeQL01")):
        require(row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("timed_out") is False and row.get("capacity_loss") is None,
                f"{label} is not successful")
        require(row.get("execution_series") == 1 and row.get("contract_sha256") == continuation_sha and
                row.get("source_commit") == continuation_source and
                row.get("plan_commit") == continuation_plan,
                f"{label} is not bound to the continuation context")
    return rows


def _validate_original_prefix(root: Path, manifest: dict[str, Any], prefix_raw: bytes) -> bytes:
    """Bind the mutable ledger to a separately sealed historical artifact.

    The live ledger is allowed to grow after the continuation.  Its predecessor
    must therefore be represented by immutable bytes in the manifest rather
    than being reconstructed from whatever happens to be on disk at validation
    time.
    """
    ref = manifest.get("original_prefix")
    require(ref == {"path": ORIGINAL_PREFIX_PATH, "rows": HISTORICAL_ROWS,
                    "sha256": ORIGINAL_PREFIX_SHA256},
            "original_prefix must bind the exact sealed 87-row predecessor")
    original = bound(root, ref, "sealed original ledger predecessor")
    require(sha(original) == ORIGINAL_PREFIX_SHA256,
            "sealed original predecessor digest differs")
    require(len(canonical_rows(original)) == HISTORICAL_ROWS,
            "sealed original predecessor has the wrong row count")
    expected = b"".join(prefix_raw.splitlines(keepends=True)[:HISTORICAL_ROWS])
    require(original == expected,
            "replacement prefix does not begin with the exact sealed predecessor bytes")
    return original


def _attempt_number(attempt_id: str) -> int:
    match = ATTEMPT_RE.fullmatch(attempt_id)
    require(match is not None, f"malformed attempt id: {attempt_id}")
    return int(match.group(1))


def accounting(prefix: list[dict[str, Any]], rows: list[dict[str, Any]],
               replacement_groups: list[str], contract_sha: str,
               source_commit: str | None = None, plan_commit: str | None = None) -> set[str]:
    """Allow exactly one series-02 row per reviewed Bifrost group, in order."""
    require(len(prefix) == ORIGINAL_ROWS and rows[:len(prefix)] == prefix,
            "historical 89-row prefix changed")
    require(len(replacement_groups) == 20 and len(set(replacement_groups)) == 20,
            "exactly20 replacement groups required")
    counts = collections.Counter(row.get("group_id") for row in prefix)
    require(all(counts[group] == (2 if group == "bifrost-c-kernel" else 1)
                for group in replacement_groups), "historical Bifrost counters changed")
    seen: set[str] = set()
    tail = rows[len(prefix):]
    require(len(tail) <= len(replacement_groups), "replacement tail has too many rows")
    for index, row in enumerate(tail):
        group = replacement_groups[index]
        require(row.get("group_id") == group and group not in seen,
                "replacement order or group identity changed")
        require(row.get("contract_sha256") == contract_sha and
                row.get("execution_series") == 2 and row.get("tool") == "bifrost",
                "replacement row has an unregistered contract context")
        if source_commit is not None:
            require(row.get("source_commit") == source_commit, "replacement source context changed")
        if plan_commit is not None:
            require(row.get("plan_commit") == plan_commit, "replacement plan context changed")
        expected_number = counts[group] + 1
        require(row.get("attempt_id") == f"{group}-attempt-{expected_number:02d}-series-02" and
                _attempt_number(row["attempt_id"]) == expected_number and
                row.get("tool_binding", {}).get("report_version") == VERSION,
                "replacement attempt number or version binding changed")
        seen.add(group)
    return seen


def select_final(prefix: list[dict[str, Any]], rows: list[dict[str, Any]],
                 replacement_groups: list[str], contract_sha: str,
                 source_commit: str | None = None, plan_commit: str | None = None
                 ) -> dict[str, dict[str, Any]]:
    require(accounting(prefix, rows, replacement_groups, contract_sha, source_commit, plan_commit)
            == set(replacement_groups), "replacement matrix is incomplete")
    selected: dict[str, dict[str, Any]] = {}
    for row in prefix:
        if row.get("status") == "completed" and row.get("tool") != "bifrost":
            require(row["group_id"] not in selected, "duplicate retained completion")
            selected[row["group_id"]] = row
    # The two continuation rows are non-Bifrost; all historical Bifrost rows
    # are deliberately superseded by the series-02 tail.
    require(len(selected) == 64, "prefix must contain64 selected non-Bifrost groups")
    for row in rows[len(prefix):]:
        require(row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("timed_out") is False and row.get("capacity_loss") is None,
                "replacement failed or incomplete")
        selected[row["group_id"]] = row
    require(len(selected) == ORIGINAL_SELECTED, "selected set must contain84 groups")
    return selected


def final_selected(prefix: list[dict[str, Any]], rows: list[dict[str, Any]],
                   replacement_groups: list[str], contract_sha: str,
                   source_commit: str | None = None, plan_commit: str | None = None
                   ) -> dict[str, dict[str, Any]]:
    accounting(prefix, rows, replacement_groups, contract_sha, source_commit, plan_commit)
    selected: dict[str, dict[str, Any]] = {}
    for row in prefix:
        if row.get("status") == "completed" and row.get("tool") != "bifrost":
            # The final continuation projection retains the original 64
            # non-Bifrost groups and the two continuation groups.
            selected[row["group_id"]] = row
    require(len(selected) == 64, "prefix selected set must contain64 non-Bifrost groups")
    # In the release benchmark, 20 Bifrost groups replace their historical
    # completions.  No old Bifrost row may survive selection.
    for row in rows[len(prefix):]:
        require(row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("timed_out") is False and row.get("capacity_loss") is None,
                "replacement failed or incomplete")
        selected[row["group_id"]] = row
    require(len(selected) == ORIGINAL_SELECTED, "final selection must contain84 groups")
    return selected


def configuration_contexts(selected: dict[str, dict[str, Any]],
                           contexts: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = collections.defaultdict(list)
    for row in selected.values():
        key = row.get("contract_sha256")
        origin = contexts.get(key)
        require(origin is not None, "selected row has unknown source context")
        require(row.get("source_commit") == origin["source_commit"] and
                row.get("plan_commit") == origin["plan_commit"],
                "selected row source/plan context mismatch")
        buckets[key].append(row["attempt_id"])
    return dict(buckets)


def _iter_diffs(old: Any, new: Any, path: str = "") -> Iterator[str]:
    if type(old) is not type(new):
        yield path or "$"
    elif isinstance(old, dict):
        for key in sorted(set(old) | set(new)):
            child = f"{path}.{key}" if path else key
            if key not in old or key not in new:
                yield child
            else:
                yield from _iter_diffs(old[key], new[key], child)
    elif isinstance(old, list):
        if len(old) != len(new):
            yield path
        else:
            for index, (a, b) in enumerate(zip(old, new)):
                yield from _iter_diffs(a, b, f"{path}[{index}]")
    elif old != new:
        yield path


def _source_delta(root: Path, design: dict[str, Any], manifest: dict[str, Any],
                  baseline: str, target: str) -> dict[str, Any]:
    """Validate complete source provenance against the fixed approved scope."""
    require(design.get("baseline_source_commit") == baseline and
            design.get("target_source_commit") == target,
            "source design baseline/target does not bind continuation and replacement commits")
    patch_files = design.get("patch_files")
    require(isinstance(patch_files, list) and patch_files, "source design patch_files is missing")
    allowed: dict[str, str] = {}
    for item in patch_files:
        require(isinstance(item, dict) and isinstance(item.get("path"), str) and
                SHA_RE.fullmatch(str(item.get("after_sha256", ""))) and
                (item.get("before_sha256") is None or SHA_RE.fullmatch(str(item.get("before_sha256")))) and
                SHA_RE.fullmatch(str(item.get("unformatted_preparation01_after_sha256", ""))),
                "source design patch entry is malformed")
        relative(item["path"], "source patch path")
        require(item["path"] not in allowed, "source design contains duplicate patch paths")
        allowed[item["path"]] = item["after_sha256"]
    extras = design.get("approved_additive_scripts", [])
    require(isinstance(extras, list), "source design additive scripts is missing")
    for item in extras:
        require(isinstance(item, dict) and isinstance(item.get("path"), str) and
                SHA_RE.fullmatch(str(item.get("after_sha256", ""))) and
                SHA_RE.fullmatch(str(item.get("unformatted_preparation01_after_sha256", ""))),
                "source design additive entry is malformed")
        relative(item["path"], "source additive path")
        require(item["path"].startswith("scripts/"), "additive source path is not a script")
        require(item["path"] not in allowed, "source patch/additive paths overlap")
        allowed[item["path"]] = item["after_sha256"]
    declared = manifest.get("source_delta_paths")
    if declared is not None:
        require(sorted(declared) == sorted(allowed), "manifest source delta differs from design")
    try:
        # First obtain the complete repository diff.  Filtering the git
        # command itself would make an unreviewed path invisible.  The fixed
        # scope below is applied only after the full set is known.
        changed = subprocess.check_output(
            ["git", "diff", "--name-status", "--no-renames", baseline, target],
            cwd=root, text=True,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Replacement05Error("source delta could not be established") from exc
    observed: set[str] = set()
    for line in changed:
        fields = line.split("\t", 1)
        require(len(fields) == 2 and fields[0] in {"A", "M"},
                "source delta contains a deletion, rename, or unsupported status")
        observed.add(fields[1])
    def in_reviewed_scope(path: str) -> bool:
        return any(path == scope or path.startswith(scope.rstrip("/") + "/")
                   for scope in SOURCE_DIFF_SCOPE)
    require(all(in_reviewed_scope(path) for path in observed),
            "source delta contains a path outside the fixed reviewed scope")
    require(observed == set(allowed), "source delta contains an unapproved path")
    unformatted = design.get("unformatted_provenance")
    require(isinstance(unformatted, dict),
            "source design must bind every unformatted provenance witness")
    for item in patch_files + extras:
        path, expected = item["path"], item["after_sha256"]
        before = item.get("before_sha256")
        if before is None:
            try:
                _git_show(root, baseline, path)
            except Replacement05Error:
                pass
            else:
                raise Replacement05Error(f"new source path existed in baseline: {path}")
        else:
            require(sha(_git_show(root, baseline, path)) == before,
                    f"source baseline bytes differ from approved digest: {path}")
        require(sha(_git_show(root, target, path)) == expected,
                f"source bytes differ from approved digest: {path}")
        witness = unformatted.get(path)
        require(isinstance(witness, dict), f"unformatted provenance witness is missing: {path}")
        witness_raw = bound(root, witness, f"unformatted provenance witness: {path}")
        require(sha(witness_raw) == item["unformatted_preparation01_after_sha256"],
                f"unformatted provenance digest differs: {path}")
    return {"baseline": baseline, "target": target, "paths": sorted(allowed),
            "patch_files": sorted(item["path"] for item in patch_files),
            "approved_additive_scripts": sorted(item["path"] for item in extras)}


def _source_inputs(root: Path, executor: Any, inherited: list[dict[str, Any]],
                   plan: dict[str, Any], manifest: dict[str, Any], source_commit: str
                   ) -> dict[str, Any]:
    entries = plan.get("source_inputs")
    require(isinstance(entries, list) and entries, "replacement source_inputs are missing")
    require(all(isinstance(item, dict) and isinstance(item.get("path"), str) and
                SHA_RE.fullmatch(str(item.get("sha256", ""))) and
                set(item) <= {"path", "sha256", "role"}
                for item in entries), "replacement source input shape differs")
    paths = [item["path"] for item in entries]
    require(len(paths) == len(set(paths)), "replacement source_inputs contain duplicate paths")
    require(LEDGER not in paths,
            "replacement source_inputs cannot freeze the mutable live ledger")
    old_by_path = {item["path"]: item for item in inherited}
    new_by_path = {item["path"]: item for item in entries}
    for path, old in old_by_path.items():
        require(new_by_path.get(path) == old,
                f"inherited source input metadata changed: {path}")
    delta = manifest.get("source_inputs_delta")
    require(isinstance(delta, list), "manifest source_inputs_delta is required")
    declared_delta = {item.get("path"): item for item in delta}
    require(len(declared_delta) == len(delta), "duplicate source input delta")
    for path, item in new_by_path.items():
        if path not in old_by_path:
            require(declared_delta.get(path) == item,
                    f"new source input is not explicitly bound: {path}")
    require(set(declared_delta) == set(new_by_path) - set(old_by_path),
            "source input delta is incomplete")
    for item in entries:
        bound(root, {"path": item["path"], "sha256": item["sha256"]},
              "replacement source input")
        try:
            if hasattr(executor, "_source_file"):
                executor._source_file(root, source_commit, item["path"], item["sha256"])
            else:
                require(sha(_git_show(root, source_commit, item["path"])) == item["sha256"],
                        f"source input differs at source commit: {item['path']}")
        except Exception as exc:
            if isinstance(exc, Replacement05Error):
                raise
            raise Replacement05Error(f"source input differs at source commit: {item['path']}") from exc
    runner_sha = plan.get("runner_source_sha256")
    require(isinstance(runner_sha, str) and SHA_RE.fullmatch(runner_sha),
            "replacement runner source hash is missing")
    require(sha(_git_show(root, source_commit, "scripts/execute-release-v092.py")) == runner_sha,
            "runner source differs at replacement source commit")
    snapshot = getattr(executor, "_assert_source_snapshot", None)
    require(callable(snapshot), "frozen executor source snapshot guard is unavailable")
    snapshot(root, source_commit, runner_sha, entries)
    return {"count": len(entries), "inherited": len(old_by_path),
            "added": len(entries) - len(old_by_path), "runner_source_sha256": runner_sha}


def _validate_qualification(root: Path, ref: object, ids: list[str]) -> dict[str, Any]:
    require(ref == QUALIFICATION_REF,
            "Bifrost qualification must bind the exact reviewed v0.14.0 artifact")
    value = _json(bound(root, ref, "Bifrost qualification"), "Bifrost qualification")
    require(value.get("status") == "measurement-with-known-limits" and
            value.get("execution_eligible") is True and
            value.get("full_policy_qualification") is False and
            value.get("groups") == ids,
            "Bifrost qualification is not the exact typed v0.14.0 qualification")
    tool = value.get("tool")
    require(isinstance(tool, dict) and tool.get("version") == "0.14.0" and
            tool.get("build_identity") == BUILD and tool.get("sha256") == BINARY_SHA and
            tool.get("bytes") == BINARY_BYTES and tool.get("public_tag_commit") == PUBLIC_TAG_COMMIT,
            "qualified Bifrost binary identity differs")
    require(tuple(value.get("limits", ())) == QUALIFICATION_LIMITS,
            "typed Bifrost qualification limits differ from the reviewed artifact")
    require(value.get("control_review") == CONTROL_REVIEW_REF,
            "Bifrost control review binding differs from the reviewed artifact")
    review = _json(bound(root, CONTROL_REVIEW_REF, "Bifrost control review"),
                   "Bifrost control review")
    require(review.get("status") in {"approved", "canonical-validation-passed",
                                      "measurement-with-known-limits"},
            "Bifrost control review is not an approved exact-schema receipt")
    return value


def _validate_runner_binding(root: Path, manifest: dict[str, Any], runner: dict[str, Any],
                             contract: dict[str, Any], source_commit: str,
                             expected_executor_environment: dict[str, str]) -> dict[str, Any]:
    """Require a reviewed runner artifact, source identity, and environment."""
    artifact_ref = manifest.get("runner_artifact")
    require(isinstance(artifact_ref, dict), "runner_artifact binding is required")
    artifact = _json(bound(root, artifact_ref, "runner artifact"), "runner artifact")
    require(artifact.get("schema") == "v092-bifrost-runner-artifact/v1" and
            artifact.get("status") == "verified" and
            artifact.get("automatic_retry") is False,
            "runner artifact is not the exact one-shot verified schema")
    require(artifact.get("runner") == runner or artifact.get("identity") == runner,
            "runner artifact identity differs from replacement contract")
    require(artifact.get("source_commit") == source_commit and
            artifact.get("runner_source_sha256") == contract.get("runner_source_sha256"),
            "runner artifact source provenance differs")
    build = artifact.get("build")
    require(isinstance(build, dict) and
            build.get("source_commit") == source_commit and
            build.get("runner_source_sha256") == contract.get("runner_source_sha256"),
            "runner artifact build provenance is incomplete")
    environment = artifact.get("environment")
    require(isinstance(environment, dict) and environment == manifest.get("runner_environment"),
            "runner invocation environment is not the reviewed exact environment")
    require(environment.get("BIFROST_OPEN_PACKS_DISABLE") == "1" and
            environment.get("PYTHONDONTWRITEBYTECODE") == "1",
            "runner environment omits required deterministic controls")
    executor_environment = artifact.get("executor_environment")
    require(executor_environment == manifest.get("executor_environment") and
            executor_environment == expected_executor_environment,
            "runner artifact executor environment is not the exact group environment")
    return artifact


def _validate_review_bindings(root: Path, manifest: dict[str, Any], *, module_sha: str,
                              test_sha: str, contract_ref: dict[str, Any],
                              source_design_ref: dict[str, Any], prefix_ref: dict[str, Any],
                              original_prefix_ref: dict[str, Any]) -> None:
    """Require external independent reviews to bind this exact implementation."""
    independent_ref = manifest.get("independent_review")
    final_ref = manifest.get("final_review")
    require(isinstance(independent_ref, dict) and isinstance(final_ref, dict),
            "independent and final review bindings are required")
    for key in ("admission_source", "supervisor_source"):
        source_ref = manifest.get(key)
        require(isinstance(source_ref, dict) and set(source_ref) == {"path", "sha256"},
                f"{key} binding is required")
        bound(root, source_ref, key)
    require(independent_ref != final_ref,
            "independent_review and final_review must be distinct exact artifacts")
    review_types: set[str] = set()
    for field in ("independent_review", "final_review"):
        ref = manifest.get(field)
        require(isinstance(ref, dict) and ref.get("path") != manifest.get("path"),
                f"{field} binding is required and cannot self-reference")
        review = _json(bound(root, ref, field), field)
        require(review.get("status") == "approved" and review.get("automatic_retry") is False,
                f"{field} is not an approved one-shot review")
        bindings = review.get("bindings") or review.get("exact_bindings")
        require(isinstance(bindings, dict), f"{field} bindings are missing")
        expected = {
            "implementation": {"path": Path(__file__).resolve().relative_to(root).as_posix(),
                                "sha256": module_sha},
            "focused_tests": {"path": manifest["implementation_test"]["path"],
                               "sha256": test_sha},
            "replacement_contract": contract_ref,
            "source_design": source_design_ref,
            "ledger_prefix": prefix_ref,
            "original_prefix": original_prefix_ref,
            "source_commit": manifest.get("source_commit"),
            "plan_commit": manifest.get("plan_commit"),
            "runner_artifact": manifest.get("runner_artifact"),
            "runner_environment": manifest.get("runner_environment"),
            "executor_environment": manifest.get("executor_environment"),
            "admission_source": manifest.get("admission_source"),
            "supervisor_source": manifest.get("supervisor_source"),
        }
        aliases = {
            "implementation": ("implementation", "implementation_sha256"),
            "focused_tests": ("focused_tests", "test", "test_sha256"),
            "replacement_contract": ("replacement_contract", "contract", "contract_sha256"),
            "source_design": ("source_design", "source_design_sha256"),
            "ledger_prefix": ("ledger_prefix", "original_prefix", "ledger_prefix_sha256"),
            "original_prefix": ("original_prefix", "original_prefix_sha256"),
            "source_commit": ("source_commit",),
            "plan_commit": ("plan_commit",),
            "runner_artifact": ("runner_artifact", "runner_artifact_sha256"),
            "runner_environment": ("runner_environment", "environment"),
            "executor_environment": ("executor_environment",),
            "admission_source": ("admission_source", "admission_source_sha256"),
            "supervisor_source": ("supervisor_source", "supervisor_source_sha256"),
        }
        def equivalent(actual: object, wanted: object) -> bool:
            if isinstance(wanted, dict):
                return actual == wanted or actual == wanted.get("sha256")
            return actual == wanted
        for key, wanted in expected.items():
            actual = next((bindings[name] for name in aliases[key] if name in bindings), None)
            # Process identity and typed source bindings must remain complete
            # path+digest objects.  A digest-only alias is insufficient for
            # helper/supervisor provenance and executor-environment identity.
            exact_object = key in {"admission_source", "supervisor_source", "executor_environment"}
            require(actual is not None and
                    (actual == wanted if exact_object else equivalent(actual, wanted)),
                    f"{field} lacks exact {key} binding")
        review_type = review.get("review_type")
        require(isinstance(review_type, str) and "bifrost" in review_type.lower() and
                "replacement" in review_type.lower(),
                f"{field} review type is not a Bifrost replacement review")
        review_types.add(review_type)
    require(len(review_types) == 2,
            "independent and final reviews must have distinct review types")


def _check_continuation_proof(root: Path, continuation: dict[str, Any], *, prefix_ref: dict[str, Any],
                              original_prefix_ref: dict[str, Any],
                              module_ref: dict[str, Any], contract_ref: dict[str, Any],
                              manifest_ref: dict[str, Any], source_commit: str,
                              plan_commit: str) -> dict[str, Any]:
    proof = continuation.get("proof") if isinstance(continuation.get("proof"), dict) else continuation
    final_ref = proof.get("final_check") or proof.get("final")
    config_ref = proof.get("configuration") or proof.get("config")
    require(isinstance(final_ref, dict) and isinstance(config_ref, dict),
            "continuation final/configuration proof bindings are required")
    final = _json(bound(root, final_ref, "continuation final check"), "continuation final check")
    config = _json(bound(root, config_ref, "continuation configuration receipt"), "continuation configuration receipt")
    require(final.get("status") == "fresh-evidence-verified" and
            final.get("automatic_retry") is False,
            "continuation final proof is not a fresh one-shot verification")
    require(config.get("status") == "canonical-validation-passed" and
            config.get("automatic_retry") is False,
            "continuation configuration proof did not pass")
    require(final.get("ledger_rows") == ORIGINAL_ROWS and final.get("selected_groups") == ORIGINAL_SELECTED and
            final.get("partitions") == ORIGINAL_PARTITIONS and final.get("rows") == ORIGINAL_REPORT_ROWS and
            final.get("known_stale") == 0,
            "continuation final proof denominator differs")
    require(config.get("partitions") == ORIGINAL_PARTITIONS and config.get("rows") == ORIGINAL_REPORT_ROWS and
            config.get("known_stale") == 0,
            "continuation configuration denominator differs")
    expected = {"module": module_ref, "contract": contract_ref,
                "source_commit": source_commit, "plan_commit": plan_commit,
                "ledger_prefix": prefix_ref, "original_prefix": original_prefix_ref}
    for receipt, label in ((final, "final"), (config, "configuration")):
        bindings = receipt.get("bindings") or receipt.get("continuation") or {}
        require(isinstance(bindings, dict), f"continuation {label} proof bindings are missing")
        for key, value in expected.items():
            actual = bindings.get(key)
            if isinstance(value, dict):
                require(actual == value, f"continuation {label} proof binding differs: {key}")
            else:
                require(actual == value, f"continuation {label} proof binding differs: {key}")
        require(receipt.get("implementation") == module_ref or
                receipt.get("module") == module_ref,
                f"continuation {label} proof omits its implementation identity")
        require(receipt.get("manifest") == manifest_ref or
                receipt.get("manifest_sha256") == manifest_ref["sha256"],
                f"continuation {label} proof omits its manifest identity")
        require(receipt.get("contract") == contract_ref or
                receipt.get("contract_sha256") == contract_ref["sha256"],
                f"continuation {label} proof omits its contract identity")
        require(receipt.get("source_commit") == source_commit and
                receipt.get("plan_commit") == plan_commit,
                f"continuation {label} proof omits its source/plan identities")
    return {"final": final, "configuration": config,
            "final_sha256": sha(bound(root, final_ref)), "configuration_sha256": sha(bound(root, config_ref))}


def _load_continuation(root: Path, m: dict[str, Any], prefix_ref: dict[str, Any],
                       original_prefix_ref: dict[str, Any]) -> dict[str, Any]:
    c = m.get("continuation")
    require(isinstance(c, dict), "continuation binding is missing")
    module_ref = c.get("module")
    manifest_ref = c.get("manifest")
    contract_ref = c.get("contract")
    require(isinstance(module_ref, dict) and module_ref.get("path") == CONTINUATION_MODULE,
            "continuation module binding is missing or unregistered")
    require(isinstance(manifest_ref, dict) and isinstance(contract_ref, dict),
            "continuation manifest/contract bindings are missing")
    module_raw = bound(root, module_ref, "continuation module")
    continuation_manifest = _json(bound(root, manifest_ref, "continuation manifest"), "continuation manifest")
    contract_raw = bound(root, contract_ref, "continuation contract")
    continuation_plan = _json(contract_raw, "continuation contract")
    source = c.get("source_commit", continuation_manifest.get("source_commit"))
    plan = c.get("plan_commit", continuation_manifest.get("plan_commit"))
    require(COMMIT_RE.fullmatch(str(source)) and COMMIT_RE.fullmatch(str(plan)) and
            continuation_plan.get("source_commit") == source,
            "continuation source/plan binding is missing")
    require(continuation_manifest.get("finalized") is True and
            continuation_manifest.get("source_commit") == source and
            continuation_manifest.get("plan_commit") == plan and
            continuation_manifest.get("continuation_contract") == contract_ref,
            "continuation manifest does not bind its exact contract/source/plan")
    historical_prefix_ref = continuation_manifest.get("ledger_prefix")
    require(isinstance(historical_prefix_ref, dict) and historical_prefix_ref.get("rows") == HISTORICAL_ROWS,
            "continuation manifest must retain the exact 87-row historical prefix")
    historical_prefix_raw = bound(root, historical_prefix_ref, "historical 87-row prefix")
    require(historical_prefix_raw == b"".join(
        bound(root, m["ledger_prefix"], "89-row ledger prefix").splitlines(keepends=True)[:HISTORICAL_ROWS]
    ), "continuation historical prefix differs from the replacement prefix")
    artifacts = continuation_manifest.get("artifacts", {})
    if isinstance(artifacts, dict) and isinstance(artifacts.get("continuation_source"), dict):
        require(artifacts["continuation_source"] == module_ref,
                "continuation artifact source binding differs")
    proof = _check_continuation_proof(root, c, prefix_ref=prefix_ref,
                                      original_prefix_ref=original_prefix_ref,
                                      module_ref=module_ref, contract_ref=contract_ref,
                                      manifest_ref=manifest_ref,
                                      source_commit=source, plan_commit=plan)
    # The source bytes and contract bytes must be committed at their declared
    # plan head.  This is a read-only ancestry check, never a materialization.
    _ancestor(root, BASE_SOURCE_COMMIT, source, "base source to continuation source")
    _ancestor(root, source, plan, "continuation source to continuation plan")
    require(_git_show(root, plan, contract_ref["path"]) == contract_raw,
            "continuation contract differs from its plan commit")
    # Invoke the exact continuation implementation after all cheap binding
    # checks.  Its returned contexts carry frozen normalized groups and
    # historical role metadata; a raw contract copy is only a test fallback.
    continuation_context = None
    continuation_module = None
    # Once Bifrost rows have been appended, the continuation module's own
    # sealed-tail parser intentionally rejects a ledger longer than its two
    # rows.  The proof above is already bound, so later per-group invocations
    # use the exact raw contract contexts below while the initial 89-row
    # preflight invokes the implementation itself.
    invoke_continuation = True
    try:
        live_count = len(canonical_rows(read(root, LEDGER)))
        invoke_continuation = live_count <= ORIGINAL_ROWS
    except Replacement05Error:
        invoke_continuation = True
    if invoke_continuation:
        try:
            spec = importlib.util.spec_from_file_location("replacement05_continuation", root / module_ref["path"])
            require(spec is not None and spec.loader is not None, "cannot import continuation module")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            continuation_module = module
            validate_fn = getattr(module, "validate", None)
            require(callable(validate_fn), "continuation module has no validate API")
            continuation_context = validate_fn(root, manifest_ref["path"], manifest_ref["sha256"],
                                               require_admission=False)
        except Replacement05Error:
            raise
        except Exception as exc:
            raise Replacement05Error("continuation implementation validation failed") from exc
    if continuation_module is None:
        try:
            spec = importlib.util.spec_from_file_location("replacement05_continuation", root / module_ref["path"])
            require(spec is not None and spec.loader is not None, "cannot import continuation module")
            continuation_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(continuation_module)
        except Replacement05Error:
            raise
        except Exception as exc:
            raise Replacement05Error("continuation implementation import failed") from exc
    return {"binding": c, "module_raw": module_raw, "module_ref": module_ref,
            "manifest": continuation_manifest, "contract": continuation_plan,
            "contract_raw": contract_raw, "contract_ref": contract_ref,
            "source_commit": source, "plan_commit": plan, "proof": proof,
            "validated_context": continuation_context,
            "validated": (continuation_context.get("repaired", {}).get("validated")
                           if isinstance(continuation_context, dict) else None),
            "base_validated": (continuation_context.get("base", {}).get("validated")
                                if isinstance(continuation_context, dict) else None),
            "module": continuation_module}


def _contract_delta(inherited: dict[str, Any], replacement: dict[str, Any],
                    manifest: dict[str, Any], bifrost_ids: list[str]) -> list[str]:
    """Enforce immutable continuation semantics with a narrow delta allowlist."""
    diffs = list(_iter_diffs(inherited, replacement))
    allowed = {
        "execution_authorized", "execution_series", "replacement_schema", "source_commit",
        "source_inputs", "tools.bifrost", "tools.runner", "qualifications.bifrost",
        "resource_reservation.expires_at_unix_seconds", "resource_recovery",
    }
    # Group changes are only permitted for explicitly identified Bifrost argv,
    # attempt cap, and report tool-version fields.
    immutable_groups: list[dict[str, Any]] = []
    old_groups = {g.get("id"): g for g in inherited.get("groups", [])}
    new_groups = {g.get("id"): g for g in replacement.get("groups", [])}
    require(set(old_groups) == set(new_groups), "group roster changed")
    for group_id in old_groups:
        old, new = old_groups[group_id], new_groups[group_id]
        if group_id not in bifrost_ids:
            require(old == new, f"non-Bifrost group changed: {group_id}")
            continue
        for key in set(old) | set(new):
            if key in {"argv", "maximum_attempts", "reports"}:
                continue
            require(old.get(key) == new.get(key), f"Bifrost group changed forbidden field: {group_id}.{key}")
        old_reports, new_reports = old.get("reports", []), new.get("reports", [])
        require(len(old_reports) == len(new_reports), f"Bifrost report partitions changed: {group_id}")
        for before, after in zip(old_reports, new_reports):
            for key in set(before) | set(after):
                if key != "tool_version":
                    require(before.get(key) == after.get(key),
                            f"Bifrost report changed forbidden field: {group_id}.{key}")
    # Remove group-level changes from the generic diff and check every other
    # diff against the explicit immutable allowlist.
    for path in diffs:
        if path.startswith("groups["):
            continue
        if path in allowed or any(path.startswith(prefix + ".") or path.startswith(prefix + "[")
                                  for prefix in ("tools.bifrost", "tools.runner",
                                                 "qualifications.bifrost", "source_inputs")):
            continue
        if path == "resource_recovery" or path.startswith("resource_recovery."):
            continue
        require(path.startswith("groups[") or path == "resource_reservation.expires_at_unix_seconds",
                f"replacement contract changed forbidden field: {path}")
    if any(path == "resource_recovery" or path.startswith("resource_recovery.") for path in diffs):
        declared = manifest.get("contract_delta", {}).get("resource_recovery")
        require(declared == replacement.get("resource_recovery"),
                "resource_recovery delta is not independently bound")
    require(replacement.get("execution_series") == 2 and replacement.get("execution_authorized") is True and
            replacement.get("replacement_schema") == REPLACEMENT_SCHEMA,
            "replacement series/schema is not exact")
    reservation = replacement.get("resource_reservation")
    old_reservation = inherited.get("resource_reservation")
    require(isinstance(reservation, dict) and isinstance(old_reservation, dict),
            "resource reservation is missing")
    require({k: v for k, v in reservation.items() if k != "expires_at_unix_seconds"} ==
            {k: v for k, v in old_reservation.items() if k != "expires_at_unix_seconds"},
            "resource reservation changed outside expiry")
    require(reservation.get("expires_at_unix_seconds") == dt.datetime.fromisoformat(CUTOFF).timestamp(),
            "replacement reservation expiry is not the reviewed cutoff")
    return diffs


def _validate_replacement_plan(root: Path, executor: Any, contract_ref: dict[str, Any],
                               contract_raw: bytes, contract: dict[str, Any],
                               plan_commit: str) -> dict[str, Any]:
    """Run the frozen validator over the exact replacement contract.

    The returned normalized object is the sole execution context.  Raw
    contract construction is intentionally insufficient because it bypasses
    source-input, qualification, resource, and runner semantics in the frozen
    executor.
    """
    validator = getattr(executor, "validate_plan", None)
    require(callable(validator), "frozen replacement plan validator is unavailable")
    path = root / Path(*relative(contract_ref["path"], "replacement contract").parts)
    try:
        validated = validator(path, repo_root=root)
    except Exception as exc:
        raise Replacement05Error("frozen executor rejected replacement contract") from exc
    require(isinstance(validated, dict), "frozen replacement validator returned no plan")
    require(validated.get("bytes_sha256") == contract_ref["sha256"],
            "frozen replacement validator used different contract bytes")
    normalized = validated.get("plan")
    require(isinstance(normalized, dict), "frozen replacement validator returned no normalized plan")
    # validate_plan returns the contract object under ``plan`` while it also
    # returns normalized tools/groups separately.  Compare the complete plan,
    # rather than a hand-maintained allowlist of fields: otherwise a new
    # resource or provenance field could be normalized differently and escape
    # this continuation's reviewed contract delta.
    require(normalized == contract,
            "frozen normalized replacement plan differs from the complete reviewed contract")
    require(normalized.get("execution_series") == 2 and
            normalized.get("replacement_schema") == REPLACEMENT_SCHEMA,
            "frozen normalized replacement semantics differ")
    require(validated.get("repo_root") == root and
            validated.get("path") == path and
            validated.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "frozen normalized replacement context is not exact")
    return validated


def _replacement_context(base_context: dict[str, Any], continuation: dict[str, Any],
                         contract: dict[str, Any], contract_raw: bytes,
                         contract_ref: dict[str, Any], root: Path, plan_commit: str,
                         frozen_validated: dict[str, Any] | None = None) -> dict[str, Any]:
    value = copy.deepcopy(frozen_validated if frozen_validated is not None else continuation)
    normalized = (frozen_validated or {}).get("plan", contract)
    value.update(path=root / contract_ref["path"], bytes_sha256=sha(contract_raw),
                 repo_root=root, plan=copy.deepcopy(normalized), plan_raw=contract_raw,
                 tools=normalized.get("tools"), source_inputs=normalized.get("source_inputs"),
                 qualification=normalized.get("qualifications"),
                 total_wall_budget_seconds=TOTAL_WALL_SECONDS)
    value["groups"] = copy.deepcopy(
        (frozen_validated or {}).get("groups", contract.get("groups", []))
    )
    return {"validated": value, "plan_commit": plan_commit,
            "source_commit": contract["source_commit"], "role": "replacement"}


def _context_map(base: dict[str, Any], continuation: dict[str, Any], replacement: dict[str, Any],
                 continuation_sha: str, replacement_sha: str, continuation_source: str,
                 continuation_plan: str, replacement_source: str, replacement_plan: str,
                 manifest: dict[str, Any], historical: dict[str, Any] | None = None
                 ) -> dict[str, dict[str, Any]]:
    contexts = {
        BASE_CONTRACT_SHA: {"validated": base, "plan_commit": BASE_PLAN_COMMIT,
                            "source_commit": BASE_SOURCE_COMMIT, "role": "base"},
        continuation_sha: {"validated": continuation, "plan_commit": continuation_plan,
                           "source_commit": continuation_source, "role": "continuation"},
        replacement_sha: replacement,
    }
    # The C4 continuation validator returns the complete mixed C2/C3 source
    # context map.  Preserve every historical contract identity instead of
    # collapsing it into the base context.
    if isinstance(historical, dict):
        for key, item in historical.items():
            if key in {continuation_sha, replacement_sha}:
                continue
            if not isinstance(item, dict) or not isinstance(item.get("validated"), dict):
                continue
            validated = item["validated"]
            plan = validated.get("plan", {})
            source = plan.get("source_commit")
            plan_commit_value = item.get("plan_commit")
            if SHA_RE.fullmatch(str(key)) and COMMIT_RE.fullmatch(str(source)) and COMMIT_RE.fullmatch(str(plan_commit_value)):
                contexts[key] = {"validated": validated, "plan_commit": plan_commit_value,
                                 "source_commit": source, "role": "historical"}
    declared = manifest.get("source_contexts")
    require(isinstance(declared, list) and declared,
            "source_contexts must enumerate every retained context")
    by_contract: dict[str, dict[str, Any]] = {}
    for item in declared:
        require(isinstance(item, dict) and SHA_RE.fullmatch(str(item.get("contract_sha256", ""))) and
                item.get("role") in {"base", "historical", "continuation", "replacement"},
                "source context entry is malformed")
        require(item["contract_sha256"] not in by_contract, "duplicate source context")
        by_contract[item["contract_sha256"]] = item
    expected = {
        key: (value["role"], value["source_commit"], value["plan_commit"])
        for key, value in contexts.items()
    }
    require(set(by_contract) == set(expected), "source context contract roster differs")
    for key, (role, source, plan) in expected.items():
        item = by_contract[key]
        require((item.get("role"), item.get("source_commit"), item.get("plan_commit")) ==
                (role, source, plan), f"source context binding differs for {role}")
    return contexts


def _check_rows_context(rows: list[dict[str, Any]], contexts: dict[str, dict[str, Any]],
                        replacement_sha: str, source_commit: str, plan_commit: str,
                        prefix_len: int) -> None:
    require(len(rows) >= prefix_len, "ledger is shorter than the sealed prefix")
    for row in rows:
        key = row.get("contract_sha256")
        require(key in contexts, "ledger row has no exact source context")
        origin = contexts[key]
        require(row.get("source_commit") == origin["source_commit"] and
                row.get("plan_commit") == origin["plan_commit"],
                "ledger row source/plan context changed")
    for row in rows[prefix_len:]:
        require(row.get("contract_sha256") == replacement_sha and
                row.get("source_commit") == source_commit and row.get("plan_commit") == plan_commit,
                "replacement tail escaped its exact context")


def _validate_admission_evidence(root: Path, ref: object, key: str, *,
                                 expected_source: dict[str, Any] | None = None,
                                 expected_lock_path: str | None = None,
                                 expected_namespace: str | None = None,
                                 expected_attempt: str | None = None) -> dict[str, Any]:
    """Load and validate a non-empty, typed one-shot admission witness.

    A path and digest alone are insufficient: an empty JSON file can otherwise
    masquerade as process ownership, lock, namespace, or helper evidence.
    The exact helper/supervisor bytes are bound by the receipt and manifest;
    this function validates the evidence object's required live-state shape.
    """
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            f"execution admission {key} evidence reference is malformed")
    raw = bound(root, ref, f"execution admission {key}")
    # The helper itself is source code, so its exact bytes are checked by the
    # binding rather than interpreted as JSON.  The separate helper witness
    # below carries the typed live-state receipt.
    if key == "admission_source":
        return {"path": ref["path"], "sha256": sha(raw)}
    value = _json(raw, f"execution admission {key}")
    expected_schema = {
        "process_ownership": "invocation-process-ownership/v1",
        "lock": "exclusive-lock/v1",
        "fresh_namespace": "fresh-sidecar-namespace/v1",
        "helper": "admission-helper/v1",
    }.get(key)
    expected_status = {
        "process_ownership": "verified",
        "lock": "held",
        "fresh_namespace": "fresh",
        "helper": "verified",
    }.get(key)
    require(value.get("schema") == expected_schema,
            f"execution admission {key} evidence schema is not exact")
    require(value.get("status") == expected_status,
            f"execution admission {key} evidence status is not exact")
    require(value.get("automatic_retry") is False,
            f"execution admission {key} evidence permits automatic retry")
    if expected_attempt is not None:
        require(value.get("attempt_id") == expected_attempt,
                f"execution admission {key} evidence attempt identity differs")
    if key == "process_ownership":
        pid = value.get("root_pid", value.get("pid"))
        require(type(pid) is int and pid > 0,
                "execution admission process evidence lacks a positive owner PID")
        tracked = value.get("tracked_processes", value.get("processes"))
        require(isinstance(tracked, list) and tracked,
                "execution admission process evidence lacks tracked processes")
        require(value.get("no_foreign_processes") is True,
                "execution admission process evidence found foreign contenders")
        require(value.get("birth_identity") or value.get("process_birth_identity") or
                all(isinstance(item, dict) and isinstance(item.get("start_identity"), str)
                    and item["start_identity"] for item in tracked),
                "execution admission process evidence lacks birth/contender proof")
    elif key == "lock":
        require(value.get("held") is True or value.get("exclusive_lock_checked") is True,
                "execution admission lock evidence is not exclusive and held")
        require(isinstance(value.get("path"), str) and value["path"],
                "execution admission lock evidence lacks its lock path")
        require(expected_lock_path is not None and value["path"] == expected_lock_path,
                "execution admission lock path is not the reviewed lock")
        require(value.get("owner_pid") is not None or value.get("owner") is not None,
                "execution admission lock evidence lacks an owner")
    elif key == "fresh_namespace":
        namespace = value.get("path", value.get("namespace"))
        require(isinstance(namespace, str) and namespace,
                "execution admission namespace evidence lacks its path")
        require(expected_namespace is not None and namespace == expected_namespace,
                "execution admission namespace path is not the reviewed namespace")
        require(value.get("fresh") is True or value.get("fresh_sidecars") is True,
                "execution admission namespace is not freshly reserved")
        require(value.get("sidecars") is not None or value.get("sidecar_count") == 0,
                "execution admission namespace evidence lacks sidecar state")
    else:
        require(isinstance(value.get("source") or value.get("helper"), dict) or
                isinstance(value.get("path"), str),
                f"execution admission {key} evidence lacks source identity")
        source_identity = value.get("source") or value.get("helper")
        require(expected_source is not None and source_identity == expected_source and
                (value.get("sha256") == ref["sha256"] or
                 value.get("source_sha256") == ref["sha256"] or
                 isinstance(source_identity, dict)),
                f"execution admission {key} evidence does not bind its bytes")
    return value


def _validate_admission(root: Path, ref: object, manifest: dict[str, Any], *,
                        group_id: str | None = None, phase: str = "execution",
                        manifest_sha256: str | None = None) -> dict[str, Any]:
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            "execution admission receipt binding is required")
    value = _json(bound(root, ref, "execution admission receipt"), "execution admission receipt")
    require(value.get("schema") == "v092-bifrost-v0140-replacement-admission/v2" and
            value.get("status") == "ready-to-execute" and value.get("automatic_retry") is False,
            "execution admission is not a one-shot ready receipt")
    require(value.get("original_origin_utc") in {ORIGIN, ORIGIN.replace("+00:00", "Z")} and
            value.get("cutoff_utc") in {CUTOFF, CUTOFF.replace("+00:00", "Z")} and
            value.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "execution admission changes the original clock")
    require(value.get("ledger_prefix") == manifest["ledger_prefix"] and
            value.get("source_commit") == manifest["source_commit"] and
            value.get("plan_commit") == manifest["plan_commit"] and
            value.get("contract_sha256") == manifest["contract"]["sha256"],
            "execution admission is not bound to the exact replacement")
    require(value.get("manifest_path") == manifest.get("_path") and
            (manifest_sha256 is None or value.get("manifest_sha256") == manifest_sha256),
            "execution admission is not bound to this finalized manifest")
    require(value.get("implementation") == manifest.get("implementation") and
            value.get("implementation_test") == manifest.get("implementation_test"),
            "execution admission is not bound to the reviewed implementation")
    if group_id is not None:
        expected_attempt = f"{group_id}-attempt-{3 if group_id == 'bifrost-c-kernel' else 2:02d}-series-02"
        require(value.get("attempt_id") == expected_attempt,
                "execution admission attempt identity differs")
    require(value.get("phase") == phase, "execution admission phase differs")
    expected_group = value.get("group_id", value.get("release_group"))
    if group_id is not None:
        require(expected_group == group_id, "execution admission group identity differs")
    else:
        require((phase == "configuration" and expected_group in {None, "configuration"}) or
                (phase == "execution" and expected_group in {None, "bifrost-v0140-replacement-05"}),
                "admission has an unexpected phase group identity")
    admission_source = manifest.get("admission_source")
    supervisor_source = manifest.get("supervisor_source")
    require(isinstance(admission_source, dict) and isinstance(supervisor_source, dict),
            "manifest must bind exact admission helper and supervisor sources")
    lock_path = manifest.get("lock_path")
    namespace_path = manifest.get("sidecar_namespace")
    require(isinstance(lock_path, str) and lock_path and
            isinstance(namespace_path, str) and namespace_path,
            "manifest must bind the exact lock and sidecar namespace")
    evidence: dict[str, dict[str, Any]] = {}
    for key in ("process_ownership", "lock", "fresh_namespace", "admission_source", "helper"):
        item = value.get(key)
        evidence[key] = _validate_admission_evidence(
            root, item, key,
            expected_source=admission_source if key == "helper" else None,
            expected_lock_path=lock_path if key == "lock" else None,
            expected_namespace=namespace_path if key == "fresh_namespace" else None,
            expected_attempt=value.get("attempt_id") if group_id is not None else None,
        )
    require(value.get("release_group") == "bifrost-v0140-replacement-05",
            "execution admission release identity differs")
    require(value.get("admission_source") == admission_source and
            value.get("supervisor_source") == supervisor_source,
            "execution admission helper/supervisor identity differs")
    require(value.get("admission_source_sha256") == admission_source.get("sha256"),
            "execution admission helper digest differs")
    bound(root, supervisor_source, "execution admission supervisor source")
    policy = manifest.get("resource_policy")
    require(policy == RESOURCE_POLICY and value.get("resource_policy") == RESOURCE_POLICY,
            "resource policy is not the exact reviewed floor")
    require(value.get("resource_policy_sha256") == sha(
        json.dumps(RESOURCE_POLICY, sort_keys=True, separators=(",", ":")).encode()
    ), "execution admission resource policy digest differs")
    reserve = value.get("remaining_reserved_seconds", value.get("phase_remaining_reserved_seconds"))
    if isinstance(reserve, dict):
        amount = reserve.get("bifrost-replacement", reserve.get("replacement", reserve.get("total")))
    else:
        amount = reserve
    require(type(amount) is int and amount >= policy["minimum_remaining_reserve_seconds"],
            "execution admission remaining reserve is below the reviewed floor")
    if group_id is not None:
        require(group_id in set(manifest["replacement_groups"]), "admission requested an unknown group")
    return value


def _runtime_plan(validated: dict[str, Any]) -> dict[str, Any]:
    plan = validated.get("plan")
    require(isinstance(plan, dict) and isinstance(plan.get("resource_reservation"), dict),
            "replacement plan lacks resource reservation")
    value = copy.copy(validated)
    value["plan"] = copy.deepcopy(plan)
    old = plan["resource_reservation"]
    value["plan"]["resource_reservation"]["expires_at_unix_seconds"] = dt.datetime.fromisoformat(CUTOFF).timestamp()
    require(all(value["plan"]["resource_reservation"].get(k) == v for k, v in old.items()
                if k != "expires_at_unix_seconds"), "runtime reservation changed fields beyond expiry")
    return value


def _check_supervisor_dispatch_permit(root: Path, admission: dict[str, Any],
                                      group_id: str) -> None:
    """Check the live supervisor handoff immediately before run_group.

    The permit is deliberately not part of generic admission validation: a
    retained receipt may be replayed or used for configuration after its
    supervisor has exited.  Only the dispatch path consumes this process-
    identity and argv-bound permit.
    """
    require(isinstance(group_id, str) and group_id,
            "supervisor permit group identity is missing")
    expected_attempt = f"{group_id}-attempt-{3 if group_id == 'bifrost-c-kernel' else 2:02d}-series-02"
    require(admission.get("attempt_id") == expected_attempt,
            "supervisor permit admission attempt identity differs")
    ref = admission.get("supervisor_permit")
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            "execution admission supervisor permit binding is required")
    raw = bound(root, ref, "execution admission supervisor permit")
    value = _json(raw, "execution admission supervisor permit")
    require(set(value) == {"pid", "birth", "token", "argv_sha256"},
            "supervisor permit fields are not exact")
    pid = os.getpid()
    require(type(pid) is int and value.get("pid") == pid,
            "supervisor permit PID does not identify this dispatch")
    try:
        birth = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "lstart="], text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Replacement05Error("cannot obtain live supervisor birth witness") from exc
    require(isinstance(birth, str) and birth and value.get("birth") == birth,
            "supervisor permit birth witness is stale or forged")
    require(isinstance(value.get("token"), str) and value["token"],
            "supervisor permit token is missing")
    require(value.get("argv_sha256") == sha(json.dumps(list(sys.argv)).encode()),
            "supervisor permit argv binding does not identify this dispatch")


@contextlib.contextmanager
def _serialized_executor(context: dict[str, Any], group_id: str) -> Iterator[dict[str, Any]]:
    """Hold the frozen executor lock through permit, receipt, and run_group.

    The frozen runner acquires ``executor._exclusive_lock`` itself.  We
    replace that inner acquisition with a no-op while holding the original
    lock here, so the supervisor permit and phase receipt are covered by the
    same lock without recursively opening the lock file.
    """
    executor = context["executor"]
    acquire = getattr(executor, "_exclusive_lock", None)
    require(callable(acquire), "frozen executor exclusive lock is unavailable")
    original = acquire

    @contextlib.contextmanager
    def held_lock() -> Iterator[None]:
        # run_group's own lock boundary is already held by this context.
        yield

    executor._exclusive_lock = held_lock
    try:
        with original():
            live = canonical_rows(read(context["root"], LEDGER))
            seen = accounting(context["prefix"], live, context["ids"],
                              context["contract_sha256"], context["manifest"]["source_commit"],
                              context["manifest"]["plan_commit"])
            remaining = [item["id"] for item in context["validated"]["groups"]
                         if item.get("id") in context["ids"] and item.get("id") not in seen]
            require(remaining and remaining[0] == group_id,
                    "replacement order changed while waiting for the frozen analyzer lock")
            yield _live_gates(context, group_id)
    finally:
        executor._exclusive_lock = original


@contextlib.contextmanager
def _serialized_configuration(context: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Hold the same durable executor lock across each configuration phase."""
    acquire = getattr(context["executor"], "_exclusive_lock", None)
    require(callable(acquire), "frozen executor exclusive lock is unavailable")
    with acquire():
        live = canonical_rows(read(context["root"], LEDGER))
        _check_rows_context(live, context["contexts"], context["contract_sha256"],
                            context["manifest"]["source_commit"],
                            context["manifest"]["plan_commit"], len(context["prefix"]))
        accounting(context["prefix"], live, context["ids"], context["contract_sha256"],
                   context["manifest"]["source_commit"], context["manifest"]["plan_commit"])
        yield _live_gates(context, None, phase="configuration",
                          admission_key="configuration_admission")


@contextlib.contextmanager
def _original_clock(executor: Any, validated: dict[str, Any]) -> Iterator[None]:
    old = getattr(executor, "_matrix_elapsed_wall", None)
    require(callable(old), "frozen executor does not expose original wall-clock guard")
    def elapsed(current: dict[str, Any], *, now_seconds: float | None = None) -> float:
        require(current is validated, "unexpected runtime clock context")
        now = time.time() if now_seconds is None else now_seconds
        value = now - dt.datetime.fromisoformat(ORIGIN).timestamp()
        require(0 <= value <= TOTAL_WALL_SECONDS, "replacement is outside original clock")
        return value
    executor._matrix_elapsed_wall = elapsed
    try:
        yield
    finally:
        executor._matrix_elapsed_wall = old


def _live_gates(context: dict[str, Any], group_id: str | None, *, phase: str = "execution",
                admission_key: str = "execution_admission") -> dict[str, Any]:
    admission = _validate_admission(
        context["root"], context["manifest"].get(admission_key), context["manifest"],
        group_id=group_id, phase=phase, manifest_sha256=context["manifest_sha256"])
    policy = context["manifest"]["resource_policy"]
    remaining = dt.datetime.fromisoformat(CUTOFF).timestamp() - time.time()
    require(remaining >= policy["minimum_remaining_reserve_seconds"],
            "live remaining reserve no longer fits the reviewed cutoff")
    require(remaining >= policy["minimum_replacement_seconds"] + policy["startup_seconds"],
            "live replacement phase reserve no longer fits")
    checker = getattr(context["executor"], "_check_resources", None)
    require(callable(checker), "frozen executor resource gate is unavailable")
    checker(context["root"], policy["minimum_free_gib"] * 1024 ** 3)
    try:
        observed_free_bytes = shutil.disk_usage(context["root"]).free
    except OSError as exc:
        raise Replacement05Error("cannot record live free-space gate result") from exc
    minimum_free_bytes = policy["minimum_free_gib"] * 1024 ** 3
    require(observed_free_bytes >= minimum_free_bytes,
            "recorded live free-space result is below the reviewed floor")
    process_table = getattr(context["executor"], "_process_table", None)
    contenders = getattr(context["executor"], "_contenders", None)
    require(callable(process_table) and callable(contenders),
            "frozen executor contender gate is unavailable")
    table = process_table()
    require(not contenders(table),
            "live admission found a foreign analyzer or release contender")
    namespace = context["manifest"].get("sidecar_namespace")
    require(isinstance(namespace, str), "sidecar_namespace is required for live gates")
    sidecar_root = context["root"] / Path(*relative(namespace, "sidecar namespace").parts)
    namespace_existed = sidecar_root.exists()
    require(not sidecar_root.is_symlink() and
            (not sidecar_root.exists() or sidecar_root.is_dir()),
            "sidecar namespace is not a safe directory")
    fresh_namespace = True
    if group_id is not None and sidecar_root.is_dir():
        # Prior completed groups may leave their receipts.  Only the current
        # attempt namespace must be absent before dispatch.
        prefix = f"{group_id}-attempt-"
        require(not any(path.name.startswith(prefix) for path in sidecar_root.iterdir()),
                "current replacement sidecar namespace is already occupied")
    source_guard = getattr(context["executor"], "_assert_source_snapshot", None)
    require(callable(source_guard), "frozen executor source guard is unavailable")
    source_guard(context["root"], context["manifest"]["source_commit"],
                 context["validated"]["plan"]["runner_source_sha256"],
                 context["validated"]["source_inputs"])
    lock_path = context["manifest"].get("lock_path")
    require(isinstance(lock_path, str) and lock_path,
            "lock_path is required for live gate receipts")
    return {
        "schema": PHASE_GATE_SCHEMA,
        "status": "live-gates-passed",
        "automatic_retry": False,
        "phase": phase,
        "group_id": group_id,
        "attempt_id": admission.get("attempt_id") if group_id is not None else None,
        "admission_key": admission_key,
        "admission": context["manifest"][admission_key],
        "manifest_path": context["manifest"]["_path"],
        "manifest_sha256": context["manifest_sha256"],
        "contract_sha256": context["contract_sha256"],
        "source_commit": context["manifest"]["source_commit"],
        "plan_commit": context["manifest"]["plan_commit"],
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "remaining_seconds": int(remaining),
        "minimum_remaining_reserve_seconds": policy["minimum_remaining_reserve_seconds"],
        "minimum_replacement_seconds": policy["minimum_replacement_seconds"],
        "startup_seconds": policy["startup_seconds"],
        "minimum_free_gib": policy["minimum_free_gib"],
        "minimum_free_bytes": minimum_free_bytes,
        "observed_free_bytes": observed_free_bytes,
        "resource_floor_checked": True,
        "no_foreign_processes": True,
        "exclusive_lock_checked": True,
        "lock_held": True,
        "lock_path": lock_path,
        "sidecar_namespace": namespace,
        "sidecar_namespace_existed": namespace_existed,
        "fresh_sidecar_namespace": fresh_namespace,
        "source_snapshot_checked": True,
        "process_ownership": admission["process_ownership"],
        "lock": admission["lock"],
        "fresh_namespace": admission["fresh_namespace"],
        "admission_source": admission["admission_source"],
        "supervisor_source": admission["supervisor_source"],
        "helper": admission["helper"],
        "supervisor_permit": admission.get("supervisor_permit"),
    }


@contextlib.contextmanager
def _checker_context(context: dict[str, Any], origin: dict[str, Any]) -> Iterator[None]:
    checker = context["checker"]
    validated = origin["validated"]
    if origin.get("role") != "replacement":
        yield
        return
    old_version = getattr(checker, "EXPECTED_TOOL_VERSIONS", {}).get("bifrost")
    old_native = getattr(checker, "_native_report_build_identity", None)
    if isinstance(getattr(checker, "EXPECTED_TOOL_VERSIONS", None), dict):
        checker.EXPECTED_TOOL_VERSIONS["bifrost"] = VERSION
    def native(tool: str, version: str, base: str, bindings: dict[str, Any], actual: Any, group: dict[str, Any]) -> str:
        if tool != "bifrost" or actual is not validated:
            return old_native(tool, version, base, bindings, actual, group)
        require(version == VERSION and base == BUILD and bindings.get("bifrost", {}).get("sha256") == BINARY_SHA,
                "replacement native identity differs")
        return f"{BUILD} — {VERSION} — standalone engine; empty shipped policy catalog; open-pack acquisition disabled; BIFROST_OPEN_PACKS_DISABLE=1"
    if callable(old_native):
        checker._native_report_build_identity = native
    try:
        yield
    finally:
        if isinstance(getattr(checker, "EXPECTED_TOOL_VERSIONS", None), dict):
            checker.EXPECTED_TOOL_VERSIONS["bifrost"] = old_version
        if callable(old_native):
            checker._native_report_build_identity = old_native


def _sidecar_path(root: Path, manifest: dict[str, Any], attempt_id: str, suffix: str) -> Path:
    namespace = manifest.get("sidecar_namespace")
    require(isinstance(namespace, str), "sidecar_namespace is required")
    base = root / Path(*relative(namespace, "sidecar namespace").parts)
    require(not base.exists() or base.is_dir(), "sidecar namespace is not a directory")
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{attempt_id}-{suffix}.json"
    require(not path.exists() and not path.is_symlink(), "sidecar path already exists")
    return path


def _phase_ref(root: Path, path: Path) -> dict[str, str]:
    """Return an exact repository-relative binding for a phase receipt."""
    try:
        relative_path = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise Replacement05Error("phase receipt escaped the repository root") from exc
    return {"path": relative_path, "sha256": sha(path.read_bytes())}


def _validate_phase_gate(context: dict[str, Any], ref: object, *, group_id: str | None,
                         phase: str, admission_key: str) -> dict[str, Any]:
    """Validate the durable live-gate result produced while its lock was held."""
    value = _json(bound(context["root"], ref, "phase live-gate receipt"),
                  "phase live-gate receipt")
    manifest = context["manifest"]
    admission = _validate_admission(
        context["root"], manifest.get(admission_key), manifest,
        group_id=group_id, phase=phase, manifest_sha256=context["manifest_sha256"])
    require(value.get("schema") == PHASE_GATE_SCHEMA and
            value.get("status") == "live-gates-passed" and
            value.get("automatic_retry") is False,
            "phase live-gate receipt is not a one-shot exact schema")
    require(value.get("phase") == phase and value.get("admission_key") == admission_key and
            value.get("admission") == manifest.get(admission_key),
            "phase live-gate admission identity differs")
    require(value.get("manifest_path") == manifest.get("_path") and
            value.get("manifest_sha256") == context["manifest_sha256"] and
            value.get("contract_sha256") == context["contract_sha256"] and
            value.get("source_commit") == manifest.get("source_commit") and
            value.get("plan_commit") == manifest.get("plan_commit"),
            "phase live-gate source/plan identity differs")
    require(isinstance(value.get("checked_at_utc"), str) and value["checked_at_utc"],
            "phase live-gate timestamp is missing")
    try:
        dt.datetime.fromisoformat(value["checked_at_utc"])
    except ValueError as exc:
        raise Replacement05Error("phase live-gate timestamp is malformed") from exc
    if group_id is not None:
        expected_attempt = f"{group_id}-attempt-{3 if group_id == 'bifrost-c-kernel' else 2:02d}-series-02"
        require(value.get("group_id") == group_id and value.get("attempt_id") == expected_attempt,
                "phase live-gate attempt identity differs")
    else:
        require(value.get("group_id") is None and value.get("attempt_id") is None,
                "configuration phase live-gate has an execution identity")
    policy = manifest["resource_policy"]
    require(value.get("minimum_remaining_reserve_seconds") == policy["minimum_remaining_reserve_seconds"] and
            value.get("minimum_replacement_seconds") == policy["minimum_replacement_seconds"] and
            value.get("startup_seconds") == policy["startup_seconds"] and
            value.get("minimum_free_gib") == policy["minimum_free_gib"],
            "phase live-gate policy differs")
    remaining = value.get("remaining_seconds")
    require(type(remaining) is int and
            remaining >= policy["minimum_remaining_reserve_seconds"] and
            remaining >= policy["minimum_replacement_seconds"] + policy["startup_seconds"],
            "phase live-gate remaining reserve is below the reviewed floor")
    minimum_bytes = policy["minimum_free_gib"] * 1024 ** 3
    require(value.get("minimum_free_bytes") == minimum_bytes and
            type(value.get("observed_free_bytes")) is int and
            value["observed_free_bytes"] >= minimum_bytes,
            "phase live-gate free-space result is below the reviewed floor")
    require(value.get("resource_floor_checked") is True and
            value.get("no_foreign_processes") is True and
            value.get("exclusive_lock_checked") is True and
            value.get("lock_held") is True and
            value.get("source_snapshot_checked") is True and
            value.get("fresh_sidecar_namespace") is True,
            "phase live-gate result omitted a required live check")
    require(value.get("lock_path") == manifest.get("lock_path") and
            value.get("sidecar_namespace") == manifest.get("sidecar_namespace"),
            "phase live-gate lock or namespace differs")
    require(value.get("process_ownership") == admission.get("process_ownership") and
            value.get("lock") == admission.get("lock") and
            value.get("fresh_namespace") == admission.get("fresh_namespace") and
            value.get("helper") == admission.get("helper") and
            value.get("admission_source") == admission.get("admission_source") and
            value.get("supervisor_source") == admission.get("supervisor_source") and
            value.get("supervisor_permit") == admission.get("supervisor_permit"),
            "phase live-gate evidence bindings differ")
    return value


def _validate_replacement_phase_receipts(context: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    """Require every replacement row to retain its complete durable chain.

    The completion sidecar is an evidence link, rather than the execution
    authority.  It therefore has to bind the exact parent admission, the
    serialized ledger transition, and the frozen executor's completed receipt
    before a later replay can treat the row as complete.
    """
    root, manifest = context["root"], context["manifest"]
    namespace = manifest.get("sidecar_namespace")
    require(isinstance(namespace, str), "sidecar_namespace is required for phase receipts")
    base = root / Path(*relative(namespace, "sidecar namespace").parts)
    require(not base.is_symlink() and (not base.exists() or base.is_dir()),
            "replacement phase namespace is not a safe directory")
    ledger_raw = read(root, LEDGER)
    require(ledger_raw.startswith(context["prefix_raw"]),
            "replacement phase ledger prefix changed")
    ledger_lines = ledger_raw.splitlines(keepends=True)
    live_rows = canonical_rows(ledger_raw)
    require(live_rows == rows and len(ledger_lines) == len(rows),
            "replacement phase ledger rows changed during validation")
    prefix_len = len(context["prefix"])
    parent_admissions: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows[prefix_len:], start=prefix_len):
        attempt_id = row.get("attempt_id")
        group_id = row.get("group_id")
        require(isinstance(attempt_id, str) and isinstance(group_id, str),
                "replacement phase receipt lacks row identity")
        require(row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("timed_out") is False and row.get("capacity_loss") is None,
                "replacement phase row is not a completed successful attempt")
        admission_path = base / f"{attempt_id}-admission.json"
        completion_path = base / f"{attempt_id}-completion.json"
        require(admission_path.is_file() and not admission_path.is_symlink(),
                f"missing replacement phase admission receipt: {attempt_id}")
        require(completion_path.is_file() and not completion_path.is_symlink(),
                f"missing replacement phase completion receipt: {attempt_id}")
        admission_raw = admission_path.read_bytes()
        admission = _json(admission_raw, f"replacement phase admission: {attempt_id}")
        parent = parent_admissions.setdefault(group_id, _validate_admission(
            root, manifest.get("execution_admission"), manifest,
            group_id=group_id, manifest_sha256=context["manifest_sha256"]))
        # This is the exact key set emitted by execute().  Rejecting added or
        # omitted fields prevents a sidecar from silently dropping a binding
        # while still passing the small identity checks below.
        expected_keys = {
            "schema", "attempt_id", "original_origin_utc", "cutoff_utc",
            "total_wall_budget_seconds", "source_commit", "plan_commit",
            "contract_sha256", "superseded_attempt_id", "superseded_receipt_sha256",
            "ledger_before_sha256", "status", "automatic_retry", "manifest_path",
            "manifest_sha256", "ledger_prefix", "implementation", "implementation_test",
            "phase", "group_id", "release_group", "process_ownership", "lock",
            "fresh_namespace", "admission_source", "supervisor_source",
            "admission_source_sha256", "helper", "supervisor_permit", "resource_policy",
            "resource_policy_sha256", "remaining_reserved_seconds", "dispatch_phase_gate",
        }
        require(set(admission) == expected_keys,
                "replacement phase admission fields are not the reviewed complete set")
        require(admission.get("schema") == "v092-bifrost-v0140-replacement-admission/v2" and
                admission.get("status") == "ready-to-execute" and
                admission.get("automatic_retry") is False and
                admission.get("attempt_id") == attempt_id and
                admission.get("group_id") == group_id and
                admission.get("contract_sha256") == context["contract_sha256"] and
                admission.get("source_commit") == manifest["source_commit"] and
                admission.get("plan_commit") == manifest["plan_commit"],
                "replacement phase admission identity differs")
        for field in (
            "schema", "attempt_id", "original_origin_utc", "cutoff_utc", "total_wall_budget_seconds",
            "source_commit", "plan_commit", "contract_sha256", "status", "automatic_retry",
            "manifest_path", "manifest_sha256", "ledger_prefix", "implementation",
            "implementation_test", "phase", "group_id", "release_group",
            "process_ownership", "lock", "fresh_namespace", "admission_source",
            "supervisor_source", "admission_source_sha256", "helper", "supervisor_permit",
            "resource_policy", "resource_policy_sha256", "remaining_reserved_seconds",
        ):
            require(admission.get(field) == parent.get(field),
                    f"replacement phase admission does not preserve parent {field}")
        old = next((candidate for candidate in context["prefix"]
                    if candidate.get("group_id") == group_id and
                    candidate.get("status") == "completed"), None)
        require(old is not None, "replacement phase row has no completed predecessor")
        old_receipt_path = f"reports/releases/v0.9.2/attempts/{old['attempt_id']}/completed.json"
        require(admission.get("superseded_attempt_id") == old["attempt_id"] and
                admission.get("superseded_receipt_sha256") == sha(read(root, old_receipt_path)),
                "replacement phase predecessor evidence changed")
        require(admission.get("ledger_before_sha256") == sha(b"".join(ledger_lines[:index])),
                "replacement phase ledger-before witness changed")
        phase_ref = admission.get("dispatch_phase_gate")
        require(isinstance(phase_ref, dict) and set(phase_ref) == {"path", "sha256"},
                "replacement phase admission lacks an exact live-gate binding")
        _validate_phase_gate(context, phase_ref, group_id=group_id,
                             phase="execution", admission_key="execution_admission")
        completed_path = f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"
        completed_raw = read(root, completed_path)
        completed = _json(completed_raw, f"completed attempt receipt: {attempt_id}")
        require(completed.get("attempt_id") == attempt_id and
                completed.get("status") == "completed" and
                completed.get("exit_code") == 0 and
                completed.get("timed_out") is False and
                completed.get("capacity_loss") is None,
                "completed attempt receipt is not a successful completion")
        completion = _json(completion_path.read_bytes(), f"replacement phase completion: {attempt_id}")
        require(completion.get("status") == "completed" and
                completion.get("status") == row.get("status") and
                completion.get("attempt_id") == attempt_id and
                completion.get("phase_gate") == phase_ref and
                completion.get("phase_gate_sha256") == phase_ref["sha256"] and
                completion.get("admission_sha256") == sha(admission_raw) and
                completion.get("completed_receipt_sha256") == sha(completed_raw) and
                completion.get("ledger_after_sha256") == sha(b"".join(ledger_lines[:index + 1])),
                "replacement completion does not bind its completed receipt and ledger transition")


def _write_new(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False)
        stream.write("\n")


def validate(root: Path | str, manifest_path: str, manifest_sha256: str,
             *, require_admission: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_raw = read(root, manifest_path)
    require(sha(manifest_raw) == manifest_sha256, "replacement manifest digest changed")
    manifest = _json(manifest_raw, "replacement manifest")
    require(manifest.get("schema") == SCHEMA and manifest.get("finalized") is True,
            "replacement manifest is not finalized")
    require(manifest.get("original_origin_utc") == ORIGIN and
            manifest.get("cutoff_utc") == CUTOFF and
            manifest.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "replacement changes the original clock")
    manifest["_path"] = manifest_path
    manifest["_sha256"] = manifest_sha256
    contract_ref = manifest.get("contract")
    require(isinstance(contract_ref, dict), "replacement contract binding is missing")
    contract_raw = bound(root, contract_ref, "replacement contract")
    contract = _json(contract_raw, "replacement contract")
    implementation_ref = manifest.get("implementation")
    expected_implementation = {"path": Path(__file__).resolve().relative_to(root).as_posix(),
                               "sha256": sha(Path(__file__).read_bytes())}
    require(implementation_ref == expected_implementation,
            "replacement manifest does not bind this exact implementation")
    test_ref = manifest.get("implementation_test")
    require(isinstance(test_ref, dict), "replacement focused test binding is missing")
    bound(root, test_ref, "replacement focused tests")
    continuation_prefix_ref = manifest.get("ledger_prefix")
    require(isinstance(continuation_prefix_ref, dict) and
            continuation_prefix_ref.get("rows") == ORIGINAL_ROWS and
            continuation_prefix_ref.get("path") == CONTINUATION_PREFIX_PATH and
            SHA_RE.fullmatch(str(continuation_prefix_ref.get("sha256", ""))),
            "manifest must bind the exact immutable 89-row ledger prefix")
    prefix_raw = bound(root, continuation_prefix_ref, "89-row ledger prefix")
    _validate_original_prefix(root, manifest, prefix_raw)
    original_prefix_ref = manifest.get("original_prefix")
    require(original_prefix_ref == {"path": ORIGINAL_PREFIX_PATH,
                                   "rows": HISTORICAL_ROWS,
                                   "sha256": ORIGINAL_PREFIX_SHA256},
            "manifest must bind the fixed sealed 87-row predecessor")
    continuation = _load_continuation(root, manifest, continuation_prefix_ref,
                                      original_prefix_ref)
    continuation_sha = continuation["contract_ref"]["sha256"]
    prefix = validate_prefix(prefix_raw, prefix_sha=continuation_prefix_ref["sha256"],
                             continuation_sha=continuation_sha,
                             continuation_source=continuation["source_commit"],
                             continuation_plan=continuation["plan_commit"])
    require(contract.get("source_commit") == manifest.get("source_commit") and
            COMMIT_RE.fullmatch(str(manifest.get("source_commit"))) and
            COMMIT_RE.fullmatch(str(manifest.get("plan_commit"))),
            "replacement source/plan identity is missing")
    source_commit, plan_commit = manifest["source_commit"], manifest["plan_commit"]
    require(source_commit != continuation["source_commit"], "replacement must use a new measured source commit")
    _ancestor(root, continuation["source_commit"], source_commit, "continuation source to replacement source")
    _ancestor(root, source_commit, plan_commit, "replacement source to replacement plan")
    require(_git_show(root, plan_commit, contract_ref["path"]) == contract_raw,
            "replacement contract differs from its registered plan commit")
    executor = _load_frozen(root, "executor")
    checker = _load_frozen(root, "checker")
    configuration = _load_frozen(root, "configuration")
    base = executor.validate_plan(root / Path(*relative(BASE_CONTRACT).parts), repo_root=root)
    require(base.get("bytes_sha256") == BASE_CONTRACT_SHA, "frozen base contract changed")
    # The continuation's committed plan is the only semantic baseline for the
    # 84-row tail; Bifrost changes must not reach unrelated groups.
    inherited = continuation["contract"]
    ids = replacement_ids(inherited)
    require(manifest.get("replacement_groups") == ids, "replacement group order/scope changed")
    _contract_delta(inherited, contract, manifest, ids)
    bifrost = contract.get("tools", {}).get("bifrost")
    require(isinstance(bifrost, dict) and bifrost.get("version") == "0.14.0" and
            bifrost.get("report_version") == VERSION and bifrost.get("build_identity") == BUILD and
            bifrost.get("sha256") == BINARY_SHA,
            "replacement contract does not bind the qualified Bifrost binary")
    runner = manifest.get("runner")
    require(isinstance(runner, dict) and contract.get("tools", {}).get("runner") == runner,
            "replacement runner identity is missing or differs")
    require(runner.get("sha256") != inherited.get("tools", {}).get("runner", {}).get("sha256"),
            "replacement runner must be an explicitly measured new identity")
    for group in contract.get("groups", []):
        if group.get("id") not in ids:
            continue
        argv = group.get("argv")
        require(isinstance(argv, list) and argv and argv[0] == runner.get("path"),
                f"replacement group does not bind the measured runner: {group.get('id')}")
        try:
            bifrost_index = argv.index("--bifrost")
        except ValueError as exc:
            raise Replacement05Error(f"replacement group lacks --bifrost: {group.get('id')}") from exc
        require(bifrost_index + 1 < len(argv) and argv[bifrost_index + 1] == bifrost.get("path"),
                f"replacement group does not bind the measured Bifrost binary: {group.get('id')}")
        expected_attempts = 3 if group.get("id") == "bifrost-c-kernel" else 2
        require(group.get("maximum_attempts") == expected_attempts,
                f"replacement attempt cap changed: {group.get('id')}")
        require(all(report.get("tool_version") == VERSION for report in group.get("reports", [])),
                f"replacement report version binding changed: {group.get('id')}")
    bifrost_environments = [group.get("environment") for group in contract.get("groups", [])
                            if group.get("id") in ids]
    require(bifrost_environments and all(environment == bifrost_environments[0]
                                         for environment in bifrost_environments) and
            isinstance(bifrost_environments[0], dict),
            "Bifrost groups do not share one exact child environment")
    _validate_runner_binding(root, manifest, runner, contract, source_commit,
                             bifrost_environments[0])
    qualified = _validate_qualification(root, manifest.get("qualification"), ids)
    require(contract.get("qualifications", {}).get("bifrost", {}).get("evidence") == manifest["qualification"],
            "contract qualification does not bind the exact manifest evidence")
    require(manifest.get("admission_source") == ADMISSION_SOURCE_REF and
            manifest.get("supervisor_source") == SUPERVISOR_SOURCE_REF,
            "replacement admission/supervisor sources are not the exact reviewed inputs")
    bound(root, ADMISSION_SOURCE_REF, "reviewed admission source")
    bound(root, SUPERVISOR_SOURCE_REF, "reviewed supervisor source")
    design = _json(bound(root, manifest.get("source_design"), "source design"), "source design")
    _validate_review_bindings(root, manifest, module_sha=expected_implementation["sha256"],
                              test_sha=test_ref["sha256"], contract_ref=contract_ref,
                              source_design_ref=manifest["source_design"], prefix_ref=continuation_prefix_ref,
                              original_prefix_ref=manifest["original_prefix"])
    delta = _source_delta(root, design, manifest, continuation["source_commit"], source_commit)
    inherited_inputs = continuation["contract"].get("source_inputs", [])
    input_summary = _source_inputs(root, executor, inherited_inputs, contract, manifest, source_commit)
    frozen_replacement = _validate_replacement_plan(root, executor, contract_ref, contract_raw,
                                                    contract, plan_commit)
    # Validate every new evidence binding explicitly declared by the design.
    source_map = {item["path"]: item["sha256"] for item in contract["source_inputs"]}
    for item in design.get("exact_acquisition_inputs", []):
        require(source_map.get(item["path"]) == item["sha256"],
                f"source closure misses acquisition witness: {item['path']}")
    runner_artifact_ref = manifest.get("runner_artifact")
    require(isinstance(runner_artifact_ref, dict) and
            source_map.get(runner_artifact_ref.get("path")) == runner_artifact_ref.get("sha256"),
            "source closure misses the reviewed runner artifact")
    for ref in (manifest.get("qualification"), qualified.get("control_review")):
        require(source_map.get(ref["path"]) == ref["sha256"],
                f"source closure misses qualification witness: {ref['path']}")
    continuation_validated = continuation.get("validated")
    historical_contexts = ((continuation.get("validated_context") or {}).get("contexts")
                           if isinstance(continuation.get("validated_context"), dict) else None)
    if historical_contexts is None:
        historical_builder = getattr(continuation.get("module"), "_historical_contexts", None)
        require(callable(historical_builder), "continuation module lacks historical context recovery")
        old_raw = b"".join(prefix_raw.splitlines(keepends=True)[:HISTORICAL_ROWS])
        historical_contexts = historical_builder(
            base, prefix[:HISTORICAL_ROWS], old_raw,
            {"validated": base, "plan_commit": BASE_PLAN_COMMIT},
        )
    if continuation_validated is None:
        continuation_validated = copy.deepcopy(base)
        continuation_validated.update(plan=continuation["contract"], plan_raw=continuation["contract_raw"],
                                      bytes_sha256=continuation_sha, repo_root=root,
                                      path=root / continuation["contract_ref"]["path"],
                                      tools=continuation["contract"].get("tools"),
                                      source_inputs=continuation["contract"].get("source_inputs"),
                                      groups=continuation["contract"].get("groups"),
                                      total_wall_budget_seconds=TOTAL_WALL_SECONDS)
    replacement_context = _replacement_context(base, continuation_validated, contract, contract_raw,
                                                contract_ref, root, plan_commit, frozen_replacement)
    contexts = _context_map(base, continuation_validated, replacement_context, continuation_sha,
                            contract_ref["sha256"], continuation["source_commit"], continuation["plan_commit"],
                            source_commit, plan_commit, manifest,
                            historical_contexts)
    live_raw = read(root, LEDGER)
    require(live_raw.startswith(prefix_raw), "live ledger no longer begins with sealed 89-row prefix")
    rows = canonical_rows(live_raw)
    _check_rows_context(rows, contexts, contract_ref["sha256"], source_commit, plan_commit, len(prefix))
    accounting(prefix, rows, ids, contract_ref["sha256"], source_commit, plan_commit)
    if require_admission:
        _validate_admission(root, manifest.get("execution_admission"), manifest,
                            manifest_sha256=manifest_sha256)
    context = {"root": root, "manifest": manifest, "manifest_sha256": manifest_sha256,
               "prefix": prefix, "prefix_raw": prefix_raw, "rows": rows,
               "contexts": contexts, "continuation": continuation,
               "base": contexts[BASE_CONTRACT_SHA],
               "repaired": contexts[continuation_sha],
               "validated": replacement_context["validated"],
               "executor": executor, "checker": checker, "configuration": configuration,
               "ids": ids, "contract": contract, "contract_raw": contract_raw,
               "contract_sha256": contract_ref["sha256"], "source_delta": delta,
               "source_inputs_summary": input_summary, "qualification": qualified}
    return context


def _row_context(context: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    key = row.get("contract_sha256")
    require(key in context["contexts"], "ledger row has no context")
    origin = context["contexts"][key]
    if row.get("group_id") in {JOERN_GROUP, CODEQL_GROUP}:
        if row.get("attempt_id") in {JOERN_ATTEMPT, CODEQL_ATTEMPT}:
            require(key == context["continuation"]["contract_ref"]["sha256"],
                    "Swift continuation row escaped its continuation context")
    return origin


def _selected_for_projection(context: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    ids = context["ids"]
    accounting(context["prefix"], rows, ids, context["contract_sha256"],
               context["manifest"]["source_commit"], context["manifest"]["plan_commit"])
    selected: dict[str, dict[str, Any]] = {}
    for row in context["prefix"]:
        if row.get("status") == "completed" and row.get("tool") != "bifrost":
            selected[row["group_id"]] = row
    for row in rows[len(context["prefix"]):]:
        require(row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("timed_out") is False and row.get("capacity_loss") is None,
                "replacement tail is not fully successful")
        selected[row["group_id"]] = row
    projection = context["manifest"].get("final_projection_groups")
    require(isinstance(projection, list) and len(projection) == ORIGINAL_SELECTED and
            len(set(projection)) == ORIGINAL_SELECTED,
            "final_projection_groups must explicitly bind84 groups")
    require(set(selected) == set(projection), "final projection group roster changed")
    return selected


def _replay(context: dict[str, Any], rows: list[dict[str, Any]], selected: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checker, executor, root = context["checker"], context["executor"], context["root"]
    raw = read(root, LEDGER)
    line_hashes = {json.loads(line)["attempt_id"]: sha(line)
                   for line in raw.splitlines(keepends=True)}
    reports: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    outcomes: collections.Counter[str] = collections.Counter()
    for row in rows:
        origin = _row_context(context, row)
        validated = origin["validated"]
        group = executor._historical_group_for_replay(validated, row)
        number = _attempt_number(row["attempt_id"])
        with _checker_context(context, origin):
            if row.get("status") == "completed":
                bindings, counts = checker._verify_one_group(root, validated, group, row,
                                                              origin["plan_commit"], number)
            else:
                receipt = root / Path(*PurePosixPath(
                    f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json").parts)
                require(receipt.is_file(), f"missing failed attempt receipt: {row['attempt_id']}")
                failures.append(checker._verify_failed_attempt(root, validated, group, row,
                                                               origin["plan_commit"], number,
                                                               line_hashes[row["attempt_id"]],
                                                               sha(receipt.read_bytes())))
                continue
        if selected.get(row["group_id"], {}).get("attempt_id") != row["attempt_id"]:
            continue
        outcomes.update(counts)
        for binding in bindings:
            binding.update(attempt_id=row["attempt_id"], attempt_number=number,
                           evidence_contract_sha256=row["contract_sha256"])
        reports.extend(bindings)
    attempt_guard = getattr(checker, "_assert_attempt_directories", None)
    if callable(attempt_guard):
        attempt_guard(root, {row["attempt_id"] for row in rows})
    wall_guard = getattr(checker, "_validate_wall_budget", None)
    if callable(wall_guard):
        wall_guard([(row, "") for row in rows], TOTAL_WALL_SECONDS)
    require(not any("stale" in str(key).lower() and count for key, count in outcomes.items()),
            "selected reports contain stale outcomes")
    require(len(reports) == ORIGINAL_PARTITIONS and sum(x.get("rows", 0) for x in reports) == ORIGINAL_REPORT_ROWS,
            "final report denominator changed")
    return {"status": "fresh-evidence-verified", "ledger_rows": len(rows),
            "selected_groups": len(selected), "partitions": len(reports),
            "rows": sum(x.get("rows", 0) for x in reports), "known_stale": 0,
            "fresh_reports": reports, "failed_attempts": failures}


def verify(context: dict[str, Any], *, final: bool = True) -> dict[str, Any]:
    if final:
        _validate_admission(context["root"], context["manifest"].get("execution_admission"),
                            context["manifest"], manifest_sha256=context["manifest_sha256"])
    raw = read(context["root"], LEDGER)
    require(raw.startswith(context["prefix_raw"]), "live ledger prefix changed")
    rows = canonical_rows(raw)
    _check_rows_context(rows, context["contexts"], context["contract_sha256"],
                        context["manifest"]["source_commit"], context["manifest"]["plan_commit"],
                        len(context["prefix"]))
    _validate_replacement_phase_receipts(context, rows)
    if final:
        selected = _selected_for_projection(context, rows)
    else:
        accounting(context["prefix"], rows, context["ids"], context["contract_sha256"],
                   context["manifest"]["source_commit"], context["manifest"]["plan_commit"])
        selected = {row["group_id"]: row for row in context["prefix"] if row.get("status") == "completed"}
    result = _replay(context, rows, selected)
    result["selected_attempts"] = [
        {"group_id": row["group_id"], "attempt_id": row["attempt_id"],
         "contract_sha256": row["contract_sha256"],
         "source_commit": row["source_commit"], "plan_commit": row["plan_commit"]}
        for row in selected.values()
    ]
    if final:
        require(len(selected) == ORIGINAL_SELECTED, "final selection must contain84 groups")
    else:
        result["status"] = "replacement-preflight-passed"
    return result


def execute(context: dict[str, Any], group_id: str) -> dict[str, Any]:
    require(group_id in context["ids"], "only authorized Bifrost replacement groups may execute")
    root, manifest = context["root"], context["manifest"]
    require(_git(root, "rev-parse", "HEAD") == manifest["plan_commit"],
            "execution requires exact registered plan HEAD")
    parent_admission = _validate_admission(
        root, manifest.get("execution_admission"), manifest,
        group_id=group_id, manifest_sha256=context["manifest_sha256"])
    live_raw = read(root, LEDGER)
    require(live_raw.startswith(context["prefix_raw"]), "ledger prefix changed before execution")
    rows = canonical_rows(live_raw)
    seen = accounting(context["prefix"], rows, context["ids"], context["contract_sha256"],
                      manifest["source_commit"], manifest["plan_commit"])
    require(group_id not in seen, "replacement allowance already consumed")
    require(all(row.get("status") == "completed" for row in rows[len(context["prefix"]):]),
            "failed/interrupted replacement requires human decision; automatic retry is forbidden")
    remaining = [group for group in context["validated"]["plan"]["groups"]
                 if group.get("id") in context["ids"] and group.get("id") not in seen]
    require(remaining and group_id == remaining[0]["id"], "replacement groups must execute in reviewed order")
    verify(context, final=False)
    old = next(row for row in context["prefix"] if row.get("group_id") == group_id and
               row.get("status") == "completed")
    supervisor_permit = parent_admission.get("supervisor_permit")
    require(isinstance(supervisor_permit, dict) and set(supervisor_permit) == {"path", "sha256"},
            "execution admission supervisor permit binding is required")
    attempt_number = 3 if group_id == "bifrost-c-kernel" else 2
    attempt_id = f"{group_id}-attempt-{attempt_number:02d}-series-02"
    admission_path = _sidecar_path(root, manifest, attempt_id, "admission")
    admission = {"schema": "v092-bifrost-v0140-replacement-admission/v2",
                 "attempt_id": attempt_id, "original_origin_utc": ORIGIN, "cutoff_utc": CUTOFF,
                 "total_wall_budget_seconds": TOTAL_WALL_SECONDS,
                 "source_commit": manifest["source_commit"], "plan_commit": manifest["plan_commit"],
                 "contract_sha256": context["contract_sha256"], "superseded_attempt_id": old["attempt_id"],
                 "superseded_receipt_sha256": sha(read(root, f"reports/releases/v0.9.2/attempts/{old['attempt_id']}/completed.json")),
                 "ledger_before_sha256": sha(live_raw), "status": "ready-to-execute",
                 "automatic_retry": False, "manifest_path": manifest["_path"],
                 "manifest_sha256": context["manifest_sha256"],
                 "ledger_prefix": manifest["ledger_prefix"],
                 "implementation": manifest["implementation"],
                 "implementation_test": manifest["implementation_test"],
                 "phase": "execution", "group_id": group_id,
                 "attempt_id": attempt_id,
                 "release_group": "bifrost-v0140-replacement-05",
                 "process_ownership": parent_admission["process_ownership"],
                 "lock": parent_admission["lock"],
                 "fresh_namespace": parent_admission["fresh_namespace"],
                 "admission_source": parent_admission["admission_source"],
                 "supervisor_source": parent_admission["supervisor_source"],
                 "admission_source_sha256": parent_admission["admission_source_sha256"],
                 "helper": parent_admission["helper"],
                 "supervisor_permit": supervisor_permit,
                 "resource_policy": manifest["resource_policy"],
                 "resource_policy_sha256": parent_admission["resource_policy_sha256"],
                 "remaining_reserved_seconds": parent_admission.get(
                     "remaining_reserved_seconds",
                     parent_admission.get("phase_remaining_reserved_seconds"))}
    phase_ref: dict[str, str] | None = None
    try:
        runtime = _runtime_plan(context["validated"])
        with _serialized_executor(context, group_id) as live_gate:
            _check_supervisor_dispatch_permit(root, parent_admission, group_id)
            phase_path = _sidecar_path(root, manifest, attempt_id, "phase-gate")
            _write_new(phase_path, live_gate)
            phase_ref = _phase_ref(root, phase_path)
            admission["dispatch_phase_gate"] = phase_ref
            _write_new(admission_path, admission)
            with _original_clock(context["executor"], runtime):
                result = context["executor"].run_group(runtime, group_id)
        require(isinstance(result, dict) and result.get("group_id") == group_id and
                result.get("attempt_id") == attempt_id and result.get("status") == "completed" and
                result.get("exit_code") == 0 and result.get("timed_out") is False and
                result.get("capacity_loss") is None,
                "replacement execution did not complete successfully")
    except BaseException as exc:
        admission_sha256 = sha(admission_path.read_bytes()) if admission_path.is_file() else None
        _write_new(_sidecar_path(root, manifest, attempt_id, "dispatch-error"),
                   {"status": "dispatch-error-no-automatic-retry", "attempt_id": attempt_id,
                    "exception": type(exc).__name__, "message": str(exc),
                    "admission_sha256": admission_sha256,
                    "phase_gate": phase_ref,
                    "ledger_after_sha256": sha(read(root, LEDGER))})
        raise
    _write_new(_sidecar_path(root, manifest, attempt_id, "completion"),
               {"status": result["status"], "attempt_id": attempt_id,
                "admission_sha256": sha(admission_path.read_bytes()),
                "phase_gate": phase_ref,
                "phase_gate_sha256": phase_ref["sha256"] if phase_ref else None,
                "ledger_after_sha256": sha(read(root, LEDGER)),
                "completed_receipt_sha256": sha(read(root, f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"))})
    return result


def config(context: dict[str, Any], output: str) -> dict[str, Any]:
    _validate_admission(context["root"], context["manifest"].get("configuration_admission"),
                        context["manifest"], phase="configuration",
                        manifest_sha256=context["manifest_sha256"])
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", output) is not None,
            "configuration output namespace is unsafe")
    root = context["root"]
    directory = root / "reports/releases/v0.9.2/validation" / output
    require(not directory.exists() and not directory.is_symlink(), "configuration namespace exists")
    staging = directory.with_name(directory.name + f".staging-{os.getpid()}")
    require(not staging.exists() and not staging.is_symlink(), "configuration staging namespace exists")
    staging.mkdir(parents=True)
    results = []
    try:
        # Keep final replay, live-ledger selection, bucket derivation, source
        # materialization, projection, and runner invocation under the same
        # durable executor lock.  Computing summary/buckets before acquiring
        # that lock permits a concurrent dispatch to make the configuration
        # receipt describe a stale ledger.
        with _serialized_configuration(context) as configuration_gate:
            summary = verify(context, final=True)
            selected_rows = _selected_for_projection(context, canonical_rows(read(root, LEDGER)))
            buckets = configuration_contexts(
                selected_rows, context["contexts"]
            )
            for index, (contract_sha, attempt_ids) in enumerate(sorted(buckets.items())):
                origin = context["contexts"][contract_sha]
                checkout = root / "execution-state/v092/validation" / f"{output}-{index:02d}"
                require(not checkout.exists() and not checkout.is_symlink(), "configuration checkout exists")
                subset = {**summary,
                          "fresh_reports": [x for x in summary["fresh_reports"] if x.get("attempt_id") in attempt_ids],
                          "selected_attempts": [x for x in summary["selected_attempts"] if x.get("attempt_id") in attempt_ids]}
                n = len(subset["fresh_reports"])
                count = sum(x.get("rows", 0) for x in subset["fresh_reports"])
                context["executor"]._materialize_source(root, origin["validated"]["plan"]["source_commit"], checkout,
                                                         [x["path"] for x in origin["validated"]["source_inputs"]])
                materialization_gate = _live_gates(
                    context, None, phase="configuration", admission_key="configuration_admission")
                context["configuration"]._project_reports(root, checkout, subset,
                                                            expected_report_count=n, expected_row_count=count)
                # The final gate is immediately adjacent to the runner call,
                # while still inside the shared durable lock.
                runner_gate = _live_gates(
                    context, None, phase="configuration", admission_key="configuration_admission")
                env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(checkout), "TMPDIR": str(checkout),
                       "LANG": "C", "LC_ALL": "C", "NO_COLOR": "1"}
                require(env == context["manifest"].get("runner_environment"),
                        "configuration runner environment differs from reviewed environment")
                invocation = context["configuration"]._invoke_runner(origin["validated"]["tools"]["runner"], checkout, env)
                (staging / f"{index:02d}-stdout.bin").write_bytes(invocation["stdout"])
                (staging / f"{index:02d}-stderr.bin").write_bytes(invocation["stderr"])
                metrics = context["configuration"]._parse_stdout(invocation["stdout"])
                require(context["configuration"]._validation_success(invocation["exit_code"], metrics, n),
                        "per-context canonical configuration validation failed")
                results.append({"contract_sha256": contract_sha, "attempt_ids": attempt_ids,
                                "partitions": n, "rows": count, "metrics": metrics,
                                "source_commit": origin["source_commit"],
                                "plan_commit": origin["plan_commit"],
                                "materialization_phase_gate": materialization_gate,
                                "runner_phase_gate": runner_gate})
            result = {"schema": "v092-bifrost-v0140-configuration-receipt/v2",
                      "status": "canonical-validation-passed", "automatic_retry": False,
                      "partitions": sum(x["partitions"] for x in results),
                      "rows": sum(x["rows"] for x in results),
                      "known_stale": sum(x["metrics"].get("known_stale", 0) for x in results),
                      "manifest_path": context["manifest"].get("_path"),
                      "manifest_sha256": context["manifest_sha256"],
                      "ledger_prefix": context["manifest"]["ledger_prefix"],
                      "original_prefix": context["manifest"]["original_prefix"],
                      "implementation": context["manifest"]["implementation"],
                      "implementation_test": context["manifest"]["implementation_test"],
                      "contract_sha256": context["contract_sha256"],
                      "source_commit": context["manifest"]["source_commit"],
                      "plan_commit": context["manifest"]["plan_commit"],
                      "runner_artifact": context["manifest"]["runner_artifact"],
                      "runner_environment": context["manifest"]["runner_environment"],
                      "executor_environment": context["manifest"]["executor_environment"],
                      "resource_policy": context["manifest"]["resource_policy"],
                      "configuration_admission": context["manifest"]["configuration_admission"],
                      "configuration_phase_gate": configuration_gate,
                      "source_contexts": results}
            require(result["partitions"] == ORIGINAL_PARTITIONS and result["rows"] == ORIGINAL_REPORT_ROWS and
                    result["known_stale"] == 0, "final configuration denominator changed")
            _write_new(staging / "receipt.json", result)
            staging.rename(directory)
            return result
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


configurations = config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "validate", "execute", "run", "verify", "check", "config"))
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--group")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        context = validate(ROOT, args.manifest, args.manifest_sha256,
                           require_admission=args.command in {"execute", "run", "verify", "check", "config"})
        if args.command in {"preflight", "validate"}:
            result = verify(context, final=False)
        elif args.command in {"execute", "run"}:
            require(args.group is not None, "execute requires --group")
            result = execute(context, args.group)
        elif args.command in {"verify", "check"}:
            result = verify(context, final=True)
        else:
            require(args.output is not None, "config requires --output")
            result = config(context, args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Replacement05Error as exc:
        print(f"replacement05 rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
