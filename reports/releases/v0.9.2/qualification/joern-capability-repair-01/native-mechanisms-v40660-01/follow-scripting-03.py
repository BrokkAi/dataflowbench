from pathlib import Path
import json,subprocess
O=Path(__file__).resolve().parent;ROOT=O.parents[5];P=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(P['runtime']['joern_root']);J=Path(P['runtime']['java_home'])/'bin/javap';cp=str(R/'lib/*')+':'+str(R/'frontends/swiftsrc2cpg/lib/*');targets=['replpp.scripting.ScriptRunner$','replpp.Config$','replpp.Config$ForClasspath$','replpp.Config$ForClasspath','io.joern.joerncli.console.Joern$','io.joern.joerncli.console.JoernConsole$','io.joern.console.Run$','io.joern.console.CpgBasedTool','io.joern.swiftsrc2cpg.passes.AstCreationPass$']
c=[]
for i,t in enumerate(targets,43):
 n=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}';a=[str(J),'-classpath',cp,'-p','-c',t];d=subprocess.run(a,capture_output=True,text=True,timeout=60)
 for s,v in [('stdout.txt',d.stdout),('stderr.txt',d.stderr)]:
  p=O/f'{n}.{s}';assert not p.exists();p.write_text(v)
 c.append({'argv':a,'returncode':d.returncode,'stdout':n+'.stdout.txt','stderr':n+'.stderr.txt'})
p=O/'static-commands-03b.json';assert not p.exists();p.write_text(json.dumps(c,indent=2)+'\n');print(json.dumps({'commands':len(c),'errors':[x['argv'][-1]for x in c if x['returncode']]}))
