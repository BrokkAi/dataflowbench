"""Normalized Joern v0.9.2 report projection without legacy activation gates."""

from __future__ import annotations

import json
from pathlib import Path

import swift_common_population_v2 as common
from swift_normal_reports_v1 import normalized


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def bound_file(root: Path, ref: object) -> Path:
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact file reference required")
    relative = Path(ref["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "unsafe raw evidence path")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "missing or escaped raw evidence")
    require(sha(path) == ref["sha256"], "raw evidence SHA mismatch")
    return path


def export(root: Path, plan_path: str, run: dict, output: Path) -> list[dict]:
    """Write the exact five historical partitions with raw rows preserved."""
    root = Path(root).resolve()
    plan = read(root / plan_path)
    population, _common_rows, _swift_rows, cases, digest = common.load_common_population(root)
    require(plan.get("schema") == "joern-common-execution-plan/v092", "v0.9.2 Joern plan required")
    require(run.get("schema") == "joern-common-run/v092", "v0.9.2 Joern run record required")
    require(run.get("plan_sha256") == sha(root / plan_path), "Joern run plan digest mismatch")
    require(run.get("population_sha256") == digest and run.get("fixture_revision") == population["fixture_revision"], "Joern report population mismatch")
    require(run.get("scored_activation") is False and run.get("aggregate_resource_qualification") == "unavailable", "Joern result must remain unscored")
    require(run.get("identity") == plan.get("identity"), "Joern run identity differs from its plan")
    require(run.get("qualification_sha256") == plan["fresh_qualification"]["sha256"], "Joern qualification receipt mismatch")
    results = run.get("results")
    require(isinstance(results, list) and len(results) == 108, "Joern report requires the exact 108-case projection")
    by_id = {row.get("case_id"): row for row in results if isinstance(row, dict)}
    require(set(by_id) == set(cases) and len(by_id) == len(results), "Joern report membership mismatch")
    raw_rows = {}
    for case_id, row in by_id.items():
        raw = read(bound_file(root, row.get("raw")))
        expected_plan = sha(root / plan_path)
        for field, expected in (
            ("case_id", case_id),
            ("plan_sha256", expected_plan),
            ("population_sha256", digest),
            ("fixture_revision", population["fixture_revision"]),
            ("configuration", row.get("configuration")),
            ("identity", plan["identity"]),
        ):
            require(raw.get(field) == expected, "Joern raw result binding mismatch: " + field)
        outcome = normalized(raw.get("raw_outcome"))
        require(raw.get("state") == outcome, "Joern typed outcome was flattened")
        if outcome == "unsupported":
            require(plan["cases"][case_id].get("disposition") == "unsupported" and raw.get("executed") is False, "unsupported outcome lacks a prospective partition")
            require(raw.get("decision_sha256") == plan["cases"][case_id].get("decision", {}).get("sha256"), "unsupported decision digest mismatch")
            duration = 0
        else:
            require(plan["cases"][case_id].get("disposition") == "attempt" and raw.get("executed") is True, "attempted outcome lacks an attempted plan row")
            duration = raw.get("duration_ms")
            require(type(duration) is int and duration >= 0, "invalid Joern case duration")
        diagnostics = raw.get("diagnostics")
        checkpoints = raw.get("witness_checkpoints")
        require(isinstance(diagnostics, list) and all(isinstance(item, str) for item in diagnostics), "Joern diagnostics are malformed")
        require(isinstance(checkpoints, list) and all(isinstance(item, str) for item in checkpoints), "Joern checkpoints are malformed")
        raw_rows[case_id] = {
            "raw_outcome": raw["raw_outcome"],
            "outcome": outcome,
            "duration_ms": duration,
            "diagnostics": diagnostics,
            "witness_checkpoints": checkpoints,
            "raw": row["raw"],
        }

    parent_plan = read(root / "reports/releases/v0.9.0/plan.json")
    group = next((item for item in parent_plan["execution_groups"] if item.get("id") == "joern-swift-common108"), None)
    require(isinstance(group, dict) and len(group.get("reports", [])) == 5, "immutable Joern report partition map is missing")
    partition_rows = {item["report"]: item for item in parent_plan["reports"]}
    output.mkdir(parents=True, exist_ok=False)
    written = []
    for ordinal, old_path in enumerate(group["reports"]):
        partition = partition_rows.get(old_path)
        require(isinstance(partition, dict) and partition.get("execution_group") == "joern-swift-common108", "Joern report partition is not registered to the common group")
        case_ids = partition.get("case_ids")
        require(isinstance(case_ids, list) and case_ids and all(case_id in raw_rows for case_id in case_ids), "Joern report partition membership mismatch")
        report = {
            "schema_version": 1,
            **plan["identity"],
            "fixture_revision": population["fixture_revision"],
            "started_at_unix_seconds": run["started_at_unix_seconds"],
            "ended_at_unix_seconds": run["ended_at_unix_seconds"],
            "cold_or_warm": "cold",
            "scored_activation": False,
            "aggregate_resource_qualification": "unavailable",
            "results": [],
        }
        for case_id in case_ids:
            case = cases[case_id]
            row = raw_rows[case_id]
            report["results"].append({
                "case_id": case_id,
                "outcome": row["outcome"],
                "source_anchors": [anchor["marker"] for anchor in case["source_anchors"]],
                "sink_anchors": [anchor["marker"] for anchor in case["sink_anchors"]],
                "witness_checkpoints": row["witness_checkpoints"],
                "diagnostics": sorted(set(row["diagnostics"] + ["AggregateResourceQualificationUnavailable"])),
                "duration_ms": row["duration_ms"],
                "peak_memory_mb": None,
                "raw_output": row["raw"]["path"],
                "raw_sha256": row["raw"]["sha256"],
            })
        destination = output / f"report-{ordinal}.json"
        destination.write_text(json.dumps(report, indent=2) + "\n")
        written.append({"ordinal": ordinal, "path": destination.relative_to(root).as_posix(), "case_ids": case_ids})
    audit = {
        "schema": "joern-common-audit/v092",
        "population_sha256": digest,
        "fixture_revision": population["fixture_revision"],
        "scored_activation": False,
        "results": [
            {"case_id": case_id, "raw_outcome": raw_rows[case_id]["raw_outcome"],
             "outcome": raw_rows[case_id]["outcome"], "raw_sha256": raw_rows[case_id]["raw"]["sha256"]}
            for case_id in sorted(raw_rows)
        ],
    }
    (output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return written
