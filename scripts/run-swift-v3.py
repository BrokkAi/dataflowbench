#!/usr/bin/env python3
"""Serial full108 CodeQL execution; no fixture binaries run, no containment claim."""
import argparse,json,shutil,subprocess,shlex,time
from pathlib import Path
from swift_v3_runner import lane,observe,configuration
from swift_v3_reports import ROOT,read,sha,require,assemble
from swift_extraction_integrity import inspect_logs
from swift_persistence_coverage import assess_coverage,CoverageStatus
import swift_v2_process as process


def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['codeql','packs','native-packs','compiler','sdk','output']:parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--smoke',action='store_true',help='Execute only the five preregistered smoke cases; never emit a full report')
    parser.add_argument('--minimum-free-gib',type=int,default=30)
    args=parser.parse_args();pop,contract,cases,envelope=configuration(ROOT)
    if args.smoke:
        smoke=read(ROOT/'adapters/codeql/swift-v3/smoke-selection.json')
        require(len(smoke['case_ids'])==5 and len(set(smoke['case_ids']))==5 and set(smoke['case_ids'])<=set(cases),'smoke selection')
        cases={key:cases[key] for key in smoke['case_ids']}
        envelope=dict(envelope,scope='swift-v3-contract-bound-smoke',selected_case_ids=smoke['case_ids'])
    output=args.output.resolve();output.relative_to(ROOT/'reports/raw/swift-v3')
    require(args.minimum_free_gib>=30,'minimum disk reserve cannot be weakened')
    plan=read(ROOT/'adapters/codeql/swift-v3/runner-plan.json')
    for name,digest in plan['files'].items():require(sha(ROOT/name)==digest,'preregistered file '+name)
    subprocess.run(['git','diff','--quiet','HEAD','--',*plan['files']],cwd=ROOT,check=True)
    subprocess.run(['git','ls-files','--error-unmatch','--',*plan['files']],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
    pins=read(ROOT/'adapters/codeql/swift-opaque-v3/plan.json')
    require(sha(args.codeql)==pins['cli_sha256'] and sha(args.compiler)==pins['compiler_sha256'] and
            sha(args.codeql.parent/'swift/tools/osx64/extractor.real')==pins['extractor_sha256'] and
            sha(args.sdk/'SDKSettings.json')==pins['sdk_settings_sha256'],'runtime pin')
    for base,manifest in [(args.packs,read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')),
                          (args.native_packs,read(ROOT/'evidence/swift-persistence-completeness-v1/pack-manifest-v1.json')['files'])]:
        for row in manifest:require(sha(base/row['path'])==row['sha256'],'pack pin')
    require(shutil.disk_usage(ROOT).free>=args.minimum_free_gib*1024**3,'insufficient disk reserve before run')
    output.mkdir(parents=True,exist_ok=False)
    resolutions={}
    for selected_lane in ['kernel','calibration','modeling','opaque','native']:
        queryroot=ROOT/('adapters/codeql/swift-native-composed-v1' if selected_lane=='native' else 'adapters/codeql/swift-opaque-v3' if selected_lane=='opaque' else 'adapters/codeql/swift-v3/queries')
        query=queryroot/('flow.ql' if selected_lane in ['native','opaque'] else selected_lane+'-flow.ql')
        packs=args.native_packs if selected_lane=='native' else args.packs
        resolved=subprocess.run([str(args.codeql),'resolve','library-path','--query='+str(query),'--additional-packs='+str(packs),'--format=json'],capture_output=True,text=True,check=True,timeout=30)
        resolutions[selected_lane]=json.loads(resolved.stdout)
        expected=str(packs/'codeql/swift-all'/('6.8.4-dfb.9' if selected_lane=='native' else '6.8.4'))
        require(expected in resolutions[selected_lane]['libraryPath'],'resolved runtime lane mismatch')
    write(output/'library-paths.json',resolutions)
    selected={e['id']:e for e in pop['cases']};results=[];stop_reason=None
    write(output/'tool-lanes.json',plan['tool_lanes'])
    write(output/'run-plan.json',dict(envelope,paths={'repository':str(ROOT),'output':str(output),'cli':str(args.codeql),'compiler':str(args.compiler),'sdk':str(args.sdk),'packs':str(args.packs),'native_packs':str(args.native_packs)},runner_plan_sha256=sha(ROOT/'adapters/codeql/swift-v3/runner-plan.json'),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    for case_id,case in cases.items():
        directory=output/case_id;directory.mkdir();selected_lane=lane(case)
        raw=dict(envelope,case_id=case_id,outcome='inconclusive',diagnostics=['NotAttempted'],lane=selected_lane,
                 execution_status='not-attempted',aggregate_resource_qualification='unavailable',commands={})
        analysis_start=None
        try:
            if stop_reason:raise RuntimeError(stop_reason)
            if shutil.disk_usage(ROOT).free<args.minimum_free_gib*1024**3:stop_reason='DiskReserveReached';raise RuntimeError(stop_reason)
            source=directory/'source';source.mkdir();case_path=ROOT/selected[case_id]['path']
            for name in case['fixture_files']:shutil.copyfile(case_path.parent/name,source/name)
            db=directory/'database';commands=raw['commands']
            def run(argv,name,deadline):
                try:
                    record=process.run(argv,directory,name,deadline)
                except process.ProcessCleanupError:
                    if (directory/(name+'.command.json')).exists():commands[name]=read(directory/(name+'.command.json'))
                    raise
                commands[name]=record
                if record['timed_out']:raise TimeoutError('BudgetExhausted:'+name)
                require(record['exit_status']==0,'CommandFailed:'+name)
                return record
            compile_argv=[str(args.compiler),'-swift-version','6','-Onone','-sdk',str(args.sdk),'-target','arm64-apple-macosx26.5',
                          '-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(directory/'cache')]+[str(source/n) for n in case['fixture_files']]+['-o',str(directory/'never-executed')]
            raw['execution_status']='attempted'
            run([str(args.codeql),'database','create',str(db),'--language=swift','--source-root='+str(source),'--threads=2','--ram=2048','--command='+shlex.join(compile_argv)],'extract',150)
            run([str(args.codeql),'resolve','database','--format=json',str(db)],'resolve-database',30)
            resolved=read(directory/'resolve-database.stdout')
            require(resolved.get('languages')==['swift'] and Path(resolved['datasetFolder']).resolve()==(db/'db-swift').resolve(),'database identity')
            require('finalised: true' in (db/'codeql-database.yml').read_text(),'database finalization')
            require(inspect_logs(db/'log/swift/extractor')['ready_for_observation'],'ExtractionIncomplete')
            queryroot=ROOT/('adapters/codeql/swift-native-composed-v1' if selected_lane=='native' else 'adapters/codeql/swift-opaque-v3' if selected_lane=='opaque' else 'adapters/codeql/swift-v3/queries')
            packs=args.native_packs if selected_lane=='native' else args.packs
            names=['roles','flow']+(['coverage','scopes'] if case['template_id']=='dfb-template-native-persistence' else [])
            analysis_start=time.monotonic();rows={}
            for name in names:
                query=queryroot/((selected_lane+'-'+name+'.ql') if selected_lane not in ['native','opaque'] else name+'.ql')
                remaining=60-(time.monotonic()-analysis_start)
                if remaining<=0:raise TimeoutError('BudgetExhausted:analysis')
                run([str(args.codeql),'query','run',str(query),'--database='+str(db),'--output='+str(directory/(name+'.bqrs')),'--additional-packs='+str(packs),'--threads=2','--ram=2048','--timeout='+str(max(1,int(remaining)))],name,remaining)
                remaining=60-(time.monotonic()-analysis_start)
                if remaining<=0:raise TimeoutError('BudgetExhausted:analysis')
                run([str(args.codeql),'bqrs','decode',str(directory/(name+'.bqrs')),'--format=json','--output='+str(directory/(name+'.json'))],name+'-decode',remaining)
                rows[name]=read(directory/(name+'.json'))['#select']['tuples']
            raw['rows']=rows;raw['outcome'],raw['diagnostics']=observe(case,rows['roles'],rows['flow'],selected_lane)
            if 'coverage' in rows:
                coverage=assess_coverage(rows['coverage'],[r[0] for r in rows['scopes']]);raw['coverage_status']=coverage.status.value
                if coverage.status is CoverageStatus.INCOMPLETE:raw['outcome']='inconclusive';raw['diagnostics'].extend(coverage.reasons)
            raw['execution_status']='completed'
        except process.ProcessCleanupError as error:
            stop_reason='StoppedAfterUncertainCleanup';raw.update(outcome='runner-error',failure_kind='cleanup',diagnostics=['UncertainCleanup',str(error)])
        except TimeoutError as error:raw.update(outcome='inconclusive',failure_kind='timeout',diagnostics=[str(error)])
        except Exception as error:raw.update(outcome='runner-error' if raw['execution_status']=='attempted' else 'inconclusive',failure_kind='command' if str(error).startswith('CommandFailed:') else 'validation',diagnostics=[str(error)])
        finally:
            if analysis_start is not None:raw['analysis_elapsed_seconds']=time.monotonic()-analysis_start
            artifacts={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}
            write(directory/'artifacts.json',artifacts);raw['artifacts_sha256']=sha(directory/'artifacts.json')
            write(directory/'observation.json',raw)
            results.append({'case_id':case_id,'outcome':raw['outcome'],'raw_output':str((directory/'observation.json').relative_to(ROOT)),'raw_sha256':sha(directory/'observation.json')})
            write(output/'run.json',dict(envelope,results=results))
        print(case_id+': '+raw['outcome'],flush=True)
    from swift_v3_verify import verify
    try:
        verified=verify(ROOT,output,allow_smoke=args.smoke)
    except Exception as error:
        write(output/'report-status.json',{'status':'unreportable','reason':str(error),'raw_evidence_preserved':True,'scored_activation':False})
        raise
    write(output/('smoke-observations.json' if args.smoke else 'coverage-report.json'),verified)

if __name__=='__main__':main()
