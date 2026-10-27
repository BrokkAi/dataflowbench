"""Small graph-owned opaque-stage bridge; no JSON runtime reconstruction."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from packet import inherited_core, require

def validate_graph_roles(root: Path, graph_refs: dict[str, Any], replacements: dict[str, Any], additions: dict[str, Any]) -> None:
    old = inherited_core(root)['runtime_module_graph']
    require(set(replacements) <= set(old), 'unknown replacement role')
    require(not set(additions) & set(old), 'added graph role collides')
    expected = dict(old)
    expected.update(replacements)
    expected.update(additions)
    require(graph_refs == expected, 'graph omits/adds/rebinds an unreviewed role')
    for name in old:
        if name not in replacements:
            require(graph_refs[name] == old[name], 'historical role changed')

def runtime_objects(pinned_bridge: Any, stage: Any, graph: Any) -> Any:
    """Delegate opaque validation; a dict receipt is not a stage."""
    require(not isinstance(stage, dict), 'opaque context transfer required; metadata cannot supply runtime')
    pinned_bridge.assert_stage_current(stage.root, stage, graph)
    return pinned_bridge.runtime_objects(stage)

def child_ledger_selector(parent: dict[str, Any]) -> dict[str, Any]:
    require(type(parent.get('ledger_rows')) is int and parent['ledger_rows'] in (109, 110), 'parent verified row count missing')
    result = dict(parent['ledger_ref'])
    require(result.get('sha256') == parent['ledger_sha256'], 'parent ledger digest differs')
    require('rows' not in result or result['rows'] == parent['ledger_rows'], 'conflicting ledger rows')
    result['rows'] = parent['ledger_rows']
    return result

def create_parent(root: Path, core: dict[str, Any], manifest_ref: dict[str, str], ledger_ref: dict[str, Any], *, graph: Any, lock_identity: Any, sidecars: dict[str, Any], runtime_role: str, runtime_ref: dict[str, str]) -> Any:
    """Use immutable opaque stage mechanics with a new graph-owned validator."""
    from packet import document, read_ref
    from stage_runtime import _pinned_member
    assert_graph95_core(root, graph, core)
    manifest = document(root, manifest_ref)
    require(manifest['core_identity'] == core['core_identity'], 'parent manifest/core differs')
    require(document(root, core['core_identity']) == {k: v for (k, v) in core.items() if k not in {'core_identity', 'prerequisite_refs'}}, 'parent current core differs from bound artifact')
    loader = _pinned_member(root, graph, runtime_role, runtime_ref).load_runtime_context
    require(type(ledger_ref.get('rows')) is int and ledger_ref['rows'] == 109, 'before parent ledger must be exact109')
    raw = read_ref(root, {k: ledger_ref[k] for k in ('path', 'sha256')})
    require(len(raw.splitlines()) == 109, 'parent ledger bytes/rows differ')
    inherited = graph.module('bridge19')
    (runtime, _) = inherited.load_runtime_stage(root, graph=graph, runtime_loader=loader, core_identity=core, mode='before', ledger_bytes=raw)
    require(isinstance(runtime, inherited.ActualRuntimeContext), 'new validator did not return actual opaque runtime')
    refs = inherited._canonical_source_refs(root, core, 'Joern05 current')
    refs += [manifest_ref, core['core_identity'], core['source_evidence'], core['source_design']]
    refs = include_adapter_source_refs(graph, refs)
    return build_parent95(root, core=core, index=0, ledger=ledger_ref, runtime=runtime, graph=graph, source_commit=core['source_commit'], plan_commit=core['plan_commit'], contract_sha256=core['contract']['sha256'], lock=lock_identity, sidecars=sidecars, source_refs=refs, analyzer_deadline_seconds=_deadline(core, root), startup_seconds=600, live_ledger={'path': 'reports/releases/v0.9.2/ledger-v1.jsonl', 'sha256': ledger_ref['sha256']})

def _deadline(core: dict[str, Any], root: Path) -> int:
    from packet import document
    from protocol import GROUP
    groups = [g for g in document(root, core['contract'])['groups'] if g['id'] == GROUP]
    require(len(groups) == 1 and type(groups[0]['deadline_seconds']) is int and (groups[0]['deadline_seconds'] > 0), 'actual singleton deadline missing')
    return groups[0]['deadline_seconds']

def create_child(root: Path, core: dict[str, Any], manifest_ref: dict[str, str], parent_ref: dict[str, str], ledger_ref: dict[str, Any], *, graph: Any, lock_identity: Any, lease: Any, child_identity: dict[str, Any], sidecars: dict[str, Any], runtime_role: str, runtime_ref: dict[str, str]) -> Any:
    """Rebuild in the child process; a compact parent never transfers runtime."""
    from packet import document, read_ref
    from stage_runtime import _pinned_member
    assert_graph95_core(root, graph, core)
    inherited = graph.module('bridge19')
    parent = inherited._read_compact_parent(root, parent_ref, core=core)
    require(parent['manifest_ref'] == manifest_ref and parent['core_identity'] == core['core_identity'], 'child parent manifest/core differs')
    expected = child_ledger_selector(parent)
    require(ledger_ref == expected, 'child ledger metadata differs from verified parent')
    raw = read_ref(root, {k: ledger_ref[k] for k in ('path', 'sha256')})
    require(len(raw.splitlines()) == ledger_ref['rows'] == 109, 'child exact109 ledger differs')
    loader = _pinned_member(root, graph, runtime_role, runtime_ref).load_runtime_context
    (runtime, _) = inherited.load_runtime_stage(root, graph=graph, runtime_loader=loader, core_identity=core, mode='before', ledger_bytes=raw)
    require(isinstance(runtime, inherited.ActualRuntimeContext), 'child runtime is not actual opaque context')
    refs = inherited._canonical_source_refs(root, core, 'Joern05 child')
    refs += [manifest_ref, core['core_identity'], core['source_evidence'], core['source_design']]
    refs = include_adapter_source_refs(graph, refs)
    require(lease.registered_deadline_seconds == _deadline(core, root) and lease.startup_seconds == 600, 'child phase lease differs')
    return build_child95(root, core=core, parent_binding=parent, runtime=runtime, graph=graph, source_refs=refs, child_creator_pid=child_identity['creator_pid'], child_creator_birth=child_identity['creator_birth'], child_pid=child_identity['pid'], child_birth=child_identity['birth'], analyzer_deadline_seconds=lease.registered_deadline_seconds, popen_monotonic=lease.popen_monotonic, sidecars=sidecars, ledger=ledger_ref, lock_identity=lock_identity, live_ledger={'path': 'reports/releases/v0.9.2/ledger-v1.jsonl', 'sha256': ledger_ref['sha256']})

# Exactly these seven additions are part of this source candidate. A runner
# revision is not an implicit eighth addition or an ambient import. Its
# accepted dependency closure must be supplied by the reviewed adapter source.
ADAPTER_NAMES = ('packet', 'history', 'protocol', 'stage_runtime', 'bridge',
                 'admission', 'supervisor')
ADAPTER_ROLES = tuple('joern05_' + name for name in ADAPTER_NAMES)
# Explicit ordinary imports, including function-local imports. Source SHA
# sealing makes this table prospective reviewed policy, not a runtime oracle.
ADAPTER_DEPENDENCIES = {
    'packet': ('bridge',), 'history': ('packet',), 'protocol': ('packet',),
    'stage_runtime': ('packet', 'protocol', 'history', 'admission', 'supervisor', 'bridge'),
    'bridge': ('packet', 'stage_runtime', 'protocol'),
    'admission': ('packet', 'protocol', 'stage_runtime'),
    'supervisor': ('packet', 'protocol', 'admission', 'stage_runtime', 'bridge', 'history'),
}
ADAPTER_IMPORT_EDGES = tuple(sorted(
    ('joern05_' + caller, 'joern05_' + target)
    for caller, targets in ADAPTER_DEPENDENCIES.items() for target in targets))


def adapter_import_edges() -> list[dict[str, str]]:
    return [{'caller_role': caller, 'target_role': target}
            for caller, target in ADAPTER_IMPORT_EDGES]



_GRAPH95_VIEWS: dict[Any, dict[str, Any]] = {}


def inherited_view(graph: Any) -> Any:
    """Return the separately registered88 authority, never impersonate it."""
    record = _GRAPH95_VIEWS.get(graph)
    return graph if record is None else record['inherited_graph88']


def close_graph95(graph: Any) -> None:
    record = _GRAPH95_VIEWS.get(graph)
    require(record is not None, 'current graph95 is not registered or already closed')
    record['dispose']()



def prepare_graph95(root: Path, *, inherited_graph: Any,
                    graph_refs: dict[str, Any], adapter_refs: dict[str, Any],
                    import_edges: list[dict[str, str]]) -> Any:
    """Extend actual inherited objects with seven exact source-owned modules.

    The caller must seal both maps in the current core. Local imports execute
    through per-module builtins, not sys.path or process-global bare aliases.
    The inherited import facade and all 88 module instances remain untouched.
    """
    import ast
    import builtins
    import importlib.util
    import sys
    import types
    import uuid
    from packet import read_ref

    old = inherited_core(root)['runtime_module_graph']
    require(len(old) == 88 and set(adapter_refs) == set(ADAPTER_ROLES),
            'graph additions must be exactly seven adapter roles')
    expected = {**old, **adapter_refs}
    require(len(graph_refs) == 95 and graph_refs == expected,
            'current graph must bind exact inherited88 plus adapter7')
    require({m.name: {'path': m.canonical_path, 'sha256': m.source_sha256}
             for m in inherited_graph.members} == old,
            'inherited graph is not the immutable88 view')
    require(len({r['path'] for r in adapter_refs.values()}) == 7,
            'adapter paths must be unique')
    require(not {r['path'] for r in old.values()} &
            {r['path'] for r in adapter_refs.values()},
            'adapter path collides with inherited source')
    for ref in old.values():
        read_ref(root, ref)
    raw_by_role = {role: read_ref(root, ref) for role, ref in adapter_refs.items()}
    require(import_edges == adapter_import_edges(),
            'adapter ordinary import edges differ from reviewed exact topology')
    observed = set()
    for role, raw in raw_by_role.items():
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in ADAPTER_NAMES:
                observed.add((role, 'joern05_' + node.module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ADAPTER_NAMES:
                        observed.add((role, 'joern05_' + alias.name))
    require(observed == set(ADAPTER_IMPORT_EDGES),
            'adapter source imports differ from reviewed exact topology')
    frozen = inherited_graph.module('bridge19')
    namespace = '_joern05_graph_' + uuid.uuid4().hex
    modules = {}
    registered = []
    real_import = builtins.__import__

    def local_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in ADAPTER_NAMES:
            callers = [role for role, module in modules.items()
                       if globals is module.__dict__]
            role = 'joern05_' + name
            require(len(callers) == 1 and (callers[0], role) in ADAPTER_IMPORT_EDGES,
                    'adapter import caller/target edge is not registered')
            require(role in modules, 'unregistered adapter import')
            return modules[role]
        require(not name.startswith('joern05_'), 'undeclared adapter selector')
        return real_import(name, globals, locals, fromlist, level)

    def dispose():
        errors = []
        for name, module in reversed(registered):
            if sys.modules.get(name) is module:
                del sys.modules[name]
            else:
                errors.append(name)
        require(not errors, 'adapter module registration identity changed: ' + ', '.join(errors))

    try:
        for role, ref in adapter_refs.items():
            name = namespace + '_' + role
            require(name not in sys.modules, 'synthetic graph name collides')
            module = types.ModuleType(name)
            module.__file__ = str(root / ref['path'])
            module.__spec__ = importlib.util.spec_from_file_location(name, module.__file__)
            module.__builtins__ = {**vars(builtins), '__import__': local_import}
            modules[role] = module
            sys.modules[name] = module
            registered.append((name, module))
        for logical in ADAPTER_NAMES:
            role = 'joern05_' + logical
            exec(compile(raw_by_role[role], modules[role].__file__, 'exec'),
                 modules[role].__dict__)
        members = list(inherited_graph.members)
        for role in sorted(ADAPTER_ROLES):
            ref = adapter_refs[role]
            members.append(frozen.GraphMember(role, ref['path'], ref['sha256'],
                                              modules[role], namespace + ':' + role))
        # The outer graph does not advertise the inherited88 import context
        # as authority for95. Its seven local routes are separately sealed;
        # frozen scopes receive inherited_graph88 explicitly.
        # The inherited constructor accepts additional sorted roles. It does
        # not invoke the exact88 import topology adapter again.
        members = list(members[:11]) + sorted(members[11:], key=lambda m: m.name)

        result = frozen.PinnedBridgeGraph(
            members, fixture_only=inherited_graph.fixture_only, import_context=None)
        record = {'inherited_graph88': inherited_graph}
        registries = (_GRAPH95_VIEWS, modules['joern05_bridge']._GRAPH95_VIEWS)
        def dispose_graph():
            for registry in registries:
                if registry.get(result) is record:
                    del registry[result]
            dispose()
        record['dispose'] = dispose_graph
        for registry in registries:
            require(result not in registry, 'outer graph identity already registered')
            registry[result] = record
        require(result.graph_sha256 != inherited_graph.graph_sha256,
                'outer95 identity must differ from inherited88')
        return result
    except BaseException as error:
        try:
            dispose()
        except BaseException as cleanup:
            from packet import attach_cleanup_error
            attach_cleanup_error(error, cleanup)
        raise


def graph_provenance(graph: Any) -> dict[str, Any]:
    """A diagnostic binding; never a replacement for the opaque graph object."""
    old = inherited_view(graph)
    require(old is not graph and len(graph.members) == 95 and len(old.members) == 88,
            'current stage requires distinct graph95 and graph88 views')
    return {'schema': 'v092-joern05-graph95-provenance/v1',
            'graph95_sha256': graph.graph_sha256,
            'inherited_graph88_sha256': old.graph_sha256,
            'ordinary_import_edges': adapter_import_edges(),
            'adapter_refs': {m.name: {'path': m.canonical_path,
                                     'sha256': m.source_sha256}
                             for m in graph.members if m.name in ADAPTER_ROLES}}


def assert_graph95_core(root: Path, graph: Any, core: dict[str, Any]) -> dict[str, Any]:
    provenance = graph_provenance(graph)
    refs = {m.name: {'path': m.canonical_path, 'sha256': m.source_sha256}
            for m in graph.members}
    require(core.get('runtime_module_graph') == refs,
            'current core does not seal exact graph95')
    require(core.get('adapter_import_edges') == provenance['ordinary_import_edges'],
            'current core does not seal exact adapter import topology')
    require(core.get('adapter_module_refs') == provenance['adapter_refs'],
            'current core does not seal exact seven adapter refs')
    # The manifest binds the exact core SHA at create_parent/create_child.
    # This binding is independently retained in the opaque runtime digest.
    return provenance


def include_adapter_source_refs(graph: Any, source_refs: list[dict]) -> list[dict]:
    from packet import HISTORY_REF
    refs = list(source_refs)
    indexed = {ref['path']: ref['sha256'] for ref in refs}
    for ref in graph_provenance(graph)['adapter_refs'].values():
        if ref['path'] in indexed:
            require(indexed[ref['path']] == ref['sha256'],
                    'stage adapter inventory conflicts with core source closure')
        else:
            refs.append(ref)
            indexed[ref['path']] = ref['sha256']
    if HISTORY_REF['path'] in indexed:
        require(indexed[HISTORY_REF['path']] == HISTORY_REF['sha256'],
                'stage history provider conflicts with canonical source closure')
    else:
        refs.append(dict(HISTORY_REF))
    return refs


def build_parent95(root: Path, *, graph: Any, core: dict[str, Any],
                   runtime: Any, **kwargs: Any) -> Any:
    """Real opaque constructor, also used by bounded fixture composition."""
    provenance = assert_graph95_core(root, graph, core)
    frozen = graph.module('bridge19')
    require(isinstance(runtime, frozen.ActualRuntimeContext) and runtime.graph is graph,
            'parent runtime must own actual outer95 graph')
    require(runtime.diagnostic.get('graph_provenance') == provenance,
            'parent runtime omits distinct outer/inherited graph bindings')
    kwargs['source_refs'] = include_adapter_source_refs(graph, kwargs['source_refs'])
    return frozen.build_parent_stage(root, runtime=runtime, graph=graph, **kwargs)


def build_child95(root: Path, *, graph: Any, core: dict[str, Any],
                  runtime: Any, **kwargs: Any) -> Any:
    provenance = assert_graph95_core(root, graph, core)
    frozen = graph.module('bridge19')
    require(isinstance(runtime, frozen.ActualRuntimeContext) and runtime.graph is graph,
            'child runtime must independently own actual outer95 graph')
    require(runtime.diagnostic.get('graph_provenance') == provenance,
            'child runtime omits distinct graph bindings')
    kwargs['source_refs'] = include_adapter_source_refs(graph, kwargs['source_refs'])
    return frozen.build_child_stage(root, runtime=runtime, graph=graph, **kwargs)
