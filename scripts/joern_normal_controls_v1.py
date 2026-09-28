"""Prospective Joern controls: native identity first, activation only after replay."""
import importlib.util
from pathlib import Path
from joern_swift import MODULE, configuration, normalize
from swift_normal_reports_v1 import require

BASE = 'adapters/joern/swift-normal-v1'
OPAQUE = {'dfb-template-model-opaque-propagator', 'dfb-template-model-propagator-position'}
WRAPPERS = [
    {'method':MODULE+'.Opaque.carry:(Swift.String)->Swift.String','owner':MODULE+'.Opaque','parameter_indices':[0,1],'flows':[[1,-1]]},
    {'method':MODULE+'.Opaque.block:(Swift.String)->Swift.String','owner':MODULE+'.Opaque','parameter_indices':[0,1],'flows':[]},
    {'method':MODULE+'.Opaque.select:(Swift.String,Swift.String)->Swift.String','owner':MODULE+'.Opaque','parameter_indices':[0,1,2],'flows':[[2,-1]]},
]


def config_for(root, case, mode='on'):
    require(mode in ('off','on'), 'unknown model arm')
    template=case['template_id']
    require(case['model_profile']=='benchmark-controlled', 'Incomplete: native capability decision required')
    if template in OPAQUE:
        config=configuration([MODULE+'.dfb_source:()->Swift.String'],[MODULE+'.dfb_sink:(Swift.String)->()'],case['source_anchors'],case['sink_anchors'])
        selected='select' if template.endswith('position') else ('carry' if case['polarity']=='positive' else 'block')
        config['wrappers']=WRAPPERS
        config['selected_wrapper']=next(w['method'] for w in WRAPPERS if '.Opaque.'+selected+':' in w['method'])
        config['semantics']=[{'method':w['method'],'flows':w['flows']} for w in WRAPPERS] if mode=='on' else []
    else:
        spec=importlib.util.spec_from_file_location('joern_historical_configuration',root/'scripts/run-joern-swift-case.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        config=module.config_for(case)
        config.update(wrappers=[],selected_wrapper='')
        if mode=='off':config['semantics']=[]
    return config


def observe(graph, config):
    """Never promote matching names to native wrapper identity."""
    if isinstance(graph,dict) and graph.get('state')=='incomplete' and graph.get('identity_status')=='incomplete':
        return 'inconclusive',['Incomplete:NativeIdentity:'+str(graph.get('error','unspecified proof gap'))]
    if not isinstance(graph,dict) or graph.get('state')=='runner-error':
        return 'runner-error',['QueryRuntimeError:'+str(graph.get('error','missing graph state') if isinstance(graph,dict) else 'invalid graph object')]
    if graph.get('state')!='analyzed' or graph.get('query_completed') is not True:
        return 'runner-error',['QueryDidNotComplete']
    outcome,diagnostics=normalize(graph,config)
    if outcome=='runner-error':return 'inconclusive',['Incomplete:EndpointIdentity:'+d for d in diagnostics]
    try:
        methods={m['id']:m for m in graph['methods']}
        evidence=graph['wrapper_evidence']
        require(len(evidence)==len(config['wrappers']), 'wrapper evidence membership')
        for spec in config['wrappers']:
            matches=[m for m in methods.values() if not m['external'] and m['full_name']==spec['method']]
            require(len(matches)==1,'wrapper declaration missing or ambiguous')
            method=matches[0]
            proofs=[e for e in evidence if e['method_id']==method['id']]
            require(len(proofs)==1,'wrapper proof absent or duplicate')
            proof=proofs[0]
            require(proof['owner_id'] and proof['owner_full_name']==spec['owner'] and method['id'] in proof['owner_ast_method_ids'], 'wrapper owner edge mismatch')
            require(proof['return_types']==['Swift.String'],'wrapper return mismatch')
            require(sorted(p['index'] for p in method['parameters'])==spec['parameter_indices'],'wrapper positions mismatch')
            require(all(p.get('type')==(spec['owner'] if p['index']==0 else 'Swift.String') for p in method['parameters']),'wrapper parameter types mismatch')
            if spec['method']==config['selected_wrapper']:
                calls=[c for c in graph['calls'] if c['callee_ids']==[method['id']] and c['method_full_name']==method['full_name'] and any(c['node']['file']==a['file'] and c['node']['line']==a['line_hint'] for a in config['sink_anchors'])]
                require(len(calls)==1,'wrapper invocation missing or ambiguous')
                require(sorted(a['index'] for a in calls[0]['arguments'])==spec['parameter_indices'],'wrapper argument positions mismatch')
        return outcome,diagnostics
    except (KeyError,TypeError,ValueError) as error:
        return 'inconclusive',['Incomplete:WrapperIdentity:'+str(error)]


def assess_controls(observations):
    """A bounded diagnostic decision, never a current108 partition."""
    expected={
        'direct-positive':('reached','reached'), 'direct-negative':('not-reached','not-reached'),
        'dfb-taint-swift-model-opaque-propagator-positive':('not-reached','reached'),
        'dfb-taint-swift-model-opaque-propagator-negative':('reached','not-reached'),
        'dfb-taint-swift-model-propagator-position-positive':('not-reached','reached'),
        'dfb-taint-swift-model-propagator-position-negative':('not-reached','not-reached'),
    }
    require(set(observations)==set(expected),'exact six-control matrix required')
    failures=[]
    for key,pair in expected.items():
        require(set(observations[key])=={'off','on'},'both control arms required')
        for arm,wanted in zip(('off','on'),pair):
            value=observations[key][arm]
            if value!=wanted:failures.append({'control':key,'arm':arm,'required':wanted,'observed':value})
    return {'status':'bounded-controls-observed' if not failures else 'incomplete','failures':failures,'scored_activation':False,'partition_registered':False,'absence_completeness':'unproven'}
