"""Private actual-constructor tests; synthetic runtime I/O, never qualification.

Inherited88 is imported from immutable real sources. A private mirror provides
source bytes, synthetic109 JSON lines, and fixture core/manifest. Only the
expensive load_runtime_context evidence-I/O boundary is replaced in the
parent/child composition. Frozen loader ownership, stage constructors, compact
writer/reader, graph checks, metadata/rows, and inventory checks are real.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import bridge
import packet


class Graph95Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = packet.inherited_core(packet.ROOT)
        cls.host_names = []
        cls.hosts = {}
        for role in ('bridge19', 'supervisor24', 'protocol24', 'admission24'):
            name = '_joern05_graph95_test_host_' + role
            cls.host_names.append(name)
            cls.hosts[role] = packet.load_bound_module(packet.ROOT, name,
                                                       cls.old['runtime_module_graph'][role])
        cls.frozen = cls.hosts['bridge19']
        cls.graph88 = cls.frozen.prepare_graph(packet.ROOT, cls.old,
                                               host_modules=cls.hosts)

    @classmethod
    def tearDownClass(cls):
        for name in cls.host_names:
            sys.modules.pop(name, None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='joern05-graph95-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        paths = {ref['path'] for ref in self.old['runtime_module_graph'].values()}
        paths.add(packet.CORE_PATH)
        paths.add(packet.HISTORY_RELATIVE_PATH)
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(packet.ROOT / path, target)
        self.adapters = {}
        for name in bridge.ADAPTER_NAMES:
            path = 'candidate/' + name + '.py'
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = (HERE / (name + '.py')).read_bytes()
            target.write_bytes(raw)
            self.adapters['joern05_' + name] = {'path': path, 'sha256': packet.digest(raw)}
        self.refs = {**self.old['runtime_module_graph'], **self.adapters}

    def prepare(self, refs=None, adapters=None):
        graph = bridge.prepare_graph95(self.root, inherited_graph=self.graph88,
                                       graph_refs=self.refs if refs is None else refs,
                                       adapter_refs=self.adapters if adapters is None else adapters,
                                       import_edges=bridge.adapter_import_edges())
        self.addCleanup(lambda: bridge.close_graph95(graph) if graph in bridge._GRAPH95_VIEWS else None)
        return graph

    def artifact(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = value if isinstance(value, bytes) else packet.canonical(value)
        target.write_bytes(raw)
        return {'path': path, 'sha256': packet.digest(raw)}

    def fixture(self, graph):
        inputs = [{**ref, 'role': 'release-input'} for ref in self.adapters.values()]
        contract = self.artifact('candidate/contract.json', {
            'source_commit': 'a' * 40, 'source_inputs': inputs,
            'groups': [{'id': 'joern-swift-common108', 'deadline_seconds': 1368}]})
        core = {'source_commit': 'a' * 40, 'plan_commit': 'b' * 40,
                'contract': contract, 'source_inputs': inputs,
                'runtime_module_graph': self.refs, 'adapter_module_refs': self.adapters,
                'adapter_import_edges': bridge.adapter_import_edges(),
                'source_evidence': self.artifact('candidate/evidence.json', {'fixture': True}),
                'source_design': self.artifact('candidate/design.json', {'fixture': True}),
                'sidecar_namespace': 'candidate/execution'}
        identity = self.artifact('candidate/core.json', core)
        core = {**core, 'core_identity': identity}
        manifest = self.artifact('candidate/manifest.json', {'core_identity': identity})
        raw = b''.join(packet.canonical({'fixture_row': n}) for n in range(109))
        ledger = {**self.artifact('candidate/ledger.jsonl', raw), 'rows': 109}
        self.artifact('reports/releases/v0.9.2/ledger-v1.jsonl', raw)
        lock_path = self.root / 'candidate/lock'
        lock_path.write_bytes(b'')
        fd = os.open(lock_path, os.O_RDWR)
        self.last_fixture_fd = fd
        self.addCleanup(os.close, fd)
        lock = self.frozen.capture_lock(self.root, str(lock_path), os.getpid(), 'fixture-birth')
        return core, manifest, ledger, lock, fd

    def actual_runtime(self, graph, root, mode, calls):
        diagnostic = {'graph_provenance': bridge.graph_provenance(graph),
                      'context_digest': 'd' * 64, 'fixture_runtime_io': True}
        modules = {name: graph.module(name) for name in self.frozen.REQUIRED_GRAPH_NAMES}
        result = self.frozen.ActualRuntimeContext(root, mode, graph, modules, diagnostic)
        calls.append(result)
        return result

    def parent_child(self, graph, *, mutate_parent=None, mutate_child=None):
        core, manifest, ledger, lock, fd = self.fixture(graph)
        source = graph.module('joern05_stage_runtime')
        calls = []

        def evidence_io(root, core, *, graph, mode, ledger_bytes):
            self.assertEqual(len(ledger_bytes.splitlines()), 109)
            return self.actual_runtime(graph, root, mode, calls)

        # The seam returns an actual runtime object; no opaque stage is mocked.
        with mock.patch.object(source, 'load_runtime_context', evidence_io):
            parent = graph.module('joern05_bridge').create_parent(
                self.root, core, manifest, ledger, graph=graph, lock_identity=lock,
                sidecars={}, runtime_role='joern05_stage_runtime',
                runtime_ref=self.adapters['joern05_stage_runtime'])
            self.frozen.assert_stage_current(self.root, parent, graph)
            parent_ref = self.frozen.write_compact_stage_receipt(
                self.root, 'candidate/execution/stages/stage-00.json', parent,
                status='parent-stage-verified', sidecar_names=[],
                manifest_ref=manifest, core_identity=core['core_identity'], core=core)
            receipt = packet.document(self.root, parent_ref)
            if mutate_parent:
                mutate_parent(receipt)
                # A caller cannot change the already witnessed hash.
                (self.root / parent_ref['path']).write_bytes(packet.canonical(receipt))
            selected = bridge.child_ledger_selector(receipt)
            if mutate_child:
                mutate_child(selected)
            sidecars = {key: self.artifact('candidate/dispatch/' + key + '.json', {'fixture': key})
                        for key in ('admission', 'phase', 'raw')}
            child = graph.module('joern05_bridge').create_child(
                self.root, core, manifest, parent_ref, selected, graph=graph,
                lock_identity=lock, lease=types.SimpleNamespace(
                    registered_deadline_seconds=1368, startup_seconds=600,
                    popen_monotonic=time.monotonic()),
                child_identity={'creator_pid': os.getpid(), 'creator_birth': 'fixture-birth',
                                'pid': os.getpid(), 'birth': 'fixture-child'},
                sidecars=sidecars, runtime_role='joern05_stage_runtime',
                runtime_ref=self.adapters['joern05_stage_runtime'])
        self.assertIsNot(calls[0], calls[1])
        self.assertIsNot(calls[0], child.runtime)
        self.assertIs(child.runtime, calls[1])
        self.frozen.assert_stage_current(self.root, child, graph)
        self.frozen.assert_child_ready(self.root, child, parent=parent, graph=graph,
                                      now_monotonic=time.monotonic())
        self.frozen.assert_child_ready_from_receipt(
            self.root, child, parent_receipt_ref=parent_ref, graph=graph,
            manifest_ref=manifest, core_identity=core['core_identity'], core=core,
            dispatch_sidecars=sidecars, now_monotonic=time.monotonic(),
            stage_bridge=self.frozen)
        self.assertEqual(len(receipt['graph_bindings']), 95)
        self.assertEqual(receipt['graph_sha256'], graph.graph_sha256)
        self.assertNotEqual(receipt['graph_sha256'], self.graph88.graph_sha256)
        self.assertEqual(child.runtime.diagnostic['graph_provenance']['inherited_graph88_sha256'],
                         self.graph88.graph_sha256)
        os.fstat(fd)  # Constructors do not close a caller-owned descriptor.
        return parent, child

    def test_exact95_preserves88_objects_and_local_imports(self):
        graph = self.prepare()
        self.assertEqual(len(graph.members), 95)
        self.assertIs(type(graph), self.frozen.PinnedBridgeGraph)
        for item in self.graph88.members:
            self.assertIs(graph.module(item.name), item.module_object)
        self.assertIs(bridge.inherited_view(graph), self.graph88)
        self.assertIs(graph.module('joern05_history').require,
                      graph.module('joern05_packet').require)
        self.assertIsNot(graph.module('joern05_history').require, packet.require)
        self.assertIsNone(graph.import_context)
        self.assertIs(bridge.inherited_view(graph).import_context, self.graph88.import_context)

    def test_missing_extra_and_inherited_drift_rejected(self):
        for mode in ('missing', 'extra', 'drift'):
            refs = copy.deepcopy(self.refs)
            if mode == 'missing':
                refs.pop('joern05_history')
            elif mode == 'extra':
                refs['joern05_unknown'] = self.adapters['joern05_packet']
            else:
                refs['executor']['sha256'] = '0' * 64
            with self.subTest(mode=mode), self.assertRaises(packet.AdapterError):
                self.prepare(refs=refs)

    def test_duplicate_path_hash_drift_and_symlink_rejected(self):
        refs = copy.deepcopy(self.adapters)
        refs['joern05_history'] = refs['joern05_packet']
        with self.assertRaises(packet.AdapterError):
            self.prepare(refs={**self.old['runtime_module_graph'], **refs}, adapters=refs)
        target = self.root / self.adapters['joern05_history']['path']
        raw = target.read_bytes()
        target.write_bytes(raw + b'\n')
        with self.assertRaises(packet.AdapterError):
            self.prepare()
        target.unlink()
        target.symlink_to(self.root / self.adapters['joern05_packet']['path'])
        with self.assertRaises(packet.AdapterError):
            self.prepare()

    def test_actual_parent_compact_child_producer_consumer(self):
        self.parent_child(self.prepare())

    def test_child_row_metadata_conflict_and_hash_tamper_rejected(self):
        for mode in ('row', 'hash'):
            graph = self.prepare()
            with self.subTest(mode=mode), self.assertRaises(Exception):
                self.parent_child(graph, mutate_child=lambda r: r.update(
                    {'rows': 108} if mode == 'row' else {'sha256': '0' * 64}))
            # Each case needs a fresh immutable writer namespace.
            shutil.rmtree(self.root / 'candidate/execution')

    def test_changed_parent_receipt_and_foreign_graph_rejected(self):
        graph = self.prepare()
        with self.assertRaises(Exception):
            self.parent_child(graph, mutate_parent=lambda r: r.update(ledger_rows=108))
        with self.assertRaises(packet.AdapterError):
            bridge.assert_graph95_core(self.root, graph,
                {'runtime_module_graph': self.old['runtime_module_graph'],
                 'adapter_module_refs': self.adapters})

    def test_runtime_io_error_restores_callback_and_retains_caller_fd(self):
        graph = self.prepare()
        core, manifest, ledger, lock, fd = self.fixture(graph)
        source = graph.module('joern05_stage_runtime')
        original = source.load_runtime_context
        def failed_io(root, core, *, graph, mode, ledger_bytes):
            raise RuntimeError('runtime evidence I/O failed')
        with mock.patch.object(source, 'load_runtime_context', failed_io):
            with self.assertRaisesRegex(RuntimeError, 'runtime evidence I/O failed'):
                graph.module('joern05_bridge').create_parent(
                    self.root, core, manifest, ledger, graph=graph,
                    lock_identity=lock, sidecars={}, runtime_role='joern05_stage_runtime',
                    runtime_ref=self.adapters['joern05_stage_runtime'])
        self.assertIs(source.load_runtime_context, original)
        os.fstat(fd)
        self.assertFalse((self.root / 'candidate/execution').exists())

    def test_child_error_restores_callback_and_retains_caller_fd(self):
        graph = self.prepare()
        source = graph.module('joern05_stage_runtime')
        original = source.load_runtime_context
        with self.assertRaises(Exception):
            self.parent_child(graph, mutate_child=lambda ref: ref.update(rows=108))
        self.assertIs(source.load_runtime_context, original)
        os.fstat(self.last_fixture_fd)
        self.assertFalse((self.root / 'candidate/execution/stages/stage-01.json').exists())

    def test_import_edges_sealed_and_foreign_caller_rejected(self):
        edges = bridge.adapter_import_edges()
        for bad in (edges[:-1], edges + [{'caller_role': 'joern05_packet',
                                         'target_role': 'joern05_history'}]):
            with self.assertRaises(packet.AdapterError):
                bridge.prepare_graph95(self.root, inherited_graph=self.graph88,
                    graph_refs=self.refs, adapter_refs=self.adapters, import_edges=bad)
        graph = self.prepare()
        importer = graph.module('joern05_history').__builtins__['__import__']
        with self.assertRaises(packet.AdapterError):
            importer('packet', {}, {}, ('require',), 0)
        with self.assertRaises(packet.AdapterError):
            importer('supervisor', graph.module('joern05_history').__dict__, {}, (), 0)
        self.assertIs(importer('packet', graph.module('joern05_history').__dict__,
                               {}, ('require',), 0), graph.module('joern05_packet'))

    def test_graph95_historical_body_uses_distinct88_and_restores_callbacks(self):
        graph = self.prepare()
        stage = self.graph88.module('stage_runtime11')
        protocol24 = self.graph88.module('protocol24')
        provider = self.graph88.module('incoming_recovery')
        originals = (stage._ACTIVE_RESUME, stage._incoming_recovery, stage.load_dependencies,
                     stage._read, protocol24.validate_resume_history)
        sentinel = RuntimeError('graph95 inherited recovery I/O sentinel')
        with mock.patch.object(provider, 'recover_bifrost_history', side_effect=sentinel):
            with self.assertRaisesRegex(Exception, 'inherited recovery I/O sentinel'):
                with graph.module('joern05_stage_runtime').historical_context_scope(
                        packet.ROOT, graph):
                    self.fail('real replay is outside this unit fixture')
        self.assertEqual(originals, (stage._ACTIVE_RESUME, stage._incoming_recovery,
                                    stage.load_dependencies, stage._read,
                                    protocol24.validate_resume_history))
        self.assertIs(bridge.inherited_view(graph), self.graph88)

    def test_close_restores_registry_and_error_disposes_new_modules(self):
        before = set(sys.modules)
        graph = self.prepare()
        names = {m.module_object.__name__ for m in graph.members if m.name in bridge.ADAPTER_ROLES}
        self.assertTrue(names <= set(sys.modules))
        bridge.close_graph95(graph)
        self.assertTrue(names.isdisjoint(sys.modules))
        self.assertTrue(before <= set(sys.modules))
        target = self.root / self.adapters['joern05_admission']['path']
        target.write_text(target.read_text() + '\nraise RuntimeError("private source execution sentinel")\n')
        refs = copy.deepcopy(self.adapters)
        refs['joern05_admission']['sha256'] = packet.digest(target.read_bytes())
        before = set(sys.modules)
        with self.assertRaisesRegex(RuntimeError, 'source execution sentinel'):
            self.prepare(refs={**self.old['runtime_module_graph'], **refs}, adapters=refs)
        self.assertEqual({n for n in sys.modules if n.startswith('_joern05_graph_')},
                         {n for n in before if n.startswith('_joern05_graph_')})


if __name__ == '__main__':
    unittest.main()
