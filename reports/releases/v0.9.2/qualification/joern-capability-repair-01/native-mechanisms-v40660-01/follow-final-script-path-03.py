import pathlib,json,subprocess
O=pathlib.Path('reports/releases/v0.9.2/qualification/joern-capability-repair-01/native-mechanisms-v40660-01');R=pathlib.Path.cwd();p=json.loads((R/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());rt=pathlib.Path(p['runtime']['joern_root']);j=pathlib.Path(p['runtime']['java_home'])/'bin/javap';cp=str(rt/'lib/*')+':'+str(rt/'frontends/swiftsrc2cpg/lib/*');a=[]
for i,t in enumerate(['replpp.UsingDirectives$','replpp.scripting.NonForkingScriptRunner$','replpp.scripting.NonForkingScriptRunner'],60):
 n=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}';argv=[str(j),'-classpath',cp,'-p','-c',t];d=subprocess.run(argv,capture_output=True,text=True,timeout=60)
 for ext,txt in [('stdout.txt',d.stdout),('stderr.txt',d.stderr)]:
  z=O/(n+'.'+ext);assert not z.exists();z.write_text(txt)
 a.append(dict(argv=argv,returncode=d.returncode,stdout=n+'.stdout.txt',stderr=n+'.stderr.txt'))
z=O/'static-commands-03d.json';assert not z.exists();z.write_text(json.dumps(a,indent=2)+'\n');print([(x['argv'][-1],x['returncode'])for x in a])
