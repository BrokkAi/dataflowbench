"""Strict native-identity and execution primitives for the independent Swift adapter."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
MODULE = 'DataFlowBenchTaintSwift'
COMPILER = Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc')
SDK = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1048576), b''):
            h.update(data)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def run(argv, out, cwd, env, timeout):
    out.mkdir()
    start = time.monotonic()
    timed_out = False
    with (out/'stdout.txt').open('wb') as stdout, (out/'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(['/usr/bin/time','-l']+list(map(str,argv)), cwd=cwd, env=env,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            status = process.wait()
    match = re.search(r'^\s*(\d+)\s+maximum resident set size\s*$', (out/'stderr.txt').read_text(), re.M)
    record = dict(argv=list(map(str,argv)), measurement_wrapper=['/usr/bin/time','-l'], cwd=str(cwd),
                  environment={k:env.get(k) for k in ['JAVA_HOME','SWIFTASTGEN_BIN','PATH','LANG','LC_ALL']},
                  elapsed_seconds=time.monotonic()-start, timeout_seconds=timeout, timed_out=timed_out,
                  exit_status=status, time_maxrss_mb=int(match.group(1))/1048576 if match else None)
    write(out/'command.json', record)
    return record


def environment(binary, java_home):
    return dict(os.environ, JAVA_HOME=str(Path(java_home).resolve()),
                SWIFTASTGEN_BIN=str(Path(binary).resolve().parent/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac'))


def extract(binary, source, out, scratch, env, deadline):
    sources = sorted(source.glob('*.swift'))
    argv = [str(COMPILER), '-module-name', MODULE, '-swift-version','6','-Onone',
            '-sdk',SDK,'-target','arm64-apple-macosx27.0.0','-module-cache-path',str(scratch/'cache')]
    argv += list(map(str,sources))+['-typecheck']
    compile_record = run(argv,out/'typecheck',scratch,env,max(0.001,deadline-time.monotonic()))
    if compile_record['timed_out'] or compile_record['exit_status']:
        return None, compile_record
    (out/'build.log').write_text(' '.join(argv)+'\n')
    cpg = scratch/'cpg.bin'
    frontend = Path(binary).resolve().parent/'frontends/swiftsrc2cpg/bin/swiftsrc2cpg'
    record = run([frontend,source,'--build-log-path',out/'build.log','--output',cpg],
                 out/'frontend',scratch,env,max(0.001,deadline-time.monotonic()))
    if record['timed_out'] or record['exit_status']:
        return None, record
    log = (out/'frontend/stdout.txt').read_text()
    counts = re.findall(r'Got (\d+) type map entries\.',log)
    if not counts or int(counts[-1]) < sum(bool(p.read_text().strip()) for p in sources) or not cpg.is_file() or cpg.stat().st_size == 0:
        raise ValueError('compiler-backed Swift import incomplete: missing type maps or graph')
    if re.search(r'\[(?:ERROR|WARN)\]',log):
        raise ValueError('Swift frontend emitted error/warning; completeness unproven')
    return cpg, record


def query(binary, cpg, config, out, scratch, env, deadline):
    write(out/'config.json',config)
    return run([binary,'--script',ROOT/'adapters/joern/swift/query.sc','--param','cpgPath='+str(cpg),
                '--param','configPath='+str(out/'config.json'),'--param','outputPath='+str(out/'graph.json')],
               out/'query',scratch,env,max(0.001,deadline-time.monotonic()))


def configuration(source_methods, sink_methods, source_anchors, sink_anchors, kind='call', semantics=None, source_enabled=True, sink_enabled=True):
    return dict(source_methods=source_methods,sink_methods=sink_methods,source_anchors=source_anchors,
                sink_anchors=sink_anchors,source_kind=kind,semantics=semantics or [],
                source_enabled=source_enabled,sink_enabled=sink_enabled)


def at(node, anchors):
    return any(node.get('file')==a['file'] and node.get('line')==a['line_hint'] for a in anchors)


def normalize(graph, config):
    """No names, source code, AST rewriting, or expected polarity supplies identity."""
    try:
        if graph['state']!='analyzed' or graph['complete'] is not True:
            raise ValueError('native query did not complete')
        if not any(m['language']=='SWIFTSRC' and 'dataflowOss' in m['overlays'] for m in graph['metadata']):
            raise ValueError('Swift frontend/dataflow overlay inactive')
        methods={m['id']:m for m in graph['methods']}
        if len(methods)!=len(graph['methods']):
            raise ValueError('duplicate native method identity')
        calls={c['node']['id']:c for c in graph['calls']}
        for role in ['source','sink']:
            ids=graph[role+'_method_ids']
            expected={i for i,m in methods.items() if not m['external'] and m['full_name'] in config[role+'_methods']}
            if not expected or set(ids)!=expected:
                raise ValueError(role+' exact declaration missing or inconsistent')
            observations=graph[role+'_observations']
            if not observations or not all(at(n,config[role+'_anchors']) for n in observations):
                raise ValueError(role+' native endpoint missing at exact anchor')
            for node in observations:
                identifier=node['id']
                if identifier in methods:
                    if identifier not in expected or methods[identifier]['node'] != node:
                        raise ValueError(role+' observation is wrong declaration')
                else:
                    call=calls.get(identifier)
                    if not call or call['node']!=node or len(call['callee_ids'])!=1 or call['callee_ids'][0] not in expected:
                        raise ValueError(role+' observation has missing/ambiguous/wrong native callee')
                    if call['method_full_name']!=methods[call['callee_ids'][0]]['full_name']:
                        raise ValueError(role+' call identity disagrees with native edge')
            anchored_declaration=any(at(methods[i]['node'],config[role+'_anchors']) for i in expected)
            eligible_calls=[c for c in calls.values() if len(c['callee_ids'])==1 and c['callee_ids'][0] in expected
                            and c['method_full_name']==methods[c['callee_ids'][0]]['full_name']
                            and (anchored_declaration or at(c['node'],config[role+'_anchors']))]
            if role=='source' and config['source_kind']=='parameter':
                required_nodes=[p['node'] for i in expected for p in methods[i]['parameters'] if p['index']==1]
            elif role=='source':
                required_nodes=[c['node'] for c in eligible_calls]
            else:
                required_nodes=[a['node'] for c in eligible_calls for a in c['arguments'] if a['index']==1]
            if {n['id'] for n in graph[role+'_nodes']} != {n['id'] for n in required_nodes}:
                raise ValueError(role+' native node inventory missing, extra, or inconsistent with anchors')
            for node in graph[role+'_nodes']:
                if role=='source' and config['source_kind']=='parameter':
                    valid=any(p['index']==1 and p['node']==node for i in expected for p in methods[i]['parameters'])
                elif role=='source':
                    call=calls.get(node['id'])
                    valid=bool(call and call['node']==node and len(call['callee_ids'])==1 and call['callee_ids'][0] in expected and call['method_full_name']==methods[call['callee_ids'][0]]['full_name'])
                else:
                    valid=any(len(c['callee_ids'])==1 and c['callee_ids'][0] in expected and c['method_full_name']==methods[c['callee_ids'][0]]['full_name'] and any(a['index']==1 and a['node']==node for a in c['arguments']) for c in calls.values())
                if not valid:
                    raise ValueError(role+' flow node has no exact native identity')
        if graph['semantics']!=config['semantics']:
            raise ValueError('model declaration mismatch')
        source_ids={n['id'] for n in graph['source_nodes']} if config['source_enabled'] else set()
        sink_ids={n['id'] for n in graph['sink_nodes']} if config['sink_enabled'] else set()
        for flow in graph['flows']:
            if not flow or flow[0]['id'] not in source_ids or flow[-1]['id'] not in sink_ids:
                raise ValueError('flow endpoints do not match exact native identities')
        return ('reached' if graph['flows'] else 'not-reached'), []
    except (KeyError,TypeError,ValueError) as error:
        return 'runner-error',[str(error)]
