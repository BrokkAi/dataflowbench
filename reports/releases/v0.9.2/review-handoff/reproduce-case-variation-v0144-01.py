#!/usr/bin/env python3
"""Read-only reconciliation of all 20 new Bifrost groups against retained v0.14.0.

No analyzer is started. Existing outputs are never overwritten. Raw evidence
state changes are not automatically semantic correctness improvements.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

BASELINE = "reports/releases/v0.9.2/review-handoff/bifrost-v0144-baseline-01.json"
BASELINE_SHA = "5c8b366be1da3be2a84e0e9772f89e8102a432875ac178af4130318b6f89d406"
PRIMITIVES = "reports/releases/v0.9.2/review-handoff/reproduce-case-variation-18-01.py"
PRIMITIVES_SHA = "6f1fc80edd1921b4a038b0dfb599b936afb18ee61cd409fe5c37db0147d8857b"
LEDGER = "reports/releases/v0.9.2/ledger-v1.jsonl"
TARGET = "bifrost-v0144-01"


def sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(part)
    return result.hexdigest()


def enrich_proof_fields(root: Path, bundle: dict) -> None:
    for item in bundle["cases"].values():
        path = root / item["raw_path"]
        assert sha(path) == item["raw_sha256"]
        raw = json.loads(path.read_text())
        runs = raw.get("runs") or []
        assert len(runs) <= 1, "case comparison requires one policy run"
        run = runs[0] if runs else {}
        item["raw_schema_version"] = raw.get("schema_version")
        item["typed_run_completion"] = run.get("completion")
        item["typed_finding_proofs"] = [
            {key: finding.get(key) for key in ("certainty", "proof", "completeness")}
            for finding in run.get("findings", [])
        ]
        item["typed_obligations"] = run.get("obligations")
        item["top_omitted_diagnostics_lower_bound"] = raw.get("omitted_diagnostics_lower_bound")
        item["run_omitted_diagnostics_lower_bound"] = run.get("omitted_diagnostics_lower_bound")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    outputs = [Path(str(args.output_prefix) + suffix) for suffix in (".json", ".csv", ".md")]
    assert all(not p.exists() and not p.is_symlink() for p in outputs), "audit output already exists"
    assert sha(root / BASELINE) == BASELINE_SHA
    assert sha(root / PRIMITIVES) == PRIMITIVES_SHA
    baseline = json.loads((root / BASELINE).read_text())
    spec = importlib.util.spec_from_file_location("immutable_case_variation_primitives", root / PRIMITIVES)
    assert spec and spec.loader
    old_audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old_audit)
    original_rows = {}
    new_rows = {}
    prefix_digest = hashlib.sha256()
    ledger_digest = hashlib.sha256()
    line_count = 0
    for line in (root / LEDGER).open("rb"):
        line_count += 1
        ledger_digest.update(line)
        row = json.loads(line)
        if line_count <= 109:
            prefix_digest.update(line)
            original_rows[row["attempt_id"]] = row
        elif row.get("target_id") == TARGET:
            group = row["group_id"]
            assert group not in new_rows, "multiple new attempts require an explicit audit successor"
            new_rows[group] = row
    assert prefix_digest.hexdigest() == baseline["ledger"]["sha256"]
    expected_groups = {r["group_id"] for r in baseline["report_refs"]}
    assert len(expected_groups) == len(new_rows) == 20 and set(new_rows) == expected_groups
    cases = []
    groups = []
    for entry in baseline["report_refs"]:
        group = entry["group_id"]
        old_row = original_rows[entry["attempt_id"]]
        new_row = new_rows[group]
        for row in (old_row, new_row):
            assert row["status"] == "completed" and row["exit_code"] == 0
            assert not row["timed_out"] and row["capacity_loss"] is None
            terminal = root / "reports/releases/v0.9.2/attempts" / row["attempt_id"] / "completed.json"
            assert json.loads(terminal.read_text()) == row, "ledger differs from actual terminal receipt"
            assert len(row["reports"]) == 1
            report_ref = row["reports"][0]
            assert sha(root / report_ref["staged_path"]) == report_ref["staged_sha256"]
        old = old_audit.report_bundle(root, old_row["attempt_id"], group)
        new = old_audit.report_bundle(root, new_row["attempt_id"], group)
        enrich_proof_fields(root, old)
        enrich_proof_fields(root, new)
        assert old["report_tool_version"] == "bifrost 0.14.0"
        assert new["report_tool_version"] == "bifrost 0.14.4"
        assert old["report_case_ids"] == new["report_case_ids"] == sorted(entry["report"]["case_ids"])
        assert old["report_fixture_revision"] == new["report_fixture_revision"]
        for case in old["report_case_ids"]:
            row = old_audit.compare_case(group, case, old["cases"][case], new["cases"][case],
                                        old["terminal_state"], new["terminal_state"])
            row["typed_finding_proof_changed"] = old["cases"][case]["typed_finding_proofs"] != new["cases"][case]["typed_finding_proofs"]
            row["typed_obligations_changed"] = old["cases"][case]["typed_obligations"] != new["cases"][case]["typed_obligations"]
            cases.append(row)
        groups.append({"group_id": group, "old": {k: v for k, v in old.items() if k != "cases"},
                       "new": {k: v for k, v in new.items() if k != "cases"},
                       "configuration_hash_equal": old["report_configuration_hash"] == new["report_configuration_hash"],
                       "separate_configuration_change": group in {"bifrost-scala-kernel", "bifrost-java-native",
                                                                  "bifrost-javascript-native", "bifrost-python-native"}})
    assert len(cases) == 1116 and len({row["case_id"] for row in cases}) == 1000
    verdicts = Counter(row["old"]["verdict"] + "->" + row["new"]["verdict"] for row in cases)
    raw_states = Counter(row["old"]["raw_state"] + "->" + row["new"]["raw_state"] for row in cases)
    transitions = Counter(row["transition_class"] for row in cases)
    decisive_changes = [row for row in cases if row["verdict_changed"] or row["completion_changed"]]
    affected_ids = {"dfb-taint-java-exception-catch-negative", "dfb-taint-java-exception-catch-positive",
                    "dfb-taint-kotlin-expression-positive", "dfb-taint-kotlin-loop-carried-positive"}
    affected = [row for row in cases if row["case_id"] in affected_ids]
    limits = baseline["comparability_limits"] + [
        "1116 paired report rows include duplicates: 1000 distinct Bifrost fixture IDs within the fixed 1108-case population.",
        "Native activation evidence paths change by version; unsupported shipped-catalog cells remain typed separately.",
        "Raw evidence changes require separate case expectation and proof review before semantic improvement claims.",
        "This audit does not qualify Joern, the full release matrix or publication.",
    ]
    result = {"schema": "v092-bifrost-v0144-case-variation/v1", "target_id": TARGET,
              "baseline": {"path": BASELINE, "sha256": BASELINE_SHA},
              "primitives": {"path": PRIMITIVES, "sha256": PRIMITIVES_SHA},
              "ledger": {"path": LEDGER, "rows": line_count, "sha256": ledger_digest.hexdigest()},
              "groups": groups, "paired_report_rows": len(cases), "distinct_bifrost_fixtures": 1000,
              "fixed_population_cases": 1108, "verdict_transitions": dict(verdicts),
              "raw_state_transitions": dict(raw_states), "transition_classes": dict(transitions),
              "decisive_or_completion_changes": decisive_changes, "four_prior_regression_fixtures": affected,
              "limits": limits, "cases": cases}
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    with outputs[0].open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with outputs[1].open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["group_id", "case_id", "old_verdict", "new_verdict", "old_raw_state", "new_raw_state",
                         "old_findings", "new_findings", "transition", "semantic_assessment"])
        for row in cases:
            writer.writerow([row["group_id"], row["case_id"], row["old"]["verdict"], row["new"]["verdict"],
                             row["old"]["raw_state"], row["new"]["raw_state"], row["old"]["findings_count"],
                             row["new"]["findings_count"], row["transition_class"], row["semantic_assessment"]])
    with outputs[2].open("x") as stream:
        stream.write("# Bifrost v0.14.0 to v0.14.4 case variation\n\n")
        stream.write("20 groups; 1,116 paired report rows; 1,000 distinct Bifrost fixtures.\n\n")
        stream.write("Verdict transitions: `" + json.dumps(dict(verdicts), sort_keys=True) + "`.\n\n")
        stream.write("Raw state transitions: `" + json.dumps(dict(raw_states), sort_keys=True) + "`.\n\n")
        stream.write("## The four previously regressed fixtures\n\n")
        for row in affected:
            stream.write(f"- `{row['group_id']}` / `{row['case_id']}`: {row['old']['verdict']} / "
                         f"{row['old']['raw_state']} → {row['new']['verdict']} / {row['new']['raw_state']}.\n")
        stream.write("\n## Comparability limits\n\n")
        for limit in limits:
            stream.write("- " + limit + "\n")
        stream.write(f"\nFull JSON SHA-256: `{sha(outputs[0])}`.\n")
        stream.write(f"CSV SHA-256: `{sha(outputs[1])}`.\n")
    print(json.dumps({"groups": 20, "paired_rows": len(cases), "distinct_fixtures": 1000,
                      "verdict_transitions": dict(verdicts), "transition_classes": dict(transitions)}, sort_keys=True))


if __name__ == "__main__":
    main()
