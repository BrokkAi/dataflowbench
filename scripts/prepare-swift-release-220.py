#!/usr/bin/env python3
"""Build a non-executable release-preparation snapshot; never select opaque semantics."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-release-preparation-220/2026-09-23'
OPAQUE=['dfb-template-model-opaque-propagator','dfb-template-model-propagator-position']
SOURCE='c155aab98da74e4299d8e38404c1342d41783d4b'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def encoded(value):return json.dumps(value,indent=2,sort_keys=True)+'\n'


def build():
    revision=hashlib.sha256();cases=[]
    for path in sorted((ROOT/'cases').rglob('case.json'),key=lambda p:p.relative_to(ROOT).parts):
        relative=str(path.relative_to(ROOT));case=json.loads(path.read_text());revision.update(relative.encode());revision.update(path.read_bytes())
        fixtures=[]
        for name in case['fixture_files']:
            fixture=path.parent/name;revision.update(name.encode());revision.update(fixture.read_bytes());fixtures.append({'path':str(fixture.relative_to(ROOT)),'sha256':digest(fixture)})
        cases.append({'id':case['id'],'path':relative,'sha256':digest(path),'fixtures':fixtures,**{k:case[k] for k in ['template_id','language','track','score_tier','model_profile','polarity']}})
    assert len(cases)==1104
    assert not any(c['language']=='swift' and c['template_id'] in OPAQUE for c in cases)
    membership={'schema_version':1,'status':'observed-current-inputs-not-final-release-selection','source_revision':SOURCE,'case_count':len(cases),'fixture_revision':'sha256:'+revision.hexdigest(),'release':None,'opaque_decision':'pending-user-choice','cases':cases}
    by_id={c['id']:c for c in cases};rows=[];groups=defaultdict(list)
    old_plan={r['report']:r for r in read('reports/releases/v0.8.0/rerun-plan.json')['reports']}
    for path in sorted((ROOT/'reports').glob('*.json')):
        report=json.loads(path.read_text())
        if 'results' not in report:continue
        relative=str(path.relative_to(ROOT));ids=sorted(r['case_id'] for r in report['results'])
        assert len(ids)==len(set(ids)) and set(ids)<=set(by_id)
        groups[report['fixture_revision']].append(relative)
        partitions=Counter((by_id[i]['track'],by_id[i]['score_tier'],by_id[i]['model_profile']) for i in ids)
        historic=old_plan.get(relative,{})
        rows.append({'id':path.stem,'tool':report['tool'],'historical_report':relative,'historical_report_sha256':digest(path),'historical_fixture_revision':report['fixture_revision'],'case_ids':ids,'case_count':len(ids),'case_ids_sha256':hashlib.sha256((json.dumps(ids,separators=(',',':'))+'\n').encode()).hexdigest(),'partitions':[{'track':k[0],'tier':k[1],'profile':k[2],'count':v} for k,v in sorted(partitions.items())],'requires_fresh_run':True,'historical_command_template':historic.get('command_template'),'executable_argv':None,'proposed_output_template':'reports/releases/{approved_release}/attempts/{attempt_id}/'+path.stem,'output_root':None,'status':'blocked-final-population-pins-versioned-runner'})
    assert len(rows)==92
    blockers=[
      {'id':'opaque-scope','status':'pending-user-choice','detail':'Neither deferral nor faithful implementation is selected for the two opaque Swift templates. No automatic exclusion or epic closure.'},
      {'id':'final-population','status':'blocked','detail':'1104 cases are an observed snapshot, not accepted release membership. Final population/release version and exact common fixture revision require review after semantic choice.'},
      {'id':'pin-integration','status':'blocked','detail':'Complete dated all-adapter review, exact root/transitive locks, asset checksums, runtime witnesses, realistic positive/negative activation and compatibility must precede reruns.'},
      {'id':'common-revision-runner','status':'blocked','detail':'Existing default reports bind1000, Swiftv1 reports bind90, Swiftv2 additions bind104. Swift runners must gain separately versioned common-population support and new output paths; never relabel prior reports.'},
      {'id':'historical-output-isolation','status':'blocked','detail':'Current runner/report destinations overlap historical artifacts or refuse overwrite; define versioned new report/raw paths, configuration hash routing and freeze inputs before commands become executable.'},
      {'id':'review-bound-docs','status':'blocked','detail':'Adapter READMEs and docs/adapters.md are digest-bound by accepted R2 review inputs. This snapshot is a supplementary dated audit; successor declarations/review are required before runtime pin integration, not silent edits.'},
      {'id':'timing-resources','status':'blocked','detail':'Review serial host/time/storage reservation, quiet-host gate, repeats/warm/overhead and retained failed attempts before execution.'},
    ]
    plan={'schema_version':1,'plan_id':'swift-release-preparation-220/2026-09-23-v1','status':'blocked','executable':False,'release':None,'source_revision':SOURCE,'population_approved':False,'provisional_population_manifest':'evidence/swift-release-preparation-220/2026-09-23/current-population.json','observed_fixture_revision':membership['fixture_revision'],'final_fixture_revision':None,'input_commits':{'observed_main':SOURCE,'qualified_runner':None},'scope_decision':{'status':'pending-user-choice','opaque_templates':OPAQUE,'deferral_selected':False,'exclusion_selected':False},'blockers':blockers,'reports':rows,'historical_revision_groups':dict(groups),'provisional_report_count':92,'provisional_result_rows':sum(r['case_count'] for r in rows),'schedule':'serialize analyzer processes; no full run in this preparation','additional_stages':['pin/runtime/activation controls','cold case runs and native decisions','warm observations with declared denominators','invocation-overhead repeats and quiet-host evidence','bounded failure triage and retained retries'],'gate_order':['resolve opaque semantics and approve full population','review dated pin bumps/holds and commit qualified versioned adapters','review exact common-revision memberships/commands/output isolation and resources','fresh serial runs including controls/cold/warm/overhead; retain every attempt','validate and merge evidence PR with terminal green CI','from clean merged main create separate freeze and generated-results PR','validate freeze/results/release notes/exact tag tree','explicit authorized tag/publication and independently verify deployment'],'historical_publication':{'release':'v0.8.0','tag_commit':'9c0916338abc42ab13565b5d9e6f310d46134afc','github_release_object':'404 at dated audit; tag is not a GitHub release object','mutation':'none'}}
    old=read('evidence/swift-coverage-220/coverage.json');v2=read('populations/swift-synthetic-v2.json');new_ids={c['id'] for c in v2['cases']}-{c['id'] for c in read('populations/swift-synthetic-v1.json')['cases']}
    families=[]
    for old_family in old['families']:
        family=dict(old_family);template=family['template_id'];additions=[c for c in cases if c['language']=='swift' and c['id'] in new_ids and c['template_id']==template]
        if additions:
            family['scope_resolution']='A38/A39-inputs-A40-typed-coverage-complete';family['historical_decision']=family.pop('decision');family['decision']='implemented-under-A38/A39-with-A40-typed-coverage';family['cases']=[]
            for case in additions:
                observations={}
                for tool in ['codeql','joern']:
                    suffix='native' if case['model_profile']=='tool-native' else 'result';rp=f'reports/{tool}-swift-v2-{suffix}.json';report=read(rp);row=next(r for r in report['results'] if r['case_id']==case['id'])
                    observations[tool]={'outcome':row['outcome'],'report':rp,'report_sha256':digest(ROOT/rp),'raw_output':row['raw_output'],'raw_sha256':digest(ROOT/row['raw_output'])}
                family['cases'].append({'id':case['id'],'path':case['path'],'results':observations})
        elif template in OPAQUE:family['scope_resolution']='pending-user-choice'
        families.append(family)
    coverage={'schema_version':2,'status':'historical-v1-plus-A40-coverage-not-common-revision-results','epic_complete':False,'historical_audit':{'path':'evidence/swift-coverage-220/coverage.json','sha256':digest(ROOT/'evidence/swift-coverage-220/coverage.json')},'families':families,'new_families_with_complete_typed_coverage':7,'unresolved_templates':OPAQUE,'release_population_approved':False,'counts':{'registry_templates':58,'current_swift_inputs':104,'historical_v1_rows_per_tool':90,'A40_rows_per_tool':14,'common_revision_release_rows':0},'limits':'Native unsupported is a prospective capability record, not analyzer execution; Result inconclusive preserves actual attempts. Historical report revisions remain distinct.'}
    return {'current-population.json':membership,'execution-plan.json':plan,'coverage-v2.json':coverage}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    for name,value in build().items():
        path=BASE/name;content=encoded(value)
        if args.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
        else:assert path.read_text()==content,'stale preparation '+name
    print('Blocked preparation:1104 observed inputs,92 report lanes,4244 historical rows; seven new families covered,two opaque choices pending')


if __name__=='__main__':main()
