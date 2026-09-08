#!/usr/bin/env python3
"""Retain current released CLI surfaces for the preregistered warm audit."""
import datetime,json,pathlib,subprocess,os
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'reports/raw/warm-observability-v071';OUT.mkdir(parents=True,exist_ok=True)
t=json.loads((ROOT/'reports/releases/v0.7.1/identities.json').read_text())['tools']
commands=[('bifrost',[t['bifrost']['path'],'--help']),('codeql-create',[t['codeql']['path'],'database','create','--help']),('codeql-analyze',[t['codeql']['path'],'database','analyze','--help']),('joern',[t['joern']['path'],'--help']),('semgrep',[t['semgrep']['path'],'scan','--help']),('infer',[t['infer']['path'],'analyze','--help']),('flowdroid',[t['java']['path'],'-jar',t['flowdroid_jar']['path'],'--help']),('pysa',[t['pyre']['path'],'analyze','--help']),('opentaint-jar',[t['java']['path'],'-jar',t['opentaint_analyzer']['path'],'--help']),('opentaint-product',['/private/tmp/dfb-v071-opentaint-full-653a/opentaint','scan','--help'])]
for name,args in commands:
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();load=os.getloadavg()
 with open(OUT/(name+'-stdout.txt'),'wb') as o,open(OUT/(name+'-stderr.txt'),'wb') as e:code=subprocess.run(args,cwd=ROOT,stdout=o,stderr=e).returncode
 with open(OUT/'commands.jsonl','a') as f:f.write(json.dumps({'id':name,'argv':args,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':code,'load_before':load})+'\n')
# Help is evidence of advertised surface, not proof that omitted capability is absent.
(OUT/'scope.json').write_text(json.dumps({'kind':'released-cli-surface-audit','scope':'Must combine these observations with existing A15/A21 contracts and executed same-work warm controls. Help absence alone proves no capability decline.','flowdroid':'Batch support previously observed; whole-population per-case-config equivalence remains unresolved and no warm number is inferred.','warm_measurements':['Joern Java','Semgrep Java largest identical-rule group']},indent=2)+'\n')
