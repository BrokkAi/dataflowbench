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


def run_patch(name: str, argv: list[str], cwd: Path) -> dict:
    sub = ATTEMPT / name
    sub.mkdir()
    started = now()
    (sub / "command.json").write_text(json.dumps({"argv": argv, "cwd": str(cwd), "started_utc": started}, indent=2) + "\n")
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    (sub / "process-start.json").write_text(json.dumps({"pid": proc.pid, "popen_start_monotonic": time.monotonic()}, indent=2) + "\n")
    while True:
        try:
            stdout, stderr = proc.communicate(timeout=45)
            break
        except subprocess.TimeoutExpired:
            # patch is owned; keep observing rather than killing it for slow output.
            continue
    (sub / "stdout.txt").write_text(stdout)
    (sub / "stderr.txt").write_text(stderr)
    term = {"finished_utc": now(), "exit_code": proc.returncode, "stdout_path": str((sub / "stdout.txt").resolve()), "stderr_path": str((sub / "stderr.txt").resolve())}
    (sub / "terminal.json").write_text(json.dumps(term, indent=2) + "\n")
    if proc.returncode != 0:
        raise RuntimeError(f"patch stage {name} failed with {proc.returncode}; preserving all output")
    return {"name": name, **term}


if DEST_ROOT.exists() or ATTEMPT.exists() or RECEIPT.exists():
    raise SystemExit("preserving prior output; refusing to reuse candidate destination or attempt")
files_bytes = FILES_PATH.read_bytes()
tree_bytes = TREE_PATH.read_bytes()
chain_bytes = CHAIN_PATH.read_bytes()
generic_bytes = GENERIC_PATCH.read_bytes()
lock_bytes = LOCK_SOURCE.read_bytes()
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
    "source_pack": str(SOURCE.resolve()),
    "destination_pack": str(PACK.resolve()),
    "expected_files": 1498,
    "expected_symlinks": 0,
    "candidate_files_manifest": {"path": str(FILES_PATH.resolve()), "sha256": digest(FILES_PATH)},
    "candidate_tree_manifest": {"path": str(TREE_PATH.resolve()), "sha256": digest(TREE_PATH)},
    "patch_chain": {"path": str(CHAIN_PATH.resolve()), "sha256": digest(CHAIN_PATH)},
    "generic_patch": {"path": str(GENERIC_PATCH.resolve()), "sha256": digest(GENERIC_PATCH)},
    "operations": ["copy stock Swift 6.8.5 pack into new isolated path", "rewrite qlpack version to 6.8.5-dfb.entry2", "apply only Swift QL library/schema hunks from tracked generic patch", "apply four tracked 6.8.5 ported pack patches", "copy exact tracked lock file", "restore two executable modes from frozen tree manifest", "verify exact path membership, SHA-256, modes and symlinks for all 1498 entries"],
    "prohibited": ["CodeQL CLI invocation", "pack install/download", "build", "analyzer", "modification of source runtime or frozen evidence"],
}
(ATTEMPT / "start.json").write_text(json.dumps(start, indent=2) + "\n")
phase_results = []
try:
    copy_started = now()
    DEST_ROOT.mkdir()
    PACK.parent.mkdir(parents=True)
    shutil.copytree(SOURCE, PACK, symlinks=True, copy_function=shutil.copy2)
    copy_terminal = {"started_utc": copy_started, "finished_utc": now(), "status": "copied", "source": str(SOURCE.resolve()), "destination": str(PACK.resolve())}
    (ATTEMPT / "copy-terminal.json").write_text(json.dumps(copy_terminal, indent=2) + "\n")

    # qlpack version suffix is frozen by the expected candidate file hash.
    qlpack = PACK / "qlpack.yml"
    ql_bytes = qlpack.read_bytes()
    expected_qlpack = expected_files["qlpack.yml"]
    assert ql_bytes.count(b"version: 6.8.5\n") == 1
    ql_bytes = ql_bytes.replace(b"version: 6.8.5\n", b"version: 6.8.5-dfb.entry2\n", 1)
    qlpack.write_bytes(ql_bytes)
    assert digest(qlpack) == expected_qlpack

    # The generic patch's pack-resident sections are only swift/ql/lib QL/schema files.
    prefix_out = "codeql/swift-all/6.8.5-dfb.entry2/"
    chunks = generic_bytes.decode("utf-8").split("diff --git ")[1:]
    selected = []
    for chunk in chunks:
        lines = chunk.splitlines(keepends=True)
        header = lines[0].strip().split()
        if len(header) != 4 or header[0] != "a/" and not header[0].startswith("a/"):
            continue
        a_path, b_path = header[2][2:], header[3][2:]
        is_schema = a_path == "swift/ql/lib/swift.dbscheme" and b_path == a_path
        is_library = a_path.startswith("swift/ql/lib/codeql/swift/") and b_path == a_path
        if not (is_schema or is_library):
            continue
        def mapped(path: str) -> str:
            if path == "swift/ql/lib/swift.dbscheme": return prefix_out + "swift.dbscheme"
            if path.startswith("swift/ql/lib/codeql/swift/"): return prefix_out + "codeql/swift/" + path[len("swift/ql/lib/codeql/swift/"):]
            raise AssertionError(path)
        mapped_a, mapped_b = mapped(a_path), mapped(b_path)
        transformed = []
        for line in lines:
            if line.startswith("diff --git "):
                transformed.append(f"diff --git a/{mapped_a} b/{mapped_b}\n")
            elif line.startswith("--- a/"):
                transformed.append(f"--- a/{mapped_a}\n")
            elif line.startswith("+++ b/"):
                transformed.append(f"+++ b/{mapped_b}\n")
            else:
                transformed.append(line)
        selected.append("".join(transformed))
    assert len(selected) == 12, f"expected 12 pack-resident generic patch sections, got {len(selected)}"
    generic_filtered = ATTEMPT / "generic-pack-sections.patch"
    generic_filtered.write_text("".join(selected))
    generic_filtered_sha = digest(generic_filtered)
    generic_result = run_patch("generic-patch-01", ["/usr/bin/patch", "--batch", "-F", "0", "-p1", "-i", str(generic_filtered.resolve())], DEST_ROOT)
    phase_results.append(generic_result)

    for i, patch_record in enumerate(chain["pack_patch_set"], 1):
        patch_path = REPO / patch_record["ported_patch"]
        assert digest(patch_path) == patch_record["ported_patch_sha256"]
        patch_result = run_patch(f"pack-patch-{i:02d}", ["/usr/bin/patch", "--batch", "-F", "0", "-p1", "-i", str(patch_path.resolve())], DEST_ROOT)
        phase_results.append({**patch_result, "patch_path": str(patch_path.resolve()), "patch_sha256": digest(patch_path), "patch_id": patch_record["id"]})

    lock_dest = PACK / "codeql-pack.lock.yml"
    assert not lock_dest.exists()
    shutil.copy2(LOCK_SOURCE, lock_dest)
    assert digest(lock_dest) == expected_files["codeql-pack.lock.yml"]

    # Apply only the exact modes frozen in the candidate tree manifest.
    mode_changes = []
    for rel, meta in expected_tree.items():
        p = PACK / rel
        assert p.is_file() and not p.is_symlink(), f"expected regular file missing before mode restore: {rel}"
        expected_mode = meta["mode"]
        actual_mode = stat.S_IMODE(p.stat().st_mode)
        if actual_mode != expected_mode:
            p.chmod(expected_mode)
            mode_changes.append({"path": rel, "before": actual_mode, "after": expected_mode})

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
    free_after = free_bytes()
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
