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

    def make_control_fixture(self, base, *, duplicate_roots=False, tamper_inventory=False,
                             reviewed_script_overlay=False):
        source = base/'source'
        destination = base/'controls'/'java-modeling'
        source.mkdir()

        def git(*args):
            return subprocess.check_output(['git', '-C', str(source), *args], stderr=subprocess.DEVNULL).decode().strip()

        def write(relative, data):
            path = source/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data if isinstance(data, bytes) else data.encode())

        git('init')
        git('config', 'user.email', 'fixture@example.test')
        git('config', 'user.name', 'Fixture')
        git('config', 'commit.gpgsign', 'false')
        write('config.txt', 'harness config\n')
        write('scripts/java-control.sh', '#!/bin/sh\necho java\n')
        write('scripts/other-control.sh', '#!/bin/sh\necho other\n')
        output = 'reports/raw/java-modeling'
        write(output + '/source-evidence.txt', 'preserve source evidence\n')
        write(output + '/scratch/stale.txt', 'stale scratch\n')
        write('reports/raw/other/keep.txt', 'other control output\n')
        git('add', '.')
        git('commit', '-m', 'exact control harness')
        harness = git('rev-parse', 'HEAD')

        inventory_path = 'reports/releases/v0.9.0/execution-v1/control-inventory.json'
        contract_path = 'reports/releases/v0.9.0/execution-v1/contract.json'
        inventory = {
            'controls': [
                {'id': 'java-modeling', 'script_identity': [
                    {'path': 'scripts/java-control.sh', 'sha256': hashlib.sha256(b'#!/bin/sh\necho java\n').hexdigest()}],
                 'output_roots': [output, output + '/scratch']},
                {'id': 'other', 'script_identity': [
                    {'path': 'scripts/other-control.sh', 'sha256': hashlib.sha256(b'#!/bin/sh\necho other\n').hexdigest()}],
                 'output_roots': ['reports/raw/other']},
            ]
        }
        inventory_bytes = json.dumps(inventory, sort_keys=True).encode()
        if reviewed_script_overlay:
            write('scripts/java-control.sh', '#!/bin/sh\necho changed\n')
            inventory['controls'][0]['script_identity'][0]['sha256'] = hashlib.sha256(
                b'#!/bin/sh\necho changed\n').hexdigest()
            inventory_bytes = json.dumps(inventory, sort_keys=True).encode()
        inventory_sha = hashlib.sha256(inventory_bytes).hexdigest()
        identities = {
            'config.txt': hashlib.sha256(b'harness config\n').hexdigest(),
            inventory_path: inventory_sha,
        }
        roots = {'java-modeling': str(destination),
                 'other': str(destination if duplicate_roots else base/'controls'/'other')}
        contract = {
            'harness_commit': harness,
            'input_identities': identities,
            'control_inventory': {'path': inventory_path, 'sha256': inventory_sha},
            'control_execution_roots': roots,
            'groups': [],
        }
        write(inventory_path, inventory_bytes)
        if tamper_inventory:
            write(inventory_path, inventory_bytes + b' ')
        write(contract_path, json.dumps(contract, sort_keys=True).encode())
        git('add', '.')
        git('commit', '-m', 'reviewed control plan descendant')
        plan = git('rev-parse', 'HEAD')
        return source, destination, plan, contract_path, output

    def test_control_root_clears_only_selected_roots_in_isolated_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, dest, plan, contract_path, output = self.make_control_fixture(base)
            receipt = prepare.prepare_control_root(source, dest, plan, contract_path, 'java-modeling')
            self.assertEqual(receipt['control_id'], 'java-modeling')
            self.assertEqual(receipt['harness_commit'],
                             subprocess.check_output(['git', '-C', str(source), 'rev-parse', plan + '^'], text=True).strip())
            self.assertFalse((dest/output).exists())
            self.assertEqual((source/output/'source-evidence.txt').read_text(), 'preserve source evidence\n')
            self.assertEqual((source/output/'scratch/stale.txt').read_text(), 'stale scratch\n')
            self.assertEqual((dest/'config.txt').read_text(), 'harness config\n')
            self.assertTrue((dest/'scripts/java-control.sh').exists())
            self.assertEqual((dest/'reports/raw/other/keep.txt').read_text(), 'other control output\n')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                prepare.prepare_control_root(source, dest, plan, contract_path, 'java-modeling')

    def test_control_roots_must_be_unique(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, dest, plan, contract_path, _ = self.make_control_fixture(base, duplicate_roots=True)
            with self.assertRaisesRegex(ValueError, 'must be unique'):
                prepare.prepare_control_root(source, dest, plan, contract_path, 'java-modeling')
            self.assertFalse(dest.exists())

    def test_control_inventory_overlay_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, dest, plan, contract_path, _ = self.make_control_fixture(base, tamper_inventory=True)
            with self.assertRaisesRegex(ValueError, 'inventory digest mismatch'):
                prepare.prepare_control_root(source, dest, plan, contract_path, 'java-modeling')
            self.assertFalse(dest.exists())

    def test_control_script_overlay_must_match_harness_even_when_rehashed(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, dest, plan, contract_path, _ = self.make_control_fixture(
                base, reviewed_script_overlay=True)
            with self.assertRaisesRegex(ValueError, 'differs from exact harness checkout'):
                prepare.prepare_control_root(source, dest, plan, contract_path, 'java-modeling')
            self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
