"""Prove the 08 successor leaves existing production functions intact."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[5]
ACQUISITION = ROOT / 'reports/releases/v0.9.2/acquisition'
SOURCE_07 = ACQUISITION / 'joern-native-controls-07'
SOURCE_08 = ACQUISITION / 'joern-native-controls-08'
UNCHANGED_SIBLINGS = (
    'process_reconciliation.py',
    'snapshot_query.py',
    'retained_resources.py',
)


def top_level_definitions(raw: bytes):
    tree = ast.parse(raw)
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def top_level_assignments(raw: bytes):
    result = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            result[node.target.id] = node.value
    return result


class SourceAncestryTests(unittest.TestCase):
    def test_every_prior_top_level_production_definition_except_request_guard_is_ast_identical(self):
        old = top_level_definitions((SOURCE_07 / 'native_qualifier.py').read_bytes())
        new = top_level_definitions((SOURCE_08 / 'native_qualifier.py').read_bytes())
        self.assertIn('validate_request', old)
        self.assertIn('validate_ledger_history', new)
        self.assertEqual(set(new), set(old) | {'validate_ledger_history'})
        for name, value in old.items():
            if name == 'validate_request':
                continue
            with self.subTest(definition=name):
                self.assertEqual(new[name], value)

    def test_local_import_and_resource_helpers_are_unchanged_bytes_from_07(self):
        for name in UNCHANGED_SIBLINGS:
            with self.subTest(file=name):
                self.assertEqual((SOURCE_08 / name).read_bytes(), (SOURCE_07 / name).read_bytes())

    def test_archive_evidence_functions_and_classes_are_ast_identical(self):
        old = top_level_definitions((SOURCE_07 / 'archive_evidence.py').read_bytes())
        new = top_level_definitions((SOURCE_08 / 'archive_evidence.py').read_bytes())
        self.assertEqual(new, old)

    def test_archive_evidence_globals_differ_only_by_exact_helper_path_pin(self):
        old_raw = (SOURCE_07 / 'archive_evidence.py').read_bytes()
        new_raw = (SOURCE_08 / 'archive_evidence.py').read_bytes()
        old = top_level_assignments(old_raw)
        new = top_level_assignments(new_raw)
        self.assertEqual(set(new), set(old))
        differences = {name for name in old if ast.dump(old[name], include_attributes=False) !=
                       ast.dump(new[name], include_attributes=False)}
        self.assertEqual(differences, {'HELPER_SOURCE_PATH'})
        self.assertEqual(ast.literal_eval(old['HELPER_SOURCE_PATH']),
                         'reports/releases/v0.9.2/acquisition/joern-native-controls-07/archive_evidence.py')
        self.assertEqual(ast.literal_eval(new['HELPER_SOURCE_PATH']),
                         'reports/releases/v0.9.2/acquisition/joern-native-controls-08/archive_evidence.py')


if __name__ == '__main__':
    unittest.main()
