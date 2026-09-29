"""Exact local runtime inventory with explicit external symlink dependencies."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inventory(root, external_files=()):
    root = Path(root).resolve(strict=True)
    allowed = {str(Path(p).resolve(strict=True)) for p in external_files}
    entries = {}
    external = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs+files):
            path = Path(directory)/name
            key = str(path.relative_to(root))
            mode = path.lstat().st_mode & 0o777
            if path.is_symlink():
                target = path.resolve(strict=True)
                entries[key] = {'symlink': os.readlink(path), 'mode': mode}
                if not target.is_relative_to(root):
                    if str(target) not in allowed or not target.is_file():
                        raise ValueError('unregistered external runtime link: ' + str(path))
                    external[str(target)] = {'sha256':sha(target), 'mode':target.stat().st_mode & 0o777}
            elif path.is_file():
                entries[key] = {'sha256':sha(path), 'mode':mode}
            elif path.is_dir():
                entries[key] = {'directory':True, 'mode':mode}
            else:
                raise ValueError('nonregular runtime entry: ' + str(path))
    if not entries:
        raise ValueError('empty runtime tree')
    return {'schema':'release-runtime-tree/v1', 'root':str(root), 'entries':entries, 'external_files':external}


def verify(manifest):
    observed = inventory(manifest['root'], manifest['external_files'])
    if observed != manifest:
        raise ValueError('runtime membership, bytes, mode or external dependency drift')
    return True
