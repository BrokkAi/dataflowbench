#!/usr/bin/env python3
"""Prepare, verify, and stage the separately labelled v0.9.2 timing supplement.

This gate publishes only the retained partial diagnostic timing evidence. It
does not run analyzers, qualify benchmark results, or change the frozen release.
Portable verification restores the existing lossless bundle into a private
temporary directory and replays the pinned reconciliation script over retained
files only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
from typing import Any, Iterable

import evidence_bundle


SCHEMA = "dataflowbench-v0.9.2-timing-supplement-publication/v1"
PUBLICATION_ID = "20261113-v1"
KIND = "partial-diagnostic-timing-supplement"
SITE_BASE = "/evidence/timing/v0-9-2/20261113-v1/"
RELEASE_COMMIT = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
EVIDENCE_COMMIT = "b29e70b9859135c53f08b0205f0d5cd62b89d8ac"
FIXTURE_REVISION = "sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62"
POPULATION = "v0.9.0"

CAMPAIGN_1 = "20261113-01"
CAMPAIGN_2 = "20261113-02"
BASE = "reports/timing/v0.9.2"
CAMPAIGN_1_BASE = f"{BASE}/{CAMPAIGN_1}"
CAMPAIGN_2_BASE = f"{BASE}/{CAMPAIGN_2}"
PUBLICATION_DIR = f"{BASE}/publications/{PUBLICATION_ID}"
MANIFEST_REL = f"{PUBLICATION_DIR}/manifest.json"
SUMMARY_REL = f"{CAMPAIGN_2_BASE}/reconciliation-v1/summary.json"
CASES_REL = f"{CAMPAIGN_2_BASE}/reconciliation-v1/cases.json"
EVIDENCE_MANIFEST_REL = f"{CAMPAIGN_2_BASE}/reconciliation-v1/evidence-manifest.json"
BUNDLE_BASE = f"{CAMPAIGN_2_BASE}/evidence-v1"
BUNDLE_PATH = BUNDLE_BASE
RECONCILE_REL = f"{CAMPAIGN_2_BASE}/reconcile.py"
FROZEN_MANIFEST_REL = "reports/releases/v0.9.2/publication-v1/manifest.json"
SUPPLEMENT_DOC_REL = "docs/v0.9.2-timing-supplement-20261113.md"
EVIDENCE_BUNDLE_TOOL_REL = "scripts/evidence_bundle.py"

PINS: dict[str, tuple[str, int]] = {
    SUMMARY_REL: ("1c6b2490eae0deaa27f0ae0abb2e5afe93da4e0b1a2d3d4914e2db588a2c9c5c", 28691),
    CASES_REL: ("b7bedd8464c0d5833fde50caa539d07058dd1dd16ae031622b605613e687b6ae", 506006),
    EVIDENCE_MANIFEST_REL: ("6de844875f27695e3098e03cae05d4bc0d9478c3c48d2f428314108be0531757", 666475),
    f"{BUNDLE_BASE}/bundle.json": ("1f696e81d1e70563b6c92c7a63b042d9c8e41756368d81e8d559b3612f11b4d2", 736),
    f"{BUNDLE_BASE}/files.jsonl.gz": ("f2da0dbb9042c5d93d01dd36b4629e60ab5b8b34345fb7f8387f58ea703e214e", 133022),
    f"{BUNDLE_BASE}/detail.tar.gz.part0000": ("3ca9aad951ba4bf0b1baea1fd9df890c7999a1f064d960803dcf11d683fe3abf", 7761029),
    f"{CAMPAIGN_1_BASE}/plan.json": ("cae756c3e1cbf5fad54cef3ad5fbbb9accf95cb5cbe1fe3ee640048236f0b844", 641356),
    f"{CAMPAIGN_1_BASE}/campaign-terminal.json": ("c6effaaf89e59253cea26851fb9b8525b02604b94ae98333fae1dcda46d1272c", 151),
    f"{CAMPAIGN_2_BASE}/plan.json": ("0580d4b228d8460e0ea767a3b247746f2e456f853f777c3181696114a5151f20", 642871),
    f"{CAMPAIGN_2_BASE}/campaign-start.json": ("199c71ed9518bde62dff5d1dde21ab0d7f85d399e6372b9301019989e2b7551d", 1148),
    f"{CAMPAIGN_2_BASE}/campaign-terminal.json": ("5615de71d3972acc2fb955ad4edc86a0d703d1e9ef71d72913537f8b4ccf8e51", 179),
    RECONCILE_REL: ("35e0dc1afa6fca5d6044a8b6efaeeef64547543d72bc89c32bf3e3950694d5d2", 7876),
    SUPPLEMENT_DOC_REL: ("41b6d62118103a77965ca8d7a34203eeecd63c623ef4f4054586a0b97e3e443b", 6973),
    FROZEN_MANIFEST_REL: ("2d4a40a10c79813a4dad8e2b8f7340daa6259da0553762a92c5847ec5d91014c", 3801526),
    EVIDENCE_BUNDLE_TOOL_REL: ("099ce4b1e133db9a2abaa658dc957413076f8a28ba00586d6eba63aff7ee942b", 28044),
}

OUTPUT_NAMES = {
    SUMMARY_REL: "summary.json",
    CASES_REL: "cases.json",
    EVIDENCE_MANIFEST_REL: "evidence-manifest.json",
    f"{BUNDLE_BASE}/bundle.json": "evidence-v1/bundle.json",
    # Some static servers treat a .gz URL as transport compression. An
    # opaque suffix keeps these archive bytes intact for browser downloads.
    f"{BUNDLE_BASE}/files.jsonl.gz": "evidence-v1/files.jsonl.gz.bin",
    f"{BUNDLE_BASE}/detail.tar.gz.part0000": "evidence-v1/detail.tar.gz.part0000",
}

EXPECTED_TOOL_BINDINGS = {
    "bifrost": {"sha256": "00b279126297d5e9f7805390799493e915eaf4a2d5940dc3e755138a577a6df9"},
    "infer": {"sha256": "17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62",
               "version": "v1.3.0", "report_version": "v1.3.0"},
    "runner": {"sha256": "934774f0fc21fe2597bc6fbdd827c8cd47a33ad8369d5a3a910e57701fd0e082",
               "bytes": 11005184},
}


class PublicationError(ValueError):
    """Raised when a publication input is unsafe or differs from its pin."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise PublicationError(message)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise PublicationError(f"invalid JSON constant: {value}")


def _json_bytes(value: object, *, pretty: bool = False) -> bytes:
    if pretty:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _load_json(raw: bytes, label: str) -> Any:
    try:
        value = json.loads(raw, object_pairs_hook=_strict_object,
                           parse_constant=_reject_json_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationError(f"invalid {label} JSON: {exc}") from exc
    def require_finite(item: object) -> None:
        if type(item) is float:
            _require(math.isfinite(item), f"non-finite number in {label} JSON")
        elif type(item) is dict:
            for child in item.values():
                require_finite(child)
        elif type(item) is list:
            for child in item:
                require_finite(child)
    require_finite(value)
    return value


def _lexical_absolute(path: os.PathLike[str] | str) -> Path:
    raw = os.fspath(path)
    _require(".." not in Path(raw).parts, "parent path component refused")
    return Path(os.path.abspath(raw))


def _assert_no_symlinks(path: Path) -> None:
    try:
        evidence_bundle._assert_no_symlink_components(path)
    except (OSError, ValueError) as exc:
        raise PublicationError(f"symlink or unsafe path refused: {path}") from exc


def _root(path: os.PathLike[str] | str) -> Path:
    root = _lexical_absolute(path)
    _assert_no_symlinks(root)
    _require(root.is_dir(), f"repository root is not a directory: {root}")
    return root.resolve(strict=True)


def _safe_relative(value: object, label: str) -> str:
    try:
        return evidence_bundle.safe_path(value).as_posix()
    except (TypeError, ValueError) as exc:
        raise PublicationError(f"{label} is not a safe relative path") from exc


def _join(root: Path, value: object, label: str, *, exists: bool = True) -> Path:
    rel = _safe_relative(value, label)
    path = root.joinpath(*PurePosixPath(rel).parts)
    _assert_no_symlinks(path)
    try:
        resolved = path.resolve(strict=exists)
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise PublicationError(f"cannot resolve {label}: {rel}") from exc
    _require(resolved.is_relative_to(resolved_root), f"{label} escapes repository root: {rel}")
    return path


def _signature(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, stat.S_IMODE(value.st_mode))


def _open_regular(path: Path, label: str):
    _assert_no_symlinks(path)
    try:
        before = path.lstat()
        _require(stat.S_ISREG(before.st_mode), f"{label} is not a regular file: {path}")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(fd)
        _require(stat.S_ISREG(opened.st_mode) and _signature(before) == _signature(opened),
                 f"{label} changed before open: {path}")
        return os.fdopen(fd, "rb"), before
    except OSError as exc:
        raise PublicationError(f"cannot open {label}: {path}") from exc


def _file_digest(path: Path, label: str = "file") -> tuple[str, int]:
    stream, before = _open_regular(path, label)
    h = hashlib.sha256()
    size = 0
    try:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
            size += len(block)
        after = os.fstat(stream.fileno())
    finally:
        stream.close()
    _require(_signature(before) == _signature(after) and
             _signature(path.lstat()) == _signature(after),
             f"{label} changed while being read: {path}")
    return h.hexdigest(), size


def _read_file(root: Path, rel: str, label: str = "file", *, max_bytes: int = 64 * 1024 * 1024) -> bytes:
    path = _join(root, rel, label)
    stream, before = _open_regular(path, label)
    try:
        raw = stream.read(max_bytes + 1)
        after = os.fstat(stream.fileno())
    finally:
        stream.close()
    _require(len(raw) <= max_bytes and _signature(before) == _signature(after) and
             _signature(path.lstat()) == _signature(after),
             f"{label} changed or exceeded size limit: {path}")
    return raw


def _ref(root: Path, rel: str, role: str, source_commit: str) -> dict[str, Any]:
    sha, size = _file_digest(_join(root, rel, role), role)
    expected = PINS.get(rel)
    if expected is not None:
        _require((sha, size) == expected, f"pinned {role} differs: {rel}")
    return {"role": role, "path": rel, "source_commit": source_commit,
            "sha256": sha, "bytes": size}


def _pinned_ref(root: Path, rel: str, role: str, source_commit: str) -> dict[str, Any]:
    _require(rel in PINS, f"missing code pin for {rel}")
    sha, size = PINS[rel]
    actual = _file_digest(_join(root, rel, role), role)
    _require(actual == (sha, size), f"pinned {role} differs: {rel}")
    return {"role": role, "path": rel, "source_commit": source_commit,
            "sha256": sha, "bytes": size}


def _load_root_json(root: Path, rel: str, label: str) -> Any:
    return _load_json(_read_file(root, rel, label), label)


def _pinned_downloads(root: Path) -> list[dict[str, Any]]:
    downloads = []
    for rel, site_suffix in OUTPUT_NAMES.items():
        sha, size = _file_digest(_join(root, rel, "download input"), "download input")
        expected = PINS.get(rel)
        _require(expected is not None and (sha, size) == expected,
                 f"pinned download differs: {rel}")
        downloads.append({"path": rel, "sha256": sha, "bytes": size,
                          "site_path": SITE_BASE + site_suffix})
    return downloads


def _validate_bundle_index(root: Path) -> dict[str, Any]:
    index = _load_root_json(root, f"{BUNDLE_BASE}/bundle.json", "bundle index")
    _require(type(index) is dict and index.get("schema") == evidence_bundle.SCHEMA,
             "unknown evidence bundle schema")
    _require(index.get("scope") == "snapshot" and index.get("snapshot_file_count") == 2580 and
             index.get("original_bytes") == 72085596 and index.get("unique_objects") == 2233,
             "lossless evidence bundle inventory differs")
    _require(index.get("benchmark_qualification") is False and
             index.get("publication_authorized") is False,
             "lossless evidence bundle qualification boundary changed")
    _require(index.get("manifest") == {
        "path": "files.jsonl.gz",
        "sha256": PINS[f"{BUNDLE_BASE}/files.jsonl.gz"][0],
        "bytes": PINS[f"{BUNDLE_BASE}/files.jsonl.gz"][1],
    }, "bundle manifest binding differs")
    _require(index.get("parts") == [{
        "path": "detail.tar.gz.part0000",
        "sha256": PINS[f"{BUNDLE_BASE}/detail.tar.gz.part0000"][0],
        "bytes": PINS[f"{BUNDLE_BASE}/detail.tar.gz.part0000"][1],
    }], "bundle archive binding differs")
    return index


def _validate_reconciliation(root: Path) -> tuple[dict[str, Any], list[Any]]:
    summary = _load_root_json(root, SUMMARY_REL, "reconciliation summary")
    _require(type(summary) is dict and summary.get("schema") == "v092-timing-reconciliation/v1",
             "unexpected reconciliation summary")
    _require(summary.get("release_commit") == RELEASE_COMMIT and
             summary.get("publication_eligible") is False,
             "reconciliation release or publication boundary differs")
    totals = summary.get("totals")
    _require(type(totals) is dict and totals == {
        "blocked_cold_groups": 63,
        "completed_cold_groups": 21,
        "completed_overhead_groups": 2,
        "identity_differences": 0,
        "outcome_changes": 0,
        "report_rows": 1170,
        "timed_rows": 1085,
    }, "reconciliation totals differ from the retained partial frontier")
    _require(len(summary.get("cold", [])) == 21 and len(summary.get("overhead", [])) == 2,
             "reconciliation group counts differ")
    for record in summary["cold"]:
        _require(type(record) is dict and record.get("identity_differences") == {} and
                 record.get("outcome_changes") == [] and
                 record.get("qualification", {}).get("certified") is False and
                 record.get("descendant_containment") == "unproven",
                 "cold result identity or qualification boundary changed")
    for record in summary["overhead"]:
        _require(type(record) is dict and record.get("qualification", {}).get("certified") is False,
                 "overhead qualification boundary changed")
    cases = _load_root_json(root, CASES_REL, "per-case timing observations")
    _require(type(cases) is list and len(cases) == 1170, "per-case row count differs")
    timed = [record for record in cases if type(record) is dict and record.get("wall_ms") is not None]
    _require(len(timed) == 1085 and len(cases) - len(timed) == 85,
             "timed and untimed case counts differ")
    for record in cases:
        _require(type(record) is dict and (record.get("wall_ms") is None or
                 (type(record["wall_ms"]) in (int, float) and
                  math.isfinite(record["wall_ms"]) and record["wall_ms"] >= 0)),
                 "invalid timing observation")
    _require(type(summary.get("frozen_manifest")) is dict and
             summary["frozen_manifest"].get("path") == FROZEN_MANIFEST_REL and
             summary["frozen_manifest"].get("sha256") == PINS[FROZEN_MANIFEST_REL][0] and
             summary["frozen_manifest"].get("bytes") == PINS[FROZEN_MANIFEST_REL][1],
             "frozen v0.9.2 publication-manifest binding differs")
    return summary, cases


def _validate_plans(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    plan1 = _load_root_json(root, f"{CAMPAIGN_1_BASE}/plan.json", "campaign 1 plan")
    plan2 = _load_root_json(root, f"{CAMPAIGN_2_BASE}/plan.json", "campaign 2 plan")
    for campaign, plan in ((CAMPAIGN_1, plan1), (CAMPAIGN_2, plan2)):
        _require(type(plan) is dict and plan.get("campaign_id") == campaign and
                 plan.get("release_commit") == RELEASE_COMMIT and
                 plan.get("fixture_revision") == FIXTURE_REVISION and
                 plan.get("population") == POPULATION and
                 plan.get("frozen_release_unchanged") is True and
                 plan.get("new_campaign_not_old_series_resume") is True,
                 f"{campaign} release, fixture, or continuation binding differs")
        _require(type(plan.get("source_projection")) is dict and
                 plan["source_projection"].get("commit") == RELEASE_COMMIT,
                 f"{campaign} source projection is not pinned to the frozen release")
        tools = plan.get("tools")
        _require(type(tools) is dict, f"{campaign} tool bindings are missing")
        for tool, expected in EXPECTED_TOOL_BINDINGS.items():
            actual = tools.get(tool)
            _require(type(actual) is dict and all(actual.get(key) == value
                     for key, value in expected.items()),
                     f"{campaign} {tool} binding differs")
    _require(plan1["tools"] == plan2["tools"], "continuation tool bindings differ from parent campaign")
    _require(plan2.get("continuation", {}).get("parent_campaign_id") == CAMPAIGN_1 and
             plan2.get("continuation", {}).get("no_cold_groups_repeated") is True and
             plan2.get("continuation", {}).get("parent_consumption_charged_to_original_budget") is True,
             "continuation relationship or accounting changed")
    terminal1 = _load_root_json(root, f"{CAMPAIGN_1_BASE}/campaign-terminal.json", "campaign 1 terminal")
    terminal2 = _load_root_json(root, f"{CAMPAIGN_2_BASE}/campaign-terminal.json", "campaign 2 terminal")
    _require(terminal1 == {"group": "overhead-bifrost-php", "reason": "fail-stop; no automatic retry",
                           "status": "stopped", "utc": "2026-11-13T03:39:57.656491+00:00"},
             "campaign 1 terminal record differs")
    _require(terminal2 == {"blocked_cold_groups": 63, "completed_commands": 2,
                           "publication_eligible": False, "status": "partial-frontier-completed",
                           "utc": "2026-11-13T03:47:22.486529+00:00"},
             "campaign 2 terminal record differs")
    return plan1, plan2


def _baseline_refs(summary: dict[str, Any]) -> list[dict[str, Any]]:
    refs: dict[str, tuple[str, int]] = {}
    for record in summary["cold"]:
        baseline = record.get("baseline")
        _require(type(baseline) is dict and type(baseline.get("path")) is str,
                 "cold record is missing its frozen baseline")
        path = _safe_relative(baseline["path"], "baseline path")
        binding = (baseline.get("sha256"), baseline.get("bytes"))
        _require(type(binding[0]) is str and len(binding[0]) == 64 and
                 type(binding[1]) is int and binding[1] >= 0,
                 f"invalid baseline hash/size: {path}")
        _require(path.startswith("reports/releases/v0.9.2/publication-v1/normal/"),
                 f"baseline is outside frozen release scope: {path}")
        _require(path not in refs or refs[path] == binding, f"conflicting baseline binding: {path}")
        refs[path] = binding
    _require(len(refs) == 21, "expected 21 distinct frozen baseline reports")
    return [{"role": "frozen-baseline-report", "path": path,
             "source_commit": RELEASE_COMMIT, "sha256": sha, "bytes": size}
            for path, (sha, size) in sorted(refs.items())]


def build_manifest(root: os.PathLike[str] | str) -> dict[str, Any]:
    """Build the only accepted manifest from pinned retained sources."""
    repo = _root(root)
    downloads = _pinned_downloads(repo)
    bundle_index = _validate_bundle_index(repo)
    summary, _cases = _validate_reconciliation(repo)
    plan1, plan2 = _validate_plans(repo)

    # Bind and validate the frozen release source before recording its 21 report refs.
    frozen = _load_root_json(repo, FROZEN_MANIFEST_REL, "frozen release manifest")
    _require(type(frozen) is dict and frozen.get("qualification_state", {}).get("publication_approved") is False and
             frozen.get("qualification_state", {}).get("scorecard_generation_allowed") is False and
             frozen.get("qualification_state", {}).get("joern_timing_certified") is False,
             "frozen v0.9.2 qualification flags changed")
    _require(summary["frozen_manifest"] == {
        "path": FROZEN_MANIFEST_REL,
        "sha256": PINS[FROZEN_MANIFEST_REL][0],
        "bytes": PINS[FROZEN_MANIFEST_REL][1],
    }, "reconciliation does not bind the frozen release manifest")

    source_refs = [
        _pinned_ref(repo, SUPPLEMENT_DOC_REL, "authored-supplement-document", EVIDENCE_COMMIT),
        _pinned_ref(repo, RECONCILE_REL, "original-reconciliation-script", EVIDENCE_COMMIT),
        _pinned_ref(repo, EVIDENCE_BUNDLE_TOOL_REL, "lossless-bundle-verifier", EVIDENCE_COMMIT),
        _pinned_ref(repo, FROZEN_MANIFEST_REL, "frozen-release-publication-manifest", RELEASE_COMMIT),
    ]
    for rel in (f"{CAMPAIGN_1_BASE}/plan.json", f"{CAMPAIGN_1_BASE}/campaign-terminal.json",
                f"{CAMPAIGN_2_BASE}/plan.json", f"{CAMPAIGN_2_BASE}/campaign-start.json",
                f"{CAMPAIGN_2_BASE}/campaign-terminal.json"):
        source_refs.append(_pinned_ref(repo, rel, "campaign-plan-or-receipt", EVIDENCE_COMMIT))
    for download in downloads:
        rel = download["path"]
        source_refs.append({"role": "published-evidence-download", "path": rel,
                            "source_commit": EVIDENCE_COMMIT,
                            "sha256": download["sha256"], "bytes": download["bytes"]})
    baseline_refs = _baseline_refs(summary)
    for ref in baseline_refs:
        current = _file_digest(_join(repo, ref["path"], "frozen baseline"), "frozen baseline")
        _require(current == (ref["sha256"], ref["bytes"]),
                 f"frozen baseline bytes differ: {ref['path']}")
    source_refs.extend(baseline_refs)

    # The first campaign's plan and its continuation bind the same immutable
    # release population, fixture, and binaries; keep the binding visible here.
    campaigns = []
    for campaign, plan in ((CAMPAIGN_1, plan1), (CAMPAIGN_2, plan2)):
        plan_rel = f"{BASE}/{campaign}/plan.json"
        terminal_rel = f"{BASE}/{campaign}/campaign-terminal.json"
        start_rel = f"{BASE}/{campaign}/campaign-start.json"
        item: dict[str, Any] = {
            "id": campaign,
            "release_commit": RELEASE_COMMIT,
            "fixture_revision": FIXTURE_REVISION,
            "population": POPULATION,
            "plan": {"path": plan_rel, "sha256": PINS[plan_rel][0], "bytes": PINS[plan_rel][1]},
            "terminal": {"path": terminal_rel, "sha256": PINS[terminal_rel][0], "bytes": PINS[terminal_rel][1]},
        }
        if campaign == CAMPAIGN_2:
            item["start"] = {"path": start_rel, "sha256": PINS[start_rel][0], "bytes": PINS[start_rel][1]}
        campaigns.append(item)

    # Keep the raw bundle's existing qualification flags intact. Publication
    # authorization here is only for this diagnostic supplement artifact.
    _require(bundle_index.get("publication_authorized") is False and
             summary.get("publication_eligible") is False,
             "retained qualification flags must remain false")
    return {
        "schema": SCHEMA,
        "id": PUBLICATION_ID,
        "kind": KIND,
        "site_base": SITE_BASE,
        "release": {"version": "v0.9.2", "commit": RELEASE_COMMIT},
        "evidence": {
            "commit": EVIDENCE_COMMIT,
            "fixture_revision": FIXTURE_REVISION,
            "population": POPULATION,
            "campaigns": [CAMPAIGN_1, CAMPAIGN_2],
        },
        "authorization": {
            "user_authorized": True,
            "scope": "publish only as a separately labelled partial DIAGNOSTIC timing supplement",
            "recorded": "2026-11-13",
        },
        "campaigns": campaigns,
        "source_refs": source_refs,
        "downloads": downloads,
        "counts": dict(summary["totals"]),
        "qualification": {
            "publication_eligible": False,
            "benchmark_qualification": False,
            "timing_certified": False,
            "quiet_certification": False,
            "descendant_containment_proven": False,
            "performance_improvement_certified": False,
            "cross_release_speedup_claim": False,
            "correctness_scoring_changed": False,
        },
    }


def _validate_manifest(root: Path, manifest: object) -> dict[str, Any]:
    _require(type(manifest) is dict, "publication manifest must be an object")
    expected = build_manifest(root)
    _require(_json_bytes(manifest) == _json_bytes(expected),
             "publication manifest differs from the pinned diagnostic-only manifest")
    return expected


def _copy_verified_ref_into_snapshot(current_root: Path, snapshot_root: Path,
                                     ref: dict[str, Any]) -> None:
    rel = _safe_relative(ref.get("path"), "source-ref path")
    expected = (ref.get("sha256"), ref.get("bytes"))
    _require(type(expected[0]) is str and type(expected[1]) is int,
             f"invalid source-ref binding: {rel}")
    source = _join(current_root, rel, "portable source ref")
    actual = _file_digest(source, "portable source ref")
    _require(actual == expected, f"current source ref differs from pinned bytes: {rel}")
    target_rel = "snapshot/" + rel
    target = _join(snapshot_root, target_rel, "restored source ref", exists=False)
    if os.path.lexists(target):
        _assert_no_symlinks(target)
        _require(_file_digest(target, "restored source ref") == expected,
                 f"restored source ref differs from pinned bytes: {rel}")
        return

    _assert_no_symlinks(target.parent)
    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(target.parent)
    source_stream, source_before = _open_regular(source, "portable source ref")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    h = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as output:
            for block in iter(lambda: source_stream.read(1024 * 1024), b""):
                output.write(block)
                h.update(block)
                size += len(block)
        after = os.fstat(source_stream.fileno())
        _require(_signature(source_before) == _signature(after) and
                 _signature(source.lstat()) == _signature(after) and
                 (h.hexdigest(), size) == expected,
                 f"source ref changed while copying: {rel}")
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    finally:
        source_stream.close()


def _load_restored_reconcile(snapshot_root: Path) -> Any:
    rel = "snapshot/" + RECONCILE_REL
    path = _join(snapshot_root, rel, "restored reconciliation script")
    _require(_file_digest(path, "restored reconciliation script") == PINS[RECONCILE_REL],
             "restored reconciliation script differs from its evidence-commit pin")
    name = "_v092_timing_original_reconcile"
    spec = importlib.util.spec_from_file_location(name, path)
    _require(spec is not None and spec.loader is not None,
             "cannot import restored reconciliation script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    _require(module.ROOT == snapshot_root.resolve(strict=True) / "snapshot",
             "restored reconciliation root is not the portable snapshot")
    return module


def _compare_reconciliation(snapshot_root: Path, current_root: Path) -> dict[str, Any]:
    # Summary metadata names the 21 baselines and original reconciliation binds
    # every candidate output. Copy those frozen inputs only after their own
    # manifest-bound bytes have been checked; existing restore copies must match.
    summary = _load_root_json(current_root, SUMMARY_REL, "reconciliation summary")
    refs = [
        {"path": FROZEN_MANIFEST_REL,
         "sha256": summary["frozen_manifest"]["sha256"],
         "bytes": summary["frozen_manifest"]["bytes"]},
        *_baseline_refs(summary),
    ]
    for ref in refs:
        _copy_verified_ref_into_snapshot(current_root, snapshot_root, ref)

    module = _load_restored_reconcile(snapshot_root)
    with tempfile.TemporaryDirectory(prefix="v092-timing-reconcile-") as temp:
        output = Path(temp) / "derived"
        module.OUT = output
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            module.main()
        expected_output = {
            "summary.json": SUMMARY_REL,
            "cases.json": CASES_REL,
            "evidence-manifest.json": EVIDENCE_MANIFEST_REL,
        }
        for name, rel in expected_output.items():
            generated = output / name
            _require(generated.is_file() and not generated.is_symlink(),
                     f"portable reconciliation did not generate {name}")
            _require(generated.read_bytes() == _read_file(current_root, rel, name),
                     f"portable reconciliation differs from retained {name}")
    # The root reconciliation has only retained-file inputs and no analyzer calls.
    # Its output is checked byte-for-byte, not interpreted as qualification.
    return {"status": "verified", "derived_files": 3}


def verify(root: os.PathLike[str] | str) -> dict[str, Any]:
    """Verify source pins, restore the lossless bundle privately, and replay outputs."""
    repo = _root(root)
    manifest_rel = MANIFEST_REL
    manifest = _load_json(_read_file(repo, manifest_rel, "publication manifest"),
                          "publication manifest")
    _validate_manifest(repo, manifest)

    bundle_path = _join(repo, BUNDLE_BASE, "evidence bundle")
    with tempfile.TemporaryDirectory(prefix="v092-timing-portable-") as temp:
        restored = Path(temp) / "restore"
        result = evidence_bundle.check(bundle_path, restore=restored)
        _require(result.get("status") == "verified" and result.get("restored") is True and
                 result.get("files") == 2580 and result.get("original_bytes") == 72085596,
                 "existing lossless evidence bundle did not restore its pinned inventory")
        reconciliation = _compare_reconciliation(restored, repo)

    return {
        "status": "verified",
        "kind": KIND,
        "publication_eligible": False,
        "bundle": {"files": 2580, "original_bytes": 72085596},
        "reconciliation": reconciliation,
        "counts": manifest["counts"],
    }


def _write_new(path: Path, raw: bytes) -> None:
    _assert_no_symlinks(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(path.parent)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    except FileExistsError as exc:
        raise PublicationError(f"append-only publication file already exists: {path}") from exc
    except OSError as exc:
        raise PublicationError(f"cannot create publication file: {path}") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def prepare(root: os.PathLike[str] | str) -> dict[str, Any]:
    """Create the append-only publication manifest after local source checks."""
    repo = _root(root)
    path = _join(repo, MANIFEST_REL, "new publication manifest", exists=False)
    _require(not os.path.lexists(path), "publication manifest already exists")
    manifest = build_manifest(repo)
    raw = _json_bytes(manifest, pretty=True)
    _write_new(path, raw)
    return {"status": "prepared", "manifest": MANIFEST_REL,
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "downloads": len(manifest["downloads"]),
            "qualification": manifest["qualification"]}


def _output_root(root: Path, output: os.PathLike[str] | str | None) -> Path:
    if output is None:
        output_path = root / "docs/public/evidence/timing/v0-9-2/20261113-v1"
    else:
        output_path = _lexical_absolute(output)
    _assert_no_symlinks(output_path)
    return output_path


def _copy_no_overwrite(source: Path, destination: Path, ref: dict[str, Any]) -> None:
    expected = (ref.get("sha256"), ref.get("bytes"))
    _require(type(expected[0]) is str and type(expected[1]) is int,
             f"invalid staged file pin: {source}")
    _assert_no_symlinks(destination.parent)
    if os.path.lexists(destination):
        _require(_file_digest(destination, "existing staged file") == expected,
                 f"refusing to overwrite a different staged file: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(destination.parent)
    source_stream, before = _open_regular(source, "staged source")
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    h = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as output:
            for block in iter(lambda: source_stream.read(1024 * 1024), b""):
                output.write(block)
                h.update(block)
                size += len(block)
        after = os.fstat(source_stream.fileno())
        _require(_signature(before) == _signature(after) and
                 _signature(source.lstat()) == _signature(after) and
                 (h.hexdigest(), size) == expected,
                 f"source changed or differs while staging: {source}")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        source_stream.close()


def stage_site(root: os.PathLike[str] | str,
               output: os.PathLike[str] | str | None = None) -> dict[str, Any]:
    """Verify and copy immutable publication inputs below a site output directory."""
    repo = _root(root)
    destination = _output_root(repo, output)
    # Ensure an output path cannot alias or contain the source evidence or manifest.
    resolved = destination.resolve(strict=False)
    _require(resolved != repo and not resolved.is_relative_to(repo / BUNDLE_BASE),
             "site output cannot replace the repository or evidence bundle")
    manifest_path = _join(repo, MANIFEST_REL, "publication manifest")
    manifest_raw = _read_file(repo, MANIFEST_REL, "publication manifest")
    manifest = _load_json(manifest_raw, "publication manifest")
    verification = verify(repo)
    _require(verification.get("status") == "verified", "portable evidence verification failed")
    _require(_read_file(repo, MANIFEST_REL, "publication manifest") == manifest_raw,
             "publication manifest changed during site verification")
    staged_manifest = {"sha256": hashlib.sha256(manifest_raw).hexdigest(),
                       "bytes": len(manifest_raw)}
    destination.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(destination)
    _copy_no_overwrite(manifest_path, destination / "manifest.json", staged_manifest)

    staged = 0
    for download in manifest["downloads"]:
        source = _join(repo, download["path"], "download source")
        site_path = download["site_path"]
        _require(type(site_path) is str and site_path.startswith(SITE_BASE),
                 "unsafe download site path")
        suffix = site_path[len(SITE_BASE):]
        relative = _safe_relative(suffix, "download site suffix")
        target = destination.joinpath(*PurePosixPath(relative).parts)
        _require(target.resolve(strict=False).is_relative_to(destination.resolve(strict=True)),
                 "download site path escapes output directory")
        _copy_no_overwrite(source, target, download)
        staged += 1
    return {"status": "staged", "output": str(destination),
            "manifest": "manifest.json", "downloads": staged,
            "verification": "verified"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "stage-site"):
        child = commands.add_parser(name)
        child.add_argument("--root", type=Path, default=Path.cwd())
        if name == "stage-site":
            child.add_argument("--output", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.root)
        elif args.command == "verify":
            result = verify(args.root)
        else:
            result = stage_site(args.root, args.output)
    except (OSError, PublicationError, RuntimeError, ValueError) as exc:
        print(f"publication gate refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
