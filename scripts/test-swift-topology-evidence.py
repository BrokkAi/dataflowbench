#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('topology',Path(__file__).with_name('check-swift-topology-evidence.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Topology(unittest.TestCase):
    def rows(self):
        return [[kind,top,'module' if kind!='top-body' else 'body'+top,count] for top in ['a','b'] for kind,count in [('top-body',-1),('top-parent-count',0),('top-membership-count',0)]]

    def test_missing_sequence_is_diagnostic_not_registry_outcome(self):
        result=module.classify_topology(self.rows());self.assertEqual(result['status'],'MissingTopLevelSequence');self.assertFalse(result['registry_outcome_changed'])

    def test_relationships_do_not_automatically_certify_order(self):
        rows=self.rows();rows[1][3]=1
        self.assertEqual(module.classify_topology(rows)['status'],'StructuralRelationshipsRequireSemanticReview')

    def test_incomplete_counts_do_not_prove_absence(self):
        with self.assertRaisesRegex(ValueError,'complete structural'):
            module.classify_topology(self.rows()[:-1])

    def test_location_labels_do_not_choose_order(self):
        rows=self.rows();a=module.classify_topology(rows)
        for row in rows:row[1]={'a':'Top@900','b':'Top@1'}[row[1]]
        self.assertEqual(module.classify_topology(list(reversed(rows))),a)

if __name__=='__main__':unittest.main(verbosity=2)
