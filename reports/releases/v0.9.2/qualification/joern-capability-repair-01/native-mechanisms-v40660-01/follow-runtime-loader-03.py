from pathlib import Path
import json,subprocess
O=Path(__file__).resolve().parent;ROOT=O.parents[5];P=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(P['runtime']['joern_root']);J=Path(P['runtime']['java_home'])/'bin/javap';cp=str(R/'lib/*')+':'+str(R/'frontends/swiftsrc2cpg/lib/*');T=['replpp.util.ClasspathHelper$','replpp.package$','replpp.scripting.Main$','replpp.Config','io.joern.joerncli.console.JoernConsole','io.joern.joerncli.console.Joern','io.joern.dataflowengineoss.queryengine.EngineContext$','io.joern.swiftsrc2cpg.passes.BuiltinTypesPass$']
a=[]
for i,t in enumerate(T,52):
 n=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}';args=[str(J),'-classpath',cp,'-p','-c',t];d=subprocess.run(args,capture_output=True,text=True,timeout=60)
 for s,v in [('stdout.txt',d.stdout),('stderr.txt',d.stderr)]:
  p=O/f'{n}.{s}';assert not p.exists();p.write_text(v)
 a.append({'argv':args,'returncode':d.returncode,'stdout':n+'.stdout.txt','stderr':n+'.stderr.txt'})
p=O/'static-commands-03c.json';assert not p.exists();p.write_text(json.dumps(a,indent=2)+'\n');print(json.dumps({'commands':len(a),'errors':[x['argv'][-1]for x in a if x['returncode']]}))
