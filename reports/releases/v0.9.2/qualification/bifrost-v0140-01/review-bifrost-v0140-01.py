#!/usr/bin/env python3
"""Review schema-6 control evidence without changing the failed strict attempt.

The existing findings, engagement, sanitizer and completeness checks still
apply. Three explicitly scoped JavaScript partial-discovery runs remain
inconclusive; stronger finding proofs never turn their runs into clean results.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ATTEMPT = "reports/releases/v0.9.2/qualification/bifrost-v0140-01/controls-attempt-01"


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def review():
    pins = {
        "scripts/qualify-bifrost-v013.py": "e6ac256769b2f01a3bed30ddcb2b7f15d00fa090fb0cc6dee66414854cf67582",
        "scripts/review-v092-bifrost-controls.py": "72634398c97e6aa1c0616cf9497322da8d854a75781119dffe6730b33aee73d2",
    }
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "review dependency changed: " + path)
    prior = module("v092_prior_review", "review-bifrost-v013-controls.py")
    controls = prior.qualifier
    controls.REPORT_SCHEMA_VERSION = 6
    attempt = ROOT / ATTEMPT
    manifest = load(attempt / "artifact-hashes.json")
    seen = set()
    for row in manifest["files"]:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe capture path")
        require(row["path"] not in seen, "duplicate capture")
        seen.add(row["path"])
        path = attempt / relative
        require(path.is_file() and not path.is_symlink(), "missing capture")
        require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], "capture changed")
    original = load(attempt / "qualification.json")
    acquisition = load(ROOT / "reports/releases/v0.9.2/qualification/bifrost-v0140-01/acquisition.json")
    identity = {**acquisition["binary"], "path": acquisition["binary_absolute_path"], "public_tag_commit": acquisition["public_tag_commit"]}
    require(original["qualification"] == "failed", "strict attempt must stay failed")
    require(original["tool"]["version"] == "0.14.0" and
            original["tool"]["build_identity"] == "c11a13ffa03ebea154f587b899954e412b5b871e" and
            original["tool"]["sha256"] == identity["sha256"], "wrong binary identity")
    require(identity["sha256"] == "fc9a2a4cff4e73b91a1b4e15f403bf572052bc796a362440e347336be46385e6" and
            identity["public_tag_commit"] == "0d713d9a1582e9e6fdef75f3b27027409bd7ec19", "official artifact changed")
    require(sha(Path(identity["path"])) == identity["sha256"], "binary changed")
    commands = [json.loads(line) for line in (attempt / "commands.jsonl").read_text().splitlines()]
    by_id = {row["id"]: row for row in commands}
    expected, vacuous = {}, set()
    for language in controls.LANGUAGES:
        for role in controls.ROLES:
            for polarity in controls.POLARITIES:
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
    require(len(commands) == len(by_id) == 44 and set(by_id) == set(expected) | other, "control membership changed")
    for name, row in by_id.items():
        code = 2 if name in prior.LIMITS else 0
        require(row["exit_code"] == code and row["status"] == ("failed" if code else "completed"), "unexpected control status: " + name)
        require(row["environment"].get("BIFROST_OPEN_PACKS_DISABLE") == "1", "external acquisition enabled")
        for stream in ("stdout", "stderr"):
            require(sha(attempt / stream / (name + ".txt")) == row[stream + "_sha256"], "stream changed")
    require((attempt / "stdout/identity-version.txt").read_text().splitlines()[0] == "bifrost 0.14.0", "wrong version banner")
    require((attempt / "stdout/identity-build.txt").read_text().strip() == original["tool"]["build_identity"], "wrong build banner")
    for name in ("catalog-scan-list-builtin-policies", "catalog-list-policies"):
        require(load(attempt / "stdout" / (name + ".txt")) == {"schema_version": 2, "packs": []}, "shipped catalog changed")
    native = load(attempt / "stdout/native-python-source-sink-positive.txt")
    require(native == {"schema_version": 1, "status": "not-evaluated", "reason": "no-active-rule-packs", "findings": []}, "native no-rules state changed")
    freeze = load(ROOT / prior.BASELINE)
    baseline_entry = next(row for row in freeze["reports"] if row["adapter"] == "bifrost-javascript-modeling")
    baseline_path = ROOT / baseline_entry["path"]
    require(sha(baseline_path) == baseline_entry["normalized_report_sha256"], "baseline report changed")
    baseline_rows = {row["case_id"]: row for row in load(baseline_path)["results"]}
    reviewed = []
    for name, (language, count) in sorted(expected.items()):
        path = attempt / "reports" / (name + ".json")
        report = controls._load_report(path)
        require(sha(path) == by_id[name]["report_sha256"], "report changed")
        require(len(report["runs"]) == len(report["rules"]) == 1, "wrong rule/run count")
        run, rule = report["runs"][0], report["rules"][0]
        for item in (run, rule):
            require(item["policy_id"] == f"dataflowbench.taint.model-{language}" and item["analysis_type"] == "taint" and item["policy_hash"], "policy identity changed")
        require(run["policy_hash"] == rule["policy_hash"], "policy hash mismatch")
        require(len(run["findings"]) == count, "finding expectation changed: " + name)
        require(run.get("obligations") == [] and run.get("obligations_truncated") is False and run.get("omitted_obligations_lower_bound") == 0, "unreviewed schema-6 obligations")
        require(not report["diagnostics_truncated"] and not run["diagnostics_truncated"], "truncated diagnostics")
        row = {"id": name, "report_sha256": sha(path), "completion": run["completion"], "findings": count}
        if name in prior.LIMITS:
            case_id = prior.LIMITS[name]
            old_row = baseline_rows[case_id]
            require(old_row["outcome"] == "inconclusive", "baseline limit was conclusive")
            old_path = ROOT / old_row["raw_output"]
            raw_entry = next(r for r in baseline_entry["raw_evidence"] if r["case_id"] == case_id)
            require(sha(old_path) == raw_entry["sha256"], "baseline evidence changed")
            before, after = prior.signature(load(old_path)), prior.signature(report)
            filename = "Config.js" if "declared-source" in name else "Audit.js"
            require(run["completion"] == {"type": "inconclusive", "reasons": ["partial_discovery"], "scope": {"type": "files", "files": [filename], "truncated": False}}, "unexpected partial scope")
            require(before["diagnostics"] == after["diagnostics"] and before["endpoints"] == after["endpoints"], "partial diagnostics or engagement changed")
            for finding in run["findings"]:
                controls._validate_finding(finding, policy_id=run["policy_id"], report_path=path)
            row.update(interpretation="inconclusive", clean=False, baseline_raw=raw_entry,
                       previous_signature=before, current_signature=after)
        elif name in vacuous:
            diagnostics = report["diagnostics"] + run["diagnostics"]
            require(run["completion"] == {"type": "complete"} and len(diagnostics) == 1, "empty-selection state changed")
            note = diagnostics[0]
            require(note["code"] == {"type": "empty_selection"} and note["severity"] == "note" and note["impact"] == "advisory" and note["family"] == "empty_selection", "unexpected diagnostic")
            endpoints = prior.signature(report)["endpoints"]
            require(len(endpoints) == 2 and any(metric["value"] == 0 for metric in endpoints), "missing empty endpoint proof")
            row.update(interpretation="unbound-endpoint", clean=False)
        else:
            controls._validate_policy_report(path, language=language, expected_findings=count)
            endpoints = prior.signature(report)["endpoints"]
            require(len(endpoints) == 2 and all(metric["value"] > 0 for metric in endpoints), "missing endpoint engagement")
            row.update(interpretation="proven-flow" if count else "complete-no-finding")
        reviewed.append(row)
    return {"schema": "v092-bifrost-control-review/v1", "status": "measurement-with-known-limits",
            "execution_eligible": True, "full_policy_qualification": False,
            "tool": {**identity, "version": "0.14.0", "build_identity": original["tool"]["build_identity"]},
            "identity_components": [], "invocations": 44, "complete_policy_runs": 36,
            "inconclusive_policy_runs": 3, "unbound_endpoint_controls": 15, "sanitizer_controls": 15,
            "original_qualification": {"path": ATTEMPT + "/qualification.json", "sha256": sha(attempt / "qualification.json"), "status": "failed"},
            "capture_manifest": {"path": ATTEMPT + "/artifact-hashes.json", "sha256": sha(attempt / "artifact-hashes.json")},
            "native": {"interpretation": "not-evaluated", "clean": False, "document": native},
            "review_implementation": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
            "controls": reviewed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print("44 controls reviewed; three partial runs remain inconclusive; strict qualification remains failed")
