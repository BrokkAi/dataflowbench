#!/usr/bin/env python3
"""Current108 prospective membership, decision provenance and capacity guards."""
import copy
import unittest
from unittest.mock import patch
from joern_normal_runner_v1 import ROOT,read,verify_activation,preflight,capacity,RESERVE,SCRATCH
from swift_normal_reports_v1 import bound_file,sha,load_population,configuration_hash

PLAN='adapters/joern/swift-normal-v1/plan-2026-09-28-04/plan.json'
class Plan(unittest.TestCase):
    def test_exact_membership_and_fresh_decisions(self):
        plan=read(ROOT/PLAN);verify_activation(ROOT,plan);_,cases,digest=load_population(ROOT)
        self.assertEqual(set(plan['cases']),set(cases))
        attempts=[i for i,c in plan['cases'].items() if c['disposition']=='attempt'];self.assertEqual(len(attempts),96)
        config=configuration_hash(ROOT,plan['configurations']['joern-current108'])
        for identity,case in cases.items():
            entry=plan['cases'][identity]
            if case['model_profile']=='benchmark-controlled':
                self.assertEqual(entry['capability'],{'identity_gate':'exact-native-edges','model_status':'unqualified','model_mode':'off'})
            else:
                self.assertEqual(entry['disposition'],'unsupported');decision=read(bound_file(ROOT,entry['decision']))
                self.assertEqual(decision['case_id'],identity);self.assertEqual(decision['population_sha256'],digest);self.assertEqual(decision['configuration_hash'],config)
                self.assertEqual(decision['identity'],plan['identity']);self.assertLessEqual(decision['reviewed_at_unix_seconds'],plan['registered_at_unix_seconds'])
                for reference in decision['evidence']:bound_file(ROOT,reference)
                for reference in decision['current_fixture_digests']:bound_file(ROOT,reference)

    def test_44gib_launch_and_40gib_running_reserve(self):
        self.assertEqual(RESERVE,40*1024**3);self.assertEqual(SCRATCH,4*1024**3)
        capacity(44*1024**3,True);capacity(40*1024**3)
        for free,launch in [(44*1024**3-1,True),(40*1024**3-1,False)]:
            with self.assertRaises(ValueError):capacity(free,launch)

    def test_exact_plan_reservation_live_capacity_and_resource_drift(self):
        plan=read(ROOT/PLAN);reservation={'plan_sha256':sha(ROOT/PLAN),'exclusive_analyzer_slot':True,'launch_free_bytes':RESERVE+SCRATCH}
        with patch('joern_normal_runner_v1.registered'),patch('joern_normal_runner_v1.verify_runtime'),patch('joern_normal_runner_v1.shutil.disk_usage') as disk:
            disk.return_value.free=RESERVE+SCRATCH
            preflight(ROOT,PLAN,reservation)
            for field,value in [('plan_sha256','0'*64),('exclusive_analyzer_slot',False),('launch_free_bytes',RESERVE+SCRATCH-1)]:
                bad=dict(reservation);bad[field]=value
                with self.assertRaisesRegex(ValueError,'reservation'):preflight(ROOT,PLAN,bad)
            disk.return_value.free=RESERVE+SCRATCH-1
            with self.assertRaisesRegex(ValueError,'Capacity'):preflight(ROOT,PLAN,reservation)
        bad=copy.deepcopy(plan);bad['resources']['scratch_allowance_bytes']=2*1024**3
        with patch('joern_normal_runner_v1.read',return_value=bad):
            with self.assertRaisesRegex(ValueError,'resource policy'):preflight(ROOT,PLAN,reservation)

if __name__=='__main__':unittest.main()
