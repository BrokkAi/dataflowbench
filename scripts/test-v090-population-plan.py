#!/usr/bin/env python3
"""Near-miss checks for the prospective common-release boundary."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('contract', Path(__file__).with_name('check-v090-population-plan.py'))
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class ContractTests(unittest.TestCase):
    def reject(self, path, change, message):
        original = contract.read
        def changed(root, relative):
            value = original(root, relative)
            if relative == path:
                value = copy.deepcopy(value)
                change(value)
            return value
        with patch.object(contract, 'read', changed):
            with self.assertRaisesRegex(ValueError, message):
                contract.validate()

    def test_exact_union(self):
        self.assertEqual(contract.validate()['cases'], 1108)

    def test_default104_cannot_replace_swift108(self):
        self.reject('populations/v0.9.0.json', lambda p: p.update(cases=[c for c in p['cases'] if not c['path'].startswith('populations/swift-opaque-v3/')]), 'exact historical union')

    def test_duplicate_partition(self):
        self.reject('reports/releases/v0.9.0/plan.json', lambda p: p['reports'][1].update(id=p['reports'][0]['id']), 'partition denominator')

    def test_historical_output_overwrite(self):
        def overwrite(plan):
            plan['reports'][0]['report'] = 'reports/bifrost-c-kernel.json'
            plan['execution_groups'][0]['reports'] = ['reports/bifrost-c-kernel.json']
        self.reject('reports/releases/v0.9.0/plan.json', overwrite, 'output must be versioned')

    def test_no_accidental_execution(self):
        self.reject('reports/releases/v0.9.0/plan.json', lambda p: p.update(status='executable'), 'cannot authorize execution')

    def test_membership_hash_is_checked(self):
        self.reject('reports/releases/v0.9.0/plan.json', lambda p: p['reports'][0]['case_membership'].update(sha256='0'*64), 'membership binding')


if __name__ == '__main__':
    unittest.main()
