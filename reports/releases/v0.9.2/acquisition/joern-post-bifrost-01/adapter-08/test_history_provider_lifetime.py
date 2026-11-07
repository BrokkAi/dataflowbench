"""Regression for the history provider registration leaking out of graph95."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("packet_under_test", Path(__file__).with_name("packet.py"))
packet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet)


class HistoryProviderLifetimeTest(unittest.TestCase):
    def test_exact_provider_leaves_no_global_registration(self):
        provider = packet.load_history_provider()
        self.assertIs(packet.load_history_provider(), provider)
        self.assertNotIn(packet._HISTORY_MODULE_NAME, sys.modules)

    def test_foreign_registration_stops_without_removal(self):
        name = packet._HISTORY_MODULE_NAME
        foreign = types.ModuleType(name)
        with patch.dict(sys.modules, {name: foreign}):
            with self.assertRaisesRegex(packet.AdapterError, "already owned"):
                packet.load_history_provider()
            self.assertIs(sys.modules[name], foreign)


if __name__ == "__main__":
    unittest.main()
