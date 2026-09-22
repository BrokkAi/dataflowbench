#!/usr/bin/env python3
"""Adversarial regression tests over retained native Swift evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from joern_swift import ROOT, normalize


class NativeGuards(unittest.TestCase):
    def setUp(self):
        root=ROOT/'evidence/joern-swift/model-activation-219/attempt-03/direct-negative/on'
        self.graph=json.loads((root/'graph.json').read_text())
        self.config=json.loads((root/'config.json').read_text())

    def check_bad(self,graph):
        self.assertEqual(normalize(graph,self.config)[0],'runner-error')

    def test_native_near_miss(self):
        self.assertEqual(normalize(self.graph,self.config)[0],'not-reached')

    def test_missing_overlay_or_empty_graph_is_not_clean(self):
        for field,value in [('metadata',[]),('methods',[]),('source_observations',[]),('sink_observations',[]),('complete',False)]:
            graph=copy.deepcopy(self.graph);graph[field]=value;self.check_bad(graph)

    def test_same_name_wrong_native_callee_is_rejected(self):
        graph=copy.deepcopy(self.graph)
        identifier=graph['source_observations'][0]['id']
        call=next(c for c in graph['calls'] if c['node']['id']==identifier)
        call['callee_ids']=graph['sink_method_ids']
        self.check_bad(graph)

    def test_ambiguous_edge_is_rejected_even_with_correct_target(self):
        graph=copy.deepcopy(self.graph)
        identifier=graph['source_observations'][0]['id']
        call=next(c for c in graph['calls'] if c['node']['id']==identifier)
        call['callee_ids']+=graph['sink_method_ids']
        self.check_bad(graph)

    def test_forged_observation_id_and_wrong_file(self):
        for change in [{'id':'999999'}, {'file':'decoy/main.swift'}, {'line':999}]:
            graph=copy.deepcopy(self.graph);graph['source_observations'][0].update(change);self.check_bad(graph)

    def test_unproven_flow_endpoints_are_rejected(self):
        graph=copy.deepcopy(self.graph)
        graph['flows']=[[{'id':'999999'},graph['sink_nodes'][0]]]
        self.check_bad(graph)

    def test_missing_source_node_is_not_a_negative(self):
        graph=copy.deepcopy(self.graph);graph['source_nodes']=[];self.check_bad(graph)

    def test_wrong_sink_argument_is_rejected(self):
        graph=copy.deepcopy(self.graph);graph['sink_nodes'][0]['id']='999999';self.check_bad(graph)

    def test_model_mismatch_is_rejected(self):
        graph=copy.deepcopy(self.graph);graph['semantics']=[];self.check_bad(graph)

    def test_source_node_cannot_be_substituted_by_name(self):
        graph=copy.deepcopy(self.graph);graph['source_nodes'][0]['id']='999999';self.check_bad(graph)

    def test_supported_root_negative_can_have_no_declared_source_call(self):
        root=ROOT/'evidence/joern-swift/model-activation-219/attempt-03/source-sibling/on'
        graph=json.loads((root/'graph.json').read_text());config=json.loads((root/'config.json').read_text())
        self.assertFalse(graph['source_nodes'])
        self.assertEqual(normalize(graph,config)[0],'not-reached')
        graph['source_observations']=[]
        self.assertEqual(normalize(graph,config)[0],'runner-error')


if __name__=='__main__':unittest.main()
