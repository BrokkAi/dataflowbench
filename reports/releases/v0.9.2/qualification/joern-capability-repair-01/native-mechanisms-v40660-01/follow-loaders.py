"""Follow concrete classes discovered in static phase01; no analyzer execution."""
from pathlib import Path
import json,subprocess,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[5];P=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(P['runtime']['joern_root']);J=Path(P['runtime']['java_home'])/'bin/javap';cp=str(R/'lib/*')+':'+str(R/'frontends/swiftsrc2cpg/lib/*')
targets=['io.joern.dataflowengineoss.semanticsloader.FullNameSemanticsParser','io.joern.joerncli.console.ReplBridge$','io.joern.console.QueryDatabase$','io.joern.console.QueryDatabase','io.joern.console.scan.package$','io.joern.console.scan.ScanPass','io.joern.console.BridgeBase','io.joern.console.Config','io.joern.swiftsrc2cpg.utils.SwiftTypesProvider','io.joern.swiftsrc2cpg.Config','io.joern.x2cpg.frontendspecific.swiftsrc2cpg.SwiftTypeRecoveryPassGenerator','io.joern.dataflowengineoss.semanticsloader.Semantics$','io.joern.dataflowengineoss.semanticsloader.FullNameSemantics$','io.joern.dataflowengineoss.semanticsloader.FlowSemantic$','io.joern.joerncli.Scan$']
cs=[]
for i,t in enumerate(targets,10):
 name=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}';a=[str(J),'-classpath',cp,'-p','-c',t];d=subprocess.run(a,capture_output=True,text=True,timeout=60)
 for s,v in [('stdout.txt',d.stdout),('stderr.txt',d.stderr)]:
  p=O/f'{name}.{s}';assert not p.exists();p.write_text(v)
 cs.append({'argv':a,'returncode':d.returncode,'stdout':name+'.stdout.txt','stderr':name+'.stderr.txt'})
p=O/'static-commands-02.json';assert not p.exists();p.write_text(json.dumps(cs,indent=2)+'\n');print(json.dumps({'commands':len(cs),'errors':[x['argv'][-1] for x in cs if x['returncode']]}))
