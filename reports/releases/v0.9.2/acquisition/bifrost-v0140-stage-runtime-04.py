#!/usr/bin/env python3
"""Read-only adapter at the frozen v0.9.2 validation boundary.

Unlike bridge-01, this module does not consume a captured ``verified`` JSON
object.  It loads the reviewed modules and calls their validators while the
caller still has the validation checkout.  The returned value is an
in-memory context; no receipt, ledger row, sidecar, checkout, process, or
attempt is written.  The fixture-module seam is deliberately explicit and is
available only to the focused tests in a temporary Git repository.
"""
from __future__ import annotations

import base64
import collections
import contextlib
import copy
import hashlib
import importlib.machinery
import importlib.util
import inspect
import json
import marshal
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import types
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "v092-bifrost-v0140-frozen-bridge/v8"
REPLACEMENT05 = {
    "path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py",
    "sha256": "32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd",
}
FROZEN = {
    "executor": {
        "path": "scripts/execute-release-v092.py",
        "sha256": "fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8",
    },
    "checker": {
        "path": "scripts/check-release-v092.py",
        "sha256": "0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928",
    },
    "configuration": {
        "path": "scripts/validate-v092-report-configurations.py",
        "sha256": "21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858",
    },
}
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
EXPECTED_GROUPS = 84
EXPECTED_PARTITIONS = 92
EXPECTED_ROWS = 4252
EXPECTED_CASES = 1108
HISTORICAL_ROWS = 88
INCOMING_MIN_ROWS = 89
TOTAL_WALL_SECONDS = 333360
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")


class FrozenBridgeError(ValueError):
    """The frozen validation boundary rejected an input or returned shape."""


class FrozenBridgeUnsupported(FrozenBridgeError):
    """Execution-side operations intentionally remain unavailable."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise FrozenBridgeError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _relative(value: object, label: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{label} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts), f"unsafe {label}")
    return path


def _read(root: Path, path: str) -> bytes:
    current = root
    for part in _relative(path).parts:
        current = current / part
        require(not current.is_symlink(), f"symlink in bound path: {path}")
    require(current.is_file(), f"missing bound file: {path}")
    return current.read_bytes()


def _path(root: Path, value: str, label: str = "path") -> Path:
    """Resolve a checked relative path without permitting traversal."""
    return root / Path(*_relative(value, label).parts)


def _ref(value: object, label: str) -> dict[str, str]:
    require(isinstance(value, dict) and set(value) <= {"path", "sha256", "rows"} and
            {"path", "sha256"} <= set(value),
            f"{label} must be an exact path/SHA binding")
    _relative(value.get("path"), f"{label} path")
    require(isinstance(value.get("sha256"), str) and SHA_RE.fullmatch(value["sha256"]),
            f"{label} SHA is malformed")
    result = {"path": value["path"], "sha256": value["sha256"]}
    if "rows" in value:
        require(type(value["rows"]) is int and value["rows"] >= 0, f"{label} rows is malformed")
        result["rows"] = value["rows"]
    return result


def _bound(root: Path, value: object, label: str) -> bytes:
    ref = _ref(value, label)
    raw = _read(root, ref["path"])
    require(sha256(raw) == ref["sha256"], f"{label} digest changed (bytes differ): {ref['path']}")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrozenBridgeError(f"{label} is not valid JSON") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _commit(value: object, label: str) -> str:
    require(isinstance(value, str) and COMMIT_RE.fullmatch(value), f"{label} is not a commit SHA")
    return value


def _git(root: Path, *args: str, check: bool = True) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, check=check,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FrozenBridgeError(f"read-only git query failed: git {' '.join(args)}") from exc
    return result.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FrozenBridgeError(f"read-only git query failed: git {' '.join(args)}") from exc


def _git_show(root: Path, commit: str, path: str) -> bytes:
    _commit(commit, "git commit")
    _relative(path, "git path")
    return _git_bytes(root, "show", f"{commit}:{path}")


def _ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    _commit(ancestor, f"{label} ancestor")
    _commit(descendant, f"{label} descendant")
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                       cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FrozenBridgeError(f"{label} is not an ancestor") from exc


def _load_module(root: Path, name: str, ref: Mapping[str, str]) -> Any:
    before = _bound(root, dict(ref), f"frozen {name}")
    spec = importlib.util.spec_from_file_location(f"v092_frozen_bridge_02_{name}", root / ref["path"])
    require(spec is not None and spec.loader is not None, f"cannot import frozen {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = _read(root, ref["path"])
    require(sha256(before) == sha256(after) == ref["sha256"], f"frozen {name} changed during import")
    return module


def load_dependencies(root: Path | str = ROOT, *, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False) -> dict[str, Any]:
    """Load only the exact production modules, or explicit temporary fixtures.

    A caller cannot inject a module into production mode.  Fixture injection
    is accepted only when ``fixture_only=True`` and all four modules are
    supplied; this is the seam used by the focused temporary-Git tests.
    """
    root = Path(root).resolve()
    names = {"replacement05", "executor", "checker", "configuration"}
    if fixture_modules is not None or fixture_only:
        require(fixture_only and fixture_modules is not None,
                "fixture modules require the explicit fixture_only seam")
        temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/private/var/folders").resolve()}
        require(root != ROOT and set(fixture_modules) == names and
                any(root == item or item in root.parents for item in temp_roots),
                "fixture injection is restricted to a temporary test root and exact module set")
        for name in names:
            module = fixture_modules[name]
            require(getattr(module, "__name__", "").startswith("fixture_"),
                    f"{name} is not a fixture module")
        replacement = fixture_modules["replacement05"]
        for export in ("_source_delta", "_source_inputs", "_validate_replacement_plan",
                       "_context_map", "_check_rows_context"):
            require(callable(getattr(replacement, export, None)),
                    f"fixture replacement-05 lacks required boundary: {export}")
        return dict(fixture_modules)
    replacement = _load_module(root, "replacement05", REPLACEMENT05)
    for export in ("_load_frozen", "_source_delta", "_source_inputs",
                   "_validate_replacement_plan",
                   "_context_map", "_check_rows_context", "_contract_delta",
                   "_validate_qualification", "_validate_runner_binding", "_replay"):
        require(callable(getattr(replacement, export, None)),
                f"replacement-05 boundary export is unavailable: {export}")
    modules = {"replacement05": replacement}
    for name, ref in FROZEN.items():
        try:
            module = replacement._load_frozen(root, name)
        except Exception as exc:
            raise FrozenBridgeError(f"replacement-05 could not load frozen {name}") from exc
        require(sha256(_read(root, ref["path"])) == ref["sha256"],
                f"frozen {name} changed after replacement-05 loader")
        modules[name] = module
    return modules


def _jsonable(value: Any) -> Any:
    """Preserve every returned field while making a digestable JSON value."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"__type__": "bytes", "encoding": "base64",
                "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise FrozenBridgeError(f"validator returned unsupported value type: {type(value).__name__}")


def _canonical_rows(raw: bytes, label: str) -> list[dict[str, Any]]:
    require(raw.endswith(b"\n") and raw, f"{label} is not a complete ledger")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FrozenBridgeError(f"{label} line {index} is not valid JSON") from exc
        require(isinstance(row, dict) and canonical_json(row) == line,
                f"{label} line {index} is not canonical JSON")
        rows.append(row)
    require(rows, f"{label} is empty")
    attempts = [row.get("attempt_id") for row in rows]
    require(all(isinstance(item, str) and item for item in attempts) and
            len(attempts) == len(set(attempts)), f"{label} has duplicate/missing attempts")
    return rows


def _shape(plan: Mapping[str, Any]) -> dict[str, Any]:
    groups = plan.get("groups")
    require(isinstance(groups, list) and len(groups) == EXPECTED_GROUPS,
            "frozen normalized plan must contain all 84 groups")
    group_ids: list[str] = []
    cases: list[str] = []
    partitions = rows = 0
    for group in groups:
        require(isinstance(group, dict) and isinstance(group.get("id"), str), "normalized group is malformed")
        group_ids.append(group["id"])
        values = group.get("case_ids")
        require(isinstance(values, list) and all(isinstance(item, str) for item in values),
                f"normalized group {group.get('id')} lacks case_ids")
        cases.extend(values)
        reports = group.get("reports")
        require(isinstance(reports, list), f"normalized group {group['id']} lacks reports")
        partitions += len(reports)
        for report in reports:
            require(isinstance(report, dict) and isinstance(report.get("case_ids"), list),
                    f"normalized report in {group['id']} is malformed")
            rows += len(report["case_ids"])
    require(len(group_ids) == len(set(group_ids)), "normalized plan has duplicate groups")
    require(len(set(cases)) == EXPECTED_CASES and partitions == EXPECTED_PARTITIONS and rows == EXPECTED_ROWS,
            "normalized plan shape does not derive the complete 84/92/4252/1108 matrix")
    return {"groups": len(group_ids), "partitions": partitions, "rows": rows,
            "unique_cases": len(set(cases)), "group_ids": group_ids}


def _validate_group_projection(plan: Mapping[str, Any], normalized_groups: object) -> None:
    """Compare every normalized group to its complete contract group.

    Case IDs may legitimately recur across tools.  The only global coverage
    assertion is the frozen union size; membership and report rows are checked
    per group so a duplicated or dropped group cannot hide behind that union.
    """
    require(isinstance(normalized_groups, list), "normalized group projection is not a list")
    expected = plan.get("groups")
    require(isinstance(expected, list) and len(normalized_groups) == len(expected),
            "normalized group projection length differs from the complete contract")
    expected_by_id = {item.get("id"): item for item in expected if isinstance(item, Mapping)}
    require(len(expected_by_id) == len(expected), "contract group IDs are not unique")
    seen: set[str] = set()
    for normalized in normalized_groups:
        require(isinstance(normalized, Mapping) and isinstance(normalized.get("id"), str),
                "normalized group projection entry is malformed")
        group_id = normalized["id"]
        require(group_id not in seen and group_id in expected_by_id,
                f"normalized group projection has unknown/duplicate group: {group_id}")
        seen.add(group_id)
        original = expected_by_id[group_id]
        case_ids = normalized.get("case_ids")
        expected_cases = original.get("case_ids")
        require(isinstance(case_ids, list) and isinstance(expected_cases, list) and
                len(case_ids) == len(set(case_ids)) and case_ids == expected_cases,
                f"normalized case membership differs for {group_id}")
        reports = normalized.get("reports")
        expected_reports = original.get("reports")
        require(isinstance(reports, list) and isinstance(expected_reports, list) and
                len(reports) == len(expected_reports),
                f"normalized report roster differs for {group_id}")
        for actual_report, expected_report in zip(reports, expected_reports):
            require(isinstance(actual_report, Mapping) and isinstance(expected_report, Mapping) and
                    actual_report.get("case_ids") == expected_report.get("case_ids"),
                    f"normalized report membership differs for {group_id}")
    require(seen == set(expected_by_id), "normalized group projection omits a contract group")


def _resolve_replacement_source_inputs(normalizer: Any, plan: Mapping[str, Any], root: Path,
                                       qualification: Mapping[str, Any],
                                       inherited: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Preserve exact incoming source closure; new paths use frozen C4 rules.

    CodeQL's independently verified context registers historical attempt and
    adapter evidence outside C4's original acquisition/qualification prefixes.
    This is not a general prefix exemption: every such item must be byte-for-
    byte inherited, and every inherited entry must remain present unchanged.
    """
    if inherited is None:
        return normalizer(plan, root, qualification)
    entries = plan.get("source_inputs")
    require(isinstance(entries, list) and all(isinstance(v, dict) for v in entries),
            "replacement source input entries are malformed")
    old = {v.get("path"): v for v in inherited}
    actual = {v.get("path"): v for v in entries}
    require(len(old) == len(inherited) and len(actual) == len(entries) and
            all(actual.get(path) == item for path, item in old.items()),
            "replacement parser changed or omitted an inherited source input")
    prefixes = ("reports/releases/v0.9.2/acquisition/", "reports/releases/v0.9.2/qualification/")
    ordinary, exceptional = [], []
    for item in entries:
        path = _relative(item.get("path"), "source input path").as_posix()
        if path.startswith(prefixes) or path == "execution-state/v092/swift-source/patch-application/applied-patch.json":
            ordinary.append(item)
        else:
            require(path in old and item == old[path] and set(item) <= {"path", "sha256", "role"},
                    "new source input is outside frozen acquisition/qualification scope")
            _bound(root, {"path": path, "sha256": item.get("sha256")}, "exact inherited source input")
            role = item.get("role", "release-input")
            require(isinstance(role, str) and bool(role), "inherited source input role is malformed")
            exceptional.append({"path": path, "sha256": item["sha256"], "role": role})
    projected = dict(plan, source_inputs=ordinary)
    result = normalizer(projected, root, qualification)
    require(not ({v["path"] for v in result} & {v["path"] for v in exceptional}),
            "qualification normalization collides with inherited exceptional input")
    return sorted([*result, *exceptional], key=lambda item: item["path"])


def _validate_normalized_source_inputs(executor: Any, validated: Mapping[str, Any],
                                       root: Path, *, inherited: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Compare the frozen normalized closure with the executor's own resolver.

    The contract's raw ``plan.source_inputs`` is intentionally not the
    normalized return: the frozen executor supplies default ``release-input``
    roles, applies qualification-evidence overrides, sorts, and deduplicates.
    Reusing that exact resolver preserves the full closure without accepting a
    hand-shaped role projection from the bridge.
    """
    normalizer = getattr(executor, "_source_inputs", None)
    require(callable(normalizer), "frozen executor source-input normalizer is unavailable")
    plan = validated.get("plan")
    qualification = validated.get("qualification", {})
    require(isinstance(plan, Mapping) and isinstance(qualification, Mapping),
            "frozen normalized source-input inputs are malformed")
    try:
        expected = _resolve_replacement_source_inputs(normalizer, plan, root, qualification, inherited)
    except Exception as exc:
        raise FrozenBridgeError("frozen executor source-input normalization failed") from exc
    require(isinstance(expected, list) and all(isinstance(item, Mapping) for item in expected),
            "frozen executor returned no normalized source-input closure")
    actual = validated.get("source_inputs")
    require(isinstance(actual, list) and actual == expected,
            "frozen normalized source-input closure differs from the executor resolver")
    return [dict(item) for item in expected]


def _validate_binary_identity(root: Path, core: Mapping[str, Any],
                              validated: Mapping[str, Any]) -> dict[str, Any]:
    """Bind the core binary object byte-for-byte to the normalized plan."""
    plan = validated.get("plan")
    tools = plan.get("tools") if isinstance(plan, Mapping) else None
    plan_binary = tools.get("bifrost") if isinstance(tools, Mapping) else None
    core_binary = core.get("binary")
    require(isinstance(plan_binary, Mapping) and isinstance(core_binary, Mapping),
            "core and normalized plan must bind a Bifrost binary identity")
    require(dict(core_binary) == dict(plan_binary),
            "core binary identity differs from the normalized plan tool identity")
    path_value = plan_binary.get("path")
    digest = plan_binary.get("sha256")
    require(isinstance(path_value, str) and path_value and "\x00" not in path_value and
            isinstance(digest, str) and SHA_RE.fullmatch(digest),
            "normalized Bifrost binary identity is malformed")
    path = Path(path_value)
    if path.is_absolute():
        require(path.resolve() == path and path.is_file() and not path.is_symlink(),
                "absolute normalized Bifrost binary is missing or indirect")
        raw = path.read_bytes()
    else:
        _relative(path_value, "Bifrost binary path")
        raw = _read(root, path_value)
    require(sha256(raw) == digest, "normalized Bifrost binary bytes differ from its identity")
    return dict(plan_binary)


def _exact_source_context_entries(core: Mapping[str, Any], *, fixture_only: bool) -> Mapping[str, Any]:
    """Return the typed context roster without accepting legacy aliases.

    The historical map is evidence about *how* the frozen context is rebuilt;
    it is not a serialized validator result.  Production callers therefore
    have to provide the exact v07 core field and the exact four entry binding
    shape.  The explicit fixture seam keeps the small tests independent of
    the release packet while never widening production input acceptance.
    """
    entries = core.get("source_contexts")
    require(isinstance(entries, Mapping) and entries,
            "source_contexts must bind every retained context")
    for key, item in entries.items():
        require(isinstance(key, str) and SHA_RE.fullmatch(key) and isinstance(item, Mapping),
                "source context key or entry is malformed")
        if not fixture_only:
            require(set(item) == {"contract", "source_commit", "plan_commit", "role"},
                    f"source context {key} has an unreviewed field")
        else:
            require({"contract", "source_commit", "plan_commit", "role"} <= set(item),
                    f"source context {key} is incomplete")
        if not fixture_only:
            require(isinstance(item.get("contract"), Mapping) and
                    set(item["contract"]) == {"path", "sha256"},
                    f"source context {key} contract binding has an unreviewed field")
        _ref(item.get("contract"), f"source context {key} contract")
        _commit(item.get("source_commit"), f"source context {key} source")
        _commit(item.get("plan_commit"), f"source context {key} plan")
        require(item.get("role") in {"base", "historical", "continuation", "replacement"},
                f"source context {key} role is not typed")
    return entries


def _incoming_recovery(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    """Recover actual CodeQL successor objects using its pinned Python validator.

    The provider must expose recover_bifrost_history(root, manifest_path,
    manifest_sha256, prefix_raw). It must validate its original exact immutable
    history and the actual CodeQL terminal tail, and return the in-process
    base/contexts/repaired objects. No JSON-normalized context is a substitute.
    The exact source/manifest/actual prefix are sealed in the reviewed core.
    """
    policy_path = Path(__file__).with_name("bifrost-v0140-replacement-13.py")
    spec = importlib.util.spec_from_file_location("bridge06_incoming_policy", policy_path)
    require(spec is not None and spec.loader is not None, "incoming policy unavailable")
    policy = importlib.util.module_from_spec(spec); spec.loader.exec_module(policy)
    policy._validate_historical_prefixes(root, core)
    seal = _json(_bound(root, core["incoming_history"], "incoming history seal"), "incoming history seal")
    module = _load_module(root, "independent_codeql_history", seal["recovery_module"])
    recover = getattr(module, "recover_bifrost_history", None)
    require(callable(recover), "pinned CodeQL validator lacks recover_bifrost_history API")
    raw = _bound(root, core["continuation_prefix"], "actual incoming prefix")
    value = recover(root, seal["recovery_manifest"]["path"],
                    seal["recovery_manifest"]["sha256"], raw)
    require(isinstance(value, dict) and set(value) == {"base", "contexts", "repaired", "prefix_sha256"} and
            value["prefix_sha256"] == sha256(raw) and isinstance(value["contexts"], dict) and
            isinstance(value["base"], dict) and isinstance(value["repaired"], dict),
            "CodeQL incoming recovery is not the exact real in-process context closure")
    return value


def _ref_for_context(entries: Mapping[str, Any], role: str) -> tuple[str, Mapping[str, Any]]:
    matches = [(key, item) for key, item in entries.items() if item.get("role") == role]
    require(len(matches) == 1, f"source_contexts must contain exactly one {role} entry")
    return matches[0]


def _ref_json(root: Path, value: object, label: str) -> tuple[dict[str, Any], dict[str, str]]:
    ref = _ref(value, label)
    return _json(_bound(root, ref, label), label), ref


def _mixed_selected(context: Mapping[str, Any], rows: list[dict[str, Any]],
                    *, final: bool) -> dict[str, dict[str, Any]]:
    """Select release evidence truthfully; no old-version fallback for Bifrost."""
    prefix = context.get("prefix")
    require(isinstance(prefix, list), "selected context lacks actual immutable incoming prefix")
    ids = context.get("ids")
    require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), "missing replacement order")
    require(rows[:len(prefix)] == prefix, "selected history changed incoming prefix")
    selected = {row["group_id"]: row for row in prefix
                if row.get("status") == "completed" and row.get("exit_code") == 0 and
                row.get("group_id") not in ids}
    tail = rows[len(prefix):]
    require(len(tail) <= len(ids), "replacement has unreviewed additional attempts")
    for index, row in enumerate(tail):
        group = ids[index]
        number = 3 if group == "bifrost-c-kernel" else 2
        require(row.get("group_id") == group and row.get("attempt_id") ==
                f"{group}-attempt-{number:02d}-series-02" and row.get("tool") == "bifrost" and
                row.get("execution_series") == 2 and
                row.get("contract_sha256") == context["contract_sha256"] and
                row.get("source_commit") == context["source_commit"] and
                row.get("plan_commit") == context["plan_commit"],
                "replacement order/global attempt/source context changed")
        # A failed replacement never silently selects old0131 evidence.
        if row.get("status") == "completed" and row.get("exit_code") == 0 and row.get("capacity_loss") is None:
            selected[group] = row
        else:
            require(row.get("status") in {"failed", "timed-out", "recorder-error", "capacity-lost"},
                    "replacement tail has no truthful terminal classification")
    if final:
        require(len(tail) == len(ids), "batch final check requires one actual outcome per independent group")
    return selected


def _observed_wall(checker: Any, rows: list[dict[str, Any]]) -> float:
    """Validate frozen timestamp/serialization rules with the actual elapsed span."""
    import datetime as dt
    timestamps = [dt.datetime.fromisoformat(row[key].replace("Z", "+00:00"))
                  for row in rows for key in ("start_utc", "end_utc")]
    require(timestamps, "partial replay has no wall provenance")
    method = getattr(checker, "_validate_wall_budget", None)
    require(callable(method), "production checker lacks actual wall provenance validation")
    return method([(row, "") for row in rows],
                  max(1.0, (max(timestamps)-min(timestamps)).total_seconds()))


def _origin_context(context: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Historical Joern04 and independent CodeQL01 keep DISTINCT origins."""
    key = row.get("contract_sha256")
    contexts = context.get("contexts")
    require(isinstance(contexts, Mapping) and key in contexts, "ledger origin is absent from recovered closure")
    origin = contexts[key]
    require(isinstance(origin, dict) and origin.get("validated", {}).get("bytes_sha256") == key and
            row.get("source_commit") == origin["validated"].get("plan", {}).get("source_commit") and
            row.get("plan_commit") == origin.get("plan_commit"),
            "historical row changed exact source/plan/contract origin")
    return origin


def _partial_replay(replacement: Any, context: dict[str, Any], rows: list[dict[str, Any]],
                    selected: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Use exact frozen per-row verifiers without inventing a full denominator."""
    checker, executor, root = context["checker"], context["executor"], context["root"]
    raw = _read(root, LEDGER_PATH)
    require(_canonical_rows(raw, "actual ledger") == rows, "partial replay ledger differs")
    line_hashes = {json.loads(line)["attempt_id"]: sha256(line)
                   for line in raw.splitlines(keepends=True)}
    reports, failures = [], []
    outcomes = collections.Counter()
    for row in rows:
        origin = _origin_context(context, row)
        normalized = origin["validated"]
        group = executor._historical_group_for_replay(normalized, row)
        number = replacement._attempt_number(row["attempt_id"])
        with replacement._checker_context(context, origin):
            if row.get("status") == "completed":
                bindings, counts = checker._verify_one_group(
                    root, normalized, group, row, origin["plan_commit"], number)
            else:
                receipt = _read(root, f"reports/releases/v0.9.2/attempts/{row['attempt_id']}/completed.json")
                failures.append(checker._verify_failed_attempt(
                    root, normalized, group, row, origin["plan_commit"], number,
                    line_hashes[row["attempt_id"]], sha256(receipt)))
                continue
        if selected.get(row["group_id"], {}).get("attempt_id") != row["attempt_id"]:
            continue
        outcomes.update(counts)
        for binding in bindings:
            binding.update(attempt_id=row["attempt_id"], attempt_number=number,
                           evidence_contract_sha256=row["contract_sha256"])
        reports.extend(bindings)
    checker._assert_attempt_directories(root, {row["attempt_id"] for row in rows})
    _observed_wall(checker, rows)
    require(not any("stale" in str(k).lower() and n for k,n in outcomes.items()),
            "selected reports contain stale outcomes")
    # Report denominators come from every selected normalized group's reports.
    expected_partitions = 0
    expected_report_rows = 0
    for row in selected.values():
        origin = _origin_context(context, row)
        group = executor._historical_group_for_replay(origin["validated"], row)
        expected_partitions += len(group["reports"])
        expected_report_rows += sum(len(report["case_ids"]) for report in group["reports"])
    require(len(reports) == expected_partitions, "partial selected partition count differs from normalized plans")
    expected_rows = sum(int(binding["rows"]) for binding in reports)
    require(expected_rows == expected_report_rows, "partial selected row count differs from normalized case partitions")
    full = len(selected) == EXPECTED_GROUPS and len(reports) == EXPECTED_PARTITIONS and expected_rows == EXPECTED_ROWS
    return {"status": "fresh-evidence-verified" if full else "partial-evidence-verified",
            "ledger_rows": len(rows), "selected_groups": len(selected), "partitions": len(reports),
            "rows": expected_rows, "known_stale": 0, "fresh_reports": reports,
            "failed_attempts": failures,
            "missing_groups": sorted(set(g["id"] for g in context["validated"]["groups"]) - set(selected)),
            "full_release_gate_satisfied": full}


def _call_mixed(replacement: Any, context: dict[str, Any], rows: list[dict[str, Any]],
                *, final: bool, fixture_only: bool = False) -> Any:
    selected = _mixed_selected(context, rows, final=final)
    if fixture_only:
        method = getattr(replacement, "_replay", None)
        require(callable(method), "fixture mixed replay unavailable")
        return method(context, rows, selected)
    return _partial_replay(replacement, context, rows, selected)


def _completed_receipt_sha(root: Path, row: Mapping[str, Any], *, fixture_only: bool) -> str:
    """Resolve a selected attempt's receipt hash from the live evidence tree."""
    supplied = row.get("completed_receipt_sha256")
    if isinstance(supplied, str) and SHA_RE.fullmatch(supplied):
        return supplied
    attempt_id = row.get("attempt_id")
    require(isinstance(attempt_id, str) and attempt_id,
            "selected completed row lacks an attempt identity")
    path = f"reports/releases/v0.9.2/attempts/{attempt_id}/completed.json"
    if fixture_only:
        # Fixture checkers intentionally do not model attempt directories.  A
        # synthetic receipt digest is acceptable only to the fixture config
        # seam, which never validates this summary.
        return sha256(canonical_json(dict(row)))
    return sha256(_read(root, path))


def _configuration_checker_summary(root: Path, checker_result: Mapping[str, Any],
                                   selected: Mapping[str, Mapping[str, Any]],
                                   validated: Mapping[str, Any], *, fixture_only: bool) -> dict[str, Any]:
    """Convert actual mixed replay output to the frozen config-checker schema.

    Every denominator and report binding comes from `_replay` or the complete
    normalized plan.  The configuration script requires a separate final
    canonical Rust gate marker; this adapter preserves that required protocol
    field without claiming that gate has run.
    """
    require(checker_result.get("status") == "fresh-evidence-verified",
            "configuration requires a completed mixed replay summary")
    reports = checker_result.get("fresh_reports")
    require(isinstance(reports, list), "mixed replay did not return fresh report bindings")
    plan = validated.get("plan")
    require(isinstance(plan, Mapping), "normalized plan is unavailable for configuration summary")
    groups = plan.get("groups")
    require(isinstance(groups, list), "normalized plan group roster is unavailable")
    unique_cases = {case_id for group in groups if isinstance(group, Mapping)
                    for case_id in group.get("case_ids", []) if isinstance(case_id, str)}
    summary = dict(checker_result)
    summary.update({
        "fresh_groups": checker_result.get("selected_groups"),
        "fresh_partitions": checker_result.get("partitions"),
        "fresh_rows": checker_result.get("rows"),
        "case_count": len(unique_cases),
        "carried_partitions": checker_result.get("carried_partitions", 0),
        "carried_rows": checker_result.get("carried_rows", 0),
        "fresh_reports": copy.deepcopy(reports),
        "selected_attempts": [
            {"status": "completed", "group_id": group_id,
             "attempt_id": row.get("attempt_id"),
             "completed_receipt_sha256": _completed_receipt_sha(
                 root, row, fixture_only=fixture_only)}
            for group_id, row in selected.items()
        ],
        "configuration_hash_validation": {
            "canonical_rust_validate_reports": "required separate final-delivery gate",
        },
    })
    require(summary["fresh_groups"] == len(selected),
            "mixed replay selected-group count does not match its selected attempts")
    return summary


def _call_configuration(configuration: Any, checker: Any, executor: Any, root: Path,
                        contract: Path, output: str, validated: Mapping[str, Any],
                        checker_summary: Mapping[str, Any]) -> Any:
    """Run frozen configuration validation with scoped, identity-checked adapters.

    The configuration module imports its own checker/executor instances.  A
    direct call would therefore validate a different module boundary and lose
    the bridge's exact normalized context.  Patch those two module attributes
    and the two entry points only for this execute=False call, then restore
    every object in a finally block.
    """
    method = getattr(configuration, "validate", None)
    require(callable(method), "frozen configuration validator is unavailable")
    missing = object()
    old_config_checker = getattr(configuration, "CHECKER", missing)
    old_config_executor = getattr(configuration, "EXECUTOR", missing)
    old_verify = getattr(checker, "verify", missing)
    old_validate_plan = getattr(executor, "validate_plan", missing)

    def scoped_verify(*args: Any, **kwargs: Any) -> dict[str, Any]:
        call_root = kwargs.get("root", args[0] if args else None)
        call_contract = kwargs.get("contract_path", args[1] if len(args) > 1 else None)
        require(call_root is not None and Path(call_root).resolve() == root,
                "configuration checker requested a different validation root")
        require(call_contract is not None and Path(call_contract).resolve() == contract,
                "configuration checker requested a different contract")
        return copy.deepcopy(dict(checker_summary))

    def scoped_validate_plan(*args: Any, **kwargs: Any) -> Mapping[str, Any]:
        call_contract = kwargs.get("contract_path", args[0] if args else None)
        call_root = kwargs.get("repo_root")
        require(call_contract is not None and Path(call_contract).resolve() == contract,
                "configuration executor requested a different contract")
        require(call_root is not None and Path(call_root).resolve() == root,
                "configuration executor requested a different validation root")
        return validated

    require(callable(old_verify), "frozen checker verify entry point is unavailable")
    require(callable(old_validate_plan), "frozen executor validate_plan entry point is unavailable")
    try:
        configuration.CHECKER = checker
        configuration.EXECUTOR = executor
        checker.verify = scoped_verify
        executor.validate_plan = scoped_validate_plan
        value = method(root=root, contract_path=contract, output=output, execute=False)
    except Exception as exc:
        raise FrozenBridgeError("frozen configuration execute=False validation failed") from exc
    finally:
        if old_config_checker is missing:
            try:
                delattr(configuration, "CHECKER")
            except AttributeError:
                pass
        else:
            configuration.CHECKER = old_config_checker
        if old_config_executor is missing:
            try:
                delattr(configuration, "EXECUTOR")
            except AttributeError:
                pass
        else:
            configuration.EXECUTOR = old_config_executor
        if old_verify is missing:
            try:
                delattr(checker, "verify")
            except AttributeError:
                pass
        else:
            checker.verify = old_verify
        if old_validate_plan is missing:
            try:
                delattr(executor, "validate_plan")
            except AttributeError:
                pass
        else:
            executor.validate_plan = old_validate_plan
    return value


def _validate_replacement_with_scoped_resource_boundary(
    root: Path, executor: Any, replacement: Any, contract_path: Path,
    contract_ref: Mapping[str, str], contract_raw: bytes, core: Mapping[str, Any],
    manifest_obj: Mapping[str, Any], source_commit: str, rows: list[dict[str, Any]],
    raw: bytes,
) -> dict[str, Any]:
    """Validate the replacement with the one reviewed C4 resource adapter.

    Frozen ``validate_plan`` is still the validator for every ordinary field.
    Its legacy parser cannot represent the reviewed replacement path, rich
    qualification identity, C03 cap, aggregate guard, and no-expiry clock.
    Exact scoped projections below preserve every other frozen field check;
    actual plan/group values and module hooks are restored before return.  The adapter first runs replacement-05's
    contract/qualification/runner gates, then obtains the complete historical
    recovery object by invoking continuation-06's exact C4 boundary.  It never
    accepts a caller-supplied serialized recovery or copies a replacement
    plan into a historical result.
    """
    contract_plan = _json(contract_raw, "replacement contract")
    require(contract_plan.get("resource_guards") == {"stop_free_gib": 48, "working_set_gib": 30},
            "replacement must inherit only the exact authorized aggregate30GiB guard")
    parser_plan = copy.deepcopy(contract_plan)
    parser_plan["resource_guards"]["working_set_gib"] = 12
    c_groups = [group for group in parser_plan.get("groups", [])
                if group.get("id") == "bifrost-c-kernel"]
    require(len(c_groups) == 1 and type(c_groups[0].get("maximum_attempts")) is int and
            c_groups[0]["maximum_attempts"] == 3,
            "replacement parser requires the exact reviewed C03 cap")
    c_groups[0]["maximum_attempts"] = 2
    original_v4 = getattr(executor, "V4_CONTRACT_PATH", None)
    require(original_v4 == PurePosixPath("reports/releases/v0.9.2/execution-v4/contract.json"),
            "frozen canonical C4 parser boundary differs")
    require(contract_path.resolve().is_relative_to(root.resolve()) and
            contract_path.resolve().relative_to(root.resolve()).as_posix() == contract_ref["path"] and
            contract_ref["path"] != original_v4.as_posix(),
            "replacement parser path must be the exact new contract, preserving C4")
    require(contract_ref["path"] ==
            "reports/releases/v0.9.2/execution-v4/continuations/bifrost-v0140-replacement-13-contract.json",
            "population projection requires the exact replacement13 contract path")
    original_population = getattr(executor, "_population", None)
    require(callable(original_population), "frozen population boundary is unavailable")
    original_inputs = getattr(executor, "_source_inputs", None)
    require(callable(original_inputs), "frozen exact source-input resolver is unavailable")
    original_read = getattr(executor, "_read_json", None)
    require(callable(original_read), "frozen exact-plan reader is unavailable")
    original = getattr(executor, "_validate_resource_recovery", None)
    original_wall = getattr(executor, "_wall_budget", None)
    require(callable(original_wall), "frozen plan wall-budget boundary is unavailable")
    require(callable(original), "frozen executor resource-recovery hook is unavailable")
    source_contexts = _exact_source_context_entries(core, fixture_only=False)
    base_key, base_entry = _ref_for_context(source_contexts, "base")
    base_ref = _ref(base_entry["contract"], "base source context contract")
    require(base_ref["path"] == "reports/releases/v0.9.2/execution-v4/contract.json" and
            base_key == "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb",
            "resource adapter base context is not the registered C4 contract")
    continuation_contract = _ref(core["continuation"]["contract"], "continuation contract")
    inherited_raw = _bound(root, continuation_contract, "typed continuation contract")
    inherited_plan = _json(inherited_raw, "typed continuation contract")
    ids = [group.get("id") for group in _json(contract_raw, "replacement contract").get("groups", [])
           if isinstance(group, Mapping) and group.get("tool") == "bifrost"]
    require(len(ids) == 20 and len(set(ids)) == 20,
            "replacement resource adapter requires the complete 20-group Bifrost subset")
    # Resolve the explicit reviewed replacement gates before entering the
    # frozen validator.  These calls bind the replacement semantics that C4's
    # resource-only successor check cannot represent.
    try:
        replacement._contract_delta(inherited_plan, _json(contract_raw, "replacement contract"),
                                    dict(manifest_obj), ids)
        replacement_plan = _json(contract_raw, "replacement contract")
        runner = manifest_obj.get("runner")
        require(isinstance(runner, dict) and replacement_plan.get("tools", {}).get("runner") == runner,
                "replacement resource adapter runner identity is missing")
        environments = [group.get("environment") for group in replacement_plan.get("groups", [])
                        if isinstance(group, Mapping) and group.get("id") in ids]
        require(environments and isinstance(environments[0], dict) and
                all(value == environments[0] for value in environments),
                "replacement resource adapter Bifrost environment is not exact")
        replacement._validate_runner_binding(root, dict(manifest_obj), runner, replacement_plan,
                                             source_commit, environments[0])
        replacement._validate_qualification(root, manifest_obj.get("qualification"), ids)
        qualification_ref = _ref(manifest_obj.get("qualification"), "qualified v0140 evidence")
        require(qualification_ref == replacement.QUALIFICATION_REF,
                "qualification parser is not bound to exact immutable reviewed evidence")
        qualification_raw = _bound(root, qualification_ref, "qualified v0140 evidence")
        qualification_obj = _json(qualification_raw, "qualified v0140 evidence")
        qualification_parser = copy.deepcopy(qualification_obj)
        # Only the two extra provenance fields are projected from this ONE
        # exact immutable evidence object. The raw bytes/digest stay original;
        # the full richer object was independently checked immediately above.
        require(set(qualification_parser["tool"]) ==
                {"path", "sha256", "version", "build_identity", "bytes", "public_tag_commit"},
                "rich qualification tool identity has unreviewed fields")
        del qualification_parser["tool"]["bytes"]
        del qualification_parser["tool"]["public_tag_commit"]
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError("replacement gates rejected the scoped resource adapter") from exc

    recovered_history = _incoming_recovery(root, core)
    base_path = root / Path(*_relative(base_ref["path"], "base source context contract").parts)
    recovery_cache: dict[str, Any] = {}

    def scoped(validated: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(validated, Mapping) or validated.get("bytes_sha256") != contract_ref["sha256"]:
            return original(validated)
        if "value" not in recovery_cache:
            try:
                base_value = recovered_history["base"]["validated"]
                require(isinstance(base_value, dict) and
                        base_value.get("bytes_sha256") == base_key and
                        isinstance(base_value.get("resource_recovery"), dict),
                        "frozen C4 boundary returned no complete historical recovery")
                recovery_cache["value"] = copy.deepcopy(base_value["resource_recovery"])
            except FrozenBridgeError:
                raise
            except Exception as exc:
                raise FrozenBridgeError("frozen C4 resource recovery could not be derived") from exc
        return copy.deepcopy(recovery_cache["value"])

    def no_expiry_plan_wall(plan):
        # The exact committed replacement contract is null.  This finite
        # historical normalization value only satisfies the frozen parser;
        # it is removed from the returned context before any consumer runs.
        if plan.get("source_commit") == source_commit and plan.get("execution_series") == 2:
            require(plan == parser_plan and plan.get("total_wall_budget_seconds") is None,
                    "no-expiry parser adapter received another plan")
            return float(TOTAL_WALL_SECONDS)
        return original_wall(plan)

    def exact_replacement_reader(path, description):
        plan_value, raw_value = original_read(path, description)
        if Path(path).resolve() == contract_path.resolve():
            require(plan_value == contract_plan and raw_value == contract_raw,
                    "aggregate parser adapter received changed contract bytes")
            return copy.deepcopy(parser_plan), raw_value
        if Path(path).resolve() == (root / qualification_ref["path"]).resolve():
            require(plan_value == qualification_obj and raw_value == qualification_raw,
                    "qualification parser received changed immutable bytes")
            return copy.deepcopy(qualification_parser), raw_value
        return plan_value, raw_value

    def exact_replacement_inputs(plan, repo_root, qualification):
        require(plan == parser_plan and Path(repo_root).resolve() == root.resolve(),
                "scoped source-input resolver received another contract")
        return _resolve_replacement_source_inputs(original_inputs, plan, repo_root,
                                                  qualification, inherited_plan["source_inputs"])

    def exact_replacement_population(plan, plan_path):
        # The frozen population helper derives the repository root from the
        # canonical C4 contract depth. Our exact successor is one level deeper.
        # Only this exact plan/path is projected onto the unchanged canonical
        # root anchor; the original helper still reads the bound population
        # and validates raw SHA, fixture identity, and complete case roster.
        require(plan == parser_plan and
                Path(plan_path).resolve() == contract_path.resolve() and
                contract_path.resolve() == (root / contract_ref["path"]).resolve(),
                "population projection received another plan/path/root")
        return original_population(plan, root / original_v4)

    executor._population = exact_replacement_population
    executor._source_inputs = exact_replacement_inputs
    executor.V4_CONTRACT_PATH = PurePosixPath(contract_ref["path"])
    executor._validate_resource_recovery = scoped
    executor._wall_budget = no_expiry_plan_wall
    executor._read_json = exact_replacement_reader
    try:
        try:
            value = executor.validate_plan(contract_path, repo_root=root)
        except FrozenBridgeError:
            raise
        except Exception as exc:
            raise FrozenBridgeError("frozen validator rejected replacement after scoped resource checks") from exc
    finally:
        executor._validate_resource_recovery = original
        executor._wall_budget = original_wall
        executor._read_json = original_read
        executor.V4_CONTRACT_PATH = original_v4
        executor._source_inputs = original_inputs
        executor._population = original_population
    require(value.get("path") == str(contract_path.resolve()),
            "frozen parser must retain the actual replacement contract path")
    require(value.get("plan") == parser_plan, "frozen aggregate parser changed another plan field")
    normalized_c = [group for group in value.get("groups", [])
                    if group.get("id") == "bifrost-c-kernel"]
    require(len(normalized_c) == 1 and normalized_c[0].get("maximum_attempts") == 2,
            "frozen parser changed the exact C cap projection")
    normalized_c[0]["maximum_attempts"] = 3
    value["plan"] = copy.deepcopy(contract_plan)
    require(value.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "frozen parser normalization changed")
    value["total_wall_budget_seconds"] = None
    return value


def _source_delta05(root: Path, design: Mapping[str, Any], manifest: Mapping[str, Any],
                    incoming_source: str, target: str, *, incoming_plan: str) -> dict[str, Any]:
    """Verify real CodeQL ancestry plus the exact immediate nine-file delta."""
    reviewed_base = _commit(design.get("reviewed_baseline_head"), "source05 reviewed baseline9b")
    baseline = _commit(design.get("immediate_patch_base"), "source05 immediate patch base")
    incoming = design.get("incoming_codeql", {})
    require(incoming.get("source_commit") == incoming_source and incoming.get("plan_commit") == incoming_plan,
            "source05 actual incoming CodeQL source/plan differs")
    require(manifest.get("source_delta_baseline") == baseline,
            "source evidence must bind source05 actual immediate patch base")
    _ancestor(root, reviewed_base, baseline, "baseline9b to immediate patch base")
    _ancestor(root, incoming_source, incoming_plan, "CodeQL source to actual CodeQL plan")
    _ancestor(root, incoming_plan, baseline, "actual CodeQL plan to immediate patch base")
    _ancestor(root, baseline, target, "immediate patch base to replacement source")
    closure = design.get("reviewed_intervening_changes")
    require(isinstance(closure, list), "reviewed CodeQL/acquisition closure missing")
    declared = {}
    for item in closure:
        require(isinstance(item, dict) and set(item) == {"path", "status", "before_sha256", "after_sha256"},
                "intervening change lacks exact reviewed fields")
        path = _relative(item["path"], "intervening reviewed path").as_posix()
        require(path.startswith(("scripts/", "reports/releases/v0.9.2/")) and path not in declared and
                item["status"] in {"A", "M"} and SHA_RE.fullmatch(str(item["after_sha256"])) and
                ((item["status"] == "A" and item["before_sha256"] is None) or
                 (item["status"] == "M" and SHA_RE.fullmatch(str(item["before_sha256"])))),
                "intervening change is outside exact reviewed CodeQL/acquisition closure")
        declared[path] = item["status"]
        if item["status"] == "M":
            require(sha256(_git_show(root, reviewed_base, path)) == item["before_sha256"],
                    "intervening reviewed before bytes differ")
        require(sha256(_git_show(root, baseline, path)) == item["after_sha256"],
                "intervening reviewed after bytes differ")
    def changes(left: str, right: str) -> dict[str, str]:
        observed = {}
        for line in _git(root, "diff", "--name-status", "--no-renames", left, right).splitlines():
            parts = line.split("\t")
            require(len(parts) == 2 and parts[0] in {"A", "M"} and parts[1] not in observed,
                    "source delta deletes, renames or repeats an input")
            observed[parts[1]] = parts[0]
        return observed
    require(changes(reviewed_base, baseline) == declared,
            "intervening source changes differ from reviewed CodeQL/acquisition closure")
    entries = design.get("allowed_source_delta")
    require(isinstance(entries, list) and len(entries) == 9, "source04 nine-file patch roster differs")
    paths = [item["path"] for item in entries]
    require(len(set(paths)) == len(paths) and sorted(manifest.get("source_delta_paths", [])) == sorted(paths),
            "source evidence delta paths differ from immutable source04")
    expected = {item["path"]: "A" if item["current_before_sha256"] is None else "M" for item in entries}
    require(changes(baseline, target) == expected,
            "replacement source commit differs outside exact reviewed nine files")
    for item in entries:
        path = _relative(item["path"], "source04 path").as_posix()
        before = item["current_before_sha256"]
        if before is not None:
            require(sha256(_git_show(root, baseline, path)) == before, "source04 baseline bytes changed")
        require(sha256(_git_show(root, target, path)) == item["expected_after_sha256"],
                "source04 target bytes differ from formatted reviewed patch")
    _bound(root, design.get("unchanged_source_patch"), "reviewed formatted source patch02")
    return {"baseline": baseline, "reviewed_baseline": reviewed_base,
            "incoming_source": incoming_source, "incoming_plan": incoming_plan, "target": target,
            "intervening_paths": sorted(declared), "paths": sorted(paths),
            "patch_files": sorted(paths), "approved_additive_scripts": []}


def _validate_historical_bifrost(root: Path, design: Mapping[str, Any],
                                 contexts: Mapping[str, Any], rows: list[dict[str, Any]]) -> None:
    """Keep every old Bifrost receipt on its original source, plan and harness.

    Actual report/capture verification stays with the unadapted frozen checker;
    this gate never regenerates historical native reports with the new harness.
    """
    expected = design.get("actual_historical_bifrost_rows")
    roster = design.get("actual_historical_bifrost_contexts")
    require(isinstance(expected, list) and len(expected) == 21 and
            isinstance(roster, list) and len(roster) == 2, "historical Bifrost roster is incomplete")
    actual = [r for r in rows if r.get("tool") == "bifrost" and r.get("execution_series") != 2]
    require(len(actual) == len(expected), "historical Bifrost receipt count differs")
    for row, declaration in zip(actual, expected):
        require(sha256((json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()) ==
                declaration["exact_ledger_row_sha256"], "historical Bifrost row bytes differ")
        for field in ("group_id", "attempt_id", "status", "source_commit", "plan_commit", "contract_sha256", "argv", "fixture_revision"):
            require(row.get(field) == declaration.get(field), f"historical Bifrost {field} changed")
        entry = contexts.get(row["contract_sha256"])
        require(isinstance(entry, dict), "historical Bifrost origin omitted")
        validated = entry["validated"]
        old = next((x for x in roster if x["contract"]["sha256"] == row["contract_sha256"]), None)
        require(old is not None and validated["bytes_sha256"] == row["contract_sha256"] and
                validated["plan"]["source_commit"] == old["contract_source_commit"] == row["source_commit"] and
                entry["plan_commit"] == row["plan_commit"], "historical Bifrost origin relabeled")
        runner = validated["tools"]["runner"]
        require(str(runner["path"]) == old["historical_harness"]["path"] == row["argv"][0] and
                runner["sha256"] == old["historical_harness"]["sha256"],
                "historical Bifrost must retain original harness")
        tool = validated["tools"]["bifrost"]
        require(all(str(tool.get(k)) == str(v) for k, v in old["tool"].items()),
                "historical Bifrost binary identity changed")


def _load_contexts(root: Path, executor: Any, core: Mapping[str, Any], replacement: Any,
                   current: dict[str, Any], contract_ref: dict[str, str],
                   source_commit: str, plan_commit: str, manifest_obj: Mapping[str, Any],
                   *, rows: list[dict[str, Any]], raw: bytes,
                   fixture_only: bool) -> dict[str, dict[str, Any]]:
    entries = _exact_source_context_entries(core, fixture_only=fixture_only)
    if fixture_only:
        # The fixture seam deliberately exercises the same replacement-05
        # context-map call but does not pretend to reproduce the production
        # C1/C2/C3 archive.  It is confined to a temporary Git repository.
        contexts: dict[str, dict[str, Any]] = {}
        for key, item in entries.items():
            ref = item["contract"]
            bound_raw = _bound(root, ref, f"historical contract {key}")
            require(sha256(bound_raw) == key, f"historical contract digest differs for {key}")
            path = root / Path(*_relative(ref["path"], "historical contract path").parts)
            try:
                value = executor.validate_plan(path, repo_root=root)
            except Exception as exc:
                raise FrozenBridgeError(f"fixture validator rejected historical contract {key}") from exc
            require(isinstance(value, dict) and value.get("bytes_sha256") == key and
                    isinstance(value.get("plan"), dict),
                    f"fixture historical validator result is incomplete for {key}")
            contexts[key] = {"validated": value, "plan_commit": item["plan_commit"],
                             "source_commit": item["source_commit"], "role": item["role"]}
        base = next((item["validated"] for item in contexts.values() if item["role"] == "base"), current)
        continuation = next((item["validated"] for item in contexts.values()
                             if item["role"] == "continuation"), current)
        historical = {key: value for key, value in contexts.items()
                      if key != contract_ref["sha256"]}
        try:
            result = replacement._context_map(
                base, continuation, {"validated": current, "plan_commit": plan_commit,
                                     "source_commit": source_commit, "role": "replacement"},
                next((key for key, item in contexts.items() if item["role"] == "continuation"),
                     contract_ref["sha256"]),
                contract_ref["sha256"], continuation.get("plan", {}).get("source_commit", source_commit),
                continuation.get("plan_commit", plan_commit), source_commit, plan_commit,
                dict(manifest_obj), historical,
            )
        except Exception as exc:
            raise FrozenBridgeError("fixture replacement-05 context map rejected the roster") from exc
        require(isinstance(result, dict) and result, "fixture replacement-05 returned no context map")
        return result

    recovered = _incoming_recovery(root, core)
    contexts = {}
    for key, value in recovered["contexts"].items():
        require(key in entries and isinstance(value, dict), "incoming history omits typed context")
        item = entries[key]
        normalized = value.get("validated")
        require(isinstance(normalized, dict) and normalized.get("bytes_sha256") == key and
                normalized.get("plan", {}).get("source_commit") == item["source_commit"] and
                value.get("plan_commit") == item["plan_commit"] and item["role"] != "replacement",
                "incoming context source/plan/contract differs")
        contexts[key] = {**value, "source_commit": item["source_commit"], "role": item["role"]}
    continuation_key, continuation_entry = _ref_for_context(entries, "continuation")
    require(continuation_key in contexts and recovered["repaired"]["validated"] ==
            contexts[continuation_key]["validated"], "actual CodeQL continuation context differs")
    replacement_entry = entries.get(contract_ref["sha256"])
    require(isinstance(replacement_entry, Mapping) and replacement_entry.get("role") == "replacement",
            "missing actual replacement source context")
    contexts[contract_ref["sha256"]] = {"validated": current, "plan_commit": plan_commit,
                                      "source_commit": source_commit, "role": "replacement"}
    require(set(contexts) == set(entries), "source context roster omits or adds incoming origins")
    design, _ = _ref_json(root, core["source_design"], "corrected source design04")
    _validate_historical_bifrost(root, design, contexts, rows)
    return contexts


def load_and_validate(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                      ledger_bytes: bytes | None = None, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False,
                      _runtime_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Invoke the frozen validators and return one lossless read-only context.

    ``before`` calls the actual retained checker API; ``after`` calls the
    actual full checker API.  Both modes call configuration validation with
    ``execute=False``.  A caller-supplied checker/configuration result is
    never accepted as authority.
    """
    require(mode in {"before", "after"}, "mode must be before or after")
    require(isinstance(core, Mapping), "core identity must be an object")
    root = Path(root).resolve()
    require(root.is_dir(), "validation root is not a directory")
    continuation = core.get("continuation")
    require(isinstance(continuation, Mapping),
            "typed continuation context is required; do not infer it from an untyped field")
    require(continuation.get("schema") == "v092-bifrost-v0140-continuation-context/v1",
            "continuation context schema is not the reviewed typed schema")
    if not fixture_only:
        require(set(continuation) == {"schema", "contract", "source_commit", "plan_commit", "source_inputs"},
                "continuation context has an unreviewed field")
    continuation_contract = _ref(continuation.get("contract"), "continuation contract")
    if not fixture_only:
        require(set(continuation_contract) == {"path", "sha256"},
                "continuation contract binding has an unreviewed field")
    continuation_source = _commit(continuation.get("source_commit"), "continuation source_commit")
    continuation_plan = _commit(continuation.get("plan_commit"), "continuation plan_commit")
    inherited_from_context = continuation.get("source_inputs")
    require(isinstance(inherited_from_context, list), "typed continuation source_inputs are missing")
    if not fixture_only:
        require("source_evidence" in core and "source_contexts" in core,
                "production core must bind typed source evidence and source contexts")
        require("runtime_manifest" not in core,
                "runtime_manifest is outside the reviewed core schema and cannot bind this bridge")
    elif "inherited_source_inputs" in core:
        require(core["inherited_source_inputs"] == inherited_from_context,
                "untyped inherited source_inputs differ from the typed continuation context")
    _bound(root, continuation_contract, "continuation contract")
    policy_path = Path(__file__).with_name("bifrost-v0140-replacement-13.py")
    policy_spec = importlib.util.spec_from_file_location("bridge03_window_policy", policy_path)
    require(policy_spec is not None and policy_spec.loader is not None, "no-expiry protocol unavailable")
    policy = importlib.util.module_from_spec(policy_spec)
    policy_spec.loader.exec_module(policy)
    policy.validate_execution_window(root, core)
    policy.validate_working_cap(root, core)
    policy.validate_breadth_first_authority(root, core)
    if not fixture_only:
        policy._validate_historical_prefixes(root, core)
    contract_ref = _ref(core.get("contract"), "canonical contract")
    if not fixture_only:
        require(set(contract_ref) == {"path", "sha256"},
                "canonical contract binding has an unreviewed field")
    source_commit = _commit(core.get("source_commit"), "source_commit")
    plan_commit = _commit(core.get("plan_commit"), "plan_commit")
    _ancestor(root, source_commit, plan_commit, "source to plan")
    head = _git(root, "rev-parse", "HEAD")
    head_tree = _git(root, "rev-parse", f"{head}^{{tree}}")
    _ancestor(root, plan_commit, head, "plan to current HEAD")
    require(fixture_only or head == plan_commit,
            "production validation requires the declared plan commit to be the current HEAD")
    contract_path = root / Path(*_relative(contract_ref["path"], "canonical contract path").parts)
    contract_raw = _bound(root, contract_ref, "canonical contract")
    require(_git_show(root, plan_commit, contract_ref["path"]) == contract_raw,
            "canonical contract bytes differ from its plan-commit Git blob")
    modules = load_dependencies(root, fixture_modules=fixture_modules, fixture_only=fixture_only)
    replacement, executor, checker, configuration = (modules[n] for n in
                                                     ("replacement05", "executor", "checker", "configuration"))
    # Read all immutable inputs needed by the scoped resource adapter before
    # entering the frozen validator.  These reads are repeated below only to
    # keep the result assembly close to its existing boundary; no file is
    # written or normalized.
    early_design_obj, _ = _ref_json(root, core.get("source_design"), "source design")
    if not fixture_only:
        policy_path = Path(__file__).with_name("bifrost-v0140-replacement-13.py")
        policy = _load_module(root, "source_design04_policy", {"path": str(policy_path.relative_to(root)), "sha256": sha256(policy_path.read_bytes())})
        policy.validate_source_design(root, core)
    early_source_ref = core.get("source_evidence") if not fixture_only else core.get(
        "source_evidence", core.get("source_change", core.get("manifest")))
    if isinstance(early_source_ref, dict) and {"path", "sha256"} <= set(early_source_ref):
        early_manifest_obj, _ = _ref_json(root, early_source_ref, "immutable source evidence")
    else:
        require(fixture_only and isinstance(early_source_ref, Mapping),
                "production mode requires an exact immutable source-evidence path/SHA binding")
        early_manifest_obj = dict(early_source_ref)
    early_manifest_obj = dict(early_manifest_obj)
    if not fixture_only:
        require(early_manifest_obj.get("breadth_first_authority") == core["breadth_first_authority"],
                "source evidence omits exact breadth-first authority")
    if not fixture_only:
        require(isinstance(early_manifest_obj.get("source_inputs_delta"), list) and
                isinstance(early_manifest_obj.get("source_contexts"), list),
                "source evidence must bind source_inputs_delta and source_contexts")
        for key in ("runner", "runner_artifact", "runner_environment", "executor_environment",
                    "qualification", "control_review", "contract_delta"):
            if key in core:
                if key in early_manifest_obj:
                    require(early_manifest_obj[key] == core[key],
                            f"source evidence {key} differs from core binding")
                else:
                    early_manifest_obj[key] = copy.deepcopy(core[key])
    for key, expected in (("source_commit", source_commit), ("plan_commit", plan_commit),
                          ("replacement_groups", list(core.get("replacement_groups", [])))):
        if key in early_manifest_obj:
            require(early_manifest_obj[key] == expected,
                    f"source evidence {key} differs from validated identity")
        else:
            early_manifest_obj[key] = expected
    early_prefix_ref = _ref(core.get("continuation_prefix"), "continuation prefix")
    early_original_ref = _ref(core.get("original_prefix"), "original prefix")
    early_original_raw = _bound(root, early_original_ref, "original prefix")
    early_continuation_raw = _bound(root, early_prefix_ref, "continuation prefix")
    early_original_rows = _canonical_rows(early_original_raw, "original prefix")
    early_continuation_rows = _canonical_rows(early_continuation_raw, "continuation prefix")
    require(len(early_original_rows) == HISTORICAL_ROWS and
            len(early_continuation_rows) == core["continuation_prefix"]["rows"] and
            early_continuation_raw.startswith(early_original_raw),
            "prefixes are not the exact immutable 88/actual-incoming-row witnesses")
    if ledger_bytes is None:
        early_ledger_path = core.get("ledger_path", LEDGER_PATH)
        require(fixture_only or early_ledger_path == LEDGER_PATH,
                "production bridge ledger path is not canonical")
        require(isinstance(early_ledger_path, str), "ledger_path must be a relative path")
        early_current_raw = _read(root, early_ledger_path)
    else:
        early_current_raw = ledger_bytes
        if not fixture_only:
            require(early_current_raw == _read(root, LEDGER_PATH),
                    "caller-supplied ledger bytes differ from the live canonical ledger")
    require(early_current_raw.startswith(early_continuation_raw),
            "ledger does not retain the exact immutable actual incoming prefix")
    early_rows = _canonical_rows(early_current_raw, "ledger")
    try:
        if fixture_only:
            validated = executor.validate_plan(contract_path, repo_root=root)
        else:
            validated = _validate_replacement_with_scoped_resource_boundary(
                root, executor, replacement, contract_path, contract_ref, contract_raw, core,
                early_manifest_obj, source_commit, early_rows, early_current_raw,
            )
    except Exception as exc:
        if isinstance(exc, FrozenBridgeError):
            raise
        raise FrozenBridgeError("frozen executor rejected canonical contract") from exc
    require(isinstance(validated, dict) and isinstance(validated.get("plan"), dict),
            "frozen executor returned no complete normalized plan")
    require(validated.get("bytes_sha256") == contract_ref["sha256"],
            "frozen executor returned a different contract digest")
    require(validated.get("plan") == _json(contract_raw, "canonical contract"),
            "frozen normalized plan differs from complete canonical contract")
    require(str(validated.get("path")) == str(contract_path) and
            Path(str(validated.get("repo_root"))).resolve() == root,
            "frozen normalized plan path/root identity differs")
    require(validated.get("plan", {}).get("resource_guards") == {"stop_free_gib": 48, "working_set_gib": 30},
            "normalized replacement aggregate source-working guard differs")
    require(validated.get("total_wall_budget_seconds") is None,
            "frozen normalized plan clock identity differs")
    normalized_groups = validated.get("groups")
    require(isinstance(normalized_groups, list) and len(normalized_groups) == EXPECTED_GROUPS,
            "frozen normalized return omits the complete group roster")
    plan_ids = [item.get("id") for item in validated["plan"].get("groups", [])
                if isinstance(item, Mapping)]
    normalized_ids = [item.get("id") for item in normalized_groups if isinstance(item, Mapping)]
    require(normalized_ids == plan_ids,
            "frozen normalized group roster differs from the complete contract")
    _validate_group_projection(validated["plan"], normalized_groups)
    normalized_binary = _validate_binary_identity(root, core, validated)
    normalized_source_inputs = _validate_normalized_source_inputs(
        executor, validated, root, inherited=None if fixture_only else inherited_from_context)
    shape = _shape(validated["plan"])
    require(validated["plan"].get("source_commit") == source_commit and
            validated["plan"].get("total_wall_budget_seconds") is None,
            "normalized plan source/clock identity differs")
    runner_sha = validated["plan"].get("runner_source_sha256")
    require(isinstance(runner_sha, str) and SHA_RE.fullmatch(runner_sha),
            "normalized plan lacks runner source identity")
    snapshot = getattr(executor, "_assert_source_snapshot", None)
    require(callable(snapshot), "frozen executor source snapshot guard is unavailable")
    design_obj, design_ref = _ref_json(root, core.get("source_design"), "source design")
    source_change_ref = core.get("source_evidence") if not fixture_only else core.get(
        "source_evidence", core.get("source_change", core.get("manifest")))
    if isinstance(source_change_ref, dict) and {"path", "sha256"} <= set(source_change_ref):
        if not fixture_only:
            require(set(source_change_ref) == {"path", "sha256"},
                    "source evidence binding has an unreviewed field")
        manifest_obj, manifest_bound_ref = _ref_json(root, source_change_ref, "immutable source evidence")
    else:
        require(fixture_only and isinstance(source_change_ref, Mapping),
                "production mode requires an exact immutable source-evidence path/SHA binding")
        manifest_obj, manifest_bound_ref = dict(source_change_ref), None
    if not fixture_only:
        require(isinstance(manifest_obj.get("source_inputs_delta"), list) and
                isinstance(manifest_obj.get("source_contexts"), list),
                "source evidence must bind source_inputs_delta and source_contexts")
    # replacement-05's helpers use a manifest-shaped object.  The immutable
    # source-evidence artifact intentionally carries no final runtime wrapper;
    # these identity fields are derived from the actual validated plan/core
    # in memory and never written back into the evidence file.
    manifest_obj = dict(manifest_obj)
    # Source evidence is the immutable delta artifact.  The typed core keeps
    # the reviewed runner/qualification bindings alongside it; copy those
    # fields into the in-memory manifest-shaped object only, never back to the
    # artifact.  This keeps replacement-05's validators lossless without
    # introducing a manifest/self-hash cycle.
    if not fixture_only:
        for key in ("runner", "runner_artifact", "runner_environment", "executor_environment",
                    "qualification", "control_review", "contract_delta"):
            if key in core:
                if key in manifest_obj:
                    require(manifest_obj[key] == core[key],
                            f"source evidence {key} differs from core binding")
                else:
                    manifest_obj[key] = copy.deepcopy(core[key])
    for key, expected in (("source_commit", source_commit), ("plan_commit", plan_commit),
                          ("replacement_groups", list(core.get("replacement_groups", [])))):
        if key in manifest_obj:
            require(manifest_obj[key] == expected, f"source evidence {key} differs from validated identity")
        else:
            manifest_obj[key] = expected
    # The protocol-07 core intentionally has no runtime-manifest field: a
    # final wrapper would create a manifest/admission hash cycle.  The
    # immutable source evidence is the only manifest-shaped input.  For an
    # after-run check, derive the projection from the complete frozen plan and
    # compare it to any projection carried by that immutable evidence.
    runtime_manifest_obj = manifest_obj
    runtime_manifest_ref = manifest_bound_ref
    # Partial selected projection is derived from actual terminal rows below;
    # no speculative full84 projection is accepted as measured evidence.
    baseline = continuation_source
    if fixture_only and "continuation_source_commit" in core:
        require(core["continuation_source_commit"] == baseline,
                "legacy continuation_source_commit differs from typed context")
    if baseline is None:
        baseline = manifest_obj.get("source_delta_baseline")
    baseline = _commit(baseline, "source-delta baseline")
    try:
        delta = (replacement._source_delta(root, design_obj, manifest_obj, baseline, source_commit)
                 if fixture_only else _source_delta05(root, design_obj, manifest_obj, baseline, source_commit,
                                      incoming_plan=core["continuation"]["plan_commit"]))
        inherited = inherited_from_context
        input_summary = replacement._source_inputs(root, executor, inherited, validated["plan"],
                                                   manifest_obj, source_commit)
        snapshot(root, source_commit, runner_sha, normalized_source_inputs)
        # The frozen replacement-05 convenience wrapper compares its
        # ``validate_plan`` path return to a Path object.  The actual frozen
        # executor returns the canonical path as a string, so use the frozen
        # validator directly here and preserve its complete return object.
        replacement_validated = validated if not fixture_only else executor.validate_plan(
            contract_path, repo_root=root)
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError("replacement-05 source/normalized-plan boundary rejected context") from exc
    require(isinstance(replacement_validated, dict) and isinstance(replacement_validated.get("plan"), dict),
            "replacement-05 returned no complete replacement normalized plan")
    prefix_ref = _ref(core.get("continuation_prefix"), "continuation prefix")
    original_ref = _ref(core.get("original_prefix"), "original prefix")
    original_raw = _bound(root, original_ref, "original prefix")
    continuation_raw = _bound(root, prefix_ref, "continuation prefix")
    original_rows = _canonical_rows(original_raw, "original prefix")
    continuation_rows = _canonical_rows(continuation_raw, "continuation prefix")
    require(len(original_rows) == HISTORICAL_ROWS and len(continuation_rows) == core["continuation_prefix"]["rows"],
            "prefixes must be the exact 88-row historical and actual incoming continuation witnesses")
    require(continuation_raw.startswith(original_raw), "actual incoming prefix does not retain exact 88-row bytes")
    if ledger_bytes is None:
        ledger_path = core.get("ledger_path", LEDGER_PATH)
        if not fixture_only:
            require(ledger_path == LEDGER_PATH, "production bridge ledger path is not canonical")
        require(isinstance(ledger_path, str), "ledger_path must be a relative path")
        current_raw = _read(root, ledger_path)
    else:
        current_raw = ledger_bytes
        if not fixture_only:
            require(current_raw == _read(root, LEDGER_PATH),
                    "caller-supplied ledger bytes differ from the live canonical ledger")
    require(current_raw.startswith(continuation_raw), "ledger does not retain the exact immutable actual incoming prefix")
    rows = _canonical_rows(current_raw, "ledger")
    contexts = _load_contexts(root, executor, core, replacement, replacement_validated, contract_ref,
                              source_commit, plan_commit, manifest_obj, rows=rows, raw=current_raw,
                              fixture_only=fixture_only)
    if not fixture_only:
        roles = {item.get("role") for item in contexts.values() if isinstance(item, Mapping)}
        require({"base", "continuation", "replacement"} <= roles,
                "production source_contexts must retain base, continuation, and replacement roles")
        derived_replacement_ids = [group.get("id") for group in validated["plan"].get("groups", [])
                                   if isinstance(group, Mapping) and group.get("tool") == "bifrost"]
        require(core.get("replacement_groups") == derived_replacement_ids,
                "replacement group subset is not derived from the complete frozen plan")
        continuation_contexts = [value for value in contexts.values()
                                 if isinstance(value, Mapping) and value.get("role") == "continuation"]
        require(len(continuation_contexts) == 1,
                "production context map must contain one typed continuation context")
        inherited_plan = continuation_contexts[0].get("validated", {}).get("plan")
        require(isinstance(inherited_plan, dict), "typed continuation context has no complete plan")
        try:
            replacement._contract_delta(inherited_plan, validated["plan"], manifest_obj,
                                        derived_replacement_ids)
        except Exception as exc:
            raise FrozenBridgeError("replacement-05 contract delta rejected the frozen replacement") from exc
        runner = manifest_obj.get("runner")
        require(isinstance(runner, dict) and validated["plan"].get("tools", {}).get("runner") == runner,
                "replacement runner identity is not bound by source evidence/core")
        bifrost_envs = [group.get("environment") for group in validated["plan"].get("groups", [])
                        if isinstance(group, Mapping) and group.get("id") in derived_replacement_ids]
        require(bifrost_envs and isinstance(bifrost_envs[0], dict) and
                all(environment == bifrost_envs[0] for environment in bifrost_envs),
                "replacement Bifrost groups do not share one exact environment")
        try:
            replacement._validate_runner_binding(root, manifest_obj, runner, validated["plan"],
                                                 source_commit, bifrost_envs[0])
            qualified = replacement._validate_qualification(root, manifest_obj.get("qualification"),
                                                             derived_replacement_ids)
        except Exception as exc:
            raise FrozenBridgeError("replacement-05 runner or qualification binding rejected the plan") from exc
        require(validated["plan"].get("qualifications", {}).get("bifrost", {}).get("evidence") ==
                manifest_obj.get("qualification"),
                "replacement plan qualification does not bind the exact reviewed evidence")
    else:
        qualified = None
    try:
        replacement._check_rows_context(rows, contexts, contract_ref["sha256"], source_commit, plan_commit,
                                         len(continuation_rows))
    except Exception as exc:
        raise FrozenBridgeError("replacement-05 row-context checker rejected ledger authority") from exc
    mixed_context = {
        "root": root, "manifest": runtime_manifest_obj,
        "manifest_sha256": runtime_manifest_ref["sha256"] if runtime_manifest_ref else None,
        "source_commit": source_commit, "plan_commit": plan_commit,
        "prefix": continuation_rows, "prefix_raw": continuation_raw, "rows": rows,
        "contexts": contexts,
        "continuation": {"contract_ref": continuation_contract,
                          "source_commit": continuation_source, "plan_commit": continuation_plan},
        "base": next((value for value in contexts.values() if value.get("role") == "base"),
                      contexts[contract_ref["sha256"]]),
        "repaired": next((value for value in contexts.values() if value.get("role") == "continuation"),
                          contexts[contract_ref["sha256"]]),
        "validated": replacement_validated, "executor": executor, "checker": checker,
        "configuration": configuration,
        "ids": list(core.get("replacement_groups", [])),
        "contract": validated["plan"], "contract_raw": contract_raw,
        "contract_sha256": contract_ref["sha256"], "source_delta": delta,
        "source_inputs_summary": input_summary,
    }
    try:
        if mode == "before":
            checker_result = _call_mixed(replacement, mixed_context, rows, final=False, fixture_only=fixture_only)
        else:
            checker_result = _call_mixed(replacement, mixed_context, rows, final=True, fixture_only=fixture_only)
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError(f"actual {mode} checker rejected context") from exc
    require(isinstance(checker_result, Mapping), "actual checker returned no structured result")
    output = core.get("configuration_output")
    require(isinstance(output, str), "configuration_output is required for execute=False validation")
    _relative(output, "configuration output namespace")
    if not fixture_only and checker_result.get("full_release_gate_satisfied") is not True:
        # The retained-prefix adapter deliberately returns a preflight result;
        # the frozen configuration validator requires the complete 84/92/4252
        # matrix and must not be fed a counts-only or projected summary.
        configuration_result = {
            "status": "configuration-pending-complete-matrix",
            "reason": "execute=False configuration validation requires after-run full replay",
        }
    else:
        selected = _mixed_selected(mixed_context, rows, final=(mode == "after"))
        configuration_summary = checker_result
        if not fixture_only:
            configuration_summary = _configuration_checker_summary(
                root, checker_result, selected, validated, fixture_only=False)
        configuration_result = _call_configuration(
            configuration, checker, executor, root, contract_path, output, validated,
            configuration_summary,
        )
    require(isinstance(configuration_result, Mapping),
            "actual configuration validator returned no structured result")
    shape_result = _jsonable(checker_result)
    loaded = {"replacement05": REPLACEMENT05, **FROZEN}
    if not fixture_only:
        incoming_seal = _json(_bound(root, core["incoming_history"], "incoming seal"), "incoming seal")
        loaded["incoming_recovery"] = incoming_seal["recovery_module"]
    result: dict[str, Any] = {
        "schema": SCHEMA, "status": "read-only-frozen-validation-passed",
        "execution_authorized": False,
        "mode": mode, "validation_root": str(root),
        "frozen_dependency_refs_and_loaded_byte_hashes": {
            name: {"path": ref["path"], "sha256": ref["sha256"], "loaded": True}
            for name, ref in loaded.items()
        },
        "validation_root_path_and_git_tree_identity": {"path": str(root), "head": head,
                                                         "head_tree": head_tree,
                                                         "source_commit": source_commit,
                                                         "plan_commit": plan_commit},
        "canonical_contract_path_and_contract_sha256": contract_ref,
        "binary_identity_bound_to_normalized_plan": normalized_binary,
        "source_commit": source_commit, "plan_commit": plan_commit,
        "validated_full_normalized_plan": _jsonable(validated),
        "validated_full_plan_digest": sha256(canonical_json(_jsonable(validated["plan"]))),
        "validated_full_return_digest": sha256(canonical_json(_jsonable(validated))),
        "replacement_validated_normalized_plan": _jsonable(replacement_validated),
        "validated_source_inputs_and_source_snapshot_summary": _jsonable(input_summary),
        "source_delta": _jsonable(delta),
        "source_design": {"ref": design_ref, "value": _jsonable(design_obj)},
        "source_closure_digest": sha256(canonical_json(_jsonable(normalized_source_inputs))),
        "historical_context_map_keyed_by_contract_sha256": _jsonable(contexts),
        "original_prefix_ref": original_ref, "continuation_prefix_ref": prefix_ref,
        "ledger_sha256": sha256(current_raw), "ledger_rows": len(rows),
        "exact_replacement_group_subset_derived_from_full_plan": list(core.get("replacement_groups", [])),
        "normalized_shape": shape, "checker_summary_or_pending": shape_result,
        "configuration_execute_false_summary_or_pending": _jsonable(configuration_result),
        "source_evidence_ref": manifest_bound_ref,
        # Kept as a descriptive compatibility field for bridge-01 consumers;
        # production input parsing accepts only the typed source_evidence key.
        "source_change_ref": manifest_bound_ref,
        "runtime_manifest_ref": runtime_manifest_ref,
        "qualification_summary": _jsonable(qualified),
        "unimplemented_boundaries": ["execute", "admit", "materialize", "replay", "dispatch",
                                      "write_phase_gate", "write_completion"],
    }
    derived = [group.get("id") for group in validated["plan"].get("groups", [])
               if isinstance(group, dict) and group.get("tool") == "bifrost"]
    require(result["exact_replacement_group_subset_derived_from_full_plan"] == derived,
            "replacement group subset is not derived from the complete normalized plan")
    unsigned = copy.deepcopy(result)
    result["context_digest"] = sha256(canonical_json(unsigned))
    if _runtime_sink is not None:
        require(isinstance(_runtime_sink, list) and not _runtime_sink,
                "runtime sink must be a fresh private list")
        _runtime_sink.append({
            "modules": modules,
            # The runtime consumer needs the exact object retained by the
            # mixed context.  Production keeps this identical to the frozen
            # return; the fixture seam may return a distinct but independently
            # validated object for its second harmless call.
            "validated": mixed_context["validated"],
            "replacement_validated": replacement_validated,
            "mixed_context": mixed_context,
            "checker_summary": checker_result,
            "configuration_summary": configuration_result,
        })
    return result


def load_runtime_context(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                         ledger_bytes: bytes | None = None,
                         fixture_modules: Mapping[str, Any] | None = None,
                         fixture_only: bool = False,
                         stdlib_importlib: Any | None = None) -> dict[str, Any]:
    """Return the same validation result with its live in-process objects.

    The diagnostic returned by :func:`load_and_validate` is JSON-safe and is
    suitable for the immutable bridge context.  Runtime callers also need
    ``Path`` values, module objects, and the actual historical context map;
    reloading those from the serialized diagnostic would silently turn them
    into untrusted data.  This entry point therefore invokes the exact
    validation path once, captures its private in-memory objects, and returns
    them alongside the independently computed diagnostic.  It performs no
    writes and never accepts a caller-supplied serialized context as authority.
    """
    sink: list[dict[str, Any]] = []
    diagnostic = load_and_validate(
        root, core, mode=mode, ledger_bytes=ledger_bytes,
        fixture_modules=fixture_modules, fixture_only=fixture_only,
        _runtime_sink=sink,
    )
    require(len(sink) == 1, "frozen bridge did not return one private runtime context")
    runtime = sink[0]
    modules = runtime.get("modules")
    require(isinstance(modules, Mapping) and
            set(modules) == {"replacement05", "executor", "checker", "configuration"},
            "frozen bridge runtime module roster is incomplete")
    validated = runtime.get("validated")
    mixed_context = runtime.get("mixed_context")
    checker_summary = runtime.get("checker_summary")
    configuration_summary = runtime.get("configuration_summary")
    require(isinstance(validated, Mapping) and isinstance(validated.get("plan"), Mapping),
            "frozen bridge runtime result lacks the normalized plan")
    require(isinstance(mixed_context, dict) and mixed_context.get("validated") is validated,
            "frozen bridge runtime context does not retain the validated object")
    require(isinstance(checker_summary, Mapping),
            "frozen bridge runtime result lacks the actual checker summary")
    require(isinstance(configuration_summary, Mapping),
            "frozen bridge runtime result lacks the configuration result")
    return {
        "schema": "v092-bifrost-v0140-runtime-context/v1",
        "lossless_runtime_objects": True,
        "mode": mode,
        "modules": dict(modules),
        "validated": validated,
        "replacement_validated": runtime.get("replacement_validated"),
        "mixed_context": mixed_context,
        "checker_summary": checker_summary,
        "configuration_summary": configuration_summary,
        # This is generated by this call, never loaded from a caller.  It is
        # a diagnostic binding for consumers that also need the immutable
        # context digest, not the source of runtime authority.
        "bridge_context": diagnostic,
    }


def validate_frozen_bridge(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the reviewed bridge API."""
    return load_and_validate(*args, **kwargs)


def _unsupported(operation: str) -> None:
    raise FrozenBridgeUnsupported(f"{operation} is intentionally unavailable in the read-only frozen bridge")


def execute(*args: Any, **kwargs: Any) -> None: _unsupported("execute")
def admit(*args: Any, **kwargs: Any) -> None: _unsupported("admit")
def materialize(*args: Any, **kwargs: Any) -> None: _unsupported("materialize")
def replay(*args: Any, **kwargs: Any) -> None: _unsupported("replay")
def dispatch(*args: Any, **kwargs: Any) -> None: _unsupported("dispatch")
def build_group_command(*args: Any, **kwargs: Any) -> None: _unsupported("build_group_command")
def run_groups(*args: Any, **kwargs: Any) -> None: _unsupported("run_groups")
def write_phase_gate(*args: Any, **kwargs: Any) -> None: _unsupported("write_phase_gate")
def write_completion(*args: Any, **kwargs: Any) -> None: _unsupported("write_completion")


if __name__ == "__main__":
    raise FrozenBridgeUnsupported("CLI execution is unavailable; call load_and_validate from a reviewed caller")

# ---------------------------------------------------------------------------
# BF14 graph-owned stage runtime successor
# ---------------------------------------------------------------------------
# The copied v7 implementation above remains available for its historical
# fixture tests.  The functions below are the successor path.  They do not
# import a graph member by path: callers pass the already pinned graph and all
# frozen objects come from that graph.  The JSON diagnostic is a compact
# binding only; opaque checker/executor objects stay in-process.

STAGE_RUNTIME_SCHEMA = "v092-bifrost-v0140-runtime-context/v1"
STAGE_GRAPH_ROLES = (
    "bridge12", "replacement17", "executor", "checker", "configuration",
    "incoming_recovery", "policy_source", "policy_runtime", "protocol17",
    "admission17", "supervisor17",
)

# The frozen helpers pass import names that differ from the sealed graph role
# names.  These are explicit reviewed routes; a requested name absent here is
# rejected even when another member happens to share its path or SHA.
STAGE_LOADER_ROUTE_NAMES = {
    "codeql_terminal_history_03": "incoming_predecessor03",
    "historical-replay-helper": "incoming_historical_replay_helper05",
    "historical-previous-helper": "incoming_historical_previous_helper01",
    "codeql_pending_executor": "incoming_nested_executor",
    "codeql_pending_checker": "incoming_nested_checker",
    "codeql_pending_configuration": "incoming_nested_configuration",
    "codeql_pending_disk_guard": "disk_guard",
    "replacement-14 protocol": "protocol17",
    "frozen bridge": "bridge12",
    "terminal disk guard": "disk_guard",
    "joern_capability_continuation_01_historical": "incoming_historical_previous_helper01",
    "joern_capability_repair_continuation_shim": "incoming_historical_replay_helper05",
    "joern_continuation_repair_shim": "incoming_historical_replay_helper05",
    "joern_continuation_disk_guard": "disk_guard",
    "execute_release_v092_for_checker": "incoming_nested_executor",
    "v092_resource_recovery_for_checker": "incoming_nested_resource_recovery",
    "v092_scoped_recovery_for_checker": "incoming_nested_scoped_recovery",
    "check_release_v092_for_config_validation": "incoming_nested_checker",
    "v092_scoped_recovery_packet": "incoming_nested_scoped_recovery",
    "check_release_v092_scoped_replay": "incoming_nested_checker",
    "v092_resource_recovery": "incoming_nested_resource_recovery",
    "check_release_v092_resource_replay": "incoming_nested_checker",
    "v092_disk_guard_runtime": "disk_guard",
}
OLD_POLICY_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py"
OLD_POLICY_SHA256 = "6fdc08000f673b5ac904aeb315be7dfa174747e31d7ff2f32b4090b161253842"


def _stage_member(graph: Any, name: str) -> Any:
    require(graph is not None and callable(getattr(graph, "module", None)),
            "stage runtime requires a pinned graph")
    try:
        value = graph.module(name)
    except Exception as exc:
        raise FrozenBridgeError(f"stage graph omits {name}") from exc
    require(value is not None, f"stage graph member {name} is empty")
    return value


def _stage_source_sha(graph: Any, name: str) -> str:
    for member in getattr(graph, "members", ()):
        if getattr(member, "name", None) == name:
            value = getattr(member, "source_sha256", None)
            require(isinstance(value, str) and SHA_RE.fullmatch(value),
                    f"stage graph source digest is invalid for {name}")
            return value
    raise FrozenBridgeError(f"stage graph omits source digest role {name}")


def _stage_modules(graph: Any, *, require_legacy: bool = True) -> dict[str, Any]:
    names = {getattr(member, "name", "") for member in getattr(graph, "members", ())}
    require(set(STAGE_GRAPH_ROLES) <= names, "stage graph omits a required runtime role")
    modules = {name: _stage_member(graph, name) for name in STAGE_GRAPH_ROLES}
    # The protocol-14 member is the static packet validator.  The copied
    # bridge08 runtime still needs the reviewed replacement-05 validator
    # exports (_contract_delta, _checker_context, and the exact C4 adapter).
    # A complete production graph therefore carries that validator as an
    # explicit extra instance.  The fixture graph may expose it under the
    # retained replacement17 slot, but only when it really has every frozen
    # runtime export; a protocol-only object must fail closed.
    legacy = None
    if "replacement05" in names:
        legacy = _stage_member(graph, "replacement05")
    elif all(callable(getattr(modules["replacement17"], name, None)) for name in (
            "_contract_delta", "_source_inputs", "_context_map", "_check_rows_context")):
        legacy = modules["replacement17"]
    if require_legacy:
        require(legacy is not None, "stage graph omits the reviewed replacement-05 runtime validator")
        modules["replacement05"] = legacy
    else:
        # The fixture branch intentionally mirrors the old graph test's
        # four-object identity seam; it is unreachable from production graphs.
        modules["replacement05"] = modules["replacement17"]
    if "stage_runtime04" in names:
        require(_stage_member(graph, "stage_runtime04") is sys.modules.get(__name__),
                "stage-runtime graph member is a foreign module instance")
    return modules


def _stage_manifest(core: Mapping[str, Any]) -> dict[str, str]:
    value = core.get("manifest_ref", core.get("manifest"))
    if not isinstance(value, Mapping):
        path = core.get("manifest_path")
        require(isinstance(path, str), "stage core has no manifest binding")
        # The protocol static core intentionally carries the manifest path,
        # while its SHA is checked by validate_static.  The stage computes the
        # same bytes only after the path has passed the regular-file boundary.
        _relative(path, "stage manifest path")
        return {"path": path, "sha256": ""}
    return _ref(value, "stage manifest")


def _stage_contract(core: Mapping[str, Any], static: Mapping[str, Any]) -> dict[str, str]:
    value = core.get("contract")
    if not isinstance(value, Mapping) and isinstance(static.get("core"), Mapping):
        value = static["core"].get("contract")
    return _ref(value, "stage contract")


def _stage_validate_plan(executor: Any, root: Path, contract_path: Path) -> Mapping[str, Any]:
    method = getattr(executor, "validate_plan", None)
    require(callable(method), "pinned executor lacks validate_plan")
    parameters = inspect.signature(method).parameters
    if "repo_root" in parameters:
        value = method(contract_path, repo_root=root)
    else:
        value = method(contract_path, root)
    require(isinstance(value, Mapping), "frozen executor returned no normalized plan")
    return value


def _stage_incoming(provider: Any, root: Path, core: Mapping[str, Any], graph: Any,
                    mode: str, ledger_bytes: bytes | None) -> Mapping[str, Any]:
    loader = getattr(provider, "load_runtime_context", None)
    if callable(loader):
        kwargs = {"root": root, "core": core, "graph": graph,
                  "mode": mode, "ledger_bytes": ledger_bytes}
        try:
            params = inspect.signature(loader).parameters
            if not any(item.kind is inspect.Parameter.VAR_KEYWORD for item in params.values()):
                kwargs = {key: value for key, value in kwargs.items() if key in params}
        except (TypeError, ValueError) as exc:
            raise FrozenBridgeError("incoming provider has no inspectable loader") from exc
        value = loader(**kwargs)
        require(isinstance(value, Mapping), "incoming provider returned no runtime mapping")
        return value
    recover = getattr(provider, "recover_bifrost_history", None)
    require(callable(recover), "incoming provider lacks actual recovery export")
    seal_ref = core.get("incoming_history")
    require(isinstance(seal_ref, Mapping), "core lacks incoming history seal")
    seal = _json(_bound(root, seal_ref, "incoming history seal"), "incoming history seal")
    manifest = _ref(seal.get("recovery_manifest"), "incoming recovery manifest")
    prefix = _bound(root, core.get("continuation_prefix"), "incoming continuation prefix")
    value = recover(root, manifest["path"], manifest["sha256"], prefix)
    require(isinstance(value, Mapping) and
            {"base", "contexts", "repaired", "prefix_sha256"} <= set(value),
            "incoming recovery mapping is incomplete")
    require(value["prefix_sha256"] == sha256(prefix), "incoming recovery prefix differs")
    return value


def _stage_ledger(root: Path, core: Mapping[str, Any], ledger_bytes: bytes | None) -> tuple[bytes, list[dict[str, Any]]]:
    raw = ledger_bytes if ledger_bytes is not None else _read(root, core.get("ledger_path", LEDGER_PATH))
    require(isinstance(raw, bytes), "stage ledger is not raw bytes")
    return raw, _canonical_rows(raw, "stage ledger")


def _stage_module_for_route(root: Path, graph: Any, actual_root: Path,
                            relative: str, name: str, expected: str | None = None) -> Any:
    """Resolve one loader request by explicit name, path, and graph digest.

    Several historical modules independently load the same source path.  A
    path-only lookup would silently select whichever instance happened to be
    listed first, so every request must resolve through the reviewed route
    table (or an exact graph member name) and then match the requested path.
    """
    require(Path(actual_root).resolve() == root.resolve(),
            "nested loader escaped the bound graph root")
    relative_path = _relative(relative, "nested loader path").as_posix()
    route_name = STAGE_LOADER_ROUTE_NAMES.get(name, name)
    candidates = [member for member in getattr(graph, "members", ())
                  if getattr(member, "name", None) == route_name]
    require(len(candidates) == 1,
            f"nested loader route is not explicitly bound: {name}")
    member = candidates[0]
    require(getattr(member, "canonical_path", None) == relative_path,
            f"nested loader route path differs: {name} -> {relative_path}")
    source_sha = getattr(member, "source_sha256", None)
    require(isinstance(source_sha, str) and SHA_RE.fullmatch(source_sha),
            f"nested loader route has no source digest: {name}")
    if expected is not None:
        require(expected == source_sha,
                f"nested loader route digest differs: {name}")
    _bound(root, {"path": relative_path, "sha256": source_sha},
           f"nested runtime source {name}")
    module = getattr(member, "module_object", None)
    require(module is not None, f"nested loader route has no module: {name}")
    return module


class _StagePinnedModuleLoader:
    """A no-reexecution loader for one already sealed graph module.

    The historical provider calls ``module_from_spec`` for its predecessor
    and helper modules.  Returning a fresh module there would silently create
    a second validator graph.  This loader returns the exact graph object and
    makes ``exec_module`` a checked no-op.  The surrounding importlib proxy is
    installed on the importing module only; the stdlib importlib object is
    never mutated.
    """

    def __init__(self, member: Any) -> None:
        self.member = member

    def create_module(self, spec: Any) -> Any:
        return self.member.module_object

    def exec_module(self, module: Any) -> None:
        require(module is self.member.module_object,
                "pinned nested loader received a foreign module object")


class _StageInvocationBinding:
    """Identity-bound evidence for one real reader-scope invocation.

    The two frozen context managers create their factory and proxy classes
    locally.  This object deliberately retains those concrete objects rather
    than accepting a class name, qualname, or source-shaped substitute.
    """

    __slots__ = (
        "route", "owner", "helper", "generator", "factory_function",
        "previous_factory", "wrapper_class", "raw_sha256", "selector",
        "nonce", "facade", "depth", "target_snapshots", "active",
        "factory_closure", "helper_closure",
    )

    def __init__(self, *, route, owner, helper, generator, factory_function,
                 previous_factory, wrapper_class, raw_sha256, selector, nonce,
                 facade, depth, factory_closure, helper_closure):
        self.route = route
        self.owner = owner
        self.helper = helper
        self.generator = generator
        self.factory_function = factory_function
        self.previous_factory = previous_factory
        self.wrapper_class = wrapper_class
        self.raw_sha256 = raw_sha256
        self.selector = selector
        self.nonce = nonce
        self.facade = facade
        self.depth = depth
        self.target_snapshots = []
        self.active = True
        self.factory_closure = factory_closure
        self.helper_closure = helper_closure


def _stage_invocation_closure(fn: Any) -> dict[str, Any]:
    code = getattr(fn, "__code__", None)
    closure = getattr(fn, "__closure__", None)
    require(code is not None and closure is not None,
            "reader-scope factory has no inspectable closure")
    require(len(code.co_freevars) == len(closure),
            "reader-scope factory closure metadata is inconsistent")
    values = {}
    for name, cell in zip(code.co_freevars, closure):
        try:
            values[name] = cell.cell_contents
        except ValueError as exc:
            raise FrozenBridgeError("reader-scope factory contains an empty closure cell") from exc
    return values


def _stage_code_digest(fn: Any) -> str:
    code = getattr(fn, "__code__", None)
    require(code is not None, "reader-scope object has no code object")
    return sha256(marshal.dumps(code))


_STAGE_MISSING = object()


class _StageSpecRecord:
    __slots__ = ("spec", "kind", "name", "path", "sha256", "target", "loader", "factory", "origin", "decorator_binding")

    def __init__(self, spec, kind, name, path, sha256_value, target, loader, factory):
        self.spec = spec
        self.kind = kind
        self.name = name
        self.path = path
        self.sha256 = sha256_value
        self.target = target
        self.loader = loader
        self.factory = factory
        self.origin = getattr(spec, "origin", None)
        self.decorator_binding = None


class _StageImportFactory:
    """One paired stdlib spec/module factory for one sealed graph scope.

    GraphImportContext owns its private ``_GraphSpec`` pair.  This pair is for
    the copied legacy body, whose callers request ordinary ModuleSpec objects.
    The two pairs never accept one another's specs.  The standard-library
    functions are supplied by the host bridge before a GraphImportlibFacade is
    installed in any graph member; reading the current module global here would
    recreate the BF15 foreign-spec failure.
    """

    _POLICY_NAMES = frozenset({
        "bridge03_window_policy", "bridge06_incoming_policy",
        "v092_frozen_bridge_02_source_design04_policy",
    })

    def __init__(self, root, graph, stdlib_importlib, *, policy_path, policy):
        require(stdlib_importlib is not None, "host did not provide stdlib importlib")
        require(not getattr(stdlib_importlib, "_stage_pinned_graph", False),
                "host stdlib importlib is a graph facade")
        util = getattr(stdlib_importlib, "util", None)
        machinery = getattr(stdlib_importlib, "machinery", None)
        require(util is not None and machinery is not None,
                "host stdlib importlib primitives are incomplete")
        self.root = Path(root).resolve()
        self.graph = graph
        self.stdlib = stdlib_importlib
        self.std_spec_from_file_location = getattr(util, "spec_from_file_location", None)
        self.std_module_from_spec = getattr(util, "module_from_spec", None)
        self.std_module_spec = getattr(machinery, "ModuleSpec", None)
        require(callable(self.std_spec_from_file_location) and
                callable(self.std_module_from_spec) and callable(self.std_module_spec),
                "host stdlib importlib pair is not callable")
        self.policy_path = PurePosixPath(policy_path).as_posix()
        self.policy = policy
        self.factory_nonce = object()
        self.records = []
        self.invocations = []
        self.bound_raw_sha256 = set()
        self._facade = None
        self.by_name = {}
        for member in getattr(graph, "members", ()):
            name = getattr(member, "name", None)
            path = getattr(member, "canonical_path", None)
            require(isinstance(name, str) and name and name not in self.by_name,
                    f"stage factory graph route name is not unique: {name}")
            require(isinstance(path, str) and path, "stage factory graph route path is missing")
            self.by_name[name] = member

    def _register(self, spec, kind, name, path, target, loader):
        relative = PurePosixPath(path).as_posix()
        # Keep the source binding on the registration itself.  Graph modules
        # intentionally do not expose a mutable ``source_sha256`` attribute,
        # so derive it from the stage-owned regular file while the spec is
        # created rather than trusting a module field.
        source_sha = sha256(_read(self.root, relative))
        require(not relative.startswith("/"), "stage factory route path is absolute")
        record = _StageSpecRecord(spec, kind, name, relative,
                                  source_sha, target,
                                  loader, self)
        self.records.append(record)  # retain the spec strongly; id reuse is impossible
        return spec

    def _standard_spec(self, name, path, loader):
        spec = self.std_spec_from_file_location(
            name, self.root / path, loader=loader)
        require(spec is not None and isinstance(spec, self.std_module_spec),
                "host stdlib factory returned no standard ModuleSpec")
        require(spec.loader is loader and spec.name == name,
                "host stdlib factory changed the reviewed loader metadata")
        return spec

    def _graph_member(self, name, path):
        member = self.by_name.get(name)
        if member is None:
            mapped = STAGE_LOADER_ROUTE_NAMES.get(name)
            member = self.by_name.get(mapped) if mapped is not None else None
        require(member is not None and getattr(member, "canonical_path", None) == path,
                f"stage graph route is not explicitly bound: {name} -> {path}")
        _bound(self.root, {"path": path, "sha256": member.source_sha256},
               f"stage graph source {name}")
        return member

    def spec_from_file_location(self, name, location, *args, **kwargs):
        require(isinstance(name, str) and name and not args and not kwargs,
                "stage factory loader options are not reviewed")
        path = Path(location).resolve()
        require(path.is_relative_to(self.root), "stage factory loader escaped the graph root")
        relative = path.relative_to(self.root).as_posix()
        if relative == self.policy_path:
            require(name in self._POLICY_NAMES,
                    f"unregistered historical policy selector: {name}")
            raw = _read(self.root, self.policy_path)
            require(sha256(raw) == OLD_POLICY_SHA256,
                    "historical policy source changed")
            loader = _StagePolicyProxyLoader(self.policy)
            spec = self._standard_spec(name, relative, loader)
            return self._register(spec, "historical-policy", name, relative,
                                  self.policy, loader)
        member = self._graph_member(name, relative)
        loader = _StagePinnedModuleLoader(member)
        spec = self._standard_spec(name, relative, loader)
        return self._register(spec, "graph-pinned", name, relative,
                              member.module_object, loader)

    def _record(self, spec):
        matches = [record for record in self.records if record.spec is spec]
        require(len(matches) == 1, "foreign or detached stage loader spec")
        record = matches[0]
        require(record.factory is self, "stage loader spec belongs to another factory")
        require(getattr(spec, "name", None) == record.name,
                "stage loader spec selector changed")
        origin = getattr(spec, "origin", None)
        require(origin == record.origin,
                "stage loader spec origin changed")
        origin_path = Path(origin).resolve() if isinstance(origin, str) else None
        require(origin_path == (self.root / Path(*PurePosixPath(record.path).parts)).resolve(),
                "stage loader spec path changed")
        require(sha256(_read(self.root, record.path)) == record.sha256,
                "stage loader source digest changed")
        if record.kind == "graph-pinned":
            member = self.by_name.get(record.name)
            if member is None:
                member = self.by_name.get(STAGE_LOADER_ROUTE_NAMES.get(record.name, record.name))
            require(member is not None and getattr(record.loader, "member", None) is member,
                    "stage loader target route changed")
            require(getattr(member, "canonical_path", None) == record.path and
                    getattr(member, "source_sha256", None) == record.sha256,
                    "stage loader target source binding changed")
            require(record.target is getattr(member, "module_object", None),
                    "stage loader target module changed")
            target_file_value = getattr(record.target, "__file__", None)
            if target_file_value:
                target_file = Path(target_file_value).resolve()
                require(target_file == (self.root / Path(*PurePosixPath(record.path).parts)).resolve(),
                        "stage loader target file changed")
        if spec.loader is not record.loader:
            self._accept_decorated_loader(record, spec.loader)
        return record

    def _active_invocation(self, route: str, selector: str) -> _StageInvocationBinding:
        matches = [item for item in self.invocations
                   if item.active and item.route == route and item.selector == selector]
        require(len(matches) == 1,
                f"decorated loader has no unique active {route} invocation")
        binding = matches[0]
        require(binding.nonce is self.factory_nonce,
                "decorated loader belongs to another stage nonce")
        return binding

    def register_invocation(self, *, route: str, owner: Any, helper: Any,
                            generator: Any, factory_function: Any,
                            previous_factory: Any, wrapper_class: Any,
                            raw: bytes, selector: str, facade: Any) -> _StageInvocationBinding:
        require(owner is not None and getattr(owner, "__dict__", None) is
                getattr(factory_function, "__globals__", None),
                "reader-scope factory globals are not the owner module dictionary")
        require(getattr(helper, "__wrapped__", None) is generator,
                "reader-scope helper/generator identity changed")
        require(getattr(generator, "__globals__", None) is owner.__dict__,
                "reader-scope generator globals belong to another module")
        require(getattr(factory_function, "__globals__", None) is owner.__dict__,
                "reader-scope factory globals belong to another module")
        expected = {"codeql-resource": ("v092_resource_recovery", "_LoaderProxy"),
                    "provider-nested": ("v092_scoped_recovery_packet", "_NestedLoader")}
        require(route in expected, "unknown reader-scope invocation route")
        expected_selector, class_cell_name = expected[route]
        require(selector == expected_selector,
                "reader-scope invocation selector is not route-bound")
        helper_code = getattr(helper, "__code__", None)
        helper_closure = getattr(helper, "__closure__", None)
        require(helper_code is not None and tuple(helper_code.co_freevars) == ("func",) and
                helper_closure is not None and len(helper_closure) == 1 and
                helper_closure[0].cell_contents is generator,
                "reader-scope helper closure is not the exact contextlib binding")
        factory_code = getattr(factory_function, "__code__", None)
        factory_closure = getattr(factory_function, "__closure__", None)
        require(factory_code is not None and
                tuple(factory_code.co_freevars) == (class_cell_name, "original_factory") and
                factory_closure is not None and len(factory_closure) == 2,
                "reader-scope factory closure tuple is not route-bound")
        cells = _stage_invocation_closure(factory_function)
        require("original_factory" in cells and class_cell_name in cells,
                "reader-scope factory closure omitted reviewed bindings")
        require(cells["original_factory"] is previous_factory,
                "reader-scope factory delegate order changed")
        wrapper_class = cells[class_cell_name]
        require(isinstance(wrapper_class, type),
                "reader-scope factory closure did not produce a class")
        require(getattr(wrapper_class, "__module__", None) == owner.__name__,
                "reader-scope wrapper class belongs to another module")
        factory_code_file = Path(factory_function.__code__.co_filename)
        owner_source = Path(getattr(owner, "__file__", "")).resolve()
        if not factory_code_file.is_absolute():
            factory_code_file = (owner_source.parent / factory_code_file).resolve()
        require(factory_code_file == owner_source,
                "reader-scope factory code belongs to another source file")
        exec_method = getattr(wrapper_class, "exec_module", None)
        require(callable(exec_method) and getattr(exec_method, "__globals__", None) is owner.__dict__,
                "reader-scope wrapper method globals belong to another module")
        for method_name in ("__init__", "create_module", "exec_module"):
            candidate = getattr(wrapper_class, method_name, None)
            require(callable(candidate),
                    f"reader-scope wrapper lacks {method_name}")
            method_code = getattr(candidate, "__code__", None)
            require(method_code is not None,
                    f"reader-scope {method_name} has no code object")
            method_file = Path(method_code.co_filename)
            if not method_file.is_absolute():
                method_file = (owner_source.parent / method_file).resolve()
            require(method_file == owner_source,
                    f"reader-scope {method_name} belongs to another source")
        method_cells = _stage_invocation_closure(exec_method)
        raw_cell_name = "historical_raw" if route == "provider-nested" else "raw"
        require(method_cells.get(raw_cell_name) is raw,
                "reader-scope wrapper closure is bound to a different raw ledger")
        require(isinstance(method_cells[raw_cell_name], bytes) and
                sha256(method_cells[raw_cell_name]) in self.bound_raw_sha256,
                "reader-scope wrapper closure lacks the bound raw ledger")
        require(getattr(generator, "__globals__", None) is owner.__dict__,
                "reader-scope generator owner globals changed")
        require(isinstance(raw, bytes) and sha256(raw) in self.bound_raw_sha256,
                "reader-scope raw ledger bytes are not stage-bound")
        require(getattr(facade, "_stage_factory", None) is self,
                "reader-scope facade belongs to another stage factory")
        binding = _StageInvocationBinding(
            route=route, owner=owner, helper=helper, generator=generator,
            factory_function=factory_function, previous_factory=previous_factory,
            wrapper_class=wrapper_class, raw_sha256=sha256(raw),
            selector=selector, nonce=self.factory_nonce, facade=facade,
            depth=len(self.invocations), factory_closure=tuple(factory_closure),
            helper_closure=tuple(helper_closure),
        )
        self.invocations.append(binding)
        return binding

    def unregister_invocation(self, binding: _StageInvocationBinding) -> None:
        require(binding.active and binding in self.invocations,
                "reader-scope invocation was already restored")
        require(self.invocations[-1] is binding,
                "reader-scope invocation unwound out of order")
        binding.active = False
        self.invocations.pop()

    def track_decorated_target(self, binding: _StageInvocationBinding, target: Any) -> None:
        sentinel = object()
        snapshot = {key: getattr(target, key, sentinel) for key in (
            "validate_packet", "_regular_bytes", "__name__", "__loader__",
            "__package__", "__spec__", "__file__", "__cached__")}
        binding.target_snapshots.append((target, snapshot, sentinel))

    def restore_invocation_targets(self, binding: _StageInvocationBinding) -> None:
        for target, snapshot, sentinel in reversed(binding.target_snapshots):
            for key, value in snapshot.items():
                if value is sentinel:
                    try:
                        delattr(target, key)
                    except AttributeError:
                        pass
                else:
                    setattr(target, key, value)
        binding.target_snapshots.clear()

    def _accept_decorated_loader(self, record: _StageSpecRecord, loader: Any) -> None:
        selector_routes = {
            "v092_resource_recovery": "codeql-resource",
            "v092_scoped_recovery_packet": "provider-nested",
        }
        route = selector_routes.get(record.name)
        require(route is not None,
                f"unreviewed decorated stage loader selector: {record.name}")
        binding = self._active_invocation(route, record.name)
        current_factory_closure = tuple(getattr(binding.factory_function, "__closure__", None) or ())
        require(len(current_factory_closure) == len(binding.factory_closure) and
                all(current is saved for current, saved in
                    zip(current_factory_closure, binding.factory_closure)),
                "decorated loader factory closure cells changed")
        current_helper_closure = tuple(getattr(binding.helper, "__closure__", None) or ())
        require(len(current_helper_closure) == len(binding.helper_closure) and
                all(current is saved for current, saved in
                    zip(current_helper_closure, binding.helper_closure)),
                "reader-scope helper closure cells changed")
        require(record.decorator_binding is None,
                "stage loader was decorated more than once")
        require(type(loader) is binding.wrapper_class,
                "decorated stage loader class is not the invocation-produced class")
        require(vars(loader) == {"_loader": record.loader},
                "decorated stage loader instance state changed")
        require(loader._loader is record.loader,
                "decorated stage loader inner delegate changed")
        method = getattr(type(loader), "exec_module", None)
        require(callable(method) and getattr(method, "__globals__", None) is binding.owner.__dict__,
                "decorated stage loader method owner changed")
        # Local class methods are generated by the owner module's real
        # generator.  The exact class identity, owner globals, and active
        # invocation already prevent copied same-shaped classes.
        require(getattr(method, "__code__", None) is not None,
                "decorated stage loader has no executable method")
        binding.target_snapshots.append((record.target, {
            key: getattr(record.target, key, _STAGE_MISSING)
            for key in ("validate_packet", "_regular_bytes", "__name__",
                        "__loader__", "__package__", "__spec__", "__file__", "__cached__")
        }, _STAGE_MISSING))
        record.decorator_binding = binding

    def module_from_spec(self, spec):
        record = self._record(spec)
        target = record.target
        sentinel = object()
        saved = {key: getattr(target, key, sentinel) for key in (
            "__name__", "__loader__", "__package__", "__spec__", "__file__", "__cached__")}
        try:
            candidate = self.std_module_from_spec(spec)
        finally:
            for key, value in saved.items():
                if value is sentinel:
                    try:
                        delattr(target, key)
                    except AttributeError:
                        pass
                else:
                    setattr(target, key, value)
        require(candidate is target,
                "stage factory loader returned a foreign graph module object")
        return candidate

    def facade(self):
        if self._facade is None:
            util = types.SimpleNamespace(
                spec_from_file_location=self.spec_from_file_location,
                module_from_spec=self.module_from_spec,
            )
            self._facade = types.SimpleNamespace(
                util=util, machinery=types.SimpleNamespace(ModuleSpec=self.std_module_spec),
                _stage_factory=self, _stage_pinned_graph=self.graph,
                _stage_pinned_root=str(self.root),
            )
        return self._facade


class _StageContextObserver:
    """Observe one real contextlib helper without replacing its generator.

    The exported module attribute is a contextlib helper; the repository
    generator is available as ``helper.__wrapped__``.  We save and invoke the
    helper object unchanged, then capture the local factory/class only after
    the real generator reaches its yield.
    """

    def __init__(self, factory: _StageImportFactory, owner: Any, attribute: str,
                 route: str, expected_selector: str, expected_source_sha: str,
                 raw_position: int):
        self.factory = factory
        self.owner = owner
        self.attribute = attribute
        self.route = route
        self.expected_selector = expected_selector
        self.expected_source_sha = expected_source_sha
        self.raw_position = raw_position
        self.helper = None
        self.generator = None
        self.wrapper = None

    def _verify_export(self) -> None:
        owner_dict = getattr(self.owner, "__dict__", None)
        require(isinstance(owner_dict, dict), "reader-scope owner has no module dictionary")
        # Once installed, the owner attribute is our contextlib wrapper.  The
        # wrapper's ``__wrapped__`` is this observer's generator, whose
        # globals are this stage module, so never rediscover the repository
        # helper from the transient wrapper.  Retain and revalidate the exact
        # helper captured at entry instead.
        helper = self.helper if self.helper is not None else owner_dict.get(self.attribute)
        require(callable(helper), "reader-scope owner attribute is not callable")
        if self.wrapper is None:
            require(owner_dict.get(self.attribute) is helper,
                    "reader-scope helper changed before observation")
        else:
            require(owner_dict.get(self.attribute) in (self.wrapper, helper),
                    "reader-scope helper wrapper changed during observation")
        generator = getattr(helper, "__wrapped__", None)
        require(callable(generator), "reader-scope helper has no wrapped repository generator")
        require(getattr(helper, "__closure__", None) is not None,
                "reader-scope contextlib helper has no closure")
        closure_values = []
        for cell in helper.__closure__ or ():
            try:
                closure_values.append(cell.cell_contents)
            except ValueError as exc:
                raise FrozenBridgeError("reader-scope helper has an empty closure") from exc
        require(generator in closure_values,
                "reader-scope helper closure does not retain its wrapped generator")
        require(getattr(generator, "__globals__", None) is owner_dict,
                "reader-scope generator globals are not the owner dictionary")
        source_file = Path(getattr(self.owner, "__file__", "")).resolve()
        require(source_file.is_file(), "reader-scope owner source is unavailable")
        require(sha256(source_file.read_bytes()) == self.expected_source_sha,
                "reader-scope owner source SHA changed")
        code_file = Path(generator.__code__.co_filename)
        if not code_file.is_absolute():
            code_file = (source_file.parent / code_file).resolve()
        require(code_file == source_file,
                "reader-scope generator code belongs to another source file")
        self.helper = helper
        self.generator = generator

    @contextlib.contextmanager
    def _observe(self, *args: Any, **kwargs: Any):
        self._verify_export()
        owner_dict = self.owner.__dict__
        saved_helper = self.helper
        require(saved_helper is not None,
                "reader-scope helper was not captured at scope entry")
        require(owner_dict.get(self.attribute) in (self.wrapper, saved_helper),
                "reader-scope helper changed before observation")
        facade = getattr(getattr(self.owner, "importlib", None), "util", None)
        require(facade is not None,
                "reader-scope owner has no stage importlib facade")
        previous_factory = getattr(facade, "module_from_spec", None)
        require(callable(previous_factory),
                "reader-scope predecessor factory is not callable")

        binding = None
        try:
            context = saved_helper(*args, **kwargs)
            require(hasattr(context, "__enter__") and hasattr(context, "__exit__"),
                    "reader-scope helper did not return a context manager")
            with context as value:
                installed_facade = getattr(getattr(self.owner, "importlib", None), "util", None)
                installed_factory = getattr(installed_facade, "module_from_spec", None)
                require(callable(installed_factory) and installed_factory is not previous_factory,
                        "reader-scope helper did not install a distinct local factory")
                raw = args[self.raw_position] if len(args) > self.raw_position else kwargs.get(
                    "historical_raw" if self.route == "provider-nested" else "raw")
                binding = self.factory.register_invocation(
                    route=self.route, owner=self.owner, helper=saved_helper,
                    generator=self.generator, factory_function=installed_factory,
                    previous_factory=previous_factory, wrapper_class=None,
                    raw=raw, selector=self.expected_selector, facade=getattr(self.owner, "importlib"),
                )
                # register_invocation resolves the class from the actual
                # factory closure; the temporary argument is intentionally
                # ignored and keeps the call signature explicit.
                yield value
        finally:
            if binding is not None:
                self.factory.restore_invocation_targets(binding)
                self.factory.unregister_invocation(binding)
            current = getattr(getattr(self.owner, "importlib", None), "util", None)
            if current is not None:
                require(getattr(current, "module_from_spec", None) is previous_factory,
                        "reader-scope factory did not restore its predecessor")
            current_helper = owner_dict.get(self.attribute)
            if current_helper not in (self.wrapper, saved_helper):
                owner_dict[self.attribute] = saved_helper
                raise FrozenBridgeError(
                    "reader-scope helper attribute changed during observation")
            # Keep the observer installed for the enclosing stage scope.  A
            # second real context-manager entry must be observed by the same
            # invocation registry; only __exit__ removes the wrapper.

    def __enter__(self):
        self._verify_export()
        owner_dict = self.owner.__dict__
        helper = self.helper
        @contextlib.contextmanager
        def wrapper(*args: Any, **kwargs: Any):
            with self._observe(*args, **kwargs) as value:
                yield value
        require(owner_dict.get(self.attribute) is helper,
                "reader-scope helper changed before installation")
        self.wrapper = wrapper
        owner_dict[self.attribute] = wrapper
        return self

    def __exit__(self, exc_type, exc, tb):
        current = self.owner.__dict__.get(self.attribute)
        if current not in (self.wrapper, self.helper):
            # Restore the exact exported helper before reporting tampering so
            # a failed invocation cannot leave a foreign callable installed.
            self.owner.__dict__[self.attribute] = self.helper
            raise FrozenBridgeError("reader-scope observer state is invalid")
        if current is self.wrapper:
            self.owner.__dict__[self.attribute] = self.helper
        return False


def _stage_observe_context(factory: _StageImportFactory, owner: Any, attribute: str,
                           route: str, selector: str, source_sha: str,
                           raw_position: int) -> _StageContextObserver:
    return _StageContextObserver(factory, owner, attribute, route, selector,
                                 source_sha, raw_position)


_ACTIVE_STAGE_FACTORY = None


def _stage_pinned_importlib(root: Path, graph: Any, original: Any, *,
                            stdlib_importlib: Any | None = None,
                            factory: _StageImportFactory | None = None) -> Any:
    """Return the exact paired stage facade; never delegate across facades."""
    root = Path(root).resolve()
    active = globals().get("_ACTIVE_STAGE_FACTORY")
    if factory is None and isinstance(active, _StageImportFactory):
        factory = active
    if factory is None:
        factory = _StageImportFactory(
            root, graph, stdlib_importlib,
            policy_path=OLD_POLICY_PATH, policy=_stage_member(graph, "policy_source"))
    existing = getattr(original, "_stage_factory", None)
    if existing is factory:
        return original
    require(existing is None,
            "nested loader belongs to another stage import factory")
    return factory.facade()


@contextlib.contextmanager
def _stage_provider_scope(root: Path, provider: Any, modules: Mapping[str, Any], graph: Any,
                          *, stdlib_importlib: Any | None = None) -> Any:
    """Route provider04's nested loaders to the same graph instances.

    Provider04 predates the stage API and normally imports its own frozen
    executor/checker/configuration plus the two historical continuation
    helpers.  Patching only its named loader functions for this call keeps the
    actual provider/replay implementation while making every dynamic load
    graph-owned.  All attributes are restored even when a nested validator
    rejects a context.
    """
    saved: list[tuple[Any, str, Any]] = []

    def replace(owner: Any, name: str, value: Any) -> None:
        if hasattr(owner, name):
            saved.append((owner, name, getattr(owner, name)))
            setattr(owner, name, value)

    disk_guard = None
    try:
        disk_guard = _stage_member(graph, "disk_guard")
    except FrozenBridgeError:
        # A provider that does not expose load_frozen may not need the disk
        # guard.  If it does, the missing graph role is a hard error below.
        disk_guard = None
    if callable(getattr(provider, "load_frozen", None)):
        require(disk_guard is not None, "provider load_frozen requires pinned disk_guard")
        pinned_frozen = {"executor": modules["executor"], "checker": modules["checker"],
                         "configuration": modules["configuration"], "disk_guard": disk_guard}
        replace(provider, "load_frozen", lambda actual_root: dict(pinned_frozen))

    def pinned_loader(actual_root: Path, relative: str, expected: str, name: str) -> Any:
        return _stage_module_for_route(root, graph, actual_root, relative, name, expected)

    if callable(getattr(provider, "_load_pinned_helper", None)):
        replace(provider, "_load_pinned_helper", pinned_loader)
    if callable(getattr(provider, "_load_module", None)):
        # Provider03's generic loader is only permitted for an exact graph
        # path; it cannot load an arbitrary source path after graph sealing.
        def pinned_generic(actual_root: Path, relative: str, name: str) -> Any:
            return _stage_module_for_route(root, graph, actual_root, relative, name)
        replace(provider, "_load_module", pinned_generic)

    # Historical helper modules themselves have the same frozen-loader seam.
    # Patch any graph-resolved helper before provider03 invokes it.  A module
    # absent from the graph is deliberately left to the provider only until it
    # requests it, at which point pinned_loader fails closed.
    stage_module = sys.modules.get(__name__)
    helper_modules = [getattr(member, "module_object", None)
                      for member in getattr(graph, "members", ())
                      if getattr(member, "module_object", None) is not stage_module]
    helper_frozen = {"executor": modules["executor"], "checker": modules["checker"],
                     "configuration": modules["configuration"]}
    try:
        helper_frozen["disk_guard"] = _stage_member(graph, "disk_guard")
    except FrozenBridgeError:
        pass
    # Several frozen helpers retain their own import-time EXECUTOR/CHECKER
    # globals.  Those objects are incidental nested imports and cannot become
    # authority during historical replay.  Rebind only existing repository
    # module attributes to the exact graph objects for this provider call;
    # every assignment is restored by the common ``saved`` finally block.
    for helper in helper_modules:
        if helper is None:
            continue
        if hasattr(helper, "EXECUTOR"):
            replace(helper, "EXECUTOR", modules["executor"])
        if hasattr(helper, "CHECKER"):
            replace(helper, "CHECKER", modules["checker"])
    try:
        # Provider04 imports CodeQL03; CodeQL03 in turn imports its two
        # historical continuation helpers. Route those imports through the
        # exact graph instances before recovery starts. This is a module-local
        # facade, so no process-global importlib patch can leak to siblings.
        # Late checker/resource-recovery imports occur after incoming replay;
        # scope every graph member that carries an importlib facade, not only
        # the provider's obvious helper exports.  The facade still resolves
        # only explicit loader names from STAGE_LOADER_ROUTE_NAMES.
        importlib_owners = []
        seen_importlib_owners: set[int] = set()
        for candidate in [provider, *helper_modules, *modules.values()]:
            if candidate is None or candidate is stage_module or id(candidate) in seen_importlib_owners:
                continue
            if getattr(candidate, "importlib", None) is not None:
                seen_importlib_owners.add(id(candidate))
                importlib_owners.append(candidate)
        for owner in importlib_owners:
            original_importlib = getattr(owner, "importlib", None)
            if original_importlib is not None and getattr(original_importlib, "util", None) is not None:
                replace(owner, "importlib", _stage_pinned_importlib(
                    root, graph, original_importlib, stdlib_importlib=stdlib_importlib))

        for helper in helper_modules:
            if helper is None or not callable(getattr(helper, "_load_frozen", None)):
                continue
            original = getattr(helper, "_load_frozen")
            def helper_loader(actual_root: Path, name: str, _m=helper_frozen) -> Any:
                key = "executor" if name in {"execute", "executor"} else name
                require(key in _m, f"unregistered nested frozen role: {name}")
                return _m[key]
            replace(helper, "_load_frozen", helper_loader)
            if callable(getattr(helper, "_load_pinned_helper", None)):
                replace(helper, "_load_pinned_helper", pinned_loader)
            if callable(getattr(helper, "_load_module", None)):
                replace(helper, "_load_module", pinned_generic)
            # Keep a reference to the original solely to make the closure
            # explicit for reviewers; it is restored by ``finally``.
            require(callable(original), "nested frozen loader is malformed")
        yield
    finally:
        for owner, name, original in reversed(saved):
            setattr(owner, name, original)


def _stage_incoming_pinned(provider: Any, root: Path, core: Mapping[str, Any], graph: Any,
                           modules: Mapping[str, Any], mode: str,
                           ledger_bytes: bytes | None,
                           stdlib_importlib: Any | None = None) -> Mapping[str, Any]:
    with _stage_provider_scope(root, provider, modules, graph,
                               stdlib_importlib=stdlib_importlib):
        return _stage_incoming(provider, root, core, graph, mode, ledger_bytes)


def _stage_public(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"__type__": "bytes", "sha256": sha256(value), "size": len(value)}
    if isinstance(value, Mapping):
        return {str(key): _stage_public(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
                if key not in {"modules", "replacement05", "executor", "checker", "configuration"}}
    if isinstance(value, (list, tuple)):
        return [_stage_public(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__opaque_type__": type(value).__module__ + ":" + type(value).__qualname__}


def _stage_closure(root: Path, core: Mapping[str, Any], graph: Any) -> list[dict[str, str]]:
    closure = core.get("runtime_graph_closure", core.get("nested_module_closure"))
    if closure is None:
        return [{"name": item.name, "path": item.canonical_path, "sha256": item.source_sha256}
                for item in getattr(graph, "members", ())]
    require(isinstance(closure, list) and closure, "runtime graph closure is empty")
    seen: set[tuple[str, str]] = set()
    result = []
    for item in closure:
        require(isinstance(item, Mapping) and set(item) <= {"name", "path", "sha256"},
                "runtime graph closure has an unbound field")
        ref = _ref({"path": item.get("path"), "sha256": item.get("sha256")},
                   "runtime graph closure")
        name = item.get("name")
        require(isinstance(name, str) and name,
                "runtime graph closure requires an explicit graph member name")
        key = (name, ref["path"])
        require(key not in seen, "runtime graph closure repeats a named member")
        seen.add(key)
        _bound(root, ref, "runtime graph closure")
        result.append({"name": name, **ref})
    if not getattr(graph, "fixture_only", False):
        # The graph order is part of the sealed loader contract.  Comparing
        # sets would accept a reordered closure and could change which
        # independently loaded alias is installed first.
        graph_refs = tuple((getattr(member, "name", None), getattr(member, "canonical_path", None),
                            getattr(member, "source_sha256", None))
                           for member in getattr(graph, "members", ()))
        closure_refs = tuple((item["name"], item["path"], item["sha256"]) for item in result)
        require(graph_refs == closure_refs,
                "runtime graph closure is not exactly the sealed ordered graph membership")
    return result


def _stage_summary(root: Path, value: Mapping[str, Any], rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    supplied = value.get("checker_summary")
    if isinstance(supplied, Mapping):
        return dict(supplied)
    checker, executor = value.get("checker"), value.get("executor")
    contexts = value.get("contexts")
    require(checker is not None and executor is not None and isinstance(contexts, Mapping),
            "stage runtime has no actual checker context")
    verify = getattr(checker, "_verify_one_group", None)
    failed = getattr(checker, "_verify_failed_attempt", None)
    group_for = getattr(executor, "_historical_group_for_replay", None)
    require(callable(verify) and callable(failed) and callable(group_for),
            "frozen checker replay API is incomplete")
    reports, failures, groups = [], [], set()
    for row in rows:
        origin = contexts.get(row.get("contract_sha256"))
        require(isinstance(origin, Mapping) and isinstance(origin.get("validated"), Mapping),
                "ledger row has no registered actual context")
        normalized = origin["validated"]
        group = group_for(normalized, row)
        number = int(row.get("attempt_number") or 1)
        if row.get("status") == "completed":
            bindings, _ = verify(root, normalized, group, row, origin.get("plan_commit"), number)
            reports.extend(bindings); groups.add(str(row.get("group_id")))
        else:
            path = root / "reports/releases/v0.9.2/attempts" / str(row.get("attempt_id")) / "completed.json"
            require(path.is_file(), "failed historical row has no completed receipt")
            failures.append(failed(root, normalized, group, row, origin.get("plan_commit"), number,
                                   sha256(canonical_json(row)), sha256(path.read_bytes())))
    return {"status": "fresh-evidence-verified" if mode == "after" else "partial-evidence-verified",
            "ledger_rows": len(rows), "selected_groups": len(groups), "partitions": len(reports),
            "rows": sum(int(item.get("rows", 0)) for item in reports if isinstance(item, Mapping)),
            "known_stale": 0, "fresh_reports": reports, "failed_attempts": failures,
            "full_release_gate_satisfied": mode == "after"}


def _stage_build_runtime_fixture(root: Path, core: Mapping[str, Any], graph: Any, *, mode: str,
                         ledger_bytes: bytes | None,
                         stdlib_importlib: Any | None = None) -> dict[str, Any]:
    modules = _stage_modules(graph, require_legacy=False)
    replacement = modules["replacement17"]
    static_fn = getattr(replacement, "validate_static", None)
    require(callable(static_fn), "replacement17 lacks validate_static")
    manifest_ref = _stage_manifest(core)
    if manifest_ref["sha256"]:
        manifest_raw = _bound(root, manifest_ref, "stage manifest")
    else:
        manifest_raw = _read(root, manifest_ref["path"])
        manifest_ref["sha256"] = sha256(manifest_raw)
    static = static_fn(root, manifest_ref["path"])
    require(isinstance(static, Mapping) and isinstance(static.get("core"), Mapping),
            "replacement17 static validator returned no core")
    contract_ref = _stage_contract(core, static)
    contract_path = _path(root, contract_ref["path"], "stage contract")
    contract_raw = _bound(root, contract_ref, "stage contract")
    validated = _stage_validate_plan(modules["executor"], root, contract_path)
    require(validated.get("bytes_sha256") == contract_ref["sha256"],
            "frozen executor returned a different contract")
    for name in ("policy_source", "policy_runtime"):
        policy = modules[name]
        checker = getattr(policy, "validate", None) or getattr(policy, "validate_runtime", None)
        if callable(checker):
            parameters = inspect.signature(checker).parameters
            if len(parameters) >= 2:
                checker(root, core)
            else:
                checker(root)
    ledger_raw, rows = _stage_ledger(root, core, ledger_bytes)
    recovered = _stage_incoming_pinned(modules["incoming_recovery"], root, core, graph,
                                       modules, mode, ledger_bytes,
                                       stdlib_importlib=stdlib_importlib)
    provider_modules = recovered.get("modules")
    if provider_modules is not None:
        require(isinstance(provider_modules, Mapping), "incoming provider module roster is malformed")
        for name, expected in (("replacement05", replacement), ("executor", modules["executor"]),
                               ("checker", modules["checker"]), ("configuration", modules["configuration"])):
            require(provider_modules.get(name) is expected,
                    f"incoming provider returned a foreign {name} object")
    contexts = recovered.get("contexts")
    require(isinstance(contexts, Mapping) and contexts, "incoming recovery omitted contexts")
    contexts = dict(contexts)
    contract_sha = contract_ref["sha256"]
    contexts[contract_sha] = {"validated": validated, "plan_commit": core.get("plan_commit"),
                              "source_commit": core.get("source_commit"), "role": "replacement"}
    base, repaired = recovered.get("base"), recovered.get("repaired")
    require(isinstance(base, Mapping) and isinstance(repaired, Mapping),
            "incoming recovery omitted base/repaired contexts")
    mixed = recovered.get("mixed_context")
    if not isinstance(mixed, Mapping):
        mixed = {"root": root, "manifest": static.get("manifest", core),
                 "manifest_sha256": manifest_ref["sha256"], "prefix": rows[:88],
                 "prefix_raw": b"".join(canonical_json(row) for row in rows[:88]),
                 "rows": rows, "contexts": contexts, "base": base, "repaired": repaired,
                 "validated": validated, "executor": modules["executor"],
                 "checker": modules["checker"], "configuration": modules["configuration"],
                 "contract": validated.get("plan"), "contract_raw": contract_raw,
                 "contract_sha256": contract_sha, "source_commit": core.get("source_commit"),
                 "plan_commit": core.get("plan_commit")}
    else:
        mixed = dict(mixed)
        mixed.update(root=root, rows=rows, contexts=contexts, validated=validated,
                     executor=modules["executor"], checker=modules["checker"],
                     configuration=modules["configuration"])
    runtime_seed = {"root": root, "contexts": contexts, "base": base, "repaired": repaired,
                    "validated": validated, "mixed_context": mixed,
                    "executor": modules["executor"], "checker": modules["checker"],
                    "configuration": modules["configuration"],
                    "checker_summary": recovered.get("checker_summary")}
    summary = _stage_summary(root, runtime_seed, rows, mode)
    config_summary = recovered.get("configuration_summary")
    if not isinstance(config_summary, Mapping):
        config_summary = {"status": "configuration-pending-complete-matrix",
                          "reason": "configuration is a separate frozen gate"}
    closure = _stage_closure(root, core, graph)
    diagnostic = {"schema": STAGE_RUNTIME_SCHEMA + "/diagnostic", "status": "read-only-frozen-validation-passed",
                  "execution_authorized": False, "mode": mode, "manifest_ref": manifest_ref,
                  "contract_ref": contract_ref, "source_commit": core.get("source_commit"),
                  "plan_commit": core.get("plan_commit"), "ledger_sha256": sha256(ledger_raw),
                  "ledger_rows": len(rows), "graph_sha256": getattr(graph, "graph_sha256", None),
                  "runtime_graph_closure": closure, "validated": _stage_public(validated),
                  "canonical_contract_path_and_contract_sha256": contract_ref,
                  "original_prefix_ref": core.get("original_prefix"),
                  "continuation_prefix_ref": core.get("continuation_prefix"),
                  "exact_replacement_group_subset_derived_from_full_plan": list(
                      core.get("replacement_groups", [])),
                  "validated_full_normalized_plan": _stage_public(validated),
                  "validated_full_plan_digest": sha256(canonical_json(_stage_public(validated.get("plan")))),
                  "replacement_validated_normalized_plan": _stage_public(validated),
                  "historical_context_map_keyed_by_contract_sha256": _stage_public(contexts),
                  "checker_summary": _stage_public(summary),
                  "checker_summary_or_pending": _stage_public(summary),
                  "configuration_summary": _stage_public(config_summary),
                  "configuration_execute_false_summary_or_pending": _stage_public(config_summary)}
    diagnostic["context_digest"] = sha256(canonical_json(diagnostic))
    runtime_modules = {"replacement05": replacement, "executor": modules["executor"],
                       "checker": modules["checker"], "configuration": modules["configuration"]}
    return {"schema": STAGE_RUNTIME_SCHEMA, "lossless_runtime_objects": True, "mode": mode,
            "modules": runtime_modules, "validated": validated, "replacement_validated": validated,
            "mixed_context": mixed, "checker_summary": summary, "configuration_summary": config_summary,
            "bridge_context": diagnostic, "graph": graph, "graph_closure": closure,
            "runtime_objects": runtime_seed}


def _stage_validate_replacement_with_scoped_resource_boundary(
    root: Path, executor: Any, replacement: Any, contract_path: Path,
    contract_ref: Mapping[str, str], contract_raw: bytes, core: Mapping[str, Any],
    manifest_obj: Mapping[str, Any], source_commit: str, rows: list[dict[str, Any]],
    raw: bytes,
) -> dict[str, Any]:
    """Validate the replacement with the one reviewed C4 resource adapter.

    Frozen ``validate_plan`` is still the validator for every ordinary field.
    Its legacy parser cannot represent the reviewed replacement path, rich
    qualification identity, C03 cap, aggregate guard, and no-expiry clock.
    Exact scoped projections below preserve every other frozen field check;
    actual plan/group values and module hooks are restored before return.  The adapter first runs replacement-05's
    contract/qualification/runner gates, then obtains the complete historical
    recovery object by invoking continuation-06's exact C4 boundary.  It never
    accepts a caller-supplied serialized recovery or copies a replacement
    plan into a historical result.
    """
    contract_plan = _json(contract_raw, "replacement contract")
    require(contract_plan.get("resource_guards") == {"stop_free_gib": 48, "working_set_gib": 30},
            "replacement must inherit only the exact authorized aggregate30GiB guard")
    parser_plan = copy.deepcopy(contract_plan)
    parser_plan["resource_guards"]["working_set_gib"] = 12
    c_groups = [group for group in parser_plan.get("groups", [])
                if group.get("id") == "bifrost-c-kernel"]
    require(len(c_groups) == 1 and type(c_groups[0].get("maximum_attempts")) is int and
            c_groups[0]["maximum_attempts"] == 3,
            "replacement parser requires the exact reviewed C03 cap")
    c_groups[0]["maximum_attempts"] = 2
    original_v4 = getattr(executor, "V4_CONTRACT_PATH", None)
    require(original_v4 == PurePosixPath("reports/releases/v0.9.2/execution-v4/contract.json"),
            "frozen canonical C4 parser boundary differs")
    require(contract_path.resolve().is_relative_to(root.resolve()) and
            contract_path.resolve().relative_to(root.resolve()).as_posix() == contract_ref["path"] and
            contract_ref["path"] != original_v4.as_posix(),
            "replacement parser path must be the exact new contract, preserving C4")
    # The successor contract path is bound by the typed core and the exact
    # byte/hash check above.  The frozen population adapter below projects only
    # its canonical C4 population input; it never aliases the successor path.
    original_population = getattr(executor, "_population", None)
    require(callable(original_population), "frozen population boundary is unavailable")
    original_inputs = getattr(executor, "_source_inputs", None)
    require(callable(original_inputs), "frozen exact source-input resolver is unavailable")
    original_read = getattr(executor, "_read_json", None)
    require(callable(original_read), "frozen exact-plan reader is unavailable")
    original = getattr(executor, "_validate_resource_recovery", None)
    original_wall = getattr(executor, "_wall_budget", None)
    require(callable(original_wall), "frozen plan wall-budget boundary is unavailable")
    require(callable(original), "frozen executor resource-recovery hook is unavailable")
    source_contexts = _exact_source_context_entries(core, fixture_only=False)
    base_key, base_entry = _ref_for_context(source_contexts, "base")
    base_ref = _ref(base_entry["contract"], "base source context contract")
    require(base_ref["path"] == "reports/releases/v0.9.2/execution-v4/contract.json" and
            base_key == "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb",
            "resource adapter base context is not the registered C4 contract")
    continuation_contract = _ref(core["continuation"]["contract"], "continuation contract")
    inherited_raw = _bound(root, continuation_contract, "typed continuation contract")
    inherited_plan = _json(inherited_raw, "typed continuation contract")
    ids = [group.get("id") for group in _json(contract_raw, "replacement contract").get("groups", [])
           if isinstance(group, Mapping) and group.get("tool") == "bifrost"]
    require(len(ids) == 20 and len(set(ids)) == 20,
            "replacement resource adapter requires the complete 20-group Bifrost subset")
    # Resolve the explicit reviewed replacement gates before entering the
    # frozen validator.  These calls bind the replacement semantics that C4's
    # resource-only successor check cannot represent.
    try:
        replacement._contract_delta(inherited_plan, _json(contract_raw, "replacement contract"),
                                    dict(manifest_obj), ids)
        replacement_plan = _json(contract_raw, "replacement contract")
        runner = manifest_obj.get("runner")
        require(isinstance(runner, dict) and replacement_plan.get("tools", {}).get("runner") == runner,
                "replacement resource adapter runner identity is missing")
        environments = [group.get("environment") for group in replacement_plan.get("groups", [])
                        if isinstance(group, Mapping) and group.get("id") in ids]
        require(environments and isinstance(environments[0], dict) and
                all(value == environments[0] for value in environments),
                "replacement resource adapter Bifrost environment is not exact")
        replacement._validate_runner_binding(root, dict(manifest_obj), runner, replacement_plan,
                                             source_commit, environments[0])
        replacement._validate_qualification(root, manifest_obj.get("qualification"), ids)
        qualification_ref = _ref(manifest_obj.get("qualification"), "qualified v0140 evidence")
        # The reviewed replacement validator has already bound the exact
        # qualification reference.  Do not import a second protocol constant;
        # retain the core's path/SHA binding as the sole source of truth.
        qualification_raw = _bound(root, qualification_ref, "qualified v0140 evidence")
        qualification_obj = _json(qualification_raw, "qualified v0140 evidence")
        qualification_parser = copy.deepcopy(qualification_obj)
        # Only the two extra provenance fields are projected from this ONE
        # exact immutable evidence object. The raw bytes/digest stay original;
        # the full richer object was independently checked immediately above.
        require(set(qualification_parser["tool"]) ==
                {"path", "sha256", "version", "build_identity", "bytes", "public_tag_commit"},
                "rich qualification tool identity has unreviewed fields")
        del qualification_parser["tool"]["bytes"]
        del qualification_parser["tool"]["public_tag_commit"]
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError("replacement gates rejected the scoped resource adapter") from exc

    recovered_history = _incoming_recovery(root, core)
    base_path = root / Path(*_relative(base_ref["path"], "base source context contract").parts)
    recovery_cache: dict[str, Any] = {}

    def scoped(validated: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(validated, Mapping) or validated.get("bytes_sha256") != contract_ref["sha256"]:
            return original(validated)
        if "value" not in recovery_cache:
            try:
                base_value = recovered_history["base"]["validated"]
                require(isinstance(base_value, dict) and
                        base_value.get("bytes_sha256") == base_key and
                        isinstance(base_value.get("resource_recovery"), dict),
                        "frozen C4 boundary returned no complete historical recovery")
                recovery_cache["value"] = copy.deepcopy(base_value["resource_recovery"])
            except FrozenBridgeError:
                raise
            except Exception as exc:
                raise FrozenBridgeError("frozen C4 resource recovery could not be derived") from exc
        return copy.deepcopy(recovery_cache["value"])

    def no_expiry_plan_wall(plan):
        # The exact committed replacement contract is null.  This finite
        # historical normalization value only satisfies the frozen parser;
        # it is removed from the returned context before any consumer runs.
        if plan.get("source_commit") == source_commit and plan.get("execution_series") == 2:
            require(plan == parser_plan and plan.get("total_wall_budget_seconds") is None,
                    "no-expiry parser adapter received another plan")
            return float(TOTAL_WALL_SECONDS)
        return original_wall(plan)

    def exact_replacement_reader(path, description):
        plan_value, raw_value = original_read(path, description)
        if Path(path).resolve() == contract_path.resolve():
            require(plan_value == contract_plan and raw_value == contract_raw,
                    "aggregate parser adapter received changed contract bytes")
            return copy.deepcopy(parser_plan), raw_value
        if Path(path).resolve() == (root / qualification_ref["path"]).resolve():
            require(plan_value == qualification_obj and raw_value == qualification_raw,
                    "qualification parser received changed immutable bytes")
            return copy.deepcopy(qualification_parser), raw_value
        return plan_value, raw_value

    def exact_replacement_inputs(plan, repo_root, qualification):
        require(plan == parser_plan and Path(repo_root).resolve() == root.resolve(),
                "scoped source-input resolver received another contract")
        return _resolve_replacement_source_inputs(original_inputs, plan, repo_root,
                                                  qualification, inherited_plan["source_inputs"])

    def exact_replacement_population(plan, plan_path):
        # The frozen population helper derives the repository root from the
        # canonical C4 contract depth. Our exact successor is one level deeper.
        # Only this exact plan/path is projected onto the unchanged canonical
        # root anchor; the original helper still reads the bound population
        # and validates raw SHA, fixture identity, and complete case roster.
        require(plan == parser_plan and
                Path(plan_path).resolve() == contract_path.resolve() and
                contract_path.resolve() == (root / contract_ref["path"]).resolve(),
                "population projection received another plan/path/root")
        return original_population(plan, root / original_v4)

    executor._population = exact_replacement_population
    executor._source_inputs = exact_replacement_inputs
    executor.V4_CONTRACT_PATH = PurePosixPath(contract_ref["path"])
    executor._validate_resource_recovery = scoped
    executor._wall_budget = no_expiry_plan_wall
    executor._read_json = exact_replacement_reader
    try:
        try:
            value = executor.validate_plan(contract_path, repo_root=root)
        except FrozenBridgeError:
            raise
        except Exception as exc:
            raise FrozenBridgeError("frozen validator rejected replacement after scoped resource checks") from exc
    finally:
        executor._validate_resource_recovery = original
        executor._wall_budget = original_wall
        executor._read_json = original_read
        executor.V4_CONTRACT_PATH = original_v4
        executor._source_inputs = original_inputs
        executor._population = original_population
    require(value.get("path") == str(contract_path.resolve()),
            "frozen parser must retain the actual replacement contract path")
    require(value.get("plan") == parser_plan, "frozen aggregate parser changed another plan field")
    normalized_c = [group for group in value.get("groups", [])
                    if group.get("id") == "bifrost-c-kernel"]
    require(len(normalized_c) == 1 and normalized_c[0].get("maximum_attempts") == 2,
            "frozen parser changed the exact C cap projection")
    normalized_c[0]["maximum_attempts"] = 3
    value["plan"] = copy.deepcopy(contract_plan)
    require(value.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
            "frozen parser normalization changed")
    value["total_wall_budget_seconds"] = None
    return value


class _StagePolicyProxyLoader:
    """Expose one already-pinned policy object under the legacy import name.

    bridge08 imports its policy twice by filename.  Importing that file again
    would create a second module graph, so the graph branch gives the legacy
    importer a fresh facade whose functions retain the pinned policy module's
    globals and objects.  The facade is scoped to one call and is never added
    to the reviewed graph or used as runtime authority.
    """

    def __init__(self, source: Any) -> None:
        self.source = source

    def create_module(self, spec: Any) -> Any:
        return self.source

    def exec_module(self, module: Any) -> None:
        require(module is self.source, "historical policy loader received a foreign module")
        # The source is already sealed and loaded in the graph. Never execute
        # or copy it into a second module graph.


@contextlib.contextmanager
def _stage_full_graph_scope(root: Path, core: Mapping[str, Any], graph: Any,
                            modules: Mapping[str, Any], *, mode: str,
                            ledger_bytes: bytes | None,
                            stdlib_importlib: Any | None = None) -> Any:
    """Run the copied bridge08 body with every loader bound to this graph.

    This is intentionally a narrow adapter around the complete legacy body;
    it does not replace C4 validation with a count projection.  The graph's
    replacement05 extra is the reviewed full bridge validator, while
    replacement17 remains the static packet protocol member.
    """
    # Callers may pass a temporary checkout through a symlink (the focused
    # fixture does this on macOS).  Normalize once at the boundary so every
    # scoped loader compares the same canonical root representation.
    root = Path(root).resolve()
    replacement = modules["replacement05"]
    provider = modules["incoming_recovery"]
    frozen = {name: modules[name] for name in ("executor", "checker", "configuration")}
    graph_by_name = {
        getattr(member, "name", None): member for member in getattr(graph, "members", ())
    }
    graph_by_path: dict[str, list[Any]] = {}
    for member in getattr(graph, "members", ()):
        graph_by_path.setdefault(getattr(member, "canonical_path", None), []).append(member)
    policy = modules["policy_source"]
    require(callable(getattr(policy, "validate_execution_window", None)) and
            callable(getattr(policy, "validate_source_design", None)),
            "pinned policy member lacks the full replacement validation API")
    old_policy_path = OLD_POLICY_PATH
    legacy_loader_routes = {
        "replacement05": "replacement05",
        "independent_codeql_history": "incoming_recovery",
        "source_design04_policy": "policy_source",
    }
    policy_member = graph_by_name.get("policy_source")
    require(policy_member is not None, "graph omits the explicit policy_source route")
    original: dict[str, Any] = {}
    object_original: list[tuple[Any, str, Any]] = []
    object_seen: set[tuple[int, str]] = set()
    missing = object()

    def replace(name: str, value: Any) -> None:
        original[name] = globals()[name]
        globals()[name] = value

    def replace_object(owner: Any, name: str, value: Any) -> None:
        key = (id(owner), name)
        if key in object_seen or not hasattr(owner, name):
            return
        object_seen.add(key)
        object_original.append((owner, name, getattr(owner, name)))
        setattr(owner, name, value)

    def bind_object(owner: Any, name: str, value: Any) -> None:
        key = (id(owner), name)
        if key in object_seen:
            return
        object_seen.add(key)
        object_original.append((owner, name, getattr(owner, name, missing)))
        setattr(owner, name, value)

    incoming_cache: dict[str, Any] = {}

    def scoped_dependencies(actual_root: Path = root, *, fixture_modules: Mapping[str, Any] | None = None,
                            fixture_only: bool = False) -> dict[str, Any]:
        require(Path(actual_root).resolve() == root,
                "graph dependency loader was called for another root")
        require(fixture_modules is None and not fixture_only,
                "graph runtime cannot switch to fixture dependencies")
        return {"replacement05": replacement, **frozen}

    def scoped_incoming(actual_root: Path, actual_core: Mapping[str, Any]) -> Mapping[str, Any]:
        require(actual_root.resolve() == root and actual_core is core,
                "incoming recovery was called with an unbound graph context")
        if "value" not in incoming_cache:
            incoming_cache["value"] = _stage_incoming_pinned(
                provider, root, core, graph, {"replacement05": replacement, **frozen},
                mode, ledger_bytes)
        return incoming_cache["value"]

    def scoped_loader(actual_root: Path, name: str, ref: Mapping[str, str]) -> Any:
        path = ref.get("path") if isinstance(ref, Mapping) else None
        expected_sha = ref.get("sha256") if isinstance(ref, Mapping) else None
        if path == old_policy_path:
            require(expected_sha == OLD_POLICY_SHA256,
                    "legacy policy route has the wrong historical source digest")
            require(policy_member.source_sha256 != OLD_POLICY_SHA256,
                    "policy14 graph route was relabeled as the historical policy")
            return policy
        route_name = legacy_loader_routes.get(name, name)
        member = graph_by_name.get(route_name)
        require(member is not None and member.canonical_path == path,
                f"legacy loader route is not explicitly bound: {name} -> {path}")
        require(member.source_sha256 == expected_sha,
                f"legacy loader requested a path with the wrong graph digest: {path}")
        # A path may have several independently loaded graph instances.  The
        # route name above selects one exact member; never collapse aliases by
        # using a path-only dictionary.
        return member.module_object

    def scoped_validator(*args: Any, **kwargs: Any) -> Any:
        # This function is defined below the copied bridge08 implementation;
        # the name is resolved dynamically by load_and_validate.
        return _stage_validate_replacement_with_scoped_resource_boundary(*args, **kwargs)

    def scoped_legacy_load_and_validate(*args: Any, **kwargs: Any) -> Any:
        return _STAGE_LEGACY_LOAD_AND_VALIDATE(*args, **kwargs)

    replace("load_dependencies", scoped_dependencies)
    replace("_load_module", scoped_loader)
    replace("_incoming_recovery", scoped_incoming)
    replace("_validate_replacement_with_scoped_resource_boundary", scoped_validator)
    replace("load_and_validate", scoped_legacy_load_and_validate)
    replace("REPLACEMENT05", {"path": next(
        member.canonical_path for member in getattr(graph, "members", ())
        if getattr(member, "name", None) == "replacement05"),
        "sha256": next(member.source_sha256 for member in getattr(graph, "members", ())
                        if getattr(member, "name", None) == "replacement05")})
    replace("FROZEN", {name: {"path": next(member.canonical_path for member in getattr(graph, "members", ())
                                             if getattr(member, "name", None) == name),
                              "sha256": next(member.source_sha256 for member in getattr(graph, "members", ())
                                             if getattr(member, "name", None) == name)}
                       for name in frozen})
    # The checker and configuration modules eagerly import their own executor
    # graph.  Pin those authority-bearing globals for the whole copied 08
    # validation body, including incoming historical replay and partial
    # checker calls.  Historical helper modules are included when they expose
    # the same globals; unknown attributes are left untouched and therefore
    # cannot be silently converted into graph authority.
    checker = modules["checker"]
    configuration = modules["configuration"]
    executor = modules["executor"]
    bind_object(checker, "EXECUTOR", executor)
    bind_object(configuration, "CHECKER", checker)
    bind_object(configuration, "EXECUTOR", executor)
    for member in getattr(graph, "members", ()):
        owner = getattr(member, "module_object", None)
        if owner is None:
            continue
        if hasattr(owner, "EXECUTOR"):
            replace_object(owner, "EXECUTOR", executor)
        if hasattr(owner, "CHECKER"):
            replace_object(owner, "CHECKER", checker)
    require(getattr(checker, "EXECUTOR", None) is executor,
            "full graph checker retains a foreign EXECUTOR instance")
    require(getattr(configuration, "CHECKER", None) is checker and
            getattr(configuration, "EXECUTOR", None) is executor,
            "full graph configuration retains a foreign checker/executor instance")
    original_importlib = globals()["importlib"]
    host_stdlib = stdlib_importlib
    if host_stdlib is None:
        host_stdlib = getattr(original_importlib, "_stage_stdlib_importlib", None)
    require(host_stdlib is not None,
            "stage scope requires host-captured stdlib importlib primitives")
    factory = _StageImportFactory(root, graph, host_stdlib,
                                  policy_path=old_policy_path, policy=policy)
    replace("_ACTIVE_STAGE_FACTORY", factory)
    # Replace this module's imported facade only. The pair owns both spec
    # creation and module creation, so a standard ModuleSpec never reaches a
    # GraphImportlibFacade and no process-global object is mutated.
    replace("importlib", factory.facade())
    # Checker/configuration/executor and historical helper modules each carry
    # their own importlib global.  Pin every graph-owned owner for the entire
    # copied validation body so late resource/scoped-recovery imports cannot
    # escape into a second module graph.  The stage module itself is already
    # covered by ``scoped_spec`` above, which composes the historical-policy
    # compatibility route with the sealed graph facade.
    stage_module = sys.modules.get(__name__)
    for member in getattr(graph, "members", ()):
        owner = getattr(member, "module_object", None)
        if owner is None or owner is stage_module:
            continue
        owner_importlib = getattr(owner, "importlib", None)
        if owner_importlib is None or getattr(owner_importlib, "util", None) is None:
            continue
        bind_object(owner, "importlib", _stage_pinned_importlib(root, graph, owner_importlib, factory=factory))
    # The provider and CodeQL reader scopes are contextlib helpers whose local
    # factories/classes exist only during one real invocation. Observe those
    # exact exported helpers; do not replace their generators or synthesize a
    # same-shaped proxy. The route owner is selected by explicit graph role.
    bound_raw = ledger_bytes
    if bound_raw is None:
        bound_raw = _read(root, core.get("ledger_path", LEDGER_PATH))
    require(isinstance(bound_raw, bytes), "stage-bound ledger is not raw bytes")
    factory.bound_raw_sha256.add(sha256(bound_raw))
    lines = bound_raw.splitlines(keepends=True)
    if len(lines) >= HISTORICAL_ROWS:
        factory.bound_raw_sha256.add(sha256(b"".join(lines[:HISTORICAL_ROWS])))
    for key in ("continuation_prefix", "incoming_prefix"):
        value = core.get(key)
        if isinstance(value, Mapping):
            try:
                factory.bound_raw_sha256.add(sha256(_bound(root, value, f"stage {key}")))
            except FrozenBridgeError:
                raise
    observer_stack = contextlib.ExitStack()
    provider_owner = provider
    codeql_owner = None
    try:
        codeql_owner = _stage_member(graph, "incoming_predecessor03")
    except FrozenBridgeError:
        # Historical fixture graphs predate the explicit local-class route.
        # They retain the inherited factory tests; a production graph that
        # carries the provider/CodeQL helpers is observed below and cannot
        # bypass this route.
        codeql_owner = None
    if (codeql_owner is not None and
            callable(getattr(provider_owner, "_scoped_nested_ledger", None)) and
            callable(getattr(codeql_owner, "_scoped_resource_recovery_ledger", None))):
        observer_stack.enter_context(_stage_observe_context(
            factory, provider_owner, "_scoped_nested_ledger", "provider-nested",
            "v092_scoped_recovery_packet", _stage_source_sha(graph, "incoming_recovery"), 1))
        observer_stack.enter_context(_stage_observe_context(
            factory, codeql_owner, "_scoped_resource_recovery_ledger", "codeql-resource",
            "v092_resource_recovery", _stage_source_sha(graph, "incoming_predecessor03"), 0))
    try:
        yield
    finally:
        try:
            observer_stack.close()
        finally:
            for name, value in reversed(tuple(original.items())):
                globals()[name] = value
            for owner, name, value in reversed(object_original):
                if value is missing:
                    try:
                        delattr(owner, name)
                    except AttributeError:
                        pass
                else:
                    setattr(owner, name, value)


def _stage_build_runtime_full(root: Path, core: Mapping[str, Any], graph: Any, *, mode: str,
                              ledger_bytes: bytes | None,
                              stdlib_importlib: Any | None = None) -> dict[str, Any]:
    """Execute the complete bridge08 validation body under graph ownership."""
    modules = _stage_modules(graph, require_legacy=True)
    sink: list[dict[str, Any]] = []
    with _stage_full_graph_scope(root, core, graph, modules, mode=mode,
                                      ledger_bytes=ledger_bytes,
                                      stdlib_importlib=stdlib_importlib):
        runtime_context = _STAGE_LEGACY_LOAD_RUNTIME_CONTEXT(
            root, core, mode=mode, ledger_bytes=ledger_bytes, fixture_only=False)
    require(isinstance(runtime_context, Mapping),
            "full bridge08 runtime loader returned no context")
    runtime = dict(runtime_context)
    runtime_modules = runtime.get("modules")
    require(isinstance(runtime_modules, Mapping) and
            set(runtime_modules) == {"replacement05", "executor", "checker", "configuration"},
            "full bridge08 body returned an incomplete runtime module map")
    require(runtime_modules["replacement05"] is modules["replacement05"] and
            runtime_modules["executor"] is modules["executor"] and
            runtime_modules["checker"] is modules["checker"] and
            runtime_modules["configuration"] is modules["configuration"],
            "full bridge08 body returned foreign runtime module objects")
    validated = runtime.get("validated")
    mixed_context = runtime.get("mixed_context")
    require(isinstance(validated, Mapping) and isinstance(validated.get("plan"), Mapping),
            "full bridge08 body returned no normalized plan object")
    require(isinstance(mixed_context, Mapping) and mixed_context.get("validated") is validated,
            "full bridge08 mixed context does not retain the validated object")
    require(isinstance(runtime.get("checker_summary"), Mapping) and
            isinstance(runtime.get("configuration_summary"), Mapping),
            "full bridge08 body returned incomplete checker/configuration summaries")
    closure = _stage_closure(root, core, graph)
    diagnostic = dict(runtime.get("bridge_context", {}))
    require(isinstance(diagnostic, dict), "full bridge08 runtime loader returned no diagnostic")
    require(isinstance(diagnostic.get("validated_full_normalized_plan"), Mapping),
            "full bridge08 diagnostic omitted the complete normalized plan")
    diagnostic.update({
        "schema": STAGE_RUNTIME_SCHEMA + "/diagnostic",
        "lossless_runtime_objects": True,
        "stage_runtime_mode": mode,
        "runtime_graph_closure": closure,
        "graph_sha256": getattr(graph, "graph_sha256", None),
        "graph_membership_verified": True,
        "validated_full_normalized_plan": diagnostic.get("validated_full_normalized_plan"),
        "checker_summary_or_pending": diagnostic.get("checker_summary_or_pending"),
        "configuration_execute_false_summary_or_pending": diagnostic.get(
            "configuration_execute_false_summary_or_pending"),
    })
    diagnostic.pop("context_digest", None)
    diagnostic["context_digest"] = sha256(canonical_json(_stage_public(diagnostic)))
    runtime["diagnostic"] = diagnostic
    runtime["graph"] = graph
    return {
        "schema": STAGE_RUNTIME_SCHEMA,
        "lossless_runtime_objects": True,
        "mode": mode,
        "modules": dict(runtime_modules),
        "validated": runtime.get("validated"),
        "replacement_validated": runtime.get("replacement_validated"),
        "mixed_context": runtime.get("mixed_context"),
        "checker_summary": runtime.get("checker_summary"),
        "configuration_summary": runtime.get("configuration_summary"),
        "bridge_context": diagnostic,
        "graph": graph,
        "graph_closure": closure,
        "runtime_objects": runtime,
    }


def _stage_build_runtime(root: Path, core: Mapping[str, Any], graph: Any, *, mode: str,
                         ledger_bytes: bytes | None,
                         stdlib_importlib: Any | None = None) -> dict[str, Any]:
    # The reduced branch is a fixture-only seam for focused temporary-Git
    # tests. Production graphs always execute the copied bridge08 body above.
    if getattr(graph, "fixture_only", False):
        return _stage_build_runtime_fixture(root, core, graph, mode=mode,
                                            ledger_bytes=ledger_bytes,
                                            stdlib_importlib=stdlib_importlib)
    return _stage_build_runtime_full(root, core, graph, mode=mode,
                                     ledger_bytes=ledger_bytes,
                                     stdlib_importlib=stdlib_importlib)


_STAGE_LEGACY_LOAD_RUNTIME_CONTEXT = load_runtime_context
_STAGE_LEGACY_LOAD_AND_VALIDATE = load_and_validate


def load_runtime_context(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                         ledger_bytes: bytes | None = None, graph: Any | None = None,
                         fixture_modules: Mapping[str, Any] | None = None,
                         fixture_only: bool = False,
                         stdlib_importlib: Any | None = None) -> dict[str, Any]:
    if graph is None:
        return _STAGE_LEGACY_LOAD_RUNTIME_CONTEXT(root, core, mode=mode, ledger_bytes=ledger_bytes,
                                                   fixture_modules=fixture_modules, fixture_only=fixture_only)
    require(not fixture_only and fixture_modules is None, "graph runtime cannot inject fixture modules")
    return _stage_build_runtime(Path(root).resolve(), core, graph, mode=mode,
                                 ledger_bytes=ledger_bytes,
                                 stdlib_importlib=stdlib_importlib)


def load_and_validate(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                      ledger_bytes: bytes | None = None, graph: Any | None = None,
                      fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False, _runtime_sink: list[dict[str, Any]] | None = None,
                      stdlib_importlib: Any | None = None) -> dict[str, Any]:
    if graph is None:
        return _STAGE_LEGACY_LOAD_AND_VALIDATE(root, core, mode=mode, ledger_bytes=ledger_bytes,
                                                fixture_modules=fixture_modules, fixture_only=fixture_only,
                                                _runtime_sink=_runtime_sink)
    value = load_runtime_context(root, core, mode=mode, ledger_bytes=ledger_bytes, graph=graph,
                                 stdlib_importlib=stdlib_importlib)
    if _runtime_sink is not None:
        require(isinstance(_runtime_sink, list) and not _runtime_sink, "runtime sink must be a fresh list")
        _runtime_sink.append(value)
    return dict(value["bridge_context"])
