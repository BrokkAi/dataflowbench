#!/usr/bin/env python3
import importlib.util
import json
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('verify_qualification', Path(__file__).with_name('verify-swift-v2-qualification.py'))
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class EvidenceTests(unittest.TestCase):
    def test_missing_modified_and_extra_artifacts_fail_closed(self):
        for mutation in ['missing', 'modified', 'extra']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); shutil.copytree(module.BASE, root / 'evidence'); base = root / 'evidence'
                path = base / 'codeql-native-source-attempt-01/database-create.command.json'
                if mutation == 'missing': path.unlink()
                elif mutation == 'modified': path.write_text(path.read_text() + '\n')
                else: (base / 'invented-result.json').write_text('{}')
                with self.assertRaises(ValueError): module.verify_files(base)

    def test_rehashed_evidence_cannot_promote_failure_or_activation(self):
        for name in ['summary.json', 'codeql-native-source-attempt-01/database-create.command.json']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary) / 'evidence'; shutil.copytree(module.BASE, base)
                path = base / name; data = json.loads(path.read_text())
                if name == 'summary.json': data['status'] = 'active'
                else: data['timed_out'] = False; data['exit_status'] = 0
                path.write_text(json.dumps(data))
                manifest_path = base / 'manifest.json'; manifest = json.loads(manifest_path.read_text())
                manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest(); manifest_path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError): module.verify(base)



if __name__ == '__main__': unittest.main()
