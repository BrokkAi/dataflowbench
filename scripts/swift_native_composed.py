"""Collect native observations without consulting expected fixture polarity."""
import json
from pathlib import Path
from swift_opaque_v3_evidence import sha, read, require, verify_closure
from swift_integration_v3 import normalize
from swift_extraction_integrity import inspect_logs
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'adapter-composed-v1'
PLAN = 'adapters/codeql/swift-native-composed-v1/plan.json'


def collect(case, roles, flows, coverage=None, scopes=None):
    """Valid unexpected flows are observations, not qualification exceptions."""
    for row in roles:
        require(isinstance(row,list) and len(row)==4 and type(row[0]) is int and row[0]>0 and
                type(row[1]) is int and row[1]>0 and row[2]==PROFILE and row[3] in ['environment','argv','sink'], 'malformed role row')
    for row in flows:
        require(isinstance(row,list) and len(row)==4 and all(type(n) is int and n>0 for n in row[:3]) and row[3]==PROFILE, 'malformed flow row')
    sources={a['line_hint'] for a in case['source_anchors']}
    sinks={a['line_hint'] for a in case['sink_anchors']}
    endpoints=(sources <= {r[0] for r in roles if r[3] in ['environment','argv']} and
               sinks <= {r[0] for r in roles if r[3]=='sink'})
    reached=any(r[0] in sources and r[1] in sinks for r in flows)
    return {'case_id':case['id'], 'outcome':'reached' if reached else 'not-reached',
            'endpoints_verified':endpoints, 'roles':roles, 'findings':flows,
            'coverage':coverage, 'expected_scopes':scopes, 'adapter_profile':PROFILE}


def replay(root, attempt):
    plan=read(root/PLAN)
    for field in ['inputs','queries','runner_files']:
        for name,digest in plan[field].items():require(sha(root/name)==digest,'preregistered input: '+name)
    verify_closure(attempt)
    run=read(attempt/'run.json')
    require(run['plan_sha256']==sha(root/PLAN) and run['scored_activation'] is False,'plan/scope binding')
    require(set(run['cases'])==set(plan['cases']),'complete native selection')
    results=[]
    for case_id,selection in plan['cases'].items():
        case=read(root/selection['case_path']);directory=attempt/case_id
        record=run['cases'][case_id]
        if record['status']!='observed':
            results.append(normalize(case,{'case_id':case_id,'outcome':'runner-error','record':record}))
            continue
        verify_closure(directory)
        require(sha(directory/'source.zip')==selection['source_archive_sha256'],'source archive identity')
        with zipfile.ZipFile(directory/'source.zip') as z:
            names=[n for n in z.namelist() if n.endswith('/source/main.swift')]
            require(len(names)==1 and z.read(names[0])==(root/selection['case_path']).parent.joinpath('main.swift').read_bytes(),'canonical source bytes')
        prior=root/selection['witness']
        witness=read(prior)
        require(not witness.get('probe_error') and not witness.get('cleanup_error') and
                inspect_logs(prior.parent/'log/swift/extractor')['ready_for_observation'],'historical extraction integrity')
        require(witness['compiler_sha256']==plan['compiler_sha256'] and witness['extractor_sha256']==plan['extractor_sha256'],'extraction runtime pins')
        phases=[]
        query_names=['roles','flow']+(['coverage','scopes'] if case['template_id']=='dfb-template-native-persistence' else [])
        for name in query_names:
            phase=read(directory/(name+'.command.json'));decode=read(directory/(name+'-decode.command.json'))
            expected=[run['cli'],'query','run',str(Path(run['output'])/'queries'/(name+'.ql')),
                      '--database='+selection['database'],'--output='+str(Path(run['output'])/case_id/(name+'.bqrs')),
                      '--additional-packs='+run['packs'],'--threads=2','--ram=2048','--timeout=60']
            require(phase['argv']==expected and phase['deadline_seconds']==60,'query provenance')
            require(decode['argv']==[run['cli'],'bqrs','decode',str(Path(run['output'])/case_id/(name+'.bqrs')),
                    '--format=json','--output='+str(Path(run['output'])/case_id/(name+'.json'))],'decode provenance')
            for p in [phase,decode]:
                require(p['exit_status']==0 and p['timed_out'] is False and p['cleanup_status']=='tracked-processes-stopped','phase completion')
                phases.append(p)
        rows={n:read(directory/(n+'.json'))['#select']['tuples'] for n in query_names}
        scopes=[r[0] for r in rows.get('scopes',[]) if isinstance(r,list) and len(r)==1 and type(r[0]) is int]
        observation=collect(case,rows['roles'],rows['flow'],rows.get('coverage'),scopes)
        observation.update(extraction_complete=True,phases=phases,execution_budget={'wall_clock_seconds':60,'peak_memory_mb':2048},
                           raw_evidence=str(directory.relative_to(root)))
        result=normalize(case,observation);result['adapter_profile']=PROFILE;results.append(result)
    for name,digest in plan['queries'].items():require(sha(attempt/'queries'/Path(name).name)==digest,'executed query bytes')
    return {'scope':'native-composed-retained-database-diagnostic','adapter_profile':PROFILE,
            'scored_activation':False,'fresh_extraction':False,'results':results}
