import subprocess,json,time,hashlib,os
from pathlib import Path
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench')
out=root/'evidence/codeql-swift/activation-218/attempt-08-models'
out.mkdir()
import shutil
shutil.copytree(out.parent/'controls',out/'controls')
for f in (out/'controls').glob('*/main.swift'):
 lines=f.read_text().splitlines(); f.write_text('\n'.join(lines[:2])+ '\nfunc runActivation() {\n'+ '\n'.join(lines[2:])+'\n}\nrunActivation()\n')
cli=Path('/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql')
def run(name,argv):
 start=time.time(); p=subprocess.run([str(a) for a in argv],capture_output=True,cwd=root)
 (out/(name+'.stdout')).write_bytes(p.stdout); (out/(name+'.stderr')).write_bytes(p.stderr)
 (out/(name+'.json')).write_text(json.dumps(dict(argv=[str(a) for a in argv],cwd=str(root),exit_status=p.returncode,started_unix=start,elapsed_seconds=time.time()-start),indent=2)+'\n')
 return p
run('cli',[cli,'version','--format=json'])
for name,args in [('compiler',['xcrun','swiftc','--version']),('compiler-path',['xcrun','--find','swiftc']),('xcode',['xcodebuild','-version']),('host',['sw_vers']),('architecture',['uname','-m']),('sdk',['xcrun','--show-sdk-path']),('sdk-version',['xcrun','--show-sdk-version']),('sdk-build',['xcrun','--show-sdk-build-version'])]:run(name,args)
for f in (out/'controls').glob('*/main.swift'):
 f.write_text(f.read_text().replace('activationSource','dfb_source').replace('activationSink','dfb_sink'))
(out/'controls/positive/main.swift').write_text('enum Config {\n static func fetchRemote() -> String { "" }\n static func fetchLocal() -> String { "" }\n}\nenum Audit {\n static func record(_ value: String) { }\n static func discard(_ value: String) { }\n}\nenum Clean {\n static func scrub(_ value: String) -> String { value }\n static func sanitize(_ value: String) -> String { value }\n}\nfunc dfb_source() -> String { "" }\nfunc dfb_sink(_ value: String) { print(value) }\nfinal class Handler {\n func onRequest(_ input: String) { dfb_sink(input) }\n func onIgnored(_ input: String) { dfb_sink(input) }\n func onDeclared(_ input: String) { dfb_sink(input) }\n func onUndeclared(_ input: String) { dfb_sink(input) }\n}\nfunc runActivation() {\n dfb_sink(Config.fetchRemote())\n dfb_sink(Config.fetchLocal())\n Audit.record(dfb_source())\n Audit.discard(dfb_source())\n dfb_sink(Clean.scrub(dfb_source()))\n dfb_sink(Clean.sanitize(dfb_source()))\n}\nrunActivation()\n\nfinal class Box { var payload = ""; var spare = "" }\nenum Bridge {\n static func `pass`(_ value: String) -> String { "" }\n static func hold(_ value: String) -> String { value }\n static func deposit(_ value: String, _ box: Box) { }\n}\nenum Store {\n static func put(_ key: String, _ value: String) { }\n static func get(_ key: String) -> String { "" }\n}\nfunc writeProbe() { Store.put("primary", dfb_source()) }\nfunc readProbe() {\n dfb_sink(Store.get("primary"))\n dfb_sink(Store.get("other"))\n}\nfunc summaryProbe() {\n dfb_sink(Bridge.pass(dfb_source()))\n dfb_sink(Bridge.hold(dfb_source()))\n let box = Box()\n Bridge.deposit(dfb_source(), box)\n dfb_sink(box.payload)\n dfb_sink(box.spare)\n}\nwriteProbe()\nreadProbe()\nsummaryProbe()\n')
compiler=Path((out/'compiler-path.stdout').read_text().strip()); sdk=(out/'sdk.stdout').read_text().strip()
files=[compiler,cli,cli.parent/'swift/tools/osx64/extractor.real',cli.parent/'swift/codeql-extractor.yml',cli.parent.parent/'codeql-osx64.zip']
(out/'identities.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
(out/'environment.json').write_text(json.dumps({k:os.environ.get(k) for k in ['PATH','DEVELOPER_DIR','SDKROOT','MACOSX_DEPLOYMENT_TARGET']},indent=2)+'\n')
for polarity in ['positive']:
 source=out/'controls'/polarity; work=Path('/private/tmp/dfb-codeql-swift-218-models-'+polarity);work.mkdir(exist_ok=False)
 args=[str(compiler),'-swift-version','6','-Onone','-sdk',sdk,'-target','arm64-apple-macosx27.0.0','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(work/'cache'),str(source/'main.swift'),'-o',str(work/'program')]
 run(polarity+'-compile',args)
 import shlex
 p=run(polarity+'-extract',[cli,'database','create',work/'db','--language=swift','--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(args)])
 print(polarity,p.returncode,p.stderr.decode()[-3000:],flush=True)
