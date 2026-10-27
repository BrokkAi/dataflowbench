import builtins
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

PRIVATE = Path(__file__).resolve().parent
REPO = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
sys.path.insert(0, str(PRIVATE))
mode = sys.argv[1]
assert mode in {'late', 'foreign', 'unknown', 'drift'}
ADAPTER_NAMES = ('packet', 'history', 'protocol', 'stage_runtime', 'bridge',
                 'admission', 'supervisor')
ADAPTER_DEPENDENCIES = {
    'packet': ('bridge',), 'history': ('packet',), 'protocol': ('packet',),
    'stage_runtime': ('packet', 'protocol', 'history', 'admission', 'supervisor', 'bridge'),
    'bridge': ('packet', 'stage_runtime', 'protocol'),
    'admission': ('packet', 'protocol', 'stage_runtime'),
    'supervisor': ('packet', 'protocol', 'admission', 'stage_runtime', 'bridge', 'history'),
}
ADAPTER_EDGES = tuple(sorted(
    ('joern05_' + caller, 'joern05_' + target)
    for caller, targets in ADAPTER_DEPENDENCIES.items() for target in targets))

# This is the supervisor's entrypoint import shape: supervisor imports packet and protocol,
# while packet/bridge are resolved from the task-owned private directory.
import supervisor
import packet

pre_supervisor_bridge = 'bridge' in sys.modules
assert not pre_supervisor_bridge

with tempfile.TemporaryDirectory(prefix='joern05-cli-import-order-', dir='/private/tmp') as directory:
    root = Path(directory).resolve()
    old = packet.inherited_core(packet.ROOT)
    for ref in [*old['runtime_module_graph'].values(), {'path': packet.CORE_PATH, 'sha256': packet.CORE_SHA}, {'path': packet.HISTORY_RELATIVE_PATH, 'sha256': packet.HISTORY_SHA}]:
        source = packet.ROOT / ref['path']
        target = root / ref['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    adapter_refs = {}
    for name in ADAPTER_NAMES:
        raw = (PRIVATE / (name + '.py')).read_bytes()
        path = 'candidate/' + name + '.py'
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        adapter_refs['joern05_' + name] = {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}
    core = {
        'runtime_module_graph': {**old['runtime_module_graph'], **adapter_refs},
        'adapter_module_refs': adapter_refs,
        'adapter_import_edges': [{'caller_role': caller, 'target_role': target}
                                 for caller, target in ADAPTER_EDGES],
    }

    if mode == 'foreign':
        import types
        foreign = types.ModuleType('foreign_bridge')
        sys.modules['bridge'] = foreign
    if mode == 'drift':
        adapter_refs['joern05_bridge']['sha256'] = '0' * 64
    result = None
    caught = None
    inherited = None
    try:
        with packet.prepare_current_graph(root, core) as graph:
            bootstrap = sys.modules['bridge']
            inherited = bootstrap.inherited_view(graph)
            assert inherited.import_context._global_sys_before['bridge'] is bootstrap
            assert len(graph.members) == 95 and len(inherited.members) == 88
            assert graph.graph_sha256 != inherited.graph_sha256
            assert not inherited.import_context._closed
            result = 'real95-and88-baseline-bound'
            if mode == 'unknown':
                import types
                sys.modules['_outer_unknown_nonstdlib'] = types.ModuleType('unknown')
    except BaseException as error:
        caught = {'type': type(error).__name__, 'message': str(error)}
    if mode == 'late':
        assert caught is None, caught
        assert inherited.import_context._closed
        assert result == 'real95-and88-baseline-bound'
    elif mode == 'foreign':
        assert caught is not None and 'owner differs' in caught['message'], caught
        assert sys.modules['bridge'] is foreign
        assert result is None
    elif mode == 'unknown':
        assert caught is not None and 'non-stdlib' in caught['message'], caught
        assert '_outer_unknown_nonstdlib' in sys.modules
    else:
        assert caught is not None and 'SHA differs' in caught['message'], caught
        assert result is None
    assert not any(name.startswith(('_joern05_boot_', '_joern05_graph_')) for name in sys.modules)
    print(json.dumps({'mode': mode, 'supervisor_imported': True,
                      'bridge_initially_absent': not pre_supervisor_bridge,
                      'result': result, 'caught': caught,
                      'frozen_close': bool(inherited and inherited.import_context._closed)}, sort_keys=True))
