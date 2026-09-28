#!/usr/bin/env python3
"""Replay compact diagnostic evidence; not a full database/containment verifier."""
import hashlib
import json
from pathlib import Path
from swift_endpoint_diagnostic import classify
from swift_artifact_closure import compare

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-endpoint-diagnostic-v1'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def require(value, reason):
    if not value: raise ValueError(reason)


def main():
    manifest=read(BASE/'manifest.json')
    require(manifest['scope']=='compact-diagnostic-replay-not-full-database-verification','scope')
    actual={str(p.relative_to(BASE)) for p in BASE.rglob('*') if p.is_file()}-{'manifest.json'}
    require(actual==set(manifest['files']),'compact closure')
    for name,digest in manifest['files'].items(): require(sha(BASE/name)==digest,'compact digest '+name)
    registration=read(BASE/'registration.json');launch=read(BASE/'launch.json')
    require(launch['registration_sha256']==sha(BASE/'registration.json'),'registration binding')
    for name,digest in registration['files'].items():require(sha(ROOT/name)==digest,'preregistered input '+name)
    controls=read(ROOT/'adapters/codeql/swift-endpoint-diagnostic-v1/plan.json')['controls']
    expected=registration['retained_case_ids']+[c['id'] for c in controls]
    results=read(BASE/'results.json')['results']
    require([r['id'] for r in results]==expected,'exact diagnostic selection')
    population={r['id']:r for r in read(ROOT/'populations/swift-synthetic-v3.json')['cases']}
    for result in results:
        base=BASE/result['id'];require(read(base/'result.json')==result,'result binding')
        require(result['execution_status']=='completed' and not result['scored_activation'],'completion/scoring')
        if result['id'] in population:
            case=read(ROOT/population[result['id']]['path'])
            anchors=[dict(file=a['file'],line=a['line_hint'],role=role) for role,key in [('source','source_anchors'),('sink','sink_anchors')] for a in case[key]]
        else:
            control=next(c for c in controls if c['id']==result['id']);anchors=control['anchors']
            require([r['status'] for r in result['endpoints']]==control['expected_statuses'],'control result')
        require(classify(read(base/'artifacts/diagnostics.json')['#select']['tuples'],anchors)==result['endpoints'],'classifier replay')
        first=read(base/'closure-before.json');after=read(base/'closure-after.json');final=read(base/'closure-final.json')
        require(compare(first,after)==result['closure'],'closure delta')
        require(compare(first,final)['status']=='CompleteArtifactClosure','late drift')
        inventory={r['path']:r for r in final['entries']}
        for p in (base/'artifacts').rglob('*'):
            if p.is_file():require(inventory[str(p.relative_to(base/'artifacts'))]['sha256']==sha(p),'retained subset artifact binding')
        records=[read(p) for p in (base/'artifacts').glob('*.command.json')]
        require({p.stem.split('.')[0] for p in (base/'artifacts').glob('*.command.json')}==({'query','decode'} if result['id'] in population else {'extract','query','decode'}),'command set')
        for r in records:
            require(r['exit_status']==0 and not r['timed_out'] and r['elapsed_seconds']<=r['deadline_seconds'] and r['cleanup_status']=='tracked-processes-stopped','command status')
            require(r['descendant_containment']=='unproven' and not r['discovery_complete'],'containment limits')
        require(result['analysis_elapsed_seconds']<=75,'analysis budget')
    audit=read(BASE/'closure-audit.json')
    require(all(r['status']=='CompleteArtifactClosure' for r in audit['cases']+audit['retained_originals']),'closure audit')
    require(not audit['stable_snapshots_prove_containment'],'containment assertion')
    print('Five structural diagnostics replayed; full databases and containment remain outside compact verification.')


if __name__=='__main__':main()
