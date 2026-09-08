#!/usr/bin/env python3
"""Derive progress and outcome deltas only from completed fresh attempt snapshots."""
import collections,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'reports/releases/v0.7.1'
plan=json.loads((BASE/'plan.json').read_text());rows=[json.loads(x) for x in (BASE/'ledger.jsonl').read_text().splitlines()];expected={r['id']:r for r in plan['reports']};latest={};attempts=[]
for row in rows:
 if row['planned_id'] not in expected:continue
 r=expected[row['planned_id']];fresh=next((o for o in row['outputs'] if o['original_path']==r['report']),None)
 if fresh is None:attempts.append({'id':row['id'],'status':'missing-fresh-report'});continue
 d=json.loads((ROOT/fresh['path']).read_text());old=json.loads(subprocess.check_output(['git','show',plan['outcome_comparison_revision']+':'+r['report']],cwd=ROOT));before={x['case_id']:x['outcome'] for x in old['results']}
 item={'id':row['id'],'planned_id':row['planned_id'],'report':fresh,'exit_code':row['exit_code'],'population_matches':sorted(x['case_id'] for x in d['results'])==sorted(r['case_ids']),'results':len(d['results']),'tool_version':d['tool_version'],'outcomes':dict(collections.Counter(x['outcome'] for x in d['results'])),'deltas':[{'case_id':x['case_id'],'before':before.get(x['case_id']),'after':x['outcome']} for x in d['results'] if before.get(x['case_id'])!=x['outcome']]};attempts.append(item);latest[row['planned_id']]=item
started_only=[p.parent.name for p in (BASE/'attempts').glob('*/started.json') if not (p.parent/'completed.json').exists()]
out={'expected_reports':82,'completed_fresh_reports':len(latest),'completed_results':sum(x['results'] for x in latest.values()),'missing_reports':sorted(set(expected)-set(latest)),'started_without_completion':started_only,'attempts':attempts,'note':'Completion is evidence coverage, not publication qualification; preserve every attempt and audit timing overlap independently.'};(BASE/'progress.json').write_text(json.dumps(out,indent=2)+'\n');print(out['completed_fresh_reports'],'reports',out['completed_results'],'results; active/incomplete',started_only)
