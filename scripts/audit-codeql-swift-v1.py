#!/usr/bin/env python3
"""Replay the unchanged CodeQL audit on an explicit immutable v1 input view."""
from pathlib import Path
import subprocess
import sys
import tempfile
from swift_v1_snapshot import materialize

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='dfb-codeql-historical-v1-') as temporary:
    snapshot = materialize(ROOT, Path(temporary))
    subprocess.run([sys.executable, str(ROOT / 'evidence/codeql-swift/execution-218/audit.py')], cwd=snapshot, check=True)
