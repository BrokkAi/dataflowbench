#!/usr/bin/env python3
"""Verify A40 provenance, exact addition coverage and profile separation."""
import argparse
import hashlib
import json
from pathlib import Path
from swift_population_v2 import ROOT, audit, require, sha


def read(path):
    return json.loads((ROOT / path).read_text())


def safe_path(value):
    require(isinstance(value, str), 'path must be a string')
    p = Path(value)
    require(bool(value) and p.as_posix() == value and not p.is_absolute()
            and all(part not in ('..', '.') for part in p.parts), 'unsafe path')
    require((ROOT / p).is_file(), 'missing input: ' + value)
    cursor = ROOT
    for part in p.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), 'symlink input: ' + value)
    return ROOT / p


def verify(configuration_only=False):
    population, cases = audit()
    by_id = {c['id']: c for _, c in cases}
    evidence = ROOT / 'evidence/swift-v2-decisions-220'
    manifest = read('evidence/swift-v2-decisions-220/manifest.json')
    actual = {str(p.relative_to(evidence)): sha(p) for p in sorted(evidence.rglob('*'))
              if p.is_file() and p != evidence / 'manifest.json'}
    require(actual == manifest, 'decision evidence file membership/digests changed')
    catalog = read('evidence/swift-v2-decisions-220/codeql-native-feasibility-attempt-01/catalog.json')['#select']['tuples']
    require(len(catalog) == 876 and sum(r[0] == 'source' for r in catalog) == 45, 'pinned CodeQL catalog census')
    for name in ('codeql-native-feasibility-attempt-01', 'codeql-entrypoint-feasibility-attempt-01'):
        witness = read('evidence/swift-v2-decisions-220/' + name + '/witness.json')
        require(witness['status'] == 'unqualified' and witness['unqualified_feasibility'], 'diagnostic promotion')
        require(witness['database_validation'] == 'finalized-swift-artifact; no containment claim', 'native diagnostic not finalized')
    vendor = read('evidence/swift-v2-decisions-220/joern-native-mechanisms/prior-vendor-evidence/structural-catalog.json')
    require(vendor['language_counts'].get('swift', 0) == 0 and vendor['language_counts'].get('Swift', 0) == 0, 'vendor Swift query census')
    for tool in ('codeql', 'joern'):
        base = f'adapters/{tool}/swift-v2/'
        partition = read(base + 'partition.json')
        require(partition['status'] == 'resolved' and partition['tool'] == tool, 'unresolved partition')
        for field in ('population', 'fixture_revision'):
            require(partition[field] == population[field], 'partition population mismatch')
        require(set(partition['cases']) == set(by_id), 'partition addition coverage')
        require(partition['budget'] == {'peak_memory_mb':512, 'wall_clock_seconds':60}, 'budget drift')
        for case_id, decision in partition['cases'].items():
            native = by_id[case_id]['model_profile'] == 'tool-native'
            require(decision['decision'] == ('unsupported' if native else 'execute'), 'A40 partition drift')
            require(bool(decision['reason']) and bool(decision['evidence']), 'missing rationale')
            for path in decision['evidence']:
                safe_path(path)
        activation = read(base + 'activation.json')
        require(activation['status'] == 'active' and activation['scope'] == 'swift-v2-additions', 'activation status')
        require(activation['executable_scope'] == 'result-language-extension'
                and activation['native_scope'] == 'committed-capability-decisions-only', 'activation scope')
        for field in ('query_sha256', 'evidence_sha256'):
            require(bool(activation[field]), 'empty activation digest map')
            for path, digest in activation[field].items():
                require(sha(safe_path(path)) == digest, 'activation digest: ' + path)
        files = read(base + 'configuration-files.json')
        require(isinstance(files, list) and len(files) == len(set(files)), 'configuration duplicates')
        bound = set(files) | {base+'configuration-files.json', 'scripts/run-swift-v2-additions.py', 'src/adapters/swift_v2.rs'}
        digest = hashlib.sha256()
        for path in sorted(bound, key=lambda value: Path(value).parts):
            digest.update(path.encode()); digest.update(safe_path(path).read_bytes())
        if configuration_only:
            continue
        raw_root = ROOT / f'reports/raw/{tool}-swift-v2-additions'
        raw_manifest = read(str(raw_root.relative_to(ROOT)) + '/manifest.json')
        observed = {str(p.relative_to(raw_root)):sha(p) for p in raw_root.rglob('*')
                    if p.is_file() and p != raw_root/'manifest.json'}
        require(raw_manifest == observed, 'raw attempt membership/digests changed')
        run = read(str(raw_root.relative_to(ROOT)) + '/run.json')
        require(run['configuration_hash'] == digest.hexdigest(), 'run/config mismatch')
        require(run['fixture_revision'] == population['fixture_revision'], 'run population mismatch')
        counts = []
        for suffix, profile, tier in [('native','tool-native','modeling'), ('result','benchmark-controlled','language-extension')]:
            report = read(f'reports/{tool}-swift-v2-{suffix}.json')
            require(report['configuration_hash'] == digest.hexdigest(), 'Python/Rust configuration hash mismatch')
            require(report['fixture_revision'] == population['fixture_revision'], 'report fixture identity')
            rows = report['results']; ids = [r['case_id'] for r in rows]
            expected = {cid for cid,c in by_id.items() if c['model_profile'] == profile and c['score_tier'] == tier}
            require(len(ids) == len(set(ids)) and set(ids) == expected, 'report exact profile coverage')
            for row in rows:
                raw = read(row['raw_output'])
                require(row['outcome'] in ('unsupported','inconclusive','runner-error'), 'uncertified correctness result')
                if suffix == 'native':
                    require(row['outcome'] == 'unsupported' and raw['analyzer_invoked'] is False, 'native scoped decision changed')
                else:
                    require(raw['budget'] == {'peak_memory_mb':512, 'wall_clock_seconds':60}, 'raw case budget')
                    require(raw['memory_compliance'] in ('unproven', 'exceeded'), 'uncertified memory promotion')
                    for name, phase in raw['phases'].items():
                        require(0 < phase['deadline_seconds'] <= 60, 'scored phase deadline drift')
                        require(phase['descendant_containment'] == 'unproven' and not phase['scratch_cleanup_authorized'], 'cleanup certainty promotion')
                    if 'analysis' in raw['phases']:
                        phase = raw['phases']['analysis']
                        if tool == 'codeql':
                            require('--ram=512' in phase['argv'] and '--timeout=60' in phase['argv'], 'CodeQL query budget')
                        else:
                            require(phase['environment']['_JAVA_OPTIONS'] == '-Xmx512m', 'Joern query budget')
                require(bool(row['diagnostics']) and bool(raw), 'missing retained typed evidence')
            counts.append(len(rows))
        require(counts == [12,2], '14 addition coverage')
    if not configuration_only:
        summary = read('evidence/swift-v2-execution-220/summary.json')
        require(summary['status'] == 'unfrozen-typed-outcomes' and summary['opaque_modeling_identities_unresolved'] == 2, 'scope promotion')
        expected_reports = {f'reports/{t}-swift-v2-{s}.json' for t in ('codeql','joern') for s in ('native','result')}
        require({r['path'] for r in summary['reports']} == expected_reports and len(summary['reports']) == 4, 'summary report coverage')
        for report in summary['reports']:
            require(sha(safe_path(report['path'])) == report['sha256'], 'summary report digest')
        rejected = ROOT/'reports/raw/codeql-swift-v2-additions-attempt-02-hash-rejected'
        retained = read(str(rejected.relative_to(ROOT))+'/manifest.json')
        require(retained == {str(p.relative_to(rejected)):sha(p) for p in rejected.rglob('*')
                            if p.is_file() and p != rejected/'manifest.json'}, 'rejected attempt changed')
    print('Swift v2 A40 configuration' + (' verified' if configuration_only else ' and 28 typed outcomes verified'))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configuration-only',action='store_true')
    verify(p.parse_args().configuration_only)
