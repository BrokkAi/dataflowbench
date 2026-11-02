"""Exact ABI4 request/source/artifact guards, no library loading or OS queries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import native_qualifier as n


class ProviderSourceGuardTests(unittest.TestCase):
    def fixture(self):
        temporary=tempfile.TemporaryDirectory(prefix='abi4-source-guard-')
        self.addCleanup(temporary.cleanup)
        root=Path(temporary.name).resolve()
        def artifact(name,raw):
            path=root/name;path.write_bytes(raw)
            return {'path':name,'sha256':n.sha(raw)}
        provider={'abi_version':4,
            'module':artifact('provider.py',b'ABI_VERSION = 4\n'),
            'c_source':artifact('provider.c',b'/* fixture only */\n'),
            'header':artifact('provider.h',b'/* fixture only */\n'),
            'library':artifact('provider.dylib',b'fixture artifact; never loaded')}
        receipt={'schema':'v092-native-provider-build/v1',
            'source_files':{provider[k]['path']:provider[k]['sha256'] for k in ('module','c_source','header')},
            'library_sha256':provider['library']['sha256'],
            'library_bytes':len((root/provider['library']['path']).read_bytes()),
            'operations':[{'argv':['clang','-dynamiclib',provider['c_source']['path'],'-o',provider['library']['path']],'exit_code':0}]}
        provider['build_receipt']=artifact('build.json',n.canonical(receipt))
        source={r['path']:r for k,r in provider.items() if k!='abi_version'}
        return root,provider,source

    def test_exact_abi4_source_and_artifact_binding(self):
        root,p,s=self.fixture()
        checked=n.validate_native_provider(root,p,s)
        self.assertEqual(checked['module_sha256'],p['module']['sha256'])
        self.assertEqual(checked['library_sha256'],p['library']['sha256'])

    def test_old_abi_boolean_and_missing_source_are_rejected(self):
        root,p,s=self.fixture()
        for value in [3,True,5,'4']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                n.validate_native_provider(root,p|{'abi_version':value},s)
        with self.assertRaises(ValueError):
            n.validate_native_provider(root,p,{k:v for k,v in s.items() if k!=p['library']['path']})

    def test_module_declaration_cannot_be_rebound_to_abi3(self):
        root,p,s=self.fixture()
        raw=b'ABI_VERSION = 3\n';(root/p['module']['path']).write_bytes(raw)
        p['module']['sha256']=n.sha(raw);s[p['module']['path']]=copy.deepcopy(p['module'])
        with self.assertRaisesRegex(ValueError,'ABI declaration'):
            n.validate_native_provider(root,p,s)

    def test_library_and_receipt_bytes_are_not_accepted_from_unchecked_metadata(self):
        root,p,s=self.fixture()
        (root/p['library']['path']).write_bytes(b'changed library')
        with self.assertRaises(ValueError):n.validate_native_provider(root,p,s)


if __name__=='__main__':unittest.main()
