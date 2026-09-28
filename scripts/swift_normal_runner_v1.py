"""Pinned, serial CodeQL runner producing exporter-compatible witness records.

No process is launched by preparation. Execution requires a committed plan and
capacity reservation. Fixture binaries are compiled only, never executed.
"""
import hashlib
import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import swift_v2_process as process
from swift_extraction_integrity import inspect_logs
from swift_artifact_closure import snapshot
from swift_normal_reports_v1 import (ROOT, bound_file, configuration_hash, export,
    load_population, normalized, phase_sequence, read, require, sha)
from swift_persistence_coverage import assess_coverage, CoverageStatus
from swift_v3_runner import lane, observe

BASE = 'adapters/codeql/swift-normal-v1'
ADAPTER = 'swift-normal-v1'
MINIMUM_RESERVE = 40 * 1024**3
LAUNCH_CAPACITY = 64 * 1024**3


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def ref(root, path):
    return {'path': str(path.relative_to(root)), 'sha256': sha(path)}


def query_files(case):
    selected = lane(case)
    directory = ROOT / BASE / 'queries' / (selected if selected in ('native', 'opaque') else 'standard')
    names = ['roles', 'flow'] + (['coverage', 'scopes'] if case['template_id'] == 'dfb-template-native-persistence' else [])
    return {name: directory / (name + '.ql' if selected in ('native', 'opaque') else selected + '-' + name + '.ql') for name in names}


def sequence(names):
    return [{'id': 'extract', 'role': 'extraction'}] + [dict(id=phase, role='analysis') for name in names for phase in (name, name + '-decode')]


def patched_identity(banner, pins):
    require(banner.get('productName') == 'CodeQL' and banner.get('version') == pins['cli_version'] and banner.get('sha') == pins['cli_build'], 'CodeQL version/build witness mismatch')
    return {'tool': 'codeql', 'tool_version': banner['version'], 'tool_build_identity': 'codeql:' + banner['sha'] + ';swift-extractor:' + pins['extractor_sha256'] + ';schema:' + pins['schema_sha256'] + ';packs:' + pins['packs_manifest_sha256'], 'adapter_version': ADAPTER}


def capacity(free_bytes, launch=False):
    require(free_bytes >= (LAUNCH_CAPACITY if launch else MINIMUM_RESERVE), 'InsufficientLaunchCapacity' if launch else 'DiskReserveReached')


def file_inventory(base):
    """Inventory regular bytes and symlink targets; reject directory escapes."""
    import os
    base = base.resolve()
    result = {}
    for directory, dirs, files in os.walk(base, followlinks=False):
        for name in dirs + files:
            path = Path(directory)/name
            relative = str(path.relative_to(base))
            if path.is_symlink():
                target = path.resolve(strict=True)
                require(target.is_relative_to(base), 'runtime symlink escapes inventory: ' + str(path))
                result[relative] = {'symlink': os.readlink(path)}
            elif path.is_file():
                result[relative] = {'sha256': sha(path)}
    require(result, 'empty runtime inventory')
    return result


def verify_query_receipt(root, plan, receipt):
    """Accept only exact retained resolution/check commands for this plan."""
    require(receipt.get('plan_sha256') == sha(root/receipt.get('plan_path', '')), 'query receipt plan mismatch')
    rt = plan['runtime']
    execution_root = receipt.get('execution_root')
    require(isinstance(execution_root,str) and Path(execution_root).is_absolute(), 'missing receipt execution root')
    references = receipt.get('queries')
    expected = {str(path.relative_to(root)) for case in load_population(root)[1].values() for path in query_files(case).values()}
    require(isinstance(references, dict) and set(references) == expected, 'query receipt membership')
    for query, row in references.items():
        require(row.get('query_sha256') == sha(root/query), 'query receipt source mismatch')
        for kind in ['resolve', 'compile']:
            record = read(bound_file(root, row[kind]))
            require(record.get('cwd') == execution_root, 'query receipt working-directory mismatch')
            argv = [rt['codeql'],'resolve','library-path','--query='+str(Path(execution_root)/query),'--additional-packs='+rt['packs'],'--format=json'] if kind == 'resolve' else [rt['codeql'],'query','compile',str(Path(execution_root)/query),'--check-only','--additional-packs='+rt['packs'],'--threads=2','--ram=2048']
            require(record.get('argv') == argv and type(record.get('exit_status')) is int and record['exit_status'] == 0 and record.get('timed_out') is False and record.get('cleanup_status') == 'tracked-processes-stopped', 'query receipt command failed/mismatched')
            require(type(record.get('elapsed_seconds')) in (int,float) and 0 <= record['elapsed_seconds'] <= record.get('deadline_seconds',0) <= 75, 'query receipt budget')
        resolution = read(bound_file(root,row['resolution_stdout']))
        expected_path = str(Path(rt['packs'])/'codeql/swift-all/6.8.4-dfb.entry1')
        require(expected_path in resolution.get('libraryPath',[]), 'wrong resolved Swift library')
        require(resolution.get('dbscheme') == expected_path+'/swift.dbscheme', 'wrong resolved schema')
        allowed_query = str((Path(execution_root)/query).parent)
        require(all(path == allowed_query or Path(path).is_relative_to(Path(rt['packs'])) for path in resolution['libraryPath']), 'unbound query dependency')
        require(not any('/codeql/swift-all/' in path and path != expected_path for path in resolution['libraryPath']), 'mixed Swift library resolution')


def prepare(root, directory, runtime):
    """Write an exact nonexecuted plan; immutable once committed for execution."""
    require(not directory.exists(), 'plan directory exists')
    population, cases, ph = load_population(root)
    repair = Path(runtime['repair'])
    pins = dict(cli_version='2.27.1', cli_build='938af3639d0709b587251e45d9f8d2bdc3505696',
                extractor_sha256=sha(repair/'candidate-extractor/swift/tools/osx64/extractor.real'),
                schema_sha256=sha(repair/'candidate-extractor/swift/swift.dbscheme'),
                packs_manifest_sha256=sha(repair/'candidate-pack-manifest.json'))
    require(sha(repair/'candidate-packs/codeql/swift-all/6.8.4-dfb.entry1/swift.dbscheme') == pins['schema_sha256'], 'extractor/query schema mismatch')
    require(pins['extractor_sha256'] == '593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f', 'unreviewed extractor')
    identity = patched_identity({'productName':'CodeQL','version':pins['cli_version'],'sha':pins['cli_build']}, pins)
    directory.mkdir(parents=True)
    runtime = dict(runtime)
    runtime['extractor_root'] = str(repair/'candidate-extractor')
    runtime['packs'] = str(repair/'candidate-packs')
    manifests = {}
    for name, source in [('extractor', repair/'candidate-extractor-manifest.json'), ('packs', repair/'candidate-pack-manifest.json')]:
        destination = directory/(name+'-files.json');shutil.copyfile(source,destination);manifests[name] = ref(root,destination)
    # Bind the entire installed CLI file surface, not only its launcher.
    cli_root = Path(runtime['codeql']).parent
    cli_manifest = {str(p.relative_to(cli_root)):sha(p) for p in sorted(cli_root.rglob('*')) if p.is_file()}
    write(directory/'cli-files.json',cli_manifest);manifests['cli'] = ref(root,directory/'cli-files.json')
    runtime['compiler_root'] = str(Path(runtime['compiler']).resolve().parent.parent)
    runtime['sdk_root'] = str(Path(runtime['sdk']).resolve())
    for name in ['compiler', 'sdk']:
        write(directory/(name+'-tree.json'),file_inventory(Path(runtime[name+'_root'])))
        manifests[name] = ref(root,directory/(name+'-tree.json'))
    runtime['manifests'] = manifests
    runtime['compiler_sha256'] = sha(Path(runtime['compiler']))
    runtime['sdk_settings_sha256'] = sha(Path(runtime['sdk'])/'SDKSettings.json')
    runtime['pins'] = pins
    contract = {'population_sha256':ph,'fixture_revision':population['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,
                'phases':{'extraction':{'wall_clock_seconds':150,'peak_memory_mb':2048},'analysis':{'wall_clock_seconds':75,'peak_memory_mb':2048}},
                'phase_sequences':{'standard':sequence(['roles','flow']),'persistence':sequence(['roles','flow','coverage','scopes'])}}
    write(directory/'contract.json',contract)
    files = [root/'scripts'/name for name in ['swift_normal_runner_v1.py','run-swift-normal-v1.py','swift_normal_reports_v1.py','swift_v3_runner.py','swift_v2_process.py','swift_extraction_integrity.py','swift_persistence_coverage.py','swift_artifact_closure.py']]
    files += [p for p in (root/BASE/'queries').rglob('*') if p.is_file()]
    files += [directory/'contract.json',*(root/r['path'] for r in manifests.values())]
    config = [ref(root,p) for p in files]
    plan = {'schema':'swift-normal-report-plan/v1','population_sha256':ph,'fixture_revision':population['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,
            'registered_at_unix_seconds':int(time.time()),'identity':identity,'execution_contract':ref(root,directory/'contract.json'),'configurations':{'patched-codeql':config},
            'cases':{i:{'configuration':'patched-codeql','disposition':'attempt','phase_sequence':'persistence' if c['template_id']=='dfb-template-native-persistence' else 'standard'} for i,c in cases.items()},
            'runtime':runtime,'resource_reservation':{'launch_free_bytes':LAUNCH_CAPACITY,'minimum_free_bytes':MINIMUM_RESERVE,'status':'not-reserved'},'output_root':'reports/raw/swift-normal-v1'}
    write(directory/'plan.json',plan)
    return plan


def verify_runtime(root, plan):
    rt=plan['runtime'];repair=Path(rt['repair'])
    for name,base in [('extractor',Path(rt['extractor_root'])/'swift'),('packs',Path(rt['packs'])),('cli',Path(rt['codeql']).parent)]:
        manifest=read(bound_file(root,rt['manifests'][name]))
        require({str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()} == set(manifest),'runtime file membership drift: '+name)
        for path,digest in manifest.items():require(sha(base/path)==digest,'runtime file drift: '+name+'/'+path)
    for name in ['compiler','sdk']:
        require(file_inventory(Path(rt[name+'_root'])) == read(bound_file(root,rt['manifests'][name])), 'full runtime tree drift: '+name)
    require(sha(Path(rt['compiler']))==rt['compiler_sha256'],'compiler drift')
    require(sha(Path(rt['sdk'])/'SDKSettings.json')==rt['sdk_settings_sha256'],'SDK drift')
    require(sha(bound_file(root,rt['manifests']['packs']))==rt['pins']['packs_manifest_sha256'],'pack identity drift')


def check_queries(root, plan_path, output):
    """Bounded resolve/check-only route; no extraction or query evaluation."""
    plan = read(root/plan_path)
    verify_runtime(root,plan)
    for refs in plan['configurations'].values():
        for reference in refs:bound_file(root,reference)
    capacity(shutil.disk_usage(root).free)
    require(not output.exists(), 'qualification output already exists')
    output.mkdir(parents=True)
    rt=plan['runtime'];queries=sorted({str(p.relative_to(root)) for c in load_population(root)[1].values() for p in query_files(c).values()})
    commands={}
    for index,query in enumerate(queries):
        commands[query]={'resolve':[rt['codeql'],'resolve','library-path','--query='+str(root/query),'--additional-packs='+rt['packs'],'--format=json'],
                         'compile':[rt['codeql'],'query','compile',str(root/query),'--check-only','--additional-packs='+rt['packs'],'--threads=2','--ram=2048']}
    registration={'plan_path':plan_path,'plan_sha256':sha(root/plan_path),'mode':'resolve-and-check-only-no-evaluation','seconds_per_command':75,'minimum_free_bytes':MINIMUM_RESERVE,'aggregate_ram':'unqualified; tool may raise requested2048 minimum','commands':commands}
    write(output/'preregistration.json',registration)
    receipt={'plan_path':plan_path,'plan_sha256':sha(root/plan_path),'execution_root':str(root),'queries':{},'status':'incomplete'}
    for index,query in enumerate(queries):
        directory=output/str(index);directory.mkdir()
        row={'query_sha256':sha(root/query)}
        for kind,argv in commands[query].items():
            capacity(shutil.disk_usage(root).free)
            record=process.run(argv,directory,kind,75,cwd=root)
            row[kind]=ref(root,directory/(kind+'.command.json'))
            row[kind+'_stdout']=ref(root,directory/(kind+'.stdout'))
            row[kind+'_stderr']=ref(root,directory/(kind+'.stderr'))
            if record['exit_status']!=0 or record['timed_out'] or record['cleanup_status']!='tracked-processes-stopped':
                receipt['queries'][query]=row;write(output/'receipt.json',receipt)
                raise ValueError('CompatibilityFailed:'+query+':'+kind)
        row['resolution_stdout']=row['resolve_stdout'];receipt['queries'][query]=row
        write(output/'receipt.json',receipt)
        print('checked '+query,flush=True)
    verify_query_receipt(root,plan,receipt)
    receipt['status']='checked-only';write(output/'receipt.json',receipt)
    return receipt


def run_phase(argv, directory, spec, deadline, invoke=process.run):
    try:
        record = invoke(argv,directory,spec['id'],deadline,cwd=ROOT)
    except process.ProcessCleanupError:
        path = directory/(spec['id']+'.command.json')
        if path.exists():
            record = read(path);record.update(phase_id=spec['id'],role=spec['role']);write(path,record)
        raise
    record.update(phase_id=spec['id'],role=spec['role'])
    write(directory/(spec['id']+'.command.json'),record)
    require(record.get('cleanup_status')=='tracked-processes-stopped','UncertainCleanup')
    if record['timed_out'] or record['elapsed_seconds'] > deadline:
        raise TimeoutError('BudgetExhausted')
    require(record['exit_status']==0,'CommandFailed:'+spec['id'])
    return record


def execute(root, plan_path, output, reservation):
    plan=read(root/plan_path);rt=plan['runtime'];contract=read(bound_file(root,plan['execution_contract']))
    receipt = read(bound_file(root,reservation.get('query_qualification')))
    require(receipt.get('plan_path') == plan_path, 'query qualification names another plan')
    verify_query_receipt(root,plan,receipt)
    population,cases,ph=load_population(root)
    require(plan['population_sha256']==ph and plan['fixture_revision']==population['fixture_revision'],'plan population drift')
    registered=[plan_path,plan['execution_contract']['path'],*[r['path'] for refs in plan['configurations'].values() for r in refs]]
    subprocess.run(['git','diff','--quiet','HEAD','--',*registered],cwd=root,check=True)
    subprocess.run(['git','ls-files','--error-unmatch','--',*registered],cwd=root,check=True,stdout=subprocess.DEVNULL)
    require(reservation.get('plan_sha256')==sha(root/plan_path) and reservation.get('launch_free_bytes',0)>=LAUNCH_CAPACITY and reservation.get('exclusive_analyzer_slot') is True,'missing exact-plan capacity reservation')
    verify_runtime(root,plan)
    for refs in plan['configurations'].values():
        for reference in refs:bound_file(root,reference)
    capacity(shutil.disk_usage(root).free,launch=True)
    require(not output.exists() and output.resolve().is_relative_to((root/plan['output_root']).resolve()),'new versioned output required')
    output.mkdir(parents=True)
    write(output/'reservation.json',reservation)
    start=int(time.time());require(plan['registered_at_unix_seconds']<start,'plan must precede execution')
    cli=rt['codeql'];version=process.run([cli,'version','--format=json'],output,'version',30,cwd=root)
    require(version['exit_status']==0 and not version['timed_out'] and version['cleanup_status']=='tracked-processes-stopped','failed identity witness')
    observed=patched_identity(read(output/'version.stdout'),rt['pins']);require(observed==plan['identity'],'plan identity mismatch')
    write(output/'identity.json',{'observed':observed,'observed_at_unix_seconds':int(time.time()),'command':version,'stdout':ref(root,output/'version.stdout')})
    run={'schema':'swift-normal-report-run/v1','plan_sha256':sha(root/plan_path),'population_sha256':ph,'fixture_revision':population['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,'started_at_unix_seconds':start,'ended_at_unix_seconds':int(time.time()),'cold_or_warm':'cold','identity':observed,'identity_witness':ref(root,output/'identity.json'),'results':[]}
    selected={c['id']:c for c in population['cases']}
    for case_id,case in cases.items():
        try:capacity(shutil.disk_usage(root).free)
        except ValueError as error:
            write(output/'stop.json',{'reason':str(error),'unattempted_case_ids':[i for i in cases if i not in {r['case_id'] for r in run['results']}],'full_report':False});break
        directory=output/case_id;directory.mkdir();source=directory/'source';source.mkdir()
        for name in case['fixture_files']:shutil.copyfile((root/selected[case_id]['path']).parent/name,source/name)
        conf=plan['cases'][case_id]['configuration'];seq=phase_sequence(contract,plan['cases'][case_id]['phase_sequence'])
        raw={'schema':'swift-normal-raw/v1','case_id':case_id,'plan_sha256':run['plan_sha256'],'population_sha256':ph,'fixture_revision':population['fixture_revision'],'configuration_hash':configuration_hash(root,plan['configurations'][conf]),'identity_witness_sha256':run['identity_witness']['sha256'],'execution_contract_sha256':plan['execution_contract']['sha256'],'raw_outcome':'inconclusive','state':'inconclusive','duration_ms':0,'diagnostics':[],'witness_checkpoints':[],'executed':True,'commands':[],'native_outputs':[],'analysis_elapsed_seconds':0}
        case_start=time.monotonic();analysis_start=None;rows={};stop=False
        try:
            compile_argv=[rt['compiler'],'-swift-version','6','-Onone','-sdk',rt['sdk'],'-target','arm64-apple-macosx26.5','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(directory/'cache'),*[str(source/n) for n in case['fixture_files']],'-o',str(directory/'never-executed')]
            db=directory/'database'
            run_phase([cli,'database','create',str(db),'--language=swift','--search-path='+rt['extractor_root'],'--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(compile_argv)],directory,seq[0],150)
            require('finalised: true' in (db/'codeql-database.yml').read_text(),'DatabaseNotFinalized')
            integrity=inspect_logs(db/'log/swift/extractor')
            write(directory/'extraction-integrity.json',integrity)
            require(integrity['ready_for_observation'],'ExtractionIncomplete')
            shutil.copyfile(db/'codeql-database.yml',directory/'database-finalization.txt')
            analysis_start=time.monotonic();queries=query_files(case)
            for spec in seq[1:]:
                capacity(shutil.disk_usage(root).free)
                remaining=75-(time.monotonic()-analysis_start)
                if remaining<=0:raise TimeoutError('BudgetExhausted')
                name=spec['id'];query_name=name.removesuffix('-decode')
                argv=[cli,'bqrs','decode',str(directory/(query_name+'.bqrs')),'--format=json','--output='+str(directory/(query_name+'.json'))] if name.endswith('-decode') else [cli,'query','run',str(queries[name]),'--database='+str(db),'--output='+str(directory/(name+'.bqrs')),'--additional-packs='+rt['packs'],'--threads=2','--ram=2048']
                run_phase(argv,directory,spec,remaining)
                if name.endswith('-decode'):rows[query_name]=read(directory/(query_name+'.json'))['#select']['tuples']
            raw['raw_outcome'],raw['diagnostics']=observe(case,rows['roles'],rows['flow'],lane(case))
            if 'coverage' in rows:
                assessment=assess_coverage(rows['coverage'],[r[0] for r in rows['scopes']])
                if assessment.status is CoverageStatus.INCOMPLETE:raw['raw_outcome']='inconclusive';raw['diagnostics'].extend(assessment.reasons)
        except TimeoutError:raw['raw_outcome']='inconclusive';raw['diagnostics'].append('BudgetExhausted')
        except Exception as error:
            raw['raw_outcome']='runner-error';raw['diagnostics'].append(str(error));stop=isinstance(error,process.ProcessCleanupError) or str(error) in ('UncertainCleanup','DiskReserveReached')
        finally:
            raw['duration_ms']=int((time.monotonic()-case_start)*1000)
            raw['analysis_elapsed_seconds']=time.monotonic()-analysis_start if analysis_start is not None else 0
            if raw['analysis_elapsed_seconds']>75:
                raw['diagnostics'].append('BudgetExhausted')
                if raw['raw_outcome']!='runner-error':raw['raw_outcome']='inconclusive'
            raw['state']=normalized(raw['raw_outcome'])
            if (directory/'database').exists():
                write(directory/'database-closure.json',snapshot(directory/'database'))
            raw['runtime_manifest_sha256']={name:reference['sha256'] for name,reference in rt['manifests'].items()}
            for spec in seq:
                command=directory/(spec['id']+'.command.json')
                if command.exists():raw['commands'].append(ref(root,command))
            raw['native_outputs']=[ref(root,p) for p in sorted(directory.iterdir()) if p.is_file() and p.suffix in ('.stdout','.stderr','.bqrs','.json','.txt') and not p.name.endswith('.command.json')]
            if len(raw['commands'])<len(seq) and 'BudgetExhausted' not in raw['diagnostics']:raw['diagnostics'].append('IncompleteExecution')
            write(directory/'raw.json',raw);run['results'].append({'case_id':case_id,'configuration':conf,'raw':ref(root,directory/'raw.json')});run['ended_at_unix_seconds']=int(time.time());write(output/'run.json',run)
        if stop:break
    if len(run['results'])==len(cases):
        bundle=export(root,plan_path,run);normal=output/'normal';normal.mkdir()
        for index,report in enumerate(bundle['reports'].values()):write(normal/f'report-{index}.json',report)
        write(normal/'audit.json',bundle['audit'])
    return run
