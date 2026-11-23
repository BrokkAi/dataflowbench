from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ATTEMPT = ROOT / "source-recovery-attempt-01"
REPO_URL = "https://raw.githubusercontent.com/github/codeql/a7057b836bf29767461026718b14d20790b9085f"
FILES = [
    ("swift/extractor/SwiftExtractor.cpp", "af2fb204c1b96e6a4b9de3a0e083cd816cb0ffaa1216c232c31f53edc430a98e"),
    ("swift/extractor/infra/SwiftDispatcher.h", "e71917ab9ff4ac157acc1f243c78c6e558597bedf2fc567af0e31b1e71c20487"),
    ("swift/extractor/translators/SwiftVisitor.h", "15c70c2cc641d788662984f03485cea8d9b5b988ad114f47459d7ec700866a2a"),
]

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

if ATTEMPT.exists():
    raise SystemExit(f"preserving existing attempt; refusing to reuse {ATTEMPT}")
ATTEMPT.mkdir()
(ATTEMPT / "start.json").write_text(json.dumps({"started_utc": utc_now(), "source_commit": REPO_URL.rsplit("/", 1)[-1], "files": [p for p, _ in FILES]}, indent=2) + "\n")
results = []
for rel, expected in FILES:
    dest = ROOT / "source-files" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise SystemExit(f"preserving existing output; refusing to overwrite {dest}")
    name = Path(rel).name
    out_path = ATTEMPT / f"{name}.stdout.txt"
    err_path = ATTEMPT / f"{name}.stderr.txt"
    cmd_path = ATTEMPT / f"{name}.command.json"
    term_path = ATTEMPT / f"{name}.terminal.json"
    url = f"{REPO_URL}/{rel}"
    argv = ["/usr/bin/curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "45", "--output", str(dest), "--write-out", "%{http_code}\\n%{url_effective}\\n%{size_download}\\n", url]
    started = utc_now()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cmd_path.write_text(json.dumps({"argv": argv, "url": url, "destination": str(dest), "started_utc": started, "pid": proc.pid, "popen_start_monotonic": time.monotonic()}, indent=2) + "\n")
    try:
        stdout, stderr = proc.communicate(timeout=50)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        stdout, stderr = proc.communicate()
        rc = proc.returncode if proc.returncode is not None else 124
        stderr += "\nlocal wrapper timeout after 50 seconds\n"
    out_path.write_text(stdout)
    err_path.write_text(stderr)
    digest = sha256(dest) if dest.is_file() else None
    terminal = {"finished_utc": utc_now(), "exit_code": rc, "http_code": stdout.splitlines()[0] if stdout else None, "effective_url": stdout.splitlines()[1] if len(stdout.splitlines()) > 1 else None, "size_download": stdout.splitlines()[2] if len(stdout.splitlines()) > 2 else None, "sha256": digest, "expected_before_patch_sha256": expected, "hash_matches": digest == expected, "destination_exists": dest.exists(), "stdout_path": str(out_path), "stderr_path": str(err_path)}
    term_path.write_text(json.dumps(terminal, indent=2) + "\n")
    results.append({"path": rel, **terminal})
    print(json.dumps({"path": rel, "exit_code": rc, "sha256": digest, "hash_matches": digest == expected, "http_code": terminal["http_code"]}))
    if rc != 0 or digest != expected:
        (ATTEMPT / "terminal.json").write_text(json.dumps({"status": "stopped-on-retrieval-or-hash-failure", "results": results}, indent=2) + "\n")
        raise SystemExit(1)
(ATTEMPT / "terminal.json").write_text(json.dumps({"status": "all-three-exact-source-files-recovered", "finished_utc": utc_now(), "results": results}, indent=2) + "\n")
