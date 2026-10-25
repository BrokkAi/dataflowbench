"""Fresh CLI-shaped imports, real graph preparation and frozen close only."""
import json
from pathlib import Path
import subprocess
import unittest


class FreshCLIImportTests(unittest.TestCase):
    def run_probe(self, mode):
        script=Path(__file__).resolve().with_name('cli_import_probe.py')
        result=subprocess.run(['/opt/homebrew/bin/python3.13','-B','-E',str(script),mode],
                              capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        proof=json.loads(result.stdout)
        self.assertTrue(proof['bridge_initially_absent'])
        return proof

    def test_actual_fresh_supervisor_import_graph95_and_frozen_close(self):
        self.assertTrue(self.run_probe('late')['frozen_close'])

    def test_foreign_bootstrap_bridge_rejected_before_graph(self):
        self.assertIsNone(self.run_probe('foreign')['result'])

    def test_foreign_postbaseline_nonstdlib_addition_still_rejected(self):
        self.assertIn('non-stdlib',self.run_probe('unknown')['caught']['message'])

    def test_wrong_sealed_bridge_hash_rejected_before_graph(self):
        self.assertIsNone(self.run_probe('drift')['result'])


if __name__ == '__main__':
    unittest.main()
