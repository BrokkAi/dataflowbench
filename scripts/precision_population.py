"""Exact prospective additions, separate from historical input inventories.

Historical audits exclude only registered paths with matching metadata bytes.
The main validator additionally verifies every fixture digest and complete pair.
No historical population manifest or analyzer report is widened by this helper.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "populations/precision-gaps-v1.json"


def historical_paths(root, paths):
    entries = {entry["path"]: entry for entry in json.loads(INVENTORY.read_text())["cases"]}
    historical = set()
    for path in paths:
        relative = path.relative_to(root).as_posix()
        entry = entries.get(relative)
        if entry is None:
            historical.add(path)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"prospective precision case digest: {relative}")
    return historical
