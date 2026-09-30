#!/usr/bin/env python3
"""Claims stay consumed across roots, crashes and concurrent dispatch requests."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import release_claim_v090 as claim


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, sort_keys=True)+'\n')


class ClaimsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'root'; self.root.mkdir()
        self.other = self.base/'other'; self.other.mkdir()
        self.ledger = self.base/'claims.jsonl'; self.anchor = self.base/'anchor.json'
        self.lock = patch.object(claim, 'SERIAL_LOCK_PATH', str(self.base/'serial.lock'))
        self.lock.start(); self.addCleanup(self.lock.stop)

    def setup_contract(self, prior=1, recovery=False, approved=True):
        baseline = {'schema': claim.BASELINE_SCHEMA, 'release': 'v0.9.0', 'historical_counts': {'control:one': prior}, 'ledger_path':str(self.ledger)}
        for root in (self.root, self.other): write(root/'baseline.json', baseline)
        binding = {'schema': claim.FIELD_SCHEMA, 'baseline': {'path':'baseline.json','sha256':sha(self.root/'baseline.json')}, 'ledger_path':str(self.ledger)}
        contract = {'release':'v0.9.0', 'cumulative_attempts':binding, 'input_identities':{'baseline.json':sha(self.root/'baseline.json')}}
        if recovery:
            binding['recovery_allocation'] = {'path':'allocation.json','sha256':None}
            allocation = {'schema':'release-recovery-allocation/v1','release':'v0.9.0', 'allocation_id':'loss-one', 'approved':approved, 'operations':['control:one'], 'claims_per_operation':1, 'ledger_path':str(self.ledger), 'contract_binding_sha256':claim.contract_binding(contract)}
            for root in (self.root,self.other):write(root/'allocation.json',allocation)
            binding['recovery_allocation']['sha256']=sha(self.root/'allocation.json')
        contract['cumulative_attempts'] = claim.initialize_ledger(self.root,'baseline.json',sha(self.root/'baseline.json'),str(self.ledger),str(self.anchor),contract=contract)
        return contract

    def test_second_root_cannot_reset_and_crash_claim_stays_consumed(self):
        contract=self.setup_contract()
        row=claim.claim_attempt(self.root,contract,'control:one')
        self.assertEqual(row['sequence'],1)
        with self.assertRaisesRegex(claim.ClaimError,'exhausted'):claim.claim_attempt(self.other,contract,'control:one')
        self.assertEqual(len(self.ledger.read_text().splitlines()),2)

    def test_unknown_prior_is_not_zero(self):
        contract=self.setup_contract(prior=None)
        with self.assertRaisesRegex(claim.ClaimError,'unknown'):claim.claim_attempt(self.root,contract,'control:one')
        self.assertEqual(len(self.ledger.read_text().splitlines()),1)

    def test_unknown_allowed_only_by_exact_approved_one_claim_exception(self):
        contract=self.setup_contract(prior=None,recovery=True)
        claim.claim_attempt(self.root,contract,'control:one')
        with self.assertRaises(claim.ClaimError):claim.claim_attempt(self.other,contract,'control:one')
        self.assertIsNone(json.loads((self.root/'baseline.json').read_text())['historical_counts']['control:one'])

    def test_unapproved_allocation_cannot_initialize(self):
        with self.assertRaisesRegex(claim.ClaimError,'approved'):self.setup_contract(prior=None,recovery=True,approved=False)
        self.assertFalse(self.ledger.exists())

    def test_allocation_cannot_move_ledger_or_change_contract(self):
        contract=self.setup_contract(prior=None,recovery=True)
        other=copy.deepcopy(contract);other['cumulative_attempts']['ledger_path']=str(self.base/'reset.jsonl')
        with self.assertRaisesRegex(claim.ClaimError,'different release ledger|another ledger'):claim.claim_attempt(self.other,other,'control:one')
        other=copy.deepcopy(contract);other['new_command']='changed'
        with self.assertRaisesRegex(claim.ClaimError,'contract binding'):claim.claim_attempt(self.root,other,'control:one')

    def test_missing_or_corrupt_ledger_never_reinitialized(self):
        contract=self.setup_contract(); raw=self.ledger.read_bytes();self.ledger.unlink()
        with self.assertRaises(claim.ClaimError):claim.claim_attempt(self.root,contract,'control:one')
        self.assertFalse(self.ledger.exists())
        self.ledger.write_bytes(raw+b'{broken')
        with self.assertRaises(claim.ClaimError):claim.claim_attempt(self.root,contract,'control:one')
        with self.assertRaises(claim.ClaimError):claim.initialize_ledger(self.root,'baseline.json',sha(self.root/'baseline.json'),str(self.ledger),str(self.anchor))

    def test_concurrent_claims_serialize(self):
        contract=self.setup_contract()
        def attempt(root):
            try:claim.claim_attempt(root,contract,'control:one');return True
            except claim.ClaimError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,[self.root,self.other]))
        self.assertEqual(sorted(results),[False,True])

    def test_fsync_failure_never_reaches_dispatch(self):
        contract=self.setup_contract(); dispatch=Mock()
        with patch.object(claim.os,'fsync',side_effect=OSError('disk failed')):
            with self.assertRaises(claim.ClaimError):
                claim.claim_attempt(self.root,contract,'control:one')
                dispatch()
        dispatch.assert_not_called()
        with self.assertRaises(claim.ClaimError):claim.claim_attempt(self.other,contract,'control:one')

    def test_recovery_entrypoint_rejects_missing_accounting(self):
        with self.assertRaisesRegex(claim.ClaimError,'requires cumulative_attempts'):claim.claim_attempt(self.root,{},'control:one')

    def test_group_launcher_failed_claim_dispatches_nothing(self):
        spec=importlib.util.spec_from_file_location('recovery_group',Path(__file__).with_name('run-release-group-recovery-v090.py'))
        launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
        write(self.root/'contract.json',{'groups':[{'id':'one','argv':['never-run'],'environment':{}}]})
        with patch('sys.argv',['launcher','--root',str(self.root),'--contract','contract.json','--group','one','--execute']), patch.object(launch,'SERIAL_LOCK_PATH',str(self.base/'launch.lock')), patch.object(launch,'validate_group',return_value={}), patch.object(launch,'launch_gate'), patch.object(launch,'claim_attempt',side_effect=claim.ClaimError('write failure')), patch.object(launch,'run_group') as dispatch:
            with self.assertRaises(claim.ClaimError):launch.main()
        dispatch.assert_not_called()

    def test_control_launcher_failed_claim_dispatches_nothing(self):
        spec=importlib.util.spec_from_file_location('recovery_launch',Path(__file__).with_name('run-release-control-recovery-v090.py'))
        launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
        write(self.root/'contract.json',{'control_inventory':{'path':'inventory.json'}})
        write(self.root/'inventory.json',{'controls':[{'id':'one'}]})
        recorder=types.ModuleType('release_control_attempt_v090');recorder.validate_control=Mock();recorder.run_control=Mock()
        gate=types.SimpleNamespace(launch_gate=Mock()); loader=Mock(); fake_spec=types.SimpleNamespace(loader=loader)
        with patch.dict('sys.modules',{recorder.__name__:recorder}), patch.object(launch,'SERIAL_LOCK_PATH',str(self.base/'launch.lock')), patch.object(launch.importlib.util,'spec_from_file_location',return_value=fake_spec), patch.object(launch.importlib.util,'module_from_spec',return_value=gate), patch.object(launch,'claim_attempt',side_effect=claim.ClaimError('write failure')):
            with self.assertRaises(claim.ClaimError):launch.launch_control(self.root,'contract.json','one',execute=True)
        recorder.run_control.assert_not_called()


if __name__=='__main__':unittest.main()
