#!/usr/bin/env python3
"""Prospectively qualify the public Bifrost 0.13.0 policy surface.

This control is deliberately independent of the release runner.  It binds one
binary, runs every command serially in an output-owned environment, and keeps
the raw command streams beside the reports it checks.  A successful return
means that the supplied-policy controls completed with the expected findings,
and that the public no-pack catalog and native no-rules diagnostic were both
observed.  An empty native finding set is never interpreted as a clean result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import Callable, Mapping, Sequence, TextIO


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.13.0"
EXPECTED_BUILD_IDENTITY = "9426a205c6ced4d438182068995d6279f0d885fe"
EXPECTED_BINARY_SHA256 = "640d0b8e4fe5fb34159c184f994e245021825b05e6144a09f2b4be9a76b129c9"
PUBLIC_TAG_COMMIT = "9ed06580b2a4334750cb98dbbf2dfe9cf840e55a"
TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 600
EVALUATION_DATE = "2026-08-11"
REPORT_SCHEMA_VERSION = 5
REPORT_KEYS = {
    "schema_version",
    "evaluation",
    "execution",
    "rules",
    "runs",
    "suppressions",
    "scope",
    "packs",
    "diagnostics",
    "diagnostics_truncated",
    "omitted_diagnostics_lower_bound",
    "worst_omitted_diagnostic_severity",
}
LANGUAGES = ("java", "javascript", "python")
ROLES = ("source", "sink")
POLARITIES = ("positive", "negative")
ENVIRONMENT_ALLOWLIST = ("BIFROST_CACHE_ROOT", "LANG", "PATH", "TMPDIR")


class QualificationError(ValueError):
    """A preflight or evidence validation error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_exists(path: Path) -> bool:
    # Path.exists() is false for a broken symlink; an output path must be new
    # in either case.
    return os.path.lexists(str(path))


def _json_dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _signal_group(process: subprocess.Popen[bytes], sig: int) -> None:
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def _stop_process_group(process: subprocess.Popen[bytes], grace_seconds: int = 1) -> None:
    _signal_group(process, signal.SIGTERM)
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # The leader may have exited while a child remains in the new session.
        _signal_group(process, signal.SIGKILL)
        process.wait()


def _run_bounded(
    argv: Sequence[str | Path], *, cwd: Path, stdout: object, stderr: object,
    env: Mapping[str, str], timeout: int = TIMEOUT_SECONDS,
) -> int:
    """Run one command in its own process group, with no retry."""
    process = subprocess.Popen(
        [str(value) for value in argv],
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        env=dict(env),
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _stop_process_group(process)
        return 124
    except BaseException:
        _stop_process_group(process)
        raise


def _fixture(root: Path, workspace: Path, language: str, case: str) -> Path:
    source = root / "cases/taint" / language / case
    if not source.is_dir():
        raise QualificationError(f"missing fixture directory: {source}")
    destination = workspace / language / case
    destination.mkdir(parents=True, exist_ok=False)
    copied = 0
    for path in sorted(source.iterdir()):
        if path.name == "case.json":
            continue
        if not path.is_file():
            raise QualificationError(f"fixture member is not a regular file: {path}")
        shutil.copy2(path, destination / path.name)
        copied += 1
    if copied == 0:
        raise QualificationError(f"fixture has no source files: {source}")
    return destination


def _remove_declared_role(policy: str, role: str) -> str:
    """Remove exactly the declared source or sink entry from a policy copy."""
    if role not in ROLES:
        raise QualificationError(f"unknown declared role: {role}")
    needle = f"({role} :id declared-{role}"
    start = policy.find(needle)
    if start < 0:
        raise QualificationError(f"declared {role} entry is missing from policy")
    if policy.find(needle, start + len(needle)) >= 0:
        raise QualificationError(f"declared {role} entry occurs more than once")

    depth = 0
    in_string = False
    escaped = False
    in_comment = False
    end: int | None = None
    for index in range(start, len(policy)):
        character = policy[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == ";":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise QualificationError(f"unterminated declared {role} entry")
    transformed = policy[:start] + policy[end:]
    if f":id declared-{role}" in transformed:
        raise QualificationError(f"counterfactual retained declared {role}")
    return transformed


def _environment(*, cache_root: Path, tmpdir: Path) -> dict[str, str]:
    """Return the complete subprocess environment, without host secrets."""
    return {
        "BIFROST_CACHE_ROOT": str(cache_root),
        "LANG": "C.UTF-8",
        "PATH": os.defpath,
        "TMPDIR": str(tmpdir),
    }


def _is_complete(completion: object) -> bool:
    return isinstance(completion, dict) and completion.get("type") == "complete"


def _load_report(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise QualificationError(f"missing JSON report: {path}")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualificationError(f"invalid JSON report {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise QualificationError(f"report is not a JSON object: {path}")
    if set(report) != REPORT_KEYS:
        raise QualificationError(
            f"report keys differ from Bifrost schema 5: {path} "
            f"(missing={sorted(REPORT_KEYS - set(report))}, "
            f"extra={sorted(set(report) - REPORT_KEYS)})"
        )
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise QualificationError(f"report is not schema_version 5: {path}")
    for key in ("rules", "runs", "diagnostics", "suppressions", "scope"):
        if not isinstance(report.get(key), list):
            raise QualificationError(f"report field {key} is not a list: {path}")
    if not isinstance(report.get("execution"), dict) or not isinstance(report.get("evaluation"), dict):
        raise QualificationError(f"report execution/evaluation shape is invalid: {path}")
    return report


def _validate_finding(finding: object, *, policy_id: str, report_path: Path) -> None:
    if not isinstance(finding, dict):
        raise QualificationError(f"finding is not an object: {report_path}")
    if finding.get("policy_id") != policy_id or finding.get("analysis_type") != "taint":
        raise QualificationError(f"finding identity does not match policy: {report_path}")
    completeness = finding.get("completeness")
    if not isinstance(completeness, dict) or completeness.get("type") != "complete":
        raise QualificationError(f"finding completeness is not complete: {report_path}")
    evidence = finding.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("type") != "taint":
        raise QualificationError(f"finding has no retained taint evidence: {report_path}")
    proof = finding.get("proof")
    if not isinstance(proof, dict) or proof.get("state") != "proven":
        raise QualificationError(f"finding is not proven: {report_path}")
    primary = finding.get("primary")
    if not isinstance(primary, dict) or not isinstance(primary.get("path"), str):
        raise QualificationError(f"finding has no primary source location: {report_path}")


def _validate_policy_report(
    path: Path, *, language: str, expected_findings: int,
) -> dict[str, object]:
    report = _load_report(path)
    policy_id = f"dataflowbench.taint.model-{language}"
    rules = report["rules"]
    runs = report["runs"]
    assert isinstance(rules, list) and isinstance(runs, list)
    if len(rules) != 1 or len(runs) != 1:
        raise QualificationError(f"expected exactly one rule and run: {path}")
    rule, run = rules[0], runs[0]
    if not isinstance(rule, dict) or not isinstance(run, dict):
        raise QualificationError(f"rule/run is not an object: {path}")
    for item, label in ((rule, "rule"), (run, "run")):
        if item.get("policy_id") != policy_id or item.get("analysis_type") != "taint":
            raise QualificationError(f"{label} identity differs from {policy_id}: {path}")
        if not isinstance(item.get("policy_hash"), str) or not item["policy_hash"]:
            raise QualificationError(f"{label} has no policy hash: {path}")
    if rule["policy_hash"] != run["policy_hash"]:
        raise QualificationError(f"rule/run policy hashes differ: {path}")
    completion = run.get("completion")
    if not isinstance(completion, dict) or not isinstance(completion.get("type"), str):
        raise QualificationError(f"run completion is absent or untyped: {path}")
    if not _is_complete(completion):
        raise QualificationError(f"run is incomplete ({completion!r}): {path}")
    diagnostics = report["diagnostics"] + (run.get("diagnostics") if isinstance(run.get("diagnostics"), list) else [])
    if diagnostics:
        raise QualificationError(f"complete policy run retained diagnostics: {path}")
    findings = run.get("findings")
    work = run.get("work")
    if not isinstance(findings, list) or not isinstance(work, dict):
        raise QualificationError(f"run findings/work shape is invalid: {path}")
    if not isinstance(work.get("scanned_files"), int) or not isinstance(work.get("retained_findings"), int):
        raise QualificationError(f"run work does not prove completed analysis: {path}")
    if len(findings) != expected_findings:
        raise QualificationError(
            f"expected {expected_findings} findings, observed {len(findings)}: {path}"
        )
    for finding in findings:
        _validate_finding(finding, policy_id=policy_id, report_path=path)
    return {
        "policy_id": policy_id,
        "completion": completion,
        "findings": len(findings),
        "expected_findings": expected_findings,
        "evidence": "proven-taint-finding" if findings else "complete-no-finding",
    }


def _diagnostic_has_no_rules(report: Mapping[str, object]) -> bool:
    diagnostics = report.get("diagnostics")
    if not isinstance(diagnostics, list) or not diagnostics:
        return False
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            continue
        # Bifrost's diagnostic contract uses a typed code object and a string
        # family. A prose message, a differently named family, or a nested
        # arbitrary value is not evidence for this control.
        code = diagnostic.get("code")
        if isinstance(code, dict) and code.get("type") == "no_rules_evaluated":
            return True
        if diagnostic.get("family") == "no_rules_evaluated":
            return True
    return False


def _validate_native_report(path: Path) -> dict[str, object]:
    report = _load_report(path)
    if report["rules"] != [] or report["runs"] != []:
        raise QualificationError(f"native scan unexpectedly evaluated rules: {path}")
    if not _diagnostic_has_no_rules(report):
        raise QualificationError(
            f"native empty result has no explicit no_rules_evaluated diagnostic: {path}"
        )
    return {
        "interpretation": "confirmed-no-rules-evaluated",
        "clean": False,
        "rules": 0,
        "runs": 0,
        "diagnostics": len(report["diagnostics"]),
    }


class ProbeRun:
    def __init__(
        self,
        *,
        bifrost: Path,
        output: Path,
        cache_root: Path,
        runner: Callable[..., int] | None,
    ) -> None:
        self.bifrost = bifrost
        self.output = output
        self.cache_root = cache_root
        self.runner = runner or _run_bounded
        self.tmp_root = output / "tmp"
        self.environment = _environment(
            cache_root=cache_root, tmpdir=self.tmp_root
        )
        self.workspace_root = output / "workspaces"
        self.command_root = output / "command-workspaces"
        self.report_root = output / "reports"
        self.policy_root = output / "policies"
        for directory in (
            self.workspace_root, self.command_root, self.report_root, self.policy_root,
            cache_root, self.tmp_root,
        ):
            directory.mkdir(parents=True, exist_ok=False)
        self.log: TextIO = (output / "commands.jsonl").open("x", encoding="utf-8")
        self.failures: list[str] = []
        self.failed = False
        self.started = time.monotonic()
        self.deadline = self.started + TOTAL_TIMEOUT_SECONDS
        self.records: list[dict[str, object]] = []

    def fail(self, message: str) -> None:
        self.failed = True
        self.failures.append(message)

    def _record(self, record: dict[str, object]) -> None:
        self.records.append(record)
        self.log.write(json.dumps(record, sort_keys=True) + "\n")
        self.log.flush()

    def run(
        self,
        name: str,
        argv: Sequence[str | Path],
        *,
        report_path: Path | None = None,
    ) -> int:
        command_cwd = self.command_root / name
        command_cwd.mkdir(parents=True, exist_ok=False)
        stdout_path = self.output / "stdout" / f"{name}.txt"
        stderr_path = self.output / "stderr" / f"{name}.txt"
        stdout_path.parent.mkdir(exist_ok=True)
        stderr_path.parent.mkdir(exist_ok=True)
        environment = dict(self.environment)
        record: dict[str, object] = {
            "id": name,
            "argv": [str(value) for value in argv],
            "cwd": str(command_cwd),
            "environment": environment,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "report_path": str(report_path) if report_path is not None else None,
            "timeout_seconds": TIMEOUT_SECONDS,
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        code: int | None = None
        status = "launch-error"
        error: str | None = None
        try:
            with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                remaining = int(self.deadline - time.monotonic())
                if remaining <= 0:
                    status = "not-started-total-timeout"
                    code = 124
                    self.fail(f"total control budget exhausted before {name}")
                else:
                    timeout = min(TIMEOUT_SECONDS, remaining)
                    code = int(self.runner(
                        [str(value) for value in argv],
                        cwd=command_cwd,
                        stdout=stdout,
                        stderr=stderr,
                        env=environment,
                        timeout=timeout,
                    ))
                    status = "timeout" if code == 124 else ("completed" if code == 0 else "failed")
                    if code != 0:
                        self.fail(f"{name} exited {code}")
        except OSError as exc:
            error = str(exc)
            code = 127
            self.fail(f"{name} launch error: {exc}")
        finally:
            record.update({
                "status": status,
                "exit_code": code,
                "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "stdout_sha256": _sha256(stdout_path) if stdout_path.is_file() else None,
                "stderr_sha256": _sha256(stderr_path) if stderr_path.is_file() else None,
                "report_sha256": _sha256(report_path) if report_path is not None and report_path.is_file() else None,
            })
            if error is not None:
                record["error"] = error
            self._record(record)
        return int(code if code is not None else 127)

    def close(self) -> None:
        self.log.close()


def _expected_findings(case: str, variant: str) -> int:
    if case.endswith("positive"):
        return 1 if variant == "with" else 0
    return 0


def _write_policy_variant(
    probe: ProbeRun, *, root: Path, language: str, role: str, polarity: str, variant: str,
) -> tuple[Path, Path, int]:
    case = f"model-declared-{role}-{polarity}"
    name = f"policy-{language}-declared-{role}-{polarity}-{variant}"
    source = root / "cases/taint" / language / case
    if not source.is_dir():
        raise QualificationError(f"missing fixture directory: {source}")
    work = probe.workspace_root / language / name
    work.mkdir(parents=True, exist_ok=False)
    for path in sorted(source.iterdir()):
        if path.name == "case.json":
            continue
        if not path.is_file():
            raise QualificationError(f"fixture member is not a regular file: {path}")
        shutil.copy2(path, work / path.name)
    policy_source = (root / "adapters/bifrost/policies" / f"model-{language}.rqlp").read_text(encoding="utf-8")
    policy = policy_source if variant == "with" else _remove_declared_role(policy_source, role)
    policy_path = probe.policy_root / f"{name}.rqlp"
    policy_path.write_text(policy, encoding="utf-8")
    shutil.copy2(policy_path, work / "policy.rqlp")
    report_path = probe.report_root / f"{name}.json"
    argv: list[str | Path] = [
        probe.bifrost,
        "--root", work,
        "--policy-file", "policy.rqlp",
        "--evaluation-date", EVALUATION_DATE,
        "--format", "json",
        "--fail-on", "never",
        "--output", report_path,
    ]
    return work, report_path, _expected_findings(case, variant)


def _run_bifrost(probe: ProbeRun, root: Path) -> None:
    for language in LANGUAGES:
        for role in ROLES:
            for polarity in POLARITIES:
                for variant in ("with", "without"):
                    name = f"policy-{language}-declared-{role}-{polarity}-{variant}"
                    try:
                        _work, report, expected = _write_policy_variant(
                            probe, root=root, language=language, role=role,
                            polarity=polarity, variant=variant,
                        )
                        probe.run(name, [
                            probe.bifrost,
                            "--root", _work,
                            "--policy-file", "policy.rqlp",
                            "--evaluation-date", EVALUATION_DATE,
                            "--format", "json",
                            "--fail-on", "never",
                            "--output", report,
                        ], report_path=report)
                        try:
                            result = _validate_policy_report(report, language=language, expected_findings=expected)
                            _json_dump(probe.output / "summaries" / f"{name}.json", result)
                        except QualificationError as exc:
                            probe.fail(f"{name}: {exc}")
                    except (OSError, QualificationError) as exc:
                        probe.fail(f"{name}: {exc}")


def _write_sanitizer_variant(
    probe: ProbeRun, *, root: Path, language: str, case: str, policy_variant: str,
) -> tuple[Path, Path, int, str]:
    name = f"sanitizer-{language}-{case.removeprefix('model-')}-{policy_variant}"
    source = root / "cases/taint" / language / case
    work = probe.workspace_root / language / name
    work.mkdir(parents=True, exist_ok=False)
    for path in sorted(source.iterdir()):
        if path.name != "case.json":
            shutil.copy2(path, work / path.name)
    policy_source = (root / "adapters/bifrost/policies" / f"model-{language}.rqlp").read_text(encoding="utf-8")
    policy = policy_source if policy_variant == "with" else _remove_sanitizer_section(policy_source)
    policy_path = probe.policy_root / f"{name}.rqlp"
    policy_path.write_text(policy, encoding="utf-8")
    shutil.copy2(policy_path, work / "policy.rqlp")
    report = probe.report_root / f"{name}.json"
    expected = 1 if case.endswith("kill-positive") or case.endswith("selectivity-positive") or (
        case.endswith("kill-negative") and policy_variant == "without"
    ) else 0
    return work, report, expected, name


def _remove_sanitizer_section(policy: str) -> str:
    marker = ":sanitizers (endpoint-set :entries ["
    start = policy.find(marker)
    if start < 0:
        raise QualificationError("sanitizer section is missing from policy")
    end_marker = ":sinks (endpoint-set"
    end = policy.find(end_marker, start)
    if end < 0:
        raise QualificationError("sanitizer section has no following sinks section")
    return policy[:start] + policy[end:]


def _run_sanitizer_controls(probe: ProbeRun, root: Path) -> None:
    controls = (
        ("model-sanitizer-kill-positive", "with"),
        ("model-sanitizer-kill-negative", "with"),
        ("model-sanitizer-kill-negative", "without"),
        ("model-sanitizer-selectivity-positive", "with"),
        ("model-sanitizer-selectivity-negative", "with"),
    )
    for language in LANGUAGES:
        for case, policy_variant in controls:
            try:
                work, report, expected, name = _write_sanitizer_variant(
                    probe, root=root, language=language, case=case, policy_variant=policy_variant
                )
                probe.run(name, [
                    probe.bifrost,
                    "--root", work,
                    "--policy-file", "policy.rqlp",
                    "--evaluation-date", EVALUATION_DATE,
                    "--format", "json",
                    "--fail-on", "never",
                    "--output", report,
                ], report_path=report)
                try:
                    result = _validate_policy_report(report, language=language, expected_findings=expected)
                    _json_dump(probe.output / "summaries" / f"{name}.json", result)
                except QualificationError as exc:
                    probe.fail(f"{name}: {exc}")
            except (OSError, QualificationError) as exc:
                probe.fail(f"sanitizer-{language}-{case}-{policy_variant}: {exc}")


def _validate_catalog(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualificationError(f"invalid policy catalog {path}: {exc}") from exc
    if document != {"schema_version": 2, "packs": []}:
        raise QualificationError(f"public v0.13 catalog is not schema 2 with packs=[]: {path}")
    return {"schema_version": 2, "packs": [], "sha256": _sha256(path)}


def _run_catalog_and_native_controls(probe: ProbeRun, root: Path) -> dict[str, object]:
    version_name = "identity-version"
    probe.run(version_name, [probe.bifrost, "--version"])
    version_text = (probe.output / "stdout" / f"{version_name}.txt").read_text(encoding="utf-8", errors="replace")
    version_lines = [line.strip() for line in version_text.splitlines() if line.strip()]
    first_version_line = version_lines[0] if version_lines else ""
    if first_version_line != f"bifrost {EXPECTED_VERSION}":
        probe.fail(f"--version did not report bifrost {EXPECTED_VERSION}")

    identity_name = "identity-build"
    probe.run(identity_name, [probe.bifrost, "--build-identity"])
    identity = (probe.output / "stdout" / f"{identity_name}.txt").read_text(encoding="utf-8", errors="replace").strip()
    if identity != EXPECTED_BUILD_IDENTITY:
        probe.fail(f"--build-identity differs from pinned identity: {identity!r}")

    scan_catalog = probe.output / "catalog-scan.json"
    list_catalog = probe.output / "catalog-list-policies.json"
    probe.run("catalog-scan-list-builtin-policies", [probe.bifrost, "scan", "--list-builtin-policies"])
    probe.run("catalog-list-policies", [probe.bifrost, "--list-policies"])
    scan_stdout = probe.output / "stdout/catalog-scan-list-builtin-policies.txt"
    list_stdout = probe.output / "stdout/catalog-list-policies.txt"
    if scan_stdout.is_file():
        shutil.copy2(scan_stdout, scan_catalog)
    if list_stdout.is_file():
        shutil.copy2(list_stdout, list_catalog)
    catalog_summary: dict[str, object] = {}
    try:
        scan_document = _validate_catalog(scan_catalog)
        list_document = _validate_catalog(list_catalog)
        if json.loads(scan_catalog.read_text(encoding="utf-8")) != json.loads(
            list_catalog.read_text(encoding="utf-8")
        ):
            raise QualificationError("scan --list-builtin-policies and --list-policies documents differ")
        catalog_summary = {
            "scan": scan_document,
            "list_policies": list_document,
            "agree": True,
        }
        _json_dump(probe.output / "catalog-summary.json", catalog_summary)
    except QualificationError as exc:
        probe.fail(str(exc))

    native_name = "native-python-source-sink-positive"
    native_work = _fixture(root, probe.workspace_root, "python", "native-source-sink-positive")
    native_report = probe.report_root / f"{native_name}.json"
    probe.run(native_name, [
        probe.bifrost,
        "scan", native_work,
        "--format", "json",
        "--evaluation-date", EVALUATION_DATE,
        "--output", native_report,
    ], report_path=native_report)
    try:
        native_summary = _validate_native_report(native_report)
        _json_dump(probe.output / "native-summary.json", native_summary)
    except QualificationError as exc:
        probe.fail(str(exc))
    return catalog_summary


def _write_artifact_hashes(output: Path) -> None:
    artifacts: list[dict[str, object]] = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name == "artifact-hashes.json":
            continue
        artifacts.append({
            "path": path.relative_to(output).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    _json_dump(output / "artifact-hashes.json", {
        "schema": "bifrost-v013-capture-artifacts/v1",
        "files": artifacts,
    })


def capture(
    bifrost: Path,
    output: Path,
    *,
    root: Path = ROOT,
    runner: Callable[..., int] | None = None,
) -> int:
    """Capture one new qualification root and return 0 only if it qualifies."""
    bifrost = Path(bifrost)
    output = Path(output)
    root = Path(root)
    if not bifrost.is_absolute():
        raise QualificationError("--bifrost must be an absolute path")
    if not output.is_absolute():
        raise QualificationError("--output must be an absolute path")
    if not bifrost.is_file():
        raise QualificationError(f"--bifrost is not a regular file: {bifrost}")
    if _path_exists(output):
        raise QualificationError(f"--output already exists: {output}")
    actual_sha256 = _sha256(bifrost)
    if actual_sha256 != EXPECTED_BINARY_SHA256:
        raise QualificationError(
            f"wrong Bifrost binary SHA-256: expected {EXPECTED_BINARY_SHA256}, got {actual_sha256}"
        )
    if not root.is_dir():
        raise QualificationError(f"repository root is missing: {root}")

    output.mkdir(parents=True, exist_ok=False)
    probe = ProbeRun(
        bifrost=bifrost,
        output=output,
        cache_root=output / "cache",
        runner=runner,
    )
    catalog_summary: dict[str, object] = {}
    try:
        _json_dump(output / "tool-identity.json", {
            "bifrost": str(bifrost),
            "version": EXPECTED_VERSION,
            "build_identity": EXPECTED_BUILD_IDENTITY,
            "public_tag_commit": PUBLIC_TAG_COMMIT,
            "expected_sha256": EXPECTED_BINARY_SHA256,
            "observed_sha256": actual_sha256,
            "timeout_seconds": TIMEOUT_SECONDS,
            "total_timeout_seconds": TOTAL_TIMEOUT_SECONDS,
            "cache_root": str(output / "cache"),
            "environment_allowlist": list(ENVIRONMENT_ALLOWLIST),
        })
        catalog_summary = _run_catalog_and_native_controls(probe, root)
        _run_bifrost(probe, root)
        _run_sanitizer_controls(probe, root)
    except (OSError, QualificationError) as exc:
        probe.fail(str(exc))
    finally:
        probe.close()
        _json_dump(output / "qualification.json", {
            "schema": "bifrost-v013-qualification/v1",
            "qualification": "failed" if probe.failed else "qualified",
            "tool": {
                "version": EXPECTED_VERSION,
                "build_identity": EXPECTED_BUILD_IDENTITY,
                "public_tag_commit": PUBLIC_TAG_COMMIT,
                "sha256": actual_sha256,
                "environment_allowlist": list(ENVIRONMENT_ALLOWLIST),
            },
            "catalog": catalog_summary,
            "invocations": len(probe.records),
            "completed_invocations": sum(record.get("status") == "completed" for record in probe.records),
            "failed_invocations": sum(record.get("status") in {"failed", "timeout", "launch-error", "not-started-total-timeout"} for record in probe.records),
            "failures": probe.failures,
            "evidence": {
                "commands": "commands.jsonl",
                "stdout": "stdout/",
                "stderr": "stderr/",
                "reports": "reports/",
                "artifact_hashes": "artifact-hashes.json",
            },
        })
        _write_artifact_hashes(output)
    return 1 if probe.failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bifrost", required=True, type=Path, help="absolute path to the pinned Bifrost binary")
    parser.add_argument("--output", required=True, type=Path, help="new absolute task-owned capture directory")
    args = parser.parse_args()
    try:
        return capture(args.bifrost, args.output)
    except (OSError, QualificationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
