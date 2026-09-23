#!/usr/bin/env python3
import copy
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('verify', Path(__file__).with_name('verify-swift-joern-identity.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)


class IdentityEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.graph = v.read(v.EVIDENCE / 'attempt-02/graph.json')

    def test_observed_gap_and_positive_controls(self):
        v.check_graph(self.graph, 2)

    def test_new_external_binding_invalidates_stale_blocker(self):
        graph = copy.deepcopy(self.graph)
        v.field(graph['nodes'], 25, 'environment')['ref'] = ['new-binding']
        with self.assertRaises(AssertionError): v.check_graph(graph, 2)

    def test_missing_real_node_cannot_prove_gap(self):
        graph = copy.deepcopy(self.graph); node = v.field(graph['nodes'], 25, 'environment')
        graph['nodes'].remove(node)
        with self.assertRaises(AssertionError): v.check_graph(graph, 2)

    def test_missing_local_binding_invalidates_control(self):
        graph = copy.deepcopy(self.graph)
        v.field(graph['nodes'], 36, 'environment')['ref'] = []
        with self.assertRaises(AssertionError): v.check_graph(graph, 2)

    def test_owner_type_change_requires_review(self):
        graph = copy.deepcopy(self.graph)
        v.field(graph['nodes'], 26, 'arguments')['properties']['TYPE_FULL_NAME'] = 'Swift.Array'
        with self.assertRaises(AssertionError): v.check_graph(graph, 2)


if __name__ == '__main__': unittest.main()
