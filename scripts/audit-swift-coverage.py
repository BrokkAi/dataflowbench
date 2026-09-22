#!/usr/bin/env python3
"""Join the full Swift applicability contract to immutable inputs and retained rows.

This is an implementation audit, not a freeze, score generator or scope approval.
Run with --check in CI; --write updates only this audit's derived artifacts.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = ('reached', 'not-reached', 'inconclusive', 'unsupported', 'runner-error')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root=ROOT):
    contract = root / 'docs/swift-kernel.md'
    families = {}
    section = ''
    for line in contract.read_text().splitlines():
        if line.startswith('## '):
            section = line[3:]
        match = re.match(r'\| `(dfb-template-[^`]+)` \| (.*?) \|(?: (.*?) \|)?$', line)
        if not match:
            continue
        identity, decision, construction = match.groups()
        require(identity not in families, f'duplicate contract identity: {identity}')
        status = decision.split(':')[0].split()[0]
        require(status in ('direct', 'adapted', 'inapplicable', 'deferred'), f'unknown decision: {decision}')
        families[identity] = dict(template_id=identity, family=section, decision=status,
                                  contract_detail='; '.join(x for x in (decision, construction) if x),
                                  scope_resolution='unresolved' if status == 'deferred' else 'contract-defined', cases=[])
    registry = {json.loads(p.read_text())['template_id'] for p in (root / 'cases').rglob('case.json')}
    require(set(families) == registry, f'contract/registry mismatch: missing={sorted(registry-set(families))}, extra={sorted(set(families)-registry)}')
    require(len(families) == 58, '58-identity contract changed; review coverage scope prospectively')
    population_path = root / 'populations/swift-synthetic-v1.json'
    population = json.loads(population_path.read_text())
    entries = {c['id']: c for c in population['cases']}
    require(len(entries) == len(population['cases']), 'duplicate population entry')
    actual = {p.relative_to(root).as_posix() for p in (root / 'cases/taint/swift').glob('*/case.json')}
    require({e['path'] for e in entries.values()} <= actual, 'v1 population file set missing; additional fixtures are audited separately by v2')
    cases = {}
    revision = hashlib.sha256()
    for entry in sorted(entries.values(), key=lambda e: e['path']):
        path = root / entry['path']
        case = json.loads(path.read_text())
        require(digest(path) == entry['sha256'], f'case digest: {entry["id"]}')
        for key in ('id', 'template_id', 'polarity', 'score_tier', 'track', 'model_profile'):
            require(case[key] == entry[key], f'population metadata {key}: {entry["id"]}')
        revision.update(entry['path'].encode()); revision.update(path.read_bytes())
        expected_fixtures = []
        for filename in case['fixture_files']:
            fixture = path.parent / filename
            revision.update(filename.encode()); revision.update(fixture.read_bytes())
            expected_fixtures.append(dict(path=fixture.relative_to(root).as_posix(), sha256=digest(fixture)))
        require(expected_fixtures == entry['fixture_digests'], f'fixture digest: {case["id"]}')
        require(case['execution_budget'] == {'peak_memory_mb': 512, 'wall_clock_seconds': 60}, f'budget changed: {case["id"]}')
        require(case['template_id'] in families, f'unmapped case: {case["id"]}')
        cases[case['id']] = case
        families[case['template_id']]['cases'].append(dict(id=case['id'], path=entry['path'], polarity=case['polarity'], score_tier=case['score_tier'], sha256=entry['sha256'], fixture_digests=expected_fixtures, results={}))
    require('sha256:' + revision.hexdigest() == population['fixture_revision'], 'population revision mismatch')
    case_rows = {c['id']: c for f in families.values() for c in f['cases']}
    for family in families.values():
        if family['decision'] in ('direct', 'adapted'):
            require(len(family['cases']) == 2 and {c['polarity'] for c in family['cases']} == {'positive', 'negative'}, f'unbalanced family: {family["template_id"]}')
        else:
            require(not family['cases'], f'undeclared implementation: {family["template_id"]}')
    reports = []
    for tool in ('codeql', 'joern'):
        observed = set()
        for tier, suffix in (('core', 'kernel'), ('modeling', 'modeling'), ('calibration', 'calibration')):
            relative = f'reports/{tool}-swift-{suffix}.json'
            report = json.loads((root / relative).read_text())
            require(report['fixture_revision'] == population['fixture_revision'], f'report revision: {relative}')
            expected = {key for key, case in cases.items() if case['score_tier'] == tier}
            ids = [row['case_id'] for row in report['results']]
            require(len(ids) == len(set(ids)) and set(ids) == expected, f'report membership: {relative}')
            counts = Counter()
            for row in report['results']:
                key = row['case_id']
                require(key not in observed, f'duplicate cross-tier result: {key}')
                observed.add(key)
                require(row['outcome'] in OUTCOMES, f'unknown outcome: {key}')
                raw_path = root / row['raw_output']
                raw = json.loads(raw_path.read_text())
                if raw['outcome'] != row['outcome']:
                    require(tool == 'codeql' and raw['outcome'] == 'inconclusive'
                            and row['outcome'] == 'runner-error'
                            and 'Swift dataflow source/sink missing at the declared file and line' in row['diagnostics'],
                            f'unexplained normalization transition: {key}')
                require(row['outcome'] not in ('reached', 'not-reached'), f'new qualified result requires coverage review: {key}')
                counts[row['outcome']] += 1
                case_rows[key]['results'][tool] = dict(report=relative, outcome=row['outcome'], raw_execution_outcome=raw['outcome'], diagnostics=row['diagnostics'], raw_output=row['raw_output'], raw_sha256=digest(raw_path))
            reports.append(dict(path=relative, sha256=digest(root / relative), tool=tool, tier=tier,
                                configuration_hash=report['configuration_hash'], outcomes={k: counts[k] for k in OUTCOMES}, assertions=len(ids)))
        require(observed == set(cases), f'incomplete {tool} participation')
    return dict(status='unfrozen-implementation-audit', epic_complete=False,
                contract=dict(path='docs/swift-kernel.md', sha256=digest(contract)),
                population=dict(path=population_path.relative_to(root).as_posix(), sha256=digest(population_path), fixture_revision=population['fixture_revision']),
                identity_counts=dict(sorted(Counter(f['decision'] for f in families.values()).items())),
                bifrost_swift='unsupported; no execution or result rows invented',
                reserved_tracks=['value-flow', 'typestate', 'witness', 'performance'],
                real_projects='separate prospective selection/review required; no new study',
                reports=reports, families=[families[key] for key in sorted(families)])


def markdown(data):
    lines = ['# Swift coverage reconciliation', '',
             'Generated by `python3 scripts/audit-swift-coverage.py --write`; checked in CI.', '',
             '**Unfrozen implementation audit.** This is not a release scorecard or acceptance of deferred scope. '
             'All 58 synthetic registry identities are reconciled below. The 45 implemented pairs contain 90 assertions; '
             'four identities are language-inapplicable and nine remain unresolved. #220 and #215 remain open.', '',
             'CodeQL and Joern execution records are independent. Analyzer language breadth is not fixture participation '
             'or qualified support. Bifrost Swift remains unsupported. Calibration is unscored. '
             'No correctness rate is defined from these outcomes; native paths are not qualified scores. '
             'Budgets remain 512 MiB / 60 seconds. Timing is descriptive, not performance certification.', '',
             '## Retained report coverage', '',
             '| Report | Assertions | Reached | Not reached | Inconclusive | Unsupported | Runner error |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for report in data['reports']:
        values = ' | '.join(str(report['outcomes'][key]) for key in OUTCOMES)
        lines.append(f'| [{report["path"]}](../{report["path"]}) | {report["assertions"]} | {values} |')
    lines += ['', 'The [machine-readable audit](../evidence/swift-coverage-220/coverage.json) binds report, '
              'case, fixture and raw-output hashes. CodeQL raw execution resource decisions and normalized endpoint errors remain separate fields; neither is rewritten. CI also replays each adapter’s deeper provenance/configuration audit. '
              'Original attempts, including Joern’s superseded completion fields, remain immutable.', '',
              '## Every synthetic identity', '',
              '| Template | Contract decision | Examples and retained outcomes |', '| --- | --- | --- |']
    for family in data['families']:
        examples = []
        for case in sorted(family['cases'], key=lambda c: c['polarity']):
            outcomes = ', '.join(f'{tool}: {row["outcome"]}' for tool, row in case['results'].items())
            examples.append(f'[{case["polarity"]}](../{case["path"]}) ({outcomes})')
        if not examples:
            examples = ['**Unresolved; acceptance required**' if family['decision'] == 'deferred' else 'Language-inapplicable under the contract']
        lines.append(f'| `{family["template_id"]}` | {family["decision"]} | {"; ".join(examples)} |')
    lines += ['', '## Unresolved scope and publication gates', '',
              'The [normative contract](swift-kernel.md) retains the exact missing constructions: '
              'opaque-propagator and propagator-position require a reviewed opacity amendment; '
              'all six native families require real API identities, safe near misses and pinned shipped-model inventory; '
              'the Result extension requires its own pair contract. None is an accepted epic exclusion. '
              'Implement them prospectively or record an explicit maintainer scope decision before closing the epic.', '',
              'Real-project selection/review stays separate and no new study is commissioned. '
              'Value-flow, typestate, witness and performance remain reserved.', '',
              'Publication requires the [normal next-release workflow](freeze.md): pin-currency review, '
              'compatible fixture revision for every freeze-bound report, merged evidence, a new validated freeze, '
              'generated scorecards with null correctness rates where no definitive outcomes exist, '
              'and tag/deployment verification. Existing release freezes and their generated artifacts remain unchanged. '
              'All-inconclusive evidence is publishable coverage once those gates pass; it is not a reason to fabricate scores.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = audit()
    artifacts = {'evidence/swift-coverage-220/coverage.json': json.dumps(data, indent=2, sort_keys=True) + '\n',
                 'docs/swift-coverage-audit.md': markdown(data)}
    for name, content in artifacts.items():
        path = ROOT / name
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        else:
            require(path.read_text() == content, f'stale audit: {name}; run --write')
    print('Swift coverage: 58 identities, 90 assertions per reference adapter; nine unresolved identities; unfrozen')


if __name__ == '__main__':
    main()
