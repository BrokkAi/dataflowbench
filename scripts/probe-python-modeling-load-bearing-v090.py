#!/usr/bin/env python3
"""Capture the preregistered Python load-bearing controls for v0.9.0."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import threading
from contextlib import contextmanager
from typing import Callable, Mapping, Sequence, TextIO


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reports/releases/v0.9.0/execution-v1/contract.json"
OUTPUT_ROOT = ROOT / "reports/raw/load-bearing-python-modeling-v090"
TIMEOUT_SECONDS = 600
TOOL_KEYS = ("bifrost", "codeql", "codeql-packs", "joern", "semgrep", "semgrep-core")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tool_record(tools: Mapping[str, object], key: str) -> Mapping[str, object]:
    entry = tools.get(key)
    if not isinstance(entry, dict):
        raise ValueError(f"v0.9 contract has no pinned tool record for {key}")
    return entry


def _bound_contract_input(root: Path, reference: Mapping[str, object], label: str) -> Path:
    relative = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(relative, str) or not isinstance(digest, str):
        raise ValueError(f"contract has no path and digest for {label}")
    candidate_path = Path(relative)
    if candidate_path.is_absolute() or ".." in candidate_path.parts:
        raise ValueError(f"unsafe contract input path for {label}")
    candidate = root / candidate_path
    if not candidate.is_file() or _sha256(candidate) != digest:
        raise ValueError(f"contract input digest differs for {label}: {relative}")
    return candidate


def _check_control_environment(contract: Mapping[str, object], root: Path) -> dict[str, str]:
    reference = contract.get("control_inventory")
    if not isinstance(reference, dict):
        raise ValueError("v0.9 contract has no bound control inventory")
    relative = reference.get("path")
    if not isinstance(relative, str):
        raise ValueError("v0.9 contract control inventory path is missing")
    identities = contract.get("input_identities")
    if not isinstance(identities, dict) or identities.get(relative) != reference.get("sha256"):
        raise ValueError("control inventory is not bound by the v0.9 contract identities")
    inventory_path = _bound_contract_input(root, reference, "control inventory")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory.get("schema") != "release-control-inventory/v1" or inventory.get("release") != "v0.9.0":
        raise ValueError("control inventory is not the bound v0.9.0 inventory")
    control_id = "probe-python-modeling-load-bearing"
    if control_id not in inventory.get("supplemental_control_ids", []):
        raise ValueError("Python modeling probe is not listed in supplemental_control_ids")
    matches = [
        item for item in inventory.get("controls", [])
        if isinstance(item, dict) and item.get("id") == control_id
    ]
    if len(matches) != 1:
        raise ValueError("control inventory must contain exactly one Python modeling probe")
    control = matches[0]
    script_path = "scripts/probe-python-modeling-load-bearing-v090.py"
    script_digest = _sha256(root / script_path)
    identities = contract.get("input_identities", {})
    if identities.get(script_path) != script_digest:
        raise ValueError("Python modeling probe differs from contract input identity")
    script_identity = control.get("script_identity")
    if not isinstance(script_identity, list) or script_identity != [
        {"path": script_path, "sha256": script_digest}
    ]:
        raise ValueError("Python modeling probe differs from control inventory script identity")
    argv = control.get("argv")
    if not isinstance(argv, list) or not argv or argv[-1] != "scripts/probe-python-modeling-load-bearing-v090.py":
        raise ValueError("Python modeling control inventory points at a different script")
    roots = control.get("output_roots")
    scratch_relative = "reports/raw/control-scratch/probe-python-modeling-load-bearing"
    if not isinstance(roots, list) or scratch_relative not in roots or "reports/raw/load-bearing-python-modeling-v090" not in roots:
        raise ValueError("Python modeling control inventory output roots differ from the probe")
    environment = control.get("environment")
    if not isinstance(environment, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in environment.items()
    ):
        raise ValueError("Python modeling control inventory has no explicit environment")
    scratch = environment.get("TMPDIR")
    if not isinstance(scratch, str) or not Path(scratch).is_absolute():
        raise ValueError("Python modeling control inventory TMPDIR must be absolute")
    expected_suffix = Path(scratch_relative).parts
    if Path(scratch).parts[-len(expected_suffix):] != expected_suffix:
        raise ValueError("Python modeling control inventory TMPDIR is outside its declared scratch root")
    if not Path(scratch).is_dir():
        raise ValueError(f"recorder-created control TMPDIR is missing: {scratch}")
    return dict(environment)


def _check_held_tool_digests(
    contract: Mapping[str, object], contract_path: Path, root: Path,
) -> dict[str, Mapping[str, object]]:
    """Bind the tools this probe invokes to both contract and held digest evidence."""
    tools = contract.get("tools")
    if not isinstance(tools, dict):
        raise ValueError("v0.9 contract tools must be an object")

    evidence_refs = [
        item for item in contract.get("identity_evidence", [])
        if isinstance(item, dict) and item.get("path", "").endswith("/held-tool-digests.json")
    ]
    if len(evidence_refs) != 1:
        raise ValueError("v0.9 contract must bind exactly one held-tool digest manifest")
    identities = contract.get("input_identities")
    if not isinstance(identities, dict) or identities.get(evidence_refs[0].get("path")) != evidence_refs[0].get("sha256"):
        raise ValueError("held-tool digest manifest is not bound by contract input identities")
    evidence_path = _bound_contract_input(root, evidence_refs[0], "held-tool-digests")
    evidence_sha = _sha256(evidence_path)
    if evidence_refs[0].get("sha256") != evidence_sha:
        raise ValueError("held-tool-digests.json differs from the v0.9 contract identity evidence")

    held = json.loads(evidence_path.read_text(encoding="utf-8"))
    artifacts = held.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("held-tool-digests.json artifacts must be a list")
    by_id = {item.get("id"): item for item in artifacts if isinstance(item, dict)}

    pinned: dict[str, Mapping[str, object]] = {}
    for key in TOOL_KEYS:
        entry = _tool_record(tools, key)
        path = entry.get("path")
        digest = entry.get("sha256")
        if key == "codeql-packs":
            # The pack tree has its own contract identity; it is not a held file
            # in held-tool-digests.json.
            if not isinstance(path, str) or not path or not isinstance(entry.get("tree_sha256"), str):
                raise ValueError("v0.9 contract has no pinned CodeQL pack tree identity")
            if not Path(path).is_dir():
                raise ValueError(f"pinned CodeQL pack tree is missing: {path}")
            pinned[key] = entry
            continue

        if not isinstance(path, str) or not path or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"v0.9 contract has no path and SHA-256 for {key}")
        record = by_id.get(key)
        if key == "codeql":
            # The held-file manifest predates the restored 2.27.1 CLI and has
            # no CodeQL row. Its current identity is bound by the Swift plan.
            if isinstance(record, dict):
                if record.get("path") != path or record.get("sha256") != digest:
                    raise ValueError("held CodeQL digest conflicts with the current v0.9 pin")
        elif not isinstance(record, dict) or record.get("path") != path or record.get("sha256") != digest:
            raise ValueError(f"held digest record differs from the v0.9 contract for {key}")
        candidate = Path(path)
        if not candidate.is_file():
            raise ValueError(f"pinned tool file is missing or not regular: {path}")
        if _sha256(candidate) != digest:
            raise ValueError(f"pinned tool digest differs from v0.9 contract: {path}")
        pinned[key] = entry

    _check_codeql_cli_tree(contract, root, pinned["codeql"])

    pack_refs = [
        item for item in contract.get("identity_evidence", [])
        if isinstance(item, dict) and item.get("path", "").endswith("/non-swift-codeql-packs.json")
    ]
    if len(pack_refs) != 1:
        raise ValueError("v0.9 contract must bind exactly one non-Swift CodeQL pack inventory")
    if identities.get(pack_refs[0].get("path")) != pack_refs[0].get("sha256"):
        raise ValueError("CodeQL pack inventory is not bound by contract input identities")
    pack_manifest_path = _bound_contract_input(root, pack_refs[0], "CodeQL pack inventory")
    pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8"))
    pack_root = Path(str(pinned["codeql-packs"].get("path", "")))
    if pack_manifest.get("root") != str(pack_root):
        raise ValueError("CodeQL pack inventory root differs from the v0.9 contract")
    expected_files = pack_manifest.get("files")
    if not isinstance(expected_files, list) or not expected_files:
        raise ValueError("CodeQL pack inventory files must be a nonempty list")
    expected: dict[str, Mapping[str, object]] = {}
    for item in expected_files:
        if not isinstance(item, dict):
            raise ValueError("invalid CodeQL pack inventory entry")
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ValueError("CodeQL pack inventory entry has no relative path")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or relative in expected:
            raise ValueError(f"unsafe or duplicate CodeQL pack path: {relative}")
        expected[relative_path.as_posix()] = item
    observed: set[str] = set()
    for directory, dirs, files in os.walk(pack_root, followlinks=False):
        base = Path(directory)
        for name in list(dirs):
            child = base / name
            if child.is_symlink():
                raise ValueError(f"CodeQL pack inventory contains an unexpected symlink: {child}")
        for name in files:
            candidate = base / name
            relative = candidate.relative_to(pack_root).as_posix()
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError(f"CodeQL pack inventory contains a nonregular file: {candidate}")
            item = expected.get(relative)
            if item is None:
                raise ValueError(f"unlisted CodeQL pack file: {relative}")
            if candidate.stat().st_size != item.get("bytes") or _sha256(candidate) != item.get("sha256"):
                raise ValueError(f"CodeQL pack file differs from v0.9 inventory: {relative}")
            observed.add(relative)
    if observed != set(expected):
        missing = sorted(set(expected) - observed)
        raise ValueError("CodeQL pack files missing from pinned tree: " + ", ".join(missing[:5]))
    return pinned


def _check_codeql_cli_tree(
    contract: Mapping[str, object], root: Path, codeql: Mapping[str, object],
) -> None:
    plans = contract.get("swift_plans")
    if not isinstance(plans, dict) or not isinstance(plans.get("codeql"), dict):
        raise ValueError("v0.9 contract has no bound current CodeQL Swift plan")
    plan_ref = plans["codeql"]
    input_identities = contract.get("input_identities")
    if not isinstance(input_identities, dict) or input_identities.get(plan_ref.get("path")) != plan_ref.get("sha256"):
        raise ValueError("CodeQL Swift plan is not bound by contract input identities")
    plan_path = _bound_contract_input(root, plan_ref, "CodeQL Swift plan")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    runtime = plan.get("runtime")
    manifests = runtime.get("manifests") if isinstance(runtime, dict) else None
    if not isinstance(runtime, dict) or runtime.get("codeql") != codeql.get("path"):
        raise ValueError("CodeQL CLI path differs from the current Swift runtime plan")
    if not isinstance(manifests, dict) or not isinstance(manifests.get("cli_tree"), dict):
        raise ValueError("CodeQL Swift plan has no bound CLI tree manifest")
    tree_ref = manifests["cli_tree"]
    tree_path = _bound_contract_input(root, tree_ref, "CodeQL CLI tree manifest")
    expected_tree = json.loads(tree_path.read_text(encoding="utf-8"))
    # Reuse the runner's established runtime membership, byte, symlink, and
    # mode inventory so the executable hash is tied to its current CLI tree.
    try:
        from swift_normal_runner_v1 import file_inventory
    except ImportError as exc:
        raise ValueError("cannot load the CodeQL runtime tree verifier") from exc
    cli_path = Path(str(codeql["path"]))
    if file_inventory(cli_path.parent) != expected_tree:
        raise ValueError("CodeQL CLI runtime tree differs from the current Swift plan")


def _python_environment(
    contract: Mapping[str, object], tool: str, control_environment: Mapping[str, str],
) -> dict[str, str]:
    groups = contract.get("groups")
    if not isinstance(groups, list):
        raise ValueError("v0.9 contract groups must be a list")
    group_id = f"{tool}-python-modeling"
    matches = [group for group in groups if isinstance(group, dict) and group.get("id") == group_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one explicit environment group {group_id}")
    environment = matches[0].get("environment")
    if not isinstance(environment, dict) or not environment or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in environment.items()
    ):
        raise ValueError(f"missing explicit tool environment: {group_id}")
    selected = dict(environment)
    # Keep subprocess-created temporary files below the recorder-owned control
    # scratch directory named by the hash-bound inventory.
    selected["TMPDIR"] = control_environment["TMPDIR"]
    return selected


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
        # The leader may exit while one of its children remains in the group.
        _signal_group(process, signal.SIGKILL)
        process.wait()


def _run_bounded(
    argv: Sequence[str | Path], *, cwd: Path, stdout: object, stderr: object,
    env: Mapping[str, str], timeout: int = TIMEOUT_SECONDS,
) -> int:
    process = subprocess.Popen(
        [str(value) for value in argv], cwd=cwd, stdout=stdout, stderr=stderr,
        env=dict(env), start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _stop_process_group(process)
        return 124
    except BaseException:
        # Covers KeyboardInterrupt and caller cancellation while the child is
        # running; preserve the original exception after the whole group exits.
        _stop_process_group(process)
        raise


class ProbeInterrupted(InterruptedError):
    """Raised when the outer recorder interrupts this probe process."""


@contextmanager
def _outer_interrupt_handlers():
    """Turn recorder signals into exceptions so nested process cleanup runs."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}

    def interrupt(signum: int, _frame: object) -> None:
        raise ProbeInterrupted(f"received signal {signum}")

    try:
        for sig in previous:
            signal.signal(sig, interrupt)
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _fixture(root: Path, workspace: Path, name: str, arm: str) -> Path:
    destination = workspace / arm
    destination.mkdir(parents=True)
    source = root / "cases/taint/python" / name
    for path in source.glob("*.py"):
        shutil.copy2(path, destination / path.name)
    return destination


class ProbeRun:
    def __init__(
        self, *, root: Path, output: Path, contract: Mapping[str, object],
        tools: Mapping[str, Mapping[str, object]], control_environment: Mapping[str, str],
        runner: Callable[..., int] | None,
    ) -> None:
        self.root = root
        self.output = output
        self.workspace = output / "workspace"
        self.contract = contract
        self.tools = tools
        self.control_environment = control_environment
        self.runner = runner
        self.failed = False
        self.log: TextIO = (output / "commands.jsonl").open("x", encoding="utf-8")

    def run(self, name: str, tool: str, argv: Sequence[str | Path]) -> int:
        start = dt.datetime.now(dt.timezone.utc).isoformat()
        environment = _python_environment(self.contract, tool, self.control_environment)
        stdout_path = self.output / f"{name}-stdout.txt"
        stderr_path = self.output / f"{name}-stderr.txt"
        command_cwd = self.output / "command-workspaces" / name
        command_cwd.mkdir(parents=True, exist_ok=False)
        record: dict[str, object] = {
            "id": name,
            "argv": [str(value) for value in argv],
            "tool": tool,
            "cwd": str(command_cwd),
            "environment": environment,
            "start_utc": start,
            "timeout_seconds": TIMEOUT_SECONDS,
        }
        code: int | None = None
        status = "launch-error"
        error: str | None = None
        try:
            with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                execute = self.runner or _run_bounded
                code = int(execute(
                    [str(value) for value in argv], cwd=command_cwd,
                    stdout=stdout, stderr=stderr, env=environment,
                    timeout=TIMEOUT_SECONDS,
                ))
            status = "timeout" if code == 124 else ("completed" if code == 0 else "failed")
            self.failed |= code != 0
            return code
        except OSError as exc:
            error = str(exc)
            self.failed = True
            return 127
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
            self.failed = True
            raise
        finally:
            record.update({
                "status": status,
                "exit_code": code,
                "end_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            })
            if error is not None:
                record["error"] = error
            self.log.write(json.dumps(record, sort_keys=True) + "\n")
            self.log.flush()


def _run_bifrost(probe: ProbeRun) -> None:
    root, output, workspace = probe.root, probe.output, probe.workspace
    policy = (root / "adapters/bifrost/policies/model-python.rqlp").read_text(encoding="utf-8")
    for role in ("source", "sink"):
        for polarity in ("positive", "negative"):
            for variant in ("with", "without"):
                name = f"bifrost-declared-{role}-{polarity}-{variant}"
                work = _fixture(root, workspace, f"model-declared-{role}-{polarity}", name)
                lines = policy.splitlines(keepends=True)
                if variant == "without":
                    matched = False
                    for index, line in enumerate(lines):
                        if ":id declared-" + role in line:
                            lines[index] = line[:line.index("(" + role)] + line[line.rindex("])") :]
                            matched = True
                            break
                    if not matched:
                        raise ValueError(f"declared {role} model missing from policy")
                artifact = output / f"{name}.rqlp"
                artifact.write_text("".join(lines), encoding="utf-8")
                shutil.copy2(artifact, work / "policy.rqlp")
                probe.run(name, "bifrost", [
                    probe.tools["bifrost"]["path"], "--root", work,
                    "--policy-file", "policy.rqlp", "--evaluation-date", "2026-08-11",
                    "--format", "json", "--fail-on", "never", "--output", output / f"{name}.json",
                ])


def _run_codeql(probe: ProbeRun) -> None:
    root, output, workspace = probe.root, probe.output, probe.workspace
    work = _fixture(root, workspace, "model-opaque-propagator-positive", "codeql-source")
    database = workspace / "codeql-db"
    codeql = probe.tools["codeql"]["path"]
    if probe.run("codeql-extract", "codeql", [
        codeql, "database", "create", database, "--language=python",
        "--source-root=" + str(work), "--overwrite",
    ]) == 0:
        for variant, query in (("with", "PythonModeling.ql"), ("without", "PythonModelingProbe.ql")):
            name = "codeql-opaque-" + variant
            probe.run(name, "codeql", [
                codeql, "database", "analyze", database,
                root / "adapters/codeql/python/queries" / query,
                "--format=sarif-latest", "--output=" + str(output / (name + ".sarif.json")),
                "--rerun", "--additional-packs=" + str(probe.tools["codeql-packs"]["path"]),
            ])


def _run_joern(probe: ProbeRun) -> None:
    root, output, workspace = probe.root, probe.output, probe.workspace
    semantics = (root / "adapters/joern/semantics/model-python.semantics").read_text(encoding="utf-8")
    needle = '"clean.py:<module>.scrub"'
    if not any(line.startswith(needle) for line in semantics.splitlines()):
        raise ValueError("declared sanitizer semantics missing from Python model")
    controls = (
        ("sanitizer-with", "model-sanitizer-kill-negative", False),
        ("sanitizer-without", "model-sanitizer-kill-negative", True),
        ("propagator-unmodeled", "model-opaque-propagator-positive", False),
        ("summary-unmodeled", "model-summary-through-positive", False),
    )
    for name, case, remove in controls:
        work = _fixture(root, workspace, case, "joern-" + name)
        semantics_path = output / ("joern-" + name + ".semantics")
        semantics_path.write_text("".join(
            line for line in semantics.splitlines(keepends=True)
            if not (remove and line.startswith(needle))
        ), encoding="utf-8")
        argv: list[str | Path] = [probe.tools["joern"]["path"], "--script", root / "adapters/joern/queries/modeling.sc"]
        for key, value in (
            ("inputPath", work), ("language", "PYTHONSRC"), ("sourceName", "dfb_source"),
            ("sinkName", "dfb_sink"), ("sourceKind", "call-return"),
            ("semanticsPath", semantics_path), ("outputPath", output / ("joern-" + name + ".json")),
        ):
            argv.extend(("--param", f"{key}={value}"))
        probe.run("joern-" + name, "joern", argv)


def _run_semgrep(probe: ProbeRun) -> None:
    root, output, workspace = probe.root, probe.output, probe.workspace
    rule = (root / "adapters/semgrep/rules/model-python.yaml").read_text(encoding="utf-8")
    for role, needle in (("source", "- pattern: fetch_remote(...)"), ("sink", "- pattern: record(...)")):
        for polarity in ("positive", "negative"):
            for variant in ("with", "without"):
                name = f"semgrep-declared-{role}-{polarity}-{variant}"
                work = _fixture(root, workspace, f"model-declared-{role}-{polarity}", name)
                artifact = output / f"{name}.yaml"
                artifact.write_text("".join(
                    line for line in rule.splitlines(keepends=True)
                    if not (variant == "without" and needle in line)
                ), encoding="utf-8")
                probe.run(name, "semgrep", [
                    probe.tools["semgrep"]["path"], "scan", "--metrics=off", "--oss-only",
                    "--disable-version-check", "--no-git-ignore", "--quiet", "--json",
                    "--config", artifact, work,
                ])
    for variant in ("safe-functions", "default-functions"):
        name = "semgrep-sanitizer-selectivity-" + variant
        work = _fixture(root, workspace, "model-sanitizer-selectivity-positive", name)
        artifact = output / (name + ".yaml")
        content = rule if variant == "safe-functions" else rule.replace(
            "taint_assume_safe_functions: true", "taint_assume_safe_functions: false"
        )
        artifact.write_text(content, encoding="utf-8")
        probe.run(name, "semgrep", [
            probe.tools["semgrep"]["path"], "scan", "--metrics=off", "--oss-only",
            "--disable-version-check", "--no-git-ignore", "--quiet", "--json",
            "--config", artifact, work,
        ])


def capture(
    contract_path: Path = CONTRACT,
    output_root: Path = OUTPUT_ROOT,
    *,
    root: Path = ROOT,
    runner: Callable[..., int] | None = None,
) -> int:
    raw_contract = contract_path.read_bytes()
    contract = json.loads(raw_contract)
    if contract.get("schema") != "release-execution-contract/v1" or contract.get("release") != "v0.9.0":
        raise ValueError("contract is not the v0.9.0 execution-v1 contract")
    if contract.get("execution_authorized") is not True:
        raise ValueError("execution authorization required: reviewed executable contract required")

    # Complete every authorization and identity check before creating output.
    control_environment = _check_control_environment(contract, root)
    tools = _check_held_tool_digests(contract, contract_path, root)
    output_root.mkdir(parents=True, exist_ok=False)
    workspace = output_root / "workspace"
    workspace.mkdir()
    probe = ProbeRun(
        root=root, output=output_root, contract=contract, tools=tools,
        control_environment=control_environment, runner=runner,
    )
    try:
        with _outer_interrupt_handlers():
            _run_bifrost(probe)
            _run_codeql(probe)
            _run_joern(probe)
            _run_semgrep(probe)
    finally:
        # The unique output root and workspace are evidence; leave them intact.
        probe.log.close()
    return 1 if probe.failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    try:
        return capture(args.contract, args.output_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
