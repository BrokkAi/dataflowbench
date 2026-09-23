#!/usr/bin/env python3
"""Mutation controls for pending native integration scope and attribution."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('integration', Path(__file__).with_name('verify-swift-native-integration.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContractTests(unittest.TestCase):
    def test_retained_configuration(self):
        self.assertEqual(m.verify()['scored_outcomes'], 0)

    def test_scope_and_promotion_mutations(self):
        activation = m.read(m.ROOT / m.BASE / 'activation.json')
        partition = m.read(m.ROOT / m.BASE / 'partition.json')
        population = m.read(m.ROOT / 'populations/swift-synthetic-v2.json')
        mutations = [
            lambda a, p: a.update(scored_activation=True),
            lambda a, p: a.update(status='active'),
            lambda a, p: a.update(qualified_outcomes=1),
            lambda a, p: a.update(aggregate_memory_compliance='verified'),
            lambda a, p: a['query_profiles'].update({'adapter-assisted': 'vendor-native'}),
            lambda a, p: a['joern'].update(normalized_outcome='unsupported'),
            lambda a, p: a.update(version='2.27.0'),
            lambda a, p: a.update(unresolved_modeling_templates=[]),
            lambda a, p: p.update(fixture_revision='wrong'),
            lambda a, p: p['cases'].pop(),
            lambda a, p: p['cases'][0].update(decision='execute'),
            lambda a, p: p.update(first_qualification_cases=[p['first_qualification_cases'][0]]),
            lambda a, p: p.update(lanes=['vendor-native']),
        ]
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                a, p = copy.deepcopy(activation), copy.deepcopy(partition)
                mutation(a, p)
                with self.assertRaises(ValueError):
                    m.verify_contract(a, p, population)


if __name__ == '__main__':
    unittest.main()
