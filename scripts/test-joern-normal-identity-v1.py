#!/usr/bin/env python3
"""Native identity replay near-misses; never launch an analyzer."""
import copy
import importlib.util
import unittest
from pathlib import Path
from swift_normal_reports_v1 import ROOT,read
spec=importlib.util.spec_from_file_location('identity_replay',Path(__file__).with_name('check-joern-normal-identity-v1.py'))
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)


class IdentityReplay(unittest.TestCase):
    def test_retained_diagnosis(self):
        self.assertEqual(replay.verify()['inspected_cpgs'],1)

    def test_endpoint_ids_and_external_status_cannot_be_substituted(self):
        inventory=read(ROOT/replay.EVIDENCE/'inventory.json');result=read(ROOT/replay.EVIDENCE/'result.json')
        for label in ('source','sink'):
            bad=copy.deepcopy(result);bad[label]['anchored_call']['callee_ids']=[bad[label]['internal_declaration']['id']]
            with self.assertRaisesRegex(ValueError,'inventory drift'):replay.validate_inventory(inventory,bad)
            bad=copy.deepcopy(inventory)
            for m in bad['methods']:
                if m['id']==result[label]['actual_callee']['id']:m['external']=False
            with self.assertRaisesRegex(ValueError,'inventory drift'):replay.validate_inventory(bad,result)

    def test_native_owner_edge_required_and_duplicate_ids_reject(self):
        inventory=read(ROOT/replay.EVIDENCE/'inventory.json');result=read(ROOT/replay.EVIDENCE/'result.json')
        bad=copy.deepcopy(inventory);bad['type_declarations'][0]['method_ids']=[]
        with self.assertRaisesRegex(ValueError,'owner edge'):replay.validate_inventory(bad,result)
        bad=copy.deepcopy(inventory);bad['methods'].append(copy.deepcopy(bad['methods'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):replay.validate_inventory(bad,result)


if __name__=='__main__':unittest.main()
