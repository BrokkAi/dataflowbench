"""Actual module execution and inherited88+adapter7 teardown; no runtime replay."""
import sys
import types
import unittest
from unittest import mock
import packet
import bridge
import test_graph95 as fixtures


class OwnershipTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.Graph95Tests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.Graph95Tests.tearDownClass.__func__)
    setUp = fixtures.Graph95Tests.setUp
    artifact = fixtures.Graph95Tests.artifact

    def core(self):
        return {'runtime_module_graph': self.refs,
                'adapter_module_refs': self.adapters,
                'adapter_import_edges': bridge.adapter_import_edges()}

    def test_failed_execution_own_and_foreign_identity(self):
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                source = 'import sys, types\n'
                if replacement:
                    source += "sys.modules[__name__]=types.ModuleType('foreign')\n"
                source += "raise RuntimeError('original-body-error')\n"
                ref = self.artifact('failure.py', source.encode())
                name = '_joern05_failed_ownership_test'
                try:
                    with self.assertRaisesRegex(RuntimeError, 'original-body-error') as caught:
                        packet.load_bound_module(self.root, name, ref)
                    if replacement:
                        self.assertEqual(sys.modules[name].__name__, 'foreign')
                        self.assertIn('identity changed', caught.exception.adapter_cleanup_errors[0]['message'])
                    else:
                        self.assertNotIn(name, sys.modules)
                finally:
                    sys.modules.pop(name, None)

    def test_actual_scope_two_entries_closes_inherited_after_adapter_before_hosts(self):
        before = dict(sys.modules)
        for _ in range(2):
            with packet.prepare_current_graph(self.root, self.core()) as graph:
                old = bridge.inherited_view(graph)
                self.assertFalse(old.import_context._closed)
                host_names = [n for n in sys.modules if n.startswith('_joern05_boot_')]
                adapter_names = [m.module_object.__name__ for m in graph.members if m.name in bridge.ADAPTER_ROLES]
                original = old.import_context.close_on_error
                seen = []
                def close():
                    self.assertTrue(all(n in sys.modules for n in host_names))
                    self.assertTrue(all(n not in sys.modules for n in adapter_names))
                    seen.append(True)
                    original()
                # Instance method override is a teardown-order observation only.
                old.import_context.close_on_error = close
            self.assertEqual(seen, [True])
            self.assertTrue(old.import_context._closed)
            self.assertTrue(all(n not in sys.modules for n in host_names))
        for name, value in before.items():
            self.assertIs(sys.modules.get(name), value)

    def test_foreign_host_and_unknown_addition_fail_preserved(self):
        for kind in ('host', 'unknown'):
            name = None
            foreign = types.ModuleType('foreign_ownership')
            try:
                with self.subTest(kind=kind), self.assertRaises(Exception):
                    with packet.prepare_current_graph(self.root, self.core()):
                        name = (next(n for n in sys.modules if n.startswith('_joern05_boot_') and n.endswith('_protocol24'))
                                if kind == 'host' else '_joern05_unknown_foreign')
                        sys.modules[name] = foreign
                self.assertIs(sys.modules[name], foreign)
            finally:
                if name is not None:
                    sys.modules.pop(name, None)

    def test_adapter_foreign_and_cross_role_replacement_fail_preserved(self):
        for kind in ('foreign', 'cross-role'):
            name = None
            try:
                with self.subTest(kind=kind), self.assertRaisesRegex(Exception, 'registration identity changed'):
                    with packet.prepare_current_graph(self.root, self.core()) as graph:
                        module = graph.module('joern05_packet')
                        name = module.__name__
                        foreign = (types.ModuleType('foreign') if kind == 'foreign'
                                   else graph.module('joern05_history'))
                        sys.modules[name] = foreign
                self.assertIs(sys.modules[name], foreign)
            finally:
                if name is not None:
                    sys.modules.pop(name, None)

    def test_original_operation_error_stays_primary_with_cleanup_diagnostic(self):
        name = '_joern05_unknown_foreign'
        foreign = types.ModuleType('foreign')
        try:
            with self.assertRaisesRegex(RuntimeError, 'original-operation') as caught:
                with packet.prepare_current_graph(self.root, self.core()):
                    sys.modules[name] = foreign
                    raise RuntimeError('original-operation')
            self.assertIs(sys.modules[name], foreign)
            self.assertTrue(caught.exception.adapter_cleanup_errors)
            self.assertFalse(any(n.startswith('_joern05_boot_') for n in sys.modules))
        finally:
            sys.modules.pop(name, None)

    def test_partial_graph95_preparation_closes_inherited_and_hosts(self):
        seen = []
        def reject(root, *, inherited_graph, **kwargs):
            seen.append(inherited_graph)
            raise RuntimeError('preparation-sentinel')
        # Preserve the real pre-baseline source/owner check. Only subsequent
        # graph95 preparation is substituted to exercise partial teardown.
        original_bootstrap = packet.bootstrap_bridge
        original_prepare = bridge.prepare_graph95
        def verified_then_reject(root, core):
            result = original_bootstrap(root, core)
            result.prepare_graph95 = reject
            return result
        try:
            with mock.patch.object(packet, 'bootstrap_bridge', side_effect=verified_then_reject):
                with self.assertRaisesRegex(RuntimeError, 'preparation-sentinel'):
                    with packet.prepare_current_graph(self.root, self.core()):
                        self.fail('must not enter')
        finally:
            bridge.prepare_graph95 = original_prepare
        self.assertTrue(seen[0].import_context._closed)
        self.assertFalse(any(n.startswith('_joern05_boot_') for n in sys.modules))


if __name__ == '__main__':
    unittest.main()
