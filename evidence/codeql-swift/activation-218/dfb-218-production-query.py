from pathlib import Path
import subprocess,time,json
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench');out=root/'evidence/codeql-swift/activation-218/attempt-04';cli='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql'
for polarity in ['positive','negative']:
 argv=[cli,'database','analyze','/private/tmp/dfb-codeql-swift-218-production-'+polarity+'/db','adapters/codeql/swift/queries/SwiftKernel.ql','adapters/codeql/swift/queries/SwiftKernelEndpointProbe.ql','--format=sarif-latest','--output='+str(out/(polarity+'.sarif')),'--common-caches=/private/tmp/dfb-codeql-swift-218-packs','--threads=2','--ram=2048']
 start=time.time();p=subprocess.run(argv,cwd=root,capture_output=True)
 (out/(polarity+'-analysis.stdout')).write_bytes(p.stdout);(out/(polarity+'-analysis.stderr')).write_bytes(p.stderr);(out/(polarity+'-analysis.json')).write_text(json.dumps(dict(argv=argv,exit_status=p.returncode,elapsed_seconds=time.time()-start),indent=2))
 print(polarity,p.returncode,p.stderr.decode()[-1000:],flush=True)
 if p.returncode:break
