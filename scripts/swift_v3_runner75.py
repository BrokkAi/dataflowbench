"""Prospective full-population runner helpers; observations never consult polarity."""
from pathlib import Path
from swift_v3_reports75 import inputs, read, sha, require


def lane(case):
    if case['model_profile']=='tool-native':return 'native'
    if case['template_id'] in ['dfb-template-model-opaque-propagator','dfb-template-model-propagator-position']:return 'opaque'
    if case['score_tier']=='modeling':return 'modeling'
    if case['score_tier']=='calibration':return 'calibration'
    return 'kernel'


def observe(case, roles, flows, selected_lane):
    if selected_lane in ['native','opaque']:
        allowed={'adapter-composed-v1'} if selected_lane=='native' else {'adapter-controlled-model-on','adapter-controlled-model-off'}
        require(all(isinstance(r,list) and len(r)==4 and type(r[0]) is int and r[0]>0 and type(r[1]) is int and r[1]>0 and isinstance(r[2],str) and r[2] in allowed and r[3] in ['source','environment','argv','sink'] for r in roles),'malformed lane endpoint rows')
        require(all(isinstance(r,list) and len(r)==4 and all(type(n) is int and n>0 for n in r[:3]) and isinstance(r[3],str) and r[3] in allowed for r in flows),'malformed lane flow rows')
        profile='adapter-composed-v1' if selected_lane=='native' else 'adapter-controlled-model-on'
        roles=[['main.swift',r[0],r[1],'source' if r[3] in ['environment','argv'] else r[3]] for r in roles if len(r)==4 and r[2]==profile]
        flows=[['main.swift',r[0],'main.swift',r[1],r[2]] for r in flows if len(r)==4 and r[3]==profile]
    require(all(isinstance(r,list) and len(r)==4 and isinstance(r[0],str) and type(r[1]) is int and type(r[2]) is int and r[3] in ['source','sink'] for r in roles),'malformed endpoint rows')
    require(all(isinstance(r,list) and len(r)==5 and isinstance(r[0],str) and isinstance(r[2],str) and all(type(r[i]) is int for i in [1,3,4]) for r in flows),'malformed flow rows')
    sources={(a['file'],a['line_hint']) for a in case['source_anchors']};sinks={(a['file'],a['line_hint']) for a in case['sink_anchors']}
    observed_sources={(r[0],r[1]) for r in roles if r[3]=='source'};observed_sinks={(r[0],r[1]) for r in roles if r[3]=='sink'}
    if not sources<=observed_sources or not sinks<=observed_sinks:return 'runner-error',['MissingExactEndpoints']
    return ('reached' if any((r[0],r[1]) in sources and (r[2],r[3]) in sinks for r in flows) else 'not-reached'),[]


def configuration(root):
    pop,contract,cases,ph,ch=inputs(root)
    return pop,contract,cases,{'scope':'swift-v3-contract-bound-execution','population':pop['population'],
        'population_sha256':ph,'fixture_revision':pop['fixture_revision'],'contract_id':contract['contract_id'],
        'contract_sha256':ch,'phases':contract['phases']}


def enforce_deadline(record, deadline):
    if record['timed_out'] or record['elapsed_seconds'] > deadline:
        raise TimeoutError('BudgetExhausted')

def completed_analysis_elapsed(elapsed):
    if elapsed > 75:
        raise TimeoutError('BudgetExhausted:analysis')
    return elapsed
