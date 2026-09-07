#!/usr/bin/env python3
"""Execute one preregistered v0.7.1 stage serially; stop on unexplained failures."""
import argparse,json,pathlib,runpy,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'reports/releases/v0.7.1'
p=argparse.ArgumentParser();p.add_argument('stage',choices=['reports','repeats','probes','native','warm','overhead']);p.add_argument('--list',action='store_true');args=p.parse_args()
plan=json.loads((BASE/'plan.json').read_text());supp=json.loads((BASE/'supplemental-plan.json').read_text())['commands']
if args.stage=='reports':steps=[r for r in plan['reports'] if not r['id'].endswith('-native')]
elif args.stage=='native':steps=[r for r in plan['reports'] if r['id'].endswith('-native')]
elif args.stage=='repeats':steps=[next(r for r in plan['reports'] if r['id']==i) for i in json.loads((BASE/'overlap-rerun-plan.json').read_text())['repeat_once']]
elif args.stage=='probes':steps=plan['script_probes']+supp
else:steps=plan[args.stage]
if args.list:
 for r in steps:print(r['id'],json.dumps(r['argv']))
 raise SystemExit(0)
record=runpy.run_path(str(ROOT/'scripts/record-release-attempt.py'))['run']
for r in steps:
 code=record(r['id'],r['argv'],settle=args.stage=='overhead')
 last=json.loads((BASE/'ledger.jsonl').read_text().splitlines()[-1])
 if 'report' in r:
  fresh=next((o for o in last['outputs'] if o['original_path']==r['report']),None)
  if fresh is None:raise SystemExit('missing fresh report '+r['id'])
  report=json.loads((ROOT/fresh['path']).read_text())
  if sorted(x['case_id'] for x in report['results'])!=sorted(r['case_ids']):raise SystemExit('population mismatch '+r['id'])
 if code:
  error=(ROOT/last['stderr']['path']).read_text()
  if 'report' not in r or not error.startswith('Error: committed reports drifted from the current adapter configuration:'):
   print('Stopped with retained failure:',last['id'],file=sys.stderr);raise SystemExit(code)
 if last['missing_fresh_output_roots']:raise SystemExit('missing fresh output roots '+r['id'])
