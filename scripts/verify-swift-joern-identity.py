#!/usr/bin/env python3
"""Verify a concrete native-property identity blocker, not an unsupported partition."""
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/swift-joern-identity-220'


def read(path):
    return json.loads(path.read_text())


def field(nodes, line, name):
    by_id = {n['id']: n for n in nodes}
    matches = [n for n in nodes if n['label'] == 'CALL'
               and n['properties'].get('NAME') == '<operator>.fieldAccess'
               and n['properties'].get('LINE_NUMBER') == str(line)
               and any(by_id[c]['label'] == 'FIELD_IDENTIFIER' and
                       by_id[c]['properties'].get('CANONICAL_NAME') == name for c in n['ast'])]
    assert len(matches) == 1, (line, name)
    return matches[0]


def check_graph(graph, offset):
    nodes = graph['nodes']; by_id = {n['id']: n for n in nodes}
    rows = []
    for line, name, observed_type in [(23, 'environment', 'ANY' if offset == 0 else '__C.NSProcessInfo'),
                                      (24, 'arguments', 'ANY' if offset == 0 else 'Swift.CommandLine'),
                                      (27, 'arguments', '__C.NSTask')]:
        n = field(nodes, line + offset, name)
        assert n['ref'] == [], 'Observed missing declaration binding changed; re-evaluate blocker'
        assert n['properties']['TYPE_FULL_NAME'] == observed_type
        assert n['call'] and all(by_id[c]['properties'].get('FULL_NAME') == '<operator>.fieldAccess' for c in n['call'])
        rows.append({'line': line + offset, 'node_id': n['id'], 'property': name,
                     'type_full_name': observed_type, 'ref_ids': n['ref']})
    # Non-vacuity: same imported CPG has real member REF edges and a compiler-derived call identity.
    for line, name in [(34, 'environment'), (35, 'arguments')]:
        n = field(nodes, line + offset, name)
        assert n['ref'] and all(by_id[c]['label'] == 'MEMBER' for c in n['ref'])
    calls = [n for n in nodes if n['label'] == 'CALL' and n['properties'].get('NAME') == 'run'
             and n['properties'].get('LINE_NUMBER') == str(25 + offset)]
    assert len(calls) == 1 and calls[0]['call']
    expected = 'cobjc:(cs)NSTask(cm)launchedTaskWithExecutableURLargumentserrorterminationHandler'
    assert calls[0]['properties']['METHOD_FULL_NAME'] == expected
    assert all(by_id[c]['properties'].get('FULL_NAME') == expected for c in calls[0]['call'])
    return rows


def verify():
    for name, digest in read(EVIDENCE / 'manifest.json')['files'].items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == digest, name
    prior = read(ROOT / 'evidence/swift-candidate-qualification-220/joern-asset/selected-runtime-assets.json')
    assert read(EVIDENCE / 'verified-runtime-assets.json') == prior
    for name, offset in [('attempt-01', 0), ('attempt-02', 2)]:
        a = EVIDENCE / name
        for file, digest in read(a / 'manifest.json').items():
            assert hashlib.sha256((a / file).read_bytes()).hexdigest() == digest, file
        w = read(a / 'witness.json')
        assert w['status'] == 'unqualified' and w['aggregate_memory'] == 'unproven'
        assert w['requested_heap_mib'] == 512 and 'failure' not in w
        assert w['source_sha256'] == hashlib.sha256((a / 'main.swift').read_bytes()).hexdigest()
        for phase, deadline in [('typecheck', 60), ('frontend', 180), ('query', 60)]:
            command = w['phases'][phase]
            assert command == read(a / (phase + '.command.json'))
            assert command['exit_status'] == 0 and not command['timed_out']
            assert command['deadline_seconds'] == deadline and command['elapsed_seconds'] < deadline
            assert command['environment']['_JAVA_OPTIONS'] == '-Xmx512m'
        log = (a / 'frontend.stdout').read_text()
        assert 'Got 1 type map entries.' in log and not re.search(r'\[(?:ERROR|WARN)\s*\]', log)
        check_graph(read(a / 'graph.json'), offset)
    print('Verified qualified/unqualified native-property REF/type gaps with non-vacuous local-member and compiler-call controls. No adapter profile or unsupported partition admitted.')


if __name__ == '__main__':
    verify()
