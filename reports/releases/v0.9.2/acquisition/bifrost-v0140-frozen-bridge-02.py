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
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "v092-bifrost-v0140-frozen-bridge/v2"
REPLACEMENT05 = {
    "path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py",
    "sha256": "32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd",
}
CONTINUATION03 = {
    "path": "reports/releases/v0.9.2/acquisition/joern-capability-continuation-03.py",
    "sha256": "06899f8e573c9e184ae25751be8581029fef9195155c7553f31ff254a85210d2",
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
HISTORICAL_ROWS = 87
CONTINUATION_ROWS = 89
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
    require(sha256(raw) == ref["sha256"], f"{label} bytes changed: {ref['path']}")
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


def _validate_normalized_source_inputs(executor: Any, validated: Mapping[str, Any],
                                       root: Path) -> list[dict[str, Any]]:
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
        expected = normalizer(plan, root, qualification)
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


def _load_continuation03(root: Path) -> Any:
    module = _load_module(root, "continuation03", CONTINUATION03)
    for export in ("_validate_base_with_historical_boundary", "_historical_contexts",
                   "_derive_context"):
        require(callable(getattr(module, export, None)),
                f"continuation-03 historical boundary lacks {export}")
    return module


def _ref_for_context(entries: Mapping[str, Any], role: str) -> tuple[str, Mapping[str, Any]]:
    matches = [(key, item) for key, item in entries.items() if item.get("role") == role]
    require(len(matches) == 1, f"source_contexts must contain exactly one {role} entry")
    return matches[0]


def _ref_json(root: Path, value: object, label: str) -> tuple[dict[str, Any], dict[str, str]]:
    ref = _ref(value, label)
    return _json(_bound(root, ref, label), label), ref


def _mixed_selected(context: Mapping[str, Any], rows: list[dict[str, Any]],
                    *, final: bool) -> dict[str, dict[str, Any]]:
    """Derive the exact rows selected by the reviewed mixed replay boundary."""
    selected: dict[str, dict[str, Any]] = {}
    if final:
        manifest = context.get("manifest")
        projection = manifest.get("final_projection_groups") if isinstance(manifest, Mapping) else None
        require(isinstance(projection, list) and projection,
                "after-run mixed context lacks the reviewed final projection")
        for row in rows:
            if row.get("status") == "completed" and row.get("exit_code") == 0:
                group_id = row.get("group_id")
                require(isinstance(group_id, str), "completed ledger row lacks group identity")
                selected[group_id] = row
        require(set(selected) == set(projection), "after-run selected groups differ from final projection")
    else:
        prefix = context.get("prefix")
        require(isinstance(prefix, list), "retained checker context lacks its immutable prefix")
        for row in rows[:len(prefix)]:
            if row.get("status") == "completed":
                group_id = row.get("group_id")
                if isinstance(group_id, str):
                    selected[group_id] = row
    return selected


def _call_mixed(replacement: Any, context: dict[str, Any], rows: list[dict[str, Any]],
                *, final: bool) -> Any:
    """Run replacement-05's actual per-group mixed-history replay.

    The frozen checker exposes one public ``verify`` API.  Retained-prefix
    validation therefore uses replacement-05's reviewed mixed-context replay
    (``_replay``), which calls the frozen checker's per-group verifier for
    every selected row.  The public ``verify`` wrapper is deliberately not
    used because it owns the old-05 admission/phase sidecar schema.  No
    invented retained-checker API is accepted.
    """
    method = getattr(replacement, "_replay", None)
    require(callable(method), "mixed-history mode requires replacement-05 _replay")
    selected = _mixed_selected(context, rows, final=final)
    try:
        return method(context, rows, selected)
    except Exception as exc:
        raise FrozenBridgeError("actual retained checker rejected the full context") from exc


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
    Its C4 resource-successor check intentionally rejects the replacement's
    authorized clock/resource overlay, so the only patched boundary is
    ``_validate_resource_recovery``.  The adapter first runs replacement-05's
    contract/qualification/runner gates, then obtains the complete historical
    recovery object by invoking continuation-03's exact C4 boundary.  It never
    accepts a caller-supplied serialized recovery or copies a replacement
    plan into a historical result.
    """
    original = getattr(executor, "_validate_resource_recovery", None)
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
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError("replacement gates rejected the scoped resource adapter") from exc

    continuation03 = _load_continuation03(root)
    base_path = root / Path(*_relative(base_ref["path"], "base source context contract").parts)
    history_rows = rows[:CONTINUATION_ROWS]
    history_raw = b"".join(raw.splitlines(keepends=True)[:CONTINUATION_ROWS])
    require(len(history_rows) == CONTINUATION_ROWS and
            len(history_raw.splitlines()) == CONTINUATION_ROWS,
            "resource adapter requires the complete immutable 89-row history")
    recovery_cache: dict[str, Any] = {}

    def scoped(validated: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(validated, Mapping) or validated.get("bytes_sha256") != contract_ref["sha256"]:
            return original(validated)
        if "value" not in recovery_cache:
            try:
                base_value = continuation03._validate_base_with_historical_boundary(
                    executor, base_path, root, history_rows, history_raw,
                )
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

    executor._validate_resource_recovery = scoped
    try:
        try:
            value = executor.validate_plan(contract_path, repo_root=root)
        except FrozenBridgeError:
            raise
        except Exception as exc:
            raise FrozenBridgeError("frozen validator rejected replacement after scoped resource checks") from exc
    finally:
        executor._validate_resource_recovery = original
    return value


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

    # Production history is reconstructed through continuation-03's reviewed
    # scoped boundary.  Directly calling validate_plan on every canonical path
    # is wrong: C1/C2/C3 archives intentionally share the canonical
    # execution-v4/contract.json path and require their registered archived
    # mode/ledger packet.  No serialized context is accepted as authority.
    continuation03 = _load_continuation03(root)
    base_key, base_entry = _ref_for_context(entries, "base")
    base_ref = _ref(base_entry["contract"], "base source context contract")
    base_raw = _bound(root, base_ref, "base source context contract")
    require(sha256(base_raw) == base_key, "base source context digest differs")
    require(base_ref["path"] == continuation03.BASE_CONTRACT and base_key == continuation03.BASE_SHA,
            "production base context is not the registered frozen C4 canonical contract")
    base_path = root / Path(*_relative(base_ref["path"], "base contract").parts)
    history_rows = rows[:CONTINUATION_ROWS]
    history_raw = b"".join(raw.splitlines(keepends=True)[:CONTINUATION_ROWS])
    require(len(history_rows) == CONTINUATION_ROWS and
            len(history_raw.splitlines()) == CONTINUATION_ROWS,
            "historical context recovery requires the complete 89-row prefix")
    try:
        base_value = continuation03._validate_base_with_historical_boundary(
            executor, base_path, root, history_rows, history_raw,
        )
    except Exception as exc:
        raise FrozenBridgeError("registered C4 frozen historical boundary rejected the ledger") from exc
    require(isinstance(base_value, dict) and base_value.get("bytes_sha256") == base_key and
            isinstance(base_value.get("plan"), dict),
            "registered C4 boundary returned no complete normalized context")
    # The historical helper itself validates C1/C2/C3 archives, retained
    # completion/failure maps, and the sealed Joern03 row.  It is intentionally
    # called with exact current bytes/rows, never with a hand-built packet.
    base_context = {"validated": base_value, "plan_commit": base_entry["plan_commit"],
                    "source_commit": base_entry["source_commit"], "role": "base"}
    try:
        recovered = continuation03._historical_contexts(
            base_value, history_rows, history_raw, base_context, root=root, executor=executor,
        )
    except Exception as exc:
        raise FrozenBridgeError("continuation-03 historical context recovery rejected the sealed roster") from exc
    require(isinstance(recovered, Mapping) and recovered,
            "continuation-03 returned no historical context map")
    contexts: dict[str, dict[str, Any]] = {}
    for key, value in recovered.items():
        require(isinstance(key, str) and SHA_RE.fullmatch(key) and isinstance(value, Mapping),
                "continuation-03 returned a malformed context key")
        validated_value = value.get("validated")
        require(isinstance(validated_value, dict) and validated_value.get("bytes_sha256") == key,
                f"continuation-03 context is not bound to {key}")
        item = entries.get(key)
        # Historical helpers return the authoritative normalized value; the
        # typed roster supplies only the independently committed identity.
        require(isinstance(item, Mapping), f"source_contexts omits recovered context {key}")
        require(item.get("role") in {"base", "historical", "continuation"},
                f"recovered context {key} has an invalid historical role")
        source_value = item["source_commit"]
        plan_value = item["plan_commit"]
        require(validated_value.get("plan", {}).get("source_commit") == source_value,
                f"recovered context {key} source commit differs")
        contexts[key] = {"validated": validated_value, "plan_commit": plan_value,
                         "source_commit": source_value, "role": item["role"]}

    # If the typed continuation is not one of the recovered immutable
    # contexts, derive it through continuation-03's exact manifest/plan
    # boundary.  The extra binding is required; a bare continuation contract
    # cannot prove the capability repair or its historical predecessor.
    continuation_key, continuation_entry = _ref_for_context(entries, "continuation")
    if continuation_key not in contexts:
        recovery = manifest_obj.get("continuation_recovery")
        require(isinstance(recovery, Mapping),
                "source evidence lacks the exact continuation-03 recovery binding")
        require(set(recovery) == {"module", "manifest", "repaired_plan"},
                "continuation recovery binding has an unreviewed field")
        module_ref = _ref(recovery["module"], "continuation recovery module")
        require(module_ref == CONTINUATION03, "continuation recovery module is not continuation-03")
        continuation_manifest, manifest_ref = _ref_json(root, recovery["manifest"],
                                                        "continuation recovery manifest")
        repaired_plan, repaired_ref = _ref_json(root, recovery["repaired_plan"],
                                                "continuation recovered plan")
        require(continuation_manifest.get("source_commit") == continuation_entry["source_commit"] and
                continuation_manifest.get("plan_commit") == continuation_entry["plan_commit"],
                "continuation recovery manifest source/plan differs from typed context")
        cont_ref = _ref(continuation_entry["contract"], "continuation source context contract")
        cont_raw = _bound(root, cont_ref, "continuation source context contract")
        try:
            cont_plan = _json(cont_raw, "continuation source context plan")
            derived = continuation03._derive_context(
                base_value, cont_plan, cont_raw, continuation_manifest, repaired_plan, executor,
            )
        except Exception as exc:
            raise FrozenBridgeError("continuation-03 could not derive the typed continuation context") from exc
        require(isinstance(derived, dict), "continuation-03 returned no continuation context")
        derived["bytes_sha256"] = continuation_key
        contexts[continuation_key] = {"validated": derived,
                                      "plan_commit": continuation_entry["plan_commit"],
                                      "source_commit": continuation_entry["source_commit"],
                                      "role": "continuation"}
    else:
        require(contexts[continuation_key]["source_commit"] == continuation_entry["source_commit"] and
                contexts[continuation_key]["plan_commit"] == continuation_entry["plan_commit"],
                "recovered continuation identity differs from typed context")

    replacement_entry = entries.get(contract_ref["sha256"])
    require(isinstance(replacement_entry, Mapping) and replacement_entry.get("role") == "replacement",
            "source_contexts lacks the exact replacement entry")
    contexts[contract_ref["sha256"]] = {"validated": current, "plan_commit": plan_commit,
                                          "source_commit": source_commit, "role": "replacement"}
    # Re-run replacement-05's reviewed lossless map builder.  Its source
    # roster is compared against the derived contexts rather than trusting
    # context-shaped JSON supplied by the caller.
    historical = {key: value for key, value in contexts.items()
                  if key not in {base_key, continuation_key, contract_ref["sha256"]}}
    try:
        result = replacement._context_map(
            base_value, contexts[continuation_key]["validated"], contexts[contract_ref["sha256"]],
            continuation_key, contract_ref["sha256"], continuation_entry["source_commit"],
            continuation_entry["plan_commit"], source_commit, plan_commit,
            dict(manifest_obj), historical,
        )
    except Exception as exc:
        raise FrozenBridgeError("replacement-05 historical context map rejected the recovered roster") from exc
    require(isinstance(result, dict) and result, "replacement-05 returned no recovered context map")
    return result


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
            len(early_continuation_rows) == CONTINUATION_ROWS and
            early_continuation_raw.startswith(early_original_raw),
            "prefixes are not the exact immutable 87/89-row witnesses")
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
            "ledger does not retain the exact immutable 89-row prefix")
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
    require(validated.get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
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
    normalized_source_inputs = _validate_normalized_source_inputs(executor, validated, root)
    shape = _shape(validated["plan"])
    require(validated["plan"].get("source_commit") == source_commit and
            validated["plan"].get("total_wall_budget_seconds") == TOTAL_WALL_SECONDS,
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
    if mode == "after" and not fixture_only:
        projection = [group.get("id") for group in validated["plan"].get("groups", [])
                      if isinstance(group, Mapping)]
        require(len(projection) == EXPECTED_GROUPS and len(set(projection)) == EXPECTED_GROUPS,
                "after-run projection cannot be derived from the complete frozen plan")
        evidence_projection = manifest_obj.get("final_projection_groups")
        if evidence_projection is not None:
            require(evidence_projection == projection,
                    "immutable source evidence final projection differs from frozen plan")
        runtime_manifest_obj = dict(manifest_obj)
        runtime_manifest_obj["final_projection_groups"] = projection
    baseline = continuation_source
    if fixture_only and "continuation_source_commit" in core:
        require(core["continuation_source_commit"] == baseline,
                "legacy continuation_source_commit differs from typed context")
    if baseline is None:
        baseline = manifest_obj.get("source_delta_baseline")
    baseline = _commit(baseline, "source-delta baseline")
    try:
        delta = replacement._source_delta(root, design_obj, manifest_obj, baseline, source_commit)
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
    require(len(original_rows) == HISTORICAL_ROWS and len(continuation_rows) == CONTINUATION_ROWS,
            "prefixes must be the exact 87-row historical and 89-row continuation witnesses")
    require(continuation_raw.startswith(original_raw), "89-row prefix does not retain exact 87-row bytes")
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
    require(current_raw.startswith(continuation_raw), "ledger does not retain the exact immutable 89-row prefix")
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
            checker_result = _call_mixed(replacement, mixed_context, rows, final=False)
        else:
            checker_result = _call_mixed(replacement, mixed_context, rows, final=True)
    except FrozenBridgeError:
        raise
    except Exception as exc:
        raise FrozenBridgeError(f"actual {mode} checker rejected context") from exc
    require(isinstance(checker_result, Mapping), "actual checker returned no structured result")
    output = core.get("configuration_output")
    require(isinstance(output, str), "configuration_output is required for execute=False validation")
    _relative(output, "configuration output namespace")
    if mode == "before" and not fixture_only:
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
    if isinstance(checker_result, Mapping):
        for field, expected in (("fresh_groups", EXPECTED_GROUPS), ("fresh_partitions", EXPECTED_PARTITIONS),
                                ("fresh_rows", EXPECTED_ROWS)):
            if field in checker_result:
                require(checker_result[field] == expected, f"checker result {field} differs from normalized shape")
    loaded = {"replacement05": REPLACEMENT05, **FROZEN}
    if not fixture_only:
        loaded["continuation03"] = CONTINUATION03
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
                         fixture_only: bool = False) -> dict[str, Any]:
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
