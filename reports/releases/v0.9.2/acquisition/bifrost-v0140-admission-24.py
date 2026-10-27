#!/usr/bin/env python3
"""Strict, one-shot Bifrost v0.14.0 replacement-24 admission writers.

The module owns the sidecar-writing boundary, but it never infers execution
identity from a caller callback.  Production writers require an exact frozen
bridge context, exact reviewed authorization, an independently checked process
permit, the canonical lock, and the replacement-24 protocol.  Fixture writes
are limited to a temporary root and an explicit test seam.
"""
from __future__ import annotations

import contextlib
import contextvars
import datetime as _datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import sys
import tempfile
import time
from typing import Any, Iterator, Mapping

ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
PROTOCOL_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-24.py"
BRIDGE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-19.py"
HELPER_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-24.py"
SUPERVISOR_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py"
FINAL_MANIFEST_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-24/manifest.json"
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
FIXTURE_ENV = "DATAFLOWBENCH_V092_REPLACEMENT24_FIXTURE_SEAM"
EXPERIMENT_ENV = "DATAFLOWBENCH_V092_REPLACEMENT24_EXPERIMENT"
# v2 deliberately removes live bridge/command digests from the human receipt.
# Those values are derived and checked under the held lock for each group;
# binding one in advance would make a future authorization impossible once the
# prior group's ledger row changes.  The receipt instead binds only finalized,
# stable execution identity and scope.
AUTHORIZATION_SCHEMA = "v092-bifrost-v0140-experiment-authorization/v2"
HUMAN_SCOPE_AMENDMENT_SCHEMA = "v092-human-scope-amendment/v2"
BATCH_AUTHORIZATION_SCHEMA = "v092-bifrost-v0140-batch-authorization/v1"
PREPARATION_HOLD_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "preparation-only-scope-01.json"
)
PREPARATION_DIRECTION_PATH = (
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/"
    "preparation-completion-direction-01.json"
)
PREPARATION_HOLD_SHA256 = "75fe01970b5ebb3eed50e59ff5043c7b38cc2fd46c246f0ce286aba21e5731e3"
PREPARATION_DIRECTION_SHA256 = "442a0c32061f10e76744285a0d03a09a99f395d2e0c935c7f6a861c5c5a3e9a8"
PROCESS_SCHEMA = "invocation-process-ownership/v1"
PERMIT_SCHEMA = "v092-bifrost-v0140-supervisor-permit/v1"
RAW_PERMIT_SCHEMA = "v092-bifrost-v0140-raw-process-permit/v1"
PARENT_SCHEMA = "v092-bifrost-v0140-parent-admission/v1"
GROUP_SCHEMA = "v092-bifrost-v0140-replacement-admission/v3"
PHASE_SCHEMA = "v092-bifrost-v0140-phase-gate/v2"
COMPLETION_SCHEMA = "v092-bifrost-v0140-replacement-completion/v3"
FROZEN_LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"

SHA_RE = __import__("re").compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = __import__("re").compile(r"[0-9a-f]{40}\Z")
RESOURCE_POLICY = {
    "minimum_free_gib": 127,
    "minimum_remaining_reserve_seconds": None,
    "minimum_replacement_seconds": 13592,
    "startup_seconds": 600,
    "aggregate_source_working_gib": 30,
    "per_source_projection_gib": 12,
}


class Admission23Error(ValueError):
    """A strict admission, sidecar, or live-gate binding failed closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise Admission23Error(message)


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


def _path(root: Path, value: str, label: str = "path") -> Path:
    current = root
    for part in _relative(value, label).parts:
        current /= part
        require(not current.is_symlink(), f"symlink in {label}: {value}")
    return current


def _lock_target(root: Path, value: object) -> Path:
    require(isinstance(value, str) and value, "lock path is missing")
    if value.startswith("/"):
        target = Path(value)
        require(value == FROZEN_LOCK_PATH or
                (_temporary_fixture(root) and target.is_absolute()),
                "production lock must be the frozen executor's canonical absolute path")
        require(not target.is_symlink(), "lock path is a symlink")
        return target
    return _path(root, value, "lock path")


def _read(root: Path, value: str, label: str = "file") -> bytes:
    path = _path(root, value, label)
    require(path.is_file(), f"missing {label}: {value}")
    return path.read_bytes()


def _ref(value: object, label: str = "ref", *, rows: bool = False) -> dict[str, Any]:
    allowed = {"path", "sha256"} | ({"rows"} if rows else set())
    require(isinstance(value, Mapping) and set(value) == allowed,
            f"{label} must be an exact path/SHA ref")
    path = value.get("path")
    digest = value.get("sha256")
    _relative(path, f"{label} path")
    require(isinstance(digest, str) and SHA_RE.fullmatch(digest), f"{label} SHA is malformed")
    if rows:
        require(type(value.get("rows")) is int and value["rows"] > 0,
                f"{label} rows are malformed")
        return {"path": path, "sha256": digest, "rows": value["rows"]}
    return {"path": path, "sha256": digest}


def _bound(root: Path, value: object, label: str = "ref", *, rows: bool = False) -> bytes:
    ref = _ref(value, label, rows=rows)
    raw = _read(root, ref["path"], label)
    require(sha256(raw) == ref["sha256"], f"{label} bytes changed")
    if rows:
        require(len(raw.splitlines()) == ref["rows"], f"{label} row count differs")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Admission23Error(f"{label} is not valid JSON") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _json_ref(root: Path, value: object, label: str) -> tuple[dict[str, Any], dict[str, str]]:
    ref = _ref(value, label)
    return _json(_bound(root, ref, label), label), ref


def _validate_parent_receipt(protocol: Any, root: Path, manifest_path: str,
                             parent_ref: Mapping[str, Any]) -> dict[str, Any]:
    """Pass the receipt path to the protocol, never its path/SHA wrapper."""
    ref = _ref(parent_ref, "parent admission")
    _bound(root, ref, "parent admission")
    return protocol.validate_parent_admission(root, manifest_path, ref["path"])


def _validate_group_receipt(protocol: Any, root: Path, manifest_path: str,
                            group_id: str, group_ref: Mapping[str, Any]) -> dict[str, Any]:
    """Pass the receipt path to the protocol, preserving its digest binding."""
    ref = _ref(group_ref, "group admission")
    _bound(root, ref, "group admission")
    return protocol.validate_group_admission(root, manifest_path, group_id, ref["path"])


def _validate_scope_amendment(root: Path, value: object) -> dict[str, Any]:
    """Validate the later human receipt that can supersede preparation hold.

    The current preparation-only receipt is never itself treated as an
    experiment grant.  A future grant must be a separate typed amendment that
    explicitly supersedes both the exact hold and its preparation direction.
    """
    ref = _ref(value, "human scope amendment")
    amendment = _json(_bound(root, ref, "human scope amendment"), "human scope amendment")
    required = {"schema", "status", "human_approved", "experiment_authorized",
                "automatic_retry", "scope", "supersedes"}
    require(set(amendment) == required, "human scope amendment has an unexpected field set")
    require(amendment.get("schema") == HUMAN_SCOPE_AMENDMENT_SCHEMA and
            amendment.get("status") == "approved" and
            amendment.get("human_approved") is True and
            amendment.get("experiment_authorized") is True and
            amendment.get("automatic_retry") is False and
            amendment.get("scope") == "bifrost-v0140-replacement-24",
            "human scope amendment is not an explicit experiment grant")
    supersedes = amendment.get("supersedes")
    require(isinstance(supersedes, Mapping) and
            set(supersedes) == {"preparation_only_scope", "preparation_direction"},
            "human scope amendment lacks the exact preparation supersession")
    expected = {
        "preparation_only_scope": (PREPARATION_HOLD_PATH, PREPARATION_HOLD_SHA256),
        "preparation_direction": (PREPARATION_DIRECTION_PATH, PREPARATION_DIRECTION_SHA256),
    }
    for name, (path, digest) in expected.items():
        nested = _ref(supersedes[name], f"human scope amendment {name}")
        require(nested == {"path": path, "sha256": digest},
                f"human scope amendment {name} is not the current receipt")
        _bound(root, nested, f"human scope amendment {name}")
    return amendment


def _commit(value: object, label: str) -> str:
    require(isinstance(value, str) and COMMIT_RE.fullmatch(value), f"{label} is not a commit SHA")
    return value


def _digest(value: object, label: str) -> str:
    require(isinstance(value, str) and SHA_RE.fullmatch(value), f"{label} is not a SHA-256")
    return value


def _load_module(root: Path, relative: str, name: str) -> Any:
    path = _path(root, relative, f"{name} source")
    require(path.is_file(), f"missing {name} source")
    before = sha256(path.read_bytes())
    spec = importlib.util.spec_from_file_location(f"v092_replacement10_{name}", path)
    require(spec is not None and spec.loader is not None, f"cannot load {name} source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha256(path.read_bytes()) == before, f"{name} source changed during import")
    return module


def _load_protocol(root: Path) -> Any:
    active = _ACTIVE_STAGE.get()
    if active is not None:
        return active["protocol"]
    return _load_module(root, PROTOCOL_PATH, "replacement-24 protocol")


def _load_bridge(root: Path, core: Mapping[str, Any]) -> Any:
    active = _ACTIVE_STAGE.get()
    if active is not None:
        active["graph"].assert_member("bridge19", active["bridge"])
        return active["bridge"]
    ref = _ref(core.get("frozen_bridge_source"), "core frozen_bridge_source")
    require(ref["path"] == BRIDGE_PATH, "bridge source path is not canonical replacement-24 bridge")
    path = _path(root, ref["path"], "frozen bridge source")
    before = _bound(root, ref, "frozen bridge source")
    tests = _ref(core.get("frozen_bridge_tests"), "core frozen_bridge_tests")
    require(tests["path"] == "reports/releases/v0.9.2/acquisition/test-bifrost-v0140-frozen-parser-19.py",
            "bridge focused-test path is not the registered actual-parser test08")
    spec = importlib.util.spec_from_file_location("v092_replacement10_frozen_bridge", path)
    require(spec is not None and spec.loader is not None, "cannot load frozen bridge")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha256(path.read_bytes()) == sha256(before) == ref["sha256"],
            "frozen bridge source changed during import")
    require(callable(getattr(module, "validate_frozen_bridge", None)),
            "frozen bridge lacks validate_frozen_bridge")
    return module


def _validate_bridge_context(root: Path, core: Mapping[str, Any], bridge_context: object) -> dict[str, Any]:
    require(isinstance(bridge_context, Mapping), "frozen bridge context must be an object")
    active = _ACTIVE_STAGE.get()
    if active is not None:
        require(bridge_context is active["context"], "bridge diagnostic is not retained actual stage output")
    context = bridge_context if active is not None else dict(bridge_context)
    require(context.get("execution_authorized") is False,
            "preparation bridge context cannot authorize execution")
    require(context.get("status") in {"preparation-only-static-bridge-validated", "static-bridge-validated",
                                        "read-only-frozen-validation-passed"},
            "frozen bridge context is not a validated preparation result")
    digest = context.get("context_digest")
    _digest(digest, "bridge context digest")
    if active is None:
        without_digest = dict(context)
        without_digest.pop("context_digest", None)
        require(sha256(canonical_json(without_digest)) == digest,
                "bridge context digest does not match its immutable fields")
    # The actual opaque stage already binds this exact runtime context; do not
    # serialize its gigabyte diagnostic anew at every same-stage receipt call.
    require(context.get("source_commit") == core.get("source_commit") and
            context.get("plan_commit") == core.get("plan_commit"),
            "bridge source/plan identity differs from core")
    contract = context.get("canonical_contract_path_and_contract_sha256")
    require(contract == core.get("contract"), "bridge contract differs from core")
    require(context.get("original_prefix_ref") == core.get("original_prefix") and
            context.get("continuation_prefix_ref") == core.get("continuation_prefix"),
            "bridge prefix refs differ from core")
    require(context.get("exact_replacement_group_subset_derived_from_full_plan") ==
            core.get("replacement_groups"), "bridge group order is not derived from core")
    require(isinstance(context.get("historical_context_map_keyed_by_contract_sha256"), Mapping),
            "bridge context map is missing")
    require(isinstance(context.get("validated_full_normalized_plan"), Mapping),
            "bridge normalized plan is missing")
    return context


def _protocol_static(root: Path, manifest_path: str, manifest_sha256: str) -> dict[str, Any]:
    protocol = _load_protocol(root)
    require(callable(getattr(protocol, "validate_static", None)), "replacement-24 protocol lacks validate_static")
    static = protocol.validate_static(root, manifest_path)
    require(isinstance(static, Mapping), "protocol static result is not an object")
    require(static.get("manifest_ref", {}).get("sha256") == manifest_sha256,
            "protocol static manifest digest differs")
    return dict(static)


def _temporary_fixture(root: Path) -> bool:
    if os.environ.get(FIXTURE_ENV) != "1" or root.resolve() == ROOT.resolve():
        return False
    # Fixture writes are confined to the operating system's temporary tree;
    # an environment marker must never turn another checkout into a writable
    # production-looking fixture.
    try:
        root.resolve().relative_to(Path(tempfile.gettempdir()).resolve())
    except ValueError:
        return False
    return True


def _require_execution_permission(root: Path, *, fixture_only: bool) -> None:
    if fixture_only:
        require(_temporary_fixture(root), "fixture writes require a temporary root")
        require(os.environ.get(FIXTURE_ENV) == "1", "fixture seam is not enabled")
    else:
        require(os.environ.get(EXPERIMENT_ENV) == "1",
                "replacement-24 execution requires the explicit reviewed experiment marker")


def _authorization(root: Path, value: object, digest: str, *, scope: str,
                   core: Mapping[str, Any], manifest: Mapping[str, Any],
                   manifest_path: str, manifest_sha256: str,
                   bridge_context: Mapping[str, Any], group_id: str | None = None,
                   attempt_id: str | None = None, command_sha256: str | None = None) -> dict[str, Any]:
    """Validate a stable human approval and leave live bindings to the gate.

    ``bridge_context`` and ``command_sha256`` remain parameters because the
    callers validate the actual per-group context and command immediately
    around this boundary.  They are intentionally *not* compared with the
    human receipt: the context includes mutable ledger/checker state and the
    command digest therefore cannot be known when a future human approval is
    recorded.  The supervisor permit and ``_validate_command_spec`` bind those
    values mechanically under the canonical lock.
    """
    ref = _ref(value, "authorization")
    raw = _bound(root, ref, "authorization")
    require(ref["sha256"] == digest and sha256(raw) == digest, "authorization digest differs")
    auth = _json(raw, "authorization")
    # All fields here are stable after the finalized manifest is sealed.  In
    # particular, there is no context digest or command digest field: either
    # would bind an unknown future ledger state into a human receipt.
    required = {"schema", "status", "human_approved", "automatic_retry", "scope",
                "core_identity", "manifest_path", "manifest_sha256", "source_commit",
                "plan_commit", "contract_sha256", "admission_source", "supervisor_source",
                "group_roster", "attempt_roster", "attempt_limits", "original_clock",
                "hold_supersession"}
    require(set(auth) >= required and not (set(auth) - {
        *required, "group_id", "attempt_id", "authorization_id"
    }), "authorization has an unexpected field set")
    require(auth.get("schema") == AUTHORIZATION_SCHEMA and auth.get("status") == "approved" and
            auth.get("human_approved") is True and auth.get("automatic_retry") is False and
            auth.get("scope") == scope, "authorization is not an exact one-shot approval")
    identity_ref = _ref(manifest.get("core_identity"), "manifest core identity")
    require(core.get("identity_ref") == identity_ref and auth.get("core_identity") == identity_ref,
            "authorization core identity differs")
    require(auth.get("manifest_path") == manifest_path and
            auth.get("manifest_sha256") == manifest_sha256 and
            auth.get("source_commit") == core.get("source_commit") and
            auth.get("plan_commit") == core.get("plan_commit") and
            auth.get("contract_sha256") == core.get("contract", {}).get("sha256"),
            "authorization does not bind exact execution identity")
    require(auth.get("admission_source") == core.get("bifrost_admission_source") and
            auth.get("supervisor_source") == core.get("bifrost_supervisor_source"),
            "authorization does not bind exact control source roles")

    groups = core.get("dispatch_groups")
    require(isinstance(groups, list) and groups and all(isinstance(x, str) and x for x in groups),
            "core replacement group roster is malformed")
    slots = manifest.get("execution_admission_slots")
    require(isinstance(slots, Mapping) and set(slots) == set(groups),
            "manifest execution slot roster differs from core")
    attempt_roster: dict[str, str] = {}
    for group in groups:
        slot = slots.get(group)
        require(isinstance(slot, Mapping) and isinstance(slot.get("attempt_id"), str) and slot["attempt_id"],
                f"manifest attempt roster is missing {group}")
        attempt_roster[group] = slot["attempt_id"]
    require(auth.get("group_roster") == list(groups) and
            auth.get("attempt_roster") == attempt_roster,
            "authorization group/attempt roster differs")

    plan = bridge_context.get("validated_full_normalized_plan")
    require(isinstance(plan, Mapping) and isinstance(plan.get("plan"), Mapping),
            "authorization cannot derive the complete attempt limits")
    plan_groups = plan["plan"].get("groups")
    require(isinstance(plan_groups, list), "normalized plan group roster is missing")
    limits: dict[str, int] = {}
    for item in plan_groups:
        if not isinstance(item, Mapping) or item.get("id") not in groups:
            continue
        maximum = item.get("maximum_attempts")
        require(type(maximum) is int and maximum > 0,
                f"normalized plan attempt limit is malformed for {item.get('id')}")
        limits[item["id"]] = maximum
    require(set(limits) == set(groups) and auth.get("attempt_limits") == limits,
            "authorization global attempt limits differ")

    expected_clock = {
        "origin_utc": core.get("original_origin_utc"),
        "cutoff_utc": core.get("cutoff_utc"),
        "total_wall_budget_seconds": core.get("total_wall_budget_seconds"),
    }
    require(isinstance(expected_clock["origin_utc"], str) and
            expected_clock["cutoff_utc"] is None and
            expected_clock["total_wall_budget_seconds"] is None and
            auth.get("original_clock") == expected_clock,
            "authorization original clock differs")

    # The hold supersession is itself immutable evidence.  Its digest is a
    # stable human-scope binding; its contents are intentionally not folded
    # into the per-group context digest, so no future ledger state can alter
    # this authorization predicate.
    hold_ref = _ref(auth.get("hold_supersession"), "authorization hold supersession")
    _validate_scope_amendment(root, hold_ref)

    # Require an actual, previously validated live context, but do not bind
    # its digest into the human approval.  _validate_bridge_context is called
    # by every public writer before this function and command/permit checks
    # below bind the refreshed digest mechanically.
    require(isinstance(bridge_context, Mapping) and
            SHA_RE.fullmatch(str(bridge_context.get("context_digest", ""))),
            "authorization lacks a current validated bridge context")
    del command_sha256
    if scope in {"parent", "configuration"}:
        require(auth.get("group_id") is None and auth.get("attempt_id") is None and
                "command_sha256" not in auth, "parent authorization carries group identity")
    else:
        require(auth.get("group_id") == group_id and auth.get("attempt_id") == attempt_id and
                auth.get("group_id") in groups and auth.get("attempt_id") == attempt_roster[auth["group_id"]],
                "group authorization differs")
    return auth


def _process(value: object) -> dict[str, Any]:
    require(isinstance(value, Mapping), "process evidence must be an object")
    result = dict(value)
    require(result.get("schema") == PROCESS_SCHEMA and result.get("status") == "verified" and
            result.get("automatic_retry") is False and result.get("no_foreign_processes") is True,
            "process evidence is not verified")
    require(type(result.get("pid")) is int and result["pid"] > 0 and
            isinstance(result.get("birth_identity"), str) and result["birth_identity"],
            "process evidence lacks PID/birth identity")
    try:
        os.kill(result["pid"], 0)
    except OSError as exc:
        raise Admission23Error("process evidence PID is not live") from exc
    return result


# Same-process authority: serialized diagnostics never substitute for a stage.
_ACTIVE_STAGE = contextvars.ContextVar("bf23_admission_stage", default=None)

def _stage_bindings(root, stage, graph, pinned_bridge):
    require(stage is not None and graph is not None and pinned_bridge is not None,
            "production admission requires explicit opaque stage, graph and pinned_bridge")
    graph.assert_member("bridge19", pinned_bridge)
    require(graph.module("admission24").__dict__ is globals(), "admission is not graph-owned module instance")
    require(isinstance(stage, pinned_bridge._OpaqueStage), "reconstructed/foreign stage is forbidden")
    stage.assert_graph(graph)
    pinned_bridge.assert_stage_current(Path(root).resolve(), stage, graph)
    opaque_runtime = stage.runtime
    returned_runtime = pinned_bridge.runtime_objects(stage)
    require(returned_runtime is opaque_runtime, "bridge returned copied runtime authority")
    if isinstance(opaque_runtime, pinned_bridge.ActualRuntimeContext):
        runtime = opaque_runtime.objects
        require(opaque_runtime.graph is graph, "runtime graph instance differs")
        require(opaque_runtime.root == Path(root).resolve(), "runtime checkout differs")
        require(runtime is opaque_runtime.objects, "bridge returned copied runtime objects")
        actual_modules = runtime.get("modules")
        require(isinstance(actual_modules, Mapping) and
                tuple(actual_modules) == ("replacement05", "executor", "checker", "configuration"),
                "runtime object map lost its frozen module roster")
        require(actual_modules["replacement05"] is pinned_bridge._replacement_runtime_member(graph) and
                all(actual_modules[name] is graph.module(name)
                    for name in ("executor", "checker", "configuration")),
                "runtime object map lost exact pinned module instances")
    else:
        require(graph.fixture_only is True and isinstance(opaque_runtime, Mapping),
                "production requires actual opaque runtime context")
        runtime = opaque_runtime
    require(isinstance(runtime, Mapping), "stage does not retain actual runtime objects")
    static = runtime.get("protocol_static")
    context = runtime.get("bridge_context")
    require(isinstance(static, Mapping) and isinstance(context, Mapping),
            "actual stage runtime lacks protocol_static or bridge_context")
    protocol = graph.module("protocol24")
    return {"stage": stage, "graph": graph, "bridge": pinned_bridge,
            "runtime": runtime, "static": static, "context": context, "protocol": protocol}


def _stage_entry(fn):
    def staged(*args, stage=None, pinned_bridge=None, graph=None,
               predecessor_stage=None, successor_stage=None, **kwargs):
        root = args[0] if args else kwargs.get("root")
        active = _ACTIVE_STAGE.get()
        if stage is None and successor_stage is not None:
            stage = successor_stage
        if stage is None and active is not None:
            stage, graph, pinned_bridge = active["stage"], active["graph"], active["bridge"]
        if stage is None:
            require(kwargs.get("fixture_only") is True and _temporary_fixture(Path(root).resolve()),
                    "production API cannot use serialized bridge context without a stage")
            return fn(*args, **kwargs)
        bindings = _stage_bindings(root, stage, graph, pinned_bridge)
        bindings["predecessor"] = predecessor_stage
        token = _ACTIVE_STAGE.set(bindings)
        try:
            with bindings["protocol"].stage_context(root, stage=stage, graph=graph,
                                                    pinned_bridge=pinned_bridge):
                return fn(*args, **kwargs)
        finally:
            _ACTIVE_STAGE.reset(token)
    staged.__name__ = fn.__name__
    staged.__doc__ = fn.__doc__
    return staged


@_stage_entry
def validate_authorization_bundle(root: Path | str, manifest_path: str, manifest_sha256: str,
                                  bridge_context: Mapping[str, Any], bundle_ref: object,
                                  bundle_sha256: str) -> dict[str, Any]:
    """Validate every stable human/group/config receipt before dispatch.

    A batch must present one immutable bundle.  Every group authorization is
    checked before the first child can be created; the per-group context and
    command digest remain dynamic mechanical bindings in ``admit_group`` and
    ``_validate_command_spec``.
    """
    root = Path(root).resolve()
    manifest, core, _protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    ref = _ref(bundle_ref, "authorization bundle")
    require(ref["sha256"] == bundle_sha256, "authorization bundle digest differs")
    bundle = _json(_bound(root, ref, "authorization bundle"), "authorization bundle")
    groups = core.get("dispatch_groups")
    require(isinstance(groups, list) and groups, "authorization bundle has no reviewed groups")
    required = {"schema", "status", "automatic_retry", "scope", "parent", "groups",
                "configuration", "experiment_authorization"}
    require(set(bundle) == required, "authorization bundle has an unexpected field set")
    require(bundle.get("schema") == BATCH_AUTHORIZATION_SCHEMA and
            bundle.get("status") == "approved" and
            bundle.get("automatic_retry") is False and
            bundle.get("scope") == "bifrost-v0140-replacement-24",
            "authorization bundle is not an approved one-shot scope")
    amendment_ref = _ref(bundle.get("experiment_authorization"), "bundle experiment authorization")
    _validate_scope_amendment(root, amendment_ref)
    refs: dict[str, Any] = {
        "bundle": ref, "experiment_authorization": amendment_ref,
        "parent": _ref(bundle.get("parent"), "bundle parent authorization"),
        "configuration": _ref(bundle.get("configuration"), "bundle configuration authorization"),
    }
    group_refs = bundle.get("groups")
    require(isinstance(group_refs, Mapping) and set(group_refs) == set(groups),
            "authorization bundle group roster differs")
    refs["groups"] = {group: _ref(group_refs[group], f"bundle {group} authorization") for group in groups}
    identity_core = {**core, "identity_ref": manifest["core_identity"]}
    _authorization(root, refs["parent"], refs["parent"]["sha256"], scope="parent",
                   core=identity_core, manifest=manifest, manifest_path=manifest_path,
                   manifest_sha256=manifest_sha256, bridge_context=bridge_context)
    for group in groups:
        slot = manifest["execution_admission_slots"][group]
        _authorization(root, refs["groups"][group], refs["groups"][group]["sha256"], scope="group",
                       core=identity_core, manifest=manifest, manifest_path=manifest_path,
                       manifest_sha256=manifest_sha256, bridge_context=bridge_context,
                       group_id=group, attempt_id=slot["attempt_id"])
    _authorization(root, refs["configuration"], refs["configuration"]["sha256"], scope="configuration",
                   core=identity_core, manifest=manifest, manifest_path=manifest_path,
                   manifest_sha256=manifest_sha256, bridge_context=bridge_context)
    return {"bundle": bundle, **refs}


def _permit(root: Path, value: object, *, scope: str, group_id: str | None,
            attempt_id: str | None, command_sha256: str | None) -> dict[str, Any]:
    ref = _ref(value, "supervisor permit")
    permit = _json(_bound(root, ref, "supervisor permit"), "supervisor permit")
    require(permit.get("schema") == RAW_PERMIT_SCHEMA and permit.get("scope") == scope and
            permit.get("automatic_retry") is False, "supervisor permit schema/scope differs")
    require(type(permit.get("pid")) is int and permit["pid"] > 0 and
            isinstance(permit.get("birth"), str) and permit["birth"] and
            isinstance(permit.get("token"), str) and permit["token"],
            "supervisor permit lacks process identity")
    require(isinstance(permit.get("argv_sha256"), str) and SHA_RE.fullmatch(permit["argv_sha256"]) and
            isinstance(permit.get("permit_id"), str) and permit["permit_id"],
            "supervisor permit argv digest is malformed")
    require(permit.get("group_id") == group_id and permit.get("attempt_id") == attempt_id,
            "supervisor permit group identity differs")
    require(permit.get("command_spec_sha256") == command_sha256,
            "supervisor permit command identity differs")
    active = _ACTIVE_STAGE.get()
    if active is not None:
        require(permit.get("stage_identity_sha256") == active["stage"].identity_sha256 and
                permit.get("graph_sha256") == active["graph"].graph_sha256,
                "raw permit escaped the actual stage/graph")
        if scope == "group":
            require(permit.get("parent_stage_identity_sha256") == active["stage"].identity_sha256,
                    "raw group permit parent stage identity differs")
    try:
        os.kill(permit["pid"], 0)
    except OSError as exc:
        raise Admission23Error("supervisor permit PID is not live") from exc
    return permit


def _policy_sha(policy: Mapping[str, Any]) -> str:
    return sha256(canonical_json(dict(policy)))


def _live_resources(root: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    policy = core.get("resource_policy", RESOURCE_POLICY)
    require(policy == RESOURCE_POLICY, "resource policy lowers or changes the reviewed floor")
    free = shutil.disk_usage(root).free
    require(free >= policy["minimum_free_gib"] * 1024 ** 3, "free-space floor is below 127 GiB")
    protocol = _load_protocol(root)
    protocol.validate_execution_window(root, core)
    protocol.validate_working_cap(root, core)
    remaining = None
    return {
        "resource_floor_checked": True,
        "observed_free_bytes": free,
        "remaining_reserved_seconds": remaining,
        "resource_policy": dict(policy),
        "resource_policy_sha256": _policy_sha(policy),
    }


class _HeldLock:
    def __init__(self, path: Path, stream: Any):
        self.path = path
        self.stream = stream
        self.closed = False

    def assert_live(self, expected: str) -> None:
        require(not self.closed and self.path.as_posix() == expected,
                "exclusive lock is not held for the canonical path")


@contextlib.contextmanager
def exclusive_lock(root: Path | str, lock_path: str) -> Iterator[_HeldLock]:
    root = Path(root).resolve()
    path = _lock_target(root, lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), "lock path is a symlink")
    stream = path.open("a+")
    try:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Admission23Error("canonical lock is already held") from exc
        held = _HeldLock(path, stream)
        yield held
    finally:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            held.closed = True
            stream.close()


def _require_lock(lock: _HeldLock | None, root: Path, core: Mapping[str, Any]) -> None:
    require(lock is not None, "writer requires the canonical lock handle")
    lock.assert_live(str(_lock_target(root, core["lock_path"])))


def _write_json_exclusive(root: Path, path: str, value: Mapping[str, Any]) -> dict[str, str]:
    raw = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode() + b"\n"
    target = _path(root, path, "sidecar path")
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists() and not target.is_symlink(), "sidecar path was already consumed")
    with target.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": path, "sha256": sha256(raw)}


def _write_bytes_exclusive(root: Path, path: str, raw: bytes) -> dict[str, str]:
    target = _path(root, path, "witness path")
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists() and not target.is_symlink(), "witness path was already consumed")
    with target.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": path, "sha256": sha256(raw)}


def _bridge_core(context: Mapping[str, Any]) -> dict[str, Any]:
    # The protocol static result normally wraps core under "core".  Keep this
    # narrow adapter explicit so no caller can pass an arbitrary context shape.
    core = context.get("core")
    require(isinstance(core, Mapping), "protocol static result lacks core identity")
    return dict(core)


@_stage_entry
def validate_preparation(root: Path | str, manifest_path: str, manifest_sha256: str,
                         bridge_context: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    require(manifest_path == FINAL_MANIFEST_PATH, "only canonical replacement-24 manifest is accepted")
    current = _ACTIVE_STAGE.get()
    if current is not None:
        static = current["static"]
        require(static.get("manifest_ref") == {"path": manifest_path, "sha256": manifest_sha256},
                "stage static manifest binding differs from caller")
        require(bridge_context is current["context"], "serialized/foreign bridge context cannot replace actual stage context")
        core = _bridge_core(static)
        _validate_bridge_context(root, core, bridge_context)
        return {**static, "bridge_context": bridge_context}
    static = _protocol_static(root, manifest_path, manifest_sha256)
    core = _bridge_core(static)
    _validate_bridge_context(root, core, bridge_context)
    bridge = _load_bridge(root, core)
    require(callable(getattr(bridge, "load_and_validate", None)),
            "frozen bridge lacks the actual read-only validation API")
    try:
        actual = bridge.load_and_validate(root, core, mode="before")
    except Exception as exc:
        raise Admission23Error("actual frozen bridge validation rejected preparation context") from exc
    require(isinstance(actual, Mapping) and dict(actual) == dict(bridge_context),
            "caller bridge context differs from actual frozen validation output")
    return {**static, "bridge_context": dict(bridge_context)}


@_stage_entry
def _manifest_context(root: Path, manifest_path: str, manifest_sha256: str,
                      bridge_context: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], Any]:
    static = validate_preparation(root, manifest_path, manifest_sha256, bridge_context)
    return dict(static["manifest"]), dict(static["core"]), (_ACTIVE_STAGE.get()["protocol"] if _ACTIVE_STAGE.get() is not None else _load_protocol(root))


def _permit_value(raw: Mapping[str, Any], identity: Mapping[str, Any], manifest_path: str,
                  helper: Mapping[str, str], supervisor: Mapping[str, str], scope: str,
                  group_id: str | None, attempt_id: str | None) -> dict[str, Any]:
    result = {
        "schema": PERMIT_SCHEMA, "status": "permitted",
        "automatic_retry": False,
        "scope": scope,
        "identity": dict(identity),
        "manifest_path": manifest_path,
        "helper": dict(helper),
        "supervisor": dict(supervisor),
        "permit_id": raw["permit_id"],
    }
    result["core_identity"] = result.pop("identity")
    if group_id is not None:
        result["group_id"] = group_id
        result["attempt_id"] = attempt_id
    return result


@_stage_entry
def admit_parent(root: Path | str, manifest_path: str, manifest_sha256: str,
                 authorization_ref: object, authorization_sha256: str,
                 permit_ref: object, process_evidence: object,
                 bridge_context: Mapping[str, Any], *, fixture_only: bool = False,
                 lock: _HeldLock | None = None) -> dict[str, str]:
    root = Path(root).resolve()
    _require_execution_permission(root, fixture_only=fixture_only)
    manifest, core, protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    identity_ref = manifest["core_identity"]
    bridge = _validate_bridge_context(root, core, bridge_context)
    _authorization(root, authorization_ref, authorization_sha256, scope="parent", core={**core, "identity_ref": identity_ref},
                   manifest=manifest,
                   manifest_path=manifest_path, manifest_sha256=manifest_sha256, bridge_context=bridge)
    process = _process(process_evidence)
    resources = _live_resources(root, core)
    raw_permit = _permit(root, permit_ref, scope="parent", group_id=None, attempt_id=None, command_sha256=None)
    permit = _permit_value(raw_permit, identity_ref, manifest_path, core["bifrost_admission_source"],
                           core["bifrost_supervisor_source"], "parent", None, None)
    own_lock = contextlib.nullcontext(lock) if lock else exclusive_lock(root, core["lock_path"])
    with own_lock as held:
        _require_lock(held, root, core)
        namespace = str(core["sidecar_namespace"])
        path = f"{namespace}/parent-admission.json"
        value = {
            "schema": PARENT_SCHEMA, "status": "ready", "automatic_retry": False,
            "core_identity": identity_ref, "manifest_path": manifest_path,
            "manifest_sha256": manifest_sha256, "helper": core["bifrost_admission_source"],
            "supervisor": core["bifrost_supervisor_source"], "supervisor_permit": permit,
            "process_ownership": process,
            "lock": {"schema": "exclusive-lock/v1", "status": "held", "automatic_retry": False,
                     "path": core["lock_path"], "owner_pid": process["pid"],
                     "owner_birth": process["birth_identity"]},
            "fresh_namespace": {"schema": "fresh-sidecar-namespace/v1", "status": "fresh",
                                "automatic_retry": False, "path": namespace, "fresh": True, "sidecar_count": 0,
                                "created_by": process["pid"]},
            "resource_policy": resources["resource_policy"],
            "resource_policy_sha256": resources["resource_policy_sha256"],
            "remaining_reserved_seconds": resources["remaining_reserved_seconds"],
        }
        result = _write_json_exclusive(root, path, value)
        protocol.validate_parent_admission(root, manifest_path, path)
        return result


@_stage_entry
def admit_configuration(root: Path | str, manifest_path: str, manifest_sha256: str,
                        authorization_ref: object, authorization_sha256: str,
                        permit_ref: object, process_evidence: object,
                        bridge_context: Mapping[str, Any], *, fixture_only: bool = False,
                        lock: _HeldLock | None = None) -> dict[str, str]:
    """Write the configuration admission under the same one-shot lock."""
    root = Path(root).resolve()
    _require_execution_permission(root, fixture_only=fixture_only)
    manifest, core, protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    bridge = _validate_bridge_context(root, core, bridge_context)
    identity_ref = manifest["core_identity"]
    _authorization(root, authorization_ref, authorization_sha256, scope="configuration",
                   core={**core, "identity_ref": identity_ref}, manifest=manifest,
                   manifest_path=manifest_path,
                   manifest_sha256=manifest_sha256, bridge_context=bridge)
    process = _process(process_evidence)
    resources = _live_resources(root, core)
    raw_permit = _permit(root, permit_ref, scope="configuration", group_id=None,
                         attempt_id=None, command_sha256=None)
    permit = _permit_value(raw_permit, identity_ref, manifest_path,
                           core["bifrost_admission_source"], core["bifrost_supervisor_source"],
                           "configuration", None, None)
    own_lock = contextlib.nullcontext(lock) if lock else exclusive_lock(root, core["lock_path"])
    with own_lock as held:
        _require_lock(held, root, core)
        slot = manifest["configuration_admission_slot"]
        path = slot["admission_path"]
        value = {
            "schema": "v092-bifrost-v0140-configuration-admission/v1", "status": "ready",
            "automatic_retry": False, "scope": "configuration", "core_identity": identity_ref,
            "manifest_path": manifest_path, "manifest_sha256": manifest_sha256,
            "admission_source": core["bifrost_admission_source"],
            "supervisor_source": core["bifrost_supervisor_source"],
            "helper": core["bifrost_admission_source"],
            "supervisor": core["bifrost_supervisor_source"], "supervisor_permit": permit,
            "resource_policy": resources["resource_policy"],
            "resource_policy_sha256": resources["resource_policy_sha256"],
            "remaining_reserved_seconds": resources["remaining_reserved_seconds"],
        }
        result = _write_json_exclusive(root, path, value)
        protocol.validate_configuration_admission(root, manifest_path, path)
        return result


def _read_jsonl(root: Path, path: str) -> tuple[bytes, list[dict[str, Any]]]:
    raw = _read(root, path, "ledger")
    rows = []
    for line_no, line in enumerate(raw.splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Admission23Error(f"ledger line {line_no} is not JSON") from exc
        require(isinstance(value, dict), f"ledger line {line_no} is not an object")
        rows.append(value)
    require(raw.endswith(b"\n") and rows, "ledger is empty or not newline terminated")
    return raw, rows


def _validate_command_spec(value: object, *, group_id: str, attempt_id: str,
                           bridge_context: Mapping[str, Any]) -> dict[str, Any]:
    require(isinstance(value, Mapping), "command spec must be an object")
    spec = dict(value)
    required = {"schema", "group_id", "attempt_id", "argv", "argv_sha256", "command_spec_sha256",
                "context_digest", "canonical_contract", "source_commit", "plan_commit", "environment"}
    active = _ACTIVE_STAGE.get()
    if active is not None:
        required |= {"stage_identity_sha256", "graph_sha256", "parent_stage_identity_sha256"}
        require(spec.get("stage_identity_sha256") == active["stage"].identity_sha256 and
                spec.get("parent_stage_identity_sha256") == active["stage"].identity_sha256 and
                spec.get("graph_sha256") == active["graph"].graph_sha256,
                "command escaped the actual ready parent stage/graph")
    require(set(spec) == required, "command spec has an unexpected field set")
    require(spec["schema"] == "v092-bifrost-v0140-frozen-command/v1" and
            spec["group_id"] == group_id and spec["attempt_id"] == attempt_id,
            "command spec identity differs")
    require(isinstance(spec["argv"], list) and spec["argv"] and
            all(isinstance(item, str) and item for item in spec["argv"]),
            "command argv is malformed")
    require(sha256(canonical_json(spec["argv"])) == spec["argv_sha256"], "command argv digest differs")
    no_spec = dict(spec)
    command_digest = no_spec.pop("command_spec_sha256")
    require(sha256(canonical_json(no_spec)) == command_digest, "command spec digest differs")
    require(spec["context_digest"] == bridge_context["context_digest"] and
            spec["source_commit"] == bridge_context["source_commit"] and
            spec["plan_commit"] == bridge_context["plan_commit"] and
            spec["canonical_contract"] == bridge_context["canonical_contract_path_and_contract_sha256"],
            "command spec escaped the frozen bridge context")
    require(isinstance(spec["environment"], dict) and
            all(isinstance(k, str) and isinstance(v, str) for k, v in spec["environment"].items()),
            "command environment is malformed")
    return spec


@_stage_entry
def admit_group(root: Path | str, manifest_path: str, manifest_sha256: str, group_id: str,
                authorization_ref: object, authorization_sha256: str, permit_ref: object,
                parent_admission_ref: object, process_evidence: object,
                bridge_context: Mapping[str, Any], command_spec: Mapping[str, Any], *,
                fixture_only: bool = False, lock: _HeldLock | None = None) -> dict[str, str]:
    root = Path(root).resolve()
    _require_execution_permission(root, fixture_only=fixture_only)
    manifest, core, protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    bridge = _validate_bridge_context(root, core, bridge_context)
    slots = manifest["execution_admission_slots"]
    require(group_id in slots, "group is outside the reviewed replacement order")
    slot = slots[group_id]
    attempt_id = slot["attempt_id"]
    spec = _validate_command_spec(command_spec, group_id=group_id, attempt_id=attempt_id, bridge_context=bridge)
    _authorization(root, authorization_ref, authorization_sha256, scope="group", core={**core, "identity_ref": manifest["core_identity"]},
                   manifest=manifest,
                   manifest_path=manifest_path, manifest_sha256=manifest_sha256, bridge_context=bridge,
                   group_id=group_id, attempt_id=attempt_id, command_sha256=spec["command_spec_sha256"])
    parent = _ref(parent_admission_ref, "parent admission")
    _validate_parent_receipt(protocol, root, manifest_path, parent)
    process = _process(process_evidence)
    resources = _live_resources(root, core)
    raw_permit = _permit(root, permit_ref, scope="group", group_id=group_id,
                         attempt_id=attempt_id, command_sha256=spec["command_spec_sha256"])
    permit = _permit_value(raw_permit, manifest["core_identity"], manifest_path,
                           core["bifrost_admission_source"], core["bifrost_supervisor_source"],
                           "group", group_id, attempt_id)
    own_lock = contextlib.nullcontext(lock) if lock else exclusive_lock(root, core["lock_path"])
    with own_lock as held:
        _require_lock(held, root, core)
        parent_value, _ = _json_ref(root, parent, "parent admission")
        require(parent_value.get("manifest_sha256") == manifest_sha256,
                "parent admission is not bound to the finalized wrapper")
        predecessor_raw = _read(root, slot["predecessor_receipt_path"], "predecessor receipt")
        ledger_raw, _ = _read_jsonl(root, LEDGER_PATH)
        groups = core["dispatch_groups"]
        index = groups.index(group_id)
        if index == 0:
            expected_ledger = _bound(root, protocol.resume_prefix_ref(root, core),
                                     "resume107 prefix", rows=True)
            expected_label = "exact continuation prefix"
        else:
            previous = groups[index - 1]
            previous_slot = manifest["execution_admission_slots"][previous]
            expected_path = str(PurePosixPath(previous_slot["completion_path"]).parent / "ledger-after.jsonl")
            expected_ledger = _read(root, expected_path, "previous completion ledger witness")
            expected_label = f"previous completion witness for {previous}"
        require(ledger_raw == expected_ledger,
                f"live ledger differs from the {expected_label}")
        witness_path = str(PurePosixPath(slot["admission_path"]).parent / "ledger-before.jsonl")
        witness = _write_bytes_exclusive(root, witness_path, ledger_raw)
        value = {
            "schema": GROUP_SCHEMA, "status": "ready-to-execute", "automatic_retry": False,
            "group_id": group_id, "attempt_id": attempt_id, "phase": "execution",
            "core_identity": manifest["core_identity"], "manifest_path": manifest_path,
            "source_commit": core["source_commit"], "plan_commit": core["plan_commit"],
            "contract_sha256": core["contract"]["sha256"], "ledger_prefix": core["continuation_prefix"],
            "superseded_attempt_id": slot["predecessor_attempt_id"],
            "superseded_receipt_sha256": sha256(predecessor_raw), "ledger_before_sha256": witness["sha256"],
            "process_ownership": process,
            "lock": {"schema": "exclusive-lock/v1", "status": "held", "automatic_retry": False,
                     "path": core["lock_path"], "owner_pid": process["pid"],
                     "owner_birth": process["birth_identity"]},
            "fresh_namespace": {"schema": "fresh-sidecar-namespace/v1", "status": "fresh",
                                "automatic_retry": False, "path": core["sidecar_namespace"], "fresh": True, "sidecar_count": 0,
                                "created_by": process["pid"]},
            "admission_source": core["bifrost_admission_source"],
            "supervisor_source": core["bifrost_supervisor_source"],
            "helper": core["bifrost_admission_source"], "supervisor_permit": permit,
            "resource_policy": resources["resource_policy"],
            "resource_policy_sha256": resources["resource_policy_sha256"],
            "remaining_reserved_seconds": resources["remaining_reserved_seconds"],
        }
        result = _write_json_exclusive(root, slot["admission_path"], value)
        _validate_group_receipt(protocol, root, manifest_path, group_id,
                                {"path": slot["admission_path"],
                                 "sha256": result["sha256"]})
        return result


@_stage_entry
def write_phase_gate(root: Path | str, manifest_path: str, manifest_sha256: str,
                     group_id: str, group_admission_ref: Mapping[str, str],
                     process_evidence: Mapping[str, Any], permit_ref: Mapping[str, str],
                     command_spec: Mapping[str, Any], bridge_context: Mapping[str, Any], *,
                     fixture_only: bool = False, lock: _HeldLock | None = None) -> dict[str, str]:
    root = Path(root).resolve()
    _require_execution_permission(root, fixture_only=fixture_only)
    manifest, core, protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    bridge = _validate_bridge_context(root, core, bridge_context)
    slot = manifest["execution_admission_slots"].get(group_id)
    require(isinstance(slot, Mapping), "phase group is outside replacement order")
    spec = _validate_command_spec(command_spec, group_id=group_id, attempt_id=slot["attempt_id"], bridge_context=bridge)
    _process(process_evidence)
    _permit(root, permit_ref, scope="group", group_id=group_id, attempt_id=slot["attempt_id"],
            command_sha256=spec["command_spec_sha256"])
    _validate_group_receipt(protocol, root, manifest_path, group_id, group_admission_ref)
    resources = _live_resources(root, core)
    own_lock = contextlib.nullcontext(lock) if lock else exclusive_lock(root, core["lock_path"])
    with own_lock as held:
        _require_lock(held, root, core)
        value = {
            "schema": PHASE_SCHEMA, "manifest_path": manifest_path, "manifest_sha256": manifest_sha256,
            "core_identity": manifest["core_identity"], "admission_ref": dict(group_admission_ref),
            "group_id": group_id, "attempt_id": slot["attempt_id"], "phase": "execution",
            "source_commit": core["source_commit"], "plan_commit": core["plan_commit"],
            "contract_sha256": core["contract"]["sha256"],
            "remaining_seconds": resources["remaining_reserved_seconds"],
            "minimum_remaining_reserve_seconds": RESOURCE_POLICY["minimum_remaining_reserve_seconds"],
            "minimum_replacement_seconds": RESOURCE_POLICY["minimum_replacement_seconds"],
            "startup_seconds": RESOURCE_POLICY["startup_seconds"],
            "minimum_free_gib": RESOURCE_POLICY["minimum_free_gib"],
            "observed_free_bytes": resources["observed_free_bytes"],
            "resource_floor_checked": True, "no_foreign_processes": True,
            "exclusive_lock_checked": True, "lock_held": True,
            "fresh_sidecar_namespace": True, "source_snapshot_checked": True,
            "helper": core["bifrost_admission_source"], "supervisor": core["bifrost_supervisor_source"],
            "supervisor_permit": _permit_value(
                _permit(root, permit_ref, scope="group", group_id=group_id,
                        attempt_id=slot["attempt_id"], command_sha256=spec["command_spec_sha256"]),
                manifest["core_identity"], manifest_path,
                core["bifrost_admission_source"], core["bifrost_supervisor_source"],
                "group", group_id, slot["attempt_id"],
            ),
        }
        path = slot["phase_gate_path"]
        result = _write_json_exclusive(root, path, value)
        protocol.validate_phase_gate(root, manifest_path, group_id, path, dict(group_admission_ref))
        return result


@_stage_entry
def write_completion(root: Path | str, manifest_path: str, manifest_sha256: str,
                     group_id: str, group_admission_ref: Mapping[str, str],
                     phase_gate_ref: Mapping[str, str], completed_receipt_ref: Mapping[str, str],
                     ledger_before_ref: Mapping[str, str], ledger_after_ref: Mapping[str, str],
                     bridge_context: Mapping[str, Any], *, fixture_only: bool = False,
                     lock: _HeldLock | None = None,
                     continuation_safety: Mapping[str, Any] | None = None) -> dict[str, str]:
    root = Path(root).resolve()
    _require_execution_permission(root, fixture_only=fixture_only)
    manifest, core, protocol = _manifest_context(root, manifest_path, manifest_sha256, bridge_context)
    _validate_bridge_context(root, core, bridge_context)
    slot = manifest["execution_admission_slots"].get(group_id)
    require(isinstance(slot, Mapping), "completion group is outside replacement order")
    require(_ref(group_admission_ref, "completion group admission")["path"] == slot["admission_path"],
            "completion admission path is not the reviewed slot")
    require(_ref(phase_gate_ref, "completion phase gate")["path"] == slot["phase_gate_path"],
            "completion phase path is not the reviewed slot")
    require(_ref(completed_receipt_ref, "completed receipt")["path"] ==
            f"reports/releases/v0.9.2/attempts/{slot['attempt_id']}/completed.json",
            "completed receipt path is not the reviewed attempt")
    require(_ref(ledger_before_ref, "ledger before")["path"] ==
            str(PurePosixPath(slot["admission_path"]).parent / "ledger-before.jsonl"),
            "ledger-before path is not the admission witness")
    require(_ref(ledger_after_ref, "ledger after")["path"] ==
            str(PurePosixPath(slot["completion_path"]).parent / "ledger-after.jsonl"),
            "ledger-after path is not the completion witness")
    admission = _json(_bound(root, group_admission_ref, "group admission"), "group admission")
    phase = _json(_bound(root, phase_gate_ref, "phase gate"), "phase gate")
    completed = _json(_bound(root, completed_receipt_ref, "completed receipt"), "completed receipt")
    before_raw = _bound(root, ledger_before_ref, "ledger before")
    after_raw = _bound(root, ledger_after_ref, "ledger after")
    require(admission.get("group_id") == group_id and admission.get("attempt_id") == slot["attempt_id"],
            "completion admission identity differs")
    require(phase.get("group_id") == group_id and phase.get("attempt_id") == slot["attempt_id"],
            "completion phase identity differs")
    protocol._terminal_identity(
        completed, group_id=group_id, attempt_id=slot["attempt_id"],
        source_commit=core["source_commit"], plan_commit=core["plan_commit"],
        contract_sha256=core["contract"]["sha256"], execution_series=2,
        label="actual terminal frozen receipt")
    protocol.validate_continuation_safety(continuation_safety, completed, completed_receipt_ref["sha256"])
    before_rows = [json.loads(line) for line in before_raw.splitlines() if line.strip()]
    after_rows = [json.loads(line) for line in after_raw.splitlines() if line.strip()]
    require(after_rows[:-1] == before_rows and len(after_rows) == len(before_rows) + 1,
            "ledger transition is not exactly one appended row")
    row = after_rows[-1]
    require(row == completed, "terminal ledger row and full frozen receipt differ")
    own_lock = contextlib.nullcontext(lock) if lock else exclusive_lock(root, core["lock_path"])
    with own_lock as held:
        _require_lock(held, root, core)
        value = {
            "schema": COMPLETION_SCHEMA, "status": completed["status"], "automatic_retry": False,
            "continuation_safety": dict(continuation_safety),
            "manifest_path": manifest_path, "manifest_sha256": manifest_sha256,
            "core_identity": manifest["core_identity"], "group_id": group_id,
            "attempt_id": slot["attempt_id"], "admission_ref": dict(group_admission_ref),
            "admission_sha256": group_admission_ref["sha256"], "phase_gate_ref": dict(phase_gate_ref),
            "phase_gate_sha256": phase_gate_ref["sha256"],
            "completed_receipt_sha256": completed_receipt_ref["sha256"],
            "ledger_before_sha256": ledger_before_ref["sha256"],
            "ledger_after_sha256": ledger_after_ref["sha256"],
        }
        active = _ACTIVE_STAGE.get()
        if active is not None:
            predecessor, successor = active["predecessor"], active["stage"]
            require(isinstance(predecessor, (active["bridge"].ParentStage, active["bridge"].FinalizedParentStage)),
                    "completion requires actual predecessor parent stage")
            require(isinstance(successor, active["bridge"].SuccessorStageDraft),
                    "completion requires full post-terminal successor draft")
            require(successor.predecessor_identity_sha256 == predecessor.identity_sha256,
                    "completion predecessor differs from actual successor draft")
            finalized = active["bridge"].write_completion(
                root, predecessor=predecessor, successor=successor, graph=active["graph"],
                completion_path=slot["completion_path"], completion=value,
                expected_group_id=group_id, expected_attempt_id=slot["attempt_id"])
            result = {"path": slot["completion_path"],
                      "sha256": sha256(_read(root, slot["completion_path"], "actual finalized completion"))}
            protocol.validate_completion(root, manifest_path, group_id, slot["completion_path"],
                                         dict(group_admission_ref), dict(phase_gate_ref))
            return result, finalized
        result = _write_json_exclusive(root, slot["completion_path"], value)
        protocol.validate_completion(root, manifest_path, group_id, slot["completion_path"],
                                    dict(group_admission_ref), dict(phase_gate_ref))
        return result


@_stage_entry
def validate_runtime(root: Path | str, manifest_path: str, manifest_sha256: str,
                     bridge_context: Mapping[str, Any], parent_admission: object,
                     configuration: tuple[object, object]) -> dict[str, Any]:
    root = Path(root).resolve()
    static = validate_preparation(root, manifest_path, manifest_sha256, bridge_context)
    protocol = _load_protocol(root)
    require(callable(getattr(protocol, "validate_runtime", None)), "replacement-24 protocol lacks validate_runtime")
    return protocol.validate_runtime(root, manifest_path, parent_admission=parent_admission,
                                    configuration=configuration)


def main(argv: list[str] | None = None) -> int:
    # There is deliberately no admit/launch CLI.  Production entrypoints are
    # supervisor-owned and remain authorization-gated until the later review.
    del argv
    raise Admission23Error("replacement-24 admission CLI is disabled; use reviewed writer APIs")


if __name__ == "__main__":
    raise SystemExit(main())


# Stage-aware BF23 seam.  The legacy writer APIs above remain available for
# historical packet validation; these functions are the only APIs used by the
# BF23 staged controller.  A supplied stage/graph is reused, so validation
# cannot silently reload the bridge or accept a serialized context lookalike.
STAGE_BRIDGE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-19.py"
STAGE_SCHEMA = "v092-bifrost-v0140-replay-stage/v4"


def validate_parent_stage(root: Path | str, stage: Any, graph: Any, *, expected_index: int,
                          expected_ledger_sha256: str | None = None,
                          stage_bridge: Any | None = None) -> dict[str, Any]:
    require(stage is not None and graph is not None, "parent stage and graph are required")
    require(stage.__class__.__name__ in {"ParentStage", "FinalizedParentStage"},
            "parent admission requires an opaque parent stage")
    require(stage.graph is graph, "parent admission received a different graph instance")
    require(stage.identity.index == expected_index, "parent stage index differs")
    if expected_ledger_sha256 is not None:
        require(stage.identity.ledger_sha256 == expected_ledger_sha256, "parent ledger digest differs")
    bridge = getattr(graph, "assert_complete", None)
    require(callable(bridge), "parent graph lacks complete identity validation")
    bridge({member.name: member.module_object for member in graph.members})
    require(stage_bridge is not None and callable(getattr(stage_bridge, "assert_stage_current", None)),
            "same-stage admission requires the pinned bridge module instance")
    stage_bridge.assert_stage_current(Path(root).resolve(), stage, graph)
    return {"schema": STAGE_SCHEMA + "/parent-admission", "status": "stage-admitted",
            "stage_index": stage.identity.index, "stage_identity_sha256": stage.identity_sha256,
            "graph_sha256": graph.graph_sha256, "ledger_sha256": stage.identity.ledger_sha256}


def validate_child_stage(root: Path | str, child: Any, parent: Any, graph: Any,
                         *, now_monotonic: float, stage_bridge: Any | None = None) -> dict[str, Any]:
    require(child is not None and parent is not None and graph is not None, "child stage inputs are required")
    require(child.__class__.__name__ == "ChildStage", "child admission requires an opaque ChildStage")
    require(child.graph is graph and child.parent_identity_sha256 == parent.identity_sha256,
            "child stage identity is not bound to the ready parent")
    require(child.identity.lock == parent.identity.lock, "child does not retain parent lock identity")
    require(stage_bridge is not None and callable(getattr(stage_bridge, "assert_child_ready", None)),
            "same-stage child admission requires the pinned bridge module instance")
    remaining = stage_bridge.assert_child_ready(Path(root).resolve(), child, parent=parent, graph=graph,
                                                now_monotonic=now_monotonic)
    return {"schema": STAGE_SCHEMA + "/child-admission", "status": "child-stage-admitted",
            "parent_stage_identity_sha256": parent.identity_sha256,
            "child_stage_identity_sha256": child.identity_sha256,
            "child": child.child_identity, "startup_remaining_seconds": remaining}



def validate_child_stage_from_receipt(
        root: Path | str, child: Any, parent_receipt_ref: Mapping[str, Any], graph: Any,
        *, manifest_ref: Mapping[str, Any], core_identity: Mapping[str, Any],
        core: Mapping[str, Any], dispatch_sidecars: Mapping[str, Mapping[str, Any]],
        now_monotonic: float, stage_bridge: Any | None = None) -> dict[str, Any]:
    """Admit an actual child using receipt metadata through its exact pinned bridge.

    This process-boundary seam never reconstructs a parent runtime, reloads a
    module, or replays evidence. The bridge guard owns the exact current-ref,
    metadata-lineage, disjoint sidecar union and original-lease checks.
    """
    require(stage_bridge is not None and graph is not None and child is not None,
            "receipt child admission requires the pinned bridge, graph and opaque child")
    require(callable(getattr(graph, "assert_member", None)), "child graph lacks exact member identity")
    graph.assert_member("bridge19", stage_bridge)
    require(isinstance(child, stage_bridge.ChildStage) and child.graph is graph,
            "receipt child admission requires this bridge's opaque ChildStage and graph")
    guard = getattr(stage_bridge, "assert_child_ready_from_receipt", None)
    require(callable(guard), "pinned bridge lacks the child receipt readiness guard")
    parent_ref = _ref(parent_receipt_ref, "parent stage receipt")
    remaining = guard(Path(root).resolve(), child, parent_receipt_ref=parent_ref,
                      graph=graph, manifest_ref=manifest_ref, core_identity=core_identity,
                      core=core, dispatch_sidecars=dispatch_sidecars,
                      now_monotonic=now_monotonic)
    require(type(remaining) in (int, float) and 0 < remaining < float("inf"),
            "child receipt readiness guard returned an invalid remaining lease")
    return {"schema": STAGE_SCHEMA + "/child-admission", "status": "child-stage-admitted",
            "parent_stage_identity_sha256": child.parent_identity_sha256,
            "parent_receipt_ref": parent_ref, "parent_stage_index": child.identity.index,
            "child_stage_identity_sha256": child.identity_sha256,
            "child": child.child_identity, "startup_remaining_seconds": remaining}


def validate_stage_completion(root: Path | str, predecessor: Any, successor: Any, graph: Any,
                              *, stage_bridge: Any | None = None) -> None:
    require(successor.predecessor_identity_sha256 == predecessor.identity_sha256,
            "completion does not name the immediate predecessor stage")
    require(successor.graph is graph and predecessor.graph is graph,
            "completion stage graph instance changed")
    require(successor.identity.index == predecessor.identity.index + 1,
            "completion stage index is not the next state")
    validate_parent_stage(root, predecessor, graph, expected_index=predecessor.identity.index,
                          stage_bridge=stage_bridge)
    validate_parent_stage(root, successor, graph, expected_index=successor.identity.index,
                          expected_ledger_sha256=successor.identity.ledger_sha256,
                          stage_bridge=stage_bridge)
