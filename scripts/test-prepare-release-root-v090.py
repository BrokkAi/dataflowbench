#!/usr/bin/env python3
"""A tiny Git fixture proves isolation and descendant-plan transport."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare', Path(__file__).with_name('prepare-release-root-v090.py'))
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class RootTests(unittest.TestCase):
    def test_exact_harness_source_preserved_and_repeat_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, dest = base/'source', base/'execution'
            source.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(source), *args], stderr=subprocess.DEVNULL).decode().strip()
            git('init')
            git('config', 'user.email', 'fixture@example.test')
            git('config', 'user.name', 'Fixture')
            git('config', 'commit.gpgsign', 'false')
            (source/'reports/raw/old').mkdir(parents=True)
            (source/'reports/raw/old/evidence.json').write_text('immutable evidence')
            (source/'input.txt').write_text('exact input')
            git('add', '.')
            git('commit', '-m', 'harness')
            harness = git('rev-parse', 'HEAD')
            contract_path = 'reports/releases/v0.9.0/execution-v1/contract.json'
            contract = {'harness_commit': harness,
                        'input_identities': {'input.txt': hashlib.sha256(b'exact input').hexdigest()},
                        'groups': [{'id': 'group', 'output_roots': ['reports/raw/old']}],
                        'execution_roots': {'group': str(dest)}}
            target = source/contract_path
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(contract))
            git('add', '.')
            git('commit', '-m', 'reviewed descendant plan')
            plan = git('rev-parse', 'HEAD')
            (source/'unrelated.txt').write_text('keep dirty work')
            receipt = prepare.prepare_root(source, dest, plan, contract_path)
            self.assertEqual(receipt['harness_commit'], harness)
            self.assertEqual((source/'reports/raw/old/evidence.json').read_text(), 'immutable evidence')
            self.assertEqual((source/'unrelated.txt').read_text(), 'keep dirty work')
            self.assertFalse((dest/'reports/raw/old').exists())
            self.assertEqual((dest/'input.txt').read_text(), 'exact input')
            self.assertEqual((dest/contract_path).read_bytes(), target.read_bytes())
            self.assertEqual(subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip(), harness)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                prepare.prepare_root(source, dest, plan, contract_path)

    def test_unsafe_path_rejected(self):
        for path in ['../source', '/absolute', 'reports/../input', './reports/raw']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare.safe_relative(path)


if __name__ == '__main__':
    unittest.main()
