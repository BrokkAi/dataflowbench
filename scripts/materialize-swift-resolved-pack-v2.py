import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

repo, base, output = map(Path, sys.argv[1:])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = json.loads((repo / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json').read_text())
patch_root = repo / 'adapters/codeql/swift-resolved-native-v1/patches'
spec = json.loads((patch_root / 'conversion-identity-v2.json').read_text())
patch = patch_root / 'conversion-identity-v2.patch'
assert sha(patch) == spec['patch_sha256']
assert not output.exists()
for row in rows:
    src = base / row['path']
    assert not src.is_symlink() and sha(src) == row['sha256'], row['path']
output.mkdir(parents=True)
for row in rows:
    dst = output / row['path']; dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base / row['path'], dst)
assert sha(output / spec['path']) == spec['original_sha256']
subprocess.run(['patch', '-p1', '--forward', '-i', str(patch.resolve())], cwd=output, check=True)
assert sha(output / spec['path']) == spec['patched_sha256']
old = output / 'codeql/swift-all/6.8.4'
new = old.with_name('6.8.4-dfb.2')
old.rename(new)
pack = new / 'qlpack.yml'
text = pack.read_text()
assert 'version: 6.8.4\n' in text and '  sha: 6e9f9e38390175c41b99070a423c875f450759ca\n' in text
text = text.replace('version: 6.8.4\n', 'version: 6.8.4-dfb.2\n').replace('buildMetadata:\n  sha: 6e9f9e38390175c41b99070a423c875f450759ca\n  cliVersion: 2.27.1\n','')
pack.write_text(text)
manifest = []
for row in rows:
    path = row['path']
    if path.startswith('codeql/swift-all/6.8.4/'):
        path = 'codeql/swift-all/6.8.4-dfb.2/' + path[len('codeql/swift-all/6.8.4/'):] 
    digest = sha(output / path)
    if row['path'] not in [spec['path'], 'codeql/swift-all/6.8.4/qlpack.yml']:
        assert digest == row['sha256'], path
    manifest.append({'path': path, 'sha256': digest, 'base_path': row['path'], 'base_sha256': row['sha256']})
actual = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}
assert actual == {r['path'] for r in manifest}
(output.parent / (output.name + '.manifest.json')).write_text(json.dumps({'scope':'adapter-patched-library-not-vendor-native','base_manifest_sha256':sha(repo / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json'),'patch_sha256':sha(patch),'files':manifest},indent=2)+'\n')
print('Verified isolated adapter library:',len(manifest),'files')
