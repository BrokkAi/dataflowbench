"""Reproducible command/artifact binding, not cryptographic proof of execution."""
import math,shlex,zipfile,re
from pathlib import Path
from swift_v3_reports import read,sha,require,assemble,inputs
from swift_v3_runner import observe,lane
from swift_extraction_integrity import inspect_logs
from swift_persistence_coverage import assess_coverage,CoverageStatus


def number(n):return type(n) in [int,float] and math.isfinite(n) and n>=0


def verify_case(root,base,case,raw,paths):
    status=raw.get('execution_status');commands=raw.get('commands')
    require(status in ['not-attempted','attempted','completed'] and isinstance(commands,dict),'execution status/commands')
    require(raw.get('lane')==lane(case),'selected lane')
    if status=='not-attempted':
        require(raw['outcome']=='inconclusive' and not commands and raw['diagnostics'] in [['StoppedAfterUncertainCleanup'],['DiskReserveReached']],'not-attempted state')
        return
    selected=lane(case);names=['roles','flow']+(['coverage','scopes'] if case['template_id']=='dfb-template-native-persistence' else [])
    phases=['extract','resolve-database']+[v for n in names for v in [n,n+'-decode']]
    present=list(commands)
    require(bool(present) and present==phases[:len(present)] and len(present)<=len(phases),'phase prefix')
    if status=='completed':require(present==phases,'complete phase set')
    original=Path(paths['output'])/case['id'];db=original/'database';cli=paths['cli']
    compiler=[paths['compiler'],'-swift-version','6','-Onone','-sdk',paths['sdk'],'-target','arm64-apple-macosx26.5','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(original/'cache')]+[str(original/'source'/n) for n in case['fixture_files']]+['-o',str(original/'never-executed')]
    expected={'extract':[cli,'database','create',str(db),'--language=swift','--source-root='+str(original/'source'),'--threads=2','--ram=2048','--command='+shlex.join(compiler)],
              'resolve-database':[cli,'resolve','database','--format=json',str(db)]}
    queryroot=Path(paths['repository'])/('adapters/codeql/swift-native-composed-v1' if selected=='native' else 'adapters/codeql/swift-opaque-v3' if selected=='opaque' else 'adapters/codeql/swift-v3/queries')
    packs=paths['native_packs'] if selected=='native' else paths['packs'];elapsed=0
    for name,record in commands.items():
        require(read(base/(name+'.command.json'))==record,'raw command binding')
        require(number(record.get('elapsed_seconds')) and number(record.get('deadline_seconds')) and record['deadline_seconds']>0,'phase timing types')
        require(type(record.get('timed_out')) is bool and (type(record.get('exit_status')) is int or record.get('exit_status') is None),'phase result types')
        require(record.get('cleanup_status') in ['tracked-processes-stopped','uncertain'],'cleanup status')
        if name in expected:
            require(record['argv']==expected[name],'extract/resolve argv')
            require(record['deadline_seconds']==(150 if name=='extract' else 30),'phase deadline')
        else:
            require(record['deadline_seconds']<=60-elapsed+0.01,'shared analysis deadline')
            if name.endswith('-decode'):
                n=name[:-7];argv=[cli,'bqrs','decode',str(original/(n+'.bqrs')),'--format=json','--output='+str(original/(n+'.json'))]
            else:
                query=queryroot/((selected+'-'+name+'.ql') if selected not in ['native','opaque'] else name+'.ql')
                argv=[cli,'query','run',str(query),'--database='+str(db),'--output='+str(original/(name+'.bqrs')),'--additional-packs='+packs,'--threads=2','--ram=2048','--timeout='+str(max(1,int(record['deadline_seconds'])))]
            require(record['argv']==argv,'query/decode argv')
            elapsed+=record['elapsed_seconds']
        if name!=present[-1] or status=='completed':
            require(record['exit_status']==0 and not record['timed_out'] and record['cleanup_status']=='tracked-processes-stopped','preceding phase completion')
            require(record['elapsed_seconds']<=record['deadline_seconds'],'successful phase overrun')
    if any(n not in expected for n in commands):
        total=raw.get('analysis_elapsed_seconds');require(number(total) and total+0.01>=elapsed,'analysis elapsed binding')
        if status=='completed':require(total<=60 and elapsed<=60,'shared analysis overrun')
    if status=='attempted':
        kind=raw.get('failure_kind');last=commands[present[-1]]
        require(kind in ['timeout','cleanup','command','validation'],'typed failure')
        require(raw['outcome']==('inconclusive' if kind=='timeout' else 'runner-error'),'failure outcome')
        if kind=='cleanup':require(last['cleanup_status']=='uncertain','cleanup failure evidence')
        elif kind=='command':require(type(last['exit_status']) is int and last['exit_status']!=0,'command failure evidence')
        elif kind=='timeout':require(last['timed_out'] or raw.get('analysis_elapsed_seconds',0)>=60,'timeout evidence')
        else:require(bool(raw['diagnostics']),'validation failure diagnostic')
        return
    metadata=(base/'database/codeql-database.yml').read_text()
    require(len(re.findall(r'^finalised: true$',metadata,re.MULTILINE))==1 and not re.search(r'^inProgress:',metadata,re.MULTILINE),'database finalization')
    resolved=read(base/'resolve-database.stdout')
    require(resolved.get('languages')==['swift'] and resolved.get('datasetFolder')==str(db/'db-swift'),'resolved database identity')
    require(inspect_logs(base/'database/log/swift/extractor')['ready_for_observation'],'extraction log integrity')
    for n in names:require((base/(n+'.bqrs')).is_file() and (base/(n+'.bqrs')).stat().st_size>0,'missing BQRS')
    archive=base/'database/src.zip';require(archive.is_file(),'missing source archive')
    with zipfile.ZipFile(archive) as z:
        for name in case['fixture_files']:
            matches=[n for n in z.namelist() if n.endswith('/source/'+name)]
            require(len(matches)==1 and z.read(matches[0])==(base/'source'/name).read_bytes(),'extracted source archive')
    rows={n:read(base/(n+'.json'))['#select']['tuples'] for n in names}
    require(rows==raw.get('rows'),'decoded row binding')
    outcome,diagnostics=observe(case,rows['roles'],rows['flow'],selected)
    if 'coverage' in rows:
        require(rows['scopes'] and all(isinstance(r,list) and len(r)==1 and type(r[0]) is int for r in rows['scopes']),'scope inventory')
        coverage=assess_coverage(rows['coverage'],[r[0] for r in rows['scopes']])
        require(raw['coverage_status']==coverage.status.value,'coverage status')
        if coverage.status is CoverageStatus.INCOMPLETE:outcome='inconclusive';diagnostics.extend(coverage.reasons)
    require(raw['outcome']==outcome and raw['diagnostics']==diagnostics,'derived observation binding')


def verify(root,directory):
    plan=read(root/'adapters/codeql/swift-v3/runner-plan.json')
    for name,digest in plan['files'].items():require(sha(root/name)==digest,'runner configuration binding')
    launch=read(directory/'run-plan.json');run=read(directory/'run.json');report=assemble(root,run)
    require(launch['runner_plan_sha256']==sha(root/'adapters/codeql/swift-v3/runner-plan.json'),'launch plan binding')
    for key in ['scope','population_sha256','fixture_revision','contract_sha256','phases']:require(launch[key]==run[key],'launch envelope binding')
    pop,_,_,_,_=inputs(root);entries={e['id']:e for e in pop['cases']}
    for row in run['results']:
        rawpath=root/row['raw_output'];raw=read(rawpath);base=rawpath.parent
        require(sha(base/'artifacts.json')==raw['artifacts_sha256'],'artifact manifest binding')
        artifacts=read(base/'artifacts.json');actual={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()}-{'artifacts.json','observation.json'}
        require(actual==set(artifacts),'complete artifact closure')
        for name,digest in artifacts.items():
            p=Path(name);require(not p.is_absolute() and '..' not in p.parts and not (base/p).is_symlink(),'artifact path')
            require(sha(base/p)==digest,'artifact digest')
        entry=entries[row['case_id']];case=read(root/entry['path'])
        if raw['execution_status']!='not-attempted':
            for name in case['fixture_files']:require((base/'source'/name).read_bytes()==(root/entry['path']).parent.joinpath(name).read_bytes(),'canonical source bytes')
        verify_case(root,base,case,raw,launch['paths'])
    return report
