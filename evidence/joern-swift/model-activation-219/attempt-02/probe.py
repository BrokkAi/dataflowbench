#!/usr/bin/env python3
"""Independent model-on/off and near-miss probes; never reads registry cases."""
import argparse
import json
from pathlib import Path
import tempfile
import time
from joern_swift import ROOT, MODULE, configuration, environment, extract, query, write, sha, normalize


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--joern',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    binary=args.joern.resolve();env=environment(binary,args.java_home)
    models=json.loads((ROOT/'adapters/joern/swift/models.json').read_text())['semantics']
    (out/'query.sc').write_bytes((ROOT/'adapters/joern/swift/query.sc').read_bytes())
    (out/'probe.py').write_bytes(Path(__file__).read_bytes())
    (out/'joern_swift.py').write_bytes((ROOT/'scripts/joern_swift.py').read_bytes())
    header='''func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }
enum Clean {
 static func scrub(_ value: String) -> String { value }
 static func sanitize(_ value: String) -> String { value }
}
enum Config {
 static func fetchRemote() -> String { "remote" }
 static func fetchLocal() -> String { "local" }
}
enum Audit {
 static func record(_ value: String) { print("audit") }
 static func discard(_ value: String) { print("audit") }
}
enum Bridge {
 static func `pass`(_ value: String) -> String { "opaque" }
 static func hold(_ value: String) -> String { value }
}
'''
    controls=[('sanitizer','dfb_sink(Clean.scrub(dfb_source()))'),('sanitizer-sibling','dfb_sink(Clean.sanitize(dfb_source()))'),
              ('source','dfb_sink(Config.fetchRemote())'),('source-sibling','dfb_sink(Config.fetchLocal())'),
              ('sink','Audit.record(dfb_source())'),('sink-sibling','Audit.discard(dfb_source())'),
              ('summary','dfb_sink(Bridge.`pass`(dfb_source()))'),('summary-no-flow','dfb_sink(Bridge.hold(dfb_source()))')]
    controls += [('entrypoint',''),('entrypoint-sibling','')]
    results={}
    for label,expression in controls:
        case=out/label;case.mkdir();source=case/MODULE;source.mkdir()
        code=header+'func probe() { '+expression+' }\nprobe()\n'
        kind='call';sources=[MODULE+'.dfb_source:()->Swift.String'];sinks=[MODULE+'.dfb_sink:(Swift.String)->()']
        sa=[dict(file='main.swift',line_hint=19)];ta=sa
        if label.startswith('source'):
            sources=[MODULE+'.Config.fetchRemote:()->Swift.String']
            sa=[dict(file='main.swift',line_hint=8)]
        if label.startswith('sink'):
            sinks=[MODULE+'.Audit.record:(Swift.String)->()']
            ta=[dict(file='main.swift',line_hint=12)]
        if label.startswith('entrypoint'):
            code=header+'''final class Handler {
 func onDeclared(_ value: String) { dfb_sink('''+('value' if label=='entrypoint' else '"clean"')+''') }
 func onUndeclared(_ value: String) { dfb_sink('''+('"clean"' if label=='entrypoint' else 'value')+''') }
}
'''
            kind='parameter';sources=[MODULE+'.Handler.onDeclared:(Swift.String)->()']
            sa=[dict(file='main.swift',line_hint=20)];ta=[dict(file='main.swift',line_hint=20 if label=='entrypoint' else 21)]
        (source/'main.swift').write_text(code)
        with tempfile.TemporaryDirectory(prefix='dfb-joern-model219-') as temp:
            scratch=Path(temp);cpg,record=extract(binary,source,case,scratch,env,time.monotonic()+180)
            if cpg is None:raise RuntimeError('probe import failed: '+label)
            for mode in ['on','off']:
                arm=case/mode;arm.mkdir()
                selected_sources=sources;selected_sinks=sinks
                # Observation retains sibling declarations; activation enables only its role.
                enabled_source=not label.startswith('source') or mode=='on'
                enabled_sink=not label.startswith('sink') or mode=='on'
                if kind=='parameter':enabled_source=mode=='on'
                config=configuration(selected_sources,selected_sinks,sa,ta,kind,models if mode=='on' else [],enabled_source,enabled_sink)
                rec=query(binary,cpg,config,arm,scratch,env,time.monotonic()+180)
                result=normalize(json.loads((arm/'graph.json').read_text()),config) if (arm/'graph.json').exists() else ('runner-error',['no graph'])
                results[label+'-'+mode]=dict(exit_status=rec['exit_status'],outcome=result[0],diagnostics=result[1])
                print(label,mode,results[label+'-'+mode],flush=True)
    write(out/'summary.json',results)
    write(out/'manifest.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})

if __name__=='__main__':main()
