#!/usr/bin/env python3
"""Retain byte-verified copies with the repository lossless bundle format."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[4]
report = Path(__file__).resolve().parent
stage = root / "execution-state/timing-retention-20261113-02"
snapshot = stage / "snapshot"
snapshot.mkdir(parents=True, exist_ok=False)
files = {root / r["path"]: r["sha256"] for r in json.loads(
    (report / "reconciliation-v1/evidence-manifest.json").read_text())}
for campaign in ["20261113-01", "20261113-02"]:
    for path in (root / "reports/timing/v0.9.2" / campaign).rglob("*"):
        if path.is_file():
            assert not path.is_symlink(), path
            files[path] = hashlib.sha256(path.read_bytes()).hexdigest()
for name in ["scripts/v092_timing_campaign.py", "scripts/v092_timing_host.py",
             "scripts/test-v092-timing-campaign.py", "scripts/test-v092-timing-host.py",
             "scripts/evidence_bundle.py", "docs/v0.9.2-timing-supplement-20261113.md"]:
    path = root / name
    files[path] = hashlib.sha256(path.read_bytes()).hexdigest()
for path, expected in sorted(files.items()):
    target = snapshot / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, path
spec = importlib.util.spec_from_file_location("evidence_bundle", root / "scripts/evidence_bundle.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)
destination = report / "evidence-v1"
packed = bundle.pack(stage, "snapshot", destination, 40 * 1024 * 1024)
checked = bundle.check(destination)
receipt = {"schema": "timing-retention-receipt/v1", "originals_modified": False,
           "snapshot_prefix": "snapshot/", "snapshot_paths_relative_to": str(root),
           "pack": packed, "check": checked,
           "qualification": "delivery integrity only; does not certify benchmark evidence"}
(report / "retention-v1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({"retained_files": len(files), "bytes": packed["original_bytes"],
                  "bundle_parts": len(packed["parts"])}))
