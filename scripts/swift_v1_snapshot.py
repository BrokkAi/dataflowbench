"""Explicit immutable v1 input view for historical certificate replay only."""
import json
from pathlib import Path
import shutil
from swift_population_v2 import V1_SHA, require, sha


def materialize(root, destination):
    manifest_path = root / 'populations/swift-synthetic-v1.json'
    require(sha(manifest_path) == V1_SHA, 'immutable v1 manifest changed')
    manifest = json.loads(manifest_path.read_text())
    entries = manifest['cases']
    require(len(entries) == 90 and len({e['id'] for e in entries}) == 90, 'v1 membership')
    for entry in entries:
        for relative, digest in [(entry['path'], entry['sha256'])] + [(f['path'], f['sha256']) for f in entry['fixture_digests']]:
            path = Path(relative)
            require(not path.is_absolute() and '..' not in path.parts, 'v1 path')
            source = root / path
            require(sha(source) == digest, f'v1 input digest: {relative}')
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    # Only cases are narrowed. All certificates/configuration/evidence remain
    # original bytes, exposed read-only by convention for these audit scripts.
    for name in ['adapters', 'evidence', 'reports', 'populations', 'scripts']:
        (destination / name).symlink_to(root / name, target_is_directory=True)
    return destination
