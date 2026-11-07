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
HISTORY_RELATIVE_PATH = 'reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history-provider-03/history_provider_03.py'
HISTORY_PATH = str(ROOT / HISTORY_RELATIVE_PATH)
HISTORY_SHA = '06da2c46dbe99f5921c5967a493d23bf86af477614ce7ca0ef5efec14ffb98c0'
HISTORY_REF = {'path': HISTORY_RELATIVE_PATH, 'sha256': HISTORY_SHA}
HISTORY_PROVIDER03_REF = HISTORY_REF
LIVE_LEDGER_PATH = 'reports/releases/v0.9.2/ledger-v1.jsonl'
MAX_LIVE_LEDGER_BYTES = 256 * 1024 * 1024
_HISTORY_MODULE_NAME = '_private_joern_history_provider03_for_adapter08'
_HISTORY_MODULE: Any | None = None

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
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, 'duplicate JSON object key: ' + key)
            value[key] = item
        return value
    try:
        value = json.loads(read_ref(root, ref), object_pairs_hook=unique)
    except json.JSONDecodeError as exc:
        raise AdapterError('artifact is not strict JSON') from exc
    require(isinstance(value, dict), 'artifact JSON must be object')
    return value

def inherited_core(root: Path) -> dict[str, Any]:
    return document(root, {'path': CORE_PATH, 'sha256': CORE_SHA})

def attach_cleanup_error(primary: BaseException, cleanup: BaseException) -> None:
    detail = {'type': type(cleanup).__name__, 'message': str(cleanup)}
    primary.adapter_cleanup_errors = [
        *getattr(primary, 'adapter_cleanup_errors', []), detail]
    primary.add_note('Additional adapter cleanup failure: ' + repr(cleanup))


def cleanup_registered_modules(entries: list[tuple[str, Any]]) -> None:
    errors = []
    for name, module in reversed(entries):
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            errors.append(name)
    require(not errors, 'module registration identity changed: ' + ', '.join(errors))


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
    except BaseException as error:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        else:
            attach_cleanup_error(error, AdapterError(
                'failed module registration identity changed: ' + name))
        raise
    return module

def load_history_provider(root: Path = ROOT) -> Any:
    """Load the exact archive-only provider only after digest verification."""
    global _HISTORY_MODULE
    require(_HISTORY_MODULE_NAME not in sys.modules,
            'private history provider module name is already owned')
    if _HISTORY_MODULE is not None:
        read_ref(root, HISTORY_REF)
        return _HISTORY_MODULE
    module = load_bound_module(root, _HISTORY_MODULE_NAME, HISTORY_REF)
    # Dataclass construction needs the registration while the provider loads.
    # The adapter retains the private module object, leaving the graph baseline intact.
    try:
        require(callable(getattr(module, 'validate_archive_only_130', None)),
                'history provider03 lacks archive-only130 API')
    finally:
        cleanup_registered_modules([(_HISTORY_MODULE_NAME, module)])
    _HISTORY_MODULE = module
    return module


def load_history_reader() -> Any:
    """Compatibility alias for graph-owned callers; returns provider03."""
    return load_history_provider()


def read_live_ledger(root: Path) -> bytes:
    """Read one bounded live snapshot without following symlink components."""
    import os
    import stat
    path = root / LIVE_LEDGER_PATH
    for item in (path, *path.parents):
        try:
            info = os.lstat(item)
        except OSError as exc:
            raise AdapterError('live ledger path is missing or unreadable') from exc
        require(not stat.S_ISLNK(info.st_mode), 'live ledger symlink forbidden')
        if item != path:
            require(stat.S_ISDIR(info.st_mode), 'live ledger path component is not a directory')
    before = os.lstat(path)
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_LIVE_LEDGER_BYTES,
            'live ledger is not a bounded regular file')
    raw = path.read_bytes()
    after = os.lstat(path)
    signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    require(signature(before) == signature(after) and len(raw) == before.st_size,
            'live ledger changed while reading')
    require(not path.is_symlink(), 'live ledger path changed to symlink')
    return raw

def missing_prerequisites(root: Path, refs: dict[str, dict[str, str]], *, purpose: str='execution') -> list[str]:
    """No future control/source/qualification receipts are fabricated."""
    required = (
        'current_contract', 'current_core', 'current_manifest', 'current_source_evidence',
        'eligible_joern_plan', 'native_decision_review', 'startup_control_review',
        'first_case_capability_review', 'source_regression_review', 'external_launch_review',
        'group_contract_review', 'native_control_request', 'native_invocation_review',
        'native_parent_started', 'native_worker_invocation', 'native_exit',
        'native_control_result', 'native_startup_sidecar_manifest',
        'native_capture_review', 'native_finalization_receipt',
        'native_finalizer_diagnostic_review',
    )
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


def bootstrap_bridge(root: Path, core: dict[str, Any]) -> Any:
    """Verify the sole bootstrap bridge before inherited88 records its baseline."""
    ref = core['adapter_module_refs']['joern05_bridge']
    read_ref(root, ref)
    sibling = Path(__file__).resolve().with_name('bridge.py')
    # The bootstrap copy must be the very source sealed as adapter7's bridge.
    read_ref(sibling.parent, {'path': sibling.name, 'sha256': ref['sha256']})
    if 'bridge' in sys.modules:
        module = sys.modules['bridge']
        require(getattr(module, '__file__', None) == str(sibling),
                'bootstrap bridge registered owner differs')
        require(getattr(module, '__spec__', None) is not None and
                module.__spec__.origin == str(sibling),
                'bootstrap bridge registered spec differs')
        for name in ('prepare_graph95', 'close_graph95'):
            function = getattr(module, name, None)
            require(callable(function) and getattr(function, '__globals__', None) is module.__dict__,
                    'bootstrap bridge function owner differs')
    else:
        module = load_bound_module(sibling.parent, 'bridge',
                                   {'path': sibling.name, 'sha256': ref['sha256']})
    from bridge import prepare_graph95, close_graph95
    require(prepare_graph95 is module.prepare_graph95 and
            close_graph95 is module.close_graph95, 'bootstrap import owner differs')
    return module


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
        bootstrap = bootstrap_bridge(root, core)
        prefix = '_joern05_boot_' + uuid.uuid4().hex
        hosts = {}
        graph = None
        graph88 = None
        primary = None
        try:
            for role in ('bridge19', 'protocol24', 'admission24', 'supervisor24'):
                hosts[role] = load_bound_module(root, prefix + '_' + role,
                                                old['runtime_module_graph'][role])
            graph88 = hosts['bridge19'].prepare_graph(root, old, host_modules=hosts)
            # Verified bootstrap dependency predates the frozen88 baseline.
            graph = bootstrap.prepare_graph95(root, inherited_graph=graph88,
                graph_refs=core['runtime_module_graph'], adapter_refs=core['adapter_module_refs'],
                import_edges=core['adapter_import_edges'])
            yield graph
        except BaseException as error:
            primary = error
            raise
        finally:
            failures = []
            # Adapter95 registrations are later than the inherited88 baseline.
            # Remove only exact owned entries before the unchanged boundary.
            if graph is not None:
                try:
                    bootstrap.close_graph95(graph)
                except BaseException as error:
                    failures.append(error)
            if graph88 is not None:
                try:
                    graph88.import_context.close_on_error()
                except BaseException as error:
                    failures.append(error)
            # Baseline host objects must remain registered through frozen close.
            try:
                cleanup_registered_modules([
                    (prefix + '_' + role, module) for role, module in hosts.items()])
            except BaseException as error:
                failures.append(error)
            if failures:
                if primary is not None:
                    for failure in failures:
                        attach_cleanup_error(primary, failure)
                else:
                    for failure in failures[1:]:
                        attach_cleanup_error(failures[0], failure)
                    raise failures[0]
    return scope()
