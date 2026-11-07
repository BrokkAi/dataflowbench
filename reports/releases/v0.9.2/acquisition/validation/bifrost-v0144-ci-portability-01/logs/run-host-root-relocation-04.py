import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
FILES = [
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/test_native_qualifier.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/test_reconciliation_policy.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/test_archive_source_gate.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/fresh_worker_probe.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/test-fixtures/native-controls01-parent-started.json",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/test-fixtures/native-controls01-parent-started.provenance.json",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/native_qualifier.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/retained_resources.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/process_reconciliation.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/snapshot_query.py",
    "reports/releases/v0.9.2/acquisition/joern-native-controls-07/archive_evidence.py",
    "scripts/execute-release-v092.py",
    "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py",
    "scripts/swift_v2_process.py",
    "scripts/joern_normal_runner_v092.py",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/pending-execution-plan-01.json",
    "reports/releases/v0.9.2/qualification/joern-capability-repair-01/plan-v092-06/control-plan-01.json",
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-control-request-05.json",
    "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native06-archived-evidence-index-02.json",
]
PROBE = r'''
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
assert native_tests.REPO==checkout
assert reconciliation_tests.CHECKOUT_ROOT==checkout
assert archive_tests.REPO==checkout
assert not missing_root.exists()
historical_source=checkout/'reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-01/parent-started.json'
assert not historical_source.exists()
with mock.patch.object(n,'ROOT',missing_root):
    fixture=native_tests.NativeTests('runTest')
    fixture.root=fixture_root
    fixture.root.mkdir(parents=True)
    cfg,plan=fixture.fixture()
    assert plan['cases'] and cfg['pending_plan']['path']=='inputs/plan.json'
    suite=unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(archive_tests.ArchiveSourceGateTests))
    suite.addTests([
        native_tests.NativeTests('test_environment_platform_specific_cf_value_and_near_miss'),
        native_tests.NativeTests('test_actual_recorded_worker_arguments_all_remain_exact'),
        native_tests.FreshWorkerEnvironmentTests('test_actual_fresh_worker_platform_specific_environment'),
        native_tests.FreshWorkerEnvironmentTests('test_actual_fresh_worker_wrong_platform_value_rejected'),
        reconciliation_tests.ReconciliationPolicyTests('test_abi3_provider_provenance_and_coverage_are_strictly_validated'),
    ])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful()
assert not missing_root.exists()
print(json.dumps({'checkout_root':str(checkout),'simulated_missing_default_root':str(missing_root),
    'missing_historical_parent_started':True,'default_root_missing_during_tests':True,
    'fixture_root':str(fixture_root),'native_test_root':str(native_tests.REPO),
    'archive_test_root':str(archive_tests.REPO),'relocated_fresh_workers':True,
    'selected_checks_passed':True},sort_keys=True))
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


started = time.monotonic()
with tempfile.TemporaryDirectory(prefix="v092-relocated-tests-03-") as temporary:
    base = Path(temporary)
    checkout = base / "relocated-checkout"
    checkout.mkdir()
    for relative in FILES:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    probe = base / "host-root-relocation-probe-04.py"
    probe.write_text(PROBE)
    missing_root = base / "unavailable-original-host-root"
    fixture_root = base / "fixture-data"
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    environment.update(
        HOME=str(base / "home"),
        PATH="/usr/bin:/bin",
        TMPDIR=str(base / "tmp"),
    )
    (base / "home").mkdir()
    (base / "tmp").mkdir()
    argv = [sys.executable, "-B", "-E", str(probe), str(checkout), str(missing_root), str(fixture_root)]
    result = subprocess.run(argv, cwd=checkout, env=environment, capture_output=True, text=True)
    (OUT / "host-root-relocation-04.stdout.txt").write_text(result.stdout)
    (OUT / "host-root-relocation-04.stderr.txt").write_text(result.stderr)
    copied_files = [
        {
            "bytes": (checkout / relative).stat().st_size,
            "path": relative,
            "sha256": sha(checkout / relative),
        }
        for relative in FILES
    ]
    receipt = {
        "argv": argv,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "checkout_root": str(checkout),
        "copied_files": copied_files,
        "copied_total_bytes": sum(item["bytes"] for item in copied_files),
        "cwd": str(checkout),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "environment": {"HOME": "<temporary root>", "PATH": "/usr/bin:/bin", "PYTHONPATH": "unset", "TMPDIR": "<temporary root>"},
        "exit_code": result.returncode,
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "missing_historical_source_artifact": "qualification/.../native-controls-01/parent-started.json was not copied and was asserted absent",
        "phase": "relocated-checkout-portability-proof-with-fresh-worker-controls",
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "stdout_path": "logs/host-root-relocation-04.stdout.txt",
        "stderr_path": "logs/host-root-relocation-04.stderr.txt",
        "limitations": "Only 19 test/source/plan files were copied. No raw archive, engine, build, native controls, benchmark, source authority, or qualification action was run.",
    }
    (OUT.parent / "receipts" / "host-root-relocation-04.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    sys.exit(result.returncode)
