#!/usr/bin/env python3
"""Replay retained bounded Joern evidence; never activate a partition."""
from pathlib import Path
from joern_normal_runner_v1 import ROOT, BASE, PHASES, read, sha, bound_file, require
from joern_normal_controls_v1 import config_for, observe, assess_controls
from joern_normal_reports_v1 import validate_phases
from swift_normal_reports_v1 import load_population, normalized


def verify(root=ROOT):
    population,cases,digest=load_population(root)
    planpath=BASE+'/plan-2026-09-28-03/plan.json'
    controlpath=BASE+'/plan-2026-09-28-03/controls.json'
    plan=read(root/planpath);control=read(root/controlpath)
    run=read(root/'reports/raw/joern-normal-v1/controls-2026-09-28-02/run.json')
    require(run['plan_sha256']==sha(root/planpath) and run['controls_sha256']==sha(root/controlpath),'run registration drift')
    require(control['plan']['sha256']==sha(root/planpath) and plan['population_sha256']==digest,'population/plan drift')
    require(plan['partition_status']=='unresolved','evidence cannot activate partition')
    require(control['registered_at_unix_seconds']<run['started_at_unix_seconds']<=run['ended_at_unix_seconds'],'chronology')
    require(len(run['records'])==12 and {(r['control'],r['arm']) for r in run['records']}=={(l,a) for l in control['controls'] for a in ['off','on']},'matrix membership')
    witness=run['identity_witness'];version=read(bound_file(root,witness['command']))
    require(version['argv']==[plan['runtime']['joern']] and version['exit_status']==0 and version['timed_out'] is False and version['cleanup_status']=='tracked-processes-stopped','version witness failed')
    require('Version: 4.0.628' in bound_file(root,witness['stdout']).read_text() and witness['observed']==plan['identity'],'version identity mismatch')
    observations={}
    for row in run['records']:
        case_id=control['controls'][row['control']];require(case_id==row['case_id'],'case routing')
        rawpath=bound_file(root,row['raw']);raw=read(rawpath)
        require(raw['plan_sha256']==run['plan_sha256'] and raw['controls_sha256']==run['controls_sha256'] and raw['case_id']==case_id and raw['arm']==row['arm'],'raw identity')
        for reference in raw['native_outputs']:bound_file(root,reference)
        config=config_for(root,cases[case_id],row['arm'])
        require(read(rawpath.parent/'config.json')==config,'configuration drift')
        outcome,diagnostics=observe(read(rawpath.parent/'graph.json'),config)
        require((outcome,diagnostics)==(raw['raw_outcome'],raw['diagnostics']) and raw['state']==normalized(outcome),'observation drift')
        validate_phases(root,raw,PHASES,raw['state'],raw['diagnostics'])
        observations.setdefault(row['control'],{})[row['arm']]=outcome
    require(observations==run['observations'] and assess_controls(observations)==run['assessment'],'assessment drift')
    require(run['assessment']['status']=='incomplete' and not run['assessment']['partition_registered'],'unexpected activation')
    return {'arms':12,'direct_arms_passed':4,'opaque_arms_incomplete':8,'activation':False,'partition':'unresolved'}


if __name__=='__main__':print(verify())
