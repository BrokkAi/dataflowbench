import subprocess,time,json
from pathlib import Path
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench');out=root/'evidence/codeql-swift/activation-218';cli='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql'
for polarity in ['positive','negative']:
 argv=[cli,'query','run','adapters/codeql/swift/ActivationFlow.ql','--database=/private/tmp/dfb-codeql-swift-218-'+polarity+'/db','--output='+str(out/(polarity+'-flow.bqrs')),'--common-caches=/private/tmp/dfb-codeql-swift-218-packs','--threads=2','--ram=2048']
 start=time.time();p=subprocess.run(argv,cwd=root,capture_output=True)
 (out/(polarity+'-flow.stdout')).write_bytes(p.stdout);(out/(polarity+'-flow.stderr')).write_bytes(p.stderr);(out/(polarity+'-flow-command.json')).write_text(json.dumps(dict(argv=argv,exit_status=p.returncode,elapsed_seconds=time.time()-start),indent=2))
 print(polarity,p.returncode,p.stderr.decode()[-1000:],flush=True)
 if p.returncode:break
 subprocess.run([cli,'bqrs','decode',str(out/(polarity+'-flow.bqrs')),'--format=json','--output='+str(out/(polarity+'-flow.json'))],check=True)
