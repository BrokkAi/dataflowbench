from pathlib import Path
import subprocess,time,json,hashlib
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench');out=root/'evidence/codeql-swift/activation-218/final-activation-v2';out.mkdir(exist_ok=False)
cli='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql';q='adapters/codeql/swift/queries/'
controls=[('models','models-positive',[q+'SwiftModeling.ql',q+'SwiftModelingOff.ql',q+'SwiftModelingEndpointProbe.ql']),('receiver-positive','receivers-positive',[q+'SwiftModeling.ql',q+'SwiftModelingOff.ql',q+'SwiftModelingEndpointProbe.ql']),('receiver-negative','receivers-negative',[q+'SwiftModeling.ql',q+'SwiftModelingOff.ql',q+'SwiftModelingEndpointProbe.ql']),('calibration-on','calibration-positive',[q+'SwiftCalibration.ql',q+'SwiftKernelEndpointProbe.ql']),('calibration-off','calibration-positive',[q+'SwiftKernel.ql',q+'SwiftKernelEndpointProbe.ql'])]
(out/'query-hashes.json').write_text(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/q).glob('*')},indent=2)+'\n')
for name,db,queries in controls:
 argv=[cli,'database','analyze','/private/tmp/dfb-codeql-swift-218-'+db+'/db']+queries+['--rerun','--format=sarif-latest','--output='+str(out/(name+'.sarif')),'--common-caches=/private/tmp/dfb-codeql-swift-218-packs','--threads=2','--ram=2048']
 start=time.time();p=subprocess.run(argv,cwd=root,capture_output=True)
 (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);(out/(name+'.command.json')).write_text(json.dumps(dict(argv=argv,exit_status=p.returncode,elapsed_seconds=time.time()-start),indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:break
