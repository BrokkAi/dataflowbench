#!/usr/bin/env python3
"""Verify the prospective native configuration; never emit scored results."""
import hashlib
import json
from pathlib import Path
from swift_population_v2 import audit, require

ROOT = Path(__file__).resolve().parents[1]
BASE = 'adapters/codeql/swift-native-v3'


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def checked_path(root, name):
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == name,
            'unsafe input path')
    current = root
    for part in path.parts:
        current /= part
        require(not current.is_symlink(), 'symlink input')
    require(current.is_file(), 'missing input: ' + name)
    return current


def verify_contract(activation, partition, population):
    require(activation['configuration_id'] == 'codeql-swift-native-v3', 'configuration identity')
    require(activation['status'] == 'pending' and activation['scored_activation'] is False,
            'unqualified activation')
    require(activation['qualified_outcomes'] == 0 and partition['scored_outcomes'] == 0,
            'diagnostic outcome promotion')
    require(activation['version'] == '2.27.1' and activation['swift_all'] == '6.8.4', 'candidate pin')
    require(activation['build_identity'] == '938af3639d0709b587251e45d9f8d2bdc3505696', 'build pin')
    require((activation['compiler_version'], activation['sdk_version'], activation['target']) ==
            ('6.3.3', '26.5', 'arm64-apple-macosx26.5'), 'toolchain pin')
    require(activation['aggregate_memory_compliance'] == activation['semantic_completeness'] == 'unproven',
            'diagnostic qualification promotion')
    require(activation['query_profiles'] == {'vendor-native': 'vendor-native', 'adapter-assisted': 'adapter-corrected'},
            'profile attribution')
    require(activation['joern'] == {'version': '4.0.633', 'status': 'blocked',
            'evidence': 'evidence/swift-joern-identity-220/summary.json', 'normalized_outcome': None},
            'Joern blocker promotion')
    require(activation['unresolved_modeling_templates'] == ['dfb-template-model-opaque-propagator',
            'dfb-template-model-propagator-position'], 'opaque scope')
    require(partition['status'] == 'prospective-qualification-only', 'partition activation')
    require(partition['population'] == population['population'] and
            partition['fixture_revision'] == population['fixture_revision'], 'population identity')
    require(partition['lanes'] == ['vendor-native', 'adapter-assisted'], 'lane separation')
    expected = [{'case_id': c['id'], 'template_id': c['template_id'], 'polarity': c['polarity'],
                 'decision': 'qualification-pending'} for c in population['cases']
                if c['model_profile'] == 'tool-native']
    require(len(expected) == 12 and partition['cases'] == expected, 'exact native population')
    require(partition['first_qualification_cases'] == ['dfb-taint-swift-native-source-sink-positive',
            'dfb-taint-swift-native-source-sink-negative'], 'balanced first qualification')


def verify(root=ROOT):
    population, _ = audit(root)
    activation = read(root / BASE / 'activation.json')
    partition = read(root / BASE / 'partition.json')
    verify_contract(activation, partition, population)
    inputs = read(root / BASE / 'inputs.json')
    required = {'populations/swift-synthetic-v2.json', activation['policy_path'],
                activation['joern']['evidence']}
    required.update(c['path'] for c in population['cases'])
    required.update(f['path'] for c in population['cases'] for f in c['fixture_digests'])
    for directory in [activation['query_directory'], 'evidence/swift-foundation-identity-v1',
                      'evidence/swift-foundation-sources-v1', 'evidence/swift-joern-identity-220']:
        required.update(str(p.relative_to(root)) for p in (root / directory).rglob('*') if p.is_file())
    required.update('evidence/swift-candidate-qualification-220/codeql-runtime/' + name
                    for name in ['version.stdout', 'assets.json', 'resolved-pack-files.json'])
    require(set(inputs) == required, 'exact configuration input closure')
    for name, digest in inputs.items():
        require(hashlib.sha256(checked_path(root, name).read_bytes()).hexdigest() == digest,
                'input digest: ' + name)
    policy = read(root / activation['policy_path'])
    require([policy[k] for k in ['extraction_wall_clock_seconds', 'analysis_wall_clock_seconds',
            'analysis_peak_memory_mb']] == [150, 60, 2048], 'prospective policy')
    require(policy['scored_activation'] is False, 'policy activation')
    h = hashlib.sha256()
    for name in ['activation.json', 'partition.json', 'inputs.json']:
        h.update(name.encode()); h.update((root / BASE / name).read_bytes())
    return {'configuration_id': activation['configuration_id'], 'configuration_hash': 'sha256:' + h.hexdigest(),
            'population_inputs': 104, 'planned_inputs_per_lane': 12, 'scored_outcomes': 0,
            'status': 'pending', 'joern': 'blocked'}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
