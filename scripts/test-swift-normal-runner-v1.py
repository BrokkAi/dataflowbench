#!/usr/bin/env python3
"""Runner protocol tests with fake invocations; never launch CodeQL."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from swift_normal_runner_v1 import capacity, patched_identity, sequence, run_phase, MINIMUM_RESERVE, LAUNCH_CAPACITY, file_inventory, verify_query_receipt
from swift_normal_reports_v1 import phase_sequence, validate_phases


class Runner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_capacity_guards(self):
        for limit, launch in [(MINIMUM_RESERVE, False), (LAUNCH_CAPACITY, True)]:
            with self.assertRaises(ValueError): capacity(limit - 1, launch)
            capacity(limit, launch)

    def test_version_banner_and_patched_identity(self):
        pins = dict(cli_version='2.27.1', cli_build='exact-build', extractor_sha256='extractor', schema_sha256='schema', packs_manifest_sha256='packs')
        banner = dict(productName='CodeQL', version='2.27.1', sha='exact-build')
        self.assertIn('swift-extractor:extractor', patched_identity(banner, pins)['tool_build_identity'])
        for key in banner:
            wrong = dict(banner);wrong[key] = 'foreign'
            with self.assertRaises(ValueError): patched_identity(wrong, pins)

    def test_lane_sequence_has_one_shared_analysis_budget(self):
        contract = {'phase_sequences': {'native': sequence(['roles', 'flow', 'coverage', 'scopes'])}}
        phases = phase_sequence(contract, 'native')
        self.assertEqual(len(phases), 9)
        self.assertEqual([p['role'] for p in phases], ['extraction'] + ['analysis'] * 8)
        with self.assertRaises(ValueError): phase_sequence(contract, 'foreign')

    def fake(self, status=0, timeout=False, elapsed=1, cleanup='tracked-processes-stopped'):
        def invoke(argv, directory, name, deadline, **kwargs):
            return dict(argv=argv,exit_status=status,timed_out=timeout,elapsed_seconds=elapsed,deadline_seconds=deadline,cleanup_status=cleanup)
        return invoke

    def test_phase_witness_roundtrips_exporter(self):
        specs = sequence(['query'])
        refs = []
        from swift_normal_reports_v1 import sha
        for spec in specs:
            run_phase(['fake'], self.root, spec, 10, self.fake())
            path = self.root / (spec['id'] + '.command.json')
            refs.append({'path': path.name, 'sha256': sha(path)})
        validate_phases(self.root, {'commands': refs, 'analysis_elapsed_seconds': 2}, specs, 'inconclusive', [])

    def test_failures_retain_role_and_command(self):
        for name, invoke, error in [('failed', self.fake(status=2), ValueError), ('timeout', self.fake(timeout=True), TimeoutError), ('overrun', self.fake(elapsed=11), TimeoutError), ('cleanup', self.fake(cleanup='uncertain'), ValueError)]:
            directory = self.root / name;directory.mkdir()
            with self.assertRaises(error): run_phase(['fake'], directory, {'id':'extract','role':'extraction'}, 10, invoke)
            record = json.loads((directory/'extract.command.json').read_text())
            self.assertEqual(record['phase_id'], 'extract');self.assertEqual(record['role'], 'extraction')

    def test_inventory_binds_bytes_and_symlinks_and_rejects_escape(self):
        (self.root/'file').write_text('before')
        (self.root/'link').symlink_to('file')
        before = file_inventory(self.root)
        self.assertEqual(before['link'], {'symlink': 'file'})
        (self.root/'file').write_text('after')
        self.assertNotEqual(before, file_inventory(self.root))
        (self.root/'escape').symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'escapes'): file_inventory(self.root)

    def test_query_receipt_requires_every_exact_query_and_library(self):
        from swift_normal_reports_v1 import sha
        query = self.root/'query.ql';query.write_text('select 1')
        planpath = self.root/'plan.json';planpath.write_text('{}')
        rt = {'codeql': '/pinned/codeql', 'packs': '/pinned/packs'}
        plan = {'runtime': rt}
        expected = '/pinned/packs/codeql/swift-all/6.8.4-dfb.entry1'
        row = {'query_sha256': sha(query)}
        for kind in ['resolve', 'compile']:
            argv = [rt['codeql'],'resolve','library-path','--query='+str(query),'--additional-packs='+rt['packs'],'--format=json'] if kind == 'resolve' else [rt['codeql'],'query','compile',str(query),'--check-only','--additional-packs='+rt['packs'],'--threads=2','--ram=2048']
            path = self.root/(kind+'.json');path.write_text(json.dumps(dict(cwd=str(self.root),argv=argv,exit_status=0,timed_out=False,cleanup_status='tracked-processes-stopped',elapsed_seconds=1,deadline_seconds=75)))
            row[kind] = {'path': path.name,'sha256':sha(path)}
        output = self.root/'resolve.stdout';output.write_text(json.dumps({'libraryPath':[expected], 'dbscheme':expected+'/swift.dbscheme'}))
        row['resolution_stdout'] = {'path':output.name,'sha256':sha(output)}
        receipt = {'execution_root':str(self.root),'plan_path':planpath.name,'plan_sha256':sha(planpath),'queries':{'query.ql':row}}
        with patch('swift_normal_runner_v1.load_population',return_value=(None,{'case':{}},None)), patch('swift_normal_runner_v1.query_files',return_value={'flow':query}):
            verify_query_receipt(self.root,plan,receipt)
            foreign_root = dict(receipt,execution_root='/foreign/root')
            with self.assertRaisesRegex(ValueError,'working-directory'):verify_query_receipt(self.root,plan,foreign_root)
            missing = dict(receipt,queries={})
            with self.assertRaisesRegex(ValueError,'membership'):verify_query_receipt(self.root,plan,missing)
            output.write_text(json.dumps({'libraryPath':[expected,'/foreign/codeql/swift-all/6.8.4'], 'dbscheme':expected+'/swift.dbscheme'}))
            row['resolution_stdout']['sha256']=sha(output)
            with self.assertRaisesRegex(ValueError,'unbound|mixed'):verify_query_receipt(self.root,plan,receipt)


    def test_committed_compatibility_receipt(self):
        from swift_normal_runner_v1 import ROOT,read
        for attempt,plan in [('01','02'),('02','03'),('03','04')]:
            directory=ROOT/('evidence/swift-normal-query-check-2026-09-28-'+attempt)
            verify_query_receipt(ROOT,read(ROOT/('adapters/codeql/swift-normal-v1/plan-2026-09-28-'+plan+'/plan.json')),read(directory/'receipt.json'))


    def test_query_receipt_replays_from_another_checkout(self):
        import shutil
        from swift_normal_runner_v1 import ROOT,read
        # Copy repository inputs only; native tools do not exist in this root.
        for name in ['cases','populations']:
            shutil.copytree(ROOT/name,self.root/name)
        for name in ['adapters/codeql/swift-normal-v1','evidence/swift-normal-query-check-2026-09-28-01']:
            shutil.copytree(ROOT/name,self.root/name)
        receipt=read(self.root/'evidence/swift-normal-query-check-2026-09-28-01/receipt.json')
        plan=read(self.root/receipt['plan_path'])
        with patch('swift_normal_runner_v1.ROOT',self.root):
            verify_query_receipt(self.root,plan,receipt)


    def test_execution_retains_failure_and_stops_after_uncertain_cleanup(self):
        from swift_normal_runner_v1 import execute,write,ref,sha
        pins=dict(cli_version='2.27.1',cli_build='exact-build',extractor_sha256='extractor',schema_sha256='schema',packs_manifest_sha256='packs')
        banner=dict(productName='CodeQL',version='2.27.1',sha='exact-build')
        identity=patched_identity(banner,pins)
        contract={'phase_sequences':{'standard':sequence(['flow'])}}
        write(self.root/'contract.json',contract)
        write(self.root/'receipt.json',{'plan_path':'plan.json'})
        runtime={'codeql':'/fake/codeql','compiler':'/fake/swiftc','sdk':'/fake/sdk','extractor_root':'/fake/extractor','packs':'/fake/packs','pins':pins,'manifests':{}}
        cases={i:{'fixture_files':['main.swift'],'template_id':'test','model_profile':'benchmark-controlled','score_tier':'core'} for i in ['first','second']}
        population={'fixture_revision':'fixture','cases':[]}
        for case_id in cases:
            path=self.root/'cases'/case_id;path.mkdir(parents=True);(path/'main.swift').write_text('let x = 1')
            population['cases'].append({'id':case_id,'path':str((path/'case.json').relative_to(self.root))})
        plan={'runtime':runtime,'execution_contract':ref(self.root,self.root/'contract.json'),'configurations':{'config':[]},'population_sha256':'population','fixture_revision':'fixture','registered_at_unix_seconds':0,'identity':identity,'cases':{i:{'configuration':'config','phase_sequence':'standard'} for i in cases},'output_root':'reports/raw/swift-normal-v1'}
        write(self.root/'plan.json',plan)
        reservation={'query_qualification':ref(self.root,self.root/'receipt.json'),'plan_sha256':sha(self.root/'plan.json'),'launch_free_bytes':LAUNCH_CAPACITY,'exclusive_analyzer_slot':True}
        def version(argv,directory,name,deadline,**kwargs):
            write(directory/'version.stdout',banner)
            return {'exit_status':0,'timed_out':False,'cleanup_status':'tracked-processes-stopped'}
        def fail(argv,directory,spec,deadline):
            write(directory/'extract.command.json',{'argv':argv,'phase_id':'extract','role':'extraction','exit_status':1,'timed_out':False,'cleanup_status':'uncertain','elapsed_seconds':1,'deadline_seconds':deadline})
            (directory/'extract.stderr').write_text('retained failure')
            raise ValueError('UncertainCleanup')
        with patch('swift_normal_runner_v1.verify_query_receipt'), patch('swift_normal_runner_v1.verify_runtime'), patch('swift_normal_runner_v1.load_population',return_value=(population,cases,'population')), patch('swift_normal_runner_v1.subprocess.run'), patch('swift_normal_runner_v1.shutil.disk_usage') as disk, patch('swift_normal_runner_v1.process.run',side_effect=version), patch('swift_normal_runner_v1.run_phase',side_effect=fail), patch('swift_normal_runner_v1.export') as exporter:
            disk.return_value.free=LAUNCH_CAPACITY
            output=self.root/'reports/raw/swift-normal-v1/test'
            run=execute(self.root,'plan.json',output,reservation)
            self.assertEqual(len(run['results']),1)
            raw=json.loads((output/'first/raw.json').read_text())
            self.assertEqual(raw['raw_outcome'],'runner-error')
            self.assertIn('UncertainCleanup',raw['diagnostics'])
            self.assertEqual(len(raw['commands']),1)
            self.assertTrue(raw['native_outputs'])
            self.assertFalse((output/'second').exists())
            exporter.assert_not_called()



if __name__ == '__main__': unittest.main()
