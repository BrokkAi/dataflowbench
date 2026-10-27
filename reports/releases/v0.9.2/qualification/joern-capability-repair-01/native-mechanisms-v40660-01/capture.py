#!/usr/bin/env python3
"""Static archive/class inspection only. Never executes an analyzer class."""
from pathlib import Path
import os,json,hashlib,zipfile,subprocess,datetime
ROOT=Path(__file__).resolve().parents[6]
OUT=Path(__file__).resolve().parent
PLAN=ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json'
plan=json.loads(PLAN.read_text()); R=Path(plan['runtime']['joern_root']); JAVAP=Path(plan['runtime']['java_home'])/'bin/javap'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(n,v):
 p=OUT/n
 if p.exists():raise RuntimeError('immutable output already exists: '+str(p))
 p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
files=[];links=[];jars=[];resources=[];classes=[];errors=[]
for folder,dirs,names in os.walk(R,followlinks=False):
 for name in sorted(dirs+names):
  p=Path(folder)/name
  if p.is_symlink():links.append({'path':str(p.relative_to(R)),'target':os.readlink(p),'resolved':str(p.resolve()),'external':not p.resolve().is_relative_to(R)})
 for name in sorted(names):
  p=Path(folder)/name
  if p.is_symlink():continue
  s=p.stat(); rel=str(p.relative_to(R)); sha=digest(p)
  files.append({'path':rel,'sha256':sha,'size':s.st_size,'mode':s.st_mode&0o7777})
  if p.suffix!='.jar':continue
  try:
   with zipfile.ZipFile(p) as z:
    entries=z.namelist();jars.append({'path':rel,'sha256':sha,'members':entries,'manifest':z.read('META-INF/MANIFEST.MF').decode('utf8',errors='replace') if 'META-INF/MANIFEST.MF'in entries else None})
    for n in entries:
     if n.endswith('/') :continue
     if n.endswith('.class'):
      if n.startswith(('io/joern/','io/shiftleft/')):classes.append({'jar':rel,'member':n})
     elif not n.endswith('.tasty'):
      d=z.read(n);resources.append({'jar':rel,'member':n,'size':len(d),'sha256':hashlib.sha256(d).hexdigest(), 'text':d.decode('utf8',errors='replace') if len(d)<65536 and (n.endswith(('.conf','.xml','.json','.properties','.MF')) or n.startswith('META-INF/services/')) else None})
  except Exception as e:errors.append({'path':rel,'error':repr(e)})
write('installation-files.json',{'root':str(R),'files':files,'symlinks':links,'errors':errors})
write('jar-members.json',jars);write('resources.json',resources);write('first-party-classes.json',classes)
manifest=json.loads((ROOT/'reports/releases/v0.9.2/acquisition/runtime-manifests/joern.json').read_text()); expected={x['path']:x['sha256'] for x in manifest['files']}; actual={x['path']:x['sha256'] for x in files}
write('runtime-manifest-comparison.json',{'manifest':{'path':'reports/releases/v0.9.2/acquisition/runtime-manifests/joern.json','sha256':digest(ROOT/'reports/releases/v0.9.2/acquisition/runtime-manifests/joern.json')},'expected_files':len(expected),'actual_files':len(actual),'missing':[k for k in expected if k not in actual],'added':[k for k in actual if k not in expected],'changed':[k for k in expected if k in actual and expected[k]!=actual[k]],'errors':errors})
# Discovery index only; role conclusions require reading actual APIs/calls.
terms=['semantic','querydb','querydatabase','scan','swift','loader','plugin','service']
write('discovery-index.json',{'warning':'Lexical discovery is not absence proof','classes':[x for x in classes if any(t in x['member'].lower() for t in terms)],'resources':[{'jar':x['jar'],'member':x['member']} for x in resources if any(t in x['member'].lower() for t in terms)]})
launchers=['joern','joern-scan','swiftsrc2cpg.sh','bin/repl-bridge','bin/joern-cli','bin/joern-scan','frontends/swiftsrc2cpg/bin/swiftsrc2cpg']
write('launcher-bindings.json',[{'path':n,'sha256':digest(R/n),'text':(R/n).read_text()}for n in launchers])
cp=str(R/'lib/*')+':'+str(R/'frontends/swiftsrc2cpg/lib/*')
targets=['io.joern.dataflowengineoss.DefaultSemantics$','io.joern.dataflowengineoss.semanticsloader.Semantics','io.joern.dataflowengineoss.semanticsloader.FullNameSemantics','io.joern.dataflowengineoss.semanticsloader.FullNameSemanticsParser$','io.joern.dataflowengineoss.semanticsloader.FlowSemantic','io.joern.swiftsrc2cpg.SwiftSrc2Cpg','io.joern.joerncli.JoernScan$','io.joern.joerncli.JoernScan','io.joern.console.ReplBridge']
commands=[]
for i,t in enumerate(targets,1):
 argv=[str(JAVAP),'-classpath',cp,'-p','-c',t];done=subprocess.run(argv,capture_output=True,text=True,timeout=60)
 name=f'javap-{i:02d}-{t.replace("$","object").replace(".","_")}'
 for suffix,text in [('stdout.txt',done.stdout),('stderr.txt',done.stderr)]:
  p=OUT/f'{name}.{suffix}'
  if p.exists():raise RuntimeError('outputexists')
  p.write_text(text)
 commands.append({'argv':argv,'cwd':str(ROOT),'returncode':done.returncode,'stdout':name+'.stdout.txt','stderr':name+'.stderr.txt'})
write('static-commands-01.json',{'javap':{'path':str(JAVAP),'sha256':digest(JAVAP)},'classpath':cp,'commands':commands,'analyzer_invocation':False})
write('capture-summary.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan':{'path':str(PLAN.relative_to(ROOT)),'sha256':digest(PLAN)},'identity':plan['identity'],'files':len(files),'jars':len(jars),'resources':len(resources),'first_party_classes':len(classes),'symlinks':len(links),'errors':errors,'static_commands':len(commands),'command_errors':[x for x in commands if x['returncode']]})
print(json.dumps({'files':len(files),'jars':len(jars),'resources':len(resources),'errors':len(errors),'command_errors':len([x for x in commands if x['returncode']])}))
