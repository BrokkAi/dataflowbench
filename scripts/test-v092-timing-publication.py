#!/usr/bin/env python3
"""Focused portable publication-gate tests (bundle replay is verified separately)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v092_timing_publication as publication


REPO_ROOT = Path(__file__).resolve().parents[1]


class TimingPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retained_manifest = json.loads(
            (REPO_ROOT / publication.MANIFEST_REL).read_text(encoding="utf-8")
        )

    def make_portable_checkout(self, directory: Path) -> Path:
        """Copy only Git-bound source material; deliberately omit execution-state."""
        root = directory / "checkout"
        root.mkdir()
        relatives = {ref["path"] for ref in self.retained_manifest["source_refs"]}
        relatives.update(item["path"] for item in self.retained_manifest["downloads"])
        for rel in sorted(relatives):
            source = REPO_ROOT / rel
            destination = root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        self.assertFalse((root / "execution-state").exists())
        return root

    def test_clean_portable_checkout_prepares_and_stages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            prepared = publication.prepare(root)
            self.assertEqual(prepared["status"], "prepared")
            manifest = json.loads((root / publication.MANIFEST_REL).read_text(encoding="utf-8"))
            self.assertEqual(manifest["kind"], publication.KIND)
            self.assertEqual(manifest["release"]["commit"], publication.RELEASE_COMMIT)
            self.assertEqual(manifest["evidence"]["commit"], publication.EVIDENCE_COMMIT)
            self.assertEqual(len(manifest["downloads"]), 6)
            self.assertTrue(all(value is False for value in manifest["qualification"].values()))
            self.assertNotIn("snapshot_paths_relative_to", json.dumps(manifest))

            site = Path(temp) / "site-output"
            with patch.object(publication, "verify", return_value={"status": "verified"}) as verify:
                staged = publication.stage_site(root, site)
            verify.assert_called_once_with(root.resolve())
            self.assertEqual(staged["downloads"], 6)
            self.assertEqual((site / "manifest.json").read_bytes(),
                             (root / publication.MANIFEST_REL).read_bytes())
            for item in manifest["downloads"]:
                suffix = item["site_path"][len(publication.SITE_BASE):]
                destination = site.joinpath(*publication.PurePosixPath(suffix).parts)
                raw = destination.read_bytes()
                self.assertEqual(len(raw), item["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
                if item["path"].endswith("/files.jsonl.gz"):
                    # A .gz URL is transport-decoded by common static servers.
                    # Preserve the archive format and checksum for browser use.
                    self.assertTrue(item["site_path"].endswith("/files.jsonl.gz.bin"))
                    self.assertTrue(raw.startswith(b"\x1f\x8b"))

    def test_tampered_download_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            publication.prepare(root)
            path = root / publication.SUMMARY_REL
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(publication.PublicationError):
                publication.verify(root)

    def test_invented_certification_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            publication.prepare(root)
            path = root / publication.MANIFEST_REL
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["qualification"]["timing_certified"] = True
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(publication.PublicationError):
                publication.verify(root)

    def test_missing_raw_bundle_part_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            publication.prepare(root)
            (root / f"{publication.BUNDLE_BASE}/detail.tar.gz.part0000").unlink()
            with self.assertRaises(publication.PublicationError):
                publication.verify(root)

    def test_output_path_escape_is_rejected_before_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            publication.prepare(root)
            with patch.object(publication, "verify") as verify:
                with self.assertRaises(publication.PublicationError):
                    publication.stage_site(root, Path(temp) / ".." / "escaped")
            verify.assert_not_called()

    def test_different_existing_site_file_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="v092-publication-test-") as temp:
            root = self.make_portable_checkout(Path(temp))
            publication.prepare(root)
            site = Path(temp) / "site-output"
            site.mkdir()
            (site / "summary.json").write_text("unrelated", encoding="utf-8")
            with patch.object(publication, "verify", return_value={"status": "verified"}):
                with self.assertRaises(publication.PublicationError):
                    publication.stage_site(root, site)
            self.assertEqual((site / "summary.json").read_text(encoding="utf-8"), "unrelated")

    def test_duplicate_keys_and_non_finite_json_are_rejected(self) -> None:
        for raw in (b'{"path":"first","path":"second"}', b'{"time":NaN}', b'{"time":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(publication.PublicationError):
                publication._load_json(raw, "test input")


if __name__ == "__main__":
    unittest.main(verbosity=2)
