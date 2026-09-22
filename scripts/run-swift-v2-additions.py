#!/usr/bin/env python3
"""Execute the committed A40 additions; Rust alone publishes normalized reports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from swift_population_v2 import ROOT, audit, require, sha
import swift_v2_scored_process as process
from joern_swift import configuration, normalize


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def safe_path(name):
    require(isinstance(name, str) and bool(name), 'invalid path')
    p = Path(name)
    require(not p.is_absolute() and p.as_posix() == name and '..' not in p.parts, 'unsafe path: ' + name)
    current = ROOT
    for part in p.parts:
        current /= part
        require(not current.is_symlink(), 'symlink input: ' + name)
    require(current.is_file(), 'missing input: ' + name)
    return current


def configuration_paths(tool):
    manifest = f'adapters/{tool}/swift-v2/configuration-files.json'
    paths = read(safe_path(manifest))
    require(isinstance(paths, list) and bool(paths), 'configuration must be a nonempty array')
    implicit = {manifest, 'scripts/run-swift-v2-additions.py', 'src/adapters/swift_v2.rs'}
    require(all(isinstance(p,str) for p in paths) and len(paths) == len(set(paths)), 'duplicate/invalid configuration path')
    require(not implicit.intersection(paths), 'implicit configuration path repeated')
    paths = sorted(set(paths) | implicit)
    for path in paths:
        safe_path(path)
    return paths


def configuration_hash(paths):
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda value: Path(value).parts):
        h.update(path.encode()); h.update(safe_path(path).read_bytes())
    return h.hexdigest()


def verify_configuration(tool, population, cases, check_git=True):
    paths = configuration_paths(tool)
    if check_git:
        subprocess.run(['git','ls-files','--error-unmatch','--',*paths],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
        subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=ROOT,check=True)
    base = ROOT / 'adapters' / tool / 'swift-v2'
    partition, activation = read(base/'partition.json'), read(base/'activation.json')
    require(partition['status'] == 'resolved' and partition['tool'] == tool, 'partition status/tool')
    require(partition['population'] == population['population'] and partition['fixture_revision'] == population['fixture_revision'], 'partition population')
    require(partition['budget'] == {'peak_memory_mb':512,'wall_clock_seconds':60}, 'partition budget')
    expected = {c['id'] for _,c in cases}
    require(len(expected) == 14 and set(partition['cases']) == expected, 'exact 14-cell partition required')
    require(activation['status'] == 'active' and activation['tool'] == tool and activation['scope'] == 'swift-v2-additions', 'activation scope')
    require(activation['executable_scope'] == 'result-language-extension' and activation['native_scope'] == 'committed-capability-decisions-only', 'activation promotion')
    for field in ('query_sha256','evidence_sha256'):
        require(bool(activation[field]), 'empty activation evidence')
        for path,digest in activation[field].items():
            require(path in paths and sha(safe_path(path)) == digest, 'activation digest: '+path)
    for _,case in cases:
        d=partition['cases'][case['id']]
        require(d['decision'] == ('unsupported' if case['model_profile']=='tool-native' else 'execute'), 'unregistered decision')
        require(bool(d['reason']) and bool(d['evidence']), 'empty decision evidence')
        for path in d['evidence']:
            require(path in paths, 'unbound decision evidence'); safe_path(path)
    return paths, partition, activation


def command(argv, out, name, timeout=60, env=None, cwd=None, measure=True, scope='scored analysis phase'):
    return process.run(list(map(str,argv)),out/name,name,timeout,env=env,cwd=cwd,measure=measure,deadline_scope=scope)


def checked(record, phase):
    if record['timed_out']:
        raise BudgetExceeded(phase+' wall-clock budget exhausted')
    require(record['exit_status']==0, phase+' invocation failed')
    require(record['cleanup_status']=='tracked-processes-stopped', phase+' cleanup uncertain')


class BudgetExceeded(RuntimeError):
    pass


def finalize_database(record, db, resolved):
    metadata=(db/'codeql-database.yml').read_text()
    require(record['exit_status']==0 and not record['timed_out'] and record['cleanup_status']=='tracked-processes-stopped'
            and len(re.findall(r'^finalised: true$',metadata,re.M))==1 and not re.search(r'^inProgress:',metadata,re.M)
            and resolved['languages']==['swift'] and Path(resolved['datasetFolder']).resolve()==(db/'db-swift').resolve()
            and (db/'db-swift').is_dir(), 'not a finalized Swift artifact')


def witness_tool(args, activation, out):
    for path,digest in activation['asset_sha256'].items():
        require(sha(Path(path))==digest,'pinned asset changed: '+path)
    if args.tool=='codeql':
        require(args.codeql and args.packs,'CodeQL paths required')
        require(sha(Path(args.codeql).parent/'swift/tools/osx64/extractor.real') == activation['asset_sha256']['/Users/dave/.cache/dataflowbench-tools/codeql-v2.27.0/codeql/swift/tools/osx64/extractor.real'],'selected extractor differs')
        actual={}
        for identity,expected in activation['pack_identities'].items():
            name,version=identity.split('@');pack=Path(args.packs)/'codeql'/name/version
            records=[[p.relative_to(pack).as_posix(),sha(p)] for p in sorted(pack.rglob('*')) if p.is_file()]
            value={'file_count':len(records),'sha256_path_digest_records':hashlib.sha256(json.dumps(records,separators=(',',':')).encode()).hexdigest()}
            require(value==expected,'pack identity changed: '+identity);actual[identity]=value
        write(out/'pack-identities.json',actual)
        r=command([args.codeql,'version','--format=json'],out,'version',measure=False,scope='run-level pin witness');checked(r,'version')
        value=read(out/'version/version.stdout');version,build=value['version'],value['sha']
    else:
        require(args.joern and args.java_home,'Joern paths required')
        r=command([args.joern,'--nocolors'],out,'version',env=joern_env(args),measure=False,scope='run-level pin witness');checked(r,'version')
        banner=(out/'version/version.stdout').read_text()+(out/'version/version.stderr').read_text()
        require('4.0.628' in banner,'Joern version absent');version='4.0.628';build='joern-cli:'+version
    require(version==activation['version'] and build==activation['build_identity'],'tool pin mismatch')
    if args.tool == 'joern':
        for suffix in ['lib/io.joern.dataflowengineoss-4.0.628.jar','frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.628.jar','frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac']:
            selected = Path(args.joern).parent / suffix
            pinned = next(v for k,v in activation['asset_sha256'].items() if k.endswith('/'+suffix))
            require(sha(selected)==pinned, 'selected Joern artifact differs: '+suffix)
        expected_java = next(v for k,v in activation['asset_sha256'].items() if k.endswith('/bin/java'))
        require(sha(Path(args.java_home)/'bin/java')==expected_java, 'selected Java differs')
    for name,argv in [('compiler',['xcrun','swiftc','--version']),('sdk',['xcrun','--show-sdk-version']),('xcode',['xcodebuild','-version']),('host',['sw_vers'])]:
        checked(command(argv,out,name,measure=False,scope='run-level environment witness'),name)
    require((out/'sdk/sdk.stdout').read_text().strip() == '27.0', 'SDK version differs')
    require((out/'xcode/xcode.stdout').read_text().strip() == 'Xcode 27.0\nBuild version 27A266a', 'Xcode pin differs')
    compiler = subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip()
    expected_compiler = next(v for k,v in activation['asset_sha256'].items() if k.endswith('/swiftc'))
    require(sha(Path(compiler)) == expected_compiler, 'selected compiler differs')
    write(out/'assets.json',activation['asset_sha256'])
    return version,build


def joern_env(args):
    return dict(os.environ,JAVA_HOME=str(args.java_home),SWIFTASTGEN_BIN=str(Path(args.joern).parent/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac'),_JAVA_OPTIONS='-Xmx512m')


def source_tree(path,case,scratch):
    source=scratch/'DataFlowBenchTaintSwift';source.mkdir()
    for name in case['fixture_files']:
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path.parent/name,target)
    return source


def compile_arguments(source,scratch,typecheck=False):
    compiler=subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip()
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    argv=[compiler,'-swift-version','6','-Onone','-sdk',sdk,'-target','arm64-apple-macosx27.0.0','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(scratch/'cache'),str(source/'main.swift')]
    return argv+(['-typecheck'] if typecheck else ['-o',str(scratch/'never-executed')])


def observe_sarif(sarif,case):
    runs=sarif.get('runs',[]);require(len(runs)==1,'missing SARIF run')
    run=runs[0];require(run.get('invocations') and all(i.get('executionSuccessful') is True for i in run['invocations']),'unsuccessful SARIF invocation')
    endpoints={'source':set(),'sink':set()};flows=[]
    for result in run.get('results',[]):
        locations=result.get('locations',[])
        require(bool(locations),'missing location')
        lines=[]
        for location in locations:
            physical=location['physicalLocation'];uri=physical['artifactLocation']['uri']
            require(uri=='main.swift' or uri.endswith('/main.swift'),'foreign finding file')
            lines.append(physical['region']['startLine'])
        rule=result.get('ruleId');message=result['message']['text']
        if rule=='dfb/swift-result-v2-endpoints':
            for part in message.splitlines():
                role=next((r for r in endpoints if part==f'Benchmark {r} endpoint observed.'),None)
                require(role is not None,'unknown endpoint role');endpoints[role].update(lines)
        elif rule=='dfb/swift-result-v2-flow':flows.extend(lines)
        else:raise ValueError('unexpected rule')
    for role in endpoints:
        require(endpoints[role]=={a['line_hint'] for a in case[role+'_anchors']},'exact endpoint mismatch')
    require(set(flows)<={a['line_hint'] for a in case['sink_anchors']},'flow not at exact sink')
    return {'flow_observed':bool(flows),'flow_sink_lines':flows,'endpoints':{k:sorted(v) for k,v in endpoints.items()}}


def execute_result(args,path,case,out):
    started=time.monotonic();scratch=Path(tempfile.mkdtemp(prefix='dfb-v2-scored-'+args.tool+'-'))
    execution={'case_id':case['id'],'outcome':'runner-error','diagnostics':[],'phases':{},'retained_scratch':str(scratch),'memory_compliance':'unproven','descendant_containment':'unproven','budget':case['execution_budget'],'fixture_sha256':{name:sha(path.parent/name) for name in case['fixture_files']}}
    phases=execution['phases'];db=None
    try:
        source=source_tree(path,case,scratch)
        if args.tool=='codeql':
            db=scratch/'db';argv=compile_arguments(source,scratch)
            r=command([args.codeql,'database','create',db,'--language=swift','--source-root='+str(source),'--threads=2','--ram=512','--command='+shlex.join(argv)],out,'extract',scope='scored extraction phase; 60-second operational cap')
            phases['extract']=r;checked(r,'extraction')
            r=command([args.codeql,'resolve','database','--format=json',db],out,'resolve',measure=False,scope='finalized-database metadata gate');phases['resolve']=r;checked(r,'database resolve')
            finalize_database(phases['extract'],db,read(out/'resolve/resolve.stdout'))
            base=ROOT/'adapters/codeql/swift-v2/queries';sarif=out/'results.sarif.json'
            r=command([args.codeql,'database','analyze',db,base/'flow.ql',base/'endpoints.ql','--rerun','--format=sarif-latest','--output='+str(sarif),'--additional-packs='+str(args.packs),'--threads=2','--ram=512','--timeout=60'],out,'analysis')
            phases['analysis']=r;checked(r,'analysis');execution['native_observation']=observe_sarif(read(sarif),case)
        else:
            env=joern_env(args);extract_start=time.monotonic();argv=compile_arguments(source,scratch,True)
            r=command(argv,out,'typecheck',env=env,scope='scored extraction phase; shared 60-second operational cap');phases['typecheck']=r;checked(r,'typecheck')
            build=out/'build.log';build.write_text(shlex.join(argv)+'\n');cpg=scratch/'cpg.bin'
            remaining=60-(time.monotonic()-extract_start)
            if remaining<=0:raise BudgetExceeded('extraction budget exhausted')
            r=command([Path(args.joern).parent/'frontends/swiftsrc2cpg/bin/swiftsrc2cpg',source,'--build-log-path',build,'--output',cpg],out,'frontend',timeout=remaining,env=env,scope='scored extraction phase; remaining shared 60-second cap');phases['frontend']=r;checked(r,'frontend')
            require(cpg.is_file() and cpg.stat().st_size>0,'missing CPG')
            config=configuration(['DataFlowBenchTaintSwift.dfb_source:()->Swift.Int'],['DataFlowBenchTaintSwift.dfb_sink:(Swift.Int)->()'],case['source_anchors'],case['sink_anchors'])
            write(out/'config.json',config)
            r=command([args.joern,'--script',ROOT/'adapters/joern/swift-v2/query.sc','--param','cpgPath='+str(cpg),'--param','configPath='+str(out/'config.json'),'--param','outputPath='+str(out/'graph.json')],out,'analysis',env=env,cwd=scratch)
            phases['analysis']=r;checked(r,'analysis');graph=read(out/'graph.json');observation,diagnostics=normalize(graph,config)
            execution['native_observation']={'outcome':observation,'diagnostics':diagnostics,'analysis_completeness':graph.get('analysis_completeness')}
            require(observation in ('reached','not-reached'),'native graph identity/flow evidence invalid: '+str(diagnostics))
        execution['outcome']='inconclusive'
        execution['diagnostics'].append('Aggregate process-tree memory compliance is unproven at the unchanged 512 MiB analysis budget; native observations are not certified correctness outcomes.')
        if args.tool=='joern':execution['diagnostics'].append('Native reachableByFlows does not prove semantic completeness or expose all exhaustion; missing flow is not a certified negative.')
    except BudgetExceeded as error:
        execution['outcome']='inconclusive';execution['diagnostics'].append(str(error))
    except Exception as error:
        execution['diagnostics'].append(str(error))
    finally:
        if db is not None and db.exists():
            for name in ['log','diagnostic']:
                if (db/name).exists():shutil.copytree(db/name,out/name)
            if (db/'codeql-database.yml').exists():shutil.copyfile(db/'codeql-database.yml',out/'codeql-database.yml')
        for name,r in phases.items():
            stderr=out/name/(name+'.stderr')
            match=re.search(r'^\s*(\d+)\s+maximum resident set size\s*$',stderr.read_text(errors='replace'),re.M) if stderr.exists() else None
            r['individual_maxrss_mb']=(int(match.group(1))+1048575)//1048576 if match else None
        analysis_rss = phases.get('analysis',{}).get('individual_maxrss_mb')
        if analysis_rss is not None and analysis_rss > case['execution_budget']['peak_memory_mb']:
            execution['memory_compliance'] = 'exceeded'
            execution['diagnostics'].append(f'Observed analysis process maximum RSS {analysis_rss} MiB exceeds the 512 MiB contract; aggregate compliance is therefore impossible for this attempt.')
        process.compress_logs(out)
        execution['duration_ms']=int((time.monotonic()-started)*1000)
        write(out/'execution.json',execution)
    return execution


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population',required=True,choices=['swift-synthetic-v2'])
    parser.add_argument('--tool',required=True,choices=['codeql','joern'])
    parser.add_argument('--output',type=Path,required=True)
    for name in ['codeql','packs','joern','java-home']:parser.add_argument('--'+name,type=Path)
    args=parser.parse_args();os.chdir(ROOT)
    population,cases=audit();paths,partition,activation=verify_configuration(args.tool,population,cases)
    expected=ROOT/'reports/raw'/f'{args.tool}-swift-v2-additions'
    require(args.output.resolve()==expected,'output must be exact versioned raw root')
    for suffix in ['native','result']:
        require(not (ROOT/f'reports/{args.tool}-swift-v2-{suffix}.json').exists(),'refusing report overwrite')
    out=expected;out.mkdir(parents=True,exist_ok=False)
    started=int(time.time());config_hash=configuration_hash(paths)
    version,build=witness_tool(args,activation,out)
    rows=[]
    for path,case in cases:
        directory=out/case['id'];directory.mkdir()
        shutil.copyfile(path,directory/'case.json')
        for name in case['fixture_files']:shutil.copyfile(path.parent/name,directory/name)
        decision=partition['cases'][case['id']]
        if decision['decision']=='unsupported':
            execution={'case_id':case['id'],'outcome':'unsupported','diagnostics':[decision['reason']],'duration_ms':0,'decision':decision,'analyzer_invoked':False}
            write(directory/'execution.json',execution)
        else:execution=execute_result(args,path,case,directory)
        rows.append({'case_id':case['id'],'model_profile':case['model_profile'],'score_tier':case['score_tier'],'outcome':execution['outcome'],'diagnostics':execution['diagnostics'],'duration_ms':execution['duration_ms'],'peak_memory_mb':None,'witness_checkpoints':[],'raw_output':str((directory/'execution.json').relative_to(ROOT))})
        print(case['id']+': '+execution['outcome'],flush=True)
    require(configuration_hash(paths)==config_hash,'configuration changed during run')
    audit()  # Fail closed if any population member changed while the run was active.
    write(out/'run.json',{'schema_version':1,'population':population['population'],'tool':args.tool,'activation_scope':activation['scope'],'executable_scope':activation['executable_scope'],'native_scope':activation['native_scope'],'tool_version':version,'tool_build_identity':build,'configuration_hash':config_hash,'fixture_revision':population['fixture_revision'],'started_at_unix_seconds':started,'ended_at_unix_seconds':int(time.time()),'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'results':rows})
    write(out/'manifest.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})


if __name__=='__main__':main()
