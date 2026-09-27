#!/usr/bin/env python3
"""Replay the portable source/command/query slice; does not verify omitted DB bytes."""
from pathlib import Path
from swift_v3_reports import ROOT,read,sha,require,inputs
from swift_v3_verify import verify_case


def check(root=ROOT):
    directory=root/'evidence/swift-v3-lane-smoke-01'
    manifest=read(directory/'export-manifest.json')
    require(manifest['scope']=='portable-command-source-query-replay-not-full-database-replay','export scope')
    actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'export-manifest.json'}
    require(actual==set(manifest['files']),'export closure')
    for name,digest in manifest['files'].items():
        path=Path(name)
        require(not path.is_absolute() and '..' not in path.parts and not (directory/path).is_symlink(),'export path')
        require(sha(directory/path)==digest,'export digest')
    run=read(directory/'run.json');launch=read(directory/'run-plan.json')
    population,contract,cases,ph,ch=inputs(root)
    selection=read(root/'adapters/codeql/swift-v3/smoke-selection.json')['case_ids']
    require(run['scope']=='swift-v3-contract-bound-smoke' and run['selected_case_ids']==selection and [r['case_id'] for r in run['results']]==selection,'smoke scope/membership')
    require(run['population_sha256']==ph and run['contract_sha256']==ch and run['fixture_revision']==population['fixture_revision'] and run['phases']==contract['phases'],'execution binding')
    for key in ['scope','population','population_sha256','contract_id','contract_sha256','fixture_revision','phases','selected_case_ids']:
        require(run[key]==launch[key],'launch binding')
    require(launch['runner_plan_sha256']==sha(directory/'preregistered-runner-plan.json'),'historical plan binding')
    expected=[]
    entries={e['id']:e for e in population['cases']}
    for row in run['results']:
        base=directory/row['case_id'];raw=read(base/'observation.json')
        require(sha(base/'observation.json')==row['raw_sha256'],'raw digest')
        require(raw['case_id']==row['case_id'] and raw['outcome']==row['outcome'],'raw identity')
        for key in ['scope','population_sha256','contract_sha256','fixture_revision','phases','selected_case_ids']:
            require(raw[key]==run[key],'raw execution binding')
        require(sha(base/'artifacts.json')==raw['artifacts_sha256'],'full closure manifest digest')
        full=read(base/'artifacts.json')
        for path in base.rglob('*'):
            if path.is_file() and path.name not in ['observation.json','artifacts.json']:
                require(sha(path)==full[str(path.relative_to(base))],'export vs full closure binding')
        case=cases[row['case_id']]
        for name in case['fixture_files']:
            require((base/'source'/name).read_bytes()==(root/entries[row['case_id']]['path']).parent.joinpath(name).read_bytes(),'canonical source')
        verify_case(root,base,case,raw,launch['paths'])
        expected.append({'case_id':row['case_id'],'raw_outcome':raw['outcome'],'outcome':'runner-error' if raw['outcome']=='runner-error' else 'inconclusive','diagnostics':raw['diagnostics']+['AggregateResourceQualificationUnavailable']})
    report=read(directory/'smoke-observations.json')
    require(report=={'scope':'verified-five-case-smoke-not-full-report','scored_activation':False,'selected_case_ids':selection,'results':expected},'smoke observation binding')
    return len(expected)

if __name__=='__main__':
    print('Verified',check(),'portable source/command/query slices; omitted database/cache bytes require local full replay; resource qualification unavailable')
