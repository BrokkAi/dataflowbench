#!/usr/bin/env python3
"""Focused tests for v0.9.2 Swift plan materialization safeguards."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "materialize_swift_plans_v092", ROOT / "scripts/materialize-swift-plans-v092.py"
)
assert SPEC is not None and SPEC.loader is not None
materializer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(materializer)


class MaterializeSwiftPlansTests(unittest.TestCase):
    def test_refresh_binds_every_query_tree_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "adapters/codeql/v0.9.2/swift/queries/standard").mkdir(parents=True)
            (root / "adapters/codeql/v0.9.2/swift/queries/standard/modeling-flow.ql").write_text("query\n")
            (root / "adapters/codeql/v0.9.2/swift/queries/standard/codeql-pack.lock.yml").write_text("lock\n")
            (root / "contracts/swift.json").parent.mkdir(parents=True)
            (root / "contracts/swift.json").write_text("{}\n")
            (root / "scripts/capture.py").parent.mkdir(parents=True)
            (root / "scripts/capture.py").write_text("capture\n")
            plan = {
                "configurations": {"profile": []},
                "execution_contract": {"path": "contracts/swift.json"},
                "runtime": {},
                "engine": "codeql",
                "query_root": "adapters/codeql/v0.9.2/swift",
            }
            with (
                patch.object(materializer, "runtime_refs", return_value=[]),
                patch.object(materializer, "component_manifest_paths", return_value=[]),
                patch.object(materializer, "references_from_control", return_value=[]),
            ):
                materializer.refresh_configuration(root, plan, {}, ["scripts/capture.py"])

            refs = {row["path"]: row["sha256"] for row in plan["configurations"]["profile"]}
            expected = {
                "adapters/codeql/v0.9.2/swift/queries/standard/modeling-flow.ql",
                "adapters/codeql/v0.9.2/swift/queries/standard/codeql-pack.lock.yml",
                "contracts/swift.json",
                "scripts/capture.py",
            }
            self.assertEqual(set(refs), expected)
            self.assertRegex(refs["adapters/codeql/v0.9.2/swift/queries/standard/codeql-pack.lock.yml"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
