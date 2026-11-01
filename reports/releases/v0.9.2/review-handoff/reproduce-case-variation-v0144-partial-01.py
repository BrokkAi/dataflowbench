#!/usr/bin/env python3
"""Compare only terminal, completed C5 reports; retain failed/missing groups.

This is a separate partial audit, not a relaxed full-target gate. No engine is
started and the original full-20 audit is unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

FULL_HELPER_SHA = "ff0b7796d09f6134cbfc26a7771953f472edd4714d4e93edb815167652ee1206"
CONTRACT_PATH = "reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/contract-02.json"
CONTRACT_SHA = "1d2188df4e7bc7f5cc4e28cc0700a839a294b0cbecc484f4d9658bb5280164e4"
SOURCE = "61ae0cb817322ac81528217479c0be7bd760fa36"
PLAN = "6500465e02e28ac279047e610d7e8dbccc844ee8"


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    handoff = root / "reports/releases/v0.9.2/review-handoff"
    full_path = handoff / "reproduce-case-variation-v0144-01.py"
    assert sha(full_path) == FULL_HELPER_SHA
    assert sha(root / CONTRACT_PATH) == CONTRACT_SHA
    contract = json.loads((root / CONTRACT_PATH).read_text())
    projections = {x["id"]: x for x in contract["groups"]}
    full = load_module(full_path, "full_audit_helpers")
    assert full.sha(root / full.BASELINE) == full.BASELINE_SHA
    assert full.sha(root / full.PRIMITIVES) == full.PRIMITIVES_SHA
    primitive = load_module(root / full.PRIMITIVES, "sealed_audit_primitives")
    baseline = json.loads((root / full.BASELINE).read_text())
    old_rows, target = {}, {}
    digest, prefix = hashlib.sha256(), hashlib.sha256()
    count = 0
    for line in (root / full.LEDGER).open("rb"):
        count += 1
        digest.update(line)
        row = json.loads(line)
        if count <= 109:
            prefix.update(line)
            old_rows[row["attempt_id"]] = row
        elif row.get("target_id") == full.TARGET:
            assert row["group_id"] not in target, "multiple attempts require an explicit successor audit"
            target[row["group_id"]] = row
    assert prefix.hexdigest() == baseline["ledger"]["sha256"]
    expected = {x["group_id"] for x in baseline["report_refs"]}
    assert set(target) <= expected and len(expected) == 20
    cases, groups, incomplete = [], [], []
    for entry in baseline["report_refs"]:
        group = entry["group_id"]
        new_row = target.get(group)
        if new_row is None:
            incomplete.append({"group_id": group, "state": "not-started", "expected_rows": len(entry["report"]["case_ids"])})
            continue
        terminal = root / "reports/releases/v0.9.2/attempts" / new_row["attempt_id"] / "completed.json"
        assert json.loads(terminal.read_text()) == new_row
        assert new_row["source_commit"] == SOURCE and new_row["plan_commit"] == PLAN
        assert new_row["contract_sha256"] == CONTRACT_SHA
        assert new_row["argv"] == projections[group]["runtime_argv"]
        assert sorted(new_row["case_ids"]) == sorted(projections[group]["base_group"]["case_ids"])
        assert new_row["environment"]["BIFROST_OPEN_PACKS_DISABLE"] == "1"
        if new_row["status"] != "completed":
            assert new_row["status"] in {"failed", "timed-out", "capacity-lost", "recorder-error"}
            assert not new_row.get("reports"), "failed group cannot supply normalized completed rows"
            incomplete.append({"group_id": group, "attempt_id": new_row["attempt_id"],
                               "state": new_row["status"], "timed_out": new_row["timed_out"],
                               "exit_code": new_row["exit_code"], "capacity_loss": new_row["capacity_loss"],
                               "expected_rows": len(entry["report"]["case_ids"]),
                               "terminal": str(terminal.relative_to(root)), "terminal_sha256": full.sha(terminal)})
            continue
        old_row = old_rows[entry["attempt_id"]]
        for row in (old_row, new_row):
            assert row["status"] == "completed" and row["exit_code"] == 0
            assert row["timed_out"] is False and row["capacity_loss"] is None
            receipt = root / "reports/releases/v0.9.2/attempts" / row["attempt_id"] / "completed.json"
            assert json.loads(receipt.read_text()) == row and len(row["reports"]) == 1
            report = row["reports"][0]
            assert full.sha(root / report["staged_path"]) == report["staged_sha256"]
        old = primitive.report_bundle(root, old_row["attempt_id"], group)
        new = primitive.report_bundle(root, new_row["attempt_id"], group)
        full.enrich_proof_fields(root, old)
        full.enrich_proof_fields(root, new)
        assert old["report_tool_version"] == "bifrost 0.14.0"
        assert new["report_tool_version"] == "bifrost 0.14.4"
        assert old["report_case_ids"] == new["report_case_ids"] == sorted(entry["report"]["case_ids"])
        assert old["report_fixture_revision"] == new["report_fixture_revision"]
        for case in old["report_case_ids"]:
            item = primitive.compare_case(group, case, old["cases"][case], new["cases"][case], old["terminal_state"], new["terminal_state"])
            item["typed_finding_proof_changed"] = old["cases"][case]["typed_finding_proofs"] != new["cases"][case]["typed_finding_proofs"]
            item["typed_obligations_changed"] = old["cases"][case]["typed_obligations"] != new["cases"][case]["typed_obligations"]
            cases.append(item)
        groups.append({"group_id": group, "old": {k: v for k, v in old.items() if k != "cases"},
                       "new": {k: v for k, v in new.items() if k != "cases"},
                       "configuration_hash_equal": old["report_configuration_hash"] == new["report_configuration_hash"]})
    expected_paired = sum(len(x["report"]["case_ids"]) for x in baseline["report_refs"] if target.get(x["group_id"], {}).get("status") == "completed")
    assert len(cases) == expected_paired
    assert len(cases) + sum(x["expected_rows"] for x in incomplete) == 1116
    affected_ids = {"dfb-taint-java-exception-catch-negative", "dfb-taint-java-exception-catch-positive", "dfb-taint-kotlin-expression-positive", "dfb-taint-kotlin-loop-carried-positive"}
    transitions = Counter(x["old"]["verdict"] + "->" + x["new"]["verdict"] for x in cases)
    states = Counter(x["old"]["raw_state"] + "->" + x["new"]["raw_state"] for x in cases)
    result = {"schema": "v092-bifrost-v0144-partial-case-variation/v1", "target_id": full.TARGET,
              "status": "partial", "full_target_complete": False,
              "reproducer": {"path": str(Path(__file__).resolve().relative_to(root)), "sha256": sha(Path(__file__))},
              "imported_helpers": [{"path": str(full_path.relative_to(root)), "sha256": FULL_HELPER_SHA},
                                   {"path": full.PRIMITIVES, "sha256": full.PRIMITIVES_SHA}],
              "contract": {"path": CONTRACT_PATH, "sha256": CONTRACT_SHA, "source_commit": SOURCE, "plan_commit": PLAN},
              "baseline": {"path": full.BASELINE, "sha256": full.BASELINE_SHA},
              "ledger": {"path": full.LEDGER, "rows": count, "sha256": digest.hexdigest(), "original_109_row_prefix_sha256": prefix.hexdigest()},
              "completed_groups": len(groups), "target_groups": 20,
              "paired_report_rows": len(cases), "expected_full_report_rows": 1116,
              "distinct_paired_fixtures": len({x["case_id"] for x in cases}),
              "full_bifrost_distinct_fixtures": 1000, "full_population_fixtures": 1108,
              "incomplete_groups": incomplete, "verdict_transitions": dict(transitions),
              "raw_state_transitions": dict(states),
              "transition_classes": dict(Counter(x["transition_class"] for x in cases)),
              "four_prior_regression_fixtures": [x for x in cases if x["case_id"] in affected_ids],
              "limits": baseline["comparability_limits"] + [
                  "Only completed groups have paired normalized rows. Failed raw partial captures are not normalized or scored as completed cases.",
                  "All incomplete groups remain in the expected 1116-row denominator; no full-target or release-readiness claim follows.",
                  "Scala includes the PR298 dependency configuration change. Native activation evidence is versioned.",
                  "One release-target run is not an uncontended controlled performance comparison.",
                  "Raw state changes are distinct from case expectation correctness and engine-only causal attribution."],
              "groups": groups, "cases": cases}
    paths = [Path(str(args.output_prefix) + suffix) for suffix in (".json", ".csv", ".md")]
    assert all(not p.exists() and not p.is_symlink() for p in paths)
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
    with paths[0].open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with paths[1].open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["group_id", "case_id", "old_verdict", "new_verdict", "old_raw_state", "new_raw_state", "transition", "semantic_assessment"])
        for item in cases:
            writer.writerow([item["group_id"], item["case_id"], item["old"]["verdict"], item["new"]["verdict"], item["old"]["raw_state"], item["new"]["raw_state"], item["transition_class"], item["semantic_assessment"]])
    with paths[2].open("x") as stream:
        stream.write(f"# Partial Bifrost v0.14.0 to v0.14.4 comparison\n\n{len(groups)}/20 completed groups; {len(cases)}/1116 paired report rows.\n\n")
        stream.write("Verdict transitions: `" + json.dumps(dict(transitions), sort_keys=True) + "`.\n\n")
        stream.write("Incomplete groups: `" + json.dumps(incomplete, sort_keys=True) + "`.\n\n")
        for item in result["four_prior_regression_fixtures"]:
            stream.write(f"- {item['group_id']} / {item['case_id']}: {item['old']['verdict']} -> {item['new']['verdict']} ({item['new']['raw_state']}).\n")
        stream.write("\n" + "\n".join("- " + limit for limit in result["limits"]) + "\n")
        stream.write(f"\nFull JSON SHA256: `{full.sha(paths[0])}`.\nCSV SHA256: `{full.sha(paths[1])}`.\n")
    print(json.dumps({k: result[k] for k in ("status", "completed_groups", "paired_report_rows", "distinct_paired_fixtures", "incomplete_groups", "verdict_transitions", "raw_state_transitions")}))


if __name__ == "__main__":
    main()
