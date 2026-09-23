"""Bounded non-scored native endpoint identity diagnostic; no fixture execution."""
from pathlib import Path
import sys,os,json,shutil,shlex,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from swift_v2_process import run
from joern_swift import COMPILER,SDK,MODULE
r=Path(__file__).resolve().parent;out=r/'attempt-02';out.mkdir()
scratch=Path(tempfile.mkdtemp(prefix='dfb-joern-native-',dir='/private/tmp'));source=scratch/MODULE;source.mkdir();shutil.copyfile(r/'control-unqualified/main.swift',source/'main.swift')
cli=Path('/private/tmp/dfb-220-candidate-assets/joern/extracted/joern-cli');env=dict(os.environ,JAVA_HOME='/Users/dave/.sdkman/candidates/java/21.0.8-tem',SWIFTASTGEN_BIN=str(cli/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac'),_JAVA_OPTIONS='-Xmx512m')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
w={'status':'unqualified','scope':'Native endpoint identity diagnostic only','scratch':str(scratch),'phases':{},'requested_heap_mib':512,'aggregate_memory':'unproven','assets':{str(p):sha(p) for p in [COMPILER,cli/'joern',Path(env['SWIFTASTGEN_BIN'])]},'source_sha256':sha(source/'main.swift')}
for p in [r/'control-unqualified/main.swift',r/'inspect.sc',Path(__file__),ROOT/'scripts/swift_v2_process.py']:shutil.copyfile(p,out/p.name)
def command(argv,name,limit):
 result=run(list(map(str,argv)),out,name,limit,measure=True,env=env,cwd=scratch);w['phases'][name]=result
 if result['exit_status']!=0 or result['timed_out']:raise RuntimeError(name+' failed or timed out')
try:
 argv=[COMPILER,'-module-name',MODULE,'-swift-version','6','-Onone','-sdk',SDK,'-target','arm64-apple-macosx27.0.0','-module-cache-path',scratch/'cache',source/'main.swift','-typecheck']
 command(argv,'typecheck',60);(out/'build.log').write_text(shlex.join(list(map(str,argv)))+'\n')
 cpg=scratch/'cpg.bin';command([cli/'frontends/swiftsrc2cpg/bin/swiftsrc2cpg',source,'--build-log-path',out/'build.log','--output',cpg],'frontend',180)
 w['cpg_before_query_sha256']=sha(cpg)
 command([cli/'joern','--script',out/'inspect.sc','--param','cpgPath='+str(cpg),'--param','outputPath='+str(out/'graph.json')],'query',60)
except Exception as e:w['failure']=str(e)
finally:
 (out/'witness.json').write_text(json.dumps(w,indent=2)+'\n')
 (out/'manifest.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},indent=2)+'\n')
print(json.dumps({k:{'exit':v['exit_status'],'seconds':v['elapsed_seconds']} for k,v in w['phases'].items()}));print(w.get('failure','query completed'))
