#!/usr/bin/env python3
"""Audit retained controls without rerunning or qualifying incomplete analysis.

The original strict qualification remains failed. This review verifies whether
the captured runtime can be measured with the existing benchmark outcome rules,
including exact, baseline-witnessed limitations. It is not a clean-result gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "reports/releases/v0.9.1/qualification/attempt-01"
BASELINE = "reports/releases/v0.9.1/baseline-v0.9.0-freeze.json"
LIMITS = {
    "policy-javascript-declared-source-positive-with": "dfb-taint-javascript-model-declared-source-positive",
    "policy-javascript-declared-sink-positive-with": "dfb-taint-javascript-model-declared-sink-positive",
    "policy-javascript-declared-sink-negative-with": "dfb-taint-javascript-model-declared-sink-negative",
}
spec = importlib.util.spec_from_file_location("v013_qualification", Path(__file__).with_name("qualify-bifrost-v013.py"))
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def signature(report):
    """Compare semantic states, diagnostics and engagement, excluding timings."""
    run = report["runs"][0]
    return {
        "completion": run["completion"],
        "findings": [{key: finding.get(key) for key in ("certainty", "proof", "completeness")}
                     for finding in run["findings"]],
        "diagnostics": report["diagnostics"] + run["diagnostics"],
        "endpoints": [metric for metric in run["work"]["metrics"]
                      if metric["name"] in ("taint.compiled_source_endpoints", "taint.compiled_sink_endpoints")],
    }


def audit(root: Path = ROOT) -> dict:
    attempt = root / ATTEMPT
    manifest = load(attempt / "artifact-hashes.json")
    seen = set()
    for entry in manifest["files"]:
        relative = Path(entry["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe capture path")
        require(entry["path"] not in seen, "duplicate capture path")
        seen.add(entry["path"])
        path = attempt / relative
        require(path.is_file() and not path.is_symlink(), f"missing capture: {relative}")
        require(path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"],
                f"changed capture: {relative}")
    original = load(attempt / "qualification.json")
    require(original["qualification"] == "failed", "original failed qualification must remain failed")
    require(original["tool"]["version"] == qualifier.EXPECTED_VERSION and
            original["tool"]["build_identity"] == qualifier.EXPECTED_BUILD_IDENTITY and
            original["tool"]["sha256"] == qualifier.EXPECTED_BINARY_SHA256, "wrong runtime identity")
    commands = [json.loads(line) for line in (attempt / "commands.jsonl").read_text().splitlines()]
    by_id = {command["id"]: command for command in commands}
    expected = {}
    vacuous = set()
    for language in qualifier.LANGUAGES:
        for role in qualifier.ROLES:
            for polarity in qualifier.POLARITIES:
                for variant in ("with", "without"):
                    name = f"policy-{language}-declared-{role}-{polarity}-{variant}"
                    expected[name] = (language, int(polarity == "positive" and variant == "with"))
                    if variant == "without" or (role == "source" and polarity == "negative"):
                        vacuous.add(name)
        for case, variant, count in (
            ("sanitizer-kill-positive", "with", 1), ("sanitizer-kill-negative", "with", 0),
            ("sanitizer-kill-negative", "without", 1), ("sanitizer-selectivity-positive", "with", 1),
            ("sanitizer-selectivity-negative", "with", 0),
        ):
            expected[f"sanitizer-{language}-{case}-{variant}"] = (language, count)
    other = {"identity-version", "identity-build", "catalog-scan-list-builtin-policies",
             "catalog-list-policies", "native-python-source-sink-positive"}
    require(len(commands) == 44 and set(by_id) == set(expected) | other, "wrong control membership")
    for name, command in by_id.items():
        code = 2 if name in LIMITS else 0
        require(command["exit_code"] == code and command["status"] == ("failed" if code else "completed"),
                f"unexpected invocation state: {name}")
        for kind in ("stdout", "stderr"):
            path = attempt / kind / f"{name}.txt"
            require(digest(path) == command[f"{kind}_sha256"], f"changed command stream: {name}")
    require((attempt / "stdout/identity-version.txt").read_text().splitlines()[0] == "bifrost 0.13.0",
            "wrong witnessed version")
    require((attempt / "stdout/identity-build.txt").read_text().strip() == qualifier.EXPECTED_BUILD_IDENTITY,
            "wrong witnessed build")
    for name in ("catalog-scan-list-builtin-policies", "catalog-list-policies"):
        require(load(attempt / "stdout" / f"{name}.txt") == {"schema_version": 2, "packs": []},
                "unexpected embedded catalog")
    native = load(attempt / "stdout/native-python-source-sink-positive.txt")
    require(native == {"schema_version": 1, "status": "not-evaluated", "reason": "no-active-rule-packs", "findings": []},
            "native state is not typed no-rules-evaluated")
    freeze = load(root / BASELINE)
    baseline_entry = next(entry for entry in freeze["reports"] if entry["adapter"] == "bifrost-javascript-modeling")
    baseline_path = root / baseline_entry["path"]
    require(digest(baseline_path) == baseline_entry["normalized_report_sha256"], "changed frozen modeling report")
    baseline_rows = {row["case_id"]: row for row in load(baseline_path)["results"]}
    controls = []
    for name, (language, count) in sorted(expected.items()):
        path = attempt / "reports" / f"{name}.json"
        report = qualifier._load_report(path)
        require(digest(path) == by_id[name]["report_sha256"], f"changed command report: {name}")
        run = report["runs"][0]
        require(len(report["runs"]) == len(report["rules"]) == 1, f"wrong rule count: {name}")
        rule = report["rules"][0]
        for item in (rule, run):
            require(item["policy_id"] == f"dataflowbench.taint.model-{language}" and
                    item["analysis_type"] == "taint" and isinstance(item["policy_hash"], str) and
                    item["policy_hash"], f"wrong policy identity: {name}")
        require(rule["policy_hash"] == run["policy_hash"], f"rule/run policy hash differs: {name}")
        require(len(run["findings"]) == count, f"unexpected finding count: {name}")
        require(not report["diagnostics_truncated"] and not run["diagnostics_truncated"], "truncated diagnostics")
        result = {"id": name, "report_sha256": digest(path), "completion": run["completion"], "findings": count}
        if name in LIMITS:
            case_id = LIMITS[name]
            row = baseline_rows[case_id]
            require(row["outcome"] == "inconclusive", "baseline limit was scored as conclusive")
            old_path = root / row["raw_output"]
            raw_entry = next(entry for entry in baseline_entry["raw_evidence"] if entry["case_id"] == case_id)
            require(digest(old_path) == raw_entry["sha256"], "changed frozen raw evidence")
            require(signature(report) == signature(load(old_path)), f"known limitation changed: {name}")
            require(run["completion"] == {"type": "inconclusive", "reasons": ["partial_discovery"]}, "wrong limit state")
            result.update(interpretation="inconclusive", clean=False, baseline_raw=raw_entry)
        elif name in vacuous:
            diagnostics = report["diagnostics"] + run["diagnostics"]
            require(run["completion"] == {"type": "complete"} and len(diagnostics) == 1, "wrong empty-selection state")
            note = diagnostics[0]
            require(note["code"] == {"type": "empty_selection"} and note["severity"] == "note" and
                    note["impact"] == "advisory" and note["family"] == "empty_selection", "unexpected diagnostic")
            endpoints = signature(report)["endpoints"]
            require(len(endpoints) == 2 and any(metric["value"] == 0 for metric in endpoints), "empty-selection lacks endpoint evidence")
            result.update(interpretation="unbound-endpoint", clean=False)
        else:
            qualifier._validate_policy_report(path, language=language, expected_findings=count)
            endpoints = signature(report)["endpoints"]
            require(len(endpoints) == 2 and all(metric["value"] > 0 for metric in endpoints), "complete result lacks endpoints")
            result.update(interpretation="proven-flow" if count else "complete-no-finding")
        controls.append(result)
    return {
        "schema": "bifrost-v013-control-review/v1",
        "measurement_contract": "verified-with-known-limits",
        "full_policy_qualification": False,
        "original_qualification": {"path": f"{ATTEMPT}/qualification.json", "sha256": digest(attempt / "qualification.json"), "status": "failed"},
        "capture_manifest": {"path": f"{ATTEMPT}/artifact-hashes.json", "sha256": digest(attempt / "artifact-hashes.json")},
        "baseline_freeze": {"path": BASELINE, "sha256": digest(root / BASELINE)},
        "tool": original["tool"],
        "native": {"interpretation": "not-evaluated", "clean": False, "document": native},
        "invocations": 44,
        "complete_policy_runs": 36,
        "inconclusive_policy_runs": 3,
        "unbound_endpoint_controls": 15,
        "sanitizer_controls": 15,
        "controls": controls,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    with args.output.open("x") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("44 retained invocations audited; full policy qualification remains false")
