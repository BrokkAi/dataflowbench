#!/usr/bin/env python3
"""Recompute issue-213 coverage and recall without changing frozen reports."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/issues/213"


def load(path):
    return json.loads(path.read_text())


def ids(report):
    return {row["case_id"] for row in report["results"]}


def metrics(results, cases):
    outcomes = Counter(row["outcome"] for row in results)
    positive = [row for row in results if cases[row["case_id"]]["polarity"] == "positive"]
    eligible = [row for row in positive if row["outcome"] in ("reached", "not-reached")]
    reached = sum(row["outcome"] == "reached" for row in eligible)
    decisive = outcomes["reached"] + outcomes["not-reached"]
    return {
        "cells": len(results), "outcomes": dict(sorted(outcomes.items())),
        "decisive": decisive, "decisive_fraction": decisive / len(results),
        "positive_cells": len(positive), "decisive_positive_cells": len(eligible),
        "reached_positive_cells": reached,
        "positive_recall": reached / len(eligible) if eligible else None,
    }


def main():
    cases = {case["id"]: case for path in (ROOT / "cases").rglob("case.json")
             for case in [load(path)]}
    summary = {
        "scope": "retrospective correctness; no latency or replacement-freeze claim",
        "v071_commit": subprocess.check_output(
            ["git", "rev-parse", "v0.7.1^{commit}"], cwd=ROOT, text=True).strip(),
        "populations": {},
    }
    for language in ("c", "cpp"):
        name = f"codeql-{language}-kernel.json"
        frozen_path = ROOT / "reports" / name
        current_path = EVIDENCE / "rerun/reports" / name
        frozen, current = load(frozen_path), load(current_path)
        previous = json.loads(subprocess.check_output(
            ["git", "show", f"v0.7.1:reports/{name}"], cwd=ROOT))
        for field in ("fixture_revision", "configuration_hash", "tool_version",
                      "tool_build_identity"):
            if frozen[field] != current[field]:
                raise RuntimeError(f"{language}: changed {field}")
        if ids(frozen) != ids(current) or len(ids(current)) != len(current["results"]):
            raise RuntimeError(f"{language}: changed or duplicated population")
        for row in current["results"]:
            if row["outcome"] == "runner-error":
                raise RuntimeError(f"{language}: runner error: {row['case_id']}")
            raw = load(EVIDENCE / "rerun" / row["raw_output"])
            statuses = [n["properties"]["attributes"]["extraction_status"]
                        for run in raw["runs"] for invocation in run["invocations"]
                        for n in invocation.get("toolExecutionNotifications", [])
                        if n.get("descriptor", {}).get("id") == "cpp/bmn/extraction-information"]
            if len(statuses) != 1 or any(
                    status["#errors"] or status["#partial"] or status["#success"] != 1
                    or status["#total"] != 1 for status in statuses):
                raise RuntimeError(f"{language}: incomplete extraction: {row['case_id']}")
        shared = ids(previous) & ids(current)
        old_rows = [row for row in previous["results"] if row["case_id"] in shared]
        new_rows = [row for row in current["results"] if row["case_id"] in shared]
        old_outcomes = {row["case_id"]: row["outcome"] for row in old_rows}
        transitions = Counter(f"{old_outcomes[row['case_id']]} -> {row['outcome']}"
                              for row in new_rows)
        summary["populations"][language] = {
            "frozen_report_sha256": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
            "current_report_sha256": hashlib.sha256(current_path.read_bytes()).hexdigest(),
            "v080_frozen": metrics(frozen["results"], cases),
            "current": metrics(current["results"], cases),
            "shared_with_v071": {
                "previous": metrics(old_rows, cases), "current": metrics(new_rows, cases),
                "transitions": dict(sorted(transitions.items())),
            },
        }
    text = json.dumps(summary, indent=2) + "\n"
    (EVIDENCE / "summary.json").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
