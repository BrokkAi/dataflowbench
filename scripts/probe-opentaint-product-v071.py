#!/usr/bin/env python3
"""Execute shipped wrapper/native controls; retain evidence without assuming equivalence."""
import datetime,json,pathlib,shutil,subprocess,os
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'reports/raw/opentaint-product-v071';OUT.mkdir(parents=True,exist_ok=True)
WRAPPER='/private/tmp/opentaint-v0.4.6-inspect/base/opentaint'
t=json.loads((ROOT/'reports/releases/v0.7.1/identities.json').read_text())['tools']

def run(name,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();load=os.getloadavg()
 with open(OUT/(name+'-stdout.txt'),'wb') as o,open(OUT/(name+'-stderr.txt'),'wb') as e:code=subprocess.run([str(x) for x in args],cwd=ROOT,stdout=o,stderr=e).returncode
 with open(OUT/'commands.jsonl','a') as f:f.write(json.dumps({'id':name,'argv':[str(x) for x in args],'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':code,'load_before':load})+'\n')
 return code
run('wrapper-version',[WRAPPER,'--version']);run('wrapper-help',[WRAPPER,'--help']);run('scan-help',[WRAPPER,'scan','--help'])

def scan(name,source_files,packages,rules='builtin'):
 work=OUT/name;source=work/'source';classes=work/'classes';source.mkdir(parents=True);classes.mkdir()
 for path,text in source_files.items():p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 if run(name+'-compile',[t['javac']['path'],'-nowarn','-d',classes,*sorted(source.rglob('*.java'))])!=0:return
 model=work/'project.yaml';model.write_text('javaProjects:\n  - sourceRoot: '+str(source)+'\n    modules:\n      - moduleSourceRoot: '+str(source)+'\n        packages:\n'+''.join('          - '+x+'\n' for x in packages)+'        moduleClasses:\n          - '+str(classes)+'\n')
 run(name+'-product',[WRAPPER,'scan',source,'--project-model',model,'--entry-points','*','--ruleset',rules,'--output',work/'product','--log-file',work/'product.log'])

for case in sorted((ROOT/'cases/taint/java').glob('native-*')):
 scan(case.name,{'dataflowbench/taint/'+p.name:p.read_text() for p in case.glob('*.java')},['dataflowbench.taint'])

stubs={'jakarta/servlet/http/HttpServlet.java':'package jakarta.servlet.http; public abstract class HttpServlet { protected void doGet(HttpServletRequest req,HttpServletResponse resp) throws java.io.IOException {} }','jakarta/servlet/http/HttpServletRequest.java':'package jakarta.servlet.http; public interface HttpServletRequest { String getParameter(String name); }','jakarta/servlet/http/HttpServletResponse.java':'package jakarta.servlet.http; public interface HttpServletResponse {}'}
for variant,value in [('positive','request.getParameter("cmd")'),('negative','"fixed-command"')]:
 files=dict(stubs);files['dataflowbench/control/ControlServlet.java']='package dataflowbench.control; import jakarta.servlet.http.*; public class ControlServlet extends HttpServlet { @Override protected void doGet(HttpServletRequest request,HttpServletResponse response) throws java.io.IOException { String cmd = '+value+'; Runtime.getRuntime().exec(cmd); } }'
 scan('servlet-'+variant,files,['dataflowbench.control'])
(OUT/'scope.json').write_text(json.dumps({'kind':'fresh-shipped-product-activation','rule_source':'builtin from intact versioned distribution','entry_points':'* passed as an observed probe parameter, not assumed equivalent to jar selector','controls':['12 unchanged Java native fixtures','servlet-identity source to Runtime.exec positive','same servlet sink with constant negative'],'normalization':'No normalized outcome is generated here. Audit raw results/load evidence before any native decline or equivalence claim.','project_model':'precompiled javac fixture model; compilation and exact argv retained'},indent=2)+'\n')
