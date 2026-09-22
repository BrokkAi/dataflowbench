#!/usr/bin/env python3
"""Retain independent Swift activation attempts; never writes scored reports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import time


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(argv, directory, cwd, env, timeout):
    directory.mkdir()
    start = time.monotonic()
    timed_out = False
    with (directory / 'stdout.txt').open('wb') as stdout, (directory / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait()
    record = dict(argv=argv, cwd=str(cwd), exit_code=code, timed_out=timed_out,
                  elapsed_seconds=time.monotonic()-start, operational_timeout_seconds=timeout,
                  environment={key: env.get(key) for key in ['JAVA_HOME', 'SWIFTASTGEN_BIN', 'PATH', 'LANG', 'LC_ALL']})
    (directory / 'command.json').write_text(json.dumps(record, indent=2)+'\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--joern', required=True, type=Path)
    parser.add_argument('--java-home', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--compiler-backed', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    binary = args.joern.resolve()
    dist = binary.parent
    java_home = args.java_home.resolve()
    env = dict(os.environ, JAVA_HOME=str(java_home), SWIFTASTGEN_BIN=str(dist/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac'))
    script = root / 'adapters/joern/swift/inspect.sc'
    (out / 'inspect.sc').write_bytes(script.read_bytes())
    (out / 'probe.py').write_bytes(Path(__file__).read_bytes())
    paths = [binary, dist/'bin/repl-bridge', dist/'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac', java_home/'bin/java', script, Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc')]
    paths += sorted((dist/'frontends/swiftsrc2cpg/lib').glob('*.jar'))
    paths += sorted((dist/'lib').glob('*.jar'))
    archive = dist.parent/'joern-cli-macos-arm64.zip'
    if archive.is_file():
        paths.append(archive)
    (out/'identity.json').write_text(json.dumps(dict(host=platform.platform(), machine=platform.machine(),
        files={str(p):digest(p) for p in paths}),indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='dfb-joern-swift-activation-') as scratch:
        scratch = Path(scratch)
        for name, argv in [('java', [str(java_home/'bin/java'), '-version']),
                           ('joern', [str(binary), '--help']),
                           ('astgen', [str(paths[2]), '--version']),
                           ('architecture', ['/usr/bin/file', str(paths[2]), str(java_home/'bin/java')]),
                           ('swift', ['/usr/bin/xcrun', 'swiftc', '--version']),
                           ('xcode', ['/usr/bin/xcodebuild', '-version']),
                           ('sdk', ['/usr/bin/xcrun', '--show-sdk-version']),
                           ('sdk-path', ['/usr/bin/xcrun', '--show-sdk-path']),
                           ('sdk-build', ['/usr/bin/xcrun', '--show-sdk-build-version']),
                           ('os', ['/usr/bin/sw_vers'])]:
            run(argv, out/name, scratch, env, 90)
        sdk = (out/'sdk-path/stdout.txt').read_text().strip()
        for variant in ['plain', 'decoy']:
            for polarity in ['positive', 'negative']:
                label = variant+'-'+polarity
                case = out/label
                case.mkdir()
                controls = case/('DataFlowBenchTaintSwift' if args.compiler_backed else 'controls')
                controls.mkdir()
                member = '''struct Decoy {
 static func probeSource() -> Int { 9 }
 static func probeSink(_ value: Int) { print(value) }
}
''' if variant == 'decoy' else ''
                text = '''func probeSource() -> Int { 7 }
func probeSink(_ value: Int) { print(value) }
'''+member+'''func probe() {
 let tainted = probeSource()
 let clean = 0
 probeSink('''+('tainted' if polarity == 'positive' else 'clean')+''')
'''+(' Decoy.probeSink(Decoy.probeSource())\n' if variant == 'decoy' else '')+'''}
probe()
'''
                (controls/'main.swift').write_text(text)
                run(['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc', str(controls/'main.swift'), '-module-name', 'DataFlowBenchTaintSwift', '-swift-version', '6', '-Onone', '-target', 'arm64-apple-macosx27.0.0', '-sdk', sdk, '-module-cache-path', str(scratch/(label+'-module-cache')), '-o', str(scratch/label)], case/'compile', scratch, env, 90)
                if (scratch/label).is_file():
                    run([str(scratch/label)], case/'concrete-execution', scratch, env, 10)
                work = scratch/(label+'-workspace')
                work.mkdir()
                extra = []
                if args.compiler_backed:
                    compile_record = json.loads((case/'compile/command.json').read_text())
                    build_log = case/'build.log'
                    typecheck = compile_record['argv'][:]
                    output_index = typecheck.index('-o')
                    del typecheck[output_index:output_index+2]
                    typecheck.append('-typecheck')
                    run(typecheck, case/'typecheck', work, env, 90)
                    build_log.write_text(' '.join(typecheck)+'\n')
                    cpg = work/'cpg.bin'
                    run(['/usr/bin/time', '-l', str(dist/'frontends/swiftsrc2cpg/bin/swiftsrc2cpg'),
                         str(controls), '--build-log-path', str(build_log), '--output', str(cpg)],
                        case/'frontend', work, env, 180)
                    extra = ['--param', 'cpgPath='+str(cpg)]
                run(['/usr/bin/time', '-l', str(binary), '--script', str(out/'inspect.sc'),
                     '--param', 'inputPath='+str(controls), '--param', 'outputPath='+str(case/'graph.json')]+extra,
                    case/'joern', work, env, 180)
    files = {str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(files,indent=2)+'\n')


if __name__ == '__main__':
    main()
