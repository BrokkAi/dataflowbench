"""Immutable Swift v2 input audit; no analyzer qualification or outcome invention."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = {f'dfb-template-native-{name}' for name in ('source-sink','propagator','sanitizer','summary','entrypoint','persistence')}
RESULT = 'dfb-template-result-error-propagation'
V1_SHA = '95e3075b26ebd55cff6dc5fa0fc413ed15733c2ae9d8e21014f80395ca24c4f5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root=ROOT):
    v1_path = root/'populations/swift-synthetic-v1.json'
    require(sha(v1_path) == V1_SHA, 'immutable v1 manifest changed')
    v1 = json.loads(v1_path.read_text())
    manifest = json.loads((root/'populations/swift-synthetic-v2.json').read_text())
    require(manifest['population'] == 'swift-synthetic-v2', 'v2 population identity')
    entries = {c['id']: c for c in manifest['cases']}
    require(len(entries) == len(manifest['cases']) == 104, 'v2 must contain 104 unique cases')
    for previous in v1['cases']:
        require(entries.get(previous['id']) == previous, f'v1 member changed: {previous["id"]}')
    require({e['path'] for e in entries.values()} == {str(p.relative_to(root)) for p in (root/'cases/taint/swift').glob('*/case.json')}, 'v2 complete file set')
    old_ids = {e['id'] for e in v1['cases']}
    new = []
    revision = hashlib.sha256()
    pairs = Counter()
    for entry in sorted(entries.values(), key=lambda e: e['path']):
        path = root/entry['path'];case = json.loads(path.read_text())
        require(sha(path) == entry['sha256'], f'case digest: {path}')
        for key in ('id','template_id','polarity','score_tier','track','model_profile'):
            require(case[key] == entry[key], f'metadata mismatch: {key}')
        require(case['language'] == 'swift' and case['track'] == 'taint', 'Swift taint scope')
        require(case['execution_budget'] == {'peak_memory_mb':512,'wall_clock_seconds':60}, 'budget drift')
        revision.update(entry['path'].encode());revision.update(path.read_bytes())
        fixtures=[]
        for name in case['fixture_files']:
            fixture=path.parent/name
            require(not Path(name).is_absolute() and '..' not in Path(name).parts and Path(name).suffix=='.swift','fixture path')
            revision.update(name.encode());revision.update(fixture.read_bytes())
            fixtures.append({'path':str(fixture.relative_to(root)),'sha256':sha(fixture)})
        require(fixtures == entry['fixture_digests'], 'fixture digest mismatch')
        if case['id'] in old_ids:continue
        template=case['template_id']
        require(template in NATIVE | {RESULT}, 'unregistered v2 addition')
        require(case['model_profile'] == ('tool-native' if template in NATIVE else 'benchmark-controlled'), 'profile separation')
        require(case['score_tier'] == ('modeling' if template in NATIVE else 'language-extension'), 'tier separation')
        require(case['tool_model_references'] == {}, 'unqualified adapter activation')
        pairs[(template,case['polarity'])]+=1
        new.append((path,case))
    require(pairs == Counter({(t,p):1 for t in NATIVE|{RESULT} for p in ('positive','negative')}), 'complete balanced additions')
    require(manifest['fixture_revision'] == 'sha256:'+revision.hexdigest(),'v2 fixture revision')
    return manifest,new


def runtime_control_allowed(case):
    return case['template_id'] == RESULT and case['model_profile'] == 'benchmark-controlled' and case['score_tier'] == 'language-extension'
