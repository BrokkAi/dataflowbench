#!/usr/bin/env python3
"""Verify the bounded native candidate audit without analyzer execution."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-candidate-native-audit-220'


def read(path):
    return json.loads(path.read_text())


def language_records(rows, language):
    return [r for r in rows if r['language'].casefold() == language.casefold()]


def verify_catalog():
    base = BASE / 'joern-catalog'
    published, loaded = read(base / 'querydb.json'), read(base / 'loaded-querydb.json')
    assert len({r['name'] for r in published}) == len(published), 'duplicate query names'
    assert sorted(published, key=lambda r: r['name']) == sorted(loaded, key=lambda r: r['name'])
    summary = read(base / 'summary.json')
    assert len(published) == summary['record_count'] == 58
    assert dict(Counter(r['language'] for r in published)) == summary['language_counts']
    assert len(language_records(published, 'swift')) == summary['swift_record_count'] == 0
    assert len(language_records(published, 'c')) == 27
    release = read(base / 'release.json')
    assert release['tag_name'] == 'v4.0.633'
    for name in ('querydb.json', 'querydb.zip'):
        acquisition = read(base / (name + '.acquisition.json'))
        asset = next(a for a in release['assets'] if a['name'] == name)
        assert acquisition['actual_bytes'] == asset['size']
        assert 'sha256:' + acquisition['actual_sha256'] == asset['digest']
    assert 'sha256:' + hashlib.sha256((base / 'querydb.json').read_bytes()).hexdigest() == next(a['digest'] for a in release['assets'] if a['name'] == 'querydb.json')
    assert [read(base / f'vendor-loader-attempt-0{i}.record.json')['exit_status'] for i in (1, 2, 3)] == [1, 1, 0]
    assert summary['capability_decision'] is None
    assert not summary['active_pin_mutation'] and not summary['native_fixture_execution']


def verify_models():
    base = BASE / 'codeql-models'
    rows = read(base / 'catalog.json')['#select']['tuples']
    parsed = [{'role': role, 'fields': next(csv.reader([row], delimiter=';')), 'row': row}
              for role, row in rows]
    assert parsed == read(base / 'model-rows.json')
    summary = read(base / 'summary.json')
    assert dict(Counter(r['role'] for r in parsed)) == summary['role_counts']
    assert len(parsed) == summary['model_row_count'] == 876
    def count(role, type_name, member):
        return sum(r['role'] == role and r['fields'][1] == type_name and r['fields'][3] == member for r in parsed)
    assert count('source', 'UITextField', 'text') == 1
    assert count('source', 'UITextField', 'text_near_miss') == 0
    assert count('sink', 'Process', 'run(_:arguments:terminationHandler:)') == 1
    assert count('source', 'ProcessInfo', 'environment') == 0
    assert count('source', 'CommandLine', 'arguments') == 0
    prior = read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')
    prefix = 'codeql/swift-all/6.8.4/'
    files = {r['path'][len(prefix):]: r['sha256'] for r in prior if r['path'].startswith(prefix)}
    inventory = read(base / 'qll-inventory.json')
    assert {r['path']: r['sha256'] for r in inventory} == {p: h for p, h in files.items() if p.endswith('.qll')}
    assert len(inventory) == summary['qll_files_inventoried'] == 1350
    for path in (base / 'shipped-source').rglob('*'):
        if path.is_file() and path.name != 'LICENSE':
            assert hashlib.sha256(path.read_bytes()).hexdigest() == files[str(path.relative_to(base / 'shipped-source'))]
    assert summary['capability_decision'] is None
    assert all(r['exit_status'] == 0 and not r['timed_out'] for r in read(base / 'witness.json')['phases'].values())


def verify_mechanisms():
    base = BASE / 'joern-mechanisms'
    status = read(base / 'status.json')
    assert status['candidate']['upstream_peeled_commit'] == 'a7c4aa366081960ab2e54b8f0e163bc7d40fc5dc'
    assert status['decision'] == 'none-emitted-parent-owned'
    controls = read(base / 'mechanism-controls.json')
    source = (base / 'source-files/DefaultSemantics.scala').read_bytes()
    assert hashlib.sha256(source).hexdigest() == controls['source_sha256']
    assert controls['positive_builtin_atoi'] and not controls['negative_near_miss_atoi']
    assert not controls['negative_ProcessInfo_in_selected_defaults']
    assert not controls['negative_CommandLine_in_selected_defaults']
    assert controls['capability_decision'] is None


def main():
    manifest = read(BASE / 'manifest.json')
    actual = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in BASE.rglob('*') if p.is_file() and p != BASE / 'manifest.json'}
    assert actual == manifest['files'], 'native candidate evidence changed'
    verify_catalog()
    verify_models()
    verify_mechanisms()
    print('Candidate native evidence verified; no capability decision or pin promotion')


if __name__ == '__main__':
    main()
