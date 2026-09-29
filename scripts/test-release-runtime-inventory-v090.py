#!/usr/bin/env python3
from pathlib import Path
import tempfile
import unittest
from release_runtime_inventory_v090 import inventory, verify

class InventoryTests(unittest.TestCase):
    def test_bytes_membership_and_external_links_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'runtime';root.mkdir();(root/'tool').write_bytes(b'one');external=base/'python';external.write_bytes(b'interpreter');(root/'python').symlink_to(external)
            with self.assertRaisesRegex(ValueError,'unregistered external'):
                inventory(root)
            recorded=inventory(root,[external]);self.assertTrue(verify(recorded))
            external.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'drift'):verify(recorded)
            external.write_bytes(b'interpreter');(root/'extra').write_bytes(b'new')
            with self.assertRaisesRegex(ValueError,'drift'):verify(recorded)

    def test_mode_changes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'tool';p.write_bytes(b'one');p.chmod(0o644);recorded=inventory(root);p.chmod(0o755)
            with self.assertRaisesRegex(ValueError,'drift'):verify(recorded)

if __name__=='__main__':unittest.main()
