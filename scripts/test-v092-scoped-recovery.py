#!/usr/bin/env python3
"""Hermetic tests for the sealed v0.9.2 scoped-recovery packet parser."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name("v092_scoped_recovery.py")
SPEC = importlib.util.spec_from_file_location("v092_scoped_recovery_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
packet_validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_validator)


class ScopedRecoveryPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = ROOT / Path(*packet_validator.MANIFEST_PATH.parts)
        self.manifest_raw = self.manifest_path.read_bytes()
        self.manifest = json.loads(self.manifest_raw)
        self.reference = {
            "path": packet_validator.MANIFEST_PATH.as_posix(),
            "sha256": hashlib.sha256(self.manifest_raw).hexdigest(),
        }
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def _copy_packet(self) -> Path:
        destination = Path(self.temp.name)
        paths = {
            packet_validator.MANIFEST_PATH.as_posix(),
            packet_validator.AUTHORIZATION_PATH.as_posix(),
            packet_validator.PREFIX_PATH.as_posix(),
            packet_validator.LEDGER_PATH.as_posix(),
            self.manifest["repair_patch"]["path"],
            self.manifest["repair_proof"]["path"],
            self.manifest["failure_diagnosis"]["path"],
        }
        for item in self.manifest["retained_completed"] + self.manifest["retained_failures"]:
            paths.add(item["started_receipt"]["path"])
            paths.add(item["completed_receipt"]["path"])
        for relative in paths:
            source = ROOT / Path(*PurePosixPath(relative).parts)
            target = destination / Path(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return destination

    def test_complete_sealed_packet_replays_from_a_relocated_copy(self):
        destination = self._copy_packet()
        replay = packet_validator.validate_packet(destination, self.reference)
        self.assertEqual(len(replay["prefix_rows"]), 27)
        self.assertEqual(len(replay["retained_completed"]), 25)
        self.assertEqual(len(replay["retained_failures"]), 2)
        self.assertEqual(replay["sealed_prefix_sha256"], packet_validator.PREFIX_SHA256)

    def test_packet_rejects_tampered_authorization_bytes(self):
        destination = self._copy_packet()
        auth = destination / Path(*packet_validator.AUTHORIZATION_PATH.parts)
        auth.write_bytes(auth.read_bytes() + b" ")
        with self.assertRaisesRegex(packet_validator.ScopedRecoveryError, "differ from their digest"):
            packet_validator.validate_packet(destination, self.reference)

    def test_packet_rejects_tampered_retained_receipt(self):
        destination = self._copy_packet()
        relative = self.manifest["retained_completed"][0]["completed_receipt"]["path"]
        receipt = destination / Path(*PurePosixPath(relative).parts)
        receipt.write_bytes(receipt.read_bytes() + b" ")
        with self.assertRaisesRegex(packet_validator.ScopedRecoveryError, "receipt digest"):
            packet_validator.validate_packet(destination, self.reference)

    def test_packet_rejects_an_unregistered_manifest_location(self):
        with self.assertRaisesRegex(packet_validator.ScopedRecoveryError, "registered path"):
            packet_validator.validate_packet(ROOT, {
                "path": "reports/releases/v0.9.2/qualification/other/manifest.json",
                "sha256": self.reference["sha256"],
            })


if __name__ == "__main__":
    unittest.main()
