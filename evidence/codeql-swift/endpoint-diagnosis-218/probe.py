import subprocess,json,time,hashlib,shlex,shutil
from pathlib import Path
root=Path.cwd();out=root/'evidence/codeql-swift/endpoint-diagnosis-218';out.mkdir(exist_ok=True)
binary='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql';packs='/private/tmp/dfb-codeql-swift-218-packs/packages'
compiler=subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip();sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
def run(name,argv):
 start=time.monotonic();p=subprocess.run(argv,capture_output=True)
 (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);(out/(name+'.command.json')).write_text(json.dumps({'argv':argv,'exit_status':p.returncode,'elapsed_seconds':time.monotonic()-start,'cwd':str(root)},indent=2)+'\n');assert p.returncode==0,p.stderr.decode()[-1500:]
for fixture in ['array-element-positive','callback-registration-positive']:
 source=root/'cases/taint/swift'/fixture;work=Path('/private/tmp/dfb-218-diagnosis-'+fixture);work.mkdir(exist_ok=False)
 args=[compiler,'-swift-version','6','-Onone','-sdk',sdk,'-target','arm64-apple-macosx27.0.0','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(work/'cache'),str(source/'main.swift'),'-o',str(work/'fixture')]
 (out/(fixture+'-fixture-sha256.txt')).write_text(hashlib.sha256((source/'main.swift').read_bytes()).hexdigest()+'\n')
 run(fixture+'-create',[binary,'database','create',str(work/'db'),'--language=swift','--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(args)])
 run(fixture+'-query',[binary,'query','run',str(root/'adapters/codeql/swift/EndpointCoverageDiagnostic.ql'),'--database='+str(work/'db'),'--output='+str(out/(fixture+'.bqrs')),'--additional-packs='+packs,'--threads=2','--ram=2048'])
 run(fixture+'-decode',[binary,'bqrs','decode',str(out/(fixture+'.bqrs')),'--format=json'])
 print(fixture,(out/(fixture+'-decode.stdout')).read_text(),flush=True)
