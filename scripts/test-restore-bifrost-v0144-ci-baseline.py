#!/usr/bin/env python3
"""Exercise the pinned one-file CI baseline restoration in isolated roots."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
RESTORE_SCRIPT = REPOSITORY_ROOT / "scripts/restore-bifrost-v0144-ci-baseline.py"
BUNDLE = REPOSITORY_ROOT / "evidence-delivery/v0.9.2-bifrost-v0144-01/ci-baseline-scala-0140"
MANIFEST_RELATIVE = Path("evidence-delivery/v0.9.2-bifrost-v0144-01/ci-baseline-scala-0140/manifest.json")
PART_RELATIVE = Path(
    "evidence-delivery/v0.9.2-bifrost-v0144-01/ci-baseline-scala-0140/"
    "detail/bifrost-scala-kernel.json.gz.part00001"
)
DESTINATION_RELATIVE = Path(
    "reports/releases/v0.9.2/normal/attempts/"
    "bifrost-scala-kernel-attempt-02-series-02/bifrost-scala-kernel.json"
)
EXPECTED_BYTES = 56575
EXPECTED_SHA256 = "5f6350db340428b4d0c1865f312d6457077eb967a99ac3b966e6335fc09c8c46"


class RestoreBifrostV0144CIBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="bifrost-v0144-ci-baseline-")
        self.temp_root = Path(self.temporary.name)
        self.fixture_checkout = self.temp_root / "fixture-checkout"
        self.fixture_checkout.mkdir()
        (self.fixture_checkout / "scripts").mkdir()
        shutil.copy2(RESTORE_SCRIPT, self.fixture_checkout / "scripts" / RESTORE_SCRIPT.name)
        fixture_manifest = self.fixture_checkout / MANIFEST_RELATIVE
        fixture_part = self.fixture_checkout / PART_RELATIVE
        fixture_manifest.parent.mkdir(parents=True)
        fixture_part.parent.mkdir(parents=True)
        shutil.copy2(BUNDLE / "manifest.json", fixture_manifest)
        shutil.copy2(BUNDLE / "detail/bifrost-scala-kernel.json.gz.part00001", fixture_part)
        self.restore_root = self.temp_root / "target-checkout"
        self.restore_root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke_restore(self) -> subprocess.CompletedProcess[str]:
        script = self.fixture_checkout / "scripts" / RESTORE_SCRIPT.name
        return subprocess.run(
            [sys.executable, str(script), "--root", str(self.restore_root)],
            cwd=self.temp_root,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONPATH": ""},
        )

    def test_restores_exact_pinned_file_into_fresh_root(self) -> None:
        result = self.invoke_restore()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["status"], "restored")
        restored = (self.restore_root / DESTINATION_RELATIVE).read_bytes()
        self.assertEqual(len(restored), EXPECTED_BYTES)
        self.assertEqual(hashlib.sha256(restored).hexdigest(), EXPECTED_SHA256)

    def test_identical_existing_file_is_preserved_idempotently(self) -> None:
        first = self.invoke_restore()
        self.assertEqual(first.returncode, 0, first.stderr)
        destination = self.restore_root / DESTINATION_RELATIVE
        original_stat = destination.stat()
        original_bytes = destination.read_bytes()

        second = self.invoke_restore()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["status"], "already-present-identical")
        self.assertEqual(destination.read_bytes(), original_bytes)
        self.assertEqual(destination.stat().st_ino, original_stat.st_ino)

    def test_tampered_compressed_part_fails_before_writing_destination(self) -> None:
        part_path = self.fixture_checkout / PART_RELATIVE
        tampered = bytearray(part_path.read_bytes())
        tampered[0] ^= 0x01
        part_path.write_bytes(tampered)

        result = self.invoke_restore()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compressed part digest mismatch", result.stderr)
        self.assertFalse((self.restore_root / DESTINATION_RELATIVE).exists())

    def test_different_existing_file_is_rejected_and_preserved(self) -> None:
        destination = self.restore_root / DESTINATION_RELATIVE
        destination.parent.mkdir(parents=True)
        existing = b"pre-existing content must not be replaced\n"
        destination.write_bytes(existing)

        result = self.invoke_restore()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to replace different existing destination bytes", result.stderr)
        self.assertEqual(destination.read_bytes(), existing)


if __name__ == "__main__":
    unittest.main(verbosity=2)
