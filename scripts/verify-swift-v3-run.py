#!/usr/bin/env python3
"""Verify source/command/artifact closure of an actual v3 run before report assembly."""
import argparse,json
from pathlib import Path
from swift_v3_reports import ROOT,read,sha,require,assemble,inputs


def verify(root,directory):
    run=read(directory/'run.json');report=assemble(root,run)
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
            require(all(p['exit_status']==0 and p['timed_out'] is False for p in raw['commands'].values()),'completed phases')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);args=p.parse_args();result=verify(ROOT,args.directory)
    print('Verified',len(result['results']),'raw-bound v3 rows; aggregate qualification unavailable')
