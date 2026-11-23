#!/usr/bin/env python3
"""Build and stage the retrospective v0.9.2 diagnostic timing publication.

`build` reads only retained campaign artifacts and emits a portable evidence
archive plus derived JSON. `verify` and `stage-site` work from that published
archive alone; they never read execution-state or invoke analyzers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import zipfile
from collections import Counter, defaultdict
from typing import Any, Iterable


SCHEMA = "v092-timing-diagnostic-publication/v1"
MANIFEST_SCHEMA = "v092-timing-publication-manifest/v1"
RELEASE_COMMIT = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
POPULATION = "v0.9.0"
FIXTURE_REVISION = "sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62"
PUBLICATION_ID = "20261123-v1"
PUBLICATION_REL = "reports/timing/v0.9.2/publication-20261123-01"
SITE_BASE = "/evidence/timing/v0-9-2/20261123-v1/"

CAMPAIGN_BASE = "reports/timing/v0.9.2"
PLAN_REL = f"{CAMPAIGN_BASE}/20261115-01/qualified-plan.json"
COVERAGE_REL = f"{CAMPAIGN_BASE}/reconciliation-20261122-01/capture-coverage-01.json"
SWIFT_AUDIT = f"{CAMPAIGN_BASE}/reconciliation-20261123-01/joern-swift-audit-01"
SWIFT_COSTS_REL = f"{SWIFT_AUDIT}/diagnostic-invocation-costs.json"
SWIFT_RECEIPT_REL = f"{SWIFT_AUDIT}/validation-receipt.json"
SWIFT_MAPPING_REL = f"{SWIFT_AUDIT}/diagnostic-mapping.json"
SWIFT_INVENTORY_REL = f"{SWIFT_AUDIT}/audit-inventory.json"
SWIFT_CAPTURE_INVENTORY_REL = f"{CAMPAIGN_BASE}/20261122-08/capture-evidence-inventory-01.json"
SWIFT_PLAN_REL = f"{CAMPAIGN_BASE}/20261122-08/supplement-plan-01.json"
SWIFT_TERMINAL_REL = f"{CAMPAIGN_BASE}/20261122-08/campaign-terminal.json"
SWIFT_LAUNCH_FAILURE_REL = f"{CAMPAIGN_BASE}/20261122-08/launch-failure-001.json"
SWIFT_ORIGINAL_COSTS_REL = f"{CAMPAIGN_BASE}/20261122-08/case-invocation-costs-01.json"
SEMgrep_AUDIT = f"{CAMPAIGN_BASE}/reconciliation-20261122-01/semgrep-warm-audit-02"
SEMgrep_RECEIPT_REL = f"{SEMgrep_AUDIT}/validation-receipt.json"
SEMgrep_INVENTORY_REL = f"{SEMgrep_AUDIT}/audit-inventory.json"

EXPECTED_PLAN_SHA = "d508f111908f2540f52085f47fc37551b553cc6fc03022c118db4bda784ebc78"
EXPECTED_SWIFT_CAPTURE_SHA = "466482c18cd38ce78e5a1562ad19470a75b139bfef4e2246b140ffce7d580f98"
EXPECTED_MASTER_PLAN_SHA = "2b1d55c362b895db47d81f5835f31f8dd53db94aa2a6f93fcdf6be19dc0d7b30"

FAMILY_ORDER = ("bifrost", "codeql", "joern", "semgrep", "opentaint", "infer", "flowdroid", "pysa")
FAMILY_NAMES = {
    "bifrost": "Bifrost",
    "codeql": "CodeQL CLI",
    "joern": "Joern",
    "semgrep": "Semgrep CE",
    "opentaint": "OpenTaint",
    "infer": "Infer",
    "flowdroid": "FlowDroid",
    "pysa": "Pysa / pyre-check",
}
LANGUAGE_NAMES = {
    "c": "C", "cpp": "C++", "csharp": "C#", "go": "Go", "java": "Java",
    "javascript": "JavaScript", "kotlin": "Kotlin", "php": "PHP", "python": "Python",
    "ruby": "Ruby", "rust": "Rust", "scala": "Scala", "swift": "Swift",
    "typescript": "TypeScript",
}


class PublicationError(ValueError):
    pass


def _require(ok: object, message: str) -> None:
    if not ok:
        raise PublicationError(message)


def _safe_rel(value: object) -> str:
    _require(isinstance(value, str) and value, "empty path")
    p = PurePosixPath(value)
    _require(not p.is_absolute() and all(part not in ("", ".", "..") for part in p.parts),
             f"unsafe relative path: {value!r}")
    return p.as_posix()


def _safe_join(root: Path, relative: str, *, must_exist: bool = True) -> Path:
    rel = _safe_rel(relative)
    path = root.joinpath(*PurePosixPath(rel).parts)
    current = root
    for part in PurePosixPath(rel).parts:
        current = current / part
        _require(not current.is_symlink(), f"symlink path component refused: {current}")
    if must_exist:
        _require(path.exists(), f"missing file: {rel}")
        resolved = path.resolve(strict=True)
        _require(resolved.is_relative_to(root.resolve(strict=True)), f"path escapes root: {rel}")
    return path


def _read_regular(root: Path, relative: str) -> bytes:
    path = _safe_join(root, relative)
    st = path.lstat()
    _require(stat.S_ISREG(st.st_mode), f"not a regular file: {relative}")
    raw = path.read_bytes()
    after = path.lstat()
    _require((st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             f"file changed while read: {relative}")
    return raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ref(raw: bytes, path: str, *, archive_path: str | None = None, kind: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"path": path, "sha256": _sha(raw), "bytes": len(raw)}
    if archive_path is not None:
        out["archive_path"] = archive_path
    if kind is not None:
        out["kind"] = kind
    return out


def _loads(raw: bytes, label: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in items:
            _require(key not in obj, f"duplicate JSON key in {label}: {key}")
            obj[key] = value
        return obj

    def reject_constant(value: str) -> None:
        raise PublicationError(f"non-finite JSON value in {label}: {value}")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationError(f"invalid JSON {label}: {exc}") from exc

    def finite(node: Any) -> None:
        if isinstance(node, float):
            _require(math.isfinite(node), f"non-finite JSON number in {label}")
        elif isinstance(node, dict):
            for child in node.values():
                finite(child)
        elif isinstance(node, list):
            for child in node:
                finite(child)
    finite(value)
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _quantile(values: list[int], p: float) -> float | int | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = p * (len(ordered) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def _summary_ms(values: list[int]) -> dict[str, Any] | None:
    if not values:
        return None
    return {"min": min(values), "median": _quantile(values, .5),
            "p90": _quantile(values, .9), "max": max(values)}


def _display_language(group: dict[str, Any]) -> str:
    group_id = group["id"]
    family = group["family"]
    if group_id.endswith("-smoke"):
        return "Mixed"
    if group_id.startswith("overhead-") or group_id.startswith("warm-"):
        remainder = group_id.split("-", 1)[1]
        if remainder.startswith(family + "-"):
            language = remainder[len(family) + 1:].split("-")[0]
        else:
            language = remainder.split("-")[0]
    elif group.get("case_ids"):
        chunks = group["case_ids"][0].split("-")
        language = chunks[2] if len(chunks) > 2 else "mixed"
    else:
        parts = group_id.split("-")
        language = parts[1] if len(parts) > 1 else "mixed"
    return LANGUAGE_NAMES.get(language, language.title())


def _tier(group: dict[str, Any]) -> str:
    if group["kind"] != "cold":
        return group["kind"]
    if group["id"] == "joern-swift-common108":
        return "mixed"
    for suffix in ("modeling", "native", "smoke", "kernel"):
        if group["id"].endswith("-" + suffix):
            return suffix
    return "mixed"


class EvidenceArchive:
    def __init__(self, root: Path, capture_refs: dict[str, dict[str, Any]]):
        self.root = root
        self.capture_refs = capture_refs
        self.files: dict[str, bytes] = {}
        self.refs: dict[str, dict[str, Any]] = {}

    def add(self, relative: str, *, capture_bound: bool = False, kind: str | None = None) -> dict[str, Any]:
        rel = _safe_rel(relative)
        if rel in self.refs:
            existing = dict(self.refs[rel])
            if kind is not None:
                existing["kind"] = kind
            return existing
        raw = _read_regular(self.root, rel)
        result = _ref(raw, rel, archive_path=f"evidence/{rel}", kind=kind)
        if capture_bound:
            expected = self.capture_refs.get(rel)
            _require(expected is not None, f"captured input absent from retained inventory: {rel}")
            _require((result["sha256"], result["bytes"]) ==
                     (expected["sha256"], expected["size_bytes"]),
                     f"captured input differs from sealed inventory: {rel}")
        self.files[result["archive_path"]] = raw
        self.refs[rel] = result
        return dict(result)

    def archive_bytes(self) -> bytes:
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for name in sorted(self.files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zf.writestr(info, self.files[name])
        return buff.getvalue()


def _capture_index(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    paths = [
        f"{CAMPAIGN_BASE}/20261121-01/parent-checkpoint-01.json",
        f"{CAMPAIGN_BASE}/20261121-01/evidence-inventory-01.json",
        f"{CAMPAIGN_BASE}/20261122-01/evidence-inventory-01.json",
        f"{CAMPAIGN_BASE}/20261122-02/capture-evidence-inventory-01.json",
        SWIFT_CAPTURE_INVENTORY_REL,
    ]
    inventory_docs: dict[str, Any] = {}
    refs: dict[str, dict[str, Any]] = {}
    for rel in paths:
        doc = _loads(_read_regular(root, rel), rel)
        inventory_docs[rel] = doc
        entries = doc.get("evidence_files", doc.get("files", []))
        for item in entries:
            existing = refs.get(item["path"])
            if existing:
                _require((existing["sha256"], existing["size_bytes"]) ==
                         (item["sha256"], item["size_bytes"]),
                         f"conflicting capture inventories for {item['path']}")
            refs[item["path"]] = item
    return refs, inventory_docs


def _phase_wall_ms(timing: dict[str, Any]) -> tuple[int, str]:
    _require(timing.get("evidence_kind") == "retained-phase-timing", "unexpected timing sidecar kind")
    phases = timing.get("phases")
    _require(isinstance(phases, list), "timing sidecar has no phase list")
    total = [p for p in phases if isinstance(p, dict) and p.get("phase") == "total"]
    if len(total) == 1 and len(phases) == 1:
        value = total[0].get("wall_ms")
        _require(type(value) is int and value >= 0, "timing sidecar total wall_ms is invalid")
        return value, "producer-total"

    # Keep the preregistered adapters' distinct phase semantics. Infer's
    # capture and analyze subprocesses form its invocation cost. FlowDroid
    # modeling records fixture materialization as well as analysis, but A20
    # explicitly excludes compile/dex; only analyze is its analyzer cost.
    phase_names = [p.get("phase") if isinstance(p, dict) else None for p in phases]
    values = [p.get("wall_ms") for p in phases]
    _require(all(type(value) is int and value >= 0 for value in values),
             "multi-phase timing wall_ms is invalid")
    adapter = timing.get("adapter")
    if adapter in {"codeql", "codeql-java", "codeql-javascript", "codeql-typescript"} and \
            phase_names == ["database-create", "database-analyze"]:
        return sum(values), "sum-of-database-create-and-analyze-subprocesses"
    if adapter == "infer" and phase_names == ["capture", "analyze"]:
        return sum(values), "sum-of-capture-and-analyze-subprocesses"
    if adapter == "flowdroid" and phase_names == ["compile", "dex", "analyze"]:
        return values[phase_names.index("analyze")], "analyzer-phase-excluding-apk-materialization"
    raise PublicationError("unsupported multi-phase timing sidecar")


def _terminal_refs(archive: EvidenceArchive, attempt: dict[str, Any]) -> list[dict[str, Any]]:
    terminal_path = attempt["terminal"]["path"]
    base = PurePosixPath(terminal_path)
    start_path = str(base.with_name("start.json"))
    host_path = str(base.with_name("host.jsonl"))
    refs = [archive.add(terminal_path, capture_bound=True, kind="attempt-terminal")]
    if _safe_join(archive.root, start_path, must_exist=False).exists():
        refs.append(archive.add(start_path, capture_bound=True, kind="attempt-start"))
    if _safe_join(archive.root, host_path, must_exist=False).exists():
        refs.append(archive.add(host_path, capture_bound=True, kind="host-samples"))
    return refs


def _build_cold_group(root: Path, archive: EvidenceArchive, group: dict[str, Any], attempt: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    campaign = attempt["campaign_id"]
    source_root = f"execution-state/timing-v092-{campaign}/sources/{group['id']}"
    report_rel = f"{source_root}/{group['reports'][0]['source_path']}"
    report_raw = _read_regular(root, report_rel)
    report = _loads(report_raw, report_rel)
    report_ref = archive.add(report_rel, capture_bound=True, kind="normal-report")
    _require(report.get("tool") == group["family"], f"tool identity differs for {group['id']}")
    _require(report.get("tool_version") == group["reports"][0].get("tool_version"),
             f"report tool version differs from bound plan for {group['id']}")
    _require(report.get("cold_or_warm") == "cold", f"report is not cold: {group['id']}")
    results = report.get("results")
    _require(isinstance(results, list), f"report results missing: {group['id']}")
    expected_ids = list(group.get("case_ids", []))
    actual_ids = [r.get("case_id") for r in results]
    _require(len(actual_ids) == len(set(actual_ids)), f"duplicate report case in {group['id']}")
    _require(set(actual_ids) == set(expected_ids), f"report case membership differs for {group['id']}")
    by_id = {r["case_id"]: r for r in results}
    terminal_refs = _terminal_refs(archive, attempt)
    rows: list[dict[str, Any]] = []
    quarantine = group["id"] == "joern-rust-kernel"
    status = "quarantined" if quarantine else "accepted-candidate"
    for case_id in expected_ids:
        result = by_id[case_id]
        outcome = result.get("outcome")
        _require(isinstance(outcome, str) and outcome, f"missing outcome: {group['id']} {case_id}")
        case_refs = [dict(report_ref)]
        raw_output_ref = None
        if isinstance(result.get("raw_output"), str):
            raw_rel = f"{source_root}/{result['raw_output']}"
            raw_output_ref = archive.add(raw_rel, capture_bound=True, kind="raw-case-output")
            case_refs.append(dict(raw_output_ref))
        timing_ref = None
        wall_ms = None
        if isinstance(result.get("raw_output"), str):
            raw_relative = PurePosixPath(result["raw_output"])
            timing_rel = str(PurePosixPath(source_root) / raw_relative.parent / f"{case_id}-timing.json")
            timing_path = _safe_join(root, timing_rel, must_exist=False)
            if timing_path.exists():
                timing_raw = _read_regular(root, timing_rel)
                timing_doc = _loads(timing_raw, timing_rel)
                _require(timing_doc.get("case_id") == case_id, f"timing case mismatch: {timing_rel}")
                timing_ref = archive.add(timing_rel, capture_bound=True, kind="timing-sidecar")
                case_refs.append(dict(timing_ref))
                wall_ms, cost_basis = _phase_wall_ms(timing_doc)
            else:
                cost_basis = "unavailable"
        else:
            cost_basis = "unavailable"
        if outcome == "unsupported":
            wall_ms = None
        accepted = (not quarantine and outcome != "unsupported" and type(wall_ms) is int)
        row_status = "quarantined" if quarantine else ("unsupported-no-invocation" if outcome == "unsupported" else "accepted-candidate")
        if outcome != "unsupported" and wall_ms is None and not quarantine:
            row_status = "missing-invocation-cost"
        rows.append({
            "group": group["id"], "case_id": case_id, "outcome": outcome,
            "wall_ms": wall_ms, "invocation_cost_ms": wall_ms,
            "invocation_cost_accepted": accepted,
            "cost_basis": cost_basis,
            "latency_eligible": False, "analysis_latency_eligible": False,
            "partial": False, "evidence_status": row_status,
            "source_refs": case_refs,
        })
    values = [r["invocation_cost_ms"] for r in rows if r["invocation_cost_accepted"]]
    counts = dict(sorted(Counter(r["outcome"] for r in rows).items()))
    refs = [dict(report_ref), *terminal_refs]
    for ref in (archive.add(PLAN_REL, kind="qualified-plan"),):
        refs.append(ref)
    record = {
        "group": group["id"], "analyzer_id": group["family"], "kernel": _display_language(group),
        "tier": _tier(group), "evidence_status": status, "report_rows": len(rows),
        "timed_rows": len(values), "summary_ms": _summary_ms(values), "outcomes": counts,
        "tool_version": report.get("tool_version"), "tool_build_identity": report.get("tool_build_identity"),
        "configuration_hash": report.get("configuration_hash"),
        "controller_status": attempt.get("status"),
        "quiet_certification": attempt.get("original_quiet_certification"),
        "source_refs": refs,
    }
    return record, rows


def _build_swift_group(root: Path, archive: EvidenceArchive, group: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    receipt = _loads(_read_regular(root, SWIFT_RECEIPT_REL), SWIFT_RECEIPT_REL)
    costs_raw = _read_regular(root, SWIFT_COSTS_REL)
    costs = _loads(costs_raw, SWIFT_COSTS_REL)
    _require(receipt.get("status") == "accepted-diagnostic-invocation-costs", "Swift wording reconciliation is not accepted")
    _require(receipt.get("publication_eligible") is False and receipt.get("full_model_qualification") is False,
             "Swift qualification flags differ")
    capture_ref = receipt.get("capture_inventory", {})
    _require(capture_ref.get("path") == SWIFT_CAPTURE_INVENTORY_REL and
             capture_ref.get("sha256") == EXPECTED_SWIFT_CAPTURE_SHA and
             receipt.get("sealed_capture_files_verified_before_and_after") == 7559,
             "Swift reconciliation does not bind the sealed capture inventory")
    _require(costs.get("accepted_diagnostic_invocation_cost_rows") == 96 and
             costs.get("accepted_successful_analysis_latency_rows") == 0 and
             costs.get("unsupported_no_invocation_rows") == 12,
             "Swift accepted cost counts differ")
    cost_ref = archive.add(SWIFT_COSTS_REL, kind="diagnostic-invocation-costs")
    report_refs: list[dict[str, Any]] = []
    reports_by_case: dict[str, dict[str, Any]] = {}
    report_ref_by_case: dict[str, dict[str, Any]] = {}
    for index in range(5):
        rel = f"{SWIFT_AUDIT}/normal/report-{index}.json"
        raw = _read_regular(root, rel)
        report = _loads(raw, rel)
        ref = archive.add(rel, kind="reconciled-normal-report")
        report_refs.append(ref)
        for result in report.get("results", []):
            _require(result.get("case_id") not in reports_by_case, "duplicate Swift case in projections")
            reports_by_case[result["case_id"]] = result
            report_ref_by_case[result["case_id"]] = ref
    expected = list(group["case_ids"])
    cost_by_id = {r["case_id"]: r for r in costs["rows"]}
    _require(set(reports_by_case) == set(expected) == set(cost_by_id), "Swift case population differs")
    partial_ids = {item["case_id"] for item in costs.get("partial_invocations", [])}
    _require(len(partial_ids) == 4, "Swift partial invocation count differs")
    rows: list[dict[str, Any]] = []
    for case_id in expected:
        cost = cost_by_id[case_id]
        result = reports_by_case[case_id]
        accepted = bool(cost.get("executed")) and cost.get("duration_ms", 0) > 0 and cost.get("latency_sample_included") is True
        unsupported = not cost.get("executed")
        wall_ms = cost.get("duration_ms") if accepted else None
        query_executed = any(c.get("phase_id") == "query" for c in cost.get("commands", []))
        is_partial = bool(cost.get("executed")) and not query_executed
        _require((case_id in partial_ids) == is_partial, "Swift partial phase mapping differs")
        row_refs = [dict(cost_ref), dict(report_ref_by_case[case_id])]
        rows.append({
            "group": group["id"], "case_id": case_id, "outcome": result.get("outcome"),
            "raw_outcome": cost.get("raw_outcome"), "wall_ms": wall_ms,
            "invocation_cost_ms": wall_ms, "invocation_cost_accepted": accepted,
            "latency_eligible": False, "analysis_latency_eligible": False,
            "partial": is_partial,
            "evidence_status": "diagnostic-costs-accepted" if accepted else "unsupported-no-invocation",
            "source_refs": row_refs,
        })
    values = [r["invocation_cost_ms"] for r in rows if r["invocation_cost_accepted"]]
    status_refs = [
        archive.add(SWIFT_RECEIPT_REL, kind="reconciliation-receipt"),
        archive.add(SWIFT_MAPPING_REL, kind="diagnostic-mapping"),
        archive.add(SWIFT_INVENTORY_REL, kind="reconciliation-inventory"),
        archive.add(SWIFT_CAPTURE_INVENTORY_REL, kind="sealed-capture-inventory"),
        archive.add(SWIFT_PLAN_REL, kind="supplement-plan"),
        archive.add(SWIFT_TERMINAL_REL, kind="original-failed-terminal"),
        archive.add(SWIFT_LAUNCH_FAILURE_REL, kind="original-launch-failure"),
        archive.add(SWIFT_ORIGINAL_COSTS_REL, kind="original-captured-costs"),
        *report_refs,
        cost_ref,
    ]
    outcome_counts = dict(sorted(Counter(r["outcome"] for r in rows).items()))
    record = {
        "group": group["id"], "analyzer_id": "joern", "kernel": "Swift", "tier": "mixed",
        "evidence_status": "diagnostic-costs-accepted", "report_rows": 108,
        "timed_rows": len(values), "summary_ms": _summary_ms(values), "outcomes": outcome_counts,
        "tool_version": "4.0.660", "tool_build_identity": "joern-cli:4.0.660",
        "controller_status": "blocked-in-original-campaign; accepted-diagnostic-costs-by-retrospective-reconciliation",
        "qualification": {"successful_analysis_latency_rows": 0, "full_model_qualification": False,
                          "retrospective": True, "publication_eligible": False},
        "source_refs": status_refs,
    }
    costs_out = costs
    return record, rows, costs_out


def _case_ids_from_report(root: Path, ref: dict[str, Any]) -> set[str]:
    raw = _read_archive_source_for_build(root, ref)
    d = _loads(raw, str(ref["path"]))
    return {r["case_id"] for r in d.get("results", [])}


def _read_archive_source_for_build(root: Path, ref: dict[str, Any]) -> bytes:
    return _read_regular(root, ref["path"])


def _build_overhead_and_warm(root: Path, archive: EvidenceArchive, plan: dict[str, Any], attempts: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    overhead: list[dict[str, Any]] = []
    warm_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in plan["groups"]:
        kind = group["kind"]
        if kind not in ("overhead", "warm"):
            continue
        attempt = attempts.get(group["id"])
        _require(attempt is not None, f"missing retained attempt: {group['id']}")
        source_root = f"execution-state/timing-v092-{attempt['campaign_id']}/sources/{group['id']}"
        out_root = group["output_roots"][0]
        artifact_name = "invocation-overhead.json" if kind == "overhead" else "warm-latency.json"
        artifact_rel = f"{source_root}/{out_root}/{artifact_name}"
        artifact = _loads(_read_regular(root, artifact_rel), artifact_rel)
        artifact_ref = archive.add(artifact_rel, capture_bound=True, kind=f"{kind}-artifact")
        env_rel = f"{source_root}/{out_root}/run-environment.json"
        env_ref = archive.add(env_rel, capture_bound=True, kind="run-environment")
        term_refs = _terminal_refs(archive, attempt)
        if kind == "overhead":
            values = [run.get("wall_ms") for run in artifact.get("runs", [])]
            _require(len(values) == 3 and all(type(v) is int and v >= 0 for v in values),
                     f"overhead samples invalid for {group['id']}")
            refs = [artifact_ref, env_ref, *term_refs]
            # Include the actual tiny fixture used by the overhead producer when present.
            fixture_rel = f"{source_root}/{out_root}/{artifact.get('fixture_file', '')}"
            if artifact.get("fixture_file") and _safe_join(root, fixture_rel, must_exist=False).exists():
                refs.append(archive.add(fixture_rel, capture_bound=True, kind="overhead-fixture"))
            overhead.append({
                "group": group["id"], "analyzer_id": group["family"], "kernel": _display_language(group),
                "tier": "overhead", "evidence_status": "candidate-overhead", "sample_count": 3,
                "samples_ms": values, "summary_ms": _summary_ms(values),
                "range_ms": {"low": min(values), "high": max(values)},
                "upper_bound_estimate": True, "source_refs": refs,
            })
        else:
            # Warm measurements are batch costs, not cold per-case costs.
            batch_rows = []
            for run in artifact.get("runs", []):
                for batch in run.get("batches", []):
                    _require(type(batch.get("wall_ms")) is int and batch["wall_ms"] >= 0,
                             f"warm batch duration invalid for {group['id']}")
                    batch_rows.append({"repeat": run.get("run"), "batch_size": batch.get("k"),
                                       "wall_ms": batch["wall_ms"], "case_count": len(batch.get("case_ids", []))})
            refs = [artifact_ref, env_ref, *term_refs]
            if group["id"] == "warm-joern-java":
                for item in archive.capture_refs.values():
                    path = item["path"]
                    if path.startswith(f"{source_root}/{out_root}/run-") and "-evidence/" in path:
                        refs.append(archive.add(path, capture_bound=True, kind="warm-case-evidence"))
                controller_status = "completed-candidate-evidence"
                evidence_status = "candidate-warm"
                case_observations = 0
                per_case_timing_rows = 0
                equivalence_status = "not-independent-certification"
            else:
                audit_receipt = _loads(_read_regular(root, SEMgrep_RECEIPT_REL), SEMgrep_RECEIPT_REL)
                audit_inventory = _loads(_read_regular(root, SEMgrep_INVENTORY_REL), SEMgrep_INVENTORY_REL)
                _verify_audit_inventory(root, audit_inventory)
                for entry in audit_inventory.get("files", []):
                    ref = archive.add(entry["path"], kind="semgrep-warm-audit-evidence")
                    _require((ref["sha256"], ref["bytes"]) == (entry["sha256"], entry["size_bytes"]),
                             f"Semgrep warm audit inventory differs: {entry['path']}")
                    refs.append(ref)
                refs.extend([
                    archive.add(SEMgrep_RECEIPT_REL, kind="semgrep-warm-audit-receipt"),
                    archive.add(SEMgrep_INVENTORY_REL, kind="semgrep-warm-audit-inventory"),
                    archive.add(f"{CAMPAIGN_BASE}/reconciliation-20261122-01/independent-review-01.json",
                                kind="semgrep-warm-independent-review"),
                ])
                controller_status = "failed; exit 0; missing family-specific evidence directory"
                evidence_status = "retrospective-diagnostic-recovered"
                case_observations = audit_receipt.get("validation", {}).get("derived_case_observation_count", 0)
                per_case_timing_rows = 0
                equivalence_status = audit_receipt.get("validation", {}).get("equivalence_status", "pending")
            values = [row["wall_ms"] for row in batch_rows]
            warm_by_family[group["family"]].append({
                "group": group["id"], "kernel": _display_language(group), "tier": "warm",
                "evidence_status": evidence_status, "controller_status": controller_status,
                "batch_count": len(batch_rows), "timed_rows": 62 if group["id"] == "warm-joern-java" else 0,
                "samples_ms": values, "batch_samples": batch_rows, "summary_ms": _summary_ms(values),
                "case_observations": case_observations or (62 if group["id"] == "warm-joern-java" else 54),
                "per_case_timing_rows": 62 if group["id"] == "warm-joern-java" else 0,
                "equivalence_status": equivalence_status, "source_refs": refs,
            })
    warm = [{"analyzer_id": family, "groups": warm_by_family[family]}
            for family in FAMILY_ORDER if family in warm_by_family]
    return overhead, warm


def _build_receipt_refs(archive: EvidenceArchive, root: Path) -> list[dict[str, Any]]:
    refs = []
    for rel in [
        PLAN_REL,
        f"{CAMPAIGN_BASE}/20261115-01/campaign-start.json",
        f"{CAMPAIGN_BASE}/20261115-01/campaign-pause-01.json",
        f"{CAMPAIGN_BASE}/20261121-01/qualified-plan.json",
        f"{CAMPAIGN_BASE}/20261121-01/campaign-start.json",
        f"{CAMPAIGN_BASE}/20261121-01/campaign-terminal.json",
        f"{CAMPAIGN_BASE}/20261121-01/completion-summary-01.json",
        f"{CAMPAIGN_BASE}/20261121-01/parent-checkpoint-01.json",
        f"{CAMPAIGN_BASE}/20261122-01/qualified-plan-02.json",
        f"{CAMPAIGN_BASE}/20261122-01/campaign-start.json",
        f"{CAMPAIGN_BASE}/20261122-01/campaign-terminal.json",
        f"{CAMPAIGN_BASE}/20261122-01/segment-checkpoint-01.json",
        f"{CAMPAIGN_BASE}/20261122-02/qualified-plan-02.json",
        f"{CAMPAIGN_BASE}/20261122-02/campaign-start.json",
        f"{CAMPAIGN_BASE}/20261122-02/campaign-terminal.json",
        f"{CAMPAIGN_BASE}/20261122-02/parent-checkpoint-01.json",
        f"{CAMPAIGN_BASE}/20261122-02/dispatch-admission-policy-01.json",
        COVERAGE_REL,
        SWIFT_PLAN_REL, SWIFT_TERMINAL_REL, SWIFT_LAUNCH_FAILURE_REL,
        SWIFT_ORIGINAL_COSTS_REL,
        SWIFT_CAPTURE_INVENTORY_REL, SWIFT_RECEIPT_REL, SWIFT_MAPPING_REL,
        SWIFT_INVENTORY_REL, SEMgrep_RECEIPT_REL, SEMgrep_INVENTORY_REL,
        f"{CAMPAIGN_BASE}/reconciliation-20261122-01/independent-review-01.json",
        "reports/timing/v0.9.2/20261115-01/reviews/codeql-native-error-diagnosis-02.json",
        "reports/timing/v0.9.2/20261115-01/reviews/codeql-native-cache-prerequisite-01.json",
        "docs/latency-v092-20261122-warm-reconciliation.md",
        "docs/latency-v092-20261123-decline-wording.md",
    ]:
        if _safe_join(root, rel, must_exist=False).exists():
            refs.append(archive.add(rel, kind="campaign-or-policy-receipt"))
    return refs


def _verify_audit_inventory(root: Path, inventory: dict[str, Any]) -> None:
    entries = inventory.get("files")
    _require(isinstance(entries, list), "audit inventory has no file list")
    for item in entries:
        raw = _read_regular(root, item["path"])
        _require(_sha(raw) == item["sha256"] and
                 ("size_bytes" not in item or len(raw) == item["size_bytes"]),
                 f"audit inventory file differs: {item['path']}")


def _build_publication(root: Path, *, include_archive: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], bytes, dict[str, Any], dict[str, Any]]:
    plan = _loads(_read_regular(root, PLAN_REL), PLAN_REL)
    _require(_sha(_read_regular(root, PLAN_REL)) == EXPECTED_MASTER_PLAN_SHA, "master timing plan SHA differs")
    _require(plan.get("release_commit") == RELEASE_COMMIT, "cold plan release differs")
    _require(plan.get("population") == POPULATION and plan.get("fixture_revision") == FIXTURE_REVISION,
             "cold plan population/fixture revision differs")
    _require(len(plan.get("source_cold_group_order", [])) == 84, "expected 84 planned cold groups")
    coverage = _loads(_read_regular(root, COVERAGE_REL), COVERAGE_REL)
    _require(coverage.get("immutable_release") == RELEASE_COMMIT and coverage.get("planned_cold_groups") == 84,
             "coverage receipt release/denominator differs")
    _require(coverage.get("publication_eligible") is False, "coverage must remain unqualified")
    capture_refs, inventory_docs = _capture_index(root)
    _require(_sha(_read_regular(root, SWIFT_PLAN_REL)) == EXPECTED_PLAN_SHA, "Swift supplement plan SHA differs")
    _require(_sha(_read_regular(root, SWIFT_CAPTURE_INVENTORY_REL)) == EXPECTED_SWIFT_CAPTURE_SHA,
             "Swift capture inventory SHA differs")
    archive = EvidenceArchive(root, capture_refs)
    _build_receipt_refs(archive, root)
    # Retain all campaign inventory receipts used to authenticate selected source files.
    for rel in inventory_docs:
        archive.add(rel, kind="capture-inventory")
    plan_copy = archive.add(PLAN_REL, kind="master-plan")
    coverage_copy = archive.add(COVERAGE_REL, kind="capture-coverage")
    swift_audit_index = _loads(_read_regular(root, SWIFT_INVENTORY_REL), SWIFT_INVENTORY_REL)
    _verify_audit_inventory(root, swift_audit_index)

    attempts = {item["group"]: item for item in coverage["attempts"]}
    plan_by_id = {group["id"]: group for group in plan["groups"]}
    rows: list[dict[str, Any]] = []
    cold_groups: list[dict[str, Any]] = []
    swift_costs_out: dict[str, Any] | None = None
    for group_id in plan["source_cold_group_order"]:
        group = plan_by_id[group_id]
        if group_id == "codeql-swift-common108":
            blocker_refs = [
                archive.add("reports/timing/v0.9.2/20261115-01/reviews/codeql-native-error-diagnosis-02.json",
                            kind="blocked-prerequisite-diagnosis"),
                archive.add("reports/timing/v0.9.2/20261115-01/reviews/codeql-native-cache-prerequisite-01.json",
                            kind="blocked-prerequisite-review"),
            ]
            cold_groups.append({
                "group": group_id, "analyzer_id": group["family"], "kernel": "Swift", "tier": "mixed",
                "evidence_status": "blocked", "blocker": "The exact pinned CodeQL Swift extractor is unavailable; Swift remains paused with no accepted analysis invocation.",
                "report_rows": 0, "timed_rows": 0, "summary_ms": None, "outcomes": {},
                "tool_version": group["reports"][0]["tool_version"], "tool_build_identity": None,
                "source_refs": blocker_refs + [dict(plan_copy), dict(coverage_copy)],
                "planned_case_rows": len(group["case_ids"]),
            })
            continue
        if group_id == "joern-swift-common108":
            record, group_rows, swift_costs_out = _build_swift_group(root, archive, group)
            cold_groups.append(record)
            rows.extend(group_rows)
            continue
        attempt = attempts.get(group_id)
        _require(attempt is not None, f"missing attempt evidence for cold group {group_id}")
        status = attempt.get("status")
        _require(status in ("completed-candidate-evidence", "failed"), f"unexpected group controller status: {group_id} {status}")
        if status == "failed":
            _require(group_id == "joern-rust-kernel", f"unexpected failed cold group: {group_id}")
        record, group_rows = _build_cold_group(root, archive, group, attempt)
        cold_groups.append(record)
        rows.extend(group_rows)

    expected_group_ids = set(plan["source_cold_group_order"])
    _require({g["group"] for g in cold_groups} == expected_group_ids, "cold group population is incomplete")
    expected_status = Counter(g["evidence_status"] for g in cold_groups)
    _require(expected_status == Counter({"accepted-candidate": 81, "diagnostic-costs-accepted": 1, "quarantined": 1, "blocked": 1}),
             f"unexpected cold group status partition: {expected_status}")
    overhead, warm = _build_overhead_and_warm(root, archive, plan, attempts)
    _require(len(overhead) == 9 and sum(x["sample_count"] for x in overhead) == 27, "overhead evidence is incomplete")
    _require(sum(len(x["groups"]) for x in warm) == 2, "warm family evidence is incomplete")

    accepted = [r for r in rows if r["invocation_cost_accepted"]]
    outcomes = Counter(r["outcome"] for r in rows)
    partial_rows = [r for r in rows if r["partial"]]
    unsupported = [r for r in rows if r["outcome"] == "unsupported"]
    _require(len([r for r in rows if r["group"] == "joern-swift-common108" and r["invocation_cost_accepted"]]) == 96,
             "Swift accepted cost row count differs")
    _require(len(partial_rows) == 4 and len(unsupported) >= 12, "partial or unsupported case rows differ")
    _require(all(r["wall_ms"] is None and not r["invocation_cost_accepted"] for r in unsupported),
             "unsupported cases must have null timing and no accepted cost")
    _require(all(not r["invocation_cost_accepted"] for r in rows if r["group"] == "joern-rust-kernel"),
             "Rust quarantined costs must not enter accepted aggregates")

    family_records: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        family_groups = [g for g in cold_groups if g["analyzer_id"] == family]
        family_rows = [r for r in rows if any(g["group"] == r["group"] for g in family_groups)]
        accepted_rows = [r for r in family_rows if r["invocation_cost_accepted"]]
        raw_outcomes = Counter(r["outcome"] for r in family_rows if r["evidence_status"] != "quarantined")
        quarantined_outcomes = Counter(r["outcome"] for r in family_rows if r["evidence_status"] == "quarantined")
        family_records.append({
            "analyzer_id": family, "name": FAMILY_NAMES[family],
            "planned_cold_groups": sum(1 for g in plan["groups"] if g["kind"] == "cold" and g["family"] == family),
            "candidate_groups": sum(g["evidence_status"] in ("accepted-candidate", "diagnostic-costs-accepted") for g in family_groups),
            "quarantined_groups": sum(g["evidence_status"] == "quarantined" for g in family_groups),
            "blocked_groups": sum(g["evidence_status"] == "blocked" for g in family_groups),
            "report_rows": len(family_rows), "timed_rows": len(accepted_rows),
            "summary_ms": _summary_ms([r["invocation_cost_ms"] for r in accepted_rows]),
            "outcomes": dict(sorted(raw_outcomes.items())),
            "quarantined_outcomes": dict(sorted(quarantined_outcomes.items())),
            "tool_versions": sorted({g.get("tool_version") for g in family_groups if g.get("tool_version")}),
            "groups": [g["group"] for g in family_groups],
        })

    swift_validation = _loads(_read_regular(root, SWIFT_RECEIPT_REL), SWIFT_RECEIPT_REL)
    _require(swift_costs_out is not None, "Swift accepted costs were not produced")
    swift_costs = swift_costs_out
    semgrep_receipt = _loads(_read_regular(root, SEMgrep_RECEIPT_REL), SEMgrep_RECEIPT_REL)
    source_refs = _build_receipt_refs(archive, root)
    source_refs.extend([dict(plan_copy), dict(coverage_copy)])
    summary = {
        "schema": SCHEMA, "publication_id": PUBLICATION_ID, "version": "0.9.2",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "release_commit": RELEASE_COMMIT,
        "population": POPULATION, "fixture_revision": FIXTURE_REVISION,
        "status": "retrospective-diagnostic-publication",
        "publication_eligible": False, "certified_timing": False, "full_model_qualification": False,
        "scored_activation": False, "retrospective": True,
        "totals": {
            "planned_cold_groups": 84, "candidate_cold_groups": 82,
            "completed_candidate_cold_groups": 81, "diagnostic_costs_accepted_cold_groups": 1,
            "quarantined_cold_groups": 1, "blocked_cold_groups": 1,
            "cold_report_rows": len(rows), "accepted_invocation_cost_rows": len(accepted),
            "unsupported_no_invocation_rows": len(unsupported), "partial_invocation_rows": len(partial_rows),
            "successful_analysis_latency_rows": 0,
            "overhead_groups": len(overhead), "overhead_samples": sum(g["sample_count"] for g in overhead),
            "warm_families": len(warm), "warm_batch_samples": sum(g["batch_count"] for fam in warm for g in fam["groups"]),
            "outcomes": dict(sorted(outcomes.items())),
        },
        "analyzer_families": family_records, "groups": cold_groups,
        "overhead_groups": overhead, "warm_families": warm,
        "diagnostic_invocation_costs": {
            "path": "diagnostic-invocation-costs.json", "source_path": SWIFT_COSTS_REL,
            "accepted_rows": swift_costs["accepted_diagnostic_invocation_cost_rows"],
            "successful_analysis_latency_rows": swift_costs["accepted_successful_analysis_latency_rows"],
            "unsupported_no_invocation_rows": swift_costs["unsupported_no_invocation_rows"],
            "partial_rows": len(swift_costs.get("partial_invocations", [])),
            "summary_ms": _summary_ms([r["invocation_cost_ms"] for r in rows
                                       if r["group"] == "joern-swift-common108" and r["invocation_cost_accepted"]]),
            "status": "accepted-diagnostic-invocation-costs",
            "retrospective": True, "publication_eligible": False,
            "source_receipt": archive.add(SWIFT_RECEIPT_REL, kind="reconciliation-receipt"),
        },
        "quarantined_groups": [g["group"] for g in cold_groups if g["evidence_status"] == "quarantined"],
        "blocked_groups": [g["group"] for g in cold_groups if g["evidence_status"] == "blocked"],
        "qualification": {
            "original_controller_acceptance": "failed", "original_a24_settled_qualification_eligible": False,
            "global_quiet_or_contention_certification": False, "descendant_containment": "unproven",
            "no_analyzer_reruns": True, "rust_semantic_mismatch_quarantined": True,
            "codeql_swift_extractor_blocked": True, "swift_full_model_qualification": False,
            "semgrep_warm_controller_failure_preserved": True,
            "semgrep_warm_reconciliation_status": semgrep_receipt["status"],
            "swift_reconciliation_status": swift_validation["status"],
        },
        "limitations": [
            "All values are retrospective diagnostic invocation costs; they do not certify analysis latency or performance.",
            "CPU and host observations remain bound in the evidence archive; global quiet qualification and descendant containment are unproven.",
            "Joern Rust's 62-case semantic mismatch remains quarantined and its raw durations are excluded from accepted aggregates.",
            "CodeQL Swift remains blocked by unresolved pinned extractor/suite discovery; no case timings are fabricated.",
            "Joern Swift contributes 96 accepted diagnostic invocation costs, including four partial invocations; no successful-analysis latency rows are accepted. Twelve unsupported cases have null cost.",
            "Semgrep warm's original controller terminal remains failed. The retrospective A29 audit recovers batch findings and outcomes, but not per-case wall times; cold/warm equivalence remains pending.",
            "Overhead samples are upper-bound estimates and warm batch measurements remain separate from cold case costs.",
            "No cross-release performance claim, full-model qualification, scored activation, or publication certification is asserted.",
        ],
        "source_refs": source_refs,
    }
    plan_out = {
        "schema": "v092-timing-publication-input-plan/v1", "publication_id": PUBLICATION_ID,
        "release_commit": RELEASE_COMMIT, "population": POPULATION, "fixture_revision": FIXTURE_REVISION,
        "source_plan": plan_copy, "capture_coverage": coverage_copy,
        "capture_inventories": [archive.refs[rel] for rel in inventory_docs],
        "cold_group_count": 84, "cold_candidate_group_count": 82,
        "all_analyzers_run": False, "source_archive_contains_selected_inputs": True,
        "input_policy": "Only retained campaign reports, case timing sidecars, group receipts, and accepted retrospective audit inputs are copied byte-for-byte; execution-state is not required after build.",
        "source_files": sorted(archive.refs.values(), key=lambda x: x["path"]),
    }
    return summary, rows, swift_costs, (archive.archive_bytes() if include_archive else b""), plan_out, {"capture_refs": capture_refs, "inventory_docs": inventory_docs}


def _case_ids_from_zip(zf: zipfile.ZipFile, ref: dict[str, Any]) -> set[str]:
    raw = zf.read(ref["archive_path"])
    _require(_sha(raw) == ref["sha256"] and len(raw) == ref["bytes"], "source report hash differs")
    report = _loads(raw, ref["path"])
    return {r["case_id"] for r in report.get("results", [])}


def _write_new(path: Path, raw: bytes) -> None:
    _require(not path.exists() and not path.is_symlink(), f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def build(root_arg: str | Path, output_rel: str = PUBLICATION_REL) -> dict[str, Any]:
    root = Path(root_arg).resolve(strict=True)
    output_rel = _safe_rel(output_rel)
    output = _safe_join(root, output_rel, must_exist=False)
    _require(not output.exists() and not output.is_symlink(), f"publication output already exists: {output_rel}")
    summary, cases, swift_costs, archive_raw, plan_out, _ = _build_publication(root)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    out_dir = output
    out_dir.mkdir(parents=True, exist_ok=False)
    try:
        files: dict[str, bytes] = {
            "summary.json": _json_bytes(summary),
            "cases.json": _json_bytes(cases),
            "diagnostic-invocation-costs.json": _read_regular(root, SWIFT_COSTS_REL),
            "source-evidence.zip": archive_raw,
            "publication-plan.json": _json_bytes(plan_out),
        }
        # `source-index.json` hashes and enumerates the exact zip members, so a
        # clean checkout can verify each copied input without execution-state.
        with zipfile.ZipFile(io.BytesIO(archive_raw), "r") as zf:
            index_entries = []
            for name in sorted(zf.namelist()):
                data = zf.read(name)
                index_entries.append({"archive_path": name, "sha256": _sha(data), "bytes": len(data)})
        files["source-index.json"] = _json_bytes({
            "schema": "v092-timing-publication-source-index/v1",
            "source_archive": "source-evidence.zip", "files": index_entries,
            "file_count": len(index_entries), "total_bytes": sum(x["bytes"] for x in index_entries),
        })
        script_raw = Path(__file__).read_bytes()
        receipt = {
            "schema": "v092-timing-publication-build-receipt/v1", "publication_id": PUBLICATION_ID,
            "created_utc": now, "status": "built-and-source-verified",
            "builder": {"path": "scripts/v092_timing_publication_20261123.py", "sha256": _sha(script_raw), "bytes": len(script_raw)},
            "source_archive_file_count": len(index_entries), "source_archive_bytes_uncompressed": sum(x["bytes"] for x in index_entries),
            "cold_groups": len(summary["groups"]), "case_rows": len(cases),
            "accepted_invocation_cost_rows": summary["totals"]["accepted_invocation_cost_rows"],
            "source_execution_state_required_for_verify_or_stage": False,
            "analyzer_invocations": 0, "publication_eligible": False,
        }
        files["build-receipt.json"] = _json_bytes(receipt)
        file_refs = {
            name.removesuffix(".json").replace("-", "_"): {"path": name, "sha256": _sha(raw), "bytes": len(raw)}
            for name, raw in files.items()
        }
        manifest = {
            "schema": MANIFEST_SCHEMA, "publication_id": PUBLICATION_ID, "version": "0.9.2",
            "created_utc": now, "release_commit": RELEASE_COMMIT, "site_base": SITE_BASE,
            "status": "diagnostic-retrospective", "publication_eligible": False,
            "certified_timing": False, "full_model_qualification": False,
            "files": file_refs, "source_refs": summary["source_refs"],
            "limitations": summary["limitations"],
        }
        files["manifest.json"] = _json_bytes(manifest)
        for name, raw in files.items():
            _write_new(out_dir / name, raw)
        return {"output": output_rel, "files": len(files), "case_rows": len(cases),
                "source_archive_bytes": len(archive_raw), "status": "built-portable-draft-unverified"}
    except Exception:
        # Preserve the failed new output for diagnosis; do not remove evidence.
        raise


def _load_publication(root: Path, relative: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base = _safe_join(root, relative)
    _require(base.is_dir(), f"publication path is not a directory: {relative}")
    manifest = _loads(_read_regular(root, f"{relative}/manifest.json"), "publication manifest")
    _require(manifest.get("schema") == MANIFEST_SCHEMA and manifest.get("publication_id") == PUBLICATION_ID,
             "publication manifest identity differs")
    files = manifest.get("files")
    _require(isinstance(files, dict), "publication manifest has no file map")
    for key, ref in files.items():
        name = _safe_rel(ref.get("path"))
        _require("/" not in name, f"published downloadable file must be top-level: {name}")
        raw = _read_regular(root, f"{relative}/{name}")
        _require((_sha(raw), len(raw)) == (ref.get("sha256"), ref.get("bytes")), f"published file hash mismatch: {name}")
    return manifest, files


def verify(root_arg: str | Path, publication_rel: str = PUBLICATION_REL) -> dict[str, Any]:
    """Replay the pure exporter from only the archived inputs, without analyzers."""
    import tempfile

    root = Path(root_arg).resolve(strict=True)
    publication_rel = _safe_rel(publication_rel)
    manifest, file_refs = _load_publication(root, publication_rel)
    expected_names = {
        "summary.json", "cases.json", "diagnostic-invocation-costs.json",
        "source-evidence.zip", "publication-plan.json", "source-index.json", "build-receipt.json",
    }
    _require({r["path"] for r in file_refs.values()} == expected_names,
             "publication download membership differs")
    for field in ("publication_eligible", "certified_timing", "full_model_qualification"):
        _require(manifest.get(field) is False, f"manifest {field} must remain false")
    _require(manifest.get("release_commit") == RELEASE_COMMIT, "manifest release identity differs")
    def document(name: str) -> Any:
        return _loads(_read_regular(root, f"{publication_rel}/{name}"), name)
    summary, cases, costs = document("summary.json"), document("cases.json"), document("diagnostic-invocation-costs.json")
    plan, index, receipt = document("publication-plan.json"), document("source-index.json"), document("build-receipt.json")
    _require(index.get("schema") == "v092-timing-publication-source-index/v1", "source index schema differs")
    index_entries = index.get("files")
    _require(isinstance(index_entries, list) and index_entries, "empty source index")
    index_map = {item["archive_path"]: item for item in index_entries}
    _require(len(index_map) == len(index_entries), "duplicate source index member")
    _require(index.get("file_count") == len(index_map), "source index count differs")
    _require(index.get("total_bytes") == sum(item["bytes"] for item in index_entries), "source index size differs")
    archive_raw = _read_regular(root, f"{publication_rel}/source-evidence.zip")
    with tempfile.TemporaryDirectory(prefix="dfb-timing-publication-verify-") as temporary:
        snapshot = Path(temporary)
        try:
            with zipfile.ZipFile(io.BytesIO(archive_raw), "r") as zf:
                members = zf.infolist()
                names = [info.filename for info in members]
                _require(len(names) == len(set(names)), "duplicate source archive member")
                _require(set(names) == set(index_map), "source archive membership differs")
                for info in members:
                    name = _safe_rel(info.filename)
                    _require(name.startswith("evidence/") and not info.is_dir(), "invalid source archive prefix")
                    mode = info.external_attr >> 16
                    _require(stat.S_IFMT(mode) in (0, stat.S_IFREG), "non-regular source archive member")
                    item = index_map[name]
                    _require(info.file_size == item["bytes"], f"source archive size differs: {name}")
                    raw = zf.read(info)
                    _require((_sha(raw), len(raw)) == (item["sha256"], item["bytes"]), f"source member hash differs: {name}")
                    relative = _safe_rel(name[len("evidence/"):])
                    _write_new(_safe_join(snapshot, relative, must_exist=False), raw)
        except (zipfile.BadZipFile, OSError) as exc:
            raise PublicationError(f"invalid source archive: {exc}") from exc
        # Reuse the same population, pinned identity, receipt, source-hash,
        # acceptance, timing and aggregate checks as generation. No subprocess
        # or analyzer dispatch exists in this derivation.
        replay_summary, replay_cases, replay_costs, replay_zip, replay_plan, _ = _build_publication(snapshot, include_archive=False)
        replay_summary["created_utc"] = summary.get("created_utc")
        for actual, expected, label in (
            (summary, replay_summary, "summary"), (cases, replay_cases, "case costs"),
            (costs, replay_costs, "Swift costs"), (plan, replay_plan, "source plan"),
        ):
            _require(actual == expected, f"portable replay differs: {label}")
        replay_refs = {ref["archive_path"]: ref for ref in replay_plan["source_files"]}
        _require(len(replay_refs) == len(replay_plan["source_files"]) and set(replay_refs) == set(index_map),
                 "portable source archive replay membership differs")
        for name, ref in replay_refs.items():
            _require((ref["sha256"], ref["bytes"]) == (index_map[name]["sha256"], index_map[name]["bytes"]),
                     f"portable source archive replay differs: {name}")
    _require(manifest.get("source_refs") == summary["source_refs"] and manifest.get("limitations") == summary["limitations"],
             "manifest provenance differs from replayed summary")
    builder = receipt.get("builder", {})
    script_raw = Path(__file__).read_bytes()
    _require(builder.get("sha256") == _sha(script_raw) and builder.get("bytes") == len(script_raw),
             "publication builder identity differs")
    _require(receipt.get("analyzer_invocations") == 0 and receipt.get("publication_eligible") is False,
             "build receipt qualification differs")
    _require(receipt.get("case_rows") == len(cases) and receipt.get("cold_groups") == 84 and
             receipt.get("accepted_invocation_cost_rows") == summary["totals"]["accepted_invocation_cost_rows"],
             "build receipt counts differ")
    return {"status": "verified-portable-publication", "publication_id": PUBLICATION_ID,
            "files": len(file_refs), "case_rows": len(cases), "source_files": len(index_map)}


def stage_site(root_arg: str | Path, output_arg: str | Path, publication_rel: str = PUBLICATION_REL) -> dict[str, Any]:
    root = Path(root_arg).resolve(strict=True)
    publication_rel = _safe_rel(publication_rel)
    verify(root, publication_rel)
    manifest, refs = _load_publication(root, publication_rel)
    output = Path(os.path.abspath(root / output_arg))
    for component in (output, *output.parents):
        _require(not component.is_symlink(), f"symlink staging destination: {component}")
    _require(not output.exists() or output.is_dir(), "staging output is not a directory")
    files = [(ref["path"], _read_regular(root, f"{publication_rel}/{ref['path']}")) for ref in refs.values()]
    files.append(("manifest.json", _read_regular(root, f"{publication_rel}/manifest.json")))
    # Check all existing files before writing, preserving different prior evidence.
    for name, raw in files:
        target = output / _safe_rel(name)
        _require(not target.is_symlink(), f"symlink staged file: {name}")
        if target.exists():
            _require(_read_regular(output, name) == raw, f"refusing to overwrite different staged file: {name}")
    output.mkdir(parents=True, exist_ok=True)
    for name, raw in files:
        if not (output / name).exists():
            _write_new(output / name, raw)
        _require(_read_regular(output, name) == raw, f"staged file hash differs: {name}")
    return {"status": "staged-portable-publication", "output": str(output),
            "publication_id": manifest["publication_id"], "files": len(files)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="build the versioned publication from retained evidence")
    build_parser.add_argument("--root", default=".")
    build_parser.add_argument("--output", default=PUBLICATION_REL)
    verify_parser = sub.add_parser("verify", help="verify committed publication files and portable source archive")
    verify_parser.add_argument("--root", default=".")
    verify_parser.add_argument("--publication", default=PUBLICATION_REL)
    stage_parser = sub.add_parser("stage-site", help="copy verified downloadable files to a new site directory")
    stage_parser.add_argument("--root", default=".")
    stage_parser.add_argument("--publication", default=PUBLICATION_REL)
    stage_parser.add_argument("--output", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.root, args.output)
        elif args.command == "verify":
            result = verify(args.root, args.publication)
        else:
            result = stage_site(args.root, args.output, args.publication)
    except (PublicationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"publication error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
