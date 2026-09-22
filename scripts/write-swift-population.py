#!/usr/bin/env python3
"""Author the prospective Swift input manifest; never changes released populations.

Run only while preparing this initial tranche, before publication. Changes to
published inputs require a new population identity, not regeneration in place.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    entries = []
    revision = hashlib.sha256()
    counts = {}
    for path in sorted((ROOT / 'cases/taint/swift').glob('*/case.json')):
        data = path.read_bytes()
        case = json.loads(data)
        relative = path.relative_to(ROOT).as_posix()
        revision.update(relative.encode())
        revision.update(data)
        fixtures = []
        for filename in case['fixture_files']:
            fixture = path.parent / filename
            content = fixture.read_bytes()
            revision.update(filename.encode())
            revision.update(content)
            fixtures.append({'path': fixture.relative_to(ROOT).as_posix(),
                             'sha256': hashlib.sha256(content).hexdigest()})
        entry = {key: case[key] for key in ('id', 'template_id', 'polarity',
                 'score_tier', 'track', 'model_profile')}
        entry.update(path=relative, sha256=hashlib.sha256(data).hexdigest(),
                     fixture_digests=fixtures)
        entries.append(entry)
        tier = case['score_tier']
        counts[tier] = counts.get(tier, 0) + 1
    if counts != {'core': 66, 'calibration': 4, 'modeling': 20}:
        raise SystemExit(f'incomplete Swift population: {counts}')
    manifest = {'population': 'swift-synthetic-v1', 'status': 'prospective-fixtures-only',
                'contract': 'docs/swift-kernel.md',
                'fixture_revision': 'sha256:' + revision.hexdigest(), 'cases': entries}
    data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    path = ROOT / 'populations/swift-synthetic-v1.json'
    if path.exists():
        raise SystemExit('refusing to overwrite existing prospective population; review changes explicitly')
    path.write_bytes(data)
    print(hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    main()
