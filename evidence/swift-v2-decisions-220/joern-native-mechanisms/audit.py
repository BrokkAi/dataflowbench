#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import zipfile

OUT = pathlib.Path('/private/tmp/dfb-220-joern-native-mechanisms')
ROOT = pathlib.Path('/Users/dave/.cache/dataflowbench-tools/joern-v4.0.628/joern-cli')
REPO = pathlib.Path('/Users/dave/.codex/worktrees/1ba0/dataflowbench')
VENDOR = REPO / 'evidence/swift-v2-vendor-result-220/joern-vendor'
UPSTREAM = REPO / 'evidence/joern-swift/activation-219/upstream-source'

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def run(argv, output):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    pathlib.Path(output).write_text('$ ' + ' '.join(argv) + '\n' + p.stdout + f'\n[exit {p.returncode}]\n')
    return p.returncode

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jars = sorted(ROOT.rglob('*.jar'))
    all_files = sorted(p for p in ROOT.rglob('*') if p.is_file())
    inventory = []
    for p in all_files:
        rel = p.relative_to(ROOT).as_posix()
        inventory.append({'path': rel, 'size_bytes': p.stat().st_size, 'sha256': sha256(p)})
    (OUT / 'pinned-file-inventory.json').write_text(json.dumps({
        'scope': str(ROOT), 'file_count': len(inventory), 'files': inventory
    }, indent=2) + '\n')
    (OUT / 'pinned-file-inventory.tsv').write_text('\n'.join(
        f"{x['path']}\t{x['size_bytes']}\t{x['sha256']}" for x in inventory
    ) + '\n')

    jar_records = []
    package_class_records = []
    resource_records = []
    keyword_hits = []
    for jar in jars:
        with zipfile.ZipFile(jar) as z:
            names = sorted(z.namelist())
        classes = [n for n in names if n.endswith('.class')]
        nonclasses = [n for n in names if not n.endswith(('.class', '.tasty')) and not n.endswith('/')]
        relevant = [n for n in names if any(k in n.lower() for k in (
            'semantic', 'model', 'source', 'sink', 'sanit', 'summary', 'entry', 'flow', 'query', 'swift', 'scan'
        ))]
        jar_records.append({
            'path': jar.relative_to(ROOT).as_posix(),
            'sha256': sha256(jar),
            'size_bytes': jar.stat().st_size,
            'member_count': len(names),
            'class_count': len(classes),
            'non_class_resource_count': len(nonclasses),
            'relevant_member_count': len(relevant),
        })
        if relevant:
            keyword_hits.append({'jar': jar.relative_to(ROOT).as_posix(), 'members': relevant})
        for n in classes:
            if n.startswith(('io/joern/', 'io/shiftleft/')):
                package_class_records.append({'jar': jar.relative_to(ROOT).as_posix(), 'member': n})
        for n in nonclasses:
            if n.startswith(('META-INF/services/', 'application.', 'reference.', 'reference/', 'io/joern/', 'io/shiftleft/')) or any(k in n.lower() for k in ('semantic', 'model', 'source', 'sink', 'sanit', 'summary', 'entry', 'query', 'swift')):
                resource_records.append({'jar': jar.relative_to(ROOT).as_posix(), 'member': n})
    (OUT / 'jar-inventory.json').write_text(json.dumps({'jars': jar_records}, indent=2) + '\n')
    (OUT / 'first-party-class-inventory.json').write_text(json.dumps({'classes': package_class_records}, indent=2) + '\n')
    (OUT / 'resource-inventory.json').write_text(json.dumps({'resources': resource_records}, indent=2) + '\n')
    (OUT / 'keyword-member-inventory.json').write_text(json.dumps({'hits': keyword_hits}, indent=2) + '\n')

    commands = [
        ['jar', 'tf', str(ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar')],
        ['jar', 'tf', str(ROOT / 'lib/io.joern.semanticcpg-4.0.628.jar')],
        ['jar', 'tf', str(ROOT / 'lib/io.joern.x2cpg-4.0.628.jar')],
        ['jar', 'tf', str(ROOT / 'lib/io.joern.joern-cli-4.0.628.jar')],
        ['jar', 'tf', str(ROOT / 'frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar')],
        ['unzip', '-Z1', str(ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar')],
        ['unzip', '-Z1', str(ROOT / 'frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar')],
    ]
    for i, argv in enumerate(commands, 1):
        run(argv, OUT / f'command-{i:02d}.txt')

    javap_specs = [
        ('DefaultSemantics', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.DefaultSemantics'),
        ('Semantics', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.semanticsloader.Semantics'),
        ('FullNameSemantics', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.semanticsloader.FullNameSemantics'),
        ('FullNameSemanticsParser', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.semanticsloader.FullNameSemanticsParser'),
        ('FlowSemantic', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.semanticsloader.FlowSemantic'),
        ('FlowPath', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.semanticsloader.FlowPath'),
        ('EngineContext', ROOT / 'lib/io.joern.dataflowengineoss-4.0.628.jar', 'io.joern.dataflowengineoss.queryengine.EngineContext'),
        ('SwiftSrc2Cpg', ROOT / 'frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar', 'io.joern.swiftsrc2cpg.SwiftSrc2Cpg'),
        ('SwiftTypeRecovery', ROOT / 'frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar', 'io.joern.x2cpg.frontendspecific.swiftsrc2cpg.SwiftTypeRecovery'),
    ]
    for name, jar, cls in javap_specs:
        run(['javap', '-classpath', str(jar), '-private', '-p', cls], OUT / f'javap-{name}.txt')
        run(['javap', '-classpath', str(jar), '-private', '-c', '-p', cls], OUT / f'javap-{name}-bytecode.txt')

    # Copy the exact locally retained upstream files with a digest map.
    copied = []
    for src in sorted(UPSTREAM.rglob('*')):
        if src.is_file():
            dst = OUT / 'upstream-source' / src.relative_to(UPSTREAM)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            copied.append({'source': str(src), 'path': str(dst.relative_to(OUT)), 'size_bytes': dst.stat().st_size, 'sha256': sha256(dst)})
    (OUT / 'upstream-source-manifest.json').write_text(json.dumps({'files': copied}, indent=2) + '\n')

    # Copy the prior vendor evidence used as the complementary query/catalog layer.
    vendor_files = []
    for src in sorted(VENDOR.iterdir()):
        if src.is_file():
            dst = OUT / 'prior-vendor-evidence' / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            vendor_files.append({'source': str(src), 'path': str(dst.relative_to(OUT)), 'size_bytes': dst.stat().st_size, 'sha256': sha256(dst)})
    (OUT / 'prior-vendor-evidence-manifest.json').write_text(json.dumps({'files': vendor_files}, indent=2) + '\n')

if __name__ == '__main__':
    main()
