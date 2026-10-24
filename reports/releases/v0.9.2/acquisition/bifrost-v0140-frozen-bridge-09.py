#!/usr/bin/env python3
"""Stage-aware frozen bridge for the append-only Bifrost-14 successor.

This module is deliberately a small boundary around the reviewed frozen
bridge.  A stage owns the opaque runtime objects produced by one validation
and the complete module graph that produced them.  Callers pass the same
stage to admission, phase, terminal and completion checks; those operations
must not reload a graph or reconstruct runtime objects from JSON.

The production loader accepts only hash-pinned path references supplied by a
reviewed core.  The only injection seam is ``fixture_only=True`` under a
temporary directory, used by the focused tests.  No function in this module
starts a process, acquires a release lock, materializes a checkout, or runs
an analyzer.
"""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "v092-bifrost-v0140-frozen-bridge/v9"
HANDSHAKE_SECONDS = 120
STARTUP_SECONDS = 600
PARENT_STAGE_COUNT = 21
CHILD_STAGE_COUNT = 20
REQUIRED_GRAPH_NAMES = (
    "bridge09", "replacement14", "executor", "checker", "configuration",
    "incoming_recovery", "policy_source", "policy_runtime", "protocol14",
    "admission14", "supervisor14",
)
OPTIONAL_GRAPH_NAMES = ("disk_guard",)
STAGE_RUNTIME_GRAPH_NAME = "stage_runtime01"
GRAPH_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")


def _graph_name_variants() -> tuple[tuple[str, ...], ...]:
    """Return the only accepted graph rosters, in deterministic order.

    ``stage_runtime01`` is an append-only successor seam.  It is optional for
    the historical bridge fixture and mandatory for the production successor;
    accepting arbitrary extra names here would let a caller smuggle an
    unreviewed loader into the runtime graph.
    """
    return (
        REQUIRED_GRAPH_NAMES,
        REQUIRED_GRAPH_NAMES + ("disk_guard",),
        REQUIRED_GRAPH_NAMES + (STAGE_RUNTIME_GRAPH_NAME,),
        REQUIRED_GRAPH_NAMES + ("disk_guard", STAGE_RUNTIME_GRAPH_NAME),
    )


def _validate_graph_names(names: Sequence[str]) -> tuple[str, ...]:
    """Validate the mandatory roster plus explicitly sealed transitive extras.

    The first eleven roles are fixed.  Later names are the exact extra module
    instances enumerated by the reviewed core graph (aliases are permitted),
    sorted for deterministic graph identity.  A loader cannot add a module
    after this boundary; each extra is still path/SHA checked by load/bind.
    """
    names = tuple(names)
    require(names[:len(REQUIRED_GRAPH_NAMES)] == REQUIRED_GRAPH_NAMES,
            "graph omits or reorders a required runtime role")
    extras = names[len(REQUIRED_GRAPH_NAMES):]
    require(len(set(names)) == len(names), "graph has duplicate module names")
    require(all(isinstance(name, str) and GRAPH_NAME_RE.fullmatch(name) for name in extras),
            "graph contains a malformed transitive module instance name")
    require(tuple(sorted(extras)) == extras, "transitive graph extras are not deterministically sorted")
    return names


def _replacement_runtime_member(graph: Any) -> object:
    """Return the graph-owned full bridge validator, never the protocol facade."""
    names = {getattr(member, "name", "") for member in getattr(graph, "members", ())}
    if "replacement05" in names:
        return graph.module("replacement05")
    return graph.module("replacement14")
SHA_RE = set("0123456789abcdef")


class FrozenBridge09Error(ValueError):
    """A stage, graph, sidecar, or stable file binding failed closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise FrozenBridge09Error(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha(value: object, label: str = "sha256") -> str:
    require(isinstance(value, str) and len(value) == 64 and set(value) <= SHA_RE, f"{label} is malformed")
    return value


def _relative(value: object, label: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{label} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts), f"unsafe {label}")
    return path


def _path(root: Path, value: str, label: str = "path") -> Path:
    relative = _relative(value, label)
    current = root.resolve()
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), f"symlink in {label}: {value}")
    require(current.is_relative_to(root.resolve()), f"{label} escaped root")
    return current


def _ref(value: object, label: str = "ref") -> dict[str, Any]:
    require(isinstance(value, Mapping) and set(value) <= {"path", "sha256", "rows", "stat"},
            f"{label} has unexpected fields")
    require("path" in value and "sha256" in value, f"{label} needs path and sha256")
    path = value["path"]
    _relative(path, f"{label} path")
    digest = _sha(value["sha256"], f"{label} sha256")
    result: dict[str, Any] = {"path": path, "sha256": digest}
    if "rows" in value:
        require(type(value["rows"]) is int and value["rows"] > 0, f"{label} rows malformed")
        result["rows"] = value["rows"]
    if "stat" in value:
        require(isinstance(value["stat"], Mapping), f"{label} stat malformed")
        result["stat"] = dict(value["stat"])
    return result


def _stat_tuple(path: Path, label: str = "file") -> tuple[int, int, int, int, int]:
    try:
        value = path.lstat()
    except OSError as exc:
        raise FrozenBridge09Error(f"cannot stat {label}") from exc
    require(stat.S_ISREG(value.st_mode) and not path.is_symlink(), f"{label} must be a regular non-symlink file")
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _stat_dict(value: tuple[int, int, int, int, int]) -> dict[str, int]:
    return dict(zip(("dev", "ino", "size", "mtime_ns", "ctime_ns"), value))


def stable_read(root: Path | str, reference: Mapping[str, Any], label: str = "file") -> tuple[bytes, dict[str, int]]:
    """Read and hash an immutable ref with lstat-before/hash/lstat-after."""
    root = Path(root).resolve()
    ref = _ref(reference, label)
    path = _path(root, ref["path"], f"{label} path")
    before = _stat_tuple(path, label)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FrozenBridge09Error(f"cannot read {label}") from exc
    after = _stat_tuple(path, label)
    require(before == after, f"{label} changed while being read")
    require(sha256(raw) == ref["sha256"], f"{label} digest changed")
    return raw, _stat_dict(before)


def stable_metadata(root: Path | str, reference: Mapping[str, Any], label: str = "file") -> dict[str, int]:
    """Check current metadata for a same-stage file without rehashing it."""
    root = Path(root).resolve()
    ref = _ref(reference, label)
    path = _path(root, ref["path"], f"{label} path")
    current = _stat_dict(_stat_tuple(path, label))
    expected = ref.get("stat")
    if expected is not None:
        require(dict(expected) == current, f"{label} metadata changed")
    return current


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return {"__type__": "path", "value": str(value)}
    if isinstance(value, bytes):
        return {"__type__": "bytes", "value": value.hex()}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Opaque runtime objects are represented by type only.  Their authority
    # never comes from this digestable representation; the pinned bridge's
    # lossless in-process object identity is retained separately by the stage.
    # Omitting ``id`` keeps the compact receipt stable across parent/child
    # processes while preventing JSON from becoming a runtime substitute.
    return {"__opaque_type__": type(value).__module__ + ":" + type(value).__qualname__}


def runtime_digest(runtime: object) -> str:
    if isinstance(runtime, ActualRuntimeContext):
        digest = runtime.diagnostic.get("context_digest")
        return _sha(digest, "actual runtime context digest")
    return sha256(canonical_json(_jsonable(runtime)))


@dataclasses.dataclass(frozen=True)
class GraphMember:
    name: str
    canonical_path: str
    source_sha256: str
    module_object: object = dataclasses.field(repr=False, compare=False)
    loader_identity: str

    def public(self) -> dict[str, str]:
        return {"name": self.name, "canonical_path": self.canonical_path,
                "source_sha256": self.source_sha256, "loader_identity": self.loader_identity}

    def binding(self) -> dict[str, str]:
        """Stable cross-process identity; loader identity stays stage-local."""
        return {"name": self.name, "canonical_path": self.canonical_path,
                "source_sha256": self.source_sha256}


class PinnedBridgeGraph:
    """Complete stage-local module graph; members are identity checked."""
    __slots__ = ("_members", "_by_name", "graph_sha256", "fixture_only", "_sealed")

    def __init__(self, members: Sequence[GraphMember], *, fixture_only: bool = False) -> None:
        canonical_names = tuple(item.name for item in members)
        _validate_graph_names(canonical_names)
        names = [item.name for item in members]
        require(len(set(names)) == len(names), "graph has duplicate module names")
        self._members = tuple(members)
        self._by_name = {item.name: item for item in members}
        self.graph_sha256 = sha256(canonical_json([item.binding() for item in members]))
        self.fixture_only = fixture_only
        self._sealed = True

    @property
    def members(self) -> tuple[GraphMember, ...]:
        return self._members

    def module(self, name: str) -> object:
        require(name in self._by_name, f"graph member is not registered: {name}")
        return self._by_name[name].module_object

    def assert_member(self, name: str, module: object) -> None:
        expected = self._by_name.get(name)
        require(expected is not None and expected.module_object is module,
                f"foreign or reloaded graph member: {name}")

    def assert_complete(self, modules: Mapping[str, object]) -> None:
        # Legacy consumers expose the eleven authority roles; stage consumers
        # pass the entire sealed transitive graph. Both shapes must retain the
        # exact registered objects, with no partial selection of extra roles.
        require(tuple(modules) in (REQUIRED_GRAPH_NAMES, tuple(self._by_name)),
                "graph consumer supplied incomplete module set")
        for name in modules:
            self.assert_member(name, modules[name])

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise FrozenBridge09Error("pinned graph is immutable")
        object.__setattr__(self, name, value)

    def __getstate__(self) -> None:
        raise FrozenBridge09Error("pinned graph cannot be serialized")


def _load_one(root: Path, name: str, ref: Mapping[str, Any], namespace: str) -> object:
    raw, _ = stable_read(root, ref, f"graph {name}")
    path = _path(root, ref["path"], f"graph {name} path")
    spec = importlib.util.spec_from_file_location(f"{namespace}_{name}", path)
    require(spec is not None and spec.loader is not None, f"cannot load graph member {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    after, _ = stable_read(root, ref, f"graph {name} after import")
    require(sha256(raw) == sha256(after) == ref["sha256"], f"graph member changed: {name}")
    return module


def load_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]], *,
               fixture_modules: Mapping[str, object] | None = None,
               fixture_only: bool = False) -> PinnedBridgeGraph:
    """Load the exact complete graph, with a temporary fixture seam only."""
    root = Path(root).resolve()
    graph_names = tuple(refs)
    _validate_graph_names(graph_names)
    if fixture_only:
        require(fixture_modules is not None, "fixture_only requires fixture modules")
        require(root != ROOT and any(root == p or p in root.parents
                                     for p in (Path(tempfile.gettempdir()).resolve(), Path("/private/var/folders").resolve())),
                "fixture graph must be under a temporary root")
        require(tuple(fixture_modules) == graph_names, "fixture graph is incomplete")
        modules = dict(fixture_modules)
        for name, module in modules.items():
            require(getattr(module, "__name__", "").startswith("fixture_"), f"{name} is not a fixture module")
            stable_read(root, refs[name], f"fixture graph {name}")
    else:
        modules = {name: _load_one(root, name, refs[name], "v092_bifrost14_graph") for name in graph_names}
    members = tuple(GraphMember(name, refs[name]["path"], refs[name]["sha256"], modules[name],
                                f"{type(modules[name]).__module__}:{type(modules[name]).__qualname__}:{id(modules[name])}")
                    for name in graph_names)
    return PinnedBridgeGraph(members, fixture_only=fixture_only)


def bind_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]],
               host_modules: Mapping[str, object]) -> PinnedBridgeGraph:
    """Bind the already-running host modules without importing duplicates.

    Production callers run the supervisor, protocol, admission and bridge in
    one interpreter.  Re-importing those files under a synthetic name would
    produce a second class/module graph, so this boundary verifies each
    existing module against its reviewed path/SHA and retains the exact
    objects supplied by the host.  It is deliberately separate from
    ``load_graph``: the latter is the fresh-child graph constructor.
    """
    root = Path(root).resolve()
    graph_names = tuple(refs)
    _validate_graph_names(graph_names)
    require(set(host_modules) <= set(graph_names) and host_modules,
            "host graph contains an unknown or empty module set")
    members: list[GraphMember] = []
    for name in graph_names:
        module = host_modules.get(name)
        if module is None:
            module = _load_one(root, name, refs[name], "v092_bifrost14_graph")
        require(module is not None and hasattr(module, "__file__"),
                f"host graph member {name} has no module file")
        module_path = Path(str(module.__file__)).resolve()
        expected_path = _path(root, refs[name]["path"], f"graph {name} path").resolve()
        require(module_path == expected_path,
                f"host graph member {name} is loaded from an unexpected path")
        raw, _ = stable_read(root, refs[name], f"graph {name}")
        require(sha256(raw) == refs[name]["sha256"],
                f"host graph member {name} has an unexpected source digest")
        members.append(GraphMember(
            name, refs[name]["path"], refs[name]["sha256"], module,
            f"{type(module).__module__}:{type(module).__qualname__}:{id(module)}"))
    return PinnedBridgeGraph(tuple(members), fixture_only=False)


def prepare_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]],
                  host_modules: Mapping[str, object] | None = None) -> PinnedBridgeGraph:
    """Complete a graph from host modules plus exact one-time nested loads."""
    # The production core calls this helper with the whole core identity while
    # the focused fixture calls it with the already extracted graph refs.  Both
    # forms are accepted, but the module set is always explicit and hash-bound.
    if "graph_refs" in refs or "runtime_module_graph" in refs:
        refs = _core_graph_inputs(refs)
    if host_modules is None:
        return load_graph(root, refs)
    return bind_graph(root, refs, host_modules)


@dataclasses.dataclass(frozen=True)
class LockIdentity:
    path: str
    dev: int
    ino: int
    parent_pid: int
    parent_birth: str


def capture_lock(root: Path | str, lock_path: str, parent_pid: int, parent_birth: str) -> LockIdentity:
    root = Path(root).resolve()
    path = Path(lock_path)
    require(path.is_absolute(), "canonical lock path must be absolute")
    require(type(parent_pid) is int and parent_pid > 0 and isinstance(parent_birth, str) and parent_birth,
            "parent lock owner identity is malformed")
    st = _stat_tuple(path, "canonical lock")
    return LockIdentity(str(path), st[0], st[1], parent_pid, parent_birth)


@dataclasses.dataclass(frozen=True)
class ResourceSample:
    free_bytes: int
    working_bytes: int
    scratch_bytes: int
    retention_bytes: int

    def satisfies(self, *, free_floor: int, working_cap: int, scratch_cap: int,
                  retention_cap: int) -> bool:
        return (self.free_bytes >= free_floor and self.working_bytes <= working_cap and
                self.scratch_bytes <= scratch_cap and self.retention_bytes <= retention_cap)


@dataclasses.dataclass(frozen=True)
class Lease:
    popen_monotonic: float
    registered_deadline_seconds: float
    startup_seconds: float = STARTUP_SECONDS

    def setup_remaining(self, now_monotonic: float) -> float:
        elapsed = now_monotonic - self.popen_monotonic
        require(elapsed >= 0, "clock moved backwards")
        return self.registered_deadline_seconds + self.startup_seconds - elapsed


@dataclasses.dataclass(frozen=True)
class StageIdentity:
    index: int
    ledger_sha256: str
    ledger_rows: int
    runtime_sha256: str
    source_commit: str
    plan_commit: str
    contract_sha256: str
    lock: LockIdentity
    analyzer_deadline_seconds: float
    startup_seconds: float
    created_monotonic: float

    def digest(self) -> str:
        value = dataclasses.asdict(self)
        value["lock"] = dataclasses.asdict(self.lock)
        return sha256(canonical_json(value))


@dataclasses.dataclass(frozen=True)
class StageRef:
    path: str
    sha256: str
    stat: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "stat": dict(self.stat)}


def _stage_ref(root: Path, ref: Mapping[str, Any], label: str) -> StageRef:
    raw, st = stable_read(root, ref, label)
    return StageRef(ref["path"], ref["sha256"], st)


def _current_ref(root: Path, ref: StageRef, label: str) -> None:
    stable_metadata(root, ref.as_dict(), label)


def _validate_identity_fields(source_commit: str, plan_commit: str, contract_sha256: str) -> None:
    require(isinstance(source_commit, str) and len(source_commit) == 40 and set(source_commit) <= SHA_RE,
            "source commit is malformed")
    require(isinstance(plan_commit, str) and len(plan_commit) == 40 and set(plan_commit) <= SHA_RE,
            "plan commit is malformed")
    _sha(contract_sha256, "contract sha256")


class _OpaqueStage:
    __slots__ = ("_identity", "_graph", "_runtime", "_inventory", "_sidecars",
                 "_live_ledger", "_sealed")

    def __init__(self, identity: StageIdentity, graph: PinnedBridgeGraph, runtime: object,
                 inventory: Sequence[StageRef], sidecars: Mapping[str, StageRef],
                 live_ledger: StageRef | None = None) -> None:
        require(isinstance(graph, PinnedBridgeGraph), "stage needs a pinned graph")
        self._identity = identity
        self._graph = graph
        self._runtime = runtime
        self._inventory = tuple(inventory)
        self._sidecars = dict(sidecars)
        self._live_ledger = live_ledger
        self._sealed = True

    @property
    def identity(self) -> StageIdentity:
        return self._identity

    @property
    def identity_sha256(self) -> str:
        return self._identity.digest()

    @property
    def graph(self) -> PinnedBridgeGraph:
        return self._graph

    @property
    def runtime(self) -> object:
        return self._runtime

    @property
    def inventory(self) -> tuple[StageRef, ...]:
        return self._inventory

    @property
    def sidecars(self) -> Mapping[str, StageRef]:
        return dict(self._sidecars)

    @property
    def live_ledger(self) -> StageRef | None:
        """The mutable canonical ledger witness, kept outside the snapshot."""
        return self._live_ledger

    def assert_graph(self, graph: PinnedBridgeGraph) -> None:
        require(graph is self._graph, "same-stage consumer supplied a different graph")

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise FrozenBridge09Error("stage is immutable")
        object.__setattr__(self, name, value)

    def __getstate__(self) -> None:
        raise FrozenBridge09Error("stage runtime is opaque and cannot be serialized")


class ParentStage(_OpaqueStage):
    pass


class SuccessorStageDraft(_OpaqueStage):
    __slots__ = ("_predecessor_identity_sha256", "_ledger_before_sha256")

    def __init__(self, *args: Any, predecessor_identity_sha256: str, ledger_before_sha256: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_predecessor_identity_sha256", predecessor_identity_sha256)
        object.__setattr__(self, "_ledger_before_sha256", ledger_before_sha256)

    @property
    def predecessor_identity_sha256(self) -> str:
        return self._predecessor_identity_sha256

    @property
    def ledger_before_sha256(self) -> str:
        return self._ledger_before_sha256


class FinalizedParentStage(_OpaqueStage):
    __slots__ = ("_predecessor_identity_sha256",)

    def __init__(self, *args: Any, predecessor_identity_sha256: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_predecessor_identity_sha256", predecessor_identity_sha256)

    @property
    def predecessor_identity_sha256(self) -> str:
        return self._predecessor_identity_sha256


class ChildStage(_OpaqueStage):
    __slots__ = ("_parent_identity_sha256", "_child_creator_pid", "_child_creator_birth", "_child_pid", "_child_birth", "_lease")

    def __init__(self, *args: Any, parent_identity_sha256: str, child_creator_pid: int,
                 child_creator_birth: str, child_pid: int, child_birth: str,
                 lease: Lease, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        require(all(type(v) is int and v > 0 for v in (child_creator_pid, child_pid)), "child PIDs malformed")
        require(all(isinstance(v, str) and v for v in (child_creator_birth, child_birth)), "child births malformed")
        object.__setattr__(self, "_parent_identity_sha256", parent_identity_sha256)
        object.__setattr__(self, "_child_creator_pid", child_creator_pid)
        object.__setattr__(self, "_child_creator_birth", child_creator_birth)
        object.__setattr__(self, "_child_pid", child_pid)
        object.__setattr__(self, "_child_birth", child_birth)
        object.__setattr__(self, "_lease", lease)

    @property
    def parent_identity_sha256(self) -> str:
        return self._parent_identity_sha256

    @property
    def child_identity(self) -> dict[str, Any]:
        return {"creator_pid": self._child_creator_pid, "creator_birth": self._child_creator_birth,
                "pid": self._child_pid, "birth": self._child_birth}

    @property
    def lease(self) -> Lease:
        return self._lease


# Compatibility boundary for the reviewed frozen validators.  The stage API
# above owns the graph and prevents reloads for same-stage consumers.  The
# legacy validator itself is still pinned by path/SHA here so the BF14
# supervisor can migrate its existing read-only bridge call sites without
# accepting an unreviewed module or serialized context.
LEGACY_BRIDGE_REF = {
    "path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py",
    "sha256": "d964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189",
}
_LEGACY_MODULE_CACHE: dict[str, object] = {}


def _legacy_bridge(root: Path) -> object:
    key = str(root.resolve())
    cached = _LEGACY_MODULE_CACHE.get(key)
    if cached is not None:
        return cached
    raw, _ = stable_read(root, LEGACY_BRIDGE_REF, "legacy frozen bridge")
    path = _path(root, LEGACY_BRIDGE_REF["path"], "legacy frozen bridge path")
    spec = importlib.util.spec_from_file_location("v092_bifrost14_legacy_bridge08", path)
    require(spec is not None and spec.loader is not None, "legacy frozen bridge cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    after, _ = stable_read(root, LEGACY_BRIDGE_REF, "legacy frozen bridge after import")
    require(raw == after, "legacy frozen bridge changed during import")
    _LEGACY_MODULE_CACHE[key] = module
    return module


def load_dependencies(root: Path | str, *, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False) -> dict[str, Any]:
    """Expose the exact legacy nested modules for migration call sites."""
    if fixture_only:
        require(fixture_modules is not None, "fixture-only dependencies need modules")
        return dict(fixture_modules)
    legacy = _legacy_bridge(Path(root).resolve())
    loader = getattr(legacy, "load_dependencies", None)
    require(callable(loader), "pinned legacy bridge lacks load_dependencies")
    modules = loader(Path(root).resolve())
    require(isinstance(modules, Mapping), "legacy bridge returned no module graph")
    return dict(modules)


def load_and_validate(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                      ledger_bytes: bytes | None = None, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False, _runtime_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run the pinned frozen validator once; no caller-supplied result is accepted."""
    legacy = _legacy_bridge(Path(root).resolve())
    loader = getattr(legacy, "load_and_validate", None)
    require(callable(loader), "pinned legacy bridge lacks load_and_validate")
    return loader(Path(root).resolve(), core, mode=mode, ledger_bytes=ledger_bytes,
                  fixture_modules=fixture_modules, fixture_only=fixture_only,
                  _runtime_sink=_runtime_sink)


@dataclasses.dataclass(frozen=True)
class ActualRuntimeContext:
    """Opaque in-process result retained by one parent/child stage.

    The diagnostic is useful for audit receipts, but no consumer is allowed
    to reconstruct runtime authority from it.  The graph and module mapping
    retain the exact objects used by the validation call.
    """

    root: Path
    mode: str
    graph: PinnedBridgeGraph
    modules: Mapping[str, object]
    diagnostic: Mapping[str, Any]
    objects: Mapping[str, object] = dataclasses.field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        require(tuple(self.modules) == REQUIRED_GRAPH_NAMES,
                "opaque runtime graph is incomplete")
        self.graph.assert_complete(self.modules)
        if self.objects:
            object_modules = self.objects.get("modules")
            # Historical bridge consumers expose the complete graph mapping.
            # The BF14 stage adapter additionally exposes the four frozen
            # checker roles under their legacy names while retaining the full
            # graph separately on ``self.modules``.  Both mappings must point
            # at the exact graph objects; neither may be reconstructed from
            # the compact diagnostic.
            if object_modules is not self.modules:
                require(isinstance(object_modules, Mapping) and
                        tuple(object_modules) == ("replacement05", "executor", "checker", "configuration"),
                        "runtime object map does not retain a recognized module mapping")
                require(object_modules["replacement05"] is _replacement_runtime_member(self.graph) and
                        object_modules["executor"] is self.graph.module("executor") and
                        object_modules["checker"] is self.graph.module("checker") and
                        object_modules["configuration"] is self.graph.module("configuration"),
                        "runtime object map contains foreign module instances")

    def __getstate__(self) -> None:
        raise FrozenBridge09Error("runtime context is opaque and cannot be serialized")


def _graph_runtime_context(root: Path, core: Mapping[str, Any], graph: PinnedBridgeGraph,
                           *, mode: str, ledger_bytes: bytes | None) -> ActualRuntimeContext:
    """Run the copied complete bridge08 validator through the pinned graph.

    Production requires stage_runtime01, which retains every historical,
    source, contract, capture and resource check and returns live objects.
    The small provider branch below is restricted to temporary fixture graphs.
    """
    require(mode in {"before", "after"}, "runtime validation mode is unknown")

    # The successor graph owns the complete frozen bridge adapter.  Keep this
    # dispatch here, rather than importing the successor by path: the graph
    # member was hash-checked and (for the parent process) is the exact module
    # object already executing the supervisor.  The adapter returns the
    # lossless v092 runtime mapping used by the frozen checker/configuration;
    # this wrapper only turns it into the bridge09 opaque holder.
    stage_loader = graph.module("stage_runtime01") if "stage_runtime01" in tuple(
        member.name for member in graph.members
    ) else None
    if stage_loader is not None:
        loader = getattr(stage_loader, "load_runtime_context", None)
        require(callable(loader), "stage-runtime graph member lacks load_runtime_context")
        value = loader(root, core, graph=graph, mode=mode, ledger_bytes=ledger_bytes)
        require(isinstance(value, Mapping), "stage-runtime provider returned no runtime mapping")
        require(value.get("schema") == "v092-bifrost-v0140-runtime-context/v1" and
                value.get("lossless_runtime_objects") is True,
                "stage-runtime provider returned an unreviewed runtime schema")
        runtime_modules = value.get("modules")
        require(isinstance(runtime_modules, Mapping) and
                tuple(runtime_modules) == ("replacement05", "executor", "checker", "configuration"),
                "stage-runtime module roster is not the frozen lossless roster")
        # The full replacement05 validator is a distinct pinned graph member;
        # the replacement14 packet protocol cannot substitute for it.
        require(runtime_modules["replacement05"] is _replacement_runtime_member(graph),
                "stage-runtime replacement object is not the pinned full bridge member")
        for name in ("executor", "checker", "configuration"):
            require(runtime_modules[name] is graph.module(name),
                    f"stage-runtime returned a foreign {name} object")
        bridge_context = value.get("bridge_context")
        require(isinstance(bridge_context, Mapping) and
                isinstance(bridge_context.get("context_digest"), str) and
                len(bridge_context["context_digest"]) == 64,
                "stage-runtime bridge context has no stable digest")
        graph_modules = {name: graph.module(name) for name in REQUIRED_GRAPH_NAMES}
        objects = dict(value)
        manifest_path = core.get("manifest_path")
        require(isinstance(manifest_path, str), "stage core lacks the exact manifest path")
        static = graph.module("protocol14").validate_static(root, manifest_path)
        require(isinstance(static, Mapping) and static.get("core") == core,
                "stage protocol static core differs from the actual runtime core")
        objects["protocol_static"] = static
        diagnostic = dict(bridge_context)
        diagnostic.setdefault("schema", "v092-bifrost-v0140-runtime-context-diagnostic/v1")
        diagnostic.setdefault("graph_sha256", graph.graph_sha256)
        return ActualRuntimeContext(root=root, mode=mode, graph=graph,
                                    modules=graph_modules, diagnostic=diagnostic,
                                    objects=objects)

    require(graph.fixture_only, "production graph omits the complete stage-runtime validator")
    replacement = graph.module("replacement14")
    executor = graph.module("executor")
    require(callable(getattr(replacement, "validate_static", None)),
            "replacement14 has no reviewed static validator")
    manifest_value = core.get("manifest_ref", core.get("manifest_path"))
    if isinstance(manifest_value, Mapping):
        manifest_path = manifest_value.get("path")
    else:
        manifest_path = manifest_value
    require(isinstance(manifest_path, str), "core has no reviewed manifest path")
    static = replacement.validate_static(root, manifest_path)
    require(isinstance(static, Mapping) and isinstance(static.get("core"), Mapping),
            "replacement14 returned no validated core")
    canonical_core = static["core"]
    contract_value = canonical_core.get("contract")
    require(isinstance(contract_value, Mapping), "validated core has no contract ref")
    contract_ref = _ref(contract_value, "validated contract")
    contract_path = _path(root, contract_ref["path"], "validated contract path")
    validate_plan = getattr(executor, "validate_plan", None)
    require(callable(validate_plan), "frozen executor has no validate_plan")
    try:
        validated = validate_plan(contract_path, repo_root=root)
    except TypeError:
        # Older frozen executors use the path plus a positional checkout root;
        # this fallback is signature-bound and does not catch validator errors.
        validated = validate_plan(contract_path, root)
    require(isinstance(validated, Mapping), "frozen executor returned no normalized plan")
    require(validated.get("bytes_sha256") == contract_ref["sha256"],
            "frozen executor normalized a different contract")
    modules = {name: graph.module(name) for name in REQUIRED_GRAPH_NAMES}
    # Full checker/configuration replay is supplied by one graph-owned
    # incoming-recovery provider.  The provider is itself pinned in the graph;
    # accepting a caller callback here would permit a serialized or foreign
    # context to masquerade as the actual replay result.  Providers may load a
    # fresh dependency graph for a changed ledger, but the returned module
    # objects must be members of this graph (or the provider must fail closed).
    provider = graph.module("incoming_recovery")
    provider_loader = getattr(provider, "load_runtime_context", None)
    require(callable(provider_loader),
            "pinned incoming-recovery graph member lacks the complete runtime provider")
    provider_kwargs: dict[str, Any] = {"mode": mode, "core": core, "graph": graph,
                                      "root": root, "ledger_bytes": ledger_bytes}
    provider_params = inspect.signature(provider_loader).parameters
    accepts_kwargs = any(parameter.kind is inspect.Parameter.VAR_KEYWORD
                         for parameter in provider_params.values())
    if not accepts_kwargs:
        provider_kwargs = {key: value for key, value in provider_kwargs.items() if key in provider_params}
    provided = provider_loader(**provider_kwargs)
    require(isinstance(provided, Mapping), "incoming-recovery provider returned no runtime mapping")
    required_runtime = {"modules", "validated", "mixed_context", "checker_summary",
                        "configuration_summary", "bridge_context"}
    require(required_runtime <= set(provided),
            "incoming-recovery provider returned an incomplete runtime mapping")
    provider_modules = provided["modules"]
    require(isinstance(provider_modules, Mapping), "incoming-recovery runtime module mapping is malformed")
    for name, module in provider_modules.items():
        graph_name = name
        # replacement05 is the historical public name used by the frozen
        # checker.  A successor graph may expose the same object under its
        # replacement14 role, but it may never silently import a second copy.
        if name == "replacement05":
            expected = _replacement_runtime_member(graph)
            require(expected is module,
                    "runtime provider returned a foreign replacement05 module")
            continue
        require(graph_name in modules and modules[graph_name] is module,
                f"runtime provider returned a foreign module: {name}")
    require(isinstance(provided["validated"], Mapping), "runtime provider normalized plan is malformed")
    require(isinstance(provided["mixed_context"], Mapping), "runtime provider mixed context is malformed")
    require(isinstance(provided["checker_summary"], Mapping), "runtime provider checker summary is malformed")
    require(isinstance(provided["configuration_summary"], Mapping),
            "runtime provider configuration summary is malformed")
    bridge_context = provided["bridge_context"]
    require(isinstance(bridge_context, Mapping), "runtime provider bridge context is malformed")
    diagnostic = {
        "schema": SCHEMA + "/graph-runtime",
        "status": "graph-owned-frozen-validation-passed",
        "execution_authorized": False,
        "mode": mode,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256(_path(root, manifest_path, "manifest").read_bytes()),
        "contract": contract_ref,
        "validated": validated,
        "ledger_bytes_sha256": None if ledger_bytes is None else sha256(ledger_bytes),
        "graph_sha256": graph.graph_sha256,
        "lossless_runtime_objects": True,
        "protocol_static": static,
        "bridge_context": bridge_context,
        "modules": modules,
        "mixed_context": provided["mixed_context"],
        "checker_summary": provided["checker_summary"],
        "configuration_summary": provided["configuration_summary"],
    }
    objects = {
        "protocol_static": static,
        "modules": modules,
        "validated": provided["validated"],
        "mixed_context": provided["mixed_context"],
        "checker_summary": provided["checker_summary"],
        "configuration_summary": provided["configuration_summary"],
        "bridge_context": bridge_context,
    }
    return ActualRuntimeContext(root=root, mode=mode, graph=graph,
                                modules=modules, diagnostic=diagnostic, objects=objects)


def load_runtime_context(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                         ledger_bytes: bytes | None = None, fixture_modules: Mapping[str, Any] | None = None,
                         fixture_only: bool = False,
                         graph: PinnedBridgeGraph | None = None) -> object:
    """Return one lossless opaque runtime context from the pinned graph.

    ``graph`` is mandatory for production stage construction.  The legacy
    bridge is used only as a pinned validator compatibility boundary while
    migration call sites are being moved; the returned object is wrapped in
    an opaque stage-local value and cannot be supplied as serialized JSON.
    """
    require(isinstance(graph, PinnedBridgeGraph),
            "runtime validation requires a pinned complete graph")
    graph.assert_member("bridge09", sys.modules.get(__name__))
    if fixture_only:
        require(fixture_modules is not None, "fixture-only runtime needs modules")
        # Fixture graph modules own their harmless runtime loader.  Production
        # never reaches this branch because fixture_only is rejected by the
        # graph boundary.
        fixture_loader = getattr(graph.module("bridge09"), "fixture_runtime_context", None)
        require(callable(fixture_loader), "fixture graph has no explicit runtime seam")
        return fixture_loader(mode=mode, core_identity=core, graph=graph)
    require(not fixture_modules, "production runtime cannot inject modules")
    return _graph_runtime_context(Path(root).resolve(), core, graph,
                                  mode=mode, ledger_bytes=ledger_bytes)


def validate_frozen_bridge(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                           **kwargs: Any) -> dict[str, Any]:
    """Compatibility name used by admission's static bridge loader."""
    return load_and_validate(root, core, mode=mode, **kwargs)


def _make_identity(*, index: int, ledger_ref: StageRef, runtime: object, source_commit: str,
                   plan_commit: str, contract_sha256: str, lock: LockIdentity,
                   ledger_rows: int,
                   analyzer_deadline_seconds: float, startup_seconds: float,
                   created_monotonic: float) -> StageIdentity:
    require(index >= 0, "stage index is negative")
    _validate_identity_fields(source_commit, plan_commit, contract_sha256)
    require(ledger_ref.stat.get("size", 0) > 0, "stage ledger is empty")
    rows = int(ledger_rows)
    require(rows > 0, "stage ledger rows are empty")
    return StageIdentity(index, ledger_ref.sha256, rows, runtime_digest(runtime), source_commit,
                         plan_commit, contract_sha256, lock, float(analyzer_deadline_seconds),
                         float(startup_seconds), float(created_monotonic))


def build_parent_stage(root: Path | str, *, index: int, ledger: Mapping[str, Any],
                       runtime: object, graph: PinnedBridgeGraph, source_commit: str,
                       plan_commit: str, contract_sha256: str, lock: LockIdentity,
                       sidecars: Mapping[str, Mapping[str, Any]], source_refs: Sequence[Mapping[str, Any]],
                       analyzer_deadline_seconds: float, startup_seconds: float = STARTUP_SECONDS,
                       created_monotonic: float | None = None,
                       live_ledger: Mapping[str, Any] | None = None) -> ParentStage:
    """Build one immutable parent stage after one full actual replay."""
    require(index < PARENT_STAGE_COUNT, "parent stage index exceeds the 21-state contract")
    root = Path(root).resolve()
    require(graph is not None and isinstance(runtime, object), "actual runtime graph/context are required")
    ledger_ref = _stage_ref(root, ledger, "stage ledger")
    require(type(ledger.get("rows")) is int and ledger["rows"] > 0, "stage ledger rows are required")
    inventory = [ledger_ref]
    for index_ref, source_ref in enumerate(source_refs):
        inventory.append(_stage_ref(root, source_ref, f"stage source closure {index_ref}"))
    refs: dict[str, StageRef] = {}
    for name, ref in sidecars.items():
        _relative(name, "sidecar key")
        refs[name] = _stage_ref(root, ref, f"stage sidecar {name}")
    identity = _make_identity(index=index, ledger_ref=ledger_ref, runtime=runtime, source_commit=source_commit,
                              plan_commit=plan_commit, contract_sha256=contract_sha256, lock=lock,
                              ledger_rows=int(ledger["rows"]),
                              analyzer_deadline_seconds=analyzer_deadline_seconds,
                              startup_seconds=startup_seconds,
                              created_monotonic=time.monotonic() if created_monotonic is None else created_monotonic)
    live_ref = None if live_ledger is None else _stage_ref(root, live_ledger, "live ledger witness")
    return ParentStage(identity, graph, runtime, inventory, refs, live_ledger=live_ref)


def assert_stage_current(root: Path | str, stage: ParentStage | SuccessorStageDraft | FinalizedParentStage,
                         graph: PinnedBridgeGraph | None = None) -> None:
    require(isinstance(stage, _OpaqueStage), "stage must be an opaque stage object")
    if graph is not None:
        stage.assert_graph(graph)
    for ref in stage.inventory:
        _current_ref(Path(root).resolve(), ref, f"stage inventory {ref.path}")
    for name, ref in stage.sidecars.items():
        _current_ref(Path(root).resolve(), ref, f"stage sidecar {name}")
    if stage.live_ledger is not None:
        _current_ref(Path(root).resolve(), stage.live_ledger, "stage live ledger witness")


def _assert_immutable_stage(root: Path | str, stage: ParentStage | FinalizedParentStage,
                            graph: PinnedBridgeGraph | None = None) -> None:
    """Validate the prior immutable snapshot while allowing its live ledger append."""
    require(isinstance(stage, _OpaqueStage), "stage must be an opaque stage object")
    if graph is not None:
        stage.assert_graph(graph)
    root = Path(root).resolve()
    for ref in stage.inventory:
        _current_ref(root, ref, f"stage inventory {ref.path}")
    for name, ref in stage.sidecars.items():
        _current_ref(root, ref, f"stage sidecar {name}")


def build_successor_stage(root: Path | str, *, predecessor: ParentStage | FinalizedParentStage,
                          index: int, ledger_after: Mapping[str, Any], runtime: object,
                          graph: PinnedBridgeGraph, source_commit: str, plan_commit: str,
                          contract_sha256: str, sidecars: Mapping[str, Mapping[str, Any]],
                          source_refs: Sequence[Mapping[str, Any]],
                          analyzer_deadline_seconds: float, startup_seconds: float = STARTUP_SECONDS,
                          created_monotonic: float | None = None,
                          live_ledger: Mapping[str, Any] | None = None) -> SuccessorStageDraft:
    require(index == predecessor.identity.index + 1, "successor stage is not the immediate next state")
    require(index < PARENT_STAGE_COUNT, "successor index exceeds the 21-state contract")
    _assert_immutable_stage(root, predecessor, predecessor.graph)
    root = Path(root).resolve()
    after_ref = _stage_ref(root, ledger_after, "successor ledger")
    require(type(ledger_after.get("rows")) is int and ledger_after["rows"] == predecessor.identity.ledger_rows + 1,
            "successor must append exactly one ledger row")
    before_path = _path(root, predecessor.inventory[0].path, "predecessor ledger")
    after_path = _path(root, after_ref.path, "successor ledger")
    before_raw = before_path.read_bytes()
    after_raw = after_path.read_bytes()
    require(after_raw.startswith(before_raw), "successor ledger is not the predecessor prefix")
    tail = after_raw[len(before_raw):]
    require(tail.count(b"\n") == 1 and tail.endswith(b"\n"), "successor ledger appends one complete row")
    if live_ledger is not None:
        live_raw, _ = stable_read(root, live_ledger, "successor live ledger witness")
        require(live_raw == after_raw,
                "successor live ledger witness is not the exact successor bytes")
    inventory = [after_ref]
    for n, ref in enumerate(source_refs):
        inventory.append(_stage_ref(root, ref, f"successor source closure {n}"))
    # A successor is an immutable extension of its predecessor.  Existing
    # admission/phase/permit/ledger sidecars remain part of the stage
    # inventory; a caller may only add new deterministic names or repeat the
    # exact same binding.  Silently replacing or dropping prior evidence would
    # make the compact stage receipt unable to account for the full history.
    refs = dict(predecessor.sidecars)
    for name, ref in sidecars.items():
        _relative(name, "successor sidecar key")
        current = refs.get(name)
        checked = _stage_ref(root, ref, f"successor sidecar {name}")
        if current is not None:
            require(current.path == checked.path and current.sha256 == checked.sha256,
                    f"successor attempts to replace prior sidecar: {name}")
        refs[name] = checked
    ledger_ref = after_ref
    identity = _make_identity(index=index, ledger_ref=ledger_ref, runtime=runtime, source_commit=source_commit,
                              plan_commit=plan_commit, contract_sha256=contract_sha256, lock=predecessor.identity.lock,
                              ledger_rows=int(ledger_after["rows"]),
                              analyzer_deadline_seconds=analyzer_deadline_seconds,
                              startup_seconds=startup_seconds,
                              created_monotonic=time.monotonic() if created_monotonic is None else created_monotonic)
    draft = SuccessorStageDraft(identity, graph, runtime, inventory, refs,
                                predecessor_identity_sha256=predecessor.identity_sha256,
                                ledger_before_sha256=predecessor.identity.ledger_sha256,
                                live_ledger=None if live_ledger is None else _stage_ref(
                                    root, live_ledger, "successor live ledger witness"))
    return draft


def write_completion(root: Path | str, *, predecessor: ParentStage | FinalizedParentStage,
                     successor: SuccessorStageDraft, completion_path: str,
                     completion: Mapping[str, Any], expected_group_id: str,
                     expected_attempt_id: str, graph: PinnedBridgeGraph) -> FinalizedParentStage:
    """Write one completion sidecar and return a new immutable successor stage."""
    require(successor.predecessor_identity_sha256 == predecessor.identity_sha256,
            "completion predecessor/successor identity mismatch")
    predecessor.assert_graph(graph)
    successor.assert_graph(graph)
    require(completion.get("group_id") == expected_group_id and completion.get("attempt_id") == expected_attempt_id,
            "completion group/attempt does not match the transition")
    root = Path(root).resolve()
    _relative(completion_path, "completion path")
    target = _path(root, completion_path, "completion path")
    raw = canonical_json(dict(completion))
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise FrozenBridge09Error("completion sidecar already exists; retry is forbidden") from exc
    ref = {"path": completion_path, "sha256": sha256(raw)}
    completion_ref = _stage_ref(root, ref, "completion sidecar")
    sidecars = dict(successor.sidecars)
    require(completion_path not in sidecars, "completion path already appeared in successor draft")
    sidecars[completion_path] = completion_ref
    return FinalizedParentStage(successor.identity, successor.graph, successor.runtime, successor.inventory,
                                sidecars, live_ledger=successor.live_ledger,
                                predecessor_identity_sha256=predecessor.identity_sha256)


def _read_compact_parent(root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    """Read and validate a compact parent receipt without rebuilding runtime."""
    require(set(value) == {"path", "sha256"}, "parent receipt ref has unexpected fields")
    raw, _ = stable_read(root, value, "parent stage receipt")
    try:
        receipt = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrozenBridge09Error("parent stage receipt is not JSON") from exc
    require(isinstance(receipt, Mapping) and
            receipt.get("schema") == SCHEMA + "/stage-receipt",
            "parent receipt schema is not the reviewed compact stage schema")
    required = {"stage_identity", "stage_identity_sha256", "ledger_ref", "graph_members",
                "graph_sha256", "source_commit", "plan_commit", "contract_sha256",
                "lock", "manifest_ref", "core_identity"}
    require(required <= set(receipt), "parent receipt omits a stable binding")
    require(receipt["stage_identity_sha256"] == sha256(canonical_json(receipt["stage_identity"])),
            "parent receipt identity digest is not canonical")
    require(isinstance(receipt["graph_members"], list) and receipt["graph_members"],
            "parent receipt graph binding is empty")
    graph_bindings = []
    for item in receipt["graph_members"]:
        require(isinstance(item, Mapping) and
                set(item) == {"name", "canonical_path", "source_sha256", "loader_identity"},
                "parent receipt graph member is malformed")
        graph_bindings.append({"name": item["name"], "canonical_path": item["canonical_path"],
                               "source_sha256": item["source_sha256"]})
    require(receipt.get("graph_bindings") == graph_bindings,
            "parent receipt graph bindings differ from its public members")
    require(receipt.get("graph_sha256") == sha256(canonical_json(graph_bindings)),
            "parent receipt graph digest is not bound to its members")
    require(isinstance(receipt["ledger_ref"], Mapping), "parent receipt ledger ref is malformed")
    ledger_ref = _ref(receipt["ledger_ref"], "parent receipt ledger")
    stage_identity = receipt["stage_identity"]
    require(isinstance(stage_identity, Mapping) and
            ledger_ref["sha256"] == stage_identity.get("ledger_sha256") and
            ledger_ref.get("rows", stage_identity.get("ledger_rows")) == stage_identity.get("ledger_rows"),
            "parent receipt ledger is not bound to its stage identity")
    return dict(receipt)


def lock_identity_matches(actual: LockIdentity, expected: LockIdentity) -> bool:
    return actual == expected


def build_child_stage(root: Path | str, *,
                      parent: ParentStage | FinalizedParentStage | None = None,
                      parent_binding: Mapping[str, Any] | None = None,
                      runtime: object, graph: PinnedBridgeGraph, source_refs: Sequence[Mapping[str, Any]],
                      child_creator_pid: int, child_creator_birth: str, child_pid: int, child_birth: str,
                      analyzer_deadline_seconds: float, popen_monotonic: float,
                      sidecars: Mapping[str, Mapping[str, Any]], ledger: Mapping[str, Any],
                      live_ledger: Mapping[str, Any] | None = None,
                      lock_identity: LockIdentity | None = None) -> ChildStage:
    if parent is not None:
        require(isinstance(parent, _OpaqueStage), "child stage needs parent stage")
        parent.assert_graph(parent.graph)
        parent_identity_sha = parent.identity_sha256
        parent_graph_binding = tuple(member.binding() for member in parent.graph.members)
        parent_identity = parent.identity
    else:
        require(isinstance(parent_binding, Mapping),
                "child stage needs a validated compact parent binding")
        parent_identity_sha = parent_binding.get("stage_identity_sha256")
        _sha(parent_identity_sha, "parent stage identity sha256")
        members = parent_binding.get("graph_members")
        require(isinstance(members, list), "compact parent graph members are malformed")
        parent_graph_binding = tuple({"name": item.get("name"),
                                      "canonical_path": item.get("canonical_path"),
                                      "source_sha256": item.get("source_sha256")}
                                     for item in members if isinstance(item, Mapping))
        identity_value = parent_binding.get("stage_identity")
        require(isinstance(identity_value, Mapping), "compact parent identity is malformed")
        lock_value = parent_binding.get("lock")
        require(isinstance(lock_value, Mapping), "compact parent lock is malformed")
        parent_identity = StageIdentity(
            index=identity_value.get("index"),
            ledger_sha256=identity_value.get("ledger_sha256"),
            ledger_rows=identity_value.get("ledger_rows"),
            runtime_sha256=identity_value.get("runtime_sha256"),
            source_commit=parent_binding.get("source_commit"),
            plan_commit=parent_binding.get("plan_commit"),
            contract_sha256=parent_binding.get("contract_sha256"),
            lock=LockIdentity(**dict(lock_value)),
            analyzer_deadline_seconds=identity_value.get("analyzer_deadline_seconds"),
            startup_seconds=identity_value.get("startup_seconds"),
            created_monotonic=identity_value.get("created_monotonic"),
        )
        require(parent_identity.digest() == parent_identity_sha,
                "compact parent identity fields do not match its digest")
    if lock_identity is None:
        lock_identity = parent_identity.lock
    require(lock_identity_matches(lock_identity, parent_identity.lock),
            "child lock identity differs from the parent permit")
    lease = Lease(float(popen_monotonic), float(analyzer_deadline_seconds), STARTUP_SECONDS)
    require(lease.setup_remaining(float(popen_monotonic)) == analyzer_deadline_seconds + STARTUP_SECONDS,
            "child lease start is not the actual Popen time")
    # The child graph is intentionally a fresh graph for a separate process,
    # but its public path/SHA tuple must equal the parent graph tuple.
    require(tuple(member.binding() for member in graph.members) == parent_graph_binding,
            "child graph path/SHA tuple differs from parent stage")
    root = Path(root).resolve()
    ledger_ref = _stage_ref(root, ledger, "child ledger")
    require(ledger_ref.sha256 == parent_identity.ledger_sha256, "child stage ledger differs from ready parent")
    inventory = [ledger_ref]
    for n, ref in enumerate(source_refs):
        inventory.append(_stage_ref(root, ref, f"child source closure {n}"))
    refs = {name: _stage_ref(root, ref, f"child sidecar {name}") for name, ref in sidecars.items()}
    identity = dataclasses.replace(parent_identity, runtime_sha256=runtime_digest(runtime),
                                   created_monotonic=float(popen_monotonic), lock=lock_identity)
    return ChildStage(identity, graph, runtime, inventory, refs,
                      live_ledger=None if live_ledger is None else _stage_ref(
                          root, live_ledger, "child live ledger witness"),
                      parent_identity_sha256=parent_identity_sha,
                      child_creator_pid=child_creator_pid, child_creator_birth=child_creator_birth,
                      child_pid=child_pid, child_birth=child_birth, lease=lease)


def assert_child_ready(root: Path | str, child: ChildStage, *, parent: ParentStage | FinalizedParentStage,
                       graph: PinnedBridgeGraph, now_monotonic: float) -> float:
    require(child.parent_identity_sha256 == parent.identity_sha256, "child parent identity differs")
    child.assert_graph(graph)
    assert_stage_current(root, parent, parent.graph)
    assert_stage_current(root, child, graph)
    remaining = child.lease.setup_remaining(now_monotonic)
    require(remaining > 0, "child startup lease expired")
    return remaining


def write_compact_stage_receipt(root: Path | str, path: str, stage: _OpaqueStage,
                                *, status: str, sidecar_names: Sequence[str],
                                manifest_ref: Mapping[str, Any] | None = None,
                                core_identity: Mapping[str, Any] | None = None) -> dict[str, str]:
    require(status in {"parent-stage-verified", "child-stage-verified", "successor-stage-verified"},
            "unknown stage receipt status")
    require(tuple(sidecar_names) == tuple(sorted(set(sidecar_names))), "stage sidecars are not deterministic")
    require(isinstance(manifest_ref, Mapping) and isinstance(core_identity, Mapping),
            "compact stage receipt needs exact manifest and core bindings")
    require(set(manifest_ref) == {"path", "sha256"}, "manifest receipt binding has unexpected fields")
    _sha(manifest_ref.get("sha256"), "manifest receipt sha256")
    _relative(manifest_ref.get("path"), "manifest receipt path")
    stage_identity = dataclasses.asdict(stage.identity)
    stage_identity["lock"] = dataclasses.asdict(stage.identity.lock)
    value = {"schema": SCHEMA + "/stage-receipt", "status": status,
             "stage_index": stage.identity.index, "stage_identity_sha256": stage.identity_sha256,
             "stage_identity": stage_identity,
             "ledger_sha256": stage.identity.ledger_sha256, "ledger_rows": stage.identity.ledger_rows,
             "runtime_sha256": stage.identity.runtime_sha256,
             "graph_sha256": stage.graph.graph_sha256,
             "graph_members": [member.public() for member in stage.graph.members],
             "graph_bindings": [member.binding() for member in stage.graph.members],
             "source_commit": stage.identity.source_commit,
             "plan_commit": stage.identity.plan_commit,
             "contract_sha256": stage.identity.contract_sha256,
             "lock": dataclasses.asdict(stage.identity.lock),
             "ledger_ref": stage.inventory[0].as_dict(),
             "live_ledger_ref": None if stage.live_ledger is None else stage.live_ledger.as_dict(),
             "manifest_ref": dict(manifest_ref), "core_identity": dict(core_identity),
             "sidecars": list(sidecar_names)}
    root = Path(root).resolve()
    target = _path(root, path, "stage receipt path")
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(value)
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise FrozenBridge09Error("stage receipt already exists; retry is forbidden") from exc
    return {"path": path, "sha256": sha256(raw)}


def validate_sidecar_transition(*, allowed: Iterable[str], present: Iterable[str],
                                future: Iterable[str] = (), required: Iterable[str] = ()) -> None:
    allowed_set, present_set, future_set, required_set = set(allowed), set(present), set(future), set(required)
    require(required_set <= allowed_set, "required sidecar is outside deterministic allowlist")
    require(not future_set - allowed_set, "future sidecar is outside deterministic allowlist")
    require(present_set <= allowed_set, "unexpected sidecar in stage inventory")
    require(required_set <= present_set, "required sidecar is missing")
    require(not future_set & present_set, "future sidecar is already present")


def validate_resource_sample(sample: ResourceSample, *, free_floor: int, working_cap: int,
                             scratch_cap: int, retention_cap: int) -> None:
    require(sample.satisfies(free_floor=free_floor, working_cap=working_cap,
                             scratch_cap=scratch_cap, retention_cap=retention_cap),
            "fresh resource sample violates unchanged guard")


def validate_lease_progress(lease: Lease, *, now_monotonic: float, registered_deadline_seconds: float) -> float:
    require(lease.registered_deadline_seconds == registered_deadline_seconds,
            "registered analyzer deadline changed")
    remaining = lease.setup_remaining(now_monotonic)
    require(remaining > 0, "registered startup lease expired")
    return remaining


def build_parent_sequence(root: Path | str, stage_specs: Sequence[Mapping[str, Any]]) -> list[ParentStage]:
    """Materialize the 21 parent states from already verified actual inputs.

    ``stage_specs`` contains the runtime object and complete pinned graph
    returned by one actual replay per state.  This function does not call a
    loader, reload a bridge, or manufacture a context from a receipt.
    """
    require(len(stage_specs) == PARENT_STAGE_COUNT, "exactly 21 parent stage inputs are required")
    stages: list[ParentStage] = []
    for index, spec in enumerate(stage_specs):
        required = {"ledger", "runtime", "graph", "source_commit", "plan_commit", "contract_sha256",
                    "lock", "sidecars", "source_refs", "analyzer_deadline_seconds"}
        require(required <= set(spec), f"parent stage {index} is missing typed actual inputs")
        stage = build_parent_stage(root, index=index, **dict(spec))
        if stages:
            require(stage.identity.ledger_rows == stages[-1].identity.ledger_rows + 1,
                    f"parent stage {index} did not append one terminal row")
            require(stage.identity.lock == stages[-1].identity.lock,
                    f"parent stage {index} changed the canonical lock identity")
        stages.append(stage)
    return stages


def build_child_sequence(root: Path | str, child_specs: Sequence[Mapping[str, Any]],
                         parent_stages: Sequence[ParentStage | FinalizedParentStage]) -> list[ChildStage]:
    """Build exactly one fresh child runtime stage after each ready phase."""
    require(len(child_specs) == CHILD_STAGE_COUNT and len(parent_stages) == PARENT_STAGE_COUNT,
            "BF14 child/parent cardinalities are not exact")
    children: list[ChildStage] = []
    for index, spec in enumerate(child_specs):
        require(spec.get("parent") is parent_stages[index],
                f"child stage {index} is not bound to its parent stage")
        child = build_child_stage(root, **dict(spec))
        require(child.identity.index == index, f"child stage {index} has a non-deterministic index")
        children.append(child)
    return children


def load_runtime_stage(root: Path | str, *, graph: PinnedBridgeGraph, runtime_loader: Any,
                       mode: str, core_identity: Mapping[str, Any],
                       ledger_bytes: bytes | None = None) -> tuple[object, str]:
    """Invoke one graph-owned runtime loader exactly once and retain its object.

    A caller cannot supply an arbitrary callback.  The callable must be the
    ``load_runtime_context`` export of one of the graph's pinned modules; the
    graph object is the authority for both the source bytes and the module
    identity.  The helper below is preferred by production callers.
    """
    require(not isinstance(runtime_loader, (str, bytes, Mapping)) and callable(runtime_loader),
            "runtime loader must be a graph-owned callable")
    owner_names = []
    for member in graph.members:
        candidate = getattr(member.module_object, "load_runtime_context", None)
        if candidate is not None and getattr(candidate, "__self__", None) is getattr(runtime_loader, "__self__", None) \
                and getattr(candidate, "__func__", candidate) is getattr(runtime_loader, "__func__", runtime_loader):
            owner_names.append(member.name)
    require(len(owner_names) == 1, "runtime loader is not the pinned graph loader")
    parameters = inspect.signature(runtime_loader).parameters
    kwargs: dict[str, Any] = {"mode": mode, "graph": graph}
    if "core" in parameters:
        kwargs["core"] = core_identity
    else:
        require(graph.fixture_only and "core_identity" in parameters,
                "production runtime loader lacks the exact core argument")
        kwargs["core_identity"] = core_identity
    if "ledger_bytes" in parameters:
        kwargs["ledger_bytes"] = ledger_bytes
    else:
        require(graph.fixture_only and ledger_bytes is None,
                "production runtime loader lacks the exact ledger argument")
    # Fixture loaders intentionally have a small signature.  The production
    # bridge loader accepts the root so it can bind every reviewed input from
    # the same checkout; inspect only the already graph-owned callable and do
    # not catch arbitrary TypeErrors from inside it.
    if "root" in parameters:
        kwargs["root"] = Path(root).resolve()
    runtime = runtime_loader(**kwargs)
    require(runtime is not None and not isinstance(runtime, (str, bytes, Mapping)),
            "runtime loader returned a serialized or missing context")
    return runtime, runtime_digest(runtime)


def load_stage_runtime(root: Path | str, *, graph: PinnedBridgeGraph, mode: str,
                       core_identity: Mapping[str, Any],
                       ledger_bytes: bytes | None = None) -> tuple[object, str]:
    """Load a lossless runtime context through the pinned bridge member."""
    loader = getattr(graph.module("bridge09"), "load_runtime_context", None)
    require(callable(loader), "pinned bridge graph lacks load_runtime_context")
    return load_runtime_stage(root, graph=graph, runtime_loader=loader, mode=mode,
                              core_identity=core_identity, ledger_bytes=ledger_bytes)


def runtime_objects(stage: _OpaqueStage) -> object:
    """Return the exact in-process runtime object owned by ``stage``.

    This is intentionally not a JSON or mapping conversion.  Cross-process
    callers use the compact stage receipt and perform their own actual child
    validation; they cannot manufacture a runtime by passing receipt fields
    back into this function.
    """
    require(isinstance(stage, _OpaqueStage), "runtime_objects needs an opaque stage")
    return stage.runtime


def _core_graph_inputs(core: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    refs = core.get("runtime_module_graph", core.get("graph_refs", core.get("frozen_graph_refs")))
    require(isinstance(refs, Mapping), "core has no exact frozen graph refs")
    # JSON object order is not semantic: canonical serialization sorts its
    # keys. Reconstruct the fixed role order without dropping any sealed alias.
    require(all(isinstance(name, str) for name in refs), "graph has a non-string module name")
    require(set(REQUIRED_GRAPH_NAMES) <= set(refs), "graph omits a required runtime role")
    names = REQUIRED_GRAPH_NAMES + tuple(sorted(set(refs) - set(REQUIRED_GRAPH_NAMES)))
    _validate_graph_names(names)
    return {name: refs[name] for name in names}


def _core_source_refs(core: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    continuation = core.get("continuation")
    refs = core.get("source_refs", core.get("source_inputs"))
    if refs is None and isinstance(continuation, Mapping):
        refs = continuation.get("source_inputs")
    require(isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)),
            "core has no typed source closure")
    return refs


def _core_contract_sha(core: Mapping[str, Any]) -> str:
    value = core.get("contract_sha256")
    if value is None and isinstance(core.get("contract"), Mapping):
        value = core["contract"].get("sha256")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping) and isinstance(continuation.get("contract"), Mapping):
        value = continuation["contract"].get("sha256")
    _sha(value, "core contract sha256")
    return value


def _core_source_commit(core: Mapping[str, Any]) -> str:
    value = core.get("source_commit")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("source_commit")
    require(isinstance(value, str), "core source commit is missing")
    return value


def _core_plan_commit(core: Mapping[str, Any]) -> str:
    value = core.get("plan_commit")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("plan_commit")
    require(isinstance(value, str), "core plan commit is missing")
    return value


def _core_deadline(core: Mapping[str, Any]) -> float:
    value = core.get("analyzer_deadline_seconds")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("analyzer_deadline_seconds")
    if value is None and isinstance(core.get("resource_policy"), Mapping):
        value = core["resource_policy"].get("minimum_replacement_seconds")
    require(type(value) in {int, float} and value > 0, "core analyzer deadline is missing")
    return float(value)


def _core_startup(core: Mapping[str, Any]) -> float:
    value = core.get("startup_seconds")
    if value is None and isinstance(core.get("resource_policy"), Mapping):
        value = core["resource_policy"].get("startup_seconds")
    return STARTUP_SECONDS if value is None else float(value)


def _load_bound_ledger_runtime(root: Path, graph: PinnedBridgeGraph,
                              core: Mapping[str, Any], ledger_ref: Mapping[str, Any],
                              mode: str) -> object:
    """Validate precisely the immutable ledger claimed by the new stage."""
    raw, metadata = stable_read(root, ledger_ref, "runtime ledger snapshot")
    require(type(ledger_ref.get("rows")) is int and
            len(raw.splitlines()) == ledger_ref["rows"],
            "runtime ledger snapshot row count differs")
    runtime, _ = load_stage_runtime(root, graph=graph, mode=mode,
                                    core_identity=core, ledger_bytes=raw)
    require(isinstance(runtime, ActualRuntimeContext),
            "production ledger runtime is not the actual opaque context")
    context = runtime.objects.get("bridge_context")
    mixed = runtime.objects.get("mixed_context")
    require(isinstance(context, Mapping) and context.get("ledger_sha256") == ledger_ref["sha256"],
            "actual validator used a different ledger snapshot")
    require(isinstance(mixed, Mapping) and
            isinstance(mixed.get("rows"), list) and len(mixed["rows"]) == ledger_ref["rows"] and
            context.get("ledger_rows") == ledger_ref["rows"],
            "actual mixed runtime does not retain the exact ledger snapshot")
    require(stable_metadata(root, {**ledger_ref, "stat": metadata}, "runtime ledger snapshot") == metadata,
            "runtime ledger snapshot changed during validation")
    return runtime


def create_parent_stage(root: Path | str, core: Mapping[str, Any], manifest_ref: Mapping[str, Any],
                        index: int, lock_identity: LockIdentity, ledger_ref: Mapping[str, Any],
                        sidecars: Mapping[str, Mapping[str, Any]] | None = None,
                        predecessor: ParentStage | FinalizedParentStage | None = None,
                        host_modules: Mapping[str, object] | None = None,
                        mode: str = "before", graph: PinnedBridgeGraph | None = None
                        , live_ledger: Mapping[str, Any] | None = None
                        ) -> ParentStage | SuccessorStageDraft:
    """Create an actual parent stage through one pinned validation call.

    Host production callers pass the modules already executing the command;
    no duplicate import is allowed.  With a predecessor this is the single
    append-only successor transition: the same pinned graph is reused and a
    fresh graph-owned runtime is produced for the new immutable ledger.
    """
    root = Path(root).resolve()
    graph_refs = _core_graph_inputs(core)
    if graph is None:
        if predecessor is not None:
            graph = predecessor.graph
            if host_modules is not None:
                supplied = bind_graph(root, graph_refs, host_modules)
                require(tuple(m.binding() for m in supplied.members) ==
                        tuple(m.binding() for m in graph.members),
                        "successor host graph differs from predecessor graph")
        elif host_modules is None:
            graph = load_graph(root, graph_refs)
        else:
            graph = bind_graph(root, graph_refs, host_modules)
    elif predecessor is not None:
        predecessor.assert_graph(graph)
    stable_read(root, manifest_ref, "stage manifest")
    runtime = _load_bound_ledger_runtime(root, graph, core, ledger_ref, mode)
    if live_ledger is None and root == ROOT:
        live_ledger = {"path": "reports/releases/v0.9.2/ledger-v1.jsonl",
                       "sha256": ledger_ref["sha256"]}
    ledger = dict(ledger_ref)
    require(type(ledger.get("rows")) is int and ledger["rows"] > 0,
            "stage ledger ref needs a positive row count")
    source_refs = list(_core_source_refs(core))
    common = dict(root=root, index=index, runtime=runtime, graph=graph,
                  source_commit=_core_source_commit(core), plan_commit=_core_plan_commit(core),
                  contract_sha256=_core_contract_sha(core), lock=lock_identity,
                  sidecars={} if sidecars is None else sidecars, source_refs=source_refs,
                  analyzer_deadline_seconds=_core_deadline(core), startup_seconds=_core_startup(core),
                  live_ledger=live_ledger)
    if predecessor is None:
        return build_parent_stage(ledger=ledger, **common)
    return build_successor_stage(root, predecessor=predecessor, index=index, ledger_after=ledger,
                                 **{key: value for key, value in common.items()
                                    if key not in {"root", "index", "lock"}})


def create_child_stage(root: Path | str, core: Mapping[str, Any], manifest_ref: Mapping[str, Any],
                       parent_receipt_ref: ParentStage | FinalizedParentStage | Mapping[str, Any],
                       lock_identity: LockIdentity, lease: Lease,
                       child_identity: Mapping[str, Any], ledger_ref: Mapping[str, Any],
                       sidecars: Mapping[str, Mapping[str, Any]] | None = None,
                       host_modules: Mapping[str, object] | None = None,
                       mode: str = "after", graph: PinnedBridgeGraph | None = None,
                       live_ledger: Mapping[str, Any] | None = None) -> ChildStage:
    """Create a child stage with one fresh actual replay after its ready gate."""
    root = Path(root).resolve()
    parent_stage = parent_receipt_ref if isinstance(parent_receipt_ref, (ParentStage, FinalizedParentStage)) else None
    parent_binding = None if parent_stage is not None else _read_compact_parent(root, parent_receipt_ref)
    if parent_binding is not None:
        expected_core = core.get("core_identity", core.get("manifest_ref"))
        if expected_core is not None:
            require(parent_binding.get("core_identity") == expected_core,
                    "compact parent receipt belongs to another core")
        require(parent_binding.get("manifest_ref") == manifest_ref,
                "compact parent receipt belongs to another manifest")
    graph_refs = _core_graph_inputs(core)
    if graph is None:
        graph = load_graph(root, graph_refs) if host_modules is None else bind_graph(root, graph_refs, host_modules)
    stable_read(root, manifest_ref, "child manifest")
    runtime = _load_bound_ledger_runtime(root, graph, core, ledger_ref, mode)
    if live_ledger is None and root == ROOT:
        live_ledger = {"path": "reports/releases/v0.9.2/ledger-v1.jsonl",
                       "sha256": ledger_ref["sha256"]}
    require(lease.popen_monotonic >= 0, "child lease is malformed")
    require(isinstance(child_identity, Mapping), "child identity is malformed")
    required = {"creator_pid", "creator_birth", "pid", "birth"}
    require(set(child_identity) == required, "child identity fields are not exact")
    return build_child_stage(
        root, parent=parent_stage, parent_binding=parent_binding, runtime=runtime, graph=graph,
        source_refs=list(_core_source_refs(core)),
        child_creator_pid=child_identity["creator_pid"],
        child_creator_birth=child_identity["creator_birth"],
        child_pid=child_identity["pid"], child_birth=child_identity["birth"],
        analyzer_deadline_seconds=lease.registered_deadline_seconds,
        popen_monotonic=lease.popen_monotonic,
        sidecars={} if sidecars is None else sidecars, ledger=dict(ledger_ref),
        lock_identity=lock_identity, live_ledger=live_ledger)


@contextlib.contextmanager
def stage_scope(root: Path | str, stage: _OpaqueStage, graph: PinnedBridgeGraph) -> Any:
    """Yield the opaque stage only while its graph and files remain stable."""
    assert_stage_current(root, stage, graph)
    try:
        yield stage
    finally:
        # Re-checking metadata after a consumer is intentional.  It detects a
        # sidecar/source mutation even when the consumer raised an exception.
        assert_stage_current(root, stage, graph)


def execute(*args: Any, **kwargs: Any) -> None:
    raise FrozenBridge09Error("frozen bridge is validation-only; execution belongs to supervisor-14")


if __name__ == "__main__":
    raise SystemExit("frozen bridge 09 is a library; production execution is disabled")
