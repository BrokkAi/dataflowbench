"""One bounded diagnostic-only build/probe; refuses unreviewed inputs/reuse."""
import os,sys,json,pathlib,hashlib,datetime,subprocess,zipfile,importlib.util,time
R=pathlib.Path('/Users/dave/.codex/worktrees/9f01/dataflowbench'); S=pathlib.Path('/private/tmp/joern05-native-control-08'); D=pathlib.Path('/private/tmp/joern05-agent05-build-01')
V=R/'reports/releases/v0.9.2/validation/joern-post-bifrost-01'; review=pathlib.Path('/private/tmp/joern05-native-control-08-independent-source-review-01.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def load(p):return json.loads(p.read_bytes())
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
assert len(sys.argv)==2 and len(sys.argv[1])==64
assert review.is_file() and sha(review)==sys.argv[1]
rv=load(review)
# Root supplies a separately sealed decision after inspecting this review.
decision=pathlib.Path('/private/tmp/joern05-agent05-build-decision-01.json');a=load(decision)
assert a['review']['sha256']==sha(review) and a['approved'] is True and a['namespace']==str(D)
assert a['source']['sha256']==sha(S/'StartupWitnessAgent.java')=='d7c4b65acf156278ab650dac993fe1e900ac4dd5b5b6e1d83453a809ce57fefa'
assert a['traversal_test']['sha256']==sha(S/'StartupWitnessAgentTraversalTest.java')=='aaa11f0f85fc8906bc04f416c91297e4a3d9df3463034c461ad2ef26d68dac6f'
assert a['runner']['sha256']==sha(pathlib.Path(__file__))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='76e6121651e94be113fd0d5f027419f7d0f0859b'
assert sha(R/'reports/releases/v0.9.2/ledger-v1.jsonl')=='2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851'
assert not D.exists();D.mkdir();C=D/'classes';C.mkdir();H=D/'home';H.mkdir();T=D/'tmp';T.mkdir();E=D/'events';E.mkdir()
java=pathlib.Path('/Users/dave/.sdkman/candidates/java/21.0.8-tem/bin/java');javac=java.with_name('javac')
env={'PATH':str(java.parent)+':/usr/bin:/bin','JAVA_HOME':str(java.parent.parent),'HOME':str(H),'TMPDIR':str(T),'LANG':'C','LC_ALL':'C'}
commands=[]
def run(argv,name,limit,process_env=env):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=D/(name+'.stdout');err=D/(name+'.stderr')
 with out.open('xb') as o,err.open('xb') as e:
  p=subprocess.run(argv,cwd=D,env=process_env,stdout=o,stderr=e,timeout=limit,check=False)
 row={'argv':argv,'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':limit,'exit_code':p.returncode,'environment':process_env,'stdout':ref(out),'stderr':ref(err)};commands.append(row);write(D/(name+'.json'),row);assert p.returncode==0,(name,err.read_text());return row
write(D/'started.json',{'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':ref(decision),'review':ref(review),'runner':ref(pathlib.Path(__file__)),'source':ref(S/'StartupWitnessAgent.java'),'traversal_test':ref(S/'StartupWitnessAgentTraversalTest.java'),'javac':ref(javac.resolve()),'java':ref(java.resolve()),'scored_run':False,'native_controls':False,'automatic_retry':False})
run([str(javac),'-J-Xmx128m','-J-XX:ActiveProcessorCount=2','--release','21','-encoding','UTF-8','-d',str(C),str(S/'StartupWitnessAgent.java'),str(S/'StartupWitnessAgentTraversalTest.java')],'javac',30)
run([str(java),'-Xmx64m','-XX:ActiveProcessorCount=2','-cp',str(C),'dfb.joern.StartupWitnessAgentTraversalTest'],'fake-traversal-tests',30)
classes=sorted((C/'dfb/joern').glob('StartupWitnessAgent*.class'));classes=[p for p in classes if 'TraversalTest' not in p.name];assert classes
jar=D/'joern-startup-witness-agent-05.jar';manifest=b'Manifest-Version: 1.0\r\nPremain-Class: dfb.joern.StartupWitnessAgent\r\n\r\n'
def package(dst):
 with zipfile.ZipFile(dst,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  pairs=[('META-INF/MANIFEST.MF',manifest)]+[(str(p.relative_to(C)),p.read_bytes()) for p in classes]
  for name,raw in pairs:
   zi=zipfile.ZipInfo(name,(1980,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=(0o100644<<16);zi.create_system=3;z.writestr(zi,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
package(jar);package(D/'packaging-repeat.jar');assert sha(jar)==sha(D/'packaging-repeat.jar')
proof={'schema':'v092-joern-agent05-bounded-build/v1','ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'built-and-fake-tests-passed; premain-probe-pending-jar-review','decision':ref(decision),'review':ref(review),'source':ref(S/'StartupWitnessAgent.java'),'traversal_test_source':ref(S/'StartupWitnessAgentTraversalTest.java'),'commands':commands,'agent_jar':ref(jar),'compiled_classes':[ref(p) for p in classes],'packaging_repeat_identical':True,'compiler_invocations':1,'fake_test_jvm_invocations':1,'standalone_premain_version_jvm_invocations':0,'native_control_matrix_executed':False,'scored_attempt_consumed':False,'qualification_inferred':False,'semantic_jvm_proof_inferred':False,'automatic_retry':False,'publication_hold':True}
write(D/'build-result-01.json',proof);print(json.dumps({'result':ref(D/'build-result-01.json'),'jar':ref(jar),'commands':len(commands)}))
