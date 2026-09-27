#!/usr/bin/env python3
"""Verify source/command/artifact closure of an actual v3 run before report assembly."""
import argparse,json,zipfile,shlex
from pathlib import Path
from swift_v3_reports import ROOT,read,sha,require,assemble,inputs
from swift_v3_runner import observe,lane
from swift_persistence_coverage import assess_coverage,CoverageStatus


def verify(root,directory):
    plan=read(root/'adapters/codeql/swift-v3/runner-plan.json')
    for name,digest in plan['files'].items():require(sha(root/name)==digest,'runner configuration binding')
    launch=read(directory/'run-plan.json')
    require(launch['runner_plan_sha256']==sha(root/'adapters/codeql/swift-v3/runner-plan.json'),'launch plan binding')
    run=read(directory/'run.json');report=assemble(root,run)
    for key in ['scope','population_sha256','fixture_revision','contract_sha256','phases']:
        require(launch[key]==run[key],'launch envelope binding')
    pop,_,_,_,_=inputs(root);entries={e['id']:e for e in pop['cases']}
    for row in run['results']:
        rawpath=root/row['raw_output'];raw=read(rawpath);base=rawpath.parent
        require(sha(base/'artifacts.json')==raw['artifacts_sha256'],'artifact manifest binding')
        artifacts=read(base/'artifacts.json')
        actual={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()}-{'artifacts.json','observation.json'}
        require(actual==set(artifacts),'complete artifact closure')
        for name,digest in artifacts.items():
            path=Path(name);require(not path.is_absolute() and '..' not in path.parts,'artifact path')
            require(sha(base/path)==digest,'artifact digest')
        if raw['execution_status']=='not-attempted':
            require(raw['outcome']=='inconclusive' and not raw['commands'],'not-attempted state')
            continue
        entry=entries[row['case_id']];case=read(root/entry['path'])
        for name in case['fixture_files']:
            require((base/'source'/name).read_bytes()==(root/entry['path']).parent.joinpath(name).read_bytes(),'actual extracted source binding')
        for name,command in raw['commands'].items():
            require(read(base/(name+'.command.json'))==command,'raw command binding')
        if raw['execution_status']=='completed':
            archive=base/'database/src.zip'
            with zipfile.ZipFile(archive) as z:
                for name in case['fixture_files']:
                    matches=[n for n in z.namelist() if n.endswith('/source/'+name)]
                    require(len(matches)==1 and z.read(matches[0])==(base/'source'/name).read_bytes(),'extracted archive binding')
            command=raw['commands']['extract']['argv']
            require(command[1:3]==['database','create'] and '--ram=2048' in command,'extraction command identity')
            compile_commands=[v.split('=',1)[1] for v in command if v.startswith('--command=')]
            require(len(compile_commands)==1,'compiler command identity')
            compile_argv=shlex.split(compile_commands[0])
            for name in case['fixture_files']:
                require(any(v.endswith('/source/'+name) for v in compile_argv),'compiler source identity')
            selected_lane=lane(case);names=['roles','flow']+(['coverage','scopes'] if case['template_id']=='dfb-template-native-persistence' else [])
            rows={name:read(base/(name+'.json'))['#select']['tuples'] for name in names}
            require(rows==raw['rows'],'decoded row binding')
            outcome,diagnostics=observe(case,rows['roles'],rows['flow'],selected_lane)
            if 'coverage' in rows:
                coverage=assess_coverage(rows['coverage'],[r[0] for r in rows['scopes']])
                if coverage.status is CoverageStatus.INCOMPLETE:outcome='inconclusive';diagnostics.extend(coverage.reasons)
            require(raw['outcome']==outcome and raw['diagnostics']==diagnostics,'derived observation binding')
            require(all(p['exit_status']==0 and p['timed_out'] is False for p in raw['commands'].values()),'completed phases')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);args=p.parse_args();result=verify(ROOT,args.directory)
    print('Verified',len(result['results']),'raw-bound v3 rows; aggregate qualification unavailable')
