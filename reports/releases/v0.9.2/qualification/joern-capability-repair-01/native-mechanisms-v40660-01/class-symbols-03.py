"""Decode JVM constant-pool structural class/method/field refs, not source regex."""
from pathlib import Path
import json,struct,zipfile,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[5];plan=json.loads((ROOT/'adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json').read_text());R=Path(plan['runtime']['joern_root'])
def parse(data):
 def u1(o):return data[o]
 def u2(o):return struct.unpack_from('>H',data,o)[0]
 assert data[:4]==b'\xca\xfe\xba\xbe';cp=[None]*u2(8);i=1;o=10
 while i<len(cp):
  t=u1(o);o+=1
  if t==1:n=u2(o);o+=2;cp[i]=(t,data[o:o+n].decode('utf8',errors='replace'));o+=n
  elif t in (3,4):cp[i]=(t,);o+=4
  elif t in (5,6):cp[i]=(t,);o+=8;i+=1
  elif t in (7,8,16,19,20):cp[i]=(t,u2(o));o+=2
  elif t in (9,10,11,12,17,18):cp[i]=(t,u2(o),u2(o+2));o+=4
  elif t==15:cp[i]=(t,u1(o),u2(o+1));o+=3
  else:raise ValueError('tag'+str(t))
  i+=1
 def utf(i):return cp[i][1]
 refs=[]
 for a in cp:
  if a and a[0] in (9,10,11):
   cl=cp[a[1]];nt=cp[a[2]];refs.append({'kind':{9:'field',10:'method',11:'interface-method'}[a[0]],'owner':utf(cl[1]),'name':utf(nt[1]),'descriptor':utf(nt[2])})
 return {'classes':sorted({utf(a[1])for a in cp if a and a[0]==7}),'strings':sorted({utf(a[1])for a in cp if a and a[0]==8}),'member_refs':refs}
targets=['frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.660.jar','frontends/swiftsrc2cpg/lib/io.joern.x2cpg-4.0.660.jar','lib/io.joern.dataflowengineoss-4.0.660.jar']
records=[];errors=[]
for rel in targets:
 with zipfile.ZipFile(R/rel)as z:
  for n in z.namelist():
   include=(rel.endswith('swiftsrc2cpg-4.0.660.jar') or 'frontendspecific/swiftsrc2cpg/'in n or n=='io/joern/dataflowengineoss/DefaultSemantics$.class')
   if not include or not n.endswith('.class'):continue
   try:d=z.read(n);records.append({'jar':rel,'member':n,'sha256':hashlib.sha256(d).hexdigest(),**parse(d)})
   except Exception as e:errors.append({'jar':rel,'member':n,'error':repr(e)})
reflection=[];semantic=[]
for c in records:
 for r in c['member_refs']:
  if r['owner'].startswith(('java/lang/reflect','java/lang/ClassLoader','java/net/URLClassLoader'))or(r['owner']=='java/lang/Class'and r['name']in ['forName','getMethod','getMethods','getDeclaredMethods','getField']):reflection.append({'class':c['member'],**r})
  if 'dataflowengineoss' in r['owner']:semantic.append({'class':c['member'],**r})
out={'schema':'jvm-structural-member-reference-inventory/v1','scope':'Every class in exact Swift frontend, every swiftspecific class in exact x2cpg, exact DefaultSemantics singleton. No class execution.','classes':records,'errors':errors,'reflection_or_classloader_member_refs':reflection,'dataflow_member_refs':semantic,'limitations':['Constant-pool presence is structural symbolic linkage, not a dynamic call reachability proof.','String inventory is not used alone as absence proof; exact loader/role interpretation requires bytecode paths.']}
p=O/'swift-structural-symbols-03.json';assert not p.exists();p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'classes':len(records),'errors':len(errors),'reflection_refs':len(reflection),'dataflow_refs':len(semantic),'reflection':reflection[:8]}))
