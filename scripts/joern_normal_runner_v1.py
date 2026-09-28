"""Serial, prospective Joern controls and current108 execution; no implicit launch."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import swift_v2_process as process
from joern_execution_revalidation_v1 import AMENDMENT, REVIEWED, EXECUTION, verify as verify_execution
from joern_normal_execution_v1 import env_for, compiler_argv, frontend_argv, query_argv
from swift_artifact_closure import snapshot
from swift_normal_reports_v1 import ROOT, read, sha, require, bound_file, load_population, configuration_hash, normalized
from swift_normal_runner_v1 import file_inventory, ref, write
from joern_normal_controls_v1 import BASE, OPAQUE, config_for, observe, assess_controls

RESERVE=40*1024**3
SCRATCH=2*1024**3
ADAPTER='joern-normal-v1'
VERSION='4.0.628'
PHASES=[{'id':name,'role':'analysis'} for name in ['typecheck','frontend','query']]


def capacity(free,launch=False):
    require(free>=RESERVE+(SCRATCH if launch else 0),'InsufficientLaunchCapacity' if launch else 'DiskReserveReached')


def runtime_inventory(runtime):
    return {name:file_inventory(Path(runtime[name])) for name in ['joern_root','java_home','compiler_root','sdk']}


def identity(runtime):
    return {'tool':'joern','tool_version':VERSION,'tool_build_identity':'joern-cli:'+VERSION+';engine:'+runtime['engine_sha256']+';frontend:'+runtime['frontend_sha256'],'adapter_version':ADAPTER}


def compiler_launcher(path):
    path=Path(path)
    return str(path.parent.resolve()/path.name)


def prepare(root,directory,runtime):
    require(not directory.exists(),'plan directory exists')
    population,cases,digest=load_population(root)
    runtime=dict(runtime)
    for key in ['joern','java_home','sdk']:runtime[key]=str(Path(runtime[key]).resolve())
    # swiftc driver spelling is an input to SwiftAstGen's compiler-log parser.
    # Resolve its parent, not the executable symlink (which names swift-frontend).
    runtime['compiler']=compiler_launcher(runtime['compiler'])
    runtime['joern_root']=str(Path(runtime['joern']).parent)
    runtime['compiler_root']=str(Path(runtime['compiler']).parent.parent)
    runtime['frontend']=str(Path(runtime['joern_root'])/'frontends/swiftsrc2cpg/bin/swiftsrc2cpg')
    runtime['astgen']=str(Path(runtime['joern_root'])/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac')
    runtime['engine_sha256']=sha(Path(runtime['joern_root'])/('lib/io.joern.dataflowengineoss-'+VERSION+'.jar'))
    runtime['frontend_sha256']=sha(Path(runtime['joern_root'])/('frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-'+VERSION+'.jar'))
    # Exact retained assets constrain the bounded pin hold; this is not activation.
    activation=read(root/'adapters/joern/swift-v2/activation.json')
    for path,expected in activation['asset_sha256'].items():require(sha(Path(path))==expected,'pinned Joern asset drift')
    trees=runtime_inventory(runtime)
    directory.mkdir(parents=True)
    runtime['inventories']={}
    for name,tree in trees.items():
        target=directory/(name+'.json');write(target,tree);runtime['inventories'][name]=ref(root,target)
    contract={'schema':'joern-normal-contract/v1','phase_sequence':PHASES,'total_wall_clock_seconds':75,'aggregate_resource_qualification':'unavailable','scored_activation':False,'population_sha256':digest,'fixture_revision':population['fixture_revision'],'memory_policy':{'fixture_peak_memory_mb':512,'aggregate_enforcement':'unavailable','jvm_heap_request_mb':512}}
    write(directory/'contract.json',contract)
    files=['scripts/joern_normal_runner_v1.py','scripts/joern_normal_execution_v1.py','scripts/joern_execution_revalidation_v1.py',AMENDMENT,'scripts/joern_normal_controls_v1.py','scripts/joern_normal_reports_v1.py','scripts/run-joern-normal-v1.py','scripts/joern_swift.py','scripts/run-joern-swift-case.py','scripts/swift_v2_process.py','scripts/swift_normal_reports_v1.py','scripts/swift_normal_runner_v1.py','scripts/swift_artifact_closure.py','adapters/joern/swift/models.json',BASE+'/query.sc',BASE+'/README.md']
    refs=[ref(root,root/p) for p in files]+[ref(root,directory/'contract.json')]+list(runtime['inventories'].values())
    plan={'schema':'joern-normal-report-plan/v1','registered_at_unix_seconds':int(time.time()),'population_sha256':digest,'fixture_revision':population['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,'identity':identity(runtime),'runtime':runtime,'execution_contract':ref(root,directory/'contract.json'),'configurations':{'joern-current108':refs},'cases':{i:{'configuration':'joern-current108','disposition':'pending-capability'} for i in cases},'output_root':'reports/raw/joern-normal-v1','partition_status':'unresolved','resources':{'reserve_bytes':RESERVE,'scratch_allowance_bytes':SCRATCH,'launch_bytes':RESERVE+SCRATCH,'status':'not-reserved','cost_estimate':'2 GiB prospective serial one-CPG scratch allowance; unmeasured for current controls, not hard containment'}}
    write(directory/'plan.json',plan)
    # Four exact population fixtures plus canonical direct baseline pair.
    direct={}
    for polarity in ['positive','negative']:
        key='dfb-taint-swift-direct-'+polarity
        require(key in cases,'canonical direct baseline missing')
        direct['direct-'+polarity]=key
    selected=dict(direct);selected.update({i:i for i,c in cases.items() if c['template_id'] in OPAQUE})
    require(len(selected)==6,'six control fixtures required')
    control={'schema':'joern-normal-controls-plan/v1','plan':ref(root,directory/'plan.json'),'registered_at_unix_seconds':int(time.time()),'controls':selected,'arms':['off','on'],'max_invocations':36,'case_arm_total_seconds':75,'max_case_arm_seconds':900,'scratch_allowance_bytes':SCRATCH,'scored_activation':False,'claim':'identity-and-load-bearing-controls-only'}
    write(directory/'controls.json',control)
    return plan


def verify_runtime(root,plan):
    rt=plan['runtime']
    for name,tree in runtime_inventory(rt).items():require(tree==read(bound_file(root,rt['inventories'][name])),'runtime tree drift:'+name)
    for key in ['joern','frontend','astgen','compiler']:
        require(Path(rt[key]).stat().st_mode & 0o111,'runtime not executable:'+key)


def registered(root,paths):
    subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=root,check=True)
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths],cwd=root,check=True,stdout=subprocess.DEVNULL)


def preflight(root,plan_path,reservation,extra=()):
    plan=read(root/plan_path)
    population,cases,digest=load_population(root)
    require(plan['population_sha256']==digest and plan['fixture_revision']==population['fixture_revision'],'population drift')
    refs=[r for rows in plan['configurations'].values() for r in rows]
    for r in refs:bound_file(root,r)
    registered(root,[plan_path,plan['execution_contract']['path'],*[r['path'] for r in refs],*extra])
    require(reservation.get('plan_sha256')==sha(root/plan_path) and reservation.get('exclusive_analyzer_slot') is True and reservation.get('launch_free_bytes',0)>=RESERVE+SCRATCH,'missing exact-plan exclusive capacity reservation')
    capacity(shutil.disk_usage(root).free,True)
    verify_runtime(root,plan)
    return plan,population,cases



def phase(argv,directory,name,deadline,env,invoke=process.run):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('BudgetExhausted')
    capacity(shutil.disk_usage(directory).free)
    try:record=invoke(argv,directory,name,remaining,env=env,cwd=directory)
    except BaseException:
        path=directory/(name+'.command.json')
        if path.exists():
            record=read(path);record.update(phase_id=name,role='analysis');write(path,record)
        raise
    record.update(phase_id=name,role='analysis');write(directory/(name+'.command.json'),record)
    require(record.get('cleanup_status')=='tracked-processes-stopped','UncertainCleanup')
    if record['timed_out'] or record['elapsed_seconds']>remaining:raise TimeoutError('BudgetExhausted')
    require(record['exit_status']==0,'CommandFailed:'+name)
    return record


def run_case(root,plan,case_path,case,directory,mode='on'):
    directory.mkdir(parents=True,exist_ok=False)
    rt=plan['runtime'];source=directory/'DataFlowBenchTaintSwift';source.mkdir()
    for name in case['fixture_files']:
        relative=Path(name);require(not relative.is_absolute() and '..' not in relative.parts and len(relative.parts)==1 and relative.suffix=='.swift','unsafe fixture')
        original=case_path.parent/name;require(not original.is_symlink(),'symlink fixture')
        shutil.copyfile(original,source/name)
    config=config_for(root,case,mode);write(directory/'config.json',config)
    start=time.monotonic();deadline=start+75;outcome='runner-error';diagnostics=[];stop=False
    env=env_for(rt);cpg=directory/'cpg.bin'
    try:
        argv=compiler_argv(rt,case,directory)
        phase(argv,directory,'typecheck',deadline,env)
        write(directory/'fixture-hashes.json',{name:sha(source/name) for name in case['fixture_files']})
        import shlex
        (directory/'build.log').write_text(shlex.join(argv)+'\n')
        phase(frontend_argv(rt,directory),directory,'frontend',deadline,env)
        log=(directory/'frontend.stdout').read_text()+(directory/'frontend.stderr').read_text()
        counts=re.findall(r'Got (\d+) type map entries\.',log)
        require(counts and int(counts[-1])>=len(case['fixture_files']) and cpg.is_file() and cpg.stat().st_size>0,'Incomplete:SwiftImport')
        require(not re.search(r'\[(?:ERROR|WARN)\]',log),'Incomplete:FrontendDiagnostics')
        phase(query_argv(root,rt,directory),directory,'query',deadline,env)
        outcome,diagnostics=observe(read(directory/'graph.json'),config)
        require(time.monotonic()<=deadline,'BudgetExhausted')
    except KeyboardInterrupt:outcome='runner-error';diagnostics.append('Cancelled');stop=True
    except TimeoutError:outcome='inconclusive';diagnostics.append('BudgetExhausted');stop=True
    except Exception as error:
        reason=str(error);diagnostics.append(reason)
        outcome='inconclusive' if reason.startswith('Incomplete:') or reason=='BudgetExhausted' else 'runner-error'
        stop=isinstance(error,process.ProcessCleanupError) or reason in ('UncertainCleanup','DiskReserveReached','BudgetExhausted')
    elapsed=time.monotonic()-start
    if elapsed>75:
        diagnostics.append('BudgetExhausted');stop=True
        if outcome!='runner-error':outcome='inconclusive'
    # Closure preserves CPG/source after all commands; failure never masks results.
    try:
        write(directory/'source-closure.json',snapshot(source))
        require(all(sha(source/n)==sha(case_path.parent/n) for n in case['fixture_files']),'StagedFixtureDrift')
    except Exception as error:
        diagnostics.append('ArtifactClosureFailed:'+str(error));stop=True
        if outcome!='runner-error':outcome='inconclusive'
    commands=[ref(root,directory/(p['id']+'.command.json')) for p in PHASES if (directory/(p['id']+'.command.json')).exists()]
    if len(commands)!=3 and 'BudgetExhausted' not in diagnostics:diagnostics.append('IncompleteExecution')
    outputs=[ref(root,p) for p in sorted(directory.iterdir()) if p.is_file() and not p.name.endswith('.command.json')]
    return {'raw_outcome':outcome,'state':normalized(outcome),'diagnostics':diagnostics,'duration_ms':int(elapsed*1000),'total_elapsed_seconds':elapsed,'commands':commands,'native_outputs':outputs,'witness_checkpoints':[],'executed':True},stop


def controls(root,plan_path,control_path,output,reservation):
    control=read(root/control_path)
    require(control.get('arms')==['off','on'] and control.get('case_arm_total_seconds')==75 and control.get('max_invocations')==36,'control budget/arms drift')
    require(control['schema']=='joern-normal-controls-plan/v1' and control['plan']==ref(root,root/plan_path),'control plan binding')
    require(reservation.get('controls_sha256')==sha(root/control_path),'control reservation mismatch')
    plan,population,cases=preflight(root,plan_path,reservation,[control_path])
    expected={i:i for i,c in cases.items() if c['template_id'] in OPAQUE}
    expected.update({'direct-'+p:'dfb-taint-swift-direct-'+p for p in ['positive','negative']})
    require(control.get('controls')==expected,'exact control membership required')
    require(control['registered_at_unix_seconds']<int(time.time()),'controls must precede execution')
    require(not output.exists() and output.resolve().is_relative_to((root/plan['output_root']).resolve()),'new owned output required')
    output.mkdir(parents=True);write(output/'reservation.json',reservation)
    paths={row['id']:root/row['path'] for row in population['cases']}
    result={'schema':'joern-normal-controls-run/v1','plan_sha256':sha(root/plan_path),'controls_sha256':sha(root/control_path),'started_at_unix_seconds':int(time.time()),'observations':{},'records':[],'scored_activation':False}
    initial=shutil.disk_usage(root).free
    version=process.run([plan['runtime']['joern']],output,'version',30,env=env_for(plan['runtime']),cwd=output)
    require(version['exit_status']==0 and not version['timed_out'] and version['cleanup_status']=='tracked-processes-stopped','failed version witness')
    require(re.search(r'(?<![0-9.])4\.0\.628(?![0-9.])',(output/'version.stdout').read_text()),'unexpected Joern version')
    result['identity_witness']={'command':ref(root,output/'version.command.json'),'stdout':ref(root,output/'version.stdout'),'observed':identity(plan['runtime'])}
    for label,case_id in control['controls'].items():
        for arm in control['arms']:
            if shutil.disk_usage(root).free<RESERVE+SCRATCH or sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>SCRATCH:
                write(output/'stop.json',{'reason':'ControlScratchAllowanceReached','full_report':False});write(output/'run.json',result);return result
            try:raw,stop=run_case(root,plan,paths[case_id],cases[case_id],output/label/arm,arm)
            except Exception as error:
                write(output/'stop.json',{'reason':'PrelaunchFailure:'+str(error),'case_id':case_id,'arm':arm,'executed':False,'full_report':False});write(output/'run.json',result);return result
            raw.update(plan_sha256=sha(root/plan_path),controls_sha256=sha(root/control_path),case_id=case_id,arm=arm,fixture_hashes={n:sha(paths[case_id].parent/n) for n in cases[case_id]['fixture_files']})
            write(output/label/arm/'raw.json',raw)
            result['records'].append({'control':label,'case_id':case_id,'arm':arm,'raw':ref(root,output/label/arm/'raw.json')})
            result['observations'].setdefault(label,{})[arm]=raw['raw_outcome']
            result['ended_at_unix_seconds']=int(time.time())
            result['observed_free_space_delta_bytes']=initial-shutil.disk_usage(root).free
            write(output/'run.json',result)
            print(label,arm,raw['raw_outcome'],raw['diagnostics'],flush=True)
            if stop or (label.startswith('direct-') and raw['raw_outcome'] not in ('reached','not-reached')):
                write(output/'stop.json',{'reason':raw['diagnostics'],'unattempted_arms':[[l,a] for l in control['controls'] for a in control['arms'] if (l,a) not in {(r['control'],r['arm']) for r in result['records']}],'full_report':False});return result
    result['assessment']=assess_controls(result['observations']);write(output/'run.json',result)
    return result


def verify_controls(root,control_path,run_path,activation_scope="opaque-models"):
    """Replay retained raw graphs, fixture identity and exact prospective matrix."""
    from joern_normal_reports_v1 import validate_phases
    control=read(root/control_path);plan_path=control['plan']['path']
    plan=read(bound_file(root,control['plan']));run=read(root/run_path)
    require(run.get('schema')=='joern-normal-controls-run/v1' and run.get('plan_sha256')==sha(root/plan_path) and run.get('controls_sha256')==sha(root/control_path),'control run binding')
    require(control['registered_at_unix_seconds']<run['started_at_unix_seconds']<=run['ended_at_unix_seconds'],'control chronology')
    _,cases,digest=load_population(root)
    require(plan['population_sha256']==digest,'control population drift')
    control_semantics(root,plan)
    witness=run['identity_witness'];command=read(bound_file(root,witness['command']))
    require(witness['observed']==plan['identity'] and command['argv']==[plan['runtime']['joern']] and command['exit_status']==0 and command['timed_out'] is False and command['cleanup_status']=='tracked-processes-stopped','control version witness')
    require(re.search(r'(?<![0-9.])4\.0\.628(?![0-9.])',bound_file(root,witness['stdout']).read_text()),'control version mismatch')
    expected={(label,arm) for label in control['controls'] for arm in ['off','on']}
    require(len(run['records'])==12 and {(r['control'],r['arm']) for r in run['records']}==expected,'incomplete control matrix')
    population=read(root/'populations/swift-synthetic-v3.json');paths={c['id']:root/c['path'] for c in population['cases']}
    observations={}
    for row in run['records']:
        label,arm=row['control'],row['arm'];case_id=control['controls'][label]
        require(row['case_id']==case_id,'control routing mismatch')
        raw=read(bound_file(root,row['raw']))
        require(raw.get('plan_sha256')==sha(root/plan_path) and raw.get('controls_sha256')==sha(root/control_path) and raw.get('case_id')==case_id and raw.get('arm')==arm,'raw control binding')
        require(raw.get('fixture_hashes')=={n:sha(paths[case_id].parent/n) for n in cases[case_id]['fixture_files']},'control fixture drift')
        for reference in raw['native_outputs']:bound_file(root,reference)
        directory=(root/row['raw']['path']).parent
        for name in ['graph.json','config.json']:
            require(any(ref['path']==str((directory/name).relative_to(root)) for ref in raw['native_outputs']),'missing native control graph/config')
        config=config_for(root,cases[case_id],arm)
        require(read(directory/'config.json')==config,'control configuration drift')
        outcome,diagnostics=observe(read(directory/'graph.json'),config)
        require(outcome==raw['raw_outcome'] and raw['state']==normalized(outcome),'control raw outcome drift')
        require(diagnostics==raw['diagnostics'],'control diagnostic drift')
        if activation_scope=='opaque-models' or label.startswith('direct-'):
            require(not diagnostics,'required activation control incomplete')
        validate_phases(root,raw,PHASES,raw['state'],raw['diagnostics'])
        observations.setdefault(label,{})[arm]=outcome
    require(observations==run['observations'],'control observation mismatch')
    assessment=assess_controls(observations)
    require(assessment==run.get('assessment'),'control assessment drift')
    require(activation_scope in ('diagnostic-identity-gated','opaque-models'),'unknown activation scope')
    if activation_scope=='opaque-models':require(assessment['status']=='bounded-controls-observed','load-bearing control matrix failed')
    else:
        require(observations['direct-positive']=={'off':'reached','on':'reached'} and observations['direct-negative']=={'off':'not-reached','on':'not-reached'},'direct diagnostic baseline failed')
    return assessment


def control_semantics(root,plan):
    # All code/configuration capable of changing compilation, identity or models
    # must match the observed control plan. Plan manifests use stable role keys.
    reviewed=set(REVIEWED+[EXECUTION,'scripts/joern_execution_revalidation_v1.py',AMENDMENT])
    files={r['path']:r['sha256'] for rows in plan['configurations'].values() for r in rows if '/plan-' not in r['path'] and r['path'] not in reviewed}
    for path,digest in files.items():require(sha(root/path)==digest,'control semantic file drift')
    rt=plan['runtime']
    return {'files':files,'contract':read(bound_file(root,plan['execution_contract'])),'runtime':{k:v for k,v in rt.items() if k!='inventories'},'trees':{k:read(bound_file(root,v)) for k,v in rt['inventories'].items()}}


def validate_capability(case,planned,scope):
    capability=planned.get('capability')
    require(isinstance(capability,dict) and capability.get('identity_gate')=='exact-native-edges','case capability identity gate required')
    if scope=='diagnostic-identity-gated':
        require(capability.get('model_status')=='unqualified' and capability.get('model_mode')=='off','diagnostic admission cannot activate models')
    else:
        require(case['template_id'] in OPAQUE and capability.get('model_status')=='activated' and capability.get('model_mode')=='on','opaque activation does not qualify other families')
    return capability


def admitted_cases(value):
    require(isinstance(value,list) and all(isinstance(i,str) and i for i in value) and len(value)==len(set(value)),'unique admitted case IDs required')
    return set(value)


def verify_activation(root,plan):
    receipt=read(bound_file(root,plan.get('activation_receipt')))
    require(receipt.get('schema')=='joern-current108-activation/v1' and receipt.get('population_sha256')==plan['population_sha256'],'current activation receipt required')
    require(receipt.get('identity')==plan['identity'] and receipt.get('configuration_hash')==configuration_hash(root,plan['configurations']['joern-current108']),'activation identity/configuration mismatch')
    require(type(receipt.get('reviewed_at_unix_seconds')) is int and receipt['reviewed_at_unix_seconds']<=plan['registered_at_unix_seconds'],'activation review must precede plan')
    require(receipt.get('evidence') and isinstance(receipt['evidence'],list),'activation evidence missing')
    for reference in receipt['evidence']:bound_file(root,reference)
    control_plan=bound_file(root,receipt.get('control_plan'));control_run=bound_file(root,receipt.get('control_run'))
    scope=receipt.get('scope')
    require(scope in ('diagnostic-identity-gated','opaque-models'),'activation scope required')
    verify_controls(root,str(control_plan.relative_to(root)),str(control_run.relative_to(root)),scope)
    _,cases,_=load_population(root)
    admitted=admitted_cases(receipt.get('admitted_case_ids'))
    require(admitted=={i for i,c in plan['cases'].items() if c['disposition']=='attempt'},'admitted case membership')
    for case_id in admitted:
        validate_capability(cases[case_id],plan['cases'][case_id],scope)
    require(receipt['reviewed_at_unix_seconds']>=read(control_run)['ended_at_unix_seconds'],'activation review predates controls')
    controls=read(control_plan)
    observed_plan=read(bound_file(root,controls['plan']))
    require(isinstance(receipt.get('execution_revalidation'),dict),'bound execution revalidation required')
    amendment=verify_execution(root,receipt['execution_revalidation'],plan)
    require(amendment['control_plan']==receipt['control_plan'] and amendment['control_run']==receipt['control_run'],'activation execution evidence mismatch')
    require(control_semantics(root,observed_plan)==control_semantics(root,plan),'control query/model/runtime closure changed')
    return receipt


def execute(root,plan_path,output,reservation):
    plan=read(root/plan_path)
    require(plan.get('partition_status')=='resolved','Incomplete: current108 capability partition not registered')
    require(set(plan['cases'])==set(load_population(root)[1]),'current108 membership')
    require(all(c.get('disposition') in ('attempt','unsupported') for c in plan['cases'].values()),'pending capability decision')
    receipt=verify_activation(root,plan)
    amendment=read(bound_file(root,receipt['execution_revalidation']))
    extra=[plan['activation_receipt']['path'],receipt['execution_revalidation']['path']]
    extra.extend(r['path'] for r in [receipt['control_plan'],receipt['control_run'],*receipt['evidence'],amendment['registered_runner'],amendment['execution_module'],*amendment['reviewed_files']])
    plan,population,cases=preflight(root,plan_path,reservation,extra)
    require(plan['registered_at_unix_seconds']<int(time.time()),'plan must precede run')
    require(not output.exists() and output.resolve().is_relative_to((root/plan['output_root']).resolve()),'new owned output required')
    output.mkdir(parents=True);write(output/'reservation.json',reservation)
    started=int(time.time());rt=plan['runtime']
    version=process.run([rt['joern']],output,'version',30,env=env_for(rt),cwd=output)
    require(version['exit_status']==0 and not version['timed_out'] and version['cleanup_status']=='tracked-processes-stopped','failed version witness')
    banner=(output/'version.stdout').read_text()
    require(re.search(r'(?<![0-9.])4\.0\.628(?![0-9.])',banner),'unexpected Joern version banner')
    write(output/'identity.json',{'observed':identity(rt),'observed_at_unix_seconds':int(time.time()),'command':version,'stdout':ref(root,output/'version.stdout')})
    run={'schema':'joern-normal-report-run/v1','plan_sha256':sha(root/plan_path),'population_sha256':plan['population_sha256'],'fixture_revision':plan['fixture_revision'],'aggregate_resource_qualification':'unavailable','scored_activation':False,'started_at_unix_seconds':started,'ended_at_unix_seconds':started,'cold_or_warm':'cold','identity':identity(rt),'identity_witness':ref(root,output/'identity.json'),'activation_receipt':plan['activation_receipt'],'results':[]}
    paths={row['id']:root/row['path'] for row in population['cases']}
    for case_id,case in cases.items():
        planned=plan['cases'][case_id];key=planned['configuration'];stop=False
        try:capacity(shutil.disk_usage(root).free)
        except ValueError as error:
            write(output/'stop.json',{'reason':str(error),'unattempted_case_ids':[i for i in cases if i not in {r['case_id'] for r in run['results']}],'full_report':False});break
        if planned['disposition']=='unsupported':
            decision=read(bound_file(root,planned.get('decision')))
            require(decision.get('case_id')==case_id and decision.get('population_sha256')==plan['population_sha256'] and decision.get('identity')==plan['identity'] and decision.get('outcome')=='unsupported','fresh prospective unsupported decision required')
            require(decision.get('configuration_hash')==configuration_hash(root,plan['configurations'][key]),'unsupported configuration mismatch')
            require(type(decision.get('reviewed_at_unix_seconds')) is int and decision['reviewed_at_unix_seconds']<=plan['registered_at_unix_seconds'],'retrospective unsupported decision')
            require(decision.get('evidence') and decision.get('reason'),'unsupported evidence/rationale missing')
            for reference in decision['evidence']:bound_file(root,reference)
            (output/case_id).mkdir()
            raw={'raw_outcome':'unsupported','state':'unsupported','duration_ms':0,'total_elapsed_seconds':0,'diagnostics':[decision['reason']],'witness_checkpoints':[],'executed':False,'decision_sha256':planned['decision']['sha256'],'native_outputs':[],'commands':[]}
        else:
            try:raw,stop=run_case(root,plan,paths[case_id],case,output/case_id,planned['capability']['model_mode'])
            except Exception as error:
                write(output/'stop.json',{'reason':'PrelaunchFailure:'+str(error),'case_id':case_id,'executed':False,'unattempted_case_ids':[i for i in cases if i not in {r['case_id'] for r in run['results']}],'full_report':False});write(output/'run.json',run);break
        if planned['disposition']=='attempt':raw['capability']=planned['capability']
        raw.update(activation_receipt=plan['activation_receipt'],schema='joern-normal-raw/v1',case_id=case_id,plan_sha256=run['plan_sha256'],population_sha256=plan['population_sha256'],fixture_revision=plan['fixture_revision'],configuration_hash=configuration_hash(root,plan['configurations'][key]),identity_witness_sha256=run['identity_witness']['sha256'],execution_contract_sha256=plan['execution_contract']['sha256'])
        write(output/case_id/'raw.json',raw)
        run['results'].append({'case_id':case_id,'configuration':key,'raw':ref(root,output/case_id/'raw.json')})
        run['ended_at_unix_seconds']=int(time.time());write(output/'run.json',run)
        if stop:
            write(output/'stop.json',{'reason':raw['diagnostics'],'unattempted_case_ids':[i for i in cases if i not in {r['case_id'] for r in run['results']}],'full_report':False});break
    if len(run['results'])==108 and not (output/'stop.json').exists():
        from joern_normal_reports_v1 import export
        bundle=export(root,plan_path,run);(output/'normal').mkdir()
        for index,report in enumerate(bundle['reports'].values()):write(output/'normal'/f'report-{index}.json',report)
        write(output/'normal/audit.json',bundle['audit'])
    return run
