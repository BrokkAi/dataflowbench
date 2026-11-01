import json, sys, unittest
from pathlib import Path
from unittest import mock
checkout=Path(sys.argv[1]).resolve()
missing_root=Path(sys.argv[2]).resolve()
fixture_root=Path(sys.argv[3]).resolve()
test_dir=checkout/'reports/releases/v0.9.2/acquisition/joern-native-controls-07'
sys.path[:0]=[str(test_dir),str(checkout)]
import native_qualifier as n
import test_native_qualifier as native_tests
import test_reconciliation_policy as reconciliation_tests
import test_archive_source_gate as archive_tests
assert Path(n.__file__).resolve().is_relative_to(checkout)
assert Path(native_tests.__file__).resolve().is_relative_to(checkout)
assert native_tests.REPO==checkout
assert reconciliation_tests.CHECKOUT_ROOT==checkout
assert archive_tests.REPO==checkout
assert not missing_root.exists()
with mock.patch.object(n,'ROOT',missing_root):
    fixture=native_tests.NativeTests('runTest')
    fixture.root=fixture_root
    fixture.root.mkdir(parents=True)
    cfg,plan=fixture.fixture()
    assert plan['cases'] and cfg['pending_plan']['path']=='inputs/plan.json'
    suite=unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(archive_tests.ArchiveSourceGateTests))
    suite.addTests([
        native_tests.NativeTests('test_env_real_derived_guarded_markers_and_near_misses'),
        native_tests.NativeTests('test_actual_recorded_worker_arguments_all_remain_exact'),
        reconciliation_tests.ReconciliationPolicyTests('test_abi3_provider_provenance_and_coverage_are_strictly_validated'),
    ])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful()
    for cls in (reconciliation_tests.ReconciliationPolicyTests,):
        assert Path(cls.executor_source.__file__).resolve().is_relative_to(checkout)
        assert Path(cls.controller_source.__file__).resolve().is_relative_to(checkout)
        assert Path(cls.process_source.__file__).resolve().is_relative_to(checkout)
print(json.dumps({'checkout_root':str(checkout),'missing_default_root':str(n.ROOT),'fixture_root':str(fixture_root),'native_module':str(Path(n.__file__).resolve()),'native_test_root':str(native_tests.REPO),'archive_test_root':str(archive_tests.REPO),'reconciliation_source_paths':[str(Path(reconciliation_tests.ReconciliationPolicyTests.executor_source.__file__).resolve()),str(Path(reconciliation_tests.ReconciliationPolicyTests.controller_source.__file__).resolve()),str(Path(reconciliation_tests.ReconciliationPolicyTests.process_source.__file__).resolve())],'selected_checks_passed':True},sort_keys=True))
