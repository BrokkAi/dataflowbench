#!/usr/bin/env python3
"""Validate the actual shell parsers without starting analyzers."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'reports/releases/v0.9.0/execution-v1/recovery-20260930-01/control-inventory.json'

def parser_command(argv):
    # Execute the script's exact existing initialization/argument checks only.
    # The first ROOT assignment begins filesystem/native execution setup.
    script = (ROOT / argv[1]).read_text()
    boundary = '\nROOT="$(cd'
    assert script.count(boundary) == 1
    parser = script.split(boundary, 1)[0]
    return ['bash', '-c', parser + '\necho "argument validation passed"\n', argv[1], *argv[2:]]

class ArgumentTests(unittest.TestCase):
    def test_registered_java_and_javascript_arguments(self):
        inventory = json.loads(PACKET.read_text())
        for language in ('java', 'javascript'):
            with self.subTest(language=language):
                control = next(c for c in inventory['controls'] if c['id'] == f'probe-{language}-modeling-load-bearing')
                argv = control['argv']
                result = subprocess.run(parser_command(argv), cwd=ROOT, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('argument validation passed', result.stdout)
                index = argv.index('--codeql-packs')
                missing = argv[:index] + argv[index + 2:]
                result = subprocess.run(parser_command(missing), cwd=ROOT, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertIn('--codeql-packs is required', result.stderr)

    def test_unknown_options_are_rejected(self):
        for language in ('java', 'javascript'):
            with self.subTest(language=language):
                result = subprocess.run(parser_command(['bash', f'scripts/probe-{language}-modeling-load-bearing.sh', '--unknown']), cwd=ROOT, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertIn('unknown argument', result.stderr)

if __name__ == '__main__':
    unittest.main()
