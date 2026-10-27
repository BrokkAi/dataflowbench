#!/usr/bin/env python3
"""One bounded CodeQL Swift extractor build, with disk and process-group checks."""
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "codeql-a7057b836bf29767461026718b14d20790b9085f"
OUT = ROOT / "build-attempt-01"
BAZEL = ROOT / "downloads/bazel-9.0.0-darwin-arm64"
PATCH = Path(__file__).resolve().parents[3] / "adapters/codeql/swift-entry-extractor-v1/repair.patch"
APPLIED_PATCH_MANIFEST = ROOT / "patch-application/applied-patch.json"
TIMEOUT_SECONDS = 900
MIN_FREE_BYTES = 40 * 1024**3
PATCH_SHA256 = "e7da7352a8b3a8e7679760e49e8f8abff05d7fa3e16007c7ed2987f49074f26a"
BAZEL_SHA256 = "2c3cce548a4b6a97a2a5267712187b784b52714c4a2b0613e7386b15669d783c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def process_rows():
    raw = subprocess.run(
        ["/bin/ps", "-axo", "pid=,ppid=,pgid=,rss="],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    rows = []
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) == 4:
            rows.append(tuple(map(int, fields)))
    return rows


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n")


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def main():
    if OUT.exists():
        raise SystemExit(f"Refusing repeat attempt; output already exists: {OUT}")
    if not SOURCE.is_dir() or not BAZEL.is_file() or not os.access(BAZEL, os.X_OK):
        raise SystemExit("Source or executable Bazel input is missing")
    if sha256(PATCH) != PATCH_SHA256:
        raise SystemExit("repair.patch SHA-256 changed")
    manifest = json.loads(APPLIED_PATCH_MANIFEST.read_text())
    if (
        manifest.get("source_commit") != "a7057b836bf29767461026718b14d20790b9085f"
        or manifest.get("patch_sha256") != PATCH_SHA256
        or manifest.get("verified_changed_paths") != 19
    ):
        raise SystemExit("Exact-source patch application manifest is invalid")
    subprocess.run(
        ["git", "-C", str(SOURCE), "apply", "--reverse", "--check", "--binary", str(PATCH)],
        check=True,
        capture_output=True,
        text=True,
    )
    if sha256(BAZEL) != BAZEL_SHA256:
        raise SystemExit("Bazel 9.0.0 SHA-256 changed")
    expected_assets = {
        ROOT / "downloads/swift-prebuilt-macos.tar.zst": "f5fddabc442a5c7664be4f022f09889177f420477060c1199eb714394987ad93",
        ROOT / "downloads/resource-dir-macos.zip": "0589f8b61a87447d03b4b81b915f6b341ff8bcb123effda586cba46cc9487bd6",
    }
    for asset, expected_sha in expected_assets.items():
        if not asset.is_file() or sha256(asset) != expected_sha:
            raise SystemExit(f"Swift source-bound asset missing or changed: {asset}")
    if not (ROOT / "compiler-prebuilt/BUILD.bazel").is_file():
        raise SystemExit("compiler-prebuilt override BUILD file is missing")
    qlpack = (SOURCE / "swift/ql/lib/qlpack.yml").read_text()
    if "name: codeql/swift-all\nversion: 6.8.5\n" not in qlpack:
        raise SystemExit("Expected CodeQL 2.27.2 Swift QL pack 6.8.5")
    initial_free = shutil.disk_usage(ROOT).free
    if initial_free < MIN_FREE_BYTES:
        raise SystemExit(f"Preflight disk reserve failed: {initial_free} < {MIN_FREE_BYTES}")

    OUT.mkdir()
    tmp = ROOT / "tmp"
    xdg = ROOT / "xdg-cache"
    tmp.mkdir(exist_ok=True)
    xdg.mkdir(exist_ok=True)

    argv = [
        str(BAZEL),
        "--batch",
        f"--output_user_root={ROOT / 'bazel-cache'}",
        "--host_jvm_args=-Xmx2048m",
        "build",
        "//swift/extractor:extractor.real",
        "--jobs=2",
        "--local_resources=cpu=2",
        "--local_resources=memory=4096",
        f"--repository_cache={ROOT / 'repository-cache'}",
        f"--override_repository=swift-prebuilt-macos={ROOT / 'compiler-prebuilt'}",
        "--repo_env=CC=/Library/Developer/CommandLineTools/usr/bin/clang",
        "--repo_env=CXX=/Library/Developer/CommandLineTools/usr/bin/clang++",
        "--repo_env=DEVELOPER_DIR=/Library/Developer/CommandLineTools",
        "--action_env=DEVELOPER_DIR=/Library/Developer/CommandLineTools",
        "--repo_env=BAZEL_CXXOPTS=-std=c++20:-isysroot:/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
        "--repo_env=BAZEL_CONLYOPTS=-isysroot:/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
        "--repo_env=BAZEL_LINKOPTS=-isysroot:/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
        "--verbose_failures",
    ]
    env = os.environ.copy()
    env.update({"TMPDIR": str(tmp), "XDG_CACHE_HOME": str(xdg)})
    inherited_env_keys = sorted(env)
    env_fingerprint = hashlib.sha256(
        b"\0".join(f"{key}={env[key]}".encode() for key in inherited_env_keys)
    ).hexdigest()
    env_record = {
        "effective_environment_sha256": env_fingerprint,
        "explicit_overrides": {
            "TMPDIR": str(tmp),
            "XDG_CACHE_HOME": str(xdg),
        },
        "inherited_environment_keys": inherited_env_keys,
        "PATH": env.get("PATH"),
        "HOME": env.get("HOME"),
        "LANG": env.get("LANG"),
        "LC_ALL": env.get("LC_ALL"),
        "DEVELOPER_DIR": env.get("DEVELOPER_DIR"),
        "SDKROOT": env.get("SDKROOT"),
        "BAZEL_CXXOPTS": env.get("BAZEL_CXXOPTS"),
        "BAZEL_CONLYOPTS": env.get("BAZEL_CONLYOPTS"),
        "BAZEL_LINKOPTS": env.get("BAZEL_LINKOPTS"),
    }
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    command = {
        "source_commit": "a7057b836bf29767461026718b14d20790b9085f",
        "patch_sha256": PATCH_SHA256,
        "bazel_sha256": BAZEL_SHA256,
        "working_directory": str(SOURCE),
        "argv": argv,
        "environment": env_record,
        "disk_floor_bytes": MIN_FREE_BYTES,
        "timeout_seconds": TIMEOUT_SECONDS,
        "sandbox_and_include_checks": "Bazel defaults retained; no sandbox bypass, include-check bypass, or retries in argv",
        "started_at_utc": started_at,
    }
    write_json(OUT / "command.json", command)

    start = time.monotonic()
    min_free = initial_free
    peak_rss_kib = 0
    observed_pids = set()
    stop_reason = None
    monitor_error = None
    process = None
    exit_code = None
    with (OUT / "build.log").open("wb") as log:
        try:
            process = subprocess.Popen(
                argv,
                cwd=SOURCE,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=env,
            )
            while process.poll() is None:
                free = shutil.disk_usage(ROOT).free
                min_free = min(min_free, free)
                try:
                    rows = process_rows()
                except Exception as exc:  # Fail closed if monitoring becomes unavailable.
                    monitor_error = f"ps monitoring failed: {type(exc).__name__}: {exc}"
                    stop_reason = "monitor-failure"
                    break
                group = [row for row in rows if row[2] == process.pid]
                observed_pids.update(row[0] for row in group)
                peak_rss_kib = max(peak_rss_kib, sum(row[3] for row in group))
                if free < MIN_FREE_BYTES:
                    stop_reason = "disk-reserve"
                    break
                if time.monotonic() - start >= TIMEOUT_SECONDS:
                    stop_reason = "timeout"
                    break
                time.sleep(1)
            if stop_reason:
                stop_group(process)
            exit_code = process.wait()
        except Exception as exc:
            monitor_error = f"runner exception: {type(exc).__name__}: {exc}"
            if process is not None and process.poll() is None:
                stop_group(process)
                exit_code = process.wait()

    remaining = []
    try:
        rows = process_rows()
        remaining = [row for row in rows if process is not None and row[2] == process.pid]
    except Exception as exc:
        monitor_error = monitor_error or f"final ps monitoring failed: {type(exc).__name__}: {exc}"

    result = {
        "exit_code": exit_code,
        "stop_reason": stop_reason,
        "monitor_error": monitor_error,
        "elapsed_seconds": time.monotonic() - start,
        "initial_free_bytes": initial_free,
        "minimum_free_bytes": min_free,
        "observed_group_peak_rss_kib": peak_rss_kib,
        "tracked_pids": sorted(observed_pids),
        "remaining_process_group_rows": remaining,
        "cleanup_scope": "Bazel --batch process group; escaped descendants are not proven absent; no retries",
        "status": "build-success" if exit_code == 0 and not stop_reason and not monitor_error and not remaining else "build-failed-or-incomplete",
    }
    write_json(OUT / "result.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "build-success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
