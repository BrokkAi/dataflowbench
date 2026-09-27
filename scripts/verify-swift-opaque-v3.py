#!/usr/bin/env python3
"""Verify the staged opaque population without changing historical case discovery."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def verify(root=ROOT):
    manifest = json.loads((root/'populations/swift-opaque-v3.json').read_text())
    def require(value, message):
        if not value:
            raise ValueError(message)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    require(manifest['population'] == 'swift-opaque-v3' and
            manifest['status'] == 'prospective-fixtures-only' and manifest['scored_activation'] is False,
            'prospective population identity')
    require(sha(root/'populations/swift-synthetic-v2.json') == manifest['historical_population_sha256'],
            'historical population digest')
    expected = {(f'dfb-template-model-{family}', polarity)
                for family in ['opaque-propagator', 'propagator-position']
                for polarity in ['positive', 'negative']}
    require(len(manifest['cases']) == 4 and {(c['template_id'], c['polarity']) for c in manifest['cases']} == expected,
            'complete balanced opaque population')
    control = (root/'evidence/swift-opaque-objc-v1/control-v2/main.swift').read_text().split('@inline(never)')[0]
    require(len({c['id'] for c in manifest['cases']}) == 4, 'unique case identities')
    observed_files = set()
    for entry in manifest['cases']:
        case_path = Path(entry['case_path'])
        require(not case_path.is_absolute() and '..' not in case_path.parts and
                case_path.parts[:2] == ('populations', 'swift-opaque-v3') and
                case_path.name == 'case.json', 'staged case path')
        require(set(entry['files']) == {str(case_path), str(case_path.parent/'main.swift')}, 'exact fixture closure')
        observed_files.update(entry['files'])
        require(all(sha(root/path) == digest for path, digest in entry['files'].items()), 'fixture digest')
        path = root/entry['case_path']; case = json.loads(path.read_text())
        require(all(case[key] == entry[key] for key in ['id','template_id','polarity']), 'case identity')
        require(case['language'] == 'swift' and case['model_profile'] == 'benchmark-controlled' and
                case['execution_budget'] == {'wall_clock_seconds':60,'peak_memory_mb':512}, 'case contract')
        text = (path.parent/'main.swift').read_text()
        require(text.startswith(control), 'qualified runtime dispatch class changed')
        for key in ['source_anchors','sink_anchors']:
            for anchor in case[key]:
                require(anchor['marker'] in text.splitlines()[anchor['line_hint']-1], 'exact anchor')
    require(observed_files == {str(p.relative_to(root)) for p in (root/'populations/swift-opaque-v3').rglob('*') if p.is_file()}, 'population file closure')
    return manifest

if __name__ == '__main__':
    verify()
    print('Four prospective opaque fixtures verified; scoring and canonical registration remain pending.')
