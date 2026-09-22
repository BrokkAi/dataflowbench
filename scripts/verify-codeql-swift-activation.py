#!/usr/bin/env python3
"""Check retained, non-scored Swift activation evidence; never manufacture scores."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('evidence/codeql-swift/activation-218')
CONTROLS = {
    'positive': ('attempt-04/positive.sarif', 'attempt-04/positive-analysis.json', 1, 2),
    'negative': ('attempt-06/negative.sarif', 'attempt-06/negative-analysis.json', 0, 2),
    'decoy': ('attempt-05/positive.sarif', 'attempt-05/positive-analysis.json', 0, 0),
}
QUERY_PATHS = [Path('adapters/codeql/swift') / name for name in (
    'qlpack.yml', 'codeql-pack.lock.yml', 'queries/SwiftEndpoints.qll',
    'queries/SwiftKernel.ql', 'queries/SwiftKernelEndpointProbe.ql')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sarif(value, expected_flows, expected_endpoints):
    runs = value.get('runs', [])
    if len(runs) != 1:
        raise ValueError('activation requires exactly one SARIF run')
    run = runs[0]
    invocations = run.get('invocations', [])
    if not invocations or any(i.get('executionSuccessful') is not True for i in invocations):
        raise ValueError('missing or failed query execution')
    for invocation in invocations:
        for key in ('toolExecutionNotifications', 'toolConfigurationNotifications'):
            if any(n.get('level') == 'error' for n in invocation.get(key, [])):
                raise ValueError('query execution/configuration error')
    results = run.get('results', [])
    flows = [r for r in results if r.get('ruleId') == 'dfb/swift-kernel']
    endpoints = [r for r in results if r.get('ruleId') == 'dfb/swift-kernel-endpoint-probe']
    if len(results) != len(flows) + len(endpoints):
        raise ValueError('unexpected activation rule')
    if len(flows) != expected_flows or len(endpoints) != expected_endpoints:
        raise ValueError('positive/near-miss/identity-decoy control failed')
    if expected_endpoints:
        messages = {r.get('message', {}).get('text') for r in endpoints}
        if messages != {'Benchmark source endpoint observed.', 'Benchmark sink endpoint observed.'}:
            raise ValueError('both distinct endpoints must be observed')
    for result in results:
        locations = result.get('locations', [])
        if not locations or not locations[0].get('physicalLocation', {}).get('region', {}).get('startLine'):
            raise ValueError('missing concrete endpoint/finding location')


def verify(root=ROOT):
    hashes = {}
    for _, (sarif, command, flows, endpoints) in CONTROLS.items():
        sarif_path, command_path = EVIDENCE / sarif, EVIDENCE / command
        record = json.loads((root / command_path).read_text())
        if record.get('exit_status') != 0 or record.get('elapsed_seconds', -1) < 0:
            raise ValueError('activation command failed or timing missing')
        check_sarif(json.loads((root / sarif_path).read_text()), flows, endpoints)
        for path in (sarif_path, command_path):
            hashes[str(path)] = digest(root / path)
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-certificate', type=Path)
    args = parser.parse_args()
    evidence_hashes = verify()
    certificate = {
        'schema_version': 1, 'status': 'active', 'scope': 'core',
        'codeql_version': '2.27.0',
        'codeql_build': 'b47b3e59262c95aff4eeb84ac72d09e25a9c37e9',
        'swift_pack': '6.8.3',
        'query_sha256': {str(p): digest(ROOT / p) for p in QUERY_PATHS},
        'evidence_sha256': evidence_hashes,
        'compiler_sha256': 'cf81104bf554eef05e28a8bb5285c763f1323b4511b944d755d8bdd6cb8db717',
        'extractor_sha256': '680adbee37bdbfc5fe0a4b6d63c45bdae23fcf3bb2210530a7b751b58f319530',
    }
    if args.write_certificate:
        if args.write_certificate.exists():
            raise ValueError('refusing to overwrite existing activation certificate')
        args.write_certificate.write_text(json.dumps(certificate, indent=2) + '\n')
    print('Verified core activation: positive, near-miss, and identity decoy. No scored execution.')


if __name__ == '__main__':
    main()
