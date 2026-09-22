#!/usr/bin/env python3
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('result_verify', Path(__file__).with_name('verify-swift-v2-result.py'))
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class ResultTests(unittest.TestCase):
    def test_missing_log_and_promoted_result_fail(self):
        for mutation in ['missing', 'promotion', 'invented-flow']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary) / 'evidence'; shutil.copytree(module.BASE, base)
                if mutation == 'missing':
                    (base / 'joern-result-positive-attempt-01/build.log').unlink()
                else:
                    name = 'summary.json' if mutation == 'promotion' else 'codeql-result-positive-attempt-01/flow.json'
                    path = base / name; data = json.loads(path.read_text())
                    if mutation == 'promotion': data['status'] = 'qualified'
                    else: data['#select']['tuples'] = [[{'label':'invented'}, 'flow']]
                    path.write_text(json.dumps(data))
                    mp = base / 'manifest.json'; manifest = json.loads(mp.read_text()); manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest(); mp.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError): module.verify(base)


if __name__ == '__main__': unittest.main()
