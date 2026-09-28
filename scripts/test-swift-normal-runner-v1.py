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
        self.assertEqual(len(phases), 10)
        self.assertEqual([p['role'] for p in phases], ['extraction'] + ['analysis'] * 9)
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
        validate_phases(self.root, {'commands': refs, 'analysis_elapsed_seconds': 3}, specs, 'inconclusive', [])

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
        self.assertEqual(before['link']['symlink'], 'file')
        (self.root/'file').chmod(0o755)
        self.assertNotEqual(before,file_inventory(self.root))
        before=file_inventory(self.root)
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


    def execution_failure(self, failure_kind):
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
            write(directory/'extract.command.json',{'argv':argv,'phase_id':'extract','role':'extraction','exit_status':1,'timed_out':failure_kind=='timeout','cleanup_status':'uncertain' if failure_kind=='cleanup' else 'tracked-processes-stopped','elapsed_seconds':1,'deadline_seconds':deadline})
            (directory/'extract.stderr').write_text('retained failure')
            if failure_kind=='closure': (directory/'database').mkdir()
            if failure_kind=='timeout': raise TimeoutError('BudgetExhausted')
            raise ValueError('UncertainCleanup' if failure_kind=='cleanup' else 'CommandFailed:extract')
        with patch('swift_normal_runner_v1.verify_query_receipt'), patch('swift_normal_runner_v1.verify_runtime'), patch('swift_normal_runner_v1.load_population',return_value=(population,cases,'population')), patch('swift_normal_runner_v1.subprocess.run'), patch('swift_normal_runner_v1.shutil.disk_usage') as disk, patch('swift_normal_runner_v1.process.run',side_effect=version), patch('swift_normal_runner_v1.run_phase',side_effect=fail), patch('swift_normal_runner_v1.export') as exporter, patch('swift_normal_runner_v1.snapshot',side_effect=OSError('snapshot failure')):
            disk.return_value.free=LAUNCH_CAPACITY
            output=self.root/'reports/raw/swift-normal-v1/test'
            run=execute(self.root,'plan.json',output,reservation)
            self.assertEqual(len(run['results']),1)
            raw=json.loads((output/'first/raw.json').read_text())
            self.assertEqual(raw['raw_outcome'],'inconclusive' if failure_kind=='timeout' else 'runner-error')
            expected={'cleanup':'UncertainCleanup','timeout':'BudgetExhausted','closure':'CommandFailed:extract'}[failure_kind]
            self.assertIn(expected,raw['diagnostics'])
            if failure_kind=='closure':self.assertTrue(any(d.startswith('ArtifactClosureFailed:') for d in raw['diagnostics']))
            self.assertEqual(len(raw['commands']),1)
            self.assertTrue(raw['native_outputs'])
            self.assertFalse((output/'second').exists())
            self.assertEqual(json.loads((output/'stop.json').read_text())['unattempted_case_ids'],['second'])
            exporter.assert_not_called()


    def test_cleanup_timeout_and_closure_failure_stop_and_retain(self):
        for kind in ['cleanup','timeout','closure']:
            with self.subTest(kind=kind):
                old=self.root
                self.root=old/kind;self.root.mkdir()
                try:self.execution_failure(kind)
                finally:self.root=old

    def test_archived_source_schema_and_owned_database(self):
        from swift_normal_runner_v1 import validate_database,sha
        import zipfile
        db=self.root/'database';(db/'db-swift').mkdir(parents=True)
        source=self.root/'source';source.mkdir();canonical=self.root/'canonical';canonical.mkdir()
        (source/'main.swift').write_text('let x = 1');(canonical/'main.swift').write_text('let x = 1')
        (db/'codeql-database.yml').write_text('finalised: true\n')
        (db/'db-swift/swift.dbscheme').write_text('schema')
        def archive(data):
            with zipfile.ZipFile(db/'src.zip','w') as z:z.writestr(str(source/'main.swift').lstrip('/'),data)
        archive('let x = 1')
        metadata={'languages':['swift'],'datasetFolder':str(db/'db-swift'),'sourceArchiveZip':str(db/'src.zip'),'sourceLocationPrefix':str(source),'logsFolder':str(db/'log')}
        args=(db,source,canonical,{'fixture_files':['main.swift']},metadata,sha(db/'db-swift/swift.dbscheme'))
        validate_database(*args)
        archive('changed')
        with self.assertRaisesRegex(ValueError,'ArchivedSourceMismatch'):validate_database(*args)
        archive('let x = 1');metadata['datasetFolder']='/foreign/database'
        with self.assertRaisesRegex(ValueError,'Ownership'):validate_database(*args)
        metadata['datasetFolder']=str(db/'db-swift')
        (db/'db-swift/swift.dbscheme').write_text('foreign')
        with self.assertRaisesRegex(ValueError,'Schema'):validate_database(*args)



class Revalidation(unittest.TestCase):
    """Replay actual committed observations without requiring native assets."""
    def setUp(self):
        import shutil
        import swift_normal_runner_v1 as runner
        self.runner=runner
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name in ['cases','populations',runner.BASE+'/queries',runner.BASE+'/plan-2026-09-28-04',runner.BASE+'/plan-2026-09-28-06','evidence/swift-normal-query-check-2026-09-28-03']:
            shutil.copytree(runner.ROOT/name,self.root/name)
        self.planpath=runner.BASE+'/plan-2026-09-28-06/plan.json'
        self.amendpath=runner.BASE+'/plan-2026-09-28-06/query-revalidation.json'
        self.plan=runner.read(self.root/self.planpath)
        self.amend=runner.read(self.root/self.amendpath)
        self.reservation={'query_qualification':self.amend['original_receipt']}
        self.publish()
        self.patch=patch('swift_normal_runner_v1.ROOT',self.root)
        self.patch.start();self.addCleanup(self.patch.stop)

    def publish(self):
        r=self.runner
        r.write(self.root/self.planpath,self.plan)
        self.amend['new_plan']=r.ref(self.root,self.root/self.planpath)
        r.write(self.root/self.amendpath,self.amend)
        self.reservation['query_revalidation']=r.ref(self.root,self.root/self.amendpath)

    def verify(self):
        return self.runner.verify_revalidation(self.root,self.planpath,self.reservation)

    def test_actual_amendment_accepts_unchanged_compile_inputs(self):
        self.assertEqual(self.verify(),self.amend)
        self.assertIn('scripts/swift_normal_runner_v1.py',self.amend['allowed_nonquery_changes'])
        self.assertEqual(self.amend['claim'],'query-compile-only-not-runner-execution')

    def test_query_import_and_membership_mutations_reject(self):
        for suffix in ['.ql','.qll']:
            path=next((self.root/self.runner.BASE/'queries').rglob('*'+suffix))
            original=path.read_bytes()
            path.write_bytes(original+b'\n// changed input\n')
            with self.assertRaises(ValueError):self.verify()
            path.write_bytes(original)
        extra=self.root/self.runner.BASE/'queries/new-import.qll';extra.write_text('class New {}')
        with self.assertRaisesRegex(ValueError,'membership'):self.verify()
        extra.unlink()
        path=next((self.root/self.runner.BASE/'queries').rglob('*.qll'))
        original=path.read_bytes();path.unlink()
        with self.assertRaisesRegex(ValueError,'membership'):self.verify()
        path.write_bytes(original)
        self.verify()

    def test_schema_cli_and_runtime_paths_reject(self):
        import copy
        baseline=copy.deepcopy(self.plan)
        self.plan['runtime']['pins']['schema_sha256']='0'*64;self.publish()
        with self.assertRaisesRegex(ValueError,'semantic inputs'):self.verify()
        self.plan=copy.deepcopy(baseline)
        self.plan['runtime']['codeql']='/foreign/codeql';self.publish()
        with self.assertRaisesRegex(ValueError,'semantic inputs'):self.verify()
        self.plan=copy.deepcopy(baseline)
        manifest=self.root/self.plan['runtime']['manifests']['cli']['path']
        old=manifest.read_bytes();data=self.runner.read(manifest)
        data[next(iter(data))]='0'*64
        self.runner.write(manifest,data)
        self.plan['runtime']['manifests']['cli']=self.runner.ref(self.root,manifest);self.publish()
        with self.assertRaisesRegex(ValueError,'semantic inputs'):self.verify()
        manifest.write_bytes(old);self.plan=baseline;self.publish();self.verify()

    def test_old_plan_receipt_and_digest_swaps_reject(self):
        import copy
        baseline=copy.deepcopy(self.amend)
        self.amend['old_plan']=self.amend['new_plan'];self.publish()
        with self.assertRaisesRegex(ValueError,'old receipt plan mismatch'):self.verify()
        self.amend=copy.deepcopy(baseline)
        oldreceipt=self.root/self.amend['original_receipt']['path']
        swapped=self.root/'swapped-receipt.json'
        receipt=self.runner.read(oldreceipt);receipt['plan_sha256']='0'*64
        self.runner.write(swapped,receipt)
        swappedref=self.runner.ref(self.root,swapped)
        self.amend['original_receipt']=swappedref;self.reservation['query_qualification']=swappedref;self.publish()
        with self.assertRaisesRegex(ValueError,'receipt plan mismatch'):self.verify()
        self.amend=copy.deepcopy(baseline);self.reservation['query_qualification']=baseline['original_receipt'];self.publish()
        self.reservation['query_revalidation']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'digest mismatch'):self.verify()
        self.publish();self.amend['old_plan']['sha256']='0'*64;self.publish()
        with self.assertRaisesRegex(ValueError,'digest mismatch'):self.verify()

    def test_missing_untracked_or_dirty_amendment_stops_before_process(self):
        import subprocess
        import shutil
        r=self.runner
        output=self.root/'reports/raw/swift-normal-v1/test'
        with patch('swift_normal_runner_v1.process.run') as native:
            missing=dict(self.reservation);missing.pop('query_revalidation')
            with self.assertRaisesRegex(ValueError,'artifact reference'):
                r.execute(self.root,self.planpath,output,missing)
            native.assert_not_called()
        # Real Git gates: all requested execution inputs tracked and unchanged,
        # except the amendment. No mocked Git exit status and no native tool.
        for refs in self.plan['configurations'].values():
            for reference in refs:
                path=self.root/reference['path']
                if not path.exists():
                    path.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(Path(__file__).resolve().parents[1]/reference['path'],path)
        def git(*args):
            return subprocess.run(['git','-c','user.name=Runner Test','-c','user.email=runner@example.invalid','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=self.root,check=True,stdout=subprocess.DEVNULL)
        git('init','-q');git('add','.');git('commit','-qm','synthetic registration')
        git('rm','--cached',self.amendpath)
        # Commit the removal so diff HEAD is clean and ls-files rejects it.
        git('commit','-qm','leave amendment untracked')
        with patch('swift_normal_runner_v1.process.run') as native:
            with self.assertRaises(subprocess.CalledProcessError):r.execute(self.root,self.planpath,output,self.reservation)
            native.assert_not_called()
        git('add',self.amendpath);git('commit','-qm','register amendment')
        self.amend['rationale']+=' Dirty amendment.';self.publish()
        with patch('swift_normal_runner_v1.process.run') as native:
            with self.assertRaises(subprocess.CalledProcessError):r.execute(self.root,self.planpath,output,self.reservation)
            native.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == '__main__': unittest.main()
