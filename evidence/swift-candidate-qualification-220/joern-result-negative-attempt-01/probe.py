#!/usr/bin/env python3
"""Independent non-scored Result controls; no fixture execution or native models."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile
from swift_population_v2 import ROOT, audit, sha
from joern_swift import MODULE, COMPILER, SDK, configuration, normalize
from swift_v2_process import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--joern', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--polarity', choices=['positive', 'negative'])
    selection.add_argument('--control-directory', type=Path)
    args = parser.parse_args()
    manifest, additions = audit()
    if args.control_directory:
        path = args.control_directory.resolve() / 'control.json'; case = json.loads(path.read_text())
        if case.get('scope') != 'non-scored-control' or case['fixture_files'] != ['main.swift'] or case['execution_budget'] != {'peak_memory_mb':512,'wall_clock_seconds':60}:
            parser.error('control must be non-scored with one Swift input and unchanged budgets')
        source_anchors = [{'file':'main.swift','line_hint':line} for line in case['expected_source_lines']]
        sink_anchors = [{'file':'main.swift','line_hint':line} for line in case['expected_sink_lines']]
    else:
        path, case = next((p, c) for p, c in additions if c['id'] == 'dfb-taint-swift-result-error-propagation-' + args.polarity)
        source_anchors, sink_anchors = case['source_anchors'], case['sink_anchors']
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='dfb-result-joern-')); source = scratch / MODULE; source.mkdir()
    shutil.copyfile(path, out / 'case.json')
    for name in case['fixture_files']:
        shutil.copyfile(path.parent / name, source / name); shutil.copyfile(path.parent / name, out / name)
    shutil.copyfile(__file__, out / 'probe.py'); shutil.copyfile(ROOT / 'scripts/swift_v2_process.py', out / 'process-runner.py')
    shutil.copyfile(ROOT / 'adapters/joern/swift/query.sc', out / 'query.sc')
    env = dict(os.environ, JAVA_HOME=str(args.java_home), SWIFTASTGEN_BIN=str(args.joern.parent / 'frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac'), _JAVA_OPTIONS='-Xmx512m')
    witness = {'status': 'unqualified', 'scope': 'Result language-extension feasibility only; not tool-native', 'case_id': case['id'], 'population': None if args.control_directory else manifest['population'], 'fixture_revision': None if args.control_directory else manifest['fixture_revision'], 'population_member': not bool(args.control_directory), 'retained_scratch': str(scratch), 'query_deadline_seconds': 60, 'extraction_deadline_seconds': 180, 'budget': case['execution_budget'], 'memory_compliance': 'unproven', 'phases': {}, 'assets': {str(COMPILER): sha(COMPILER), str(args.joern): sha(args.joern), env['SWIFTASTGEN_BIN']: sha(Path(env['SWIFTASTGEN_BIN']))}}
    def command(argv, name, timeout):
        result = run(list(map(str, argv)), out, name, timeout, measure=True, env=env, cwd=scratch)
        witness['phases'][name] = result
        if result['exit_status'] != 0 or result['timed_out']: raise RuntimeError(name + ' failed or timed out')
        return result
    try:
        compile_argv = [COMPILER, '-module-name', MODULE, '-swift-version', '6', '-Onone', '-sdk', SDK, '-target', 'arm64-apple-macosx27.0.0', '-module-cache-path', scratch / 'cache', source / 'main.swift', '-typecheck']
        command(compile_argv, 'typecheck', 60)
        (out / 'build.log').write_text(shlex.join(list(map(str, compile_argv))) + '\n')
        frontend = args.joern.parent / 'frontends/swiftsrc2cpg/bin/swiftsrc2cpg'; cpg = scratch / 'cpg.bin'
        command([frontend, source, '--build-log-path', out / 'build.log', '--output', cpg], 'frontend', 180)
        if not cpg.is_file() or cpg.stat().st_size == 0: raise RuntimeError('missing graph')
        config = configuration([MODULE + '.dfb_source:()->Swift.Int'], [MODULE + '.dfb_sink:(Swift.Int)->()'], source_anchors, sink_anchors)
        (out / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
        command([args.joern, '--script', out / 'query.sc', '--param', 'cpgPath=' + str(cpg), '--param', 'configPath=' + str(out / 'config.json'), '--param', 'outputPath=' + str(out / 'graph.json')], 'query', 60)
        witness['native_observation'] = normalize(json.loads((out / 'graph.json').read_text()), config)
    except Exception as error:
        witness['failure'] = str(error)
    finally:
        # Scratch is retained even after normal completion; no containment proof.
        (out / 'witness.json').write_text(json.dumps(witness, indent=2) + '\n')
        (out / 'manifest.json').write_text(json.dumps({str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}, indent=2) + '\n')
    print(json.dumps(witness.get('native_observation', {'failure': witness.get('failure')})), flush=True)


if __name__ == '__main__': main()
