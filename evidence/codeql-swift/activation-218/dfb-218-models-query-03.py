from pathlib import Path
import subprocess,json,time
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench');out=root/'evidence/codeql-swift/activation-218/attempt-08-models';cli='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql'
argv=[cli,'database','analyze','/private/tmp/dfb-codeql-swift-218-models-positive/db','adapters/codeql/swift/queries/SwiftModeling.ql','adapters/codeql/swift/queries/SwiftModelingOff.ql','--format=sarif-latest','--output='+str(out/'models-03.sarif'),'--common-caches=/private/tmp/dfb-codeql-swift-218-packs','--threads=2','--ram=2048']
start=time.time();p=subprocess.run(argv,cwd=root,capture_output=True)
(out/'analysis-03.stdout').write_bytes(p.stdout);(out/'analysis-03.stderr').write_bytes(p.stderr);(out/'analysis-03.json').write_text(json.dumps(dict(argv=argv,exit_status=p.returncode,elapsed_seconds=time.time()-start),indent=2));print(p.returncode,p.stderr.decode()[-1500:])
