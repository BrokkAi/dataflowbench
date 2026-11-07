#!/usr/bin/env python3
"""Independently review captured v0.14.4 Bifrost schema-6 controls.

The review distinguishes completed controls, exact retained partial proofs,
unbound near misses, and the native no-rules state. It never converts the
empty native catalog or an incomplete run into evidence of cleanliness.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[5]
QUALIFICATION_DIR = Path(__file__).resolve().parent
CAPTURE_IMPLEMENTATION = QUALIFICATION_DIR / "qualify-bifrost-v0144-01.py"
PRIOR_REVIEW = ROOT / "reports/releases/v0.9.2/qualification/bifrost-review-01.json"
PRIOR_REVIEW_SHA256 = "038cbb99350c5873d3449eaf6bee26315292cfcb256e58bf9d9a1a6a4fd9ef08"
PRIOR_ATTEMPT = ROOT / "reports/releases/v0.9.2/qualification/bifrost-attempt-02"
PRIOR_REVIEW_IMPLEMENTATION = ROOT / "scripts/review-bifrost-v013-controls.py"
PRIOR_REVIEW_IMPLEMENTATION_SHA256 = "02c8fccce53f832c1aa4472b0f0b6efeed9066a51346fa898df1d4bb8f89bd79"
FROZEN_QUALIFIER_SHA256 = "e6ac256769b2f01a3bed30ddcb2b7f15d00fa090fb0cc6dee66414854cf67582"


class ReviewError(ValueError):
    """Captured evidence does not satisfy the v0.14.4 review contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewError(f"cannot read JSON evidence: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewError(f"JSON evidence is not an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewError(message)


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_module():
    return import_module("bifrost_v0144_capture", CAPTURE_IMPLEMENTATION)


def controls_module():
    capture = capture_module()
    controls = capture.controls_for_release()
    controls.REPORT_SCHEMA_VERSION = 6
    return controls


def expected_controls(controls) -> tuple[dict[str, tuple[str, int]], set[str], set[str]]:
    expected: dict[str, tuple[str, int]] = {}
    vacuous: set[str] = set()
    for language in controls.LANGUAGES:
        for role in controls.ROLES:
            for polarity in controls.POLARITIES:
                for variant in ("with", "without"):
                    name = f"policy-{language}-declared-{role}-{polarity}-{variant}"
                    expected[name] = (language, int(polarity == "positive" and variant == "with"))
                    if variant == "without" or (role == "source" and polarity == "negative"):
                        vacuous.add(name)
        for case, variant, count in (
            ("sanitizer-kill-positive", "with", 1),
            ("sanitizer-kill-negative", "with", 0),
            ("sanitizer-kill-negative", "without", 1),
            ("sanitizer-selectivity-positive", "with", 1),
            ("sanitizer-selectivity-negative", "with", 0),
        ):
            expected[f"sanitizer-{language}-{case}-{variant}"] = (language, count)
    other = {
        "identity-version", "identity-build", "catalog-scan-list-builtin-policies",
        "catalog-list-policies", "native-python-source-sink-positive",
    }
    require(len(expected) == 39 and len(vacuous) == 15 and len(other) == 5,
            "frozen control roster changed")
    return expected, vacuous, other


def verify_artifact_manifest(attempt: Path, *, require_closed: bool = True) -> dict:
    require(attempt.is_dir() and not attempt.is_symlink(), "capture root is missing or a symlink")
    manifest_path = attempt / "artifact-hashes.json"
    require(manifest_path.is_file() and not manifest_path.is_symlink(),
            "capture manifest is missing or a symlink")
    manifest = load_json(manifest_path)
    require(manifest.get("schema") == "bifrost-v013-capture-artifacts/v1", "wrong capture manifest schema")
    rows = manifest.get("files")
    require(isinstance(rows, list), "capture manifest has no file inventory")
    seen: set[str] = set()
    for row in rows:
        require(isinstance(row, dict), "capture manifest contains a non-object row")
        relative_text = row.get("path")
        require(isinstance(relative_text, str), "capture manifest path is not text")
        relative = Path(relative_text)
        require(not relative.is_absolute() and ".." not in relative.parts and relative_text not in seen,
                "unsafe or duplicate capture path")
        seen.add(relative_text)
        path = attempt / relative
        require(path.is_file() and not path.is_symlink(), f"missing capture or symlink: {relative_text}")
        require(path.stat().st_size == row.get("bytes") and sha256(path) == row.get("sha256"),
                f"captured file changed: {relative_text}")
    actual: set[str] = set()
    for path in attempt.rglob("*"):
        require(not path.is_symlink(), f"capture contains a symlink: {path.relative_to(attempt)}")
        if path.is_file() and path != manifest_path:
            actual.add(path.relative_to(attempt).as_posix())
    if require_closed:
        require(actual == seen, "capture manifest does not close the exact file inventory")
    return manifest


def normalize_signature(value: dict) -> dict:
    """Ignore only human-readable diagnostic text across analyzer versions."""
    require(isinstance(value, dict), "partial witness signature is not an object")
    diagnostics = value.get("diagnostics")
    require(isinstance(diagnostics, list) and all(isinstance(item, dict) for item in diagnostics),
            "partial witness diagnostics are not typed")
    normalized = dict(value)
    normalized["diagnostics"] = [
        {key: field for key, field in item.items() if key != "message"}
        for item in diagnostics
    ]
    return normalized


def signature(report: dict) -> dict:
    run = report["runs"][0]
    return normalize_signature({
        "completion": run["completion"],
        "findings": [{key: finding.get(key) for key in ("certainty", "proof", "completeness")}
                     for finding in run["findings"]],
        "diagnostics": report["diagnostics"] + run["diagnostics"],
        "endpoints": [metric for metric in run["work"]["metrics"]
                      if metric.get("name") in ("taint.compiled_source_endpoints", "taint.compiled_sink_endpoints")],
    })


def prior_limit_roster() -> dict[str, str]:
    require(PRIOR_REVIEW_IMPLEMENTATION.is_file() and not PRIOR_REVIEW_IMPLEMENTATION.is_symlink(),
            "prior review implementation is missing or redirected")
    require(sha256(PRIOR_REVIEW_IMPLEMENTATION) == PRIOR_REVIEW_IMPLEMENTATION_SHA256,
            "prior limitation roster implementation changed")
    prior = import_module("bifrost_v013_partial_roster", PRIOR_REVIEW_IMPLEMENTATION)
    limits = getattr(prior, "LIMITS", None)
    require(isinstance(limits, dict) and set(limits) == {
        "policy-javascript-declared-source-positive-with",
        "policy-javascript-declared-sink-positive-with",
        "policy-javascript-declared-sink-negative-with",
    }, "prior partial-control roster changed")
    return limits


def _prior_partial_witnesses(controls, root: Path) -> tuple[dict[str, dict], dict]:
    require(PRIOR_REVIEW.is_file() and not PRIOR_REVIEW.is_symlink(), "historical partial review is missing")
    require(sha256(PRIOR_REVIEW) == PRIOR_REVIEW_SHA256, "historical partial review changed")
    prior = load_json(PRIOR_REVIEW)
    require(prior.get("schema") == "v092-bifrost-control-review/v1" and
            prior.get("execution_eligible") is True and prior.get("full_policy_qualification") is False,
            "historical partial review has an unexpected contract")
    # The historical review allowed a later cache inventory sidecar outside
    # its original manifest; only its listed captures are relied upon here.
    old_manifest = verify_artifact_manifest(PRIOR_ATTEMPT, require_closed=False)
    old_manifest_sha = sha256(PRIOR_ATTEMPT / "artifact-hashes.json")
    rows = {row.get("id"): row for row in prior.get("controls", []) if isinstance(row, dict)}
    witnesses = {}
    for name in prior_limit_roster():
        row = rows.get(name)
        if not row or row.get("interpretation") != "inconclusive":
            continue
        report_path = PRIOR_ATTEMPT / "reports" / f"{name}.json"
        report = controls._load_report(report_path)
        actual_signature = signature(report)
        expected_findings = 0 if name == "policy-javascript-declared-sink-negative-with" else 1
        require(row.get("report_sha256") == sha256(report_path) and
                normalize_signature(row.get("current_signature")) == actual_signature,
                f"historical partial proof is not bound to its capture: {name}")
        require(row.get("clean") is False and row.get("findings") == expected_findings and
                len(actual_signature["findings"]) == expected_findings,
                f"historical partial proof has changed finding count or clean status: {name}")
        require(any(item.get("path") == f"reports/{name}.json" for item in old_manifest["files"]),
                f"historical partial report is absent from its artifact manifest: {name}")
        completion = actual_signature["completion"]
        require(completion == {
            "type": "inconclusive", "reasons": ["partial_discovery"],
            "scope": {"type": "files", "files": ["Config.js" if "declared-source" in name else "Audit.js"],
                      "truncated": False},
        }, f"historical partial scope changed: {name}")
        witnesses[name] = actual_signature
    require(set(witnesses) == set(prior_limit_roster()), "historical partial control set changed")
    return witnesses, {"path": str(PRIOR_REVIEW.relative_to(root)), "sha256": PRIOR_REVIEW_SHA256,
                       "capture_manifest_sha256": old_manifest_sha}


def obligations_are_closed(run: dict) -> bool:
    return (run.get("obligations") == [] and run.get("obligations_truncated") is False and
            run.get("omitted_obligations_lower_bound") == 0)


def accepted_exact_partial(name: str, expected_findings: int, report: dict,
                           witness: dict | None) -> bool:
    """Admit only the three pinned partials, retaining unknown coverage."""
    prior_counts = {
        "policy-javascript-declared-source-positive-with": 1,
        "policy-javascript-declared-sink-positive-with": 1,
        "policy-javascript-declared-sink-negative-with": 0,
    }
    if name not in prior_counts or expected_findings != prior_counts[name] or witness is None:
        return False
    run = report["runs"][0]
    findings = run.get("findings")
    if (run.get("completion", {}).get("type") != "inconclusive" or
            not isinstance(findings, list) or len(findings) != expected_findings or
            signature(report) != witness):
        return False
    if expected_findings == 0:
        return name == "policy-javascript-declared-sink-negative-with" and not findings
    return all(
        isinstance(finding.get("certainty"), dict) and finding["certainty"].get("type") == "definite" and
        isinstance(finding.get("proof"), dict) and finding["proof"].get("state") == "proven" and
        isinstance(finding.get("completeness"), dict) and finding["completeness"].get("type") == "complete" and
        isinstance(finding.get("evidence"), dict) and finding["evidence"].get("type") == "taint" and
        isinstance(finding.get("primary"), dict) and isinstance(finding["primary"].get("path"), str)
        for finding in findings
    )


def endpoint_metrics(report: dict) -> list[dict]:
    run = report["runs"][0]
    work = run.get("work")
    require(isinstance(work, dict) and isinstance(work.get("metrics"), list), "run has no work metrics")
    values = [metric for metric in work["metrics"] if isinstance(metric, dict) and
              metric.get("name") in ("taint.compiled_source_endpoints", "taint.compiled_sink_endpoints")]
    by_name = {metric.get("name"): metric for metric in values}
    expected_names = {"taint.compiled_source_endpoints", "taint.compiled_sink_endpoints"}
    require(len(values) == 2 and set(by_name) == expected_names, "endpoint metrics are missing or duplicated")
    for metric in values:
        value = metric.get("value")
        require(isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0,
                "endpoint metric value is invalid")
    return [by_name[name] for name in sorted(expected_names)]


def _validate_report(name: str, language: str, expected_findings: int, vacuous: set[str],
                     path: Path, controls, witness: dict | None) -> dict:
    report = controls._load_report(path)
    require(len(report["runs"]) == len(report["rules"]) == 1, f"wrong rule/run count: {name}")
    run, rule = report["runs"][0], report["rules"][0]
    require(isinstance(run, dict) and isinstance(rule, dict), f"rule/run is not an object: {name}")
    policy_id = f"dataflowbench.taint.model-{language}"
    for item in (run, rule):
        require(item.get("policy_id") == policy_id and item.get("analysis_type") == "taint" and
                isinstance(item.get("policy_hash"), str) and item.get("policy_hash"),
                f"wrong policy identity: {name}")
    require(rule["policy_hash"] == run["policy_hash"], f"rule/run policy hash differs: {name}")
    findings = run.get("findings")
    require(isinstance(findings, list) and len(findings) == expected_findings,
            f"unexpected finding count: {name}")
    require(obligations_are_closed(run), f"schema-6 obligations are incomplete or truncated: {name}")
    require(report.get("diagnostics_truncated") is False and
            report.get("omitted_diagnostics_lower_bound") == 0 and
            run.get("diagnostics_truncated") is False and
            ("omitted_diagnostics_lower_bound" not in run or
             run.get("omitted_diagnostics_lower_bound") == 0),
            f"diagnostics are truncated: {name}")
    for finding in findings:
        controls._validate_finding(finding, policy_id=policy_id, report_path=path)
    completion = run.get("completion")
    require(isinstance(completion, dict) and isinstance(completion.get("type"), str),
            f"run completion is not typed: {name}")
    endpoints = endpoint_metrics(report)
    if name in vacuous:
        require(completion == {"type": "complete"} and not findings,
                f"unbound near-miss is not a completed no-finding control: {name}")
        diagnostics = report["diagnostics"] + run.get("diagnostics", [])
        require(len(diagnostics) == 1, f"unbound near-miss lacks one empty-selection diagnostic: {name}")
        note = diagnostics[0]
        require(note.get("code") == {"type": "empty_selection"} and note.get("severity") == "note" and
                note.get("impact") == "advisory" and note.get("family") == "empty_selection",
                f"unexpected unbound near-miss diagnostic: {name}")
        require(any(metric["value"] == 0 for metric in endpoints),
                f"unbound near-miss lacks a zero endpoint count: {name}")
        return {"id": name, "completion": completion, "findings": 0,
                "interpretation": "unbound-endpoint", "clean": False,
                "report_sha256": sha256(path), "endpoints": endpoints}
    if completion == {"type": "complete"}:
        controls._validate_policy_report(path, language=language, expected_findings=expected_findings)
        require(all(metric["value"] > 0 for metric in endpoints),
                f"completed policy control lacks source/sink engagement: {name}")
        return {"id": name, "completion": completion, "findings": expected_findings,
                "interpretation": "proven-flow" if expected_findings else "complete-no-finding",
                "report_sha256": sha256(path), "endpoints": endpoints}
    require(accepted_exact_partial(name, expected_findings, report, witness),
            f"new or unproven incompleteness is not admissible: {name}")
    require(all(metric["value"] > 0 for metric in endpoints),
            f"partial positive lacks source/sink engagement: {name}")
    return {"id": name, "completion": completion, "findings": expected_findings,
            "interpretation": "inconclusive", "clean": False,
            "report_sha256": sha256(path), "endpoints": endpoints,
            "prior_partial_witness": {"path": "reports/releases/v0.9.2/qualification/bifrost-review-01.json",
                                      "sha256": PRIOR_REVIEW_SHA256}}


def _validate_commands(attempt: Path, commands: list[dict], expected: dict[str, tuple[str, int]],
                       other: set[str], binary_path: str, evaluation_date: str) -> None:
    by_id = {row.get("id"): row for row in commands}
    require(len(commands) == len(by_id) == 44 and set(by_id) == set(expected) | other,
            "control command membership differs from the fixed 44-control roster")
    fixed_argv = {
        "identity-version": [binary_path, "--version"],
        "identity-build": [binary_path, "--build-identity"],
        "catalog-scan-list-builtin-policies": [binary_path, "scan", "--list-builtin-policies"],
        "catalog-list-policies": [binary_path, "--list-policies"],
        "native-python-source-sink-positive": [
            binary_path, "scan", str(attempt / "workspaces/python/native-source-sink-positive"),
            "--format", "json", "--evaluation-date", evaluation_date,
        ],
    }
    for name, command in by_id.items():
        if name in expected:
            language, _expected_findings = expected[name]
            report_path = attempt / "reports" / f"{name}.json"
            expected_argv = [
                binary_path, "--root", str(attempt / "workspaces" / language / name),
                "--policy-file", "policy.rqlp", "--evaluation-date", evaluation_date,
                "--format", "json", "--fail-on", "never", "--output", str(report_path),
            ]
        else:
            report_path = None
            expected_argv = fixed_argv[name]
        require(command.get("argv") == expected_argv,
                f"control invocation differs from the exact v0.14.4 command vector: {name}")
        require(command.get("cwd") == str(attempt / "command-workspaces" / name) and
                command.get("timeout_seconds") == 30,
                f"control working directory or timeout changed: {name}")
        environment = command.get("environment")
        require(isinstance(environment, dict) and environment.get("BIFROST_OPEN_PACKS_DISABLE") == "1",
                f"external policy-pack acquisition was not disabled: {name}")
        for stream in ("stdout", "stderr"):
            path = attempt / stream / f"{name}.txt"
            require(command.get(f"{stream}_path") == str(path) and path.is_file() and not path.is_symlink() and
                    command.get(f"{stream}_sha256") == sha256(path), f"command stream changed: {name}/{stream}")
        if report_path is not None:
            require(command.get("report_path") == str(report_path), f"command report path changed: {name}")
            require(command.get("report_sha256") == sha256(report_path), f"command report digest changed: {name}")
        else:
            require(command.get("report_path") is None and command.get("report_sha256") is None,
                    f"unexpected report binding on identity/catalog control: {name}")
        # The pinned 0.14.4 CLI documents --on-inconclusive=pass by default;
        # report completion is reviewed independently, and the exact captured
        # invocation must still have succeeded as a process.
        require(command.get("exit_code") == 0 and command.get("status") == "completed",
                f"captured CLI invocation did not complete successfully: {name}")


def _validate_strict_failures(qualification: dict, reviewed: dict[str, dict],
                              expected: dict[str, tuple[str, int]], capture: Path) -> dict:
    status = qualification.get("qualification")
    failures = qualification.get("failures")
    require(status in {"qualified", "failed"} and isinstance(failures, list),
            "strict capture result is missing or has an unknown state")
    if status == "qualified":
        require(not failures, "strict capture is marked qualified but carries failures")
        return {"status": status, "failure_count": 0, "reviewed_failures": []}
    require(failures, "strict capture failed without preserving failure reasons")
    names = set(expected)
    schema_failure = re.compile(r"^(.+?): report is not schema_version 5: (.+)$")
    key_failure = re.compile(r"^(.+?): report keys differ from Bifrost schema 5: (.+)$")
    accepted = []
    for failure in failures:
        require(isinstance(failure, str), "strict failure is not text")
        if failure.endswith(" exited 2"):
            name = failure[:-len(" exited 2")]
            require(name in names and reviewed.get(name, {}).get("interpretation") == "inconclusive",
                    f"unreviewed nonzero invocation: {failure}")
            accepted.append(failure)
            continue
        match = schema_failure.match(failure) or key_failure.match(failure)
        if match:
            name, report_text = match.groups()
            report_path = (capture / "reports" / f"{name}.json").resolve()
            require(name in names and name in reviewed and Path(report_text).resolve() == report_path,
                    f"schema-5 strict failure is not bound to a reviewed schema-6 report: {failure}")
            accepted.append(failure)
            continue
        match = re.match(r"^(.+?): run is incomplete \(.+\): (.+)$", failure)
        if match:
            name, report_text = match.groups()
            report_path = (capture / "reports" / f"{name}.json").resolve()
            require(name in names and reviewed.get(name, {}).get("interpretation") == "inconclusive" and
                    Path(report_text).resolve() == report_path,
                    f"strict incomplete-run failure has no exact partial review: {failure}")
            accepted.append(failure)
            continue
        raise ReviewError(f"strict capture has an unexplained failure: {failure}")
    return {"status": status, "failure_count": len(failures), "reviewed_failures": accepted}


def review_capture(attempt: Path, *, root: Path = ROOT) -> dict:
    attempt = Path(attempt).absolute()
    require(not attempt.is_symlink(), "capture path is a symlink")
    attempt = attempt.resolve(strict=True)
    qualification_root = (root / "reports/releases/v0.9.2/qualification/bifrost-v0144-01").resolve()
    require(attempt.is_relative_to(qualification_root) and attempt != qualification_root,
            "capture path is outside the v0.14.4 qualification namespace")
    capture_impl = capture_module()
    identity, acquisition_ref = capture_impl.acquired_identity(root)
    auth, auth_ref = capture_impl.authorization(root)
    manifest = verify_artifact_manifest(attempt)
    context = load_json(attempt / "capture-context.json")
    require(context.get("schema") == "v092-bifrost-v0144-capture-context/v1", "wrong capture context schema")
    require(context.get("tool") == identity and context.get("acquisition_receipt") == acquisition_ref and
            context.get("human_authorization") == auth_ref,
            "capture context does not bind the current acquisition and authorization")
    require(context.get("attempt_path") == str(attempt.relative_to(root)), "capture context path changed")
    require(context.get("controls") == {"invocations": 44, "per_control_timeout_seconds": 30,
                                         "total_timeout_seconds": 600},
            "capture timeout or roster context changed")
    require(context.get("environment") == {"BIFROST_OPEN_PACKS_DISABLE": "1"},
            "capture did not bind external-pack suppression")
    require(context.get("frozen_qualifier") == {
        "path": "scripts/qualify-bifrost-v013.py", "sha256": FROZEN_QUALIFIER_SHA256},
        "capture did not use the exact frozen qualifier")
    require(context.get("capture_implementation", {}).get("path") ==
            str(CAPTURE_IMPLEMENTATION.relative_to(root)) and
            context["capture_implementation"].get("sha256") == sha256(CAPTURE_IMPLEMENTATION),
            "capture implementation changed after collection")
    require(context.get("strict_exit_code") in (0, 1), "strict capture exit status is invalid")

    original = load_json(attempt / "qualification.json")
    require(original.get("schema") == "bifrost-v013-qualification/v1", "strict qualification receipt schema changed")
    require(original.get("tool", {}).get("version") == identity["version"] and
            original["tool"].get("build_identity") == identity["build_identity"] and
            original["tool"].get("public_tag_commit") == identity["public_tag_commit"] and
            original["tool"].get("sha256") == identity["sha256"], "strict capture identity differs from acquisition")
    require(context.get("strict_status") == original.get("qualification"), "capture context strict status differs")
    require(original.get("invocations") == 44 and
            context["strict_exit_code"] == (0 if original["qualification"] == "qualified" else 1),
            "strict capture did not record all 44 controls or its matching exit status")
    commands_path = attempt / "commands.jsonl"
    require(commands_path.is_file() and not commands_path.is_symlink(), "commands.jsonl is missing")
    try:
        commands = [json.loads(line) for line in commands_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewError(f"cannot parse captured commands: {exc}") from exc
    controls = controls_module()
    expected, vacuous, other = expected_controls(controls)
    witnesses, prior_ref = _prior_partial_witnesses(controls, root)
    reviewed = {}
    for name, (language, expected_findings) in sorted(expected.items()):
        report_path = attempt / "reports" / f"{name}.json"
        reviewed[name] = _validate_report(name, language, expected_findings, vacuous, report_path,
                                          controls, witnesses.get(name))
    _validate_commands(attempt, commands, expected, other, identity["path"], controls.EVALUATION_DATE)
    strict = _validate_strict_failures(original, reviewed, expected, attempt)

    stdout = attempt / "stdout"
    version_text = (stdout / "identity-version.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    require(bool(version_text) and version_text[0].strip() == f"bifrost {identity['version']}",
            "captured --version output differs from acquisition")
    require((stdout / "identity-build.txt").read_text(encoding="utf-8").strip() == identity["build_identity"],
            "captured build identity differs from acquisition")
    for name in ("catalog-scan-list-builtin-policies", "catalog-list-policies"):
        require(load_json(stdout / f"{name}.txt") == {"schema_version": 2, "packs": []},
                "embedded policy catalog changed")
    native = load_json(stdout / "native-python-source-sink-positive.txt")
    require(native == {"schema_version": 1, "status": "not-evaluated",
                       "reason": "no-active-rule-packs", "findings": []},
            "native empty-catalog state is not typed not-evaluated")

    rows = list(reviewed.values())
    complete_count = sum(row["completion"] == {"type": "complete"} for row in rows)
    partial_count = sum(row["interpretation"] == "inconclusive" for row in rows)
    sanitizer_count = sum(name.startswith("sanitizer-") for name in reviewed)
    require(sanitizer_count == 15 and len(rows) == 39, "reviewed report partition count changed")
    capture_ref = {"path": str(attempt.relative_to(root)), "sha256": sha256(attempt / "qualification.json"),
                   "strict_status": original["qualification"]}
    return {
        "schema": "v092-bifrost-v0144-control-review/v1",
        "status": "measurement-with-known-limits",
        "execution_eligible": True,
        "full_policy_qualification": False,
        "tool": identity,
        "identity_components": [],
        "invocations": 44,
        "complete_policy_runs": complete_count,
        "inconclusive_policy_runs": partial_count,
        "unbound_endpoint_controls": 15,
        "sanitizer_controls": sanitizer_count,
        "strict_capture": strict,
        "original_qualification": capture_ref,
        "capture_manifest": {"path": str((attempt / "artifact-hashes.json").relative_to(root)),
                             "sha256": sha256(attempt / "artifact-hashes.json"),
                             "files": len(manifest["files"])},
        "acquisition_receipt": acquisition_ref,
        "human_authorization": auth_ref,
        "prior_partial_witness": prior_ref,
        "native": {"interpretation": "not-evaluated", "clean": False, "document": native},
        "review_implementation": {"path": str(Path(__file__).resolve().relative_to(root)),
                                  "sha256": sha256(Path(__file__).resolve())},
        "controls": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = review_capture(args.capture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "execution_eligible": True,
                      "complete_policy_runs": result["complete_policy_runs"],
                      "inconclusive_policy_runs": result["inconclusive_policy_runs"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
