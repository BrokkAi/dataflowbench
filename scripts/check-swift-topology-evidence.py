#!/usr/bin/env python3
"""Replay bounded topology evidence without inferring execution order from labels."""
import hashlib,json,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-top-level-topology-v1'


def require(value, message):
    if not value:raise ValueError(message)


def classify_topology(rows):
    for row in rows:
        require(isinstance(row,list) and len(row)==4 and all(isinstance(x,str) for x in row[:3]) and type(row[3]) is int,'topology schema')
    require(len({tuple(row) for row in rows})==len(rows),'duplicate topology row')
    tops={r[1] for r in rows if r[0]=='top-body'}
    def counts(relation):
        result={}
        for row in rows:
            if row[0]!=relation:continue
            require(row[3]>=0,'negative structural count')
            require(row[1] not in result,'conflicting structural count records')
            result[row[1]]=row[3]
        return result
    parents=counts('top-parent-count')
    members=counts('top-membership-count')
    require(tops and tops==set(parents)==set(members),'complete structural count inventory')
    if all(parents[t]==0 and members[t]==0 for t in tops):
        return {'status':'MissingTopLevelSequence' if len(tops)>1 else 'SingleUnparentedTopLevelBody','top_level_bodies':len(tops),'registry_outcome_changed':False}
    return {'status':'StructuralRelationshipsRequireSemanticReview','top_level_bodies':len(tops),'registry_outcome_changed':False}


def main():
    record=json.loads((BASE/'record.json').read_text());archive=BASE/'portable-evidence.tar.gz'
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==record['archive_sha256'],'archive digest')
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers();names=[m.name for m in members]
        require(len(set(names))==len(names) and set(names)==set(record['files']),'archive closure')
        content={}
        for member in members:
            require(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,'archive path/type')
            data=tar.extractfile(member).read();require(hashlib.sha256(data).hexdigest()==record['files'][member.name],'member digest');content[member.name]=data
    read=lambda name:json.loads(content[name])
    for attempt in ['attempt-01','attempt-02','attempt-03']:
        launch=read(attempt+'/launch.json');registration=read(attempt+'/registration.json')
        require(hashlib.sha256(content[attempt+'/registration.json']).hexdigest()==launch['registration_sha256'],'preregistration binding')
        for name in ['topology.ql','qlpack.yml']:
            require(hashlib.sha256(content[attempt+'/'+name]).hexdigest()==registration['files']['adapters/codeql/swift-top-level-topology-v1/'+name],'query binding')
        results=read(attempt+'/results.json');require([r['id'] for r in results]==registration['case_ids'],'exact selection')
        require(all(x['delta']['status']=='CompleteArtifactClosure' for x in read(attempt+'/closure-audit.json')['observations']),'observed closure drift')
        for r in results:
            prefix=attempt+'/'+r['id'];require(r==read(prefix+'/result.json'),'case binding')
            closure=read(prefix+'/closure-after.json');inventory={x['path']:x for x in closure['entries']}
            for name,data in content.items():
                if name.startswith(prefix+'/artifacts/'):
                    relative=name[len(prefix+'/artifacts/'):];require(inventory[relative]['sha256']==hashlib.sha256(data).hexdigest(),'artifact subset binding')
            if attempt=='attempt-01':continue
            require(r['status']=='completed' and r['analysis_elapsed_seconds']<=75,'bounded completion')
            require(r['rows']==read(prefix+'/artifacts/topology.json')['#select']['tuples'],'decoded rows')
            query=read(prefix+'/artifacts/query.command.json');decode=read(prefix+'/artifacts/decode.command.json')
            paths=launch['paths'];artifactroot=Path(paths['output'])/r['id']/'artifacts'
            expected=[paths['codeql'],'query','run',str(Path(paths['output']).parents[3]/'adapters/codeql/swift-top-level-topology-v1/topology.ql'),'--database='+str(artifactroot/'database'),'--output='+str(artifactroot/'topology.bqrs'),'--additional-packs='+paths['packs'],'--threads=2','--ram=2048','--timeout=75']
            require(query['argv']==expected,'query command binding')
            require(decode['argv']==[paths['codeql'],'bqrs','decode',str(artifactroot/'topology.bqrs'),'--format=json','--output='+str(artifactroot/'topology.json')],'decode binding')
            for command in [query,decode]:require(command['exit_status']==0 and not command['timed_out'] and command['elapsed_seconds']<=command['deadline_seconds'],'native command completion')
            require(query['elapsed_seconds']+decode['elapsed_seconds']<=r['analysis_elapsed_seconds'],'shared budget')
            if attempt=='attempt-03':
                diagnosis=classify_topology(r['rows']);expected_count=1 if r['id'].endswith('-direct-positive') else 4
                require(diagnosis['top_level_bodies']==expected_count,'body count')
                require(diagnosis['status']==('SingleUnparentedTopLevelBody' if expected_count==1 else 'MissingTopLevelSequence'),'diagnosis')
                print(r['id'],diagnosis)
        if attempt=='attempt-01':
            require([r['status'] for r in results]==['attempted','not-attempted','not-attempted'],'failed compile preserved')
            require(results[0]['failure']['message']=='CommandFailed:query','compile rejection')
    require(not record['registry_outcome_changed'],'no registry reclassification')


if __name__=='__main__':main()
