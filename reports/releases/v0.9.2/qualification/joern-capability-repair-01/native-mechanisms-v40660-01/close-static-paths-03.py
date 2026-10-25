"""Append-only disassembly of concrete frontend/startup call targets from capture02."""
from pathlib import Path
import json,subprocess,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[5];P=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(P['runtime']['joern_root']);J=Path(P['runtime']['java_home'])/'bin/javap';cp=str(R/'lib/*')+':'+str(R/'frontends/swiftsrc2cpg/lib/*')
targets=['io.joern.console.ScriptExecution','io.joern.console.PluginHandling','io.joern.console.Config$','io.joern.joerncli.console.RunBeforeCode$','io.joern.console.BridgeBase$$anon$1','io.joern.swiftsrc2cpg.utils.AstGenRunner','io.joern.swiftsrc2cpg.passes.AstCreationPass','io.joern.swiftsrc2cpg.passes.BuiltinTypesPass','io.joern.swiftsrc2cpg.passes.ClosureBindingsPass','io.joern.swiftsrc2cpg.passes.ConfigFileCreationPass','io.joern.swiftsrc2cpg.passes.DependenciesPass','io.joern.swiftsrc2cpg.passes.ExtensionsPass','io.joern.swiftsrc2cpg.passes.FullNameUniquenessPass','io.joern.swiftsrc2cpg.passes.MetaDataPass','io.joern.swiftsrc2cpg.passes.ObjcCallFullNamePass','io.joern.x2cpg.X2CpgFrontend','io.joern.swiftsrc2cpg.Main$','io.joern.swiftsrc2cpg.passes.SwiftTypeNodePass$']
cs=[]
for i,t in enumerate(targets,25):
 name=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}';a=[str(J),'-classpath',cp,'-p','-c',t];d=subprocess.run(a,capture_output=True,text=True,timeout=60)
 for s,v in [('stdout.txt',d.stdout),('stderr.txt',d.stderr)]:
  p=O/f'{name}.{s}';assert not p.exists();p.write_text(v)
 cs.append({'argv':a,'returncode':d.returncode,'stdout':name+'.stdout.txt','stderr':name+'.stderr.txt'})
p=O/'static-commands-03.json';assert not p.exists();p.write_text(json.dumps(cs,indent=2)+'\n');print(json.dumps({'commands':len(cs),'errors':[x['argv'][-1] for x in cs if x['returncode']]}))
