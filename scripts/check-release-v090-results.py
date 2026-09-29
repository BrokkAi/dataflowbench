#!/usr/bin/env python3
"""Check the v0.9.0 freeze and generated release results.

The release revision is supplied explicitly because the v0.9.0 evidence
revision is not known during preparation. ``--plan-only`` validates the
prospective population and report partition plan; it never qualifies a
release. The release gate requires an actual v0.9.0 freeze and delegates the
clone, remote-main, tag, and generated-results checks to the v0.8 gate with
v0.9.0's release identity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "v0.9.0"
REQUIRED_REMOTE = "https://github.com/BrokkAi/dataflowbench.git"
EXPECTED_CASES = 1_108
EXPECTED_REPORT_PARTITIONS = 92
EXPECTED_REPORT_ROWS = 4_252
V090_PLAN = Path("reports/releases/v0.9.0/plan.json")
V090_POPULATION = Path("populations/v0.9.0.json")
HEX_COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class GateError(RuntimeError):
    """A release or planning gate assertion failed."""


def _load_v080_gate():
    """Load the existing release mechanics without changing its source bytes."""
    path = Path(__file__).with_name("check-release-results.py")
    spec = importlib.util.spec_from_file_location("_dataflowbench_v080_release_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load existing release gate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_V080_GATE = _load_v080_gate()


def _read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{description} must be a JSON object: {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _membership_digest(case_ids: list[str]) -> str:
    canonical = json.dumps(case_ids, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_plan(root: Path | None = None) -> dict:
    """Validate the bounded, prospective v0.9.0 plan without running anything."""
    root = (root or ROOT).resolve()
    plan_path = root / V090_PLAN
    population_path = root / V090_POPULATION
    plan = _read_json(plan_path, "v0.9.0 release plan")
    population = _read_json(population_path, "v0.9.0 population")

    if plan.get("release") != RELEASE:
        raise GateError(f"release plan declares {plan.get('release')!r}, expected {RELEASE!r}")
    if plan.get("schema_version") != 1:
        raise GateError("v0.9.0 release plan must use schema_version 1")
    if plan.get("status") != "pending-parent-review":
        raise GateError(
            "planning validation expects status 'pending-parent-review'; "
            f"found {plan.get('status')!r}"
        )
    blockers = plan.get("execution_blockers")
    if not isinstance(blockers, list) or not blockers:
        raise GateError("prospective plan must retain its execution blockers")

    if population.get("population") != RELEASE:
        raise GateError("population identity is not v0.9.0")
    if population.get("status") != "prospective-inputs-not-release-evidence":
        raise GateError("v0.9.0 population must remain marked prospective, not release evidence")
    if plan.get("fixture_revision") != population.get("fixture_revision"):
        raise GateError("plan and population fixture revisions differ")

    population_ref = plan.get("population")
    if not isinstance(population_ref, dict):
        raise GateError("plan is missing its population path and digest")
    if population_ref.get("path") != V090_POPULATION.as_posix():
        raise GateError(f"plan population path must be {V090_POPULATION.as_posix()!r}")
    declared_digest = population_ref.get("sha256")
    if not isinstance(declared_digest, str) or not SHA256.fullmatch(declared_digest):
        raise GateError("plan population sha256 must be 64 lowercase hexadecimal characters")
    if _sha256(population_path.read_bytes()) != declared_digest:
        raise GateError("v0.9.0 population bytes do not match the plan's SHA-256")

    cases = population.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASES:
        actual = len(cases) if isinstance(cases, list) else "missing"
        raise GateError(f"population has {actual} cases; expected {EXPECTED_CASES}")
    case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(case_ids) != len(cases) or any(not isinstance(value, str) or not value for value in case_ids):
        raise GateError("population contains a case without a non-empty string id")
    population_ids = set(case_ids)
    if len(population_ids) != EXPECTED_CASES:
        raise GateError("population case ids are not unique")
    if plan.get("expected_cases") != EXPECTED_CASES:
        raise GateError("plan expected_cases does not match the v0.9.0 population")

    reports = plan.get("reports")
    if not isinstance(reports, list) or len(reports) != EXPECTED_REPORT_PARTITIONS:
        actual = len(reports) if isinstance(reports, list) else "missing"
        raise GateError(
            f"plan has {actual} report partitions; expected {EXPECTED_REPORT_PARTITIONS}"
        )
    if plan.get("expected_report_partitions") != EXPECTED_REPORT_PARTITIONS:
        raise GateError("plan expected_report_partitions does not match its report rows")

    report_ids: set[str] = set()
    output_paths: set[str] = set()
    selected_ids: set[str] = set()
    row_count = 0
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            raise GateError(f"report partition {index} must be an object")
        report_id = report.get("id")
        if not isinstance(report_id, str) or not report_id or report_id in report_ids:
            raise GateError(f"report partition {index} has a missing or duplicate id")
        report_ids.add(report_id)
        output_path = report.get("report")
        if not isinstance(output_path, str) or not output_path.startswith(
            "reports/releases/v0.9.0/normal/"
        ) or output_path in output_paths:
            raise GateError(f"report partition {report_id} has an invalid or duplicate output path")
        output_paths.add(output_path)
        if report.get("argv"):
            raise GateError(f"prospective report partition {report_id} must not have executable argv")
        membership = report.get("case_ids")
        if (
            not isinstance(membership, list)
            or not membership
            or any(not isinstance(value, str) for value in membership)
            or len(membership) != len(set(membership))
        ):
            raise GateError(f"report partition {report_id} has invalid case_ids")
        unknown = set(membership) - population_ids
        if unknown:
            raise GateError(f"report partition {report_id} selects cases outside the population")
        declared_membership = report.get("case_membership")
        if (
            not isinstance(declared_membership, dict)
            or declared_membership.get("count") != len(membership)
            or declared_membership.get("sha256") != _membership_digest(membership)
        ):
            raise GateError(f"report partition {report_id} membership count or digest is invalid")
        selected_ids.update(membership)
        row_count += len(membership)

    if selected_ids != population_ids:
        raise GateError("report partitions do not cover the complete v0.9.0 population")
    if plan.get("expected_report_rows") != EXPECTED_REPORT_ROWS or row_count != EXPECTED_REPORT_ROWS:
        raise GateError(
            f"plan report membership has {row_count} rows; expected {EXPECTED_REPORT_ROWS}"
        )

    return {
        "release": RELEASE,
        "status": plan["status"],
        "population_cases": len(cases),
        "report_partitions": len(reports),
        "report_rows": row_count,
        "execution_blockers": len(blockers),
        "release_evidence": False,
    }


def _validate_evidence_revision(value: str) -> str:
    if not HEX_COMMIT.fullmatch(value):
        raise GateError("--evidence-revision must be a full 40-hex Git commit SHA")
    return value.lower()


def _load_release_manifest(source: Path, evidence_revision: str) -> dict:
    manifest_path = source / "reports" / "freeze.json"
    if not manifest_path.is_file():
        raise GateError(
            f"actual {RELEASE} release freeze is absent: {manifest_path}; "
            "prospective plans and historical freezes cannot qualify this release"
        )
    manifest = _read_json(manifest_path, "release freeze manifest")
    try:
        claim_scope = manifest["claim"]["scope"]
        benchmark = manifest["benchmark"]
        release = benchmark["release"]
        revision = benchmark["revision"]
        dirty = benchmark["dirty"]
    except (KeyError, TypeError) as exc:
        raise GateError(f"freeze manifest is missing its release identity: {exc}") from exc
    if manifest.get("schema_version") != 1:
        raise GateError("release freeze must use schema_version 1")
    if claim_scope != "release":
        raise GateError(f"freeze claim scope is {claim_scope!r}, expected 'release'")
    if release != RELEASE:
        raise GateError(f"freeze release is {release!r}, expected {RELEASE!r}")
    if revision != evidence_revision:
        raise GateError(
            f"freeze benchmark.revision is {revision!r}, "
            f"expected the supplied evidence revision {evidence_revision!r}"
        )
    if dirty is not False:
        raise GateError("release freeze must assert benchmark.dirty=false")

    population_path = source / V090_POPULATION
    population = _read_json(population_path, "v0.9.0 population")
    plan_path = source / V090_PLAN
    plan = _read_json(plan_path, "v0.9.0 release plan")
    if plan.get("release") != RELEASE:
        raise GateError(f"release plan declares {plan.get('release')!r}, expected {RELEASE!r}")
    plan_population = plan.get("population")
    if (
        not isinstance(plan_population, dict)
        or plan_population.get("path") != V090_POPULATION.as_posix()
        or plan_population.get("sha256") != _sha256(population_path.read_bytes())
    ):
        raise GateError("release plan does not bind the exact v0.9.0 population bytes")
    if benchmark.get("fixture_revision") != population.get("fixture_revision"):
        raise GateError("freeze and v0.9.0 population fixture revisions differ")
    population_cases = population.get("cases")
    frozen_cases = manifest.get("cases")
    if not isinstance(population_cases, list) or len(population_cases) != EXPECTED_CASES:
        raise GateError(f"v0.9.0 population must contain {EXPECTED_CASES} cases")
    if not isinstance(frozen_cases, list) or len(frozen_cases) != EXPECTED_CASES:
        raise GateError(f"v0.9.0 freeze must bind exactly {EXPECTED_CASES} cases")

    population_by_id = {
        item.get("id"): item for item in population_cases if isinstance(item, dict)
    }
    frozen_by_id = {item.get("id"): item for item in frozen_cases if isinstance(item, dict)}
    if len(population_by_id) != EXPECTED_CASES or len(frozen_by_id) != EXPECTED_CASES:
        raise GateError("population or freeze contains missing or duplicate case identities")
    if population_by_id.keys() != frozen_by_id.keys():
        raise GateError("freeze case ids do not match the exact v0.9.0 population")
    for case_id, population_case in population_by_id.items():
        frozen_case = frozen_by_id[case_id]
        for field in ("path", "sha256", "track", "score_tier", "model_profile", "fixture_digests"):
            if frozen_case.get(field) != population_case.get(field):
                raise GateError(f"freeze case {case_id!r} differs from population field {field!r}")

    reports = manifest.get("reports")
    if not isinstance(reports, list) or len(reports) != EXPECTED_REPORT_PARTITIONS:
        raise GateError(f"v0.9.0 freeze must contain {EXPECTED_REPORT_PARTITIONS} reports")
    planned_reports = plan.get("reports")
    if not isinstance(planned_reports, list) or len(planned_reports) != EXPECTED_REPORT_PARTITIONS:
        raise GateError(f"v0.9.0 plan must contain {EXPECTED_REPORT_PARTITIONS} report partitions")
    planned_memberships = {
        row.get("report"): row.get("case_ids")
        for row in planned_reports
        if isinstance(row, dict)
    }
    if len(planned_memberships) != EXPECTED_REPORT_PARTITIONS:
        raise GateError("v0.9.0 plan contains missing or duplicate report paths")
    frozen_memberships: dict[str, list[str]] = {}
    rows = 0
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            raise GateError(f"freeze report {index} must be an object")
        case_ids = report.get("case_ids")
        if (
            not isinstance(case_ids, list)
            or any(not isinstance(value, str) for value in case_ids)
            or len(case_ids) != len(set(case_ids))
        ):
            raise GateError(f"freeze report {index} has invalid case_ids")
        if set(case_ids) - population_by_id.keys():
            raise GateError(f"freeze report {index} references a case outside v0.9.0")
        path = report.get("path")
        if not isinstance(path, str) or path in frozen_memberships:
            raise GateError(f"freeze report {index} has a missing or duplicate report path")
        frozen_memberships[path] = case_ids
        rows += len(case_ids)
    if rows != EXPECTED_REPORT_ROWS:
        raise GateError(f"freeze reports select {rows} case rows; expected {EXPECTED_REPORT_ROWS}")
    if frozen_memberships != planned_memberships:
        raise GateError("freeze report partitions do not match the reviewed v0.9.0 plan")
    return manifest


def run_gate(
    source: Path | None = None,
    *,
    binary: Path,
    evidence_revision: str,
    generate_output: Path | None = None,
    git_remote: str = REQUIRED_REMOTE,
) -> None:
    """Run the v0.9.0 release gate for a caller-supplied evidence commit."""
    source = (source or ROOT).resolve()
    revision = _validate_evidence_revision(evidence_revision)
    _load_release_manifest(source, revision)

    # The v0.8 checker owns the already-reviewed clone/fetch/tag/result
    # mechanics. Scope its release identity to this call and restore it even
    # when validation fails. Its CLI remains unchanged and v0.8 remains fixed.
    old_release = _V080_GATE.RELEASE
    old_revision = _V080_GATE.EXPECTED_REVISION
    try:
        _V080_GATE.RELEASE = RELEASE
        _V080_GATE.EXPECTED_REVISION = revision
        _V080_GATE.run_gate(
            source,
            binary=binary,
            generate_output=generate_output,
            git_remote=git_remote,
        )
    except _V080_GATE.GateError as exc:
        raise GateError(str(exc)) from exc
    finally:
        _V080_GATE.RELEASE = old_release
        _V080_GATE.EXPECTED_REVISION = old_revision


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="validate prospective plan/population identities; does not qualify a release",
    )
    parser.add_argument(
        "--evidence-revision",
        help="exact full commit SHA recorded by the actual v0.9.0 freeze",
    )
    parser.add_argument(
        "--binary",
        type=Path,
        help="absolute path to the reviewed, unmodified dataflowbench binary",
    )
    parser.add_argument(
        "--generate-output",
        type=Path,
        help="copy generated results here only when the v0.9.0 tag is absent",
    )
    args = parser.parse_args(argv)
    if args.plan_only:
        if args.evidence_revision or args.binary or args.generate_output:
            parser.error("--plan-only cannot be combined with release-gate options")
    else:
        if not args.evidence_revision:
            parser.error("--evidence-revision is required for the release gate")
        if args.binary is None:
            parser.error("--binary is required for the release gate")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.plan_only:
            result = validate_plan()
            print(json.dumps(result, sort_keys=True))
            return 0
        run_gate(
            binary=args.binary,
            evidence_revision=args.evidence_revision,
            generate_output=args.generate_output,
        )
    except GateError as exc:
        print(f"release gate failed: {exc}", file=sys.stderr)
        return 1
    print(f"release gate passed for {RELEASE} at {args.evidence_revision.lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
