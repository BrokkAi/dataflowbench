"""Resolve installed launch classpaths and disassembled class providers only."""
from pathlib import Path
import json,zipfile,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[5];P=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(P['runtime']['joern_root']);j=json.loads((O/'jar-members.json').read_text());by={x['path']:x for x in j}
def manifestattrs(s):
 s=s.replace('\r\n','\n').replace('\n ','');return dict(line.split(': ',1) for line in s.splitlines() if ': ' in line)
launcher='frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.660-launcher.jar';a=manifestattrs(by[launcher]['manifest']);swift=[]
for n in a['Class-Path'].split():
 p=(R/launcher).parent/n
 swift.append({'manifest_entry':n,'path':str(p.relative_to(R)),'exists':p.is_file(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None})
rootlib=[{'path':x['path'],'sha256':x['sha256']} for x in j if x['path'].startswith('lib/')]
commands=json.loads((O/'static-commands-01.json').read_text())['commands']+json.loads((O/'static-commands-02.json').read_text());targets=sorted(set(x['argv'][-1] for x in commands if x['returncode']==0));providers=[]
for t in targets:
 n=t.replace('.','/')+'.class';ps=[]
 for x in j:
  if x['path'].startswith(('lib/','frontends/swiftsrc2cpg/lib/')) and n in x['members']:
   with zipfile.ZipFile(R/x['path']) as z:d=z.read(n)
   ps.append({'jar':x['path'],'jar_sha256':x['sha256'],'member':n,'class_sha256':hashlib.sha256(d).hexdigest()})
 providers.append({'class':t,'providers':ps,'distinct_class_hashes':sorted(set(x['class_sha256'] for x in ps))})
res=json.loads((O/'resources.json').read_text());nested=[{'jar':x['jar'],'member':x['member'],'sha256':x['sha256']} for x in res if x['member'].lower().endswith(('.jar','.zip','.tar','.gz','.tgz'))]
v={'launchers':{'joern':'joern -> bin/repl-bridge main io.joern.joerncli.console.ReplBridge; app_classpath lib/*','joern_scan':'joern-scan -> bin/joern-scan main io.joern.joerncli.JoernScan; app_classpath lib/*','swift_frontend':{'launcher':launcher,'main':a['Main-Class'],'manifest_classpath':swift}},'root_lib_classpath':rootlib,'disassembly_class_providers':providers,'nested_archive_resources':nested,'nested_runtime_scope_archive_resources':[x for x in nested if x['jar'].startswith(('lib/','frontends/swiftsrc2cpg/lib/'))],'scanner_bundle_members_installed':[{'jar':x['path'],'member':n}for x in j for n in x['members'] if n.startswith(('io/joern/scanners/','io/shiftleft/ocular/scanners/'))], 'limitations':['Launcher command line/environment can supply code, Java options, agents and user-controlled configuration; this capture does not execute or exhaust all possible external classloader state.','Nested archives outside bound Swift/root runtime paths are inventoried but not recursively inspected.','No upstream source checkout was fetched or used as exact4.0.660 implementation authority.']}
p=O/'classpath-and-providers.json';assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'root_lib_jars':len(rootlib),'swift_manifest_jars':len(swift),'missing_swift_refs':sum(not x['exists'] for x in swift),'class_provider_conflicts':sum(len(x['distinct_class_hashes'])!=1 for x in providers),'nested_runtime_archives':len(v['nested_runtime_scope_archive_resources']),'shipped_scanner_members':len(v['scanner_bundle_members_installed'])}))
