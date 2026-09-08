import pathlib,subprocess,json,datetime,hashlib,shutil,os,sys
root=pathlib.Path('/Users/dave/.codex/worktrees/653a/dataflowbench');mode=sys.argv[1];base=root/'reports/releases/v0.7.1/codeql-extraction-diagnosis'/mode;base.mkdir(exist_ok=True)
work=pathlib.Path('/private/tmp/dfb-v071-codeql-extraction-control');src=work/'source';src.mkdir(parents=True,exist_ok=True)
fixture=root/'cases/taint/c/alias-propagation-positive/alias_propagation_positive.c';shutil.copy2(fixture,src/fixture.name)
codeql='/opt/homebrew/bin/codeql';db=work/'database'
commands=[[codeql,'database','create',str(db),'--language=cpp','--source-root='+str(src),'--overwrite','--build-mode=none'],[codeql,'database','analyze',str(db),'adapters/codeql/cpp/queries/CKernel.ql','adapters/codeql/cpp/queries/CKernelEndpointProbe.ql','--format=sarif-latest','--output='+str(base/'result.sarif.json'),'--rerun']]
record={'mode':mode,'fixture':str(fixture),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'environment':{k:os.environ.get(k) for k in ['PATH','JAVA_HOME','TMPDIR']},'commands':[]}
for i,argv in enumerate(commands):
 row={'argv':argv,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with (base/f'{i}-stdout.txt').open('wb') as out,(base/f'{i}-stderr.txt').open('wb') as err:row['exit_code']=subprocess.run(argv,cwd=root,stdout=out,stderr=err).returncode
 row['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['commands'].append(row);(base/'commands.json').write_text(json.dumps(record,indent=2)+'\n')
 if row['exit_code']:break
if (db/'log').exists():shutil.copytree(db/'log',base/'database-log',dirs_exist_ok=True)
print(json.dumps(record),flush=True)
