#!/usr/bin/env python3
"""Non-scored compiler/CodeQL/Joern reflection comparison; immutable fresh attempts."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from joern_swift import ROOT, MODULE, environment, extract, query, configuration, normalize, sha, write

spec = importlib.util.spec_from_file_location('codeql_runner', ROOT/'scripts/run-codeql-swift-case.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
CONTROLS = {
 'direct-positive': 'dfb_sink(dfb_source())',
 'direct-negative': 'let value = dfb_source(); dfb_sink("clean")',
 'carry': 'dfb_sink(Opaque.carry(dfb_source()))',
 'block': 'dfb_sink(Opaque.block(dfb_source()))',
 'select-positive': 'dfb_sink(Opaque.select("clean", dfb_source()))',
 'select-negative': 'dfb_sink(Opaque.select(dfb_source(), "clean"))',
}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--codeql',type=Path,required=True)
 p.add_argument('--packs',type=Path,required=True);p.add_argument('--joern',type=Path,required=True)
 p.add_argument('--java-home',type=Path,required=True)
 args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
 probe=ROOT/'evidence/swift-reflection-220/probe'
 shutil.copytree(probe,out/'inputs');shutil.copyfile(__file__,out/'probe.py')
 write(out/'source-commit.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'scope':'non-scored; no registry or budget qualification'})
 result={}
 with tempfile.TemporaryDirectory(prefix='dfb-reflection220-') as temp:
  scratch=Path(temp);compiler=subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip()
  sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
  witness=out/'witness';witness.mkdir()
  for name,argv in [('swift',[compiler,'--version']),('sdk',['xcrun','--show-sdk-build-version']),('host',['sw_vers']),('codeql',[str(args.codeql),'version','--format=json']),('java',[str(args.java_home/'bin/java'),'-version'])]:
   runner.run(argv,witness,name,30)
  write(witness/'digests.json',{'compiler':sha(compiler),'extractor':sha(args.codeql.parent/'swift/tools/osx64/extractor.real'),'joern_launcher':sha(args.joern)})
  source=scratch/MODULE;source.mkdir();template=(probe/'template.swift').read_text()
  combined=template
  for i,(label,expression) in enumerate(CONTROLS.items()):combined+=f'func probe{i}() {{ {expression} }}\nprobe{i}()\n'
  combined += 'precondition(Opaque.carry(dfb_source()) == dfb_source())\nprecondition(Opaque.block(dfb_source()) == dfb_source())\nprecondition(Opaque.select("clean", dfb_source()) == dfb_source())\nprecondition(Opaque.select(dfb_source(), "clean") == "clean")\n'
  (source/'main.swift').write_text(combined);(out/'combined.swift').write_text(combined)
  compile_args=[compiler,'-swift-version','6','-Onone','-sdk',sdk,'-target','arm64-apple-macosx27.0.0','-module-name',MODULE,'-module-cache-path',str(scratch/'cache'),str(source/'main.swift'),'-o',str(scratch/'fixture')]
  concrete=out/'concrete';concrete.mkdir()
  for value in ['SOURCE','SECOND']:
   (source/'main.swift').write_text(combined.replace('"SOURCE"',json.dumps(value)))
   rec=runner.run(compile_args,concrete,'compile-'+value,180)
   if rec['exit_status']!=0:raise RuntimeError('concrete compile failed')
   executed=runner.run([str(scratch/'fixture')],concrete,'execute-'+value,10)
   result['concrete-'+value]=executed
   # Continue independent native diagnostics after failure, never certify fidelity.
  (source/'main.swift').write_text(combined)
  import shlex
  cq=out/'codeql';cq.mkdir();db=scratch/'db'
  rec=runner.run([str(args.codeql),'database','create',str(db),'--language=swift','--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(compile_args)],cq,'create',180)
  if rec['exit_status']!=0:raise RuntimeError('CodeQL extraction failed')
  for mode in ['off','on']:
   arm=cq/mode;arm.mkdir()
   rec=runner.run([str(args.codeql),'database','analyze',str(db),str(probe/'queries'/f'{mode}.ql'),str(probe/'queries/endpoints.ql'),'--rerun','--format=sarif-latest','--output='+str(arm/'results.sarif.json'),'--additional-packs='+str(args.packs),'--threads=2','--ram=512','--timeout=180'],arm,'analyze',180,measure=True)
   result['codeql-'+mode]=rec
  jenv=environment(args.joern,args.java_home)
  semantics=[{'method':MODULE+'.Opaque.carry:(Swift.String)->Swift.String','flows':[[1,-1]]},{'method':MODULE+'.Opaque.block:(Swift.String)->Swift.String','flows':[]},{'method':MODULE+'.Opaque.select:(Swift.String,Swift.String)->Swift.String','flows':[[2,-1]]}]
  for label,expr in CONTROLS.items():
   case=out/'joern'/label;case.mkdir(parents=True)
   src=case/MODULE;src.mkdir();code=template+'func probe() { '+expr+' }\nprobe()\n';(src/'main.swift').write_text(code)
   cpg,rec=extract(args.joern,src,case,scratch,jenv,time.monotonic()+180)
   if cpg is None:raise RuntimeError('Joern extraction failed: '+label)
   line=len(template.splitlines())+1
   for mode in ['off','on']:
    arm=case/mode;arm.mkdir()
    config=configuration([MODULE+'.dfb_source:()->Swift.String'],[MODULE+'.dfb_sink:(Swift.String)->()'],[{'file':'main.swift','line_hint':line}],[{'file':'main.swift','line_hint':line}],semantics=semantics if mode=='on' else [])
    rec=query(args.joern,cpg,config,arm,scratch,jenv,time.monotonic()+180)
    result['joern-'+label+'-'+mode]={'command':rec,'native':normalize(json.loads((arm/'graph.json').read_text()),config) if (arm/'graph.json').exists() else ['runner-error',['missing graph']]}
    print(label,mode,result['joern-'+label+'-'+mode]['native'],flush=True)
 write(out/'summary.json',result)
 write(out/'manifest.json',{str(path.relative_to(out)):sha(path) for path in sorted(out.rglob('*')) if path.is_file()})

if __name__=='__main__':main()
