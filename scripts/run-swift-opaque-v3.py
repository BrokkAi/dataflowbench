#!/usr/bin/env python3
"""Serial, preregistered exact-fixture observations; never executes fixture binaries."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from swift_opaque_v3_evidence import ROOT, read, sha, require

PLAN = ROOT/'adapters/codeql/swift-opaque-v3/plan.json'


def manifest(directory):
    (directory/'manifest.json').write_text(json.dumps({str(p.relative_to(directory)):sha(p)
        for p in sorted(directory.rglob('*')) if p.is_file() and p != directory/'manifest.json'}, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['output','codeql','packs','compiler','sdk']:
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args(); plan = read(PLAN)
    inputs = [str(PLAN.relative_to(ROOT))]
    for field in ['inputs','queries','runner_files']:
        for name, digest in plan[field].items():
            require(sha(ROOT/name) == digest, 'preregistered digest: '+name)
            inputs.append(name)
    subprocess.run(['git','ls-files','--error-unmatch','--',*inputs],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
    subprocess.run(['git','diff','--quiet','HEAD','--',*inputs],cwd=ROOT,check=True)
    require(sha(args.codeql) == plan['cli_sha256'], 'CLI identity')
    require(sha(args.codeql.parent/'swift/tools/osx64/extractor.real') == plan['extractor_sha256'], 'extractor identity')
    require(sha(args.compiler) == plan['compiler_sha256'], 'compiler identity')
    require(sha(args.sdk/'SDKSettings.json') == plan['sdk_settings_sha256'], 'SDK identity')
    pack_rows = read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')
    for row in pack_rows:
        require(sha(args.packs/row['path']) == row['sha256'], 'pack identity: '+row['path'])
    resolved = subprocess.run([str(args.codeql),'resolve','library-path','--query='+str(ROOT/'adapters/codeql/swift-opaque-v3/flow.ql'),
        '--additional-packs='+str(args.packs),'--format=json'],capture_output=True,text=True,check=True,timeout=30)
    require(str(args.packs/'codeql/swift-all/6.8.4') in json.loads(resolved.stdout)['libraryPath'], 'pack resolution')
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    (output/'library-path.json').write_text(resolved.stdout)
    population = read(ROOT/'populations/swift-opaque-v3.json')
    run = {'plan_sha256':sha(PLAN),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'scored_activation':False,'resource_qualification':'unavailable',
           'pack_files_verified':len(pack_rows),'cases':{e['id']:{'status':'not-attempted'} for e in population['cases']}}
    try:
        for entry in population['cases']:
            directory = output/entry['id']; directory.mkdir()
            case = read(ROOT/entry['case_path'])
            control = directory/'input'; control.mkdir()
            shutil.copyfile((ROOT/entry['case_path']).parent/'main.swift',control/'main.swift')
            (control/'control.json').write_text(json.dumps({'id':'control-'+case['id'], 'scope':'non-scored-control',
                'fixture_files':['main.swift'],'execution_budget':case['execution_budget']},indent=2)+'\n')
            argv = [sys.executable,str(ROOT/'scripts/probe-swift-v2-codeql.py'),'--output',str(directory/'probe'),
                    '--codeql',str(args.codeql),'--packs',str(args.packs),'--compiler',str(args.compiler),
                    '--sdk',str(args.sdk),'--target','arm64-apple-macosx26.5','--control-directory',str(control),
                    '--query-directory',str(ROOT/'adapters/codeql/swift-opaque-v3'),
                    '--probe-queries','roles','flow','identity']
            record = {'status':'failed','argv':argv}
            try:
                with (directory/'runner.stdout').open('w') as stdout, (directory/'runner.stderr').open('w') as stderr:
                    result = subprocess.run(argv,cwd=ROOT,stdout=stdout,stderr=stderr)
                record['exit_status'] = result.returncode
                witness = read(directory/'probe/witness.json')
                archive = Path(witness['retained_scratch'])/'db/src.zip'
                if archive.exists(): shutil.copyfile(archive,directory/'source.zip')
                require(result.returncode == 0 and not witness.get('probe_error') and not witness.get('cleanup_error'), 'probe failed')
                record['status'] = 'observed'
            except Exception as error:
                record['error'] = str(error)
            finally:
                run['cases'][entry['id']] = record
                manifest(directory)
                (output/'run.json').write_text(json.dumps(run,indent=2)+'\n')
            print(entry['id']+': '+record['status'],flush=True)
            # Uncertain descendant cleanup must stop serial work, not overlap it.
            if (directory/'probe/witness.json').exists() and read(directory/'probe/witness.json').get('cleanup_error'):
                break
    finally:
        (output/'run.json').write_text(json.dumps(run,indent=2)+'\n')
        manifest(output)

if __name__ == '__main__': main()
