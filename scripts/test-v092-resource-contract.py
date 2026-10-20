#!/usr/bin/env python3
"""Resource successor rejects measurement or historical evidence changes."""
from __future__ import annotations
import copy
import ast
import hashlib
import json
import tempfile
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('resource_contract_executor', Path(__file__).with_name('execute-release-v092.py'))
executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(executor)

class ResourceContractTests(unittest.TestCase):
    def setUp(self):
        self.old = {'repo_root':Path('/tmp'), 'source_inputs':[{'path':'old','sha256':'a'*64}],
                    'plan':{'source_commit':'1'*40,'resource_budget':{'minimum_launch_free_gib':125,'protected_reserve_gib':40,'scratch_gib':24},
                            'groups':[{'id':'group','argv':['same-tool'],'maximum_attempts':2}],
                            'resource_reservation':{'expires_at_unix_seconds':1792560780.680937,'exclusive_analyzer_slot':True,'serial_analyzers':1},
                            'tools':{'runner':{'sha256':'a'*64}},'execution_series':1,'total_wall_budget_seconds':102960}}
        self.new = copy.deepcopy(self.old)
        self.new['total_wall_budget_seconds'] = 102960
        self.new['plan'].update(source_commit='2'*40,resource_budget={**self.old['plan']['resource_budget'],'minimum_launch_free_gib':110},
                                resource_guards={'stop_free_gib':48,'working_set_gib':12},resource_recovery={'path':'packet','sha256':'b'*64})
    def check(self):
        with mock.patch.object(executor,'_require_ancestor'), mock.patch.object(executor.subprocess,'check_output',return_value=''):
            executor._validate_resource_successor_equivalent(self.old,self.new)
    def test_resource_only_successor_accepted(self): self.check()
    def test_semantic_changes_are_rejected(self):
        self.new['plan']['groups'][0]['argv'].append('--different')
        with self.assertRaises(executor.ReleaseError): self.check()
    def test_reserve_cannot_be_reduced(self):
        self.new['plan']['resource_budget']['protected_reserve_gib']=39
        with self.assertRaises(executor.ReleaseError): self.check()
    def test_original_inputs_cannot_be_relabelled(self):
        self.new['source_inputs'][0]['sha256']='b'*64
        with self.assertRaises(executor.ReleaseError): self.check()
    def test_original_deadline_cannot_be_reset(self):
        self.new['total_wall_budget_seconds']=102961
        with self.assertRaises(executor.ReleaseError): self.check()
    def test_resolver_source_change_rejected(self):
        with mock.patch.object(executor,'_require_ancestor'), mock.patch.object(executor.subprocess,'check_output',return_value='src/resolver.rs\n'):
            with self.assertRaises(executor.ReleaseError):
                executor._validate_resource_successor_equivalent(self.old,self.new)
    def test_new_script_outside_review_scope_rejected(self):
        with mock.patch.object(executor,'_require_ancestor'), mock.patch.object(executor.subprocess,'check_output',side_effect=['','scripts/run-codeql-v092.py\n']):
            with self.assertRaises(executor.ReleaseError):
                executor._validate_resource_successor_equivalent(self.old,self.new)

class ResourceGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('resource_generator', self.root/'scripts/prepare-release-v092.py')
        self.generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.generator)
        self.raw = (self.root/'reports/releases/v0.9.2/execution-v3/contract.json').read_bytes()
        self.old = json.loads(self.raw)
        self.bindings = {
            'source_commit':'2'*40, 'source_inputs':self.old['source_inputs'],
            'tool_components':self.old['tool_components'],
            'scoped_recovery':self.old['scoped_recovery'],
            'path_replacements':self.old['path_replacements'],
            'resource_reservation':self.old['resource_reservation'],
            'resource_recovery':{'path':executor.RESOURCE_RECOVERY_MANIFEST_PATH.as_posix(),'sha256':'a'*64},
        }
    def generate(self, root, tools):
        archive = root/executor.ARCHIVED_RESOURCE_CONTRACT_03_PATH
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(self.raw)
        destination = root/executor.V4_CONTRACT_PATH
        with mock.patch.object(self.generator.executor, 'validate_plan', return_value={}) as validate:
            result = self.generator._build_c4_contract(self.bindings, tools, 'b'*64, root=root, destination=destination)
        validate.assert_called_once_with(destination, repo_root=root)
        return result
    def test_real_c3_measurement_semantics_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.generate(Path(directory),copy.deepcopy(self.old['tools']))
        for field in ['groups','tools','tool_components','scoped_recovery','path_replacements','qualification','population','total_wall_budget_seconds','execution_series']:
            if field in self.old:
                self.assertEqual(result[field],self.old[field],field)
        self.assertEqual(result['resource_budget'],dict(self.old['resource_budget'],minimum_launch_free_gib=110))
        self.assertEqual(result['resource_guards'],{'stop_free_gib':48,'working_set_gib':12})
        self.assertFalse(result['execution_authorized'])
    def test_analyzer_change_rejected_before_contract_write(self):
        tools=copy.deepcopy(self.old['tools'])
        tools['codeql']['version']='different'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(self.generator.executor.ReleaseError): self.generate(root,tools)
            self.assertFalse((root/executor.V4_CONTRACT_PATH).exists())
    def test_canonical_v4_output_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            relative,destination=self.generator._contract_output(self.bindings,None,Path(directory))
        self.assertEqual(relative,executor.V4_CONTRACT_PATH)

class GuardedReportStagingTests(unittest.TestCase):
    def make_fixture(self, root):
        guard_spec=importlib.util.spec_from_file_location('staging_disk_guard',Path(__file__).with_name('v092_disk_guard.py'))
        self.guards=importlib.util.module_from_spec(guard_spec)
        guard_spec.loader.exec_module(self.guards)
        execution=root/'execution'; output=execution/'out'; output.mkdir(parents=True)
        raw=b'{"native":"evidence"}'
        (output/'raw.json').write_bytes(raw)
        self.fixture='sha256:'+'f'*64
        original=json.dumps({'fixture_revision':self.fixture,'tool':'fake','tool_version':'1','results':[{'case_id':'case-1','raw_output':'out/raw.json','raw_sha256':hashlib.sha256(raw).hexdigest()}]}).encode()
        (output/'report.json').write_bytes(original)
        report={'source_path':'out/report.json','path':str(executor.NORMAL_ROOT/'sample.json'),'tool':'fake','tool_version':'1','case_ids':['case-1']}
        capture={'out/report.json':{'sha256':hashlib.sha256(original).hexdigest(),'bytes':len(original)},'out/raw.json':{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}}
        attempt_id='sample-attempt-01-series-01'; attempt=root/executor.ATTEMPTS_ROOT/attempt_id
        attempt.mkdir(parents=True)
        return execution,output,original,report,capture,attempt_id,attempt
    def test_guarded_staging_preserves_original_and_changes_only_raw_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); execution,output,original,report,capture,attempt_id,attempt=self.make_fixture(root)
            guard=self.guards.DiskGuard(disk_usage=lambda _path:200*1024**3)
            receipt=executor._stage_report(root,attempt,execution,attempt_id,report,capture,[output],self.fixture,disk_guard=guard,retained_paths=[root/'reports',output])
            self.assertEqual((root/receipt['original_path']).read_bytes(),original)
            staged=json.loads((root/receipt['staged_path']).read_bytes())
            expected=json.loads(original); expected['results'][0]['raw_output']=str(executor.ATTEMPTS_ROOT/attempt_id/'capture/out/raw.json')
            self.assertEqual(staged,expected)
    def test_combined_staging_projection_refuses_before_original_or_report_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); execution,output,original,report,capture,attempt_id,attempt=self.make_fixture(root)
            guard=self.guards.DiskGuard(disk_usage=lambda _path:200*1024**3,retention_ceiling_bytes=0)
            with self.assertRaises(self.guards.DiskGuardError):
                executor._stage_report(root,attempt,execution,attempt_id,report,capture,[output],self.fixture,disk_guard=guard,retained_paths=[root/'reports',output])
            self.assertFalse((attempt/'original').exists())
            self.assertFalse((root/executor.NORMAL_ROOT/'attempts'/attempt_id).exists())

class GuardReceiptSchemaTests(unittest.TestCase):
    def load_checker(self):
        spec=importlib.util.spec_from_file_location('guard_schema_checker',Path(__file__).with_name('check-release-v092.py'))
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        return checker
    def test_every_guard_error_metadata_field_has_a_checker_interpreter(self):
        checker=self.load_checker(); keys=set(); codes=set()
        for filename in ['v092_disk_guard.py','execute-release-v092.py']:
            for node in ast.walk(ast.parse(Path(__file__).with_name(filename).read_text())):
                if not isinstance(node,ast.Call): continue
                guard_call=(isinstance(node.func,ast.Name) and node.func.id=='DiskGuardError') or (isinstance(node.func,ast.Attribute) and node.func.attr=='error' and isinstance(node.func.value,ast.Name) and node.func.value.id=='disk_guard')
                if guard_call:
                    keys.update(keyword.arg for keyword in node.keywords if keyword.arg)
                    if node.args and isinstance(node.args[0],ast.Constant):codes.add(node.args[0].value)
        self.assertFalse(keys-set(checker.RESOURCE_CAPACITY_ERROR_METADATA))
        self.assertFalse(codes-set(checker.RESOURCE_GUARD_ERROR_CODES))
    def test_source_signature_error_retains_typed_stat_evidence(self):
        checker=self.load_checker()
        value={'code':'source_changed','message':'output changed after preflight','source_path':'out/raw.json','expected_signature':[1,2,3,4,5],'actual_signature':[1,2,6,7,8]}
        self.assertEqual(checker._verify_resource_guard_error('group',value,capacity_loss=False),value)
        value['actual_signature']=['1',2,6,7,8]
        with self.assertRaises(checker.EvidenceError):checker._verify_resource_guard_error('group',value,capacity_loss=False)

class RetainedFlowDroidReplayTests(unittest.TestCase):
    def test_actual_retained_flowdroid_receipt_uses_validated_d8_components(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('flowdroid_replay_checker',root/'scripts/check-release-v092.py')
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        raw=(root/'reports/releases/v0.9.2/execution-v3/contract.json').read_bytes();plan=json.loads(raw)
        group=next(item for item in plan['groups'] if item['id']=='flowdroid-java-kernel')
        self.assertNotIn('identity_components',group)
        normalized={**group,'identity_components':plan['tool_components']['flowdroid']}
        self.assertIn('d8',normalized['identity_components'])
        row=json.loads((root/'reports/releases/v0.9.2/attempts/flowdroid-java-kernel-attempt-01-series-01/completed.json').read_bytes())
        validated={'repo_root':root,'plan':plan,'groups':[normalized],'tools':plan['tools'],'source_inputs':row['source_inputs'],'qualification':{'flowdroid':row['qualification']},'fixture_revision':row['fixture_revision'],'bytes_sha256':hashlib.sha256(raw).hexdigest()}
        bindings,_counts=checker._verify_one_group(root,validated,group,row,row['plan_commit'],1)
        self.assertEqual(len(bindings),1)
        self.assertEqual(bindings[0]['adapter'],group['reports'][0]['path'])
        normalized['identity_components']=[name for name in normalized['identity_components'] if name!='d8']
        with self.assertRaises(checker.EvidenceError):checker._verify_one_group(root,validated,group,row,row['plan_commit'],1)

class LastMomentAdmissionTests(unittest.TestCase):
    def integration(self):
        spec=importlib.util.spec_from_file_location('last_moment_guard_fixture',Path(__file__).with_name('test-v092-disk-integration.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        class Error(RuntimeError):
            def __init__(self,code,message,**details):
                super().__init__(message);self.code=code;self.details=details
            def as_dict(self):return {'code':self.code,'message':str(self),**self.details}
        module.FakeDiskGuardError=Error
        return module,module.DiskGuardExecutorTests()
    def test_final_pre_popen_capacity_refusal_keeps_zero_analyzer_duration(self):
        module,fixture=self.integration()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);validated,attempt,execution,cache,ledger=fixture.make_validated(root)
            def materialize(_repo,_commit,destination,_inputs,*,preflight_only=False,**_kwargs):
                if preflight_only:return 128
                destination.mkdir(parents=True);(destination/'src').mkdir()
            def refuse(_argv,_cwd,_env,stdout,stderr,_timeout,*,ownership,**_kwargs):
                stdout.write_bytes(b'');stderr.write_bytes(b'');ownership['root_pid']=None
                gib=1024**3
                return 125,False,0.125,{'code':'stop_floor','message':'reserve fell before Popen','phase':'active','free_bytes':45*gib,'projected_bytes':0,'post_write_free_bytes':45*gib,'required_free_bytes':48*gib,'protected_reserve_bytes':40*gib,'capacity_path':str(root)}
            with fixture.patch_executor(validated,attempt,execution,cache,ledger,materialize,refuse):
                row=module.executor.run_group(validated,'guard-test')
            self.assertEqual(row['status'],'capacity-lost')
            self.assertEqual(row['duration_seconds'],0.0)
            self.assertEqual(row['exit_code'],125)
            self.assertEqual(row['reports'],[])
            self.assertNotIn('process_ownership',row)
            self.assertFalse((execution/'out').exists())
    def test_generic_source_setup_error_has_replayable_no_child_sentinel(self):
        module,fixture=self.integration()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);validated,attempt,execution,cache,ledger=fixture.make_validated(root)
            def materialize(_repo,_commit,_destination,_inputs,*,preflight_only=False,**_kwargs):
                if preflight_only:return 128
                raise RuntimeError('source setup failed before analyzer launch')
            def forbidden(*_args,**_kwargs):self.fail('analyzer must not start')
            with fixture.patch_executor(validated,attempt,execution,cache,ledger,materialize,forbidden):
                row=module.executor.run_group(validated,'guard-test')
            self.assertEqual(row['status'],'recorder-error')
            self.assertEqual(row['exit_code'],125)
            self.assertEqual(row['duration_seconds'],0.0)
            self.assertFalse(row['timed_out'])
            self.assertIsNone(row['capacity_loss'])
            self.assertEqual(row['stdout']['bytes'],0)
            self.assertEqual(row['stderr']['bytes'],0)
            self.assertNotIn('process_ownership',row)

if __name__ == '__main__': unittest.main()
