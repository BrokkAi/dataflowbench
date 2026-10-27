#!/usr/bin/env python3
"""Static packet-14 shape checks; no packet is written by these tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("packet14_test", BASE / "bifrost-v0140-packet-14.py")
assert spec is not None and spec.loader is not None
packet = importlib.util.module_from_spec(spec); sys.modules[spec.name] = packet; spec.loader.exec_module(packet)


class Packet14Tests(unittest.TestCase):
    def test_packet_binds_replacement14_protocol_and_has_no_execution_entrypoint(self):
        self.assertEqual(packet.PROTOCOL_PATH,
                         "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py")
        self.assertTrue(callable(packet.prepare_identity))
        self.assertTrue(callable(packet.seal))

    def test_missing_future_core_fails_closed_before_write(self):
        with self.assertRaises(ValueError):
            packet.prepare_identity(Path(__file__).resolve().parents[4], {"schema": "future"})


if __name__ == "__main__":
    unittest.main()
