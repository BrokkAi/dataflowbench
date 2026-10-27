#!/usr/bin/env python3
"""No-expiry policy positive and near-miss tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BASE = Path(__file__).resolve().parent
def repository_root():
    candidate = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents)>4 else Path.cwd()
    if not (candidate/'scripts/execute-release-v092.py').is_file(): candidate=Path.cwd().resolve()
    assert (candidate/'scripts/execute-release-v092.py').is_file(), 'run private canonical staging from repository root'
    return candidate
ROOT=repository_root()
HISTORICAL_BASE=ROOT/'reports/releases/v0.9.2/acquisition'

spec = importlib.util.spec_from_file_location("noexpiry14_test", BASE / "bifrost-v0140-no-expiry-24.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)


class NoExpiry24Tests(unittest.TestCase):
    def core(self):
        return {"cutoff_utc": None, "total_wall_budget_seconds": None,
                "original_origin_utc": module.ORIGIN,
                "execution_window_authority": module.AUTHORITY,
                "resource_policy": dict(module.RESOURCE_POLICY)}

    def test_exact_authority_and_finite_runtime_policy(self):
        root = ROOT
        self.assertEqual(module.validate(root, self.core())["status"], "validated")
        self.assertEqual(module.RESOURCE_POLICY["startup_seconds"], 600)
        self.assertEqual(module.RESOURCE_POLICY["handshake_seconds"], 120)

    def test_expiry_and_guard_mutations_fail(self):
        root = ROOT
        value = self.core(); value["cutoff_utc"] = "2099-01-01T00:00:00Z"
        with self.assertRaises(module.NoExpiry23Error):
            module.validate(root, value)
        value = self.core(); value["resource_policy"]["startup_seconds"] = 601
        with self.assertRaises(module.NoExpiry23Error):
            module.validate(root, value)


if __name__ == "__main__":
    unittest.main()
