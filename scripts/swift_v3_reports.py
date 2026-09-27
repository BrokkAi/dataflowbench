"""Strict v3 coverage report assembly; never relabel historical diagnostics."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
OUTCOMES={'reached','not-reached','inconclusive','unsupported','runner-error'}


def require(value,message):
    if not value:raise ValueError(message)


def inputs(root=ROOT):
    path=root/'populations/swift-synthetic-v3.json';population=read(path)
    contract_path=root/'adapters/codeql/swift-v3/execution-contract.json';contract=read(contract_path)
    require(contract['population']==population['population']=='swift-synthetic-v3','population identity')
    require(contract['population_sha256']==sha(path) and contract['fixture_revision']==population['fixture_revision'],'contract population binding')
    require(contract['phases']=={'extraction':{'wall_clock_seconds':150,'peak_memory_mb':2048},'analysis':{'wall_clock_seconds':60,'peak_memory_mb':2048}},'prospective phase budgets')
    require(contract['aggregate_resource_qualification']=='unavailable' and contract['scored_activation'] is False,'unqualified contract')
    cases={}
    for e in population['cases']:
        require(e['id'] not in cases,'duplicate population case')
        p=root/e['path'];require(sha(p)==e['sha256'],'case hash')
        case=read(p);require(case['id']==e['id'],'case identity')
        for f in e['fixture_digests']:require(sha(root/f['path'])==f['sha256'],'fixture hash')
        cases[e['id']]=case
    require(len(cases)==108,'full 108-case population')
    return population,contract,cases,sha(path),sha(contract_path)


def assemble(root,run):
    population,contract,cases,pop_hash,contract_hash=inputs(root)
    require(run.get('scope')=='swift-v3-contract-bound-execution','new execution scope required')
    require(run.get('population')==population['population'] and run.get('population_sha256')==pop_hash and
            run.get('fixture_revision')==population['fixture_revision'],'run population/revision binding')
    require(run.get('contract_id')==contract['contract_id'] and run.get('contract_sha256')==contract_hash,'run contract binding')
    require(run.get('phases')==contract['phases'],'run phase budgets')
    rows=run.get('results');require(isinstance(rows,list),'result list')
    ids=[r.get('case_id') for r in rows if isinstance(r,dict)]
    require(len(ids)==len(rows)==len(set(ids))==108 and set(ids)==set(cases),'exact result membership; missing foreign or duplicate')
    result=[]
    for row in rows:
        require(row.get('outcome') in OUTCOMES,'typed raw outcome')
        relative=Path(row.get('raw_output',''))
        require(relative.parts[:3]==('reports','raw','swift-v3') and '..' not in relative.parts,'new raw evidence path')
        require(not (root/relative).is_symlink() and sha(root/relative)==row.get('raw_sha256'),'raw evidence digest')
        raw=read(root/relative)
        for key,value in [('case_id',row['case_id']),('population_sha256',pop_hash),('fixture_revision',population['fixture_revision']),('contract_sha256',contract_hash),('scope','swift-v3-contract-bound-execution')]:
            require(raw.get(key)==value,'raw execution binding: '+key)
        require(raw.get('outcome')==row['outcome'],'raw outcome binding')
        diagnostics=raw.get('diagnostics');require(isinstance(diagnostics,list) and all(isinstance(d,str) for d in diagnostics),'typed diagnostics')
        # No available containment verifier: even claimed qualified input stays incomplete.
        outcome='runner-error' if row['outcome']=='runner-error' else 'inconclusive'
        result.append({'case_id':row['case_id'],'model_profile':cases[row['case_id']]['model_profile'],
                       'score_tier':cases[row['case_id']]['score_tier'],'raw_outcome':row['outcome'],'outcome':outcome,
                       'diagnostics':sorted(set(diagnostics+['AggregateResourceQualificationUnavailable'])),
                       'raw_output':str(relative),'raw_sha256':row['raw_sha256']})
    return {'schema':'swift-v3-coverage-report/v1','population':population['population'],'population_sha256':pop_hash,
            'fixture_revision':population['fixture_revision'],'contract_sha256':contract_hash,
            'scored_activation':False,'aggregate_resource_qualification':'unavailable','results':result}
