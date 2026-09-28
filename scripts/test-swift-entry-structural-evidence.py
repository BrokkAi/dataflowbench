#!/usr/bin/env python3
"""Mutate retained native rows without changing immutable evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest

spec = importlib.util.spec_from_file_location('structural', Path(__file__).with_name('check-swift-entry-structural-evidence.py'))
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class StructuralEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tarfile.open(verifier.EVIDENCE / 'portable-evidence.tar.gz') as archive:
            cls.files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
        cls.prefix = 'structural-attempt-01/'
        cls.plan = cls.read('preregistration.json')
        cls.control = cls.plan['controls'][0]

    @classmethod
    def read(cls, path):
        return json.loads(cls.files[cls.prefix + path])

    def test_retained_rows(self):
        verifier.validate_facts(self.read('branch/structure.json')['#select']['tuples'], self.plan, self.control)
        verifier.validate_identities(self.read('branch/identity-all.json')['#select']['tuples'], self.control)

    def test_fact_duplicate_conflicting_missing_unknown_and_malformed(self):
        original = self.read('branch/structure.json')['#select']['tuples']
        mutations = [original + [original[0]], original + [[original[0][0], 99]], original[1:], original + [['foreign', 0]], original + [['entries']], original + [None]]
        for value in [True, False, -1, 1.0, '1', None]:
            rows = copy.deepcopy(original)
            rows[0][1] = value
            mutations.append(rows)
        for rows in mutations:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                verifier.validate_facts(rows, self.plan, self.control)

    def test_identity_mutations(self):
        for kind in ['gap', 'duplicate-index', 'boolean-index', 'duplicate-declaration', 'duplicate-body', 'foreign-owner', 'boolean-id', 'missing-row']:
            rows = self.read('branch/identity-all.json')['#select']['tuples']
            if kind == 'gap': rows[1][3] = 20
            if kind == 'duplicate-index': rows[1][3] = rows[0][3]
            if kind == 'boolean-index': rows[0][3] = False
            if kind == 'duplicate-declaration': rows[1][4]['id'] = rows[0][4]['id']
            if kind == 'duplicate-body': rows[1][5]['id'] = rows[0][5]['id']
            if kind == 'foreign-owner': rows[1][1]['id'] += 1
            if kind == 'boolean-id': rows[0][0]['id'] = True
            if kind == 'missing-row': rows.pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verifier.validate_identities(rows, self.control)

    def test_supplement_budget_and_provenance(self):
        for kind in ['valid', 'deadline', 'elapsed', 'nan', 'boolean-time', 'argv', 'digest', 'duplicate-control', 'conflated', 'failed', 'boolean-exit']:
            registration = self.read('supplemental-decode-registration.json')
            command = self.read('branch/identity-all-decode.command.json')
            bqrs = self.files[self.prefix + 'branch/identity.bqrs']
            if kind == 'deadline': command['deadline_seconds'] = 16
            if kind == 'elapsed': command['elapsed_seconds'] = 16
            if kind == 'nan': command['elapsed_seconds'] = float('nan')
            if kind == 'boolean-time': command['elapsed_seconds'] = False
            if kind == 'argv': command['argv'][0] = '/foreign/codeql'
            if kind == 'digest': bqrs += b'changed'
            if kind == 'duplicate-control': registration['commands'].append(registration['commands'][0])
            if kind == 'conflated': registration['not_part_of_original_75_seconds'] = False
            if kind == 'failed': command['exit_status'] = 1
            if kind == 'boolean-exit': command['exit_status'] = False
            if kind == 'valid':
                verifier.validate_supplement(self.control, registration, command, bqrs)
            else:
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    verifier.validate_supplement(self.control, registration, command, bqrs)


if __name__ == '__main__':
    unittest.main()
