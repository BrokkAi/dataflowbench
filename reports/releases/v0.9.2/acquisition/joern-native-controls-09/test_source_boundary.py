"""The interval successor changes only reviewed production boundaries."""
import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[5]
BASE=ROOT/'reports/releases/v0.9.2/acquisition'
def definitions(path):
 return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))}
class SourceBoundaryTests(unittest.TestCase):
 def test_qualifier_delta_is_limited_to_provider_policy_and_supervisor(self):
  before=definitions(BASE/'joern-native-controls-08/native_qualifier.py');after=definitions(BASE/'joern-native-controls-09/native_qualifier.py')
  self.assertEqual(set(after)-set(before),{'validate_interval_evaluation'})
  self.assertFalse(set(before)-set(after))
  changed={name for name in before if before[name]!=after[name]}
  self.assertEqual(changed,{'validate_native_provider','required_source_closure','validate_request','supervise'})
 def test_resource_and_archive_semantics_are_preserved(self):
  self.assertEqual((BASE/'joern-native-controls-08/retained_resources.py').read_bytes(),(BASE/'joern-native-controls-09/retained_resources.py').read_bytes())
  old=(BASE/'joern-native-controls-08/archive_evidence.py').read_bytes()
  self.assertEqual(old.replace(b'joern-native-controls-08/archive_evidence.py',b'joern-native-controls-09/archive_evidence.py'),(BASE/'joern-native-controls-09/archive_evidence.py').read_bytes())
if __name__=='__main__':unittest.main()
