#!/usr/bin/env python3
"""Mutation guards for retained blocked sanitizer evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verifier', Path(__file__).with_name('verify-swift-sanitizer-control.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Controls(unittest.TestCase):
    def test_retained(self):
        self.assertEqual(m.verify()['status'], 'blocked')

    def test_semantics(self):
        plan = m.read(m.BASE / 'control-plan.json')
        rows = [m.read(m.BASE / 'diagnosis-attempt-01' / (n + '.json'))['#select']['tuples']
                for n in ['conversion-identity', 'barriers', 'numeric-bases']]
        rows += [m.read(m.BASE / 'control-attempt-01/probe' / (n + '.json'))['#select']['tuples'] for n in ['roles', 'flow']]
        with self.assertRaisesRegex(ValueError, 'spurious local'):
            m.check_rows(*rows, plan)
        for r in rows[1]:
            if r[2:4] == [m.LOCAL, 'Int']:
                r[4] = False
        with self.assertRaisesRegex(ValueError, 'missing independent'):
            m.check_rows(*rows, plan)
        rows[4] += [[17, 27, 87, 'adapter-corrected'], [17, 31, 87, 'adapter-corrected']]
        m.check_rows(*rows, plan)
        for mutation in [lambda r: r[0].pop(), lambda r: r[0][0].__setitem__(4, 'Int'),
                         lambda r: r[1].clear(), lambda r: r[2].clear(),
                         lambda r: r[3].clear(), lambda r: r[4].pop()]:
            changed = copy.deepcopy(rows)
            mutation(changed)
            with self.assertRaises(ValueError):
                m.check_rows(*changed, plan)

    def test_retained_mutations(self):
        changes = [
            ('control-attempt-01', 'probe/flow.json', lambda v: v['#select'].update(tuples=[])),
            ('diagnosis-attempt-01', 'run.json', lambda v: v.update(scored_activation=True)),
            ('diagnosis-attempt-01', 'numeric-bases.json', lambda v: v['#select'].update(tuples=[])),
            ('diagnosis-attempt-01', 'conversion-identity.json', lambda v: v['#select']['tuples'][0].__setitem__(4, 'Int')),
        ]
        original = m.BASE
        for directory, filename, mutation in changes:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                m.BASE = Path(tmp) / 'evidence'
                try:
                    shutil.copytree(original, m.BASE)
                    root = m.BASE / directory
                    path = root / filename
                    value = m.read(path)
                    mutation(value)
                    path.write_text(json.dumps(value))
                    (root / 'manifest.json').write_text(json.dumps({str(p.relative_to(root)): m.sha(p)
                        for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json'}))
                    with self.assertRaises(ValueError):
                        m.verify()
                finally:
                    m.BASE = original


if __name__ == '__main__':
    unittest.main()
