#!/usr/bin/env python3
"""Validate the exact 16-template Python taint-kernel population.

The Rust validator checks that every individual core key has one positive and
one negative. This narrow, analyzer-independent check additionally prevents a
Python port from silently omitting a template (or adding a second core
template under a different spelling).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_TEMPLATES = {
    "dfb-template-alias-propagation-separation",
    "dfb-template-argument-position-separation",
    "dfb-template-arithmetic-expression-propagation",
    "dfb-template-array-element-separation",
    "dfb-template-branch-join",
    "dfb-template-call-context-separation",
    "dfb-template-direct-propagation",
    "dfb-template-exception-catch",
    "dfb-template-infeasible-branch",
    "dfb-template-local-multi-step-chain",
    "dfb-template-local-overwrite-kill",
    "dfb-template-loop-carried-kill",
    "dfb-template-object-separation",
    "dfb-template-return-relay-one-hop",
    "dfb-template-return-relay-two-hop",
    "dfb-template-same-object-field-separation",
}


def fail(message: str) -> int:
    print(f"python kernel validation failed: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=Path("cases/taint/python"),
        help="Python case directory (default: cases/taint/python)",
    )
    args = parser.parse_args()

    paths = sorted(args.cases_root.rglob("case.json"))
    if not paths:
        return fail(f"no case.json files found beneath {args.cases_root}")

    cases = []
    ids = []
    for path in paths:
        try:
            case = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            return fail(f"{path}: cannot read JSON ({error})")
        if case.get("language") != "python" or case.get("track") != "taint":
            return fail(f"{path}: expected language=python and track=taint")
        if not isinstance(case.get("id"), str) or not case["id"]:
            return fail(f"{path}: case ID must be a non-empty string")
        cases.append((path, case))
        ids.append(case.get("id"))

    duplicate_ids = sorted(identifier for identifier, count in Counter(ids).items() if count != 1)
    if duplicate_ids:
        return fail(f"duplicate or missing case IDs: {duplicate_ids}")

    core = [(path, case) for path, case in cases if case.get("score_tier") == "core"]
    if len(core) != 2 * len(EXPECTED_TEMPLATES):
        return fail(
            f"expected {2 * len(EXPECTED_TEMPLATES)} Python core cases, found {len(core)}"
        )

    by_template = defaultdict(list)
    for path, case in core:
        by_template[case.get("template_id")].append((path, case))

    actual_templates = set(by_template)
    missing = sorted(EXPECTED_TEMPLATES - actual_templates)
    extra = sorted(actual_templates - EXPECTED_TEMPLATES)
    if missing or extra:
        return fail(f"template set mismatch (missing={missing}, extra={extra})")

    for template in sorted(EXPECTED_TEMPLATES):
        entries = by_template[template]
        polarities = Counter(case.get("polarity") for _, case in entries)
        if polarities != Counter({"positive": 1, "negative": 1}):
            locations = [str(path) for path, _ in entries]
            return fail(
                f"{template}: expected one positive and one negative; "
                f"found {dict(polarities)} in {locations}"
            )
        profiles = {case.get("model_profile") for _, case in entries}
        if profiles != {"benchmark-controlled"}:
            return fail(
                f"{template}: expected benchmark-controlled on both cases; "
                f"found {sorted(profiles)}"
            )

    print(
        f"validated Python semantic kernel: {len(EXPECTED_TEMPLATES)} templates, "
        f"{len(core)} core cases (one positive and one negative per template)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
