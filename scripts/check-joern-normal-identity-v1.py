#!/usr/bin/env python3
"""Replay the one retained native identity diagnosis, without invoking Joern."""
from pathlib import Path
from swift_normal_reports_v1 import ROOT,read,sha,bound_file,require

BASE='adapters/joern/swift-normal-v1'
EVIDENCE='evidence/joern-normal-identity-2026-09-28-02'
PLAN=BASE+'/identity-diagnostic-2026-09-28-02/plan.json'


def validate_inventory(inventory,result):
    require(inventory['schema']=='joern-structural-inventory/v1','inventory schema')
    require(result['status']=='incomplete-native-endpoint-link' and result['query_evaluated'] is True,'diagnostic status')
    methods={m['id']:m for m in inventory['methods']}
    calls={c['node']['id']:c for c in inventory['calls']}
    owners={o['id']:o for o in inventory['type_declarations']}
    require(len(methods)==len(inventory['methods']) and len(calls)==len(inventory['calls']) and len(owners)==len(inventory['type_declarations']),'duplicate native identity')
    for label in ('source','sink'):
        endpoint=result[label];local=endpoint['internal_declaration'];call=endpoint['anchored_call'];actual=endpoint['actual_callee']
        require(methods.get(local['id'])==local and methods.get(actual['id'])==actual and calls.get(call['node']['id'])==call,'endpoint inventory drift')
        require(local['external'] is False and actual['external'] is True and local['id']!=actual['id'],'distinct native declaration/stub required')
        require(call['callee_ids']==[actual['id']],'native endpoint callee mismatch')
    require(set(result['wrappers'])=={'carry','block','select'},'wrapper membership')
    for name,wrapper in result['wrappers'].items():
        require(methods.get(wrapper['id'])==wrapper and wrapper['external'] is False,'wrapper inventory drift')
        owner=owners.get(wrapper['ast_parent']['id'])
        require(owner is not None and wrapper['id'] in owner['method_ids'],'wrapper native owner edge')
        parameters=wrapper['parameters'];indices=[0,1,2] if name=='select' else [0,1]
        require([p['index'] for p in parameters]==indices,'wrapper parameter indices')
        require(all(p['type']==(owner['full_name'] if p['index']==0 else 'Swift.String') for p in parameters) and wrapper['return']['type']=='Swift.String','wrapper native types')
    # Follow the sink argument's node ID to its actual CALL and native callee.
    arguments=result['sink']['anchored_call']['arguments']
    nested=[calls[a['node']['id']] for a in arguments if a['node']['id'] in calls]
    require(len(nested)==1 and nested[0]['callee_ids']==[result['wrappers']['carry']['id']],'carry argument native callee')


def verify(root=ROOT):
    plan=read(root/PLAN);directory=root/EVIDENCE
    result=read(directory/'result.json')
    for name,digest in result['files'].items():
        require(Path(name).name==name,'unsafe diagnostic output')
        require(sha(directory/name)==digest,'diagnostic evidence digest:'+name)
    for key in ('source_cpg','query','runtime_plan'):bound_file(root,plan[key])
    require(sha(directory/'input-cpg.bin')==plan['source_cpg']['sha256'],'diagnostic CPG binding')
    before=read(directory/'closure-before.json');after=read(directory/'closure-after.json')
    for closure in (before,after):
        require(closure['source_sha256']==closure['clone_sha256']==plan['source_cpg']['sha256'],'diagnostic CPG closure')
    require(after['original_unchanged'] is True and result['original_cpg_unchanged'] is True,'immutable original CPG')
    reservation=read(directory/'reservation.json')
    require(reservation['plan_sha256']==sha(root/PLAN) and plan['registered_at_unix_seconds']<reservation['registered_at_unix_seconds'],'diagnostic prospective registration')
    command=read(directory/'inventory.command.json');cwd=Path(command['cwd'])
    require(cwd.is_absolute() and cwd.parts[-2:]==Path(EVIDENCE).parts,'diagnostic cwd')
    execution_root=cwd.parents[1];runtime=read(bound_file(root,plan['runtime_plan']))['runtime']
    expected=[runtime['joern'],'--script',str(execution_root/plan['query']['path']),'--param','cpgPath='+str(cwd/'input-cpg.bin'),'--param','outputPath='+str(cwd/'inventory.json')]
    require(command['argv']==expected and command['measurement_wrapper']==[],'diagnostic command binding')
    require(command['exit_status']==0 and command['timed_out'] is False and command['cleanup_status']=='tracked-processes-stopped','diagnostic command failed')
    require(0<=command['elapsed_seconds']<=command['deadline_seconds']<=plan['query_seconds']==75,'diagnostic budget')
    validate_inventory(read(directory/'inventory.json'),result)
    capability=read(root/BASE/'capability-2026-09-28.json')
    require(capability['status']=='incomplete' and all(capability[k] is False for k in ['unsupported_decision','partition_registered','scored_activation']),'diagnosis cannot activate or infer unsupported')
    for reference in capability['evidence']:bound_file(root,reference)
    require({r['path'] for r in capability['evidence']}=={EVIDENCE+'/inventory.json',EVIDENCE+'/result.json'},'capability evidence membership')
    return {'native_endpoint_identity':'incomplete','inspected_cpgs':1,'unsupported':False,'activation':False}


if __name__=='__main__':print(verify())
