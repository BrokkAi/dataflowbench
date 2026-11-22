from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
PATCH_SOURCE = Path.cwd() / "adapters/codeql/swift-entry-extractor-v1/repair.patch"
SOURCE_ROOT = BASE / "source-files"
CHECK = BASE / "patch-check-01"
ATTEMPT = CHECK / "attempt"
WORK = CHECK / "worktree"
RECEIPT = Path.cwd() / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01/three-source-patch-verification-01.json"
FILES = {
    "swift/extractor/SwiftExtractor.cpp": ("af2fb204c1b96e6a4b9de3a0e083cd816cb0ffaa1216c232c31f53edc430a98e", "0665c1c0f439db96208a45ce56632881ea3783bf8511a543e4dc910befde92c1"),
    "swift/extractor/infra/SwiftDispatcher.h": ("e71917ab9ff4ac157acc1f243c78c6e558597bedf2fc567af0e31b1e71c20487", "fec68616891ec3c2f46950897d043fa2d384539f4f021ac7158b918bcb920ae9"),
    "swift/extractor/translators/SwiftVisitor.h": ("15c70c2cc641d788662984f03485cea8d9b5b988ad114f47459d7ec700866a2a", "8108eaae7a697a1d7a75a70e6212d0954ade40e062cd53c09c28d74e803ef733"),
}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

if CHECK.exists() or RECEIPT.exists():
    raise SystemExit("preserving existing patch-check output; refusing to overwrite")
original = PATCH_SOURCE.read_bytes()
text = original.decode("utf-8")
chunks = text.split("diff --git ")[1:]
selected = []
for chunk in chunks:
    header = chunk.splitlines()[0]
    if any(header.startswith(f"a/{path} b/{path}") for path in FILES):
        selected.append("diff --git " + chunk)
selected_paths = [chunk.splitlines()[0].split()[1][2:] for chunk in selected]
if set(selected_paths) != set(FILES) or len(selected_paths) != 3:
    raise SystemExit(f"expected exactly three source-file patch sections, got {selected_paths}")
CHECK.mkdir()
ATTEMPT.mkdir()
WORK.mkdir()
partial_patch = CHECK / "three-source-files.patch"
partial_patch.write_text("".join(selected))
for rel, (before, _) in FILES.items():
    source = SOURCE_ROOT / rel
    if sha(source) != before:
        raise SystemExit(f"pre-patch source hash mismatch: {rel}")
    dest = WORK / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
argv = ["/usr/bin/patch", "--batch", "--fuzz=0", "-p1", "-i", str(partial_patch.resolve())]
started = now()
(ATTEMPT / "start.json").write_text(json.dumps({"started_utc": started, "argv": argv, "cwd": str(WORK.resolve()), "source_patch_path": str(PATCH_SOURCE.resolve()), "source_patch_sha256": sha(PATCH_SOURCE), "filtered_patch_path": str(partial_patch.resolve()), "filtered_patch_sha256": sha(partial_patch)}, indent=2) + "\n")
proc = subprocess.Popen(argv, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(ATTEMPT / "process-start.json").write_text(json.dumps({"pid": proc.pid, "popen_start_monotonic": time.monotonic()}, indent=2) + "\n")
stdout, stderr = proc.communicate(timeout=30)
(ATTEMPT / "stdout.txt").write_text(stdout)
(ATTEMPT / "stderr.txt").write_text(stderr)
results=[]
for rel,(before,after) in FILES.items():
    p=WORK/rel
    digest=sha(p)
    results.append({"path":rel,"before_sha256":before,"after_sha256":after,"observed_after_sha256":digest,"matches_expected_after":digest==after,"mode":oct(p.stat().st_mode & 0o777)})
status = "verified-three-patch-hunks-and-after-hashes" if proc.returncode==0 and all(x['matches_expected_after'] for x in results) else "patch-or-after-hash-failure"
terminal={"finished_utc":now(),"exit_code":proc.returncode,"status":status,"files":results,"stdout_path":str((ATTEMPT/'stdout.txt').resolve()),"stderr_path":str((ATTEMPT/'stderr.txt').resolve())}
(ATTEMPT/'terminal.json').write_text(json.dumps(terminal,indent=2)+"\n")
receipt={"schema":"codeql-swift-three-source-patch-verification/v1","status":status,"started_utc":started,"finished_utc":terminal['finished_utc'],"source_commit":"a7057b836bf29767461026718b14d20790b9085f","source_patch_path":str(PATCH_SOURCE.resolve()),"source_patch_sha256":sha(PATCH_SOURCE),"filtered_patch_path":str(partial_patch.resolve()),"filtered_patch_sha256":sha(partial_patch),"process_argv":argv,"process_exit_code":proc.returncode,"scope":"three source-file patch hunks applied to disposable exact-before-hash copies; no build or analyzer","files":results,"attempt_directory":str(ATTEMPT.resolve())}
if RECEIPT.exists(): raise SystemExit("receipt exists; refusing to overwrite")
RECEIPT.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({"status":status,"exit_code":proc.returncode,"receipt":str(RECEIPT.resolve()),"files":results},indent=2))
if status!="verified-three-patch-hunks-and-after-hashes": raise SystemExit(1)
