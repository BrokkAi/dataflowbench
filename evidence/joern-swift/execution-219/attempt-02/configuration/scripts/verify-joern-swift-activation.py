#!/usr/bin/env python3
"""Verify independent native controls, model load bearing and resolved Swift partitions."""
import json
from pathlib import Path
from joern_swift import ROOT, normalize, sha


def verify(root=ROOT):
    certificate=json.loads((root/'adapters/joern/swift/activation.json').read_text())
    if certificate['status']!='active':raise ValueError('Swift activation inactive')
    for group in ['configuration_sha256','evidence_sha256']:
        if not certificate[group]:raise ValueError('empty activation hash set')
        for name,expected in certificate[group].items():
            if sha(root/name)!=expected:raise ValueError('activation bytes changed: '+name)
    if not certificate['assets'] or not certificate['environment_commands']:raise ValueError('missing runtime pin')
    for control in certificate['controls']:
        directory=root/control['path']
        graph=json.loads((directory/'graph.json').read_text());config=json.loads((directory/'config.json').read_text())
        command=json.loads((directory/'query/command.json').read_text())
        frontend=json.loads((directory.parent/'frontend/command.json').read_text())
        compilation=json.loads((directory.parent/'typecheck/command.json').read_text())
        if any(c['exit_status']!=0 or c['timed_out'] for c in [command,frontend,compilation]):
            raise ValueError('control invocation failed: '+control['path'])
        outcome,diagnostics=normalize(graph,config)
        if outcome!=control['expected'] or diagnostics:
            raise ValueError('control activation mismatch: '+control['path']+' '+str((outcome,diagnostics)))
    partition=json.loads((root/'adapters/joern/swift/partition.json').read_text())
    if partition['status']!='resolved':raise ValueError('unresolved Swift partition')
    actual={}
    for path in (root/'cases/taint/swift').glob('*/case.json'):
        case=json.loads(path.read_text());identity=case['template_id']
        cell=partition['templates'].get(identity)
        if not cell or cell['tier']!=case['score_tier'] or cell['profile']!=case['model_profile'] or cell['decision'] not in ['execute','unsupported']:
            raise ValueError('partition missing/inconsistent: '+identity)
        if cell['decision']=='unsupported' and (case['score_tier']!='modeling' or not cell.get('reason')):
            raise ValueError('unjustified Swift unsupported partition: '+identity)
        actual[identity]=actual.get(identity,0)+1
    if set(actual)!=set(partition['templates']) or any(n!=2 for n in actual.values()):
        raise ValueError('Swift partition identity/polarity population mismatch')
    if len(actual)!=45:raise ValueError('Swift template inventory changed')
    return {'activation':'active','controls':len(certificate['controls']),'templates':len(actual),
            'execute_assertions':sum(actual[k] for k,v in partition['templates'].items() if v['decision']=='execute'),
            'unsupported_assertions':sum(actual[k] for k,v in partition['templates'].items() if v['decision']=='unsupported')}


if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
