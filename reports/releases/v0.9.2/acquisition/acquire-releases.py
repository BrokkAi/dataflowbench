import concurrent.futures,hashlib,json,subprocess,tarfile,zipfile
from pathlib import Path
repo=Path('/Users/dave/.codex/worktrees/9f01/dataflowbench');dest=repo/'execution-state/v092/tools';meta=repo/'reports/releases/v0.9.2/acquisition'
selection=[('bifrost','bifrost-release.json','bifrost-v0.13.1-universal-apple-darwin.tar.gz','.sha256'),('codeql','codeql-cli-binaries-release.json','codeql-osx64.zip','.checksum.txt'),('joern','joern-release.json','joern-cli-macos-arm64.zip','.sha512')]
def acquire(row):
 key,record,name,suffix=row;folder=dest/key;folder.mkdir(exist_ok=True);assets=json.loads((meta/record).read_text())['assets'];asset=next(a for a in assets if a['name']==name);checksum=next(a for a in assets if a['name']==name+suffix)
 archive=folder/name
 if archive.exists():raise RuntimeError('refusing existing archive '+str(archive))
 subprocess.run(['curl','--fail','--location','--retry','3','--output',str(archive),asset['browser_download_url']],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 checksum_path=meta/(name+suffix);subprocess.run(['curl','--fail','--location','--output',str(checksum_path),checksum['browser_download_url']],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 algorithm='sha512' if suffix=='.sha512' else 'sha256';h=hashlib.new(algorithm)
 with archive.open('rb') as f:
  for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
 digest=h.hexdigest()
 if digest.lower() not in checksum_path.read_text().lower():raise RuntimeError('checksum mismatch '+name)
 if name.endswith('.zip'):
  subprocess.run(['unzip','-q',str(archive),'-d',str(folder)],check=True)
 else:
  subprocess.run(['tar','-xzf',str(archive),'-C',str(folder)],check=True)
 receipt={'asset':asset,'algorithm':algorithm,'verified_digest':digest,'archive':str(archive),'extracted_root':str(folder)};(meta/(key+'-acquisition.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(key+' acquired and publisher checksum verified',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(acquire,selection))
