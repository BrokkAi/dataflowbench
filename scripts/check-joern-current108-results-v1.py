#!/usr/bin/env python3
"""Replay the current108 diagnostic export without launching an analyzer."""
from collections import Counter
from pathlib import Path
from swift_normal_reports_v1 import ROOT,read,require,bound_file
from joern_normal_reports_v1 import export

PLAN='adapters/joern/swift-normal-v1/plan-2026-09-28-04/plan.json'
RUN='reports/raw/joern-normal-v1/current108-2026-09-28-01'


def verify(root=ROOT):
    directory=root/RUN
    require(not (directory/'stop.json').exists(),'interrupted run cannot be full108')
    run=read(directory/'run.json');bundle=export(root,PLAN,run)
    require(read(directory/'normal/audit.json')==bundle['audit'],'normal audit drift')
    reports=list(bundle['reports'].values())
    require(len(list((directory/'normal').glob('report-*.json')))==len(reports),'normal report membership')
    for index,report in enumerate(reports):
        require(read(directory/'normal'/f'report-{index}.json')==report,'normal report drift')
    raw=[read(bound_file(root,row['raw'])) for row in run['results']]
    require(len(raw)==108 and sum(r['executed'] is True for r in raw)==96,'exact actual attempt membership')
    require(sum(r['raw_outcome']=='unsupported' and r['executed'] is False for r in raw)==12,'exact native capability decision membership')
    require(all(r.get('capability',{}).get('model_mode')=='off' for r in raw if r['executed']),'diagnostic models-off only')
    outcomes=Counter(row['outcome'] for report in reports for row in report['results'])
    require(outcomes.get('reached',0)==outcomes.get('not-reached',0)==0,'unqualified run cannot promote observations')
    require(bundle['audit']['scored_activation'] is False,'score activation forbidden')
    return {'rows':108,'executed':96,'capability_decisions':12,'raw_outcomes':dict(Counter(r['raw_outcome'] for r in raw)),'normalized_outcomes':dict(outcomes),'scored_activation':False}


if __name__=='__main__':print(verify())
