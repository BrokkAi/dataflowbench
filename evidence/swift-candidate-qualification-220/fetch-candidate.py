import hashlib,json,subprocess,sys,time,zipfile,posixpath
from pathlib import Path
from datetime import datetime,timezone
root=Path('/Users/dave/.codex/worktrees/1ba0/dataflowbench')
metadata=root/'evidence/swift-release-preparation-220/2026-09-23/pin-metadata/next-pin-manifest.json'
name=sys.argv[1];candidate=next(t for t in json.loads(metadata.read_text())['targets'] if t['name']==name);asset=candidate['asset']
out=Path('/private/tmp/dfb-220-candidate-assets')/name;out.mkdir(parents=True,exist_ok=False)
archive=out/asset['name'];cmd=['curl','--fail','--location','--retry','2','--max-time','900','--dump-header',str(out/'download.headers'),'--output',str(archive),asset['url']]
record={'scope':'non-scored candidate qualification only','source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'metadata_path':str(metadata.relative_to(root)),'metadata_sha256':hashlib.sha256(metadata.read_bytes()).hexdigest(),'candidate':candidate,'command':cmd,'started_utc':datetime.now(timezone.utc).isoformat()}
with (out/'download.stdout').open('w') as stdout,(out/'download.stderr').open('w') as stderr:
 r=subprocess.run(cmd,stdout=stdout,stderr=stderr)
record['exit_status']=r.returncode;record['finished_utc']=datetime.now(timezone.utc).isoformat()
(out/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n')
assert r.returncode==0,'download failed'
h=hashlib.sha256()
with archive.open('rb') as f:
 for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
record['actual_sha256']=h.hexdigest();record['actual_bytes']=archive.stat().st_size
record['publisher_digest_matches']='sha256:'+h.hexdigest()==asset['publisher_digest'];record['publisher_size_matches']=archive.stat().st_size==asset['size']
(out/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n')
assert record['publisher_digest_matches'] and record['publisher_size_matches'],'publisher mismatch; do not extract'
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  assert not info.filename.startswith('/') and '..' not in Path(info.filename).parts,'unsafe archive path'
  if (info.external_attr>>16)&0o170000==0o120000:
   target=z.read(info).decode();resolved=posixpath.normpath(posixpath.join(posixpath.dirname(info.filename),target));assert not target.startswith('/') and resolved!='..' and not resolved.startswith('../'),'unsafe symlink'
 record['archive_entries']=len(z.infolist());record['uncompressed_bytes']=sum(x.file_size for x in z.infolist())
 dest=out/'extracted';dest.mkdir();subprocess.run(['/usr/bin/ditto','-x','-k',str(archive),str(dest)],check=True)
record['extraction']='path/symlink checked; ditto successful';record['extracted_directory']=str(dest)
(out/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['actual_sha256','actual_bytes','uncompressed_bytes','extracted_directory']}),flush=True)
