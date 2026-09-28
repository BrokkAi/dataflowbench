#!/usr/bin/env python3
"""Execution reuse mutations; no analyzer process and no historical file writes."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import joern_execution_revalidation_v1 as proof
from swift_normal_reports_v1 import ROOT,read,bound_file
from joern_normal_runner_v1 import admitted_cases


class ExecutionProof(unittest.TestCase):
    def setUp(self):
        self.amendment=read(ROOT/proof.AMENDMENT)
        self.old=bound_file(ROOT,self.amendment['registered_runner']).read_text()
        self.new=(ROOT/proof.EXECUTION).read_text()

    def test_twelve_arms_replay_and_explicit_unobserved_environment(self):
        result=proof.verify(ROOT)
        self.assertEqual(result['environment_limitations']['JAVA_OPTS'],'unobserved; registered-code equivalence only')
        self.assertEqual(result['environment_limitations']['aggregate_memory'],'unqualified')

    def test_exact_ast_rejects_env_heap_driver_frontend_query_arguments(self):
        for before,after in [('LANG=\'C\'','LANG=\'other\''),('-Xmx512m','-Xmx1024m'),("rt['compiler']","rt['frontend']"),('-swift-version','-other-version'),("rt['frontend']","rt['joern']"),('query.sc','different.sc'),('configPath=','otherPath='),('import os','import os as other'),("BASE='adapters/joern/swift-normal-v1'","BASE='elsewhere'"),('def compiler_argv(rt,case,directory):','def compiler_argv(rt,case,directory=None):')]:
            self.assertIn(before,self.new)
            with self.subTest(change=before),self.assertRaises(ValueError):proof.verify_ast(self.old,self.new.replace(before,after))

    def test_file_hash_drift_rejects_new_module_and_old_registered_source(self):
        original=proof.bound_file
        for key in ('registered_runner','execution_module'):
            reference=self.amendment[key]
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);target=root/reference['path'];target.parent.mkdir(parents=True);target.write_text('tampered')
                def redirected(base,ref):
                    return original(root if ref==reference else base,ref)
                with patch.object(proof,'bound_file',side_effect=redirected):
                    with self.assertRaisesRegex(ValueError,'digest'):proof.verify(ROOT)

    def test_recorded_inputs_reject_current_generator_or_environment_drift(self):
        for name in ('compiler_argv','frontend_argv','query_argv'):
            original=getattr(proof,name)
            def changed(*args):
                argv=original(*args);argv[0]='/foreign/launcher';return argv
            with self.subTest(generator=name),patch.object(proof,name,side_effect=changed):
                with self.assertRaisesRegex(ValueError,'invocation'):proof.verify(ROOT)
        original=proof.env_for
        def changed_env(rt):
            env=original(rt);env['JAVA_HOME']='/foreign/java';return env
        with patch.object(proof,'env_for',side_effect=changed_env):
            with self.assertRaisesRegex(ValueError,'environment changed'):proof.verify(ROOT)

    def test_missing_or_duplicate_admitted_ids_rejected(self):
        self.assertEqual(admitted_cases(['a','b']),{'a','b'})
        for value in (None,{},'a',['a','a'],[''],[1],[['a']]):
            with self.subTest(value=value),self.assertRaises(ValueError):admitted_cases(value)

    def test_prospective_plan_must_bind_reviewed_execution_bytes(self):
        from swift_normal_runner_v1 import ref
        reference=ref(ROOT,ROOT/proof.AMENDMENT)
        plan={'registered_at_unix_seconds':self.amendment['registered_at_unix_seconds']+1,'configurations':{'test':[self.amendment['execution_module'],*self.amendment['reviewed_files'],reference]}}
        proof.verify(ROOT,reference,plan)
        for path in (proof.EXECUTION,proof.AMENDMENT,'scripts/joern_normal_runner_v1.py'):
            bad=copy.deepcopy(plan)
            for r in bad['configurations']['test']:
                if r['path']==path:r['sha256']='0'*64
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'prospective'):proof.verify(ROOT,reference,bad)


if __name__=='__main__':unittest.main()
