#!/usr/bin/env python3
"""Verify portable canonical entrypoint qualification evidence without analyzer execution."""
import importlib.util
import json
import re
import zipfile
from pathlib import Path
from swift_extraction_integrity import inspect_logs

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qualification', ROOT / 'scripts/run-swift-entrypoint-qualification.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


def verify(directory=None):
    directory = directory or ROOT / 'evidence/swift-entrypoint-qualification-v1/attempt-01'
    plan, configuration = q.verify_preregistration(False)
    manifest = q.read(directory / 'manifest.json')
    actual = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()} - {'manifest.json'}
    q.require(set(manifest) == actual, 'exact retained artifact set')
    for name, digest in manifest.items():
        q.require(q.sha(q.integration.checked_path(directory, name)) == digest, 'retained digest: ' + name)
    run = q.read(directory / 'run.json')
    q.require(run['scope'] == plan['scope'] and run['scored_activation'] is False, 'run scope')
    q.require(run['configuration'] == configuration and run['plan_sha256'] == q.sha(q.PLAN), 'run configuration')
    q.require([a['case_id'] for a in run['attempts']] == plan['cases'], 'complete canonical pair')
    q.require(run['status'] == 'retained-non-scored-attempts' and 'error' not in run, 'run error')
    runtime = q.read(directory / 'runtime.json')
    q.require(runtime['assets'] == q.read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json'), 'asset witness')
    q.require(runtime['sdk_settings_sha256'] == plan['sdk_settings_sha256'], 'SDK witness')
    prior = q.read(ROOT / 'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    q.require(runtime['compiler_sha256'] == prior['compiler_sha256'], 'compiler identity')
    q.require(runtime['pack_files_verified'] == len(q.read(ROOT / 'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json')), 'pack closure count')
    version = q.read(directory / 'version.json')
    q.require(version['version'] == '2.27.1' and version['sha'] == '938af3639d0709b587251e45d9f8d2bdc3505696', 'version witness')
    population = q.read(ROOT / 'populations/swift-synthetic-v2.json')
    for case_id in plan['cases']:
        path = directory / case_id
        entry = next(c for c in population['cases'] if c['id'] == case_id)
        canonical = ROOT / entry['path']; case = q.read(canonical)
        join = q.read(path / 'canonical-join.json')
        q.require(join['canonical_entry'] == entry and join['case_id'] == case_id and
                  join['population'] == population['population'] and join['fixture_revision'] == population['fixture_revision'], 'canonical join')
        q.require((path / 'canonical-case.json').read_bytes() == canonical.read_bytes(), 'canonical metadata')
        expected_source = (canonical.parent / 'main.swift').read_bytes()
        for source in ['control/main.swift', 'probe/main.swift']:
            q.require((path / source).read_bytes() == expected_source, 'canonical source')
        probe = path / 'probe'; witness = q.read(probe / 'witness.json')
        q.require(witness['source_commit'] == run['source_commit'], 'preregistered revision')
        q.require(witness['status'] == 'unqualified' and not witness.get('probe_error') and
                  not witness.get('cleanup_error') and witness['population_member'] is False, 'probe scope/error')
        q.require(witness['analysis_budget'] == {'wall_clock_seconds': 60, 'peak_memory_mb': 2048} and
                  witness['extraction_phase_deadline_seconds'] == 150, 'phase limits')
        q.require(witness['compiler_sha256'] == runtime['compiler_sha256'], 'compiler join')
        q.require(inspect_logs(probe / 'log/swift/extractor')['ready_for_observation'], 'raw extraction gate')
        for phase in ['database-create', 'database-resolve', 'roles', 'flow', 'identity', 'roles-decode', 'flow-decode', 'identity-decode']:
            record = q.read(probe / (phase + '.command.json'))
            q.require(record['exit_status'] == 0 and not record['timed_out'] and
                      record['cleanup_status'] == 'tracked-processes-stopped', 'phase failure')
            q.require(record['deadline_seconds'] == (150 if phase == 'database-create' else 60), 'phase deadline')
            if phase in ['roles', 'flow', 'identity']:
                q.require('--ram=2048' in record['argv'] and '--timeout=60' in record['argv'], 'query budget')
        for query in (ROOT / 'adapters/codeql/swift-foundation-sources-v1/queries').iterdir():
            if query.is_file():
                q.require((probe / 'queries' / query.name).read_bytes() == query.read_bytes(), 'query provenance')
        observation = q.read(path / 'observation.json')
        for phase in ['database-create', 'roles', 'flow', 'identity']:
            record = q.read(probe / (phase + '.command.json'))
            q.require(record == witness['phases'][phase], 'phase witness join')
            rss = re.search(r'(\d+)\s+maximum resident set size', (probe / (phase + '.stderr')).read_text())
            q.require(observation['phase_measurements'][phase] == {
                'elapsed_seconds': record['elapsed_seconds'],
                'command_maxrss_bytes': int(rss[1]) if rss else None}, 'phase measurement join')
        q.require(observation['status'] == 'observed-unqualified' and observation['scored_activation'] is False and
                  observation['aggregate_memory_compliance'] == observation['semantic_completeness'] == 'unproven', 'observation promotion')
        q.require(observation['source_sha256'] == entry['fixture_digests'][0]['sha256'] == join['staged_source_sha256'], 'archive source identity')
        archive = directory.parent / 'source-archives' / (case_id + '.zip')
        q.require(q.sha(archive) == observation['archive_sha256'], 'retained archive digest')
        with zipfile.ZipFile(archive) as z:
            q.require(z.read(observation['archive_member']) == expected_source, 'retained archived bytes')
        roles = q.read(probe / 'roles.json')['#select']['tuples']
        flows = q.read(probe / 'flow.json')['#select']['tuples']
        identities = q.read(probe / 'identity.json')['#select']['tuples']
        source, sink = case['source_anchors'][0]['line_hint'], case['sink_anchors'][0]['line_hint']
        q.require(any(r[:5] == [source, 'Swift', 'Swift', 'CommandLine', 'arguments'] for r in identities), 'resolved source')
        q.require(all(r[2] in ['vendor-native', 'adapter-corrected'] for r in roles) and
                  all(r[3] in ['vendor-native', 'adapter-corrected'] for r in flows), 'unknown profile')
        for lane, profile in [('vendor-native', 'vendor-native'), ('adapter-assisted', 'adapter-corrected')]:
            view = observation['lanes'][lane]
            q.require(view['source_rows'] == [r for r in roles if r[2] == profile and r[3] != 'sink'] and
                      view['sink_rows'] == [r for r in roles if r[2] == profile and r[3] == 'sink'] and
                      view['flow_rows'] == [r for r in flows if r[3] == profile], 'raw row join')
            q.require(view['sink_rows'] and all(r[0] == sink for r in view['sink_rows']), 'nonvacuous sink')
            q.require(view['source_anchor_recognized'] == any(r[0] == source for r in view['source_rows']) and
                      view['sink_anchor_recognized'] == bool(view['sink_rows']), 'role observation flags')
            q.require(view['observed_anchor_flow'] == any(r[0] == source for r in view['flow_rows']), 'observation flow flag')
        assisted = observation['lanes']['adapter-assisted']
        vendor = observation['lanes']['vendor-native']
        q.require(not vendor['source_rows'] and not vendor['flow_rows'] and len(vendor['sink_rows']) == 2, 'retained vendor observation')
        q.require(len(assisted['source_rows']) == 2 and len(assisted['sink_rows']) == 2 and
                  len([r for r in assisted['flow_rows'] if r[0] == source]) == (1 if case['polarity'] == 'positive' else 0), 'retained assisted counts')
        q.require({r[0] for r in assisted['source_rows']} == {source - 1, source}, 'nonvacuous source')
        q.require(case['polarity'] == 'positive' or not assisted['flow_rows'], 'negative auxiliary flow')
        q.require(assisted['observed_anchor_flow'] == (case['polarity'] == 'positive'), 'canonical separating behavior')
        q.require(all(r[0] in {source - 1, source} and any(s[:2] == r[1:3] for s in assisted['sink_rows'])
                      for r in assisted['flow_rows']), 'canonical flow joins')
    print('Verified canonical entrypoint pair, separate raw lanes and immutable joins; non-scored, memory/completeness unproven.')


if __name__ == '__main__':
    verify()
