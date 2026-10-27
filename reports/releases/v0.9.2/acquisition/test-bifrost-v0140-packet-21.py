#!/usr/bin/env python3
"""Static packet-18 shape checks; no packet is written by these tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("packet21_test", BASE / "bifrost-v0140-packet-21.py")
assert spec is not None and spec.loader is not None
packet = importlib.util.module_from_spec(spec); sys.modules[spec.name] = packet; spec.loader.exec_module(packet)


class Packet18Tests(unittest.TestCase):
    def test_packet_binds_replacement21_protocol_and_has_no_execution_entrypoint(self):
        self.assertEqual(packet.PROTOCOL_PATH,
                         "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-21.py")
        self.assertTrue(callable(packet.prepare_identity))
        self.assertTrue(callable(packet.seal))

    def test_missing_future_core_fails_closed_before_write(self):
        with self.assertRaises(ValueError):
            packet.prepare_identity(Path(__file__).resolve().parents[4], {"schema": "future"})


class Packet18RuntimeApiTests(unittest.TestCase):
    """Exercise the real packet/protocol boundary using an isolated Git fixture."""
    def setUp(self):
        spec = importlib.util.spec_from_file_location("packet21_protocol_fixture", BASE/"test-bifrost-v0140-replacement-21.py")
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        self.fixture = module.RuntimeCoreSchema18Tests("test_sorted_serialized_graph_and_real_contract_source_closure")
        self.fixture.setUp()
        target = self.fixture.root/packet.PROTOCOL_PATH
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((BASE/"bifrost-v0140-replacement-21.py").read_bytes())

    def tearDown(self):
        self.fixture.tearDown()

    def fields(self, core):
        graph=core["runtime_module_graph"]
        return packet.runtime_core_fields(self.fixture.root,core,
            policy_source=graph["policy_source"],policy_runtime=graph["policy_runtime"],
            incoming_recovery=graph["incoming_recovery"],runtime_module_graph=graph)

    def test_real_packet_api_preserves_exact_graph_source_and_manifest_path(self):
        core=self.fixture.clone()
        fields=self.fields(core)
        self.assertEqual(fields["runtime_module_graph"],core["runtime_module_graph"])
        self.assertEqual(fields["source_inputs"],core["source_inputs"])
        self.assertEqual(fields["manifest_path"],"reports/releases/v0.9.2/qualification/bifrost-v0140-replacement-21/manifest.json")
        self.assertEqual(core,self.fixture.core)

    def test_old_protocol_role_and_foreign_source_hash_are_rejected(self):
        core=self.fixture.clone();core["runtime_module_graph"]["protocol14"]=core["runtime_module_graph"].pop("protocol21")
        with self.assertRaises(ValueError):self.fields(core)
        core=self.fixture.clone();core["runtime_module_graph"]["protocol21"]["sha256"]="f"*64
        with self.assertRaises(ValueError):self.fields(core)


if __name__ == "__main__":
    unittest.main()
