#!/usr/bin/env python3
"""Mutation guards for blocked Data summary evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verifier', Path(__file__).with_name('verify-swift-summary-control.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Controls(unittest.TestCase):
    def test_retained(self):
        self.assertEqual(m.verify()['status'], 'blocked')

    def test_semantics(self):
        plan = m.read(m.BASE / 'control-plan.json')
        p = m.BASE / 'control-attempt-01/probe'
        identities, ports, transfers, roles, flows = [m.read(p / (n + '.json'))['#select']['tuples']
            for n in ['summary-identity', 'summary-ports', 'summary-transfer', 'roles', 'flow']]
        stores = m.read(m.BASE / 'store-attempt-01/summary-store.json')['#select']['tuples']
        rows = [identities, ports, transfers, stores, roles, flows]
        with self.assertRaisesRegex(ValueError, 'constant-body summary overreach'):
            m.check_qualification(*rows, plan)
        with self.assertRaisesRegex(ValueError, 'false flow'):
            m.check_flows(flows, roles, plan)
        # Synthetic passing rows isolate each guard without modifying retained files.
        for r in rows[0]:
            if r[0] >= 23:
                r[7] = False
        for index in [1, 2, 3]:
            rows[index] = [r for r in rows[index] if r[0] < 23]
        rows[5] = [flows[0]]
        m.check_qualification(*rows, plan)
        for mutation in [lambda r: r[0].pop(), lambda r: r[0][0].__setitem__(2, 'Swift'),
                         lambda r: r[1][0].__setitem__(3, 'invented'), lambda r: r[2].clear(),
                         lambda r: r[3].clear(), lambda r: r[4].clear(), lambda r: r[5].clear()]:
            changed = copy.deepcopy(rows)
            mutation(changed)
            with self.assertRaises(ValueError):
                m.check_qualification(*changed, plan)

    def test_copied_evidence_mutations(self):
        changes = [
            ('control-attempt-01', 'probe/flow.json', lambda v: v['#select'].update(tuples=[[12, 17, 87, 'adapter-corrected']])),
            ('control-attempt-01', 'probe/summary-ports.json', lambda v: v['#select']['tuples'][0].__setitem__(3, 'invented')),
            ('store-attempt-01', 'summary-store.json', lambda v: v['#select'].update(tuples=[])),
            ('store-attempt-01', 'run.json', lambda v: v.update(scored_activation=True)),
        ]
        original = m.BASE
        for directory, filename, mutation in changes:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                m.BASE = Path(tmp) / 'evidence'
                try:
                    shutil.copytree(original, m.BASE)
                    root = m.BASE / directory
                    path = root / filename
                    value = m.read(path); mutation(value); path.write_text(json.dumps(value))
                    (root / 'manifest.json').write_text(json.dumps({str(p.relative_to(root)): m.sha(p)
                        for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json'}))
                    with self.assertRaises(ValueError):
                        m.verify()
                finally:
                    m.BASE = original


if __name__ == '__main__':
    unittest.main()
