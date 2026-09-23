#!/usr/bin/env python3
"""Mutation controls for blocked UserDefaults evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verifier', Path(__file__).with_name('verify-swift-persistence-control.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Controls(unittest.TestCase):
    def test_retained(self):
        self.assertEqual(m.verify()['status'], 'blocked')

    def test_semantics(self):
        plan = m.read(m.BASE / 'control-plan.json')
        p = m.BASE / 'control-attempt-01/probe'
        rows = [m.read(p / (n + '.json'))['#select']['tuples'] for n in
            ['persistence-identity', 'persistence-keys', 'persistence-ports', 'persistence-edges', 'roles', 'flow']]
        with self.assertRaisesRegex(ValueError, 'missing persistence model engagement'):
            m.check_qualification(*rows, plan)
        with self.assertRaisesRegex(ValueError, 'missing real same-key flow'):
            m.check_flows(rows[5], rows[4], plan)
        # Synthetic rows exercise the original gate; these are not native evidence.
        required = {plan['control_labels'][n] for n in plan['expectations']['real_engagement_labels']}
        for r in rows[0]:
            if r[0] in required:
                r[7] = True
        rows[2] = [[line, 'synthetic', 'synthetic', False, ''] for line in required]
        rows[3] = [[line, line, 1, line, 1, 'synthetic'] for line in required]
        rows[5] += [[12, 16, 87, 'adapter-corrected']]
        m.check_qualification(*rows, plan)
        for mutation in [lambda r: r[0].pop(), lambda r: r[0][0].__setitem__(2, 'Swift'),
                         lambda r: r[1][0].__setitem__(4, 'other'), lambda r: r[1].pop(),
                         lambda r: r[2].clear(), lambda r: r[3].clear(), lambda r: r[5].pop(),
                         lambda r: r[5].append([12, 18, 87, 'adapter-corrected'])]:
            changed = copy.deepcopy(rows); mutation(changed)
            with self.assertRaises(ValueError):
                m.check_qualification(*changed, plan)

    def test_copied_evidence_mutations(self):
        changes = [
            ('probe/flow.json', lambda v: v['#select'].update(tuples=[])),
            ('probe/persistence-keys.json', lambda v: v['#select']['tuples'][3].__setitem__(4, 'other')),
            ('probe/persistence-identity.json', lambda v: v['#select']['tuples'][3].__setitem__(7, True)),
            ('run.json', lambda v: v.update(scored_activation=True)),
        ]
        original = m.BASE
        for filename, mutation in changes:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                m.BASE = Path(tmp) / 'evidence'
                try:
                    shutil.copytree(original, m.BASE)
                    root = m.BASE / 'control-attempt-01'; path = root / filename
                    value = m.read(path); mutation(value); path.write_text(json.dumps(value))
                    (root / 'manifest.json').write_text(json.dumps({str(p.relative_to(root)): m.sha(p)
                        for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json'}))
                    with self.assertRaises(ValueError):
                        m.verify()
                finally:
                    m.BASE = original


if __name__ == '__main__':
    unittest.main()
