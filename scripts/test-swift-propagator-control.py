#!/usr/bin/env python3
"""Non-vacuous identity/transfer guards for the independent append control."""
import copy
import json
import shutil
import tempfile
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('control', Path(__file__).with_name('verify-swift-propagator-control.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class ControlTests(unittest.TestCase):
    def test_retained(self):
        self.assertEqual(m.verify()['status'], 'blocked')

    def test_semantic_mutations(self):
        plan = m.read(m.BASE / 'control-plan.json')
        base = m.BASE / 'control-attempt-01/probe'
        rows = [m.read(base / (name + '.json'))['#select']['tuples']
                for name in ['append-identity', 'append-transfer', 'roles', 'flow']]
        with self.assertRaisesRegex(ValueError, 'independent positive and separating controls'):
            m.check_rows(*rows, plan)
        # A synthetic passing set isolates each guard; retained failed rows stay untouched.
        rows[3] = [r for r in rows[3] if r[1] == plan['control_labels']['POSITIVE_SINK']]
        m.check_rows(*rows, plan)
        mutations = [
            lambda x: x[0].pop(),
            lambda x: x[1].clear(),
            lambda x: x[1][0].__setitem__(5, 'invented-origin'),
            lambda x: x[3].clear(),
            lambda x: x[3].append([plan['control_labels']['SOURCE'], plan['control_labels']['SAFE_SINK'], 87, 'adapter-corrected']),
            lambda x: x[0][0].__setitem__(7, False),
        ]
        for number, mutation in enumerate(mutations):
            with self.subTest(number=number):
                changed = copy.deepcopy(rows); mutation(changed)
                with self.assertRaises(ValueError):
                    m.check_rows(*changed, plan)


class PortableMutations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dfb-append-evidence-')
        self.addCleanup(self.temp.cleanup)
        self.old_base = m.BASE
        m.BASE = Path(self.temp.name) / 'evidence'
        self.addCleanup(setattr, m, 'BASE', self.old_base)
        shutil.copytree(self.old_base, m.BASE)

    def mutate(self, directory, filename, change):
        path = m.BASE / directory / filename
        value = m.read(path)
        change(value)
        path.write_text(json.dumps(value))
        root = m.BASE / directory
        (root / 'manifest.json').write_text(json.dumps({
            str(p.relative_to(root)): m.sha(p) for p in root.rglob('*')
            if p.is_file() and p != root / 'manifest.json'}))

    def test_false_flow_cannot_be_erased(self):
        self.mutate('control-attempt-01', 'probe/flow.json',
                    lambda v: v['#select'].update(tuples=[r for r in v['#select']['tuples'] if r[1] == 14]))
        with self.assertRaisesRegex(ValueError, 'silently requalified'):
            m.verify()

    def test_diagnosis_cannot_be_promoted(self):
        self.mutate('heuristic-attempt-01', 'run.json', lambda v: v.update(scored_activation=True))
        with self.assertRaisesRegex(ValueError, 'diagnosis scope'):
            m.verify()

    def test_heuristic_witness_cannot_be_empty(self):
        self.mutate('heuristic-attempt-01', 'heuristic.json', lambda v: v['#select'].update(tuples=[]))
        with self.assertRaisesRegex(ValueError, 'nonvacuous additional-step'):
            m.verify()

    def test_path_provenance_cannot_be_invented(self):
        self.mutate('trace-attempt-02', 'path.json', lambda v: v['edges'].update(tuples=[]))
        with self.assertRaisesRegex(ValueError, 'native edge provenance'):
            m.verify()


if __name__ == '__main__':
    unittest.main()
