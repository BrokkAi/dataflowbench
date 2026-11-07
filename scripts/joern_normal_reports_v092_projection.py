"""Normalized Joern v0.9.2 report projection without legacy activation gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import swift_common_population_v2 as common
from swift_normal_reports_v1 import normalized

HISTORICAL_PLAN_SHA256 = "f4ae8f2ca3ece1bb253ce24a70368e969f0a25bc8d35dd2c8f7578d730aff4e9"
HISTORICAL_RUN_CANONICAL_SHA256 = "e0dda22dfd8d08bf268f6c8e214bfd9e9e7b92ffec338e7d3e5faa65310417e1"
HISTORICAL_SOURCE_SNAPSHOT = (
    "execution-state/v092/groups/series-02/joern-swift-common108/attempt-05"
)
HISTORICAL_RAW_ROOT = (
    "execution-state/v092/groups/series-02/joern-swift-common108/attempt-05/"
    "reports/raw/joern-common-v2/current108-v092-01/"
)


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
    require(isinstance(ref.get("path"), str), "file reference path must be a string")
    relative = Path(ref["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "unsafe raw evidence path")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "missing or escaped raw evidence")
    require(sha(path) == ref["sha256"], "raw evidence SHA mismatch")
    return path


def configuration_hash(root: Path, plan: dict, key: str = "joern-current108",
                       source_snapshot: Path | str | None = None) -> str:
    """Derive the report configuration hash from the pinned plan closure."""
    configurations = plan.get("configurations")
    references = configurations.get(key) if isinstance(configurations, dict) else None
    require(isinstance(references, list) and references, "Joern plan lacks configuration closure: " + key)
    require(all(isinstance(item, dict) and set(item) == {"path", "sha256"}
                and isinstance(item.get("path"), str) for item in references),
            "Joern configuration entries must bind exactly path and SHA-256")
    seen: set[str] = set()
    digest = hashlib.sha256()
    snapshot_root = None
    if source_snapshot is not None:
        snapshot_ref = Path(source_snapshot)
        require(not snapshot_ref.is_absolute() and ".." not in snapshot_ref.parts,
                "unsafe Joern configuration source snapshot")
        snapshot_root = root / snapshot_ref
        require(snapshot_root.is_dir() and not snapshot_root.is_symlink() and
                snapshot_root.resolve().is_relative_to(root.resolve()),
                "Joern configuration source snapshot is missing or escaped")
    for reference in sorted(references, key=lambda item: tuple(Path(item["path"]).parts)):
        relative_path = Path(reference["path"])
        require(not relative_path.is_absolute() and ".." not in relative_path.parts,
                "unsafe Joern configuration path")
        try:
            path = bound_file(root, reference)
        except ValueError:
            if snapshot_root is None:
                raise
            path = snapshot_root / relative_path
            require(path.is_file() and not path.is_symlink() and
                    path.resolve().is_relative_to(snapshot_root.resolve()) and
                    sha(path) == reference["sha256"],
                    "configuration snapshot differs from its pinned reference: " + reference["path"])
        relative = relative_path.as_posix()
        require(relative not in seen, "duplicate Joern configuration path: " + relative)
        seen.add(relative)
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _require_exact_historical_run(root: Path, run: dict) -> None:
    """Bind the historical configuration snapshot to the original attempt05 run."""
    canonical = json.dumps(run, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode()
    require(hashlib.sha256(canonical).hexdigest() == HISTORICAL_RUN_CANONICAL_SHA256,
            "historical configuration snapshot requires the exact retained attempt-05 run")
    results = run.get("results")
    require(isinstance(results, list) and len(results) == 108,
            "retained attempt-05 run lacks its exact 108 raw references")
    seen: set[str] = set()
    for row in results:
        require(isinstance(row, dict) and row.get("configuration") == "joern-current108",
                "retained attempt-05 run has a non-current configuration")
        case_id = row.get("case_id")
        raw_ref = row.get("raw")
        require(isinstance(case_id, str) and case_id and case_id not in seen and
                isinstance(raw_ref, dict) and
                raw_ref.get("path") == HISTORICAL_RAW_ROOT + case_id + "/raw.json",
                "retained attempt-05 run raw reference escapes its exact attempt root")
        seen.add(case_id)
        bound_file(root, raw_ref)
    require(len(seen) == 108, "retained attempt-05 run raw case references are incomplete")


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
    require(all(row.get("configuration") == "joern-current108" for row in by_id.values()),
            "Joern result configuration differs from the exact joern-current108 plan")
    source_snapshot = None
    if run.get("plan_sha256") == HISTORICAL_PLAN_SHA256:
        _require_exact_historical_run(root, run)
        source_snapshot = HISTORICAL_SOURCE_SNAPSHOT
    config_hash = configuration_hash(root, plan, source_snapshot=source_snapshot)
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
            "configuration_hash": config_hash,
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
