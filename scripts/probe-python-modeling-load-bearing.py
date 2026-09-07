#!/usr/bin/env python3
"""Refresh documented Python load-bearing controls without changing scored models."""
import datetime,json,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/raw/load-bearing-python-modeling'
OUT.mkdir(parents=True,exist_ok=True)
TOOLS=json.loads((ROOT/'reports/releases/v0.7.1/identities.json').read_text())['tools']
W=pathlib.Path(tempfile.mkdtemp(prefix='dfb-python-modeling-'))
failed=False

def run(name,args):
 global failed
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with open(OUT/(name+'-stdout.txt'),'wb') as o,open(OUT/(name+'-stderr.txt'),'wb') as e:
  code=subprocess.run([str(x) for x in args],cwd=W,stdout=o,stderr=e).returncode
 with open(OUT/'commands.jsonl','a') as f:f.write(json.dumps({'id':name,'argv':[str(x) for x in args],'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':code})+'\n')
 failed |= code!=0
 return code

def fixture(name,arm):
 p=W/arm;p.mkdir(parents=True)
 for f in (ROOT/'cases/taint/python'/name).glob('*.py'):shutil.copy2(f,p/f.name)
 return p

# S: independently remove the declared source or sink; keep undeclared siblings.
policy=(ROOT/'adapters/bifrost/policies/model-python.rqlp').read_text()
for role in ['source','sink']:
 for polarity in ['positive','negative']:
  for variant in ['with','without']:
   name=f'bifrost-declared-{role}-{polarity}-{variant}'
   work=fixture(f'model-declared-{role}-{polarity}',name)
   lines=policy.splitlines(keepends=True)
   if variant=='without':
    matched=False
    for i,line in enumerate(lines):
     if ':id declared-'+role in line:
      lines[i]=line[:line.index('('+role)]+line[line.rindex('])'):];matched=True;break
    assert matched
   artifact=OUT/(name+'.rqlp');artifact.write_text(''.join(lines))
   shutil.copy2(artifact,work/'policy.rqlp')
   run(name,[TOOLS['bifrost']['path'],'--root',work,'--policy-file','policy.rqlp','--evaluation-date','2026-08-11','--format','json','--fail-on','never','--output',OUT/(name+'.json')])

# P: the committed CodeQL removal query differs only in the propagator declaration.
work=fixture('model-opaque-propagator-positive','codeql-source');db=W/'codeql-db'
if run('codeql-extract',[TOOLS['codeql']['path'],'database','create',db,'--language=python','--source-root='+str(work),'--overwrite'])==0:
 for variant,query in [('with','PythonModeling.ql'),('without','PythonModelingProbe.ql')]:
  run('codeql-opaque-'+variant,[TOOLS['codeql']['path'],'database','analyze',db,ROOT/'adapters/codeql/python/queries'/query,'--format=sarif-latest','--output='+str(OUT/('codeql-opaque-'+variant+'.sarif.json')),'--rerun','--additional-packs=/Users/dave/.codeql/packages'])

# Z and the unsupported P/O rationale: declared and deleted NilSemantics.
sem=(ROOT/'adapters/joern/semantics/model-python.semantics').read_text()
needle='"clean.py:<module>.scrub"';assert any(x.startswith(needle) for x in sem.splitlines())
for name,case,remove in [('sanitizer-with','model-sanitizer-kill-negative',False),('sanitizer-without','model-sanitizer-kill-negative',True),('propagator-unmodeled','model-opaque-propagator-positive',False),('summary-unmodeled','model-summary-through-positive',False)]:
 work=fixture(case,'joern-'+name);sp=OUT/('joern-'+name+'.semantics');sp.write_text(''.join(x for x in sem.splitlines(keepends=True) if not(remove and x.startswith(needle))))
 args=[TOOLS['joern']['path'],'--script',ROOT/'adapters/joern/queries/modeling.sc']
 for key,value in [('inputPath',work),('language','PYTHONSRC'),('sourceName','dfb_source'),('sinkName','dfb_sink'),('sourceKind','call-return'),('semanticsPath',sp),('outputPath',OUT/('joern-'+name+'.json'))]:args+=['--param',str(key)+'='+str(value)]
 run('joern-'+name,args)
 if (W/'workspace').exists():shutil.rmtree(W/'workspace')

# S removal controls and Z undeclared-sibling behavior with/without safe-function option.
rule=(ROOT/'adapters/semgrep/rules/model-python.yaml').read_text()
for role,needle in [('source','- pattern: fetch_remote(...)'),('sink','- pattern: record(...)')]:
 for polarity in ['positive','negative']:
  for variant in ['with','without']:
   name=f'semgrep-declared-{role}-{polarity}-{variant}';work=fixture(f'model-declared-{role}-{polarity}',name);r=OUT/(name+'.yaml');r.write_text(''.join(x for x in rule.splitlines(keepends=True) if not(variant=='without' and needle in x)))
   run(name,[TOOLS['semgrep']['path'],'scan','--metrics=off','--oss-only','--disable-version-check','--no-git-ignore','--quiet','--json','--config',r,work])
for variant in ['safe-functions','default-functions']:
 name='semgrep-sanitizer-selectivity-'+variant;work=fixture('model-sanitizer-selectivity-positive',name);r=OUT/(name+'.yaml');r.write_text(rule if variant=='safe-functions' else rule.replace('taint_assume_safe_functions: true','taint_assume_safe_functions: false'))
 run(name,[TOOLS['semgrep']['path'],'scan','--metrics=off','--oss-only','--disable-version-check','--no-git-ignore','--quiet','--json','--config',r,work])
if failed:print('retained failed probe scratch:',W);raise SystemExit(1)
shutil.rmtree(W)
