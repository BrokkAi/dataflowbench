#!/usr/bin/env python3
"""Run composed native queries serially over immutable retained datasets."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from swift_native_composed import ROOT, PLAN, read, sha, require
import swift_v2_process as commands


def manifest(directory):
    (directory/'manifest.json').write_text(json.dumps({str(p.relative_to(directory)):sha(p)
        for p in sorted(directory.rglob('*')) if p.is_file() and p!=directory/'manifest.json'},indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ['output','codeql','packs']:parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args();plan=read(ROOT/PLAN);paths=[PLAN]
    for field in ['inputs','queries','runner_files']:
        for path,digest in plan[field].items():
            require(sha(ROOT/path)==digest,'preregistered input: '+path);paths.append(path)
    subprocess.run(['git','ls-files','--error-unmatch','--',*paths],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
    subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=ROOT,check=True)
    require(sha(args.codeql)==plan['cli_sha256'],'CLI pin')
    for row in read(ROOT/'evidence/swift-persistence-completeness-v1/pack-manifest-v1.json')['files']:
        require(sha(args.packs/row['path'])==row['sha256'],'patched pack identity')
    for selection in plan['cases'].values():
        db=Path(selection['database']);require(sha(db/'src.zip')==selection['source_archive_sha256'],'source archive pin')
        files={str(p.relative_to(db)) for p in (db/'db-swift').rglob('*') if p.is_file() and 'default/cache/' not in str(p)}
        require(files==set(selection['dataset_files']),'dataset closure')
        for name,digest in selection['dataset_files'].items():require(sha(db/name)==digest,'dataset identity')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    querydir=out/'queries';querydir.mkdir()
    for name in plan['queries']:shutil.copyfile(ROOT/name,querydir/Path(name).name)
    resolved=subprocess.run([str(args.codeql),'resolve','library-path','--query='+str(querydir/'flow.ql'),
                            '--additional-packs='+str(args.packs),'--format=json'],capture_output=True,text=True,check=True,timeout=30)
    require(str(args.packs/'codeql/swift-all/6.8.4-dfb.9') in json.loads(resolved.stdout)['libraryPath'],'patched runtime resolution')
    (out/'library-path.json').write_text(resolved.stdout)
    run={'plan_sha256':sha(ROOT/PLAN),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
         'scored_activation':False,'cli':str(args.codeql),'packs':str(args.packs),'output':str(out),
         'cases':{k:{'status':'not-attempted'} for k in plan['cases']}}
    try:
        for case_id,selection in plan['cases'].items():
            directory=out/case_id;directory.mkdir();record={'status':'failed'}
            shutil.copyfile(Path(selection['database'])/'src.zip',directory/'source.zip')
            names=['roles','flow']+(['coverage','scopes'] if 'native-persistence-' in case_id else [])
            try:
                for name in names:
                    bqrs=directory/(name+'.bqrs')
                    result=commands.run([str(args.codeql),'query','run',str(querydir/(name+'.ql')),
                        '--database='+selection['database'],'--output='+str(bqrs),'--additional-packs='+str(args.packs),
                        '--threads=2','--ram=2048','--timeout=60'],directory,name,60)
                    require(result['exit_status']==0 and not result['timed_out'],'query failed: '+name)
                    result=commands.run([str(args.codeql),'bqrs','decode',str(bqrs),'--format=json',
                        '--output='+str(directory/(name+'.json'))],directory,name+'-decode',60)
                    require(result['exit_status']==0 and not result['timed_out'],'decode failed: '+name)
                record['status']='observed'
            except commands.ProcessCleanupError:
                record['error']='uncertain cleanup';raise
            except Exception as error:
                record['error']=str(error)
            finally:
                run['cases'][case_id]=record;manifest(directory)
                (out/'run.json').write_text(json.dumps(run,indent=2)+'\n')
            print(case_id+': '+record['status'],flush=True)
    finally:
        (out/'run.json').write_text(json.dumps(run,indent=2)+'\n');manifest(out)

if __name__=='__main__':main()
