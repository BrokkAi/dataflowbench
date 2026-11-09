#!/usr/bin/env python3
"""Prospective paths cannot widen a historical inventory or hide mutations."""
import json
from pathlib import Path
import tempfile
import unittest

from precision_population import INVENTORY, ROOT, historical_paths


class PrecisionPopulationTests(unittest.TestCase):
    def test_historical_selection_remains_exact(self):
        paths = set((ROOT / "cases").rglob("case.json"))
        historical = historical_paths(ROOT, paths)
        additions = json.loads(INVENTORY.read_text())["cases"]
        self.assertEqual(paths - historical, {ROOT / entry["path"] for entry in additions})

    def test_registered_path_requires_exact_metadata_bytes(self):
        entry = json.loads(INVENTORY.read_text())["cases"][0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / entry["path"]
            path.parent.mkdir(parents=True)
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "precision case digest"):
                historical_paths(root, [path])

    def test_unregistered_copy_stays_visible_to_historical_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "cases/taint/swift/unregistered/case.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}")
            self.assertEqual(historical_paths(root, [path]), {path})


if __name__ == "__main__":
    unittest.main()
