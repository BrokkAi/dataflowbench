#!/usr/bin/env python3
"""Verify retained non-scored Swift follow-up controls, including failed attempts."""
import hashlib
import json
from pathlib import Path
from joern_swift import normalize

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    reflection = ROOT / 'evidence/swift-reflection-220'
    roots = [reflection / name for name in ('attempt-01', 'attempt-02', 'attempt-03', 'lifetime-attempt-01')]
    roots.append(ROOT / 'evidence/swift-result-220/attempt-01')
    for root in roots:
        manifest = read(root / 'manifest.json')
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p != root/'manifest.json'}
        require(set(manifest) == actual, f'manifest membership: {root}')
        for name, expected in manifest.items():
            require(hashlib.sha256((root/name).read_bytes()).hexdigest() == expected, f'digest: {root}/{name}')
    attempt = reflection / 'attempt-03'
    require(read(reflection/'pack-identity-readback.json')['packs'] == read(ROOT/'evidence/codeql-swift/activation-218/pack-tree-identities.json'), 'installed pack identity readback')
    cert = read(ROOT / 'adapters/codeql/swift/activation.json')
    witness = read(attempt / 'witness/digests.json')
    require(witness['compiler'] == cert['compiler_sha256'], 'compiler identity')
    require(witness['extractor'] == cert['extractor_sha256'], 'extractor identity')
    version = read(attempt / 'witness/cli.stdout') if (attempt/'witness/cli.stdout').exists() else read(attempt/'witness/codeql.stdout')
    require(version['version'] == cert['codeql_version'] and version['sha'] == cert['codeql_build'], 'CodeQL identity')
    # Lines belong to the retained combined input, not a source-text semantic matcher.
    expected_flow_lines = {'off': {24}, 'on': {24, 28, 32}}
    for mode, expected in expected_flow_lines.items():
        arm = attempt / 'codeql' / mode
        require(read(arm/'analyze.command.json')['exit_status'] == 0, 'CodeQL command failed')
        sarif = read(arm/'results.sarif.json')
        require(len(sarif['runs']) == 1, 'unexpected SARIF run count')
        run = sarif['runs'][0]
        require(all(i['executionSuccessful'] for i in run['invocations']), 'SARIF invocation failure')
        require(not any(n.get('level') == 'error' for i in run['invocations'] for n in i.get('toolExecutionNotifications', [])), 'SARIF error notification')
        results = run['results']
        observed = {r['locations'][0]['physicalLocation']['region']['startLine'] for r in results if r['ruleId'] == f'dfb/swift-reflection-{mode}'}
        require(observed == expected, f'CodeQL diagnostic flow set: {mode}')
        for line in [24, 26, 28, 30, 32, 34]:
            roles = set()
            for r in results:
                if r['ruleId'] == 'dfb/swift-reflection-endpoints' and r['locations'][0]['physicalLocation']['region']['startLine'] == line:
                    roles.update(r['message']['text'].splitlines())
            require(roles == {'source', 'sink'}, f'missing resolved endpoints: {line}')
    for label in ['direct-positive', 'direct-negative', 'carry', 'block', 'select-positive', 'select-negative']:
        for mode in ['off', 'on']:
            arm = attempt/'joern'/label/mode
            graph, config = read(arm/'graph.json'), read(arm/'config.json')
            outcome, diagnostics = normalize(graph, config)
            expected = 'not-reached' if label == 'direct-negative' or (label == 'block' and mode == 'on') else 'reached'
            require(outcome == expected and not diagnostics, f'Joern native diagnostic: {label}/{mode}')
            require(graph['analysis_completeness']['status'] == 'unproven', 'unqualified completeness')
    lifetime = read(reflection/'lifetime-attempt-01/summary.json')['rows']
    require(lifetime == {'direct': {'compile': 0, 'execute': 0}, 'retained': {'compile': 0, 'execute': -10}}, 'lifetime failure must remain visible')
    result = read(ROOT/'evidence/swift-result-220/attempt-01/summary.json')['rows']
    require(set(result) == {'positive-7', 'positive-19', 'negative-7', 'negative-19'}, 'Result control set')
    require(all(r == {'compile': 0, 'execute': 0} for r in result.values()), 'Result concrete control failure')
    print('Verified immutable non-scored attempts: reflection unqualified; Result concrete pair passes; no registry outcome or score')


if __name__ == '__main__':
    main()
