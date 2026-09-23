from pathlib import Path
import json,subprocess,hashlib,zipfile
from datetime import datetime,timezone
repo=Path('/Users/dave/.codex/worktrees/1ba0/dataflowbench');metadata=repo/'evidence/swift-release-preparation-220/2026-09-23/pin-metadata/raw/joern_latest_alias.json';release=json.loads(metadata.read_text());assert release['tag_name']=='v4.0.633'
out=Path('/private/tmp/dfb-220-querydb-candidate');out.mkdir(exist_ok=False);(out/'release.json').write_bytes(metadata.read_bytes())
for name in ['querydb.json','querydb.zip']:
 a=next(a for a in release['assets'] if a['name']==name);cmd=['curl','--fail','--location','--retry','2','--max-time','180','--dump-header',str(out/(name+'.headers')),'--output',str(out/name),a['browser_download_url']];record={'asset':a,'command':cmd,'started_utc':datetime.now(timezone.utc).isoformat(),'source_metadata_sha256':hashlib.sha256(metadata.read_bytes()).hexdigest()}
 with (out/(name+'.stdout')).open('w') as so,(out/(name+'.stderr')).open('w') as se:r=subprocess.run(cmd,stdout=so,stderr=se)
 record['exit_status']=r.returncode;record['finished_utc']=datetime.now(timezone.utc).isoformat();(out/(name+'.acquisition.json')).write_text(json.dumps(record,indent=2)+'\n');assert r.returncode==0
 record['actual_sha256']=hashlib.sha256((out/name).read_bytes()).hexdigest();record['actual_bytes']=(out/name).stat().st_size;assert 'sha256:'+record['actual_sha256']==a['digest'];assert record['actual_bytes']==a['size'];(out/(name+'.acquisition.json')).write_text(json.dumps(record,indent=2)+'\n');print(name,record['actual_bytes'],record['actual_sha256'],flush=True)
with zipfile.ZipFile(out/'querydb.zip') as z:
 assert z.testzip() is None
 for info in z.infolist():assert not info.filename.startswith('/') and '..' not in Path(info.filename).parts
 z.extractall(out/'extracted')
