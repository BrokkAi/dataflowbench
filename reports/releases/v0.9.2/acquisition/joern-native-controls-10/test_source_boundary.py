"""Only the approved evaluator/supervisor scope changes; provider stays pinned."""
import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/'reports/releases/v0.9.2/acquisition'
def definitions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))}
class SourceBoundaryTests(unittest.TestCase):
    def test_qualifier_delta_is_limited_to_policy_scope_and_supervisor(self):
        before=definitions(BASE/'joern-native-controls-09/native_qualifier.py');after=definitions(BASE/'joern-native-controls-10/native_qualifier.py')
        self.assertEqual(set(after)-set(before),{'validate_semantic_policy'})
        self.assertFalse(set(before)-set(after))
        self.assertEqual({name for name in before if before[name]!=after[name]},
                         {'validate_request','validate_interval_evaluation','supervise','_run_worker_body'})
    def test_resources_query_and_archive_semantics_are_preserved(self):
        for name in ('retained_resources.py','snapshot_query.py'):
            self.assertEqual((BASE/'joern-native-controls-09'/name).read_bytes(),(BASE/'joern-native-controls-10'/name).read_bytes())
        old=(BASE/'joern-native-controls-09/archive_evidence.py').read_bytes()
        self.assertEqual(old.replace(b'joern-native-controls-09/archive_evidence.py',b'joern-native-controls-10/archive_evidence.py'),(BASE/'joern-native-controls-10/archive_evidence.py').read_bytes())
if __name__=='__main__':unittest.main()
