#!/usr/bin/env python3
"""Reviewed v0.14.0 replacement-21 supervisor boundary.

This module is deliberately the only command factory for the replacement.  It
does not accept a callback, arbitrary executable, or caller-provided process
runner.  The command is a fixed child entry point which reloads the exact
frozen bridge and invokes the frozen executor's ``run_group`` API.  The child
inherits the supervisor's already-held lock descriptor; the executor's own
lock context is temporarily made a no-op only inside that child and is always
restored before exit.

Importing the module is side-effect free.  ``run_groups`` remains guarded by
the reviewed experiment marker and is not used by the preparation tests.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import re
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterator, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-21.py"
HELPER_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-21.py"
SUPERVISOR_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-21.py"
BRIDGE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-16.py"
MANIFEST_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-21/manifest.json"
CONTEXT_PATH = "reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-21/bridge-context.json"
LEDGER_PATH = "reports/releases/v0.9.2/ledger-v1.jsonl"
FROZEN_LOCK_PATH = "/private/tmp/dataflowbench-v0.9.0-exclusive-analyzer.lock"
RAW_PERMIT_SCHEMA = "v092-bifrost-v0140-raw-process-permit/v1"
PROCESS_SCHEMA = "invocation-process-ownership/v1"
COMMAND_SCHEMA = "v092-bifrost-v0140-frozen-command/v1"
FIXTURE_ENV = "DATAFLOWBENCH_V092_REPLACEMENT21_FIXTURE_SEAM"
EXPERIMENT_ENV = "DATAFLOWBENCH_V092_REPLACEMENT21_EXPERIMENT"
ORIGIN = "2026-10-20T00:57:00.680937+00:00"
HISTORICAL_TOTAL_WALL_SECONDS = 333360
PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS = 600
PER_ATTEMPT_STARTUP_ALLOWANCE_SOURCE = "bifrost-v0140-replacement-21.RESOURCE_POLICY.startup_seconds"
SHA_RE = __import__("re").compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = __import__("re").compile(r"[0-9a-f]{40}\Z")


class Supervisor21Error(ValueError):
    """A reviewed command, process, or frozen-runtime binding failed closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise Supervisor21Error(message)


class _HeldLockProxy:
    """The admission writer's narrow lock protocol over this supervisor lock."""

    def __init__(self, root: Path, stream: Any):
        self.root = root
        self.path = Path(stream.name).resolve()
        self.stream = stream
        self.closed = False
        self.identity = os.fstat(stream.fileno())

    def assert_live(self, expected: str) -> None:
        expected_path = _lock_target(self.root, expected)
        require(not self.closed and self.path == expected_path.resolve(),
                "supervisor lock proxy is not the canonical lock")
        current = os.fstat(self.stream.fileno())
        target = expected_path.stat()
        require((current.st_dev, current.st_ino) == (self.identity.st_dev, self.identity.st_ino) ==
                (target.st_dev, target.st_ino), "canonical held lock inode changed")


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
                _temporary_fixture(root),
                "production lock must be the frozen executor's canonical absolute path")
        require(not target.is_symlink(), "lock path is a symlink")
        return target
    return _path(root, value, "lock path")


def _temporary_fixture(root: Path) -> bool:
    if os.environ.get(FIXTURE_ENV) != "1" or root.resolve() == ROOT.resolve():
        return False
    try:
        root.resolve().relative_to(Path(tempfile.gettempdir()).resolve())
    except ValueError:
        return False
    return True


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
        raise Supervisor21Error(f"{label} is not valid JSON") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_module(root: Path, relative: str, name: str) -> Any:
    path = _path(root, relative, f"{name} source")
    before = sha256(path.read_bytes())
    spec = importlib.util.spec_from_file_location(f"v092_replacement21_supervisor_{name}", path)
    require(spec is not None and spec.loader is not None, f"cannot load {name} source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(sha256(path.read_bytes()) == before, f"{name} source changed during import")
    return module


def _load_protocol(root: Path) -> Any:
    return _load_module(root, PROTOCOL_PATH, "replacement-21 protocol")


def _static(root: Path, manifest_path: str, manifest_sha256: str) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    protocol = _load_protocol(root)
    static = protocol.validate_static(root, manifest_path)
    require(static.get("manifest_ref", {}).get("sha256") == manifest_sha256,
            "manifest digest differs from the reviewed static identity")
    return protocol, dict(static["manifest"]), dict(static["core"])


def _load_admission(root: Path, core: Mapping[str, Any]) -> Any:
    ref = _ref(core.get("bifrost_admission_source"), "admission source")
    require(ref["path"] == HELPER_PATH, "admission source path is not canonical v21")
    _bound(root, ref, "admission source")
    return _load_module(root, HELPER_PATH, "admission-21")


def _load_bridge(root: Path, core: Mapping[str, Any]) -> Any:
    ref = _ref(core.get("frozen_bridge_source"), "frozen bridge source")
    require(ref["path"] == BRIDGE_PATH, "frozen bridge path is not canonical v13")
    _bound(root, ref, "frozen bridge source")
    return _load_module(root, BRIDGE_PATH, "frozen bridge")


def _actual_runtime_context(root: Path, core: Mapping[str, Any], bridge: Any, *,
                            expected_context_digest: str | None = None,
                            mode: str = "before", stage: Any | None = None) -> dict[str, Any]:
    """Load bridge-owned runtime objects after scoped frozen validation.

    ``load_and_validate`` intentionally returns a JSON-safe diagnostic
    context.  It is not a substitute for the in-process ``Path``- and
    module-bearing objects used by the executor/checker/configuration code.
    The bridge therefore exposes this separate, lossless API.  Requiring its
    schema and object marker prevents a caller from feeding serialized
    context dictionaries back into the runtime as if they were validation
    results.
    """
    root = Path(root).resolve()
    loader = getattr(bridge, "load_runtime_context", None)
    require(callable(loader), "frozen bridge lacks the lossless runtime-context API")
    if stage is None:
        value = loader(root, core, mode=mode)
    else:
        bridge.assert_stage_current(root, stage, stage.graph)
        retained = bridge.runtime_objects(stage)
        require(retained is stage.runtime, "stage runtime identity differs")
        value = retained.objects
    require(isinstance(value, Mapping), "frozen bridge runtime context is not an object")
    require(value.get("schema") == "v092-bifrost-v0140-runtime-context/v1" and
            value.get("lossless_runtime_objects") is True,
            "frozen bridge runtime context is not the reviewed lossless result")
    modules = value.get("modules")
    require(isinstance(modules, Mapping) and
            {"replacement05", "executor", "checker", "configuration"} <= set(modules),
            "frozen bridge runtime module roster is incomplete")
    for name in ("replacement05", "executor", "checker", "configuration"):
        require(modules[name] is not None, f"frozen bridge runtime module {name} is missing")
    validated = value.get("validated")
    require(isinstance(validated, Mapping) and isinstance(validated.get("plan"), Mapping),
            "frozen bridge runtime result lacks the normalized plan")
    contract = _ref(core.get("contract"), "canonical contract")
    contract_path = _path(root, contract["path"], "canonical contract")
    require(validated.get("bytes_sha256") == contract["sha256"] and
            str(Path(str(validated.get("path"))).resolve()) == str(contract_path.resolve()) and
            Path(str(validated.get("repo_root"))).resolve() == root,
            "lossless frozen runtime result escaped the canonical contract root")
    mixed_context = value.get("mixed_context")
    require(isinstance(mixed_context, Mapping),
            "frozen bridge runtime result lacks the lossless mixed context")
    require(isinstance(mixed_context.get("root"), Path) and
            mixed_context["root"].resolve() == root and
            mixed_context.get("executor") is modules["executor"] and
            mixed_context.get("checker") is modules["checker"] and
            mixed_context.get("configuration") is modules["configuration"] and
            mixed_context.get("validated") is validated,
            "frozen bridge mixed context is not the same in-process runtime")
    require(isinstance(mixed_context.get("rows"), list) and
            isinstance(mixed_context.get("prefix"), list) and
            isinstance(mixed_context.get("contexts"), Mapping),
            "frozen bridge mixed context is incomplete")
    context = value.get("bridge_context")
    require(isinstance(context, Mapping) and
            isinstance(context.get("context_digest"), str) and
            SHA_RE.fullmatch(context["context_digest"]),
            "frozen bridge runtime result lacks its live context digest")
    if expected_context_digest is not None:
        require(context["context_digest"] == expected_context_digest,
                "lossless frozen runtime context differs from the reviewed command context")
    checker_summary = value.get("checker_summary")
    configuration_summary = value.get("configuration_summary")
    require(isinstance(checker_summary, Mapping) and
            checker_summary.get("status") in {"fresh-evidence-verified", "partial-evidence-verified"},
            "frozen bridge runtime result lacks the actual mixed checker summary")
    require(isinstance(configuration_summary, Mapping) and
            configuration_summary.get("status") in {
                "configuration-pending-complete-matrix", "canonical-validation-passed"
            },
            "frozen bridge runtime result lacks the reviewed configuration summary")
    return {"modules": dict(modules), "validated": validated, "mixed_context": mixed_context,
            "bridge_context": dict(context),
            "checker_summary": dict(checker_summary),
            "configuration_summary": dict(configuration_summary)}


def _validate_context(root: Path, core: Mapping[str, Any], value: object, *,
                      admission: Any | None = None, stage: Any | None = None,
                      bridge: Any | None = None) -> dict[str, Any]:
    if stage is not None:
        require(bridge is not None, "opaque context requires pinned bridge")
        bridge.assert_stage_current(root, stage, stage.graph)
        retained = bridge.runtime_objects(stage).objects
        require(retained["bridge_context"] is value, "context is not retained stage output")
        context = value
    else:
        admission = _load_admission(root, core) if admission is None else admission
        context = admission._validate_bridge_context(root, core, value)
    require(context.get("execution_authorized") is False,
            "the preparation bridge cannot itself authorize execution")
    plan = context.get("validated_full_normalized_plan", {}).get("plan")
    require(isinstance(plan, Mapping), "bridge context lacks the complete normalized plan")
    # The plan's own reviewed eligibility is distinct from the bridge's
    # preparation-only status.  A later authorization may permit a command
    # only when the exact plan says execution is eligible.
    require(plan.get("execution_authorized") is True,
            "normalized plan is not execution-authorized")
    return context


def _birth(pid: int) -> str:
    require(type(pid) is int and pid > 0, "PID is malformed")
    try:
        value = subprocess.check_output(["ps", "-p", str(pid), "-o", "lstart="],
                                        text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Supervisor21Error("cannot obtain process birth identity") from exc
    require(value, "process birth identity is empty")
    return value


def _process(pid: int) -> dict[str, Any]:
    birth = _birth(pid)
    try:
        os.kill(pid, 0)
    except OSError as exc:
        raise Supervisor21Error("process is not live") from exc
    return {"schema": PROCESS_SCHEMA, "status": "verified", "automatic_retry": False,
            "pid": pid, "birth_identity": birth, "no_foreign_processes": True,
            "tracked_processes": [{"pid": pid, "start_identity": birth}]}


def _attempt_id(group_id: str) -> str:
    require(isinstance(group_id, str) and group_id.startswith("bifrost-"), "group is not a Bifrost group")
    number = 3 if group_id == "bifrost-c-kernel" else 2
    return f"{group_id}-attempt-{number:02d}-series-02"


def _context_file(root: Path, value: str, expected_digest: str,
                  *, allowed_paths: tuple[str, ...] = (CONTEXT_PATH,)) -> dict[str, Any]:
    require(value in allowed_paths, "bridge context path is not a reviewed immutable context")
    raw = _read(root, value, "bridge context")
    context = _json(raw, "bridge context")
    require(context.get("context_digest") == expected_digest, "bridge context digest differs from command")
    unsigned = dict(context)
    unsigned.pop("context_digest", None)
    require(sha256(canonical_json(unsigned)) == expected_digest, "bridge context bytes are not self-bound")
    return context


def _group_context_path(manifest: Mapping[str, Any], group_id: str) -> str:
    """Return the fresh immutable context sibling for one ordered slot."""
    slot = manifest.get("execution_admission_slots", {}).get(group_id)
    require(isinstance(slot, Mapping), "group context has no reviewed execution slot")
    admission_path = _relative(slot.get("admission_path"), "group admission path")
    return str(admission_path.parent / "bridge-context.json")


def _write_context(protocol: Any, root: Path, path: str, context: Mapping[str, Any]) -> dict[str, str]:
    """Create one immutable per-group bridge context and verify its digest."""
    value = dict(context)
    digest = value.get("context_digest")
    require(isinstance(digest, str) and SHA_RE.fullmatch(digest),
            "fresh bridge context has no valid digest")
    unsigned = dict(value)
    unsigned.pop("context_digest", None)
    require(sha256(canonical_json(unsigned)) == digest,
            "fresh bridge context digest is not self-bound")
    result = protocol.write_immutable(root, path, value)
    require(result["sha256"] == sha256(canonical_json(value)),
            "fresh bridge context writer returned a different digest")
    return result


def _environment(group: Mapping[str, Any], group_id: str) -> dict[str, str]:
    raw = group.get("environment")
    require(isinstance(raw, Mapping) and raw.get("PATH"), "group environment lacks explicit PATH")
    result = dict(raw)
    require(all(isinstance(key, str) and isinstance(value, str) for key, value in result.items()),
            "group environment must contain strings")
    for key in result:
        require(not any(token in key.upper() for token in ("SECRET", "TOKEN", "PASSWORD", "CREDENTIAL")),
                "secret-bearing environment key is not permitted")
    result.update({EXPERIMENT_ENV: "1", "DATAFLOWBENCH_V092_GROUP_ID": group_id})
    return result


def _child_interpreter() -> str:
    """Use this runtime's actual executable, preserving the sealed OS argv.

    macOS framework launchers can replace ``sys.executable`` before Python
    starts. The interpreter in ``orig_argv`` is the executable that already
    passed that launcher, so invoking it directly preserves the exact permit.
    """
    require(isinstance(sys.orig_argv, list) and sys.orig_argv,
            "runtime lacks its original interpreter invocation")
    interpreter = Path(sys.orig_argv[0])
    require(interpreter.is_absolute() and interpreter.is_file() and
            os.access(interpreter, os.X_OK), "actual interpreter is not executable")
    return str(interpreter)


def build_group_command(root: Path | str, manifest_path: str, manifest_sha256: str,
                        bridge_context: Mapping[str, Any], group_id: str, *,
                        fixture_only: bool = False,
                        context_path: str = CONTEXT_PATH,
                        lock_fd: int = 3, stage: Any | None = None,
                        bridge: Any | None = None, admission: Any | None = None,
                        protocol: Any | None = None, manifest: Any | None = None,
                        core: Any | None = None, parent_stage_ref: Any | None = None,
                        popen_monotonic: float | None = None) -> dict[str, Any]:
    """Build the one reviewed child command and its exact command identity."""
    root = Path(root).resolve()
    if fixture_only:
        require(_temporary_fixture(root),
                "fixture command construction requires a temporary test root")
    else:
        require(os.environ.get(EXPERIMENT_ENV) == "1",
                "production command construction requires the reviewed experiment marker")
    require(manifest_path == MANIFEST_PATH, "only the canonical replacement-21 manifest is accepted")
    if stage is None:
        protocol, manifest, core = _static(root, manifest_path, manifest_sha256)
        admission = _load_admission(root, core)
    else:
        require(all(x is not None for x in (bridge, admission, protocol, manifest, core, parent_stage_ref, popen_monotonic)),
                "stage command bindings are incomplete")
    if not fixture_only:
        prepared = admission.validate_preparation(root, manifest_path, manifest_sha256, bridge_context,
                    stage=stage, pinned_bridge=bridge, graph=stage.graph)
        require(prepared.get("bridge_context") == dict(bridge_context),
                "actual frozen bridge output differs from command context")
    context = _validate_context(root, core, bridge_context, admission=admission, stage=stage, bridge=bridge)
    groups = context["validated_full_normalized_plan"]["plan"]["groups"]
    group = next((item for item in groups if isinstance(item, Mapping) and item.get("id") == group_id), None)
    require(isinstance(group, Mapping), "group is not present in the complete normalized plan")
    slot = manifest["execution_admission_slots"].get(group_id)
    require(isinstance(slot, Mapping), "group is not present in the reviewed slot map")
    attempt_id = slot["attempt_id"]
    require(attempt_id == _attempt_id(group_id), "slot attempt is not the reviewed series-02 identity")
    expected_context_path = _group_context_path(manifest, group_id)
    if not fixture_only:
        require(context_path == expected_context_path,
                "production group command must use its fresh immutable context path")
    _relative(context_path, "bridge context path")
    if not fixture_only and stage is None:
        _context_file(root, context_path, context["context_digest"],
                      allowed_paths=(expected_context_path,))
    argv = [_child_interpreter(), "-E", str(_path(root, SUPERVISOR_PATH, "supervisor source")),
            "--child", "--root", str(root), "--manifest", manifest_path,
            "--manifest-sha256", manifest_sha256,
            "--group", group_id, "--attempt-id", attempt_id,
            "--bridge-context", context_path, "--context-sha256", context["context_digest"],
            "--lock-fd", str(lock_fd)]
    if stage is not None:
        argv.extend(["--parent-stage", parent_stage_ref["path"], "--parent-stage-sha256",
                     parent_stage_ref["sha256"], "--popen-monotonic", repr(popen_monotonic)])
    environment = _environment(group, group_id)
    spec: dict[str, Any] = {
        "schema": COMMAND_SCHEMA, "group_id": group_id, "attempt_id": attempt_id,
        "argv": argv, "argv_sha256": sha256(canonical_json(argv)),
        "context_digest": context["context_digest"],
        "canonical_contract": context["canonical_contract_path_and_contract_sha256"],
        "source_commit": context["source_commit"], "plan_commit": context["plan_commit"],
        "environment": environment,
    }
    if stage is not None:
        spec.update(stage_identity_sha256=stage.identity_sha256,
                    parent_stage_identity_sha256=stage.identity_sha256, graph_sha256=stage.graph.graph_sha256)
    spec["command_spec_sha256"] = sha256(canonical_json(spec))
    return spec


def raw_permit(pid: int, command_spec: Mapping[str, Any], *, scope: str = "group",
               group_id: str | None = None, attempt_id: str | None = None,
               stage: Any | None = None) -> dict[str, Any]:
    """Create a process permit from the live child, never from caller claims."""
    require(scope in {"parent", "group", "configuration"}, "permit scope is unsupported")
    require(scope == "group" and group_id and attempt_id or scope in {"parent", "configuration"},
            "permit scope identity is incomplete")
    argv = command_spec.get("argv")
    digest = command_spec.get("command_spec_sha256")
    require(isinstance(argv, list), "permit command identity is incomplete")
    if scope == "group":
        require(isinstance(digest, str) and SHA_RE.fullmatch(digest),
                "group permit command identity is incomplete")
    else:
        require(digest is None, "parent permit unexpectedly carries group command identity")
    birth = _birth(pid)
    token = secrets.token_hex(32)
    value: dict[str, Any] = {
        "schema": RAW_PERMIT_SCHEMA, "scope": scope, "automatic_retry": False,
        "pid": pid, "birth": birth, "token": token,
        "argv_sha256": sha256(canonical_json(argv)),
        "command_spec_sha256": digest,
        "permit_id": "pending",
    }
    if scope == "group":
        value.update({"group_id": group_id, "attempt_id": attempt_id})
    if stage is not None:
        value.update(stage_identity_sha256=stage.identity_sha256,
                     graph_sha256=stage.graph.graph_sha256)
        if scope == "group":
            value["parent_stage_identity_sha256"] = stage.identity_sha256
    unsigned = dict(value)
    unsigned["permit_id"] = None
    value["permit_id"] = sha256(canonical_json(unsigned))
    return value


def _registered_group_timeout(validated: Mapping[str, Any], group_id: str) -> int:
    matches = [g for g in validated["plan"]["groups"] if g.get("id") == group_id]
    require(len(matches) == 1 and type(matches[0].get("deadline_seconds")) is int and matches[0]["deadline_seconds"] > 0,
            "dispatch lease lacks exact per-attempt timeout")
    return matches[0]["deadline_seconds"]


def _wait_group_child(child: Any, validated: Mapping[str, Any], group_id: str, *,
                      popen_monotonic: float) -> int:
    """Wait for the same finite lease granted to the frozen child runtime.

    The analyzer retains its registered timeout; the supervisor additionally
    permits the inherited startup allowance.  A nonzero exit is terminal and
    this helper never dispatches or retries another process.
    """
    elapsed = time.monotonic() - popen_monotonic
    require(elapsed >= 0, "child lease clock moved backwards")
    timeout = _registered_group_timeout(validated, group_id) + PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS - elapsed
    require(timeout > 0, "child dispatch lease expired before wait")
    code = child.wait(timeout=float(timeout))
    require(type(code) is int, "child exit status is unavailable")
    return code


@contextlib.contextmanager
def _per_source_projection_guard(executor: Any, runtime: Mapping[str, Any]) -> Iterator[None]:
    """Preserve the original12GiB per-snapshot bound under aggregate30GiB.

    Frozen run_group still discovers every historical working path and charges
    the complete projected remaining matrix.  Only the aggregate ceiling in
    the exact committed plan changes.  This hook rejects an oversized source
    at frozen preflight before attempt.mkdir, and rechecks the exact frozen
    projected count before actual extraction.
    """
    original = getattr(executor, "_materialize_source", None)
    require(callable(original), "frozen source projection boundary is unavailable")
    def scoped(*args, **kwargs):
        require(len(args) >= 3 and args[0] == runtime["repo_root"] and
                args[1] == runtime["plan"]["source_commit"] and kwargs.get("disk_guard") is not None,
                "source projection guard received another execution context")
        if kwargs.get("preflight_only") is True:
            projected = original(*args, **kwargs)
            require(type(projected) is int and 0 <= projected <= 12*1024**3,
                    "per-source projection exceeds retained12GiB ceiling")
            return projected
        projected = kwargs.get("expected_projected_bytes")
        require(type(projected) is int and 0 <= projected <= 12*1024**3,
                "source extraction lacks a bounded original12GiB projection")
        return original(*args, **kwargs)
    executor._materialize_source = scoped
    try:
        yield
    finally:
        executor._materialize_source = original


def _dispatch_lease(validated: Mapping[str, Any], group_id: str, *,
                    popen_monotonic: float, now_seconds: float | None = None,
                    now_monotonic: float | None = None) -> dict[str, Any]:
    """Bound only this invocation; this lease is not a user execution-window expiry."""
    import copy
    require(validated["plan"].get("resource_guards") == {"stop_free_gib": 48, "working_set_gib": 30},
            "runtime must inherit exact aggregate30GiB/stop48GiB guard")
    now = time.time() if now_seconds is None else now_seconds
    elapsed = now - dt.datetime.fromisoformat(ORIGIN).timestamp()
    require(elapsed >= 0, "dispatch timestamp precedes original origin")
    deadline_seconds = _registered_group_timeout(validated, group_id)
    clock = time.monotonic() if now_monotonic is None else now_monotonic
    setup_elapsed = clock - popen_monotonic
    require(setup_elapsed >= 0, "dispatch lease clock moved backwards")
    lease_seconds = deadline_seconds + PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS - setup_elapsed
    require(lease_seconds > 0, "dispatch lease expired during child setup")
    runtime = dict(validated)
    runtime["plan"] = copy.deepcopy(validated["plan"])
    runtime["total_wall_budget_seconds"] = elapsed + lease_seconds
    runtime["plan"]["total_wall_budget_seconds"] = elapsed + lease_seconds
    runtime["execution_window_runtime"] = {"mode": "no-user-imposed-expiry",
        "actual_elapsed_wall_seconds": elapsed, "per_attempt_lease_seconds": lease_seconds,
        "group_id": group_id, "deadline_seconds": deadline_seconds,
        "startup_allowance_seconds": PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS,
        "popen_monotonic": popen_monotonic, "setup_elapsed_seconds": setup_elapsed,
        "startup_allowance_source": PER_ATTEMPT_STARTUP_ALLOWANCE_SOURCE}
    runtime["plan"]["resource_reservation"]["expires_at_unix_seconds"] = now + lease_seconds
    return runtime


@contextlib.contextmanager
def _scoped_fresh_attempt(executor: Any, group_id: str) -> Iterator[None]:
    """Bind frozen ``run_group`` to the reviewed global attempt number.

    The frozen runner counts every historical row when enforcing its generic
    maximum-attempt cap.  Replacement-09 explicitly permits the C group to
    continue at global attempt 03 in series 02, while every other group uses
    global attempt 02.  The adapter delegates all freshness, terminal-state,
    collision, report-path, and ledger checks to the frozen function and only
    supplies the reviewed C cap of three for that one identity.
    """
    original = getattr(executor, "_assert_fresh", None)
    require(callable(original), "frozen executor freshness guard is unavailable")

    def scoped(repo_root: Path, group: Mapping[str, Any], reports: Any, series: int):
        if group.get("id") != "bifrost-c-kernel":
            result = original(repo_root, group, reports, series)
        else:
            reviewed = dict(group)
            # Bridge07 restores the actual reviewed C03 cap after the
            # legacy parser projection. Never accept C02 or C04 here.
            require(type(group.get("maximum_attempts")) is int and
                    group["maximum_attempts"] == 3,
                    "C freshness adapter requires the reviewed maximum_attempts=3")
            reviewed["maximum_attempts"] = 3
            result = original(repo_root, reviewed, reports, series)
        expected = _attempt_id(group_id)
        require(result[-1] == expected,
                "frozen freshness guard selected an attempt outside the reviewed global identity")
        return result

    executor._assert_fresh = scoped
    try:
        yield
    finally:
        executor._assert_fresh = original


@contextlib.contextmanager
def _scoped_contract_snapshot(executor: Any, runtime: Mapping[str, Any],
                              expected_plan_commit: str) -> Iterator[None]:
    """Keep the frozen contract check bound to this exact runtime object.

    The bridge validates the contract before the child waits for its admission
    sidecars.  The frozen executor checks the committed HEAD again inside
    ``run_group``; retain that check, but make its result an exact binding to
    the reviewed plan commit and to the in-process runtime object that the
    bridge returned.  A changed HEAD or a reconstructed/serialized runtime
    therefore fails before the executor can create an attempt.  The original
    module hook is restored even when the frozen call raises.
    """
    original = getattr(executor, "_assert_contract_snapshot", None)
    require(callable(original), "frozen executor contract snapshot guard is unavailable")
    require(isinstance(expected_plan_commit, str) and COMMIT_RE.fullmatch(expected_plan_commit),
            "reviewed plan commit is malformed")

    def scoped(candidate: Mapping[str, Any]) -> str:
        require(candidate is runtime,
                "frozen executor received a runtime object outside the reviewed bridge result")
        current = original(candidate)
        require(current == expected_plan_commit,
                "frozen executor contract snapshot resolved to an unexpected HEAD")
        return current

    executor._assert_contract_snapshot = scoped
    try:
        yield
    finally:
        executor._assert_contract_snapshot = original


def _write_raw_permit(root: Path, relative: str, value: Mapping[str, Any], *,
                      protocol: Any | None = None) -> dict[str, str]:
    protocol = _load_protocol(root) if protocol is None else protocol
    writer = getattr(protocol, "write_immutable", None)
    require(callable(writer), "protocol immutable writer is unavailable")
    return writer(root, relative, dict(value))


def _file_ref(root: Path, relative: str, label: str) -> dict[str, str]:
    """Read one CLI-supplied immutable file and derive its exact ref."""
    _relative(relative, label)
    raw = _read(root, relative, label)
    return {"path": relative, "sha256": sha256(raw)}


def _jsonl(root: Path, relative: str) -> tuple[bytes, list[dict[str, Any]]]:
    raw = _read(root, relative, "ledger")
    require(raw.endswith(b"\n"), "ledger is not newline terminated")
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines():
        value = _json(line, "ledger row")
        rows.append(value)
    require(rows, "ledger is empty")
    return raw, rows


def _stable_bridge_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    root_identity = value.get("validation_root_path_and_git_tree_identity")
    contract = value.get("canonical_contract_path_and_contract_sha256")
    require(isinstance(root_identity, Mapping) and isinstance(contract, Mapping),
            "bridge context lacks stable root/contract identity")
    return {
        "root": root_identity.get("path"),
        "source_commit": value.get("source_commit"),
        "plan_commit": value.get("plan_commit"),
        "contract": dict(contract),
        "ledger_sha256": value.get("ledger_sha256"),
    }


def _mixed_runtime_context(root: Path, manifest: Mapping[str, Any], core: Mapping[str, Any],
                           manifest_sha256: str, bridge_context: Mapping[str, Any],
                           bridge: Any, *, mode: str = "before") -> tuple[dict[str, Any], Any]:
    """Use the bridge's lossless mixed context for the requested checker mode."""
    runtime_objects = _actual_runtime_context(
        root, core, bridge,
        expected_context_digest=(str(bridge_context.get("context_digest")) if mode == "before" else None),
        mode=mode)
    modules = runtime_objects["modules"]
    replacement = modules["replacement05"]
    executor = modules["executor"]
    contract = _ref(core["contract"], "canonical contract")
    if mode == "after":
        require(_stable_bridge_identity(bridge_context) ==
                _stable_bridge_identity(runtime_objects["bridge_context"]),
                "after-mode bridge context changed stable root/source/plan/contract/ledger identity")
    # ``validated`` and every module come from the bridge's scoped C4 resource
    # boundary; calling the raw frozen validator here would reject the
    # reviewed replacement clock/resource overlay.
    validated = runtime_objects["validated"]
    require(validated.get("bytes_sha256") == contract["sha256"], "mixed context contract digest differs")
    runtime = dict(runtime_objects["mixed_context"])
    runtime["checker_summary"] = runtime_objects["checker_summary"]
    runtime["configuration_summary"] = runtime_objects["configuration_summary"]
    require(runtime.get("root").resolve() == root and
            runtime.get("contract_sha256") == contract["sha256"] and
            runtime.get("source_delta") is not None,
            "bridge mixed context is not bound to the reviewed replacement")
    require(runtime.get("source_commit") == core["source_commit"] and
            runtime.get("plan_commit") == core["plan_commit"],
            "bridge mixed context source/plan identity differs")
    contexts = runtime.get("contexts")
    prefix = runtime.get("prefix")
    prefix_raw = runtime.get("prefix_raw")
    rows = runtime.get("rows")
    require(isinstance(contexts, Mapping) and contexts and isinstance(prefix, list) and
            isinstance(prefix_raw, bytes) and isinstance(rows, list),
            "bridge did not return a complete lossless mixed context")
    require(bytes(prefix_raw) == b"".join(canonical_json(item) for item in prefix),
            "bridge mixed prefix bytes are not lossless")
    require(bytes(prefix_raw) == _bound(root, core["continuation_prefix"],
                                         "continuation prefix", rows=True),
            "bridge mixed context prefix differs from the registered continuation")
    replacement._check_rows_context(rows, contexts, contract["sha256"], core["source_commit"],
                                     core["plan_commit"], len(prefix))
    return runtime, modules


def _configuration_summary(runtime: dict[str, Any], replacement: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Run the actual mixed-context checker replay and bind its stable result.

    ``replacement._replay`` is the reviewed adapter around the frozen
    checker/executor instances loaded by the bridge.  It intentionally returns
    the checker scalars and report rows, while the older ``verify`` wrapper is
    not used because it owns the superseded admission schema.  Add the same
    selected-attempt projection that the frozen wrapper would attach so the
    later per-context configuration pass cannot silently invent a roster.
    """
    selected = replacement._selected_for_projection(runtime, runtime["rows"])
    # The frozen bridge already ran the actual replacement-05 replay and the
    # separate configuration module's execute=False checker path.  Consume
    # those in-process results rather than invoking a second, unbound checker
    # instance here.
    summary = runtime.get("checker_summary")
    require(isinstance(summary, Mapping), "bridge runtime checker summary is missing")
    require(isinstance(summary, Mapping) and
            summary.get("status") == "fresh-evidence-verified" and
            summary.get("selected_groups") == 84 and summary.get("partitions") == 92 and
            summary.get("rows") == 4252 and summary.get("known_stale") == 0,
            "mixed-context replay did not produce the registered 84/92/4252/0 result")
    selected_attempts = [
        {"group_id": row["group_id"], "attempt_id": row["attempt_id"],
         "contract_sha256": row["contract_sha256"],
         "source_commit": row["source_commit"], "plan_commit": row["plan_commit"]}
        for row in selected.values()
    ]
    checker_summary = {
        "schema": "v092-bifrost-v0140-checker-summary/v1",
        "status": summary["status"], "automatic_retry": False,
        "ledger_rows": summary["ledger_rows"],
        "selected_groups": summary["selected_groups"],
        "partitions": summary["partitions"], "rows": summary["rows"],
        "known_stale": summary["known_stale"],
        "selected_attempts": selected_attempts,
    }
    return {**dict(summary), "selected_attempts": selected_attempts,
            "checker_summary": checker_summary}, selected


def _expanded_runner_environment(core: Mapping[str, Any], checkout: Path) -> dict[str, str]:
    """Expand only the reviewed checkout placeholders in the runner env."""
    raw = core.get("runner_environment")
    require(isinstance(raw, Mapping) and raw, "reviewed runner environment is missing")
    substitutions = {
        "{checkout}": str(checkout), "${CHECKOUT}": str(checkout),
        "<checkout>": str(checkout),
    }
    result: dict[str, str] = {}
    for key, value in raw.items():
        require(isinstance(key, str) and isinstance(value, str),
                "reviewed runner environment must contain strings")
        expanded = value
        for marker, replacement in substitutions.items():
            expanded = expanded.replace(marker, replacement)
        result[key] = expanded
    require(result.get("HOME") == str(checkout) and result.get("TMPDIR") == str(checkout),
            "runner HOME/TMPDIR are not expanded to the isolated checkout")
    return result


def _configuration_live_gate(admission: Any, executor: Any, root: Path, core: Mapping[str, Any],
                             lock: _HeldLockProxy, validated: Mapping[str, Any],
                             source_commit: str, phase: str) -> dict[str, Any]:
    """Recheck live resource, process, lock, and source gates at each boundary."""
    lock.assert_live(str(_lock_target(root, core["lock_path"])))
    resources = admission._live_resources(root, core)
    checker = getattr(executor, "_check_resources", None)
    process_table = getattr(executor, "_process_table", None)
    contenders = getattr(executor, "_contenders", None)
    source_guard = getattr(executor, "_assert_source_snapshot", None)
    require(callable(checker) and callable(process_table) and callable(contenders) and
            callable(source_guard), "frozen live configuration gates are unavailable")
    minimum_free = resources["resource_policy"]["minimum_free_gib"] * 1024 ** 3
    checker(root, minimum_free)
    table = process_table()
    require(not contenders(table), "live configuration gate found a foreign analyzer contender")
    source_inputs = validated.get("source_inputs")
    runner_sha = validated.get("plan", {}).get("runner_source_sha256")
    require(isinstance(source_inputs, list) and isinstance(runner_sha, str),
            "configuration source snapshot binding is incomplete")
    source_guard(root, source_commit, runner_sha, source_inputs)
    return {
        "schema": "v092-bifrost-v0140-configuration-phase-gate/v1",
        "status": "live-gates-passed", "automatic_retry": False, "phase": phase,
        "lock_path": str(_lock_target(root, core["lock_path"])), "lock_held": True,
        "resource_floor_checked": True, "observed_free_bytes": resources["observed_free_bytes"],
        "remaining_reserved_seconds": resources["remaining_reserved_seconds"],
        "resource_policy": resources["resource_policy"],
        "resource_policy_sha256": resources["resource_policy_sha256"],
        "no_foreign_processes": True, "source_snapshot_checked": True,
        "source_commit": source_commit,
    }


@contextlib.contextmanager
def _lock_fd(path: Path) -> Iterator[Any]:
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Supervisor21Error("canonical supervisor lock is already held") from exc
        yield stream
    finally:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()


def _run_frozen_group(root: Path, manifest_path: str, manifest_sha256: str,
                      group_id: str, attempt_id: str, context_path: str,
                      context_digest: str, lock_fd: int, *, parent_stage_ref: Mapping[str, str],
                      popen_monotonic: float) -> dict[str, Any]:
    """Child-only bridge to the frozen executor, with every patch restored."""
    require(os.environ.get(EXPERIMENT_ENV) == "1", "child execution marker is missing")
    import fcntl
    try:
        os.fstat(lock_fd)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        raise Supervisor21Error("child did not inherit the supervisor's canonical lock") from exc
    protocol, manifest, core = _static(root, manifest_path, manifest_sha256)
    admission = _load_admission(root, core)
    bridge = _load_bridge(root, core)
    graph = bridge.prepare_graph(root, bridge._core_graph_inputs(core), host_modules={
        "supervisor21": sys.modules[__name__], "protocol21": protocol,
        "admission21": admission, "bridge16": bridge})
    slot = manifest["execution_admission_slots"].get(group_id)
    require(isinstance(slot, Mapping) and slot["attempt_id"] == attempt_id,
            "child attempt identity differs from the finalized slot")
    require(context_path == _group_context_path(manifest, group_id), "child context slot differs")
    # Nothing expensive runs until the same parent has written its actual
    # admission and phase gate. The 120-second handshake never includes a
    # frozen replay on either side.
    admission_path, phase_path = slot["admission_path"], slot["phase_gate_path"]
    deadline = popen_monotonic + 120.0
    while not _path(root, admission_path, "group admission").is_file() or not _path(root, phase_path, "phase gate").is_file():
        require(time.monotonic() < deadline, "child waited too long for admission/phase gate")
        time.sleep(0.1)
    require(time.monotonic() <= deadline, "parent ready gate arrived after the handshake deadline")
    group_admission = _json(_read(root, admission_path, "group admission"), "group admission")
    phase = _json(_read(root, phase_path, "phase gate"), "phase gate")
    permit = group_admission.get("supervisor_permit")
    require(isinstance(permit, Mapping) and permit.get("scope") == "group" and
            permit.get("group_id") == group_id and permit.get("attempt_id") == attempt_id,
            "child group permit is not bound to this dispatch")
    raw_path = str(PurePosixPath(admission_path).parent / "supervisor-permit.json")
    raw = _json(_read(root, raw_path, "raw supervisor permit"), "raw supervisor permit")
    # sys.argv omits the interpreter and -E, whereas the parent seals the
    # complete Popen argv. Python retains that exact invocation in orig_argv.
    require(isinstance(sys.orig_argv, list) and all(isinstance(x, str) for x in sys.orig_argv),
            "child full interpreter invocation is unavailable")
    require(raw.get("schema") == RAW_PERMIT_SCHEMA and raw.get("scope") == "group" and
            raw.get("pid") == os.getpid() and raw.get("birth") == _birth(os.getpid()) and
            raw.get("group_id") == group_id and raw.get("attempt_id") == attempt_id and
            raw.get("argv_sha256") == sha256(canonical_json(list(sys.orig_argv))),
            "child process/argv identity differs")
    require(phase.get("group_id") == group_id and phase.get("attempt_id") == attempt_id,
            "child phase identity differs")
    parent = bridge._read_compact_parent(root, parent_stage_ref, core=core)
    require(parent["manifest_ref"] == {"path": manifest_path, "sha256": manifest_sha256} and
            parent["core_identity"] == manifest["core_identity"], "parent receipt escaped manifest/core")
    require(raw.get("parent_stage_identity_sha256") == parent["stage_identity_sha256"] and
            raw.get("stage_identity_sha256") == parent["stage_identity_sha256"] and
            raw.get("graph_sha256") == graph.graph_sha256 == parent["graph_sha256"],
            "child permit escaped ready parent stage/graph")
    owner = parent["lock"]
    require(owner["parent_pid"] == os.getppid() and _birth(os.getppid()) == owner["parent_birth"],
            "child creator exact birth differs from parent stage")
    held = os.fstat(lock_fd)
    target = _lock_target(root, core["lock_path"]).stat()
    require((held.st_dev, held.st_ino) == (owner["dev"], owner["ino"]) ==
            (target.st_dev, target.st_ino), "child inherited lock inode differs")
    lock_identity = bridge.LockIdentity(**owner)
    contract_raw = _bound(root, core["contract"], "child canonical contract")
    registered = _registered_group_timeout({"plan": _json(contract_raw, "child canonical contract")}, group_id)
    lease = bridge.Lease(popen_monotonic, registered, PER_ATTEMPT_STARTUP_ALLOWANCE_SECONDS)
    bridge.validate_lease_progress(lease, now_monotonic=time.monotonic(), registered_deadline_seconds=registered)
    dispatch_sidecars = {
        admission_path: _file_ref(root, admission_path, "group admission"),
        phase_path: _file_ref(root, phase_path, "phase gate"),
        raw_path: _file_ref(root, raw_path, "raw permit"),
    }
    child_stage = bridge.create_child_stage(
        root, core, {"path": manifest_path, "sha256": manifest_sha256}, parent_stage_ref,
        lock_identity, lease, {"creator_pid": os.getppid(), "creator_birth": owner["parent_birth"],
        "pid": os.getpid(), "birth": _birth(os.getpid())}, parent["ledger_ref"],
        sidecars=dispatch_sidecars, graph=graph, mode="before")

    def check_child_ready() -> None:
        # Metadata witnesses never replace the actual opaque child or its graph.
        # Both checks charge the original Popen lease; neither replays evidence.
        admission.validate_child_stage_from_receipt(
            root, child_stage, parent_receipt_ref=parent_stage_ref, graph=graph,
            manifest_ref={"path": manifest_path, "sha256": manifest_sha256},
            core_identity=manifest["core_identity"], core=core,
            dispatch_sidecars=dispatch_sidecars, now_monotonic=time.monotonic(),
            stage_bridge=bridge)

    check_child_ready()
    runtime_objects = _actual_runtime_context(root, core, bridge, stage=child_stage, mode="before")
    require(runtime_objects["bridge_context"]["context_digest"] == context_digest,
            "actual child context differs from parent command")
    bridge.validate_lease_progress(lease, now_monotonic=time.monotonic(), registered_deadline_seconds=registered)
    bridge_modules = runtime_objects["modules"]
    executor = bridge_modules["executor"]
    replacement = bridge_modules["replacement05"]
    contract = _ref(core["contract"], "canonical contract")
    # The bridge's lossless runtime API has already run the scoped C4
    # validation and returns the in-process normalized object.  Re-running
    # raw ``executor.validate_plan`` here would reject the reviewed overlay.
    validated = runtime_objects["validated"]
    require(validated.get("bytes_sha256") == contract["sha256"], "child contract digest differs")
    require(validated.get("plan", {}).get("source_commit") == core["source_commit"] and
            validated.get("plan", {}).get("execution_series") == 2,
            "child frozen plan identity differs")
    require(_registered_group_timeout(validated, group_id) == registered, "child registered deadline changed")
    runtime = _dispatch_lease(validated, group_id, popen_monotonic=popen_monotonic)
    original_lock = getattr(executor, "_exclusive_lock", None)
    original_clock = getattr(executor, "_matrix_elapsed_wall", None)
    require(callable(original_lock) and callable(original_clock),
            "frozen executor lock/clock boundaries are unavailable")

    @contextlib.contextmanager
    def inherited_lock() -> Iterator[None]:
        # The parent supervisor holds this descriptor through the child.  A
        # second open would deadlock, so only the already-held lock is used.
        yield

    def resumed_clock(current: dict[str, Any], *, now_seconds: float | None = None) -> float:
        require(current is runtime, "frozen executor received an unexpected runtime context")
        now = time.time() if now_seconds is None else now_seconds
        origin = dt.datetime.fromisoformat(ORIGIN).timestamp()
        elapsed = now - origin
        require(elapsed >= 0, "child elapsed clock precedes original origin")
        return elapsed

    original_contenders = executor._contenders
    executor._contenders = lambda table: list(dict.fromkeys(original_contenders(table) + _hashed_bifrost_contenders(table)))
    executor._exclusive_lock = inherited_lock
    executor._matrix_elapsed_wall = resumed_clock
    try:
        loaders = graph.module("runtime_loaders21")
        with loaders.scoped_runtime_loaders(
                root, executor=executor, graph=graph,
                module_names=loaders.PRODUCTION_MODULE_NAMES):
            with _scoped_contract_snapshot(executor, runtime, core["plan_commit"]):
                with _scoped_fresh_attempt(executor, group_id):
                    with _per_source_projection_guard(executor, runtime):
                        check_child_ready()
                        result = executor.run_group(runtime, group_id)
    finally:
        executor._contenders = original_contenders
        executor._exclusive_lock = original_lock
        executor._matrix_elapsed_wall = original_clock
    protocol._terminal_identity(dict(result), group_id=group_id, attempt_id=attempt_id,
                                source_commit=core["source_commit"], plan_commit=core["plan_commit"],
                                contract_sha256=core["contract"]["sha256"], execution_series=2,
                                label="frozen terminal result")
    return dict(result)


def _hashed_bifrost_contenders(table: str) -> list[str]:
    found = []
    for line in table.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) != 4:
            continue
        args = fields[3].lower()
        command = Path(args.split()[0]).name if args else ""
        if re.fullmatch(r"bifrost-[0-9a-f]{6,64}", command) is None:
            continue
        try:
            cpu = float(fields[1])
        except ValueError:
            cpu = 100.0
        if ("--mcp" in args or "--lsp" in args) and cpu < 1.0:
            continue
        found.append(line.strip())
    return found


def _terminal_continuation_safety(root: Path, core: Mapping[str, Any], row: Mapping[str, Any],
                                  receipt_sha: str, executor: Any, admission: Any,
                                  validated: Mapping[str, Any], lock: _HeldLockProxy, *,
                                  protocol: Any | None = None, disk: Any | None = None) -> dict[str, Any]:
    """Recheck exact tracked births and ALL resource categories before next slot."""
    protocol = _load_protocol(root) if protocol is None else protocol
    protocol._terminal_identity(dict(row), group_id=row.get("group_id"), attempt_id=row.get("attempt_id"),
                                source_commit=core["source_commit"], plan_commit=core["plan_commit"],
                                contract_sha256=core["contract"]["sha256"], execution_series=2,
                                label="terminal containment boundary")
    tracker = executor._process_tracker()
    table = tracker._process_table()
    tracked = row["process_ownership"]["tracked_processes"]
    for item in tracked:
        require(isinstance(item, Mapping) and type(item.get("pid")) is int and
                isinstance(item.get("start_identity"), str) and item["start_identity"],
                "tracked birth receipt is malformed")
        current = table.get(item["pid"])
        require(current is None or current[1] != item["start_identity"],
                "owned exact-birth analyzer descendant remains live")
    normalized = dict(validated)
    normalized["repo_root"] = root
    _configuration_live_gate(admission, executor, root, core, lock, normalized,
                             core["source_commit"], "terminal-before-next-independent-slot")
    require(not _hashed_bifrost_contenders(executor._process_table()), "foreign hashed Bifrost contender")
    execution = Path(row["execution_root"])
    execution_base = root / Path(*executor.EXECUTION_ROOT.parts)
    require(execution.is_absolute() and executor._under(execution, execution_base),
            "terminal source execution root escapes task namespace")
    retained, scratch = executor._matrix_capacity_paths(
        normalized, execution, {"HOME": str(execution / "home"), "TMPDIR": str(execution / "tmp")}, [])
    # Include exact historical output roots, even where later reviewed contracts
    # changed their normalized group path. Never replace these with latest paths.
    rows = [json.loads(line) for line in _read(root, LEDGER_PATH).splitlines()]
    source_roots = {execution}
    for old in rows:
        previous = Path(old.get("execution_root", ""))
        require(previous.is_absolute() and executor._under(previous, execution_base),
                "historical source execution root escapes task namespace")
        source_roots.add(previous)
        for output in old.get("output_roots", []):
            relative = protocol._relative(output, "historical retained root")
            retained.append(previous / Path(*relative.parts))
    if execution_base.exists():
        for series in execution_base.iterdir():
            require(not series.is_symlink() and series.is_dir(), "unsafe source series namespace")
            for group in series.iterdir():
                require(not group.is_symlink() and group.is_dir(), "unsafe source group namespace")
                for attempt in group.iterdir():
                    require(not attempt.is_symlink() and attempt.is_dir(), "unsafe source attempt namespace")
                    source_roots.add(attempt)
    members = tuple(executor.SNAPSHOT_DIRECTORIES) + tuple(executor.SNAPSHOT_FILES) + tuple(
        item["path"] for item in normalized["source_inputs"]) + (".git",)
    working = [source / Path(*protocol._relative(member, "source working member").parts)
               for source in source_roots for member in members]
    disk = _load_module(root, "scripts/v092_disk_guard.py", "terminal disk guard") if disk is None else disk
    gib = 1024 ** 3
    guard = disk.DiskGuard(launch_floor_bytes=127*gib, protected_reserve_bytes=40*gib,
                           stop_margin_bytes=8*gib, stop_floor_bytes=48*gib,
                           scratch_ceiling_bytes=24*gib, retention_ceiling_bytes=24*gib,
                           working_ceiling_bytes=30*gib)
    for category, paths in (("scratch", scratch), ("retention", retained), ("working", working)):
        guard.check(projected_bytes=0, category=category, paths=paths, capacity_path=root)
    return {"schema": "v092-bifrost-v0140-terminal-continuation-safety/v1",
            "status": "tracked-cleanup-and-resource-checked", "group_id": row["group_id"],
            "attempt_id": row["attempt_id"], "receipt_sha256": receipt_sha,
            "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "owned_processes_gone": True, "resources_valid": True,
            "tracked_processes": list(tracked)}


def _stage_context(bridge: Any, stage: Any) -> Mapping[str, Any]:
    retained = bridge.runtime_objects(stage)
    require(retained is stage.runtime, "opaque stage runtime identity changed")
    value = retained.objects["bridge_context"]
    require(isinstance(value, Mapping), "stage has no actual bridge diagnostic")
    return value


def _stage_ledger(root: Path, admission: Any, core: Mapping[str, Any], index: int) -> dict[str, Any]:
    """Retain an immutable actual ledger for each of the 21 replay states."""
    raw, rows = _jsonl(root, LEDGER_PATH)
    path = str(PurePosixPath(core["sidecar_namespace"]) / "stages" / f"stage-{index:02d}-ledger.jsonl")
    ref = admission._write_bytes_exclusive(root, path, raw)
    return {**ref, "rows": len(rows)}


def _stage_receipt(root: Path, bridge: Any, stage: Any, core: Mapping[str, Any],
                   manifest_ref: Mapping[str, Any], core_identity: Mapping[str, Any],
                   predecessor_receipt_ref: Mapping[str, str] | None = None) -> dict[str, str]:
    path = str(PurePosixPath(core["sidecar_namespace"]) / "stages" /
               f"stage-{stage.identity.index:02d}.json")
    return bridge.write_compact_stage_receipt(
        root, path, stage,
        status="parent-stage-verified" if stage.identity.index == 0 else "successor-stage-verified",
        sidecar_names=tuple(sorted(stage.sidecars)), manifest_ref=manifest_ref,
        core_identity=core_identity, predecessor_receipt_ref=predecessor_receipt_ref, core=core)


def run_groups(root: Path | str, manifest_path: str, manifest_sha256: str,
               bridge_context: Mapping[str, Any] | None, parent_authorization_ref: object,
               parent_authorization_sha256: str | None,
               group_authorizations: Mapping[str, tuple[object, str]], *,
               fixture_only: bool = False,
               authorization_bundle_ref: object | None = None,
               authorization_bundle_sha256: str | None = None) -> dict[str, Any]:
    """One S0 replay, then one full successor replay for every actual terminal.

    Same-state consumers retain the exact graph and opaque runtime. A child
    starts its own single replay only after its ready gate. No retry branch
    exists here; contained failures are retained before the next group.
    """
    root = Path(root).resolve()
    require((fixture_only and _temporary_fixture(root)) or os.environ.get(EXPERIMENT_ENV) == "1",
            "batch execution requires the reviewed experiment marker")
    protocol, manifest, core = _static(root, manifest_path, manifest_sha256)
    admission = _load_admission(root, core)
    bridge = _load_bridge(root, core)
    graph = bridge.prepare_graph(root, bridge._core_graph_inputs(core), host_modules={
        "supervisor21": sys.modules[__name__], "protocol21": protocol,
        "admission21": admission, "bridge16": bridge})
    results: list[dict[str, Any]] = []
    manifest_ref = {"path": manifest_path, "sha256": manifest_sha256}
    with _lock_fd(_lock_target(root, core["lock_path"])) as lock:
        lock_proxy = _HeldLockProxy(root, lock)
        parent_process = _process(os.getpid())
        lock_identity = bridge.capture_lock(root, core["lock_path"], os.getpid(), parent_process["birth_identity"])
        ledger = _stage_ledger(root, admission, core, 0)
        stage = bridge.create_parent_stage(root, core, manifest_ref, 0, lock_identity, ledger,
                                           graph=graph)
        stage_ref = _stage_receipt(root, bridge, stage, core, manifest_ref, manifest["core_identity"])
        context = _stage_context(bridge, stage)
        bindings = {"stage": stage, "pinned_bridge": bridge, "graph": graph}
        require(authorization_bundle_ref is not None and authorization_bundle_sha256,
                "batch requires one exact authorization bundle")
        bundle = admission.validate_authorization_bundle(
            root, manifest_path, manifest_sha256, context,
            authorization_bundle_ref, authorization_bundle_sha256, **bindings)
        parent_authorization_ref = bundle["parent"]
        parent_authorization_sha256 = bundle["parent"]["sha256"]
        group_authorizations = {g: (bundle["groups"][g], bundle["groups"][g]["sha256"])
                                for g in core["replacement_groups"]}
        parent_permit = raw_permit(os.getpid(), {"argv": list(sys.argv), "command_spec_sha256": None},
                                   scope="parent", stage=stage)
        parent_slot = str(PurePosixPath(core["sidecar_namespace"]) / "parent-permit.json")
        parent_permit_ref = _write_raw_permit(root, parent_slot, parent_permit, protocol=protocol)
        parent_ref = admission.admit_parent(
            root, manifest_path, manifest_sha256, parent_authorization_ref,
            parent_authorization_sha256, parent_permit_ref, parent_process, context,
            fixture_only=fixture_only, lock=lock_proxy, **bindings)
        for index, group_id in enumerate(core["replacement_groups"]):
            bridge.assert_stage_current(root, stage, graph)
            context = _stage_context(bridge, stage)
            bindings = {"stage": stage, "pinned_bridge": bridge, "graph": graph}
            slot = manifest["execution_admission_slots"][group_id]
            auth_pair = group_authorizations[group_id]
            # Start the one finite lease immediately before command assembly /
            # Popen; every operation after this point is charged to that lease.
            popen_monotonic = time.monotonic()
            spec = build_group_command(
                root, manifest_path, manifest_sha256, context, group_id,
                fixture_only=fixture_only, context_path=_group_context_path(manifest, group_id),
                lock_fd=lock.fileno(), stage=stage, bridge=bridge, admission=admission,
                protocol=protocol, manifest=manifest, core=core, parent_stage_ref=stage_ref,
                popen_monotonic=popen_monotonic)
            child = subprocess.Popen(spec["argv"], cwd=root, env=dict(spec["environment"]),
                                     start_new_session=True, close_fds=True, pass_fds=(lock.fileno(),))
            try:
                process = _process(child.pid)
                permit = raw_permit(child.pid, spec, group_id=group_id,
                                    attempt_id=slot["attempt_id"], stage=stage)
                permit_path = str(PurePosixPath(slot["admission_path"]).parent / "supervisor-permit.json")
                permit_ref = _write_raw_permit(root, permit_path, permit, protocol=protocol)
                group_ref = admission.admit_group(
                    root, manifest_path, manifest_sha256, group_id, auth_pair[0], auth_pair[1],
                    permit_ref, parent_ref, process, context, spec,
                    fixture_only=fixture_only, lock=lock_proxy, **bindings)
                phase_ref = admission.write_phase_gate(
                    root, manifest_path, manifest_sha256, group_id, group_ref, process,
                    permit_ref, spec, context, fixture_only=fixture_only, lock=lock_proxy, **bindings)
                code = _wait_group_child(child, bridge.runtime_objects(stage).objects["validated"],
                                         group_id, popen_monotonic=popen_monotonic)
                after_path = str(PurePosixPath(slot["completion_path"]).parent / "ledger-after.jsonl")
                after_ref = admission._write_bytes_exclusive(root, after_path, _read(root, LEDGER_PATH))
                next_ledger = _stage_ledger(root, admission, core, index + 1)
                before_path = str(PurePosixPath(slot["admission_path"]).parent / "ledger-before.jsonl")
                before_ref = _file_ref(root, before_path, "ledger before")
                terminal_path = f"reports/releases/v0.9.2/attempts/{slot['attempt_id']}/completed.json"
                terminal_raw = _read(root, terminal_path)
                terminal = _json(terminal_raw, "actual terminal receipt")
                terminal_ref = {"path": terminal_path, "sha256": sha256(terminal_raw)}
                transition_refs = [parent_ref, parent_permit_ref, stage_ref, group_ref,
                                   phase_ref, permit_ref, before_ref, after_ref, terminal_ref]
                transition_sidecars = {ref["path"]: ref for ref in transition_refs}
                # Full updated capture/ledger replay happens BEFORE completion.
                successor = bridge.create_parent_stage(
                    root, core, manifest_ref, index + 1, lock_identity, next_ledger,
                    graph=graph, predecessor=stage, sidecars=transition_sidecars)
                completion_context = _stage_context(bridge, successor)
                actual = bridge.runtime_objects(successor).objects
                loaders = graph.module("runtime_loaders21")
                with loaders.scoped_runtime_loaders(
                        root, executor=actual["modules"]["executor"], graph=graph,
                        module_names=loaders.PRODUCTION_MODULE_NAMES):
                    safety = _terminal_continuation_safety(
                        root, core, terminal, sha256(terminal_raw), actual["modules"]["executor"],
                        admission, actual["validated"], lock_proxy, protocol=protocol,
                        disk=graph.module("disk_guard"))
                completion_ref, finalized = admission.write_completion(
                    root, manifest_path, manifest_sha256, group_id, group_ref, phase_ref,
                    terminal_ref, before_ref, after_ref, completion_context,
                    fixture_only=fixture_only, lock=lock_proxy, continuation_safety=safety,
                    predecessor_stage=stage, successor_stage=successor,
                    pinned_bridge=bridge, graph=graph)
                previous_stage_ref = stage_ref
                stage = finalized
                stage_ref = _stage_receipt(
                    root, bridge, stage, core, manifest_ref, manifest["core_identity"],
                    predecessor_receipt_ref=previous_stage_ref)
                results.append({"group_id": group_id, "attempt_id": slot["attempt_id"],
                                "status": terminal["status"], "child_exit_code": code,
                                "automatic_retry": False, "completion": completion_ref,
                                "stage_after": stage_ref})
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                protocol.write_immutable(root, str(PurePosixPath(core["sidecar_namespace"]) /
                    f"batch-stop-{len(results):02d}.json"), {
                    "schema": "v092-bifrost-v0140-independent-batch-stop/v1",
                    "status": "batch-stopped-for-global-guard-or-integrity-failure",
                    "automatic_retry": False, "breadth_first_authority": core["breadth_first_authority"],
                    "incoming_history": core["incoming_history"], "outcomes": results,
                    "stopped_group": group_id, "stopped_attempt": slot["attempt_id"],
                    "later_groups_dispatched": False})
                raise
        require(len(results) == 20 and stage.identity.index == 20,
                "batch did not reach all 21 reviewed parent states")
        selected = _stage_context(bridge, stage)["checker_summary_or_pending"]
        result = {"schema": "v092-bifrost-v0140-independent-batch-outcomes/v1",
                  "status": "batch-covered" if all(x["status"] == "completed" for x in results)
                            else "batch-covered-with-failures", "automatic_retry": False,
                  "breadth_first_authority": core["breadth_first_authority"],
                  "incoming_history": core["incoming_history"], "outcomes": results,
                  "selected_matrix": selected,
                  "full_release_gate_satisfied": selected.get("full_release_gate_satisfied") is True}
        protocol.write_immutable(root, str(PurePosixPath(core["sidecar_namespace"]) / "batch-outcomes.json"), result)
        return result


def run_configuration(root: Path | str, manifest_path: str, manifest_sha256: str,
                      bridge_context: Mapping[str, Any], authorization_ref: object,
                      authorization_sha256: str, *, output: str,
                      fixture_only: bool = False,
                      authorization_bundle_ref: object | None = None,
                      authorization_bundle_sha256: str | None = None) -> dict[str, Any]:
    """Run mixed-context configuration validation under the canonical lock.

    The routine uses the frozen bridge's actual modules and replacement-05's
    context-aware replay/projector primitives.  It writes a fresh summary,
    stdout/stderr captures, and one protocol configuration receipt through
    exclusive creation.  It never calls the old replacement execute/config
    entrypoint or accepts a runner callback.
    """
    root = Path(root).resolve()
    if fixture_only:
        require(_temporary_fixture(root),
                "fixture configuration requires a temporary root")
    else:
        require(os.environ.get(EXPERIMENT_ENV) == "1",
                "configuration requires later explicit experiment authorization")
    require(isinstance(output, str) and output and ".." not in PurePosixPath(output).parts,
            "configuration output path is unsafe")
    protocol, manifest, core = _static(root, manifest_path, manifest_sha256)
    require(output == core.get("configuration_output"),
            "configuration output must equal the reviewed core.configuration_output path")
    _relative(output, "configuration output path")
    admission = _load_admission(root, core)
    bridge = _load_bridge(root, core)
    context = _validate_context(root, core, bridge_context)
    if not fixture_only:
        require(authorization_bundle_ref is not None and authorization_bundle_sha256,
                "production configuration requires one exact authorization bundle")
        bundle = admission.validate_authorization_bundle(
            root, manifest_path, manifest_sha256, bridge_context,
            authorization_bundle_ref, authorization_bundle_sha256)
        authorization_ref = bundle["configuration"]
        authorization_sha256 = bundle["configuration"]["sha256"]
    require(authorization_ref is not None and authorization_sha256,
            "configuration authorization is missing")
    if not fixture_only:
        prepared = admission.validate_preparation(root, manifest_path, manifest_sha256, bridge_context)
        require(prepared.get("bridge_context") == dict(bridge_context),
                "configuration bridge context differs from actual frozen validation")
    lock_path = _lock_target(root, core["lock_path"])
    output_path = root / Path(*_relative(output, "configuration output path").parts)
    staging = output_path.parent / f".{output_path.name}.staging-{os.getpid()}"
    require(not staging.exists() and not output_path.exists() and not output_path.is_symlink(),
            "configuration output namespace already exists")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True)
    results: list[dict[str, Any]] = []
    try:
        with _lock_fd(lock_path) as lock:
            proxy = _HeldLockProxy(root, lock)
            process = _process(os.getpid())
            permit = raw_permit(os.getpid(), {"argv": list(sys.argv), "command_spec_sha256": None},
                                scope="configuration")
            slot = manifest["configuration_admission_slot"]
            permit_ref = _write_raw_permit(
                root, str(PurePosixPath(slot["admission_path"]).parent / "supervisor-permit.json"), permit)
            admission_ref = admission.admit_configuration(
                root, manifest_path, manifest_sha256, authorization_ref, authorization_sha256,
                permit_ref, process, context, fixture_only=fixture_only, lock=proxy)
            # Admission validated the before context above.  Configuration
            # consumes a fresh after-mode lossless bridge context so its
            # checker summary covers the complete final 90+20-row ledger.
            runtime, modules = _mixed_runtime_context(
                root, manifest, core, manifest_sha256, context, bridge, mode="after")
            replacement = modules["replacement05"]
            configuration = modules["configuration"]
            summary, selected = _configuration_summary(runtime, replacement)
            buckets = replacement.configuration_contexts(selected, runtime["contexts"])
            for index, (contract_sha, attempt_ids) in enumerate(sorted(buckets.items())):
                origin = runtime["contexts"].get(contract_sha)
                require(isinstance(origin, Mapping), "selected context is not registered")
                validated = origin.get("validated")
                require(isinstance(validated, Mapping), "selected context lacks validated plan")
                checkout = root / "execution-state/v092/validation" / f"{output}-{index:02d}"
                require(not checkout.exists() and not checkout.is_symlink(), "configuration checkout exists")
                subset = {**summary,
                          "fresh_reports": [x for x in summary["fresh_reports"] if x.get("attempt_id") in attempt_ids],
                          "selected_attempts": [x for x in summary["selected_attempts"] if x.get("attempt_id") in attempt_ids]}
                partitions = len(subset["fresh_reports"])
                rows = sum(x.get("rows", 0) for x in subset["fresh_reports"])
                source_inputs = validated.get("source_inputs")
                require(isinstance(source_inputs, list), "selected context source closure is missing")
                source_paths: list[str] = []
                for item in source_inputs:
                    if isinstance(item, Mapping):
                        require(isinstance(item.get("path"), str),
                                "selected source input ref has no path")
                        source_paths.append(item["path"])
                    else:
                        require(isinstance(item, str), "selected source input path is malformed")
                        source_paths.append(item)
                checkout.parent.mkdir(parents=True, exist_ok=True)
                materialization_gate = _configuration_live_gate(
                    admission, runtime["executor"], root, core, proxy, validated,
                    origin["source_commit"], "materialization")
                runtime["executor"]._materialize_source(
                    root, origin["source_commit"], checkout, source_paths)
                configuration._project_reports(root, checkout, subset,
                                               expected_report_count=partitions,
                                               expected_row_count=rows)
                runner = validated.get("tools", {}).get("runner")
                require(isinstance(runner, Mapping), "selected context runner identity is missing")
                environment = _expanded_runner_environment(core, checkout)
                runner_gate = _configuration_live_gate(
                    admission, runtime["executor"], root, core, proxy, validated,
                    origin["source_commit"], "runner")
                invocation = configuration._invoke_runner(runner, checkout, environment)
                (staging / f"{index:02d}-stdout.bin").write_bytes(invocation["stdout"])
                (staging / f"{index:02d}-stderr.bin").write_bytes(invocation["stderr"])
                metrics = configuration._parse_stdout(invocation["stdout"])
                require(configuration._validation_success(invocation["exit_code"], metrics, partitions),
                        "mixed-context canonical configuration validation failed")
                results.append({"contract_sha256": contract_sha, "attempt_ids": attempt_ids,
                                "partitions": partitions, "rows": rows, "metrics": metrics,
                                "source_commit": origin["source_commit"],
                                "plan_commit": origin["plan_commit"],
                                "stdout_path": f"{output}.{index:02d}-stdout.bin",
                                "stdout_sha256": sha256(invocation["stdout"]),
                                "stderr_path": f"{output}.{index:02d}-stderr.bin",
                                "stderr_sha256": sha256(invocation["stderr"]),
                                "exit_code": invocation.get("exit_code"),
                                "timed_out": invocation.get("timed_out", False),
                                "invocation_error": invocation.get("error"),
                                "materialization_phase_gate": materialization_gate,
                                "runner_phase_gate": runner_gate,
                                "runner": dict(runner), "runner_environment": environment})
            require(sum(item["partitions"] for item in results) == 92 and
                    sum(item["rows"] for item in results) == 4252 and
                    sum(item["metrics"].get("known_stale", 0) for item in results) == 0,
                    "configuration denominator changed")
            require(results, "configuration produced no source-context results")
            # Move captures into the reviewed sidecar namespace before sealing
            # the summary.  A failure leaves the staging directory and any
            # completed captures available for diagnosis.
            for item in results:
                for field in ("stdout_path", "stderr_path"):
                    relative = item[field]
                    target = root / Path(*_relative(relative, field).parts)
                    require(not target.exists() and not target.is_symlink(),
                            f"configuration capture already exists: {relative}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    staged = staging / PurePosixPath(relative).name
                    require(staged.is_file(), f"missing staged configuration capture: {relative}")
                    staged.rename(target)
            staging.rmdir()
            summary_value = {"status": "canonical-validation-passed", "automatic_retry": False,
                             "core_identity": manifest["core_identity"],
                             "manifest_path": manifest_path, "manifest_sha256": manifest_sha256,
                             "output_path": output, "ledger_sha256": sha256(_read(root, LEDGER_PATH)),
                             "partitions": 92, "rows": 4252, "known_stale": 0,
                             "checker_summary": summary["checker_summary"],
                             "configuration_summary": runtime["configuration_summary"],
                             "source_contexts": results}
            summary_ref = protocol.write_immutable(root, output, summary_value)
            receipt = {"schema": "v092-bifrost-v0140-configuration-receipt/v1",
                       "status": "canonical-validation-passed", "automatic_retry": False,
                       "core_identity": manifest["core_identity"], "manifest_path": manifest_path,
                       "manifest_sha256": manifest_sha256, "output_path": output,
                       "output_sha256": summary_ref["sha256"], "partitions": 92, "rows": 4252,
                       "known_stale": 0}
            receipt_ref = protocol.write_immutable(root, slot["receipt_path"], receipt)
            protocol.validate_configuration_admission(root, manifest_path, admission_ref["path"],
                                                     receipt_ref["path"])
            return {"status": receipt["status"], "admission": admission_ref,
                    "receipt": receipt_ref, "summary": summary_ref}
    except BaseException:
        # Preserve every staged capture and any sealed output for independent
        # diagnosis.  Fresh-namespace checks intentionally block an implicit
        # retry from overwriting this evidence.
        raise


def _child_main(args: argparse.Namespace) -> int:
    result = _run_frozen_group(Path(args.root).resolve(), args.manifest, args.manifest_sha256, args.group,
                               args.attempt_id, args.bridge_context, args.context_sha256,
                               args.lock_fd, parent_stage_ref={"path": args.parent_stage,
                               "sha256": args.parent_stage_sha256}, popen_monotonic=args.popen_monotonic)
    print(json.dumps({"status": result["status"], "group_id": result["group_id"],
                      "attempt_id": result["attempt_id"]}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--configuration", action="store_true")
    parser.add_argument("--batch", action="store_true",
                        help="validate one bound authorization bundle and run the ordered replacement batch")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--manifest", default=MANIFEST_PATH)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--group")
    parser.add_argument("--attempt-id")
    parser.add_argument("--bridge-context", default=CONTEXT_PATH)
    parser.add_argument("--context-sha256")
    parser.add_argument("--lock-fd", type=int)
    parser.add_argument("--parent-stage")
    parser.add_argument("--parent-stage-sha256")
    parser.add_argument("--popen-monotonic", type=float)
    parser.add_argument("--authorization")
    parser.add_argument("--authorization-sha256")
    parser.add_argument("--authorization-bundle")
    parser.add_argument("--authorization-bundle-sha256")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    require(sum(bool(mode) for mode in (args.child, args.configuration, args.batch)) <= 1,
            "child, configuration, and batch modes are mutually exclusive")
    require(not args.configuration,
            "replacement-21 configuration requires the later reviewed full-matrix validation controller")
    if args.batch or args.configuration:
        require(args.manifest_sha256 and (args.batch or args.context_sha256) and args.output and
                args.authorization_bundle and args.authorization_bundle_sha256,
                "batch/configuration arguments require one exact authorization bundle")
        root = Path(args.root).resolve()
        protocol, manifest, core = _static(root, args.manifest, args.manifest_sha256)
        del protocol
        allowed = [CONTEXT_PATH]
        for group in core["replacement_groups"]:
            slot = manifest["execution_admission_slots"][group]
            allowed.append(_group_context_path(manifest, group))
            allowed.append(str(PurePosixPath(slot["completion_path"]).parent /
                              "bridge-context-after.json"))
        context = None if args.batch else _context_file(
            root, args.bridge_context, args.context_sha256, allowed_paths=tuple(allowed))
        bundle_ref = _file_ref(root, args.authorization_bundle, "authorization bundle")
        require(bundle_ref["sha256"] == args.authorization_bundle_sha256,
                "authorization bundle digest differs")
        if args.batch:
            # run_groups validates every stable parent/group/configuration
            # receipt before it creates the first child.  The group loop then
            # refreshes each mutable bridge context under the held lock.
            groups_result = run_groups(
                root, args.manifest, args.manifest_sha256, context,
                None, None, {}, authorization_bundle_ref=bundle_ref,
                authorization_bundle_sha256=args.authorization_bundle_sha256)
            if not groups_result["full_release_gate_satisfied"]:
                print(json.dumps({"status": groups_result["status"], "batch": groups_result,
                                  "configuration": {"status": "configuration-pending-complete-matrix"}},
                                 sort_keys=True))
                return 0
            print(json.dumps({"status": groups_result["status"], "batch": groups_result,
                              "configuration": {"status": "separate-final-validation-required"}}, sort_keys=True))
            return 0
        # Configuration remains a separately invokable fixed entrypoint, but
        # it uses the same immutable bundle and performs the same full
        # admission check.  There is no legacy single-authorization branch.
        result = run_configuration(
            root, args.manifest, args.manifest_sha256, context,
            None, None, output=args.output,
            authorization_bundle_ref=bundle_ref,
            authorization_bundle_sha256=args.authorization_bundle_sha256)
        print(json.dumps(result, sort_keys=True))
        return 0
    if not args.child:
        raise Supervisor21Error("replacement-21 supervisor has no unbound CLI launch mode")
    require(args.group and args.attempt_id and args.manifest_sha256 and args.context_sha256 and
            args.lock_fd is not None and args.parent_stage and args.parent_stage_sha256 and
            args.popen_monotonic is not None,
            "child launch arguments are incomplete")
    return _child_main(args)




# BF21 staged controller --------------------------------------------------
# This is a pure stage coordinator.  Production process dispatch remains in
# the reviewed outer controller; this API exists so that controller code can
# pass one actual opaque stage through admission, phase, terminal and
# completion without triggering hidden bridge reloads.
STAGE_SCHEMA = "v092-bifrost-v0140-replay-stage/v4"
STAGE_BRIDGE_PATH = "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-16.py"
PARENT_STAGE_COUNT = 21
CHILD_STAGE_COUNT = 20


def validate_stage_graph(graph: Any) -> None:
    require(graph is not None and callable(getattr(graph, "assert_complete", None)),
            "stage graph has no pinned completeness boundary")
    # The bridge-owned class checks its canonical complete transitive roster;
    # duplicating a second list here would drift when a nested loader changes.
    graph.assert_complete({member.name: member.module_object for member in graph.members})


def staged_parent_ready(root: Path | str, stage: Any, graph: Any, *, index: int,
                       expected_ledger_sha256: str | None = None,
                       stage_bridge: Any | None = None) -> dict[str, Any]:
    """Validate an already replayed stage without replaying or dispatching."""
    validate_stage_graph(graph)
    require(stage.graph is graph and stage.identity.index == index, "parent stage/graph mismatch")
    if expected_ledger_sha256 is not None:
        require(stage.identity.ledger_sha256 == expected_ledger_sha256, "parent stage ledger mismatch")
    require(stage_bridge is not None and callable(getattr(stage_bridge, "assert_stage_current", None)),
            "same-stage supervisor use requires the pinned bridge module instance")
    stage_bridge.assert_stage_current(Path(root).resolve(), stage, graph)
    return {"schema": STAGE_SCHEMA + "/parent-ready", "stage_index": index,
            "stage_identity_sha256": stage.identity_sha256, "graph_sha256": graph.graph_sha256,
            "ledger_sha256": stage.identity.ledger_sha256, "status": "ready"}


def staged_child_ready(root: Path | str, child: Any, parent: Any, graph: Any,
                       *, now_monotonic: float, stage_bridge: Any | None = None) -> dict[str, Any]:
    validate_stage_graph(graph)
    require(child.graph is graph, "child stage graph instance differs from the supplied child graph")
    require(tuple(member.binding() for member in parent.graph.members) ==
            tuple(member.binding() for member in graph.members),
            "child graph path/SHA binding differs from the parent stage")
    require(stage_bridge is not None and callable(getattr(stage_bridge, "assert_child_ready", None)),
            "same-stage supervisor child use requires the pinned bridge module instance")
    remaining = stage_bridge.assert_child_ready(Path(root).resolve(), child, parent=parent, graph=graph,
                                                now_monotonic=now_monotonic)
    return {"schema": STAGE_SCHEMA + "/child-ready", "status": "ready",
            "parent_stage_identity_sha256": parent.identity_sha256,
            "child_stage_identity_sha256": child.identity_sha256,
            "child": child.child_identity, "startup_remaining_seconds": remaining}


def validate_stage_sequence(root: Path | str, parent_stages: Sequence[Any], child_stages: Sequence[Any],
                            graph_by_stage: Sequence[Any], *, stage_bridges: Sequence[Any] | None = None) -> dict[str, Any]:
    """Validate the 21/20 stage cardinalities and immutable transitions."""
    require(len(parent_stages) == PARENT_STAGE_COUNT, "BF21 requires exactly 21 parent stages")
    require(len(child_stages) == CHILD_STAGE_COUNT, "BF21 requires exactly 20 child stages")
    require(len(graph_by_stage) == PARENT_STAGE_COUNT, "one complete graph is required per parent stage")
    require(stage_bridges is not None and len(stage_bridges) == PARENT_STAGE_COUNT,
            "each stage requires its pinned bridge module instance")
    for index, (stage, graph, stage_bridge) in enumerate(zip(parent_stages, graph_by_stage, stage_bridges)):
        staged_parent_ready(root, stage, graph, index=index, stage_bridge=stage_bridge)
        if index:
            previous = parent_stages[index - 1]
            require(stage.identity.ledger_rows == previous.identity.ledger_rows + 1,
                    "each successor stage must append one terminal row")
            require(stage.identity.lock == previous.identity.lock, "canonical lock identity changed between stages")
    for index, child in enumerate(child_stages):
        require(child.identity.index == index, "child stage index is not deterministic")
        require(child.parent_identity_sha256 == parent_stages[index].identity_sha256,
                "child stage parent identity differs")
    return {"schema": STAGE_SCHEMA + "/sequence", "status": "stage-sequence-verified",
            "parent_stages": len(parent_stages), "child_stages": len(child_stages),
            "graph_sha256": [graph.graph_sha256 for graph in graph_by_stage]}



if __name__ == "__main__" and __spec__ is None:
    raise SystemExit(main())
