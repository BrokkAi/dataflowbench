#!/usr/bin/env python3
"""Replay the immutable Joern v1 certificate against its original population.

This audit does not activate v2 or modify the hash-bound runner/verifier.
New execution requires the separately versioned qualification tranche.
"""
import json
from pathlib import Path
from unittest.mock import patch
import runpy

ROOT = Path(__file__).resolve().parents[1]
original_glob = Path.glob
paths = [ROOT / entry['path'] for entry in json.loads((ROOT / 'populations/swift-synthetic-v1.json').read_text())['cases']]


def scoped_glob(self, pattern):
    if self == ROOT / 'cases/taint/swift' and pattern == '*/case.json':
        return iter(paths)
    return original_glob(self, pattern)


with patch.object(Path, 'glob', scoped_glob):
    runpy.run_path(str(ROOT / 'scripts/verify-joern-swift-activation.py'), run_name='__main__')
