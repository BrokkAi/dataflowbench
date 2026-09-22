from pathlib import Path
import subprocess,time,json
root=Path('/Users/dave/.codex/worktrees/739a/dataflowbench');out=root/'evidence/codeql-swift/activation-218';cli='/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/codeql'
args=[cli,'bqrs','decode','/private/tmp/dfb-218-graph.bqrs','--format=json','--output='+str(out/'graph.json')];subprocess.run(args,check=True)
for attempt,prefix in [('attempt-02',''),('attempt-03','wrapped-'),('attempt-04','production-')]:
 for polarity in ['positive','negative']:
  db=Path('/private/tmp/dfb-codeql-swift-218-'+prefix+polarity+'/db')
  if not db.exists():continue
  import shutil
  dest=out/attempt/(polarity+'-database-logs')
  if not dest.exists():shutil.copytree(db/'log',dest)
  if (db/'codeql-database.yml').exists():shutil.copyfile(db/'codeql-database.yml',out/attempt/(polarity+'-database.yml'))
