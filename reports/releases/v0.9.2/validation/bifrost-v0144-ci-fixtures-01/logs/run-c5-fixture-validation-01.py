import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
TEST_PATH = "scripts/test_bifrost_v0144_benchmark.py"
PRODUCTION_PATH = "scripts/bifrost_v0144_benchmark.py"
ORIGINAL_TEST_COMMIT = "579f2d3100a7865cc73bdaf47340c3056e48408a"
ORIGINAL_TEST_SHA256 = "2e740f8629a2731fa368cc62adde692b7f34236a64b3296a0ef9c276a2a73e1d"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_test_module():
    spec = importlib.util.spec_from_file_location("c5_unit_test_for_fixture_inventory", ROOT / TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import the C5 test module for the fixture inventory")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


test_module = load_test_module()
driver = test_module.driver
fixture_manifest = test_module.unit_fixture_manifest()
qualification = test_module.read_json(ROOT / driver.QUALIFICATION_DEFAULT)
capture_manifest = test_module.read_json(ROOT / f"{driver.CONTROL_CAPTURE_DEFAULT}/artifact-hashes.json")
independent_review = test_module.read_json(ROOT / driver.INDEPENDENT_REVIEW_DEFAULT)
required = {
    driver.CONTROL_REVIEW_DEFAULT,
    driver.INDEPENDENT_REVIEW_DEFAULT,
    driver.BIFROST_RECEIPT_DEFAULT,
    "reports/releases/v0.9.2/qualification/bifrost-v0144-01/review-bifrost-v0144-01.py",
    "reports/releases/v0.9.2/qualification/bifrost-v0144-01/control-comparison-diagnostic-01.json",
    "reports/releases/v0.9.2/qualification/bifrost-v0140-01/controls-attempt-01/artifact-hashes.json",
    "reports/releases/v0.9.2/qualification/bifrost-v0140-01/control-review-01.json",
    driver.NATIVE_EVIDENCE_PATHS["help_stdout"],
    f"{driver.CONTROL_CAPTURE_DEFAULT}/artifact-hashes.json",
    f"{driver.CONTROL_CAPTURE_DEFAULT}/commands.jsonl",
    f"{driver.CONTROL_CAPTURE_DEFAULT}/qualification.json",
    driver.HUMAN_AUTHORIZATION_DEFAULT,
    driver.BASE_PARENT_EXECUTION_REL,
    driver.LEDGER_REL,
    qualification["binding_implementation"]["path"],
}
required.update(f"{driver.CONTROL_CAPTURE_DEFAULT}/{item['path']}" for item in capture_manifest["files"])
required.update(independent_review["source_review"]["files"])
required.update(item["path"] for item in independent_review["evidence_refs"].values())
capture_prefix = driver.CONTROL_CAPTURE_DEFAULT + "/"
copy_paths = {
    path for path in required
    if path != driver.LEDGER_REL and not path.startswith(capture_prefix)
}
copy_paths.update({
    TEST_PATH,
    PRODUCTION_PATH,
    "scripts/execute-release-v092.py",
    driver.QUALIFICATION_DEFAULT,
    driver.BASE_PLAN_REL,
    driver.BASE_POPULATION_REL,
    driver.BASE_PARENT_EXECUTION_REL,
    driver.BASE_CONTRACT_REL,
    fixture_manifest["control_capture_archive"]["manifest_path"],
    fixture_manifest["control_capture_archive"]["part_path"],
})
unit_fixture_paths = sorted(
    path.relative_to(ROOT).as_posix()
    for path in test_module.UNIT_FIXTURE_ROOT.rglob("*")
    if path.is_file()
)
copy_paths.update(unit_fixture_paths)

tracked = set(subprocess.check_output(["git", "ls-files", "--full-name"], cwd=ROOT, text=True).splitlines())
untracked_inputs = sorted(path for path in copy_paths if path not in tracked)
untracked_non_fixture_inputs = sorted(set(untracked_inputs) - set(unit_fixture_paths))
if untracked_non_fixture_inputs:
    raise RuntimeError(f"lightweight checkout source set includes non-versioned inputs: {untracked_non_fixture_inputs}")

baseline_blob = subprocess.check_output(
    ["git", "show", f"{ORIGINAL_TEST_COMMIT}:{TEST_PATH}"], cwd=ROOT
)
baseline_digest = hashlib.sha256(baseline_blob).hexdigest()
if baseline_digest != ORIGINAL_TEST_SHA256:
    raise RuntimeError("original C5 test hash at the measured SOURCE commit differs")

paths_to_hash = [TEST_PATH, PRODUCTION_PATH, *unit_fixture_paths,
                 fixture_manifest["control_capture_archive"]["manifest_path"],
                 fixture_manifest["control_capture_archive"]["part_path"]]
source_sha256_before = {path: digest(ROOT / path) for path in paths_to_hash}
commands = []


def run(name, argv, cwd, environment=None):
    started = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, text=True)
    elapsed = time.monotonic() - started
    stdout_path = OUT / f"{name}.stdout.txt"
    stderr_path = OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout)
    stderr_path.write_text(result.stderr)
    combined = result.stdout + "\n" + result.stderr
    count = re.search(r"Ran (\d+) tests?", combined)
    commands.append({
        "argv": argv,
        "cwd": str(cwd),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": result.returncode,
        "name": name,
        "stderr_bytes": len(result.stderr.encode()),
        "stderr_path": str(stderr_path.relative_to(OUT)),
        "stdout_bytes": len(result.stdout.encode()),
        "stdout_path": str(stdout_path.relative_to(OUT)),
        "unittest_count": int(count.group(1)) if count else None,
    })
    return result.returncode


provider = 0
local_command = [sys.executable, "-B", TEST_PATH]
provider |= run("c5-unit-current-root-01", local_command, ROOT)

with tempfile.TemporaryDirectory(prefix="c5-lightweight-checkout-01-") as temporary:
    base = Path(temporary)
    checkout = base / "checkout"
    checkout.mkdir()
    copied_files = []
    for relative in sorted(copy_paths):
        source = ROOT / relative
        if source.is_symlink() or not source.is_file():
            raise RuntimeError(f"required lightweight-checkout input is missing or unsafe: {relative}")
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied_files.append({"path": relative, "bytes": target.stat().st_size, "sha256": digest(target)})

    forbidden_paths = [
        "execution-state/v092/tools/scala-maven-2.13.16/repository",
        driver.LEDGER_REL,
        driver.CONTROL_CAPTURE_DEFAULT,
    ]
    absent_before = [relative for relative in forbidden_paths if not (checkout / relative).exists()]
    if len(absent_before) != len(forbidden_paths):
        raise RuntimeError(f"ignored original C5 inputs unexpectedly copied: {forbidden_paths}")
    home = base / "home"
    tmp = base / "tmp"
    home.mkdir()
    tmp.mkdir()
    environment = {
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
    relocated_command = [sys.executable, "-B", TEST_PATH]
    provider |= run("c5-unit-relocated-checkout-01", relocated_command, checkout, environment)
    absent_after = [relative for relative in forbidden_paths if not (checkout / relative).exists()]
    if len(absent_after) != len(forbidden_paths):
        provider = 1
    relocation = {
        "checkout_root": str(checkout),
        "copied_file_count": len(copied_files),
        "copied_total_bytes": sum(item["bytes"] for item in copied_files),
        "copied_files": copied_files,
        "environment": {"HOME": "<temporary>", "TMPDIR": "<temporary>", "PATH": "/usr/bin:/bin", "PYTHONPATH": "unset"},
        "forbidden_original_inputs": forbidden_paths,
        "all_forbidden_inputs_absent_before_and_after": len(absent_before) == len(forbidden_paths) and len(absent_after) == len(forbidden_paths),
    }

receipt = {
    "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    "commands": commands,
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "original_test_source": {"commit": ORIGINAL_TEST_COMMIT, "sha256": baseline_digest},
    "phase": "v0144-c5-test-fixtures-portability",
    "python_executable": sys.executable,
    "python_version": sys.version,
    "platform": __import__("platform").platform(),
    "relocation": relocation,
    "source_sha256_after": {path: digest(ROOT / path) for path in paths_to_hash},
    "source_sha256_before": source_sha256_before,
    "limitations": "Offline unit tests only. No Bifrost/Joern/analyzer process, build, benchmark, or qualification was run; exact archived controls were extracted only into test temporary directories.",
}
receipt_path = OUT.parent / "receipts" / "c5-fixture-validation-01.json"
receipt_path.parent.mkdir(parents=True, exist_ok=True)
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
sys.exit(provider)
