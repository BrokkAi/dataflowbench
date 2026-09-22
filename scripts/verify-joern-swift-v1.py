#!/usr/bin/env python3
"""Replay the historical Joern certificate on an explicit immutable v1 view.

This does not certify current runtime activation or qualify any v2 input.
"""
import importlib.util
from pathlib import Path
import tempfile
from swift_v1_snapshot import materialize

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('historical_joern_verifier', ROOT / 'scripts/verify-joern-swift-activation.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
with tempfile.TemporaryDirectory(prefix='dfb-historical-v1-') as temporary:
    result = verifier.verify(materialize(ROOT, Path(temporary)))
    print({'scope': 'historical-v1-certificate-only', 'current_runtime_activation': 'not-qualified', 'certificate': result})
