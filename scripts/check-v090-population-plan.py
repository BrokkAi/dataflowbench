#!/usr/bin/env python3
"""Validate the prospective common population without executing any analyzer."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(value, message):
    if not value:
        raise ValueError(message)


def read(root, path):
    return json.loads((root / path).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root=ROOT):
    population_path = 'populations/v0.9.0.json'
    population = read(root, population_path)
    plan = read(root, 'reports/releases/v0.9.0/plan.json')
    historical = read(root, 'reports/releases/v0.8.0/population.json')
    swift = read(root, 'populations/swift-synthetic-v3.json')
    historical_cases = []
    for selected in historical['cases']:
        case = read(root, selected['path'])
        require(digest(root / selected['path']) == selected['sha256'], 'historical case bytes changed')
        historical_cases.append({
            **{k: selected[k] for k in ['id', 'path', 'sha256', 'track', 'score_tier', 'model_profile']},
            'template_id': case['template_id'], 'polarity': case['polarity'],
            'fixture_digests': selected['fixtures'],
        })
    expected = sorted(historical_cases + swift['cases'], key=lambda c: c['path'])
    require(population['cases'] == expected, 'common population must preserve exact historical union')
    require(len(expected) == len({c['id'] for c in expected}) == 1108, 'common denominator')
    revision = hashlib.sha256()
    languages = set()
    swift_count = 0
    for selected in expected:
        relative = selected['path']
        path = root / relative
        require(digest(path) == selected['sha256'], 'case bytes changed: ' + relative)
        case = json.loads(path.read_text())
        require(case['id'] == selected['id'], 'case identity mismatch')
        languages.add(case['language'])
        swift_count += case['language'] == 'swift'
        revision.update(relative.encode())
        revision.update(path.read_bytes())
        fixtures = {f['path']: f['sha256'] for f in selected['fixture_digests']}
        require(len(fixtures) == len(selected['fixture_digests']), 'duplicate fixture')
        require(set(fixtures) == {str(Path(relative).parent / f) for f in case['fixture_files']}, 'fixture membership')
        for name in case['fixture_files']:
            fixture = path.parent / name
            require(digest(fixture) == fixtures[str(Path(relative).parent / name)], 'fixture bytes changed')
            revision.update(name.encode())
            revision.update(fixture.read_bytes())
    require(len(languages) == 14 and swift_count == 108, 'language denominator')
    require(population['fixture_revision'] == plan['fixture_revision'] == 'sha256:' + revision.hexdigest(), 'common revision mismatch')
    require(plan['population'] == {'path': population_path, 'sha256': digest(root / population_path)}, 'population binding')
    rows = plan['reports']
    require(len(rows) == len({r['id'] for r in rows}) == 92, 'partition denominator')
    require(sum(len(r['case_ids']) for r in rows) == 4252, 'report row denominator')
    require(len({r['report'] for r in rows}) == 92, 'duplicate output path')
    for name in ['pin_review', 'control_plan', 'dependency_contract']:
        reference = plan[name]
        require(digest(root / reference['path']) == reference['sha256'], name + ' binding')
    groups = plan['execution_groups']
    require(len(groups) == len({g['id'] for g in groups}) == 84, 'execution group denominator')
    assigned = [path for g in groups for path in g['reports']]
    require(len(assigned) == len(set(assigned)) == 92 and set(assigned) == {r['report'] for r in rows}, 'execution group report coverage')
    for group in groups:
        members = [r for r in rows if r['execution_group'] == group['id']]
        require(sorted({case for row in members for case in row['case_ids']}) == group['case_ids'], 'execution group membership')
    common_ids = {c['id'] for c in expected}
    for row in rows:
        ids = row['case_ids']
        require(ids == sorted(set(ids)) and set(ids) <= common_ids, 'invalid report membership')
        encoded = (json.dumps(ids, sort_keys=True, separators=(',', ':')) + '\n').encode()
        require(row['case_membership'] == {'count': len(ids), 'sha256': hashlib.sha256(encoded).hexdigest()}, 'report membership binding')
        reference = row['historical_reference']
        require(digest(root / reference['path']) == reference['sha256'], 'historical report changed')
        report = read(root, reference['path'])
        require(sorted(r['case_id'] for r in report['results']) == ids, 'report population drift')
        require(row['report'].startswith('reports/releases/v0.9.0/normal/'), 'new output must be versioned')
    require(plan['status'] == 'pending-parent-review', 'prospective plan cannot authorize execution')
    require(not any(row.get('argv') for row in [*rows, *groups]), 'prospective plan must not carry executable argv')
    return {'cases': 1108, 'swift': 108, 'languages': 14, 'partitions': 92, 'rows': 4252}


if __name__ == '__main__':
    print(json.dumps(validate(), sort_keys=True))
