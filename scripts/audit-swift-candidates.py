#!/usr/bin/env python3
"""Reconcile non-scored candidate controls without promoting active pins."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-candidate-qualification-220'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def endpoint_lines(rows, role=None):
    lines = []
    for row in rows:
        if role and row[1] != f'Benchmark {role} endpoint observed.':
            continue
        match = re.fullmatch(r'file://.+/main\.swift:(\d+):\d+:\d+:\d+', row[0]['label'])
        assert match, 'unrecognized decoded source location'
        lines.append(int(match.group(1)))
    return sorted(lines)


def summarize_attempt(path):
    witness = read(path / 'witness.json')
    phases = witness['phases']
    complete = bool(phases) and all(r['exit_status'] == 0 and not r['timed_out']
                                   and r['cleanup_status'] == 'tracked-processes-stopped'
                                   for r in phases.values())
    control = read(path / 'case.json')
    result = {'path': str(path.relative_to(ROOT)), 'case_id': witness['case_id'],
              'invocations_completed': complete,
              'failure': witness.get('probe_error', witness.get('failure')),
              'scored_qualification': False, 'memory_compliance': 'unproven',
              'phase_exit_status': {k: r['exit_status'] for k, r in phases.items()},
              'peak_individual_command_rss_mb': None}
    rss = []
    for stderr in path.glob('*.stderr'):
        rss += [int(n) / 1048576 for n in re.findall(r'^\s*(\d+)\s+maximum resident set size\s*$', stderr.read_text(), re.M)]
    if rss:
        result['peak_individual_command_rss_mb'] = round(max(rss), 3)
    result['individual_command_rss_exceeded_512_mb'] = bool(rss) and max(rss) > 512
    if path.name.startswith('codeql-'):
        complete = complete and all((path / (q + '.json')).is_file() for q in ('endpoints', 'flow'))
        if complete:
            endpoints = read(path / 'endpoints.json')['#select']['tuples']
            sources = endpoint_lines(endpoints, 'source')
            sinks = endpoint_lines(endpoints, 'sink')
            flows = endpoint_lines(read(path / 'flow.json')['#select']['tuples'])
            result.update(source_lines=sources, sink_lines=sinks, flow_sink_lines=flows,
                          exact_endpoints=(sources == sorted(control['expected_source_lines'])
                                           and sinks == sorted(control['expected_sink_lines'])))
            result['native_observation'] = 'flow' if flows else 'no-flow'
            if 'expected_flow_sink_lines' in control:
                result['identity_control_pass'] = result['exact_endpoints'] and flows == control['expected_flow_sink_lines']
    else:
        complete = complete and (path / 'graph.json').is_file() and 'native_observation' in witness
        if complete:
            graph = read(path / 'graph.json')
            result['native_observation'] = witness['native_observation']
            result['analysis_completeness'] = graph['analysis_completeness']
            result['query_completed'] = graph['query_completed']
            result['source_lines'] = sorted(n['line'] for n in graph['source_nodes'])
            result['sink_lines'] = sorted(n['line'] for n in graph['sink_nodes'])
            result['exact_endpoints'] = (result['source_lines'] == sorted(control['expected_source_lines'])
                                         and result['sink_lines'] == sorted(control['expected_sink_lines']))
            # The pinned query emits a flow ending at the sink argument node.
            result['flow_sink_lines'] = sorted(flow[-1]['line'] for flow in graph['flows'])
            if 'expected_flow_sink_lines' in control:
                result['identity_control_pass'] = result['exact_endpoints'] and result['flow_sink_lines'] == control['expected_flow_sink_lines']
    result['observations_complete'] = complete
    return result


def build():
    plan = read(BASE / 'plan.json')
    assert not plan['active_pin_mutation'] and not plan['release_population_approved']
    assert plan['opaque_choice'] == 'pending'
    for path, digest in plan['files'].items():
        assert sha(ROOT / path) == digest, path
    pins_path = ROOT / 'evidence/swift-release-preparation-220/2026-09-23/pin-metadata/next-pin-manifest.json'
    pins = {p['name']: p for p in read(pins_path)['targets']}
    for tool, pin in [('codeql', 'codeql-cli'), ('joern', 'joern')]:
        asset = read(BASE / f'{tool}-asset/acquisition.json')
        assert asset['metadata_sha256'] == sha(pins_path)
        assert 'sha256:' + asset['actual_sha256'] == pins[pin]['asset']['publisher_digest']
        assert asset['actual_bytes'] == pins[pin]['asset']['size']
    assert read(BASE / 'codeql-runtime/version.stdout')['version'] == '2.27.1'
    assert '4.0.633' in (BASE / 'joern-runtime/version-attempt-03.stdout').read_text()
    bifrost = read(BASE / 'bifrost-identity/verification.json')
    assert bifrost['artifact']['observed_sha256'] == pins['bifrost']['asset']['publisher_digest']
    assert bifrost['artifact']['observed_size_bytes'] == pins['bifrost']['asset']['size']
    assert bifrost['manifest']['sha256'] == sha(pins_path)
    assert (BASE / 'bifrost-identity/runtime-version.stdout').read_text().splitlines() == bifrost['runtime']['stdout']
    assert bifrost['runtime']['stdout'][0] == 'bifrost 0.11.5'
    assert not bifrost['release_qualification_claim']
    attempts = [summarize_attempt(p.parent) for p in sorted(BASE.glob('*-attempt-*/witness.json'))]
    assert len(attempts) == 7, 'retain failed first CodeQL attempt and six final controls'
    return {'schema_version': 1, 'scope': 'non-scored candidate compatibility observations',
            'active_pins_changed': False, 'release_qualified': False, 'opaque_choice': 'pending',
            'attempts': attempts,
            'limits': 'Individual-command RSS, phase deadlines and endpoint controls do not establish aggregate scored budget compliance or general analyzer completeness. No old unsupported decision is carried forward.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    value = json.dumps(build(), indent=2, sort_keys=True) + '\n'
    if args.write:
        (BASE / 'summary.json').write_text(value)
    else:
        assert (BASE / 'summary.json').read_text() == value, 'stale candidate summary'
        manifest = read(BASE / 'manifest.json')
        files = {str(p.relative_to(BASE)): sha(p) for p in BASE.rglob('*')
                 if p.is_file() and p != BASE / 'manifest.json'}
        assert files == manifest['files'], 'candidate evidence changed'
    print('Candidate controls reconciled; no active pins or release qualification changed')


if __name__ == '__main__':
    main()
