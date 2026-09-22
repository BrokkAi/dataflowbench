#!/usr/bin/env python3
"""Replay the unchanged CodeQL v1 audit against its immutable population."""
import json
from pathlib import Path
from unittest.mock import patch
import runpy

ROOT = Path(__file__).resolve().parents[1]
original_glob = Path.glob
paths = [Path(entry['path']) for entry in json.loads((ROOT/'populations/swift-synthetic-v1.json').read_text())['cases']]

def scoped_glob(self, pattern):
    if self == Path('.') and pattern == 'cases/taint/swift/*/case.json':
        return iter(paths)
    return original_glob(self, pattern)

with patch.object(Path, 'glob', scoped_glob):
    runpy.run_path(str(ROOT/'evidence/codeql-swift/execution-218/audit.py'), run_name='__main__')
