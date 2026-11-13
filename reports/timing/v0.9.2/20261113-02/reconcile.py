#!/usr/bin/env python3
"""Read retained candidates; never dispatch analyzers or rewrite release evidence."""
import collections
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / "reconciliation-v1"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path),
            "bytes": path.stat().st_size}


def distribution(values):
    values = sorted(values)
    def quantile(p):
        if not values:
            return None
        i = p * (len(values) - 1)
        lo, hi = math.floor(i), math.ceil(i)
        return values[lo] + (values[hi] - values[lo]) * (i - lo)
    return {"n": len(values), **{name: quantile(p) for name, p in
            [("min", 0), ("p10", .1), ("q1", .25), ("median", .5),
             ("q3", .75), ("p90", .9), ("max", 1)]}}


def main():
    manifest_path = ROOT / "reports/releases/v0.9.2/publication-v1/manifest.json"
    frozen = {r["adapter"]: r for r in read(manifest_path)["reports"]}
    summary = {"schema": "v092-timing-reconciliation/v1", "publication_eligible": False,
               "release_commit": "86092336d8f9ca32fe9e2c4042c2dced76c1feb1",
               "frozen_manifest": binding(manifest_path), "cold": [], "overhead": [],
               "limitations": ["Environment-scoped candidate evidence only; no speedup comparison.",
                   "Continuous queue does not meet original A24 inter-adapter settling qualification.",
                   "Observed contention, missing observations and unproven descendant containment remain unqualified.",
                   "A timing sidecar does not certify successful or semantically complete analysis.",
                   "Warm marginal measurements and other analyzer runtimes remain blocked."]}
    evidence, cases = {}, []
    def retain(path):
        evidence[str(path.relative_to(ROOT))] = binding(path)
    for campaign in ["20261113-01", "20261113-02"]:
        report = ROOT / "reports/timing/v0.9.2" / campaign
        plan = read(report / "plan.json")
        retain(report / "plan.json")
        retain(report / "campaign-terminal.json")
        for group in plan["groups"]:
            attempt = report / "attempts" / group["id"] / "attempt-01"
            if not (attempt / "terminal.json").exists():
                continue
            terminal = read(attempt / "terminal.json")
            source = ROOT / "execution-state" / ("timing-v092-" + campaign) / "sources" / group["id"]
            for relative in group["output_roots"]:
                path = source / relative
                for file in ([path] if path.is_file() else sorted(path.rglob("*"))):
                    if file.is_file():
                        assert not file.is_symlink(), file
                        retain(file)
            if terminal["status"] != "completed-candidate-evidence":
                continue
            if group["kind"] == "overhead":
                artifact = source / group["output_roots"][0] / "invocation-overhead.json"
                data = read(artifact)
                values = [r["wall_ms"] for r in data["runs"]]
                assert len(values) == 3 and data["repeats"] == 3
                assert data["estimated_overhead_ms"] == {"low": min(values), "high": max(values)}
                summary["overhead"].append({"group": group["id"], "artifact": binding(artifact),
                    "repeats_ms": values, "range_ms": data["estimated_overhead_ms"],
                    "qualification": terminal["quiet_certification"], "upper_bound_estimate": True})
                continue
            for descriptor in group["reports"]:
                path = source / descriptor["source_path"]
                candidate = read(path)
                baseline_path = ROOT / frozen[descriptor["path"]]["published_report"]["path"]
                assert digest(baseline_path) == frozen[descriptor["path"]]["published_report"]["sha256"]
                baseline = read(baseline_path)
                rows = {r["case_id"]: r for r in candidate["results"]}
                base_rows = {r["case_id"]: r for r in baseline["results"]}
                assert len(rows) == len(candidate["results"])
                assert set(rows) == set(base_rows) == set(descriptor["case_ids"])
                identity = ["adapter_version", "cold_or_warm", "configuration_hash", "fixture_revision",
                            "tool", "tool_build_identity", "tool_version"]
                identity_differences = {k: {"candidate": candidate.get(k), "frozen": baseline.get(k)}
                                        for k in identity if candidate.get(k) != baseline.get(k)}
                changes, times, untimed = [], [], collections.Counter()
                for case_id, row in sorted(rows.items()):
                    assert (source / row["raw_output"]).is_file(), row["raw_output"]
                    if row["outcome"] != base_rows[case_id]["outcome"]:
                        changes.append({"case_id": case_id, "candidate": row["outcome"],
                                        "frozen": base_rows[case_id]["outcome"]})
                    sidecar = (source / row["raw_output"]).parent / (case_id + "-timing.json")
                    record = {"group": group["id"], "case_id": case_id, "outcome": row["outcome"],
                              "wall_ms": None, "sidecar": None}
                    if sidecar.exists():
                        data = read(sidecar)
                        assert data["schema_version"] == 1 and data["clock"] == "monotonic"
                        assert data["evidence_kind"] == "retained-phase-timing" and data["case_id"] == case_id
                        assert data["adapter"] == group["family"] and data["phases"]
                        assert all(isinstance(p["wall_ms"], (int, float)) and math.isfinite(p["wall_ms"])
                                   and p["wall_ms"] >= 0 for p in data["phases"])
                        record.update(wall_ms=sum(p["wall_ms"] for p in data["phases"]), sidecar=binding(sidecar))
                        times.append(record["wall_ms"])
                    else:
                        untimed[row["outcome"]] += 1
                    cases.append(record)
                summary["cold"].append({"group": group["id"], "report": binding(path),
                    "baseline": binding(baseline_path), "cases": len(rows),
                    "outcomes": dict(collections.Counter(r["outcome"] for r in rows.values())),
                    "untimed_outcomes": dict(untimed), "whole_invocation_ms": distribution(times),
                    "identity_differences": identity_differences, "outcome_changes": changes,
                    "qualification": terminal["quiet_certification"],
                    "descendant_containment": terminal["process_ownership"]["descendant_containment"]})
    summary["totals"] = {"completed_cold_groups": len(summary["cold"]),
        "report_rows": sum(r["cases"] for r in summary["cold"]),
        "timed_rows": sum(r["whole_invocation_ms"]["n"] for r in summary["cold"]),
        "outcome_changes": sum(len(r["outcome_changes"]) for r in summary["cold"]),
        "identity_differences": sum(len(r["identity_differences"]) for r in summary["cold"]),
        "completed_overhead_groups": len(summary["overhead"]), "blocked_cold_groups": 63}
    OUT.mkdir(exist_ok=False)
    for name, data in [("summary.json", summary), ("cases.json", cases),
                       ("evidence-manifest.json", list(evidence.values()))]:
        (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
