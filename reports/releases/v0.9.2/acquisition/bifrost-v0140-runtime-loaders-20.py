#!/usr/bin/env python3
"""Scoped graph-owned late loaders for the frozen BF16 executor.

This does not import helper source or replace process-global import machinery.
The executor's existing loader call sites (and their preceding checks) still
execute; their spec/module/exec operations resolve only graph-pinned modules.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
from pathlib import Path, PurePosixPath
import stat
import sys
import types


class RuntimeLoaders20Error(ValueError):
    pass


# Exact names and paths used by the immutable executor. Unknown late imports
# fail closed rather than silently escaping the graph.
LOADERS = {
    "v092_process_tracker": "scripts/swift_v2_scored_process.py",
    "v092_disk_guard_runtime": "scripts/v092_disk_guard.py",
    "v092_scoped_recovery_packet": "scripts/v092_scoped_recovery.py",
    "check_release_v092_scoped_replay": "scripts/check-release-v092.py",
    "v092_resource_recovery": "scripts/v092_resource_recovery.py",
    "check_release_v092_resource_replay": "scripts/check-release-v092.py",
}


# Exact executor loader edges in the reviewed complete graph. Callers pass this
# map explicitly; no source-path ordering can choose a module instance.
PRODUCTION_MODULE_NAMES = {
    "v092_process_tracker": "nested_024_v092_process_tracker",
    "v092_disk_guard_runtime": "nested_025_v092_disk_guard_runtime",
    "v092_scoped_recovery_packet": "nested_020_v092_scoped_recovery_packet",
    "check_release_v092_scoped_replay": "nested_022_check_release_v092_scoped_replay",
    "v092_resource_recovery": "nested_021_v092_resource_recovery",
    "check_release_v092_resource_replay": "nested_023_check_release_v092_resource_replay",
}


def require(value, message):
    if not value:
        raise RuntimeLoaders20Error(message)


def _source(root, member):
    relative = PurePosixPath(member.canonical_path)
    require(not relative.is_absolute() and relative.parts and
            all(x not in (".", "..") for x in relative.parts), "noncanonical graph source path")
    path = root.joinpath(*relative.parts)
    for ancestor in (path, *path.parents):
        if ancestor == root:
            break
        require(not ancestor.is_symlink(), "symlink in graph source path")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "graph source is not a regular file")
    data = path.read_bytes()
    after = path.lstat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(signature(before) == signature(after), "graph source changed during read")
    require(hashlib.sha256(data).hexdigest() == member.source_sha256, "graph source SHA mismatch")
    require(Path(member.module_object.__file__) == path, "graph module has foreign source identity")
    return path


class _PinnedSpec:
    def __init__(self, name, member, loader):
        self.name, self.member, self.loader = name, member, loader


class _PinnedUtil:
    def __init__(self, root, graph, original, module_names):
        self.root, self.graph, self.original = root, graph, original
        self.module_names = module_names
        self.specs = []

    def _check(self, spec):
        require(any(x is spec for x in self.specs), "foreign loader spec")
        self.graph.assert_member(spec.member.name, spec.member.module_object)
        _source(self.root, spec.member)
        return spec.member.module_object

    def spec_from_file_location(self, name, location, *args, **kwargs):
        require(not args and not kwargs, "unexpected frozen loader options")
        require(name in LOADERS, "unregistered frozen loader name")
        expected = self.root / LOADERS[name]
        require(Path(location) == expected, "frozen loader path differs from exact registered path")
        candidates = [m for m in self.graph.members if m.canonical_path == LOADERS[name]]
        require(candidates, "helper source absent from runtime graph")
        require(len({m.source_sha256 for m in candidates}) == 1, "conflicting helper source aliases")
        selected_name = self.module_names.get(name)
        if selected_name is not None:
            candidates = [m for m in candidates if m.name == selected_name]
            require(len(candidates) == 1, "requested helper graph member differs")
        else:
            require(len(candidates) == 1,
                    "ambiguous helper graph aliases require explicit module selection")
        member, = candidates
        spec = _PinnedSpec(name, member, self)
        self.specs.append(spec)
        self._check(spec)
        return spec

    def module_from_spec(self, spec):
        return self._check(spec)

    def exec_module(self, module):
        candidates = [s for s in self.specs if s.member.module_object is module]
        require(candidates, "foreign module passed to pinned loader")
        self._check(candidates[-1])

    def __getattr__(self, name):
        # No other util API is used by the frozen executor. In particular never
        # expose find_spec or a fallback import path through this scope.
        raise RuntimeLoaders20Error("unregistered importlib.util operation: " + name)


@contextmanager
def scoped_runtime_loaders(root, *, executor, graph, module_names=None):
    """Scope actual executor late imports to this stage's exact module graph.

    ``module_names`` optionally chooses an exact graph role for a frozen loader
    name when one source occurs as multiple module instances; an ambiguous
    source without an explicit selection fails closed. The scope itself
    must be pinned as graph role ``runtime_loaders20``. No global hooks or
    process-wide module cache are changed. Nested scopes on one executor fail.
    """
    root = Path(root)
    require(root.is_absolute() and root == root.resolve(), "checkout root is not canonical")
    graph.assert_member("runtime_loaders20", sys.modules[__name__])
    graph.assert_member("executor", executor)
    executor_members = [m for m in graph.members if m.name == "executor"]
    require(len(executor_members) == 1 and executor_members[0].canonical_path == "scripts/execute-release-v092.py",
            "executor graph path differs")
    _source(root, executor_members[0])
    names = dict(module_names or {})
    require(all(name in LOADERS and isinstance(role, str) for name, role in names.items()),
            "invalid explicit loader member selection")
    original = executor.importlib
    require(not getattr(original, "_bf16_scoped", False), "executor loader scope already active")
    util = _PinnedUtil(root, graph, original.util, names)
    # Require these two actual late dependencies before any attempt can start.
    for name in ("v092_process_tracker", "v092_disk_guard_runtime"):
        util.spec_from_file_location(name, root / LOADERS[name])
    facade = types.SimpleNamespace(util=util, _bf16_scoped=True)
    executor.importlib = facade
    try:
        yield
    finally:
        unchanged = executor.importlib is facade
        executor.importlib = original
        require(unchanged, "executor import binding changed inside loader scope")
