#!/usr/bin/env python3
"""Execute one Swift case with retained commands and no shared mutable workspaces."""
import argparse
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tempfile
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv, directory, name, timeout, measure=False):
    start = time.time()
    monotonic_start = time.monotonic()
    with (directory / (name + '.stdout')).open('wb') as stdout, (directory / (name + '.stderr')).open('wb') as stderr:
        process = subprocess.Popen((["/usr/bin/time", "-l"] if measure else []) + argv, stdout=stdout, stderr=stderr, start_new_session=True)
        timed_out = False
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            status = process.wait()
    record = dict(argv=argv, measurement_wrapper=['/usr/bin/time','-l'] if measure else [], cwd=os.getcwd(), started_unix=start,
                  elapsed_seconds=time.monotonic()-monotonic_start, exit_status=status, timed_out=timed_out)
    if measure:
        match = re.search(r'^\s*(\d+)\s+maximum resident set size\s*$', (directory / (name + '.stderr')).read_text(), re.MULTILINE)
        record['time_maxrss_mb'] = (int(match.group(1)) + 1048575) // 1048576 if match else None
    (directory / (name + '.command.json')).write_text(json.dumps(record, indent=2)+'\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codeql', required=True)
    parser.add_argument('--packs', required=True)
    parser.add_argument('--case', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--query', required=True)
    parser.add_argument('--probe', required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = args.output / 'execution.json'
    summary = {'outcome': 'runner-error', 'diagnostics': [], 'phases': {}}
    scratch = Path(tempfile.mkdtemp(prefix='dfb-swift-218-'))
    try:
        case = json.loads(args.case.read_text())
        cert = json.loads(Path('adapters/codeql/swift/activation.json').read_text())
        compiler = subprocess.check_output(['xcrun','--find','swiftc'], text=True).strip()
        sdk = subprocess.check_output(['xcrun','--show-sdk-path'], text=True).strip()
        binary = str(Path(args.codeql).resolve())
        identities = {
            'compiler': compiler, 'compiler_sha256': sha(compiler),
            'extractor_sha256': sha(Path(binary).parent/'swift/tools/osx64/extractor.real'),
            'sdk': sdk,
            'execution_git_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'fixture_sha256': {name: sha(args.case.parent/name) for name in case['fixture_files']},
        }
        witnesses = [('compiler',['xcrun','swiftc','--version']),('sdk-version',['xcrun','--show-sdk-version']),
                     ('sdk-build',['xcrun','--show-sdk-build-version']),('xcode',['xcodebuild','-version']),
                     ('host',['sw_vers']),('architecture',['uname','-m']),('cli',[binary,'version','--format=json'])]
        for name, command in witnesses:
            if run(command,args.output,name,30)['exit_status'] != 0:
                raise ValueError('failed toolchain witness: '+name)
        identities['environment'] = {k: os.environ.get(k) for k in ('PATH','DEVELOPER_DIR','SDKROOT','MACOSX_DEPLOYMENT_TARGET')}
        (args.output/'provenance.json').write_text(json.dumps(identities,indent=2)+'\n')
        if identities['compiler_sha256'] != cert['compiler_sha256'] or identities['extractor_sha256'] != cert['extractor_sha256']:
            raise ValueError('compiler/extractor digest differs from activation')
        version = json.loads((args.output/'cli.stdout').read_text())
        if version['version'] != cert['codeql_version'] or version['sha'] != cert['codeql_build']:
            raise ValueError('CLI version/build differs from activation')
        for name, expected in [('sdk-version','27.0'),('sdk-build','26A425'),('architecture','arm64')]:
            if (args.output/(name+'.stdout')).read_text().strip() != expected:
                raise ValueError('toolchain pin mismatch: '+name)
        host=dict(line.split(':',1) for line in (args.output/'host.stdout').read_text().splitlines() if ':' in line)
        if host.get('ProductVersion','').strip() != '27.0' or host.get('BuildVersion','').strip() != '26A428':
            raise ValueError('local activation host pin mismatch')
        if (args.output/'xcode.stdout').read_text().strip() != 'Xcode 27.0\nBuild version 27A266a':
            raise ValueError('Xcode pin mismatch')
        expected_packs=json.loads(Path('evidence/codeql-swift/activation-218/pack-tree-identities.json').read_text())
        actual_packs={}
        for identity, expected in expected_packs.items():
            name,version=identity.split('@');pack=Path(args.packs)/'codeql'/name/version
            records=[[p.relative_to(pack).as_posix(),sha(p)] for p in sorted(pack.rglob('*')) if p.is_file()]
            actual={'file_count':len(records),'sha256_path_digest_records':hashlib.sha256(json.dumps(records,separators=(',',':')).encode()).hexdigest()}
            if actual != expected:raise ValueError('pack bytes differ from activation: '+identity)
            actual_packs[identity]=actual
        (args.output/'pack-identities.json').write_text(json.dumps(actual_packs,indent=2)+'\n')
        source = scratch/'source';source.mkdir()
        for name in case['fixture_files']:
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or path.suffix != '.swift':
                raise ValueError('unsafe or non-Swift fixture input')
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.case.parent/path,target)
        compile_argv=[compiler,'-swift-version','6','-Onone','-sdk',sdk,'-target','arm64-apple-macosx27.0.0','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(scratch/'cache')]+[str(source/name) for name in case['fixture_files']]+['-o',str(scratch/'fixture')]
        db=scratch/'db'
        create=run([binary,'database','create',str(db),'--language=swift','--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(compile_argv)],args.output,'database-create',180)
        summary['phases']['database-create']=create['elapsed_seconds']
        if create['timed_out']:
            summary['outcome']='inconclusive';raise ValueError('extraction wall-clock budget exhausted')
        if create['exit_status'] != 0:raise ValueError('Swift compilation/extraction failed')
        analysis=[binary,'database','analyze',str(db),args.query,args.probe,'--rerun','--format=sarif-latest','--output='+str(args.output.resolve()/'results.sarif.json'),'--additional-packs='+args.packs,'--threads=2','--ram='+str(case['execution_budget'].get('peak_memory_mb',512)),'--timeout='+str(case['execution_budget']['wall_clock_seconds'])]
        analyzed=run(analysis,args.output,'database-analyze',case['execution_budget']['wall_clock_seconds'],measure=True)
        summary['phases']['database-analyze']=analyzed['elapsed_seconds']
        if analyzed['timed_out']:
            summary['outcome']='inconclusive';raise ValueError('analysis wall-clock budget exhausted')
        if analyzed['exit_status'] != 0:raise ValueError('CodeQL query execution failed')
        summary['time_maxrss_mb']=analyzed['time_maxrss_mb']
        summary['peak_memory_mb']=None
        budget=case['execution_budget'].get('peak_memory_mb')
        if budget:
            summary['outcome']='inconclusive'
            raise ValueError(('analysis memory budget exceeded' if analyzed['time_maxrss_mb'] is not None and analyzed['time_maxrss_mb'] > budget else 'aggregate process-tree memory compliance unavailable')+': time maxrss '+str(analyzed['time_maxrss_mb'])+' MiB, case budget '+str(budget))
        summary['outcome']='analyzed'
    except Exception as error:
        summary['diagnostics'].append(str(error))
    finally:
        db=scratch/'db'
        if db.exists():
            for folder in ('log','diagnostic','results'):
                if (db/folder).exists():shutil.copytree(db/folder,args.output/folder)
            if (db/'codeql-database.yml').exists():shutil.copyfile(db/'codeql-database.yml',args.output/'codeql-database.yml')
        for log in args.output.rglob('*.log'):
            payload = log.read_bytes()
            compressed = gzip.compress(payload, mtime=0)
            assert gzip.decompress(compressed) == payload
            log.with_suffix('.log.txt.gz').write_bytes(compressed)
            log.unlink()
        result.write_text(json.dumps(summary,indent=2)+'\n')
        shutil.rmtree(scratch)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
