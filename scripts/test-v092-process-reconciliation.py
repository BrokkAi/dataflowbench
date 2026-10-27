#!/usr/bin/env python3
"""Run synthetic process-policy tests using this checkout's retained sources.

The production qualifier keeps its exact execution root. Only the test host
binds source lookup to this checkout; providers, Popen and clocks are fixtures.
This entry point never invokes native controls or an analyzer.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/releases/v0.9.2/acquisition/joern-native-controls-06"
sys.path.insert(0, str(SOURCE))
import native_qualifier
native_qualifier.ROOT = ROOT

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        "test_reconciliation_policy", "test_contention_repair",
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
