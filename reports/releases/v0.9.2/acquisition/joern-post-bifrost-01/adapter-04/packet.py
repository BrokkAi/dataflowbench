"""Private artifact binding and immutable inherited-module loading only."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
CORE_PATH = 'reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-24/manifest-identity.json'
CORE_SHA = 'b1b405d1f28bae9b84632de4830352ae9a27f352f47bbb49a3a046e2567add6d'
HISTORY_RELATIVE_PATH = 'reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history_provider_02.py'
HISTORY_PATH = str(ROOT / HISTORY_RELATIVE_PATH)
HISTORY_SHA = 'da691ca16a4d1169e1f32d3524fb146bc4e60722dd99ea12bb9e03ac38436a8b'
HISTORY_REF = {'path': HISTORY_RELATIVE_PATH, 'sha256': HISTORY_SHA}

class AdapterError(ValueError):
    pass

def require(value: Any, message: str) -> None:
    if not value:
        raise AdapterError(message)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()

def read_ref(root: Path, ref: dict[str, str]) -> bytes:
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'exact artifact ref required')
    value = ref['path']
    require(isinstance(value, str) and value and ('\\' not in value), 'artifact path invalid')
    relative = Path(value)
    require(not relative.is_absolute() and relative.as_posix() == value and ('..' not in relative.parts), 'canonical relative artifact path required')
    path = root / relative
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'artifact symlink forbidden')
    before = path.stat()
    require(path.is_file() and before.st_size <= 256 * 1024 ** 2, 'artifact must be bounded regular file')
    raw = path.read_bytes()
    after = path.stat()
    signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    require(signature(before) == signature(after), 'artifact changed during read')
    require(digest(raw) == ref['sha256'], 'artifact SHA differs')
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'artifact path changed to symlink')
    return raw

def document(root: Path, ref: dict[str, str]) -> dict[str, Any]:
    value = json.loads(read_ref(root, ref))
    require(isinstance(value, dict), 'artifact JSON must be object')
    return value

def inherited_core(root: Path) -> dict[str, Any]:
    return document(root, {'path': CORE_PATH, 'sha256': CORE_SHA})

def load_bound_module(root: Path, name: str, ref: dict[str, str]) -> Any:
    raw = read_ref(root, ref)
    require(name not in sys.modules, 'module name already registered')
    path = root / ref['path']
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None, 'no module spec')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), 'exec'), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module

def load_history_reader() -> Any:
    raw = Path(HISTORY_PATH).read_bytes()
    require(digest(raw) == HISTORY_SHA, 'history candidate changed')
    name = '_private_joern05_history02'
    if name in sys.modules:
        require(sys.modules[name].__file__ == HISTORY_PATH, 'history module owner differs')
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HISTORY_PATH)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, HISTORY_PATH, 'exec'), module.__dict__)
    sys.modules[name] = module
    return module

def missing_prerequisites(root: Path, refs: dict[str, dict[str, str]], *, purpose: str='execution') -> list[str]:
    """No future control/source/qualification receipts are fabricated."""
    required = ('current_contract', 'current_core', 'current_manifest', 'current_source_evidence', 'eligible_joern_plan', 'native_decision_review', 'startup_control_review', 'first_case_capability_review', 'source_regression_review', 'external_launch_review', 'group_contract_review')
    require(purpose in {'stage-qualification', 'execution'}, 'unknown validation purpose')
    if purpose == 'stage-qualification':
        required = tuple(name for name in required if name != 'external_launch_review')
    missing = [name for name in required if name not in refs]
    for name in required:
        if name in refs:
            document(root, refs[name])
    return missing

def bound_current_core(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    """Runtime envelope fields are not serialized into the core they bind."""
    require(isinstance(value.get('core_identity'), dict), 'exact core identity ref required')
    artifact = {key: item for (key, item) in value.items() if key not in {'core_identity', 'prerequisite_refs'}}
    require(document(root, value['core_identity']) == artifact, 'runtime envelope/core bytes differ')
    return artifact


def prepare_current_graph(root: Path, core: dict[str, Any]):
    """Context manager for one actual inherited88 plus sealed adapter7 graph.

    Hosts are exact immutable predecessors, loaded normally for dataclass and
    CLI metadata correctness. No predecessor callback is accepted from JSON.
    """
    import contextlib
    import uuid

    @contextlib.contextmanager
    def scope():
        old = inherited_core(root)
        prefix = '_joern05_boot_' + uuid.uuid4().hex
        hosts = {}
        graph = None
        try:
            for role in ('bridge19', 'protocol24', 'admission24', 'supervisor24'):
                hosts[role] = load_bound_module(root, prefix + '_' + role,
                                                old['runtime_module_graph'][role])
            graph88 = hosts['bridge19'].prepare_graph(root, old, host_modules=hosts)
            # Import the outer loader from its actual sealed source. Bare
            # local imports in this bootstrap resolve only the verified sibling
            # sources; graph-owned actual operation uses the new local routes.
            from bridge import prepare_graph95, close_graph95
            graph = prepare_graph95(root, inherited_graph=graph88,
                graph_refs=core['runtime_module_graph'], adapter_refs=core['adapter_module_refs'],
                import_edges=core['adapter_import_edges'])
            yield graph
        finally:
            if graph is not None:
                close_graph95(graph)
            for role in hosts:
                sys.modules.pop(prefix + '_' + role, None)
    return scope()
