"""Pinning and historical-loader tests without loading or querying a native ABI4 dylib."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import time
import unittest

import snapshot_query as sq


class SnapshotQueryPinTests(unittest.TestCase):
    def _fake_module(self, directory: Path, *, abi: int) -> tuple[Path, str]:
        identity = sq.DARWIN_ABI4_PROVIDER_IDENTITY if abi == 4 else sq.DARWIN_ABI3_PROVIDER_IDENTITY
        source = (
            "ABI_VERSION = " + str(abi) + "\n"
            "class DarwinKernProcAllProvider:\n"
            "    identity = " + repr(identity) + "\n"
            "    def __init__(self, library_path, library_sha256, *, deadline):\n"
            "        self.identity = " + repr(identity) + "\n"
            "        self.library_sha256 = library_sha256.lower()\n"
            "    def native_table(self):\n"
            "        return [], {'provider_evidence': {'identity': self.identity, 'abi_version': " + str(abi) + ", 'library_sha256': self.library_sha256}}\n"
        ).encode()
        path = directory / ("provider-abi" + str(abi) + ".py")
        path.write_bytes(source)
        return path, hashlib.sha256(source).hexdigest()

    def test_missing_explicit_pins_fail_before_provider_work(self):
        with self.assertRaisesRegex(sq.SnapshotFailure, "explicit absolute module/dylib paths"):
            sq.PinnedDarwinNativeProvider(
                5.0, module_path=None, module_sha256=None,
                dylib_path=None, dylib_sha256=None,
            )

    def test_abi4_requires_the_exact_production_module_and_library_refs(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as directory_name:
            directory = Path(directory_name)
            module_path, module_sha = self._fake_module(directory, abi=4)
            dylib_path = directory / "provider.dylib"
            dylib_path.write_bytes(b"synthetic placeholder; never loaded")
            dylib_sha = hashlib.sha256(dylib_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(sq.SnapshotFailure, "exact approved refs"):
                sq.PinnedDarwinNativeProvider(
                    5.0, module_path=module_path, module_sha256=module_sha,
                    dylib_path=dylib_path, dylib_sha256=dylib_sha,
                )

    def test_abi3_legacy_loader_remains_synthetic_and_path_bound(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as directory_name:
            directory = Path(directory_name)
            module_path, module_sha = self._fake_module(directory, abi=3)
            dylib_path = directory / "provider.dylib"
            dylib_path.write_bytes(b"synthetic placeholder; never loaded")
            dylib_sha = hashlib.sha256(dylib_path.read_bytes()).hexdigest()
            provider = sq.PinnedDarwinNativeProvider(
                time.monotonic() + 5.0,
                module_path=module_path, module_sha256=module_sha,
                dylib_path=dylib_path, dylib_sha256=dylib_sha,
            )
            rows, coverage = provider.native_table()
            self.assertEqual(rows, [])
            evidence = coverage["provider_evidence"]
            self.assertEqual(evidence["module_source_sha256"], module_sha)
            self.assertEqual(evidence["module_source_path"], str(module_path))
            self.assertEqual(evidence["library_sha256"], dylib_sha)
            self.assertEqual(evidence["library_path"], str(dylib_path))

    def test_abi4_final_pins_match_provider_owner_receipt(self):
        self.assertEqual(
            sq.DARWIN_ABI4_PROVIDER_MODULE_SHA256,
            "b67c56a10e80d7d208c4bbd0f923f41bcc2a710943bf78b6c52881ef386c3158",
        )
        self.assertEqual(
            sq.DARWIN_ABI4_PROVIDER_LIBRARY_SHA256,
            "242d8ff705a1bd3bc8b8f397e5018828942c23bb2fc12701bfc68a8030ebe9e2",
        )


if __name__ == "__main__":
    unittest.main()
