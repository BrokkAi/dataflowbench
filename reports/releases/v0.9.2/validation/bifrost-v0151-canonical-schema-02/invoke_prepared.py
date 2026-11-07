#!/usr/bin/env python3
"""Repair two path-argument types before the unchanged, prepared metadata gate.

This does not prepare a checkout or run an analyzer. The original source,
preparation, independent review, guards, Rust invocation and result writer stay
intact. Only its two producer-generated relative JSON path strings are adapted
to the PurePosixPath API expected by its existing reader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from types import ModuleType

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OLD_REL = "reports/releases/v0.9.2/validation/bifrost-v0151-canonical-schema-01/run_canonical.py"
OLD_SHA = "f05736416d36dc241adcf29bdfedbcfeccf996676e038b2fab6289f3d70daa6f"
PREPARED_SHA = "3a8eeec921440b23613e6272415962f9413ba026dd90a5f67fcddb44436c0f1e"
PREFIX = "reports/releases/v0.9.2/validation/bifrost-v0151-canonical-schema-01/diagnosis/"
STRING_PATHS = frozenset({PREFIX + "preparation-diagnosis.json", PREFIX + "baseline-diagnosis.json"})


def load_adapted(root: Path = ROOT) -> ModuleType:
    path = root / OLD_REL
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != OLD_SHA:
        raise ValueError("original reviewed helper bytes changed")
    legacy = ModuleType("v092_prepared_canonical_gate")
    legacy.__file__ = str(path)
    exec(compile(source, str(path), "exec"), legacy.__dict__)
    original_reader = legacy._read_json_under

    def typed_reader(repo_root, relative, description):
        if isinstance(relative, str):
            if relative not in STRING_PATHS:
                raise ValueError("unreviewed string path at legacy JSON reader")
            relative = PurePosixPath(relative)
        return original_reader(repo_root, relative, description)

    legacy._read_json_under = typed_reader
    return legacy


def require_committed_review() -> None:
    review_path = HERE / "independent-review-01.json"
    review = json.loads(review_path.read_bytes())
    if review.get("status") != "passed-for-root-integration-review" or review.get("findings") != []:
        raise ValueError("typed-path repair requires its independent review")
    for name in ("invoke_prepared.py", "test_invoke_prepared.py"):
        path = HERE / name
        if review["reviewed_sources_sha256"].get(name) != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("typed-path repair source differs from independent review")
    for path in (HERE / "invoke_prepared.py", HERE / "test_invoke_prepared.py", review_path):
        rel = path.relative_to(ROOT).as_posix()
        subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        if subprocess.check_output(["git", "status", "--porcelain=v1", "--", rel], cwd=ROOT):
            raise ValueError("typed-path repair and review must be committed and clean")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invoke", action="store_true", required=True)
    parser.parse_args()
    require_committed_review()
    legacy = load_adapted()
    result = legacy.invoke(ROOT, prepared_diagnosis_sha256=PREPARED_SHA)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "canonical-validation-passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
