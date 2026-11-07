import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
SUITE = "reports/releases/v0.9.2/acquisition/joern-native-controls-07"
SOURCES = [
    f"{SUITE}/fresh_worker_probe.py",
    f"{SUITE}/test_native_qualifier.py",
    f"{SUITE}/test_archive_source_gate.py",
    f"{SUITE}/test_reconciliation_policy.py",
    f"{SUITE}/native_qualifier.py",
    f"{SUITE}/test-fixtures/native-controls01-parent-started.json",
    f"{SUITE}/test-fixtures/native-controls01-parent-started.provenance.json",
]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


commands = [
    (
        "python313-cf-fixture-provider-05",
        [sys.executable, "-B", f"{SUITE}/darwin-provider/test_darwin_native_provider.py"],
    ),
    (
        "python313-cf-fixture-discovery-05",
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            SUITE,
            "-p",
            "test_*.py",
        ],
    ),
]

source_sha256_before = {path: digest(path) for path in SOURCES}
results = []
for name, argv in commands:
    started = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.monotonic() - started
    stdout_path = OUT / f"{name}.stdout.txt"
    stderr_path = OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout)
    stderr_path.write_text(result.stderr)
    count_match = re.search(r"Ran (\d+) tests?", result.stderr)
    results.append(
        {
            "argv": argv,
            "cwd": str(ROOT),
            "elapsed_seconds": round(elapsed, 3),
            "exit_code": result.returncode,
            "name": name,
            "stderr_bytes": len(result.stderr.encode()),
            "stderr_path": str(stderr_path.relative_to(OUT)),
            "stdout_bytes": len(result.stdout.encode()),
            "stdout_path": str(stdout_path.relative_to(OUT)),
            "unittest_count": int(count_match.group(1)) if count_match else None,
        }
    )

receipt = {
    "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    "commands": results,
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "phase": "fresh-worker-platform-environment-and-portable-historical-fixture",
    "platform": platform.platform(),
    "python_executable": sys.executable,
    "python_version": sys.version,
    "source_sha256_after": {path: digest(path) for path in SOURCES},
    "source_sha256_before": source_sha256_before,
    "limitations": "No engine, native controls, benchmark, build, source authority, or qualification action was run.",
}
(OUT.parent / "receipts" / "python313-cf-fixture-suite-05.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(receipt, indent=2, sort_keys=True))
sys.exit(0 if all(result["exit_code"] == 0 for result in results) else 1)
