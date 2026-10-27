#!/usr/bin/env python3
"""Bind the replayed Bifrost control review to the fixed 20 release groups."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    implementation = ROOT / "scripts/review-v092-bifrost-controls.py"
    spec = importlib.util.spec_from_file_location("bifrost_review_v092", implementation)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    review_path = ROOT / "reports/releases/v0.9.2/qualification/bifrost-review-01.json"
    retained = json.loads(review_path.read_bytes())
    if module.review() != retained:
        raise ValueError("retained Bifrost review differs from fresh evidence replay")
    parent_path = ROOT / "reports/releases/v0.9.0/execution-v1/contract.json"
    parent = json.loads(parent_path.read_bytes())
    groups = [row["id"] for row in parent["groups"] if row["tool"] == "bifrost"]
    if len(groups) != 20 or len(set(groups)) != 20:
        raise ValueError("historical Bifrost group scope changed")
    result = {
        "schema": "v092-bifrost-release-qualification/v1",
        "status": retained["status"],
        "execution_eligible": retained["execution_eligible"],
        "full_policy_qualification": False,
        "groups": groups,
        "tool": retained["tool"],
        "identity_components": retained["identity_components"],
        "control_review": {"path": str(review_path.relative_to(ROOT)), "sha256": sha(review_path)},
        "scope_source": {"path": str(parent_path.relative_to(ROOT)), "sha256": sha(parent_path)},
        "binding_implementation": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "limits": [
            "Three JavaScript policy controls remain inconclusive with partial discovery.",
            "Unbound endpoint controls are not evidence of cleanliness.",
            "The empty shipped native catalog remains not evaluated.",
            "Strict schema-5 qualification failed and remains preserved.",
            "Control eligibility is separate from completed release-group execution.",
        ],
    }
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print("Replayed 44 controls; bound the 20 historical Bifrost groups with known limits.")


if __name__ == "__main__":
    main()
