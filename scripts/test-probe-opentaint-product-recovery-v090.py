#!/usr/bin/env python3
"""Relocated recovery contracts fail before analyzer dispatch."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD = load('product_fixture', 'test-probe-opentaint-product-v090.py')
REC = load('recovery_product', 'probe-opentaint-product-recovery-v090.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'execution-state' / 'test-fixtures'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        checkout = base / 'isolated-checkout'
        checkout.mkdir()
        self.fx = OLD.Fixture(checkout)
        runtime = base / 'durable-runtime'
        shutil.move(self.fx.bundle, runtime)
        self.fx.bundle = runtime
        self.contract = json.loads(self.fx.contract_path.read_text())
        self.contract['tools']['opentaint-wrapper']['path'] = str(runtime / 'opentaint')
        for path in [self.fx.restoration_path, self.fx.runtime_path]:
            doc = json.loads(path.read_text())
            doc['bundle_root' if path == self.fx.restoration_path else 'root'] = str(runtime)
            self.fx._json(path, doc)
        wrapper = checkout / REC.SCRIPT_REL
        shutil.copyfile(Path(REC.__file__), wrapper)
        inventory = json.loads(self.fx.control_path.read_text())
        inventory['controls'][0]['argv'] = ['/usr/bin/python3', str(REC.SCRIPT_REL), '--contract', str(self.fx.contract_rel)]
        inventory['controls'][0]['script_identity'] = [{'path': str(REC.SCRIPT_REL), 'sha256': sha(wrapper)}]
        self.fx._json(self.fx.control_path, inventory)
        self.contract['control_inventory']['sha256'] = sha(self.fx.control_path)
        self.contract['runtime_trees'][0]['sha256'] = sha(self.fx.runtime_path)
        refs = {'restoration': self.fx.restoration_rel, 'runtime_tree': self.fx.runtime_rel,
                'implementation': REC.IMPLEMENTATION_REL}
        self.contract['opentaint_recovery'] = {k: {'path': str(v), 'sha256': sha(checkout/v)} for k,v in refs.items()}
        for relative in [*refs.values(), self.fx.control_rel]:
            self.contract['input_identities'][str(relative)] = sha(checkout/relative)
        self.save()

    def save(self):
        self.fx._json(self.fx.contract_path, self.contract)

    def verify(self):
        with patch.object(REC._PROBE, '_run_bounded', side_effect=AssertionError('analyzer dispatched')):
            return REC.prepare_recovery(self.fx.root, self.fx.contract_rel)

    def test_external_durable_runtime_passes_complete_predispatch_verifier(self):
        self.assertIsInstance(self.verify(), dict)
        self.assertFalse((self.fx.root / 'reports/raw/opentaint-product-v090').exists())

    def test_missing_recovery_refs_fail(self):
        del self.contract['opentaint_recovery']
        self.save()
        with self.assertRaises(REC.RecoveryContractError): self.verify()

    def test_mismatched_manifest_digest_fails(self):
        self.contract['opentaint_recovery']['runtime_tree']['sha256'] = '0'*64
        self.save()
        with self.assertRaises(REC.RecoveryContractError): self.verify()

    def test_stale_temporary_root_fails_even_when_hash_rebound(self):
        doc = json.loads(self.fx.restoration_path.read_text())
        doc['bundle_root'] = '/private/tmp/lost-opentaint'
        self.fx._json(self.fx.restoration_path, doc)
        digest = sha(self.fx.restoration_path)
        self.contract['opentaint_recovery']['restoration']['sha256'] = digest
        self.contract['input_identities'][str(self.fx.restoration_rel)] = digest
        self.save()
        with self.assertRaises(REC.RecoveryContractError): self.verify()

    def test_wrapper_path_mismatch_fails(self):
        self.contract['tools']['opentaint-wrapper']['path'] = str(self.fx.javac)
        self.save()
        with self.assertRaises(REC._PROBE.ProbeError): self.verify()

    def test_extra_runtime_member_fails(self):
        (self.fx.bundle/'extra').write_text('unexpected')
        with self.assertRaises(REC._PROBE.ProbeError): self.verify()

    def test_wrong_version_fails(self):
        self.contract['tools']['opentaint-wrapper']['version'] = '0.4.7'
        self.save()
        with self.assertRaises(REC._PROBE.ProbeError): self.verify()


if __name__ == '__main__': unittest.main()
