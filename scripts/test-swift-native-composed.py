#!/usr/bin/env python3
import unittest
from swift_native_composed import collect, PROFILE
from swift_integration_v3 import normalize

class Collection(unittest.TestCase):
    def setUp(self):
        self.case={'id':'fixture','template_id':'dfb-template-native-persistence','polarity':'negative',
                   'source_anchors':[{'line_hint':4}], 'sink_anchors':[{'line_hint':9}],
                   'execution_budget':{'wall_clock_seconds':60,'peak_memory_mb':512}}
        self.roles=[[4,15,PROFILE,'environment'],[9,80,PROFILE,'sink']]
    def test_unexpected_negative_flow_retained(self):
        flows=[[4,9,80,PROFILE]]
        row=collect(self.case,self.roles,flows)
        self.assertEqual(row['outcome'],'reached');self.assertEqual(row['findings'],flows)
    def test_positive_absence_is_observation(self):
        self.case['polarity']='positive'
        self.assertEqual(collect(self.case,self.roles,[])['outcome'],'not-reached')
    def test_off_anchor_flow_retained_but_not_scored(self):
        flows=[[4,12,80,PROFILE]];row=collect(self.case,self.roles,flows)
        self.assertEqual(row['outcome'],'not-reached');self.assertEqual(row['findings'],flows)
    def test_missing_endpoint_not_clean(self):
        row=collect(self.case,self.roles[:1],[])
        self.assertFalse(row['endpoints_verified']);self.assertEqual(normalize(self.case,row)['outcome'],'runner-error')
    def test_foreign_profile_rejected(self):
        with self.assertRaisesRegex(ValueError,'flow row'):collect(self.case,self.roles,[[4,9,80,'vendor-native']])
    def test_incomplete_coverage_retained(self):
        row=collect(self.case,self.roles,[],[[3,'Incomplete','IncompleteInitialState',8]],[3])
        self.assertIn('IncompleteInitialState',normalize(self.case,row)['diagnostics'])
    def test_malformed_flow_rejected(self):
        for flows in [[[True,9,80,PROFILE]],[[4,9]],[[4,9,0,PROFILE]]]:
            with self.assertRaisesRegex(ValueError,'flow row'):collect(self.case,self.roles,flows)

if __name__=='__main__':unittest.main(verbosity=2)
