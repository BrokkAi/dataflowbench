#!/usr/bin/env python3
"""Run a preregistered Swift fixture with immutable native evidence and strict budgets."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time
from joern_swift import ROOT, MODULE, COMPILER, environment, extract, query, normalize, configuration, sha, write, run


def config_for(case):
    template=case['template_id']; scalar='Swift.String' if case['score_tier']=='modeling' else 'Swift.Int'
    source=[MODULE+'.dfb_source:()->'+scalar];sink=[MODULE+'.dfb_sink:('+scalar+')->()'];kind='call'
    if template=='dfb-template-model-declared-source':source=[MODULE+'.Config.fetchRemote:()->Swift.String']
    if template=='dfb-template-model-declared-sink':sink=[MODULE+'.Audit.record:(Swift.String)->()']
    if template in ['dfb-template-model-entrypoint-parameter','dfb-template-model-entrypoint-selectivity']:
        method='onRequest' if template.endswith('-parameter') else 'onDeclared'
        source=[MODULE+'.Handler.'+method+':(Swift.String)->()'];kind='parameter'
    models=json.loads((ROOT/'adapters/joern/swift/models.json').read_text())['semantics']
    owner = ('Clean' if template in ['dfb-template-model-sanitizer-kill','dfb-template-model-sanitizer-selectivity']
             else 'Bridge' if template=='dfb-template-model-summary-through'
             else 'ThirdPartyBridge' if template=='dfb-template-modeled-external-summary' else None)
    semantics=[model for model in models if owner and model['method'].startswith(MODULE+'.'+owner+'.')]
    return configuration(source,sink,case['source_anchors'],case['sink_anchors'],kind,semantics)


def verify_pins(binary, java_home, output, scratch, env):
    cert=json.loads((ROOT/'adapters/joern/swift/activation.json').read_text())
    measured={}
    for asset in cert['assets']:
        base={'joern':binary.parent,'java':java_home,'compiler':COMPILER.parent}[asset['root']]
        path=base/asset['path'];actual=sha(path)
        if actual!=asset['sha256']:raise ValueError('activation pin mismatch: '+str(path))
        measured[str(path)]=actual
    write(output/'binary-identities.json',measured)
    for label,argv,expected in cert['environment_commands']:
        record=run(argv,output/label,scratch,env,15)
        if record['exit_status'] or record['timed_out'] or (output/label/'stdout.txt').read_text().strip()!=expected:
            raise ValueError('activation environment changed: '+label)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--joern',required=True,type=Path);parser.add_argument('--java-home',required=True,type=Path)
    parser.add_argument('--case',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();binary=args.joern.resolve();java_home=args.java_home.resolve();env=environment(binary,java_home)
    verifier=ROOT/'scripts/verify-joern-swift-activation.py'
    import runpy
    runpy.run_path(str(verifier))['verify']()
    import subprocess
    paths=['scripts/run-joern-swift-case.py','scripts/joern_swift.py','scripts/verify-joern-swift-activation.py','adapters/joern/swift/query.sc','adapters/joern/swift/models.json','adapters/joern/swift/partition.json','adapters/joern/swift/activation.json']
    if subprocess.run(['git','ls-files','--error-unmatch',*paths],cwd=ROOT,stdout=subprocess.DEVNULL).returncode or subprocess.run(['git','diff','--quiet','HEAD','--',*paths],cwd=ROOT).returncode:
        raise ValueError('Swift configuration and partition must be committed before execution')
    case=json.loads(args.case.read_text());summary=dict(outcome='runner-error',diagnostics=[],peak_memory_mb=None,phases={},native_evidence=None,engine_limits={'max_call_depth':4,'max_args_to_allow':1000,'max_output_args_expansion':1000,'exhaustion_observable':False})
    try:
        partition=json.loads((ROOT/'adapters/joern/swift/partition.json').read_text())
        cell=partition['templates'][case['template_id']]
        if partition['status']!='resolved' or cell['tier']!=case['score_tier'] or cell['profile']!=case['model_profile']:
            raise ValueError('case not in resolved preregistered partition')
        with tempfile.TemporaryDirectory(prefix='dfb-joern-swift219-') as temp:
            scratch=Path(temp)
            verify_pins(binary,java_home,out,scratch,env)
            if cell['decision']=='unsupported':
                summary.update(outcome='unsupported',diagnostics=[cell['reason']])
            elif cell['decision']=='execute':
                source=scratch/MODULE;source.mkdir()
                hashes={str(args.case):sha(args.case)}
                for name in case['fixture_files']:
                    path=Path(name)
                    if path.is_absolute() or '..' in path.parts or path.suffix!='.swift' or len(path.parts)!=1:
                        raise ValueError('unsafe/non-flat Swift fixture path')
                    original=args.case.parent/path
                    if original.is_symlink():raise ValueError('symlink fixture input')
                    shutil.copyfile(original,source/path);hashes[name]=sha(original)
                write(out/'fixture-hashes.json',hashes)
                # Joern's normative granularity is total: compilation/import/overlays/query all share 60s.
                deadline=time.monotonic()+case['execution_budget']['wall_clock_seconds']
                cpg,record=extract(binary,source,out,scratch,env,deadline)
                if cpg is None:
                    summary.update(outcome='inconclusive' if record['timed_out'] else 'runner-error',diagnostics=['Swift import/typecheck timeout' if record['timed_out'] else 'Swift import/typecheck failed'])
                else:
                    config=config_for(case);record=query(binary,cpg,config,out,scratch,env,deadline)
                    if record['timed_out']:
                        summary.update(outcome='inconclusive',diagnostics=['total Swift analysis wall-clock budget exhausted'])
                    elif record['exit_status'] or not (out/'graph.json').is_file():
                        summary['diagnostics']=['native Swift query failed or output missing']
                    else:
                        graph=json.loads((out/'graph.json').read_text());outcome,diagnostics=normalize(graph,config)
                        present={m['full_name'] for m in graph.get('methods',[]) if not m['external']}
                        if any(model['method'] not in present for model in config['semantics']):
                            outcome,diagnostics='runner-error',['required native model declaration did not bind']
                        summary.update(outcome=outcome,diagnostics=diagnostics,native_evidence='graph.json',native_outcome=outcome)
                        if outcome in ['reached','not-reached']:
                            memory=case['execution_budget'].get('peak_memory_mb')
                            commands=[json.loads(p.read_text()) for p in out.glob('*/command.json') if p.parent.name in ['typecheck','frontend','query']]
                            readings=[c['time_maxrss_mb'] for c in commands if c['time_maxrss_mb'] is not None]
                            summary['time_maxrss_mb']=max(readings) if readings else None
                            if memory:
                                breach=any(value>memory for value in readings)
                                summary.update(outcome='inconclusive',diagnostics=[('measured individual RSS exceeds fixture memory budget' if breach else 'aggregate process-tree memory compliance unavailable')+f': individual max {summary["time_maxrss_mb"]} MiB, budget {memory} MiB'])
            else:raise ValueError('unresolved partition decision')
    except Exception as error:
        summary['diagnostics'].append(str(error))
    if summary.get('native_outcome')=='not-reached':
        summary['diagnostics'].append('native engine uses k=4 call/field and 1000 argument expansion bounds; exhaustion is not exposed by reachableByFlows, so absence is not a completeness proof')
        if summary['outcome']=='not-reached':summary['outcome']='inconclusive'
    summary['phases']={'total':time.monotonic()-start}
    write(out/'execution.json',summary)
    write(out/'manifest.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})


if __name__=='__main__':main()
