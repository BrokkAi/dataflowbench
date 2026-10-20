#!/usr/bin/env python3
import hashlib
import json
import re
import tarfile
from pathlib import Path

here = Path(__file__).resolve().parent
task_root = here.parent
source = task_root / "codeql-a7057b836bf29767461026718b14d20790b9085f"
archive = task_root / "codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz"
patch = Path(__file__).resolve().parents[4] / "adapters/codeql/swift-entry-extractor-v1/repair.patch"
source_prefix = "codeql-a7057b836bf29767461026718b14d20790b9085f/"

paths = []
for line in patch.read_text().splitlines():
    if line.startswith("diff --git a/"):
        match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
        if not match or match.group(1) != match.group(2):
            raise SystemExit(f"invalid diff header: {line}")
        paths.append(match.group(1))

rows = []
with tarfile.open(archive, "r:gz") as tar:
    for rel in paths:
        extracted = source / rel
        if not extracted.is_file():
            raise SystemExit(f"patched path missing: {rel}")
        current_sha = hashlib.sha256(extracted.read_bytes()).hexdigest()
        member_name = source_prefix + rel
        try:
            member = tar.getmember(member_name)
        except KeyError:
            baseline_sha = None
        else:
            stream = tar.extractfile(member)
            if stream is None:
                raise SystemExit(f"baseline member not readable: {rel}")
            baseline_sha = hashlib.sha256(stream.read()).hexdigest()
        if baseline_sha == current_sha:
            raise SystemExit(f"patch made no byte change to expected file: {rel}")
        rows.append({
            "path": rel,
            "baseline_sha256": baseline_sha,
            "patched_sha256": current_sha,
            "state": "added" if baseline_sha is None else "modified",
        })

if len(rows) != 19:
    raise SystemExit(f"expected 19 patch paths, found {len(rows)}")

result = {
    "source_commit": "a7057b836bf29767461026718b14d20790b9085f",
    "source_archive_sha256": "c737189f5f9f6a89eefabf2e82e6ecf9a2f866c4de2caf1f6407f69d143eae16",
    "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
    "expected_patch_paths": len(rows),
    "verified_changed_paths": len(rows),
    "paths": rows,
}
(here / "applied-patch.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in result if k != "paths"}, sort_keys=True))
