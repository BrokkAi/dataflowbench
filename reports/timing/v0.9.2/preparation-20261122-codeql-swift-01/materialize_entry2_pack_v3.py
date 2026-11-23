from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

REPO = Path.cwd()
BASE = REPO / "execution-state/timing-codeql-swift-repair-20261122-01"
REPORT = REPO / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01"
SOURCE = REPO / "execution-state/timing-runtime-20261114-01/codeql/packs/codeql/swift-all/6.8.5"
DEST_ROOT = BASE / "candidate-packs-entry2"
PACK = DEST_ROOT / "codeql/swift-all/6.8.5-dfb.entry2"
ATTEMPT = BASE / "entry2-materialization-attempt-01"
RECEIPT = REPORT / "entry2-pack-materialization-01.json"
PREREG = REPORT / "preregistration-entry2-pack-03.json"
PREFLIGHT_DIR = REPORT / "entry2-parser-preflight-01"
PREFLIGHT_RECEIPT = PREFLIGHT_DIR / "receipt.json"
PREFLIGHT_PATCH = PREFLIGHT_DIR / "filtered-generic-pack-sections.patch"
PREFLIGHT_RECEIPT_SHA = "58a6b7aba7dfcde89c97ed97ac647313a574b823294553e6eebf096226cc1d6e"
PREFLIGHT_PATCH_SHA = "f572e380c3c68b44145234ad51744d1bd5bcb209b747af3c54f9be13e7ffc540"
PATCH_DEADLINE_SECONDS = 60.0
FILES_PATH = REPO / "reports/releases/v0.9.2/qualification/codeql-swift-packs/candidate-packs-files-entry2.json"
TREE_PATH = REPO / "reports/releases/v0.9.2/qualification/codeql-swift-packs/candidate-packs-tree-entry2.json"
CHAIN_PATH = REPO / "adapters/codeql/v0.9.2/swift/patches/patch-chain.json"
GENERIC_PATCH = REPO / "adapters/codeql/swift-entry-extractor-v1/repair.patch"
LOCK_SOURCE = REPO / "adapters/codeql/v0.9.2/swift/queries/standard/codeql-pack.lock.yml"
FLOOR = 125 * 1024**3
PREFIX = "codeql/swift-all/6.8.5-dfb.entry2/"
GENERIC_PATCH_SHA = "e7da7352a8b3a8e7679760e49e8f8abff05d7fa3e16007c7ed2987f49074f26a"
FILES_SHA = "fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc"
TREE_SHA = "5b1dca82019e9d47a6aa6a38f1045d69422e4d627b04331205d418344388f431"
CHAIN_SHA = "35163ef1cdac52910390c570c8fc02ebe698cdfd1402d4e634c4f1d008698557"
LOCK_SHA = "5af1ed48732ec612914ce6a4911bf801419883ce72b9e6133a6871131aee696b"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def free_bytes() -> int:
    return shutil.disk_usage(REPO).free


def disk_observation(stage: str) -> int:
    free = free_bytes()
    record = {"observed_utc": now(), "stage": stage, "free_bytes": free, "floor_bytes": FLOOR, "floor_met": free >= FLOOR}
    with (ATTEMPT / "disk-observations.jsonl").open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return free


def disk_guard(stage: str) -> int:
    free = disk_observation(stage)
    if free < FLOOR:
        raise RuntimeError(f"disk floor breach before {stage}: {free} < {FLOOR}")
    return free


def run_patch(name: str, argv: list[str], cwd: Path) -> dict:
    free_before = disk_guard(name + ":before-start")
    sub = ATTEMPT / name
    sub.mkdir()
    stdout_path = sub / "stdout.txt"
    stderr_path = sub / "stderr.txt"
    started_utc = now()
    start_monotonic = time.monotonic()
    (sub / "command.json").write_text(json.dumps({"argv": argv, "cwd": str(cwd), "started_utc": started_utc, "disk_free_before_bytes": free_before, "disk_floor_bytes": FLOOR, "deadline_seconds": PATCH_DEADLINE_SECONDS}, indent=2) + "\n")
    timeout_reason = None
    termination_method = None
    process_reaped = None
    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=stdout_file, stderr=stderr_file)
        (sub / "process-start.json").write_text(json.dumps({"pid": proc.pid, "popen_started_utc": started_utc, "popen_start_monotonic": start_monotonic, "identity_scope": "direct Popen handle; no process-tree claim"}, indent=2) + "\n")
        while True:
            free_now = disk_observation(name + ":active")
            if free_now < FLOOR:
                timeout_reason = "disk_floor_breach"
                break
            exit_code = proc.poll()
            if exit_code is not None:
                process_reaped = True
                break
            if time.monotonic() - start_monotonic >= PATCH_DEADLINE_SECONDS:
                timeout_reason = "patch_deadline_exceeded"
                break
            time.sleep(1.0)
        if timeout_reason is not None and proc.poll() is None:
            try:
                proc.terminate()
                termination_method = "Popen.terminate on owned direct process handle"
            except Exception as exc:
                termination_method = f"Popen.terminate raised {type(exc).__name__}: {exc}"
            try:
                proc.wait(timeout=5.0)
                process_reaped = True
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    termination_method += "; then Popen.kill on same owned direct handle"
                except Exception as exc:
                    termination_method += f"; Popen.kill raised {type(exc).__name__}: {exc}"
                try:
                    proc.wait(timeout=5.0)
                    process_reaped = True
                except subprocess.TimeoutExpired:
                    process_reaped = False
        exit_code = proc.poll()
    free_after = disk_observation(name + ":after-terminal")
    term = {"finished_utc": now(), "exit_code": exit_code, "termination_reason": timeout_reason, "termination_method": termination_method, "process_reaped": process_reaped, "stdout_path": str(stdout_path.resolve()), "stderr_path": str(stderr_path.resolve()), "disk_free_after_bytes": free_after, "disk_floor_met_after": free_after >= FLOOR}
    (sub / "terminal.json").write_text(json.dumps(term, indent=2) + "\n")
    if timeout_reason is not None:
        raise RuntimeError(f"patch stage {name} stopped only through owned Popen handle after {timeout_reason}; preserving logs/output")
    if exit_code != 0:
        raise RuntimeError(f"patch stage {name} failed with {exit_code}; preserving all output")
    if free_after < FLOOR:
        raise RuntimeError(f"disk floor breached after patch stage {name}; preserving output")
    return {"name": name, **term}


if DEST_ROOT.exists() or ATTEMPT.exists() or RECEIPT.exists():
    raise SystemExit("preserving prior output; refusing to reuse candidate destination or attempt")
files_bytes = FILES_PATH.read_bytes()
tree_bytes = TREE_PATH.read_bytes()
chain_bytes = CHAIN_PATH.read_bytes()
generic_bytes = GENERIC_PATCH.read_bytes()
lock_bytes = LOCK_SOURCE.read_bytes()
preflight_bytes = PREFLIGHT_RECEIPT.read_bytes()
preflight_patch_bytes = PREFLIGHT_PATCH.read_bytes()
assert digest(PREFLIGHT_RECEIPT) == PREFLIGHT_RECEIPT_SHA
assert digest(PREFLIGHT_PATCH) == PREFLIGHT_PATCH_SHA
preflight_doc = json.loads(preflight_bytes)
assert preflight_doc["status"] == "verified-12-remapped-sections-and-frozen-hash-bindings"
assert preflight_doc["filtered_patch_sha256"] == PREFLIGHT_PATCH_SHA
prereg_doc = json.loads(PREREG.read_text())
assert prereg_doc["materializer_path"] == str(Path(__file__).resolve())
assert prereg_doc["materializer_sha256"] == digest(Path(__file__))
assert digest(FILES_PATH) == FILES_SHA
assert digest(TREE_PATH) == TREE_SHA
assert digest(CHAIN_PATH) == CHAIN_SHA
assert digest(GENERIC_PATCH) == GENERIC_PATCH_SHA
assert digest(LOCK_SOURCE) == LOCK_SHA
files_doc = json.loads(files_bytes)
tree_doc = json.loads(tree_bytes)
chain = json.loads(chain_bytes)
expected_files = {k[len(PREFIX):]: v for k, v in files_doc.items() if k.startswith(PREFIX)}
expected_tree = {k[len(PREFIX):]: v for k, v in tree_doc.items() if k.startswith(PREFIX)}
assert len(expected_files) == 1498 and set(expected_files) == set(expected_tree)
assert chain["result_pack"] == "codeql/swift-all@6.8.5-dfb.entry2"
assert chain["source_codeql_revision"] == "a7057b836bf29767461026718b14d20790b9085f"
assert chain["status"] == "ported-exact-accepted-common108-patch-set"
assert len(chain["pack_patch_set"]) == 4
assert free_bytes() >= FLOOR
assert SOURCE.is_dir() and not SOURCE.is_symlink()
assert not DEST_ROOT.exists()

ATTEMPT.mkdir()
start = {
    "schema": "codeql-entry2-pack-materialization-attempt/v1",
    "started_utc": now(),
    "disk_free_before_bytes": free_bytes(),
    "disk_floor_bytes": FLOOR,
    "disk_floor_met_before_dispatch": free_bytes() >= FLOOR,
    "source_pack": str(SOURCE.resolve()),
    "destination_pack": str(PACK.resolve()),
    "expected_files": 1498,
    "expected_symlinks": 0,
    "candidate_files_manifest": {"path": str(FILES_PATH.resolve()), "sha256": digest(FILES_PATH)},
    "candidate_tree_manifest": {"path": str(TREE_PATH.resolve()), "sha256": digest(TREE_PATH)},
    "patch_chain": {"path": str(CHAIN_PATH.resolve()), "sha256": digest(CHAIN_PATH)},
    "generic_patch": {"path": str(GENERIC_PATCH.resolve()), "sha256": digest(GENERIC_PATCH)},
    "parser_preflight_receipt": {"path": str(PREFLIGHT_RECEIPT.resolve()), "sha256": digest(PREFLIGHT_RECEIPT)},
    "parser_preflight_filtered_patch": {"path": str(PREFLIGHT_PATCH.resolve()), "sha256": digest(PREFLIGHT_PATCH)},
    "patch_deadline_seconds": PATCH_DEADLINE_SECONDS,
    "operations": ["copy stock Swift 6.8.5 pack into new isolated path", "rewrite qlpack version to 6.8.5-dfb.entry2", "apply only Swift QL library/schema hunks from tracked generic patch", "apply four tracked 6.8.5 ported pack patches", "copy exact tracked lock file", "restore two executable modes from frozen tree manifest", "verify exact path membership, SHA-256, modes and symlinks for all 1498 entries"],
    "prohibited": ["CodeQL CLI invocation", "pack install/download", "build", "analyzer", "modification of source runtime or frozen evidence"],
}
(ATTEMPT / "start.json").write_text(json.dumps(start, indent=2) + "\n")
phase_results = []
try:
    disk_guard("copy-before")
    copy_started = now()
    DEST_ROOT.mkdir()
    PACK.parent.mkdir(parents=True)
    shutil.copytree(SOURCE, PACK, symlinks=True, copy_function=shutil.copy2)
    copy_terminal = {"started_utc": copy_started, "finished_utc": now(), "status": "copied", "source": str(SOURCE.resolve()), "destination": str(PACK.resolve())}
    (ATTEMPT / "copy-terminal.json").write_text(json.dumps(copy_terminal, indent=2) + "\n")
    disk_guard("copy-after")

    # qlpack version suffix is frozen by the expected candidate file hash.
    disk_guard("qlpack-rewrite-before")
    qlpack = PACK / "qlpack.yml"
    ql_bytes = qlpack.read_bytes()
    expected_qlpack = expected_files["qlpack.yml"]
    assert ql_bytes.count(b"version: 6.8.5\n") == 1
    ql_bytes = ql_bytes.replace(b"version: 6.8.5\n", b"version: 6.8.5-dfb.entry2\n", 1)
    qlpack.write_bytes(ql_bytes)
    assert digest(qlpack) == expected_qlpack
    disk_guard("qlpack-rewrite-after")

    # Use the immutable 12-section patch already accepted by git apply --numstat preflight.
    generic_filtered = PREFLIGHT_PATCH
    generic_filtered_sha = digest(generic_filtered)
    assert generic_filtered_sha == PREFLIGHT_PATCH_SHA
    generic_result = run_patch("generic-patch-01", ["/usr/bin/patch", "--batch", "-F", "0", "-p1", "-i", str(generic_filtered.resolve())], DEST_ROOT)
    phase_results.append(generic_result)

    for i, patch_record in enumerate(chain["pack_patch_set"], 1):
        patch_path = REPO / patch_record["ported_patch"]
        assert digest(patch_path) == patch_record["ported_patch_sha256"]
        patch_result = run_patch(f"pack-patch-{i:02d}", ["/usr/bin/patch", "--batch", "-F", "0", "-p1", "-i", str(patch_path.resolve())], DEST_ROOT)
        phase_results.append({**patch_result, "patch_path": str(patch_path.resolve()), "patch_sha256": digest(patch_path), "patch_id": patch_record["id"]})

    disk_guard("lock-copy-before")
    lock_dest = PACK / "codeql-pack.lock.yml"
    assert not lock_dest.exists()
    shutil.copy2(LOCK_SOURCE, lock_dest)
    assert digest(lock_dest) == expected_files["codeql-pack.lock.yml"]
    disk_guard("lock-copy-after")

    # Apply only the exact modes frozen in the candidate tree manifest.
    disk_guard("mode-restore-before")
    mode_changes = []
    for rel, meta in expected_tree.items():
        p = PACK / rel
        assert p.is_file() and not p.is_symlink(), f"expected regular file missing before mode restore: {rel}"
        expected_mode = meta["mode"]
        actual_mode = stat.S_IMODE(p.stat().st_mode)
        if actual_mode != expected_mode:
            p.chmod(expected_mode)
            mode_changes.append({"path": rel, "before": actual_mode, "after": expected_mode})

    disk_guard("mode-restore-after")
    disk_guard("full-verification-before")
    actual = {}
    actual_symlinks = {}
    for current, dirs, names in os.walk(PACK, followlinks=False):
        base = Path(current)
        for name in list(dirs):
            p = base / name
            if p.is_symlink():
                rel = p.relative_to(PACK).as_posix()
                actual_symlinks[rel] = os.readlink(p)
                dirs.remove(name)
        for name in names:
            p = base / name
            rel = p.relative_to(PACK).as_posix()
            if p.is_symlink():
                actual_symlinks[rel] = os.readlink(p)
            elif p.is_file():
                actual[rel] = {"mode": stat.S_IMODE(p.stat().st_mode), "sha256": digest(p)}
    expected = {rel: {"mode": meta["mode"], "sha256": expected_files[rel]} for rel, meta in expected_tree.items()}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    hash_mode_diff = {rel: {"expected": expected[rel], "actual": actual.get(rel)} for rel in expected if actual.get(rel) != expected[rel]}
    actual_canonical = json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()
    actual_path = ATTEMPT / "actual-inventory.json"
    actual_path.write_text(json.dumps(actual, sort_keys=True, indent=2) + "\n")
    status = "verified-exact-1498-entry2-pack" if not missing and not extra and not hash_mode_diff and not actual_symlinks and len(actual) == 1498 else "verification-failed-preserved-output"
    free_after = disk_observation("full-verification-after")
    verification = {
        "status": status,
        "expected_entries": len(expected),
        "actual_regular_files": len(actual),
        "actual_symlinks": len(actual_symlinks),
        "missing_paths": missing,
        "extra_paths": extra,
        "hash_mode_mismatches": hash_mode_diff,
        "symlink_targets": actual_symlinks,
        "membership_exact": not missing and not extra and not actual_symlinks,
        "hashes_modes_exact": not hash_mode_diff,
        "actual_inventory_path": str(actual_path.resolve()),
        "actual_inventory_sha256": digest(actual_path),
        "actual_inventory_canonical_sha256": hashlib.sha256(actual_canonical).hexdigest(),
        "expected_files_manifest_sha256": digest(FILES_PATH),
        "expected_tree_manifest_sha256": digest(TREE_PATH),
        "mode_changes_applied": mode_changes,
        "disk_floor_bytes": FLOOR,
        "free_bytes_after": free_after,
        "disk_floor_met": free_after >= FLOOR,
    }
    (ATTEMPT / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    if status != "verified-exact-1498-entry2-pack" or free_after < FLOOR:
        raise RuntimeError("full exact manifest verification or disk floor failed; preserving output")
    final = {
        "schema": "codeql-entry2-pack-materialization-receipt/v1",
        **verification,
        "started_utc": start["started_utc"],
        "finished_utc": now(),
        "source_pack": str(SOURCE.resolve()),
        "candidate_pack": str(PACK.resolve()),
        "candidate_root": str(DEST_ROOT.resolve()),
        "candidate_pack_id": chain["result_pack"],
        "source_codeql_revision": chain["source_codeql_revision"],
        "generic_patch_path": str(GENERIC_PATCH.resolve()),
        "generic_patch_sha256": digest(GENERIC_PATCH),
        "generic_pack_sections": 12,
        "parser_preflight_receipt_path": str(PREFLIGHT_RECEIPT.resolve()),
        "parser_preflight_receipt_sha256": digest(PREFLIGHT_RECEIPT),
        "patch_deadline_seconds": PATCH_DEADLINE_SECONDS,
        "preregistration_path": str(PREREG.resolve()),
        "preregistration_sha256": digest(PREREG),
        "generic_filtered_patch_path": str(generic_filtered.resolve()),
        "generic_filtered_patch_sha256": generic_filtered_sha,
        "ported_pack_patches": [{"id": x["id"], "path": str((REPO/x["ported_patch"]).resolve()), "sha256": x["ported_patch_sha256"]} for x in chain["pack_patch_set"]],
        "lock_file_source": str(LOCK_SOURCE.resolve()),
        "lock_file_sha256": digest(LOCK_SOURCE),
        "patch_processes": phase_results,
        "attempt_directory": str(ATTEMPT.resolve()),
        "disk_free_before_bytes": start["disk_free_before_bytes"],
    }
    RECEIPT.write_text(json.dumps(final, indent=2) + "\n")
    (ATTEMPT / "terminal.json").write_text(json.dumps({"status": status, "finished_utc": final["finished_utc"], "receipt_path": str(RECEIPT.resolve()), "receipt_sha256": digest(RECEIPT)}, indent=2) + "\n")
    print(json.dumps({"status": status, "candidate_pack": str(PACK.resolve()), "entries": len(actual), "symlinks": len(actual_symlinks), "receipt": str(RECEIPT.resolve()), "receipt_sha256": digest(RECEIPT), "free_bytes_after": free_after, "mode_changes": mode_changes}, indent=2))
except Exception as exc:
    (ATTEMPT / "terminal.json").write_text(json.dumps({"status": "failed-preserved-output", "finished_utc": now(), "error_type": type(exc).__name__, "error": str(exc), "phase_results": phase_results, "destination_exists": DEST_ROOT.exists(), "free_bytes": free_bytes()}, indent=2) + "\n")
    raise
