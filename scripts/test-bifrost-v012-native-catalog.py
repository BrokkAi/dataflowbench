#!/usr/bin/env python3
"""Check zero-configuration catalog selection against immutable failed evidence."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'reports/releases/v0.9.0/execution-v1/resume-20261007-02/native-failure-evidence'
class CatalogTests(unittest.TestCase):
    def test_exact_default_membership_and_distinct_opt_in_policies(self):
        catalog=json.loads((EVIDENCE/'builtin-policy-catalog.json').read_text())
        report=json.loads((EVIDENCE/'scan/java-native-entrypoint-negative.full.json').read_text())
        policies=[p for pack in catalog['packs'] for p in pack['policies']]
        self.assertEqual({p['activation'] for p in policies},{'default','opt-in'})
        defaults={p['id'] for p in policies if p['activation']=='default'}
        optional={p['id'] for p in policies if p['activation']=='opt-in'}
        self.assertEqual(len(defaults),44);self.assertEqual(len(optional),26)
        self.assertFalse(defaults & optional)
        self.assertEqual(len(report['runs']),len(defaults))
        self.assertEqual({r['policy_id'] for r in report['runs']},defaults)
        self.assertIn('inconclusive',{r['completion']['type'] for r in report['runs']})
        source=(ROOT/'scripts/probe-bifrost-scan-native-v012.sh').read_text()
        block=source.split('expected_ids = {',1)[1].split('completion_types =',1)[0]
        namespace={'catalog':catalog,'report':report,'language':'java','fixture':'retained'}
        exec('expected_ids = {'+block,namespace)
        for mutate in ('missing','duplicate','unexpected'):
            changed=json.loads(json.dumps(report))
            if mutate=='missing':changed['runs'].pop()
            elif mutate=='duplicate':changed['runs'].append(changed['runs'][0])
            else:changed['runs'][0]['policy_id']=next(iter(optional))
            with self.subTest(mutate=mutate),self.assertRaises(AssertionError):
                exec('expected_ids = {'+block,{**namespace,'report':changed})
        catalog['packs'][0]['policies'][0]['activation']='unknown'
        with self.assertRaises(AssertionError):exec('expected_ids = {'+block,namespace)
if __name__=='__main__':unittest.main()
