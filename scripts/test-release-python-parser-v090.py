#!/usr/bin/env python3
"""Exercise existing parser statements, stopping before all runtime dispatch."""
import argparse
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'reports/releases/v0.9.0/execution-v1/recovery-20260930-01'

def parse_only(script, arguments):
    path = ROOT / script
    spec = importlib.util.spec_from_file_location('parser_inspection', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    main = next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    prefix = []
    for node in main.body:
        prefix.append(node)
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == 'parse_args'):
            break
    else:
        raise ValueError('no reviewed parser boundary')
    namespace = dict(vars(module))
    with patch.object(sys, 'argv', [script, *arguments]):
        exec(compile(ast.Module(body=prefix, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['args']

class ParserTests(unittest.TestCase):
    def commands(self):
        inventory = json.loads((PACKET / 'control-inventory.json').read_text())
        contract = json.loads((PACKET / 'contract.json').read_text())
        return [row['argv'] for row in inventory['controls'] + contract['groups']
                if len(row['argv']) > 1 and row['argv'][1].endswith('.py')]

    def test_all_five_registered_python_commands(self):
        commands = self.commands()
        self.assertEqual(len(commands), 5)
        for argv in commands:
            with self.subTest(script=argv[1]):
                result = parse_only(argv[1], argv[2:])
                self.assertIsInstance(result, argparse.Namespace)
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
                    parse_only(argv[1], argv[2:] + ['--unregistered-option'])
                self.assertEqual(failure.exception.code, 2)

    def test_swift_execute_requires_reservation(self):
        for argv in self.commands():
            if '--reservation' not in argv:
                continue
            index = argv.index('--reservation')
            with self.subTest(script=argv[1]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
                parse_only(argv[1], argv[2:index] + argv[index+2:])
            self.assertEqual(failure.exception.code, 2)

if __name__ == '__main__':
    unittest.main()
